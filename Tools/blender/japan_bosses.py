# Sky Squad, the japanese island's five bosses (2026-10-10: "give me for desert pyramids and japanese island"): the koi streamer, the snow
# crane, the samurai spirit, the sky dragon and the pagoda isle. Built from code like the other worlds' bosses (alien_bosses.py lends its Boss
# class and shapes).
# Run: blender -b -P Tools/blender/japan_bosses.py -- <out dir> [export] [ids,comma,separated]
# Conventions as alien_bosses.py: +Y nose, +Z up, +X right; "Flap*" rock about the nose axis, "Sway*" about the wing axis, "Spin*" turn slowly
# about up, "Cloth" stays still without the outline, "Muzzle" is where his shots leave from.
import bpy, bmesh, math, sys, os, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mathutils import Vector, Matrix
from enemy_planes import loft, sweep, lathe, box, hull, tube, mirror_x, airfoil
import alien_bosses as AB
from alien_bosses import Boss, xf, ball, pipe, cone, bez, torus, sheet, grow, ang

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ONLY = argv[2].split(",") if len(argv) > 2 and argv[2] else None

RED = ((0.82, 0.10, 0.08), 0.55)
GOLD = ((0.98, 0.76, 0.22), 0.8)
SAKURA = ((1.0, 0.72, 0.82), 0.4)


def speckle(c, k=1.0):
    v = math.sin(c.x * 12.9898 * k + c.y * 78.233 * k + c.z * 37.719 * k) * 43758.5453
    return v - math.floor(v)

def fine(keys, step=0.08):
    secs = []
    for a0, a1 in zip(keys, keys[1:]):
        n = max(2, int((a1[0] - a0[0]) / step))
        secs += [tuple(u + (v - u) * i / n for u, v in zip(a0, a1)) for i in range(n)]
    secs.append(keys[-1])
    return secs

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

def fan(hub, tips, thick=0.02, scallop=0.12):
    polys = []
    for a, b in zip(tips, tips[1:]):
        mid = (a + b) * 0.5 + (hub - (a + b) * 0.5) * scallop
        polys.append([hub, a, mid]); polys.append([hub, mid, b])
    return sheet([[tuple(p) for p in poly] for poly in polys], thick)

def roof(c, w, d, h, up=0.18):
    """a pagoda roof: a shallow hipped roof whose corners sweep up."""
    c = Vector(c)
    pts = [c + Vector((sx * w, sy * d, up)) for sx in (-1, 1) for sy in (-1, 1)]
    pts += [c + Vector((sx * w * 0.8, sy * d * 0.8, -0.02)) for sx in (-1, 1) for sy in (-1, 1)]
    pts += [c + Vector((sx * w * 0.35, sy * d * 0.35, h)) for sx in (-1, 1) for sy in (-1, 1)]
    return hull([tuple(p) for p in pts])


# ================================================================= 1. the koi streamer
def J_koi():
    """A koinobori, the carp streamer, swimming the sky: a red-and-white koi of cloth with gold-edged scales, a hoop for a mouth, great
    eyes, fins that row and a tail that sweeps."""
    P = Boss("koi", {"Base": RED, "Belly": ((0.98, 0.97, 0.95), 0.35), "Accent": ((0.05, 0.05, 0.07), 0.5), "Trim": GOLD,
                     "Glass": ((0.25, 0.45, 0.90), 0.6), "Dark": ((0.10, 0.03, 0.03), 0.4), "Glow": ((1.0, 0.85, 0.45), 0.5),
                     "Metal": ((0.6, 0.6, 0.6), 0.6), "Lamp": ((1.0, 0.92, 0.55), 0.8)})
    def scales(c, n):
        if n.z < -0.35: return "Belly"
        u = (c.y * 3.0) % 1.0; v = (math.atan2(c.x, c.z) * 1.6 + (0.5 if int(c.y * 3.0) % 2 else 0.0)) % 1.0
        if (u - 0.5) ** 2 + (v - 0.5) ** 2 * 0.6 > 0.3: return "Trim"
        return "Base" if speckle(Vector((int(c.y * 3), int(v * 4), 0)), 3.0) < 0.75 else "Belly"
    rings = [(1.6, 0.55, 0.55, 0, 0.0), (1.2, 0.62, 0.62, 0, 0.05), (0.5, 0.6, 0.6, 0, 0.12), (-0.3, 0.5, 0.5, 0, 0.05), (-1.0, 0.36, 0.36, 0, -0.08), (-1.6, 0.22, 0.22, 0, -0.05), (-1.9, 0.12, 0.12, 0, 0.05)]
    P.obj("Body", loft(rings, 22, cs=False), scales, 1)
    P.obj("Hoop", torus(0.55, 0.05, 0.0, 22, 6), "Trim"); P.parts[-1].data.transform(Matrix.Translation((0, 1.6, 0.0)) @ Matrix.Rotation(math.radians(90), 4, "X"))
    P.obj("Mouth", lathe([(0.0, 1.35), (0.5, 1.55)], 22, "y"), "Dark")
    for s in (1, -1):
        P.obj("EyeWhite", ball((s * 0.42, 1.2, 0.3), (0.12, 0.2, 0.2), 12, 6), "Belly")
        P.obj("Iris", ball((s * 0.5, 1.24, 0.3), (0.06, 0.14, 0.14), 10, 5), "Accent")
        P.obj("Ring", torus(0.2, 0.025, 0.0, 16, 4), "Glass"); P.parts[-1].data.transform(Matrix.Translation((s * 0.46, 1.2, 0.3)) @ Matrix.Rotation(math.radians(90), 4, "Y"))
        name = "FlapR" if s > 0 else "FlapL"
        hub = Vector((s * 0.5, 0.6, -0.25))
        P.part(name, fan(hub, [hub + Vector((s * 0.65, 0.1, -0.3)), hub + Vector((s * 0.75, -0.25, -0.35)), hub + Vector((s * 0.5, -0.55, -0.3))]), "Base", tuple(hub), 0, False)
    P.obj("Dorsal", sheet([[(0, 0.5, 0.7), (0, -0.4, 0.95), (0, -0.6, 0.55)], [(0, 0.5, 0.7), (0, -0.6, 0.55), (0, 0.1, 0.6)]], 0.02), "Base", 0, False)
    hub = Vector((0, -1.85, 0.05))
    P.part("Sway0", fan(hub, [hub + Vector((0.0, -0.4, 0.75)), hub + Vector((0.0, -0.75, 0.3)), hub + Vector((0.0, -0.55, 0.0)), hub + Vector((0.0, -0.75, -0.3)), hub + Vector((0.0, -0.4, -0.7))], 0.02, 0.2),
           lambda c, n: "Belly" if abs(c.z - 0.05) < 0.15 else "Base", tuple(hub), 0, False)
    P.part("Muzzle", ball((0, 1.62, 0.0), (0.12, 0.05, 0.12), 8, 4), "Glow", (0, 1.62, 0.0))
    return P


# ================================================================= 2. the snow crane
def slab(polys, thick=0.03):
    """flat polygons made two-sided by offsetting along each polygon's own normal (the wings stand near upright, so sheet()'s z offset would not do)."""
    bm = bmesh.new()
    for poly in polys:
        pts = [Vector(p) for p in poly]
        nrm = (pts[1] - pts[0]).cross(pts[2] - pts[0])
        nrm = nrm.normalized() if nrm.length > 1e-8 else Vector((0, 0, 1))
        top = [bm.verts.new(p + nrm * thick * 0.5) for p in pts]
        bot = [bm.verts.new(p - nrm * thick * 0.5) for p in pts]
        bm.faces.new(top); bm.faces.new(list(reversed(bot)))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm

def plume(root, tip, nrm, w, bend=0.0):
    """a long feather from root to tip lying across nrm: a tapered quill-shaped outline (bend curls the tip along nrm)."""
    root = Vector(root); tip = Vector(tip); nrm = Vector(nrm).normalized(); d = tip - root
    side = d.cross(nrm).normalized() * w
    pts = [root, root + d * 0.18 + side * 0.75, root + d * 0.55 + side, root + d * 0.85 + side * 0.65 + nrm * bend * 0.5, tip + nrm * bend,
           root + d * 0.85 - side * 0.65 + nrm * bend * 0.5, root + d * 0.55 - side, root + d * 0.18 - side * 0.75]
    c = root + d * 0.5
    return [[tuple(c), tuple(a), tuple(b)] for a, b in zip(pts, pts[1:] + pts[:1])]

def J_crane():
    """The snow crane (2026-10-12, remade: "edit it, make it better"): a majestic red-crowned crane spirit with her great wings raised high
    in display - layer on layer of snow-white feathers, the long primaries fanned and dipped in black and edged with glowing gold - a proud
    S-curved black neck, a scarlet crown under a golden crescent maedate and circlet, fierce golden eyes under dark brows, a long golden
    beak, a red-lacquered breastplate laced in gold, red silk ribbons streaming from her neck, a black-and-white tail bustle, legs trailing
    with golden talons clutching a glowing pearl, and cherry blossoms whirling round her."""
    P = Boss("crane", {"Base": ((0.97, 0.97, 0.98), 0.4), "Belly": ((0.80, 0.84, 0.92), 0.35), "Accent": ((0.05, 0.05, 0.07), 0.5),
                       "Trim": GOLD, "Glass": ((0.88, 0.07, 0.10), 0.6), "Dark": ((0.02, 0.02, 0.03), 0.6), "Glow": ((1.0, 0.55, 0.78), 0.5),
                       "Metal": ((0.62, 0.06, 0.05), 0.75), "Lamp": ((1.0, 0.82, 0.30), 0.8)})
    # the body and its breast
    P.obj("Body", ball((0, -0.05, 0.0), (0.42, 0.8, 0.4), 16, 8), lambda c, n: "Belly" if n.z < -0.45 else "Base", 1)
    # the red-lacquered breastplate (do-maru), laced in gold, with a gold mon
    def plate(c, n):
        if c.z > 0.24 or abs(c.x) < 0.035: return "Trim"   # a gold rim and the lacing down the middle
        if (c.z * 4.0) % 1.0 < 0.1: return "Trim"
        return "Metal"
    P.obj("Breastplate", ball((0, 0.4, -0.02), (0.37, 0.26, 0.34), 14, 7), plate, 1)
    P.obj("Mon", lathe([(0.0, 0.0), (0.11, 0.0), (0.11, 0.03), (0.0, 0.035)], 14, "y", (0, 0.65, 0.05)), "Trim")
    P.obj("MonGem", ball((0, 0.69, 0.05), (0.05, 0.02, 0.05), 8, 4), "Lamp")
    for s in (1, -1):
        P.obj("Shoulder", ball((s * 0.36, 0.25, 0.18), (0.18, 0.22, 0.12), 10, 5), lambda c, n: "Trim" if c.z < 0.1 else "Metal", 1)
    # the S-curved neck: white below, black above
    neck = bez((0, 0.5, 0.18), (0, 0.95, 0.38), (0, 0.72, 0.95), (0, 1.0, 1.22), 10)
    P.obj("Neck", pipe(neck, [0.22, 0.19, 0.17, 0.155, 0.145, 0.135, 0.13, 0.125, 0.12, 0.12, 0.12], 12), lambda c, n: "Accent" if c.z > 0.55 else "Base", 1)
    # the head: scarlet crown, black face, white nape (all of it drawn 1.6 times bigger about the top of the neck, so it reads)
    n_head = len(P.parts)
    HC = Vector((0, 1.08, 1.3))
    P.obj("Head", ball(tuple(HC), (0.15, 0.21, 0.15), 14, 7), lambda c, n: "Glass" if c.z > 1.38 else ("Accent" if c.y > 1.1 else "Base"), 1)
    P.obj("Crown", ball((0, 1.12, 1.42), (0.1, 0.13, 0.05), 10, 5), "Glass")
    P.obj("Beak", pipe([(0, 1.24, 1.28), (0, 1.55, 1.22), (0, 1.88, 1.12)], [0.06, 0.035, 0.0], 8), "Trim")
    P.obj("BeakLine", pipe([(0, 1.25, 1.255), (0, 1.75, 1.15)], [0.012, 0.008], 4), "Accent")
    for s in (1, -1):
        P.obj("Eye", ball((s * 0.115, 1.17, 1.33), (0.035, 0.04, 0.035), 8, 4), "Lamp")
        P.obj("Pupil", ball((s * 0.13, 1.19, 1.33), (0.012, 0.015, 0.025), 6, 3), "Dark")
        P.obj("Brow", hull([(s * 0.04, 1.24, 1.39), (s * 0.17, 1.13, 1.4), (s * 0.17, 1.12, 1.37), (s * 0.05, 1.22, 1.36), (s * 0.12, 1.2, 1.41)]), "Dark", 0, False)
    # the golden circlet and crescent maedate
    P.obj("Circlet", xf(torus(0.155, 0.022, 0.0, 20, 5), Matrix.Rotation(math.radians(-18), 3, "X"), (0, 1.07, 1.36)), "Trim")
    arc = [Vector((math.sin(t) * 0.24, 1.2, 1.5 + math.cos(t) * 0.24 - 0.18)) for t in [math.radians(-75 + 150 * i / 14) for i in range(15)]]
    P.obj("Maedate", pipe(arc, [0.0] + [0.04 * math.sin(math.pi * i / 14) + 0.008 for i in range(1, 14)] + [0.0], 6), "Trim")
    P.obj("MaedateGem", ball((0, 1.2, 1.39), (0.035, 0.02, 0.035), 8, 4), "Lamp")
    # a crest of three long plumes trailing back from her head
    for k in (-1, 0, 1):
        P.obj("Crest", slab(plume((k * 0.04, 1.0, 1.4), (k * 0.25, 0.45, 1.7 - abs(k) * 0.12), (1, 0, 0) if k == 0 else (1, 0, 0.3 * k), 0.06, 0.08)), "Base", 0, False)
    big = Matrix.Translation((0, 1.0, 1.2)) @ Matrix.Scale(1.6, 4) @ Matrix.Translation((0, -1.0, -1.2))
    for ob in P.parts[n_head:]: ob.data.transform(big)
    # the wings, raised high in display: coverts, secondaries and a fan of black-dipped primaries; they beat about the shoulder
    for s in (1, -1):
        name = "FlapR" if s > 0 else "FlapL"
        hub = Vector((s * 0.36, 0.05, 0.3))
        D = Vector((s * 1.0, 0.0, 0.42)).normalized()           # out along the arm, raised
        U = Vector((0.0, -0.55, 1.0)).normalized()              # up and back: the way the feathers lie
        U = (U - D * U.dot(D)).normalized()
        N = D.cross(U).normalized()
        if N.y < 0: N = -N                                        # the face of the wing turned toward the player
        span = 2.2
        def fpaint(root, d, black):
            def f(c, n, root=root, d=d, black=black):
                u = (c - root).dot(d) / d.length_squared
                if black and u > 0.62: return "Accent"
                return "Base"
            return f
        # the arm: a white leading edge with a glowing gold rim and beads
        lead = [hub + D * (span * i / 8) + U * (-0.06 + 0.12 * math.sin(math.pi * i / 8)) for i in range(9)]
        P.part(name, pipe(lead, [0.12, 0.11, 0.1, 0.09, 0.08, 0.07, 0.06, 0.05, 0.03], 8), "Base", tuple(hub), 0)
        P.part(name, pipe([p + N * 0.05 - U * 0.08 for p in lead], [0.022] * 8 + [0.01], 5), "Trim", tuple(hub))
        for i in (2, 4, 6):
            P.part(name, ball(tuple(lead[i] + N * 0.07 - U * 0.08), (0.045, 0.045, 0.045), 6, 3), "Lamp", tuple(hub))
        # coverts: short soft feathers along the arm
        for i in range(10):
            t = (i + 0.5) / 10
            root = hub + D * (span * 0.92 * t) + N * 0.02
            tip = root + U * (0.42 - 0.12 * t) - D * 0.05
            P.part(name, slab(plume(root, tip, N, 0.12 - 0.03 * t)), "Base", tuple(hub), 0, False)
        # secondaries: long white feathers behind them, the inner ones tipped in black
        for i in range(9):
            t = (i + 0.3) / 9
            root = hub + D * (span * 0.78 * t) + U * 0.2 - N * 0.015
            L = 0.95 + 0.15 * math.sin(math.pi * t)
            tip = root + U * L - D * 0.12 * (1 - t)
            d = tip - root
            P.part(name, slab(plume(root, tip, N, 0.15)), fpaint(root, d, i < 4), tuple(hub), 0, False)
        # primaries: a fan at the tip of the wing, black dipped, edged in glowing gold
        wt = hub + D * span * 0.82 + U * 0.15
        for k in range(7):
            a = math.radians(-8 + 15 * k)                            # from straight out along the arm to up along the feathers
            dirv = (D * math.cos(a) + U * math.sin(a)).normalized()
            L = 1.05 - 0.05 * abs(k - 2)
            root = wt + dirv * 0.05 - N * 0.03 * k
            tip = root + dirv * L
            d = tip - root
            P.part(name, slab(plume(root, tip, N, 0.12, 0.05)), fpaint(root, d, True), tuple(hub), 0, False)
            P.part(name, pipe([root + d * 0.62 + N * 0.03, tip + N * 0.03], [0.014, 0.004], 4), "Lamp", tuple(hub))
    # the tail bustle: black plumes over white tail feathers
    for k in range(7):
        a = math.radians(-36 + 12 * k)
        root = Vector((math.sin(a) * 0.12, -0.7, 0.08))
        tip = root + Vector((math.sin(a) * 0.55, -0.95, -0.12 - 0.06 * abs(k - 3)))
        P.obj("TailFeather", slab(plume(root, tip, (0, 0.15, 1), 0.11)), "Base", 0, False)
    for k in range(5):
        a = math.radians(-30 + 15 * k)
        root = Vector((math.sin(a) * 0.1, -0.55, 0.22))
        tip = root + Vector((math.sin(a) * 0.45, -0.75, 0.05 + 0.08 * (k % 2)))
        P.obj("Bustle", slab(plume(root, tip, (0, 0.2, 1), 0.1, 0.12)), "Accent", 0, False)
    # the legs trailing behind, golden talons clutching a glowing pearl
    for s in (1, -1):
        knee = Vector((s * 0.14, -0.55, -0.42)); foot = Vector((s * 0.1, -1.25, -0.55))
        P.obj("Leg", pipe([(s * 0.16, -0.25, -0.25), knee, foot], [0.045, 0.035, 0.028], 6), "Accent")
        for k in (-1, 0, 1):
            P.obj("Talon", pipe(bez(foot, foot + Vector((k * 0.07, -0.08, -0.03)), foot + Vector((k * 0.1, -0.16, -0.1)), foot + Vector((k * 0.06 - s * 0.04, -0.18, -0.18)), 3), [0.02, 0.018, 0.012, 0.0], 5), "Trim")
    P.obj("Pearl", ball((0, -1.38, -0.68), (0.12, 0.12, 0.12), 12, 6), "Lamp")
    P.obj("PearlHalo", xf(torus(0.18, 0.012, 0.0, 20, 4), Matrix.Rotation(math.radians(90), 3, "X"), (0, -1.38, -0.68)), "Trim")
    # red silk ribbons streaming from her neck, gold tassels at their ends; each sways
    for s, k in ((1, 0), (-1, 1)):
        base = Vector((s * 0.14, 0.62, 0.62))
        path = bez(base, base + Vector((s * 0.35, -0.35, 0.05)), base + Vector((s * 0.15, -0.95, -0.35)), base + Vector((s * 0.5, -1.55, -0.15)), 12)
        polys = []
        for i in range(12):
            a, b = path[i], path[i + 1]
            w0 = 0.09 - 0.03 * i / 12; w1 = 0.09 - 0.03 * (i + 1) / 12
            tw0 = Vector((0, math.sin(i * 0.5) * 0.3, 1)).normalized(); tw1 = Vector((0, math.sin((i + 1) * 0.5) * 0.3, 1)).normalized()
            polys.append([tuple(a + tw0 * w0), tuple(b + tw1 * w1), tuple(b - tw1 * w1), tuple(a - tw0 * w0)])
        name = "SwayRibbon%d" % k
        P.part(name, slab(polys, 0.02), "Glass", tuple(base), 0, False)
        P.part(name, cone(path[-1], path[-1] + Vector((s * 0.06, -0.12, -0.22)), 0.06, 6), "Trim", tuple(base), 0, False)
    P.obj("NeckKnot", ball((0, 0.66, 0.62), (0.14, 0.09, 0.08), 10, 5), "Glass")
    # cherry blossoms whirling round her
    for k in range(14):
        a = 2 * math.pi * k / 14
        c = Vector((math.sin(a) * 1.9, -0.1 + math.cos(a) * 1.7, 0.45 + 0.35 * math.sin(a * 3)))
        for j in range(5):
            b = 2 * math.pi * j / 5 + a
            q = c + Vector((math.cos(b) * 0.06, 0, math.sin(b) * 0.06))
            P.part("SpinBlossoms", ball(tuple(q), (0.05, 0.015, 0.05), 6, 3), "Glow", (0, -0.1, 0.45))
        P.part("SpinBlossoms", ball(tuple(c + Vector((0, 0.01, 0))), (0.025, 0.02, 0.025), 5, 3), "Lamp", (0, -0.1, 0.45))
    mz = big @ Vector((0, 1.9, 1.11))
    P.part("Muzzle", ball(tuple(mz), (0.06, 0.04, 0.05), 8, 4), "Lamp", tuple(mz))
    return P


# ================================================================= 3. the samurai spirit
def J_samurai():
    """An empty suit of samurai armour risen as a spirit: a black lacquered helmet with golden horns, a red demon mask with burning blue
    eyes, laced red shoulder plates, a black-and-gold breastplate, a katana raised in both hands, and blue spirit flame where the legs should be."""
    P = Boss("samurai", {"Base": ((0.08, 0.08, 0.10), 0.75), "Belly": ((0.90, 0.88, 0.82), 0.4), "Accent": RED, "Trim": GOLD,
                         "Glass": ((0.80, 0.85, 0.90), 0.9), "Dark": ((0.03, 0.03, 0.04), 0.5), "Glow": ((0.40, 0.75, 1.0), 0.5),
                         "Metal": ((0.70, 0.72, 0.76), 0.85), "Lamp": ((0.55, 0.90, 1.0), 0.8)})
    lace = lambda c, n: "Trim" if (c.z * 8) % 1.0 < 0.14 else "Accent"
    P.obj("Do", lathe([(0.32, 0.0), (0.42, 0.35), (0.5, 0.75), (0.45, 0.95), (0.0, 1.0)], 18, "z"), lambda c, n: "Trim" if (c.z * 6) % 1.0 < 0.1 else "Base", 1)
    for v in P.parts[-1].data.vertices: v.co.y *= 0.7
    P.obj("Kusazuri", lathe([(0.34, 0.02), (0.55, -0.45), (0.0, -0.45)], 16, "z"), lace, 1)
    for v in P.parts[-1].data.vertices: v.co.y *= 0.75
    for s in (1, -1):
        for k in range(4):   # the layered shoulder plates
            P.obj("Sode", box((s * (0.62 + k * 0.02), 0.0, 0.88 - k * 0.15), (0.32, 0.42, 0.13), Matrix.Rotation(math.radians(-s * 18), 3, "Y")), lace, 0, False)
        sh = Vector((s * 0.5, 0.05, 0.8)); el = Vector((s * 0.6, 0.35, 0.65)); hd = Vector((s * 0.18, 0.55, 0.95))
        P.obj("Arm", pipe([sh, el, hd], [0.12, 0.1, 0.09], 8), "Base", 1)
        P.obj("Kote", pipe([el + (hd - el) * 0.2, el + (hd - el) * 0.8], [0.11, 0.1], 8), "Trim")
        P.obj("Hand", ball(tuple(hd), (0.09, 0.09, 0.09), 8, 4), "Dark")
    # the katana raised
    P.obj("Tsuka", pipe([(0, 0.55, 0.78), (0, 0.6, 1.1)], [0.04, 0.04], 6), lambda c, n: "Belly" if (c.z * 20) % 1.0 < 0.5 else "Dark")
    P.obj("Tsuba", lathe([(0.0, 1.1), (0.12, 1.1), (0.12, 1.13), (0.0, 1.13)], 12, "z", (0, 0.6, 0)), "Trim")
    P.obj("Blade", hull([(0, 0.58, 1.13), (0, 0.64, 1.13), (0.012, 0.6, 1.13), (-0.012, 0.6, 1.13), (0, 0.85, 2.35), (0, 0.8, 2.4), (0, 0.86, 2.28)]), "Metal", 0, False)
    # the helmet and the mask
    P.obj("Kabuto", ball((0, 0.05, 1.42), (0.3, 0.3, 0.26), 14, 7), "Base", 1)
    P.obj("Shikoro", lathe([(0.28, 1.4), (0.5, 1.12), (0.46, 1.08), (0.25, 1.36)], 18, "z", (0, -0.05, 0)), lace)
    for s in (1, -1):
        P.obj("Kuwagata", pipe(bez((s * 0.08, 0.28, 1.5), (s * 0.25, 0.35, 1.7), (s * 0.45, 0.3, 1.95), (s * 0.55, 0.2, 2.15), 6), [0.05, 0.05, 0.045, 0.04, 0.035, 0.025, 0.0], 6), "Trim")
        P.obj("Eye", ball((s * 0.1, 0.3, 1.32), (0.06, 0.03, 0.03), 8, 4), "Lamp")
        P.obj("Fukigaeshi", box((s * 0.33, 0.15, 1.3), (0.06, 0.22, 0.2), Matrix.Rotation(math.radians(s * 20), 3, "Z")), "Accent", 0, False)
    P.obj("Crest", ball((0, 0.33, 1.6), (0.07, 0.03, 0.07), 8, 4), "Trim")
    P.obj("Mask", ball((0, 0.24, 1.22), (0.22, 0.12, 0.17), 12, 6), "Accent", 1)
    P.obj("MaskMouth", box((0, 0.36, 1.13), (0.16, 0.02, 0.04)), "Dark", 0, False)
    for k in range(4): P.obj("Fang", cone((-0.06 + k * 0.04, 0.37, 1.15), (-0.06 + k * 0.04, 0.38, 1.1), 0.012, 4), "Belly", 0, False)
    P.obj("Moustache", pipe(bez((-0.16, 0.34, 1.22), (-0.05, 0.37, 1.24), (0.05, 0.37, 1.24), (0.16, 0.34, 1.22), 5), [0.02] * 6, 5), "Belly")
    # spirit flame below, and wisps circling
    for k in range(7):
        a = 2 * math.pi * k / 7
        P.obj("Flame", cone((math.cos(a) * 0.25, math.sin(a) * 0.2, -0.4), (math.cos(a) * 0.12, math.sin(a) * 0.1 - 0.1, -1.15 - 0.15 * (k % 2)), 0.14, 6), "Glow", 0, False)
    P.obj("FlameCore", cone((0, 0, -0.35), (0, -0.1, -1.4), 0.22, 8), "Lamp", 0, False)
    for k in range(6):
        a = 2 * math.pi * k / 6
        P.part("SpinWisps", ball((math.cos(a) * 1.3, math.sin(a) * 1.1, 0.5 + 0.3 * math.sin(a * 2)), (0.09, 0.09, 0.12), 8, 4), "Glow", (0, 0, 0.5))
    P.part("Muzzle", ball((0, 0.4, 1.32), (0.05, 0.03, 0.04), 8, 4), "Lamp", (0, 0.4, 1.32))
    return P


# ================================================================= 4. the sky dragon
def J_dragon():
    """An eastern dragon winding through the sky: a long jade body in coils with a golden belly and a crimson mane down its back, a long head
    with golden antlers and flowing whiskers, four clawed legs, one holding a glowing pearl, and a flame tuft at the tail."""
    P = Boss("ryu", {"Base": ((0.10, 0.52, 0.34), 0.6), "Belly": ((0.96, 0.84, 0.48), 0.5), "Accent": RED, "Trim": GOLD,
                     "Glass": ((0.75, 0.95, 1.0), 0.9), "Dark": ((0.03, 0.05, 0.04), 0.6), "Glow": ((0.80, 0.95, 1.0), 0.5),
                     "Metal": ((0.6, 0.6, 0.6), 0.6), "Lamp": ((1.0, 0.85, 0.30), 0.8)})
    ctrl = [(0, 1.4, 0.75), (0, 0.9, 0.4), (0.85, 0.45, 0.25), (1.0, -0.3, 1.1), (0.0, -0.6, 1.75), (-1.0, -0.8, 1.15), (-0.85, -1.4, 0.2), (0.2, -1.8, -0.05), (0.8, -2.2, 0.5)]
    sp = spline(ctrl, 5); N = len(sp)
    rad = [0.26 * (1 - 0.75 * (i / (N - 1)) ** 1.4) + 0.03 for i in range(N)]
    P.obj("Body", pipe(sp, rad, 14), lambda c, n: "Belly" if n.z < -0.35 else ("Trim" if speckle(c, 2.0) < 0.05 else "Base"), 0)
    for i in range(1, N - 2, 2):   # the crimson mane
        p = sp[i]; t = (sp[i + 1] - sp[i - 1]).normalized()
        side = t.cross(Vector((0, 0, 1))); side = side.normalized() if side.length > 1e-3 else Vector((1, 0, 0))
        up = side.cross(t).normalized()
        if up.z < 0: up = -up
        P.obj("Mane", cone(p + up * rad[i] * 0.8, p + up * (rad[i] + 0.22) - t * 0.15, 0.06, 5), "Accent", 0, False)
    tp = sp[-1]
    for k in range(5):
        a = math.radians(-40 + k * 20)
        P.obj("TailFlame", cone(tp, tp + Vector((math.sin(a) * 0.25, -0.35, 0.15 + 0.1 * math.cos(a))), 0.07, 5), "Accent", 0, False)
    # the head
    HC = Vector((0, 1.4, 0.75)); HK = 1.25
    def H(bm): return grow(bm, HC, HK)
    P.obj("Head", H(loft([(1.3, 0.2, 0.2, 0, 0.78), (1.55, 0.22, 0.18, 0, 0.82), (1.85, 0.17, 0.12, 0, 0.8), (2.1, 0.12, 0.08, 0, 0.76), (2.22, 0.08, 0.06, 0, 0.74)], 14)),
          lambda c, n: "Belly" if n.z < -0.4 else "Base", 1)
    P.obj("Jaw", H(loft([(1.45, 0.16, 0.06, 0, 0.62), (1.85, 0.13, 0.05, 0, 0.58), (2.1, 0.06, 0.03, 0, 0.56)], 12)), "Belly", 1)
    P.obj("Nose", H(ball((0, 2.2, 0.8), (0.1, 0.06, 0.06), 8, 4)), "Accent")
    for s in (1, -1):
        P.obj("Eye", H(ball((s * 0.15, 1.65, 0.9), (0.05, 0.07, 0.045), 8, 4)), "Lamp")
        P.obj("Brow", H(cone((s * 0.12, 1.55, 0.95), (s * 0.22, 1.35, 1.05), 0.05, 5)), "Accent", 0, False)
        ant = bez((s * 0.1, 1.45, 0.95), (s * 0.18, 1.25, 1.2), (s * 0.3, 1.0, 1.35), (s * 0.38, 0.85, 1.5), 6)
        P.obj("Antler", H(pipe(ant, [0.05, 0.045, 0.04, 0.035, 0.03, 0.02, 0.0], 6)), "Trim")
        for k in (2, 4): P.obj("Tine", H(cone(ant[k], ant[k] + Vector((s * 0.08, 0.1, 0.14)), 0.02, 4)), "Trim", 0, False)
        whisk = bez((s * 0.1, 2.15, 0.76), (s * 0.45, 2.25, 0.8), (s * 0.85, 1.95, 0.65), (s * 1.05, 1.5, 0.75), 10)
        P.obj("Whisker", H(pipe(whisk, [0.02] * 10 + [0.0], 5)), "Trim")
        P.obj("Beard", H(cone((s * 0.06, 1.8, 0.56), (s * 0.08, 1.75, 0.35), 0.04, 5)), "Belly", 0, False)
        for k in range(3):
            P.obj("Tooth", H(cone((s * (0.12 - 0.03 * k), 1.8 + 0.12 * k, 0.7), (s * (0.12 - 0.03 * k), 1.82 + 0.12 * k, 0.63), 0.018, 4)), "Belly", 0, False)
    # four legs with claws, the front right one holding the pearl
    for (idx, s, lift) in ((4, 1, True), (4, -1, False), (N - 14, 1, False), (N - 14, -1, False)):
        p = sp[idx]
        hip = p + Vector((s * rad[idx] * 0.7, 0, -rad[idx] * 0.3))
        foot = hip + Vector((s * 0.25, 0.3 if lift else 0.1, 0.15 if lift else -0.35))
        P.obj("Leg", pipe([hip, hip + (foot - hip) * 0.5 + Vector((0, 0, 0.05)), foot], [0.07, 0.055, 0.04], 8), "Base")
        for k in (-1, 0, 1): P.obj("Claw", cone(foot, foot + Vector((s * 0.04 + k * 0.05, 0.1, -0.06)), 0.02, 4), "Trim", 0, False)
        if lift: P.obj("Pearl", ball(tuple(foot + Vector((s * 0.02, 0.12, 0.05))), (0.13, 0.13, 0.13), 12, 6), "Glow")
    mz = HC + (Vector((0, 2.25, 0.7)) - HC) * HK
    P.part("Muzzle", ball(tuple(mz), (0.06, 0.04, 0.05), 8, 4), "Glow", tuple(mz))
    return P


