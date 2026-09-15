// SceneBuilder.cs (Editor only)
// Builds the whole playable project from code: materials, placeholder meshes, prefabs,
// the data assets, the main scene with camera/lights/water/HUD, and player settings.
// Menu: Sky Squad > Build Everything. Command line:
//   Unity.exe -batchmode -projectPath <proj> -executeMethod SkySquad.EditorTools.SceneBuilder.BuildAll -quit
// Re-running is safe: assets are overwritten in place.
using System;
using System.Collections.Generic;
using System.IO;
using TMPro;
using UnityEditor;
using UnityEditor.Build;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;
using UnityEngine.SceneManagement;
using UnityEngine.UI;

namespace SkySquad.EditorTools
{
    public static class SceneBuilder
    {
        const string Root = "Assets/_Game";
        const string Gen = Root + "/Generated";
        static readonly Color Navy = new Color(0.04f, 0.14f, 0.31f);
        static readonly Color Gold = new Color(1f, 0.82f, 0.25f);
        static readonly Color Red = new Color(1f, 0.23f, 0.31f);
        static readonly Color Blue = new Color(0.37f, 0.69f, 1f);

        class Mats { public Material planeBody, planeBody2, planeAccent, glass, leader, attackerBody, attackerAccent, jetBody, jetAccent, jetGlow, enemyBody, enemyAccent, enemyGlass, bomberBody, bomberAccent, zepBody, zepAccent, zepPlate, crate, crateBand, canopy, outline, bomberGlow, bullet, water, cloud, buoy, buoyPole, tracer, particle, smoke, shieldBubble, barBg, barHp, barTimer, flash, prop, rocketBody, rocketFin, coin, stopLine; }
        class Meshes { public Mesh fighter, attacker, jet, prop, enemy, zeppelin, crate, rocket, buoy, bullet, coin; }
        class Prefabs { public GameObject planeFighter, planeAttacker, planeJet, enemyFighter, miniBoss, breakable, bullet, boss, explosion, sparks, floatText, ring, rocket, coin; }
        class Defs { public GameConfig config; public WeaponDef gatling, rockets, laser; public EnemyKindDef fighter, miniBoss; }
        static TMP_FontAsset font; static Material fontOutline, fontOutlineSmall;

        [MenuItem("Sky Squad/1. Prepare (import TMP resources)")]
        public static void Prepare()
        {
            if (TMP_Settings.instance != null) { Debug.Log("[SkySquad] TMP resources already present"); return; }
            Type t = null;
            foreach (var asm in AppDomain.CurrentDomain.GetAssemblies())
            {
                try { foreach (var ty in asm.GetTypes()) if (ty.Name == "TMP_PackageResourceImporter") { t = ty; break; } } catch { }
                if (t != null) break;
            }
            if (t == null) { Debug.LogError("[SkySquad] TMP_PackageResourceImporter not found"); EditorApplication.Exit(3); return; }
            var m = t.GetMethod("ImportResources", System.Reflection.BindingFlags.Static | System.Reflection.BindingFlags.Public);
            m.Invoke(null, new object[] { true, false, false });
            AssetDatabase.SaveAssets();
            AssetDatabase.Refresh();
            Debug.Log("[SkySquad] TMP essential resources imported");
        }

        [MenuItem("Sky Squad/2. Build Everything")]
        public static void BuildAll()
        {
            if (TMP_Settings.instance == null) { Debug.LogError("[SkySquad] TMP essentials missing: run Prepare first"); EditorApplication.Exit(2); return; }
            foreach (var d in new[] { Gen, Gen + "/Materials", Gen + "/Meshes", Gen + "/Prefabs", Gen + "/Data", Gen + "/Textures", Root + "/Scenes", Gen + "/Fonts" })
                if (!AssetDatabase.IsValidFolder(d)) { var parent = Path.GetDirectoryName(d).Replace('\\', '/'); AssetDatabase.CreateFolder(parent, Path.GetFileName(d)); }
            CreateFont();
            foreach (var stale in new[] {   // assets from older designs (gates, hordes, blimps)
                Gen + "/Prefabs/Gate.prefab", Gen + "/Prefabs/Horde.prefab", Gen + "/Prefabs/Drone.prefab", Gen + "/Prefabs/Bomber.prefab",
                Gen + "/Data/Horde_Fighter.asset", Gen + "/Data/Horde_Drone.asset", Gen + "/Data/Horde_Bomber.asset",
                Gen + "/Meshes/Blimp.asset", Gen + "/Meshes/GateFrame.asset", Gen + "/Meshes/GatePanel.asset", Gen + "/Meshes/Drone.asset",
                Gen + "/Materials/CargoBody.mat", Gen + "/Materials/CargoAccent.mat", Gen + "/Materials/GateFrame.mat", Gen + "/Materials/GatePanel.mat",
                Gen + "/Materials/DroneBody.mat", Gen + "/Materials/DroneAccent.mat", Gen + "/Materials/DroneEye.mat" })
                if (File.Exists(stale)) AssetDatabase.DeleteAsset(stale);   // File.Exists: a data asset whose script is gone loads as null
            var mats = CreateMaterials();
            var meshes = CreateMeshes();
            var prefabs = CreatePrefabs(mats, meshes);
            var defs = CreateDefinitions(prefabs);
            BuildScene(mats, meshes, prefabs, defs);
            ApplyPlayerSettings();
            AssetDatabase.SaveAssets();
            AssetDatabase.Refresh();
            Debug.Log("[SkySquad] BUILD COMPLETE");
        }

        // ---------------------------------------------------------------- font
        static void CreateFont()
        {
            string path = Gen + "/Fonts/LilitaOne SDF.asset";
            font = AssetDatabase.LoadAssetAtPath<TMP_FontAsset>(path);
            if (font == null)
            {
                try
                {
                    var ttf = AssetDatabase.LoadAssetAtPath<Font>(Root + "/Fonts/LilitaOne-Regular.ttf");
                    if (ttf != null)
                    {
                        var fa = TMP_FontAsset.CreateFontAsset(ttf, 90, 9, UnityEngine.TextCore.LowLevel.GlyphRenderMode.SDFAA, 1024, 1024, AtlasPopulationMode.Dynamic, true);
                        fa.name = "LilitaOne SDF";
                        AssetDatabase.CreateAsset(fa, path);
                        fa.material.name = "LilitaOne SDF Material";
                        AssetDatabase.AddObjectToAsset(fa.material, fa);
                        fa.atlasTexture.name = "LilitaOne SDF Atlas";
                        AssetDatabase.AddObjectToAsset(fa.atlasTexture, fa);
                        AssetDatabase.SaveAssets();
                        font = AssetDatabase.LoadAssetAtPath<TMP_FontAsset>(path);
                    }
                }
                catch (Exception e) { Debug.LogWarning("[SkySquad] font asset creation failed, using default: " + e.Message); }
            }
            if (font == null) font = TMP_Settings.defaultFontAsset;
            fontOutline = FontPreset("LilitaOne Outline", 0.25f, Navy);
            fontOutlineSmall = FontPreset("LilitaOne Outline Thin", 0.15f, Navy);
        }

        static Material FontPreset(string name, float width, Color c)
        {
            string path = Gen + "/Fonts/" + name + ".mat";
            var m = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (m == null) { m = new Material(font.material); AssetDatabase.CreateAsset(m, path); }
            m.shader = font.material.shader;
            m.CopyPropertiesFromMaterial(font.material);
            m.SetFloat(ShaderUtilities.ID_OutlineWidth, width);
            m.SetColor(ShaderUtilities.ID_OutlineColor, c);
            m.SetFloat(ShaderUtilities.ID_FaceDilate, 0.05f);
            m.EnableKeyword("OUTLINE_ON");
            EditorUtility.SetDirty(m);
            return m;
        }

