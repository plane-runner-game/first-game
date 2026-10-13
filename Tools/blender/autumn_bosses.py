# Sky Squad, the autumn forest's five bosses (2026-10-10: "now for the autumn forest"): the acorn airship, the harvest scarecrow, the fox
# spirit, the royal stag and the pumpkin castle. Built from code like the other worlds' bosses (alien_bosses.py lends its Boss class and shapes).
# 2026-10-13, the five in play remade like the alien bosses (realistic details, scarier, the cartoon shape kept) and each given its own way to
# fly ("not wings for all of them - a special way for each boss"): the fox sky-runs on foxfire, the stag rides a whirlwind of leaves, the
# squirrel knight flies a maple-seed rotor, the scarecrow is carried by his crows, the oak king floats on the island he tore from the ground.
# Run: blender -b -P Tools/blender/autumn_bosses.py -- <out dir> [export] [ids,comma,separated]
# Conventions as alien_bosses.py: +Y nose, +Z up, +X right; "Prop*" spin about the nose, "Flap*" rock about the nose axis, "Sway*" about the
# wing axis ("SwayLeg0-3" a galloping leg: fore R, fore L, hind R, hind L), "Rotor*" spin fast about up, "Spin*" turn slowly about up, "Cloth" stays still without the outline, "Muzzle" is where his shots leave from.
import bpy, bmesh, math, sys, os, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
from enemy_planes import loft, sweep, lathe, box, hull, tube, mirror_x, airfoil
import alien_bosses as AB
from alien_bosses import Boss, xf, ball, pipe, cone, bez, torus, sheet, grow, ang, lerp_keys, spine_frames, body_loft, skin, oriented_ball

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ONLY = argv[2].split(",") if len(argv) > 2 and argv[2] else None

AUTUMN = {"Base": ((0.55, 0.30, 0.12), 0.45), "Belly": ((0.96, 0.92, 0.82), 0.35), "Accent": ((0.86, 0.36, 0.08), 0.45),
          "Trim": ((0.95, 0.72, 0.18), 0.55), "Glass": ((0.72, 0.12, 0.08), 0.45), "Dark": ((0.10, 0.06, 0.04), 0.4),
          "Glow": ((1.0, 0.70, 0.25), 0.5), "Metal": ((0.32, 0.45, 0.18), 0.4), "Lamp": ((1.0, 0.82, 0.40), 0.8)}


def pal(**over):
    p = dict(AUTUMN); p.update(over); return p

def leaf_outline(c, size, u, v, n=30):
    """a maple leaf's outline in the plane of u (across) and v (up the leaf), about c."""
    c, u, v = Vector(c), Vector(u), Vector(v)
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        r = size * (0.55 + 0.35 * max(0.0, math.cos(5 * (a - math.pi / 2))) ** 0.6 + 0.12 * math.cos(10 * (a - math.pi / 2)))
        if math.sin(a) < -0.6: r *= 0.55   # the stalk end is narrow
        pts.append(c + u * math.cos(a) * r + v * math.sin(a) * r)
    return pts

def leaf(c, size, u, v, thick=0.02):
    outline = leaf_outline(c, size, u, v)
    polys = [[Vector(c), a, b] for a, b in zip(outline, outline[1:] + outline[:1])]
    return sheet([[tuple(p) for p in poly] for poly in polys], thick)

