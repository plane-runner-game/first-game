# Sky Squad, the lava world's (INFERNO) five bosses (2026-10-10: "now for the lava, inferno" - five beautiful ones that suit the world, and
# the world ends after the fifth, as the sea). Built from code like the alien and sea bosses (alien_bosses.py lends its Boss class and
# shapes): the magma phoenix, the ember scarab, the inferno golem, the fire ifrit and the volcano fortress.
# Run: blender -b -P Tools/blender/lava_bosses.py -- <out dir> [export] [ids,comma,separated]
# Conventions as alien_bosses.py / sea_bosses.py: +Y nose, +Z up, +X right; "Flap*" rock about the nose axis, "Sway*" about the wing axis,
# "Spin*" turn slowly about up, "Cloth" stays still without the outline, "Muzzle" is where his shots leave from.
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

def rock(c, r, rng, n=14, squash=(1, 1, 1)):
    """a lumpy convex rock about c."""
    pts = []
    for _ in range(n):
        d = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1)))
        if d.length < 1e-3: continue
        d.normalize(); k = r * rng.uniform(0.75, 1.0)
        pts.append(Vector(c) + Vector((d.x * k * squash[0], d.y * k * squash[1], d.z * k * squash[2])))
    return hull([tuple(p) for p in pts])

def fine(keys, step=0.08):
    """wing sections interpolated every 'step' so painted bands come out as thin stripes."""
    secs = []
    for a0, a1 in zip(keys, keys[1:]):
        n = max(2, int((a1[0] - a0[0]) / step))
        secs += [tuple(u + (v - u) * i / n for u, v in zip(a0, a1)) for i in range(n)]
    secs.append(keys[-1])
    return secs

def cracks(c, n):
    """glowing lava cracks over dark rock: a few thin wavy bands."""
    w = math.sin(c.x * 7.0 + math.sin(c.y * 5.0) * 1.5) * math.sin(c.y * 6.0 + c.z * 4.0)
    return abs(w) < 0.06


