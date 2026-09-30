// SceneBuilder.Bosses.cs (Editor only)
// The thirty bosses (2026-09-30: "at least 30 bosses, every boss different from another; take one thing from each boss and create
// another"). Six are the pack models the game already had (Sparrow 1, Cruiser 3, Station 5, Virginia 10, Dropship 15, Corvette 30);
// the other 24 are kitbashed in BossKit from a hull + wings + crown each, in their own colours. Every boss has TWO attacks: the one
// he opens with and the one he is enraged into below half his hp (Enemy.Enrage), and his own way of moving (MoveStyle).
// Stages of five: the fifth boss of each stage (5, 10, 15, 20, 25, 30) is its finale, drawn wider than the rest.
using UnityEngine;
using UnityEditor;

namespace SkySquad.EditorTools
{
    public static partial class SceneBuilder
    {
        const int BossCount = 30;
        static readonly int[] PackBossNumbers = { 1, 3, 5, 10, 15, 30 };   // the bosses that wear a pack model (or the Sparrow): everything else is a kit boss

        static readonly string[] BossNames = {
            "SPARROW", "IRON MANTA", "THUNDER CRUISER", "GRIM SKULL", "STATION OMEGA",
            "STORM DART", "CRIMSON CARRIER", "EMBER ORB", "TWIN FANG", "IRON VIRGINIA",
            "FROST WARDEN", "THUNDER BLOCK", "VIPER CROSS", "SOLAR HALO", "R35 DROPSHIP",
            "JADE SENTINEL", "NIGHT REAPER", "IVORY LANCE", "RUST TITAN", "ABYSS EYE",
            "GOLDEN CROWN", "PLASMA WIDOW", "BONE DRAGON", "STEEL HORNET", "SKY FORTRESS",
            "VOID SPIDER", "COBALT CRESCENT", "INFERNO KING", "STAR EATER", "OVERLORD F3" };

        static GameObject[] procBosses;   // by boss number - 1; null where a pack model serves

        static bool IsPackBoss(int number) { return System.Array.IndexOf(PackBossNumbers, number) >= 0; }

        /// <summary>
        /// The ship each of the 24 other bosses wears (2026-09-30: "some of the boss shapes are disgusting - find free assets and use them"):
        /// the kitbashed shapes read as boxes, so the bosses are now the free ships already in the project - Star Sparrow's forty (the three
        /// the squad flies are left out) and HiRez's examples - each in its own colours, baked light like the other pack bosses. The kit
        /// (BossKit) stays as the fallback when a pack is not imported.
        /// </summary>
        static readonly string[] ShipForBoss = new string[BossCount + 1] {
            null,
            null, "S26", null, "S9", null,                  // 1-5    (1 Sparrow, 3 cruiser, 5 station: their own models)
            "S22", "H1", "S13", "S8", null,                 // 6-10   (10 Virginia)
            "S38", "H2", "S10", "S21", null,                // 11-15  (15 dropship)
            "S24", "S6", "H3", "S35", "S17",                // 16-20  (20: the yellow heavy)
            "S7", "S18", "S39", "H4", "S30",                // 21-25  (25: the quad-tail)
            "S14", "S19", "S23", "S15", null };             // 26-30  (30 corvette)

        static string ShipPath(string code)
        {
            if (code[0] == 'S') return "Assets/StarSparrow/Prefabs/Examples/StarSparrow" + code.Substring(1) + ".prefab";
            string[] hirez = { "Example1NoInterior_Grey", "Example2NoInterior_Grey", "Example3NoInterior_Red", "Example4NoInterior_Grey" };
            return "Assets/HiRezSpaceshipsCreatorFree/Prefabs/ExamplesNoInterior/" + hirez[int.Parse(code.Substring(1)) - 1] + ".prefab";
        }

