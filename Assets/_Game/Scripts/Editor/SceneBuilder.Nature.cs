// SceneBuilder.Nature.cs (Editor only)
// World 4: the sunny meadow (2026-10-02: "also do Low-Poly Simple Nature Pack, and just 5 bosses, not all"). A short world: one stage of five
// bosses (WorldEntry.lastBoss = 5) over a green meadow with trees, bushes, flowers, boulders and mushrooms from the pack, under the AllSky
// "Cartoon Base BlueSky" with the sea world's cloud bank. The pack ships Built-in Standard materials: every piece is given the URP copy of its
// palette material (UrpCopy). The cast: wasp-yellow fighters, boulder crates on a turf pad, two repainted ships and three giants of the wood.
using System;
using System.Collections.Generic;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

namespace SkySquad.EditorTools
{
    public static partial class SceneBuilder
    {
        const string NatDir = "Assets/SimpleNaturePack/";

        static GameObject NaturePrefab(string rel) { var p = AssetDatabase.LoadAssetAtPath<GameObject>(NatDir + "Prefabs/" + rel + ".prefab"); if (p == null) Debug.LogWarning("[SkySquad] nature prefab missing: " + rel); return p; }
        static bool HaveNature() { return AssetDatabase.LoadAssetAtPath<GameObject>(NatDir + "Prefabs/Tree_01.prefab") != null; }

        class NatureMats { public Material prop, grass, sky; public VolumeProfile post; }
        static NatureMats NM;

        static Texture2D NatureGrassTexture()
        {
            int s = 256; var t = new Texture2D(s, s, TextureFormat.RGB24, false);
            var rnd = new System.Random(77);
            float[,] g = new float[16, 16]; for (int x = 0; x < 16; x++) for (int y = 0; y < 16; y++) g[x, y] = (float)rnd.NextDouble();
            float Noise(float fx, float fy) { int x0 = Mathf.FloorToInt(fx), y0 = Mathf.FloorToInt(fy); float tx = fx - x0, ty = fy - y0; tx = tx * tx * (3f - 2f * tx); ty = ty * ty * (3f - 2f * ty); int xa = ((x0 % 16) + 16) % 16, xb = (xa + 1) % 16, ya = ((y0 % 16) + 16) % 16, yb = (ya + 1) % 16; return Mathf.Lerp(Mathf.Lerp(g[xa, ya], g[xb, ya], tx), Mathf.Lerp(g[xa, yb], g[xb, yb], tx), ty); }
            Color a = new Color(0.26f, 0.55f, 0.16f), b = new Color(0.47f, 0.80f, 0.28f), c = new Color(0.15f, 0.38f, 0.11f);
            for (int y = 0; y < s; y++) for (int x = 0; x < s; x++)
            {
                float n = 0.6f * Noise(x / 256f * 16f, y / 256f * 16f) + 0.4f * Noise(x / 256f * 32f, y / 256f * 32f);
                n = Mathf.Clamp01(n + 0.16f * Mathf.Sin(y / 256f * Mathf.PI * 4f));   // mown bands
                t.SetPixel(x, y, n < 0.5f ? Color.Lerp(c, a, n * 2f) : Color.Lerp(a, b, (n - 0.5f) * 2f));
            }
            t.Apply();
            var tex = SaveTex(t, "NatureGrass");
            var imp = AssetImporter.GetAtPath(Gen + "/Textures/NatureGrass.png") as TextureImporter;
            if (imp != null && imp.wrapMode != TextureWrapMode.Repeat) { imp.wrapMode = TextureWrapMode.Repeat; imp.SaveAndReimport(); }
            return tex;
        }

