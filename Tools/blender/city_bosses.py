# Sky Squad, downtown's five bosses (2026-10-11: "the rest of the worlds that have no bosses yet"): the billboard blimp, the news chopper,
# the king pigeon, the traffic titan and the skyscraper fortress. Built from code like the other worlds' bosses (alien_bosses.py lends its
# Boss class and shapes).
# Run: blender -b -P Tools/blender/city_bosses.py -- <out dir> [export] [ids,comma,separated]
# Conventions as alien_bosses.py: +Y nose, +Z up, +X right; "Prop*" spin about the nose, "Rotor*" about up, "TailRotor" about the wing axis,
# "Flap*" rock about the nose axis, "Sway*" about the wing axis, "Spin*" turn slowly about up, "Muzzle" is where his shots leave from.
import bpy, bmesh, math, sys, os, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mathutils import Vector, Matrix
from enemy_planes import loft, sweep, lathe, box, hull, tube, mirror_x, airfoil
import alien_bosses as AB
from alien_bosses import Boss, xf, ball, pipe, cone, bez, torus, sheet, grow, ang

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ONLY = argv[2].split(",") if len(argv) > 2 and argv[2] else None

TAXI = ((1.0, 0.76, 0.06), 0.6)
GOLD = ((0.98, 0.76, 0.22), 0.8)
STEEL = ((0.55, 0.58, 0.62), 0.7)


def fine(keys, step=0.08):
    secs = []
    for a0, a1 in zip(keys, keys[1:]):
        n = max(2, int((a1[0] - a0[0]) / step))
        secs += [tuple(u + (v - u) * i / n for u, v in zip(a0, a1)) for i in range(n)]
    secs.append(keys[-1])
    return secs

def fan(hub, tips, thick=0.02, scallop=0.12):
    polys = []
    for a, b in zip(tips, tips[1:]):
        mid = (a + b) * 0.5 + (hub - (a + b) * 0.5) * scallop
        polys.append([hub, a, mid]); polys.append([hub, mid, b])
    return sheet([[tuple(p) for p in poly] for poly in polys], thick)

def rings_of(profile, step=0.12):
    """(y, r) keys -> loft rings every step along y, round sections."""
    out = []
    for (y0, r0), (y1, r1) in zip(profile, profile[1:]):
        n = max(1, int(abs(y1 - y0) / step))
        for i in range(n):
            t = i / n; s = 0.5 - 0.5 * math.cos(math.pi * t)
            out.append((y0 + (y1 - y0) * t, r0 + (r1 - r0) * s, r0 + (r1 - r0) * s, 0, 0))
    out.append((profile[-1][0], profile[-1][1], profile[-1][1], 0, 0))
    return out

def at(bm, t):
    return xf(bm, None, t)


