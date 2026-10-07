// SeaBob.cs
// Scenery afloat (2026-10-07, the sea world's ships, islets and wreck): the model rides the swell - a slow heave, roll and pitch, each on
// its own phase so no two ships rock together. Moves only the child it is given; WorldScroller carries the holder past.
using UnityEngine;

namespace SkySquad
{
    public class SeaBob : MonoBehaviour
    {
        public Transform target;                 // the visual child; its rest pose is read at Start
        public float heave = 0.12f, roll = 2.2f, pitch = 0.8f;   // units / degrees
        public float period = 5.5f;
        public float phase;

        Vector3 restPos; Quaternion restRot;

        void Start()
        {
            if (target == null) target = transform;
            restPos = target.localPosition; restRot = target.localRotation;
        }

        void Update()
        {
            float t = Time.time * Mathf.PI * 2f / period + phase;
            target.localPosition = restPos + Vector3.up * (Mathf.Sin(t) * heave);
            target.localRotation = restRot * Quaternion.Euler(Mathf.Sin(t * 0.83f + 1.1f) * pitch, 0f, Mathf.Sin(t * 0.61f) * roll);
        }
    }
}
