// BossKit.cs (Editor only)
// The kit the 24 procedural bosses are bashed together from (2026-09-30: "30 bosses, every one different, take one thing from
// each boss and make another"). A boss = one HULL + one pair of WINGS + one CROWN (a weapon or a trim), each a part borrowed from
// a different kind of shmup boss - the manta, the skull, the carrier, the halo... - plus his own colours and width. Eight of each
// make 512 bosses; the 24 combinations below never repeat a triple and never put the same hull on two neighbours.
// Submeshes match MeshFactory.BossPlane: 0 body, 1 accent, 2 glass, 3 dark, 4 glow. Nose is +Z, like every boss mesh.
using UnityEngine;

namespace SkySquad.EditorTools
{
    public static class BossKit
    {
        public const int Hulls = 8, Wings = 8, Crowns = 8;

        public struct Built { public Mesh mesh; public float noseZ; public float top; }

        /// <summary>Hull, wing and crown indices for the i-th procedural boss (0-based): a triple that never repeats.</summary>
        public static void Triple(int i, out int hull, out int wing, out int crown)
        {
            hull = i % Hulls;
            wing = (i * 3 + i / 8) % Wings;
            crown = (i * 5 + i / 8 * 3 + 1) % Crowns;
        }

        public static string HullName(int h) { return new[] { "dart", "orb", "manta", "block", "twin-pod", "skull-spine", "cross", "carrier" }[h]; }
        public static string WingName(int w) { return new[] { "straight", "forward-swept", "delta", "gull", "blades", "biplane", "drones", "crescent" }[w]; }
        public static string CrownName(int c) { return new[] { "dorsal guns", "chin cannon", "engine cluster", "shield dish", "horns", "sponsons", "halo", "missile hump" }[c]; }

        /// <summary>The boss mesh for a triple, scaled so his widest part is 'width' (fighter units; EnemyKindDef.scale then multiplies).</summary>
        public static Built Build(string name, int hull, int wing, int crown, float width)
        {
            var b = new MeshBuilder(5);
            float nose = Hull(b, hull);
            WingsOf(b, wing);
            nose += Crown(b, crown, nose);
            var m = b.Build(name);
            float k = width / Mathf.Max(0.5f, m.bounds.size.x);
            float len = m.bounds.size.z * k;
            if (len > 4.6f) k *= 4.6f / len;   // never a pole: the longest part keeps to the screen
            var v = m.vertices;
            var c = m.bounds.center;
            for (int i = 0; i < v.Length; i++) v[i] = new Vector3(v[i].x * k, v[i].y * k, (v[i].z - c.z) * k);   // centred on z, so he turns about his middle
            m.vertices = v;
            m.RecalculateBounds();
            return new Built { mesh = m, noseZ = (nose - c.z) * k, top = m.bounds.max.y };
        }

        static Quaternion Yaw(float d) { return Quaternion.Euler(0f, d, 0f); }
        static Quaternion Roll(float d) { return Quaternion.Euler(0f, 0f, d); }
        static Vector3 V(float x, float y, float z) { return new Vector3(x, y, z); }

