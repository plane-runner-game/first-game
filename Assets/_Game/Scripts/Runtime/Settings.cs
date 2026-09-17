// Settings.cs
// Player settings (the SETTINGS panel: HUD.OnSettingsButton / OnDragSlider / OnSettingsDone). Only one so far:
// how far the squad moves for a swipe (GameConfig.dragUnitsPerScreen is the default, the slider overrides it,
// saved in PlayerPrefs "sq_drag"). Requested 2026-09-18: "a settings button, and in it control of the plane's speed".
using UnityEngine;

namespace SkySquad
{
    public static class Settings
    {
        public const float DragMin = 1f, DragMax = 20f;   // 10..60 until 2026-09-18: "speed 60 is far too high, I want the most 20 and the least 1"

        static bool loaded;
        static float drag;   // 0 = not set: use the config's value

        /// <summary>Units the squad moves for a drag across the whole screen height: the player's setting, or the config default.</summary>
        public static float DragUnits(GameConfig cfg)
        {
            if (!loaded) { drag = PlayerPrefs.GetFloat("sq_drag", 0f); if (drag > 0f) drag = Mathf.Clamp(drag, DragMin, DragMax); loaded = true; }   // a value saved under the old 10..60 range is pulled into the new one
            return drag > 0f ? drag : (cfg != null ? cfg.dragUnitsPerScreen : 30f);
        }

        public static void SetDragUnits(float v) { drag = Mathf.Clamp(v, DragMin, DragMax); loaded = true; }

        public static void Save()
        {
            if (drag > 0f) PlayerPrefs.SetFloat("sq_drag", drag);
            PlayerPrefs.Save();
        }
    }
}
