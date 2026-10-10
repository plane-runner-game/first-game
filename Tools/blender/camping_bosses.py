# Sky Squad, the camping forest's five bosses (2026-10-10: "bosses now for the camping forest"), the night by the fire: the firefly queen,
# the great horned owl, the lantern balloon, the star bear and the forest guardian. Built from code like the alien / sea / lava bosses
# (alien_bosses.py lends its Boss class and shapes).
# Run: blender -b -P Tools/blender/camping_bosses.py -- <out dir> [export] [ids,comma,separated]
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

def blob(c, r, n=24, seg=10):
    """a rounded wing outline: n points round an ellipse-ish shape, a fan from its first point."""
    return [Vector(c) + Vector((math.cos(2 * math.pi * i / n) * r[0], math.sin(2 * math.pi * i / n) * r[1], 0)) for i in range(n)]

def fan_sheet(center, outline, thick=0.02):
    polys = [[center, a, b] for a, b in zip(outline, outline[1:] + outline[:1])]
    return sheet([[tuple(p) for p in poly] for poly in polys], thick)

def tilt(bm, ax, deg, about):
    m = Matrix.Rotation(math.radians(deg), 3, ax)
    for v in bm.verts: v.co = m @ (v.co - Vector(about)) + Vector(about)
    return bm


# ================================================================= 1. the firefly queen
def C_firefly():
    """A giant firefly: a dark body with a fiery orange shield, huge dark eyes, feathery golden antennae, six thin legs, an abdomen whose last
    rings glow like a lantern, and four broad pale wings with glowing spots that beat."""
    P = Boss("firefly", {"Base": ((0.10, 0.08, 0.08), 0.5), "Belly": ((0.50, 0.38, 0.24), 0.3), "Accent": ((0.95, 0.40, 0.12), 0.5),
                         "Trim": ((0.92, 0.75, 0.32), 0.6), "Glass": ((0.80, 0.92, 0.85), 0.9), "Dark": ((0.03, 0.03, 0.04), 0.85),
                         "Glow": ((0.85, 1.0, 0.30), 0.5), "Metal": ((0.4, 0.4, 0.4), 0.5), "Lamp": ((1.0, 0.85, 0.40), 0.8)})
    P.obj("Head", ball((0, 1.25, 0.1), (0.3, 0.26, 0.26), 14, 7), "Base", 1)
    for s in (1, -1):
        P.obj("Eye", ball((s * 0.24, 1.33, 0.14), (0.15, 0.15, 0.17), 12, 6), "Dark")
        P.obj("EyeShine", ball((s * 0.3, 1.42, 0.22), (0.035, 0.03, 0.035), 6, 3), "Lamp")
        ant = bez((s * 0.08, 1.45, 0.3), (s * 0.25, 1.75, 0.55), (s * 0.55, 1.85, 0.7), (s * 0.75, 1.7, 0.85), 8)
        P.obj("Antenna", pipe(ant, [0.03] * 8 + [0.02], 6), "Trim")
        for k in range(2, 9):
            q = ant[k]
            for side in (-1, 1):
                P.obj("Barb", cone(q, q + Vector((0.0, -0.08, 0.12 * side * 0.6 + 0.06)), 0.012, 4), "Trim", 0, False)
        for k, y in enumerate((0.95, 0.65, 0.35)):
            hip = Vector((s * 0.22, y, -0.15)); knee = Vector((s * 0.6, y + 0.1 - 0.1 * k, 0.05)); foot = Vector((s * 0.75, y + 0.2 - 0.3 * k, -0.45))
            P.obj("Leg", pipe([hip, knee, foot], [0.04, 0.03, 0.015], 6), "Base")
    P.obj("Shield", ball((0, 0.95, 0.18), (0.36, 0.3, 0.16), 14, 6), lambda c, n: "Dark" if abs(c.x) < 0.06 else "Accent", 1)
    P.obj("Thorax", ball((0, 0.7, 0.0), (0.33, 0.35, 0.3), 14, 7), "Belly", 1)
    for k in range(6):   # the abdomen: rings, the last three a lantern
        y = 0.35 - k * 0.27; r = 0.34 - k * 0.025
        P.obj("Ring", ball((0, y, -0.08 - k * 0.03), (r, 0.17, r * 0.85), 14, 6), "Glow" if k >= 3 else ("Belly" if k % 2 else "Base"), 1)
    # four wings, beating together
    for s in (1, -1):
        name = "FlapR" if s > 0 else "FlapL"
        hub = Vector((s * 0.22, 0.75, 0.25))
        fore = [hub + Vector((s * (0.15 + 1.25 * (0.5 + 0.5 * math.cos(t))), 0.35 * math.sin(t) + 0.15, 0.25 * (0.5 + 0.5 * math.cos(t)))) for t in [2 * math.pi * i / 20 for i in range(20)]]
        hind = [hub + Vector((s * (0.1 + 1.0 * (0.5 + 0.5 * math.cos(t))), 0.3 * math.sin(t) - 0.45, 0.15 * (0.5 + 0.5 * math.cos(t)))) for t in [2 * math.pi * i / 20 for i in range(20)]]
        P.part(name, fan_sheet(hub + Vector((s * 0.6, 0.15, 0.12)), fore), "Glass", tuple(hub), 0, False)
        P.part(name, fan_sheet(hub + Vector((s * 0.5, -0.45, 0.08)), hind), "Glass", tuple(hub), 0, False)
        for t in (fore[0], fore[4], fore[16]): P.part(name, pipe([hub, t], [0.02, 0.008], 5), "Trim", tuple(hub))
        for t in (hind[0], hind[5], hind[15]): P.part(name, pipe([hub, t], [0.018, 0.007], 5), "Trim", tuple(hub))
        for k, (dx, dy) in enumerate(((1.0, 0.2), (1.25, 0.05), (0.75, -0.5), (0.95, -0.6))):
            P.part(name, ball(tuple(hub + Vector((s * dx, dy, 0.24 if dy > 0 else 0.14))), (0.08, 0.08, 0.025), 8, 3), "Glow", tuple(hub))
    P.part("Muzzle", ball((0, 1.52, 0.05), (0.07, 0.04, 0.05), 8, 4), "Glow", (0, 1.52, 0.05))
    return P


