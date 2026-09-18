// HUD.cs
// Everything drawn flat on the screen: the numbers of the attempt (attempt, coins with the "+N"
// pop, horde progress or the boss health bar, planes, weapon, kills), the banner in the middle,
// the red warning vignette, the flash, the pause button, and the overlays: the lobby (three
// upgrade cards and the start button), paused, and the death screen.
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
        public TextMeshProUGUI coinPopText;
        public CanvasGroup coinPopGroup;
        public RectTransform progressFill;
        public float progressWidth = 150f;
        public Image progressImage;
        public TextMeshProUGUI progressText;
        [Header("Bottom")]
        public TextMeshProUGUI planesText;
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
        [Header("Lobby")]
        public GameObject titlePanel;
        public TextMeshProUGUI lobbyCoins;
        public TextMeshProUGUI attemptInfo;
        public TextMeshProUGUI[] cardLevel = new TextMeshProUGUI[3];
        public TextMeshProUGUI[] cardEffect = new TextMeshProUGUI[3];
        public TextMeshProUGUI[] cardCost = new TextMeshProUGUI[3];
        public Image[] cardBuyFace = new Image[3], cardBuyShelf = new Image[3];   // the price button's edge ring and plate: amber when the bank covers it, grey when not (UI kit, 2026-09-18)
        public Color buyFace, buyShelf, cantFace, cantShelf, buyText, cantText;   // ...those colours (edge, plate, label), set by the builder
        [Header("Overlays")]
        public GameObject pausePanel;
        public GameObject clearPanel;
        public TextMeshProUGUI clearTitle, clearSub, clearTap;   // "BOSS / DOWN! / TAP FOR NEXT", or the victory wording
        public TextMeshProUGUI clearStats;
        public GameObject overPanel;
        public TextMeshProUGUI overReason;
        public TextMeshProUGUI overStats;
        public GameObject playGroup;
        [Header("Buttons")]
        public TextMeshProUGUI soundGlyph;

        public GameObject settingsPanel;               // SETTINGS: opened from the lobby and the pause screen (2026-09-18)
        public UnityEngine.UI.Slider dragSlider;       // "PLANE SPEED": Settings.DragUnits, 1..20
        public TextMeshProUGUI dragValueText;
        float settingsClosedAt = -10f;
        /// <summary>The settings panel is up (or was closed this instant): GameManager.OnTap ignores the tap, so DONE does not also resume the game.</summary>
        public bool SettingsOpen => (settingsPanel != null && settingsPanel.activeSelf) || Time.unscaledTime - settingsClosedAt < 0.25f;

        float bannerT, bannerDur, warnT, flashT, flashDur, hintT, popT;
        int popAmount;
        Color flashColor = Color.white;
        static readonly Color Gold = new Color(1f, 0.82f, 0.25f), Red = new Color(1f, 0.23f, 0.31f), Blue = new Color(0.37f, 0.69f, 1f), Dim = new Color(0.55f, 0.58f, 0.65f);

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
            if (pausePanel) pausePanel.SetActive(s == GameState.Paused);
            if (clearPanel) clearPanel.SetActive(s == GameState.LevelClear);
            if (overPanel) overPanel.SetActive(s == GameState.GameOver);
            if (playGroup) playGroup.SetActive(s != GameState.Title);
            var gm = GameManager.I;
            if (gm == null) return;
            if (s == GameState.Title) RefreshLobby();
            if (s == GameState.LevelClear)
            {
                var t1 = clearTitle ? clearTitle : FindText(clearPanel, "C1");
                var t2 = clearSub ? clearSub : FindText(clearPanel, "C2");
                var t3 = clearTap ? clearTap : FindText(clearPanel, "CTap");
                if (gm.Won)
                {   // the last boss is down: the game is won
                    if (t1) t1.text = "VICTORY";
                    if (t2) t2.text = "SKY CLEARED";
                    if (t3) t3.text = "TAP TO CONTINUE";
                    if (clearStats) clearStats.text = "All " + gm.config.lastBoss + " bosses down   ·   attempt " + Progress.Attempts + "   ·   kills " + gm.UnitsKilled + "\n+" + gm.RunCoins + " coins   ·   planes left: " + gm.squad.Count;
                }
                else
                {
                    if (t1) t1.text = "BOSS";
                    if (t2) t2.text = "DOWN!";
                    if (t3) t3.text = "TAP FOR NEXT";
                    if (clearStats) clearStats.text = "Planes left: " + gm.squad.Count + "   ·   kills: " + gm.UnitsKilled + "   ·   coins " + gm.Coins;
                }
            }
            if (s == GameState.GameOver)
            {
                var ws = WaveSpawner.I;
                if (overReason) overReason.text = gm.LoseReason;
                if (overStats) overStats.text = "ATTEMPT " + Progress.Attempts + "   ·   horde " + (ws != null ? ws.Horde : 1) + "   ·   kills " + gm.UnitsKilled + "\n+" + gm.RunCoins + " coins for the next attempt";
            }
        }

        /// <summary>A text child of a generated panel by name (scenes built before the field existed are not wired).</summary>
        static TextMeshProUGUI FindText(GameObject panel, string name)
        {
            if (panel == null) return null;
            var t = panel.transform.Find(name);
            return t ? t.GetComponent<TextMeshProUGUI>() : null;
        }

        /// <summary>Lobby numbers: the bank, the attempt counter, and each card: level / effect / price.</summary>
        public void RefreshLobby()
        {
            if (lobbyCoins) lobbyCoins.text = Progress.Coins.ToString("N0", System.Globalization.CultureInfo.InvariantCulture);   // the coin icon says what it is; "3,691" (the "$ " prefix went with the tactical UI, 2026-09-18)
            if (attemptInfo) attemptInfo.text = "ATTEMPT " + (Progress.Attempts + 1) + (Progress.Won ? "   ·   GAME COMPLETED" : "   ·   best: horde " + Mathf.Max(1, Progress.BestHorde));
            for (int i = 0; i < 3; i++)
            {
                var u = (Upgrade)i;
                if (cardLevel != null && i < cardLevel.Length && cardLevel[i]) cardLevel[i].text = "LV " + Progress.Levels[i];
                if (cardEffect != null && i < cardEffect.Length && cardEffect[i]) cardEffect[i].text = Progress.Effect(u);
                bool can = Progress.CanBuy(u);
                if (cardCost != null && i < cardCost.Length && cardCost[i]) { cardCost[i].text = "$ " + Progress.Cost(u).ToString("N0", System.Globalization.CultureInfo.InvariantCulture); cardCost[i].color = can ? buyText : cantText; }
                if (cardBuyFace != null && i < cardBuyFace.Length && cardBuyFace[i]) cardBuyFace[i].color = can ? buyFace : cantFace;
                if (cardBuyShelf != null && i < cardBuyShelf.Length && cardBuyShelf[i]) cardBuyShelf[i].color = can ? buyShelf : cantShelf;
            }
        }

        public void OnBuy(int idx)
        {
            var gm = GameManager.I;
            if (gm == null || gm.State != GameState.Title) return;
            bool ok = Progress.Buy((Upgrade)Mathf.Clamp(idx, 0, 2));
            if (AudioManager.I != null) AudioManager.I.Play(ok ? Sfx.Pickup : Sfx.Tick);
            RefreshLobby();
        }

        public void OnStartButton()
        {
            var gm = GameManager.I;
            if (gm != null && gm.State == GameState.Title) gm.StartGame();
        }

        void Update()
        {
            var gm = GameManager.I;
            if (gm == null) return;
            float dt = Time.deltaTime;
            if (levelText) levelText.text = "ATT " + Progress.Attempts;
            if (coinsText) coinsText.text = Progress.Coins.ToString("N0", System.Globalization.CultureInfo.InvariantCulture);
            if (killsText) killsText.text = gm.UnitsKilled.ToString();
            if (planesText && gm.squad != null) planesText.text = gm.squad.Shield > 0 ? gm.squad.Count + "  <color=#94C4FF><size=70%>SHIELD " + gm.squad.Shield + "</size></color>" : gm.squad.Count.ToString();
            if (gm.squad != null && gm.squad.Weapon != null)
            {
                if (weaponName) { weaponName.text = gm.squad.Weapon.displayName; weaponName.color = gm.squad.Weapon.color; }
                if (weaponDesc) weaponDesc.text = gm.squad.Weapon.description;
            }
            if (progressFill)
            {   // horde progress toward its boss, or the health of the boss while he is up
                var ws = WaveSpawner.I;
                var boss = ws != null ? ws.CurrentBoss : null;
                float prog; Color c; string txt;
                if (boss != null) { prog = boss.MaxHp > 0f ? boss.Hp / boss.MaxHp : 0f; c = Red; txt = "BOSS " + ws.Bosses; }   // the hp number lives over the boss's own bar now (2026-09-18)
                else if (ws != null) { prog = ws.HordeProgress; c = Blue; txt = "HORDE " + ws.Horde + "   " + ws.HordeKilled + "/" + ws.HordeTarget; }
                else { prog = 0f; c = Blue; txt = ""; }
                progressFill.sizeDelta = new Vector2(Mathf.Max(8f, progressWidth * prog), progressFill.sizeDelta.y);
                if (progressImage) progressImage.color = c;
                if (progressText) progressText.text = txt;
            }
            if (coinPopGroup)
            {
                popT = Mathf.Max(0f, popT - dt);
                coinPopGroup.alpha = popT > 0.3f ? 1f : popT / 0.3f;
                if (coinPopText)
                {
                    coinPopText.transform.localScale = Vector3.Lerp(coinPopText.transform.localScale, Vector3.one, 1f - Mathf.Pow(0.001f, dt));
                    var rt = coinPopGroup.transform as RectTransform;
                    if (rt) rt.anchoredPosition = new Vector2(rt.anchoredPosition.x, -58f - (1.2f - popT) * 6f);
                }
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

        /// <summary>"+N" under the coin counter; coins earned within a second or so add up into one pop.</summary>
        public void CoinPop(int n)
        {
            popAmount = n;   // one pop per reward, never summed: two quick kills read "+10" "+10", not "+20" ("10 per plane, not 20", 2026-09-16)
            popT = 1.2f;
            if (coinPopText) { coinPopText.text = "+" + popAmount; coinPopText.transform.localScale = Vector3.one * 1.3f; }
        }

        public void OnPauseButton()
        {
            var gm = GameManager.I;
            if (gm != null) gm.Pause();
        }

        public void OnSettingsButton()
        {
            var gm = GameManager.I;
            if (gm != null && gm.State == GameState.Playing) gm.Pause();   // the tap that pressed the button on the pause screen may have resumed the game first
            if (dragSlider != null) dragSlider.SetValueWithoutNotify(Settings.DragUnits(gm != null ? gm.config : null));
            RefreshDragValue();
            if (pausePanel) pausePanel.SetActive(false);   // the PAUSED / TAP TO RESUME text would show through the settings panel
            if (settingsPanel) settingsPanel.SetActive(true);
        }

        public void OnSettingsDone()
        {
            if (settingsPanel) settingsPanel.SetActive(false);
            settingsClosedAt = Time.unscaledTime;
            var gm = GameManager.I;
            if (pausePanel && gm != null) pausePanel.SetActive(gm.State == GameState.Paused);   // back to the pause screen (tap to resume)
            Settings.Save();
        }

        public void OnDragSlider(float v)
        {
            Settings.SetDragUnits(v);
            RefreshDragValue();
        }

        void RefreshDragValue()
        {
            if (dragValueText && dragSlider) dragValueText.text = Mathf.RoundToInt(dragSlider.value).ToString();
        }

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
