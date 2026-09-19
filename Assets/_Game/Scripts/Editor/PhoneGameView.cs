// PhoneGameView.cs - every time play mode starts, the Game view switches to the phone: a 540x960 portrait
// size (the player's own defaultScreenWidth/Height), added to the Game view's size list if it is not there.
// "Whenever I press play I want the screen for the phone" (2026-09-19). Unity keeps no public API for the
// Game view's size dropdown, so this goes through reflection on GameViewSizes / GameView; it fails quietly
// (a warning, no exception) if a Unity update renames something. Sky Squad/Phone Game View toggles it.
using System;
using System.Reflection;
using UnityEditor;
using UnityEngine;

namespace SkySquad.EditorTools
{
    [InitializeOnLoad]
    public static class PhoneGameView
    {
        const string PrefKey = "SkySquad.PhoneGameView";
        const string MenuPath = "Sky Squad/Phone Game View on Play";
        const int W = 540, H = 960;

        static bool On { get => EditorPrefs.GetBool(PrefKey, true); set => EditorPrefs.SetBool(PrefKey, value); }

        static PhoneGameView()
        {
            EditorApplication.playModeStateChanged += s => { if (s == PlayModeStateChange.ExitingEditMode && On) Apply(); };
        }

        [MenuItem(MenuPath)] static void Toggle() { On = !On; if (On) Apply(); }
        [MenuItem(MenuPath, true)] static bool ToggleValidate() { Menu.SetChecked(MenuPath, On); return true; }

        /// <summary>Puts the Game view on the 540x960 portrait size right now.</summary>
        [MenuItem("Sky Squad/Phone Game View now")]
        public static void Apply()
        {
            try
            {
                var asm = typeof(Editor).Assembly;
                var sizesType = asm.GetType("UnityEditor.GameViewSizes");
                var singleton = typeof(ScriptableSingleton<>).MakeGenericType(sizesType);
                var sizes = singleton.GetProperty("instance", BindingFlags.Public | BindingFlags.Static).GetValue(null);
                var group = sizesType.GetProperty("currentGroup", BindingFlags.Public | BindingFlags.Instance).GetValue(sizes);
                var groupType = group.GetType();
                int total = (int)groupType.GetMethod("GetTotalCount").Invoke(group, null);
                int index = -1;
                for (int i = 0; i < total; i++)
                {
                    var gvs = groupType.GetMethod("GetGameViewSize").Invoke(group, new object[] { i });
                    var t = gvs.GetType();
                    int w = (int)t.GetProperty("width").GetValue(gvs), h = (int)t.GetProperty("height").GetValue(gvs);
                    int kind = (int)t.GetProperty("sizeType").GetValue(gvs);   // 0 AspectRatio, 1 FixedResolution
                    if (kind == 1 && w == W && h == H) { index = i; break; }
                }
                if (index < 0)
                {   // not in the list yet: add a custom FixedResolution entry named for the game
                    var gvsType = asm.GetType("UnityEditor.GameViewSize");
                    var sizeTypeEnum = asm.GetType("UnityEditor.GameViewSizeType");
                    var gvs = Activator.CreateInstance(gvsType, Enum.ToObject(sizeTypeEnum, 1), W, H, "Sky Squad phone");
                    groupType.GetMethod("AddCustomSize").Invoke(group, new[] { gvs });
                    sizesType.GetMethod("SaveToHDD", BindingFlags.Public | BindingFlags.Instance)?.Invoke(sizes, null);
                    index = total;   // the custom sizes come after the built-ins
                }
                var gameViewType = asm.GetType("UnityEditor.GameView");
                var gameView = EditorWindow.GetWindow(gameViewType, false, null, false);
                var prop = gameViewType.GetProperty("selectedSizeIndex", BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance);
                if ((int)prop.GetValue(gameView) != index) { prop.SetValue(gameView, index); gameView.Repaint(); }
            }
            catch (Exception e) { Debug.LogWarning("[SkySquad] PhoneGameView could not set the Game view size: " + e.Message); }
        }
    }
}
