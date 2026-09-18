// HangarShowcase.cs
// The title screen's hero: a real 3D aircraft (the EmbersStorm AirStrike pack's fighter jet) turning slowly on a stand,
// rendered by its own camera into a RenderTexture that the lobby shows in a RawImage. The rig lives far under the sea on
// its own layer so neither camera sees the other's world; HUD switches the whole rig on with the title panel and off with
// it, so it costs nothing in play. (2026-09-18: "use the EmbersStorm planes as UI - a 3D plane on the title screen")
using UnityEngine;

namespace SkySquad
{
    public class HangarShowcase : MonoBehaviour
    {
        public Transform model;         // the pivot the aircraft hangs under, centred on the aircraft's bounds
        public float turnSpeed = 16f;   // degrees per second around the vertical
        public float bank = 5f;         // a gentle roll as it turns, like a banking pass
        public float pitch = 3f;
        public float bob = 0.1f;
        public float startAngle = 35f;  // three-quarter view at the first frame, not a side-on silhouette

        float angle;

        void OnEnable() { angle = startAngle; }

        void Update()
        {
            if (model == null) return;
            float t = Time.unscaledTime, dt = Time.unscaledDeltaTime;   // unscaled: the lobby may sit under timeScale 0
            angle += turnSpeed * dt;
            model.localRotation = Quaternion.Euler(Mathf.Sin(t * 0.9f) * pitch, angle, Mathf.Sin(t * 0.7f) * bank);
            model.localPosition = new Vector3(0f, Mathf.Sin(t * 1.3f) * bob, 0f);
        }
    }
}
