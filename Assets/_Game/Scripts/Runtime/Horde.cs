// Horde.cs
// One cluster of enemy units flying at the squad. It has a unit count (the number
// over its head), homes in on the player, and rams the squad if it arrives alive.
using System.Collections.Generic;
using UnityEngine;

namespace SkySquad
{
    public class Horde : MonoBehaviour
    {
        public TMPro.TextMeshPro label;
        public Transform unitsRoot;

        public HordeKindDef Kind { get; private set; }
        public int Units { get; private set; }
        public float Hp { get; private set; }
        public float HalfWidth { get; private set; }
        public bool Dead { get; private set; }
        public float X, Z, Alt;

        readonly List<Transform> units = new List<Transform>();
        readonly List<Vector3> slots = new List<Vector3>();
        float seed, flashT;
        int units0;

        public void Init(HordeKindDef kind, int n, float x, float z, float alt)
        {
            Kind = kind;
            Units = units0 = Mathf.Max(2, n);
            Hp = Units * kind.unitHp;
            X = x; Z = z; Alt = alt;
            seed = Random.value * 10f;
            Dead = false;
            int rows = Mathf.CeilToInt((Mathf.Sqrt(8f * Mathf.Min(Units, 36) + 1f) - 1f) / 2f);
            HalfWidth = 1.5f + rows * 0.6f;
            BuildSlots();
            RebuildUnits();
            UpdateTransform();
        }

        void BuildSlots()
        {
            slots.Clear();
            slots.Add(Vector3.zero);
            for (int k = 1; slots.Count < 36; k++)
                for (int j = 0; j <= k && slots.Count < 36; j++)
                    slots.Add(new Vector3((j - k / 2f) * 1.3f, 0f, k * 1.0f)); // wedge: leader closest to the player
        }

        void RebuildUnits()
        {
            int want = Mathf.Min(Units, 36);
            while (units.Count < want)
            {
                var go = Instantiate(Kind.unitPrefab, unitsRoot != null ? unitsRoot : transform);
                go.transform.localScale = Vector3.one * Kind.unitScale;
                units.Add(go.transform);
            }
            for (int i = 0; i < units.Count; i++)
            {
                bool on = i < want;
                units[i].gameObject.SetActive(on);
                if (on) units[i].localPosition = slots[i];
            }
            if (label != null) label.text = Units.ToString();
        }

        void Update()
        {
            var gm = GameManager.I;
            if (Dead || gm == null || gm.State != GameState.Playing) return;
            float dt = Time.deltaTime;
            var sq = gm.squad;
            Z -= (gm.ScrollSpeed + Kind.approachSpeed) * dt;
            X += Mathf.Clamp(sq.X - X, -1f, 1f) * 1.3f * dt;
            Alt += Mathf.Clamp(sq.Alt - Alt, -1f, 1f) * 1.0f * dt;
            flashT = Mathf.Max(0f, flashT - dt);
            UpdateTransform();
            for (int i = 0; i < units.Count; i++)
            {
                if (!units[i].gameObject.activeSelf) continue;
                units[i].localPosition = slots[i] + Vector3.up * (Mathf.Sin(Time.time * 7f + i * 1.7f + seed) * 0.12f);
                units[i].localRotation = Quaternion.Euler(0f, 0f, Mathf.Sin(Time.time * 3f + i + seed) * 7f);
            }
            if (label != null)
            {
                bool near = Z < 30f;
                label.color = near && ((int)(Time.time * 6f)) % 2 == 0 ? new Color(1f, 0.23f, 0.31f) : Color.white;
            }
            if (Z <= 0.4f)
            {
                Dead = true;
                int dmg = Units * Kind.contactPower;
                FXManager.I.Explosion(sq.transform.position, dmg > 8);
                sq.Damage(dmg, Kind.displayName.ToLower() + " crashed into the squad (" + dmg + " planes).");
                HordeSpawner.I.Release(this);
            }
        }

        void UpdateTransform()
        {
            transform.position = new Vector3(X, 1f + Alt, Z);
            float s = flashT > 0f ? 1.12f : 1f;
            transform.localScale = new Vector3(s, s, s);
        }

        public void TakeDamage(float dmg)
        {
            if (Dead) return;
            int before = Mathf.CeilToInt(Hp / Kind.unitHp);
            Hp -= dmg;
            int after = Mathf.Max(0, Mathf.CeilToInt(Hp / Kind.unitHp));
            if (after < before)
            {
                flashT = 0.06f;
                GameManager.I.UnitsKilled += before - after;
                int k = Mathf.Min(4, before - after);
                for (int i = 0; i < k; i++)
                {
                    int idx = Mathf.Clamp(before - 1 - i, 0, slots.Count - 1);
                    Vector3 wp = transform.TransformPoint(slots[idx]);
                    FXManager.I.UnitFall(Kind.unitPrefab, wp, Kind.unitScale);
                    FXManager.I.Sparks(wp, new Color(1f, 0.62f, 0.1f), 3);
                }
                AudioManager.I.Play(Sfx.Unit);
                Units = after;
                RebuildUnits();
            }
            if (Hp <= 0f) Kill(false);
        }

        public void Kill(bool silent)
        {
            if (Dead) return;
            Dead = true;
            GameManager.I.AddCoins(units0);
            if (!silent)
            {
                FXManager.I.Explosion(transform.position, Kind.id == "bomber");
                FXManager.I.FloatText(transform.position + Vector3.up * 1.5f, "CLEARED", new Color(1f, 0.82f, 0.25f), 0.7f);
                AudioManager.I.Play(Sfx.Explode);
            }
            HordeSpawner.I.Release(this);
        }
    }
}