        static NatureMats CreateNatureMaterials(Mats M)
        {
            var N = new NatureMats();
            var src = AssetDatabase.LoadAssetAtPath<Material>(NatDir + "Materials/SimpleNaturePack_Texture_01.mat");
            N.prop = UrpCopy(src);
            N.grass = Mat("NatureGrass", "Universal Render Pipeline/Lit", Color.white, m => { m.SetTexture("_BaseMap", NatureGrassTexture()); m.SetFloat("_Smoothness", 0.05f); m.SetFloat("_Metallic", 0f); });
            var packSky = AssetDatabase.LoadAssetAtPath<Material>("Assets/AllSkyFree/Cartoon Base BlueSky/Day_BlueSky_Nothing.mat");
            if (packSky != null)
            {
                string sp = Gen + "/Materials/SkyboxNature.mat";
                var sky = AssetDatabase.LoadAssetAtPath<Material>(sp);
                if (sky == null) { sky = new Material(packSky); AssetDatabase.CreateAsset(sky, sp); }
                sky.shader = packSky.shader; sky.CopyPropertiesFromMaterial(packSky);
                EditorUtility.SetDirty(sky); N.sky = sky;
            }
            string pp = Gen + "/Data/PostFX_Nature.asset";
            var profile = AssetDatabase.LoadAssetAtPath<VolumeProfile>(pp);
            if (profile == null) { profile = ScriptableObject.CreateInstance<VolumeProfile>(); AssetDatabase.CreateAsset(profile, pp); }
            T Fx<T>() where T : VolumeComponent
            {
                if (profile.TryGet(out T have)) return have;
                var c = profile.Add<T>(true); c.hideFlags = HideFlags.HideInHierarchy; AssetDatabase.AddObjectToAsset(c, profile); return c;
            }
            var bloom = Fx<Bloom>(); bloom.threshold.Override(1.1f); bloom.intensity.Override(0.5f); bloom.scatter.Override(0.6f);
            var tone = Fx<Tonemapping>(); tone.mode.Override(TonemappingMode.Neutral);
            var vig = Fx<Vignette>(); vig.intensity.Override(0.2f); vig.smoothness.Override(0.45f);
            var grade = Fx<ColorAdjustments>(); grade.saturation.Override(18f); grade.contrast.Override(8f); grade.postExposure.Override(0.1f); grade.colorFilter.Override(Color.white);
            EditorUtility.SetDirty(profile); N.post = profile;
            return N;
        }

        /// <summary>A piece of the pack with its base on the origin of a holder: `height` tall, the URP material on every renderer.</summary>
        static GameObject NaturePiece(Transform parent, string rel, Vector3 localPos, float height, float yaw)
        {
            var prefab = NaturePrefab(rel); if (prefab == null) return null;
            var inst = (GameObject)PrefabUtility.InstantiatePrefab(prefab); PrefabUtility.UnpackPrefabInstance(inst, PrefabUnpackMode.Completely, InteractionMode.AutomatedAction);
            var rs = inst.GetComponentsInChildren<Renderer>(true);
            var b = rs[0].bounds; foreach (var r in rs) b.Encapsulate(r.bounds);
            var holder = new GameObject("Piece_" + rel); holder.transform.SetParent(parent, false);
            holder.transform.localPosition = localPos; holder.transform.localRotation = Quaternion.Euler(0f, yaw, 0f);
            inst.transform.SetParent(holder.transform, false);
            float k = height / Mathf.Max(0.001f, b.size.y);
            inst.transform.localScale = Vector3.one * k;
            inst.transform.localPosition = new Vector3(-b.center.x * k, -b.min.y * k, -b.center.z * k);
            foreach (var r in rs)
            {
                r.shadowCastingMode = ShadowCastingMode.Off; r.receiveShadows = false;
                var ms = r.sharedMaterials; for (int i = 0; i < ms.Length; i++) ms[i] = NM.prop; r.sharedMaterials = ms;
            }
            return holder;
        }

