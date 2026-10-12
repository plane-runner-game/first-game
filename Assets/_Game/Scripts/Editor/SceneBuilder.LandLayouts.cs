// SceneBuilder.LandLayouts.cs (Editor only)
// The eight land locations, laid out by hand (2026-10-07: "every one a different design, not all alike"), and since 2026-10-08 moving again,
// realistically ("make it move, but realistically, and beautiful"): the scenery is one long strip of LandLoop units that streams toward the
// squad at the scroll speed and loops (WorldScroller.loopLength) - every prop keeps its own size, the far end sinks into the haze - and the
// world ends in its gate (SceneBuilder.LandGates), which stands still and is where the planes come from. Each world: a forest corridor under
// arching trees, night camps by their fires, a village street under arches of lights, dunes and pyramids, a ruined city burning, a stadium,
// a launch pad, a railway town with a train running. Pieces come from any of the pack's dioramas (placed as the author stood them: rockets
// upright, logs lying) or, failing that, from the pack's own prefabs. The view is narrow (portrait, fov 52, camera at z -11): about
// 0.27 x (z + 11) to either side of the lane.
using System.Collections.Generic;
using System.Text.RegularExpressions;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;

namespace SkySquad.EditorTools
{
    public static partial class SceneBuilder
    {
        static readonly string[] LandLocationNames = {
            "autumn atmosphere forest with environment", "camping forest with environment", "christmas village with environment", "desert pyramids with environment",
            "downtown with environment", "soccer field with environment", "space shuttle launch with environment", "wild west railway station with environment" };

        class LandKit
        {
            public Transform root; public System.Random rnd; public Mats M;
            public readonly Dictionary<string, Piece> pieces = new Dictionary<string, Piece>();
            public readonly Dictionary<string, string> prefabs = new Dictionary<string, string>();
            public readonly Dictionary<string, GameObject> dioramas = new Dictionary<string, GameObject>();
            public readonly List<Transform> moving = new List<Transform>();   // what scrolls (WorldScroller.buoys)
            public bool far;                  // placing static pieces (the gate's): not scrolled, they cast shadows
            public Transform parent;          // placing into a group or the gate instead of the world root
            public int n;
            public float R(float a, float b) { return a + (b - a) * (float)rnd.NextDouble(); }
            public string Pick(params string[] a) { return a[rnd.Next(a.Length)]; }
        }

        static string BaseName(string n) { return Regex.Replace(n, @"\s*\(\d+\)$", "").Trim().ToLowerInvariant(); }

        static LandKit OpenLandKit(string location, Transform root, System.Random rnd, Mats M)
        {
            var K = new LandKit { root = root, rnd = rnd, M = M };
            foreach (var g in AssetDatabase.FindAssets("t:Prefab", new[] { AtmoDir + "Prefabs" }))
            {
                var p = AssetDatabase.GUIDToAssetPath(g); if (p.Contains("Prefabs/Location")) continue;
                var nm = System.IO.Path.GetFileNameWithoutExtension(p).ToLowerInvariant(); if (!K.prefabs.ContainsKey(nm)) K.prefabs[nm] = p;
            }
            var order = new List<string>(); if (location != null) order.Add(location); foreach (var l in LandLocationNames) if (l != location) order.Add(l);   // the world's own diorama wins a name
            foreach (var loc in order)
            {
                var asset = AssetDatabase.LoadAssetAtPath<GameObject>(AtmoDir + "Prefabs/Location with environment/" + loc + ".prefab"); if (asset == null) continue;
                var d = (GameObject)PrefabUtility.InstantiatePrefab(asset); d.transform.position = Vector3.zero; d.transform.rotation = Quaternion.identity;
                K.dioramas[loc] = d;
                foreach (var p in LandPieces(d)) { var k = BaseName(p.name); if (!K.pieces.ContainsKey(k)) K.pieces[k] = p; }
            }
            return K;
        }

        static void CloseLandKit(LandKit K) { foreach (var d in K.dioramas.Values) if (d != null) Object.DestroyImmediate(d); K.dioramas.Clear(); K.pieces.Clear(); }

        static void Placed(LandKit K, GameObject holder)
        {
            if (K.parent != null) holder.transform.SetParent(K.parent, true);
            if (!K.far && K.parent == null) K.moving.Add(holder.transform);
            foreach (var r in holder.GetComponentsInChildren<Renderer>(true)) { r.shadowCastingMode = K.far ? ShadowCastingMode.On : ShadowCastingMode.Off; r.receiveShadows = true; }
        }

