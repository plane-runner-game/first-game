// UpgradeGate.cs
// One reward square in the LOW band. A crate's reward is not handed over when the crate breaks: it rides
// behind the crate as blue squares (one square per plane; a shield or a new plane is one square), and
// the moment the crate breaks the squares shoot forward at the squad. Dive into the low band and fly
// THROUGH a square to take what it holds:
//   PLANES  +1 plane per square (blue)
//   SHIELD  a bubble that soaks Amount hits, then is gone (cyan)
//   PLANE   every plane becomes the next, stronger plane (WeaponDef colour); past the last weapon
//           +gatePowerBonus damage ("MK n")
// Stay high or slip past it and the square is simply gone.
using UnityEngine;

namespace SkySquad
{
    public class UpgradeGate : MonoBehaviour
    {
        public Transform model;
        public Renderer frame;            // the square's frame; tinted per reward
        public Renderer panel;            // the translucent fill; pulses, brighter once launched
        public TMPro.TextMeshPro label;   // what you get
        public TMPro.TextMeshPro hint;    // how

        public CrateReward Kind { get; private set; }
        public int Amount { get; private set; }   // Planes: always 1 (one square per plane); Shield: hits it soaks
        public float X, Z, Alt;
        public bool Launched { get; private set; }
        public bool Done { get; private set; }
        public float HalfWidth => 1.0f;           // the square is 2 x 2
        public const float PassSlack = 0.9f;      // the squad's own half-width: it passes if any of it overlaps the square

        static MaterialPropertyBlock mpb;
        static readonly int BaseColor = Shader.PropertyToID("_BaseColor");
        public static readonly Color PlanesColor = new Color(0.32f, 0.62f, 1f), ShieldColor = new Color(0.45f, 0.95f, 0.9f);
        float targetZ, seed;
        bool placed;
        Color color;

        public void Init(CrateReward kind, int amount, float x)
        {
            Kind = kind; Amount = amount; X = x;
            Alt = GameManager.I.config.supplyAlt;
            Launched = Done = placed = false; seed = Random.value * 10f;
            RefreshLabel();
        }

        /// <summary>Where it waits: behind its crate. The crate calls this from SetSlot, so the group moves together.</summary>
        public void SetHold(float z)
        {
            targetZ = z;
            if (!placed) { Z = z + 28f; placed = true; Apply(); }   // slides in from far ahead WITH its crate, never alone
        }

        /// <summary>The crate in front is gone: shoot forward at the squad.</summary>
        public void Launch() { Launched = true; }

        void RefreshLabel()
        {
            var gm = GameManager.I;
            var sq = gm.squad;
            switch (Kind)
            {
                case CrateReward.Shield:
                    color = ShieldColor;
                    if (label != null) { label.text = "SHIELD"; label.color = color; }
                    if (hint != null) hint.text = Amount + (Amount == 1 ? " HIT" : " HITS");
                    break;
                case CrateReward.Plane:
                    var next = SupplyLane.I.NextWeapon(sq.Weapon);
                    color = next != null ? next.color : new Color(0.55f, 1f, 0.6f);
                    if (label != null) { label.text = next != null ? next.displayName : "MK " + (sq.PowerTier + 2); label.color = color; }
                    if (hint != null) hint.text = next != null ? "NEW PLANES" : "+" + Mathf.RoundToInt(gm.config.gatePowerBonus * 100f) + "% DAMAGE";
                    break;
                default:
                    color = PlanesColor;
                    if (label != null) { label.text = "+" + Amount; label.color = Color.white; }
                    if (hint != null) hint.text = Amount == 1 ? "PLANE" : "PLANES";
                    break;
            }
            if (mpb == null) mpb = new MaterialPropertyBlock();
            if (frame != null) { mpb.SetColor(BaseColor, color); frame.SetPropertyBlock(mpb); }
        }

