// Enemy.cs
// One enemy plane in the HIGH band. Fighters are kamikazes: each picks a lane at spawn and flies straight
// down it at its own speed, weaving a little, and over the last few units dives to the squad's altitude -
// one that reaches you in your lane blows up and takes a plane; stay out of its lane and it flies past.
// They never change lanes. Only a boss stops: he parks
// on the front line and shoots on his own clock, every landed shot costing a plane.
using UnityEngine;

namespace SkySquad
{
    public class Enemy : MonoBehaviour
    {
        public Transform model;
        public Transform propeller;
        public Transform[] propellers;    // the boss: four engines
        public Renderer bodyRenderer;
        public Renderer flashRenderer;    // muzzle flash quad, enabled briefly when a boss shoots
        public TMPro.TextMeshPro hpLabel;
        public GameObject hpBarRoot;      // boss: the health bar over his head, his hp number above it (2026-09-18)
        public Transform hpBarFill;       // scaled on x from a left pivot, as BossController does for the zeppelin
        public float hpBarWidth = 3.6f;
        public TrailRenderer trail;       // fighter: streams smoke on its strike run

        public EnemyKindDef Kind { get; private set; }
        public float Hp { get; private set; }
        public float MaxHp { get; private set; }
        public bool Wide { get; private set; }         // boss: any lane hits him
        public bool Dead { get; private set; }
        public bool Parked { get; private set; }       // boss: settled on the front line, shooting
        public bool Held { get; private set; }         // fighter: waiting behind a living boss
        public float Pending;                          // damage already in the air toward this plane
        public float ShotDamage { get; private set; }  // planes a boss shot (or a ram) takes
        public int HordeIndex = 1;
        public float HoldOffset;                       // how far behind the boss this one waits
        public float SpeedMult = 1f;                   // fighter: its own pace, faster or slower than the swarm's base speed
        public float X, Z, Alt;
        public float HalfWidth => Kind.halfWidth;

        static MaterialPropertyBlock hitBlock;
        static readonly int BaseColor = Shader.PropertyToID("_BaseColor");
        float baseX, fireT, hitT, muzzleT, parkT, seed, shrink = 1f, sPitch, sBank, strikeRoll, aimX, aimAlt;   // aimX/aimAlt: where the run is steering, chasing the plane at a real turn rate
        bool hitShown, wasParked, crossed, burning;             // crossed: it has passed the green line
        int strikeSlot = -1;                           // the squad plane it locked when it crossed, or -1
        public int StrikeStyle;                        // 0..4, picked by the spawner: which figure it flies on its strike run
        Vector3 strikeStart, prevPos;                  // (X, Alt, Z) where the strike began; last frame's position for the flight direction
        public const int StrikeStyles = 4;             // 0, 1 dive; 2 pop-up; 3 wing-over
        public bool Striking => strikeSlot >= 0;       // on its strike run: bullets pass through it, it cannot be stopped
        public float StrikeT { get; private set; }     // seconds since it crossed the line (ThreatMarkers pops its reticle on that)
        public float Pitch => sPitch;                  // the model's current attitude (degrees, + = nose down / right wing down): the wreck starts from it (FXManager.PlaneWreck)
        public float Bank => sBank;

        Color tint = Color.white; bool tinted;
        /// <summary>A body colour multiplied over the model's texture (the Sparrow bosses: one colour per boss, WaveSpawner.bossColors, 2026-09-18). HDR values brighten a dark texture.</summary>
        public void SetTint(Color c) { tint = c; tinted = true; ApplyBodyColor(hitShown); }
        /// <summary>Back to the plain (or tinted) body colour. The killing hit leaves the HDR-white flash on, and nothing would
        /// ever turn it off once the model falls as a wreck (Apply no longer runs on a dead enemy).</summary>
        public void ClearHitFlash() { hitT = 0f; hitShown = false; ApplyBodyColor(false); }
        void ApplyBodyColor(bool hit)
        {
            if (bodyRenderer == null) return;
            if (!hit && !tinted) { bodyRenderer.SetPropertyBlock(null); return; }
            if (hitBlock == null) hitBlock = new MaterialPropertyBlock();
            hitBlock.SetColor(BaseColor, hit ? new Color(3f, 3f, 3f) : tint);   // HDR white: the textured OH-1 / Sparrow (2026-09-18) must still flash, the base colour multiplies the texture
            bodyRenderer.SetPropertyBlock(hitBlock);
        }

