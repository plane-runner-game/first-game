// SceneBuilder.AlienBosses.cs (Editor only)
// The alien forest's cast (2026-10-02): fighters, crates, thirty bosses in six stages of five, and sixty attacks of plasma, crystal, spore and
// starlight. Eighteen bosses are ships (Star Sparrow hulls) repainted in bioluminescent liveries - cyan, violet, lime, magenta, pearl, teal and
// gold - with glowing crystals, wing shards and the pack's antenna fitted on; twelve are creatures and monuments of the forest itself, taken from
// the pack: the spore cap, the crystal hydra, the signal spire, the stone gate, the monolith, the elder tree, the pyramid warden, and the planet
// that is the last boss.
using System;
using System.Collections.Generic;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;

namespace SkySquad.EditorTools
{
    public static partial class SceneBuilder
    {
        static readonly string[] AlienBossNames = {
            "GLOW MOTH", "SPORE DART", "SPORE CAP", "NEBULA RAY", "CRYSTAL HYDRA",
            "PRISM WASP", "VOID PETAL", "SIGNAL SPIRE", "LUMEN FANG", "STONE GATE",
            "DRIFT PHANTOM", "SIGMA STINGER", "MONOLITH", "IONIC BEETLE", "ELDER TREE",
            "AURORA SERAPH", "COMET HAWK", "PYRAMID WARDEN", "ASTRO MANTIS", "PRISM SHARD",
            "PLASMA WRAITH", "GRAVITY LANCE", "FROST PYRAMID", "SHARD SCARAB", "TWIN CAPS",
            "STAR KESTREL", "ZENITH SPHINX", "PINE WRAITH", "COSMIC PHOENIX", "WORLD EATER" };
        static readonly string[] AlienStageNames = { "LANDING ZONE", "SPORE MARSH", "CRYSTAL FIELDS", "GLOW CANYON", "DEEP FOREST", "ALIEN HEART" };

        static LavaBossDef[] AlienBossDefs()
        {
            var d = new LavaBossDef[BossCount];
            // model: "S26" Star Sparrow, or "alien:SP_..." a piece of the pack; palette; parts; width; maxHeight; spin
            d[0] = new LavaBossDef("S26", 0, "crystals", 3.0f);
            d[1] = new LavaBossDef("S9", 2, "spikes", 3.0f);
            d[2] = new LavaBossDef("alien:SP_Tree03", 0, "", 3.0f, 2.6f);
            d[3] = new LavaBossDef("S22", 1, "antenna", 3.0f);
            d[4] = new LavaBossDef("alien:SP_Crystal02", 0, "", 3.0f, 3.0f);
            d[5] = new LavaBossDef("S13", 3, "crystals+spikes", 3.0f);
            d[6] = new LavaBossDef("S8", 1, "crystals", 3.0f);
            d[7] = new LavaBossDef("alien:SP_Sci-fi_Antenna", 0, "", 2.0f, 3.6f);
            d[8] = new LavaBossDef("S38", 0, "spikes", 3.0f);
            d[9] = new LavaBossDef("alien:SP_Rock08", 0, "", 3.2f, 3.0f);
            d[10] = new LavaBossDef("S10", 4, "antenna+crystals", 3.1f);
            d[11] = new LavaBossDef("S21", 2, "spikes", 3.0f);
            d[12] = new LavaBossDef("alien:SP_Rock07", 0, "", 2.2f, 3.6f);
            d[13] = new LavaBossDef("S24", 1, "crystals+spikes", 3.0f);
            d[14] = new LavaBossDef("alien:SP_Tree01", 0, "", 3.4f, 3.3f);
            d[15] = new LavaBossDef("S6", 5, "crystals", 3.2f);
            d[16] = new LavaBossDef("S35", 0, "antenna", 3.0f);
            d[17] = new LavaBossDef("alien:SP_Mountain02", 0, "", 3.2f, 3.0f);
            d[18] = new LavaBossDef("S17", 3, "spikes+antenna", 3.0f);
            d[19] = new LavaBossDef("alien:SP_Crystal01", 0, "", 2.6f, 3.2f);
            d[20] = new LavaBossDef("S7", 1, "crystals", 3.0f);
            d[21] = new LavaBossDef("S18", 4, "spikes", 3.0f);
            d[22] = new LavaBossDef("alien:SP_Mountain01", 0, "", 3.2f, 3.2f);
            d[23] = new LavaBossDef("S39", 5, "crystals+antenna", 3.0f);
            d[24] = new LavaBossDef("alien:SP_Tree02", 0, "", 3.4f, 3.0f);
            d[25] = new LavaBossDef("S30", 0, "spikes+crystals", 3.2f);
            d[26] = new LavaBossDef("S14", 2, "antenna", 3.1f);
            d[27] = new LavaBossDef("alien:SP_Tree04", 0, "", 2.2f, 3.6f);
            d[28] = new LavaBossDef("S19", 3, "crystals+spikes", 3.8f);
            d[29] = new LavaBossDef("alien:SP_Planet", 0, "", 3.4f, 3.4f, true);
            return d;
        }

