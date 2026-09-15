// Breakable.cs
// One crate in the supply lane (the LOW band). Its number is the bullets it takes; its reward is fixed
// by the crate table (GameConfig.crates) and shown under it. The reward rides behind the crate as blue
// squares (UpgradeGate): break the crate and the squares come at the squad - fly through them, down in
// the low band, to collect. The crate itself pays coins (hp x coinsPerHp) the moment it breaks.
// It holds a queue slot a fixed distance ahead of the squad; every bullet that lands flashes it white
// and rocks it.
using System.Collections.Generic;
using UnityEngine;

namespace SkySquad
{
    public class Breakable : MonoBehaviour
    {
        public TMPro.TextMeshPro label;
        public TMPro.TextMeshPro hint;
        public Transform model;
        public Renderer crateRenderer;    // materials: 0 crate, 1 bands, 2 canopy (tinted per reward)

        public int Index { get; private set; }           // crate number this attempt, 0 = the first
        public CrateReward Reward { get; private set; }
        public int Amount { get; private set; }          // planes / shield hits / bonus coins
        public float Hp { get; private set; }
        public float MaxHp { get; private set; }
        public int Slot { get; private set; }            // 0 = front of the queue
        public bool Dead { get; private set; }
        public float X, Z, Alt;
        public readonly List<UpgradeGate> Squares = new List<UpgradeGate>();   // the reward squares riding behind this crate; launched when it breaks

        public float HalfWidth => 1.4f;
        public Vector3 AimPoint => transform.position + Vector3.up * 0.2f;

        static MaterialPropertyBlock hitBlock;
        static readonly int BaseColor = Shader.PropertyToID("_BaseColor");
        float hitT, seed, targetZ, rockDir;
        bool hitShown;

        public void Init(int index, float hp, CrateReward reward, int amount, int slot)
        {
            var cfg = GameManager.I.config;
            Index = index; Reward = reward; Amount = amount;
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
                label.color = new Color(1f, 0.82f, 0.25f);
                label.overflowMode = TMPro.TextOverflowModes.Overflow;
                label.rectTransform.sizeDelta = new Vector2(24f, 4f);
            }
            if (hint != null) { hint.text = RewardText(); hint.color = c; }
            RefreshLabel();
            UpdateTransform();
        }

        /// <summary>The canopy's colour says what the crate holds: blue planes, cyan shield, the weapon's colour, gold coins.</summary>
        public Color ColorFor()
        {
            switch (Reward)
            {
                case CrateReward.Shield: return UpgradeGate.ShieldColor;
                case CrateReward.Plane: var w = SupplyLane.I != null ? SupplyLane.I.NextWeapon(GameManager.I.squad.Weapon) : null; return w != null ? w.color : new Color(0.55f, 1f, 0.6f);
                case CrateReward.Coins: return new Color(1f, 0.82f, 0.25f);
                default: return UpgradeGate.PlanesColor;
            }
        }

        string RewardText()
        {
            switch (Reward)
            {
                case CrateReward.Shield: return "SHIELD " + Amount;
                case CrateReward.Plane: var w = SupplyLane.I != null ? SupplyLane.I.NextWeapon(GameManager.I.squad.Weapon) : null; return w != null ? w.displayName : "MK " + (GameManager.I.squad.PowerTier + 2);
                case CrateReward.Coins: return "$ " + Amount;
                default: return "+" + Amount + (Amount == 1 ? " PLANE" : " PLANES");
            }
        }

        void RefreshLabel()
        {
            if (label != null) label.text = Mathf.CeilToInt(Hp).ToString();
        }

        /// <summary>Queue position; the crate eases toward the z that slot maps to, and its squares hold behind it in rows of two.</summary>
        public void SetSlot(int slot)
        {
            var cfg = GameManager.I.config;
            Slot = slot;
            targetZ = cfg.supplyFrontZ + slot * cfg.supplySpacing;
            for (int i = 0; i < Squares.Count; i++)
                if (Squares[i] != null) Squares[i].SetHold(targetZ + cfg.gateGap + (i / 2) * cfg.squareRowSpacing);
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

        /// <summary>Called by BulletPool for every bullet that lands: one countable chunk of damage.</summary>
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
            var fx = FXManager.I;
            Vector3 p = transform.position;
            Color c = ColorFor();
            int coins = gm.AddCoins(Mathf.Max(1, Mathf.RoundToInt(MaxHp * gm.config.coinsPerHp)));   // the bank applies the revenue multiplier
            fx.Explosion(p, false);
            fx.Sparks(p, c, 12);
            fx.CoinBurst(p + Vector3.up * 1.6f, coins);
            if (Squares.Count > 0)
            {   // the barrier is down: its squares come at the squad, fast, carrying the reward
                foreach (var s in Squares) if (s != null) s.Launch();
                Squares.Clear();
            }
            else if (Amount > 0)
            {   // no squares (gatesEnabled off, or a coins-only crate): the crate itself pays
                var (title, tc) = UpgradeGate.Grant(Reward, Amount);
                fx.FloatText(p + Vector3.up * 2.2f, title, tc, 1.1f);
            }
            AudioManager.I.Play(Sfx.Good);
            SupplyLane.I.Release(this);
        }
    }
}
