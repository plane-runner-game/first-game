// TracerPool.cs - short glowing lines for gatling bullets and the laser beam (visual only).
using System.Collections.Generic;
using UnityEngine;

namespace SkySquad
{
    public class TracerPool : MonoBehaviour
    {
        public static TracerPool I { get; private set; }   // enemies borrow it for their own shots
        public Material material;
        class Tracer { public LineRenderer lr; public float t, life; public Color color; }
        readonly List<Tracer> pool = new List<Tracer>();

        void Awake() { I = this; }

        public void Fire(Vector3 a, Vector3 b, Color c, float life, float width)
        {
            Tracer tr = null;
            foreach (var p in pool) if (!p.lr.enabled) { tr = p; break; }
            if (tr == null)
            {
                var go = new GameObject("Tracer");
                go.transform.SetParent(transform, false);
                var lr = go.AddComponent<LineRenderer>();
                lr.material = material;
                lr.positionCount = 2;
                lr.useWorldSpace = true;
                lr.numCapVertices = 2;
                lr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
                lr.receiveShadows = false;
                tr = new Tracer { lr = lr };
                pool.Add(tr);
            }
            tr.lr.enabled = true;
            tr.lr.SetPosition(0, a);
            tr.lr.SetPosition(1, b);
            tr.lr.startWidth = tr.lr.endWidth = width;
            tr.color = c;
            tr.lr.startColor = tr.lr.endColor = c;
            tr.t = 0f; tr.life = life;
        }

        void Update()
        {
            float dt = Time.deltaTime;
            foreach (var tr in pool)
            {
                if (!tr.lr.enabled) continue;
                tr.t += dt;
                if (tr.t >= tr.life) { tr.lr.enabled = false; continue; }
                var c = tr.color; c.a = 1f - tr.t / tr.life;
                tr.lr.startColor = tr.lr.endColor = c;
            }
        }
    }
}
