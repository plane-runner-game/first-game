// SceneBuilder.LavaBosses.cs (Editor only)
// The lava world's cast (2026-10-02: "the bosses of this level must be its own - everything lava"): the fighters, the crate on its raft, and thirty
// bosses in six stages of five, each with two attacks of fire, ash and magma. Eighteen bosses are ships (the Star Sparrow hulls the sea world did
// not use, plus one HiRez) repainted in obsidian / ember / copper / bone liveries with horns, tusks, crystals and gears from the Inferno pack
// bolted on; twelve are relics of the volcano itself - the horned lid, the forge cube, the cogwork, the cauldron, the red axe, the great gear,
// the molten urn, the mimic chest, the obelisk, the tower, the furnace and, at the end, the statue of the Inferno King.
using System;
using System.Collections.Generic;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;

namespace SkySquad.EditorTools
{
    public static partial class SceneBuilder
    {
        static readonly string[] LavaBossNames = {
            "CINDER WASP", "SPARK VIPER", "HORNED MAW", "EMBER BAT", "FORGE WARDEN",
            "ASH HORNET", "SOOT REAPER", "COGWORK DRAKE", "OBSIDIAN FANG", "CAULDRON KING",
            "BASALT CROWN", "LAVA STINGER", "RED AXE", "SLAG BEETLE", "IRON GEARHEART",
            "FIRE SERAPH", "CRATER HAWK", "MOLTEN URN", "VOLCANO MANTIS", "HORNED MIMIC",
            "PYRO WRAITH", "BRIMSTONE LANCE", "OBSIDIAN OBELISK", "MAGMA SCARAB", "EMBER TOWER",
            "DEMON KESTREL", "SCORCHED SPHINX", "FURNACE SENTINEL", "PHOENIX ASH", "INFERNO KING" };
        static readonly string[] LavaStageNames = { "EMBER SHORE", "ASH PLAINS", "OBSIDIAN GATE", "MAGMA FALLS", "VOLCANO HEART", "INFERNO THRONE" };

        /// <summary>One lava boss: a ship (a pack prefab, a livery, what is bolted on) or a relic (an Inferno prefab fitted by height).</summary>
        class LavaBossDef
        {
            public string model;          // "S31" (a Star Sparrow), "H1R" (the HiRez red), or an Inferno prefab "Props/Box_001"
            public int palette;           // livery for the ship's paint zones
            public string parts = "";     // horns, tusks, crystals, gear (joined with +)
            public float width = 3.0f, maxHeight = 0f;
            public bool spin;             // a relic that turns (the gears)
            public LavaBossDef(string model, int palette, string parts = "", float width = 3f, float maxHeight = 0f, bool spin = false) { this.model = model; this.palette = palette; this.parts = parts; this.width = width; this.maxHeight = maxHeight; this.spin = spin; }
        }