        /// <summary>One piece standing on the ground at (x, z): its base centre there, `s` times its own size, turned `yaw` degrees.</summary>
        static GameObject Put(LandKit K, string name, float x, float z, float s, float yaw = 0f, float lift = 0f)
        {
            string key = name.ToLowerInvariant(); GameObject holder;
            if (K.pieces.TryGetValue(key, out var p)) holder = ClonePieceTo(p, K.root, name);
            else if (K.prefabs.TryGetValue(key, out var path))
            {
                var inst = (GameObject)PrefabUtility.InstantiatePrefab(AssetDatabase.LoadAssetAtPath<GameObject>(path));
                PrefabUtility.UnpackPrefabInstance(inst, PrefabUnpackMode.Completely, InteractionMode.AutomatedAction);
                var rs = inst.GetComponentsInChildren<Renderer>(true); if (rs.Length == 0) { Object.DestroyImmediate(inst); return null; }
                var b = rs[0].bounds; foreach (var r in rs) b.Encapsulate(r.bounds);
                holder = new GameObject(name); holder.transform.SetParent(K.root, false);
                inst.name = "Visual"; inst.transform.SetParent(holder.transform, false);
                inst.transform.localPosition = new Vector3(inst.transform.localPosition.x - b.center.x, inst.transform.localPosition.y - b.min.y, inst.transform.localPosition.z - b.center.z);
                foreach (var r in rs) { var ms = r.sharedMaterials; for (int i = 0; i < ms.Length; i++) ms[i] = AtmoMaterial(); r.sharedMaterials = ms; }
            }
            else { Debug.LogWarning("[SkySquad] land piece missing: " + name); return null; }
            holder.name = "Prop" + K.n++ + "_" + name;
            holder.transform.position = new Vector3(x, SeaLevel - 0.03f + lift, z);
            holder.transform.rotation = Quaternion.Euler(0f, yaw, 0f);
            holder.transform.localScale = Vector3.one * s;
            Placed(K, holder);
            return holder;
        }

        /// <summary>Starts a set piece that scrolls as one (a camp with its fire and light, a ruin with its smoke, the train): what is placed until
        /// EndGroup goes inside it.</summary>
        static Transform Group(LandKit K, string name, Vector3 pos)
        {
            var g = new GameObject(name); g.transform.SetParent(K.root, false); g.transform.position = pos;
            K.moving.Add(g.transform); K.parent = g.transform;
            return g.transform;
        }
        static void EndGroup(LandKit K) { K.parent = null; }

        static Bounds WorldBounds(GameObject go)
        {
            var rs = go.GetComponentsInChildren<Renderer>(true); var b = rs[0].bounds; foreach (var r in rs) b.Encapsulate(r.bounds); return b;
        }

        /// <summary>Slides a placed piece sideways so its edge nearest the lane is at |x| = inner. Returns its depth along z.</summary>
        static float Flank(GameObject go, int side, float inner)
        {
            if (go == null) return 0f;
            var b = WorldBounds(go);
            float edge = side > 0 ? b.min.x : -b.max.x;
            go.transform.position += new Vector3(side * (inner - edge), 0f, 0f);
            return b.size.z;
        }

        /// <summary>Random pieces from `names` along both sides of the lane, one every `step` (each side), between |x| xMin and xMax.</summary>
        static void Scatter(LandKit K, string[] names, float z0, float z1, float step, float xMin, float xMax, float sMin, float sMax, int perSide = 1, int onlySide = 0)
        {
            for (float z = z0; z < z1; z += step)
                for (int side = -1; side <= 1; side += 2)
                    if (onlySide == 0 || side == onlySide) for (int c = 0; c < perSide; c++)
                        Put(K, K.Pick(names), side * K.R(xMin, xMax), z + K.R(0f, step), K.R(sMin, sMax), K.R(0f, 360f));
        }

        /// <summary>A set of a diorama's pieces moved together, keeping where the author stood them relative to each other.</summary>
        static void PutGroup(LandKit K, string location, string[] names, float x, float z, float s, float yaw)
        {
            if (!K.dioramas.TryGetValue(location, out var d)) return;
            var found = new List<Piece>();
            foreach (var p in LandPieces(d)) foreach (var nm in names) if (BaseName(p.name) == nm) found.Add(p);
            if (found.Count == 0) return;
            var gb = found[0].b; foreach (var p in found) gb.Encapsulate(p.b);
            var q = Quaternion.Euler(0f, yaw, 0f);
            foreach (var p in found)
            {
                var h = ClonePieceTo(p, K.root, "Prop" + K.n++ + "_" + p.name);
                Vector3 off = new Vector3(p.b.center.x - gb.center.x, p.b.min.y - gb.min.y, p.b.center.z - gb.center.z) * s;
                h.transform.position = new Vector3(x, SeaLevel - 0.03f, z) + q * off;
                h.transform.rotation = q; h.transform.localScale = Vector3.one * s;
                Placed(K, h);
            }
        }

