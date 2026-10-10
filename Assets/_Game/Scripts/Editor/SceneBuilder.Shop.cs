// SceneBuilder.Shop.cs (Editor only)
// The diamonds shop (2026-10-07): the + on the diamonds pill opens a full screen in the world-select screen's look - the navy page
// with its dots, the title, the bank at the top right, the cards in two columns, the big white X - selling GemShop's six packs (the
// amounts, prices and bonuses come from GemShop's formula; HUD.RefreshShop writes them). Every piece is the GUI Pro - Casual Game
// kit: the cards are the world cards' chunky slabs, the price sits on the kit's green Button01, the bonus hangs on its orange ribbon
// tag, the best value wears a red BEST VALUE tab, and the pictures are its gem art - the single blue gem, and the pink gem pile and gem
// box recoloured to that gem's blue (ShopGemSprite) so they match the diamond on the pill. A pack's picture grows with the pack:
// one gem, a pile, a bigger pile, the gem box, the box and a pile, the box between two piles.
// Sky Squad > Rebuild Shop swaps just this panel (and wires the +) in the open scene - Build Everything regenerates the whole world,
// which drops the worlds whose asset packs are not imported on this machine.
using System.Collections.Generic;
using System.IO;
using UnityEditor;
using UnityEngine;
using UnityEngine.UI;

namespace SkySquad.EditorTools
{
    public static partial class SceneBuilder
    {
        const string ShopGemRef = "Icon_ItemIcons/256/Icon_Gem01_Blue.png";   // the kit's blue gem: the pill's diamond, and the palette the pink art is recoloured to
        const int ShopFlyPool = 24;   // flying diamonds: the biggest pack sends 20, a quick second purchase takes what is left

        /// <summary>A kit sprite's PNG as a readable texture, straight from the file (the kit's import settings stay untouched).</summary>
        static Texture2D KitPixels(string rel)
        {
            string path = GuiDir + rel;
            if (!File.Exists(path)) { Debug.LogWarning("[SkySquad] GUI Pro sprite missing: " + path); return null; }
            var t = new Texture2D(2, 2, TextureFormat.RGBA32, false);
            t.LoadImage(File.ReadAllBytes(path));
            return t;
        }

        static float Luma(Color c) => 0.2126f * c.r + 0.7152f * c.g + 0.0722f * c.b;

        /// <summary>A gem-coloured pixel: in the hue band [lo, hi] degrees, not grey. bright = only its lit facets (value 0.5 and up), not the dark rim.</summary>
        static bool GemHue(Color c, float lo, float hi, bool bright)
        {
            Color.RGBToHSV(c, out float h, out float s, out float v);
            float deg = h * 360f;
            return deg >= lo && deg <= hi && s >= 0.06f && (!bright || v >= 0.5f);
        }