# ================================================================= 2. the great horned owl
def C_owl():
    """A huge horned owl: a round brown body barred down a cream breast, a pale face disc with great glowing amber eyes, ear tufts, a hooked
    beak, a lit lantern swinging from its talons - and broad barred wings that beat."""
    P = Boss("owl", {"Base": ((0.42, 0.27, 0.15), 0.35), "Belly": ((0.90, 0.82, 0.64), 0.3), "Accent": ((0.22, 0.13, 0.07), 0.35),
                     "Trim": ((0.78, 0.64, 0.30), 0.6), "Glass": ((1.0, 0.85, 0.5), 0.9), "Dark": ((0.03, 0.02, 0.02), 0.8),
                     "Glow": ((1.0, 0.70, 0.25), 0.5), "Metal": ((0.25, 0.22, 0.2), 0.6), "Lamp": ((1.0, 0.72, 0.12), 0.8)})
    def breast(c, n):
        if n.y > 0.3 and c.z < 0.55: return "Accent" if (c.z * 7.0 + abs(c.x) * 2.0) % 1.0 < 0.16 else "Belly"
        return "Base"
    P.obj("Body", ball((0, 0.2, 0.0), (0.72, 0.68, 0.85), 18, 10), breast, 1)
    P.obj("Head", ball((0, 0.5, 0.95), (0.6, 0.52, 0.48), 18, 9), "Base", 1)
    P.obj("Face", ball((0, 0.86, 0.92), (0.5, 0.18, 0.4), 18, 8), lambda c, n: "Accent" if n.y < 0.5 else "Belly", 1)
    for s in (1, -1):
        P.obj("Eye", ball((s * 0.21, 1.0, 0.98), (0.15, 0.08, 0.15), 14, 7), "Lamp")
        P.obj("Pupil", ball((s * 0.21, 1.07, 0.98), (0.07, 0.03, 0.08), 10, 5), "Dark")
        P.obj("Shine", ball((s * 0.25, 1.09, 1.03), (0.025, 0.015, 0.025), 6, 3), "Belly")
        P.obj("Tuft", pipe(bez((s * 0.3, 0.55, 1.25), (s * 0.4, 0.5, 1.45), (s * 0.48, 0.45, 1.6), (s * 0.52, 0.38, 1.72), 5), [0.12, 0.1, 0.08, 0.05, 0.025, 0.0], 8), "Accent")
        P.obj("Brow", box((s * 0.2, 0.98, 1.17), (0.28, 0.06, 0.05), Matrix.Rotation(math.radians(-s * 15), 3, "Y")), "Accent", 0, False)
        for k in (-1, 0, 1):
            P.obj("Talon", pipe(bez((s * 0.2 + k * 0.05, 0.45, -0.75), (s * 0.2 + k * 0.07, 0.6, -0.85), (s * 0.18 + k * 0.08, 0.72, -0.85), (s * 0.15 + k * 0.08, 0.75, -0.78), 4), [0.04, 0.035, 0.03, 0.02, 0.0], 6), "Trim")
        name = "FlapR" if s > 0 else "FlapL"
        hub = (s * 0.6, 0.2, 0.35)
        keys = [(0.55, 0.65, -0.65, 0.18, 0.35), (1.3, 0.6, -0.85, 0.12, 0.5), (2.1, 0.45, -0.85, 0.08, 0.6), (2.75, 0.2, -0.65, 0.04, 0.62), (3.0, -0.05, -0.4, 0.02, 0.6)]
        bm = sweep([(x, airfoil(le, te, th, z)) for (x, le, te, th, z) in fine(keys)], "x")
        if s < 0: bm = mirror_x(bm)
        P.part(name, bm, lambda c, n: "Belly" if n.z < -0.3 else ("Accent" if (abs(c.x) * 2.6) % 1.0 < 0.18 or c.y < -0.62 else "Base"), hub, 0)
        for k in range(5):
            x0 = 2.4 + k * 0.12; y0 = 0.15 - k * 0.15
            P.part(name, cone((s * x0, y0, 0.6), (s * (x0 + 0.45), y0 - 0.12 - k * 0.06, 0.6), 0.07, 4), "Accent", hub, 0, False)
    P.obj("Beak", pipe(bez((0, 1.02, 0.86), (0, 1.12, 0.84), (0, 1.14, 0.76), (0, 1.1, 0.68), 4), [0.07, 0.06, 0.04, 0.02, 0.0], 8), "Trim")
    for k in range(5):
        a = math.radians(-30 + k * 15)
        P.obj("TailFeather", box((math.sin(a) * 0.3, -0.6 - math.cos(a) * 0.3, -0.45), (0.14, 0.6, 0.04), Matrix.Rotation(-a, 3, "Z") @ Matrix.Rotation(math.radians(25), 3, "X")),
              lambda c, n: "Accent" if (c.y * 5) % 1.0 < 0.3 else "Base", 0, False)
    # the lantern it carries
    P.obj("Handle", torus(0.09, 0.012, 0.0, 12, 4), "Metal"); P.parts[-1].data.transform(Matrix.Translation((0, 0.75, -0.95)) @ Matrix.Rotation(math.radians(90), 4, "Y"))
    P.obj("LanternTop", lathe([(0.0, -1.0), (0.16, -1.08), (0.12, -1.12)], 10, "z", (0, 0.75, 0)), "Metal")
    P.obj("LanternGlass", lathe([(0.12, -1.12), (0.13, -1.38), (0.0, -1.4)], 10, "z", (0, 0.75, 0)), "Glow")
    P.obj("LanternBase", lathe([(0.15, -1.38), (0.15, -1.43), (0.0, -1.43)], 10, "z", (0, 0.75, 0)), "Metal")
    P.part("Muzzle", ball((0, 0.75, -1.25), (0.06, 0.06, 0.06), 8, 4), "Lamp", (0, 0.75, -1.25))
    return P