def pumpkin(c, r, h, ribs=10, seg=40, rings=12):
    """a ribbed pumpkin about c: radius r, height h."""
    bm = bmesh.new(); c = Vector(c); grid = []
    for j in range(rings + 1):
        t = j / rings; phi = math.pi * t
        z = -math.cos(phi) * h * 0.5; rr = math.sin(phi)
        row = []
        for i in range(seg):
            a = 2 * math.pi * i / seg
            k = r * rr * (1 - 0.08 * (0.5 - 0.5 * math.cos(ribs * a)))
            if j == 0 or j == rings: row.append(None); continue
            row.append(bm.verts.new(c + Vector((math.cos(a) * k, math.sin(a) * k, z * (1 - 0.1 * rr)))))
        grid.append(row)
    bot = bm.verts.new(c + Vector((0, 0, -h * 0.45))); top = bm.verts.new(c + Vector((0, 0, h * 0.42)))
    for j in range(1, rings - 1):
        for i in range(seg):
            i2 = (i + 1) % seg
            bm.faces.new((grid[j][i], grid[j][i2], grid[j + 1][i2], grid[j + 1][i]))
    for i in range(seg):
        i2 = (i + 1) % seg
        bm.faces.new((bot, grid[1][i2], grid[1][i]))
        bm.faces.new((top, grid[rings - 1][i], grid[rings - 1][i2]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


# ================================================================= 1. the acorn airship
def A_acorn():
    """A giant acorn flying as a balloon: the glossy nut hanging under its scaly cap, the stem on top, a wicker gondola below with lanterns,
    two propellers on outriggers, and maple-leaf sails in red, orange and gold spread from the cap."""
    P = Boss("acorn", pal())
    up = Matrix.Rotation(math.radians(-90), 3, "X")   # built lying along y, stood up: the cap on top, the tip down
    def stand(bm): return xf(bm, up, (0, 0, 0.6))
    P.obj("Nut", stand(lathe([(0.0, 2.0), (0.25, 1.85), (0.62, 1.45), (0.88, 0.85), (0.95, 0.2), (0.9, -0.3)], 22, "y")), "Accent", 1)
    def cap(c, n):
        a = math.atan2(c.x, c.y)
        return "Dark" if ((a * 3.0 + c.z * 4.0) % 1.0 < 0.12 or (a * 3.0 - c.z * 4.0) % 1.0 < 0.12) else "Base"
    P.obj("Cap", stand(lathe([(0.98, -0.25), (1.05, -0.4), (0.98, -0.75), (0.75, -1.05), (0.4, -1.22), (0.0, -1.27)], 22, "y")), cap, 1)
    P.obj("Stem", pipe(bez((0, 0, 1.85), (0, 0.05, 2.1), (0.1, 0.1, 2.3), (0.25, 0.1, 2.4), 5), [0.11, 0.1, 0.09, 0.08, 0.07, 0.06], 8), "Dark")
    P.obj("Tip", cone((0, 0, -1.35), (0, 0, -1.6), 0.1, 8), "Dark", 0, False)
    # the gondola hanging below the tip
    P.obj("Gondola", loft([(0.75, 0.1, 0.1, 0, -2.05), (0.55, 0.42, 0.22, 0, -2.0), (-0.45, 0.42, 0.22, 0, -2.0), (-0.65, 0.12, 0.12, 0, -1.95)], 14, sq=1.6),
          lambda c, n: "Trim" if (c.y * 6 + c.z * 6) % 1.0 < 0.5 else "Base", 1)
    for s in (1, -1):
        for y in (0.45, -0.35):
            P.obj("Rope", pipe([(s * 0.35, y, -1.85), (s * 0.55, y * 0.8, -0.6)], [0.015, 0.015], 4), "Dark")
        P.obj("Lantern", ball((s * 0.4, 0.65, -1.92), (0.07, 0.07, 0.09), 8, 4), "Lamp")
        P.obj("Outrigger", pipe([(s * 0.8, 0.0, 0.0), (s * 1.4, 0.05, -0.1)], [0.04, 0.04], 6), "Dark")
        P.obj("Pod", loft([(0.55, 0.06, 0.06, s * 1.45, -0.1), (0.4, 0.15, 0.15, s * 1.45, -0.1), (-0.2, 0.13, 0.13, s * 1.45, -0.1), (-0.35, 0.04, 0.04, s * 1.45, -0.1)], 12), "Base", 1)
        P.prop((s * 1.45, 0.6, -0.1), 0.42, 4, blade="Trim", tip="Accent", spinner="Dark", spinner_len=0.12)
        for k, col in enumerate(("Glass", "Trim")):   # leaf sails spread from the cap
            P.part("Cloth", leaf((s * (1.2 + 0.35 * k), -0.1 - 0.1 * k, 1.35 + 0.35 * k), 0.4 - 0.08 * k, (s * 0.9, -0.3, 0.3), (s * 0.3, 0, 1)), col, (0, 0, 0), 0, False)
    P.part("Cloth", leaf((0, -0.45, 2.15), 0.38, (1, 0, 0), (0, -0.4, 1)), "Accent", (0, 0, 0), 0, False)
    P.part("Muzzle", ball((0, 0.85, -2.0), (0.07, 0.04, 0.07), 8, 4), "Glow", (0, 0.85, -2.0))
    return P


# ================================================================= 2. the harvest scarecrow
def A_scarecrow():
    """A scarecrow flying on his pole: a carved pumpkin head with a glowing grin under a battered straw hat, a red patched shirt, arms
    spread along the crossbar with straw bursting from the cuffs, tattered coat tails, a crow on the bar and more crows circling him."""
    P = Boss("scarecrow", pal(Glass=((0.62, 0.12, 0.10), 0.35), Metal=((0.20, 0.30, 0.55), 0.35)))
    P.obj("Head", pumpkin((0, 0.0, 1.25), 0.45, 0.72), "Accent", 1)
    P.obj("Stalk", pipe([(0, 0, 1.55), (0.05, 0.02, 1.68)], [0.06, 0.05], 6), "Metal")
    for s in (1, -1):   # the carved eyes
        P.obj("EyeGlow", hull([(s * 0.1, 0.42, 1.38), (s * 0.28, 0.4, 1.38), (s * 0.19, 0.43, 1.5), (s * 0.19, 0.38, 1.44)]), "Glow", 0, False)
    P.obj("Nose", hull([(-0.05, 0.45, 1.25), (0.05, 0.45, 1.25), (0, 0.47, 1.33), (0, 0.42, 1.28)]), "Glow", 0, False)
    pts = [(x, 0.44 - abs(x) * 0.25, 1.1 + (0.05 if int((x + 0.3) * 13) % 2 else 0.0) + x * x * 0.6) for x in [i / 10 * 0.6 - 0.3 for i in range(11)]]
    P.obj("Grin", pipe(pts, [0.035] * len(pts), 5), "Glow")
    # the straw hat
    P.obj("Brim", lathe([(0.0, 1.55), (0.62, 1.52), (0.66, 1.48), (0.0, 1.58)], 20, "z", (0, -0.02, 0)), "Trim")
    P.obj("Crown", lathe([(0.3, 1.55), (0.26, 1.82), (0.1, 1.92), (0.0, 1.9)], 16, "z", (0.03, -0.04, 0)), "Trim")
    P.obj("Band", lathe([(0.305, 1.56), (0.29, 1.63), (0.0, 1.63)], 16, "z", (0.03, -0.04, 0)), "Glass")
    # the body and the crossbar
    P.obj("Pole", pipe([(0, -0.1, -1.4), (0, -0.1, 1.0)], [0.07, 0.07], 8), "Base")
    P.obj("Bar", pipe([(-1.5, -0.12, 0.75), (1.5, -0.12, 0.75)], [0.06, 0.06], 8), "Base")
    P.obj("Shirt", ball((0, 0.0, 0.45), (0.45, 0.32, 0.5), 14, 7), lambda c, n: "Metal" if ((c.x * 4) % 1.0 < 0.15 or (c.z * 4) % 1.0 < 0.15) else "Glass", 1)
    P.obj("Patch", box((0.15, 0.3, 0.55), (0.16, 0.03, 0.16)), "Trim", 0, False)
    P.obj("Rope", torus(0.4, 0.035, 0.0, 16, 4), "Trim"); P.parts[-1].data.transform(Matrix.Translation((0, 0.0, 0.08)))
    for s in (1, -1):
        P.obj("Sleeve", pipe([(s * 0.35, 0, 0.75), (s * 1.1, -0.05, 0.75)], [0.17, 0.14], 10), lambda c, n: "Glass" if (c.x * 3) % 1.0 > 0.2 else "Metal", 1)
        for k in range(6):   # straw from the cuffs
            a = 2 * math.pi * k / 6
            P.obj("Straw", cone((s * 1.12, -0.05, 0.75), (s * 1.4, -0.05 + math.cos(a) * 0.12, 0.75 + math.sin(a) * 0.12), 0.03, 4), "Trim", 0, False)
        for k in range(4):
            P.obj("StrawLeg", cone((s * 0.15, 0.0, 0.05), (s * (0.15 + 0.05 * k), 0.05 * k - 0.05, -0.45 - 0.05 * k), 0.035, 4), "Trim", 0, False)
        P.part("Cloth", sheet([[(s * 0.38, -0.25, 0.25), (s * 0.15, -0.3, 0.3), (s * 0.3, -0.55, -0.4)], [(s * 0.38, -0.25, 0.25), (s * 0.3, -0.55, -0.4), (s * 0.55, -0.45, -0.25)]], 0.02),
               "Metal", (0, 0, 0), 0, False)
    # a crow on the bar, and crows circling
    def crow(c, k, spin):
        c = Vector(c)
        parts = [ball(tuple(c), (0.1, 0.16, 0.1), 8, 4), ball(tuple(c + Vector((0, 0.14, 0.08))), (0.07, 0.07, 0.07), 8, 4), cone(c + Vector((0, 0.2, 0.08)), c + Vector((0, 0.3, 0.06)), 0.025, 4)]
        for s2 in (1, -1): parts.append(sheet([[tuple(c + Vector((s2 * 0.05, 0.05, 0.02))), tuple(c + Vector((s2 * 0.35, -0.05, 0.12))), tuple(c + Vector((s2 * 0.05, -0.1, 0.02)))]], 0.02))
        for b in parts:
            if spin: P.part("SpinCrows", b, "Dark", (0, 0, 0.6), 0, False)
            else: P.obj("Crow", b, "Dark", 0, False)
    crow((0.95, -0.12, 0.87), 0, False)
    for k in range(4):
        a = 2 * math.pi * k / 4 + 0.4
        crow((math.cos(a) * 1.9, math.sin(a) * 1.4, 0.9 + 0.3 * math.sin(a * 2)), k, True)
    P.part("Muzzle", ball((0, 0.47, 1.15), (0.07, 0.03, 0.05), 8, 4), "Glow", (0, 0.47, 1.15))
    return P


# ================================================================= 3. the fox spirit
def A_castle():
    """The last boss: a giant pumpkin carved into a castle - glowing arched windows and a great door, little pumpkin turrets under witch-hat
    roofs, its stalk risen into a tower, vines curling round it, lanterns, and a ring of falling leaves turning round it."""
    P = Boss("castle", pal(Glass=((0.30, 0.16, 0.38), 0.45), Metal=((0.28, 0.45, 0.16), 0.4)))
    P.obj("Pumpkin", pumpkin((0, 0, 0), 1.45, 1.9, 12, 48, 14), "Accent", 0)
    def window(c, w, h, nrm):
        c = Vector(c); nrm = Vector(nrm).normalized(); side = Vector((-nrm.y, nrm.x, 0))
        pts = [c + side * w * 0.5 + Vector((0, 0, -h * 0.5)), c - side * w * 0.5 + Vector((0, 0, -h * 0.5)), c - side * w * 0.5 + Vector((0, 0, h * 0.2)), c + side * w * 0.5 + Vector((0, 0, h * 0.2)), c + Vector((0, 0, h * 0.5))]
        return hull([tuple(p + nrm * d) for p in pts for d in (-0.02, 0.04)])
    P.obj("Door", window((0, 1.43, -0.35), 0.45, 0.6, (0, 1, 0)), "Glow", 0, False)
    for k, (a, z) in enumerate(((0.45, 0.25), (-0.45, 0.25), (0.9, -0.1), (-0.9, -0.1), (0.25, 0.55), (-0.25, 0.55), (1.3, 0.3), (-1.3, 0.3))):
        d = Vector((math.sin(a), math.cos(a), 0))
        r = 1.45 * math.cos(math.asin(min(0.95, abs(z) / 0.95))) * 0.98
        P.obj("Window", window(tuple(d * r + Vector((0, 0, z))), 0.2, 0.28, tuple(d)), "Glow", 0, False)
    # the stalk tower
    P.obj("Stalk", pipe(bez((0, 0, 0.75), (0, 0, 1.2), (0.05, -0.05, 1.5), (0.15, -0.1, 1.75), 5), [0.3, 0.27, 0.24, 0.22, 0.2, 0.2], 10), "Metal", 1)
    P.obj("TowerRoof", lathe([(0.32, 1.72), (0.0, 2.35)], 12, "z", (0.15, -0.1, 0)), "Glass")
    P.obj("TowerWindow", box((0.15, 0.1, 1.55), (0.1, 0.06, 0.14)), "Glow", 0, False)
    for k in range(4):   # pumpkin turrets with witch-hat roofs
        a = math.pi / 4 + k * math.pi / 2
        c = (math.sin(a) * 1.0, math.cos(a) * 0.95, 0.7)
        P.obj("Turret", pumpkin(c, 0.32, 0.45, 8, 20, 8), "Trim")
        P.obj("Hat", lathe([(0.34, 0.92), (0.3, 0.95), (0.14, 1.05), (0.0, 1.45)], 12, "z", (c[0], c[1], 0)), "Glass")
        P.obj("Brim", lathe([(0.0, 0.9), (0.4, 0.9), (0.4, 0.92), (0.0, 0.93)], 12, "z", (c[0], c[1], 0)), "Glass")
        P.obj("TurretWindow", box((c[0] * 1.32, c[1] * 1.32, 0.7), (0.08, 0.08, 0.12), Matrix.Rotation(-a, 3, "Z")), "Glow", 0, False)
    # vines and lanterns
    for s in (1, -1):
        v = [Vector((s * (1.3 - 0.1 * i), 0.4 + 0.2 * math.sin(i), -0.6 + 0.25 * i)) for i in range(7)]
        P.obj("Vine", pipe(v, [0.05] * 7, 6), "Metal")
        for q in v[1::2]:
            P.part("Cloth", leaf(tuple(q + Vector((s * 0.08, 0.1, 0.0))), 0.15, (s, 0.3, 0), (0, 0.3, 1)), "Metal", (0, 0, 0), 0, False)
        P.obj("Lantern", ball((s * 0.55, 1.45, 0.1), (0.07, 0.07, 0.1), 8, 4), "Lamp")
        P.obj("LanternHook", pipe([(s * 0.55, 1.4, 0.32), (s * 0.55, 1.45, 0.18)], [0.012, 0.012], 4), "Dark")
    P.obj("Root", cone((0, 0, -0.85), (0, 0, -1.35), 0.25, 8), "Base", 0, False)
    for k in range(12):   # the ring of falling leaves
        a = 2 * math.pi * k / 12
        c = (math.cos(a) * 2.1, math.sin(a) * 2.0, 0.2 + 0.4 * math.sin(a * 3))
        P.part("SpinLeaves", leaf(c, 0.17, (math.cos(a + 1), math.sin(a + 1), 0.3), (0, 0, 1)), ("Glass", "Accent", "Trim")[k % 3], (0, 0, 0.2), 0, False)
    P.part("Muzzle", ball((0, 1.5, -0.35), (0.08, 0.04, 0.08), 8, 4), "Glow", (0, 1.5, -0.35))
    return P


# ================================================================= 2026-10-11: the new round ("new bosses with features, grand, suiting the world")
def spline(pts, n):
    P = [Vector(p) for p in pts]
    P = [P[0] * 2 - P[1]] + P + [P[-1] * 2 - P[-2]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for k in range(n):
            t = k / n
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(P[-2])
    return out

def carve_on(surf, quad, d0=-0.04, d1=0.03):
    """a convex patch on a surface: quad is a list of (x, z) on the front, surf(x, z) -> (point, normal); the patch stands d0..d1 off it."""
    pts = []
    for (x, z) in quad:
        q, n = surf(x, z)
        pts += [tuple(q + n * d0), tuple(q + n * d1)]
    return hull(pts)

def strip(surf, top, bot, n, name, P, paint, d0=-0.04, d1=0.03):
    """a concave band (a grin, a brow) cut into convex quads between two curves top(t), bot(t), t in 0..1."""
    for i in range(n):
        t0, t1 = i / n, (i + 1) / n
        P.obj(name, carve_on(surf, [top(t0), top(t1), bot(t1), bot(t0)], d0, d1), paint, 0, False)

def ellipsoid_surf(c, rx, ry, rz):
    """the front (+y) of an ellipsoid: (x, z) -> (point, normal)."""
    c = Vector(c)
    def surf(x, z):
        u = (x - c.x) / rx; w = (z - c.z) / rz
        k = max(0.0, 1 - u * u - w * w)
        y = c.y + ry * math.sqrt(k)
        q = Vector((x, y, z))
        nrm = Vector(((x - c.x) / rx ** 2, (y - c.y) / ry ** 2, (z - c.z) / rz ** 2)).normalized()
        return q, nrm
    return surf



# ================================================================= fox
# Sky Squad, the autumn fox spirit remade (2026-10-13). Merged later into Tools/blender/autumn_bosses.py as A_fox.


def fx_ring_at(rings, y):
    """the loft section (y, a, b, cx, cz) at y, interpolated."""
    for r0, r1 in zip(rings, rings[1:]):
        if y <= r1[0]:
            f = max(0.0, (y - r0[0]) / (r1[0] - r0[0])); return [a + (b - a) * f for a, b in zip(r0, r1)]
    return list(rings[-1])

def fx_top(rings, x, y, k=1.0):
    """a point on the upper surface of a loft at (x, y), lifted k times its height."""
    r = fx_ring_at(rings, y); u = min(0.98, abs(x) / max(r[1], 1e-4))
    return Vector((x, y, r[4] + r[2] * math.sqrt(1 - u * u) * k))

def fx_frame(bm, o, X, Y, Z):
    """the mesh built in its own axes (x across, y along, z out) put at o along the world axes X, Y, Z."""
    return xf(bm, Matrix((X, Y, Z)).transposed(), tuple(o))

def fx_tuft(base, d, L, w, nrm, bend=0.0):
    """a fur tuft: a flat pointed blade from base along d, w wide, lying across nrm; bend lifts its tip along nrm."""
    base = Vector(base); d = Vector(d).normalized(); nrm = Vector(nrm).normalized()
    side = d.cross(nrm).normalized(); t = w * 0.3
    tip = base + d * L + nrm * bend
    pts = [base + side * w, base - side * w, base + nrm * t, base - nrm * t,
           base + d * L * 0.4 + side * w * 0.75 + nrm * bend * 0.3, base + d * L * 0.4 - side * w * 0.75 + nrm * bend * 0.3, tip]
    return hull([tuple(p) for p in pts])


def A_fox():
    """The fox spirit (2026-10-13, remade: "same as the alien bosses - realistic details, scarier, keep the cartoon shape"): the same
    nine-tailed kitsune charging at the player, now built like a real red fox - a long low body with a deep narrow chest, a lean waist and
    strong haunches; a rufous coat with a darker saddle down the back, a white bib from the chin down the throat and chest, a cream belly,
    and the black stockings of a red fox on all four legs. Its hackles are up: a crest of fur tufts stands along the neck and shoulders,
    graded biggest over the withers. The head is a fox's - a broad skull, flaring white cheek ruffs, a long narrow muzzle with the dark
    tear line from the eye to the lip, whisker pads with four whiskers a side, a black nose - but snarling: the jaw dropped, the black
    lips drawn back over long ivory canines and a row of teeth, the top of the muzzle creased with three wrinkles, a red tongue. Amber
    eyes glow under low frowning brows, each with the vertical slit pupil a fox really has; big cupped ears with black backs and tips and
    white tufts inside. Red Inari-mask markings sweep from the eyes up to the ears, with a red jewel-flame on the brow. A twisted straw
    shimenawa rope round the neck with four zigzag paper shide hanging from it and a gold bell at the throat. Forepaws reach at the player,
    toes spread with hooked claws. Nine great brushes fan out behind, thick in the middle, each with the dark tail-gland spot near
    the root and the white tip of a red fox splitting into three locks; over each tip floats one tongue of blue foxfire, and the tails wave
    one after another. It flies by SKY-RUNNING ON FOXFIRE: it gallops through the air like a real fox at full stretch - the right foreleg
    reaching far out at the player, the left tucked with its wrist folded, the left hind leg pushing off behind, the right swinging forward
    under the belly - and under every paw floats a lotus of blue foxfire, a flat glowing core in a ring of flame tongues, that it steps on
    and carries with the paw. Each leg is its own mover hinged at the shoulder or hip (Sway0-3), so the legs swing one after another in a
    gallop, the nine tails waving after them (SwayT0-8); behind it three smaller lotuses, left and right in turn, fade away along its path:
    its footprints in the sky."""
    P = Boss("fox", pal(Base=((0.80, 0.22, 0.035), 0.4), Belly=((0.96, 0.93, 0.86), 0.3), Accent=((0.80, 0.05, 0.06), 0.5),
                        Trim=((0.95, 0.74, 0.28), 0.6), Glass=((0.95, 0.91, 0.80), 0.55), Dark=((0.05, 0.035, 0.03), 0.45),
                        Glow=((0.08, 0.55, 1.0), 0.5), Metal=((0.40, 0.09, 0.02), 0.35), Lamp=((1.0, 0.70, 0.12), 0.8)))

    for m in P.mats:
        if m.name.endswith("_Glow"):
            b = next(x for x in m.node_tree.nodes if x.type == "BSDF_PRINCIPLED"); b.inputs["Emission Strength"].default_value = 2.2
    # ---- the spine: the neck rises to the head, a deep chest, a narrow waist, the haunches, the tail root
    neck = bez((0, 0.95, 0.62), (0, 0.86, 0.45), (0, 0.72, 0.32), (0, 0.55, 0.24), 6)
    torso = bez((0, 0.55, 0.24), (0, 0.15, 0.14), (0, -0.4, 0.14), (0, -0.84, 0.26), 12)[1:]
    PTS = neck + torso; NN = len(neck)
    RX, RZ = [], []
    for i in range(len(neck)):
        u = i / (len(neck) - 1)
        RX.append(lerp_keys(u, [(0, 0.17), (0.5, 0.2), (1, 0.25)])); RZ.append(lerp_keys(u, [(0, 0.2), (0.5, 0.25), (1, 0.32)]))
    for i in range(len(torso)):
        u = (i + 1) / len(torso)
        RX.append(lerp_keys(u, [(0, 0.25), (0.15, 0.27), (0.5, 0.19), (0.78, 0.24), (0.93, 0.19), (1, 0.12)]))
        RZ.append(lerp_keys(u, [(0, 0.32), (0.15, 0.35), (0.5, 0.22), (0.78, 0.27), (0.93, 0.2), (1, 0.12)]))
    FR = spine_frames(PTS); n = len(PTS)
    def locate(c):
        return min(range(n), key=lambda k: (PTS[k] - c).length_squared)
    def coat(c, n_):
        i = locate(c); t, side, up = FR[i]; d = c - PTS[i]
        u = d.dot(side) / RX[i]; v = d.dot(up) / RZ[i]
        if i < NN + 1 and v < 0.05: return "Belly"                       # the white bib up the throat
        if i < NN + 4 and v < -0.2 and abs(u) < 0.8: return "Belly"       # ... down the chest
        if v < -0.45 and abs(u) < 0.7: return "Belly"                      # the cream belly
        if v > 0.55 and NN - 2 < i < n - 1: return "Metal"                 # the darker saddle
        return "Base"
    P.obj("Body", body_loft(PTS, RX, RZ, FR, seg=24, sq=1.1, flat=0.9), coat, 0)
    # raised hackles: tufts along the neck and withers, biggest over the shoulders, combed back
    for i in range(1, NN + 5):
        p = PTS[i]; t, side, up = FR[i]
        h = 0.07 + 0.09 * math.sin(math.pi * min(1.0, i / (NN + 4)))
        for s in (0, 1, -1):
            q = p + up * RZ[i] * 0.9 + side * s * RX[i] * 0.35
            d = (up * 1.0 + t * 0.9 + side * s * 0.35)
            P.obj("Hackle", fx_tuft(q, d, h * (1.0 if s == 0 else 0.75), 0.05, side.cross(d.normalized())), "Metal" if s == 0 else "Base", 0, False)
    # the chest fluff: white tufts in a V on the bib, pointing down
    for row in range(3):
        i = NN - 1 + row * 2; p = PTS[i]; t, side, up = FR[i]
        for s in (-1.5, -0.5, 0.5, 1.5) if row < 2 else (-1, 0, 1):
            q = p - up * RZ[i] * 0.85 + side * s * RX[i] * 0.25
            P.obj("ChestFluff", fx_tuft(q, -up + Vector((0, 0.35, 0)), 0.17 - 0.03 * row, 0.055, side), "Belly", 0, False)

    # ---- the head (built pointing +Y from the back of the skull, then tipped down a little and scaled)
    HB = Vector((0, 0.84, 0.7)); HR = Matrix.Rotation(math.radians(-8), 3, "X") @ Matrix.Scale(1.32, 3); HI = HR.inverted()
    def H(bm): return xf(bm, HR, tuple(HB))
    def hp(fn): return lambda c, n_: fn(HI @ (c - HB), (HI @ n_).normalized())
    def hpt(p): return HB + HR @ Vector(p)
    UP = [(-0.12, 0.1, 0.09, 0, 0.02), (-0.03, 0.2, 0.18, 0, 0.04), (0.08, 0.25, 0.2, 0, 0.05), (0.2, 0.25, 0.17, 0, 0.04),
          (0.3, 0.19, 0.12, 0, 0.0), (0.4, 0.125, 0.085, 0, -0.035), (0.52, 0.1, 0.07, 0, -0.05), (0.63, 0.08, 0.058, 0, -0.055),
          (0.71, 0.06, 0.045, 0, -0.055), (0.76, 0.03, 0.025, 0, -0.05)]
    def skull(c, n_):
        if c.y > 0.32 and n_.z < 0.25: return "Belly"           # the white upper lip under the muzzle's sides
        if c.y < 0.3 and n_.z < -0.35: return "Belly"           # the white under the jaw
        return "Base"
    P.obj("Skull", H(loft(UP, 22, sq=1.15)), hp(skull), 0)
    P.obj("Nose", H(ball((0, 0.765, -0.035), (0.04, 0.035, 0.035), 10, 5)), "Dark")
    for s in (1, -1):
        P.obj("Nostril", H(ball((s * 0.017, 0.795, -0.045), (0.012, 0.008, 0.008), 6, 3)), "Metal")
    # the lower jaw, hinged under the ear and dropped open in a snarl
    LO = [(0.1, 0.15, 0.06, 0, -0.08), (0.3, 0.1, 0.045, 0, -0.1), (0.5, 0.075, 0.035, 0, -0.1), (0.64, 0.05, 0.028, 0, -0.095), (0.69, 0.025, 0.018, 0, -0.09)]
    J = Vector((0, 0.12, -0.07)); JR = Matrix.Rotation(math.radians(-24), 3, "X")
    def Jw(bm): return H(xf(bm, JR, tuple(J - JR @ J)))
    P.obj("Jaw", Jw(loft(LO, 16, sq=1.1)), hp(lambda c, n_: "Dark" if n_.z > 0.55 else "Belly"), 0)
    P.obj("Mouth", H(ball((0, 0.4, -0.11), (0.075, 0.28, 0.05), 12, 6)), "Dark")
    P.obj("Tongue", Jw(pipe([(0, 0.2, -0.06), (0, 0.42, -0.065), (0, 0.6, -0.06)], [0.045, 0.04, 0.02], 8)), "Accent")
    for s in (1, -1):
        # the lips drawn back: a black line along the upper muzzle and the jaw's edge
        up_lip = [Vector((s * fx_ring_at(UP, y)[1] * 0.92, y, fx_ring_at(UP, y)[4] - fx_ring_at(UP, y)[2] * 0.75)) for y in (0.32, 0.42, 0.52, 0.62, 0.7, 0.745)]
        P.obj("Lip", H(pipe(up_lip, [0.016] * 5 + [0.01], 5)), "Dark")
        lo_lip = [Vector((s * fx_ring_at(LO, y)[1] * 0.9, y, fx_ring_at(LO, y)[4] + fx_ring_at(LO, y)[2] * 0.8)) for y in (0.16, 0.3, 0.45, 0.58, 0.67)]
        P.obj("Lip", Jw(pipe(lo_lip, [0.013] * 4 + [0.008], 5)), "Dark")
        # teeth: a long canine near the front of each jaw, premolars behind, little incisors at the tip
        for y, L in ((0.36, 0.035), (0.44, 0.045), (0.52, 0.04), (0.62, 0.115), (0.69, 0.03)):
            r = fx_ring_at(UP, y); top = Vector((s * r[1] * 0.8, y, r[4] - r[2] * 0.8))
            P.obj("Tooth", H(cone(top, top + Vector((-s * 0.008, 0.012, -L)), 0.012 + L * 0.13, 6)), "Glass", 0, False)
        for y, L in ((0.3, 0.03), (0.42, 0.035), (0.56, 0.085), (0.645, 0.025)):
            r = fx_ring_at(LO, y); bot = Vector((s * r[1] * 0.75, y, r[4] + r[2] * 0.8))
            P.obj("Tooth", Jw(cone(bot, bot + Vector((-s * 0.008, 0.01, L)), 0.011 + L * 0.13, 6)), "Glass", 0, False)
        # the eye: almond, amber, a vertical slit pupil and a glint, a black rim; the tear line runs from it down the muzzle
        ec = Vector((s * 0.135, 0.3, 0.075)); dv = Vector((s * 0.55, 0.83, 0.12)).normalized()
        ex = dv.cross(Vector((0, 0, 1))).normalized(); ez = ex.cross(dv).normalized()
        if ez.z < 0: ez = -ez
        P.obj("EyeRim", H(oriented_ball(ec - dv * 0.004, (0.078, 0.03, 0.05), ex, dv, ez, 12, 6)), "Dark")
        P.obj("Eye", H(oriented_ball(ec + dv * 0.006, (0.066, 0.03, 0.04), ex, dv, ez, 12, 6)), "Lamp")
        P.obj("Pupil", H(oriented_ball(ec + dv * 0.03, (0.01, 0.012, 0.036), ex, dv, ez, 6, 4)), "Dark")
        P.obj("Glint", H(ball(tuple(ec + dv * 0.033 + ez * 0.02 - ex * s * 0.015), (0.01, 0.01, 0.01), 6, 3)), "Belly")
        P.obj("Brow", H(pipe(bez((s * 0.045, 0.345, 0.09), (s * 0.1, 0.335, 0.125), (s * 0.16, 0.31, 0.145), (s * 0.2, 0.27, 0.15), 6),
                             [0.016, 0.024, 0.028, 0.028, 0.025, 0.018, 0.008], 7)), "Base")   # low at the nose: a frown
        tear = [ec + Vector((-s * 0.045, 0.03, -0.02)), Vector((s * 0.085, 0.42, -0.0)), Vector((s * 0.08, 0.52, -0.03)), Vector((s * 0.072, 0.6, -0.06))]
        P.obj("Tear", H(pipe(tear, [0.014, 0.012, 0.01, 0.006], 5)), "Dark")
        # the red Inari-mask marking: from the eye's outer corner up over the brow toward the ear
        mk = [fx_top(UP, s * x, y, 1.02) for (x, y) in ((0.19, 0.27), (0.17, 0.2), (0.14, 0.12), (0.12, 0.05))]
        P.obj("Marking", H(pipe(mk, [0.012, 0.02, 0.018, 0.0], 5)), "Accent")
        # three snarl wrinkles across the top of the muzzle
    for k, y in enumerate((0.43, 0.48, 0.53)):
        r = fx_ring_at(UP, y)
        pts = [fx_top(UP, x * r[1], y - 0.02 * abs(x), 1.03) for x in (-0.75, -0.4, 0.0, 0.4, 0.75)]
        P.obj("Wrinkle", H(pipe(pts, [0.0, 0.007, 0.009, 0.007, 0.0], 4)), "Metal")
    flame = [fx_top(UP, 0, y, 1.02) for y in (0.26, 0.21, 0.16, 0.1)]   # the red jewel-flame on the brow
    P.obj("BrowFlame", H(pipe(flame, [0.0, 0.03, 0.022, 0.0], 6)), "Accent")
    P.obj("BrowJewel", H(ball(tuple(fx_top(UP, 0, 0.215, 1.08)), (0.022, 0.022, 0.016), 8, 4)), "Glow")
    for s in (1, -1):
        # the ears: big, cupped, black on the back and at the tip, white tufts inside
        eb = fx_top(UP, s * 0.12, 0.04, 0.9); ED = Vector((s * 0.38, -0.12, 1.0)).normalized()
        EZ = (Vector((0, 1, 0)) - ED * ED.y).normalized(); EX = ED.cross(EZ).normalized()
        EAR = [(0.0, 0.13, 0.045, 0, 0.0), (0.12, 0.125, 0.04, 0, -0.012), (0.26, 0.1, 0.035, 0, -0.018), (0.38, 0.06, 0.025, 0, -0.012), (0.46, 0.012, 0.012, 0, 0.0)]
        ob = loft(EAR, 14, sq=1.0)
        fx_frame(ob, eb, EX, ED, EZ)
        def earpaint(c, n_, eb=eb, ED=ED, EZ=EZ):
            if (c - eb).dot(ED) > 0.33: return "Dark"
            return "Dark" if n_.dot(EZ) < -0.1 else "Base"
        P.obj("Ear", H(ob), hp(earpaint), 0)
        inner = loft([(0.02, 0.09, 0.02, 0, 0.03), (0.15, 0.085, 0.02, 0, 0.025), (0.27, 0.06, 0.016, 0, 0.018), (0.36, 0.02, 0.01, 0, 0.01)], 10)
        P.obj("EarInner", H(fx_frame(inner, eb, EX, ED, EZ)), "Dark")
        for k, a in enumerate((-0.6, 0.0, 0.6)):
            b = eb + ED * 0.03 + EX * a * 0.06 + EZ * 0.04
            P.obj("EarTuft", H(fx_tuft(b, ED + EX * a * 0.5 + EZ * 0.3, 0.2 - 0.03 * abs(a), 0.03, EZ)), "Belly", 0, False)
        # the cheek ruffs: white fur flaring out and back below the ears
        for k, (z, L) in enumerate(((0.03, 0.13), (-0.02, 0.17), (-0.07, 0.19), (-0.12, 0.16), (-0.16, 0.12))):
            b = Vector((s * 0.18, 0.14 + 0.015 * k, z))
            P.obj("CheekRuff", H(fx_tuft(b, (s * 1.0, -0.55, -0.15 - 0.2 * k), L, 0.07, (0, 0.3, 1), -0.03)), "Belly" if k else "Base", 0, False)
        # whiskers from the whisker pads, fanned out and back (on the Cloth part: no outline)
        pad = Vector((s * 0.075, 0.6, -0.055))
        P.obj("WhiskerPad", H(ball(tuple(pad), (0.035, 0.07, 0.03), 8, 4)), "Belly")
        for k in range(4):
            d = Vector((s * 1.0, -0.25 - 0.12 * k, 0.12 - 0.1 * k)).normalized()
            w = bez(pad, pad + d * 0.1, pad + d * 0.19 + Vector((0, 0, -0.02)), pad + d * 0.27 + Vector((0, 0, -0.05)), 4)
            P.part("Cloth", H(pipe([Vector(p) for p in w], [0.006, 0.005, 0.004, 0.003, 0.0], 4)), "Dark", (0, 0, 0), 0, False)

    # ---- the shimenawa: a twisted straw rope round the neck, four zigzag paper shide and a gold bell at the throat
    ci = 3; cp = PTS[ci] + FR[ci][2] * 0.02; t, side, up = FR[ci]
    def ring_pt(a, rr=0.0, ph=0.0):
        base = cp + side * math.cos(a) * (RX[ci] + 0.03) + up * math.sin(a) * (RZ[ci] + 0.03)
        out = (side * math.cos(a) * RZ[ci] + up * math.sin(a) * RX[ci]).normalized()
        return base + (out * math.cos(ph) + t * math.sin(ph)) * rr
    for strand in (0, math.pi):
        pts = [ring_pt(2 * math.pi * k / 72, 0.028, strand + 2 * math.pi * k / 72 * 9) for k in range(73)]
        P.obj("Rope", pipe(pts, [0.03] * 73, 6, cap=False), "Trim")
    for a in (math.radians(-90 + 40), math.radians(-90 - 40), math.radians(-90 + 95), math.radians(-90 - 95)):
        top = ring_pt(a, 0.035)
        poly = []; w = 0.035
        down = -up * 0.8 - t * 0.2
        for k in range(4):   # a zigzag strip of paper: each step jogs out and back
            q = top + down.normalized() * 0.075 * k + side * (0.03 if k % 2 else -0.03) * (1 if math.cos(a) >= 0 else -1)
            poly.append(q)
        outn = (side * math.cos(a) + up * math.sin(a)).normalized()
        for q0, q1 in zip(poly, poly[1:]):
            Wd = t * w
            quad = [q0 - Wd, q0 + Wd, q1 + Wd, q1 - Wd]
            bm = bmesh.new()
            vs = [bm.verts.new(q + outn * 0.006) for q in quad] + [bm.verts.new(q - outn * 0.006) for q in quad]
            bm.faces.new(vs[:4]); bm.faces.new(list(reversed(vs[4:])))
            for i in range(4): bm.faces.new((vs[i], vs[(i + 1) % 4], vs[4 + (i + 1) % 4], vs[4 + i]))
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
            P.part("Cloth", bm, "Belly", (0, 0, 0), 0, False)
    bt = ring_pt(-math.pi / 2, 0.04)
    P.obj("BellCord", pipe([bt, bt - up * 0.06], [0.014, 0.014], 5), "Accent")
    P.obj("Bell", ball(tuple(bt - up * 0.12 + t * 0.0), (0.075, 0.075, 0.07), 14, 7), "Trim")
    P.obj("BellSlot", oriented_ball(bt - up * 0.16 - t * 0.065, (0.045, 0.012, 0.01), side, -t, up, 6, 3), "Dark")
    P.obj("BellBand", pipe([bt - up * 0.12 + (side * math.cos(2 * math.pi * k / 16) - t * math.sin(2 * math.pi * k / 16)) * 0.076 for k in range(17)], [0.008] * 17, 4), "Metal")

    # ---- sky-running: the legs gallop (each its own Sway mover, hinged at the shoulder or hip) and every paw steps on a lotus of foxfire
    def lotus(c, r, name, hub, tongues=8, k0=0.0):
        """a floating disc of foxfire: a flat glowing core inside a ring of flame tongues that lean out and curl up."""
        c = Vector(c)
        bm = ball(tuple(c), (r * 0.66, r * 0.66, r * 0.2), 14, 5)
        P.part(name, bm, "Glow", hub) if hub is not None else P.part(name, bm, "Glow", (0, 0, 0), 0, False)
        for m in range(tongues):
            a = 2 * math.pi * (m + k0) / tongues; o = Vector((math.cos(a), math.sin(a), 0))
            b = c + o * r * 0.5
            pts = bez(b, b + o * r * 0.35 + Vector((0, 0, r * 0.08)), b + o * r * 0.55 + Vector((0, 0, r * 0.3)), b + o * r * 0.5 + Vector((0, 0, r * 0.62)), 4)
            bm = pipe(pts, [r * 0.17, r * 0.15, r * 0.11, r * 0.06, 0.0], 6)
            if hub is not None: P.part(name, bm, "Glow", hub)
            else: P.part(name, bm, "Glow", (0, 0, 0), 0, False)
    def paw(name, hub, ft, d, size=1.0):
        d = Vector(d).normalized(); sd = d.cross(Vector((0, 0, 1))).normalized(); upp = sd.cross(d).normalized()
        P.part(name, oriented_ball(ft, (0.07 * size, 0.08 * size, 0.045 * size), sd, d, upp, 10, 5), "Dark", hub)
        for k in range(4):
            a = (k - 1.5) * 0.32
            dd = (Matrix.Rotation(a, 3, upp) @ d).normalized()
            tp = ft + dd * 0.08 * size - upp * 0.01
            P.part(name, ball(tuple(tp), (0.03 * size, 0.035 * size, 0.026 * size), 8, 4), "Dark", hub)
            c0 = tp + dd * 0.025 * size
            P.part(name, pipe(bez(c0, c0 + dd * 0.035, c0 + dd * 0.06 - upp * 0.015, c0 + dd * 0.065 - upp * 0.055, 4),
                              [0.014 * size, 0.012 * size, 0.008 * size, 0.004, 0.0], 5), "Glass", hub)
    def leg(name, joints, radii, dark_from, pawdir, size=1.0):
        """a leg through joints (shoulder or hip first, the foot last), black from joint dark_from down; its paw on a lotus of foxfire."""
        hub = tuple(joints[0])
        for i in range(len(joints) - 1):
            a, b = joints[i], joints[i + 1]
            P.part(name, pipe([a, (a + b) * 0.5, b], [radii[i], (radii[i] + radii[i + 1]) * 0.5, radii[i + 1]], 9),
                   "Dark" if i >= dark_from else "Base", hub)
            if 0 < i: P.part(name, ball(tuple(a), (radii[i] * 1.05,) * 3, 8, 4), "Dark" if i >= dark_from else "Base", hub)
        ft = joints[-1]; paw(name, hub, ft, pawdir, size)
        lotus(ft + Vector((0, 0, -0.09)), 0.24, name, hub)
    for s in (1, -1):
        P.obj("Shoulder", ball((s * 0.16, 0.47, 0.0), (0.1, 0.17, 0.18), 10, 5), "Base")
        P.obj("Thigh", oriented_ball(Vector((s * 0.2, -0.56, -0.02)), (0.13, 0.26, 0.21), Vector((1, 0, 0)), Vector((0, 0.8, -0.6)).normalized(), Vector((0, 0.6, 0.8)).normalized(), 12, 6), "Base")
    V_ = Vector
    # right foreleg reaching far out at the player; left foreleg tucked, the wrist folded so the paw turns back under the chest
    leg("SwayLeg0", [V_((0.17, 0.48, 0.02)), V_((0.2, 0.64, -0.18)), V_((0.2, 0.93, -0.28)), V_((0.2, 1.03, -0.31))], [0.11, 0.068, 0.048, 0.05], 1, (0, 1, -0.3))
    leg("SwayLeg1", [V_((-0.17, 0.48, 0.02)), V_((-0.2, 0.4, -0.25)), V_((-0.2, 0.62, -0.36)), V_((-0.2, 0.55, -0.47))], [0.11, 0.068, 0.048, 0.05], 1, (0, 0.35, -1))
    # left hind leg pushing off, stretched back; right hind leg swinging forward under the belly
    leg("SwayLeg3", [V_((-0.19, -0.6, 0.1)), V_((-0.23, -0.48, -0.2)), V_((-0.21, -0.9, -0.3)), V_((-0.2, -1.13, -0.36))], [0.12, 0.075, 0.05, 0.046], 2, (0, -1, -0.3), 0.95)
    leg("SwayLeg2", [V_((0.19, -0.6, 0.1)), V_((0.23, -0.3, -0.14)), V_((0.21, -0.56, -0.36)), V_((0.2, -0.36, -0.5))], [0.12, 0.075, 0.05, 0.046], 2, (0, 1, -0.25), 0.95)
    # the foxfire footprints it leaves behind: three smaller lotuses fading away along its path, left and right in turn
    for k, (x, y, z, r) in enumerate(((-0.2, -1.2, -0.58, 0.16), (0.2, -1.5, -0.66, 0.12), (-0.2, -1.8, -0.73, 0.085))):
        lotus(V_((x, y, z)), r, "Cloth", None, 6, 0.5 * k)

    # ---- nine great brushes fanned behind, waving one after another; each a red fox's tail with a white tip, and a foxfire over it
    p0 = Vector((0, -0.86, 0.27))
    for k in range(9):
        a = math.radians(-64 + k * 16); lift = math.cos(a)
        tip = p0 + Vector((math.sin(a) * 1.4, -0.62 - 0.25 * lift, 0.72 + 0.48 * lift))
        pts = bez(p0, p0 + Vector((math.sin(a) * 0.15, -0.45, 0.05)), tip + Vector((-math.sin(a) * 0.15, 0.25, -0.45)), tip, 12)
        rr = [lerp_keys(j / 12, [(0, 0.08), (0.15, 0.14), (0.45, 0.23), (0.65, 0.245), (0.82, 0.21), (0.93, 0.13), (1, 0.045)]) for j in range(13)]
        name = "SwayT%d" % k
        def brush(c, n_, pts=pts):
            j = min(range(len(pts)), key=lambda m: (pts[m] - c).length_squared)
            return "Belly" if j >= 10 else "Base"
        P.part(name, pipe(pts, rr, 14), brush, tuple(p0), 0)
        tt = (pts[4] - pts[2]).normalized(); upv = Vector((0, 0, 1)) - tt * tt.z; upv.normalize()
        P.part(name, oriented_ball(pts[3] + upv * rr[3] * 0.92, (0.05, 0.08, 0.02), tt.cross(upv).normalized(), tt, upv, 8, 4), "Dark", tuple(p0))   # the tail-gland spot
        d = (pts[-1] - pts[-3]).normalized(); sd = d.cross(Vector((0, 0, 1))).normalized(); uv = sd.cross(d).normalized()
        for m in range(3):   # the white tip splits into three locks
            ang_ = 2 * math.pi * m / 3 + k * 0.4
            o = (sd * math.cos(ang_) + uv * math.sin(ang_))
            b = pts[-2] + o * 0.05
            P.part(name, pipe(bez(b, b + d * 0.08 + o * 0.03, b + d * 0.15 + o * 0.03, b + d * 0.22 + o * 0.0, 4), [0.05, 0.045, 0.03, 0.015, 0.0], 6), "Belly", tuple(p0))
        f = pts[-1] + d * 0.27 + Vector((0, 0, 0.04))   # the foxfire: a teardrop flame floating over the tip
        P.part(name, ball(tuple(f), (0.075, 0.075, 0.075), 10, 5), "Glow", tuple(p0))
        P.part(name, pipe(bez(f, f + Vector((0, 0, 0.08)), f + Vector((0, -0.03, 0.15)), f + Vector((0, -0.07, 0.24)), 4), [0.072, 0.06, 0.04, 0.02, 0.0], 8), "Glow", tuple(p0))

    mz = hpt((0, 0.62, -0.1))
    P.part("Muzzle", ball(tuple(mz), (0.06, 0.03, 0.04), 8, 4), "Lamp", tuple(mz))
    return P



# ================================================================= stag
HB = Vector((0, 1.0, 1.0))                                                     # the poll, where the neck meets the skull
HR = Matrix.Rotation(math.radians(-18), 3, "X") @ Matrix.Scale(1.25, 3); HI = HR.inverted()
HEAD_AT = tuple(HB + HR @ Vector((0, 0.3, 0.1)))


def st_loft(pts, rx, ru, rd, fr, seg=24, sq=1.15):
    """a body along a spine: sections rx across, ru above the spine and rd below it (a deep chest hangs lower than the back rises)."""
    bm = bmesh.new(); rings = []
    for i, p in enumerate(pts):
        t, side, up = fr[i]
        if rx[i] < 1e-4: rings.append([bm.verts.new(p)]); continue
        ring = []
        for k in range(seg):
            a = 2 * math.pi * k / seg; ca, sa = math.cos(a), math.sin(a)
            u = math.copysign(abs(ca) ** (1 / sq), ca) * rx[i]
            v = math.copysign(abs(sa) ** (1 / sq), sa) * (ru[i] if sa > 0 else rd[i])
            ring.append(bm.verts.new(p + side * u + up * v))
        rings.append(ring)
    return skin(bm, rings, seg)

def st_sheet(polys, thick=0.02):
    """flat polygons made two-sided, the two faces pushed apart along each polygon's own normal (so upright cloth has a thickness too)."""
    bm = bmesh.new()
    for poly in polys:
        pv = [Vector(p) for p in poly]
        n = (pv[1] - pv[0]).cross(pv[-1] - pv[0])
        n = n.normalized() if n.length > 1e-9 else Vector((0, 0, 1))
        top = [bm.verts.new(p + n * thick * 0.5) for p in pv]; bot = [bm.verts.new(p - n * thick * 0.5) for p in pv]
        bm.faces.new(top); bm.faces.new(list(reversed(bot)))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm

def st_cloth(polys, thick=0.018):
    """quads welded into one surface (shared corners, so it shades smooth) and given a thickness."""
    bm = bmesh.new(); vs = {}
    def V(p):
        k = tuple(round(x, 5) for x in p)
        if k not in vs: vs[k] = bm.verts.new(p)
        return vs[k]
    for poly in polys:
        try: bm.faces.new([V(p) for p in poly])
        except ValueError: pass
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=thick)
    return bm

def st_H(bm): return xf(bm, HR, tuple(HB))
def st_hpt(p): return HB + HR @ Vector(p)
def st_hp(fn): return lambda c, n: fn(HI @ (c - HB), (HI @ n).normalized())


def A_stag():
    """The royal stag (2026-10-13, remade: "same as the alien bosses - realistic details, scarier, keep the cartoon shape"): the same
    galloping stag with the giant rack and the crimson caparison, now built like a real red deer stag in the rut. A deep chest and high
    withers, a lean waist and round haunches; a russet coat, a cream belly and the buff rump patch round a short tail; the thick neck of
    the rut under a shaggy dark mane hanging from the throat in even rows. The head is long, with a pale muzzle, a black wet nose with
    flared nostrils, the mouth open in the rut roar showing his lower incisors (his shots leave from its glowing throat), glowing amber
    eyes with the horizontal pupil of a deer under heavy dark lids slanted down in a glare, the dark preorbital gland in front of each eye flared in anger and the ears pinned back.
    The antlers are a real "royal" head of twelve points: from each pedicle a coronet burr, then the beam with pearling at its base, the
    brow and bez tines reaching forward, the trez tine at mid-beam and a crown of three at the top, brown with polished ivory tips. The
    legs are jointed like a deer's: the front ones tucked at the knee, the hind ones thrown back from the hock, every foot a cloven hoof
    with two dewclaws behind the fetlock. The royal tack is real horse tack: a crimson bridle with gold studs and a gold forehead
    medallion, a gold band on each antler above the burr, a lantern hung from each trez tine, a crimson caparison with a gold border of
    crimson lozenges, a scalloped hem with a gold tassel at each point and a gold maple leaf on each flank, a breast strap with a gold
    medallion and a girth strap.
    He does not fly on wings: he rides a whirlwind of autumn leaves. Under his hooves a funnel of wind stands on its point and widens up
    to a rim that carries him, his hooves on it as on the ground. Pale streaks of wind wind round it in spirals (an inner layer, SpinA,
    and an outer one with the leaves, SpinB, which the game turns about the funnel's axis); maple and oak leaves in crimson, gold and
    russet are caught evenly along the outer spirals, more and bigger toward the top where the wind is strongest, with a few twigs and
    acorns tumbling in it."""
    P = Boss("stag", pal(Base=((0.42, 0.18, 0.07), 0.4), Belly=((0.93, 0.83, 0.64), 0.35), Accent=((0.62, 0.05, 0.06), 0.5),
                         Trim=((1.0, 0.74, 0.2), 0.85), Glass=((0.36, 0.24, 0.13), 0.12), Dark=((0.10, 0.05, 0.03), 0.5),
                         Glow=((1.0, 0.52, 0.08), 0.5), Metal=((0.24, 0.15, 0.08), 0.6), Lamp=((1.0, 0.80, 0.36), 0.8)))
    # ---- the body: neck from the poll down to high withers, a deep chest, a lean waist, round haunches, the rump
    neck = bez(tuple(HB + Vector((0, -0.02, -0.04))), (0, 0.9, 0.7), (0, 0.78, 0.42), (0, 0.55, 0.27), 9)
    torso = bez((0, 0.55, 0.27), (0, 0.15, 0.22), (0, -0.45, 0.22), (0, -0.92, 0.2), 10)[1:]
    PTS = neck + torso + [Vector((0, -1.04, 0.19))]
    n = len(PTS); FR = spine_frames(PTS)
    RX, RU, RD = [], [], []
    for i in range(len(neck)):
        u = i / (len(neck) - 1)
        RX.append(lerp_keys(u, [(0, 0.13), (0.5, 0.17), (1, 0.27)]))
        RU.append(lerp_keys(u, [(0, 0.15), (0.5, 0.2), (1, 0.33)])); RD.append(lerp_keys(u, [(0, 0.16), (0.5, 0.25), (1, 0.42)]))
    for i in range(len(torso)):
        u = (i + 1) / len(torso)
        RX.append(lerp_keys(u, [(0, 0.29), (0.3, 0.3), (0.6, 0.26), (0.85, 0.29), (1, 0.25)]))
        RU.append(lerp_keys(u, [(0, 0.2), (0.3, 0.15), (0.6, 0.15), (0.85, 0.19), (1, 0.16)]))
        RD.append(lerp_keys(u, [(0, 0.42), (0.3, 0.4), (0.6, 0.31), (0.85, 0.27), (1, 0.22)]))
    RX.append(0.0); RU.append(0.0); RD.append(0.0)
    def coat(c, nn):
        if c.y < -0.86 and nn.y < -0.2: return "Belly"                               # the buff rump patch
        if c.y > 0.6 and c.z > 0.3 and nn.y > 0.35 and nn.z < 0.4: return "Dark"   # the dark throat under the mane
        if nn.z < -0.6 and c.y < 0.45: return "Belly"                                # the cream belly
        return "Base"
    bodybm = st_loft(PTS, RX, RU, RD, FR); BV = BVHTree.FromBMesh(bodybm.copy())
    def onbody(c, d, lift):
        """the point where a ray from c (inside the body) along d leaves the skin, lifted off it."""
        hit = BV.ray_cast(Vector(c), Vector(d).normalized(), 5.0)
        return (hit[0] + hit[1] * lift) if hit[0] is not None else Vector(c) + Vector(d).normalized() * 0.3
    P.obj("Body", bodybm, coat, 0)
    # the rut mane: shaggy tufts hanging from the throat in even staggered rows
    for i in range(2, len(neck) - 1):
        p = PTS[i]; t, side, up = FR[i]
        for j in range(-3, 4):
            if (i + j) % 2: continue
            a = j * 0.3
            q = p - up * RD[i] * math.cos(a) * 0.95 + side * RX[i] * math.sin(a) * 0.95
            down = (Vector((0, 0.25, -1)) + side * math.sin(a) * 0.4).normalized()
            L = 0.17 + 0.08 * (1 - abs(j) / 3)
            lock = pipe([q - down * 0.03, q + down * L * 0.45, q + down * L * 0.8 + Vector((0, -0.01, 0)), q + down * L + Vector((0, -0.03, 0.01))], [0.034, 0.026, 0.014, 0.0], 6)
            fl = side.cross(down).normalized()
            for v in lock.verts:   # flattened into a lock of hair lying on the throat
                d = v.co - q; v.co = q + d - fl * d.dot(fl) * 0.55
            P.obj("Mane", lock, "Dark", 0)
    # the short tail over the buff patch
    P.obj("Tail", pipe([(0, -1.0, 0.27), (0, -1.1, 0.22), (0, -1.14, 0.1)], [0.07, 0.06, 0.0], 8), lambda c, nn: "Belly" if nn.y < -0.3 else "Base")

    # ---- the legs (each its own Sway part about the shoulder or hip): jointed like a deer's, cloven hooves, dewclaws behind
    def leg(name, hub, joints, radii):
        hub = Vector(hub); J = [Vector(p) for p in joints]
        P.part(name, oriented_ball(hub + Vector((0, 0, -0.05)), (0.15, 0.2, 0.26), Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1)), 12, 6), "Base", tuple(hub))
        P.part(name, pipe([hub] + J[:-1], radii, 10), "Base", tuple(hub))
        for k in range(1, len(J) - 2):
            P.part(name, ball(tuple(J[k]), (radii[k + 1] * 1.25,) * 3, 8, 4), "Base", tuple(hub))   # the knee / hock and fetlock knobs
        fet, cor, tip = J[-3], J[-2], J[-1]
        d = (tip - cor).normalized(); back = (fet - cor).normalized()
        across = d.cross(Vector((0, 0, 1))).normalized() if abs(d.z) < 0.95 else Vector((1, 0, 0))
        cannon = (fet - J[-4]).normalized()
        bdir = -(d - cannon * d.dot(cannon)).normalized()
        for s in (1, -1):   # the two toes of the cloven hoof, a cleft between them; a dewclaw behind the fetlock over each
            o = across * s * 0.03
            P.part(name, pipe([cor + o, cor + o + d * 0.07, tip + o], [0.032, 0.03, 0.006], 6), "Dark", tuple(hub))
            b = fet + bdir * 0.03 + across * s * 0.022
            P.part(name, cone(b, b + cannon * 0.05 + bdir * 0.025, 0.015, 5), "Dark", tuple(hub))
    for s in (1, -1):
        lead = 0.05 if s > 0 else -0.05
        # front: elbow, knee tucked forward, cannon folded back, fetlock, coronet, hoof tip
        leg("SwayLeg%d" % (0 if s > 0 else 1), (s * 0.2, 0.5, 0.02),
            [(s * 0.22, 0.44 + lead, -0.32), (s * 0.23, 0.7 + lead, -0.52), (s * 0.23, 0.6 + lead, -0.83), (s * 0.23, 0.66 + lead, -0.9), (s * 0.23, 0.74 + lead, -0.98)],
            [0.14, 0.085, 0.05, 0.035, 0.03])
        # hind: stifle forward, hock back, cannon down and back, fetlock, coronet, hoof tip
        leg("SwayLeg%d" % (2 if s > 0 else 3), (s * 0.21, -0.72, 0.08),
            [(s * 0.24, -0.5 - lead, -0.25), (s * 0.24, -0.92 - lead, -0.45), (s * 0.24, -1.12 - lead, -0.73), (s * 0.24, -1.17 - lead, -0.8), (s * 0.24, -1.26 - lead, -0.84)],
            [0.17, 0.1, 0.055, 0.037, 0.032])

    # ---- the head (built pointing +Y about the poll, then tipped down and drawn big)
    UP = [(-0.06, 0.12, 0.12, 0, 0.0), (0.04, 0.15, 0.14, 0, 0.02), (0.16, 0.15, 0.13, 0, 0.01), (0.28, 0.115, 0.1, 0, -0.01),
          (0.4, 0.09, 0.08, 0, -0.02), (0.5, 0.08, 0.07, 0, -0.025), (0.58, 0.072, 0.06, 0, -0.025), (0.63, 0.04, 0.035, 0, -0.025)]
    def face(c, nn):
        if c.y > 0.56 and nn.z > 0.1: return "Dark"                              # the black wet nose
        if c.y > 0.44 and nn.z < 0.15: return "Belly"                            # the pale lips and chin
        if nn.z < -0.55: return "Dark" if c.y > 0.12 else "Belly"                 # the roof of the open mouth; the throat behind
        return "Base"
    P.obj("Skull", st_H(loft(UP, 22, sq=1.2)), st_hp(face), 0)
    # the lower jaw hinged under the ear, dropped open in the roar; a tongue, lower incisors at the front
    J0 = Vector((0, 0.06, -0.08)); JR = Matrix.Rotation(math.radians(-24), 3, "X")
    def Jw(bm): return st_H(xf(bm, JR, tuple(J0 - JR @ J0)))
    LO = [(0.0, 0.11, 0.06, 0, -0.07), (0.2, 0.1, 0.05, 0, -0.08), (0.4, 0.07, 0.04, 0, -0.08), (0.54, 0.055, 0.035, 0, -0.075), (0.58, 0.03, 0.025, 0, -0.07)]
    JI = JR.inverted()
    P.obj("Jaw", Jw(loft(LO, 16, sq=1.2)), st_hp(lambda c, nn: "Dark" if (JI @ nn).z > 0.5 else ("Belly" if c.y > 0.4 or (JI @ nn).z < -0.4 else "Base")), 0)
    P.obj("Mouth", st_H(ball((0, 0.3, -0.07), (0.075, 0.25, 0.04), 12, 6)), "Dark")
    P.obj("Throat", st_H(ball((0, 0.16, -0.08), (0.07, 0.12, 0.05), 10, 5)), "Glow")
    P.obj("Tongue", Jw(pipe([(0, 0.12, -0.04), (0, 0.32, -0.045), (0, 0.48, -0.04)], [0.04, 0.035, 0.015], 8)), "Accent")
    for k in range(6):   # the lower incisors, a neat fan at the front of the jaw
        x = -0.035 + 0.014 * k
        P.obj("Tooth", Jw(cone((x, 0.55, -0.045), (x * 1.1, 0.565, -0.01), 0.008, 4)), "Belly", 0, False)
    for s in (1, -1):
        # the wet nose and flared nostrils
        P.obj("Nostril", st_H(oriented_ball((s * 0.04, 0.615, -0.01), (0.022, 0.012, 0.03), Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1)), 8, 4)), "Dark")
        # glowing amber eyes with the horizontal bar pupil of a deer, in dark sockets under heavy lowered brows
        e = Vector((s * 0.135, 0.2, 0.05))
        P.obj("Socket", st_H(oriented_ball(e, (0.03, 0.055, 0.045), Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1)), 10, 5)), "Dark")
        P.obj("Eye", st_H(oriented_ball(e + Vector((s * 0.012, 0.005, 0)), (0.026, 0.045, 0.036), Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1)), 10, 5)), "Glow")
        P.obj("Pupil", st_H(oriented_ball(e + Vector((s * 0.036, 0.008, 0)), (0.006, 0.024, 0.008), Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1)), 6, 3)), "Dark")
        # a heavy dark upper lid slanted down toward the nose: the glare
        ly = Vector((0, 0.92, -0.38)); lz = Vector((0, 0.38, 0.92))
        P.obj("Lid", st_H(oriented_ball(e + Vector((s * 0.018, 0.004, 0.022)), (0.022, 0.058, 0.02), Vector((1, 0, 0)), ly, lz, 10, 5)), "Dark")
        # the preorbital gland, a dark slit in front of the eye, flared
        P.obj("Gland", st_H(pipe([(s * 0.13, 0.25, 0.03), (s * 0.115, 0.31, 0.0), (s * 0.1, 0.35, -0.02)], [0.014, 0.012, 0.0], 5)), "Dark")
        # the ears pinned back and out
        ear = ball((0, 0, 0), (0.05, 0.16, 0.025), 10, 5)
        xf(ear, Matrix.Rotation(math.radians(s * 35), 3, "Z") @ Matrix.Rotation(math.radians(20), 3, "X"), (s * 0.19, -0.1, 0.1))
        P.obj("Ear", st_H(ear), st_hp(lambda c, nn, s=s: "Belly" if nn.z > 0.6 else "Base"))

        # ---- the antlers: a royal head of six points a side
        ped = Vector((s * 0.085, 0.06, 0.13))
        beam = bez(ped, (s * 0.42, -0.14, 0.3), (s * 0.62, -0.26, 0.72), (s * 0.48, -0.08, 1.02), 14)
        BR = [0.05 - 0.032 * (i / 14) for i in range(15)]; BR[-1] = 0.0
        tipcol = lambda base, L: (lambda c, nn: "Belly" if (HI @ (c - HB) - base).length > L * 0.72 else "Glass")
        P.obj("Antler", st_H(pipe(beam, BR, 9)), st_hp(lambda c, nn: "Belly" if c.z > 1.05 else "Glass"))
        P.obj("Pedicle", st_H(pipe([ped - Vector((0, 0, 0.06)), ped], [0.05, 0.048], 9)), "Base")
        burr = torus(0.058, 0.02, 0.0, 14, 5); xf(burr, None, tuple(ped + Vector((0, 0, 0.01))))
        P.obj("Burr", st_H(burr), "Glass")
        band = torus(0.05, 0.014, 0.0, 14, 5); xf(band, None, tuple(beam[1] + Vector((0, 0, -0.01))))
        P.obj("CrownBand", st_H(band), "Trim")
        for k in range(6):   # pearling: knobs set evenly round the lower beam
            i = 1 + k // 3; q = beam[i]; t, side, up = spine_frames(beam)[i]
            a = 2 * math.pi * (k % 3) / 3 + i
            nn = (side * math.cos(a) + up * math.sin(a)).normalized()
            P.obj("Pearl", st_H(ball(tuple(q + nn * BR[i] * 0.9), (0.011,) * 3, 6, 3)), "Glass")
        def tine(i, d, curl, r0, name="Tine"):
            b = beam[i]; d = Vector(d); L = d.length
            pts = bez(b, b + d * 0.4, b + d * 0.8 + Vector((0, 0, curl)), b + d + Vector((0, -curl * 0.3, curl * 1.4)), 6)
            P.obj(name, st_H(pipe(pts, [r0 * (1 - j / 6) ** 0.8 for j in range(7)], 7)), st_hp(tipcol(b, L + curl)))
            return pts
        tine(1, (-s * 0.03, 0.36, 0.05), 0.12, 0.036)       # brow tine
        tine(3, (s * 0.02, 0.3, 0.04), 0.1, 0.032)          # bez tine
        trez = tine(7, (s * 0.1, 0.32, 0.03), 0.1, 0.03)    # trez tine
        tine(11, (s * 0.14, 0.14, 0.22), 0.05, 0.026)       # the crown of three: two from the cup, the beam's end the third
        tine(11, (-s * 0.06, -0.16, 0.22), 0.05, 0.026)
        # a lantern hung on a chain from the trez tine
        q = trez[3] + Vector((0, 0, -0.01)); bot = q + Vector((0, 0, -0.2))
        P.obj("Chain", st_H(pipe([q, bot], [0.008, 0.008], 4)), "Metal")
        L0 = bot
        P.obj("LanternCap", st_H(lathe([(0.0, 0.0), (0.035, -0.02), (0.06, -0.05), (0.055, -0.06)], 8, "z", tuple(L0))), "Trim")
        P.obj("Lantern", st_H(lathe([(0.05, -0.06), (0.055, -0.16), (0.0, -0.17)], 8, "z", tuple(L0))), "Lamp")
        for k in range(4):
            a = 2 * math.pi * (k + 0.5) / 4
            P.obj("LanternBar", st_H(pipe([L0 + Vector((math.cos(a) * 0.056, math.sin(a) * 0.056, -0.06)), L0 + Vector((math.cos(a) * 0.058, math.sin(a) * 0.058, -0.165))], [0.008, 0.008], 4)), "Metal")
        P.obj("LanternBase", st_H(lathe([(0.0, -0.165), (0.06, -0.165), (0.06, -0.18), (0.0, -0.19)], 8, "z", tuple(L0))), "Trim")

    # ---- the bridle: crimson brow band and noseband joined by cheek straps, gold studs at even steps, a medallion on the forehead
    def strap(pts, stud_every=0.05):
        pts = [Vector(p) for p in pts]
        P.obj("Bridle", st_H(pipe(pts, [0.016] * len(pts), 6)), "Accent")
        acc = 0.0
        for a, b in zip(pts, pts[1:]):
            L = (b - a).length; x = (stud_every - acc) % stud_every
            while x < L:
                P.obj("Stud", st_H(ball(tuple(a + (b - a) * (x / L)), (0.012,) * 3, 6, 3)), "Trim"); x += stud_every
            acc = (acc + L) % stud_every
    arc = lambda y, rx, rz, zc, a0, a1, m: [(math.sin(math.radians(a0 + (a1 - a0) * k / m)) * rx, y, zc + math.cos(math.radians(a0 + (a1 - a0) * k / m)) * rz) for k in range(m + 1)]
    strap(arc(0.1, 0.158, 0.148, 0.02, -85, 85, 12))                                  # brow band over the forehead, under the antlers
    strap(arc(0.42, 0.098, 0.088, -0.02, -120, 120, 14))                              # noseband
    for s in (1, -1):
        strap([(s * 0.157, 0.1, 0.0), (s * 0.13, 0.26, -0.04), (s * 0.095, 0.42, -0.06)])
    P.obj("Medallion", st_H(lathe([(0.0, 0.0), (0.05, 0.0), (0.05, 0.015), (0.0, 0.025)], 14, "y", (0, 0.13, 0.15))), "Trim")
    P.obj("MedalGem", st_H(ball((0, 0.16, 0.16), (0.022, 0.012, 0.022), 8, 4)), "Glow")

    # ---- the caparison: a crimson cloth draped over his back, gold border with crimson lozenges, a scalloped hem with gold tassels
    def spine_at(y):
        i = min(range(len(neck) - 1, n - 1), key=lambda k: abs(PTS[k].y - y))
        return PTS[i], RX[i], RU[i], RD[i]
    Y0, Y1, NU, NV = 0.42, -0.86, 16, 14
    HANG = 0.28
    def cap_pt(u, v, lift=0.0):
        """u along the back 0..1 (front to rump); v from -1 (left hem) through 0 (the spine) to 1 (right hem)."""
        y = Y0 + (Y1 - Y0) * u; p, rx, ru, rd = spine_at(y)
        s = 1 if v >= 0 else -1; w = abs(v); g = 0.035 + lift
        if w <= 0.6:
            a = (w / 0.6) * math.pi / 2
            return Vector((s * math.sin(a) * (rx + g), y, p.z + math.cos(a) * (ru + g)))
        return Vector((s * (rx + g), y, p.z - (w - 0.6) / 0.4 * HANG))
    def hem(u): return 1.0 + 0.09 * abs(math.sin(math.pi * u * 4))   # four scallops a side: v past 1 dips in a point
    field, border = [], []
    for i in range(NU):
        for j in range(-NV, NV):
            u0, u1, v0, v1 = i / NU, (i + 1) / NU, j / NV, (j + 1) / NV
            def V(u, v): return tuple(cap_pt(u, v * hem(u) if abs(v) > 0.999 else v))
            quad = [V(u0, v0), V(u1, v0), V(u1, v1), V(u0, v1)]
            edge = min(u0, 1 - u1) < 1.0 / NU + 1e-6 or max(abs(v0), abs(v1)) > 1 - 2.0 / NV + 1e-6
            (border if edge else field).append(quad)
    P.part("Cloth", st_cloth(field, 0.016), "Accent", (0, 0, 0), 0, True)
    P.part("ClothBorder", st_cloth(border, 0.02), "Trim", (0, 0, 0), 0, True)
    for s in (1, -1):
        for k in range(8):   # crimson lozenges evenly along the gold border of each flank
            u = (k + 0.5) / 8; c = cap_pt(u, s * (1 - 1.0 / NV), 0.012)
            P.part("ClothLozenge", st_sheet([[tuple(c + Vector((0, 0.035, 0))), tuple(c + Vector((0, 0, 0.022))), tuple(c + Vector((0, -0.035, 0))), tuple(c + Vector((0, 0, -0.022)))]], 0.01), "Accent", (0, 0, 0), 0, False)
        for k in range(5):   # a gold tassel at each scallop point
            u = k / 4; c = cap_pt(u, s * hem(u))
            P.obj("Tassel", pipe([c, c + Vector((0, 0, -0.04)), c + Vector((0, 0, -0.1))], [0.012, 0.022, 0.0], 6), "Trim", 0)
        # a gold maple leaf on each flank
        c = cap_pt(0.5, s * 0.72, 0.012)
        P.part("ClothEmblem", leaf(tuple(c), 0.12, (0, 1, 0), (0, 0, 1), 0.012), "Trim", (0, 0, 0), 0, False)
    # the breast strap round the chest with a gold medallion, and the girth strap under the belly
    C0 = Vector((0, 0.5, 0.12)); F = Vector((0, 0.8, -0.6)).normalized()
    br = [onbody(C0, F * math.cos(math.radians(a)) + Vector((math.sin(math.radians(a)), 0, 0)) + Vector((0, 0, 0.25 * (abs(a) / 90) ** 2)), 0.02) for a in range(-90, 91, 10)]
    br = [q + (q - C0).normalized() * 0.01 for q in br]
    P.obj("BreastStrap", pipe(br, [0.026] * len(br), 6), "Accent")
    for q in br[1:-1:2]: P.obj("Stud", ball(tuple(q + (q - C0).normalized() * 0.03), (0.016,) * 3, 6, 3), "Trim")
    P.obj("BreastMedal", lathe([(0.0, 0.0), (0.075, 0.0), (0.075, 0.02), (0.0, 0.035)], 16, "y", tuple(br[9] + F * 0.0)), "Trim")
    P.obj("BreastGem", ball(tuple(br[9] + Vector((0, 0.035, 0))), (0.03, 0.015, 0.03), 8, 4), "Glow")
    p, rx, ru, rd = spine_at(0.22)
    gs = [onbody((0, 0.22, p.z), (math.sin(math.radians(a)), 0, math.cos(math.radians(a))), 0.015) for a in range(105, 256, 10)]
    P.obj("Girth", pipe(gs, [0.022] * len(gs), 6), "Accent")

    P.part("Muzzle", st_H(ball((0, 0.46, -0.08), (0.045, 0.03, 0.035), 8, 4)), "Glow", tuple(st_hpt((0, 0.46, -0.08))))
    st_whirlwind(P)
    st_scale(P, 0.72)
    return P