# ================================================================= 5. the pagoda isle
def J_isle():
    """The last boss: a floating island - a grassy top on a rocky root with a waterfall spilling from its edge, a five-tiered red pagoda with
    sweeping teal roofs and a golden spire, two cherry trees in bloom, a red torii gate at the front, glowing stone lanterns, and a ring of
    cherry petals turning round it."""
    P = Boss("isle", {"Base": ((0.15, 0.32, 0.34), 0.5), "Belly": ((0.55, 0.50, 0.46), 0.3), "Accent": RED, "Trim": GOLD,
                      "Glass": SAKURA, "Dark": ((0.10, 0.07, 0.06), 0.4), "Glow": ((0.55, 0.85, 1.0), 0.5),
                      "Metal": ((0.30, 0.55, 0.22), 0.35), "Lamp": ((1.0, 0.82, 0.45), 0.8)})
    rng = random.Random(9)
    P.obj("Ground", lathe([(0.0, 0.1), (1.8, 0.1), (1.9, 0.0), (1.85, -0.1)], 28, "z"), lambda c, n: "Metal" if n.z > 0.5 else "Belly")
    root = []
    for k in range(36):
        a = rng.uniform(0, 2 * math.pi); r = rng.uniform(0.2, 1.85)
        root.append((math.sin(a) * r, math.cos(a) * r, -0.1 - (1.85 - r) * rng.uniform(0.5, 0.8)))
    root += [(math.sin(2 * math.pi * k / 16) * 1.85, math.cos(2 * math.pi * k / 16) * 1.85, -0.08) for k in range(16)] + [(0, 0, -1.4)]
    P.obj("Root", hull(root), "Belly", 0, False)
    # the pagoda
    pc = Vector((0, -0.35, 0.1))
    for k in range(5):
        w = 0.6 - k * 0.08; z = pc.z + 0.1 + k * 0.42
        P.obj("Storey", box((pc.x, pc.y, z + 0.14), (w * 1.2, w * 1.2, 0.28)), lambda c, n: "Accent" if abs(n.z) < 0.5 and (abs(c.x) * 6) % 1.0 > 0.25 else "Belly", 0, False)
        P.obj("Roof", roof((pc.x, pc.y, z + 0.3), w + 0.25, w + 0.25, 0.12, 0.1), lambda c, n: "Base" if n.z > -0.3 else "Dark", 0, False)
        for sx in (-1, 1):
            for sy in (-1, 1):
                P.obj("Bell", ball((pc.x + sx * (w + 0.24), pc.y + sy * (w + 0.24), z + 0.36), (0.035, 0.035, 0.035), 6, 3), "Trim")
        P.obj("Window", box((pc.x, pc.y + w * 0.6 + 0.01, z + 0.14), (0.16, 0.02, 0.12)), "Lamp", 0, False)
    P.obj("Spire", pipe([(pc.x, pc.y, pc.z + 2.2), (pc.x, pc.y, pc.z + 2.85)], [0.04, 0.02], 6), "Trim")
    for k in range(5): P.obj("SpireRing", torus(0.07, 0.015, pc.z + 2.3 + k * 0.1, 10, 4), "Trim")
    # cherry trees in bloom
    for s in (1, -1):
        tc = Vector((s * 1.1, 0.1, 0.1))
        P.obj("Trunk", pipe(bez(tc, tc + Vector((s * 0.1, 0, 0.4)), tc + Vector((s * 0.05, 0.05, 0.7)), tc + Vector((s * 0.2, 0.0, 0.9)), 4), [0.08, 0.07, 0.06, 0.05, 0.04], 6), "Dark")
        for k in range(6):
            a = k * 2.4
            P.obj("Blossom", ball(tuple(tc + Vector((s * 0.15 + math.cos(a) * 0.32, math.sin(a) * 0.28, 1.0 + 0.12 * math.sin(a * 2)))), (0.3, 0.28, 0.24), 10, 5), "Glass", 1)
    # the torii at the front, lanterns
    for s in (1, -1):
        P.obj("Pillar", pipe([(s * 0.45, 1.35, 0.1), (s * 0.42, 1.35, 1.05)], [0.06, 0.055], 8), "Accent")
        P.obj("StoneLantern", lathe([(0.1, 0.1), (0.06, 0.3), (0.12, 0.32), (0.1, 0.45), (0.15, 0.47), (0.0, 0.58)], 8, "z", (s * 0.85, 1.25, 0)), lambda c, n: "Lamp" if 0.33 < c.z < 0.45 else "Belly")
    P.obj("Kasagi", hull([(-0.72, 1.35, 1.12), (0.72, 1.35, 1.12), (-0.62, 1.35, 1.02), (0.62, 1.35, 1.02), (-0.8, 1.3, 1.18), (0.8, 1.3, 1.18), (-0.8, 1.4, 1.18), (0.8, 1.4, 1.18)]), "Dark", 0, False)
    P.obj("Nuki", box((0, 1.35, 0.85), (1.1, 0.06, 0.08)), "Accent", 0, False)
    P.obj("Kasagi2", box((0, 1.35, 1.05), (1.25, 0.1, 0.08)), "Accent", 0, False)
    for k in range(14):   # the ring of cherry petals
        a = 2 * math.pi * k / 14
        c = Vector((math.cos(a) * 2.3, math.sin(a) * 2.2, 0.6 + 0.4 * math.sin(a * 3)))
        P.part("SpinPetals", sheet([[tuple(c + Vector((0.12, 0, 0))), tuple(c + Vector((0, 0.07, 0.04))), tuple(c + Vector((-0.12, 0, 0))), tuple(c + Vector((0, -0.07, -0.04)))]], 0.015),
               "Glass", (0, 0, 0.6), 0, False)
    P.part("Muzzle", ball((pc.x, pc.y + 0.62, pc.z + 1.0), (0.07, 0.03, 0.07), 8, 4), "Lamp", (pc.x, pc.y + 0.62, pc.z + 1.0))
    return P


# ================================================================= 2026-10-11 round two: the tengu lord, the golden fortune cat, raijin
# ("new bosses with a new shape, with a face, grand, that suit the world": they stand in for the koi streamer, the snow crane and the pagoda isle)
def feather(root, tip, w, up=(0, 0, 1)):
    """a flat feather from root to tip, w wide, lying in the plane its width and the up vector span."""
    root = Vector(root); tip = Vector(tip); d = tip - root
    side = d.cross(Vector(up)); side = side.normalized() * w if side.length > 1e-4 else Vector((w, 0, 0))
    m1 = root + d * 0.35; m2 = root + d * 0.75
    return sheet([[tuple(root), tuple(m1 + side), tuple(m2 + side * 0.7), tuple(tip), tuple(m2 - side * 0.7), tuple(m1 - side)]], 0.03)

def zigzag(p0, p1, n, amp, rng):
    p0 = Vector(p0); p1 = Vector(p1); pts = []
    for i in range(n + 1):
        q = p0 + (p1 - p0) * (i / n)
        if 0 < i < n: q += Vector((rng.uniform(-amp, amp), rng.uniform(-amp * 0.4, amp * 0.4), 0))
        pts.append(q)
    return pts

def at(ob, t, m=None):
    """moves a just-made object's mesh: m (4x4) first, then to t."""
    M = Matrix.Translation(t) @ (m if m is not None else Matrix.Identity(4))
    ob.data.transform(M)
    return ob


# ================================================================= 6. the tengu lord (stands in for the koi streamer)
def J_tengu():
    """The TENGU LORD, king of the mountain spirits: a crimson face with a great long nose, white brows knitted in anger, golden eyes, a
    flowing white mane and beard, the little black tokin cap of the mountain monks, indigo robes with gold bands and pompoms, huge black
    feathered wings that beat, a feather fan in one hand and a golden ringed staff in the other."""
    P = Boss("tengu", {"Base": ((0.80, 0.10, 0.07), 0.45), "Belly": ((0.96, 0.95, 0.92), 0.35), "Accent": ((0.05, 0.05, 0.07), 0.55),
                       "Trim": GOLD, "Glass": ((1.0, 0.78, 0.15), 0.8), "Dark": ((0.02, 0.02, 0.03), 0.4), "Glow": ((0.70, 0.90, 1.0), 0.5),
                       "Metal": ((0.16, 0.18, 0.46), 0.45), "Lamp": ((1.0, 0.85, 0.40), 0.8)})
    band = lambda c, n: "Trim" if (c.z * 3.2) % 1.0 < 0.12 else "Metal"
    # the robes, flaring into a trailing bell
    P.obj("Robe", lathe([(0.0, -1.35), (0.62, -1.3), (0.55, -0.9), (0.42, -0.3), (0.38, 0.2), (0.34, 0.55), (0.0, 0.62)], 18, "z", (0, -0.05, 0)), band, 1)
    for v in P.parts[-1].data.vertices: v.co.y *= 0.8
    P.obj("Collar", torus(0.3, 0.07, 0.56, 18, 6), "Belly")
    P.obj("Sash", torus(0.4, 0.06, -0.2, 18, 6), "Trim")
    for k in range(6):   # the yamabushi pompoms down the chest
        z = 0.45 - k * 0.16; x = 0.12 if k % 2 else -0.12
        P.obj("Pompom", ball((x, 0.33 - k * 0.012, z), (0.07, 0.06, 0.07), 8, 4), "Belly" if k % 2 else "Trim")
    # the head (built life size, then grown so the face reads from afar)
    n0 = len(P.parts)
    HC = Vector((0, 0.1, 1.0))
    P.obj("Head", ball(tuple(HC), (0.3, 0.3, 0.34), 16, 8), "Base", 1)
    P.obj("Nose", pipe([(0, 0.35, 1.02), (0, 0.65, 1.08), (0, 0.95, 1.16), (0, 1.12, 1.2)], [0.1, 0.075, 0.05, 0.0], 10), "Base")
    P.obj("Nostril", ball((0, 0.43, 0.93), (0.1, 0.06, 0.05), 8, 4), "Base")
    for s in (1, -1):
        P.obj("EyeWhite", ball((s * 0.13, 0.34, 1.08), (0.075, 0.04, 0.06), 10, 5), "Belly")
        P.obj("Iris", ball((s * 0.13, 0.375, 1.075), (0.045, 0.02, 0.045), 8, 4), "Glass")
        P.obj("Pupil", ball((s * 0.13, 0.392, 1.075), (0.018, 0.01, 0.022), 6, 3), "Dark")
        # brows knitted down to the nose, thick and white
        P.obj("Brow", pipe([(s * 0.04, 0.37, 1.14), (s * 0.14, 0.36, 1.2), (s * 0.27, 0.3, 1.27), (s * 0.36, 0.2, 1.33)], [0.05, 0.06, 0.05, 0.0], 8), "Belly")
        P.obj("Cheek", ball((s * 0.18, 0.3, 0.92), (0.1, 0.06, 0.07), 8, 4), "Base")
        P.obj("Ear", ball((s * 0.3, 0.05, 1.02), (0.05, 0.08, 0.12), 8, 4), "Base")
        for k in range(5):   # the mane sweeping back and out
            a = math.radians(-50 + k * 25)
            P.obj("Mane", cone((s * 0.22, -0.05, 1.05 + math.sin(a) * 0.2), (s * (0.55 + 0.1 * math.cos(a)), -0.45, 0.95 + math.sin(a) * 0.5), 0.12, 6), "Belly", 0, False)
    P.obj("Mouth", box((0, 0.3, 0.84), (0.2, 0.04, 0.035)), "Dark", 0, False)
    for s in (1, -1): P.obj("Fang", cone((s * 0.07, 0.32, 0.84), (s * 0.075, 0.33, 0.77), 0.022, 4), "Belly", 0, False)
    for k in range(7):   # the beard
        x = -0.18 + k * 0.06
        P.obj("Beard", cone((x, 0.22 - abs(x) * 0.3, 0.86), (x * 1.3, 0.25, 0.42 - 0.08 * (3 - abs(k - 3))), 0.06, 6), "Belly", 0, False)
    P.obj("BackHair", ball((0, -0.12, 1.05), (0.3, 0.25, 0.35), 12, 6), "Belly", 1)
    # the tokin cap
    P.obj("Tokin", hull([(math.cos(2 * math.pi * k / 6) * 0.11, 0.18 + math.sin(2 * math.pi * k / 6) * 0.11, 1.3) for k in range(6)] + [(0, 0.2, 1.45)]), "Accent", 0, False)
    for s in (1, -1): P.obj("TokinCord", pipe([(s * 0.1, 0.2, 1.3), (s * 0.28, 0.12, 1.12), (s * 0.3, 0.0, 0.9)], [0.015] * 3, 5), "Trim")
    G = Matrix.Translation((0, 0.12, 0.62)) @ Matrix.Scale(1.45, 4) @ Matrix.Translation((0, -0.12, -0.62))
    for ob in P.parts[n0:]: ob.data.transform(G)
    # the arms: a feather fan on the right, a ringed staff on the left
    for s in (1, -1):
        sh = Vector((s * 0.36, 0.0, 0.45)); el = Vector((s * 0.7, 0.2, 0.2)); hd = Vector((s * 0.8, 0.45, 0.45))
        P.obj("Sleeve", pipe([sh, el, hd - (hd - el) * 0.25], [0.15, 0.17, 0.19], 10), "Metal", 1)
        at(P.obj("Cuff", torus(0.17, 0.03, 0.0, 12, 4), "Trim"), tuple(hd - (hd - el) * 0.25), Matrix.Rotation(math.radians(70), 4, "X"))
        P.obj("Hand", ball(tuple(hd), (0.09, 0.09, 0.09), 8, 4), "Base")
    hd = Vector((0.8, 0.45, 0.45))
    P.obj("FanHandle", pipe([hd + Vector((0, 0, -0.1)), hd + Vector((0.05, 0.05, 0.35))], [0.03, 0.03], 6), "Trim")
    fc = hd + Vector((0.05, 0.08, 0.38))
    for k in range(9):
        a = math.radians(-60 + k * 15)
        P.obj("Fan", feather(fc, fc + Vector((math.sin(a) * 0.6, 0.06, math.cos(a) * 0.6)), 0.09, (0, 1, 0)), "Belly" if k % 2 else "Trim", 0, False)
    hd = Vector((-0.8, 0.45, 0.45))
    P.obj("Staff", pipe([hd + Vector((0, 0, -0.9)), hd + Vector((0, 0, 1.0))], [0.03, 0.03], 6), "Trim")
    at(P.obj("StaffHead", torus(0.16, 0.025, 0.0, 16, 4), "Trim"), tuple(hd + Vector((0, 0, 1.15))), Matrix.Rotation(math.radians(90), 4, "X"))
    for k in range(4):
        a = math.radians(-60 + k * 40)
        at(P.obj("StaffRing", torus(0.06, 0.012, 0.0, 10, 4), "Trim"), tuple(hd + Vector((math.sin(a) * 0.17, 0, 1.15 + math.cos(a) * 0.17 - 0.05))), Matrix.Rotation(math.radians(90), 4, "X"))
    # the great black wings, gold at the coverts
    for s in (1, -1):
        name = "FlapR" if s > 0 else "FlapL"
        hub = Vector((s * 0.25, -0.25, 0.55))
        P.part(name, ball(tuple(hub + Vector((s * 0.35, -0.05, 0.15))), (0.4, 0.12, 0.25), 10, 5), "Accent", tuple(hub))
        for row, (L, n, z0, w, col) in enumerate(((1.75, 8, 0.0, 0.26, "Accent"), (1.2, 7, 0.06, 0.24, "Dark"), (0.7, 6, 0.12, 0.2, "Trim"))):
            for k in range(n):
                a = math.radians(-5 + k * (95.0 / (n - 1)))
                root = hub + Vector((s * (0.15 + row * 0.05), -0.12 - row * 0.03 - 0.02 * k, 0.1 + z0))
                tip = root + Vector((s * math.cos(a) * L, -0.2 - 0.05 * k, math.sin(a) * L * 0.85))
                P.part(name, feather(root, tip, w, (0, 1, 0)), col, tuple(hub), 0, False)
            if row == 0:   # a gold edge to the long feathers' tips
                for k in range(n):
                    a = math.radians(-5 + k * (95.0 / (n - 1)))
                    root = hub + Vector((s * 0.15, -0.14 - 0.02 * k - 0.005, 0.1))
                    tip = root + Vector((s * math.cos(a) * L, -0.2 - 0.05 * k, math.sin(a) * L * 0.85))
                    P.part(name, feather(root + (tip - root) * 0.82, tip + (tip - root) * 0.02, w * 0.55, (0, 1, 0)), "Trim", tuple(hub), 0, False)
    rng = random.Random(5)
    for k in range(9):   # a cloud of mountain mist he rides, puffs drifting round
        a = 2 * math.pi * k / 9; r = rng.uniform(0.45, 0.75)
        P.obj("Mist", ball((math.cos(a) * r, math.sin(a) * r * 0.8, -1.25 + rng.uniform(-0.06, 0.06)), (0.34, 0.3, 0.2), 10, 5), "Belly", 1)
    for k in range(6):
        a = 2 * math.pi * k / 6
        P.part("SpinWind", ball((math.cos(a) * 0.95, math.sin(a) * 0.8, -1.15 + 0.1 * math.sin(a * 2)), (0.24, 0.2, 0.14), 10, 5), "Belly", (0, 0, -1.15), 1)
    P.part("Muzzle", ball((0, 1.14, 1.2), (0.05, 0.03, 0.04), 8, 4), "Lamp", (0, 1.14, 1.2))
    return P


# ================================================================= 7. the golden fortune cat (stands in for the snow crane)
def J_neko():
    """The GOLDEN FORTUNE CAT: a giant maneki-neko of white porcelain with calico patches, great golden eyes, a pink nose, whiskers and a
    happy grin, a red collar with a golden bell, a golden koban coin hugged to its chest, its raised paw beckoning, on a purple-and-gold
    cushion riding a cloud, with gold coins circling."""
    P = Boss("neko", {"Base": ((0.98, 0.55, 0.12), 0.5), "Belly": ((0.99, 0.98, 0.96), 0.75), "Accent": RED, "Trim": GOLD,
                      "Glass": ((1.0, 0.78, 0.10), 0.95), "Dark": ((0.03, 0.03, 0.04), 0.6), "Glow": ((1.0, 0.55, 0.65), 0.5),
                      "Metal": ((0.40, 0.10, 0.42), 0.45), "Lamp": ((1.0, 0.90, 0.60), 0.8)})
    calico = lambda c, n: ("Base" if (c - Vector((0.25, -0.1, 0.3))).length < 0.28 or (c - Vector((-0.3, -0.2, -0.1))).length < 0.24 else
                           ("Trim" if (c - Vector((-0.1, -0.35, 0.45))).length < 0.18 else "Belly"))
    P.obj("Body", ball((0, -0.05, 0.05), (0.62, 0.55, 0.62), 18, 9), calico, 1)
    P.obj("Haunch", ball((0, -0.05, -0.35), (0.7, 0.6, 0.35), 16, 8), "Belly", 1)
    for s in (1, -1): P.obj("Foot", ball((s * 0.3, 0.42, -0.55), (0.18, 0.16, 0.12), 10, 5), "Belly", 1)
    # the head
    HC = Vector((0, 0.1, 0.95))
    P.obj("Head", ball(tuple(HC), (0.6, 0.5, 0.48), 18, 9), lambda c, n: "Base" if c.z > 1.2 and c.x > 0.12 and c.y < 0.45 else "Belly", 1)
    for s in (1, -1):
        P.obj("Ear", cone((s * 0.35, 0.05, 1.25), (s * 0.5, 0.05, 1.68), 0.18, 8), "Belly" if s < 0 else "Base", 0, False)
        P.obj("EarIn", cone((s * 0.35, 0.12, 1.28), (s * 0.48, 0.12, 1.6), 0.11, 8), "Glow", 0, False)
        P.obj("EyeRim", ball((s * 0.22, 0.5, 1.02), (0.15, 0.06, 0.15), 12, 6), "Dark")
        P.obj("Eye", ball((s * 0.22, 0.53, 1.02), (0.13, 0.05, 0.13), 12, 6), "Glass")
        P.obj("Pupil", ball((s * 0.22, 0.575, 1.02), (0.035, 0.02, 0.1), 8, 4), "Dark")
        P.obj("Shine", ball((s * 0.22 + 0.05, 0.585, 1.08), (0.03, 0.01, 0.03), 6, 3), "Lamp")
        P.obj("Blush", ball((s * 0.36, 0.4, 0.86), (0.1, 0.03, 0.06), 8, 4), "Glow")
        for k in range(3):   # whiskers
            P.obj("Whisker", pipe([(s * 0.25, 0.55, 0.81 + k * 0.05), (s * 0.55, 0.55, 0.8 + k * 0.08), (s * 0.85, 0.45, 0.78 + k * 0.12)], [0.012, 0.01, 0.0], 4), "Dark")
        P.obj("Brow", pipe([(s * 0.12, 0.49, 1.2), (s * 0.22, 0.5, 1.24), (s * 0.32, 0.47, 1.21)], [0.025, 0.03, 0.0], 5), "Trim")
    P.obj("Snout", ball((0, 0.5, 0.86), (0.2, 0.08, 0.1), 10, 5), "Belly", 1)
    P.obj("Nose", ball((0, 0.6, 0.93), (0.055, 0.03, 0.04), 8, 4), "Glow")
    P.obj("Grin", pipe(bez((-0.15, 0.56, 0.85), (-0.07, 0.6, 0.76), (0.07, 0.6, 0.76), (0.15, 0.56, 0.85), 8), [0.016] * 9, 5), "Dark")
    P.obj("Mouth", ball((0, 0.565, 0.79), (0.07, 0.02, 0.04), 8, 4), "Accent")
    # the collar, bell and the koban
    P.obj("Collar", torus(0.48, 0.06, 0.55, 22, 6), "Accent")
    P.obj("Bell", ball((0, 0.55, 0.42), (0.11, 0.1, 0.11), 12, 6), "Trim")
    P.obj("BellSlot", box((0, 0.65, 0.4), (0.1, 0.01, 0.015)), "Dark", 0, False)
    P.obj("Koban", ball((0.12, 0.55, 0.05), (0.2, 0.05, 0.3), 14, 7), lambda c, n: "Dark" if abs(n.y) > 0.8 and abs(c.x - 0.12) < 0.06 and 0.0 < c.z < 0.2 else "Glass")
    at(P.obj("KobanRim", torus(0.2, 0.02, 0.0, 18, 4), "Trim"), (0.12, 0.6, 0.05), Matrix.Rotation(math.radians(90), 4, "X") @ Matrix.Diagonal((1.0, 1.5, 1.0, 1.0)))
    P.obj("HugPaw", ball((-0.12, 0.55, 0.0), (0.15, 0.13, 0.13), 10, 5), "Belly", 1)
    # the beckoning paw (sways about the wing axis)
    hub = Vector((0.45, 0.15, 0.5))
    P.obj("Shoulder", ball(tuple(hub), (0.24, 0.24, 0.24), 10, 5), "Belly", 1)
    pw = Vector((0.82, 0.32, 1.12))
    for k in range(1, 6):   # the arm, a chain of round porcelain up to the paw
        t = k / 6.0
        q = hub + (pw - hub) * t + Vector((0.08 * math.sin(math.pi * t), 0, 0))
        P.part("SwayPaw", ball(tuple(q), (0.19, 0.18, 0.19), 10, 5), "Belly", tuple(hub), 1)
    P.part("SwayPaw", ball(tuple(pw), (0.22, 0.18, 0.21), 12, 6), "Belly", tuple(hub), 1)
    for k in range(3): P.part("SwayPaw", ball(tuple(pw + Vector((-0.1 + k * 0.1, 0.17, 0.1))), (0.045, 0.02, 0.045), 6, 3), "Glow", tuple(hub))
    P.part("SwayPaw", ball(tuple(pw + Vector((0, 0.18, -0.04))), (0.08, 0.02, 0.07), 6, 3), "Glow", tuple(hub))
    # the tail curling up behind
    P.obj("Tail", pipe(bez((0, -0.55, -0.2), (0.3, -0.85, -0.1), (0.4, -0.8, 0.4), (0.15, -0.65, 0.7), 8), [0.1, 0.1, 0.1, 0.1, 0.09, 0.08, 0.07, 0.06, 0.05], 8), lambda c, n: "Base" if c.z > 0.3 else "Belly")
    # the cushion, its tassels, the cloud
    P.obj("Cushion", loft([(-0.85, 0.75, 0.12, 0, -0.68), (-0.6, 0.95, 0.18, 0, -0.68), (0.6, 0.95, 0.18, 0, -0.68), (0.85, 0.75, 0.12, 0, -0.68)], 20, sq=2.2), "Metal", 1)
    P.obj("CushionRim", torus(0.92, 0.04, -0.68, 24, 4), "Trim")
    for sx in (1, -1):
        for sy in (1, -1):
            c = Vector((sx * 0.85, sy * 0.85, -0.68))
            P.obj("Tassel", cone(c, c + Vector((sx * 0.12, sy * 0.12, -0.3)), 0.06, 6), "Trim", 0, False)
    rng = random.Random(3)
    for k in range(11):
        a = 2 * math.pi * k / 11; r = rng.uniform(0.7, 1.05)
        P.obj("Cloud", ball((math.cos(a) * r, math.sin(a) * r * 0.8, -1.0 + rng.uniform(-0.08, 0.05)), (0.42, 0.38, 0.24), 12, 6), "Belly", 1)
    for k in range(10):
        a = 2 * math.pi * k / 10
        P.part("SpinCoins", ball((math.cos(a) * 1.55, math.sin(a) * 1.35, 0.3 + 0.25 * math.sin(a * 2)), (0.13, 0.03, 0.17), 10, 5), "Glass", (0, 0, 0.3))
    P.part("Muzzle", ball((0, 0.6, 0.85), (0.05, 0.03, 0.04), 8, 4), "Lamp", (0, 0.6, 0.85))
    return P


