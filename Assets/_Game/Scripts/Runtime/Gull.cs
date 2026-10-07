// Gull.cs
// A seagull over the sea world (2026-10-07, "the first level's details"): circles its flock's centre, flapping in bursts and gliding
// between them, banked into the turn. The flock root rides WorldScroller like a buoy, so the circle drifts past with the sea.
using UnityEngine;

namespace SkySquad
{
    public class Gull : MonoBehaviour
    {
        public Transform wingL, wingR;
        public float radius = 6f, height = 0f;   // the circle round the flock root, and this gull's height on it
        public float speed = 4f;                  // units per second along the circle (negative turns the other way)
        public float phase;

        float angle, flapT;

        void Start() { angle = phase; flapT = phase * 3.1f; }

        void Update()
        {
            float dt = Time.deltaTime;
            angle += speed / Mathf.Max(0.5f, radius) * dt;
            float dir = Mathf.Sign(speed);
            var p = new Vector3(Mathf.Cos(angle) * radius, height + Mathf.Sin(angle * 2.3f + phase) * 0.6f, Mathf.Sin(angle) * radius);
            transform.localPosition = p;
            var tangent = new Vector3(-Mathf.Sin(angle), 0f, Mathf.Cos(angle)) * dir;
            transform.localRotation = Quaternion.LookRotation(tangent, Vector3.up) * Quaternion.Euler(0f, 0f, -dir * 22f);   // banked into the turn
            // flap for ~1.6 s, glide for ~2 s, wings held a little up while gliding
            flapT += dt;
            float cycle = flapT % 3.6f;
            float a = cycle < 1.6f ? Mathf.Sin(cycle * 14f) * 32f : 8f;
            if (wingR != null) wingR.localRotation = Quaternion.Euler(0f, 0f, a);
            if (wingL != null) wingL.localRotation = Quaternion.Euler(0f, 0f, -a);
        }
    }
}
