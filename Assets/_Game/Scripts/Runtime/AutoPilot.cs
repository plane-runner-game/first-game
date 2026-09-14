// AutoPilot.cs
// Test harness: run the build with "-autoplay -shots C:\dir -seconds 60" and a bot plays
// the game, saving a screenshot every few seconds plus a status.jsonl log. This is how
// the game gets verified without a human at the keyboard.
using System;
using System.IO;
using UnityEngine;

namespace SkySquad
{
    public class AutoPilot : MonoBehaviour
    {
        public SquadController squad;
        public float shotEvery = 3f;

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
            if (!enabledByArgs) { enabled = false; return; }
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
            float tx = squad.X, ta = squad.Alt;
            bool have = false;
            if (gm.boss.Active && gm.boss.Fighting)
            {
                tx = 0f; ta = 3f; have = true;
                Horde near = null;
                foreach (var h in HordeSpawner.I.Active) if (!h.Dead && h.Z < 25f && (near == null || h.Z < near.Z)) near = h;
                if (near != null) { tx = near.X; ta = near.Alt; }
            }
            else
            {
                Horde h0 = null;
                foreach (var h in HordeSpawner.I.Active) if (!h.Dead && h.Z > 10f && (h0 == null || h.Z < h0.Z)) h0 = h;
                Pickup p0 = null;
                foreach (var p in PickupSpawner.I.Active)
                {
                    if (p.Dead || p.Z <= 6f) continue;
                    if (p.Kind == PickupKind.Weapon) continue;
                    if (p0 == null || p.Z < p0.Z) p0 = p;
                }
                float split = GameManager.I.config.altitudeSplit;
                bool committed = p0 != null && p0.Z < 22f && Mathf.Abs(p0.X - squad.X) < 2.5f && (squad.Alt >= split) == p0.High;
                if (committed) { tx = p0.X; ta = p0.High ? split + 2.2f : 2.2f; have = true; }
                else if (h0 != null)
                {
                    bool urgent = h0.Z < 26f || h0.Units * h0.Kind.contactPower >= squad.Count;
                    float secondsToArrive = Mathf.Max(0f, h0.Z - 12f) / (GameManager.I.ScrollSpeed + h0.Kind.approachSpeed);
                    bool killableLater = h0.Units * h0.Kind.unitHp < squad.Dps * secondsToArrive * 0.8f;
                    if (p0 != null && !urgent && killableLater && p0.Z < h0.Z + 40f) { tx = p0.X; ta = p0.High ? split + 2.2f : 2.2f; }
                    else { tx = h0.X; ta = h0.Alt; }
                    have = true;
                }
                else if (p0 != null) { tx = p0.X; ta = p0.High ? split + 2.2f : 2.2f; have = true; }
            }
            if (!have) { squad.AutoAxis = Vector2.zero; return; }
            float dx = tx - squad.X, da = ta - squad.Alt;
            squad.AutoAxis = new Vector2(Mathf.Abs(dx) > 0.3f ? Mathf.Sign(dx) : 0f, Mathf.Abs(da) > 0.4f ? Mathf.Sign(da) : 0f);
        }

        string Status(GameManager gm)
        {
            int hordes = HordeSpawner.I != null ? HordeSpawner.I.Active.Count : 0;
            int maxUnits = 0; if (HordeSpawner.I != null) foreach (var h in HordeSpawner.I.Active) maxUnits = Mathf.Max(maxUnits, h.Units);
            return "{\"t\":" + Time.timeSinceLevelLoad.ToString("0.0") + ",\"state\":\"" + gm.State + "\",\"level\":" + gm.Level + ",\"levelTime\":" + gm.LevelTime.ToString("0.0") +
                   ",\"count\":" + gm.squad.Count + ",\"shield\":" + gm.squad.Shield + ",\"kills\":" + gm.UnitsKilled + ",\"hordes\":" + hordes + ",\"maxUnits\":" + maxUnits +
                   ",\"weapon\":\"" + (gm.squad.Weapon != null ? gm.squad.Weapon.id : "") + "\",\"boss\":" + (gm.boss.Active ? Mathf.CeilToInt(gm.boss.Hp) : -1) +
                   ",\"fps\":" + (1f / Mathf.Max(0.0001f, Time.smoothDeltaTime)).ToString("0") + ",\"x\":" + gm.squad.X.ToString("0.0") + ",\"alt\":" + gm.squad.Alt.ToString("0.0") + "}";
        }

        void Log(string line)
        {
            if (string.IsNullOrEmpty(shotDir)) { Debug.Log("[AutoPilot] " + line); return; }
            try { File.AppendAllText(Path.Combine(shotDir, "status.jsonl"), line + "\n"); } catch { }
        }
    }
}
