// SceneBuilder.LandGates.cs (Editor only)
// Where the planes come from in the land worlds (2026-10-08: "the planes come out of something, not all out of fog - in the city from between
// destroyed buildings; every world different, something exclusive and beautiful"). Each land world ends in its own gate, standing at GateZ
// across the lane: a dark hall (HallHW either side of the lane, HallH tall, HallLen deep, a glow at its back) that the fighters, the bosses
// and the crates fly out of, dressed as something of that world - two collapsed towers, a step pyramid, a stadium tunnel, an assembly hangar,
// a mine in a mesa, a giant gift box, a cave, a hollow log, a beehive. The cast is drawn all the way back inside the hall (WorldEntry.appearZ),
// so a plane is seen leaving the dark mouth instead of growing from a point. Around each gate, its life: smoke and fire, bats, bees, snow, sand,
// floodlights, a shuttle launch. The gate stands still; the world scrolls toward the squad (WorldScroller.loopLength).
using System.Collections.Generic;
using TMPro;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;

namespace SkySquad.EditorTools
{
    public static partial class SceneBuilder
    {
        const float GateZ = 140f, HallHW = 8.5f, HallH = 15f, HallLen = 32f;
        const float GateAppearZ = GateZ + 18f, GateAppearRange = 12f;   // the cast is full size up to 158, nothing past 170 (deep in the hall)
        const float LandLoop = 300f, LandLoopFrom = -30f;              // the scenery loops over z -30..270, re-entering deep in the haze

        class GateKit { public Transform root; public Mats M; public string id; public LandKit K; public float clearX = 16f; }

        static float GY(float h) { return SeaLevel + h; }

        static GameObject GBox(Transform p, string n, Vector3 c, Vector3 size, Material m, Vector3 euler = default(Vector3), bool shadow = true)
        {
            var go = GameObject.CreatePrimitive(PrimitiveType.Cube); Object.DestroyImmediate(go.GetComponent<Collider>());
            go.name = n; go.transform.SetParent(p, false); go.transform.position = c; go.transform.rotation = Quaternion.Euler(euler); go.transform.localScale = size;
            var r = go.GetComponent<MeshRenderer>(); r.sharedMaterial = m; r.shadowCastingMode = shadow ? ShadowCastingMode.On : ShadowCastingMode.Off; r.receiveShadows = true;
            return go;
        }

        static GameObject GPrim(Transform p, PrimitiveType type, string n, Vector3 c, Vector3 size, Material m, Vector3 euler = default(Vector3))
        {
            var go = GameObject.CreatePrimitive(type); Object.DestroyImmediate(go.GetComponent<Collider>());
            go.name = n; go.transform.SetParent(p, false); go.transform.position = c; go.transform.rotation = Quaternion.Euler(euler); go.transform.localScale = size;
            var r = go.GetComponent<MeshRenderer>(); r.sharedMaterial = m; r.shadowCastingMode = ShadowCastingMode.Off;
            return go;
        }

        static Material GLit(string id, string part, Color c, float smooth = 0.15f) { return Lit("Gate_" + id + "_" + part, c, smooth); }
        static Material GGlow(string id, string part, Color hdr) { return Unlit("Gate_" + id + "_" + part, hdr); }
        static Material GAdd(string id, string part, Color c) { var m = Transparent("Gate_" + id + "_" + part, c, true); m.SetTexture("_BaseMap", SoftTexture()); return m; }
        static Material GTex(string id, string part, Texture2D tex, Vector2 tiling, Color tint, float emission = 0f)
        {
            return Lit("Gate_" + id + "_" + part, tint, 0.1f).Also(m =>
            {
                m.SetTexture("_BaseMap", tex); m.SetTextureScale("_BaseMap", tiling);
                if (emission > 0f) { m.EnableKeyword("_EMISSION"); m.SetTexture("_EmissionMap", tex); m.SetTextureScale("_EmissionMap", tiling); m.SetColor("_EmissionColor", Color.white * emission); m.globalIlluminationFlags = MaterialGlobalIlluminationFlags.None; }
                else m.DisableKeyword("_EMISSION");
                EditorUtility.SetDirty(m);
            });
        }
        static Material AlphaParticle() { var m = Particle("GateAlphaParticle", Color.white, false); m.SetTexture("_BaseMap", SoftTexture()); return m; }

        static Texture2D GateTexture(string name, int w, int h, System.Func<int, int, Color> paint)
        {
            var t = new Texture2D(w, h, TextureFormat.RGB24, true);
            var px = new Color[w * h]; for (int y = 0; y < h; y++) for (int x = 0; x < w; x++) px[y * w + x] = paint(x, y);
            t.SetPixels(px); t.Apply();
            return SaveTex(t, name);
        }

        // ------------------------------------------------------------------ meshes
        static void GQuad(List<Vector3> v, List<Vector2> uv, List<int> t, Vector3 a, Vector3 b, Vector3 c, Vector3 d, Vector2 ua, Vector2 ub, Vector2 uc, Vector2 ud, Vector3 outward)
        {
            int i = v.Count; v.Add(a); v.Add(b); v.Add(c); v.Add(d); uv.Add(ua); uv.Add(ub); uv.Add(uc); uv.Add(ud);
            if (Vector3.Dot(Vector3.Cross(b - a, c - a), outward) >= 0f) { t.Add(i); t.Add(i + 1); t.Add(i + 2); t.Add(i); t.Add(i + 2); t.Add(i + 3); }
            else { t.Add(i); t.Add(i + 2); t.Add(i + 1); t.Add(i); t.Add(i + 3); t.Add(i + 2); }
        }

        /// <summary>A body of revolution about the y axis (a beehive, a stepped pyramid with 4 sides): `prof` is (radius, height) bottom to top. Face 0
        /// looks at -z (the camera). Quads whose centre falls in the doorway (|x| &lt; holeHW, height &lt; holeTop, front half) are left out. Flat shaded.</summary>
        static Mesh LatheMesh(string name, Vector2[] prof, int sides, float holeHW, float holeTop, float uTiles, float vScale, int sub = 1)
        {
            var v = new List<Vector3>(); var uv = new List<Vector2>(); var t = new List<int>();
            for (int k = 0; k < sides; k++)
            {
                float a0 = (k - 0.5f) / sides * Mathf.PI * 2f, a1 = (k + 0.5f) / sides * Mathf.PI * 2f;
                for (int j = 0; j + 1 < prof.Length; j++)
                {
                    Vector3 P(Vector2 p, float a) { return new Vector3(p.x * Mathf.Sin(a), p.y, -p.x * Mathf.Cos(a)); }
                    Vector3 A0 = P(prof[j], a0), B0 = P(prof[j], a1), C0 = P(prof[j + 1], a1), D0 = P(prof[j + 1], a0);
                    for (int q = 0; q < sub; q++)
                    {   // a wide flat face (a pyramid's) is cut into columns, so the doorway takes only its own
                        float f0 = (float)q / sub, f1 = (float)(q + 1) / sub;
                        Vector3 A = Vector3.Lerp(A0, B0, f0), B = Vector3.Lerp(A0, B0, f1), C = Vector3.Lerp(D0, C0, f1), D = Vector3.Lerp(D0, C0, f0);
                        Vector3 c = (A + B + C + D) * 0.25f;
                        if (c.z < 0f && Mathf.Abs(c.x) < holeHW && c.y < holeTop) continue;
                        if ((A - D).sqrMagnitude < 1e-6f && (B - C).sqrMagnitude < 1e-6f) continue;
                        Vector3 outw = new Vector3(c.x, 0f, c.z).normalized + Vector3.up * 0.5f;
                        float u0 = (k + f0) / sides * uTiles, u1 = (k + f1) / sides * uTiles;
                        GQuad(v, uv, t, A, B, C, D, new Vector2(u0, A.y * vScale), new Vector2(u1, B.y * vScale), new Vector2(u1, C.y * vScale), new Vector2(u0, D.y * vScale), outw);
                    }
                }
            }
            var m = new Mesh { name = name }; m.indexFormat = IndexFormat.UInt32; m.SetVertices(v); m.SetUVs(0, uv); m.SetTriangles(t, 0); m.RecalculateNormals(); m.RecalculateBounds();
            return SaveMesh(m);
        }