        public void Init(EnemyKindDef kind, float hp, bool wide, float x, float z, float alt, float shotDamage)
        {
            Kind = kind; MaxHp = Hp = hp; Wide = wide; baseX = X = x; Z = z; Alt = alt; ShotDamage = shotDamage;
            Dead = Parked = Held = wasParked = crossed = burning = false; strikeSlot = -1; shrink = 1f; sPitch = -3f; sBank = strikeRoll = 0f;
            hitT = muzzleT = parkT = 0f; Pending = 0f; seed = Random.value * 10f;
            tinted = false; hitShown = false; ApplyBodyColor(false);   // a pooled body starts plain (a boss gets its tint right after Init)
            prevPos = new Vector3(x, 1f + alt, z);
            ApplyModelScale(1f);
            if (flashRenderer != null) flashRenderer.enabled = false;
            if (trail != null) { trail.emitting = false; trail.Clear(); }
            if (hpBarRoot != null) { hpBarRoot.SetActive(Kind.miniBoss); hpBarRoot.transform.localScale = Vector3.one; }   // a boss wears a health bar, his number above it (2026-09-18)
            if (hpLabel != null) { hpLabel.text = Mathf.CeilToInt(Hp).ToString(); hpLabel.gameObject.SetActive(Kind.miniBoss); }   // a fighter's hp shows only once it has been hit
            SetHpBar();
            Apply();
        }