WY, WTOP, WBOT, WR = -0.27, -0.93, -2.65, 1.02   # the whirlwind's axis (y), rim height, point height and rim radius

def st_wr(u):
    """the funnel's radius at height u (0 at the point, 1 at the rim): a narrow stem flaring into a wide cup."""
    return 0.06 + (WR - 0.06) * u ** 1.45

def st_helix(u, a0, turns, k=1.0, sense=1):
    a = a0 + sense * 2 * math.pi * turns * u
    r = st_wr(u) * k
    return Vector((math.cos(a) * r, WY + math.sin(a) * r, WBOT + (WTOP - WBOT) * u)), a

def st_oak(c, size, u, v, n=36):
    """an oak leaf: an oval with five rounded lobes a side and a short stalk, in the plane of u (across) and v (along)."""
    c, u, v = Vector(c), Vector(u), Vector(v)
    pts = []
    for i in range(n):
        t = 2 * math.pi * i / n
        x, y = math.sin(t), -math.cos(t)
        r = size * (1 - 0.18 * abs(math.sin(5 * t)))
        pts.append(c + u * x * r * 0.55 + v * y * r)
    polys = [[c, a, b] for a, b in zip(pts, pts[1:] + pts[:1])]
    return st_sheet([[tuple(p) for p in q] for q in polys], 0.012)

