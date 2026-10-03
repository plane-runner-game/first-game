// SceneBuilder.DeathScreen.cs (Editor only)
// The death screen (2026-10-03, "it looks like shit and doesn't match the start theme"): the kit's own Play_Continue screen (GUI Pro -
// Casual Game, Prefabs_DemoScene_Panels/Play_Continue) turned to the portrait. No popup box: the game dims, a red glow swells under a big
// red MAYDAY!, why the squad went down under it, a ring counting down the seconds the revive is offered, the yellow REVIVE with the
// kit's clapperboard hanging off its corner (a rewarded ad, Ads.cs) and the blue RESTART with the kit's refresh picto. HUD.cs animates it.
// Sky Squad > Rebuild Death Screen swaps just this panel in the open scene and saves it - Build Everything regenerates the whole world,
// which drops the worlds whose asset packs are not imported on this machine.
using UnityEditor;
using UnityEngine;
using UnityEngine.UI;

namespace SkySquad.EditorTools
{
    public static partial class SceneBuilder
    {
        static Sprite uiRing;

        /// <summary>A white ring (128 px, 16 px thick) for the countdown: drawn Filled / Radial360 it drains like a clock.</summary>
        static Sprite RingSprite()
        {
            var s = AssetDatabase.LoadAssetAtPath<Sprite>(Gen + "/Textures/UI_Ring.png");
            if (s != null) return s;
            return SaveSprite(Shape(128, 128, (x, y) => White(Edge(Mathf.Abs(Mathf.Sqrt(x * x + y * y) - 55f) - 8f))), "UI_Ring", Vector4.zero);
        }

        /// <summary>A kit button the lobby's way: the kit's Button01 pill (its own lip and shine), the label in the title face, the press
        /// squash. holder is what HUD slides; the button itself squashes inside it (UIButtonFx owns its scale).</summary>
        static Button KitButton(string name, RectTransform holder, Sprite pill, Vector2 size, string label, float fontSize, out UIButtonFx fx, out RectTransform face)
        {
            face = UI(name, holder, Mid, Mid, Vector2.zero, size);
            var im = GImg("Face", face, pill, Color.white, Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero, Fit(145f, size.y));
            im.raycastTarget = true;
            if (!string.IsNullOrEmpty(label)) TxtTitle("Label", face, label, fontSize, Color.white, Mid, new Vector2(0f, 5f), new Vector2(size.x - 24f, size.y));   // a touch up: the pill's darker lip runs along its bottom
            var btn = face.gameObject.AddComponent<Button>(); btn.transition = Selectable.Transition.None; btn.targetGraphic = im;
            fx = face.gameObject.AddComponent<UIButtonFx>(); fx.tint = im; fx.pressedColor = UiPressed;
            return btn;
        }

