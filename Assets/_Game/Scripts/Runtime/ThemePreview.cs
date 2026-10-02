// ThemePreview.cs
// Editor only. Shows each candidate level background the way the game would draw it (2026-10-01: "show me how the ten levels will look"): the
// sky material, the fog, the sun, the sea's colours and the cloud bank swapped per theme, a boss fighting in front of a squad of 24. One jpg per
// theme in Captures/themes. Nothing is saved: the scene and its materials are put back as they were.
#if UNITY_EDITOR
using System.Collections;
using System.IO;
using UnityEngine;
using UnityEngine.Rendering;

namespace SkySquad
{
    public class ThemePreview : MonoBehaviour
    {
        [System.Serializable]
        public class Theme
        {
            public string name, skyPath;
            public Color fog, sun, waterBase, waterShallow, waterHorizon, cloud;
            public float sunIntensity = 1.2f, sunPitch = 40f, ambient = 1f, exposure = 1f;
            public int boss = 1;
            public bool hideClouds;
        }

        public Theme[] themes;
        public string outDir = "Captures/themes";
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
            gm.squad.SetCount(24, false);
            var af = gm.squad.GetComponent<AutoFire>(); if (af != null) af.enabled = false;
            gm.enemies.debugFreeze = true;
            gm.supply.enabled = false;
            foreach (var b in FindObjectsByType<Breakable>(FindObjectsInactive.Exclude)) b.gameObject.SetActive(false);
            foreach (var g in FindObjectsByType<UpgradeGate>(FindObjectsInactive.Exclude)) g.gameObject.SetActive(false);
            Light sun = RenderSettings.sun;
            Material water = null, cloud = null; GameObject cloudGo = null;
            foreach (var r in FindObjectsByType<Renderer>(FindObjectsSortMode.None))
            {
                if (r.name == "Water") water = r.material;                // instance: the asset is never touched
                if (r.name == "WaterFar") r.sharedMaterial = null;        // set below with the same instance
                if (r.name == "CloudWall") { cloud = r.material; cloudGo = r.gameObject; }
            }
            foreach (var r in FindObjectsByType<Renderer>(FindObjectsSortMode.None)) if (r.name == "WaterFar" && water != null) r.sharedMaterial = water;
            yield return Frames(20);
            for (int i = 0; i < themes.Length; i++)
            {
                var t = themes[i];
                var sky = UnityEditor.AssetDatabase.LoadAssetAtPath<Material>(t.skyPath);
                if (sky != null) { sky = new Material(sky); if (sky.HasProperty("_Exposure")) sky.SetFloat("_Exposure", t.exposure); RenderSettings.skybox = sky; }
                RenderSettings.fogColor = t.fog;
                RenderSettings.ambientIntensity = t.ambient;
                DynamicGI.UpdateEnvironment();
                if (sun != null) { sun.color = t.sun; sun.intensity = t.sunIntensity; sun.transform.rotation = Quaternion.Euler(t.sunPitch, -28f, 0f); }
                if (water != null) { water.SetColor("_BaseColor", t.waterBase); water.SetColor("_ShallowColor", t.waterShallow); water.SetColor("_HorizonColor", t.waterHorizon); }
                if (cloud != null) cloud.SetColor("_Color", t.cloud);
                if (cloudGo != null) cloudGo.SetActive(!t.hideClouds);
                var boss = gm.enemies.DebugBoss(t.boss);
                boss.Z = gm.config.enemyStopZ + 22f;
                yield return Frames(30 * 5);
                yield return Shot(i);
                yield return Frames(24);
                boss.TakeDamage(boss.MaxHp * 2f);
                yield return Frames(30 * 2);
            }
            Time.captureFramerate = 0;
            Done = true;
        }

        IEnumerator Frames(int n) { for (int i = 0; i < n; i++) yield return null; }

        IEnumerator Shot(int i)
        {
            yield return new WaitForEndOfFrame();
            var tex = ScreenCapture.CaptureScreenshotAsTexture();
            File.WriteAllBytes(Path.Combine(outDir, i.ToString("00") + ".jpg"), tex.EncodeToJPG(90));
            Destroy(tex);
        }
    }
}
#endif
