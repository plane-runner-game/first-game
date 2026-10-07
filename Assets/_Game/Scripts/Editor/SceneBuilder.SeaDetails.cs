// SceneBuilder.SeaDetails.cs (Editor only)
// World 1's details (2026-10-07: "the first level's details, beautiful, everything; take all the time"): the open sea had only its buoys.
// Now a navy sails alongside the lane - an aircraft carrier with the hero plane parked on its deck, three destroyers - with rocky islets
// under palms, a wreck settled on a sandbar and flocks of gulls wheeling overhead. The ships and the gull are our own models
// (Tools/blender/sea_props.py -> Art/Sea/*.fbx); the stones, palms and wreck are the Low Poly Atmospheric Locations Pack's.
// Everything rides WorldScroller as a "buoy", so it scrolls with the sea and comes out of the same line as the crates and the planes
// (Breakable.Appear), and it all stands clear of the lane: nothing here ever covers the fight.
using System;
using System.Collections.Generic;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;

namespace SkySquad.EditorTools
{
    public static partial class SceneBuilder
    {
        const string SeaArtDir = Root + "/Art/Sea/";

        static Dictionary<string, Material> seaMats;

        /// <summary>The ship and gull FBX slots (named in the Blender script) mapped onto generated materials.</summary>
        static Material SeaRemap(Material src)
        {
            if (seaMats == null)
            {
                seaMats = new Dictionary<string, Material>
                {
                    { "ShipGrey",   Lit("Sea_ShipGrey",   new Color(0.58f, 0.63f, 0.67f), 0.30f) },
                    { "ShipDark",   Lit("Sea_ShipDark",   new Color(0.22f, 0.24f, 0.27f), 0.30f) },
                    { "ShipDeck",   Lit("Sea_ShipDeck",   new Color(0.34f, 0.36f, 0.38f), 0.15f) },
                    { "ShipRed",    Lit("Sea_ShipRed",    new Color(0.62f, 0.16f, 0.13f), 0.25f) },
                    { "ShipWhite",  Lit("Sea_ShipWhite",  new Color(0.95f, 0.95f, 0.92f), 0.30f) },
                    { "ShipGlass",  Lit("Sea_ShipGlass",  new Color(0.12f, 0.22f, 0.34f), 0.85f) },
                    { "ShipBlack",  Lit("Sea_ShipBlack",  new Color(0.08f, 0.08f, 0.09f), 0.25f) },
                    { "ShipYellow", Lit("Sea_ShipYellow", new Color(1.00f, 0.80f, 0.20f), 0.30f) },
                    { "GullWhite",  Lit("Sea_GullWhite",  new Color(0.98f, 0.98f, 0.96f), 0.20f) },
                    { "GullGrey",   Lit("Sea_GullGrey",   new Color(0.66f, 0.70f, 0.75f), 0.20f) },
                    { "GullBlack",  Lit("Sea_GullBlack",  new Color(0.12f, 0.12f, 0.13f), 0.20f) },
                    { "GullBeak",   Lit("Sea_GullBeak",   new Color(1.00f, 0.72f, 0.12f), 0.30f) },
                };
            }
            if (src != null) foreach (var kv in seaMats) if (src.name.StartsWith(kv.Key)) return kv.Value;
            return UrpCopy(src);
        }

        /// <summary>An instance of one of our FBX models, unpacked, nose +Z (the importer's 180 on the root undone), materials remapped,
        /// no shadows cast (scenery far off the lane: its shadows only cost), parented under <paramref name="parent"/> at the origin.</summary>
        static GameObject ModelCopy(string path, Transform parent, string name, Func<Material, Material> remap)
        {
            var src = AssetDatabase.LoadAssetAtPath<GameObject>(path);
            if (src == null) { Debug.LogWarning("[SkySquad] model missing: " + path); return null; }
            var go = (GameObject)PrefabUtility.InstantiatePrefab(src);
            PrefabUtility.UnpackPrefabInstance(go, PrefabUnpackMode.Completely, InteractionMode.AutomatedAction);
            go.name = name; go.transform.SetParent(parent, false);
            go.transform.localPosition = Vector3.zero; go.transform.localRotation = Quaternion.identity; go.transform.localScale = Vector3.one;
            foreach (var r in go.GetComponentsInChildren<Renderer>(true))
            {
                var ms = r.sharedMaterials; for (int i = 0; i < ms.Length; i++) ms[i] = remap(ms[i]); r.sharedMaterials = ms;
                r.shadowCastingMode = ShadowCastingMode.Off; r.receiveShadows = true;
            }
            return go;
        }