        /// <summary>Builds the death screen under the HUD canvas and wires it into hud. Returns the panel (inactive: HUD shows it on GameOver).</summary>
        static GameObject BuildDeathScreen(Transform canvas, HUD hud)
        {
            uiRing = RingSprite();
            var over = Panel("OverPanel", canvas, 0.84f);   // the kit's Dimed: the game stays visible under it (linear colour space: 0.72 left the crates reading through the ring)
            hud.overPanel = over;
            hud.overGroup = over.AddComponent<CanvasGroup>();
            var root = over.transform;

            // the title: the kit's red glow (its particle burst, kept as one soft sprite that swells in and breathes) under MAYDAY!
            var glow = GImg("Glow", root, Gp("Popup/Common_Popup_Glow.png"), new Color(0.95f, 0.06f, 0.12f, 0.5f), Mid, Mid, new Vector2(0f, 212f), new Vector2(520f, 290f), 1f, false);   // tight behind the word: wider, it washed the sky pink
            glow.preserveAspect = false;
            hud.overGlow = glow.rectTransform;
            var title = TxtTitle("Title", root, "MAYDAY!", 84f, new Color(1f, 0.20f, 0.24f), Mid, new Vector2(0f, 215f), new Vector2(520f, 110f), 2f);
            title.enableAutoSizing = true; title.fontSizeMin = 40f; title.fontSizeMax = 84f;
            hud.overTitle = title.rectTransform;
            hud.overReason = TxtBold("Reason", root, "rammed by a fighter", 22f, Color.white, Mid, new Vector2(0f, 148f), new Vector2(460f, 32f), 0f, false);
            hud.overStats = null;   // the attempt / horde / kills line went with the old popup

            // the countdown: a dark disc, a faint track, the ring that drains (gold, red at the end), the seconds in it
            var timer = UI("Timer", root, Mid, Mid, new Vector2(0f, 22f), new Vector2(150f, 150f));
            hud.overTimer = timer;
            Icon("Disc", timer, uiCircle, new Color(0.04f, 0.08f, 0.16f, 0.9f), Mid, Vector2.zero, 132f);
            Icon("Track", timer, uiRing, new Color(1f, 1f, 1f, 0.16f), Mid, Vector2.zero, 150f);
            var fill = Icon("Fill", timer, uiRing, UiYellow, Mid, Vector2.zero, 150f);
            fill.type = Image.Type.Filled; fill.fillMethod = Image.FillMethod.Radial360; fill.fillOrigin = (int)Image.Origin360.Top; fill.fillClockwise = false; fill.fillAmount = 1f;
            hud.overTimerFill = fill;
            hud.overTimerText = TxtTitle("Count", timer, "5", 68f, Color.white, Mid, new Vector2(0f, 4f), new Vector2(150f, 100f));
            hud.overReviveInfo = TxtBold("ReviveInfo", root, "REVIVE WITH 1 PLANE", 20f, Color.white, Mid, new Vector2(0f, -72f), new Vector2(460f, 30f), 0f, false);

            // REVIVE: the kit's yellow continue button with its clapperboard over the top-right corner, breathing
            var revive = UI("Revive", root, Mid, Mid, new Vector2(0f, -150f), new Vector2(330f, 100f));
            var reviveBtn = KitButton("ReviveBtn", revive, G("Button/Button01_145_Yellow"), new Vector2(330f, 100f), "REVIVE", 42f, out var reviveFx, out var reviveFace);
            reviveFx.pulse = true; reviveFx.pulseAmount = 0.03f; reviveFx.pulseSpeed = 4f;
            Icon("Ad", reviveFace, Gp("IconMisc/Icon_ImageIcon_Ad_00_s.png"), Color.white, Mid, new Vector2(147f, 43f), 54f);   // the kit's spot: 213.8, 61.8 on its 480 x 145 button
            UnityEditor.Events.UnityEventTools.AddPersistentListener(reviveBtn.onClick, hud.OnReviveButton);
            hud.overRevive = revive;

            // RESTART: the kit's blue with its refresh picto (Play_Pause's restart), smaller - the way out, not the offer
            var restart = UI("Restart", root, Mid, Mid, new Vector2(0f, -268f), new Vector2(250f, 80f));
            var restartBtn = KitButton("RestartBtn", restart, G("Button/Button01_145_Blue"), new Vector2(250f, 80f), "", 30f, out var restartFx, out var restartFace);
            Glyph("Icon", restartFace, "Refresh", Mid, new Vector2(-78f, 5f), 36f);
            TxtTitle("Label", restartFace, "RESTART", 32f, Color.white, Mid, new Vector2(20f, 5f), new Vector2(170f, 60f));
            restartFx.pulseAmount = 0.03f; restartFx.pulseSpeed = 4f;   // HUD turns the pulse on when RESTART is the only way on
            UnityEditor.Events.UnityEventTools.AddPersistentListener(restartBtn.onClick, hud.OnRestartButton);
            hud.overRestart = restart; hud.overRestartFx = restartFx;

            over.SetActive(false);
            return over;
        }

        [MenuItem("Sky Squad/Rebuild Death Screen")]
        public static void RebuildDeathScreen()
        {
            var hud = HudForPatch("Rebuild Death Screen");   // SceneBuilder.HudPatches.cs
            if (hud == null) return;
            int index = -1;
            if (hud.overPanel != null) { index = hud.overPanel.transform.GetSiblingIndex(); Object.DestroyImmediate(hud.overPanel); }
            var panel = BuildDeathScreen(hud.transform, hud);
            if (index >= 0) panel.transform.SetSiblingIndex(index);   // the same place in the draw order: over the lobby, under pause / settings / splash
            SaveHudScene(hud, "death screen rebuilt");
        }
    }
}
