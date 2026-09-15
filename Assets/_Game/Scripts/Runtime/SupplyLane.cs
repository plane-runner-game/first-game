// SupplyLane.cs
// The LOW band's conveyor: a short queue of crates flying a fixed distance ahead of the squad, each
// with an upgrade gate riding right behind it. The crate is the barrier: shoot it down (its hp in
// coins) and its gate shoots forward at the squad - fly through it for the reward: +2 or +5 planes,
// or, rarely, a shield / the next plane (a weighted seeded roll per crate). The rest slide
// forward and a new crate+gate pair joins at the back. Every crate is tougher than the last.
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
        System.Random rng = new System.Random(11);                   // the gate rolls: the same every attempt
        int level = 1, nextIndex, boxIndex;

        public IReadOnlyList<Breakable> Active => active;
        public Breakable Front => active.Count > 0 ? active[0] : null;

        void Awake() { I = this; }

        public void ResetForLevel(int n)
        {
            level = n;
            rng = new System.Random(11);
            foreach (var b in active) if (b != null) Destroy(b.gameObject);
            active.Clear();
            foreach (var g in gates) if (g != null) Destroy(g.gameObject);
            gates.Clear();
            nextIndex = boxIndex = 0;
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
            BreakableKind kind = BreakableKind.Box;
            WeaponDef weapon = null;
            bool weaponSlot = cfg.weaponAt >= 0 && idx >= cfg.weaponAt && (idx - cfg.weaponAt) % Mathf.Max(1, cfg.weaponEvery) == 0;   // weaponAt < 0 = no weapon crates
            if (weaponSlot) weapon = NextWeapon(gm.squad.Weapon);
            if (weapon != null) kind = BreakableKind.Weapon;
            float hp = Mathf.Round(cfg.boxHpBase * Mathf.Pow(cfg.boxHpPerLevel, level - 1) * Mathf.Pow(cfg.boxHpGrowth, boxIndex));
            if (kind == BreakableKind.Box) boxIndex++;   // weapon crates don't climb the ladder...
            else hp = Mathf.Round(hp * 0.5f);            // ...and are cheap, so they don't block the +planes crates behind them for long
            var go = Instantiate(breakablePrefab, transform);
            var b = go.GetComponent<Breakable>();
            if (cfg.gatesEnabled && gatePrefab != null && kind == BreakableKind.Box)
            {   // what rides behind this crate: one weighted, seeded roll - nothing (coins only, common), +2 (ordinary),
                // a shield (uncommon), +5 (rare), the next plane (very rare)
                float wEmpty = Mathf.Max(0f, cfg.gateWeightEmpty), wSmall = Mathf.Max(0f, cfg.gateWeightSmall), wShield = Mathf.Max(0f, cfg.gateWeightShield), wBig = Mathf.Max(0f, cfg.gateWeightBig), wPlane = Mathf.Max(0f, cfg.gateWeightPlane);
                float r = (float)rng.NextDouble() * (wEmpty + wSmall + wShield + wBig + wPlane);
                GateKind gk = GateKind.Planes; int amount = 0;
                if (r < wEmpty) amount = 0;
                else if ((r -= wEmpty) < wSmall) amount = cfg.gatePlanesSmall;
                else if ((r -= wSmall) < wShield) { gk = GateKind.Shield; amount = rng.Next(cfg.gateShieldMin, cfg.gateShieldMax + 1); }   // 1..3 hits
                else if ((r -= wShield) < wBig) amount = cfg.gatePlanesBig;
                else gk = GateKind.Plane;
                if (boxIndex == 1) { gk = GateKind.Planes; amount = cfg.gatePlanesSmall; }   // the first crate of an attempt always carries +2: the opening is "break it, take two planes"
                if (gk != GateKind.Planes || amount > 0)
                {
                    var g = Instantiate(gatePrefab, transform).GetComponent<UpgradeGate>();
                    g.Init(gk, amount);
                    gates.Add(g);
                    b.Gate = g;
                }
            }
            b.Init(kind, cfg.gatesEnabled ? 0 : cfg.boxPlanes, weapon, Mathf.Max(1f, hp), active.Count);   // with gates on the crate pays coins only (its gate pays the planes); Init -> SetSlot places the gate
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
