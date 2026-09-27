// TestModeMenu.cs
// Sky Squad > Test Mode: the strong squad for trying every boss (TestMode.cs). A tick in the menu shows it is on.
using UnityEditor;

namespace SkySquad.EditorTools
{
    static class TestModeMenu
    {
        const string Item = "Sky Squad/Test Mode (1 plane, cannot be destroyed)";

        [MenuItem(Item, false, 100)]
        static void Toggle()
        {
            bool on = !EditorPrefs.GetBool(TestMode.Key, false);
            EditorPrefs.SetBool(TestMode.Key, on);
            TestMode.On = on;
            UnityEngine.Debug.Log("[SkySquad] Test Mode " + (on ? "ON: one plane that cannot be destroyed" : "OFF: the game as it is"));
        }

        [MenuItem(Item, true)]
        static bool Validate()
        {
            Menu.SetChecked(Item, EditorPrefs.GetBool(TestMode.Key, false));
            return true;
        }
    }
}
