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

        bool enabledByArgs;
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
            }
            if (!enabledByArgs && !(Application.isEditor && autoplayInEditor)) { enabled = false; return; }
            if (!enabledByArgs) seconds = float.MaxValue;
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
                if (startLevel > 0) gm.StartLevel(startLevel); else gm.OnTap();
            }
            if (gm.State == GameState.LevelClear || gm.State == GameState.GameOver)
            {
                tapT += dt;
                if (tapT > 1.3f) { tapT = 0f; gm.OnTap(); }
            }
            else tapT = 0f;

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
            float highAlt = cfg.altitudeSplit + cfg.enemyAltAboveSplit;
            Enemy near = null;
            foreach (var e in WaveSpawner.I.Active) if (!e.Dead && e.Z > 1f && (near == null || e.Z < near.Z)) near = e;
            bool up = gm.boss.Active || (near != null && (near.Parked || near.Z < 26f));
            float ta = up ? highAlt : cfg.supplyAlt;
            float tx = 0f;
            if (up && near != null && !gm.boss.Active) tx = Mathf.Clamp(near.X, -cfg.laneHalfWidth, cfg.laneHalfWidth) * 0.5f;   // drift toward the action, looks natural
            float dx = tx - squad.X, da = ta - squad.Alt;
            squad.AutoAxis = new Vector2(Mathf.Abs(dx) > 0.3f ? Mathf.Sign(dx) : 0f, Mathf.Abs(da) > 0.4f ? Mathf.Sign(da) : 0f);
        }

        string Status(GameManager gm)
        {
            var ws = WaveSpawner.I;
            int enemies = ws != null ? ws.Active.Count : 0, parked = ws != null ? ws.ParkedCount : 0, flight = ws != null ? ws.Flight : 0;
            var front = SupplyLane.I != null ? SupplyLane.I.Front : null;
            string frontS = front != null ? "\"" + front.Kind + ":" + Mathf.CeilToInt(front.Hp) + "\"" : "\"\"";
            return "{\"t\":" + Time.timeSinceLevelLoad.ToString("0.0") + ",\"state\":\"" + gm.State + "\",\"level\":" + gm.Level + ",\"levelTime\":" + gm.LevelTime.ToString("0.0") +
                   ",\"count\":" + gm.squad.Count + ",\"coins\":" + gm.Coins + ",\"kills\":" + gm.UnitsKilled + ",\"enemies\":" + enemies + ",\"parked\":" + parked + ",\"wave\":" + flight +
                   ",\"front\":" + frontS + ",\"weapon\":\"" + (gm.squad.Weapon != null ? gm.squad.Weapon.id : "") + "\",\"boss\":" + (gm.boss.Active ? Mathf.CeilToInt(gm.boss.Hp) : -1) +
                   ",\"fps\":" + (1f / Mathf.Max(0.0001f, Time.smoothDeltaTime)).ToString("0") + ",\"x\":" + gm.squad.X.ToString("0.0") + ",\"alt\":" + gm.squad.Alt.ToString("0.0") + "}";
        }

        void Log(string line)
        {
            if (string.IsNullOrEmpty(shotDir)) { Debug.Log("[AutoPilot] " + line); return; }
            try { File.AppendAllText(Path.Combine(shotDir, "status.jsonl"), line + "\n"); } catch { }
        }
    }
}