        /// <summary>A hollow tube along +z from 0 to len (the giant log): submesh 0 the bark outside, 1 the wood inside, 2 the cut face at z 0.</summary>
        static Mesh TubeMesh(string name, float rOut, float rIn, float len, int segs)
        {
            var v = new List<Vector3>(); var uv = new List<Vector2>(); var t0 = new List<int>(); var t1 = new List<int>(); var t2 = new List<int>();
            for (int k = 0; k < segs; k++)
            {
                float a0 = (float)k / segs * Mathf.PI * 2f, a1 = (float)(k + 1) / segs * Mathf.PI * 2f;
                Vector3 d0 = new Vector3(Mathf.Sin(a0), Mathf.Cos(a0), 0f), d1 = new Vector3(Mathf.Sin(a1), Mathf.Cos(a1), 0f), dm = (d0 + d1).normalized;
                float u0 = (float)k / segs * 8f, u1 = (float)(k + 1) / segs * 8f;
                GQuad(v, uv, t0, d0 * rOut, d1 * rOut, d1 * rOut + Vector3.forward * len, d0 * rOut + Vector3.forward * len, new Vector2(u0, 0f), new Vector2(u1, 0f), new Vector2(u1, len / 10f), new Vector2(u0, len / 10f), dm);
                GQuad(v, uv, t1, d0 * rIn, d1 * rIn, d1 * rIn + Vector3.forward * len, d0 * rIn + Vector3.forward * len, new Vector2(u0, 0f), new Vector2(u1, 0f), new Vector2(u1, len / 10f), new Vector2(u0, len / 10f), -dm);
                Vector2 R(Vector3 p) { return new Vector2(p.x / (2f * rOut) + 0.5f, p.y / (2f * rOut) + 0.5f); }
                GQuad(v, uv, t2, d0 * rIn, d1 * rIn, d1 * rOut, d0 * rOut, R(d0 * rIn), R(d1 * rIn), R(d1 * rOut), R(d0 * rOut), Vector3.back);
            }
            var m = new Mesh { name = name }; m.SetVertices(v); m.SetUVs(0, uv); m.subMeshCount = 3; m.SetTriangles(t0, 0); m.SetTriangles(t1, 1); m.SetTriangles(t2, 2); m.RecalculateNormals(); m.RecalculateBounds();
            return SaveMesh(m);
        }

        /// <summary>An open cone, apex at the origin, opening along +y (a searchlight's beam, a rocket's flame).</summary>
        static Mesh ConeMesh(string name, float len, float radius, int segs)
        {
            var v = new List<Vector3>(); var uv = new List<Vector2>(); var t = new List<int>();
            for (int k = 0; k < segs; k++)
            {
                float a0 = (float)k / segs * Mathf.PI * 2f, a1 = (float)(k + 1) / segs * Mathf.PI * 2f;
                Vector3 b0 = new Vector3(Mathf.Sin(a0) * radius, len, Mathf.Cos(a0) * radius), b1 = new Vector3(Mathf.Sin(a1) * radius, len, Mathf.Cos(a1) * radius);
                Vector3 tip = Vector3.zero, tip2 = Vector3.up * 0.001f;
                GQuad(v, uv, t, tip, tip2, b1, b0, new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f), new Vector2(0.5f, 1f), new Vector2(0.5f, 1f), new Vector3((b0.x + b1.x), 0f, (b0.z + b1.z)));
            }
            var m = new Mesh { name = name }; m.SetVertices(v); m.SetUVs(0, uv); m.SetTriangles(t, 0); m.RecalculateNormals(); m.RecalculateBounds();
            return SaveMesh(m);
        }

        // ------------------------------------------------------------------ particles
        static ParticleSystem Ambient(Transform parent, string name, Vector3 pos, Vector3 box, float rate, Vector2 life, Vector3 velMin, Vector3 velMax, Vector2 size, Color c0, Color c1, Material mat, float noise = 0f, float gravity = 0f, int max = 300, bool prewarm = true)
        {
            var go = new GameObject(name); go.transform.SetParent(parent, false); go.transform.position = pos;
            var ps = go.AddComponent<ParticleSystem>();
            var main = ps.main; main.loop = true; main.playOnAwake = true; main.prewarm = prewarm; main.maxParticles = max; main.simulationSpace = ParticleSystemSimulationSpace.World;
            main.startLifetime = new ParticleSystem.MinMaxCurve(life.x, life.y); main.startSpeed = 0f; main.startSize = new ParticleSystem.MinMaxCurve(size.x, size.y);
            main.startColor = new ParticleSystem.MinMaxGradient(c0, c1); main.gravityModifier = gravity;
            var em = ps.emission; em.rateOverTime = rate;
            var sh = ps.shape; sh.shapeType = ParticleSystemShapeType.Box; sh.scale = box;
            var vel = ps.velocityOverLifetime; vel.enabled = true; vel.space = ParticleSystemSimulationSpace.World;
            vel.x = new ParticleSystem.MinMaxCurve(velMin.x, velMax.x); vel.y = new ParticleSystem.MinMaxCurve(velMin.y, velMax.y); vel.z = new ParticleSystem.MinMaxCurve(velMin.z, velMax.z);
            if (noise > 0f) { var nz = ps.noise; nz.enabled = true; nz.strength = noise; nz.frequency = 0.35f; }
            var col = ps.colorOverLifetime; col.enabled = true;
            var g = new Gradient(); g.SetKeys(new[] { new GradientColorKey(Color.white, 0f), new GradientColorKey(Color.white, 1f) }, new[] { new GradientAlphaKey(0f, 0f), new GradientAlphaKey(1f, 0.15f), new GradientAlphaKey(1f, 0.7f), new GradientAlphaKey(0f, 1f) });
            col.color = new ParticleSystem.MinMaxGradient(g);
            var r = go.GetComponent<ParticleSystemRenderer>(); r.sharedMaterial = mat; r.shadowCastingMode = ShadowCastingMode.Off;
            return ps;
        }

        /// <summary>A column of smoke rising and leaning with the wind (a burning ruin, a camp fire, the launch pad).</summary>
        static ParticleSystem Smoke(Transform parent, Vector3 pos, float width, float height, Color c, float rate = 6f)
        {
            var ps = Ambient(parent, "Smoke", pos, new Vector3(width, 0.5f, width), rate, new Vector2(height / 3.2f, height / 2.4f), new Vector3(0.6f, 2.6f, -0.3f), new Vector3(1.6f, 3.6f, 0.3f), new Vector2(width * 1.2f, width * 2.4f), c, new Color(c.r * 0.8f, c.g * 0.8f, c.b * 0.8f, c.a), AlphaParticle(), 0.6f, 0f, 120);
            var sz = ps.sizeOverLifetime; sz.enabled = true; sz.size = new ParticleSystem.MinMaxCurve(1f, AnimationCurve.Linear(0f, 0.5f, 1f, 1.8f));
            return ps;
        }

        static ParticleSystem Fire(Transform parent, Vector3 pos, float width, Material add)
        {
            var ps = Ambient(parent, "Fire", pos, new Vector3(width, 0.2f, width), 30f * width, new Vector2(0.5f, 0.9f), new Vector3(-0.3f, 1.8f, -0.3f), new Vector3(0.3f, 3.2f, 0.3f), new Vector2(width * 0.5f, width * 0.9f), new Color(1f, 0.55f, 0.15f), new Color(1f, 0.85f, 0.35f), add, 0.4f, 0f, 150);
            var sz = ps.sizeOverLifetime; sz.enabled = true; sz.size = new ParticleSystem.MinMaxCurve(1f, AnimationCurve.Linear(0f, 1f, 1f, 0.2f));
            return ps;
        }

        static Light GLight(Transform parent, Vector3 pos, Color c, float range, float intensity, bool flicker = false)
        {
            var go = new GameObject("Light"); go.transform.SetParent(parent, false); go.transform.position = pos;
            var l = go.AddComponent<Light>(); l.type = LightType.Point; l.color = c; l.range = range; l.intensity = intensity; l.shadows = LightShadows.None;
            if (flicker) { var f = go.AddComponent<Flicker>(); f.target = l; f.baseIntensity = intensity; }
            return l;
        }

