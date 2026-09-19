// BossController.cs
// The zeppelin. Appears when the level timer runs out, descends, then holds a distance
// and slowly closes in. Kill it before the timer bar empties or it rams the squad.
using UnityEngine;

namespace SkySquad
{
    public class BossController : MonoBehaviour
    {
        public Transform model;
        public TMPro.TextMeshPro hpLabel;
        public Transform hpBarFill;      // scaled on x from a left pivot
        public Transform timerBarFill;
        public float hpBarWidth = 8f;

        public bool Active { get; private set; }
        public bool Fighting { get; private set; }
        public bool Dead { get; private set; }
        public float Hp { get; private set; }
        public float MaxHp { get; private set; }
        public float Z => z;
        public float HalfWidth = 4.4f;   // for the squad's line-of-fire test

        float z, alt, introT, fightT, fireT, winT;

        public void ResetForLevel()
        {
            Active = Fighting = Dead = false;
            gameObject.SetActive(false);
        }

        public void Summon()
        {
            var cfg = GameManager.I.config;
            Active = true; Fighting = false; Dead = false;
            z = cfg.spawnDistance * 0.8f;
            alt = 17f;
            introT = 1.6f;
            gameObject.SetActive(true);
            SetBars(0f, 0f);
            WaveSpawner.I.KillAll(true);   // the escort clears out: the boss fight is the boss alone
            AudioManager.I.Play(Sfx.Warn);
        }

        void Update()
        {
            var gm = GameManager.I;
            if (!Active || gm == null || gm.State != GameState.Playing) return;
            var cfg = gm.config;
            var sq = gm.squad;
            float dt = Time.deltaTime;
            Color red = new Color(1f, 0.23f, 0.31f);

            if (!Fighting)
            {
                z -= gm.ScrollSpeed * dt;
                introT = Mathf.Max(0f, introT - dt);
                alt = Mathf.Lerp(6f, 17f, introT / 1.6f);
                if (z <= cfg.bossStartDistance)
                {
                    Fighting = true;
                    fightT = 0f; fireT = 0.8f;
                    MaxHp = Hp = Mathf.Max(10f, Mathf.Round(sq.Dps * cfg.bossHpPerDps + sq.Count * cfg.bossHpPerPlane));
                    FXManager.I.Shake(0.25f);
                }
            }
            else if (!Dead)
            {
                fightT += dt;
                z = Mathf.Lerp(cfg.bossStartDistance, cfg.bossEndDistance, Mathf.Min(1f, fightT / cfg.bossFightSeconds));
                if (fightT >= cfg.bossFightSeconds)
                {
                    gm.Lose("The boss rammed you with " + Mathf.CeilToInt(Hp) + " HP left.");
                    return;
                }
                fireT -= dt;
                if (fireT <= 0f)
                {
                    fireT = cfg.bossFireEvery;
                    Vector3 slot = sq.SlotWorld(Random.Range(0, sq.VisibleCount));
                    var af = sq.GetComponent<AutoFire>();
                    if (af != null && af.tracers != null) af.tracers.Fire(transform.position, slot, red, 0.18f, 0.1f);
                    FXManager.I.Sparks(slot, new Color(1f, 0.42f, 0.17f), 8);
                    sq.Damage(1, "The boss had " + Mathf.CeilToInt(Hp) + " HP left.");
                    if (gm.State != GameState.Playing) return;
                }
                if (Hp <= 0f) Die();
            }
            else
            {
                winT -= dt;
                if (Random.value < 0.35f) FXManager.I.Explosion(transform.position + Random.insideUnitSphere * 3f, false);
                if (winT <= 0f)
                {
                    Active = false;
                    gameObject.SetActive(false);
                    gm.LevelCleared();
                    return;
                }
            }

            transform.position = new Vector3(0f, 1f + alt + Mathf.Sin(Time.time * 1.5f) * 0.2f, z);
            if (model != null) model.localRotation = Quaternion.Euler(0f, 0f, Mathf.Sin(Time.time * 0.9f) * 2f);
            if (hpLabel != null) hpLabel.text = Fighting && !Dead ? Mathf.CeilToInt(Hp).ToString() : "";
            SetBars(Fighting ? Mathf.Clamp01(Hp / Mathf.Max(1f, MaxHp)) : 0f, Fighting ? Mathf.Clamp01(1f - fightT / cfg.bossFightSeconds) : 0f);
        }

        void SetBars(float hp, float timer)
        {
            if (hpBarFill != null) { hpBarFill.localScale = new Vector3(hpBarWidth * hp, hpBarFill.localScale.y, 1f); hpBarFill.localPosition = new Vector3(-hpBarWidth / 2f + hpBarWidth * hp / 2f, hpBarFill.localPosition.y, 0f); }
            if (timerBarFill != null) { timerBarFill.localScale = new Vector3(hpBarWidth * timer, timerBarFill.localScale.y, 1f); timerBarFill.localPosition = new Vector3(-hpBarWidth / 2f + hpBarWidth * timer / 2f, timerBarFill.localPosition.y, 0f); }
        }

        public void TakeDamage(float d)
        {
            if (!Fighting || Dead) return;
            Hp = Mathf.Max(0f, Hp - d);
        }

        void Die()
        {
            Dead = true;
            winT = 1.4f;
            AudioManager.I.Play(Sfx.Boom);
            var p = transform.position;
            var fx = FXManager.I;
            fx.Explosion(p, true); fx.Explosion(p + Vector3.left * 3f, true); fx.Explosion(p + Vector3.right * 3f, true);
            fx.Shake(0.5f); fx.Flash(Color.white, 0.25f);
            WaveSpawner.I.KillAll(true);
        }
    }
}