        /// <summary>A land world's scenery and its gate (any but the two islands). The scrolling props go to `sc`; returns the gate's half-width.</summary>
        static void ComposeLand(LandTheme t, Transform root, System.Random rnd, Mats M, WorldScroller sc)
        {
            var K = OpenLandKit(t.location, root, rnd, M);
            switch (t.id)
            {
                case "autumn": AutumnLayout(K); break;
                case "camping": CampingLayout(K); break;
                case "christmas": ChristmasLayout(K); break;
                case "desert": DesertLayout(K); break;
                case "city": CityLayout(K); break;
                case "west": WestLayout(K); break;
                default: Debug.LogWarning("[SkySquad] no layout for land world " + t.id); break;
            }
            float clear = BuildGate(t.id, root, M, K);
            CloseLandKit(K);
            LandScroll(sc, K, clear);
        }

        static void LandScroll(WorldScroller sc, LandKit K, float clear)
        {
            sc.buoys.AddRange(K.moving);
            sc.loopLength = LandLoop; sc.recycleBehind = LandLoopFrom; sc.recycleAhead = LandLoopFrom + LandLoop;
            sc.gateZ = GateZ; sc.gateClearX = clear;
        }

        const float Z0 = LandLoopFrom + 2f, Z1 = LandLoopFrom + LandLoop;   // the strip the scenery fills

        // ------------------------------------------------------------------ AUTUMN FOREST: a corridor through a dense wood, great trees arching over the path
        static void AutumnLayout(LandKit K)
        {
            string[] broad = { "autumn tree", "autumn tree 2", "autumn tree 3", "autumn tree 4", "autumn tree 5" };
            string[] tall = { "autumn pine tree medium", "autumn pine tree small", "pine tree large", "fir tree medium" };
            string[] low = { "autumn shrub", "autumn shrub 2", "autumn bush plant", "autumn bush plant 2", "autumn bush plant 3", "grass yellow", "grass yellow 2", "grass yellow 3", "plants yellow", "grass brown 3" };
            Scatter(K, broad, Z0, Z1, 3.6f, 7.5f, 12f, 1.3f, 1.8f, 1);          // the wall of the wood right at the path
            Scatter(K, tall, Z0, Z1, 4.6f, 9f, 14f, 1.3f, 1.7f, 1);
            Scatter(K, broad, Z0, Z1, 4.4f, 13f, 26f, 1.5f, 2.1f, 1);           // and deeper in
            Scatter(K, tall, Z0, Z1, 5f, 22f, 40f, 1.6f, 2.2f, 1);
            Scatter(K, low, Z0, Z1, 2.2f, 4.6f, 7.5f, 1.2f, 1.8f, 1);            // the undergrowth along the path
            for (float z = 40f; z < Z1; z += 58f)
            {   // two great trees leaning in from either side, their crowns reaching over the path
                var a = Put(K, "autumn tree 5", -11f, z, 1.9f, 20f); if (a != null) a.transform.rotation = Quaternion.Euler(0f, 20f, -9f);
                var b = Put(K, "autumn tree 4", 11f, z + 3f, 2.0f, 200f); if (b != null) b.transform.rotation = Quaternion.Euler(0f, 200f, 9f);
            }
            for (float z = 0f; z < Z1; z += 23f) { int side = ((int)z / 23) % 2 == 0 ? -1 : 1; Put(K, "tree trunk", side * K.R(5.5f, 8f), z + K.R(0f, 6f), 1.8f, K.R(-30f, 30f)); }   // fallen logs
            for (float z = 4f; z < Z1; z += 17f) Put(K, K.Pick("desert stone small", "desert stone small 3", "desert stone small 5", "desert stone small 7"), (K.rnd.Next(2) * 2 - 1) * K.R(5.5f, 9f), z, K.R(0.9f, 1.4f), K.R(0f, 360f));
        }