        /// <summary>The 24 other bosses as prefabs, indexed by boss number - 1 (null for the six that have their own).</summary>
        static GameObject[] BuildProceduralBosses(Mats M)
        {
            var res = new GameObject[BossCount];
            int i = 0;
            for (int number = 1; number <= BossCount; number++)
            {
                if (IsPackBoss(number)) continue;
                bool finale = number % 5 == 0;
                string id = "ProcBoss" + number.ToString("00");
                GameObject prefab = null;
                string code = ShipForBoss[number];
                if (code != null)
                {
                    var def = new PackBoss { name = "Ship" + number.ToString("00"), packPrefab = ShipPath(code), width = finale ? 3.6f : 3.0f, triangles = 6000, lieAcross = false, keepMaterials = code[0] == 'S' };
                    prefab = PackBossPrefab(def, EnsurePackBossLow(def), M);
                    if (prefab != null) Debug.Log("[SkySquad] boss " + number + " " + BossNames[number - 1] + ": " + code);
                }
                if (prefab == null)
                {   // the pack is not there: the kitbashed shape
                    BossKit.Triple(i, out int hull, out int wing, out int crown);
                    float width = finale ? 3.3f : 2.4f + 0.02f * number;
                    var kb = BossKit.Build(id, hull, wing, crown, width);
                    var mesh = SaveMesh(kb.mesh);
                    float h = Mathf.Repeat(i * 0.618f + 0.08f, 1f);
                    var body = Lit(id + "Body", Color.HSVToRGB(h, 0.6f, 0.55f), 0.4f);
                    var accent = Lit(id + "Accent", Color.HSVToRGB(Mathf.Repeat(h + 0.45f, 1f), 0.85f, 1f), 0.4f);
                    var glow = Unlit(id + "Glow", Color.HSVToRGB(Mathf.Repeat(h + 0.45f, 1f), 0.45f, 1f));
                    prefab = ProcBossPrefab(id, mesh, kb, body, accent, glow, M);
                }
                res[number - 1] = prefab;
                i++;
            }
            return res;
        }

        static GameObject ProcBossPrefab(string name, Mesh mesh, BossKit.Built kb, Material body, Material accent, Material glow, Mats M)
        {
            var root = new GameObject(name);
            var en = root.AddComponent<Enemy>();
            var bodyGo = MeshObj("Body", mesh, root.transform, body, accent, M.bossGlass, M.enemyCowl, glow);
            bodyGo.transform.localRotation = Quaternion.Euler(0f, 180f, 0f);   // nose toward the player; EnemyKindDef.scale is applied at runtime
            Outline(bodyGo, mesh, M.outline, 1.05f);
            en.model = bodyGo.transform;
            en.bodyRenderer = bodyGo.GetComponent<Renderer>();
            var flash = GameObject.CreatePrimitive(PrimitiveType.Quad); Object.DestroyImmediate(flash.GetComponent<Collider>());
            flash.name = "Flash"; flash.transform.SetParent(bodyGo.transform, false);
            flash.transform.localPosition = new Vector3(0f, -0.1f, kb.noseZ + 0.15f); flash.transform.localRotation = Quaternion.Euler(0f, 180f, 0f); flash.transform.localScale = Vector3.one * 0.7f;
            var fr = flash.GetComponent<MeshRenderer>(); fr.sharedMaterial = M.bossFlash; fr.enabled = false; fr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            en.flashRenderer = fr;
            float barY = Mathf.Max(2.8f, kb.top * BossModelScale + 0.6f);
            en.hpLabel = Label3D("HpLabel", root.transform, new Vector3(0f, barY + 0.82f, 0f), 10f, Color.white, fontOutline);
            BossHpBar(en, root, M, barY, 3.6f);
            return SavePrefab(root, name);
        }

