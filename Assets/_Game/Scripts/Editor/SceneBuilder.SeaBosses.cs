// SceneBuilder.SeaBosses.cs (Editor only)
// The sea world's five bosses (2026-10-10: "bosses for Sky Sea - something completely professional"), modelled from code in Blender
// (Tools/blender/sea_bosses.py -> Art/Enemies/SeaBosses/Boss_<id>.fbx) in place of the Star Sparrow ships and pack models it flew before:
// the THUNDER FORTRESS (a six-engine bomber, props spinning, gun turrets), the SKY GALLEON (a flying sailing ship, canvas wings beating),
// the HURRICANE GUNSHIP (a huge helicopter with two rotors side by side), the ABYSS LEVIATHAN (a sea serpent in the sky, fan fins rowing)
// and the POSEIDON BATTLESHIP (triple turrets, a turning radar, hover engines, a golden trident). Every stage brings all five in that order.
using UnityEngine;

namespace SkySquad.EditorTools
{
    public static partial class SceneBuilder
    {
        const string SeaBossDir = Root + "/Art/Enemies/SeaBosses";
        static readonly string[] SeaBossIds = { "fortress", "galleon", "gunship", "leviathan", "battleship" };
        static readonly string[] SeaBossTitles = { "THUNDER FORTRESS", "SKY GALLEON", "HURRICANE GUNSHIP", "ABYSS LEVIATHAN", "POSEIDON BATTLESHIP" };
        static readonly string[] SeaStageNames = { "OPEN WATER", "STORM FRONT", "CORAL STRAIT", "THUNDER BAY", "DEEP BLUE", "THE TRIDENT" };

        /// <summary>The five, by boss number - 1 (boss n is model (n-1) % 5); null when an FBX is missing (that world keeps its old cast).</summary>
        static GameObject[] BuildSeaBosses(Mats M, Meshes X)
        {
            // width across, no taller than, no longer than (model units), how fast the wings / fins beat
            float[] width = { 4.0f, 3.6f, 4.0f, 3.0f, 3.6f }, maxHeight = { 2.4f, 3.0f, 2.4f, 2.6f, 2.8f }, maxLength = { 4.6f, 4.4f, 4.4f, 4.6f, 4.6f };
            float[] beat = { 2f, 1.8f, 2f, 2.4f, 2f };
            var five = new GameObject[SeaBossIds.Length];
            for (int i = 0; i < five.Length; i++)
            {
                five[i] = ModelBossPrefab(SeaBossDir, SeaBossIds[i], "BossSea_" + SeaBossIds[i], M, X, width[i], maxHeight[i], maxLength[i], beat[i]);
                if (five[i] == null) { Debug.LogWarning("[SkySquad] sea boss " + SeaBossTitles[i] + " could not be built (no " + SeaBossDir + "/Boss_" + SeaBossIds[i] + ".fbx): the sea keeps its old bosses"); return null; }
            }
            return StageCycle(five);
        }
    }
}