        // livery: paint zones 1-3, glow colours 1-3
        static readonly Color[][] AlienPalettes = {
            new[] { new Color(0.05f, 0.45f, 0.55f), new Color(0.06f, 0.08f, 0.16f), new Color(0.40f, 1f, 1f), new Color(0f, 0.30f, 0.45f), new Color(0.10f, 0.90f, 1f), new Color(0.7f, 1f, 1f) },       // 0 cyan
            new[] { new Color(0.30f, 0.12f, 0.55f), new Color(0.07f, 0.06f, 0.15f), new Color(0.85f, 0.50f, 1f), new Color(0.20f, 0f, 0.40f), new Color(0.60f, 0.25f, 1f), new Color(0.95f, 0.8f, 1f) },  // 1 violet
            new[] { new Color(0.25f, 0.55f, 0.12f), new Color(0.06f, 0.10f, 0.07f), new Color(0.80f, 1f, 0.30f), new Color(0f, 0.30f, 0.05f), new Color(0.40f, 1f, 0.20f), new Color(0.9f, 1f, 0.6f) },    // 2 lime
            new[] { new Color(0.60f, 0.10f, 0.40f), new Color(0.10f, 0.05f, 0.12f), new Color(1f, 0.50f, 0.85f), new Color(0.40f, 0f, 0.20f), new Color(1f, 0.20f, 0.60f), new Color(1f, 0.8f, 0.95f) },    // 3 magenta
            new[] { new Color(0.75f, 0.85f, 0.90f), new Color(0.15f, 0.20f, 0.28f), new Color(0.40f, 0.90f, 1f), new Color(0f, 0.30f, 0.45f), new Color(0.10f, 0.90f, 1f), new Color(0.8f, 1f, 1f) },     // 4 pearl
            new[] { new Color(0.08f, 0.40f, 0.35f), new Color(0.10f, 0.10f, 0.08f), new Color(1f, 0.80f, 0.30f), new Color(0f, 0.30f, 0.20f), new Color(0.30f, 1f, 0.70f), new Color(1f, 0.95f, 0.6f) },    // 5 teal and gold
        };

        static Material AlienShipMaterial(int palette)
        {
            var src = AssetDatabase.LoadAssetAtPath<Material>("Assets/StarSparrow/Materials/StarSparrow_Black.mat");
            if (src == null) return null;
            string path = Gen + "/Materials/AlienShip" + palette + ".mat";
            var m = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (m == null) { m = new Material(src); AssetDatabase.CreateAsset(m, path); }
            m.shader = src.shader; m.CopyPropertiesFromMaterial(src);
            var p = AlienPalettes[palette % AlienPalettes.Length];
            m.SetColor("_Color1", p[0]); m.SetColor("_Color2", p[1]); m.SetColor("_Color3", p[2]);
            m.SetColor("_Emission1", p[3]); m.SetColor("_Emission2", p[4]); m.SetColor("_Emission3", p[5]);
            m.SetColor("_Cockpit1", p[3]); m.SetColor("_Cockpit2", p[4]); m.SetColor("_Cockpit3", p[5]);
            m.SetFloat("_EmissionMultiplier", 2.2f); m.SetFloat("_CockpitMultiplier", 1.6f); m.SetFloat("_Dirty", 0.2f); m.SetFloat("_Darken", 0f);
            EditorUtility.SetDirty(m);
            return m;
        }

        static void DecorateAlienShip(GameObject model, string parts)
        {
            if (string.IsNullOrEmpty(parts)) return;
            var rs = model.GetComponentsInChildren<Renderer>(true); if (rs.Length == 0) return;
            var b = rs[0].bounds; foreach (var r in rs) b.Encapsulate(r.bounds);
            Vector3 c = b.center, s = b.size; float top = b.max.y;
            foreach (var part in parts.Split('+'))
            {
                switch (part)
                {
                    case "crystals":
                        AddLavaPart(model, "alienglow:SP_Crystal01", new Vector3(0f, top - 0.05f * s.y, c.z - 0.04f * s.z), Vector3.zero, 0.30f * s.z);
                        AddLavaPart(model, "alienglow:SP_Crystal01", new Vector3(-0.07f * s.x, top - 0.08f * s.y, c.z - 0.10f * s.z), new Vector3(0f, 0f, 24f), 0.20f * s.z);
                        AddLavaPart(model, "alienglow:SP_Crystal01", new Vector3(0.07f * s.x, top - 0.08f * s.y, c.z - 0.10f * s.z), new Vector3(0f, 0f, -24f), 0.20f * s.z);
                        break;
                    case "spikes":
                        for (int sx = -1; sx <= 1; sx += 2)
                            AddLavaPart(model, "alienglow:SP_Crystal02", new Vector3(sx * 0.32f * s.x, c.y, c.z - 0.02f * s.z), new Vector3(0f, 0f, -sx * 72f), 0.22f * s.z);
                        break;
                    case "antenna":
                        AddLavaPart(model, "alien:SP_Sci-fi_Antenna", new Vector3(0f, top - 0.05f * s.y, c.z - 0.22f * s.z), new Vector3(-12f, 0f, 0f), 0.36f * s.z);
                        break;
                }
            }
        }

        static Material AlienShipRemap(Material m, int palette)
        {
            if (m == null || m.shader == null || m.shader.name.IndexOf("ColorizeSparrow", StringComparison.OrdinalIgnoreCase) < 0) return null;
            return AlienShipMaterial(palette);
        }