        /// <summary>A pack prefab (Low Poly Atmospheric Locations) standing base-centre on the origin of a new child, its palette on URP.</summary>
        static GameObject AtmoCopy(string rel, Transform parent, string name)
        {
            var src = AssetDatabase.LoadAssetAtPath<GameObject>(AtmoDir + "Prefabs/" + rel + ".prefab");
            if (src == null) { Debug.LogWarning("[SkySquad] pack prefab missing: " + rel); return null; }
            var holder = new GameObject(name); holder.transform.SetParent(parent, false);
            var go = (GameObject)PrefabUtility.InstantiatePrefab(src);
            PrefabUtility.UnpackPrefabInstance(go, PrefabUnpackMode.Completely, InteractionMode.AutomatedAction);
            go.name = "Visual";
            go.transform.position = Vector3.zero; go.transform.rotation = Quaternion.identity;   // measured at the origin, before it joins the holder
            var rs = go.GetComponentsInChildren<Renderer>(true);
            Vector3 offset = Vector3.zero;
            if (rs.Length > 0)
            {
                var b = rs[0].bounds; foreach (var r in rs) b.Encapsulate(r.bounds);
                offset = new Vector3(-b.center.x, -b.min.y, -b.center.z);
            }
            go.transform.SetParent(holder.transform, false);
            go.transform.localPosition = offset; go.transform.localRotation = Quaternion.identity;
            foreach (var r in rs)
            {
                var ms = r.sharedMaterials; for (int i = 0; i < ms.Length; i++) ms[i] = AtmoMaterial(); r.sharedMaterials = ms;
                r.shadowCastingMode = ShadowCastingMode.Off; r.receiveShadows = true;
            }
            return holder;
        }

        static void Bob(GameObject holder, Transform visual, float heave, float roll, float pitch, float period, float phase)
        {
            var b = holder.AddComponent<SeaBob>(); b.target = visual; b.heave = heave; b.roll = roll; b.pitch = pitch; b.period = period; b.phase = phase;
        }

        /// <summary>A white wake behind a ship: a long soft quad flat on the water, fading toward its tail (the ship sails "away" from the squad).</summary>
        static void Wake(Transform ship, float length, float width, float sternZ)
        {
            var mat = Transparent("Sea_Wake", new Color(1f, 1f, 1f, 0.55f)); mat.SetTexture("_BaseMap", WakeTexture());
            var q = GameObject.CreatePrimitive(PrimitiveType.Quad); UnityEngine.Object.DestroyImmediate(q.GetComponent<Collider>());
            q.name = "Wake"; q.transform.SetParent(ship, false);
            q.transform.localPosition = new Vector3(0f, 0.12f, sternZ - length * 0.5f + 0.5f);
            q.transform.localRotation = Quaternion.Euler(90f, 0f, 0f); q.transform.localScale = new Vector3(width, length, 1f);
            var r = q.GetComponent<MeshRenderer>(); r.sharedMaterial = mat; r.shadowCastingMode = ShadowCastingMode.Off; r.receiveShadows = false;
        }

