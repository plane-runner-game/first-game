// EnemyKindDef.cs - one enemy plane type (fighter / mini boss). Tunable in the Inspector.
using UnityEngine;

namespace SkySquad
{
    [CreateAssetMenu(menuName = "Sky Squad/Enemy Kind")]
    public class EnemyKindDef : ScriptableObject
    {
        public string id = "fighter";
        public string displayName = "FIGHTER";
        public float hp = 1f;                 // mini bosses get theirs from the wave formula instead
        public float halfWidth = 0.7f;        // for the line-of-fire overlap test
        public float approachSpeed = 6.5f;    // extra closing speed on top of world scroll
        public float fireEvery = 1.5f;        // seconds between shots once parked
        public float shotDamage = 0.15f;      // planes per shot; fractions add up until one falls
        public int coins = 10;
        public float scale = 1f;
        public bool miniBoss = false;         // wide: blocks every column behind it, shows its hp
        public GameObject prefab;
        public Color color = new Color(1f, 0.23f, 0.31f);
    }
}
