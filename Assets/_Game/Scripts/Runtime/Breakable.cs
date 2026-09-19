// Breakable.cs
// One crate in the supply lane (the LOW band): a supply box worth its hp in coins with a +N planes
// gate riding behind it, or a weapon crate with the next plane hovering on top of it (every plane
// changes to it on break). It shows its HP on the box, holds a queue slot a fixed distance ahead of
// the squad, and pays out when shot down. Every bullet that lands flashes it white and rocks it.
using System.Collections.Generic;
using UnityEngine;

namespace SkySquad
{
    public enum BreakableKind { Box, Weapon }

    public class Breakable : MonoBehaviour
    {
        public TMPro.TextMeshPro label;
        public TMPro.TextMeshPro hint;
        public Transform model;           // the crate box: explodes on break
        public Renderer crateRenderer;    // materials: 0 crate, 1 bands
        public Transform boat;            // the boat under it (since 2026-09-18, parachutes before): detached and sunk on break (SinkingBoat)
        public Renderer boatRenderer;     // materials: 0 trim/mast, 1 hull (tinted per kind); a weapon boat adds 2 = white stripe
        public Mesh weaponBoatMesh;       // the weapon crate's boat: bigger, hull stripe and pennants in white (submeshes trim, hull, stripe)

        public BreakableKind Kind { get; private set; }
        public int Value { get; private set; }           // planes granted by a Box
        public WeaponDef Weapon { get; private set; }
        public float Hp { get; private set; }
        public float MaxHp { get; private set; }
        public int Slot { get; private set; }            // 0 = front of the queue
        public bool Dead { get; private set; }
        public float X, Z, Alt;
        public readonly List<UpgradeGate> Gates = new List<UpgradeGate>();   // the +1 gates riding one behind the other directly behind this crate (one per plane when gatesEnabled); all launched when the crate breaks

        public float HalfWidth => 1.4f;
        public Vector3 AimPoint => transform.position + Vector3.up * 0.2f;

        static MaterialPropertyBlock hitBlock;
        static readonly int BaseColor = Shader.PropertyToID("_BaseColor");
        public float boxTop = 1.13f;                     // the top of the box (set by the builder: 1.98 for the wooden box scaled to the gate width, 2026-09-18); the prize plane and the hint sit above it
        float ShowcaseHeight => boxTop + 0.37f;          // where the prize plane sits: just on the box
        float hitT, seed, targetZ, rockDir;
        bool hitShown;
        Transform showcase;                              // a weapon crate: the plane you will get, turning slowly, with its glow


