// GameConfig.cs - every tunable number in one asset (world scale, pacing, enemy stream, crates, boss).
using UnityEngine;

namespace SkySquad
{
    /// <summary>One row of the crate ladder (GameConfig.crates): the crate's hp, the planes riding behind it, whether it holds the next plane.</summary>
    [System.Serializable]
    public class CrateDef
    {
        public float hp;      // bullets to break it
        public int planes;    // the gate behind it: +planes (0 = no gate, coins only)
        public bool weapon;   // a weapon crate: the next plane (WeaponDef) sits on top of it and every plane changes to it on break
        public CrateDef(float hp, int planes, bool weapon = false) { this.hp = hp; this.planes = planes; this.weapon = weapon; }
    }

    [CreateAssetMenu(menuName = "Sky Squad/Game Config")]
    public class GameConfig : ScriptableObject
    {
        [Header("World (units: 1 unit ~ 20 px of the HTML prototype)")]
        public float scrollSpeed = 9f;
        public float laneHalfWidth = 4.2f;
        public float altitudeMax = 5.85f;     // = the crowd's altitude: you can meet them, never fly over them
        public float altitudeSplit = 4.4f;  // below = LOW band (crates), above = HIGH band (enemies)
        public float spawnDistance = 150f;    // fighters spawn here: beyond what the eye resolves, so there is no pop-in (was 80: they appeared inside the fog, half transparent)
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
        public float lineOfFireRange = 48f;   // guns engage this close (34 → 48: "let my bullets reach farther"); do not go to 95, the swarm then dies at the horizon
        public float pierceHalfWidth = 1.2f;    // laser: planes behind the first hit within this x band are hit too
        public float bulletSpeed = 38f;         // the squad's slugs
        public float enemyBulletSpeed = 28f;    // the parked crowd's shots at you
        public float bulletHitRadius = 0.55f;   // a bullet hits any plane within this much of its x: its own column only
        public float bulletLife = 1.45f;        // seconds a bullet flies before it fades (x bulletSpeed 38 = 55 u, past lineOfFireRange)
        public float bulletSize = 1.6f;         // visual scale of the squad's slugs

        [Header("Level pacing")]
        public float levelDurationBase = 55f;
        public float levelDurationPerLevel = 8f;

        [Header("Enemy swarm (high band)")]
        public float laneHalfWidthAim = 0.6f;   // your bullets only go to planes within this much of your x
        public float swarmRate = 4.5f;           // kamikazes per second, no gaps until the boss (2.5 → 3.2 → 4 → 6 → 4.5: "too many in level 1")
        public float swarmRatePerHorde = 1.5f;   // every horde streams this much faster
        public int openingCrowd = 35;            // fighters already in the sky ahead when the attempt starts ("a crowd at the front from the start, not too many")
        public float openingCrowdNearZ = 62f;    // ...spread between these depths
        public float openingCrowdFarZ = 148f;
        public float swarmXRange = 3.8f;        // the sky's half width: the outer lanes sit at +-this
        public int swarmLanes = 6;              // the sky is split into this many lanes; a fighter picks one at spawn and keeps it all the way in
        public float swarmAltSpread = 0.8f;     // and this much above/below the band's centre
        public float swarmDepth = 12f;          // spawn depth jitter so they never line up
        public float swarmSpeedSpread = 0.4f;   // every kamikaze flies its own speed: net approach x (1 +- this), so they never arrive as a row
        public float swarmSpawnJitter = 0.6f;   // the gap between two spawns is scaled by 1 +- this: one comes early, the next late
        public float weave = 0.2f;              // side-to-side weave amplitude inside its lane (keep it below half the lane spacing)
        public float swarmBank = 7f;            // degrees a fighter banks into its weave (was 22: "they lean too much while flying")
        public float diveZ = 7f;                // the strike line (invisible): crossing it a fighter locks the nearest squad plane and strikes it - always
        public float threatWarnRange = 20f;     // a fighter gets its lock-on reticle (ThreatMarkers) this many units before the strike line
        public float strikeLift = 1.2f;         // the strike run arcs this high into the air mid-way before coming down onto the plane
        public float strikeSide = 1.3f;         // how far the slalom and corkscrew figures swing sideways mid-run
        public float strikeAccel = 0.8f;        // it speeds up into the dive: by impact it flies (1 + this) x its cruise speed
        public float strikeShrink = 0.5f;       // it shrinks to this fraction of its size by impact ("becomes half when it is ready to destroy me")
        public int maxAliveEnemies = 300;       // the stream waits while this many are in the air
        public float bossSpawnGap = 3f;         // seconds after the boss before the next horde starts
        public float holdBehindBoss = 4f;       // the next horde loiters this far behind a living boss
        public float enemyStopZ = 12f;          // the front line: a boss parks here and shoots
        public float enemyAltAboveSplit = 1.4f; // centre of the band the swarm flies in
        public float enemyHeightScale = 1.35f;  // a fighter's model is stretched this much vertically (same footprint as a squad plane, taller: reads head-on)
        public float enemyFarScale = 1.7f;      // a fighter's model is this many times bigger at spawnDistance, easing to 1x at enemyFarScaleZ (so the far swarm is never a speck)
        public float enemyFarScaleZ = 22f;      // ...the z where the distance boost has fully faded
        public float miniBossHpBase = 280f;
        public float miniBossHpGrowth = 2.5f;   // boss k hp = miniBossHpBase * growth^(k-1)
        public float miniBossShotPerBoss = 2f;  // boss k shots take base + (k-1)*this planes