# ================================================================= 1. the magma phoenix
def L_phoenix():
    """A fire bird: a crimson body, an orange breast, a golden beak, a crest of flame plumes, long tail plumes trailing fire, and broad wings
    that run from crimson through orange to gold with a burning trailing edge."""
    P = Boss("phoenix", {"Base": ((0.82, 0.12, 0.05), 0.45), "Belly": ((1.0, 0.48, 0.08), 0.45), "Accent": ((1.0, 0.78, 0.18), 0.6),
                         "Trim": ((0.30, 0.06, 0.03), 0.4), "Glass": ((1.0, 0.85, 0.4), 0.9), "Dark": ((0.06, 0.03, 0.02), 0.5),
                         "Glow": ((1.0, 0.55, 0.08), 0.5), "Metal": ((0.6, 0.5, 0.4), 0.6), "Lamp": ((1.0, 0.95, 0.55), 0.8)})
    P.obj("Body", loft([(1.4, 0.18, 0.2, 0, 0.42), (1.1, 0.3, 0.33, 0, 0.28), (0.5, 0.45, 0.45, 0, 0.08), (-0.3, 0.42, 0.4, 0, 0.02),
                        (-0.95, 0.24, 0.22, 0, 0.05), (-1.25, 0.1, 0.08, 0, 0.08)], 16), lambda c, n: "Belly" if n.z < -0.2 or n.y > 0.5 else "Base", 1)
    P.obj("Head", ball((0, 1.5, 0.52), (0.26, 0.32, 0.27), 14, 7), "Base")
    P.obj("Beak", pipe(bez((0, 1.74, 0.5), (0, 2.05, 0.5), (0, 2.2, 0.42), (0, 2.24, 0.3), 6), [0.1, 0.085, 0.065, 0.045, 0.03, 0.015, 0.0], 10), "Accent")
    for s in (1, -1):
        P.obj("Eye", ball((s * 0.18, 1.68, 0.6), (0.045, 0.06, 0.045), 8, 4), "Lamp")
        P.obj("Mask", box((s * 0.16, 1.66, 0.64), (0.14, 0.16, 0.04), Matrix.Rotation(math.radians(s * 20), 3, "Y")), "Accent", 0, False)
    for k in range(7):   # the crest of flame plumes
        a = math.radians(-45 + k * 15)
        base = Vector((math.sin(a) * 0.12, 1.42, 0.72))
        tip = base + Vector((math.sin(a) * 0.35, -0.45 - 0.1 * (3 - abs(k - 3)), 0.55 + 0.1 * (3 - abs(k - 3))))
        P.obj("Crest", pipe(bez(base, base + Vector((0, -0.05, 0.25)), tip + Vector((0, 0.15, -0.1)), tip, 5), [0.06, 0.055, 0.045, 0.03, 0.015, 0.0], 6),
              lambda c, n, b=base: "Glow" if (c - b).length > 0.45 else "Belly")
    for k in range(5):   # the tail plumes, trailing fire
        a = math.radians(-30 + k * 15)
        p0 = Vector((0, -1.15, 0.08))
        tip = p0 + Vector((math.sin(a) * 1.0, -1.6 - 0.2 * (2 - abs(k - 2)), 0.35 - 0.1 * abs(k - 2)))
        pts = bez(p0, p0 + Vector((math.sin(a) * 0.2, -0.5, -0.05)), tip + Vector((-math.sin(a) * 0.2, 0.5, -0.2)), tip, 8)
        P.obj("Plume", pipe(pts, [0.07, 0.07, 0.065, 0.06, 0.05, 0.04, 0.035, 0.03, 0.0], 6), lambda c, n, p0=p0: "Glow" if (c - p0).length > 1.2 else "Base")
        P.obj("PlumeEye", ball(tuple(pts[6]), (0.09, 0.12, 0.05), 8, 4), "Accent")
    for s in (1, -1):
        for k in (-1, 0, 1):
            P.obj("Talon", pipe(bez((s * 0.2, 0.0, -0.3), (s * (0.22 + k * 0.05), 0.15, -0.55), (s * (0.24 + k * 0.08), 0.32, -0.56), (s * (0.24 + k * 0.08), 0.42, -0.46), 4), [0.035, 0.03, 0.025, 0.015, 0.0], 6), "Accent")
        name = "FlapR" if s > 0 else "FlapL"
        hub = (s * 0.4, 0.45, 0.25)
        keys = [(0.38, 0.95, -0.55, 0.16, 0.25), (1.2, 0.9, -0.85, 0.1, 0.45), (2.0, 0.7, -0.9, 0.07, 0.68), (2.7, 0.4, -0.75, 0.04, 0.85), (3.1, 0.05, -0.45, 0.02, 0.95)]
        bm = sweep([(x, airfoil(le, te, th, z)) for (x, le, te, th, z) in fine(keys)], "x")
        if s < 0: bm = mirror_x(bm)
        def feather(c, n):
            x = abs(c.x)
            if n.z < -0.3: return "Belly" if x < 1.8 else "Accent"
            if c.y < -0.55 - x * 0.08 or (x > 2.6 and c.y < 0.0): return "Glow"   # the burning trailing edge
            if x > 2.1: return "Accent"
            if x > 1.2: return "Belly"
            return "Base"
        P.part(name, bm, feather, hub, 0)
        for k in range(6):   # flame feathers off the trailing edge
            x0 = 1.0 + k * 0.38; y0 = -0.75 - x0 * 0.06 + (0.25 if x0 > 2.6 else 0.0)
            P.part(name, cone((s * x0, y0, 0.3 + x0 * 0.2), (s * (x0 + 0.1), y0 - 0.45, 0.28 + x0 * 0.2), 0.08, 4), "Glow", hub, 0, False)
    P.part("Muzzle", ball((0, 2.24, 0.32), (0.08, 0.05, 0.07), 8, 4), "Glow", (0, 2.24, 0.32))
    return P


