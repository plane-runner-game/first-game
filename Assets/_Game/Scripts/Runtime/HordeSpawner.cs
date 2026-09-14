// HordeSpawner.cs
// Decides WHEN a wave comes and HOW BIG it is (level, time into the level, and your own
// squad size all push the number up), then creates Horde objects ahead of the player.
using System;
using System.Collections.Generic;
using UnityEngine;

namespace SkySquad
{
    public class HordeSpawner : MonoBehaviour
    {
        public static HordeSpawner I { get; private set; }
        public GameObject hordePrefab;

        readonly List<Horde> active = new List<Horde>();
        System.Random rng = new System.Random(1);
        float waveT;
        int level = 1;

        public IReadOnlyList<Horde> Active => active;
        public Horde[] ActiveSnapshot() => active.ToArray();

        void Awake() { I = this; }

        public void ResetForLevel(int n)
        {
            level = n;
            rng = new System.Random(n * 7919 + 3);
            foreach (var h in active) if (h != null) Destroy(h.gameObject);
            active.Clear();
            waveT = 2.6f;
        }

        void Update()
        {
            var gm = GameManager.I;
            if (gm == null || gm.State != GameState.Playing || gm.BossPhase) return;
            var cfg = gm.config;
            waveT -= Time.deltaTime;
            if (waveT <= 0f && gm.LevelTime < gm.LevelDuration)
            {
                waveT = Mathf.Max(cfg.waveEveryMin, cfg.waveEveryBase - level * cfg.waveEveryPerLevel);
                SpawnWave();
            }
        }

        public void SpawnWave()
        {
            var gm = GameManager.I;
            var cfg = gm.config;
            float ramp = 0.35f + 0.65f * Mathf.Min(1f, gm.LevelTime / cfg.rampSeconds);
            float growth = (cfg.hordeGrowth + level * cfg.hordeGrowthPerLevel) * (1f + level * 0.15f);
            float size = (cfg.hordeBase + level * cfg.hordeBasePerLevel + gm.LevelTime * growth + gm.squad.Count * cfg.hordeScaleByCount) * ramp;
            double doubleChance = Math.Min(0.6, 0.08 + level * 0.07);
            int n = rng.NextDouble() < doubleChance ? 2 : 1;
            for (int i = 0; i < n; i++)
            {
                var kind = PickKind();
                float units = size / n * kind.sizeFactor;
                float spread = cfg.laneHalfWidth * 0.75f;
                float x = n == 1 ? (float)(rng.NextDouble() - 0.5) * spread * 1.6f : (i == 0 ? -1f : 1f) * (spread * 0.5f + (float)rng.NextDouble() * spread * 0.5f);
                float alt = rng.NextDouble() < 0.5 ? 1.5f + (float)rng.NextDouble() * 1.3f : 6f + (float)rng.NextDouble() * 1.5f;
                Spawn(kind, Mathf.RoundToInt(units), x, cfg.spawnDistance, alt);
            }
        }

        HordeKindDef PickKind()
        {
            var kinds = GameManager.I.config.hordeKinds;
            float total = 0f;
            foreach (var k in kinds) total += EffectiveWeight(k);
            double r = rng.NextDouble() * total;
            foreach (var k in kinds)
            {
                float w = EffectiveWeight(k);
                if (w <= 0f) continue;
                if (r < w) return k;
                r -= w;
            }
            return kinds[0];
        }

        float EffectiveWeight(HordeKindDef k)
        {
            if (level < k.minLevel) return 0f;
            float fade = k.minLevel > 1 ? Mathf.Min(1f, 0.4f + (level - k.minLevel) * 0.15f) : 1f;
            return k.weight * fade;
        }

        public Horde Spawn(HordeKindDef kind, int units, float x, float z, float alt)
        {
            var go = Instantiate(hordePrefab, transform);
            var h = go.GetComponent<Horde>();
            h.Init(kind, units, x, z, alt);
            active.Add(h);
            var gm = GameManager.I;
            if (units >= gm.config.bigHordeThreshold)
            {
                gm.hud.Banner("BIG HORDE!", new Color(1f, 0.23f, 0.31f), 1.1f);
                gm.hud.Warn(1.2f);
                AudioManager.I.Play(Sfx.Warn);
            }
            return h;
        }

        public void Release(Horde h)
        {
            active.Remove(h);
            if (h != null) Destroy(h.gameObject);
        }

        public void KillAll(bool silent)
        {
            foreach (var h in active.ToArray()) h.Kill(silent);
        }

        public float RandomRange(float a, float b) => a + (float)rng.NextDouble() * (b - a);
    }
}
