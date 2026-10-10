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
def J_crane():
    """A great red-crowned crane: snow-white plumage, a black neck and black flight feathers, a red crown, a long amber beak, legs trailing
    behind it, and broad white wings tipped in black that beat."""
    P = Boss("crane", {"Base": ((0.97, 0.97, 0.98), 0.4), "Belly": ((0.88, 0.90, 0.94), 0.35), "Accent": ((0.06, 0.06, 0.08), 0.5),
                       "Trim": RED, "Glass": ((0.95, 0.70, 0.25), 0.6), "Dark": ((0.03, 0.03, 0.04), 0.6), "Glow": ((1.0, 0.85, 0.45), 0.5),
                       "Metal": ((0.5, 0.5, 0.5), 0.6), "Lamp": ((1.0, 0.85, 0.35), 0.8)})
    P.obj("Body", ball((0, 0.0, 0.0), (0.38, 0.8, 0.35), 14, 7), lambda c, n: "Belly" if n.z < -0.4 else "Base", 1)
    neck = bez((0, 0.6, 0.15), (0, 1.0, 0.35), (0, 1.35, 0.55), (0, 1.55, 0.62), 7)
    P.obj("Neck", pipe(neck, [0.17, 0.14, 0.11, 0.1, 0.095, 0.09, 0.09, 0.09], 10), lambda c, n: "Accent" if c.y > 0.85 else "Base", 1)
    P.obj("Head", ball((0, 1.62, 0.64), (0.12, 0.16, 0.12), 10, 5), lambda c, n: "Trim" if c.z > 0.7 else ("Belly" if c.y < 1.6 else "Accent"))
    P.obj("Beak", cone((0, 1.74, 0.62), (0, 2.25, 0.55), 0.05, 8), "Glass", 0, False)
    for s in (1, -1):
        P.obj("Eye", ball((s * 0.08, 1.7, 0.67), (0.02, 0.02, 0.02), 6, 3), "Dark")
        P.obj("Leg", pipe([(s * 0.12, -0.5, -0.2), (s * 0.12, -1.2, -0.3), (s * 0.12, -1.75, -0.35)], [0.03, 0.025, 0.02], 6), "Accent")
        for k in (-1, 0, 1): P.obj("Toe", cone((s * 0.12, -1.75, -0.35), (s * 0.12 + k * 0.08, -1.95, -0.38), 0.015, 4), "Accent", 0, False)
        name = "FlapR" if s > 0 else "FlapL"
        hub = (s * 0.32, 0.1, 0.18)
        keys = [(0.3, 0.55, -0.45, 0.12, 0.18), (1.2, 0.55, -0.7, 0.08, 0.32), (2.1, 0.4, -0.75, 0.06, 0.45), (2.9, 0.15, -0.6, 0.03, 0.55), (3.2, -0.05, -0.35, 0.02, 0.58)]
        bm = sweep([(x, airfoil(le, te, th, z)) for (x, le, te, th, z) in fine(keys)], "x")
        if s < 0: bm = mirror_x(bm)
        P.part(name, bm, lambda c, n: "Belly" if n.z < -0.3 else ("Accent" if abs(c.x) > 2.35 or (c.y < -0.55 and abs(c.x) > 0.9) else "Base"), hub, 0)
        for k in range(5):
            x0 = 2.6 + k * 0.12; y0 = 0.1 - k * 0.15
            P.part(name, cone((s * x0, y0, 0.55), (s * (x0 + 0.5), y0 - 0.1 - k * 0.07, 0.58), 0.06, 4), "Accent", hub, 0, False)
    for k in range(5):   # the black bustle of the tail
        a = math.radians(-30 + k * 15)
        P.obj("Tail", cone((math.sin(a) * 0.1, -0.7, 0.1), (math.sin(a) * 0.4, -1.25, 0.15 - 0.05 * abs(k - 2)), 0.1, 5), "Accent", 0, False)
    P.part("Muzzle", ball((0, 2.27, 0.55), (0.05, 0.03, 0.04), 8, 4), "Glow", (0, 2.27, 0.55))
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


BOSSES = [("koi", J_koi), ("crane", J_crane), ("samurai", J_samurai), ("ryu", J_dragon), ("isle", J_isle)]

if __name__ == "__main__":
    os.makedirs(AB.OUT, exist_ok=True)
    for bid, fn in BOSSES:
        if ONLY and bid not in ONLY: continue
        fn().finish()
    print("DONE")