        static LavaBossDef[] LavaBossDefs()
        {
            var d = new LavaBossDef[BossCount];
            // stage 1: EMBER SHORE
            d[0] = new LavaBossDef("S31", 0, "horns", 2.9f);
            d[1] = new LavaBossDef("S12", 1, "tusks", 2.9f);
            d[2] = new LavaBossDef("Props/Lid_002", 0, "", 2.6f, 2.2f);
            d[3] = new LavaBossDef("S16", 2, "crystals", 3.0f);
            d[4] = new LavaBossDef("Props/Box_001", 0, "", 2.4f, 2.6f);
            // stage 2: ASH PLAINS
            d[5] = new LavaBossDef("S25", 3, "horns+crystals", 3.0f);
            d[6] = new LavaBossDef("S33", 4, "tusks+crystals", 3.0f);
            d[7] = new LavaBossDef("Props/Gear_002", 0, "", 2.4f, 2.5f, true);
            d[8] = new LavaBossDef("S3", 7, "horns", 3.0f);
            d[9] = new LavaBossDef("Props/Brazier_004", 0, "", 2.9f, 2.0f);
            // stage 3: OBSIDIAN GATE
            d[10] = new LavaBossDef("S20", 5, "gear", 3.1f);
            d[11] = new LavaBossDef("S34", 6, "tusks", 3.0f);
            d[12] = new LavaBossDef("Statues/Axe_001", 0, "", 2.0f, 3.6f);
            d[13] = new LavaBossDef("S28", 0, "horns+gear", 3.0f);
            d[14] = new LavaBossDef("Props/Gear_001", 0, "", 2.8f, 2.9f, true);
            // stage 4: MAGMA FALLS
            d[15] = new LavaBossDef("S4", 4, "crystals+horns", 3.2f);
            d[16] = new LavaBossDef("S27", 3, "tusks", 3.0f);
            d[17] = new LavaBossDef("Props/Vase_001", 0, "", 2.0f, 2.3f);
            d[18] = new LavaBossDef("S32", 2, "horns+tusks", 3.0f);
            d[19] = new LavaBossDef("Decorations/ChestBig_001", 0, "", 2.9f, 2.9f);
            // stage 5: VOLCANO HEART
            d[20] = new LavaBossDef("S36", 7, "crystals", 3.0f);
            d[21] = new LavaBossDef("S29", 6, "tusks+crystals", 3.0f);
            d[22] = new LavaBossDef("Decorations/ColumnBig_001", 0, "", 2.3f, 3.3f);
            d[23] = new LavaBossDef("S37", 1, "gear", 3.0f);
            d[24] = new LavaBossDef("Buildings/TowerBig_001", 0, "", 1.8f, 4.0f);
            // stage 6: INFERNO THRONE
            d[25] = new LavaBossDef("S2", 0, "horns+crystals", 3.2f);
            d[26] = new LavaBossDef("S40", 5, "horns+gear", 3.1f);
            d[27] = new LavaBossDef("Props/Brazier_002", 0, "", 2.1f, 2.7f);
            d[28] = new LavaBossDef("H1R", 7, "horns", 3.8f);
            d[29] = new LavaBossDef("Statues/StatueKnight_002", 0, "", 2.4f, 3.0f);
            return d;
        }

        // the liveries: paint zone 1 (the hull), 2 (panels), 3 (trim), then the three glow colours of the engines and lights and the cockpit - all heated
        static readonly Color[][] LavaPalettes = {
            new[] { new Color(0.07f, 0.06f, 0.07f), new Color(0.20f, 0.07f, 0.04f), new Color(0.60f, 0.22f, 0.05f), new Color(0.40f, 0.04f, 0.0f), new Color(1f, 0.32f, 0.03f), new Color(1f, 0.80f, 0.25f) },   // 0 obsidian
            new[] { new Color(0.46f, 0.08f, 0.03f), new Color(0.12f, 0.06f, 0.06f), new Color(0.95f, 0.42f, 0.08f), new Color(0.45f, 0.05f, 0.0f), new Color(1f, 0.38f, 0.04f), new Color(1f, 0.85f, 0.35f) },  // 1 ember
            new[] { new Color(0.30f, 0.28f, 0.28f), new Color(0.11f, 0.10f, 0.11f), new Color(0.78f, 0.30f, 0.08f), new Color(0.35f, 0.05f, 0.0f), new Color(1f, 0.30f, 0.03f), new Color(1f, 0.70f, 0.20f) },  // 2 ash
            new[] { new Color(0.52f, 0.24f, 0.09f), new Color(0.14f, 0.07f, 0.05f), new Color(1f, 0.66f, 0.20f), new Color(0.40f, 0.08f, 0.0f), new Color(1f, 0.45f, 0.06f), new Color(1f, 0.90f, 0.45f) },    // 3 copper
            new[] { new Color(0.72f, 0.64f, 0.50f), new Color(0.20f, 0.09f, 0.06f), new Color(0.92f, 0.36f, 0.06f), new Color(0.45f, 0.06f, 0.0f), new Color(1f, 0.34f, 0.04f), new Color(1f, 0.82f, 0.30f) },  // 4 bone
            new[] { new Color(0.80f, 0.22f, 0.04f), new Color(0.10f, 0.06f, 0.06f), new Color(1f, 0.80f, 0.20f), new Color(0.50f, 0.05f, 0.0f), new Color(1f, 0.50f, 0.05f), new Color(1f, 0.92f, 0.5f) },     // 5 magma
            new[] { new Color(0.68f, 0.52f, 0.08f), new Color(0.08f, 0.07f, 0.06f), new Color(1f, 0.36f, 0.05f), new Color(0.45f, 0.10f, 0.0f), new Color(1f, 0.55f, 0.06f), new Color(1f, 0.95f, 0.5f) },    // 6 sulfur
            new[] { new Color(0.34f, 0.03f, 0.05f), new Color(0.10f, 0.05f, 0.06f), new Color(0.92f, 0.16f, 0.10f), new Color(0.50f, 0.02f, 0.03f), new Color(1f, 0.22f, 0.06f), new Color(1f, 0.70f, 0.30f) }, // 7 crimson
        };

