// SquadInput.cs
// Reads the finger / mouse / keyboard every frame and exposes simple values:
// DragDelta (how far the finger moved this frame, as a fraction of screen height),
// KeyAxis (-1..1 on each axis from arrows/WASD) and Tapped (press + release without moving).
using UnityEngine;
using UnityEngine.InputSystem;

namespace SkySquad
{
    public class SquadInput : MonoBehaviour
    {
        public Vector2 DragDelta { get; private set; }
        public Vector2 KeyAxis { get; private set; }
        public bool Tapped { get; private set; }
        public bool Pressed { get; private set; }
        public bool Swiping => down && moved;   // the finger is down and has moved past the tap threshold: the lobby starts the attempt on this (2026-09-19)

        bool down, moved;
        Vector2 last, start;

        void Update()
        {
            DragDelta = Vector2.zero;
            Tapped = false;

            bool pressed = false;
            Vector2 pos = Vector2.zero;
            var ms = Mouse.current;
            foreach (var dev in InputSystem.devices)   // any touchscreen, not only the "current" one: Unity Remote's phone screen counts too
                if (dev is Touchscreen ts && ts.primaryTouch.press.isPressed) { pressed = true; pos = ts.primaryTouch.position.ReadValue(); break; }
            if (!pressed && ms != null && ms.leftButton.isPressed) { pressed = true; pos = ms.position.ReadValue(); }
            Pressed = pressed;

            if (pressed)
            {
                if (!down) { down = true; last = start = pos; moved = false; }
                else
                {
                    Vector2 d = pos - last;
                    last = pos;
                    DragDelta = d / Mathf.Max(1f, Screen.height);
                    if ((pos - start).magnitude > 12f) moved = true;
                }
            }
            else if (down)
            {
                down = false;
                if (!moved) Tapped = true;
            }

            float kx = 0f, ky = 0f;
            var kb = Keyboard.current;
            if (kb != null)
            {
                if (kb.leftArrowKey.isPressed || kb.aKey.isPressed) kx -= 1f;
                if (kb.rightArrowKey.isPressed || kb.dKey.isPressed) kx += 1f;
                if (kb.upArrowKey.isPressed || kb.wKey.isPressed) ky += 1f;
                if (kb.downArrowKey.isPressed || kb.sKey.isPressed) ky -= 1f;
                if (kb.spaceKey.wasPressedThisFrame || kb.enterKey.wasPressedThisFrame) Tapped = true;
            }
            KeyAxis = new Vector2(kx, ky);
        }
    }
}
