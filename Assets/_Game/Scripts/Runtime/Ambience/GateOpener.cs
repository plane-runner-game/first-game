// GateOpener.cs
// The door of a land world's gate (2026-10-08): shut while the squad waits in the lobby, it swings or slides open as the attempt starts, so the
// first planes come out of a door that has just opened. Each part moves from its closed pose (as built) by `openOffset` / `openEuler`.
using UnityEngine;

namespace SkySquad
{
    public class GateOpener : MonoBehaviour
    {
        public Transform[] parts;
        public Vector3[] openOffset;          // local position added when open
        public Vector3[] openEuler;           // local rotation added when open
        public float seconds = 1.2f;
        Vector3[] p0; Quaternion[] r0; float k;

        void Start()
        {
            if (parts == null) return;
            p0 = new Vector3[parts.Length]; r0 = new Quaternion[parts.Length];
            for (int i = 0; i < parts.Length; i++) if (parts[i] != null) { p0[i] = parts[i].localPosition; r0[i] = parts[i].localRotation; }
        }

        void Update()
        {
            if (parts == null || p0 == null) return;
            var gm = GameManager.I;
            bool open = gm == null || gm.State != GameState.Title;
            k = Mathf.MoveTowards(k, open ? 1f : 0f, Time.deltaTime / Mathf.Max(0.05f, seconds));
            float e = k * k * (3f - 2f * k);
            for (int i = 0; i < parts.Length; i++)
            {
                if (parts[i] == null) continue;
                Vector3 off = openOffset != null && i < openOffset.Length ? openOffset[i] : Vector3.zero;
                Vector3 eul = openEuler != null && i < openEuler.Length ? openEuler[i] : Vector3.zero;
                parts[i].localPosition = p0[i] + off * e;
                parts[i].localRotation = r0[i] * Quaternion.Euler(eul * e);
            }
        }
    }
}