        // ------------------------------------------------------------------ hulls: return where the nose ends
        static float Hull(MeshBuilder b, int h)
        {
            switch (h)
            {
                case 0:   // dart: a long tapering spear with a glazed canopy
                    b.Box(V(0, 0, -0.1f), V(0.62f, 0.5f, 2.4f), 0, 0.35f, 0.75f);
                    b.Ellipsoid(V(0, 0.02f, 1.15f), V(0.2f, 0.2f, 0.5f), 10, 5, 0);
                    b.Ellipsoid(V(0, 0.27f, 0.3f), V(0.25f, 0.2f, 0.55f), 10, 5, 2);
                    b.Box(V(0, 0.26f, -0.4f), V(0.12f, 0.05f, 1.3f), 1);
                    b.Box(V(0, 0, -1.35f), V(0.34f, 0.24f, 0.1f), 4);
                    return 1.65f;
                case 1:   // orb: a big armoured sphere with one huge eye
                    b.Ellipsoid(V(0, 0, 0), V(0.85f, 0.8f, 0.85f), 16, 8, 0);
                    b.Ellipsoid(V(0, 0, 0.3f), V(0.93f, 0.93f, 0.1f), 16, 4, 1);
                    b.Ellipsoid(V(0, 0.05f, 0.72f), V(0.42f, 0.38f, 0.22f), 12, 6, 2);
                    b.Ellipsoid(V(0, 0.05f, 0.9f), V(0.18f, 0.18f, 0.1f), 10, 5, 4);
                    b.Ellipsoid(V(0, 0, -0.5f), V(0.6f, 0.6f, 0.25f), 12, 5, 3);
                    return 1.05f;
                case 2:   // manta: a flat, wide ray with a dark mouth and two glowing eyes
                    b.Ellipsoid(V(0, 0, 0), V(1.2f, 0.2f, 1.05f), 16, 6, 0);
                    b.Box(V(0, 0.2f, -0.2f), V(0.14f, 0.12f, 1.3f), 1);
                    b.Ellipsoid(V(0, 0.16f, 0.3f), V(0.28f, 0.14f, 0.5f), 10, 5, 2);
                    b.Box(V(0, -0.02f, 0.95f), V(0.7f, 0.12f, 0.2f), 3);
                    b.Box(V(-0.35f, 0.1f, 1.0f), V(0.12f, 0.08f, 0.1f), 4);
                    b.Box(V(0.35f, 0.1f, 1.0f), V(0.12f, 0.08f, 0.1f), 4);
                    return 1.15f;
                case 3:   // block: a slab of armour with a bridge tower
                    b.Box(V(0, 0, 0), V(1.0f, 0.7f, 2.4f), 0, 0.85f, 1f);
                    b.Box(V(0, 0.36f, 0.4f), V(1.02f, 0.05f, 0.2f), 1);
                    b.Box(V(0, 0.36f, -0.5f), V(1.02f, 0.05f, 0.2f), 1);
                    b.Box(V(0, 0.6f, -0.5f), V(0.5f, 0.4f, 0.6f), 3);
                    b.Box(V(0, 0.68f, -0.24f), V(0.4f, 0.14f, 0.14f), 2);
                    b.Box(V(0, -0.1f, 1.3f), V(0.6f, 0.4f, 0.3f), 3);
                    b.Box(V(0, -0.1f, 1.5f), V(0.3f, 0.15f, 0.08f), 4);
                    return 1.6f;
                case 4:   // twin pod: two fat hulls joined by a bridge, one gun between
                    foreach (float x in new[] { -0.75f, 0.75f })
                    {
                        b.Ellipsoid(V(x, 0, 0.1f), V(0.4f, 0.4f, 1.2f), 12, 6, 0);
                        b.Ellipsoid(V(x, 0.2f, 0.7f), V(0.18f, 0.18f, 0.3f), 8, 4, 2);
                        b.Ellipsoid(V(x, 0, 0.55f), V(0.44f, 0.44f, 0.1f), 12, 4, 1);
                    }
                    b.Box(V(0, 0, -0.1f), V(1.1f, 0.22f, 0.6f), 0);
                    b.Box(V(0, -0.05f, 0.5f), V(0.14f, 0.14f, 1.0f), 3);
                    b.Box(V(0, -0.05f, 1.05f), V(0.1f, 0.1f, 0.08f), 4);
                    return 1.3f;
                case 5:   // skull-spine: a bony spine with ribs and a grinning skull
                    b.Box(V(0, 0, -0.2f), V(0.3f, 0.3f, 2.6f), 0);
                    for (int i = 0; i < 4; i++) b.Box(V(0, 0, -1.0f + i * 0.5f), V(1.3f - i * 0.28f, 0.12f, 0.14f), 1);
                    b.Ellipsoid(V(0, 0, 1.2f), V(0.4f, 0.35f, 0.4f), 12, 6, 0);
                    b.Box(V(-0.15f, 0.08f, 1.55f), V(0.1f, 0.1f, 0.06f), 4);
                    b.Box(V(0.15f, 0.08f, 1.55f), V(0.1f, 0.1f, 0.06f), 4);
                    b.Box(V(0, -0.22f, 1.3f), V(0.3f, 0.08f, 0.3f), 3);
                    b.Ellipsoid(V(0, 0, -1.5f), V(0.25f, 0.25f, 0.2f), 8, 4, 3);
                    b.Box(V(0, 0, -1.72f), V(0.16f, 0.16f, 0.06f), 4);
                    return 1.55f;
                case 6:   // cross: a plus-shaped hull with a glowing hub
                    b.Box(V(0, 0, 0), V(0.5f, 0.4f, 3.0f), 0, 0.5f, 0.8f);
                    b.Box(V(0, 0, 0.1f), V(2.4f, 0.3f, 0.5f), 0);
                    b.Ellipsoid(V(0, 0.1f, 0.1f), V(0.4f, 0.3f, 0.4f), 12, 6, 1);
                    b.Ellipsoid(V(0, 0.3f, 0.15f), V(0.2f, 0.14f, 0.2f), 8, 4, 2);
                    b.Box(V(-1.2f, 0, 0.1f), V(0.12f, 0.12f, 0.12f), 4);
                    b.Box(V(1.2f, 0, 0.1f), V(0.12f, 0.12f, 0.12f), 4);
                    b.Box(V(0, 0, 1.55f), V(0.12f, 0.12f, 0.12f), 4);
                    return 1.6f;
                default:  // carrier: a flat deck with an island and a dark hangar mouth
                    b.Box(V(0, 0, 0), V(1.7f, 0.3f, 2.4f), 0, 0.8f, 1f);
                    b.Box(V(0.55f, 0.4f, -0.4f), V(0.34f, 0.5f, 0.6f), 3);
                    b.Box(V(0.55f, 0.62f, -0.3f), V(0.28f, 0.1f, 0.3f), 2);
                    b.Box(V(-0.2f, 0.16f, 0.1f), V(0.08f, 0.02f, 2.0f), 1);
                    b.Box(V(0, -0.02f, 1.2f), V(0.9f, 0.2f, 0.1f), 3);
                    b.Box(V(-0.7f, 0.16f, 1.15f), V(0.1f, 0.04f, 0.1f), 4);
                    b.Box(V(0.7f, 0.16f, 1.15f), V(0.1f, 0.04f, 0.1f), 4);
                    return 1.3f;
            }
        }

