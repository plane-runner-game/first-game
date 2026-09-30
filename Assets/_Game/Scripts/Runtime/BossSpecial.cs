// BossSpecial.cs
// The boss attacks that are not a bullet flying at a plane (2026-09-30: "every boss his own NEW way of firing, not the same one in another
// colour"). Each one is a shape in the air that the player can read and steer out of: a beam that sweeps across the squad, an area that is
// marked and then erupts, a tornado that walks in, a wave with one safe pocket, lightning that jumps plane to plane, portals that open next to
// the squad and fire point blank, a line of crystals marching down a lane. Damage is counted by who is standing inside the shape when it lands
// (never more than the attack's cost, one plane each), so a squad that moves takes less. The coroutines run on the squad, so an attack that has
// begun still lands if the boss dies mid-way. Effects come from the free packs (Free Quick Effects Vol. 1, Hovl's Magic Effects).
using System.Collections;
using System.Collections.Generic;
using UnityEngine;

namespace SkySquad
{
    public static class BossSpecial
    {
        class Budget { public int left; }

        public static IEnumerator Run(Enemy boss, SquadController sq, BossAttack a, int total, List<int> marked, Vector3 muzzle)
        {
            var b = new Budget { left = Mathf.Max(1, total) };
            switch (a.kind)
            {
                case AttackKind.Sweep: return Sweep(boss, sq, a, b, marked, muzzle);
                case AttackKind.Zone: return Many(sq, a, b, marked, ZoneOne);
                case AttackKind.Tornado: return Many(sq, a, b, marked, TornadoOne, muzzle);
                case AttackKind.Wave: return Wave(sq, a, b, marked, muzzle);
                case AttackKind.Chain: return Chain(sq, a, b, marked, muzzle);
                case AttackKind.Portal: return Many(sq, a, b, marked, PortalOne);
                case AttackKind.Spikes: return Many(sq, a, b, marked, SpikesOne, muzzle);
            }
            return Nothing();
        }

        static IEnumerator Nothing() { yield break; }

        // ------------------------------------------------------------------ helpers
        static bool Live(SquadController sq) { return GameManager.I != null && GameManager.I.State == GameState.Playing && sq != null && sq.Count > 0; }

        static GameObject Spawn(GameObject prefab, Vector3 pos, float scale, float life)
        {
            if (prefab == null) return null;
            var go = Object.Instantiate(prefab, pos, Quaternion.identity);
            go.transform.localScale = Vector3.one * scale;
            foreach (var ps in go.GetComponentsInChildren<ParticleSystem>(true)) ps.Play();
            Object.Destroy(go, life);
            return go;
        }

        static Vector3 Centre(SquadController sq)
        {
            int n = Mathf.Max(1, sq.VisibleCount); Vector3 c = Vector3.zero;
            for (int i = 0; i < n; i++) c += sq.SlotWorld(i);
            return c / n;
        }

        static void Extent(SquadController sq, out float xMin, out float xMax)
        {
            xMin = float.MaxValue; xMax = float.MinValue;
            for (int i = 0; i < Mathf.Max(1, sq.VisibleCount); i++) { float x = sq.SlotWorld(i).x; xMin = Mathf.Min(xMin, x); xMax = Mathf.Max(xMax, x); }
        }

        /// <summary>How many planes stand within r of p (across, and half as much for depth), and the nearest one.</summary>
        static int Inside(SquadController sq, Vector3 p, float r, out int nearest)
        {
            int n = 0; nearest = 0; float best = float.MaxValue;
            for (int i = 0; i < sq.VisibleCount; i++)
            {
                Vector3 q = sq.SlotWorld(i);
                float d = Mathf.Sqrt((q.x - p.x) * (q.x - p.x) + 0.25f * (q.z - p.z) * (q.z - p.z));
                if (d <= r) { n++; if (d < best) { best = d; nearest = i; } }
            }
            return n;
        }

        static void Hurt(SquadController sq, int victims, int nearest, Budget b)
        {
            int d = Mathf.Min(b.left, victims);
            if (d <= 0 || !Live(sq)) return;
            b.left -= d;
            sq.FallSlot = Mathf.Min(nearest, sq.VisibleCount - 1);
            sq.Damage(d, "caught in a boss attack");
        }

