// Breakable.cs
// One crate in the supply lane (the LOW band): a supply box worth +N planes and its hp in coins,
// or a weapon crate. It shows its HP on the box, holds a queue slot a fixed distance ahead of the
// squad, and pays out when shot down. Every bullet that lands flashes it white and rocks it.
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
        float hitT, seed, targetZ, rockDir;
        bool hitShown;

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
            if (hint != null) hint.text = Kind == BreakableKind.Box ? (Gate != null ? "BREAK IT" : Value > 0 ? "+" + Value + " PLANES" : "$ " + Mathf.Max(1, Mathf.RoundToInt(MaxHp * GameManager.I.config.coinsPerHp))) : (Weapon != null ? Weapon.displayName : "AMMO");   // an empty crate (no gate) shows what it is worth: coins
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
            Color gold = new Color(1f, 0.82f, 0.25f), green = new Color(0.45f, 0.95f, 0.5f);
            switch (Kind)
            {
                case BreakableKind.Box:
                    int coins = Mathf.Max(1, Mathf.RoundToInt(MaxHp * gm.config.coinsPerHp));
                    coins = gm.AddCoins(coins);   // the bank applies the revenue multiplier
                    if (Gate == null && Value > 0) { sq.Grow(Value); fx.FloatText(p + Vector3.up * 2.2f, "+" + Value + " PLANES", green, 1.1f); }   // gates off: the crate itself pays the planes
                    fx.Explosion(p, false);
                    fx.Sparks(p, green, 12);
                    if (Gate != null) { Gate.Launch(); Gate = null; }   // the barrier is down: its gate comes at the squad, fast, with the reward
                    fx.CoinBurst(p + Vector3.up * 1.6f, coins);
                    AudioManager.I.Play(Sfx.Good);
                    break;
                case BreakableKind.Weapon:
                    sq.SetWeapon(Weapon);
                    fx.Explosion(p, false);
                    fx.Ring(p + Vector3.up * 0.5f, Weapon.color, 9f);
                    fx.FloatText(sq.transform.position + Vector3.up * 2.6f, Weapon.displayName + "!", Weapon.color, 1f);
                    gm.hud.Banner(Weapon.displayName + "!", Weapon.color, 0.9f);
                    AudioManager.I.Play(Sfx.Pickup);
                    break;
            }
            SupplyLane.I.Release(this);
        }
    }
}