        static GameObject BuildNatureWorld(Mats M, Meshes X, Defs D)
        {
            var root = new GameObject("NatureWorld");
            var sc = root.AddComponent<WorldScroller>();
            // the meadow: one big plane tiled with the grass texture (a tile every 9 units), sliding toward the camera
            var floor = GameObject.CreatePrimitive(PrimitiveType.Plane); UnityEngine.Object.DestroyImmediate(floor.GetComponent<Collider>());
            floor.name = "Meadow"; floor.transform.SetParent(root.transform, false); floor.transform.position = new Vector3(0f, SeaLevel, 120f); floor.transform.localScale = new Vector3(60f, 1f, 40f);
            var fr = floor.GetComponent<MeshRenderer>(); fr.sharedMaterial = NM.grass; fr.shadowCastingMode = ShadowCastingMode.Off; fr.receiveShadows = true;
            NM.grass.SetTextureScale("_BaseMap", new Vector2(600f / 18f, 400f / 18f));
            sc.water = fr; sc.waterTilesPerUnit = 1f / 18f;
            var rnd = new System.Random(41);
            string[] trees = { "Tree_01", "Tree_02", "Tree_03", "Tree_04", "Tree_05" };
            int n = 0;
            for (float z = -22f; z < 200f; z += 3.4f)
            {
                for (int side = -1; side <= 1; side += 2)
                {
                    int count = 1 + rnd.Next(3);
                    for (int c = 0; c < count; c++)
                    {
                        float roll = (float)rnd.NextDouble();
                        float x = side * Mathf.Lerp(8f, roll < 0.6f ? 20f : 50f, (float)rnd.NextDouble());
                        var p = new GameObject("Prop" + n++); p.transform.SetParent(root.transform, false);   // unit scale: WorldScroller scales it by the line things come out of
                        p.transform.position = new Vector3(x, SeaLevel - 0.05f, z + (float)rnd.NextDouble() * 3f);
                        float far = Mathf.Abs(x) > 24f ? 1.8f : 1f;
                        float kind = (float)rnd.NextDouble();
                        if (kind < 0.30f) NaturePiece(p.transform, trees[rnd.Next(trees.Length)], Vector3.zero, Mathf.Lerp(5f, 10f, (float)rnd.NextDouble()) * far, rnd.Next(360));
                        else if (kind < 0.46f) NaturePiece(p.transform, "Bush_0" + (1 + rnd.Next(3)), Vector3.zero, Mathf.Lerp(1.8f, 3.4f, (float)rnd.NextDouble()) * far, rnd.Next(360));
                        else if (kind < 0.64f) NaturePiece(p.transform, "Flowers_0" + (1 + rnd.Next(2)), Vector3.zero, Mathf.Lerp(1.4f, 2.6f, (float)rnd.NextDouble()), rnd.Next(360));
                        else if (kind < 0.80f) NaturePiece(p.transform, "Rock_0" + (1 + rnd.Next(5)), Vector3.zero, Mathf.Lerp(1.5f, 4.2f, (float)rnd.NextDouble()) * far, rnd.Next(360));
                        else if (kind < 0.90f) NaturePiece(p.transform, "Mushroom_0" + (1 + rnd.Next(2)), Vector3.zero, Mathf.Lerp(1.6f, 3.2f, (float)rnd.NextDouble()), rnd.Next(360));
                        else if (kind < 0.95f) NaturePiece(p.transform, "Stump_01", Vector3.zero, Mathf.Lerp(1.3f, 2.2f, (float)rnd.NextDouble()), rnd.Next(360));
                        else NaturePiece(p.transform, "Grass_0" + (1 + rnd.Next(2)), Vector3.zero, Mathf.Lerp(1.4f, 2.4f, (float)rnd.NextDouble()), rnd.Next(360));
                        sc.buoys.Add(p.transform);
                    }
                }
            }
            sc.recycleBehind = -26f; sc.recycleAhead = 226f;
            // distant plateaus: the pack's ground chunks, great and hazy, far to either side
            var ridge = new GameObject("Ridge"); ridge.transform.SetParent(root.transform, false);
            float[][] pl = { new[] { -150f, 300f, 12f }, new[] { 170f, 330f, 15f }, new[] { -330f, 380f, 18f }, new[] { 330f, 400f, 14f } };
            string[] pr = { "Ground_02", "Ground_02", "Ground_02", "Ground_02" };
            for (int i = 0; i < pl.Length; i++)
            {
                var h = NaturePiece(ridge.transform, pr[i], new Vector3(pl[i][0], SeaLevel - 2f, pl[i][1]), pl[i][2], i * 90f);
            }
            // the cloud bank the world ends in and the near clouds: the sea world's own
            var wallMesh = MeshFactory.Panel(70f, 27f); wallMesh.name = "CloudWall";
            var wall = MeshObj("CloudWall", SaveMesh(wallMesh), root.transform, M.cloudWall);
            wall.transform.position = new Vector3(0f, SeaLevel - 4f, D.config.appearZ + D.config.appearRange + 8f);
            var wrr = wall.GetComponent<MeshRenderer>(); wrr.shadowCastingMode = ShadowCastingMode.Off; wrr.receiveShadows = false;
            for (int i = 0; i < 9; i++)
            {
                var cluster = new GameObject("Cloud" + i); cluster.transform.SetParent(root.transform, false);
                float side = i % 2 == 0 ? -1f : 1f;
                cluster.transform.position = new Vector3(side * (12f + (float)rnd.NextDouble() * 40f), 12f + (float)rnd.NextDouble() * 12f, 30f + i * 22f);
                int puffs = 2 + rnd.Next(2);
                for (int p = 0; p < puffs; p++)
                {
                    var q = GameObject.CreatePrimitive(PrimitiveType.Quad); UnityEngine.Object.DestroyImmediate(q.GetComponent<Collider>());
                    q.name = "Puff" + p; q.transform.SetParent(cluster.transform, false);
                    float s = 12f + (float)rnd.NextDouble() * 12f, flip = rnd.Next(2) == 0 ? -1f : 1f;
                    q.transform.localPosition = new Vector3(((float)rnd.NextDouble() - 0.5f) * s * 0.9f, ((float)rnd.NextDouble() - 0.3f) * s * 0.25f, p * 1.5f);
                    q.transform.localScale = new Vector3(s * flip, s * 0.5f, 1f);
                    var qr = q.GetComponent<MeshRenderer>(); qr.sharedMaterial = M.cloud; qr.shadowCastingMode = ShadowCastingMode.Off;
                }
                sc.clouds.Add(cluster.transform);
            }
            {   // pollen and drifting petals
                var go = new GameObject("Pollen"); go.transform.SetParent(root.transform, false); go.transform.position = new Vector3(0f, SeaLevel + 3f, 62f);
                var ps = go.AddComponent<ParticleSystem>();
                var main = ps.main; main.loop = true; main.playOnAwake = true; main.simulationSpace = ParticleSystemSimulationSpace.World; main.maxParticles = 200; main.prewarm = true;
                main.startLifetime = new ParticleSystem.MinMaxCurve(6f, 10f); main.startSpeed = 0f; main.startSize = new ParticleSystem.MinMaxCurve(0.08f, 0.22f);
                main.startColor = new ParticleSystem.MinMaxGradient(new Color(1f, 0.95f, 0.6f, 0.9f), new Color(1f, 1f, 1f, 0.9f));
                var em = ps.emission; em.rateOverTime = 14f;
                var sh = ps.shape; sh.shapeType = ParticleSystemShapeType.Box; sh.scale = new Vector3(60f, 8f, 100f);
                var vel = ps.velocityOverLifetime; vel.enabled = true; vel.space = ParticleSystemSimulationSpace.World;
                vel.x = new ParticleSystem.MinMaxCurve(-0.6f, 0.6f); vel.y = new ParticleSystem.MinMaxCurve(0.1f, 0.7f); vel.z = new ParticleSystem.MinMaxCurve(-10f, -7f);
                var noise = ps.noise; noise.enabled = true; noise.strength = 0.8f; noise.frequency = 0.2f;
                var pr2 = go.GetComponent<ParticleSystemRenderer>(); pr2.sharedMaterial = LM != null ? LM.ember : M.particle; pr2.shadowCastingMode = ShadowCastingMode.Off;
            }
            return root;
        }