        // ------------------------------------------------------------------ CAMPING FOREST: camps by their fires in a dark fir wood, lanterns strung over the trail
        static void CampingLayout(LandKit K)
        {
            string[] firs = { "fir tree large", "fir tree medium", "fir tree tilted", "fir tree bent", "fir tree small", "pine tree large" };
            Scatter(K, firs, Z0, Z1, 4.2f, 13f, 20f, 1.5f, 2.0f, 1);
            Scatter(K, firs, Z0, Z1, 4.6f, 19f, 38f, 1.6f, 2.2f, 1);
            Scatter(K, new[] { "fir tree small", "dry tree", "dry tree 2" }, Z0, Z1, 9f, 6.5f, 9f, 1.2f, 1.6f, 1);
            Scatter(K, new[] { "mushroom brown", "mushroom brown 2", "mushroom brown 3" }, Z0, Z1, 3.4f, 4.8f, 7f, 2.2f, 3.2f, 1);
            Scatter(K, new[] { "stone small", "stone small 3" }, Z0, Z1, 12f, 5.5f, 8f, 1.0f, 1.4f, 1);
            var add = GAdd("camping", "CampFire", new Color(1f, 0.6f, 0.2f, 0.9f));
            var fire = new Color(1f, 0.55f, 0.2f);
            string[] tents = { "camping tent red", "camping tent blue", "camping tent yellow" };
            int c = 0;
            for (float z = 20f; z < Z1 - 20f; z += 50f, c++)
            {   // a camp: a tent or two round a fire that crackles and smokes
                int side = c % 2 == 0 ? -1 : 1;
                Group(K, "Camp" + c, new Vector3(side * 8f, SeaLevel, z));
                Put(K, tents[c % 3], side * 10f, z - 3f, 1.4f, side * -80f);
                if (c % 2 == 1) Put(K, tents[(c + 1) % 3], side * 12.5f, z + 5f, 1.4f, side * -110f);
                Put(K, "bonfire", side * 6.6f, z + 1f, 2f);
                Put(K, "tree trunk", side * 7.6f, z + 3.6f, 1.4f, 80f); Put(K, "tree trunk 2", side * 8.6f, z - 0.8f, 1.4f, 10f);
                Fire(K.parent, new Vector3(side * 6.6f, SeaLevel + 0.6f, z + 1f), 0.9f, add);
                Smoke(K.parent, new Vector3(side * 6.6f, SeaLevel + 2f, z + 1f), 1.2f, 14f, new Color(0.35f, 0.35f, 0.4f, 0.35f), 3f);
                GLight(K.parent, new Vector3(side * 6.6f, SeaLevel + 1.4f, z + 1f), fire, 11f, 3f, true);
                EndGroup(K);
            }
            var lantern = GGlow("camping", "Lantern", new Color(3f, 1.8f, 0.6f));
            var rope = GLit("camping", "Rope", new Color(0.25f, 0.18f, 0.1f));
            for (float z = 45f; z < Z1; z += 100f)
            {   // a string of lanterns across the trail, swaying
                var g = Group(K, "Lanterns", new Vector3(0f, SeaLevel + 11f, z));
                GBox(g, "Rope", new Vector3(0f, SeaLevel + 11f, z), new Vector3(22f, 0.12f, 0.12f), rope, default(Vector3), false);
                for (int i = 0; i < 7; i++)
                {
                    var l = GBox(g, "Lantern", new Vector3(-9f + i * 3f, SeaLevel + 10.1f - Mathf.Sin(i / 6f * Mathf.PI) * 1.2f, z), new Vector3(0.6f, 0.9f, 0.6f), lantern, default(Vector3), false);
                    var hv = l.AddComponent<Hover>(); hv.height = 0.08f; hv.speed = 0.6f; hv.sway = 6f;
                }
                EndGroup(K);
            }
        }