        /// <summary>The kit's pink gem art recoloured to the blue gem's palette, saved as a generated sprite. Histogram matching on brightness:
        /// each pink facet takes the colour the blue gem has at the same brightness rank (its 64 brightness bands, averaged), so the light
        /// facets come out cyan, the mid ones azure and the dark ones indigo, the way the blue gem is shaded. The dark rim keeps its darkness on
        /// a navy hue, and every pixel that is not pink (the gem box's wood and straps) is left as it is.</summary>
        static Sprite ShopGemSprite(string kitRel, string name)
        {
            var src = KitPixels(kitRel);
            var refTex = KitPixels(ShopGemRef);
            if (src == null || refTex == null) return Gp(kitRel);
            // the palette: the blue gem's lit pixels, darkest to lightest, in 64 bands
            var refPx = new List<Color>();
            foreach (var c in refTex.GetPixels()) if (c.a >= 0.98f && GemHue(c, 150f, 270f, true)) refPx.Add(c);
            refPx.Sort((a, b) => Luma(a).CompareTo(Luma(b)));
            const int Bands = 64;
            var band = new Color[Bands];
            for (int i = 0; i < Bands; i++)
            {
                int from = i * refPx.Count / Bands, to = Mathf.Max(from + 1, (i + 1) * refPx.Count / Bands);
                Color sum = Color.clear;
                for (int k = from; k < to; k++) sum += refPx[k];
                band[i] = sum / (to - from);
            }
            Color Palette(float q)
            {
                float f = q * Bands - 0.5f;
                int i = Mathf.Clamp(Mathf.FloorToInt(f), 0, Bands - 1), j = Mathf.Min(Bands - 1, i + 1);
                return Color.Lerp(band[i], band[j], Mathf.Clamp01(f - i));
            }
            // the source's own brightness ranks: its lit pink pixels, sorted
            var px = src.GetPixels();
            var ranks = new List<float>();
            foreach (var c in px) if (c.a >= 0.98f && GemHue(c, 250f, 345f, true)) ranks.Add(Luma(c));
            ranks.Sort();
            int Lower(float x) { int lo = 0, hi = ranks.Count; while (lo < hi) { int m = (lo + hi) >> 1; if (ranks[m] < x) lo = m + 1; else hi = m; } return lo; }
            int Upper(float x) { int lo = 0, hi = ranks.Count; while (lo < hi) { int m = (lo + hi) >> 1; if (ranks[m] <= x) lo = m + 1; else hi = m; } return lo; }
            for (int p = 0; p < px.Length; p++)
            {
                var c = px[p];
                if (c.a <= 0f || !GemHue(c, 250f, 345f, false)) continue;
                Color.RGBToHSV(c, out _, out float s, out float v);
                Color n;
                if (v < 0.5f || ranks.Count == 0) n = Color.HSVToRGB(222f / 360f, s, v);   // the dark rim: navy instead of plum
                else n = Palette((Lower(Luma(c)) + Upper(Luma(c))) * 0.5f / ranks.Count);
                n.a = c.a;
                px[p] = n;
            }
            src.SetPixels(px); src.Apply();
            var sprite = SaveSprite(src, "UI_" + name, Vector4.zero);
            Object.DestroyImmediate(src); Object.DestroyImmediate(refTex);
            return sprite;
        }

        /// <summary>One piece of a pack's picture: which art (0 the gem, 1 the pile, 2 the box), where in the well and how wide (units).</summary>
        struct ShopPiece { public int art; public float x, y, size; public ShopPiece(int art, float x, float y, float size) { this.art = art; this.x = x; this.y = y; this.size = size; } }

        /// <summary>The pictures, smallest pack first, inside the well's 200 x 98 clip: drawn in order, so the front pieces come last.</summary>
        static readonly ShopPiece[][] ShopPictures =
        {
            new[] { new ShopPiece(0, 0f, 0f, 96f) },                                                                   // 100: one gem
            new[] { new ShopPiece(1, 0f, 0f, 118f) },                                                                  // 600: the pile
            new[] { new ShopPiece(1, 0f, 4f, 110f), new ShopPiece(0, -66f, -20f, 54f), new ShopPiece(0, 66f, -24f, 46f) },   // 1,250: the pile and two more gems
            new[] { new ShopPiece(2, 0f, 0f, 134f) },                                                                  // 2,700: the gem box
            new[] { new ShopPiece(2, -18f, 4f, 124f), new ShopPiece(1, 60f, -16f, 80f) },                              // 7,200: the box and a pile
            new[] { new ShopPiece(2, 0f, 6f, 120f), new ShopPiece(1, -62f, -18f, 76f), new ShopPiece(1, 62f, -18f, 76f) },   // 15,000: the box between two piles
        };