        // ------------------------------------------------------------------ the hall every gate is built round
        /// <summary>The hall the cast flies out of: thick walls and a roof in `outer`, lined inside with `inner`, a floor of shadow, a glowing back
        /// wall and a light near the back that catches the planes as they come.</summary>
        static void GateHall(GateKit G, Material outer, Material inner, Color glow, bool shell = true)
        {
            var p = G.root; float zc = GateZ + HallLen * 0.5f;
            if (shell)
            {
                GBox(p, "HallWallL", new Vector3(-(HallHW + 1f), GY((HallH + 2f) * 0.5f), zc), new Vector3(2f, HallH + 2f, HallLen), outer);
                GBox(p, "HallWallR", new Vector3(HallHW + 1f, GY((HallH + 2f) * 0.5f), zc), new Vector3(2f, HallH + 2f, HallLen), outer);
                GBox(p, "HallRoof", new Vector3(0f, GY(HallH + 1f), zc), new Vector3(HallHW * 2f + 4f, 2f, HallLen), outer);
            }
            GBox(p, "LinerL", new Vector3(-(HallHW + 0.03f), GY(HallH * 0.5f), zc + 0.3f), new Vector3(0.06f, HallH, HallLen - 0.6f), inner, default(Vector3), false);
            GBox(p, "LinerR", new Vector3(HallHW + 0.03f, GY(HallH * 0.5f), zc + 0.3f), new Vector3(0.06f, HallH, HallLen - 0.6f), inner, default(Vector3), false);
            GBox(p, "LinerTop", new Vector3(0f, GY(HallH - 0.03f), zc + 0.3f), new Vector3(HallHW * 2f, 0.06f, HallLen - 0.6f), inner, default(Vector3), false);
            GBox(p, "Floor", new Vector3(0f, GY(0.03f), zc + 0.8f), new Vector3(HallHW * 2f, 0.06f, HallLen - 0.4f), inner, default(Vector3), false);
            GBox(p, "Glow", new Vector3(0f, GY(HallH * 0.5f), GateZ + HallLen - 0.3f), new Vector3(HallHW * 2f, HallH, 0.2f), GGlow(G.id, "Glow", glow * 0.3f), default(Vector3), false);   // a dim light deep inside: the mouth reads dark, not as a lit screen
            var haze = GAdd(G.id, "Haze", new Color(Mathf.Min(1f, glow.r * 0.4f), Mathf.Min(1f, glow.g * 0.4f), Mathf.Min(1f, glow.b * 0.4f), 0.5f));
            for (int i = 0; i < 3; i++) GPrim(p, PrimitiveType.Quad, "Haze", new Vector3(0f, GY(HallH * 0.45f), GateZ + HallLen - 3f - i * 7f), new Vector3(HallHW * 2.4f, HallH * 1.1f, 1f), haze);   // glowing haze in the depth
            GLight(p, new Vector3(0f, GY(7f), GateZ + 6f), new Color(Mathf.Min(1f, glow.r), Mathf.Min(1f, glow.g), Mathf.Min(1f, glow.b)), 26f, 2.4f);
        }

        /// <summary>Pushes a placed piece out of the hall and its mouth if it reaches into them.</summary>
        static void KeepOutOfHall(GameObject go)
        {
            if (go == null) return;
            var b = WorldBounds(go);
            if (b.min.y > GY(HallH + 2f) || b.max.z < GateZ - 3f) return;
            if (b.max.x <= -(HallHW + 0.2f) || b.min.x >= HallHW + 0.2f) return;
            float side = b.center.x < 0f ? -1f : 1f;
            float shift = side < 0f ? -(HallHW + 0.2f) - b.max.x : (HallHW + 0.2f) - b.min.x;
            go.transform.position += new Vector3(shift, 0f, 0f);
        }

        static GameObject GPut(GateKit G, string name, float x, float z, float s, float yaw = 0f, float lift = 0f)
        {
            G.K.far = true; G.K.parent = G.root; var go = Put(G.K, name, x, z, s, yaw, lift); G.K.far = false; G.K.parent = null;
            return go;
        }

        /// <summary>The gate of a land world, by id. Returns how far either side of the lane its mass reaches (scenery closer than that grows at its foot).</summary>
        static float BuildGate(string id, Transform worldRoot, Mats M, LandKit K)
        {
            var root = new GameObject("Gate"); root.transform.SetParent(worldRoot, false);
            var G = new GateKit { root = root.transform, M = M, id = id, K = K };
            switch (id)
            {
                case "city": RuinsGate(G); break;
                case "desert": PyramidGate(G); break;
                case "soccer": StadiumGate(G); break;
                case "shuttle": HangarGate(G); break;
                case "west": MineGate(G); break;
                case "christmas": GiftGate(G); break;
                case "camping": CaveGate(G); break;
                case "autumn": LogGate(G); break;
                case "nature": HiveGate(G); break;
            }
            return G.clearX;
        }

        // ------------------------------------------------------------------ DOWNTOWN: a ruined city - the planes pour out between two collapsed towers
        static Texture2D RuinWindowTexture()
        {
            var rnd = new System.Random(5);
            var lit = new bool[8, 16]; var dark = new bool[8, 16];
            for (int i = 0; i < 8; i++) for (int j = 0; j < 16; j++) { double r = rnd.NextDouble(); lit[i, j] = r < 0.08; dark[i, j] = r > 0.55; }
            return GateTexture("GateRuinWindows", 128, 256, (x, y) =>
            {
                float n = VNoise(x / 9f, y / 9f, 41) * 0.12f, soot = Mathf.Clamp01(VNoise(x / 40f, y / 30f, 42) * 1.4f - 0.4f);
                Color wall = Color.Lerp(new Color(0.46f + n, 0.45f + n, 0.43f + n), new Color(0.12f, 0.11f, 0.1f), soot * 0.8f);
                int cx = x / 16, cy = y / 16; int lx = x % 16, ly = y % 16;
                if (lx >= 3 && lx <= 12 && ly >= 4 && ly <= 12)
                {
                    if (lit[cx, cy]) return Color.Lerp(new Color(1f, 0.55f, 0.15f), new Color(1f, 0.8f, 0.3f), ly / 12f);   // burning inside
                    return dark[cx, cy] ? new Color(0.03f, 0.03f, 0.04f) : new Color(0.12f + n, 0.15f + n, 0.18f + n);
                }
                return wall;
            });
        }

        /// <summary>A gutted tower: a body with burnt windows, a broken crown of floors of uneven height, beams sticking out, a slight lean.</summary>
        static GameObject RuinTower(Transform parent, string name, Vector3 basePos, Vector3 size, Material walls, Material concrete, Material steel, System.Random rnd, float lean)
        {
            var t = new GameObject(name); t.transform.SetParent(parent, false); t.transform.position = basePos;
            GBox(t.transform, "Body", basePos + Vector3.up * size.y * 0.5f, size, walls).transform.SetParent(t.transform, true);
            int chunks = 4 + rnd.Next(3);
            for (int i = 0; i < chunks; i++)
            {   // the broken crown: blocks of the upper floors, some gone, some taller
                float w = size.x / chunks, h = (float)rnd.NextDouble() * size.y * 0.22f;
                if (rnd.NextDouble() < 0.3) continue;
                var c = GBox(t.transform, "Crown" + i, basePos + new Vector3(-size.x * 0.5f + w * (i + 0.5f), size.y + h * 0.5f, ((float)rnd.NextDouble() - 0.5f) * size.z * 0.3f), new Vector3(w * 0.96f, h, size.z * (0.6f + (float)rnd.NextDouble() * 0.4f)), walls);
                c.transform.SetParent(t.transform, true);
            }
            for (int i = 0; i < 5; i++)
            {   // bare beams
                var b = GBox(t.transform, "Beam" + i, basePos + new Vector3(((float)rnd.NextDouble() - 0.5f) * size.x, size.y + (float)rnd.NextDouble() * 3f, ((float)rnd.NextDouble() - 0.5f) * size.z), new Vector3(0.35f, 2.5f + (float)rnd.NextDouble() * 4f, 0.35f), steel, new Vector3(((float)rnd.NextDouble() - 0.5f) * 50f, 0f, ((float)rnd.NextDouble() - 0.5f) * 50f));
                b.transform.SetParent(t.transform, true);
            }
            for (int i = 0; i < 7; i++)
            {   // rubble at its foot
                float s = 0.8f + (float)rnd.NextDouble() * 2.2f;
                var r = GBox(t.transform, "Rubble" + i, basePos + new Vector3(((float)rnd.NextDouble() - 0.5f) * (size.x + 4f), s * 0.3f, -size.z * 0.5f - (float)rnd.NextDouble() * 3f), new Vector3(s, s * 0.7f, s), concrete, new Vector3((float)rnd.NextDouble() * 40f, (float)rnd.NextDouble() * 360f, (float)rnd.NextDouble() * 40f), false);
                r.transform.SetParent(t.transform, true);
            }
            t.transform.rotation = Quaternion.Euler(0f, 0f, lean);   // the lean, about its foot
            return t;
        }

