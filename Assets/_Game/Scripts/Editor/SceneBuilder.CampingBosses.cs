// SceneBuilder.CampingBosses.cs (Editor only)
// The camping forest's five bosses (2026-10-10: "bosses now for the camping forest"), the night by the fire, modelled from code in Blender
// (Tools/blender/camping_bosses.py -> Art/Enemies/CampingBosses/Boss_<id>.fbx) in place of the tent, the lamppost, the bonfire and the two
// Star Sparrows the theme borrowed: the FIREFLY QUEEN (a lantern abdomen, four pale wings beating), the GREAT HORNED OWL (glowing amber eyes,
// a lantern in its talons, wings beating), the LANTERN BALLOON (a patchwork balloon carrying a log cabin, lanterns, a propeller), the STAR
// BEAR (a bear of the night sky, constellations on its back, legs running, a ring of stars turning) and the FOREST GUARDIAN (a tree spirit,
// lanterns hanging from its branches, roots swaying). A land world is five bosses long already (LandEntry, lastBoss 5).
using UnityEngine;

namespace SkySquad.EditorTools
{
    public static partial class SceneBuilder
    {
        const string CampingBossDir = Root + "/Art/Enemies/CampingBosses";
        static readonly string[] CampingBossIds = { "firefly", "owl", "balloon", "bear", "guardian" };
        static readonly string[] CampingBossTitles = { "FIREFLY QUEEN", "GREAT HORNED OWL", "LANTERN BALLOON", "STAR BEAR", "FOREST GUARDIAN" };

        /// <summary>A land world's own five FBX bosses where it has them (the camping forest so far), with their names; null otherwise, or when an
        /// FBX is missing, and the theme's pack models stand in.</summary>
        static GameObject[] LandModelBosses(LandTheme t, Mats M, Meshes X, out string[] names)
        {
            names = null;
            if (t.id != "camping") return null;
            // width across, no taller than, no longer than (model units), how fast wings beat / legs and roots swing
            float[] width = { 3.6f, 4.2f, 2.6f, 3.2f, 3.8f }, maxHeight = { 2.4f, 2.6f, 3.6f, 2.4f, 3.6f }, maxLength = { 3.6f, 3.0f, 3.0f, 4.0f, 3.0f };
            float[] beat = { 7f, 2.2f, 2f, 3.2f, 1.5f };
            var five = new GameObject[CampingBossIds.Length];
            for (int i = 0; i < five.Length; i++)
            {
                five[i] = ModelBossPrefab(CampingBossDir, CampingBossIds[i], "BossCamping_" + CampingBossIds[i], M, X, width[i], maxHeight[i], maxLength[i], beat[i]);
                if (five[i] == null) { Debug.LogWarning("[SkySquad] camping boss " + CampingBossTitles[i] + " could not be built (no " + CampingBossDir + "/Boss_" + CampingBossIds[i] + ".fbx): the theme keeps its old bosses"); return null; }
            }
            names = CampingBossTitles;
            return five;
        }
    }
}