        [Header("Hordes")]
        public int hordePlanesBase = 120;       // planes in horde 1 before its boss (scaled with swarmRate so boss 1 comes ~27 s after the stream starts)
        public int hordePlanesPerHorde = 100;   // every horde after it has this many more

        [Header("Upgrades (persist between attempts)")]
        public float upgradeCostFire = 10f;
        public float upgradeCostDamage = 10f;
        public float upgradeCostRevenue = 10f;
        public float upgradeCostGrowth = 1.6f;  // price x this per level bought
        public float fireRatePerLevel = 0.15f;  // volleys per second x (1 + level * this)
        public float damagePerLevel = 0.35f;    // bullet damage x (1 + level * this)
        public float revenuePerLevel = 0.2f;    // coins x (1 + level * this)

        [Header("Supply lane (low band)")]
        public float supplyAlt = 1.5f;          // altitude the crate queue flies at
        public float supplyFrontZ = 17f;        // the front crate holds this distance ahead
        public float supplySpacing = 6.5f;      // z gap between queued crates (plus gateStep per gate the crate in front carries, so its gates fit behind it)
        public int supplyVisible = 10;          // crates kept alive in the queue: a long line you can see, new ones join far beyond view
        public CrateDef[] crates;               // the fixed crate ladder, front to back: hp (bullets), the planes riding behind it, whether the next plane sits on top
        public float crateHpGrowthAfter = 1.7f; // past the end of the table every crate is this much tougher than the last and pays the last row's planes
        public float boxHpPerLevel = 1.15f;     // the whole ladder x this per level
        public float coinsPerHp = 0.3f;         // crate reward = hp * this
        public bool gatesEnabled = true;        // the planes ride behind the crate as a gate you fly through (UpgradeGate); false = the crate itself pays them on break
        public float gateGap = 3.5f;            // how far behind its crate the first gate rides
        public float gateStep = 2f;             // a +n crate carries n gates of +1 one behind the other, this far apart
        public float gateSpeed = 34f;           // how fast a released gate shoots at the squad (u/s): "very fast"
        public float gatePowerBonus = 0.25f;    // past the last weapon, each gate passed adds this much damage (MK n)

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

        /// <summary>World x of the centre of lane i (0 .. swarmLanes-1): the lanes are spread evenly from -swarmXRange to +swarmXRange.</summary>
        public float LaneX(int i)
        {
            int n = Mathf.Max(1, swarmLanes);
            return n == 1 ? 0f : -swarmXRange + i * (2f * swarmXRange / (n - 1));
        }
    }
}
