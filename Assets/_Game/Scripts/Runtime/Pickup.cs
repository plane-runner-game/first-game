// Pickup.cs
// A side gate: +N planes, x2, shield, bomb or a weapon crate. Sits on the left or right
// edge, low or high. Shooting a +N gate grows its number; flying through it collects it.
using UnityEngine;

namespace SkySquad
{
    public enum PickupKind { Plus, X2, Shield, Bomb, Weapon }

    public class Pickup : MonoBehaviour
    {
        public TMPro.TextMeshPro label;
        public TMPro.TextMeshPro hint;
        public Renderer frameRenderer;
        public Renderer panelRenderer;
        public Transform icon;

        public PickupKind Kind { get; private set; }
        public int Value { get; private set; }
        public WeaponDef Weapon { get; private set; }
        public bool High { get; private set; }
        public bool Dead { get; private set; }
        public float X, Z;

        int baseValue;
        float hitAcc, pulse, seed;

        public float CenterAlt => High ? GameManager.I.config.altitudeSplit + 0.2f + 2.05f : 2.05f;

        public void Init(PickupKind kind, int value, WeaponDef weapon, bool high, float x, float z)
        {
            Kind = kind; Value = baseValue = value; Weapon = weapon; High = high; X = x; Z = z;
            hitAcc = 0f; pulse = 0f; seed = Random.value * 10f; Dead = false;
            Color c = ColorFor();
            if (frameRenderer != null) frameRenderer.material.color = c;
            if (panelRenderer != null) { var pc = c; pc.a = 0.35f; panelRenderer.material.color = pc; }
            if (label != null) { label.text = Label(); label.color = kind == PickupKind.Plus || kind == PickupKind.X2 ? Color.white : c; }
            if (hint != null) hint.text = kind == PickupKind.Plus ? "SHOOT ME" : "";
            if (icon != null) icon.gameObject.SetActive(false);
            UpdateTransform();
        }

        public Color ColorFor()
        {
            switch (Kind)
            {
                case PickupKind.Weapon: return Weapon != null ? Weapon.color : Color.white;
                case PickupKind.Shield: return new Color(0.58f, 0.77f, 0.99f);
                case PickupKind.Bomb: return new Color(1f, 0.82f, 0.25f);
                default: return new Color(0.37f, 0.69f, 1f);
            }
        }

        public string Label()
        {
            switch (Kind)
            {
                case PickupKind.Plus: return "+" + Value;
                case PickupKind.X2: return "x2";
                case PickupKind.Shield: return "SHIELD";
                case PickupKind.Bomb: return "BOMB";
                default: return Weapon != null ? Weapon.displayName : "AMMO";
            }
        }

        void Update()
        {
            var gm = GameManager.I;
            if (Dead || gm == null || gm.State != GameState.Playing) return;
            float dt = Time.deltaTime;
            Z -= gm.ScrollSpeed * dt;
            pulse = Mathf.Max(0f, pulse - dt);
            UpdateTransform();
            if (label != null) label.text = Label();
            if (Z <= 0.6f)
            {
                var sq = gm.squad;
                if (Mathf.Abs(X - sq.X) < 3.1f && sq.IsHigh == High) Collect();
                else
                {
                    Dead = true;
                    if (Kind == PickupKind.Plus || Kind == PickupKind.X2)
                        FXManager.I.FloatText(new Vector3(X, 3f, 0f), "missed", new Color(0.81f, 0.9f, 1f), 0.5f);
                    PickupSpawner.I.Release(this);
                }
            }
        }

        void UpdateTransform()
        {
            float baseY = High ? 1f + GameManager.I.config.altitudeSplit + 0.2f : 1f;
            transform.position = new Vector3(X, baseY + Mathf.Sin(Time.time * 2.2f + seed) * 0.2f, Z);
            transform.localScale = Vector3.one * (1f + pulse * 1.5f);
        }

        /// <summary>Called by AutoFire while the gate is in the line of fire.</summary>
        public void Shoot(float dmg)
        {
            pulse = Mathf.Max(pulse, 0.1f);
            if (Kind == PickupKind.Plus)
            {
                hitAcc += dmg;
                while (hitAcc >= 2.5f && Value < baseValue * 3) { hitAcc -= 2.5f; Value++; pulse = 0.15f; }
            }
            else if (Kind == PickupKind.Shield)
            {
                hitAcc += dmg;
                while (hitAcc >= 4f && Value < 60) { hitAcc -= 4f; Value += 2; pulse = 0.15f; }
            }
        }

        void Collect()
        {
            Dead = true;
            var gm = GameManager.I;
            var sq = gm.squad;
            var fx = FXManager.I;
            Vector3 p = sq.transform.position + Vector3.up * 2.6f;
            Color blue = new Color(0.37f, 0.69f, 1f), cyan = new Color(0.55f, 0.91f, 1f);
            switch (Kind)
            {
                case PickupKind.Plus:
                    sq.Grow(Value); gm.AddCoins(Value);
                    fx.FloatText(p, "+" + Value + " PLANES", blue, 1.1f);
                    fx.Sparks(sq.transform.position, cyan, 12);
                    AudioManager.I.Play(Sfx.Good);
                    break;
                case PickupKind.X2:
                    sq.SetCount(sq.Count * 2);
                    fx.FloatText(p, "x2!", cyan, 1.5f);
                    fx.Ring(sq.transform.position, cyan, 12f);
                    fx.Flash(blue, 0.15f);
                    gm.hud.Banner("x2 SQUADRON!", cyan, 1f);
                    AudioManager.I.Play(Sfx.Big);
                    break;
                case PickupKind.Shield:
                    sq.AddShield(Value);
                    fx.FloatText(p, "SHIELD +" + Value, new Color(0.58f, 0.77f, 0.99f), 1f);
                    fx.Ring(sq.transform.position, new Color(0.58f, 0.77f, 0.99f), 7f);
                    AudioManager.I.Play(Sfx.Pickup);
                    break;
                case PickupKind.Bomb:
                    gm.Detonate();
                    break;
                case PickupKind.Weapon:
                    sq.SetWeapon(Weapon);
                    fx.FloatText(p, Weapon.displayName + "!", Weapon.color, 1f);
                    fx.Ring(sq.transform.position, Weapon.color, 9f);
                    AudioManager.I.Play(Sfx.Pickup);
                    break;
            }
            PickupSpawner.I.Release(this);
        }
    }
}
