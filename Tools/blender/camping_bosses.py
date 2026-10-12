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


# ================================================================= 2026-10-11: three new ones with faces ("new shapes, with features, grand")
def curve(*segs):
    """bezier pieces joined end to start (each 4 points), sampled 8 per piece, as one outline."""
    out = []
    for sg in segs: out += bez(*sg, 8)[:-1]
    return out

def wing_polys(center, outline, rings=7):
    """a flat wing as a polar grid from an inner point to its outline (so it can be painted face by face)."""
    c = Vector(center); polys = []
    o = [Vector(p) for p in outline]
    for i in range(len(o)):
        a, b = o[i], o[(i + 1) % len(o)]
        for j in range(rings):
            u0, u1 = j / rings, (j + 1) / rings
            p = [c + (a - c) * u0, c + (b - c) * u0, c + (b - c) * u1, c + (a - c) * u1]
            polys.append([tuple(q) for q in (p[1:] if j == 0 else p)])
    return polys


# ----------------------------------------------------------------- the campfire king (in place of the lantern balloon)
def C_ember():
    """A king made of the campfire: a ring of hearth stones and a teepee of burning logs for a body, a great head of living flame with a
    face - dark charcoal brows over blazing eyes, a wide grin full of embers - a molten gold crown, two burning-log arms with fists of
    fire that swing, and a halo of sparks circling him."""
    P = Boss("ember", {"Base": ((0.20, 0.12, 0.07), 0.3), "Belly": ((0.42, 0.40, 0.38), 0.3), "Accent": ((1.0, 0.42, 0.06), 0.5),
                       "Trim": ((1.0, 0.76, 0.22), 0.85), "Glass": ((1.0, 0.97, 0.85), 0.6), "Dark": ((0.05, 0.03, 0.03), 0.4),
                       "Glow": ((0.9, 0.16, 0.02), 0.5), "Metal": ((0.55, 0.42, 0.25), 0.7), "Lamp": ((1.0, 0.50, 0.05), 0.8)})
    log = lambda c, n: "Dark" if speckle(c, 2.3) < 0.18 else "Base"
    # the hearth: stones round a bed of coals
    for k in range(10):
        a = 2 * math.pi * k / 10
        P.obj("Stone", ball((math.sin(a) * 0.78, math.cos(a) * 0.78, -0.92), (0.2, 0.2, 0.14), 10, 5), "Belly", 1)
    P.obj("Coals", lathe([(0.0, -0.9), (0.68, -0.92), (0.6, -0.82), (0.0, -0.74)], 16, "z"), lambda c, n: "Lamp" if speckle(c, 7) < 0.4 else "Glow")
    # a teepee of logs, glowing where they burn
    for k in range(7):
        a = 2 * math.pi * k / 7 + 0.2
        foot = Vector((math.sin(a) * 0.62, math.cos(a) * 0.62, -0.85)); top = Vector((math.sin(a + 0.6) * 0.12, math.cos(a + 0.6) * 0.12, 0.25))
        P.obj("Log", pipe([foot, foot + (top - foot) * 0.5, top], [0.11, 0.1, 0.09], 8), lambda c, n: "Glow" if c.z < -0.68 or speckle(c, 3.1) < 0.08 else log(c, n))
        P.obj("LogEnd", ball(tuple(top), (0.09, 0.09, 0.09), 8, 4), "Lamp")
    for k in range(8):   # flames licking up between the logs
        a = 2 * math.pi * k / 8
        b = Vector((math.sin(a) * 0.35, math.cos(a) * 0.35, -0.7))
        P.obj("Lick", cone(b, b + Vector((math.sin(a) * 0.12, math.cos(a) * 0.12, 0.55 + 0.15 * (k % 2))), 0.13, 6), "Accent" if k % 2 else "Glow", 0)
    # the head of flame
    head = lathe([(0.0, 0.1), (0.42, 0.18), (0.62, 0.45), (0.64, 0.78), (0.55, 1.08), (0.36, 1.36), (0.16, 1.58), (0.0, 1.68)], 22, "z")
    P.obj("Head", head, lambda c, n: "Glow" if c.z > 1.2 or n.y < -0.3 else "Accent", 1)
    for k in range(13):   # tongues of flame round the head, the tallest at the top
        a = 2 * math.pi * k / 13
        if math.cos(a) > 0.75: continue   # keep the face clear
        b = Vector((math.sin(a) * 0.5, math.cos(a) * 0.5, 0.85 + 0.25 * math.cos(k)))
        tip = b + Vector((math.sin(a) * 0.4, math.cos(a) * 0.25, 0.55 + 0.2 * (k % 3)))
        P.obj("Tongue", pipe(bez(b, b + Vector((math.sin(a) * 0.15, math.cos(a) * 0.1, 0.25)), tip + Vector((-math.sin(a) * 0.15, 0, -0.2)), tip, 5), [0.16, 0.14, 0.11, 0.07, 0.04, 0.0], 7), "Glow" if k % 2 else "Accent", 1)
    for k in range(5):
        x = (k - 2) * 0.13
        P.obj("Crest", pipe(bez((x, 0.05, 1.45), (x * 1.2, 0.1, 1.75), (x * 1.5, 0.0, 2.0), (x * 1.8, -0.1, 2.2 - abs(k - 2) * 0.18), 5), [0.12, 0.1, 0.08, 0.05, 0.03, 0.0], 7), "Lamp" if k % 2 == 0 else "Glow", 1)
    # the face: charcoal sockets and blazing eyes, angry brows, a grin full of embers
    for s in (1, -1):
        P.obj("Socket", ball((s * 0.24, 0.53, 0.84), (0.19, 0.08, 0.15), 14, 7), "Dark")
        P.obj("Eye", ball((s * 0.24, 0.59, 0.83), (0.12, 0.05, 0.1), 12, 6), "Glass")
        P.obj("Iris", ball((s * 0.22, 0.63, 0.82), (0.06, 0.03, 0.07), 10, 5), "Accent")
        P.obj("Pupil", ball((s * 0.215, 0.65, 0.82), (0.025, 0.02, 0.045), 8, 4), "Dark")
        P.obj("Brow", hull([(s * 0.05, 0.62, 0.99), (s * 0.45, 0.5, 1.12), (s * 0.45, 0.42, 1.06), (s * 0.06, 0.55, 0.92), (s * 0.25, 0.62, 1.07), (s * 0.25, 0.5, 0.98)]), "Dark", 0, False)
    P.obj("Nose", ball((0, 0.64, 0.68), (0.07, 0.06, 0.06), 8, 4), "Accent")
    P.obj("Mouth", ball((0, 0.56, 0.47), (0.34, 0.08, 0.13), 16, 8), "Dark")
    P.obj("MouthGlow", ball((0, 0.58, 0.44), (0.24, 0.05, 0.07), 12, 6), "Lamp")
    for k in range(6):
        x = (k - 2.5) * 0.1
        P.obj("Tooth", cone((x, 0.62, 0.56 - abs(x) * 0.25), (x, 0.64, 0.46 - abs(x) * 0.25), 0.035, 4), "Glass", 0, False)
    # the molten gold crown
    P.obj("Crown", lathe([(0.47, 1.12), (0.5, 1.12), (0.46, 1.3), (0.43, 1.3)], 22, "z"), "Trim")
    for k in range(8):
        a = 2 * math.pi * k / 8
        b = Vector((math.sin(a) * 0.46, math.cos(a) * 0.46, 1.28))
        P.obj("CrownPoint", cone(b, b + Vector((math.sin(a) * 0.05, math.cos(a) * 0.05, 0.22)), 0.07, 4), "Trim", 0, False)
        P.obj("CrownGem", ball(tuple(b + Vector((math.sin(a) * 0.03, math.cos(a) * 0.03, -0.08))), (0.045, 0.045, 0.045), 6, 3), "Glass" if k % 2 else "Accent")
    # burning-log arms with fists of fire, swinging
    for s in (1, -1):
        sh = Vector((s * 0.45, 0.0, 0.25))
        name = "SwayR" if s > 0 else "SwayL"
        arm = [sh, sh + Vector((s * 0.45, 0.1, -0.15)), sh + Vector((s * 0.85, 0.3, 0.05)), sh + Vector((s * 1.0, 0.5, 0.35))]
        P.part(name, pipe(arm, [0.2, 0.18, 0.17, 0.15], 8), log, tuple(sh), 1)
        band = torus(0.19, 0.035, 0.0, 12, 4)
        for v in band.verts: v.co = Matrix.Rotation(math.radians(90), 3, "Y") @ v.co + arm[1]
        P.part(name, band, "Metal", tuple(sh))
        fist = arm[-1] + Vector((s * 0.05, 0.08, 0.12))
        P.part(name, ball(tuple(fist), (0.25, 0.25, 0.25), 12, 6), "Accent", tuple(sh), 1)
        for k in range(5):
            a = 2 * math.pi * k / 5
            b = fist + Vector((math.sin(a) * 0.15, math.cos(a) * 0.12, 0.1))
            P.part(name, cone(b, b + Vector((math.sin(a) * 0.08, 0.0, 0.32)), 0.08, 5), "Lamp", tuple(sh), 0)
    # a halo of sparks circling him
    for k in range(16):
        a = 2 * math.pi * k / 16
        c = Vector((math.sin(a) * 1.55, math.cos(a) * 1.25, 0.4 + 0.35 * math.sin(a * 3)))
        r = 0.08 if k % 4 == 0 else 0.05
        P.part("SpinSparks", hull([c + Vector((r, 0, 0)), c - Vector((r, 0, 0)), c + Vector((0, r, 0)), c - Vector((0, r, 0)), c + Vector((0, 0, r * 2)), c - Vector((0, 0, r * 2))]), "Lamp", (0, 0, 0.4), 0, False)
    P.part("Muzzle", ball((0, 0.62, 0.45), (0.08, 0.04, 0.05), 8, 4), "Lamp", (0, 0.62, 0.45))
    return P

