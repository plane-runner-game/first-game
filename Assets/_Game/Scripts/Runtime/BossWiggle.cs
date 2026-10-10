// BossWiggle.cs
// The alien world's living bosses (2026-10-10, "a space dragon that flies"): parts that rock to and fro about their own Z from where they
// were built - the void dragon's wings beating about the nose axis, the space kraken's tentacles swinging one after another.
using UnityEngine;

namespace SkySquad
{
    public class BossWiggle : MonoBehaviour
    {
        public Transform[] parts;
        public float[] amplitude;   // degrees each way, per part (the sign sets which way it starts)
        public float[] phase;       // radians, per part
        public float speed = 3f;    // radians a second

        Quaternion[] rest;

        void Awake()
        {
            rest = new Quaternion[parts.Length];
            for (int i = 0; i < parts.Length; i++) rest[i] = parts[i] != null ? parts[i].localRotation : Quaternion.identity;
        }

        void Update()
        {
            float t = Time.time * speed;
            for (int i = 0; i < parts.Length; i++)
                if (parts[i] != null) parts[i].localRotation = rest[i] * Quaternion.Euler(0f, 0f, Mathf.Sin(t + phase[i]) * amplitude[i]);
        }
    }
}
