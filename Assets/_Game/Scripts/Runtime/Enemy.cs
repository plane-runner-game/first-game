// Enemy.cs
// One enemy plane in the HIGH band. It flies down the lane weaving and banking, stops when it
// reaches the front line (or a plane ahead of it), and once parked on the line it shoots at the
// squad from there. It never leaves the high band: the only way to stop the shooting is to climb
// up and clear it. Hits flash it white and pop its scale; kills drop a tumbling wreck.
using UnityEngine;

namespace SkySquad
{
    public class Enemy : MonoBehaviour
    {
        public Transform model;
        public Transform propeller;
        public Renderer bodyRenderer;
        public Renderer flashRenderer;    // muzzle flash quad, enabled briefly when it shoots
        public TMPro.TextMeshPro hpLabel;

        public EnemyKindDef Kind { get; private set; }
        public float Hp { get; private set; }
        public float MaxHp { get; private set; }
        public bool Wide { get; private set; }     // mini boss: blocks everything behind it
        public bool Dead { get; private set; }
        public bool Parked { get; private set; }
        public float X, Z, Alt;
        public float HalfWidth => Kind.halfWidth;

        static MaterialPropertyBlock hitBlock;
        static readonly int BaseColor = Shader.PropertyToID("_BaseColor");
        float fireT, hitT, muzzleT, seed;
        bool hitShown;

        public void Init(EnemyKindDef kind, float hp, bool wide, float x, float z, float alt)
        {
            Kind = kind; MaxHp = Hp = hp; Wide = wide; X = x; Z = z; Alt = alt;
            Dead = Parked = false; hitT = muzzleT = 0f; seed = Random.value * 10f;
            fireT = kind.fireEvery * (0.6f + Random.value * 0.8f);
            if (model != null) model.localScale = Vector3.one * kind.scale;
            if (flashRenderer != null) flashRenderer.enabled = false;
            if (hpLabel != null) hpLabel.text = Mathf.CeilToInt(Hp).ToString();
            Apply();
        }

        /// <summary>Advance toward the squad but never past limitZ (the front line or the plane ahead).
        /// WaveSpawner calls this front-to-back every frame, so the crowd compacts and never overlaps.
        /// Only a plane on the front line shoots: the ones stuck behind a friend can't fire past it.</summary>
        public void Tick(float dt, float limitZ, bool frontRow)
        {
            if (Dead) return;
            var gm = GameManager.I;
            float want = Z - (gm.ScrollSpeed + Kind.approachSpeed) * dt;
            Z = Mathf.Max(want, limitZ);
            Parked = want <= limitZ;
            hitT = Mathf.Max(0f, hitT - dt);
            muzzleT = Mathf.Max(0f, muzzleT - dt);
            if (Parked && frontRow)
            {
                fireT -= dt;
                if (fireT <= 0f) { fireT = Kind.fireEvery * (0.75f + Random.value * 0.5f); Shoot(); }
            }
            Apply();
        }

        void Apply()
        {
            float t = Time.time;
            float weave = Parked ? 0f : Mathf.Sin(t * 1.1f + seed) * 0.35f;          // visual only; blocking uses X
            float bob = Mathf.Sin(t * 5f + seed) * 0.1f;
            transform.position = new Vector3(X + weave, 1f + Alt + bob, Z);
            float s = 1f + hitT * 2.5f;
            transform.localScale = new Vector3(s, s, s);
            if (model != null)
            {
                float bank = Parked ? Mathf.Sin(t * 2.3f + seed) * 6f : Mathf.Cos(t * 1.1f + seed) * 14f;   // bank into the weave
                float pitch = Parked ? 8f + muzzleT * 40f : -3f;                                            // recoil when it fires
                model.localRotation = Quaternion.Euler(pitch, 180f, bank);                                  // nose toward the player
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
            if (sq.Count <= 0) return;
            Vector3 slot = sq.SlotWorld(Random.Range(0, sq.VisibleCount));
            Color red = new Color(1f, 0.32f, 0.3f);
            if (TracerPool.I != null) TracerPool.I.Fire(transform.position, slot, red, 0.16f, Kind.miniBoss ? 0.14f : 0.08f);
            FXManager.I.Sparks(slot, new Color(1f, 0.42f, 0.17f), Kind.miniBoss ? 8 : 3);
            AudioManager.I.Play(Sfx.Flak);
            muzzleT = 0.09f;
            sq.TakeShot(Kind.shotDamage * (1f + sq.Count * gm.config.enemyShotPerPlane), Kind.displayName.ToLower() + " fire from above");
        }

        public void TakeDamage(float d)
        {
            if (Dead) return;
            Hp -= d;
            hitT = 0.07f;
            if (hpLabel != null) hpLabel.text = Mathf.CeilToInt(Mathf.Max(0f, Hp)).ToString();
            if (Hp <= 0f) Kill(false);
        }

        public void Kill(bool silent)
        {
            if (Dead) return;
            Dead = true;
            var gm = GameManager.I;
            gm.UnitsKilled++;
            if (!silent)
            {
                gm.AddCoins(Kind.coins);
                var fx = FXManager.I;
                fx.Explosion(transform.position, Kind.miniBoss);
                fx.UnitFall(Kind.prefab, transform.position, Kind.scale);
                if (Kind.miniBoss) fx.FloatText(transform.position + Vector3.up * 2f, "+" + Kind.coins, new Color(1f, 0.82f, 0.25f), 1f);
                AudioManager.I.Play(Kind.miniBoss ? Sfx.Boom : Sfx.Unit);
            }
            WaveSpawner.I.Release(this);
        }
    }
}
