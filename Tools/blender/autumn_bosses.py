# Sky Squad, the autumn forest's five bosses (2026-10-10: "now for the autumn forest"): the acorn airship, the harvest scarecrow, the fox
# spirit, the royal stag and the pumpkin castle. Built from code like the other worlds' bosses (alien_bosses.py lends its Boss class and shapes).
# Run: blender -b -P Tools/blender/autumn_bosses.py -- <out dir> [export] [ids,comma,separated]
# Conventions as alien_bosses.py: +Y nose, +Z up, +X right; "Prop*" spin about the nose, "Flap*" rock about the nose axis, "Sway*" about the
# wing axis, "Spin*" turn slowly about up, "Cloth" stays still without the outline, "Muzzle" is where his shots leave from.
import bpy, bmesh, math, sys, os, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mathutils import Vector, Matrix
from enemy_planes import loft, sweep, lathe, box, hull, tube, mirror_x, airfoil
import alien_bosses as AB
from alien_bosses import Boss, xf, ball, pipe, cone, bez, torus, sheet, grow, ang

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
def A_fox():
    """A spirit fox: an orange body with a white chest and black socks, tall ears, golden eyes, a crown of red leaves, five great white-
    tipped tails fanned behind it that wave one after another, and blue foxfire circling it."""
    P = Boss("fox", pal(Base=((0.92, 0.42, 0.10), 0.45), Glow=((0.45, 0.80, 1.0), 0.5), Lamp=((1.0, 0.85, 0.35), 0.8)))
    P.obj("Body", ball((0, 0.0, 0.0), (0.45, 0.95, 0.42), 16, 8), lambda c, n: "Belly" if n.z < -0.4 or (n.y > 0.5 and c.z < 0.15) else "Base", 1)
    P.obj("Chest", ball((0, 0.6, -0.05), (0.32, 0.3, 0.35), 12, 6), "Belly", 1)
    P.obj("Neck", pipe([(0, 0.6, 0.15), (0, 0.95, 0.45)], [0.25, 0.2], 10), "Base")
    P.obj("Head", ball((0, 1.05, 0.55), (0.3, 0.3, 0.27), 14, 7), lambda c, n: "Belly" if c.z < 0.5 and n.y > 0.2 else "Base", 1)
    P.obj("Snout", cone((0, 1.2, 0.5), (0, 1.6, 0.45), 0.15, 10), lambda c, n: "Belly" if c.z < 0.47 else "Base", 0, False)
    P.obj("Nose", ball((0, 1.6, 0.46), (0.05, 0.04, 0.04), 6, 3), "Dark")
    for s in (1, -1):
        P.obj("Ear", hull([(s * 0.12, 1.0, 0.75), (s * 0.3, 0.95, 0.72), (s * 0.28, 0.98, 1.15), (s * 0.2, 1.05, 0.8)]), "Base", 0, False)
        P.obj("EarIn", hull([(s * 0.16, 1.02, 0.78), (s * 0.27, 0.99, 0.76), (s * 0.26, 1.0, 1.05), (s * 0.21, 1.04, 0.8)]), "Dark", 0, False)
        P.obj("Eye", ball((s * 0.13, 1.28, 0.62), (0.05, 0.03, 0.035), 8, 4), "Lamp")
        P.obj("Pupil", ball((s * 0.13, 1.3, 0.62), (0.015, 0.012, 0.03), 6, 3), "Dark")
        for fy in (0.55, -0.6):   # legs stretched out in flight, black socks
            hip = Vector((s * 0.28, fy, -0.2))
            foot = hip + Vector((0, 0.35 if fy > 0 else -0.4, -0.35))
            P.obj("Leg", pipe([hip, foot], [0.11, 0.07], 8), lambda c, n, f=foot: "Dark" if (c - f).length < 0.15 else "Base")
    for k in range(5):   # the leaf crown
        a = math.radians(-50 + k * 25)
        P.part("Cloth", leaf((math.sin(a) * 0.22, 0.95, 0.85 + 0.05 * math.cos(a)), 0.1, (math.cos(a), 0, -math.sin(a)), (math.sin(a) * 0.3, -0.3, 1)), "Glass" if k % 2 else "Trim", (0, 0, 0), 0, False)
    for k in range(5):   # five tails, each waving on its own
        a = math.radians(-50 + k * 25)
        p0 = Vector((0, -0.85, 0.1))
        tip = p0 + Vector((math.sin(a) * 1.35, -0.75 - 0.3 * math.cos(a), 0.9 + 0.35 * math.cos(a)))
        pts = bez(p0, p0 + Vector((math.sin(a) * 0.2, -0.45, 0.0)), tip + Vector((-math.sin(a) * 0.1, 0.2, -0.45)), tip, 8)
        rr = [0.12, 0.2, 0.26, 0.28, 0.27, 0.24, 0.18, 0.1, 0.0]
        P.part("Sway%d" % k, pipe(pts, rr, 10), lambda c, n, t=tip: "Belly" if (c - t).length < 0.38 else "Base", tuple(p0), 1)
    for k in range(6):   # foxfire circling it
        a = 2 * math.pi * k / 6
        c = Vector((math.cos(a) * 1.5, math.sin(a) * 1.5, 0.4 + 0.25 * math.sin(a * 2)))
        P.part("SpinFoxfire", ball(tuple(c), (0.12, 0.12, 0.12), 8, 4), "Glow", (0, 0, 0.4))
        P.part("SpinFoxfire", cone(c + Vector((0, 0, 0.05)), c + Vector((0, -0.05, 0.32)), 0.08, 5), "Glow", (0, 0, 0.4), 0, False)
    P.part("Muzzle", ball((0, 1.62, 0.42), (0.06, 0.03, 0.04), 8, 4), "Lamp", (0, 1.62, 0.42))
    return P


