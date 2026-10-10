// Billboard.cs
// Keeps a flat sprite turned to the camera whatever its parent does (the weapon crate's ammo icon, which
// rides a showcase that tilts and rolls, then a flight that turns along its path). It sways a little and
// every few seconds spins once round its upright, so it reads as a pickup rather than a sticker.
using UnityEngine;

namespace SkySquad
{
    public class Billboard : MonoBehaviour
    {
        public float sway = 8f;          // degrees of side-to-side tilt
        public float spinEvery = 3.6f;   // seconds between spins; 0 = never
        float seed;
        Camera cam;

        void Awake() { seed = Random.value * 10f; }

        void LateUpdate()
        {
            if (cam == null) { cam = Camera.main; if (cam == null) return; }
            float t = Time.time + seed;
            float spin = 0f;
            if (spinEvery > 0f)
            {
                float r = Mathf.Clamp01(((t % spinEvery) - (spinEvery - 0.6f)) / 0.6f);
                spin = r * r * (3f - 2f * r) * 360f;
            }
            transform.rotation = cam.transform.rotation * Quaternion.Euler(0f, spin, Mathf.Sin(t * 1.6f) * sway);
        }
    }
}
