// SceneBuilder.LavaAttacks.cs (Editor only)
// The lava bosses' ways of fighting (2026-10-02): thirty openings and thirty enraged attacks, all of fire, ash, magma and falling rock, built on the
// same eight shapes as the sea world (Shot, Sky strike, Zone, Sweep, Tornado, Wave, Chain, Portal, Spikes - see BossAttack / BossSpecial) with the
// effects the project already has (Free Quick Effects Vol. 1, Hovl Magic Effects, Casual RPG VFX, Cartoon FX Remaster). The five bosses of a stage go
// from the plainest shape (a volley of fire) to the stage's finale; each stage opens a little faster than the last, and every boss's second
// attack, below half hp, is a different shape that comes quicker and marks more planes.
using System;
using UnityEngine;
using UnityEditor;

namespace SkySquad.EditorTools
{
    public static partial class SceneBuilder
    {
        static readonly Color CMolten = new Color(1f, 0.38f, 0.06f), CWhiteHot = new Color(1f, 0.90f, 0.60f), CCrimson = new Color(0.95f, 0.15f, 0.08f);

        // ---- the shapes, with every number a parameter
        static BossAttack LZone(string name, float wind, MoveStyle mv, float range, float spd, float bob, float fire, int count, float radius, float delay, float hitDelay, GameObject fx, float fxScale, GameObject tell, float tellScale, GameObject hit, float hitScale, float stagger, float shake, string glow = GlowFire)
        {
            return Nw(name, wind, mv, range, spd, bob, fire, glow, a => { a.kind = AttackKind.Zone; a.count = count; a.radius = radius; a.delay = delay; a.hitDelay = hitDelay; a.fx = fx; a.fxScale = fxScale; a.fxTell = tell; a.tellScale = tellScale; a.fxHit = hit; a.hitScale = hitScale; a.volleyStagger = stagger; a.shake = shake; });
        }
        static BossAttack LSweep(string name, float wind, MoveStyle mv, float range, float spd, float bob, float fire, ShotOrder order, GameObject fx, float fxScale, GameObject hit, float hitScale, float duration, float radius, float tick, float shake, float homing = 3f, bool beam = false, Color? beamColor = null, float beamWidth = 0.5f, string glow = GlowFire)
        {
            return Nw(name, wind, mv, range, spd, bob, fire, glow, a =>
            {
                a.kind = AttackKind.Sweep; a.order = order; a.fx = fx; a.fxScale = fxScale; a.fxHit = hit; a.hitScale = hitScale; a.duration = duration; a.radius = radius; a.tick = tick; a.shake = shake; a.homing = homing; a.telegraph = order == ShotOrder.Random; a.sound = Sfx.Rocket;
                if (beam) { a.beamMat = BeamMat(); a.beamColor = beamColor ?? CMolten; a.beamWidth = beamWidth; a.sound = Sfx.Laser; }
            });
        }
        static BossAttack LSpikes(string name, float wind, MoveStyle mv, float range, float spd, float bob, float fire, int count, GameObject fx, float fxScale, float radius, int steps, float duration, float stagger, GameObject hit, float hitScale, string glow = GlowFire)
        {
            return Nw(name, wind, mv, range, spd, bob, fire, glow, a => { a.kind = AttackKind.Spikes; a.count = count; a.fx = fx; a.fxScale = fxScale; a.radius = radius; a.steps = steps; a.duration = duration; a.volleyStagger = stagger; a.fxHit = hit; a.hitScale = hitScale; });
        }
        static BossAttack LTornado(string name, float wind, MoveStyle mv, float range, float spd, float bob, float fire, int count, GameObject fx, float fxScale, float radius, float duration, float homing, float stagger, GameObject hit, float hitScale, float shake, string glow = GlowFire)
        {
            return Nw(name, wind, mv, range, spd, bob, fire, glow, a => { a.kind = AttackKind.Tornado; a.count = count; a.fx = fx; a.fxScale = fxScale; a.radius = radius; a.duration = duration; a.homing = homing; a.volleyStagger = stagger; a.fxHit = hit; a.hitScale = hitScale; a.shake = shake; });
        }
        static BossAttack LWave(string name, float wind, MoveStyle mv, float range, float spd, float bob, float fire, float delay, float duration, float gap, GameObject fx, float fxScale, GameObject tell, float tellScale, GameObject hit, float hitScale, float shake, string glow = GlowFire)
        {
            return Nw(name, wind, mv, range, spd, bob, fire, glow, a => { a.kind = AttackKind.Wave; a.delay = delay; a.duration = duration; a.gap = gap; a.fx = fx; a.fxScale = fxScale; a.fxTell = tell; a.tellScale = tellScale; a.fxHit = hit; a.hitScale = hitScale; a.shake = shake; a.telegraph = false; });
        }
        static BossAttack LChain(string name, float wind, MoveStyle mv, float range, float spd, float bob, float fire, int links, GameObject fx, float fxScale, GameObject hit, float hitScale, float stagger, Color col, float width, string glow = GlowFire)
        {
            return Nw(name, wind, mv, range, spd, bob, fire, glow, a => { a.kind = AttackKind.Chain; a.count = links; a.fx = fx; a.fxScale = fxScale; a.fxHit = hit; a.hitScale = hitScale; a.volleyStagger = stagger; a.beamMat = BeamMat(); a.beamColor = col; a.beamWidth = width; a.telegraph = false; });
        }
        static BossAttack LPortal(string name, float wind, MoveStyle mv, float range, float spd, float bob, float fire, int count, GameObject portal, float portalScale, float delay, float stagger, string proj, float projScale, float speedMul, string glow = GlowFire)
        {
            return Nw(name, wind, mv, range, spd, bob, fire, glow, a =>
            {
                a.kind = AttackKind.Portal; a.count = count; a.delay = delay; a.fx = portal; a.fxScale = portalScale; a.volleyStagger = stagger;
                a.projectile = Vfx("Range_attack/Projectiles_" + proj); a.projectileScale = projScale; a.hit = Cfxr("Fire/CFXR3 Hit Fire B (Air)"); a.muzzle = Vfx("Range_attack/Hit_" + proj); a.speedMul = speedMul; a.sound = Sfx.Rocket;
            });
        }

