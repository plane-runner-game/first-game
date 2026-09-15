// Enemy.cs
// One enemy plane in the HIGH band. Fighters are kamikazes: they fly in scattered, drift slowly toward
// the squad's lane while weaving, and over the last few units dive onto the squad - one that gets there
// blows up on you and takes a plane; slip out of its way and it flies past. Only a boss stops: he parks
// on the front line and shoots on his own clock, every landed shot costing a plane.
using UnityEngine;

namespace SkySquad
{
    public class Enemy : MonoBehaviour
    {
        public Transform model;
        public Transform propeller;
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
        public float X, Z, Alt;
        public float HalfWidth => Kind.halfWidth;

        static MaterialPropertyBlock hitBlock;
        static readonly int BaseColor = Shader.PropertyToID("_BaseColor");
        float baseX, fireT, hitT, muzzleT, parkT, diveT, seed;
        bool hitShown, wasParked;

        public void Init(EnemyKindDef kind, float hp, bool wide, float x, float z, float alt, float shotDamage)
        {
            Kind = kind; MaxHp = Hp = hp; Wide = wide; baseX = X = x; Z = z; Alt = alt; ShotDamage = shotDamage;
            Dead = Parked = Held = wasParked = false;
            hitT = muzzleT = parkT = diveT = 0f; Pending = 0f; seed = Random.value * 10f;
            if (model != null) model.localScale = Vector3.one * kind.scale;
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
            {   // kamikaze: slow drift toward the squad's lane, a weave, then the dive
                float net = gm.ScrollSpeed + Kind.approachSpeed;
                Z = Mathf.Max(Z - net * dt, limitZ);
                Held = Z <= limitZ + 0.02f;
                bool diving = !Held && Z < cfg.diveZ;
                diveT = diving ? diveT + dt : 0f;
                baseX = Mathf.MoveTowards(baseX, sq.X, (diving ? cfg.diveFollow : cfg.followSpeed) * dt);
                X = baseX + Mathf.Sin(t * 1.4f + seed) * cfg.weave;
                if (diving) Alt = Mathf.MoveTowards(Alt, sq.Alt, cfg.diveClimb * dt);
                float hitX = cfg.ramHitX + cfg.ramHitPerPlane * sq.VisibleCount;
                if (Z <= cfg.ramZ && Mathf.Abs(X - sq.X) < hitX && Mathf.Abs(Alt - sq.Alt) < 1.6f) { Ram(); return; }
                if (Z < -4f) { Vanish(); return; }   // missed: flew past
            }
            Apply();
        }

        void Apply()
        {
            float t = Time.time;
            bool still = Parked || Held;
            float bob = still ? Mathf.Sin(t * 2.2f + seed) * 0.06f : Mathf.Sin(t * 5f + seed) * 0.1f;
            transform.position = new Vector3(X, 1f + Alt + bob, Z);
            float s = 1f + hitT * 2.5f;
            transform.localScale = new Vector3(s, s, s);
            if (model != null)
            {
                float pitch, bank;
                if (Kind.miniBoss) { pitch = Parked ? -14f * Mathf.Exp(-parkT * 3f) + muzzleT * 60f : -3f; bank = 0f; }
                else
                {   // banks into its weave; noses down as it dives at the squad
                    bank = Held ? Mathf.Sin(t * 1.1f + seed) * 6f : -Mathf.Cos(t * 1.4f + seed) * 22f;
                    pitch = diveT > 0f ? Mathf.Min(22f, diveT * 40f) : -3f;
                }
                model.localRotation = Quaternion.Euler(pitch, 180f, bank);   // nose toward the player
            }
            if (propeller != null) propeller.Rotate(0f, 0f, 2400f * Time.deltaTime, Space.Self);
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
            if (Dead) return;
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

        /// <summary>Reached the squad: blows up on it. No coins, no kill - a plane lost.</summary>
        void Ram()
        {
            if (Dead) return;
            Dead = true;
            var fx = FXManager.I;
            fx.Explosion(transform.position, false);
            fx.FloatText(transform.position + Vector3.up * 1.2f, "RAMMED", new Color(1f, 0.23f, 0.31f), 0.7f);
            AudioManager.I.Play(Sfx.Boom);
            WaveSpawner.I.Release(this);
            GameManager.I.squad.Damage(Mathf.Max(1, Mathf.RoundToInt(ShotDamage)), "rammed by a fighter");
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
