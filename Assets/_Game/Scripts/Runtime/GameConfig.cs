// GameConfig.cs - every tunable number in one asset (world scale, pacing, horde sizing, boss).
using UnityEngine;

namespace SkySquad
{
    [CreateAssetMenu(menuName = "Sky Squad/Game Config")]
    public class GameConfig : ScriptableObject
    {
        [Header("World (units: 1 unit ~ 20 px of the HTML prototype)")]
        public float scrollSpeed = 15f;
        public float laneHalfWidth = 4.2f;
        public float sideX = 3.8f;          // where side gates sit
        public float altitudeMax = 8.8f;
        public float altitudeSplit = 4.4f;  // below = LOW band, above = HIGH band
        public float spawnDistance = 95f;

        [Header("Squad")]
        public int startCount = 6;
        public int startCountPerLevel = 4;
        public float steerSpeed = 10f;
        public float climbSpeed = 9.5f;
        public float dragUnitsPerScreen = 22f;  // drag across the whole screen height = this many units
        public int maxVisiblePlanes = 28;

        [Header("Combat")]
        public float baseDps = 3f;
        public float dpsPerPlane = 0.45f;
        public float fireConeHalfWidth = 1.2f;  // added to the target's own half width
        public float fireConeHalfHeight = 4f;
        public float lineOfFireRange = 95f;

        [Header("Level pacing")]
        public float levelDurationBase = 32f;
        public float levelDurationPerLevel = 5f;
        public float waveEveryBase = 3.4f;
        public float waveEveryPerLevel = 0.18f;
        public float waveEveryMin = 1.5f;
        public float pickEveryBase = 2.6f;
        public float pickEveryPerLevel = 0.08f;
        public float pickEveryMin = 1.6f;

        [Header("Horde sizing")]
        public float hordeBase = 3f;
        public float hordeBasePerLevel = 2.5f;
        public float hordeGrowth = 0.18f;       // units per second of level time
        public float hordeGrowthPerLevel = 0.03f;
        public float hordeScaleByCount = 0.28f; // rubber band: hordes grow with your squad
        public float rampSeconds = 15f;         // first waves of a level are smaller
        public int bigHordeThreshold = 18;

        [Header("Boss")]
        public float bossHpPerDps = 4.5f;
        public float bossHpPerPlane = 0.4f;
        public float bossFightSeconds = 10f;
        public float bossFireEvery = 0.55f;
        public float bossWaveEvery = 4f;
        public float bossStartDistance = 22f;
        public float bossEndDistance = 10.5f;

        [Header("Definitions")]
        public WeaponDef[] weapons;
        public HordeKindDef[] hordeKinds;
    }
}
