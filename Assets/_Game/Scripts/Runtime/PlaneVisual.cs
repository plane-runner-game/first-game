// PlaneVisual.cs
// Cosmetic behaviour of one plane model: gentle bob, spinning propeller, muzzle flash,
// and swapping the body material to gold for the leader.
using UnityEngine;

namespace SkySquad
{
    public class PlaneVisual : MonoBehaviour
    {
        public int index;
        public Transform propeller;
        public Transform[] propellers;                     // imported models (Asset Store packs) can have several: the C-130 has four
        public Vector3 propellerAxis = Vector3.forward;   // local spin axis of the imported propellers (the procedural prop spins on Z)
        public Renderer bodyRenderer;
        public Renderer flashRenderer;     // small glowing quad at the nose, enabled briefly when firing
        [HideInInspector] public Material leaderMaterial;

        Material originalBody;
        Vector3 basePos, baseScale;
        float flashT, popT = -1f, popDelay;
        bool isLeader, scaleKnown;

        /// <summary>The squad changed plane (2026-09-27, "make the planes on the crates nicer, with animation - something professional"):
        /// this one pops in after 'delay' - from nothing, a little past full size, back - with a sparkle, so the change runs through
        /// the squad as a wave front to back instead of every plane swapping in the same frame.</summary>
        public void Pop(float delay)
        {
            if (!scaleKnown) { baseScale = transform.localScale; scaleKnown = true; }
            popDelay = delay; popT = 0f;
            transform.localScale = Vector3.zero;
        }

        public void SetBase(Vector3 localPos)
        {
            basePos = localPos;
            transform.localPosition = localPos;
        }

        void Update()
        {
            float phase = index * 1.3f;
            transform.localPosition = basePos + Vector3.up * (Mathf.Sin(Time.time * 8f + phase) * 0.05f);
            if (popT >= 0f)
            {
                popT += Time.deltaTime;
                float k = Mathf.Clamp01((popT - popDelay) / 0.35f);
                if (k > 0f && popT - Time.deltaTime - popDelay <= 0f && index % 2 == 0 && FXManager.I != null && FXManager.I.joinPrefab != null)
                    FXManager.I.Burst(FXManager.I.joinPrefab, transform.position, 0.45f, 1f);   // every other plane sparkles as it pops: all of them would be a white-out
                float s = k <= 0f ? 0f : 1f + Mathf.Sin(k * Mathf.PI) * 0.25f * (1f - k) + (1f - Mathf.Pow(1f - k, 3f)) - 1f;   // eases up to full size with a little overshoot
                transform.localScale = baseScale * s;
                if (k >= 1f) { popT = -1f; transform.localScale = baseScale; }
            }
            if (propeller != null) propeller.Rotate(0f, 0f, 2400f * Time.deltaTime, Space.Self);
            if (propellers != null) { float a = 2400f * Time.deltaTime; for (int i = 0; i < propellers.Length; i++) if (propellers[i] != null) propellers[i].Rotate(propellerAxis * a, Space.Self); }
            if (flashT > 0f)
            {
                flashT -= Time.deltaTime;
                if (flashT <= 0f && flashRenderer != null) flashRenderer.enabled = false;
            }
        }

        public void Flash(Color c)
        {
            if (flashRenderer == null) return;
            flashRenderer.enabled = true;
            flashRenderer.material.color = c;
            flashT = 0.06f;
        }

        public void SetLeader(bool on)
        {
            if (bodyRenderer == null || leaderMaterial == null || on == isLeader) return;
            isLeader = on;
            var mats = bodyRenderer.sharedMaterials;
            if (mats.Length == 0) return;
            if (originalBody == null) originalBody = mats[0];
            mats[0] = on ? leaderMaterial : originalBody;
            bodyRenderer.sharedMaterials = mats;
        }
    }
}