        // ---- the effects the lava attacks share
        static GameObject FxBoom1() { return Gq("Explosion_01"); }
        static GameObject FxBoom2() { return Gq("Explosion_02"); }
        static GameObject FxFlames() { return Gq("Flames_01"); }
        static GameObject FxJet1() { return Gq("Flamethrower_01"); }
        static GameObject FxJet2() { return Gq("Flamethrower_02"); }
        static GameObject FxGeyser() { return Vfx("Fire/Fire_explosion_earth"); }
        static GameObject FxHit() { return Hv("Hits and explosions/Explosion"); }

        static BossAttack[] LavaAttacks()
        {
            var A = new BossAttack[BossCount];
            // ======== stage 1: EMBER SHORE - fire you can read
            A[0] = Sig(Fly("ember darts", "fire", 3, 0.18f, 1.6f, 0.5f, MoveStyle.Sway, 1.0f, 0.6f, 0f, 4.4f, 2.4f), ShotOrigin.Muzzle, ShotOrder.LeftToRight, 1f, 1, 0.45f, 0.15f, "Fire/CFXR Fire");
            A[1] = Sig(Fly("fire lances", "fire", 2, 0.25f, 2.2f, 0.5f, MoveStyle.Dash, 3.0f, 1f, 0f, 4.4f, 2.8f), ShotOrigin.Wings, ShotOrder.Random, 1.6f, 1, 0.45f, 0.2f, "Fire/CFXR Fire");
            A[2] = LZone("maw bombs", 0.5f, MoveStyle.Sway, 0.6f, 0.6f, 0f, 4.4f, 2, 1.8f, 1.0f, 0.15f, FxGeyser(), 1.5f, TellOrange(), 4.5f, FxBoom2(), 4.5f, 0.35f, 0.25f);
            A[3] = Sky("ember rain", "top_down_rocket_circle_red", 3, 0.2f, 0.5f, MoveStyle.Figure8, 1.8f, 0.9f, 0.3f, 4.6f);
            A[4] = LWave("forge wall", 0.8f, MoveStyle.Sway, 0.8f, 0.5f, 0f, 5.0f, 1.5f, 0f, 1.3f, Hv("AoE effects/Red energy explosion"), 1.4f, Hv("Magic circles/Healing circle"), 0.35f, null, 1f, 0.35f);
            // ======== stage 2: ASH PLAINS - ash, hornets, jets
            A[5] = Sig(Fly("ash stingers", "dark_magic", 5, 0.09f, 2.4f, 0.4f, MoveStyle.Dash, 3.2f, 1f, 0f, 3.8f, 2.2f), ShotOrigin.Above, ShotOrder.LeftToRight, 1.2f, 1, 0.45f, 0.1f, "Fire/CFXR Fire");
            A[6] = LZone("ash clouds", 0.6f, MoveStyle.Sway, 1.6f, 0.8f, 0f, 4.4f, 3, 1.9f, 1.0f, 0.15f, Hv("AoE effects/Smoke AOE explosion"), 1.0f, TellOrange(), 3.5f, FxBoom1(), 3.5f, 0.3f, 0.3f);
            A[7] = LSweep("flame jet", 0.5f, MoveStyle.Figure8, 2.0f, 1.0f, 0.5f, 4.2f, ShotOrder.RightToLeft, FxJet2(), 2.8f, null, 1f, 2.0f, 1.3f, 0.2f, 0.2f);
            A[8] = LSpikes("magma rows", 0.6f, MoveStyle.Dash, 3.2f, 1f, 0f, 4.0f, 2, FxGeyser(), 1.3f, 1.3f, 7, 1.4f, 0.3f, FxBoom1(), 3f);
            A[9] = LZone("boiling shells", 0.6f, MoveStyle.Sway, 1.8f, 0.7f, 0f, 4.6f, 4, 1.7f, 0.9f, 0.15f, FxFlames(), 2.4f, TellOrange(), 4f, FxHit(), 2f, 0.2f, 0.3f);
            // ======== stage 3: OBSIDIAN GATE - meteors, chains, portals
            A[10] = LZone("meteor shower", 0.6f, MoveStyle.Figure8, 1.6f, 0.8f, 0.4f, 4.4f, 3, 2.0f, 1.2f, 0.5f, Gq("MeteorRain_01"), 1.5f, TellRune(), 1.3f, FxBoom2(), 5f, 0.4f, 0.3f);
            A[11] = LChain("ember chain", 0.5f, MoveStyle.Sway, 1.4f, 0.8f, 0f, 3.8f, 5, Gq("Impact_01"), 3f, FxHit(), 2.5f, 0.14f, CMolten, 0.3f);
            A[12] = LSweep("red cleave", 1.0f, MoveStyle.Sweep, 3.0f, 0.9f, 0f, 4.4f, ShotOrder.LeftToRight, null, 1f, FxHit(), 3.5f, 2.4f, 1.2f, 0.25f, 0.3f, 3f, true, CCrimson, 0.85f);
            A[13] = LPortal("slag gates", 0.6f, MoveStyle.Dash, 3.0f, 1f, 0f, 3.8f, 3, Hv("Portals/Portal red"), 2.8f, 0.9f, 0.3f, "fire", 3f, 1.3f);
            A[14] = LWave("grinding wave", 0.9f, MoveStyle.Sway, 1.0f, 0.5f, 0f, 5.0f, 1.4f, 1.0f, 1.2f, Gq("Shockwave_01"), 5f, Hv("Magic circles/Healing circle"), 0.3f, FxBoom2(), 5f, 0.45f);
            // ======== stage 4: MAGMA FALLS - rays, dives, geysers
            A[15] = LSweep("seraph rays", 0.7f, MoveStyle.Orbit, 3.0f, 0.9f, 0.8f, 4.4f, ShotOrder.Random, null, 1f, FxHit(), 4f, 2.8f, 1.2f, 0.25f, 0.3f, 2.2f, true, CWhiteHot, 0.9f);
            A[16] = Sky("crater dives", "top_down_rocket_circle_red", 4, 0.16f, 0.5f, MoveStyle.Dash, 3.4f, 1f, 0f, 4.0f);
            A[17] = LSpikes("magma geysers", 0.5f, MoveStyle.Figure8, 2.6f, 1.1f, 0.5f, 4.0f, 3, FxGeyser(), 1.5f, 1.2f, 8, 1.5f, 0.25f, FxBoom1(), 3f);
            A[18] = LSweep("mantis claws", 0.6f, MoveStyle.Sweep, 3.0f, 1.2f, 0f, 4.2f, ShotOrder.CenterOut, FxJet1(), 2.8f, FxFlames(), 1.1f, 2.0f, 1.2f, 0.18f, 0.3f);
            A[19] = LZone("mimic maw", 0.5f, MoveStyle.Dash, 3.4f, 1f, 0f, 3.8f, 4, 2.0f, 0.8f, 0.15f, Hv("AoE effects/Ground AOE explosion"), 1.1f, TellOrange(), 4f, FxBoom1(), 4f, 0.22f, 0.3f);
            // ======== stage 5: VOLCANO HEART - walkers, lances, falling stone
            A[20] = LTornado("fire walkers", 0.6f, MoveStyle.Sway, 0.8f, 0.5f, 0f, 5.2f, 2, FxFlames(), 3f, 1.6f, 2.6f, 2.4f, 0.8f, null, 1f, 0.2f);
            A[21] = Sig(Fly("brimstone", "fire", 1, 0.2f, 0.5f, 0.7f, MoveStyle.Sway, 1.4f, 0.8f, 0f, 4.8f, 4.5f), ShotOrigin.Muzzle, ShotOrder.Random, 2.6f, 4, 0.35f, 0.25f, "Fire/CFXR Fire", 1.4f);
            A[22] = Sky("falling obelisks", "top_down_stone_circle", 3, 0.22f, 0.7f, MoveStyle.Sway, 1.2f, 0.7f, 0f, 4.8f);
            A[23] = LPortal("scarab gates", 0.5f, MoveStyle.Sweep, 3.4f, 1.8f, 0f, 3.4f, 4, Hv("Portals/Portal yellow"), 2.6f, 0.7f, 0.18f, "fire", 3f, 1.6f);
            A[24] = LZone("tower rain", 1.0f, MoveStyle.Sway, 1.0f, 0.5f, 0f, 5.4f, 5, 1.5f, 1.2f, 0.15f, FxBoom2(), 5f, TellOrange(), 3.5f, FxHit(), 2f, 0.18f, 0.4f);
            // ======== stage 6: INFERNO THRONE - the finale
            A[25] = LSweep("kestrel beam", 0.6f, MoveStyle.Sweep, 3.4f, 1.2f, 0f, 3.8f, ShotOrder.LeftToRight, null, 1f, FxHit(), 3f, 1.8f, 1.1f, 0.16f, 0.3f, 3f, true, CMolten, 0.6f);
            A[26] = LWave("sphinx wall", 1.0f, MoveStyle.Sweep, 3.0f, 0.8f, 0f, 4.4f, 1.8f, 1.6f, 1.0f, Hv("AoE effects/Red energy explosion"), 1.4f, Hv("Magic circles/Healing circle"), 0.3f, FxBoom1(), 5f, 0.5f);
            A[27] = Sky("furnace sparks", "top_down_lightning_dot_orange", 5, 0.12f, 0.5f, MoveStyle.Figure8, 2.6f, 1.1f, 0.5f, 3.8f);
            A[28] = LZone("ash rebirth", 0.9f, MoveStyle.Orbit, 2.4f, 1f, 0.8f, 4.8f, 3, 2.0f, 1.4f, 0.15f, Hv("AoE effects/Meteors AOE"), 1.0f, Gq("Implosion_01"), 3.2f, FxBoom2(), 5f, 0.4f, 0.4f);
            A[29] = LZone("king's meteors", 1.0f, MoveStyle.Sway, 1.6f, 0.7f, 0f, 4.6f, 4, 2.2f, 1.4f, 0.6f, Gq("MeteorRain_02"), 1.6f, TellRune(), 1.5f, FxBoom2(), 6f, 0.3f, 0.5f);
            return A;
        }