# ================================================================= 8. raijin, the thunder god (stands in for the pagoda isle as the last boss)
def J_raijin():
    """The last boss: RAIJIN, THE THUNDER GOD, riding a black storm cloud - storm-blue skin, a fierce roaring face with burning golden eyes,
    two golden horns and a wild white mane blowing up like flame, a tiger-skin sash, golden armlets, a drumstick raised in each hand, a
    ring of eight taiko drums turning face-on behind him on a golden hoop, and lightning hanging from the cloud."""
    P = Boss("raijin", {"Base": ((0.18, 0.40, 0.72), 0.45), "Belly": ((0.97, 0.96, 0.92), 0.35), "Accent": RED, "Trim": GOLD,
                        "Glass": ((1.0, 0.80, 0.15), 0.85), "Dark": ((0.10, 0.10, 0.14), 0.35), "Glow": ((0.75, 0.90, 1.0), 0.5),
                        "Metal": ((0.55, 0.32, 0.12), 0.5), "Lamp": ((1.0, 0.78, 0.05), 0.8)})
    tiger = lambda c, n: "Dark" if math.sin(c.x * 22 + c.z * 9) > 0.55 else "Trim"
    n0 = len(P.parts)
    # the torso, muscled
    P.obj("Chest", ball((0, 0.05, 0.55), (0.48, 0.34, 0.42), 16, 8), "Base", 1)
    for s in (1, -1): P.obj("Pec", ball((s * 0.2, 0.3, 0.68), (0.2, 0.1, 0.15), 10, 5), "Base", 1)
    for k in range(3):
        for s in (1, -1): P.obj("Ab", ball((s * 0.09, 0.3, 0.38 - k * 0.12), (0.08, 0.06, 0.055), 8, 4), "Base", 1)
    P.obj("Belt", lathe([(0.38, 0.12), (0.44, 0.0), (0.46, -0.1), (0.0, -0.12)], 18, "z"), tiger)
    for v in P.parts[-1].data.vertices: v.co.y *= 0.8
    P.obj("Loin", lathe([(0.45, -0.08), (0.55, -0.45), (0.0, -0.5)], 18, "z"), tiger, 1)
    for v in P.parts[-1].data.vertices: v.co.y *= 0.85
    for s in (1, -1):
        P.obj("Thigh", pipe([(s * 0.25, 0.1, -0.35), (s * 0.5, 0.45, -0.55), (s * 0.45, 0.4, -0.95)], [0.17, 0.14, 0.11], 10), "Base", 1)
        P.obj("Anklet", torus(0.12, 0.03, -0.9, 12, 4), "Trim")
        for v in P.parts[-1].data.vertices: v.co.x += s * 0.45; v.co.y += 0.4
        P.obj("Foot", ball((s * 0.45, 0.5, -1.02), (0.11, 0.18, 0.07), 8, 4), "Base")
    # the head, roaring
    HC = Vector((0, 0.12, 1.2))
    P.obj("Head", ball(tuple(HC), (0.3, 0.28, 0.32), 16, 8), "Base", 1)
    P.obj("Jaw", ball((0, 0.22, 1.02), (0.24, 0.2, 0.14), 12, 6), "Base", 1)
    P.obj("MouthOpen", ball((0, 0.36, 1.03), (0.15, 0.06, 0.1), 10, 5), "Accent")
    P.obj("Throat", ball((0, 0.38, 1.03), (0.1, 0.04, 0.06), 8, 4), "Dark")
    for s in (1, -1):
        P.obj("Fang", cone((s * 0.1, 0.39, 1.12), (s * 0.09, 0.4, 1.02), 0.025, 4), "Belly", 0, False)
        P.obj("Tusk", cone((s * 0.11, 0.38, 0.95), (s * 0.14, 0.41, 1.07), 0.03, 4), "Belly", 0, False)
        P.obj("EyeWhite", ball((s * 0.12, 0.35, 1.27), (0.08, 0.04, 0.06), 10, 5), "Belly")
        P.obj("Eye", ball((s * 0.12, 0.38, 1.27), (0.05, 0.02, 0.05), 8, 4), "Lamp")
        P.obj("Pupil", ball((s * 0.12, 0.397, 1.27), (0.02, 0.01, 0.025), 6, 3), "Dark")
        P.obj("Brow", pipe([(s * 0.03, 0.38, 1.33), (s * 0.15, 0.38, 1.38), (s * 0.3, 0.3, 1.46)], [0.045, 0.05, 0.0], 8), "Belly")
        P.obj("Horn", pipe(bez((s * 0.13, 0.2, 1.45), (s * 0.18, 0.25, 1.65), (s * 0.3, 0.2, 1.8), (s * 0.42, 0.12, 1.85), 6), [0.07, 0.065, 0.055, 0.045, 0.03, 0.015, 0.0], 8), "Trim")
        at(P.obj("Earring", torus(0.06, 0.015, 0.0, 10, 4), "Trim"), (s * 0.3, 0.1, 1.08), Matrix.Rotation(math.radians(90), 4, "Y"))
        P.obj("Moustache", pipe(bez((s * 0.02, 0.4, 1.15), (s * 0.15, 0.42, 1.16), (s * 0.25, 0.38, 1.1), (s * 0.33, 0.32, 1.0), 6), [0.03, 0.035, 0.03, 0.025, 0.02, 0.01, 0.0], 6), "Belly")
    P.obj("Nose", ball((0, 0.4, 1.2), (0.07, 0.05, 0.06), 8, 4), "Base")
    for k in range(9):   # the white mane streaming up like flame
        a = math.radians(-80 + k * 20)
        base = HC + Vector((math.sin(a) * 0.22, -0.12, math.cos(a) * 0.22))
        P.obj("Mane", cone(tuple(base), tuple(base + Vector((math.sin(a) * 0.45, -0.3, 0.35 + math.cos(a) * 0.35))), 0.13, 6), "Belly", 0, False)
    P.obj("Beard", cone((0, 0.25, 0.95), (0, 0.32, 0.72), 0.12, 6), "Belly", 0, False)
    # the arms, each hand raising a drumstick
    for s in (1, -1):
        P.obj("Shoulder", ball((s * 0.48, 0.05, 0.75), (0.17, 0.17, 0.17), 10, 5), "Base", 1)
        sh = Vector((s * 0.5, 0.05, 0.75)); el = Vector((s * 0.95, 0.15, 0.8)); hd = Vector((s * 1.05, 0.3, 1.25))
        P.obj("Arm", pipe([sh, el, hd], [0.15, 0.12, 0.1], 10), "Base", 1)
        at(P.obj("Armlet", torus(0.13, 0.03, 0.0, 12, 4), "Trim"), tuple(sh + (el - sh) * 0.5), Matrix.Rotation(math.radians(90), 4, "Y"))
        P.obj("Fist", ball(tuple(hd), (0.11, 0.11, 0.11), 8, 4), "Base")
        P.obj("Bachi", pipe([hd + Vector((0, 0, -0.12)), hd + Vector((s * 0.2, 0.05, 0.5))], [0.035, 0.03], 6), "Metal")
        P.obj("BachiTip", ball(tuple(hd + Vector((s * 0.2, 0.05, 0.52))), (0.06, 0.06, 0.06), 6, 3), "Accent")
    # the scarf that floats in an arch over him
    arch = bez((-0.5, -0.05, 0.75), (-1.1, -0.3, 1.9), (1.1, -0.3, 1.9), (0.5, -0.05, 0.75), 16)
    P.obj("Scarf", pipe(arch, [0.06] * 17, 6), "Accent")
    G = Matrix.Translation((0, 0.1, -0.9)) @ Matrix.Scale(1.3, 4) @ Matrix.Translation((0, -0.1, 0.9))
    for ob in P.parts[n0:]: ob.data.transform(G)
    # the storm cloud and the lightning
    rng = random.Random(21)
    for k in range(13):
        a = 2 * math.pi * k / 13; r = rng.uniform(0.55, 1.1)
        P.obj("Cloud", ball((math.cos(a) * r, math.sin(a) * r * 0.75, -1.15 + rng.uniform(-0.1, 0.08)), (0.45, 0.4, 0.28), 12, 6), "Dark", 1)
    P.obj("CloudCore", ball((0, 0, -1.1), (0.7, 0.6, 0.3), 12, 6), "Dark", 1)
    for k in range(4):
        x = -0.9 + k * 0.6
        P.obj("Bolt", pipe(zigzag((x, 0.2, -1.3), (x * 1.2, 0.3, -2.2), 5, 0.16, rng), [0.07, 0.065, 0.06, 0.05, 0.04, 0.0], 5), "Lamp")
    # the ring of eight taiko drums, turning face-on behind him
    RC = Vector((0, -0.5, 1.15)); R = 2.05
    P.part("RollDrums", xf(torus(R, 0.05, 0.0, 48, 6), Matrix.Rotation(math.radians(90), 3, "X"), tuple(RC)), "Trim", tuple(RC))
    def tomoe(c, n, dc):
        if n.y < 0.6: return None
        d = Vector((c.x - dc.x, c.z - dc.z, 0)); r = d.length / 0.26
        a = math.atan2(d.y, d.x)
        if r > 0.9: return "Trim"
        return "Accent" if 0.15 < r < 0.85 and ((a + r * 3.0) % (2 * math.pi / 3)) < 0.75 else "Belly"
    for k in range(8):
        a = 2 * math.pi * k / 8 + math.pi / 8
        dc = RC + Vector((math.cos(a) * R, 0, math.sin(a) * R))
        P.part("RollDrums", lathe([(0.0, -0.13), (0.24, -0.13), (0.3, 0.0), (0.24, 0.13), (0.0, 0.13)], 16, "y", tuple(dc)),
               (lambda dc: (lambda c, n: tomoe(c, n, dc) or ("Belly" if n.y < -0.6 else ("Trim" if abs(c.y - dc.y) > 0.1 else "Metal"))))(dc), tuple(RC))
    P.part("Muzzle", ball((0, 0.42, 1.04), (0.05, 0.03, 0.04), 8, 4), "Lamp", (0, 0.42, 1.04))
    return P


# ================================================================= 9. the komainu guardian (stands in for the snow crane; the fortune cat was "disgusting")
def lock(c, u, v, r0, turns=1.4, rad=0.07, n=14):
    """a curled lock of mane: a spiral tube in the plane of u and v, tightening from r0 about c."""
    c = Vector(c); u = Vector(u).normalized(); v = Vector(v).normalized(); T = 2 * math.pi * turns
    pts = []; radii = []
    for i in range(n + 1):
        t = T * i / n; k = 1 - 0.82 * i / n
        pts.append(c + (u * math.cos(t) + v * math.sin(t)) * r0 * k)
        radii.append(rad * (1 - 0.7 * i / n))
    radii[-1] = 0.0
    return pipe(pts, radii, 8)


def J_komainu():
    """The KOMAINU GUARDIAN, the temple's lion-dog come to life: white marble with a great mane of curled jade locks tipped in gold, a
    golden horn, fierce bulging golden eyes under heavy brows, a roaring mouth of fangs, a gold collar with a great bell and red cords, a
    glowing jade pearl under one forepaw, a tail of curls rising behind like flame, and blue spirit fire at its paws as it bounds through
    the sky."""
    P = Boss("komainu", {"Base": ((0.92, 0.90, 0.84), 0.35), "Belly": ((0.70, 0.68, 0.64), 0.3), "Accent": RED, "Trim": GOLD,
                         "Glass": ((1.0, 0.72, 0.08), 0.9), "Dark": ((0.03, 0.03, 0.04), 0.5), "Glow": ((0.05, 0.35, 1.0), 0.5),
                         "Metal": ((0.10, 0.55, 0.40), 0.65), "Lamp": ((0.02, 0.85, 0.40), 0.8)})
    tip = lambda c, n: "Metal"
    # the body, bounding toward you
    P.obj("Body", ball((0, -0.35, 0.15), (0.5, 0.85, 0.45), 16, 8), lambda c, n: "Belly" if n.z < -0.5 else "Base", 1)
    P.obj("Chest", ball((0, 0.25, 0.3), (0.58, 0.5, 0.55), 16, 8), "Base", 1)
    # the mane: a jade mass ringed with curled locks round the face
    MC = Vector((0, 0.42, 0.95))
    P.obj("Mane", ball(tuple(MC), (0.82, 0.32, 0.78), 18, 9), "Metal", 1)
    for k in range(16):
        a = 2 * math.pi * k / 16
        c = MC + Vector((math.cos(a) * 0.78, 0.08, math.sin(a) * 0.74))
        out = Vector((math.cos(a), 0, math.sin(a)))
        P.obj("Lock", lock(c, out, Vector((0, 1, 0)).cross(out) * (1 if k % 2 else -1), 0.2, 1.3, 0.085), "Metal")
        P.obj("LockTip", ball(tuple(c), (0.06, 0.06, 0.06), 6, 3), "Trim")
    for k in range(9):   # an inner ring of smaller curls, gold
        a = math.radians(200 + k * 17.5)
        c = MC + Vector((math.cos(a) * 0.55, 0.22, math.sin(a) * 0.52 + 0.05))
        P.obj("Curl", lock(c, (1, 0, 0), (0, 0, 1), 0.11, 1.2, 0.04), "Trim")
    # the head
    HC = Vector((0, 0.68, 0.95))
    P.obj("Head", ball(tuple(HC), (0.46, 0.4, 0.42), 16, 8), "Base", 1)
    P.obj("Snout", ball((0, 1.0, 0.82), (0.3, 0.2, 0.2), 12, 6), "Base", 1)
    P.obj("Nose", ball((0, 1.18, 0.9), (0.15, 0.08, 0.09), 10, 5), "Dark")
    for s in (1, -1):
        P.obj("Nostril", ball((s * 0.07, 1.24, 0.88), (0.035, 0.02, 0.025), 6, 3), "Belly")
        # great bulging eyes under heavy angry brows
        P.obj("EyeWhite", ball((s * 0.21, 0.98, 1.08), (0.15, 0.09, 0.12), 12, 6), "Dark")
        P.obj("Eye", ball((s * 0.21, 1.03, 1.07), (0.12, 0.06, 0.1), 12, 6), "Glass")
        P.obj("Pupil", ball((s * 0.21, 1.085, 1.06), (0.04, 0.015, 0.06), 8, 4), "Dark")
        P.obj("Brow", pipe([(s * 0.04, 1.05, 1.2), (s * 0.2, 1.06, 1.24), (s * 0.36, 0.96, 1.3), (s * 0.46, 0.82, 1.34)], [0.06, 0.075, 0.06, 0.0], 8), "Metal")
        P.obj("BrowCurl", lock((s * 0.42, 0.88, 1.32), (s, 0, 0), (0, 0, 1), 0.08, 1.2, 0.035), "Trim")
        P.obj("Ear", cone((s * 0.38, 0.62, 1.2), (s * 0.6, 0.55, 1.05), 0.11, 6), "Base", 0, False)
        # whisker curls at the cheeks, and the beard curls under the jaw
        P.obj("Cheek", lock((s * 0.36, 1.0, 0.8), (s, 0, 0), (0, 0, -1), 0.1, 1.3, 0.045), "Metal")
        P.obj("Beard", lock((s * 0.14, 0.95, 0.5), (0, 0, -1), (s, 0, 0), 0.09, 1.3, 0.045), "Metal")
        # the fangs
        P.obj("Fang", cone((s * 0.16, 1.12, 0.74), (s * 0.15, 1.15, 0.6), 0.035, 5), "Base", 0, False)
        P.obj("FangLow", cone((s * 0.15, 1.1, 0.55), (s * 0.14, 1.13, 0.66), 0.03, 5), "Base", 0, False)
    # the roaring mouth: an upper lip, a dropped jaw, a red tongue
    P.obj("Lip", ball((0, 1.08, 0.74), (0.26, 0.12, 0.06), 10, 5), "Base", 1)
    P.obj("MouthIn", ball((0, 1.05, 0.62), (0.22, 0.1, 0.11), 10, 5), "Accent")
    P.obj("Throat", ball((0, 1.1, 0.63), (0.13, 0.06, 0.06), 8, 4), "Dark")
    P.obj("Jaw", ball((0, 0.98, 0.5), (0.24, 0.15, 0.07), 10, 5), "Base", 1)
    P.obj("Tongue", ball((0, 1.1, 0.56), (0.1, 0.08, 0.03), 8, 4), "Accent")
    # the golden horn and the jewel on the brow
    P.obj("Horn", pipe(bez((0, 0.8, 1.3), (0, 0.85, 1.48), (0, 0.78, 1.6), (0, 0.66, 1.68), 6), [0.07, 0.06, 0.05, 0.04, 0.03, 0.015, 0.0], 8), "Trim")
    P.obj("Jewel", ball((0, 1.05, 1.27), (0.05, 0.03, 0.05), 8, 4), "Lamp")
    # the collar, the great bell and its red cords
    P.obj("Collar", torus(0.5, 0.06, 0.0, 22, 6), "Trim"); at(P.parts[-1], (0, 0.5, 0.5), Matrix.Rotation(math.radians(-62), 4, "X"))
    P.obj("Bell", ball((0, 0.9, 0.32), (0.13, 0.12, 0.13), 12, 6), "Trim")
    P.obj("BellSlot", box((0, 1.02, 0.3), (0.12, 0.01, 0.02)), "Dark", 0, False)
    for s in (1, -1):
        P.obj("Cord", pipe(bez((s * 0.08, 0.92, 0.38), (s * 0.3, 1.0, 0.2), (s * 0.35, 0.95, 0.0), (s * 0.3, 0.9, -0.15), 6), [0.025] * 7, 5), "Accent")
        P.obj("Tassel", cone((s * 0.3, 0.9, -0.12), (s * 0.3, 0.9, -0.38), 0.07, 6), "Accent", 0, False)
    # four legs bounding, curls at the elbows, golden claws, blue spirit fire at the paws
    for (y, s, fwd, name) in ((0.35, 1, True, "SwayLegFR"), (0.35, -1, True, "SwayLegFL"), (-0.85, 1, False, "SwayLegBR"), (-0.85, -1, False, "SwayLegBL")):
        hip = Vector((s * 0.38, y, 0.15))
        knee = hip + Vector((s * 0.12, 0.3 if fwd else -0.15, -0.35))
        paw = knee + Vector((0, 0.3 if fwd else -0.2, -0.35))
        P.part(name, pipe([hip, knee, paw], [0.2, 0.15, 0.13], 10), "Base", tuple(hip), 1)
        P.part(name, ball(tuple(paw + Vector((0, 0.05, -0.04))), (0.16, 0.2, 0.11), 10, 5), "Base", tuple(hip), 1)
        P.part(name, lock(knee + Vector((s * 0.12, -0.05, 0.02)), (0, -1, 0), (0, 0, 1), 0.09, 1.2, 0.045), "Metal", tuple(hip))
        for k in (-1, 0, 1): P.part(name, cone(paw + Vector((k * 0.07, 0.2, -0.06)), paw + Vector((k * 0.08, 0.3, -0.12)), 0.025, 4), "Trim", tuple(hip), 0, False)
        P.part(name, torus(0.13, 0.03, 0.0, 12, 4), "Trim", tuple(hip))
        P.spin[-1].data.transform(Matrix.Translation(tuple(knee + (paw - knee) * 0.55)))
        for k in range(2):
            c = paw + Vector(((k - 0.5) * 0.14, -0.12, -0.12))
            P.part(name, ball(tuple(c), (0.08, 0.1, 0.07), 8, 4), "Lamp", tuple(hip))
            P.part(name, cone(c + Vector((0, -0.05, 0)), c + Vector((0, -0.38, 0.06)), 0.07, 6), "Lamp", tuple(hip), 0, False)
    # the jade pearl it guards, under the right forepaw
    P.obj("Pearl", ball((0.52, 1.0, -0.55), (0.2, 0.2, 0.2), 14, 7), "Lamp")
    P.obj("PearlBand", torus(0.205, 0.02, -0.55, 18, 4), "Trim"); [setattr(v.co, "x", v.co.x + 0.52) for v in P.parts[-1].data.vertices]; [setattr(v.co, "y", v.co.y + 1.0) for v in P.parts[-1].data.vertices]
    # the tail: a fan of great curls rising behind like flame
    for k in range(5):
        a = math.radians(-56 + k * 28)
        base = Vector((0, -1.1, 0.4))
        tipp = base + Vector((math.sin(a) * 0.8, -0.2, 0.75 + math.cos(a) * 0.55))
        P.obj("TailStem", pipe(bez(base, base + Vector((math.sin(a) * 0.15, -0.35, 0.25)), tipp + Vector((-math.sin(a) * 0.1, -0.2, -0.3)), tipp, 8), [0.16, 0.15, 0.14, 0.13, 0.12, 0.11, 0.1, 0.09, 0.08], 10), "Metal")
        P.obj("TailCurl", lock(tipp, (math.sin(a), 0, math.cos(a)), (math.cos(a), 0, -math.sin(a)), 0.22, 1.4, 0.085), "Trim")
    # spirit fire turning round it
    for k in range(6):
        a = 2 * math.pi * k / 6
        c = Vector((math.cos(a) * 1.35, math.sin(a) * 1.25, 0.2 + 0.25 * math.sin(a * 2)))
        P.part("SpinFlames", cone(c + Vector((0, 0, 0.05)), c + Vector((0, 0, 0.32)), 0.08, 6), "Lamp", (0, 0, 0.2), 0, False)
        P.part("SpinFlames", ball(tuple(c), (0.09, 0.09, 0.08), 8, 4), "Lamp", (0, 0, 0.2))
    P.part("Muzzle", ball((0, 1.12, 0.64), (0.05, 0.03, 0.04), 8, 4), "Lamp", (0, 1.12, 0.64))
    return P


# ================================================================= 2026-10-12 round three: the oni warlord and the shogun mecha
# ("koi and isle - change them, I want something better and impressive": they take the koi streamer's and the pagoda isle's places)
def J_oni():
    """The oni warlord: a hulking red demon riding a cloud of fire - two great horns ringed in gold, a mane of living flame, furious yellow
    eyes under heavy brows, tusks and a fanged roaring mouth, a gold armoured shoulder and a rope of prayer beads, a tiger-skin loincloth,
    a spiked iron kanabo raised high in one fist (it swings) and a fireball blazing in the other open palm, embers circling him."""
    P = Boss("oni", {"Base": ((0.82, 0.16, 0.10), 0.35), "Belly": ((0.95, 0.42, 0.30), 0.3), "Accent": ((0.98, 0.72, 0.14), 0.4),
                     "Trim": ((1.0, 0.80, 0.28), 0.85), "Glass": ((0.97, 0.95, 0.88), 0.5), "Dark": ((0.05, 0.03, 0.03), 0.5),
                     "Glow": ((1.0, 0.42, 0.05), 0.5), "Metal": ((0.28, 0.28, 0.32), 0.7), "Lamp": ((1.0, 0.86, 0.25), 0.8)})
    skin = "Base"
    # the cloud of fire he rides
    for k in range(9):
        a = 2 * math.pi * k / 9
        r = 0.55 + 0.15 * (k % 2)
        P.obj("Cloud", ball((math.sin(a) * r, math.cos(a) * r * 0.8, -1.05 + 0.06 * (k % 3)), (0.38, 0.34, 0.24), 12, 6), "Dark", 1)
    P.obj("Cloud", ball((0, 0, -0.95), (0.6, 0.55, 0.3), 14, 7), "Dark", 1)
    for k in range(14):
        a = 2 * math.pi * k / 14
        b = Vector((math.sin(a) * 0.85, math.cos(a) * 0.7, -1.05))
        P.obj("CloudFlame", cone(b, b + Vector((math.sin(a) * 0.15, math.cos(a) * 0.12, 0.35 + 0.15 * (k % 3))), 0.12, 5), "Glow" if k % 2 else "Lamp", 0, False)
    # the torso: a barrel chest, a big belly, shoulders like boulders
    P.obj("Torso", lathe([(0.0, -0.35), (0.48, -0.32), (0.56, 0.05), (0.6, 0.4), (0.72, 0.8), (0.62, 1.02), (0.25, 1.12), (0.0, 1.14)], 22, "z"), skin, 1)
    for s in (1, -1):
        P.obj("Pec", ball((s * 0.24, 0.42, 0.78), (0.24, 0.12, 0.17), 12, 6), "Belly", 1)
    for k in range(3):
        P.obj("Abs", ball((0, 0.5, 0.42 - k * 0.17), (0.2, 0.06, 0.07), 10, 5), "Belly", 1)
    # the tiger-skin loincloth and a rope belt
    P.obj("Loin", lathe([(0.56, -0.05), (0.6, -0.3), (0.62, -0.55), (0.0, -0.55)], 20, "z"), lambda c, n: "Dark" if (ang(c) * 2.6 + c.z * 3) % 1.0 < 0.28 else "Accent", 0)
    P.obj("Belt", torus(0.58, 0.06, -0.05, 24, 6), "Glass")
    P.obj("BeltKnot", ball((0, 0.6, -0.06), (0.12, 0.08, 0.1), 8, 4), "Glass")
    # legs planted on the cloud
    for s in (1, -1):
        hip = Vector((s * 0.3, 0.0, -0.4)); knee = Vector((s * 0.5, 0.2, -0.7)); ankle = Vector((s * 0.48, 0.1, -0.95))
        P.obj("Leg", pipe([hip, knee, ankle], [0.24, 0.18, 0.14], 10), "Base", 1)
        P.obj("Anklet", xf(torus(0.15, 0.03, 0.0, 14, 4), None, tuple(ankle + Vector((0, 0, 0.05)))), "Trim")
        P.obj("Foot", ball(tuple(ankle + Vector((0, 0.12, -0.06))), (0.14, 0.22, 0.08), 10, 5), "Base", 1)
    # the head: a broad brutish face
    HC = Vector((0, 0.18, 1.45))
    P.obj("Head", ball(tuple(HC), (0.4, 0.38, 0.4), 16, 8), "Base", 1)
    P.obj("Jaw", ball((0, 0.36, 1.25), (0.34, 0.24, 0.18), 14, 7), "Base", 1)
    P.obj("Nose", ball((0, 0.58, 1.4), (0.1, 0.07, 0.08), 10, 5), "Base", 1)
    P.obj("Mouth", ball((0, 0.52, 1.24), (0.24, 0.07, 0.1), 14, 7), "Dark")
    P.obj("Tongue", ball((0, 0.53, 1.2), (0.13, 0.05, 0.04), 10, 5), "Glow")
    for s in (1, -1):
        P.obj("EyeWhite", ball((s * 0.15, 0.52, 1.55), (0.11, 0.05, 0.09), 12, 6), "Lamp")
        P.obj("Pupil", ball((s * 0.15, 0.565, 1.55), (0.04, 0.02, 0.045), 8, 4), "Dark")
        P.obj("Brow", hull([(s * 0.03, 0.58, 1.66), (s * 0.34, 0.47, 1.73), (s * 0.34, 0.42, 1.67), (s * 0.04, 0.54, 1.6), (s * 0.2, 0.56, 1.72)]), "Dark", 0, False)
        P.obj("Ear", ball((s * 0.4, 0.15, 1.45), (0.07, 0.1, 0.14), 8, 4), "Base")
        P.obj("Earring", xf(torus(0.06, 0.015, 0.0, 12, 4), Matrix.Rotation(math.radians(90), 3, "Y"), (s * 0.44, 0.17, 1.3)), "Trim")
        P.obj("Tusk", pipe(bez((s * 0.17, 0.5, 1.2), (s * 0.19, 0.55, 1.3), (s * 0.2, 0.56, 1.4), (s * 0.24, 0.52, 1.48), 4), [0.045, 0.04, 0.03, 0.015, 0.0], 6), "Glass")
        for k in range(3):
            x = s * (0.04 + k * 0.06)
            P.obj("Fang", cone((x, 0.56, 1.32), (x, 0.57, 1.25), 0.022, 4), "Glass", 0, False)
        # the two great horns, ringed in gold
        h0 = HC + Vector((s * 0.2, 0.05, 0.3))
        horn = bez(h0, h0 + Vector((s * 0.15, 0.05, 0.3)), h0 + Vector((s * 0.35, 0.0, 0.5)), h0 + Vector((s * 0.32, 0.15, 0.78)), 7)
        P.obj("Horn", pipe(horn, [0.11, 0.1, 0.085, 0.07, 0.055, 0.04, 0.02, 0.0], 8), "Glass", 1)
        P.obj("HornRing", xf(torus(0.11, 0.025, 0.0, 14, 4), None, tuple(horn[1])), "Trim")
    # the mane of living flame
    for k in range(17):
        a = math.radians(-130 + 260 * k / 16)
        b = HC + Vector((math.sin(a) * 0.36, -math.cos(a) * 0.32 - 0.05, 0.12 + 0.15 * math.cos(a * 0.5)))
        L = 0.55 + 0.25 * math.cos(a * 0.7) + 0.1 * (k % 2)
        tip = b + Vector((math.sin(a) * 0.35, -0.3, L))
        P.obj("Mane", pipe(bez(b, b + Vector((math.sin(a) * 0.1, -0.05, 0.2)), tip + Vector((0, 0.1, -0.25)), tip, 5), [0.14, 0.12, 0.09, 0.06, 0.03, 0.0], 7),
              "Glow" if k % 3 else "Lamp", 1)
    # the gold shoulder armour, and the prayer beads across his chest
    P.obj("Sode", xf(lathe([(0.0, 0.25), (0.3, 0.18), (0.4, 0.0), (0.38, -0.08)], 14, "z"), Matrix.Rotation(math.radians(-25), 3, "Y"), (-0.72, 0.05, 0.98)), "Trim", 1)
    for k in range(4):
        P.obj("SodeLace", xf(torus(0.36 - k * 0.02, 0.018, 0.0, 18, 4), Matrix.Rotation(math.radians(-25), 3, "Y"), (-0.74 - k * 0.02, 0.05, 0.92 - k * 0.07)), "Accent")
    for k in range(16):
        t = k / 15
        c = Vector((-0.55 + 1.05 * t, 0.42 + 0.18 * math.sin(math.pi * t), 1.05 - 0.75 * t))
        P.obj("Bead", ball(tuple(c), (0.06, 0.06, 0.06), 8, 4), "Dark" if k % 4 else "Accent")
    # the right arm raises the kanabo high - it swings
    sh = Vector((0.68, 0.05, 0.92))
    el = sh + Vector((0.32, 0.12, 0.25)); wr = el + Vector((-0.02, 0.1, 0.42))
    P.part("SwayClub", pipe([sh, el, wr], [0.22, 0.17, 0.14], 10), "Base", tuple(sh), 1)
    P.part("SwayClub", xf(torus(0.14, 0.03, 0.0, 14, 4), None, tuple(wr + Vector((0, 0, -0.08)))), "Trim", tuple(sh))
    P.part("SwayClub", ball(tuple(wr + Vector((0, 0.03, 0.08))), (0.15, 0.15, 0.15), 10, 5), "Base", tuple(sh), 1)
    g0 = wr + Vector((0, 0.03, -0.25)); g1 = wr + Vector((0.05, -0.05, 1.45))
    P.part("SwayClub", pipe([g0, g0 + (g1 - g0) * 0.3, g1], [0.06, 0.13, 0.2], 10), "Metal", tuple(sh))
    P.part("SwayClub", ball(tuple(g1), (0.2, 0.2, 0.12), 10, 5), "Metal", tuple(sh))
    for i in range(1, 6):
        q = g0 + (g1 - g0) * (0.35 + 0.13 * i); r = 0.1 + 0.02 * i
        for k in range(6):
            a = 2 * math.pi * k / 6 + i * 0.5
            d = Vector((math.sin(a), math.cos(a), 0))
            P.part("SwayClub", cone(tuple(q + d * r * 0.9), tuple(q + d * (r + 0.12)), 0.035, 4), "Trim", tuple(sh), 0, False)
    P.part("SwayClub", xf(torus(0.1, 0.03, 0.0, 12, 4), None, tuple(g0 + (g1 - g0) * 0.25)), "Trim", tuple(sh))
    # the left arm: an open palm, a fireball blazing in it
    sh = Vector((-0.68, 0.05, 0.85))
    el = sh + Vector((-0.3, 0.3, -0.25)); wr = el + Vector((0.05, 0.4, 0.05))
    P.obj("Arm", pipe([sh, el, wr], [0.22, 0.17, 0.14], 10), "Base", 1)
    P.obj("Bracer", xf(torus(0.15, 0.035, 0.0, 14, 4), Matrix.Rotation(math.radians(80), 3, "X"), tuple(el + (wr - el) * 0.55)), "Trim")
    P.obj("Palm", ball(tuple(wr + Vector((0, 0.1, 0))), (0.16, 0.14, 0.07), 10, 5), "Base", 1)
    fb = wr + Vector((0, 0.15, 0.3))
    P.obj("Fireball", ball(tuple(fb), (0.23, 0.23, 0.23), 14, 7), "Lamp")
    for k in range(9):
        a = 2 * math.pi * k / 9
        b = fb + Vector((math.sin(a) * 0.2, math.cos(a) * 0.2, 0.05))
        P.obj("FireTongue", cone(tuple(b), tuple(b + Vector((math.sin(a) * 0.1, math.cos(a) * 0.1, 0.32))), 0.09, 5), "Glow", 0)
    # embers circling him
    for k in range(14):
        a = 2 * math.pi * k / 14
        c = Vector((math.sin(a) * 1.55, math.cos(a) * 1.3, 0.5 + 0.4 * math.sin(a * 3)))
        r = 0.07 if k % 3 == 0 else 0.05
        P.part("SpinEmbers", hull([c + Vector((r, 0, 0)), c - Vector((r, 0, 0)), c + Vector((0, r, 0)), c - Vector((0, r, 0)), c + Vector((0, 0, r * 2)), c - Vector((0, 0, r))]),
               "Glow" if k % 2 else "Lamp", (0, 0, 0.5), 0, False)
    P.part("Muzzle", ball(tuple(fb + Vector((0, 0.25, 0))), (0.08, 0.05, 0.08), 8, 4), "Lamp", tuple(fb + Vector((0, 0.25, 0))))
    return P


