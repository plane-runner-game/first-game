// SceneBuilder.Worlds.cs (Editor only)
// The worlds as a whole (2026-10-02): the WorldManager that holds each world's scene roots, sky, light, post and cast, and the level-select UI
// (the chip at the top of the lobby and the full-screen list of worlds). World 1 is the sea the game always had, its numbers exactly as they
// were; world 2 is the lava world (SceneBuilder.Lava.cs, SceneBuilder.LavaBosses.cs).
using System;
using System.IO;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.UI;
using TMPro;

namespace SkySquad.EditorTools
{
    public static partial class SceneBuilder
    {
        const string WorldArtDir = Root + "/Art/Worlds";

        /// <summary>A world's card picture from Art/Worlds (captured from the game itself, Sky Squad/Capture world pictures): a 1024-wide sprite. A flat colour when not captured yet.</summary>
        static Sprite WorldSprite(string file, Color fallback)
        {
            string path = WorldArtDir + "/" + file;
            if (!File.Exists(path))
            {
                var t = new Texture2D(8, 8, TextureFormat.RGBA32, false);
                for (int y = 0; y < 8; y++) for (int x = 0; x < 8; x++) t.SetPixel(x, y, Color.Lerp(fallback, fallback * 0.45f, y / 7f));
                t.Apply();
                return SaveSprite(t, "World_" + Path.GetFileNameWithoutExtension(file) + "_flat", Vector4.zero);
            }
            var imp = AssetImporter.GetAtPath(path) as TextureImporter;
            if (imp == null) { AssetDatabase.ImportAsset(path); imp = AssetImporter.GetAtPath(path) as TextureImporter; }
            if (imp != null && (imp.textureType != TextureImporterType.Sprite || imp.maxTextureSize != 1024 || imp.mipmapEnabled))
            {
                imp.textureType = TextureImporterType.Sprite; imp.spriteImportMode = SpriteImportMode.Single; imp.spritePixelsPerUnit = 100f;
                imp.mipmapEnabled = false; imp.alphaIsTransparency = false; imp.wrapMode = TextureWrapMode.Clamp; imp.maxTextureSize = 1024; imp.filterMode = FilterMode.Bilinear;
                var ts = imp.GetDefaultPlatformTextureSettings(); ts.textureCompression = TextureImporterCompression.CompressedHQ; imp.SetPlatformTextureSettings(ts);
                imp.SaveAndReimport();
            }
            return AssetDatabase.LoadAssetAtPath<Sprite>(path);
        }

