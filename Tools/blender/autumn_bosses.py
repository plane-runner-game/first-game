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
    """The fox spirit (2026-10-12, remade: "make it better"): a nine-tailed kitsune leaping at the player - a sleek orange body with a
    fluffy white chest and cheek ruffs, black socks, a long snout with a sly smile, slanted golden eyes painted with red kabuki marks and a
    red flame on the brow, tall ears with white fluff and black tips, a gold circlet with a crown of red leaves, a sacred rope collar with
    red tassels and a golden bell, nine great tails fanned behind it each ending in a tongue of blue foxfire that wave one after another,
    and foxfire wisps circling it."""
    P = Boss("fox", pal(Base=((0.95, 0.45, 0.10), 0.45), Belly=((0.98, 0.96, 0.92), 0.3), Accent=((0.85, 0.08, 0.10), 0.5),
                        Trim=((1.0, 0.78, 0.25), 0.85), Glass=((0.98, 0.93, 0.80), 0.4), Dark=((0.06, 0.04, 0.04), 0.5),
                        Glow=((0.35, 0.82, 1.0), 0.5), Metal=((0.10, 0.07, 0.07), 0.3), Lamp=((1.0, 0.82, 0.25), 0.8)))
    coat = lambda c, n: "Belly" if n.z < -0.45 else "Base"
    # the body: a deep chest, a lean waist, haunches
    P.obj("Body", loft([(0.85, 0.2, 0.24, 0, 0.22), (0.6, 0.34, 0.38, 0, 0.12), (0.2, 0.33, 0.35, 0, 0.04), (-0.25, 0.27, 0.29, 0, 0.04),
                        (-0.6, 0.31, 0.32, 0, 0.1), (-0.88, 0.14, 0.15, 0, 0.16)], 18), coat, 1)
    P.obj("Chest", ball((0, 0.74, 0.08), (0.24, 0.16, 0.26), 12, 6), "Belly", 1)
    for k in range(5):   # the fluffy white chest
        a = math.radians(-50 + 25 * k)
        b = Vector((math.sin(a) * 0.15, 0.82 + math.cos(a) * 0.04, -0.08))
        P.obj("ChestFluff", cone(b, b + Vector((math.sin(a) * 0.04, 0.06, -0.14)), 0.07, 5), "Belly", 0, False)
    P.obj("Neck", pipe([(0, 0.68, 0.2), (0, 0.92, 0.45), (0, 1.02, 0.56)], [0.25, 0.22, 0.2], 12), lambda c, n: "Belly" if n.y > 0.4 and n.z < 0.3 else "Base", 1)
    # the head
    hc = Vector((0, 1.1, 0.62))
    P.obj("Head", ball(tuple(hc), (0.3, 0.28, 0.26), 16, 8), lambda c, n: "Belly" if c.z < hc.z - 0.08 and n.y > 0.1 else "Base", 1)
    P.obj("Snout", loft([(1.22, 0.16, 0.13, 0, 0.55), (1.42, 0.11, 0.09, 0, 0.52), (1.6, 0.06, 0.05, 0, 0.5), (1.66, 0.03, 0.03, 0, 0.5)], 12),
          lambda c, n: "Belly" if n.z < 0.05 else "Base", 1)
    P.obj("Nose", ball((0, 1.66, 0.52), (0.05, 0.04, 0.035), 8, 4), "Dark")
    P.obj("Smile", pipe(bez((-0.1, 1.42, 0.45), (-0.04, 1.5, 0.43), (0.04, 1.5, 0.43), (0.1, 1.42, 0.45), 6), [0.012] * 7, 4), "Dark")
    P.obj("Brand", hull([(0, 1.37, 0.84), (-0.05, 1.36, 0.74), (0.05, 1.36, 0.74), (0, 1.33, 0.68), (0, 1.32, 0.95)]), "Accent", 0, False)   # the red flame on the brow
    for s in (1, -1):
        eye = ball((0, 0, 0), (0.085, 0.03, 0.04), 10, 5)
        xf(eye, Matrix.Rotation(math.radians(s * 20), 3, "Y"), (s * 0.13, hc.y + 0.24, hc.z + 0.05))
        P.obj("Eye", eye, "Lamp")
        P.obj("Pupil", ball((s * 0.13, hc.y + 0.27, hc.z + 0.05), (0.014, 0.012, 0.035), 6, 3), "Dark")
        P.obj("Liner", hull([(s * 0.04, hc.y + 0.255, hc.z + 0.02), (s * 0.24, hc.y + 0.2, hc.z + 0.1), (s * 0.3, hc.y + 0.15, hc.z + 0.17),
                             (s * 0.24, hc.y + 0.21, hc.z + 0.12), (s * 0.05, hc.y + 0.26, hc.z + 0.05)]), "Dark", 0, False)
        P.obj("Kabuki", hull([(s * 0.17, hc.y + 0.24, hc.z + 0.1), (s * 0.23, hc.y + 0.2, hc.z + 0.21), (s * 0.21, hc.y + 0.21, hc.z + 0.1), (s * 0.19, hc.y + 0.23, hc.z + 0.16)]), "Accent", 0, False)
        P.obj("Kabuki", hull([(s * 0.12, hc.y + 0.24, hc.z - 0.05), (s * 0.25, hc.y + 0.17, hc.z - 0.09), (s * 0.24, hc.y + 0.18, hc.z - 0.06), (s * 0.13, hc.y + 0.25, hc.z - 0.03)]), "Accent", 0, False)
        for k in range(3):   # white cheek ruffs
            b = Vector((s * 0.2, hc.y + 0.05, hc.z - 0.1 - k * 0.05))
            P.obj("CheekRuff", cone(b, b + Vector((s * (0.3 - k * 0.05), -0.08, -0.08 - k * 0.04)), 0.09, 5), "Belly", 0, False)
        # tall ears
        P.obj("Ear", hull([(s * 0.1, hc.y + 0.02, hc.z + 0.2), (s * 0.3, hc.y - 0.02, hc.z + 0.16), (s * 0.3, hc.y - 0.05, hc.z + 0.68), (s * 0.2, hc.y + 0.06, hc.z + 0.25)]), "Base", 0, False)
        P.obj("EarFluff", hull([(s * 0.14, hc.y + 0.05, hc.z + 0.22), (s * 0.27, hc.y + 0.02, hc.z + 0.2), (s * 0.27, hc.y + 0.0, hc.z + 0.5), (s * 0.2, hc.y + 0.07, hc.z + 0.26)]), "Belly", 0, False)
        P.obj("EarTip", cone((s * 0.29, hc.y - 0.04, hc.z + 0.52), (s * 0.3, hc.y - 0.05, hc.z + 0.7), 0.05, 5), "Metal", 0, False)
        # legs leaping: forelegs reaching, hind legs stretched back, black socks
        for front in (True, False):
            hip = Vector((s * 0.22, 0.6 if front else -0.62, -0.08))
            knee = hip + (Vector((s * 0.04, 0.3, -0.22)) if front else Vector((s * 0.04, -0.25, -0.2)))
            foot = knee + (Vector((0, 0.32, -0.12)) if front else Vector((0, -0.42, 0.0)))
            P.obj("Leg", pipe([hip, knee, foot], [0.12, 0.085, 0.06], 8), lambda c, n, f=foot, k=knee: "Metal" if (c - f).length < (k - f).length * 0.7 else "Base")
            P.obj("Paw", ball(tuple(foot), (0.075, 0.1, 0.06), 8, 4), "Metal")
    # a gold circlet with a crown of red leaves and a jewel
    P.obj("Circlet", pipe(bez((-0.22, hc.y + 0.12, hc.z + 0.2), (-0.1, hc.y + 0.26, hc.z + 0.28), (0.1, hc.y + 0.26, hc.z + 0.28), (0.22, hc.y + 0.12, hc.z + 0.2), 8), [0.025] * 9, 5), "Trim")
    P.obj("Jewel", ball((0, hc.y + 0.25, hc.z + 0.3), (0.045, 0.03, 0.055), 8, 4), "Glow")
    for k in range(5):
        a = math.radians(-44 + k * 22)
        P.obj("CrownLeaf", leaf((math.sin(a) * 0.17, hc.y + 0.12, hc.z + 0.36 + 0.04 * math.cos(a)), 0.085, (math.cos(a), 0, -math.sin(a)), (math.sin(a) * 0.4, 0.1, 1)), "Accent" if k % 2 == 0 else "Trim", 0, False)
    # the sacred rope collar, red tassels, and the golden bell
    rope = torus(0.25, 0.04, 0.0, 22, 6)
    xf(rope, Matrix.Rotation(math.radians(55), 3, "X"), (0, 0.85, 0.36))
    P.obj("Rope", rope, "Glass")
    for s in (1, -1):
        b = Vector((s * 0.2, 0.98, 0.28))
        P.obj("Tassel", cone(b, b + Vector((s * 0.05, 0.03, -0.25)), 0.045, 6), "Accent", 0, False)
    P.obj("Bell", lathe([(0.0, 0.0), (0.06, -0.02), (0.08, -0.1), (0.09, -0.15), (0.0, -0.15)], 12, "z", (0, 1.06, 0.2)), "Trim")
    P.obj("BellSlot", ball((0, 1.13, 0.1), (0.04, 0.015, 0.015), 6, 3), "Dark")
    # nine tails fanned behind, each tipped with a tongue of foxfire, waving one after another
    for k in range(9):
        a = math.radians(-64 + k * 16)
        p0 = Vector((0, -0.85, 0.15))
        lift = math.cos(a)
        tip = p0 + Vector((math.sin(a) * 1.45, -0.6 - 0.25 * lift, 0.75 + 0.5 * lift))
        pts = bez(p0, p0 + Vector((math.sin(a) * 0.15, -0.45, 0.05)), tip + Vector((-math.sin(a) * 0.15, 0.25, -0.45)), tip, 8)
        rr = [0.1, 0.17, 0.22, 0.24, 0.23, 0.2, 0.15, 0.08, 0.0]
        name = "Sway%d" % k
        P.part(name, pipe(pts, rr, 10), lambda c, n, t=tip: "Belly" if (c - t).length < 0.42 else "Base", tuple(p0), 1)
        d = (pts[-1] - pts[-3]).normalized()
        P.part(name, pipe(bez(tip - d * 0.05, tip + d * 0.12, tip + d * 0.22 + Vector((0, 0, 0.1)), tip + d * 0.32 + Vector((0, -0.05, 0.2)), 4), [0.11, 0.1, 0.07, 0.035, 0.0], 7), "Glow", tuple(p0))
    # foxfire wisps circling it
    for k in range(8):
        a = 2 * math.pi * k / 8
        c = Vector((math.sin(a) * 1.55, math.cos(a) * 1.55, 0.35 + 0.25 * math.sin(a * 2)))
        P.part("SpinFoxfire", ball(tuple(c), (0.1, 0.1, 0.1), 8, 4), "Glow", (0, 0, 0.35))
        P.part("SpinFoxfire", pipe(bez(c + Vector((0, 0, 0.04)), c + Vector((0, 0, 0.15)), c + Vector((0.05, -0.05, 0.25)), c + Vector((0, -0.1, 0.36)), 3), [0.08, 0.06, 0.03, 0.0], 6), "Glow", (0, 0, 0.35))
    P.part("Muzzle", ball((0, 1.65, 0.45), (0.06, 0.03, 0.04), 8, 4), "Lamp", (0, 1.65, 0.45))
    return P


