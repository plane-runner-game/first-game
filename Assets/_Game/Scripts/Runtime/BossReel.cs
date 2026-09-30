// BossReel.cs
// Editor only. Films every boss in turn for a video (2026-09-30: "a video of all 30 bosses fighting"): Test Mode's one plane that
// cannot be destroyed, the sky cleared, boss n dropped in close, left to fight for a while, hurt to just under half so he ENRAGES
// (his second attack, faster), then shot down. Time runs at a fixed 30 frames a second (Time.captureFramerate) and every frame goes
// to a jpg, so nothing drops however slow the editor is. Started from execute_code: new GameObject().AddComponent<BossReel>().
#if UNITY_EDITOR
using System.Collections;
using System.IO;
using System.Text;
using UnityEngine;

namespace SkySquad
{
    public class BossReel : MonoBehaviour
    {
        public string outDir = "Captures/reel";
        public int from = 1, to = 30;
        public int planes = 24;   // a real squad, so a sweep or a collapse to the middle can be seen
        public float calmSeconds = 5f, rageSeconds = 5f, wreckSeconds = 2.2f;
        public bool Done { get; private set; }
        public int Frame { get; private set; }

        readonly StringBuilder log = new StringBuilder();

        void Start() { StartCoroutine(Run()); }

        IEnumerator Run()
        {
            var gm = GameManager.I;
            Directory.CreateDirectory(outDir);
            Time.captureFramerate = 30;
            TestMode.On = true;
            gm.StartLevel(1);
            gm.squad.AutoInput = true;
            gm.squad.SetCount(planes, false);
            var ws = gm.enemies;
            ws.debugFreeze = true;
            gm.supply.enabled = false;   // no crates or gates in the frame: the bosses are the show
            HideSupply();
            yield return Wait(0.5f);
            for (int n = from; n <= to; n++)
            {
                HideSupply();
                var boss = ws.DebugBoss(n);
                boss.Z = gm.config.enemyStopZ + 26f;
                log.Append("{\"boss\":" + n + ",\"name\":\"" + ws.BossName + "\",\"start\":" + Frame + ",");
                float t = 0f;
                while (!boss.Parked && t < 8f) { yield return Wait(0f); t += 1f / 30f; }
                yield return Wait(calmSeconds);
                boss.TakeDamage(Mathf.Max(0f, boss.Hp - boss.MaxHp * 0.45f));   // just under half: he is enraged
                yield return Wait(rageSeconds);
                boss.TakeDamage(boss.MaxHp * 2f);
                yield return Wait(wreckSeconds);
                log.Append("\"enraged\":" + (boss.Enraged ? "true" : "false") + ",\"end\":" + Frame + "}\n");
                if (gm.State != GameState.Playing) break;
            }
            File.WriteAllText(Path.Combine(outDir, "reel.jsonl"), log.ToString());
            Time.captureFramerate = 0;
            Done = true;
        }

        static void HideSupply()
        {
            foreach (var b in FindObjectsByType<Breakable>(FindObjectsInactive.Exclude)) b.gameObject.SetActive(false);
            foreach (var g in FindObjectsByType<UpgradeGate>(FindObjectsInactive.Exclude)) g.gameObject.SetActive(false);
        }

        /// <summary>Waits this long in game time, capturing every frame on the way (a Wait(0) is one frame).</summary>
        IEnumerator Wait(float seconds)
        {
            int frames = Mathf.Max(1, Mathf.RoundToInt(seconds * 30f));
            for (int i = 0; i < frames; i++)
            {
                yield return new WaitForEndOfFrame();
                var tex = ScreenCapture.CaptureScreenshotAsTexture();
                File.WriteAllBytes(Path.Combine(outDir, "f" + Frame.ToString("00000") + ".jpg"), tex.EncodeToJPG(88));
                Destroy(tex);
                Frame++;
            }
        }
    }
}
#endif