def st_whirlwind(P):
    hub = (0, WY, (WTOP + WBOT) * 0.5)
    # the wind: pale streaks spiralling up the funnel, inner layer one way, outer layer a little wider
    def streak(name, a0, turns, k, w0, w1, u0=0.02, u1=1.0, sense=1, m=40):
        quads = []
        prev = None
        for i in range(m + 1):
            u = u0 + (u1 - u0) * i / m
            p, a = st_helix(u, a0, turns, k, sense)
            w = (w0 + (w1 - w0) * u) * math.sin(math.pi * i / m) ** 0.5 + 0.004   # tapering to a point at each end
            row = (p - Vector((0, 0, w * 0.5)), p + Vector((0, 0, w * 0.5)))
            if prev: quads.append([tuple(prev[0]), tuple(row[0]), tuple(row[1]), tuple(prev[1])])
            prev = row
        P.part(name, st_cloth(quads, 0.012), "Belly", hub, 0, True)
    for j in range(5):
        streak("SpinA", 2 * math.pi * j / 5, 1.15, 0.9, 0.05, 0.16)
    for j in range(4):
        streak("SpinB", 2 * math.pi * (j + 0.5) / 4, 0.9, 1.06, 0.03, 0.11, 0.2, 1.0)
    # the leaves caught in the outer spirals: evenly along each band, closer and bigger toward the top
    cols = ("Accent", "Trim", "Base")
    n = 0
    for j in range(4):
        a0 = 2 * math.pi * (j + 0.5) / 4
        for k in range(7):
            u = 0.3 + 0.7 * math.sqrt((k + 0.5) / 7)
            p, a = st_helix(u, a0, 0.9, 1.1)
            tan = Vector((-math.sin(a), math.cos(a), 0.25)).normalized(); out = Vector((math.cos(a), math.sin(a), 0))
            v = (tan + Vector((0, 0, 0.6)) + out * 0.3 * ((k % 3) - 1)).normalized(); uu = v.cross(out).normalized()
            size = 0.07 + 0.11 * u
            bm = leaf(tuple(p), size, tuple(uu), tuple(v), 0.012) if n % 2 == 0 else st_oak(p, size * 1.1, uu, v)
            P.part("SpinB", bm, cols[n % 3], hub, 0, True)
            P.part("SpinB", pipe([p - v * size * 0.55, p - v * size * 0.9], [0.008, 0.004], 4), "Dark", hub, 0, True)   # the stalk
            n += 1
    # a few twigs and acorns tumbling in it, half way up, between the bands
    for j in range(3):
        u = 0.45 + 0.12 * j; a0 = 2 * math.pi * j / 3 + 0.4
        p, a = st_helix(u, a0, 0.9, 1.0)
        d = Vector((math.cos(a + 1.2), math.sin(a + 1.2), 0.5)).normalized()
        P.part("SpinB", pipe([p - d * 0.14, p, p + d * 0.14], [0.014, 0.012, 0.006], 5), "Dark", hub, 0, True)
        f = p + d * 0.03
        P.part("SpinB", pipe([f, f + (d + Vector((0, 0, 0.8))).normalized() * 0.08], [0.008, 0.003], 4), "Dark", hub, 0, True)
        q, a = st_helix(u + 0.06, a0 + 2.0, 0.9, 1.0)
        P.part("SpinB", ball(tuple(q - Vector((0, 0, 0.012))), (0.032, 0.032, 0.042), 8, 4), "Base", hub, 0, True)   # the nut
        P.part("SpinB", ball(tuple(q + Vector((0, 0, 0.02))), (0.038, 0.038, 0.022), 8, 4), "Dark", hub, 0, True)     # its scaly cap

def st_scale(P, k):
    """everything drawn k times smaller about the origin (the whirlwind made him too tall)."""
    m = Matrix.Scale(k, 4)
    for ob in P.parts: ob.data.transform(m)
    for ob in P.spin: ob.data.transform(m); ob.location = ob.location * k



# ================================================================= squirrel
# ================================================================= squirrel knight helpers
def sq_axes(n, up=(0, 0, 1)):
    """(across, up, out) unit axes for something facing n."""
    n = Vector(n).normalized(); up = Vector(up)
    x = up.cross(n)
    if x.length < 1e-4: x = Vector((1, 0, 0))
    x.normalize(); y = n.cross(x).normalized()
    return x, y, n