        void Update()
        {
            var gm = GameManager.I;
            if (Done || gm == null || gm.State != GameState.Playing || !placed) return;
            float dt = Time.deltaTime;
            if (!Launched) Z = Mathf.Lerp(Z, targetZ, 1f - Mathf.Pow(0.08f, dt));
            else
            {
                Z -= gm.config.gateSpeed * dt;   // at the squad about a second after the crate breaks
                var sq = gm.squad;
                if (Z <= 0.4f)
                {
                    if (!sq.IsHigh && Mathf.Abs(sq.X - X) < HalfWidth + PassSlack) { Pass(); return; }
                    if (Z < -6f) { Done = true; SupplyLane.I.ReleaseGate(this); return; }   // flown past
                }
            }
            Apply();
        }

        void Apply()
        {
            float t = Time.time;
            transform.position = new Vector3(X, 1f + Alt - 1.3f + Mathf.Sin(t * 1.6f + seed) * 0.08f, Z);   // the square sits centred on the squad's altitude
            if (panel != null)
            {
                if (mpb == null) mpb = new MaterialPropertyBlock();
                var c = color; c.a = Launched ? 0.42f + 0.12f * Mathf.Sin(t * 12f) : 0.2f + 0.06f * Mathf.Sin(t * 3f + seed);
                mpb.SetColor(BaseColor, c);
                panel.SetPropertyBlock(mpb);
            }
        }

        /// <summary>The squad flew through: the reward.</summary>
        void Pass()
        {
            Done = true;
            var gm = GameManager.I;
            var sq = gm.squad;
            var fx = FXManager.I;
            var (title, c) = Grant(Kind, Amount);
            Vector3 p = sq.transform.position;
            fx.Ring(p + Vector3.up * 0.5f, c, 9f);
            fx.Sparks(p, c, Kind == CrateReward.Planes ? 8 : 16);
            if (Kind == CrateReward.Planes) fx.FloatText(p + Vector3.up * (2.4f + Mathf.Abs(X) * 0.3f) + Vector3.right * X * 1.6f, "+1", c, 1.2f);   // each square pops its own "+1", left and right, never on top of each other
            else fx.FloatText(p + Vector3.up * 2.6f, title, c, 1.1f);
            if (Kind != CrateReward.Planes) { gm.hud.Banner(title, c, 0.9f); fx.Flash(new Color(c.r, c.g, c.b, 0.5f), 0.15f); }
            AudioManager.I.Play(Kind == CrateReward.Planes ? Sfx.Good : Sfx.Pickup);
            SupplyLane.I.ReleaseGate(this);
        }

        /// <summary>Hands the reward to the squad. Shared with Breakable, which pays directly when the squares are turned off (gatesEnabled = false).</summary>
        public static (string title, Color color) Grant(CrateReward kind, int amount)
        {
            var gm = GameManager.I;
            var sq = gm.squad;
            switch (kind)
            {
                case CrateReward.Shield:
                    sq.SetShield(amount);   // a fresh shield, not stacked: n hits, then it is gone
                    return ("SHIELD  " + amount + (amount == 1 ? " HIT" : " HITS"), ShieldColor);
                case CrateReward.Plane:
                    var next = SupplyLane.I.NextWeapon(sq.Weapon);
                    if (next != null) { sq.SetWeapon(next); return (next.displayName + "!", next.color); }
                    sq.PowerTier++;
                    return ("MK " + (sq.PowerTier + 1) + "  +" + Mathf.RoundToInt(gm.config.gatePowerBonus * 100f) + "% DMG", new Color(0.55f, 1f, 0.6f));
                case CrateReward.Coins:
                    int v = gm.AddCoins(amount);
                    return ("+" + v, new Color(1f, 0.82f, 0.25f));
                default:
                    sq.Grow(amount);
                    return ("+" + amount + (amount == 1 ? " PLANE" : " PLANES"), PlanesColor);
            }
        }
    }
}
