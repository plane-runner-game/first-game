// CameraFollow.cs
// Sits on the camera rig. Keeps the squad framed: the rig follows a fraction (followX) of the squad's x (the squad itself
// is stopped before a plane leaves the screen, SquadController.XLimit) and a fraction of its altitude, and adds the screen-shake
// offset from FXManager. The vertical field of view is derived from a fixed horizontal one, so the visible
// width at the squad is the same on every phone aspect.
// pitchLow / dollyLow blend a flatter pitch and a rig further back at altitude 0 (both neutral since
// 2026-09-18: the user wants the camera to hold its place on the swarm while the squad dives).
using UnityEngine;

namespace SkySquad
{
    public class CameraFollow : MonoBehaviour
    {
        public SquadController squad;
        public Vector3 basePosition = new Vector3(0f, 7.48f, -11f);   // the rig at altitude 0; at the ceiling it is base + followAlt * altitudeMax = (0, 8.65, -11)
        public float followX = 0.55f;     // the rig slides this fraction of the squad's X (1 = centred was tried 2026-09-18 and rejected: "the camera as it was, it must not move with me"; instead SquadController.XLimit stops the squad before a plane leaves the screen)
        public float maxLagX = 0.5f;      // the smoothed follow trails the squad sideways by at most this much: a fast swipe cannot push the formation off the edge
        public float followAlt = 0.2f;    // 0.2 (was 0.7): the camera stays up on the swarm when the squad dives for crates, dropping only 1.2 on a full dive ("the camera stays up on the enemy planes like before the dive", 2026-09-18)
        public float smoothing = 6f;
        public float horizontalFov = 30.7f;   // degrees; the vertical FOV follows the aspect (52 at 9:16, ~61 on a 9:19.5 phone) so the formation width that fits is the same everywhere
        [Header("Dive framing (blend by squad altitude: ceiling -> 0)")]
        public float pitchHigh = 13.5f;   // camera pitch in degrees with the squad at the ceiling: squad at 51% of the screen, horizon 75%
        public float pitchLow = 13.5f;    // ...and at altitude 0 (same: the view does not tilt on the dive; 8.9 with dollyLow 4 was the "zoom out on the dive" tried and dropped the same day)
        public float dollyLow = 0f;       // extra distance behind basePosition at altitude 0 (0: the camera holds its place, only the squad moves down the screen)
        [Header("Lobby framing (2026-09-19: the menu is the level, the squad starts at the bottom)")]
        public float lobbyPitch = 24f;    // pitched further down in the lobby so the low squad sits mid-screen, above the cards; swings back to the play pitch on the first swipe
        public float lobbyBlend = 5f;     // how fast that swing is (per second)

        Vector3 follow;
        float low;          // 0 at the ceiling .. 1 at altitude 0, smoothed
        float lobby = 1f;   // 1 in the lobby framing .. 0 in play, smoothed
        Transform cam;
        Camera camComp;

        void Awake()
        {
            camComp = GetComponentInChildren<Camera>();
            if (camComp != null) cam = camComp.transform;
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
                follow.x = Mathf.Clamp(follow.x, target.x - maxLagX, target.x + maxLagX);
                low = Mathf.Lerp(low, 1f - u, k);
            }
            Vector3 shake = FXManager.I != null ? FXManager.I.ShakeOffset : Vector3.zero;
            transform.position = basePosition + follow + shake;
            var gm = GameManager.I;
            lobby = Mathf.Lerp(lobby, gm != null && gm.State == GameState.Title ? 1f : 0f, 1f - Mathf.Exp(-lobbyBlend * Time.deltaTime));
            if (cam != null) cam.localRotation = Quaternion.Euler(Mathf.Lerp(Mathf.Lerp(pitchHigh, pitchLow, low), lobbyPitch, lobby), 0f, 0f);
            if (camComp != null && horizontalFov > 0f && camComp.aspect > 0f)
                camComp.fieldOfView = Mathf.Max(52f, 2f * Mathf.Atan(Mathf.Tan(horizontalFov * 0.5f * Mathf.Deg2Rad) / camComp.aspect) * Mathf.Rad2Deg);   // never below the 9:16 value: a landscape / free-aspect Game view would otherwise zoom right onto the squad ("the game is very close, in my face", 2026-09-18)
        }
    }
}
