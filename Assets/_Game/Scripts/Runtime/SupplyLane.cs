// SupplyLane.cs
// The LOW band's conveyor: a short queue of crates flying a fixed distance ahead of the squad, each
// with an upgrade gate riding right behind it. The crate is the barrier: shoot it down (its hp in
// coins) and its gate shoots forward at the squad - fly through it for the planes. What each crate
// is and what rides behind it comes from a fixed table (GameConfig.crates: 15/+2, 275/+2, 780 with
// the next plane on top/+3, ...); past the table the hp keeps growing. The rest slide forward and a
// new crate+gate pair joins at the back.
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
            if (gm == null || gm.State != GameState.Playing) return;
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
            {   // the planes ride behind the crate as a gate; the crate is the barrier
                var g = Instantiate(gatePrefab, transform).GetComponent<UpgradeGate>();
                g.Init(GateKind.Planes, planes);
                gates.Add(g);
                b.Gate = g;
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

        public void Release(Breakable b)
        {
            active.Remove(b);
            if (b != null)
            {
                if (b.Gate != null) { ReleaseGate(b.Gate); b.Gate = null; }   // removed without breaking (level reset): its gate goes too
                Destroy(b.gameObject);
            }
            for (int i = 0; i < active.Count; i++) active[i].SetSlot(i);
        }
    }
}