        // ----------------------------------------------------------- materials
        static Material Mat(string name, string shader, Color c, Action<Material> tweak = null)
        {
            string path = Gen + "/Materials/" + name + ".mat";
            var m = AssetDatabase.LoadAssetAtPath<Material>(path);
            var sh = Shader.Find(shader);
            if (sh == null) throw new Exception("shader not found: " + shader);
            if (m == null) { m = new Material(sh); AssetDatabase.CreateAsset(m, path); } else m.shader = sh;
            if (m.HasProperty("_BaseColor")) m.SetColor("_BaseColor", c);
            if (m.HasProperty("_Color")) m.SetColor("_Color", c);
            if (m.HasProperty("_Smoothness")) m.SetFloat("_Smoothness", 0.35f);
            if (m.HasProperty("_Metallic")) m.SetFloat("_Metallic", 0f);
            tweak?.Invoke(m);
            EditorUtility.SetDirty(m);
            return m;
        }
        static Material Lit(string n, Color c, float smooth = 0.35f) => Mat(n, "Universal Render Pipeline/Lit", c, m => m.SetFloat("_Smoothness", smooth));
        static Material Unlit(string n, Color c) => Mat(n, "Universal Render Pipeline/Unlit", c);
        static void MakeTransparent(Material m, bool additive)
        {
            m.SetFloat("_Surface", 1f);
            m.SetFloat("_Blend", additive ? 2f : 0f);
            m.SetFloat("_SrcBlend", (float)(additive ? BlendMode.One : BlendMode.SrcAlpha));
            m.SetFloat("_DstBlend", (float)(additive ? BlendMode.One : BlendMode.OneMinusSrcAlpha));
            m.SetFloat("_ZWrite", 0f);
            m.SetOverrideTag("RenderType", "Transparent");
            m.EnableKeyword("_SURFACE_TYPE_TRANSPARENT");
            m.renderQueue = (int)RenderQueue.Transparent;
        }
        static Material Transparent(string n, Color c, bool additive = false) => Mat(n, "Universal Render Pipeline/Unlit", c, m => MakeTransparent(m, additive));
        static Material Particle(string n, Color c, bool additive) => Mat(n, "Universal Render Pipeline/Particles/Unlit", c, m => MakeTransparent(m, additive));

        static Mats CreateMaterials()
        {
            var M = new Mats();
            M.planeBody = Lit("PlaneBody", new Color(0.96f, 0.97f, 1f));
            M.planeBody2 = Lit("PlaneBody2", new Color(0.79f, 0.85f, 0.93f));
            M.planeAccent = Lit("PlaneAccent", new Color(0.18f, 0.48f, 1f));
            M.glass = Lit("Canopy", new Color(0.12f, 0.23f, 0.43f), 0.9f);
            M.leader = Lit("LeaderGold", new Color(1f, 0.85f, 0.35f), 0.5f);
            M.attackerBody = Lit("AttackerBody", new Color(0.62f, 0.75f, 0.35f));
            M.attackerAccent = Lit("AttackerAccent", Gold);
            M.jetBody = Lit("JetBody", new Color(0.9f, 0.93f, 0.96f), 0.6f);
            M.jetAccent = Lit("JetAccent", new Color(0.5f, 0.95f, 1f));
            M.jetGlow = Unlit("JetGlow", new Color(0.5f, 0.95f, 1f));
            M.enemyBody = Lit("EnemyBody", new Color(0.96f, 0.24f, 0.2f), 0.45f);     // bright, so they read against the sky
            M.enemyAccent = Lit("EnemyAccent", new Color(1f, 0.86f, 0.3f));
            M.enemyGlass = Lit("EnemyGlass", new Color(0.12f, 0.1f, 0.2f), 0.85f);
            M.bomberBody = Lit("BomberBody", new Color(0.23f, 0.25f, 0.3f));
            M.bomberAccent = Lit("BomberAccent", new Color(1f, 0.62f, 0.1f));
            M.zepBody = Lit("ZepBody", new Color(0.69f, 0.16f, 0.23f), 0.45f);
            M.zepAccent = Lit("ZepAccent", new Color(0.17f, 0.17f, 0.23f));
            M.zepPlate = Lit("ZepPlate", new Color(0.96f, 0.96f, 0.96f));
            M.crate = Lit("Crate", new Color(0.72f, 0.5f, 0.27f));
            M.crateBand = Lit("CrateBand", new Color(0.36f, 0.24f, 0.13f));
            M.canopy = Lit("ChuteCanopy", Color.white, 0.2f);
            M.outline = Mat("Outline", "Universal Render Pipeline/Unlit", new Color(0.05f, 0.05f, 0.08f), m => m.SetFloat("_Cull", 1f)); // inside-out hull = toon outline
            M.bomberGlow = Unlit("BomberGlow", Red);
            M.bullet = Unlit("Bullet", Color.white);   // tinted per shot with a property block
            M.coin = Lit("Coin", new Color(1f, 0.85f, 0.3f), 0.75f);
            M.stopLine = Transparent("StopLine", new Color(1f, 0.25f, 0.3f, 0.6f));   // StopLine pulses the alpha
            M.water = Lit("Water", new Color(0.08f, 0.5f, 0.78f), 0.8f);
            M.water.SetTexture("_BaseMap", WaterTexture()); M.water.SetTextureScale("_BaseMap", new Vector2(150f, 150f));
            M.cloud = Transparent("Cloud", Color.white); M.cloud.SetTexture("_BaseMap", CloudTexture());
            M.buoy = Lit("Buoy", new Color(1f, 0.54f, 0.24f));
            M.buoyPole = Lit("BuoyPole", Color.white);
            M.tracer = Particle("Tracer", Color.white, true);
            var soft = SoftTexture();
            M.particle = Particle("ParticleAdd", Color.white, true); M.particle.SetTexture("_BaseMap", soft);
            M.smoke = Particle("Smoke", new Color(0.35f, 0.35f, 0.4f, 0.6f), false); M.smoke.SetTexture("_BaseMap", soft);
            M.shieldBubble = Transparent("ShieldBubble", new Color(0.58f, 0.77f, 0.99f, 0.28f));
            M.barBg = Unlit("BarBg", new Color(0.29f, 0.06f, 0.09f));
            M.barHp = Unlit("BarHp", Red);
            M.barTimer = Unlit("BarTimer", Color.white);
            M.flash = Transparent("MuzzleFlash", new Color(1f, 0.9f, 0.4f, 0.9f), true);
            M.prop = Lit("Propeller", new Color(0.15f, 0.15f, 0.18f));
            M.rocketBody = Lit("RocketBody", new Color(0.9f, 0.91f, 0.93f));
            M.rocketFin = Lit("RocketFin", Red);
            return M;
        }

        static Texture2D SaveTex(Texture2D t, string name)
        {
            string path = Gen + "/Textures/" + name + ".png";
            File.WriteAllBytes(path, t.EncodeToPNG());
            AssetDatabase.ImportAsset(path);
            var imp = AssetImporter.GetAtPath(path) as TextureImporter;
            if (imp != null) { imp.wrapMode = TextureWrapMode.Repeat; imp.mipmapEnabled = true; imp.alphaIsTransparency = true; imp.SaveAndReimport(); }
            return AssetDatabase.LoadAssetAtPath<Texture2D>(path);
        }
        static Texture2D WaterTexture()
        {
            int n = 128; var t = new Texture2D(n, n, TextureFormat.RGBA32, false);
            for (int y = 0; y < n; y++) for (int x = 0; x < n; x++)
                {
                    float u = x / (float)n * Mathf.PI * 2f, w = y / (float)n * Mathf.PI * 2f;
                    float v = 0.9f + 0.05f * Mathf.Sin(u * 2f + Mathf.Sin(w) * 1.3f) * Mathf.Sin(w * 3f + Mathf.Sin(u * 2f)) + 0.03f * Mathf.Sin(u * 5f + w * 3f);
                    float crest = Mathf.Max(0f, Mathf.Sin(w * 3f + Mathf.Sin(u * 2f) * 1.5f) - 0.94f) * 1.6f;
                    float c = Mathf.Clamp01(v + crest);
                    t.SetPixel(x, y, new Color(c, c, c, 1f));
                }
            t.Apply();
            return SaveTex(t, "WaterTiles");
        }
        static Texture2D SoftTexture()
        {
            int n = 64; var t = new Texture2D(n, n, TextureFormat.RGBA32, false);
            for (int y = 0; y < n; y++) for (int x = 0; x < n; x++)
                {
                    float d = Vector2.Distance(new Vector2(x + 0.5f, y + 0.5f), new Vector2(n / 2f, n / 2f)) / (n / 2f);
                    float a = Mathf.Clamp01(1f - d); a = a * a * (3f - 2f * a);
                    t.SetPixel(x, y, new Color(1f, 1f, 1f, a));
                }
            t.Apply();
            var tex = SaveTex(t, "SoftParticle");
            var imp = AssetImporter.GetAtPath(Gen + "/Textures/SoftParticle.png") as TextureImporter;
            if (imp != null) { imp.wrapMode = TextureWrapMode.Clamp; imp.SaveAndReimport(); }
            return tex;
        }
        static Texture2D CloudTexture()
        {
            int w = 256, h = 128; var t = new Texture2D(w, h, TextureFormat.RGBA32, false);
            var blobs = new[] { new Vector3(70, 60, 42), new Vector3(120, 70, 55), new Vector3(175, 62, 46), new Vector3(100, 45, 36), new Vector3(150, 44, 34) };
            for (int y = 0; y < h; y++) for (int x = 0; x < w; x++)
                {
                    float a = 0f;
                    foreach (var b in blobs) { float d = Vector2.Distance(new Vector2(x, y), new Vector2(b.x, b.y)) / b.z; a = Mathf.Max(a, Mathf.Clamp01(1f - d * d)); }
                    a = Mathf.SmoothStep(0f, 1f, a);
                    t.SetPixel(x, y, new Color(1f, 1f, 1f, a));
                }
            t.Apply();
            return SaveTex(t, "CloudSoft");
        }