# ================================================================= 2. the ember scarab
def L_scarab():
    """A giant beetle: an obsidian shell split by glowing lava cracks, a golden rhino horn and mandibles, six bronze legs, amber eyes - and
    two amber wings out from under the shell that buzz."""
    P = Boss("scarab", {"Base": ((0.08, 0.06, 0.07), 0.75), "Belly": ((0.32, 0.07, 0.04), 0.5), "Accent": ((0.96, 0.66, 0.16), 0.75),
                        "Trim": ((0.48, 0.30, 0.15), 0.6), "Glass": ((1.0, 0.58, 0.18), 0.9), "Dark": ((0.03, 0.02, 0.02), 0.5),
                        "Glow": ((1.0, 0.40, 0.05), 0.5), "Metal": ((0.45, 0.4, 0.35), 0.6), "Lamp": ((1.0, 0.90, 0.40), 0.8)})
    P.obj("Thorax", ball((0, 0.7, 0.05), (0.62, 0.45, 0.38), 18, 9), lambda c, n: "Belly" if n.z < -0.4 else ("Glow" if cracks(c, n) else "Base"), 1)
    P.obj("Head", ball((0, 1.2, -0.02), (0.38, 0.3, 0.26), 14, 7), lambda c, n: "Belly" if n.z < -0.4 else "Base", 1)
    P.obj("Horn", pipe(bez((0, 1.3, 0.12), (0, 1.65, 0.3), (0, 1.85, 0.65), (0, 1.75, 0.95), 7), [0.16, 0.14, 0.12, 0.1, 0.075, 0.05, 0.03, 0.0], 10), "Accent")
    P.obj("HornSpur", cone((0, 1.0, 0.3), (0, 1.15, 0.62), 0.08, 8), "Accent", 0, False)
    for s in (1, -1):
        P.obj("Eye", ball((s * 0.26, 1.33, 0.05), (0.07, 0.07, 0.06), 8, 4), "Lamp")
        P.obj("Mandible", pipe(bez((s * 0.18, 1.4, -0.12), (s * 0.35, 1.65, -0.15), (s * 0.25, 1.85, -0.15), (s * 0.06, 1.9, -0.12), 5), [0.06, 0.055, 0.045, 0.03, 0.015, 0.0], 8), "Accent")
        P.obj("Antenna", pipe(bez((s * 0.15, 1.42, 0.1), (s * 0.4, 1.7, 0.25), (s * 0.55, 1.75, 0.35), (s * 0.62, 1.7, 0.42), 4), [0.02, 0.018, 0.015, 0.012, 0.01], 5), "Trim")
        for k, y in enumerate((0.95, 0.6, 0.2)):   # six legs, bent
            hip = Vector((s * 0.45, y, -0.18)); knee = Vector((s * (0.95 + 0.05 * k), y + 0.15 - 0.15 * k, 0.05)); foot = Vector((s * (1.15 + 0.08 * k), y + 0.25 - 0.35 * k, -0.45))
            P.obj("Leg", pipe([hip, knee, foot], [0.07, 0.055, 0.03], 8), "Trim")
            P.obj("Claw", cone(foot, foot + Vector((s * 0.06, 0.1, -0.12)), 0.025, 5), "Accent", 0, False)
        # the elytra: the two halves of the shell, a little open, cracked with lava
        el = ball((0, 0, 0), (0.5, 1.1, 0.42), 16, 8)
        for v in el.verts:
            if v.co.z < -0.05: v.co.z = -0.05
        xf(el, Matrix.Rotation(math.radians(s * 8), 3, "Y"), (s * 0.36, -0.35, 0.22))
        P.obj("Elytron", el, lambda c, n: "Belly" if n.z < -0.6 else ("Glow" if cracks(c, n) else ("Accent" if abs(c.x) < 0.06 else "Base")), 1)
        # the wing out from under it, buzzing
        name = "FlapR" if s > 0 else "FlapL"
        hub = Vector((s * 0.35, 0.25, 0.45))
        tips = [hub + Vector((s * 1.3, 0.35, 0.55)), hub + Vector((s * 2.0, -0.3, 0.5)), hub + Vector((s * 1.7, -1.0, 0.3)), hub + Vector((s * 0.6, -1.25, 0.1))]
        polys = []
        for a, b in zip(tips, tips[1:]):
            mid = (a + b) * 0.5 + (hub - (a + b) * 0.5) * 0.08
            polys.append([hub, a, mid]); polys.append([hub, mid, b])
        P.part(name, sheet([[tuple(p) for p in poly] for poly in polys], 0.02), "Glass", tuple(hub), 0, False)
        for t in tips: P.part(name, pipe([hub, t], [0.025, 0.008], 5), "Trim", tuple(hub))
    P.obj("Abdomen", ball((0, -0.5, -0.12), (0.55, 0.95, 0.3), 16, 8), lambda c, n: "Glow" if n.z < -0.5 and (c.y * 6) % 1.0 < 0.25 else "Belly", 1)
    P.part("Muzzle", ball((0, 1.76, 0.98), (0.08, 0.07, 0.08), 8, 4), "Glow", (0, 1.76, 0.98))
    return P