        static GameObject[] BuildAlienBosses(Mats M)
        {
            var defs = AlienBossDefs();
            var res = new GameObject[BossCount];
            for (int n = 1; n <= BossCount; n++)
            {
                var d = defs[n - 1];
                bool ship = d.model[0] == 'S' && d.model.Length > 1 && char.IsDigit(d.model[1]);
                var def = new PackBoss { name = "Alien" + n.ToString("00"), triangles = 12000, width = d.width, maxHeight = d.maxHeight, lieAcross = false, spin = d.spin, keepMaterials = true };
                if (ship)
                {
                    def.packPrefab = LavaShipPath(d.model);
                    int pal = d.palette; string parts = d.parts;
                    def.remap = m => AlienShipRemap(m, pal);
                    def.decorate = go => DecorateAlienShip(go, parts);
                }
                else def.packPrefab = AlienDir + "Prefabs/Space Forest/" + AlienFolder(d.model.Substring(6)) + d.model.Substring(6) + ".prefab";
                var prefab = PackBossPrefab(def, EnsurePackBossLow(def), M);
                if (prefab == null) Debug.LogWarning("[SkySquad] alien boss " + n + " " + AlienBossNames[n - 1] + " could not be built (" + def.packPrefab + ")");
                res[n - 1] = prefab;
            }
            return res;
        }

        static string AlienFolder(string name)
        {
            if (name.StartsWith("SP_Crystal")) return "SP_Crystals/";
            if (name.StartsWith("SP_Mountain")) return "SP_Mountains/";
            if (name.StartsWith("SP_Rock")) return "SP_Rocks/";
            if (name.StartsWith("SP_Tree")) return "SP_Trees/";
            if (name.StartsWith("SP_Plant")) return "SP_Plants/";
            return "";
        }

        // ------------------------------------------------------------------ fighters, crate, splash
        static GameObject BuildAlienFighter(Mats M, Meshes X)
        {
            var low = EnsureOH1Low(); if (low == null) return null;
            var body = Lit("AlienFighterBody", Color.white, 0.45f);
            body.SetColor("_BaseColor", new Color(0.22f, 0.34f, 0.52f));
            var alb = AssetDatabase.LoadAssetAtPath<Texture2D>(Root + "/Art/Enemies/OH1_Fuselage_BaseColor.png"); if (alb != null) body.SetTexture("_BaseMap", alb);
            var nrm = NormalMap(Root + "/Art/Enemies/OH1_Fuselage_Normal.png"); if (nrm != null) { body.SetTexture("_BumpMap", nrm); body.EnableKeyword("_NORMALMAP"); }
            if (alb != null) { body.SetTexture("_EmissionMap", alb); body.SetColor("_EmissionColor", new Color(0.10f, 0.85f, 1.0f) * 0.55f); body.EnableKeyword("_EMISSION"); body.globalIlluminationFlags = MaterialGlobalIlluminationFlags.None; }
            var glass = Transparent("AlienFighterGlass", new Color(0.25f, 1f, 0.85f, 0.70f));
            return OH1EnemyPrefab("EnemyFighterAlien", low, X.prop, M, () => null, body, glass, new Color(0.3f, 1f, 0.95f, 0.95f));
        }