        /// <summary>The wake's picture: a V of foam, dense at the top (the stern) and frayed toward the bottom, with noise breaking it up.</summary>
        static Texture2D WakeTexture()
        {
            const int W = 64, H = 256;
            var t = new Texture2D(W, H, TextureFormat.RGBA32, false);
            var rnd = new System.Random(3);
            var noise = new float[W * H]; for (int i = 0; i < noise.Length; i++) noise[i] = (float)rnd.NextDouble();
            for (int y = 0; y < H; y++)
                for (int x = 0; x < W; x++)
                {
                    float v = y / (float)(H - 1);               // 1 at the stern (top), 0 at the tail
                    float u = Mathf.Abs(x / (float)(W - 1) - 0.5f) * 2f;   // 0 centre, 1 edge
                    float spread = Mathf.Lerp(1f, 0.35f, v);    // the V opens toward the tail
                    float edge = Mathf.Clamp01(1f - Mathf.Abs(u - spread * 0.85f) / 0.22f);   // the two arms
                    float core = Mathf.Clamp01(1f - u / (0.25f + 0.35f * (1f - v))) * v;      // the churned water right behind the stern
                    float n = 0.55f + 0.45f * noise[(y / 3) * W + x];
                    float a = Mathf.Clamp01(Mathf.Max(edge * 0.8f, core) * n * Mathf.Pow(v, 0.6f));
                    t.SetPixel(x, y, new Color(1f, 1f, 1f, a));
                }
            t.Apply();
            var tex = SaveTex(t, "SeaWake");
            var imp = AssetImporter.GetAtPath(Gen + "/Textures/SeaWake.png") as TextureImporter;
            if (imp != null && (!imp.alphaIsTransparency || imp.wrapMode != TextureWrapMode.Clamp)) { imp.alphaIsTransparency = true; imp.wrapMode = TextureWrapMode.Clamp; imp.SaveAndReimport(); tex = AssetDatabase.LoadAssetAtPath<Texture2D>(Gen + "/Textures/SeaWake.png"); }
            return tex;
        }

