// BulletPool.cs
// Real bullets: glowing slugs with a trail. A bullet is fired along a straight line toward the point
// it was aimed at and never turns - moving the squad after the shot leaves it on its path. It lands
// on the first thing it flies through: its own target, or (if that plane is already gone) the next
// plane queued in the same column. The crowd's shots at the squad are the one exception: they track
// the formation slot they were aimed at, because a landed shot always costs a plane.
using System.Collections.Generic;
using UnityEngine;

namespace SkySquad
{
    public class BulletPool : MonoBehaviour
    {
        public static BulletPool I { get; private set; }
        public GameObject bulletPrefab;
        public GameObject rocketPrefab;   // the Rockets weapon's bullet: the finned rocket model with its fire tail (taken from RocketPool if left empty)

        class B { public GameObject go; public Renderer rend; public TrailRenderer trail; public object target; public Vector3 aim, pos, dir; public Color color; public float t, dmg, speed, splash; public bool live, homing, rocket; }
        readonly List<B> pool = new List<B>();
        Transform root;   // bullets live at the world root, never under the squad, so they do not move with it
        static MaterialPropertyBlock mpb;
        static readonly int BaseColor = Shader.PropertyToID("_BaseColor");

        void Awake()
        {
            I = this; root = new GameObject("Bullets").transform;
            if (rocketPrefab == null) { var rp = FindObjectOfType<RocketPool>(); if (rp != null) rocketPrefab = rp.rocketPrefab; }
        }

        /// <summary>Fire at 'target' (Enemy, Breakable, BossController or SquadController). For a squad target
        /// 'aim' is the formation-local slot to hit; with no target the bullet flies to 'aim' and fades.
        /// 'splash' > 0 (rockets): when it lands on a fighter, the fighters within that box take 60% of the damage too.
        /// 'rocket': drawn as the rocket model with a fire tail instead of a slug - same flight, same impact rule.</summary>
        public void Fire(Vector3 from, object target, Vector3 aim, float dmg, Color color, float speed, float size, float splash = 0f, bool rocket = false)
        {
            if (rocket && rocketPrefab == null) rocket = false;
            B b = null;
            foreach (var p in pool) if (!p.live && p.rocket == rocket) { b = p; break; }
            if (b == null)
            {
                if (rocket)
                {
                    var go = Instantiate(rocketPrefab, root);
                    b = new B { go = go, rend = go.GetComponentInChildren<MeshRenderer>(), trail = go.GetComponentInChildren<TrailRenderer>(), rocket = true };
                }
                else
                {
                    var go = Instantiate(bulletPrefab, root);
                    var slug = go.transform.Find("Slug");
                    b = new B { go = go, rend = slug != null ? slug.GetComponent<Renderer>() : null, trail = go.GetComponent<TrailRenderer>() };
                }
                pool.Add(b);
            }
            b.live = true; b.target = target; b.aim = aim; b.dmg = dmg; b.speed = speed; b.color = color; b.splash = splash; b.t = 0f;
            b.homing = target is SquadController;
            b.pos = from;
            Vector3 dir = TargetPoint(b) - from;
            b.dir = dir.sqrMagnitude > 0.001f ? dir.normalized : Vector3.forward;
            b.go.transform.position = from;
            b.go.transform.rotation = Quaternion.LookRotation(b.dir);
            b.go.transform.localScale = Vector3.one * size;
            b.go.SetActive(true);
            if (mpb == null) mpb = new MaterialPropertyBlock();
            if (b.rocket)
            {   // the look of the old RocketPool: orange-tinted body, tail of fire from hot yellow into orange, fading out
                mpb.SetColor(BaseColor, new Color(1f, 0.75f, 0.3f));
                if (b.rend != null) b.rend.SetPropertyBlock(mpb);
                if (b.trail != null) { b.trail.Clear(); b.trail.startColor = new Color(1f, 0.8f, 0.25f, 1f); b.trail.endColor = new Color(1f, 0.3f, 0.05f, 0f); }
            }
            else
            {
                mpb.SetColor(BaseColor, color);
                if (b.rend != null) b.rend.SetPropertyBlock(mpb);
                if (b.trail != null) { b.trail.Clear(); b.trail.startColor = color; b.trail.endColor = new Color(color.r, color.g, color.b, 0f); }
            }
            if (target is Enemy e) e.Pending += dmg;   // so the next volley aims elsewhere
        }

        static bool Alive(object o)
        {
            if (o is Enemy e) return !e.Dead && !e.Striking;   // a fighter on its strike run is untouchable
            if (o is Breakable k) return !k.Dead;
            if (o is BossController b) return b.Active && !b.Dead;
            if (o is SquadController s) return s.Count > 0;
            return false;
        }

