// UpgradeGate.cs
// The reward gate that rides directly behind a crate in the LOW band. The crate is the barrier; the moment
// it breaks, the gate shoots forward at the squad (gateSpeed) and, if the squad is in the low band and
// inside the MIDDLE of the frame (PassHalfWidth, and between its bars) when it arrives, the squad flies THROUGH it and takes the reward:
//   PLANES  +1 plane (a +n crate carries n of these one behind the other)
// SHIELD  a bubble that soaks Amount hits, then is gone                   } coded but not spawned any more
// PLANE   every plane becomes the next, stronger plane (WeaponDef)   } (the crate table only makes +1 gates;
//         (past the last weapon: +gatePowerBonus damage, "MK n")     }  the next plane rides on a weapon crate)
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

        public GateKind Kind { get; private set; }
        public int Amount { get; private set; }   // Planes: how many planes; Shield: how many hits it soaks
        public int Planes => Amount;
        public float X, Z, Alt;
        public bool Launched { get; private set; }
        public bool Done { get; private set; }
        public float HalfWidth => 2.2f;         // the frame: MeshFactory.GateFrame(2.2, 3.4)
        public const float Height = 3.4f;
        public float PassHalfWidth => 1.1f;     // the squad must fly through the MIDDLE of the frame, not clip a post ("hit it in its middle", 2026-09-18; was the full 2.2)

        static MaterialPropertyBlock mpb;
        static readonly int BaseColor = Shader.PropertyToID("_BaseColor");
        static readonly Color ShieldColor = new Color(0.58f, 0.77f, 0.99f), PlanesColor = new Color(0.45f, 0.95f, 0.45f);   // green (2026-09-19, "the ones behind the box green"; amber on 2026-09-18, mint before)
        float targetZ, seed;
        bool placed;
        Color color;

        public void Init(GateKind kind, int amount)
        {
            Kind = kind; Amount = amount;
            X = 0f; Alt = GameManager.I.config.supplyAlt;
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
                    color = next != null ? next.color : PlanesColor;
                    if (label != null) { label.text = next != null ? next.displayName : "MK " + (sq.PowerTier + 2); label.color = color; }
                    if (hint != null) hint.text = next != null ? "NEW PLANES" : "+" + Mathf.RoundToInt(gm.config.gatePowerBonus * 100f) + "% DAMAGE";
                    break;
                default:
                    color = PlanesColor;
                    if (label != null) { label.text = "+" + Amount; label.color = color; }
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
                if (Z <= sq.Z + 0.4f)   // measured from the squad, which flies forward when it dives (SquadController.Z)
                {
                    float dy = sq.transform.position.y - transform.position.y;   // the frame stands on transform.position: the squad must be inside it, not over the top bar
                    if (!sq.IsHigh && Mathf.Abs(sq.X - X) < PassHalfWidth && dy > -0.4f && dy < Height + 0.4f) { Pass(); return; }   // 0.4 of slack: the planes have a body
                    if (Z < sq.Z - 6f) { Done = true; SupplyLane.I.ReleaseGate(this); return; }   // flown past
                }
            }
            Apply();
        }

        void Apply()
        {
            float t = Time.time;
            transform.position = new Vector3(X, 1f + Alt - 1.2f + Mathf.Sin(t * 1.6f + seed) * 0.1f, Z);
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
            fx.GateBurst(p, color);   // the pack's rings burst + the game's ring (2026-09-19)
            fx.Sparks(p, color, Kind == GateKind.Planes ? 8 : 16);
            if (Kind == GateKind.Planes) fx.FloatText(p + Vector3.up * (2.2f + Random.value * 1.2f) + Vector3.right * (Random.value - 0.5f) * 2.4f, title, color, 1.1f);   // a train of +1 gates passes in a blink: scatter the texts so they do not stack
            else fx.FloatText(p + Vector3.up * 2.6f, title, color, 1.1f);
            if (Kind != GateKind.Planes) { gm.hud.Banner(title, color, 0.9f); fx.Flash(new Color(color.r, color.g, color.b, 0.5f), 0.15f); }
            AudioManager.I.Play(Kind == GateKind.Planes ? Sfx.Good : Sfx.Pickup);
            SupplyLane.I.ReleaseGate(this);
        }
    }
}