        /// <summary>The chip at the top of the lobby (the current world's number and name, a chevron) and the full-screen world list it opens. The chip
        /// lives in the lobby panel (so it leaves with it); the list is a root panel. Wires everything into the HUD; WorldManager fills the texts.</summary>
        static void BuildWorldUi(Transform canvas, Transform lobby, HUD hud, WorldEntry[] worlds)
        {
            // --- the chip
            var chip = UI("WorldChip", lobby, TC, TC, new Vector2(0f, -42f), new Vector2(214f, 50f));
            var chipShadow = UIImage("Shadow", chip, new Color(0f, 0f, 0f, 0.30f), Vector2.zero, Vector2.one, new Vector2(0f, -7f), new Vector2(16f, 16f)); chipShadow.sprite = uiSoft; chipShadow.type = Image.Type.Sliced; chipShadow.pixelsPerUnitMultiplier = UiSoftFade / 20f;
            var body = Chunk("Body", chip, Gp("Frame/BasicFrame_Round20.png"), new Color(0.16f, 0.27f, 0.45f), new Color(0.07f, 0.12f, 0.22f), Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero, 4f, 5f, 2.5f, 16f);
            var face = body.Find("Face").GetComponent<Image>(); face.raycastTarget = true;
            var btn = chip.gameObject.AddComponent<Button>(); btn.transition = Selectable.Transition.None; btn.targetGraphic = face;
            UnityEditor.Events.UnityEventTools.AddPersistentListener(btn.onClick, hud.OnWorldButton);
            chip.gameObject.AddComponent<UIButtonFx>();
            var disc = UI("Disc", chip, new Vector2(0f, 0.5f), new Vector2(0f, 0.5f), new Vector2(27f, 1f), new Vector2(38f, 38f));
            Icon("Stroke", disc, uiCircle, UiNavy, Mid, Vector2.zero, 38f + UiStroke * 2f);
            hud.worldChipDisc = Icon("Face", disc, uiCircle, UiSkyBlue, Mid, Vector2.zero, 38f);
            hud.worldChipNumber = TxtBold("Number", disc, "1", 22f, Color.white, Mid, new Vector2(0f, 1f), new Vector2(38f, 38f));
            hud.worldChipName = TxtBold("Name", chip, "SKY SEA", 20f, Color.white, Mid, new Vector2(6f, 1f), new Vector2(118f, 40f));
            hud.worldChipName.enableAutoSizing = true; hud.worldChipName.fontSizeMin = 11f; hud.worldChipName.fontSizeMax = 20f;
            Icon("Chevron", chip, Picto("Arrow_Down"), Color.white, new Vector2(1f, 0.5f), new Vector2(-22f, 1f), 22f);

            // --- the list
            var panel = Panel("WorldPanel", canvas, 1f); hud.worldPanel = panel;
            var pim = panel.GetComponent<Image>(); pim.raycastTarget = true; pim.color = new Color(0.12f, 0.19f, 0.32f, 1f);
            { var dots = UIImage("Dots", panel.transform, new Color(1f, 1f, 1f, 0.05f), Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero); dots.sprite = uiCircle; dots.type = Image.Type.Tiled; dots.pixelsPerUnitMultiplier = 64f / 48f; }
            TxtTitle("Title", panel.transform, "SELECT WORLD", 42f, Color.white, TC, new Vector2(0f, -62f), new Vector2(420f, 64f));
            var coins = CoinBar("WorldCoins", panel.transform, TR, new Vector2(-88f, -34f), new Vector2(140f, 40f), gResCoin, 46f);
            hud.worldCoins = Type("WorldCoinsText", coins, "0", 22f, GText, Mid, new Vector2(-10f, 1f), new Vector2(100f, 40f));
            int n = worlds.Length;
            hud.worldCardFace = new Image[n]; hud.worldCardPicture = new RawImage[n]; hud.worldCardName = new TextMeshProUGUI[n]; hud.worldCardInfo = new TextMeshProUGUI[n]; hud.worldCardTag = new TextMeshProUGUI[n]; hud.worldCardSelected = new GameObject[n];
            for (int i = 0; i < n; i++)
            {
                var e = worlds[i];
                bool compact = n > 2;
                float cardH = compact ? 238f : 330f, wellH = compact ? 112f : 190f, top = cardH * 0.5f;
                float cy = n == 2 ? (i == 0 ? 168f : -192f) : compact ? (1 - i) * 256f : 160f - i * 360f;
                float wellY = top - 14f - wellH * 0.5f, nameY = compact ? -30f : -62f, tagY = compact ? -54f : -94f, infoY = compact ? -91f : -133f, numY = compact ? -40f : -78f;
                Color col = Color.Lerp(e.accent, UiNavy, 0.25f), dark = Color.Lerp(e.accent, UiNavy, 0.62f);
                var card = UI("WorldCard" + i, panel.transform, Mid, Mid, new Vector2(0f, cy), new Vector2(468f, cardH));
                var sh = UIImage("Shadow", card, new Color(0f, 0f, 0f, 0.40f), Vector2.zero, Vector2.one, new Vector2(0f, -12f), new Vector2(24f, 24f)); sh.sprite = uiSoft; sh.type = Image.Type.Sliced; sh.pixelsPerUnitMultiplier = UiSoftFade / 20f;
                var cb = Chunk("Body", card, Gp("Frame/BorderFrame_Round02.png"), col, dark, Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero, 3f, 7f, UiStroke);
                var cf = cb.Find("Face").GetComponent<Image>(); cf.raycastTarget = true; hud.worldCardFace[i] = cf;
                var cbtn = card.gameObject.AddComponent<Button>(); cbtn.transition = Selectable.Transition.None; cbtn.targetGraphic = cf;
                UnityEditor.Events.UnityEventTools.AddIntPersistentListener(cbtn.onClick, hud.OnWorldPick, i);
                card.gameObject.AddComponent<UIButtonFx>();
                // the picture: the world as the player sees it, in a navy-outlined well
                var well = Outlined("Well", card, "Frame/BasicFrame_Round20.png", Color.Lerp(e.accent, UiNavy, 0.7f), Mid, Mid, new Vector2(0f, wellY), new Vector2(436f, wellH), 4f, 2.5f);
                var picRt = UI("Picture", well, Vector2.zero, Vector2.one, Vector2.zero, new Vector2(-10f, -10f)); var pic = picRt.gameObject.AddComponent<RawImage>(); pic.raycastTarget = false; if (e.thumbnail != null) pic.texture = e.thumbnail.texture;
                hud.worldCardPicture[i] = pic;
                hud.worldCardName[i] = TxtTitle("Name", card, e.displayName, 30f, Color.white, Mid, new Vector2(30f, nameY), new Vector2(300f, 42f)); hud.worldCardName[i].alignment = TextAlignmentOptions.Left;
                hud.worldCardName[i].enableAutoSizing = true; hud.worldCardName[i].fontSizeMin = 16f; hud.worldCardName[i].fontSizeMax = 30f;
                hud.worldCardTag[i] = TxtBold("Tag", card, e.tagline, 15f, new Color(1f, 1f, 1f, 0.85f), Mid, new Vector2(30f, tagY), new Vector2(300f, 24f), 0f, false, TextAlignmentOptions.Left);
                var num = UI("Number", card, Mid, Mid, new Vector2(-196f, numY), new Vector2(54f, 54f));
                Icon("Stroke", num, uiCircle, UiNavy, Mid, Vector2.zero, 54f + UiStroke * 2f); Icon("Face", num, uiCircle, e.accent, Mid, Vector2.zero, 54f);
                TxtTitle("Num", num, (i + 1).ToString(), 34f, Color.white, Mid, new Vector2(0f, 2f), new Vector2(54f, 54f));
                var info = Outlined("InfoPill", card, "Frame/BasicFrame_Round20.png", new Color(0.07f, 0.11f, 0.2f, 0.9f), Mid, Mid, new Vector2(0f, infoY), new Vector2(436f, compact ? 30f : 34f), 4f, 2f);
                hud.worldCardInfo[i] = TxtBold("Info", info, "30 BOSSES", 15f, Color.white, Mid, new Vector2(0f, 1f), new Vector2(420f, 30f), 0f, false);
                var sel = UI("Selected", card, TR, TR, new Vector2(-84f, 4f), new Vector2(142f, 38f));
                Outlined("Pill", sel, "Frame/BasicFrame_Round20.png", UiGreen, Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero, 4f, 2.5f);
                TxtBold("Label", sel, "SELECTED", 17f, Color.white, Mid, new Vector2(0f, 1f), new Vector2(138f, 34f));
                hud.worldCardSelected[i] = sel.gameObject;
            }
            var close = GlyphButton("WorldClose", panel.transform, BC, new Vector2(0f, 62f), 56f, gIcoClose);
            UnityEditor.Events.UnityEventTools.AddPersistentListener(close.onClick, hud.OnWorldClose);
            panel.SetActive(false);
        }
    }
}
