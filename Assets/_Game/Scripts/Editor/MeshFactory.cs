// MeshFactory.cs (Editor only)
// Builds low-poly placeholder meshes in code: planes, enemy units, the zeppelin, gates.
// Every face has its own vertices so the models render flat-shaded. These get replaced
// by real Blender models later; the prefabs keep the same names and scripts.
using System.Collections.Generic;
using UnityEngine;

namespace SkySquad.EditorTools
{
    public class MeshBuilder
    {
        readonly List<Vector3> verts = new List<Vector3>();
        readonly List<int>[] tris;
        public MeshBuilder(int submeshes) { tris = new List<int>[submeshes]; for (int i = 0; i < submeshes; i++) tris[i] = new List<int>(); }

        /// <summary>Quad from four corners; winding is fixed automatically to face 'normal'.</summary>
        public void Quad(Vector3 a, Vector3 b, Vector3 c, Vector3 d, Vector3 normal, int sub)
        {
            if (Vector3.Dot(Vector3.Cross(b - a, c - a), normal) < 0f) { var t = b; b = d; d = t; }
            int i = verts.Count;
            verts.Add(a); verts.Add(b); verts.Add(c); verts.Add(d);
            tris[sub].AddRange(new[] { i, i + 1, i + 2, i, i + 2, i + 3 });
        }

        /// <summary>Box whose +z face is scaled by 'front' and -z face by 'back' (1 = plain box).</summary>
        public void Box(Vector3 c, Vector3 size, int sub, float front = 1f, float back = 1f, Quaternion? rot = null)
        {
            Vector3 h = size * 0.5f;
            Vector3 P(float x, float y, float z)
            {
                float s = z > 0 ? front : back;
                var p = new Vector3(x * h.x * s, y * h.y * s, z * h.z);
                if (rot.HasValue) p = rot.Value * p;
                return c + p;
            }
            Vector3 R(Vector3 n) => rot.HasValue ? rot.Value * n : n;
            Quad(P(-1, -1, 1), P(1, -1, 1), P(1, 1, 1), P(-1, 1, 1), R(Vector3.forward), sub);
            Quad(P(-1, -1, -1), P(1, -1, -1), P(1, 1, -1), P(-1, 1, -1), R(Vector3.back), sub);
            Quad(P(-1, 1, -1), P(1, 1, -1), P(1, 1, 1), P(-1, 1, 1), R(Vector3.up), sub);
            Quad(P(-1, -1, -1), P(1, -1, -1), P(1, -1, 1), P(-1, -1, 1), R(Vector3.down), sub);
            Quad(P(1, -1, -1), P(1, 1, -1), P(1, 1, 1), P(1, -1, 1), R(Vector3.right), sub);
            Quad(P(-1, -1, -1), P(-1, 1, -1), P(-1, 1, 1), P(-1, -1, 1), R(Vector3.left), sub);
        }

        public void Ellipsoid(Vector3 c, Vector3 r, int segs, int rings, int sub)
        {
            Vector3 P(int i, int j)
            {
                float u = i / (float)segs * Mathf.PI * 2f, v = j / (float)rings * Mathf.PI;
                return c + new Vector3(Mathf.Sin(v) * Mathf.Cos(u) * r.x, Mathf.Cos(v) * r.y, Mathf.Sin(v) * Mathf.Sin(u) * r.z);
            }
            for (int j = 0; j < rings; j++)
                for (int i = 0; i < segs; i++)
                {
                    Vector3 a = P(i, j), b = P(i + 1, j), cc = P(i + 1, j + 1), d = P(i, j + 1);
                    Vector3 n = ((a + b + cc + d) / 4f - c);
                    Quad(a, b, cc, d, n, sub);
                }
        }

