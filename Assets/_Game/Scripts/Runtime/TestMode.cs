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

        // the strong plane (2026-10-10: "make me stronger so I can try the bosses, I want my plane strong"): its own switch, Sky Squad >
        // Strong Plane; Progress.DamageMult / FireRateMult multiply by these while it is on. The saved upgrades are not touched.
        public const string StrongKey = "SkySquad.TestStrong";
        public const float StrongDamage = 50f, StrongFireRate = 2f;
        public static bool Strong;

#if UNITY_EDITOR
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
        static void Load() { On = UnityEditor.EditorPrefs.GetBool(Key, false); Strong = UnityEditor.EditorPrefs.GetBool(StrongKey, false); }
#endif
    }
}