        static readonly Dictionary<int, Material> lavaShipMats = new Dictionary<int, Material>();

        /// <summary>The Star Sparrow paint shader (Colorize) in a lava livery: its three paint zones and three glows recoloured. One material per palette, saved under Generated.</summary>
        static Material LavaShipMaterial(int palette)
        {
            if (lavaShipMats.TryGetValue(palette, out var have) && have != null) return have;
            var src = AssetDatabase.LoadAssetAtPath<Material>("Assets/StarSparrow/Materials/StarSparrow_Black.mat");
            if (src == null) return null;
            string path = Gen + "/Materials/LavaShip" + palette + ".mat";
            var m = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (m == null) { m = new Material(src); AssetDatabase.CreateAsset(m, path); }
            m.shader = src.shader; m.CopyPropertiesFromMaterial(src);
            var p = LavaPalettes[palette % LavaPalettes.Length];
            m.SetColor("_Color1", p[0]); m.SetColor("_Color2", p[1]); m.SetColor("_Color3", p[2]);
            m.SetColor("_Emission1", p[3]); m.SetColor("_Emission2", p[4]); m.SetColor("_Emission3", p[5]);
            m.SetColor("_Cockpit1", p[3]); m.SetColor("_Cockpit2", p[4]); m.SetColor("_Cockpit3", p[5]);
            m.SetFloat("_EmissionMultiplier", 2.2f); m.SetFloat("_CockpitMultiplier", 1.6f); m.SetFloat("_Dirty", 0.35f); m.SetFloat("_Darken", 0f);
            EditorUtility.SetDirty(m);
            lavaShipMats[palette] = m;
            return m;
        }

        /// <summary>An Inferno piece fitted to a hull: its base (or, for a disc, its middle) sits at pos, turned by euler about that point, `height` tall.</summary>
        static GameObject AddLavaPart(GameObject model, string rel, Vector3 pos, Vector3 euler, float height, bool mirror = false, bool centred = false, string name = null)
        {
            var prefab = InfPrefab(rel); if (prefab == null) return null;
            var inst = (GameObject)PrefabUtility.InstantiatePrefab(prefab); PrefabUtility.UnpackPrefabInstance(inst, PrefabUnpackMode.Completely, InteractionMode.AutomatedAction);
            var prs = inst.GetComponentsInChildren<Renderer>(true);   // measured on the instance at the origin, in world units: the pack's own import scale is already in them
            var bb = prs.Length > 0 ? prs[0].bounds : new Bounds(Vector3.zero, Vector3.one); foreach (var r in prs) bb.Encapsulate(r.bounds);
            var holder = new GameObject(name ?? "Part_" + rel.Substring(rel.LastIndexOf('/') + 1)); holder.transform.SetParent(model.transform, false);
            holder.transform.localPosition = pos; holder.transform.localRotation = Quaternion.Euler(euler);
            inst.transform.SetParent(holder.transform, false);
            float k = height / Mathf.Max(0.001f, bb.size.y);
            inst.transform.localScale = new Vector3(mirror ? -k : k, k, k);
            Vector3 off = centred ? bb.center : new Vector3(bb.center.x, bb.min.y, bb.center.z);
            inst.transform.localPosition = new Vector3(-off.x * (mirror ? -k : k), -off.y * k, -off.z * k);
            foreach (var r in inst.GetComponentsInChildren<Renderer>()) { r.shadowCastingMode = ShadowCastingMode.On; r.receiveShadows = true; }
            return holder;
        }

