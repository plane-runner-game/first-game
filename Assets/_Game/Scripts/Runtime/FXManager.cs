// FXManager.cs
// All the juice: explosions, sparks, floating numbers, expanding rings, screen shake,
// screen flash, planes flying in to join the squad and planes falling out of it.
using System.Collections.Generic;
using UnityEngine;

namespace SkySquad
{
    public class FXManager : MonoBehaviour
    {
        public static FXManager I { get; private set; }

        public GameObject explosionPrefab;
        public GameObject sparksPrefab;
        public GameObject floatTextPrefab;
        public GameObject ringPrefab;
        public Vector3 ShakeOffset { get; private set; }
        public HUD hud;

        float shake;

        class Mover { public GameObject go; public Vector3 from, to, vel; public float t, life; public int kind; public Vector3 spin; public Transform parent; }
        readonly List<Mover> movers = new List<Mover>();
        class RingFx { public LineRenderer lr; public Vector3 center; public float t, life, r, vr; public Color c; }
        readonly List<RingFx> rings = new List<RingFx>();
        class Ftext { public TMPro.TextMeshPro tmp; public float t, life; public Color c; public float size; }
        readonly List<Ftext> ftexts = new List<Ftext>();

        void Awake() { I = this; }

        void Update()
        {
            float dt = Time.deltaTime;
            shake = Mathf.Max(0f, shake - dt);
            float m = 0.35f * shake / 0.4f;
            ShakeOffset = shake > 0f ? new Vector3(Random.Range(-m, m), Random.Range(-m, m), 0f) : Vector3.zero;
            for (int i = movers.Count - 1; i >= 0; i--)
            {
                var mv = movers[i];
                mv.t += dt;
                float k = Mathf.Min(1f, mv.t / mv.life);
                if (mv.kind == 0)
                { // joiner: ease in from the side into its slot
                    float e = 1f - Mathf.Pow(1f - k, 3f);
                    Vector3 target = mv.parent != null ? mv.parent.TransformPoint(mv.to) : mv.to;
                    mv.go.transform.position = Vector3.Lerp(mv.from, target, e);
                    mv.go.transform.rotation = Quaternion.Euler(0f, 0f, (1f - e) * (mv.from.x < 0 ? 35f : -35f));
                }
                else
                { // faller: tumble down
                    mv.vel += Vector3.down * 12f * dt;
                    mv.go.transform.position += mv.vel * dt;
                    mv.go.transform.Rotate(mv.spin * dt, Space.Self);
                    if (Random.value < 0.15f && sparksPrefab != null) Sparks(mv.go.transform.position, new Color(0.35f, 0.35f, 0.4f), 1);
                }
                if (mv.t >= mv.life) { Destroy(mv.go); movers.RemoveAt(i); }
            }
            for (int i = rings.Count - 1; i >= 0; i--)
            {
                var r = rings[i];
                r.t += dt; r.r += r.vr * dt;
                int n = r.lr.positionCount;
                for (int j = 0; j < n; j++)
                {
                    float a = j / (float)(n - 1) * Mathf.PI * 2f;
                    r.lr.SetPosition(j, r.center + new Vector3(Mathf.Cos(a) * r.r, Mathf.Sin(a) * r.r * 0.6f, 0f));
                }
                var c = r.c; c.a = 1f - r.t / r.life; r.lr.startColor = r.lr.endColor = c;
                if (r.t >= r.life) { Destroy(r.lr.gameObject); rings.RemoveAt(i); }
            }
            for (int i = ftexts.Count - 1; i >= 0; i--)
            {
                var f = ftexts[i];
                f.t += dt;
                float k = f.t / f.life;
                f.tmp.transform.position += Vector3.up * 2.2f * dt;
                float pop = f.t < 0.12f ? 1f + (0.12f - f.t) * 4f : 1f;
                f.tmp.transform.localScale = Vector3.one * pop;
                var c = f.c; c.a = k < 0.7f ? 1f : 1f - (k - 0.7f) / 0.3f; f.tmp.color = c;
                if (f.t >= f.life) { Destroy(f.tmp.gameObject); ftexts.RemoveAt(i); }
            }
        }

        public void Shake(float s) { shake = Mathf.Max(shake, s); }
        public void Flash(Color c, float dur) { if (hud != null) hud.Flash(c, dur); }