        static BossAttack[] LavaAttacks2()
        {
            var B = new BossAttack[BossCount];
            // ======== stage 1
            B[0] = Sig(Fly("cinder salvo", "fire", 4, 0.12f, 2.4f, 0.4f, MoveStyle.Sway, 1.4f, 1.0f, 0f, 3.4f, 2.4f), ShotOrigin.Wings, ShotOrder.CenterOut, 1.2f, 2, 0.5f, 0.2f, "Fire/CFXR Fire");
            B[1] = Sig(Fly("lance storm", "fire", 3, 0.15f, 3.0f, 0.3f, MoveStyle.Dash, 3.6f, 1.2f, 0f, 3.0f, 2.8f), ShotOrigin.Sides, ShotOrder.Random, 1.8f, 1, 0.45f, 0.2f, "Fire/CFXR Fire");
            B[2] = LZone("maw rain", 0.4f, MoveStyle.Sway, 1.4f, 0.9f, 0f, 3.4f, 5, 1.7f, 0.8f, 0.15f, FxGeyser(), 1.5f, TellOrange(), 4f, FxBoom2(), 4.5f, 0.15f, 0.3f);
            B[3] = Sky("ember storm", "top_down_rocket_circle_red", 5, 0.12f, 0.4f, MoveStyle.Figure8, 2.4f, 1.2f, 0.5f, 3.4f);
            B[4] = LSweep("forge jets", 0.4f, MoveStyle.Sway, 1.4f, 1.0f, 0f, 3.4f, ShotOrder.LeftToRight, FxJet1(), 2.8f, FxFlames(), 1.1f, 2.0f, 1.4f, 0.2f, 0.3f);
            // ======== stage 2
            B[5] = Sig(Fly("hornet swarm", "dark_magic", 7, 0.07f, 3.0f, 0.3f, MoveStyle.Dash, 3.6f, 1.4f, 0f, 3.2f, 2.2f), ShotOrigin.Above, ShotOrder.CenterOut, 1.4f, 2, 0.5f, 0.15f, "Fire/CFXR Fire");
            B[6] = LZone("ash storm", 0.4f, MoveStyle.Dash, 3.4f, 1.3f, 0f, 3.2f, 6, 1.8f, 0.8f, 0.15f, Hv("AoE effects/Smoke AOE explosion"), 1.0f, TellOrange(), 3.5f, FxBoom1(), 3.5f, 0.14f, 0.3f);
            B[7] = LSweep("dragon breath", 0.5f, MoveStyle.Figure8, 2.8f, 0.9f, 0.8f, 3.6f, ShotOrder.OutsideIn, FxJet2(), 3f, FxFlames(), 1.2f, 2.2f, 1.3f, 0.2f, 0.3f);
            B[8] = LSpikes("fang rows", 0.4f, MoveStyle.Sweep, 3.4f, 1.6f, 0f, 3.2f, 4, FxGeyser(), 1.3f, 1.2f, 7, 1.2f, 0.18f, FxBoom1(), 3f);
            B[9] = LWave("boil over", 0.6f, MoveStyle.Sway, 1.8f, 0.9f, 0f, 3.6f, 1.3f, 1.0f, 1.2f, Gq("Shockwave_01"), 5f, Hv("Magic circles/Healing circle"), 0.35f, FxBoom2(), 5f, 0.4f);
            // ======== stage 3
            B[10] = LZone("meteor storm", 0.5f, MoveStyle.Figure8, 3.0f, 1.2f, 0.8f, 3.4f, 5, 1.8f, 1.0f, 0.4f, Gq("MeteorRain_02"), 1.4f, TellRune(), 1.3f, FxBoom2(), 5f, 0.16f, 0.4f);
            B[11] = LChain("slag chain", 0.4f, MoveStyle.Figure8, 2.4f, 1.2f, 0.5f, 3.2f, 7, Gq("Lightning_01"), 4f, FxHit(), 2.5f, 0.1f, CWhiteHot, 0.28f);
            B[12] = LSweep("red crescents", 0.6f, MoveStyle.Orbit, 3.0f, 1.2f, 0.8f, 3.4f, ShotOrder.OutsideIn, null, 1f, FxHit(), 3f, 2.0f, 1.1f, 0.16f, 0.3f, 3f, true, CCrimson, 0.65f);
            B[13] = LPortal("slag barrage", 0.3f, MoveStyle.Sweep, 3.6f, 2.2f, 0f, 3.0f, 5, Hv("Portals/Portal red"), 2.6f, 0.6f, 0.12f, "fire", 3.2f, 1.7f);
            B[14] = LTornado("gear flames", 0.5f, MoveStyle.Sway, 1.2f, 0.8f, 0f, 3.8f, 3, FxFlames(), 2.6f, 1.5f, 2.8f, 2.2f, 0.6f, FxBoom2(), 4f, 0.3f);
            // ======== stage 4
            B[15] = LZone("sun fall", 0.7f, MoveStyle.Orbit, 2.4f, 1.0f, 0.8f, 3.8f, 3, 2.4f, 1.5f, 0.15f, Hv("AoE effects/Red energy explosion"), 0.9f, Gq("Implosion_01"), 3f, FxBoom2(), 5f, 0.4f, 0.4f);
            B[16] = Sky("hawk storm", "top_down_rocket_circle_red", 6, 0.1f, 0.4f, MoveStyle.Dash, 3.6f, 1.3f, 0f, 3.2f);
            B[17] = LSpikes("geyser field", 0.4f, MoveStyle.Figure8, 3.0f, 1.3f, 0.6f, 3.2f, 5, FxGeyser(), 1.5f, 1.2f, 6, 1.1f, 0.14f, FxBoom1(), 3f);
            B[18] = LSweep("mantis shears", 0.5f, MoveStyle.Sweep, 3.4f, 1.6f, 0f, 3.2f, ShotOrder.OutsideIn, FxJet2(), 3f, FxFlames(), 1.2f, 1.8f, 1.2f, 0.16f, 0.3f);
            B[19] = LWave("devour", 0.8f, MoveStyle.Dash, 3.0f, 1f, 0f, 3.6f, 1.2f, 0.9f, 1.0f, FxBoom2(), 6f, Hv("Magic circles/Healing circle"), 0.3f, Hv("AoE effects/Ground AOE explosion"), 1.2f, 0.5f);
            // ======== stage 5
            B[20] = LTornado("wraith storm", 0.4f, MoveStyle.Sweep, 3.4f, 1.8f, 0f, 3.2f, 4, FxFlames(), 3f, 1.5f, 2.0f, 3.4f, 0.4f, FxBoom2(), 4f, 0.3f);
            B[21] = Sig(Fly("brimstone barrage", "fire", 3, 0.1f, 2.4f, 0.4f, MoveStyle.Dash, 3.0f, 1.3f, 0f, 3.6f, 4.0f), ShotOrigin.Wings, ShotOrder.CenterOut, 2.8f, 3, 0.4f, 0.3f, "Fire/CFXR Fire", 1.4f);
            B[22] = Sky("obelisk rain", "top_down_stone_dot", 6, 0.1f, 0.5f, MoveStyle.Figure8, 2.6f, 1.1f, 0.5f, 3.4f);
            B[23] = LPortal("scarab swarm", 0.3f, MoveStyle.Orbit, 2.8f, 1.2f, 0.9f, 3.0f, 6, Hv("Portals/Portal yellow"), 2.4f, 0.6f, 0.11f, "fire", 3f, 1.8f);
            B[24] = LZone("tower collapse", 0.9f, MoveStyle.Orbit, 1.6f, 1.0f, 0.9f, 4.2f, 1, 3.2f, 1.9f, 0.15f, Hv("AoE effects/Smoke AOE explosion"), 1.4f, Gq("Implosion_01"), 4.5f, FxBoom1(), 7f, 0.5f, 0.5f);
            // ======== stage 6
            B[25] = LSweep("kestrel crescents", 0.5f, MoveStyle.Orbit, 3.2f, 1.3f, 0.8f, 3.2f, ShotOrder.OutsideIn, null, 1f, FxHit(), 3f, 2.0f, 1.1f, 0.15f, 0.3f, 3f, true, CMolten, 0.65f);
            B[26] = LWave("sphinx walls", 0.8f, MoveStyle.Figure8, 3.2f, 1.2f, 0.6f, 3.4f, 1.4f, 1.2f, 1.0f, Hv("AoE effects/Red energy explosion"), 1.4f, Hv("Magic circles/Healing circle"), 0.3f, FxBoom1(), 5f, 0.5f);
            B[27] = Sky("furnace storm", "top_down_lightning_dot_orange", 7, 0.1f, 0.4f, MoveStyle.Sweep, 3.4f, 1.4f, 0f, 3.0f);
            B[28] = LZone("ash cinders", 0.5f, MoveStyle.Figure8, 3.2f, 1.2f, 0.9f, 3.4f, 6, 1.8f, 0.9f, 0.15f, FxFlames(), 2.4f, TellOrange(), 4f, FxBoom1(), 4f, 0.13f, 0.4f);
            B[29] = LSweep("king's wrath", 0.6f, MoveStyle.Sweep, 3.4f, 1.4f, 0f, 3.2f, ShotOrder.OutsideIn, FxJet2(), 3.2f, FxBoom1(), 3f, 2.8f, 1.3f, 0.14f, 0.4f);
            return B;
        }
    }
}
