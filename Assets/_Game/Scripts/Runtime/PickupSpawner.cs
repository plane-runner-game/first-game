// PickupSpawner.cs
// Drops a side gate every few seconds: mostly +N planes, sometimes x2, shield, bomb,
// or a weapon crate. Left/right and low/high are random.
using System.Collections.Generic;
using UnityEngine;

namespace SkySquad
{
    public class PickupSpawner : MonoBehaviour
    {
        public static PickupSpawner I { get; private set; }
        public GameObject gatePrefab;

        readonly List<Pickup> active = new List<Pickup>();
        System.Random rng = new System.Random(2);
        float pickT;
        int level = 1;

        public IReadOnlyList<Pickup> Active => active;

        void Awake() { I = this; }

        public void ResetForLevel(int n)
        {
            level = n;
            rng = new System.Random(n * 104729 + 11);
            foreach (var p in active) if (p != null) Destroy(p.gameObject);
            active.Clear();
            pickT = 1.6f;
        }

        void Update()
        {
            var gm = GameManager.I;
            if (gm == null || gm.State != GameState.Playing) return;
            var cfg = gm.config;
            pickT -= Time.deltaTime;
            if (pickT <= 0f)
            {
                float every = Mathf.Max(cfg.pickEveryMin, cfg.pickEveryBase - level * cfg.pickEveryPerLevel);
                pickT = gm.BossPhase ? every * 1.5f : every;
                SpawnOne();
            }
        }

        void SpawnOne()
        {
            var gm = GameManager.I;
            var cfg = gm.config;
            float side = rng.NextDouble() < 0.5 ? -1f : 1f;
            bool high = rng.NextDouble() < 0.5;
            double r = rng.NextDouble();
            PickupKind kind; int value = 0; WeaponDef weapon = null;
            if (r < 0.5) { kind = PickupKind.Plus; value = 3 + level * 2 + rng.Next(0, 3); }
            else if (r < 0.58) { kind = PickupKind.X2; value = 2; }
            else if (r < 0.72) { kind = PickupKind.Shield; value = 12 + level * 4; }
            else if (r < 0.80) { kind = PickupKind.Bomb; }
            else
            {
                kind = PickupKind.Weapon;
                var ws = cfg.weapons;
                int wi = rng.Next(0, ws.Length);
                if (ws[wi] == gm.squad.Weapon) wi = (wi + 1) % ws.Length;
                weapon = ws[wi];
            }
            var go = Instantiate(gatePrefab, transform);
            var p = go.GetComponent<Pickup>();
            p.Init(kind, value, weapon, high, side * cfg.sideX, cfg.spawnDistance + 5f);
            active.Add(p);
        }

        public void Release(Pickup p)
        {
            active.Remove(p);
            if (p != null) Destroy(p.gameObject);
        }
    }
}
