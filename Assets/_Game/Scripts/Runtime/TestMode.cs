// TestMode.cs
// For trying every boss in the editor (2026-09-27: "make me strong so I can try all the bosses", then "I want to be just one
// plane, but not be destroyed"): one plane that loses nothing - hits still show their number and flash. Its guns are the ones
// bought ("put the plane's strength back as it was": the fire-rate / damage boost it had at first is gone). Switched from
// the menu Sky Squad > Test Mode (Editor/TestModeMenu.cs) and remembered in EditorPrefs; the saved progress is never touched,
// so switching it off is the game as it was. It does not exist in a player build: On is always false there.
using UnityEngine;

namespace SkySquad
{
    public static class TestMode
    {
        public const string Key = "SkySquad.TestMode";
        public const int StartPlanes = 1;         // one plane, as the game starts - it just cannot be lost (SquadController.Damage)

        public static bool On;

#if UNITY_EDITOR
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
        static void Load() => On = UnityEditor.EditorPrefs.GetBool(Key, false);
#endif
    }
}
