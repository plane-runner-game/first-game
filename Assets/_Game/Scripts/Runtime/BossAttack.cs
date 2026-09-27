// BossAttack.cs
// How one boss's shot looks (2026-09-27: "for the rest of the bosses, find the best assets and set them all up"). None of the
// boss packs carry an animation clip, so a boss's attack is built out of VFX: either a shot that flies (the bullet, dressed as
// one of the pack's projectiles) or a strike that comes down from the sky onto the plane (no bullet at all). The cost is the
// same either way - boss k's shot takes what it always took - only the look differs, one per boss number (WaveSpawner.bossAttacks).
using System;
using UnityEngine;

namespace SkySquad
{
    [Serializable]
    public class BossAttack
    {
        public string name;                    // what it is ("fireball", "lightning", ...): empty means "not set", the prefab's own stays
        // --- a shot that flies ---
        public Color color = new Color(1f, 0.35f, 0.3f);   // the plain slug's colour (and its trail's)
        public float size = 3.6f;                          // the plain slug's scale
        public GameObject projectile;          // a Casual RPG VFX Projectiles_* riding the bullet in place of the slug; null keeps the slug
        public float projectileScale = 1f;
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
        public AudioClip sfx;                  // the shot's sound from a pack (a sky strike plays it as it lands)
        public Sfx sound = Sfx.Flak;           // the built-in one when there is no pack clip

        public bool IsSet => !string.IsNullOrEmpty(name);
    }
}
