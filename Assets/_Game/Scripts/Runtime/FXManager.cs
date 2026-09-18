// FXManager.cs
// All the juice: explosions, sparks, floating numbers, expanding rings, screen shake,
// screen flash, planes flying in to join the squad, and the wrecks of shot-down planes falling to the sea.
using System.Collections.Generic;
using UnityEngine;

namespace SkySquad
{
    public class FXManager : MonoBehaviour
    {
        public static FXManager I { get; private set; }

        public GameObject explosionPrefab;
        public GameObject sparksPrefab;
        public GameObject splashPrefab;    // the spray a wreck throws up when it hits the sea (2026-09-18); Sparks stand in when it is missing
        public GameObject floatTextPrefab;
        public GameObject ringPrefab;
        public GameObject coinPrefab;
        public Vector3 ShakeOffset { get; private set; }
        public HUD hud;

        float shake;

        class Mover { public GameObject go; public Vector3 from, to, vel; public float t, life; public int kind; public Vector3 spin; public Transform parent; }
        readonly List<Mover> movers = new List<Mover>();
        class RingFx { public LineRenderer lr; public Vector3 center; public float t, life, r, vr; public Color c; public bool flat; }
        readonly List<RingFx> rings = new List<RingFx>();
        class Ftext { public TMPro.TextMeshPro tmp; public float t, life; public Color c; public float size; }
        readonly List<Ftext> ftexts = new List<Ftext>();