def sq_fan(center, outline, nrm, thick, bulge=0.0, bulge_fn=None):
    """a closed flat solid: the outline (a loop of points round center) filled as a fan, thick along nrm; bulge pushes the middle out
    (bulge_fn(point) -> extra offset along nrm, for a curved shield)."""
    n = Vector(nrm).normalized(); h = n * thick * 0.5; c = Vector(center)
    off = bulge_fn or (lambda p: 0.0)
    bm = bmesh.new()
    ct = bm.verts.new(c + h + n * bulge); cb = bm.verts.new(c - h + n * bulge * 0.6)
    top = [bm.verts.new(Vector(p) + h + n * off(Vector(p))) for p in outline]
    bot = [bm.verts.new(Vector(p) - h + n * off(Vector(p))) for p in outline]
    m = len(outline)
    for i in range(m):
        j = (i + 1) % m
        bm.faces.new((ct, top[i], top[j])); bm.faces.new((cb, bot[j], bot[i]))
        bm.faces.new((top[i], bot[i], bot[j], top[j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm

def sq_maple_outline(c, size, u, v, n=96):
    """a real sugar-maple leaf about c (v up the leaf, u across): three big pointed lobes and two small basal ones, rounded sinuses between
    them, even teeth along each lobe's edge, and a notch at the base where the stalk joins. Returns (outline, lobe tips)."""
    c, u, v = Vector(c), Vector(u), Vector(v)
    lobes = [(0.0, 1.0), (0.95, 0.88), (-0.95, 0.88), (1.95, 0.5), (-1.95, 0.5)]
    def r_at(th):
        r = 0.42; best = 0.0
        for a, L in lobes:
            d = abs(math.atan2(math.sin(th - a), math.cos(th - a)))
            f = max(0.0, 1 - d / 0.62) ** 1.25
            r += L * 0.62 * f; best = max(best, f)
        if best > 0.12: r *= 1 + 0.05 * (abs(((th * 30 / math.pi) % 2) - 1) - 0.5) * 2   # the teeth
        if abs(th) > 2.7: r *= 0.55   # the notch at the stalk
        return r * size
    pts = []
    for i in range(n):
        th = -math.pi + 2 * math.pi * i / n
        r = r_at(th); pts.append(c + v * math.cos(th) * r + u * math.sin(th) * r)
    tips = [c + v * math.cos(a) * r_at(a) + u * math.sin(a) * r_at(a) for a, L in lobes]
    return pts, tips

# ================================================================= the squirrel knight
def A_squirrel():
    """The SQUIRREL KNIGHT (2026-10-13, remade: "same as the alien bosses - realistic details, scarier, keep the cartoon shape"): the same
    big-headed red squirrel in armour, now flying like a maple seed and built like the real animal and like real armour. A red squirrel's
    body - rust-red fur, a cream chest and chin, the pale ring round each eye, long tufted ears pinned back in anger (the left one notched
    from an old fight), a short blunt muzzle with a cleft lip, a dark nose and four whiskers a side fanning from the whisker pads; the lips
    are drawn back in a snarl over the long orange-enamelled incisors of a rodent, two above and two below, the snout creased above them,
    and the black eyes are narrowed under heavy lids and a scowling brow, an ember glint in each. Big haunches, long hind feet with five
    clawed toes, four long clawed fingers on each hand. His tail is a real squirrel's tail: one S-curve sweeping up behind him, its tip curled
    back, flattened side to side, the fur in long soft locks lying back along it and overlapping row on row, longest at the sides; it
    swings as his rudder. The armour is real plate: a brass-gilt sallet with a raised comb,
    rivets round the brim and a flared tail over the nape, its visor raised on two pivots so the face shows under the sight slit, and a fan
    of seven red plume feathers set in a holder at the back; a two-lame gorget, a keeled cuirass with a maple leaf on it, a fauld of three
    riveted lames, pauldrons of three overlapping lames, couters at the elbows and vambraces. On his right arm a heater shield - crimson,
    gold rim, rivets evenly round it, a painted acorn with a scaled cap; in his left fist a flanged mace with seven flanges, a top spike, a
    leather-wrapped grip and a pommel. A crimson cape behind. He flies as a maple-seed helicopter: a wooden backpack frame (two rails, three
    cross bars, brass standoffs) buckled on with leather shoulder straps carries a brass-banded mast up past his helm, and on its brass
    hub turns a pair of real maple samaras as the rotor - the plump veined nutlets joined at the hub, the long papery wings curving out,
    a thick vein down each leading edge and fine veins fanning from the nutlet to the trailing edge, red by the seed fading to gold at
    the tip, the way maple seeds spin down in autumn. He spits his shots."""
    P = Boss("squirrel", pal(Base=((0.66, 0.24, 0.07), 0.35), Belly=((0.96, 0.86, 0.68), 0.3), Accent=((0.24, 0.11, 0.05), 0.4),
                             Trim=((0.98, 0.62, 0.12), 0.75), Glass=((0.62, 0.05, 0.05), 0.5), Dark=((0.04, 0.025, 0.02), 0.7),
                             Glow=((1.0, 0.55, 0.12), 0.5), Metal=((0.78, 0.58, 0.28), 0.85), Lamp=((1.0, 0.95, 0.85), 0.9)))
    fine = lambda bm, paint: P.part("ClothDetail", bm, paint, (0, 0, 0))   # thin details: no toon outline

    # ---- the body: a pear of fur, cream down the chest; big haunches; long hind feet
    P.obj("Torso", ball((0, -0.04, 0.02), (0.38, 0.34, 0.55), 18, 10), lambda c, n: "Belly" if n.y > 0.45 and abs(c.x) < 0.2 else "Base", 1)
    for s in (1, -1):
        P.obj("Haunch", ball((s * 0.27, -0.08, -0.32), (0.2, 0.3, 0.24), 14, 7), lambda c, n: "Belly" if n.y > 0.6 else "Base", 1)
        heel = Vector((s * 0.3, -0.04, -0.55)); toe = Vector((s * 0.33, 0.5, -0.66))
        P.obj("HindFoot", pipe(bez(heel, heel + Vector((0, 0.15, -0.04)), toe - Vector((0, 0.2, 0)), toe, 6), [0.08, 0.09, 0.085, 0.08, 0.075, 0.07, 0.06], 10),
              lambda c, n: "Accent" if n.z < -0.6 else "Base")
        for k in range(5):   # five toes, spread evenly, each with a dark curved claw
            a = math.radians(-36 + 18 * k); d = Vector((math.sin(a) * 0.45, math.cos(a), -0.15)).normalized()
            b = toe + Vector((s * math.sin(a) * 0.05, 0, 0))
            t1 = b + d * (0.13 if k in (1, 2, 3) else 0.09)
            P.obj("Toe", pipe([b, t1], [0.035, 0.03], 7), "Base")
            fine(pipe(bez(t1, t1 + d * 0.04, t1 + d * 0.07 + Vector((0, 0, -0.02)), t1 + d * 0.08 + Vector((0, 0, -0.06)), 4), [0.022, 0.018, 0.012, 0.006, 0.0], 5), "Dark")

    # ---- the cuirass: a keeled breastplate with a maple leaf, a two-lame gorget, a fauld of three riveted lames, a belt
    P.obj("Cuirass", ball((0, 0.02, 0.1), (0.4, 0.37, 0.42), 22, 10), lambda c, n: "Trim" if abs(c.x) < 0.025 and n.y > 0.2 else "Metal", 1)
    P.obj("Keel", hull([(-0.02, 0.37, 0.42), (0.02, 0.37, 0.42), (-0.02, 0.4, 0.05), (0.02, 0.4, 0.05), (0, 0.42, 0.2)]), "Trim", 0, False)
    lo, ti = sq_maple_outline((0, 0.43, 0.1), 0.13, (1, 0, 0), Vector((0, 0.12, 1)).normalized())
    P.obj("Emblem", sq_fan((0, 0.43, 0.1), lo, (0, 1, -0.12), 0.025), "Glass", 0, False)
    for k in range(2):   # the gorget
        P.obj("Gorget", xf(lathe([(0.25 - 0.03 * k, 0.0), (0.3 - 0.03 * k, 0.05), (0.26 - 0.03 * k, 0.1), (0.0, 0.1)], 28, "z"), None, (0, 0.04, 0.46 + 0.07 * k)),
              lambda c, n: "Trim" if n.z > 0.5 else "Metal")
    for k in range(3):   # the fauld: three lames below the waist, each flaring a little more, riveted along the edge
        z0 = -0.26 - 0.1 * k; r0 = 0.39 + 0.03 * k
        P.obj("Fauld", xf(lathe([(r0 - 0.02, 0.0), (r0 + 0.05, -0.12), (r0 + 0.02, -0.13), (0.0, -0.13)][:3] + [(r0 - 0.04, 0.0)], 30, "z"), None, (0, 0.0, z0)),
              lambda c, n, z0=z0: "Trim" if c.z < z0 - 0.1 else "Metal")
        for j in range(7):
            a = math.radians(-60 + 20 * j)
            fine(ball((math.sin(a) * (r0 + 0.035), math.cos(a) * (r0 + 0.035), z0 - 0.04), (0.018, 0.018, 0.018), 6, 3), "Trim")
    P.obj("Belt", xf(torus(0.405, 0.04, 0.0, 30, 6), None, (0, 0.0, -0.22)), "Accent")
    P.obj("Buckle", box((0, 0.43, -0.22), (0.12, 0.03, 0.1)), "Trim", 0, False)
    P.obj("Tongue", box((0, 0.45, -0.22), (0.02, 0.02, 0.1)), "Accent", 0, False)

    # ---- the head
    hc = Vector((0, 0.14, 0.88))
    P.obj("Head", ball(tuple(hc), (0.36, 0.34, 0.33), 20, 10), lambda c, n: "Belly" if n.y > 0.35 and c.z < hc.z - 0.1 else "Base", 1)
    mz = Vector((0, hc.y + 0.27, hc.z - 0.1))
    P.obj("Muzzle", ball(tuple(mz), (0.17, 0.17, 0.13), 14, 7), lambda c, n: "Belly" if c.z < mz.z - 0.03 else "Base", 1)
    for s in (1, -1):
        P.obj("WhiskerPad", ball((s * 0.075, mz.y + 0.12, mz.z - 0.05), (0.075, 0.06, 0.06), 10, 5), "Belly")
    P.obj("Nose", hull([(-0.05, mz.y + 0.16, mz.z + 0.05), (0.05, mz.y + 0.16, mz.z + 0.05), (0, mz.y + 0.19, mz.z + 0.02), (0, mz.y + 0.17, mz.z - 0.01),
                        (-0.035, mz.y + 0.13, mz.z + 0.06), (0.035, mz.y + 0.13, mz.z + 0.06)]), "Dark", 0)
    fine(pipe([(0, mz.y + 0.18, mz.z), (0, mz.y + 0.18, mz.z - 0.05)], [0.008, 0.008], 4), "Dark")   # the cleft of the lip
    for k in range(3):   # the snarl: creases across the top of the snout
        z = mz.z + 0.08 + 0.025 * k; y = mz.y + 0.12 - 0.04 * k
        fine(pipe(bez((-0.08, y - 0.02, z - 0.01), (-0.03, y + 0.01, z + 0.01), (0.03, y + 0.01, z + 0.01), (0.08, y - 0.02, z - 0.01), 5), [0.006, 0.01, 0.011, 0.011, 0.01, 0.006], 4), "Accent")
    # the mouth drawn back: dark gums, the incisors bared - long, orange-enamelled, two above and two below
    P.obj("Mouth", hull([(-0.1, mz.y + 0.09, mz.z - 0.08), (0.1, mz.y + 0.09, mz.z - 0.08), (-0.07, mz.y + 0.11, mz.z - 0.17), (0.07, mz.y + 0.11, mz.z - 0.17),
                         (0, mz.y + 0.15, mz.z - 0.09), (0, mz.y + 0.13, mz.z - 0.17), (0, mz.y + 0.02, mz.z - 0.12)]), "Dark", 0, False)
    for s in (1, -1):
        b = Vector((s * 0.026, mz.y + 0.155, mz.z - 0.07))
        P.obj("Incisor", pipe(bez(b, b + Vector((0, 0.025, -0.06)), b + Vector((0, 0.02, -0.14)), b + Vector((0, -0.01, -0.19)), 5), [0.028, 0.03, 0.03, 0.028, 0.022, 0.01], 6),
              lambda c, n: "Belly" if n.y < -0.3 else "Trim")
        b = Vector((s * 0.02, mz.y + 0.11, mz.z - 0.22))
        P.obj("Incisor", pipe(bez(b, b + Vector((0, 0.02, 0.03)), b + Vector((0, 0.03, 0.05)), b + Vector((0, 0.035, 0.07)), 4), [0.018, 0.018, 0.016, 0.012, 0.006], 6), "Trim")
    P.obj("Chin", ball((0, mz.y + 0.05, mz.z - 0.2), (0.09, 0.08, 0.06), 10, 5), "Belly")
    for s in (1, -1):
        for k in range(4):   # four whiskers a side, fanned evenly from the pad
            b = Vector((s * 0.12, mz.y + 0.13, mz.z - 0.03 - 0.025 * k))
            d = Vector((s * 1.0, 0.25 - 0.1 * k, 0.18 - 0.14 * k)).normalized()
            fine(pipe(bez(b, b + d * 0.11, b + d * 0.22 + Vector((0, -0.02, -0.01)), b + d * 0.32 + Vector((0, -0.05, -0.03)), 5), [0.006, 0.005, 0.004, 0.003, 0.002, 0.001], 4), "Dark")
    # the eyes: black and glossy in a pale eye ring, narrowed by heavy lids slanting down to the nose, a scowling brow, an ember glint
    for s in (1, -1):
        e = Vector((s * 0.205, hc.y + 0.235, hc.z + 0.04)); en = Vector((s * 0.62, 0.78, 0.05)).normalized()
        x, y, n = sq_axes(en)
        P.obj("EyeRing", oriented_ball(e - n * 0.01, (0.115, 0.1, 0.05), x, y, n, 14, 6), "Belly")
        P.obj("Eye", oriented_ball(e + n * 0.02, (0.085, 0.075, 0.05), x, y, n, 14, 7), "Dark")
        fine(oriented_ball(e + n * 0.068 + y * 0.025 - x * s * 0.02, (0.018, 0.018, 0.01), x, y, n, 8, 4), "Lamp")
        fine(oriented_ball(e + n * 0.064 - y * 0.03 + x * s * 0.025, (0.022, 0.012, 0.01), x, y, n, 8, 4), "Glow")
        def lp(ax, ay, az): return tuple(e - x * ax + y * ay + n * az)   # ax > 0 toward the outer corner
        # upper lid: a thick fold over the top of the eye, lowest at the inner corner (toward the nose)
        P.obj("Lid", hull([lp(-s * 0.11, -0.005, 0.03), lp(-s * 0.1, 0.06, 0.0), lp(s * 0.11, 0.045, 0.03), lp(s * 0.1, 0.1, 0.0),
                           lp(0, 0.04, 0.075), lp(0, 0.09, 0.05), lp(-s * 0.08, 0.02, 0.07), lp(s * 0.08, 0.06, 0.07)]), "Base", 0)
        P.obj("LowerLid", hull([lp(-s * 0.09, -0.04, 0.02), lp(s * 0.09, -0.05, 0.02), lp(0, -0.075, 0.03), lp(0, -0.06, 0.06), lp(-s * 0.06, -0.05, 0.05), lp(s * 0.06, -0.055, 0.05)]), "Belly", 0)
        P.obj("Brow", pipe([lp(-s * 0.13, 0.05, 0.05), lp(0, 0.12, 0.07), lp(s * 0.14, 0.17, 0.03)], [0.035, 0.04, 0.025], 7), "Accent")
    # the ears: long, pinned back in anger, a cream inside, a tuft of dark winter hairs fanned from each tip; the left one notched
    for s in (1, -1):
        b = Vector((s * 0.2, hc.y - 0.08, hc.z + 0.24)); t = Vector((s * 0.33, hc.y - 0.42, hc.z + 0.5))
        w = Vector((0, 0.1, 0.05))
        ear = [b + w, b - w, (b * 0.4 + t * 0.6) + w * 0.9, (b * 0.4 + t * 0.6) - w * 0.9, t]
        P.obj("Ear", hull([tuple(p + Vector((s * 0.03, 0, 0))) for p in ear] + [tuple(p - Vector((s * 0.03, 0, 0))) for p in ear]), "Base", 0, False)
        P.obj("EarInside", hull([tuple(p + Vector((s * 0.035, 0, 0))) for p in [b + w * 0.6, b - w * 0.6, (b * 0.45 + t * 0.55) + w * 0.5, (b * 0.45 + t * 0.55) - w * 0.5, b * 0.15 + t * 0.85]]
                                + [tuple(p + Vector((s * 0.045, 0, 0))) for p in [b + w * 0.4, b - w * 0.4, b * 0.2 + t * 0.8]]), "Belly", 0, False)
        if s < 0:   # the notch: a dark nick out of the left ear's back edge
            q = b * 0.35 + t * 0.65 - w * 0.9
            P.obj("Notch", ball(tuple(q), (0.05, 0.035, 0.035), 8, 4), "Dark")
        for k in range(7):
            a = math.radians(-45 + 15 * k)
            d = (Vector((0, -0.55, 0.85)).normalized() * math.cos(a) + Vector((s, 0, 0)) * math.sin(a) * 0.6).normalized()
            fine(cone(t - (t - b).normalized() * 0.03, t + d * (0.2 - 0.05 * abs(k - 3) / 3), 0.02, 4), "Accent")
        P.obj("EarGuard", xf(torus(0.07, 0.022, 0.0, 14, 5), Matrix.Rotation(math.radians(s * -35), 3, "Y"), tuple(b + Vector((0, 0, 0.02)))), "Trim")

    # ---- the sallet: a brass-gilt dome with a raised comb and a flared tail over the nape, rivets round the brim, the visor raised
    hb = Vector((0, hc.y - 0.04, 0))
    P.obj("Helm", xf(lathe([(0.37, hc.z + 0.1), (0.375, hc.z + 0.2), (0.33, hc.z + 0.33), (0.22, hc.z + 0.43), (0.0, hc.z + 0.47)], 32, "z"), None, tuple(hb)),
          lambda c, n: "Trim" if c.z < hc.z + 0.12 else "Metal", 1)
    P.obj("Comb", hull([(-0.018, hc.y + 0.25, hc.z + 0.36), (0.018, hc.y + 0.25, hc.z + 0.36), (-0.018, hc.y - 0.35, hc.z + 0.36), (0.018, hc.y - 0.35, hc.z + 0.36),
                        (0, hc.y + 0.1, hc.z + 0.55), (0, hc.y - 0.2, hc.z + 0.56), (0, hc.y + 0.2, hc.z + 0.45), (0, hc.y - 0.3, hc.z + 0.47)]), "Trim", 0, False)
    def tail_pt(a, k):   # the sallet's tail: the brim swept back and down over the nape
        r = 0.37 + 0.18 * k; return Vector((math.sin(a) * r, hb.y - math.cos(a) * r * 1.05, hc.z + 0.12 - 0.12 * k))
    tq = []
    for i in range(10):
        a0, a1 = math.radians(-70 + 14 * i), math.radians(-70 + 14 * (i + 1))
        tq.append([tuple(tail_pt(a0, 0)), tuple(tail_pt(a1, 0)), tuple(tail_pt(a1, 1)), tuple(tail_pt(a0, 1))])
    for q in tq:
        P.obj("SalletTail", hull([tuple(Vector(p) + Vector((0, 0, 0.015))) for p in q] + [tuple(Vector(p) - Vector((0, 0, 0.015))) for p in q]), "Metal", 0, False)
    for k in range(18):
        a = 2 * math.pi * k / 18
        if abs(math.atan2(math.sin(a), math.cos(a))) < 0.2: continue
        fine(ball((math.sin(a) * 0.385, hb.y + math.cos(a) * 0.385, hc.z + 0.15), (0.02, 0.02, 0.02), 6, 3), "Trim")
    # the visor, raised on two pivots: a curved plate over the brow, its sight slit dark
    for i in range(12):
        a0, a1 = math.radians(-70 + 140 * i / 12), math.radians(-70 + 140 * (i + 1) / 12)
        for (z0, z1, paint) in ((hc.z + 0.2, hc.z + 0.255, "Metal"), (hc.z + 0.255, hc.z + 0.275, "Dark"), (hc.z + 0.275, hc.z + 0.36, "Metal")):
            def vp(a, z, r): rr = r - (z - hc.z - 0.2) * 0.45; return (math.sin(a) * rr, hb.y + math.cos(a) * rr, z)
            P.obj("Visor", hull([vp(a0, z0, 0.42), vp(a1, z0, 0.42), vp(a0, z1, 0.42), vp(a1, z1, 0.42), vp(a0, z0, 0.395), vp(a1, z0, 0.395), vp(a0, z1, 0.395), vp(a1, z1, 0.395)]),
                  paint, 0, False)
    for s in (1, -1):
        P.obj("Pivot", oriented_ball((s * 0.385, hb.y + 0.06, hc.z + 0.24), (0.045, 0.045, 0.02), *sq_axes((s, 0, 0)), 10, 4), "Trim")
    # the plume: seven red feathers fanned from a holder at the back of the helm
    ph = Vector((0, hc.y - 0.3, hc.z + 0.42))
    P.obj("PlumeHolder", pipe([ph - Vector((0, -0.04, 0.08)), ph + Vector((0, -0.02, 0.06))], [0.04, 0.035], 8), "Trim")
    for k in range(7):
        a = math.radians(-36 + 12 * k)
        d = Vector((math.sin(a) * 0.6, -0.2, 0.78)).normalized()
        b = ph + Vector((0, -0.02, 0.06))
        pts = bez(b, b + d * 0.25, b + d * 0.45 + Vector((0, -0.1, 0.05)), b + d * 0.5 + Vector((math.sin(a) * 0.25, -0.3, 0.02)), 8)
        P.obj("Plume", pipe(pts, [0.02, 0.05, 0.075, 0.085, 0.085, 0.075, 0.06, 0.035, 0.0], 7), "Glass")
        fine(pipe(pts[:-1], [0.012] * 8, 4), "Trim")   # the quill down each feather

    # ---- the arms: fur, pauldrons of three lames, couters, vambraces, long clawed fingers
    for s in (1, -1):
        sh = Vector((s * 0.37, 0.02, 0.33)); el = Vector((s * 0.62, 0.1, 0.05)); wr = Vector((s * 0.66, 0.42, 0.02))
        P.obj("UpperArm", pipe([sh, (sh + el) * 0.5, el], [0.12, 0.11, 0.09], 10), "Base")
        P.obj("Forearm", pipe([el, wr], [0.09, 0.075], 10), "Base")
        P.obj("Vambrace", pipe([el + (wr - el) * 0.15, el + (wr - el) * 0.85], [0.1, 0.088], 12), lambda c, n: "Trim" if n.dot((wr - el).normalized()) > 0.5 else "Metal")
        for k in range(3):
            c = sh + Vector((s * (0.02 + 0.05 * k), 0, 0.08 - 0.09 * k))
            P.obj("Pauldron", ball(tuple(c), (0.22 - 0.02 * k, 0.21 - 0.015 * k, 0.11), 16, 6), lambda c2, n, c=c: "Trim" if c2.z < c.z - 0.02 else "Metal")
        for k in range(4):   # rivets along the top lame
            fine(ball(tuple(sh + Vector((s * 0.08, -0.12 + 0.08 * k, 0.185))), (0.018, 0.018, 0.018), 6, 3), "Trim")
        P.obj("Couter", ball(tuple(el), (0.1, 0.1, 0.1), 12, 6), "Metal")
        P.obj("CouterWing", hull([tuple(el + Vector((s * 0.06, -0.02, 0.1))), tuple(el + Vector((s * 0.06, -0.02, -0.1))), tuple(el + Vector((s * 0.13, -0.08, 0))),
                                  tuple(el + Vector((s * 0.04, -0.06, 0))), tuple(el + Vector((s * 0.08, 0.02, 0.0)))]), "Trim", 0, False)
        P.obj("Paw", ball(tuple(wr + Vector((0, 0.05, 0))), (0.085, 0.09, 0.075), 10, 5), "Base")
    # the right fist (+x) grips the shield; the left closes round the mace; four curled fingers each, a dark claw at each tip
    for s, grip in ((1, Vector((0.7, 0.5, 0.03))), (-1, Vector((-0.7, 0.52, 0.03)))):
        for k in range(4):
            z = grip.z + 0.06 - 0.04 * k
            b = Vector((s * 0.62, 0.5, z)); m = Vector((s * 0.67, 0.6, z)); e2 = Vector((s * 0.76, 0.58, z))
            P.obj("Finger", pipe([b, m, e2], [0.026, 0.024, 0.02], 6), "Base")
            fine(pipe(bez(e2, e2 + Vector((s * 0.02, -0.02, 0)), e2 + Vector((s * 0.03, -0.05, 0)), e2 + Vector((s * 0.02, -0.08, -0.01)), 3), [0.016, 0.012, 0.006, 0.0], 5), "Dark")

    # ---- the heater shield on his right arm: crimson field, gold rim, rivets round it, a painted acorn with a scaled cap
    sc = Vector((0.9, 0.62, 0.02)); W, T, B = 0.78, 0.42, -0.58
    out = []
    for i in range(20):   # right edge from the top corner down to the point, then back up the left
        t = i / 20; out.append(Vector((W * 0.5 * (1 - t ** 2.4) ** 0.7, 0, T - (T - B) * t)))
    out.append(Vector((0, 0, B)))
    out += [Vector((-p.x, 0, p.z)) for p in reversed(out[:-1])]
    out += [Vector((-W * 0.5 + W * k / 8, 0, T)) for k in range(1, 8)]
    rot = Matrix.Rotation(math.radians(-14), 3, "Z")   # turned a little toward his side
    place = lambda p: sc + rot @ p
    curve = lambda p: -0.5 * ((rot.transposed() @ (p - sc)).x) ** 2   # the shield curves back at the sides
    nrm = rot @ Vector((0, 1, 0))
    P.obj("Shield", sq_fan(tuple(sc), [place(p) for p in out], nrm, 0.05, 0.0, curve), "Glass", 0, False)
    rim = [place(p) + nrm * (0.03 + curve(place(p))) for p in out]
    P.obj("ShieldRim", pipe(rim + rim[:2], [0.03] * (len(rim) + 2), 6, False), "Trim")
    for i in range(0, len(out), 3):
        p = place(out[i] * 0.9); fine(ball(tuple(p + nrm * (0.03 + curve(p))), (0.022, 0.022, 0.022), 6, 3), "Trim")
    ac = Vector((0, 0, -0.1))
    def on(p, lift): q = place(p); return q + nrm * (lift + curve(q))
    x, y, n = sq_axes(nrm)
    P.obj("ShieldNut", oriented_ball(on(ac + Vector((0, 0, -0.06)), 0.03), (0.15, 0.19, 0.03), x, y, n, 16, 5), "Trim")
    P.obj("ShieldNutTip", oriented_ball(on(ac + Vector((0, 0, -0.24)), 0.035), (0.03, 0.04, 0.02), x, y, n, 8, 4), "Accent")
    P.obj("ShieldCap", oriented_ball(on(ac + Vector((0, 0, 0.1)), 0.04), (0.19, 0.1, 0.035), x, y, n, 16, 5), "Accent")
    for r in range(2):   # the cap's scales: two even rows
        for k in range(6 - r):
            p = ac + Vector((-0.13 + 0.26 * (k + 0.5 * r) / (5 - 0.0), 0, 0.12 - 0.06 * r))
            fine(oriented_ball(on(p, 0.07), (0.025, 0.02, 0.012), x, y, n, 6, 3), "Base")
    P.obj("ShieldStem", pipe([on(ac + Vector((0, 0, 0.19)), 0.05), on(ac + Vector((0.04, 0, 0.3)), 0.05)], [0.025, 0.018], 6), "Accent")

    # ---- the flanged mace in his left fist: a leather grip, a pommel, seven flanges round the head and a top spike
    mx, my = -0.72, 0.54
    P.obj("Haft", pipe([(mx, my, -0.42), (mx, my, 0.78)], [0.035, 0.035], 8), "Accent")
    for k in range(6):   # the leather wrap of the grip
        fine(xf(torus(0.04, 0.008, 0.0, 10, 4), None, (mx, my, -0.12 + 0.05 * k)), "Base")
    P.obj("Pommel", ball((mx, my, -0.46), (0.065, 0.065, 0.06), 10, 5), "Trim")
    P.obj("Collar", xf(lathe([(0.05, 0.0), (0.06, 0.03), (0.05, 0.06), (0.0, 0.06)], 12, "z"), None, (mx, my, 0.74)), "Trim")
    hz0, hz1 = 0.8, 1.12
    P.obj("MaceCore", pipe([(mx, my, hz0), (mx, my, hz1)], [0.055, 0.055], 10), "Metal")
    for k in range(7):
        a = 2 * math.pi * k / 7; d = Vector((math.cos(a), math.sin(a), 0))
        q = lambda r, z: tuple(Vector((mx, my, 0)) + d * r + Vector((0, 0, z)))
        side = Vector((-d.y, d.x, 0)) * 0.012
        pts = [q(0.04, hz0), q(0.04, hz1), q(0.09, hz0 + 0.0), q(0.21, hz0 + 0.15), q(0.16, hz1), q(0.07, hz1 + 0.03)]
        P.obj("Flange", hull([tuple(Vector(p) + side) for p in pts] + [tuple(Vector(p) - side) for p in pts]), "Metal", 0, False)
    P.obj("MaceTop", cone((mx, my, hz1), (mx, my, hz1 + 0.18), 0.05, 8), "Trim")

    # ---- the crimson cape, hanging from the pauldrons behind him
    def cape(u, v):
        a = math.radians(-75 + 150 * u)
        return (math.sin(a) * (0.42 + 0.22 * v), -0.2 - math.cos(a) * (0.28 + 0.2 * v), 0.48 - 1.05 * v + 0.04 * math.sin(u * 14))
    P.part("Cloth", sheet([[cape(i / 10, j / 5), cape((i + 1) / 10, j / 5), cape((i + 1) / 10, (j + 1) / 5), cape(i / 10, (j + 1) / 5)] for i in range(10) for j in range(5)], 0.02),
           lambda c, n: "Trim" if c.z < -0.5 else "Glass", (0, 0, 0), 0, False)

    # ---- the tail: one S-curve up behind him, its tip curled back (it steers like a rudder), flattened side to side; the fur in long soft
    # locks lying back along it, each overlapping the next row, longest along the sides
    tail = spline([(0.0, -0.32, -0.38), (0.0, -0.9, -0.3), (0.03, -1.3, 0.15), (0.04, -1.32, 0.75), (0.03, -1.18, 1.2), (0.0, -1.0, 1.38), (0.0, -0.92, 1.25)], 4)
    tb = tuple(tail[0])
    m = len(tail)
    rr = [0.12 + 0.28 * math.sin(math.pi * min(1.0, 0.12 + i / (m - 1) * 0.95)) for i in range(m)]
    rr[-1] = 0.1
    bm = bmesh.new(); rings = []; seg = 14
    for i, p in enumerate(tail):
        t = (tail[min(i + 1, m - 1)] - tail[max(i - 1, 0)]).normalized()
        sx = Vector((1, 0, 0)); up = t.cross(sx).normalized()
        rings.append([bm.verts.new(p + sx * math.cos(2 * math.pi * k / seg) * rr[i] * 1.15 + up * math.sin(2 * math.pi * k / seg) * rr[i] * 0.72) for k in range(seg)])
    P.part("SwayTail", AB.skin(bm, rings, seg), "Base", tb, 1)
    for i in range(1, m - 1):
        t = (tail[i + 1] - tail[i - 1]).normalized(); sx = Vector((1, 0, 0)); up = t.cross(sx).normalized()
        for k in range(10):
            a = 2 * math.pi * (k + 0.5 * (i % 2)) / 10
            d = (sx * math.cos(a) * 0.72 + up * math.sin(a) * 1.15).normalized()
            lat = abs(math.cos(a))
            q = tail[i] + sx * math.cos(a) * rr[i] * 1.05 + up * math.sin(a) * rr[i] * 0.62
            L = (0.26 + 0.16 * lat) * (0.6 + 0.4 * rr[i] / 0.4); w = 0.065 + 0.03 * lat
            root = q - d * 0.03 - t * 0.05
            pts = bez(root, root + t * L * 0.35 + d * L * 0.16, root + t * L * 0.75 + d * L * 0.22, root + t * L * 1.0 + d * L * 0.1, 4)
            lock = pipe(pts, [w * 0.8, w, w * 0.85, w * 0.45, 0.0], 6)
            for v in lock.verts:   # flattened: a lock of hair lies on the tail, it does not stand off it
                along = (v.co - root).dot(d); v.co -= d * along * 0.5
            P.part("SwayTail", lock, "Base", tb, 0)

    # ---- how he flies: a maple-seed helicopter. A wooden backpack frame on brass straps carries a mast up behind his helm; on top a brass
    # hub turns a pair of real maple samaras - the plump veined nutlets joined at the hub, the long papery wings curving out as the blades
    fx, fy = 0.16, -0.5
    for s in (1, -1):
        P.obj("FrameRail", pipe([(s * fx, fy, -0.15), (s * fx, fy, 0.72)], [0.035, 0.035], 8), "Accent")
        P.obj("Standoff", pipe([(s * fx, fy, 0.6), (s * fx * 0.9, -0.3, 0.55)], [0.025, 0.025], 6), "Metal")
        P.obj("Standoff", pipe([(s * fx, fy, 0.0), (s * fx * 0.9, -0.33, 0.02)], [0.025, 0.025], 6), "Metal")
        # the shoulder strap: from the frame's top over the pauldron and down the breastplate to the belt, a buckle on the chest
        strap = bez((s * fx, fy, 0.7), (s * 0.22, -0.2, 0.78), (s * 0.24, 0.3, 0.6), (s * 0.18, 0.4, -0.18), 10)
        P.obj("Strap", pipe(strap, [0.03] * 11, 6), "Accent")
        P.obj("StrapBuckle", oriented_ball(strap[7] + Vector((0, 0.025, 0)), (0.045, 0.055, 0.015), *sq_axes((0, 1, 0.3)), 8, 3), "Trim")
    for z in (-0.1, 0.3, 0.68):   # the cross bars
        P.obj("FrameBar", pipe([(-fx, fy, z), (fx, fy, z)], [0.03, 0.03], 6), "Accent")
    my2 = -0.62; H = Vector((0, my2, 2.05))
    P.obj("Mast", pipe([(0, my2, -0.05), (0, my2, 1.95)], [0.045, 0.04], 8), "Accent")
    for z in (0.3, 0.68, 1.1, 1.5, 1.9):   # brass bands round the mast
        P.obj("MastBand", xf(torus(0.05, 0.014, 0.0, 12, 4), None, (0, my2, z)), "Trim")
    for z in (0.3, 0.68):
        P.obj("MastClamp", pipe([(0, fy, z), (0, my2, z)], [0.03, 0.03], 6), "Metal")
    P.obj("Brace", pipe([(-fx, fy, 0.68), (0, my2, 1.15), (fx, fy, 0.68)], [0.022, 0.02, 0.022], 6), "Metal")
    # the rotor: one part, turning about the hub
    P.part("Rotor", lathe([(0.0, 1.88), (0.09, 1.9), (0.1, 1.98), (0.0, 1.99)], 14, "z", (0, my2, 0)), "Trim", tuple(H))
    P.part("Rotor", lathe([(0.11, 1.99), (0.12, 2.06), (0.07, 2.13), (0.0, 2.15)], 18, "z", (0, my2, 0)), "Trim", tuple(H))
    for s in (1, -1):
        rot = Matrix.Rotation(0 if s > 0 else math.pi, 3, "Z")
        tilt = Matrix.Rotation(math.radians(-5), 3, "Y") @ Matrix.Rotation(math.radians(9), 3, "X")   # coned up a little, pitched
        def put(p, rot=rot, tilt=tilt): return H + rot @ (tilt @ Vector(p))
        # the nutlet: a plump seed by the hub, ribbed with veins
        nb = ball((0.24, 0.0, 0.0), (0.19, 0.12, 0.09), 14, 7)
        for v in nb.verts: v.co = put(v.co)
        P.part("Rotor", nb, "Accent", tuple(H))
        for k in range(4):
            yy = -0.06 + 0.04 * k
            P.part("Rotor", pipe([put((0.1, yy * 0.6, 0.06)), put((0.24, yy, 0.075)), put((0.38, yy * 0.7, 0.05))], [0.01, 0.012, 0.008], 4), "Dark", tuple(H))
        # the wing: a thick straight leading edge, the trailing edge bowing out to the widest point two-thirds along, a rounded tip
        n = 18; X0, X1 = 0.34, 1.45
        le = []; te = []
        for i in range(n + 1):
            u = i / n; x = X0 + (X1 - X0) * u
            le.append((x, 0.06 + 0.03 * math.sin(math.pi * u) - 0.09 * u ** 4, 0.0))
            w = 0.42 * math.sin(math.pi * min(1.0, u * 0.78 + 0.05)) ** 0.8 * (1 - u ** 6)
            te.append((x, le[-1][1] - 0.08 - w, 0.0))
        bm = bmesh.new(); h = 0.012
        T = [[bm.verts.new(put((p[0], p[1], h * (1 - 0.6 * i / n)))) for p in (le[i], te[i])] for i in range(n + 1)]
        Bt = [[bm.verts.new(put((p[0], p[1], -h * (1 - 0.6 * i / n)))) for p in (le[i], te[i])] for i in range(n + 1)]
        for i in range(n):
            bm.faces.new((T[i][0], T[i + 1][0], T[i + 1][1], T[i][1])); bm.faces.new((Bt[i][1], Bt[i + 1][1], Bt[i + 1][0], Bt[i][0]))
            bm.faces.new((T[i][0], Bt[i][0], Bt[i + 1][0], T[i + 1][0])); bm.faces.new((T[i + 1][1], Bt[i + 1][1], Bt[i][1], T[i][1]))
        bm.faces.new((T[0][0], T[0][1], Bt[0][1], Bt[0][0])); bm.faces.new((T[n][1], T[n][0], Bt[n][0], Bt[n][1]))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        P.part("Rotor", bm, lambda c, nn: "Glass" if (c - H).length < 0.75 else "Trim", tuple(H), 0, False)
        # the veins: the leading edge's thick one, and fine ones fanning from the nutlet and curving out to the trailing edge
        P.part("Rotor", pipe([put((p[0], p[1] - 0.012, 0.0)) for p in le[:-1]], [0.024 - 0.014 * i / n for i in range(n)], 6), "Glass", tuple(H))
        for ue in (0.3, 0.45, 0.6, 0.75, 0.88):
            i = int(ue * n); e = te[i]; mid = le[i]
            pts = bez((X0 + 0.02, -0.02, 0.0), (X0 + (e[0] - X0) * 0.45, -0.01, 0), (mid[0] - 0.05, (mid[1] + e[1]) * 0.5, 0), (e[0], e[1] + 0.015, 0.0), 8)
            for f in (1, -1):
                P.part("Rotor", pipe([put((p.x, p.y, f * 0.012)) for p in pts], [0.008] * 9, 4), "Glass", tuple(H), 0, False)

    mzp = (0, mz.y + 0.17, mz.z - 0.13)
    P.part("Muzzle", ball(mzp, (0.05, 0.03, 0.04), 8, 4), "Glow", mzp)
    return P



# ================================================================= scarecrow2
# ================================================================= scarecrow helpers
def sc_sheet(polys, nrm, thick=0.02):
    """flat polygons made two-sided, the two faces thick apart along nrm (any direction, unlike sheet() which offsets in z)."""
    bm = bmesh.new(); n = Vector(nrm).normalized()
    for poly in polys:
        top = [bm.verts.new(Vector(p) + n * thick * 0.5) for p in poly]
        bot = [bm.verts.new(Vector(p) - n * thick * 0.5) for p in poly]
        f = bm.faces.new(top); g = bm.faces.new(list(reversed(bot)))
        f.normal_update()
        if f.normal.dot(n) < 0: bmesh.ops.reverse_faces(bm, faces=[f, g])
        for a in range(len(poly)):   # the edge band, so a thin sheet still has a rim
            b = (a + 1) % len(poly)
            bm.faces.new((top[a], top[b], bot[b], bot[a]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm

# the coat: (z, half width, half depth) from the hem up to the collar
SC_COAT = [(-0.22, 0.52, 0.38), (-0.05, 0.45, 0.33), (0.18, 0.37, 0.28), (0.4, 0.41, 0.31), (0.62, 0.47, 0.33), (0.8, 0.5, 0.32),
           (0.9, 0.36, 0.26), (0.96, 0.2, 0.17)]

def sc_coat_r(z):
    if z <= SC_COAT[0][0]: return SC_COAT[0][1], SC_COAT[0][2]
    for (z0, a0, b0), (z1, a1, b1) in zip(SC_COAT, SC_COAT[1:]):
        if z <= z1:
            t = (z - z0) / (z1 - z0); t = t * t * (3 - 2 * t)
            return a0 + (a1 - a0) * t, b0 + (b1 - b0) * t
    return SC_COAT[-1][1], SC_COAT[-1][2]

def sc_coat(seg=40, teeth=10):
    """the coat as a shell: rings from the hem to the collar, the hem cut into ragged points (each point one tooth of a regular zigzag)."""
    bm = bmesh.new(); rows = []
    zs = [SC_COAT[0][0] + (SC_COAT[-1][0] - SC_COAT[0][0]) * i / 16 for i in range(17)]
    for j, z in enumerate(zs):
        a_, b_ = sc_coat_r(z); row = []
        for i in range(seg):
            a = 2 * math.pi * i / seg
            zz = z
            if j == 0: zz = z - (0.13 if (i * teeth * 2 // seg) % 2 == 0 and i % (seg // teeth // 2 or 1) == 0 else 0.0) * (1.0 if i % 2 == 0 else 0.6)
            row.append(bm.verts.new((math.sin(a) * a_, math.cos(a) * b_, zz)))
        rows.append(row)
    for r0, r1 in zip(rows, rows[1:]):
        for i in range(seg):
            k = (i + 1) % seg
            bm.faces.new((r0[i], r0[k], r1[k], r1[i]))
    top = bm.verts.new((0, 0, SC_COAT[-1][0] + 0.02))
    for i in range(seg): bm.faces.new((rows[-1][i], rows[-1][(i + 1) % seg], top))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    # recalc may flip an open shell inward: make sure the side faces point away from the axis
    for f in bm.faces:
        c = f.calc_center_median()
        if Vector((c.x, c.y, 0)).dot(f.normal) < 0 and abs(f.normal.z) < 0.9: f.normal_flip()
    return bm

def sc_coat_surf(x, z, front=True):
    """the coat's outside at (x, z): (point, normal); front = the +y (player) side."""
    a_, b_ = sc_coat_r(z)
    u = max(-0.98, min(0.98, x / a_)); y = b_ * math.sqrt(1 - u * u) * (1 if front else -1)
    n = Vector((x / a_ ** 2, y / b_ ** 2, 0.0)).normalized()
    return Vector((x, y, z)), n

def sc_patch(P, surf, quad, slot, stitch_every=0.06):
    """a sewn-on patch: a raised piece of cloth with running stitches just inside its edge."""
    P.obj("Patch", carve_on(surf, quad, -0.02, 0.016), slot, 0, False)
    cx = sum(p[0] for p in quad) / len(quad); cz = sum(p[1] for p in quad) / len(quad)
    for a, b in zip(quad, quad[1:] + quad[:1]):
        L = math.hypot(b[0] - a[0], b[1] - a[1]); n = max(2, int(L / stitch_every))
        for k in range(n):
            t = (k + 0.5) / n
            px = a[0] + (b[0] - a[0]) * t; pz = a[1] + (b[1] - a[1]) * t
            px += (cx - px) * 0.12; pz += (cz - pz) * 0.12          # just inside the edge
            ux, uz = (b[0] - a[0]) / L, (b[1] - a[1]) / L           # along the edge
            vx, vz = -uz, ux                                         # across it: the stitch crosses the edge
            d = 0.018
            q = [(px - vx * d - ux * 0.006, pz - vz * d - uz * 0.006), (px - vx * d + ux * 0.006, pz - vz * d + uz * 0.006),
                 (px + vx * d + ux * 0.006, pz + vz * d + uz * 0.006), (px + vx * d - ux * 0.006, pz + vz * d - uz * 0.006)]
            P.obj("Stitch", carve_on(surf, q, 0.0, 0.026), "Dark", 0, False)

def sc_straw_burst(P, c, axis, n, length, spread, r=0.028, name="Straw", paint="Trim"):
    """a tuft of straw bursting out of an opening at c along axis: n stalks evenly round a cone of half-angle spread, every other one longer."""
    c = Vector(c); ax = Vector(axis).normalized()
    up = Vector((0, 0, 1)) if abs(ax.z) < 0.9 else Vector((1, 0, 0))
    u = ax.cross(up).normalized(); v = ax.cross(u).normalized()
    for k in range(n):
        a = 2 * math.pi * k / n
        d = (ax * math.cos(spread) + (u * math.cos(a) + v * math.sin(a)) * math.sin(spread)).normalized()
        L = length * (1.0 if k % 2 == 0 else 0.72)
        b = c + (u * math.cos(a) + v * math.sin(a)) * r * 1.5
        P.obj(name, pipe([b, b + d * L * 0.6 + ax * 0.02, b + d * L], [r, r * 0.7, 0.0], 4), paint, 0, False)

def sc_crow(P, c, heading, mode, k=1.0, bank=0.0, pitch=0.0, spin=None, flap=None):
    """a crow (or a raven): a teardrop body, a big head with a heavy black bill and glowing amber eyes, a wedge of tail feathers fanned out,
    and wings with the long separate 'fingers' of the primaries a crow shows in flight. mode "fly": wings spread in a glide; "perch":
    wings folded along the back, the primaries crossed over the tail, legs gripping; "carry": wings spread, legs hanging with the feet
    clenched round a rope. Built facing +y, turned to heading (degrees about up). flap: a name - each wing becomes its own mover
    "Flap<name>L" / "Flap<name>R" (the crow's own left and right) hinged at its shoulder. Returns where the feet close (for a rope)."""
    parts = []
    def add(bm, slot, side=0): parts.append((bm, slot, side))
    up = 0.25 if mode == "perch" else 0.0
    add(pipe([(0, -0.15, 0.01), (0, -0.08, 0.0), (0, 0.03, 0.0), (0, 0.11, 0.03 + up * 0.1)], [0.035, 0.08, 0.095, 0.065], 10), "Dark")
    hc = Vector((0, 0.16, 0.06 + up * 0.12))
    add(ball(tuple(hc), (0.06, 0.07, 0.062), 10, 6), "Dark")
    add(pipe([hc + Vector((0, 0.045, -0.005)), hc + Vector((0, 0.1, -0.012)), hc + Vector((0, 0.15, -0.03))], [0.028, 0.018, 0.0], 6), "Dark")   # the bill, hooked at the tip
    add(ball(tuple(hc + Vector((0, 0.035, 0.022))), (0.028, 0.05, 0.016), 6, 3), "Dark")   # nasal bristles over the bill
    for s in (1, -1):
        add(ball(tuple(hc + Vector((s * 0.045, 0.03, 0.018))), (0.014, 0.016, 0.013), 6, 3), "Glow")
    # the tail: a wedge of six feathers fanned out (closed narrow on a perched bird)
    fan = 0.16 if mode == "perch" else 0.42
    for i in range(6):
        a = -fan + 2 * fan * i / 5
        d = Vector((math.sin(a), -math.cos(a), -0.05)); w = Vector((math.cos(a), math.sin(a), 0)) * 0.03
        b = Vector((0, -0.12, 0.0)); L = 0.2 + 0.02 * (1 - abs(i - 2.5) / 2.5)
        add(sc_sheet([[tuple(b - w * 0.4), tuple(b + d * L - w), tuple(b + d * (L + 0.02)), tuple(b + d * L + w), tuple(b + w * 0.4)]], (0, 0, 1), 0.01), "Dark")
    for s in (1, -1):
        if mode != "perch":
            # the arm of the wing, then five primaries spread like fingers, the longest in the middle
            arm = [(s * 0.05, 0.07, 0.02), (s * 0.3, 0.07, 0.06), (s * 0.36, 0.02, 0.07), (s * 0.34, -0.08, 0.06), (s * 0.05, -0.09, 0.01)]
            add(sc_sheet([arm], (0, 0, 1), 0.02), "Dark", s)
            for j in range(5):
                a = math.radians(-8 + 26 * j / 4) * s
                root = Vector((s * 0.33, 0.04 - 0.11 * j / 4, 0.065))
                d = Vector((s * math.cos(a), -math.sin(a) * s * s, 0.03)).normalized()
                L = [0.22, 0.27, 0.28, 0.25, 0.2][j]
                w = Vector((-d.y, d.x, 0)) * 0.022
                add(sc_sheet([[tuple(root - w), tuple(root + d * L * 0.6 - w * 1.1), tuple(root + d * L), tuple(root + d * L * 0.6 + w * 1.1), tuple(root + w)]], (0, 0, 1), 0.01), "Dark", s)
            for j in range(4):   # coverts: a row of short rounded feathers along the arm's trailing edge
                x0 = s * (0.08 + 0.065 * j)
                add(sc_sheet([[(x0, -0.07, 0.025), (x0 + s * 0.06, -0.075, 0.03), (x0 + s * 0.04, -0.13, 0.025), (x0 + s * 0.015, -0.13, 0.022)]], (0, 0, 1), 0.01), "Dark", s)
            if mode == "carry":   # legs hanging, the feet balled round the rope
                hip = Vector((s * 0.03, 0.0, -0.06)); foot = Vector((s * 0.012, 0.0, -0.17))
                add(pipe([hip, hip + Vector((0, 0.01, -0.05)), foot], [0.014, 0.012, 0.01], 5), "Dark")
                for t in (-0.6, 0.0, 0.6):
                    add(pipe([foot, foot + Vector((-s * 0.01 + math.sin(t) * 0.02, 0.03 * math.cos(t), -0.02)), foot + Vector((-s * 0.025, 0.012, -0.04))], [0.008, 0.007, 0.0], 4), "Dark")
        else:
            add(ball((s * 0.075, -0.01, 0.03), (0.035, 0.12, 0.06), 8, 4), "Dark")
            add(sc_sheet([[(s * 0.07, -0.08, 0.04), (s * 0.02, -0.26, 0.03), (-s * 0.01, -0.27, 0.035), (s * 0.05, -0.08, 0.05)]], (0, 0, 1), 0.01), "Dark")
            # legs and feet gripping whatever it stands on
            hip = Vector((s * 0.035, 0.02, -0.06)); foot = Vector((s * 0.04, 0.03, -0.14))
            add(pipe([hip, foot], [0.012, 0.01], 5), "Dark")
            for t in (-0.4, 0.0, 0.4):
                add(pipe([foot, foot + Vector((math.sin(t) * 0.05, math.cos(t) * 0.05, -0.005)), foot + Vector((math.sin(t) * 0.07, math.cos(t) * 0.06, -0.03))], [0.008, 0.006, 0.0], 4), "Dark")
            add(pipe([foot, foot + Vector((0, -0.05, -0.02))], [0.008, 0.0], 4), "Dark")
    M = (Matrix.Translation(c) @ Matrix.Rotation(math.radians(heading), 4, "Z") @ Matrix.Rotation(math.radians(bank), 4, "Y")
         @ Matrix.Rotation(math.radians(pitch), 4, "X") @ Matrix.Scale(k, 4))
    for bm, slot, side in parts:
        bm.transform(M)
        if flap is not None and side:
            P.part("Flap%s%s" % (flap, "L" if side < 0 else "R"), bm, slot, tuple(M @ Vector((side * 0.05, 0.0, 0.02))), 0, False)
        elif spin is not None: P.part(spin[0], bm, slot, spin[1], 0, False)
        else: P.obj("Crow", bm, slot, 0, False)
    return M @ Vector((0, 0.0, -0.2))

def sc_timber(P, name, a, b, r, seg=6, knots=()):
    """a rough-hewn pole from a to b: six-sided, swelling and thinning a little along its length, grain lines in dark and a few knots."""
    a, b = Vector(a), Vector(b); L = (b - a).length; ax = (b - a) / L
    n = 12; pts = [a + (b - a) * (i / n) for i in range(n + 1)]
    radii = [r * (1 + 0.07 * math.sin(i * 1.7) + 0.04 * math.cos(i * 3.1)) for i in range(n + 1)]
    up = Vector((0, 0, 1)) if abs(ax.z) < 0.9 else Vector((1, 0, 0))
    u = ax.cross(up).normalized(); v = ax.cross(u).normalized()
    def grain(c, nr):
        d = c - a; t = d.dot(ax); q = d - ax * t
        ang = math.atan2(q.dot(v), q.dot(u)) / (2 * math.pi)
        return "Dark" if (ang * 4 + 0.18 * math.sin(t * 5.0)) % 1.0 < 0.08 else "Base"
    P.obj(name, pipe(pts, radii, seg), grain, 0, False)
    for t, ang in knots:
        c = a + ax * L * t; d = u * math.cos(ang) + v * math.sin(ang)
        P.obj(name + "Knot", ball(tuple(c + d * r * 0.95), (r * 0.35, r * 0.35, r * 0.35), 6, 3), "Dark")

def sc_wrap(P, c, axis, R, turns=3, gap=0.035, r=0.016, name="Lashing", slot="Trim"):
    """rope wound round a pole: turns rings side by side along axis, each a little twisted torus."""
    c = Vector(c); ax = Vector(axis).normalized()
    rot = ax.to_track_quat("Z", "Y").to_matrix().to_4x4()
    for k in range(turns):
        t = torus(R, r, 0.0, 16, 5)
        t.transform(Matrix.Translation(c + ax * gap * (k - (turns - 1) / 2)) @ rot @ Matrix.Rotation(math.radians(8), 4, "X"))
        P.obj(name, t, slot, 0, False)


# ================================================================= the harvest scarecrow
def A_scarecrow2():
    """The harvest scarecrow (2026-10-13, remade: "same as the alien bosses - realistic details, scarier, keep the cartoon shape"): the
    same jack-o'-lantern scarecrow on his pole with his crows, now built like a real one. The head is a real carved pumpkin - deep ribs
    darkened in their grooves, a thick six-sided stalk curling over with a tendril, the zigzag line where the lid was cut glowing as the
    candle's light leaks through it; carved into it a menacing face: angry slanted eyes under carved brows with a burning slit pupil in
    each, a carved nose and a wide grin up to the cheeks with interlocking jagged teeth, every cut edged sharp and dark round a fire
    inside. A battered wide-brim straw hat is tipped back, its woven brim warped and torn at the back with straw sticking out of the
    tears, a red band with a crow's feather tucked in it, the crown dented in. His body is a burlap coat stuffed with straw: wide at the
    shoulders, tied in at the waist with a rope belt knotted at the front, buttoned, the hem cut ragged; patches in red, olive and brown
    sewn on with running stitches (chest, belly, elbow, knee); straw bursts evenly from the collar under a twine tie, from the cuffs and
    the hem; olive trousers hang below with straw at the ankles, ragged coat tails stream behind. His arms are tied along a rough-hewn
    crossbar - six-sided timber with grain and knots, lashed with rope at the wrists - and the pole runs down below him, bound with rope
    under the coat; in his right hand hangs a rusted sickle with a honed edge. He flies the way a scarecrow
    would: he is carried by his crows. Five big carrier crows fly over him in a fixed V - real crows with heavy hooked bills, glowing
    amber eyes, fanned wedge tails and the long fingered primaries a crow spreads in flight - each with its feet balled round a rope that
    runs down taut to him: the lead crow's to a knot on his hat, two to ties round his arms, two to the ends of the crossbar, so he hangs
    under them like a marionette, the pole dangling below and his coat tails blown back. Each crow's wings beat on their own (FlapC0L/R ..
    FlapC4L/R, hinged at the shoulders). His shots leave from his grin."""
    P = Boss("scarecrow2", pal(Base=((0.36, 0.23, 0.12), 0.35), Belly=((0.52, 0.38, 0.21), 0.25), Accent=((0.88, 0.38, 0.07), 0.45),
                               Trim=((0.86, 0.66, 0.24), 0.3), Glass=((0.58, 0.13, 0.07), 0.3), Dark=((0.05, 0.04, 0.04), 0.45),
                               Glow=((1.0, 0.42, 0.04), 0.5), Metal=((0.30, 0.33, 0.13), 0.3), Lamp=((1.0, 0.92, 0.45), 0.9)))
    hc = Vector((0, 0.0, 1.32)); R = 0.62; H = 0.95
    # ---- the pumpkin head: ribbed, the grooves between the ribs darker
    def rind(c, n):
        a = math.atan2(c.y - hc.y, c.x - hc.x)
        return "Base" if math.cos(12 * a) < -0.82 and abs(c.z - hc.z) < 0.36 else "Accent"
    P.obj("Head", pumpkin(tuple(hc), R, H, 12, 48, 16), rind, 1)
    surf = ellipsoid_surf(hc, R * 0.97, R * 0.97, H * 0.5)
    def feature(name, quad, grow_k=1.12):
        """a carved hole: the pale rind round its edge, the fire showing in it."""
        cx = sum(p[0] for p in quad) / len(quad); cz = sum(p[1] for p in quad) / len(quad)
        rim = [(cx + (x - cx) * grow_k, cz + (z - cz) * grow_k) for x, z in quad]
        P.obj("Cut", carve_on(surf, rim, -0.05, 0.012), "Dark", 0, False)
        P.obj(name, carve_on(surf, quad, -0.05, 0.022), "Glow", 0, False)
    for s in (1, -1):
        # angry eyes: the top edge slopes down to the nose, a notch cut in the bottom
        feature("Eye", [(s * 0.07, hc.z + 0.07), (s * 0.38, hc.z + 0.25), (s * 0.33, hc.z + 0.02), (s * 0.2, hc.z - 0.04)])
        q, n = surf(s * 0.23, hc.z + 0.07)
        P.obj("Pupil", ball(tuple(q + n * 0.03), (0.03, 0.03, 0.07), 8, 4), "Lamp")
        brow = [(s * 0.03, hc.z + 0.16), (s * 0.42, hc.z + 0.38), (s * 0.43, hc.z + 0.32), (s * 0.06, hc.z + 0.11)]
        P.obj("Brow", carve_on(surf, brow, -0.03, 0.04), "Dark", 0, False)
    feature("Nose", [(-0.07, hc.z - 0.04), (0.07, hc.z - 0.04), (0.0, hc.z - 0.15)])
    # the grin: wide, its corners pulled up to the cheeks
    def top(t):
        x = -0.5 + 1.0 * t; return (x, hc.z - 0.22 + 0.62 * x * x)
    def bot(t):
        x = -0.43 + 0.86 * t; return (x, hc.z - 0.44 + 0.5 * x * x)
    def top_r(t):
        x = -0.54 + 1.08 * t; return (x, hc.z - 0.19 + 0.62 * x * x)
    def bot_r(t):
        x = -0.47 + 0.94 * t; return (x, hc.z - 0.48 + 0.5 * x * x)
    strip(surf, top_r, bot_r, 12, "Cut", P, "Dark", -0.05, 0.012)
    strip(surf, top, bot, 12, "Grin", P, "Glow", -0.05, 0.022)
    for i, x in enumerate((-0.33, -0.2, -0.07, 0.07, 0.2, 0.33)):   # upper fangs, the two in the middle longest
        zt = hc.z - 0.22 + 0.62 * x * x; L = 0.13 if abs(x) < 0.1 else (0.1 if abs(x) < 0.25 else 0.08)
        P.obj("Tooth", carve_on(surf, [(x - 0.05, zt + 0.01), (x + 0.05, zt + 0.01), (x + 0.008, zt - L), (x - 0.008, zt - L)], -0.05, 0.03), "Accent", 0, False)
    for x in (-0.27, -0.135, 0.0, 0.135, 0.27):   # lower teeth, set between the upper ones
        zb = hc.z - 0.44 + 0.5 * x * x
        P.obj("Tooth", carve_on(surf, [(x - 0.045, zb - 0.01), (x + 0.045, zb - 0.01), (x + 0.006, zb + 0.09), (x - 0.006, zb + 0.09)], -0.05, 0.03), "Accent", 0, False)
    # the lid line: a zigzag cut round the top, the candle's light leaking out of it
    rz = H * 0.5 * 0.9; n = 28
    def lid_pt(i):
        a = 2 * math.pi * i / n; dz = 0.365 + (0.03 if i % 2 == 0 else -0.035)
        r = R * math.sqrt(max(0.0, 1 - (dz / rz) ** 2)) * 0.985
        p = hc + Vector((math.cos(a) * r, math.sin(a) * r, dz))
        nn = Vector((math.cos(a) * r / R ** 2, math.sin(a) * r / R ** 2, dz / rz ** 2)).normalized()
        return p, nn
    for i in range(n):
        (p0, n0), (p1, n1) = lid_pt(i), lid_pt(i + 1)
        w = (n0 + n1).normalized()
        side = (p1 - p0).cross(w).normalized() * 0.012
        P.obj("Lid", hull([tuple(p0 - side - w * 0.03), tuple(p0 + side - w * 0.03), tuple(p1 - side - w * 0.03), tuple(p1 + side - w * 0.03),
                           tuple(p0 - side + w * 0.018), tuple(p0 + side + w * 0.018), tuple(p1 - side + w * 0.018), tuple(p1 + side + w * 0.018)]), "Glow", 0, False)
    # the stalk: thick, six-sided like a real one, curling over, a dry tendril twisting off it
    st = bez((0, -0.04, hc.z + 0.36), (0.0, -0.06, hc.z + 0.62), (0.12, -0.12, hc.z + 0.74), (0.26, -0.08, hc.z + 0.66), 7)
    P.obj("Stalk", pipe(st, [0.1, 0.09, 0.08, 0.075, 0.068, 0.06, 0.055, 0.05], 6), "Metal")
    tend = [Vector((0.06 + 0.05 * math.cos(t * 1.4), -0.06 + 0.05 * math.sin(t * 1.4), hc.z + 0.5 - t * 0.015)) + Vector((t * 0.025, 0, 0)) for t in range(10)]
    P.obj("Tendril", pipe(tend, [0.014] * 9 + [0.0], 5), "Metal")
    # ---- the hat: tipped back so the face reads; a warped woven brim, torn at the back, a dented crown, a red band with a crow feather
    pivot = Vector((0, 0, hc.z + 0.42))
    T = Matrix.Translation((0, -0.2, hc.z + 0.5)) @ Matrix.Rotation(math.radians(-26), 4, "X") @ Matrix.Rotation(math.radians(9), 4, "Y")
    Ti = T.inverted()
    def hat(bm):
        bm.transform(T @ Matrix.Translation(-pivot)); return bm
    def weave(c, n):
        l = Ti @ c; r = math.hypot(l.x, l.y)
        return "Belly" if (r * 22) % 1.0 < 0.3 else "Trim"
    seg = 40; rin, rout = 0.34, 0.8
    bm = bmesh.new(); tops, bots = [], []
    for j in range(5):
        r = rin + (rout - rin) * j / 4; tr, br = [], []
        for i in range(seg):
            a = 2 * math.pi * i / seg
            rr = r
            if j > 0 and abs(math.sin((a + math.pi / 2) / 2)) < 0.14: rr = rin + (r - rin) * 0.72   # the tear at the back
            w = 0.07 * math.sin(3 * a + 0.6) * (rr - rin) / (rout - rin) + 0.04 * ((rr - rin) / (rout - rin)) ** 2 * math.sin(a)
            z = pivot.z - 0.02 * (rr - rin) / (rout - rin) + w
            tr.append(bm.verts.new((math.cos(a) * rr, math.sin(a) * rr, z + 0.014)))
            br.append(bm.verts.new((math.cos(a) * rr, math.sin(a) * rr, z - 0.014)))
        tops.append(tr); bots.append(br)
    for j in range(4):
        for i in range(seg):
            k = (i + 1) % seg
            bm.faces.new((tops[j][i], tops[j][k], tops[j + 1][k], tops[j + 1][i]))
            bm.faces.new((bots[j][i], bots[j + 1][i], bots[j + 1][k], bots[j][k]))
    for i in range(seg):
        k = (i + 1) % seg
        bm.faces.new((tops[4][i], tops[4][k], bots[4][k], bots[4][i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    P.obj("Brim", hat(bm), weave)
    crown = lathe([(rin + 0.01, pivot.z - 0.01), (rin - 0.03, pivot.z + 0.2), (rin - 0.07, pivot.z + 0.3), (0.2, pivot.z + 0.36), (0.0, pivot.z + 0.33)], 24, "z")
    for v in crown.verts:   # the crease pressed into the top, front to back
        if v.co.z > pivot.z + 0.25: v.co.z -= 0.09 * math.exp(-(v.co.x / 0.12) ** 2)
    P.obj("Crown", hat(crown), weave)
    P.obj("Band", hat(lathe([(rin - 0.005, pivot.z + 0.0), (rin - 0.025, pivot.z + 0.1), (0.0, pivot.z + 0.1)], 24, "z")), "Glass")
    feather = [(0.25, 0.18, pivot.z + 0.06), (0.36, 0.1, pivot.z + 0.42), (0.33, 0.02, pivot.z + 0.48), (0.2, 0.12, pivot.z + 0.08)]
    P.obj("Feather", hat(sc_sheet([feather], (0.6, -0.8, 0), 0.012)), "Dark", 0, False)
    for k in range(5):   # straw sticking out of the tear and the worn edge
        a = -math.pi / 2 + (k - 2) * 0.09
        b = Vector((math.cos(a) * rin * 1.6, math.sin(a) * rin * 1.6, pivot.z))
        P.obj("StrawHat", hat(cone(b, b + Vector((math.cos(a) * 0.32, math.sin(a) * 0.32, 0.02 * (k - 2))), 0.02, 4)), "Trim", 0, False)
    for k in range(8):
        a = 2 * math.pi * k / 8 + 0.2
        if abs(math.sin((a + math.pi / 2) / 2)) < 0.3: continue
        b = Vector((math.cos(a) * rout * 0.95, math.sin(a) * rout * 0.95, pivot.z))
        P.obj("StrawHat", hat(cone(b, b + Vector((math.cos(a) * 0.12, math.sin(a) * 0.12, -0.02)), 0.015, 4)), "Trim", 0, False)
    # ---- the frame: a rough pole and crossbar
    sc_timber(P, "Pole", (0, -0.1, -1.45), (0, -0.1, 1.0), 0.075, knots=((0.08, 1.0), (0.2, 3.5)))
    sc_timber(P, "Bar", (-1.52, -0.12, 0.76), (1.52, -0.12, 0.76), 0.065, knots=((0.03, 1.6), (0.97, 4.2)))
    sc_wrap(P, (0, -0.1, -0.5), (0, 0, 1), 0.095, 4)
    # ---- the coat
    P.obj("Coat", sc_coat(), "Belly", 0, True)
    P.obj("Stuffing", ball((0, 0, -0.15), (0.44, 0.31, 0.06), 16, 4), "Trim")
    for s in (1, -1):
        sc_straw_burst(P, (s * 0.18, 0.0, -0.32), (s * 0.4, 0.15, -1), 7, 0.32, 0.45)
        sc_straw_burst(P, (s * 0.38, -0.05, -0.28), (s * 0.6, 0, -1), 5, 0.26, 0.4)
    sc_straw_burst(P, (0, 0.25, -0.3), (0, 0.4, -1), 5, 0.3, 0.4)
    sc_straw_burst(P, (0, -0.3, -0.3), (0, -0.4, -1), 5, 0.3, 0.4)
    for k in range(3):   # buttons down the front
        q, n = sc_coat_surf(0.0, 0.62 - 0.17 * k)
        P.obj("Button", ball(tuple(q + n * 0.02), (0.045, 0.045, 0.045), 8, 4), "Dark")
    # the patches, sewn on
    sc_patch(P, sc_coat_surf, [(0.12, 0.72), (0.34, 0.75), (0.36, 0.52), (0.14, 0.5)], "Glass")
    sc_patch(P, sc_coat_surf, [(-0.32, 0.4), (-0.12, 0.42), (-0.1, 0.25), (-0.3, 0.22)], "Metal")
    sc_patch(P, sc_coat_surf, [(0.1, 0.05), (0.32, 0.08), (0.34, -0.12), (0.12, -0.14)], "Base")
    # rope belt, knotted at the front with the ends hanging
    a_, b_ = sc_coat_r(0.2)
    belt = torus(a_ + 0.01, 0.03, 0.0, 32, 6)
    belt.transform(Matrix.Translation((0, 0, 0.2)) @ Matrix.Scale((b_ + 0.01) / (a_ + 0.01), 4, Vector((0, 1, 0))))
    P.obj("Belt", belt, "Trim")
    P.obj("Knot", ball((0.06, b_ + 0.02, 0.2), (0.06, 0.04, 0.05), 8, 4), "Trim")
    for s in (1, -1):
        P.obj("BeltEnd", pipe([(0.06, b_ + 0.03, 0.18), (0.06 + s * 0.05, b_ + 0.05, 0.02), (0.06 + s * 0.07, b_ + 0.04, -0.12)], [0.025, 0.022, 0.0], 5), "Trim")
    # collar: straw bursting out under a twine tie round the neck
    P.obj("NeckTie", torus(0.2, 0.025, 0.95, 20, 5), "Base")
    for k in range(16):
        a = 2 * math.pi * k / 16
        b = Vector((math.sin(a) * 0.22, math.cos(a) * 0.18, 0.93))
        d = Vector((math.sin(a), math.cos(a), -0.35 if k % 2 else 0.1)).normalized()
        L = 0.24 if k % 2 == 0 else 0.17
        P.obj("Collar", pipe([b, b + d * L * 0.6, b + d * L], [0.03, 0.02, 0.0], 4), "Trim", 0, False)
    # ---- the arms tied along the bar
    for s in (1, -1):
        sl = [(s * 0.42, -0.02, 0.8), (s * 0.62, -0.06, 0.77), (s * 0.82, -0.08, 0.76), (s * 1.0, -0.1, 0.76), (s * 1.12, -0.11, 0.76)]
        P.obj("Sleeve", pipe(sl, [0.2, 0.165, 0.175, 0.155, 0.16], 12), "Belly", 0, True)
        P.obj("Cuff", pipe([(s * 1.08, -0.11, 0.76), (s * 1.16, -0.11, 0.76)], [0.172, 0.172], 12), "Glass")
        sc_wrap(P, (s * 1.3, -0.12, 0.76), (1, 0, 0), 0.08, 3)
        sc_straw_burst(P, (s * 1.16, -0.11, 0.76), (s, 0, 0), 9, 0.3, 0.42, 0.03)
        sc_straw_burst(P, (s * 1.16, -0.11, 0.76), (s, 0, -0.15), 5, 0.22, 0.15, 0.02)
        # coat tails, ragged, hanging behind (they flap with the cloth)
        tail = [(s * 0.08, -0.36, 0.25), (s * 0.42, -0.3, 0.25), (s * 0.46, -0.62, -0.4), (s * 0.38, -0.58, -0.28), (s * 0.3, -0.68, -0.5),
                (s * 0.2, -0.6, -0.32), (s * 0.12, -0.66, -0.45)]
        P.part("Cloth", sc_sheet([tail[:3] + [tail[3]], [tail[0], tail[3], tail[4], tail[5]], [tail[0], tail[5], tail[6]]], (0, 1, 0), 0.02), "Belly", (0, 0, 0), 0, False)
        # trousers hanging below the coat, straw at the ankles
        leg = [(s * 0.2, 0.0, -0.05), (s * 0.22, 0.02, -0.4), (s * 0.24, 0.04, -0.72)]
        P.obj("Leg", pipe(leg, [0.15, 0.13, 0.12], 10), "Metal", 0, True)
        P.obj("Ankle", torus(0.115, 0.02, -0.64, 14, 4), "Base"); P.parts[-1].data.transform(Matrix.Translation((s * 0.24, 0.04, 0)))
        sc_straw_burst(P, (s * 0.24, 0.04, -0.72), (s * 0.15, 0.1, -1), 7, 0.24, 0.35, 0.025)
    def knee(x, z):
        return Vector((x, 0.15, z)), Vector((0, 1, 0.1)).normalized()
    sc_patch(P, knee, [(0.13, -0.33), (0.28, -0.33), (0.28, -0.47), (0.13, -0.47)], "Glass", 0.05)
    P.obj("Patch", box((-0.82, -0.08, 0.93), (0.2, 0.2, 0.025)), "Base", 0, False)
    for k in range(7):
        P.obj("Stitch", box((-0.92 + 0.033 * k, -0.08 + 0.09, 0.945), (0.012, 0.04, 0.012)), "Dark", 0, False)
        P.obj("Stitch", box((-0.92 + 0.033 * k, -0.08 - 0.09, 0.945), (0.012, 0.04, 0.012)), "Dark", 0, False)
    # ---- the sickle hanging from his right hand: a worn handle, a rusted crescent blade, its inner edge honed bright
    P.obj("Handle", pipe([(1.24, -0.06, 0.74), (1.25, 0.0, 0.5), (1.26, 0.05, 0.3)], [0.035, 0.038, 0.034], 8), "Base")
    P.obj("Ferrule", pipe([(1.26, 0.04, 0.33), (1.26, 0.055, 0.27)], [0.045, 0.045], 8), "Dark")
    outer = bez((0.05, 0.28), (0.45, 0.12), (0.8, 0.38), (0.6, 0.72), 12)
    blade_pts = []
    for i, p in enumerate(outer):
        t = i / (len(outer) - 1)
        d = (outer[min(i + 1, len(outer) - 1)] - outer[max(i - 1, 0)]).normalized()
        nrm = Vector((-d.y, d.x))   # inward (the curve bends left)
        blade_pts.append((p, p + nrm * 0.1 * (1 - t) ** 0.8))
    for (o0, i0), (o1, i1) in zip(blade_pts, blade_pts[1:]):
        pts = []
        for p in (o0, i0, o1, i1):
            for dx in (-0.012, 0.012): pts.append((1.26 + dx, p.x, p.y))
        P.obj("Blade", hull(pts), "Dark", 0, False)
        e = []
        for p, q in ((i0, o0), (i1, o1)):
            m = p + (q - p) * 0.25
            for dx in (-0.014, 0.014): e += [(1.26 + dx, p.x, p.y), (1.26 + dx, m.x, m.y)]
        P.obj("Edge", hull(e), "Belly", 0, False)
    # ---- he hangs from the flock: everything so far scaled down a little, then five carrier crows over him, a taut rope from each
    S = 0.76; crown_top = (T @ Vector((0, 0, 0.27))) * S
    for ob in P.parts: ob.data.transform(Matrix.Scale(S, 4))
    for ob in P.spin: ob.data.transform(Matrix.Scale(S, 4)); ob.location = ob.location * S
    for x in (-0.72, 0.72):   # rope tied round each arm
        for w in range(2):
            t = torus(0.172 * S, 0.014, 0.0, 16, 5)
            t.transform(Matrix.Translation((x * S + (w - 0.5) * 0.03, -0.075 * S, 0.765 * S)) @ Matrix.Rotation(math.radians(90), 4, "Y"))
            P.obj("ArmTie", t, "Trim", 0, False)
    P.obj("HatKnot", ball(tuple(crown_top), (0.05, 0.05, 0.04), 8, 4), "Trim")
    flock = [  # (name, crow position, the point on him its rope runs to)
        ("C0", (0.0, 0.12, 2.62), crown_top),
        ("C1", (0.74, -0.04, 2.32), Vector((0.72, -0.075, 0.94)) * S),
        ("C2", (-0.74, -0.04, 2.32), Vector((-0.72, -0.075, 0.94)) * S),
        ("C3", (1.36, -0.22, 2.04), Vector((1.36, -0.12, 0.82)) * S),
        ("C4", (-1.36, -0.22, 2.04), Vector((-1.36, -0.12, 0.82)) * S)]
    for name, c, to in flock:
        feet = sc_crow(P, c, 0, "carry", 1.08, pitch=12, flap=name)
        d = (Vector(to) - feet).normalized()
        P.obj("Rope", pipe([feet + d * 0.02, Vector(to)], [0.016, 0.016], 5), "Trim", 0, False)
    q, n = surf(0.0, hc.z - 0.33); q = q * S
    P.part("Muzzle", ball(tuple(q + n * 0.03), (0.06, 0.025, 0.04), 8, 4), "Glow", tuple(q + n * 0.03))
    return P



# ================================================================= oakking
# ================================================================= the oak king's shapes
OK_FURROWS = 12          # bark ridges round the trunk
OK_ROOTS = 6             # buttress roots round the base, none straight in front of the face

def ok_base(z):
    """the trunk's radius at height z: a root flare at the foot, a slight waist, a shoulder where the limbs leave."""
    keys = [(-1.44, 0.6), (-1.38, 0.98), (-1.24, 1.06), (-1.1, 1.02), (-0.8, 0.96), (-0.3, 0.91), (0.3, 0.9), (0.85, 0.92), (1.15, 0.88), (1.32, 0.78), (1.42, 0.5), (1.46, 0.0)]
    if z <= keys[0][0]: return keys[0][1]
    for (z0, r0), (z1, r1) in zip(keys, keys[1:]):
        if z <= z1:
            t = (z - z0) / (z1 - z0); t = t * t * (3 - 2 * t)
            return r0 + (r1 - r0) * t
    return 0.0

def ok_face_w(a, z):
    """1 on the smooth face (front, between chin and brow), 0 on the furrowed bark."""
    fa = math.exp(-(a / 0.62) ** 4)
    fz = 1.0 if -0.62 < z < 0.98 else math.exp(-((z - (0.98 if z > 0 else -0.62)) / 0.12) ** 2)
    return fa * fz

def ok_ridge(a, z):
    """the bark: OK_FURROWS long vertical ridges that wander a little as they climb (a slow twist and a sway), broken into plates
    every so often like real oak bark. -1 deep in a furrow, +1 on a ridge top."""
    ph = OK_FURROWS * a + 0.9 * math.sin(1.7 * z + 2 * a) + 0.35 * z
    s = math.sin(ph)
    plate = 0.5 + 0.5 * math.cos(math.pi * (z * 2.6 + 0.5 * math.floor(ph / (2 * math.pi) + 0.5)))   # plate breaks, staggered ridge to ridge
    return s if s < 0 else s * (0.55 + 0.45 * plate ** 0.3)

def ok_flare(a, z):
    """the buttresses: OK_ROOTS lobes at the foot, swelling into the roots."""
    k = max(0.0, min(1.0, (-0.55 - z) / 0.7)) ** 1.6
    lobe = max(0.0, math.cos(OK_ROOTS * (a - math.pi / OK_ROOTS))) ** 3
    return 1 + 0.26 * k * lobe

def ok_R(a, z):
    w = ok_face_w(a, z)
    top = max(0.0, min(1.0, (1.45 - z) / 0.2))
    s = ok_ridge(a, z); prof = 1.0 if s > -0.2 else max(-1.0, 1.0 + (s + 0.2) * 3.2)   # flat-topped ridges, each furrow a deep narrow V
    return ok_base(z) * ok_flare(a, z) + 0.06 * prof * (1 - 0.92 * w) * top

def ok_pt(a, z):
    r = ok_R(a, z)
    return Vector((math.sin(a) * r, math.cos(a) * r, z))

def ok_surf(x, z):
    """the face on the front of the trunk: (x, z) -> (point, outward normal)."""
    a = math.asin(max(-0.99, min(0.99, x / ok_base(z))))
    for _ in range(3):
        a = math.asin(max(-0.99, min(0.99, x / ok_R(a, z))))
    p = ok_pt(a, z); e = 0.004
    ta = ok_pt(a + e, z) - ok_pt(a - e, z); tz = ok_pt(a, z + e) - ok_pt(a, z - e)
    n = ta.cross(tz).normalized()
    if n.dot(Vector((p.x, p.y, 0))) < 0: n = -n
    return p, n

def ok_trunk(seg=60, rings=30, z0=-1.44, z1=1.46):
    bm = bmesh.new(); grid = []
    for j in range(rings + 1):
        z = z0 + (z1 - z0) * j / rings
        if j == rings: grid.append([bm.verts.new((0, 0, z1))]); continue
        grid.append([bm.verts.new(ok_pt(2 * math.pi * i / seg - math.pi, z)) for i in range(seg)])
    bot = bm.verts.new((0, 0, z0))
    for i in range(seg): bm.faces.new((bot, grid[0][(i + 1) % seg], grid[0][i]))
    for j in range(rings - 1):
        for i in range(seg):
            i2 = (i + 1) % seg
            bm.faces.new((grid[j][i], grid[j][i2], grid[j + 1][i2], grid[j + 1][i]))
    for i in range(seg): bm.faces.new((grid[rings - 1][i], grid[rings - 1][(i + 1) % seg], grid[rings][0]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm

def ok_orient(bm, n, c, spin=0.0):
    """a shape built about the origin facing +y turned to face n (turned spin radians about it first), moved to c."""
    q = Vector((0, 1, 0)).rotation_difference(Vector(n).normalized()).to_matrix() @ Matrix.Rotation(spin, 3, "Y")
    for v in bm.verts: v.co = q @ v.co + Vector(c)
    return bm

def ok_oball(c, r, n, spin=0.0, seg=12, rings=6):
    return ok_orient(ball((0, 0, 0), r, seg, rings), n, c, spin)

def ok_ring(R, r, n, c, sx=1.0, spin=0.0, seg=20, sides=6):
    """a torus round the y axis (an eye's rim), squashed sx across, turned to face n."""
    bm = torus(R, r, 0.0, seg, sides)
    for v in bm.verts: v.co = Vector((v.co.x * sx, v.co.z, v.co.y))
    return ok_orient(bm, n, c, spin)

def ok_leaf(c, size, v, n, curl=0.18, thick=0.012):
    """an oak leaf: three rounded lobes a side cut by deep sinuses, a rounded tip lobe, a short stalk end; v runs from the stalk to the
    tip, n is the leaf's face; it cups a little along the midrib. Two-sided."""
    c = Vector(c); v = Vector(v).normalized(); n = Vector(n); n = (n - v * n.dot(v)).normalized(); u = v.cross(n)
    L = size * 2.0; steps = 7
    env = lambda t: math.sin(math.pi * min(1.0, t * 1.08) ** 0.75)
    W = [0.0] + [size * 0.62 * env(i / steps) * (1.0 if i % 2 else 0.42) for i in range(1, steps)] + [0.0]
    W[steps - 1] = max(W[steps - 1], size * 0.22)
    mids, eL, eR = [], [], []
    for i in range(steps + 1):
        t = i / steps
        m = c + v * (t - 0.4) * L - n * curl * size * math.sin(math.pi * t) * 0.6
        mids.append(m)
        lift = n * curl * size * (W[i] / size) * 0.9
        eL.append(m - u * W[i] + lift); eR.append(m + u * W[i] + lift)
    bm = bmesh.new()
    def quad(pts):
        top = [bm.verts.new(p + n * thick * 0.5) for p in pts]; bot = [bm.verts.new(p - n * thick * 0.5) for p in pts]
        f = bm.faces.new(top); g = bm.faces.new(list(reversed(bot)))
        f.normal_update()
        if f.normal.dot(n) < 0: bmesh.ops.reverse_faces(bm, faces=[f, g])
    for i in range(steps):
        quad([mids[i], mids[i + 1], eR[i + 1], eR[i]])
        quad([mids[i], eL[i], eL[i + 1], mids[i + 1]])
    return bm

def ok_acorn(c, s, d=(0, 0, -1), nut="Metal"):
    """an acorn hanging along d from its stalk at c: a short stalk, a cup of overlapping scales (rows of little knobs, staggered row to
    row) and a smooth pointed nut with a nipple at the tip. Returns [(bm, slot)]."""
    c = Vector(c); d = Vector(d).normalized()
    q = Vector((0, 0, -1)).rotation_difference(d).to_matrix()
    put = lambda bm: [setattr(v, "co", q @ v.co + c) for v in bm.verts] and bm or bm
    out = [(put(pipe([(0, 0, 0), (0, 0, -0.12 * s)], [0.035 * s, 0.03 * s], 5)), "Base")]
    prof = [(0.0, -0.12), (0.2, -0.13), (0.3, -0.17), (0.36, -0.23), (0.41, -0.29), (0.44, -0.35), (0.45, -0.41), (0.40, -0.47), (0.0, -0.44)]
    cup = lathe(prof, 10, "z")
    for v in cup.verts:   # the scales: every other vertex pushed out, staggered row to row, so the cup reads as overlapping scales
        r = math.hypot(v.co.x, v.co.y)
        if r > 0.25:
            row = min(range(len(prof)), key=lambda i: abs(prof[i][1] - v.co.z)); k = round(math.atan2(v.co.y, v.co.x) / (2 * math.pi) * 10)
            if (row + k) % 2: v.co.x *= 1.12; v.co.y *= 1.12; v.co.z -= 0.02
        v.co *= s
    out.append((put(cup), lambda c, n: "Dark" if n.z < -0.6 else "Base"))
    nutp = lathe([(0.0, -0.4), (0.36, -0.42), (0.38, -0.6), (0.33, -0.8), (0.2, -0.98), (0.06, -1.06), (0.0, -1.1)], 10, "z")
    for v in nutp.verts: v.co *= s
    out.append((put(nutp), nut))
    return out

def ok_bracket(c, out_dir, R, P):
    """a turkey-tail bracket fungus: a half disc standing out of the bark, domed on top, in bands of orange, red and cream to the rim."""
    c = Vector(c); u = Vector((out_dir[0], out_dir[1], 0)).normalized(); t = Vector((-u.y, u.x, 0))
    pts = []
    for i in range(6):
        rho = i / 5
        for k in range(10):
            ph = math.pi * (k / 9 - 0.5)
            p = c + (u * math.cos(ph) * 0.8 + t * math.sin(ph)) * rho * R
            pts += [tuple(p + Vector((0, 0, 0.22 * R * (1 - rho * rho) + 0.02))), tuple(p - Vector((0, 0, 0.06 * R * (1 - rho) + 0.01)))]
    pts.append(tuple(c - u * 0.1 * R))
    def paint(q, n):
        if n.z < -0.3: return "Trim"   # the cream pores underneath
        rho = (q - c).length / R
        return "Trim" if rho > 0.86 else ("Accent" if rho > 0.62 else ("Glass" if rho > 0.42 else "Accent"))
    P.obj("Fungus", hull(pts), paint, 0, False)

def ok_limb(P, p, d, L, r, depth, roll, tips, forks, name="Limb"):
    """an oak limb: crooked (it bends one way then the other, as limbs that grew toward the light do), a knot at each fork, then two
    smaller limbs forking out in a plane turned a quarter round from the last fork's (so the crown fills out on every side)."""
    d = d.normalized()
    side = d.cross(Vector((0, 0, 1)) if abs(d.z) < 0.95 else Vector((1, 0, 0))).normalized()
    side = Matrix.Rotation(roll, 3, d) @ side
    end = p + d * L
    pts = [p, p + d * L * 0.35 + side * L * 0.08, p + d * L * 0.7 - side * L * 0.06, end]
    P.obj(name, pipe(pts, [r, r * 0.88, r * 0.78, r * 0.7], 8), "Base")
    if depth == 0:
        tips.append((end, d)); return
    P.obj(name + "Knot", ball(tuple(end), (r * 0.82, r * 0.82, r * 0.82), 6, 3), "Base")
    forks.append((end, d, r))
    for sgn in (1, -1):
        nd = (Matrix.Rotation(sgn * math.radians(30), 3, side) @ d)
        nd = (nd + Vector((0, 0, 0.25))).normalized()
        ok_limb(P, end, nd, L * 0.66, r * 0.68, depth - 1, roll + math.pi / 2, tips, forks, name)


# ================================================================= the island he tore out of the forest (in the final, scaled frame)
OK_K, OK_TZ = 0.75, 0.08     # the tree is made this much smaller and lifted this much, to stand on the island
OK_TOP = -0.95               # the island's rim
OK_DEPTH = 1.65             # rim to the tip of its cone
OK_STRATA = (0.2, 0.56)      # topsoil above the first, clay to the second, rock below

def ok_rim(a):
    return 1.62 * (1 + 0.07 * math.sin(3 * a + 0.5) + 0.04 * math.sin(5 * a + 2.0))

def ok_layer(t, a):
    """0 topsoil, 1 clay, 2 rock: the strata boundaries wave a little round the island."""
    w = 0.03 * math.sin(3 * a + 1.0)
    return 0 if t < OK_STRATA[0] + w else (1 if t < OK_STRATA[1] - w else 2)

def ok_side_r(t, a):
    """the cone's radius at t (0 rim .. 1 tip): every stratum juts out at its top and tucks in under it, so the layers read as
    ledges; the rock is broken into facets."""
    g = (1 - t) ** 1.15
    L = ok_layer(t, a); t0 = (0.0, OK_STRATA[0], OK_STRATA[1])[L]; t1 = (OK_STRATA[0], OK_STRATA[1], 1.0)[L]
    f = (t - t0) / (t1 - t0)
    g *= 1 + 0.09 * (1 - f) ** 2 - 0.03
    if L == 2: g *= 1 + 0.1 * abs(math.sin(4 * a + t * 5.0))
    return ok_rim(a) * max(0.0, g)

def ok_side(t, a, off=0.0):
    r = ok_side_r(t, a) + off
    return Vector((math.sin(a) * r, math.cos(a) * r, OK_TOP - OK_DEPTH * t))

def ok_top(rho, a):
    r = ok_rim(a) * rho
    return Vector((math.sin(a) * r, math.cos(a) * r, OK_TOP + 0.1 * (1 - rho * rho)))

def ok_island(seg=40):
    bm = bmesh.new(); rows = [[bm.verts.new(ok_top(0.0, 0))]]
    for rho in (0.3, 0.55, 0.8, 0.95):
        rows.append([bm.verts.new(ok_top(rho, 2 * math.pi * i / seg)) for i in range(seg)])
    for t in [0.0, 0.03] + [0.06 + 0.92 * j / 15 for j in range(16)]:
        rows.append([bm.verts.new(ok_side(t, 2 * math.pi * i / seg) + (Vector((0, 0, 0.02)) if t == 0.0 else Vector())) for i in range(seg)])
    rows.append([bm.verts.new(ok_side(1.0, 0))])
    for r0, r1 in zip(rows, rows[1:]):
        for i in range(seg):
            i2 = (i + 1) % seg
            if len(r0) == 1: bm.faces.new((r0[0], r1[i], r1[i2]))
            elif len(r1) == 1: bm.faces.new((r0[i], r0[i2], r1[0]))
            else: bm.faces.new((r0[i], r1[i], r1[i2], r0[i2]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm

def ok_island_paint(c, n):
    if c.z > OK_TOP + 0.005 and n.z > 0.3: return "Belly"                       # the moss of the forest floor
    t = (OK_TOP - c.z) / OK_DEPTH
    return ("Dark", "Base", "Trim")[ok_layer(max(0.0, t), math.atan2(c.x, c.y))]

def ok_rock(c, r, k=0):
    """a broken stone: a hull of twelve points on an ellipsoid, each pushed in or out by a fixed pattern (k shifts it)."""
    g = (1 + 5 ** 0.5) / 2
    dirs = [(0, 1, g), (0, -1, g), (0, 1, -g), (0, -1, -g), (1, g, 0), (-1, g, 0), (1, -g, 0), (-1, -g, 0), (g, 0, 1), (-g, 0, 1), (g, 0, -1), (-g, 0, -1)]
    pts = []
    for i, d in enumerate(dirs):
        v = Vector(d).normalized() * (0.72 + 0.28 * (((i * 7 + k * 3) % 5) / 4))
        pts.append(tuple(Vector(c) + Vector((v.x * r[0], v.y * r[1], v.z * r[2]))))
    return hull(pts)


def A_oakking():
    """The last boss (2026-10-13, remade: "same as the alien bosses - realistic details, scarier, keep the cartoon shape"): the OAK KING,
    the ancient heart of the forest, built like a real old oak. How he flies: he tore his own patch of forest out of the ground and it
    floats. He stands rooted on a floating island - a forest floor of moss on top with fallen oak leaves between his roots, fly agarics
    in front and mossy stones, and under it an upside-down cone of earth in strata, dark topsoil, brown clay and grey broken rock at the
    tip, each layer a ledge over the next; amber sap veins glow in the rock (the forest magic that holds it up), and his long roots hang
    out of the bottom in a tangle, swaying (Sway0-4, a tap root out of the tip). A slow ring of loose rocks and mossy clods torn up with
    him turns round the island with falling leaves and acorns (SpinDebris). The tree: a thick trunk whose bark stands in raised,
    flat-topped ridges with deep narrow furrows in shadow between them, broken into plates the way oak bark cracks, a slow twist in them
    as they climb; at the foot it flares into six buttresses, and out of each a root-leg runs over the forest floor, grips the rim and
    clings down the side of the island, with rootlets either side; a staircase of turkey-tail bracket fungus (orange, red and cream bands,
    cream pores beneath) on each flank. His face is carved into the smooth front of the trunk: two knot holes for eyes, each with a raised
    ring of bark round a deep socket and an ember eye with a slit pupil burning inside, slanted in anger under two heavy bark brows that
    meet in a deep, cracked furrow; a nose that is the stub of a broken branch, pale heartwood at the break; a wide split in the bark for
    a mouth, frowning at the corners, jagged pale wooden splinters for teeth (longest at the corners like fangs), a fire glowing deep
    inside, and the bark split open from the corners of the mouth; a beard of hanging moss. Two crooked oak limbs for arms, a burl at the
    elbow, fingers of knotted twigs with claw tips; the right fist holds a golden acorn, oak leaves sprouting at the wrists. His crown is
    grown, not made: three living twigs woven round his brow with antler-like tines rising from it (each with a side tine), amber beads of
    sap set in the weave, a big amber at the front. Above him five main limbs fork twice each, and every twig ends in a clump of lobed oak
    leaves turned red on top where the sun reaches, orange below, gold underneath; a golden acorn with a scaly cup hangs under every
    smaller fork."""
    P = Boss("oakking", pal(Base=((0.30, 0.21, 0.14), 0.3), Dark=((0.06, 0.04, 0.03), 0.3), Belly=((0.34, 0.46, 0.12), 0.25),
                            Metal=((1.0, 0.70, 0.18), 0.75), Lamp=((1.0, 0.62, 0.12), 0.9), Glow=((1.0, 0.38, 0.05), 0.6),
                            Glass=((0.74, 0.11, 0.05), 0.4), Accent=((0.95, 0.42, 0.06), 0.45), Trim=((0.86, 0.72, 0.48), 0.4)))

    # ---- the trunk: furrowed bark, moss on the flare, the face smooth
    def bark(c, n):
        a = math.atan2(c.x, c.y); z = c.z
        if -1.3 < z < -0.95 and n.z > 0.6 and ok_flare(a, z) > 1.08: return "Belly"   # moss on the tops of the buttresses
        if ok_face_w(a, z) > 0.5 or z > 1.3: return "Base"
        return "Dark" if ok_ridge(a, z) < -0.88 else "Base"   # only the bottom of each furrow, in shadow
    P.obj("Trunk", ok_trunk(), bark, 0, True)
    surf = ok_surf

    # ---- the face
    for s in (1, -1):
        q, n = surf(s * 0.34, 0.5)
        tilt = -s * math.radians(16)                                           # the outer corners raised: an angry slant
        P.obj("Socket", ok_oball(q - n * 0.02, (0.25, 0.1, 0.17), n, tilt), "Dark")
        P.obj("Knot", ok_ring(0.23, 0.06, n, q + n * 0.015, 1.15, tilt, 16, 5), "Base")
        P.obj("Eye", ok_oball(q + n * 0.05, (0.16, 0.05, 0.1), n, tilt), "Lamp")
        P.obj("Pupil", ok_oball(q + n * 0.09, (0.025, 0.02, 0.075), n, tilt), "Dark")
        # the brow: a heavy ridge of bark from the furrow up over the eye, low at the middle, with slabs of bark along its crest
        pts = []
        for k in range(5):
            t = k / 4; x = s * (0.04 + 0.6 * t); z = 0.6 + 0.3 * t - 0.12 * math.sin(math.pi * t) * 0.0
            b, bn = surf(x, z); pts.append(b + bn * (0.09 - 0.03 * t))
        P.obj("Brow", pipe(pts, [0.09, 0.13, 0.13, 0.11, 0.06], 8), "Base", 1)
        for k in range(4):
            t = (k + 0.5) / 4; b, bn = surf(s * (0.04 + 0.6 * t), 0.6 + 0.3 * t)
            base = b + bn * 0.12 + Vector((0, 0, 0.07))
            P.obj("BrowSlab", cone(base, base + Vector((s * 0.05, -0.02, 0.11 - 0.02 * k)), 0.05, 4), "Base", 0, False)
        # the bark split open from the corners of the mouth, out and down, and a crack up from each corner of the eye
        strip(surf, lambda t, s=s: (s * (0.5 + 0.2 * t), -0.24 - 0.32 * t + 0.02), lambda t, s=s: (s * (0.5 + 0.2 * t), -0.24 - 0.32 * t - 0.02), 3, "Crack", P, "Dark")
        strip(surf, lambda t, s=s: (s * (0.58 + 0.12 * t), 0.58 + 0.26 * t + 0.015), lambda t, s=s: (s * (0.58 + 0.12 * t), 0.58 + 0.26 * t - 0.015), 2, "Crack", P, "Dark")
    # the furrow between the brows: three deep cracks
    for x in (-0.06, 0.0, 0.06):
        strip(surf, lambda t, x=x: (x - 0.015, 0.62 + 0.36 * t), lambda t, x=x: (x + 0.015, 0.62 + 0.36 * t), 3, "Furrow", P, "Dark", -0.05, 0.02)
    # the nose: the stub of a broken branch, pale heartwood at the break
    nq, nn = surf(0.0, 0.3)
    tip = nq + nn * 0.3 + Vector((0, 0, -0.12))
    P.obj("Nose", pipe([nq - nn * 0.05, nq + nn * 0.15 + Vector((0, 0, -0.03)), tip], [0.15, 0.12, 0.1], 8, False), "Base", 0)
    P.obj("NoseBurl", ball(tuple(nq + nn * 0.08 + Vector((0, 0, 0.05))), (0.13, 0.08, 0.08), 8, 4), "Base")
    P.obj("NoseEnd", ok_oball(tip, (0.1, 0.02, 0.09), (tip - nq).normalized(), 0, 10, 4), "Trim")
    # the mouth: a wide split in the bark, frowning at the corners, fire deep inside
    mq, mn = surf(0.0, -0.2)
    P.obj("Mouth", ok_oball(mq - mn * 0.05, (0.52, 0.12, 0.26), mn, 0, 16, 8), "Dark")
    P.obj("Fire", ok_oball(mq + mn * 0.0, (0.38, 0.085, 0.14), mn, 0, 12, 6), "Glow")
    def lip(z0, sag, sgnz):
        pts = []
        for k in range(9):
            t = k / 8; x = -0.52 + 1.04 * t
            z = z0 + sag * (1 - (2 * t - 1) ** 2) - 0.1 * (2 * t - 1) ** 4
            b, bn = surf(x, z); pts.append(b + bn * 0.05)
        return pts
    up, lo = lip(0.0, 0.04, 1), lip(-0.44, -0.02, -1)
    P.obj("Lip", pipe(up, [0.05, 0.075, 0.08, 0.08, 0.08, 0.08, 0.08, 0.075, 0.05], 8), "Base")
    P.obj("Lip", pipe(lo, [0.05, 0.07, 0.08, 0.085, 0.085, 0.085, 0.08, 0.07, 0.05], 8), "Base")
    for row, pts, dz in ((0, up, -1), (1, lo, 1)):
        for k in range(1, 8):
            t = k / 8; x = -0.52 + 1.04 * t
            L = 0.12 + 0.1 * (abs(2 * t - 1) > 0.5) + 0.04 * (k % 2)               # splinters, the longest at the corners like fangs
            if row == 1: L *= 0.8
            b = pts[k] + mn * 0.03
            P.obj("Tooth", cone(b, b + mn * 0.04 + Vector((0.01 * (2 * t - 1), 0, dz * L)), 0.045 + 0.012 * (k % 2), 4), "Trim", 0, False)
    # a beard of hanging moss under the lip, longest in the middle
    for k in range(9):
        t = k / 8; x = -0.46 + 0.92 * t
        q, n = surf(x, -0.55 - 0.06 * abs(2 * t - 1))
        L = 0.75 - 0.4 * abs(2 * t - 1)
        P.obj("Moss", pipe(bez(q, q + n * 0.12 + Vector((0, 0, -0.1)), q + n * 0.16 + Vector((x * 0.08, 0, -L * 0.6)), q + n * 0.1 + Vector((x * 0.15, 0, -L)), 4),
                           [0.075, 0.07, 0.06, 0.04, 0.0], 5), "Belly")

    # ---- the crown grown round his brow: three woven twigs, antler tines, amber beads of sap
    for j in range(3):
        pts = []
        for i in range(25):
            a = 2 * math.pi * i / 24
            r = ok_base(1.17) + 0.07; z = 1.17 + 0.06 * math.sin(3 * a + j * 2 * math.pi / 3)
            pts.append(Vector((math.sin(a) * r, math.cos(a) * r, z)))
        P.obj("CrownTwig", pipe(pts, [0.04] * 25, 5, False), "Base")
    for k in range(7):
        a = math.radians(-72 + k * 24)
        d = Vector((math.sin(a), math.cos(a), 0)); h = 0.62 - 0.22 * abs(k - 3) / 3
        b = d * (ok_base(1.17) + 0.06) + Vector((0, 0, 1.2))
        top = b + d * 0.16 + Vector((0, 0, h))
        mid = b + d * 0.06 + Vector((0, 0, h * 0.55))
        P.obj("Tine", pipe(bez(b, b + Vector((0, 0, h * 0.4)), top - d * 0.1 - Vector((0, 0, h * 0.2)), top, 5), [0.06, 0.052, 0.042, 0.032, 0.02, 0.0], 6), "Base")
        sd = Vector((-d.y, d.x, 0)) * (1 if k >= 3 else -1)
        P.obj("Tine", pipe([mid, mid + sd * 0.1 + d * 0.06 + Vector((0, 0, h * 0.2)), mid + sd * 0.14 + d * 0.08 + Vector((0, 0, h * 0.36))], [0.035, 0.022, 0.0], 5), "Base")
        P.obj("Amber", ok_oball(b + d * 0.05 + Vector((0, 0, -0.02)), (0.045, 0.035, 0.06) if k != 3 else (0.1, 0.06, 0.12), d, 0, 8 if k != 3 else 12, 4 if k != 3 else 6), "Lamp")

    # ---- the crown of the tree: five limbs that fork twice; leaf clumps on every twig; acorns in pairs under the forks
    tips, forks = [], []
    for k, (dx, dy, dz) in enumerate(((-0.95, -0.3, 0.45), (-0.5, -0.32, 0.85), (0.0, -0.4, 0.9), (0.5, -0.32, 0.85), (0.95, -0.3, 0.45))):
        p0 = Vector((dx * 0.5, -0.1 + dy * 0.45, 1.2))
        ok_limb(P, p0, Vector((dx, dy, dz)), 0.95 - 0.12 * abs(dx), 0.24, 2, k * 0.7, tips, forks)
    leafcol = lambda z: "Glass" if z > 2.7 else ("Accent" if z > 2.05 else "Metal")
    golden = math.pi * (3 - math.sqrt(5))
    for ti, (c, d) in enumerate(tips):
        R = 0.35
        cc = c + d * 0.18
        P.obj("Canopy", ball(tuple(cc), (R, R, R * 0.85), 8, 4), "Glass" if leafcol(cc.z + 0.1) == "Glass" else "Accent")   # the shade inside the clump
        N = 6
        for i in range(N):                                                     # leaves spread evenly over the clump (a Fibonacci sphere)
            zz = 1 - 1.75 * (i + 0.5) / N; rr = math.sqrt(max(0.0, 1 - zz * zz)); th = golden * i + ti
            o = Vector((math.cos(th) * rr, math.sin(th) * rr, zz))
            q = cc + o * R * 0.95
            v = (o - Vector((0, 0, 0.6))).normalized()
            P.part("Cloth", ok_leaf(q + o * 0.05, 0.36, v, o), leafcol(q.z), (0, 0, 0), 0, False)
    for (c, d, r) in forks:
        if r > 0.15: continue                                                  # only the smaller forks bear acorns
        side = d.cross(Vector((0, 0, 1))).normalized()
        for bm, slot in ok_acorn(c - Vector((0, 0, r * 0.6)), 0.26, Vector((0, 0.15, -1))):
            P.obj("Acorn", bm, slot, 0, True)

    # ---- the arms: crooked oak limbs, a burl at the elbow, knotted twig fingers with claws
    for s in (1, -1):
        sh = Vector((s * 0.78, -0.05, 0.3)); el = Vector((s * 1.48, 0.05, -0.02)); wr = Vector((s * 1.8, 0.55, 0.32))
        P.obj("Arm", pipe(bez(sh, sh + Vector((s * 0.35, 0.05, 0.05)), el + Vector((-s * 0.15, -0.05, 0.0)), el, 4), [0.28, 0.24, 0.21, 0.19, 0.18], 9), "Base", 0)
        P.obj("Arm", pipe(bez(el, el + Vector((s * 0.15, 0.1, 0.05)), wr + Vector((0, -0.2, -0.12)), wr, 4), [0.18, 0.17, 0.15, 0.14, 0.13], 9), "Base", 0)
        P.obj("Burl", ball(tuple(el + Vector((0, -0.03, 0.03))), (0.24, 0.22, 0.22), 10, 5), "Base")
        P.obj("Burl", ball(tuple(sh + Vector((s * 0.12, 0.05, 0.06))), (0.24, 0.2, 0.2), 10, 5), "Base")
        for f in range(4):                                                     # three fingers and a thumb, each two knotted joints and a claw
            a = math.radians(-35 + 25 * f) if f < 3 else math.radians(-100)
            fd = Vector((s * 0.35 * math.cos(a), 0.8, math.sin(a) * 0.8 + 0.25)).normalized()
            curl = Vector((0, 0.1, -0.25)) if s == 1 else Vector((0, 0.05, 0.15))
            j1 = wr + fd * 0.28; j2 = j1 + (fd + curl).normalized() * 0.25; j3 = j2 + (fd + curl * 2.5).normalized() * 0.22
            P.obj("Finger", pipe([wr, j1, j2, j3], [0.09, 0.07, 0.05, 0.0], 6), "Base")
            for j in (j1, j2): P.obj("Knuckle", ball(tuple(j), (0.075, 0.075, 0.075), 6, 3), "Base")
            P.obj("Claw", cone(j2 + (j3 - j2) * 0.5, j3 + (j3 - j2).normalized() * 0.12, 0.04, 5), "Dark", 0, False)
        for k in range(2):
            a = math.radians(70 + 40 * k)
            q = wr + Vector((s * 0.1 * math.cos(a), -0.08, 0.1 * math.sin(a)))
            P.part("Cloth", ok_leaf(q + Vector((0, 0, 0.12)), 0.17, Vector((s * 0.6, -0.2, 0.8)), Vector((0, 1, 0.2))), ("Accent", "Glass")[k], (0, 0, 0), 0, False)
        if s == 1:
            for bm, slot in ok_acorn(wr + Vector((0.02, 0.32, 0.55)), 0.5, (0, 0.15, -1)):
                P.obj("GoldAcorn", bm, slot, 0, True)
        # hanging moss under the forearm
        for k in range(3):
            q = el + (wr - el) * (0.25 + 0.3 * k) + Vector((0, 0, -0.14))
            P.obj("Moss", pipe([q, q + Vector((0, 0.02, -0.22 + 0.06 * k)), q + Vector((s * 0.03, 0.03, -0.38 + 0.08 * k))], [0.04, 0.03, 0.0], 5), "Belly")

    # ---- bracket fungus, a staircase on each flank
    for a, zs in ((-2.0, (-0.38, -0.62, -0.88)), (2.15, (-0.52, -0.8))):
        for z in zs:
            p = ok_pt(a, z); u = Vector((p.x, p.y, 0)).normalized()
            ok_bracket(p - u * 0.05, (u.x, u.y), 0.4 - 0.05 * zs.index(z), P)

    # ---- the whole tree made smaller and lifted onto the island he tore out of the forest
    T = Matrix.Translation((0, 0, OK_TZ)) @ Matrix.Scale(OK_K, 4)
    for ob in P.parts + P.spin: ob.data.transform(T)
    mq = T @ mq

    # ---- the island: a forest floor on top, an upside-down cone of soil and rock under it
    P.obj("Island", ok_island(), ok_island_paint, 0, True)
    # his root-legs: out of each buttress, over the forest floor, gripping the rim and clinging down the side
    for k in range(OK_ROOTS):
        a = math.pi / OK_ROOTS + 2 * math.pi * k / OK_ROOTS
        d = Vector((math.sin(a), math.cos(a), 0)); w = 1 if k % 2 else -1
        p0 = T @ (d * 0.92 + Vector((0, 0, -0.95)))
        pts = [p0] + [ok_top(rho, a + 0.04 * w * rho) + Vector((0, 0, 0.08 - 0.03 * rho)) for rho in (0.62, 0.8, 0.95)]
        pts += [ok_side(t, a + 0.06 * w * t, 0.06) for t in (0.08, 0.2, 0.34, 0.46)]
        path = spline(pts, 3)
        P.obj("Root", pipe(path, [0.17 * (1 - i / len(path)) ** 0.7 + 0.015 for i in range(len(path) - 1)] + [0.0], 6),
              "Base", 0)
        side = Vector((-d.y, d.x, 0))
        for sgn in (1, -1):                                                    # two rootlets gripping the rim either side
            b = ok_top(0.96, a); e = ok_side(0.22, a + sgn * 0.22, 0.03)
            P.obj("Root", pipe(bez(b, b + side * sgn * 0.12 + d * 0.08, e + Vector((0, 0, 0.12)) + d * 0.04, e, 4), [0.06, 0.05, 0.04, 0.025, 0.0], 6), "Base")
    # the forest floor he brought with him: fallen leaves between the roots, fly agarics, mossy stones
    golden = math.pi * (3 - math.sqrt(5)); n_leaf = 0; gap = 2 * math.pi / OK_ROOTS
    for i in range(60):
        a = golden * i * 3.0; rho = 0.6 + 0.33 * ((i * 0.618) % 1.0)
        m = (a - math.pi / OK_ROOTS) % gap
        if min(m, gap - m) < 0.2 or n_leaf >= 10: continue
        q = ok_top(rho, a) + Vector((0, 0, 0.012)); n_leaf += 1
        P.part("Cloth", ok_leaf(q, 0.15, Vector((math.cos(a * 2.3), math.sin(a * 2.3), 0.05)), Vector((0.08 * math.sin(a), 0.08 * math.cos(a), 1)), 0.1, 0.008),
               ("Glass", "Accent", "Metal")[n_leaf % 3], (0, 0, 0), 0, False)
    for (a, rho, h) in ((0.0, 0.8, 0.2), (0.16, 0.86, 0.13), (-0.14, 0.88, 0.1), (2.1, 0.82, 0.16), (-2.2, 0.84, 0.15)):
        b = ok_top(rho, a)
        P.obj("Stem", pipe([b, b + Vector((0, 0, h))], [0.03, 0.024], 6), "Trim")
        cap = lathe([(0.0, 0.0), (h * 0.62, 0.0), (h * 0.6, h * 0.12), (h * 0.42, h * 0.3), (0.0, h * 0.38)], 10, "z", tuple(b + Vector((0, 0, h * 0.92))))
        P.obj("Cap", cap, lambda c, n: "Trim" if n.z < -0.5 else "Glass")
        for j in range(4):                                                     # the white flecks of a fly agaric
            aa = 2 * math.pi * j / 4 + a
            P.obj("Fleck", ball(tuple(b + Vector((math.cos(aa) * h * 0.32, math.sin(aa) * h * 0.32, h * 1.17))), (h * 0.07,) * 3, 4, 2), "Trim")
    for (a, rho, r) in ((1.05, 0.78, 0.16), (-1.05, 0.83, 0.12), (math.pi, 0.75, 0.18)):
        P.obj("Stone", ok_rock(ok_top(rho, a) + Vector((0, 0, r * 0.35)), (r, r * 0.85, r * 0.65), int(a * 10) % 7),
              lambda c, n: "Belly" if n.z > 0.55 else "Trim")
    # amber sap veins in the rock: the forest magic that holds it up
    for k in range(6):
        a0 = 2 * math.pi * k / 6 + 0.25
        pts = [ok_side(t, a0 + 0.1 * math.sin(t * 9 + k), 0.012) for t in (0.14, 0.26, 0.38, 0.5, 0.62, 0.74, 0.86)]
        P.obj("Vein", pipe(pts, [0.018, 0.018, 0.016, 0.015, 0.013, 0.01, 0.0], 4), "Glow", 0, False)
        b = pts[2]; br = [b] + [ok_side(t, a0 + 0.1 * math.sin(0.38 * 9 + k) + (0.3 if k % 2 else -0.3) * (t - 0.38) / 0.3, 0.012) for t in (0.5, 0.62, 0.7)]
        P.obj("Vein", pipe(br, [0.014, 0.012, 0.008, 0.0], 4), "Glow", 0, False)
    # his long roots hanging out of the bottom in a tangle: they sway
    for k in range(5):
        if k < 4:
            a = 2 * math.pi * k / 4 + 0.4; t = 0.8 + 0.06 * (k % 2)
            p0 = ok_side(t, a, -0.03); d = Vector((math.sin(a), math.cos(a), 0))
            L = 0.9 + 0.2 * (k % 2)
        else:
            p0 = ok_side(0.99, 0.0, -0.03); d = Vector((0.3, -0.2, 0)); L = 1.15      # the tap root out of the tip
        e = p0 + d * 0.25 + Vector((0, 0, -L))
        path = bez(p0, p0 + d * 0.25 + Vector((0, 0, -0.15)), e + Vector((d.y * 0.25, -d.x * 0.25, 0.4)), e, 7)
        name = "Sway%d" % k
        P.part(name, pipe(path, [0.1, 0.09, 0.075, 0.06, 0.045, 0.032, 0.018, 0.0], 6), "Base", tuple(p0))
        for sgn, f in ((1, 2), (-1, 4)):
            b = path[f]; side = Vector((-d.y, d.x, 0)) * sgn
            P.part(name, pipe(bez(b, b + side * 0.12 + Vector((0, 0, -0.05)), b + side * 0.2 + Vector((0, 0, -0.25)), b + side * 0.14 + d * 0.05 + Vector((0, 0, -0.55 + 0.1 * f / 4)), 4),
                              [0.045, 0.035, 0.025, 0.012, 0.0], 5), "Base", tuple(p0))

    # ---- the slow ring round the island: loose rocks and clods torn up with him, falling leaves and acorns
    hub = (0, 0, OK_TOP - 0.5)
    for k in range(16):
        a = 2 * math.pi * k / 16
        c = Vector((math.cos(a) * 2.45, math.sin(a) * 2.2, OK_TOP - 0.5 + 0.3 * math.sin(a * 3)))
        kind = k % 4
        if kind == 0:
            P.part("SpinDebris", ok_rock(c, (0.17, 0.14, 0.12), k), "Trim", hub)
        elif kind == 2:
            P.part("SpinDebris", ok_rock(c, (0.16, 0.15, 0.1), k + 3), lambda q, n: "Belly" if n.z > 0.6 else "Dark", hub)
        elif k % 8 == 1:
            for bm, slot in ok_acorn(c + Vector((0, 0, 0.12)), 0.24, (0.3 * math.cos(a), 0.3 * math.sin(a), -1)):
                P.part("SpinDebris", bm, slot, hub)
        else:
            P.part("SpinDebris", ok_leaf(c, 0.2, Vector((math.cos(a + 1), math.sin(a + 1), 0.3)), Vector((0.2, 0, 1))), ("Glass", "Accent", "Metal")[(k // 2) % 3], hub, 0, False)
    P.part("Muzzle", ball(tuple(mq + mn * 0.045), (0.06, 0.03, 0.045), 8, 4), "Glow", tuple(mq + mn * 0.045))
    return P


BOSSES = [("fox", A_fox), ("stag", A_stag), ("squirrel", A_squirrel), ("scarecrow2", A_scarecrow2), ("oakking", A_oakking)]

if __name__ == "__main__":
    os.makedirs(AB.OUT, exist_ok=True)
    for bid, fn in BOSSES:
        if ONLY and bid not in ONLY: continue
        fn().finish()
    print("DONE")
