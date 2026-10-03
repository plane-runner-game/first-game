// SceneBuilder.HudPatches.cs (Editor only)
// Small HUD fixes applied to the open scene in place, without Build Everything (which regenerates the whole world and drops the worlds
// whose asset packs are not imported on this machine). Each patch is the same code the full build runs, so the two never drift.
using TMPro;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace SkySquad.EditorTools
{
    public static partial class SceneBuilder
    {
        /// <summary>The heavy UI type: Lilita One with a navy outline as thick as the title's and a darker drop shadow. For small type on a
        /// bright box, where the standard outline (0.30) comes out about a pixel wide.</summary>
        static Material UiHeavyPreset()
        {
            var m = FontPreset(font, "LilitaOne UI Heavy", 0.5f, UiNavy, true, 0.85f);
            m.SetFloat(ShaderUtilities.ID_FaceDilate, 0.1f);
            EditorUtility.SetDirty(m);
            AssetDatabase.SaveAssetIfDirty(m);
            return m;
        }

        /// <summary>The UPGRADE word and the price on a card's buy box (2026-10-03: "barely visible, I can barely read the number"): when the bank
        /// is short HUD greys them (cantText 0.72), the same grey as the green / yellow box, and the standard outline left nothing between them.
        /// The heavy outline and two points more keep them grey but readable; white when the price can be paid.</summary>
        static void StyleCardBuyText(TextMeshProUGUI label, TextMeshProUGUI cost)
        {
            label.fontSharedMaterial = fontUiHeavy; label.fontSize = 19f; label.rectTransform.sizeDelta = new Vector2(108f, 28f);
            cost.fontSharedMaterial = fontUiHeavy; cost.fontSize = 17f; cost.rectTransform.sizeDelta = new Vector2(72f, 26f);
            cost.enableAutoSizing = true; cost.fontSizeMin = 12f; cost.fontSizeMax = 17f;   // a long price shrinks before it reaches the coin
        }

        /// <summary>The UI the HUD patches draw with, loaded as the last Build Everything left it (only the heavy preset is made when missing).</summary>
        static bool LoadUiForPatch()
        {
            Material M(string n) => AssetDatabase.LoadAssetAtPath<Material>(Gen + "/Fonts/" + n + ".mat");
            Sprite S(string n) => AssetDatabase.LoadAssetAtPath<Sprite>(Gen + "/Textures/" + n + ".png");
            font = AssetDatabase.LoadAssetAtPath<TMP_FontAsset>(Gen + "/Fonts/LilitaOne SDF.asset");
            fontOutline = M("LilitaOne Outline"); fontOutlineSmall = M("LilitaOne Outline Thin");
            fontUiPlain = M("LilitaOne UI"); fontUiLightPlain = M("LilitaOne UI Thin"); fontUiTitle = M("LilitaOne UI Title"); fontUiInk = M("LilitaOne Ink");
            fontUiHeavy = M("LilitaOne UI Heavy");
            if (fontUiHeavy == null && font != null) fontUiHeavy = UiHeavyPreset();
            uiCircle = S("UI_Circle"); uiSoft = S("UI_Soft"); uiPill = S("UI_Pill"); uiChamfer = S("UI_Chamfer");
            LoadGui();
            return font != null && fontUiTitle != null && fontUiLightPlain != null && fontUiHeavy != null && uiCircle != null;
        }

        /// <summary>The open scene's HUD, or null (with the reason in the console) when a patch cannot run.</summary>
        static HUD HudForPatch(string patch)
        {
            if (EditorApplication.isPlayingOrWillChangePlaymode) { Debug.LogError("[SkySquad] " + patch + ": leave Play mode first"); return null; }
            if (!LoadUiForPatch()) { Debug.LogError("[SkySquad] " + patch + ": the UI fonts / sprites are missing - run Build Everything once"); return null; }
            var hud = Object.FindAnyObjectByType<HUD>(FindObjectsInactive.Include);
            if (hud == null) Debug.LogError("[SkySquad] " + patch + ": no HUD in the open scene (open Assets/_Game/Scenes/Main.unity)");
            return hud;
        }

        static void SaveHudScene(HUD hud, string what)
        {
            EditorUtility.SetDirty(hud);
            var scene = hud.gameObject.scene;
            EditorSceneManager.MarkSceneDirty(scene);
            EditorSceneManager.SaveScene(scene);
            Debug.Log("[SkySquad] " + what + " in " + scene.path);
        }

        /// <summary>Every small HUD fix since the last full build, applied to the open scene. Each step is safe to run again (it sets
        /// values or removes what is gone from the builder), so the menu can simply be run after any change listed here.</summary>
        [MenuItem("Sky Squad/Patch HUD")]
        public static void PatchHud()
        {
            var hud = HudForPatch("Patch HUD");
            if (hud == null) return;
            // 2026-10-03: the upgrade cards' UPGRADE word and price, readable when greyed (StyleCardBuyText)
            for (int i = 0; i < 3; i++)
            {
                var label = i < hud.cardBuyLabel.Length ? hud.cardBuyLabel[i] : null;
                var cost = i < hud.cardCost.Length ? hud.cardCost[i] : null;
                if (label == null || cost == null) { Debug.LogError("[SkySquad] Patch HUD: upgrade card " + i + " is not wired"); return; }
                StyleCardBuyText(label, cost);
                EditorUtility.SetDirty(label); EditorUtility.SetDirty(cost);
            }
            // 2026-10-03: the settings screen's "SKY SQUAD / mtjrcloud" credit is gone
            var credits = hud.settingsPanel != null ? hud.settingsPanel.transform.Find("SCredits") : null;
            if (credits != null) Object.DestroyImmediate(credits.gameObject);
            SaveHudScene(hud, "HUD patched");
        }
    }
}
