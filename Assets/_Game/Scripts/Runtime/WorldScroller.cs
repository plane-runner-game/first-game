// WorldScroller.cs
// The illusion of flying forward: the water texture slides toward the camera, the lane
// buoys and clouds drift past and get recycled ahead of the squad.
using System.Collections.Generic;
using UnityEngine;

namespace SkySquad
{
    public class WorldScroller : MonoBehaviour
    {
        public Renderer water;
        public float waterTilesPerUnit = 0.1f;
        public List<Transform> buoys = new List<Transform>();
        public List<Transform> clouds = new List<Transform>();
        public float recycleBehind = -20f;
        public float recycleAhead = 200f;

        Material waterMat;
        float offset;
        static readonly int BaseMap = Shader.PropertyToID("_BaseMap");
        static readonly int SeaScroll = Shader.PropertyToID("_SeaScroll");   // the Sea shader (2026-09-18): units travelled, global so the near grid and the far plane agree

        void Start() { if (water != null) waterMat = water.material; }

        void Update()
        {
            var gm = GameManager.I;
            float speed = gm == null ? 10f : gm.State == GameState.Playing ? gm.ScrollSpeed : (gm.State == GameState.Paused || gm.State == GameState.Title) ? 0f : gm.config.scrollSpeed * 0.6f;   // Title: the armed level waits still (2026-09-19); the sea itself still moves (its waves run on time)
            float dt = Time.deltaTime;
            offset += speed * dt * waterTilesPerUnit;
            if (waterMat != null) waterMat.SetTextureOffset(BaseMap, new Vector2(0f, -offset));   // the old flat sea scrolled its tile texture
            Shader.SetGlobalFloat(SeaScroll, offset / Mathf.Max(0.0001f, waterTilesPerUnit));   // the wave field slides toward the camera with the buoys
            float appearZ = gm != null ? gm.config.appearZ : 100f, appearRange = gm != null ? gm.config.appearRange : 12f;
            foreach (var b in buoys)
            {
                if (b == null) continue;
                var p = b.position; p.z -= speed * dt;
                if (p.z < recycleBehind) p.z += recycleAhead - recycleBehind;
                b.position = p;
                b.localScale = Vector3.one * Breakable.Appear(p.z, appearZ, appearRange);   // a buoy comes out of the same line as the crates and the planes: nothing past it ("the orange things on the right and left too", 2026-09-20)
            }
            foreach (var c in clouds)
            {
                if (c == null) continue;
                var p = c.position; p.z -= speed * 0.35f * dt;
                if (p.z < 20f) p.z += 200f;
                c.position = p;
            }
        }
    }
}
