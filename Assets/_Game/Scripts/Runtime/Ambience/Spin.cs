// Spin.cs
// A windmill's wheel, a beacon's lamp, a fan of the scenery: turns about a local axis forever (2026-10-08, the land worlds' ambience).
using UnityEngine;

namespace SkySquad
{
    public class Spin : MonoBehaviour
    {
        public Vector3 axis = Vector3.forward;
        public float degreesPerSecond = 60f;

        void Update() { transform.Rotate(axis, degreesPerSecond * Time.deltaTime, Space.Self); }
    }
}
