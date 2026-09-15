// AutoPilot.cs
// Test harness: run the build with "-autoplay -shots C:\dir -seconds 60" and a bot plays
// the game, saving a screenshot every few seconds plus a status.jsonl log. This is how
// the game gets verified without a human at the keyboard. Its policy is the intended
// player's: stay up and shoot while anything is parked (or about to park), dive for a crate
// only while the sky is quiet. Aim is band-wide, so it only ever picks an altitude.
using System;
using System.IO;
using UnityEngine;

namespace SkySquad
{
    public class AutoPilot : MonoBehaviour
    {
        public SquadController squad;
        public float shotEvery = 3f;
        public bool autoplayInEditor;   // flip in the Inspector to let the bot drive play mode

        bool enabledByArgs, resetProgress;
        float lobbyT;
        string shotDir;
        float seconds = 60f, shotT, statusT, tapT;
        int startLevel = 0, shotIndex;
        bool started;

        void Start()
        {
            var args = Environment.GetCommandLineArgs();
            for (int i = 0; i < args.Length; i++)
            {
                if (args[i] == "-autoplay") enabledByArgs = true;
                else if (args[i] == "-shots" && i + 1 < args.Length) shotDir = args[i + 1];
                else if (args[i] == "-seconds" && i + 1 < args.Length) float.TryParse(args[i + 1], out seconds);
                else if (args[i] == "-level" && i + 1 < args.Length) int.TryParse(args[i + 1], out startLevel);
                else if (args[i] == "-shotevery" && i + 1 < args.Length) float.TryParse(args[i + 1], out shotEvery);
                else if (args[i] == "-reset") resetProgress = true;
            }
            if (!enabledByArgs && !(Application.isEditor && autoplayInEditor)) { enabled = false; return; }
            if (!enabledByArgs) seconds = float.MaxValue;
            if (resetProgress) Progress.Reset();
            if (!string.IsNullOrEmpty(shotDir)) Directory.CreateDirectory(shotDir);
            squad.AutoInput = true;
            Log("autopilot on, seconds=" + seconds + " level=" + startLevel);
        }

        void Update()
        {
            var gm = GameManager.I;
            if (gm == null) return;
            float dt = Time.deltaTime;
            if (!started && Time.timeSinceLevelLoad > 1f)
            {
                started = true;
                if (startLevel > 0) gm.StartLevel(startLevel);
            }
            if (gm.State == GameState.LevelClear || gm.State == GameState.GameOver)
            {
                tapT += dt;
                if (tapT > 1.3f) { tapT = 0f; gm.OnTap(); }
            }
            else tapT = 0f;

            if (gm.State == GameState.Title)
            {   // the lobby, played like a player would: buy the cheapest upgrade while you can, then go again
                lobbyT += dt;
                if (lobbyT > 0.8f)
                {
                    lobbyT = 0f;
                    for (int guard = 0; guard < 12; guard++)
                    {
                        Upgrade best = Upgrade.FireRate; int bestCost = int.MaxValue;
                        for (int u = 0; u < 3; u++) { int c = Progress.Cost((Upgrade)u); if (c < bestCost) { bestCost = c; best = (Upgrade)u; } }
                        if (!Progress.Buy(best)) break;
                    }
                    Log("lobby: attempt " + (Progress.Attempts + 1) + " levels " + Progress.Levels[0] + "/" + Progress.Levels[1] + "/" + Progress.Levels[2] + " bank " + Progress.Coins);
                    gm.StartGame();
                }
            }
            else lobbyT = 0f;

            if (gm.State == GameState.Playing) Steer(gm);

            shotT += dt;
            if (shotT >= shotEvery && !string.IsNullOrEmpty(shotDir))
            {
                shotT = 0f;
                ScreenCapture.CaptureScreenshot(Path.Combine(shotDir, "shot_" + (shotIndex++).ToString("000") + ".png"));
            }
            statusT += dt;
            if (statusT >= 0.5f) { statusT = 0f; Log(Status(gm)); }
            if (Time.timeSinceLevelLoad >= seconds) { Log("autopilot done"); Application.Quit(); }
        }