# ================================================================= 1. the billboard blimp
def C_blimp():
    """An advertising airship over downtown: a silver envelope with a red nose cap and red fins, glowing LED screens down both flanks, a neon
    billboard standing on its back facing you, a gondola with lit windows and two propellers."""
    P = Boss("blimp", {"Base": ((0.82, 0.84, 0.88), 0.55), "Belly": ((0.62, 0.65, 0.70), 0.5), "Accent": ((0.85, 0.12, 0.12), 0.6), "Trim": GOLD,
                       "Glass": ((0.10, 0.80, 1.0), 0.9), "Dark": ((0.06, 0.07, 0.09), 0.5), "Glow": ((0.15, 0.85, 1.0), 0.5),
                       "Metal": STEEL, "Lamp": ((1.0, 0.30, 0.70), 0.8)})
    prof = [(-2.35, 0.06), (-2.0, 0.5), (-1.2, 0.92), (0.0, 1.05), (1.2, 0.95), (1.85, 0.62), (2.15, 0.25), (2.25, 0.04)]
    def env(c, n):
        if c.y > 1.8: return "Accent"
        if abs(n.x) > 0.55 and abs(c.y) < 1.15 and -0.35 < c.z < 0.45:
            if (c.y * 5.0) % 1.0 < 0.12 or abs(c.z - 0.05) < 0.03: return "Dark"
            return "Glass" if (int((c.y + 2) * 2.5) + (1 if c.z > 0.05 else 0)) % 3 else "Lamp"
        if abs(n.x) > 0.5 and abs(c.y) < 1.25 and -0.45 < c.z < 0.55: return "Dark"
        if abs(c.y + 1.45) < 0.06 or abs(c.y - 1.45) < 0.06: return "Accent"
        return "Belly" if n.z < -0.5 else "Base"
    P.obj("Body", loft(rings_of(prof, 0.1), 32), env, 0)
    # four red tail fins
    for k in range(4):
        a = math.radians(45 + 90 * k)
        secs = [(0.0, airfoil(-1.55, -2.25, 0.08, 0.0)), (0.45, airfoil(-1.75, -2.3, 0.06, 0.0)), (0.85, airfoil(-2.0, -2.38, 0.05, 0.0))]
        fb = sweep(secs, "x")
        for v in fb.verts:
            v.co += Vector((0.55, 0, 0))
            v.co = Matrix.Rotation(a, 3, "Y") @ v.co
        P.obj("Fin", fb, lambda c, n: "Trim" if math.hypot(c.x, c.z) > 1.3 else "Accent", 0, False)
    # the neon billboard on its back, facing the player
    P.obj("Pylon", box((-0.45, 0.0, 1.15), (0.08, 0.08, 0.35)), "Metal", 0, False)
    P.obj("Pylon", box((0.45, 0.0, 1.15), (0.08, 0.08, 0.35)), "Metal", 0, False)
    P.obj("Board", box((0, 0.0, 1.62), (1.7, 0.12, 0.72)), "Dark", 0, False)
    for i in range(6):
        for j in range(3):
            slot = "Lamp" if (i + j) % 2 else "Glass"
            if j == 1 and 1 <= i <= 4: slot = "Trim"
            P.obj("Pixel", box((-0.68 + i * 0.272, 0.07, 1.4 + j * 0.22), (0.23, 0.03, 0.18)), slot, 0, False)
    for s in (1, -1):
        for k in range(4): P.obj("Bulb", ball((s * (0.88), 0.08, 1.3 + k * 0.21), (0.04, 0.04, 0.04), 6, 3), "Trim")
    # the gondola
    P.obj("Gondola", loft([(0.95, 0.06, 0.06, 0, -1.08), (0.8, 0.28, 0.2, 0, -1.12), (0.0, 0.34, 0.24, 0, -1.15), (-0.7, 0.26, 0.2, 0, -1.12), (-0.85, 0.05, 0.05, 0, -1.08)], 14),
          lambda c, n: "Lamp" if abs(n.x) > 0.6 and abs(c.z + 1.12) < 0.07 and (c.y * 5) % 1.0 > 0.35 else ("Glass" if c.y > 0.65 and n.z > -0.3 else "Accent"), 1)
    for s in (1, -1):
        P.obj("Strut", pipe([(s * 0.18, 0.4, -1.0), (s * 0.3, 0.4, -0.88)], [0.03, 0.03], 6), "Metal")
        P.obj("Strut", pipe([(s * 0.18, -0.4, -1.0), (s * 0.3, -0.4, -0.88)], [0.03, 0.03], 6), "Metal")
        P.obj("Arm", pipe([(s * 0.3, -0.35, -1.1), (s * 0.85, -0.35, -1.0)], [0.035, 0.035], 6), "Metal")
        P.obj("Nacelle", loft([(-0.05, 0.06, 0.06, s * 0.88, -1.0), (-0.15, 0.12, 0.12, s * 0.88, -1.0), (-0.55, 0.1, 0.1, s * 0.88, -1.0), (-0.7, 0.04, 0.04, s * 0.88, -1.0)], 10), "Base", 1)
        P.prop((s * 0.88, -0.75, -1.0), 0.38, 3, blade="Dark", tip="Accent", spinner="Trim", spinner_len=0.1)
    P.obj("Searchlight", lathe([(0.0, 0.0), (0.09, 0.02), (0.11, 0.12), (0.0, 0.13)], 10, "y", (0, 0.92, -1.2)), lambda c, n: "Lamp" if n.y > 0.6 else "Metal")
    P.part("Muzzle", ball((0, 1.06, -1.2), (0.07, 0.04, 0.07), 8, 4), "Lamp", (0, 1.06, -1.2))
    return P