# ================================================================= 4. the royal stag
def A_stag():
    """A great stag galloping through the air: a brown coat with a pale belly and throat, a mane of autumn leaves, amber eyes, and huge
    branching antlers hung with red, orange and gold leaves; its legs gallop."""
    P = Boss("stag", pal(Base=((0.50, 0.30, 0.15), 0.4), Lamp=((1.0, 0.75, 0.25), 0.8)))
    P.obj("Body", ball((0, 0.0, 0.0), (0.42, 1.0, 0.45), 16, 8), lambda c, n: "Belly" if n.z < -0.4 else "Base", 1)
    P.obj("Rump", ball((0, -0.95, 0.12), (0.12, 0.08, 0.12), 8, 4), "Belly")
    P.obj("Neck", pipe([(0, 0.7, 0.15), (0, 1.0, 0.6), (0, 1.1, 0.85)], [0.28, 0.22, 0.18], 10), lambda c, n: "Belly" if n.y > 0.5 and n.z < 0.2 else "Base", 1)
    P.obj("Head", ball((0, 1.2, 0.95), (0.18, 0.28, 0.18), 12, 6), "Base", 1)
    P.obj("Muzzle_", ball((0, 1.45, 0.88), (0.11, 0.12, 0.1), 10, 5), "Belly")
    P.obj("Nose", ball((0, 1.56, 0.9), (0.05, 0.03, 0.04), 6, 3), "Dark")
    for s in (1, -1):
        P.obj("Eye", ball((s * 0.13, 1.28, 1.02), (0.035, 0.035, 0.035), 6, 3), "Lamp")
        P.obj("Ear", ball((s * 0.2, 1.05, 1.08), (0.12, 0.05, 0.06), 8, 4), "Base")
        # the antler: a curving beam with tines, leaves hanging off it
        beam = bez((s * 0.08, 1.12, 1.1), (s * 0.35, 1.0, 1.45), (s * 0.75, 0.95, 1.7), (s * 1.05, 0.8, 2.05), 7)
        P.obj("Antler", pipe(beam, [0.06, 0.055, 0.05, 0.045, 0.04, 0.03, 0.02, 0.0], 6), "Trim")
        for k, t in enumerate((2, 4, 5, 6)):
            q = beam[t]; tip = q + Vector((s * 0.05, 0.15 + 0.05 * k, 0.32 - 0.04 * k))
            P.obj("Tine", pipe([q, tip], [0.03, 0.0], 5), "Trim")
            P.part("Cloth", leaf(tuple(tip + Vector((s * 0.12, 0.0, 0.03))), 0.13, (s, 0, 0), (0, 0.4, 1)), ("Glass", "Accent", "Trim", "Glass")[k], (0, 0, 0), 0, False)
        for fy, k in ((0.7, 0), (-0.7, 1)):   # the legs, galloping
            hip = Vector((s * 0.25, fy, -0.2))
            reach = Vector((0, 0.35, -0.5)) if k == 0 else Vector((0, -0.4, -0.45))
            name = "Sway%d" % (k * 2 + (1 if s > 0 else 0))
            P.part(name, pipe([hip, hip + reach * 0.5 + Vector((0, 0.0, -0.05)), hip + reach], [0.12, 0.07, 0.05], 8), "Base", tuple(hip))
            P.part(name, ball(tuple(hip + reach + Vector((0, 0.03, -0.04))), (0.05, 0.07, 0.05), 6, 3), "Dark", tuple(hip))
    for k in range(9):   # a mane of autumn leaves down its neck
        y = 0.7 + k * 0.05; z = 0.45 + k * 0.06
        P.part("Cloth", leaf((0.0, y, z + 0.2), 0.12, (1, 0, 0), (0, -0.6, 1)), ("Glass", "Accent", "Trim")[k % 3], (0, 0, 0), 0, False)
    P.obj("Tail", ball((0, -1.02, 0.25), (0.08, 0.1, 0.12), 8, 4), "Belly")
    P.part("Muzzle", ball((0, 1.58, 0.86), (0.05, 0.03, 0.04), 8, 4), "Lamp", (0, 1.58, 0.86))
    return P


# ================================================================= 5. the pumpkin castle
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


BOSSES = [("acorn", A_acorn), ("scarecrow", A_scarecrow), ("fox", A_fox), ("stag", A_stag), ("castle", A_castle)]

if __name__ == "__main__":
    os.makedirs(AB.OUT, exist_ok=True)
    for bid, fn in BOSSES:
        if ONLY and bid not in ONLY: continue
        fn().finish()
    print("DONE")
