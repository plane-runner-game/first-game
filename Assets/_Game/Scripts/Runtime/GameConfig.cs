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
        public float altitudeMax = 5.85f;     // = the crowd's altitude: you can meet them, never fly over them
        public float altitudeSplit = 4.4f;  // below = LOW band (crates), above = HIGH band (enemies)
        public float spawnDistance = 80f;
        public bool endless = true;         // test mode: no mini boss, no zeppelin, the stream never ends

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
        public float lineOfFireRange = 34f;   // guns only engage this close: the swarm gets to fly in before it dies
        public float pierceHalfWidth = 1.2f;    // laser: planes behind the first hit within this x band are hit too
        public float bulletSpeed = 38f;         // the squad's slugs
        public float enemyBulletSpeed = 28f;    // the parked crowd's shots at you
        public float bulletHitRadius = 0.55f;   // a bullet hits any plane within this much of its x: its own column only
        public float bulletLife = 1.1f;         // seconds a bullet flies before it fades
        public float bulletSize = 1.6f;         // visual scale of the squad's slugs

        [Header("Level pacing")]
        public float levelDurationBase = 55f;
        public float levelDurationPerLevel = 8f;

        [Header("Enemy swarm (high band)")]
        public float laneHalfWidthAim = 0.6f;   // your bullets only go to planes within this much of your x
        public float swarmRate = 2.5f;           // kamikazes per second, no gaps until the boss
        public float swarmRatePerHorde = 1.5f;   // every horde streams this much faster
        public float swarmXRange = 3.8f;        // they spawn anywhere across this much of the sky (+-)
        public float swarmAltSpread = 0.8f;     // and this much above/below the band's centre
        public float swarmDepth = 12f;          // spawn depth jitter so they never line up
        public float followSpeed = 0.6f;        // how fast a fighter drifts toward your lane while far away
        public float weave = 0.35f;             // side-to-side weave amplitude
        public float diveZ = 7f;                // closer than this it dives at you...
        public float diveFollow = 3f;           // ...closing sideways this fast...
        public float diveClimb = 8f;            // ...and matching your altitude this fast
        public float ramZ = 1.2f;               // it blows up on you when it reaches this z inside the hit width
        public float ramHitX = 1.4f;            // hit width around the squad's x...
        public float ramHitPerPlane = 0.08f;    // ...plus this per visible plane (a big formation is a big target)
        public int maxAliveEnemies = 150;       // the stream waits while this many are in the air
        public float bossSpawnGap = 3f;         // seconds after the boss before the next horde starts
        public float holdBehindBoss = 4f;       // the next horde loiters this far behind a living boss
        public float enemyStopZ = 12f;          // the front line: a boss parks here and shoots
        public float enemyAltAboveSplit = 1.4f; // centre of the band the swarm flies in
        public float miniBossHpBase = 280f;
        public float miniBossHpGrowth = 2.5f;   // boss k hp = miniBossHpBase * growth^(k-1)
        public float miniBossShotPerBoss = 2f;  // boss k shots take base + (k-1)*this planes

        [Header("Hordes")]
        public int hordePlanesBase = 100;       // planes in horde 1 before its boss
        public int hordePlanesPerHorde = 100;   // every horde after it has this many more

        [Header("Upgrades (persist between attempts)")]
        public float upgradeCostFire = 50f;
        public float upgradeCostDamage = 60f;
        public float upgradeCostRevenue = 40f;
        public float upgradeCostGrowth = 1.6f;  // price x this per level bought
        public float fireRatePerLevel = 0.15f;  // volleys per second x (1 + level * this)
        public float damagePerLevel = 0.35f;    // bullet damage x (1 + level * this)
        public float revenuePerLevel = 0.2f;    // coins x (1 + level * this)

        [Header("Supply lane (low band)")]
        public float supplyAlt = 1.5f;          // altitude the crate queue flies at
        public float supplyFrontZ = 17f;        // the front crate holds this distance ahead
        public float supplySpacing = 6.5f;      // z gap between queued crates
        public int supplyVisible = 4;           // crates kept alive in the queue
        public float boxHpBase = 15f;           // first crate of the level, in bullets
        public float boxHpGrowth = 2.2f;        // every crate after it is this much tougher
        public float boxHpPerLevel = 1.15f;
        public int boxPlanes = 2;               // planes per crate
        public float coinsPerHp = 0.3f;           // crate reward = hp * this
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
