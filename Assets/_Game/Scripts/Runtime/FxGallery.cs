// FxGallery.cs
// Editor only. Plays each effect prefab in the list in front of the squad and photographs it 0.7 s and 1.5 s in (Captures/fxgallery), so an
// effect's size, direction and length can be read before a boss is built on it. Also writes gallery.txt: every prefab's longest duration,
// whether it loops, and its particle systems' count.
#if UNITY_EDITOR
using System.Collections;
using System.IO;
using System.Text;
using UnityEngine;

namespace SkySquad
{
    public class FxGallery : MonoBehaviour
    {
        public string[] paths;
        public string outDir = "Captures/fxgallery";
        public Vector3 at = new Vector3(0f, 2f, 8f);
        public float scale = 3f;
        public bool Done { get; private set; }

        void Start() { StartCoroutine(Run()); }

        IEnumerator Run()
        {
            Directory.CreateDirectory(outDir);
            var gm = GameManager.I;
            Time.captureFramerate = 30;
            TestMode.On = true;
            gm.StartLevel(1);
            gm.squad.AutoInput = true;
            var af = gm.squad.GetComponent<AutoFire>(); if (af != null) af.enabled = false;   // no bullet streams in the picture
            gm.squad.SetCount(12, false);
            gm.enemies.debugFreeze = true;
            gm.enemies.ClearSky();
            gm.supply.enabled = false;
            foreach (var b in FindObjectsByType<Breakable>(FindObjectsInactive.Exclude)) b.gameObject.SetActive(false);
            foreach (var g in FindObjectsByType<UpgradeGate>(FindObjectsInactive.Exclude)) g.gameObject.SetActive(false);
            yield return Frames(15);
            var info = new StringBuilder();
            for (int i = 0; i < paths.Length; i++)
            {
                var prefab = UnityEditor.AssetDatabase.LoadAssetAtPath<GameObject>(paths[i]);
                if (prefab == null) { info.AppendLine(i + " MISSING " + paths[i]); continue; }
                var go = Instantiate(prefab, at, Quaternion.identity); go.transform.localScale = Vector3.one * scale;
                float dur = 0f; bool loop = false; int n = 0;
                foreach (var ps in go.GetComponentsInChildren<ParticleSystem>(true)) { var m = ps.main; n++; loop |= m.loop; dur = Mathf.Max(dur, m.duration + m.startLifetime.constantMax); }
                info.AppendLine(i + " " + paths[i] + " systems=" + n + " loop=" + loop + " length=" + dur.ToString("0.0"));
                yield return Frames(21);
                yield return Shot(i, 0);
                yield return Frames(24);
                yield return Shot(i, 1);
                Destroy(go);
                yield return Frames(6);
            }
            File.WriteAllText(Path.Combine(outDir, "gallery.txt"), info.ToString());
            Time.captureFramerate = 0;
            Done = true;
        }

        IEnumerator Frames(int n) { for (int i = 0; i < n; i++) yield return null; }

        IEnumerator Shot(int i, int k)
        {
            yield return new WaitForEndOfFrame();
            var tex = ScreenCapture.CaptureScreenshotAsTexture();
            File.WriteAllBytes(Path.Combine(outDir, i.ToString("000") + "_" + k + ".jpg"), tex.EncodeToJPG(85));
            Destroy(tex);
        }
    }
}
#endif