def plate(c, w, h, t, rx=0.0, ry=0.0, rz=0.0):
    """a flat armour plate w wide, h tall, t thick, turned rx/ry/rz degrees about its centre."""
    m = Matrix.Rotation(math.radians(rz), 3, "Z") @ Matrix.Rotation(math.radians(ry), 3, "Y") @ Matrix.Rotation(math.radians(rx), 3, "X")
    return box(tuple(c), (w, t, h), m)

def J_shogun():
    """The last boss: the shogun mecha - a towering samurai war-machine in red lacquer and black with gold edging. A kabuto helmet with a
    great golden crescent crest and flared side wings, a black face mask with a blazing cyan visor and a grille mouth, layered shoulder
    plates as big as doors, a glowing core in the breastplate, a skirt of armour plates, legs ending in thrusters, a beam katana raised
    high (that arm swings), a gatling arm-cannon on the other, two war banners on its back, and a great ring of glowing crests turning
    behind it like a halo."""
    P = Boss("shogun", {"Base": ((0.72, 0.07, 0.07), 0.7), "Belly": ((0.07, 0.07, 0.09), 0.6), "Accent": ((0.86, 0.87, 0.92), 0.6),
                        "Trim": ((1.0, 0.78, 0.25), 0.9), "Glass": ((0.40, 0.95, 1.0), 0.95), "Dark": ((0.02, 0.02, 0.03), 0.5),
                        "Glow": ((0.30, 0.90, 1.0), 0.5), "Metal": ((0.38, 0.38, 0.44), 0.75), "Lamp": ((1.0, 0.55, 0.12), 0.8)})
    # the torso: a black frame, a red lacquered breastplate edged in gold, a glowing core
    P.obj("Frame", lathe([(0.0, -0.2), (0.42, -0.18), (0.5, 0.3), (0.62, 0.8), (0.55, 1.05), (0.0, 1.08)], 16, "z"), "Belly", 0)
    P.obj("Breast", hull([(-0.62, 0.3, 1.02), (0.62, 0.3, 1.02), (-0.58, 0.55, 0.85), (0.58, 0.55, 0.85), (-0.48, 0.58, 0.35), (0.48, 0.58, 0.35),
                          (-0.38, 0.45, 0.05), (0.38, 0.45, 0.05), (-0.55, 0.1, 0.5), (0.55, 0.1, 0.5), (-0.62, 0.0, 1.0), (0.62, 0.0, 1.0)]),
          lambda c, n: "Trim" if c.z > 0.97 or c.z < 0.1 else "Base", 0, False)
    for k in range(4):   # gold lacing bands across the breastplate
        z = 0.22 + k * 0.18
        P.obj("Lace", box((0, 0.56 - 0.04 * (k == 0), z), (0.95 - 0.12 * (k == 0), 0.03, 0.025)), "Trim", 0, False)
    P.obj("CoreRing", xf(torus(0.17, 0.04, 0.0, 22, 6), Matrix.Rotation(math.radians(90), 3, "X"), (0, 0.6, 0.66)), "Trim")
    P.obj("Core", ball((0, 0.6, 0.66), (0.14, 0.06, 0.14), 14, 7), "Glow")
    P.obj("Mon", ball((0, 0.63, 0.66), (0.06, 0.02, 0.06), 8, 4), "Accent")
    # the armour skirt: plates in a ring, red with gold hems, black ties between
    for k in range(9):
        a = math.radians(-160 + 320 * k / 8)
        c = Vector((math.sin(a) * 0.55, math.cos(a) * 0.5, -0.4))
        P.obj("Kusazuri", plate(c, 0.32, 0.55, 0.05, -12 * math.cos(a), 12 * math.sin(a), -math.degrees(a)), lambda c, n: "Trim" if c.z < -0.62 else "Base", 0, False)
    P.obj("Waist", torus(0.52, 0.07, -0.12, 24, 6), "Belly")
    # legs: black thighs, red shin guards, thruster feet
    for s in (1, -1):
        hip = Vector((s * 0.28, 0.0, -0.35)); knee = Vector((s * 0.38, 0.15, -0.95)); ank = Vector((s * 0.38, 0.0, -1.45))
        P.obj("Thigh", pipe([hip, knee], [0.2, 0.17], 10), "Belly")
        P.obj("Knee", ball(tuple(knee), (0.17, 0.17, 0.17), 10, 5), "Trim")
        P.obj("Shin", hull([tuple(knee + Vector((x, y, z))) for x in (-0.18, 0.18) for y in (-0.15, 0.24) for z in (0.0, -0.5)]),
              lambda c, n: "Trim" if n.y > 0.5 and c.z > knee.z - 0.08 else "Base", 0, False)
        P.obj("Foot", hull([tuple(ank + Vector((x, y, z))) for x in (-0.16, 0.16) for (y, z) in ((-0.15, 0.05), (0.32, 0.0), (0.32, -0.12), (-0.15, -0.12))]), "Belly", 0, False)
        P.obj("Thruster", lathe([(0.12, 0.0), (0.16, -0.12), (0.14, -0.14)], 12, "z", tuple(ank + Vector((0, 0.0, -0.12)))), "Metal")
        P.obj("Jet", cone(tuple(ank + Vector((0, 0, -0.2))), tuple(ank + Vector((0, -0.05, -0.75))), 0.13, 8), "Lamp", 0)
    # the head: a black mask with a cyan visor and a grille mouth, under the kabuto
    HC = Vector((0, 0.15, 1.42))
    P.obj("Neck", pipe([(0, 0.1, 1.05), (0, 0.12, 1.25)], [0.15, 0.13], 10), "Metal")
    P.obj("Mask", ball(tuple(HC), (0.3, 0.3, 0.3), 14, 7), "Belly", 1)
    P.obj("Visor", hull([(-0.27, 0.42, 1.5), (0.27, 0.42, 1.5), (-0.24, 0.4, 1.42), (0.24, 0.4, 1.42), (0, 0.46, 1.44), (0, 0.44, 1.52)]), "Glass", 0, False)
    for s in (1, -1):
        P.obj("EyeGlint", ball((s * 0.13, 0.46, 1.47), (0.06, 0.02, 0.025), 8, 4), "Glow")
    P.obj("Grille", box((0, 0.42, 1.3), (0.26, 0.05, 0.14)), "Metal", 0, False)
    for k in range(5):
        P.obj("GrilleBar", box(((k - 2) * 0.05, 0.45, 1.3), (0.018, 0.03, 0.12)), "Dark", 0, False)
    P.obj("Mustache", hull([(-0.2, 0.43, 1.37), (0.2, 0.43, 1.37), (0, 0.46, 1.4), (-0.24, 0.4, 1.32), (0.24, 0.4, 1.32)]), "Accent", 0, False)
    # the kabuto: a ribbed dome, a flared neck-guard in tiers, side wings, a golden crescent crest
    P.obj("Kabuto", lathe([(0.0, 0.5), (0.18, 0.47), (0.3, 0.38), (0.36, 0.24), (0.37, 0.12)], 20, "z", tuple(HC)),
          lambda c, n: "Trim" if (ang(c) / (2 * math.pi) * 20) % 1.0 < 0.12 else "Base", 0)
    P.obj("Brim", lathe([(0.38, 0.13), (0.42, 0.11), (0.36, 0.09)], 22, "z", tuple(HC)), "Trim")
    for k in range(4):   # the neck-guard: tiers of plates round the back and sides of the head
        for j in range(9):
            a = math.radians(70 + 220 * j / 8)
            r = 0.4 + k * 0.07
            c = HC + Vector((math.sin(a) * r, math.cos(a) * r - 0.04, 0.05 - k * 0.11))
            P.obj("Shikoro", plate(c, 0.2 + k * 0.02, 0.13, 0.04, 35, 0, -math.degrees(a)), "Trim" if k == 3 else ("Base" if k % 2 == 0 else "Belly"), 0, False)
    for s in (1, -1):
        P.obj("Fukigaeshi", hull([(s * 0.36, 0.25, 1.52), (s * 0.4, 0.3, 1.56), (s * 0.7, 0.35, 1.72), (s * 0.66, 0.15, 1.58), (s * 0.38, 0.1, 1.42), (s * 0.68, 0.32, 1.6)]),
              lambda c, n: "Trim" if abs(c.x) > 0.6 else "Base", 0, False)
    arc = [Vector((math.sin(t) * 0.75, 0.38, 1.98 + math.cos(t) * 0.48 - 0.38)) for t in [math.radians(-80 + 160 * i / 16) for i in range(17)]]
    polys = []
    for i in range(16):   # the crescent: a band thick in the middle, tapering to points
        w0 = 0.02 + 0.14 * math.sin(math.pi * i / 16); w1 = 0.02 + 0.14 * math.sin(math.pi * (i + 1) / 16)
        a0, a1 = arc[i], arc[i + 1]
        polys.append([tuple(a0), tuple(a1), tuple(a1 + (a1 - Vector((0, 0.38, 1.6))).normalized() * w1), tuple(a0 + (a0 - Vector((0, 0.38, 1.6))).normalized() * w0)])
    P.obj("Maedate", sheet(polys, 0.04), "Trim", 0, False)
    P.obj("CrestGem", ball((0, 0.44, 1.72), (0.08, 0.04, 0.08), 10, 5), "Glow")
    # the shoulder plates: tiers of red lacquer hung from a gold bar, big as doors
    for s in (1, -1):
        top = Vector((s * 0.8, 0.05, 1.1))
        P.obj("SodeBar", box(tuple(top + Vector((0, 0, 0.05))), (0.5, 0.5, 0.08)), "Trim", 0, False)
        for k in range(4):
            c = top + Vector((s * (0.06 + k * 0.05), 0, -0.12 - k * 0.17))
            P.obj("Sode", plate(c, 0.52, 0.2, 0.55, 0, s * (18 + k * 3), 90), lambda c, n, k=k: "Trim" if k == 3 and abs(n.z) < 0.5 else ("Base" if k % 2 == 0 else "Belly"), 0, False)
    # right arm: the beam katana raised high - it swings
    sh = Vector((0.72, 0.05, 0.85))
    el = sh + Vector((0.3, 0.25, -0.1)); wr = el + Vector((0.02, 0.15, 0.4))
    P.part("SwayBlade", pipe([sh, el], [0.15, 0.13], 10), "Belly", tuple(sh))
    P.part("SwayBlade", ball(tuple(el), (0.14, 0.14, 0.14), 10, 5), "Trim", tuple(sh))
    P.part("SwayBlade", hull([tuple(el + (wr - el) * u + Vector((x, y, 0))) for u in (0.1, 0.9) for x in (-0.14, 0.14) for y in (-0.12, 0.14)]), "Base", tuple(sh), 0, False)
    P.part("SwayBlade", ball(tuple(wr + Vector((0, 0, 0.05))), (0.15, 0.15, 0.15), 10, 5), "Belly", tuple(sh))
    hilt0 = wr + Vector((0, 0.0, -0.25)); hilt1 = wr + Vector((0, 0.0, 0.3))
    P.part("SwayBlade", pipe([hilt0, hilt1], [0.05, 0.05], 8), lambda c, n: "Trim" if (c.z * 14) % 1.0 < 0.35 else "Belly", tuple(sh))
    P.part("SwayBlade", xf(torus(0.12, 0.035, 0.0, 16, 4), None, tuple(hilt1)), "Trim", tuple(sh))   # the tsuba
    bt = hilt1 + Vector((-0.15, 0.05, 1.9))
    blade = [hilt1 + (bt - hilt1) * (i / 8) + Vector((0, -0.12 * math.sin(math.pi * i / 16), 0)) for i in range(9)]
    P.part("SwayBlade", pipe(blade, [0.07, 0.075, 0.075, 0.07, 0.065, 0.06, 0.05, 0.035, 0.0], 6), "Glass", tuple(sh))
    P.part("SwayBlade", pipe(blade[:-1], [0.03] * 8, 5), "Glow", tuple(sh))
    # left arm: a gatling arm-cannon
    sh = Vector((-0.72, 0.05, 0.85))
    el = sh + Vector((-0.3, 0.3, -0.25))
    P.obj("Arm", pipe([sh, el], [0.15, 0.13], 10), "Belly")
    P.obj("Elbow", ball(tuple(el), (0.14, 0.14, 0.14), 10, 5), "Trim")
    g0 = el + Vector((0.0, 0.05, 0.0)); g1 = el + Vector((0.08, 1.0, 0.1))
    P.obj("CannonBody", pipe([g0, g0 + (g1 - g0) * 0.45], [0.2, 0.2], 12), lambda c, n: "Trim" if abs(c.y - (g0.y + 0.2)) < 0.04 else "Base")
    for k in range(6):
        a = 2 * math.pi * k / 6
        d = Vector((math.sin(a) * 0.1, 0, math.cos(a) * 0.1))
        P.obj("Barrel", pipe([g0 + (g1 - g0) * 0.4 + d, g1 + d], [0.04, 0.04], 6), "Metal")
    P.obj("BarrelRing", xf(torus(0.15, 0.03, 0.0, 16, 4), Matrix.Rotation(math.radians(90), 3, "X"), tuple(g1 - (g1 - g0) * 0.05)), "Trim")
    P.obj("BarrelRing", xf(torus(0.15, 0.03, 0.0, 16, 4), Matrix.Rotation(math.radians(90), 3, "X"), tuple(g0 + (g1 - g0) * 0.6)), "Trim")
    # two war banners on poles from its back
    for s in (1, -1):
        p0 = Vector((s * 0.3, -0.4, 0.6)); p1 = Vector((s * 0.55, -0.55, 2.55))
        P.obj("Pole", pipe([p0, p1], [0.035, 0.03], 6), "Belly")
        P.obj("PoleTip", cone(tuple(p1), tuple(p1 + Vector((s * 0.03, -0.01, 0.18))), 0.05, 5), "Trim", 0, False)
        corners = [p1 + Vector((0, 0, -0.12)), p1 + Vector((s * 0.6, 0.0, -0.12)), p1 + Vector((s * 0.6, 0.0, -1.35)), p1 + Vector((0, 0, -1.35))]
        P.obj("Banner", hull([tuple(q + Vector((0, d, 0))) for q in corners for d in (-0.012, 0.012)]), "Accent", 0, False)
        mc = p1 + Vector((s * 0.3, 0.02, -0.65))
        P.obj("BannerMon", xf(lathe([(0.0, 0.0), (0.2, 0.0), (0.2, 0.02), (0.0, 0.02)], 16, "y"), None, tuple(mc)), "Base")
        P.obj("BannerMonC", xf(lathe([(0.0, 0.0), (0.09, 0.0), (0.09, 0.03), (0.0, 0.03)], 12, "y"), None, tuple(mc + Vector((0, 0.005, 0)))), "Trim")
        P.obj("BannerEdge", box(tuple(p1 + Vector((s * 0.3, 0, -1.37))), (0.62, 0.04, 0.06)), "Trim", 0, False)
    # back thrusters
    for s in (1, -1):
        b = Vector((s * 0.28, -0.42, 0.65))
        P.obj("BackPod", pipe([b + Vector((0, 0.2, 0.25)), b], [0.13, 0.15], 10), "Metal")
        P.obj("BackJet", cone(tuple(b), tuple(b + Vector((s * 0.05, -0.45, -0.45))), 0.12, 8), "Lamp", 0)
    # a great ring of glowing crests turning behind it like a halo
    RC = Vector((0, -0.75, 1.2))
    halo = torus(1.45, 0.045, 0.0, 48, 6)
    xf(halo, Matrix.Rotation(math.radians(90), 3, "X"), (0, 0, 0))
    P.part("RollHalo", xf(halo, None, tuple(RC)), "Trim", tuple(RC))
    for k in range(8):
        a = 2 * math.pi * k / 8
        c = RC + Vector((math.sin(a) * 1.45, 0, math.cos(a) * 1.45))
        P.part("RollHalo", xf(lathe([(0.0, -0.04), (0.2, -0.04), (0.2, 0.04), (0.0, 0.04)], 16, "y"), None, tuple(c)), "Belly", tuple(RC))
        P.part("RollHalo", xf(lathe([(0.0, 0.0), (0.12, 0.0), (0.12, 0.06), (0.0, 0.06)], 12, "y"), None, tuple(c)), "Glow" if k % 2 else "Trim", tuple(RC))
    P.part("Muzzle", ball(tuple(g1 + Vector((0, 0.1, 0))), (0.1, 0.06, 0.1), 8, 4), "Lamp", tuple(g1 + Vector((0, 0.1, 0))))
    return P



# ================================================================= 2026-10-14: the five remade like the alien / west / treasure / sea / meadow ones
# Real anatomy and proportions, scarier faces, the cartoon idea kept, details that sit evenly - each flying its own way, one you can see from
# the front - and their surfaces baked into textures (boss_bake.py) so they stop looking like plastic.
from west_bosses import V_, glow_strength, AB_pal
from alien_bosses import lerp_keys, spine_frames, oriented_ball, frame, skin
from autumn_bosses import st_loft, st_cloth, sq_axes, spline as st_spline
from sea_bosses import ell_cap, rh, ring_on
import boss_bake as BB


def jg(x, w):
    """a bump: 1 at x = 0, falling away over w."""
    return math.exp(-(x / w) ** 2)


def surf_grid(fn, nz, na, z0, z1, cap=True):
    """a closed surface of rings: fn(z, a) -> point, a measured round from +Y toward +X; capped top and bottom with a point."""
    bm = bmesh.new(); rings = []
    for i in range(nz + 1):
        z = z0 + (z1 - z0) * i / nz
        rings.append([bm.verts.new(fn(z, 2 * math.pi * k / na)) for k in range(na)])
    if cap:
        b = sum((v.co for v in rings[0]), Vector()) / na; t = sum((v.co for v in rings[-1]), Vector()) / na
        rings = [[bm.verts.new(b)]] + rings + [[bm.verts.new(t)]]
    return skin(bm, rings, na, cap=False)


def bm_join(bms):
    """several little meshes made one (dozens of teeth, studs, beads as a single part)."""
    out = bmesh.new()
    for b in bms:
        m = {v: out.verts.new(v.co) for v in b.verts}
        for f in b.faces:
            try: out.faces.new([m[v] for v in f.verts])
            except ValueError: pass
        b.free()
    return out


def small(ob):
    """marks a part as little repeated pieces: the bake gives them one swatch of the atlas between them instead of room of their own."""
    at = ob.data.attributes.get("small") or ob.data.attributes.new("small", "INT", "FACE")
    at.data.foreach_set("value", [1] * len(ob.data.polygons)); return ob


def limb(A, B, r0, r1, bulges=(), up=None, seg=20, n=14):
    """a limb from A to B tapering r0 -> r1, swollen by the muscles under its skin: bulges are (t, wt, ang, wa, k) - a muscle at t along it
    (wt long) and ang round it from `up` (wa wide), swelling the radius by k; capped at both ends (the joints cover them)."""
    A, B = V_(A), V_(B); ax = B - A; L = ax.length; ax = ax / L
    if up is None: u, v = frame(ax)
    else: u = (V_(up) - ax * V_(up).dot(ax)).normalized(); v = ax.cross(u)
    bm = bmesh.new(); rings = [[bm.verts.new(A)]]
    for i in range(n + 1):
        t = i / n; r = r0 + (r1 - r0) * t; ring = []
        for k in range(seg):
            a = 2 * math.pi * k / seg; m = 1.0
            for (tb, wt, ab, wa, kk) in bulges:
                m += kk * jg(t - tb, wt) * jg(math.atan2(math.sin(a - ab), math.cos(a - ab)), wa)
            ring.append(bm.verts.new(A + ax * (L * t) + (u * math.cos(a) + v * math.sin(a)) * (r * m)))
        rings.append(ring)
    rings.append([bm.verts.new(B)])
    return skin(bm, rings, seg, cap=False)


def claw_hand(P, wrist, fwd, palm, thumb, curl, k=1.0, spread=0.14, name="Hand", hub=None, skin_slot="Base", nail_slot="Dark"):
    """a big clawed hand at the wrist: the palm reaching along fwd, its face toward palm, the thumb on the side toward thumb; four fingers
    of three joints (the middle one longest), each joint bent toward the palm by curl (radians: 0 open, ~1.5 closed), splayed by spread,
    a hooked black claw on each; knuckles at every joint."""
    wrist = V_(wrist); f = V_(fwd).normalized(); n = V_(palm); n = (n - f * n.dot(f)).normalized()
    sd = V_(thumb); sd = (sd - f * sd.dot(f) - n * sd.dot(n)).normalized()
    def put(bm, sl):
        if hub is None: P.obj(name, bm, sl)
        else: P.part(name, bm, sl, tuple(hub))
    pc = wrist + f * (0.1 * k)
    put(oriented_ball(pc, (0.105 * k, 0.12 * k, 0.05 * k), *rh(sd, f, -n), 14, 8), skin_slot)
    segs, knuckles, nails = [], [], []
    for i in range(4):
        x = (1.5 - i) / 1.5                                      # +1 the index finger (the thumb's side) .. -1 the little one
        d = (f + sd * (x * spread)).normalized(); h = d.cross(n).normalized()
        p = pc + f * (0.1 * k) + sd * (x * 0.068 * k) - n * (0.01 * k)
        Ls = [L * k * (1.0 - 0.13 * abs(x - 0.33)) for L in (0.085, 0.06, 0.048)]
        rs = [0.034 * k, 0.03 * k, 0.026 * k, 0.022 * k]
        knuckles.append(ball(tuple(p), (rs[0] * 1.08,) * 3, 8, 4))
        for j in range(3):
            d = (Matrix.Rotation(curl * (1.0 if j else 0.7), 3, h) @ d).normalized()
            q = p + d * Ls[j]
            segs.append(pipe([p, p.lerp(q, 0.5), q], [rs[j], (rs[j] + rs[j + 1]) * 0.5 * 1.05, rs[j + 1]], 8))
            knuckles.append(ball(tuple(q), (rs[j + 1] * 1.05,) * 3, 8, 4))
            p = q
        nails.append(pipe(bez(p, p + d * (0.03 * k), p + d * (0.05 * k) + n * (0.012 * k), p + d * (0.06 * k) + n * (0.03 * k), 4),
                          [rs[3] * 0.9, rs[3] * 0.75, rs[3] * 0.5, rs[3] * 0.25, 0.0], 6))
    # the thumb: from the heel of the palm, out to the side and forward, two joints
    d = (sd * 0.75 + f * 0.55 + n * 0.25).normalized(); h = d.cross(n).normalized()
    p = wrist + f * (0.06 * k) + sd * (0.08 * k) + n * (0.01 * k)
    knuckles.append(ball(tuple(p), (0.04 * k,) * 3, 8, 4))
    for j, L in enumerate((0.07, 0.055)):
        d = (Matrix.Rotation(curl * 0.8, 3, h) @ d).normalized(); q = p + d * (L * k)
        segs.append(pipe([p, p.lerp(q, 0.5), q], [0.038 * k, 0.036 * k, 0.03 * k], 8)); knuckles.append(ball(tuple(q), (0.031 * k,) * 3, 8, 4)); p = q
    nails.append(pipe(bez(p, p + d * (0.03 * k), p + d * (0.05 * k) + n * (0.012 * k), p + d * (0.06 * k) + n * (0.03 * k), 4), [0.026 * k, 0.02 * k, 0.014 * k, 0.007 * k, 0.0], 6))
    put(bm_join(segs + knuckles), skin_slot)
    put(bm_join(nails), nail_slot)


def fist(P, c, gax, kd, k=1.0, grip_r=0.06, name="Fist", hub=None, skin_slot="Base", nail_slot="Dark"):
    """a big fist clenched round a grip (a haft through c along gax): four fingers wrapped round it, their knuckles toward kd, the back of
    the hand behind them, the thumb locked over the first two; a black claw tucked at each fingertip."""
    c, gx = V_(c), V_(gax).normalized(); kd = V_(kd); kd = (kd - gx * kd.dot(gx)).normalized(); bk = gx.cross(kd)   # bk: round from kd
    def put(bm, sl):
        if hub is None: P.obj(name, bm, sl)
        else: P.part(name, bm, sl, tuple(hub))
    R = grip_r + 0.032 * k; parts, nails = [], []
    def on(a, x, r=R): return c + gx * x + (kd * math.cos(a) + bk * math.sin(a)) * r
    for i in range(4):
        x = (i - 1.5) * 0.058 * k
        arc = [on(math.radians(a), x) for a in range(-75, 236, 20)]
        parts.append(pipe(arc, [0.033 * k] * (len(arc) - 1) + [0.026 * k], 8))
        for a in (0, 90):   # the knuckles: the big ones at the front, the middle joints below
            parts.append(ball(tuple(on(math.radians(a), x, R + 0.008 * k)), (0.037 * k, 0.037 * k, 0.037 * k), 8, 4))
        tip = arc[-1]; td = (arc[-1] - arc[-2]).normalized()
        nails.append(cone(tip, tip + td * (0.04 * k), 0.02 * k, 5))
    # the back of the hand: a block behind the knuckles, running back toward the wrist
    parts.append(oriented_ball(c - bk * (R * 0.6) + kd * (R * 0.55), (0.13 * k, 0.11 * k, 0.05 * k), *rh(gx, kd, -bk), 14, 7))
    # the thumb wrapped over the first two fingers
    th = [c + gx * (0.13 * k) + kd * (R * 0.3) - bk * (R * 0.9), c + gx * (0.1 * k) + kd * (R * 1.15) - bk * (R * 0.2), c + gx * (0.03 * k) + kd * (R * 1.25) + bk * (R * 0.35)]
    parts.append(pipe(th, [0.045 * k, 0.04 * k, 0.032 * k], 8)); parts.append(ball(tuple(th[1]), (0.042 * k,) * 3, 8, 4))
    nails.append(cone(th[-1], th[-1] + (th[-1] - th[-2]).normalized() * (0.04 * k) - gx * (0.01 * k), 0.022 * k, 5))
    put(bm_join(parts), skin_slot)
    put(bm_join(nails), nail_slot)
    return c - bk * (R * 0.7) - gx * (0.0)                      # where the wrist meets the back of the hand


def tube_rmf(pts, radii, seg=12):
    """a tube through pts, its rings carried along by parallel transport (they never flip the way a fixed 'up' does when the path turns
    upright - a horn rising and curling), radius per point, 0 closing to a point."""
    pts = [V_(p) for p in pts]; n = len(pts)
    tg = [(pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]).normalized() for i in range(n)]
    u = tg[0].orthogonal().normalized(); us = [u]
    for i in range(1, n):
        u = u - tg[i] * u.dot(tg[i]); u = u.normalized() if u.length > 1e-6 else tg[i].orthogonal().normalized(); us.append(u)
    bm = bmesh.new(); rings = []
    for i in range(n):
        if radii[i] < 1e-5: rings.append([bm.verts.new(pts[i])]); continue
        v = tg[i].cross(us[i])
        rings.append([bm.verts.new(pts[i] + (us[i] * math.cos(2 * math.pi * k / seg) + v * math.sin(2 * math.pi * k / seg)) * radii[i]) for k in range(seg)])
    if len(rings[0]) > 1: rings = [[bm.verts.new(pts[0])]] + rings
    if len(rings[-1]) > 1: rings = rings + [[bm.verts.new(pts[-1])]]
    return skin(bm, rings, seg, cap=False)


def fireball(P, name, c, R, hub=None, n=5):
    """a ball of fire as fire burns: a round body of flame whose top splits into n tongues climbing and twisting to points, the white-hot
    heart showing in the grooves between them."""
    c = V_(c); Hh = R * 2.0
    def fn(z, a):
        r = R * max(0.0, 1 - (z / (R * 0.9)) ** 2) ** 0.5 if z < 0 else R * (1 - z / Hh) ** 1.1
        u = max(0.0, z) / Hh; r *= 1 + (0.1 + 0.6 * u) * math.sin(n * a + u * 5.0)
        return c + V_((math.sin(a + u * 0.6) * r, math.cos(a + u * 0.6) * r, z))
    def paint(p, nn):
        z = p.z - c.z; u = max(0.0, z) / Hh; q = p - c; a = math.atan2(q.x, q.y) - u * 0.6
        return "Lamp" if (math.sin(n * a + u * 5.0) < -0.4 and z < Hh * 0.55) or z < -R * 0.2 else "Glow"
    bm = surf_grid(fn, 22, 40, -R * 0.9, Hh * 0.97)
    if hub is None: P.obj(name, bm, paint)
    else: P.part(name, bm, paint, tuple(hub))


def grow_since(P, n_parts, n_spin, c, k):
    """everything built since (P.parts had n_parts, P.spin n_spin) drawn k times bigger about c - movers too, hub and all."""
    c = V_(c)
    for ob in P.parts[n_parts:]:
        for v in ob.data.vertices: v.co = c + (v.co - c) * k
    for ob in P.spin[n_spin:]:
        loc = ob.location.copy(); nl = c + (loc - c) * k
        for v in ob.data.vertices: v.co = (c + (loc + v.co - c) * k) - nl
        ob.location = nl


def oni_torso_pt(z, a):
    """the oni's trunk at height z, a round from the front: a heavyweight's - a pot belly, a barrel chest, slabs of pectoral, the lats
    flaring under the arms, the trapezius rising like hills to the neck - every muscle a swelling under the skin."""
    rx = lerp_keys(z, [(-0.36, 0.46), (-0.1, 0.5), (0.15, 0.56), (0.4, 0.62), (0.72, 0.8), (0.92, 0.84), (1.02, 0.62), (1.1, 0.32), (1.14, 0.25)])
    ry = lerp_keys(z, [(-0.36, 0.34), (-0.1, 0.38), (0.15, 0.44), (0.4, 0.42), (0.72, 0.44), (0.92, 0.38), (1.02, 0.32), (1.1, 0.24), (1.14, 0.22)])
    af = math.atan2(math.sin(a), math.cos(a)); m = 0.12 * jg(af, 0.9) * jg(z - 0.12, 0.25)          # the belly
    m -= 0.05 * jg(af, 0.07) * jg(z - 0.08, 0.035)                                                    # the navel
    for s in (1, -1):
        m += 0.14 * jg(af - s * 0.52, 0.42) * jg(z - 0.75, 0.13) - 0.05 * jg(af - s * 0.55, 0.5) * jg(z - 0.6, 0.04)   # pectorals, crease
        m += 0.07 * jg(af - s * 1.35, 0.35) * jg(z - 0.6, 0.2) + 0.04 * jg(af - s * 0.95, 0.25) * jg(z - 0.2, 0.18)   # lats, obliques
        m += 0.09 * jg(af - s * 2.5, 0.45) * jg(z - 0.98, 0.12) + 0.05 * jg(af - s * 2.6, 0.3) * jg(z - 0.78, 0.13)    # traps, shoulder blades
    m -= 0.025 * jg(af, 0.06) * (1.0 if 0.25 < z < 0.95 else 0.0) + 0.03 * jg(abs(af) - math.pi, 0.08) * (1.0 if 0.0 < z < 1.0 else 0.0)
    return V_((math.sin(a) * rx * (1 + m), math.cos(a) * ry * (1 + m), z))