        /// <summary>Top half of an ellipsoid (a parachute canopy), open underneath.</summary>
        public void Dome(Vector3 c, Vector3 r, int segs, int rings, int sub)
        {
            Vector3 P(int i, int j)
            {
                float u = i / (float)segs * Mathf.PI * 2f, v = j / (float)rings * Mathf.PI * 0.5f;
                return c + new Vector3(Mathf.Sin(v) * Mathf.Cos(u) * r.x, Mathf.Cos(v) * r.y, Mathf.Sin(v) * Mathf.Sin(u) * r.z);
            }
            for (int j = 0; j < rings; j++)
                for (int i = 0; i < segs; i++)
                {
                    Vector3 a = P(i, j), b = P(i + 1, j), cc = P(i + 1, j + 1), d = P(i, j + 1);
                    Vector3 n = ((a + b + cc + d) / 4f - c);
                    Quad(a, b, cc, d, n, sub);
                }
        }

        public Mesh Build(string name)
        {
            var m = new Mesh { name = name };
            m.SetVertices(verts);
            m.subMeshCount = tris.Length;
            for (int i = 0; i < tris.Length; i++) m.SetTriangles(tris[i], i);
            m.RecalculateNormals();
            m.RecalculateBounds();
            return m;
        }
    }

    public static class MeshFactory
    {
        // submesh 0 = body, 1 = accent, 2 = glass/glow
        public static Mesh Plane(string style)
        {
            var b = new MeshBuilder(3);
            if (style == "jet")
            {
                b.Box(new Vector3(0, 0, 0.02f), new Vector3(0.24f, 0.2f, 1.25f), 0, 0.35f, 0.75f);
                b.Box(new Vector3(0, -0.02f, -0.18f), new Vector3(1.3f, 0.05f, 0.62f), 0, 0.12f, 1f);   // delta wing
                b.Box(new Vector3(0, 0.13f, -0.45f), new Vector3(0.04f, 0.24f, 0.28f), 1, 1f, 0.5f);  // fin
                b.Box(new Vector3(0, 0.09f, 0.18f), new Vector3(0.15f, 0.1f, 0.34f), 2, 0.6f, 0.9f);  // canopy
                b.Box(new Vector3(0, 0, -0.62f), new Vector3(0.16f, 0.14f, 0.08f), 2);                // exhaust glow
                b.Box(new Vector3(-0.45f, -0.02f, -0.35f), new Vector3(0.14f, 0.03f, 0.2f), 1); b.Box(new Vector3(0.45f, -0.02f, -0.35f), new Vector3(0.14f, 0.03f, 0.2f), 1);
            }
            else if (style == "fighter")
            {   // the squad's plane: chunky and friendly. Fat rounded fuselage, round blue cowl, wide wing with blue tips,
                // a big canopy, a tall fin - it is seen from behind and above, so the top surfaces carry the colour.
                b.Box(new Vector3(0, 0, -0.04f), new Vector3(0.34f, 0.34f, 1.15f), 0, 0.95f, 0.5f);      // fuselage, tapering to the tail
                b.Ellipsoid(new Vector3(0, -0.02f, 0.05f), new Vector3(0.2f, 0.22f, 0.5f), 10, 5, 0);   // belly: rounds the body out
                b.Ellipsoid(new Vector3(0, 0, 0.55f), new Vector3(0.2f, 0.2f, 0.2f), 12, 6, 1);          // round blue cowl
                b.Box(new Vector3(0, 0, 0.42f), new Vector3(0.38f, 0.38f, 0.1f), 1);                     // blue ring behind it
                b.Box(new Vector3(0, -0.04f, 0.05f), new Vector3(1.6f, 0.08f, 0.44f), 0, 0.7f, 1f);      // wing: wide, tapered leading edge
                b.Box(new Vector3(-0.66f, -0.04f, 0.05f), new Vector3(0.28f, 0.1f, 0.46f), 1);          // blue wing tips
                b.Box(new Vector3(0.66f, -0.04f, 0.05f), new Vector3(0.28f, 0.1f, 0.46f), 1);
                b.Box(new Vector3(-0.3f, 0.005f, 0.05f), new Vector3(0.08f, 0.09f, 0.46f), 1);          // blue stripes inboard
                b.Box(new Vector3(0.3f, 0.005f, 0.05f), new Vector3(0.08f, 0.09f, 0.46f), 1);
                b.Box(new Vector3(0, 0.04f, -0.5f), new Vector3(0.62f, 0.05f, 0.2f), 0);                 // tail plane
                b.Box(new Vector3(0, 0.22f, -0.48f), new Vector3(0.05f, 0.34f, 0.26f), 0, 1f, 0.5f);     // fin
                b.Box(new Vector3(0, 0.38f, -0.5f), new Vector3(0.07f, 0.08f, 0.2f), 1);                 // blue fin tip
                b.Box(new Vector3(0, 0.22f, 0.1f), new Vector3(0.22f, 0.16f, 0.42f), 2, 0.6f, 0.85f);    // canopy
                b.Box(new Vector3(-0.22f, -0.03f, 0.3f), new Vector3(0.04f, 0.04f, 0.22f), 1); b.Box(new Vector3(0.22f, -0.03f, 0.3f), new Vector3(0.04f, 0.04f, 0.22f), 1); // guns
            }
            else if (style == "attacker")
            {   // the rocket plane (crate 3): the fighter's family and size - same fat fuselage, round cowl and big canopy - but a
                // different plane: a wing swept back to arrow tips, rocket pods under it, and twin fins instead of one (requested:
                // "like the main plane but a different shape, the same size")
                b.Box(new Vector3(0, 0, -0.04f), new Vector3(0.34f, 0.34f, 1.15f), 0, 0.95f, 0.5f);      // fuselage, tapering to the tail
                b.Ellipsoid(new Vector3(0, -0.02f, 0.05f), new Vector3(0.2f, 0.22f, 0.5f), 10, 5, 0);   // belly
                b.Ellipsoid(new Vector3(0, 0, 0.55f), new Vector3(0.2f, 0.2f, 0.2f), 12, 6, 1);          // round cowl
                b.Box(new Vector3(0, 0, 0.42f), new Vector3(0.38f, 0.38f, 0.1f), 1);                     // ring behind it
                b.Box(new Vector3(-0.42f, -0.04f, 0.0f), new Vector3(0.84f, 0.08f, 0.5f), 0, 0.55f, 1f, Quaternion.Euler(0f, -18f, 0f));   // wing halves swept back (outer end toward the tail)
                b.Box(new Vector3(0.42f, -0.04f, 0.0f), new Vector3(0.84f, 0.08f, 0.5f), 0, 0.55f, 1f, Quaternion.Euler(0f, 18f, 0f));
                b.Box(new Vector3(-0.74f, -0.04f, -0.12f), new Vector3(0.16f, 0.1f, 0.3f), 1, 0.5f, 1f);  // arrow wing tips
                b.Box(new Vector3(0.74f, -0.04f, -0.12f), new Vector3(0.16f, 0.1f, 0.3f), 1, 0.5f, 1f);
                b.Box(new Vector3(-0.4f, -0.12f, 0.08f), new Vector3(0.11f, 0.11f, 0.5f), 1, 0.6f, 0.9f); // rocket pods under the wing
                b.Box(new Vector3(0.4f, -0.12f, 0.08f), new Vector3(0.11f, 0.11f, 0.5f), 1, 0.6f, 0.9f);
                b.Box(new Vector3(0, 0.04f, -0.5f), new Vector3(0.7f, 0.05f, 0.2f), 0);                  // tail plane
                b.Box(new Vector3(-0.3f, 0.18f, -0.5f), new Vector3(0.05f, 0.26f, 0.22f), 0, 1f, 0.5f);  // twin fins
                b.Box(new Vector3(0.3f, 0.18f, -0.5f), new Vector3(0.05f, 0.26f, 0.22f), 0, 1f, 0.5f);
                b.Box(new Vector3(-0.3f, 0.3f, -0.52f), new Vector3(0.07f, 0.07f, 0.16f), 1);            // fin tips
                b.Box(new Vector3(0.3f, 0.3f, -0.52f), new Vector3(0.07f, 0.07f, 0.16f), 1);
                b.Box(new Vector3(0, 0.22f, 0.05f), new Vector3(0.22f, 0.16f, 0.52f), 2, 0.6f, 0.85f);    // long canopy
            }
            else
            {
                b.Box(new Vector3(0, 0, 0), new Vector3(0.22f, 0.22f, 1.1f), 0, 0.5f, 0.7f);
                b.Box(new Vector3(0, -0.02f, 0.05f), new Vector3(1.3f, 0.05f, 0.32f), 0, 0.85f, 1f);
                b.Box(new Vector3(0, 0.02f, -0.45f), new Vector3(0.5f, 0.04f, 0.2f), 0);              // tail plane
                b.Box(new Vector3(0, 0.14f, -0.45f), new Vector3(0.04f, 0.22f, 0.22f), 1, 1f, 0.5f);  // fin
                b.Box(new Vector3(0, 0.14f, 0.15f), new Vector3(0.14f, 0.12f, 0.3f), 2, 0.6f, 0.9f);  // canopy
                b.Box(new Vector3(-0.5f, -0.02f, 0.05f), new Vector3(0.16f, 0.03f, 0.2f), 1); b.Box(new Vector3(0.5f, -0.02f, 0.05f), new Vector3(0.16f, 0.03f, 0.2f), 1); // wing stripes
                b.Box(new Vector3(-0.2f, -0.01f, 0.3f), new Vector3(0.03f, 0.03f, 0.18f), 1); b.Box(new Vector3(0.2f, -0.01f, 0.3f), new Vector3(0.03f, 0.03f, 0.18f), 1); // guns
            }
            return b.Build("Plane_" + style);
        }