# ================================================================= 3. the inferno golem
def L_golem():
    """A giant of molten rock: basalt boulders for a body, lava glowing in every crack, a burning heart in his chest, horns and blazing eyes,
    great fists of stone, a tail of fire beneath him and a ring of rocks circling him."""
    P = Boss("golem", {"Base": ((0.14, 0.11, 0.10), 0.3), "Belly": ((0.24, 0.17, 0.14), 0.3), "Accent": ((0.55, 0.12, 0.04), 0.4),
                       "Trim": ((0.36, 0.30, 0.27), 0.3), "Glass": ((1.0, 0.75, 0.3), 0.9), "Dark": ((0.04, 0.03, 0.03), 0.4),
                       "Glow": ((1.0, 0.42, 0.05), 0.5), "Metal": ((0.4, 0.38, 0.36), 0.5), "Lamp": ((1.0, 0.90, 0.40), 0.8)})
    rng = random.Random(7)
    lava = lambda c, n: "Glow" if cracks(c, n) or speckle(c, 1.3) < 0.025 else ("Trim" if n.z > 0.6 else "Base")
    P.obj("Chest", rock((0, 0.2, 0.55), 0.85, rng, 26, (1.25, 0.8, 0.9)), lava, 1)
    P.obj("Belly", rock((0, 0.1, -0.2), 0.6, rng, 20, (1.1, 0.8, 0.8)), lava, 1)
    P.obj("Heart", ball((0, 0.85, 0.5), (0.26, 0.12, 0.26), 12, 6), "Glow")
    P.obj("HeartRim", torus(0.3, 0.05, 0.0, 16, 6), "Accent")
    P.parts[-1].data.transform(Matrix.Translation((0, 0.82, 0.5)) @ Matrix.Rotation(math.radians(90), 4, "X"))
    P.obj("Head", rock((0, 0.45, 1.45), 0.36, rng, 18, (1.0, 0.9, 0.85)), lava, 1)
    for s in (1, -1):
        P.obj("Eye", ball((s * 0.13, 0.75, 1.5), (0.07, 0.04, 0.04), 8, 4), "Lamp")
        P.obj("Horn", pipe(bez((s * 0.22, 0.45, 1.6), (s * 0.5, 0.4, 1.8), (s * 0.62, 0.55, 2.05), (s * 0.55, 0.75, 2.2), 6), [0.1, 0.09, 0.075, 0.06, 0.04, 0.02, 0.0], 8), "Trim")
        P.obj("Shoulder", rock((s * 1.05, 0.2, 0.9), 0.48, rng, 18), lava, 1)
        P.obj("Arm", rock((s * 1.35, 0.35, 0.35), 0.36, rng, 16, (0.9, 0.9, 1.3)), lava, 1)
        P.obj("Fist", rock((s * 1.45, 0.75, -0.15), 0.5, rng, 20), lava, 1)
        P.obj("FistGlow", ball((s * 1.45, 1.15, -0.15), (0.16, 0.08, 0.16), 8, 4), "Glow")
    P.obj("Mouth", box((0, 0.78, 1.32), (0.2, 0.04, 0.05)), "Glow", 0, False)
    P.obj("FireTail", pipe(bez((0, 0.0, -0.55), (0, -0.2, -1.0), (0, -0.6, -1.3), (0, -1.0, -1.45), 6), [0.42, 0.36, 0.28, 0.2, 0.13, 0.06, 0.0], 12),
          lambda c, n: "Glow" if c.z < -0.9 else "Accent")
    for k in range(8):   # the ring of rocks circling him
        a = 2 * math.pi * k / 8
        P.part("SpinRocks", rock((math.sin(a) * 2.0, math.cos(a) * 1.7, 0.4 + 0.25 * math.sin(a * 3)), 0.17 + 0.05 * (k % 3), rng, 10), lava, (0, 0.2, 0.4), 0, False)
    P.part("Muzzle", ball((0, 0.98, 0.5), (0.1, 0.05, 0.1), 8, 4), "Lamp", (0, 0.98, 0.5))
    return P