        static void Kick(BossAttack a) { if (a.shake > 0f && FXManager.I != null) FXManager.I.Shake(a.shake); }

        static void Sound(BossAttack a) { if (a.sfx != null) AudioManager.I.PlayClip(a.sfx); else AudioManager.I.Play(a.sound); }

        static Vector3 Origin(Enemy boss, Vector3 fallback) { return boss != null && !boss.Dead ? boss.transform.position + (fallback - boss.transform.position) : fallback; }

        /// <summary>One coroutine per marked plane, started 'volleyStagger' apart (so an ordered set sweeps across the squad). The budget is shared.</summary>
        static IEnumerator Many(SquadController sq, BossAttack a, Budget b, List<int> marked, System.Func<SquadController, BossAttack, Budget, int, int, Vector3, IEnumerator> one, Vector3? from = null)
        {
            int n = Mathf.Max(1, Mathf.Min(marked.Count, b.left));
            for (int i = 0; i < n; i++)
            {
                if (!Live(sq)) yield break;
                sq.StartCoroutine(one(sq, a, b, marked[i], n, from ?? Vector3.zero));
                if (i < n - 1 && a.volleyStagger > 0f) yield return new WaitForSeconds(a.volleyStagger);
            }
        }

        static IEnumerator Many(SquadController sq, BossAttack a, Budget b, List<int> marked, System.Func<SquadController, BossAttack, Budget, int, int, IEnumerator> one)
        {
            int n = Mathf.Max(1, Mathf.Min(marked.Count, b.left));
            for (int i = 0; i < n; i++)
            {
                if (!Live(sq)) yield break;
                sq.StartCoroutine(one(sq, a, b, marked[i], n));
                if (i < n - 1 && a.volleyStagger > 0f) yield return new WaitForSeconds(a.volleyStagger);
            }
        }

        // ------------------------------------------------------------------ Zone: marked, then it erupts
        static IEnumerator ZoneOne(SquadController sq, BossAttack a, Budget b, int slot, int of)
        {
            if (!Live(sq)) yield break;
            slot = Mathf.Min(slot, sq.VisibleCount - 1);
            Vector3 p = sq.SlotWorld(slot); p.x += Random.Range(-0.5f, 0.5f); p.y -= 1f;
            if (a.fxTell != null) Spawn(a.fxTell, p, a.tellScale, a.delay + 0.3f); else if (FXManager.I != null) FXManager.I.Ring(p + Vector3.up, new Color(1f, 0.3f, 0.2f), 3f, true);
            yield return new WaitForSeconds(a.delay);
            if (!Live(sq)) yield break;
            Spawn(a.fx, p, a.fxScale, 4f);
            Spawn(a.fxHit, p, a.hitScale, 3f);
            Kick(a); Sound(a);
            yield return new WaitForSeconds(a.hitDelay);
            int near; int hit = Inside(sq, p, a.radius, out near);
            Hurt(sq, hit, near, b);
        }

        // ------------------------------------------------------------------ Spikes: a line of eruptions marching down one lane
        static IEnumerator SpikesOne(SquadController sq, BossAttack a, Budget b, int slot, int of, Vector3 from)
        {
            if (!Live(sq)) yield break;
            slot = Mathf.Min(slot, sq.VisibleCount - 1);
            Vector3 lane = sq.SlotWorld(slot);
            if (FXManager.I != null) FXManager.I.Ring(lane + Vector3.down * 0.5f, new Color(1f, 0.3f, 0.2f), 3f, true);
            int steps = Mathf.Max(3, a.steps);
            float z0 = from.z - 3f, z1 = lane.z;
            for (int k = 0; k < steps; k++)
            {
                if (!Live(sq)) yield break;
                Vector3 p = new Vector3(lane.x, lane.y - 1f, Mathf.Lerp(z0, z1, k / (float)(steps - 1)));
                Spawn(a.fx, p, a.fxScale * Mathf.Lerp(0.7f, 1.1f, k / (float)(steps - 1)), 3f);
                if (k == steps - 1)
                {
                    Spawn(a.fxHit, p, a.hitScale, 3f); Kick(a); Sound(a);
                    int near; int hit = Inside(sq, new Vector3(lane.x, lane.y, Centre(sq).z), a.radius, out near);
                    Hurt(sq, hit, near, b);
                }
                yield return new WaitForSeconds(a.duration / steps);
            }
        }

