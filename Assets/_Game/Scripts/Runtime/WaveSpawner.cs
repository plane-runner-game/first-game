// WaveSpawner.cs
// The script of the round, identical every attempt (seeded; nothing here looks at the player).
// Fighters stream in scattered - a random lane out of swarmLanes, random height, random depth, its own
// speed - with no gaps: horde 1 is the first 100, then boss 1 flies in behind them. The next horde starts a few seconds
// behind the boss and loiters behind him while he lives, then floods forward the moment he dies. The
// fighters are kamikazes (Enemy.cs); only the boss stops on the front line and shoots.
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
        readonly List<Enemy> ticking = new List<Enemy>();
        readonly int[] killedPerHorde = new int[64];
        System.Random rng = new System.Random(7);
        int level = 1, spawned, horde = 1, hordeSpawned, bosses;
        float pauseT, spawnAcc, spawnCost = 1f;   // spawnCost: how much of spawnAcc the next spawn needs (jittered so spawns are not metronomic)
        bool bossAnnounced;   // the boss only counts (bar, banner, bot) once he is close to the front line
        Enemy currentBoss;

        public IReadOnlyList<Enemy> Active => active;
        public int Flight => spawned;                  // planes spawned this attempt
        /// <summary>The horde the player is fighting: the stream is one ahead while a boss is still flying in.</summary>
        public int Horde => currentBoss != null && !currentBoss.Dead && !bossAnnounced ? Mathf.Max(1, horde - 1) : horde;
        public int HordeSpawned => hordeSpawned;
        int TargetOf(int h) => GameManager.I.config.hordePlanesBase + (h - 1) * GameManager.I.config.hordePlanesPerHorde;
        int StreamTarget => TargetOf(horde);
        public int HordeTarget => TargetOf(Horde);
        public int HordeKilled => killedPerHorde[Mathf.Clamp(Horde - 1, 0, killedPerHorde.Length - 1)];   // shot down, rammed or flown past: gone
        public float HordeProgress => Mathf.Clamp01(HordeKilled / (float)Mathf.Max(1, HordeTarget));
        public int Bosses => bosses;
        public Enemy CurrentBoss => currentBoss != null && !currentBoss.Dead && bossAnnounced ? currentBoss : null;
        public bool BossAlive => CurrentBoss != null;
        public int ParkedCount { get { int n = 0; foreach (var e in active) if (!e.Dead && (e.Parked || e.Held)) n++; return n; } }

        void Awake() { I = this; }

        public void ResetForLevel(int n)
        {
            level = n;
            rng = new System.Random(7);   // the same round every attempt
            foreach (var e in active) if (e != null) Destroy(e.gameObject);
            active.Clear();
            System.Array.Clear(killedPerHorde, 0, killedPerHorde.Length);
            spawned = hordeSpawned = bosses = 0;
            horde = 1;
            pauseT = spawnAcc = 0f; spawnCost = 1f;
            currentBoss = null;
            bossAnnounced = false;
            var cfg = GameManager.I.config;
            for (int i = 0; i < cfg.openingCrowd && hordeSpawned < StreamTarget; i++)
            {   // the opening crowd: a modest group already in the sky ahead when the attempt starts, so it does not open on empty air
                float z = Mathf.Lerp(cfg.openingCrowdNearZ, Mathf.Max(cfg.openingCrowdNearZ, cfg.openingCrowdFarZ - cfg.swarmDepth), (float)rng.NextDouble());
                SpawnOne(z);   // SpawnOne adds its usual 0..swarmDepth jitter
            }
        }

        /// <summary>Planes per second, a little faster every horde.</summary>
        float SwarmRate()
        {
            var cfg = GameManager.I.config;
            return cfg.swarmRate + (horde - 1) * cfg.swarmRatePerHorde;
        }

        void Update()
        {
            var gm = GameManager.I;
            if (gm == null || gm.State != GameState.Playing) return;
            var cfg = gm.config;
            float dt = Time.deltaTime;

            pauseT = Mathf.Max(0f, pauseT - dt);
            if (pauseT <= 0f && !gm.BossPhase && gm.LevelTime < gm.LevelDuration)
            {
                if (hordeSpawned >= StreamTarget)
                {   // the horde is complete: its boss follows it in, the next horde starts a few seconds behind him
                    SpawnMiniBoss(cfg.spawnDistance + 2f);
                    horde++; hordeSpawned = 0; spawnAcc = 0f;
                    pauseT = cfg.bossSpawnGap;
                }
                else
                {
                    spawnAcc += SwarmRate() * dt;
                    while (spawnAcc >= spawnCost && hordeSpawned < StreamTarget && active.Count < cfg.maxAliveEnemies)
                    {   // one comes early, the next late: the interval is jittered, the average rate stays SwarmRate()
                        SpawnOne(cfg.spawnDistance); spawnAcc -= spawnCost;
                        spawnCost = 1f + ((float)rng.NextDouble() * 2f - 1f) * cfg.swarmSpawnJitter;
                    }
                }
            }

            // flight: a boss brakes into the front line; fighters of the horde behind a living boss loiter behind him
            var boss = currentBoss != null && !currentBoss.Dead ? currentBoss : null;
            ticking.Clear();
            ticking.AddRange(active);
            foreach (var e in ticking)
            {
                if (e.Dead) continue;
                float limit;
                if (e.Kind.miniBoss) limit = cfg.enemyStopZ;
                else if (boss != null && e.HordeIndex > boss.HordeIndex) limit = boss.Z + cfg.holdBehindBoss + e.HoldOffset;
                else limit = float.NegativeInfinity;
                e.Tick(dt, limit);
                if (gm.State != GameState.Playing) return;
            }

            if (boss != null && !bossAnnounced && boss.Z < cfg.enemyStopZ + 14f)
            {   // he spawned behind his horde; the alarm sounds once he is nearly at the line
                bossAnnounced = true;
                gm.hud.Banner("BOSS " + bosses, new Color(1f, 0.23f, 0.31f), 1.5f);
                gm.hud.Warn(1.5f);
                AudioManager.I.Play(Sfx.Warn);
            }
        }

        void SpawnOne(float z)
        {
            var cfg = GameManager.I.config;
            float x = cfg.LaneX(rng.Next(Mathf.Max(1, cfg.swarmLanes)));   // its lane for the whole flight
            float alt = cfg.altitudeSplit + cfg.enemyAltAboveSplit + ((float)rng.NextDouble() * 2f - 1f) * cfg.swarmAltSpread;
            var e = Spawn(fighterPrefab, cfg.enemyFighter, cfg.enemyFighter.hp, false, x, z + (float)rng.NextDouble() * cfg.swarmDepth, alt, cfg.enemyFighter.shotDamage);
            e.HordeIndex = horde;
            e.HoldOffset = (float)rng.NextDouble() * 6f;
            e.SpeedMult = 1f + ((float)rng.NextDouble() * 2f - 1f) * cfg.swarmSpeedSpread;   // its own pace: some race ahead, some lag behind
            e.StrikeStyle = rng.Next(Enemy.StrikeStyles);   // which figure it flies past the green line: hop, swoop, barrel roll, slalom, corkscrew
            spawned++;
            hordeSpawned++;
        }

        void SpawnMiniBoss(float z)
        {
            var cfg = GameManager.I.config;
            bosses++;
            float hp = Mathf.Round(cfg.miniBossHpBase * Mathf.Pow(cfg.miniBossHpGrowth, bosses - 1));
            float shot = cfg.enemyMiniBoss.shotDamage + (bosses - 1) * cfg.miniBossShotPerBoss;
            float alt = cfg.altitudeSplit + cfg.enemyAltAboveSplit;
            currentBoss = Spawn(miniBossPrefab, cfg.enemyMiniBoss, hp, true, 0f, z, alt + 0.6f, shot);
            currentBoss.HordeIndex = horde;
            bossAnnounced = false;
        }

        Enemy Spawn(GameObject prefab, EnemyKindDef kind, float hp, bool wide, float x, float z, float alt, float shotDamage)
        {
            var go = Instantiate(prefab, transform);
            var e = go.GetComponent<Enemy>();
            e.Init(kind, hp, wide, x, z, alt, shotDamage);
            active.Add(e);
            return e;
        }

        public void Release(Enemy e)
        {
            active.Remove(e);
            if (e != null)
            {
                if (!e.Wide) killedPerHorde[Mathf.Clamp(e.HordeIndex - 1, 0, killedPerHorde.Length - 1)]++;
                Destroy(e.gameObject);
            }
        }

        public void KillAll(bool silent)
        {
            foreach (var e in active.ToArray()) e.Kill(silent);
        }
    }
}
