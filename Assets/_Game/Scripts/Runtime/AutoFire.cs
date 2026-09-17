// AutoFire.cs
// The squad's guns fire volleys on their own at whatever its altitude band holds. Up high every
// plane picks its own enemy - nearest first, counting bullets already in the air - so five planes
// drop five planes; down low every bullet goes into the front crate. All three weapons fire real
// projectiles that do their damage on impact (BulletPool, ProjectileKind.Tracer): the Rockets are the
// same bullets in orange with splash on landing. The old instant-hit Rocket/Beam branches are kept
// but unused (2026-09-17: "the enemy planes were destroyed before the shot reached them"). Planes
// with nothing to shoot still fire straight ahead so the guns read as live.
using System.Collections.Generic;
using UnityEngine;

namespace SkySquad
{
    public class AutoFire : MonoBehaviour
    {
        public SquadController squad;
        public TracerPool tracers;
        public RocketPool rockets;
        public BulletPool bullets;

        readonly List<Enemy> cands = new List<Enemy>();
        float volleyT;

        public object Primary { get; private set; }

        void Update()
        {
            Primary = null;
            var gm = GameManager.I;
            if (gm == null || gm.State != GameState.Playing || squad.Count <= 0 || squad.Weapon == null) return;
            var cfg = gm.config;
            var w = squad.Weapon;
            volleyT -= Time.deltaTime;
            if (volleyT > 0f) return;
            volleyT = w.fireInterval / Progress.FireRateMult;
            bool inFight = gm.boss.Active && gm.boss.Fighting && !gm.boss.Dead;
            int n = squad.Count;

            if (squad.IsHigh)
            {
                cands.Clear();
                // only the planes in your own lane: a wide boss counts as in-lane across his whole width
                foreach (var e in WaveSpawner.I.Active)
                    if (!e.Dead && !e.Striking && e.Z > squad.Z + 1f && e.Z <= squad.Z + cfg.lineOfFireRange && Mathf.Abs(e.X - squad.X) < cfg.laneHalfWidthAim + (e.Wide ? e.HalfWidth : 0f)) cands.Add(e);
                float sx = squad.X;
                cands.Sort((a, b) => (Mathf.Round(a.Z) * 100f + Mathf.Abs(a.X - sx)).CompareTo(Mathf.Round(b.Z) * 100f + Mathf.Abs(b.X - sx)));
                if (cands.Count == 0 && inFight)
                {
                    for (int i = 0; i < n; i++) FireOne(i, gm.boss, w, cfg);
                    Primary = gm.boss;
                }
                else
                {
                    int ci = 0;
                    for (int i = 0; i < n; i++)
                    {
                        while (ci < cands.Count && cands[ci].Pending >= cands[ci].Hp) ci++;   // already has enough bullets coming
                        FireOne(i, ci < cands.Count ? cands[ci] : null, w, cfg);
                    }
                    Primary = cands.Count > 0 ? cands[0] : null;
                }
            }
            else
            {
                var f = SupplyLane.I.Front;
                object t = f != null && !f.Dead && f.Z > squad.Z + 1f && Mathf.Abs(f.X - squad.X) < cfg.laneHalfWidthAim + f.HalfWidth ? f : null;   // line up with the crate too
                for (int i = 0; i < n; i++) FireOne(i, t, w, cfg);
                Primary = t;
            }

            squad.MuzzleFlash();
            AudioManager.I.Play(w.projectile == ProjectileKind.Rocket || w.id == "rockets" ? Sfx.Rocket : w.projectile == ProjectileKind.Beam ? Sfx.Laser : Sfx.Gun);
        }

        void FireOne(int i, object target, WeaponDef w, GameConfig cfg)
        {
            Vector3 from = squad.SlotWorld(i % Mathf.Max(1, squad.VisibleCount)) + Vector3.forward * 0.6f;
            float dmg = w.damage * Progress.DamageMult * squad.PowerMult;
            switch (w.projectile)
            {
                case ProjectileKind.Tracer:
                    if (bullets == null) break;
                    Vector3 idle = from + Vector3.forward * 30f + new Vector3(Random.Range(-0.4f, 0.4f), Random.Range(-0.2f, 0.2f), 0f);
                    bool rocket = w.id == "rockets";   // the Rockets weapon: same bullet, drawn as the finned rocket with its fire tail, faster (the old rockets flew 55-100 u/s)
                    bullets.Fire(from, target, idle, dmg, w.color, rocket ? cfg.bulletSpeed * 1.8f : cfg.bulletSpeed, rocket ? 1f : cfg.bulletSize, w.splashRadius, rocket);
                    break;
                case ProjectileKind.Rocket:
                    if (target != null)
                    {
                        Hit(target, dmg);
                        if (target is Enemy fe && w.splashRadius > 0f)
                            foreach (var e in new List<Enemy>(WaveSpawner.I.Active))   // a kill removes from Active: iterate a copy
                                if (e != fe && !e.Dead && Mathf.Abs(e.X - fe.X) < w.splashRadius && Mathf.Abs(e.Z - fe.Z) < w.splashRadius) e.TakeDamage(dmg * 0.6f);
                    }
                    rockets.Fire(from, target, w.color, target == null ? dmg : 0f, w.splashRadius);   // nothing to hit: the rocket flies straight ahead and hits the first plane it passes in its column, like the Gatling's idle bullets
                    break;
                case ProjectileKind.Beam:
                    Vector3 end = target != null ? TargetPos(target) : from + Vector3.forward * 40f;
                    if (target != null)
                    {
                        Hit(target, dmg);
                        if (target is Enemy be && w.pierce)
                            foreach (var e in new List<Enemy>(WaveSpawner.I.Active))
                                if (e != be && !e.Dead && e.Z > be.Z && Mathf.Abs(e.X - be.X) < cfg.pierceHalfWidth) { e.TakeDamage(dmg); end = e.transform.position; }
                        FXManager.I.Sparks(TargetPos(target) + Random.insideUnitSphere * 0.4f, w.color, 2);
                    }
                    tracers.Fire(from, end + Random.insideUnitSphere * 0.2f, w.color, Mathf.Max(0.08f, volleyT * 1.1f), 0.16f);   // the beam lasts until the next volley, so it never blinks off between shots
                    break;
            }
        }

        static void Hit(object t, float d)
        {
            if (t is BossController b) b.TakeDamage(d);
            else if (t is Enemy e) e.TakeDamage(d);
            else if (t is Breakable k) k.Shoot(d);
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