# ================================================================= 4. the fire ifrit
def L_ifrit():
    """A fire genie: a crimson torso, curving black horns, a mane of flame, gold bracers, collar and earrings, a fireball in each hand, a
    tail of fire swirling below him and a ring of flame turning round his waist."""
    P = Boss("ifrit", {"Base": ((0.78, 0.14, 0.08), 0.45), "Belly": ((0.95, 0.35, 0.14), 0.45), "Accent": ((0.98, 0.74, 0.20), 0.75),
                       "Trim": ((0.10, 0.07, 0.07), 0.6), "Glass": ((1.0, 0.85, 0.4), 0.9), "Dark": ((0.05, 0.03, 0.03), 0.5),
                       "Glow": ((1.0, 0.50, 0.06), 0.5), "Metal": ((0.5, 0.45, 0.4), 0.6), "Lamp": ((1.0, 0.95, 0.55), 0.8)})
    P.obj("Torso", lathe([(0.0, -0.3), (0.42, -0.25), (0.5, 0.2), (0.68, 0.65), (0.6, 0.9), (0.3, 1.02), (0.0, 1.05)], 18, "z", (0, 0, 0)),
          lambda c, n: "Belly" if n.y > 0.55 and 0.1 < c.z < 0.75 else "Base", 1)
    for v in P.parts[-1].data.vertices: v.co.y *= 0.72
    P.obj("Collar", torus(0.33, 0.06, 0.0, 18, 6), "Accent"); P.parts[-1].data.transform(Matrix.Translation((0, 0, 1.0)))
    P.obj("Head", ball((0, 0.06, 1.32), (0.27, 0.27, 0.33), 14, 7), "Base", 1)
    P.obj("Jaw", ball((0, 0.17, 1.17), (0.18, 0.14, 0.11), 10, 5), "Base")
    P.obj("Beard", cone((0, 0.2, 1.1), (0, 0.25, 0.82), 0.1, 6), "Glow", 0, False)
    for s in (1, -1):
        P.obj("Eye", ball((s * 0.1, 0.28, 1.38), (0.06, 0.03, 0.03), 8, 4), "Lamp")
        P.obj("Brow", box((s * 0.1, 0.27, 1.43), (0.12, 0.04, 0.03), Matrix.Rotation(math.radians(-s * 20), 3, "Y")), "Trim", 0, False)
        P.obj("Horn", pipe(bez((s * 0.18, 0.0, 1.5), (s * 0.45, -0.05, 1.6), (s * 0.55, 0.1, 1.9), (s * 0.4, 0.25, 2.1), 6), [0.08, 0.07, 0.06, 0.045, 0.03, 0.015, 0.0], 8), "Trim")
        P.obj("Earring", torus(0.06, 0.015, 0.0, 10, 4), "Accent"); P.parts[-1].data.transform(Matrix.Translation((s * 0.28, 0.02, 1.2)) @ Matrix.Rotation(math.radians(90), 4, "Y"))
        P.obj("Ear", cone((s * 0.25, 0.02, 1.33), (s * 0.4, -0.05, 1.42), 0.05, 5), "Base", 0, False)
        sh = Vector((s * 0.62, 0.0, 0.85)); el = Vector((s * 1.15, 0.15, 0.6)); hd = Vector((s * 1.45, 0.45, 0.75))
        P.obj("UpperArm", pipe([sh, el], [0.2, 0.15], 10), "Base", 1)
        P.obj("Forearm", pipe([el, hd], [0.15, 0.12], 10), "Base", 1)
        P.obj("Bracer", pipe([el + (hd - el) * 0.35, el + (hd - el) * 0.75], [0.16, 0.14], 10), "Accent")
        P.obj("Hand", ball(tuple(hd), (0.13, 0.13, 0.12), 10, 5), "Base")
        P.obj("Fireball", ball(tuple(hd + Vector((0, 0.15, 0.25))), (0.24, 0.24, 0.24), 12, 6), "Glow")
        P.obj("FireCore", ball(tuple(hd + Vector((0, 0.15, 0.25))), (0.14, 0.26, 0.14), 8, 4), "Lamp")
        P.obj("Pauldron", ball(tuple(sh + Vector((0, 0, 0.08))), (0.24, 0.24, 0.16), 12, 6), "Accent")
    for k in range(9):   # the mane of flame
        a = math.radians(-80 + k * 20)
        base = Vector((math.sin(a) * 0.2, -0.12 - abs(math.cos(a)) * 0.05, 1.5))
        P.obj("Flame", cone(base, base + Vector((math.sin(a) * 0.3, -0.35, 0.35 + 0.15 * math.cos(a))), 0.09, 5), "Glow", 0, False)
    sp = [Vector((math.sin(t * 2.4) * 0.35 * (1 - t), -0.15 + math.cos(t * 2.4) * 0.25 * (1 - t), -0.25 - t * 1.4)) for t in [i / 10 for i in range(11)]]
    P.obj("Tail", pipe(sp, [0.42 * (1 - i / 10) + 0.02 for i in range(11)], 12), lambda c, n: "Glow" if c.z < -0.9 or speckle(c, 2.0) < 0.15 else "Belly", 1)
    P.obj("Sash", torus(0.46, 0.07, 0.0, 22, 6), "Accent"); P.parts[-1].data.transform(Matrix.Translation((0, 0, -0.22)))
    for k in range(10):   # the ring of flame round his waist
        a = 2 * math.pi * k / 10
        c = Vector((math.sin(a) * 1.15, math.cos(a) * 0.95, -0.15))
        P.part("SpinFlames", cone(c, c + Vector((0, 0, 0.42)), 0.11, 5), "Glow", (0, 0, -0.15), 0, False)
        P.part("SpinFlames", ball(tuple(c), (0.1, 0.1, 0.06), 6, 3), "Lamp", (0, 0, -0.15))
    P.part("Muzzle", ball((0, 0.33, 1.2), (0.07, 0.04, 0.05), 8, 4), "Glow", (0, 0.33, 1.2))
    return P


