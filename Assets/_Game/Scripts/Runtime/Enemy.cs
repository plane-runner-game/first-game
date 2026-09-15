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
        float baseX, fireT, hitT, muzzleT, parkT, seed, shrink = 1f, sPitch, sBank, strikeRoll;
        bool hitShown, wasParked, crossed;             // crossed: it has passed the green line
        int strikeSlot = -1;                           // the squad plane it locked when it crossed, or -1
        public int StrikeStyle;                        // 0..4, picked by the spawner: which figure it flies on its strike run
        Vector3 strikeStart, prevPos;                  // (X, Alt, Z) where the strike began; last frame's position for the flight direction
        public const int StrikeStyles = 5;
        public bool Striking => strikeSlot >= 0;       // on its strike run: bullets pass through it, it cannot be stopped
        public float StrikeT { get; private set; }     // seconds since it crossed the line (ThreatMarkers pops its reticle on that)

        public void Init(EnemyKindDef kind, float hp, bool wide, float x, float z, float alt, float shotDamage)
        {
            Kind = kind; MaxHp = Hp = hp; Wide = wide; baseX = X = x; Z = z; Alt = alt; ShotDamage = shotDamage;
            Dead = Parked = Held = wasParked = crossed = false; strikeSlot = -1; shrink = 1f; sPitch = -3f; sBank = strikeRoll = 0f;
            hitT = muzzleT = parkT = 0f; Pending = 0f; seed = Random.value * 10f;
            prevPos = new Vector3(x, 1f + alt, z);
            ApplyModelScale(1f);
            if (flashRenderer != null) flashRenderer.enabled = false;
            if (hpLabel != null) hpLabel.text = Mathf.CeilToInt(Hp).ToString();
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
                float net = (gm.ScrollSpeed + Kind.approachSpeed) * SpeedMult;   // each one at its own speed
                Z = Mathf.Max(Z - net * dt, limitZ);
                Held = Z <= limitZ + 0.02f;
                if (!crossed && !Held && Z < cfg.diveZ && sq.VisibleCount > 0)
                {   // crossing the green line: lock the squad plane nearest to its lane. Every fighter that crosses strikes one.
                    crossed = true;
                    float best = float.MaxValue;
                    for (int i = 0; i < sq.VisibleCount; i++)
                    {
                        float d = Mathf.Abs(sq.SlotWorld(i).x - X);
                        if (d < best) { best = d; strikeSlot = i; }
                    }
                    strikeStart = new Vector3(X, Alt, Z);   // where the run begins: X/Alt ease from here to the plane as Z closes
                    StrikeT = 0f;
                }
                if (strikeSlot >= 0 && sq.VisibleCount > 0)
                {   // the strike run: Z keeps flowing at its own pace (no hitch at the line) and speeds up into the dive; X and
                    // altitude ease from where it crossed onto the plane's slot (re-read every frame, so it tracks the squad);
                    // one of five figures is layered on top (StrikeStyle); it shrinks a little; and it lands exactly on the
                    // plane when Z gets there. Bullets cannot touch it on the run (Striking).
                    if (strikeSlot >= sq.VisibleCount) strikeSlot = sq.VisibleCount - 1;   // its plane is already gone: take the last slot left
                    StrikeT += dt;
                    Vector3 tp = sq.SlotWorld(strikeSlot);
                    float span = Mathf.Max(0.5f, strikeStart.z - tp.z);
                    float p = Mathf.Clamp01(1f - (Z - tp.z) / span);            // 0 at the line .. 1 on the plane
                    float e = p * p * (3f - 2f * p);                                // smoothstep: eases in and out
                    float arc = Mathf.Sin(p * Mathf.PI);                            // 0 at both ends, 1 mid-run: every figure fades in and out of the straight path
                    float lift = 0f, side = 0f; strikeRoll = 0f;
                    switch (StrikeStyle)
                    {
                        case 0:   // HOP: up into the air, then down onto the plane
                            lift = arc * cfg.strikeLift; break;
                        case 1:   // SWOOP: dips under, then climbs into the plane from below
                            lift = -arc * cfg.strikeLift * 0.8f; break;
                        case 2:   // BARREL ROLL: a shallow hop with one full roll around its own axis
                            lift = arc * cfg.strikeLift * 0.35f; strikeRoll = 360f * e; break;
                        case 3:   // SLALOM: an S-curve sideways, so it comes in from the flank
                            side = Mathf.Sin(p * Mathf.PI * 2f) * cfg.strikeSide * (seed < 5f ? 1f : -1f); lift = arc * cfg.strikeLift * 0.5f; break;
                        default:  // CORKSCREW: two turns of a spiral that opens then tightens onto the plane
                            float a = p * Mathf.PI * 4f, r = arc * cfg.strikeSide;
                            side = Mathf.Sin(a) * r; lift = (Mathf.Cos(a) - 1f) * r * 0.5f + arc * cfg.strikeLift * 0.6f; strikeRoll = -Mathf.Sin(a) * 35f; break;
                    }
                    baseX = X = Mathf.Lerp(strikeStart.x, tp.x, e) + side;
                    Alt = Mathf.Lerp(strikeStart.y, tp.y - 1f, e) + lift;
                    float sc = p * p * p * (p * (p * 6f - 15f) + 10f);              // smootherstep: the shrink glides, no visible start or stop
                    shrink = Mathf.Lerp(1f, cfg.strikeShrink, sc) * (1f + 0.08f * Mathf.Sin(Mathf.Min(1f, p * 2.5f) * Mathf.PI));   // a soft puff as it commits, then it shrinks
                    Z -= net * cfg.strikeAccel * e * dt;                            // eases into the faster dive
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
                {   // on the run the nose follows the flight path (up over the arc, down onto the plane) and the wings bank into the turn
                    float dt = Mathf.Max(Time.deltaTime, 0.001f);
                    Vector3 v = (pos - prevPos) / dt;
                    float fwd = Mathf.Max(0.5f, -v.z);
                    pitch = Mathf.Clamp(-Mathf.Atan2(v.y, fwd) * Mathf.Rad2Deg, -45f, 60f);
                    bank = Mathf.Clamp(-v.x * 6f, -40f, 40f) + strikeRoll;   // plus the figure's own roll (barrel roll, corkscrew)
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
            if (showHit != hitShown && bodyRenderer != null)
            {
                hitShown = showHit;
                if (showHit)
                {
                    if (hitBlock == null) hitBlock = new MaterialPropertyBlock();
                    hitBlock.SetColor(BaseColor, Color.white);
                    bodyRenderer.SetPropertyBlock(hitBlock);
                }
                else bodyRenderer.SetPropertyBlock(null);
            }
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
            if (hpLabel != null) hpLabel.text = Mathf.CeilToInt(Mathf.Max(0f, Hp)).ToString();
            if (Hp <= 0f) Kill(false);
        }

        /// <summary>Shot down: coins, a wreck falling, a kill on the counter.</summary>
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
                fx.UnitFall(Kind.prefab, transform.position, Kind.scale);
                fx.CoinBurst(transform.position, v);
                AudioManager.I.Play(Kind.miniBoss ? Sfx.Boom : Sfx.Unit);
            }
            WaveSpawner.I.Release(this);
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
