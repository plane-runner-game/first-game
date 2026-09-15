// ThreatMarkers.cs
// The "incoming" indicator: a lock-on reticle (ring + corner brackets, billboarded) pinned on every fighter
// inside threatWarnRange of the strike line. Far away it is large, faint and slowly turning; as the fighter
// nears the line it tightens onto the plane, spins faster and goes red, pulsing. The moment the fighter
// crosses and commits to its strike the reticle pops outward and fades - the lock is "released". This
// replaces the old dashed line: it points at the actual threat and reads at a glance.
using System.Collections.Generic;
using UnityEngine;

namespace SkySquad
{
    public class ThreatMarkers : MonoBehaviour
    {
        public Material material;
        public int poolSize = 40;
        public Color farColor = new Color(1f, 1f, 1f, 0.35f);
        public Color nearColor = new Color(1f, 0.2f, 0.25f, 1f);
        public float popSeconds = 0.3f;   // the release pop after the fighter crosses the line
        public Color bossColor = new Color(1f, 0.6f, 0.15f, 0.85f);   // the boss wears a big slow orange reticle from the moment he spawns until he parks

        readonly List<Transform> pool = new List<Transform>();
        readonly List<Renderer> rends = new List<Renderer>();
        static MaterialPropertyBlock mpb;
        static readonly int BaseColor = Shader.PropertyToID("_BaseColor");

        void Awake()
        {
            for (int i = 0; i < poolSize; i++)
            {
                var q = GameObject.CreatePrimitive(PrimitiveType.Quad);
                Destroy(q.GetComponent<Collider>());
                q.name = "Marker" + i; q.transform.SetParent(transform, false);
                var r = q.GetComponent<MeshRenderer>();
                r.sharedMaterial = material; r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off; r.receiveShadows = false;
                q.SetActive(false);
                pool.Add(q.transform); rends.Add(r);
            }
        }

        void LateUpdate()
        {
            var gm = GameManager.I;
            var cam = Camera.main;
            int used = 0;
            if (gm != null && cam != null && (gm.State == GameState.Playing || gm.State == GameState.Paused) && WaveSpawner.I != null)
            {
                var cfg = gm.config;
                if (mpb == null) mpb = new MaterialPropertyBlock();
                float t = Time.time;
                var camRot = cam.transform.rotation;
                foreach (var e in WaveSpawner.I.Active)
                {
                    if (used >= pool.Count) break;
                    if (e == null || e.Dead || e.Held) continue;
                    float size, spin, ahead; Color c;
                    if (e.Kind.miniBoss)
                    {   // the boss: a big, slow, orange reticle the whole way in, so he is unmistakable from the horizon; off once he parks
                        if (e.Parked) continue;
                        size = 1.7f * e.Kind.scale * (1f + 0.04f * Mathf.Sin(t * 3f));
                        spin = t * 20f; ahead = 3.5f;
                        c = bossColor;
                    }
                    else
                    {
                        float d = e.Z - cfg.diveZ;
                        bool pop = e.Striking && e.StrikeT < popSeconds;
                        if (!pop && (e.Striking || d > cfg.threatWarnRange)) continue;

                        float n = e.Striking ? 1f : Mathf.Clamp01(1f - d / cfg.threatWarnRange);   // 0 far .. 1 at the line
                        float k = n * n;                                                            // most of the change happens close in
                        size = Mathf.Lerp(2.8f, 1.25f, k) * e.Kind.scale * 1.5f;
                        spin = t * Mathf.Lerp(35f, 240f, k); ahead = 1.4f;
                        c = Color.Lerp(farColor, nearColor, k);
                        if (n > 0.6f) c.a *= 0.8f + 0.2f * Mathf.Sin(t * 16f);                      // pulses when it is nearly there
                        if (pop)
                        {   // lock released: flares out and fades
                            float u = e.StrikeT / popSeconds;
                            size = Mathf.Lerp(1.25f, 2.4f, u * u) * e.Kind.scale * 1.5f;
                            c = nearColor; c.a = 1f - u;
                        }
                    }

                    var m = pool[used]; var r = rends[used]; used++;
                    if (!m.gameObject.activeSelf) m.gameObject.SetActive(true);
                    Vector3 p = e.transform.position;
                    Vector3 toCam = (cam.transform.position - p).normalized;
                    m.position = p + toCam * ahead;                                            // in front of the plane so the ring is never cut by the wings
                    m.rotation = camRot * Quaternion.Euler(0f, 0f, spin);
                    m.localScale = Vector3.one * size;
                    mpb.SetColor(BaseColor, c);
                    r.SetPropertyBlock(mpb);
                }
            }
            for (int i = used; i < pool.Count; i++) if (pool[i].gameObject.activeSelf) pool[i].gameObject.SetActive(false);
        }
    }
}