        static void RuinsGate(GateKit G)
        {
            G.clearX = 30f;
            var rnd = new System.Random(77);
            var tex = RuinWindowTexture();
            var wallsL = GTex(G.id, "RuinL", tex, new Vector2(1f, 2.5f), Color.white, 1.4f);
            var concrete = GLit(G.id, "Concrete", new Color(0.42f, 0.41f, 0.4f));
            var steel = GLit(G.id, "Steel", new Color(0.22f, 0.2f, 0.19f), 0.4f);
            var soot = GLit(G.id, "Soot", new Color(0.1f, 0.09f, 0.09f));
            GateHall(G, concrete, soot, new Color(3f, 1.2f, 0.35f));
            // the two towers either side of the street, leaning in over it; a slab of a third fallen across between them
            RuinTower(G.root, "TowerL", new Vector3(-(HallHW + 9f), GY(0f), GateZ + 10f), new Vector3(16f, 46f, 18f), wallsL, concrete, steel, rnd, -4f);
            RuinTower(G.root, "TowerR", new Vector3(HallHW + 9.5f, GY(0f), GateZ + 12f), new Vector3(17f, 38f, 20f), wallsL, concrete, steel, rnd, 5f);
            RuinTower(G.root, "TowerBackL", new Vector3(-30f, GY(0f), GateZ + 30f), new Vector3(14f, 56f, 14f), wallsL, concrete, steel, rnd, 2f);
            RuinTower(G.root, "TowerBackR", new Vector3(32f, GY(0f), GateZ + 26f), new Vector3(15f, 30f, 15f), wallsL, concrete, steel, rnd, -3f);
            GBox(G.root, "FallenSlab", new Vector3(0f, GY(HallH + 4f), GateZ + 2f), new Vector3(32f, 4.5f, 9f), wallsL, new Vector3(0f, 6f, -9f));
            GBox(G.root, "FallenSlab2", new Vector3(-2f, GY(HallH + 8f), GateZ + 6f), new Vector3(20f, 3.5f, 8f), concrete, new Vector3(10f, -14f, 12f));
            for (int i = 0; i < 6; i++)   // girders hanging off the slab
                GBox(G.root, "Girder" + i, new Vector3(-12f + i * 4.6f, GY(HallH + 1.5f), GateZ - 1.2f), new Vector3(0.4f, 3f + (i % 3), 0.4f), steel, new Vector3(0f, 0f, (i % 2 == 0 ? 1 : -1) * (8f + i * 3f)));
            // the burning: fire in the towers' broken floors, smoke columns, embers drifting
            var add = GAdd(G.id, "Fire", new Color(1f, 0.6f, 0.2f, 0.9f));
            foreach (var f in new[] { new Vector3(-(HallHW + 6f), GY(30f), GateZ + 2f), new Vector3(HallHW + 12f, GY(24f), GateZ + 3f), new Vector3(-30f, GY(42f), GateZ + 23f), new Vector3(2f, GY(HallH + 7f), GateZ + 1f) })
            {
                Fire(G.root, f, 2.2f, add); Smoke(G.root, f + Vector3.up * 2f, 3f, 40f, new Color(0.18f, 0.17f, 0.17f, 0.55f));
                GLight(G.root, f + new Vector3(0f, 1f, -3f), new Color(1f, 0.55f, 0.2f), 18f, 2.5f, true);
            }
            Ambient(G.root, "Embers", new Vector3(0f, GY(14f), GateZ - 20f), new Vector3(50f, 20f, 40f), 18f, new Vector2(3f, 6f), new Vector3(-0.6f, 0.4f, -1.5f), new Vector3(0.6f, 1.6f, 0.5f), new Vector2(0.1f, 0.22f), new Color(1f, 0.55f, 0.15f), new Color(1f, 0.8f, 0.3f), G.M.particle, 1f);
            // a searchlight from the far roof still sweeps the smoke
            var beamMat = GAdd(G.id, "Beam", new Color(0.9f, 0.95f, 1f, 0.12f));
            var beamMesh = ConeMesh("GateSearchBeam", 90f, 6f, 16);
            foreach (var b in new[] { new Vector3(-30f, GY(58f), GateZ + 30f), new Vector3(32f, GY(32f), GateZ + 26f) })
            {
                var pivot = new GameObject("Searchlight"); pivot.transform.SetParent(G.root, false); pivot.transform.position = b; pivot.transform.rotation = Quaternion.Euler(-30f, b.x < 0f ? 25f : -25f, 0f);
                var cone = MeshObj("Beam", beamMesh, pivot.transform, beamMat); cone.GetComponent<MeshRenderer>().shadowCastingMode = ShadowCastingMode.Off;
                var sw = pivot.AddComponent<Sweep>(); sw.phase = b.x; sw.yawAmplitude = 40f;
            }
        }

        // ------------------------------------------------------------------ DESERT: a step pyramid with a golden door that sinks into the sand
        static void PyramidGate(GateKit G)
        {
            G.clearX = 30f;
            var sand = GLit(G.id, "Sandstone", new Color(0.86f, 0.7f, 0.46f));
            var dark = GLit(G.id, "Inner", new Color(0.14f, 0.09f, 0.05f));
            var gold = GLit(G.id, "Gold", new Color(1f, 0.78f, 0.25f), 0.7f); gold.SetFloat("_Metallic", 0.8f);
            var glowGold = GGlow(G.id, "Sun", new Color(3f, 2.2f, 0.7f));
            GateHall(G, sand, dark, new Color(3f, 2.3f, 1.1f));
            var prof = new List<Vector2>(); float r = 50f, h = 0f;
            for (int i = 0; i < 7; i++) { prof.Add(new Vector2(r, h)); h += 5.6f; prof.Add(new Vector2(r, h)); r -= 6.3f; }
            prof.Add(new Vector2(r + 6.3f - 2f, h)); prof.Add(new Vector2(0f, h));
            var mesh = LatheMesh("GateStepPyramid", prof.ToArray(), 4, HallHW + 0.6f, HallH + 1.2f, 6f, 0.15f, 16);
            var pyr = MeshObj("StepPyramid", mesh, G.root, sand); pyr.transform.position = new Vector3(0f, GY(0f), GateZ + 3f + 50f * Mathf.Cos(Mathf.PI / 4f));
            // the temple's pylon round the door, the winged sun over it, the door itself (it sinks when the attempt starts)
            foreach (int s in new[] { -1, 1 })
            {
                GBox(G.root, "Pylon", new Vector3(s * (HallHW + 2.2f), GY(10f), GateZ - 0.6f), new Vector3(3.4f, 20f, 3f), sand);
                GBox(G.root, "PylonBand", new Vector3(s * (HallHW + 2.2f), GY(17.5f), GateZ - 2.2f), new Vector3(3.6f, 0.8f, 0.3f), gold);
                GBox(G.root, "Wing", new Vector3(s * 5.5f, GY(HallH + 3.2f), GateZ - 2.3f), new Vector3(7f, 1.4f, 0.3f), gold, new Vector3(0f, 0f, s * -8f));
                GBox(G.root, "Obelisk", new Vector3(s * (HallHW + 7f), GY(9f), GateZ - 6f), new Vector3(1.8f, 18f, 1.8f), sand);
                GBox(G.root, "ObeliskTip", new Vector3(s * (HallHW + 7f), GY(18.4f), GateZ - 6f), new Vector3(1.3f, 1.3f, 1.3f), gold, new Vector3(45f, 0f, 45f));
            }
            GBox(G.root, "Lintel", new Vector3(0f, GY(HallH + 1.4f), GateZ - 1f), new Vector3(HallHW * 2f + 8f, 2.8f, 3.6f), sand);
            var sun = GPrim(G.root, PrimitiveType.Cylinder, "SunDisk", new Vector3(0f, GY(HallH + 3.2f), GateZ - 2.6f), new Vector3(3f, 0.2f, 3f), glowGold, new Vector3(90f, 0f, 0f));
            var door = GBox(G.root, "Door", new Vector3(0f, GY(HallH * 0.5f), GateZ - 0.2f), new Vector3(HallHW * 2f, HallH, 0.6f), sand);
            GBox(door.transform, "DoorEye", new Vector3(0f, GY(HallH * 0.62f), GateZ - 0.55f), new Vector3(3f, 1.2f, 0.1f), gold).transform.SetParent(door.transform, true);
            var op = G.root.gameObject.AddComponent<GateOpener>(); op.parts = new[] { door.transform }; op.openOffset = new[] { new Vector3(0f, -(HallH + 0.4f), 0f) }; op.seconds = 1.8f;
            // a beam of sunlight from the summit; sand blowing across the dunes
            var beam = GAdd(G.id, "Beam", new Color(1f, 0.85f, 0.45f, 0.22f));
            for (int i = 0; i < 2; i++) { var q = GPrim(G.root, PrimitiveType.Quad, "SkyBeam", new Vector3(0f, GY(h + 60f), pyr.transform.position.z), new Vector3(4f, 120f, 1f), beam, new Vector3(0f, i * 90f, 0f)); }
            Ambient(G.root, "BlowingSand", new Vector3(-10f, GY(1.2f), 70f), new Vector3(30f, 2f, 160f), 40f, new Vector2(4f, 7f), new Vector3(5f, -0.1f, -1f), new Vector3(9f, 0.4f, 1f), new Vector2(0.8f, 2.2f), new Color(0.92f, 0.78f, 0.55f, 0.18f), new Color(0.85f, 0.7f, 0.48f, 0.12f), AlphaParticle(), 0.5f);
        }

