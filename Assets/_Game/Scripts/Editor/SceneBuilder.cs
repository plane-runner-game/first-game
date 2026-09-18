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

        class Mats { public Material planeBody, planeBody2, planeAccent, glass, leader, attackerBody, attackerAccent, jetBody, jetAccent, jetGlow, enemyBody, enemyAccent, enemyGlass, bomberBody, bomberAccent, boss2Body, boss2Accent, boss3Body, boss3Accent, boss4Body, boss4Accent, bossGlass, zepBody, zepAccent, zepPlate, crate, crateBand, hull, outline, bomberGlow, bullet, water, cloud, buoy, buoyPole, tracer, particle, smoke, shieldBubble, barBg, barHp, barTimer, flash, prop, rocketBody, rocketFin, coin, stopLine, threatMarker, enemyCowl, propDisc, bossFlash, gateFrame, gatePanel; }
        class Meshes { public Mesh fighter, attacker, jet, prop, enemy, boss, boss2, boss3, boss4, zeppelin, crate, boat, boatWeapon, rocket, buoy, bullet, coin, gateFrame, gatePanel, sea; }
        class Prefabs { public GameObject planeFighter, planeAttacker, planeJet, enemyFighter, miniBoss, miniBoss2, miniBoss3, miniBoss4, breakable, gate, bullet, boss, explosion, sparks, floatText, ring, rocket, coin; }
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
                Gen + "/Meshes/Blimp.asset", Gen + "/Meshes/Drone.asset",
                Gen + "/Materials/CargoBody.mat", Gen + "/Materials/CargoAccent.mat",
                Gen + "/Materials/DroneBody.mat", Gen + "/Materials/DroneAccent.mat", Gen + "/Materials/DroneEye.mat", Gen + "/Materials/DiveLine.mat",
                Gen + "/Textures/WaterTiles.png" /* the flat sea's grey tiles (until 2026-09-18) */ })
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
            M.enemyBody = Lit("EnemyBody", new Color(0.88f, 0.16f, 0.16f), 0.4f);     // crimson: reads against the sky, distinct from the orange boss
            M.enemyAccent = Lit("EnemyAccent", new Color(0.98f, 0.94f, 0.82f));      // cream bands: bright dots head-on
            M.enemyGlass = Lit("EnemyGlass", new Color(0.35f, 0.6f, 0.8f), 0.9f);    // sky-blue tinted canopy
            M.enemyCowl = Lit("EnemyCowl", new Color(0.16f, 0.15f, 0.17f), 0.5f);    // dark engine cowl and guns
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
                m.SetColor("_ShallowColor", new Color(0.09f, 0.60f, 0.82f)); m.SetColor("_DeepColor", new Color(0.02f, 0.22f, 0.52f)); m.SetColor("_SSSColor", new Color(0.20f, 0.85f, 0.75f));
                m.SetColor("_SkyHorizon", new Color(0.80f, 0.87f, 0.95f)); m.SetColor("_SkyZenith", new Color(0.34f, 0.58f, 0.92f)); m.SetColor("_FoamColor", new Color(0.95f, 0.98f, 1f));
                m.SetTexture("_BaseMap", SeaNormalTexture()); m.SetTextureScale("_BaseMap", Vector2.one); m.SetTextureOffset("_BaseMap", Vector2.zero);
                m.SetTexture("_FoamMap", SeaFoamTexture()); m.SetTextureScale("_FoamMap", new Vector2(0.07f, 0.07f));   // tiles per unit: one foam tile every ~14 units
                m.SetFloat("_Tiling", 0.12f); m.SetFloat("_NormalStrength", 0.3f);
                m.SetVector("_WaveA", new Vector4(0.15f, -1f, 0.10f, 16f)); m.SetVector("_WaveB", new Vector4(0.6f, -0.8f, 0.09f, 9f));   // (dir x, dir z, steepness, length): a long swell toward the player and three shorter crossing waves; amplitude = steepness x length / 2pi, ~0.4 at the highest crest
                m.SetVector("_WaveC", new Vector4(-0.7f, -0.7f, 0.07f, 5.5f)); m.SetVector("_WaveD", new Vector4(0.3f, -0.95f, 0.05f, 3.5f));
                m.SetFloat("_WaveSpeed", 1f); m.SetFloat("_Reflect", 0.35f); m.SetFloat("_Fresnel", 5f);   /* 0.6 / 4 washed the far sea white */
                m.SetFloat("_SpecPower", 260f); m.SetFloat("_SpecIntensity", 1.2f); m.SetFloat("_Foam", 0.5f); m.SetFloat("_FoamStart", 0.62f);   /* 0.9 / 0.45: foam everywhere */
            });
            M.cloud = Transparent("Cloud", new Color(1f, 1f, 1f, 0.72f)); M.cloud.SetTexture("_BaseMap", CloudTexture());   // softer now that the real sky has its own clouds: these are the near, moving ones
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
            M.flash = Transparent("MuzzleFlash", new Color(1f, 0.9f, 0.4f, 0.9f), true); M.flash.SetTexture("_BaseMap", soft);   // soft additive glow, not a hard square
            M.bossFlash = Transparent("BossFlash", new Color(1f, 0.45f, 0.3f, 0.9f), true); M.bossFlash.SetTexture("_BaseMap", soft);
            M.gateFrame = Unlit("GateFrame", new Color(0.55f, 1f, 0.75f));                       // bright mint frame: the gate reads as a reward, not a threat
            M.gatePanel = Transparent("GatePanel", new Color(0.55f, 1f, 0.75f, 0.2f), true);      // UpgradeGate tints and pulses it per gate
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
        const float SkyRotation = 120f;   // turns the HDRI so the blue, sun-lit cumulus side fills the view ahead (330 and 200 put the grey overcast mass overhead)

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
            en.hpLabel = boss ? Label3D("HpLabel", root.transform, new Vector3(0f, 2.8f, 0f), 10f, Color.white, fontOutline)
                              : Label3D("HpLabel", root.transform, new Vector3(0f, 1.25f, 0f), 6f, Color.white, fontOutline);
            return SavePrefab(root, name);
        }

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
            en.hpLabel = Label3D("HpLabel", root.transform, new Vector3(0f, 2.8f, 0f), 10f, Color.white, fontOutline);
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
                Vector3.zero, 1.6f, 2f, Vector3.forward, new[] { "BlueFire", "Chassis_Back_L", "Chassis_Back_R", "Chassis_Front" }, M,
                () => PlanePrefab("PlaneJet", X.jet, X.prop, M, M.jetBody, M.jetAccent, M.jetGlow, false));
            P.enemyFighter = EnemyPrefab("EnemyFighter", X.enemy, X.prop, M, false, null, M.enemyBody, M.enemyAccent, M.enemyGlass, M.enemyCowl);
            // the four boss looks: bosses 1-2 the gunship, 3-4 the twin-boom, 5-6 the flying wing, 7 the airship (requested: "every two bosses the same shape, the last one different")
            P.miniBoss = BossPrefab("EnemyMiniBoss", X.boss, X.prop, M, new[] { new Vector3(-0.9f, -0.1f, 0.82f), new Vector3(-0.48f, -0.1f, 0.82f), new Vector3(0.48f, -0.1f, 0.82f), new Vector3(0.9f, -0.1f, 0.82f) }, 0.85f, new Vector3(0f, -0.34f, 1.5f), M.bomberBody, M.bomberAccent, M.bossGlass, M.enemyCowl, M.bomberGlow);   // the gunship: slate body, orange bands, glass nose, dark guns, red-hot tips
            P.miniBoss2 = BossPrefab("EnemyMiniBoss2", X.boss2, X.prop, M, new[] { new Vector3(-0.75f, -0.02f, 1.08f), new Vector3(0.75f, -0.02f, 1.08f) }, 1.05f, new Vector3(0f, -0.3f, 1.45f), M.boss2Body, M.boss2Accent, M.bossGlass, M.enemyCowl, M.bomberGlow);   // the twin-boom: olive, yellow bands, two big props
            P.miniBoss3 = BossPrefab("EnemyMiniBoss3", X.boss3, X.prop, M, new[] { new Vector3(-1.45f, 0.14f, 0.32f), new Vector3(-0.95f, 0.14f, 0.46f), new Vector3(-0.5f, 0.14f, 0.59f), new Vector3(0.5f, 0.14f, 0.59f), new Vector3(0.95f, 0.14f, 0.46f), new Vector3(1.45f, 0.14f, 0.32f) }, 0.7f, new Vector3(0f, -0.3f, 1.52f), M.boss3Body, M.boss3Accent, M.bossGlass, M.enemyCowl, M.bomberGlow);   // the flying wing: crimson, cream bands, six props along the sweep
            P.miniBoss4 = BossPrefab("EnemyMiniBoss4", X.boss4, X.prop, M, new[] { new Vector3(-0.8f, -0.62f, -0.62f), new Vector3(0.8f, -0.62f, -0.62f) }, 0.8f, new Vector3(0f, -0.95f, 1.2f), M.boss4Body, M.boss4Accent, M.bossGlass, M.enemyCowl, M.bomberGlow);   // the airship: purple, gold belts, pusher props behind the pods

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
            D.fighter = Asset<EnemyKindDef>("Enemy_Fighter", e => { e.id = "fighter"; e.displayName = "FIGHTER"; e.hp = 1f;   /* one hit at upgrade level 0 (2 was tried and dropped the same day: "I didn't like two hits", 2026-09-16) */ e.halfWidth = 1.0f; e.approachSpeed = 2f;   /* -4 -> 2: net 11 u/s, was 5 ("the planes are far too slow, speed them up", 2026-09-16) */ e.fireEvery = 3f; e.shotDamage = 1f; e.coins = 20;   /* "I want the coins to go up 20, not 10" (2026-09-16; was 10 earlier the same day) */ e.scale = 0.72f;   /* wingspan matches a squad plane; enemyHeightScale stretches it vertically */ e.miniBoss = false; e.prefab = P.enemyFighter; e.color = Red; });
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
                c.bossHp = new[] { 555f, 3945f, 15960f, 27500f, 60500f, 76500f, 125200f }; c.bossHpGrowthAfter = 1.6f;   // the seven bosses the user gave (2026-09-16); past them x1.6 each
                c.bossFirstAt = 20f; c.bossEvery = 23f; c.bossesPerLook = 2; c.lastBoss = 7;   /* "boss 7 is the last thing, nothing after him, I have won" (2026-09-16) */   // boss 1 starts moving 20 s in ("20 s until he starts moving, not until he reaches me"), then one every 23 s ("between 22 and 24"); two bosses per look, the 7th alone with the last look
                c.upgradeCostFire = 20f; c.upgradeCostDamage = 20f; c.upgradeCostRevenue = 20f; c.upgradeCostGrowth = 2.4f;   /* 20, 48, 115, 276, 663, 1592, 3822, 9172 up to level 8 ("still too easy" at x2 from 15: 7665) */ c.upgradeLinearFromLevel = 8; c.upgradeLinearStep = 5000f;   /* from level 8 on a flat +5000 per level: 14172, 19172, 24172 ... instead of 22013, 52831 ... ("at level 8 the cost goes up by 5 thousand", 2026-09-16) */ c.fireRatePerLevel = 0.4f; c.damagePerLevel = 1.0f;   /* "upgrades must strengthen the plane noticeably" (2026-09-16): level 6 now equals the old level 17-18 */ c.revenuePerLevel = 0.1f;   /* 10 coins x 1.10 per revenue level */
                c.supplyAlt = 0.65f + SeaLevel; /* the crates ride boats on the sea (2026-09-18): the hull sits in the water at this altitude - 0.65 above the waterline, which is SeaLevel since the same evening (was 1.5 under parachutes, 2.2 for an hour) */ c.supplyFrontZ = 17f; c.supplySpacing = 6.5f; c.supplyVisible = 10;   /* a long full line of crates, not 3 that trickle in */ c.boxHpPerLevel = 1.15f; c.coinsPerHp = 0f;   /* boxes pay no coins (was 0.3: "no coins when I destroy the box", 2026-09-16); coins come from shot-down planes only */
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
            var im = UIImage(name, parent, new Color(0.02f, 0.1f, 0.2f, alpha), Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero);
            im.raycastTarget = false;
            return im.gameObject;
        }

        /// <summary>A "SETTINGS" pill that opens HUD.settingsPanel (next to the pause button during play).</summary>
        static void SettingsButton(string name, Transform parent, Vector2 anchor, Vector2 pos, HUD hud)
        {
            var im = UIImage(name, parent, new Color(0.04f, 0.14f, 0.31f, 0.75f), anchor, anchor, pos, new Vector2(100f, 40f));
            im.raycastTarget = true;
            var btn = im.gameObject.AddComponent<Button>();
            UnityEditor.Events.UnityEventTools.AddPersistentListener(btn.onClick, hud.OnSettingsButton);
            UIText(name + "Text", im.transform, "SETTINGS", 14f, Color.white, new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(100f, 40f));
        }
        /// <summary>A horizontal slider built like Unity's default (background, fill area, handle slide area).</summary>
        static Slider UISlider(string name, Transform parent, Vector2 pos, Vector2 size, float min, float max)
        {
            var rt = UI(name, parent, new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f), pos, size);
            var bg = UIImage("Background", rt, new Color(0.02f, 0.08f, 0.18f, 0.9f), Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero); bg.raycastTarget = true;
            var fillArea = UI("Fill Area", rt, Vector2.zero, Vector2.one, Vector2.zero, new Vector2(-24f, -12f));
            var fill = UIImage("Fill", fillArea, Gold, Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero);
            var handleArea = UI("Handle Slide Area", rt, Vector2.zero, Vector2.one, Vector2.zero, new Vector2(-24f, 0f));
            var handle = UIImage("Handle", handleArea, Color.white, new Vector2(0f, 0f), new Vector2(0f, 1f), Vector2.zero, new Vector2(24f, 0f)); handle.raycastTarget = true;
            var s = rt.gameObject.AddComponent<Slider>();
            s.fillRect = fill.rectTransform; s.handleRect = handle.rectTransform; s.targetGraphic = handle;
            s.direction = Slider.Direction.LeftToRight; s.minValue = min; s.maxValue = max; s.wholeNumbers = true; s.value = max;
            return s;
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
            light.type = LightType.Directional; light.color = new Color(1f, 0.96f, 0.88f); light.intensity = 1.5f; light.shadows = LightShadows.Soft; light.shadowStrength = 0.55f;
            lightGo.transform.rotation = Quaternion.Euler(52f, -28f, 0f);
            // the sky: a real photographed sky (Poly Haven "Kloofendal 48d partly cloudy" pure-sky HDRI, CC0, Assets/_Game/Art/Sky)
            // on the panoramic skybox shader, lighting the scene through skybox ambient. Falls back to the old procedural
            // gradient if the file is missing. (requested 2026-09-16: "the background is ugly, I want a professional sky")
            var skyPath = Gen + "/Materials/Skybox.mat";
            var sky = AssetDatabase.LoadAssetAtPath<Material>(skyPath);
            var hdri = ImportSkyHdri(Root + "/Art/Sky/kloofendal_48d_partly_cloudy_puresky_4k.hdr");
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
            RenderSettings.fog = true; RenderSettings.fogMode = FogMode.Linear; RenderSettings.fogStartDistance = 175f; RenderSettings.fogEndDistance = 340f;   /* starts past spawnDistance: fighters are never seen half-fogged */ RenderSettings.fogColor = new Color(0.8f, 0.87f, 0.95f);   /* the HDRI horizon: pale haze, so the far sea melts into the sky */

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
            var vignette = Fx<Vignette>(); vignette.intensity.Override(0.28f); vignette.smoothness.Override(0.45f);
            var grade = Fx<ColorAdjustments>(); grade.saturation.Override(12f); grade.contrast.Override(10f); grade.postExposure.Override(0.1f);
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
            far.name = "WaterFar"; far.transform.SetParent(worldGo.transform, false); far.transform.position = new Vector3(0f, SeaLevel - 0.5f, 120f); far.transform.localScale = new Vector3(120f, 1f, 120f);
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

            var enemiesGo = new GameObject("Enemies"); var enemies = enemiesGo.AddComponent<WaveSpawner>(); enemies.fighterPrefab = P.enemyFighter; enemies.bossPrefabs = new[] { P.miniBoss, P.miniBoss2, P.miniBoss3, P.miniBoss4 };
            var supplyGo = new GameObject("Supply"); var supply = supplyGo.AddComponent<SupplyLane>(); supply.breakablePrefab = P.breakable; supply.gatePrefab = P.gate;
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
            SettingsButton("SettingsBtn", play, new Vector2(0f, 1f), new Vector2(122f, -78f), hud);   // next to the pause button, during play ("a settings button at the top, not every time I die", 2026-09-18)
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
            hud.clearTitle = clear.transform.Find("C1").GetComponent<TextMeshProUGUI>();
            hud.clearSub = clear.transform.Find("C2").GetComponent<TextMeshProUGUI>();
            hud.clearStats = UIText("CStats", clear.transform, "", 18f, new Color(0.81f, 0.9f, 1f), new Vector2(0.5f, 0.5f), new Vector2(0f, -30f), new Vector2(500f, 70f), TextAlignmentOptions.Center, true);
            hud.clearTap = UIText("CTap", clear.transform, "TAP FOR NEXT", 30f, Gold, new Vector2(0.5f, 0.5f), new Vector2(0f, -150f), new Vector2(400f, 50f));

            var over = Panel("OverPanel", canvasGo.transform, 0.78f); hud.overPanel = over;
            UIText("O1", over.transform, "SQUADRON", 80f, Color.white, new Vector2(0.5f, 0.5f), new Vector2(0f, 180f), new Vector2(520f, 100f));
            UIText("O2", over.transform, "LOST", 90f, Red, new Vector2(0.5f, 0.5f), new Vector2(0f, 90f), new Vector2(500f, 100f));
            hud.overReason = UIText("OReason", over.transform, "", 16f, Color.white, new Vector2(0.5f, 0.5f), new Vector2(0f, -10f), new Vector2(500f, 60f), TextAlignmentOptions.Center, true);
            hud.overStats = UIText("OStats", over.transform, "", 16f, new Color(0.81f, 0.9f, 1f), new Vector2(0.5f, 0.5f), new Vector2(0f, -60f), new Vector2(500f, 30f), TextAlignmentOptions.Center, true);
            UIText("OTap", over.transform, "TAP TO CONTINUE", 30f, Gold, new Vector2(0.5f, 0.5f), new Vector2(0f, -170f), new Vector2(400f, 50f));

            var pause = Panel("PausePanel", canvasGo.transform, 0.6f); hud.pausePanel = pause;
            UIText("P1", pause.transform, "PAUSED", 80f, Color.white, new Vector2(0.5f, 0.5f), new Vector2(0f, 110f), new Vector2(500f, 100f));
            UIText("PTap", pause.transform, "TAP TO RESUME", 30f, Gold, new Vector2(0.5f, 0.5f), new Vector2(0f, -40f), new Vector2(400f, 50f));

            // settings: a full-screen panel with the "plane speed" slider (2026-09-18: "a settings button, and in it control of the plane's movement speed")
            var settings = Panel("SettingsPanel", canvasGo.transform, 0.85f); hud.settingsPanel = settings; settings.GetComponent<Image>().raycastTarget = true;
            UIText("S1", settings.transform, "SETTINGS", 60f, Color.white, new Vector2(0.5f, 0.5f), new Vector2(0f, 170f), new Vector2(500f, 80f));
            UIText("SLabel", settings.transform, "PLANE SPEED", 22f, new Color(0.81f, 0.9f, 1f), new Vector2(0.5f, 0.5f), new Vector2(0f, 62f), new Vector2(400f, 34f));
            hud.dragSlider = UISlider("DragSlider", settings.transform, new Vector2(0f, 12f), new Vector2(360f, 40f), Settings.DragMin, Settings.DragMax);
            UnityEditor.Events.UnityEventTools.AddPersistentListener(hud.dragSlider.onValueChanged, new UnityEngine.Events.UnityAction<float>(hud.OnDragSlider));
            hud.dragValueText = UIText("SValue", settings.transform, "20", 26f, Gold, new Vector2(0.5f, 0.5f), new Vector2(0f, -34f), new Vector2(200f, 40f));
            UIText("SHint", settings.transform, "how far the squad flies for one thumb swipe", 12f, new Color(0.81f, 0.9f, 1f), new Vector2(0.5f, 0.5f), new Vector2(0f, -66f), new Vector2(420f, 24f), TextAlignmentOptions.Center, true);
            var doneIm = UIImage("DoneBtn", settings.transform, Gold, new Vector2(0.5f, 0.5f), new Vector2(0.5f, 0.5f), new Vector2(0f, -150f), new Vector2(240f, 60f));
            doneIm.raycastTarget = true;
            var doneBtn = doneIm.gameObject.AddComponent<Button>();
            UnityEditor.Events.UnityEventTools.AddPersistentListener(doneBtn.onClick, hud.OnSettingsDone);
            UIText("DoneText", doneIm.transform, "DONE", 28f, Navy, new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(240f, 60f));
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
