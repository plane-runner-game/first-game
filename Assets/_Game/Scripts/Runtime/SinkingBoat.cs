// SinkingBoat.cs
// The boat a broken crate rode on. Breakable.Break detaches it from the crate (which explodes and is destroyed) and adds
// this: the boat drifts back with the sea like the buoys, lifts its bow, lists to one side and slides under, then is
// destroyed (requested 2026-09-18: "I want the boat to sink after the crate is destroyed").
using UnityEngine;

namespace SkySquad
{
    public class SinkingBoat : MonoBehaviour
    {
        const float Duration = 2.4f;   // seconds from the break to fully under

        float t, roll;
        Vector3 start;
        Quaternion startRot;

        void Start()
        {
            start = transform.position;
            startRot = transform.rotation;
            roll = Random.value < 0.5f ? -1f : 1f;
            if (FXManager.I != null) FXManager.I.Ring(new Vector3(start.x, 0.05f, start.z), new Color(0.85f, 0.95f, 1f), 5f);   // a ripple on the water
        }

        void Update()
        {
            var gm = GameManager.I;
            if (gm != null && gm.State != GameState.Playing) { Destroy(gameObject); return; }
            float dt = Time.deltaTime;
            t += dt;
            float u = Mathf.Clamp01(t / Duration);
            start.z -= (gm != null ? gm.ScrollSpeed : 9f) * dt;   // on the water now: it drifts back with the sea
            float sink = u * u * 4.2f;                            // slowly at first, then it goes
            transform.position = new Vector3(start.x, start.y - sink, start.z);
            transform.rotation = startRot * Quaternion.Euler(-Mathf.SmoothStep(0f, 55f, u), 0f, roll * Mathf.SmoothStep(0f, 18f, u));   // bow up, listing
            if (t >= Duration || transform.position.z < -8f) Destroy(gameObject);
        }
    }
}