        // ------------------------------------------------------------------ SOCCER FIELD: the stadium's main stand - the planes run out of the players' tunnel
        static void StadiumGate(GateKit G)
        {
            G.clearX = 46f;
            var crowdTex = GateTexture("GateCrowd", 128, 64, (x, y) =>
            {
                float h = Hash2(x / 2, y / 3, 61); if ((y / 3) % 2 == 1) return new Color(0.15f, 0.16f, 0.2f);
                return h < 0.3f ? new Color(0.9f, 0.15f, 0.15f) : h < 0.55f ? new Color(0.95f, 0.95f, 0.95f) : h < 0.75f ? new Color(0.15f, 0.35f, 0.9f) : h < 0.85f ? new Color(1f, 0.85f, 0.2f) : new Color(0.3f, 0.25f, 0.2f);
            });
            var crowd = GTex(G.id, "Crowd", crowdTex, new Vector2(10f, 1f), Color.white);
            var concrete = GLit(G.id, "Concrete", new Color(0.78f, 0.78f, 0.8f));
            var blue = GLit(G.id, "Team", new Color(0.15f, 0.3f, 0.85f), 0.3f);
            var dark = GLit(G.id, "Inner", new Color(0.06f, 0.06f, 0.08f));
            var white = GLit(G.id, "Roof", new Color(0.95f, 0.95f, 0.97f), 0.5f);
            GateHall(G, blue, dark, new Color(1.6f, 2.6f, 1.6f));
            for (int i = 0; i < 11; i++)
            {   // the tiers climb back from the touchline; the lower ones part for the tunnel
                float top = 2.3f * (i + 1), z0 = GateZ + 1f + 2.4f * i, z1 = GateZ + 30f, zc = (z0 + z1) * 0.5f, depth = z1 - z0;
                foreach (int s in new[] { -1, 1 }) GBox(G.root, "Tier" + i, new Vector3(s * (HallHW + 2f + 21f), GY(top * 0.5f), zc), new Vector3(42f, top, depth), crowd);
                if (top > HallH + 2.2f) GBox(G.root, "TierOver" + i, new Vector3(0f, GY((top + HallH + 2f) * 0.5f), zc), new Vector3(2f * (HallHW + 2f), top - (HallH + 2f), depth), crowd);   // over the tunnel, above its roof
            }
            foreach (int s in new[] { -1, 1 })
            {
                GBox(G.root, "TunnelFlank", new Vector3(s * (HallHW + 1.2f), GY(HallH * 0.5f + 1f), GateZ - 1.6f), new Vector3(2.4f, HallH + 2f, 3.2f), blue);
                for (int k = 0; k < 4; k++) GBox(G.root, "Pillar", new Vector3(s * (12f + k * 12f), GY(30f), GateZ + 22f), new Vector3(1f, 12f, 1f), white);
            }
            GBox(G.root, "TunnelHood", new Vector3(0f, GY(HallH + 1.6f), GateZ - 1.6f), new Vector3(HallHW * 2f + 4.8f, 3.2f, 3.2f), blue);
            GBox(G.root, "Canopy", new Vector3(0f, GY(36.5f), GateZ + 22f), new Vector3(104f, 1f, 22f), white, new Vector3(-6f, 0f, 0f));
            // the giant screen on the roof: the match score (planes shot down : planes lost) and the clock
            var screen = GBox(G.root, "Screen", new Vector3(0f, GY(44f), GateZ + 14f), new Vector3(30f, 11f, 1.2f), GLit(G.id, "Screen", new Color(0.03f, 0.04f, 0.06f), 0.8f));
            GBox(G.root, "ScreenPost", new Vector3(0f, GY(39f), GateZ + 15f), new Vector3(2f, 6f, 1f), white);
            var sb = screen.AddComponent<Scoreboard>();
            sb.score = Label3D("Score", G.root, new Vector3(0f, GY(45.2f), GateZ + 13.2f), 60f, new Color(1f, 0.9f, 0.3f), fontOutline); sb.score.text = "0 : 0"; sb.score.rectTransform.sizeDelta = new Vector2(28f, 7f);
            sb.clock = Label3D("Clock", G.root, new Vector3(0f, GY(40.6f), GateZ + 13.2f), 24f, Color.white, fontOutline); sb.clock.text = "00:00"; sb.clock.rectTransform.sizeDelta = new Vector2(20f, 3f);
            Label3D("Home", G.root, new Vector3(-10.5f, GY(48.5f), GateZ + 13.2f), 16f, new Color(0.5f, 0.75f, 1f), fontOutline).text = "SQUAD";
            Label3D("Away", G.root, new Vector3(10.5f, GY(48.5f), GateZ + 13.2f), 16f, new Color(1f, 0.45f, 0.4f), fontOutline).text = "ENEMY";
            // camera flashes all over the stand; confetti thrown every few seconds
            Ambient(G.root, "Flashes", new Vector3(0f, GY(14f), GateZ + 14f), new Vector3(100f, 22f, 26f), 30f, new Vector2(0.06f, 0.14f), Vector3.zero, Vector3.zero, new Vector2(0.6f, 1.1f), Color.white, new Color(1f, 1f, 0.85f), G.M.particle, 0f, 0f, 60, false);
            var conf = Ambient(G.root, "Confetti", new Vector3(0f, GY(26f), GateZ + 6f), new Vector3(90f, 2f, 10f), 0f, new Vector2(4f, 6f), new Vector3(-1.5f, 2f, -4f), new Vector3(1.5f, 6f, -1f), new Vector2(0.25f, 0.45f), new Color(1f, 0.3f, 0.3f), new Color(0.3f, 0.6f, 1f), G.M.particle, 1.2f, 0.25f, 400, false);
            var em = conf.emission; em.SetBursts(new[] { new ParticleSystem.Burst(0f, (short)120, (short)160, 0, 9f) });
            var colr = conf.main; colr.startColor = new ParticleSystem.MinMaxGradient(new Gradient { colorKeys = new[] { new GradientColorKey(new Color(1f, 0.25f, 0.25f), 0f), new GradientColorKey(new Color(1f, 0.9f, 0.2f), 0.33f), new GradientColorKey(new Color(0.3f, 1f, 0.4f), 0.66f), new GradientColorKey(new Color(0.3f, 0.55f, 1f), 1f) } }) { mode = ParticleSystemGradientMode.RandomColor };
        }

