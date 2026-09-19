// GameManager.cs
// The one object that knows what phase the game is in (lobby / playing / paused / lost), the
// live numbers of the attempt, and the coin bank via Progress. Everything else asks it:
// GameManager.I.State ("I" = the single instance, like a Java static singleton).
// The loop: lobby (buy upgrades) -> the same round every time -> die -> lobby with more coins.
using System;
using UnityEngine;

namespace SkySquad
{
    public enum GameState { Title, Playing, Paused, LevelClear, GameOver }

    public class GameManager : MonoBehaviour
    {
        public static GameManager I { get; private set; }

        [Header("Wiring (set by SceneBuilder)")]
        public GameConfig config;
        public SquadController squad;
        public SquadInput input;
        public WaveSpawner enemies;
        public SupplyLane supply;
        public BossController boss;
        public HUD hud;
        public FXManager fx;
        public AudioManager sfx;
        public WorldScroller world;

        public GameState State { get; private set; } = GameState.Title;
        public int Level { get; private set; } = 1;
        public int Coins => Progress.Coins;          // the bank, live
        public int RunCoins { get; private set; }    // earned this attempt
        public int UnitsKilled { get; set; }
        public float LevelTime { get; private set; }
        public float StateTime { get; private set; }
        public string LoseReason { get; private set; } = "";
        public bool Won { get; private set; }         // this attempt killed the last boss (the clear panel shows VICTORY instead of BOSS DOWN)
        bool armed;                                   // the round is set up and waiting under the lobby (PrepareLevel): the first swipe starts it without a second reset

        public event Action<GameState> OnStateChanged;

        public float LevelDuration => config.endless ? float.PositiveInfinity : config.levelDurationBase + config.levelDurationPerLevel * Level;
        public bool BossPhase => boss != null && boss.Active;
        public float ScrollSpeed => (BossPhase && boss.Fighting) ? config.scrollSpeed * 0.35f : config.scrollSpeed;

        void Awake()
        {
            I = this;
            Progress.Load();
            Application.targetFrameRate = 60;
        }

        void Start() { SetState(GameState.Title); }

        void Update()
        {
            StateTime += Time.deltaTime;
            if (input != null && input.Tapped) OnTap();
            if (State == GameState.Title)
            {   // the lobby is the level itself, waiting (2026-09-19, the reference's menu): armed on the first frame here, started by the first swipe
                if (!armed) PrepareLevel();
                if (input != null && input.Swiping && StateTime > 0.35f && !(hud != null && (hud.SettingsOpen || (hud.splashPanel != null && hud.splashPanel.activeSelf)))) StartGame();   // not under the loading splash
                return;
            }
            if (State != GameState.Playing) return;
            LevelTime += Time.deltaTime;
            if (!config.endless && !boss.Active && LevelTime >= LevelDuration) boss.Summon();
        }

        /// <summary>A tap anywhere: resumes from pause, leaves the death screen for the lobby. The lobby itself
        /// uses buttons (upgrade cards + start) so a stray tap never launches an attempt.</summary>
        public void OnTap()
        {
            if (hud != null && hud.SettingsOpen) return;   // taps on the settings panel (slider, DONE) are not "tap to resume"
            switch (State)
            {
                case GameState.Paused: if (StateTime > 0.3f) Resume(); break;
                case GameState.LevelClear: if (StateTime > 0.8f) Lobby(); break;
                case GameState.GameOver: if (StateTime > 1.0f) Lobby(); break;
            }
        }

        public void StartGame()
        {
            if (State == GameState.Playing) return;
            Progress.Attempts++;
            Progress.Save();
            if (armed && State == GameState.Title)
            {   // the round is already set up under the lobby: just let it run
                armed = false;
                SetState(GameState.Playing);
                hud.Banner("ATTEMPT " + Progress.Attempts, Color.white, 1.3f);
                hud.ShowHint(Progress.Attempts <= 1 ? 9f : 3f);
            }
            else StartLevel(1);
        }