# ================================================================= 2. the news chopper
def C_chopper():
    """A chunky news helicopter turned gunship: a red-and-white body with a yellow stripe, a big bubble canopy, a camera turret under its chin
    with a glowing lens, two mech arms ending in gatling guns, skids, a satellite dish turning on its back, a four-blade rotor and a tail rotor."""
    P = Boss("chopper", {"Base": ((0.86, 0.12, 0.10), 0.6), "Belly": ((0.95, 0.95, 0.96), 0.5), "Accent": ((0.10, 0.25, 0.65), 0.55), "Trim": TAXI,
                         "Glass": ((0.30, 0.65, 0.85), 0.92), "Dark": ((0.07, 0.07, 0.09), 0.5), "Glow": ((1.0, 0.25, 0.15), 0.5),
                         "Metal": STEEL, "Lamp": ((0.75, 0.95, 1.0), 0.8)})
    def livery(c, n):
        if n.z < -0.35: return "Belly"
        if abs(c.z - 0.02) < 0.07: return "Trim"
        return "Base"
    P.obj("Hull", loft([(1.15, 0.12, 0.1, 0, 0.0), (1.0, 0.42, 0.4, 0, 0.0), (0.55, 0.62, 0.55, 0, 0.05), (-0.1, 0.62, 0.55, 0, 0.08), (-0.6, 0.45, 0.42, 0, 0.12), (-0.9, 0.22, 0.24, 0, 0.18)], 18, sq=1.4), livery, 1)
    P.obj("Boom", pipe([(0, -0.8, 0.2), (0, -1.6, 0.26), (0, -2.35, 0.32)], [0.2, 0.13, 0.09], 10), livery, 1)
    P.obj("Canopy", ball((0, 0.62, 0.22), (0.5, 0.52, 0.42), 16, 8), lambda c, n: "Glass" if n.y > -0.2 and c.z > -0.02 else "Base", 1)
    P.obj("Frame", torus(0.5, 0.025, 0.0, 24, 5), "Dark"); P.parts[-1].data.transform(Matrix.Translation((0, 0.62, 0.22)) @ Matrix.Rotation(math.radians(90), 4, "Y"))
    # tail: fin, stabiliser
    P.obj("TailFin", hull([(0, -2.05, 0.3), (0, -2.45, 0.3), (0, -2.55, 0.85), (0, -2.35, 0.85), (0.03, -2.3, 0.5), (-0.03, -2.3, 0.5)]), "Base", 0, False)
    P.obj("Stab", box((0, -2.0, 0.3), (0.9, 0.18, 0.04)), lambda c, n: "Trim" if abs(c.x) > 0.36 else "Belly", 0, False)
    P.prop((0.12, -2.42, 0.6), 0.32, 3, axis="x", chord=0.08, blade="Belly", tip="Base", spinner="Metal", spinner_len=0.05, name="TailRotor")
    # the camera turret under the chin
    P.obj("Turret", ball((0, 0.98, -0.42), (0.22, 0.22, 0.2), 12, 6), "Dark", 1)
    P.obj("Lens", lathe([(0.0, 0.0), (0.12, 0.0), (0.13, 0.12), (0.1, 0.16), (0.0, 0.15)], 14, "y", (0, 1.1, -0.44)), lambda c, n: "Glow" if n.y > 0.7 else "Metal")
    # mech arms with gatlings
    for s in (1, -1):
        sh = Vector((s * 0.6, 0.15, -0.05)); el = Vector((s * 1.05, 0.25, -0.35)); hd = Vector((s * 0.95, 0.75, -0.4))
        P.obj("Shoulder", ball(tuple(sh), (0.17, 0.17, 0.17), 10, 5), "Dark")
        P.obj("Arm", pipe([sh, el], [0.1, 0.09], 8), "Metal")
        P.obj("Elbow", ball(tuple(el), (0.12, 0.12, 0.12), 10, 5), "Trim")
        P.obj("Fore", pipe([el, hd], [0.11, 0.12], 8), "Base", 1)
        P.obj("GunBody", lathe([(0.0, 0.0), (0.13, 0.0), (0.13, 0.25), (0.0, 0.25)], 12, "y", tuple(hd)), "Dark")
        for k in range(6):
            a = 2 * math.pi * k / 6
            o = Vector((math.cos(a) * 0.07, 0, math.sin(a) * 0.07))
            P.obj("Barrel", pipe([hd + o + Vector((0, 0.25, 0)), hd + o + Vector((0, 0.7, 0))], [0.025, 0.025], 6), "Metal")
        P.obj("GunRing", torus(0.1, 0.02, 0.0, 14, 4), "Trim"); P.parts[-1].data.transform(Matrix.Translation(hd + Vector((0, 0.62, 0))) @ Matrix.Rotation(math.radians(90), 4, "X"))
        # skids
        P.obj("Skid", pipe([(s * 0.48, 0.85, -0.58), (s * 0.5, 0.7, -0.68), (s * 0.5, -0.6, -0.68), (s * 0.48, -0.75, -0.6)], [0.035] * 4, 6), "Dark")
        for y in (0.4, -0.35): P.obj("SkidLeg", pipe([(s * 0.32, y, -0.38), (s * 0.5, y, -0.68)], [0.03, 0.03], 6), "Dark")
        P.obj("NavLight", ball((s * 0.62, 0.4, 0.05), (0.04, 0.04, 0.04), 6, 3), "Glow" if s > 0 else "Lamp")
    # the dish turning on its back, the mast and the rotor
    P.part("SpinDish", lathe([(0.0, 0.08), (0.2, 0.12), (0.28, 0.2), (0.26, 0.21), (0.0, 0.1)], 14, "z", (0, -0.55, 0.55)), "Belly", (0, -0.55, 0.55), 0, False)
    P.part("SpinDish", pipe([(0, -0.55, 0.55), (0.0, -0.55, 0.85)], [0.02, 0.01], 5), "Metal", (0, -0.55, 0.55))
    P.part("SpinDish", ball((0, -0.55, 0.86), (0.03, 0.03, 0.03), 6, 3), "Glow", (0, -0.55, 0.55))
    P.obj("DishBase", pipe([(0, -0.55, 0.4), (0, -0.55, 0.58)], [0.06, 0.05], 8), "Metal")
    P.obj("Mast", pipe([(0, 0.05, 0.55), (0, 0.05, 0.85)], [0.07, 0.06], 10), "Metal")
    P.obj("Cowl", ball((0, -0.05, 0.6), (0.3, 0.45, 0.18), 12, 6), "Base", 1)
    P.prop((0, 0.05, 0.88), 1.65, 4, axis="z", chord=0.16, blade="Dark", tip="Trim", spinner="Metal", spinner_len=0.08, name="Rotor")
    P.part("Muzzle", ball((0, 1.27, -0.44), (0.06, 0.03, 0.06), 8, 4), "Glow", (0, 1.27, -0.44))
    return P