        public void Init(BreakableKind kind, int value, WeaponDef weapon, float hp, int slot)
        {
            var cfg = GameManager.I.config;
            Kind = kind; Value = value; Weapon = weapon;
            MaxHp = Hp = Mathf.Max(1f, hp);
            Dead = false; hitT = 0f; seed = Random.value * 10f;
            X = 0f; Alt = cfg.supplyAlt;
            SetSlot(slot);
            Z = targetZ + 28f;                            // slides in from far ahead
            Color c = ColorFor();
            if (boatRenderer != null)
            {
                var ms = boatRenderer.materials;          // instances, so the tint is per crate
                if (ms.Length > 1) ms[1].color = c;       // the hull (and its flag) in the crate's colour
            }
            if (label != null)
            {   // the number sits ON the box, reference style, never wrapping
                label.color = Kind == BreakableKind.Box ? new Color(1f, 0.82f, 0.25f) : c;
                label.overflowMode = TMPro.TextOverflowModes.Overflow;
                label.rectTransform.sizeDelta = new Vector2(24f, 4f);
            }
            if (hint != null) hint.color = Kind == BreakableKind.Weapon ? c : new Color(1f, 0.82f, 0.25f);
            if (showcase != null) { Destroy(showcase.gameObject); showcase = null; }
            bool prize = Kind == BreakableKind.Weapon && Weapon != null && Weapon.planePrefab != null;
            if (boat != null && weaponBoatMesh != null && prize)
            {   // a weapon crate rides its own boat: bigger, hull in the weapon colour with a white stripe, two masts with white pennants
                // (2026-09-18, boats instead of parachutes; before: "a distinctive shape - it has a parachute, but a distinctive one")
                var mf = boat.GetComponent<MeshFilter>(); if (mf != null) mf.sharedMesh = weaponBoatMesh;
                if (boatRenderer != null)
                {
                    var ms = boatRenderer.materials;   // instances: trim, hull (tinted the weapon colour above)
                    if (ms.Length >= 2 && weaponBoatMesh.subMeshCount > 2)
                    {
                        var stripe = new Material(ms[1]); stripe.color = Color.white;
                        boatRenderer.materials = new[] { ms[0], ms[1], stripe };
                    }
                }
                var outline = boat.Find("Outline");
                if (outline != null)
                {
                    var omf = outline.GetComponent<MeshFilter>(); if (omf != null) omf.sharedMesh = weaponBoatMesh;
                    var or = outline.GetComponent<Renderer>();
                    if (or != null && or.sharedMaterials.Length < weaponBoatMesh.subMeshCount)
                    {   // one outline material per submesh, whatever the mesh has
                        var om = new Material[weaponBoatMesh.subMeshCount]; for (int i = 0; i < om.Length; i++) om[i] = or.sharedMaterials[0];
                        or.sharedMaterials = om;
                    }
                }
            }
            if (hint != null) hint.transform.localPosition = prize ? new Vector3(0f, boxTop + 1.62f, -0.6f) : new Vector3(0f, boxTop + 0.82f, -0.6f);   // above the prize plane on the box / above the box (the crates ride boats since 2026-09-18, no canopy to clear)
            if (prize)
            {   // the plane you will get sits on the box under the canopy, turning slowly; break the box to take it
                showcase = new GameObject("Showcase").transform;
                showcase.SetParent(transform, false);
                showcase.localPosition = new Vector3(0f, ShowcaseHeight, 0f);
                var plane = Instantiate(Weapon.planePrefab, showcase);
                plane.transform.localScale = Vector3.one * 1.5f;   // bigger than the squad's planes: it is the prize (fits under the wider canopy)
            }
            RefreshLabel();
            UpdateTransform();
        }

        public Color ColorFor()
        {
            switch (Kind)
            {
                case BreakableKind.Weapon: return Weapon != null ? Weapon.color : Color.white;
                default: return new Color(1f, 0.6f, 0.2f);
            }
        }

        void RefreshLabel()
        {
            if (label == null) return;
            int hp = Mathf.CeilToInt(Hp);
            label.text = hp.ToString();
            if (hint != null)
            {   // what this crate is worth: the planes behind it (gate or crate), the new plane on top, or coins only
                int planes = Gates.Count > 0 ? Gates.Count : Value;   // one +1 gate per plane
                string planesText = planes > 0 ? "+" + planes + " PLANES" : "";
                if (Kind == BreakableKind.Weapon && Weapon != null) hint.text = planes > 0 ? Weapon.displayName + "  ·  " + planesText : Weapon.displayName;
                else { int c = Mathf.RoundToInt(MaxHp * GameManager.I.config.coinsPerHp); hint.text = planes > 0 ? planesText : c > 0 ? "$ " + c : ""; }
            }
        }

        /// <summary>Queue position; the crate eases toward the z that slot maps to.</summary>
        public void SetSlot(int slot)
        {
            var cfg = GameManager.I.config;
            Slot = slot;
            targetZ = SupplyLane.I != null ? SupplyLane.I.SlotZ(slot) : cfg.supplyFrontZ + slot * cfg.supplySpacing;   // the crates ahead push this one back by their gates
            for (int i = 0; i < Gates.Count; i++) Gates[i].SetHold(targetZ + cfg.gateGap + i * cfg.gateStep);   // its gates keep riding right behind it, one behind the other
        }

        void Update()
        {
            var gm = GameManager.I;
            if (Dead || gm == null || (gm.State != GameState.Playing && gm.State != GameState.Title)) return;   // Title: it settles into its slot and bobs under the lobby (2026-09-19)
            float dt = Time.deltaTime;
            Z = Mathf.Lerp(Z, targetZ, 1f - Mathf.Pow(0.08f, dt));
            hitT = Mathf.Max(0f, hitT - dt);
            UpdateTransform();
        }