        // ------------------------------------------------------------------ Tornado: walks in, following a plane
        static IEnumerator TornadoOne(SquadController sq, BossAttack a, Budget b, int slot, int of, Vector3 from)
        {
            if (!Live(sq)) yield break;
            Vector3 c = Centre(sq);
            Vector3 p = new Vector3(from.x, c.y - 1.2f, from.z);
            var go = Spawn(a.fx, p, a.fxScale, a.duration + 4f);
            bool hitDone = false;
            float t = 0f;
            while (t < a.duration + 1.2f && Live(sq))
            {
                t += Time.deltaTime;
                Vector3 tp = sq.SlotWorld(Mathf.Min(slot, sq.VisibleCount - 1));
                p.x = Mathf.MoveTowards(p.x, tp.x, a.homing * Time.deltaTime);
                p.z = Mathf.Lerp(from.z, Centre(sq).z - 1f, t / a.duration);
                p.y = Mathf.Lerp(p.y, tp.y - 1.2f, 2f * Time.deltaTime);
                if (go != null) go.transform.position = p;
                if (!hitDone && t >= a.duration)
                {
                    hitDone = true;
                    Kick(a); Sound(a);
                    int near; int hit = Inside(sq, p, a.radius, out near);
                    Hurt(sq, hit, near, b);
                }
                yield return null;
            }
            if (go != null) Object.Destroy(go);
        }

        // ------------------------------------------------------------------ Wave: covers everything but one safe pocket
        static IEnumerator Wave(SquadController sq, BossAttack a, Budget b, List<int> marked, Vector3 muzzle)
        {
            if (!Live(sq)) yield break;
            Vector3 c = Centre(sq);
            Vector3 g = sq.SlotWorld(Mathf.Min(marked.Count > 0 ? marked[0] : 0, sq.VisibleCount - 1));
            Vector3 gp = new Vector3(g.x, c.y - 1.2f, c.z);
            var safe = Spawn(a.fxTell, gp, a.tellScale, a.delay + 0.8f);
            if (a.duration > 0f) Spawn(a.fx, new Vector3(0f, gp.y, muzzle.z - 2f), a.fxScale, a.delay + a.duration + 1f);
            float t = 0f;
            while (t < a.delay && Live(sq)) { t += Time.deltaTime; yield return null; }
            if (!Live(sq)) yield break;
            if (a.duration <= 0f) Spawn(a.fx, new Vector3(0f, gp.y, c.z), a.fxScale, 3.5f);
            Kick(a); Sound(a);
            float dur = 0f;
            while (dur < a.duration) { dur += Time.deltaTime; yield return null; }
            int victims = 0, nearest = 0; float best = float.MaxValue;
            for (int i = 0; i < sq.VisibleCount; i++)
            {
                float d = Mathf.Abs(sq.SlotWorld(i).x - gp.x);
                if (d > a.gap) { victims++; if (d < best) { best = d; nearest = i; } }
            }
            if (a.fxHit != null) Spawn(a.fxHit, new Vector3(sq.SlotWorld(nearest).x, gp.y, c.z), a.hitScale, 2f);
            Hurt(sq, victims, nearest, b);
        }