        // ------------------------------------------------------------------ wings
        static void WingsOf(MeshBuilder b, int w)
        {
            switch (w)
            {
                case 0:   // straight
                    b.Box(V(0, -0.05f, 0), V(2.6f, 0.12f, 0.8f), 0, 0.62f, 1f);
                    b.Box(V(-1.1f, -0.05f, 0), V(0.4f, 0.14f, 0.75f), 1, 0.7f, 1f);
                    b.Box(V(1.1f, -0.05f, 0), V(0.4f, 0.14f, 0.75f), 1, 0.7f, 1f);
                    break;
                case 1:   // forward-swept
                    foreach (float s in new[] { -1f, 1f })
                    {
                        b.Box(V(s * 0.95f, -0.04f, 0.15f), V(1.4f, 0.1f, 0.55f), 0, 0.8f, 1f, Yaw(-s * 25f));
                        b.Box(V(s * 1.6f, -0.04f, 0.5f), V(0.4f, 0.12f, 0.4f), 1, 0.8f, 1f, Yaw(-s * 25f));
                    }
                    break;
                case 2:   // delta
                    b.Box(V(0, -0.05f, -0.3f), V(2.6f, 0.1f, 1.3f), 0, 0.15f, 1f);
                    b.Box(V(-0.95f, -0.02f, -0.6f), V(0.5f, 0.12f, 0.2f), 1);
                    b.Box(V(0.95f, -0.02f, -0.6f), V(0.5f, 0.12f, 0.2f), 1);
                    break;
                case 3:   // gull: up, then down
                    foreach (float s in new[] { -1f, 1f })
                    {
                        b.Box(V(s * 0.6f, 0.05f, 0f), V(1.0f, 0.1f, 0.7f), 0, 1f, 1f, Roll(s * 15f));
                        b.Box(V(s * 1.45f, -0.05f, 0f), V(0.9f, 0.1f, 0.6f), 1, 0.8f, 1f, Roll(-s * 25f));
                    }
                    break;
                case 4:   // blades: two vertical fins on top over a stub wing
                    b.Box(V(0, -0.05f, 0), V(1.7f, 0.08f, 0.6f), 0);
                    foreach (float s in new[] { -1f, 1f })
                    {
                        b.Box(V(s * 0.6f, 0.5f, -0.2f), V(0.08f, 0.95f, 0.9f), 0, 0.7f, 1f, Roll(-s * 14f));
                        b.Box(V(s * 0.72f, 1.0f, -0.2f), V(0.1f, 0.12f, 0.9f), 1);
                    }
                    break;
                case 5:   // biplane
                    b.Box(V(0, -0.15f, 0.1f), V(2.4f, 0.08f, 0.6f), 0);
                    b.Box(V(0, 0.3f, -0.2f), V(2.0f, 0.08f, 0.6f), 0);
                    foreach (float s in new[] { -1f, 1f })
                    {
                        b.Box(V(s * 0.9f, 0.08f, -0.05f), V(0.06f, 0.5f, 0.06f), 3);
                        b.Box(V(s * 1.15f, -0.15f, 0.1f), V(0.3f, 0.1f, 0.6f), 1);
                    }
                    break;
                case 6:   // drones: a pod out on each side on a strut
                    foreach (float s in new[] { -1f, 1f })
                    {
                        b.Ellipsoid(V(s * 1.5f, 0, 0.2f), V(0.28f, 0.22f, 0.6f), 10, 5, 0);
                        b.Ellipsoid(V(s * 1.5f, 0, 0.3f), V(0.32f, 0.26f, 0.08f), 10, 4, 1);
                        b.Box(V(s * 1.5f, 0, 0.8f), V(0.1f, 0.1f, 0.06f), 4);
                        b.Box(V(s * 0.9f, 0, 0.2f), V(1.0f, 0.06f, 0.1f), 3);
                    }
                    break;
                default:  // crescent: three steps back on each side
                    foreach (float s in new[] { -1f, 1f })
                    {
                        b.Box(V(s * 0.5f, 0, -0.1f), V(0.9f, 0.1f, 0.5f), 0);
                        b.Box(V(s * 1.15f, 0, -0.35f), V(0.6f, 0.1f, 0.5f), 0);
                        b.Box(V(s * 1.6f, 0, -0.7f), V(0.4f, 0.12f, 0.5f), 1);
                    }
                    break;
            }
        }