# ================================================================= 5. the volcano fortress
def L_volcano():
    """The last boss: a floating volcanic island - a jagged basalt root below dripping lava falls, a smoking cone with a glowing crater and
    lava rivers running down it, a black fortress of towers with burning windows and red banners on its rim, a gate cannon at the front,
    and rocks drifting round it."""
    P = Boss("volcano", {"Base": ((0.13, 0.10, 0.10), 0.35), "Belly": ((0.22, 0.15, 0.12), 0.3), "Accent": ((0.70, 0.08, 0.05), 0.45),
                         "Trim": ((0.95, 0.70, 0.20), 0.7), "Glass": ((1.0, 0.75, 0.3), 0.9), "Dark": ((0.04, 0.03, 0.03), 0.4),
                         "Glow": ((1.0, 0.42, 0.05), 0.5), "Metal": ((0.30, 0.27, 0.27), 0.5), "Lamp": ((1.0, 0.85, 0.35), 0.8)})
    rng = random.Random(11)
    # the island: a flat top, a jagged root hanging below
    P.obj("Ground", lathe([(0.0, 0.18), (1.85, 0.18), (1.95, 0.08), (1.9, -0.05)], 30, "z"), lambda c, n: "Belly" if n.z > 0.5 else "Base")
    root = []
    for k in range(40):
        a = rng.uniform(0, 2 * math.pi); r = rng.uniform(0.2, 1.9); z = -0.05 - (1.9 - r) * rng.uniform(0.6, 0.9)
        root.append((math.sin(a) * r, math.cos(a) * r, z))
    root += [(math.sin(2 * math.pi * k / 16) * 1.9, math.cos(2 * math.pi * k / 16) * 1.9, -0.04) for k in range(16)] + [(0, 0, -1.6)]
    P.obj("Root", hull(root), lambda c, n: "Glow" if cracks(c, n) else "Base", 1)
    for k in range(6):   # lava falls off the rim
        a = 2 * math.pi * (k + 0.3) / 6
        p0 = Vector((math.sin(a) * 1.9, math.cos(a) * 1.9, 0.1))
        P.obj("LavaFall", pipe([p0, p0 + Vector((math.sin(a) * 0.15, math.cos(a) * 0.15, -0.3)), p0 + Vector((math.sin(a) * 0.12, math.cos(a) * 0.12, -0.9))], [0.07, 0.06, 0.0], 6), "Glow")
    # the volcano: rivers of lava down its flanks, the crater glowing
    cone_bm = lathe([(1.25, 0.18), (0.95, 0.55), (0.55, 1.15), (0.38, 1.35), (0.3, 1.32), (0.28, 1.2)], 28, "z", (0, -0.35, 0))
    def flank(c, n):
        if c.z > 1.28 or (c.z > 1.15 and n.z > 0.3): return "Glow"
        a = ang(Vector((c.x, c.y + 0.35, 0)))
        return "Glow" if (a / (2 * math.pi) * 5 + c.z * 0.25) % 1.0 < 0.08 else ("Belly" if c.z < 0.4 else "Base")
    P.obj("Cone", cone_bm, flank)
    P.obj("Crater", lathe([(0.0, 1.22), (0.28, 1.22)], 16, "z", (0, -0.35, 0)), "Glow")
    for k in range(5):   # the smoke and sparks over the crater
        P.obj("Ember", ball((rng.uniform(-0.15, 0.15), -0.35 + rng.uniform(-0.15, 0.15), 1.45 + k * 0.12), (0.07, 0.07, 0.09), 6, 3), "Lamp" if k % 2 else "Glow")
    # the fortress round the rim at the front: wall, towers, banners, the gate cannon
    for k in range(7):
        a = math.radians(-75 + k * 25)
        c = (math.sin(a) * 1.55, math.cos(a) * 1.4, 0.18)
        h = 0.55 + 0.2 * (k % 2)
        P.obj("Tower", lathe([(0.17, 0.0), (0.15, h), (0.2, h + 0.03), (0.2, h + 0.1)], 10, "z", c), lambda c2, n, h=h: "Glow" if abs(c2.z - 0.18 - h * 0.6) < 0.035 and n.z < 0.3 else "Metal")
        P.obj("Spike", cone((c[0], c[1], c[2] + h + 0.1), (c[0], c[1], c[2] + h + 0.42), 0.12, 8), "Dark", 0, False)
        if k % 2 == 0:
            P.obj("Banner", box((c[0], c[1] + 0.13, c[2] + h - 0.12), (0.02, 0.18, 0.3)), "Accent", 0, False)
    for k in range(6):
        a0 = math.radians(-75 + k * 25); a1 = math.radians(-50 + k * 25)
        p0 = Vector((math.sin(a0) * 1.55, math.cos(a0) * 1.4, 0.35)); p1 = Vector((math.sin(a1) * 1.55, math.cos(a1) * 1.4, 0.35))
        mid = (p0 + p1) * 0.5; d = p1 - p0
        P.obj("Wall", box(tuple(mid), (d.length, 0.12, 0.35), Matrix.Rotation(math.atan2(d.y, d.x), 3, "Z")), lambda c2, n: "Trim" if n.z > 0.5 else "Metal", 0, False)
    P.obj("Gate", box((0, 1.47, 0.32), (0.32, 0.1, 0.3)), "Glow", 0, False)
    P.obj("Cannon", pipe([(0, 1.35, 0.62), (0, 2.0, 0.66)], [0.13, 0.1], 10), "Metal")
    P.obj("CannonRing", pipe([(0, 1.9, 0.66), (0, 1.98, 0.66)], [0.12, 0.12], 10), "Trim")
    for k in range(7):   # rocks drifting round it
        a = 2 * math.pi * k / 7
        P.part("SpinRocks", rock((math.sin(a) * 2.4, math.cos(a) * 2.2, 0.2 + 0.3 * math.sin(a * 2)), 0.16 + 0.05 * (k % 3), rng, 10),
               lambda c, n: "Glow" if speckle(c, 1.1) < 0.12 else "Base", (0, 0, 0.2), 1)
    P.part("Muzzle", ball((0, 2.05, 0.66), (0.1, 0.05, 0.1), 8, 4), "Glow", (0, 2.05, 0.66))
    return P


BOSSES = [("phoenix", L_phoenix), ("scarab", L_scarab), ("golem", L_golem), ("ifrit", L_ifrit), ("volcano", L_volcano)]

if __name__ == "__main__":
    os.makedirs(AB.OUT, exist_ok=True)
    for bid, fn in BOSSES:
        if ONLY and bid not in ONLY: continue
        fn().finish()
    print("DONE")