# ================================================================= 3. the lantern balloon
def C_balloon():
    """A patchwork hot-air balloon at night: red, cream and mustard gores with string lights round its belly, carrying a little log cabin
    with glowing windows and a chimney, lanterns hanging from its ropes, flag garlands, and a propeller at the back."""
    P = Boss("balloon", {"Base": ((0.45, 0.28, 0.15), 0.35), "Belly": ((0.95, 0.90, 0.78), 0.3), "Accent": ((0.80, 0.16, 0.12), 0.4),
                         "Trim": ((0.95, 0.70, 0.20), 0.5), "Glass": ((0.25, 0.45, 0.35), 0.4), "Dark": ((0.10, 0.07, 0.05), 0.4),
                         "Glow": ((1.0, 0.80, 0.35), 0.5), "Metal": ((0.35, 0.32, 0.3), 0.6), "Lamp": ((1.0, 0.62, 0.22), 0.8)})
    env = lathe([(0.0, 3.35), (0.55, 3.28), (0.95, 3.05), (1.2, 2.65), (1.25, 2.25), (1.12, 1.8), (0.82, 1.38), (0.45, 1.08), (0.32, 1.0)], 24, "z")
    def gores(c, n):
        k = int(((ang(c) / (2 * math.pi)) % 1.0) * 12)
        if 2.15 < c.z < 2.25: return "Glow"
        return ("Accent", "Belly", "Trim")[k % 3]
    P.obj("Envelope", env, gores, 1)
    for k in range(12):   # the string lights round its belly
        a = 2 * math.pi * (k + 0.5) / 12
        P.obj("Bulb", ball((math.sin(a) * 1.26, math.cos(a) * 1.26, 2.2), (0.06, 0.06, 0.06), 6, 3), "Lamp")
    P.obj("Crown", lathe([(0.0, 3.42), (0.18, 3.38), (0.2, 3.3)], 10, "z"), "Trim")
    # the cabin: a log hut with a roof, windows aglow, a chimney
    P.obj("Cabin", box((0, 0, 0.0), (1.05, 0.95, 0.6)), lambda c, n: "Base" if (c.z * 8) % 1.0 > 0.15 else "Dark", 0, False)
    P.obj("Roof", hull([(-0.65, -0.55, 0.3), (0.65, -0.55, 0.3), (-0.65, 0.55, 0.3), (0.65, 0.55, 0.3), (0, -0.55, 0.72), (0, 0.55, 0.72)]), "Accent", 0, False)
    P.obj("Chimney", box((0.3, -0.2, 0.68), (0.14, 0.14, 0.3)), "Metal", 0, False)
    for s in (1, -1):
        P.obj("Window", box((s * 0.25, 0.48, 0.02), (0.22, 0.02, 0.22)), "Glow", 0, False)
        P.obj("SideWindow", box((s * 0.53, 0.0, 0.02), (0.02, 0.22, 0.22)), "Glow", 0, False)
    P.obj("Door", box((0, -0.48, -0.05), (0.24, 0.02, 0.36)), "Dark", 0, False)
    P.obj("Porch", box((0, 0.62, -0.3), (0.9, 0.3, 0.05)), "Base", 0, False)
    # the ropes up to the envelope, lanterns hanging, a garland of flags between them
    tops = [Vector((math.sin(a) * 0.38, math.cos(a) * 0.38, 1.02)) for a in [2 * math.pi * k / 4 + math.pi / 4 for k in range(4)]]
    bots = [Vector((sx * 0.5, sy * 0.45, 0.3)) for sx, sy in ((1, 1), (1, -1), (-1, -1), (-1, 1))]
    bots = [bots[0], bots[1], bots[2], bots[3]]
    for t, b in zip(sorted(tops, key=lambda v: (v.x > 0, v.y > 0)), sorted(bots, key=lambda v: (v.x > 0, v.y > 0))):
        P.obj("Rope", pipe([b, t], [0.015, 0.015], 4), "Dark")
        mid = b + (t - b) * 0.35
        P.obj("LanternLine", pipe([mid, mid + Vector((0, 0, -0.18))], [0.008, 0.008], 4), "Dark")
        P.obj("Lantern", ball(tuple(mid + Vector((0, 0, -0.26))), (0.07, 0.07, 0.09), 8, 4), "Lamp")
    for k in range(9):   # flags along the porch garland
        x = -0.48 + k * 0.12
        P.obj("Flag", hull([(x - 0.045, 0.77, -0.12), (x + 0.045, 0.77, -0.12), (x, 0.77, -0.24), (x, 0.79, -0.12)]), ("Accent", "Belly", "Trim")[k % 3], 0, False)
    P.obj("Garland", pipe([(-0.5, 0.77, -0.11), (0.5, 0.77, -0.11)], [0.008, 0.008], 4), "Dark")
    # the propeller at the back on a boom, a rudder fin
    P.obj("Boom", pipe([(0, -0.48, 0.1), (0, -0.95, 0.15)], [0.04, 0.04], 6), "Metal")
    P.prop((0, -1.0, 0.15), 0.42, 3, blade="Base", tip="Accent", spinner="Trim", spinner_len=0.12)
    P.obj("Rudder", hull([(0, -0.9, 0.35), (0, -1.3, 0.55), (0, -1.3, 0.25), (0.02, -1.1, 0.4), (-0.02, -1.1, 0.4)]), "Accent", 0, False)
    P.part("Muzzle", ball((0, 0.8, 0.0), (0.07, 0.05, 0.07), 8, 4), "Glow", (0, 0.8, 0.0))
    return P