        /// <summary>World 1's scenery, added to the sea's WorldScroller. z runs over one recycle span (-20 .. 200).</summary>
        static void BuildSeaDetails(Transform worldRoot, WorldScroller world)
        {
            seaMats = null;
            var root = new GameObject("SeaDetails").transform; root.SetParent(worldRoot, false);
            float y0 = SeaLevel;
            int n = 0;
            GameObject Holder(string name, float x, float z, float yaw)
            {
                var h = new GameObject(name + n++); h.transform.SetParent(root, false);
                h.transform.position = new Vector3(x, y0, z); h.transform.rotation = Quaternion.Euler(0f, yaw, 0f);
                world.buoys.Add(h.transform);
                return h;
            }

            // --- the carrier, to starboard, sailing the way we fly; the hero plane parked on deck (the squad's home)
            {
                var h = Holder("Carrier", 21f, 72f, 0f);
                var c = ModelCopy(SeaArtDir + "Carrier.fbx", h.transform, "Visual", SeaRemap);
                if (c != null)
                {
                    Bob(h, c.transform, 0.06f, 0.6f, 0.3f, 8f, 0.4f);
                    Wake(c.transform, 22f, 6f, -12f);
                    var hero = HeroModel();
                    if (hero != null)
                    {   // four fighters on deck: three parked aft by the island, one on the bow catapult
                        var spots = new[] { new Vector3(1.0f, 1.66f, -7.5f), new Vector3(1.0f, 1.66f, -9.6f), new Vector3(1.0f, 1.66f, -11.7f), new Vector3(-0.6f, 1.66f, 9.0f) };
                        var yaws = new[] { -60f, -60f, -60f, 0f };
                        for (int i = 0; i < spots.Length; i++)
                        {
                            var p = ModelCopy(HeroFbx, c.transform, "DeckPlane" + i, HeroRemap);
                            if (p == null) continue;
                            p.transform.localScale = Vector3.one * 0.3f;   // 1.5 long against the 26 deck
                            p.transform.localRotation = Quaternion.Euler(0f, yaws[i], 0f);
                            p.transform.localPosition = spots[i] + Vector3.up * 0.28f;   // the model is centred on its bounds: half its 1.84 height x 0.3
                        }
                    }
                }
            }
            // --- three destroyers: two to port, one to starboard, spread over the span
            foreach (var (x, z, yaw, ph) in new[] { (-16f, 22f, 0f, 0f), (-19f, 128f, 4f, 2.1f), (15.5f, 168f, -3f, 4.3f) })
            {
                var h = Holder("Destroyer", x, z, yaw);
                var d = ModelCopy(SeaArtDir + "Destroyer.fbx", h.transform, "Visual", SeaRemap);
                if (d == null) continue;
                Bob(h, d.transform, 0.1f, 1.8f, 0.6f, 5.5f, ph);
                Wake(d.transform, 14f, 3.6f, -7f);
            }
            // --- rocky islets with palms
            var rnd = new System.Random(11);
            string[] rocks = { "stone large gray blue", "stone large gray blue 2", "stone large gray blue 3", "stone large gray blue 4", "stone large gray blue 5", "stone large gray blue 6" };
            string[] palms = { "palm tree large", "palm tree bent", "palm tree tilted", "palm tree small" };
            foreach (var (x, z) in new[] { (-15f, 58f), (16f, 8f), (14f, 112f), (-18.5f, 178f), (27f, 196f), (-27f, 92f) })
            {
                var h = Holder("Islet", x, z, rnd.Next(360));
                h.transform.position += Vector3.down * 0.5f;   // sunk a little: the sea laps at the rocks
                float s = Mathf.Lerp(0.9f, 1.3f, (float)rnd.NextDouble());   // the pack stones are 3.6-6 across: an islet ends up about 8-12 wide
                int count = 2 + rnd.Next(2);
                float top = 0f;
                for (int i = 0; i < count; i++)
                {
                    var r = AtmoCopy("Stones/Stones large gray blue/" + rocks[rnd.Next(rocks.Length)], h.transform, "Rock" + i);
                    if (r == null) continue;
                    float rs = s * Mathf.Lerp(0.7f, 1.15f, (float)rnd.NextDouble());
                    r.transform.localScale = Vector3.one * rs;
                    r.transform.localPosition = new Vector3(((float)rnd.NextDouble() - 0.5f) * 3.2f * s, 0f, ((float)rnd.NextDouble() - 0.5f) * 3.2f * s);
                    r.transform.localRotation = Quaternion.Euler(0f, rnd.Next(360), 0f);
                    foreach (var rr in r.GetComponentsInChildren<Renderer>()) top = Mathf.Max(top, rr.bounds.max.y - h.transform.position.y);
                }
                int pc = 1 + rnd.Next(3);
                for (int i = 0; i < pc; i++)
                {
                    var p = AtmoCopy("Trees/Palm trees/" + palms[rnd.Next(palms.Length)], h.transform, "Palm" + i);
                    if (p == null) continue;
                    p.transform.localScale = Vector3.one * s * Mathf.Lerp(0.7f, 1.0f, (float)rnd.NextDouble());   // palms 5-9 tall
                    p.transform.localPosition = new Vector3(((float)rnd.NextDouble() - 0.5f) * 1.2f * s, top * 0.55f, ((float)rnd.NextDouble() - 0.5f) * 1.2f * s);
                    p.transform.localRotation = Quaternion.Euler(0f, rnd.Next(360), 0f);
                }
            }
            // --- the wreck: settled on a sandbar to port, listing, half under
            {
                var h = Holder("Wreck", -12.5f, 150f, 35f);
                var w = AtmoCopy("Vehicles/destroyed ship", h.transform, "Wreck");
                if (w != null)
                {
                    var rs = w.GetComponentsInChildren<Renderer>(); var b = rs[0].bounds; foreach (var r in rs) b.Encapsulate(r.bounds);
                    float k = 9f / Mathf.Max(0.01f, Mathf.Max(b.size.x, b.size.z));   // about 9 long
                    w.transform.localScale = Vector3.one * k;
                    w.transform.localPosition = Vector3.down * (b.size.y * k * 0.35f);
                    w.transform.localRotation = Quaternion.Euler(0f, 0f, 14f);
                }
            }
            // --- gulls: three flocks wheeling over the sea, off the lane and above the fight
            foreach (var (x, z, alt, count) in new[] { (-11f, 40f, 11f, 4), (12f, 100f, 13f, 3), (-9f, 165f, 12f, 5) })
            {
                var h = Holder("Gulls", x, z, 0f);
                h.transform.position = new Vector3(x, alt, z);
                for (int i = 0; i < count; i++)
                {
                    var g = ModelCopy(SeaArtDir + "Gull.fbx", h.transform, "Gull" + i, SeaRemap);
                    if (g == null) continue;
                    g.transform.localScale = Vector3.one * 1.1f;
                    var gull = g.AddComponent<Gull>();
                    gull.wingL = g.transform.Find("WingL"); gull.wingR = g.transform.Find("WingR");
                    gull.radius = 4.5f + i * 1.3f; gull.height = (i % 2) * 1.2f; gull.speed = (i % 3 == 2 ? -1f : 1f) * (3.6f + i * 0.4f); gull.phase = i * 1.9f;
                }
            }
        }
    }
}
