// Breakable.cs
// One crate in the supply lane (the LOW band): a supply box worth its hp in coins with a +N planes
// gate riding behind it, or a weapon crate with the next plane hovering on top of it (every plane
// changes to it on break). It shows its HP on the box, holds a queue slot a fixed distance ahead of
// the squad, and pays out when shot down. Every bullet that lands flashes it white and rocks it.
using UnityEngine;

namespace SkySquad
{
    public enum BreakableKind { Box, Weapon }

    public class Breakable : MonoBehaviour
    {
        public TMPro.TextMeshPro label;
        public TMPro.TextMeshPro hint;
        public Transform model;
        public Renderer crateRenderer;    // materials: 0 crate, 1 bands, 2 canopy (tinted per kind)

        public BreakableKind Kind { get; private set; }
        public int Value { get; private set; }           // planes granted by a Box
        public WeaponDef Weapon { get; private set; }
        public float Hp { get; private set; }
        public float MaxHp { get; private set; }
        public int Slot { get; private set; }            // 0 = front of the queue
        public bool Dead { get; private set; }
        public float X, Z, Alt;
        public UpgradeGate Gate;                         // the gate riding directly behind this crate (every crate has one when gatesEnabled); launched when the crate breaks

        public float HalfWidth => 1.4f;
        public Vector3 AimPoint => transform.position + Vector3.up * 0.2f;

        static MaterialPropertyBlock hitBlock;
        static readonly int BaseColor = Shader.PropertyToID("_BaseColor");
        const float ShowcaseHeight = 3.4f;               // where the new plane hovers: above the parachute
        float hitT, seed, targetZ, rockDir;
        bool hitShown;
        Transform showcase;                              // a weapon crate: the plane you will get, turning slowly on top

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
            if (crateRenderer != null)
            {
                var ms = crateRenderer.materials;         // instances, so the tint is per crate
                if (ms.Length > 2) ms[2].color = c;
            }
            if (label != null)
            {   // the number sits ON the box, reference style, never wrapping
                label.color = Kind == BreakableKind.Box ? new Color(1f, 0.82f, 0.25f) : c;
                label.overflowMode = TMPro.TextOverflowModes.Overflow;
                label.rectTransform.sizeDelta = new Vector2(24f, 4f);
            }
            if (hint != null) hint.color = Kind == BreakableKind.Weapon ? c : new Color(1f, 0.82f, 0.25f);
            if (showcase != null) { Destroy(showcase.gameObject); showcase = null; }
            if (Kind == BreakableKind.Weapon && Weapon != null && Weapon.planePrefab != null)
            {   // the new plane sits on top of the crate so you see what your planes will become
                showcase = new GameObject("Showcase").transform;
                showcase.SetParent(transform, false);
                showcase.localPosition = new Vector3(0f, ShowcaseHeight, 0f);
                var plane = Instantiate(Weapon.planePrefab, showcase);
                plane.transform.localScale = Vector3.one * 1.3f;
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
                int planes = Gate != null ? Gate.Planes : Value;
                string planesText = planes > 0 ? "+" + planes + " PLANES" : "";
                if (Kind == BreakableKind.Weapon && Weapon != null) hint.text = planes > 0 ? Weapon.displayName + "  ·  " + planesText : Weapon.displayName;
                else hint.text = planes > 0 ? planesText : "$ " + Mathf.Max(1, Mathf.RoundToInt(MaxHp * GameManager.I.config.coinsPerHp));
            }
        }

        /// <summary>Queue position; the crate eases toward the z that slot maps to.</summary>
        public void SetSlot(int slot)
        {
            var cfg = GameManager.I.config;
            Slot = slot;
            targetZ = cfg.supplyFrontZ + slot * cfg.supplySpacing;
            if (Gate != null) Gate.SetHold(targetZ + cfg.gateGap);   // its gate keeps riding right behind it
        }

        void Update()
        {
            var gm = GameManager.I;
            if (Dead || gm == null || gm.State != GameState.Playing) return;
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
            if (showcase != null)
            {   // the new plane turns slowly on top, nose a little up, and lifts with the bob
                showcase.localPosition = new Vector3(0f, ShowcaseHeight + Mathf.Sin(t * 2.2f + seed) * 0.1f, 0f);
                showcase.localRotation = Quaternion.Euler(-8f, t * 50f + seed * 30f, 0f);
            }
            bool showHit = hitT > 0f;
            if (showHit != hitShown && crateRenderer != null)
            {
                hitShown = showHit;
                if (showHit)
                {
                    if (hitBlock == null) hitBlock = new MaterialPropertyBlock();
                    hitBlock.SetColor(BaseColor, Color.white);
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
            Color green = new Color(0.45f, 0.95f, 0.5f);
            // every crate: its hp in coins, and the planes behind it (the gate launches at the squad; with gates off the crate pays them)
            int coins = Mathf.Max(1, Mathf.RoundToInt(MaxHp * gm.config.coinsPerHp));
            coins = gm.AddCoins(coins);   // the bank applies the revenue multiplier
            if (Gate == null && Value > 0) { sq.Grow(Value); fx.FloatText(p + Vector3.up * 2.2f, "+" + Value + " PLANES", green, 1.1f); }
            fx.Explosion(p, false);
            fx.Sparks(p, green, 12);
            if (Gate != null) { Gate.Launch(); Gate = null; }   // the barrier is down: its gate comes at the squad, fast, with the reward
            fx.CoinBurst(p + Vector3.up * 1.6f, coins);
            if (Kind == BreakableKind.Weapon && Weapon != null)
            {   // a weapon crate: every plane changes to the plane that was on top of it
                sq.SetWeapon(Weapon);
                fx.Ring(p + Vector3.up * 0.5f, Weapon.color, 9f);
                fx.FloatText(sq.transform.position + Vector3.up * 2.6f, Weapon.displayName + "!", Weapon.color, 1f);
                gm.hud.Banner(Weapon.displayName + "!", Weapon.color, 0.9f);
                AudioManager.I.Play(Sfx.Pickup);
            }
            else AudioManager.I.Play(Sfx.Good);
            SupplyLane.I.Release(this);
        }
    }
}
