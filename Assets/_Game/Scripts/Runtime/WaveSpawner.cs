// WaveSpawner.cs
// The HIGH band's stream: V-wing flights of enemy planes keep coming on a steady beat, every
// N-th one a mini boss with two escorts followed by a short pause. Flights never stop while you
// farm below - the crowd parked at the front line only grows. Also owns the blocking: every frame
// each plane may advance until the front line or a plane ahead of it whose x overlaps its own.
using System.Collections.Generic;
using UnityEngine;

namespace SkySquad
{
    public class WaveSpawner : MonoBehaviour
    {
        public static WaveSpawner I { get; private set; }
        public GameObject fighterPrefab;
        public GameObject miniBossPrefab;

        readonly List<Enemy> active = new List<Enemy>();
        readonly List<Enemy> ordered = new List<Enemy>();
        System.Random rng = new System.Random(1);
        int level = 1, flight, bosses;
        float nextT;          // level time of the next flight

        public IReadOnlyList<Enemy> Active => active;
        public int Flight => flight;
        public int ParkedCount { get { int n = 0; foreach (var e in active) if (!e.Dead && e.Parked) n++; return n; } }

        void Awake() { I = this; }

        public void ResetForLevel(int n)
        {
            level = n;
            rng = new System.Random(n * 31 + 7);
            foreach (var e in active) if (e != null) Destroy(e.gameObject);
            active.Clear();
            flight = bosses = 0;
            nextT = 0f;
        }

        void Update()
        {
            var gm = GameManager.I;
            if (gm == null || gm.State != GameState.Playing) return;
            var cfg = gm.config;
            float dt = Time.deltaTime;

            // the beat
            if (!gm.BossPhase && gm.LevelTime < gm.LevelDuration && gm.LevelTime >= nextT)
            {
                float z = flight == 0 ? cfg.firstFlightDistance : cfg.spawnDistance;
                bool bossFlight = flight > 0 && cfg.flightsPerMiniBoss > 0 && flight % cfg.flightsPerMiniBoss == 0;
                if (bossFlight) { SpawnMiniBoss(z); nextT = gm.LevelTime + cfg.miniBossPause; }
                else { SpawnFlight(z); nextT = gm.LevelTime + Mathf.Max(cfg.flightEveryMin, cfg.flightEveryBase - (level - 1) * cfg.flightEveryPerLevel); }
                flight++;
            }

            // movement with blocking, front to back: a plane holds behind any nearer plane whose x overlaps
            ordered.Clear();
            foreach (var e in active) if (!e.Dead) ordered.Add(e);
            ordered.Sort((a, b) => a.Z.CompareTo(b.Z));
            for (int i = 0; i < ordered.Count; i++)
            {
                var e = ordered[i];
                float ahead = float.NegativeInfinity;
                for (int j = 0; j < i; j++)
                {
                    var o = ordered[j];
                    if (o.Dead) continue;
                    float w = (e.Wide || o.Wide) ? 99f : cfg.blockWidth;
                    if (Mathf.Abs(o.X - e.X) < w) ahead = Mathf.Max(ahead, o.Z);
                }
                bool frontRow = float.IsNegativeInfinity(ahead);   // nobody ahead: it parks on the line and gets to shoot
                float limit = frontRow ? cfg.enemyStopZ : Mathf.Max(cfg.enemyStopZ, ahead + cfg.rowSpacing);
                e.Tick(dt, limit, frontRow);
                if (gm.State != GameState.Playing) return;
            }
        }

        void SpawnFlight(float z)
        {
            var cfg = GameManager.I.config;
            int n = Mathf.Min(cfg.flightSizeMax, cfg.flightSizeBase + flight / Mathf.Max(1, cfg.flightSizeEvery));
            float hp = FighterHp();
            float margin = cfg.laneHalfWidth - 2.2f;
            float xc = (float)(rng.NextDouble() * 2.0 - 1.0) * margin;
            float alt = cfg.altitudeSplit + cfg.enemyAltAboveSplit;
            for (int i = 0; i < n; i++)
            {   // inverted V: leader in front, wingmen alternate left/right one row back per pair
                int k = (i + 1) / 2;
                float side = i % 2 == 0 ? 1f : -1f;
                float x = Mathf.Clamp(xc + side * k * cfg.wingSpacingX, -cfg.laneHalfWidth + 0.6f, cfg.laneHalfWidth - 0.6f);
                Spawn(fighterPrefab, cfg.enemyFighter, hp, false, x, z + k * cfg.wingSpacingZ, alt + k * 0.12f);
            }
        }

        void SpawnMiniBoss(float z)
        {
            var cfg = GameManager.I.config;
            bosses++;
            float hp = (cfg.miniBossHpBase + (bosses - 1) * cfg.miniBossHpPerBoss + (level - 1) * cfg.miniBossHpPerLevel) * (1f + GameManager.I.squad.Count * cfg.miniBossHpPerPlane);
            float alt = cfg.altitudeSplit + cfg.enemyAltAboveSplit;
            Spawn(miniBossPrefab, cfg.enemyMiniBoss, Mathf.Round(hp), true, 0f, z, alt + 0.8f);
            float escortHp = FighterHp();
            Spawn(fighterPrefab, cfg.enemyFighter, escortHp, false, -2.6f, z - 1.2f, alt);
            Spawn(fighterPrefab, cfg.enemyFighter, escortHp, false, 2.6f, z - 1.2f, alt);
        }

        /// <summary>Fighters toughen with the level's flight count and, gently, with your own plane count.</summary>
        float FighterHp()
        {
            var cfg = GameManager.I.config;
            return Mathf.Round(cfg.enemyFighter.hp + flight / Mathf.Max(1, cfg.fighterHpEvery) + (level - 1) + GameManager.I.squad.Count * cfg.fighterHpPerPlane);
        }

        Enemy Spawn(GameObject prefab, EnemyKindDef kind, float hp, bool wide, float x, float z, float alt)
        {
            var go = Instantiate(prefab, transform);
            var e = go.GetComponent<Enemy>();
            e.Init(kind, hp, wide, x, z, alt);
            active.Add(e);
            return e;
        }

        public void Release(Enemy e)
        {
            active.Remove(e);
            if (e != null) Destroy(e.gameObject);
        }

        public void KillAll(bool silent)
        {
            foreach (var e in active.ToArray()) e.Kill(silent);
        }
    }
}