        /// <summary>The crate: three slabs of glowing crystal rock stacked on a hovering ground pad, a pool of cyan light under it.</summary>
        static GameObject BuildAlienBreakable(Mats M, Meshes X)
        {
            var slab = AlienPrefab("SP_Rock06"); var pad = AlienPrefab("SP_Ground02");
            if (slab == null || pad == null) return null;
            var root = new GameObject("BreakableAlien");
            var bk = root.AddComponent<Breakable>();
            float raftTop = -1.125f;
            var crate = new GameObject("Crate"); crate.transform.SetParent(root.transform, false);
            int n = 3; float tierH = 1.15f, h = tierH * n;
            crate.transform.localPosition = new Vector3(0f, raftTop + h * 0.5f, 0f);
            var tiers = new GameObject[n]; var rends = new Renderer[n];
            for (int i = 0; i < n; i++)
            {
                var inst = (GameObject)PrefabUtility.InstantiatePrefab(slab); PrefabUtility.UnpackPrefabInstance(inst, PrefabUnpackMode.Completely, InteractionMode.AutomatedAction);
                inst.name = "Tier" + i; inst.transform.SetParent(crate.transform, false);
                var rs = inst.GetComponentsInChildren<Renderer>(true); var b = rs[0].bounds; foreach (var r in rs) b.Encapsulate(r.bounds);
                float kx = 5.0f / b.size.x, ky = tierH / b.size.y, kz = 3.0f / b.size.z;
                inst.transform.localScale = new Vector3(kx, ky, kz);
                inst.transform.localRotation = Quaternion.Euler(0f, (i - 1) * 5f, 0f);
                inst.transform.localPosition = new Vector3(-b.center.x * kx, -h * 0.5f + tierH * (n - 1 - i) - b.min.y * ky, -b.center.z * kz);
                foreach (var r in rs) { r.shadowCastingMode = ShadowCastingMode.On; r.receiveShadows = true; }
                tiers[i] = inst; rends[i] = rs[0];
            }
            var boat = new GameObject("Boat"); boat.transform.SetParent(root.transform, false);
            var pi = (GameObject)PrefabUtility.InstantiatePrefab(pad); PrefabUtility.UnpackPrefabInstance(pi, PrefabUnpackMode.Completely, InteractionMode.AutomatedAction);
            pi.transform.SetParent(boat.transform, false);
            var prs = pi.GetComponentsInChildren<Renderer>(true); var pb = prs[0].bounds; foreach (var r in prs) pb.Encapsulate(r.bounds);
            float pk = 7.2f / Mathf.Max(pb.size.x, pb.size.z);
            pi.transform.localScale = new Vector3(pk, pk * 2.5f, pk);
            pi.transform.localPosition = new Vector3(-pb.center.x * pk, raftTop - pb.max.y * pk * 2.5f, -pb.center.z * pk);
            foreach (var r in prs) { r.shadowCastingMode = ShadowCastingMode.Off; r.receiveShadows = true; }
            var glow = GameObject.CreatePrimitive(PrimitiveType.Quad); UnityEngine.Object.DestroyImmediate(glow.GetComponent<Collider>());
            glow.name = "PadGlow"; glow.transform.SetParent(root.transform, false); glow.transform.localPosition = new Vector3(0f, -1.66f, 0f); glow.transform.localRotation = Quaternion.Euler(90f, 0f, 0f); glow.transform.localScale = new Vector3(11f, 11f, 1f);
            var gr = glow.GetComponent<MeshRenderer>(); gr.sharedMaterial = AM.glow; gr.shadowCastingMode = ShadowCastingMode.Off; gr.receiveShadows = false;
            float boxTop = raftTop + h;
            bk.model = crate.transform; bk.tiers = tiers; bk.crateRenderers = rends;
            bk.boat = boat.transform; bk.boatRenderer = null; bk.weaponBoatMesh = null;
            bk.label = Label3D("Label", root.transform, new Vector3(0f, raftTop + h * 0.45f, -1.65f), 18f, Color.white, fontOutline);
            bk.hint = Label3D("Hint", root.transform, new Vector3(0f, boxTop + 0.82f, -0.6f), 4f, Gold, fontOutlineSmall);
            bk.boxTop = boxTop;
            bk.prizeAura = Cfxr("Misc/CFXR2 Shiny Item (Loop)"); bk.prizeGlow = Cfxr("Light/CFXR3 LightGlow A (Loop)"); bk.prizeTrail = M.tracer;
            return SavePrefab(root, "BreakableAlien");
        }

        static GameObject BuildAlienSplash(Mats M)
        {
            var root = new GameObject("AlienSplash");
            var ps = ParticlePrefab(root, M.particle, 0, 3f, 8f, 0.16f, 0.45f, 0.45f, 0.9f, new Color(0.5f, 1f, 1f), new Color(0.7f, 0.4f, 1f), 1.2f, true);
            var em = ps.emission; em.SetBursts(new ParticleSystem.Burst[0]);
            var main = ps.main; main.playOnAwake = false;
            var sh = ps.shape; sh.shapeType = ParticleSystemShapeType.Cone; sh.angle = 30f; sh.radius = 0.4f; sh.rotation = new Vector3(-90f, 0f, 0f);
            return SavePrefab(root, "AlienSplash");
        }

        // ------------------------------------------------------------------ the entry
        static WorldEntry AlienEntry(GameObject root, WorldEntry sea, Prefabs P, Mats M, Meshes X)
        {
            var A = AM;
            var bosses = BuildAlienBosses(M);
            var fighter = BuildAlienFighter(M, X);
            var crate = BuildAlienBreakable(M, X);
            var splash = BuildAlienSplash(M);
            return new WorldEntry
            {
                id = "alien", displayName = "ALIEN FOREST", tagline = "Glowing lake  -  crystal bosses",
                thumbnail = WorldSprite("world_alien.png", new Color(0.2f, 0.7f, 0.8f)), accent = new Color(0.25f, 0.85f, 0.80f),
                environment = new[] { root }, skybox = A.sky, skyRotation = 0f,
                sunColor = new Color(0.65f, 0.80f, 1f), sunIntensity = 1.3f, sunEuler = new Vector3(42f, -28f, 0f), sunShadow = 0.45f,
                fog = true, fogColor = new Color(0.24f, 0.16f, 0.46f), fogStart = 105f, fogEnd = 250f,
                ambientFromSky = false, ambientSky = new Color(0.30f, 0.28f, 0.60f), ambientEquator = new Color(0.22f, 0.40f, 0.52f), ambientGround = new Color(0.10f, 0.75f, 0.70f), ambientIntensity = 1.2f,
                post = A.post,
                fighterPrefab = fighter != null ? fighter : sea.fighterPrefab, bossPrefabs = bosses, bossPrefabByNumber = bosses, bossAttacks = AlienAttacks(), bossAttacks2 = AlienAttacks2(), bossNames = AlienBossNames, bossColors = null, stageNames = AlienStageNames,
                bossHpMul = 1.7f, breakablePrefab = crate != null ? crate : sea.breakablePrefab, splashPrefab = splash != null ? splash : sea.splashPrefab, surfaceRing = new Color(0.4f, 1f, 1f)
            };
        }