def rear(P, deg, head_deg, head_names, head_c):
    """the whole boss pitched by deg about the wing axis (nose down when negative, so the top of a flat wing faces the player); the parts named in head_names only by
    head_deg about their own centre so the face still looks ahead. Paint was laid on before, so nothing is repainted."""
    Rb = Matrix.Rotation(math.radians(deg), 4, "X")
    hc = Rb @ Vector(head_c)
    Rh = Matrix.Translation(hc) @ Matrix.Rotation(math.radians(head_deg - deg), 4, "X") @ Matrix.Translation(-hc)
    for ob in P.parts:
        m = Rb if ob.name.split(".")[0] not in head_names else Rh @ Rb
        ob.data.transform(m)
    for ob in P.spin:
        loc = Rb @ Vector(ob.location)
        ob.data.transform(Matrix.Rotation(math.radians(deg), 4, "X"))
        ob.location = loc


# ----------------------------------------------------------------- the luna moth empress (in place of the star bear)
def C_moth():
    """A luna moth as big as a tent: broad pale-jade wings edged in plum with golden eye-spots, long swallow tails, a fluffy white body and
    ruff, a sweet face with huge glossy black eyes and a little smile, golden fern antennae, a crescent-moon tiara, and a full moon held
    in her front legs - the wings beat slowly."""
    P = Boss("moth", {"Base": ((0.42, 0.85, 0.62), 0.4), "Belly": ((0.97, 0.96, 0.92), 0.2), "Accent": ((0.52, 0.16, 0.40), 0.4),
                      "Trim": ((1.0, 0.80, 0.32), 0.85), "Glass": ((0.02, 0.02, 0.05), 0.95), "Dark": ((0.10, 0.05, 0.10), 0.4),
                      "Glow": ((0.30, 0.80, 0.95), 0.5), "Metal": ((0.75, 0.75, 0.8), 0.7), "Lamp": ((1.0, 0.78, 0.30), 0.8)})
    # the fluffy body: a thorax, a ruff of fur, an abdomen in soft rings
    P.obj("Thorax", ball((0, 0.4, 0.05), (0.36, 0.4, 0.33), 16, 8), "Belly", 1)
    for k in range(16):
        a = 2 * math.pi * k / 16
        b = Vector((math.sin(a) * 0.3, 0.62, 0.05 + math.cos(a) * 0.28))
        P.obj("Ruff", cone(b, b + Vector((math.sin(a) * 0.2, 0.06, math.cos(a) * 0.18)), 0.1, 5), "Belly", 0)
    for k in range(5):
        y = 0.0 - k * 0.24; r = 0.27 - k * 0.035
        P.obj("Ring", ball((0, y, -0.02 - k * 0.03), (r, 0.16, r * 0.9), 14, 6), "Belly" if k % 2 == 0 else "Glow", 1)
    # the head and its face
    P.obj("Head", ball((0, 0.86, 0.12), (0.31, 0.26, 0.28), 16, 8), "Belly", 1)
    for s in (1, -1):
        P.obj("Eye", ball((s * 0.19, 1.0, 0.17), (0.15, 0.12, 0.16), 14, 7), "Glass")
        P.obj("Shine", ball((s * 0.15, 1.1, 0.25), (0.045, 0.02, 0.045), 8, 4), "Lamp")
        P.obj("Shine2", ball((s * 0.23, 1.1, 0.1), (0.02, 0.01, 0.02), 6, 3), "Lamp")
        P.obj("Cheek", ball((s * 0.25, 1.03, -0.02), (0.06, 0.02, 0.035), 8, 4), "Accent")
        P.obj("Lash", hull([(s * 0.08, 1.07, 0.32), (s * 0.32, 1.0, 0.33), (s * 0.32, 0.98, 0.3), (s * 0.08, 1.05, 0.29), (s * 0.36, 0.99, 0.38)]), "Dark", 0, False)
        # golden fern antennae
        ant = bez((s * 0.08, 0.98, 0.35), (s * 0.2, 1.15, 0.65), (s * 0.45, 1.25, 0.85), (s * 0.7, 1.2, 1.0), 9)
        P.obj("Antenna", pipe(ant, [0.03] * 9 + [0.015], 6), "Trim")
        for k in range(2, 10):
            q = ant[k]; L = 0.2 * math.sin(math.pi * k / 10) + 0.04
            for side in (-1, 1):
                P.obj("Barb", cone(q, q + Vector((s * 0.03, -L * 0.6, side * L)), 0.014, 4), "Trim", 0, False)
        # front legs cradling the moon
        P.obj("Leg", pipe(bez((s * 0.18, 0.7, -0.15), (s * 0.3, 0.9, -0.4), (s * 0.28, 1.1, -0.5), (s * 0.18, 1.18, -0.45), 5), [0.04, 0.035, 0.03, 0.03, 0.025, 0.02], 6), "Belly")
        for k in range(2):
            y = 0.3 - k * 0.3
            P.obj("Leg", pipe([(s * 0.25, y, -0.2), (s * 0.55, y + 0.05, -0.45), (s * 0.6, y - 0.05, -0.7)], [0.035, 0.03, 0.015], 6), "Belly")
    P.obj("Smile", pipe(bez((-0.09, 1.07, -0.02), (-0.04, 1.1, -0.07), (0.04, 1.1, -0.07), (0.09, 1.07, -0.02), 6), [0.015] * 7, 5), "Dark")
    # the crescent-moon tiara and a jewel
    arc = [Vector((math.sin(t) * 0.16, 1.02, 0.42 + math.cos(t) * 0.16)) for t in [math.radians(-120 + 240 * i / 12) for i in range(13)]]
    P.obj("Crescent", pipe(arc, [0.0] + [0.045 * math.sin(math.pi * i / 12) + 0.01 for i in range(1, 12)] + [0.0], 6), "Lamp")
    P.obj("Band", pipe(bez((-0.27, 0.95, 0.3), (-0.12, 1.06, 0.37), (0.12, 1.06, 0.37), (0.27, 0.95, 0.3), 8), [0.022] * 9, 5), "Trim")
    P.obj("Jewel", ball((0, 1.09, 0.36), (0.05, 0.03, 0.06), 8, 4), "Glow")
    # the full moon she holds
    P.obj("Moon", ball((0, 1.22, -0.5), (0.22, 0.22, 0.22), 16, 8), lambda c, n: "Metal" if speckle(c, 4.0) < 0.2 else "Trim")
    # the wings: jade, plum edged, golden eye-spots, long swallow tails
    for s in (1, -1):
        name = "FlapR" if s > 0 else "FlapL"
        hub = Vector((s * 0.28, 0.4, 0.15))
        X = lambda p, s=s: (s * p[0], p[1], p[2])
        fore = curve(((0.3, 0.65, 0.18), (0.9, 1.1, 0.3), (1.55, 1.25, 0.4), (2.05, 1.1, 0.45)),
                     ((2.05, 1.1, 0.45), (2.2, 0.75, 0.42), (2.05, 0.3, 0.36), (1.65, 0.1, 0.3)),
                     ((1.65, 0.1, 0.3), (1.2, 0.05, 0.24), (0.7, 0.2, 0.18), (0.3, 0.35, 0.15)))
        hind = curve(((0.3, 0.25, 0.12), (0.95, 0.2, 0.18), (1.55, 0.0, 0.2), (1.5, -0.55, 0.15)),
                     ((1.5, -0.55, 0.15), (1.4, -1.0, 0.1), (1.1, -1.7, 0.0), (1.0, -2.3, -0.1)),
                     ((1.0, -2.3, -0.1), (0.85, -1.6, -0.02), (0.55, -0.6, 0.05), (0.3, -0.05, 0.1)))
        fore = [X(p) for p in fore]; hind = [X(p) for p in hind]
        spots = [(Vector((s * 1.3, 0.62, 0.32)), 1.0), (Vector((s * 1.02, -0.45, 0.16)), 0.9)]
        def paint(c, n, outline, spots=spots, s=s, hub=hub):
            c = Matrix.Rotation(math.radians(s * 14), 3, "Y") @ (c - hub) + hub   # back to the flat wing the spots are drawn on
            for sp, k in spots:
                d = ((c - sp) * Vector((1, 1, 0))).length / k
                if d < 0.09: return "Dark"
                if d < 0.15: return "Lamp"
                if d < 0.21: return "Trim"
                if d < 0.25: return "Accent"
            e = min(((c - Vector(o)) * Vector((1, 1, 0))).length for o in outline)
            if e < 0.07: return "Accent"
            if e < 0.13 and speckle(c, 9) < 0.5: return "Trim"
            return "Base"
        lift = lambda bm, s=s, hub=hub: tilt(bm, "Y", -s * 14, hub)   # the wings held up in a V
        P.part(name, lift(sheet(wing_polys(X((1.2, 0.65, 0.3)), fore, 8), 0.035)), lambda c, n, o=fore, p=paint: p(c, n, o), tuple(hub), 0, False)
        P.part(name, lift(sheet(wing_polys(X((0.95, -0.4, 0.12)), hind, 8), 0.035)), lambda c, n, o=hind, p=paint: p(c, n, o), tuple(hub), 0, False)
        for t in (fore[4], fore[9], fore[14]): P.part(name, lift(pipe([hub, Vector(t) * 0.82 + hub * 0.18], [0.025, 0.01], 5)), "Accent", tuple(hub))
        P.part(name, lift(ball(X((1.0, -2.3, -0.1)), (0.06, 0.06, 0.04), 6, 3)), "Glow", tuple(hub))
    P.part("Muzzle", ball((0, 1.42, -0.5), (0.07, 0.04, 0.07), 8, 4), "Lamp", (0, 1.42, -0.5))
    rear(P, -30, -6, ("Head", "Eye", "Shine", "Shine2", "Cheek", "Lash", "Antenna", "Barb", "Smile", "Crescent", "Band", "Jewel"), (0, 0.86, 0.12))
    return P


