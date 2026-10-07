// Roller.cs
// A tumbleweed (2026-10-08, the Wild West): it bowls across the street from one side to the other, hopping and rolling, rests out of sight for
// a while, then comes back the other way.
using UnityEngine;

namespace SkySquad
{
    public class Roller : MonoBehaviour
    {
        public float xFrom = -26f, xTo = 26f, speed = 7f, radius = 0.9f, hop = 0.8f;
        public float restMin = 3f, restMax = 9f;
        public Transform visual;
        float x, dir = 1f, rest, ground, hopT;

        void Start() { ground = transform.position.y; x = xFrom; rest = Random.Range(0f, restMax); if (visual == null) visual = transform; }

        void Update()
        {
            float dt = Time.deltaTime;
            if (rest > 0f) { rest -= dt; return; }
            x += dir * speed * dt;
            hopT += dt * 2.3f;
            var p = transform.position;
            p.x = x; p.y = ground + Mathf.Abs(Mathf.Sin(hopT)) * hop;
            transform.position = p;
            visual.Rotate(Vector3.forward, -dir * speed * dt / Mathf.Max(0.1f, radius) * Mathf.Rad2Deg, Space.World);
            if ((dir > 0f && x > xTo) || (dir < 0f && x < xFrom))
            {   // over the far side: rest, and come back the other way
                dir = -dir; x = Mathf.Clamp(x, xFrom, xTo); rest = Random.Range(restMin, restMax);
            }
        }
    }
}
