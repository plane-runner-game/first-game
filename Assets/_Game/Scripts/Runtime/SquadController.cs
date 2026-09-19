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
        public float Z { get; private set; }           // world z of the squad: 0 at the ceiling, config.diveForward at altitude 0 (the dive pushes it ahead so it stays above the thumb; the strike line, gates and guns are measured from here)
        public float XVel { get; private set; }
        public float AltVel { get; private set; }
        public bool IsHigh => Alt >= config.altitudeSplit;
        public int PowerTier { get; set; }             // upgrade gates passed beyond the last weapon: each adds config.gatePowerBonus damage
        public float PowerMult => 1f + PowerTier * config.gatePowerBonus;
        public float Dps => Weapon != null ? Count * Weapon.damage * Progress.DamageMult * PowerMult / Mathf.Max(0.02f, Weapon.fireInterval / Progress.FireRateMult) : 0f;   // one bullet per plane per volley
        public int VisibleCount => Mathf.Min(Count, config.maxVisiblePlanes);
        public GameObject CurrentPlanePrefab => currentPlanePrefab;

        // AutoPilot hooks: when AutoInput is true the bot steers instead of the finger.
        [NonSerialized] public bool AutoInput;
        [NonSerialized] public Vector2 AutoAxis;
        [NonSerialized] public int FallSlot = -1;   // set by a strike: the plane at this slot is the one that tumbles (else the last one)

        public event Action<int, int> OnCountChanged; // (before, after)

        readonly List<PlaneVisual> planes = new List<PlaneVisual>();
        readonly List<Vector3> slots = new List<Vector3>();
        GameObject currentPlanePrefab;
        float pillPop, introT, muzzleT, shotAcc;

        void Awake() { BuildSlots(1); }

        /// <summary>Formation for n visible planes. Up to 5: an inverted V, the leader at the apex and each
        /// pair of wingmen one row back and one step out. Beyond that: a phyllotaxis spiral (r = c*sqrt(i),
        /// theta = i * golden angle) - packed, symmetric, and it only grows like sqrt(n).</summary>
        void BuildSlots(int n)
        {
            slots.Clear();
            n = Mathf.Max(1, n);
            if (n <= 5)
            {
                float dx = config.formationSpacingX, dz = config.formationSpacingZ;
                for (int i = 0; i < n; i++)
                {
                    int k = (i + 1) / 2;                       // ceil(i/2)
                    float side = i % 2 == 0 ? 1f : -1f;        // (-1)^i
                    slots.Add(new Vector3(side * k * dx, 0f, -k * dz));
                }
            }
            else
            {
                float c = config.spiralSpacing;
                for (int i = 0; i < n; i++)
                {
                    float r = c * Mathf.Sqrt(i), a = i * 2.39996f;
                    slots.Add(new Vector3(Mathf.Cos(a) * r, 0f, Mathf.Sin(a) * r * 0.8f - 0.2f));
                }
            }
        }

        public void ResetForLevel(int startCount)
        {
            X = 0f; Alt = 0f; XVel = AltVel = 0f; Shield = 0; introT = 0.9f; shotAcc = 0f; PowerTier = 0;   // start at the BOTTOM, the crates' band (2026-09-19, "start from the bottom not top"; the ceiling, the enemies' altitude, before that; supplyAlt earlier still)   // (was: start up in the HIGH band at the enemies' altitude (was supplyAlt, down at the crates: "the plane should go for the planes first, not the boxes below", 2026-09-17)
            SetWeapon(config.weapons[0]);
            SetCount(startCount, false);
            UpdateTransform();
        }

        Camera cam; CameraFollow camFollow;

        /// <summary>How far sideways the squad may go: the lane, but stopped earlier when the outer plane of the formation
        /// would leave the screen (the camera follows only followX of the squad's X, so a wide formation reaches the edge first),
        /// never short of laneReachMin ("stop me before the planes leave the screen", 2026-09-18).</summary>
        public float XLimit()
        {
            float lane = config.laneHalfWidth;
            if (cam == null) { cam = Camera.main; if (cam != null) camFollow = cam.GetComponentInParent<CameraFollow>(); }
            if (cam == null || camFollow == null || camFollow.followX >= 0.999f) return lane;
            Vector3 local = cam.transform.InverseTransformPoint(new Vector3(cam.transform.position.x, transform.position.y, transform.position.z));
            float half = Mathf.Max(0.1f, local.z) * Mathf.Tan(cam.fieldOfView * 0.5f * Mathf.Deg2Rad) * cam.aspect;   // visible half-width at the squad's depth
            float reach = 0f;
            int n = Mathf.Min(VisibleCount, slots.Count);
            for (int i = 0; i < n; i++) reach = Mathf.Max(reach, Mathf.Abs(slots[i].x));
            reach += config.planeHalfWidth;
            float limit = (half - reach) / (1f - camFollow.followX);   // at rest the rig sits at followX * X, so the edge is at followX * X + half
            return Mathf.Clamp(limit, Mathf.Min(config.laneReachMin, lane), lane);
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
            float dragUnits = Settings.DragUnits(config);   // the player's "plane speed" setting, else config.dragUnitsPerScreen
            float speed = config.dragUnitsPerScreen > 0f ? dragUnits / config.dragUnitsPerScreen : 1f;   // the same setting scales the keyboard steer/climb, so "speed" means every direction
            float xLimit = XLimit();
            float hard = Mathf.Max(xLimit, Mathf.Abs(X));   // already past the limit (the formation just grew): no further out, eased back below
            X = Mathf.Clamp(X + axis.x * config.steerSpeed * speed * dt + drag.x * dragUnits, -hard, hard);
            if (Mathf.Abs(X) > xLimit) X = Mathf.MoveTowards(X, Mathf.Sign(X) * xLimit, 6f * dt);
            Alt = Mathf.Clamp(Alt + axis.y * config.climbSpeed * speed * dt + drag.y * dragUnits, 0f, config.altitudeMax);
            float k = 1f - Mathf.Pow(0.001f, dt);
            XVel = Mathf.Lerp(XVel, (X - ox) / Mathf.Max(dt, 0.001f), k);
            AltVel = Mathf.Lerp(AltVel, (Alt - oa) / Mathf.Max(dt, 0.001f), k);
            UpdateTransform();
        }

        void UpdateTransform()
        {
            float e = introT > 0f ? 1f - Mathf.Pow(1f - Mathf.Clamp01(1f - introT / 0.9f), 3f) : 1f;
            Z = config.altitudeMax > 0f ? (1f - Mathf.Clamp01(Alt / config.altitudeMax)) * config.diveForward : 0f;
            transform.position = new Vector3(X, 1f + Alt - (1f - e) * 8f, Z);
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
            BuildSlots(VisibleCount);
            RebuildPlanes();
            OnCountChanged?.Invoke(before, Count);
            if (animate && FXManager.I != null)
            {
                if (Count > before) FXManager.I.Joiners(this, before, Count);
                else if (Count < before) FXManager.I.Fallers(this, before, Count);
            }
            FallSlot = -1;
        }

        public void Grow(int n) => SetCount(Count + n);
        public void AddShield(int n) { Shield += n; }
        public void SetShield(int n) { Shield = Mathf.Max(Shield, n); }   // a gate shield: fresh 5 hits, never less than what is left

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
            planes.RemoveAll(p => p == null);   // survives a domain reload in play mode (editor only) without throwing on destroyed planes
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

        /// <summary>Enemy fire from the parked crowd: fractions of a plane add up until one falls.</summary>
        public void TakeShot(float planes, string reason)
        {
            shotAcc += planes;
            int n = Mathf.FloorToInt(shotAcc);
            if (n <= 0) return;
            shotAcc -= n;
            Damage(n, reason);
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
            if (dmg <= 0) { FallSlot = -1; return; }   // the shield took it all: no plane falls (and no stale strike slot)
            SetCount(Count - dmg);
            fx.FloatText(p + Vector3.up * 2.6f, "-" + dmg, new Color(1f, 0.23f, 0.31f), 1.3f);
            fx.Flash(new Color(1f, 0.23f, 0.31f), 0.22f);
            fx.Shake(0.3f);
            AudioManager.I.Play(Sfx.Bad);
            if (Count <= 0) GameManager.I.Lose(reason);
        }
    }
}