        // submesh 0 = body, 1 = accent (cream bands), 2 = glass, 3 = cowl (dark). Designed to be read HEAD-ON, which is how
        // the player always sees it: a round dark engine cowl with a cream nose ring, a wide wing with a cream band on
        // each side, a canopy bump and a fin. (The old one showed as a yellow "+" with a red dot.)
        public static Mesh EnemyPlane()
        {
            var b = new MeshBuilder(4);
            b.Box(new Vector3(0, 0, -0.05f), new Vector3(0.62f, 0.66f, 1.5f), 0, 0.92f, 0.5f);     // fuselage: fat and tall, tapering to the tail
            b.Ellipsoid(new Vector3(0, -0.1f, 0.08f), new Vector3(0.36f, 0.4f, 0.72f), 12, 6, 0);   // big belly: rounds the body out under the wing
            b.Ellipsoid(new Vector3(0, 0, 0.66f), new Vector3(0.36f, 0.36f, 0.34f), 12, 6, 3);     // engine cowl: round, dark
            b.Box(new Vector3(0, 0, 0.5f), new Vector3(0.72f, 0.74f, 0.14f), 1);                  // cream nose ring behind the cowl
            b.Box(new Vector3(0, -0.06f, 0.05f), new Vector3(2.4f, 0.16f, 0.72f), 0, 0.7f, 1f);    // wing: wide, with a tapered leading edge
            b.Box(new Vector3(-0.78f, -0.06f, 0.05f), new Vector3(0.42f, 0.2f, 0.74f), 1);         // cream wing bands (bright dots head-on)
            b.Box(new Vector3(0.78f, -0.06f, 0.05f), new Vector3(0.42f, 0.2f, 0.74f), 1);
            b.Box(new Vector3(0, 0.06f, -0.66f), new Vector3(1.0f, 0.08f, 0.3f), 0);               // tail plane
            b.Box(new Vector3(0, 0.36f, -0.62f), new Vector3(0.08f, 0.5f, 0.38f), 0, 1f, 0.5f);    // fin
            b.Box(new Vector3(0, 0.6f, -0.66f), new Vector3(0.1f, 0.1f, 0.3f), 1);                 // cream fin tip
            b.Box(new Vector3(0, 0.4f, 0.12f), new Vector3(0.34f, 0.24f, 0.56f), 2, 0.6f, 0.85f); // canopy
            b.Box(new Vector3(-0.42f, -0.1f, 0.4f), new Vector3(0.07f, 0.07f, 0.4f), 3);           // guns (dark)
            b.Box(new Vector3(0.42f, -0.1f, 0.4f), new Vector3(0.07f, 0.07f, 0.4f), 3);
            return b.Build("EnemyPlane");
        }