        /// <summary>The + on the diamonds pill as a button that opens the shop: its green face takes the tap, padded to a thumb's size.</summary>
        static void WireShopPlus(Transform plus, HUD hud)
        {
            var faceT = plus.Find("Face");
            var face = faceT != null ? faceT.GetComponent<Image>() : null;
            if (face == null) { Debug.LogError("[SkySquad] the diamonds pill's + has no Face image"); return; }
            face.raycastTarget = true;
            face.raycastPadding = new Vector4(-12f, -12f, -12f, -12f);   // drawn 22 units, 46 to the thumb
            var btn = plus.GetComponent<Button>();
            if (btn == null) btn = plus.gameObject.AddComponent<Button>();
            btn.transition = Selectable.Transition.None; btn.targetGraphic = face;
            for (int k = btn.onClick.GetPersistentEventCount() - 1; k >= 0; k--) UnityEditor.Events.UnityEventTools.RemovePersistentListener(btn.onClick, k);
            UnityEditor.Events.UnityEventTools.AddPersistentListener(btn.onClick, hud.OnShopButton);
            var fx = plus.GetComponent<UIButtonFx>();
            if (fx == null) fx = plus.gameObject.AddComponent<UIButtonFx>();
            fx.tint = face; fx.pressedColor = new Color(UiGreen.r * 0.72f, UiGreen.g * 0.72f, UiGreen.b * 0.72f, 1f);   // a darker green on the press, not grey
        }

