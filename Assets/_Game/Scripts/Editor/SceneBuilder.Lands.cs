// SceneBuilder.Lands.cs (Editor only)
// Worlds 5-14: the ten locations of the "Low Poly Atmospheric Locations Pack" (2026-10-02: "ten different backgrounds, each a different level; the
// city's floor streets, the desert sand, the football field a pitch"). One data-driven builder serves all ten: each LandTheme names its location
// (the pack's diorama prefab, whose pieces - buildings, trees, benches, goals, pyramids - become the scenery that scrolls past), the ground that
// replaces the sea (street, pitch, sand, snow, leaves, trail, dirt, concrete - or water for the two islands), the sky, the light, five bosses and
// the attacks they borrow from the lava / alien / meadow sets. Every world is five bosses long.
// The pack ships Built-in Standard materials: every piece is rebuilt with the URP copy of its one palette material.
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
        const string AtmoDir = "Assets/Palmov Island/Low Poly Atmospheric Locations Pack/";

        enum GroundKind { Street, Pitch, Sand, Snow, Leaves, Trail, Dirt, Concrete, Water }

        class LandTheme
        {
            public string id, name, tagline, location, sky;
            public GroundKind ground;
            public Color accent;
            public Color sun = Color.white; public float sunInt = 1.5f; public Vector3 sunEuler = new Vector3(50f, -28f, 0f);
            public Color fog = new Color(0.8f, 0.85f, 0.9f); public float fogStart = 120f, fogEnd = 210f;
            public Color ambSky = new Color(0.6f, 0.62f, 0.7f), ambEq = new Color(0.5f, 0.52f, 0.55f), ambGround = new Color(0.35f, 0.33f, 0.3f); public float amb = 1f;
            public float minX = 8f;                // the scenery stands this far from the lane at the nearest
            public float density = 1f;
            public string[] bosses, models;        // five names and five models ("S26" a Star Sparrow hull, or a pack prefab "Environment/sphinx")
            public string crate = "Stones/Stones large/stone large", pad = "Stones/Stones flat brown/stone flat brown";
            public string picks;                   // the attacks they borrow: "L2,L7,A3,N1,N4" (L lava, A alien, N meadow)
            public float hpMul = 1.2f;
            public Color fighter = Color.white; public Color trail = new Color(1f, 0.7f, 0.4f, 0.9f);
            public float sat = 14f, contrast = 8f, vignette = 0.22f; public Color filter = Color.white;
            public Color waterBase, waterShallow, waterHorizon;
            public float[] custom;                 // reserved
        }

        static LandTheme[] LandThemes()
        {
            return new[] {
                new LandTheme { id = "autumn", name = "AUTUMN FOREST", tagline = "Falling leaves", location = "autumn atmosphere forest with environment", sky = "Cold Sunset/Cold Sunset.mat", ground = GroundKind.Leaves, accent = new Color(1f, 0.55f, 0.15f),
                    sun = new Color(1f, 0.78f, 0.55f), sunInt = 1.5f, sunEuler = new Vector3(34f, -30f, 0f), fog = new Color(0.82f, 0.62f, 0.45f), fogStart = 110f, fogEnd = 220f, ambSky = new Color(0.75f, 0.6f, 0.5f), ambEq = new Color(0.6f, 0.45f, 0.32f), ambGround = new Color(0.4f, 0.28f, 0.15f), minX = 7f,
                    bosses = new[] { "LEAF MOTH", "OAK KEEPER", "ACORN WASP", "HOLLOW LOG", "FOREST SPIRIT" }, models = new[] { "S9", "Trees/Autumn trees/autumn tree 2", "S22", "Trees/Tree trunks/tree trunk", "Trees/Autumn trees/autumn tree 4" }, picks = "N1,N2,N3,N4,N0",
                    fighter = new Color(1f, 0.6f, 0.2f), trail = new Color(1f, 0.6f, 0.2f, 0.9f), sat = 18f, filter = new Color(1f, 0.95f, 0.88f), hpMul = 1.0f },
                new LandTheme { id = "camping", name = "CAMPING FOREST", tagline = "Night by the fire", location = "camping forest with environment", sky = "Night MoonBurst/Night Moon Burst.mat", ground = GroundKind.Trail, accent = new Color(1f, 0.65f, 0.2f),
                    sun = new Color(0.6f, 0.7f, 1f), sunInt = 0.9f, sunEuler = new Vector3(40f, -30f, 0f), fog = new Color(0.12f, 0.16f, 0.28f), fogStart = 90f, fogEnd = 190f, ambSky = new Color(0.25f, 0.3f, 0.5f), ambEq = new Color(0.2f, 0.25f, 0.35f), ambGround = new Color(0.25f, 0.2f, 0.12f), amb = 1.1f, minX = 7f,
                    bosses = new[] { "FIREFLY", "TENT KEEPER", "SPARK OWL", "OLD LANTERN", "BONFIRE KING" }, models = new[] { "S13", "Environment/Camping environment/camping tent red", "S8", "Environment/lamppost", "Environment/Camping environment/bonfire" }, crate = "Environment/Box/box", pad = "Stones/Stones flat brown/stone flat brown", picks = "L2,L7,L9,L10,L19",
                    fighter = new Color(0.5f, 0.7f, 1f), trail = new Color(0.6f, 0.8f, 1f, 0.9f), sat = 10f, contrast = 12f, vignette = 0.32f, filter = new Color(0.85f, 0.92f, 1f), hpMul = 1.1f },
                new LandTheme { id = "christmas", name = "CHRISTMAS VILLAGE", tagline = "Snow and lights", location = "christmas village with environment", sky = "Cold Night/Cold Night.mat", ground = GroundKind.Snow, accent = new Color(0.55f, 0.85f, 1f),
                    sun = new Color(0.8f, 0.88f, 1f), sunInt = 1.2f, sunEuler = new Vector3(42f, -30f, 0f), fog = new Color(0.55f, 0.62f, 0.78f), fogStart = 100f, fogEnd = 200f, ambSky = new Color(0.55f, 0.6f, 0.8f), ambEq = new Color(0.5f, 0.55f, 0.7f), ambGround = new Color(0.6f, 0.65f, 0.8f), minX = 7f,
                    bosses = new[] { "FROST SPRITE", "SNOW TREE", "ICE MOTH", "FIR GIANT", "WINTER HOUSE" }, models = new[] { "S10", "Trees/christmas tree", "S38", "Environment/Winter environment/snowman", "Houses/Wooden winter houses/wooden winter house" }, crate = "Stones/Stones large gray blue/stone large gray blue", pad = "Stones/Stones winter small/stone winter small", picks = "A8,A14,A20,A22,A2",
                    fighter = new Color(0.7f, 0.9f, 1f), trail = new Color(0.8f, 0.95f, 1f, 0.9f), sat = 8f, filter = new Color(0.92f, 0.96f, 1f), hpMul = 1.2f },
                new LandTheme { id = "desert", name = "DESERT PYRAMIDS", tagline = "Sand and sun", location = "desert pyramids with environment", sky = "Epic_GloriousPink/Epic_GloriousPink.mat", ground = GroundKind.Sand, accent = new Color(1f, 0.8f, 0.35f),
                    sun = new Color(1f, 0.82f, 0.6f), sunInt = 1.7f, sunEuler = new Vector3(36f, -30f, 0f), fog = new Color(0.9f, 0.68f, 0.5f), fogStart = 110f, fogEnd = 220f, ambSky = new Color(0.85f, 0.7f, 0.6f), ambEq = new Color(0.7f, 0.55f, 0.4f), ambGround = new Color(0.6f, 0.45f, 0.3f), minX = 8f,
                    bosses = new[] { "SAND WASP", "CACTUS KING", "DUNE RAY", "SPHINX", "PYRAMID LORD" }, models = new[] { "S6", "Plants/Cacti/cactus 3", "S35", "Environment/sphinx", "Environment/Pyramids/pyramid" }, crate = "Stones/Stones large brown/stone large brown", pad = "Stones/Stones flat brown/stone flat brown", picks = "L2,L9,L10,L19,L24",
                    fighter = new Color(1f, 0.8f, 0.4f), trail = new Color(1f, 0.85f, 0.5f, 0.9f), sat = 16f, filter = new Color(1f, 0.94f, 0.85f), hpMul = 1.3f },
                new LandTheme { id = "city", name = "DOWNTOWN", tagline = "City streets", location = "downtown with environment", sky = "Overcast Low/AllSky_Overcast4_Low.mat", ground = GroundKind.Street, accent = new Color(1f, 0.85f, 0.3f),
                    sun = new Color(0.95f, 0.95f, 1f), sunInt = 1.3f, sunEuler = new Vector3(55f, -25f, 0f), fog = new Color(0.62f, 0.66f, 0.72f), fogStart = 100f, fogEnd = 210f, ambSky = new Color(0.62f, 0.65f, 0.72f), ambEq = new Color(0.5f, 0.52f, 0.56f), ambGround = new Color(0.32f, 0.32f, 0.34f), minX = 13f, density = 0.9f,
                    bosses = new[] { "TAXI DRONE", "STREET LAMP", "TRAFFIC HAWK", "FOUNTAIN CORE", "SKY TOWER" }, models = new[] { "S17", "Environment/lamppost", "S7", "Environment/fountain", "Houses/Buildings/building 2" }, crate = "Environment/Box/box", pad = "Stones/Stones flat brown/stone flat brown", picks = "A7,A13,A21,A11,A27",
                    fighter = new Color(1f, 0.85f, 0.3f), trail = new Color(1f, 0.9f, 0.5f, 0.9f), sat = 10f, contrast = 10f, hpMul = 1.4f },
                new LandTheme { id = "japan", name = "JAPANESE ISLAND", tagline = "Temple on the water", location = "japanes island", sky = "Deep Dusk/Deep Dusk.mat", ground = GroundKind.Water, accent = new Color(1f, 0.55f, 0.7f),
                    sun = new Color(1f, 0.8f, 0.85f), sunInt = 1.3f, sunEuler = new Vector3(30f, -30f, 0f), fog = new Color(0.62f, 0.5f, 0.68f), fogStart = 110f, fogEnd = 210f, ambSky = new Color(0.65f, 0.55f, 0.75f), ambEq = new Color(0.5f, 0.45f, 0.6f), ambGround = new Color(0.3f, 0.4f, 0.5f), minX = 14f,
                    waterBase = new Color(0.08f, 0.2f, 0.4f), waterShallow = new Color(0.3f, 0.7f, 0.8f), waterHorizon = new Color(1.4f, 0.9f, 1.4f), pad = "Vehicles/japanese boat",
                    bosses = new[] { "PAPER CRANE", "TORII", "KOI RAY", "STONE LANTERN", "TEMPLE GUARDIAN" }, models = new[] { "S18", "Environment/torii gate", "S39", "Environment/japanese lantern", "Houses/japanes temple" }, picks = "A8,A9,A15,A17,A3",
                    fighter = new Color(1f, 0.6f, 0.75f), trail = new Color(1f, 0.7f, 0.85f, 0.9f), sat = 16f, filter = new Color(1f, 0.94f, 0.98f), hpMul = 1.5f },
                new LandTheme { id = "soccer", name = "SOCCER FIELD", tagline = "Match day", location = "soccer field with environment", sky = "Cartoon Base BlueSky/Day_BlueSky_Nothing.mat", ground = GroundKind.Pitch, accent = new Color(0.4f, 1f, 0.4f),
                    sun = new Color(1f, 0.97f, 0.88f), sunInt = 1.6f, sunEuler = new Vector3(55f, -28f, 0f), fog = new Color(0.82f, 0.9f, 0.97f), fogStart = 120f, fogEnd = 210f, ambSky = new Color(0.7f, 0.78f, 0.9f), ambEq = new Color(0.55f, 0.6f, 0.55f), ambGround = new Color(0.3f, 0.45f, 0.25f), minX = 36f, density = 0.7f,
                    bosses = new[] { "STRIKER", "GOAL POST", "REFEREE", "BENCH WARMER", "STADIUM" }, models = new[] { "S30", "Environment/Sports environment/soccer goal", "S14", "Environment/Benchs/bench", "Environment/Sports environment/soccer grandstand" }, crate = "Environment/Box/box", pad = "Stones/Stones flat brown/stone flat brown", picks = "N0,N1,A16,N3,N4",
                    fighter = new Color(1f, 1f, 1f), trail = new Color(1f, 1f, 1f, 0.9f), sat = 20f, hpMul = 1.6f },
                new LandTheme { id = "shuttle", name = "SPACE LAUNCH", tagline = "T-minus zero", location = "space shuttle launch with environment", sky = "Epic_BlueSunset/Epic_BlueSunset.mat", ground = GroundKind.Concrete, accent = new Color(1f, 0.55f, 0.2f),
                    sun = new Color(1f, 0.85f, 0.7f), sunInt = 1.5f, sunEuler = new Vector3(38f, -30f, 0f), fog = new Color(0.7f, 0.72f, 0.85f), fogStart = 120f, fogEnd = 220f, ambSky = new Color(0.62f, 0.66f, 0.82f), ambEq = new Color(0.55f, 0.55f, 0.6f), ambGround = new Color(0.4f, 0.38f, 0.36f), minX = 15f,
                    bosses = new[] { "ROCKET ANT", "FUEL TANK", "BOOSTER", "LAUNCH TOWER", "SPACE SHUTTLE" }, models = new[] { "S19", "Environment/external tank", "Environment/solid rocket booster", "Environment/water tank", "Vehicles/space shuttle" }, crate = "Environment/Box/box", pad = "Stones/Stones flat brown/stone flat brown", picks = "L2,A21,L10,A22,L24",
                    fighter = new Color(1f, 0.6f, 0.3f), trail = new Color(1f, 0.7f, 0.3f, 0.9f), sat = 12f, hpMul = 1.7f },
                new LandTheme { id = "treasure", name = "TREASURE ISLAND", tagline = "Pirate waters", location = "treasure Island with environment", sky = "Cartoon Base NightSky/Cartoon Base NightSky.mat", ground = GroundKind.Water, accent = new Color(1f, 0.82f, 0.25f),
                    sun = new Color(0.75f, 0.85f, 1f), sunInt = 1.1f, sunEuler = new Vector3(40f, -30f, 0f), fog = new Color(0.14f, 0.2f, 0.36f), fogStart = 100f, fogEnd = 200f, ambSky = new Color(0.3f, 0.38f, 0.6f), ambEq = new Color(0.25f, 0.35f, 0.5f), ambGround = new Color(0.1f, 0.35f, 0.4f), amb = 1.1f, minX = 14f,
                    waterBase = new Color(0.02f, 0.12f, 0.3f), waterShallow = new Color(0.05f, 0.65f, 0.6f), waterHorizon = new Color(0.4f, 1.2f, 1.6f), pad = "Vehicles/boat",
                    bosses = new[] { "PIRATE GULL", "TREASURE CHEST", "GHOST SHIP", "PALM KING", "SKULL MOUNTAIN" }, models = new[] { "S23", "Environment/chest", "Vehicles/destroyed ship", "Trees/Palm trees/palm tree large", "Mountains/skull mountain" }, picks = "A3,L2,A13,L10,A29",
                    fighter = new Color(0.6f, 0.8f, 1f), trail = new Color(0.7f, 0.9f, 1f, 0.9f), sat = 14f, contrast = 12f, vignette = 0.3f, hpMul = 1.8f },
                new LandTheme { id = "west", name = "WILD WEST", tagline = "Railway station", location = "wild west railway station with environment", sky = "Cold Sunset/Cold Sunset.mat", ground = GroundKind.Dirt, accent = new Color(0.95f, 0.6f, 0.3f),
                    sun = new Color(1f, 0.82f, 0.62f), sunInt = 1.6f, sunEuler = new Vector3(32f, -30f, 0f), fog = new Color(0.85f, 0.68f, 0.5f), fogStart = 110f, fogEnd = 220f, ambSky = new Color(0.82f, 0.68f, 0.58f), ambEq = new Color(0.65f, 0.5f, 0.38f), ambGround = new Color(0.5f, 0.38f, 0.25f), minX = 9f,
                    bosses = new[] { "DUST HAWK", "WATER TOWER", "IRON HORSE", "FREIGHT WAGON", "STATION BOSS" }, models = new[] { "S15", "Environment/water tank", "Vehicles/train", "Vehicles/freight wagon black", "Houses/railway station" }, crate = "Environment/Box/box", pad = "Stones/Stones flat brown/stone flat brown", picks = "L2,L9,L10,L19,L24",
                    fighter = new Color(0.95f, 0.65f, 0.35f), trail = new Color(1f, 0.75f, 0.45f, 0.9f), sat = 14f, filter = new Color(1f, 0.93f, 0.85f), hpMul = 1.9f },
            };
        }

        static bool HaveAtmo() { return AssetDatabase.LoadAssetAtPath<GameObject>(AtmoDir + "Prefabs/Location with environment/downtown with environment.prefab") != null; }
        static Material atmoMat;
        static Material AtmoMaterial()
        {
            if (atmoMat != null) return atmoMat;
            var src = AssetDatabase.LoadAssetAtPath<Material>(AtmoDir + "Materials/mat main.mat");
            atmoMat = src != null ? UrpCopy(src) : null;
            if (atmoMat != null) { atmoMat.SetFloat("_Smoothness", 0.12f); EditorUtility.SetDirty(atmoMat); }
            return atmoMat;
        }

        // ------------------------------------------------------------------ the ground
        static float Fr(float v) { return v - Mathf.Floor(v); }
        static float Hash2(int x, int y, int seed) { unchecked { int h = x * 374761393 + y * 668265263 + seed * 144665; h = (h ^ (h >> 13)) * 1274126177; return ((h ^ (h >> 16)) & 0xffff) / 65535f; } }
        static float VNoise(float x, float y, int seed)
        {
            int x0 = Mathf.FloorToInt(x), y0 = Mathf.FloorToInt(y); float tx = x - x0, ty = y - y0; tx = tx * tx * (3f - 2f * tx); ty = ty * ty * (3f - 2f * ty);
            return Mathf.Lerp(Mathf.Lerp(Hash2(x0, y0, seed), Hash2(x0 + 1, y0, seed), tx), Mathf.Lerp(Hash2(x0, y0 + 1, seed), Hash2(x0 + 1, y0 + 1, seed), tx), ty);
        }

        /// <summary>The ground of a land world as a tile: u across (the lane at u = 0.5 on an odd number of tiles), v along. Units noted per kind.</summary>
        static Texture2D LandGroundTexture(LandTheme t, out float tileX, out float tileZ, out int tilesAcross)
        {
            int S = 512; var tex = new Texture2D(S, S, TextureFormat.RGB24, false);
            tileX = 24f; tileZ = 24f; tilesAcross = 25;
            Func<float, float, Color> paint;
            switch (t.ground)
            {
                case GroundKind.Street:
                    tileX = 24f; tileZ = 24f;
                    paint = (u, v) =>
                    {
                        float x = (u - 0.5f) * 24f, z = v * 24f, ax = Mathf.Abs(x);
                        float n = VNoise(u * 40f, v * 40f, 3) * 0.06f;
                        if (ax < 7f)
                        {
                            Color c = new Color(0.20f + n, 0.21f + n, 0.23f + n);
                            if (ax < 0.16f && Fr(z / 6f) < 0.55f) c = new Color(0.95f, 0.8f, 0.25f);               // centre line, dashed
                            if (Mathf.Abs(ax - 3.5f) < 0.1f && Fr(z / 4f) < 0.5f) c = new Color(0.85f, 0.85f, 0.85f);   // lane lines
                            if (Mathf.Abs(ax - 6.4f) < 0.1f) c = new Color(0.88f, 0.88f, 0.88f);                     // kerb line
                            if (z < 2.4f && ax < 6.2f && Mathf.FloorToInt(x / 1.2f + 20f) % 2 == 0) c = new Color(0.9f, 0.9f, 0.9f);   // zebra crossing
                            return c;
                        }
                        if (ax < 7.5f) return new Color(0.55f, 0.55f, 0.57f);                                          // kerb
                        float tile = (Mathf.Floor(x / 1.6f) + Mathf.Floor(z / 1.6f)) % 2 == 0 ? 0.62f : 0.57f;
                        return new Color(tile + n, tile + n, tile + 0.02f + n);
                    }; break;
                case GroundKind.Pitch:
                    tileX = 120f; tileZ = 100f; tilesAcross = 1;
                    paint = (u, v) =>
                    {
                        float x = (u - 0.5f) * 120f, z = v * 100f, ax = Mathf.Abs(x);
                        float n = VNoise(u * 60f, v * 60f, 5) * 0.05f;
                        if (ax > 34f) return new Color(0.28f + n, 0.46f + n, 0.22f + n);                                // the grass beyond the touchline
                        bool band = Mathf.FloorToInt(z / 6f) % 2 == 0;
                        Color c = band ? new Color(0.20f + n, 0.58f + n, 0.20f + n) : new Color(0.16f + n, 0.50f + n, 0.17f + n);
                        bool line = false; float w = 0.28f;
                        if (Mathf.Abs(ax - 30f) < w) line = true;                                                         // touchlines
                        if (z < w || z > 100f - w) line = line || ax < 30f;                                               // goal lines
                        if (Mathf.Abs(z - 50f) < w && ax < 30f) line = true;                                              // halfway
                        if (Mathf.Abs(Mathf.Sqrt(x * x + (z - 50f) * (z - 50f)) - 9.2f) < w) line = true;                 // centre circle
                        if (Mathf.Sqrt(x * x + (z - 50f) * (z - 50f)) < 0.7f) line = true;
                        float dz = Mathf.Min(z, 100f - z);
                        if (ax < 20f && Mathf.Abs(dz - 16f) < w) line = true; if (Mathf.Abs(ax - 20f) < w && dz < 16f) line = true;   // penalty areas
                        if (ax < 9f && Mathf.Abs(dz - 6f) < w) line = true; if (Mathf.Abs(ax - 9f) < w && dz < 6f) line = true;     // goal areas
                        return line ? new Color(0.94f, 0.96f, 0.94f) : c;
                    }; break;
                case GroundKind.Sand:
                    tileX = 28f; tileZ = 28f;
                    paint = (u, v) =>
                    {
                        float n = VNoise(u * 12f, v * 12f, 7) * 0.5f + VNoise(u * 36f, v * 36f, 8) * 0.3f + VNoise(u * 90f, v * 90f, 9) * 0.2f;
                        float rip = 0.5f + 0.5f * Mathf.Sin((v * 14f + n * 3f) * Mathf.PI * 2f);
                        Color a = new Color(0.90f, 0.76f, 0.48f), b = new Color(0.80f, 0.64f, 0.38f);
                        Color c = Color.Lerp(b, a, Mathf.Clamp01(n * 0.7f + rip * 0.35f));
                        if (Hash2(Mathf.FloorToInt(u * 256f), Mathf.FloorToInt(v * 256f), 11) > 0.992f) c *= 0.7f;
                        return c;
                    }; break;
                case GroundKind.Snow:
                    tileX = 28f; tileZ = 28f;
                    paint = (u, v) =>
                    {
                        float n = VNoise(u * 10f, v * 10f, 13) * 0.6f + VNoise(u * 40f, v * 40f, 14) * 0.4f;
                        Color c = Color.Lerp(new Color(0.78f, 0.86f, 0.97f), new Color(0.97f, 0.98f, 1f), n);
                        if (Hash2(Mathf.FloorToInt(u * 256f), Mathf.FloorToInt(v * 256f), 15) > 0.985f) c = Color.white;
                        return c;
                    }; break;
                case GroundKind.Leaves:
                    tileX = 24f; tileZ = 24f;
                    paint = (u, v) =>
                    {
                        float n = VNoise(u * 14f, v * 14f, 17) * 0.6f + VNoise(u * 50f, v * 50f, 18) * 0.4f;
                        Color c = Color.Lerp(new Color(0.22f, 0.15f, 0.08f), new Color(0.42f, 0.28f, 0.12f), n);
                        float h = Hash2(Mathf.FloorToInt(u * 170f), Mathf.FloorToInt(v * 170f), 19);
                        if (h > 0.93f) c = Color.Lerp(new Color(0.85f, 0.4f, 0.1f), new Color(0.9f, 0.7f, 0.15f), Hash2(Mathf.FloorToInt(u * 170f), Mathf.FloorToInt(v * 170f), 20));
                        else if (h > 0.90f) c = new Color(0.65f, 0.15f, 0.08f);
                        return c;
                    }; break;
                case GroundKind.Trail:
                    tileX = 24f; tileZ = 24f;
                    paint = (u, v) =>
                    {
                        float x = (u - 0.5f) * 24f, ax = Mathf.Abs(x);
                        float n = VNoise(u * 30f, v * 30f, 21) * 0.5f + VNoise(u * 90f, v * 90f, 22) * 0.5f;
                        Color grass = Color.Lerp(new Color(0.10f, 0.26f, 0.10f), new Color(0.18f, 0.40f, 0.14f), n);
                        float edge = Mathf.SmoothStep(0f, 1f, Mathf.InverseLerp(6.5f, 5f, ax + (VNoise(u * 20f, v * 20f, 23) - 0.5f) * 2f));
                        Color dirt = Color.Lerp(new Color(0.34f, 0.24f, 0.14f), new Color(0.46f, 0.34f, 0.2f), n);
                        return Color.Lerp(grass, dirt, edge);
                    }; break;
                case GroundKind.Dirt:
                    tileX = 24f; tileZ = 24f;
                    paint = (u, v) =>
                    {
                        float x = (u - 0.5f) * 24f, ax = Mathf.Abs(x);
                        float n = VNoise(u * 16f, v * 16f, 25) * 0.6f + VNoise(u * 70f, v * 70f, 26) * 0.4f;
                        Color c = Color.Lerp(new Color(0.62f, 0.46f, 0.28f), new Color(0.78f, 0.6f, 0.38f), n);
                        if (Mathf.Abs(ax - 2.2f) < 0.35f) c *= 0.72f;                                    // wagon ruts
                        if (Hash2(Mathf.FloorToInt(u * 200f), Mathf.FloorToInt(v * 200f), 27) > 0.985f) c *= 0.6f;
                        return c;
                    }; break;
                case GroundKind.Concrete:
                    tileX = 30f; tileZ = 30f;
                    paint = (u, v) =>
                    {
                        float x = (u - 0.5f) * 30f, z = v * 30f, ax = Mathf.Abs(x);
                        float n = VNoise(u * 40f, v * 40f, 29) * 0.07f;
                        if (ax > 13f) { float g = VNoise(u * 30f, v * 30f, 31); return Color.Lerp(new Color(0.22f, 0.36f, 0.16f), new Color(0.32f, 0.5f, 0.22f), g); }
                        Color c = new Color(0.56f + n, 0.58f + n, 0.60f + n);
                        if (Fr(x / 10f) < 0.012f || Fr(z / 10f) < 0.012f) c *= 0.7f;                      // slab seams
                        if (ax < 0.2f && Fr(z / 5f) < 0.5f) c = new Color(0.95f, 0.8f, 0.2f);
                        if (ax > 11.5f && ax < 12.5f && (Mathf.FloorToInt(z / 1.5f) % 2 == 0)) c = new Color(0.95f, 0.78f, 0.15f);   // hazard stripes at the edge
                        return c;
                    }; break;
                default:
                    paint = (u, v) => Color.gray; break;
            }
            var px = new Color[S * S];
            for (int y = 0; y < S; y++) for (int x = 0; x < S; x++) px[y * S + x] = paint((x + 0.5f) / S, (y + 0.5f) / S);
            tex.SetPixels(px); tex.Apply();
            var saved = SaveTex(tex, "LandGround_" + t.id);
            var imp = AssetImporter.GetAtPath(Gen + "/Textures/LandGround_" + t.id + ".png") as TextureImporter;
            if (imp != null && (imp.wrapMode != TextureWrapMode.Repeat || imp.anisoLevel < 4)) { imp.wrapMode = TextureWrapMode.Repeat; imp.anisoLevel = 4; imp.SaveAndReimport(); }
            return saved;
        }

        // ------------------------------------------------------------------ scenery
        class Piece { public Transform src; public string name; public Bounds b; public float h, foot; }

        /// <summary>The scenery pieces of a location diorama: every child except the ground slab and the water, measured at the origin.</summary>
        static List<Piece> LandPieces(GameObject dioramaInstance)
        {
            var list = new List<Piece>();
            foreach (Transform c in dioramaInstance.transform)
            {
                string n = c.name.ToLowerInvariant();
                if (n.StartsWith("land ") || n.StartsWith("water location")) continue;
                var rs = c.GetComponentsInChildren<Renderer>(); if (rs.Length == 0) continue;
                var b = rs[0].bounds; foreach (var r in rs) b.Encapsulate(r.bounds);
                if (b.size.x > 30f || b.size.z > 30f) continue;   // a slab
                if (b.size.y < 0.25f && Mathf.Max(b.size.x, b.size.z) < 0.6f) continue;
                list.Add(new Piece { src = c, name = c.name, b = b, h = b.size.y, foot = Mathf.Max(b.size.x, b.size.z) });
            }
            return list;
        }

        /// <summary>A copy of a diorama piece standing on a holder: base-centre on the holder's origin, URP material on every renderer, pivot untouched.</summary>
        static GameObject ClonePieceTo(Piece p, Transform parent, string name)
        {
            var holder = new GameObject(name); holder.transform.SetParent(parent, false);
            var vis = UnityEngine.Object.Instantiate(p.src.gameObject, holder.transform, false);
            vis.name = "Visual";
            vis.transform.localPosition = new Vector3(p.src.position.x - p.b.center.x, p.src.position.y - p.b.min.y, p.src.position.z - p.b.center.z);
            vis.transform.localRotation = p.src.rotation; vis.transform.localScale = p.src.lossyScale;
            foreach (var r in vis.GetComponentsInChildren<Renderer>(true))
            {
                r.shadowCastingMode = ShadowCastingMode.Off; r.receiveShadows = false;
                var ms = r.sharedMaterials; for (int i = 0; i < ms.Length; i++) ms[i] = AtmoMaterial(); r.sharedMaterials = ms;
            }
            return holder;
        }

        static GameObject BuildLandWorld(LandTheme t, Mats M, Meshes X, Defs D, out Material skyMat, out VolumeProfile post)
        {
            var root = new GameObject("Land_" + t.id);
            var sc = root.AddComponent<WorldScroller>();
            // --- ground
            if (t.ground == GroundKind.Water)
            {
                var srcWater = AssetDatabase.LoadAssetAtPath<Material>("Assets/Stylized Water 3/Materials/StylizedWater3_ArcadeOcean.mat");
                Material w = M.water;
                if (srcWater != null)
                {
                    string path = Gen + "/Materials/WaterLand_" + t.id + ".mat";
                    w = AssetDatabase.LoadAssetAtPath<Material>(path);
                    if (w == null) { w = new Material(srcWater); AssetDatabase.CreateAsset(w, path); } else { w.shader = srcWater.shader; w.CopyPropertiesFromMaterial(srcWater); w.shaderKeywords = srcWater.shaderKeywords; }
                    w.SetVector("_Direction", new Vector4(0f, -1f, 0f, 0f)); w.SetFloat("_WaveHeight", 0.3f);
                    w.SetColor("_BaseColor", t.waterBase); w.SetColor("_ShallowColor", t.waterShallow); w.SetColor("_HorizonColor", t.waterHorizon);
                    EditorUtility.SetDirty(w);
                }
                var lake = MeshObj("Water", X.sea, root.transform, w); lake.transform.localPosition = new Vector3(0f, SeaLevel, 0f);
                var lr = lake.GetComponent<MeshRenderer>(); lr.shadowCastingMode = ShadowCastingMode.Off; lr.receiveShadows = true;
                var far = GameObject.CreatePrimitive(PrimitiveType.Plane); UnityEngine.Object.DestroyImmediate(far.GetComponent<Collider>());
                far.name = "WaterFar"; far.transform.SetParent(root.transform, false); far.transform.position = new Vector3(0f, SeaLevel - 1f, 120f); far.transform.localScale = new Vector3(120f, 1f, 120f);
                var fr2 = far.GetComponent<MeshRenderer>(); fr2.sharedMaterial = w; fr2.shadowCastingMode = ShadowCastingMode.Off;
                sc.water = lr;
            }
            else
            {
                var tex = LandGroundTexture(t, out float tileX, out float tileZ, out int across);
                var gm = Mat("LandGround_" + t.id, "Universal Render Pipeline/Lit", Color.white, m => { m.SetTexture("_BaseMap", tex); m.SetFloat("_Smoothness", 0.05f); m.SetFloat("_Metallic", 0f); });
                float planeW = tileX * across, planeD = 400f;
                gm.SetTextureScale("_BaseMap", new Vector2(across, planeD / tileZ));
                var floor = GameObject.CreatePrimitive(PrimitiveType.Plane); UnityEngine.Object.DestroyImmediate(floor.GetComponent<Collider>());
                floor.name = "Ground"; floor.transform.SetParent(root.transform, false); floor.transform.position = new Vector3(0f, SeaLevel, 120f); floor.transform.localScale = new Vector3(planeW / 10f, 1f, planeD / 10f);
                var fr = floor.GetComponent<MeshRenderer>(); fr.sharedMaterial = gm; fr.shadowCastingMode = ShadowCastingMode.Off; fr.receiveShadows = true;
                sc.water = fr; sc.waterTilesPerUnit = 1f / tileZ; sc.waterScrollSign = -1f;   // Plane v = 0.5 - z/10: a falling offset carries the markings toward the camera
                if (t.ground == GroundKind.Pitch)
                {   // beyond the pitch's own 120: plain turf out to the horizon, a hair lower
                    var apron = GameObject.CreatePrimitive(PrimitiveType.Plane); UnityEngine.Object.DestroyImmediate(apron.GetComponent<Collider>());
                    apron.name = "Apron"; apron.transform.SetParent(root.transform, false); apron.transform.position = new Vector3(0f, SeaLevel - 0.05f, 120f); apron.transform.localScale = new Vector3(120f, 1f, 40f);
                    var am = Mat("LandApron_" + t.id, "Universal Render Pipeline/Lit", new Color(0.28f, 0.46f, 0.22f), m => { m.SetFloat("_Smoothness", 0.05f); });
                    var ar = apron.GetComponent<MeshRenderer>(); ar.sharedMaterial = am; ar.shadowCastingMode = ShadowCastingMode.Off;
                }
            }
            // --- scenery from the diorama
            int seed = 17; foreach (char ch in t.id) seed = seed * 31 + ch;
            var rnd = new System.Random(seed);
            var dio = (GameObject)PrefabUtility.InstantiatePrefab(AssetDatabase.LoadAssetAtPath<GameObject>(AtmoDir + "Prefabs/Location with environment/" + t.location + ".prefab"));
            dio.transform.position = Vector3.zero; dio.transform.rotation = Quaternion.identity;
            var pieces = LandPieces(dio);
            float waterTop = 0f;
            if (t.ground == GroundKind.Water) foreach (Transform c in dio.transform) if (c.name.ToLowerInvariant().StartsWith("water location")) { var wr = c.GetComponentInChildren<Renderer>(); if (wr != null) waterTop = wr.bounds.max.y; }
            int n = 0;
            if (t.ground == GroundKind.Water)
            {   // an island: the author's own composition (temple, lanterns, boats, stones) lifted off its water slab, scattered along both sides
                for (float z = -10f; z < 200f; z += 46f)
                    for (int side = -1; side <= 1; side += 2)
                    {
                        var isle = new GameObject("Island" + n++); isle.transform.SetParent(root.transform, false);
                        float s = Mathf.Lerp(0.75f, 1.1f, (float)rnd.NextDouble());
                        isle.transform.position = new Vector3(side * Mathf.Lerp(24f, 38f, (float)rnd.NextDouble()), SeaLevel, z + (float)rnd.NextDouble() * 20f);
                        isle.transform.rotation = Quaternion.Euler(0f, side > 0 ? 180f : 0f, 0f);
                        foreach (Transform c in dio.transform)
                        {
                            string nm = c.name.ToLowerInvariant(); if (nm.StartsWith("water location")) continue;
                            var rs = c.GetComponentsInChildren<Renderer>(); if (rs.Length == 0) continue;
                            var copy = UnityEngine.Object.Instantiate(c.gameObject, isle.transform, false);
                            copy.transform.localPosition = new Vector3(c.position.x, c.position.y - waterTop, c.position.z) * s; copy.transform.localRotation = c.rotation; copy.transform.localScale = c.lossyScale * s;
                            foreach (var r in copy.GetComponentsInChildren<Renderer>(true)) { r.shadowCastingMode = ShadowCastingMode.Off; r.receiveShadows = false; var ms = r.sharedMaterials; for (int i = 0; i < ms.Length; i++) ms[i] = AtmoMaterial(); r.sharedMaterials = ms; }
                        }
                        sc.buoys.Add(isle.transform);
                    }
            }
            else
            {
                // a land world: single pieces drawn from the pool, scaled by size class, stood clear of the lane
                var pool = pieces.FindAll(p => p.h > 0.3f);
                if (pool.Count == 0) Debug.LogWarning("[SkySquad] " + t.id + ": no scenery pieces found in " + t.location);
                float zStep = 3.6f / Mathf.Max(0.3f, t.density);
                for (float z = -22f; z < 200f && pool.Count > 0; z += zStep)
                    for (int side = -1; side <= 1; side += 2)
                    {
                        int count = 1 + rnd.Next(2);
                        for (int c = 0; c < count; c++)
                        {
                            var p = pool[rnd.Next(pool.Count)];
                            float s = p.h < 2f ? Mathf.Lerp(2.4f, 3.4f, (float)rnd.NextDouble()) : p.h < 8f ? Mathf.Lerp(1.4f, 2.2f, (float)rnd.NextDouble()) : Mathf.Lerp(0.85f, 1.25f, (float)rnd.NextDouble());
                            bool far = rnd.NextDouble() < 0.22; if (far) s *= 1.7f;
                            float r = p.foot * s * 0.5f;
                            float x = side * (t.minX + r + (far ? 22f : 0f) + (float)rnd.NextDouble() * (far ? 30f : 12f));
                            var holder = ClonePieceTo(p, root.transform, "Prop" + n++);
                            holder.transform.position = new Vector3(x, SeaLevel - 0.03f, z + (float)rnd.NextDouble() * zStep);
                            holder.transform.rotation = Quaternion.Euler(0f, p.h > 8f || p.foot > 5f ? (rnd.Next(2) * 180f) : rnd.Next(360), 0f);
                            holder.transform.localScale = Vector3.one * s;
                            sc.buoys.Add(holder.transform);
                        }
                    }
            }
            UnityEngine.Object.DestroyImmediate(dio);
            sc.recycleBehind = -30f; sc.recycleAhead = 230f;
            // --- the cloud bank the world ends in and the near clouds (the sea world's, tinted by the world's fog)
            var wallMesh = MeshFactory.Panel(70f, 27f); wallMesh.name = "CloudWall";
            var wallMat = Mat("LandWall_" + t.id, "SkySquad/CloudWall", new Color(t.fog.r * 1.1f, t.fog.g * 1.1f, t.fog.b * 1.1f, 1f), m => m.SetTexture("_MainTex", CloudWallTexture()));
            var wall = MeshObj("Wall", SaveMesh(wallMesh), root.transform, wallMat);
            wall.transform.position = new Vector3(0f, SeaLevel - 4f, D.config.appearZ + D.config.appearRange + 8f);
            var wrr = wall.GetComponent<MeshRenderer>(); wrr.shadowCastingMode = ShadowCastingMode.Off; wrr.receiveShadows = false;
            var puffMat = Transparent("LandPuff_" + t.id, new Color(Mathf.Lerp(t.fog.r, 1f, 0.5f), Mathf.Lerp(t.fog.g, 1f, 0.5f), Mathf.Lerp(t.fog.b, 1f, 0.5f), 0.6f)); puffMat.SetTexture("_BaseMap", CloudTexture());
            for (int i = 0; i < 9; i++)
            {
                var cluster = new GameObject("Cloud" + i); cluster.transform.SetParent(root.transform, false);
                float sd = i % 2 == 0 ? -1f : 1f;
                cluster.transform.position = new Vector3(sd * (12f + (float)rnd.NextDouble() * 40f), 12f + (float)rnd.NextDouble() * 12f, 30f + i * 22f);
                int puffs = 2 + rnd.Next(2);
                for (int pp = 0; pp < puffs; pp++)
                {
                    var q = GameObject.CreatePrimitive(PrimitiveType.Quad); UnityEngine.Object.DestroyImmediate(q.GetComponent<Collider>());
                    q.name = "Puff" + pp; q.transform.SetParent(cluster.transform, false);
                    float sz = 12f + (float)rnd.NextDouble() * 12f, flip = rnd.Next(2) == 0 ? -1f : 1f;
                    q.transform.localPosition = new Vector3(((float)rnd.NextDouble() - 0.5f) * sz * 0.9f, ((float)rnd.NextDouble() - 0.3f) * sz * 0.25f, pp * 1.5f);
                    q.transform.localScale = new Vector3(sz * flip, sz * 0.5f, 1f);
                    var qr = q.GetComponent<MeshRenderer>(); qr.sharedMaterial = puffMat; qr.shadowCastingMode = ShadowCastingMode.Off;
                }
                sc.clouds.Add(cluster.transform);
            }
            // --- sky and post
            var packSky = AssetDatabase.LoadAssetAtPath<Material>("Assets/AllSkyFree/" + t.sky);
            skyMat = null;
            if (packSky != null)
            {
                string sp = Gen + "/Materials/SkyLand_" + t.id + ".mat";
                var sky = AssetDatabase.LoadAssetAtPath<Material>(sp);
                if (sky == null) { sky = new Material(packSky); AssetDatabase.CreateAsset(sky, sp); }
                sky.shader = packSky.shader; sky.CopyPropertiesFromMaterial(packSky);
                EditorUtility.SetDirty(sky); skyMat = sky;
            }
            string pp2 = Gen + "/Data/PostFX_" + t.id + ".asset";
            var profile = AssetDatabase.LoadAssetAtPath<VolumeProfile>(pp2);
            if (profile == null) { profile = ScriptableObject.CreateInstance<VolumeProfile>(); AssetDatabase.CreateAsset(profile, pp2); }
            T Fx<T>() where T : VolumeComponent
            {
                if (profile.TryGet(out T have)) return have;
                var c = profile.Add<T>(true); c.hideFlags = HideFlags.HideInHierarchy; AssetDatabase.AddObjectToAsset(c, profile); return c;
            }
            var bloom = Fx<Bloom>(); bloom.threshold.Override(1.1f); bloom.intensity.Override(0.55f); bloom.scatter.Override(0.65f);
            var tone = Fx<Tonemapping>(); tone.mode.Override(TonemappingMode.Neutral);
            var vig = Fx<Vignette>(); vig.intensity.Override(t.vignette); vig.smoothness.Override(0.45f);
            var grade = Fx<ColorAdjustments>(); grade.saturation.Override(t.sat); grade.contrast.Override(t.contrast); grade.postExposure.Override(0.1f); grade.colorFilter.Override(t.filter);
            EditorUtility.SetDirty(profile); post = profile;
            return root;
        }

        // ------------------------------------------------------------------ the cast
        static Material LandShipMaterial(LandTheme t)
        {
            var src = AssetDatabase.LoadAssetAtPath<Material>("Assets/StarSparrow/Materials/StarSparrow_Black.mat"); if (src == null) return null;
            string path = Gen + "/Materials/LandShip_" + t.id + ".mat";
            var m = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (m == null) { m = new Material(src); AssetDatabase.CreateAsset(m, path); }
            m.shader = src.shader; m.CopyPropertiesFromMaterial(src);
            Color a = t.accent;
            m.SetColor("_Color1", a * 0.62f); m.SetColor("_Color2", new Color(0.08f, 0.08f, 0.1f)); m.SetColor("_Color3", Color.Lerp(a, Color.white, 0.5f));
            m.SetColor("_Emission1", a * 0.35f); m.SetColor("_Emission2", a); m.SetColor("_Emission3", Color.Lerp(a, Color.white, 0.7f));
            m.SetColor("_Cockpit1", a * 0.35f); m.SetColor("_Cockpit2", a); m.SetColor("_Cockpit3", Color.Lerp(a, Color.white, 0.7f));
            m.SetFloat("_EmissionMultiplier", 1.8f); m.SetFloat("_CockpitMultiplier", 1.5f); m.SetFloat("_Dirty", 0.25f); m.SetFloat("_Darken", 0f);
            EditorUtility.SetDirty(m);
            return m;
        }

        static Material LandRemap(Material m, LandTheme t)
        {
            if (m == null || m.shader == null) return null;
            string sn = m.shader.name;
            if (sn.IndexOf("ColorizeSparrow", StringComparison.OrdinalIgnoreCase) >= 0) return LandShipMaterial(t);
            if (sn == "Standard") return AtmoMaterial();
            return null;
        }

        static GameObject[] BuildLandBosses(LandTheme t, Mats M)
        {
            var res = new GameObject[5];
            for (int i = 0; i < 5; i++)
            {
                string model = t.models[i];
                bool ship = model.Length > 1 && model[0] == 'S' && char.IsDigit(model[1]);
                string packPath = ship ? LavaShipPath(model) : AtmoDir + "Prefabs/" + model + ".prefab";
                if (!ship && AssetDatabase.LoadAssetAtPath<GameObject>(packPath) == null) { Debug.LogWarning("[SkySquad] " + t.id + " boss " + (i + 1) + ": " + model + " is missing, a ship stands in"); ship = true; packPath = LavaShipPath("S26"); }
                bool finale = i == 4;
                var def = new PackBoss { name = "Land" + t.id + (i + 1), packPrefab = packPath, triangles = 12000, keepMaterials = true, lieAcross = false,
                    width = ship ? 3.0f : finale ? 4.2f : 3.3f, maxHeight = ship ? 0f : finale ? 5.0f : 3.6f };
                def.remap = m => LandRemap(m, t);
                res[i] = PackBossPrefab(def, EnsurePackBossLow(def), M);
                if (res[i] == null) Debug.LogWarning("[SkySquad] " + t.id + " boss " + (i + 1) + " could not be built (" + packPath + ")");
            }
            return res;
        }

        static GameObject BuildLandFighter(LandTheme t, Mats M, Meshes X)
        {
            var low = EnsureOH1Low(); if (low == null) return null;
            var body = Lit("LandFighter_" + t.id, Color.white, 0.4f);
            body.SetColor("_BaseColor", t.fighter);
            var alb = AssetDatabase.LoadAssetAtPath<Texture2D>(Root + "/Art/Enemies/OH1_Fuselage_BaseColor.png"); if (alb != null) body.SetTexture("_BaseMap", alb);
            var nrm = NormalMap(Root + "/Art/Enemies/OH1_Fuselage_Normal.png"); if (nrm != null) { body.SetTexture("_BumpMap", nrm); body.EnableKeyword("_NORMALMAP"); }
            var glass = Transparent("LandFighterGlass_" + t.id, new Color(t.accent.r, t.accent.g, t.accent.b, 0.7f));
            return OH1EnemyPrefab("EnemyFighter_" + t.id, low, X.prop, M, () => null, body, glass, t.trail);
        }

        static GameObject LandPrefabAsset(string rel) { return AssetDatabase.LoadAssetAtPath<GameObject>(AtmoDir + "Prefabs/" + rel + ".prefab"); }

        static GameObject BuildLandBreakable(LandTheme t, Mats M, Meshes X)
        {
            var slab = LandPrefabAsset(t.crate); var pad = LandPrefabAsset(t.pad);
            if (slab == null || pad == null) { Debug.LogWarning("[SkySquad] " + t.id + ": crate pieces missing"); return null; }
            var root = new GameObject("BreakableLand_" + t.id);
            var bk = root.AddComponent<Breakable>();
            float raftTop = -1.125f; int n = 3; float tierH = 1.15f, h = tierH * n;
            var crate = new GameObject("Crate"); crate.transform.SetParent(root.transform, false);
            crate.transform.localPosition = new Vector3(0f, raftTop + h * 0.5f, 0f);
            var tiers = new GameObject[n]; var rends = new Renderer[n];
            for (int i = 0; i < n; i++)
            {
                var inst = (GameObject)PrefabUtility.InstantiatePrefab(slab); PrefabUtility.UnpackPrefabInstance(inst, PrefabUnpackMode.Completely, InteractionMode.AutomatedAction);
                inst.name = "Tier" + i; inst.transform.SetParent(crate.transform, false);
                var rs = inst.GetComponentsInChildren<Renderer>(true); var b = rs[0].bounds; foreach (var r in rs) b.Encapsulate(r.bounds);
                float kx = 5.0f / Mathf.Max(0.1f, b.size.x), ky = tierH / Mathf.Max(0.1f, b.size.y), kz = 3.0f / Mathf.Max(0.1f, b.size.z);
                inst.transform.localScale = new Vector3(kx, ky, kz);
                inst.transform.localRotation = Quaternion.Euler(0f, (i - 1) * 5f, 0f);
                inst.transform.localPosition = new Vector3(-b.center.x * kx, -h * 0.5f + tierH * (n - 1 - i) - b.min.y * ky, -b.center.z * kz);
                foreach (var r in rs) { r.shadowCastingMode = ShadowCastingMode.On; r.receiveShadows = true; var ms = r.sharedMaterials; for (int k = 0; k < ms.Length; k++) ms[k] = AtmoMaterial(); r.sharedMaterials = ms; }
                tiers[i] = inst; rends[i] = rs[0];
            }
            var boat = new GameObject("Boat"); boat.transform.SetParent(root.transform, false);
            var pi = (GameObject)PrefabUtility.InstantiatePrefab(pad); PrefabUtility.UnpackPrefabInstance(pi, PrefabUnpackMode.Completely, InteractionMode.AutomatedAction);
            pi.transform.SetParent(boat.transform, false);
            var prs = pi.GetComponentsInChildren<Renderer>(true); var pb = prs[0].bounds; foreach (var r in prs) pb.Encapsulate(r.bounds);
            bool water = t.ground == GroundKind.Water;
            float pk = (water ? 7.6f : 7.2f) / Mathf.Max(pb.size.x, pb.size.z);
            float thick = Mathf.Clamp(0.5f / Mathf.Max(0.05f, pb.size.y * pk), 0.5f, 2.5f);   // flat pads are kept thin; a boat keeps its own depth
            if (water) thick = 1f;
            pi.transform.localScale = new Vector3(pk, pk * thick, pk);
            pi.transform.localPosition = new Vector3(-pb.center.x * pk, raftTop - pb.max.y * pk * thick, -pb.center.z * pk);
            foreach (var r in prs) { r.shadowCastingMode = ShadowCastingMode.Off; r.receiveShadows = true; var ms = r.sharedMaterials; for (int k = 0; k < ms.Length; k++) ms[k] = AtmoMaterial(); r.sharedMaterials = ms; }
            float boxTop = raftTop + h;
            bk.model = crate.transform; bk.tiers = tiers; bk.crateRenderers = rends;
            bk.boat = boat.transform; bk.boatRenderer = null; bk.weaponBoatMesh = null;
            bk.label = Label3D("Label", root.transform, new Vector3(0f, raftTop + h * 0.45f, -1.65f), 18f, Color.white, fontOutline);
            bk.hint = Label3D("Hint", root.transform, new Vector3(0f, boxTop + 0.82f, -0.6f), 4f, Gold, fontOutlineSmall);
            bk.boxTop = boxTop;
            bk.prizeAura = Cfxr("Misc/CFXR2 Shiny Item (Loop)"); bk.prizeGlow = Cfxr("Light/CFXR3 LightGlow A (Loop)"); bk.prizeTrail = M.tracer;
            return SavePrefab(root, "BreakableLand_" + t.id);
        }

        static GameObject BuildLandSplash(LandTheme t, Mats M)
        {
            var root = new GameObject("LandSplash_" + t.id);
            Color c = t.ground == GroundKind.Water ? new Color(0.85f, 0.95f, 1f) : Color.Lerp(t.accent, new Color(0.7f, 0.6f, 0.45f), 0.6f);
            var ps = ParticlePrefab(root, M.particle, 0, 3f, 8f, 0.18f, 0.5f, 0.45f, 0.9f, c, Color.Lerp(c, Color.white, 0.4f), 1.2f, true);
            var em = ps.emission; em.SetBursts(new ParticleSystem.Burst[0]);
            var main = ps.main; main.playOnAwake = false;
            var sh = ps.shape; sh.shapeType = ParticleSystemShapeType.Cone; sh.angle = 34f; sh.radius = 0.4f; sh.rotation = new Vector3(-90f, 0f, 0f);
            return SavePrefab(root, "LandSplash_" + t.id);
        }

        /// <summary>The attacks a land world borrows: "L2" is lava opening 2, "A3" alien, "N1" meadow; the same index of each set's enraged attack.</summary>
        static void LandAttacks(LandTheme t, out BossAttack[] a1, out BossAttack[] a2)
        {
            var L1 = LavaAttacks(); var L2 = LavaAttacks2(); var A1 = AlienAttacks(); var A2 = AlienAttacks2(); var N1 = NatureAttacks(); var N2 = NatureAttacks2();
            a1 = new BossAttack[5]; a2 = new BossAttack[5];
            var p = t.picks.Split(',');
            for (int i = 0; i < 5; i++)
            {
                char k = p[i][0]; int idx = int.Parse(p[i].Substring(1));
                switch (k)
                {
                    case 'L': a1[i] = L1[idx]; a2[i] = L2[idx]; break;
                    case 'A': a1[i] = A1[idx]; a2[i] = A2[idx]; break;
                    default: a1[i] = N1[Mathf.Min(idx, 4)]; a2[i] = N2[Mathf.Min(idx, 4)]; break;
                }
            }
        }

        static WorldEntry LandEntry(LandTheme t, GameObject root, Material sky, VolumeProfile post, WorldEntry sea, Mats M, Meshes X)
        {
            var bosses = BuildLandBosses(t, M);
            var fighter = BuildLandFighter(t, M, X);
            var crate = BuildLandBreakable(t, M, X);
            var splash = BuildLandSplash(t, M);
            LandAttacks(t, out var a1, out var a2);
            return new WorldEntry
            {
                id = t.id, displayName = t.name, tagline = t.tagline, thumbnail = WorldSprite("world_" + t.id + ".png", t.accent), accent = t.accent,
                environment = new[] { root }, skybox = sky, skyRotation = 0f,
                sunColor = t.sun, sunIntensity = t.sunInt, sunEuler = t.sunEuler, sunShadow = 0.5f,
                fog = true, fogColor = t.fog, fogStart = t.fogStart, fogEnd = t.fogEnd,
                ambientFromSky = false, ambientSky = t.ambSky, ambientEquator = t.ambEq, ambientGround = t.ambGround, ambientIntensity = t.amb,
                post = post, fighterPrefab = fighter != null ? fighter : sea.fighterPrefab, bossPrefabs = bosses, bossPrefabByNumber = bosses, bossAttacks = a1, bossAttacks2 = a2,
                bossNames = t.bosses, bossColors = null, stageNames = new[] { t.name },
                onGround = t.ground != GroundKind.Water, lastBoss = 5, bossHpMul = t.hpMul,
                breakablePrefab = crate != null ? crate : sea.breakablePrefab, splashPrefab = splash != null ? splash : sea.splashPrefab,
                surfaceRing = t.ground == GroundKind.Water ? new Color(0.85f, 0.95f, 1f) : Color.Lerp(t.accent, Color.white, 0.5f)
            };
        }
    }
}