        // ------------------------------------------------------------------ cast
        static readonly string[] NatureBossNames = { "THORN WASP", "BARK BEETLE", "MOSS GOLEM", "FUNGUS KING", "ANCIENT GROVE" };
        static readonly string[] NatureStageNames = { "WILD MEADOW" };

        static readonly Color[][] NaturePalettes = {
            new[] { new Color(0.35f, 0.62f, 0.14f), new Color(0.08f, 0.10f, 0.05f), new Color(1f, 0.85f, 0.2f), new Color(0.1f, 0.3f, 0.02f), new Color(0.6f, 1f, 0.2f), new Color(1f, 1f, 0.6f) },    // 0 leaf and sun
            new[] { new Color(0.85f, 0.62f, 0.10f), new Color(0.10f, 0.08f, 0.04f), new Color(0.30f, 0.20f, 0.05f), new Color(0.4f, 0.25f, 0f), new Color(1f, 0.75f, 0.1f), new Color(1f, 0.95f, 0.5f) },  // 1 amber and bark
        };

        static Material NatureShipMaterial(int palette)
        {
            var src = AssetDatabase.LoadAssetAtPath<Material>("Assets/StarSparrow/Materials/StarSparrow_Black.mat"); if (src == null) return null;
            string path = Gen + "/Materials/NatureShip" + palette + ".mat";
            var m = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (m == null) { m = new Material(src); AssetDatabase.CreateAsset(m, path); }
            m.shader = src.shader; m.CopyPropertiesFromMaterial(src);
            var p = NaturePalettes[palette % NaturePalettes.Length];
            m.SetColor("_Color1", p[0]); m.SetColor("_Color2", p[1]); m.SetColor("_Color3", p[2]);
            m.SetColor("_Emission1", p[3]); m.SetColor("_Emission2", p[4]); m.SetColor("_Emission3", p[5]);
            m.SetColor("_Cockpit1", p[3]); m.SetColor("_Cockpit2", p[4]); m.SetColor("_Cockpit3", p[5]);
            m.SetFloat("_EmissionMultiplier", 1.6f); m.SetFloat("_CockpitMultiplier", 1.4f); m.SetFloat("_Dirty", 0.25f); m.SetFloat("_Darken", 0f);
            EditorUtility.SetDirty(m);
            return m;
        }

