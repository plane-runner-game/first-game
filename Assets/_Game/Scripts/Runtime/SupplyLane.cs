// SupplyLane.cs
// The LOW band's conveyor: a short queue of crates flying a fixed distance ahead of the squad, each
// with its reward riding right behind it as +1 gates, one behind the other. The crate is the barrier: shoot it down (its hp in
// coins) and its gates shoot forward at the squad - fly through them, +1 plane each. What each crate
// is and what rides behind it comes from a fixed table (GameConfig.crates: 15/+2, 275/+2, 780 with
// the next plane on top/+3, ...); past the table the hp keeps growing. The rest slide forward and a
// new crate with its gates joins at the back.
using System.Collections.Generic;
using UnityEngine;

namespace SkySquad
{
    public class SupplyLane : MonoBehaviour
    {
        public static SupplyLane I { get; private set; }
        public GameObject breakablePrefab;
        public GameObject gatePrefab;

        readonly List<Breakable> active = new List<Breakable>();   // front first
        readonly List<UpgradeGate> gates = new List<UpgradeGate>();  // waiting behind their crates or flying at the squad
        WeaponDef queuedWeapon;                                      // the plane the last weapon crate in the queue holds (the queue is spawned ahead of the squad taking them)
        int level = 1, nextIndex;

        public IReadOnlyList<Breakable> Active => active;
        public Breakable Front => active.Count > 0 ? active[0] : null;

        void Awake() { I = this; }

        public void ResetForLevel(int n)
        {
            level = n;
            queuedWeapon = null;
            foreach (var b in active) if (b != null) Destroy(b.gameObject);
            active.Clear();
            foreach (var g in gates) if (g != null) Destroy(g.gameObject);
            gates.Clear();
            nextIndex = 0;
        }

        void Update()
        {
            var gm = GameManager.I;
            if (gm == null || (gm.State != GameState.Playing && gm.State != GameState.Title)) return;   // Title too: the lobby shows the armed level with its crate queue ahead (2026-09-19)
            while (active.Count < gm.config.supplyVisible) SpawnNext();
        }

        public void ReleaseGate(UpgradeGate g)
        {
            gates.Remove(g);
            if (g != null) Destroy(g.gameObject);
        }

        void SpawnNext()
        {
            var gm = GameManager.I;
            var cfg = gm.config;
            int idx = nextIndex++;
            // the row of the table this crate is; past the table: the last row, tougher by crateHpGrowthAfter per crate
            var table = cfg.crates;
            float hp = 15f; int planes = 2; bool wantWeapon = false;
            if (table != null && table.Length > 0)
            {
                var row = table[Mathf.Min(idx, table.Length - 1)];
                hp = row.hp; planes = row.planes;
                if (idx < table.Length) wantWeapon = row.weapon;
                else hp *= Mathf.Pow(Mathf.Max(1f, cfg.crateHpGrowthAfter), idx - table.Length + 1);
            }
            hp = Mathf.Round(hp * Mathf.Pow(cfg.boxHpPerLevel, level - 1));
            WeaponDef weapon = null;
            if (wantWeapon)
            {   // the next plane up from the last one queued (the whole queue is spawned before the squad takes any of them)
                weapon = NextWeapon(queuedWeapon != null ? queuedWeapon : gm.squad.Weapon);
                if (weapon != null) queuedWeapon = weapon;
            }
            BreakableKind kind = weapon != null ? BreakableKind.Weapon : BreakableKind.Box;
            var go = Instantiate(breakablePrefab, transform);
            var b = go.GetComponent<Breakable>();
            if (cfg.gatesEnabled && gatePrefab != null && planes > 0)
            {   // the planes ride behind the crate as gates of +1 one behind the other (requested: "+5 = five come one behind the other, +1 each"); the crate is the barrier
                for (int i = 0; i < planes; i++)
                {
                    var g = Instantiate(gatePrefab, transform).GetComponent<UpgradeGate>();
                    g.Init(GateKind.Planes, 1);
                    gates.Add(g);
                    b.Gates.Add(g);
                }
            }
            b.Init(kind, cfg.gatesEnabled ? 0 : planes, weapon, Mathf.Max(1f, hp), active.Count);   // with gates on the crate pays coins only (its gate pays the planes); Init -> SetSlot places the gate
            active.Add(b);
        }

        /// <summary>Weapons are ordered weakest to strongest in the config; a crate or gate always holds the next one up.</summary>
        public WeaponDef NextWeapon(WeaponDef current)
        {
            var ws = GameManager.I.config.weapons;
            int i = System.Array.IndexOf(ws, current);
            return i >= 0 && i + 1 < ws.Length ? ws[i + 1] : null;
        }

        /// <summary>Where queue slot i holds: supplyFrontZ, then every crate ahead of it takes supplySpacing plus gateStep per gate it carries, so a crate's gates fit behind it.</summary>
        public float SlotZ(int slot)
        {
            var cfg = GameManager.I.config;
            float z = cfg.supplyFrontZ;
            for (int i = 0; i < slot && i < active.Count; i++) z += cfg.supplySpacing + cfg.gateStep * active[i].Gates.Count;
            for (int i = active.Count; i < slot; i++) z += cfg.supplySpacing;
            return z;
        }

        public void Release(Breakable b)
        {
            active.Remove(b);
            if (b != null)
            {
                foreach (var g in b.Gates) ReleaseGate(g);   // removed without breaking (level reset): its gates go too
                b.Gates.Clear();
                Destroy(b.gameObject);
            }
            for (int i = 0; i < active.Count; i++) active[i].SetSlot(i);
        }
    }
}