        // -------------------------------------------------------------- meshes
        static Mesh SaveMesh(Mesh m)
        {
            string path = Gen + "/Meshes/" + m.name + ".asset";
            var existing = AssetDatabase.LoadAssetAtPath<Mesh>(path);
            if (existing != null)
            {
                existing.Clear();
                existing.SetVertices(m.vertices);
                existing.subMeshCount = m.subMeshCount;
                for (int i = 0; i < m.subMeshCount; i++) existing.SetTriangles(m.GetTriangles(i), i);
                existing.RecalculateNormals(); existing.RecalculateBounds();
                EditorUtility.SetDirty(existing);
                return existing;
            }
            AssetDatabase.CreateAsset(m, path);
            return m;
        }
        static Meshes CreateMeshes()
        {
            return new Meshes
            {
                fighter = SaveMesh(MeshFactory.Plane("fighter")), attacker = SaveMesh(MeshFactory.Plane("attacker")), jet = SaveMesh(MeshFactory.Plane("jet")),
                prop = SaveMesh(MeshFactory.Propeller()), enemy = SaveMesh(MeshFactory.EnemyPlane()), zeppelin = SaveMesh(MeshFactory.Zeppelin()), crate = SaveMesh(MeshFactory.Crate()),
                rocket = SaveMesh(MeshFactory.Rocket()), buoy = SaveMesh(MeshFactory.Buoy()), bullet = SaveMesh(MeshFactory.Bullet()), coin = SaveMesh(MeshFactory.Coin())
            };
        }

        // ------------------------------------------------------------- prefabs
        static GameObject MeshObj(string name, Mesh mesh, Transform parent, params Material[] mats)
        {
            var go = new GameObject(name);
            go.transform.SetParent(parent, false);
            go.AddComponent<MeshFilter>().sharedMesh = mesh;
            var mr = go.AddComponent<MeshRenderer>();
            mr.sharedMaterials = mats;
            mr.shadowCastingMode = ShadowCastingMode.On;   // gameplay objects cast; water, clouds and FX opt out
            mr.receiveShadows = true;
            return go;
        }
        /// <summary>Toon outline: the same mesh, slightly bigger, drawn inside-out in black.</summary>
        static void Outline(GameObject body, Mesh mesh, Material outline, float grow)
        {
            var o = MeshObj("Outline", mesh, body.transform, outline, outline, outline);
            o.transform.localScale = Vector3.one * grow;
            var r = o.GetComponent<MeshRenderer>(); r.shadowCastingMode = ShadowCastingMode.Off; r.receiveShadows = false;
        }
        static TextMeshPro Label3D(string name, Transform parent, Vector3 pos, float size, Color color, Material preset)
        {
            var go = new GameObject(name);
            go.transform.SetParent(parent, false);
            go.transform.localPosition = pos;
            var t = go.AddComponent<TextMeshPro>();
            t.font = font; t.fontSharedMaterial = preset; t.fontSize = size; t.color = color;
            t.alignment = TextAlignmentOptions.Center;
            t.rectTransform.sizeDelta = new Vector2(14f, 3f);
            t.sortingOrder = 10;
            return t;
        }
        static GameObject SavePrefab(GameObject go, string name)
        {
            string path = Gen + "/Prefabs/" + name + ".prefab";
            var p = PrefabUtility.SaveAsPrefabAsset(go, path);
            UnityEngine.Object.DestroyImmediate(go);
            return p;
        }
        static GameObject PlanePrefab(string name, Mesh mesh, Mesh propMesh, Mats M, Material body, Material accent, Material glass, bool prop)
        {
            var root = new GameObject(name);
            root.transform.localScale = Vector3.one * 0.8f;
            var pv = root.AddComponent<PlaneVisual>();
            var bodyGo = MeshObj("Body", mesh, root.transform, body, accent, glass);
            Outline(bodyGo, mesh, M.outline, 1.06f);
            pv.bodyRenderer = bodyGo.GetComponent<Renderer>();
            if (prop) { var p = MeshObj("Propeller", propMesh, root.transform, M.prop); p.transform.localPosition = new Vector3(0f, 0f, 0.58f); pv.propeller = p.transform; }
            var flash = GameObject.CreatePrimitive(PrimitiveType.Quad);
            UnityEngine.Object.DestroyImmediate(flash.GetComponent<Collider>());
            flash.name = "Flash"; flash.transform.SetParent(root.transform, false);
            flash.transform.localPosition = new Vector3(0f, 0.04f, 0.78f); flash.transform.localScale = Vector3.one * 0.35f;
            var fr = flash.GetComponent<MeshRenderer>(); fr.sharedMaterial = M.flash; fr.enabled = false; fr.shadowCastingMode = ShadowCastingMode.Off;
            pv.flashRenderer = fr;
            pv.leaderMaterial = M.leader;
            return SavePrefab(root, name);
        }
        static Mesh GetMesh(string name) => AssetDatabase.LoadAssetAtPath<Mesh>(Gen + "/Meshes/" + name + ".asset");

        static GameObject EnemyPrefab(string name, Mesh mesh, Mesh propMesh, Mats M, bool hpLabel, Material glow, params Material[] mats)
        {
            var root = new GameObject(name);
            var en = root.AddComponent<Enemy>();
            var body = MeshObj("Body", mesh, root.transform, mats);
            body.transform.localRotation = Quaternion.Euler(0f, 180f, 0f); // nose toward the player; EnemyKindDef.scale is applied at runtime
            Outline(body, mesh, M.outline, 1.07f);
            en.model = body.transform;
            en.bodyRenderer = body.GetComponent<Renderer>();
            var prop = MeshObj("Propeller", propMesh, body.transform, M.prop); prop.transform.localPosition = new Vector3(0f, 0f, 0.78f); en.propeller = prop.transform;
            var flash = GameObject.CreatePrimitive(PrimitiveType.Quad); UnityEngine.Object.DestroyImmediate(flash.GetComponent<Collider>());
            flash.name = "Flash"; flash.transform.SetParent(body.transform, false);
            flash.transform.localPosition = new Vector3(0f, -0.05f, 0.95f); flash.transform.localRotation = Quaternion.Euler(0f, 180f, 0f); flash.transform.localScale = Vector3.one * 0.6f;
            var fr = flash.GetComponent<MeshRenderer>(); fr.sharedMaterial = glow != null ? glow : M.flash; fr.enabled = false; fr.shadowCastingMode = ShadowCastingMode.Off;
            en.flashRenderer = fr;
            if (hpLabel) en.hpLabel = Label3D("HpLabel", root.transform, new Vector3(0f, 2.8f, 0f), 10f, Color.white, fontOutline);
            return SavePrefab(root, name);
        }

        static ParticleSystem ParticlePrefab(GameObject go, Material mat, int burst, float speedMin, float speedMax, float sizeMin, float sizeMax, float lifeMin, float lifeMax, Color c0, Color c1, float gravity, bool shrink)
        {
            var ps = go.AddComponent<ParticleSystem>();
            var main = ps.main;
            main.duration = 0.6f; main.loop = false; main.playOnAwake = true;
            main.startLifetime = new ParticleSystem.MinMaxCurve(lifeMin, lifeMax);
            main.startSpeed = new ParticleSystem.MinMaxCurve(speedMin, speedMax);
            main.startSize = new ParticleSystem.MinMaxCurve(sizeMin, sizeMax);
            main.startColor = new ParticleSystem.MinMaxGradient(c0, c1);
            main.gravityModifier = gravity;
            main.simulationSpace = ParticleSystemSimulationSpace.World;
            main.maxParticles = 200;
            var em = ps.emission; em.rateOverTime = 0f; em.SetBursts(new[] { new ParticleSystem.Burst(0f, (short)burst) });
            var sh = ps.shape; sh.shapeType = ParticleSystemShapeType.Sphere; sh.radius = 0.25f;
            var col = ps.colorOverLifetime; col.enabled = true;
            var g = new Gradient();
            g.SetKeys(new[] { new GradientColorKey(Color.white, 0f), new GradientColorKey(Color.white, 1f) }, new[] { new GradientAlphaKey(1f, 0f), new GradientAlphaKey(0.9f, 0.5f), new GradientAlphaKey(0f, 1f) });
            col.color = new ParticleSystem.MinMaxGradient(g);
            if (shrink) { var sz = ps.sizeOverLifetime; sz.enabled = true; sz.size = new ParticleSystem.MinMaxCurve(1f, AnimationCurve.Linear(0f, 1f, 1f, 0.1f)); }
            var r = ps.GetComponent<ParticleSystemRenderer>(); r.sharedMaterial = mat; r.renderMode = ParticleSystemRenderMode.Billboard;
            return ps;
        }

