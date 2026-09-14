// CameraFollow.cs
// Sits on the camera rig. Keeps the squad framed: the rig slides a fraction of the way
// toward the squad's x and altitude (soft follow) and adds the screen-shake offset from FXManager.
using UnityEngine;

namespace SkySquad
{
    public class CameraFollow : MonoBehaviour
    {
        public SquadController squad;
        public Vector3 basePosition = new Vector3(0f, 6.2f, -9.5f);
        public float followX = 0.55f;
        public float followAlt = 0.25f;
        public float smoothing = 6f;

        Vector3 follow;

        void LateUpdate()
        {
            if (squad != null)
            {
                Vector3 target = new Vector3(squad.X * followX, squad.Alt * followAlt, 0f);
                follow = Vector3.Lerp(follow, target, 1f - Mathf.Exp(-smoothing * Time.deltaTime));
            }
            Vector3 shake = FXManager.I != null ? FXManager.I.ShakeOffset : Vector3.zero;
            transform.position = basePosition + follow + shake;
        }
    }
}