        void Steer(GameManager gm)
        {
            var cfg = gm.config;
            var ws = WaveSpawner.I;
            var boss = ws.CurrentBoss;
            bool bossUp = boss != null && boss.Parked;
            // the nearest kamikaze still coming (not one loitering behind a boss)
            Enemy threat = null;
            foreach (var e in ws.Active)
                if (!e.Dead && !e.Kind.miniBoss && !e.Held && e.Z > -1f && (threat == null || e.Z < threat.Z)) threat = e;
            bool danger = threat != null && threat.Z < 20f;
            // dive for the crate when it is quick and nothing is close, or when down to the last planes
            var front = SupplyLane.I != null ? SupplyLane.I.Front : null;
            float crateSeconds = front != null ? front.Hp / Mathf.Max(0.5f, squad.Dps) : 99f;
            bool incoming = SupplyLane.I != null && SupplyLane.I.Incoming > 0;   // the crate just broke: its gate / squares are on their way, stay down for them
            bool wantCrate = incoming || (front != null && squad.Count < cfg.maxVisiblePlanes && (crateSeconds <= (bossUp ? 2.5f : danger ? 4.5f : 8f) || squad.Count <= 1));   // a ram costs 1, a crate gives 2: dive whenever it is quick
            bool up = !wantCrate && (threat != null || bossUp);
            float tx = front != null ? front.X : 0f;
            if (up)
            {   // get under the nearest kamikaze (they drift into your lane anyway), else line up on the boss
                if (threat != null && (!bossUp || threat.Z < 26f)) tx = threat.X;
                else if (boss != null) tx = boss.X;
            }
            float ta = up ? cfg.altitudeMax : cfg.supplyAlt;
            tx = Mathf.Clamp(tx, -cfg.laneHalfWidth, cfg.laneHalfWidth);
            float dx = tx - squad.X, da = ta - squad.Alt;
            squad.AutoAxis = new Vector2(Mathf.Abs(dx) > 0.15f ? Mathf.Sign(dx) : 0f, Mathf.Abs(da) > 0.3f ? Mathf.Sign(da) : 0f);
        }

        string Status(GameManager gm)
        {
            var ws = WaveSpawner.I;
            int enemies = ws != null ? ws.Active.Count : 0, parked = ws != null ? ws.ParkedCount : 0, flight = ws != null ? ws.Flight : 0;
            var front = SupplyLane.I != null ? SupplyLane.I.Front : null;
            string frontS = front != null ? "\"" + front.Kind + ":" + Mathf.CeilToInt(front.Hp) + "\"" : "\"\"";
            return "{\"t\":" + Time.timeSinceLevelLoad.ToString("0.0") + ",\"state\":\"" + gm.State + "\",\"level\":" + gm.Level + ",\"levelTime\":" + gm.LevelTime.ToString("0.0") +
                   ",\"count\":" + gm.squad.Count + ",\"coins\":" + gm.Coins + ",\"kills\":" + gm.UnitsKilled + ",\"enemies\":" + enemies + ",\"parked\":" + parked + ",\"wave\":" + flight + ",\"attempt\":" + Progress.Attempts + ",\"horde\":" + (ws != null ? ws.Horde : 0) +
                   ",\"front\":" + frontS + ",\"weapon\":\"" + (gm.squad.Weapon != null ? gm.squad.Weapon.id : "") + "\",\"boss\":" + (ws != null && ws.CurrentBoss != null ? Mathf.CeilToInt(ws.CurrentBoss.Hp) : -1) +
                   ",\"fps\":" + (1f / Mathf.Max(0.0001f, Time.smoothDeltaTime)).ToString("0") + ",\"x\":" + gm.squad.X.ToString("0.0") + ",\"alt\":" + gm.squad.Alt.ToString("0.0") + "}";
        }

        void Log(string line)
        {
            if (string.IsNullOrEmpty(shotDir)) { Debug.Log("[AutoPilot] " + line); return; }
            try { File.AppendAllText(Path.Combine(shotDir, "status.jsonl"), line + "\n"); } catch { }
        }
    }
}
