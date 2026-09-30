// ShipSheet.cs (Editor only): renders each prefab in a list to a 480px jpg, seen from in front and above like the player sees a boss,
// so a pack's ships can be judged side by side (Captures/ships/<index>.jpg; the caller labels them).
using System.IO;
using UnityEditor;
using UnityEngine;

namespace SkySquad.EditorTools
{
    public static class ShipSheet
    {
        public static float Side = 1f;   // +1 looks from +Z, -1 from -Z (a boss prefab stands with his nose toward -Z)
        public static string Render(string[] paths, string dir)
        {
            Directory.CreateDirectory(dir);
            var pru = new PreviewRenderUtility();
            var log = "";
            try
            {
                for (int i = 0; i < paths.Length; i++)
                {
                    var prefab = AssetDatabase.LoadAssetAtPath<GameObject>(paths[i]);
                    if (prefab == null) { log += "missing " + paths[i] + "\n"; continue; }
                    var go = (GameObject)Object.Instantiate(prefab);
                    go.transform.position = Vector3.zero; go.transform.rotation = Quaternion.identity; go.transform.localScale = Vector3.one;
                    foreach (var c in go.GetComponentsInChildren<Collider>(true)) Object.DestroyImmediate(c);
                    foreach (var t in go.GetComponentsInChildren<Transform>(true)) if (t != null && t != go.transform && (t.name == "HpBar" || t.name == "HpLabel" || t.name == "Flash")) Object.DestroyImmediate(t.gameObject);   // the boss's bar and label are not the ship
                    var rs = go.GetComponentsInChildren<Renderer>();
                    if (rs.Length == 0) { Object.DestroyImmediate(go); log += "no renderer " + paths[i] + "\n"; continue; }
                    var b = rs[0].bounds; foreach (var r in rs) b.Encapsulate(r.bounds);
                    pru.AddSingleGO(go);
                    float rad = Mathf.Max(0.01f, b.extents.magnitude);
                    var cam = pru.camera;
                    cam.clearFlags = CameraClearFlags.SolidColor; cam.backgroundColor = new Color(0.16f, 0.36f, 0.6f);
                    cam.fieldOfView = 30f; cam.nearClipPlane = 0.01f; cam.farClipPlane = rad * 20f;
                    // the ship's nose is +Z (or whatever it is): look from +Z-ish, above and a little to the side
                    Vector3 dir3 = new Vector3(0.45f, 0.5f, Side).normalized;
                    cam.transform.position = b.center + dir3 * rad * 3.1f; cam.transform.LookAt(b.center);
                    pru.lights[0].intensity = 2.2f; pru.lights[0].transform.rotation = Quaternion.Euler(40f, 150f, 0f);
                    pru.ambientColor = new Color(0.8f, 0.8f, 0.85f);
                    var rect = new Rect(0, 0, 480, 480);
                    pru.BeginPreview(rect, GUIStyle.none);
                    cam.Render();
                    var tex = pru.EndPreview() as RenderTexture;
                    var old = RenderTexture.active; RenderTexture.active = tex;
                    var t2 = new Texture2D(480, 480, TextureFormat.RGB24, false); t2.ReadPixels(new Rect(0, 0, 480, 480), 0, 0); t2.Apply();
                    RenderTexture.active = old;
                    File.WriteAllBytes(Path.Combine(dir, i.ToString("000") + ".jpg"), t2.EncodeToJPG(88));
                    Object.DestroyImmediate(t2); Object.DestroyImmediate(go);
                }
            }
            finally { pru.Cleanup(); }
            return log;
        }
    }
}
