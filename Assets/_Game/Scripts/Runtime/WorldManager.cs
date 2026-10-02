// WorldManager.cs
// The worlds of the game (2026-10-02: "a complete second level from the Inferno World pack, its own bosses, and a screen to choose the level").
// A world is a whole look and a whole cast: its scene roots (sea or lava, rocks, smoke), its sky, light, fog and post-processing, its fighters
// and its thirty bosses with their attacks. Every world lives in the one scene; Apply(i) switches one on and the other off in a single frame,
// and WaveSpawner / SupplyLane / FXManager are handed that world's prefabs. The round itself (rules, crates, upgrades) is shared.
using System;
using UnityEngine;
using UnityEngine.Rendering;

namespace SkySquad
{
    [Serializable]
    public class WorldEntry
    {
        [Header("Identity")]
        public string id = "sea";
        public string displayName = "SKY SEA";
        public string tagline = "Open ocean";
        public Sprite thumbnail;                 // the card on the world-select screen (captured from the world itself)
        public Color accent = new Color(0.3f, 0.7f, 1f);

        [Header("Scene")]
        public GameObject[] environment;         // scene roots that are on in this world and off in the others
        public Material skybox;
        public float skyRotation = 0f;
        public Color sunColor = Color.white; public float sunIntensity = 1.5f; public Vector3 sunEuler = new Vector3(52f, -28f, 0f); public float sunShadow = 0.55f;
        public bool fog = true; public Color fogColor = Color.white; public float fogStart = 130f, fogEnd = 160f;
        public bool ambientFromSky = true;       // true: lit by the skybox; false: a three-colour gradient (sky / equator / ground) - the lava world lights the planes' undersides orange from below
        public Color ambientSky = Color.gray, ambientEquator = Color.gray, ambientGround = Color.gray; public float ambientIntensity = 1f;
        public VolumeProfile post;

        [Header("Cast")]
        public GameObject fighterPrefab;
        public GameObject[] bossPrefabs;         // the looks (fallback when a number has none of its own)
        public GameObject[] bossPrefabByNumber;  // boss N wears element N-1
        public BossAttack[] bossAttacks, bossAttacks2;
        public string[] bossNames;
        public string[] stageNames;              // a name for each stage of five bosses (the banner says "STAGE 2 - ASH PLAINS")
        public Color[] bossColors;
        public bool onGround;                    // a land world: crates stand still on the ground instead of bobbing on water
        public int lastBoss;                     // 0: the config's (30); a short world ends after this many bosses (the meadow has 5)
        public float bossHpMul = 1f;             // this world's bosses have this much more hp than the table (the second world is harder)

        [Header("Props")]
        public GameObject breakablePrefab;       // the supply crate on its raft
        public GameObject splashPrefab;          // what a wreck throws up where it lands (spray on water, sparks and embers in lava)
        public Color surfaceRing = new Color(0.85f, 0.95f, 1f);   // the ripple ring colour where something sinks (SinkingBoat)
    }

    public class WorldManager : MonoBehaviour
    {
        public static WorldManager I { get; private set; }

        public WorldEntry[] worlds;
        public Light sun;
        public Volume volume;
        public int Current { get; private set; } = -1;
        public WorldEntry Entry => worlds != null && Current >= 0 && Current < worlds.Length ? worlds[Current] : null;
        public int Count => worlds != null ? worlds.Length : 0;
        public event Action<int> OnWorldChanged;

        void Awake() { I = this; }

        void Start()
        {
            if (Current < 0) Apply(Mathf.Clamp(Progress.World, 0, Mathf.Max(0, Count - 1)));
        }

        /// <summary>Switches the whole game to world i: the scene, the light, the cast, the props. Safe to call at any time (the round that was
        /// waiting in the lobby is rebuilt by GameManager.SelectWorld afterwards).</summary>
        public void Apply(int i)
        {
            if (worlds == null || worlds.Length == 0) return;
            i = Mathf.Clamp(i, 0, worlds.Length - 1);
            for (int w = 0; w < worlds.Length; w++)
                if (w != i && worlds[w].environment != null)
                    foreach (var go in worlds[w].environment) if (go != null) go.SetActive(false);
            var e = worlds[i];
            if (e.environment != null) foreach (var go in e.environment) if (go != null) go.SetActive(true);
            Current = i;

            if (e.skybox != null)
            {
                RenderSettings.skybox = e.skybox;
                if (e.skybox.HasProperty("_Rotation")) e.skybox.SetFloat("_Rotation", e.skyRotation);
            }
            RenderSettings.fog = e.fog; RenderSettings.fogMode = FogMode.Linear;
            RenderSettings.fogColor = e.fogColor; RenderSettings.fogStartDistance = e.fogStart; RenderSettings.fogEndDistance = e.fogEnd;
            if (e.ambientFromSky) { RenderSettings.ambientMode = UnityEngine.Rendering.AmbientMode.Skybox; RenderSettings.ambientIntensity = e.ambientIntensity; }
            else
            {
                RenderSettings.ambientMode = UnityEngine.Rendering.AmbientMode.Trilight;
                RenderSettings.ambientSkyColor = e.ambientSky; RenderSettings.ambientEquatorColor = e.ambientEquator; RenderSettings.ambientGroundColor = e.ambientGround; RenderSettings.ambientIntensity = e.ambientIntensity;
            }
            if (sun != null)
            {
                sun.color = e.sunColor; sun.intensity = e.sunIntensity; sun.shadowStrength = e.sunShadow;
                sun.transform.rotation = Quaternion.Euler(e.sunEuler);
                RenderSettings.sun = sun;
            }
            if (volume != null && e.post != null) volume.sharedProfile = e.post;
            DynamicGI.UpdateEnvironment();

            var ws = WaveSpawner.I != null ? WaveSpawner.I : FindAnyObjectByType<WaveSpawner>();
            if (ws != null)
            {
                if (e.fighterPrefab != null) ws.fighterPrefab = e.fighterPrefab;
                ws.bossPrefabs = e.bossPrefabs; ws.bossPrefabByNumber = e.bossPrefabByNumber;
                ws.bossAttacks = e.bossAttacks; ws.bossAttacks2 = e.bossAttacks2;
                ws.bossNames = e.bossNames; ws.stageNames = e.stageNames; ws.bossColors = e.bossColors; ws.bossHpMul = e.bossHpMul;
            }
            var sl = SupplyLane.I != null ? SupplyLane.I : FindAnyObjectByType<SupplyLane>();
            if (sl != null && e.breakablePrefab != null) sl.breakablePrefab = e.breakablePrefab;
            var fx = FXManager.I != null ? FXManager.I : FindAnyObjectByType<FXManager>();
            if (fx != null && e.splashPrefab != null) fx.splashPrefab = e.splashPrefab;
            OnWorldChanged?.Invoke(i);
        }
    }
}
