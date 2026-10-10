// SceneBuilder.Lava.cs (Editor only)
// World 2: the lava world (2026-10-02: "a complete second level from the Inferno World pack - only the lava and everything that goes with it").
// Everything here is built from Assets/ithappy/Inferno_World_Free: its Lava shader for the surface, its rocks, horns, columns, braziers and
// cliffs for the shore, its sky for the heavens. The sea of world 1 is not touched; WorldManager switches between the two roots.
// If the pack is missing the builder logs a warning and the game has just the one world.
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
        const string Inf = "Assets/ithappy/Inferno_World_Free/";

        static GameObject InfPrefab(string rel) { var p = AssetDatabase.LoadAssetAtPath<GameObject>(Inf + "Prefabs/" + rel + ".prefab"); if (p == null) Debug.LogWarning("[SkySquad] Inferno prefab missing: " + rel); return p; }
        static bool HaveInferno() { return AssetDatabase.LoadAssetAtPath<Material>(Inf + "Materials/Lava.mat") != null && AssetDatabase.LoadAssetAtPath<GameObject>(Inf + "Prefabs/Rocks/RockMid_001.prefab") != null; }

        class LavaMats { public Material lava, ashWall, smoke, ember, glow, sky; public VolumeProfile post; }
        static LavaMats LM;

        // the lava's palette: the pack's own three colours, pushed hotter so it glows against the dark rock (the pack's are 0.54 / 0.19 / 0.13, 0.68 / 0.30 / 0.11, 0.86 / 0.52 / 0.16)
        static readonly Color LavaA = new Color(0.62f, 0.14f, 0.05f), LavaB = new Color(0.95f, 0.36f, 0.06f), LavaC = new Color(1f, 0.74f, 0.18f);

        static LavaMats CreateLavaMaterials(Mats M)
        {
            var L = new LavaMats();
            var pack = AssetDatabase.LoadAssetAtPath<Material>(Inf + "Materials/Lava.mat");
            string lavaPath = Gen + "/Materials/Lava.mat";
            var lava = AssetDatabase.LoadAssetAtPath<Material>(lavaPath);
            if (lava == null) { lava = new Material(pack); AssetDatabase.CreateAsset(lava, lavaPath); }
            lava.shader = pack.shader;
            lava.CopyPropertiesFromMaterial(pack);
            lava.SetColor("_Color_A", LavaA); lava.SetColor("_Color_B", LavaB); lava.SetColor("_Color_C", LavaC);
            EditorUtility.SetDirty(lava);
            L.lava = lava;
            // the smoke bank the world ends in: the same ragged-edged wall as the sea's cloud bank, tinted dark volcanic brown with a rust glow
            L.ashWall = Mat("AshWall", "SkySquad/CloudWall", new Color(0.50f, 0.22f, 0.13f, 1f), m => m.SetTexture("_MainTex", CloudWallTexture()));
            // near smoke puffs drifting past (the sea's near clouds, dark and warm)
            L.smoke = Transparent("AshSmoke", new Color(0.20f, 0.11f, 0.09f, 0.60f)); L.smoke.SetTexture("_BaseMap", CloudTexture());
            L.ember = Particle("Ember", Color.white, true); L.ember.SetTexture("_BaseMap", SoftTexture());
            L.glow = Particle("LavaGlow", new Color(1f, 0.42f, 0.08f, 0.55f), true); L.glow.SetTexture("_BaseMap", SoftTexture());
            // the sky: the pack's own red-orange cubemap skybox, copied so its exposure can be set here
            string skyPath = Gen + "/Materials/SkyboxLava.mat";
            var packSky = AssetDatabase.LoadAssetAtPath<Material>(Inf + "Skyboxes/Skybox_1.mat");
            if (packSky != null)
            {
                var sky = AssetDatabase.LoadAssetAtPath<Material>(skyPath);
                if (sky == null) { sky = new Material(packSky); AssetDatabase.CreateAsset(sky, skyPath); }
                sky.shader = packSky.shader; sky.CopyPropertiesFromMaterial(packSky);
                if (sky.HasProperty("_Exposure")) sky.SetFloat("_Exposure", 1.0f);
                if (sky.HasProperty("_Tint")) sky.SetColor("_Tint", new Color(0.55f, 0.50f, 0.50f, 1f));
                EditorUtility.SetDirty(sky);
                L.sky = sky;
            }
            // post: more bloom for the glow, a warm grade, a heavier vignette
            string profilePath = Gen + "/Data/PostFX_Lava.asset";
            var profile = AssetDatabase.LoadAssetAtPath<VolumeProfile>(profilePath);
            if (profile == null) { profile = ScriptableObject.CreateInstance<VolumeProfile>(); AssetDatabase.CreateAsset(profile, profilePath); }
            T Fx<T>() where T : VolumeComponent
            {
                if (profile.TryGet(out T have)) return have;
                var c = profile.Add<T>(true); c.hideFlags = HideFlags.HideInHierarchy; AssetDatabase.AddObjectToAsset(c, profile); return c;
            }
            var bloom = Fx<Bloom>(); bloom.threshold.Override(0.95f); bloom.intensity.Override(0.9f); bloom.scatter.Override(0.7f);
            var tone = Fx<Tonemapping>(); tone.mode.Override(TonemappingMode.Neutral);
            var vig = Fx<Vignette>(); vig.intensity.Override(0.36f); vig.smoothness.Override(0.5f); vig.color.Override(new Color(0.12f, 0.02f, 0f));
            var grade = Fx<ColorAdjustments>(); grade.saturation.Override(10f); grade.contrast.Override(14f); grade.postExposure.Override(0.05f); grade.colorFilter.Override(new Color(1f, 0.93f, 0.86f));
            EditorUtility.SetDirty(profile);
            L.post = profile;
            return L;
        }

        struct RockSpec { public string path; public float height; public float yaw; public RockSpec(string p, float h, float y = -1f) { path = p; height = h; yaw = y; } }

        /// <summary>The whole lava world as one scene root: the lava (a dense grid near the camera and a far plane, the pack's Lava shader), the shore
        /// of rock, horn and column that scrolls past on both sides, glow pools round their feet, the volcano range and the statue far behind, the
        /// smoke bank the world ends in, drifting ash, and embers rising through all of it. Returns the root (off by WorldManager when world 1 is on).</summary>
        static GameObject BuildLavaWorld(Mats M, Meshes X, Defs D)
        {
            var root = new GameObject("LavaWorld");
            var sc = root.AddComponent<WorldScroller>();
            var L = LM;

            // --- the surface
            var lava = MeshObj("Lava", X.sea, root.transform, L.lava); lava.transform.localPosition = new Vector3(0f, SeaLevel, 0f);
            var lr = lava.GetComponent<MeshRenderer>(); lr.shadowCastingMode = ShadowCastingMode.Off; lr.receiveShadows = false;
            var far = GameObject.CreatePrimitive(PrimitiveType.Plane); UnityEngine.Object.DestroyImmediate(far.GetComponent<Collider>());
            far.name = "LavaFar"; far.transform.SetParent(root.transform, false); far.transform.position = new Vector3(0f, SeaLevel - 1f, 120f); far.transform.localScale = new Vector3(120f, 1f, 120f);
            var fr = far.GetComponent<MeshRenderer>(); fr.sharedMaterial = L.lava; fr.shadowCastingMode = ShadowCastingMode.Off; fr.receiveShadows = false;
            sc.lava = L.lava; sc.lavaRenderers = new Renderer[] { lr, fr };

            var rnd = new System.Random(11);

            // --- the shore: rock, horn, column and spike rising out of the lava on both sides of the lane, scrolling past with the world
            var near = new[] {   // small and mid pieces close to the lane (x 8.5 .. 14)
                new RockSpec("Rocks/RockSmall_001", 2.6f), new RockSpec("Rocks/RockSmall_002", 1.8f), new RockSpec("Rocks/RockMid_003", 4.5f), new RockSpec("Rocks/RockMid_004", 2.4f),
                new RockSpec("Rocks/Stone_006", 0.9f), new RockSpec("Rocks/Stone_005", 0.8f), new RockSpec("Props/Spike_001", 2.2f), new RockSpec("Decorations/Bone_004", 5.5f), new RockSpec("Decorations/Mound_005", 1.6f),
                new RockSpec("Decorations/ColumnBigBroken_001", 3.6f), new RockSpec("Props/Brazier_002", 2.4f) };
            var mid = new[] {    // taller pieces further out (x 15 .. 28)
                new RockSpec("Rocks/RockMid_001", 6f), new RockSpec("Rocks/RockMid_002", 9f), new RockSpec("Rocks/Crag_001", 8f), new RockSpec("Decorations/Bone_003", 9f), new RockSpec("Decorations/Bone_006", 8f),
                new RockSpec("Decorations/ColumnBig_001", 8f), new RockSpec("Decorations/PedestalBig_001", 4.5f), new RockSpec("Rocks/Crag_003", 14f), new RockSpec("Decorations/CirclePlatformSmall_001", 2.4f) };
            var far2 = new[] {   // the big spires standing back from the shore (x 30 .. 60)
                new RockSpec("Rocks/RockBig_001", 28f), new RockSpec("Rocks/RockBig_003", 22f), new RockSpec("Rocks/RockBig_004", 30f), new RockSpec("Rocks/Crag_003", 24f), new RockSpec("Buildings/TowerBig_001", 30f), new RockSpec("Rocks/RockBig_001", 20f) };
            int count = 0;
            for (float z = -22f; z < 200f; z += 5.2f)
            {
                for (int side = -1; side <= 1; side += 2)
                {
                    float roll = (float)rnd.NextDouble();
                    RockSpec[] set; float x0, x1;
                    if (roll < 0.52f) { set = near; x0 = 8.5f; x1 = 14f; }
                    else if (roll < 0.86f) { set = mid; x0 = 15f; x1 = 28f; }
                    else { set = far2; x0 = 32f; x1 = 58f; }
                    var spec = set[rnd.Next(set.Length)];
                    var prefab = InfPrefab(spec.path); if (prefab == null) continue;
                    float x = side * Mathf.Lerp(x0, x1, (float)rnd.NextDouble());
                    var p = new GameObject("Shore" + count++); p.transform.SetParent(root.transform, false);   // unit scale: WorldScroller scales this by the line things come out of
                    p.transform.position = new Vector3(x, SeaLevel - 0.35f, z + (float)rnd.NextDouble() * 4f);
                    var inst = (GameObject)PrefabUtility.InstantiatePrefab(prefab); inst.transform.SetParent(p.transform, false);
                    var mr = inst.GetComponentInChildren<MeshFilter>();
                    float h = mr != null && mr.sharedMesh != null ? mr.sharedMesh.bounds.size.y : 1f;
                    float k = spec.height * (0.85f + 0.35f * (float)rnd.NextDouble()) / Mathf.Max(0.01f, h);
                    inst.transform.localScale = Vector3.one * k;
                    inst.transform.localRotation = Quaternion.Euler(0f, rnd.Next(360), 0f);
                    // rest the piece on the lava: its mesh bottom sits at the waterline minus a little (the pivots are not all at the base)
                    if (mr != null && mr.sharedMesh != null) inst.transform.localPosition = new Vector3(0f, -mr.sharedMesh.bounds.min.y * k, 0f);
                    foreach (var r in inst.GetComponentsInChildren<Renderer>()) { r.shadowCastingMode = ShadowCastingMode.Off; r.receiveShadows = false; }
                    // the lava glows round its foot: a soft orange pool lying on the surface
                    var gl = GameObject.CreatePrimitive(PrimitiveType.Quad); UnityEngine.Object.DestroyImmediate(gl.GetComponent<Collider>());
                    gl.name = "Glow"; gl.transform.SetParent(p.transform, false); gl.transform.localPosition = new Vector3(0f, 0.38f, 0f); gl.transform.localRotation = Quaternion.Euler(90f, 0f, 0f);
                    float footprint = mr != null && mr.sharedMesh != null ? Mathf.Max(mr.sharedMesh.bounds.size.x, mr.sharedMesh.bounds.size.z) * k : 4f;
                    gl.transform.localScale = new Vector3(footprint * 1.9f, footprint * 1.9f, 1f);
                    var gr = gl.GetComponent<MeshRenderer>(); gr.sharedMaterial = L.glow; gr.shadowCastingMode = ShadowCastingMode.Off; gr.receiveShadows = false;
                    sc.buoys.Add(p.transform);
                }
            }
            sc.recycleBehind = -26f; sc.recycleAhead = 226f;   // the shore loops over 226 + 26 units: longer than the 220 of the buoys, so the rocks thin out toward the back

            // --- the volcano range: the pack's cliffs and the great statue stand far back, drifting at a fraction of the speed (like the clouds), under the fog
            var ridge = new GameObject("Ridge"); ridge.transform.SetParent(root.transform, false);
            var cliffs = new[] { new object[] { "Mountains/Cliff_003", -150f, 0.55f, 330f, 20f }, new object[] { "Mountains/Cliff_004", 130f, 0.6f, 350f, 200f }, new object[] { "Mountains/Cliff_005", -10f, 0.7f, 420f, 300f },
                                 new object[] { "Mountains/Cliff_004", -260f, 0.5f, 380f, 140f }, new object[] { "Mountains/Cliff_003", 250f, 0.55f, 390f, 60f } };
            foreach (var c in cliffs)
            {
                var prefab = InfPrefab((string)c[0]); if (prefab == null) continue;
                var inst = (GameObject)PrefabUtility.InstantiatePrefab(prefab); inst.transform.SetParent(ridge.transform, false);
                inst.transform.position = new Vector3((float)c[1], SeaLevel - 6f, (float)c[3]);
                inst.transform.localScale = Vector3.one * (float)c[2];
                inst.transform.localRotation = Quaternion.Euler(0f, (float)c[4], 0f);
                foreach (var r in inst.GetComponentsInChildren<Renderer>()) { r.shadowCastingMode = ShadowCastingMode.Off; r.receiveShadows = false; }
            }
            var statue = InfPrefab("Statues/StatueKnight_002");
            if (statue != null)
            {   // the guardian of the volcano, to the left of the lane's axis and well back, on a rock of his own
                var inst = (GameObject)PrefabUtility.InstantiatePrefab(statue); inst.transform.SetParent(ridge.transform, false);
                inst.transform.position = new Vector3(-62f, SeaLevel - 1f, 235f); inst.transform.localScale = Vector3.one * 2.4f; inst.transform.localRotation = Quaternion.Euler(0f, 160f, 0f);
                foreach (var r in inst.GetComponentsInChildren<Renderer>()) { r.shadowCastingMode = ShadowCastingMode.Off; r.receiveShadows = false; }
            }

            // --- the smoke bank the world ends in (the sea's cloud bank, dark and rust-lit) and the drifting ash in front of it
            {
                float wallZ = D.config.appearZ + D.config.appearRange + 8f;
                var wallMesh = MeshFactory.Panel(70f, 27f); wallMesh.name = "CloudWall";
                var wall = MeshObj("AshWall", SaveMesh(wallMesh), root.transform, L.ashWall);
                wall.transform.position = new Vector3(0f, SeaLevel - 4f, wallZ);
                var wrr = wall.GetComponent<MeshRenderer>(); wrr.shadowCastingMode = ShadowCastingMode.Off; wrr.receiveShadows = false;
            }
            for (int i = 0; i < 9; i++)
            {
                var cluster = new GameObject("Ash" + i); cluster.transform.SetParent(root.transform, false);
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
                    var qr = q.GetComponent<MeshRenderer>(); qr.sharedMaterial = L.smoke; qr.shadowCastingMode = ShadowCastingMode.Off;
                }
                sc.clouds.Add(cluster.transform);
            }

            // --- embers: sparks rising from the lava, streaming back past the camera with the world
            {
                var go = new GameObject("Embers"); go.transform.SetParent(root.transform, false); go.transform.position = new Vector3(0f, SeaLevel + 3f, 62f);
                var ps = go.AddComponent<ParticleSystem>();
                var main = ps.main; main.loop = true; main.playOnAwake = true; main.simulationSpace = ParticleSystemSimulationSpace.World; main.maxParticles = 320; main.prewarm = true;
                main.startLifetime = new ParticleSystem.MinMaxCurve(5f, 9f); main.startSpeed = 0f;
                main.startSize = new ParticleSystem.MinMaxCurve(0.07f, 0.22f);
                main.startColor = new ParticleSystem.MinMaxGradient(new Color(1f, 0.55f, 0.12f, 1f), new Color(1f, 0.85f, 0.35f, 1f));
                main.gravityModifier = 0f;
                var em = ps.emission; em.rateOverTime = 34f;
                var sh = ps.shape; sh.shapeType = ParticleSystemShapeType.Box; sh.scale = new Vector3(60f, 10f, 100f);
                var vel = ps.velocityOverLifetime; vel.enabled = true; vel.space = ParticleSystemSimulationSpace.World;
                vel.x = new ParticleSystem.MinMaxCurve(-0.8f, 0.8f); vel.y = new ParticleSystem.MinMaxCurve(0.8f, 2.4f); vel.z = new ParticleSystem.MinMaxCurve(-10f, -7f);
                var col = ps.colorOverLifetime; col.enabled = true;
                var g = new Gradient(); g.SetKeys(new[] { new GradientColorKey(Color.white, 0f), new GradientColorKey(new Color(1f, 0.5f, 0.2f), 1f) }, new[] { new GradientAlphaKey(0f, 0f), new GradientAlphaKey(1f, 0.12f), new GradientAlphaKey(0.8f, 0.7f), new GradientAlphaKey(0f, 1f) });
                col.color = g;
                var noise = ps.noise; noise.enabled = true; noise.strength = 0.6f; noise.frequency = 0.25f;
                var pr = go.GetComponent<ParticleSystemRenderer>(); pr.sharedMaterial = L.ember; pr.shadowCastingMode = ShadowCastingMode.Off; pr.renderMode = ParticleSystemRenderMode.Billboard;
            }
            return root;
        }

        /// <summary>World 2's entry: its scene root, sky, light, fog, post, and (until its own cast is built) the cast of world 1.</summary>
        static WorldEntry LavaEntry(GameObject lavaRoot, WorldEntry sea, Prefabs P, Mats M, Meshes X)
        {
            var L = LM;
            var bosses = BuildLavaBosses(M);                 // thirty prefabs, each with an Enemy on it
            var fighter = BuildLavaFighter(M, X);            // the lava gunship
            var crate = BuildLavaBreakable(M, X);            // a chest on a basalt slab
            var splash = BuildLavaSplash(M);
            var e = new WorldEntry
            {
                id = "lava", displayName = "INFERNO", tagline = "Lava sea  -  fire bosses",
                thumbnail = WorldSprite("world_lava.png", new Color(0.8f, 0.25f, 0.05f)), accent = new Color(1f, 0.45f, 0.1f),
                environment = new[] { lavaRoot }, skybox = L.sky, skyRotation = 0f,
                sunColor = new Color(1f, 0.66f, 0.40f), sunIntensity = 1.6f, sunEuler = new Vector3(40f, -28f, 0f), sunShadow = 0.5f,
                fog = true, fogColor = new Color(0.62f, 0.23f, 0.10f), fogStart = 105f, fogEnd = 250f,
                ambientFromSky = false, ambientSky = new Color(0.62f, 0.34f, 0.28f), ambientEquator = new Color(0.50f, 0.24f, 0.15f), ambientGround = new Color(1f, 0.38f, 0.10f), ambientIntensity = 1.15f,
                post = L.post,
                fighterPrefab = fighter != null ? fighter : sea.fighterPrefab, bossPrefabs = bosses, bossPrefabByNumber = bosses, bossAttacks = LavaAttacks(), bossAttacks2 = LavaAttacks2(), bossNames = LavaBossNames, bossColors = null, stageNames = LavaStageNames,
                bossHpMul = 1.35f, breakablePrefab = crate != null ? crate : sea.breakablePrefab, splashPrefab = splash != null ? splash : sea.splashPrefab, surfaceRing = new Color(1f, 0.55f, 0.15f)
            };
            return e;
        }
    }
}
