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

        public event Action<GameState> OnStateChanged;

        public float LevelDuration => config.endless ? float.PositiveInfinity : config.levelDurationBase + config.levelDurationPerLevel * Level;
        // the levels (2026-09-18): level n has n bosses; hp and stream rate scale linearly through the tuned baseline level (GameConfig.levelBaseline)
        public int LevelCount => Mathf.Max(1, config.levelCount);
        public int BossCount => Mathf.Max(1, Level);
        float LevelLine(float atLevel1) { float t = (Level - 1f) / Mathf.Max(1f, config.levelBaseline - 1f); return Mathf.LerpUnclamped(atLevel1, 1f, t); }
        public float HpScale => LevelLine(config.level1HpScale);
        public float RateScale => LevelLine(config.level1RateScale);
        public bool GameCompleted => Won && Level >= LevelCount;   // this attempt cleared the last level
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
            StartLevel(Mathf.Clamp(Progress.Stage, 1, LevelCount));   // the level chosen in the lobby (the levels, 2026-09-18)
        }

        public void Lobby() { if (State != GameState.Playing) SetState(GameState.Title); }
        /// <summary>The lobby's level arrows: any level up to the one after the highest cleared.</summary>
        public void SelectLevel(int delta)
        {
            if (State != GameState.Title) return;
            Progress.Stage = Mathf.Clamp(Progress.Stage + delta, 1, Mathf.Min(LevelCount, Progress.Cleared + 1));
            Progress.Save();
            if (hud != null) hud.RefreshLobby();
        }
        public void Pause() { if (State == GameState.Playing) SetState(GameState.Paused); }
        public void Resume() { if (State == GameState.Paused) SetState(GameState.Playing); }

        public void StartLevel(int n)
        {
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
            hud.Banner("LEVEL " + n, Color.white, 1.3f);
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
            Progress.Cleared = Mathf.Max(Progress.Cleared, Level);
            if (Level < LevelCount) Progress.Stage = Level + 1; else Progress.Won = true;   // the next level opens; the last one clears the game
            if (enemies != null) Progress.BestHorde = Mathf.Max(Progress.BestHorde, enemies.Horde);
            Progress.Save();
            sfx.Play(Sfx.Big);
            hud.Banner(GameCompleted ? "VICTORY!" : "LEVEL " + Level + " CLEARED", new Color(1f, 0.82f, 0.25f), 1.6f);
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