# ================================================================= 3. the king pigeon
def C_pigeon():
    """The king of the rooftops: a giant plump city pigeon in blue-grey with a shimmering green-and-violet neck, orange eyes, a golden crown
    set with rubies, black bars across broad wings that beat, a fanned tail and coral feet tucked under it."""
    P = Boss("pigeon", {"Base": ((0.48, 0.52, 0.62), 0.4), "Belly": ((0.70, 0.73, 0.80), 0.35), "Accent": ((0.95, 0.45, 0.45), 0.4), "Trim": GOLD,
                        "Glass": ((0.20, 0.75, 0.50), 0.85), "Dark": ((0.12, 0.13, 0.17), 0.4), "Glow": ((1.0, 0.10, 0.20), 0.5),
                        "Metal": ((0.55, 0.30, 0.75), 0.8), "Lamp": ((1.0, 0.55, 0.10), 0.8)})
    P.obj("Body", ball((0, -0.05, 0.0), (0.78, 1.05, 0.7), 16, 8), lambda c, n: "Belly" if n.z < -0.3 or (n.y > 0.4 and c.z < 0.1) else "Base", 1)
    def neck(c, n):
        v = math.sin(c.x * 9 + c.z * 7) * 0.5 + 0.5
        return "Glass" if v > 0.45 else "Metal"
    P.obj("Neck", ball((0, 0.7, 0.4), (0.54, 0.5, 0.56), 14, 7), neck, 1)
    P.obj("Head", ball((0, 1.08, 0.9), (0.4, 0.42, 0.38), 14, 7), "Base", 1)
    P.obj("Beak", cone((0, 1.42, 0.84), (0, 1.8, 0.74), 0.08, 8), "Dark", 0, False)
    P.obj("Cere", ball((0, 1.46, 0.9), (0.08, 0.09, 0.06), 8, 4), "Belly")
    for s in (1, -1):
        P.obj("Eye", ball((s * 0.3, 1.24, 0.98), (0.07, 0.13, 0.13), 10, 5), "Lamp")
        P.obj("Pupil", ball((s * 0.355, 1.28, 0.99), (0.03, 0.06, 0.06), 8, 4), "Dark")
        P.obj("Brow", box((s * 0.27, 1.27, 1.13), (0.2, 0.08, 0.05), Matrix.Rotation(math.radians(-s * 22), 3, "Y")), "Dark", 0, False)
    # the crown
    P.obj("Crown", lathe([(0.22, 1.18), (0.25, 1.28), (0.26, 1.4), (0.23, 1.4), (0.2, 1.24)], 16, "z", (0, 1.04, 0)), "Trim")
    for k in range(6):
        a = 2 * math.pi * k / 6
        b = Vector((math.cos(a) * 0.25, 1.04 + math.sin(a) * 0.25, 1.38))
        P.obj("CrownSpike", cone(b, b + Vector((math.cos(a) * 0.05, math.sin(a) * 0.05, 0.2)), 0.05, 5), "Trim", 0, False)
        P.obj("CrownPearl", ball(tuple(b + Vector((math.cos(a) * 0.05, math.sin(a) * 0.05, 0.22))), (0.035, 0.035, 0.035), 6, 3), "Belly")
        P.obj("Ruby", ball((math.cos(a + 0.52) * 0.26, 1.04 + math.sin(a + 0.52) * 0.26, 1.31), (0.035, 0.035, 0.035), 6, 3), "Glow")
    # wings with the two black bars and dark tips
    for s in (1, -1):
        name = "FlapR" if s > 0 else "FlapL"
        hub = (s * 0.6, 0.15, 0.3)
        keys = [(0.5, 0.75, -0.75, 0.2, 0.3), (1.1, 0.8, -1.05, 0.14, 0.42), (1.7, 0.65, -1.1, 0.1, 0.5), (2.2, 0.35, -0.95, 0.06, 0.55), (2.45, 0.0, -0.6, 0.03, 0.55)]
        bm = sweep([(x, airfoil(le, te, th, z)) for (x, le, te, th, z) in fine(keys)], "x")
        if s < 0: bm = mirror_x(bm)
        def wp(c, n):
            if n.z < -0.3: return "Belly"
            if abs(c.x) > 1.95: return "Dark"
            if 0.7 < abs(c.x) < 1.7 and (abs(c.y + 0.3) < 0.09 or abs(c.y + 0.6) < 0.09): return "Dark"
            return "Base"
        P.part(name, bm, wp, hub, 0)
        for k in range(5):
            x0 = 1.95 + k * 0.1; y0 = 0.2 - k * 0.22
            P.part(name, cone((s * x0, y0, 0.53), (s * (x0 + 0.5), y0 - 0.15 - k * 0.08, 0.55), 0.09, 4), "Dark", hub, 0, False)
        P.obj("Foot", pipe([(s * 0.2, 0.1, -0.5), (s * 0.22, 0.2, -0.68)], [0.05, 0.04], 6), "Accent")
        for k in (-1, 0, 1): P.obj("Toe", cone((s * 0.22, 0.2, -0.68), (s * 0.22 + k * 0.08, 0.4, -0.72), 0.025, 4), "Accent", 0, False)
    # fanned tail
    hub = Vector((0, -0.95, 0.1))
    tips = [hub + Vector((math.sin(math.radians(a)) * 0.75, -math.cos(math.radians(a)) * 0.85, 0.05)) for a in range(-50, 51, 20)]
    P.obj("Tail", fan(hub, tips, 0.04, 0.05), lambda c, n: "Dark" if (c - hub).length > 0.62 else "Base", 0, False)
    P.part("Muzzle", ball((0, 1.82, 0.74), (0.05, 0.03, 0.04), 8, 4), "Glow", (0, 1.82, 0.74))
    return P