        // ------------------------------------------------------------------ SPACE LAUNCH: the assembly hangar - its tall doors slide up and the planes roll out
        static void HangarGate(GateKit G)
        {
            G.clearX = 38f;
            var panelTex = GateTexture("GatePanels", 128, 128, (x, y) =>
            {
                float n = VNoise(x / 12f, y / 12f, 71) * 0.05f;
                bool seam = x % 32 == 0 || x % 32 == 1 || y % 64 == 0;
                return seam ? new Color(0.6f, 0.62f, 0.66f) : new Color(0.86f + n, 0.87f + n, 0.89f + n);
            });
            var wall = GTex(G.id, "Panels", panelTex, new Vector2(4f, 6f), Color.white);
            var dark = GLit(G.id, "Inner", new Color(0.06f, 0.06f, 0.07f));
            var door = GLit(G.id, "Door", new Color(0.55f, 0.57f, 0.6f), 0.4f);
            var orange = GLit(G.id, "Stripe", new Color(1f, 0.45f, 0.1f));
            var hazard = GTex(G.id, "Hazard", GateTexture("GateHazard", 64, 16, (x, y) => ((x + y) / 8) % 2 == 0 ? new Color(0.95f, 0.75f, 0.1f) : new Color(0.08f, 0.08f, 0.08f)), new Vector2(8f, 1f), Color.white);
            GateHall(G, wall, dark, new Color(2.6f, 1.7f, 0.8f), false);
            float w = 34f, hgt = 60f, d = 40f, zc = GateZ + d * 0.5f;
            foreach (int s in new[] { -1, 1 }) GBox(G.root, "Block", new Vector3(s * (HallHW + (w - HallHW) * 0.5f), GY(hgt * 0.5f), zc), new Vector3(w - HallHW, hgt, d), wall);
            GBox(G.root, "Over", new Vector3(0f, GY(HallH + (hgt - HallH) * 0.5f), zc), new Vector3(HallHW * 2f, hgt - HallH, d), wall);
            GBox(G.root, "DoorRecess", new Vector3(0f, GY(HallH + 15f), GateZ - 0.1f), new Vector3(HallHW * 2f + 2f, 30f, 0.3f), door);
            for (int i = 0; i < 6; i++) GBox(G.root, "DoorLine", new Vector3(0f, GY(HallH + 2.5f + i * 5f), GateZ - 0.3f), new Vector3(HallHW * 2f + 2f, 0.25f, 0.2f), dark);
            GBox(G.root, "Hazard", new Vector3(0f, GY(HallH + 0.6f), GateZ - 0.35f), new Vector3(HallHW * 2f + 2f, 1.2f, 0.2f), hazard);
            GBox(G.root, "StripeL", new Vector3(-(HallHW + 9f), GY(hgt * 0.5f), GateZ - 0.15f), new Vector3(5f, hgt, 0.2f), orange);
            var bay = Label3D("Bay", G.root, new Vector3(HallHW + 13f, GY(48f), GateZ - 0.4f), 70f, new Color(0.25f, 0.3f, 0.42f), fontOutline); bay.text = "BAY 39"; bay.rectTransform.sizeDelta = new Vector2(24f, 8f);
            // the doors: two halves that slide up into the recess as the attempt starts
            var lower = GBox(G.root, "DoorLower", new Vector3(0f, GY(HallH * 0.25f), GateZ - 0.6f), new Vector3(HallHW * 2f, HallH * 0.5f, 0.5f), door);
            var upper = GBox(G.root, "DoorUpper", new Vector3(0f, GY(HallH * 0.75f), GateZ - 0.9f), new Vector3(HallHW * 2f, HallH * 0.5f, 0.5f), door);
            var op = G.root.gameObject.AddComponent<GateOpener>(); op.parts = new[] { lower.transform, upper.transform }; op.openOffset = new[] { new Vector3(0f, HallH + 1f, 0f), new Vector3(0f, HallH * 0.5f + 1f, 0f) }; op.seconds = 2.2f;
            // red beacons blinking on the roof corners
            var red = GGlow(G.id, "Beacon", new Color(4f, 0.3f, 0.2f));
            int b = 0;
            foreach (int s in new[] { -1, 1 })
                foreach (float bz in new[] { GateZ + 1f, GateZ + d - 1f })
                {
                    var lamp = GBox(G.root, "Beacon", new Vector3(s * (w - 1f), GY(hgt + 0.6f), bz), new Vector3(1.2f, 1.2f, 1.2f), red, default(Vector3), false);
                    var holder = new GameObject("BeaconBlink"); holder.transform.SetParent(G.root, false);
                    var bl = holder.AddComponent<Blink>(); bl.lamps = new[] { lamp }; bl.seconds = new[] { 0.35f }; bl.darkSeconds = 1.1f; bl.phase = b++ * 0.37f;
                }
        }

        // ------------------------------------------------------------------ WILD WEST: a mine driven into a red mesa, lanterns at its timbered mouth
        static void MineGate(GateKit G)
        {
            G.clearX = 34f;
            var rock = GLit(G.id, "Rock", new Color(0.62f, 0.38f, 0.22f));
            var dark = GLit(G.id, "Inner", new Color(0.09f, 0.05f, 0.03f));
            var timber = GLit(G.id, "Timber", new Color(0.38f, 0.24f, 0.13f));
            var iron = GLit(G.id, "Iron", new Color(0.25f, 0.24f, 0.24f), 0.5f);
            GateHall(G, rock, dark, new Color(2.6f, 1.3f, 0.4f));
            var rocks = new List<GameObject>();
            void R(string n, float x, float z, float s, float yaw, float lift) { var g = GPut(G, n, x, z, s, yaw, lift); KeepOutOfHall(g); if (g != null) rocks.Add(g); }
            R("stone large brown", -22f, GateZ + 6f, 4.2f, 10f, 0f); R("stone large brown 2", 22f, GateZ + 8f, 4.4f, 190f, 0f);
            R("stone large brown", -14f, GateZ + 20f, 4.8f, 80f, 0f); R("stone large brown 2", 15f, GateZ + 22f, 4.8f, 250f, 0f);
            R("stone large brown 2", 0f, GateZ + 12f, 4.6f, 30f, HallH + 2f); R("stone large brown", -26f, GateZ + 24f, 5.5f, 140f, 8f); R("stone large brown", 28f, GateZ + 26f, 5.5f, 300f, 7f);
            R("stone large brown 2", 0f, GateZ + 30f, 6.5f, 200f, 14f); R("stone large brown", -44f, GateZ + 36f, 6f, 60f, 0f); R("stone large brown 2", 46f, GateZ + 38f, 6f, 120f, 0f);
            // the timbered portal, braces, a sign, two lanterns
            foreach (int s in new[] { -1, 1 })
            {
                GBox(G.root, "Post", new Vector3(s * (HallHW + 0.7f), GY(HallH * 0.5f + 0.5f), GateZ - 0.8f), new Vector3(1.4f, HallH + 1f, 1.4f), timber);
                GBox(G.root, "Brace", new Vector3(s * (HallHW - 1.6f), GY(HallH - 1.6f), GateZ - 0.8f), new Vector3(0.6f, 4.5f, 0.6f), timber, new Vector3(0f, 0f, s * 45f));
                var lanternPos = new Vector3(s * (HallHW + 2.4f), GY(HallH - 2.5f), GateZ - 1.6f);
                GBox(G.root, "Lantern", lanternPos, new Vector3(0.7f, 1f, 0.7f), GGlow(G.id, "Lantern", new Color(3f, 1.6f, 0.5f)), default(Vector3), false);
                GLight(G.root, lanternPos + Vector3.back, new Color(1f, 0.65f, 0.3f), 14f, 2.2f, true);
            }
            GBox(G.root, "Lintel", new Vector3(0f, GY(HallH + 1f), GateZ - 0.8f), new Vector3(HallHW * 2f + 3.4f, 1.6f, 1.6f), timber);
            GBox(G.root, "Sign", new Vector3(0f, GY(HallH + 3.2f), GateZ - 1f), new Vector3(10f, 2.4f, 0.3f), timber);
            Label3D("SignText", G.root, new Vector3(0f, GY(HallH + 3.2f), GateZ - 1.25f), 22f, new Color(1f, 0.9f, 0.6f), fontOutline).text = "GOLD MINE";
            // the mine track runs out of the mouth down the street
            foreach (int s in new[] { -1, 1 }) GBox(G.root, "Rail", new Vector3(s * 1.1f, GY(0.1f), GateZ + 5f - 90f), new Vector3(0.18f, 0.18f, 190f), iron, default(Vector3), false);
        }

