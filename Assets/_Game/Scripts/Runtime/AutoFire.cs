// AutoFire.cs
// The squad's guns fire volleys on their own at whatever its altitude band holds: up high, the
// nearest enemy plane (no lining up needed - the shots turn to face it), down low, the front crate.
// Damage is discrete: one bullet per plane per volley, so the HP numbers count real hits. Rockets
// splash the planes around the one they hit, the laser pierces the planes behind it. The zeppelin
// boss is the target up high once its escort is gone.
using System.Collections.Generic;
using UnityEngine;

namespace SkySquad
{
    public class AutoFire : MonoBehaviour
    {
        public SquadController squad;
        public TracerPool tracers;
        public RocketPool rockets;

        readonly List<object> targets = new List<object>();
        float volleyT;

        public IReadOnlyList<object> Targets => targets;
        public object Primary => targets.Count > 0 ? targets[0] : null;

        void Update()
        {
            targets.Clear();
            var gm = GameManager.I;
            if (gm == null || gm.State != GameState.Playing || squad.Count <= 0 || squad.Weapon == null) return;
            var cfg = gm.config;
            var w = squad.Weapon;
            bool inFight = gm.boss.Active && gm.boss.Fighting && !gm.boss.Dead;

            if (squad.IsHigh)
            {
                // nearest plane first; among a parked row (same distance) the one in front of you, so a
                // row is swept outward from where you are - but you never have to be exactly on it
                Enemy best = null; float bestKey = float.MaxValue;
                foreach (var e in WaveSpawner.I.Active)
                {
                    if (e.Dead || e.Z <= 1f || e.Z > cfg.lineOfFireRange) continue;
                    float key = Mathf.Round(e.Z) * 100f + Mathf.Abs(e.X - squad.X);
                    if (key < bestKey) { bestKey = key; best = e; }
                }
                if (best != null)
                {
                    targets.Add(best);
                    if (w.pierce)
                    {
                        foreach (var e in WaveSpawner.I.Active)
                            if (e != best && !e.Dead && e.Z > best.Z && Mathf.Abs(e.X - best.X) < cfg.pierceHalfWidth) targets.Add(e);
                    }
                    else if (w.splashRadius > 0f)
                    {
                        foreach (var e in WaveSpawner.I.Active)
                            if (e != best && !e.Dead && Mathf.Abs(e.X - best.X) < w.splashRadius && Mathf.Abs(e.Z - best.Z) < w.splashRadius) targets.Add(e);
                    }
                }
                else if (inFight) targets.Add(gm.boss);
            }
            else
            {
                var f = SupplyLane.I.Front;
                if (f != null && !f.Dead && f.Z > 1f) targets.Add(f);
            }

            volleyT -= Time.deltaTime;
            if (volleyT > 0f) return;
            volleyT = w.fireInterval;

            int bullets = squad.Count;
            float dmg = bullets * w.damage;
            for (int i = 0; i < targets.Count; i++)
            {
                float d = (i == 0 || w.pierce) ? dmg : dmg * 0.6f;   // splash neighbours take less
                var t = targets[i];
                if (t is BossController b) b.TakeDamage(d);
                else if (t is Enemy e) e.TakeDamage(d);
                else if (t is Breakable k) k.Shoot(d);
            }

            // the guns run all the time so the line of fire is always readable; with a target the shots face it
            object main = targets.Count > 0 ? targets[0] : null;
            Vector3 tp = main != null ? TargetPos(main) : squad.transform.position + Vector3.forward * (cfg.lineOfFireRange * 0.7f);
            int n = w.projectile == ProjectileKind.Rocket ? 1 : Mathf.Clamp(bullets, 1, 4);
            for (int i = 0; i < n; i++)
            {
                int slot = n <= squad.VisibleCount ? Random.Range(0, squad.VisibleCount) : i;
                Vector3 from = squad.SlotWorld(slot) + Vector3.forward * 0.5f;
                switch (w.projectile)
                {
                    case ProjectileKind.Tracer:
                        tracers.Fire(from, tp + Random.insideUnitSphere * (main != null ? 0.5f : 0.15f), w.color, 0.1f, 0.07f);
                        AudioManager.I.Play(Sfx.Gun);
                        break;
                    case ProjectileKind.Rocket:
                        if (main != null) { rockets.Fire(from, main, w.color); AudioManager.I.Play(Sfx.Rocket); }
                        break;
                    case ProjectileKind.Beam:
                        object far = targets.Count > 0 ? targets[targets.Count - 1] : null;
                        tracers.Fire(from, (far != null ? TargetPos(far) : tp) + Random.insideUnitSphere * 0.3f, w.color, 0.08f, 0.16f);
                        AudioManager.I.Play(Sfx.Laser);
                        break;
                }
            }
            if (main != null && w.projectile != ProjectileKind.Rocket) FXManager.I.Sparks(tp + Random.insideUnitSphere * 0.5f, w.color, 3);
            squad.MuzzleFlash();
        }

        public static Vector3 TargetPos(object o)
        {
            if (o is BossController b) return b.transform.position;
            if (o is Enemy e) return e.transform.position;
            if (o is Breakable k) return k.AimPoint;
            return Vector3.zero;
        }
    }
}
