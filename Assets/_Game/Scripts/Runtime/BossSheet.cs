// BossSheet.cs
// Editor only. One picture of every boss of the world the game is in, parked on the front line and calm, cropped round him and laid out as a
// contact sheet (Captures/bosses_<world>.png) - the quick way to check thirty models, liveries and sizes at once (2026-10-02, the lava world).
// Started from execute_code: new GameObject().AddComponent<BossSheet>() (optionally set from / to / columns first).
#if UNITY_EDITOR
using System.Collections;
using System.IO;
using UnityEngine;

namespace SkySquad
{
    public class BossSheet : MonoBehaviour
    {
        public int from = 1, to = 30, columns = 6;
        public Rect crop = new Rect(20f, 470f, 500f, 300f);   // the screen pixels around the front line (portrait 540 x 960, y up from the bottom)
        public float scale = 0.7f;
        public float calm = 1.2f;
        public string name = "bosses";
        public bool Done { get; private set; }

        void Start() { StartCoroutine(Run()); }

        IEnumerator Run()
        {
            var gm = GameManager.I;
            TestMode.On = true;
            gm.StartLevel(1);
            gm.squad.AutoInput = true;
            var af = gm.squad.GetComponent<AutoFire>(); if (af != null) af.enabled = false;
            gm.enemies.debugFreeze = true;
            gm.supply.enabled = false;
            foreach (var b in FindObjectsByType<Breakable>(FindObjectsInactive.Exclude)) b.gameObject.SetActive(false);
            foreach (var g in FindObjectsByType<UpgradeGate>(FindObjectsInactive.Exclude)) g.gameObject.SetActive(false);
            yield return new WaitForSeconds(0.5f);
            int count = to - from + 1, rows = (count + columns - 1) / columns;
            int cw = Mathf.RoundToInt(crop.width * scale), ch = Mathf.RoundToInt(crop.height * scale);
            var sheet = new Texture2D(cw * columns, ch * rows, TextureFormat.RGB24, false);
            for (int n = from; n <= to; n++)
            {
                var boss = gm.enemies.DebugBoss(n);
                boss.Z = gm.config.enemyStopZ + 6f;
                float t = 0f;
                while (!boss.Parked && t < 8f) { yield return null; t += Time.deltaTime; }
                yield return new WaitForSeconds(calm);
                yield return new WaitForEndOfFrame();
                var tex = ScreenCapture.CaptureScreenshotAsTexture();
                var small = new Texture2D(cw, ch, TextureFormat.RGB24, false);
                int idx = n - from, cx = idx % columns, cy = rows - 1 - idx / columns;
                for (int y = 0; y < ch; y++)
                    for (int x = 0; x < cw; x++)
                        small.SetPixel(x, y, tex.GetPixel(Mathf.Clamp(Mathf.RoundToInt(crop.x + (x + 0.5f) / cw * crop.width), 0, tex.width - 1), Mathf.Clamp(Mathf.RoundToInt(crop.y + (y + 0.5f) / ch * crop.height), 0, tex.height - 1)));
                sheet.SetPixels(cx * cw, cy * ch, cw, ch, small.GetPixels());
                Destroy(tex); Destroy(small);
                boss.TakeDamage(boss.MaxHp * 2f);
                yield return new WaitForSeconds(0.25f);
            }
            sheet.Apply();
            Directory.CreateDirectory("Captures");
            File.WriteAllBytes("Captures/" + name + ".png", sheet.EncodeToPNG());
            Done = true;
        }
    }
}
#endif