        // ------------------------------------------------------------------ CHRISTMAS VILLAGE: a giant gift - its front flap drops open, its lid floats on golden light
        static void GiftGate(GateKit G)
        {
            G.clearX = 30f;
            var red = GLit(G.id, "Paper", new Color(0.82f, 0.08f, 0.1f), 0.45f);
            var gold = GLit(G.id, "Ribbon", new Color(1f, 0.8f, 0.25f), 0.7f); gold.SetFloat("_Metallic", 0.6f);
            var dark = GLit(G.id, "Inner", new Color(0.12f, 0.03f, 0.03f));
            var glow = GGlow(G.id, "Light", new Color(3f, 2.3f, 1f));
            GateHall(G, red, dark, new Color(3f, 2.2f, 0.9f), false);
            float W = 25f, H = 30f, D = 42f, T = 1.5f, zc = GateZ + D * 0.5f;
            foreach (int s in new[] { -1, 1 })
            {
                GBox(G.root, "Side", new Vector3(s * (W - T * 0.5f), GY(H * 0.5f), zc), new Vector3(T, H, D), red);
                GBox(G.root, "Front", new Vector3(s * (HallHW + (W - HallHW) * 0.5f), GY(H * 0.5f), GateZ + T * 0.5f), new Vector3(W - HallHW, H, T), red);
                GBox(G.root, "RibbonV", new Vector3(s * (HallHW + 0.8f), GY(H * 0.5f), GateZ - 0.05f), new Vector3(1.6f, H, 0.3f), gold);
                GBox(G.root, "RibbonSide", new Vector3(s * (W + 0.05f), GY(H * 0.5f), zc), new Vector3(0.3f, H, 3f), gold);
            }
            GBox(G.root, "Back", new Vector3(0f, GY(H * 0.5f), GateZ + D - T * 0.5f), new Vector3(2f * W, H, T), red);
            GBox(G.root, "FrontTop", new Vector3(0f, GY(HallH + (H - HallH) * 0.5f), GateZ + T * 0.5f), new Vector3(HallHW * 2f, H - HallH, T), red);
            GBox(G.root, "RibbonH", new Vector3(0f, GY(HallH + 1f), GateZ - 0.05f), new Vector3(2f * W, 1.6f, 0.3f), gold);
            GBox(G.root, "InnerLight", new Vector3(0f, GY(H - 0.6f), zc), new Vector3(2f * W - 3f, 0.4f, D - 3f), glow, default(Vector3), false);
            // the lid floats on the light that pours out under it
            var lid = new GameObject("Lid"); lid.transform.SetParent(G.root, false); lid.transform.position = new Vector3(0f, GY(H + 3.5f), zc);
            GBox(lid.transform, "LidTop", lid.transform.position, new Vector3(2f * W + 2f, 3f, D + 2f), red).transform.SetParent(lid.transform, true);
            GBox(lid.transform, "LidRibbonX", lid.transform.position + Vector3.up * 0.05f, new Vector3(2f * W + 2.2f, 3.1f, 3f), gold).transform.SetParent(lid.transform, true);
            GBox(lid.transform, "LidRibbonZ", lid.transform.position + Vector3.up * 0.05f, new Vector3(3f, 3.1f, D + 2.2f), gold).transform.SetParent(lid.transform, true);
            foreach (int s in new[] { -1, 1 }) GBox(lid.transform, "Bow", lid.transform.position + new Vector3(s * 4.5f, 4f, 0f), new Vector3(8f, 5f, 2.4f), gold, new Vector3(0f, s * 20f, s * 28f)).transform.SetParent(lid.transform, true);
            GBox(lid.transform, "Knot", lid.transform.position + Vector3.up * 2.6f, new Vector3(3f, 3f, 3f), gold, new Vector3(0f, 45f, 0f)).transform.SetParent(lid.transform, true);
            var hv = lid.AddComponent<Hover>(); hv.height = 0.8f; hv.speed = 0.25f; hv.sway = 1.2f;
            var beam = GAdd(G.id, "Rays", new Color(1f, 0.85f, 0.45f, 0.2f));
            for (int i = 0; i < 5; i++) GPrim(G.root, PrimitiveType.Quad, "Ray", new Vector3(-20f + i * 10f, GY(H + 9f), GateZ + 4f), new Vector3(3f, 14f, 1f), beam, new Vector3(0f, 0f, (i - 2) * 12f));
            // the front flap: a panel of the box hinged at its foot, standing shut in the lobby, dropping flat toward the squad as the attempt starts
            var hinge = new GameObject("FlapHinge"); hinge.transform.SetParent(G.root, false); hinge.transform.position = new Vector3(0f, GY(0f), GateZ - 0.2f);
            var flap = GBox(hinge.transform, "Flap", new Vector3(0f, GY(HallH * 0.5f), GateZ - 0.2f), new Vector3(HallHW * 2f, HallH, 0.8f), red);
            flap.transform.SetParent(hinge.transform, true);
            GBox(flap.transform, "FlapRibbon", new Vector3(0f, GY(HallH * 0.5f), GateZ - 0.65f), new Vector3(1.8f, HallH, 0.1f), gold).transform.SetParent(flap.transform, true);
            var op = G.root.gameObject.AddComponent<GateOpener>(); op.parts = new[] { hinge.transform }; op.openEuler = new[] { new Vector3(-90f, 0f, 0f) }; op.seconds = 1.4f;
            // two giant candy canes, and snow falling over everything
            var white = GLit(G.id, "CaneWhite", new Color(0.97f, 0.97f, 0.97f), 0.6f);
            foreach (int s in new[] { -1, 1 })
            {
                for (int k = 0; k < 12; k++) GPrim(G.root, PrimitiveType.Cylinder, "Cane", new Vector3(s * (W + 4f), GY(0.75f + k * 1.5f), GateZ - 3f), new Vector3(1.6f, 0.75f, 1.6f), k % 2 == 0 ? red : white);
                for (int k = 0; k < 6; k++) { float a = k / 5f * Mathf.PI; GPrim(G.root, PrimitiveType.Cylinder, "CaneHook", new Vector3(s * (W + 4f) - s * (1.6f - Mathf.Cos(a) * 1.6f), GY(18f + Mathf.Sin(a) * 1.6f), GateZ - 3f), new Vector3(1.6f, 0.75f, 1.6f), k % 2 == 0 ? white : red, new Vector3(0f, 0f, s * (90f - k * 36f))); }
            }
            Ambient(G.root, "Snow", new Vector3(0f, GY(28f), 70f), new Vector3(90f, 2f, 160f), 140f, new Vector2(10f, 14f), new Vector3(-0.5f, -2.6f, -0.6f), new Vector3(0.5f, -1.6f, 0.2f), new Vector2(0.14f, 0.3f), Color.white, new Color(0.9f, 0.95f, 1f), G.M.particle, 0.5f, 0f, 1500);
        }

        // ------------------------------------------------------------------ CAMPING FOREST: a cave in the mountain, torches at its mouth, bats pouring out of the dark
        static void CaveGate(GateKit G)
        {
            G.clearX = 34f;
            var rock = GLit(G.id, "Rock", new Color(0.32f, 0.35f, 0.42f));
            var dark = GLit(G.id, "Inner", new Color(0.04f, 0.04f, 0.06f));
            var wood = GLit(G.id, "Wood", new Color(0.3f, 0.2f, 0.12f));
            GateHall(G, rock, dark, new Color(1.2f, 0.5f, 2.6f));
            void R(string n, float x, float z, float s, float yaw, float lift) { KeepOutOfHall(GPut(G, n, x, z, s, yaw, lift)); }
            R("stone large gray blue 5", -20f, GateZ + 6f, 2.0f, 10f, 0f); R("stone large gray blue 6", 21f, GateZ + 8f, 2.0f, 200f, 0f);
            R("stone large gray blue 4", 0f, GateZ + 10f, 1.9f, 40f, HallH + 2f); R("stone large gray blue 5", -16f, GateZ + 24f, 2.6f, 90f, 6f); R("stone large gray blue 6", 17f, GateZ + 26f, 2.6f, 260f, 6f);
            R("stone large gray blue 4", 0f, GateZ + 30f, 3.2f, 150f, 14f); R("stone large gray blue 5", -40f, GateZ + 30f, 2.8f, 60f, 0f); R("stone large gray blue 6", 42f, GateZ + 32f, 2.8f, 120f, 0f);
            G.K.far = true; G.K.parent = G.root; Scatter(G.K, new[] { "fir tree large", "fir tree medium", "pine tree large" }, GateZ - 6f, GateZ + 30f, 5f, 26f, 48f, 1.6f, 2.2f, 1); G.K.far = false; G.K.parent = null;
            // torches either side of the mouth
            var add = GAdd(G.id, "Flame", new Color(1f, 0.6f, 0.2f, 0.9f));
            foreach (int s in new[] { -1, 1 })
            {
                var basePos = new Vector3(s * (HallHW + 3f), GY(0f), GateZ - 3f);
                GBox(G.root, "TorchPole", basePos + Vector3.up * 3f, new Vector3(0.45f, 6f, 0.45f), wood);
                GBox(G.root, "TorchBowl", basePos + Vector3.up * 6.2f, new Vector3(1.2f, 0.6f, 1.2f), GLit(G.id, "Iron", new Color(0.2f, 0.2f, 0.22f)));
                Fire(G.root, basePos + Vector3.up * 6.6f, 0.9f, add);
                GLight(G.root, basePos + new Vector3(0f, 7.5f, -1f), new Color(1f, 0.6f, 0.25f), 16f, 3f, true);
            }
            // bats burst out of the cave every few seconds and scatter over the camp
            var bats = Ambient(G.root, "Bats", new Vector3(0f, GY(9f), GateZ + 4f), new Vector3(10f, 6f, 2f), 0f, new Vector2(4f, 6f), new Vector3(-5f, 0.5f, -14f), new Vector3(5f, 3.5f, -9f), new Vector2(0.45f, 0.8f), new Color(0.05f, 0.04f, 0.06f, 1f), new Color(0.1f, 0.08f, 0.1f, 1f), AlphaParticle(), 2.5f, 0f, 200, false);
            var em = bats.emission; em.SetBursts(new[] { new ParticleSystem.Burst(1f, (short)20, (short)30, 0, 7f) });
            Ambient(G.root, "Fireflies", new Vector3(0f, GY(1.5f), 60f), new Vector3(36f, 4f, 140f), 25f, new Vector2(4f, 7f), new Vector3(-0.3f, -0.1f, -0.3f), new Vector3(0.3f, 0.3f, 0.3f), new Vector2(0.12f, 0.22f), new Color(0.8f, 1f, 0.4f), new Color(1f, 0.95f, 0.5f), G.M.particle, 1f, 0f, 400);
        }