        // ------------------------------------------------------------------ the attacks
        static readonly Color CCyan = new Color(0.30f, 0.95f, 1f), CViolet = new Color(0.70f, 0.40f, 1f), CLime = new Color(0.55f, 1f, 0.35f), CMagenta = new Color(1f, 0.30f, 0.80f), CPearl = new Color(0.85f, 1f, 1f);
        const string GlowAlien = "Light/CFXR3 LightGlow A (Loop)";

        static BossAttack[] AlienAttacks()
        {
            var A = new BossAttack[BossCount];
            // ======== stage 1: LANDING ZONE
            A[0] = Sig(Fly("spore darts", "green_shuriken", 3, 0.18f, 1.6f, 0.5f, MoveStyle.Sway, 1.0f, 0.6f, 0f, 4.4f, 2.4f), ShotOrigin.Muzzle, ShotOrder.LeftToRight, 1f, 1, 0.45f, 0.15f, GlowAlien);
            A[1] = Sig(Fly("light lances", "light", 2, 0.25f, 2.2f, 0.5f, MoveStyle.Dash, 3.0f, 1f, 0f, 4.4f, 2.8f), ShotOrigin.Wings, ShotOrder.Random, 1.6f, 1, 0.45f, 0.2f, GlowAlien);
            A[2] = LZone("spore bursts", 0.5f, MoveStyle.Sway, 0.6f, 0.6f, 0f, 4.4f, 2, 1.8f, 1.0f, 0.15f, Hv("AoE effects/Smoke AOE explosion"), 1.1f, TellGreen(), 4.5f, Hv("Hits and explosions/Green hit"), 4f, 0.35f, 0.25f, GlowAlien);
            A[3] = Sky("nebula strikes", "top_down_beam_circle_green", 3, 0.2f, 0.5f, MoveStyle.Figure8, 1.8f, 0.9f, 0.3f, 4.6f);
            A[4] = LSpikes("crystal lanes", 0.6f, MoveStyle.Sway, 0.8f, 0.5f, 0f, 5.0f, 2, Hv("AoE effects/Crystals front attack"), 1.4f, 1.3f, 7, 1.4f, 0.3f, Hv("Hits and explosions/Snow hit"), 3f, GlowAlien);
            // ======== stage 2: SPORE MARSH
            A[5] = Sig(Fly("prism darts", "wind", 5, 0.09f, 2.4f, 0.4f, MoveStyle.Dash, 3.2f, 1f, 0f, 3.8f, 2.2f), ShotOrigin.Above, ShotOrder.LeftToRight, 1.2f, 1, 0.45f, 0.1f, GlowAlien);
            A[6] = LZone("void blooms", 0.6f, MoveStyle.Figure8, 1.6f, 0.8f, 0.4f, 4.4f, 3, 1.9f, 1.2f, 0.15f, Hv("AoE effects/Plexus AoE"), 1.4f, Gq("Implosion_01"), 3f, Hv("Hits and explosions/Star hit"), 4f, 0.4f, 0.3f, GlowAlien);
            A[7] = LChain("signal chain", 0.5f, MoveStyle.Sway, 1.4f, 0.8f, 0f, 3.8f, 5, Gq("Electricity_01"), 1.6f, Hv("Hits and explosions/Electro hit"), 2.5f, 0.14f, CCyan, 0.3f, GlowAlien);
            A[8] = LSweep("lumen beam", 0.7f, MoveStyle.Sweep, 3.0f, 0.9f, 0f, 4.4f, ShotOrder.LeftToRight, null, 1f, Hv("Hits and explosions/Holy hit"), 3.5f, 2.4f, 1.2f, 0.25f, 0.3f, 3f, true, CCyan, 0.8f, GlowAlien);
            A[9] = LPortal("gate portals", 0.6f, MoveStyle.Dash, 3.0f, 1f, 0f, 3.8f, 3, Hv("Portals/Portal blue"), 2.8f, 0.9f, 0.3f, "magic", 3f, 1.3f, GlowAlien);
            // ======== stage 3: CRYSTAL FIELDS
            A[10] = Sky("phantom bolts", "top_down_lightning_circle_blue", 4, 0.16f, 0.5f, MoveStyle.Orbit, 2.4f, 0.9f, 0.8f, 4.4f);
            A[11] = LPortal("sting gates", 0.5f, MoveStyle.Figure8, 2.2f, 1.2f, 0f, 3.8f, 4, Hv("Portals/Portal green"), 2.6f, 0.7f, 0.22f, "green_shuriken", 3f, 1.5f, GlowAlien);
            A[12] = LWave("monolith pulse", 0.9f, MoveStyle.Sway, 1.0f, 0.5f, 0f, 5.0f, 1.4f, 0f, 1.2f, Hv("AoE effects/Laser AOE"), 1.3f, Hv("Magic circles/Healing circle"), 0.3f, null, 1f, 0.4f, GlowAlien);
            A[13] = LChain("ion chain", 0.5f, MoveStyle.Figure8, 2.0f, 1.0f, 0.5f, 3.6f, 6, Gq("Lightning_02"), 3.5f, Hv("Hits and explosions/Electro hit"), 2.5f, 0.12f, CViolet, 0.36f, GlowAlien);
            A[14] = LTornado("root storms", 0.6f, MoveStyle.Sway, 0.8f, 0.5f, 0f, 5.2f, 2, Gq("Tornado_01"), 3f, 1.6f, 2.6f, 2.4f, 0.8f, null, 1f, 0.2f, GlowAlien);
            // ======== stage 4: GLOW CANYON
            A[15] = LSweep("aurora rays", 0.7f, MoveStyle.Orbit, 3.0f, 0.9f, 0.8f, 4.4f, ShotOrder.Random, null, 1f, Hv("Hits and explosions/Green hit"), 4f, 2.8f, 1.2f, 0.25f, 0.3f, 2.2f, true, CLime, 0.9f, GlowAlien);
            A[16] = Sig(Fly("comet shower", "frost", 4, 0.10f, 2.6f, 0.4f, MoveStyle.Dash, 3.4f, 1f, 0f, 3.8f, 2.6f), ShotOrigin.Above, ShotOrder.CenterOut, 1.4f, 2, 0.5f, 0.15f, GlowAlien);
            A[17] = LZone("pyramid nova", 0.5f, MoveStyle.Dash, 3.4f, 1f, 0f, 3.8f, 4, 2.0f, 0.8f, 0.15f, Hv("AoE effects/Ground AOE explosion"), 1.1f, TellBlue(), 4f, Hv("Hits and explosions/Snow hit"), 4f, 0.22f, 0.3f, GlowAlien);
            A[18] = LSweep("mantis scythes", 0.6f, MoveStyle.Sweep, 3.0f, 1.2f, 0f, 4.2f, ShotOrder.CenterOut, null, 1f, Hv("Hits and explosions/Love hit"), 3f, 2.0f, 1.1f, 0.18f, 0.3f, 3f, true, CViolet, 0.5f, GlowAlien);
            A[19] = LSpikes("prism rows", 0.4f, MoveStyle.Dash, 3.6f, 1f, 0f, 3.2f, 3, Hv("AoE effects/Crystals crossfade 2"), 0.45f, 1.1f, 8, 1.5f, 0.25f, Hv("Hits and explosions/Snow hit"), 3f, GlowAlien);
            // ======== stage 5: DEEP FOREST
            A[20] = LTornado("plasma walkers", 0.6f, MoveStyle.Sway, 0.8f, 0.5f, 0f, 5.2f, 3, Gq("Tornado_01"), 2.8f, 1.6f, 3.0f, 1.8f, 0.9f, Hv("Hits and explosions/Green hit"), 3f, 0.2f, GlowAlien);
            A[21] = Sig(Fly("gravity lance", "magic", 1, 0.2f, 0.5f, 0.7f, MoveStyle.Sway, 1.4f, 0.8f, 0f, 4.8f, 4.5f), ShotOrigin.Muzzle, ShotOrder.Random, 2.6f, 4, 0.35f, 0.25f, GlowAlien, 1.4f);
            A[22] = Sky("frost spears", "top_down_beam_dot_purple", 3, 0.22f, 0.7f, MoveStyle.Sway, 1.2f, 0.7f, 0f, 4.8f);
            A[23] = LPortal("shard gates", 0.5f, MoveStyle.Sweep, 3.4f, 1.8f, 0f, 3.4f, 4, Hv("Portals/Portal yellow"), 2.6f, 0.7f, 0.18f, "light", 3f, 1.6f, GlowAlien);
            A[24] = LZone("spore rain", 1.0f, MoveStyle.Sway, 1.0f, 0.5f, 0f, 5.4f, 5, 1.5f, 1.2f, 0.15f, Hv("AoE effects/Snow AOE"), 0.9f, TellBlue(), 3.5f, Hv("Hits and explosions/Snow hit"), 3f, 0.18f, 0.4f, GlowAlien);
            // ======== stage 6: ALIEN HEART
            A[25] = LSweep("kestrel beam", 0.6f, MoveStyle.Sweep, 3.4f, 1.2f, 0f, 3.8f, ShotOrder.LeftToRight, null, 1f, Hv("Hits and explosions/Star hit"), 3f, 1.8f, 1.1f, 0.16f, 0.3f, 3f, true, CPearl, 0.6f, GlowAlien);
            A[26] = LWave("sphinx wall", 1.0f, MoveStyle.Sweep, 3.0f, 0.8f, 0f, 4.4f, 1.8f, 1.6f, 1.0f, Gq("Shockwave_01"), 5f, Hv("Magic circles/Healing circle"), 0.3f, Hv("Hits and explosions/Star hit"), 4f, 0.5f, GlowAlien);
            A[27] = Sky("wraith lightning", "top_down_lightning_line_green", 5, 0.12f, 0.5f, MoveStyle.Figure8, 2.6f, 1.1f, 0.5f, 3.8f);
            A[28] = LZone("cosmic collapse", 0.9f, MoveStyle.Orbit, 2.4f, 1f, 0.8f, 4.8f, 3, 2.0f, 1.4f, 0.15f, Hv("AoE effects/Plexus AoE"), 1.4f, Gq("Implosion_01"), 3.2f, Hv("Hits and explosions/Star hit"), 4f, 0.4f, 0.4f, GlowAlien);
            A[29] = LZone("world collapse", 1.0f, MoveStyle.Sway, 1.6f, 0.7f, 0f, 4.6f, 4, 2.2f, 1.6f, 0.15f, Hv("AoE effects/Plexus AoE"), 1.6f, Gq("Implosion_01"), 4.5f, Gq("Explosion_01"), 7f, 0.3f, 0.5f, GlowAlien);
            return A;
        }