        /// <summary>Horns, tusks, crystals and a gear fitted to a Star Sparrow hull, sized and placed from its own bounds (nose +z, up +y).</summary>
        static void DecorateLavaShip(GameObject model, string parts, int palette)
        {
            if (string.IsNullOrEmpty(parts)) return;
            var rs = model.GetComponentsInChildren<Renderer>(true); if (rs.Length == 0) return;
            var b = rs[0].bounds; foreach (var r in rs) b.Encapsulate(r.bounds);   // the model sits at the origin, unscaled: world bounds are its own
            Vector3 c = b.center, s = b.size; float top = b.max.y;
            foreach (var part in parts.Split('+'))
            {
                switch (part)
                {
                    case "horns":
                        for (int sx = -1; sx <= 1; sx += 2)
                            AddLavaPart(model, "Decorations/Bone_004", new Vector3(sx * 0.13f * s.x, top - 0.10f * s.y, c.z + 0.16f * s.z), new Vector3(-8f, 0f, -sx * 24f), 0.20f * s.z, sx < 0);
                        break;
                    case "tusks":
                        for (int sx = -1; sx <= 1; sx += 2)
                            AddLavaPart(model, "Decorations/Bone_003", new Vector3(sx * 0.10f * s.x, c.y - 0.05f * s.y, b.max.z - 0.34f * s.z), new Vector3(82f, 0f, sx * 12f), 0.30f * s.z, sx < 0);
                        break;
                    case "crystals":
                        {
                            string gem = palette == 7 || palette == 2 ? "Props/Gem_004" : "Props/Gem_003";
                            AddLavaPart(model, gem, new Vector3(0f, top - 0.05f * s.y, c.z - 0.04f * s.z), Vector3.zero, 0.30f * s.z);
                            AddLavaPart(model, gem, new Vector3(-0.07f * s.x, top - 0.08f * s.y, c.z - 0.10f * s.z), new Vector3(0f, 0f, 24f), 0.20f * s.z);
                            AddLavaPart(model, gem, new Vector3(0.07f * s.x, top - 0.08f * s.y, c.z - 0.10f * s.z), new Vector3(0f, 0f, -24f), 0.20f * s.z);
                            break;
                        }
                    case "gear":
                        AddLavaPart(model, "Props/Gear_002", new Vector3(0f, top + 0.05f * s.y, c.z - 0.20f * s.z), new Vector3(60f, 0f, 0f), 0.42f * s.x, false, true, "SpinGear");
                        break;
                }
            }
        }

        static Material LavaShipRemap(Material m, int palette)
        {
            if (m == null || m.shader == null || m.shader.name.IndexOf("ColorizeSparrow", StringComparison.OrdinalIgnoreCase) < 0) return null;   // only the hull's paint: the Inferno parts keep their own materials
            return LavaShipMaterial(palette);
        }

        static string LavaShipPath(string code)
        {
            if (code == "H1R") return "Assets/HiRezSpaceshipsCreatorFree/Prefabs/ExamplesNoInterior/Example1NoInterior_Red.prefab";
            return "Assets/StarSparrow/Prefabs/Examples/StarSparrow" + code.Substring(1) + ".prefab";
        }