        /// <summary>Builds the shop under the HUD canvas and wires it into hud. Returns the panel (inactive: the + opens it).</summary>
        static GameObject BuildShop(Transform canvas, HUD hud)
        {
            var art = new[] { Gp(ShopGemRef), ShopGemSprite("Icon_ItemIcons/256/Icon_Gems.png", "ShopGemPile"), ShopGemSprite("IconMisc/Icon_ShopIcon_GemBox.png", "ShopGemBox") };
            var pillGem = Gp("UI_Etc/ResourceBar_Icon_Gem_Blue.png");
            var panel = Panel("ShopPanel", canvas, 1f); hud.shopPanel = panel;
            var pim = panel.GetComponent<Image>(); pim.raycastTarget = true; pim.color = new Color(0.12f, 0.19f, 0.32f, 1f);
            { var dots = UIImage("Dots", panel.transform, new Color(1f, 1f, 1f, 0.05f), Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero); dots.sprite = uiCircle; dots.type = Image.Type.Tiled; dots.pixelsPerUnitMultiplier = 64f / 48f; }
            TxtTitle("Title", panel.transform, "SHOP", 42f, Color.white, TC, new Vector2(0f, -62f), new Vector2(420f, 64f));
            var bank = CoinBar("ShopGems", panel.transform, TR, new Vector2(-88f, -34f), new Vector2(140f, 40f), pillGem, 40f);
            hud.shopGems = Type("ShopGemsText", bank, "0", 22f, GText, Mid, new Vector2(-10f, 1f), new Vector2(100f, 40f));
            hud.shopBankIcon = bank.Find("Icon") as RectTransform;   // where the bought diamonds land
            var popRt = UI("ShopPop", panel.transform, TR, TR, new Vector2(-88f, -74f), new Vector2(140f, 28f));
            var popGroup = popRt.gameObject.AddComponent<CanvasGroup>(); popGroup.alpha = 0f; popGroup.blocksRaycasts = false; hud.shopPopGroup = popGroup;
            hud.shopPopText = TxtTitle("ShopPopText", popRt, "+0", 22f, new Color(0.55f, 0.90f, 1f), Mid, Vector2.zero, new Vector2(140f, 28f));

            // the packs: two columns of three between the title and the X, in a scroll view that only scrolls when the screen is too short
            int n = GemShop.Count, rows = (n + 1) / 2, best = GemShop.BestValue;
            const float CardW = 226f, CardH = 224f, Pitch = 248f;   // 24 between the rows: room for the ribbon tags and the BEST VALUE tab
            var vp = UI("Viewport", panel.transform, Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero); vp.offsetMin = new Vector2(0f, 112f); vp.offsetMax = new Vector2(0f, -104f);
            var vim = vp.gameObject.AddComponent<Image>(); vim.color = new Color(0f, 0f, 0f, 0f); vim.raycastTarget = true; vp.gameObject.AddComponent<RectMask2D>();
            var content = UI("Content", vp, new Vector2(0f, 0.5f), new Vector2(1f, 0.5f), Vector2.zero, new Vector2(0f, (rows - 1) * Pitch + CardH + 20f));   // the cards plus their tags, shelves and shadows; pivot in the middle: centred when the screen has room
            var sr = vp.gameObject.AddComponent<ScrollRect>(); sr.viewport = vp; sr.content = content; sr.horizontal = false; sr.vertical = true; sr.movementType = ScrollRect.MovementType.Elastic; sr.scrollSensitivity = 30f;
            hud.shopAmount = new TMPro.TextMeshProUGUI[n]; hud.shopPrice = new TMPro.TextMeshProUGUI[n]; hud.shopBonus = new TMPro.TextMeshProUGUI[n]; hud.shopPackArt = new RectTransform[n];
            var blue = new Color(0.33f, 0.66f, 0.96f);   // the diamonds pill's face: every card, the best value too (its gold card and the kit's thumbs-up badge went the same day: "remove this, the colour the same as the others")
            for (int i = 0; i < n; i++)
            {
                float cx = i % 2 == 0 ? -118f : 118f, cy = ((rows - 1) * 0.5f - i / 2) * Pitch;
                Color col = Color.Lerp(blue, UiNavy, 0.2f), dark = Color.Lerp(blue, UiNavy, 0.6f), lit = Color.Lerp(blue, Color.white, 0.22f);
                var card = UI("Pack" + i, content, Mid, Mid, new Vector2(cx, cy), new Vector2(CardW, CardH));
                var sh = UIImage("Shadow", card, new Color(0f, 0f, 0f, 0.40f), Vector2.zero, Vector2.one, new Vector2(0f, -12f), new Vector2(24f, 24f)); sh.sprite = uiSoft; sh.type = Image.Type.Sliced; sh.pixelsPerUnitMultiplier = UiSoftFade / 20f;
                var body = Chunk("Body", card, Gp("Frame/BorderFrame_Round02.png"), col, dark, Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero, 3f, 7f, UiStroke);
                var face = body.Find("Face").GetComponent<Image>(); face.raycastTarget = true;
                var btn = card.gameObject.AddComponent<Button>(); btn.transition = Selectable.Transition.None; btn.targetGraphic = face;
                UnityEditor.Events.UnityEventTools.AddIntPersistentListener(btn.onClick, hud.OnShopBuy, i);
                card.gameObject.AddComponent<UIButtonFx>();   // the whole card squashes on the press, like the upgrade and world cards
                // the amount: the pill's gem and the number, centred together in the lighter head band
                Kit("Head", card, "Frame/BasicFrame_Round20.png", lit, TC, TC, new Vector2(0f, -24f), new Vector2(206f, 34f), 4f);
                var amount = UI("Amount", card, TC, TC, new Vector2(0f, -24f), new Vector2(200f, 34f));
                var row = amount.gameObject.AddComponent<HorizontalLayoutGroup>(); row.childAlignment = TextAnchor.MiddleCenter; row.spacing = 4f;
                row.childControlWidth = true; row.childControlHeight = true; row.childForceExpandWidth = false; row.childForceExpandHeight = false;
                var gemIcon = Icon("Gem", amount, pillGem, Color.white, Mid, Vector2.zero, 28f);
                var gemLe = gemIcon.gameObject.AddComponent<LayoutElement>(); gemLe.preferredWidth = 24f; gemLe.preferredHeight = 28f;
                hud.shopAmount[i] = TxtTitle("Value", amount, GemShop.Diamonds(i).ToString("N0", System.Globalization.CultureInfo.InvariantCulture), 26f, Color.white, Mid, Vector2.zero, new Vector2(150f, 34f));
                // the picture: a dark well with a cyan glow behind the gems, clipped to the well
                var well = Outlined("Well", card, "Frame/BasicFrame_Round20.png", Color.Lerp(blue, UiNavy, 0.72f), Mid, Mid, new Vector2(0f, 10f), new Vector2(206f, 104f), 4f, 2.5f);
                hud.shopPackArt[i] = well;   // a purchase's diamonds burst out of here
                var inner = UI("Inner", well, Vector2.zero, Vector2.one, Vector2.zero, new Vector2(-6f, -6f)); inner.gameObject.AddComponent<RectMask2D>();
                var glow = GImg("Glow", inner, Gp("Popup/Common_Popup_Glow.png"), new Color(0.35f, 0.85f, 1f, 0.42f), Mid, Mid, Vector2.zero, new Vector2(230f, 140f), 1f, false); glow.preserveAspect = false;
                var pic = i < ShopPictures.Length ? ShopPictures[i] : ShopPictures[ShopPictures.Length - 1];
                for (int k = 0; k < pic.Length; k++) Icon("Art" + k, inner, art[pic[k].art], Color.white, Mid, new Vector2(pic[k].x, pic[k].y), pic[k].size);
                // the price on the kit's green button (the card is the button: tap anywhere on it)
                var priceFace = GImg("Price", card, G("Button/Button01_145_Green"), Color.white, Mid, Mid, new Vector2(0f, -74f), new Vector2(196f, 52f), Fit(145f, 52f));
                hud.shopPrice[i] = TxtTitle("Label", priceFace.transform, GemShop.PriceText(i), 28f, Color.white, Mid, new Vector2(0f, 4f), new Vector2(180f, 48f));
                // the bonus on the kit's orange ribbon tag, hanging over the top-left corner (none on the first pack: it sets the rate)
                var tag = UI("Bonus", card, TL, TL, new Vector2(18f, -26f), new Vector2(64f, 74f));
                GImg("Ribbon", tag, Gp("Label/Label_Ribbon_Single_Orange.png"), Color.white, Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero, 1f, false);
                hud.shopBonus[i] = TxtBold("Text", tag, "+" + GemShop.BonusPercent(i) + "%", 22f, Color.white, Mid, new Vector2(-1f, 10f), new Vector2(64f, 32f));
                hud.shopBonus[i].fontSharedMaterial = fontUiHeavy != null ? fontUiHeavy : fontUiPlain;   // the heavy outline: small type on a bright tag
                tag.gameObject.SetActive(GemShop.BonusPercent(i) > 0);
                if (i == best)
                {   // the best value: a red BEST VALUE tab on the top edge
                    var tab = Outlined("BestTab", card, "Frame/BasicFrame_Round20.png", UiRed, TC, TC, new Vector2(0f, 4f), new Vector2(116f, 22f), 4f, 2.5f);
                    TxtBold("Label", tab, "BEST VALUE", 14f, Color.white, Mid, new Vector2(0f, 1f), new Vector2(112f, 22f));
                }
            }
            var close = GlyphButton("ShopClose", panel.transform, BC, new Vector2(0f, 62f), 56f, gIcoClose);
            UnityEditor.Events.UnityEventTools.AddPersistentListener(close.onClick, hud.OnShopClose);
            // the diamonds a purchase sends from its pack to the bank (HUD.LaunchGems): the pill's gem, a pool over everything on the page
            var flyLayer = UI("Fly", panel.transform, Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero); hud.shopFlyLayer = flyLayer;
            hud.shopFlyGems = new Image[ShopFlyPool];
            for (int k = 0; k < ShopFlyPool; k++) { hud.shopFlyGems[k] = Icon("Gem" + k, flyLayer, pillGem, Color.white, Mid, Vector2.zero, 40f); hud.shopFlyGems[k].gameObject.SetActive(false); }
            panel.SetActive(false);
            return panel;
        }

        [MenuItem("Sky Squad/Rebuild Shop")]
        public static void RebuildShop()
        {
            var hud = HudForPatch("Rebuild Shop");   // SceneBuilder.HudPatches.cs
            if (hud == null) return;
            int index = -1;
            if (hud.shopPanel != null) { index = hud.shopPanel.transform.GetSiblingIndex(); Object.DestroyImmediate(hud.shopPanel); }
            else if (hud.settingsPanel != null) index = hud.settingsPanel.transform.GetSiblingIndex();   // a new shop goes under settings and the splash, over the rest
            var panel = BuildShop(hud.transform, hud);
            if (index >= 0) panel.transform.SetSiblingIndex(index);
            var plus = hud.gemsText != null ? hud.gemsText.transform.parent.Find("Plus") : null;
            if (plus != null) WireShopPlus(plus, hud);
            else Debug.LogError("[SkySquad] Rebuild Shop: the diamonds pill has no + (run Build Everything once)");
            SaveHudScene(hud, "shop rebuilt");
        }
    }
}