# ================================================================= 4. the star bear
def C_bear():
    """A bear made of the night sky: a deep blue body speckled with glowing stars and joined by constellation lines, a pale starlit muzzle,
    golden eyes, legs that run through the air, and a ring of little stars circling it."""
    P = Boss("bear", {"Base": ((0.08, 0.13, 0.38), 0.85), "Belly": ((0.30, 0.42, 0.85), 0.7), "Accent": ((0.55, 0.65, 1.0), 0.8),
                      "Trim": ((0.85, 0.90, 1.0), 0.6), "Glass": ((0.6, 0.8, 1.0), 0.95), "Dark": ((0.02, 0.03, 0.08), 0.8),
                      "Glow": ((0.75, 0.90, 1.0), 0.5), "Metal": ((0.4, 0.45, 0.6), 0.6), "Lamp": ((1.0, 0.85, 0.35), 0.8)})
    body = ball((0, 0.0, 0.0), (0.72, 1.25, 0.62), 20, 10)
    stars = [v.co.copy() for v in body.verts if v.co.z > 0.0 and speckle(v.co, 1.9) < 0.12]
    P.obj("Body", body, lambda c, n: "Belly" if n.z < -0.4 else "Base", 1)
    for q in stars: P.obj("Star", ball(tuple(q * 1.03), (0.05, 0.05, 0.05), 6, 3), "Glow")
    path = sorted(stars, key=lambda v: v.y)[::2]
    for a, b in zip(path, path[1:]):
        if (a - b).length < 0.9: P.obj("Line", pipe([a * 1.03, b * 1.03], [0.012, 0.012], 4), "Accent")
    P.obj("Head", ball((0, 1.3, 0.3), (0.45, 0.42, 0.4), 16, 8), "Base", 1)
    P.obj("Snout", ball((0, 1.68, 0.2), (0.22, 0.22, 0.17), 12, 6), "Belly", 1)
    P.obj("Nose", ball((0, 1.88, 0.26), (0.08, 0.05, 0.06), 8, 4), "Dark")
    for s in (1, -1):
        P.obj("Ear", ball((s * 0.32, 1.15, 0.68), (0.13, 0.08, 0.13), 10, 5), "Base")
        P.obj("EarIn", ball((s * 0.32, 1.2, 0.68), (0.07, 0.04, 0.08), 8, 4), "Belly")
        P.obj("Eye", ball((s * 0.18, 1.62, 0.43), (0.06, 0.05, 0.06), 8, 4), "Lamp")
        P.obj("HeadStar", ball((s * 0.2, 1.35, 0.68), (0.045, 0.045, 0.045), 6, 3), "Glow")
        for fy, k in ((0.8, 0), (-0.8, 1)):   # the legs: they run through the air, each swinging on its own
            hip = Vector((s * 0.45, fy, -0.25))
            leg = pipe([hip, hip + Vector((0, 0.15 if fy > 0 else -0.15, -0.45)), hip + Vector((0, 0.3 if fy > 0 else -0.05, -0.75))], [0.22, 0.18, 0.16], 10)
            name = "Sway%d" % (k * 2 + (1 if s > 0 else 0))
            P.part(name, leg, "Base", tuple(hip), 1)
            paw = hip + Vector((0, 0.32 if fy > 0 else -0.03, -0.82))
            P.part(name, ball(tuple(paw), (0.18, 0.2, 0.1), 10, 5), "Belly", tuple(hip))
            for t in (-1, 0, 1): P.part(name, cone(paw + Vector((t * 0.08, 0.12, -0.02)), paw + Vector((t * 0.09, 0.24, -0.06)), 0.025, 4), "Trim", tuple(hip), 0, False)
    P.obj("Tail", ball((0, -1.25, 0.2), (0.15, 0.14, 0.14), 8, 4), "Glow")
    for k in range(12):   # the ring of stars circling it
        a = 2 * math.pi * k / 12
        c = Vector((math.sin(a) * 1.5, math.cos(a) * 1.75, 0.35 + 0.15 * math.sin(a * 3)))
        r = 0.09 if k % 3 == 0 else 0.05
        P.part("SpinStars", hull([c + Vector((r * 2, 0, 0)), c + Vector((-r * 2, 0, 0)), c + Vector((0, r * 2, 0)), c + Vector((0, -r * 2, 0)), c + Vector((0, 0, r)), c + Vector((0, 0, -r))]), "Glow", (0, 0, 0.35), 0, False)
    P.part("Muzzle", ball((0, 1.95, 0.18), (0.07, 0.04, 0.05), 8, 4), "Glow", (0, 1.95, 0.18))
    return P


