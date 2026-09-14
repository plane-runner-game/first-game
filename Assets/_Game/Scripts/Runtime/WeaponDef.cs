// WeaponDef.cs - one weapon type (gatling / rockets / laser). Tunable in the Inspector.
// Damage is discrete: every plane fires one bullet per volley, every bullet is worth 'damage',
// so a crate marked 15 takes exactly 15 gatling bullets.
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
        public float damage = 1f;           // per bullet (one bullet per plane per volley)
        public float fireInterval = 0.3f;   // seconds between volleys
        public ProjectileKind projectile = ProjectileKind.Tracer;
        public Color color = new Color(1f, 0.89f, 0.48f);
        public GameObject planePrefab;      // what the squadron looks like with this weapon
        public float splashRadius = 0f;     // rockets: planes near the one hit take 60% too (world units)
        public bool pierce = false;         // laser: hits everything behind the first plane in its x band
    }
}