        /// <summary>Sets round 1 up under the lobby: the squad on its mark, the crates and the opening crowd ahead, nothing moving
        /// (every Update loop waits for Playing). The menu shows the game itself, like the reference; the first swipe starts it.</summary>
        void PrepareLevel()
        {
            Level = 1;
            LevelTime = 0f;
            UnitsKilled = 0;
            RunCoins = 0;
            LoseReason = "";
            Won = false;
            CancelInvoke(nameof(ShowWin));
            fx.ClearAll();
            enemies.ResetForLevel(1);
            supply.ResetForLevel(1);
            boss.ResetForLevel();
            squad.ResetForLevel(config.startCount);
            armed = true;
        }

        public void Lobby() { if (State != GameState.Playing) SetState(GameState.Title); }
        /// <summary>HOME from the pause screen (2026-09-19): the attempt is abandoned - the sky cleared, the coins kept - and the lobby comes up.</summary>
        public void Home()
        {
            if (State != GameState.Playing && State != GameState.Paused) return;
            if (enemies != null) { Progress.BestHorde = Mathf.Max(Progress.BestHorde, enemies.Horde); enemies.ClearSky(); }
            if (fx != null) fx.ClearAll();
            Progress.Save();
            SetState(GameState.Title);
        }
        public void Pause() { if (State == GameState.Playing) SetState(GameState.Paused); }
        public void Resume() { if (State == GameState.Paused) SetState(GameState.Playing); }

        public void StartLevel(int n)
        {
            armed = false;
            Level = n;
            LevelTime = 0f;
            UnitsKilled = 0;
            RunCoins = 0;
            LoseReason = "";
            Won = false;
            CancelInvoke(nameof(ShowWin));
            fx.ClearAll();
            enemies.ResetForLevel(n);
            supply.ResetForLevel(n);
            boss.ResetForLevel();
            squad.ResetForLevel(config.startCount + (n - 1) * config.startCountPerLevel);
            SetState(GameState.Playing);
            hud.Banner("ATTEMPT " + Progress.Attempts, Color.white, 1.3f);
            hud.ShowHint(Progress.Attempts <= 1 ? 9f : 3f);
        }

        /// <summary>Coins go straight into the bank, scaled by the revenue upgrade.</summary>
        public int AddCoins(int c)
        {
            if (c <= 0) return 0;
            int v = Mathf.Max(1, Mathf.RoundToInt(c * Progress.RevenueMult));
            Progress.Coins += v;
            RunCoins += v;
            if (hud != null) hud.CoinPop(v);
            return v;
        }

        public void LevelCleared()
        {
            AddCoins(squad.Count * 2);
            sfx.Play(Sfx.Clear);
            SetState(GameState.LevelClear);
        }

        /// <summary>The last boss is down: the round is won. The victory panel comes after a beat so the explosion plays out.</summary>
        public void Win()
        {
            if (State != GameState.Playing || Won) return;
            Won = true;
            Progress.Won = true;
            if (enemies != null) Progress.BestHorde = Mathf.Max(Progress.BestHorde, enemies.Horde);
            Progress.Save();
            sfx.Play(Sfx.Big);
            hud.Banner("VICTORY!", new Color(1f, 0.82f, 0.25f), 1.6f);
            Invoke(nameof(ShowWin), 1.6f);
        }

        void ShowWin()
        {
            if (State != GameState.Playing || !Won) return;
            sfx.Play(Sfx.Clear);
            SetState(GameState.LevelClear);
        }

        public void Lose(string reason)
        {
            if (State != GameState.Playing) return;
            LoseReason = reason;
            if (enemies != null) Progress.BestHorde = Mathf.Max(Progress.BestHorde, enemies.Horde);
            Progress.Save();
            sfx.Play(Sfx.Lose);
            sfx.Play(Sfx.Over);
            fx.Explosion(squad.transform.position, true);
            SetState(GameState.GameOver);
        }

        void SetState(GameState s)
        {
            State = s;
            StateTime = 0f;
            OnStateChanged?.Invoke(s);
        }
    }
}