        static Prefabs CreatePrefabs(Mats M, Meshes X)
        {
            var P = new Prefabs();
            P.planeFighter = PlanePrefab("PlaneFighter", X.fighter, X.prop, M, M.planeBody, M.planeAccent, M.glass, true);
            P.planeAttacker = PlanePrefab("PlaneAttacker", X.attacker, X.prop, M, M.attackerBody, M.attackerAccent, M.glass, true);
            P.planeJet = PlanePrefab("PlaneJet", X.jet, X.prop, M, M.jetBody, M.jetAccent, M.jetGlow, false);
            P.enemyFighter = EnemyPrefab("EnemyFighter", X.enemy, X.prop, M, false, null, M.enemyBody, M.enemyAccent, M.enemyGlass);
            P.miniBoss = EnemyPrefab("EnemyMiniBoss", X.enemy, X.prop, M, true, M.bomberGlow, M.bomberBody, M.bomberAccent, M.bomberGlow);

            { // breakable: a supply crate under a parachute; Breakable.Init tints the canopy per kind
                var root = new GameObject("Breakable");
                var bk = root.AddComponent<Breakable>();
                var crate = MeshObj("Crate", X.crate, root.transform, M.crate, M.crateBand, M.canopy);
                crate.transform.localScale = Vector3.one * 1.5f;   // reads at about a quarter of the screen at the front slot
                Outline(crate, X.crate, M.outline, 1.05f);
                bk.model = crate.transform;
                bk.crateRenderer = crate.GetComponent<Renderer>();
                bk.label = Label3D("Label", root.transform, new Vector3(0f, 0.05f, -1.4f), 12f, Color.white, fontOutline);
                bk.hint = Label3D("Hint", root.transform, new Vector3(0f, 1.75f, -1.5f), 4f, Gold, fontOutlineSmall);
                P.breakable = SavePrefab(root, "Breakable");
            }
            { // boss
                var root = new GameObject("Boss");
                var bc = root.AddComponent<BossController>();
                var model = MeshObj("Model", X.zeppelin, root.transform, M.zepBody, M.zepAccent, M.zepPlate);
                model.transform.localRotation = Quaternion.Euler(0f, 180f, 0f); // nose (skull) toward the player
                bc.model = model.transform;
                bc.hpLabel = Label3D("HpLabel", root.transform, new Vector3(0f, 5.4f, -8f), 14f, Color.white, fontOutline);
                float barY = 3.9f, barZ = -8f; bc.hpBarWidth = 8f;
                GameObject Bar(string n, Material m, float y, float h, float w) { var b = GameObject.CreatePrimitive(PrimitiveType.Cube); UnityEngine.Object.DestroyImmediate(b.GetComponent<Collider>()); b.name = n; b.transform.SetParent(root.transform, false); b.transform.localPosition = new Vector3(0f, y, barZ); b.transform.localScale = new Vector3(w, h, 0.1f); var r = b.GetComponent<MeshRenderer>(); r.sharedMaterial = m; r.shadowCastingMode = ShadowCastingMode.Off; return b; }
                Bar("HpBarBg", M.barBg, barY, 0.45f, 8.2f);
                bc.hpBarFill = Bar("HpBarFill", M.barHp, barY, 0.35f, 8f).transform;
                Bar("TimerBg", M.barBg, barY - 0.5f, 0.2f, 8.2f);
                bc.timerBarFill = Bar("TimerFill", M.barTimer, barY - 0.5f, 0.14f, 8f).transform;
                P.boss = SavePrefab(root, "Boss");
            }
            { // explosion: fire burst + smoke child
                var root = new GameObject("Explosion");
                ParticlePrefab(root, M.particle, 40, 5f, 12f, 0.35f, 0.8f, 0.4f, 0.8f, new Color(1f, 0.82f, 0.25f), new Color(1f, 0.42f, 0.17f), 0.6f, true);
                var smoke = new GameObject("Smoke"); smoke.transform.SetParent(root.transform, false);
                var sps = ParticlePrefab(smoke, M.smoke, 10, 1f, 3f, 0.6f, 1.2f, 0.7f, 1.2f, new Color(0.4f, 0.4f, 0.45f, 0.7f), new Color(0.25f, 0.25f, 0.3f, 0.6f), -0.1f, false);
                var ssz = sps.sizeOverLifetime; ssz.enabled = true; ssz.size = new ParticleSystem.MinMaxCurve(1f, AnimationCurve.Linear(0f, 0.6f, 1f, 1.6f));
                P.explosion = SavePrefab(root, "Explosion");
            }
            {
                var root = new GameObject("Sparks");
                var ps = ParticlePrefab(root, M.particle, 0, 3f, 8f, 0.12f, 0.25f, 0.2f, 0.45f, Color.white, Color.white, 0.8f, true);
                var em = ps.emission; em.SetBursts(new ParticleSystem.Burst[0]);
                var main = ps.main; main.playOnAwake = false;
                P.sparks = SavePrefab(root, "Sparks");
            }
            {
                var root = new GameObject("FloatText");
                var t = root.AddComponent<TextMeshPro>();
                t.font = font; t.fontSharedMaterial = fontOutline; t.fontSize = 6f; t.alignment = TextAlignmentOptions.Center; t.rectTransform.sizeDelta = new Vector2(20f, 4f); t.sortingOrder = 20;
                P.floatText = SavePrefab(root, "FloatText");
            }
            {
                var root = new GameObject("Ring");
                var lr = root.AddComponent<LineRenderer>();
                lr.sharedMaterial = M.tracer; lr.positionCount = 33; lr.loop = true; lr.useWorldSpace = true; lr.startWidth = lr.endWidth = 0.12f; lr.shadowCastingMode = ShadowCastingMode.Off;
                P.ring = SavePrefab(root, "Ring");
            }
            {
                var root = new GameObject("Rocket");
                MeshObj("Body", X.rocket, root.transform, M.rocketBody, M.rocketFin);
                var tr = root.AddComponent<TrailRenderer>();
                tr.sharedMaterial = M.smoke; tr.time = 0.35f; tr.startWidth = 0.18f; tr.endWidth = 0.02f; tr.minVertexDistance = 0.1f; tr.shadowCastingMode = ShadowCastingMode.Off;
                P.rocket = SavePrefab(root, "Rocket");
            }
            { // bullet: a glowing slug with a short additive trail; BulletPool tints and steers it
                var root = new GameObject("Bullet");
                var tr = root.AddComponent<TrailRenderer>();
                tr.sharedMaterial = M.tracer; tr.time = 0.22f; tr.startWidth = 0.22f; tr.endWidth = 0.05f; tr.minVertexDistance = 0.05f; tr.shadowCastingMode = ShadowCastingMode.Off;
                var slug = MeshObj("Slug", X.bullet, root.transform, M.bullet);
                var sr = slug.GetComponent<MeshRenderer>(); sr.shadowCastingMode = ShadowCastingMode.Off; sr.receiveShadows = false;
                P.bullet = SavePrefab(root, "Bullet");
            }
            { // coin: a gold disc that pops out of every kill (FXManager.CoinBurst)
                var root = MeshObj("Coin", X.coin, null, M.coin);
                var cr = root.GetComponent<MeshRenderer>(); cr.shadowCastingMode = ShadowCastingMode.Off; cr.receiveShadows = false;
                P.coin = SavePrefab(root, "Coin");
            }
            return P;
        }

