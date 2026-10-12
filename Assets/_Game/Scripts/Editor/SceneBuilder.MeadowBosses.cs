// SceneBuilder.MeadowBosses.cs (Editor only)
// The sunny meadow's five bosses (2026-10-11, "do the bosses for the rest of the maps"), modelled from code in Blender
// (Tools/blender/meadow_bosses.py -> Art/Enemies/MeadowBosses/Boss_<id>.fbx) in place of the bush, the mushrooms, the rock and the tree of
// BuildNatureBosses (kept as the fallback when an FBX is missing): the QUEEN BUMBLEBEE (four wings buzzing, a crown), the GIANT LADYBUG (spotted
// wing cases and amber wings beating), the EMERALD DRAGONFLY (four long wings), the SUNFLOWER TITAN (the petals turn face-on, leaf arms sway)
// and WINDMILL HILL (a floating hill with a windmill, the sails turn face-on, bees circle). The meadow is five bosses long already.
using UnityEngine;

namespace SkySquad.EditorTools
{
    public static partial class SceneBuilder
    {
        const string MeadowBossDir = Root + "/Art/Enemies/MeadowBosses";
        static readonly string[] MeadowBossIds = { "bee", "ladybug", "dragonfly", "evilflower", "snail" };
        static readonly string[] MeadowBossTitles = { "QUEEN BUMBLEBEE", "GIANT LADYBUG", "EMERALD DRAGONFLY", "DEMON SUNFLOWER", "SNAIL KING" };

        /// <summary>The five, by boss number - 1; null when an FBX is missing (the old five stand in).</summary>
        static GameObject[] BuildMeadowBosses(Mats M, Meshes X)
        {
            // width across, no taller than, no longer than (model units), how fast the wings beat
            float[] width = { 4.2f, 3.6f, 4.4f, 3.0f, 4.2f }, maxHeight = { 2.4f, 2.4f, 2.2f, 4.2f, 4.6f }, maxLength = { 4.0f, 4.0f, 4.0f, 3.0f, 4f };
            float[] beat = { 9f, 5f, 8f, 2f, 2f };
            var five = new GameObject[MeadowBossIds.Length];
            for (int i = 0; i < five.Length; i++)
            {
                five[i] = ModelBossPrefab(MeadowBossDir, MeadowBossIds[i], "BossMeadow_" + MeadowBossIds[i], M, X, width[i], maxHeight[i], maxLength[i], beat[i]);
                if (five[i] == null) { Debug.LogWarning("[SkySquad] meadow boss " + MeadowBossTitles[i] + " could not be built (no " + MeadowBossDir + "/Boss_" + MeadowBossIds[i] + ".fbx): the meadow keeps its old bosses"); return null; }
            }
            return five;
        }
    }
}
