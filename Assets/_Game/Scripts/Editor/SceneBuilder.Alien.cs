// SceneBuilder.Alien.cs (Editor only)
// World 3: the alien forest (2026-10-02: "a world from the Free Demo of Low Poly Space Alien Worlds 3D pack, as professional as the lava world").
// Built from Assets/Free Demo of Low Poly Space Alien Worlds 3D Asset Pack (one biome, "Space Forest": glowing crystals, saucer-cap trees, spires,
// ground slabs, a sci-fi antenna, a planet) over a bioluminescent lake (Stylized Water 3 recoloured), under the AllSky "Another Planet" night sky.
// The shore is islands - a ground slab with trees, crystals and rocks standing on it - that scroll past on both sides.
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
        const string AlienDir = "Assets/Free Demo of Low Poly Space Alien Worlds 3D Asset Pack/";

        static GameObject AlienPrefab(string rel)
        {
            string[] folders = { "SP_Crystals/", "SP_Ground/", "SP_Mountains/", "SP_Plants/", "SP_Rocks/", "SP_Stones/", "SP_Trees/", "" };
            foreach (var f in folders) { var p = AssetDatabase.LoadAssetAtPath<GameObject>(AlienDir + "Prefabs/Space Forest/" + f + rel + ".prefab"); if (p != null) return p; }
            Debug.LogWarning("[SkySquad] alien prefab missing: " + rel); return null;
        }
        static bool HaveAlien() { return AssetDatabase.LoadAssetAtPath<GameObject>(AlienDir + "Prefabs/Space Forest/SP_Trees/SP_Tree01.prefab") != null; }

        class AlienMats { public Material water, glowCrystal, glow, mist, mistPuff, sky, spore; public VolumeProfile post; }
        static AlienMats AM;

        static AlienMats CreateAlienMaterials(Mats M)
        {
            var A = new AlienMats();
            // the lake: Stylized Water 3 as the sea is, recoloured to a deep violet with a turquoise glow in the shallows and a cyan horizon
            var srcWater = AssetDatabase.LoadAssetAtPath<Material>("Assets/Stylized Water 3/Materials/StylizedWater3_ArcadeOcean.mat");
            if (srcWater != null)
            {
                string path = Gen + "/Materials/WaterAlien.mat";
                var w = AssetDatabase.LoadAssetAtPath<Material>(path);
                if (w == null) { w = new Material(srcWater); AssetDatabase.CreateAsset(w, path); }
                else { w.shader = srcWater.shader; w.CopyPropertiesFromMaterial(srcWater); w.shaderKeywords = srcWater.shaderKeywords; }
                w.SetVector("_Direction", new Vector4(0f, -1f, 0f, 0f)); w.SetFloat("_WaveHeight", 0.3f);
                w.SetColor("_BaseColor", new Color(0.035f, 0.01f, 0.13f)); w.SetColor("_ShallowColor", new Color(0.04f, 0.40f, 0.45f));
                w.SetColor("_HorizonColor", new Color(0.30f, 0.9f, 1.6f)); w.SetColor("_FoamColor", new Color(0.7f, 1f, 1f));
                w.SetFloat("_ReflectionStrength", 0.5f); w.SetFloat("_SunReflectionStrength", 4f);
                EditorUtility.SetDirty(w);
                A.water = w;
            }
            // crystals glow: the pack's palette material with its own texture as the emission, boosted cyan
            var packMat = AssetDatabase.LoadAssetAtPath<GameObject>(AlienDir + "Prefabs/Space Forest/SP_Crystals/SP_Crystal01.prefab").GetComponentInChildren<Renderer>().sharedMaterial;
            string cp = Gen + "/Materials/AlienCrystal.mat";
            var cm = AssetDatabase.LoadAssetAtPath<Material>(cp);
            if (cm == null) { cm = new Material(packMat); AssetDatabase.CreateAsset(cm, cp); }
            cm.shader = packMat.shader; cm.CopyPropertiesFromMaterial(packMat);
            var tex = packMat.GetTexture("_BaseMap");
            cm.SetTexture("_EmissionMap", tex); cm.SetColor("_EmissionColor", new Color(0.35f, 1.2f, 1.7f)); cm.EnableKeyword("_EMISSION"); cm.globalIlluminationFlags = MaterialGlobalIlluminationFlags.None; cm.SetFloat("_Smoothness", 0.7f);
            EditorUtility.SetDirty(cm);
            A.glowCrystal = cm;
            // the pools of light round every island, the mist bank the world ends in, the spores
            A.glow = Particle("AlienGlow", new Color(0.15f, 0.9f, 0.85f, 0.5f), true); A.glow.SetTexture("_BaseMap", SoftTexture());
            A.mist = Mat("AlienMist", "SkySquad/CloudWall", new Color(0.36f, 0.26f, 0.62f, 1f), m => m.SetTexture("_MainTex", CloudWallTexture()));
            A.mistPuff = Transparent("AlienMistPuff", new Color(0.30f, 0.22f, 0.50f, 0.55f)); A.mistPuff.SetTexture("_BaseMap", CloudTexture());
            A.spore = Particle("Spore", Color.white, true); A.spore.SetTexture("_BaseMap", SoftTexture());
            var packSky = AssetDatabase.LoadAssetAtPath<Material>("Assets/AllSkyFree/Space_AnotherPlanet/AllSky_Space_AnotherPlanet.mat");
            if (packSky != null)
            {
                string sp = Gen + "/Materials/SkyboxAlien.mat";
                var sky = AssetDatabase.LoadAssetAtPath<Material>(sp);
                if (sky == null) { sky = new Material(packSky); AssetDatabase.CreateAsset(sky, sp); }
                sky.shader = packSky.shader; sky.CopyPropertiesFromMaterial(packSky);
                EditorUtility.SetDirty(sky); A.sky = sky;
            }
            string profilePath = Gen + "/Data/PostFX_Alien.asset";
            var profile = AssetDatabase.LoadAssetAtPath<VolumeProfile>(profilePath);
            if (profile == null) { profile = ScriptableObject.CreateInstance<VolumeProfile>(); AssetDatabase.CreateAsset(profile, profilePath); }
            T Fx<T>() where T : VolumeComponent
            {
                if (profile.TryGet(out T have)) return have;
                var c = profile.Add<T>(true); c.hideFlags = HideFlags.HideInHierarchy; AssetDatabase.AddObjectToAsset(c, profile); return c;
            }
            var bloom = Fx<Bloom>(); bloom.threshold.Override(0.9f); bloom.intensity.Override(1.0f); bloom.scatter.Override(0.75f);
            var tone = Fx<Tonemapping>(); tone.mode.Override(TonemappingMode.Neutral);
            var vig = Fx<Vignette>(); vig.intensity.Override(0.34f); vig.smoothness.Override(0.5f); vig.color.Override(new Color(0.03f, 0.0f, 0.10f));
            var grade = Fx<ColorAdjustments>(); grade.saturation.Override(16f); grade.contrast.Override(12f); grade.postExposure.Override(0.1f); grade.colorFilter.Override(new Color(0.92f, 0.95f, 1f));
            EditorUtility.SetDirty(profile); A.post = profile;
            return A;
        }

        /// <summary>One placed piece of the pack: its base on the origin of a unit-scale holder, `height` tall, crystals in the glowing material.</summary>
        static GameObject AlienPiece(Transform parent, string rel, Vector3 localPos, float height, float yaw, bool glowMat = false, float lean = 0f)
        {
            var prefab = AlienPrefab(rel); if (prefab == null) return null;
            var inst = (GameObject)PrefabUtility.InstantiatePrefab(prefab); PrefabUtility.UnpackPrefabInstance(inst, PrefabUnpackMode.Completely, InteractionMode.AutomatedAction);
            var rs = inst.GetComponentsInChildren<Renderer>(true);
            var b = rs[0].bounds; foreach (var r in rs) b.Encapsulate(r.bounds);   // at the origin: world units
            var holder = new GameObject("Piece_" + rel); holder.transform.SetParent(parent, false);
            holder.transform.localPosition = localPos; holder.transform.localRotation = Quaternion.Euler(lean, yaw, 0f);
            inst.transform.SetParent(holder.transform, false);
            float k = height / Mathf.Max(0.001f, b.size.y);
            inst.transform.localScale = Vector3.one * k;
            inst.transform.localPosition = new Vector3(-b.center.x * k, -b.min.y * k, -b.center.z * k);
            foreach (var r in rs)
            {
                r.shadowCastingMode = ShadowCastingMode.Off; r.receiveShadows = false;
                if (glowMat && AM != null && AM.glowCrystal != null) { var ms = r.sharedMaterials; for (int i = 0; i < ms.Length; i++) ms[i] = AM.glowCrystal; r.sharedMaterials = ms; }
            }
            return holder;
        }

        /// <summary>The whole alien world as one scene root: the lake, the islands that scroll past, the far mountains and a moon, the mist bank the world
        /// ends in, drifting mist and rising spores.</summary>
        static GameObject BuildAlienWorld(Mats M, Meshes X, Defs D)
        {
            var root = new GameObject("AlienWorld");
            var sc = root.AddComponent<WorldScroller>();
            var A = AM;
            var lake = MeshObj("Lake", X.sea, root.transform, A.water != null ? A.water : M.water); lake.transform.localPosition = new Vector3(0f, SeaLevel, 0f);
            var lr = lake.GetComponent<MeshRenderer>(); lr.shadowCastingMode = ShadowCastingMode.Off; lr.receiveShadows = true;
            var far = GameObject.CreatePrimitive(PrimitiveType.Plane); UnityEngine.Object.DestroyImmediate(far.GetComponent<Collider>());
            far.name = "LakeFar"; far.transform.SetParent(root.transform, false); far.transform.position = new Vector3(0f, SeaLevel - 1f, 120f); far.transform.localScale = new Vector3(120f, 1f, 120f);
            var fr = far.GetComponent<MeshRenderer>(); fr.sharedMaterial = A.water != null ? A.water : M.water; fr.shadowCastingMode = ShadowCastingMode.Off;
            sc.water = lr;
            var rnd = new System.Random(31);
            string[] trees = { "SP_Tree01", "SP_Tree02", "SP_Tree03", "SP_Tree04" };
            string[] crystals = { "SP_Crystal01", "SP_Crystal02" };
            string[] rocks = { "SP_Rock01", "SP_Rock02", "SP_Rock04", "SP_Rock05", "SP_Rock06", "SP_Rock07", "SP_Rock09" };
            string[] plants = { "SP_Plant01", "SP_Plant06", "SP_Plant07", "SP_Plant08" };
            string[] slabs = { "SP_Ground02", "SP_Ground05", "SP_Ground04", "SP_Ground03" };
            int n = 0;
            for (float z = -22f; z < 200f; z += 6.4f)
            {
                for (int side = -1; side <= 1; side += 2)
                {
                    float roll = (float)rnd.NextDouble();
                    if (roll < 0.12f) continue;   // gaps: not every slot has an island
                    float x = side * Mathf.Lerp(9.5f, roll < 0.7f ? 18f : 36f, (float)rnd.NextDouble());
                    var isle = new GameObject("Island" + n++); isle.transform.SetParent(root.transform, false);   // unit scale: WorldScroller scales this by the line things come out of
                    isle.transform.position = new Vector3(x, SeaLevel - 0.1f, z + (float)rnd.NextDouble() * 4f);
                    float size = Mathf.Lerp(5f, 11f, (float)rnd.NextDouble()); if (x * x > 22f * 22f) size *= 1.6f;
                    AlienPiece(isle.transform, slabs[rnd.Next(slabs.Length)], Vector3.zero, 0.5f, rnd.Next(360));
                    // the slab is wider than tall: AlienPiece fitted it 0.5 tall; widen it to the island's size
                    var slab = isle.transform.GetChild(0); var sr = slab.GetComponentsInChildren<Renderer>(); var sb2 = sr[0].bounds; foreach (var r in sr) sb2.Encapsulate(r.bounds);
                    float widen = size / Mathf.Max(0.1f, Mathf.Max(sb2.size.x, sb2.size.z)); slab.localScale = new Vector3(widen, 1f, widen);
                    int pieces = 2 + rnd.Next(4);
                    for (int p = 0; p < pieces; p++)
                    {
                        float a = (float)rnd.NextDouble() * Mathf.PI * 2f, rr = (float)rnd.NextDouble() * size * 0.28f;
                        var pos = new Vector3(Mathf.Cos(a) * rr, 0.3f, Mathf.Sin(a) * rr);
                        float kind = (float)rnd.NextDouble();
                        if (kind < 0.34f) AlienPiece(isle.transform, trees[rnd.Next(trees.Length)], pos, Mathf.Lerp(3.5f, 7.5f, (float)rnd.NextDouble()) * (x * x > 22f * 22f ? 1.7f : 1f), rnd.Next(360));
                        else if (kind < 0.62f) AlienPiece(isle.transform, crystals[rnd.Next(crystals.Length)], pos, Mathf.Lerp(2.6f, 5.5f, (float)rnd.NextDouble()), rnd.Next(360), true);
                        else if (kind < 0.86f) AlienPiece(isle.transform, rocks[rnd.Next(rocks.Length)], pos, Mathf.Lerp(1.8f, 5f, (float)rnd.NextDouble()), rnd.Next(360));
                        else AlienPiece(isle.transform, plants[rnd.Next(plants.Length)], pos, Mathf.Lerp(1.4f, 3f, (float)rnd.NextDouble()), rnd.Next(360), true);
                    }
                    if (rnd.NextDouble() < 0.12) AlienPiece(isle.transform, "SP_Sci-fi_Antenna", new Vector3(0f, 0.3f, 0f), 6f, rnd.Next(360));
                    var gl = GameObject.CreatePrimitive(PrimitiveType.Quad); UnityEngine.Object.DestroyImmediate(gl.GetComponent<Collider>());
                    gl.name = "Glow"; gl.transform.SetParent(isle.transform, false); gl.transform.localPosition = new Vector3(0f, 0.12f, 0f); gl.transform.localRotation = Quaternion.Euler(90f, 0f, 0f); gl.transform.localScale = new Vector3(size * 1.7f, size * 1.7f, 1f);
                    var gr = gl.GetComponent<MeshRenderer>(); gr.sharedMaterial = A.glow; gr.shadowCastingMode = ShadowCastingMode.Off; gr.receiveShadows = false;
                    sc.buoys.Add(isle.transform);
                }
            }
            sc.recycleBehind = -26f; sc.recycleAhead = 226f;
            // the far range: pyramid mountains and a moon, drifting slowly
            var ridge = new GameObject("Ridge"); ridge.transform.SetParent(root.transform, false);
            float[][] mts = { new[] { -190f, 330f, 38f }, new[] { 170f, 350f, 46f }, new[] { -110f, 430f, 56f }, new[] { -300f, 390f, 34f }, new[] { 290f, 400f, 42f } };
            string[] mp = { "SP_Mountain01", "SP_Mountain02", "SP_Mountain01", "SP_Mountain02", "SP_Mountain01" };
            for (int i = 0; i < mts.Length; i++) AlienPiece(ridge.transform, mp[i], new Vector3(mts[i][0], SeaLevel - 4f, mts[i][1]), mts[i][2], i * 70f);
            var moon = AlienPiece(ridge.transform, "SP_Planet", new Vector3(120f, 62f, 340f), 60f, 30f);
            var wallMesh = MeshFactory.Panel(70f, 27f); wallMesh.name = "CloudWall";
            var wall = MeshObj("MistWall", SaveMesh(wallMesh), root.transform, A.mist);
            wall.transform.position = new Vector3(0f, SeaLevel - 4f, D.config.appearZ + D.config.appearRange + 8f);
            var wrr = wall.GetComponent<MeshRenderer>(); wrr.shadowCastingMode = ShadowCastingMode.Off; wrr.receiveShadows = false;
            for (int i = 0; i < 9; i++)
            {
                var cluster = new GameObject("Mist" + i); cluster.transform.SetParent(root.transform, false);
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
                    var qr = q.GetComponent<MeshRenderer>(); qr.sharedMaterial = AM.mistPuff; qr.shadowCastingMode = ShadowCastingMode.Off;
                }
                sc.clouds.Add(cluster.transform);
            }
            {   // spores: glowing motes rising out of the lake and streaming back with the world
                var go = new GameObject("Spores"); go.transform.SetParent(root.transform, false); go.transform.position = new Vector3(0f, SeaLevel + 3f, 62f);
                var ps = go.AddComponent<ParticleSystem>();
                var main = ps.main; main.loop = true; main.playOnAwake = true; main.simulationSpace = ParticleSystemSimulationSpace.World; main.maxParticles = 300; main.prewarm = true;
                main.startLifetime = new ParticleSystem.MinMaxCurve(6f, 10f); main.startSpeed = 0f; main.startSize = new ParticleSystem.MinMaxCurve(0.10f, 0.32f);
                main.startColor = new ParticleSystem.MinMaxGradient(new Color(0.3f, 1f, 0.9f, 1f), new Color(0.8f, 0.5f, 1f, 1f));
                var em = ps.emission; em.rateOverTime = 28f;
                var sh = ps.shape; sh.shapeType = ParticleSystemShapeType.Box; sh.scale = new Vector3(60f, 10f, 100f);
                var vel = ps.velocityOverLifetime; vel.enabled = true; vel.space = ParticleSystemSimulationSpace.World;
                vel.x = new ParticleSystem.MinMaxCurve(-0.6f, 0.6f); vel.y = new ParticleSystem.MinMaxCurve(0.3f, 1.2f); vel.z = new ParticleSystem.MinMaxCurve(-10f, -7f);
                var col = ps.colorOverLifetime; col.enabled = true;
                var g = new Gradient(); g.SetKeys(new[] { new GradientColorKey(Color.white, 0f), new GradientColorKey(Color.white, 1f) }, new[] { new GradientAlphaKey(0f, 0f), new GradientAlphaKey(1f, 0.15f), new GradientAlphaKey(0.8f, 0.7f), new GradientAlphaKey(0f, 1f) });
                col.color = g;
                var noise = ps.noise; noise.enabled = true; noise.strength = 0.8f; noise.frequency = 0.2f;
                var pr = go.GetComponent<ParticleSystemRenderer>(); pr.sharedMaterial = A.spore; pr.shadowCastingMode = ShadowCastingMode.Off;
            }
            return root;
        }
    }
}