        // ------------------------------------------------------------------ crowns: return how far they push the muzzle forward
        static float Crown(MeshBuilder b, int c, float nose)
        {
            switch (c)
            {
                case 0:   // twin dorsal guns
                    b.Ellipsoid(V(0, 0.35f, -0.3f), V(0.22f, 0.16f, 0.22f), 10, 5, 3);
                    b.Box(V(-0.08f, 0.4f, 0.05f), V(0.05f, 0.05f, 0.5f), 3);
                    b.Box(V(0.08f, 0.4f, 0.05f), V(0.05f, 0.05f, 0.5f), 3);
                    b.Box(V(-0.08f, 0.4f, 0.32f), V(0.07f, 0.07f, 0.05f), 4);
                    b.Box(V(0.08f, 0.4f, 0.32f), V(0.07f, 0.07f, 0.05f), 4);
                    return 0f;
                case 1:   // chin cannon
                    b.Box(V(0, -0.35f, 0.7f), V(0.36f, 0.3f, 1.0f), 3);
                    b.Box(V(0, -0.35f, 1.4f), V(0.14f, 0.14f, 0.5f), 3);
                    b.Box(V(0, -0.35f, 1.68f), V(0.18f, 0.18f, 0.06f), 4);
                    return Mathf.Max(0f, 1.7f - nose);
                case 2:   // rear engine cluster
                    foreach (float x in new[] { -0.4f, 0f, 0.4f })
                    {
                        b.Ellipsoid(V(x, 0, -1.15f), V(0.18f, 0.18f, 0.3f), 8, 4, 3);
                        b.Box(V(x, 0, -1.45f), V(0.14f, 0.14f, 0.05f), 4);
                    }
                    b.Box(V(0, 0, -1.0f), V(1.2f, 0.12f, 0.2f), 1);
                    return 0f;
                case 3:   // shield: a broad plate slung under the nose (it stood in front of the whole face until it was lowered)
                    b.Ellipsoid(V(0, -0.42f, nose + 0.2f), V(0.8f, 0.3f, 0.08f), 14, 5, 1);
                    b.Box(V(-0.85f, -0.42f, nose + 0.2f), V(0.08f, 0.08f, 0.08f), 4);
                    b.Box(V(0.85f, -0.42f, nose + 0.2f), V(0.08f, 0.08f, 0.08f), 4);
                    return 0.5f;
                case 4:   // horns: a fan of spikes swept forward
                    for (int i = -2; i <= 2; i++)
                    {
                        b.Box(V(i * 0.26f, 0.15f, nose - 0.1f + 0.4f - Mathf.Abs(i) * 0.08f), V(0.07f, 0.07f, 0.8f - Mathf.Abs(i) * 0.15f), 3, 0.5f, 1f, Yaw(i * 7f));
                        b.Box(V(i * 0.26f, 0.15f, nose + 0.05f), V(0.12f, 0.12f, 0.12f), 1);
                    }
                    b.Box(V(0, 0.15f, nose + 0.85f), V(0.09f, 0.09f, 0.06f), 4);
                    return 0.7f;
                case 5:   // sponsons
                    foreach (float s in new[] { -1f, 1f })
                    {
                        b.Box(V(s * 0.85f, -0.2f, 0.3f), V(0.3f, 0.3f, 1.0f), 3);
                        b.Box(V(s * 0.85f, -0.2f, 1.0f), V(0.08f, 0.08f, 0.5f), 3);
                        b.Box(V(s * 0.85f, -0.2f, 1.28f), V(0.11f, 0.11f, 0.05f), 4);
                    }
                    return 0f;
                case 6:   // halo: a ring of plates standing round the hull, lit at every other one
                    for (int i = 0; i < 10; i++)
                    {
                        float a = i / 10f * Mathf.PI * 2f, cs = Mathf.Cos(a), sn = Mathf.Sin(a);
                        b.Box(V(cs * 1.0f, sn * 0.8f, -0.2f), V(0.5f, 0.1f, 0.14f), 1, 1f, 1f, Roll(a * Mathf.Rad2Deg + 90f));
                        if ((i & 1) == 0) b.Box(V(cs * 1.0f, sn * 0.8f, -0.05f), V(0.08f, 0.08f, 0.08f), 4);
                    }
                    return 0f;
                default:  // missile hump: a dorsal core flanked by two racks
                    b.Ellipsoid(V(0, 0.35f, 0), V(0.45f, 0.3f, 0.7f), 12, 5, 0);
                    b.Ellipsoid(V(0, 0.5f, 0), V(0.18f, 0.12f, 0.25f), 8, 4, 4);
                    foreach (float s in new[] { -1f, 1f })
                    {
                        b.Box(V(s * 0.5f, 0.25f, 0.1f), V(0.18f, 0.18f, 0.8f), 3);
                        b.Box(V(s * 0.5f, 0.25f, 0.55f), V(0.12f, 0.12f, 0.1f), 1);
                    }
                    return 0f;
            }
        }
    }
}