        /// <summary>The thirty lava bosses as prefabs, indexed by boss number - 1.</summary>
        static GameObject[] BuildLavaBosses(Mats M)
        {
            var defs = LavaBossDefs();
            var res = new GameObject[BossCount];
            for (int n = 1; n <= BossCount; n++)
            {
                var d = defs[n - 1];
                bool ship = d.model[0] == 'S' && char.IsDigit(d.model[1]) || d.model == "H1R";
                var def = new PackBoss { name = "Lava" + n.ToString("00"), triangles = 12000, width = d.width, maxHeight = d.maxHeight, lieAcross = false, spin = d.spin };
                if (ship)
                {
                    def.packPrefab = LavaShipPath(d.model);
                    def.keepMaterials = d.model[0] == 'S';
                    if (d.model[0] == 'S') { int pal = d.palette; def.remap = m => LavaShipRemap(m, pal); }
                    int palette = d.palette; string parts = d.parts;
                    def.decorate = go => DecorateLavaShip(go, parts, palette);
                }
                else { def.packPrefab = Inf + "Prefabs/" + d.model + ".prefab"; def.keepMaterials = true; }
                var prefab = PackBossPrefab(def, EnsurePackBossLow(def), M);
                if (prefab == null) Debug.LogWarning("[SkySquad] lava boss " + n + " " + LavaBossNames[n - 1] + " could not be built (" + def.packPrefab + ")");
                res[n - 1] = prefab;
            }
            return res;
        }

        // ------------------------------------------------------------------ the fighters
        static GameObject BuildLavaFighter(Mats M, Meshes X)
        {
            var low = EnsureOH1Low(); if (low == null) return null;
            var body = Lit("LavaFighterBody", Color.white, 0.35f);
            body.SetColor("_BaseColor", new Color(0.33f, 0.24f, 0.22f));
            var alb = AssetDatabase.LoadAssetAtPath<Texture2D>(Root + "/Art/Enemies/OH1_Fuselage_BaseColor.png"); if (alb != null) body.SetTexture("_BaseMap", alb);
            var nrm = NormalMap(Root + "/Art/Enemies/OH1_Fuselage_Normal.png"); if (nrm != null) { body.SetTexture("_BumpMap", nrm); body.EnableKeyword("_NORMALMAP"); }
            if (alb != null) { body.SetTexture("_EmissionMap", alb); body.SetColor("_EmissionColor", new Color(1.0f, 0.22f, 0.03f) * 0.55f); body.EnableKeyword("_EMISSION"); body.globalIlluminationFlags = MaterialGlobalIlluminationFlags.None; }   // the paint glows ember-red through its own detail
            var glass = Transparent("LavaFighterGlass", new Color(0.95f, 0.38f, 0.08f, 0.70f));
            return OH1EnemyPrefab("EnemyFighterLava", low, X.prop, M, () => null, body, glass, new Color(1f, 0.40f, 0.08f, 0.95f));
        }