        /// <summary>A shot-down plane on its way into the sea (2026-09-18, "make them fall to the water"). Until then a wreck was a
        /// fresh copy of the prefab that tumbled for 0.9 s and vanished in mid-air. Now it is the plane's own model, handed over by
        /// Enemy.Kill (or a clone of a squad plane, Fallers), and it lives through three beats: the FALL (gravity, the nose drops,
        /// it corkscrews, smoke and embers stream off it), the SPLASH when it reaches the waterline, and the SINK under the waves.</summary>
        class Wreck
        {
            public Transform tf;            // the model itself, parented to this manager
            public Transform[] props;       // its propellers, windmilling down
            public TrailRenderer trail;     // its smoke
            public Vector3 vel;             // x / y: sideways kick and vertical speed (u/s)
            public float air;               // its forward airspeed over the water (+ = away from the camera); the sea scrolls under it at ScrollSpeed, so it moves at air - scroll on screen
            public float yaw, pitch, bank;  // degrees; pitch + = nose down, the Enemy.Apply convention
            public float pitchTo, rollRate, propSpin, t, sunk, fireT;
            public float waterline;         // how high above the waterline its pivot sits when it touches (a boss hull is deep)
            public float sinkTime, sinkDepth;
            public bool big, inWater;
        }
        readonly List<Wreck> wrecks = new List<Wreck>();
        const float WreckGravity = 20f;     // u/s^2: from the swarm's altitude (y ~6) to the sea (-2.5) in about a second
        const float WreckDrag = 1f;         // airspeed halves every 0.7 s once the engine is dead

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
                { // coin: tossed up, falls, spins, shrinks away
                    mv.vel += Vector3.down * 14f * dt;
                    mv.go.transform.position += mv.vel * dt;
                    mv.go.transform.Rotate(mv.spin * dt, Space.Self);
                    mv.go.transform.localScale = Vector3.one * (k > 0.6f ? 1f - (k - 0.6f) / 0.4f : 1f);
                }
                if (mv.t >= mv.life) { Destroy(mv.go); movers.RemoveAt(i); }
            }
            TickWrecks(dt);
            for (int i = rings.Count - 1; i >= 0; i--)
            {
                var r = rings[i];
                r.t += dt; r.r += r.vr * dt;
                int n = r.lr.positionCount;
                for (int j = 0; j < n; j++)
                {
                    float a = j / (float)(n - 1) * Mathf.PI * 2f;
                    r.lr.SetPosition(j, r.center + (r.flat ? new Vector3(Mathf.Cos(a) * r.r, 0f, Mathf.Sin(a) * r.r)          // a ripple lying on the water
                                                          : new Vector3(Mathf.Cos(a) * r.r, Mathf.Sin(a) * r.r * 0.6f, 0f)));  // a blast ring facing the camera
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

        /// <summary>One frame of every wreck: the fall, the splash, the sink.</summary>
        void TickWrecks(float dt)
        {
            var gm = GameManager.I;
            float sea = gm != null && gm.config != null ? gm.config.seaLevel : -2.5f;
            float scroll = gm != null ? (gm.State == GameState.Playing ? gm.ScrollSpeed : gm.State == GameState.Paused ? 0f : gm.config.scrollSpeed * 0.6f) : 9f;   // the same pace WorldScroller moves the sea at
            for (int i = wrecks.Count - 1; i >= 0; i--)
            {
                var w = wrecks[i];
                if (w.tf == null) { wrecks.RemoveAt(i); continue; }
                w.t += dt;
                Vector3 p = w.tf.position;
                if (!w.inWater)
                {
                    // THE FALL: gravity takes it, the sideways kick bleeds off, the nose drops toward pitchTo and it rolls on around
                    // its own axis - a corkscrew. Its airspeed decays with the engine dead, so on screen it starts at its old pace
                    // and ends up carried toward the camera with the sea like everything else that floats.
                    w.vel.y -= WreckGravity * dt;
                    w.vel.x *= Mathf.Exp(-1.2f * dt);
                    w.air *= Mathf.Exp(-WreckDrag * dt);
                    p += new Vector3(w.vel.x, w.vel.y, w.air - scroll) * dt;
                    w.pitch = Mathf.Lerp(w.pitch, w.pitchTo, 1f - Mathf.Exp(-2.4f * dt));
                    w.bank += w.rollRate * dt;
                    w.propSpin = Mathf.Lerp(w.propSpin, 300f, 1f - Mathf.Exp(-1.5f * dt));   // the prop windmills down
                    w.fireT -= dt;
                    if (w.fireT <= 0f)
                    {   // embers stream off it; a boss also throws small secondary blasts on the way down
                        Sparks(p + Random.insideUnitSphere * (w.big ? 0.8f : 0.2f), new Color(1f, 0.55f, 0.2f), w.big ? 3 : 1);
                        w.fireT = w.big ? 0.05f : 0.11f;
                        if (w.big && Random.value < 0.2f)
                        {
                            Vector3 b = p + Random.insideUnitSphere * 1.2f;
                            Sparks(b, new Color(1f, 0.85f, 0.4f), 10); Ring(b, new Color(1f, 0.6f, 0.25f), 7f);
                        }
                    }
                    if (p.y <= sea + w.waterline)
                    {   // SPLASHDOWN
                        p.y = sea + w.waterline;
                        w.inWater = true; w.sunk = 0f; w.vel = Vector3.zero; w.air = 0f;
                        w.rollRate *= 0.15f;
                        Splash(p, w.big);
                        if (w.trail != null) w.trail.emitting = false;   // the smoke stops; what is already in the air fades over the splash
                    }
                }
                else
                {
                    // THE SINK: it settles nose-first and goes under, carried back with the water. The sea is opaque, so once it
                    // is below the waves it is gone, and the object is destroyed there (or when it passes behind the camera).
                    w.sunk += dt;
                    float k = Mathf.Clamp01(w.sunk / w.sinkTime);
                    p.y = sea + w.waterline - w.sinkDepth * k * k;
                    p.z -= scroll * dt;
                    w.rollRate *= Mathf.Exp(-3f * dt);
                    w.bank += w.rollRate * dt;
                    w.pitch = Mathf.Lerp(w.pitch, 80f, 1f - Mathf.Exp(-1.5f * dt));   // the tail comes up as the nose goes under
                    if (k >= 1f || p.z < -12f) { Destroy(w.tf.gameObject); wrecks.RemoveAt(i); continue; }
                }
                w.tf.position = p;
                w.tf.rotation = Quaternion.Euler(w.pitch, w.yaw, w.bank);
                if (w.props != null) foreach (var pr in w.props) if (pr != null) pr.Rotate(0f, 0f, w.propSpin * dt, Space.Self);
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

        /// <summary>A wreck hitting the sea: a column of white spray, two ripples spreading on the water, the splash sound.
        /// The rings are laid flat (the camera looks down on the water at 13.5 degrees, so they read as ellipses).</summary>
        public void Splash(Vector3 p, bool big)
        {
            var gm = GameManager.I;
            float sea = gm != null && gm.config != null ? gm.config.seaLevel : -2.5f;
            Vector3 s = new Vector3(p.x, sea + 0.2f, p.z);   // on the crests, so the spray is not born under the waves
            var spray = new Color(0.9f, 0.96f, 1f);
            if (splashPrefab != null)
            {
                var go = Instantiate(splashPrefab, s, Quaternion.identity, transform);
                go.transform.localScale = Vector3.one * (big ? 2.4f : 1f);
                var ps = go.GetComponent<ParticleSystem>();
                if (ps != null) ps.Emit(big ? 60 : 22);
                Destroy(go, 1.5f);
            }
            else Sparks(s, spray, big ? 40 : 14);
            Ring(s, spray, big ? 15f : 8f, true);
            Ring(s, new Color(spray.r, spray.g, spray.b, 0.5f), big ? 9f : 4.5f, true);
            if (big) Shake(0.2f);
            if (AudioManager.I != null) AudioManager.I.Play(Sfx.Splash);
        }

        public void Ring(Vector3 center, Color c, float speed, bool flat = false)
        {
            if (ringPrefab == null) return;
            var go = Instantiate(ringPrefab, center, Quaternion.identity, transform);
            var lr = go.GetComponent<LineRenderer>();
            rings.Add(new RingFx { lr = lr, center = center, t = 0f, life = flat ? 0.6f : 0.4f, r = 0.3f, vr = speed, c = c, flat = flat });
        }

        public void FloatText(Vector3 p, string text, Color c, float size)
        {
            if (floatTextPrefab == null) return;
            var go = Instantiate(floatTextPrefab, p, Quaternion.identity, transform);
            var tmp = go.GetComponent<TMPro.TextMeshPro>();
            tmp.text = text; tmp.color = c; tmp.fontSize = 6f * size;
            ftexts.Add(new Ftext { tmp = tmp, t = 0f, life = 1f, c = c, size = size });
        }

        /// <summary>Coins popping out of a kill: a few gold discs tossed up that fall and fade, with the "+N" over them.</summary>
        public void CoinBurst(Vector3 p, int value)
        {
            FloatText(p + Vector3.up * 1.2f, "+" + value, new Color(1f, 0.82f, 0.25f), value >= 10 ? 1.1f : 0.8f);
            if (coinPrefab == null) return;
            int n = Mathf.Clamp(1 + value / 4, 1, 5);
            for (int i = 0; i < n; i++)
            {
                var go = Instantiate(coinPrefab, p + Random.insideUnitSphere * 0.3f, Random.rotation, transform);
                movers.Add(new Mover { go = go, vel = new Vector3(Random.Range(-3f, 3f), Random.Range(4f, 7f), Random.Range(-2f, 1f)), t = 0f, life = 0.75f, kind = 2, spin = new Vector3(0f, Random.Range(300f, 700f), Random.Range(-200f, 200f)) });
            }
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

        /// <summary>Planes lost from the squad: a clone of each drops out of its slot and falls to the sea like any other wreck
        /// (it flew at the squad's pace, so it hangs near you for a moment and then falls back and away).</summary>
        public void Fallers(SquadController sq, int before, int after)
        {
            if (sq.CurrentPlanePrefab == null) return;
            var gm = GameManager.I;
            int k = Mathf.Min(10, before - after);
            for (int i = 0; i < k; i++)
            {
                int slot = Mathf.Clamp(i == 0 && sq.FallSlot >= 0 ? sq.FallSlot : before - 1 - i, 0, sq.VisibleCount);   // a strike drops the plane it hit
                var go = Instantiate(sq.CurrentPlanePrefab, transform);
                var pv = go.GetComponent<PlaneVisual>(); if (pv != null) pv.enabled = false;
                go.transform.position = sq.SlotWorld(slot);
                var w = new Wreck
                {
                    tf = go.transform, big = false, yaw = 0f, pitch = 0f, bank = 0f,
                    pitchTo = Random.Range(45f, 75f), rollRate = (Random.value < 0.5f ? -1f : 1f) * Random.Range(120f, 260f),
                    vel = new Vector3(Random.Range(-6f, 6f), 2f, 0f), air = gm != null ? gm.ScrollSpeed : 9f,
                    propSpin = 2400f, waterline = 0.15f, sinkTime = 0.8f, sinkDepth = 1.8f,
                };
                w.trail = SmokeTrail(go.transform, false);
                wrecks.Add(w);
            }
        }

        /// <summary>A shot-down enemy: its model leaves the dead Enemy (which WaveSpawner destroys along with the hp number and the
        /// boss bar) and falls on as a burning wreck - see Wreck. Taking the model itself, not a copy, keeps its tint, its size at
        /// that distance and the attitude it was flying at, so nothing pops at the moment of death.</summary>
        public void PlaneWreck(Enemy en)
        {
            if (en == null || en.model == null) return;
            en.ClearHitFlash();   // the killing hit left it HDR-white
            var tf = en.model;
            bool big = en.Kind.miniBoss;
            tf.SetParent(transform, true);
            var w = new Wreck
            {
                tf = tf, big = big, yaw = 180f, pitch = en.Pitch, bank = en.Bank,   // it flew nose toward the camera: it keeps that yaw
                pitchTo = big ? Random.Range(45f, 65f) : Random.Range(60f, 85f),
                rollRate = (Random.value < 0.5f ? -1f : 1f) * (big ? Random.Range(30f, 60f) : Random.Range(150f, 320f)),
                vel = new Vector3(Random.Range(-2.5f, 2.5f), big ? 0.5f : Random.Range(0.5f, 2.5f), 0f),
                // a fighter flew at the swarm's pace toward you; a boss held the line, i.e. flew at the squad's pace - both keep that momentum
                air = big ? (GameManager.I != null ? GameManager.I.ScrollSpeed : 9f) : -en.Kind.approachSpeed * en.SpeedMult,
                propSpin = 2400f,
                waterline = big ? 0.9f : 0.15f, sinkTime = big ? 1.6f : 0.8f, sinkDepth = big ? 4.5f : 1.8f,
                trail = en.trail,
                props = en.propellers != null && en.propellers.Length > 0 ? en.propellers : en.propeller != null ? new[] { en.propeller } : null,
            };
            if (w.trail != null) { w.trail.Clear(); w.trail.time = 0.7f; w.trail.emitting = true; }   // the fighter's strike-run smoke, streaming now
            else w.trail = SmokeTrail(tf, big);
            wrecks.Add(w);
        }

        /// <summary>A smoke trail for a wreck that has none of its own (the bosses, the squad's planes): hot at the tail, fading to
        /// pale smoke, on the same additive material the rings and bullet trails use.</summary>
        TrailRenderer SmokeTrail(Transform tf, bool big)
        {
            var mat = ringPrefab != null ? ringPrefab.GetComponent<LineRenderer>() : null;
            if (mat == null || mat.sharedMaterial == null) return null;
            var go = new GameObject("Smoke"); go.transform.SetParent(tf, false);
            var tr = go.AddComponent<TrailRenderer>();
            tr.sharedMaterial = mat.sharedMaterial; tr.time = big ? 1f : 0.7f; tr.startWidth = big ? 1.1f : 0.34f; tr.endWidth = 0.05f; tr.minVertexDistance = 0.06f;
            tr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            tr.startColor = new Color(1f, 0.62f, 0.3f, 0.95f); tr.endColor = new Color(0.75f, 0.75f, 0.8f, 0f);
            return tr;
        }

        public void ClearAll()
        {
            foreach (var m in movers) if (m.go != null) Destroy(m.go);
            movers.Clear();
            foreach (var w in wrecks) if (w.tf != null) Destroy(w.tf.gameObject);
            wrecks.Clear();
            foreach (var r in rings) if (r.lr != null) Destroy(r.lr.gameObject);
            rings.Clear();
            foreach (var f in ftexts) if (f.tmp != null) Destroy(f.tmp.gameObject);
            ftexts.Clear();
            shake = 0f;
        }
    }
}