        /// <summary>One frame of flight. limitZ is the front line for a boss, the hold line behind a living
        /// boss for a fighter of the next horde, or -infinity for a free fighter. WaveSpawner calls this.</summary>
        public void Tick(float dt, float limitZ)
        {
            if (Dead) return;
            var gm = GameManager.I;
            var cfg = gm.config;
            var sq = gm.squad;
            float t = Time.time;
            hitT = Mathf.Max(0f, hitT - dt);
            muzzleT = Mathf.Max(0f, muzzleT - dt);
            if (Kind.miniBoss)
            {   // brakes into the front line and opens fire the moment he settles, then every fireEvery
                float gap = Z - limitZ;
                float brake = Mathf.Max(0.3f, Mathf.Clamp01(gap / 3f));
                Z = Mathf.Max(Z - (gm.ScrollSpeed + Kind.approachSpeed) * brake * dt, limitZ);
                Parked = Z <= limitZ + 0.02f;
                parkT = Parked ? parkT + dt : 0f;
                if (Parked && !wasParked) fireT = 0f;
                wasParked = Parked;
                if (Parked) { fireT -= dt; if (fireT <= 0f) { Shoot(); fireT = Kind.fireEvery; } }
            }
            else
            {   // kamikaze: straight down its own lane (baseX never changes), a small weave, then the strike
                // the opening of an attempt is flown at swarmOpeningApproach (the old, slow pace); after swarmOpeningSeconds the swarm eases up to the kind's full approachSpeed
                float ramp = cfg.swarmOpeningBlend > 0f ? Mathf.Clamp01((gm.LevelTime - cfg.swarmOpeningSeconds) / cfg.swarmOpeningBlend) : (gm.LevelTime >= cfg.swarmOpeningSeconds ? 1f : 0f);
                float approach = Mathf.Lerp(cfg.swarmOpeningApproach, Kind.approachSpeed, ramp);
                float net = (gm.ScrollSpeed + approach) * SpeedMult;   // each one at its own speed
                Z = Mathf.Max(Z - net * dt, limitZ);
                Held = Z <= limitZ + 0.02f;
                if (!crossed && !Held && Z < cfg.diveZ + sq.Z && sq.VisibleCount > 0)   // the strike line rides diveZ ahead of the squad, which flies forward when it dives (SquadController.Z)
                {   // crossing the line: it commits. Locks the squad plane nearest to its lane - every fighter that crosses strikes one.
                    crossed = true;
                    float best = float.MaxValue;
                    for (int i = 0; i < sq.VisibleCount; i++)
                    {
                        float d = Mathf.Abs(sq.SlotWorld(i).x - X);
                        if (d < best) { best = d; strikeSlot = i; }
                    }
                    Vector3 lock0 = sq.SlotWorld(strikeSlot);
                    strikeStart = new Vector3(X, Alt, Z);   // where the run begins: X/Alt curve from here onto the plane as Z closes
                    aimX = lock0.x; aimAlt = lock0.y - 1f;
                    StrikeT = 0f;
                    if (trail != null) { trail.Clear(); trail.emitting = true; }   // engine to the wall: it streams smoke all the way in
                }
                if (strikeSlot >= 0 && sq.VisibleCount > 0)
                {   // THE STRIKE RUN - a committed dive, not an aerobatic figure. Z keeps flowing (no hitch at the line) and the
                    // fighter accelerates all the way in (strikeAccel). Its aim point chases the plane it locked, but only as fast
                    // as a real turn allows (strikeTurnRate), so it curves onto the plane rather than sliding sideways with it;
                    // X and altitude ease from where it crossed onto that aim point. Two of four fly a variation: a pop-up (a
                    // quick climb, then a steeper dive) or a wing-over (rolls over the top into the dive). The nose follows the
                    // flight path and the wings bank into the turn (Apply). Bullets cannot touch it on the run (Striking).
                    if (strikeSlot >= sq.VisibleCount) strikeSlot = sq.VisibleCount - 1;   // its plane is already gone: take the last slot left
                    StrikeT += dt;
                    Vector3 tp = sq.SlotWorld(strikeSlot);
                    aimX = Mathf.MoveTowards(aimX, tp.x, cfg.strikeTurnRate * dt);
                    aimAlt = Mathf.MoveTowards(aimAlt, tp.y - 1f, cfg.strikeTurnRate * 1.2f * dt);
                    float span = Mathf.Max(0.5f, strikeStart.z - tp.z);
                    float p = Mathf.Clamp01(1f - (Z - tp.z) / span);            // 0 at the line .. 1 on the plane
                    float e = p * p * (3f - 2f * p);                                // smoothstep: rolls into the turn, straightens onto the plane
                    float lift; strikeRoll = 0f;
                    switch (StrikeStyle)
                    {
                        case 2:   // POP-UP: a quick climb right after committing, then the steeper dive
                            lift = Mathf.Sin(Mathf.Pow(p, 0.6f) * Mathf.PI) * cfg.strikeLift; break;
                        case 3:   // WING-OVER: rolls over the top into the dive, wings level again by impact
                            strikeRoll = Mathf.Sin(Mathf.Clamp01(p / 0.85f) * Mathf.PI) * 150f * (seed < 5f ? 1f : -1f);
                            lift = Mathf.Sin(p * Mathf.PI) * cfg.strikeLift * 0.45f; break;
                        default:  // DIVE: straight in, the merest float over the top as it noses down
                            lift = Mathf.Sin(p * Mathf.PI) * cfg.strikeLift * 0.15f; break;
                    }
                    baseX = X = Mathf.Lerp(strikeStart.x, aimX, e);
                    Alt = Mathf.Lerp(strikeStart.y, aimAlt, e) + lift;
                    float sc = p * p * p * (p * (p * 6f - 15f) + 10f);              // smootherstep
                    shrink = Mathf.Lerp(1f, cfg.strikeShrink, sc);
                    Z -= net * cfg.strikeAccel * e * dt;                            // throttle open: faster and faster into the plane
                    if (Z <= tp.z + 0.02f) { X = tp.x; Alt = tp.y - 1f; Ram(strikeSlot); return; }
                }
                else
                {   // still flying in: keeps its lane, weaving a little
                    X = baseX + Mathf.Sin(t * 1.4f + seed) * cfg.weave;
                    if (Z < -4f) { Vanish(); return; }   // nobody left to strike: flew past
                }
            }
            Apply();
        }