        // ------------------------------------------------------------------ CHRISTMAS VILLAGE: a snowy street of wooden houses under arches of lights
        static void ChristmasLayout(LandKit K)
        {
            string[] houses = { "wooden winter house", "wooden winter house 2", "wooden winter house 3" };
            for (int side = -1; side <= 1; side += 2)
            {
                float z = side < 0 ? Z0 : Z0 + 6f;
                while (z < Z1 - 6f)
                {
                    var h = Put(K, K.Pick(houses), side * 14f, z, 1.5f, side > 0 ? -90f : 90f);
                    float depth = Flank(h, side, 9f);
                    if (h != null) h.transform.position += new Vector3(0f, 0f, depth * 0.5f);
                    Put(K, "christmas tree", side * K.R(8.8f, 9.6f), z + depth + 1.6f, K.R(1.2f, 1.5f), K.R(0f, 360f));
                    z += depth + 4.5f;
                }
            }
            for (float z = Z0; z < Z1; z += 8f)   // posts along both kerbs, garlands strung between them
                for (int side = -1; side <= 1; side += 2)
                {
                    Put(K, "wooden post", side * 6.8f, z, 1.5f);
                    Put(K, "garland", side * 6.8f, z + 4f, 1.15f, 90f, 3.6f);
                }
            Scatter(K, new[] { "fir tree winter large", "fir tree winter medium", "fir tree winter tilted", "fir tree winter bent" }, Z0, Z1, 5f, 22f, 38f, 1.5f, 2.0f, 1);
            Scatter(K, new[] { "fir tree winter small", "fir tree winter small", "snowman" }, Z0, Z1, 9f, 4.8f, 6.0f, 1.0f, 1.3f, 1);
            // arches of lights over the street, their bulbs taking turns
            var frame = GLit("christmas", "Arch", new Color(0.9f, 0.92f, 0.95f), 0.5f);
            var bulbA = GGlow("christmas", "BulbA", new Color(3f, 0.5f, 0.4f)); var bulbB = GGlow("christmas", "BulbB", new Color(0.6f, 2.6f, 0.8f)); var bulbC = GGlow("christmas", "BulbC", new Color(3f, 2.4f, 0.8f));
            for (float z = 30f; z < Z1; z += 60f)
            {
                var g = Group(K, "LightArch", new Vector3(0f, SeaLevel, z));
                var setA = new GameObject("A"); setA.transform.SetParent(g, false); var setB = new GameObject("B"); setB.transform.SetParent(g, false);
                const int segs = 14; float rad = 8.6f, cy = SeaLevel + 6f;
                for (int i = 0; i <= segs; i++)
                {
                    float a = i / (float)segs * Mathf.PI; var p = new Vector3(-Mathf.Cos(a) * rad, cy + Mathf.Sin(a) * rad, z);
                    if (i < segs) { float a2 = (i + 1) / (float)segs * Mathf.PI; var p2 = new Vector3(-Mathf.Cos(a2) * rad, cy + Mathf.Sin(a2) * rad, z); GBox(g, "Seg", (p + p2) * 0.5f, new Vector3(0.25f, (p2 - p).magnitude + 0.1f, 0.25f), frame, new Vector3(0f, 0f, Mathf.Atan2(p2.y - p.y, p2.x - p.x) * Mathf.Rad2Deg - 90f), false); }
                    GBox(i % 2 == 0 ? setA.transform : setB.transform, "Bulb", p + Vector3.back * 0.2f, Vector3.one * 0.45f, i % 3 == 0 ? bulbA : i % 3 == 1 ? bulbB : bulbC, default(Vector3), false);
                }
                foreach (int s in new[] { -1, 1 }) GBox(g, "Leg", new Vector3(s * rad, SeaLevel + 3f, z), new Vector3(0.3f, 6f, 0.3f), frame, default(Vector3), false);
                var bl = g.gameObject.AddComponent<Blink>(); bl.lamps = new[] { setA, setB }; bl.seconds = new[] { 0.5f };
                EndGroup(K);
            }
        }

        // ------------------------------------------------------------------ DESERT PYRAMIDS: open dunes, pyramids and the sphinx passing, an oasis of palms
        static void DesertLayout(LandKit K)
        {
            Put(K, "pyramid 2", -32f, 88f, 1.7f, 12f); Put(K, "pyramid", 28f, 60f, 1.8f, -8f); Put(K, "pyramid", -24f, 180f, 1.5f, 30f); Put(K, "pyramid 2", 34f, 230f, 1.5f, 0f);
            Put(K, "sphinx", 13f, 120f, 1.5f, 180f); Put(K, "sphinx", -13f, 20f, 1.3f, 180f);
            for (float z = 40f; z < Z1; z += 110f)
            {   // an oasis of palms
                int side = ((int)z / 110) % 2 == 0 ? -1 : 1;
                Put(K, "palm tree large", side * 10f, z, 1.5f, 20f); Put(K, "palm tree bent", side * 13.5f, z + 5f, 1.5f, 160f); Put(K, "palm tree small", side * 8f, z + 6f, 1.6f, 70f); Put(K, "palm tree tilted", side * 12f, z - 4f, 1.5f, 260f);
                Scatter(K, new[] { "grass", "grass 2", "grass 3" }, z - 6f, z + 10f, 2.5f, 6f, 12f, 1.6f, 2.2f, 1, side);
            }
            Scatter(K, new[] { "cactus", "cactus 2", "cactus 4", "cactus 5", "cactus 6" }, Z0, Z1, 9f, 6f, 22f, 1.4f, 1.9f, 1);
            Scatter(K, new[] { "desert stone small 8", "desert stone small 9", "desert stone small 10", "desert stone small 11", "stone small 5", "stone small 6" }, Z0, Z1, 7f, 5f, 20f, 1.2f, 2.0f, 1);
            var sand = GLit("desert", "Sandstone", new Color(0.86f, 0.7f, 0.46f)); var gold = GLit("desert", "Gold", new Color(1f, 0.78f, 0.25f), 0.7f);
            for (float z = 70f; z < Z1; z += 75f)
                foreach (int s in new[] { -1, 1 })
                {   // obelisks in pairs along the way
                    var g = Group(K, "Obelisk", new Vector3(s * 8.5f, SeaLevel, z));
                    GBox(g, "Shaft", new Vector3(s * 8.5f, SeaLevel + 6f, z), new Vector3(1.4f, 12f, 1.4f), sand, default(Vector3), false);
                    GBox(g, "Tip", new Vector3(s * 8.5f, SeaLevel + 12.3f, z), new Vector3(1f, 1f, 1f), gold, new Vector3(45f, 0f, 45f), false);
                    EndGroup(K);
                }
        }

