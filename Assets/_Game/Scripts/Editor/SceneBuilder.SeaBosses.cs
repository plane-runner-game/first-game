// SceneBuilder.SeaBosses.cs (Editor only)
// The sea world's five bosses (2026-10-10: "bosses for Sky Sea - something completely professional"), modelled from code in Blender
// (Tools/blender/sea_bosses.py -> Art/Enemies/SeaBosses/Boss_<id>.fbx) in place of the Star Sparrow ships and pack models it flew before:
// the SKY WHALE (star spots on its back, long fins rowing, the fluke beating), the SKY GALLEON (a flying sailing ship, canvas wings beating),
// the THUNDER ROC (a storm seabird, lightning on its wings), the ABYSS LEVIATHAN (a sea serpent in the sky, fan fins rowing) and the CITADEL
// TURTLE (a white-and-gold citadel on its shell, the lighthouse beam turning). The bomber, the gunship and the battleship that stood in 1, 3 and
// 5 the same afternoon were thrown out ("only the second and the fourth are beautiful"). The sea is five bosses long: the fifth ends it.
// 2026-10-14 all five remade like the alien ones, each with its own way to fly and its surfaces baked into textures (boss_bake.py): a humpback
// lunging on its fins, a porcupinefish emperor on its fluttering fins, a storm albatross diving, an oarfish leviathan on flying-fish wings,
// an ancient loggerhead flying on its front flippers with the citadel on its shell.
using UnityEditor;
using UnityEngine;

namespace SkySquad.EditorTools
{
    public static partial class SceneBuilder
    {
        const string SeaBossDir = Root + "/Art/Enemies/SeaBosses";
        static readonly string[] SeaBossIds = { "whale", "puffer", "roc", "leviathan", "turtle" };
        static readonly string[] SeaBossTitles = { "SKY WHALE", "PUFFERFISH EMPEROR", "THUNDER ROC", "ABYSS LEVIATHAN", "CITADEL TURTLE" };
        static readonly string[] SeaStageNames = { "OPEN WATER" };
        const int SeaLastBoss = 5;   // "make this level only 5 bosses and it ends" (WorldEntry.lastBoss)

        /// <summary>The five, by boss number - 1 (boss n is model (n-1) % 5); null when an FBX is missing (that world keeps its old cast).</summary>
        static GameObject[] BuildSeaBosses(Mats M, Meshes X)
        {
            // width across, no taller than, no longer than (model units), how fast the wings / fins beat
            float[] width = { 4.6f, 3.6f, 5.0f, 3.8f, 4.8f }, maxHeight = { 3.0f, 3.6f, 3.0f, 4.0f, 3.6f }, maxLength = { 5.0f, 3.4f, 4.4f, 4.6f, 4.6f };
            float[] beat = { 1.6f, 3.5f, 2.2f, 2.4f, 1.5f };
            var five = new GameObject[SeaBossIds.Length];
            for (int i = 0; i < five.Length; i++)
            {
                five[i] = ModelBossPrefab(SeaBossDir, SeaBossIds[i], "BossSea_" + SeaBossIds[i], M, X, width[i], maxHeight[i], maxLength[i], beat[i]);
                if (five[i] == null) { Debug.LogWarning("[SkySquad] sea boss " + SeaBossTitles[i] + " could not be built (no " + SeaBossDir + "/Boss_" + SeaBossIds[i] + ".fbx): the sea keeps its old bosses"); return null; }
            }
            return StageCycle(five);
        }

        [MenuItem("Sky Squad/Rebuild Sea Bosses")]
        public static void RebuildSeaBosses()
        {
            CreateFont();
            var M = CreateMaterials(); var X = CreateMeshes();
            var five = BuildSeaBosses(M, X);
            AssetDatabase.SaveAssets();
            Debug.Log("[SkySquad] sea bosses rebuilt: " + (five == null ? "FAILED (see the warning above)" : five.Length + " prefabs"));
        }

        /// <summary>Pictures of the sea's five boss prefabs as the game's renderer draws them, from the player's side (ShipSheet:
        /// Captures/bosses/sea/000-004.jpg, git-ignored).</summary>
        [MenuItem("Sky Squad/Render Sea Bosses")]
        public static void RenderSeaBosses()
        {
            ShipSheet.Side = 1f;   // a model boss's nose is +Z (ModelBossPrefab turns the FBX round)
            var paths = System.Array.ConvertAll(SeaBossIds, i => Gen + "/Prefabs/BossSea_" + i + ".prefab");
            Debug.Log("[SkySquad] sea boss pictures in Captures/bosses/sea " + ShipSheet.Render(paths, "Captures/bosses/sea"));
        }
    }
}