        /// <summary>The model's scale: the kind's size, a fighter stretched vertically (enemyHeightScale) so it reads head-on, times a
        /// distance boost that fades out as it comes in (perspective compensation; 1 = none).</summary>
        void ApplyModelScale(float far)
        {
            if (model == null) return;
            var cfg = GameManager.I != null ? GameManager.I.config : null;
            float s = Kind.scale * far, h = Kind.miniBoss || cfg == null ? 1f : cfg.enemyHeightScale;
            model.localScale = new Vector3(s, s * h, s);
        }

        void Apply()
        {
            float t = Time.time;
            var cfg = GameManager.I.config;
            bool still = Parked || Held;
            bool striking = strikeSlot >= 0;
            float bob = still ? Mathf.Sin(t * 2.2f + seed) * 0.06f : striking ? 0f : Mathf.Sin(t * 5f + seed) * 0.1f;   // no bob on the strike run: the path is the animation
            var pos = new Vector3(X, 1f + Alt + bob, Z);
            transform.position = pos;
            float s = (1f + hitT * 2.5f) * shrink;   // a striking fighter shrinks to half as it comes down on its plane
            float far = Mathf.Lerp(1f, cfg.enemyFarScale, Mathf.Clamp01((Z - cfg.enemyFarScaleZ) / Mathf.Max(1f, cfg.spawnDistance - cfg.enemyFarScaleZ)));   // bigger while far, so the swarm (and the boss) read at the horizon
            ApplyModelScale(Kind.miniBoss ? 1f + (far - 1f) * 0.6f : far);
            transform.localScale = new Vector3(s, s, s);
            if (model != null)
            {
                float pitch, bank;
                if (Kind.miniBoss) { pitch = Parked ? -14f * Mathf.Exp(-parkT * 3f) + muzzleT * 60f : -3f; bank = 0f; }
                else if (striking)
                {   // on the run the nose follows the flight path (over the top, then down onto the plane), the wings bank into the
                    // turn like a coordinated turn (the harder it curves sideways, the steeper the bank), with a little buffet on top
                    float dt = Mathf.Max(Time.deltaTime, 0.001f);
                    Vector3 v = (pos - prevPos) / dt;
                    float fwd = Mathf.Max(0.5f, -v.z);
                    pitch = Mathf.Clamp(-Mathf.Atan2(v.y, fwd) * Mathf.Rad2Deg, -50f, 70f) + Mathf.Sin(t * 23f + seed) * 1.5f;
                    bank = Mathf.Clamp(-Mathf.Atan2(v.x, fwd) * Mathf.Rad2Deg * 1.8f, -60f, 60f) + Mathf.Sin(t * 17f + seed) * 4f + strikeRoll;   // plus the wing-over's roll
                }
                else
                {   // banks into its weave
                    bank = Held ? Mathf.Sin(t * 1.1f + seed) * 6f : -Mathf.Cos(t * 1.4f + seed) * cfg.swarmBank;
                    pitch = 6f;   // a touch nose-down in cruise so the wing tops catch the light and the shape reads head-on
                }
                float k = 1f - Mathf.Exp(-12f * Time.deltaTime);   // smoothed so the attitude never snaps
                sPitch = Mathf.Lerp(sPitch, pitch, k); sBank = Mathf.Lerp(sBank, bank, k);
                model.localRotation = Quaternion.Euler(sPitch, 180f, sBank);   // nose toward the player
            }
            prevPos = pos;
            if (propeller != null) propeller.Rotate(0f, 0f, 2400f * Time.deltaTime, Space.Self);
            if (propellers != null) foreach (var p in propellers) if (p != null) p.Rotate(0f, 0f, 2400f * Time.deltaTime, Space.Self);
            if (flashRenderer != null) flashRenderer.enabled = muzzleT > 0f;
            bool showHit = hitT > 0f;
            if (showHit != hitShown && bodyRenderer != null) { hitShown = showHit; ApplyBodyColor(showHit); }
        }

