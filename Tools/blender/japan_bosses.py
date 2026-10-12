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


BOSSES = [("oni", J_oni), ("crane", J_crane), ("samurai", J_samurai), ("ryu", J_dragon), ("shogun", J_shogun)]

if __name__ == "__main__":
    os.makedirs(AB.OUT, exist_ok=True)
    for bid, fn in BOSSES:
        if ONLY and bid not in ONLY: continue
        fn().finish()
    print("DONE")