        static BossAttack[] AlienAttacks2()
        {
            var B = new BossAttack[BossCount];
            B[0] = Sig(Fly("spore salvo", "green_shuriken", 4, 0.12f, 2.4f, 0.4f, MoveStyle.Sway, 1.4f, 1.0f, 0f, 3.4f, 2.4f), ShotOrigin.Wings, ShotOrder.CenterOut, 1.2f, 2, 0.5f, 0.2f, GlowAlien);
            B[1] = Sig(Fly("lance storm", "light", 3, 0.15f, 3.0f, 0.3f, MoveStyle.Dash, 3.6f, 1.2f, 0f, 3.0f, 2.8f), ShotOrigin.Sides, ShotOrder.Random, 1.8f, 1, 0.45f, 0.2f, GlowAlien);
            B[2] = LZone("spore storm", 0.4f, MoveStyle.Sway, 1.4f, 0.9f, 0f, 3.4f, 5, 1.7f, 0.8f, 0.15f, Hv("AoE effects/Smoke AOE explosion"), 1.1f, TellGreen(), 4f, Hv("Hits and explosions/Green hit"), 4f, 0.15f, 0.3f, GlowAlien);
            B[3] = Sky("nebula storm", "top_down_beam_circle_green", 5, 0.12f, 0.4f, MoveStyle.Figure8, 2.4f, 1.2f, 0.5f, 3.4f);
            B[4] = LSweep("hydra beams", 0.4f, MoveStyle.Sway, 1.4f, 1.0f, 0f, 3.4f, ShotOrder.OutsideIn, null, 1f, Hv("Hits and explosions/Snow hit"), 3f, 2.0f, 1.3f, 0.2f, 0.3f, 3f, true, CCyan, 0.7f, GlowAlien);
            B[5] = Sig(Fly("prism swarm", "wind", 7, 0.07f, 3.0f, 0.3f, MoveStyle.Dash, 3.6f, 1.4f, 0f, 3.2f, 2.2f), ShotOrigin.Above, ShotOrder.CenterOut, 1.4f, 2, 0.5f, 0.15f, GlowAlien);
            B[6] = LZone("void field", 0.4f, MoveStyle.Dash, 3.4f, 1.3f, 0f, 3.2f, 6, 1.8f, 0.8f, 0.15f, Hv("AoE effects/Plexus AoE"), 1.2f, TellRune(), 1.3f, Hv("Hits and explosions/Star hit"), 3f, 0.14f, 0.3f, GlowAlien);
            B[7] = LChain("signal storm", 0.4f, MoveStyle.Figure8, 2.4f, 1.2f, 0.5f, 3.2f, 8, Gq("Lightning_01"), 4f, Hv("Hits and explosions/Electro hit"), 2.5f, 0.1f, CPearl, 0.3f, GlowAlien);
            B[8] = LSweep("lumen cross", 0.5f, MoveStyle.Figure8, 2.8f, 0.9f, 0.8f, 3.6f, ShotOrder.OutsideIn, null, 1f, Hv("Hits and explosions/Holy hit"), 3f, 2.2f, 1.2f, 0.2f, 0.3f, 3f, true, CLime, 0.6f, GlowAlien);
            B[9] = LPortal("gate barrage", 0.3f, MoveStyle.Sweep, 3.6f, 2.2f, 0f, 3.0f, 5, Hv("Portals/Portal blue"), 2.6f, 0.6f, 0.12f, "magic", 3.2f, 1.7f, GlowAlien);
            B[10] = LZone("phantom rain", 0.5f, MoveStyle.Figure8, 3.0f, 1.2f, 0.8f, 3.4f, 5, 1.8f, 1.0f, 0.15f, Hv("AoE effects/Snow AOE"), 0.9f, TellBlue(), 3.5f, Hv("Hits and explosions/Snow hit"), 3f, 0.16f, 0.4f, GlowAlien);
            B[11] = LChain("sting chain", 0.4f, MoveStyle.Orbit, 2.6f, 1.2f, 0.9f, 3.2f, 7, Gq("Impact_01"), 3f, Hv("Hits and explosions/Green hit"), 3f, 0.11f, CLime, 0.3f, GlowAlien);
            B[12] = LWave("monolith quake", 0.8f, MoveStyle.Dash, 3.0f, 1f, 0f, 3.6f, 1.2f, 0.9f, 1.0f, Gq("Shockwave_01"), 5f, Hv("Magic circles/Healing circle"), 0.3f, Hv("Hits and explosions/Star hit"), 4f, 0.5f, GlowAlien);
            B[13] = LPortal("ion gates", 0.3f, MoveStyle.Orbit, 2.8f, 1.2f, 0.9f, 3.0f, 6, Hv("Portals/Portal green"), 2.4f, 0.6f, 0.11f, "electric", 3f, 1.8f, GlowAlien);
            B[14] = LTornado("elder storm", 0.5f, MoveStyle.Sway, 1.2f, 0.8f, 0f, 3.8f, 4, Gq("Tornado_01"), 2.6f, 1.5f, 2.2f, 3.0f, 0.5f, null, 1f, 0.3f, GlowAlien);
            B[15] = LZone("aurora fall", 0.7f, MoveStyle.Orbit, 2.4f, 1.0f, 0.8f, 3.8f, 3, 2.4f, 1.5f, 0.15f, Hv("AoE effects/Snow AOE"), 1.1f, Gq("Implosion_01"), 3f, Hv("Hits and explosions/Holy hit"), 4f, 0.4f, 0.4f, GlowAlien);
            B[16] = Sky("hawk lightning", "top_down_lightning_circle_blue", 6, 0.1f, 0.4f, MoveStyle.Dash, 3.6f, 1.3f, 0f, 3.2f);
            B[17] = LSpikes("pyramid rows", 0.4f, MoveStyle.Figure8, 3.0f, 1.3f, 0.6f, 3.2f, 5, Hv("AoE effects/Crystals front attack"), 1.3f, 1.2f, 6, 1.1f, 0.14f, Hv("Hits and explosions/Snow hit"), 3f, GlowAlien);
            B[18] = LSweep("mantis shears", 0.5f, MoveStyle.Sweep, 3.4f, 1.6f, 0f, 3.2f, ShotOrder.OutsideIn, null, 1f, Hv("Hits and explosions/Love hit"), 3f, 1.8f, 1.1f, 0.16f, 0.3f, 3f, true, CMagenta, 0.55f, GlowAlien);
            B[19] = LWave("prism wall", 0.8f, MoveStyle.Sweep, 3.2f, 1.2f, 0f, 3.6f, 1.3f, 0f, 1.0f, Hv("AoE effects/Laser AOE"), 1.3f, Hv("Magic circles/Healing circle"), 0.3f, null, 1f, 0.4f, GlowAlien);
            B[20] = LTornado("wraith storm", 0.4f, MoveStyle.Sweep, 3.4f, 1.8f, 0f, 3.2f, 4, Gq("Tornado_01"), 3f, 1.5f, 2.0f, 3.4f, 0.4f, Hv("Hits and explosions/Green hit"), 3f, 0.3f, GlowAlien);
            B[21] = Sig(Fly("gravity barrage", "magic", 3, 0.1f, 2.4f, 0.4f, MoveStyle.Dash, 3.0f, 1.3f, 0f, 3.6f, 4.0f), ShotOrigin.Wings, ShotOrder.CenterOut, 2.8f, 3, 0.4f, 0.3f, GlowAlien, 1.4f);
            B[22] = Sky("frost storm", "top_down_beam_dot_purple", 6, 0.1f, 0.5f, MoveStyle.Figure8, 2.6f, 1.1f, 0.5f, 3.4f);
            B[23] = LPortal("scarab swarm", 0.3f, MoveStyle.Orbit, 2.8f, 1.2f, 0.9f, 3.0f, 6, Hv("Portals/Portal yellow"), 2.4f, 0.6f, 0.11f, "light", 3f, 1.8f, GlowAlien);
            B[24] = LZone("cap collapse", 0.9f, MoveStyle.Orbit, 1.6f, 1.0f, 0.9f, 4.2f, 1, 3.2f, 1.9f, 0.15f, Hv("AoE effects/Smoke AOE explosion"), 1.4f, Gq("Implosion_01"), 4.5f, Hv("Hits and explosions/Star hit"), 6f, 0.5f, 0.5f, GlowAlien);
            B[25] = LSweep("kestrel crescents", 0.5f, MoveStyle.Orbit, 3.2f, 1.3f, 0.8f, 3.2f, ShotOrder.OutsideIn, null, 1f, Hv("Hits and explosions/Star hit"), 3f, 2.0f, 1.1f, 0.15f, 0.3f, 3f, true, CViolet, 0.65f, GlowAlien);
            B[26] = LWave("sphinx walls", 0.8f, MoveStyle.Figure8, 3.2f, 1.2f, 0.6f, 3.4f, 1.4f, 1.2f, 1.0f, Gq("Shockwave_01"), 5f, Hv("Magic circles/Healing circle"), 0.3f, Hv("Hits and explosions/Holy hit"), 4f, 0.5f, GlowAlien);
            B[27] = Sky("wraith storm", "top_down_lightning_line_green", 7, 0.1f, 0.4f, MoveStyle.Sweep, 3.4f, 1.4f, 0f, 3.0f);
            B[28] = LZone("phoenix rebirth", 0.5f, MoveStyle.Figure8, 3.2f, 1.2f, 0.9f, 3.4f, 6, 1.8f, 0.9f, 0.15f, Hv("AoE effects/Plexus AoE"), 1.2f, TellPink(), 1.2f, Hv("Hits and explosions/Love hit"), 4f, 0.13f, 0.4f, GlowAlien);
            B[29] = LSweep("devouring beams", 0.6f, MoveStyle.Sweep, 3.4f, 1.4f, 0f, 3.2f, ShotOrder.OutsideIn, null, 1f, Gq("Explosion_01"), 3f, 2.8f, 1.3f, 0.14f, 0.4f, 3f, true, CCyan, 0.9f, GlowAlien);
            return B;
        }
    }
}