        static Material NatureRemap(Material m, int palette)
        {
            if (m == null || m.shader == null) return null;
            string sn = m.shader.name;
            if (sn.IndexOf("ColorizeSparrow", StringComparison.OrdinalIgnoreCase) >= 0) return NatureShipMaterial(palette);
            if (sn == "Standard") return NM.prop;   // the pack's own pieces: bush, mushroom, rock
            return null;
        }

        static void DecorateNatureShip(GameObject model, string parts)
        {
            var rs = model.GetComponentsInChildren<Renderer>(true); if (rs.Length == 0) return;
            var b = rs[0].bounds; foreach (var r in rs) b.Encapsulate(r.bounds);
            Vector3 c = b.center, s = b.size; float top = b.max.y;
            foreach (var part in parts.Split('+'))
            {
                if (part == "bush") AddLavaPart(model, "nature:Bush_03", new Vector3(0f, top - 0.06f * s.y, c.z - 0.05f * s.z), Vector3.zero, 0.2f * s.z);
                else if (part == "mushrooms")
                    for (int sx = -1; sx <= 1; sx += 2) AddLavaPart(model, "nature:Mushroom_01", new Vector3(sx * 0.3f * s.x, c.y + 0.1f * s.y, c.z), new Vector3(0f, 0f, -sx * 25f), 0.20f * s.z);
                else if (part == "flowers") AddLavaPart(model, "nature:Flowers_01", new Vector3(0f, top - 0.04f * s.y, c.z + 0.15f * s.z), Vector3.zero, 0.16f * s.z);
            }
        }