# ----------------------------------------------------------------- the sasquatch king (in place of the forest guardian, the last boss)
def C_bigfoot():
    """The last boss: Bigfoot, the king of the woods - a towering shaggy giant striding through the air on enormous feet, a broad leathery
    face with a heavy brow, glowing amber eyes and a fanged grin, great antlers hung with lanterns and crowned in gold, a royal red cloak
    with a fur collar, a lantern staff in one fist and a log club in the other, fireflies circling him."""
    P = Boss("bigfoot", {"Base": ((0.36, 0.22, 0.12), 0.15), "Belly": ((0.66, 0.48, 0.34), 0.25), "Accent": ((0.62, 0.07, 0.09), 0.4),
                         "Trim": ((1.0, 0.78, 0.26), 0.85), "Glass": ((0.97, 0.95, 0.88), 0.5), "Dark": ((0.05, 0.03, 0.02), 0.5),
                         "Glow": ((0.80, 1.0, 0.40), 0.5), "Metal": ((0.30, 0.28, 0.26), 0.6), "Lamp": ((1.0, 0.70, 0.20), 0.8)})
    fur = lambda c, n: "Base"
    # the torso, chest and shaggy fur
    P.obj("Torso", lathe([(0.0, -0.75), (0.55, -0.7), (0.68, -0.2), (0.86, 0.4), (0.93, 0.75), (0.55, 1.05), (0.0, 1.1)], 22, "z"), "Base", 1)
    P.obj("Chest", ball((0, 0.8, 0.38), (0.42, 0.13, 0.4), 16, 8), "Belly", 1)
    rng = random.Random(3)
    for k in range(0):
        a = rng.uniform(0, 2 * math.pi); z = rng.uniform(-0.65, 0.8)
        if math.cos(a) > 0.55 and -0.15 < z < 0.7: continue   # keep the chest bare
        r = 0.7 + 0.1 * math.sin(z * 2)
        b = Vector((math.sin(a) * r, math.cos(a) * r, z))
        P.obj("Shag", cone(b, b + Vector((math.sin(a) * 0.18, math.cos(a) * 0.14, -0.15)), 0.09, 4), "Base", 0, False)
    # the head and his face
    P.obj("Head", ball((0, 0.2, 1.4), (0.55, 0.5, 0.52), 18, 9), fur, 1)
    P.obj("Face", ball((0, 0.52, 1.3), (0.42, 0.2, 0.38), 16, 8), "Belly", 1)
    P.obj("BrowRidge", hull([(-0.36, 0.62, 1.5), (0.36, 0.62, 1.5), (-0.4, 0.5, 1.6), (0.4, 0.5, 1.6), (0, 0.7, 1.45), (-0.3, 0.6, 1.42), (0.3, 0.6, 1.42), (0, 0.55, 1.62)]), "Base", 0, False)
    for s in (1, -1):
        P.obj("EyeWhite", ball((s * 0.16, 0.66, 1.38), (0.13, 0.06, 0.1), 12, 6), "Glass")
        P.obj("Iris", ball((s * 0.15, 0.7, 1.37), (0.08, 0.035, 0.08), 10, 5), "Lamp")
        P.obj("Pupil", ball((s * 0.145, 0.725, 1.37), (0.035, 0.015, 0.04), 8, 4), "Dark")
        P.obj("Brow", hull([(s * 0.04, 0.73, 1.48), (s * 0.32, 0.68, 1.56), (s * 0.32, 0.62, 1.52), (s * 0.05, 0.68, 1.44)]), "Dark", 0, False)
        P.obj("Ear", ball((s * 0.47, 0.2, 1.38), (0.08, 0.1, 0.13), 8, 4), "Belly")
        for k in range(4):   # cheek whiskers of fur
            b = Vector((s * 0.32, 0.45, 1.25 - k * 0.08))
            P.obj("Whisk", cone(b, b + Vector((s * 0.22, -0.02, -0.08 - k * 0.02)), 0.06, 4), "Base", 0, False)
        # antlers: a great branching rack, gold tipped, lanterns hanging
        root = Vector((s * 0.28, 0.15, 1.75))
        main = bez(root, root + Vector((s * 0.25, 0.0, 0.25)), root + Vector((s * 0.65, -0.05, 0.35)), root + Vector((s * 0.95, -0.1, 0.65)), 7)
        P.obj("Antler", pipe(main, [0.08, 0.075, 0.07, 0.06, 0.05, 0.045, 0.035, 0.02], 7), "Belly")
        P.obj("AntlerTip", ball(tuple(main[-1]), (0.04, 0.04, 0.04), 6, 3), "Trim")
        for t, (dx, dz) in ((2, (0.05, 0.4)), (4, (0.1, 0.45)), (6, (0.25, 0.25))):
            q = main[t]; tip = q + Vector((s * dx, 0.08, dz))
            P.obj("Tine", pipe([q, tip], [0.045, 0.02], 6), "Belly")
            P.obj("AntlerTip", ball(tuple(tip), (0.03, 0.03, 0.03), 6, 3), "Trim")
        for t in (3, 5):
            q = main[t]
            P.obj("LanternLine", pipe([q, q + Vector((0, 0, -0.22))], [0.008, 0.008], 4), "Dark")
            P.obj("LanternCap", lathe([(0.0, -0.2), (0.07, -0.24), (0.05, -0.26)], 8, "z", tuple(q)), "Metal")
            P.obj("Lantern", lathe([(0.05, -0.26), (0.055, -0.38), (0.0, -0.4)], 8, "z", tuple(q)), "Lamp")
    # the fanged grin and a broad nose
    P.obj("Nose", ball((0, 0.72, 1.26), (0.12, 0.07, 0.08), 10, 5), "Dark")
    P.obj("Mouth", ball((0, 0.66, 1.1), (0.24, 0.07, 0.09), 14, 6), "Dark")
    for s in (1, -1):
        P.obj("Fang", cone((s * 0.11, 0.71, 1.17), (s * 0.1, 0.73, 1.05), 0.035, 4), "Glass", 0, False)
        P.obj("Tusk", cone((s * 0.17, 0.69, 1.05), (s * 0.18, 0.72, 1.17), 0.03, 4), "Glass", 0, False)
    # the gold crown between the antlers
    P.obj("Crown", lathe([(0.36, 1.74), (0.4, 1.74), (0.38, 1.96), (0.34, 1.96)], 22, "z", (0, 0.15, 0)), "Trim")
    for k in range(6):
        a = 2 * math.pi * k / 6
        b = Vector((math.sin(a) * 0.37, 0.15 + math.cos(a) * 0.37, 1.94))
        P.obj("CrownPoint", cone(b, b + Vector((0, 0, 0.3)), 0.08, 4), "Trim", 0, False)
        P.obj("CrownPearl", ball(tuple(b + Vector((0, 0, 0.32))), (0.04, 0.04, 0.04), 6, 3), "Glass")
        P.obj("CrownGem", ball(tuple(b + Vector((math.sin(a) * 0.02, math.cos(a) * 0.02, -0.07))), (0.04, 0.04, 0.04), 6, 3), "Accent" if k % 2 else "Glow")
    # the royal cloak and its fur collar
    def cpt(u, v):
        a = math.radians(-120 + 240 * u)
        r = 0.85 + 0.35 * v
        return (math.sin(a) * r, -0.05 - math.cos(a) * r * 0.75 - 0.08 * v, 0.95 - 1.85 * v + 0.06 * math.sin(u * 18))
    polys = [[cpt(i / 10, j / 6), cpt((i + 1) / 10, j / 6), cpt((i + 1) / 10, (j + 1) / 6), cpt(i / 10, (j + 1) / 6)] for i in range(10) for j in range(6)]
    P.part("Cloth", sheet(polys, 0.03), lambda c, n: "Trim" if c.z < -0.78 else "Accent", (0, 0, 0), 0, False)
    collar = torus(0.62, 0.13, 0.98, 22, 7)
    for v in collar.verts: v.co.y += 0.05
    P.obj("Collar", collar, "Glass", 1)
    # arms: a lantern staff in the right fist, a log club in the left
    for s in (1, -1):
        sh = Vector((s * 0.75, 0.15, 0.7))
        el = sh + Vector((s * 0.35, 0.25, -0.35)); wr = el + Vector((s * 0.1, 0.4, -0.05))
        P.obj("Arm", pipe([sh, el, wr], [0.26, 0.21, 0.18], 10), fur, 1)
        P.obj("Hand", ball(tuple(wr + Vector((0, 0.12, 0))), (0.17, 0.17, 0.17), 10, 5), "Belly", 1)
        for k in range(5):
            a = 2 * math.pi * k / 5
            b = sh + (el - sh) * 0.5 + Vector((math.sin(a) * 0.2, math.cos(a) * 0.15, 0))
            P.obj("ArmShag", cone(b, b + Vector((s * 0.12, -0.05, -0.18)), 0.07, 4), "Base", 0, False)
    hr = Vector((1.2, 1.07, 0.3)); hl = Vector((-1.2, 1.07, 0.3))
    P.obj("Staff", pipe([hr + Vector((0, 0, -0.9)), hr + Vector((0, 0, 1.05))], [0.05, 0.05], 8), lambda c, n: "Trim" if (c.z * 4) % 1.0 < 0.12 else "Base")
    top = hr + Vector((0, 0, 1.05))
    P.obj("StaffCap", lathe([(0.0, 0.0), (0.16, 0.06), (0.14, 0.1)], 10, "z", tuple(top)), "Trim")
    P.obj("StaffLamp", lathe([(0.13, 0.1), (0.15, 0.4), (0.0, 0.42)], 10, "z", tuple(top)), "Lamp")
    for k in range(4):
        a = 2 * math.pi * k / 4 + 0.4
        P.obj("Cage", pipe([top + Vector((math.sin(a) * 0.15, math.cos(a) * 0.15, 0.08)), top + Vector((math.sin(a) * 0.16, math.cos(a) * 0.16, 0.42))], [0.015, 0.015], 4), "Metal")
    P.obj("StaffTop", lathe([(0.17, 0.42), (0.1, 0.52), (0.0, 0.62)], 10, "z", tuple(top)), "Trim")
    P.obj("Club", pipe([hl + Vector((0, -0.1, -0.3)), hl + Vector((-0.1, 0.1, 0.4)), hl + Vector((-0.2, 0.25, 0.9))], [0.07, 0.16, 0.2], 10), lambda c, n: "Dark" if speckle(c, 3) < 0.2 else "Belly")
    for k in range(4):
        b = hl + Vector((-0.12 - 0.03 * k, 0.15, 0.5 + 0.12 * k))
        P.obj("Knot", ball(tuple(b + Vector((-0.15, 0.0, 0))), (0.06, 0.06, 0.06), 6, 3), "Base")
    # legs striding on enormous feet
    for s, k in ((1, 0), (-1, 1)):
        hip = Vector((s * 0.35, 0.0, -0.6))
        name = "Sway%d" % k
        P.part(name, pipe([hip, hip + Vector((s * 0.05, 0.1, -0.45)), hip + Vector((s * 0.08, 0.0, -0.85))], [0.28, 0.23, 0.2], 10), fur, tuple(hip), 1)
        foot = hip + Vector((s * 0.08, 0.2, -0.98))
        P.part(name, ball(tuple(foot), (0.24, 0.42, 0.13), 12, 6), "Belly", tuple(hip), 1)
        for t in range(5):
            x = (t - 2) * 0.09
            P.part(name, ball(tuple(foot + Vector((x, 0.42 - abs(t - 2) * 0.04, 0.0))), (0.055, 0.07, 0.05), 6, 3), "Belly", tuple(hip))
    # fireflies circling him
    for k in range(14):
        a = 2 * math.pi * k / 14
        P.part("SpinFireflies", ball((math.sin(a) * 1.7, math.cos(a) * 1.4, 0.5 + 0.4 * math.sin(a * 2)), (0.05, 0.05, 0.05), 6, 3), "Glow", (0, 0, 0.5))
    P.part("Muzzle", ball(tuple(top + Vector((0, 0, 0.25))), (0.08, 0.08, 0.08), 8, 4), "Lamp", tuple(top + Vector((0, 0, 0.25))))
    return P