        static Vector3 TargetPoint(B b)
        {
            if (b.target is SquadController s) return s.formationRoot.TransformPoint(b.aim);
            if (b.target != null) return AutoFire.TargetPos(b.target);
            return b.aim;
        }

        /// <summary>Did the bullet pass this plane between the two positions? Same column (x), same band (y), and its z went by.</summary>
        static bool Crossed(Vector3 prev, Vector3 now, Enemy e, GameConfig cfg)
        {
            float r = cfg.bulletHitRadius + (e.Wide ? e.HalfWidth : 0f);
            if (Mathf.Abs(e.X - now.x) > r) return false;
            if (Mathf.Abs(e.transform.position.y - now.y) > 1.4f) return false;
            return prev.z <= e.Z + 0.35f && now.z >= e.Z - 0.35f;
        }

        void Update()
        {
            float dt = Time.deltaTime;
            var gm = GameManager.I;
            bool playing = gm != null && gm.State == GameState.Playing;
            for (int i = 0; i < pool.Count; i++)
            {
                var b = pool[i];
                if (!b.live) continue;
                if (!playing) { Retire(b); continue; }
                var cfg = gm.config;
                b.t += dt;
                float step = b.speed * dt;
                bool alive = b.target != null && Alive(b.target);
                if (b.homing)
                {   // crowd fire: chases the slot it was aimed at
                    if (!alive) { Retire(b); continue; }
                    Vector3 tp = TargetPoint(b);
                    Vector3 to = tp - b.pos;
                    float dist = to.magnitude;
                    if (dist <= step + 0.5f) { Land(b, b.target, tp); continue; }
                    b.dir = to / dist;
                    b.pos += b.dir * step;
                }
                else
                {   // straight line, no steering: the direction was fixed when the trigger was pulled
                    Vector3 prev = b.pos;
                    b.pos += b.dir * step;
                    object hit = null; Vector3 at = b.pos;
                    if (alive)
                    {
                        Vector3 tp = TargetPoint(b);
                        float r = b.target is Breakable ? 1.1f : b.target is BossController ? 2.5f : 0.6f;
                        if (Vector3.Distance(b.pos, tp) <= step * 0.5f + r || (b.target is Enemy te && Crossed(prev, b.pos, te, cfg))) { hit = b.target; at = tp; }
                    }
                    if (hit == null && (b.target is Enemy || b.target == null) && WaveSpawner.I != null)
                    {   // flew past its own plane (or had none): whatever crosses its path takes the bullet
                        foreach (var e in WaveSpawner.I.Active)
                            if (!e.Dead && !e.Striking && Crossed(prev, b.pos, e, cfg)) { hit = e; at = e.transform.position; break; }
                    }
                    if (hit != null) { Land(b, hit, at); continue; }
                    if (b.t > cfg.bulletLife || (b.target == null && Vector3.Distance(b.pos, b.aim) <= step)) { Retire(b); continue; }
                }
                b.go.transform.position = b.pos;
                b.go.transform.rotation = Quaternion.LookRotation(b.dir);
            }
        }

        void Land(B b, object hit, Vector3 at)
        {
            var fx = FXManager.I;
            if (b.target is Enemy te) te.Pending = Mathf.Max(0f, te.Pending - b.dmg);   // its own target's bookkeeping, whichever plane it hit
            switch (hit)
            {
                case Enemy e:
                    fx.Hit(at, b.color, b.splash > 0f ? 6 : 3);   // the pack's fire hit, throttled (2026-09-19)
                    e.TakeDamage(b.dmg);
                    if (b.splash > 0f && WaveSpawner.I != null)   // rockets: the planes around the one hit take 60% too - on impact, never before
                        foreach (var o in new List<Enemy>(WaveSpawner.I.Active))   // a kill removes from Active: iterate a copy
                            if (o != e && !o.Dead && !o.Striking && Mathf.Abs(o.X - e.X) < b.splash && Mathf.Abs(o.Z - e.Z) < b.splash) o.TakeDamage(b.dmg * 0.6f);
                    break;
                case Breakable k: fx.Sparks(at, b.color, 3); k.Shoot(b.dmg); break;
                case BossController bc: fx.Sparks(at, b.color, 3); bc.TakeDamage(b.dmg); break;
                case SquadController s: fx.Sparks(at, new Color(1f, 0.42f, 0.17f), 8); s.Damage(Mathf.Max(1, Mathf.RoundToInt(b.dmg)), "enemy fire from above"); break;
            }
            b.live = false;
            b.go.SetActive(false);
        }

        void Retire(B b)
        {
            if (b.target is Enemy e) e.Pending = Mathf.Max(0f, e.Pending - b.dmg);
            b.live = false;
            b.go.SetActive(false);
        }
    }
}
