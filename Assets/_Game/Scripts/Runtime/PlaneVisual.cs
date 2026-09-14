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
        public Renderer bodyRenderer;
        public Renderer flashRenderer;     // small glowing quad at the nose, enabled briefly when firing
        [HideInInspector] public Material leaderMaterial;

        Material originalBody;
        Vector3 basePos;
        float flashT;
        bool isLeader;

        public void SetBase(Vector3 localPos)
        {
            basePos = localPos;
            transform.localPosition = localPos;
        }

        void Update()
        {
            float phase = index * 1.3f;
            transform.localPosition = basePos + Vector3.up * (Mathf.Sin(Time.time * 8f + phase) * 0.05f);
            if (propeller != null) propeller.Rotate(0f, 0f, 2400f * Time.deltaTime, Space.Self);
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