# ================================================================= 5. the forest guardian
def C_guardian():
    """The last boss: an ancient tree spirit - a gnarled trunk with a face of glowing eyes and a moss beard, red-capped mushrooms up its bark,
    two great branch arms with lanterns hanging from them, a crown of leaves full of fireflies, and roots trailing below that sway."""
    P = Boss("guardian", {"Base": ((0.30, 0.20, 0.12), 0.25), "Belly": ((0.16, 0.36, 0.16), 0.3), "Accent": ((0.28, 0.55, 0.20), 0.3),
                          "Trim": ((0.80, 0.16, 0.10), 0.5), "Glass": ((0.95, 0.92, 0.85), 0.4), "Dark": ((0.04, 0.03, 0.02), 0.5),
                          "Glow": ((0.75, 1.0, 0.35), 0.5), "Metal": ((0.3, 0.28, 0.25), 0.5), "Lamp": ((1.0, 0.68, 0.22), 0.8)})
    rng = random.Random(5)
    bark = lambda c, n: "Dark" if (ang(c) * 5.0 + c.z * 1.5) % 1.0 < 0.08 else "Base"
    P.obj("Trunk", lathe([(0.0, -0.6), (0.55, -0.55), (0.48, 0.0), (0.42, 0.7), (0.46, 1.2), (0.55, 1.5), (0.0, 1.6)], 18, "z"), bark, 1)
    for s in (1, -1):
        P.obj("Eye", ball((s * 0.17, 0.42, 0.75), (0.09, 0.05, 0.06), 10, 5), "Glow")
        P.obj("Brow", box((s * 0.17, 0.44, 0.86), (0.2, 0.08, 0.06), Matrix.Rotation(math.radians(-s * 18), 3, "Y")), "Base", 0, False)
        # the branch arms, lanterns hanging off them
        arm = bez((s * 0.35, 0.0, 1.05), (s * 0.9, 0.1, 1.25), (s * 1.35, 0.25, 1.15), (s * 1.8, 0.35, 1.35), 7)
        P.obj("Branch", pipe(arm, [0.2, 0.17, 0.14, 0.11, 0.09, 0.07, 0.05, 0.03], 8), bark, 1)
        for k, t in enumerate((3, 5, 7)):
            q = arm[t]
            twig = q + Vector((s * 0.15, 0.1, 0.3 + 0.1 * k))
            P.obj("Twig", pipe([q, twig], [0.04, 0.015], 5), "Base")
            line_top = q + Vector((0, 0, -0.05))
            P.obj("LanternLine", pipe([line_top, line_top + Vector((0, 0, -0.28))], [0.008, 0.008], 4), "Dark")
            P.obj("Lantern", ball(tuple(line_top + Vector((0, 0, -0.38))), (0.08, 0.08, 0.1), 8, 4), "Lamp")
        for k in range(3):   # mushrooms up the bark
            y = 0.1 + 0.3 * k; z = 0.0 + 0.35 * k
            c = Vector((s * 0.45, y - 0.2, z))
            P.obj("Stalk", pipe([c, c + Vector((s * 0.12, 0, 0.05))], [0.03, 0.03], 5), "Glass")
            P.obj("Cap", ball(tuple(c + Vector((s * 0.14, 0, 0.08))), (0.12, 0.12, 0.06), 10, 4), lambda c2, n: "Glass" if speckle(c2, 3.0) < 0.25 else "Trim")
    P.obj("Mouth", ball((0, 0.4, 0.45), (0.17, 0.06, 0.09), 10, 5), "Dark")
    for k in range(7):   # the moss beard
        a = math.radians(-60 + k * 20)
        base = Vector((math.sin(a) * 0.3, 0.38 + math.cos(a) * 0.04, 0.35))
        P.obj("Moss", cone(base, base + Vector((math.sin(a) * 0.08, 0.05, -0.45 - 0.1 * (3 - abs(k - 3)))), 0.07, 5), "Accent", 0, False)
    # the crown of leaves with fireflies in it
    for k in range(11):
        a = k * 2.399; r = 0.35 + 0.08 * k
        c = (math.sin(a) * min(r, 1.4), math.cos(a) * min(r, 1.0) * 0.8 - 0.1, 1.75 + 0.25 * math.cos(k * 1.3))
        P.obj("Leaves", ball(c, (0.55, 0.5, 0.42), 16, 8), lambda c2, n: "Accent" if n.z > 0.35 else "Belly", 0)
    for k in range(18):
        a = k * 2.1; r = 0.5 + 0.06 * k
        P.obj("Firefly", ball((math.sin(a) * min(r, 1.6), math.cos(a) * min(r, 1.1) * 0.8 + 0.3, 1.55 + 0.5 * speckle(Vector((k, 1, 2)))), (0.04, 0.04, 0.04), 6, 3), "Glow")
    # roots trailing below, swaying
    for k in range(6):
        a = 2 * math.pi * k / 6 + 0.3
        out = Vector((math.sin(a), math.cos(a), 0))
        p0 = out * 0.35 + Vector((0, 0, -0.5))
        pts = bez(p0, p0 + out * 0.35 + Vector((0, 0, -0.3)), p0 + out * 0.55 + Vector((0, 0.1, -0.75)), p0 + out * 0.45 + Vector((0, 0.15, -1.05)), 6)
        P.part("Sway%d" % k, pipe(pts, [0.13, 0.11, 0.09, 0.07, 0.05, 0.03, 0.0], 8), bark, tuple(p0), 1)
    P.part("Muzzle", ball((0, 0.47, 0.45), (0.08, 0.04, 0.05), 8, 4), "Lamp", (0, 0.47, 0.45))
    return P


BOSSES = [("firefly", C_firefly), ("owl", C_owl), ("balloon", C_balloon), ("bear", C_bear), ("guardian", C_guardian)]

if __name__ == "__main__":
    os.makedirs(AB.OUT, exist_ok=True)
    for bid, fn in BOSSES:
        if ONLY and bid not in ONLY: continue
        fn().finish()
    print("DONE")
