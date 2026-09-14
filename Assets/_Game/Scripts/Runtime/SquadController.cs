// SquadController.cs
// The player. Holds the plane count, shield and current weapon, moves the formation
// with the finger, and spawns/removes the visible plane models to match the count.
// The squad always sits at z = 0; the world moves toward it.
using System;
using System.Collections.Generic;
using UnityEngine;

namespace SkySquad
{
    public class SquadController : MonoBehaviour
    {
        public GameConfig config;
        public SquadInput input;
        public Transform formationRoot;
        public TMPro.TextMeshPro countLabel;
        public TMPro.TextMeshPro shieldLabel;
        public GameObject shieldBubble;
        public Material leaderMaterial;

        public int Count { get; private set; }
        public int Shield { get; private set; }
        public WeaponDef Weapon { get; private set; }
        public float X { get; private set; }
        public float Alt { get; private set; }
        public float XVel { get; private set; }
        public float AltVel { get; private set; }
        public bool IsHigh => Alt >= config.altitudeSplit;
        public float Dps => (config.baseDps + Count * config.dpsPerPlane) * (Weapon != null ? Weapon.dpsMultiplier : 1f);
        public int VisibleCount => Mathf.Min(Count, slots.Count);
        public GameObject CurrentPlanePrefab => currentPlanePrefab;

        // AutoPilot hooks: when AutoInput is true the bot steers instead of the finger.
        [NonSerialized] public bool AutoInput;
        [NonSerialized] public Vector2 AutoAxis;

        public event Action<int, int> OnCountChanged; // (before, after)

        readonly List<PlaneVisual> planes = new List<PlaneVisual>();
        readonly List<Vector3> slots = new List<Vector3>();
        GameObject currentPlanePrefab;
        float pillPop, introT, muzzleT;

        void Awake() { BuildSlots(); }

        void BuildSlots()
        {
            slots.Clear();
            slots.Add(Vector3.zero);
            for (int k = 1; slots.Count < config.maxVisiblePlanes; k++)
                for (int j = 0; j <= k && slots.Count < config.maxVisiblePlanes; j++)
                    slots.Add(new Vector3((j - k / 2f) * 0.92f, 0f, -k * 0.72f));
        }

        public void ResetForLevel(int startCount)
        {
            X = 0f; Alt = 1.5f; XVel = AltVel = 0f; Shield = 0; introT = 0.9f;
            SetWeapon(config.weapons[0]);
            SetCount(startCount, false);
            UpdateTransform();
        }

        public Vector3 SlotWorld(int i)
        {
            i = Mathf.Clamp(i, 0, slots.Count - 1);
            return formationRoot.TransformPoint(slots[i]);
        }
        public Vector3 SlotLocal(int i) => slots[Mathf.Clamp(i, 0, slots.Count - 1)];

        void Update()
        {
            var gm = GameManager.I;
            float dt = Time.deltaTime;
            introT = Mathf.Max(0f, introT - dt);
            pillPop = Mathf.Max(0f, pillPop - dt);
            muzzleT = Mathf.Max(0f, muzzleT - dt);
            if (gm == null || gm.State != GameState.Playing) { UpdateTransform(); return; }

            float ox = X, oa = Alt;
            Vector2 axis = AutoInput ? AutoAxis : input.KeyAxis;
            Vector2 drag = AutoInput ? Vector2.zero : input.DragDelta;
            X = Mathf.Clamp(X + axis.x * config.steerSpeed * dt + drag.x * config.dragUnitsPerScreen, -config.laneHalfWidth, config.laneHalfWidth);
            Alt = Mathf.Clamp(Alt + axis.y * config.climbSpeed * dt + drag.y * config.dragUnitsPerScreen, 0f, config.altitudeMax);
            float k = 1f - Mathf.Pow(0.001f, dt);
            XVel = Mathf.Lerp(XVel, (X - ox) / Mathf.Max(dt, 0.001f), k);
            AltVel = Mathf.Lerp(AltVel, (Alt - oa) / Mathf.Max(dt, 0.001f), k);
            UpdateTransform();
        }

