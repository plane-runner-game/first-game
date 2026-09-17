// CameraFollow.cs
// Sits on the camera rig. Keeps the squad framed: the rig slides a fraction of the way
// toward the squad's x and altitude (soft follow) and adds the screen-shake offset from FXManager.
// Dive framing (2026-09-18): the rig also pulls back and the camera looks flatter as the squad drops
// from the ceiling to altitude 0, so the swarm above stays in the frame while you shoot the crates
// (before, the camera sank with the squad and the fighters ended up at 78-86% of the screen, under the
// HUD and lost in the horizon haze: "the camera goes down so far with me that the planes above no longer show").
using UnityEngine;

namespace SkySquad
{
    public class CameraFollow : MonoBehaviour
    {
        public SquadController squad;
        public Vector3 basePosition = new Vector3(0f, 4.55f, -11f);
        public float followX = 0.55f;
        public float followAlt = 0.7f;
        public float smoothing = 6f;
        [Header("Dive framing (blend by squad altitude: ceiling -> 0)")]
        public float pitchHigh = 13.5f;   // camera pitch in degrees with the squad at the ceiling: squad at 58% of the screen, horizon 75%
        public float pitchLow = 8.9f;     // ...and at altitude 0: squad still at 42%, horizon 66%, the swarm at 65-75% instead of 78-86%
        public float dollyLow = 4f;       // the rig sits this much further back at altitude 0 (z -15 instead of -11), nothing extra at the ceiling

        Vector3 follow;
        float low;          // 0 at the ceiling .. 1 at altitude 0, smoothed
        Transform cam;

        void Awake()
        {
            var c = GetComponentInChildren<Camera>();
            if (c != null) cam = c.transform;
        }

        void LateUpdate()
        {
            if (squad != null)
            {
                float altMax = squad.config != null ? squad.config.altitudeMax : 5.85f;
                float u = altMax > 0f ? Mathf.Clamp01(squad.Alt / altMax) : 1f;   // 1 at the ceiling, 0 at altitude 0
                Vector3 target = new Vector3(squad.X * followX, squad.Alt * followAlt, -(1f - u) * dollyLow);
                float k = 1f - Mathf.Exp(-smoothing * Time.deltaTime);
                follow = Vector3.Lerp(follow, target, k);
                low = Mathf.Lerp(low, 1f - u, k);
            }
            Vector3 shake = FXManager.I != null ? FXManager.I.ShakeOffset : Vector3.zero;
            transform.position = basePosition + follow + shake;
            if (cam != null) cam.localRotation = Quaternion.Euler(Mathf.Lerp(pitchHigh, pitchLow, low), 0f, 0f);
        }
    }
}