        /// <summary>The boss: a heavy four-engine gunship. Submeshes: 0 body (slate), 1 accent (orange bands), 2 glass
        /// (glazed nose, canopy), 3 dark (cowls, turret, guns), 4 glow (gun tips, exhausts). Built in fighter units:
        /// EnemyKindDef.scale (3.2) makes it about 7.5 wide and 9 long.</summary>
        public static Mesh BossPlane()
        {
            var b = new MeshBuilder(5);
            // fuselage: a long slab tapering to the tail, a round belly, a glazed bomber nose, orange rings fore and aft
            b.Box(new Vector3(0, 0.02f, -0.15f), new Vector3(0.72f, 0.66f, 2.0f), 0, 0.8f, 0.42f);      // ends at z 0.85, inside the round nose collar
            b.Ellipsoid(new Vector3(0, -0.1f, 0.2f), new Vector3(0.44f, 0.4f, 0.95f), 14, 7, 0);
            b.Ellipsoid(new Vector3(0, 0.01f, 0.9f), new Vector3(0.33f, 0.31f, 0.24f), 14, 7, 3);    // round dark nose socket: no flat face head-on
            b.Ellipsoid(new Vector3(0, 0.0f, 1.04f), new Vector3(0.25f, 0.23f, 0.3f), 12, 6, 2);     // glazed nose, smaller than the body
            b.Ellipsoid(new Vector3(0, 0.01f, 0.82f), new Vector3(0.37f, 0.35f, 0.12f), 14, 7, 1);   // round orange nose collar
            b.Box(new Vector3(-0.37f, 0.12f, -0.1f), new Vector3(0.04f, 0.1f, 1.7f), 1, 0.9f, 0.6f);   // cheat lines along the flanks
            b.Box(new Vector3(0.37f, 0.12f, -0.1f), new Vector3(0.04f, 0.1f, 1.7f), 1, 0.9f, 0.6f);
            b.Box(new Vector3(0, 0.02f, -0.5f), new Vector3(0.7f, 0.64f, 0.14f), 1);
            b.Box(new Vector3(0, 0.42f, 0.4f), new Vector3(0.4f, 0.22f, 0.6f), 2, 0.6f, 0.85f);     // cockpit canopy
            // dorsal turret with twin guns
            b.Ellipsoid(new Vector3(0, 0.4f, -0.2f), new Vector3(0.2f, 0.15f, 0.2f), 10, 5, 3);
            b.Box(new Vector3(-0.07f, 0.44f, 0.05f), new Vector3(0.05f, 0.05f, 0.44f), 3);
            b.Box(new Vector3(0.07f, 0.44f, 0.05f), new Vector3(0.05f, 0.05f, 0.44f), 3);
            // chin gun pod: the boss's guns, their tips glowing (the muzzle flash sits just ahead of them)
            b.Box(new Vector3(0, -0.34f, 0.75f), new Vector3(0.3f, 0.16f, 0.5f), 3, 0.8f, 1f);
            b.Box(new Vector3(-0.09f, -0.34f, 1.1f), new Vector3(0.05f, 0.05f, 0.4f), 3);
            b.Box(new Vector3(0.09f, -0.34f, 1.1f), new Vector3(0.05f, 0.05f, 0.4f), 3);
            b.Box(new Vector3(-0.09f, -0.34f, 1.32f), new Vector3(0.07f, 0.07f, 0.06f), 4);
            b.Box(new Vector3(0.09f, -0.34f, 1.32f), new Vector3(0.07f, 0.07f, 0.06f), 4);
            // wing: wide with a tapered leading edge, orange tips, four engine nacelles with cowl rings and exhaust glow
            b.Box(new Vector3(0, -0.06f, 0.08f), new Vector3(2.35f, 0.14f, 0.86f), 0, 0.62f, 1f);
            b.Box(new Vector3(-1.0f, -0.06f, 0.08f), new Vector3(0.36f, 0.16f, 0.8f), 1, 0.7f, 1f);   // painted tips
            b.Box(new Vector3(1.0f, -0.06f, 0.08f), new Vector3(0.36f, 0.16f, 0.8f), 1, 0.7f, 1f);
            foreach (float x in new[] { -0.9f, -0.48f, 0.48f, 0.9f })
            {
                b.Ellipsoid(new Vector3(x, -0.1f, 0.28f), new Vector3(0.16f, 0.16f, 0.5f), 12, 6, 3);   // nacelle
                b.Ellipsoid(new Vector3(x, -0.1f, 0.6f), new Vector3(0.2f, 0.2f, 0.12f), 12, 6, 1);     // round orange cowl ring
                b.Box(new Vector3(x, -0.18f, -0.17f), new Vector3(0.07f, 0.05f, 0.1f), 4);
            }
            // tail: a wide plane, twin fins with orange tips, a tail gun
            b.Box(new Vector3(0, 0.12f, -1.0f), new Vector3(1.5f, 0.08f, 0.44f), 0, 0.85f, 1f);
            foreach (float x in new[] { -0.7f, 0.7f })
            {
                b.Box(new Vector3(x, 0.38f, -1.02f), new Vector3(0.08f, 0.5f, 0.42f), 0, 1f, 0.55f);
                b.Box(new Vector3(x, 0.62f, -1.06f), new Vector3(0.1f, 0.1f, 0.36f), 1);
            }
            b.Box(new Vector3(0, 0.04f, -1.24f), new Vector3(0.16f, 0.14f, 0.22f), 3);
            b.Box(new Vector3(0, 0.04f, -1.38f), new Vector3(0.06f, 0.06f, 0.1f), 4);
            return b.Build("BossPlane");
        }

