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
        static TMP_FontAsset font, fontUi, fontUiLight; static Material fontOutline, fontOutlineSmall, fontUiPlain, fontUiLightPlain, fontUiTitle, fontUiInk;

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
            ImportKit();   // the bought sheets and icons (2026-09-18): borders, import settings, the sprite lookups
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
            // the screen UI (2026-09-19, GUI Pro Casual): Lilita One everywhere, white with the kit's navy outline and a soft drop shadow - the
            // reference's type. (Barlow Condensed, the tactical face of 2026-09-18, is out; its TTFs stay in Fonts.)
            fontUi = font; fontUiLight = font;
            fontUiPlain = FontPreset(font, "LilitaOne UI", 0.30f, UiNavy, true, 0.5f);          // bold outlines, like the reference ("the words should have bolder outlines", 2026-09-19)
            fontUiLightPlain = FontPreset(font, "LilitaOne UI Thin", 0.22f, UiNavy, true, 0.4f);
            fontUiTitle = FontPreset(font, "LilitaOne UI Title", 0.34f, UiNavy, true, 0.7f);
            fontUiPlain.SetFloat(ShaderUtilities.ID_FaceDilate, 0.1f); fontUiTitle.SetFloat(ShaderUtilities.ID_FaceDilate, 0.1f);   // and a heavier face
            fontUiInk = FontPreset(font, "LilitaOne Ink", 0f, Color.black, false);   // dark type on the white panels: no outline
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
                // the bright day (2026-09-19, "from sunset to bright day, matching the new UI"): the reference's vivid cartoon sea - a saturated
                // blue, lighter through the crests, white foam; the reflection is the gradient sky's own two colours (SkyGradient.shader / fog)
                m.SetColor("_ShallowColor", new Color(0.22f, 0.66f, 0.95f)); m.SetColor("_DeepColor", new Color(0.08f, 0.40f, 0.82f)); m.SetColor("_SSSColor", new Color(0.30f, 0.85f, 0.95f));
                m.SetColor("_SkyHorizon", new Color(0.62f, 0.85f, 0.98f)); m.SetColor("_SkyZenith", new Color(0.25f, 0.60f, 0.95f)); m.SetColor("_FoamColor", new Color(1f, 1f, 1f));
                m.SetTexture("_BaseMap", SeaNormalTexture()); m.SetTextureScale("_BaseMap", Vector2.one); m.SetTextureOffset("_BaseMap", Vector2.zero);
                m.SetTexture("_FoamMap", SeaFoamTexture()); m.SetTextureScale("_FoamMap", new Vector2(0.07f, 0.07f));   // tiles per unit: one foam tile every ~14 units
                m.SetFloat("_Tiling", 0.12f); m.SetFloat("_NormalStrength", 0.3f);
                m.SetVector("_WaveA", new Vector4(0.15f, -1f, 0.10f, 16f)); m.SetVector("_WaveB", new Vector4(0.6f, -0.8f, 0.09f, 9f));   // (dir x, dir z, steepness, length): a long swell toward the player and three shorter crossing waves; amplitude = steepness / k
                m.SetVector("_WaveC", new Vector4(-0.7f, -0.7f, 0.07f, 5.5f)); m.SetVector("_WaveD", new Vector4(0.3f, -0.95f, 0.05f, 3.5f));
                m.SetFloat("_WaveSpeed", 1f); m.SetFloat("_Reflect", 0.5f); m.SetFloat("_Fresnel", 4f);
                m.SetFloat("_SpecPower", 220f); m.SetFloat("_SpecIntensity", 1.0f); m.SetFloat("_Foam", 0.5f); m.SetFloat("_FoamStart", 0.6f);   /* some whitecaps (0.75 / 0.5 streaked the whole sea white) */
            });
            M.cloud = Transparent("Cloud", new Color(1f, 1f, 1f, 0.72f)); M.cloud.SetTexture("_BaseMap", CloudTexture());   /* white for the bright day (grey-mauve in the dusk) */   // softer now that the real sky has its own clouds: these are the near, moving ones
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
        static Sprite uiChamfer, uiChamferEdge, uiSoft, uiCircle, uiGrad, uiPill, uiPillSlant, uiPillSlantStroke, uiTicks, uiCoin, uiGear, uiPause, uiPlane, uiCross, uiPlay, uiSoundOn, uiSoundOff;
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
                imp.mipmapEnabled = true; imp.wrapMode = repeat ? TextureWrapMode.Repeat : TextureWrapMode.Clamp; imp.filterMode = FilterMode.Trilinear; imp.alphaIsTransparency = true; imp.sRGBTexture = true;   // mipmaps + trilinear (2026-09-19): a sprite drawn below its source scale (the pips' pill at 2 source px per unit in a 1x Game view) aliased without them
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
        /// <summary>A rounded bar whose right end is slanted (the reference's diamonds pill, 2026-09-19): the shear ramps in over the right
        /// half, so the left end stays straight for the "+" button to sit on. Not a true distance under the varying shear, but the
        /// zero crossing is exact and the edge stays anti-aliased.</summary>
        static float SlantPill(float x, float y, float hw, float hh, float r)
        {
            float k = Mathf.SmoothStep(0f, 1f, (x + 20f) / 80f) * 0.34f;
            return RoundBox(x - k * y, y, hw, hh, r);
        }
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
            uiGrad = SaveSprite(Shape(8, 64, (x, y) => White(Mathf.Clamp01(0.5f - y / 64f))), "UI_Grad", Vector4.zero);
            uiPill = SaveSprite(Shape(32, 32, (x, y) => White(Edge(RoundBox(x, y, 16f, 16f, 10f)))), "UI_Pill", new Vector4(12f, 12f, 12f, 12f));
            uiPillSlant = SaveSprite(Shape(176, 60, (x, y) => White(Edge(SlantPill(x, y, 76f, 30f, 12f)))), "UI_PillSlant", Vector4.zero);                // the diamonds pill, drawn whole at 88 x 30 (0.5 unit per px)
            uiPillSlantStroke = SaveSprite(Shape(190, 74, (x, y) => White(Edge(SlantPill(x, y, 83f, 37f, 19f)))), "UI_PillSlantStroke", Vector4.zero);    // ...and its outline: the same shape 7 px (3.5 units) fatter, drawn at 95 x 37   // a small rounded rect, supersampled, for tiny things drawn near 1:1 (the cards' pips: the kit's 51-px frame squeezed to 19 x 13 aliased, 2026-09-19)   // solid at the bottom, clear at the top: the cards' picture panels shade dark-to-light like the reference (2026-09-19)
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

        const float SkyRotation = 90f;   // turns the HDRI so the dark cloud roof fills the view with the sunset glow low on the right (0 = grey mass ahead, 105-180 = the bare sun: washed out), over the enemies (the Belfast sky; 120 put the Kloofendal sky's blue cumulus side ahead)

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
        static GameObject Panel(string name, Transform parent, float alpha) => Panel(name, parent, new Color(0.01f, 0.015f, 0.03f, alpha));
        static GameObject Panel(string name, Transform parent, Color c)
        {
            var im = UIImage(name, parent, c, Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero);
            im.raycastTarget = false;
            return im.gameObject;
        }

        // ------------------------------------------------------------ UI kit (2026-09-19, fourth pass: GUI Pro - Casual Game)
        // "Use GUI Pro Casual and make it like the reference" (Real War's screens): chunky rounded buttons on a darker shelf, white rounded
        // panels with a navy outline, the navy resource pill with the gold coin hanging off its end, coloured upgrade cards with a grey level
        // badge and pips, flags and ribbons for titles, flat white picto icons, and Lilita One in white with a navy outline on everything (the
        // kit ships that very font). Layer Lab's sprites are authored for a 1080-wide canvas at 100 px per unit; this canvas is 540 wide, so
        // most are drawn at pixelsPerUnitMultiplier 2-3 (a 145-px button is ~55 units tall). Every kit sprite is loaded by file name from
        // Assets/Layer Lab/GUI Pro-CasualGame (only the sprite folders were copied in, with their metas, so the 9-slice borders come along);
        // a missing file warns and falls back to the generated chamfer plate, so a build never breaks on art.
        // (The Strategic Warfare / AIRIDev pass of 2026-09-18 came before this; those packs stay in the project, unused.)
        const string PlanePackDir = "Assets/EmbersStorm - AirStrike Aviation Pack/Prefabs/";
        const string GpDir = "Assets/Layer Lab/GUI Pro-CasualGame/ResourcesData/Sprites/Components/";
        static readonly Dictionary<string, Sprite> gp = new Dictionary<string, Sprite>();
        static Sprite Gp(string rel)
        {
            if (gp.TryGetValue(rel, out var s)) return s;
            s = AssetDatabase.LoadAssetAtPath<Sprite>(GpDir + rel);
            if (s == null) Debug.LogWarning("[SkySquad] GUI Pro sprite missing: " + GpDir + rel);
            gp[rel] = s;
            return s;
        }
        static Sprite Picto(string name) => Gp("Icon_PictoIcons/128/Pictoicon_" + name + ".Png");
        /// <summary>The picture panel's background for upgrade card i (2026-09-19, "a gradient, each icon its own style"): a rounded 224 x 200
        /// texture generated from the card's colour. FIRE RATE: dark at the top shading to bright at the bottom. DAMAGE: a light glow behind the
        /// icon on deep blue, darker toward the bottom. REVENUE: orange at the top-left to yellow at the bottom-right, a warm glow behind the coins.
        /// Drawn over the panel's face at its size; the rounded alpha edge matches the face's corners.</summary>
        static Sprite CardGradient(int style, Color col)
        {
            Color dark = Color.Lerp(col, UiNavy, 0.55f), light = Color.Lerp(col, Color.white, 0.18f), glow = Color.Lerp(col, Color.white, 0.42f);
            Color warm = Color.Lerp(col, UiOrange, 0.85f); warm = Color.Lerp(warm, UiNavy, 0.12f);
            float Smooth(float t) { t = Mathf.Clamp01(t); return t * t * (3f - 2f * t); }
            var t = Shape(224, 200, (x, y) =>
            {
                float a = Edge(RoundBox(x, y, 112f, 100f, 8f));
                float u = (x + 112f) / 224f, v = (y + 100f) / 200f;                          // 0..1 across and up
                float d = Mathf.Sqrt(x * x / (112f * 112f) + y * y / (100f * 100f));         // 0 at the centre, 1 on the edge ellipse
                Color c;
                switch (style)
                {
                    case 1: c = Color.Lerp(glow, dark, Smooth(d * 1.05f)); c = Color.Lerp(c, dark, (1f - v) * 0.25f); break;
                    case 2: c = Color.Lerp(warm, light, Smooth((u - v + 1f) * 0.5f)); c = Color.Lerp(c, glow, (1f - Smooth(d / 0.8f)) * 0.55f); break;
                    default: c = Color.Lerp(light, dark, Smooth(v)); break;
                }
                c.a = a;
                return c;
            });
            return SaveSprite(t, "UI_CardGrad" + style, Vector4.zero);
        }
        /// <summary>A sprite from Art/UI (the user's own pictures, e.g. the mortar rocket on the DAMAGE card): imported as a single 256-px sprite, no mips.</summary>
        static Sprite ArtSprite(string file)
        {
            string path = Root + "/Art/UI/" + file;
            var imp = AssetImporter.GetAtPath(path) as TextureImporter;
            if (imp == null) { AssetDatabase.ImportAsset(path); imp = AssetImporter.GetAtPath(path) as TextureImporter; }
            if (imp == null) { Debug.LogWarning("[SkySquad] art sprite missing: " + path); return null; }
            if (imp.textureType != TextureImporterType.Sprite || imp.spriteImportMode != SpriteImportMode.Single || imp.mipmapEnabled || imp.maxTextureSize != 256)
            {
                imp.textureType = TextureImporterType.Sprite; imp.spriteImportMode = SpriteImportMode.Single; imp.spritePixelsPerUnit = 100f;
                imp.mipmapEnabled = false; imp.alphaIsTransparency = true; imp.wrapMode = TextureWrapMode.Clamp; imp.maxTextureSize = 256; imp.filterMode = FilterMode.Bilinear;
                var ts = imp.GetDefaultPlatformTextureSettings(); ts.textureCompression = TextureImporterCompression.CompressedHQ; imp.SetPlatformTextureSettings(ts);
                imp.SaveAndReimport();
            }
            return AssetDatabase.LoadAssetAtPath<Sprite>(path);
        }
        static void ImportKit() { gp.Clear(); }   // the sprites load on demand (Gp); the kit's metas carry their import settings and borders

        // the palette: the kit's own colours, which are the reference's
        static readonly Color UiNavy = new Color(0.12f, 0.19f, 0.32f);            // the outline / dark ink of the kit
        static readonly Color UiInkText = new Color(0.20f, 0.29f, 0.42f);         // body text on white panels
        static readonly Color UiSkyBlue = new Color(0.23f, 0.61f, 0.91f);         // the settings screen, the blue card
        static readonly Color UiGreen = new Color(0.47f, 0.77f, 0.25f);
        static readonly Color UiYellow = new Color(0.98f, 0.77f, 0.19f);
        static readonly Color UiOrange = new Color(1f, 0.55f, 0.17f);
        static readonly Color UiRed = new Color(0.93f, 0.29f, 0.30f);
        static readonly Color UiGrey = new Color(0.66f, 0.70f, 0.75f);            // pips off, a greyed button
        static readonly Color UiDim = new Color(0.62f, 0.62f, 0.62f);             // the tint on a button that cannot be pressed
        static readonly Color UiPressed = new Color(0.72f, 0.72f, 0.72f);         // a button's tint while pressed (UIButtonFx lerps toward it)
        static readonly Vector2 Mid = new Vector2(0.5f, 0.5f), TL = new Vector2(0f, 1f), TC = new Vector2(0.5f, 1f), TR = new Vector2(1f, 1f), BL = new Vector2(0f, 0f), BC = new Vector2(0.5f, 0f), BR = new Vector2(1f, 0f);

        /// <summary>A kit sprite as an Image: 9-sliced with its own borders at 1 / ppuMul of its pixels in canvas units, or (sliced = false)
        /// drawn whole at its own aspect inside the rect. Falls back to the generated chamfer plate when the file is not in the project.</summary>
        static Image Kit(string name, Transform parent, string sprite, Color tint, Vector2 anchorMin, Vector2 anchorMax, Vector2 pos, Vector2 size, float ppuMul = 2f, bool sliced = true)
        {
            var im = UIImage(name, parent, tint, anchorMin, anchorMax, pos, size);
            var s = Gp(sprite);
            if (s != null) { im.sprite = s; im.type = sliced ? Image.Type.Sliced : Image.Type.Simple; im.pixelsPerUnitMultiplier = ppuMul; im.preserveAspect = !sliced; }
            else { im.sprite = uiChamfer; im.type = Image.Type.Sliced; im.pixelsPerUnitMultiplier = UiCut / 8f; }
            return im;
        }
        static Image Icon(string name, Transform parent, Sprite s, Color c, Vector2 anchor, Vector2 pos, float size)
        {
            var im = UIImage(name, parent, c, anchor, anchor, pos, new Vector2(size, size));
            im.sprite = s; im.type = Image.Type.Simple; im.preserveAspect = true;
            return im;
        }
        /// <summary>Kit(), given the sprite itself (a generated one, or a kit sprite already looked up).</summary>
        static Image KitS(string name, Transform parent, Sprite s, Color tint, Vector2 anchorMin, Vector2 anchorMax, Vector2 pos, Vector2 size, float ppuMul = 2f, bool sliced = true)
        {
            var im = UIImage(name, parent, tint, anchorMin, anchorMax, pos, size);
            if (s != null) { im.sprite = s; im.type = sliced ? Image.Type.Sliced : Image.Type.Simple; im.pixelsPerUnitMultiplier = ppuMul; im.preserveAspect = !sliced; }
            else { im.sprite = uiChamfer; im.type = Image.Type.Sliced; im.pixelsPerUnitMultiplier = UiCut / 8f; }
            return im;
        }
        const float UiStroke = 3.5f;   // the bold outline the reference draws round every card, band, pip, button, badge and pill ("bold outlines", 2026-09-19)
        /// <summary>A kit sprite with that bold outline: a navy copy of the same sprite stroke units larger on every side, under the tinted one.
        /// Returns the root; "Face" is the coloured image, "Stroke" the outline.</summary>
        static RectTransform Outlined(string name, Transform parent, string sprite, Color tint, Vector2 anchorMin, Vector2 anchorMax, Vector2 pos, Vector2 size, float ppuMul = 2f, float stroke = -1f, bool sliced = true)
        {
            if (stroke < 0f) stroke = UiStroke;
            var rt = UI(name, parent, anchorMin, anchorMax, pos, size);
            Kit("Stroke", rt, sprite, UiNavy, Vector2.zero, Vector2.one, Vector2.zero, new Vector2(stroke * 2f, stroke * 2f), ppuMul, sliced);
            Kit("Face", rt, sprite, tint, Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero, ppuMul, sliced);
            return rt;
        }
        /// <summary>A chunky slab, the reference's depth: the navy outline round both, a darker shelf depth units under the face, the face on top.
        /// Returns the root; "Face" is the coloured image, "Shelf" the darker one under it.</summary>
        static RectTransform Chunk(string name, Transform parent, Sprite sprite, Color face, Color shelf, Vector2 anchorMin, Vector2 anchorMax, Vector2 pos, Vector2 size, float ppuMul, float depth, float stroke, float radiusPx = 0f)
        {
            var rt = UI(name, parent, anchorMin, anchorMax, pos, size);
            // the stroke is an enlarged copy: for its corners to run concentric with the face's (radius + stroke), it is drawn at its own scale -
            // radiusPx / (radiusPx / ppuMul + stroke) - else the outline thins at the ends of a small slab (the pips, 2026-09-19)
            float strokePpu = radiusPx > 0f ? radiusPx / (radiusPx / ppuMul + stroke) : ppuMul;
            if (stroke > 0f) KitS("Stroke", rt, sprite, UiNavy, Vector2.zero, Vector2.one, new Vector2(0f, -depth * 0.5f), new Vector2(stroke * 2f, stroke * 2f + depth), strokePpu);
            KitS("Shelf", rt, sprite, shelf, Vector2.zero, Vector2.one, new Vector2(0f, -depth), Vector2.zero, ppuMul);
            KitS("Face", rt, sprite, face, Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero, ppuMul);
            return rt;
        }
        /// <summary>A picto icon in the kit's look: the white glyph over eight navy copies a little offset, which read as its outline (the
        /// reference's bare gear and X). Returns the root; the white glyph is the child "Icon".</summary>
        static RectTransform Glyph(string name, Transform parent, string picto, Vector2 anchor, Vector2 pos, float size, float outline = 0.035f)
        {
            var rt = UI(name, parent, anchor, anchor, pos, new Vector2(size, size));
            var s = Picto(picto);
            if (outline > 0f)
                for (int k = 0; k < 8; k++)
                {
                    float a = k * Mathf.PI * 0.25f;
                    Icon("O" + k, rt, s, UiNavy, Mid, new Vector2(Mathf.Cos(a), Mathf.Sin(a) - 0.5f) * size * outline, size);
                }
            Icon("Icon", rt, s, Color.white, Mid, Vector2.zero, size);
            return rt;
        }
        /// <summary>UI type: Lilita One, white with the navy outline and a soft shadow. heavy = the standard outline; else the thin one (small print).</summary>
        static TextMeshProUGUI Type(string name, Transform parent, string text, float size, Color color, Vector2 anchor, Vector2 pos, Vector2 box, float tracking = 0f, bool heavy = true, TextAlignmentOptions align = TextAlignmentOptions.Center)
        {
            var rt = UI(name, parent, anchor, anchor, pos, box);
            var t = rt.gameObject.AddComponent<TextMeshProUGUI>();
            t.font = font; t.fontSharedMaterial = heavy ? fontUiPlain : fontUiLightPlain;
            t.text = text; t.fontSize = size; t.color = color; t.alignment = align; t.characterSpacing = tracking; t.raycastTarget = false;
            return t;
        }
        /// <summary>The big words: the thicker outline and a deeper shadow.</summary>
        static TextMeshProUGUI Title(string name, Transform parent, string text, float size, Color color, Vector2 anchor, Vector2 pos, Vector2 box, float tracking = 0f)
        {
            var t = Type(name, parent, text, size, color, anchor, pos, box, tracking, true);
            t.fontSharedMaterial = fontUiTitle;
            return t;
        }
        /// <summary>Dark type on a white panel: no outline (the kit's popup body text).</summary>
        static TextMeshProUGUI Ink(string name, Transform parent, string text, float size, Vector2 anchor, Vector2 pos, Vector2 box, TextAlignmentOptions align = TextAlignmentOptions.Center, Color? color = null)
        {
            var t = Type(name, parent, text, size, color ?? UiInkText, anchor, pos, box, 0f, true, align);
            t.fontSharedMaterial = fontUiInk;
            return t;
        }
        /// <summary>A rounded panel with the kit's navy outline and shadow (BorderFrame_Round02, white), tinted to any colour. Returns the root; "Face" is the image.</summary>
        static RectTransform Panel9(string name, Transform parent, Vector2 anchor, Vector2 pos, Vector2 size, Color tint, float ppuMul = 2f, string sprite = "Frame/BorderFrame_Round02.png", float stroke = -1f)
        {
            var rt = UI(name, parent, anchor, anchor, pos, size);
            if (stroke < 0f) stroke = UiStroke;
            if (stroke > 0f) Kit("Stroke", rt, sprite, UiNavy, Vector2.zero, Vector2.one, Vector2.zero, new Vector2(stroke * 2f, stroke * 2f), ppuMul);
            Kit("Face", rt, sprite, tint, Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero, ppuMul);
            return rt;
        }
        /// <summary>The kit's resource pill: the navy bar (free width, a fixed 64 px tall) with the number inside and an icon hanging off its
        /// right end, bigger than the bar, the way the reference hangs its coin. Returns the root; the number is tm.</summary>
        static RectTransform Pill(string name, Transform parent, Vector2 anchor, Vector2 pos, Vector2 size, Sprite icon, float iconSize, string text, float fontSize, out TextMeshProUGUI tm, Color? tint = null)
        {
            var rt = UI(name, parent, anchor, anchor, pos, size);
            Outlined("Bar", rt, "UI_Etc/ResourceBar_Bg.png", tint ?? new Color(0.40f, 0.70f, 0.96f), Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero, 64f / size.y);   // the kit's bar is white to be tinted (light blue since 2026-09-19, deep blue before), with the bold outline
            float left = -size.x * 0.5f + 6f, right = size.x * 0.5f - iconSize * 0.8f;   // between the left margin and the icon hanging off the right end
            tm = Type("Value", rt, text, fontSize, Color.white, Mid, new Vector2((left + right) * 0.5f, 1f), new Vector2(right - left, size.y));
            tm.enableAutoSizing = true; tm.fontSizeMin = 11f; tm.fontSizeMax = fontSize;   // a long bank shrinks to fit the compact pill (2026-09-19)
            if (icon != null) Icon("Icon", rt, icon, Color.white, new Vector2(1f, 0.5f), new Vector2(-iconSize * 0.3f, 1f), iconSize);
            return rt;
        }
        /// <summary>The kit's chunky button (Button01_145 / _175: the coloured face on its darker shelf, a fixed height that fills the rect, free
        /// width) with a white outlined label and an optional picto at the left. interactive = a real Button with the press squash and darkening
        /// (UIButtonFx); false = the same look as a "tap anywhere" prompt. colour: Green / Blue / Yellow / Orange / Sky / White / Gray / Red.</summary>
        static RectTransform Chunky(string name, Transform parent, Vector2 anchor, Vector2 pos, Vector2 size, string colour, string label, float fontSize, out Image faceIm, out TextMeshProUGUI labelTm, bool interactive = true, string picto = null, float iconSize = 0f, bool tall = false)
        {
            var rt = UI(name, parent, anchor, anchor, pos, size);
            string file = tall ? "Button/Button01_175_" + colour + ".png" : "Button/Button01_145_" + colour + ".Png";
            float ppu = (tall ? 175f : 145f) / size.y;
            Kit("Stroke", rt, file, UiNavy, Vector2.zero, Vector2.one, Vector2.zero, new Vector2(UiStroke * 2f, UiStroke * 2f), ppu);   // the bold outline
            faceIm = Kit("Face", rt, file, Color.white, Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero, ppu);
            float shift = 0f;
            if (picto != null) { Glyph("Icon", rt, picto, new Vector2(0f, 0.5f), new Vector2(18f + iconSize * 0.5f, size.y * 0.06f), iconSize, 0f); shift = iconSize * 0.5f + 8f; }
            labelTm = Type("Label", rt, label, fontSize, Color.white, Mid, new Vector2(shift, size.y * 0.07f), new Vector2(size.x - shift * 2f - 16f, size.y));   // a touch up: the shelf takes the bottom
            if (interactive)
            {
                faceIm.raycastTarget = true;
                var btn = rt.gameObject.AddComponent<Button>(); btn.transition = Selectable.Transition.None; btn.targetGraphic = faceIm;
                var fx = rt.gameObject.AddComponent<UIButtonFx>(); fx.tint = faceIm; fx.pressedColor = UiPressed;
            }
            return rt;
        }
        static Button ChunkyButton(string name, Transform parent, Vector2 anchor, Vector2 pos, Vector2 size, string colour, string label, float fontSize, string picto = null, float iconSize = 0f, bool tall = false)
        {
            var rt = Chunky(name, parent, anchor, pos, size, colour, label, fontSize, out _, out _, true, picto, iconSize, tall);
            return rt.GetComponent<Button>();
        }
        /// <summary>A bare outlined picto as a button (the reference's gear and X): press squash only.</summary>
        static Button GlyphButton(string name, Transform parent, string picto, Vector2 anchor, Vector2 pos, float size)
        {
            var rt = Glyph(name, parent, picto, anchor, pos, size);
            var hit = UIImage("Hit", rt, new Color(1f, 1f, 1f, 0f), Vector2.zero, Vector2.one, Vector2.zero, new Vector2(16f, 16f)); hit.raycastTarget = true;   // a little larger than the glyph: an easy thumb target
            var btn = rt.gameObject.AddComponent<Button>(); btn.transition = Selectable.Transition.None; btn.targetGraphic = hit;
            rt.gameObject.AddComponent<UIButtonFx>();
            return btn;
        }
        /// <summary>A round plate button (the kit's Button_Circle147, navy or white) with a picto on it. The picto is the child "Icon".</summary>
        static Button RoundButton(string name, Transform parent, Vector2 anchor, Vector2 pos, float size, string plate, string picto, float iconSize, Color iconColor)
        {
            var rt = UI(name, parent, anchor, anchor, pos, new Vector2(size, size));
            Icon("Stroke", rt, uiCircle, UiNavy, Mid, new Vector2(0f, -size * 0.02f), size + UiStroke * 2f);   // the bold outline
            var face = Kit("Face", rt, "Button/Button_Circle147_" + plate + ".png", Color.white, Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero, 1f, false); face.raycastTarget = true;
            Icon("Icon", rt, Picto(picto), iconColor, Mid, new Vector2(0f, size * 0.04f), iconSize);
            var btn = rt.gameObject.AddComponent<Button>(); btn.transition = Selectable.Transition.None; btn.targetGraphic = face;
            var fx = rt.gameObject.AddComponent<UIButtonFx>(); fx.tint = face; fx.pressedColor = UiPressed;
            return btn;
        }
        /// <summary>A thin rounded bar (the kit's tiny BasicTriple track, sliced): a dark track and a fill growing from the left (HUD sets the
        /// fill's width in units; hud.progressWidth = size.x - 6).</summary>
        static RectTransform Bar(string name, Transform parent, Vector2 anchor, Vector2 pos, Vector2 size, Color track, Color fill, out Image fillIm)
        {
            var rt = UI(name, parent, anchor, anchor, pos, size);
            Outlined("Track", rt, "Slider/Slider_BasicTriple_Bg.png", track, Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero, 6f / size.y, 2.5f);
            var inner = UI("Inner", rt, Vector2.zero, Vector2.one, Vector2.zero, new Vector2(-6f, -6f));
            fillIm = Kit("Fill", inner, "Slider/Slider_BasicTriple_Bg.png", fill, new Vector2(0f, 0f), new Vector2(0f, 1f), Vector2.zero, new Vector2(8f, 0f), 6f / (size.y - 6f));
            fillIm.rectTransform.pivot = new Vector2(0f, 0.5f);
            return rt;
        }
        /// <summary>A horizontal slider (background, fill area, handle slide area, like Unity's default) in the kit's look: a white rounded
        /// track with the navy outline, a yellow fill, the kit's arrowed handle.</summary>
        static Slider UISlider(string name, Transform parent, Vector2 pos, Vector2 size, float min, float max)
        {
            var rt = UI(name, parent, Mid, Mid, pos, size);
            float trackH = 22f;
            var track = UI("Track", rt, new Vector2(0f, 0.5f), new Vector2(1f, 0.5f), Vector2.zero, new Vector2(0f, trackH));
            Kit("Background", track, "Frame/BorderFrame_Round02.png", Color.white, Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero, 3f).raycastTarget = true;
            var fillArea = UI("Fill Area", track, Vector2.zero, Vector2.one, Vector2.zero, new Vector2(-14f, -8f));
            var fill = Kit("Fill", fillArea, "Slider/Slider_BasicTriple_Bg.png", UiYellow, Vector2.zero, Vector2.one, Vector2.zero, new Vector2(8f, 0f), 6f / (trackH - 8f));
            var handleArea = UI("Handle Slide Area", rt, Vector2.zero, Vector2.one, Vector2.zero, new Vector2(-24f, 0f));
            var handle = Kit("Handle", handleArea, "Slider/Slider_Handle_Icon.png", Color.white, new Vector2(0f, 0f), new Vector2(0f, 1f), Vector2.zero, new Vector2(26f, 0f), 1f, false); handle.raycastTarget = true;
            var s = rt.gameObject.AddComponent<Slider>();
            s.fillRect = fill.rectTransform; s.handleRect = handle.rectTransform; s.targetGraphic = handle; s.transition = Selectable.Transition.None;
            s.direction = Slider.Direction.LeftToRight; s.minValue = min; s.maxValue = max; s.wholeNumbers = true; s.value = max;
            return s;
        }
        /// <summary>The kit's ribbon (Title_Ribbon_Bg, free width, a fixed 141 px tall) with the words on it: the banners.</summary>
        static RectTransform Ribbon(string name, Transform parent, Vector2 anchor, Vector2 pos, Vector2 size, string colour)
        {
            var rt = UI(name, parent, anchor, anchor, pos, size);
            Kit("Face", rt, "Label/Title_Ribbon_Bg_" + colour + ".png", Color.white, Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero, 141f / size.y);
            return rt;
        }
        /// <summary>A popup: the kit's white rounded panel with its shadow, a coloured flag hanging over its top edge with the title on it.
        /// Content goes in the root at its size; the flag takes the top ~50 units.</summary>
        static RectTransform Popup(string name, Transform parent, Vector2 pos, Vector2 size, string flagColour, string title, float titleSize)
        {
            var rt = UI(name, parent, Mid, Mid, pos, size);
            Kit("Face", rt, "Popup/Popoup01~03_White_Bg.png", Color.white, Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero, 2f);
            var flag = Kit("Flag", rt, "Label/Title_Flag01_" + flagColour + ".png", Color.white, TC, TC, new Vector2(0f, 22f), new Vector2(310f, 87f), 1f, false);   // 820 x 231 drawn whole
            Title("Title", flag.transform, title, titleSize, Color.white, Mid, new Vector2(0f, 6f), new Vector2(300f, 60f));
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
            // a bright day (2026-09-19, "from sunset to bright day"): a high white sun from behind-right, short soft shadows. The war dusk
            // (2026-09-18) was (1, 0.72, 0.5) x 1.35 from 18 degrees.
            light.type = LightType.Directional; light.color = new Color(1f, 0.98f, 0.94f); light.intensity = 1.5f; light.shadows = LightShadows.Soft; light.shadowStrength = 0.45f;
            lightGo.transform.rotation = Quaternion.Euler(50f, -30f, 0f);
            // the sky: a real photographed sky (Poly Haven "Kloofendal 48d partly cloudy" pure-sky HDRI, CC0, Assets/_Game/Art/Sky)
            // on the panoramic skybox shader, lighting the scene through skybox ambient. Falls back to the old procedural
            // gradient if the file is missing. (requested 2026-09-16: "the background is ugly, I want a professional sky")
            var skyPath = Gen + "/Materials/Skybox.mat";
            var sky = AssetDatabase.LoadAssetAtPath<Material>(skyPath);
            Texture2D hdri = null;   // the bright day is the gradient sky (SkyGradient.shader, below); the HDRIs stay in Art/Sky unused (the Belfast sunset was the war dusk of 2026-09-18, the Kloofendal morning before it) - point ImportSkyHdri at one to get a photographed sky back
            if (hdri != null)
            {
                if (sky == null || sky.shader.name != "Skybox/Panoramic") { sky = new Material(Shader.Find("Skybox/Panoramic")); AssetDatabase.CreateAsset(sky, skyPath); }
                sky.SetTexture("_MainTex", hdri); sky.SetFloat("_Mapping", 1f); sky.SetFloat("_ImageType", 0f); sky.SetFloat("_Layout", 0f);   // lat-long, 360 degrees
                sky.SetFloat("_Exposure", 0.9f); sky.SetFloat("_Rotation", SkyRotation); sky.SetColor("_Tint", new Color(0.5f, 0.5f, 0.5f));
                EditorUtility.SetDirty(sky);
                RenderSettings.skybox = sky; RenderSettings.sun = light;
                RenderSettings.ambientMode = AmbientMode.Skybox; RenderSettings.ambientIntensity = 1.0f;
            }
            else
            {
                // the flat cartoon sky of the reference: a two-colour gradient, pale at the horizon and saturated overhead (the horizon colour
                // is also the fog and the sea's reflection), a small sun where the light comes from. Explicit three-colour ambient: nothing to bake.
                if (sky == null || sky.shader.name != "SkySquad/SkyGradient") { sky = new Material(Shader.Find("SkySquad/SkyGradient")); AssetDatabase.CreateAsset(sky, skyPath); }
                sky.SetColor("_TopColor", new Color(0.20f, 0.55f, 0.93f)); sky.SetColor("_HorizonColor", new Color(0.62f, 0.85f, 0.98f)); sky.SetColor("_GroundColor", new Color(0.45f, 0.70f, 0.90f));
                sky.SetFloat("_Curve", 1.1f); sky.SetColor("_SunColor", new Color(1f, 0.98f, 0.9f)); sky.SetFloat("_SunSize", 0.9975f); sky.SetFloat("_SunGlow", 0.5f);
                EditorUtility.SetDirty(sky);
                RenderSettings.skybox = sky; RenderSettings.sun = light; RenderSettings.ambientMode = AmbientMode.Trilight;
                RenderSettings.ambientSkyColor = new Color(0.55f, 0.75f, 0.95f); RenderSettings.ambientEquatorColor = new Color(0.60f, 0.75f, 0.85f); RenderSettings.ambientGroundColor = new Color(0.25f, 0.45f, 0.65f);
            }
            RenderSettings.fog = true; RenderSettings.fogMode = FogMode.Linear; RenderSettings.fogStartDistance = 175f; RenderSettings.fogEndDistance = 340f;   /* starts past spawnDistance: fighters are never seen half-fogged */ RenderSettings.fogColor = new Color(0.62f, 0.85f, 0.98f);   /* the gradient sky at the horizon: the far sea fades into it */

            // post: bloom makes tracers and explosions glow, a vignette frames the lane, a touch more colour
            string profilePath = Gen + "/Data/PostFX.asset";
            var profile = AssetDatabase.LoadAssetAtPath<VolumeProfile>(profilePath);
            if (profile == null) { profile = ScriptableObject.CreateInstance<VolumeProfile>(); AssetDatabase.CreateAsset(profile, profilePath); }
            T Fx<T>() where T : VolumeComponent
            {
                if (profile.TryGet(out T have)) return have;
                var c = profile.Add<T>(true); c.hideFlags = HideFlags.HideInHierarchy; AssetDatabase.AddObjectToAsset(c, profile); return c;
            }
            var bloom = Fx<Bloom>(); bloom.threshold.Override(1.2f); bloom.intensity.Override(0.35f); bloom.scatter.Override(0.6f);   // above the HDRI sky's brightness: tracers, flashes and explosions glow, the clouds do not turn milky
            var tone = Fx<Tonemapping>(); tone.mode.Override(TonemappingMode.Neutral);   // the photographed sky has real HDR highlights: roll them off instead of clipping to white
            var vignette = Fx<Vignette>(); vignette.intensity.Override(0f); vignette.smoothness.Override(0.5f);   /* none: the bright day is open like the reference (0.38 in the dusk) */
            var grade = Fx<ColorAdjustments>(); grade.saturation.Override(15f); grade.contrast.Override(5f); grade.postExposure.Override(0f); grade.colorFilter.Override(Color.white);   /* the bright day: vivid, no crunch, no tint (the dusk was -4 / 22 / warm) */
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

            // HUD (2026-09-19, fourth pass: GUI Pro - Casual Game, laid out like the reference: gear top-left, the attempt top-centre, the coin pill top-right)
            var canvasGo = new GameObject("HUD", typeof(Canvas), typeof(CanvasScaler), typeof(GraphicRaycaster));
            var canvas = canvasGo.GetComponent<Canvas>(); canvas.renderMode = RenderMode.ScreenSpaceOverlay;
            var scaler = canvasGo.GetComponent<CanvasScaler>(); scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize; scaler.referenceResolution = new Vector2(540f, 960f); scaler.matchWidthOrHeight = 0.5f;
            var hud = canvasGo.AddComponent<HUD>();
            hud.buyFace = Color.white; hud.buyShelf = Color.white; hud.buyText = Color.white;   // a price you can pay: the button in its colour, white type
            hud.cantFace = Color.white; hud.cantShelf = Color.white; hud.cantText = new Color(0.72f, 0.72f, 0.72f);   // one you cannot: the box stays bright like the reference, only the price greys
            hud.pipOff = new Color(0.80f, 0.83f, 0.87f);   // an unlit pip: pale grey, like the reference
            hud.hangar = null; if (hangar != null) hangar.SetActive(false);   // the lobby shows the real squad on the real level now (2026-09-19); the jet showcase rig stays built, off
            hud.soundOn = Picto("Sound"); hud.soundOff = Picto("Sound_Off");
            var coinSprite = Gp("UI_Etc/ResourceBar_Icon_Coin.png");
            var flash = UIImage("Flash", canvasGo.transform, new Color(1f, 1f, 1f, 0f), Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero); hud.flashImage = flash;
            var warn = UIImage("Warn", canvasGo.transform, new Color(1f, 0.23f, 0.31f, 0f), Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero); hud.warnImage = warn;

            var play = UI("PlayGroup", canvasGo.transform, Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero); hud.playGroup = play.gameObject;
            // top left: the gear (settings), the pause plate under it
            var settingsBtn = GlyphButton("SettingsBtn", play, "Gear", TL, new Vector2(38f, -38f), 46f);   // "a settings button at the top, not every time I die" (2026-09-18)
            UnityEditor.Events.UnityEventTools.AddPersistentListener(settingsBtn.onClick, hud.OnSettingsButton);
            var pauseBtn = RoundButton("PauseBtn", play, TL, new Vector2(38f, -96f), 44f, "White", "Control_Pause", 18f, UiNavy);
            UnityEditor.Events.UnityEventTools.AddPersistentListener(pauseBtn.onClick, hud.OnPauseButton);
            // top centre: the attempt (the reference's "Level 1"), the horde bar under it with the BOSS chip at its end
            hud.levelText = Type("LevelText", play, "ATTEMPT 1", 26f, Color.white, TC, new Vector2(0f, -36f), new Vector2(260f, 36f));
            var progressBar = Bar("Progress", play, TC, new Vector2(0f, -68f), new Vector2(190f, 16f), new Color(0.10f, 0.20f, 0.36f, 0.8f), UiSkyBlue, out var progressFill);
            hud.progressFill = progressFill.rectTransform; hud.progressImage = progressFill; hud.progressWidth = 184f;
            hud.progressText = Type("ProgressText", play, "HORDE 1", 10f, Color.white, TC, new Vector2(0f, -68f), new Vector2(190f, 16f), 0f, false);
            var bossChip = Panel9("BossBadge", play, TC, new Vector2(126f, -68f), new Vector2(56f, 24f), UiRed, 3f);
            Type("Skull", bossChip, "BOSS", 11f, Color.white, Mid, new Vector2(0f, 1f), new Vector2(56f, 24f), 0f, false);
            // top right: the bank (the coin hangs off the pill's end, the "+N" pops under it), the planes under it
            // the banks, smaller and lighter since 2026-09-19: coins on a light blue pill, diamonds on an aqua one (the plane-count pill went: the squad wears its count)
            Pill("Coins", play, TR, new Vector2(-61f, -42f), new Vector2(88f, 30f), coinSprite, 38f, "0", 19f, out hud.coinsText, new Color(0.20f, 0.47f, 0.88f));   // 88 x 30: the reference's compact pill - full height, no spare width (2026-09-19)   // the reference's deeper blue
            // the diamonds pill like the reference: a brighter blue bar with its right end slanted, the gem hanging off that end, a green "+" hanging off the left
            var gems = UI("Gems", play, TR, TR, new Vector2(-61f, -98f), new Vector2(88f, 30f));   // 56 under the coins: a clear gap
            var gStroke = UIImage("Stroke", gems, UiNavy, Vector2.zero, Vector2.one, Vector2.zero, new Vector2(UiStroke * 2f, UiStroke * 2f)); gStroke.sprite = uiPillSlantStroke; gStroke.type = Image.Type.Simple;
            var gFace = UIImage("Face", gems, new Color(0.33f, 0.66f, 0.96f), Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero); gFace.sprite = uiPillSlant; gFace.type = Image.Type.Simple;
            hud.gemsText = Type("Value", gems, "0", 19f, Color.white, Mid, new Vector2(-6f, 1f), new Vector2(48f, 30f));   // between the + and the gem
            hud.gemsText.enableAutoSizing = true; hud.gemsText.fontSizeMin = 11f; hud.gemsText.fontSizeMax = 19f;
            Icon("Icon", gems, Gp("UI_Etc/ResourceBar_Icon_Gem_Blue.png"), Color.white, new Vector2(1f, 0.5f), new Vector2(-8f, 1f), 36f);
            var plus = UI("Plus", gems, new Vector2(0f, 0.5f), new Vector2(0f, 0.5f), new Vector2(1f, 0f), new Vector2(22f, 22f));   // not wired: there is nothing to buy diamonds with yet
            Icon("Stroke", plus, uiCircle, UiNavy, Mid, Vector2.zero, 22f + UiStroke * 2f);
            Icon("Face", plus, uiCircle, UiGreen, Mid, Vector2.zero, 22f);
            Icon("Glyph", plus, Gp("UI_Etc/ResourceBar_Btn_Icon_Add.png"), Color.white, Mid, Vector2.zero, 13f);
            hud.planesText = null;
            var popRt = UI("CoinPop", play, TR, TR, new Vector2(-61f, -132f), new Vector2(88f, 24f));
            var popGroup = popRt.gameObject.AddComponent<CanvasGroup>(); popGroup.alpha = 0f; hud.coinPopGroup = popGroup;
            hud.coinPopText = Type("CoinPopText", popRt, "+0", 16f, UiYellow, Mid, Vector2.zero, new Vector2(88f, 24f));
            // bottom: the weapon at the left, the kills at the right - white pills with dark type
            var weapon = Panel9("Weapon", play, BL, new Vector2(96f, 34f), new Vector2(172f, 46f), Color.white, 2.2f);
            hud.weaponName = Type("WeaponName", weapon, "GATLING", 17f, UiYellow, Mid, new Vector2(0f, 9f), new Vector2(160f, 22f));
            hud.weaponDesc = Ink("WeaponDesc", weapon, "single target, fast", 10f, Mid, new Vector2(0f, -9f), new Vector2(160f, 16f));
            var kills = Panel9("Kills", play, BR, new Vector2(-62f, 34f), new Vector2(104f, 46f), Color.white, 2.2f);
            Icon("KillsIcon", kills, Gp("IconMisc/Icon_ImageIcon_Knife_Battle.png"), Color.white, new Vector2(0f, 0.5f), new Vector2(24f, 1f), 30f);
            hud.killsText = Ink("Kills", kills, "0", 20f, Mid, new Vector2(12f, 1f), new Vector2(60f, 30f));
            var hintRt = Panel9("Hint", play, BC, new Vector2(0f, 150f), new Vector2(300f, 52f), Color.white, 2.2f);
            var hintGroup = hintRt.gameObject.AddComponent<CanvasGroup>(); hud.hintGroup = hintGroup;
            hud.hintText = Ink("HintText", hintRt, "DRAG TO FLY\nDIVE for crates  ·  CLIMB to fight", 12f, Mid, new Vector2(0f, 1f), new Vector2(290f, 46f));
            hud.playOnly = new[] { pauseBtn.gameObject, progressBar.gameObject, hud.progressText.gameObject, bossChip.gameObject, weapon.gameObject, kills.gameObject };   // hidden in the lobby; the gear, the attempt and the pills stay

            // the banner: the kit's ribbon across the middle with the words on it
            var bannerRt = Ribbon("Banner", canvasGo.transform, Mid, new Vector2(0f, 190f), new Vector2(440f, 72f), "Orange");
            var bannerGroup = bannerRt.gameObject.AddComponent<CanvasGroup>(); bannerGroup.alpha = 0f; hud.bannerGroup = bannerGroup;
            hud.bannerText = Title("BannerText", bannerRt, "", 40f, Color.white, Mid, new Vector2(0f, 4f), new Vector2(400f, 60f));

            // the lobby (2026-09-19, like the reference): the level itself, armed and waiting, under the name, three upgrade cards low on the
            // screen and a hand rising over them ("swipe"); the first swipe starts the attempt and the deck drops away (HUD.titleOut)
            var title = Panel("TitlePanel", canvasGo.transform, 0.0f); hud.titlePanel = title; hud.titleGroup = title.AddComponent<CanvasGroup>();
            Title("T1", title.transform, "SKY <color=#FFD23F>SQUAD</color>", 56f, Color.white, TC, new Vector2(0f, -138f), new Vector2(520f, 70f));   // up under the top bar, in the sky band: the lobby camera pitches down and the crate queue rises to mid-screen
            var deck = UI("Deck", title.transform, BC, BC, new Vector2(0f, 170f), new Vector2(540f, 340f)); hud.deck = deck;   // its bottom edge on the screen's (UI() pivots at the centre)
            var handRt = Glyph("Hand", deck, "Tap", BC, new Vector2(0f, 300f), 52f); hud.hand = handRt; hud.handGroup = handRt.gameObject.AddComponent<CanvasGroup>();   // the kit's tapping hand
            string[] cardNames = { "FIRE RATE", "DAMAGE", "REVENUE" };
            Color[] cardCols = { UiGreen, UiSkyBlue, UiYellow };
            Sprite[] cardIcons = { Gp("Icon_ItemIcons/256/Icon_Energy_Yellow.png"), ArtSprite("Missile.png"), Gp("Icon_ItemIcons/256/Icon_Golds.png") };   // DAMAGE: the mortar rocket render the user gave (Art/UI, cut out of its checkerboard 2026-09-19)
            float[] cardIconSize = { 66f, 76f, 66f };   // the rocket lies on the diagonal of its square: a little bigger than the others to weigh the same (92 read too big)
            for (int i = 0; i < 3; i++)
            {   // an upgrade card like the reference: the card colour as a rounded outlined panel, the name in its lighter header band, a grey level
                // badge on the corner, the icon on a dark inset, five pips, the UPGRADE button with the coin price. Tap anywhere on the card to buy;
                // HUD.RefreshLobby fills in level, effect, pips and price and dims the button when the bank is short
                // sized for a phone (2026-09-19: "thinner, smaller, bold outlines, the badge inside its own card"): 140 x 226, 16 apart
                float cx = (i - 1) * 154f;   // thinner cards, 28 apart ("more space between each other", 2026-09-19)
                Color col = cardCols[i], dark = Color.Lerp(col, UiNavy, 0.42f), lit = Color.Lerp(col, Color.white, 0.25f);
                // the card is a chunky slab like the reference's (2026-09-19, "it has depth and shadows"): a soft shadow under it, the navy outline, a darker
                // shelf along its bottom, the face on top; low on the screen, in the deck that slides away
                var card = UI("Card" + i, deck, BC, BC, new Vector2(cx, 150f), new Vector2(126f, 232f));
                var cardShadow = UIImage("Shadow", card, new Color(0f, 0f, 0f, 0.35f), Vector2.zero, Vector2.one, new Vector2(0f, -10f), new Vector2(20f, 20f)); cardShadow.sprite = uiSoft; cardShadow.type = Image.Type.Sliced; cardShadow.pixelsPerUnitMultiplier = UiSoftFade / 20f;
                var body = Chunk("Body", card, Gp("Frame/BorderFrame_Round02.png"), col, dark, Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero, 3f, 6f, UiStroke);
                var cardFace = body.Find("Face").GetComponent<Image>(); cardFace.raycastTarget = true;
                var buy = card.gameObject.AddComponent<Button>(); buy.transition = Selectable.Transition.None; buy.targetGraphic = cardFace;
                UnityEditor.Events.UnityEventTools.AddIntPersistentListener(buy.onClick, hud.OnBuy, i);
                card.gameObject.AddComponent<UIButtonFx>();   // the whole card squashes on the press
                Kit("Head", card, "Frame/BasicFrame_Round20.png", lit, TC, TC, new Vector2(0f, -24f), new Vector2(112f, 32f), 4f);   // a lighter band under the name: the slab's lit top
                var nameTm = Title("CardName" + i, card, cardNames[i], 21f, Color.white, TC, new Vector2(0f, -24f), new Vector2(116f, 36f));   // big, filling the width like the reference, in the title face (thicker outline, deeper shadow); shrinks only if a name would not fit
                nameTm.enableAutoSizing = true; nameTm.fontSizeMin = 12f; nameTm.fontSizeMax = 21f;
                // the picture panel is sunk: the navy outline round a face that carries the card's own gradient (CardGradient: vertical / radial glow / diagonal)
                var inset = Outlined("Inset" + i, card, "Frame/BasicFrame_Round20.png", Color.Lerp(col, UiNavy, 0.6f), Mid, Mid, new Vector2(0f, 26f), new Vector2(112f, 100f), 4f, 2.5f);
                var grad = UIImage("Grad", inset, Color.white, Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero);
                grad.sprite = CardGradient(i, col); grad.type = Image.Type.Simple;
                Icon("CardIcon" + i, card, cardIcons[i], Color.white, Mid, new Vector2(0f, 26f), cardIconSize[i]);
                for (int j = 0; j < 5; j++)
                    hud.cardPips[i * 5 + j] = Chunk("Pip" + i + "_" + j, card, uiPill, UiGrey, new Color(0.10f, 0.15f, 0.25f, 0.6f), Mid, Mid, new Vector2(-44f + j * 22f, -36f), new Vector2(17f, 13f), 2f, 2.5f, 2f, 10f).Find("Face").GetComponent<Image>();   // the smooth small pill (corners 5 units), its outline concentric (radius 10 px); 17 wide at 22 apart: each pip keeps its own outline with a sliver of card between, like the reference
                hud.cardPipOn[i] = Color.Lerp(col, Color.white, 0.1f);   // a lit pip: the card's own colour, a touch brighter
                // the UPGRADE box: the kit's chunky button in the card's colour (its own shelf built in), outlined; dims when the bank is short
                var buyRt = Chunk("CardBuy" + i, card, Gp("Frame/BasicFrame_Round20.png"), col, dark, Mid, Mid, new Vector2(0f, -80f), new Vector2(112f, 58f), 4f, 5f, 2.5f, 16f);   // the UPGRADE box: the card's own colour on a darker shelf, outlined - the reference's slab (the kit's white button has a LIGHT shelf: tinted, it went flat)
                hud.cardBuyFace[i] = buyRt.Find("Face").GetComponent<Image>(); hud.cardBuyShelf[i] = null; hud.cardBuyTint[i] = col;   // the shelf keeps its dark colour; the face stays the card's (no dim: only the price greys)
                hud.cardBuyLabel[i] = Type("BuyLabel" + i, buyRt, "UPGRADE", 17f, Color.white, Mid, new Vector2(0f, 11f), new Vector2(108f, 24f));   // greys with the price when the bank is short
                Icon("BuyCoin" + i, buyRt, coinSprite, Color.white, Mid, new Vector2(-25f, -10f), 19f);
                hud.cardCost[i] = Type("CardCost" + i, buyRt, "0", 15f, Color.white, Mid, new Vector2(9f, -10f), new Vector2(72f, 20f));
                // the level badge: a navy-outlined grey disc on the card's top-right corner, overhanging it a little but never its neighbour
                var badge = UI("Badge" + i, card, TR, TR, new Vector2(-6f, 4f), new Vector2(38f, 38f));
                Icon("Stroke", badge, uiCircle, UiNavy, Mid, Vector2.zero, 38f + UiStroke * 2f);
                Kit("Face", badge, "Button/Button_Circle147_Gray.png", Color.white, Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero, 1f, false);
                hud.cardLevel[i] = Type("CardLevel" + i, badge, "0", 19f, Color.white, Mid, new Vector2(0f, 2f), new Vector2(38f, 38f));
            }

            // the overlays: a navy dim and the kit's white popup each, its title on the flag hanging over the top, the prompt as a chunky button
            var clear = Panel("ClearPanel", canvasGo.transform, new Color(0.05f, 0.12f, 0.25f, 0.6f)); hud.clearPanel = clear;
            var clearCard = Popup("ClearCard", clear.transform, new Vector2(0f, 20f), new Vector2(430f, 400f), "Blue", "MISSION", 30f);
            hud.clearTitle = Title("C1", clearCard, "BOSS", 62f, UiInkText, Mid, new Vector2(0f, 80f), new Vector2(420f, 80f));
            hud.clearSub = Title("C2", clearCard, "DOWN!", 62f, UiYellow, Mid, new Vector2(0f, 14f), new Vector2(420f, 80f));
            hud.clearStats = Ink("CStats", clearCard, "", 14f, Mid, new Vector2(0f, -62f), new Vector2(400f, 60f));
            Chunky("CTapBtn", clearCard, Mid, new Vector2(0f, -140f), new Vector2(260f, 60f), "Green", "TAP FOR NEXT", 22f, out _, out hud.clearTap, false);

            var over = Panel("OverPanel", canvasGo.transform, new Color(0.05f, 0.12f, 0.25f, 0.65f)); hud.overPanel = over;
            var overCard = Popup("OverCard", over.transform, new Vector2(0f, 5f), new Vector2(430f, 430f), "Red", "SQUADRON", 30f);
            Title("O2", overCard, "LOST", 66f, UiRed, Mid, new Vector2(0f, 84f), new Vector2(420f, 84f));
            var reasonBar = Panel9("OReasonBar", overCard, Mid, new Vector2(0f, 14f), new Vector2(360f, 44f), new Color(1f, 0.88f, 0.86f), 2.5f, "Frame/BasicFrame_Round20.png");
            hud.overReason = Ink("OReason", reasonBar, "", 14f, Mid, new Vector2(0f, 1f), new Vector2(340f, 40f), TextAlignmentOptions.Center, UiRed);
            hud.overStats = Ink("OStats", overCard, "", 14f, Mid, new Vector2(0f, -48f), new Vector2(400f, 44f));
            Chunky("OTapBtn", overCard, Mid, new Vector2(0f, -150f), new Vector2(260f, 60f), "Green", "TAP TO CONTINUE", 20f, out _, out _, false);

            var pause = Panel("PausePanel", canvasGo.transform, new Color(0.05f, 0.12f, 0.25f, 0.55f)); hud.pausePanel = pause;
            var pauseCard = Popup("PauseCard", pause.transform, new Vector2(0f, 35f), new Vector2(400f, 260f), "Blue", "PAUSED", 30f);
            Ink("P1", pauseCard, "the squadron is holding", 15f, Mid, new Vector2(0f, 10f), new Vector2(380f, 30f));
            Chunky("PTapBtn", pauseCard, Mid, new Vector2(0f, -62f), new Vector2(260f, 60f), "Green", "TAP TO RESUME", 22f, out _, out _, false, "Control_Play", 22f);

            // settings, like the reference: a full blue screen with the dot pattern, the title, the "plane speed" slider, the sound toggle, the big X to close
            var settings = Panel("SettingsPanel", canvasGo.transform, UiSkyBlue); hud.settingsPanel = settings; settings.GetComponent<Image>().raycastTarget = true;
            var dots = UIImage("Dots", settings.transform, new Color(1f, 1f, 1f, 0.07f), Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero);
            dots.sprite = uiCircle; dots.type = Image.Type.Tiled; dots.pixelsPerUnitMultiplier = 1.8f;
            Title("S1", settings.transform, "SETTINGS", 46f, Color.white, TC, new Vector2(0f, -80f), new Vector2(400f, 70f));
            Type("SLabel", settings.transform, "PLANE SPEED", 20f, Color.white, Mid, new Vector2(0f, 130f), new Vector2(400f, 30f));
            hud.dragSlider = UISlider("DragSlider", settings.transform, new Vector2(0f, 84f), new Vector2(340f, 40f), Settings.DragMin, Settings.DragMax);
            UnityEditor.Events.UnityEventTools.AddPersistentListener(hud.dragSlider.onValueChanged, new UnityEngine.Events.UnityAction<float>(hud.OnDragSlider));
            hud.dragValueText = Type("SValue", settings.transform, "20", 30f, Color.white, Mid, new Vector2(0f, 40f), new Vector2(200f, 40f));
            Type("SHint", settings.transform, "how far the squad flies for one thumb swipe", 12f, Color.white, Mid, new Vector2(0f, 8f), new Vector2(420f, 24f), 0f, false);
            Type("SSoundLabel", settings.transform, "SOUND", 20f, Color.white, Mid, new Vector2(0f, -60f), new Vector2(200f, 30f));
            var soundBtn = RoundButton("SoundBtn", settings.transform, Mid, new Vector2(0f, -112f), 64f, "Navy", "Sound", 32f, Color.white);
            hud.soundIcon = soundBtn.transform.Find("Icon").GetComponent<Image>();
            UnityEditor.Events.UnityEventTools.AddPersistentListener(soundBtn.onClick, hud.ToggleSound);
            var doneBtn = GlyphButton("DoneBtn", settings.transform, "Close", BC, new Vector2(0f, 96f), 64f);
            UnityEditor.Events.UnityEventTools.AddPersistentListener(doneBtn.onClick, hud.OnSettingsDone);
            settings.SetActive(false);

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
