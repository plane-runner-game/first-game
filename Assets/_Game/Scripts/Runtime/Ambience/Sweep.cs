// Sweep.cs
// A searchlight on a rooftop: swings to and fro about its local Y and nods about X (2026-10-08, downtown's gate).
using UnityEngine;

namespace SkySquad
{
    public class Sweep : MonoBehaviour
    {
        public float yawAmplitude = 35f, yawSpeed = 0.12f;
        public float pitchAmplitude = 8f, pitchSpeed = 0.09f;
        public float phase;
        Quaternion rest;

        void Start() { rest = transform.localRotation; }

        void Update()
        {
            float t = Time.time + phase;
            transform.localRotation = rest * Quaternion.Euler(Mathf.Sin(t * pitchSpeed * 2f * Mathf.PI) * pitchAmplitude, Mathf.Sin(t * yawSpeed * 2f * Mathf.PI) * yawAmplitude, 0f);
        }
    }
}