        // --------------------------------------------------------------- data
        static T Asset<T>(string name, Action<T> init) where T : ScriptableObject
        {
            string path = Gen + "/Data/" + name + ".asset";
            var a = AssetDatabase.LoadAssetAtPath<T>(path);
            if (a == null) { a = ScriptableObject.CreateInstance<T>(); AssetDatabase.CreateAsset(a, path); }
            init(a);
            EditorUtility.SetDirty(a);
            return a;
        }
        static Defs CreateDefinitions(Prefabs P)
        {
            var D = new Defs();
            D.gatling = Asset<WeaponDef>("Weapon_Gatling", w => { w.id = "gatling"; w.displayName = "GATLING"; w.description = "one bullet per plane"; w.damage = 1f; w.fireInterval = 0.5f; w.projectile = ProjectileKind.Tracer; w.color = new Color(1f, 0.89f, 0.48f); w.planePrefab = P.planeFighter; w.splashRadius = 0f; w.pierce = false; });
            D.rockets = Asset<WeaponDef>("Weapon_Rockets", w => { w.id = "rockets"; w.displayName = "ROCKETS"; w.description = "splash damage"; w.damage = 3f; w.fireInterval = 0.7f; w.projectile = ProjectileKind.Rocket; w.color = new Color(1f, 0.62f, 0.1f); w.planePrefab = P.planeAttacker; w.splashRadius = 2.5f; w.pierce = false; });
            D.laser = Asset<WeaponDef>("Weapon_Laser", w => { w.id = "laser"; w.displayName = "LASER"; w.description = "pierces the column"; w.damage = 1f; w.fireInterval = 0.2f; w.projectile = ProjectileKind.Beam; w.color = new Color(0.5f, 0.95f, 1f); w.planePrefab = P.planeJet; w.splashRadius = 0f; w.pierce = true; });
            D.fighter = Asset<EnemyKindDef>("Enemy_Fighter", e => { e.id = "fighter"; e.displayName = "FIGHTER"; e.hp = 1f; e.halfWidth = 1.0f; e.approachSpeed = -4f; e.fireEvery = 3f; e.shotDamage = 1f; e.coins = 1; e.scale = 1.25f; e.miniBoss = false; e.prefab = P.enemyFighter; e.color = Red; });
            D.miniBoss = Asset<EnemyKindDef>("Enemy_MiniBoss", e => { e.id = "miniboss"; e.displayName = "MINI BOSS"; e.hp = 10f; e.halfWidth = 3.4f; e.approachSpeed = -1f; e.fireEvery = 1.6f; e.shotDamage = 1f; e.coins = 60; e.scale = 3.2f; e.miniBoss = true; e.prefab = P.miniBoss; e.color = new Color(1f, 0.62f, 0.1f); });
            // the asset keeps old values for fields it already had, so every number that matters is set here
            D.config = Asset<GameConfig>("GameConfig", c =>
            {
                c.weapons = new[] { D.gatling, D.rockets, D.laser }; c.enemyFighter = D.fighter; c.enemyMiniBoss = D.miniBoss;
                c.scrollSpeed = 9f; c.laneHalfWidth = 4.2f; c.spawnDistance = 80f;
                c.startCount = 1; c.startCountPerLevel = 0; c.steerSpeed = 8f; c.climbSpeed = 7.5f; c.dragUnitsPerScreen = 18f; c.maxVisiblePlanes = 28;
                c.formationSpacingX = 1.1f; c.formationSpacingZ = 0.9f; c.spiralSpacing = 0.62f; c.lineOfFireRange = 34f; c.pierceHalfWidth = 1.2f;
                c.levelDurationBase = 55f; c.levelDurationPerLevel = 8f;
                c.laneHalfWidthAim = 0.6f; c.swarmRate = 2.5f; c.swarmRatePerHorde = 1.5f; c.swarmXRange = 3.8f; c.swarmAltSpread = 0.8f; c.swarmDepth = 12f; c.followSpeed = 0.6f; c.weave = 0.35f;
                c.diveZ = 7f; c.diveFollow = 3f; c.diveClimb = 8f; c.ramZ = 1.2f; c.ramHitX = 1.4f; c.ramHitPerPlane = 0.08f; c.maxAliveEnemies = 150; c.bossSpawnGap = 3f; c.holdBehindBoss = 4f;
                c.endless = true; c.bulletSpeed = 38f; c.enemyBulletSpeed = 28f; c.bulletHitRadius = 0.55f; c.bulletLife = 1.1f; c.bulletSize = 1.6f; c.hordePlanesBase = 100; c.hordePlanesPerHorde = 100;
                c.enemyStopZ = 12f; c.enemyAltAboveSplit = 1.4f; c.altitudeSplit = 4.4f; c.altitudeMax = 5.85f;   // the ceiling is the crowd's altitude
                c.miniBossHpBase = 280f; c.miniBossHpGrowth = 2.5f; c.miniBossShotPerBoss = 2f;
                c.upgradeCostFire = 50f; c.upgradeCostDamage = 60f; c.upgradeCostRevenue = 40f; c.upgradeCostGrowth = 1.6f; c.fireRatePerLevel = 0.15f; c.damagePerLevel = 0.35f; c.revenuePerLevel = 0.2f;
                c.supplyAlt = 1.5f; c.supplyFrontZ = 17f; c.supplySpacing = 6.5f; c.supplyVisible = 4; c.boxHpBase = 15f; c.boxHpGrowth = 2.2f; c.boxHpPerLevel = 1.15f; c.boxPlanes = 2; c.coinsPerHp = 0.3f; c.weaponAt = -1; c.weaponEvery = 6;   // weapon crates off: fire rate / damage come from the lobby
                c.bossHpPerDps = 2.0f; c.bossHpPerPlane = 0.4f; c.bossFireEvery = 2.2f;
            });
            return D;
        }

        // --------------------------------------------------------------- scene
        static RectTransform UI(string name, Transform parent, Vector2 anchorMin, Vector2 anchorMax, Vector2 pos, Vector2 size)
        {
            var go = new GameObject(name, typeof(RectTransform));
            go.transform.SetParent(parent, false);
            var rt = go.GetComponent<RectTransform>();
            rt.anchorMin = anchorMin; rt.anchorMax = anchorMax; rt.pivot = new Vector2(0.5f, 0.5f);
            rt.anchoredPosition = pos; rt.sizeDelta = size;
            return rt;
        }
        static TextMeshProUGUI UIText(string name, Transform parent, string text, float size, Color color, Vector2 anchor, Vector2 pos, Vector2 boxSize, TextAlignmentOptions align = TextAlignmentOptions.Center, bool thin = false)
        {
            var rt = UI(name, parent, anchor, anchor, pos, boxSize);
            var t = rt.gameObject.AddComponent<TextMeshProUGUI>();
            t.font = font; t.fontSharedMaterial = thin ? fontOutlineSmall : fontOutline; t.text = text; t.fontSize = size; t.color = color; t.alignment = align; t.raycastTarget = false;
            return t;
        }
        static Image UIImage(string name, Transform parent, Color c, Vector2 anchorMin, Vector2 anchorMax, Vector2 pos, Vector2 size)
        {
            var rt = UI(name, parent, anchorMin, anchorMax, pos, size);
            var im = rt.gameObject.AddComponent<Image>(); im.color = c; im.raycastTarget = false;
            return im;
        }
        static GameObject Panel(string name, Transform parent, float alpha)
        {
            var im = UIImage(name, parent, new Color(0.02f, 0.1f, 0.2f, alpha), Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero);
            im.raycastTarget = false;
            return im.gameObject;
        }

        static void BuildScene(Mats M, Meshes X, Prefabs P, Defs D)
        {
            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);

            // camera rig
            var rig = new GameObject("CameraRig"); rig.transform.position = new Vector3(0f, 6.2f, -9.5f);
            var follow = rig.AddComponent<CameraFollow>(); follow.basePosition = rig.transform.position; follow.followAlt = 0.7f;   // climb with the squad so the wall's depth shows when it is up high
            var camGo = new GameObject("Main Camera"); camGo.tag = "MainCamera"; camGo.transform.SetParent(rig.transform, false);
            var cam = camGo.AddComponent<Camera>(); camGo.AddComponent<AudioListener>();
            cam.fieldOfView = 52f; cam.nearClipPlane = 0.3f; cam.farClipPlane = 500f; cam.clearFlags = CameraClearFlags.Skybox;
            var camData = cam.GetUniversalAdditionalCameraData();
            camData.renderPostProcessing = true; camData.antialiasing = AntialiasingMode.FastApproximateAntialiasing;
            camGo.transform.LookAt(new Vector3(0f, 3.6f, 9f));

            // light + sky
            var lightGo = new GameObject("Sun"); var light = lightGo.AddComponent<Light>();
            light.type = LightType.Directional; light.color = new Color(1f, 0.96f, 0.88f); light.intensity = 1.5f; light.shadows = LightShadows.Soft; light.shadowStrength = 0.55f;
            lightGo.transform.rotation = Quaternion.Euler(52f, -28f, 0f);
            var skyPath = Gen + "/Materials/Skybox.mat";
            var sky = AssetDatabase.LoadAssetAtPath<Material>(skyPath);
            if (sky == null) { sky = new Material(Shader.Find("Skybox/Procedural")); AssetDatabase.CreateAsset(sky, skyPath); }
            sky.SetColor("_SkyTint", new Color(0.5f, 0.75f, 1f)); sky.SetColor("_GroundColor", new Color(0.12f, 0.45f, 0.72f)); sky.SetFloat("_Exposure", 1.15f); sky.SetFloat("_SunSize", 0.05f); sky.SetFloat("_AtmosphereThickness", 0.55f);
            EditorUtility.SetDirty(sky);
            RenderSettings.skybox = sky; RenderSettings.sun = light; RenderSettings.ambientMode = AmbientMode.Trilight;
            RenderSettings.ambientSkyColor = new Color(0.6f, 0.78f, 1f); RenderSettings.ambientEquatorColor = new Color(0.45f, 0.6f, 0.8f); RenderSettings.ambientGroundColor = new Color(0.15f, 0.3f, 0.45f);
            RenderSettings.fog = true; RenderSettings.fogMode = FogMode.Linear; RenderSettings.fogStartDistance = 70f; RenderSettings.fogEndDistance = 240f; RenderSettings.fogColor = new Color(0.62f, 0.8f, 0.98f);