        /// <summary>A stubby slug, long axis along +z (the bullet looks down its own flight path).</summary>
        public static Mesh Bullet()
        {
            var b = new MeshBuilder(1);
            b.Ellipsoid(Vector3.zero, new Vector3(0.11f, 0.11f, 0.32f), 8, 5, 0);
            return b.Build("Bullet");
        }

        /// <summary>A fat gold disc, flat along z so it faces the camera as it tumbles.</summary>
        public static Mesh Coin()
        {
            var b = new MeshBuilder(1);
            b.Ellipsoid(Vector3.zero, new Vector3(0.3f, 0.3f, 0.08f), 12, 5, 0);
            return b.Build("Coin");
        }

        // submesh 0 = hub + thin blades, 1 = the translucent spin disc (a running prop reads as a faint disc, not a solid cross)
        public static Mesh Propeller()
        {
            var b = new MeshBuilder(2);
            b.Box(Vector3.zero, new Vector3(0.62f, 0.035f, 0.02f), 0);
            b.Box(Vector3.zero, new Vector3(0.035f, 0.62f, 0.02f), 0);
            b.Box(Vector3.zero, new Vector3(0.1f, 0.1f, 0.06f), 0);
            b.Ellipsoid(Vector3.zero, new Vector3(0.31f, 0.31f, 0.006f), 16, 4, 1);
            return b.Build("Propeller");
        }

