// SceneBuilder.Hero.cs (Editor only)
// The hero plane (2026-10-07: "a plane that suits the game, simple and attractive, that the player remembers", then "bigger, longer, more
// of a warplane"): the plane every attempt starts on, our own model instead of a pack ship. Modelled from code in Blender
// (Tools/blender/hero_plane.py -> Art/Hero/HeroPlane.fbx): a twin-engine fighter in blue-grey camouflage with a pointed dark radome, a red
// nose band, a gold canopy, two tall red canted tails, blue-white-red roundels and four red-headed missiles (one on each wing tip, one under
// each wing). It is designed for the one angle the player sees it from - behind and a little above - where it reads as an "H" (the tip
// missiles) with a red "V" (the tails) over two glowing nozzles. 4.6k triangles. A red-and-white toy jet came first the same day.
using System.Collections.Generic;
using UnityEditor;
using UnityEngine;

namespace SkySquad.EditorTools
{
    public static partial class SceneBuilder
    {
        const string HeroFbx = Root + "/Art/Hero/HeroPlane.fbx";

        static GameObject HeroModel() => AssetDatabase.LoadAssetAtPath<GameObject>(HeroFbx);

        static Dictionary<string, Material> heroMats;

        /// <summary>The FBX's six slots (named in the Blender script) mapped onto generated materials, so the colours live here and not in the file.</summary>
        static Material HeroRemap(Material src)
        {
            if (heroMats == null)
            {
                heroMats = new Dictionary<string, Material>
                {
                    { "HeroBody",  Lit("HeroBody",  new Color(0.47f, 0.55f, 0.60f), 0.45f) },   // blue-grey
                    { "HeroCamo",  Lit("HeroCamo",  new Color(0.29f, 0.36f, 0.40f), 0.40f) },   // the darker camouflage patches
                    { "HeroBelly", Lit("HeroBelly", new Color(0.78f, 0.81f, 0.83f), 0.45f) },
                    { "HeroRed",   Lit("HeroRed",   new Color(0.90f, 0.12f, 0.12f), 0.55f) },   // nose band, tails, missile heads: the squad's mark
                    { "HeroWhite", Lit("HeroWhite", new Color(0.96f, 0.96f, 0.95f), 0.50f) },
                    { "HeroBlue",  Lit("HeroBlue",  new Color(0.10f, 0.24f, 0.62f), 0.45f) },
                    { "HeroGlass", Lit("HeroGlass", new Color(0.62f, 0.36f, 0.08f), 0.95f) },   // a dark amber visor canopy (bright gold read as a yellow nose from behind)
                    { "HeroDark",  Lit("HeroDark",  new Color(0.10f, 0.11f, 0.14f), 0.40f) },
                    { "HeroGlow",  Mat("HeroGlow", "Universal Render Pipeline/Lit", new Color(1f, 0.62f, 0.2f), m =>
                        {   // the engines: HDR orange past the bloom threshold (1.15), so the two nozzles glow from behind
                            m.EnableKeyword("_EMISSION"); m.globalIlluminationFlags = MaterialGlobalIlluminationFlags.None;
                            m.SetColor("_EmissionColor", new Color(3.2f, 1.45f, 0.35f));
                        }) },
                };
            }
            if (src != null) foreach (var kv in heroMats) if (src.name.StartsWith(kv.Key)) return kv.Value;
            return UrpCopy(src);
        }

        /// <summary>The squad's first plane, fitted 1.75 across and at most 2.3 long (the pack planes are 1.45 / 2.05): "make the plane bigger".</summary>
        static GameObject HeroPlanePrefab(Mats M, Meshes X)
        {
            heroMats = null;   // re-read the colours on every build
            return ModelPlanePrefab("PlaneFighter", HeroModel(), Vector3.zero, 1.75f, 2.3f, Vector3.forward, new string[0], M,
                () => PlanePrefab("PlaneFighter", X.fighter, X.prop, M, M.planeBody, M.planeAccent, M.glass, true), HeroRemap);
        }
    }
}
