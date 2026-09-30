// BossAttack.cs
// How one boss's shot looks (2026-09-27: "for the rest of the bosses, find the best assets and set them all up"). None of the
// boss packs carry an animation clip, so a boss's attack is built out of VFX: either a shot that flies (the bullet, dressed as
// one of the pack's projectiles) or a strike that comes down from the sky onto the plane (no bullet at all). The cost is the
// same either way - boss k's shot takes what it always took - only the look differs, one per boss number (WaveSpawner.bossAttacks).
using System;
using UnityEngine;

namespace SkySquad
{
    /// <summary>How a boss travels along the front line while he fights.</summary>
    public enum MoveStyle { Sway, Sweep, Dash, Figure8, Orbit }
    /// <summary>Where a boss shots leave from.</summary>
    public enum ShotOrigin { Muzzle, Wings, Above, Sides }
    /// <summary>The order a boss works through the planes he has marked: a sweep across the squad, or in from the middle.</summary>
    public enum ShotOrder { Random, LeftToRight, RightToLeft, CenterOut, OutsideIn }

    [Serializable]
    public class BossAttack
    {
        public string name;                    // what it is ("fireball", "lightning", ...): empty means "not set", the prefab's own stays
        // --- a shot that flies ---
        public Color color = new Color(1f, 0.35f, 0.3f);   // the plain slug's colour (and its trail's)
        public float size = 3.6f;                          // the plain slug's scale
        public GameObject projectile;          // a Casual RPG VFX Projectiles_* riding the bullet in place of the slug; null keeps the slug
        public float projectileScale = 1f;
        public Vector3 projectileTurn = new Vector3(0f, -90f, 0f);   // its rotation on the bullet (+z = the way it flies): the pack's projectiles fly along +x; a ring lies flat and is stood up to face its path
        public GameObject hit;                 // a burst where it lands on the plane; null leaves the sparks
        public float hitScale = 1f;
        public GameObject muzzle;              // a burst at the boss's muzzle as it fires
        public float muzzleScale = 1f;
        // --- or a strike from the sky ---
        public GameObject sky;                 // a strike effect with its pivot on the plane (Zap bolt, Casual RPG top_down_*); set, there is no bullet
        public float skyScale = 1f;
        public float skySpeed = 1f;            // < 1 plays it slower
        public float skyImpact;                // seconds into the effect (at its own pace) when the hit lands: the top-down rockets fall for ~0.8 s first
        public int skyCount = 1;               // strikes per shot, each on a different plane; the shot's cost is split between them (boss 3: 3 bolts, a plane each)
        public float skyStagger = 0.15f;       // seconds between one strike and the next, so each one reads
        public GameObject skyHit;              // a burst on the plane as the strike lands (the bolt alone is gone in a blink)
        public float skyHitScale = 1f;
        public string[] skyHide;               // children of the effect switched off (the Zap's ground scorch: over the sea, under a plane, it hangs in the air)
        // --- how he fires: more than one shot, and never standing still (2026-09-27: "only boss 1 fires a single shell; the rest
        // should move and fire more than one thing, and animate when they fire - he cannot just stay frozen in place") ---
        public int volley = 1;                 // flying shots per attack, each at a different plane; the attack's cost is split between them
        public float volleyStagger = 0.12f;    // seconds between them
        public float volleySpread = 1.2f;      // they leave from across his width, left edge to right edge (world units either side)
        public float windup = 0.35f;           // he charges before he fires: pulls back, noses up, glows; then lunges as it goes
        public GameObject charge;              // the glow at his muzzle while he charges
        public float chargeScale = 1f;
        public float moveRange;                // he weaves across the front line this far either side while he fights (0: holds his lane)
        public float moveSpeed = 1f;           // radians a second of that weave
        // --- 30 bosses (2026-09-30): how he moves and how he fights when hurt ---
        public MoveStyle move = MoveStyle.Sway;
        public float bobRange;                 // he also rises and sinks this much (Figure8, Orbit)
        public float fireEvery;                // seconds between his attacks; 0 = the kind's own
        public float enrageAt = 0.5f;          // below this fraction of his hp he is enraged: 0 = never
        public float enrageFire = 0.7f;        // his fireEvery is multiplied by this once enraged
        public int enrageVolley = 1;           // and he fires / strikes this many more at once
        // --- his signature (2026-09-30: every boss his own way of firing) ---
        public ShotOrigin origin = ShotOrigin.Muzzle;   // Wings: from either tip in turn; Above: falling out of the sky; Sides: across from the screen edges
        public ShotOrder order = ShotOrder.Random;      // the marked planes are hit in this order: a sweep, a collapse to the middle
        public float speedMul = 1f;                     // his shots fly this much faster (a slow orb, a lance)
        public int salvos = 1;                          // the whole volley repeats this many times
        public float salvoGap = 0.45f;                  // seconds between one salvo and the next
        public float shake;                             // camera kick as it goes
        public bool telegraph = true;                   // a ring closes on every plane he has marked while he charges
        public AudioClip sfx;                 // the shot's sound from a pack (a sky strike plays it as it lands)
        public Sfx sound = Sfx.Flak;           // the built-in one when there is no pack clip

        public bool IsSet => !string.IsNullOrEmpty(name);
    }
}