        // ------------------------------------------------------------------ attacks
        static BossAttack Fly(string name, string kind, int volley, float stagger, float spread, float windup, MoveStyle mv, float range, float speed,
                              float bob = 0f, float fire = 0f, float scale = 2.5f, int eVol = 1, float eFire = 0.7f)
        {
            string hit; Sfx snd;
            switch (kind)
            {
                case "fire": hit = "Fire/CFXR3 Hit Fire B (Air)"; snd = Sfx.Rocket; break;
                case "frost": hit = "Ice/CFXR3 Hit Ice B (Air)"; snd = Sfx.Laser; break;
                case "magic": hit = "Eerie/CFXR2 WW Enemy Explosion"; snd = Sfx.Laser; break;
                case "dark_magic": hit = "Misc/CFXR3 Hit Misc A"; snd = Sfx.Flak; break;
                case "light": hit = "Light/CFXR3 Hit Light B (Air)"; snd = Sfx.Laser; break;
                case "water": hit = "Liquids/CFXR Water Splash (Smaller)"; snd = Sfx.Flak; break;
                case "wind": hit = "Nature/CFXR3 Hit Leaves A (Lit)"; snd = Sfx.Flak; break;
                default: hit = "Impacts/CFXR Hit A (Red)"; snd = Sfx.Flak; break;   // green_shuriken
            }
            return new BossAttack {
                name = name, volley = volley, volleyStagger = stagger, volleySpread = spread, windup = windup, move = mv, moveRange = range, moveSpeed = speed, bobRange = bob,
                fireEvery = fire, enrageVolley = eVol, enrageFire = eFire, charge = Cfxr("Light/CFXR3 LightGlow A (Loop)"), chargeScale = 1.2f,
                projectile = Vfx("Range_attack/Projectiles_" + kind), projectileScale = scale, hit = Cfxr(hit), hitScale = 1f,
                muzzle = Vfx("Range_attack/Hit_" + kind), muzzleScale = 0.8f, sound = snd };
        }

        /// <summary>A strike from the sky: family "rocket" (a shell falls, hit 0.7 s in), "lightning" (a bolt, 0.2 s), "beam" (a column, 1 s); the variant is the prefab's own name.</summary>
        static BossAttack Sky(string name, string variant, int count, float stagger, float windup, MoveStyle mv, float range, float speed,
                              float bob = 0f, float fire = 0f, int eVol = 1, float eFire = 0.7f)
        {
            const string zap = "Assets/Vefects/Zap VFX URP/";
            var a = new BossAttack {
                name = name, sky = Vfx("Top_down_attack/" + variant), skyCount = count, skyStagger = stagger, windup = windup, move = mv, moveRange = range, moveSpeed = speed, bobRange = bob,
                fireEvery = fire, enrageVolley = eVol, enrageFire = eFire, charge = Cfxr("Light/CFXR3 LightGlow A (Loop)"), chargeScale = 1.2f };
            if (variant.Contains("rocket")) { a.skyScale = 0.4f; a.skyImpact = 0.7f; a.sound = Sfx.Boom; a.skyHit = Cfxr("Explosions/CFXR Explosion 1"); a.skyHitScale = 0.8f; }
            else if (variant.Contains("lightning")) { a.skyScale = 1f; a.skyImpact = 0.2f; a.skyHit = Cfxr("Electric/CFXR3 Hit Electric C (Air)"); a.skyHitScale = 0.8f; a.sfx = AssetDatabase.LoadAssetAtPath<AudioClip>(zap + "Audio/WAV/SFX_Vefects_Zap_Big_01.wav"); }
            else { a.skyScale = 0.6f; a.skyImpact = 1f; a.skyHit = Cfxr("Impacts/CFXR Impact Glowing HDR (Blue)"); a.skyHitScale = 1f; a.sfx = AssetDatabase.LoadAssetAtPath<AudioClip>(zap + "Audio/WAV/SFX_Vefects_Zap_Big_02.wav"); }
            return a;
        }

        /// <summary>A boss's signature laid over his shot: where it leaves from, the order he works through the squad, how fast it flies, how many
        /// times it repeats, the kick, and what glows at his muzzle while he charges (an element's own glow, not the same white one for everybody).</summary>
        static BossAttack Sig(BossAttack a, ShotOrigin o = ShotOrigin.Muzzle, ShotOrder ord = ShotOrder.Random, float sp = 1f, int salvos = 1, float gap = 0.45f, float shake = 0f, string charge = null, float chargeScale = 1f)
        {
            a.origin = o; a.order = ord; a.speedMul = sp; a.salvos = salvos; a.salvoGap = gap; a.shake = shake;
            if (charge != null) { var c = Cfxr(charge); if (c != null) { a.charge = c; a.chargeScale = chargeScale; } }
            return a;
        }

