// UpgradeGate.cs
// The reward gate that rides directly behind a crate in the LOW band. The crate is the barrier; the moment
// it breaks, the gate shoots forward at the squad (gateSpeed) and, if the squad is in the low band and
// inside the gate's width when it arrives, the squad flies THROUGH it and takes the reward:
//   PLANES  +2 (ordinary) or +5 (rare) planes
// SHIELD  a bubble that soaks Amount (1..3) hits, then is gone            } rolled per crate by weight:
// PLANE   every plane becomes the next, stronger plane (WeaponDef)   } shield uncommon, +5 rare,
//         (past the last weapon: +gatePowerBonus damage, "MK n")     } the next plane very rare
// Fly past it or stay high and it is simply gone.
using UnityEngine;

namespace SkySquad
{
    public enum GateKind { Planes, Shield, Plane }

    public class UpgradeGate : MonoBehaviour
    {
        public Transform model;
        public Renderer panel;            // the translucent fill; pulses, flashes on pass
        public TMPro.TextMeshPro label;   // what you get
        public TMPro.TextMeshPro hint;    // how
        public bool square;               // the RewardSquare prefab: a blue 2 x 2 square worth +1 plane (crate 1 carries two of them)

        public GateKind Kind { get; private set; }
        public int Amount { get; private set; }   // Planes: how many planes; Shield: how many hits it soaks
        public int Planes => Amount;
        public float X, Z, Alt;
        public bool Launched { get; private set; }
        public bool Done { get; private set; }
        public float HalfWidth => square ? 1.0f : 2.2f;

        static MaterialPropertyBlock mpb;
        static readonly int BaseColor = Shader.PropertyToID("_BaseColor");
        static readonly Color ShieldColor = new Color(0.58f, 0.77f, 0.99f), PlanesColor = new Color(0.45f, 0.95f, 0.5f), SquareColor = new Color(0.32f, 0.62f, 1f);
        float targetZ, seed;
        bool placed;
        Color color;

        public void Init(GateKind kind, int amount, float x = 0f)
        {
            Kind = kind; Amount = amount;
            X = x; Alt = GameManager.I.config.supplyAlt;
            Launched = Done = placed = false; seed = Random.value * 10f;
            if (panel != null) panel.enabled = kind != GateKind.Plane;   // the new-plane gate has no fill: just the frame and the name (requested)
            RefreshLabel();
        }

        /// <summary>Where it waits: right behind its crate. The crate calls this from SetSlot, so the pair moves together.</summary>
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
                case GateKind.Shield:
                    color = ShieldColor;
                    if (label != null) { label.text = "SHIELD"; label.color = color; }
                    if (hint != null) hint.text = Amount + (Amount == 1 ? " HIT" : " HITS");
                    break;
                case GateKind.Plane:
                    var next = SupplyLane.I.NextWeapon(sq.Weapon);
                    color = next != null ? next.color : new Color(0.55f, 1f, 0.6f);
                    if (label != null) { label.text = next != null ? next.displayName : "MK " + (sq.PowerTier + 2); label.color = color; }
                    if (hint != null) hint.text = next != null ? "NEW PLANES" : "+" + Mathf.RoundToInt(gm.config.gatePowerBonus * 100f) + "% DAMAGE";
                    break;
                default:
                    color = square ? SquareColor : PlanesColor;
                    if (label != null) { label.text = "+" + Amount; label.color = square ? Color.white : color; }
                    if (hint != null) hint.text = Amount == 1 ? "PLANE" : "PLANES";
                    break;
            }
        }

        void Update()
        {
            var gm = GameManager.I;
            if (Done || gm == null || gm.State != GameState.Playing || !placed) return;
            float dt = Time.deltaTime;
            if (!Launched) Z = Mathf.Lerp(Z, targetZ, 1f - Mathf.Pow(0.08f, dt));
            else
            {
                Z -= gm.config.gateSpeed * dt;   // fast: it is at the squad well under a second after the crate breaks
                var sq = gm.squad;
                if (Z <= 0.4f)
                {
                    if (!sq.IsHigh && Mathf.Abs(sq.X - X) < HalfWidth + (square ? 0.9f : 0f)) { Pass(); return; }   // a square counts if any of the squad overlaps it: at x = 0 you take both
                    if (Z < -6f) { Done = true; SupplyLane.I.ReleaseGate(this); return; }   // flown past
                }
            }
            Apply();
        }

        void Apply()
        {
            float t = Time.time;
            transform.position = new Vector3(X, 1f + Alt - (square ? 1.3f : 1.2f) + Mathf.Sin(t * 1.6f + seed) * 0.1f, Z);   // a square sits centred on the squad's altitude
            if (panel != null && Kind != GateKind.Plane)
            {
                if (mpb == null) mpb = new MaterialPropertyBlock();
                var c = color; c.a = Launched ? 0.4f + 0.12f * Mathf.Sin(t * 12f) : 0.18f + 0.06f * Mathf.Sin(t * 3f + seed);
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
            string title;
            switch (Kind)
            {
                case GateKind.Shield:
                    sq.SetShield(Amount);   // a fresh shield, not stacked: 1..3 hits, then it is gone
                    title = "SHIELD  " + Amount + (Amount == 1 ? " HIT" : " HITS");
                    break;
                case GateKind.Plane:
                    var next = SupplyLane.I.NextWeapon(sq.Weapon);
                    if (next != null) { sq.SetWeapon(next); title = next.displayName + "!"; color = next.color; }
                    else { sq.PowerTier++; title = "MK " + (sq.PowerTier + 1) + "  +" + Mathf.RoundToInt(gm.config.gatePowerBonus * 100f) + "% DMG"; }
                    break;
                default:
                    sq.Grow(Amount);
                    title = "+" + Amount + (Amount == 1 ? " PLANE" : " PLANES");
                    break;
            }
            Vector3 p = sq.transform.position;
            fx.Ring(p + Vector3.up * 0.5f, color, 9f);
            fx.Sparks(p, color, 16);
            if (square) fx.FloatText(p + Vector3.up * (2.4f + Mathf.Abs(X) * 0.3f) + Vector3.right * X * 1.6f, "+1", color, 1.2f);   // each square pops its own "+1", left and right
            else fx.FloatText(p + Vector3.up * 2.6f, title, color, 1.1f);
            if (Kind != GateKind.Planes) { gm.hud.Banner(title, color, 0.9f); fx.Flash(new Color(color.r, color.g, color.b, 0.5f), 0.15f); }
            AudioManager.I.Play(Kind == GateKind.Planes ? Sfx.Good : Sfx.Pickup);
            SupplyLane.I.ReleaseGate(this);
        }
    }
}
