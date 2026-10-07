// Blink.cs
// Lamps that take turns: a traffic light's three, a beacon on a roof, the bulbs on a string. One of `lamps` is on at a time, each for its own
// share of the cycle, with an optional dark beat at the end (2026-10-08, the land worlds' ambience).
using UnityEngine;

namespace SkySquad
{
    public class Blink : MonoBehaviour
    {
        public GameObject[] lamps;
        public float[] seconds = { 1f };     // how long each lamp stays on (the last value repeats)
        public float phase;
        public float darkSeconds;            // all off for this long after the last lamp (a beacon's off time)

        void Update()
        {
            if (lamps == null || lamps.Length == 0) return;
            float total = darkSeconds; for (int i = 0; i < lamps.Length; i++) total += Dur(i);
            float t = (Time.time + phase) % Mathf.Max(0.01f, total), acc = 0f; int on = -1;
            for (int i = 0; i < lamps.Length; i++) { acc += Dur(i); if (t < acc) { on = i; break; } }
            for (int i = 0; i < lamps.Length; i++) if (lamps[i] != null && lamps[i].activeSelf != (i == on)) lamps[i].SetActive(i == on);
        }

        float Dur(int i) { return seconds == null || seconds.Length == 0 ? 1f : seconds[Mathf.Min(i, seconds.Length - 1)]; }
    }
}