        // ------------------------------------------------------------------ AUTUMN FOREST: a giant hollow log fallen across the way - the planes fly out of the trunk
        static void LogGate(GateKit G)
        {
            G.clearX = 22f;
            var bark = GTex(G.id, "Bark", GateTexture("GateBark", 64, 128, (x, y) =>
            {
                float s = Mathf.Abs(Mathf.Sin((x + VNoise(x / 6f, y / 20f, 81) * 12f) / 64f * Mathf.PI * 10f));
                return Color.Lerp(new Color(0.18f, 0.11f, 0.06f), new Color(0.42f, 0.27f, 0.15f), s);
            }), new Vector2(1f, 1f), Color.white);
            var wood = GLit(G.id, "Hollow", new Color(0.16f, 0.09f, 0.04f));
            var rings = GTex(G.id, "Rings", GateTexture("GateRings", 256, 256, (x, y) =>
            {
                float dx = x / 256f - 0.5f, dy = y / 256f - 0.5f, r = Mathf.Sqrt(dx * dx + dy * dy) * 2f;
                float ring = 0.5f + 0.5f * Mathf.Sin((r + VNoise(x / 30f, y / 30f, 82) * 0.04f) * 90f);
                return Color.Lerp(new Color(0.62f, 0.42f, 0.22f), new Color(0.82f, 0.62f, 0.36f), ring) * (r > 0.92f ? 0.5f : 1f);
            }), Vector2.one, Color.white);
            float rOut = 14f, rIn = 10.6f, cy = GY(9.4f), len = HallLen + 8f;
            var tube = MeshObj("Log", TubeMesh("GateLog", rOut, rIn, len, 30), G.root, bark, wood, rings);
            tube.transform.position = new Vector3(0f, cy, GateZ);
            GPrim(G.root, PrimitiveType.Quad, "Glow", new Vector3(0f, cy - 2f, GateZ + len - 1f), new Vector3(2f * rIn, 2f * rIn, 1f), GGlow(G.id, "Glow", new Color(0.8f, 0.4f, 0.1f)));
            GLight(G.root, new Vector3(0f, GY(7f), GateZ + 6f), new Color(1f, 0.65f, 0.3f), 26f, 2.4f);
            // moss, shelf fungi, mushrooms, a sapling on the trunk; broken branches
            var moss = GLit(G.id, "Moss", new Color(0.3f, 0.45f, 0.15f));
            var fungus = GLit(G.id, "Fungus", new Color(0.85f, 0.6f, 0.3f));
            for (int i = 0; i < 6; i++) GBox(G.root, "Moss", new Vector3(-8f + i * 3.2f, cy + rOut - 0.2f - Mathf.Abs(i - 2.5f) * 0.4f, GateZ + 4f + i * 4f), new Vector3(4f, 0.8f, 5f), moss, new Vector3(0f, i * 23f, (i - 2.5f) * 8f));
            foreach (int s in new[] { -1, 1 })
            {
                for (int k = 0; k < 3; k++) GPrim(G.root, PrimitiveType.Cylinder, "Shelf", new Vector3(s * (rOut - 0.4f), cy - 2f + k * 2.2f, GateZ + 6f + k * 5f), new Vector3(3f, 0.25f, 2f), fungus, new Vector3(0f, 0f, s * -12f));
                GPrim(G.root, PrimitiveType.Cylinder, "Branch", new Vector3(s * (rOut + 2.5f), cy + 5f, GateZ + 18f), new Vector3(1.6f, 4f, 1.6f), bark, new Vector3(0f, 0f, s * -60f));
            }
            GPut(G, "autumn tree 3", -4f, GateZ + 14f, 1.4f, 30f, rOut + 9.4f - 0.8f);
            GPut(G, "mushroom brown 2", 7f, GateZ + 8f, 6f, 0f, rOut + 9.4f - 1.6f);
            GPut(G, "mushroom brown", 9.5f, GateZ + 10f, 5f, 40f, rOut + 9.4f - 2.6f);
            G.K.far = true; G.K.parent = G.root; Scatter(G.K, new[] { "autumn tree 4", "autumn tree 5", "pine tree large", "autumn pine tree medium" }, GateZ - 4f, GateZ + 40f, 5f, 18f, 46f, 1.8f, 2.4f, 2); G.K.far = false; G.K.parent = null;
            // leaves falling everywhere, turning as they go
            var leaves = Ambient(G.root, "Leaves", new Vector3(0f, GY(22f), 70f), new Vector3(70f, 4f, 160f), 50f, new Vector2(9f, 13f), new Vector3(-0.8f, -2f, -1f), new Vector3(1.2f, -1.2f, 0.5f), new Vector2(0.3f, 0.5f), new Color(0.95f, 0.45f, 0.1f), new Color(1f, 0.8f, 0.2f), AlphaParticle(), 1.2f, 0f, 900);
            var rot = leaves.rotationOverLifetime; rot.enabled = true; rot.z = new ParticleSystem.MinMaxCurve(-2f, 2f);
        }

        // ------------------------------------------------------------------ SUNNY MEADOW: a giant straw beehive - the squad's enemies swarm out of it like wasps
        static void HiveGate(GateKit G)
        {
            G.clearX = 30f;
            var straw = GTex(G.id, "Straw", GateTexture("GateStraw", 64, 64, (x, y) =>
            {
                float n = VNoise(x / 3f, y / 14f, 91);
                return Color.Lerp(new Color(0.72f, 0.52f, 0.2f), new Color(0.95f, 0.78f, 0.38f), n);
            }), new Vector2(10f, 1f), Color.white);
            var dark = GLit(G.id, "Inner", new Color(0.14f, 0.08f, 0.02f));
            var wood = GLit(G.id, "Board", new Color(0.5f, 0.33f, 0.16f));
            GateHall(G, straw, dark, new Color(3f, 1.8f, 0.35f), false);
            float[] R = { 25f, 25.2f, 24.2f, 22.4f, 19.8f, 16.4f, 12.2f, 7.2f };
            var prof = new List<Vector2>(); float ring = 5.4f;
            for (int i = 0; i < R.Length; i++)
            {
                float next = i + 1 < R.Length ? R[i + 1] : 2f;
                prof.Add(new Vector2(R[i], i * ring)); prof.Add(new Vector2(Mathf.Max(R[i], next) + 1.1f, i * ring + ring * 0.5f));
            }
            prof.Add(new Vector2(2f, R.Length * ring)); prof.Add(new Vector2(0f, R.Length * ring + 1f));
            var hive = MeshObj("Hive", LatheMesh("GateHive", prof.ToArray(), 28, HallHW + 0.4f, HallH + 0.8f, 14f, 1f / ring), G.root, straw);
            hive.transform.position = new Vector3(0f, GY(0f), GateZ + 25f);
            GBox(G.root, "LandingBoard", new Vector3(0f, GY(0.25f), GateZ - 2.5f), new Vector3(HallHW * 2f + 6f, 0.5f, 6f), wood);
            foreach (int s in new[] { -1, 1 }) GBox(G.root, "Frame", new Vector3(s * (HallHW + 0.6f), GY(HallH * 0.5f), GateZ - 0.4f), new Vector3(1.2f, HallH, 2f), wood);
            GBox(G.root, "FrameTop", new Vector3(0f, GY(HallH + 0.5f), GateZ - 0.4f), new Vector3(HallHW * 2f + 2.4f, 1.2f, 2f), wood);
            var honey = GGlow(G.id, "Honey", new Color(2.4f, 1.4f, 0.2f));
            for (int i = 0; i < 5; i++) GPrim(G.root, PrimitiveType.Sphere, "HoneyDrip", new Vector3(-6f + i * 3f, GY(HallH - 0.6f - (i % 2) * 0.6f), GateZ - 1.2f), new Vector3(0.7f, 1.1f, 0.7f), honey);
            // bees round the hive, butterflies along the meadow
            Ambient(G.root, "Bees", new Vector3(0f, GY(16f), GateZ + 2f), new Vector3(54f, 30f, 16f), 40f, new Vector2(4f, 7f), new Vector3(-1f, -0.5f, -1f), new Vector3(1f, 0.5f, 1f), new Vector2(0.25f, 0.4f), new Color(1f, 0.85f, 0.1f), new Color(0.3f, 0.2f, 0.05f), G.M.particle, 3f, 0f, 400);
            Ambient(G.root, "Butterflies", new Vector3(0f, GY(1.8f), 60f), new Vector3(30f, 3f, 140f), 10f, new Vector2(6f, 10f), new Vector3(-0.6f, -0.2f, -0.6f), new Vector3(0.6f, 0.4f, 0.6f), new Vector2(0.35f, 0.5f), new Color(1f, 0.5f, 0.8f), new Color(0.5f, 0.8f, 1f), G.M.particle, 1.5f, 0f, 200);
        }
    }

    static class GateMaterialExt
    {
        public static Material Also(this Material m, System.Action<Material> f) { f(m); return m; }
    }
}