# ----------------------------------------------------------------- the moon wolf king (2026-10-12, in place of the sasquatch king, the last boss)
def C_wolf():
    """The last boss: the moon wolf king - a huge silver-blue spirit wolf leaping at the player, a thick shaggy ruff, a snarling muzzle full
    of fangs, blazing amber eyes under a heavy brow, tall ears, a gold collar with a moon medallion, glowing spirit flames rising along his
    back, a great plume of a tail of aurora light that sways, forelegs reaching with claws out, a full moon and a halo of stars behind his
    head, and spirit wisps circling him."""
    P = Boss("wolf", {"Base": ((0.36, 0.42, 0.62), 0.35), "Belly": ((0.88, 0.91, 0.98), 0.3), "Accent": ((0.20, 0.24, 0.42), 0.35),
                      "Trim": ((1.0, 0.78, 0.26), 0.85), "Glass": ((0.97, 0.97, 0.95), 0.6), "Dark": ((0.04, 0.04, 0.07), 0.5),
                      "Glow": ((0.35, 0.90, 1.0), 0.5), "Metal": ((0.95, 0.93, 0.80), 0.5), "Lamp": ((1.0, 0.65, 0.12), 0.8)})
    coat = lambda c, n: "Belly" if n.z < -0.35 else ("Accent" if n.z > 0.7 and abs(c.x) < 0.25 else "Base")
    # the body: deep chest forward, a lean waist, haunches behind
    P.obj("Torso", loft([(1.0, 0.3, 0.32, 0, 0.35), (0.7, 0.5, 0.55, 0, 0.25), (0.25, 0.48, 0.5, 0, 0.18), (-0.25, 0.38, 0.38, 0, 0.2),
                         (-0.7, 0.42, 0.42, 0, 0.25), (-1.05, 0.34, 0.34, 0, 0.3), (-1.3, 0.12, 0.12, 0, 0.32)], 18), coat, 1)
    # the shaggy ruff round his neck and shoulders, and shag down his flanks
    for ring, (y, z, R, L) in enumerate(((0.9, 0.5, 0.52, 0.32), (0.65, 0.42, 0.6, 0.3), (0.4, 0.35, 0.55, 0.22))):
        for k in range(18):
            a = 2 * math.pi * (k + 0.5 * ring) / 18
            b = Vector((math.sin(a) * R, y, z + math.cos(a) * R * 0.95))
            d = Vector((math.sin(a) * 0.8, -0.6, math.cos(a) * 0.8)).normalized()
            P.obj("Ruff", cone(b, b + d * L, 0.13, 5), "Belly" if math.cos(a) < -0.3 else "Base", 0, False)
    for k in range(12):
        y = 0.1 - k * 0.11; s = 1 if k % 2 else -1
        b = Vector((s * 0.4, y, 0.05))
        P.obj("Shag", cone(b, b + Vector((s * 0.12, -0.18, -0.2)), 0.08, 4), "Base", 0, False)
    # the head: skull, muzzle, snarling jaw
    P.obj("Skull", ball((0, 1.2, 0.72), (0.36, 0.34, 0.32), 16, 8), coat, 1)
    P.obj("Muzzle", loft([(1.35, 0.2, 0.17, 0, 0.66), (1.6, 0.16, 0.13, 0, 0.62), (1.82, 0.11, 0.09, 0, 0.6), (1.9, 0.06, 0.05, 0, 0.6)], 14),
          lambda c, n: "Belly" if n.z < -0.2 else "Base", 1)
    P.obj("Nose", ball((0, 1.9, 0.66), (0.08, 0.06, 0.06), 10, 5), "Dark")
    P.obj("Jaw", loft([(1.35, 0.16, 0.06, 0, 0.47), (1.65, 0.12, 0.05, 0, 0.44), (1.8, 0.07, 0.03, 0, 0.45)], 12), "Belly", 1)
    P.obj("Mouth", ball((0, 1.58, 0.52), (0.13, 0.25, 0.05), 12, 6), "Dark")
    P.obj("Tongue", ball((0, 1.58, 0.48), (0.08, 0.2, 0.03), 10, 5), "Lamp")
    for s in (1, -1):
        for k in range(3):
            y = 1.55 + k * 0.1
            P.obj("Fang", cone((s * (0.12 - k * 0.02), y, 0.58), (s * (0.115 - k * 0.02), y + 0.01, 0.46 + 0.02 * k), 0.025 - k * 0.004, 5), "Glass", 0, False)
            P.obj("Fang", cone((s * (0.1 - k * 0.02), y - 0.04, 0.45), (s * (0.095 - k * 0.02), y - 0.03, 0.54), 0.02, 5), "Glass", 0, False)
        P.obj("Canine", cone((s * 0.14, 1.72, 0.6), (s * 0.13, 1.74, 0.42), 0.04, 6), "Glass", 0, False)
        # the eyes: amber, slit-pupilled, glowing, under a heavy brow
        P.obj("Socket", ball((s * 0.17, 1.44, 0.82), (0.11, 0.06, 0.07), 10, 5), "Dark")
        P.obj("Eye", ball((s * 0.17, 1.47, 0.82), (0.085, 0.04, 0.055), 10, 5), "Lamp")
        P.obj("Pupil", ball((s * 0.17, 1.5, 0.82), (0.015, 0.02, 0.045), 6, 3), "Dark")
        P.obj("Brow", hull([(s * 0.05, 1.5, 0.92), (s * 0.3, 1.38, 0.97), (s * 0.3, 1.33, 0.92), (s * 0.06, 1.46, 0.87), (s * 0.18, 1.48, 0.97)]), "Accent", 0, False)
        P.obj("Cheek", cone((s * 0.3, 1.2, 0.6), (s * 0.55, 1.05, 0.5), 0.12, 5), "Belly", 0, False)
        # tall pointed ears, pale inside
        ear = [(s * 0.17, 1.15, 0.95), (s * 0.36, 1.1, 0.92), (s * 0.32, 1.02, 1.42), (s * 0.27, 1.16, 1.0), (s * 0.25, 1.05, 0.98)]
        P.obj("Ear", hull(ear), "Base", 0, False)
        P.obj("EarIn", hull([(s * 0.2, 1.17, 1.0), (s * 0.32, 1.13, 0.98), (s * 0.3, 1.08, 1.3), (s * 0.26, 1.15, 1.02)]), "Belly", 0, False)
        # forelegs reaching for the player, claws out; hind legs pushing back off the leap
        sh = Vector((s * 0.32, 0.75, 0.05))
        P.obj("Foreleg", pipe([sh, sh + Vector((s * 0.06, 0.35, -0.3)), sh + Vector((s * 0.05, 0.75, -0.35))], [0.17, 0.12, 0.1], 10), coat, 1)
        paw = sh + Vector((s * 0.05, 0.85, -0.36))
        P.obj("Paw", ball(tuple(paw), (0.14, 0.15, 0.09), 10, 5), "Belly", 1)
        for k in range(4):
            x = (k - 1.5) * 0.065
            P.obj("Claw", cone(tuple(paw + Vector((x, 0.1, -0.02))), tuple(paw + Vector((x * 1.2, 0.24, -0.1))), 0.025, 5), "Glass", 0, False)
        hip = Vector((s * 0.3, -0.95, 0.15))
        P.obj("Haunch", ball(tuple(hip + Vector((0, 0.05, 0.0))), (0.24, 0.32, 0.3), 12, 6), coat, 1)
        P.obj("Hindleg", pipe([hip, hip + Vector((s * 0.05, -0.15, -0.38)), hip + Vector((s * 0.05, -0.5, -0.45)), hip + Vector((s * 0.05, -0.75, -0.48))], [0.15, 0.1, 0.07, 0.06], 8), coat)
        P.obj("Paw", ball(tuple(hip + Vector((s * 0.05, -0.8, -0.5))), (0.09, 0.13, 0.06), 8, 4), "Belly", 1)
    # the gold collar and its moon medallion
    collar = torus(0.4, 0.05, 0.0, 26, 6)
    xf(collar, Matrix.Rotation(math.radians(70), 3, "X"), (0, 0.95, 0.45))
    P.obj("Collar", collar, "Trim")
    for k in range(10):
        a = 2 * math.pi * k / 10
        c = Matrix.Rotation(math.radians(70), 3, "X") @ Vector((math.sin(a) * 0.4, math.cos(a) * 0.4, 0)) + Vector((0, 0.95, 0.45))
        P.obj("Stud", ball(tuple(c), (0.045, 0.045, 0.045), 6, 3), "Metal")
    P.obj("Medallion", lathe([(0.0, 0.0), (0.14, 0.0), (0.14, 0.04), (0.0, 0.05)], 16, "y", (0, 1.24, 0.17)), "Trim")
    P.obj("MedalMoon", ball((0, 1.3, 0.17), (0.09, 0.025, 0.09), 10, 5), "Glow")
    # spirit flames rising along his back
    for k in range(9):
        y = 0.85 - k * 0.24; h = 0.45 - abs(k - 3) * 0.04
        b = Vector((0, y, 0.6 - abs(y - 0.3) * 0.12))
        P.obj("SpiritFlame", pipe(bez(b, b + Vector((0.0, -0.05, h * 0.4)), b + Vector((0.08 * (1 if k % 2 else -1), -0.15, h * 0.75)), b + Vector((0, -0.25, h)), 5),
                                  [0.12, 0.1, 0.08, 0.05, 0.025, 0.0], 7), "Glow" if k % 2 else "Belly", 0)
    # the aurora tail: a great plume that sways
    tb = Vector((0, -1.3, 0.35))
    tail = bez(tb, tb + Vector((0, -0.45, 0.25)), tb + Vector((0.3, -0.9, 0.75)), tb + Vector((0.1, -1.15, 1.3)), 8)
    tr = [0.13, 0.2, 0.26, 0.29, 0.29, 0.26, 0.2, 0.12, 0.0]
    P.part("SwayTail", pipe(tail, tr, 12), lambda c, n, tb=tb: "Glow" if (c - tb).length > 1.1 else ("Belly" if (c - tb).length > 0.75 else "Base"), tuple(tb), 1)
    for i in range(2, 8):
        for k in range(5):
            a = 2 * math.pi * k / 5 + i
            q = tail[i] + Vector((math.sin(a) * tr[i] * 0.9, 0, math.cos(a) * tr[i] * 0.9))
            P.part("SwayTail", cone(tuple(q), tuple(q + Vector((math.sin(a) * 0.12, -0.12, math.cos(a) * 0.1 + 0.05))), 0.06, 4), "Glow" if i > 4 else "Belly", tuple(tb), 0, False)
    # the full moon behind his head, ringed with stars
    moon_c = Vector((0, 0.55, 1.55))
    P.obj("Moon", ball(tuple(moon_c), (0.55, 0.06, 0.55), 22, 10), lambda c, n: "Metal" if speckle(c, 4.0) < 0.25 else "Glass")
    P.obj("MoonRim", xf(torus(0.6, 0.035, 0.0, 30, 5), Matrix.Rotation(math.radians(90), 3, "X"), tuple(moon_c)), "Glow")
    for k in range(8):
        a = 2 * math.pi * k / 8
        c = moon_c + Vector((math.sin(a) * 0.8, -0.02, math.cos(a) * 0.8))
        r = 0.09 if k % 2 == 0 else 0.06
        P.obj("Star", hull([c + Vector((r, 0, 0)), c - Vector((r, 0, 0)), c + Vector((0, 0, r * 1.8)), c - Vector((0, 0, r * 1.8)), c + Vector((0, 0.03, 0)), c - Vector((0, 0.03, 0))]), "Lamp", 0, False)
    # spirit wisps circling him
    for k in range(12):
        a = 2 * math.pi * k / 12
        c = Vector((math.sin(a) * 1.6, -0.1 + math.cos(a) * 1.7, 0.3 + 0.35 * math.sin(a * 2)))
        P.part("SpinWisps", pipe([c, c + Vector((math.cos(a) * 0.2, -math.sin(a) * 0.2, 0.08))], [0.06, 0.0], 6), "Glow", (0, -0.1, 0.3))
        P.part("SpinWisps", ball(tuple(c), (0.065, 0.065, 0.065), 6, 3), "Belly", (0, -0.1, 0.3))
    P.part("Muzzle", ball((0, 1.75, 0.52), (0.08, 0.05, 0.05), 8, 4), "Lamp", (0, 1.75, 0.52))
    return P


BOSSES = [("firefly", C_firefly), ("owl", C_owl), ("ember", C_ember), ("moth", C_moth), ("wolf", C_wolf)]

if __name__ == "__main__":
    os.makedirs(AB.OUT, exist_ok=True)
    for bid, fn in BOSSES:
        if ONLY and bid not in ONLY: continue
        fn().finish()
    print("DONE")