# ================================================================= 4. the traffic titan
def C_titan():
    """A robot built from the street: a yellow taxi for a chest with a checker belt, headlights and a roof sign, a traffic light for a head
    (red, amber and green eyes under their hoods), traffic cones for shoulders, a stop sign for a shield, a street-lamp cannon, and legs on
    rocket boots that swing."""
    P = Boss("titan", {"Base": TAXI, "Belly": ((0.95, 0.95, 0.95), 0.5), "Accent": ((0.85, 0.08, 0.08), 0.6), "Trim": ((1.0, 0.42, 0.06), 0.5),
                       "Glass": ((0.15, 0.95, 0.35), 0.9), "Dark": ((0.08, 0.09, 0.10), 0.5), "Glow": ((1.0, 0.12, 0.08), 0.5),
                       "Metal": STEEL, "Lamp": ((1.0, 0.78, 0.25), 0.8)})
    # the taxi chest
    def taxi(c, n):
        if abs(c.z - 0.0) < 0.09 and abs(n.z) < 0.5:
            return "Dark" if (int((c.x + c.y + 3) * 6) + int((c.z + 1) * 11)) % 2 else "Belly"
        return "Base"
    P.obj("Chest", hull([(sx * w, sy * d, z) for sx in (-1, 1) for sy in (-1, 1) for (w, d, z) in ((0.62, 0.42, -0.45), (0.72, 0.5, -0.1), (0.75, 0.5, 0.35), (0.62, 0.4, 0.62))]), taxi, 0, False)
    P.obj("Checker", box((0, 0.0, 0.0), (1.47, 1.0, 0.18)), lambda c, n: ("Dark" if (int((c.x + 3) * 7) + int((c.y + 3) * 7) + int((c.z + 3) * 11)) % 2 else "Belly") if abs(n.z) < 0.5 else "Base", 0, False)
    for i in range(10):
        for j in range(2):
            x = -0.66 + i * 0.147
            P.obj("Check", box((x, 0.505, -0.045 + j * 0.09), (0.147, 0.02, 0.09)), "Dark" if (i + j) % 2 else "Belly", 0, False)
    P.obj("Windshield", hull([(-0.55, 0.42, 0.28), (0.55, 0.42, 0.28), (-0.48, 0.36, 0.58), (0.48, 0.36, 0.58), (-0.55, 0.47, 0.28), (0.55, 0.47, 0.28), (-0.48, 0.41, 0.58), (0.48, 0.41, 0.58)]), "Glass", 0, False)
    for s in (1, -1):
        P.obj("Headlight", lathe([(0.0, 0.0), (0.11, 0.0), (0.12, 0.05), (0.0, 0.06)], 12, "y", (s * 0.48, 0.5, -0.28)), "Lamp")
    P.obj("Grille", box((0, 0.52, -0.28), (0.5, 0.03, 0.14)), lambda c, n: "Metal", 0, False)
    P.obj("Bumper", box((0, 0.53, -0.43), (1.3, 0.08, 0.06)), "Metal", 0, False)
    # the traffic-light head
    P.obj("NeckPole", pipe([(0, 0, 0.6), (0, 0, 0.82)], [0.08, 0.08], 8), "Metal")
    P.obj("Signal", box((0, 0.0, 1.32), (0.5, 0.36, 1.0)), "Trim", 0, False)
    P.obj("Visor", box((0, 0.17, 1.32), (0.44, 0.04, 0.94)), "Dark", 0, False)
    for k, slot in enumerate(("Glow", "Lamp", "Glass")):
        z = 1.66 - k * 0.32
        P.obj("Light", ball((0, 0.2, z), (0.13, 0.06, 0.13), 14, 7), slot)
        P.obj("Hood", sheet([[(-0.17, 0.2, z + 0.15), (0.17, 0.2, z + 0.15), (0.15, 0.36, z + 0.1), (-0.15, 0.36, z + 0.1)]], 0.03), "Dark", 0, False)
    P.obj("SignalCap", box((0, 0.0, 1.85), (0.56, 0.42, 0.06)), "Dark", 0, False)
    P.obj("RoofSign", box((0, -0.15, 0.7), (0.4, 0.14, 0.14)), "Lamp", 0, False)
    # cone shoulders, arms
    for s in (1, -1):
        sh = Vector((s * 0.88, 0.0, 0.42))
        P.obj("ConeBase", box(tuple(sh + Vector((0, 0, -0.06))), (0.42, 0.42, 0.06)), "Trim", 0, False)
        tip = sh + Vector((s * 0.25, 0, 0.6))
        P.obj("Cone", pipe([sh + (tip - sh) * t for t in (0.0, 0.3, 0.42, 0.55, 0.62, 1.0)], [0.22, 0.16, 0.14, 0.12, 0.1, 0.0], 12),
              lambda c, n, sh=sh, tip=tip: "Belly" if 0.3 < (c - sh).dot((tip - sh).normalized()) / (tip - sh).length < 0.5 else "Trim", 0, False)
        el = Vector((s * 1.05, 0.25, -0.05)); hd = Vector((s * 1.0, 0.75, -0.08))
        P.obj("UpperArm", pipe([sh + Vector((0, 0, -0.08)), el], [0.11, 0.1], 8), "Metal")
        P.obj("Elbow", ball(tuple(el), (0.13, 0.13, 0.13), 10, 5), "Dark")
        P.obj("Fore", pipe([el, hd], [0.12, 0.13], 8), "Base", 1)
        if s < 0:   # the stop sign shield
            sc = hd + Vector((-0.1, 0.2, 0.1))
            oct8 = lambda r, y: [(sc.x + math.cos(math.pi / 8 + k * math.pi / 4) * r, sc.y + y, sc.z + math.sin(math.pi / 8 + k * math.pi / 4) * r) for k in range(8)]
            P.obj("StopRim", hull(oct8(0.5, 0.0) + oct8(0.5, 0.04)), "Belly", 0, False)
            P.obj("Stop", hull(oct8(0.44, 0.04) + oct8(0.44, 0.07)), "Accent", 0, False)
            P.obj("StopBar", box((sc.x, sc.y + 0.08, sc.z), (0.6, 0.02, 0.1)), "Belly", 0, False)
            P.obj("Grip", pipe([hd, sc], [0.06, 0.06], 6), "Metal")
        else:       # the street-lamp cannon
            P.obj("Cannon", pipe([hd, hd + Vector((0, 0.65, 0))], [0.14, 0.11], 12), "Metal")
            P.obj("LampHead", lathe([(0.0, 0.0), (0.2, 0.05), (0.22, 0.2), (0.12, 0.28), (0.0, 0.28)], 12, "y", tuple(hd + Vector((0, 0.6, 0)))),
                  lambda c, n: "Lamp" if n.y > 0.5 else "Dark")
            for k in range(3): P.obj("Band", torus(0.15, 0.025, 0.0, 14, 4), "Trim"); P.parts[-1].data.transform(Matrix.Translation(hd + Vector((0, 0.15 + k * 0.15, 0))) @ Matrix.Rotation(math.radians(90), 4, "X"))
    # legs on rocket boots
    for s in (1, -1):
        name = "SwayR" if s > 0 else "SwayL"
        hip = Vector((s * 0.35, 0.0, -0.45)); kn = hip + Vector((s * 0.05, 0.1, -0.45)); ft = kn + Vector((0, -0.05, -0.45))
        P.part(name, pipe([hip, kn], [0.13, 0.12], 8), "Metal", tuple(hip))
        P.part(name, ball(tuple(kn), (0.14, 0.14, 0.14), 10, 5), "Dark", tuple(hip))
        P.part(name, pipe([kn, ft], [0.14, 0.17], 8), "Base", tuple(hip), 1)
        P.part(name, at(torus(0.17, 0.07, 0.0, 16, 6), ft), "Dark", tuple(hip))
        P.part(name, lathe([(0.12, 0.0), (0.08, -0.14), (0.0, -0.14)], 10, "z", tuple(ft + Vector((0, 0, -0.05)))), "Metal", tuple(hip))
        P.part(name, cone(ft + Vector((0, 0, -0.18)), ft + Vector((0, -0.05, -0.62)), 0.1, 8), "Glow", tuple(hip), 0, False)
    P.part("Muzzle", ball((1.0, 1.42, -0.08), (0.08, 0.04, 0.08), 8, 4), "Lamp", (1.0, 1.42, -0.08))
    return P