        public static Mesh Drone()
        {
            var b = new MeshBuilder(3);
            b.Ellipsoid(Vector3.zero, new Vector3(0.42f, 0.36f, 0.42f), 10, 6, 0);
            b.Box(new Vector3(0, 0, 0.3f), new Vector3(0.22f, 0.16f, 0.24f), 2, 0.5f, 1f);              // eye
            for (int i = 0; i < 4; i++)
            {
                float a = (i + 0.5f) * Mathf.PI / 2f;
                var arm = new Vector3(Mathf.Cos(a) * 0.55f, 0.1f, Mathf.Sin(a) * 0.55f);
                b.Box(arm * 0.6f, new Vector3(0.5f, 0.06f, 0.08f), 1, 1f, 1f, Quaternion.Euler(0, -a * Mathf.Rad2Deg, 0));
                b.Box(arm + Vector3.up * 0.08f, new Vector3(0.5f, 0.02f, 0.14f), 2);                    // rotor blur
            }
            return b.Build("Drone");
        }

        public static Mesh Zeppelin()
        {
            var b = new MeshBuilder(3);
            b.Ellipsoid(Vector3.zero, new Vector3(4.4f, 2.2f, 7.5f), 16, 10, 0);
            b.Box(new Vector3(0, -2.4f, -0.5f), new Vector3(2.2f, 0.9f, 3.2f), 1, 0.8f, 0.9f);           // gondola
            b.Box(new Vector3(0, 1.6f, -6.2f), new Vector3(0.2f, 3.2f, 2.6f), 1, 0.4f, 1f);              // top fin
            b.Box(new Vector3(0, -1.2f, -6.2f), new Vector3(0.2f, 2.6f, 2.4f), 1, 0.4f, 1f);             // bottom fin
            b.Box(new Vector3(-3.0f, 0.2f, -6.2f), new Vector3(3.2f, 0.2f, 2.6f), 1, 0.4f, 1f);          // side fins
            b.Box(new Vector3(3.0f, 0.2f, -6.2f), new Vector3(3.2f, 0.2f, 2.6f), 1, 0.4f, 1f);
            b.Box(new Vector3(0, 0.2f, 7.2f), new Vector3(2.4f, 2.4f, 0.4f), 2);                          // skull plate
            b.Box(new Vector3(-0.6f, 0.5f, 7.45f), new Vector3(0.5f, 0.55f, 0.1f), 1); b.Box(new Vector3(0.6f, 0.5f, 7.45f), new Vector3(0.5f, 0.55f, 0.1f), 1); // eyes
            b.Box(new Vector3(0, -0.45f, 7.45f), new Vector3(1.3f, 0.35f, 0.1f), 1);                     // teeth bar
            return b.Build("Zeppelin");
        }

