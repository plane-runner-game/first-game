// StopLine.cs
// The dashed red line across the sky where a boss parks and opens fire. It appears as he closes in
// on the line and flares brighter the nearer he gets, so the player sees where and when.
using UnityEngine;

namespace SkySquad
{
    public class StopLine : MonoBehaviour
    {
        public Renderer[] dashes;
        public Color color = new Color(1f, 0.25f, 0.3f);

        static MaterialPropertyBlock mpb;
        static readonly int BaseColor = Shader.PropertyToID("_BaseColor");

        void Update()
        {
            var gm = GameManager.I;
            if (gm == null || dashes == null) return;
            var boss = WaveSpawner.I != null ? WaveSpawner.I.CurrentBoss : null;
            bool show = (gm.State == GameState.Playing || gm.State == GameState.Paused) && boss != null;
            float near = 0f;
            if (show && !boss.Parked) near = Mathf.Clamp01(1f - (boss.Z - gm.config.enemyStopZ) / 14f);
            float a = show ? 0.45f + 0.12f * Mathf.Sin(Time.time * 4f) + 0.45f * near : 0f;
            if (mpb == null) mpb = new MaterialPropertyBlock();
            var c = color; c.a = Mathf.Clamp01(a);
            mpb.SetColor(BaseColor, c);
            foreach (var r in dashes) if (r != null) { r.enabled = show; r.SetPropertyBlock(mpb); }
        }
    }
}