            // post: bloom makes tracers and explosions glow, a vignette frames the lane, a touch more colour
            string profilePath = Gen + "/Data/PostFX.asset";
            var profile = AssetDatabase.LoadAssetAtPath<VolumeProfile>(profilePath);
            if (profile == null) { profile = ScriptableObject.CreateInstance<VolumeProfile>(); AssetDatabase.CreateAsset(profile, profilePath); }
            T Fx<T>() where T : VolumeComponent
            {
                if (profile.TryGet(out T have)) return have;
                var c = profile.Add<T>(true); c.hideFlags = HideFlags.HideInHierarchy; AssetDatabase.AddObjectToAsset(c, profile); return c;
            }
            var bloom = Fx<Bloom>(); bloom.threshold.Override(0.85f); bloom.intensity.Override(0.7f); bloom.scatter.Override(0.6f);
            var vignette = Fx<Vignette>(); vignette.intensity.Override(0.28f); vignette.smoothness.Override(0.45f);
            var grade = Fx<ColorAdjustments>(); grade.saturation.Override(12f); grade.contrast.Override(10f); grade.postExposure.Override(0.1f);
            EditorUtility.SetDirty(profile);
            var postGo = new GameObject("PostFX"); var vol = postGo.AddComponent<Volume>(); vol.isGlobal = true; vol.profile = profile;

            // pipeline: anti-aliasing and soft shadows on every URP asset in the project (the "pixly" fix)
            foreach (var guid in AssetDatabase.FindAssets("t:UniversalRenderPipelineAsset", new[] { "Assets" }))   // the project's own, not the package copies
            {
                var urp = AssetDatabase.LoadAssetAtPath<UniversalRenderPipelineAsset>(AssetDatabase.GUIDToAssetPath(guid));
                if (urp == null) continue;
                var so = new SerializedObject(urp);
                SetProp(so, "m_MSAA", 4); SetProp(so, "m_MainLightShadowsSupported", true); SetProp(so, "m_SoftShadowsSupported", true);
                SetProp(so, "m_ShadowDistance", 70f); SetProp(so, "m_MainLightShadowmapResolution", 2048);
                so.ApplyModifiedProperties(); EditorUtility.SetDirty(urp);
            }

            // world
            var worldGo = new GameObject("World"); var world = worldGo.AddComponent<WorldScroller>();
            var water = GameObject.CreatePrimitive(PrimitiveType.Plane); UnityEngine.Object.DestroyImmediate(water.GetComponent<Collider>());
            water.name = "Water"; water.transform.SetParent(worldGo.transform, false); water.transform.position = new Vector3(0f, 0f, 120f); water.transform.localScale = new Vector3(60f, 1f, 60f);
            var wr = water.GetComponent<MeshRenderer>(); wr.sharedMaterial = M.water; wr.shadowCastingMode = ShadowCastingMode.Off; world.water = wr; world.waterTilesPerUnit = 0.1f;
            var rnd = new System.Random(5);
            for (int i = 0; i < 16; i++)
            {
                float side = i % 2 == 0 ? -1f : 1f;
                var b = MeshObj("Buoy" + i, X.buoy, worldGo.transform, M.buoy, M.buoyPole);
                b.transform.position = new Vector3(side * (D.config.laneHalfWidth + 2.0f), 0.15f, -20f + i / 2 * 27.5f);
                world.buoys.Add(b.transform);
            }
            for (int i = 0; i < 9; i++)
            {
                var q = GameObject.CreatePrimitive(PrimitiveType.Quad); UnityEngine.Object.DestroyImmediate(q.GetComponent<Collider>());
                q.name = "Cloud" + i; q.transform.SetParent(worldGo.transform, false);
                q.transform.position = new Vector3((float)(rnd.NextDouble() - 0.5) * 90f, 14f + (float)rnd.NextDouble() * 14f, 30f + i * 22f);
                float s = 10f + (float)rnd.NextDouble() * 12f; q.transform.localScale = new Vector3(s, s * 0.5f, 1f);
                var qr = q.GetComponent<MeshRenderer>(); qr.sharedMaterial = M.cloud; qr.shadowCastingMode = ShadowCastingMode.Off;
                world.clouds.Add(q.transform);
            }

            // cloud rails: puffs along both lane edges at the split altitude mark where the low band ends
            // and the high band begins (a solid deck there would hide the supply lane from the camera)
            for (int i = 0; i < 20; i++)
            {
                float side = i % 2 == 0 ? -1f : 1f;
                var q = GameObject.CreatePrimitive(PrimitiveType.Quad); UnityEngine.Object.DestroyImmediate(q.GetComponent<Collider>());
                q.name = "Rail" + i; q.transform.SetParent(worldGo.transform, false);
                q.transform.position = new Vector3(side * (D.config.laneHalfWidth + 1.8f), 1f + D.config.altitudeSplit, -20f + i / 2 * 22f);
                q.transform.localScale = new Vector3(3.4f, 1.5f, 1f);
                var qr = q.GetComponent<MeshRenderer>(); qr.sharedMaterial = M.cloud; qr.shadowCastingMode = ShadowCastingMode.Off;
                world.buoys.Add(q.transform);
            }

            // the front line: a dashed red line where a boss parks and opens fire (StopLine shows it as he comes)
            {
                var slGo = new GameObject("StopLine"); var sl = slGo.AddComponent<StopLine>();
                int lanes = 7; float dashStep = D.config.swarmXRange * 2f / lanes; var dashes = new Renderer[lanes];
                for (int i = 0; i < lanes; i++)
                {
                    var q = GameObject.CreatePrimitive(PrimitiveType.Quad); UnityEngine.Object.DestroyImmediate(q.GetComponent<Collider>());
                    q.name = "Dash" + i; q.transform.SetParent(slGo.transform, false);
                    float x = (i - (lanes - 1) / 2f) * dashStep;
                    q.transform.position = new Vector3(x, 1f + D.config.altitudeSplit + D.config.enemyAltAboveSplit - 0.55f, D.config.enemyStopZ - 0.9f);
                    q.transform.localScale = new Vector3(dashStep * 0.7f, 0.14f, 1f);
                    var qr = q.GetComponent<MeshRenderer>(); qr.sharedMaterial = M.stopLine; qr.shadowCastingMode = ShadowCastingMode.Off; qr.receiveShadows = false;
                    dashes[i] = qr;
                }
                sl.dashes = dashes;
            }

            // managers
            var gameGo = new GameObject("Game");
            var gm = gameGo.AddComponent<GameManager>();
            var audio = gameGo.AddComponent<AudioManager>();
            var fx = gameGo.AddComponent<FXManager>();
            fx.explosionPrefab = P.explosion; fx.sparksPrefab = P.sparks; fx.floatTextPrefab = P.floatText; fx.ringPrefab = P.ring; fx.coinPrefab = P.coin;

            // squad
            var squadGo = new GameObject("Squad");
            var squad = squadGo.AddComponent<SquadController>();
            var input = squadGo.AddComponent<SquadInput>();
            var fire = squadGo.AddComponent<AutoFire>();
            var tracers = squadGo.AddComponent<TracerPool>(); tracers.material = M.tracer;
            var rockets = squadGo.AddComponent<RocketPool>(); rockets.rocketPrefab = P.rocket;
            var bulletPool = squadGo.AddComponent<BulletPool>(); bulletPool.bulletPrefab = P.bullet;
            var pilot = squadGo.AddComponent<AutoPilot>(); pilot.squad = squad;
            follow.squad = squad;
            var formation = new GameObject("Formation"); formation.transform.SetParent(squadGo.transform, false);
            squad.config = D.config; squad.input = input; squad.formationRoot = formation.transform; squad.leaderMaterial = M.leader;
            // no world-space count over the squad: at this camera angle it lands on top of the supply
            // lane's hp numbers. The plane count lives in the HUD instead (see PlanesBg below).
            var bubble = new GameObject("ShieldBubble"); bubble.transform.SetParent(squadGo.transform, false); bubble.transform.localPosition = new Vector3(0f, 0f, -2.2f);
            var bm = bubble.AddComponent<MeshFilter>(); bm.sharedMesh = BubbleMesh(); var br = bubble.AddComponent<MeshRenderer>(); br.sharedMaterial = M.shieldBubble; br.shadowCastingMode = ShadowCastingMode.Off;
            bubble.SetActive(false); squad.shieldBubble = bubble;
            fire.squad = squad; fire.tracers = tracers; fire.rockets = rockets; fire.bullets = bulletPool;

