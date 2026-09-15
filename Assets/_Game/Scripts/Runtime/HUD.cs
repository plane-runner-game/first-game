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
        [Header("Overlays")]
        public GameObject pausePanel;
        public GameObject clearPanel;
        public TextMeshProUGUI clearStats;
        public GameObject overPanel;
        public TextMeshProUGUI overReason;
        public TextMeshProUGUI overStats;
        public GameObject playGroup;
        [Header("Buttons")]
        public TextMeshProUGUI soundGlyph;

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
            if (s == GameState.LevelClear && clearStats) clearStats.text = "Planes left: " + gm.squad.Count + "   ·   kills: " + gm.UnitsKilled + "   ·   coins " + gm.Coins;
            if (s == GameState.GameOver)
            {
                var ws = WaveSpawner.I;
                if (overReason) overReason.text = gm.LoseReason;
                if (overStats) overStats.text = "ATTEMPT " + Progress.Attempts + "   ·   horde " + (ws != null ? ws.Horde : 1) + "   ·   kills " + gm.UnitsKilled + "\n+" + gm.RunCoins + " coins for the next attempt";
            }
        }

        /// <summary>Lobby numbers: the bank, the attempt counter, and each card: level / effect / price.</summary>
        public void RefreshLobby()
        {
            if (lobbyCoins) lobbyCoins.text = "$ " + Progress.Coins;
            if (attemptInfo) attemptInfo.text = "ATTEMPT " + (Progress.Attempts + 1) + "   ·   best: horde " + Mathf.Max(1, Progress.BestHorde);
            for (int i = 0; i < 3; i++)
            {
                var u = (Upgrade)i;
                if (cardLevel != null && i < cardLevel.Length && cardLevel[i]) cardLevel[i].text = "LV " + Progress.Levels[i];
                if (cardEffect != null && i < cardEffect.Length && cardEffect[i]) cardEffect[i].text = Progress.Effect(u);
                if (cardCost != null && i < cardCost.Length && cardCost[i]) { cardCost[i].text = "$ " + Progress.Cost(u); cardCost[i].color = Progress.CanBuy(u) ? Gold : Dim; }
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
            if (coinsText) coinsText.text = "$ " + Progress.Coins;
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
                if (boss != null) { prog = boss.MaxHp > 0f ? boss.Hp / boss.MaxHp : 0f; c = Red; txt = "BOSS " + ws.Bosses + "   " + Mathf.CeilToInt(boss.Hp); }
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
            popAmount = popT > 0f ? popAmount + n : n;
            popT = 1.2f;
            if (coinPopText) { coinPopText.text = "+" + popAmount; coinPopText.transform.localScale = Vector3.one * 1.3f; }
        }

        public void OnPauseButton()
        {
            var gm = GameManager.I;
            if (gm != null) gm.Pause();
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
