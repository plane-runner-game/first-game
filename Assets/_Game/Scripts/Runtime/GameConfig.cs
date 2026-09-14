// GameConfig.cs - every tunable number in one asset (world scale, pacing, enemy stream, crates, boss).
using UnityEngine;

namespace SkySquad
{
    [CreateAssetMenu(menuName = "Sky Squad/Game Config")]
    public class GameConfig : ScriptableObject
    {
        [Header("World (units: 1 unit ~ 20 px of the HTML prototype)")]
        public float scrollSpeed = 9f;
        public float laneHalfWidth = 4.2f;
        public float altitudeMax = 8.8f;
        public float altitudeSplit = 4.4f;  // below = LOW band (crates), above = HIGH band (enemies)
        public float spawnDistance = 80f;

        [Header("Squad")]
        public int startCount = 1;
        public int startCountPerLevel = 0;
        public float steerSpeed = 8f;
        public float climbSpeed = 7.5f;
        public float dragUnitsPerScreen = 18f;  // drag across the whole screen height = this many units
        public int maxVisiblePlanes = 28;
        public float formationSpacingX = 1.1f;  // V-wing: sideways step per pair
        public float formationSpacingZ = 0.9f;  // V-wing: back step per pair
        public float spiralSpacing = 0.62f;     // phyllotaxis: r = spacing * sqrt(i)

        [Header("Combat")]
        public float lineOfFireRange = 95f;
        public float pierceHalfWidth = 1.2f;    // laser: planes behind the first hit within this x band are hit too

        [Header("Level pacing")]
        public float levelDurationBase = 55f;
        public float levelDurationPerLevel = 8f;

        [Header("Enemy stream (high band)")]
        public float firstFlightDistance = 45f; // the first flight starts closer so the shooting begins fast
        public float flightEveryBase = 2.0f;    // seconds between flights: the stream is constant
        public float flightEveryPerLevel = 0.2f;
        public float flightEveryMin = 1.2f;
        public int flightSizeBase = 3;          // planes per V-wing flight
        public int flightSizeMax = 8;
        public int flightSizeEvery = 3;         // flights per +1 plane in a flight
        public int fighterHpEvery = 4;          // flights per +1 hp on fighters
        public float fighterHpPerPlane = 0.15f; // rubber band: fighter hp grows with your plane count
        public float miniBossHpPerPlane = 0.08f;// rubber band: mini boss hp x (1 + count * this)
        public float enemyShotPerPlane = 0.15f; // rubber band: enemy shots hurt more the bigger you are
        public int flightsPerMiniBoss = 4;      // every N-th flight is a mini boss (with two escorts)
        public float miniBossPause = 5f;        // breathing room after a mini boss
        public float wingSpacingX = 1.9f;       // V-wing geometry of a flight
        public float wingSpacingZ = 1.6f;
        public float blockWidth = 1.3f;         // a plane holds behind another whose x is this close
        public float rowSpacing = 2.2f;         // z gap it keeps from the plane ahead
        public float enemyStopZ = 9f;           // the front line: nobody flies closer, they park and shoot
        public float enemyAltAboveSplit = 1.4f; // how high above the split the stream flies
        public float miniBossHpBase = 10f;
        public float miniBossHpPerBoss = 8f;
        public float miniBossHpPerLevel = 5f;

        [Header("Supply lane (low band)")]
        public float supplyAlt = 1.5f;          // altitude the crate queue flies at
        public float supplyFrontZ = 17f;        // the front crate holds this distance ahead
        public float supplySpacing = 6.5f;      // z gap between queued crates
        public int supplyVisible = 4;           // crates kept alive in the queue
        public float boxHpBase = 15f;           // first crate of the level, in bullets
        public float boxHpGrowth = 1.6f;        // every crate after it is this much tougher
        public float boxHpPerLevel = 1.15f;
        public int boxPlanes = 2;               // planes per crate
        public float coinsPerHp = 1f;           // crate reward = hp * this
        public int weaponAt = 3;                // queue index of the first weapon crate (then every weaponEvery)
        public int weaponEvery = 6;

        [Header("Boss")]
        public float bossHpPerDps = 2.0f;       // seconds of the squad's full fire to kill it
        public float bossHpPerPlane = 0.4f;
        public float bossFightSeconds = 10f;
        public float bossFireEvery = 2.2f;      // one plane per shot: fast enough to hurt, slow enough to win
        public float bossStartDistance = 22f;
        public float bossEndDistance = 10.5f;

        [Header("Definitions")]
        public WeaponDef[] weapons;
        public EnemyKindDef enemyFighter;
        public EnemyKindDef enemyMiniBoss;
    }
}