        public void Explosion(Vector3 p, bool big)
        {
            if (explosionPrefab == null) return;
            var go = Instantiate(explosionPrefab, p, Quaternion.identity, transform);
            go.transform.localScale = Vector3.one * (big ? 2.2f : 1f);
            var ps = go.GetComponent<ParticleSystem>();
            if (ps != null) ps.Play();
            Destroy(go, 2.5f);
            Ring(p, new Color(1f, 0.82f, 0.25f), big ? 14f : 8f);
            Shake(big ? 0.35f : 0.12f);
        }

        public void Sparks(Vector3 p, Color c, int n)
        {
            if (sparksPrefab == null) return;
            var go = Instantiate(sparksPrefab, p, Quaternion.identity, transform);
            var ps = go.GetComponent<ParticleSystem>();
            if (ps != null)
            {
                var main = ps.main; main.startColor = c;
                ps.Emit(n);
            }
            Destroy(go, 1.2f);
        }

        public void Ring(Vector3 center, Color c, float speed)
        {
            if (ringPrefab == null) return;
            var go = Instantiate(ringPrefab, center, Quaternion.identity, transform);
            var lr = go.GetComponent<LineRenderer>();
            rings.Add(new RingFx { lr = lr, center = center, t = 0f, life = 0.4f, r = 0.3f, vr = speed, c = c });
        }

        public void FloatText(Vector3 p, string text, Color c, float size)
        {
            if (floatTextPrefab == null) return;
            var go = Instantiate(floatTextPrefab, p, Quaternion.identity, transform);
            var tmp = go.GetComponent<TMPro.TextMeshPro>();
            tmp.text = text; tmp.color = c; tmp.fontSize = 6f * size;
            ftexts.Add(new Ftext { tmp = tmp, t = 0f, life = 1f, c = c, size = size });
        }

        public void Joiners(SquadController sq, int before, int after)
        {
            if (sq.CurrentPlanePrefab == null) return;
            int k = Mathf.Min(8, after - before);
            for (int i = 0; i < k; i++)
            {
                int slot = Mathf.Min(sq.VisibleCount - 1, before + i);
                float side = Random.value < 0.5f ? -1f : 1f;
                var go = Instantiate(sq.CurrentPlanePrefab, transform);
                var pv = go.GetComponent<PlaneVisual>(); if (pv != null) pv.enabled = false;
                go.transform.position = new Vector3(side * 14f, sq.transform.position.y - 2f + Random.value * 3f, -4f - Random.value * 4f);
                movers.Add(new Mover { go = go, from = go.transform.position, to = sq.SlotLocal(slot), t = 0f, life = 0.55f, kind = 0, parent = sq.formationRoot });
            }
        }

        public void Fallers(SquadController sq, int before, int after)
        {
            if (sq.CurrentPlanePrefab == null) return;
            int k = Mathf.Min(10, before - after);
            for (int i = 0; i < k; i++)
            {
                int slot = Mathf.Clamp(before - 1 - i, 0, sq.VisibleCount);
                var go = Instantiate(sq.CurrentPlanePrefab, transform);
                var pv = go.GetComponent<PlaneVisual>(); if (pv != null) pv.enabled = false;
                go.transform.position = sq.SlotWorld(slot);
                movers.Add(new Mover { go = go, vel = new Vector3(Random.Range(-6f, 6f), 2f, -3f), t = 0f, life = 1.1f, kind = 1, spin = new Vector3(Random.Range(-300f, 300f), 0f, Random.Range(-400f, 400f)) });
            }
        }

        public void UnitFall(GameObject unitPrefab, Vector3 worldPos, float scale)
        {
            if (unitPrefab == null) return;
            var go = Instantiate(unitPrefab, worldPos, Quaternion.identity, transform);
            go.transform.localScale = Vector3.one * scale;
            movers.Add(new Mover { go = go, vel = new Vector3(Random.Range(-5f, 5f), 1.5f, -6f), t = 0f, life = 0.9f, kind = 1, spin = new Vector3(Random.Range(-400f, 400f), 0f, Random.Range(-500f, 500f)) });
        }

        public void ClearAll()
        {
            foreach (var m in movers) if (m.go != null) Destroy(m.go);
            movers.Clear();
            foreach (var r in rings) if (r.lr != null) Destroy(r.lr.gameObject);
            rings.Clear();
            foreach (var f in ftexts) if (f.tmp != null) Destroy(f.tmp.gameObject);
            ftexts.Clear();
            shake = 0f;
        }
    }
}