        public static Mesh GateFrame(float halfW, float height)
        {
            var b = new MeshBuilder(1);
            float t = 0.22f;
            b.Box(new Vector3(-halfW, height / 2f, 0), new Vector3(t, height + t, t), 0);
            b.Box(new Vector3(halfW, height / 2f, 0), new Vector3(t, height + t, t), 0);
            b.Box(new Vector3(0, height, 0), new Vector3(halfW * 2f + t, t, t), 0);
            b.Box(new Vector3(0, 0, 0), new Vector3(halfW * 2f + t, t, t), 0);
            b.Box(new Vector3(-halfW, height + 0.25f, 0), new Vector3(0.36f, 0.36f, 0.36f), 0);
            b.Box(new Vector3(halfW, height + 0.25f, 0), new Vector3(0.36f, 0.36f, 0.36f), 0);
            return b.Build("GateFrame");
        }

        public static Mesh Panel(float halfW, float height)
        {
            var b = new MeshBuilder(1);
            b.Quad(new Vector3(-halfW, 0, 0), new Vector3(halfW, 0, 0), new Vector3(halfW, height, 0), new Vector3(-halfW, height, 0), Vector3.back, 0);
            b.Quad(new Vector3(-halfW, 0, 0), new Vector3(halfW, 0, 0), new Vector3(halfW, height, 0), new Vector3(-halfW, height, 0), Vector3.forward, 0);
            return b.Build("GatePanel");
        }

