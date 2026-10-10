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
        public TextMeshProUGUI gemsText;               // the diamonds pill under the coins (2026-09-19; the plane-count bar it replaces is gone, the squad wears its count)
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
        // the orange ribbon banner was removed entirely on 2026-09-19 (user: "remove the ribbon entirely")
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
        public Image[] cardPips = new Image[15];         // five pips per card (i * 5 + k): level mod 5 lit, 5 lit on a multiple of 5 (the reference's look, 2026-09-19)
        public Color[] cardPipOn = new Color[3]; public Color pipOff = new Color(0.55f, 0.57f, 0.6f);
        public bool badgeLevel;                          // the level as a bare number in the card's badge ("10"), not "LV 10"
        public bool pricePlain;                          // the price without the "$ " (a coin icon sits beside it)
        public Color buyFace, buyShelf, cantFace, cantShelf, buyText, cantText;   // ...those colours (edge, plate, label), set by the builder
        public Color[] cardBuyTint = new Color[3];                                // the UPGRADE box's own colour per card; buyFace / cantFace multiply it (2026-09-19)
        public TextMeshProUGUI[] cardBuyLabel = new TextMeshProUGUI[3];           // the "UPGRADE" word: greys with the price when the bank is short
        [Header("Overlays")]
        public GameObject pausePanel;
        public GameObject clearPanel;
        public TextMeshProUGUI clearTitle, clearSub, clearTap;   // "BOSS / DOWN! / TAP FOR NEXT", or the victory wording
        public TextMeshProUGUI clearStats;
        public GameObject overPanel;
        public TextMeshProUGUI overReason;
        public TextMeshProUGUI overStats;
        public GameObject playGroup;
        [Header("Death screen (2026-10-03: the kit's Play_Continue - MAYDAY!, a countdown, REVIVE with an ad or RESTART)")]
        public CanvasGroup overGroup;                  // the whole screen: fades in after a beat (the squad's explosion plays first)
        public RectTransform overTitle;                // MAYDAY!: pops in
        public RectTransform overGlow;                 // the red glow behind it: swells in, then breathes
        public RectTransform overTimer;                // the countdown: a ring that drains around the seconds left
        public Image overTimerFill;
        public TextMeshProUGUI overTimerText;
        public TextMeshProUGUI overReviveInfo;         // "REVIVE WITH 24 PLANES"
        public RectTransform overRevive, overRestart;  // the buttons' holders: HUD slides these, each button squashes inside its own
        public UIButtonFx overRestartFx;               // RESTART breathes once it is the only way on
        [Header("Buttons")]
        public TextMeshProUGUI soundGlyph;             // the old text glyph (unused since the bought UI kit, 2026-09-18)
        public Image soundIcon;                        // the settings screen's speaker button: swaps between soundOn / soundOff (AIRIDev volume icons)
        public Sprite soundOn, soundOff;
        public RectTransform soundHandle;              // the switch's knob (GUI Pro kit, 2026-09-19): slides to +soundHandleX when on, -soundHandleX when muted
        public float soundHandleX = 18f;
        public Image[] soundIcons = new Image[0];       // every speaker glyph on screen (the pause row, the settings row): all swap between soundOn / soundOff (2026-09-19)
        [Header("Splash")]
        public GameObject splashPanel;                 // the loading screen the references show (2026-09-19): the logo over the hangar, a bar that fills over splashSeconds, then it goes
        public Image splashFill;
        public TextMeshProUGUI splashPercent;
        public float splashSeconds = 2.2f;
        float splashT;
        public GameObject hangar;                      // the title screen's 3D aircraft rig (HangarShowcase): on with the title panel, off with it (the splash shows it; the lobby itself shows the real squad since 2026-09-19)
        [Header("Lobby (2026-09-19: the menu is the level itself)")]
        public CanvasGroup titleGroup;                 // the whole title panel: fades out on the first swipe
        public RectTransform deck;                     // the cards and the hand: slide down and away on the first swipe
        public RectTransform hand;                     // the swipe hint: a hand rising over and over
        public CanvasGroup handGroup;
        public GameObject[] playOnly;                  // HUD pieces of the run itself (pause, the horde bar, weapon): hidden in the lobby, the pills stay

        public GameObject settingsPanel;               // SETTINGS: opened from the lobby and the pause screen (2026-09-18)
        public UnityEngine.UI.Slider dragSlider;       // "PLANE SPEED": Settings.DragUnits, 1..20
        public TextMeshProUGUI dragValueText;
        public TextMeshProUGUI settingsCoins;           // the bank on the settings screen (the reference, 2026-09-19)
        float settingsClosedAt = -10f;
        /// <summary>The settings panel is up (or was closed this instant): GameManager.OnTap ignores the tap, so DONE does not also resume the game.</summary>
        public bool SettingsOpen => (settingsPanel != null && settingsPanel.activeSelf) || Time.unscaledTime - settingsClosedAt < 0.25f || WorldOpen || ShopOpen;

        [Header("Shop (2026-10-07: the diamonds shop behind the + on the diamonds pill)")]
        public GameObject shopPanel;                   // the full-screen shop: six packs of diamonds (GemShop), opened by the + on the diamonds pill
        public TextMeshProUGUI shopGems;               // the diamonds bank at the top of the shop
        public TextMeshProUGUI[] shopAmount = new TextMeshProUGUI[0], shopPrice = new TextMeshProUGUI[0], shopBonus = new TextMeshProUGUI[0];   // per pack: "1,250", "$9.99", "+23%" (the tag is the text's parent)
        public CanvasGroup shopPopGroup;               // "+1,250" under the bank after a purchase
        public TextMeshProUGUI shopPopText;
        public RectTransform shopFlyLayer;             // over everything on the page: the diamonds that fly from a bought pack to the bank (2026-10-07)
        public Image[] shopFlyGems = new Image[0];     // their pool, hidden until a purchase
        public RectTransform shopBankIcon;             // where they land: the bank's gem, which punches on every landing
        public RectTransform[] shopPackArt = new RectTransform[0];   // where they burst from: each pack's picture
        float shopClosedAt = -10f, shopPopT;
        public bool ShopOpen => (shopPanel != null && shopPanel.activeSelf) || Time.unscaledTime - shopClosedAt < 0.25f;

        [Header("Worlds (2026-10-02: the level-select screen)")]
        public GameObject worldPanel;                  // the full-screen list of worlds, opened by the chip at the top of the lobby
        public TextMeshProUGUI worldChipName, worldChipNumber;   // the chip: "SKY SEA" / "WORLD 1"
        public Image worldChipDisc;
        public Image[] worldCardFace = new Image[0];   // one card per world: its frame (tinted by the world), picture, name, line of numbers and the SELECTED tick
        public RawImage[] worldCardPicture = new RawImage[0];
        public TextMeshProUGUI[] worldCardName = new TextMeshProUGUI[0], worldCardInfo = new TextMeshProUGUI[0], worldCardTag = new TextMeshProUGUI[0];
        public GameObject[] worldCardSelected = new GameObject[0];
        public TextMeshProUGUI worldCoins;
        public ScrollRect worldScroll;                 // the list of worlds, when there are more than four
        float worldClosedAt = -10f;
        public bool WorldOpen => (worldPanel != null && worldPanel.activeSelf) || Time.unscaledTime - worldClosedAt < 0.25f;

        float warnT, flashT, flashDur, hintT, popT, popBaseY = -58f;   // popBaseY: where the builder put the "+N" (under the pills)
        float titleOut; Vector2 deckBase, handBase; const float TitleOutTime = 0.28f;    // the lobby's exit: quick, the cards drop away as the squad moves
        int popAmount;
        Color flashColor = Color.white;
        static readonly Color Gold = new Color(1f, 0.82f, 0.25f), Red = new Color(1f, 0.23f, 0.31f), Blue = new Color(0.37f, 0.69f, 1f), Dim = new Color(0.55f, 0.58f, 0.65f);

        void Start()
        {
            var gm = GameManager.I;
            if (gm != null) gm.OnStateChanged += OnState;
            if (WorldManager.I != null) WorldManager.I.OnWorldChanged += _ => RefreshWorlds();
            if (deck) deckBase = deck.anchoredPosition;
            if (hand) handBase = hand.anchoredPosition;
            if (overRevive) reviveBase = overRevive.anchoredPosition;
            if (overRestart) restartBase = overRestart.anchoredPosition;
            OnState(gm != null ? gm.State : GameState.Title);
            RefreshSound();
            if (coinPopGroup) { var prt = coinPopGroup.transform as RectTransform; if (prt) popBaseY = prt.anchoredPosition.y; }
            if (splashPanel) { splashPanel.SetActive(true); splashT = 0f; }
            fly = new FlyGem[shopFlyGems != null ? shopFlyGems.Length : 0];
            for (int k = 0; k < fly.Length; k++) fly[k] = new FlyGem();
        }

        void OnState(GameState s)
        {
            bool title = s == GameState.Title;
            if (titlePanel)
            {
                if (title) { titlePanel.SetActive(true); titleOut = 0f; if (titleGroup) titleGroup.alpha = 1f; if (deck) deck.anchoredPosition = deckBase; }
                else if (titlePanel.activeSelf && s == GameState.Playing) titleOut = TitleOutTime;   // the first swipe: the cards drop away and the panel fades (Update), then it hides
                else titlePanel.SetActive(false);
            }
            if (worldPanel && !title) worldPanel.SetActive(false);
            if (shopPanel && !title && s != GameState.Paused) shopPanel.SetActive(false);   // the shop lives over the lobby or a paused run
            if (pausePanel) pausePanel.SetActive(s == GameState.Paused);
            if (clearPanel) clearPanel.SetActive(s == GameState.LevelClear);
            if (overPanel) overPanel.SetActive(s == GameState.GameOver);
            if (playGroup) playGroup.SetActive(true);   // the top bar stays up in the lobby too (the reference shows its coins over the menu); playOnly hides the run's own readouts
            if (playOnly != null) foreach (var go in playOnly) if (go) go.SetActive(!title);
            if (hangar) hangar.SetActive(title);   // the splash shows the jet
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
                    if (clearStats) clearStats.text = "All " + gm.LastBoss + " bosses down   ·   attempt " + Progress.Attempts + "   ·   kills " + gm.UnitsKilled + "\n+" + gm.RunCoins + " coins   ·   planes left: " + gm.squad.Count;
                }
                else
                {
                    if (t1) t1.text = "BOSS";
                    if (t2) t2.text = "DOWN!";
                    if (t3) t3.text = "TAP FOR NEXT";
                    if (clearStats) clearStats.text = "Planes left: " + gm.squad.Count + "   ·   kills: " + gm.UnitsKilled + "   ·   coins " + Money(gm.Coins);
                }
            }
            if (s == GameState.GameOver)
            {
                var ws = WaveSpawner.I;
                if (overReason) overReason.text = gm.LoseReason;
                if (overStats) overStats.text = "ATTEMPT " + Progress.Attempts + "   ·   horde " + (ws != null ? ws.Horde : 1) + "   ·   kills " + gm.UnitsKilled + "\n+" + gm.RunCoins + " coins for the next attempt";
                OpenOver(gm);
            }
        }

        // ------------------------------------------------------------------ the death screen
        // (2026-10-03) The kit's Play_Continue in the portrait: the dim, a red glow under MAYDAY!, why the squad went down, a ring counting
        // down reviveSeconds, the yellow REVIVE (a rewarded ad, Ads.cs; once per attempt) and the blue RESTART. When the ring runs out
        // REVIVE folds away and RESTART rises into its place. No tap-anywhere here: only the buttons act.
        float overT, reviveLeft, reviveSpan, reviveGoneT, timerPunch, restartY;
        int reviveShown;
        bool reviveOn, reviveGone;
        Vector2 reviveBase, restartBase;
        const float OverDelay = 0.45f;   // the squad's explosion plays this long before the screen comes in

        void OpenOver(GameManager gm)
        {
            overT = 0f; reviveGoneT = 0f; timerPunch = 0f;
            reviveOn = gm.CanRevive && Ads.RewardedReady;
            reviveGone = !reviveOn;
            reviveSpan = Mathf.Max(1f, gm.config.reviveSeconds); reviveLeft = reviveSpan; reviveShown = Mathf.CeilToInt(reviveSpan);
            int planes = gm.RevivePlanes;
            if (overReviveInfo) { overReviveInfo.text = "REVIVE WITH " + planes + (planes == 1 ? " PLANE" : " PLANES"); overReviveInfo.gameObject.SetActive(reviveOn); }
            if (overTimerText) { overTimerText.text = reviveShown.ToString(); overTimerText.transform.localScale = Vector3.one; }
            if (overTimer) { overTimer.gameObject.SetActive(reviveOn); overTimer.localScale = Vector3.one; }
            if (overRevive) { overRevive.gameObject.SetActive(reviveOn); overRevive.localScale = Vector3.one; }
            if (overRestartFx) overRestartFx.pulse = !reviveOn;
            restartY = reviveOn ? restartBase.y : reviveBase.y;   // alone, RESTART stands where REVIVE would
            AnimateOver(0f);
        }

        static float BackOut(float k) { k = Mathf.Clamp01(k) - 1f; return k * k * (2.70158f * k + 1.70158f) + 1f; }   // 0 -> 1 with a small overshoot
        static float OutCubic(float k) { k = 1f - Mathf.Clamp01(k); return 1f - k * k * k; }

        void AnimateOver(float dt)
        {
            overT += dt;
            float t = overT - OverDelay;   // below 0: the explosion's beat, nothing shows yet
            if (overGroup) overGroup.alpha = Mathf.Clamp01(t / 0.18f);
            if (overTitle) overTitle.localScale = Vector3.one * BackOut(t / 0.35f);
            if (overGlow) overGlow.localScale = Vector3.one * (OutCubic(t / 0.5f) * (1f + 0.05f * Mathf.Sin(overT * 2.6f)));
            // the countdown: it starts once the buttons are in, waits while an ad is on screen, ticks every second
            if (!reviveGone && t > 0.55f && !Ads.Showing)
            {
                reviveLeft -= dt;
                int sec = Mathf.Max(0, Mathf.CeilToInt(reviveLeft));
                if (sec != reviveShown)
                {
                    reviveShown = sec;
                    if (overTimerText) overTimerText.text = sec.ToString();
                    timerPunch = 1f;
                    if (sec > 0 && AudioManager.I != null) AudioManager.I.Play(Sfx.Tick);
                }
                if (reviveLeft <= 0f) { reviveGone = true; if (overRestartFx) overRestartFx.pulse = true; }
            }
            timerPunch = Mathf.Max(0f, timerPunch - dt * 4f);
            if (overTimerText) overTimerText.transform.localScale = Vector3.one * (1f + 0.35f * timerPunch * timerPunch);
            if (overTimerFill)
            {
                float left = Mathf.Clamp01(reviveLeft / reviveSpan);
                overTimerFill.fillAmount = left;
                overTimerFill.color = Color.Lerp(Red, Gold, Mathf.Clamp01((reviveLeft - 0.5f) / 2f));   // gold, turning red over the last two seconds
            }
            // the buttons rise into place one after the other; when the offer runs out the ring and REVIVE fold away
            float fold = 1f;
            if (reviveOn && reviveGone)
            {
                reviveGoneT += dt;
                fold = 1f - OutCubic(reviveGoneT / 0.25f);
                if (reviveGoneT > 0.25f)
                {
                    if (overTimer && overTimer.gameObject.activeSelf) overTimer.gameObject.SetActive(false);
                    if (overRevive && overRevive.gameObject.activeSelf) overRevive.gameObject.SetActive(false);
                    if (overReviveInfo && overReviveInfo.gameObject.activeSelf) overReviveInfo.gameObject.SetActive(false);
                }
            }
            if (overTimer) overTimer.localScale = Vector3.one * (BackOut((t - 0.1f) / 0.3f) * fold);
            if (overReviveInfo) overReviveInfo.alpha = Mathf.Clamp01((t - 0.2f) / 0.2f) * fold;
            if (overRevive)
            {
                overRevive.anchoredPosition = reviveBase + Vector2.down * (160f * (1f - BackOut((t - 0.15f) / 0.35f)));
                overRevive.localScale = Vector3.one * fold;
            }
            if (overRestart)
            {
                float target = reviveGone ? reviveBase.y : restartBase.y;
                restartY = Mathf.Lerp(restartY, target, 1f - Mathf.Exp(-12f * dt));
                overRestart.anchoredPosition = new Vector2(restartBase.x, restartY - 160f * (1f - BackOut((t - 0.25f) / 0.35f)));
            }
        }

        /// <summary>REVIVE on the death screen: the rewarded ad (Ads.cs), and when it was watched the attempt goes on.</summary>
        public void OnReviveButton()
        {
            var gm = GameManager.I;
            if (gm == null || !gm.CanRevive || reviveGone || Ads.Showing || overT < OverDelay + 0.3f) return;
            if (AudioManager.I != null) AudioManager.I.Play(Sfx.Pickup);
            Ads.ShowRewarded("revive", ok => { var g = GameManager.I; if (ok && g != null) g.Revive(); });
        }

        /// <summary>RESTART on the death screen: back to the start line (the lobby, the round armed under it).</summary>
        public void OnRestartButton()
        {
            var gm = GameManager.I;
            if (gm == null || gm.State != GameState.GameOver || Ads.Showing || overT < OverDelay + 0.3f) return;
            if (AudioManager.I != null) AudioManager.I.Play(Sfx.Tick);
            gm.Restart();
        }

        static readonly string[] MoneyUnits = { "k", "M", "B", "T" };

        /// <summary>A bank the way the counters show it (2026-10-03, "23.1k instead of 23,100"): 950, 23.1k, 123k, 4.5M, 1.2B. One decimal below 100,
        /// none above; rounded down, so a counter never shows more than there is. Whole numbers only, no float rounding.</summary>
        public static string Money(long n)
        {
            if (n < 0) return "-" + Money(-n);
            if (n < 1000) return n.ToString(System.Globalization.CultureInfo.InvariantCulture);
            long div = 1; int u = -1;
            while (n / div >= 1000 && u < MoneyUnits.Length - 1) { div *= 1000; u++; }
            long whole = n / div;
            if (whole >= 100) return whole + MoneyUnits[u];
            long tenths = n / (div / 10) % 10;
            return whole + (tenths > 0 ? "." + tenths : "") + MoneyUnits[u];
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
            RefreshWorlds();
            if (lobbyCoins) lobbyCoins.text = Money(Progress.Coins);   // the coin icon says what it is; "3.6k" (HUD.Money, 2026-10-03) (the "$ " prefix went with the tactical UI, 2026-09-18)
            if (attemptInfo) attemptInfo.text = "Attempt " + (Progress.Attempts + 1) + (Progress.Won ? "  ·  completed" : "");
            for (int i = 0; i < 3; i++)
            {
                var u = (Upgrade)i;
                int lv = Progress.Levels[i];
                if (cardLevel != null && i < cardLevel.Length && cardLevel[i]) cardLevel[i].text = (badgeLevel ? "" : "LV ") + lv;
                int lit = lv <= 0 ? 0 : (lv - 1) % 5 + 1;   // the pips: 1..5 within the current tier of five
                for (int k = 0; k < 5; k++) { int p = i * 5 + k; if (cardPips != null && p < cardPips.Length && cardPips[p]) cardPips[p].color = k < lit && i < cardPipOn.Length ? cardPipOn[i] : pipOff; }
                if (cardEffect != null && i < cardEffect.Length && cardEffect[i]) cardEffect[i].text = Progress.Effect(u);
                bool can = Progress.CanBuy(u);
                if (cardCost != null && i < cardCost.Length && cardCost[i]) { cardCost[i].text = (pricePlain ? "" : "$ ") + Progress.Cost(u).ToString("N0", System.Globalization.CultureInfo.InvariantCulture); cardCost[i].color = can ? buyText : cantText; }
                if (cardBuyLabel != null && i < cardBuyLabel.Length && cardBuyLabel[i]) cardBuyLabel[i].color = can ? buyText : cantText;
                Color tint = cardBuyTint != null && i < cardBuyTint.Length && cardBuyTint[i].a > 0f ? cardBuyTint[i] : Color.white;
                if (cardBuyFace != null && i < cardBuyFace.Length && cardBuyFace[i]) cardBuyFace[i].color = tint * (can ? buyFace : cantFace);
                if (cardBuyShelf != null && i < cardBuyShelf.Length && cardBuyShelf[i]) cardBuyShelf[i].color = tint * (can ? buyShelf : cantShelf);
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
            if (levelText) levelText.text = "Attempt " + Progress.Attempts;   // the reference's "Level 1" words, top centre (2026-09-19)
            if (coinsText) coinsText.text = Money(Progress.Coins);
            if (gemsText) gemsText.text = Money(Progress.Gems);
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
                else if (ws != null) { prog = ws.HordeProgress; c = Blue; txt = "HORDE " + ws.Horde + "   " + Mathf.RoundToInt(prog * 100f) + "%"; }   // the reference's "2%" (2026-09-19; was gone/target)
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
                    if (rt) rt.anchoredPosition = new Vector2(rt.anchoredPosition.x, popBaseY - (1.2f - popT) * 6f);
                }
            }
            if (shopPopGroup)
            {   // "+1,250" under the shop's bank after a purchase: pops big, settles, fades (unscaled: the shop can be up over a paused run)
                float udt = Time.unscaledDeltaTime;
                shopPopT = Mathf.Max(0f, shopPopT - udt);
                shopPopGroup.alpha = shopPopT > 0.3f ? 1f : shopPopT / 0.3f;
                if (shopPopText) shopPopText.transform.localScale = Vector3.Lerp(shopPopText.transform.localScale, Vector3.one, 1f - Mathf.Pow(0.001f, udt));
            }
            if (shopPanel && shopPanel.activeSelf)
            {   // a purchase: the diamonds fly to the bank, and the bank's number rolls up toward what has landed (fast, then settling on the exact total)
                float udt = Mathf.Min(Time.unscaledDeltaTime, 1f / 30f);   // a hitch (a store's payment sheet closing, a slow frame) slows the flight down instead of skipping it
                TickFly(udt);
                if (shopBankShown != shopBankLanded)
                {
                    shopBankShown += (shopBankLanded - shopBankShown) * (1.0 - System.Math.Exp(-9.0 * udt));
                    if (System.Math.Abs(shopBankLanded - shopBankShown) < 0.5) shopBankShown = shopBankLanded;
                    if (shopGems) shopGems.text = Money((long)shopBankShown);
                }
                shopBankPunch = Mathf.Max(0f, shopBankPunch - udt * 5f);
                if (shopBankIcon) shopBankIcon.localScale = Vector3.one * (1f + 0.35f * shopBankPunch * shopBankPunch);
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
            if (splashPanel != null && splashPanel.activeSelf)
            {   // the loading screen: a bar that fills in splashSeconds, then the lobby (unscaled: it plays before anything runs)
                splashT += Time.unscaledDeltaTime;
                float k = Mathf.Clamp01(splashT / Mathf.Max(0.1f, splashSeconds));
                if (splashFill) splashFill.fillAmount = k;
                if (splashPercent) splashPercent.text = Mathf.RoundToInt(k * 100f) + "%";
                if (k >= 1f && splashT > splashSeconds + 0.35f) splashPanel.SetActive(false);
            }
            if (hintGroup)
            {
                hintT = Mathf.Max(0f, hintT - dt);
                hintGroup.alpha = gm.State == GameState.Playing ? Mathf.Min(1f, hintT) : 0f;
            }
            if (titleOut > 0f && titlePanel)
            {   // the lobby's exit: the deck accelerates down off the screen while the whole panel fades, 0.28 s
                titleOut = Mathf.Max(0f, titleOut - Time.unscaledDeltaTime);
                float k = 1f - titleOut / TitleOutTime;
                if (deck) deck.anchoredPosition = deckBase + new Vector2(0f, -460f * k * k);
                if (titleGroup) titleGroup.alpha = 1f - k;
                if (titleOut <= 0f) titlePanel.SetActive(false);
            }
            if (overPanel && overPanel.activeSelf) AnimateOver(Time.unscaledDeltaTime);
            if (hand && gm.State == GameState.Title && titleOut <= 0f)
            {   // the swipe hint: the hand rises and fades, over and over
                float t = (Time.unscaledTime % 1.25f) / 1.25f;
                float ease = 1f - (1f - t) * (1f - t);
                hand.anchoredPosition = handBase + new Vector2(0f, 46f * ease);
                if (handGroup) handGroup.alpha = Mathf.Min(1f, Mathf.Sin(t * Mathf.PI) * 1.4f);
            }
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

        /// <summary>HOME on the pause screen (2026-09-19): leaves the attempt for the lobby.</summary>
        public void OnHomeButton() { var gm = GameManager.I; if (gm != null) gm.Home(); }

        public void OnResumeButton() { var gm = GameManager.I; if (gm != null) gm.Resume(); }

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
            if (settingsCoins) settingsCoins.text = Money(Progress.Coins);
            RefreshDragValue();
            if (pausePanel) pausePanel.SetActive(false);   // the PAUSED / TAP TO RESUME text would show through the settings panel
            if (settingsPanel) settingsPanel.SetActive(true);
        }

        // ------------------------------------------------------------------ worlds
        /// <summary>The chip at the top of the lobby: opens the list of worlds.</summary>
        public void OnWorldButton()
        {
            var gm = GameManager.I;
            if (gm == null || gm.State != GameState.Title || worldPanel == null) return;
            RefreshWorlds();
            worldPanel.SetActive(true);
            if (worldScroll != null && WorldManager.I != null)
            {   // open on the world the player is in
                int rows = (WorldManager.I.Count + 1) / 2, row = Mathf.Max(0, WorldManager.I.Current) / 2;
                Canvas.ForceUpdateCanvases();
                worldScroll.verticalNormalizedPosition = rows <= 1 ? 1f : Mathf.Clamp01(1f - row / (float)Mathf.Max(1, rows - 3));
            }
            if (AudioManager.I != null) AudioManager.I.Play(Sfx.Tick);
        }

        public void OnWorldClose()
        {
            if (worldPanel) worldPanel.SetActive(false);
            worldClosedAt = Time.unscaledTime;
        }

        /// <summary>A card on the world screen: the world is chosen and the screen goes (the lobby behind it is already that world).</summary>
        public void OnWorldPick(int i)
        {
            var gm = GameManager.I;
            if (gm == null || gm.State != GameState.Title) return;
            bool ok = gm.SelectWorld(i);
            if (AudioManager.I != null) AudioManager.I.Play(ok ? Sfx.Pickup : Sfx.Tick);
            if (!ok) return;
            RefreshWorlds();
            OnWorldClose();
        }

        /// <summary>The chip's name and number, and every card: the picture, the numbers (bosses, best horde, completed) and which one is selected.</summary>
        public void RefreshWorlds()
        {
            var wm = WorldManager.I;
            if (wm == null || wm.worlds == null) return;
            int cur = wm.Current;
            for (int i = 0; i < wm.worlds.Length; i++)
            {
                var e = wm.worlds[i];
                if (i == cur)
                {
                    if (worldChipName) worldChipName.text = e.displayName;
                    if (worldChipNumber) worldChipNumber.text = (i + 1).ToString();
                    if (worldChipDisc) worldChipDisc.color = e.accent;
                }
                if (i >= worldCardName.Length) continue;
                if (worldCardName[i]) worldCardName[i].text = e.displayName;
                if (i < worldCardTag.Length && worldCardTag[i]) worldCardTag[i].text = e.tagline;
                if (i < worldCardPicture.Length && worldCardPicture[i] && e.thumbnail != null)
                {   // the picture covers its well without stretching: the middle band of the texture that fits the well's shape
                    var raw = worldCardPicture[i]; raw.texture = e.thumbnail.texture;
                    var rr = raw.rectTransform.rect; float well = rr.height > 1f ? rr.width / rr.height : 2.3f, tex = (float)e.thumbnail.texture.width / Mathf.Max(1, e.thumbnail.texture.height);
                    raw.uvRect = well > tex ? new Rect(0f, (1f - tex / well) * 0.5f, 1f, tex / well) : new Rect((1f - well / tex) * 0.5f, 0f, well / tex, 1f);
                }
                int best = i < Progress.MaxWorlds ? Progress.WorldBest[i] : 0;
                bool won = i < Progress.MaxWorlds && Progress.WorldWon[i];
                int bosses = e.lastBoss > 0 ? e.lastBoss : GameManager.I != null ? GameManager.I.config.lastBoss : 30;
                if (i < worldCardInfo.Length && worldCardInfo[i])
                    worldCardInfo[i].text = won ? "COMPLETED  -  " + bosses + " BOSSES" : best > 0 ? "BEST: BOSS " + best + " OF " + bosses : bosses + " BOSSES";
                if (i < worldCardSelected.Length && worldCardSelected[i]) worldCardSelected[i].SetActive(i == cur);
            }
            if (worldCoins) worldCoins.text = Money(Progress.Coins);
        }

        // ------------------------------------------------------------------ the diamonds shop
        /// <summary>The + on the diamonds pill: the shop. Mid-attempt it pauses the run first (like the settings gear) and closing it goes back
        /// to the pause screen; over the death and clear screens it does nothing.</summary>
        public void OnShopButton()
        {
            var gm = GameManager.I;
            if (gm == null || shopPanel == null) return;
            if (gm.State == GameState.Playing) gm.Pause();
            if (gm.State != GameState.Title && gm.State != GameState.Paused) return;
            if (pausePanel) pausePanel.SetActive(false);
            ClearFly();
            RefreshShop();
            if (shopPopGroup) shopPopGroup.alpha = 0f;
            shopPopT = 0f;
            shopPanel.SetActive(true);
            if (AudioManager.I != null) AudioManager.I.Play(Sfx.Tick);
        }

        public void OnShopClose()
        {
            ClearFly();
            if (shopPanel) shopPanel.SetActive(false);
            shopClosedAt = Time.unscaledTime;
            var gm = GameManager.I;
            if (pausePanel && gm != null) pausePanel.SetActive(gm.State == GameState.Paused);
        }

        /// <summary>A pack on the shop screen: paid through the store (GemShop / Store.cs). The diamonds go into the bank at once (saved); on
        /// screen they burst out of the pack's picture and fly to the bank, which counts up as they land, with a "+n" under it.</summary>
        public void OnShopBuy(int i)
        {
            if (shopPanel == null || !shopPanel.activeSelf || Store.Busy) return;
            GemShop.Buy(i, got =>
            {
                if (AudioManager.I != null) AudioManager.I.Play(Sfx.Pickup);
                shopPopT = 1.2f;
                if (shopPopText) { shopPopText.text = "+" + got.ToString("N0", System.Globalization.CultureInfo.InvariantCulture); shopPopText.transform.localScale = Vector3.one * 1.3f; }
                LaunchGems(i, got);
                RefreshShop();
            }, () => { if (AudioManager.I != null) AudioManager.I.Play(Sfx.Tick); });
        }

        // the flight (2026-10-07, "an animation after the purchase: the diamonds moving from the pack to the counter, and the counter increasing
        // gradually"): a burst of the bank's own gem pops out of the bought pack's picture, scatters a little, then the gems fly one after the
        // other on curves fanning out toward the bank's gem, speeding up and shrinking. Each landing punches the bank's gem, pops, and adds its
        // share of the pack to what the bank shows; the number rolls up after them and ends on the exact total. More diamonds, more gems: 6 for
        // the first pack, 2 more per doubling of it, about 20 for the last. The bank itself (Progress.Gems) was paid in full the moment the purchase went through.
        class FlyGem { public bool live; public Vector2 from, burst, ctrl; public float t, delay, size, spin; public int value; }
        FlyGem[] fly;
        double shopBankShown, shopBankLanded;   // the bank as the shop shows it, and how much of the bank has landed: the number rolls toward the second
        float shopBankPunch, flySoundAt = -10f;
        const float FlyBurst = 0.22f, FlyTime = 0.55f, FlyStagger = 0.045f;

        /// <summary>A rect's centre in the fly layer's space (the pack may sit anywhere in the scroll view).</summary>
        Vector2 FlyPoint(RectTransform r) => shopFlyLayer.InverseTransformPoint(r.TransformPoint(r.rect.center));

        void LaunchGems(int pack, int amount)
        {
            var src = pack >= 0 && pack < shopPackArt.Length ? shopPackArt[pack] : null;
            int n = 0;
            if (fly != null && shopFlyLayer != null && shopBankIcon != null && src != null)
            {
                int want = Mathf.Clamp(Mathf.RoundToInt(6f + 2f * Mathf.Log(Mathf.Max(1f, amount / (float)GemShop.BaseDiamonds), 2f)), 6, fly.Length);
                for (int k = 0; k < fly.Length && n < want; k++) if (!fly[k].live) n++;
            }
            if (n == 0) { shopBankLanded += amount; return; }   // nothing can fly (no free gem): the number just rolls up
            Vector2 from = FlyPoint(src), target = FlyPoint(shopBankIcon);
            var area = src.rect;
            int share = amount / n, rest = amount - share * n, launched = 0;
            for (int k = 0; k < fly.Length && launched < n; k++)
            {
                var g = fly[k];
                if (g.live) continue;
                g.live = true; g.t = 0f;
                g.from = from + new Vector2(Random.Range(-0.3f, 0.3f) * area.width, Random.Range(-0.25f, 0.25f) * area.height);
                g.burst = g.from + Random.insideUnitCircle.normalized * Random.Range(26f, 64f);
                Vector2 d = target - g.burst, side = new Vector2(-d.y, d.x).normalized;
                g.ctrl = g.burst + d * 0.35f + side * Random.Range(-110f, 110f);   // each its own curve: the stream fans out on its way up
                g.delay = launched * FlyStagger + Random.Range(0f, 0.03f);
                g.size = Random.Range(0.85f, 1.15f); g.spin = Random.Range(-30f, 30f);
                g.value = share + (launched == n - 1 ? rest : 0);   // the shares add up to the pack exactly
                var rt = shopFlyGems[k].rectTransform; rt.anchoredPosition = g.from; rt.localScale = Vector3.zero; rt.localEulerAngles = new Vector3(0f, 0f, g.spin);
                shopFlyGems[k].gameObject.SetActive(true);
                launched++;
            }
        }

        void TickFly(float dt)
        {
            if (fly == null || shopFlyLayer == null || shopBankIcon == null) return;
            Vector2 target = FlyPoint(shopBankIcon);
            for (int k = 0; k < fly.Length; k++)
            {
                var g = fly[k];
                if (!g.live) continue;
                g.t += dt;
                Vector2 p; float s, rot = g.spin;
                if (g.t < FlyBurst)
                {   // out of the picture with a little overshoot
                    float b = g.t / FlyBurst;
                    p = Vector2.Lerp(g.from, g.burst, OutCubic(b)); s = g.size * BackOut(b);
                }
                else if (g.t < FlyBurst + g.delay) { p = g.burst; s = g.size; }   // waiting its turn
                else
                {   // to the bank on its curve, speeding up, shrinking toward the bank's gem
                    float f = Mathf.Clamp01((g.t - FlyBurst - g.delay) / FlyTime), e = f * f, u = 1f - e;
                    if (f >= 1f) { Land(k); continue; }
                    p = u * u * g.burst + 2f * u * e * g.ctrl + e * e * target;
                    s = g.size * Mathf.Lerp(1f, 0.6f, e); rot = g.spin * u;
                }
                var rt = shopFlyGems[k].rectTransform;
                rt.anchoredPosition = p; rt.localScale = new Vector3(s, s, 1f); rt.localEulerAngles = new Vector3(0f, 0f, rot);
            }
        }

        void Land(int k)
        {
            var g = fly[k];
            g.live = false;
            if (shopFlyGems[k]) shopFlyGems[k].gameObject.SetActive(false);
            shopBankLanded += g.value;
            shopBankPunch = 1f;
            if (AudioManager.I != null && Time.unscaledTime - flySoundAt > 0.07f) { flySoundAt = Time.unscaledTime; AudioManager.I.Play(Sfx.Pop); }
        }

        /// <summary>No gem in the air and the bank showing the real bank (the shop opening or closing).</summary>
        void ClearFly()
        {
            if (fly != null)
                for (int k = 0; k < fly.Length; k++)
                    if (fly[k].live) { fly[k].live = false; if (shopFlyGems[k]) shopFlyGems[k].gameObject.SetActive(false); }
            shopBankShown = shopBankLanded = Progress.Gems;
            shopBankPunch = 0f;
            if (shopBankIcon) shopBankIcon.localScale = Vector3.one;
        }

        /// <summary>The bank (as far as it has landed) and every pack's amount, price and bonus tag, from GemShop (the formula lives there, not in the scene).</summary>
        public void RefreshShop()
        {
            if (shopGems) shopGems.text = Money((long)shopBankShown);
            for (int i = 0; i < GemShop.Count; i++)
            {
                if (i < shopAmount.Length && shopAmount[i]) shopAmount[i].text = GemShop.Diamonds(i).ToString("N0", System.Globalization.CultureInfo.InvariantCulture);
                if (i < shopPrice.Length && shopPrice[i]) shopPrice[i].text = GemShop.PriceText(i);
                if (i < shopBonus.Length && shopBonus[i])
                {
                    int b = GemShop.BonusPercent(i);
                    shopBonus[i].text = "+" + b + "%";
                    if (shopBonus[i].transform.parent) shopBonus[i].transform.parent.gameObject.SetActive(b > 0);
                }
            }
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
            if (AudioManager.I == null) return;
            if (soundGlyph) soundGlyph.text = AudioManager.I.Muted ? "x" : "))";
            if (soundIcon && soundOn && soundOff) soundIcon.sprite = AudioManager.I.Muted ? soundOff : soundOn;
            if (soundHandle) soundHandle.anchoredPosition = new Vector2(AudioManager.I.Muted ? -soundHandleX : soundHandleX, soundHandle.anchoredPosition.y);
            if (soundIcons != null && soundOn && soundOff) foreach (var si in soundIcons) if (si) si.sprite = AudioManager.I.Muted ? soundOff : soundOn;
        }
    }
}