            var enemiesGo = new GameObject("Enemies"); var enemies = enemiesGo.AddComponent<WaveSpawner>(); enemies.fighterPrefab = P.enemyFighter; enemies.miniBossPrefab = P.miniBoss;
            var supplyGo = new GameObject("Supply"); var supply = supplyGo.AddComponent<SupplyLane>(); supply.breakablePrefab = P.breakable;
            var bossGo = (GameObject)PrefabUtility.InstantiatePrefab(P.boss); bossGo.name = "Boss"; var boss = bossGo.GetComponent<BossController>(); bossGo.SetActive(false);

            // HUD
            var canvasGo = new GameObject("HUD", typeof(Canvas), typeof(CanvasScaler), typeof(GraphicRaycaster));
            var canvas = canvasGo.GetComponent<Canvas>(); canvas.renderMode = RenderMode.ScreenSpaceOverlay;
            var scaler = canvasGo.GetComponent<CanvasScaler>(); scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize; scaler.referenceResolution = new Vector2(540f, 960f); scaler.matchWidthOrHeight = 0.5f;
            var hud = canvasGo.AddComponent<HUD>();
            var flash = UIImage("Flash", canvasGo.transform, new Color(1f, 1f, 1f, 0f), Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero); hud.flashImage = flash;
            var warn = UIImage("Warn", canvasGo.transform, new Color(1f, 0.23f, 0.31f, 0f), Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero); hud.warnImage = warn;

            var play = UI("PlayGroup", canvasGo.transform, Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero); hud.playGroup = play.gameObject;
            UIImage("LevelBg", play, new Color(0.04f, 0.14f, 0.31f, 0.55f), new Vector2(0f, 1f), new Vector2(0f, 1f), new Vector2(56f, -30f), new Vector2(92f, 40f));
            hud.levelText = UIText("Level", play, "LV 1", 28f, Color.white, new Vector2(0f, 1f), new Vector2(56f, -30f), new Vector2(92f, 40f));
            UIImage("CoinsBg", play, new Color(0.04f, 0.14f, 0.31f, 0.55f), new Vector2(0f, 1f), new Vector2(0f, 1f), new Vector2(160f, -30f), new Vector2(100f, 40f));
            hud.coinsText = UIText("Coins", play, "$ 0", 18f, Gold, new Vector2(0f, 1f), new Vector2(160f, -30f), new Vector2(100f, 40f), TextAlignmentOptions.Center, true);
            var popRt = UI("CoinPop", play, new Vector2(0f, 1f), new Vector2(0f, 1f), new Vector2(160f, -58f), new Vector2(100f, 24f));
            var popGroup = popRt.gameObject.AddComponent<CanvasGroup>(); popGroup.alpha = 0f; hud.coinPopGroup = popGroup;
            hud.coinPopText = UIText("CoinPopText", popRt, "+0", 16f, Gold, new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(100f, 24f));
            var pauseIm = UIImage("PauseBtn", play, new Color(0.04f, 0.14f, 0.31f, 0.75f), new Vector2(0f, 1f), new Vector2(0f, 1f), new Vector2(40f, -78f), new Vector2(56f, 40f));
            pauseIm.raycastTarget = true;
            var pauseBtn = pauseIm.gameObject.AddComponent<Button>();
            UnityEditor.Events.UnityEventTools.AddPersistentListener(pauseBtn.onClick, hud.OnPauseButton);
            UIText("PauseGlyph", pauseIm.transform, "II", 20f, Color.white, new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(56f, 40f));
            UIImage("ProgressBg", play, new Color(0.04f, 0.14f, 0.31f, 0.55f), new Vector2(1f, 1f), new Vector2(1f, 1f), new Vector2(-135f, -30f), new Vector2(160f, 14f));
            var fill = UIImage("ProgressFill", play, Blue, new Vector2(1f, 1f), new Vector2(1f, 1f), new Vector2(-215f, -30f), new Vector2(8f, 14f));
            fill.rectTransform.pivot = new Vector2(0f, 0.5f); fill.rectTransform.anchoredPosition = new Vector2(-215f, -30f);
            hud.progressFill = fill.rectTransform; hud.progressImage = fill; hud.progressWidth = 160f;
            hud.progressText = UIText("ProgressText", play, "0%", 11f, Color.white, new Vector2(1f, 1f), new Vector2(-135f, -30f), new Vector2(160f, 14f), TextAlignmentOptions.Center, true);
            UIText("Skull", play, "BOSS", 12f, Color.white, new Vector2(1f, 1f), new Vector2(-32f, -30f), new Vector2(50f, 20f), TextAlignmentOptions.Center, true);
            UIImage("PlanesBg", play, new Color(0.04f, 0.14f, 0.31f, 0.7f), new Vector2(0.5f, 0f), new Vector2(0.5f, 0f), new Vector2(0f, 96f), new Vector2(104f, 46f));
            UIText("PlanesLabel", play, "PLANES", 10f, new Color(0.81f, 0.9f, 1f), new Vector2(0.5f, 0f), new Vector2(0f, 110f), new Vector2(104f, 16f), TextAlignmentOptions.Center, true);
            hud.planesText = UIText("Planes", play, "0", 24f, Color.white, new Vector2(0.5f, 0f), new Vector2(0f, 88f), new Vector2(104f, 26f));
            UIImage("WeaponBg", play, new Color(0.04f, 0.14f, 0.31f, 0.55f), new Vector2(0f, 0f), new Vector2(0f, 0f), new Vector2(84f, 30f), new Vector2(150f, 44f));
            hud.weaponName = UIText("WeaponName", play, "GATLING", 18f, Gold, new Vector2(0f, 0f), new Vector2(84f, 38f), new Vector2(150f, 22f));
            hud.weaponDesc = UIText("WeaponDesc", play, "single target, fast", 11f, new Color(0.81f, 0.9f, 1f), new Vector2(0f, 0f), new Vector2(84f, 20f), new Vector2(150f, 18f), TextAlignmentOptions.Center, true);
            UIImage("KillsBg", play, new Color(0.04f, 0.14f, 0.31f, 0.55f), new Vector2(1f, 0f), new Vector2(1f, 0f), new Vector2(-54f, 30f), new Vector2(90f, 44f));
            UIText("KillsLabel", play, "KILLS", 10f, new Color(0.81f, 0.9f, 1f), new Vector2(1f, 0f), new Vector2(-54f, 41f), new Vector2(90f, 16f), TextAlignmentOptions.Center, true);
            hud.killsText = UIText("Kills", play, "0", 18f, Color.white, new Vector2(1f, 0f), new Vector2(-54f, 24f), new Vector2(90f, 22f));
            var hintRt = UI("Hint", play, new Vector2(0.5f, 0f), new Vector2(0.5f, 0f), new Vector2(20f, 34f), new Vector2(200f, 44f));
            var hintGroup = hintRt.gameObject.AddComponent<CanvasGroup>(); hud.hintGroup = hintGroup;
            UIImage("HintBg", hintRt, new Color(0.04f, 0.14f, 0.31f, 0.6f), Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero);
            hud.hintText = UIText("HintText", hintRt, "DRAG TO FLY\nDIVE for crates  ·  CLIMB to fight", 12f, Color.white, new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(200f, 44f), TextAlignmentOptions.Center, true);

            var bannerRt = UI("Banner", canvasGo.transform, new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f), new Vector2(0f, 190f), new Vector2(540f, 70f));
            var bannerGroup = bannerRt.gameObject.AddComponent<CanvasGroup>(); bannerGroup.alpha = 0f; hud.bannerGroup = bannerGroup;
            UIImage("BannerBg", bannerRt, new Color(0.02f, 0.1f, 0.2f, 0.55f), Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero);
            hud.bannerText = UIText("BannerText", bannerRt, "", 52f, Color.white, new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(540f, 70f));