        void UpdateTransform()
        {
            float e = introT > 0f ? 1f - Mathf.Pow(1f - Mathf.Clamp01(1f - introT / 0.9f), 3f) : 1f;
            transform.position = new Vector3(X, 1f + Alt - (1f - e) * 8f, 0f);
            float bank = Mathf.Clamp(-XVel * 2.5f, -30f, 30f);
            float pitch = Mathf.Clamp(-AltVel * 2f, -18f, 18f);
            formationRoot.localRotation = Quaternion.Euler(pitch, 0f, bank);
            if (countLabel != null)
            {
                countLabel.text = Count.ToString();
                countLabel.transform.localScale = Vector3.one * (1f + pillPop * 1.2f);
            }
            if (shieldLabel != null) shieldLabel.text = Shield > 0 ? "SHIELD " + Shield : "";
            if (shieldBubble != null) shieldBubble.SetActive(Shield > 0);
        }

        public void SetCount(int c, bool animate = true)
        {
            int before = Count;
            Count = Mathf.Max(0, c);
            pillPop = 0.25f;
            RebuildPlanes();
            OnCountChanged?.Invoke(before, Count);
            if (animate && FXManager.I != null)
            {
                if (Count > before) FXManager.I.Joiners(this, before, Count);
                else if (Count < before) FXManager.I.Fallers(this, before, Count);
            }
        }

        public void Grow(int n) => SetCount(Count + n);
        public void AddShield(int n) { Shield += n; }

        public void SetWeapon(WeaponDef w)
        {
            Weapon = w;
            if (currentPlanePrefab != w.planePrefab)
            {
                currentPlanePrefab = w.planePrefab;
                foreach (var p in planes) if (p != null) Destroy(p.gameObject);
                planes.Clear();
                RebuildPlanes();
            }
        }

        void RebuildPlanes()
        {
            if (currentPlanePrefab == null) return;
            int want = VisibleCount;
            while (planes.Count < want)
            {
                var go = Instantiate(currentPlanePrefab, formationRoot);
                go.name = "Plane" + planes.Count;
                var pv = go.GetComponent<PlaneVisual>();
                if (pv == null) pv = go.AddComponent<PlaneVisual>();
                pv.leaderMaterial = leaderMaterial;
                planes.Add(pv);
            }
            for (int i = 0; i < planes.Count; i++)
            {
                bool on = i < want;
                planes[i].gameObject.SetActive(on);
                if (on)
                {
                    planes[i].index = i;
                    planes[i].SetBase(slots[i]);
                    planes[i].SetLeader(i == 0);
                }
            }
        }

        public void MuzzleFlash()
        {
            muzzleT = 0.06f;
            for (int i = 0; i < Mathf.Min(6, planes.Count); i++) planes[i].Flash(Weapon.color);
        }

        public void Damage(int dmg, string reason)
        {
            if (dmg <= 0) return;
            var fx = FXManager.I;
            Vector3 p = transform.position;
            if (Shield > 0)
            {
                int ab = Mathf.Min(Shield, dmg);
                Shield -= ab; dmg -= ab;
                fx.Ring(p + Vector3.up * 0.5f, new Color(0.58f, 0.77f, 0.99f), 3f);
                fx.FloatText(p + Vector3.up * 3.2f, "SHIELD -" + ab, new Color(0.58f, 0.77f, 0.99f), 0.8f);
                AudioManager.I.Play(Sfx.ShieldHit);
            }
            if (dmg <= 0) return;
            SetCount(Count - dmg);
            fx.FloatText(p + Vector3.up * 2.6f, "-" + dmg, new Color(1f, 0.23f, 0.31f), 1.3f);
            fx.Flash(new Color(1f, 0.23f, 0.31f), 0.22f);
            fx.Shake(0.3f);
            AudioManager.I.Play(Sfx.Bad);
            if (Count <= 0) GameManager.I.Lose(reason);
        }
    }
}