        void UpdateTransform()
        {
            float t = Time.time;
            float bob = Mathf.Sin(t * 1.8f + seed) * 0.15f;
            transform.position = new Vector3(X, 1f + Alt + bob, Z);
            float s = 1f + hitT * 1.5f;
            transform.localScale = new Vector3(s, s, s);
            if (model != null)
                model.localRotation = Quaternion.Euler(Mathf.Sin(t * 1.3f + seed) * 3f + hitT * 90f, 0f, Mathf.Sin(t * 1.1f + seed) * 4f + hitT * 60f * rockDir);
            if (boat != null)   // the boat rides the same swell as the box, without the hit kick
                boat.localRotation = Quaternion.Euler(Mathf.Sin(t * 1.3f + seed) * 3f, 0f, Mathf.Sin(t * 1.1f + seed) * 4f);
            if (showcase != null)
            {   // the new plane turns slowly on top, nose a little up, and lifts with the bob
                showcase.localPosition = new Vector3(0f, ShowcaseHeight + Mathf.Sin(t * 2.2f + seed) * 0.04f, 0f);
                showcase.localRotation = Quaternion.Euler(-8f, t * 50f + seed * 30f, 0f);
            }
            bool showHit = hitT > 0f;
            if (showHit != hitShown && crateRenderer != null)
            {
                hitShown = showHit;
                if (showHit)
                {
                    if (hitBlock == null) hitBlock = new MaterialPropertyBlock();
                    hitBlock.SetColor(BaseColor, new Color(3f, 3f, 3f));   // HDR: the textured wooden box (2026-09-18) must still flash white, base colour multiplies its texture
                    crateRenderer.SetPropertyBlock(hitBlock);
                }
                else crateRenderer.SetPropertyBlock(null);
            }
        }

        /// <summary>Called by AutoFire once per volley that lands: one countable chunk of damage.</summary>
        public void Shoot(float dmg)
        {
            if (Dead) return;
            Hp -= dmg;
            hitT = 0.08f;
            rockDir = Random.value < 0.5f ? -1f : 1f;
            RefreshLabel();
            if (Hp <= 0f) Break();
        }

        void Break()
        {
            Dead = true;
            var gm = GameManager.I;
            var sq = gm.squad;
            var fx = FXManager.I;
            Vector3 p = transform.position;
            Color gold = new Color(1f, 0.82f, 0.35f);   // the +planes colour, amber like the gates (green until 2026-09-18)
            // every crate: its hp in coins, and the planes behind it (the gate launches at the squad; with gates off the crate pays them)
            int coins = Mathf.RoundToInt(MaxHp * gm.config.coinsPerHp);   // 0 with coinsPerHp 0: "no coins from boxes" (2026-09-16), the planes/gates/weapon are the prize
            if (coins > 0) coins = gm.AddCoins(coins);   // the bank applies the revenue multiplier
            if (Gates.Count == 0 && Value > 0) { sq.Grow(Value); fx.FloatText(p + Vector3.up * 2.2f, "+" + Value + " PLANES", gold, 1.1f); }
            fx.Explosion(p, false);
            fx.Sparks(p, gold, 12);
            foreach (var g in Gates) g.Launch();   // the barrier is down: its gates come at the squad, fast, one after the other, +1 each
            Gates.Clear();
            if (coins > 0) fx.CoinBurst(p + Vector3.up * 1.6f, coins);
            if (Kind == BreakableKind.Weapon && Weapon != null)
            {   // a weapon crate: every plane changes to the plane that was on top of it
                sq.SetWeapon(Weapon);
                fx.Ring(p + Vector3.up * 0.5f, Weapon.color, 9f);
                fx.FloatText(sq.transform.position + Vector3.up * 2.6f, Weapon.displayName + "!", Weapon.color, 1f);
                gm.hud.Banner(Weapon.displayName + "!", Weapon.color, 0.9f);
                AudioManager.I.Play(Sfx.Pickup);
            }
            else AudioManager.I.Play(Sfx.Good);
            if (boat != null)
            {   // the box blew up; the boat under it goes down (requested 2026-09-18): detached so it outlives this crate, SinkingBoat drifts it back with the sea and under
                boat.SetParent(null, true);
                boat.gameObject.AddComponent<SinkingBoat>();
                boat = null;
            }
            SupplyLane.I.Release(this);
        }
    }
}
