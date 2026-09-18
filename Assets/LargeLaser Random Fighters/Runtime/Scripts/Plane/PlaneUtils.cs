using System.Collections;
using System.Collections.Generic;
using UnityEngine;

namespace LargeLaser
{
    public class PlaneUtils
    {
        public enum WingState
        {
            Sweep,
            Delay
        }

        public static void RotatePropeller(Plane plane, ref float angle)
        {
            angle += 500f * Time.deltaTime;
            plane.SetPropAngle(angle);
        }

        public static void UpdateFlaps(Plane plane, ref float angle)
        {
            angle += 2f * Time.deltaTime;
            float flapAngle = Mathf.Sin(angle) * 45f;
            plane.SetFlapAngle(flapAngle);
        }

        public static void InitWingSweep(ref WingState wingState, ref float time, ref float direction)
        {
            time = 1;
            direction = 1;
            wingState = WingState.Sweep;
        }

        public static void UpdateWingSweep(Plane plane, ref WingState wingState, ref float time, ref float direction)
        {
            if (wingState == WingState.Delay)
            {
                time -= Time.deltaTime;

                if (time <= 0)
                {
                    wingState = WingState.Sweep;

                    time = 1;
                }
            }
            else if (wingState == WingState.Sweep)
            {
                time = Mathf.Max(0, time - Time.deltaTime);

                float perc = time / 1f;
                perc = Mathf.SmoothStep(0f, 1f, perc);

                if (direction > 0)
                {
                    perc = 1f - perc;
                }

                float angle = perc * 30;
                plane.SetWingAngle(angle);

                if (time == 0)
                {
                    direction *= -1;

                    wingState = WingState.Delay;

                    time = 1f;
                }
            }
        }

        public static Transform Get(Transform parent, string name)
        {
            foreach(Transform c in parent)
            {
                if(c.name == name)
                {
                    return c;
                }

                var t = Get(c, name);
                if(t != null)
                {
                    return t;
                }
            }

            return null;
        }
    }
}