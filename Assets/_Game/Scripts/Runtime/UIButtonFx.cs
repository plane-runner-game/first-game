// UIButtonFx.cs
// The feel of a UI button (2026-09-18, the UI kit): a press squashes the button a touch and darkens its face; release springs
// it back. Runs on unscaled time so it works while paused. (The first kit's shelf drop and idle pulse are still supported
// through face / pressDepth / pulse but unused since the "tactical glass" pass.)
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;

namespace SkySquad
{
    public class UIButtonFx : MonoBehaviour, IPointerDownHandler, IPointerUpHandler, IPointerExitHandler
    {
        public RectTransform face;        // a plate that drops by pressDepth on press (null = none)
        public float faceUp = 0f;         // its resting y
        public float pressDepth = 0f;
        public Image tint;                // the graphic that darkens on press (null = none)
        public Color pressedColor = new Color(0.12f, 0.15f, 0.2f, 0.95f);
        public bool pulse;                // idle breathing
        public float pulseAmount = 0.035f;
        public float pulseSpeed = 3.2f;

        bool down;
        float press;                      // 0 = up, 1 = fully pressed (eased)
        Color baseColor; bool haveBase;

        public void OnPointerDown(PointerEventData e) { down = true; }
        public void OnPointerUp(PointerEventData e) { down = false; }
        public void OnPointerExit(PointerEventData e) { down = false; }

        void OnEnable() { if (tint != null && !haveBase) { baseColor = tint.color; haveBase = true; } }
        void OnDisable() { down = false; press = 0f; Apply(); }

        void Update()
        {
            float dt = Time.unscaledDeltaTime;
            press = Mathf.Lerp(press, down ? 1f : 0f, 1f - Mathf.Exp(-(down ? 30f : 14f) * dt));   // snaps down, springs up a little slower
            Apply();
        }

        void Apply()
        {
            if (face != null) face.anchoredPosition = new Vector2(face.anchoredPosition.x, faceUp - pressDepth * press);
            if (tint != null && haveBase) tint.color = Color.Lerp(baseColor, pressedColor, press);
            float s = 1f - 0.04f * press;
            if (pulse) s *= 1f + Mathf.Sin(Time.unscaledTime * pulseSpeed) * pulseAmount;
            transform.localScale = new Vector3(s, s, 1f);
        }
    }
}
