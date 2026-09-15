// RocketPool.cs - fast fire rockets with a short flame tail that explode on arrival (visual only: the
// damage is dealt the moment they are fired, AutoFire). They leave the plane straight and fast with a
// touch of spread and home in the rest of the way - requested: "shoots fire, nicer and faster".
using System.Collections.Generic;
using UnityEngine;

namespace SkySquad
{
    public class RocketPool : MonoBehaviour
    {
        public GameObject rocketPrefab;
        class R { public GameObject go; public TrailRenderer trail; public Renderer body; public object target; public Vector3 vel; public Color color; public float t; public bool live; }
        static MaterialPropertyBlock mpb;
        static readonly int BaseColor = Shader.PropertyToID("_BaseColor");
        readonly List<R> pool = new List<R>();

        public void Fire(Vector3 from, object target, Color c)
        {
            R r = null;
            foreach (var p in pool) if (!p.live) { r = p; break; }
            if (r == null)
            {
                var go = Instantiate(rocketPrefab, transform);
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
            r.target = target; r.color = c;
            r.vel = new Vector3(Random.Range(-1.5f, 1.5f), Random.Range(-0.3f, 0.6f), 55f);   // straight out of the pods, a little spread
            r.t = 0f;
            if (r.trail != null)
            {   // the tail is fire: the weapon colour into a hot yellow-white core, fading out
                r.trail.Clear();
                r.trail.startColor = new Color(1f, 0.8f, 0.25f, 1f);
                r.trail.endColor = new Color(1f, 0.3f, 0.05f, 0f);
            }
        }

        void Update()
        {
            float dt = Time.deltaTime;
            foreach (var r in pool)
            {
                if (!r.live) continue;
                r.t += dt;
                bool alive = r.target is Enemy en ? !en.Dead : r.target is BossController b ? !b.Dead : r.target is Breakable bk ? !bk.Dead : false;
                Vector3 tp = alive ? AutoFire.TargetPos(r.target) : r.go.transform.position + Vector3.forward * 10f;
                Vector3 dir = (tp - r.go.transform.position).normalized;
                float sp = 55f + 45f * Mathf.Min(1f, r.t / 0.3f);   // 55 -> 100 u/s in a third of a second
                float turn = 1f - Mathf.Pow(0.001f, dt);             // snaps onto the target line almost at once
                r.vel = Vector3.Lerp(r.vel, dir * sp, turn);
                r.go.transform.position += r.vel * dt;
                if (r.vel.sqrMagnitude > 0.01f) r.go.transform.rotation = Quaternion.LookRotation(r.vel);
                if ((tp - r.go.transform.position).magnitude < 1.0f || r.t > 1.0f)
                {
                    FXManager.I.Sparks(r.go.transform.position, r.color, 6);   // a burst of fire, not a full explosion + shake per rocket (2-3 rockets/s per plane now)
                    r.live = false;
                    r.go.SetActive(false);
                }
            }
        }
    }
}
