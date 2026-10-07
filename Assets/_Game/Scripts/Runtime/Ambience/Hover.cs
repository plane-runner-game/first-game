// Hover.cs
// Something that floats: the lifted lid of the gift box, a balloon, a lantern on a string. Bobs and sways gently (2026-10-08).
using UnityEngine;

namespace SkySquad
{
    public class Hover : MonoBehaviour
    {
        public float height = 0.6f, speed = 0.5f, sway = 2f;
        Vector3 p0; Quaternion r0; float seed;

        void Start() { p0 = transform.localPosition; r0 = transform.localRotation; seed = Random.value * 10f; }

        void Update()
        {
            float t = (Time.time + seed) * speed * 2f * Mathf.PI;
            transform.localPosition = p0 + Vector3.up * Mathf.Sin(t) * height;
            transform.localRotation = r0 * Quaternion.Euler(Mathf.Sin(t * 0.7f) * sway, 0f, Mathf.Cos(t * 0.6f) * sway);
        }
    }
}