# ================================================================= 4. the royal stag
def A_stag():
    """The royal stag (2026-10-12, remade: "make it better"): a mighty stag galloping through the air - a rich brown coat with a pale
    throat ruff, a noble head with blazing amber eyes under a stern brow, a golden circlet with a jewel, colossal branching ivory antlers with
    gold-capped tines hung with red and gold leaves and two glowing lanterns, a royal crimson caparison with a gold border and a gold oak-leaf
    emblem draped over his back, a gold breastplate medallion, hooves of jet, and a whirl of autumn leaves circling him."""
    P = Boss("stag", pal(Base=((0.46, 0.26, 0.12), 0.4), Belly=((0.95, 0.88, 0.74), 0.3), Accent=((0.66, 0.06, 0.08), 0.5),
                         Trim=((1.0, 0.76, 0.22), 0.85), Glass=((0.92, 0.85, 0.68), 0.45), Dark=((0.05, 0.03, 0.02), 0.6),
                         Glow=((1.0, 0.62, 0.15), 0.5), Metal=((0.85, 0.30, 0.06), 0.4), Lamp=((1.0, 0.82, 0.35), 0.8)))
    coat = lambda c, n: "Belly" if n.z < -0.5 else "Base"
    P.obj("Body", loft([(0.85, 0.28, 0.34, 0, 0.18), (0.5, 0.4, 0.46, 0, 0.06), (0.0, 0.36, 0.42, 0, 0.0), (-0.5, 0.39, 0.44, 0, 0.05),
                        (-0.85, 0.27, 0.3, 0, 0.1), (-1.0, 0.1, 0.12, 0, 0.12)], 18), coat, 1)
    P.obj("Neck", pipe([(0, 0.72, 0.2), (0, 0.95, 0.6), (0, 1.05, 0.92)], [0.3, 0.24, 0.2], 12), "Base", 1)
    P.obj("Throat", ball((0, 0.98, 0.48), (0.2, 0.14, 0.24), 12, 6), "Belly", 1)
    for k in range(8):   # the pale throat ruff
        a = math.radians(-80 + 160 * k / 7); z = 0.42
        b = Vector((math.sin(a) * 0.2, 0.98 + math.cos(a) * 0.08, z))
        P.obj("Ruff", cone(b, b + Vector((math.sin(a) * 0.05, 0.07, -0.15)), 0.08, 5), "Belly", 0, False)
    # the head: a long noble face
    P.obj("Head", loft([(0.95, 0.17, 0.2, 0, 1.08), (1.15, 0.18, 0.19, 0, 1.06), (1.38, 0.13, 0.12, 0, 0.98), (1.55, 0.09, 0.09, 0, 0.92), (1.62, 0.05, 0.05, 0, 0.9)], 14),
          lambda c, n: "Belly" if n.z < -0.3 or c.y > 1.48 else "Base", 1)
    P.obj("Nose", ball((0, 1.62, 0.93), (0.065, 0.04, 0.05), 8, 4), "Dark")
    P.obj("Mouth", pipe([(-0.07, 1.5, 0.84), (0, 1.53, 0.83), (0.07, 1.5, 0.84)], [0.01] * 3, 4), "Dark")
    for s in (1, -1):
        P.obj("Socket", ball((s * 0.14, 1.18, 1.13), (0.07, 0.06, 0.055), 8, 4), "Dark")
        P.obj("Eye", ball((s * 0.15, 1.21, 1.13), (0.05, 0.035, 0.04), 8, 4), "Glow")
        P.obj("Pupil", ball((s * 0.155, 1.235, 1.13), (0.02, 0.015, 0.025), 6, 3), "Dark")
        P.obj("Brow", hull([(s * 0.05, 1.24, 1.21), (s * 0.24, 1.15, 1.22), (s * 0.24, 1.13, 1.18), (s * 0.06, 1.22, 1.17)]), "Dark", 0, False)
        ear = ball((0, 0, 0), (0.15, 0.05, 0.07), 10, 5)
        xf(ear, Matrix.Rotation(math.radians(-s * 25), 3, "Y"), (s * 0.27, 1.02, 1.17))
        P.obj("Ear", ear, lambda c, n: "Belly" if n.y > 0.5 else "Base")
        # the antlers: a great beam sweeping up and back, gold-capped tines, leaves and lanterns hanging
        beam = bez((s * 0.1, 1.05, 1.25), (s * 0.4, 0.95, 1.55), (s * 0.85, 0.85, 1.75), (s * 1.25, 0.6, 2.25), 9)
        P.obj("Antler", pipe(beam, [0.075, 0.07, 0.065, 0.06, 0.055, 0.05, 0.04, 0.035, 0.025, 0.0], 8), "Glass")
        P.obj("Burr", torus(0.08, 0.025, 0.0, 10, 4), "Glass"); P.parts[-1].data.transform(Matrix.Translation(beam[1]))
        for k, (t, d) in enumerate(((2, (0.05, 0.25, 0.4)), (3, (-0.05, -0.1, 0.5)), (5, (0.08, 0.2, 0.45)), (6, (0.05, -0.15, 0.5)), (7, (0.12, 0.15, 0.35)), (8, (0.15, -0.1, 0.25)))):
            q = beam[t]; tip = q + Vector((s * d[0], d[1], d[2]))
            mid = (q + tip) * 0.5 + Vector((s * 0.04, 0, -0.03))
            P.obj("Tine", pipe([q, mid, tip], [0.04, 0.03, 0.012], 6), "Glass")
            P.obj("TineCap", ball(tuple(tip), (0.03, 0.03, 0.04), 6, 3), "Trim")
            if k in (0, 2, 4):
                P.obj("Leaf", leaf(tuple(q + Vector((s * 0.08, 0.05, -0.12))), 0.13, (s, 0.2, 0), (0, 0.3, -1)), ("Accent", "Trim", "Metal")[k // 2], 0, False)
        for t in (4, 7):   # two lanterns hanging from each antler
            q = beam[t]
            P.obj("Line", pipe([q, q + Vector((0, 0, -0.22))], [0.008, 0.008], 4), "Dark")
            P.obj("LanternCap", lathe([(0.0, -0.2), (0.07, -0.24), (0.05, -0.26)], 8, "z", tuple(q)), "Trim")
            P.obj("Lantern", lathe([(0.05, -0.26), (0.06, -0.38), (0.0, -0.4)], 8, "z", tuple(q)), "Lamp")
        # the legs, galloping, jet hooves
        for fy, k in ((0.62, 0), (-0.62, 1)):
            hip = Vector((s * 0.24, fy, -0.15))
            if k == 0: knee = hip + Vector((0, 0.32, -0.3)); foot = knee + Vector((0, -0.05, -0.38))
            else: knee = hip + Vector((0, -0.12, -0.38)); foot = knee + Vector((0, -0.4, -0.15))
            name = "Sway%d" % (k * 2 + (1 if s > 0 else 0))
            P.part(name, ball(tuple(hip + Vector((0, 0, 0.05))), (0.17, 0.25, 0.25), 10, 5), "Base", tuple(hip), 1)
            P.part(name, pipe([hip, knee, foot], [0.13, 0.065, 0.05], 8), "Base", tuple(hip))
            P.part(name, lathe([(0.07, 0.0), (0.075, -0.1), (0.0, -0.11)], 8, "z", tuple(foot)), "Dark", tuple(hip))
    # the gold circlet and its jewel
    circ = torus(0.17, 0.025, 0.0, 18, 5)
    xf(circ, Matrix.Rotation(math.radians(-30), 3, "X"), (0, 1.07, 1.24))
    P.obj("Circlet", circ, "Trim")
    P.obj("Jewel", ball((0, 1.22, 1.22), (0.05, 0.03, 0.06), 8, 4), "Accent")
    for k in range(5):
        a = math.radians(-60 + 30 * k)
        b = Vector((math.sin(a) * 0.16, 1.07 + math.cos(a) * 0.14, 1.27 - math.cos(a) * 0.07))
        P.obj("CirclePoint", cone(b, b + Vector((0, 0.02, 0.12)), 0.03, 4), "Trim", 0, False)
    # the royal caparison over his back: crimson, a gold border, a gold emblem on each side
    def cap_pt(u, v):
        y = 0.5 - 1.2 * u; a = math.radians(-105 + 210 * v)
        R = 0.47 + 0.03 * math.sin(math.pi * u)
        return (math.sin(a) * R, y, 0.07 + math.cos(a) * R)
    polys = [[cap_pt(i / 12, j / 14), cap_pt((i + 1) / 12, j / 14), cap_pt((i + 1) / 12, (j + 1) / 14), cap_pt(i / 12, (j + 1) / 14)] for i in range(12) for j in range(14)]
    def cap_paint(c, n):
        a = abs(math.degrees(math.atan2(c.x, c.z - 0.07)))
        if a > 92 or c.y > 0.43 or c.y < -0.63: return "Trim"
        return "Accent"
    P.part("Cloth", sheet(polys, 0.02), cap_paint, (0, 0, 0), 0, False)
    for s in (1, -1):
        P.part("Cloth", leaf((s * 0.49, -0.08, -0.12), 0.13, (0, 1, 0), (0, 0, 1)), "Trim", (0, 0, 0), 0, False)
        for k in range(4):   # gold tassels along the hem
            b = Vector((s * 0.46, 0.35 - k * 0.3, -0.07))
            P.obj("Tassel", cone(b, b + Vector((0, 0, -0.14)), 0.03, 5), "Trim", 0, False)
    P.obj("Medallion", lathe([(0.0, 0.0), (0.14, 0.0), (0.14, 0.03), (0.0, 0.05)], 16, "y", (0, 1.02, 0.28)), "Trim")
    P.obj("MedalGem", ball((0, 1.08, 0.28), (0.06, 0.025, 0.06), 8, 4), "Glow")
    P.obj("Tail", ball((0, -1.02, 0.22), (0.09, 0.12, 0.14), 8, 4), "Belly")
    # a whirl of autumn leaves circling him
    for k in range(12):
        a = 2 * math.pi * k / 12
        c = Vector((math.sin(a) * 1.6, math.cos(a) * 1.6, 0.6 + 0.35 * math.sin(a * 3)))
        P.part("SpinLeaves", leaf(tuple(c), 0.12, (math.cos(a), -math.sin(a), 0.3), (0, 0.3, 1)), ("Accent", "Trim", "Metal")[k % 3], (0, 0, 0.6), 0, False)
    P.part("Muzzle", ball((0, 1.62, 0.84), (0.05, 0.03, 0.04), 8, 4), "Glow", (0, 1.62, 0.84))
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


def A_scarecrow2():
    """The harvest scarecrow with a new head: a big ribbed jack-o'-lantern carved with a menacing, mischievous face - slanted triangle eyes
    under carved brows, a glowing pupil in each, a carved nose and a wide jagged grin with teeth, all burning gold from within, a curled
    stalk and a battered straw hat tipped back so the face reads."""
    P = Boss("scarecrow2", pal(Glass=((0.62, 0.12, 0.10), 0.35), Metal=((0.20, 0.30, 0.55), 0.35), Lamp=((1.0, 0.95, 0.6), 0.9),
                               Glow=((1.0, 0.62, 0.12), 0.5), Belly=((0.30, 0.42, 0.14), 0.4)))
    hc = Vector((0, 0.0, 1.3)); R = 0.62; H = 0.95
    P.obj("Head", pumpkin(tuple(hc), R, H, 12, 44, 14), "Accent", 1)
    surf = ellipsoid_surf(hc, R * 0.97, R * 0.97, H * 0.5)
    def feature(name, quad, grow_k=1.18):
        cx = sum(p[0] for p in quad) / len(quad); cz = sum(p[1] for p in quad) / len(quad)
        rim = [(cx + (x - cx) * grow_k, cz + (z - cz) * grow_k) for x, z in quad]
        P.obj("Cut", carve_on(surf, rim, -0.05, 0.012), "Dark", 0, False)
        P.obj(name, carve_on(surf, quad, -0.05, 0.022), "Glow", 0, False)
    for s in (1, -1):
        eye = [(s * 0.06, hc.z + 0.12), (s * 0.36, hc.z + 0.26), (s * 0.27, hc.z - 0.02)]
        feature("Eye", eye)
        q, n = surf(s * 0.24, hc.z + 0.1)
        P.obj("Pupil", ball(tuple(q + n * 0.03), (0.045, 0.03, 0.045), 8, 4), "Lamp")
        brow = [(s * 0.04, hc.z + 0.24), (s * 0.40, hc.z + 0.40), (s * 0.40, hc.z + 0.34), (s * 0.06, hc.z + 0.19)]
        P.obj("Brow", carve_on(surf, brow, -0.03, 0.035), "Dark", 0, False)
    feature("Nose", [(-0.08, hc.z - 0.02), (0.08, hc.z - 0.02), (0.0, hc.z - 0.14)])
    def top(t):
        x = -0.46 + 0.92 * t; return (x, hc.z - 0.20 + 0.55 * x * x)
    def bot(t):
        x = -0.40 + 0.80 * t; return (x, hc.z - 0.40 + 0.45 * x * x)
    def top_r(t):
        x = -0.50 + 1.0 * t; return (x, hc.z - 0.17 + 0.55 * x * x)
    def bot_r(t):
        x = -0.44 + 0.88 * t; return (x, hc.z - 0.44 + 0.45 * x * x)
    strip(surf, top_r, bot_r, 10, "Cut", P, "Dark", -0.05, 0.012)
    strip(surf, top, bot, 10, "Grin", P, "Glow", -0.05, 0.022)
    for x in (-0.27, -0.09, 0.09, 0.27):   # upper teeth
        zt = hc.z - 0.20 + 0.55 * x * x
        P.obj("Tooth", carve_on(surf, [(x - 0.055, zt + 0.01), (x + 0.055, zt + 0.01), (x, zt - 0.09)], -0.05, 0.03), "Accent", 0, False)
    for x in (-0.18, 0.0, 0.18):   # lower teeth
        zb = hc.z - 0.40 + 0.45 * x * x
        P.obj("Tooth", carve_on(surf, [(x - 0.05, zb - 0.01), (x + 0.05, zb - 0.01), (x, zb + 0.08)], -0.05, 0.03), "Accent", 0, False)
    P.obj("Stalk", pipe(bez((0, -0.05, hc.z + 0.42), (0.02, -0.05, hc.z + 0.6), (0.15, -0.1, hc.z + 0.7), (0.25, -0.05, hc.z + 0.62), 6), [0.08, 0.075, 0.07, 0.06, 0.05, 0.04, 0.03], 7), "Belly")
    tilt = Matrix.Rotation(math.radians(-28), 4, "X") @ Matrix.Rotation(math.radians(10), 4, "Y")
    def hat(bm):
        for v in bm.verts: v.co = (tilt @ (v.co - Vector((0, 0, hc.z + 0.42)))) + Vector((0, -0.18, hc.z + 0.5))
        return bm
    P.obj("Brim", hat(lathe([(0.0, hc.z + 0.42), (0.78, hc.z + 0.40), (0.84, hc.z + 0.36), (0.0, hc.z + 0.46)], 22, "z")), "Trim")
    P.obj("Crown", hat(lathe([(0.36, hc.z + 0.42), (0.31, hc.z + 0.72), (0.12, hc.z + 0.82), (0.0, hc.z + 0.8)], 16, "z")), "Trim")
    P.obj("Band", hat(lathe([(0.365, hc.z + 0.43), (0.35, hc.z + 0.52), (0.0, hc.z + 0.52)], 16, "z")), "Glass")
    for k in range(7):
        a = math.radians(200 + k * 20)
        P.obj("StrawHat", hat(cone((math.cos(a) * 0.55, math.sin(a) * 0.55, hc.z + 0.4), (math.cos(a) * 0.95, math.sin(a) * 0.95, hc.z + 0.3), 0.03, 4)), "Trim", 0, False)
    P.obj("Pole", pipe([(0, -0.1, -1.4), (0, -0.1, 1.0)], [0.07, 0.07], 8), "Base")
    P.obj("Bar", pipe([(-1.5, -0.12, 0.75), (1.5, -0.12, 0.75)], [0.06, 0.06], 8), "Base")
    P.obj("Shirt", ball((0, 0.0, 0.45), (0.45, 0.32, 0.5), 14, 7), lambda c, n: "Metal" if ((c.x * 4) % 1.0 < 0.15 or (c.z * 4) % 1.0 < 0.15) else "Glass", 1)
    P.obj("Patch", box((0.15, 0.3, 0.55), (0.16, 0.03, 0.16)), "Trim", 0, False)
    P.obj("Rope", torus(0.4, 0.035, 0.0, 16, 4), "Trim"); P.parts[-1].data.transform(Matrix.Translation((0, 0.0, 0.08)))
    for s in (1, -1):
        P.obj("Sleeve", pipe([(s * 0.35, 0, 0.75), (s * 1.1, -0.05, 0.75)], [0.17, 0.14], 10), lambda c, n: "Glass" if (c.x * 3) % 1.0 > 0.2 else "Metal", 1)
        for k in range(6):
            a = 2 * math.pi * k / 6
            P.obj("Straw", cone((s * 1.12, -0.05, 0.75), (s * 1.4, -0.05 + math.cos(a) * 0.12, 0.75 + math.sin(a) * 0.12), 0.03, 4), "Trim", 0, False)
        for k in range(4):
            P.obj("StrawLeg", cone((s * 0.15, 0.0, 0.05), (s * (0.15 + 0.05 * k), 0.05 * k - 0.05, -0.45 - 0.05 * k), 0.035, 4), "Trim", 0, False)
        P.part("Cloth", sheet([[(s * 0.38, -0.25, 0.25), (s * 0.15, -0.3, 0.3), (s * 0.3, -0.55, -0.4)], [(s * 0.38, -0.25, 0.25), (s * 0.3, -0.55, -0.4), (s * 0.55, -0.45, -0.25)]], 0.02),
               "Metal", (0, 0, 0), 0, False)
    def crow(c, spin):
        c = Vector(c)
        parts = [ball(tuple(c), (0.1, 0.16, 0.1), 8, 4), ball(tuple(c + Vector((0, 0.14, 0.08))), (0.07, 0.07, 0.07), 8, 4), cone(c + Vector((0, 0.2, 0.08)), c + Vector((0, 0.3, 0.06)), 0.025, 4)]
        for s2 in (1, -1): parts.append(sheet([[tuple(c + Vector((s2 * 0.05, 0.05, 0.02))), tuple(c + Vector((s2 * 0.35, -0.05, 0.12))), tuple(c + Vector((s2 * 0.05, -0.1, 0.02)))]], 0.02))
        for b in parts:
            if spin: P.part("SpinCrows", b, "Dark", (0, 0, 0.6), 0, False)
            else: P.obj("Crow", b, "Dark", 0, False)
    crow((0.95, -0.12, 0.87), False)
    for k in range(4):
        a = 2 * math.pi * k / 4 + 0.4
        crow((math.cos(a) * 1.9, math.sin(a) * 1.4, 0.9 + 0.3 * math.sin(a * 2)), True)
    q, n = surf(0.0, hc.z - 0.3)
    P.part("Muzzle", ball(tuple(q + n * 0.04), (0.07, 0.03, 0.05), 8, 4), "Glow", tuple(q + n * 0.04))
    return P


def A_squirrel():
    """The SQUIRREL KNIGHT (2026-10-12, remade: "make it better"): a red squirrel in gilded plate flying on two pairs of great maple-leaf
    wings - big glossy eyes under fierce brows, a cocky buck-toothed grin, tufted ears through a golden helmet with a nose guard and a red
    plume, a breastplate with an oak-leaf emblem, layered pauldrons, a red acorn shield with a gold acorn on it and a spiked chestnut mace, a
    crimson cape, a huge fluffy curled tail striped cream along its inside, and golden acorns orbiting him."""
    P = Boss("squirrel", pal(Base=((0.80, 0.36, 0.10), 0.4), Belly=((0.98, 0.90, 0.76), 0.35), Glass=((0.66, 0.06, 0.06), 0.45),
                             Metal=((0.95, 0.70, 0.25), 0.85), Dark=((0.07, 0.04, 0.03), 0.6), Lamp=((1.0, 1.0, 0.95), 0.9),
                             Glow=((1.0, 0.72, 0.25), 0.5), Accent=((0.45, 0.24, 0.10), 0.4)))
    P.obj("Body", ball((0, 0.0, 0.0), (0.42, 0.38, 0.55), 16, 8), lambda c, n: "Belly" if n.y > 0.35 and abs(c.x) < 0.25 else "Base", 1)
    # the breastplate with an oak-leaf emblem, a tasset skirt, a belt
    P.obj("Breastplate", ball((0, 0.12, 0.12), (0.37, 0.31, 0.38), 16, 8), lambda c, n: "Trim" if abs(c.z + 0.17) < 0.035 else "Metal", 1)
    P.obj("Emblem", leaf((0, 0.44, 0.15), 0.14, (1, 0, 0), (0, 0.25, 1)), "Glass", 0, False)
    for k in range(7):
        a = math.radians(-75 + 25 * k)
        b = Vector((math.sin(a) * 0.4, math.cos(a) * 0.36, -0.25))
        P.obj("Tasset", hull([b + Vector((-0.08, 0, 0)), b + Vector((0.08, 0, 0)), b + Vector((-0.07, 0.05, -0.22)), b + Vector((0.07, 0.05, -0.22)),
                              b + Vector((0, -0.05, -0.1))]), "Metal" if k % 2 else "Trim", 0, False)
    P.obj("Belt", torus(0.41, 0.045, -0.2, 22, 5), "Accent")
    P.obj("Buckle", box((0, 0.42, -0.2), (0.11, 0.04, 0.09)), "Metal", 0, False)
    # the head and face
    hc = Vector((0, 0.12, 0.85))
    P.obj("Head", ball(tuple(hc), (0.42, 0.38, 0.38), 16, 8), lambda c, n: "Belly" if n.y > 0.55 and c.z < hc.z - 0.02 else "Base", 1)
    P.obj("Snout", ball((0, hc.y + 0.32, hc.z - 0.1), (0.17, 0.14, 0.12), 12, 6), "Belly", 1)
    P.obj("Nose", ball((0, hc.y + 0.46, hc.z - 0.04), (0.065, 0.04, 0.045), 8, 4), "Dark")
    P.obj("Grin", pipe(bez((-0.12, hc.y + 0.38, hc.z - 0.12), (-0.06, hc.y + 0.44, hc.z - 0.19), (0.06, hc.y + 0.44, hc.z - 0.19), (0.13, hc.y + 0.39, hc.z - 0.1), 6), [0.014] * 7, 4), "Dark")
    for s in (1, -1):
        P.obj("Tooth", box((s * 0.03, hc.y + 0.44, hc.z - 0.23), (0.05, 0.02, 0.07)), "Lamp", 0, False)
        P.obj("Eye", ball((s * 0.17, hc.y + 0.29, hc.z + 0.04), (0.11, 0.07, 0.13), 12, 6), "Dark")
        P.obj("Shine", ball((s * 0.14, hc.y + 0.35, hc.z + 0.09), (0.04, 0.015, 0.04), 6, 3), "Lamp")
        P.obj("Shine2", ball((s * 0.2, hc.y + 0.35, hc.z - 0.01), (0.018, 0.01, 0.018), 6, 3), "Lamp")
        P.obj("Brow", hull([(s * 0.05, hc.y + 0.36, hc.z + 0.18), (s * 0.3, hc.y + 0.28, hc.z + 0.27), (s * 0.3, hc.y + 0.3, hc.z + 0.21), (s * 0.05, hc.y + 0.38, hc.z + 0.13),
                             (s * 0.05, hc.y + 0.32, hc.z + 0.15), (s * 0.3, hc.y + 0.24, hc.z + 0.23)]), "Dark", 0, False)
        P.obj("Cheek", ball((s * 0.25, hc.y + 0.25, hc.z - 0.13), (0.08, 0.04, 0.05), 8, 4), "Glass")
        P.obj("Whisker", pipe([(s * 0.15, hc.y + 0.42, hc.z - 0.08), (s * 0.42, hc.y + 0.38, hc.z - 0.02)], [0.008, 0.004], 4), "Dark")
        P.obj("Whisker", pipe([(s * 0.15, hc.y + 0.42, hc.z - 0.11), (s * 0.42, hc.y + 0.38, hc.z - 0.15)], [0.008, 0.004], 4), "Dark")
        # tufted ears up through the helmet
        P.obj("Ear", hull([(s * 0.18, hc.y, hc.z + 0.36), (s * 0.36, hc.y - 0.02, hc.z + 0.32), (s * 0.4, hc.y - 0.06, hc.z + 0.78), (s * 0.27, hc.y + 0.04, hc.z + 0.4)]), "Base", 0, False)
        P.obj("Tuft", cone((s * 0.39, hc.y - 0.06, hc.z + 0.72), (s * 0.48, hc.y - 0.1, hc.z + 1.02), 0.075, 5), "Base", 0, False)
        P.obj("CheekGuard", hull([(s * 0.36, hc.y + 0.05, hc.z + 0.2), (s * 0.43, hc.y + 0.05, hc.z + 0.05), (s * 0.4, hc.y + 0.15, hc.z - 0.12), (s * 0.33, hc.y + 0.22, hc.z - 0.05),
                                  (s * 0.3, hc.y + 0.15, hc.z + 0.22), (s * 0.43, hc.y - 0.05, hc.z + 0.1)]), "Metal", 0, False)
    # the golden helmet: a dome with ribs, a rim, a nose guard and a red plume
    P.obj("Helmet", lathe([(0.43, hc.z + 0.2), (0.44, hc.z + 0.28), (0.38, hc.z + 0.42), (0.24, hc.z + 0.52), (0.0, hc.z + 0.56)], 22, "z", (0, hc.y - 0.04, 0)),
          lambda c, n: "Trim" if abs(c.x) < 0.035 else "Metal", 1)
    P.obj("Rim", torus(0.44, 0.04, hc.z + 0.21, 24, 5), "Trim"); P.parts[-1].data.transform(Matrix.Translation((0, hc.y - 0.04, 0)))
    P.obj("NoseGuard", box((0, hc.y + 0.4, hc.z + 0.16), (0.06, 0.04, 0.22)), "Metal", 0, False)
    P.obj("Crest", sheet([[(0, hc.y + 0.25, hc.z + 0.5), (0, hc.y - 0.3, hc.z + 0.52), (0, hc.y - 0.1, hc.z + 0.62)]], 0.03), "Trim", 0, False)
    plume = bez((0, hc.y - 0.04, hc.z + 0.55), (0, hc.y + 0.1, hc.z + 0.85), (0, hc.y - 0.2, hc.z + 1.0), (0, hc.y - 0.55, hc.z + 0.85), 9)
    P.obj("Plume", pipe(plume, [0.05, 0.09, 0.12, 0.14, 0.14, 0.12, 0.1, 0.07, 0.04, 0.0], 8), "Glass", 1)
    for s in (1, -1):
        sh = Vector((s * 0.4, 0.05, 0.25)); hand = Vector((s * 0.74, 0.38, 0.05))
        P.obj("Arm", pipe([sh, (sh + hand) * 0.5 + Vector((s * 0.05, 0, -0.08)), hand], [0.12, 0.1, 0.09], 8), "Base")
        P.obj("Bracer", pipe([(sh + hand) * 0.5 + (hand - sh) * 0.1, hand - (hand - sh) * 0.12], [0.11, 0.1], 10), "Metal")
        for k in range(3):   # layered pauldrons
            P.obj("Pauldron", ball(tuple(sh + Vector((s * 0.03 * k, 0, 0.1 - 0.07 * k))), (0.19 - 0.015 * k, 0.17, 0.1), 12, 5), "Metal" if k != 1 else "Trim")
        P.obj("Foot", ball((s * 0.2, 0.15, -0.58), (0.12, 0.18, 0.09), 8, 4), "Belly")
        P.obj("Greave", pipe([(s * 0.2, 0.08, -0.25), (s * 0.2, 0.1, -0.5)], [0.1, 0.09], 10), "Metal")
    # the acorn shield: red with a gold rim and a golden acorn on it
    sc = Vector((0.82, 0.0, 0.05))
    P.obj("Shield", lathe([(0.0, 0.36), (0.36, 0.4), (0.44, 0.47), (0.4, 0.52), (0.0, 0.56)], 24, "y", tuple(sc)), lambda c, n: "Trim" if ((c.x - sc.x) ** 2 + (c.z - sc.z) ** 2) > 0.12 else "Glass", 1)
    P.obj("ShieldAcorn", ball((sc.x, 0.6, sc.z - 0.05), (0.11, 0.05, 0.14), 10, 5), "Metal")
    P.obj("ShieldCap", ball((sc.x, 0.61, sc.z + 0.08), (0.14, 0.055, 0.07), 10, 5), "Accent")
    P.obj("ShieldStem", cone((sc.x, 0.62, sc.z + 0.13), (sc.x + 0.03, 0.62, sc.z + 0.22), 0.025, 5), "Accent", 0, False)
    # the chestnut mace
    mc = Vector((-0.74, 0.44, 0.8))
    P.obj("Haft", pipe([(-0.74, 0.38, -0.2), tuple(mc - Vector((0, 0, 0.12)))], [0.04, 0.04], 6), lambda c, n: "Trim" if (c.z * 6) % 1.0 < 0.2 else "Accent")
    P.obj("Pommel", ball((-0.74, 0.37, -0.24), (0.06, 0.06, 0.06), 8, 4), "Metal")
    P.obj("Burr", ball(tuple(mc), (0.18, 0.18, 0.18), 12, 6), "Metal")
    for k in range(18):
        a = 2 * math.pi * k / 6 + (k // 6) * 0.5; b = ((k // 6) - 1) * 0.75
        d = Vector((math.cos(a) * math.cos(b), math.sin(a) * math.cos(b), math.sin(b)))
        P.obj("Spike", cone(mc + d * 0.15, mc + d * 0.34, 0.04, 4), "Trim", 0, False)
    P.obj("Spike", cone(mc + Vector((0, 0, 0.15)), mc + Vector((0, 0, 0.38)), 0.045, 4), "Trim", 0, False)
    # the crimson cape
    def cape(u, v):
        a = math.radians(-70 + 140 * u)
        return (math.sin(a) * (0.42 + 0.25 * v), -0.18 - math.cos(a) * (0.3 + 0.2 * v), 0.5 - 1.1 * v + 0.04 * math.sin(u * 14))
    P.part("Cloth", sheet([[cape(i / 8, j / 5), cape((i + 1) / 8, j / 5), cape((i + 1) / 8, (j + 1) / 5), cape(i / 8, (j + 1) / 5)] for i in range(8) for j in range(5)], 0.02),
           lambda c, n: "Trim" if c.z < -0.5 else "Glass", (0, 0, 0), 0, False)
    # the great fluffy tail, curled up behind him, cream along its inside, tufts along its edge
    tail = spline([(0.1, -0.3, -0.3), (0.35, -0.85, -0.1), (0.75, -1.05, 0.5), (0.95, -0.85, 1.25), (0.85, -0.45, 1.75), (0.55, -0.2, 1.8), (0.45, -0.1, 1.55)], 4)
    rr = [0.15 + 0.38 * math.sin(math.pi * min(1.0, i / (len(tail) - 1) * 1.15)) for i in range(len(tail))]
    rr[-1] = 0.12
    tb = (0.1, -0.3, -0.3)
    P.part("SwayTail", pipe(tail, rr, 14), lambda c, n: "Belly" if n.y > 0.8 else "Base", tb, 1)
    for i in range(2, len(tail) - 1):
        t = (tail[i + 1] - tail[i - 1]).normalized()
        a0, b0 = AB.frame(t)
        for k in range(4):
            a = 2 * math.pi * k / 4 + i * 0.6
            d = a0 * math.cos(a) + b0 * math.sin(a)
            if d.y > 0.55: continue
            q = tail[i] + d * rr[i] * 0.92
            P.part("SwayTail", cone(tuple(q), tuple(q + d * 0.11 - t * 0.08), 0.07, 4), "Base", tb, 0, False)
    # two pairs of great maple-leaf wings, held up like a butterfly's, gold veined
    for s in (1, -1):
        root = Vector((s * 0.3, -0.28, 0.45)); nm = "Flap" + ("R" if s > 0 else "L")
        for (dx, dz, size, col, up) in ((0.72, 0.42, 0.62, "Glass", 0.55), (0.6, -0.22, 0.44, "Metal", -0.35)):
            c = root + Vector((s * dx, -0.18, dz))
            v = Vector((s * 0.65, 0.0, up)).normalized(); u = Vector((s * 0.3, 0.0, -0.95 if up > 0 else 0.95)).normalized()
            if s < 0: u = -u
            P.part(nm, leaf(tuple(c), size, tuple(u), tuple(v), 0.025), col, tuple(root), 0, False)
    # golden acorns orbiting him
    for k in range(8):
        a = 2 * math.pi * k / 8
        c = Vector((math.sin(a) * 1.45, math.cos(a) * 1.3, 0.45 + 0.3 * math.sin(a * 2)))
        P.part("SpinAcorns", ball(tuple(c), (0.08, 0.08, 0.1), 8, 4), "Metal", (0, 0, 0.45))
        P.part("SpinAcorns", ball(tuple(c + Vector((0, 0, 0.07))), (0.095, 0.095, 0.05), 8, 4), "Accent", (0, 0, 0.45))
    P.part("Muzzle", ball((0, hc.y + 0.47, hc.z - 0.15), (0.05, 0.03, 0.04), 8, 4), "Glow", (0, hc.y + 0.47, hc.z - 0.15))
    return P


def A_oakking():
    """Replaces the pumpkin castle as the last boss: the OAK KING - the ancient heart of the forest, a great oak with a face in its bark:
    heavy frowning brows, deep sockets with burning amber eyes, a gnarled nose, a mouth roaring with fire inside and a long beard of moss;
    a golden crown grown into his brow, a vast canopy of red, orange and gold above him, branch arms with golden acorns in his fists, roots
    trailing below that sway, and a ring of falling leaves and golden acorns turning round him."""
    P = Boss("oakking", pal(Base=((0.40, 0.27, 0.17), 0.35), Dark=((0.07, 0.04, 0.03), 0.35), Belly=((0.38, 0.50, 0.16), 0.3),
                            Metal=((1.0, 0.76, 0.28), 0.9), Lamp=((1.0, 0.78, 0.22), 0.9), Glow=((1.0, 0.45, 0.08), 0.6),
                            Glass=((0.80, 0.12, 0.06), 0.4), Accent=((0.95, 0.42, 0.06), 0.45), Trim=((1.0, 0.80, 0.22), 0.6)))
    def bark(c, n):
        a = math.atan2(c.x, c.y)
        if n.y > 0.6 and abs(c.x) < 0.6 and -0.6 < c.z < 1.1: return "Base"   # the face stays smooth
        return "Dark" if (a * 6.0 + math.sin(c.z * 3.0) * 0.35) % 1.0 < 0.1 else "Base"
    P.obj("Trunk", lathe([(0.0, -1.3), (0.8, -1.25), (1.05, -1.0), (0.95, -0.5), (0.9, 0.2), (0.92, 0.8), (0.82, 1.2), (0.45, 1.5), (0.0, 1.55)], 30, "z"), bark, 1)
    surf = ellipsoid_surf((0, 0, 0.15), 0.92, 0.92, 1.25)
    for s in (1, -1):
        q, n = surf(s * 0.34, 0.42)
        P.obj("Socket", ball(tuple(q - n * 0.03), (0.25, 0.1, 0.19), 12, 6), "Dark")
        P.obj("Eye", ball(tuple(q + n * 0.02), (0.16, 0.06, 0.12), 12, 6), "Lamp")
        P.obj("Pupil", ball(tuple(q + n * 0.07 + Vector((-s * 0.02, 0, 0))), (0.035, 0.02, 0.09), 6, 3), "Dark")
        b0, n0 = surf(s * 0.06, 0.6); b1, n1 = surf(s * 0.62, 0.82)
        P.obj("Brow", pipe([b0 + n0 * 0.07, (b0 + b1) * 0.5 + (n0 + n1) * 0.09 + Vector((0, 0, 0.04)), b1 + n1 * 0.04], [0.11, 0.14, 0.08], 8), "Base", 1)
        c0, cn = surf(s * 0.5, 0.08)
        P.obj("Cheek", ball(tuple(c0), (0.22, 0.12, 0.17), 10, 5), "Base", 1)
    nq, nn = surf(0.0, 0.3)
    P.obj("Nose", pipe([nq - nn * 0.05, nq + nn * 0.14 + Vector((0, 0, -0.06)), nq + nn * 0.24 + Vector((0, 0, -0.18))], [0.14, 0.12, 0.09], 8), "Base", 1)
    P.obj("NoseTip", ball(tuple(nq + nn * 0.24 + Vector((0, 0, -0.2))), (0.11, 0.1, 0.09), 8, 4), "Base")
    mq, mn = surf(0.0, -0.22)
    P.obj("Mouth", ball(tuple(mq - mn * 0.03), (0.4, 0.12, 0.2), 14, 7), "Dark")
    P.obj("Fire", ball(tuple(mq), (0.3, 0.09, 0.12), 12, 6), "Glow")
    for x in (-0.24, -0.08, 0.08, 0.24):
        tq, tn = surf(x, -0.06)
        P.obj("Fang", cone(tq + tn * 0.06, tq + tn * 0.08 + Vector((0, 0, -0.13)), 0.05, 5), "Belly", 0, False)
    rng = random.Random(4)
    for k in range(21):
        x = -0.62 + 1.24 * k / 20
        q, n = surf(x, -0.44 - 0.15 * abs(x))
        L = 0.95 - 0.6 * abs(x) + rng.uniform(-0.1, 0.1)
        P.obj("Beard", pipe(bez(q, q + n * 0.14 + Vector((0, 0, -0.15)), q + n * 0.22 + Vector((x * 0.1, 0, -L * 0.6)), q + n * 0.12 + Vector((x * 0.2, 0, -L)), 4),
                            [0.08, 0.08, 0.07, 0.05, 0.0], 6), "Belly")
    # the golden crown grown into his brow: a band with tall points, a ruby at the front
    P.obj("Crown", lathe([(0.9, 0.92), (0.95, 0.96), (0.95, 1.1), (0.91, 1.13), (0.0, 1.13)], 30, "z"), "Trim")
    for k in range(11):
        a = math.radians(-75 + k * 15)
        d = Vector((math.sin(a), math.cos(a), 0))
        hgt = 0.38 if k == 5 else (0.3 if k % 2 == 0 else 0.2)
        base = d * 0.93 + Vector((0, 0, 1.1))
        P.obj("CrownPoint", cone(base, base + d * 0.08 + Vector((0, 0, hgt)), 0.07, 6), "Trim", 0, False)
        P.obj("CrownBead", ball(tuple(base + d * 0.08 + Vector((0, 0, hgt + 0.03))), (0.045, 0.045, 0.045), 6, 3), "Lamp")
    jq, jn = surf(0.0, 1.02)
    P.obj("Jewel", ball(tuple(jq + jn * 0.06), (0.11, 0.06, 0.12), 10, 5), "Glass")
    for s in (1, -1):
        g, gn = surf(s * 0.38, 1.02)
        P.obj("Gem", ball(tuple(g + gn * 0.05), (0.06, 0.04, 0.07), 8, 4), "Belly")
    # a vast canopy of autumn leaves behind and above him, thick branches holding it
    cols = ("Glass", "Accent", "Trim")
    for s in (1, -1):
        for k, tip in enumerate(((s * 1.25, -0.45, 2.0), (s * 0.55, -0.6, 2.45), (s * 1.8, -0.3, 1.45))):
            p0 = Vector((s * 0.35, -0.3, 1.25)); tip = Vector(tip)
            br = bez(p0, p0 + Vector((0, 0, 0.4)), tip + Vector((-s * 0.3, 0, -0.35)), tip, 6)
            P.obj("Branch", pipe(br, [0.22, 0.19, 0.16, 0.13, 0.1, 0.08, 0.06], 8), "Base")
    rng = random.Random(11)
    clumps = []
    for row, (el, n) in enumerate(((0.05, 11), (0.45, 10), (0.85, 8), (1.25, 5))):
        for k in range(n):
            az = math.radians(-100 + 200 * (k + 0.5 * (row % 2)) / max(1, n - 1 + 0.5 * (row % 2)))
            d = Vector((math.sin(az) * math.cos(el), -0.35 - 0.3 * math.cos(az) * math.cos(el), math.sin(el)))
            clumps.append(Vector((d.x * 2.0, -0.6 + d.y * 0.6, 1.35 + d.z * 1.15)) + Vector((rng.uniform(-0.08, 0.08), rng.uniform(-0.1, 0.1), rng.uniform(-0.08, 0.08))))
    for k, c in enumerate(clumps):
        r = rng.uniform(0.36, 0.48)
        v = math.sin(c.x * 2.3 + c.z * 1.7) * 0.5 + 0.5
        col = "Glass" if v < 0.33 else ("Accent" if v < 0.7 else "Trim")
        P.obj("Canopy", ball(tuple(c), (r, r * 0.8, r * 0.85), 10, 5), col, 1)
        for j in range(3):
            a = 2 * math.pi * (j / 3 + rng.random() * 0.2)
            q = c + Vector((math.cos(a) * r * 0.9, 0.25 * r, math.sin(a) * r * 0.85))
            if j < 2: P.part("Cloth", leaf(tuple(q), 0.2, (math.cos(a + 0.5), 0.3, 0.2), (0.2, 0.4, 1)), cols[(k + j + 1) % 3], (0, 0, 0), 0, False)
    # branch arms with golden acorns in the fists
    for s in (1, -1):
        sh = Vector((s * 0.82, 0.0, 0.25)); el = Vector((s * 1.5, 0.2, -0.05)); fist = Vector((s * 1.8, 0.6, 0.35))
        P.obj("Arm", pipe(bez(sh, el, el + Vector((s * 0.1, 0.15, 0.1)), fist, 6), [0.26, 0.22, 0.18, 0.15, 0.14, 0.14, 0.15], 8), "Base", 1)
        for j in range(3):
            a = math.radians(-40 + j * 40)
            P.obj("Twig", pipe([fist, fist + Vector((s * 0.12 * math.cos(a), 0.2, 0.22 * math.sin(a) + 0.1))], [0.06, 0.025], 5), "Base")
        P.obj("GoldAcorn", ball(tuple(fist + Vector((0, 0.12, 0.3))), (0.16, 0.16, 0.2), 10, 5), "Metal", 1)
        P.obj("GoldCap", ball(tuple(fist + Vector((0, 0.12, 0.46))), (0.18, 0.18, 0.08), 10, 5), "Dark", 1)
    # roots trailing below, swaying
    for k in range(7):
        a = 2 * math.pi * k / 7 + 0.2
        d = Vector((math.cos(a), math.sin(a), 0))
        p0 = d * 0.7 + Vector((0, 0, -1.1))
        pts = bez(p0, p0 + d * 0.45 + Vector((0, 0, -0.15)), p0 + d * 0.6 + Vector((0, 0, -0.6)), p0 + d * 0.45 + Vector((0, 0, -1.0)), 5)
        P.part("Sway%d" % (k % 2), pipe(pts, [0.2, 0.16, 0.12, 0.08, 0.05, 0.0], 7), "Base", tuple(p0))
    # a ring of falling leaves and golden acorns
    for k in range(16):
        a = 2 * math.pi * k / 16
        c = Vector((math.cos(a) * 2.5, math.sin(a) * 2.1, 0.1 + 0.35 * math.sin(a * 3)))
        if k % 2:
            P.part("SpinLeaves", ball(tuple(c), (0.11, 0.11, 0.13), 8, 4), "Metal", (0, 0, 0.1))
            P.part("SpinLeaves", ball(tuple(c + Vector((0, 0, 0.11))), (0.12, 0.12, 0.05), 8, 4), "Dark", (0, 0, 0.1))
        else:
            P.part("SpinLeaves", leaf(tuple(c), 0.22, (math.cos(a + 1), math.sin(a + 1), 0.3), (0, 0, 1)), cols[(k // 2) % 3], (0, 0, 0.1), 0, False)
    P.part("Muzzle", ball(tuple(mq + mn * 0.06), (0.08, 0.04, 0.06), 8, 4), "Glow", tuple(mq + mn * 0.06))
    return P

BOSSES = [("fox", A_fox), ("stag", A_stag), ("squirrel", A_squirrel), ("scarecrow2", A_scarecrow2), ("oakking", A_oakking)]

if __name__ == "__main__":
    os.makedirs(AB.OUT, exist_ok=True)
    for bid, fn in BOSSES:
        if ONLY and bid not in ONLY: continue
        fn().finish()
    print("DONE")
