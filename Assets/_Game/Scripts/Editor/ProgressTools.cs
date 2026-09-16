// ProgressTools.cs - editor menu to wipe the saved meta progress (coins, the three upgrade levels,
// attempts, best horde) so the next attempt starts from zero. Works in and out of play mode.
using UnityEditor;
using UnityEngine;

namespace SkySquad.EditorTools
{
    public static class ProgressTools
    {
        [MenuItem("Sky Squad/Reset Progress (coins + upgrades)")]
        public static void ResetProgress()
        {
            Progress.Reset();   // zeroes the statics and saves the zeros to PlayerPrefs
            Debug.Log("Sky Squad: progress reset - coins 0, all upgrade levels 0, attempts 0.");
        }
    }
}