def flame_tongue(P, root, d, L, r, curl, hot="Lamp", cool="Glow", name="Flame", hub=None):
    """one tongue of fire: from root along d, curling by curl at its tip, tapering to a point - white-hot at the root, flame-coloured out."""
    root, d, curl = V_(root), V_(d).normalized(), V_(curl)
    pts = bez(root, root + d * (L * 0.4), root + d * (L * 0.8) + curl * 0.5, root + d * L + curl, 8)
    paint = lambda c, n, root=root, L=L: hot if (c - root).length < L * 0.38 else cool
    bm = pipe(pts, [r * (1 - (i / 8) ** 1.4) * (0.9 + 0.25 * math.sin(math.pi * i / 8)) for i in range(8)] + [0.0], 8)
    if hub is None: P.obj(name, bm, paint)
    else: P.part(name, bm, paint, tuple(hub))


def J2_oni():
    """THE ONI WARLORD (2026-10-14, remade like the alien / west / treasure / sea / meadow bosses): an aka-oni built like a heavyweight -
    a pot belly and a barrel chest, slabs of pectoral, the lats flaring, the trapezius rising like hills to his bull neck, deltoids like
    boulders, every muscle of his arms swelling under the red skin; big clawed hands - one a fist round the haft of his kanabo, the other
    open, a fireball blazing in its palm. The face of the oni masks: the brow ridge knotted and drawn down hard over deep-set eyes that
    burn yellow, a broad flat nose with flaring nostrils, a mouth open in a roar - square teeth, fangs above, and the oni's great tusks
    rising from his lower jaw past the lip; two horns ringed in gold, curly black hair, gold rings in his ears.
    The cartoon idea kept: the warlord with his iron club (octagonal, studded in even rows, banded in gold) raised high - it swings; the
    tiger-skin loincloth under a twisted white rope; the prayer beads across his chest; the gold shoulder plate; a halo of flame behind his
    head like Fudo Myoo's; embers circling him.
    He flies the way the thunder gods do: standing on his own storm cloud, billows of dark grey lit from inside by fire, curled at the rim
    the way clouds are painted in Japan, lightning cracking from its belly."""
    P = Boss("oni", AB_pal(Base=((0.42, 0.045, 0.03), 0.4), Belly=((0.3, 0.025, 0.025), 0.4), Accent=((0.85, 0.32, 0.04), 0.5), Trim=((0.98, 0.72, 0.2), 0.7),
                           Glass=((0.85, 0.78, 0.6), 0.6), Dark=((0.03, 0.025, 0.02), 0.4), Glow=((1.0, 0.32, 0.04), 0.5), Metal=((0.17, 0.17, 0.19), 0.5),
                           Lamp=((1.0, 0.8, 0.25), 0.8)))
    glow_strength(P, 2.0)
    # ---- the body
    P.obj("Torso", surf_grid(oni_torso_pt, 44, 48, -0.36, 1.14), "Base")
    P.obj("Neck", limb((0, 0.0, 1.0), (0, 0.04, 1.36), 0.27, 0.23, [(0.5, 0.3, math.radians(35), 0.4, 0.08), (0.5, 0.3, math.radians(-35), 0.4, 0.08)], up=(0, 1, 0)), "Base")
    for s in (1, -1):   # the legs, planted wide on the cloud
        hip, knee, ank = V_((s * 0.27, 0.0, -0.3)), V_((s * 0.56, 0.16, -0.68)), V_((s * 0.58, 0.06, -1.0))
        P.obj("Leg", limb(hip, knee, 0.26, 0.18, [(0.38, 0.3, 0.0, 0.7, 0.16), (0.45, 0.3, math.pi, 0.8, 0.1)], up=(0, 1, 0)), "Base")
        P.obj("Leg", limb(knee, ank, 0.18, 0.11, [(0.3, 0.25, math.pi, 0.8, 0.28), (0.25, 0.25, 0.0, 0.5, 0.06)], up=(0, 1, 0)), "Base")
        P.obj("Knee", ball(tuple(knee), (0.19, 0.19, 0.19), 14, 7), "Base")
        P.obj("Anklet", ring_on(ank + V_((0, 0, 0.04)), (0, 0, 1), 0.12, 0.028, 20, 6), "Trim")
        fc = ank + V_((0, 0.13, -0.07))
        P.obj("Foot", oriented_ball(fc, (0.13, 0.21, 0.08), V_((1, 0, 0)), V_((0, 1, 0)), V_((0, 0, 1)), 14, 7), "Base")
        for t in (-1, 0, 1):
            tp = fc + V_((t * 0.07, 0.19, 0.0))
            P.obj("Toe", ball(tuple(tp), (0.045, 0.06, 0.045), 8, 4), "Base")
            P.obj("Claw", cone(tp + V_((0, 0.04, 0.0)), tp + V_((0, 0.1, -0.03)), 0.028, 6), "Dark")
    # the tiger-skin loincloth under a twisted white rope, the knot in front
    P.obj("Loin", lathe([(0.5, 0.02), (0.6, -0.12), (0.65, -0.36), (0.67, -0.54), (0.61, -0.54), (0.58, -0.36), (0.53, -0.12), (0.46, 0.02)], 40, "z"), "Accent")
    rope = []
    for st in (0, 1):
        pts = []
        for i in range(121):
            t = i / 120.0; a = 2 * math.pi * t; ph = 2 * math.pi * t * 26 + st * math.pi
            c = V_((math.sin(a) * 0.6, math.cos(a) * 0.53, 0.0)); out = V_((math.sin(a), math.cos(a), 0))
            pts.append(c + (out * math.cos(ph) + V_((0, 0, 1)) * math.sin(ph)) * 0.03)
        rope.append(pipe(pts, [0.034] * 121, 8))
    for s in (1, -1):   # the knot's two loops and its two ends
        rope.append(ring_on(V_((s * 0.11, 0.58, 0.02)), (s * 0.3, 1.0, 0.25), 0.08, 0.032, 18, 6))
        rope.append(pipe(bez(V_((s * 0.03, 0.6, -0.02)), V_((s * 0.08, 0.66, -0.15)), V_((s * 0.06, 0.66, -0.28)), V_((s * 0.1, 0.64, -0.4)), 8), [0.034] * 8 + [0.022], 8))
    rope.append(ball((0, 0.6, 0.0), (0.06, 0.05, 0.06), 10, 5))
    P.obj("Rope", bm_join(rope), "Glass")
    # the prayer beads across his chest, from his left shoulder to his right hip, lying on the skin
    beads = []
    for i in range(18):
        t = i / 17.0; x, z = -0.62 + 1.12 * t, 1.0 - 1.08 * t
        a = min((abs(oni_torso_pt(z, math.radians(d)).x - x), math.radians(d)) for d in range(-90, 91, 2))[1]
        p = oni_torso_pt(z, a); out = V_((p.x, p.y * 1.4, 0.0)).normalized()
        beads.append((p + out * 0.06, i))
    P.obj("Bead", bm_join([ball(tuple(p), (0.058, 0.058, 0.058), 10, 5) for p, i in beads if i % 6 != 3]), "Dark")
    P.obj("Bead", bm_join([ball(tuple(p), (0.08, 0.08, 0.08), 12, 6) for p, i in beads if i % 6 == 3]), "Accent")
    # ---- the head: the oni mask's face
    H = V_((0, 0.06, 1.52)); HS = 1.2; _obj = P.obj
    def hobj(name, bm, paint="Base", *a):
        for v in bm.verts: v.co = H + (v.co - H) * HS
        return _obj(name, bm, paint, *a)
    hobj("Head", oriented_ball(H + V_((0, -0.03, 0.04)), (0.29, 0.3, 0.33), V_((1, 0, 0)), V_((0, 1, 0)), V_((0, 0, 1)), 24, 12), "Base")
    hobj("Jaw", oriented_ball(H + V_((0, 0.1, -0.21)), (0.27, 0.23, 0.15), V_((1, 0, 0)), V_((0, 1, 0)), V_((0, 0, 1)), 20, 10), "Base")
    hobj("Mouth", oriented_ball(H + V_((0, 0.25, -0.22)), (0.18, 0.08, 0.085), V_((1, 0, 0)), V_((0, 1, 0)), V_((0, 0, 1)), 18, 9), "Belly")
    up_lip = [H + V_((x, 0.315 - 0.25 * x * x, -0.14 + 0.03 * abs(x) / 0.2 + 0.02 * jg(x, 0.05))) for x in [-0.2 + 0.4 * i / 12 for i in range(13)]]
    lo_lip = [H + V_((x, 0.3 - 0.3 * x * x, -0.305 + 0.05 * (abs(x) / 0.2) ** 2)) for x in [-0.19 + 0.38 * i / 12 for i in range(13)]]
    hobj("Lip", pipe(up_lip, [0.035] * 13, 8), "Belly"); hobj("Lip", pipe(lo_lip, [0.034] * 13, 8), "Belly")
    teeth = []
    for i in range(8):
        x = -0.105 + 0.03 * i
        teeth.append(box(tuple(H + V_((x, 0.305 - 0.25 * x * x, -0.17))), (0.026, 0.022, 0.04)))
        teeth.append(box(tuple(H + V_((x, 0.29 - 0.3 * x * x, -0.272))), (0.026, 0.022, 0.036)))
    for s in (1, -1):
        b = H + V_((s * 0.135, 0.3, -0.155)); teeth.append(cone(b, b + V_((0, 0.004, -0.085)), 0.022, 6))       # the fangs
    hobj("Tooth", bm_join(teeth), "Glass")
    for s in (1, -1):
        b = H + V_((s * 0.16, 0.28, -0.29))
        hobj("Tusk", pipe(bez(b, b + V_((s * 0.01, 0.03, 0.08)), b + V_((s * 0.04, 0.05, 0.17)), b + V_((s * 0.09, 0.03, 0.25)), 8),
                           [0.04, 0.038, 0.034, 0.028, 0.022, 0.015, 0.009, 0.004, 0.0], 8), "Glass")
        # the brow knotted and drawn down at its inner end over the eye, the furrows between
        bw = bez(H + V_((s * 0.035, 0.315, 0.075)), H + V_((s * 0.11, 0.315, 0.1)), H + V_((s * 0.2, 0.28, 0.15)), H + V_((s * 0.28, 0.21, 0.18)), 10)
        hobj("Brow", tube_rmf(bw, [0.034 + 0.016 * math.sin(math.pi * (0.15 + 0.7 * i / 10)) for i in range(11)], 12), "Base")
        ec = H + V_((s * 0.135, 0.262, 0.035)); th = math.radians(18); ex = V_((math.cos(th), 0, s * math.sin(th)))
        hobj("Eye", oriented_ball(ec, (0.085, 0.055, 0.058), *rh(ex, V_((0, 1, 0)), ex.cross(V_((0, 1, 0))) * -1), 18, 9), "Lamp")
        hobj("Pupil", oriented_ball(ec + V_((-s * 0.01, 0.052, -0.006)), (0.024, 0.012, 0.03), V_((1, 0, 0)), V_((0, 1, 0)), V_((0, 0, 1)), 10, 5), "Dark")
        hobj("Lid", pipe([ec + V_((-s * 0.06, 0.03, -0.045)), ec + V_((0, 0.045, -0.05)), ec + V_((s * 0.07, 0.025, -0.025))], [0.016, 0.02, 0.014], 6), "Base")
        hobj("Cheek", oriented_ball(H + V_((s * 0.19, 0.22, -0.07)), (0.11, 0.08, 0.09), V_((1, 0, 0)), V_((0, 1, 0)), V_((0, 0, 1)), 12, 6), "Base")
        hobj("Nostril", oriented_ball(H + V_((s * 0.075, 0.31, -0.08)), (0.045, 0.05, 0.04), V_((1, 0, 0)), V_((0, 1, 0)), V_((0, 0, 1)), 10, 5), "Base")
        hobj("NoseHole", oriented_ball(H + V_((s * 0.05, 0.355, -0.105)), (0.028, 0.02, 0.018), V_((1, 0, 0)), V_((0, 1, 0)), V_((0, 0, 1)), 8, 4), "Dark")
        hobj("Ear", oriented_ball(H + V_((s * 0.3, 0.0, 0.0)), (0.05, 0.1, 0.13), V_((1, 0, 0)), V_((0, 1, 0)), V_((0, 0, 1)), 10, 6), "Base")
        hobj("Earring", ring_on(H + V_((s * 0.33, 0.03, -0.14)), (1, 0, 0), 0.055, 0.013, 16, 5), "Trim")
        # the horns, ringed in gold
        b = H + V_((s * 0.13, 0.12, 0.26))
        hp = bez(b, b + V_((s * 0.06, 0.03, 0.2)), b + V_((s * 0.2, 0.0, 0.42)), b + V_((s * 0.26, 0.1, 0.62)), 10)
        hobj("Horn", tube_rmf(hp, [0.085 - 0.0085 * i for i in range(10)] + [0.0], 12), "Glass")
        hobj("HornRing", ring_on(hp[1], hp[2] - hp[0], 0.085, 0.022, 18, 5), "Trim")
    hobj("Nose", oriented_ball(H + V_((0, 0.33, -0.05)), (0.1, 0.075, 0.075), V_((1, 0, 0)), V_((0, 1, 0)), V_((0, 0, 1)), 12, 6), "Base")
    hobj("Nose", pipe([H + V_((0, 0.315, 0.05)), H + V_((0, 0.35, -0.03))], [0.038, 0.045], 8), "Base")
    curls = []
    for row, (n, r, z, y) in enumerate(((9, 0.22, 0.27, -0.1), (7, 0.15, 0.33, -0.16), (4, 0.07, 0.36, -0.2))):
        for k in range(n):
            a = math.radians(-80 + 160 * k / (n - 1)); c = H + V_((math.sin(a) * r, y - math.cos(a) * 0.04, z + 0.02 * math.cos(a)))
            curls.append(ball(tuple(c), (0.07, 0.07, 0.065), 10, 5))
    hobj("Hair", bm_join(curls), "Dark")
    # the fire behind him (Fudo Myoo's blaze): tongues rising from the back of his head and shoulders, every one climbing, wavering in an S
    # and flicking at its tip, the tallest behind his head; a white-hot core at their roots
    for k in range(11):
        u = (k - 5) / 5.0; root = H + V_((u * 0.62, -0.46 - 0.1 * abs(u), -0.05 - 0.42 * u * u))
        L = 1.05 - 0.5 * abs(u) ** 1.3; w = 0.13 - 0.03 * abs(u); up = V_((u * 0.45, -0.12, 1.0)).normalized(); sd = V_((1, 0, 0)) * (1 if k % 2 else -1)
        pts = bez(root, root + up * (L * 0.35) + sd * (L * 0.12), root + up * (L * 0.7) - sd * (L * 0.14), root + up * L + sd * (L * 0.16), 12)
        paint = lambda c, nn, root=root, L=L: "Lamp" if (c - root).length < L * 0.3 else "Glow"
        P.obj("Halo", pipe(pts, [w * (1 - (i / 12) ** 1.6) * (0.8 + 0.4 * math.sin(math.pi * (i / 12) ** 0.7)) for i in range(12)] + [0.0], 9), paint)
    # ---- the arms: deltoids like boulders, biceps and triceps, the forearm's muscles
    for s in (1, -1):
        sh = V_((s * 0.8, 0.0, 0.93 if s > 0 else 0.89))
        P.obj("Deltoid", oriented_ball(sh + V_((s * 0.04, 0.0, 0.03)), (0.27, 0.26, 0.25), V_((1, 0, 0)), V_((0, 1, 0)), V_((0, 0, 1)), 18, 9), "Base")
    # his right arm raises the kanabo: a fist round its haft, the club upright - it swings
    sh, el = V_((0.8, 0.0, 0.93)), V_((1.24, 0.08, 1.12)); hub = tuple(sh)
    gax = V_((0.12, -0.06, 1.0)).normalized(); kd = V_((0.45, 0.9, 0.0))
    kdp = (kd - gax * kd.dot(gax)).normalized(); bk = gax.cross(kdp)
    G = V_((1.16, 0.26, 1.6))
    wr = G - bk * (0.093 * 0.75) - gax * 0.02
    P.part("SwayClub", limb(sh, el, 0.24, 0.19, [(0.5, 0.28, math.radians(90), 0.7, 0.24), (0.4, 0.3, math.radians(-90), 0.8, 0.16)], up=(0, 1, 0)), "Base", hub)
    P.part("SwayClub", ball(tuple(el), (0.195, 0.195, 0.195), 12, 6), "Base", hub)
    P.part("SwayClub", limb(el, wr, 0.2, 0.13, [(0.25, 0.25, 0.0, 0.8, 0.2)], up=(1, 0, 0)), "Base", hub)
    P.part("SwayClub", ring_on(el.lerp(wr, 0.78), wr - el, 0.15, 0.032, 20, 6), "Trim", hub)
    fist(P, G, gax, kd, 1.2, 0.065, "SwayClub", hub)
    g0, g1 = G - gax * 0.3, G + gax * 1.5
    club = [g0 + (g1 - g0) * t for t in (0.0, 0.08, 0.2, 0.3, 0.45, 0.65, 0.85, 1.0)]
    P.part("SwayClub", pipe(club, [0.055, 0.062, 0.065, 0.08, 0.12, 0.155, 0.17, 0.12], 8), "Metal", hub)
    for t, r in ((0.0, 0.07), (0.3, 0.1), (0.94, 0.185)):
        P.part("SwayClub", ring_on(g0 + (g1 - g0) * t, gax, r, 0.025, 8, 5), "Trim", hub)
    studs = []
    fr0 = frame(gax)
    for i in range(6):   # six rings of iron studs, one on each of the eight faces, every other ring turned half a face
        t = 0.4 + 0.1 * i; q = g0 + (g1 - g0) * t; r = lerp_keys(t, [(0.3, 0.08), (0.45, 0.12), (0.65, 0.155), (0.85, 0.17)])
        for k in range(8):
            a = 2 * math.pi * (k + 0.5 * (i % 2)) / 8; d = fr0[0] * math.cos(a) + fr0[1] * math.sin(a)
            studs.append(cone(q + d * (r * 0.95), q + d * (r + 0.07), 0.034, 6))
    P.part("SwayClub", bm_join(studs), "Metal", hub)
    # his left arm held out, palm up, the fireball blazing in it; the gold shoulder plate over it
    sh, el, wr = V_((-0.8, 0.0, 0.89)), V_((-1.2, 0.16, 0.6)), V_((-1.08, 0.62, 0.68))
    P.obj("Arm", limb(sh, el, 0.24, 0.19, [(0.5, 0.28, math.radians(90), 0.7, 0.24), (0.4, 0.3, math.radians(-90), 0.8, 0.16)], up=(0, 1, 0)), "Base")
    P.obj("Elbow", ball(tuple(el), (0.195, 0.195, 0.195), 12, 6), "Base")
    P.obj("Arm", limb(el, wr, 0.2, 0.13, [(0.25, 0.25, 0.0, 0.8, 0.2)], up=(0, 0, 1)), "Base")
    P.obj("Bracer", ring_on(el.lerp(wr, 0.78), wr - el, 0.15, 0.032, 20, 6), "Trim")
    claw_hand(P, wr, (0.12, 1.0, 0.12), (0, 0, 1), (-1, 0, 0), 0.32, 1.25)
    sode = lathe([(0.0, 0.34), (0.23, 0.31), (0.34, 0.2), (0.4, 0.04), (0.38, -0.06), (0.34, 0.0), (0.3, 0.16), (0.18, 0.26), (0.0, 0.29)], 28, "z")
    xf(sode, Matrix.Rotation(math.radians(-28), 3, "Y"), (-0.9, 0.0, 0.95))
    P.obj("Sode", sode, "Trim")
    for k in range(3):
        lace = ring_on(V_((0, 0, 0)), (0, 0, 1), 0.37 - 0.03 * k, 0.016, 28, 5)
        xf(lace, Matrix.Rotation(math.radians(-28), 3, "Y"), (-0.92 - 0.025 * k, 0.0, 0.92 - 0.06 * k))
        P.obj("SodeLace", lace, "Accent")
    FB = wr + V_((0.02, 0.2, 0.33))
    fireball(P, "Fireball", FB - V_((0, 0, 0.08)), 0.22)
    # ---- the storm cloud he rides: billows of grey, curled at the rim the way clouds are painted, lightning cracking from its belly
    puffs = []
    for k in range(12):
        a = 2 * math.pi * k / 12
        puffs.append(ball((math.sin(a) * 1.0, math.cos(a) * 0.72 - 0.05, -1.32 + 0.04 * math.cos(2 * a)), (0.38, 0.36, 0.3), 16, 8))
    for k in range(7):
        a = 2 * math.pi * k / 7 + 0.2
        puffs.append(ball((math.sin(a) * 0.52, math.cos(a) * 0.38 - 0.05, -1.18), (0.42, 0.4, 0.3), 16, 8))
    puffs.append(ball((0, -0.05, -1.2), (0.55, 0.5, 0.3), 18, 9))
    P.obj("Cloud", bm_join(puffs), "Metal")
    for x in (-0.9, -0.3, 0.3, 0.9):   # the painted curls along its front
        c = V_((x, 0.74 - 0.12 * abs(x), -1.36)); sp_ = []
        for i in range(41):
            t = i / 40.0; a = (math.pi * 0.5 + 2.6 * math.pi * t) * (1 if x > 0 else -1); r = 0.17 * (1 - 0.8 * t)
            sp_.append(c + V_((math.cos(a) * r, 0.0, math.sin(a) * r)))
        P.obj("CloudCurl", pipe(sp_, [0.06 * (1 - 0.6 * i / 40) for i in range(41)], 8), "Metal")
    for sx in (1, -1):   # lightning: a forked bolt cracking out sideways from each end of the cloud (hanging under it they read as legs)
        b = V_((sx * 1.25, 0.1, -1.4)); d = V_((sx * 1.0, 0.1, -0.35)).normalized(); sd = V_((-d.z, 0.0, d.x)) * sx
        pts = [b] + [b + d * (0.16 * i) + sd * (0.08 if i % 2 else -0.06) for i in range(1, 6)]
        P.obj("Lightning", pipe(pts, [0.045, 0.04, 0.035, 0.03, 0.022, 0.0], 6), "Lamp")
        f0 = pts[2]; fd = (d - sd * 0.9).normalized()
        P.obj("Lightning", pipe([f0, f0 + fd * 0.13 + sd * 0.05, f0 + fd * 0.26 - sd * 0.04, f0 + fd * 0.38], [0.03, 0.024, 0.016, 0.0], 6), "Lamp")
    # ---- embers circling him
    em = []
    for k in range(14):
        a = 2 * math.pi * k / 14; c = V_((math.sin(a) * 1.55, math.cos(a) * 1.3, 0.5 + 0.4 * math.sin(a * 3))); r = 0.06 if k % 2 else 0.045
        em.append(hull([c + V_((r, 0, 0)), c - V_((r, 0, 0)), c + V_((0, r, 0)), c - V_((0, r, 0)), c + V_((0, 0, r * 2)), c - V_((0, 0, r))]))
    P.part("SpinEmbers", bm_join(em), "Glow", (0, 0, 0.5))
    mz = FB + V_((0, 0.24, 0))
    P.part("Muzzle", ball(tuple(mz), (0.03, 0.03, 0.03), 6, 3), "Lamp", tuple(mz))
    return P


from treasure_bosses import feather as vane, long_feather as long_vane
from west_bosses import flat_pipe


