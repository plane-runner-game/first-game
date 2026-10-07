// SceneBuilder.LandLayouts.cs (Editor only)
// The eight land locations as fixed scenes (2026-10-07: "the ground and the background fixed, nothing moving; a ground that has nothing to do
// with the sea; every one a different design, not all alike"). Until then every land world was the same random scatter of its diorama's pieces
// scrolling past. Now each one is laid out once, by hand, and stands still: a forest corridor, a night camp, a village street, open dunes under
// the pyramids, a city canyon, a stadium, a launch pad and a railway town. Pieces come from any of the pack's dioramas (placed as the author
// stood them: rockets upright, logs lying) or, failing that, from the pack's own prefabs. Everything sits inside the camera's wedge: the view
// is narrow (portrait, fov 52, camera at z -11), about 0.27 x (z + 11) to either side of the lane.
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
            public Transform root; public System.Random rnd;
            public readonly Dictionary<string, Piece> pieces = new Dictionary<string, Piece>();
            public readonly Dictionary<string, string> prefabs = new Dictionary<string, string>();
            public readonly Dictionary<string, GameObject> dioramas = new Dictionary<string, GameObject>();
            public int n;
            public float R(float a, float b) { return a + (b - a) * (float)rnd.NextDouble(); }
            public string Pick(params string[] a) { return a[rnd.Next(a.Length)]; }
        }

        static string BaseName(string n) { return Regex.Replace(n, @"\s*\(\d+\)$", "").Trim().ToLowerInvariant(); }

        static LandKit OpenLandKit(LandTheme t, Transform root, System.Random rnd)
        {
            var K = new LandKit { root = root, rnd = rnd };
            foreach (var g in AssetDatabase.FindAssets("t:Prefab", new[] { AtmoDir + "Prefabs" }))
            {
                var p = AssetDatabase.GUIDToAssetPath(g); if (p.Contains("Prefabs/Location")) continue;
                var nm = System.IO.Path.GetFileNameWithoutExtension(p).ToLowerInvariant(); if (!K.prefabs.ContainsKey(nm)) K.prefabs[nm] = p;
            }
            var order = new List<string> { t.location }; foreach (var l in LandLocationNames) if (l != t.location) order.Add(l);   // the world's own diorama wins a name
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
            foreach (var r in holder.GetComponentsInChildren<Renderer>(true)) { r.shadowCastingMode = ShadowCastingMode.On; r.receiveShadows = true; }   // it stands still now: it may as well anchor itself with a shadow
            return holder;
        }

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
                foreach (var r in h.GetComponentsInChildren<Renderer>(true)) { r.shadowCastingMode = ShadowCastingMode.On; r.receiveShadows = true; }
            }
        }

        static void WarmLight(Transform root, Vector3 p, Color c, float range, float intensity)
        {
            var go = new GameObject("Glow"); go.transform.SetParent(root, false); go.transform.position = p;
            var l = go.AddComponent<Light>(); l.type = LightType.Point; l.color = c; l.range = range; l.intensity = intensity; l.shadows = LightShadows.None;
        }

        /// <summary>The fixed scene of a land world (any but the two islands).</summary>
        static void ComposeLand(LandTheme t, Transform root, System.Random rnd)
        {
            var K = OpenLandKit(t, root, rnd);
            switch (t.id)
            {
                case "autumn": AutumnLayout(K); break;
                case "camping": CampingLayout(K); break;
                case "christmas": ChristmasLayout(K); break;
                case "desert": DesertLayout(K); break;
                case "city": CityLayout(K); break;
                case "soccer": SoccerLayout(K); break;
                case "shuttle": LaunchLayout(K); break;
                case "west": WestLayout(K); break;
                default: Debug.LogWarning("[SkySquad] no layout for land world " + t.id); break;
            }
            CloseLandKit(K);
        }

        // ------------------------------------------------------------------ AUTUMN FOREST: a corridor through a dense wood of orange and gold
        static void AutumnLayout(LandKit K)
        {
            string[] broad = { "autumn tree", "autumn tree 2", "autumn tree 3", "autumn tree 4", "autumn tree 5" };
            string[] tall = { "autumn pine tree medium", "autumn pine tree small", "pine tree large", "fir tree medium" };
            string[] low = { "autumn shrub", "autumn shrub 2", "autumn bush plant", "autumn bush plant 2", "autumn bush plant 3", "grass yellow", "grass yellow 2", "grass yellow 3", "plants yellow", "grass brown 3" };
            Scatter(K, broad, 2f, 100f, 3.4f, 7.5f, 12f, 1.3f, 1.8f, 1);          // the wall of the wood right at the path
            Scatter(K, tall, 6f, 100f, 4.2f, 9f, 14f, 1.3f, 1.7f, 1);
            Scatter(K, broad, 20f, 100f, 3.6f, 13f, 24f, 1.5f, 2.1f, 2);          // and deeper in
            Scatter(K, tall, 40f, 100f, 3.6f, 20f, 34f, 1.6f, 2.2f, 2);
            Scatter(K, low, 0f, 100f, 2.0f, 4.6f, 7.5f, 1.2f, 1.8f, 1);           // the undergrowth along the path
            for (int i = 0; i < 7; i++) { int side = i % 2 == 0 ? -1 : 1; Put(K, "tree trunk", side * K.R(5.5f, 8f), 8f + i * 13f + K.R(0f, 5f), 1.8f, K.R(-30f, 30f)); }   // fallen logs
            for (int i = 0; i < 8; i++) { int side = i % 2 == 0 ? 1 : -1; Put(K, K.Pick("desert stone small", "desert stone small 3", "desert stone small 5", "desert stone small 7"), side * K.R(5.5f, 9f), 4f + i * 12f, K.R(0.9f, 1.4f), K.R(0f, 360f)); }
        }

        // ------------------------------------------------------------------ CAMPING FOREST: three camps by their fires in a dark fir wood
        static void CampingLayout(LandKit K)
        {
            string[] firs = { "fir tree large", "fir tree medium", "fir tree tilted", "fir tree bent", "fir tree small", "pine tree large" };
            Scatter(K, firs, 4f, 100f, 3.8f, 13f, 20f, 1.5f, 2.0f, 1);
            Scatter(K, firs, 30f, 100f, 3.4f, 19f, 34f, 1.6f, 2.2f, 2);
            Scatter(K, new[] { "fir tree small", "dry tree", "dry tree 2" }, 2f, 100f, 9f, 6.5f, 9f, 1.2f, 1.6f, 1);
            Scatter(K, new[] { "mushroom brown", "mushroom brown 2", "mushroom brown 3" }, 0f, 100f, 3.2f, 4.8f, 7f, 2.2f, 3.2f, 1);
            Scatter(K, new[] { "stone small", "stone small 3" }, 6f, 100f, 11f, 5.5f, 8f, 1.0f, 1.4f, 1);
            Color fire = new Color(1f, 0.55f, 0.2f);
            // camp 1, left: one red tent at the fire
            Put(K, "camping tent red", -9.5f, 24f, 1.4f, 70f); Put(K, "bonfire", -6.2f, 29f, 1.8f); Put(K, "tree trunk", -6.5f, 32f, 1.4f, 80f); Put(K, "tree trunk 2", -8.6f, 29.5f, 1.4f, 10f);
            WarmLight(K.root, new Vector3(-6.2f, SeaLevel + 1.2f, 29f), fire, 10f, 3f);
            // camp 2, right: blue and yellow tents round a bigger fire
            Put(K, "camping tent blue", 10f, 46f, 1.4f, -80f); Put(K, "camping tent yellow", 12f, 55f, 1.4f, -110f); Put(K, "bonfire", 7f, 50f, 2.2f);
            Put(K, "tree trunk", 8.5f, 47f, 1.4f, 30f); Put(K, "cauldron", 6.4f, 53f, 2f);
            WarmLight(K.root, new Vector3(7f, SeaLevel + 1.2f, 50f), fire, 12f, 3.2f);
            // camp 3, left again, further: yellow tent and a pennant line
            Put(K, "camping tent yellow", -12f, 74f, 1.5f, 100f); Put(K, "camping tent red", -15f, 84f, 1.5f, 120f); Put(K, "bonfire", -8f, 79f, 2.2f); Put(K, "wooden pendant", -10f, 70f, 1.6f, 90f);
            WarmLight(K.root, new Vector3(-8f, SeaLevel + 1.2f, 79f), fire, 12f, 3.2f);
            Put(K, "wooden bridge", 15f, 92f, 1.4f, 90f);   // over a dry gully on the right, far
        }

        // ------------------------------------------------------------------ CHRISTMAS VILLAGE: a snowy street of wooden houses strung with garlands
        static void ChristmasLayout(LandKit K)
        {
            string[] houses = { "wooden winter house", "wooden winter house 2", "wooden winter house 3" };
            for (int side = -1; side <= 1; side += 2)
            {
                float z = side < 0 ? 6f : 12f;
                while (z < 100f)
                {
                    if (side > 0 && z > 46f && z < 66f) { z = 66f; continue; }   // the village square on the right
                    var h = Put(K, K.Pick(houses), side * 14f, z, 1.5f, side > 0 ? -90f : 90f);
                    float depth = Flank(h, side, 9f);
                    if (h != null) h.transform.position += new Vector3(0f, 0f, depth * 0.5f);
                    Put(K, "christmas tree", side * K.R(8.8f, 9.6f), z + depth + 1.6f, K.R(1.2f, 1.5f), K.R(0f, 360f));
                    z += depth + 4.5f;
                }
            }
            for (float z = 4f; z < 100f; z += 8f)   // lamp posts along both kerbs, garlands strung between them
                for (int side = -1; side <= 1; side += 2)
                {
                    Put(K, "wooden post", side * 6.8f, z, 1.5f);
                    if (z + 8f < 100f) Put(K, "garland", side * 6.8f, z + 4f, 1.15f, 90f, 3.6f);
                }
            Put(K, "winter well", 12f, 56f, 1.5f, -90f); Put(K, "christmas tree", 15f, 62f, 2.4f); Put(K, "snowman", 9f, 52f, 1.6f, -120f); Put(K, "snowman", 10f, 60f, 1.4f, -60f);
            Put(K, "stones group winter", 19f, 50f, 1.0f, 0f);
            Scatter(K, new[] { "fir tree winter large", "fir tree winter medium", "fir tree winter tilted", "fir tree winter bent" }, 30f, 100f, 4f, 22f, 36f, 1.5f, 2.0f, 2);
            Scatter(K, new[] { "fir tree winter small", "fir tree winter small", "snowman" }, 2f, 100f, 9f, 4.8f, 6.0f, 1.0f, 1.3f, 1);
        }

        // ------------------------------------------------------------------ DESERT PYRAMIDS: open dunes, the pyramids on the horizon, the sphinx, an oasis of palms
        static void DesertLayout(LandKit K)
        {
            Put(K, "pyramid 2", -30f, 88f, 1.7f, 12f);
            Put(K, "pyramid", 27f, 80f, 1.8f, -8f);
            Put(K, "pyramid", -14f, 104f, 1.3f, 30f);
            Put(K, "pyramid 2", 40f, 104f, 1.2f, 0f);
            Put(K, "sphinx", 13f, 44f, 1.5f, 180f);
            Put(K, "sphinx", -13f, 64f, 1.3f, 180f);
            // the oasis, left
            Put(K, "palm tree large", -10f, 24f, 1.5f, 20f); Put(K, "palm tree bent", -13.5f, 29f, 1.5f, 160f); Put(K, "palm tree small", -8f, 30f, 1.6f, 70f); Put(K, "palm tree tilted", -12f, 20f, 1.5f, 260f);
            Scatter(K, new[] { "grass", "grass 2", "grass 3" }, 18f, 34f, 2.5f, 6f, 12f, 1.6f, 2.2f, 1);
            Put(K, "palm tree large", 10f, 92f, 1.6f, 0f); Put(K, "palm tree bent", 13f, 96f, 1.6f, 90f);
            Scatter(K, new[] { "cactus", "cactus 2", "cactus 4", "cactus 5", "cactus 6" }, 6f, 100f, 9f, 6f, 20f, 1.4f, 1.9f, 1);
            Scatter(K, new[] { "desert stone small 8", "desert stone small 9", "desert stone small 10", "desert stone small 11", "stone small 5", "stone small 6" }, 0f, 100f, 6.5f, 5f, 18f, 1.2f, 2.0f, 1);
        }

        // ------------------------------------------------------------------ DOWNTOWN: a canyon of towers, a busy kerb, a plaza with a fountain
        static void CityLayout(LandKit K)
        {
            string[] towers = { "building", "building 2", "building 3", "building 4" };
            for (int side = -1; side <= 1; side += 2)
            {
                float z = side < 0 ? 4f : 10f;
                while (z < 100f)
                {
                    if (side < 0 && z > 44f && z < 62f) { z = 62f; continue; }   // the plaza on the left
                    var b = Put(K, K.Pick(towers), side * 16f, z, K.R(0.95f, 1.15f), side > 0 ? -90f : 90f);
                    float depth = Flank(b, side, 9.6f);
                    if (b != null) b.transform.position += new Vector3(0f, 0f, depth * 0.5f);
                    z += depth + 1.2f;
                }
            }
            for (float z = 2f; z < 100f; z += 12f)
                for (int side = -1; side <= 1; side += 2)
                {
                    Put(K, "lamppost", side * 8.1f, z, 1.5f, side > 0 ? -90f : 90f);
                    string kerb = K.Pick("tree", "bush plant", "bench", "trash can");
                    Put(K, kerb, side * 8.6f, z + 6f, kerb == "tree" ? 1.5f : 1.8f, side > 0 ? -90f : 90f);
                }
            string[] cars = { "car SUV large yellow", "sedan car brown", "car SUVs pickups lights red" };
            for (int i = 0; i < 6; i++) { int side = i % 2 == 0 ? 1 : -1; Put(K, K.Pick(cars), side * 6.0f, 14f + i * 14f + K.R(0f, 4f), 1.4f, K.R(-4f, 4f) + (K.rnd.Next(2) * 180f)); }
            Put(K, "fountain", -15f, 53f, 1.6f); Put(K, "bench", -11f, 47f, 1.6f, 90f); Put(K, "bench", -11f, 59f, 1.6f, 90f); Put(K, "tree", -19f, 47f, 1.8f); Put(K, "tree", -19f, 59f, 1.8f);
        }

        // ------------------------------------------------------------------ SOCCER FIELD: one whole pitch from goal to goal, stands and floodlights on both touchlines
        const float PitchHalfW = 18f, PitchLen = 100f, PitchNear = -2f;   // the pitch the ground texture paints: touchlines at |x| 18, goal lines at z -2 and 98

        static void SoccerLayout(LandKit K)
        {
            Put(K, "soccer goal", 0f, PitchNear + PitchLen + 0.6f, 1.9f, 0f);
            for (float x = -16f; x <= 16f; x += 4.4f) Put(K, "mesh fence", x, PitchNear + PitchLen + 5f, 1.1f);
            string[] stands = { "soccer grandstand 2", "soccer grandstand" };
            for (int side = -1; side <= 1; side += 2)
            {
                float z = 4f;
                while (z < 96f)
                {
                    var s = Put(K, stands[0], side * 26f, z, 1.4f, side > 0 ? -90f : 90f);
                    float depth = Flank(s, side, PitchHalfW + 3f);
                    if (s != null) s.transform.position += new Vector3(0f, 0f, depth * 0.5f);
                    z += depth + 0.6f;
                }
                foreach (float lz in new[] { 6f, 48f, 92f }) Put(K, "stadium lighting", side * (PitchHalfW + 2f), lz, 1.6f, side > 0 ? -90f : 90f);
            }
            Scatter(K, new[] { "tree 2" }, 40f, 104f, 6f, 34f, 42f, 1.4f, 1.8f, 1);
        }

        // ------------------------------------------------------------------ SPACE LAUNCH: the shuttle stack on its pad, spare stages lying by the apron
        static void LaunchLayout(LandKit K)
        {
            PutGroup(K, "space shuttle launch with environment", new[] { "space shuttle", "external tank", "solid rocket booster" }, -19f, 80f, 1.05f, 20f);
            Put(K, "water tank", 18f, 62f, 1.4f, 0f);
            Put(K, "water tank", 22f, 74f, 1.2f, 40f);
            Put(K, "external tank", 15.5f, 32f, 0.75f, 0f);          // the pack's prefab lies down: a spare tank on the apron
            Put(K, "solid rocket booster", -14.5f, 44f, 0.7f, 0f);
            foreach (float z in new[] { 8f, 36f, 64f, 92f }) { Put(K, "stadium lighting", -12.8f, z, 1.5f, 90f); Put(K, "stadium lighting", 12.8f, z + 14f, 1.5f, -90f); }
            Scatter(K, new[] { "box", "box 2", "barrel", "barrel 2" }, 4f, 100f, 7f, 10f, 11f, 1.8f, 2.4f, 1);
            Put(K, "stone large gray blue 5", 34f, 94f, 1.4f, 0f); Put(K, "stone large gray blue 4", -38f, 100f, 1.4f, 60f); Put(K, "stone large gray blue 6", 30f, 50f, 1.0f, 120f);
            Scatter(K, new[] { "stone small gray blue 2", "stone small gray blue 3", "stone small gray blue 4", "stone small gray blue 6" }, 10f, 100f, 6f, 15f, 26f, 1.3f, 1.9f, 1);
        }

        // ------------------------------------------------------------------ WILD WEST: the railway on the left with its train and station, the town's hitching rails on the right
        static void WestLayout(LandKit K)
        {
            const float rail = -11f;
            for (float z = -10f; z < 110f; z += 44.9f) Put(K, "railway", rail, z + 22.5f, 1f);
            Put(K, "train", rail, 38f, 1.0f, 90f);                   // the diorama stands its rolling stock along x: a quarter turn puts it on the rails
            Put(K, "passenger wagon", rail, 52f, 1.0f, 90f);
            Put(K, "freight wagon black", rail, 65.5f, 1.0f, 90f);
            Put(K, "railway station", -23f, 86f, 1.1f, 90f);
            Put(K, "water tank", -18f, 26f, 1.2f, 0f);
            Put(K, "coal", -17f, 60f, 1.2f, 0f);
            Put(K, "information post", -7.5f, 22f, 1.5f, 90f);
            for (float z = 6f; z < 100f; z += 18f) Put(K, "electric pole", -15f, z, 1.4f, 90f);
            // the town side
            string[] horses = { "horse black", "horse brown", "horse silver", "horse white" };
            foreach (float z in new[] { 18f, 46f, 78f })
            {
                Put(K, "hitching post", 7.5f, z, 1.6f, 90f);
                Put(K, horses[K.rnd.Next(4)], 9f, z - 1.2f, 1.5f, -90f); Put(K, horses[K.rnd.Next(4)], 9.2f, z + 1.4f, 1.5f, -80f);
            }
            Put(K, "cart", 11f, 32f, 1.4f, 10f); Put(K, "cart", 13f, 62f, 1.4f, -20f);
            Scatter(K, new[] { "barrel 2", "box 2", "bench 2" }, 8f, 100f, 14f, 6.5f, 8f, 1.1f, 1.4f, 1);
            Scatter(K, new[] { "cactus", "cactus 2", "cactus 3", "cactus 4", "cactus 5", "cactus 6" }, 10f, 100f, 4f, 12f, 26f, 1.5f, 2.0f, 1, 1);
            Scatter(K, new[] { "grass brown", "grass brown 2", "grass brown 3" }, 0f, 100f, 3f, 5f, 8f, 1.4f, 2.0f, 1);
            Put(K, "stone large brown", 30f, 82f, 1.5f, 0f); Put(K, "stone large brown 2", 24f, 98f, 1.4f, 70f); Put(K, "stone large brown 2", -36f, 100f, 1.5f, 200f);
        }
    }
}
