// SinkingBoat.cs
// The boat a broken crate rode on. Breakable.Break detaches it from the crate (which explodes and is destroyed) and adds
// this: the boat drops straight down under the sea at once, drifting back with the water as it goes, then is destroyed
// (requested 2026-09-18: "I want the boat to sink after the crate is destroyed", then "when the small box is destroyed
// the big one falls straight down immediately" - the earlier bow-up, listing, 1-2 s sink was replaced by a plain fast drop).
using UnityEngine;

namespace SkySquad
{
    public class SinkingBoat : MonoBehaviour
    {
        const float Duration = 0.6f;   // seconds from the break to fully under

        float t;
        Vector3 start;

        void Start()
        {
            start = transform.position;
            if (FXManager.I != null) FXManager.I.Ring(new Vector3(start.x, 0.05f, start.z), new Color(0.85f, 0.95f, 1f), 6f);   // a ripple on the water
        }

        void Update()
        {
            var gm = GameManager.I;
            if (gm != null && gm.State != GameState.Playing) { Destroy(gameObject); return; }
            float dt = Time.deltaTime;
            t += dt;
            start.z -= (gm != null ? gm.ScrollSpeed : 9f) * dt;   // on the water now: it drifts back with the sea
            float sink = 4f * t + 12f * t * t;                    // straight down, fast from the first frame (about 6 units in 0.6 s)
            transform.position = new Vector3(start.x, start.y - sink, start.z);
            if (t >= Duration || transform.position.z < -8f) Destroy(gameObject);
        }
    }
}
