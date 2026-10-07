// ShuttleLaunch.cs
// The space launch world's show (2026-10-08): the shuttle on its pad vents steam while it waits; `launchAt` seconds into an attempt the engines
// light and the whole stack climbs away into the sky, flame and smoke under it. It is back on the pad for the next attempt.
using UnityEngine;

namespace SkySquad
{
    public class ShuttleLaunch : MonoBehaviour
    {
        public Transform stack;               // what flies: the shuttle, its tank and boosters
        public GameObject flame;              // on from ignition (a child of the stack, so it rides up with it)
        public ParticleSystem smoke;          // the cloud left on the pad
        public ParticleSystem steam;          // the venting while it waits
        public float launchAt = 24f, climbAccel = 3.5f, holdDown = 1.6f;
        Vector3 rest; bool lit; float t, vel;

        void Start() { if (stack != null) rest = stack.localPosition; ResetStack(); }

        void ResetStack()
        {
            lit = false; t = 0f; vel = 0f;
            if (stack != null) stack.localPosition = rest;
            if (flame != null) flame.SetActive(false);
            if (smoke != null) { smoke.Stop(true, ParticleSystemStopBehavior.StopEmittingAndClear); var em = smoke.emission; em.enabled = true; }
            if (steam != null && !steam.isPlaying) steam.Play();
        }

        void Update()
        {
            var gm = GameManager.I;
            if (gm == null || stack == null) return;
            bool running = gm.State == GameState.Playing || gm.State == GameState.Paused;
            if (!running || gm.LevelTime < launchAt * 0.5f) { if (lit) ResetStack(); return; }
            if (gm.State == GameState.Paused) return;
            if (!lit && gm.LevelTime >= launchAt)
            {
                lit = true; t = 0f;
                if (flame != null) flame.SetActive(true);
                if (smoke != null) smoke.Play();
                if (steam != null) steam.Stop();
                if (FXManager.I != null) FXManager.I.Shake(0.25f);
            }
            if (!lit) return;
            t += Time.deltaTime;
            if (t < holdDown) return;                       // the engines roar on the pad first
            vel += climbAccel * Time.deltaTime;
            stack.localPosition += Vector3.up * vel * Time.deltaTime;
            if (smoke != null && t > holdDown + 4f) { var em = smoke.emission; em.enabled = false; }
        }
    }
}
