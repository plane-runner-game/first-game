// AutoFire.cs
// The squad shoots on its own at whatever is lined up in front of it. Gatling hits the
// nearest thing, rockets splash nearby hordes, laser pierces through everything in line.
// During the boss fight the boss is always a target so side gates can't steal the fire.
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
        readonly List<(object o, float z)> cands = new List<(object, float)>();
        float shotT;

        public IReadOnlyList<object> Targets => targets;
        public bool Has(object o) => targets.Contains(o);

        void Update()
        {
            targets.Clear();
            var gm = GameManager.I;
            if (gm == null || gm.State != GameState.Playing || squad.Count <= 0 || squad.Weapon == null) return;
            var cfg = gm.config;
            var w = squad.Weapon;
            bool inFight = gm.boss.Active && gm.boss.Fighting && !gm.boss.Dead;

            cands.Clear();
            foreach (var h in HordeSpawner.I.Active)
            {
                if (h.Dead || h.Z <= 2f || h.Z > cfg.lineOfFireRange) continue;
                if (Mathf.Abs(h.X - squad.X) < h.HalfWidth + cfg.fireConeHalfWidth && Mathf.Abs(h.Alt - squad.Alt) < cfg.fireConeHalfHeight)
                    cands.Add((h, h.Z));
            }
            if (!inFight)
            {
                foreach (var p in PickupSpawner.I.Active)
                {
                    if (p.Dead || p.Z <= 2f || p.Z > cfg.lineOfFireRange) continue;
                    if (Mathf.Abs(p.X - squad.X) < 3.1f + cfg.fireConeHalfWidth && Mathf.Abs(p.CenterAlt - squad.Alt) < 3.3f)
                        cands.Add((p, p.Z));
                }
            }
            cands.Sort((a, b) => a.z.CompareTo(b.z));

            if (inFight)
            {
                targets.Add(gm.boss);
                if (w.pierce) foreach (var c in cands) targets.Add(c.o);
                else if (cands.Count > 0) targets.Add(cands[0].o);
            }
            else if (cands.Count > 0)
            {
                if (w.pierce) foreach (var c in cands) targets.Add(c.o);
                else if (w.splashRadius > 0f)
                {
                    var first = cands[0].o;
                    targets.Add(first);
                    if (first is Horde fh)
                        foreach (var h in HordeSpawner.I.Active)
                            if (h != fh && !h.Dead && Mathf.Abs(h.X - fh.X) < w.splashRadius && Mathf.Abs(h.Z - fh.Z) < 13f) targets.Add(h);
                }
                else targets.Add(cands[0].o);
            }
            if (targets.Count == 0) return;

            float D = squad.Dps * Time.deltaTime;
            foreach (var t in targets)
            {
                if (t is BossController b) b.TakeDamage(D);
                else if (t is Horde h) h.TakeDamage(D);
                else if (t is Pickup p) p.Shoot(D);
            }

            shotT -= Time.deltaTime;
            if (shotT > 0f) return;
            shotT = w.fireInterval;
            object main = targets[0];
            Vector3 tp = TargetPos(main);
            int n = w.projectile == ProjectileKind.Rocket ? 1 : Mathf.Clamp(Mathf.RoundToInt(squad.Count / 6f), 1, 3);
            for (int i = 0; i < n; i++)
            {
                Vector3 from = squad.SlotWorld(Random.Range(0, squad.VisibleCount)) + Vector3.forward * 0.5f;
                switch (w.projectile)
                {
                    case ProjectileKind.Tracer:
                        tracers.Fire(from, tp + Random.insideUnitSphere * 0.8f, w.color, 0.1f, 0.07f);
                        AudioManager.I.Play(Sfx.Gun);
                        break;
                    case ProjectileKind.Rocket:
                        rockets.Fire(from, main, w.color);
                        AudioManager.I.Play(Sfx.Rocket);
                        break;
                    case ProjectileKind.Beam:
                        object far = targets[targets.Count - 1];
                        tracers.Fire(from, TargetPos(far) + Random.insideUnitSphere * 0.3f, w.color, 0.08f, 0.16f);
                        AudioManager.I.Play(Sfx.Laser);
                        break;
                }
            }
            if (w.projectile != ProjectileKind.Rocket) FXManager.I.Sparks(tp + Random.insideUnitSphere * 0.6f, w.color, 2);
            squad.MuzzleFlash();
        }

        public static Vector3 TargetPos(object o)
        {
            if (o is BossController b) return b.transform.position;
            if (o is Horde h) return h.transform.position;
            if (o is Pickup p) return p.transform.position + Vector3.up * 2f;
            return Vector3.zero;
        }
    }
}
