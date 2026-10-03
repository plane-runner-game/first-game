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
        public WorldManager worlds;                  // the sea and the lava (2026-10-02): which one is on, and the world-select screen

        public GameState State { get; private set; } = GameState.Title;
        public int Level { get; private set; } = 1;
        public int Coins => Progress.Coins;          // the bank, live
        public int RunCoins { get; private set; }    // earned this attempt
        public int UnitsKilled { get; set; }
        public float LevelTime { get; private set; }
        public float StateTime { get; private set; }
        public string LoseReason { get; private set; } = "";
        public bool Won { get; private set; }         // this attempt killed the last boss (the clear panel shows VICTORY instead of BOSS DOWN)
        public bool Revived { get; private set; }     // this attempt's one revive is spent (the death screen offers no second)
        bool armed;                                   // the round is set up and waiting under the lobby (PrepareLevel): the first swipe starts it without a second reset

        public event Action<GameState> OnStateChanged;

        public float LevelDuration => config.endless ? float.PositiveInfinity : config.levelDurationBase + config.levelDurationPerLevel * Level;
        public bool BossPhase => boss != null && boss.Active;
        public float ScrollSpeed => (BossPhase && boss.Fighting) ? config.scrollSpeed * 0.35f : config.scrollSpeed;

        void Awake()
        {
            I = this;
            Progress.Load();
#if UNITY_WEBGL && !UNITY_EDITOR
            Application.targetFrameRate = -1;   // the browser's own animation frame (a 60 cap makes the web player pace with setTimeout: judder), 2026-09-19
#else
            Application.targetFrameRate = 60;
#endif
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

        /// <summary>A tap anywhere: resumes from pause, leaves the clear screen for the lobby. The lobby and the death screen
        /// use buttons (upgrade cards; REVIVE / RESTART) so a stray tap never launches or throws away an attempt.</summary>
        public void OnTap()
        {
            if (hud != null && hud.SettingsOpen) return;   // taps on the settings panel (slider, DONE) are not "tap to resume"
            switch (State)
            {
                case GameState.Paused: if (StateTime > 0.3f) Resume(); break;
                case GameState.LevelClear: if (StateTime > 0.8f) Lobby(); break;
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
            Revived = false;
            CancelInvoke(nameof(ShowWin));
            fx.ClearAll();
            enemies.ResetForLevel(1);
            supply.ResetForLevel(1);
            boss.ResetForLevel();
            squad.ResetForLevel(TestMode.On ? TestMode.StartPlanes : config.startCount);
            armed = true;
        }

        /// <summary>The world the player is in (0 = sea, 1 = lava ...).</summary>
        /// <summary>How many bosses end the round in this world: the world's own count (the meadow has 5), else the config's.</summary>
        public int LastBoss { get { var e = worlds != null ? worlds.Entry : null; return e != null && e.lastBoss > 0 ? e.lastBoss : config.lastBoss; } }

        public int WorldIndex => worlds != null && worlds.Current >= 0 ? worlds.Current : Mathf.Max(0, Progress.World);

        /// <summary>The world-select screen's choice (lobby only): the scene, the light, the cast and the props switch, and the round waiting under the
        /// lobby is set up again in the new world on the next frame. Remembered between launches.</summary>
        public bool SelectWorld(int i)
        {
            if (State != GameState.Title || worlds == null || i < 0 || i >= worlds.Count) return false;
            if (i == worlds.Current) return true;
            Progress.World = i;
            Progress.Save();
            fx.ClearAll();
            worlds.Apply(i);
            armed = false;   // Update -> PrepareLevel: the crowd, the crates and the squad again, now with this world's planes
            if (hud != null) hud.RefreshLobby();
            return true;
        }

        public void Lobby() { if (State != GameState.Playing) SetState(GameState.Title); }
        /// <summary>HOME from the pause screen (2026-09-19): the attempt is abandoned - the sky cleared, the coins kept - and the lobby comes up.</summary>
        public void Home()
        {
            if (State != GameState.Playing && State != GameState.Paused) return;
            if (enemies != null) { Progress.NoteHorde(enemies.Horde); enemies.ClearSky(); }
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
            Revived = false;
            CancelInvoke(nameof(ShowWin));
            fx.ClearAll();
            enemies.ResetForLevel(n);
            supply.ResetForLevel(n);
            boss.ResetForLevel();
            squad.ResetForLevel(TestMode.On ? TestMode.StartPlanes : config.startCount + (n - 1) * config.startCountPerLevel);
            SetState(GameState.Playing);
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
            Progress.NoteWon();
            if (enemies != null) Progress.NoteHorde(enemies.Horde);
            Progress.Save();
            sfx.Play(Sfx.Big);
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
            if (enemies != null) Progress.NoteHorde(enemies.Horde);
            Progress.Save();
            sfx.Play(Sfx.Lose);
            sfx.Play(Sfx.Over);
            fx.Explosion(squad.transform.position, true);
            SetState(GameState.GameOver);
        }

        /// <summary>The death screen may offer REVIVE: the squad is down and this attempt has not used its revive yet.</summary>
        public bool CanRevive => State == GameState.GameOver && !Revived && squad != null;

        /// <summary>The planes a revive brings back: reviveShare of the best count of the attempt, never fewer than the start.</summary>
        public int RevivePlanes => squad == null ? 0 : Mathf.Max(Mathf.Max(1, config.startCount), Mathf.CeilToInt(squad.Peak * config.reviveShare));

        /// <summary>REVIVE (after the rewarded ad, Ads.cs): the attempt goes on where it fell. The squad flies back in behind a shield,
        /// every plane in the air goes (a boss stays, his health as it was), the clock and the coins carry on. Once per attempt.</summary>
        public void Revive()
        {
            if (!CanRevive) return;
            Revived = true;
            LoseReason = "";
            if (enemies != null) enemies.ClearForRevive();
            squad.Revive(RevivePlanes, config.reviveShield);
            if (fx != null) { fx.Ring(squad.transform.position + Vector3.up * 0.5f, new Color(0.58f, 0.77f, 0.99f), 8f); fx.Flash(Color.white, 0.35f); }
            if (sfx != null) sfx.Play(Sfx.Big);
            SetState(GameState.Playing);
        }

        /// <summary>RESTART on the death screen: back to the start line - the lobby, the round armed and waiting for the first swipe.</summary>
        public void Restart() { if (State == GameState.GameOver) Lobby(); }

        void SetState(GameState s)
        {
            State = s;
            StateTime = 0f;
            OnStateChanged?.Invoke(s);
        }
    }
}