        // ------------------------------------------------------------------ Chain: jumps from plane to plane
        static IEnumerator Chain(SquadController sq, BossAttack a, Budget b, List<int> marked, Vector3 muzzle)
        {
            if (!Live(sq)) yield break;
            int links = Mathf.Min(a.count + 0, b.left);
            var hitSlots = new List<int>();
            Vector3 prev = muzzle;
            int cur = Mathf.Min(marked.Count > 0 ? marked[0] : 0, sq.VisibleCount - 1);
            for (int k = 0; k < links; k++)
            {
                if (!Live(sq)) yield break;
                if (k > 0)
                {   // the nearest plane it has not touched yet
                    int best = -1; float bd = float.MaxValue;
                    for (int i = 0; i < sq.VisibleCount; i++)
                    {
                        if (hitSlots.Contains(i)) continue;
                        float d = (sq.SlotWorld(i) - prev).sqrMagnitude;
                        if (d < bd) { bd = d; best = i; }
                    }
                    if (best < 0) break;
                    cur = best;
                }
                hitSlots.Add(cur);
                Vector3 tp = sq.SlotWorld(cur);
                Arc(a, prev, tp);
                Spawn(a.fx, tp, a.fxScale, 2.5f);
                Spawn(a.fxHit, tp, a.hitScale, 2f);
                Kick(a); Sound(a);
                Hurt(sq, 1, cur, b);
                prev = tp;
                yield return new WaitForSeconds(a.volleyStagger > 0f ? a.volleyStagger : 0.15f);
            }
        }

        /// <summary>A jagged bolt between two points, gone in a blink.</summary>
        static void Arc(BossAttack a, Vector3 from, Vector3 to)
        {
            if (a.beamMat == null) return;
            var go = new GameObject("Arc");
            var lr = go.AddComponent<LineRenderer>();
            int n = 9; lr.positionCount = n; lr.material = a.beamMat; lr.startColor = lr.endColor = a.beamColor;
            lr.widthMultiplier = a.beamWidth; lr.numCapVertices = 2; lr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            for (int i = 0; i < n; i++)
            {
                Vector3 p = Vector3.Lerp(from, to, i / (float)(n - 1));
                if (i > 0 && i < n - 1) p += Random.insideUnitSphere * 0.35f;
                lr.SetPosition(i, p);
            }
            Object.Destroy(go, 0.22f);
        }

        // ------------------------------------------------------------------ Portal: opens beside the squad and fires point blank
        static IEnumerator PortalOne(SquadController sq, BossAttack a, Budget b, int slot, int of)
        {
            if (!Live(sq)) yield break;
            slot = Mathf.Min(slot, sq.VisibleCount - 1);
            Vector3 tp = sq.SlotWorld(slot);
            float side = Random.value < 0.5f ? -1f : 1f;
            Vector3 p = new Vector3(tp.x + side * Random.Range(1.5f, 3.2f), tp.y + 0.8f, tp.z + Random.Range(4f, 7f));
            var portal = Spawn(a.fx, p, a.fxScale, a.delay + 1.2f);
            yield return new WaitForSeconds(a.delay);
            if (!Live(sq)) yield break;
            slot = Mathf.Min(slot, sq.VisibleCount - 1);
            int dmg = Mathf.Max(1, b.left / Mathf.Max(1, of)); b.left = Mathf.Max(0, b.left - dmg);
            BulletPool.I.Fire(p, sq, sq.SlotLocal(slot), dmg, a.color, GameManager.I.config.enemyBulletSpeed * Mathf.Max(0.1f, a.speedMul), a.size, 0f, false, a.projectile, a.projectileScale, a.hit, a.hitScale, a.projectileTurn);
            if (a.muzzle != null && FXManager.I != null) FXManager.I.Burst(a.muzzle, p, a.muzzleScale, 0.45f);
            Sound(a);
        }

