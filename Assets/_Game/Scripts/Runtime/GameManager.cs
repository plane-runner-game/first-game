// GameManager.cs
// The one object that knows what phase the game is in (title / playing / paused / cleared /
// lost), which level we are on, and the coins. Everything else asks it: GameManager.I.State
// ("I" = the single instance, like a Java static singleton).
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
        public int Best { get; private set; } = 1;
        public int Coins { get; private set; }
        public int UnitsKilled { get; set; }
        public float LevelTime { get; private set; }
        public float StateTime { get; private set; }
        public string LoseReason { get; private set; } = "";

        int coinsAtLevelStart;

        public event Action<GameState> OnStateChanged;

        public float LevelDuration => config.levelDurationBase + config.levelDurationPerLevel * Level;
        public bool BossPhase => boss != null && boss.Active;
        public float ScrollSpeed => (BossPhase && boss.Fighting) ? config.scrollSpeed * 0.35f : config.scrollSpeed;

        void Awake()
        {
            I = this;
            Best = PlayerPrefs.GetInt("sky_best", 1);
            Application.targetFrameRate = 60;
        }

        void Start() { SetState(GameState.Title); }

        void Update()
        {
            StateTime += Time.deltaTime;
            if (input != null && input.Tapped) OnTap();
            if (State != GameState.Playing) return;
            LevelTime += Time.deltaTime;
            if (!boss.Active && LevelTime >= LevelDuration) boss.Summon();
        }

        public void OnTap()
        {
            switch (State)
            {
                case GameState.Title: if (StateTime > 0.3f) StartGame(); break;
                case GameState.Paused: if (StateTime > 0.3f) Resume(); break;
                case GameState.LevelClear: if (StateTime > 0.8f) NextLevel(); break;
                case GameState.GameOver: if (StateTime > 1.0f) Retry(); break;
            }
        }

        public void StartGame() { Level = 1; Coins = 0; StartLevel(1); }
        public void NextLevel() { StartLevel(Level + 1); }
        public void Retry() { Coins = coinsAtLevelStart; StartLevel(Level); }

        /// <summary>The HUD pause button. Resuming is a tap anywhere (see OnTap).</summary>
        public void Pause() { if (State == GameState.Playing) SetState(GameState.Paused); }
        public void Resume() { if (State == GameState.Paused) SetState(GameState.Playing); }

        public void StartLevel(int n)
        {
            Level = n;
            LevelTime = 0f;
            UnitsKilled = 0;
            LoseReason = "";
            coinsAtLevelStart = Coins;
            if (n > Best) { Best = n; PlayerPrefs.SetInt("sky_best", n); PlayerPrefs.Save(); }
            fx.ClearAll();
            enemies.ResetForLevel(n);
            supply.ResetForLevel(n);
            boss.ResetForLevel();
            squad.ResetForLevel(config.startCount + (n - 1) * config.startCountPerLevel);
            SetState(GameState.Playing);
            hud.Banner("LEVEL " + n, Color.white, 1.3f);
            hud.ShowHint(n == 1 ? 9f : 3f);
        }

        public void AddCoins(int c)
        {
            if (c <= 0) return;
            Coins += c;
            if (hud != null) hud.CoinPop(c);
        }

        public void LevelCleared()
        {
            AddCoins(squad.Count * 2);
            sfx.Play(Sfx.Clear);
            SetState(GameState.LevelClear);
        }

        public void Lose(string reason)
        {
            if (State != GameState.Playing) return;
            LoseReason = reason;
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