        // ------------------------------------------------------------------ DOWNTOWN: a ruined city - gutted towers, burnt cars, smoke rising from the rubble
        static void CityLayout(LandKit K)
        {
            var rnd = new System.Random(31);
            var tex = RuinWindowTexture();
            var walls = GTex("city", "RuinStreet", tex, new Vector2(1f, 2f), Color.white, 1.4f);
            var concrete = GLit("city", "Concrete", new Color(0.42f, 0.41f, 0.4f));
            var steel = GLit("city", "Steel", new Color(0.22f, 0.2f, 0.19f), 0.4f);
            var burnt = GLit("city", "Burnt", new Color(0.12f, 0.1f, 0.09f), 0.3f);
            var add = GAdd("city", "Fire", new Color(1f, 0.6f, 0.2f, 0.9f));
            string[] towers = { "building", "building 2", "building 3", "building 4" };
            int lights = 0;
            for (int side = -1; side <= 1; side += 2)
            {
                float z = side < 0 ? Z0 : Z0 + 7f; int k = 0;
                while (z < Z1 - 8f)
                {
                    if (k++ % 3 != 1)
                    {   // a gutted tower, some still burning
                        float w = 10f + (float)rnd.NextDouble() * 6f, d = 10f + (float)rnd.NextDouble() * 6f, h = 16f + (float)rnd.NextDouble() * 26f;
                        var g = Group(K, "Ruin", new Vector3(side * (9.6f + w * 0.5f), SeaLevel, z + d * 0.5f));
                        RuinTower(g, "Tower", new Vector3(side * (9.6f + w * 0.5f), SeaLevel, z + d * 0.5f), new Vector3(w, h, d), walls, concrete, steel, rnd, side * (float)rnd.NextDouble() * 3f);
                        if (rnd.NextDouble() < 0.45)
                        {
                            var top = new Vector3(side * (9.6f + w * 0.4f), SeaLevel + h - 2f, z + d * 0.3f);
                            Fire(g, top, 1.8f, add); Smoke(g, top + Vector3.up * 2f, 2.6f, 34f, new Color(0.16f, 0.15f, 0.15f, 0.5f), 4f);
                            if (lights++ < 4) GLight(g, top + new Vector3(-side * 3f, 0f, -2f), new Color(1f, 0.55f, 0.2f), 16f, 2.2f, true);
                        }
                        EndGroup(K);
                        z += d + 1.5f;
                    }
                    else
                    {   // one still standing, scorched
                        var b = Put(K, K.Pick(towers), side * 16f, z, K.R(0.9f, 1.1f), side > 0 ? -90f : 90f);
                        float depth = Flank(b, side, 9.6f);
                        if (b != null) b.transform.position += new Vector3(0f, 0f, depth * 0.5f);
                        z += depth + 1.5f;
                    }
                }
            }
            string[] cars = { "car SUV large yellow", "sedan car brown", "car SUVs pickups lights red" };
            for (float z = 8f; z < Z1; z += 19f)
            {   // burnt-out cars along the kerb, some still smoking
                int side = K.rnd.Next(2) * 2 - 1;
                var car = Put(K, K.Pick(cars), side * 6.0f, z + K.R(0f, 6f), 1.4f, K.R(-25f, 25f) + K.rnd.Next(2) * 180f);
                if (car != null) foreach (var r in car.GetComponentsInChildren<Renderer>()) { var ms = r.sharedMaterials; for (int i = 0; i < ms.Length; i++) ms[i] = burnt; r.sharedMaterials = ms; }
                if (car != null && K.rnd.NextDouble() < 0.4) Smoke(car.transform, car.transform.position + Vector3.up * 2f, 1.2f, 16f, new Color(0.2f, 0.19f, 0.19f, 0.4f), 3f);
            }
            for (float z = 2f; z < Z1; z += 14f)
            {   // the street's lamps, bent; rubble heaped at the kerbs
                int side = K.rnd.Next(2) * 2 - 1;
                var lamp = Put(K, "lamppost", side * 8.1f, z, 1.5f, side > 0 ? -90f : 90f); if (lamp != null) lamp.transform.rotation = Quaternion.Euler(0f, side > 0 ? -90f : 90f, K.R(-25f, 25f));
                var heap = Group(K, "Rubble", new Vector3(-side * 7.5f, SeaLevel, z + 7f));
                for (int i = 0; i < 5; i++) { float s = K.R(0.6f, 1.6f); GBox(heap, "Chunk", new Vector3(-side * K.R(6.5f, 8.5f), SeaLevel + s * 0.3f, z + 7f + K.R(-1.5f, 1.5f)), new Vector3(s, s * 0.7f, s), concrete, new Vector3(K.R(0f, 40f), K.R(0f, 360f), K.R(0f, 40f)), false); }
                EndGroup(K);
            }
            Ambient(K.root, "Ash", new Vector3(0f, SeaLevel + 14f, 70f), new Vector3(50f, 20f, 160f), 30f, new Vector2(6f, 10f), new Vector3(-0.5f, -0.8f, -1f), new Vector3(0.5f, -0.2f, 0.3f), new Vector2(0.08f, 0.16f), new Color(0.75f, 0.72f, 0.7f, 0.8f), new Color(0.5f, 0.48f, 0.46f, 0.8f), AlphaParticle(), 0.8f, 0f, 500);
        }

