// SupplyLane.cs
// The LOW band's conveyor: a short queue of crates flying a fixed distance ahead of the squad.
// Shoot the front one down (+2 planes, and its hp in coins) and the rest slide forward while a
// new one joins at the back. Every crate is a bit tougher than the last (15, 19, 23, ...), and a
// weapon crate shows up now and then. Every second spent down here is a second the crowd parked
// above keeps shooting.
using System.Collections.Generic;
using UnityEngine;

namespace SkySquad
{
    public class SupplyLane : MonoBehaviour
    {
        public static SupplyLane I { get; private set; }
        public GameObject breakablePrefab;

        readonly List<Breakable> active = new List<Breakable>();   // front first
        int level = 1, nextIndex, boxIndex;

        public IReadOnlyList<Breakable> Active => active;
        public Breakable Front => active.Count > 0 ? active[0] : null;

        void Awake() { I = this; }

        public void ResetForLevel(int n)
        {
            level = n;
            foreach (var b in active) if (b != null) Destroy(b.gameObject);
            active.Clear();
            nextIndex = boxIndex = 0;
        }

        void Update()
        {
            var gm = GameManager.I;
            if (gm == null || gm.State != GameState.Playing) return;
            while (active.Count < gm.config.supplyVisible) SpawnNext();
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
            b.Init(kind, cfg.boxPlanes, weapon, Mathf.Max(1f, hp), active.Count);
            active.Add(b);
        }

        /// <summary>Weapons are ordered weakest to strongest in the config; a crate always holds the next one up.</summary>
        WeaponDef NextWeapon(WeaponDef current)
        {
            var ws = GameManager.I.config.weapons;
            int i = System.Array.IndexOf(ws, current);
            return i >= 0 && i + 1 < ws.Length ? ws[i + 1] : null;
        }

        public void Release(Breakable b)
        {
            active.Remove(b);
            if (b != null) Destroy(b.gameObject);
            for (int i = 0; i < active.Count; i++) active[i].SetSlot(i);
        }
    }
}
