// HUD.cs
// Everything drawn flat on the screen: level, coins, progress to the boss, weapon badge,
// the banner in the middle, the red warning vignette, the flash, and the three overlays
// (title / level cleared / squadron lost).
using UnityEngine;
using UnityEngine.UI;
using TMPro;

namespace SkySquad
{
    public class HUD : MonoBehaviour
    {
        [Header("Top bar")]
        public TextMeshProUGUI levelText;
        public TextMeshProUGUI coinsText;
        public RectTransform progressFill;
        public float progressWidth = 150f;
        public Image progressImage;
        [Header("Bottom")]
        public TextMeshProUGUI weaponName;
        public TextMeshProUGUI weaponDesc;
        public TextMeshProUGUI killsText;
        public TextMeshProUGUI hintText;
        public CanvasGroup hintGroup;
        [Header("Center")]
        public TextMeshProUGUI bannerText;
        public CanvasGroup bannerGroup;
        public Image warnImage;
        public Image flashImage;
        [Header("Overlays")]
        public GameObject titlePanel;
        public TextMeshProUGUI titleBest;
        public GameObject clearPanel;
        public TextMeshProUGUI clearStats;
        public GameObject overPanel;
        public TextMeshProUGUI overReason;
        public TextMeshProUGUI overStats;
        public GameObject playGroup;
        [Header("Buttons")]
        public TextMeshProUGUI soundGlyph;

        float bannerT, bannerDur, warnT, flashT, flashDur, hintT;
        Color flashColor = Color.white;

        void Start()
        {
            var gm = GameManager.I;
            if (gm != null) gm.OnStateChanged += OnState;
            OnState(gm != null ? gm.State : GameState.Title);
            RefreshSound();
        }

        void OnState(GameState s)
        {
            if (titlePanel) titlePanel.SetActive(s == GameState.Title);
            if (clearPanel) clearPanel.SetActive(s == GameState.LevelClear);
            if (overPanel) overPanel.SetActive(s == GameState.GameOver);
            if (playGroup) playGroup.SetActive(s != GameState.Title);
            var gm = GameManager.I;
            if (gm == null) return;
            if (s == GameState.Title && titleBest) titleBest.text = "BEST LEVEL " + gm.Best + "   ·   desktop: arrows / WASD";
            if (s == GameState.LevelClear && clearStats) clearStats.text = "Level " + gm.Level + " cleared\nPlanes left: " + gm.squad.Count + "   ·   kills: " + gm.UnitsKilled + "   ·   coins " + gm.Coins;
            if (s == GameState.GameOver)
            {
                if (overReason) overReason.text = gm.LoseReason;
                if (overStats) overStats.text = "Level " + gm.Level + "   ·   kills " + gm.UnitsKilled + "   ·   best " + gm.Best;
            }
        }

        void Update()
        {
            var gm = GameManager.I;
            if (gm == null) return;
            float dt = Time.deltaTime;
            if (levelText) levelText.text = "LV " + gm.Level;
            if (coinsText) coinsText.text = "$ " + gm.Coins;
            if (killsText) killsText.text = gm.UnitsKilled.ToString();
            if (gm.squad != null && gm.squad.Weapon != null)
            {
                if (weaponName) { weaponName.text = gm.squad.Weapon.displayName; weaponName.color = gm.squad.Weapon.color; }
                if (weaponDesc) weaponDesc.text = gm.squad.Weapon.description;
            }
            if (progressFill)
            {
                float prog = gm.State == GameState.Playing || gm.State == GameState.LevelClear ? Mathf.Clamp01(gm.LevelTime / gm.LevelDuration) : 0f;
                progressFill.sizeDelta = new Vector2(Mathf.Max(8f, progressWidth * prog), progressFill.sizeDelta.y);
                if (progressImage) progressImage.color = gm.BossPhase ? new Color(1f, 0.23f, 0.31f) : new Color(0.37f, 0.69f, 1f);
            }
            if (bannerGroup)
            {
                bannerT = Mathf.Max(0f, bannerT - dt);
                float k = bannerDur > 0f ? bannerT / bannerDur : 0f;
                bannerGroup.alpha = bannerT > 0f ? Mathf.Min(1f, k / 0.25f) * Mathf.Min(1f, (1f - k) / 0.12f + 0.2f) : 0f;
                bannerGroup.transform.localPosition = new Vector3(0f, 190f + (1f - Mathf.Min(1f, (1f - k) / 0.15f)) * 40f, 0f);
            }
            if (warnImage)
            {
                warnT = Mathf.Max(0f, warnT - dt);
                var c = warnImage.color; c.a = warnT > 0f ? 0.35f * (warnT / 1.2f) * (0.6f + 0.4f * Mathf.Sin(Time.time * 12f)) : 0f; warnImage.color = c;
            }
            if (flashImage)
            {
                flashT = Mathf.Max(0f, flashT - dt);
                var c = flashColor; c.a = flashDur > 0f ? 0.45f * flashT / flashDur : 0f; flashImage.color = c;
            }
            if (hintGroup)
            {
                hintT = Mathf.Max(0f, hintT - dt);
                hintGroup.alpha = gm.State == GameState.Playing ? Mathf.Min(1f, hintT) : 0f;
            }
        }

        public void Banner(string text, Color color, float dur)
        {
            if (bannerText) { bannerText.text = text; bannerText.color = color; bannerText.fontSize = text.Length > 14 ? 34f : 52f; }
            bannerT = bannerDur = dur;
        }
        public void Warn(float dur) { warnT = dur; }
        public void Flash(Color c, float dur) { flashColor = c; flashT = flashDur = dur; }
        public void ShowHint(float seconds) { hintT = seconds; }

        public void ToggleSound()
        {
            var a = AudioManager.I;
            if (a == null) return;
            a.Muted = !a.Muted;
            RefreshSound();
        }
        void RefreshSound()
        {
            if (soundGlyph && AudioManager.I != null) soundGlyph.text = AudioManager.I.Muted ? "x" : "))";
        }
    }
}