        // submesh 0 = crate, 1 = bands + cords, 2 = parachute canopy (tinted per crate kind at runtime)
        public static Mesh Crate()
        {
            var b = new MeshBuilder(3);
            b.Box(Vector3.zero, new Vector3(1.7f, 1.5f, 1.7f), 0);
            b.Box(Vector3.zero, new Vector3(1.76f, 0.16f, 1.76f), 1);
            b.Box(new Vector3(0, 0.62f, 0), new Vector3(1.76f, 0.12f, 1.76f), 1);
            b.Box(new Vector3(0, -0.62f, 0), new Vector3(1.76f, 0.12f, 1.76f), 1);
            for (int i = 0; i < 4; i++)
            {
                float sx = (i & 1) == 0 ? -0.5f : 0.5f, sz = (i & 2) == 0 ? -0.5f : 0.5f;
                b.Box(new Vector3(sx, 1.1f, sz), new Vector3(0.05f, 0.7f, 0.05f), 1);              // cords
            }
            b.Dome(new Vector3(0, 1.4f, 0), new Vector3(1.7f, 0.65f, 1.7f), 14, 4, 2);
            return b.Build("Crate");
        }

        // submesh 0 = envelope, 1 = fins/cables, 2 = the crate slung underneath
        public static Mesh Blimp()
        {
            var b = new MeshBuilder(3);
            b.Ellipsoid(Vector3.zero, new Vector3(1.15f, 0.85f, 2.2f), 12, 8, 0);
            b.Box(new Vector3(0, 0.55f, -1.9f), new Vector3(0.12f, 1.1f, 0.9f), 1, 0.4f, 1f);      // top fin
            b.Box(new Vector3(-0.9f, 0.05f, -1.9f), new Vector3(1.1f, 0.1f, 0.9f), 1, 0.4f, 1f);  // side fins
            b.Box(new Vector3(0.9f, 0.05f, -1.9f), new Vector3(1.1f, 0.1f, 0.9f), 1, 0.4f, 1f);
            b.Box(new Vector3(-0.3f, -0.95f, 0.1f), new Vector3(0.05f, 0.5f, 0.05f), 1);           // cables
            b.Box(new Vector3(0.3f, -0.95f, 0.1f), new Vector3(0.05f, 0.5f, 0.05f), 1);
            b.Box(new Vector3(0, -1.6f, 0.1f), new Vector3(1.0f, 0.85f, 1.0f), 2);                 // crate
            return b.Build("Blimp");
        }

        public static Mesh Rocket()
        {
            var b = new MeshBuilder(2);
            b.Box(Vector3.zero, new Vector3(0.14f, 0.14f, 0.5f), 0, 0.2f, 1f);
            b.Box(new Vector3(0, 0, -0.2f), new Vector3(0.34f, 0.04f, 0.12f), 1);
            b.Box(new Vector3(0, 0, -0.2f), new Vector3(0.04f, 0.34f, 0.12f), 1);
            return b.Build("Rocket");
        }

        public static Mesh Buoy()
        {
            var b = new MeshBuilder(2);
            b.Ellipsoid(Vector3.zero, new Vector3(0.5f, 0.5f, 0.5f), 8, 5, 0);
            b.Box(new Vector3(0, 0.55f, 0), new Vector3(0.12f, 0.6f, 0.12f), 1);
            return b.Build("Buoy");
        }
    }
}
