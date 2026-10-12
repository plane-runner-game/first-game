// SceneBuilder.InfernoBosses.cs (Editor only)
// The lava world's (INFERNO) five bosses (2026-10-10: "now for the lava, inferno" - five beautiful ones that suit the world, five bosses and
// it ends, as the sea), modelled from code in Blender (Tools/blender/lava_bosses.py -> Art/Enemies/InfernoBosses/Boss_<id>.fbx) in place of
// the thirty ship and relic bosses of SceneBuilder.LavaBosses.cs (kept as the fallback when an FBX is missing): the HELLFIRE GALLEON (the sky galleon
// in obsidian and crimson, burning sails and rails, a horned skull at the bow; the magma phoenix stood here until the same evening, "ugly"), the EMBER SCARAB (obsidian shell cracked with lava, a golden horn, amber wings
// buzzing), the INFERNO GOLEM (molten boulders, a burning heart, a ring of rocks turning round him), the FIRE IFRIT (a fire genie with
// fireballs in his hands, a ring of flame turning round his waist) and the VOLCANO FORTRESS (a floating volcanic island, black towers on its
// rim, rocks drifting round it). The world ends when the fifth falls.
using UnityEngine;

namespace SkySquad.EditorTools
{
    public static partial class SceneBuilder
    {
        const string InfernoBossDir = Root + "/Art/Enemies/InfernoBosses";
        static readonly string[] InfernoBossIds = { "salamander", "scarab", "golem", "ifrit", "demon" };
        static readonly string[] InfernoBossTitles = { "MAGMA SALAMANDER KING", "EMBER SCARAB", "INFERNO GOLEM", "FIRE IFRIT", "DEMON LORD" };
        static readonly string[] InfernoStageNames = { "EMBER SHORE" };
        const int InfernoLastBoss = 5;

        /// <summary>The five, by boss number - 1 (boss n is model (n-1) % 5); null when an FBX is missing (the old thirty stand in).</summary>
        static GameObject[] BuildInfernoBosses(Mats M, Meshes X)
        {
            // width across, no taller than, no longer than (model units), how fast the wings beat
            float[] width = { 3.4f, 3.8f, 3.8f, 3.6f, 4.6f }, maxHeight = { 2.4f, 2.4f, 3.2f, 3.4f, 3.6f }, maxLength = { 4.4f, 4.0f, 3.6f, 3.0f, 2f };
            float[] beat = { 3f, 9f, 2f, 2f, 1.6f };
            var five = new GameObject[InfernoBossIds.Length];
            for (int i = 0; i < five.Length; i++)
            {
                five[i] = ModelBossPrefab(InfernoBossDir, InfernoBossIds[i], "BossInferno_" + InfernoBossIds[i], M, X, width[i], maxHeight[i], maxLength[i], beat[i]);
                if (five[i] == null) { Debug.LogWarning("[SkySquad] inferno boss " + InfernoBossTitles[i] + " could not be built (no " + InfernoBossDir + "/Boss_" + InfernoBossIds[i] + ".fbx): the lava keeps its old bosses"); return null; }
            }
            return StageCycle(five);
        }
    }
}