def J2_crane():
    """THE SNOW CRANE (2026-10-14, remade like the alien / west / treasure / sea / meadow bosses): a red-crowned crane built like the real
    bird, swooping at you in the moment a crane brakes to land - body tipped up, the great wings thrown forward and cupped so their faces
    turn to you, the long-fingered primaries splayed, the legs dropped, the talons reaching. Her plumage is the real one: snow-white, the
    secondaries and the drooping tertials black (a black band all along the trailing edge of each wing), the primaries white; the neck
    black with the white band that runs from behind the eye down the nape; the bare red crown on top of the head, the face black, a long
    dagger of an olive bill aimed at you and parted on its red tongue; fierce gold eyes under a black brow.
    The cartoon idea kept: the spirit-crane in armour - Date Masamune's golden crescent as a maedate on her brow with its circlet, a
    red-lacquered breastplate laced in gold with a gold mon, red silk ribbons streaming from her neck (they sway), golden talons clutching
    a glowing pearl, cherry blossoms whirling round her (SpinBlossoms).
    She flies as a crane flies: the wings beat (FlapL / FlapR)."""
    P = Boss("crane", AB_pal(Base=((0.84, 0.85, 0.88), 0.4), Belly=((0.33, 0.33, 0.22), 0.45), Accent=((0.018, 0.018, 0.022), 0.45),
                             Trim=((0.98, 0.72, 0.2), 0.7), Glass=((0.6, 0.02, 0.03), 0.5), Dark=((0.025, 0.025, 0.03), 0.4), Glow=((1.0, 0.45, 0.62), 0.5),
                             Metal=((0.45, 0.02, 0.02), 0.5), Lamp=((1.0, 0.82, 0.4), 0.8)))
    glow_strength(P, 1.6)
    SP = V_((0, 0.87, 0.5)).normalized()                       # the spine, tail to shoulders: tipped up thirty degrees as she brakes
    sp = [V_((0, -0.52, -0.3)) + SP * (1.15 * i / 24) for i in range(25)]
    FR = spine_frames(sp); n = len(sp); uu = [i / (n - 1) for i in range(n)]
    RX = [lerp_keys(u, [(0, 0.06), (0.15, 0.17), (0.4, 0.26), (0.65, 0.27), (0.85, 0.22), (1, 0.12)]) for u in uu]
    RU = [lerp_keys(u, [(0, 0.05), (0.4, 0.18), (0.65, 0.2), (0.85, 0.16), (1, 0.1)]) for u in uu]
    RD = [lerp_keys(u, [(0, 0.05), (0.4, 0.22), (0.65, 0.28), (0.85, 0.24), (1, 0.12)]) for u in uu]
    P.obj("Body", st_loft(sp, RX, RU, RD, FR, 32, 1.1), "Base")
    def bpt(u, a, k=1.0):   # the body's surface at u along it, a round it (0 the right side, 90 the back, -90 the breast)
        i = min(n - 2, int(u * (n - 1))); f = u * (n - 1) - i
        t, sd, up = FR[i]; c = sp[i].lerp(sp[i + 1], f); rx = RX[i] + (RX[i + 1] - RX[i]) * f
        r2 = (RU[i] + (RU[i + 1] - RU[i]) * f) if math.sin(a) > 0 else (RD[i] + (RD[i + 1] - RD[i]) * f)
        return c + (sd * (math.cos(a) * rx) + up * (math.sin(a) * r2)) * k
    # ---- the neck: rising from the shoulders and levelling out toward you; black, with the white band down its nape
    N0 = sp[-1] + FR[-1][2] * 0.02
    neck = bez(N0, N0 + V_((0, 0.22, 0.32)), N0 + V_((0, 0.62, 0.48)), N0 + V_((0, 1.0, 0.42)), 16)
    nr = [lerp_keys(i / 16, [(0, 0.14), (0.25, 0.1), (0.7, 0.085), (1, 0.09)]) for i in range(17)]
    P.obj("Neck", tube_rmf(neck, nr, 16), "Accent")
    nape = []
    for i in range(17):
        tg = (neck[min(16, i + 1)] - neck[max(0, i - 1)]).normalized(); bk = (V_((0, 0, 1)) - tg * tg.z).normalized()
        nape.append(neck[i] + bk * (nr[i] * 0.78))
    P.obj("Nape", flat_pipe(nape, [nr[i] * 0.55 for i in range(17)], V_((0, 0, 1)), 0.6, 10), "Base")
    # ---- the head: the bare red crown, the black face, the white patch behind the eye, the dagger bill aimed at you
    HC = neck[-1] + V_((0, 0.08, 0.02)); fwd = V_((0, 0.84, -0.54)).normalized(); hx, hz = V_((1, 0, 0)), V_((1, 0, 0)).cross(fwd)
    h0 = len(P.parts); HK = 1.35
    if hz.z < 0: hz = -hz
    P.obj("Head", oriented_ball(HC, (0.12, 0.17, 0.12), *rh(hx, fwd, hz), 22, 11), "Accent")
    P.obj("Crown", ell_cap(HC + hz * 0.012, (0.115, 0.15, 0.115), hx, fwd, hz, hz - fwd * 0.25, 0.07, 28, 7, 0.01), "Glass")
    for s in (1, -1):
        P.obj("Cheek", oriented_ball(HC + hx * (s * 0.075) - fwd * 0.06 + hz * 0.0, (0.06, 0.09, 0.075), *rh(hx, fwd, hz), 12, 6), "Base")
        ec = HC + hx * (s * 0.075) + fwd * 0.1 + hz * 0.045; ed = (hx * (s * 0.55) + fwd * 0.75 + hz * 0.35).normalized()   # (she glares ahead)
        ex_ = ed.cross(hz).normalized(); ez_ = ex_.cross(ed).normalized()
        P.obj("Eye", oriented_ball(ec, (0.042, 0.045, 0.045), *rh(ex_, ed, ez_), 16, 8), "Lamp")
        P.obj("Pupil", oriented_ball(ec + ed * 0.04, (0.011, 0.01, 0.028), *rh(ex_, ed, ez_), 8, 4), "Dark")
        P.obj("Brow", tube_rmf(bez(ec + fwd * 0.06 + hz * 0.018 - hx * (s * 0.035), ec + fwd * 0.03 + hz * 0.05 - hx * (s * 0.01), ec - fwd * 0.02 + hz * 0.062 + hx * (s * 0.01),
                                  ec - fwd * 0.07 + hz * 0.075 + hx * (s * 0.015), 6), [0.014, 0.024, 0.028, 0.024, 0.016, 0.008, 0.0], 8), "Accent")
    bb = HC + fwd * 0.15
    up_b = [bb + fwd * (0.62 * t) + hz * (0.03 * (1 - t) + 0.006) for t in [i / 10 for i in range(11)]]
    lo_b = [bb + fwd * (0.56 * t) - hz * (0.035 * (1 - t) + 0.07 * t) for t in [i / 10 for i in range(11)]]
    P.obj("Bill", flat_pipe(up_b, [0.05 * (1 - t) ** 0.8 + 0.004 for t in [i / 10 for i in range(11)]], hx, 0.3, 10), "Belly")
    P.obj("Bill", flat_pipe(lo_b, [0.042 * (1 - t) ** 0.8 + 0.003 for t in [i / 10 for i in range(11)]], hx, 0.3, 10), "Belly")
    P.obj("Tongue", pipe([bb + fwd * 0.02 - hz * 0.012, bb + fwd * 0.2 - hz * 0.035, bb + fwd * 0.34 - hz * 0.045], [0.022, 0.018, 0.0], 6), "Glass")
    # Date Masamune's golden crescent: the maedate on her brow, its circlet round her head
    P.obj("Circlet", ring_on(HC + hz * 0.02 - fwd * 0.01, hz + fwd * 0.3, 0.125, 0.014, 28, 5), "Trim")
    mb = HC + V_((0, -0.02, 0.135))   # standing up on top of her head (on the brow it hid her face from in front)
    arc = [mb + V_((math.sin(t) * 0.32, -0.04 * (1 - math.cos(t)), 0.32 * (1 - math.cos(t)) * 0.75)) for t in [math.radians(-80 + 160 * i / 24) for i in range(25)]]
    P.obj("Maedate", tube_rmf(arc, [0.0] + [0.034 * math.sin(math.pi * i / 24) ** 0.6 + 0.004 for i in range(1, 24)] + [0.0], 8), "Trim")
    P.obj("MaedateGem", ball(tuple(mb + V_((0, 0.02, 0.0))), (0.028, 0.02, 0.028), 10, 5), "Lamp")
    for ob in P.parts[h0:]:   # the head drawn HK times bigger about where it meets the neck
        for v in ob.data.vertices: v.co = neck[-1] + (v.co - neck[-1]) * HK
    # ---- her breastplate: four lames of red lacquer round the breast, laced together in gold, a gold mon on the top lame
    lames, lace = [], []
    for k in range(4):
        u0 = 0.52 + 0.1 * k; quads = []
        for j in range(12):
            a0, a1 = math.radians(-165 + 150 * j / 12), math.radians(-165 + 150 * (j + 1) / 12)
            quads.append([tuple(bpt(u0, a0, 1.08)), tuple(bpt(u0 + 0.095, a0, 1.1)), tuple(bpt(u0 + 0.095, a1, 1.1)), tuple(bpt(u0, a1, 1.08))])
        lames.append(st_cloth(quads, 0.025))
        for j in range(7):
            a = math.radians(-150 + 120 * j / 6)
            lace.append(pipe([bpt(u0 - 0.01, a, 1.14), bpt(u0 + 0.03, a, 1.13)], [0.012, 0.012], 5))
    P.obj("Plate", bm_join(lames), "Metal")
    P.obj("PlateLace", bm_join(lace), "Trim")
    mc_ = bpt(0.86, math.radians(-90), 1.18); mn = (mc_ - bpt(0.86, math.radians(-90), 0.0)).normalized()
    P.obj("Mon", ring_on(mc_, mn, 0.075, 0.014, 24, 5), "Trim")
    P.obj("Mon", oriented_ball(mc_, (0.06, 0.06, 0.012), *sq_axes(mn), 16, 4), "Trim")
    # ---- the wings, thrown forward and cupped to brake, their faces to you; each one Flap part beating about the nose axis
    S0 = bpt(0.68, math.radians(40), 0.8); U0 = V_((0.85, 0.25, 0.48)).normalized(); C0 = V_((0.0, -0.3, -1.0)); C0 = (C0 - U0 * C0.dot(U0)).normalized()
    N0 = U0.cross(C0).normalized()
    if N0.y < 0: N0 = -N0
    SPAN = 1.75
    def W(s, u, c, h=0.0):   # u 0 the shoulder .. 1 the wrist-to-tip (the wrist at 0.55), c down the chord, h off the face
        cup = 0.16 * math.sin(math.pi * min(max(u, 0.0), 1.0)) * (0.5 + c)
        p = S0 + U0 * (u * SPAN) + C0 * c + N0 * (h - cup) + V_((0, 0, 0.12 * u * u))
        return V_((s * p.x, p.y, p.z))
    def M(s, v): return V_((s * v.x, v.y, v.z))
    for s in (1, -1):
        name = "FlapR" if s > 0 else "FlapL"; hub = tuple(W(s, 0, 0)); nrm = M(s, N0)
        quads = []
        for i in range(14):
            for j in range(3):
                u0, u1 = 0.95 * i / 14, 0.95 * (i + 1) / 14; c0, c1 = 0.34 * j / 3, 0.34 * (j + 1) / 3
                quads.append([tuple(W(s, u0, c0, -0.012)), tuple(W(s, u1, c0, -0.012)), tuple(W(s, u1, c1, -0.012)), tuple(W(s, u0, c1, -0.012))])
        P.part(name, st_cloth(quads, 0.024), "Base", hub, 0, True)
        P.part(name, tube_rmf([W(s, 0.97 * k / 14, -0.01, 0.02) for k in range(15)], [lerp_keys(k / 14, [(0, 0.075), (0.55, 0.05), (1, 0.03)]) for k in range(15)], 12), "Base", hub)
        for row, (c0, L, w, du, h) in enumerate(((0.0, 0.12, 0.045, 0.05, 0.05), (0.07, 0.15, 0.05, 0.055, 0.04), (0.15, 0.2, 0.06, 0.065, 0.03))):
            u = 0.03 + (du * 0.5 if row % 2 else 0.0)
            while u < 0.95:   # the coverts in shingled rows: lesser, median, greater - snow-white
                P.part(name, vane(W(s, u, c0, h), M(s, (C0 + U0 * (0.12 * u)).normalized()), L * (1 - 0.15 * u), w, nrm, -0.01, 0.5), "Base", hub, 0, False)
                u += du
        for k in range(14):   # the secondaries: black, square-tipped, the trailing edge of the arm
            u = 0.06 + 0.5 * k / 13
            P.part(name, vane(W(s, u, 0.28, 0.006 * (k % 2)), M(s, (C0 + U0 * (0.05 + 0.12 * k / 13)).normalized()), 0.74 - 0.06 * k / 13, 0.12, nrm, -0.03, 0.62),
                   "Accent", hub, 0, False)
        for k in range(4):    # the tertials: long, black, drooping over the body
            u = 0.0 + 0.05 * k
            P.part(name, long_vane(W(s, u, 0.22, 0.01), M(s, (C0 - U0 * 0.25 + V_((0, -0.2, 0))).normalized()), 0.9 - 0.05 * k, 0.12, nrm, -0.06, 0.45), "Accent", hub, 0, False)
        for k in range(10):   # the primaries: white, the outer six splayed apart like fingers and curling up at their tips
            phi = math.radians(-74 + 92 * k / 9)
            L = lerp_keys(k / 9, [(0, 0.82), (0.35, 1.0), (0.6, 1.18), (0.8, 1.2), (1, 1.05)])
            d = M(s, U0 * math.cos(phi) - C0 * math.sin(phi))
            w = 0.13 if k < 4 else 0.1
            P.part(name, long_vane(W(s, 0.92 + 0.08 * k / 9, 0.3 - 0.26 * k / 9, 0.005 * (10 - k)), d, L, w, nrm, 0.05 + 0.03 * (k >= 4), 0.18 if k >= 4 else 0.3),
                   "Base", hub, 0, False)
        for k in range(6):    # the primary coverts over their bases
            phi = math.radians(-60 + 80 * k / 5)
            P.part(name, vane(W(s, 0.9 + 0.06 * k / 5, 0.26 - 0.2 * k / 5, 0.035), M(s, U0 * math.cos(phi) - C0 * math.sin(phi)), 0.3, 0.08, nrm, -0.01, 0.45),
                   "Base", hub, 0, False)
    # ---- the tail: twelve white feathers fanned below her, under the drooping tertials
    tb = sp[1] + FR[1][2] * 0.02
    for k in range(12):
        c_ = (k - 5.5) / 5.5; d = (-SP + V_((c_ * 0.55, 0.0, -0.2))).normalized()
        P.obj("Tail", vane(tb + V_((c_ * 0.06, 0, 0)), d, 0.5 - 0.1 * abs(c_), 0.08, FR[1][2], -0.02, 0.5), "Base")
    # ---- the legs dropped to land: white thighs, long black shanks, golden talons round the glowing pearl
    PE = V_((0, 0.18, -1.12))
    for s in (1, -1):
        hip = bpt(0.42, math.radians(-90 + s * 55), 0.85); knee = hip + V_((s * 0.04, 0.22, -0.28)); heel = V_((s * 0.13, 0.02, -0.7)); ank = PE + V_((s * 0.11, -0.05, 0.13))
        P.obj("Thigh", limb(hip, knee, 0.085, 0.05), "Base")
        P.obj("Leg", pipe([knee, knee.lerp(heel, 0.5), heel], [0.03, 0.026, 0.028], 8), "Dark")
        P.obj("Leg", ball(tuple(heel), (0.036, 0.036, 0.036), 8, 4), "Dark")
        P.obj("Leg", pipe([heel, heel.lerp(ank, 0.5), ank], [0.026, 0.024, 0.026], 8), "Dark")
        e1 = (ank - PE).normalized()
        for k, spread in enumerate((V_((s * 0.25 - 0.55, 1.0, 0.0)), V_((s * 0.25, 1.0, 0.0)), V_((s * 0.25 + 0.55, 1.0, 0.0)), V_((s * 0.3, -1.0, 0.0)))):
            e2 = (spread - e1 * e1.dot(spread)).normalized()   # three toes forward over the pearl, the hind toe behind it, each curling round it
            toe = [PE + (e1 * math.cos(th) + e2 * math.sin(th)) * 0.175 for th in [math.radians(14 + 96 * j / 6) for j in range(7)]]
            P.obj("Toe", pipe(toe, [0.024, 0.023, 0.022, 0.021, 0.019, 0.016, 0.012], 6), "Dark")
            P.obj("Talon", cone(toe[-1], toe[-1] + (toe[-1] - toe[-2]).normalized() * 0.07 - (toe[-1] - PE).normalized() * 0.02, 0.016, 6), "Trim")
    P.obj("Pearl", ball(tuple(PE), (0.15, 0.15, 0.15), 20, 10), "Lamp")
    P.obj("PearlRing", ring_on(PE, (0, 1, 0), 0.19, 0.012, 32, 5), "Trim")
    # ---- red silk ribbons streaming from a knot at the base of her neck, gold tassels at their ends; each sways
    knot = neck[3] + V_((0, 0.06, -0.05))
    P.obj("NeckKnot", ball(tuple(knot), (0.1, 0.07, 0.07), 12, 6), "Glass")
    for s, k in ((1, 0), (-1, 1)):
        path = bez(knot, knot + V_((s * 0.22, -0.3, -0.12)), knot + V_((s * 0.3, -0.85, -0.45)), knot + V_((s * 0.45, -1.35, -0.75)), 14)
        polys = []
        for i in range(14):
            a, b = path[i], path[i + 1]; w0, w1 = 0.07 - 0.02 * i / 14, 0.07 - 0.02 * (i + 1) / 14
            t0 = V_((0, math.sin(i * 0.5) * 0.4, 1)).normalized(); t1 = V_((0, math.sin((i + 1) * 0.5) * 0.4, 1)).normalized()
            polys.append([tuple(a + t0 * w0), tuple(b + t1 * w1), tuple(b - t1 * w1), tuple(a - t0 * w0)])
        P.part("SwayRibbon%d" % k, st_cloth(polys, 0.016), "Glass", tuple(knot), 0, True)
        P.part("SwayRibbon%d" % k, cone(path[-1], path[-1] + V_((s * 0.05, -0.08, -0.16)), 0.045, 8), "Trim", tuple(knot), 0, False)
    # ---- cherry blossoms whirling round her: five petals each, a gold heart
    bl = []; hearts = []
    for k in range(14):
        a = 2 * math.pi * k / 14; c = V_((math.sin(a) * 2.2, -0.1 + math.cos(a) * 1.8, 0.3 + 0.3 * math.sin(a * 3)))
        for j in range(5):
            b = 2 * math.pi * j / 5 + a
            bl.append(oriented_ball(c + V_((math.cos(b) * 0.055, 0, math.sin(b) * 0.055)), (0.045, 0.012, 0.03), *rh(V_((math.cos(b), 0, math.sin(b))), V_((0, 1, 0)), V_((-math.sin(b), 0, math.cos(b)))), 8, 4))
        hearts.append(ball(tuple(c + V_((0, 0.012, 0))), (0.022, 0.018, 0.022), 6, 3))
    P.part("SpinBlossoms", bm_join(bl), "Glow", (0, -0.1, 0.3))
    P.part("SpinBlossoms", bm_join(hearts), "Lamp", (0, -0.1, 0.3))
    mz = bb + fwd * 0.66
    P.part("Muzzle", ball(tuple(mz), (0.02, 0.02, 0.02), 6, 3), "Dark", tuple(mz))
    return P


def lame_band(z0, z1, rx0, ry0, rx1, ry1, a0=-180.0, a1=180.0, seg=40, thick=0.025, yk=1.0):
    """one lame of armour: a band round the body from height z0 (radii rx0, ry0) to z1 (rx1, ry1), from angle a0 to a1 (degrees round from
    the front toward +x), given a thickness; yk squashes it front to back."""
    quads = []
    for j in range(seg):
        b0, b1 = math.radians(a0 + (a1 - a0) * j / seg), math.radians(a0 + (a1 - a0) * (j + 1) / seg)
        def q(a, z, rx, ry): return (math.sin(a) * rx, math.cos(a) * ry * yk, z)
        quads.append([q(b0, z0, rx0, ry0), q(b1, z0, rx0, ry0), q(b1, z1, rx1, ry1), q(b0, z1, rx1, ry1)])
    return st_cloth(quads, thick)


def laced(P, name, z0, z1, rx0, ry0, rx1, ry1, a0, a1, n, slot="Accent", yk=1.0, r=0.011, hub=None):
    """the silk cords lacing a lame to the next: n of them evenly across it, standing on its face."""
    cords = []
    for k in range(n):
        a = math.radians(a0 + (a1 - a0) * (k + 0.5) / n)
        p0 = V_((math.sin(a) * (rx0 + 0.016), math.cos(a) * (ry0 + 0.016) * yk, z0)); p1 = V_((math.sin(a) * (rx1 + 0.016), math.cos(a) * (ry1 + 0.016) * yk, z1))
        cords.append(pipe([p0, p0.lerp(p1, 0.5), p1], [r, r, r], 5))
    ob = P.obj(name, bm_join(cords), slot) if hub is None else P.part(name, bm_join(cords), slot, tuple(hub))
    small(ob)


def plate_stack(P, name, origin, across, down, out, w, h, n, curve=0.0, flare=0.0, slot="Base", lace_slot="Accent", cords=8, hub=None):
    """a hanging armour piece (a sode, a skirt section of the kusazuri, the neck guard) built the real way: n lames, each a curved plate
    w wide and h / n deep, overlapping the one below, flaring out by flare toward the bottom, laced together by cords running down
    across all of them, a gold-capped top lame."""
    origin, across, down, out = V_(origin), V_(across).normalized(), V_(down).normalized(), V_(out).normalized()
    lh = h / n; plates, lace = [], []
    def put(bm, sl):
        if hub is None: return P.obj(name, bm, sl)
        return P.part(name, bm, sl, tuple(hub))
    for i in range(n):
        top = origin + down * (lh * i * 0.92) + out * (flare * (i / max(1, n - 1)) ** 1.3)
        quads = []
        for j in range(10):
            x0, x1 = -w / 2 + w * j / 10, -w / 2 + w * (j + 1) / 10
            def q(x, d): return tuple(top + across * x + down * d + out * (curve * (1 - (2 * x / w) ** 2) - 0.035 * d / lh))
            quads.append([q(x0, 0.0), q(x1, 0.0), q(x1, lh), q(x0, lh)])
        plates.append(st_cloth(quads, 0.022))
    put(bm_join(plates), slot)
    for k in range(cords):
        x = -w / 2 + w * (k + 0.5) / cords
        pts = [origin + across * x + down * (lh * i * 0.92 + lh * 0.5) + out * (flare * (i / max(1, n - 1)) ** 1.3 + curve * (1 - (2 * x / w) ** 2) + 0.018) for i in range(n)]
        if len(pts) < 3: pts = [pts[0], pts[0].lerp(pts[-1], 0.5), pts[-1]]
        lace.append(pipe(pts, [0.012] * len(pts), 5))
    small(put(bm_join(lace), lace_slot))
    put(pipe([origin + across * (-w / 2) + out * (curve * 0.0 + 0.012), origin + out * (curve + 0.012), origin + across * (w / 2) + out * 0.012], [0.02, 0.02, 0.02], 6), "Trim")


