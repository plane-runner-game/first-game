// RocketPool.cs - homing rockets with a smoke trail that explode on arrival (visual only).
using System.Collections.Generic;
using UnityEngine;

namespace SkySquad
{
    public class RocketPool : MonoBehaviour
    {
        public GameObject rocketPrefab;
        class R { public GameObject go; public TrailRenderer trail; public object target; public Vector3 vel; public float t; public bool live; }
        readonly List<R> pool = new List<R>();

        public void Fire(Vector3 from, object target, Color c)
        {
            R r = null;
            foreach (var p in pool) if (!p.live) { r = p; break; }
            if (r == null)
            {
                var go = Instantiate(rocketPrefab, transform);
                r = new R { go = go, trail = go.GetComponentInChildren<TrailRenderer>() };
                pool.Add(r);
            }
            r.live = true;
            r.go.SetActive(true);
            r.go.transform.position = from;
            r.target = target;
            r.vel = new Vector3(Random.Range(-6f, 6f), 8f, 4f);
            r.t = 0f;
            if (r.trail != null) r.trail.Clear();
        }

        void Update()
        {
            float dt = Time.deltaTime;
            foreach (var r in pool)
            {
                if (!r.live) continue;
                r.t += dt;
                bool alive = r.target is Horde h ? !h.Dead : r.target is BossController b ? !b.Dead : r.target is Pickup p ? !p.Dead : false;
                Vector3 tp = alive ? AutoFire.TargetPos(r.target) : r.go.transform.position + Vector3.forward * 10f;
                Vector3 dir = (tp - r.go.transform.position).normalized;
                float k = Mathf.Min(1f, r.t / 0.6f);
                float sp = 26f + 45f * k;
                float turn = 1f - Mathf.Pow(0.02f, dt);
                r.vel = Vector3.Lerp(r.vel, dir * sp, turn);
                r.go.transform.position += r.vel * dt;
                if (r.vel.sqrMagnitude > 0.01f) r.go.transform.rotation = Quaternion.LookRotation(r.vel);
                if ((tp - r.go.transform.position).magnitude < 0.9f || r.t > 1.6f)
                {
                    FXManager.I.Explosion(r.go.transform.position, false);
                    r.live = false;
                    r.go.SetActive(false);
                }
            }
        }
    }
}
