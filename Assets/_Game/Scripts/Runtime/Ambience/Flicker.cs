// Flicker.cs
// A torch, a bonfire, a lantern: its light breathes on Perlin noise, and its flame mesh (optional) swells with it (2026-10-08).
using UnityEngine;

namespace SkySquad
{
    public class Flicker : MonoBehaviour
    {
        public Light target;
        public float baseIntensity = 2f, amount = 0.6f, speed = 6f;
        public Transform flame;
        float seed; Vector3 flameScale;

        void Start()
        {
            seed = Random.value * 100f;
            if (target == null) target = GetComponent<Light>();
            if (flame != null) flameScale = flame.localScale;
        }

        void Update()
        {
            float n = Mathf.PerlinNoise(seed, Time.time * speed) * 2f - 1f;
            if (target != null) target.intensity = baseIntensity * (1f + n * amount);
            if (flame != null) flame.localScale = new Vector3(flameScale.x * (1f + n * 0.12f), flameScale.y * (1f + n * 0.25f), flameScale.z * (1f + n * 0.12f));
        }
    }
}