            var title = Panel("TitlePanel", canvasGo.transform, 0.0f); hud.titlePanel = title;
            UIText("T1", title.transform, "SKY", 100f, Color.white, new Vector2(0.5f, 1f), new Vector2(0f, -110f), new Vector2(500f, 110f));
            UIText("T2", title.transform, "SQUAD", 100f, Gold, new Vector2(0.5f, 1f), new Vector2(0f, -200f), new Vector2(500f, 110f));
            UIImage("LobbyCoinsBg", title.transform, new Color(0.04f, 0.14f, 0.31f, 0.7f), new Vector2(0.5f, 1f), new Vector2(0.5f, 1f), new Vector2(0f, -290f), new Vector2(220f, 46f));
            hud.lobbyCoins = UIText("LobbyCoins", title.transform, "$ 0", 24f, Gold, new Vector2(0.5f, 1f), new Vector2(0f, -290f), new Vector2(220f, 46f));
            hud.attemptInfo = UIText("AttemptInfo", title.transform, "ATTEMPT 1", 14f, new Color(0.81f, 0.9f, 1f), new Vector2(0.5f, 1f), new Vector2(0f, -330f), new Vector2(500f, 24f), TextAlignmentOptions.Center, true);
            string[] cardNames = { "FIRE RATE", "DAMAGE", "REVENUE" };
            Color[] cardCols = { new Color(1f, 0.62f, 0.1f), Red, new Color(0.45f, 0.95f, 0.5f) };
            for (int i = 0; i < 3; i++)
            {   // upgrade cards: tap to buy; HUD.RefreshLobby fills in level, effect and price
                float cx = (i - 1) * 165f;
                var card = UIImage("Card" + i, title.transform, new Color(0.04f, 0.14f, 0.31f, 0.85f), new Vector2(0.5f, 0f), new Vector2(0.5f, 0f), new Vector2(cx, 240f), new Vector2(150f, 165f));
                card.raycastTarget = true;
                var buy = card.gameObject.AddComponent<Button>();
                UnityEditor.Events.UnityEventTools.AddIntPersistentListener(buy.onClick, hud.OnBuy, i);
                UIImage("CardTop" + i, card.transform, cardCols[i], new Vector2(0.5f, 1f), new Vector2(0.5f, 1f), new Vector2(0f, -4f), new Vector2(150f, 8f));
                UIText("CardName" + i, card.transform, cardNames[i], 15f, Color.white, new Vector2(0.5f, 1f), new Vector2(0f, -30f), new Vector2(150f, 30f));
                hud.cardLevel[i] = UIText("CardLevel" + i, card.transform, "LV 0", 26f, cardCols[i], new Vector2(0.5f, 0.5f), new Vector2(0f, 8f), new Vector2(150f, 40f));
                hud.cardEffect[i] = UIText("CardEffect" + i, card.transform, "", 11f, new Color(0.81f, 0.9f, 1f), new Vector2(0.5f, 0.5f), new Vector2(0f, -18f), new Vector2(150f, 20f), TextAlignmentOptions.Center, true);
                UIImage("CardCostBg" + i, card.transform, new Color(0.02f, 0.08f, 0.18f, 0.9f), new Vector2(0.5f, 0f), new Vector2(0.5f, 0f), new Vector2(0f, 24f), new Vector2(130f, 34f));
                hud.cardCost[i] = UIText("CardCost" + i, card.transform, "$ 0", 18f, Gold, new Vector2(0.5f, 0f), new Vector2(0f, 24f), new Vector2(130f, 34f));
            }
            var startIm = UIImage("StartBtn", title.transform, Gold, new Vector2(0.5f, 0f), new Vector2(0.5f, 0f), new Vector2(0f, 100f), new Vector2(300f, 66f));
            startIm.raycastTarget = true;
            var startBtn = startIm.gameObject.AddComponent<Button>();
            UnityEditor.Events.UnityEventTools.AddPersistentListener(startBtn.onClick, hud.OnStartButton);
            UIText("StartText", startIm.transform, "TAP TO START", 30f, Navy, new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(300f, 66f));
            UIText("LobbyHint", title.transform, "same round every attempt - spend, then go again   |   desktop: arrows / WASD", 11f, new Color(0.81f, 0.9f, 1f), new Vector2(0.5f, 0f), new Vector2(0f, 48f), new Vector2(520f, 20f), TextAlignmentOptions.Center, true);

            var clear = Panel("ClearPanel", canvasGo.transform, 0.72f); hud.clearPanel = clear;
            UIText("C1", clear.transform, "BOSS", 90f, Color.white, new Vector2(0.5f, 0.5f), new Vector2(0f, 170f), new Vector2(500f, 100f));
            UIText("C2", clear.transform, "DOWN!", 90f, Gold, new Vector2(0.5f, 0.5f), new Vector2(0f, 80f), new Vector2(500f, 100f));
            hud.clearStats = UIText("CStats", clear.transform, "", 18f, new Color(0.81f, 0.9f, 1f), new Vector2(0.5f, 0.5f), new Vector2(0f, -30f), new Vector2(500f, 70f), TextAlignmentOptions.Center, true);
            UIText("CTap", clear.transform, "TAP FOR NEXT", 30f, Gold, new Vector2(0.5f, 0.5f), new Vector2(0f, -150f), new Vector2(400f, 50f));

            var over = Panel("OverPanel", canvasGo.transform, 0.78f); hud.overPanel = over;
            UIText("O1", over.transform, "SQUADRON", 80f, Color.white, new Vector2(0.5f, 0.5f), new Vector2(0f, 180f), new Vector2(520f, 100f));
            UIText("O2", over.transform, "LOST", 90f, Red, new Vector2(0.5f, 0.5f), new Vector2(0f, 90f), new Vector2(500f, 100f));
            hud.overReason = UIText("OReason", over.transform, "", 16f, Color.white, new Vector2(0.5f, 0.5f), new Vector2(0f, -10f), new Vector2(500f, 60f), TextAlignmentOptions.Center, true);
            hud.overStats = UIText("OStats", over.transform, "", 16f, new Color(0.81f, 0.9f, 1f), new Vector2(0.5f, 0.5f), new Vector2(0f, -60f), new Vector2(500f, 30f), TextAlignmentOptions.Center, true);
            UIText("OTap", over.transform, "TAP TO CONTINUE", 30f, Gold, new Vector2(0.5f, 0.5f), new Vector2(0f, -170f), new Vector2(400f, 50f));

            var pause = Panel("PausePanel", canvasGo.transform, 0.6f); hud.pausePanel = pause;
            UIText("P1", pause.transform, "PAUSED", 80f, Color.white, new Vector2(0.5f, 0.5f), new Vector2(0f, 110f), new Vector2(500f, 100f));
            UIText("PTap", pause.transform, "TAP TO RESUME", 30f, Gold, new Vector2(0.5f, 0.5f), new Vector2(0f, -40f), new Vector2(400f, 50f));

            // UI buttons need an event system; the squad's drag/tap input reads the devices directly
            new GameObject("EventSystem", typeof(UnityEngine.EventSystems.EventSystem), typeof(UnityEngine.InputSystem.UI.InputSystemUIInputModule));

            // wire the game manager
            gm.config = D.config; gm.squad = squad; gm.input = input; gm.enemies = enemies; gm.supply = supply; gm.boss = boss; gm.hud = hud; gm.fx = fx; gm.sfx = audio; gm.world = world;
            fx.hud = hud;

            string scenePath = Root + "/Scenes/Main.unity";
            EditorSceneManager.SaveScene(scene, scenePath);
            EditorBuildSettings.scenes = new[] { new EditorBuildSettingsScene(scenePath, true) };
            Debug.Log("[SkySquad] scene saved: " + scenePath);
        }

        static void SetProp(SerializedObject so, string name, object value)
        {
            var p = so.FindProperty(name);
            if (p == null) { Debug.LogWarning("[SkySquad] pipeline asset has no field " + name); return; }
            switch (value) { case int i: p.intValue = i; break; case float f: p.floatValue = f; break; case bool b: p.boolValue = b; break; }
        }

        static Mesh BubbleMesh()
        {
            string path = Gen + "/Meshes/Bubble.asset";
            var m = AssetDatabase.LoadAssetAtPath<Mesh>(path);
            if (m != null) return m;
            var b = new MeshBuilder(1);
            b.Ellipsoid(Vector3.zero, new Vector3(4.2f, 2.4f, 4.2f), 18, 10, 0);
            m = b.Build("Bubble");
            AssetDatabase.CreateAsset(m, path);
            return m;
        }

        static void ApplyPlayerSettings()
        {
            PlayerSettings.companyName = "mtjrcloud";
            PlayerSettings.productName = "Sky Squad";
            PlayerSettings.defaultInterfaceOrientation = UIOrientation.Portrait;
            PlayerSettings.allowedAutorotateToLandscapeLeft = false; PlayerSettings.allowedAutorotateToLandscapeRight = false;
            PlayerSettings.allowedAutorotateToPortrait = true; PlayerSettings.allowedAutorotateToPortraitUpsideDown = false;
            PlayerSettings.defaultScreenWidth = 540; PlayerSettings.defaultScreenHeight = 960;
            PlayerSettings.fullScreenMode = FullScreenMode.Windowed; PlayerSettings.resizableWindow = true;
            PlayerSettings.runInBackground = true;
            PlayerSettings.SetApplicationIdentifier(NamedBuildTarget.Android, "com.mtjrcloud.skysquad");
            PlayerSettings.SetApplicationIdentifier(NamedBuildTarget.iOS, "com.mtjrcloud.skysquad");
            PlayerSettings.SetApplicationIdentifier(NamedBuildTarget.Standalone, "com.mtjrcloud.skysquad");
            AssetDatabase.SaveAssets();
        }
    }
}
