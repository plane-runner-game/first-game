// Cruise.cs
// Something of the scenery that travels on its own as well as scrolling with the world: the Wild West's train running down its line toward
// the squad (2026-10-08). WorldScroller loops it like any other prop.
using UnityEngine;

namespace SkySquad
{
    public class Cruise : MonoBehaviour
    {
        public Vector3 velocity = new Vector3(0f, 0f, -7f);

        void Update()
        {
            var gm = GameManager.I;
            if (gm != null && gm.State == GameState.Paused) return;
            transform.position += velocity * Time.deltaTime;
        }
    }
}