        const string GlowFire = "Fire/CFXR Fire", GlowBolt = "Electric/CFXR Electrified 3", GlowRune = "Magic Misc/CFXR3 Magic Aura A (Runic)", GlowLight = "Light/CFXR3 LightGlow A (Loop)";

        /// <summary>Boss N's opening attack (element N-1). The six that keep their pack models keep the shots they were given on 2026-09-27
        /// (with a signature laid over each); the other 24 each have their own. No two bosses share where the shot leaves from, the order he works
        /// through the squad, the element, the speed and the count all at once.</summary>
        static BossAttack[] BossAttacks30()
        {
            var old = BossAttacks();   // 0 fireball, 1 vortex, 2 lightning, 3 missiles, 4 plasma, 5 frost, 6 orbital beam
            var A = new BossAttack[BossCount];
            A[0] = Sig(old[0], sp: 0.8f, shake: 0.1f, charge: GlowFire, chargeScale: 1.4f);                                              // 1  SPARROW: one slow fireball
            A[2] = Sig(old[1], ShotOrigin.Muzzle, ShotOrder.Random, 1f, 1, 0.45f, 0.15f);                                                // 3  CRUISER: the tornado
            A[4] = Sig(old[2], ShotOrigin.Muzzle, ShotOrder.LeftToRight, 1f, 1, 0.45f, 0.2f, GlowBolt, 1.4f);                            // 5  STATION: three bolts, left to right
            A[9] = Sig(old[3], ShotOrigin.Muzzle, ShotOrder.RightToLeft, 1f, 1, 0.45f, 0.2f);                                            // 10 VIRGINIA: shells walking right to left
            A[14] = Sig(old[4], ShotOrigin.Wings, ShotOrder.Random, 1.1f, 1, 0.45f, 0.15f, GlowRune);                                    // 15 DROPSHIP: plasma off both wings
            A[29] = Sig(old[6], ShotOrigin.Muzzle, ShotOrder.CenterOut, 1f, 1, 0.45f, 0.3f, GlowLight, 1.6f);                           // 30 CORVETTE: beams closing out from the middle
            A[1] = Sig(Fly("gale fan", "wind", 5, 0.08f, 2.4f, 0.4f, MoveStyle.Sweep, 2.4f, 1.2f, 0f, 3.4f), ShotOrigin.Wings, ShotOrder.LeftToRight, 1.3f);
            A[3] = Sig(Fly("curse rain", "dark_magic", 4, 0.16f, 1.6f, 0.6f, MoveStyle.Dash, 3.0f, 1f, 0f, 3.8f, 3.0f), ShotOrigin.Above, ShotOrder.CenterOut, 0.6f, 1, 0.45f, 0.1f, GlowRune);
            A[5] = Sig(Fly("shuriken spin", "green_shuriken", 5, 0.07f, 1.6f, 0.35f, MoveStyle.Sweep, 3.0f, 1.6f, 0f, 3.2f), ShotOrigin.Muzzle, ShotOrder.Random, 1.6f, 2, 0.35f);
            A[6] = Sig(Sky("rocket salvo", "top_down_rocket_dot_pink", 3, 0.25f, 0.6f, MoveStyle.Sway, 1.2f, 0.7f, 0f, 4.2f), ShotOrigin.Muzzle, ShotOrder.RightToLeft, 1f, 1, 0.45f, 0.15f);
            A[7] = Sig(Fly("fire comets", "fire", 3, 0.22f, 1.4f, 0.45f, MoveStyle.Figure8, 2.0f, 1f, 0.6f, 3.6f, 3.0f), ShotOrigin.Above, ShotOrder.OutsideIn, 0.7f, 1, 0.45f, 0.15f, GlowFire, 1.2f);
            A[8] = Sig(Fly("twin lances", "light", 2, 0.3f, 2.4f, 0.5f, MoveStyle.Dash, 3.2f, 1f, 0f, 3.2f, 4.0f), ShotOrigin.Wings, ShotOrder.Random, 2.0f, 1, 0.45f, 0.2f);
            A[10] = Sig(Fly("ice barrage", "frost", 6, 0.1f, 1.6f, 0.4f, MoveStyle.Sway, 1.5f, 1.1f, 0f, 3.8f), ShotOrigin.Above, ShotOrder.CenterOut, 0.8f);
            A[11] = Sig(Sky("thunder grid", "top_down_lightning_circle_blue", 4, 0.12f, 0.8f, MoveStyle.Sway, 1.0f, 0.6f, 0f, 4.6f), ShotOrigin.Muzzle, ShotOrder.LeftToRight, 1f, 1, 0.45f, 0.2f, GlowBolt, 1.2f);
            A[12] = Sig(Fly("acid spit", "water", 3, 0.12f, 2.4f, 0.3f, MoveStyle.Sweep, 3.4f, 2.0f, 0f, 2.8f), ShotOrigin.Wings, ShotOrder.Random, 1.7f, 3, 0.5f);
            A[13] = Sig(Sky("sun beams", "top_down_beam_circle_green", 2, 0.3f, 0.9f, MoveStyle.Orbit, 2.0f, 0.9f, 0.8f, 4.2f), ShotOrigin.Muzzle, ShotOrder.OutsideIn, 1f, 1, 0.45f, 0.2f, GlowLight, 1.6f);
            A[15] = Sig(Fly("jade stars", "green_shuriken", 3, 0.14f, 2.0f, 0.4f, MoveStyle.Figure8, 2.6f, 1.1f, 0.5f, 3.6f, 2.8f), ShotOrigin.Sides, ShotOrder.Random, 0.7f, 1, 0.45f, 0f, GlowRune);
            A[16] = Sig(Fly("reaper volley", "dark_magic", 5, 0.1f, 2.0f, 0.5f, MoveStyle.Dash, 3.4f, 1f, 0f, 3.4f), ShotOrigin.Wings, ShotOrder.RightToLeft, 1.4f, 2, 0.4f, 0.1f, GlowRune);
            A[17] = Sig(Fly("ivory lance", "light", 1, 0.1f, 1.0f, 1.0f, MoveStyle.Sweep, 3.2f, 1.0f, 0f, 3.0f, 4.6f), ShotOrigin.Muzzle, ShotOrder.Random, 2.4f, 1, 0.45f, 0.3f, GlowLight, 1.8f);
            A[18] = Sig(Sky("rust barrage", "top_down_rocket_line_pink", 4, 0.18f, 0.8f, MoveStyle.Sway, 0.8f, 0.6f, 0f, 5.0f), ShotOrigin.Muzzle, ShotOrder.RightToLeft, 1f, 1, 0.45f, 0.2f);
            A[19] = Sig(Fly("abyss gaze", "magic", 6, 0.2f, 1.8f, 0.5f, MoveStyle.Orbit, 1.6f, 1.0f, 0.9f, 3.8f, 3.2f), ShotOrigin.Above, ShotOrder.OutsideIn, 0.55f, 1, 0.45f, 0.15f, GlowRune, 1.4f);
            A[20] = Sig(Fly("golden rain", "light", 4, 0.12f, 2.4f, 0.4f, MoveStyle.Figure8, 2.4f, 1.2f, 0.7f, 3.4f, 2.6f), ShotOrigin.Above, ShotOrder.Random, 1.5f);
            A[21] = Sig(Fly("plasma web", "magic", 6, 0.07f, 2.2f, 0.4f, MoveStyle.Sweep, 3.6f, 2.2f, 0f, 3.0f), ShotOrigin.Sides, ShotOrder.OutsideIn, 1.2f, 1, 0.45f, 0.1f);
            A[22] = Sig(Fly("dragon breath", "fire", 5, 0.05f, 1.2f, 0.5f, MoveStyle.Figure8, 2.8f, 0.9f, 0.8f, 3.6f, 2.8f), ShotOrigin.Muzzle, ShotOrder.Random, 1.3f, 2, 0.35f, 0.15f, GlowFire, 1.4f);
            A[23] = Sig(Fly("hornet swarm", "wind", 6, 0.09f, 2.2f, 0.3f, MoveStyle.Dash, 3.6f, 1f, 0f, 2.6f), ShotOrigin.Wings, ShotOrder.CenterOut, 1.8f, 2, 0.3f);
            A[24] = Sig(Sky("fortress fire", "top_down_rocket_circle_red", 5, 0.12f, 1.0f, MoveStyle.Sway, 1.0f, 0.5f, 0f, 5.0f), ShotOrigin.Muzzle, ShotOrder.CenterOut, 1f, 1, 0.45f, 0.3f, GlowFire, 1.6f);
            A[25] = Sig(Fly("void fangs", "dark_magic", 7, 0.07f, 2.4f, 0.4f, MoveStyle.Orbit, 2.2f, 1.1f, 0.8f, 3.6f), ShotOrigin.Sides, ShotOrder.LeftToRight, 0.65f, 1, 0.45f, 0.1f, GlowRune);
            A[26] = Sig(Sky("crescent beams", "top_down_beam_line_blue", 4, 0.2f, 0.9f, MoveStyle.Sweep, 3.2f, 1.2f, 0f, 4.2f), ShotOrigin.Muzzle, ShotOrder.LeftToRight, 1f, 1, 0.45f, 0.2f, GlowLight, 1.5f);
            A[27] = Sig(Fly("inferno", "fire", 8, 0.06f, 2.6f, 0.6f, MoveStyle.Figure8, 3.0f, 1.0f, 1.0f, 4.0f, 3.0f), ShotOrigin.Above, ShotOrder.OutsideIn, 1f, 2, 0.5f, 0.35f, GlowFire, 1.8f);
            A[28] = Sig(Sky("star storm", "top_down_lightning_circle_blue", 6, 0.1f, 0.9f, MoveStyle.Orbit, 2.4f, 1.0f, 0.8f, 4.4f), ShotOrigin.Muzzle, ShotOrder.Random, 1f, 2, 0.6f, 0.3f, GlowBolt, 1.6f);
            for (int i = 0; i < BossCount; i++) { if (A[i] != null && A[i].charge == null) A[i].charge = Cfxr(GlowLight); if (A[i] != null && A[i].enrageAt <= 0f) A[i].enrageAt = 0.5f; }
            return A;
        }

