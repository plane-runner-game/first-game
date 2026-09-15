// SupplyLane.cs
// The LOW band's conveyor: a queue of crates flying a fixed distance ahead of the squad, each with
// its reward squares riding behind it. Crate n's number and reward come straight from the crate
// table (GameConfig.crates - the same every attempt); past the table the numbers keep climbing.
// Shoot the front crate down (coins) and its squares shoot forward at the squad - fly through
// them for the planes / shield / next plane. The rest slide forward and a new crate joins at the back.
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
        int nextIndex;

        public IReadOnlyList<Breakable> Active => active;
        public Breakable Front => active.Count > 0 ? active[0] : null;
        /// <summary>Squares launched and still on their way: the bot stays low for them.</summary>
        public int Incoming { get { int n = 0; foreach (var g in gates) if (g != null && g.Launched && !g.Done && g.Z > -1f) n++; return n; } }

        void Awake() { I = this; }

        public void ResetForLevel(int n)
        {
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
            var spec = cfg.CrateAt(idx);
            var go = Instantiate(breakablePrefab, transform);
            var b = go.GetComponent<Breakable>();
            if (cfg.gatesEnabled && gatePrefab != null && spec.reward != CrateReward.Coins && spec.amount > 0)
            {   // one square per plane (rows of two behind the crate); a shield or a new plane is a single square
                int n = spec.reward == CrateReward.Planes ? spec.amount : 1;
                for (int i = 0; i < n; i++)
                {
                    bool pair = n - (i / 2) * 2 >= 2;                                   // this row has two squares: left and right
                    float x = pair ? (i % 2 == 0 ? -cfg.squareSideStep : cfg.squareSideStep) : 0f;
                    var g = Instantiate(gatePrefab, transform).GetComponent<UpgradeGate>();
                    g.Init(spec.reward, spec.reward == CrateReward.Planes ? 1 : spec.amount, x);
                    gates.Add(g);
                    b.Squares.Add(g);
                }
            }
            b.Init(idx, spec.hp, spec.reward, spec.amount, active.Count);   // Init -> SetSlot places the crate and its squares
            active.Add(b);
        }

        /// <summary>Weapons are ordered weakest to strongest in the config; a new-plane square always holds the next one up.</summary>
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
                foreach (var g in b.Squares) ReleaseGate(g);   // removed without breaking (level reset): its squares go too
                b.Squares.Clear();
                Destroy(b.gameObject);
            }
            for (int i = 0; i < active.Count; i++) active[i].SetSlot(i);
        }
    }
}
