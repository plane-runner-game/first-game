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

        /// <summary>The 24 kit bosses as prefabs, indexed by boss number - 1 (null for the six pack bosses).</summary>
        static GameObject[] BuildProceduralBosses(Mats M)
        {
            var res = new GameObject[BossCount];
            int i = 0;
            for (int number = 1; number <= BossCount; number++)
            {
                if (IsPackBoss(number)) continue;
                BossKit.Triple(i, out int hull, out int wing, out int crown);
                bool finale = number % 5 == 0;
                float width = finale ? 3.3f : 2.4f + 0.02f * number;
                string id = "ProcBoss" + number.ToString("00");
                var kb = BossKit.Build(id, hull, wing, crown, width);
                var mesh = SaveMesh(kb.mesh);
                float h = Mathf.Repeat(i * 0.618f + 0.08f, 1f);
                var body = Lit(id + "Body", Color.HSVToRGB(h, 0.6f, 0.55f), 0.4f);
                var accent = Lit(id + "Accent", Color.HSVToRGB(Mathf.Repeat(h + 0.45f, 1f), 0.85f, 1f), 0.4f);
                var glow = Unlit(id + "Glow", Color.HSVToRGB(Mathf.Repeat(h + 0.45f, 1f), 0.45f, 1f));
                res[number - 1] = ProcBossPrefab(id, mesh, kb, body, accent, glow, M);
                Debug.Log("[SkySquad] boss " + number + " " + BossNames[number - 1] + ": " + BossKit.HullName(hull) + " / " + BossKit.WingName(wing) + " wings / " + BossKit.CrownName(crown));
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

        /// <summary>Boss N's opening attack (element N-1). The six pack bosses keep the shots they were given on 2026-09-27; the kit bosses each get their own.</summary>
        static BossAttack[] BossAttacks30()
        {
            var old = BossAttacks();   // 0 fireball, 1 vortex, 2 lightning, 3 missiles, 4 plasma, 5 frost, 6 orbital beam
            var A = new BossAttack[BossCount];
            A[0] = old[0]; A[2] = old[1]; A[4] = old[2]; A[9] = old[3]; A[14] = old[4]; A[29] = old[6];
            const string f = "Light/CFXR3 LightGlow A (Loop)";
            A[1] = Fly("gale", "wind", 2, 0.25f, 2.0f, 0.4f, MoveStyle.Sweep, 2.4f, 1.2f, 0f, 3.4f);
            A[3] = Fly("curse", "dark_magic", 1, 0.1f, 1.2f, 0.6f, MoveStyle.Dash, 3.0f, 1f, 0f, 3.6f, 3.4f, 2, 0.7f);
            A[5] = Fly("shuriken storm", "green_shuriken", 4, 0.1f, 1.8f, 0.35f, MoveStyle.Sweep, 3.0f, 1.6f, 0f, 3.2f, 2.5f, 2, 0.7f);
            A[6] = Sky("rocket salvo", "top_down_rocket_dot_pink", 3, 0.2f, 0.6f, MoveStyle.Sway, 1.2f, 0.7f, 0f, 4.2f, 2);
            A[7] = Fly("fire orbs", "fire", 3, 0.15f, 1.6f, 0.45f, MoveStyle.Figure8, 2.0f, 1f, 0.6f, 3.6f, 2.8f, 1, 0.65f);
            A[8] = Fly("twin fangs", "light", 2, 0.25f, 2.2f, 0.4f, MoveStyle.Dash, 3.2f, 1f, 0f, 3.2f, 2.5f, 2, 0.7f);
            A[10] = Fly("ice volley", "frost", 5, 0.09f, 2.0f, 0.4f, MoveStyle.Sway, 1.5f, 1.1f, 0f, 3.8f, 2.5f, 3, 0.7f);
            A[11] = Sky("thunder rain", "top_down_lightning_circle_blue", 4, 0.12f, 0.8f, MoveStyle.Sway, 1.0f, 0.6f, 0f, 4.6f, 2, 0.7f);
            A[12] = Fly("acid stream", "water", 3, 0.12f, 2.4f, 0.3f, MoveStyle.Sweep, 3.4f, 2.0f, 0f, 2.8f, 2.5f, 2, 0.55f);
            A[13] = Sky("solar beams", "top_down_beam_circle_green", 2, 0.3f, 0.9f, MoveStyle.Orbit, 2.0f, 0.9f, 0.8f, 4.2f, 2, 0.7f);
            A[15] = Fly("jade stars", "green_shuriken", 3, 0.14f, 2.0f, 0.4f, MoveStyle.Figure8, 2.6f, 1.1f, 0.5f, 3.6f, 2.8f, 2, 0.7f);
            A[16] = Fly("reaper shards", "dark_magic", 5, 0.1f, 2.0f, 0.5f, MoveStyle.Dash, 3.4f, 1f, 0f, 3.4f, 2.5f, 3, 0.65f);
            A[17] = Fly("lance of light", "light", 1, 0.1f, 1.0f, 1.0f, MoveStyle.Sweep, 3.2f, 1.0f, 0f, 3.0f, 4.2f, 2, 0.7f);
            A[18] = Sky("rust barrage", "top_down_rocket_line_pink", 4, 0.18f, 0.8f, MoveStyle.Sway, 0.8f, 0.6f, 0f, 5.0f, 2, 0.7f);
            A[19] = Fly("abyss gaze", "magic", 6, 0.08f, 1.8f, 0.5f, MoveStyle.Orbit, 1.6f, 1.0f, 0.9f, 3.8f, 2.5f, 2, 0.7f);
            A[20] = Fly("golden rain", "light", 4, 0.12f, 2.4f, 0.4f, MoveStyle.Figure8, 2.4f, 1.2f, 0.7f, 3.4f, 2.6f, 2, 0.7f);
            A[21] = Fly("plasma web", "magic", 6, 0.07f, 2.2f, 0.4f, MoveStyle.Sweep, 3.6f, 2.2f, 0f, 3.0f, 2.5f, 3, 0.65f);
            A[22] = Fly("dragon breath", "fire", 5, 0.12f, 2.0f, 0.5f, MoveStyle.Figure8, 2.8f, 0.9f, 0.8f, 3.6f, 2.8f, 3, 0.7f);
            A[23] = Fly("hornet swarm", "wind", 6, 0.09f, 2.2f, 0.3f, MoveStyle.Dash, 3.6f, 1f, 0f, 2.6f, 2.5f, 3, 0.6f);
            A[24] = Sky("fortress fire", "top_down_rocket_circle_red", 5, 0.12f, 1.0f, MoveStyle.Sway, 1.0f, 0.5f, 0f, 5.0f, 3, 0.7f);
            A[25] = Fly("void fangs", "dark_magic", 7, 0.07f, 2.4f, 0.4f, MoveStyle.Orbit, 2.2f, 1.1f, 0.8f, 3.6f, 2.5f, 3, 0.7f);
            A[26] = Sky("crescent beams", "top_down_beam_line_blue", 4, 0.2f, 0.9f, MoveStyle.Sweep, 3.2f, 1.2f, 0f, 4.2f, 2, 0.7f);
            A[27] = Fly("inferno", "fire", 8, 0.06f, 2.6f, 0.6f, MoveStyle.Figure8, 3.0f, 1.0f, 1.0f, 4.0f, 3.0f, 4, 0.65f);
            A[28] = Sky("star storm", "top_down_lightning_circle_blue", 6, 0.1f, 0.9f, MoveStyle.Orbit, 2.4f, 1.0f, 0.8f, 4.4f, 3, 0.65f);
            for (int i = 0; i < BossCount; i++) if (A[i] != null && A[i].charge == null) A[i].charge = Cfxr(f);
            return A;
        }

        /// <summary>Boss N's enraged attack (element N-1), or null to keep his opening one (faster, and with enrageVolley more at once).</summary>
        static BossAttack[] BossAttacks2()
        {
            var B = new BossAttack[BossCount];
            B[0] = Fly("twin fireballs", "fire", 2, 0.2f, 1.2f, 0.3f, MoveStyle.Sway, 1.4f, 1f);
            B[1] = Sky("thunder strikes", "top_down_lightning_dot_orange", 3, 0.15f, 0.5f, MoveStyle.Sweep, 3.0f, 1.6f);
            B[3] = Fly("skull barrage", "dark_magic", 3, 0.1f, 2.2f, 0.4f, MoveStyle.Dash, 3.4f, 1.2f);
            B[5] = Fly("shuriken blizzard", "green_shuriken", 6, 0.07f, 2.2f, 0.3f, MoveStyle.Sweep, 3.4f, 2.2f);
            B[6] = Sky("rocket carpet", "top_down_rocket_line_pink", 5, 0.15f, 0.5f, MoveStyle.Sway, 1.6f, 0.9f);
            B[7] = Sky("meteor rain", "top_down_rocket_circle_red", 3, 0.2f, 0.5f, MoveStyle.Figure8, 2.4f, 1.2f, 0.7f);
            B[8] = Fly("fang volley", "light", 4, 0.15f, 2.6f, 0.3f, MoveStyle.Dash, 3.6f, 1.2f);
            B[9] = Sky("missile carpet", "top_down_rocket_line_pink", 4, 0.16f, 0.5f, MoveStyle.Sway, 1.8f, 0.8f);
            B[10] = Fly("frost storm", "frost", 8, 0.06f, 2.6f, 0.3f, MoveStyle.Sweep, 3.0f, 1.8f);
            B[11] = Sky("bolt storm", "top_down_lightning_dot_orange", 6, 0.1f, 0.6f, MoveStyle.Sway, 1.6f, 0.9f);
            B[12] = Fly("acid flood", "water", 5, 0.09f, 2.8f, 0.25f, MoveStyle.Sweep, 3.6f, 2.6f);
            B[13] = Sky("sun beams", "top_down_beam_line_blue", 4, 0.2f, 0.7f, MoveStyle.Orbit, 2.4f, 1.1f, 0.9f);
            B[14] = Sky("plasma columns", "top_down_beam_dot_purple", 3, 0.25f, 0.7f, MoveStyle.Figure8, 2.4f, 1.0f, 0.6f);
            B[15] = Sky("jade bolts", "top_down_lightning_line_green", 4, 0.12f, 0.6f, MoveStyle.Figure8, 2.8f, 1.3f, 0.6f);
            B[16] = Fly("reaper storm", "dark_magic", 8, 0.06f, 2.6f, 0.4f, MoveStyle.Dash, 3.6f, 1.4f);
            B[17] = Fly("triple lance", "light", 3, 0.2f, 2.4f, 0.8f, MoveStyle.Sweep, 3.4f, 1.4f, 0f, 0f, 3.4f);
            B[18] = Sky("titan shells", "top_down_rocket_circle_red", 6, 0.14f, 0.7f, MoveStyle.Sway, 1.2f, 0.7f);
            B[19] = Sky("abyss columns", "top_down_beam_dot_purple", 4, 0.18f, 0.8f, MoveStyle.Orbit, 1.8f, 1.1f, 1.0f);
            B[20] = Sky("golden bolts", "top_down_lightning_dot_orange", 5, 0.12f, 0.6f, MoveStyle.Figure8, 2.6f, 1.3f, 0.8f);
            B[21] = Fly("plasma tempest", "magic", 9, 0.05f, 2.8f, 0.3f, MoveStyle.Sweep, 3.8f, 2.6f);
            B[22] = Sky("dragon rockets", "top_down_rocket_dot_pink", 6, 0.12f, 0.6f, MoveStyle.Figure8, 3.0f, 1.1f, 0.9f);
            B[23] = Fly("hornet storm", "wind", 9, 0.05f, 2.8f, 0.25f, MoveStyle.Dash, 3.8f, 1.6f);
            B[24] = Sky("fortress inferno", "top_down_rocket_circle_red", 8, 0.1f, 0.8f, MoveStyle.Sway, 1.4f, 0.7f);
            B[25] = Sky("void columns", "top_down_beam_circle_green", 5, 0.15f, 0.7f, MoveStyle.Orbit, 2.6f, 1.2f, 0.9f);
            B[26] = Fly("frost crescent", "frost", 9, 0.06f, 3.0f, 0.4f, MoveStyle.Sweep, 3.4f, 1.6f);
            B[27] = Sky("meteor storm", "top_down_rocket_circle_red", 8, 0.08f, 0.8f, MoveStyle.Figure8, 3.2f, 1.2f, 1.0f);
            B[28] = Sky("star beams", "top_down_beam_dot_purple", 7, 0.1f, 0.8f, MoveStyle.Orbit, 2.8f, 1.2f, 1.0f);
            B[29] = Sky("final beams", "top_down_beam_line_blue", 6, 0.12f, 0.6f, MoveStyle.Sweep, 3.4f, 1.4f);
            B[2] = null; B[4] = null;   // the cruiser and the station keep theirs and only come faster / wider
            return B;
        }
    }
}
