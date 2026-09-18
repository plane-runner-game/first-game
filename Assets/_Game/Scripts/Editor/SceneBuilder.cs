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
        const float SeaLevel = -2.5f;   // the waterline (2026-09-18, "the sea is close to me, I want it farther": 0 until then). The water, the buoys and, through supplyAlt, the boats / crates / gates all sit on it
        static readonly Color Navy = new Color(0.04f, 0.14f, 0.31f);
        static readonly Color Gold = new Color(1f, 0.82f, 0.25f);
        static readonly Color Red = new Color(1f, 0.23f, 0.31f);
        static readonly Color Blue = new Color(0.37f, 0.69f, 1f);

        class Mats { public Material planeBody, planeBody2, planeAccent, glass, leader, attackerBody, attackerAccent, jetBody, jetAccent, jetGlow, enemyBody, enemyAccent, enemyGlass, bomberBody, bomberAccent, boss2Body, boss2Accent, boss3Body, boss3Accent, boss4Body, boss4Accent, bossGlass, zepBody, zepAccent, zepPlate, crate, crateBand, hull, outline, bomberGlow, bullet, water, cloud, buoy, buoyPole, tracer, particle, smoke, shieldBubble, barBg, barHp, barGhost, barTimer, flash, prop, rocketBody, rocketFin, coin, stopLine, threatMarker, enemyCowl, propDisc, bossFlash, gateFrame, gatePanel, oh1Body, oh1Glass, sparrowBody; }
        class Meshes { public Mesh fighter, attacker, jet, prop, enemy, boss, boss2, boss3, boss4, zeppelin, crate, boat, boatWeapon, rocket, buoy, bullet, coin, gateFrame, gatePanel, sea; }
        class Prefabs { public GameObject planeFighter, planeAttacker, planeJet, enemyFighter, miniBoss, miniBoss2, miniBoss3, miniBoss4, sparrowBoss, breakable, gate, bullet, boss, explosion, sparks, splash, floatText, ring, rocket, coin; }
        class Defs { public GameConfig config; public WeaponDef gatling, rockets, laser; public EnemyKindDef fighter, miniBoss; }
        static TMP_FontAsset font, fontUi, fontUiLight; static Material fontOutline, fontOutlineSmall, fontUiPlain, fontUiLightPlain, fontUiTitle;

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
            CreateUiSprites();
            LoadGui();   // the GUI Pro - Casual Game sprites (2026-09-19)
            foreach (var stale in new[] {   // assets from older designs (gates, hordes, blimps)
                Gen + "/Prefabs/Gate.prefab", Gen + "/Prefabs/Horde.prefab", Gen + "/Prefabs/Drone.prefab", Gen + "/Prefabs/Bomber.prefab",
                Gen + "/Data/Horde_Fighter.asset", Gen + "/Data/Horde_Drone.asset", Gen + "/Data/Horde_Bomber.asset",
                Gen + "/Meshes/Blimp.asset", Gen + "/Meshes/Drone.asset",
                Gen + "/Materials/CargoBody.mat", Gen + "/Materials/CargoAccent.mat",
                Gen + "/Materials/DroneBody.mat", Gen + "/Materials/DroneAccent.mat", Gen + "/Materials/DroneEye.mat", Gen + "/Materials/DiveLine.mat",
                Gen + "/Textures/WaterTiles.png", /* the flat sea's grey tiles (until 2026-09-18) */
                Gen + "/Textures/UI_Round.png", Gen + "/Textures/UI_Grad.png", Gen + "/Fonts/LilitaOne Title.mat" /* the candy UI pass (an hour on 2026-09-18) */ })
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
            fontOutline = FontPreset(font, "LilitaOne Outline", 0.25f, Navy);
            fontOutlineSmall = FontPreset(font, "LilitaOne Outline Thin", 0.15f, Navy);
            // the screen UI's face (2026-09-18): Barlow Condensed (OFL), a tight modern condensed sans - the tactical look. Lilita stays on the
            // in-world labels (hp numbers, gate "+2 PLANES", "+10" pops), which need its fat outlined shapes to read over the sea.
            fontUi = LoadOrCreateFont(Root + "/Fonts/BarlowCondensed-Bold.ttf", "BarlowCondensed-Bold SDF") ?? font;
            fontUiLight = LoadOrCreateFont(Root + "/Fonts/BarlowCondensed-SemiBold.ttf", "BarlowCondensed-SemiBold SDF") ?? fontUi;
            fontUiPlain = FontPreset(fontUi, "BarlowCondensed Bold Shadow", 0f, Color.black, true, 0.55f);        // no outline, a soft drop shadow for legibility over the sky
            fontUiLightPlain = FontPreset(fontUiLight, "BarlowCondensed SemiBold Shadow", 0f, Color.black, true, 0.5f);
            fontUiTitle = FontPreset(fontUi, "BarlowCondensed Bold Title", 0f, Color.black, true, 0.8f);         // the big words: a deeper shadow
        }
        /// <summary>A TMP font asset (dynamic SDF atlas) for a .ttf in the project, created once and reused on later builds.</summary>
        static TMP_FontAsset LoadOrCreateFont(string ttfPath, string name)
        {
            string path = Gen + "/Fonts/" + name + ".asset";
            var fa = AssetDatabase.LoadAssetAtPath<TMP_FontAsset>(path);
            if (fa != null) return fa;
            var ttf = AssetDatabase.LoadAssetAtPath<Font>(ttfPath);
            if (ttf == null) { Debug.LogWarning("[SkySquad] font not found: " + ttfPath); return null; }
            try
            {
                fa = TMP_FontAsset.CreateFontAsset(ttf, 90, 9, UnityEngine.TextCore.LowLevel.GlyphRenderMode.SDFAA, 1024, 1024, AtlasPopulationMode.Dynamic, true);
                fa.name = name;
                AssetDatabase.CreateAsset(fa, path);
                fa.material.name = name + " Material"; AssetDatabase.AddObjectToAsset(fa.material, fa);
                fa.atlasTexture.name = name + " Atlas"; AssetDatabase.AddObjectToAsset(fa.atlasTexture, fa);
                AssetDatabase.SaveAssets();
                return AssetDatabase.LoadAssetAtPath<TMP_FontAsset>(path);
            }
            catch (Exception e) { Debug.LogWarning("[SkySquad] font asset creation failed for " + name + ": " + e.Message); return null; }
        }

        static Material FontPreset(TMP_FontAsset fa, string name, float width, Color c, bool shadow = false, float shadowAlpha = 0.75f)
        {
            string path = Gen + "/Fonts/" + name + ".mat";
            var m = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (m == null) { m = new Material(fa.material); AssetDatabase.CreateAsset(m, path); }
            m.shader = fa.material.shader;
            m.CopyPropertiesFromMaterial(fa.material);
            if (width > 0f)
            {
                m.SetFloat(ShaderUtilities.ID_OutlineWidth, width);
                m.SetColor(ShaderUtilities.ID_OutlineColor, c);
                m.SetFloat(ShaderUtilities.ID_FaceDilate, 0.05f);
                m.EnableKeyword("OUTLINE_ON");
            }
            else { m.SetFloat(ShaderUtilities.ID_OutlineWidth, 0f); m.SetFloat(ShaderUtilities.ID_FaceDilate, 0f); m.DisableKeyword("OUTLINE_ON"); }
            if (shadow)
            {   // TMP's underlay: a dark copy offset down and right, soft
                m.SetColor(ShaderUtilities.ID_UnderlayColor, new Color(c.r, c.g, c.b, shadowAlpha));
                m.SetFloat(ShaderUtilities.ID_UnderlayOffsetX, 0.25f); m.SetFloat(ShaderUtilities.ID_UnderlayOffsetY, -0.35f);
                m.SetFloat(ShaderUtilities.ID_UnderlayDilate, 0.25f); m.SetFloat(ShaderUtilities.ID_UnderlaySoftness, 0.35f);
                m.EnableKeyword("UNDERLAY_ON");
            }
            else m.DisableKeyword("UNDERLAY_ON");
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
        /// <summary>A texture file imported as a normal map (the importer flag, set once). Null if the file is missing.</summary>
        static Texture2D NormalMap(string path)
        {
            var imp = AssetImporter.GetAtPath(path) as TextureImporter; if (imp == null) return null;
            if (imp.textureType != TextureImporterType.NormalMap) { imp.textureType = TextureImporterType.NormalMap; imp.SaveAndReimport(); }
            return AssetDatabase.LoadAssetAtPath<Texture2D>(path);
        }
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
            M.enemyBody = Lit("EnemyBody", new Color(0.88f, 0.16f, 0.16f), 0.4f);     // crimson: reads against the sky, distinct from the orange boss
            M.enemyAccent = Lit("EnemyAccent", new Color(0.98f, 0.94f, 0.82f));      // cream bands: bright dots head-on
            M.enemyGlass = Lit("EnemyGlass", new Color(0.35f, 0.6f, 0.8f), 0.9f);    // sky-blue tinted canopy
            M.enemyCowl = Lit("EnemyCowl", new Color(0.16f, 0.15f, 0.17f), 0.5f);    // dark engine cowl and guns
            // the OH-1 Ninja enemy (2026-09-18): the pack's fuselage albedo + normal, downsized to 1k under Art/Enemies (the pack is 836 MB and stays out of git); the canopy a dark tinted glass
            M.oh1Body = Lit("OH1Fuselage", Color.white, 0.3f);
            var oh1Albedo = AssetDatabase.LoadAssetAtPath<Texture2D>(Root + "/Art/Enemies/OH1_Fuselage_BaseColor.png"); if (oh1Albedo != null) M.oh1Body.SetTexture("_BaseMap", oh1Albedo);
            var oh1Normal = NormalMap(Root + "/Art/Enemies/OH1_Fuselage_Normal.png"); if (oh1Normal != null) { M.oh1Body.SetTexture("_BumpMap", oh1Normal); M.oh1Body.EnableKeyword("_NORMALMAP"); }
            M.oh1Glass = Transparent("OH1Glass", new Color(0.22f, 0.32f, 0.40f, 0.65f));
            // the Sparrow bosses (2026-09-18): the pack's grey albedo + normal + emissive at 1k under Art/Enemies (the pack is 840 MB and stays out of git); WaveSpawner tints each boss
            M.sparrowBody = Lit("SparrowBody", Color.white, 0.5f); M.sparrowBody.SetFloat("_Metallic", 0.25f);
            var spAlbedo = AssetDatabase.LoadAssetAtPath<Texture2D>(Root + "/Art/Enemies/Sparrow_Grey.png"); if (spAlbedo != null) M.sparrowBody.SetTexture("_BaseMap", spAlbedo);
            var spNormal = NormalMap(Root + "/Art/Enemies/Sparrow_Normal.png"); if (spNormal != null) { M.sparrowBody.SetTexture("_BumpMap", spNormal); M.sparrowBody.EnableKeyword("_NORMALMAP"); }
            var spEmis = AssetDatabase.LoadAssetAtPath<Texture2D>(Root + "/Art/Enemies/Sparrow_Emissive.png"); if (spEmis != null) { M.sparrowBody.SetTexture("_EmissionMap", spEmis); M.sparrowBody.SetColor("_EmissionColor", new Color(2.2f, 2.2f, 2.4f)); M.sparrowBody.EnableKeyword("_EMISSION"); M.sparrowBody.globalIlluminationFlags = MaterialGlobalIlluminationFlags.None; }
            M.bomberBody = Lit("BomberBody", new Color(0.23f, 0.25f, 0.3f));
            M.bomberAccent = Lit("BomberAccent", new Color(1f, 0.62f, 0.1f));
            M.boss2Body = Lit("Boss2Body", new Color(0.3f, 0.37f, 0.22f));      // bosses 3-4, the twin-boom: olive with yellow bands
            M.boss2Accent = Lit("Boss2Accent", new Color(1f, 0.85f, 0.2f));
            M.boss3Body = Lit("Boss3Body", new Color(0.46f, 0.12f, 0.16f));     // bosses 5-6, the flying wing: crimson with cream bands
            M.boss3Accent = Lit("Boss3Accent", new Color(0.95f, 0.92f, 0.8f));
            M.boss4Body = Lit("Boss4Body", new Color(0.3f, 0.14f, 0.42f));      // boss 7, the airship: purple with gold
            M.boss4Accent = Lit("Boss4Accent", new Color(1f, 0.8f, 0.3f));
            M.bossGlass = Lit("BossGlass", new Color(0.5f, 0.74f, 0.88f), 0.92f);   // the gunship's glazed nose and canopy
            M.zepBody = Lit("ZepBody", new Color(0.69f, 0.16f, 0.23f), 0.45f);
            M.zepAccent = Lit("ZepAccent", new Color(0.17f, 0.17f, 0.23f));
            M.zepPlate = Lit("ZepPlate", new Color(0.96f, 0.96f, 0.96f));
            M.crate = Lit("Crate", new Color(0.72f, 0.5f, 0.27f));
            M.crateBand = Lit("CrateBand", new Color(0.36f, 0.24f, 0.13f));
            M.hull = Lit("BoatHull", Color.white, 0.3f);   // the crate boat's hull, tinted per crate kind at runtime (was the parachute canopy "ChuteCanopy" until 2026-09-18)
            M.outline = Mat("Outline", "Universal Render Pipeline/Unlit", new Color(0.05f, 0.05f, 0.08f), m => m.SetFloat("_Cull", 1f)); // inside-out hull = toon outline
            M.bomberGlow = Unlit("BomberGlow", Red);
            M.bullet = Unlit("Bullet", Color.white);   // tinted per shot with a property block
            M.coin = Lit("Coin", new Color(1f, 0.85f, 0.3f), 0.75f);
            M.stopLine = Transparent("StopLine", new Color(1f, 0.25f, 0.3f, 0.6f));   // StopLine pulses the alpha
            M.threatMarker = Transparent("ThreatMarker", Color.white); M.threatMarker.SetTexture("_BaseMap", ReticleTexture());   // ThreatMarkers tints it per fighter
            // the sea: Gerstner waves, sky-gradient fresnel, sun glitter, crest foam (Shaders/Sea.shader, 2026-09-18: "a better sea that works on the web",
            // after Crest turned out Built-in-only and never WebGL). The flat Lit plane with grey tiles (and, for a day on 2026-09-16, a normal-mapped
            // ripple shader reflecting the HDRI - "ugly, put it back") came before. Every number that matters is set here; the textures are generated.
            M.water = Mat("Water", "SkySquad/Sea", Color.white, m =>
            {
                m.SetColor("_ShallowColor", new Color(0.16f, 0.66f, 0.78f)); m.SetColor("_DeepColor", new Color(0.03f, 0.30f, 0.58f)); m.SetColor("_SSSColor", new Color(0.35f, 0.90f, 0.85f));   /* a tropical ocean (2026-09-19, "prettier, simple, more realistic"): turquoise over deep blue, the crests glowing aqua (the flat two-green lagoon lasted an hour); the war dusk was (0.16, 0.34, 0.42) / (0.03, 0.09, 0.18) / (0.30, 0.50, 0.42) */   /* the war dusk (2026-09-18): slate-teal over near-black; the morning sea was (0.09, 0.60, 0.82) / (0.02, 0.22, 0.52) / (0.20, 0.85, 0.75) */
                m.SetColor("_SkyHorizon", new Color(0.86f, 0.93f, 0.96f)); m.SetColor("_SkyZenith", new Color(0.40f, 0.70f, 0.92f)); m.SetColor("_FoamColor", new Color(0.96f, 1f, 0.98f));   /* the water reflects a clear morning sky, white foam (the dusk: (0.95, 0.58, 0.32) / (0.22, 0.24, 0.33) / (0.82, 0.78, 0.74)) */   /* the water reflects the burning horizon and the dark cloud roof; greyish foam (morning: (0.80, 0.87, 0.95) / (0.34, 0.58, 0.92) / white) */
                m.SetTexture("_BaseMap", SeaNormalTexture()); m.SetTextureScale("_BaseMap", Vector2.one); m.SetTextureOffset("_BaseMap", Vector2.zero);
                m.SetTexture("_FoamMap", SeaFoamTexture()); m.SetTextureScale("_FoamMap", new Vector2(0.07f, 0.07f));   // tiles per unit: one foam tile every ~14 units
                m.SetFloat("_Tiling", 0.12f); m.SetFloat("_NormalStrength", 0.32f);   /* a real-looking but calm sea (2026-09-19): soft ripples, a rolling swell, a little sky in it, a touch of glitter and crest foam */
                m.SetVector("_WaveA", new Vector4(0.15f, -1f, 0.08f, 18f)); m.SetVector("_WaveB", new Vector4(0.6f, -0.8f, 0.06f, 10f));   // (dir x, dir z, steepness, length): a long swell toward the player and three shorter crossing waves; amplitude = steepness x length / 2pi, ~0.4 at the highest crest
                m.SetVector("_WaveC", new Vector4(-0.7f, -0.7f, 0.05f, 6f)); m.SetVector("_WaveD", new Vector4(0.3f, -0.95f, 0.03f, 3.5f));
                m.SetFloat("_WaveSpeed", 0.85f); m.SetFloat("_Reflect", 0.42f); m.SetFloat("_Fresnel", 4f);   /* 0.6 / 4 washed the far sea white */
                m.SetFloat("_SpecPower", 260f); m.SetFloat("_SpecIntensity", 0.7f); m.SetFloat("_Foam", 0.3f); m.SetFloat("_FoamStart", 0.7f);   /* 0.9 / 0.45: foam everywhere */
            });
            M.cloud = Transparent("Cloud", new Color(1f, 1f, 1f, 0.72f));   /* white again with the bright morning (2026-09-19; grey-mauve for the war dusk) */ M.cloud.SetTexture("_BaseMap", CloudTexture());   /* grey-mauve for the war dusk (white with the morning sky) */   // softer now that the real sky has its own clouds: these are the near, moving ones
            M.buoy = Lit("Buoy", new Color(1f, 0.54f, 0.24f));
            M.buoyPole = Lit("BuoyPole", Color.white);
            M.tracer = Particle("Tracer", Color.white, true);
            var soft = SoftTexture();
            M.particle = Particle("ParticleAdd", Color.white, true); M.particle.SetTexture("_BaseMap", soft);
            M.smoke = Particle("Smoke", new Color(0.35f, 0.35f, 0.4f, 0.6f), false); M.smoke.SetTexture("_BaseMap", soft);
            M.shieldBubble = Transparent("ShieldBubble", new Color(0.58f, 0.77f, 0.99f, 0.28f));
            M.barBg = Unlit("BarBg", new Color(0.29f, 0.06f, 0.09f));
            M.barHp = Unlit("BarHp", Red);
            M.barGhost = Unlit("BarGhost", new Color(1f, 0.93f, 0.74f));   // the pale bar left hanging where the boss's hp was, before it slides down (2026-09-18)
            M.barTimer = Unlit("BarTimer", Color.white);
            M.flash = Transparent("MuzzleFlash", new Color(1f, 0.9f, 0.4f, 0.9f), true); M.flash.SetTexture("_BaseMap", soft);   // soft additive glow, not a hard square
            M.bossFlash = Transparent("BossFlash", new Color(1f, 0.45f, 0.3f, 0.9f), true); M.bossFlash.SetTexture("_BaseMap", soft);
            M.gateFrame = Unlit("GateFrame", new Color(1f, 0.82f, 0.38f));                       // amber frame, the coin gold: a reward against the dark sea (mint green until 2026-09-18: "not green, a colour that fits the game")
            M.gatePanel = Transparent("GatePanel", new Color(1f, 0.82f, 0.38f, 0.2f), true);      // UpgradeGate tints and pulses it per gate
            M.prop = Lit("Propeller", new Color(0.15f, 0.15f, 0.18f));
            M.propDisc = Transparent("PropDisc", new Color(0.92f, 0.92f, 0.96f, 0.16f));   // the faint disc of a running prop
            M.rocketBody = Lit("RocketBody", new Color(0.9f, 0.91f, 0.93f));
            M.rocketFin = Lit("RocketFin", Red);
            return M;
        }

        static Texture2D SaveTex(Texture2D t, string name, bool linear = false)
        {
            string path = Gen + "/Textures/" + name + ".png";
            File.WriteAllBytes(path, t.EncodeToPNG());
            AssetDatabase.ImportAsset(path);
            var imp = AssetImporter.GetAtPath(path) as TextureImporter;
            if (imp != null) { imp.wrapMode = TextureWrapMode.Repeat; imp.mipmapEnabled = true; imp.alphaIsTransparency = !linear; imp.sRGBTexture = !linear; imp.SaveAndReimport(); }   // linear: data (normals), not colour
            return AssetDatabase.LoadAssetAtPath<Texture2D>(path);
        }
        /// <summary>Tileable ripple normals for the sea shader: three layers of crossing sine swells plus a fine chop, encoded xyz -> rgb (0.5 = flat).</summary>
        static Texture2D SeaNormalTexture()
        {
            int n = 256; var t = new Texture2D(n, n, TextureFormat.RGBA32, false);
            float H(float u, float w)
            {   // periodic in both axes (u, w in 0..2pi) so the tile repeats seamlessly
                return 0.55f * Mathf.Sin(u * 2f + Mathf.Sin(w) * 1.2f) * Mathf.Sin(w * 3f + Mathf.Sin(u * 2f) * 0.8f)
                     + 0.3f * Mathf.Sin(u * 5f + w * 3f + Mathf.Sin(w * 2f))
                     + 0.15f * Mathf.Sin(u * 11f - w * 7f) * Mathf.Sin(w * 9f + u * 4f);
            }
            float step = Mathf.PI * 2f / n;
            for (int y = 0; y < n; y++) for (int x = 0; x < n; x++)
                {
                    float u = x * step, w = y * step;
                    float dx = (H(u + step, w) - H(u - step, w)) / (2f * step) * 0.35f;   // slope -> normal (the 0.35 sets how steep the ripples read)
                    float dz = (H(u, w + step) - H(u, w - step)) / (2f * step) * 0.35f;
                    var nrm = new Vector3(-dx, 1f, -dz).normalized;
                    t.SetPixel(x, y, new Color(nrm.x * 0.5f + 0.5f, nrm.z * 0.5f + 0.5f, nrm.y * 0.5f + 0.5f, 1f));   // rgb = xz slope, y up in blue
                }
            t.Apply();
            return SaveTex(t, "SeaNormals", true);
        }
        /// <summary>Tileable foam noise for the sea shader: three octaves of periodic value noise, streaked a little along z, in red (0..1).</summary>
        /// <summary>The WoodenBoxes pack albedo recoloured to brown wood: every low-saturation (grey plank) pixel is tinted warm brown by its
        /// brightness, the blue steel corners and the olive rope keep their colour. Read through a Blit so the pack's import settings stay untouched.</summary>
        static Texture2D CrateWoodTexture(Texture src)
        {
            int n = 1024; var rt = RenderTexture.GetTemporary(n, n, 0, RenderTextureFormat.ARGB32, RenderTextureReadWrite.sRGB);
            Graphics.Blit(src, rt); RenderTexture.active = rt;
            var t = new Texture2D(n, n, TextureFormat.RGBA32, false); t.ReadPixels(new Rect(0, 0, n, n), 0, 0); RenderTexture.active = null; RenderTexture.ReleaseTemporary(rt);
            var px = t.GetPixels();
            var brown = new Color(1.25f, 0.82f, 0.48f);   // x grey: mid grey 0.5 -> (0.62, 0.41, 0.24), a warm oak
            for (int i = 0; i < px.Length; i++)
            {
                var c = px[i]; float h, s, v; Color.RGBToHSV(c, out h, out s, out v);
                float keep = Mathf.Clamp01((s - 0.12f) / 0.18f);   // coloured pixels (blue steel, rope) keep their hue; grey planks get the tint
                var tinted = new Color(Mathf.Clamp01(v * brown.r), Mathf.Clamp01(v * brown.g), Mathf.Clamp01(v * brown.b), c.a);
                px[i] = Color.Lerp(tinted, c, keep);
            }
            t.SetPixels(px); t.Apply();
            return SaveTex(t, "CrateWood");
        }
        static Texture2D SeaFoamTexture()
        {
            int n = 256; var t = new Texture2D(n, n, TextureFormat.RGBA32, false);
            var rnd = new System.Random(7);
            float[][] grids = new float[3][]; int[] sizes = { 8, 16, 32 };
            for (int o = 0; o < 3; o++) { grids[o] = new float[sizes[o] * sizes[o]]; for (int i = 0; i < grids[o].Length; i++) grids[o][i] = (float)rnd.NextDouble(); }
            float Value(int o, float fx, float fy)
            {   // smooth periodic value noise on the o-th grid
                int s = sizes[o]; fx = (fx % 1f + 1f) % 1f * s; fy = (fy % 1f + 1f) % 1f * s;
                int x0 = (int)fx, y0 = (int)fy, x1 = (x0 + 1) % s, y1 = (y0 + 1) % s;
                float tx = Mathf.SmoothStep(0f, 1f, fx - x0), ty = Mathf.SmoothStep(0f, 1f, fy - y0);
                float a = grids[o][y0 * s + x0], b = grids[o][y0 * s + x1], c = grids[o][y1 * s + x0], d = grids[o][y1 * s + x1];
                return Mathf.Lerp(Mathf.Lerp(a, b, tx), Mathf.Lerp(c, d, tx), ty);
            }
            for (int y = 0; y < n; y++) for (int x = 0; x < n; x++)
                {
                    float u = x / (float)n, w = y / (float)n;
                    float v = Value(0, u, w * 0.5f) * 0.5f + Value(1, u, w * 0.5f) * 0.3f + Value(2, u, w) * 0.2f;   // w halved on the big octaves: streaks along the travel direction
                    v = Mathf.Clamp01((v - 0.25f) * 1.7f);
                    t.SetPixel(x, y, new Color(v, v, v, 1f));
                }
            t.Apply();
            return SaveTex(t, "SeaFoam", true);
        }
        /// <summary>A lock-on reticle: a thin ring with four corner brackets and a centre dot, white on transparent,
        /// anti-aliased. ThreatMarkers tints and spins it on every incoming fighter.</summary>
        static Texture2D ReticleTexture()
        {
            int n = 128; var t = new Texture2D(n, n, TextureFormat.RGBA32, false);
            float Line(float v, float lo, float hi, float soft) => Mathf.Clamp01(Mathf.Min(v - lo, hi - v) / soft + 0.5f);   // 1 inside [lo,hi], soft edges
            for (int y = 0; y < n; y++) for (int x = 0; x < n; x++)
                {
                    float u = (x + 0.5f) / n - 0.5f, v = (y + 0.5f) / n - 0.5f;   // -0.5 .. 0.5
                    float d = Mathf.Sqrt(u * u + v * v);
                    float ring = Line(d, 0.30f, 0.335f, 0.012f);
                    float dot = Line(d, -1f, 0.03f, 0.012f);
                    float au = Mathf.Abs(u), av = Mathf.Abs(v);
                    float edge = Line(Mathf.Max(au, av), 0.455f, 0.5f, 0.012f);   // on the outer square's edge...
                    float arm = Mathf.Max(Line(au, 0.28f, 0.5f, 0.012f) * Line(av, 0.455f, 0.5f, 0.012f), Line(av, 0.28f, 0.5f, 0.012f) * Line(au, 0.455f, 0.5f, 0.012f));
                    float bracket = Mathf.Min(edge, 1f) * (arm > 0f ? arm : 0f);   // ...only near the corners
                    float a = Mathf.Max(ring, Mathf.Max(dot, bracket));
                    t.SetPixel(x, y, new Color(1f, 1f, 1f, a));
                }
            t.Apply();
            var tex = SaveTex(t, "Reticle");
            var imp = AssetImporter.GetAtPath(Gen + "/Textures/Reticle.png") as TextureImporter;
            if (imp != null) { imp.wrapMode = TextureWrapMode.Clamp; imp.SaveAndReimport(); }
            return tex;
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
        // ------------------------------------------------------------ UI sprites (the UI kit, 2026-09-18)
        // Every shape the HUD is drawn with is generated here as a small PNG and imported as a sprite. The look is "tactical glass"
        // (the first pass, rounded candy buttons with shelves and gloss, was thrown out the same evening: "too childish"): a 9-sliced
        // chamfered plate and its 2-px edge ring (Chamfer() gives them any cut size through pixelsPerUnitMultiplier), a soft-edged
        // square for glows, a circle, a tick strip for segmented bars, and flat white icons (coin, gear, pause bars, plane, crosshair).
        // Until this the UI was bare Image squares ("transparent grey rectangles").
        static Sprite uiChamfer, uiChamferEdge, uiSoft, uiCircle, uiTicks, uiCoin, uiGear, uiPause, uiPlane, uiCross, uiPlay, uiSoundOn, uiSoundOff;
        const float UiCut = 12f;      // the chamfer sprite's corner cut in pixels
        const float UiSoftFade = 24f; // the soft sprite's fade width in pixels

        static Sprite SaveSprite(Texture2D t, string name, Vector4 border, bool repeat = false)
        {
            string path = Gen + "/Textures/" + name + ".png";
            File.WriteAllBytes(path, t.EncodeToPNG());
            AssetDatabase.ImportAsset(path);
            var imp = AssetImporter.GetAtPath(path) as TextureImporter;
            if (imp != null)
            {
                imp.textureType = TextureImporterType.Sprite; imp.spriteImportMode = SpriteImportMode.Single; imp.spriteBorder = border; imp.spritePixelsPerUnit = 100f;
                var ts = imp.GetDefaultPlatformTextureSettings(); ts.textureCompression = TextureImporterCompression.Uncompressed; imp.SetPlatformTextureSettings(ts);
                imp.mipmapEnabled = false; imp.wrapMode = repeat ? TextureWrapMode.Repeat : TextureWrapMode.Clamp; imp.filterMode = FilterMode.Bilinear; imp.alphaIsTransparency = true; imp.sRGBTexture = true;
                var ss = new TextureImporterSettings(); imp.ReadTextureSettings(ss); ss.spriteMeshType = SpriteMeshType.FullRect; imp.SetTextureSettings(ss);   // full quads: a sliced sprite must not be trimmed to its opaque pixels
                imp.SaveAndReimport();
            }
            return AssetDatabase.LoadAssetAtPath<Sprite>(path);
        }
        /// <summary>Signed distance to a rounded box centred on the origin (negative inside): half size hw x hh, corner radius r.</summary>
        static float RoundBox(float px, float py, float hw, float hh, float r)
        {
            float qx = Mathf.Abs(px) - (hw - r), qy = Mathf.Abs(py) - (hh - r);
            float ox = Mathf.Max(qx, 0f), oy = Mathf.Max(qy, 0f);
            return Mathf.Sqrt(ox * ox + oy * oy) + Mathf.Min(Mathf.Max(qx, qy), 0f) - r;
        }
        static float Edge(float d) => Mathf.Clamp01(0.5f - d);   // an anti-aliased edge from a signed distance
        /// <summary>Rasterizes f(px, py) -> colour (px, py measured from the centre in pixels, y up) with 3x3 supersampling; the colour
        /// of an edge pixel is the alpha-weighted average, so tinted shapes get no dark fringe.</summary>
        static Texture2D Shape(int w, int h, Func<float, float, Color> f)
        {
            var t = new Texture2D(w, h, TextureFormat.RGBA32, false);
            const int ss = 3;
            for (int y = 0; y < h; y++) for (int x = 0; x < w; x++)
                {
                    float r = 0f, g = 0f, b = 0f, a = 0f;
                    for (int sy = 0; sy < ss; sy++) for (int sx = 0; sx < ss; sx++)
                        {
                            var c = f(x + (sx + 0.5f) / ss - w * 0.5f, y + (sy + 0.5f) / ss - h * 0.5f);
                            r += c.r * c.a; g += c.g * c.a; b += c.b * c.a; a += c.a;
                        }
                    t.SetPixel(x, y, a > 0f ? new Color(r / a, g / a, b / a, a / (ss * ss)) : new Color(1f, 1f, 1f, 0f));
                }
            t.Apply();
            return t;
        }
        static Color White(float a) => new Color(1f, 1f, 1f, a);
        /// <summary>Signed distance to a box with its corners cut at 45 degrees (negative inside): half size hw x hh, cut c.</summary>
        static float ChamferBox(float px, float py, float hw, float hh, float c)
        {
            float ax = Mathf.Abs(px), ay = Mathf.Abs(py);
            float box = Mathf.Max(ax - hw, ay - hh);
            float diag = (ax + ay - (hw + hh - c)) * 0.7071f;
            return Mathf.Max(box, diag);
        }
        static void CreateUiSprites()
        {
            uiChamfer = SaveSprite(Shape(64, 64, (x, y) => White(Edge(ChamferBox(x, y, 32f, 32f, UiCut)))), "UI_Chamfer", new Vector4(16f, 16f, 16f, 16f));
            uiChamferEdge = SaveSprite(Shape(64, 64, (x, y) => { float d = ChamferBox(x, y, 32f, 32f, UiCut); return White(Mathf.Clamp01(Edge(d) - Edge(d + 2f))); }), "UI_ChamferEdge", new Vector4(16f, 16f, 16f, 16f));   // a 2-px ring just inside the plate's edge
            uiSoft = SaveSprite(Shape(96, 96, (x, y) => { float d = RoundBox(x, y, 24f, 24f, 10f); float k = 1f - Mathf.Clamp01(d / UiSoftFade); return White(k * k * (3f - 2f * k)); }), "UI_Soft", new Vector4(40f, 40f, 40f, 40f));
            uiCircle = SaveSprite(Shape(64, 64, (x, y) => White(Edge(Mathf.Sqrt(x * x + y * y) - 31f))), "UI_Circle", Vector4.zero);
            uiTicks = SaveSprite(Shape(16, 8, (x, y) => White(Edge(Mathf.Abs(x + 7.5f) - 0.5f))), "UI_Ticks", Vector4.zero, true);   // one 1-px line at the left of a 16-px tile: tiled over a bar it segments it
            uiCoin = SaveSprite(Shape(64, 64, (x, y) =>
            {   // a flat coin: a ring and a solid centre (white, tinted amber at use)
                float d = Mathf.Sqrt(x * x + y * y);
                return White(Mathf.Max(Edge(Mathf.Abs(d - 26f) - 3.5f), Edge(d - 14f)));
            }), "UI_Coin", Vector4.zero);
            uiGear = SaveSprite(Shape(64, 64, (x, y) =>
            {   // eight soft teeth around a hub with a hole
                float d = Mathf.Sqrt(x * x + y * y), a = Mathf.Atan2(y, x);
                float tooth = Mathf.SmoothStep(0f, 1f, Mathf.Clamp01((Mathf.Cos(a * 8f) + 0.25f) / 0.5f));
                float rt = 20f + 8.5f * tooth;
                return White(Edge(d - rt) * Edge(8.5f - d));
            }), "UI_Gear", Vector4.zero);
            uiPause = SaveSprite(Shape(64, 64, (x, y) => White(Mathf.Max(Edge(RoundBox(x + 11f, y, 6.5f, 19f, 4f)), Edge(RoundBox(x - 11f, y, 6.5f, 19f, 4f))))), "UI_Pause", Vector4.zero);
            uiPlane = SaveSprite(Shape(64, 64, (x, y) =>
            {   // a plane from above, nose up: fuselage, swept wings, tailplane
                float ax = Mathf.Abs(x);
                float body = Edge(RoundBox(x, y - 1f, 5f, 25f, 5f));
                float wing = Edge(Mathf.Max(ax - 28f, Mathf.Max(y - (5f - ax * 0.42f), (-7f - ax * 0.22f) - y)));
                float tail = Edge(Mathf.Max(ax - 12f, Mathf.Max(y - (-18f - ax * 0.35f), -27f - y)));
                return White(Mathf.Max(body, Mathf.Max(wing, tail)));
            }), "UI_Plane", Vector4.zero);
            uiCross = SaveSprite(Shape(64, 64, (x, y) =>
            {   // a crosshair: ring, four ticks, a dot
                float d = Mathf.Sqrt(x * x + y * y), ax = Mathf.Abs(x), ay = Mathf.Abs(y);
                float ring = Edge(Mathf.Abs(d - 21f) - 3f);
                float ticks = Mathf.Max(Edge(Mathf.Max(ax - 3f, Mathf.Max(13f - ay, ay - 30f))), Edge(Mathf.Max(ay - 3f, Mathf.Max(13f - ax, ax - 30f))));
                float dot = Edge(d - 4.5f);
                return White(Mathf.Max(ring, Mathf.Max(ticks, dot)));
            }), "UI_Cross", Vector4.zero);
            uiPlay = SaveSprite(Shape(64, 64, (x, y) =>
            {   // a play triangle, its point to the right, corners softened
                float px = x + 4f; float d = Mathf.Max(-24f - px, Mathf.Max(Mathf.Abs(y) - (24f - (px + 24f) * 0.5f) + 1f, px - 24f));
                return White(Edge(d - 2f));
            }), "UI_Play", Vector4.zero);
            Func<float, float, float> speaker = (x, y) =>
            {   // a speaker: the driver box and its cone, from the left of the tile
                float box = RoundBox(x + 18f, y, 6f, 8f, 1.5f);
                float cone = Mathf.Max(-x - 14f, Mathf.Max(Mathf.Abs(y) - (7f + (x + 14f) * 0.8f), x - 2f));
                return Mathf.Max(Edge(box), Edge(cone));
            };
            uiSoundOn = SaveSprite(Shape(64, 64, (x, y) =>
            {   // the speaker and two arcs of sound to its right
                float d = Mathf.Sqrt((x - 2f) * (x - 2f) + y * y), a = Mathf.Abs(Mathf.Atan2(y, x - 2f));
                float arcs = a < 0.8f ? Mathf.Max(Edge(Mathf.Abs(d - 12f) - 2.2f), Edge(Mathf.Abs(d - 21f) - 2.2f)) : 0f;
                return White(Mathf.Max(speaker(x, y), arcs));
            }), "UI_SoundOn", Vector4.zero);
            uiSoundOff = SaveSprite(Shape(64, 64, (x, y) =>
            {   // the speaker and a cross where the sound would be
                float cx = x - 14f; float cross = Mathf.Max(Edge(Mathf.Abs(cx - y) * 0.7071f - 2.2f) * Edge(Mathf.Max(Mathf.Abs(cx), Mathf.Abs(y)) - 9f), Edge(Mathf.Abs(cx + y) * 0.7071f - 2.2f) * Edge(Mathf.Max(Mathf.Abs(cx), Mathf.Abs(y)) - 9f));
                return White(Mathf.Max(speaker(x, y), cross));
            }), "UI_SoundOff", Vector4.zero);
        }

        const float SkyRotation = 120f;   // the Kloofendal sky again (2026-09-19): its blue, sun-lit cumulus side ahead (90 framed the Belfast sunset on 2026-09-18)   // turns the HDRI so the dark cloud roof fills the view with the sunset glow low on the right (0 = grey mass ahead, 105-180 = the bare sun: washed out), over the enemies (the Belfast sky; 120 put the Kloofendal sky's blue cumulus side ahead)

        /// <summary>The sky HDRI (Assets/_Game/Art/Sky): imported as a lat-long HDR texture for the panoramic skybox. Null if the file is missing.</summary>
        static Texture2D ImportSkyHdri(string path)
        {
            if (!File.Exists(path)) { Debug.LogWarning("[SkySquad] sky HDRI missing at " + path + " - using the procedural sky"); return null; }
            var imp = AssetImporter.GetAtPath(path) as TextureImporter;
            if (imp == null) { AssetDatabase.ImportAsset(path); imp = AssetImporter.GetAtPath(path) as TextureImporter; }
            if (imp != null)
            {
                bool dirty = imp.textureShape != TextureImporterShape.Texture2D || imp.maxTextureSize != 4096 || imp.wrapModeU != TextureWrapMode.Repeat || imp.wrapModeV != TextureWrapMode.Clamp || imp.mipmapEnabled != true || imp.filterMode != FilterMode.Trilinear;
                if (dirty)
                {
                    imp.textureShape = TextureImporterShape.Texture2D; imp.textureType = TextureImporterType.Default; imp.sRGBTexture = false;
                    imp.maxTextureSize = 4096; imp.mipmapEnabled = true; imp.filterMode = FilterMode.Trilinear; imp.anisoLevel = 4;
                    imp.wrapModeU = TextureWrapMode.Repeat; imp.wrapModeV = TextureWrapMode.Clamp;
                    imp.textureCompression = TextureImporterCompression.CompressedHQ;
                    imp.SaveAndReimport();
                }
            }
            return AssetDatabase.LoadAssetAtPath<Texture2D>(path);
        }

        /// <summary>A cumulus puff: a flat-bottomed heap of round lobes, white on top shading to a pale blue-grey underside,
        /// with a soft edge and a little lumpy noise so no two clouds read as the same stamp when scaled and flipped.</summary>
        static Texture2D CloudTexture()
        {
            int w = 512, h = 256; var t = new Texture2D(w, h, TextureFormat.RGBA32, false);
            var lobes = new[] { new Vector3(120, 118, 70), new Vector3(210, 150, 92), new Vector3(300, 160, 84), new Vector3(385, 122, 68), new Vector3(165, 92, 60), new Vector3(255, 96, 66), new Vector3(340, 92, 58), new Vector3(90, 82, 42), new Vector3(420, 84, 44), new Vector3(240, 195, 48) };
            for (int y = 0; y < h; y++) for (int x = 0; x < w; x++)
                {
                    float a = 0f;
                    foreach (var b in lobes) { float d = Vector2.Distance(new Vector2(x, y), new Vector2(b.x, b.y)) / b.z; a = Mathf.Max(a, Mathf.Clamp01(1f - d * d)); }
                    a *= Mathf.Clamp01((y - 40f) / 18f);                                            // a flat-ish base
                    a += 0.06f * Mathf.Sin(x * 0.19f) * Mathf.Sin(y * 0.23f + x * 0.05f);          // lumpy edge
                    a = Mathf.SmoothStep(0.08f, 0.85f, a);
                    float light = Mathf.Clamp01((y - 50f) / 130f);                                  // sunlit top, shaded underside
                    var c = Color.Lerp(new Color(0.78f, 0.84f, 0.94f), Color.white, light);
                    t.SetPixel(x, y, new Color(c.r, c.g, c.b, a));
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
                prop = SaveMesh(MeshFactory.Propeller()), enemy = SaveMesh(MeshFactory.EnemyPlane()), boss = SaveMesh(MeshFactory.BossPlane()), boss2 = SaveMesh(MeshFactory.BossTwinBoom()), boss3 = SaveMesh(MeshFactory.BossFlyingWing()), boss4 = SaveMesh(MeshFactory.BossAirship()), zeppelin = SaveMesh(MeshFactory.Zeppelin()), crate = SaveMesh(MeshFactory.Crate()), boat = SaveMesh(MeshFactory.Boat()), boatWeapon = SaveMesh(MeshFactory.BoatWeapon()),
                rocket = SaveMesh(MeshFactory.Rocket()), buoy = SaveMesh(MeshFactory.Buoy()), bullet = SaveMesh(MeshFactory.Bullet()), coin = SaveMesh(MeshFactory.Coin()), sea = SaveMesh(MeshFactory.SeaGrid()),
                gateFrame = SaveMesh(MeshFactory.GateFrame(2.2f, 3.4f)), gatePanel = SaveMesh(MeshFactory.Panel(2.2f, 3.4f))   /* 1.5 x 2.4 for an hour on 2026-09-18 ("the green ones behind the box smaller", then "put them back to their original size") */
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
            var mats = new Material[Mathf.Max(1, mesh.subMeshCount)]; for (int i = 0; i < mats.Length; i++) mats[i] = outline;   // one per submesh, whatever the mesh has
            var o = MeshObj("Outline", mesh, body.transform, mats);
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

        /// <summary>The health bar over a boss's head, in place of the number (2026-09-18): a dark backing and a red fill
        /// that Enemy.SetHpBar scales from its left edge. Parented to the root, which never rotates, so it always faces the camera.</summary>
        static void BossHpBar(Enemy en, GameObject root, Mats M, float y, float width)
        {
            var bar = new GameObject("HpBar");
            bar.transform.SetParent(root.transform, false);
            bar.transform.localPosition = new Vector3(0f, y, 0f);
            GameObject Piece(string n, Material m, float h, float w, float z)
            {
                var b = GameObject.CreatePrimitive(PrimitiveType.Cube);
                UnityEngine.Object.DestroyImmediate(b.GetComponent<Collider>());
                b.name = n; b.transform.SetParent(bar.transform, false);
                b.transform.localPosition = new Vector3(0f, 0f, z);
                b.transform.localScale = new Vector3(w, h, 0.08f);
                var r = b.GetComponent<MeshRenderer>(); r.sharedMaterial = m; r.shadowCastingMode = ShadowCastingMode.Off;
                return b;
            }
            Piece("Bg", M.barBg, width * 0.155f, width * 1.06f, 0f);
            var ghost = Piece("Ghost", M.barGhost, width * 0.115f, width, -0.03f);   // between the backing and the fill
            var fill = Piece("Fill", M.barHp, width * 0.115f, width, -0.06f);        // in front of both: the camera looks down +z
            en.hpBarRoot = bar; en.hpBarFill = fill.transform; en.hpBarGhost = ghost.transform;
            en.hpBarFillRenderer = fill.GetComponent<MeshRenderer>(); en.hpBarWidth = width;
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
            root.transform.localScale = Vector3.one * 1.05f;   // bigger squad planes (was 0.8)
            var pv = root.AddComponent<PlaneVisual>();
            var bodyGo = MeshObj("Body", mesh, root.transform, body, accent, glass);
            Outline(bodyGo, mesh, M.outline, 1.06f);
            pv.bodyRenderer = bodyGo.GetComponent<Renderer>();
            if (prop) { var p = MeshObj("Propeller", propMesh, root.transform, M.prop, M.propDisc); p.transform.localPosition = new Vector3(0f, 0f, 0.78f); pv.propeller = p.transform;   /* just ahead of the cowl */ }
            var flash = GameObject.CreatePrimitive(PrimitiveType.Quad);
            UnityEngine.Object.DestroyImmediate(flash.GetComponent<Collider>());
            flash.name = "Flash"; flash.transform.SetParent(root.transform, false);
            flash.transform.localPosition = new Vector3(0f, 0.04f, 0.9f); flash.transform.localScale = Vector3.one * 0.35f;
            var fr = flash.GetComponent<MeshRenderer>(); fr.sharedMaterial = M.flash; fr.enabled = false; fr.shadowCastingMode = ShadowCastingMode.Off;
            pv.flashRenderer = fr;
            pv.leaderMaterial = M.leader;
            return SavePrefab(root, name);
        }

        /// <summary>
        /// A squad plane built around an imported Asset Store model (2026-09-18: "use this airplane instead of the airplane in my game":
        /// Zero Fighter for the Gatling, Aircraft C-130 for the Rockets, Space shuttle of the future for the Cannon).
        /// <paramref name="model"/> is the pack's prefab or FBX (<see cref="FindModel"/>); <paramref name="euler"/> turns it nose toward +Z
        /// (the squad flies along +Z, the flash sits on the nose), it is scaled to <paramref name="wingspan"/> units across and centred on the
        /// root. Built-in (Standard) materials are copied to URP Lit so the pack renders under URP. Propellers are any child named "prop…"
        /// (all of them spin: the C-130 has four). Falls back to the procedural plane when the pack has not been imported yet.
        /// </summary>
        static GameObject ModelPlanePrefab(string name, GameObject model, Vector3 euler, float wingspan, float maxLength, Vector3 propAxis, string[] drop, Mats M, Func<GameObject> fallback)
        {
            if (model == null) { Debug.LogWarning(name + ": Asset Store model not found, using the procedural plane"); return fallback(); }
            var root = new GameObject(name);
            root.transform.localScale = Vector3.one * 1.05f;   // same root scale as the procedural planes (the formation is tuned to it)
            var pv = root.AddComponent<PlaneVisual>();
            var body = AssetDatabase.Contains(model) ? (GameObject)PrefabUtility.InstantiatePrefab(model) : model;   // a pack prefab, or an assembly built in code (AssembleC130)
            if (PrefabUtility.IsPartOfPrefabInstance(body)) PrefabUtility.UnpackPrefabInstance(body, PrefabUnpackMode.Completely, InteractionMode.AutomatedAction);   // self-contained: the saved prefab references the pack's meshes only
            body.name = "Body";
            body.transform.SetParent(root.transform, false);
            body.transform.localRotation = Quaternion.Euler(euler);
            body.transform.localPosition = Vector3.zero; body.transform.localScale = Vector3.one;
            // strip the pack's demo extras: landing gear / exhaust FX by name, then every script, animator, light, sound and collider
            foreach (var t in body.GetComponentsInChildren<Transform>(true)) if (t != null && t != body.transform && Array.IndexOf(drop, t.name) >= 0) UnityEngine.Object.DestroyImmediate(t.gameObject);
            foreach (var c in body.GetComponentsInChildren<MonoBehaviour>(true)) if (c != null) UnityEngine.Object.DestroyImmediate(c);
            foreach (var an in body.GetComponentsInChildren<Animator>(true)) UnityEngine.Object.DestroyImmediate(an);   // a pack's demo animation must not fight PlaneVisual
            foreach (var l in body.GetComponentsInChildren<Light>(true)) UnityEngine.Object.DestroyImmediate(l);
            foreach (var a in body.GetComponentsInChildren<AudioSource>(true)) UnityEngine.Object.DestroyImmediate(a);
            foreach (var c in body.GetComponentsInChildren<Collider>(true)) UnityEngine.Object.DestroyImmediate(c);
            var rends = body.GetComponentsInChildren<Renderer>(true);
            if (rends.Length == 0) { UnityEngine.Object.DestroyImmediate(root); Debug.LogWarning(name + ": the model has no renderers, using the procedural plane"); return fallback(); }
            // fit: measure in root space (after the rotation), scale to the wingspan (but no longer than maxLength: the formation rows are 0.9 apart), centre on the root
            Bounds b = RootBounds(root.transform, rends);
            float k = Mathf.Min(wingspan / Mathf.Max(0.001f, b.size.x), maxLength / Mathf.Max(0.001f, b.size.z));
            body.transform.localScale = Vector3.one * k;
            b = RootBounds(root.transform, rends);
            body.transform.localPosition = -b.center;
            b = RootBounds(root.transform, rends);
            // materials: Built-in shaders are pink under URP; copy them to URP Lit (once, under Generated/Materials)
            Renderer biggest = null; float bestVol = -1f;
            foreach (var r in rends)
            {
                var mats = r.sharedMaterials;
                for (int i = 0; i < mats.Length; i++) mats[i] = UrpCopy(mats[i]);
                r.sharedMaterials = mats;
                r.shadowCastingMode = ShadowCastingMode.On; r.receiveShadows = true;
                float vol = r.bounds.size.x * r.bounds.size.y * r.bounds.size.z;
                if (vol > bestVol) { bestVol = vol; biggest = r; }
                var mf = r.GetComponent<MeshFilter>();
                if (mf != null && mf.sharedMesh != null && r is MeshRenderer)
                {   // toon outline like the procedural planes; only on parts whose pivot is near their centre (the inverted hull grows about the pivot)
                    var mb = mf.sharedMesh.bounds;
                    if (mb.center.magnitude < 0.35f * mb.size.magnitude) Outline(r.gameObject, mf.sharedMesh, M.outline, 1.04f);
                }
            }
            pv.bodyRenderer = biggest;
            var props = new List<Transform>();
            foreach (var t in body.GetComponentsInChildren<Transform>(true)) if (t != body.transform && t.name.IndexOf("prop", StringComparison.OrdinalIgnoreCase) >= 0 && (t.parent == null || t.parent.name.IndexOf("prop", StringComparison.OrdinalIgnoreCase) < 0)) props.Add(t);
            pv.propellers = props.ToArray(); pv.propellerAxis = propAxis;
            var flash = GameObject.CreatePrimitive(PrimitiveType.Quad);
            UnityEngine.Object.DestroyImmediate(flash.GetComponent<Collider>());
            flash.name = "Flash"; flash.transform.SetParent(root.transform, false);
            flash.transform.localPosition = new Vector3(0f, 0.04f, b.max.z + 0.05f); flash.transform.localScale = Vector3.one * 0.35f;   // on the nose
            var fr = flash.GetComponent<MeshRenderer>(); fr.sharedMaterial = M.flash; fr.enabled = false; fr.shadowCastingMode = ShadowCastingMode.Off;
            pv.flashRenderer = fr;
            pv.leaderMaterial = M.leader;
            return SavePrefab(root, name);
        }
        /// <summary>
        /// The Aircraft C-130 pack ships its parts as separate prefabs and only its demo scene puts them together; this rebuilds that
        /// assembly (the demo's transforms, nose toward +Z): fuselage turned (0, 90, 90), four motors with a "paddle" propeller each
        /// (spinning about their local Y), the nose radome and the cockpit glass. Null when the pack is not imported.
        /// </summary>
        static GameObject AssembleC130()
        {
            const string dir = "Assets/Aircraft C-130/Prefabs/";
            var fuselage = AssetDatabase.LoadAssetAtPath<GameObject>(dir + "C130Air.prefab");
            if (fuselage == null) return null;
            var motor = AssetDatabase.LoadAssetAtPath<GameObject>(dir + "MotorC130.prefab");
            var paddle = AssetDatabase.LoadAssetAtPath<GameObject>(dir + "paddle .prefab");
            var sphere = AssetDatabase.LoadAssetAtPath<GameObject>(dir + "SphereC130.prefab");
            var glass = AssetDatabase.LoadAssetAtPath<GameObject>(dir + "Glass.prefab");
            var root = new GameObject("C130");
            Func<GameObject, string, Transform, Vector3, Vector3, Vector3, GameObject> put = (prefab, n, parent, pos, rot, scl) =>
            {
                if (prefab == null) return null;
                var go = (GameObject)PrefabUtility.InstantiatePrefab(prefab);
                PrefabUtility.UnpackPrefabInstance(go, PrefabUnpackMode.Completely, InteractionMode.AutomatedAction);
                go.name = n; go.transform.SetParent(parent, false);
                go.transform.localPosition = pos; go.transform.localEulerAngles = rot; go.transform.localScale = scl;
                return go;
            };
            put(fuselage, "Fuselage", root.transform, Vector3.zero, new Vector3(0f, 90f, 90f), Vector3.one);
            var motorX = new[] { -5.6f, -2.59f, 2.95f, 5.91f }; var motorY = new[] { -0.14f, -0.14f, -0.21f, -0.05f };
            for (int i = 0; i < 4; i++)
            {
                var m = put(motor, "Motor" + (i + 1), root.transform, new Vector3(motorX[i], motorY[i], 0.19f), new Vector3(0f, 90f, 90f), Vector3.one);
                if (m != null) put(paddle, "Propeller" + (i + 1), m.transform, new Vector3(-0.14f, 0.97f, -0.03f), Vector3.zero, Vector3.one);
            }
            put(sphere, "Nose", root.transform, new Vector3(0.01f, -0.21f, 5.03f), Vector3.zero, Vector3.one * 0.8f);
            put(glass, "Glass", root.transform, new Vector3(-0.39f, 0.63f, 4.46f), new Vector3(17.19f, 0f, 0f), new Vector3(0.8f, 0.7f, 0.8f));
            return root;
        }
        static Bounds RootBounds(Transform root, Renderer[] rends)
        {
            var b = new Bounds(); bool first = true;
            foreach (var r in rends)
            {
                var mf = r.GetComponent<MeshFilter>(); var smr = r as SkinnedMeshRenderer;
                Mesh mesh = mf != null ? mf.sharedMesh : smr != null ? smr.sharedMesh : null;
                if (mesh == null) continue;
                var mb = mesh.bounds; var l2r = root.worldToLocalMatrix * r.transform.localToWorldMatrix;
                for (int i = 0; i < 8; i++)
                {
                    var corner = mb.center + Vector3.Scale(mb.extents, new Vector3((i & 1) == 0 ? -1f : 1f, (i & 2) == 0 ? -1f : 1f, (i & 4) == 0 ? -1f : 1f));
                    var p = l2r.MultiplyPoint3x4(corner);
                    if (first) { b = new Bounds(p, Vector3.zero); first = false; } else b.Encapsulate(p);
                }
            }
            return b;
        }
        /// <summary>The pack's material, or a URP Lit copy of it (saved once as Generated/Materials/Imported_&lt;name&gt;) when it uses a Built-in shader.</summary>
        static Material UrpCopy(Material src)
        {
            if (src == null || src.shader == null) return src;
            string sn = src.shader.name;
            if (sn.StartsWith("Universal Render Pipeline") || sn.StartsWith("Shader Graphs") || sn.StartsWith("TextMeshPro")) return src;
            string path = Gen + "/Materials/Imported_" + src.name + ".mat";
            var m = AssetDatabase.LoadAssetAtPath<Material>(path);
            bool transparent = sn.IndexOf("Transparent", StringComparison.OrdinalIgnoreCase) >= 0 || sn.IndexOf("Glass", StringComparison.OrdinalIgnoreCase) >= 0 || (src.HasProperty("_Mode") && src.GetFloat("_Mode") >= 2f);
            var sh = Shader.Find("Universal Render Pipeline/Lit");
            if (m == null) { m = new Material(sh); AssetDatabase.CreateAsset(m, path); } else m.shader = sh;
            var tex = src.HasProperty("_MainTex") ? src.GetTexture("_MainTex") : src.mainTexture;
            if (tex != null) { m.SetTexture("_BaseMap", tex); if (src.HasProperty("_MainTex")) { m.SetTextureScale("_BaseMap", src.GetTextureScale("_MainTex")); m.SetTextureOffset("_BaseMap", src.GetTextureOffset("_MainTex")); } }
            m.SetColor("_BaseColor", src.HasProperty("_Color") ? src.GetColor("_Color") : Color.white);
            if (src.HasProperty("_BumpMap") && src.GetTexture("_BumpMap") != null) { m.SetTexture("_BumpMap", src.GetTexture("_BumpMap")); m.EnableKeyword("_NORMALMAP"); }
            if (src.HasProperty("_MetallicGlossMap") && src.GetTexture("_MetallicGlossMap") != null) { m.SetTexture("_MetallicGlossMap", src.GetTexture("_MetallicGlossMap")); m.EnableKeyword("_METALLICSPECGLOSSMAP"); }
            if (src.HasProperty("_EmissionMap") && src.GetTexture("_EmissionMap") != null) { m.SetTexture("_EmissionMap", src.GetTexture("_EmissionMap")); m.SetColor("_EmissionColor", src.HasProperty("_EmissionColor") ? src.GetColor("_EmissionColor") : Color.white); m.EnableKeyword("_EMISSION"); }
            m.SetFloat("_Metallic", src.HasProperty("_Metallic") ? Mathf.Min(0.2f, src.GetFloat("_Metallic")) : 0f);   // capped: the C-130 ships at metallic 1 and renders black without reflections
            m.SetFloat("_Smoothness", src.HasProperty("_Glossiness") ? Mathf.Min(0.6f, src.GetFloat("_Glossiness")) : 0.35f);   // capped: a glossy pack looks plastic next to the flat-shaded game
            if (transparent) { m.SetFloat("_Surface", 1f); m.SetFloat("_Blend", 0f); m.SetOverrideTag("RenderType", "Transparent"); m.renderQueue = (int)RenderQueue.Transparent; m.SetInt("_SrcBlend", (int)BlendMode.SrcAlpha); m.SetInt("_DstBlend", (int)BlendMode.OneMinusSrcAlpha); m.SetInt("_ZWrite", 0); m.EnableKeyword("_SURFACE_TYPE_TRANSPARENT"); }
            EditorUtility.SetDirty(m);
            return m;
        }
        /// <summary>The first prefab (else FBX) whose path contains every keyword, outside _Game (the Asset Store packs import at the Assets root).</summary>
        static GameObject FindModel(params string[] keywords)
        {
            GameObject best = null; int bestScore = int.MinValue;
            foreach (var g in AssetDatabase.FindAssets("t:Prefab t:Model"))
            {
                string p = AssetDatabase.GUIDToAssetPath(g);
                if (p.StartsWith(Root) || !p.StartsWith("Assets/")) continue;
                string lp = p.ToLowerInvariant();
                bool ok = true; foreach (var k in keywords) if (lp.IndexOf(k.ToLowerInvariant()) < 0) { ok = false; break; }
                if (!ok) continue;
                int score = (lp.EndsWith(".prefab") ? 100 : 0) - p.Length;   // a ready prefab (materials assigned) over the raw FBX; the shortest path over demo variants
                if (score > bestScore) { var go = AssetDatabase.LoadAssetAtPath<GameObject>(p); if (go != null && go.GetComponentInChildren<Renderer>(true) != null) { best = go; bestScore = score; } }
            }
            return best;
        }
        static Mesh GetMesh(string name) => AssetDatabase.LoadAssetAtPath<Mesh>(Gen + "/Meshes/" + name + ".asset");

        static GameObject EnemyPrefab(string name, Mesh mesh, Mesh propMesh, Mats M, bool boss, Material glow, params Material[] mats)
        {
            var root = new GameObject(name);
            var en = root.AddComponent<Enemy>();
            var body = MeshObj("Body", mesh, root.transform, mats);
            body.transform.localRotation = Quaternion.Euler(0f, 180f, 0f); // nose toward the player; EnemyKindDef.scale is applied at runtime
            Outline(body, mesh, M.outline, 1.1f);   // a bit heavier than the squad's: the enemy must read at distance
            en.model = body.transform;
            en.bodyRenderer = body.GetComponent<Renderer>();
            var prop = MeshObj("Propeller", propMesh, body.transform, M.prop, M.propDisc); prop.transform.localPosition = new Vector3(0f, 0f, 1.03f);   /* just ahead of the cowl */ en.propeller = prop.transform;
            var flash = GameObject.CreatePrimitive(PrimitiveType.Quad); UnityEngine.Object.DestroyImmediate(flash.GetComponent<Collider>());
            flash.name = "Flash"; flash.transform.SetParent(body.transform, false);
            flash.transform.localPosition = new Vector3(0f, -0.05f, 1.12f); flash.transform.localRotation = Quaternion.Euler(0f, 180f, 0f); flash.transform.localScale = Vector3.one * 0.6f;
            var fr = flash.GetComponent<MeshRenderer>(); fr.sharedMaterial = glow != null ? glow : M.flash; fr.enabled = false; fr.shadowCastingMode = ShadowCastingMode.Off;
            en.flashRenderer = fr;
            if (!boss)
            {   // a fighter streams dark smoke on its strike run (Enemy turns it on when it commits)
                var trailGo = new GameObject("Trail"); trailGo.transform.SetParent(body.transform, false); trailGo.transform.localPosition = new Vector3(0f, 0.05f, -0.8f);
                var tr = trailGo.AddComponent<TrailRenderer>();
                tr.sharedMaterial = M.tracer; tr.time = 0.5f; tr.startWidth = 0.34f; tr.endWidth = 0.03f; tr.minVertexDistance = 0.06f; tr.emitting = false; tr.shadowCastingMode = ShadowCastingMode.Off;
                tr.startColor = new Color(1f, 0.62f, 0.3f, 0.95f); tr.endColor = new Color(0.75f, 0.75f, 0.8f, 0f);   // hot at the tail, fading to pale smoke: reads against the sea
                en.trail = tr;
            }
            // the hp over its head: a boss shows his all the time, a fighter only once it has been hit (Enemy.Init / TakeDamage: "I want its hp to show above it when I shoot it", 2026-09-16)
            en.hpLabel = boss ? Label3D("HpLabel", root.transform, new Vector3(0f, 3.62f, 0f), 10f, Color.white, fontOutline)   // a boss's number rides above his bar (2026-09-18)
                              : Label3D("HpLabel", root.transform, new Vector3(0f, 1.25f, 0f), 6f, Color.white, fontOutline);
            if (boss) BossHpBar(en, root, M, 2.8f, 3.6f);
            return SavePrefab(root, name);
        }

        // ----------------------------------------------------------- the OH-1 Ninja enemy (2026-09-18: "I want the enemy planes to be the OH-1 Ninja JGSDF")
        const string OH1Pack = "Assets/OH-1_Complex/Prefabs/metallic/OH-1.prefab";
        const string OH1Low = Root + "/Art/Enemies/OH1_Ninja_low.prefab";
        /// <summary>
        /// The light OH-1: the pack's helicopter is ~200k vertices (cockpit interior, pilots, lights, 9k-shard rotor blades) and the swarm shows
        /// 40-60 at once, so this keeps the outer shell only (fuselage, glass, doors, rotor hub, tail rotor, fixed gear; ~3.8k triangles) with each
        /// part decimated by UnityMeshSimplifier (git package com.whinarn.unitymeshsimplifier) at the pack prefab's own transforms. Generated once
        /// into Art/Enemies (prefab + a mesh container) and reused after: the 836 MB pack itself stays out of git. Null when neither exists.
        /// </summary>
        static GameObject EnsureOH1Low()
        {
            var low = AssetDatabase.LoadAssetAtPath<GameObject>(OH1Low);
            if (low != null) return low;
            var pack = AssetDatabase.LoadAssetAtPath<GameObject>(OH1Pack);
            if (pack == null) { Debug.LogWarning("[SkySquad] neither " + OH1Low + " nor the OH-1 pack is present: the enemy stays the procedural fighter"); return null; }
            var budget = new Dictionary<string, int> {
                { "Fuselage", 2600 }, { "Glass", 160 }, { "Door_1", 140 }, { "Door_2", 140 }, { "Door_1_Glass", 40 }, { "Door_2_Glass", 40 },
                { "Rotor", 260 }, { "Tail_Rotor", 60 }, { "Tail_Rotor_Blades", 90 },
                { "Left_Gear_1", 120 }, { "Left_Wheel", 60 }, { "Right_Gear_2 1", 120 }, { "Right_Wheel", 60 }, { "Camera_Base", 40 }, { "Camera", 40 } };
            var go = (GameObject)PrefabUtility.InstantiatePrefab(pack);
            PrefabUtility.UnpackPrefabInstance(go, PrefabUnpackMode.Completely, InteractionMode.AutomatedAction);
            foreach (var c in go.GetComponentsInChildren<Component>(true)) if (c is Animator || c is MonoBehaviour || c is Light || c is AudioSource || c is Collider) UnityEngine.Object.DestroyImmediate(c);
            var all = go.GetComponentsInChildren<Transform>(true);
            var keep = new HashSet<Transform>();
            foreach (var t in all) if (budget.ContainsKey(t.name) && t.GetComponent<MeshFilter>() != null) { var q = t; while (q != null) { keep.Add(q); q = q.parent; } }
            foreach (var t in all) if (t != null && !keep.Contains(t)) UnityEngine.Object.DestroyImmediate(t.gameObject);
            foreach (var t in go.GetComponentsInChildren<Transform>(true)) if (!budget.ContainsKey(t.name)) { var mr = t.GetComponent<Renderer>(); var mf = t.GetComponent<MeshFilter>(); if (mr != null) UnityEngine.Object.DestroyImmediate(mr); if (mf != null) UnityEngine.Object.DestroyImmediate(mf); }   // a kept ancestor that is not itself a kept part draws nothing
            string meshPath = Root + "/Art/Enemies/OH1_Ninja_low_meshes.asset";
            AssetDatabase.DeleteAsset(meshPath);
            Mesh first = null; int total = 0;
            foreach (var mf in go.GetComponentsInChildren<MeshFilter>(true))
            {
                var src = mf.sharedMesh; if (src == null) continue;
                int tris = src.triangles.Length / 3, want = budget[mf.name];
                Mesh m;
                if (tris > want)
                {
                    // the defaults protect borders / UV seams and stop early on these dense scans (the fuselage stayed at 10k): let them go and take a few passes
                    var opts = UnityMeshSimplifier.SimplificationOptions.Default;
                    opts.PreserveBorderEdges = false; opts.PreserveUVSeamEdges = false; opts.PreserveUVFoldoverEdges = false; opts.PreserveSurfaceCurvature = false; opts.EnableSmartLink = true; opts.MaxIterationCount = 200; opts.Agressiveness = 7.0;   /* 12 with a 0.02 link distance glued the scan together: 69k triangles in 165 s */
                    Mesh cur = src;
                    for (int pass = 0; pass < 5 && cur.triangles.Length / 3 > want * 1.15f; pass++)
                    {
                        var s = new UnityMeshSimplifier.MeshSimplifier(); s.SimplificationOptions = opts; s.Initialize(cur); s.SimplifyMesh(want / (float)(cur.triangles.Length / 3));
                        var next = s.ToMesh(); if (next.triangles.Length >= cur.triangles.Length) break; cur = next;
                    }
                    m = cur == src ? UnityEngine.Object.Instantiate(src) : cur;
                }
                else m = UnityEngine.Object.Instantiate(src);
                m.name = "OH1_" + mf.name; m.RecalculateBounds(); total += m.triangles.Length / 3;
                if (first == null) { AssetDatabase.CreateAsset(m, meshPath); first = m; } else AssetDatabase.AddObjectToAsset(m, meshPath);
                mf.sharedMesh = m;
            }
            AssetDatabase.SaveAssets();
            low = PrefabUtility.SaveAsPrefabAsset(go, OH1Low);
            UnityEngine.Object.DestroyImmediate(go);
            Debug.Log("[SkySquad] built " + OH1Low + " from the OH-1 pack: " + total + " triangles");
            return low;
        }
        static Transform FindDeep(Transform t, string name) { if (t.name == name) return t; foreach (Transform c in t) { var r = FindDeep(c, name); if (r != null) return r; } return null; }
        /// <summary>
        /// The enemy fighter as the light OH-1 (EnsureOH1Low): the pack's nose is -Z, so the helicopter sits turned 180 inside the "Body" that
        /// Enemy turns toward the player; fitted to 3.3 long (rotor disc ~2.8 across, the procedural fighter was 2.4 wide; EnemyKindDef.scale
        /// 0.72 still applies at runtime), centred. The rotor hub spins as `propeller` with the game's prop disc scaled to the pack's 11.5 m rotor
        /// (its shard blades are gone), the tail rotor spins through a pivot whose Z is the hub axis, toon outline per part, the chin-gun flash at
        /// the nose, the strike-run smoke at the tail, the HP label overhead. Falls back to the procedural fighter without the low model.
        /// </summary>
        static GameObject OH1EnemyPrefab(string name, GameObject low, Mesh propMesh, Mats M, Func<GameObject> fallback)
        {
            if (low == null) return fallback();
            var root = new GameObject(name);
            var en = root.AddComponent<Enemy>();
            var body = new GameObject("Body"); body.transform.SetParent(root.transform, false);
            en.model = body.transform;
            var heli = (GameObject)PrefabUtility.InstantiatePrefab(low);
            PrefabUtility.UnpackPrefabInstance(heli, PrefabUnpackMode.Completely, InteractionMode.AutomatedAction);
            heli.name = "OH1"; heli.transform.SetParent(body.transform, false);
            heli.transform.localRotation = Quaternion.Euler(0f, 180f, 0f);
            var rends = heli.GetComponentsInChildren<Renderer>(true);
            Renderer biggest = null; float bestVol = -1f;
            foreach (var r in rends)
            {
                var mats = r.sharedMaterials;
                for (int i = 0; i < mats.Length; i++) mats[i] = mats[i] != null && mats[i].name.StartsWith("Glass") ? M.oh1Glass : M.oh1Body;
                r.sharedMaterials = mats; r.shadowCastingMode = ShadowCastingMode.On; r.receiveShadows = true;
            }
            Bounds b = RootBounds(body.transform, rends);
            float k = 3.3f / Mathf.Max(0.001f, b.size.z);
            heli.transform.localScale = Vector3.one * k;
            b = RootBounds(body.transform, rends); heli.transform.localPosition = -b.center; b = RootBounds(body.transform, rends);
            foreach (var r in rends)
            {
                float vol = r.bounds.size.x * r.bounds.size.y * r.bounds.size.z; if (vol > bestVol) { bestVol = vol; biggest = r; }
                var mf = r.GetComponent<MeshFilter>(); if (mf != null && mf.sharedMesh != null && r.name == "Fuselage") Outline(r.gameObject, mf.sharedMesh, M.outline, 1.08f);   // the fuselage only: the silhouette, at a third of the cost
            }
            en.bodyRenderer = biggest;
            var rotor = FindDeep(heli.transform, "Rotor");
            if (rotor != null)
            {
                var disc = MeshObj("RotorDisc", propMesh, rotor, M.propDisc, M.propDisc);   // both submeshes translucent: at 18x the prop's blades read as a black cross, a blur disc is what a running rotor looks like
                disc.transform.localPosition = new Vector3(0f, 0f, 0.35f); disc.transform.localScale = Vector3.one * (11.5f / 0.62f);   // the pack's blade span over the prop mesh's 0.62
                var dr = disc.GetComponent<MeshRenderer>(); dr.shadowCastingMode = ShadowCastingMode.Off;
                en.propeller = rotor;   // Enemy spins it on local Z = the pack's mast axis
            }
            var tail = FindDeep(heli.transform, "Tail_Rotor");
            if (tail != null)
            {
                var pivot = new GameObject("TailRotorPivot").transform; pivot.SetParent(tail.parent, false);
                pivot.localPosition = tail.localPosition; pivot.localRotation = tail.localRotation * Quaternion.Euler(0f, 90f, 0f); pivot.localScale = tail.localScale;   // pivot Z = the hub's local X (the blades' thin axis)
                tail.SetParent(pivot, true);
                en.propellers = new[] { pivot };
            }
            var flash = GameObject.CreatePrimitive(PrimitiveType.Quad); UnityEngine.Object.DestroyImmediate(flash.GetComponent<Collider>());
            flash.name = "Flash"; flash.transform.SetParent(body.transform, false);
            flash.transform.localPosition = new Vector3(0f, -0.12f, b.max.z + 0.05f); flash.transform.localRotation = Quaternion.Euler(0f, 180f, 0f); flash.transform.localScale = Vector3.one * 0.6f;
            var fr = flash.GetComponent<MeshRenderer>(); fr.sharedMaterial = M.flash; fr.enabled = false; fr.shadowCastingMode = ShadowCastingMode.Off;
            en.flashRenderer = fr;
            var trailGo = new GameObject("Trail"); trailGo.transform.SetParent(body.transform, false); trailGo.transform.localPosition = new Vector3(0f, 0.1f, b.min.z + 0.3f);
            var tr = trailGo.AddComponent<TrailRenderer>();
            tr.sharedMaterial = M.tracer; tr.time = 0.5f; tr.startWidth = 0.34f; tr.endWidth = 0.03f; tr.minVertexDistance = 0.06f; tr.emitting = false; tr.shadowCastingMode = ShadowCastingMode.Off;
            tr.startColor = new Color(1f, 0.62f, 0.3f, 0.95f); tr.endColor = new Color(0.75f, 0.75f, 0.8f, 0f);
            en.trail = tr;
            en.hpLabel = Label3D("HpLabel", root.transform, new Vector3(0f, 1.4f, 0f), 6f, Color.white, fontOutline);
            return SavePrefab(root, name);
        }

        // ----------------------------------------------------------- the Sparrow boss (2026-09-18: "every boss a different colour, use the SPARROW Fighter Spacecraft for the bosses")
        const string SparrowFbx = "Assets/Sparrow_Fighter/Meshes/Sparrow_grey.FBX";
        const string SparrowLow = Root + "/Art/Enemies/Sparrow_low.asset";
        /// <summary>The Sparrow mesh decimated to ~6k triangles (from 24k) with UnityMeshSimplifier, generated once into Art/Enemies and reused
        /// (the 840 MB pack stays out of git). Null when neither exists.</summary>
        static Mesh EnsureSparrowLow()
        {
            var low = AssetDatabase.LoadAssetAtPath<Mesh>(SparrowLow);
            if (low != null) return low;
            var fbx = AssetDatabase.LoadAssetAtPath<GameObject>(SparrowFbx);
            var mf = fbx != null ? fbx.GetComponentInChildren<MeshFilter>() : null;
            if (mf == null || mf.sharedMesh == null) { Debug.LogWarning("[SkySquad] neither " + SparrowLow + " nor the Sparrow pack is present: the bosses stay the procedural planes"); return null; }
            var src = mf.sharedMesh; int want = 6000;
            var opts = UnityMeshSimplifier.SimplificationOptions.Default;
            opts.PreserveBorderEdges = false; opts.PreserveUVSeamEdges = false; opts.PreserveUVFoldoverEdges = false; opts.PreserveSurfaceCurvature = false; opts.EnableSmartLink = true; opts.MaxIterationCount = 200; opts.Agressiveness = 7.0;
            Mesh cur = src;
            for (int pass = 0; pass < 5 && cur.triangles.Length / 3 > want * 1.15f; pass++)
            {
                var s = new UnityMeshSimplifier.MeshSimplifier(); s.SimplificationOptions = opts; s.Initialize(cur); s.SimplifyMesh(want / (float)(cur.triangles.Length / 3));
                var next = s.ToMesh(); if (next.triangles.Length >= cur.triangles.Length) break; cur = next;
            }
            var m = cur == src ? UnityEngine.Object.Instantiate(src) : cur;
            m.name = "Sparrow_low"; m.RecalculateBounds();
            AssetDatabase.CreateAsset(m, SparrowLow); AssetDatabase.SaveAssets();
            Debug.Log("[SkySquad] built " + SparrowLow + ": " + m.triangles.Length / 3 + " triangles");
            return m;
        }
        /// <summary>
        /// The boss as the Sparrow: one mesh (nose +Z like the procedural bosses, so BossPrefab's 180° turn applies), fitted 2.6 wide (the old
        /// gunship was 2.36; EnemyKindDef.scale 3.2 still applies), centred, toon outline, the muzzle flash ahead of the nose, the HP label overhead.
        /// The grey pack texture is the base; WaveSpawner tints every boss its own colour (Enemy.SetTint). No propellers: it is a spacecraft.
        /// </summary>
        static GameObject SparrowBossPrefab(string name, Mesh mesh, Mats M)
        {
            var root = new GameObject(name);
            var en = root.AddComponent<Enemy>();
            var body = new GameObject("Body"); body.transform.SetParent(root.transform, false);
            body.transform.localRotation = Quaternion.Euler(0f, 180f, 0f);   // nose toward the player, as the procedural bosses
            en.model = body.transform;
            float k = 2.6f / Mathf.Max(0.001f, mesh.bounds.size.x);
            var ship = MeshObj("Ship", mesh, body.transform, M.sparrowBody);
            ship.transform.localScale = Vector3.one * k; ship.transform.localPosition = -mesh.bounds.center * k;
            Outline(ship, mesh, M.outline, 1.04f);
            en.bodyRenderer = ship.GetComponent<Renderer>();
            float halfLen = mesh.bounds.size.z * k * 0.5f;
            var flash = GameObject.CreatePrimitive(PrimitiveType.Quad); UnityEngine.Object.DestroyImmediate(flash.GetComponent<Collider>());
            flash.name = "Flash"; flash.transform.SetParent(body.transform, false);
            flash.transform.localPosition = new Vector3(0f, -0.1f, halfLen + 0.15f); flash.transform.localRotation = Quaternion.Euler(0f, 180f, 0f); flash.transform.localScale = Vector3.one * 0.7f;
            var fr = flash.GetComponent<MeshRenderer>(); fr.sharedMaterial = M.bossFlash; fr.enabled = false; fr.shadowCastingMode = ShadowCastingMode.Off;
            en.flashRenderer = fr;
            en.hpLabel = Label3D("HpLabel", root.transform, new Vector3(0f, 3.62f, 0f), 10f, Color.white, fontOutline);   // his number rides above the bar (2026-09-18)
            BossHpBar(en, root, M, 2.8f, 3.6f);
            return SavePrefab(root, name);
        }
        /// <summary>One vivid colour per boss (the seven bosses of a run), multiplied over the dark grey Sparrow texture, so they are HDR-bright.</summary>
        static readonly Color[] BossTints = {
            new Color(0.30f, 0.65f, 1.0f) * 2.6f,   // 1 blue
            new Color(1.0f, 0.50f, 0.12f) * 2.6f,   // 2 orange
            new Color(0.30f, 0.95f, 0.40f) * 2.4f,  // 3 green
            new Color(1.0f, 0.22f, 0.22f) * 2.6f,   // 4 red
            new Color(0.70f, 0.40f, 1.0f) * 2.6f,   // 5 violet
            new Color(1.0f, 0.90f, 0.25f) * 2.4f,   // 6 yellow
            new Color(0.85f, 0.85f, 0.95f) * 2.2f,  // 7 white
        };

        /// <summary>The boss: the gunship mesh with four spinning props on its nacelles, the muzzle flash ahead of the chin guns.</summary>
        /// <summary>A boss prefab: the mesh (submeshes body, accent, glass, dark, glow), one propeller per engine at propPositions
        /// (just ahead of its nacelle, body space, nose +z), the muzzle flash at flashPos (ahead of its guns).</summary>
        static GameObject BossPrefab(string name, Mesh mesh, Mesh propMesh, Mats M, Vector3[] propPositions, float propScale, Vector3 flashPos, params Material[] mats)
        {
            var root = new GameObject(name);
            var en = root.AddComponent<Enemy>();
            var body = MeshObj("Body", mesh, root.transform, mats);
            body.transform.localRotation = Quaternion.Euler(0f, 180f, 0f); // nose toward the player; EnemyKindDef.scale is applied at runtime
            Outline(body, mesh, M.outline, 1.05f);   // a thinner hull than the fighters': at 3.2x the outline is heavy enough
            en.model = body.transform;
            en.bodyRenderer = body.GetComponent<Renderer>();
            var props = new List<Transform>();
            foreach (var p in propPositions)
            {
                var prop = MeshObj("Propeller", propMesh, body.transform, M.prop, M.propDisc);
                prop.transform.localPosition = p;
                prop.transform.localScale = Vector3.one * propScale;
                props.Add(prop.transform);
            }
            en.propellers = props.ToArray();
            var flash = GameObject.CreatePrimitive(PrimitiveType.Quad); UnityEngine.Object.DestroyImmediate(flash.GetComponent<Collider>());
            flash.name = "Flash"; flash.transform.SetParent(body.transform, false);
            flash.transform.localPosition = flashPos; flash.transform.localRotation = Quaternion.Euler(0f, 180f, 0f); flash.transform.localScale = Vector3.one * 0.7f;
            var fr = flash.GetComponent<MeshRenderer>(); fr.sharedMaterial = M.bossFlash; fr.enabled = false; fr.shadowCastingMode = ShadowCastingMode.Off;
            en.flashRenderer = fr;
            en.hpLabel = Label3D("HpLabel", root.transform, new Vector3(0f, 3.62f, 0f), 10f, Color.white, fontOutline);   // his number rides above the bar (2026-09-18)
            BossHpBar(en, root, M, 2.8f, 3.6f);
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
            // the three squad planes are Asset Store models since 2026-09-18 (Zero Fighter / Aircraft C-130 / Space shuttle of the future);
            // the procedural planes stay as the fallback when a pack is not imported. Rotation: each pack's own axes -> nose toward +Z.
            // Zero Fighter (Klareh Games): URP already, nose +Z, one "Propeller" spinning on Z; the landing gear ("Wheels") is dropped
            P.planeFighter = ModelPlanePrefab("PlaneFighter", AssetDatabase.LoadAssetAtPath<GameObject>("Assets/Klareh Games/Zero/zero.prefab") ?? FindModel("zero"),
                Vector3.zero, 1.6f, 2f, Vector3.forward, new[] { "Wheels" }, M,
                () => PlanePrefab("PlaneFighter", X.fighter, X.prop, M, M.planeBody, M.planeAccent, M.glass, true));
            // Aircraft C-130 (Redballgamedev): loose parts assembled like its demo scene, Standard materials copied to URP (its lava texture is the pack's own); a little wider than the others
            P.planeAttacker = ModelPlanePrefab("PlaneAttacker", AssembleC130(), Vector3.zero, 1.7f, 2f, Vector3.up, new string[0], M,
                () => PlanePrefab("PlaneAttacker", X.attacker, X.prop, M, M.attackerBody, M.attackerAccent, M.glass, true));
            // Space shuttle of the future (Devekros) v2: nose +Z, Standard materials; the exhaust particles (legacy shaders + a point light) and the landing gear are dropped
            P.planeJet = ModelPlanePrefab("PlaneJet", AssetDatabase.LoadAssetAtPath<GameObject>("Assets/SpaceShuttle/Assets/Prefabs/SpaceShuttle v2.prefab") ?? FindModel("shuttle"),
                new Vector3(-24f, 0f, 0f), 1.6f, 2f, Vector3.forward,   /* nose pitched up 24 degrees so the camera behind sees its back, not just the engine nozzle ("the third plane with its nose raised, show its back", 2026-09-18) */ new[] { "BlueFire", "Chassis_Back_L", "Chassis_Back_R", "Chassis_Front" }, M,
                () => PlanePrefab("PlaneJet", X.jet, X.prop, M, M.jetBody, M.jetAccent, M.jetGlow, false));
            P.enemyFighter = OH1EnemyPrefab("EnemyFighter", EnsureOH1Low(), X.prop, M, () => EnemyPrefab("EnemyFighter", X.enemy, X.prop, M, false, null, M.enemyBody, M.enemyAccent, M.enemyGlass, M.enemyCowl));   // the OH-1 Ninja since 2026-09-18; the crimson procedural fighter is the fallback
            // the four boss looks: bosses 1-2 the gunship, 3-4 the twin-boom, 5-6 the flying wing, 7 the airship (requested: "every two bosses the same shape, the last one different")
            P.miniBoss = BossPrefab("EnemyMiniBoss", X.boss, X.prop, M, new[] { new Vector3(-0.9f, -0.1f, 0.82f), new Vector3(-0.48f, -0.1f, 0.82f), new Vector3(0.48f, -0.1f, 0.82f), new Vector3(0.9f, -0.1f, 0.82f) }, 0.85f, new Vector3(0f, -0.34f, 1.5f), M.bomberBody, M.bomberAccent, M.bossGlass, M.enemyCowl, M.bomberGlow);   // the gunship: slate body, orange bands, glass nose, dark guns, red-hot tips
            P.miniBoss2 = BossPrefab("EnemyMiniBoss2", X.boss2, X.prop, M, new[] { new Vector3(-0.75f, -0.02f, 1.08f), new Vector3(0.75f, -0.02f, 1.08f) }, 1.05f, new Vector3(0f, -0.3f, 1.45f), M.boss2Body, M.boss2Accent, M.bossGlass, M.enemyCowl, M.bomberGlow);   // the twin-boom: olive, yellow bands, two big props
            P.miniBoss3 = BossPrefab("EnemyMiniBoss3", X.boss3, X.prop, M, new[] { new Vector3(-1.45f, 0.14f, 0.32f), new Vector3(-0.95f, 0.14f, 0.46f), new Vector3(-0.5f, 0.14f, 0.59f), new Vector3(0.5f, 0.14f, 0.59f), new Vector3(0.95f, 0.14f, 0.46f), new Vector3(1.45f, 0.14f, 0.32f) }, 0.7f, new Vector3(0f, -0.3f, 1.52f), M.boss3Body, M.boss3Accent, M.bossGlass, M.enemyCowl, M.bomberGlow);   // the flying wing: crimson, cream bands, six props along the sweep
            P.miniBoss4 = BossPrefab("EnemyMiniBoss4", X.boss4, X.prop, M, new[] { new Vector3(-0.8f, -0.62f, -0.62f), new Vector3(0.8f, -0.62f, -0.62f) }, 0.8f, new Vector3(0f, -0.95f, 1.2f), M.boss4Body, M.boss4Accent, M.bossGlass, M.enemyCowl, M.bomberGlow);   // the airship: purple, gold belts, pusher props behind the pods
            { var sp = EnsureSparrowLow(); P.sparrowBoss = sp != null ? SparrowBossPrefab("BossSparrow", sp, M) : null; }   // the Sparrow serves every boss since 2026-09-18, tinted per boss; the four procedural looks stay as the fallback

            { // breakable: a supply crate riding a boat (under a parachute until 2026-09-18); the crate explodes on break, the boat sinks (SinkingBoat)
                var root = new GameObject("Breakable");
                var bk = root.AddComponent<Breakable>();
                // the box is the WoodenBoxes pack's SquareBoxClosed since 2026-09-18 ("I want to use this box": dark planks, blue steel corners),
                // fitted to the old crate's footprint (2.1 tall, base at -1.125 like the 1.5x procedural box so the label / hint / prize plane keep their places);
                // the pivot stays at the box centre (Breakable rocks `model` about it). The procedural banded box is the fallback when the pack is missing.
                GameObject crate;
                var woodMesh = AssetDatabase.LoadAssetAtPath<Mesh>("Assets/WoodenBoxes/Meshes/SquareBoxClosed.fbx");
                var woodMat = AssetDatabase.LoadAssetAtPath<Material>("Assets/WoodenBoxes/Materials/WoodenBox_Mat.mat");
                float boxTop = 1.13f, boxFront = 1.32f, boatW = 1.5f;   // the procedural box: top / front face / boat scale
                if (woodMesh != null && woodMat != null)
                {
                    float k = 5.2f / woodMesh.bounds.size.x;   // 5.2 wide (3.7 tall): "make the box the size of the ones behind it" (the 4.4 gate), then "bigger still, and the green ones behind it smaller" (2026-09-18; 3.0 wide for a couple of hours)
                    float h = woodMesh.bounds.size.y * k;
                    boxTop = -1.125f + h; boxFront = woodMesh.bounds.size.z * k * 0.5f; boatW = 2.5f;   // the hull widened (x only) to carry it; length unchanged so the gates behind stay clear of the stern
                    crate = new GameObject("Crate"); crate.transform.SetParent(root.transform, false);
                    crate.transform.localScale = Vector3.one * k;
                    crate.transform.localPosition = new Vector3(0f, -1.125f + h * 0.5f, 0f);
                    var boxMat = UrpCopy(woodMat);
                    boxMat.SetTexture("_BaseMap", CrateWoodTexture(woodMat.mainTexture));   // the pack's planks are grey: a brown-wood recolour, the blue steel corners kept ("I want the box brown, wooden", 2026-09-18)
                    var box = MeshObj("Box", woodMesh, crate.transform, boxMat);
                    box.transform.localPosition = -woodMesh.bounds.center;   // the FBX pivot is at the base: centre the mesh on the crate pivot
                    Outline(box, woodMesh, M.outline, 1.04f);
                    box.transform.Find("Outline").localPosition = -0.04f * woodMesh.bounds.center;   // grow the hull about the mesh centre, not its base pivot
                }
                else
                {
                    crate = MeshObj("Crate", X.crate, root.transform, M.crate, M.crateBand);
                    crate.transform.localScale = Vector3.one * 1.5f;   // reads at about a quarter of the screen at the front slot
                    Outline(crate, X.crate, M.outline, 1.05f);
                }
                var boat = MeshObj("Boat", X.boat, root.transform, M.crateBand, M.hull);   // Breakable.Init tints the hull per kind
                boat.transform.localScale = new Vector3(boatW, 1.5f, 1.5f);   // wider under the big wooden box (2.1 x), the old 1.5 otherwise
                Outline(boat, X.boat, M.outline, 1.05f);
                bk.model = crate.transform;
                bk.crateRenderer = crate.GetComponentInChildren<Renderer>();   // the wooden box is a child ("Box") of the pivot object
                bk.boat = boat.transform;
                bk.boatRenderer = boat.GetComponent<Renderer>();
                bk.weaponBoatMesh = X.boatWeapon;   // a weapon crate: a bigger boat with a white hull stripe and pennants (3 submeshes: trim, hull, stripe)
                bk.label = Label3D("Label", root.transform, new Vector3(0f, -1.125f + (boxTop + 1.125f) * 0.45f, -boxFront - 0.1f), boxTop > 1.5f ? 18f : 12f, Color.white, fontOutline);   // the number just in front of the box face, a little below its middle (bigger on the big wooden box)
                bk.hint = Label3D("Hint", root.transform, new Vector3(0f, boxTop + 0.82f, -0.6f), 4f, Gold, fontOutlineSmall);   // Breakable.Init places it above the box / above the prize plane (from boxTop)
                bk.boxTop = boxTop;
                P.breakable = SavePrefab(root, "Breakable");
            }
            { // upgrade gate: a glowing frame with a translucent fill the squad flies through (UpgradeGate); waits behind the front crate
                var root = new GameObject("UpgradeGate");
                var ug = root.AddComponent<UpgradeGate>();
                var frame = MeshObj("Frame", X.gateFrame, root.transform, M.gateFrame);
                Outline(frame, X.gateFrame, M.outline, 1.06f);
                var panel = MeshObj("Panel", X.gatePanel, root.transform, M.gatePanel);
                var pr = panel.GetComponent<MeshRenderer>(); pr.shadowCastingMode = ShadowCastingMode.Off; pr.receiveShadows = false;
                ug.model = frame.transform;
                ug.panel = pr;
                ug.label = Label3D("Label", root.transform, new Vector3(0f, 2.15f, -0.3f), 7f, Color.white, fontOutline);
                ug.hint = Label3D("Hint", root.transform, new Vector3(0f, 1.2f, -0.3f), 3.6f, Color.white, fontOutlineSmall);
                P.gate = SavePrefab(root, "UpgradeGate");
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
            { // splash: the spray a wreck throws up when it hits the sea (FXManager.Splash emits it, 2026-09-18) - a cone of white
              // droplets fired straight up that fall back under gravity; the ripple rings are LineRenderers drawn by FXManager
                var root = new GameObject("Splash");
                var ps = ParticlePrefab(root, M.particle, 0, 4f, 9f, 0.16f, 0.4f, 0.35f, 0.7f, Color.white, new Color(0.8f, 0.92f, 1f), 1.6f, true);
                var em = ps.emission; em.SetBursts(new ParticleSystem.Burst[0]);
                var main = ps.main; main.playOnAwake = false;
                var sh = ps.shape; sh.shapeType = ParticleSystemShapeType.Cone; sh.angle = 28f; sh.radius = 0.35f; sh.rotation = new Vector3(-90f, 0f, 0f);   // the cone's axis is local +z: turned to point up
                P.splash = SavePrefab(root, "Splash");
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
                tr.sharedMaterial = M.tracer; tr.time = 0.16f; tr.startWidth = 0.26f; tr.endWidth = 0.0f; tr.minVertexDistance = 0.05f; tr.shadowCastingMode = ShadowCastingMode.Off;   // a short additive fire tail (RocketPool tints it); was grey smoke
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
            D.rockets = Asset<WeaponDef>("Weapon_Rockets", w => { w.id = "rockets"; w.displayName = "ROCKETS"; w.description = "fast fire rockets"; w.damage = 1.7f; w.fireInterval = 0.4f; w.projectile = ProjectileKind.Tracer; /* 1.7 and Tracer: the tuned asset values (real bullets drawn as rockets, commit 556c2f9); the builder said 1.2 / Rocket until 2026-09-18 and a rebuild reverted them */ w.color = new Color(1f, 0.55f, 0.12f); w.planePrefab = P.planeAttacker; w.splashRadius = 1.2f; w.pierce = false;   /* only a little stronger than the Gatling (x1.5 dps, was x2.1 + big splash): requested */ });
            D.laser = Asset<WeaponDef>("Weapon_Laser", w => { w.id = "laser"; w.displayName = "CANNON"; w.description = "rapid bullets"; w.damage = 2.5f; /* the tuned asset value ("Cannon 2.5 dmg", commit 556c2f9); the builder said 1 until 2026-09-18 */ w.fireInterval = 0.3f;   /* 0.2 -> 0.3: "a little slower, the hits are too fast" (2026-09-16) */ w.projectile = ProjectileKind.Tracer;   /* was a piercing Beam with 40 u reach: "no laser, I want it to shoot bullets" (2026-09-16); same bullets and range as the Gatling, ~1.7x the rate */ w.color = new Color(0.5f, 0.95f, 1f); w.planePrefab = P.planeJet; w.splashRadius = 0f; w.pierce = false; });
            D.fighter = Asset<EnemyKindDef>("Enemy_Fighter", e => { e.id = "fighter"; e.displayName = "FIGHTER"; e.hp = 1f;   /* one hit at upgrade level 0 (2 was tried and dropped the same day: "I didn't like two hits", 2026-09-16) */ e.halfWidth = 1.0f; e.approachSpeed = 2f;   /* -4 -> 2: net 11 u/s, was 5 ("the planes are far too slow, speed them up", 2026-09-16) */ e.fireEvery = 3f; e.shotDamage = 1f; e.coins = 20;   /* "I want the coins to go up 20, not 10" (2026-09-16; was 10 earlier the same day) */ e.scale = 0.85f;   /* 0.72 until 2026-09-18 ("make the enemy planes a little bigger", right after the OH-1 came in); enemyHeightScale stretches it vertically */ e.miniBoss = false; e.prefab = P.enemyFighter; e.color = Red; });
            D.miniBoss = Asset<EnemyKindDef>("Enemy_MiniBoss", e => { e.id = "miniboss"; e.displayName = "MINI BOSS"; e.hp = 10f; e.halfWidth = 3.4f; e.approachSpeed = 2f; e.fireEvery = 4f;   /* one shot every 4 s (was 1.6; requested 2026-09-16) */ e.shotDamage = 1f; e.coins = 60; e.scale = 3.2f; e.miniBoss = true; e.prefab = P.miniBoss; e.color = new Color(1f, 0.62f, 0.1f); });
            // the asset keeps old values for fields it already had, so every number that matters is set here
            D.config = Asset<GameConfig>("GameConfig", c =>
            {
                c.weapons = new[] { D.gatling, D.rockets, D.laser }; c.enemyFighter = D.fighter; c.enemyMiniBoss = D.miniBoss;
                c.scrollSpeed = 9f; c.laneHalfWidth = 4.2f; c.spawnDistance = 150f;
                c.startCount = 1; /* 50 for a few hours on 2026-09-18 ("I want to start with 50 planes"), then back: "I want to start the game with one plane" */ c.startCountPerLevel = 0; c.steerSpeed = 8f; c.climbSpeed = 7.5f; c.dragUnitsPerScreen = 20f; /* the default, the top of the slider (30 until 2026-09-18: "speed 60 is far too high, the most 20 and the least 1"); the SETTINGS slider overrides it (Settings.cs) */ c.maxVisiblePlanes = 28; c.laneReachMin = 3.2f; c.planeHalfWidth = 0.55f; /* the squad is stopped before its outer plane leaves the screen, but never short of laneReachMin (enough to cover the outer lane at 3.8): "stop me at 15 of 20", 2026-09-18 */
                c.formationSpacingX = 1.1f; c.formationSpacingZ = 0.9f; c.spiralSpacing = 0.65f;   /* the tuned asset values (smaller squad planes, commit 556c2f9; the builder said 1.4 / 1.1 / 0.8 until 2026-09-18) */ c.lineOfFireRange = 48f; c.pierceHalfWidth = 1.2f;
                c.levelDurationBase = 55f; c.levelDurationPerLevel = 8f;
                c.laneHalfWidthAim = 0.6f; c.swarmRate = 4.5f; c.swarmRatePerHorde = 1.5f; c.openingCrowd = 35; c.openingCrowdNearZ = 62f; c.openingCrowdFarZ = 148f;   /* a dense column already in the air from the start, the nearest a few seconds out (strike line in ~10 s): time to break the first crate and take its +2 gate first */ c.swarmXRange = 3.8f; c.swarmLanes = 6; c.swarmAltSpread = 0.8f; c.swarmDepth = 12f; c.weave = 0.2f; c.swarmBank = 7f;   // 6 lanes, 1.52 apart; a fighter keeps its lane, barely banking
                c.swarmSpeedSpread = 0.4f; c.swarmSpawnJitter = 0.6f;   // no two kamikazes fly the same speed and spawns are not metronomic: they never arrive as a row
                c.swarmOpeningSeconds = 10f; c.swarmOpeningApproach = -4f; c.swarmOpeningBlend = 2f;   // the first 10 s of an attempt at the old pace (net 5 u/s), then over 2 s up to the kind's approachSpeed 2 (net 11): "only the start slow, the first 10 seconds like before, then fast" (2026-09-16)
                c.diveZ = 7f; c.threatWarnRange = 20f; c.strikeLift = 1.2f; c.strikeTurnRate = 7f; c.strikeAccel = 1.4f; c.strikeShrink = 0.8f;   /* the strike line, its reticle warning and the run past it */ c.maxAliveEnemies = 300; c.bossSpawnGap = 3f; c.holdBehindBoss = 4f;
                c.endless = true; c.bulletSpeed = 38f; c.enemyBulletSpeed = 28f; c.bulletHitRadius = 0.55f; c.bulletLife = 1.45f; c.bulletSize = 1.6f;
                c.enemyStopZ = 12f; c.enemyAltAboveSplit = 1.4f; c.enemyHeightScale = 1.35f; c.enemyFarScale = 1.7f; c.enemyFarScaleZ = 22f; c.altitudeSplit = 3.6f; c.altitudeMax = 5.0f; /* bands pulled together 2026-09-18 (were split 4.4 / ceiling 5.85, crates 1.5): "going up, the distance is long" */ c.diveForward = 0f; /* the dive is a straight drop (8.5 = fly ahead while diving was tried and reverted the same day) */   // the ceiling is the crowd's altitude
                c.miniBossShotPerBoss = 1f;   // boss k's shot takes k planes: 1, 2, 3, 4... (was 1, 3, 5...; requested 2026-09-16)
                c.bossHp = new[] { 555f, 3945f, 15960f, 27500f, 60500f, 76500f, 125200f }; c.bossHpGrowthAfter = 1.6f;   // the seven bosses the user gave (2026-09-16); boss 1: 555 until 2026-09-18, then 3445 ("higher, but 500 under boss 2"), back to 555 on 2026-09-19 ("why 3000, the first boss should be 555"); past the table x1.6 each
                c.bossFirstAt = 20f; c.bossEvery = 23f; c.bossesPerLook = 2; c.lastBoss = 7;   /* "boss 7 is the last thing, nothing after him, I have won" (2026-09-16) */   // boss 1 starts moving 20 s in ("20 s until he starts moving, not until he reaches me"), then one every 23 s ("between 22 and 24"); two bosses per look, the 7th alone with the last look
                c.upgradeCostFire = 20f; c.upgradeCostDamage = 20f; c.upgradeCostRevenue = 20f; c.upgradeCostGrowth = 2.4f;   /* 20, 48, 115, 276, 663, 1592, 3822, 9172 up to level 8 ("still too easy" at x2 from 15: 7665) */ c.upgradeLinearFromLevel = 8; c.upgradeLinearStep = 5000f;   /* from level 8 on a flat +5000 per level: 14172, 19172, 24172 ... instead of 22013, 52831 ... ("at level 8 the cost goes up by 5 thousand", 2026-09-16) */ c.fireRatePerLevel = 0.4f; c.damagePerLevel = 1.0f;   /* "upgrades must strengthen the plane noticeably" (2026-09-16): level 6 now equals the old level 17-18 */ c.revenuePerLevel = 0.1f;   /* 10 coins x 1.10 per revenue level */
                c.seaLevel = SeaLevel;   /* the wrecks of shot-down planes fall to this waterline and splash (FXManager, 2026-09-18) */ c.supplyAlt = 0.65f + SeaLevel; /* the crates ride boats on the sea (2026-09-18): the hull sits in the water at this altitude - 0.65 above the waterline, which is SeaLevel since the same evening (was 1.5 under parachutes, 2.2 for an hour) */ c.supplyFrontZ = 17f; c.supplySpacing = 6.5f; c.supplyVisible = 10;   /* a long full line of crates, not 3 that trickle in */ c.boxHpPerLevel = 1.15f; c.coinsPerHp = 0f;   /* boxes pay no coins (was 0.3: "no coins when I destroy the box", 2026-09-16); coins come from shot-down planes only */
                c.crates = new[]
                {   // the fixed crate ladder the user gave (2026-09-16): hp, the planes behind it, the next plane on top
                    new CrateDef(15f, 2), new CrateDef(275f, 2), new CrateDef(780f, 3, true),   /* ROCKETS on top */ new CrateDef(7380f, 4), new CrateDef(12850f, 5),
                    new CrateDef(28900f, 5, true),   /* LASER on top */ new CrateDef(45500f, 7), new CrateDef(68500f, 7), new CrateDef(115890f, 9),
                };
                c.crateHpGrowthAfter = 1.7f;   // past the table: x1.7 per crate, +9 each
                c.gatesEnabled = true; c.gateGap = 3.5f; c.gateStep = 2f; c.gateSpeed = 34f; c.gatePowerBonus = 0.25f;   // a +n crate carries n gates of +1, 2 apart, one behind the other; set gatesEnabled = false and the crates pay the planes themselves
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
            var im = UIImage(name, parent, new Color(0.01f, 0.015f, 0.03f, alpha), Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero);   // a neutral near-black (was a navy tint until the tactical pass, 2026-09-18)
            im.raycastTarget = false;
            return im.gameObject;
        }

        // ------------------------------------------------------------ UI kit (2026-09-19, fourth pass: GUI Pro - Casual Game)
        // "I downloaded GUI Pro - Casual Game: convert everything to what you see fit from it." Every screen is drawn with the Layer Lab
        // kit (Assets/Layer Lab/GUI Pro-CasualGame): its rounded buttons (Button01 in orange / yellow / grey, the big Button02), its
        // popup and card frames, resource bars, sliders, switch, flag titles and ribbon banners, and its flat picto icons. The sprites
        // come pre-sliced at 100 px/unit, so a sliced Image is drawn at pixelsPerUnitMultiplier = the sprite's design height / the
        // wanted height and keeps the kit's corner radius at every size. Its type is Lilita One with a navy outline - the font the game
        // already uses in the world (fontOutline / fontOutlineSmall), so the UI and the world speak with one voice again.
        // Palette: the kit's navy for every frame (white frames tinted GNavy), its orange / yellow for the one primary action of a screen
        // (the dusk's amber), red for danger. (The Strategic Warfare / AIRIDev pass of 2026-09-18 lasted a day.)
        const string PlanePackDir = "Assets/EmbersStorm - AirStrike Aviation Pack/Prefabs/";   // the title screen's jet (HangarShowcase)
        const string GuiDir = "Assets/Layer Lab/GUI Pro-CasualGame/ResourcesData/Sprites/Components/";
        static readonly Color GNavy = new Color(0.10f, 0.20f, 0.36f), GNavyDark = new Color(0.05f, 0.10f, 0.20f), GNavyLight = new Color(0.16f, 0.30f, 0.50f);
        static readonly Color GText = Color.white, GTextDim = new Color(0.66f, 0.76f, 0.90f), GInk = new Color(0.16f, 0.12f, 0.06f), GGold = new Color(1f, 0.82f, 0.25f), GRed = new Color(1f, 0.30f, 0.32f), GSky = new Color(0.30f, 0.72f, 1f);
        static readonly Vector2 Mid = new Vector2(0.5f, 0.5f), TL = new Vector2(0f, 1f), TC = new Vector2(0.5f, 1f), TR = new Vector2(1f, 1f), BL = new Vector2(0f, 0f), BC = new Vector2(0.5f, 0f), BR = new Vector2(1f, 0f);
        static Sprite gBtnOrange, gBtnYellow, gBtnGray, gBtnRed, gBtnSky, gBtnSquare, gBtnBig, gCircleNavy, gRound20, gPopup, gFlagOrange, gFlagRed, gFlagBlue, gRibbon, gBubble, gSliderBg, gSliderFill, gSliderFillYellow, gResBar, gResCoin, gSwitchOn, gSwitchOff, gSwitchHandle, gCardOrange, gCardBlue, gCardGreen,
            gIcoPause, gIcoGear, gIcoPlay, gIcoCoin, gIcoTrophy, gIcoPlane, gIcoTarget, gIcoThunder, gIcoSword, gIcoBoot, gIcoSkull, gIcoSoundOn, gIcoSoundOff, gIcoFlag, gIcoClose;
        static Sprite G(string rel)
        {
            var s = AssetDatabase.LoadAssetAtPath<Sprite>(GuiDir + rel + ".png") ?? AssetDatabase.LoadAssetAtPath<Sprite>(GuiDir + rel + ".Png");
            if (s == null) Debug.LogWarning("[SkySquad] GUI Pro sprite missing: " + rel + " (is the Layer Lab pack imported?)");
            return s;
        }
        static void LoadGui()
        {
            gBtnOrange = G("Button/Button01_145_Orange"); gBtnYellow = G("Button/Button01_145_Yellow"); gBtnGray = G("Button/Button01_145_Gray"); gBtnRed = G("Button/Button01_175_Red"); gBtnBig = G("Button/Button02_Yellow");
            gCircleNavy = G("Button/Button_Circle147_Navy"); gRound20 = G("Frame/BasicFrame_Round20"); gPopup = G("Popup/Popup01_Single_Navy");
            gFlagOrange = G("Label/Title_Flag01_Orange"); gFlagRed = G("Label/Title_Flag01_Red"); gFlagBlue = G("Label/Title_Flag01_Blue"); gRibbon = G("Label/Title_Ribbon_Bg_Orange"); gBubble = G("Label/Label_Bubble02_Single_Yellow");
            gSliderBg = G("Slider/Slider_Basic02_Bg"); gSliderFill = G("Slider/Slider_Basic02_Fill_White"); gSliderFillYellow = G("Slider/Slider_Basic02_Fill_Yellow");
            gResBar = G("UI_Etc/ResourceBar_Bg"); gResCoin = G("UI_Etc/ResourceBar_Icon_Coin"); gSwitchOn = G("UI_Etc/Switch_Bg_On"); gSwitchOff = G("UI_Etc/Switch_Bg_Off"); gSwitchHandle = G("UI_Etc/Switch_Handle_On");
            gCardOrange = G("Frame/CardFrame03_Single_Orange"); gCardBlue = G("Frame/CardFrame03_Single_Blue"); gCardGreen = G("Frame/CardFrame03_Single_Green");
            gIcoPause = G("IconMisc/Icon_PictoIcon_Pause"); gIcoGear = G("IconMisc/Icon_PictoIcon_Setting"); gIcoPlay = G("IconMisc/Icon_PictoIcon_Play"); gIcoCoin = G("IconMisc/Icon_ImageIcon_Coin01_s"); gIcoTrophy = G("IconMisc/Icon_ImageIcon_Trophy_S");
            gIcoPlane = G("Icon_PictoIcons/128/Pictoicon_Airplane"); gIcoTarget = G("Icon_PictoIcons/128/Pictoicon_Target"); gIcoThunder = G("Icon_PictoIcons/128/Pictoicon_Thunder"); gIcoSword = G("IconMisc/Icon_StatsIcon_Damage"); gIcoBoot = G("IconMisc/Icon_StatsIcon_Speed"); gIcoSkull = G("IconMisc/Icon_StatsIcon_Boss");
            gIcoSoundOn = G("IconMisc/Icon_PictoIcon_Sound_on"); gIcoSoundOff = G("IconMisc/Icon_PictoIcon_Sound_off"); gIcoFlag = G("Icon_PictoIcons/128/Pictoicon_Flag_0"); gIcoClose = G("IconMisc/Icon_PictoIcon_Close");
            gBtnSky = G("Button/Button01_145_Sky"); gBtnSquare = G("Button/Button_Square05_Blue");
        }
        /// <summary>A kit sprite as an Image: 9-sliced at the multiplier that draws it at the sprite's design size scaled to <paramref name="designHeight"/>
        /// -> the rect's height (so corners keep their radius), or (sliced = false) whole at its own aspect. The generated chamfer plate stands in
        /// when the pack is missing.</summary>
        static Image GImg(string name, Transform parent, Sprite s, Color tint, Vector2 anchorMin, Vector2 anchorMax, Vector2 pos, Vector2 size, float ppuMul = 1f, bool sliced = true)
        {
            var im = UIImage(name, parent, tint, anchorMin, anchorMax, pos, size);
            if (s != null) { im.sprite = s; im.type = sliced ? Image.Type.Sliced : Image.Type.Simple; im.pixelsPerUnitMultiplier = ppuMul; im.preserveAspect = !sliced; }
            else { im.sprite = uiChamfer; im.type = Image.Type.Sliced; im.pixelsPerUnitMultiplier = 1.5f; }
            return im;
        }
        /// <summary>The multiplier that draws a sliced kit sprite of design height <paramref name="spriteH"/> at <paramref name="wantH"/> units.</summary>
        static float Fit(float spriteH, float wantH) => Mathf.Max(0.2f, spriteH / Mathf.Max(1f, wantH));
        static Image Icon(string name, Transform parent, Sprite s, Color c, Vector2 anchor, Vector2 pos, float size)
        {
            var im = UIImage(name, parent, c, anchor, anchor, pos, new Vector2(size, size));
            im.sprite = s; im.type = Image.Type.Simple; im.preserveAspect = true;
            return im;
        }
        /// <summary>UI type: Lilita One with the navy outline (the kit's own face). small = the thinner outline for labels.</summary>
        static TextMeshProUGUI Type(string name, Transform parent, string text, float size, Color color, Vector2 anchor, Vector2 pos, Vector2 box, bool small = false, TextAlignmentOptions align = TextAlignmentOptions.Center)
        {
            var rt = UI(name, parent, anchor, anchor, pos, box);
            var t = rt.gameObject.AddComponent<TextMeshProUGUI>();
            t.font = font; t.fontSharedMaterial = small ? fontOutlineSmall : fontOutline;
            t.text = text; t.fontSize = size; t.color = color; t.alignment = align; t.raycastTarget = false;
            return t;
        }
        /// <summary>A plate: the kit's round frame tinted navy. Content goes inside at the root's size.</summary>
        static RectTransform Plate(string name, Transform parent, Vector2 anchor, Vector2 pos, Vector2 size, Color? tint = null)
        {
            var rt = UI(name, parent, anchor, anchor, pos, size);
            GImg("Face", rt, gRound20, tint ?? GNavy, Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero, Fit(50f, Mathf.Min(size.y, 60f)));
            return rt;
        }
        /// <summary>A resource bar: the kit's dark pill with a round icon overhanging its left end (the bank, the plane count).</summary>
        static RectTransform ResourceBar(string name, Transform parent, Vector2 anchor, Vector2 pos, Vector2 size, Sprite icon, float iconSize, Color iconTint, bool iconOnNavyDisc)
        {
            var rt = UI(name, parent, anchor, anchor, pos, size);
            GImg("Bar", rt, gResBar, GNavyDark, Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero, Fit(64f, size.y));
            if (iconOnNavyDisc) GImg("Disc", rt, gCircleNavy, Color.white, new Vector2(0f, 0.5f), new Vector2(0f, 0.5f), new Vector2(2f, 0f), new Vector2(iconSize * 1.25f, iconSize * 1.25f), 1f, false);
            Icon("Icon", rt, icon, iconTint, new Vector2(0f, 0.5f), new Vector2(2f, 0f), iconSize);
            return rt;
        }
        /// <summary>A button in the kit's face: one of its Button01 pills (orange / yellow = primary, grey = quiet, red = danger) or the big Button02,
        /// the label in Lilita, an optional picto at the left. A real Button with the press squash (UIButtonFx) when interactive; the same look as
        /// a "tap anywhere" prompt when not. Out: the pill (faceIm) and the label, so HUD can grey out a price.</summary>
        static RectTransform GButton(string name, Transform parent, Vector2 anchor, Vector2 pos, Vector2 size, Sprite pill, float pillH, string label, float fontSize, Color labelColor, out Image faceIm, out TextMeshProUGUI labelTm, bool interactive = true, Sprite icon = null, float iconSize = 0f, Color? iconTint = null)
        {
            var rt = UI(name, parent, anchor, anchor, pos, size);
            faceIm = GImg("Face", rt, pill, Color.white, Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero, Fit(pillH, size.y));
            float shift = 0f;
            if (icon != null) { Icon("Icon", rt, icon, iconTint ?? Color.white, new Vector2(0f, 0.5f), new Vector2(16f + iconSize * 0.5f, 2f), iconSize); shift = iconSize * 0.5f + 6f; }
            labelTm = Type("Label", rt, label, fontSize, labelColor, Mid, new Vector2(shift, 3f), new Vector2(size.x - shift * 2f, size.y));   // a touch up: the pills carry a darker lip along the bottom
            if (interactive)
            {
                faceIm.raycastTarget = true;
                var btn = rt.gameObject.AddComponent<Button>(); btn.transition = Selectable.Transition.None; btn.targetGraphic = faceIm;
                var fx = rt.gameObject.AddComponent<UIButtonFx>(); fx.tint = faceIm; fx.pressedColor = new Color(0.72f, 0.72f, 0.72f);
            }
            return rt;
        }
        static Button GButtonClick(string name, Transform parent, Vector2 anchor, Vector2 pos, Vector2 size, Sprite pill, float pillH, string label, float fontSize, Color labelColor, Sprite icon = null, float iconSize = 0f)
        {
            var rt = GButton(name, parent, anchor, pos, size, pill, pillH, label, fontSize, labelColor, out _, out _, true, icon, iconSize);
            return rt.GetComponent<Button>();
        }
        /// <summary>An icon button: the kit's navy disc with a white picto (pause, settings). Press squash + a dimming.</summary>
        static Button IconButton(string name, Transform parent, Vector2 anchor, Vector2 pos, float size, Sprite icon, float iconSize)
        {
            var rt = UI(name, parent, anchor, anchor, pos, new Vector2(size, size));
            var face = GImg("Face", rt, gCircleNavy, Color.white, Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero, 1f, false); face.raycastTarget = true;
            Icon("Icon", rt, icon, GText, Mid, new Vector2(0f, 2f), iconSize);
            var btn = rt.gameObject.AddComponent<Button>(); btn.transition = Selectable.Transition.None; btn.targetGraphic = face;
            var fx = rt.gameObject.AddComponent<UIButtonFx>(); fx.tint = face; fx.pressedColor = new Color(0.7f, 0.7f, 0.75f);
            return btn;
        }
        /// <summary>A bare glyph button (the reference's gear / pause): the white picto with a navy outline and shadow, no plate. Press squash + dimming.</summary>
        static Button GlyphButton(string name, Transform parent, Vector2 anchor, Vector2 pos, float size, Sprite icon)
        {
            var im = Icon(name, parent, icon, GText, anchor, pos, size); im.raycastTarget = true;
            var ol = im.gameObject.AddComponent<Outline>(); ol.effectColor = new Color(0.08f, 0.14f, 0.28f, 1f); ol.effectDistance = new Vector2(2.5f, -2.5f); ol.useGraphicAlpha = true;
            var sh = im.gameObject.AddComponent<Shadow>(); sh.effectColor = new Color(0f, 0f, 0f, 0.35f); sh.effectDistance = new Vector2(0f, -4f);
            var rt = im.rectTransform; rt.sizeDelta = new Vector2(size * 1.6f, size * 1.6f);   // a thumb-sized hit box
            var btn = im.gameObject.AddComponent<Button>(); btn.transition = Selectable.Transition.None; btn.targetGraphic = im;
            var fx = im.gameObject.AddComponent<UIButtonFx>(); fx.tint = im; fx.pressedColor = new Color(0.75f, 0.78f, 0.85f);
            return btn;
        }
        /// <summary>A resource bar the reference's way: the kit's dark pill with the icon overhanging its RIGHT end (the coin, the plane).</summary>
        static RectTransform CoinBar(string name, Transform parent, Vector2 anchor, Vector2 pos, Vector2 size, Sprite icon, float iconSize)
        {
            var rt = UI(name, parent, anchor, anchor, pos, size);
            GImg("Bar", rt, gResBar, new Color(0.10f, 0.20f, 0.36f, 0.95f), Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero, Fit(64f, size.y));
            var im = Icon("Icon", rt, icon, Color.white, new Vector2(1f, 0.5f), new Vector2(-6f, 0f), iconSize);
            if (icon == gIcoPlane) { var ol = im.gameObject.AddComponent<Outline>(); ol.effectColor = new Color(0.08f, 0.14f, 0.28f, 1f); ol.effectDistance = new Vector2(2f, -2f); }
            return rt;
        }
        /// <summary>A square button (the reference's pause): the kit's blue square with a white picto. Press squash + dimming.</summary>
        static Button SquareButton(string name, Transform parent, Vector2 anchor, Vector2 pos, float size, Sprite icon, float iconSize)
        {
            var rt = UI(name, parent, anchor, anchor, pos, new Vector2(size, size));
            var face = GImg("Face", rt, gBtnSquare, Color.white, Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero, Fit(gBtnSquare != null ? gBtnSquare.rect.height : 54f, size)); face.raycastTarget = true;
            Icon("Icon", rt, icon, GText, Mid, new Vector2(0f, 2f), iconSize);
            var btn = rt.gameObject.AddComponent<Button>(); btn.transition = Selectable.Transition.None; btn.targetGraphic = face;
            var fx = rt.gameObject.AddComponent<UIButtonFx>(); fx.tint = face; fx.pressedColor = new Color(0.72f, 0.72f, 0.72f);
            return btn;
        }
        /// <summary>A progress bar: the kit's pill track (dark navy) with its rounded fill growing from the left (HUD sets the fill width in units;
        /// hud.progressWidth = the inner width, size.x - 8).</summary>
        static RectTransform Bar(string name, Transform parent, Vector2 anchor, Vector2 pos, Vector2 size, Color fill, out Image fillIm)
        {
            var rt = UI(name, parent, anchor, anchor, pos, size);
            GImg("Track", rt, gSliderBg, GNavyDark, Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero, Fit(46f, size.y));
            var inner = UI("Inner", rt, Vector2.zero, Vector2.one, Vector2.zero, new Vector2(-8f, -8f));
            fillIm = GImg("Fill", inner, gSliderFill, fill, new Vector2(0f, 0f), new Vector2(0f, 1f), Vector2.zero, new Vector2(12f, 0f), Fit(67f, size.y - 8f));
            fillIm.rectTransform.pivot = new Vector2(0f, 0.5f);
            return rt;
        }
        /// <summary>A horizontal slider (background, fill area, handle slide area, like Unity's default): the kit's pill track, yellow fill, white knob.</summary>
        static Slider UISlider(string name, Transform parent, Vector2 pos, Vector2 size, float min, float max)
        {
            var rt = UI(name, parent, Mid, Mid, pos, size);
            float trackH = 22f;
            var track = UI("Track", rt, new Vector2(0f, 0.5f), new Vector2(1f, 0.5f), Vector2.zero, new Vector2(0f, trackH));
            GImg("Background", track, gSliderBg, GNavyDark, Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero, Fit(46f, trackH)).raycastTarget = true;
            var fillArea = UI("Fill Area", track, Vector2.zero, Vector2.one, Vector2.zero, new Vector2(-20f, -6f));
            var fill = GImg("Fill", fillArea, gSliderFillYellow, Color.white, Vector2.zero, Vector2.one, Vector2.zero, new Vector2(12f, 0f), Fit(67f, trackH - 6f));
            var handleArea = UI("Handle Slide Area", rt, Vector2.zero, Vector2.one, Vector2.zero, new Vector2(-30f, 0f));
            var handle = GImg("Handle", handleArea, gSwitchHandle, Color.white, new Vector2(0f, 0f), new Vector2(0f, 1f), Vector2.zero, new Vector2(30f, 0f), 1f, false); handle.raycastTarget = true;
            var s = rt.gameObject.AddComponent<Slider>();
            s.fillRect = fill.rectTransform; s.handleRect = handle.rectTransform; s.targetGraphic = handle; s.transition = Selectable.Transition.None;
            s.direction = Slider.Direction.LeftToRight; s.minValue = min; s.maxValue = max; s.wholeNumbers = true; s.value = max;
            return s;
        }
        /// <summary>A modal card: the kit's navy popup with its flag title hanging over the top edge (orange / red / blue by mood), the words on it.</summary>
        static RectTransform Card(string name, Transform parent, Vector2 anchor, Vector2 pos, Vector2 size, Sprite flag, string title, float titleSize)
        {
            var rt = UI(name, parent, anchor, anchor, pos, size);
            GImg("Face", rt, gPopup, Color.white, Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero, 1.2f);
            if (!string.IsNullOrEmpty(title))
            {
                var flagRt = UI("Flag", rt, TC, TC, new Vector2(0f, 4f), new Vector2(300f, 84f));
                GImg("FlagImg", flagRt, flag, Color.white, Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero, 1f, false);
                Type("Title", flagRt, title, titleSize, GText, Mid, new Vector2(0f, 8f), new Vector2(280f, 60f));
            }
            return rt;
        }
        /// <summary>An upgrade card: one of the kit's colour card frames (a coloured head band over a lighter body).</summary>
        static RectTransform ColourCard(string name, Transform parent, Vector2 anchor, Vector2 pos, Vector2 size, Sprite frame)
        {
            var rt = UI(name, parent, anchor, anchor, pos, size);
            GImg("Face", rt, frame, Color.white, Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero, Fit(144f, size.y));
            return rt;
        }
        /// <summary>A named layer, added to the TagManager if the project has none.</summary>
        static int EnsureLayer(string name)
        {
            int idx = LayerMask.NameToLayer(name);
            if (idx >= 0) return idx;
            var tm = new SerializedObject(AssetDatabase.LoadAllAssetsAtPath("ProjectSettings/TagManager.asset")[0]);
            var layers = tm.FindProperty("layers");
            for (int i = 8; i < layers.arraySize; i++)
            {
                var p = layers.GetArrayElementAtIndex(i);
                if (string.IsNullOrEmpty(p.stringValue)) { p.stringValue = name; tm.ApplyModifiedProperties(); return i; }
            }
            Debug.LogWarning("[SkySquad] no free layer for " + name); return 0;
        }
        /// <summary>A RenderTexture asset of the given size, created once and reused (recreated when the size changes).</summary>
        static RenderTexture LoadOrCreateRt(string path, int w, int h)
        {
            var rt = AssetDatabase.LoadAssetAtPath<RenderTexture>(path);
            if (rt != null && rt.width == w && rt.height == h) return rt;
            if (rt != null) AssetDatabase.DeleteAsset(path);
            rt = new RenderTexture(w, h, 24, RenderTextureFormat.ARGB32) { name = Path.GetFileNameWithoutExtension(path), useMipMap = false, antiAliasing = 1 };
            AssetDatabase.CreateAsset(rt, path);
            return rt;
        }

        static void BuildScene(Mats M, Meshes X, Prefabs P, Defs D)
        {
            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);

            // camera rig
            var rig = new GameObject("CameraRig"); rig.transform.position = new Vector3(0f, 7.48f, -11f);   // the rig at altitude 0; with followAlt 0.2 the ceiling (where every attempt starts) is (0, 8.65, -11): squad at 58% of the screen, swarm 66-75%, horizon 75%. On a full dive the camera drops only 1.2: squad 19%, swarm 71-74% ("the camera stays up on the enemy planes like before the dive", 2026-09-18; before: base y 4.55 / followAlt 0.7 = squad 42% but the swarm at 78-86%, gone)
            var follow = rig.AddComponent<CameraFollow>(); follow.basePosition = rig.transform.position; follow.followX = 0.55f; /* 1 (centred) was tried 2026-09-18 and rejected: the squad is clamped instead (SquadController.XLimit) */ follow.followAlt = 0.2f;   // barely climbs with the squad: the view is anchored on the swarm (was 0.7)
            follow.pitchHigh = 13.5f; follow.pitchLow = 13.5f; follow.dollyLow = 0f;   // no tilt or zoom-out on the dive (pitchLow 8.9 / dollyLow 4 was tried and dropped the same day: the user wants the camera to hold its place)
            var camGo = new GameObject("Main Camera"); camGo.tag = "MainCamera"; camGo.transform.SetParent(rig.transform, false);
            var cam = camGo.AddComponent<Camera>(); camGo.AddComponent<AudioListener>();
            cam.fieldOfView = 52f; cam.nearClipPlane = 0.3f; cam.farClipPlane = 500f; cam.clearFlags = CameraClearFlags.Skybox;
            var camData = cam.GetUniversalAdditionalCameraData();
            camData.renderPostProcessing = true; camData.antialiasing = AntialiasingMode.FastApproximateAntialiasing;
            camGo.transform.localRotation = Quaternion.Euler(13.5f, 0f, 0f);   // pitch 13.5 from (0, 4.55, -11): squad at 42% (alt 0) to 57% (ceiling, where it starts), bottom 35% free for the thumb, front crate ~66%, horizon ~75% (was y 5 / pitch 11: squad 29-46%, horizon 70%)

            // light + sky
            var lightGo = new GameObject("Sun"); var light = lightGo.AddComponent<Light>();
            // a war dusk (2026-09-18, "I don't want a morning, something that says war"): a low orange sun, long soft shadows; was (1, 0.96, 0.88) x 1.5 from 52 degrees up
            light.type = LightType.Directional; light.color = new Color(1f, 0.97f, 0.90f); light.intensity = 1.5f; light.shadows = LightShadows.Soft; light.shadowStrength = 0.55f;   /* a bright morning sun again (2026-09-19, "light, simple colours"); the war dusk sat at (1, 0.72, 0.5) x 1.35 from 18 degrees */
            lightGo.transform.rotation = Quaternion.Euler(52f, -28f, 0f);   /* low, from ahead-left where the HDRI's sun sits */
            // the sky: a real photographed sky (Poly Haven "Kloofendal 48d partly cloudy" pure-sky HDRI, CC0, Assets/_Game/Art/Sky)
            // on the panoramic skybox shader, lighting the scene through skybox ambient. Falls back to the old procedural
            // gradient if the file is missing. (requested 2026-09-16: "the background is ugly, I want a professional sky")
            var skyPath = Gen + "/Materials/Skybox.mat";
            var sky = AssetDatabase.LoadAssetAtPath<Material>(skyPath);
            var hdri = ImportSkyHdri(Root + "/Art/Sky/kloofendal_48d_partly_cloudy_puresky_4k.hdr");   /* Poly Haven "Kloofendal 48d partly cloudy" pure sky: blue with white cumulus, back since 2026-09-19 (the Belfast sunset served the war dusk for a day) */   /* Poly Haven "Belfast sunset" pure sky: heavy dark cloud over a burning horizon (the Kloofendal partly-cloudy morning until 2026-09-18) */
            if (hdri != null)
            {
                if (sky == null || sky.shader.name != "Skybox/Panoramic") { sky = new Material(Shader.Find("Skybox/Panoramic")); AssetDatabase.CreateAsset(sky, skyPath); }
                sky.SetTexture("_MainTex", hdri); sky.SetFloat("_Mapping", 1f); sky.SetFloat("_ImageType", 0f); sky.SetFloat("_Layout", 0f);   // lat-long, 360 degrees
                sky.SetFloat("_Exposure", 1.05f); sky.SetFloat("_Rotation", SkyRotation); sky.SetColor("_Tint", new Color(0.5f, 0.5f, 0.5f));
                EditorUtility.SetDirty(sky);
                RenderSettings.skybox = sky; RenderSettings.sun = light;
                RenderSettings.ambientMode = AmbientMode.Skybox; RenderSettings.ambientIntensity = 1.0f;
            }
            else
            {
                if (sky == null || sky.shader.name != "Skybox/Procedural") { sky = new Material(Shader.Find("Skybox/Procedural")); AssetDatabase.CreateAsset(sky, skyPath); }
                sky.SetColor("_SkyTint", new Color(0.5f, 0.75f, 1f)); sky.SetColor("_GroundColor", new Color(0.12f, 0.45f, 0.72f)); sky.SetFloat("_Exposure", 1.15f); sky.SetFloat("_SunSize", 0.05f); sky.SetFloat("_AtmosphereThickness", 0.55f);
                EditorUtility.SetDirty(sky);
                RenderSettings.skybox = sky; RenderSettings.sun = light; RenderSettings.ambientMode = AmbientMode.Trilight;
                RenderSettings.ambientSkyColor = new Color(0.6f, 0.78f, 1f); RenderSettings.ambientEquatorColor = new Color(0.45f, 0.6f, 0.8f); RenderSettings.ambientGroundColor = new Color(0.15f, 0.3f, 0.45f);
            }
            RenderSettings.fog = true; RenderSettings.fogMode = FogMode.Linear; RenderSettings.fogStartDistance = 175f; RenderSettings.fogEndDistance = 340f;   /* starts past spawnDistance: fighters are never seen half-fogged */ RenderSettings.fogColor = new Color(0.82f, 0.91f, 0.94f);   /* a pale morning haze (the dusk's rose (0.74, 0.60, 0.56)) */   /* the dusk horizon: dusty rose haze, so the far sea melts into the sky (pale (0.8, 0.87, 0.95) with the morning sky) */

            // post: bloom makes tracers and explosions glow, a vignette frames the lane, a touch more colour
            string profilePath = Gen + "/Data/PostFX.asset";
            var profile = AssetDatabase.LoadAssetAtPath<VolumeProfile>(profilePath);
            if (profile == null) { profile = ScriptableObject.CreateInstance<VolumeProfile>(); AssetDatabase.CreateAsset(profile, profilePath); }
            T Fx<T>() where T : VolumeComponent
            {
                if (profile.TryGet(out T have)) return have;
                var c = profile.Add<T>(true); c.hideFlags = HideFlags.HideInHierarchy; AssetDatabase.AddObjectToAsset(c, profile); return c;
            }
            var bloom = Fx<Bloom>(); bloom.threshold.Override(1.15f); bloom.intensity.Override(0.6f); bloom.scatter.Override(0.6f);   // above the HDRI sky's brightness: tracers, flashes and explosions glow, the clouds do not turn milky
            var tone = Fx<Tonemapping>(); tone.mode.Override(TonemappingMode.Neutral);   // the photographed sky has real HDR highlights: roll them off instead of clipping to white
            var vignette = Fx<Vignette>(); vignette.intensity.Override(0.22f); vignette.smoothness.Override(0.45f);   /* heavier for the war dusk (0.28 / 0.45) */
            var grade = Fx<ColorAdjustments>(); grade.saturation.Override(14f); grade.contrast.Override(8f); grade.postExposure.Override(0.1f); grade.colorFilter.Override(Color.white);   /* bright and clean for the casual UI (2026-09-19); the war dusk: -4 / +22 / 0 / warm filter */   /* the war dusk: muted, contrasty, warm (was +12 / +10 / 0.1 for the morning) */
            EditorUtility.SetDirty(profile);
            var postGo = new GameObject("PostFX"); var vol = postGo.AddComponent<Volume>(); vol.isGlobal = true; vol.sharedProfile = profile;   // sharedProfile: .profile made a runtime clone and the scene saved with NO profile (post FX were silently off until 2026-09-16)

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
            // the sea (2026-09-18): a dense grid near the camera that the Sea shader lifts into waves, and the old 1200 x 1200 flat plane
            // half a unit lower for the horizon (past the far clip, so the sea meets the sky at the fog colour and the HDRI's grey below-horizon
            // half never shows; the step down hides under the fog at the grid's edge). Same material on both; WorldScroller drives _SeaScroll.
            var water = MeshObj("Water", X.sea, worldGo.transform, M.water); water.transform.localPosition = new Vector3(0f, SeaLevel, 0f);
            var wr = water.GetComponent<MeshRenderer>(); wr.shadowCastingMode = ShadowCastingMode.Off; wr.receiveShadows = true; world.water = wr; world.waterTilesPerUnit = 0.1f;
            var far = GameObject.CreatePrimitive(PrimitiveType.Plane); UnityEngine.Object.DestroyImmediate(far.GetComponent<Collider>());
            far.name = "WaterFar"; far.transform.SetParent(worldGo.transform, false); far.transform.position = new Vector3(0f, SeaLevel - 1f, 120f);   /* a full unit under the wave troughs (0.5 let its flat polygons poke through) */ far.transform.localScale = new Vector3(120f, 1f, 120f);
            var fr = far.GetComponent<MeshRenderer>(); fr.sharedMaterial = M.water; fr.shadowCastingMode = ShadowCastingMode.Off;
            var rnd = new System.Random(5);
            for (int i = 0; i < 16; i++)
            {
                float side = i % 2 == 0 ? -1f : 1f;
                var b = MeshObj("Buoy" + i, X.buoy, worldGo.transform, M.buoy, M.buoyPole);
                b.transform.position = new Vector3(side * (D.config.laneHalfWidth + 2.0f), SeaLevel + 0.15f, -20f + i / 2 * 27.5f);
                world.buoys.Add(b.transform);
            }
            // near clouds: 9 clusters drifting past on both sides, each a heap of 2-3 overlapping puffs (some mirrored) at
            // slightly different depths, so they read as lumpy cumulus rather than one flat stamp (requested: "improve the clouds around me")
            for (int i = 0; i < 9; i++)
            {
                var cluster = new GameObject("Cloud" + i); cluster.transform.SetParent(worldGo.transform, false);
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
                world.clouds.Add(cluster.transform);
            }

            // (the cloud rails - small puffs along both lane edges at the split altitude, scrolling with the buoys - were removed on 2026-09-19: "the clouds in a straight line left and right, I don't want them")

            // dashed lines across the sky, one dash per swarm lane centred on it (the scripts drive colour/alpha)
            Renderer[] LaneDashes(Transform parent, float z, Material mat)
            {
                int lanes = Mathf.Max(1, D.config.swarmLanes); float dashStep = lanes > 1 ? D.config.swarmXRange * 2f / (lanes - 1) : D.config.swarmXRange * 2f; var dashes = new Renderer[lanes];
                for (int i = 0; i < lanes; i++)
                {
                    var q = GameObject.CreatePrimitive(PrimitiveType.Quad); UnityEngine.Object.DestroyImmediate(q.GetComponent<Collider>());
                    q.name = "Dash" + i; q.transform.SetParent(parent, false);
                    q.transform.position = new Vector3(D.config.LaneX(i), 1f + D.config.altitudeSplit + D.config.enemyAltAboveSplit - 0.55f, z);
                    q.transform.localScale = new Vector3(dashStep * 0.7f, 0.14f, 1f);
                    var qr = q.GetComponent<MeshRenderer>(); qr.sharedMaterial = mat; qr.shadowCastingMode = ShadowCastingMode.Off; qr.receiveShadows = false;
                    dashes[i] = qr;
                }
                return dashes;
            }
            // the front line: a dashed red line where a boss parks and opens fire (StopLine shows it as he comes)
            {
                var slGo = new GameObject("StopLine"); var sl = slGo.AddComponent<StopLine>();
                sl.dashes = LaneDashes(slGo.transform, D.config.enemyStopZ - 0.9f, M.stopLine);
            }
            // the threat reticles: a lock-on marker pinned on every fighter approaching the strike line (ThreatMarkers)
            {
                var tmGo = new GameObject("ThreatMarkers"); var tm = tmGo.AddComponent<ThreatMarkers>();
                tm.material = M.threatMarker;
            }

            // managers
            var gameGo = new GameObject("Game");
            var gm = gameGo.AddComponent<GameManager>();
            var audio = gameGo.AddComponent<AudioManager>();
            var fx = gameGo.AddComponent<FXManager>();
            fx.explosionPrefab = P.explosion; fx.sparksPrefab = P.sparks; fx.splashPrefab = P.splash; fx.floatTextPrefab = P.floatText; fx.ringPrefab = P.ring; fx.coinPrefab = P.coin;

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

            var enemiesGo = new GameObject("Enemies"); var enemies = enemiesGo.AddComponent<WaveSpawner>(); enemies.fighterPrefab = P.enemyFighter; enemies.bossPrefabs = P.sparrowBoss != null ? new[] { P.sparrowBoss } : new[] { P.miniBoss, P.miniBoss2, P.miniBoss3, P.miniBoss4 }; enemies.bossColors = BossTints;
            var supplyGo = new GameObject("Supply"); var supply = supplyGo.AddComponent<SupplyLane>(); supply.breakablePrefab = P.breakable; supply.gatePrefab = P.gate;
            var bossGo = (GameObject)PrefabUtility.InstantiatePrefab(P.boss); bossGo.name = "Boss"; var boss = bossGo.GetComponent<BossController>(); bossGo.SetActive(false);

            // the hangar: the title screen's 3D aircraft (EmbersStorm AirStrike pack), turning on its own layer far under the sea, rendered by
            // its own camera into a RenderTexture the lobby shows in a RawImage (HangarShowcase; HUD switches the rig on and off with the title)
            GameObject hangar = null; RenderTexture hangarRt = null;
            var jetPrefab = AssetDatabase.LoadAssetAtPath<GameObject>(PlanePackDir + "AirFightJet.prefab");
            if (jetPrefab != null)
            {
                int layer = EnsureLayer("Hangar");
                hangarRt = LoadOrCreateRt(Gen + "/Textures/Hangar.renderTexture", 960, 600);   // 2x the 480 x 300 view: the downscale smooths the edges (no post, no MSAA on this camera)
                hangar = new GameObject("Hangar"); hangar.transform.position = new Vector3(0f, -300f, 0f);
                var pivot = new GameObject("Pivot"); pivot.transform.SetParent(hangar.transform, false);
                var jet = (GameObject)PrefabUtility.InstantiatePrefab(jetPrefab); jet.name = "AirFightJet"; jet.transform.SetParent(pivot.transform, false);
                var jrs = jet.GetComponentsInChildren<Renderer>(); var jb = jrs[0].bounds; foreach (var r in jrs) jb.Encapsulate(r.bounds);
                jet.transform.localPosition = jet.transform.position - jb.center;   // the pack's pivot is the model's origin, not its middle: centre it so it turns in place
                foreach (var t in jet.GetComponentsInChildren<Transform>(true)) t.gameObject.layer = layer;
                var show = hangar.AddComponent<HangarShowcase>(); show.model = pivot.transform;
                var hcGo = new GameObject("HangarCamera"); hcGo.transform.SetParent(hangar.transform, false);
                hcGo.transform.localPosition = new Vector3(0f, 3.2f, -13.5f); hcGo.transform.localRotation = Quaternion.Euler(12f, 0f, 0f);   // a little above, looking down on the wings
                var hc = hcGo.AddComponent<Camera>();
                hc.cullingMask = 1 << layer; hc.clearFlags = CameraClearFlags.SolidColor; hc.backgroundColor = new Color(0f, 0f, 0f, 0f);   // transparent: the sky shows through around the jet
                hc.fieldOfView = 30f; hc.nearClipPlane = 0.5f; hc.farClipPlane = 60f; hc.targetTexture = hangarRt; hc.depth = -10f;
                hc.allowHDR = false; hc.allowMSAA = false;   // LDR: URP's HDR buffer has no alpha channel, and the RawImage needs the alpha to composite
                var hcd = hc.GetUniversalAdditionalCameraData(); hcd.renderPostProcessing = false; hcd.renderShadows = true; hcd.antialiasing = AntialiasingMode.None;
                cam.cullingMask &= ~(1 << layer);   // the world camera never sees the hangar
                // its own lights (the sun is low and behind the camera's view of the wings; without these the jet is a silhouette): a warm key from the camera's
                // upper left, a cool fill from the right, both spots that light only the hangar layer
                var key = new GameObject("HangarKey").AddComponent<Light>(); key.transform.SetParent(hangar.transform, false); key.transform.localPosition = new Vector3(-8f, 9f, -9f); key.transform.LookAt(hangar.transform);
                key.type = LightType.Spot; key.spotAngle = 70f; key.range = 40f; key.intensity = 3.2f; key.color = new Color(1f, 0.86f, 0.7f); key.cullingMask = 1 << layer; key.shadows = LightShadows.None;
                var fill = new GameObject("HangarFill").AddComponent<Light>(); fill.transform.SetParent(hangar.transform, false); fill.transform.localPosition = new Vector3(9f, 3f, -6f); fill.transform.LookAt(hangar.transform);
                fill.type = LightType.Spot; fill.spotAngle = 80f; fill.range = 40f; fill.intensity = 1.4f; fill.color = new Color(0.6f, 0.75f, 1f); fill.cullingMask = 1 << layer; fill.shadows = LightShadows.None;
            }
            else Debug.LogWarning("[SkySquad] EmbersStorm AirFightJet prefab missing: the title screen has no 3D aircraft");

            // HUD (2026-09-19, fifth pass: the hyper-casual layout the user showed - flat white icons, "Level" words top centre, a coin bar
            // top right with the coin overhanging its end, and three tall upgrade cards along the bottom with a level badge, a big picture,
            // a five-pip bar and an UPGRADE button each - drawn with the GUI Pro - Casual Game kit, Lilita One with the navy outline)
            var canvasGo = new GameObject("HUD", typeof(Canvas), typeof(CanvasScaler), typeof(GraphicRaycaster));
            var canvas = canvasGo.GetComponent<Canvas>(); canvas.renderMode = RenderMode.ScreenSpaceOverlay;
            var scaler = canvasGo.GetComponent<CanvasScaler>(); scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize; scaler.referenceResolution = new Vector2(540f, 960f); scaler.matchWidthOrHeight = 0.5f;
            var hud = canvasGo.AddComponent<HUD>();
            hud.buyShelf = Color.white; hud.buyText = GText;                                             // a price you can pay: the card's pill as painted
            hud.cantShelf = new Color(0.55f, 0.57f, 0.62f); hud.cantText = new Color(0.86f, 0.88f, 0.92f);   // one you cannot: the pill dimmed to grey
            hud.buyFace = hud.cantFace = Color.white; hud.badgeLevel = true; hud.pricePlain = true;
            hud.hangar = hangar; hud.soundOn = gIcoSoundOn; hud.soundOff = gIcoSoundOff;   // the speaker glyphs swap between these (the pause row, the settings screen)
            var flash = UIImage("Flash", canvasGo.transform, new Color(1f, 1f, 1f, 0f), Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero); hud.flashImage = flash;
            var warn = UIImage("Warn", canvasGo.transform, new Color(1f, 0.23f, 0.31f, 0f), Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero); hud.warnImage = warn;

            var play = UI("PlayGroup", canvasGo.transform, Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero); hud.playGroup = play.gameObject;
            // top (the references, 2026-09-19): the pause as a blue square at the left, the horde bar with its percent and a flag in the middle,
            // the bank at the right with the plane count under it; settings live on the pause screen
            var pauseBtn = SquareButton("PauseBtn", play, TL, new Vector2(40f, -40f), 48f, gIcoPause, 20f);
            UnityEditor.Events.UnityEventTools.AddPersistentListener(pauseBtn.onClick, hud.OnPauseButton);
            Bar("Progress", play, TC, new Vector2(-14f, -40f), new Vector2(190f, 22f), GSky, out var progressFill);
            hud.progressFill = progressFill.rectTransform; hud.progressImage = progressFill; hud.progressWidth = 182f;
            hud.progressText = Type("ProgressText", play, "HORDE 1   0%", 14f, GText, TC, new Vector2(-14f, -40f), new Vector2(190f, 22f), true);
            var flag = Icon("Flag", play, gIcoFlag, GText, TC, new Vector2(94f, -36f), 26f); { var ol = flag.gameObject.AddComponent<Outline>(); ol.effectColor = new Color(0.08f, 0.14f, 0.28f, 1f); ol.effectDistance = new Vector2(2f, -2f); }
            GButton("BossBadge", play, TC, new Vector2(-166f, -40f), new Vector2(60f, 28f), gBtnRed, 175f, "BOSS", 12f, GText, out _, out _, false);
            hud.levelText = null;
            var coins = CoinBar("Coins", play, TR, new Vector2(-88f, -34f), new Vector2(140f, 40f), gResCoin, 46f);
            hud.coinsText = Type("CoinsText", coins, "0", 22f, GText, Mid, new Vector2(-10f, 1f), new Vector2(100f, 40f));
            var popRt = UI("CoinPop", play, TR, TR, new Vector2(-88f, -66f), new Vector2(140f, 24f));
            var popGroup = popRt.gameObject.AddComponent<CanvasGroup>(); popGroup.alpha = 0f; hud.coinPopGroup = popGroup;
            hud.coinPopText = Type("CoinPopText", popRt, "+0", 16f, GGold, Mid, new Vector2(-10f, 0f), new Vector2(140f, 24f), true);
            var planes = CoinBar("PlanesBadge", play, TR, new Vector2(-88f, -96f), new Vector2(140f, 40f), gIcoPlane, 32f);
            hud.planesText = Type("Planes", planes, "0", 22f, GText, Mid, new Vector2(-10f, 1f), new Vector2(100f, 40f));
            // bottom left: the weapon, small
            var weapon = Plate("Weapon", play, BL, new Vector2(88f, 32f), new Vector2(160f, 46f), new Color(GNavy.r, GNavy.g, GNavy.b, 0.85f));
            hud.weaponName = Type("WeaponName", weapon, "GATLING", 17f, GGold, Mid, new Vector2(0f, 8f), new Vector2(160f, 22f));
            hud.weaponDesc = Type("WeaponDesc", weapon, "single target, fast", 11f, GTextDim, Mid, new Vector2(0f, -10f), new Vector2(160f, 16f), true);
            var hintRt = UI("Hint", play, BC, BC, new Vector2(0f, 150f), new Vector2(300f, 62f));   // the kit's yellow pill
            GImg("Face", hintRt, gBtnYellow, Color.white, Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero, Fit(145f, 62f));
            var hintGroup = hintRt.gameObject.AddComponent<CanvasGroup>(); hud.hintGroup = hintGroup;
            hud.hintText = Type("HintText", hintRt, "DRAG TO FLY\nDIVE for crates  ·  CLIMB to fight", 13f, GInk, Mid, new Vector2(0f, 3f), new Vector2(280f, 50f), true);

            // the banner: the kit's orange ribbon across the screen, the words on it
            var bannerRt = UI("Banner", canvasGo.transform, Mid, Mid, new Vector2(0f, 190f), new Vector2(560f, 72f));
            var bannerGroup = bannerRt.gameObject.AddComponent<CanvasGroup>(); bannerGroup.alpha = 0f; hud.bannerGroup = bannerGroup;
            GImg("BannerBg", bannerRt, gRibbon, Color.white, Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero, Fit(142f, 72f));
            hud.bannerText = Type("BannerText", bannerRt, "", 40f, GText, Mid, new Vector2(0f, 4f), new Vector2(540f, 72f));

            // the lobby: the same top bar (gear, attempt words, the bank), the name, the jet in its hangar, the start pill, the three upgrade cards
            var title = Panel("TitlePanel", canvasGo.transform, 0.0f); hud.titlePanel = title;
            var lobbyGear = GlyphButton("LobbyGear", title.transform, TL, new Vector2(40f, -40f), 40f, gIcoGear);
            UnityEditor.Events.UnityEventTools.AddPersistentListener(lobbyGear.onClick, hud.OnSettingsButton);
            hud.attemptInfo = Type("AttemptInfo", title.transform, "Attempt 1", 26f, GText, TC, new Vector2(0f, -40f), new Vector2(300f, 40f));
            var lobbyCoins = CoinBar("LobbyCoins", title.transform, TR, new Vector2(-88f, -34f), new Vector2(140f, 40f), gResCoin, 46f);
            hud.lobbyCoins = Type("LobbyCoinsText", lobbyCoins, "0", 22f, GText, Mid, new Vector2(-10f, 1f), new Vector2(100f, 40f));
            Type("T1", title.transform, "SKY <color=#FFB020>SQUAD</color>", 64f, GText, TC, new Vector2(0f, -118f), new Vector2(520f, 80f));   // one wordmark on one line
            if (hangarRt != null)
            {
                var hv = UI("HangarView", title.transform, TC, TC, new Vector2(0f, -280f), new Vector2(440f, 250f));
                var raw = hv.gameObject.AddComponent<RawImage>(); raw.texture = hangarRt; raw.raycastTarget = false;
            }
            var startBtn = GButtonClick("StartBtn", title.transform, BC, new Vector2(0f, 334f), new Vector2(300f, 60f), gBtnBig, 244f, "TAP TO START", 24f, GInk, gIcoPlay, 20f);
            startBtn.transform.Find("Icon").GetComponent<Image>().color = GInk;
            UnityEditor.Events.UnityEventTools.AddPersistentListener(startBtn.onClick, hud.OnStartButton);
            string[] cardNames = { "FIRE RATE", "DAMAGE", "REVENUE" };
            Color[] cardCols = { new Color(0.52f, 0.78f, 0.22f), new Color(0.20f, 0.62f, 0.95f), new Color(0.98f, 0.76f, 0.16f) };   // the reference's green / blue / yellow
            Sprite[] cardPills = { G("Button/Button01_145_Green"), G("Button/Button01_145_Blue"), gBtnYellow };
            Sprite[] cardIcons = { gIcoThunder, gIcoTarget, G("IconMisc/Icon_ImageIcon_Coin01_l") };
            Color[] cardIconTint = { Color.white, Color.white, Color.white };
            for (int i = 0; i < 3; i++)
            {   // an upgrade card (the reference, 2026-09-19): the coloured frame, its name in the head, the level in a grey badge at the corner, the picture
                // in a darker body, five pips (level mod 5), the UPGRADE pill with the coin and the price; tap anywhere on the card to buy
                float cx = (i - 1) * 172f; var col = cardCols[i];
                var card = UI("Card" + i, title.transform, BC, BC, new Vector2(cx, 150f), new Vector2(164f, 262f));
                var cardFace = GImg("Face", card, gRound20, col, Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero, Fit(50f, 60f)); cardFace.raycastTarget = true;
                var buy = card.gameObject.AddComponent<Button>(); buy.transition = Selectable.Transition.None; buy.targetGraphic = cardFace;
                UnityEditor.Events.UnityEventTools.AddIntPersistentListener(buy.onClick, hud.OnBuy, i);
                var cardFx = card.gameObject.AddComponent<UIButtonFx>(); cardFx.tint = cardFace; cardFx.pressedColor = col * 0.8f;
                Type("CardName" + i, card, cardNames[i], 17f, GText, TC, new Vector2(-6f, -22f), new Vector2(150f, 26f));
                var body = GImg("Body", card, gRound20, new Color(col.r * 0.55f, col.g * 0.55f, col.b * 0.62f), TC, TC, new Vector2(0f, -46f), new Vector2(148f, 118f), Fit(50f, 60f));   // a darker well for the picture
                body.rectTransform.pivot = new Vector2(0.5f, 1f);
                Icon("CardIcon" + i, body.transform, cardIcons[i], cardIconTint[i], Mid, new Vector2(0f, 0f), 84f);
                hud.cardEffect[i] = Type("CardEffect" + i, body.transform, "", 12f, GText, BC, new Vector2(0f, 12f), new Vector2(140f, 18f), true);
                var badge = GImg("Badge" + i, card, gCircleNavy, new Color(0.38f, 0.40f, 0.45f), TR, TR, new Vector2(6f, 8f), new Vector2(42f, 42f), 1f, false);
                hud.cardLevel[i] = Type("CardLevel" + i, badge.transform, "0", 20f, GText, Mid, new Vector2(0f, 1f), new Vector2(42f, 42f));
                for (int k = 0; k < 5; k++)
                {   // the pips: five small rounded blocks
                    var pip = GImg("Pip" + i + "_" + k, card, gRound20, hud.pipOff, TC, TC, new Vector2(-56f + k * 28f, -176f), new Vector2(24f, 16f), Fit(50f, 24f));
                    hud.cardPips[i * 5 + k] = pip;
                }
                hud.cardPipOn[i] = new Color(Mathf.Min(1f, col.r * 1.15f), Mathf.Min(1f, col.g * 1.15f), Mathf.Min(1f, col.b * 1.15f));
                var pill = GButton("CardBuy" + i, card, BC, new Vector2(0f, 34f), new Vector2(148f, 56f), cardPills[i], 145f, "", 15f, GText, out hud.cardBuyShelf[i], out _, false);
                Type("UpgradeWord" + i, pill, "UPGRADE", 15f, GText, TC, new Vector2(0f, -15f), new Vector2(148f, 20f));
                Icon("PriceCoin" + i, pill, gIcoCoin, Color.white, BC, new Vector2(-30f, 16f), 18f);
                hud.cardCost[i] = Type("CardPrice" + i, pill, "0", 15f, GText, BC, new Vector2(8f, 16f), new Vector2(90f, 20f), true);
                hud.cardBuyFace[i] = null;
            }
            Type("LobbyHint", title.transform, "same round every attempt - spend, then go again   |   desktop: arrows / WASD", 11f, GText, BC, new Vector2(0f, 8f), new Vector2(520f, 16f), true);

            // the overlays: a dark backdrop and a kit popup each, its flag title over the top edge, the big words in the body, the prompt as an orange pill
            var clear = Panel("ClearPanel", canvasGo.transform, 0.72f); hud.clearPanel = clear;
            var clearCard = Card("ClearCard", clear.transform, Mid, new Vector2(0f, 20f), new Vector2(460f, 420f), gFlagOrange, "MISSION REPORT", 24f);
            hud.clearTitle = Type("C1", clearCard, "BOSS", 66f, GText, Mid, new Vector2(0f, 76f), new Vector2(440f, 84f));
            hud.clearSub = Type("C2", clearCard, "DOWN!", 66f, GGold, Mid, new Vector2(0f, 6f), new Vector2(440f, 84f));
            hud.clearStats = Type("CStats", clearCard, "", 14f, GTextDim, Mid, new Vector2(0f, -70f), new Vector2(420f, 60f), true);
            GButton("CTapBtn", clearCard, Mid, new Vector2(0f, -150f), new Vector2(300f, 58f), gBtnOrange, 145f, "TAP FOR NEXT", 24f, GText, out _, out hud.clearTap, false);

            var over = Panel("OverPanel", canvasGo.transform, 0.78f); hud.overPanel = over;
            var overCard = Card("OverCard", over.transform, Mid, new Vector2(0f, 5f), new Vector2(460f, 440f), gFlagRed, "SQUADRON LOST", 24f);
            Type("O1", overCard, "SQUADRON", 52f, GText, Mid, new Vector2(0f, 92f), new Vector2(440f, 70f));
            Type("O2", overCard, "LOST", 66f, GRed, Mid, new Vector2(0f, 26f), new Vector2(440f, 84f));
            GButton("OReasonBar", overCard, Mid, new Vector2(0f, -50f), new Vector2(400f, 46f), gBtnRed, 175f, "", 14f, GText, out _, out hud.overReason, false);
            hud.overStats = Type("OStats", overCard, "", 13f, GTextDim, Mid, new Vector2(0f, -100f), new Vector2(430f, 40f), true);
            GButton("OTapBtn", overCard, Mid, new Vector2(0f, -162f), new Vector2(300f, 58f), gBtnOrange, 145f, "TAP TO CONTINUE", 24f, GText, out _, out _, false);

            var pause = Panel("PausePanel", canvasGo.transform, 0.0f); hud.pausePanel = pause;   // the reference's pause: a blue dim, a row of glyphs, HOME and RESUME
            UIImage("PauseDim", pause.transform, new Color(0.12f, 0.30f, 0.50f, 0.72f), Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero);
            {
                var soundGlyph = GlyphButton("PauseSound", pause.transform, Mid, new Vector2(-60f, 150f), 44f, gIcoSoundOn);
                UnityEditor.Events.UnityEventTools.AddPersistentListener(soundGlyph.onClick, hud.ToggleSound);
                var gearGlyph = GlyphButton("PauseGear", pause.transform, Mid, new Vector2(60f, 150f), 44f, gIcoGear);
                UnityEditor.Events.UnityEventTools.AddPersistentListener(gearGlyph.onClick, hud.OnSettingsButton);
                hud.soundIcons = new[] { soundGlyph.GetComponent<Image>() };
            }
            var homeBtn = GButtonClick("HomeBtn", pause.transform, Mid, new Vector2(0f, 10f), new Vector2(300f, 66f), gBtnGray, 145f, "HOME", 28f, GText);
            UnityEditor.Events.UnityEventTools.AddPersistentListener(homeBtn.onClick, hud.OnHomeButton);
            var resumeBtn = GButtonClick("ResumeBtn", pause.transform, Mid, new Vector2(0f, -80f), new Vector2(300f, 66f), gBtnSky, 145f, "RESUME", 28f, GText);
            UnityEditor.Events.UnityEventTools.AddPersistentListener(resumeBtn.onClick, hud.OnResumeButton);

            // settings (the reference, 2026-09-19): a full screen of light blue with a dot pattern, SETTINGS and the bank at the top, the PLANE SPEED bar
            // with its slider, the speaker glyph, credits and the version at the bottom, a big white X to close
            var settings = Panel("SettingsPanel", canvasGo.transform, 1f); hud.settingsPanel = settings; settings.GetComponent<Image>().raycastTarget = true; settings.GetComponent<Image>().color = new Color(0.33f, 0.62f, 0.78f, 1f);
            { var dots = UIImage("Dots", settings.transform, new Color(1f, 1f, 1f, 0.07f), Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero); dots.sprite = uiCircle; dots.type = Image.Type.Tiled; dots.pixelsPerUnitMultiplier = 64f / 48f; }
            Type("STitle", settings.transform, "SETTINGS", 42f, GText, TC, new Vector2(-60f, -50f), new Vector2(360f, 60f));
            var sCoins = CoinBar("SettingsCoins", settings.transform, TR, new Vector2(-88f, -34f), new Vector2(140f, 40f), gResCoin, 46f);
            hud.settingsCoins = Type("SettingsCoinsText", sCoins, "0", 22f, GText, Mid, new Vector2(-10f, 1f), new Vector2(100f, 40f));
            var speedBar = GButton("SpeedBar", settings.transform, Mid, new Vector2(0f, 150f), new Vector2(340f, 64f), gBtnGray, 145f, "", 24f, GText, out _, out _, false);
            Type("SLabel", speedBar, "PLANE SPEED:", 24f, GText, Mid, new Vector2(-34f, 3f), new Vector2(240f, 40f));
            hud.dragValueText = Type("SValue", speedBar, "20", 30f, GText, Mid, new Vector2(108f, 3f), new Vector2(80f, 40f));
            hud.dragSlider = UISlider("DragSlider", settings.transform, new Vector2(0f, 90f), new Vector2(340f, 34f), Settings.DragMin, Settings.DragMax);
            UnityEditor.Events.UnityEventTools.AddPersistentListener(hud.dragSlider.onValueChanged, new UnityEngine.Events.UnityAction<float>(hud.OnDragSlider));
            Type("SHint", settings.transform, "how far the squad flies for one thumb swipe", 13f, GText, Mid, new Vector2(0f, 56f), new Vector2(420f, 24f), true);
            {
                var soundGlyph = GlyphButton("SettingsSound", settings.transform, Mid, new Vector2(0f, -40f), 60f, gIcoSoundOn);
                UnityEditor.Events.UnityEventTools.AddPersistentListener(soundGlyph.onClick, hud.ToggleSound);
                hud.soundIcons = new[] { hud.soundIcons[0], soundGlyph.GetComponent<Image>() };
                Type("SSoundLabel", settings.transform, "SOUND", 16f, GText, Mid, new Vector2(0f, -90f), new Vector2(200f, 24f), true);
            }
            Type("SCredits", settings.transform, "SKY SQUAD\nmtjrcloud", 14f, GText, BL, new Vector2(110f, 120f), new Vector2(200f, 44f), true, TextAlignmentOptions.Left);
            Type("SVersion", settings.transform, "v" + PlayerSettings.bundleVersion, 16f, GText, BR, new Vector2(-70f, 120f), new Vector2(120f, 24f), true, TextAlignmentOptions.Right);
            var closeBtn = GlyphButton("SettingsClose", settings.transform, BC, new Vector2(0f, 70f), 56f, gIcoClose);
            UnityEditor.Events.UnityEventTools.AddPersistentListener(closeBtn.onClick, hud.OnSettingsDone);
            settings.SetActive(false);

            // the loading screen (the reference, 2026-09-19): the two-tone logo over the sky, the jet in its hangar, a yellow bar filling to 100%
            var splash = Panel("SplashPanel", canvasGo.transform, 1f); hud.splashPanel = splash; splash.GetComponent<Image>().raycastTarget = true; splash.GetComponent<Image>().color = new Color(0.45f, 0.78f, 0.95f, 1f);
            { var dots = UIImage("Dots", splash.transform, new Color(1f, 1f, 1f, 0.08f), Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero); dots.sprite = uiCircle; dots.type = Image.Type.Tiled; dots.pixelsPerUnitMultiplier = 64f / 48f; }
            Type("SplashSky", splash.transform, "SKY", 110f, GSky, TC, new Vector2(0f, -170f), new Vector2(520f, 120f));
            Type("SplashSquad", splash.transform, "SQUAD", 110f, new Color(1f, 0.62f, 0.15f), TC, new Vector2(0f, -270f), new Vector2(520f, 120f));
            Type("SplashTag", splash.transform, "ONE PLANE. THEN A SQUADRON.", 18f, GText, TC, new Vector2(0f, -350f), new Vector2(520f, 30f));
            if (hangarRt != null) { var hv = UI("SplashHangar", splash.transform, Mid, Mid, new Vector2(0f, -40f), new Vector2(500f, 320f)); var raw = hv.gameObject.AddComponent<RawImage>(); raw.texture = hangarRt; raw.raycastTarget = false; }
            {
                var barRt = UI("SplashBar", splash.transform, BC, BC, new Vector2(0f, 120f), new Vector2(460f, 40f));
                GImg("Track", barRt, gSliderBg, GNavyDark, Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero, Fit(46f, 40f));
                var fill = GImg("Fill", barRt, gSliderFillYellow, Color.white, Vector2.zero, Vector2.one, Vector2.zero, new Vector2(-8f, -8f), Fit(67f, 32f));
                fill.type = Image.Type.Filled; fill.fillMethod = Image.FillMethod.Horizontal; fill.fillOrigin = 0; fill.fillAmount = 0f;
                hud.splashFill = fill;
                hud.splashPercent = Type("SplashPercent", barRt, "0%", 26f, GText, Mid, new Vector2(0f, 2f), new Vector2(200f, 40f));
                Type("SplashLoading", splash.transform, "LOADING", 30f, GText, BC, new Vector2(0f, 70f), new Vector2(300f, 40f));
            }

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
