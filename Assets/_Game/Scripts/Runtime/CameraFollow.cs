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
        public Vector3 basePosition = new Vector3(0f, 7.48f, -11f);   // the rig at altitude 0; at the ceiling it is base + followAlt * altitudeMax = (0, 8.65, -11)
        public float followX = 0.55f;
        public float followAlt = 0.2f;    // 0.2 (was 0.7): the camera stays up on the swarm when the squad dives for crates, dropping only 1.2 on a full dive ("the camera stays up on the enemy planes like before the dive", 2026-09-18)
        public float smoothing = 6f;
        [Header("Dive framing (blend by squad altitude: ceiling -> 0)")]
        public float pitchHigh = 13.5f;   // camera pitch in degrees with the squad at the ceiling: squad at 58% of the screen, horizon 75%
        public float pitchLow = 13.5f;    // ...and at altitude 0 (same: the view does not tilt on the dive; 8.9 with dollyLow 4 was the "zoom out on the dive" tried and dropped the same day)
        public float dollyLow = 0f;       // extra distance behind basePosition at altitude 0 (0: the camera holds its place, only the squad moves down the screen)

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