        static GameObject[] BuildNatureBosses(Mats M)
        {
            var defs = new[] {
                new LavaBossDef("S17", 0, "bush+flowers", 3.0f), new LavaBossDef("S28", 1, "mushrooms", 3.1f),
                new LavaBossDef("nature:Rock_05", 0, "", 3.4f, 3.0f), new LavaBossDef("nature:Mushroom_01", 0, "", 3.3f, 3.4f), new LavaBossDef("nature:Tree_01", 0, "", 4.0f, 5.0f) };
            var res = new GameObject[5];
            for (int i = 0; i < 5; i++)
            {
                var d = defs[i];
                bool ship = d.model[0] == 'S' && char.IsDigit(d.model[1]);
                var def = new PackBoss { name = "Nature" + (i + 1).ToString("00"), triangles = 12000, width = d.width, maxHeight = d.maxHeight, lieAcross = false, keepMaterials = true };
                int pal = d.palette; string parts = d.parts;
                def.remap = m => NatureRemap(m, pal);
                if (ship) { def.packPrefab = LavaShipPath(d.model); def.decorate = go => DecorateNatureShip(go, parts); }
                else def.packPrefab = NatDir + "Prefabs/" + d.model.Substring(7) + ".prefab";
                res[i] = PackBossPrefab(def, EnsurePackBossLow(def), M);
                if (res[i] == null) Debug.LogWarning("[SkySquad] nature boss " + (i + 1) + " could not be built");
            }
            return res;
        }

        static GameObject BuildNatureFighter(Mats M, Meshes X)
        {
            var low = EnsureOH1Low(); if (low == null) return null;
            var body = Lit("WaspFighterBody", Color.white, 0.4f);
            body.SetColor("_BaseColor", new Color(1f, 0.82f, 0.25f));
            var alb = AssetDatabase.LoadAssetAtPath<Texture2D>(Root + "/Art/Enemies/OH1_Fuselage_BaseColor.png"); if (alb != null) body.SetTexture("_BaseMap", alb);
            var nrm = NormalMap(Root + "/Art/Enemies/OH1_Fuselage_Normal.png"); if (nrm != null) { body.SetTexture("_BumpMap", nrm); body.EnableKeyword("_NORMALMAP"); }
            var glass = Transparent("WaspFighterGlass", new Color(0.4f, 0.8f, 0.3f, 0.7f));
            return OH1EnemyPrefab("EnemyFighterWasp", low, X.prop, M, () => null, body, glass, new Color(1f, 0.9f, 0.4f, 0.9f));
        }

