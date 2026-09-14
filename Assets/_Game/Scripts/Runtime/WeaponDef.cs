// WeaponDef.cs - one weapon type (gatling / rockets / laser). Tunable in the Inspector.
using UnityEngine;

namespace SkySquad
{
    public enum ProjectileKind { Tracer, Rocket, Beam }

    [CreateAssetMenu(menuName = "Sky Squad/Weapon")]
    public class WeaponDef : ScriptableObject
    {
        public string id = "gatling";
        public string displayName = "GATLING";
        public string description = "single target, fast";
        public float dpsMultiplier = 1f;
        public float fireInterval = 0.09f;
        public ProjectileKind projectile = ProjectileKind.Tracer;
        public Color color = new Color(1f, 0.89f, 0.48f);
        public GameObject planePrefab;      // what the squadron looks like with this weapon
        public float splashRadius = 0f;     // rockets: hit nearby hordes too (world units)
        public bool pierce = false;         // laser: hit everything in the line of fire
    }
}