def katana(P, name, kashira, ax, edge, L=1.75, hub=None):
    """a katana by its hilt: the grip (tsuka) from the pommel up along ax, bound in a diamond wrap; the round gold guard; the gold collar;
    the blade curving back from the edge side (its sori), a diamond section, its tip (kissaki) - marked for the bake: "kh" 0 at the edge ..
    1 at the back (the temper line runs between), "ka" along it."""
    k0, ax = V_(kashira), V_(ax).normalized(); ed = V_(edge); ed = (ed - ax * ed.dot(ax)).normalized(); fl = ax.cross(ed)
    def put(bm, sl):
        if hub is None: return P.obj(name, bm, sl)
        return P.part(name, bm, sl, tuple(hub))
    TS = 0.32
    put(oriented_ball(k0, (0.032, 0.026, 0.04), *rh(ed, fl, ax), 10, 5), "Trim")                         # the pommel cap
    put(pipe([k0, k0 + ax * TS * 0.5, k0 + ax * TS], [0.03, 0.028, 0.03], 8), "Dark")                    # the grip
    wrap = []
    for i in range(8):   # the diamond wrap of silk cord over it
        t = (i + 0.5) / 8; c = k0 + ax * (TS * t)
        for sgn in (1, -1):
            wrap.append(pipe([c - ax * 0.018 + ed * (0.031 * sgn) , c + fl * 0.031, c + ax * 0.018 - ed * (0.031 * sgn)], [0.007] * 3, 4))
    small(put(bm_join(wrap), "Accent"))
    tb = k0 + ax * TS
    g = lathe([(0.0, -0.011), (0.085, -0.011), (0.09, -0.005), (0.09, 0.005), (0.085, 0.011), (0.0, 0.011)], 28, "z")
    m = Matrix((ed, fl, ax)).transposed(); xf(g, m, tuple(tb)); put(g, "Trim")
    put(pipe([tb + ax * 0.011, tb + ax * 0.05], [0.024, 0.022], 8), "Trim")                             # the collar
    bm = bmesh.new(); lh, la = bm.verts.layers.float.new("kh"), bm.verts.layers.float.new("ka"); rows = []; NB = 24
    for i in range(NB + 1):
        t = i / NB; s_ = tb + ax * (0.05 + L * t) - ed * (0.06 * t * t)                                   # the curve: the tip swept back
        wid = 0.034 * (1 - 0.35 * t) if t < 0.92 else 0.034 * 0.68 * (1 - (t - 0.92) / 0.08) ** 0.7
        th = 0.011 * (1 - 0.4 * t)
        if t >= 1.0: wid, th = 0.0005, 0.0005
        pts = [(s_ + ed * wid, 0.0), (s_ + fl * th, 0.62), (s_ - ed * wid, 1.0), (s_ - fl * th, 0.62)]   # edge, flat, back, flat
        row = []
        for p, kh in pts:
            v = bm.verts.new(p); v[lh] = kh; v[la] = t; row.append(v)
        rows.append(row)
    for r0, r1 in zip(rows, rows[1:]):
        for j in range(4): bm.faces.new((r0[j], r0[(j + 1) % 4], r1[(j + 1) % 4], r1[j]))
    bm.faces.new(list(reversed(rows[0]))); bm.faces.new(rows[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    put(bm, "Metal")
    return tb + ax * (0.05 + L)


def sensu(P, name, pivot, mid, nrm, R0=0.3, R1=1.35, spread=130.0, ribs=15, hub=None):
    """a great folding war fan opened: ribs of black lacquer from the gold rivet at the pivot, the paper leaf between R0 and R1 pleated into
    even mountain and valley folds, marked for the bake ("gu" across the fan 0..1, "gv" out along the ribs 0..1: the red sun painted on it,
    the gold borders)."""
    pivot, mid, nrm = V_(pivot), V_(mid).normalized(), V_(nrm).normalized(); side = nrm.cross(mid).normalized()
    def put(bm, sl):
        if hub is None: return P.obj(name, bm, sl)
        return P.part(name, bm, sl, tuple(hub))
    NA = (ribs - 1) * 2; NR = 8
    bm = bmesh.new(); lu, lv = bm.verts.layers.float.new("gu"), bm.verts.layers.float.new("gv"); grid = []
    for i in range(NA + 1):
        u = i / NA; a = math.radians(-spread / 2 + spread * u); d = mid * math.cos(a) + side * math.sin(a)
        fold = 0.035 * (1 if i % 2 else -1)                                                                 # the pleats
        row = []
        for j in range(NR + 1):
            v_ = j / NR; r = R0 + (R1 - R0) * v_
            vv = bm.verts.new(pivot + d * r + nrm * (fold * (r / R1)) - nrm * (0.08 * (r / R1) ** 2)); vv[lu] = u; vv[lv] = v_; row.append(vv)
        grid.append(row)
    for i in range(NA):
        for j in range(NR): bm.faces.new((grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=0.012)
    put(bm, "Belly")
    rb = []
    for k in range(ribs):
        a = math.radians(-spread / 2 + spread * k / (ribs - 1)); d = mid * math.cos(a) + side * math.sin(a)
        outer = (k == 0 or k == ribs - 1)
        rb.append(pipe([pivot + d * 0.05, pivot + d * (R0 * 0.6), pivot + d * (R1 * (1.0 if outer else 0.98))], [0.022 if outer else 0.016, 0.02 if outer else 0.013, 0.016 if outer else 0.01], 6))
    put(bm_join(rb), "Base")
    put(ring_on(pivot, nrm, 0.045, 0.02, 16, 6), "Trim"); put(oriented_ball(pivot, (0.04, 0.04, 0.03), *sq_axes(nrm), 12, 6), "Trim")


def J2_samurai():
    """THE SAMURAI SPIRIT (2026-10-14, remade like the alien / west / treasure / sea / meadow bosses): an empty suit of armour risen as a
    spirit, the armour built the way it really was. The helmet bowl of riveted plates, its ridges running up to the gold rosette at the top,
    the neck guard of laced lames flaring out behind with its turned-back wings at the front; the cuirass of lacquered lames laced together
    with red silk cords; the great shoulder guards hanging in laced lames; the skirt of the kusazuri in seven laced sections; armoured
    sleeves; and where a face should be, the red demon mask (menpo) snarling - nose, cheeks, teeth, a white horsehair moustache and beard -
    with blue spirit fire burning in its eyes and mouth, a laced throat guard under it.
    The cartoon idea kept: the black-and-gold armour with its golden kuwagata horns and crest, the katana raised (held in hasso, by the
    right shoulder, both hands on the hilt; a real katana - the diamond-bound grip, the round gold guard, the curved blade with its
    temper line), blue spirit flame twisting down where the legs should be, wisps of ghost fire circling him.
    He flies on two great war fans spread on his back like wings, the red sun painted on them - they beat (FlapL / FlapR)."""
    P = Boss("samurai", AB_pal(Base=((0.022, 0.022, 0.028), 0.4), Belly=((0.85, 0.8, 0.66), 0.4), Accent=((0.5, 0.015, 0.02), 0.5), Trim=((0.98, 0.72, 0.2), 0.7),
                               Glass=((0.2, 0.55, 1.0), 0.5), Dark=((0.02, 0.025, 0.05), 0.4), Glow=((0.35, 0.8, 1.0), 0.5), Metal=((0.74, 0.76, 0.8), 0.4),
                               Lamp=((0.75, 0.95, 1.0), 0.8)))
    glow_strength(P, 2.0)
    # ---- the cuirass (do): six lacquered lames round him laced in red, the gold-edged breast plate at the top
    zs = [-0.05, 0.12, 0.29, 0.46, 0.63, 0.8]
    def drx(z): return lerp_keys(z, [(-0.05, 0.42), (0.3, 0.45), (0.65, 0.52), (0.95, 0.5)])
    def dry(z): return lerp_keys(z, [(-0.05, 0.3), (0.3, 0.31), (0.65, 0.36), (0.95, 0.33)])
    lames = [lame_band(z, z + 0.19, drx(z) + 0.01, dry(z) + 0.01, drx(z + 0.19), dry(z + 0.19), seg=44) for z in zs]
    P.obj("Do", bm_join(lames), "Base")
    for z in zs: laced(P, "DoLace", z + 0.03, z + 0.16, drx(z), dry(z), drx(z + 0.16), dry(z + 0.16), -150, 150, 26)
    P.obj("Munaita", lame_band(0.95, 1.05, 0.5, 0.33, 0.36, 0.25, -60, 60, 20, 0.03), "Base")
    P.obj("MunaitaRim", pipe([V_((math.sin(math.radians(a)) * 0.5, math.cos(math.radians(a)) * 0.345, 0.96)) for a in range(-60, 61, 10)], [0.016] * 13, 6), "Trim")
    P.obj("DoCore", surf_grid(lambda z, a: V_((math.sin(a) * drx(z) * 0.97, math.cos(a) * dry(z) * 0.97, z)), 12, 32, -0.05, 1.0), "Dark")
    for s in (1, -1):   # gold fittings on the breast: two ring bosses for the cords
        P.obj("Kan", ring_on(V_((s * 0.18, 0.37, 0.9)), (0, 1, 0.2), 0.035, 0.012, 14, 5), "Trim")
    # ---- the kusazuri: seven laced sections hanging round his hips, flaring out
    for k in range(7):
        a = math.radians(-150 + 300 * k / 6); d = V_((math.sin(a), math.cos(a), 0.0)); acr = V_((math.cos(a), -math.sin(a), 0.0))
        org = V_((math.sin(a) * 0.43, math.cos(a) * 0.31, -0.06))
        plate_stack(P, "Kusazuri", org, acr, V_((0, 0, -1)), d, 0.34, 0.5, 5, 0.03, 0.14, cords=6)
    # ---- the shoulder guards (o-sode): six lames each, hanging from the shoulders and swung out
    for s in (1, -1):
        org = V_((s * 0.66, 0.0, 1.0)); acr = V_((0, 1, 0)); out = V_((s * 1.0, 0.0, 0.25)).normalized()
        plate_stack(P, "Sode", org, acr, (V_((s * 0.25, 0, -1.0))).normalized(), out, 0.46, 0.66, 6, 0.06, 0.1, cords=8)
    # ---- the arms: armoured sleeves (kote), black gloves on the hilt
    TK = V_((0.24, 0.43, 0.84)); TAX = V_((0.2, -0.12, 1.0)).normalized()
    for s, (sh, el, wr, g) in ((1, (V_((0.55, 0.0, 0.92)), V_((0.74, 0.26, 0.74)), TK + TAX * 0.22 + V_((0.06, -0.02, -0.04)), TK + TAX * 0.25)),
                               (-1, (V_((-0.55, 0.0, 0.92)), V_((-0.4, 0.42, 0.6)), TK + TAX * 0.06 + V_((-0.06, 0.0, -0.04)), TK + TAX * 0.09))):
        P.obj("Kote", limb(sh, el, 0.13, 0.11), "Dark"); P.obj("Kote", ball(tuple(el), (0.115, 0.115, 0.115), 12, 6), "Dark")
        P.obj("Kote", limb(el, wr, 0.11, 0.085), "Dark")
        for k in range(4):   # the gold-edged plates down the forearm
            t = 0.15 + 0.2 * k; c = el.lerp(wr, t); d = (wr - el).normalized()
            P.obj("KotePlate", ring_on(c, d, 0.105 - 0.006 * k, 0.018, 16, 5), "Trim" if k % 3 == 0 else "Base")
        fist(P, g, TAX, V_((0.55, 0.85, -0.1)), 0.95, 0.03, "Glove", None, "Dark", "Trim")
    tip = katana(P, "Katana", TK, TAX, V_((0.95, 0.3, 0.0)), 1.45)   # (its flat to you, so the blade and its temper line show)
    # ---- the helmet: the riveted bowl and its ridges, the gold rosette, the visor, the neck guard of laced lames, the turned-back wings
    HC = V_((0, 0.0, 1.4))
    P.obj("Kabuto", lathe([(0.0, 0.3), (0.12, 0.28), (0.22, 0.22), (0.29, 0.12), (0.31, 0.0), (0.3, -0.03)], 40, "z", tuple(HC)), "Base")
    ridges = []
    for k in range(32):
        a = 2 * math.pi * k / 32
        ridges.append(pipe([HC + V_((math.sin(a) * r, math.cos(a) * r, z)) for r, z in ((0.075, 0.296), (0.16, 0.262), (0.235, 0.205), (0.29, 0.11), (0.312, 0.0))], [0.009] * 5, 4))
    small(P.obj("KabutoRidge", bm_join(ridges), "Base"))
    P.obj("Tehen", lathe([(0.0, 0.33), (0.05, 0.32), (0.08, 0.3), (0.06, 0.29)], 24, "z", tuple(HC)), "Trim")
    P.obj("Mabizashi", lame_band(1.41, 1.36, 0.33, 0.33, 0.37, 0.4, -70, 70, 24, 0.02), "Base")
    P.obj("MabizashiRim", pipe([V_((math.sin(math.radians(a)) * 0.37, math.cos(math.radians(a)) * 0.4, 1.36)) for a in range(-70, 71, 10)], [0.013] * 15, 5), "Trim")
    for i in range(4):   # the neck guard (shikoro): four lames flaring out round the back and sides
        z = 1.36 - 0.075 * i; r0, r1 = 0.32 + 0.06 * i, 0.38 + 0.06 * i
        P.obj("Shikoro", lame_band(z, z - 0.09, r0, r0, r1, r1, 70, 290, 40, 0.022), "Base")
        laced(P, "ShikoroLace", z - 0.01, z - 0.08, r0, r0, r1, r1, 72, 288, 22)
    for s in (1, -1):   # the turned-back wings (fukigaeshi), a gold mon on each
        b = V_((s * 0.33, 0.24, 1.32))
        plate_stack(P, "Fukigaeshi", b, V_((s * 0.5, 0.86, 0.0)), V_((0, 0, -1)), V_((s * 0.86, -0.5, 0.0)), 0.16, 0.22, 3, 0.02, 0.04, cords=3)
        P.obj("Mon", ring_on(b + V_((s * 0.06, 0.04, -0.1)), (s * 0.86, -0.5, 0.0), 0.04, 0.012, 14, 5), "Trim")
    # the golden kuwagata horns and the crest between them: a gold sun
    for s in (1, -1):
        b = HC + V_((s * 0.08, 0.31, 0.06))
        hp = bez(b, b + V_((s * 0.1, 0.06, 0.22)), b + V_((s * 0.34, 0.06, 0.45)), b + V_((s * 0.46, -0.02, 0.72)), 12)
        P.obj("Kuwagata", flat_pipe(hp, [0.045, 0.05, 0.052, 0.05, 0.047, 0.043, 0.039, 0.034, 0.028, 0.022, 0.015, 0.008, 0.0], V_((0, 1, 0)), 0.75, 8), "Trim")
    P.obj("Maedate", oriented_ball(HC + V_((0, 0.34, 0.14)), (0.085, 0.02, 0.085), V_((1, 0, 0)), V_((0, 1, 0)), V_((0, 0, 1)), 24, 6), "Trim")
    rays = [cone(HC + V_((math.sin(a) * 0.085, 0.34, 0.14 + math.cos(a) * 0.085)), HC + V_((math.sin(a) * 0.15, 0.335, 0.14 + math.cos(a) * 0.15)), 0.022, 4)
            for a in [2 * math.pi * k / 12 for k in range(12)]]
    P.obj("Maedate", bm_join(rays), "Trim")
    # ---- the red demon mask (menpo) where the face should be: the fire of the spirit burning in its eyes and mouth
    MC = HC + V_((0, 0.2, -0.25))
    P.obj("Void", oriented_ball(HC + V_((0, 0.05, -0.05)), (0.26, 0.24, 0.26), V_((1, 0, 0)), V_((0, 1, 0)), V_((0, 0, 1)), 18, 9), "Dark")
    P.obj("Menpo", oriented_ball(MC, (0.21, 0.12, 0.16), V_((1, 0, 0)), V_((0, 1, 0)), V_((0, 0, 1)), 22, 11), "Accent")
    P.obj("MenpoNose", tube_rmf(bez(MC + V_((0, 0.105, 0.12)), MC + V_((0, 0.15, 0.09)), MC + V_((0, 0.175, 0.03)), MC + V_((0, 0.15, -0.0)), 8),
                                [0.022, 0.03, 0.036, 0.042, 0.046, 0.045, 0.038, 0.026, 0.0], 10), "Accent")
    for s in (1, -1):
        P.obj("MenpoNose", oriented_ball(MC + V_((s * 0.032, 0.13, 0.005)), (0.028, 0.03, 0.022), V_((1, 0, 0)), V_((0, 1, 0)), V_((0, 0, 1)), 10, 5), "Accent")
    for s in (1, -1):
        cx = V_((math.cos(math.radians(25)), 0.0, s * math.sin(math.radians(25))))
        P.obj("MenpoCheek", oriented_ball(MC + V_((s * 0.12, 0.085, 0.03)), (0.09, 0.035, 0.05), *rh(cx, V_((0, 1, 0)), cx.cross(V_((0, 1, 0)))), 14, 7), "Accent")
        P.obj("MenpoWrinkle", tube_rmf(bez(MC + V_((s * 0.04, 0.15, 0.0)), MC + V_((s * 0.09, 0.14, -0.03)), MC + V_((s * 0.13, 0.11, -0.06)), MC + V_((s * 0.16, 0.06, -0.09)), 6),
                                       [0.012, 0.015, 0.015, 0.012, 0.009, 0.005, 0.0], 6), "Accent")
        ec = HC + V_((s * 0.1, 0.27, -0.06))
        P.obj("EyeFire", oriented_ball(ec, (0.06, 0.03, 0.03), *rh(V_((math.cos(math.radians(14)), 0, s * math.sin(math.radians(14)))), V_((0, 1, 0)),
                                                                     V_((-s * math.sin(math.radians(14)), 0, math.cos(math.radians(14))))), 14, 7), "Lamp")
    P.obj("MenpoMouth", oriented_ball(MC + V_((0, 0.1, -0.085)), (0.12, 0.035, 0.05), V_((1, 0, 0)), V_((0, 1, 0)), V_((0, 0, 1)), 16, 8), "Glass")
    teeth = [box(tuple(MC + V_((x, 0.128, -0.05))), (0.02, 0.012, 0.026)) for x in [-0.075 + 0.025 * i for i in range(7)]]
    teeth += [box(tuple(MC + V_((x, 0.122, -0.122))), (0.02, 0.012, 0.024)) for x in [-0.062 + 0.031 * i for i in range(5)]]
    teeth += [cone(MC + V_((s * 0.09, 0.125, -0.045)), MC + V_((s * 0.09, 0.127, -0.115)), 0.014, 5) for s in (1, -1)]
    P.obj("Teeth", bm_join(teeth), "Trim")
    hair = []
    for s in (1, -1):   # the white horsehair moustache sweeping out and down, the beard below
        for k in range(5):
            b = MC + V_((s * (0.02 + 0.025 * k), 0.13, -0.02 + 0.004 * k))
            hair.append(tube_rmf(bez(b, b + V_((s * 0.07, 0.03, 0.0)), b + V_((s * 0.15, 0.02, -0.06)), b + V_((s * 0.2, -0.02, -0.16 - 0.02 * k)), 6),
                                 [0.012, 0.014, 0.013, 0.011, 0.008, 0.005, 0.0], 5))
    for k in range(9):
        x = -0.12 + 0.03 * k; b = MC + V_((x, 0.06, -0.15))
        hair.append(tube_rmf(bez(b, b + V_((x * 0.2, 0.03, -0.1)), b + V_((x * 0.4, 0.0, -0.22)), b + V_((x * 0.5, -0.04, -0.34 + 0.06 * abs(x) / 0.12)), 6),
                             [0.014, 0.015, 0.014, 0.012, 0.009, 0.005, 0.0], 5))
    P.obj("Beard", bm_join(hair), "Belly")
    for i in range(3):   # the throat guard (yodare-kake): three laced lames under the mask
        z = MC.z - 0.16 - 0.06 * i
        P.obj("Yodare", lame_band(z, z - 0.065, 0.2 + 0.03 * i, 0.2 + 0.03 * i, 0.23 + 0.03 * i, 0.23 + 0.03 * i, -80, 80, 20, 0.018, yk=1.1), "Base")
        laced(P, "YodareLace", z - 0.01, z - 0.055, 0.2 + 0.03 * i, 0.2 + 0.03 * i, 0.23 + 0.03 * i, 0.23 + 0.03 * i, -76, 76, 12, yk=1.1)
    # ---- the spirit fire twisting down where his legs should be: five strands of blue flame wound round each other to a point
    for k in range(5):
        a0 = 2 * math.pi * k / 5; pts = []
        for i in range(25):
            t = i / 24; a = a0 + t * 2.4; r = 0.36 * (1 - t) ** 1.2 + 0.02
            pts.append(V_((math.sin(a) * r, math.cos(a) * r * 0.85, -0.3 - 1.25 * t)))
        P.obj("SpiritFire", tube_rmf(pts, [0.16 * (1 - (i / 24) ** 0.9) + 0.004 for i in range(24)] + [0.0], 10), lambda c, n: "Lamp" if c.z > -0.65 else "Glow")
    # ---- the two great war fans on his back, spread like wings, the red sun on each - they beat
    for s in (1, -1):
        name = "FlapR" if s > 0 else "FlapL"; pv = V_((s * 0.22, -0.4, 0.98))
        mid = V_((s * 0.82, -0.18, 0.55)).normalized(); nrm = V_((0, 1, 0)) - mid * mid.y; nrm.normalize()
        P.part(name, pipe([V_((s * 0.12, -0.3, 0.9)), pv], [0.03, 0.03], 6), "Base", tuple(pv))
        sensu(P, name, pv, mid, nrm, 0.32, 1.45, 110.0, 15, pv)
    # ---- wisps of ghost fire circling him: little flames with tails
    ws = []
    for k in range(8):
        a = 2 * math.pi * k / 8; c = V_((math.sin(a) * 1.6, math.cos(a) * 1.3, 0.5 + 0.35 * math.sin(a * 2)))
        tg = V_((math.cos(a), -math.sin(a), 0.0))
        ws.append(ball(tuple(c), (0.085, 0.085, 0.085), 10, 5))
        ws.append(tube_rmf(bez(c - tg * 0.04, c - tg * 0.16 + V_((0, 0, 0.05)), c - tg * 0.28 + V_((0, 0, 0.02)), c - tg * 0.4 + V_((0, 0, 0.08)), 6), [0.075, 0.065, 0.05, 0.035, 0.02, 0.008, 0.0], 8))
    P.part("SpinWisps", bm_join(ws), "Glow", (0, 0, 0.5))
    mz = MC + V_((0, 0.09, -0.085))   # (inside the mouth)
    P.part("Muzzle", ball(tuple(mz), (0.012, 0.012, 0.012), 6, 3), "Dark", tuple(mz))
    return P


def serpent(pts, radii, seg=24, flat=0.86):
    """a serpent's body along pts (radius per point), its rings carried by parallel transport and turned so that each ring's angle 0 lies
    on the belly (world down, seen square to the body); the belly a little flattened. Marked for the bake: "su" the length along the body
    in units of its own radius (scales stay in proportion as it thins), "sv" round it (0 the belly .. 0.5 the spine .. 1). Returns the mesh
    and per point (centre, tangent, belly direction, radius)."""
    pts = [V_(p) for p in pts]; n = len(pts)
    tg = [(pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]).normalized() for i in range(n)]
    bel = []; prev = None
    for i in range(n):
        d = V_((0, 0, -1)) - tg[i] * (-tg[i].z)
        if d.length < 0.25 and prev is not None: d = prev - tg[i] * prev.dot(tg[i])
        d.normalize()
        if prev is not None and d.dot(prev) < 0.2: d = (prev - tg[i] * prev.dot(tg[i])).normalized().lerp(d, 0.3).normalized()
        bel.append(d); prev = d
    for _ in range(3):   # smoothed so the belly never twists sharply
        bel = [((bel[max(0, i - 1)] + bel[i] * 2 + bel[min(n - 1, i + 1)]) - tg[i] * (bel[max(0, i - 1)] + bel[i] * 2 + bel[min(n - 1, i + 1)]).dot(tg[i])).normalized() for i in range(n)]
    bm = bmesh.new(); lu, lv = bm.verts.layers.float.new("su"), bm.verts.layers.float.new("sv"); rings = []; su = 0.0
    for i in range(n):
        if i: su += (pts[i] - pts[i - 1]).length / max(0.02, (radii[i] + radii[i - 1]) * 0.5)
        b = bel[i]; sd = tg[i].cross(b)
        if radii[i] < 1e-5: rings.append([bm.verts.new(pts[i])]); continue
        ring = []
        for k in range(seg):
            a = 2 * math.pi * k / seg; r = radii[i] * (flat if math.cos(a) > 0 else 1.0) ** abs(math.cos(a))
            v = bm.verts.new(pts[i] + (b * math.cos(a) + sd * math.sin(a)) * r); v[lu] = su; v[lv] = k / seg; ring.append(v)
        rings.append(ring)
    rings = [[bm.verts.new(pts[0])]] + rings
    return skin(bm, rings, seg, cap=False), list(zip(pts, tg, bel, radii))


def J2_ryu():
    """THE SKY DRAGON (2026-10-14, remade like the alien / west / treasure / sea / meadow bosses): a Japanese ryu built the way the old
    painters built one - out of real animals (the nine resemblances): a camel's long head, a stag's antlers, a cow's ears, a carp's
    barbels for whiskers, a serpent's long neck and body, the carp's scales over it in even rows, a clam's belly of golden plates, the
    eagle's claws - three to a foot, as a Japanese dragon has them - and a tiger's pads. He comes at you with his jaws open, fangs bared,
    the tongue lashing, glaring from under bushy brows; the crimson mane flows back down his neck, the spiny crest runs down his back, and
    tufts of flame burn at his elbows.
    The cartoon idea kept: the jade dragon in coils, golden belly, crimson mane, golden antlers and whiskers, four clawed legs, the glowing
    pearl in his foremost claw, a flame tuft at the tail.
    He flies as dragons fly in the paintings: swimming through the clouds - billows of cloud wrapped round his coils, more of them
    turning round him (SpinClouds); his whiskers stream (Sway)."""
    P = Boss("ryu", AB_pal(Base=((0.03, 0.24, 0.13), 0.45), Belly=((0.86, 0.6, 0.18), 0.5), Accent=((0.55, 0.02, 0.025), 0.5), Trim=((0.98, 0.72, 0.2), 0.7),
                           Glass=((0.95, 0.92, 0.82), 0.5), Dark=((0.02, 0.02, 0.02), 0.4), Glow=((1.0, 0.45, 0.08), 0.5), Metal=((0.78, 0.8, 0.86), 0.5),
                           Lamp=((1.0, 0.68, 0.08), 0.8)))
    glow_strength(P, 2.0)
    # ---- the body: head toward you, the neck curving down and back into coils that ring the head, the tail curling away
    ctrl = [(0, 1.18, 0.55), (0, 0.85, 0.4), (0.15, 0.45, 0.05), (0.75, 0.1, -0.3), (1.15, -0.4, 0.2), (0.85, -0.85, 0.95), (0.0, -0.95, 1.25),
            (-0.85, -0.7, 0.85), (-1.15, -0.15, 0.1), (-0.7, 0.2, -0.55), (0.1, 0.0, -0.85), (0.85, -0.35, -0.75), (1.4, -0.75, -0.3), (1.65, -1.0, 0.15)]
    sp = st_spline([V_(c) for c in ctrl], 7); NS = len(sp)
    rad = [lerp_keys(i / (NS - 1), [(0, 0.2), (0.08, 0.22), (0.2, 0.27), (0.45, 0.25), (0.75, 0.16), (0.92, 0.08), (1, 0.025)]) for i in range(NS)]
    body, fr = serpent(sp, rad, 26)
    P.obj("Body", body, "Base")
    # the belly's golden plates: a broad band of transverse scutes along the underside, evenly spaced
    scutes = []
    for i in range(2, NS - 4, 2):
        c, t, b, r = fr[i]; sd = t.cross(b)
        arc = [c + (b * math.cos(a) + sd * math.sin(a)) * (r * 1.03 * (0.86 if math.cos(a) > 0 else 1.0) ** abs(math.cos(a))) for a in [math.radians(-55 + 110 * k / 8) for k in range(9)]]
        scutes.append(tube_rmf(arc, [r * 0.11] * 9, 6))
    P.obj("Scute", bm_join(scutes), "Belly")
    # the spiny crest down his back: carp-fin spines, longest behind the head, every one webbed to the next
    crest, mane = [], []
    for i in range(10, NS - 3, 3):
        c, t, b, r = fr[i]; up = -b; L = 0.1 + 0.22 * rad[i] / 0.27
        base = c + up * (r * 0.92)
        crest.append(st_cloth([[tuple(base + t * (L * 0.35)), tuple(base + up * L - t * (L * 0.55)), tuple(base - t * (L * 0.45))]], 0.02))
    P.obj("Crest", bm_join(crest), "Accent")
    # ---- the head (a camel's long one), built along its own axis
    HC = V_((0, 1.28, 0.6)); fwd = V_((0, 0.95, -0.28)).normalized(); hx = V_((1, 0, 0)); hz = hx.cross(fwd).normalized()
    n0, s0 = len(P.parts), len(P.spin)
    def hp(x, y, z): return HC + hx * x + fwd * y + hz * z
    g = math.radians(48); jd = (fwd * math.cos(g) - hz * math.sin(g)).normalized(); jz = (hz * math.cos(g) + fwd * math.sin(g)).normalized(); JH = hp(0, 0.02, -0.1)
    def jp(x, y, z): return JH + hx * x + jd * y + jz * z          # the lower jaw, dropped open
    P.obj("Head", oriented_ball(hp(0, 0.0, 0.03), (0.21, 0.26, 0.19), *rh(hx, fwd, hz), 24, 12), "Base")
    P.obj("Snout", tube_rmf([hp(0, 0.1, 0.02), hp(0, 0.26, 0.0), hp(0, 0.4, -0.01), hp(0, 0.5, 0.0)], [0.16, 0.14, 0.125, 0.11], 18), "Base")
    P.obj("NosePad", oriented_ball(hp(0, 0.5, 0.03), (0.15, 0.07, 0.065), *rh(hx, fwd, hz), 16, 8), "Base")
    curls = []
    for s_ in (1, -1):   # the nostrils, curled like the painted ones
        nc = hp(s_ * 0.075, 0.5, 0.075)
        curls.append(tube_rmf([nc + (hx * math.cos(a_) * s_ + fwd * math.sin(a_)) * (0.042 - 0.012 * k / 10) + hz * 0.01 for k, a_ in enumerate([math.radians(-40 + 300 * k / 10) for k in range(11)])],
                              [0.016] * 10 + [0.008], 8))
        P.obj("Nostril", oriented_ball(nc + hz * 0.005, (0.024, 0.02, 0.012), *rh(hx, fwd, hz), 10, 5), "Dark")
    P.obj("NostrilRim", bm_join(curls), "Base")
    P.obj("LowerJaw", tube_rmf([jp(0, 0.04, -0.03), jp(0, 0.2, -0.06), jp(0, 0.36, -0.07), jp(0, 0.46, -0.06)], [0.13, 0.11, 0.085, 0.065], 16), "Base")
    P.obj("Mouth", oriented_ball(hp(0, 0.24, -0.16), (0.1, 0.22, 0.1), *rh(hx, (fwd + jd).normalized(), (hz + jz).normalized()), 18, 9), "Accent")
    P.obj("Tongue", tube_rmf(bez(jp(0, 0.08, 0.0), jp(0, 0.35, 0.02), jp(0, 0.55, -0.02) - hz * 0.05, jp(0, 0.62, -0.08) - hz * 0.2, 10),
                             [0.04, 0.042, 0.042, 0.04, 0.036, 0.03, 0.025, 0.02, 0.014, 0.008, 0.0], 8), "Accent")
    teeth = []
    for s_ in (1, -1):
        for k in range(5):   # the rows of teeth, upper and lower, the fangs at the front
            y = 0.14 + 0.07 * k; x = s_ * (0.09 - 0.01 * k)
            teeth.append(cone(hp(x, y, -0.075), hp(x, y + 0.005, -0.125), 0.014, 5))
            teeth.append(cone(jp(x * 0.95, y - 0.02, 0.02), jp(x * 0.95, y - 0.015, 0.07), 0.013, 5))
        teeth.append(cone(hp(s_ * 0.075, 0.45, -0.06), hp(s_ * 0.08, 0.47, -0.24), 0.032, 6))     # the great fangs above
        teeth.append(cone(jp(s_ * 0.05, 0.42, 0.0), jp(s_ * 0.055, 0.44, 0.16), 0.028, 6))       # and below
    P.obj("Tooth", bm_join(teeth), "Glass")
    for s in (1, -1):
        ec = hp(s * 0.135, 0.1, 0.13)
        P.obj("Eye", oriented_ball(ec, (0.066, 0.07, 0.056), *rh(hx, fwd, hz), 18, 9), "Lamp")
        P.obj("EyeRim", ring_on(ec + fwd * 0.03 + hx * (s * 0.012), fwd + hx * (s * 0.5), 0.062, 0.014, 20, 5), "Accent")
        P.obj("Pupil", oriented_ball(ec + hx * (s * 0.025) + fwd * 0.05, (0.01, 0.012, 0.045), *rh(hx, fwd, hz), 8, 4), "Dark")
        # the bushy brow, drawn down hard at the inner end; tufts of it flaring up and back
        bw = bez(hp(s * 0.05, 0.2, 0.13), hp(s * 0.12, 0.17, 0.18), hp(s * 0.19, 0.08, 0.21), hp(s * 0.22, -0.02, 0.26), 8)
        P.obj("Brow", tube_rmf(bw, [0.03, 0.038, 0.042, 0.044, 0.042, 0.038, 0.03, 0.02, 0.0], 10), "Accent")
        for k in range(4):
            q = bw[2 + k]; P.obj("Brow", cone(q, q + hz * 0.08 - fwd * 0.12 + hx * (s * 0.03), 0.022, 6), "Accent")
        P.obj("Ear", oriented_ball(hp(s * 0.18, -0.12, 0.1), (0.04, 0.1, 0.06), *rh(hx, fwd, hz), 10, 5), "Base")
        # the stag's antlers, gold, sweeping back with their tines
        ab = hp(s * 0.09, -0.05, 0.16)
        ant = bez(ab, ab + hz * 0.2 + hx * (s * 0.05), ab + hz * 0.38 - fwd * 0.25 + hx * (s * 0.14), ab + hz * 0.5 - fwd * 0.55 + hx * (s * 0.22), 10)
        P.obj("Antler", tube_rmf(ant, [0.045 - 0.004 * i for i in range(10)] + [0.0], 10), "Trim")
        for k, (L, d) in enumerate(((0.17, hz * 0.8 + fwd * 0.5 + hx * (s * 0.2)), (0.15, hz * 0.9 + fwd * 0.2 + hx * (s * 0.3)), (0.12, hz * 0.7 - fwd * 0.2 + hx * (s * 0.5)))):
            q = ant[3 + 2 * k]; P.obj("Antler", tube_rmf(bez(q, q + d.normalized() * (L * 0.4), q + d.normalized() * (L * 0.8) + hz * 0.02, q + d.normalized() * L, 4), [0.025, 0.02, 0.014, 0.008, 0.0], 8), "Trim")
        # the carp's barbels: long whiskers from the upper lip, streaming back in an S (they sway)
        wb = hp(s * 0.1, 0.5, -0.02); name = "SwayWhiskerR" if s > 0 else "SwayWhiskerL"
        wk = bez(wb, wb + hx * (s * 0.35) + fwd * 0.12 + hz * 0.05, wb + hx * (s * 0.7) - fwd * 0.45 - hz * 0.15, wb + hx * (s * 1.05) - fwd * 0.75 + hz * 0.15, 16)
        P.part(name, tube_rmf(wk, [0.026 - 0.0014 * i for i in range(16)] + [0.0], 8), "Trim", tuple(wb))
        # the beard tufts under the chin, the cheek frills
        for k in range(3):
            q = jp(s * (0.04 + 0.04 * k), 0.3 - 0.07 * k, -0.1)
            P.obj("Beard", tube_rmf(bez(q, q - hz * 0.08, q - hz * 0.16 - fwd * 0.05, q - hz * 0.24 - fwd * 0.12 + hx * (s * 0.02), 6), [0.03, 0.03, 0.026, 0.02, 0.014, 0.008, 0.0], 8), "Accent")
        for k in range(4):
            q = hp(s * 0.17, -0.02 - 0.06 * k, -0.04 + 0.03 * k)
            P.obj("Frill", cone(q, q + hx * (s * 0.12) - fwd * 0.14 - hz * 0.04, 0.035, 6), "Accent")
    grow_since(P, n0, s0, HC, 1.4)
    # the crimson mane: flowing back from the head down the neck, locks of it in even rows
    for i in range(1, 16):
        c, t, b, r = fr[i]; up = -b; sd = t.cross(b)
        for j in (-1, 0, 1):
            base = c + up * (r * 0.85) + sd * (j * r * 0.45)
            mane.append(tube_rmf(bez(base, base + up * 0.1 - t * 0.08 + sd * (j * 0.05), base + up * 0.18 - t * 0.2 + sd * (j * 0.1), base + up * 0.16 - t * 0.34 + sd * (j * 0.16), 6),
                                 [0.05, 0.048, 0.042, 0.034, 0.024, 0.012, 0.0], 8))
    P.obj("Mane", bm_join(mane), "Accent")
    # ---- four legs: a tiger's limbs with flame tufts at the elbows, three eagle's talons to a foot; the foremost one holds the pearl
    PEARL = None
    for idx, s, reach in ((22, 1, True), (22, -1, False), (68, 1, False), (68, -1, False)):
        c, t, b, r = fr[idx]; sd = t.cross(b) * (1 if t.cross(b).x * s > 0 else -1)
        sh = c + sd * (r * 0.7) + b * (r * 0.3)
        el = sh + sd * 0.22 + b * 0.18 + t * 0.12
        wr = (el + sd * 0.05 + b * 0.05 + V_((0, 0.35, 0.25))) if reach else (el + sd * 0.06 + b * 0.22 - t * 0.1)
        P.obj("Leg", limb(sh, el, 0.1, 0.075, [(0.45, 0.3, 0.0, 0.8, 0.18)]), "Base")
        P.obj("Leg", ball(tuple(el), (0.075, 0.075, 0.075), 10, 5), "Base")
        P.obj("Leg", limb(el, wr, 0.07, 0.05), "Base")
        for k in range(3):   # the flame tuft at the elbow
            P.obj("ElbowFlame", tube_rmf(bez(el, el - t * 0.08 + sd * 0.04 + b * (0.03 * (k - 1)), el - t * 0.18 + sd * 0.02 + b * (0.06 * (k - 1)), el - t * 0.28 + b * (0.05 * (k - 1)) - sd * 0.02, 6),
                                         [0.035, 0.032, 0.026, 0.02, 0.013, 0.007, 0.0], 8), "Accent")
        fd = (wr - el).normalized(); pd = (b if not reach else V_((0, 0, 1))); pd = (pd - fd * pd.dot(fd)).normalized()
        P.obj("Foot", oriented_ball(wr + fd * 0.04, (0.05, 0.065, 0.035), *rh(fd.cross(pd).normalized(), fd, pd), 10, 5), "Base")
        cc = wr + fd * 0.14 + pd * 0.06 if reach else None
        for k in (-1, 0, 1):   # three eagle's toes, scaled, each ending in a hooked golden talon
            td = (fd + fd.cross(pd).normalized() * (0.45 * k)).normalized()
            if reach:
                e1 = (wr + fd * 0.04 - cc).normalized(); e2 = (td - e1 * e1.dot(td)).normalized()
                toe = [cc + (e1 * math.cos(th) + e2 * math.sin(th)) * 0.13 for th in [math.radians(15 + 105 * j / 5) for j in range(6)]]
            else:
                toe = bez(wr + fd * 0.06, wr + fd * 0.11 + td * 0.06, wr + fd * 0.1 + td * 0.12 + pd * 0.05, wr + fd * 0.06 + td * 0.15 + pd * 0.1, 5)
            P.obj("Toe", tube_rmf(toe, [0.022, 0.021, 0.02, 0.018, 0.016, 0.013], 8), "Base")
            tp = toe[-1]; tdd = (toe[-1] - toe[-2]).normalized()
            P.obj("Talon", tube_rmf(bez(tp, tp + tdd * 0.03, tp + tdd * 0.06 + pd * 0.02, tp + tdd * 0.07 + pd * 0.05, 4), [0.016, 0.013, 0.009, 0.005, 0.0], 6), "Trim")
        if reach: PEARL = cc
    # the flaming pearl (the tama) in his foremost claw
    P.obj("Pearl", ball(tuple(PEARL), (0.115, 0.115, 0.115), 20, 10), "Lamp")
    for k in range(7):
        a = 2 * math.pi * k / 7
        P.obj("PearlFlame", tube_rmf(bez(PEARL + V_((math.sin(a) * 0.1, math.cos(a) * 0.1, 0.03)), PEARL + V_((math.sin(a) * 0.17, math.cos(a) * 0.17, 0.12)),
                                         PEARL + V_((math.sin(a + 0.4) * 0.14, math.cos(a + 0.4) * 0.14, 0.24)), PEARL + V_((math.sin(a + 0.7) * 0.08, math.cos(a + 0.7) * 0.08, 0.34)), 8),
                                     [0.04, 0.042, 0.04, 0.035, 0.028, 0.02, 0.012, 0.006, 0.0], 8), "Glow")
    # the flame tuft at the tail's end
    c, t, b, r = fr[-2]
    for k in range(5):
        a = math.radians(-50 + 25 * k); sd = t.cross(b)
        P.obj("TailFlame", tube_rmf(bez(c, c + t * 0.15 + sd * (math.sin(a) * 0.08), c + t * 0.3 + sd * (math.sin(a) * 0.18) - b * 0.05, c + t * 0.45 + sd * (math.sin(a) * 0.22) - b * (0.12 - 0.03 * abs(k - 2)), 6),
                                    [0.04, 0.04, 0.034, 0.026, 0.017, 0.008, 0.0], 8), "Accent")
    # ---- the clouds he swims through: billows wrapped round his coils, the painted curl on each
    for i in (34, 52, 84):
        c, t, b, r = fr[i]; sd = t.cross(b); puffs = []
        for k in range(5):
            a = 2 * math.pi * k / 5
            puffs.append(ball(tuple(c + (b * math.cos(a) + sd * math.sin(a)) * (r * 1.25) + b * 0.06), (r * 0.95,) * 3, 14, 7))
        P.obj("Cloud", bm_join(puffs), "Metal")
        cc_ = c + b * (r * 1.6) + V_((0, 0.05, 0)); spl = []
        for j in range(31):
            u = j / 30.0; a = math.pi * 0.5 + 2.4 * math.pi * u; rr = 0.12 * (1 - 0.8 * u)
            spl.append(cc_ + V_((math.cos(a) * rr, 0.0, math.sin(a) * rr)))
        P.obj("CloudCurl", tube_rmf(spl, [0.045 * (1 - 0.6 * j / 30) for j in range(30)] + [0.0], 8), "Metal")
    cl = []
    for k in range(6):   # and more turning round him
        a = 2 * math.pi * k / 6 + 0.3; c = V_((math.sin(a) * 2.0, -0.2 + math.cos(a) * 1.7, -0.6 + 0.25 * math.sin(a * 2)))
        for j in range(3):
            cl.append(ball(tuple(c + V_((math.cos(a) * (j - 1) * 0.22, -math.sin(a) * (j - 1) * 0.22, 0.06 * (j % 2)))), (0.2 - 0.04 * abs(j - 1), 0.17, 0.14), 12, 6))
    P.part("SpinClouds", bm_join(cl), "Metal", (0, -0.2, -0.6))
    mz = HC + (hp(0, 0.42, -0.18) - HC) * 1.4
    P.part("Muzzle", ball(tuple(mz), (0.015, 0.015, 0.015), 6, 3), "Dark", tuple(mz))
    return P


def piston(a, b, r, frac=0.58):
    """a hydraulic ram from a to b: the cylinder (frac of the way), the polished rod out of it, an eye at each end."""
    a, b = V_(a), V_(b); d = (b - a); L = d.length; d = d / L; m = a + d * (L * frac)
    parts = [pipe([a, a.lerp(m, 0.5), m], [r, r, r], 10), pipe([m - d * 0.01, b], [r * 0.45, r * 0.45], 8), ring_on(m, d, r * 1.02, r * 0.18, 12, 4)]
    u, v = frame(d)
    for p in (a, b): parts.append(oriented_ball(p, (r * 0.9, r * 0.9, r * 0.6), *rh(u, d, v), 10, 5))
    return bm_join(parts)


def bell(c, d, r0, r1, L, seg=24):
    """a rocket engine's bell: from its throat (radius r0, at c) widening along d to its mouth (r1) over L, a cooling-tube band at the
    throat; open at the mouth."""
    c, d = V_(c), V_(d).normalized(); u, v = frame(d)
    bm = bmesh.new(); rings = []
    for i in range(13):
        t = i / 12; r = r0 + (r1 - r0) * t ** 1.6
        rings.append([bm.verts.new(c + d * (L * t) + (u * math.cos(2 * math.pi * k / seg) + v * math.sin(2 * math.pi * k / seg)) * r) for k in range(seg)])
    inner = [[bm.verts.new(c + d * (L * t) + (u * math.cos(2 * math.pi * k / seg) + v * math.sin(2 * math.pi * k / seg)) * ((r0 + (r1 - r0) * t ** 1.6) * 0.9)) for k in range(seg)] for t in [i / 12 for i in range(13)]]
    for r_a, r_b in zip(rings, rings[1:]):
        for k in range(seg): bm.faces.new((r_a[k], r_a[(k + 1) % seg], r_b[(k + 1) % seg], r_b[k]))
    for r_a, r_b in zip(inner, inner[1:]):
        for k in range(seg): bm.faces.new((r_a[k], r_b[k], r_b[(k + 1) % seg], r_a[(k + 1) % seg]))
    for k in range(seg): bm.faces.new((rings[-1][k], rings[-1][(k + 1) % seg], inner[-1][(k + 1) % seg], inner[-1][k]))
    bm.faces.new(list(reversed(rings[0])))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def jet(P, name, c, d, r, L, hub=None):
    """the jet out of a bell: a white-hot core in a long flame, tapering away, a shock diamond in it."""
    c, d = V_(c), V_(d).normalized()
    def put(bm, sl):
        if hub is None: P.obj(name, bm, sl)
        else: P.part(name, bm, sl, tuple(hub))
    put(tube_rmf([c + d * (L * t) for t in [i / 10 for i in range(11)]], [r * (1.0 - 0.15 * t) * (1 - t ** 2.2) + 0.0 for t in [i / 10 for i in range(11)]], 16), "Lamp")
    put(tube_rmf([c + d * (L * 0.62 * t) for t in [i / 8 for i in range(9)]], [r * 0.55 * (1 - t ** 1.8) for t in [i / 8 for i in range(9)]], 12), "Glow")


def J2_shogun():
    """THE SHOGUN MECHA (2026-10-14, remade like the alien / west / treasure / sea / meadow bosses): a samurai war-machine built like a real
    machine - every joint a working joint: ball joints at the shoulders and hips, hinges at the elbows and knees with gold caps over their
    pins, hydraulic rams working each limb, a reactor core glowing in his chest behind a ring of vents, cooling fins in even rows, the
    abdomen in black lames riveted in gold, his armour red lacquer edged in gold over a black frame - the samurai's own armour turned
    to steel: the great shoulder guards laced in gold, the skirt of hinged plates, the kabuto with its ridged bowl, tiers of neck guard and
    the golden crescent. His face is a war mask: a steel faceplate with a grille of fangs for a mouth and two eyes slanted in a glare,
    burning cyan in the visor.
    The cartoon idea kept: the beam katana raised high in his right hand (it swings), the rotary cannon on his left forearm aimed at you
    (its barrels turn - his shots leave from it), two war banners on his back, the great ring of glowing crests turning behind him.
    He flies on rockets: a bell engine under each foot and two more on his back, all burning."""
    P = Boss("shogun", AB_pal(Base=((0.42, 0.03, 0.025), 0.4), Belly=((0.03, 0.03, 0.035), 0.4), Accent=((0.86, 0.85, 0.8), 0.5), Trim=((0.98, 0.72, 0.2), 0.7),
                              Glass=((0.3, 0.9, 1.0), 0.5), Dark=((0.015, 0.015, 0.02), 0.4), Glow=((0.6, 1.0, 1.0), 0.5), Metal=((0.42, 0.44, 0.48), 0.5),
                              Lamp=((1.0, 0.55, 0.12), 0.8)))
    glow_strength(P, 2.0)
    # ---- the torso: a boxy chest of red lacquer over the black frame, the abdomen in riveted lames, the reactor core
    def crx(z): return lerp_keys(z, [(0.3, 0.46), (0.6, 0.6), (0.85, 0.64), (1.0, 0.58), (1.08, 0.3)])
    def cry(z): return lerp_keys(z, [(0.3, 0.33), (0.6, 0.42), (0.85, 0.42), (1.0, 0.36), (1.08, 0.24)])
    def chest(z, a):
        sa, ca = math.sin(a), math.cos(a)
        return V_((math.copysign(abs(sa) ** 0.62, sa) * crx(z), math.copysign(abs(ca) ** 0.62, ca) * cry(z), z))
    P.obj("Chest", surf_grid(chest, 20, 48, 0.3, 1.08), "Base")
    P.obj("ChestRim", tube_rmf([chest(0.31, math.radians(a)) * 1.02 + V_((0, 0, 0.0)) for a in range(-180, 181, 10)], [0.022] * 37, 6), "Trim")
    P.obj("ChestRim", tube_rmf([V_((p.x * 1.02, p.y * 1.02, p.z)) for p in [chest(1.0, math.radians(a)) for a in range(-180, 181, 10)]], [0.022] * 37, 6), "Trim")
    abd = [lame_band(z, z - 0.13, 0.43 - 0.015 * i, 0.31 - 0.01 * i, 0.42 - 0.015 * i, 0.3 - 0.01 * i, seg=40, thick=0.03) for i, z in enumerate((0.3, 0.17, 0.04))]
    P.obj("Abdomen", bm_join(abd), "Belly")
    P.obj("AbdomenCore", surf_grid(lambda z, a: V_((math.sin(a) * 0.39, math.cos(a) * 0.28, z)), 6, 32, -0.18, 0.32), "Dark")
    riv = []
    for i, z in enumerate((0.235, 0.105, -0.025)):
        for k in range(14):
            a = math.radians(-130 + 260 * k / 13); r0, r1 = 0.43 - 0.015 * i, 0.31 - 0.01 * i
            riv.append(ball((math.sin(a) * (r0 + 0.012), math.cos(a) * (r1 + 0.012), z), (0.014, 0.014, 0.014), 6, 3))
    small(P.obj("Rivet", bm_join(riv), "Trim"))
    CC = V_((0, 0.45, 0.7))
    P.obj("CoreRing", ring_on(CC, (0, 1, 0), 0.17, 0.035, 32, 8), "Trim")
    P.obj("Core", oriented_ball(CC + V_((0, 0.01, 0)), (0.15, 0.05, 0.15), V_((1, 0, 0)), V_((0, 1, 0)), V_((0, 0, 1)), 24, 8), "Glow")
    vents = []
    for k in range(12):   # the vents round the core, evenly
        a = 2 * math.pi * k / 12; d = V_((math.sin(a), 0, math.cos(a)))
        vents.append(box(tuple(CC + d * 0.26 + V_((0, -0.01, 0))), (0.03, 0.03, 0.09), Matrix.Rotation(-a, 3, "Y")))
    P.obj("Vent", bm_join(vents), "Dark")
    fins = []
    for s in (1, -1):    # cooling fins on the flanks, in even rows
        for k in range(6):
            z = 0.5 + 0.08 * k; p = chest(z, math.radians(s * 100))
            fins.append(box(tuple(p + V_((s * 0.02, 0, 0))), (0.06, 0.2, 0.025)))
    P.obj("Fin", bm_join(fins), "Belly")
    P.obj("Collar", ring_on(V_((0, 0.0, 1.07)), (0, 0, 1), 0.27, 0.05, 32, 8), "Trim")
    # ---- the waist gimbal and the skirt of hinged plates
    P.obj("Waist", ring_on(V_((0, 0.0, -0.17)), (0, 0, 1), 0.4, 0.07, 36, 8), "Metal")
    for k in range(9):
        a = math.radians(-160 + 320 * k / 8); d = V_((math.sin(a), math.cos(a), 0)); rz = Matrix.Rotation(-a, 3, "Z") @ Matrix.Rotation(math.radians(-14), 3, "X")
        c = V_((math.sin(a) * 0.5, math.cos(a) * 0.4, -0.45)) + d * 0.04
        P.obj("Kusazuri", box(tuple(c), (0.3, 0.05, 0.5), rz), "Base")
        P.obj("KusazuriHem", box(tuple(c + rz @ V_((0, 0.0, -0.25))), (0.31, 0.06, 0.05), rz), "Trim")
        P.obj("Hinge", pipe([c + rz @ V_((-0.1, 0.0, 0.27)), c + rz @ V_((0.1, 0.0, 0.27))], [0.025, 0.025], 8), "Trim")
    # ---- the legs: ball joints, armoured thighs worked by rams, gold-capped knees, shin guards, rocket boots
    for s in (1, -1):
        hip, knee, ank = V_((s * 0.3, 0.0, -0.3)), V_((s * 0.38, 0.14, -0.86)), V_((s * 0.38, 0.0, -1.32))
        P.obj("HipJoint", ball(tuple(hip), (0.16, 0.16, 0.16), 14, 7), "Metal")
        P.obj("Thigh", limb(hip, knee, 0.17, 0.15), "Belly")
        P.obj("ThighArmor", box(tuple(hip.lerp(knee, 0.5) + V_((s * 0.03, 0.12, 0.0))), (0.3, 0.08, 0.42), Matrix.Rotation(math.radians(-8), 3, "X")), "Base")
        P.obj("Ram", piston(hip + V_((s * 0.1, -0.12, -0.05)), knee + V_((s * 0.1, -0.1, 0.06)), 0.04), "Metal")
        P.obj("Knee", ring_on(knee, (1, 0, 0), 0.12, 0.05, 20, 8), "Trim"); P.obj("Knee", ball(tuple(knee), (0.14, 0.14, 0.14), 12, 6), "Belly")
        P.obj("Shin", limb(knee, ank, 0.14, 0.12), "Belly")
        P.obj("ShinGuard", hull([tuple(knee + V_((x, y, z))) for x in (-0.17, 0.17) for y in (0.05, 0.22) for z in (-0.04, -0.46)] + [tuple(knee + V_((0, 0.27, -0.1)))]), "Base")
        P.obj("ShinRim", pipe([knee + V_((-0.17, 0.225, -0.04)), knee + V_((0, 0.29, -0.06)), knee + V_((0.17, 0.225, -0.04))], [0.02, 0.02, 0.02], 6), "Trim")
        P.obj("Boot", hull([tuple(ank + V_((x, y, z))) for x in (-0.17, 0.17) for (y, z) in ((-0.17, 0.08), (0.28, 0.0), (0.28, -0.12), (-0.17, -0.16))]), "Belly")
        P.obj("BootPlate", box(tuple(ank + V_((0, 0.2, -0.02))), (0.3, 0.14, 0.12), Matrix.Rotation(math.radians(-20), 3, "X")), "Base")
        P.obj("Engine", bell(ank + V_((0, 0.02, -0.14)), (0, 0, -1), 0.08, 0.15, 0.22), "Metal")
        jet(P, "Jet", ank + V_((0, 0.02, -0.34)), (0, -0.05, -1), 0.13, 0.7)
    # ---- the shoulders: ball joints, the great guards laced in gold
    for s in (1, -1):
        sh = V_((s * 0.78, 0.0, 0.98))
        P.obj("ShoulderJoint", ball(tuple(sh), (0.19, 0.19, 0.19), 14, 7), "Metal")
        P.obj("SodeBar", box(tuple(sh + V_((s * 0.06, 0, 0.17))), (0.42, 0.5, 0.07), Matrix.Rotation(math.radians(s * 14), 3, "Y")), "Trim")
        out = V_((s * 0.75, 0.6, 0.28)).normalized(); acr = V_((0, 0, 1)).cross(out).normalized() * s
        plate_stack(P, "Sode", sh + V_((s * 0.16, 0.06, 0.14)), acr, V_((s * 0.3, 0.05, -1.0)).normalized(), out, 0.6, 0.76, 4, 0.08, 0.12, "Base", "Trim", 7)
    # ---- the right arm raises the beam katana: a ram on the upper arm, the gold-capped elbow, the armoured forearm (it swings)
    sh, el, wr = V_((0.78, 0.0, 0.98)), V_((1.12, 0.12, 1.2)), V_((1.06, 0.24, 1.62)); hub = tuple(sh)
    P.part("SwayBlade", limb(sh, el, 0.13, 0.12), "Belly", hub)
    P.part("SwayBlade", piston(sh + V_((0.02, 0.12, -0.08)), el + V_((-0.05, 0.1, -0.06)), 0.035), "Metal", hub)
    P.part("SwayBlade", ring_on(el, (0, 1, 0), 0.12, 0.05, 20, 8), "Trim", hub); P.part("SwayBlade", ball(tuple(el), (0.13, 0.13, 0.13), 12, 6), "Belly", hub)
    P.part("SwayBlade", limb(el, wr, 0.15, 0.12, [(0.4, 0.4, 0.0, 1.2, 0.12)]), "Base", hub)
    P.part("SwayBlade", ring_on(el.lerp(wr, 0.85), wr - el, 0.13, 0.025, 20, 5), "Trim", hub)
    gax = V_((0.5, -0.08, 0.86)).normalized()
    fist(P, wr + gax * 0.12, gax, V_((0.3, 1.0, 0.0)), 1.15, 0.045, "SwayBlade", hub, "Belly", "Trim")
    h0 = wr + gax * 0.12 - gax * 0.2; h1 = wr + gax * 0.12 + gax * 0.22
    P.part("SwayBlade", pipe([h0, h0.lerp(h1, 0.5), h1], [0.045, 0.045, 0.045], 10), "Belly", hub)
    P.part("SwayBlade", ring_on(h0, gax, 0.05, 0.016, 12, 5), "Trim", hub)
    g_ = lathe([(0.0, -0.014), (0.13, -0.014), (0.14, 0.0), (0.13, 0.014), (0.0, 0.014)], 28, "z"); u_, v_ = frame(gax)
    xf(g_, Matrix((u_, v_, gax)).transposed(), tuple(h1)); P.part("SwayBlade", g_, "Trim", hub)
    bl = [h1 + gax * (0.04 + 1.9 * t) - u_ * (0.1 * t * t) for t in [i / 12 for i in range(13)]]
    fl_ = V_((0, 1, 0)) - gax * gax.y; fl_.normalize()
    P.part("SwayBlade", flat_pipe(bl, [0.085] * 11 + [0.055, 0.0], fl_, 0.7, 10), "Glass", hub)
    P.part("SwayBlade", flat_pipe(bl[:-1], [0.035] * 11 + [0.0], fl_, 0.45, 8), "Glow", hub)
    # ---- the left arm: the rotary cannon on the forearm, aimed at you; its barrels turn
    sh, el, wr = V_((-0.78, 0.0, 0.98)), V_((-1.06, 0.22, 0.72)), V_((-1.0, 0.72, 0.74))
    P.obj("Arm", limb(sh, el, 0.13, 0.12), "Belly")
    P.obj("Ram", piston(sh + V_((-0.02, 0.12, -0.08)), el + V_((0.05, 0.08, 0.06)), 0.035), "Metal")
    P.obj("Elbow", ring_on(el, (1, 0, 0), 0.12, 0.05, 20, 8), "Trim"); P.obj("Elbow", ball(tuple(el), (0.13, 0.13, 0.13), 12, 6), "Belly")
    ax_ = (wr - el).normalized()
    P.obj("Cannon", tube_rmf([el + ax_ * 0.05, el + ax_ * 0.3, wr + ax_ * 0.1], [0.19, 0.2, 0.2], 24), "Base")
    for t in (0.12, 0.62):
        P.obj("CannonBand", ring_on(el.lerp(wr + ax_ * 0.1, t), ax_, 0.205, 0.025, 28, 6), "Trim")
    P.obj("Drum", tube_rmf([wr - ax_ * 0.25 + V_((-0.2, 0, -0.06)), wr - ax_ * 0.25 + V_((-0.36, 0, -0.06))], [0.15, 0.15], 20), "Belly")
    P.obj("DrumCap", ring_on(wr - ax_ * 0.25 + V_((-0.37, 0, -0.06)), (1, 0, 0), 0.12, 0.03, 20, 6), "Trim")
    belt = []
    for k in range(8):   # the feed belt from the drum into the breech
        t = k / 7; q = wr - ax_ * 0.25 + V_((-0.2 + 0.12 * t, 0.06 + 0.1 * t, 0.06 + 0.06 * math.sin(math.pi * t)))
        belt.append(box(tuple(q), (0.05, 0.03, 0.06)))
    P.obj("Belt", bm_join(belt), "Trim")
    bc = wr + ax_ * 0.1; hubb = tuple(bc)
    for k in range(6):
        a = 2 * math.pi * k / 6; u2, v2 = frame(ax_); d = u2 * math.cos(a) + v2 * math.sin(a)
        P.part("RollBarrels", pipe([bc + d * 0.1, bc + d * 0.1 + ax_ * 0.7], [0.04, 0.04], 10), "Metal", hubb)
        P.part("RollBarrels", ring_on(bc + d * 0.1 + ax_ * 0.7, ax_, 0.04, 0.012, 10, 4), "Dark", hubb)
    for t in (0.25, 0.6):
        P.part("RollBarrels", ring_on(bc + ax_ * (0.7 * t), ax_, 0.15, 0.03, 24, 6), "Trim", hubb)
    P.part("RollBarrels", pipe([bc, bc + ax_ * 0.72], [0.035, 0.035], 8), "Metal", hubb)
    # ---- the head: the steel war mask - a grille of fangs, slanted eyes burning cyan - under the kabuto and its golden crescent
    HC = V_((0, 0.06, 1.42))
    P.obj("Neck", piston(V_((0.08, 0.0, 1.05)), HC + V_((0.08, -0.04, -0.12)), 0.04), "Metal")
    P.obj("Neck", piston(V_((-0.08, 0.0, 1.05)), HC + V_((-0.08, -0.04, -0.12)), 0.04), "Metal")
    P.obj("Head", oriented_ball(HC, (0.26, 0.27, 0.27), V_((1, 0, 0)), V_((0, 1, 0)), V_((0, 0, 1)), 24, 12), "Belly")
    P.obj("Faceplate", oriented_ball(HC + V_((0, 0.13, -0.07)), (0.23, 0.15, 0.2), V_((1, 0, 0)), V_((0, 1, 0)), V_((0, 0, 1)), 24, 12), "Metal")
    P.obj("Grille", oriented_ball(HC + V_((0, 0.24, -0.15)), (0.14, 0.05, 0.075), V_((1, 0, 0)), V_((0, 1, 0)), V_((0, 0, 1)), 16, 8), "Dark")
    fangs = []
    for k in range(7):   # the grille's bars, shaped as fangs
        x = -0.09 + 0.03 * k; L = 0.11 if k in (1, 5) else 0.075
        fangs.append(cone(HC + V_((x, 0.285 - 0.3 * x * x, -0.09)), HC + V_((x, 0.29 - 0.3 * x * x, -0.09 - L)), 0.014, 5))
        fangs.append(cone(HC + V_((x, 0.28 - 0.3 * x * x, -0.215)), HC + V_((x, 0.285 - 0.3 * x * x, -0.215 + L * 0.7)), 0.012, 5))
    P.obj("Fang", bm_join(fangs), "Trim")
    for s in (1, -1):   # the eyes: two slits slanted down to the middle in a glare, burning cyan, a gold brow over each
        th = math.radians(20); ex = V_((math.cos(th), 0, s * math.sin(th)))
        ec = HC + V_((s * 0.1, 0.25, 0.04))
        P.obj("Eye", oriented_ball(ec, (0.075, 0.02, 0.022), *rh(ex, V_((0, 1, 0)), ex.cross(V_((0, 1, 0)))), 14, 6), "Glass")
        P.obj("EyeBrow", tube_rmf([ec + ex * (-0.09) + V_((0, 0.015, 0.035)), ec + V_((0, 0.02, 0.04)), ec + ex * 0.09 + V_((0, 0.0, 0.04))], [0.016, 0.02, 0.012], 8), "Trim")
        P.obj("Cheek", oriented_ball(HC + V_((s * 0.16, 0.2, -0.07)), (0.07, 0.05, 0.08), V_((1, 0, 0)), V_((0, 1, 0)), V_((0, 0, 1)), 12, 6), "Metal")
    P.obj("Kabuto", lathe([(0.0, 0.5), (0.18, 0.47), (0.3, 0.38), (0.35, 0.24), (0.36, 0.12)], 36, "z", tuple(HC)), "Base")
    rid = []
    for k in range(24):
        a = 2 * math.pi * k / 24
        rid.append(pipe([HC + V_((math.sin(a) * r, math.cos(a) * r, z)) for r, z in ((0.1, 0.495), (0.2, 0.462), (0.3, 0.385), (0.355, 0.24), (0.365, 0.12))], [0.012] * 5, 4))
    small(P.obj("KabutoRidge", bm_join(rid), "Trim"))
    P.obj("Brim", lathe([(0.37, 0.13), (0.43, 0.1), (0.36, 0.085)], 36, "z", tuple(HC)), "Trim")
    for i in range(3):   # the tiers of neck guard round the back and sides
        z = HC.z + 0.08 - 0.1 * i; r0, r1 = 0.38 + 0.06 * i, 0.44 + 0.06 * i
        P.obj("Shikoro", lame_band(z, z - 0.11, r0, r0, r1, r1, 75, 285, 36, 0.025), "Base" if i % 2 == 0 else "Belly")
        P.obj("ShikoroRim", pipe([HC + V_((math.sin(math.radians(a)) * r1, math.cos(math.radians(a)) * r1, z - 0.11 - HC.z)) for a in range(75, 286, 15)], [0.014] * 15, 5), "Trim")
    for s in (1, -1):
        P.obj("Fukigaeshi", hull([(s * 0.36, 0.25, 1.52), (s * 0.4, 0.3, 1.56), (s * 0.66, 0.34, 1.7), (s * 0.62, 0.15, 1.58), (s * 0.38, 0.1, 1.42)]), "Base")
        P.obj("FukiRim", pipe([V_((s * 0.38, 0.27, 1.53)), V_((s * 0.66, 0.35, 1.71)), V_((s * 0.62, 0.16, 1.58))], [0.016, 0.016, 0.016], 5), "Trim")
    arc = [V_((math.sin(t) * 0.72, 0.36, 1.97 + math.cos(t) * 0.48 - 0.38)) for t in [math.radians(-80 + 160 * i / 24) for i in range(25)]]
    polys = []
    for i in range(24):   # the golden crescent: thick in the middle, tapering to its points
        w0 = 0.015 + 0.13 * math.sin(math.pi * i / 24); w1 = 0.015 + 0.13 * math.sin(math.pi * (i + 1) / 24)
        a0, a1 = arc[i], arc[i + 1]; o = V_((0, 0.36, 1.59))
        polys.append([tuple(a0), tuple(a1), tuple(a1 + (a1 - o).normalized() * w1), tuple(a0 + (a0 - o).normalized() * w0)])
    P.obj("Maedate", st_cloth(polys, 0.04), "Trim")
    P.obj("CrestGem", oriented_ball(V_((0, 0.4, 1.68)), (0.07, 0.035, 0.07), V_((1, 0, 0)), V_((0, 1, 0)), V_((0, 0, 1)), 14, 7), "Glass")
    # ---- the back: two rocket pods burning, the war banners on their poles
    for s in (1, -1):
        b = V_((s * 0.3, -0.42, 0.62))
        P.obj("Pod", tube_rmf([b + V_((0, 0.22, 0.42)), b + V_((0, 0.1, 0.2)), b], [0.15, 0.17, 0.16], 20), "Base")
        P.obj("PodBand", ring_on(b + V_((0, 0.1, 0.2)), (0, 0.5, 1.0), 0.175, 0.025, 24, 6), "Trim")
        P.obj("Engine", bell(b, (s * 0.1, -0.35, -1.0), 0.1, 0.18, 0.26), "Metal")
        jet(P, "Jet", b + V_((s * 0.1, -0.35, -1.0)).normalized() * 0.26, (s * 0.1, -0.4, -1.0), 0.15, 0.85)
        p0 = V_((s * 0.22, -0.4, 0.9)); p1 = V_((s * 0.5, -0.55, 2.5))
        P.obj("Pole", pipe([p0, p0.lerp(p1, 0.5), p1], [0.03, 0.028, 0.025], 8), "Belly")
        P.obj("PoleTip", cone(p1, p1 + V_((s * 0.02, 0.0, 0.16)), 0.045, 6), "Trim")
        cr = [p1 + V_((0, 0, -0.1)), p1 + V_((s * 0.55, 0.0, -0.1)), p1 + V_((s * 0.55, 0.0, -1.25)), p1 + V_((0, 0, -1.25))]
        P.obj("ClothBanner", st_cloth([[tuple(q) for q in cr]], 0.02), "Accent")
        mc = p1 + V_((s * 0.275, 0.02, -0.66))
        P.obj("BannerMon", ring_on(mc, (0, 1, 0), 0.15, 0.03, 28, 6), "Base")
        P.obj("BannerMon", oriented_ball(mc, (0.09, 0.012, 0.09), V_((1, 0, 0)), V_((0, 1, 0)), V_((0, 0, 1)), 18, 4), "Base")
        P.obj("BannerEdge", box(tuple(p1 + V_((s * 0.275, 0, -1.27))), (0.57, 0.035, 0.05)), "Trim")
    # ---- the great ring of glowing crests turning behind him
    RC = V_((0, -0.78, 1.2))
    hal = torus(1.45, 0.045, 0.0, 64, 6); xf(hal, Matrix.Rotation(math.radians(90), 3, "X"), tuple(RC))
    P.part("RollHalo", hal, "Trim", tuple(RC))
    for k in range(8):
        a = 2 * math.pi * k / 8; c = RC + V_((math.sin(a) * 1.45, 0, math.cos(a) * 1.45))
        P.part("RollHalo", ring_on(c, (0, 1, 0), 0.18, 0.035, 24, 6), "Trim", tuple(RC))
        P.part("RollHalo", oriented_ball(c, (0.15, 0.04, 0.15), V_((1, 0, 0)), V_((0, 1, 0)), V_((0, 0, 1)), 18, 6), "Glow" if k % 2 else "Belly", tuple(RC))
    mz = bc + ax_ * 0.78
    P.part("Muzzle", ball(tuple(mz), (0.02, 0.02, 0.02), 6, 3), "Dark", tuple(mz))
    return P


BOSSES = [("oni", J2_oni), ("crane", J2_crane), ("samurai", J2_samurai), ("ryu", J2_ryu), ("shogun", J2_shogun)]

# the surfaces each part is made of, for the bake (boss_bake.py): slot defaults, then part-name patterns
BB.TABLES.update({
    "oni": ({"Base": "skin", "Belly": "flesh", "Accent": "tiger", "Trim": "gold", "Glass": "horn", "Dark": "keratin", "Glow": "glow",
             "Metal": "iron", "Lamp": "glow"},
            [("Cloud*", {"Metal": "stormcloud"}), ("Bead", {"Dark": "wood", "Accent": "gem"}), ("Rope", "rope"), ("Tooth", "enamel"), ("Tusk", "enamel"),
             ("Hair", "hair"), ("Pupil", "eye"), ("Eye", "lamp"), ("SodeLace", "silk"), ("Lightning", "glow"), ("Halo", "fire"), ("Fire*", "fire"),
             ("SpinEmbers", "fire"), ("Muzzle", "matte")]),
    "crane": ({"Base": "feather", "Belly": "horn", "Accent": "feather", "Trim": "gold", "Glass": "silk", "Dark": "keratin", "Glow": "glow",
               "Metal": "enamel", "Lamp": "glow"},
              [("Body", "down"), ("Neck", "down"), ("Nape", "down"), ("Head", "down"), ("Cheek", "down"), ("Thigh", "down"), ("Crown", "flesh"),
               ("Eye", "lamp"), ("Pupil", "eye"), ("Tongue", "flesh"), ("Plate", "enamel"), ("PlateLace", "silk"), ("Maedate", "gold"),
               ("Leg", "scales"), ("Toe", "scales"), ("SpinBlossoms", {"Glow": "petal", "Lamp": "glow"}), ("Muzzle", "matte")]),
    "samurai": ({"Base": "lacquer", "Belly": "sensu", "Accent": "silk", "Trim": "gold", "Glass": "fire", "Dark": "cloth", "Glow": "fire",
                 "Metal": "katana", "Lamp": "glow"},
                [("Menpo*", {"Accent": "lacquer"}), ("Beard", "hair"), ("Katana", {"Dark": "leather", "Accent": "silk", "Trim": "gold", "Metal": "katana"}),
                 ("Glove", {"Dark": "leather", "Trim": "gold"}), ("SpiritFire", {"Lamp": "glow", "Glow": "fire"}), ("EyeFire", "glow"), ("Void", "matte"),
                 ("DoCore", "matte"), ("SpinWisps", "glow"), ("Muzzle", "matte")]),
    "ryu": ({"Base": "ryu_hide", "Belly": "horn", "Accent": "hair", "Trim": "gold", "Glass": "enamel", "Dark": "eye", "Glow": "fire",
             "Metal": "cloud", "Lamp": "glow"},
            [("Head", "skin"), ("Snout", "skin"), ("NosePad", "skin"), ("NostrilRim", "skin"), ("LowerJaw", "skin"), ("Ear", "skin"), ("Leg", "skin"),
             ("Foot", "skin"), ("Toe", "scales"), ("Mouth", "flesh"), ("Tongue", "flesh"), ("Eye", "lamp"), ("Crest", "fin"), ("PearlFlame", "fire"),
             ("TailFlame", "fire"), ("ElbowFlame", "fire"), ("EyeRim", "flesh"), ("Muzzle", "matte")]),
    "shogun": ({"Base": "lacquer", "Belly": "steel", "Accent": "silk", "Trim": "gold", "Glass": "glow", "Dark": "matte", "Glow": "glow",
                "Metal": "steel", "Lamp": "fire"},
               [("Jet", {"Lamp": "fire", "Glow": "glow"}), ("BannerMon", "lacquer"), ("Muzzle", "matte")]),
})

if __name__ == "__main__":
    os.makedirs(AB.OUT, exist_ok=True)
    for bid, fn in BOSSES:
        if ONLY and bid not in ONLY: continue
        P = fn()
        if AB.EXPORT and bid in BB.TABLES: BB.finish_baked(P, AB.OUT)   # the real surfaces baked into textures beside the FBX
        else: P.finish()
    print("DONE")