        // ------------------------------------------------------------------ Sweep: a beam or a jet of fire dragged across the squad
        static IEnumerator Sweep(Enemy boss, SquadController sq, BossAttack a, Budget b, List<int> marked, Vector3 muzzle)
        {
            if (!Live(sq)) yield break;
            bool two = a.order == ShotOrder.CenterOut || a.order == ShotOrder.OutsideIn;
            int beams = two ? 2 : 1;
            var objs = new GameObject[beams]; var lines = new LineRenderer[beams]; var marks = new GameObject[beams];
            for (int i = 0; i < beams; i++)
            {
                if (a.fx != null) { objs[i] = Object.Instantiate(a.fx, muzzle, Quaternion.identity); objs[i].transform.localScale = Vector3.one * a.fxScale; foreach (var ps in objs[i].GetComponentsInChildren<ParticleSystem>(true)) ps.Play(); }
                if (a.beamMat != null)
                {
                    var go = new GameObject("Beam"); var lr = go.AddComponent<LineRenderer>();
                    lr.positionCount = 2; lr.material = a.beamMat; lr.startColor = lr.endColor = a.beamColor; lr.numCapVertices = 4;
                    lr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off; lines[i] = lr;
                    if (objs[i] == null) objs[i] = go; else go.transform.SetParent(objs[i].transform, true);
                }
                if (a.fxHit != null) { marks[i] = Object.Instantiate(a.fxHit, muzzle, Quaternion.identity); marks[i].transform.localScale = Vector3.one * a.hitScale; foreach (var ps in marks[i].GetComponentsInChildren<ParticleSystem>(true)) ps.Play(); }
            }
            Sound(a);
            float t = 0f, tickT = 0f, trackX = Centre(sq).x;
            int tracked = Mathf.Min(marked.Count > 0 ? marked[0] : 0, sq.VisibleCount - 1);
            while (t < a.duration && Live(sq))
            {
                t += Time.deltaTime; tickT += Time.deltaTime;
                float p = Mathf.Clamp01(t / a.duration);
                float xMin, xMax; Extent(sq, out xMin, out xMax);
                Vector3 c = Centre(sq);
                Vector3 o = boss != null && !boss.Dead ? (boss.flashRenderer != null ? boss.flashRenderer.transform.position : boss.transform.position) : muzzle;
                for (int i = 0; i < beams; i++)
                {
                    float x;
                    switch (a.order)
                    {
                        case ShotOrder.LeftToRight: x = Mathf.Lerp(xMin - 0.8f, xMax + 0.8f, p); break;
                        case ShotOrder.RightToLeft: x = Mathf.Lerp(xMax + 0.8f, xMin - 0.8f, p); break;
                        case ShotOrder.CenterOut: x = Mathf.Lerp(c.x, i == 0 ? xMin - 0.8f : xMax + 0.8f, p); break;
                        case ShotOrder.OutsideIn: x = Mathf.Lerp(i == 0 ? xMin - 0.8f : xMax + 0.8f, c.x, p); break;
                        default:
                            tracked = Mathf.Min(tracked, sq.VisibleCount - 1);
                            trackX = Mathf.MoveTowards(trackX, sq.SlotWorld(tracked).x, a.homing * Time.deltaTime); x = trackX; break;
                    }
                    Vector3 target = new Vector3(x, c.y, c.z);
                    float wob = 1f + 0.15f * Mathf.Sin(Time.time * 40f);
                    if (lines[i] != null) { lines[i].SetPosition(0, o); lines[i].SetPosition(1, target); lines[i].widthMultiplier = a.beamWidth * wob * Mathf.Clamp01(Mathf.Min(t, a.duration - t) * 6f + 0.2f); }
                    if (a.fx != null && objs[i] != null) { objs[i].transform.position = o; Vector3 d = target - o; if (d.sqrMagnitude > 0.01f) objs[i].transform.rotation = Quaternion.LookRotation(d); }
                    if (marks[i] != null) marks[i].transform.position = target;
                    if (tickT >= a.tick)
                    {
                        int near; int hit = Inside(sq, target, a.radius, out near);
                        if (hit > 0) Hurt(sq, 1, near, b);
                    }
                }
                if (tickT >= a.tick) tickT = 0f;
                if (a.shake > 0f && FXManager.I != null && Random.value < 0.25f) FXManager.I.Shake(a.shake * 0.4f);
                yield return null;
            }
            for (int i = 0; i < beams; i++) { if (objs[i] != null) Object.Destroy(objs[i], a.fx != null ? 1.2f : 0f); if (marks[i] != null) Object.Destroy(marks[i], 1f); }
            foreach (var o in objs) if (o != null) foreach (var ps in o.GetComponentsInChildren<ParticleSystem>(true)) { var em = ps.emission; em.enabled = false; }
        }
    }
}