# ================================================================= 5. the skyscraper fortress
def C_tower():
    """The last boss: the crown of a skyscraper torn loose and flying - an art-deco tower stepping up in three tiers of lit windows, a great
    clock on its face, a golden sunburst crown and a spire with a beacon, antennas blinking red, cannon turrets on its terraces, a broken
    concrete root with four thrusters under it, and a ring of drones turning round it."""
    P = Boss("tower", {"Base": ((0.20, 0.24, 0.34), 0.7), "Belly": ((0.92, 0.90, 0.84), 0.4), "Accent": ((0.62, 0.60, 0.58), 0.3), "Trim": GOLD,
                       "Glass": ((0.35, 0.55, 0.80), 0.9), "Dark": ((0.06, 0.07, 0.09), 0.5), "Glow": ((1.0, 0.15, 0.1), 0.5),
                       "Metal": STEEL, "Lamp": ((1.0, 0.85, 0.50), 0.8)})
    rng = random.Random(4)
    tiers = [(-0.2, 0.75, 1.0), (0.75, 1.45, 0.78), (1.45, 2.05, 0.58)]   # z0, z1, half width
    for (z0, z1, w) in tiers:
        P.obj("Tier", box((0, 0, (z0 + z1) / 2), (w * 2, w * 2, z1 - z0)), "Base", 0, False)
        P.obj("Ledge", box((0, 0, z1 + 0.03), (w * 2 + 0.12, w * 2 + 0.12, 0.06)), "Trim", 0, False)
        cols = max(3, int(w * 2 / 0.3)); rows = max(2, int((z1 - z0 - 0.15) / 0.24))
        for side in range(4):
            R = Matrix.Rotation(math.radians(90 * side), 3, "Z")
            for i in range(cols):
                for j in range(rows):
                    x = -w + (i + 0.5) * (2 * w / cols); z = z0 + 0.1 + (j + 0.5) * ((z1 - z0 - 0.15) / rows)
                    if side == 0 and z0 > 0.5 and z0 < 1.0 and abs(x) < 0.45 and z > 0.85: continue   # the clock
                    lit = rng.random() < 0.5
                    b = box((x, w + 0.012, z), (2 * w / cols * 0.62, 0.03, 0.15))
                    P.obj("Window", xf(b, R), "Lamp" if lit else "Glass", 0, False)
            for i in range(cols + 1):   # vertical piers
                x = -w + i * (2 * w / cols)
                P.obj("Pier", xf(box((x, w + 0.02, (z0 + z1) / 2), (0.04, 0.04, z1 - z0)), R), "Accent", 0, False)
    # the great clock on the middle tier
    cz = 1.12
    P.obj("ClockRim", lathe([(0.0, 0.0), (0.36, 0.0), (0.36, 0.06), (0.0, 0.06)], 24, "y", (0, 0.78, cz)), "Trim")
    P.obj("ClockFace", lathe([(0.0, 0.0), (0.31, 0.0), (0.0, 0.002)], 24, "y", (0, 0.845, cz)), "Belly")
    for k in range(12):
        a = 2 * math.pi * k / 12
        P.obj("Tick", box((math.sin(a) * 0.25, 0.85, cz + math.cos(a) * 0.25), (0.03, 0.02, 0.06), Matrix.Rotation(-a, 3, "Y")), "Dark", 0, False)
    P.obj("HandH", box((0.07, 0.86, cz + 0.05), (0.03, 0.02, 0.16), Matrix.Rotation(math.radians(-55), 3, "Y")), "Dark", 0, False)
    P.obj("HandM", box((-0.02, 0.86, cz + 0.11), (0.02, 0.02, 0.24), Matrix.Rotation(math.radians(10), 3, "Y")), "Dark", 0, False)
    # the art-deco crown: stacked sunburst arches and the spire
    for k in range(4):
        z = 2.1 + k * 0.2; r = 0.5 - k * 0.1
        P.obj("CrownStep", lathe([(r, z), (r, z + 0.12), (r * 0.7, z + 0.2), (0.0, z + 0.2)], 8, "z"), lambda c, n: "Trim" if n.z < 0.6 else "Base", 0, False)
        for a in range(8):
            ax = 2 * math.pi * (a + 0.5) / 8
            P.obj("Sunray", ball((math.cos(ax) * r * 0.93, math.sin(ax) * r * 0.93, z + 0.1), (0.05, 0.05, 0.09), 6, 3), "Lamp")
    P.obj("Spire", pipe([(0, 0, 2.85), (0, 0, 3.8)], [0.07, 0.0], 8), "Metal")
    P.obj("Beacon", ball((0, 0, 3.25), (0.08, 0.08, 0.08), 8, 4), "Glow")
    for sx in (-1, 1):
        for sy in (-1, 1):
            b = Vector((sx * 0.52, sy * 0.52, 2.05))
            P.obj("Antenna", pipe([b, b + Vector((0, 0, 0.55))], [0.025, 0.012], 5), "Metal")
            P.obj("Blink", ball(tuple(b + Vector((0, 0, 0.57))), (0.04, 0.04, 0.04), 6, 3), "Glow")
            # cannon turrets on the lower terrace corners
            t = Vector((sx * 0.86, sy * 0.86, 0.85))
            P.obj("Turret", ball(tuple(t), (0.14, 0.14, 0.1), 10, 5), "Dark")
            P.obj("Gun", pipe([t + Vector((0, 0.05, 0.02)), t + Vector((0, 0.45, 0.04))], [0.04, 0.035], 6), "Metal")
    # the broken concrete root and the thrusters
    root = []
    for k in range(30):
        a = rng.uniform(0, 2 * math.pi); r = rng.uniform(0.1, 1.0)
        root.append((math.cos(a) * r * 0.98, math.sin(a) * r * 0.98, -0.2 - (1.0 - r) * rng.uniform(0.5, 0.9)))
    root += [(sx * 0.98, sy * 0.98, -0.18) for sx in (-1, 1) for sy in (-1, 1)] + [(0, 0, -1.05)]
    P.obj("Root", hull(root), "Accent", 0, False)
    for k in range(10):
        a = rng.uniform(0, 2 * math.pi); r = rng.uniform(0.3, 0.8)
        b = Vector((math.cos(a) * r, math.sin(a) * r, -0.35))
        P.obj("Rebar", pipe([b, b + Vector((rng.uniform(-0.15, 0.15), rng.uniform(-0.15, 0.15), -0.45))], [0.015, 0.015], 4), "Dark")
    for sx in (-1, 1):
        for sy in (-1, 1):
            c = (sx * 0.65, sy * 0.65, -0.3)
            P.obj("Thruster", lathe([(0.0, 0.05), (0.18, 0.05), (0.2, -0.15), (0.16, -0.3), (0.0, -0.3)], 12, "z", c), "Metal")
            P.obj("Flame", cone((c[0], c[1], -0.32), (c[0], c[1], -0.85), 0.13, 8), "Lamp", 0, False)
    # the ring of drones
    for k in range(8):
        a = 2 * math.pi * k / 8
        d = Vector((math.cos(a) * 2.25, math.sin(a) * 2.25, 1.0 + 0.25 * math.sin(a * 2)))
        P.part("SpinDrones", box(tuple(d), (0.22, 0.22, 0.08)), "Dark", (0, 0, 1.0), 0, False)
        P.part("SpinDrones", ball(tuple(d + Vector((0, 0, -0.06))), (0.06, 0.06, 0.05), 6, 3), "Glow", (0, 0, 1.0))
        for sx in (-1, 1):
            for sy in (-1, 1):
                P.part("SpinDrones", lathe([(0.0, 0.0), (0.09, 0.0), (0.09, 0.015), (0.0, 0.015)], 8, "z", tuple(d + Vector((sx * 0.15, sy * 0.15, 0.05)))), "Metal", (0, 0, 1.0), 0, False)
    P.part("Muzzle", ball((0, 1.02, 0.35), (0.08, 0.04, 0.08), 8, 4), "Lamp", (0, 1.02, 0.35))
    return P


BOSSES = [("blimp", C_blimp), ("chopper", C_chopper), ("pigeon", C_pigeon), ("titan", C_titan), ("tower", C_tower)]

if __name__ == "__main__":
    os.makedirs(AB.OUT, exist_ok=True)
    for bid, fn in BOSSES:
        if ONLY and bid not in ONLY: continue
        fn().finish()
    print("DONE")