        // ------------------------------------------------------------------ the crate: a horned chest on a slab of basalt
        static GameObject BuildLavaBreakable(Mats M, Meshes X)
        {
            var chestPrefab = InfPrefab("Decorations/ChestBig_001"); var rockPrefab = InfPrefab("Rocks/Stone_006");
            if (chestPrefab == null || rockPrefab == null) return null;
            var root = new GameObject("BreakableLava");
            var bk = root.AddComponent<Breakable>();
            float raftTop = -1.125f;   // where the box stood on the boat deck
            // the chest: the pack's horned treasure chest, 5 wide, its front (the key) turned to the camera
            var crate = new GameObject("Crate"); crate.transform.SetParent(root.transform, false);
            var chest = (GameObject)PrefabUtility.InstantiatePrefab(chestPrefab); PrefabUtility.UnpackPrefabInstance(chest, PrefabUnpackMode.Completely, InteractionMode.AutomatedAction);
            chest.name = "Chest"; chest.transform.SetParent(crate.transform, false);
            var crs = chest.GetComponentsInChildren<Renderer>(true);
            var cb = crs[0].bounds; foreach (var r in crs) cb.Encapsulate(r.bounds);
            float k = 5.0f / Mathf.Max(0.01f, cb.size.x);
            chest.transform.localRotation = Quaternion.Euler(0f, 180f, 0f);
            chest.transform.localScale = Vector3.one * k;
            float height = cb.size.y * k, depth = cb.size.z * k;
            crate.transform.localPosition = new Vector3(0f, raftTop + height * 0.5f, 0f);   // pivoted at its middle (it rocks about it), its underside on the deck
            chest.transform.localPosition = new Vector3(cb.center.x * k, -cb.center.y * k, cb.center.z * k);   // the bounds' middle on the pivot, after the half turn
            foreach (var r in crs) { r.shadowCastingMode = ShadowCastingMode.On; r.receiveShadows = true; }
            // the raft: a slab of basalt, flat, wide enough to carry it, its top at the deck line, a little of it under the lava
            var rock = new GameObject("Boat"); rock.transform.SetParent(root.transform, false);
            var raftInst = (GameObject)PrefabUtility.InstantiatePrefab(rockPrefab); PrefabUtility.UnpackPrefabInstance(raftInst, PrefabUnpackMode.Completely, InteractionMode.AutomatedAction);
            raftInst.transform.SetParent(rock.transform, false);
            var rmf = raftInst.GetComponentInChildren<MeshFilter>(); var rb = rmf.sharedMesh.bounds;
            float rk = 6.4f / Mathf.Max(0.01f, rb.size.x);
            raftInst.transform.localScale = new Vector3(rk, rk * 0.9f, rk);
            raftInst.transform.localPosition = new Vector3(-rb.center.x * rk, raftTop - rb.max.y * rk * 0.9f, -rb.center.z * rk);
            foreach (var r in raftInst.GetComponentsInChildren<Renderer>()) { r.shadowCastingMode = ShadowCastingMode.Off; r.receiveShadows = true; }
            // the lava glows round the raft: a flat orange pool at the surface (root sits at 1 + supplyAlt = SeaLevel + 1.65 above the lava)
            var glow = GameObject.CreatePrimitive(PrimitiveType.Quad); UnityEngine.Object.DestroyImmediate(glow.GetComponent<Collider>());
            glow.name = "RaftGlow"; glow.transform.SetParent(root.transform, false); glow.transform.localPosition = new Vector3(0f, -1.66f, 0f); glow.transform.localRotation = Quaternion.Euler(90f, 0f, 0f); glow.transform.localScale = new Vector3(11f, 11f, 1f);
            var gr = glow.GetComponent<MeshRenderer>(); gr.sharedMaterial = LM.glow; gr.shadowCastingMode = ShadowCastingMode.Off; gr.receiveShadows = false;
            float boxTop = raftTop + height;
            bk.model = crate.transform; bk.tiers = null;
            bk.crateRenderers = new[] { crs[0] };
            bk.boat = rock.transform; bk.boatRenderer = null; bk.weaponBoatMesh = null;
            bk.label = Label3D("Label", root.transform, new Vector3(0f, raftTop + height * 0.42f, -depth * 0.5f - 0.15f), 18f, Color.white, fontOutline);
            bk.hint = Label3D("Hint", root.transform, new Vector3(0f, boxTop + 0.82f, -0.6f), 4f, Gold, fontOutlineSmall);
            bk.boxTop = boxTop;
            bk.prizeAura = Cfxr("Misc/CFXR2 Shiny Item (Loop)"); bk.prizeGlow = Cfxr("Light/CFXR3 LightGlow A (Loop)"); bk.prizeTrail = M.tracer;
            return SavePrefab(root, "BreakableLava");
        }

        /// <summary>A flat orange splash of sparks where a wreck falls into the lava (the sea's white spray, hot).</summary>
        static GameObject BuildLavaSplash(Mats M)
        {
            var root = new GameObject("LavaSplash");
            var ps = ParticlePrefab(root, M.particle, 0, 3f, 8f, 0.18f, 0.5f, 0.45f, 0.9f, new Color(1f, 0.78f, 0.25f), new Color(1f, 0.32f, 0.05f), 1.2f, true);
            var em = ps.emission; em.SetBursts(new ParticleSystem.Burst[0]);
            var main = ps.main; main.playOnAwake = false;
            var sh = ps.shape; sh.shapeType = ParticleSystemShapeType.Cone; sh.angle = 34f; sh.radius = 0.4f; sh.rotation = new Vector3(-90f, 0f, 0f);
            return SavePrefab(root, "LavaSplash");
        }
    }
}