        // ------------------------------------------------------------------ the pitch ground (the soccer field was removed 2026-10-11; GroundKind.Pitch still reads these)
        const float PitchHalfW = 18f, PitchLen = 100f, PitchNear = -2f;   // the pitch the ground texture paints: touchlines at |x| 18, goal lines every 100 from z -2

        // ------------------------------------------------------------------ WILD WEST: a train running on the rails at the left, the town on the right, tumbleweeds blowing across
        static void WestLayout(LandKit K)
        {
            const float rail = -11f;
            for (float z = Z0; z < Z1 + 30f; z += 44.9f) Put(K, "railway", rail, z + 22.5f, 1f);
            // the train: engine and two wagons coupled as one, running down the line toward the squad (faster than the ground)
            var train = Group(K, "Train", new Vector3(rail, SeaLevel, 60f));
            Put(K, "train", rail, 46f, 1.0f, 90f); Put(K, "passenger wagon", rail, 60f, 1.0f, 90f); Put(K, "freight wagon black", rail, 73.5f, 1.0f, 90f);
            Smoke(train, new Vector3(rail, SeaLevel + 6.5f, 41.5f), 0.9f, 12f, new Color(0.35f, 0.33f, 0.32f, 0.5f), 10f);
            EndGroup(K);
            var cr = train.gameObject.AddComponent<Cruise>(); cr.velocity = new Vector3(0f, 0f, -7f);
            Put(K, "railway station", -23f, 120f, 1.1f, 90f);
            Put(K, "water tank", -18f, 26f, 1.2f, 0f); Put(K, "water tank", -18f, 200f, 1.2f, 0f);
            Put(K, "coal", -17f, 160f, 1.2f, 0f);
            Put(K, "information post", -7.5f, 22f, 1.5f, 90f);
            for (float z = Z0; z < Z1; z += 18f) Put(K, "electric pole", -15f, z, 1.4f, 90f);
            string[] horses = { "horse black", "horse brown", "horse silver", "horse white" };
            for (float z = 18f; z < Z1; z += 32f)
            {
                Put(K, "hitching post", 7.5f, z, 1.6f, 90f);
                Put(K, horses[K.rnd.Next(4)], 9f, z - 1.2f, 1.5f, -90f); Put(K, horses[K.rnd.Next(4)], 9.2f, z + 1.4f, 1.5f, -80f);
            }
            Put(K, "cart", 11f, 32f, 1.4f, 10f); Put(K, "cart", 13f, 150f, 1.4f, -20f);
            Scatter(K, new[] { "barrel 2", "box 2", "bench 2" }, Z0, Z1, 14f, 6.5f, 8f, 1.1f, 1.4f, 1);
            Scatter(K, new[] { "cactus", "cactus 2", "cactus 3", "cactus 4", "cactus 5", "cactus 6" }, Z0, Z1, 4f, 12f, 28f, 1.5f, 2.0f, 1, 1);
            Scatter(K, new[] { "grass brown", "grass brown 2", "grass brown 3" }, Z0, Z1, 3f, 5f, 8f, 1.4f, 2.0f, 1);
            Put(K, "stone large brown", 30f, 82f, 1.5f, 0f); Put(K, "stone large brown 2", 24f, 230f, 1.4f, 70f); Put(K, "stone large brown 2", -36f, 250f, 1.5f, 200f);
            var timber = GLit("west", "Timber", new Color(0.38f, 0.24f, 0.13f));
            for (float z = 30f; z < Z1; z += 140f)
            {   // the town's arch over the road, its sign swinging
                var g = Group(K, "TownArch", new Vector3(0f, SeaLevel, z));
                foreach (int s in new[] { -1, 1 }) GBox(g, "Post", new Vector3(s * 8.5f, SeaLevel + 7f, z), new Vector3(0.8f, 14f, 0.8f), timber, default(Vector3), false);
                GBox(g, "Beam", new Vector3(0f, SeaLevel + 13.6f, z), new Vector3(19f, 0.9f, 0.9f), timber, default(Vector3), false);
                var sign = new GameObject("Sign"); sign.transform.SetParent(g, false); sign.transform.position = new Vector3(0f, SeaLevel + 13f, z);
                GBox(sign.transform, "Board", new Vector3(0f, SeaLevel + 11.6f, z), new Vector3(9f, 2.2f, 0.25f), timber, default(Vector3), false);
                var txt = Label3D("Text", sign.transform, Vector3.zero, 18f, new Color(1f, 0.88f, 0.6f), fontOutline); txt.transform.position = new Vector3(0f, SeaLevel + 11.6f, z - 0.2f); txt.text = "DUST CREEK";
                var hv = sign.AddComponent<Hover>(); hv.height = 0f; hv.speed = 0.35f; hv.sway = 4f;
                EndGroup(K);
            }
            // a windmill pumping by the road, and tumbleweeds blowing across it
            var wm = Group(K, "Windmill", new Vector3(17f, SeaLevel, 100f));
            var iron = GLit("west", "Iron", new Color(0.3f, 0.29f, 0.28f), 0.4f);
            foreach (int a in new[] { -1, 1 }) foreach (int b in new[] { -1, 1 }) GBox(wm, "Leg", new Vector3(17f + a * 1.2f, SeaLevel + 6f, 100f + b * 1.2f), new Vector3(0.25f, 12.2f, 0.25f), iron, new Vector3(b * 5f, 0f, -a * 5f), false);
            var hub = new GameObject("Wheel"); hub.transform.SetParent(wm, false); hub.transform.position = new Vector3(17f, SeaLevel + 12.6f, 99f);
            for (int i = 0; i < 12; i++) { var bl = GBox(hub.transform, "Blade", hub.transform.position, new Vector3(0.6f, 3.2f, 0.08f), timber, default(Vector3), false); bl.transform.localRotation = Quaternion.Euler(0f, 0f, i * 30f); bl.transform.localPosition = bl.transform.localRotation * new Vector3(0f, 1.9f, 0f); }
            GBox(wm, "Tail", new Vector3(17f, SeaLevel + 12.6f, 101.8f), new Vector3(0.1f, 1.6f, 3f), timber, default(Vector3), false);
            hub.AddComponent<Spin>().degreesPerSecond = 70f;
            EndGroup(K);
            var weed = GLit("west", "Tumbleweed", new Color(0.55f, 0.42f, 0.25f));
            for (int i = 0; i < 3; i++)
            {
                var tw = new GameObject("Tumbleweed"); tw.transform.SetParent(K.root, false); tw.transform.position = new Vector3(-26f, SeaLevel + 0.9f, 24f + i * 26f);
                var vis = new GameObject("Ball"); vis.transform.SetParent(tw.transform, false); vis.transform.position = tw.transform.position;
                for (int k = 0; k < 9; k++) GBox(vis.transform, "Twig", tw.transform.position, new Vector3(0.08f, 1.8f, 0.08f), weed, new Vector3(K.R(0f, 180f), K.R(0f, 180f), K.R(0f, 180f)), false);
                GPrim(vis.transform, PrimitiveType.Sphere, "Core", tw.transform.position, Vector3.one * 1.1f, weed);
                var ro = tw.AddComponent<Roller>(); ro.visual = vis.transform; ro.speed = 6f + i * 1.5f; ro.radius = 0.9f; ro.restMin = 2f + i; ro.restMax = 7f + i * 2f;
                K.moving.Add(tw.transform);   // it drifts back with the ground as it rolls across
            }
        }
    }
}