        static GameObject BuildNatureBreakable(Mats M, Meshes X)
        {
            var slab = NaturePrefab("Rock_05"); var pad = NaturePrefab("Ground_01");
            if (slab == null || pad == null) return null;
            var root = new GameObject("BreakableNature");
            var bk = root.AddComponent<Breakable>();
            float raftTop = -1.125f; int n = 3; float tierH = 1.15f, h = tierH * n;
            var crate = new GameObject("Crate"); crate.transform.SetParent(root.transform, false);
            crate.transform.localPosition = new Vector3(0f, raftTop + h * 0.5f, 0f);
            var tiers = new GameObject[n]; var rends = new Renderer[n];
            for (int i = 0; i < n; i++)
            {
                var inst = (GameObject)PrefabUtility.InstantiatePrefab(slab); PrefabUtility.UnpackPrefabInstance(inst, PrefabUnpackMode.Completely, InteractionMode.AutomatedAction);
                inst.name = "Tier" + i; inst.transform.SetParent(crate.transform, false);
                var rs = inst.GetComponentsInChildren<Renderer>(true); var b = rs[0].bounds; foreach (var r in rs) b.Encapsulate(r.bounds);
                float kx = 5.0f / b.size.x, ky = tierH / b.size.y, kz = 3.0f / b.size.z;
                inst.transform.localScale = new Vector3(kx, ky, kz);
                inst.transform.localRotation = Quaternion.Euler(0f, (i - 1) * 6f, 0f);
                inst.transform.localPosition = new Vector3(-b.center.x * kx, -h * 0.5f + tierH * (n - 1 - i) - b.min.y * ky, -b.center.z * kz);
                foreach (var r in rs) { r.shadowCastingMode = ShadowCastingMode.On; r.receiveShadows = true; var ms = r.sharedMaterials; for (int k = 0; k < ms.Length; k++) ms[k] = NM.prop; r.sharedMaterials = ms; }
                tiers[i] = inst; rends[i] = rs[0];
            }
            var boat = new GameObject("Boat"); boat.transform.SetParent(root.transform, false);
            var pi = (GameObject)PrefabUtility.InstantiatePrefab(pad); PrefabUtility.UnpackPrefabInstance(pi, PrefabUnpackMode.Completely, InteractionMode.AutomatedAction);
            pi.transform.SetParent(boat.transform, false);
            var prs = pi.GetComponentsInChildren<Renderer>(true); var pb = prs[0].bounds; foreach (var r in prs) pb.Encapsulate(r.bounds);
            float pk = 7.4f / Mathf.Max(pb.size.x, pb.size.z);
            pi.transform.localScale = new Vector3(pk, pk * 1.6f, pk);
            pi.transform.localPosition = new Vector3(-pb.center.x * pk, raftTop - pb.max.y * pk * 1.6f, -pb.center.z * pk);
            foreach (var r in prs) { r.shadowCastingMode = ShadowCastingMode.Off; r.receiveShadows = true; var ms = r.sharedMaterials; for (int k = 0; k < ms.Length; k++) ms[k] = NM.prop; r.sharedMaterials = ms; }
            float boxTop = raftTop + h;
            bk.model = crate.transform; bk.tiers = tiers; bk.crateRenderers = rends;
            bk.boat = boat.transform; bk.boatRenderer = null; bk.weaponBoatMesh = null;
            bk.label = Label3D("Label", root.transform, new Vector3(0f, raftTop + h * 0.45f, -1.65f), 18f, Color.white, fontOutline);
            bk.hint = Label3D("Hint", root.transform, new Vector3(0f, boxTop + 0.82f, -0.6f), 4f, Gold, fontOutlineSmall);
            bk.boxTop = boxTop;
            bk.prizeAura = Cfxr("Misc/CFXR2 Shiny Item (Loop)"); bk.prizeGlow = Cfxr("Light/CFXR3 LightGlow A (Loop)"); bk.prizeTrail = M.tracer;
            return SavePrefab(root, "BreakableNature");
        }

        static GameObject BuildNatureSplash(Mats M)
        {
            var root = new GameObject("NatureSplash");
            var ps = ParticlePrefab(root, M.particle, 0, 3f, 8f, 0.18f, 0.5f, 0.45f, 0.9f, new Color(0.7f, 1f, 0.4f), new Color(0.85f, 0.7f, 0.35f), 1.2f, true);
            var em = ps.emission; em.SetBursts(new ParticleSystem.Burst[0]);
            var main = ps.main; main.playOnAwake = false;
            var sh = ps.shape; sh.shapeType = ParticleSystemShapeType.Cone; sh.angle = 34f; sh.radius = 0.4f; sh.rotation = new Vector3(-90f, 0f, 0f);
            return SavePrefab(root, "NatureSplash");
        }

        static BossAttack[] NatureAttacks()
        {
            var A = new BossAttack[5];
            A[0] = Sig(Fly("thorn darts", "green_shuriken", 4, 0.14f, 2.0f, 0.5f, MoveStyle.Sway, 1.4f, 0.8f, 0f, 4.2f, 2.4f), ShotOrigin.Muzzle, ShotOrder.LeftToRight, 1f, 1, 0.45f, 0.15f, GlowAlien);
            A[1] = Sky("falling boulders", "top_down_stone_circle", 3, 0.2f, 0.6f, MoveStyle.Dash, 3.0f, 1f, 0f, 4.4f);
            A[2] = LSpikes("root spikes", 0.6f, MoveStyle.Sway, 1.2f, 0.7f, 0f, 4.4f, 3, Hv("AoE effects/Crystals crossfade 2"), 0.45f, 1.2f, 8, 1.5f, 0.25f, Hv("Hits and explosions/Green hit"), 3f, GlowAlien);
            A[3] = LZone("spore clouds", 0.6f, MoveStyle.Figure8, 2.0f, 0.9f, 0.5f, 4.2f, 4, 1.9f, 1.1f, 0.15f, Hv("AoE effects/Smoke AOE explosion"), 1.1f, TellGreen(), 4f, Hv("Hits and explosions/Green hit"), 4f, 0.25f, 0.3f, GlowAlien);
            A[4] = LTornado("leaf storm", 0.7f, MoveStyle.Sway, 1.4f, 0.7f, 0f, 4.6f, 3, Gq("Tornado_01"), 3f, 1.6f, 2.8f, 2.4f, 0.6f, Cfxr("Nature/CFXR3 Hit Leaves A (Lit)"), 3f, 0.3f, GlowAlien);
            return A;
        }