        /// <summary>Boss N's enraged attack (element N-1), or null to keep his opening one (faster, and with enrageVolley more at once). Each is a
        /// different figure from his first: a sweep where he stood still, a rain where he fired across, the element changed.</summary>
        static BossAttack[] BossAttacks2()
        {
            var B = new BossAttack[BossCount];
            B[0] = Sig(Fly("twin fireballs", "fire", 2, 0.2f, 1.2f, 0.3f, MoveStyle.Sway, 1.4f, 1f), ShotOrigin.Wings, ShotOrder.Random, 1.1f, 1, 0.45f, 0.2f, GlowFire, 1.4f);
            B[1] = Sig(Sky("thunder strikes", "top_down_lightning_dot_orange", 3, 0.15f, 0.5f, MoveStyle.Sweep, 3.0f, 1.6f), ShotOrigin.Muzzle, ShotOrder.LeftToRight, 1f, 1, 0.45f, 0.2f, GlowBolt);
            B[3] = Sig(Fly("skull barrage", "dark_magic", 3, 0.1f, 2.2f, 0.4f, MoveStyle.Dash, 3.4f, 1.2f), ShotOrigin.Sides, ShotOrder.Random, 1.3f, 2, 0.3f, 0.2f, GlowRune);
            B[5] = Sig(Fly("shuriken blizzard", "green_shuriken", 6, 0.07f, 2.2f, 0.3f, MoveStyle.Sweep, 3.4f, 2.2f), ShotOrigin.Above, ShotOrder.LeftToRight, 1.6f, 2, 0.3f, 0.2f);
            B[6] = Sig(Sky("rocket carpet", "top_down_rocket_line_pink", 5, 0.15f, 0.5f, MoveStyle.Sway, 1.6f, 0.9f), ShotOrigin.Muzzle, ShotOrder.CenterOut, 1f, 1, 0.45f, 0.25f);
            B[7] = Sig(Sky("meteor rain", "top_down_rocket_circle_red", 3, 0.2f, 0.5f, MoveStyle.Figure8, 2.4f, 1.2f, 0.7f), ShotOrigin.Muzzle, ShotOrder.OutsideIn, 1f, 2, 0.4f, 0.25f, GlowFire, 1.3f);
            B[8] = Sig(Fly("fang volley", "light", 4, 0.15f, 2.6f, 0.3f, MoveStyle.Dash, 3.6f, 1.2f), ShotOrigin.Wings, ShotOrder.LeftToRight, 2.0f, 2, 0.4f, 0.2f);
            B[9] = Sig(Sky("missile carpet", "top_down_rocket_line_pink", 4, 0.16f, 0.5f, MoveStyle.Sway, 1.8f, 0.8f), ShotOrigin.Muzzle, ShotOrder.LeftToRight, 1f, 2, 0.5f, 0.3f);
            B[10] = Sig(Fly("frost storm", "frost", 8, 0.06f, 2.6f, 0.3f, MoveStyle.Sweep, 3.0f, 1.8f), ShotOrigin.Sides, ShotOrder.OutsideIn, 1.3f, 1, 0.45f, 0.2f);
            B[11] = Sig(Sky("bolt storm", "top_down_lightning_dot_orange", 6, 0.1f, 0.6f, MoveStyle.Sway, 1.6f, 0.9f), ShotOrigin.Muzzle, ShotOrder.CenterOut, 1f, 1, 0.45f, 0.3f, GlowBolt, 1.4f);
            B[12] = Sig(Fly("acid flood", "water", 5, 0.09f, 2.8f, 0.25f, MoveStyle.Sweep, 3.6f, 2.6f), ShotOrigin.Above, ShotOrder.Random, 1.9f, 2, 0.4f);
            B[13] = Sig(Sky("sun lances", "top_down_beam_line_blue", 4, 0.2f, 0.7f, MoveStyle.Orbit, 2.4f, 1.1f, 0.9f), ShotOrigin.Muzzle, ShotOrder.LeftToRight, 1f, 1, 0.45f, 0.25f, GlowLight, 1.6f);
            B[14] = Sig(Sky("plasma columns", "top_down_beam_dot_purple", 3, 0.25f, 0.7f, MoveStyle.Figure8, 2.4f, 1.0f, 0.6f), ShotOrigin.Muzzle, ShotOrder.OutsideIn, 1f, 1, 0.45f, 0.25f, GlowRune, 1.4f);
            B[15] = Sig(Sky("jade bolts", "top_down_lightning_line_green", 4, 0.12f, 0.6f, MoveStyle.Figure8, 2.8f, 1.3f, 0.6f), ShotOrigin.Muzzle, ShotOrder.RightToLeft, 1f, 2, 0.4f, 0.2f, GlowBolt);
            B[16] = Sig(Fly("reaper storm", "dark_magic", 8, 0.06f, 2.6f, 0.4f, MoveStyle.Dash, 3.6f, 1.4f), ShotOrigin.Above, ShotOrder.CenterOut, 1.5f, 2, 0.35f, 0.25f, GlowRune);
            B[17] = Sig(Fly("triple lance", "light", 3, 0.2f, 2.4f, 0.8f, MoveStyle.Sweep, 3.4f, 1.4f, 0f, 0f, 3.6f), ShotOrigin.Wings, ShotOrder.Random, 2.4f, 1, 0.45f, 0.35f, GlowLight, 1.8f);
            B[18] = Sig(Sky("titan shells", "top_down_rocket_circle_red", 6, 0.14f, 0.7f, MoveStyle.Sway, 1.2f, 0.7f), ShotOrigin.Muzzle, ShotOrder.OutsideIn, 1f, 1, 0.45f, 0.35f, GlowFire, 1.6f);
            B[19] = Sig(Sky("abyss columns", "top_down_beam_dot_purple", 4, 0.18f, 0.8f, MoveStyle.Orbit, 1.8f, 1.1f, 1.0f), ShotOrigin.Muzzle, ShotOrder.CenterOut, 1f, 1, 0.45f, 0.3f, GlowRune, 1.6f);
            B[20] = Sig(Sky("golden bolts", "top_down_lightning_dot_orange", 5, 0.12f, 0.6f, MoveStyle.Figure8, 2.6f, 1.3f, 0.8f), ShotOrigin.Muzzle, ShotOrder.OutsideIn, 1f, 2, 0.4f, 0.25f, GlowBolt);
            B[21] = Sig(Fly("plasma tempest", "magic", 9, 0.05f, 2.8f, 0.3f, MoveStyle.Sweep, 3.8f, 2.6f), ShotOrigin.Wings, ShotOrder.LeftToRight, 1.6f, 2, 0.3f, 0.25f, GlowRune);
            B[22] = Sig(Sky("dragon rockets", "top_down_rocket_dot_pink", 6, 0.12f, 0.6f, MoveStyle.Figure8, 3.0f, 1.1f, 0.9f), ShotOrigin.Muzzle, ShotOrder.RightToLeft, 1f, 2, 0.4f, 0.3f, GlowFire, 1.4f);
            B[23] = Sig(Fly("hornet storm", "wind", 9, 0.05f, 2.8f, 0.25f, MoveStyle.Dash, 3.8f, 1.6f), ShotOrigin.Sides, ShotOrder.Random, 2.0f, 2, 0.3f, 0.2f);
            B[24] = Sig(Sky("fortress inferno", "top_down_rocket_circle_red", 8, 0.1f, 0.8f, MoveStyle.Sway, 1.4f, 0.7f), ShotOrigin.Muzzle, ShotOrder.LeftToRight, 1f, 2, 0.6f, 0.4f, GlowFire, 1.8f);
            B[25] = Sig(Sky("void columns", "top_down_beam_circle_green", 5, 0.15f, 0.7f, MoveStyle.Orbit, 2.6f, 1.2f, 0.9f), ShotOrigin.Muzzle, ShotOrder.OutsideIn, 1f, 1, 0.45f, 0.3f, GlowRune, 1.6f);
            B[26] = Sig(Fly("frost crescent", "frost", 9, 0.06f, 3.0f, 0.4f, MoveStyle.Sweep, 3.4f, 1.6f), ShotOrigin.Wings, ShotOrder.RightToLeft, 1.4f, 2, 0.35f, 0.25f);
            B[27] = Sig(Sky("meteor storm", "top_down_rocket_circle_red", 8, 0.08f, 0.8f, MoveStyle.Figure8, 3.2f, 1.2f, 1.0f), ShotOrigin.Muzzle, ShotOrder.CenterOut, 1f, 2, 0.5f, 0.45f, GlowFire, 1.8f);
            B[28] = Sig(Sky("star beams", "top_down_beam_dot_purple", 7, 0.1f, 0.8f, MoveStyle.Orbit, 2.8f, 1.2f, 1.0f), ShotOrigin.Muzzle, ShotOrder.LeftToRight, 1f, 2, 0.6f, 0.45f, GlowRune, 1.8f);
            B[29] = Sig(Sky("final beams", "top_down_beam_line_blue", 6, 0.12f, 0.6f, MoveStyle.Sweep, 3.4f, 1.4f), ShotOrigin.Muzzle, ShotOrder.OutsideIn, 1f, 2, 0.6f, 0.5f, GlowLight, 1.8f);
            B[2] = null; B[4] = null;   // the cruiser and the station keep theirs and only come faster / wider
            return B;
        }
    }
}