        void Shoot()
        {
            var gm = GameManager.I;
            var sq = gm.squad;
            if (sq.Count <= 0 || BulletPool.I == null) return;
            Vector3 slot = sq.SlotLocal(Random.Range(0, sq.VisibleCount));
            Vector3 muzzle = transform.position + Vector3.down * 0.15f;
            BulletPool.I.Fire(muzzle, sq, slot, ShotDamage, new Color(1f, 0.35f, 0.3f), gm.config.enemyBulletSpeed, 3.6f);
            muzzleT = 0.1f;
            AudioManager.I.Play(Sfx.Flak);
        }

        public void TakeDamage(float d)
        {
            if (Dead || Striking) return;   // past the green line nothing stops it
            Hp -= d;
            hitT = 0.07f;
            if (hpLabel != null) { hpLabel.text = Mathf.CeilToInt(Mathf.Max(0f, Hp)).ToString(); hpLabel.gameObject.SetActive(true); }   // a fighter's number appears on its first hit; a boss's is always up
            if (Kind.miniBoss) SetHpBar();   // the bar just drains: the ghost / flash / kick animation was removed 2026-09-19 ("remove the getting damaged animation")
            if (Kind.miniBoss && !burning && Hp > 0f && Hp < MaxHp * 0.3f && FXManager.I != null && FXManager.I.bossFirePrefab != null) { burning = true; FXManager.I.Attach(FXManager.I.bossFirePrefab, model != null ? model : transform, new Vector3(0f, 0.3f, -0.4f), 1.4f); }   // a boss under 30%: the pack's fire on him (2026-09-19)
            if (Hp <= 0f) Kill(false);
        }

        /// <summary>Scales one bar piece from its left edge, so it drains left to right
        /// (the same left-pivot trick BossController uses for the zeppelin).</summary>
        void ScaleBar(Transform t, float k)
        {
            if (t == null) return;
            var sc = t.localScale;
            t.localScale = new Vector3(hpBarWidth * k, sc.y, sc.z);
            var lp = t.localPosition;
            t.localPosition = new Vector3(-hpBarWidth * 0.5f + hpBarWidth * k * 0.5f, lp.y, lp.z);
        }

        void SetHpBar() { ScaleBar(hpBarFill, MaxHp > 0f ? Mathf.Clamp01(Hp / MaxHp) : 0f); }

        /// <summary>Shot down: coins, a kill on the counter, and the model itself falls on as a burning wreck until it hits the
        /// sea (FXManager.PlaneWreck takes it off this object before WaveSpawner destroys the rest: the hp number, the boss bar).</summary>
        public void Kill(bool silent)
        {
            if (Dead) return;
            Dead = true;
            var gm = GameManager.I;
            gm.UnitsKilled++;
            if (!silent)
            {
                int v = gm.AddCoins(Kind.coins);
                var fx = FXManager.I;
                fx.Explosion(transform.position, Kind.miniBoss);
                transform.localScale = Vector3.one;   // drop the hit pulse (Apply scales the root up for 0.07 s after a hit) so the wreck leaves at its true size
                fx.PlaneWreck(this);
                fx.CoinBurst(transform.position, v);
                AudioManager.I.Play(Kind.miniBoss ? Sfx.Boom : Sfx.Unit);
            }
            WaveSpawner.I.Release(this);
            if (Kind.miniBoss && !silent) WaveSpawner.I.BossKilled(this);   // the last boss wins the game
        }

        /// <summary>Reached the squad: blows up on it. No coins, no kill - a plane lost. slot is the plane it
        /// struck (that one tumbles), or -1 for the old box hit around the leader.</summary>
        void Ram(int slot)
        {
            if (Dead) return;
            Dead = true;
            var fx = FXManager.I;
            fx.Explosion(transform.position, false);
            fx.FloatText(transform.position + Vector3.up * 1.2f, "RAMMED", new Color(1f, 0.23f, 0.31f), 0.7f);
            AudioManager.I.Play(Sfx.Boom);
            WaveSpawner.I.Release(this);
            var sq = GameManager.I.squad;
            sq.FallSlot = slot;
            sq.Damage(Mathf.Max(1, Mathf.RoundToInt(ShotDamage)), "rammed by a fighter");
        }

        /// <summary>Flew past without touching anyone.</summary>
        void Vanish()
        {
            if (Dead) return;
            Dead = true;
            WaveSpawner.I.Release(this);
        }
    }
}
