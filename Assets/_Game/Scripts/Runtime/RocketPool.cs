// RocketPool.cs - fast fire rockets with a short flame tail that explode on arrival. A rocket fired AT a
// plane deals its damage the moment it is fired (AutoFire) and flies to the spot as the visual; a rocket
// fired at nothing (or whose plane died on the way) flies straight on and hits the first plane it passes
// in its own column - exactly like the Gatling's idle bullets - so what you see it fly through, it hits.
// They leave the plane straight and fast with a touch of spread and home in the rest of the way.
// Rockets live at the world root, never under the squad: moving the squad does not drag fired rockets.
using System.Collections.Generic;
using UnityEngine;

namespace SkySquad
{
    public class RocketPool : MonoBehaviour
    {
        public GameObject rocketPrefab;
        class R { public GameObject go; public TrailRenderer trail; public Renderer body; public object target; public Vector3 vel; public Color color; public float t, dmg, splash; public bool live; }
        static MaterialPropertyBlock mpb;
        static readonly int BaseColor = Shader.PropertyToID("_BaseColor");
        readonly List<R> pool = new List<R>();
        Transform root;

        void Awake() { root = new GameObject("Rockets").transform; }

        public void Fire(Vector3 from, object target, Color c, float dmg = 0f, float splash = 0f)
        {
            R r = null;
            foreach (var p in pool) if (!p.live) { r = p; break; }
            if (r == null)
            {
                var go = Instantiate(rocketPrefab, root != null ? root : null);
                r = new R { go = go, trail = go.GetComponentInChildren<TrailRenderer>(), body = go.GetComponentInChildren<MeshRenderer>() };
                if (r.body != null)
                {   // the rocket itself glows the weapon colour (its shared material is grey)
                    if (mpb == null) mpb = new MaterialPropertyBlock();
                    mpb.SetColor(BaseColor, new Color(1f, 0.75f, 0.3f));
                    r.body.SetPropertyBlock(mpb);
                }
                pool.Add(r);
            }
            r.live = true;
            r.go.SetActive(true);
            r.go.transform.position = from;
            r.target = target; r.color = c; r.dmg = dmg; r.splash = splash;
            r.vel = new Vector3(Random.Range(-1.5f, 1.5f), Random.Range(-0.3f, 0.6f), 55f);   // straight out of the pods, a little spread
            r.t = 0f;
            if (r.trail != null)
            {   // the tail is fire: the weapon colour into a hot yellow-white core, fading out
                r.trail.Clear();
                r.trail.startColor = new Color(1f, 0.8f, 0.25f, 1f);
                r.trail.endColor = new Color(1f, 0.3f, 0.05f, 0f);
            }
        }

        /// <summary>Did the rocket pass this plane between the two positions? Same column (x), same band (y), and its z went by (BulletPool's rule).</summary>
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
            var cfg = gm != null ? gm.config : null;
            foreach (var r in pool)
            {
                if (!r.live) continue;
                r.t += dt;
                bool alive = r.target is Enemy en ? !en.Dead : r.target is BossController b ? !b.Dead : r.target is Breakable bk ? !bk.Dead : false;
                Vector3 prev = r.go.transform.position;
                Vector3 tp = alive ? AutoFire.TargetPos(r.target) : prev + Vector3.forward * 10f;
                Vector3 dir = (tp - prev).normalized;
                float sp = 55f + 45f * Mathf.Min(1f, r.t / 0.3f);   // 55 -> 100 u/s in a third of a second
                float turn = 1f - Mathf.Pow(0.001f, dt);             // snaps onto the target line almost at once
                r.vel = Vector3.Lerp(r.vel, dir * sp, turn);
                Vector3 now = prev + r.vel * dt;
                r.go.transform.position = now;
                if (r.vel.sqrMagnitude > 0.01f) r.go.transform.rotation = Quaternion.LookRotation(r.vel);
                if (!alive && r.dmg > 0f && cfg != null && WaveSpawner.I != null)
                {   // no plane of its own (or it died on the way): the first plane it flies through takes it, splash included
                    Enemy hit = null;
                    foreach (var e in WaveSpawner.I.Active)
                        if (!e.Dead && !e.Striking && Crossed(prev, now, e, cfg)) { hit = e; break; }
                    if (hit != null)
                    {
                        Vector3 at = hit.transform.position;
                        hit.TakeDamage(r.dmg);
                        if (r.splash > 0f)
                            foreach (var e in new List<Enemy>(WaveSpawner.I.Active))   // a kill removes from Active: iterate a copy
                                if (e != hit && !e.Dead && !e.Striking && Mathf.Abs(e.X - hit.X) < r.splash && Mathf.Abs(e.Z - hit.Z) < r.splash) e.TakeDamage(r.dmg * 0.6f);
                        FXManager.I.Sparks(at, r.color, 6);
                        r.live = false;
                        r.go.SetActive(false);
                        continue;
                    }
                }
                if ((tp - now).magnitude < 1.0f || r.t > (r.target != null ? 1.0f : 0.45f))   // an idle rocket (nothing to hit) burns out short, ahead of the squad
                {
                    FXManager.I.Sparks(now, r.color, 6);   // a burst of fire, not a full explosion + shake per rocket (2-3 rockets/s per plane now)
                    r.live = false;
                    r.go.SetActive(false);
                }
            }
        }
    }
}