        static BossAttack[] NatureAttacks2()
        {
            var B = new BossAttack[5];
            B[0] = Sig(Fly("wasp swarm", "wind", 7, 0.07f, 3.0f, 0.3f, MoveStyle.Dash, 3.4f, 1.3f, 0f, 3.2f, 2.2f), ShotOrigin.Above, ShotOrder.CenterOut, 1.4f, 2, 0.5f, 0.15f, GlowAlien);
            B[1] = Sky("boulder rain", "top_down_stone_dot", 5, 0.12f, 0.5f, MoveStyle.Figure8, 2.6f, 1.2f, 0.5f, 3.4f);
            B[2] = LSpikes("root field", 0.4f, MoveStyle.Sweep, 3.4f, 1.5f, 0f, 3.2f, 5, Hv("AoE effects/Crystals crossfade 2"), 0.45f, 1.2f, 7, 1.1f, 0.15f, Hv("Hits and explosions/Green hit"), 3f, GlowAlien);
            B[3] = LZone("toxic bloom", 0.5f, MoveStyle.Orbit, 2.8f, 1.1f, 0.8f, 3.4f, 6, 1.8f, 0.9f, 0.15f, Hv("AoE effects/Ground AOE explosion"), 1.1f, TellGreen(), 4f, Hv("Hits and explosions/Green hit"), 4f, 0.14f, 0.4f, GlowAlien);
            B[4] = LSweep("grove wrath", 0.6f, MoveStyle.Sweep, 3.2f, 1.2f, 0f, 3.2f, ShotOrder.OutsideIn, null, 1f, Hv("Hits and explosions/Green hit"), 3f, 2.6f, 1.3f, 0.14f, 0.4f, 3f, true, CLime, 0.8f, GlowAlien);
            return B;
        }

        static WorldEntry NatureEntry(GameObject root, WorldEntry sea, Prefabs P, Mats M, Meshes X)
        {
            var N = NM;
            var bosses = BuildNatureBosses(M);
            var fighter = BuildNatureFighter(M, X);
            var crate = BuildNatureBreakable(M, X);
            var splash = BuildNatureSplash(M);
            return new WorldEntry
            {
                id = "nature", displayName = "SUNNY MEADOW", tagline = "Green hills  -  5 bosses",
                thumbnail = WorldSprite("world_nature.png", new Color(0.4f, 0.75f, 0.3f)), accent = new Color(0.45f, 0.80f, 0.25f),
                environment = new[] { root }, skybox = N.sky, skyRotation = 0f,
                sunColor = new Color(1f, 0.96f, 0.86f), sunIntensity = 1.5f, sunEuler = new Vector3(52f, -28f, 0f), sunShadow = 0.55f,
                fog = true, fogColor = new Color(0.86f, 0.93f, 0.98f), fogStart = 120f, fogEnd = 200f, ambientFromSky = true, ambientIntensity = 1f,
                post = N.post,
                fighterPrefab = fighter != null ? fighter : sea.fighterPrefab, bossPrefabs = bosses, bossPrefabByNumber = bosses, bossAttacks = NatureAttacks(), bossAttacks2 = NatureAttacks2(), bossNames = NatureBossNames, bossColors = null, stageNames = NatureStageNames,
                lastBoss = 5, bossHpMul = 1.2f, breakablePrefab = crate != null ? crate : sea.breakablePrefab, splashPrefab = splash != null ? splash : sea.splashPrefab, surfaceRing = new Color(0.8f, 1f, 0.6f)
            };
        }
    }
}
