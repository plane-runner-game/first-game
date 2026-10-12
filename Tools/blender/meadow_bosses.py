# Sky Squad, the sunny meadow's five bosses (2026-10-11: "do the bosses for the other maps that do not have their own yet"): the queen
# bumblebee, the giant ladybug, the emerald dragonfly, the sunflower titan and the windmill hill. Built from code like the other worlds' bosses
# (alien_bosses.py lends its Boss class and shapes).
# Run: blender -b -P Tools/blender/meadow_bosses.py -- <out dir> [export] [ids,comma,separated]
# Conventions as alien_bosses.py: +Y nose, +Z up, +X right; "Flap*" rock about the nose axis, "Sway*" about the wing axis, "Spin*" turn slowly
# about up, "Roll*" turn slowly about the nose axis, "Cloth" stays still without the outline, "Muzzle" is where his shots leave from.
import bpy, bmesh, math, sys, os, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mathutils import Vector, Matrix
from enemy_planes import loft, sweep, lathe, box, hull, tube, mirror_x, airfoil
import alien_bosses as AB
from alien_bosses import Boss, xf, ball, pipe, cone, bez, torus, sheet, grow, ang

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ONLY = argv[2].split(",") if len(argv) > 2 and argv[2] else None

GOLD = ((0.98, 0.76, 0.22), 0.8)
WING = ((0.86, 0.95, 1.0), 0.9)
INK = ((0.05, 0.04, 0.05), 0.5)


def R(axis, deg):
    return Matrix.Rotation(math.radians(deg), 3, axis)

def ewing(hub, L, W, yaw, lift, s, thick=0.03, seg=18):
    """a flat oval wing from the hub outwards (+x on the right), swept back by yaw, raised by lift; s = -1 mirrors it to the left."""
    bm = ball((L * 0.5, 0, 0), (L * 0.5, W * 0.5, thick), seg, 6)
    xf(bm, R("Z", -yaw) @ R("Y", -lift))
    if s < 0: bm = mirror_x(bm)
    return xf(bm, None, hub)

def leaf(c, L, W, yaw, pitch, thick=0.05):
    """a pointed leaf lying along +x from c, turned by yaw about up and pitch about the nose axis."""
    bm = ball((L * 0.5, 0, 0), (L * 0.5, W * 0.5, thick), 16, 6)
    for v in bm.verts:
        t = v.co.x / L                       # pinch both ends to points
        v.co.y *= 0.35 + 0.9 * math.sin(math.pi * min(max(t, 0.0), 1.0)) ** 0.8
        v.co.z += 0.12 * L * t * t           # the tip curls up
    xf(bm, R("Z", yaw) @ R("Y", -pitch))
    return xf(bm, None, c)

def cute_eyes(P, c, r, s, white="Glass", pupil="Dark", shine="Glow", look=(0, 1, 0)):
    """a big cartoon eye: a white, a pupil looking forward, a spark of light."""
    c = Vector(c); L = Vector(look).normalized()
    P.obj("EyeWhite", ball(tuple(c), (r, r * 0.7, r * 1.1), 12, 6), white)
    pc = c + L * r * 0.55 + Vector((-s * r * 0.08, 0, -r * 0.05))
    P.obj("Pupil", ball(tuple(pc), (r * 0.55, r * 0.35, r * 0.65), 10, 5), pupil)
    P.obj("Spark", ball(tuple(pc + L * r * 0.28 + Vector((s * r * 0.15, 0, r * 0.25))), (r * 0.15, r * 0.08, r * 0.15), 6, 3), shine)


# ================================================================= 1. the queen bumblebee
def M_bee():
    """The queen of the meadow: a round fuzzy bumblebee in gold and black bands, a golden crown with ruby gems, big glossy eyes, curling
    antennae, four glassy wings buzzing, a honey-dipper sceptre in her hand and a stinger behind."""
    P = Boss("bee", {"Base": ((1.0, 0.78, 0.12), 0.35), "Belly": ((0.98, 0.58, 0.10), 0.25), "Accent": ((0.85, 0.08, 0.16), 0.8), "Trim": GOLD,
                     "Glass": WING, "Dark": INK, "Glow": ((1.0, 1.0, 0.95), 0.5), "Metal": ((0.6, 0.6, 0.6), 0.6), "Lamp": ((1.0, 0.62, 0.10), 0.9)})
    band = lambda c, n: "Dark" if int((0.25 - c.y) / 0.3) % 2 else "Base"
    rings = [(-0.1, 0.32, 0.3, 0, 0.05), (-0.35, 0.56, 0.52, 0, 0.02), (-0.75, 0.66, 0.6, 0, -0.04), (-1.15, 0.58, 0.54, 0, -0.08), (-1.48, 0.38, 0.36, 0, -0.1), (-1.72, 0.12, 0.12, 0, -0.1)]
    P.obj("Abdomen", loft(rings, 22), band, 1)
    P.obj("Stinger", cone((0, -1.68, -0.1), (0, -2.05, -0.16), 0.07, 8), "Dark", 0, False)
    P.obj("Thorax", ball((0, 0.15, 0.1), (0.5, 0.46, 0.46), 16, 8), "Belly", 1)
    P.obj("Collar", torus(0.36, 0.08, 0.0, 22, 6), "Base"); P.parts[-1].data.transform(Matrix.Translation((0, 0.5, 0.12)) @ Matrix.Rotation(math.radians(90), 4, "X"))
    HC = (0, 0.78, 0.18)
    P.obj("Head", ball(HC, (0.38, 0.32, 0.34), 16, 8), "Dark", 1)
    for s in (1, -1):
        cute_eyes(P, (s * 0.17, 1.0, 0.24), 0.14, s, white="Glass", pupil="Dark", shine="Glow")
        P.obj("Cheek", ball((s * 0.22, 1.02, 0.06), (0.07, 0.03, 0.05), 8, 4), "Belly")
        ant = bez((s * 0.1, 0.95, 0.45), (s * 0.18, 1.1, 0.75), (s * 0.35, 1.2, 0.85), (s * 0.45, 1.3, 0.8), 6)
        P.obj("Antenna", pipe(ant, [0.03] * 6 + [0.025], 6), "Dark")
        P.obj("AntennaTip", ball(tuple(ant[-1]), (0.06, 0.06, 0.06), 8, 4), "Trim")
        for k in range(3):   # six legs
            hip = Vector((s * 0.28, 0.3 - 0.2 * k, -0.2)); knee = Vector((s * 0.52, 0.38 - 0.25 * k, -0.42)); foot = Vector((s * 0.42, 0.5 - 0.3 * k, -0.7))
            if k == 0 and s > 0: foot = Vector((s * 0.62, 0.78, -0.25))
            P.obj("Leg", pipe([hip, knee, foot], [0.05, 0.045, 0.035], 6), "Dark")
        name = "FlapR" if s > 0 else "FlapL"
        hub = (s * 0.3, 0.2, 0.5)
        wp = lambda c, n: "Trim" if abs(n.z) < 0.3 else "Glass"
        P.part(name, ewing(hub, 1.55, 0.62, 18, 22, s), wp, hub, 0)
        P.part(name, ewing((s * 0.3, 0.05, 0.45), 1.05, 0.44, 48, 14, s), wp, hub, 0)
    # the crown
    P.obj("Crown", lathe([(0.22, 0.0), (0.26, 0.16), (0.25, 0.17), (0.2, 0.02)], 16, "z", (0, 0.74, 0.47)), "Trim")
    for k in range(6):
        a = 2 * math.pi * k / 6
        b = Vector((math.cos(a) * 0.25, 0.74 + math.sin(a) * 0.25, 0.63))
        P.obj("CrownSpike", cone(tuple(b), tuple(b + Vector((math.cos(a) * 0.04, math.sin(a) * 0.04, 0.2))), 0.055, 5), "Trim", 0, False)
        P.obj("CrownBall", ball(tuple(b + Vector((math.cos(a) * 0.04, math.sin(a) * 0.04, 0.22))), (0.035, 0.035, 0.035), 6, 3), "Trim")
        P.obj("Ruby", ball((math.cos(a) * 0.26, 0.74 + math.sin(a) * 0.26, 0.55), (0.05, 0.05, 0.05), 6, 3), "Accent")
    # the honey-dipper sceptre in her right hand
    P.obj("Staff", pipe([(0.62, 0.78, -0.5), (0.66, 0.8, 0.3)], [0.03, 0.03], 6), "Trim")
    P.obj("Dipper", lathe([(0.0, 0.3), (0.1, 0.32), (0.14, 0.4), (0.1, 0.48), (0.14, 0.56), (0.1, 0.64), (0.0, 0.67)], 12, "z", (0.66, 0.8, 0)), "Lamp")
    for k in range(4): P.obj("Drip", ball((0.66 + 0.08 * math.cos(k * 1.7), 0.8 + 0.08 * math.sin(k * 1.7), 0.26 - 0.06 * k), (0.035, 0.035, 0.05), 6, 3), "Lamp")
    P.part("Muzzle", ball((0, 1.1, 0.12), (0.06, 0.03, 0.05), 8, 4), "Glow", (0, 1.1, 0.12))
    return P


# ================================================================= 2. the giant ladybug
def M_ladybug():
    """A great ladybug in flight: a glossy scarlet shell split open as two raised wing cases with black spots, amber flying wings beneath, a
    black head with white patches, big friendly eyes and curled antennae, six little legs."""
    P = Boss("ladybug", {"Base": ((0.90, 0.08, 0.06), 0.85), "Belly": ((0.97, 0.97, 0.95), 0.4), "Accent": ((1.0, 0.85, 0.3), 0.5), "Trim": GOLD,
                         "Glass": ((1.0, 0.9, 0.7), 0.9), "Dark": INK, "Glow": ((1.0, 1.0, 0.95), 0.5), "Metal": ((0.6, 0.6, 0.6), 0.6), "Lamp": ((1.0, 0.85, 0.35), 0.8)})
    P.obj("Under", ball((0, -0.15, -0.05), (0.72, 1.0, 0.4), 18, 8), "Dark", 1)
    P.obj("Pronotum", ball((0, 0.7, 0.12), (0.6, 0.38, 0.34), 16, 8), lambda c, n: "Belly" if abs(c.x) > 0.3 and n.z > -0.2 else "Dark", 1)
    HC = (0, 1.02, 0.02)
    P.obj("Head", ball(HC, (0.38, 0.3, 0.3), 14, 7), "Dark", 1)
    for s in (1, -1):
        cute_eyes(P, (s * 0.18, 1.2, 0.12), 0.13, s, white="Belly")
        P.obj("Smile", pipe(bez((s * 0.0, 1.31, -0.08), (s * 0.06, 1.32, -0.11), (s * 0.12, 1.3, -0.1), (s * 0.16, 1.27, -0.05), 4), [0.018] * 5, 5), "Belly")
        ant = bez((s * 0.12, 1.15, 0.25), (s * 0.2, 1.35, 0.55), (s * 0.4, 1.45, 0.6), (s * 0.42, 1.35, 0.45), 7)
        P.obj("Antenna", pipe(ant, [0.025] * 8, 6), "Dark")
        P.obj("AntennaTip", ball(tuple(ant[-1]), (0.05, 0.05, 0.05), 8, 4), "Dark")
        for k in range(3):
            hip = Vector((s * 0.45, 0.45 - 0.4 * k, -0.25)); knee = Vector((s * 0.75, 0.5 - 0.45 * k, -0.35)); foot = Vector((s * 0.7, 0.6 - 0.5 * k, -0.6))
            P.obj("Leg", pipe([hip, knee, foot], [0.05, 0.045, 0.035], 6), "Dark")
        # the wing case, raised and opened on its hinge, and the flying wing under it
        name = "FlapR" if s > 0 else "FlapL"
        hinge = Vector((s * 0.06, 0.45, 0.35))
        ctr = Vector((s * 0.4, -0.25, 0.12)); rad = Vector((0.46, 0.95, 0.5))
        rot = R("Y", -s * 28) @ R("X", 12)
        T = lambda p: rot @ (Vector(p) - hinge) + hinge
        dirs = [(0.2, 0.75, 0.6), (0.55, 0.2, 0.75), (0.3, -0.3, 0.9), (0.75, -0.45, 0.45), (0.25, -0.8, 0.5), (0.85, 0.3, 0.3)]
        bm = ball(tuple(ctr), tuple(rad), 24, 12)
        for v in bm.verts:
            if v.co.z < ctr.z: v.co.z = ctr.z + (v.co.z - ctr.z) * 0.25   # a shallow shell, not a ball
            v.co = T(v.co)
        P.part(name, bm, "Base", tuple(hinge), 1)
        for k, d in enumerate(dirs):   # round black spots sitting on the shell
            d = Vector((s * d[0], d[1], d[2])).normalized()
            on = ctr + Vector((d.x * rad.x, d.y * rad.y, d.z * rad.z))
            nrm = (rot @ Vector((d.x / rad.x, d.y / rad.y, d.z / rad.z))).normalized()
            r = 0.15 if k % 2 == 0 else 0.12
            sp = ball((0, 0, 0), (r, r, 0.035), 14, 5)
            xf(sp, nrm.to_track_quat("Z", "Y").to_matrix(), tuple(T(on) + nrm * 0.005))
            P.part(name, sp, "Dark", tuple(hinge), 0)
        P.part(name, ewing((s * 0.25, 0.25, 0.25), 1.75, 0.7, 30, 6, s), lambda c, n: "Trim" if abs(n.z) < 0.3 else "Glass", tuple(hinge), 0)
    P.part("Muzzle", ball((0, 1.3, -0.02), (0.06, 0.03, 0.05), 8, 4), "Glow", (0, 1.3, -0.02))
    return P


# ================================================================= 3. the emerald dragonfly
def M_dragonfly():
    """A great dragonfly of the summer pond: a shining emerald thorax, huge turquoise eyes, a long jewelled tail banded in gold, four long
    glassy wings edged in gold with dark tips, beating."""
    P = Boss("dragonfly", {"Base": ((0.08, 0.62, 0.38), 0.85), "Belly": ((0.12, 0.35, 0.65), 0.8), "Accent": ((0.0, 0.85, 0.85), 0.9), "Trim": GOLD,
                           "Glass": ((0.80, 0.95, 1.0), 0.9), "Dark": INK, "Glow": ((1.0, 1.0, 0.95), 0.5), "Metal": ((0.6, 0.6, 0.6), 0.6), "Lamp": ((0.5, 1.0, 0.8), 0.8)})
    P.obj("Thorax", ball((0, 0.3, 0.05), (0.4, 0.55, 0.42), 14, 7), lambda c, n: "Trim" if abs(c.x) < 0.06 and n.z > 0.5 else "Base", 1)
    P.obj("Head", ball((0, 0.92, 0.1), (0.34, 0.24, 0.27), 12, 6), "Base", 1)
    for s in (1, -1):
        P.obj("Eye", ball((s * 0.25, 1.0, 0.22), (0.29, 0.26, 0.3), 14, 7), lambda c, n: "Belly" if n.z < -0.4 else "Accent", 1)
        P.obj("Spark", ball((s * 0.3, 1.22, 0.36), (0.06, 0.025, 0.06), 6, 3), "Glow")
        for k in range(3):
            hip = Vector((s * 0.15, 0.55 - 0.18 * k, -0.22)); foot = Vector((s * 0.35, 0.65 - 0.25 * k, -0.6))
            P.obj("Leg", pipe([hip, (hip + foot) * 0.5 + Vector((s * 0.1, 0, 0.05)), foot], [0.035, 0.03, 0.02], 5), "Dark")
        name = "FlapR" if s > 0 else "FlapL"
        hub = (s * 0.18, 0.3, 0.32)
        def wp(c, n, s=s):
            if abs(c.x) > 1.85: return "Dark"
            if abs(n.z) < 0.3: return "Trim"
            return "Glass"
        P.part(name, ewing((s * 0.22, 0.45, 0.36), 2.15, 0.56, -4, 8, s), wp, hub, 0)
        P.part(name, ewing((s * 0.22, 0.12, 0.34), 2.0, 0.62, 14, 6, s), wp, hub, 0)
    # the long tail in ten segments
    N = 10
    for k in range(N):
        y0 = -0.15 - k * 0.24; y1 = y0 - 0.24
        r0 = 0.14 - 0.006 * k; r1 = r0 - 0.012
        z0 = 0.02 + 0.012 * k; z1 = z0 + 0.012
        P.obj("Tail", loft([(y0, r0, r0, 0, z0), (y0 - 0.04, r0 * 1.08, r0 * 1.08, 0, z0), (y1 + 0.03, r1 * 0.9, r1 * 0.9, 0, z1), (y1, r1 * 0.85, r1 * 0.85, 0, z1)], 12),
              lambda c, n, y0=y0: "Trim" if c.y > y0 - 0.06 else ("Belly" if n.z < -0.3 else "Base"), 0)
    tip = Vector((0, -0.15 - N * 0.24, 0.02 + 0.012 * N))
    for s in (1, -1): P.obj("Clasper", cone(tuple(tip), tuple(tip + Vector((s * 0.08, -0.18, 0.04))), 0.035, 5), "Dark", 0, False)
    P.part("Muzzle", ball((0, 1.13, -0.02), (0.06, 0.03, 0.05), 8, 4), "Glow", (0, 1.06, 0.0))
    return P


# ================================================================= 4. the sunflower titan
def M_sunflower():
    """A giant sunflower come alive, flying in its terracotta pot: a smiling face on the seed disc, two rings of golden petals turning slowly
    face-on, leaf arms waving, a curling stem, a ladybug on a leaf."""
    P = Boss("sunflower", {"Base": ((0.28, 0.66, 0.18), 0.45), "Belly": ((1.0, 0.56, 0.08), 0.45), "Accent": ((0.78, 0.36, 0.18), 0.3), "Trim": ((1.0, 0.82, 0.10), 0.5),
                           "Glass": ((0.98, 0.98, 0.95), 0.7), "Dark": ((0.14, 0.07, 0.03), 0.4), "Glow": ((1.0, 1.0, 0.9), 0.5),
                           "Metal": ((0.40, 0.22, 0.07), 0.5), "Lamp": ((1.0, 0.85, 0.35), 0.8)})
    FC = Vector((0, 0.25, 1.05))                          # the middle of the face
    # the face: a seed disc facing the player
    def seeds(c, n):
        d = c - FC; r = math.hypot(d.x, d.z)
        if n.y < 0.2: return "Base"
        a = math.atan2(d.z, d.x)
        return "Metal" if ((a / (2 * math.pi) * 13 + r * 9) % 1.0 < 0.5) ^ ((a / (2 * math.pi) * -8 + r * 9) % 1.0 < 0.5) else "Dark"
    P.obj("Disc", lathe([(0.0, 0.16), (0.42, 0.14), (0.66, 0.06), (0.72, -0.02), (0.6, -0.1), (0.0, -0.16)], 28, "y", tuple(FC)), seeds, 0)
    for s in (1, -1):
        cute_eyes(P, (FC.x + s * 0.24, FC.y + 0.14, FC.z + 0.12), 0.13, s, white="Glass")
        P.obj("Cheek", ball((FC.x + s * 0.4, FC.y + 0.12, FC.z - 0.08), (0.08, 0.03, 0.06), 8, 4), "Belly")
    P.obj("Smile", pipe(bez((-0.24, FC.y + 0.16, FC.z - 0.12), (-0.1, FC.y + 0.19, FC.z - 0.3), (0.1, FC.y + 0.19, FC.z - 0.3), (0.24, FC.y + 0.16, FC.z - 0.12), 8), [0.035] * 9, 6), "Accent")
    # the petals turn face-on about the nose axis
    for ring, (n, rr, L, W, col, dy, off) in enumerate(((18, 0.7, 0.62, 0.3, "Trim", 0.0, 0.0), (18, 0.66, 0.55, 0.28, "Belly", -0.06, 0.5))):
        for k in range(n):
            a = 2 * math.pi * (k + off) / n
            bm = ball((0, 0, L * 0.5), (W * 0.5, 0.04, L * 0.5), 10, 5)
            for v in bm.verts:   # pointed tips
                t = v.co.z / L; v.co.x *= 0.45 + 0.75 * math.sin(math.pi * min(max(t, 0.0), 1.0)) ** 0.7
                v.co.y += 0.08 * t * t * (1 if ring == 0 else -1)
            xf(bm, R("Y", math.degrees(a)), (FC.x + math.sin(a) * rr, FC.y + dy, FC.z + math.cos(a) * rr))
            P.part("RollPetals", bm, col, tuple(FC), 0)
    # the stem, the leaf arms and the pot
    stem = bez((0, FC.y - 0.15, FC.z - 0.2), (0, -0.25, 0.45), (0, 0.15, -0.15), (0, 0.0, -0.55), 8)
    P.obj("Stem", pipe(stem, [0.13, 0.12, 0.12, 0.11, 0.11, 0.11, 0.12, 0.13, 0.14], 10), "Base")
    for s in (1, -1):
        hub = Vector((s * 0.08, 0.05, -0.05))
        name = "SwayR" if s > 0 else "SwayL"
        P.part(name, leaf(hub, 1.45, 0.7, 25 if s > 0 else 155, 18), "Base", tuple(hub), 1)
    P.obj("Pot", lathe([(0.0, -1.35), (0.36, -1.35), (0.52, -0.75), (0.62, -0.72), (0.64, -0.55), (0.56, -0.52), (0.5, -0.56), (0.0, -0.56)], 22, "z"),
          lambda c, n: "Dark" if c.z > -0.58 and n.z > 0.5 else "Accent", 0)
    for k in range(6):
        a = 2 * math.pi * k / 6 + 0.3
        P.obj("Pebble", ball((math.cos(a) * 0.3, math.sin(a) * 0.3, -0.54), (0.07, 0.06, 0.04), 6, 3), "Metal")
    # a little ladybug riding on the right leaf
    lb = Vector((0.75, 0.42, 0.32))
    P.obj("Bug", ball(tuple(lb), (0.1, 0.12, 0.07), 10, 5), lambda c, n: "Dark" if abs(c.x - lb.x) < 0.012 or (c - lb).length < 0.05 else "Accent")
    P.part("Muzzle", ball((0, FC.y + 0.17, FC.z - 0.24), (0.04, 0.02, 0.03), 8, 4), "Accent", (0, FC.y + 0.17, FC.z - 0.24))
    return P


# ================================================================= 5. the windmill hill
def M_windmill():
    """The last boss: a whole hill of the meadow flown up into the sky - a grassy island on an earthy root, a white windmill with a red cap
    whose four sails turn face-on, a cottage with glowing windows, a pond, round trees, flowers everywhere, and bees circling round it."""
    P = Boss("windmill", {"Base": ((0.36, 0.72, 0.22), 0.3), "Belly": ((0.97, 0.94, 0.86), 0.35), "Accent": ((0.84, 0.18, 0.12), 0.55), "Trim": ((1.0, 0.82, 0.18), 0.6),
                          "Glass": ((0.32, 0.65, 0.98), 0.85), "Dark": ((0.36, 0.22, 0.10), 0.3), "Glow": ((1.0, 1.0, 0.9), 0.5),
                          "Metal": ((0.60, 0.58, 0.54), 0.25), "Lamp": ((1.0, 0.82, 0.45), 0.8)})
    rng = random.Random(4)
    P.obj("Ground", lathe([(0.0, 0.12), (1.7, 0.12), (1.85, 0.06), (1.9, -0.02), (1.85, -0.1)], 30, "z"), lambda c, n: "Base" if n.z > 0.3 else "Dark")
    root = []
    for k in range(40):
        a = rng.uniform(0, 2 * math.pi); r = rng.uniform(0.2, 1.85)
        root.append((math.sin(a) * r, math.cos(a) * r, -0.1 - (1.85 - r) * rng.uniform(0.45, 0.75)))
    root += [(math.sin(2 * math.pi * k / 18) * 1.85, math.cos(2 * math.pi * k / 18) * 1.85, -0.08) for k in range(18)] + [(0, 0, -1.35)]
    P.obj("Root", hull(root), lambda c, n: "Metal" if speckle(c, 1.5) < 0.3 else "Dark", 0, False)
    # the windmill
    wc = Vector((-0.35, -0.35, 0.12))
    P.obj("Tower", lathe([(0.55, 0.0), (0.5, 0.6), (0.4, 1.6), (0.36, 1.75), (0.0, 1.75)], 8, "z", tuple(wc)),
          lambda c, n: "Dark" if 0.62 < c.z - wc.z < 0.72 else "Belly", 0, False)
    P.obj("Gallery", lathe([(0.62, 0.62), (0.62, 0.7), (0.0, 0.7)], 16, "z", tuple(wc)), "Dark", 0, False)
    P.obj("Cap", lathe([(0.44, 1.72), (0.42, 1.95), (0.25, 2.2), (0.0, 2.32)], 16, "z", tuple(wc)), "Accent")
    P.obj("Door", box((wc.x, wc.y + 0.52, wc.z + 0.2), (0.22, 0.05, 0.38)), "Dark", 0, False)
    for z in (0.95, 1.35): P.obj("Window", box((wc.x, wc.y + 0.49 - 0.1 * (z - 0.6), wc.z + z), (0.14, 0.06, 0.16)), "Lamp", 0, False)
    hub = Vector((wc.x, wc.y + 0.55, wc.z + 1.85))
    P.obj("Axle", pipe([hub + Vector((0, -0.2, 0)), hub + Vector((0, 0.08, 0))], [0.07, 0.07], 8), "Dark")
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        d = Vector((math.cos(a), 0, math.sin(a))); side = Vector((-d.z, 0, d.x))
        P.part("RollSails", pipe([hub, hub + d * 1.25], [0.035, 0.03], 5), "Dark", tuple(hub), 0, False)
        q = [hub + d * 0.3 + side * 0.04, hub + d * 1.22 + side * 0.04, hub + d * 1.22 + side * 0.32, hub + d * 0.3 + side * 0.28]
        P.part("RollSails", sheet([[tuple(p) for p in q]], 0.02), "Belly", tuple(hub), 0, False)   # the canvas
        for t in (0.45, 0.7, 0.95):   # the lattice
            P.part("RollSails", pipe([hub + d * (t + 0.08) + side * 0.03, hub + d * (t + 0.08) + side * 0.33], [0.015, 0.015], 4), "Dark", tuple(hub), 0, False)
        P.part("RollSails", pipe([hub + d * 1.22 + side * 0.34, hub + d * 0.3 + side * 0.32], [0.015, 0.015], 4), "Dark", tuple(hub), 0, False)
    # the cottage
    cc = Vector((0.85, -0.2, 0.12))
    P.obj("Cottage", box((cc.x, cc.y, cc.z + 0.25), (0.6, 0.5, 0.5)), "Belly", 0, False)
    P.obj("CottageRoof", hull([(cc.x - 0.36, cc.y - 0.32, cc.z + 0.48), (cc.x + 0.36, cc.y - 0.32, cc.z + 0.48), (cc.x - 0.36, cc.y + 0.32, cc.z + 0.48), (cc.x + 0.36, cc.y + 0.32, cc.z + 0.48),
                                (cc.x - 0.36, cc.y, cc.z + 0.8), (cc.x + 0.36, cc.y, cc.z + 0.8)]), "Accent", 0, False)
    P.obj("Chimney", box((cc.x + 0.18, cc.y - 0.1, cc.z + 0.8), (0.1, 0.1, 0.25)), "Metal", 0, False)
    P.obj("CDoor", box((cc.x, cc.y + 0.26, cc.z + 0.16), (0.14, 0.03, 0.26)), "Dark", 0, False)
    for s in (1, -1): P.obj("CWin", box((cc.x + s * 0.2, cc.y + 0.26, cc.z + 0.3), (0.1, 0.03, 0.1)), "Lamp", 0, False)
    # the pond, trees, flowers, a fence
    P.obj("Pond", ball((0.55, 0.85, 0.13), (0.42, 0.3, 0.03), 18, 4), "Glass")
    for (x, y, h) in ((-1.25, 0.35, 0.6), (1.3, 0.55, 0.45), (-0.95, -1.15, 0.7), (1.1, -1.05, 0.55)):
        P.obj("Trunk", pipe([(x, y, 0.1), (x, y, 0.1 + h)], [0.07, 0.05], 6), "Dark")
        P.obj("Crown", ball((x, y, 0.15 + h + 0.25), (0.34, 0.34, 0.36), 12, 6), "Base", 1)
        P.obj("Apple", ball((x + 0.2, y + 0.22, 0.15 + h + 0.25), (0.05, 0.05, 0.05), 6, 3), "Accent")
    for k in range(60):
        a = rng.uniform(0, 2 * math.pi); r = rng.uniform(0.3, 1.75)
        x, y = math.sin(a) * r, math.cos(a) * r
        if (Vector((x, y)) - wc.xy).length < 0.7 or (Vector((x, y)) - cc.xy).length < 0.5 or (Vector((x, y)) - Vector((0.55, 0.85))).length < 0.5: continue
        P.obj("Flower", ball((x, y, 0.17), (0.06, 0.06, 0.04), 6, 3), ("Trim", "Accent", "Belly", "Glass")[k % 4])
    for k in range(9):   # a little fence along the front edge
        a = math.radians(-50 + k * 12.5)
        p = Vector((math.sin(a) * 1.6, math.cos(a) * 1.6, 0.12))
        P.obj("Post", box((p.x, p.y, p.z + 0.12), (0.05, 0.05, 0.24)), "Belly", 0, False)
    P.obj("Rail", pipe([(math.sin(math.radians(-50 + t * 2.5)) * 1.6, math.cos(math.radians(-50 + t * 2.5)) * 1.6, 0.3) for t in range(41)], [0.022] * 41, 4), "Belly")
    # bees circling
    for k in range(8):
        a = 2 * math.pi * k / 8
        b = Vector((math.cos(a) * 2.3, math.sin(a) * 2.2, 0.9 + 0.35 * math.sin(a * 2)))
        P.part("SpinBees", ball(tuple(b), (0.09, 0.13, 0.09), 8, 4), lambda c, n, b=b: "Dark" if int((c.y - b.y + 0.2) / 0.08) % 2 else "Trim", (0, 0, 0.9))
        for s in (1, -1): P.part("SpinBees", ball(tuple(b + Vector((s * 0.1, 0, 0.08))), (0.08, 0.04, 0.02), 6, 3), "Glass", (0, 0, 0.9))
    P.part("Muzzle", ball((wc.x, wc.y + 0.6, wc.z + 0.5), (0.07, 0.03, 0.07), 8, 4), "Lamp", (wc.x, wc.y + 0.6, wc.z + 0.5))
    return P


def speckle(c, k=1.0):
    v = math.sin(c.x * 12.9898 * k + c.y * 78.233 * k + c.z * 37.719 * k) * 43758.5453
    return v - math.floor(v)


# ================================================================= 2026-10-11 round two: the snail king (in place of windmill hill)
def lid(c, r, s, tilt=18):
    """a heavy upper eyelid: the top of a ball a little bigger than the eye, tipped forward - a proud, half-closed look."""
    bm = ball(tuple(c), (r * 1.08, r * 1.08, r * 1.08), 12, 8)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < c[2] + r * 0.42], context="VERTS")
    xf(bm, None, (-c[0], -c[1], -c[2])); xf(bm, R("X", -tilt) @ R("Y", s * 8)); xf(bm, None, tuple(c))
    bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=0.02)
    return bm

def M_snail():
    """The last boss: the snail king of the meadow - a great soft snail with a golden spiral shell banded in pearl, and on top of the
    shell his own little castle with red-roofed turrets, flags and glowing windows; a proud face with heavy-lidded eyes on tall stalks,
    rosy cheeks, a curling golden moustache and a smile, a jewelled crown between the stalks, a gold collar, and butterflies circling
    round him. The spiral faces the player, rising behind him like a golden shield."""
    P = Boss("snail", {"Base": ((0.52, 0.80, 0.60), 0.4), "Belly": ((0.98, 0.97, 0.94), 0.4), "Accent": ((0.82, 0.10, 0.16), 0.55), "Trim": GOLD,
                       "Glass": ((0.20, 0.45, 0.98), 0.9), "Dark": INK, "Glow": ((1.0, 1.0, 0.95), 0.5),
                       "Metal": ((0.95, 0.93, 0.96), 0.85), "Lamp": ((1.0, 0.78, 0.35), 0.9)})
    # the soft body, long and low, rising into the neck and head
    P.obj("Foot", pipe([(0, -1.45, -0.75), (0, -1.1, -0.68), (0, -0.3, -0.62), (0, 0.5, -0.55), (0, 0.95, -0.3), (0, 1.15, 0.1)],
                       [0.04, 0.36, 0.56, 0.6, 0.58, 0.52], 18), lambda c, n: "Metal" if n.z < -0.6 else "Base", 1)
    P.obj("Head", ball((0, 1.2, 0.5), (0.72, 0.6, 0.66), 16, 8), "Base", 1)
    # the golden spiral shell, banded in pearl
    C = Vector((0, -0.55, 1.15)); R0, K = 1.25, 0.12
    pts, rad = [], []
    for i in range(70):
        t = i / 69.0 * 3.4 * math.pi; r = R0 * math.exp(-K * t); th = -math.pi / 2 + t
        pts.append(tuple(C + Vector((-math.cos(th) * r, 0, math.sin(th) * r)))); rad.append(0.0 if i == 69 else 0.5 * r / R0 * (1.0 if i < 64 else (69 - i) / 5.0))
    bm = pipe(pts, rad, 18)
    for v in bm.verts: v.co.y = C.y + (v.co.y - C.y) * 1.25
    def band(c, n):
        d = c - C; a = math.atan2(d.z, -d.x)
        return "Metal" if math.sin(a * 7.0) > 0.72 else "Trim"
    P.obj("Shell", bm, band, 1)
    for k in range(5):
        t = (k + 0.5) / 5.0 * 3.0 * math.pi; r = R0 * math.exp(-K * t); th = -math.pi / 2 + t
        q = C + Vector((-math.cos(th) * r, 0.42 * r / R0 + 0.02, math.sin(th) * r))
        P.obj("ShellGem", ball(tuple(q), (0.09 * r / R0 + 0.03, 0.05, 0.09 * r / R0 + 0.03), 10, 5), "Glass" if k % 2 else "Accent")
    # his castle on top of the shell
    rt = R0 * math.exp(-K * math.pi); k0 = Vector((0, C.y - 0.1, C.z + rt + 0.4 * rt / R0 * 0.8))
    P.obj("Keep", box(tuple(k0 + Vector((0, 0, 0.3))), (0.5, 0.5, 0.6)), lambda c, n: "Lamp" if abs(n.y) > 0.5 and abs(c.x) < 0.1 and c.z > k0.z + 0.35 else "Belly", 0, False)
    P.obj("KeepRoof", cone(tuple(k0 + Vector((0, 0, 0.6))), tuple(k0 + Vector((0, 0, 1.15))), 0.4, 4), "Accent", 0, False)
    P.obj("KeepFlagPole", pipe([tuple(k0 + Vector((0, 0, 1.1))), tuple(k0 + Vector((0, 0, 1.45)))], [0.015, 0.015], 4), "Dark")
    P.part("Cloth", sheet([[tuple(k0 + Vector((0, 0, 1.45))), tuple(k0 + Vector((0, 0, 1.31))), tuple(k0 + Vector((0, -0.28, 1.38)))]], 0.02), "Glass", (0, 0, 0), 0, False)
    for sx in (1, -1):
        for sy in (1, -1):
            tc = k0 + Vector((sx * 0.36, sy * 0.3, 0))
            P.obj("Turret", lathe([(0.15, 0.0), (0.15, 0.5), (0.18, 0.52), (0.18, 0.6), (0.0, 0.6)], 12, "z", tuple(tc)), lambda c, n: "Lamp" if n.y > 0.6 and 0.25 < c.z - k0.z < 0.36 else "Belly", 0, False)
            P.obj("TurretRoof", cone(tuple(tc + Vector((0, 0, 0.6))), tuple(tc + Vector((0, 0, 0.95))), 0.21, 12), "Accent", 0, False)
            P.obj("TurretTip", ball(tuple(tc + Vector((0, 0, 0.97))), (0.03, 0.03, 0.03), 6, 3), "Trim")
    # the face: heavy-lidded eyes on tall stalks, rosy cheeks, a golden moustache, a smile
    for s in (1, -1):
        top = Vector((s * 0.45, 1.55, 1.62))
        P.obj("Stalk", pipe([(s * 0.22, 1.3, 0.95), (s * 0.34, 1.45, 1.3), tuple(top - Vector((0, 0, 0.16)))], [0.11, 0.09, 0.085], 10), "Base", 1)
        P.obj("EyeWhite", ball(tuple(top), (0.27, 0.24, 0.27), 14, 7), "Belly", 1)
        P.obj("Pupil", ball(tuple(top + Vector((-s * 0.03, 0.2, -0.06))), (0.15, 0.07, 0.16), 10, 5), "Dark")
        P.obj("Spark", ball(tuple(top + Vector((s * 0.02, 0.27, 0.0))), (0.05, 0.02, 0.05), 6, 3), "Glow")
        P.obj("Lid", lid(top, 0.27, s, 12), "Base", 0, True)
        P.obj("Feeler", pipe([(s * 0.3, 1.68, 0.36), (s * 0.44, 1.88, 0.4), (s * 0.5, 1.96, 0.48)], [0.05, 0.04, 0.0], 8), "Base")
        P.obj("Cheek", ball((s * 0.42, 1.68, 0.44), (0.16, 0.06, 0.11), 10, 5), "Accent")
        P.obj("Moustache", pipe([(s * 0.03, 1.82, 0.42), (s * 0.2, 1.84, 0.36), (s * 0.38, 1.78, 0.42), (s * 0.48, 1.7, 0.55), (s * 0.43, 1.65, 0.65)],
                                [0.065, 0.07, 0.055, 0.03, 0.0], 8), "Trim")
    P.obj("Smile", pipe([(-0.22, 1.76, 0.24), (-0.1, 1.82, 0.16), (0.1, 1.82, 0.16), (0.22, 1.76, 0.24)], [0.03, 0.035, 0.035, 0.03], 6), "Dark")
    # the crown between the stalks
    cc = (0, 1.1, 1.08)
    P.obj("Crown", lathe([(0.24, 0.0), (0.27, 0.06), (0.28, 0.18), (0.25, 0.18), (0.22, 0.04)], 18, "z", cc), "Trim")
    for k in range(6):
        a = 2 * math.pi * k / 6 + 0.26
        b = Vector(cc) + Vector((math.cos(a) * 0.27, math.sin(a) * 0.27, 0.16))
        P.obj("CrownSpike", cone(tuple(b), tuple(b + Vector((0, 0, 0.17))), 0.06, 5), "Trim", 0, False)
        P.obj("CrownPearl", ball(tuple(b + Vector((0, 0, 0.19))), (0.035, 0.035, 0.035), 6, 3), "Belly")
        P.obj("CrownGem", ball(tuple(Vector(cc) + Vector((math.cos(a + 0.52) * 0.28, math.sin(a + 0.52) * 0.28, 0.09))), (0.04, 0.03, 0.04), 6, 3), "Glass" if k % 2 else "Accent")
    # a gold collar of office where the head meets the body
    P.obj("Collar", xf(torus(0.62, 0.07, 0.0, 26, 6), Matrix.Rotation(math.radians(-25), 3, "X") @ Matrix.Diagonal((1.0, 0.8, 1.0)), (0, 0.85, 0.05)), "Trim", 1)
    P.obj("CollarGem", ball((0, 1.38, -0.1), (0.1, 0.06, 0.1), 10, 5), "Accent")
    # butterflies circling
    cols = ("Glass", "Accent", "Trim", "Belly")
    for k in range(6):
        a = 2 * math.pi * k / 6 + 0.5
        b = Vector((math.cos(a) * 1.85, math.sin(a) * 1.7, 1.2 + 0.3 * math.sin(a * 2)))
        f = Vector((-math.sin(a), math.cos(a), 0))
        side = Vector((math.cos(a), math.sin(a), 0))
        P.part("SpinFlies", pipe([tuple(b - f * 0.12), tuple(b + f * 0.12)], [0.025, 0.02], 5), "Dark", (0, 0, 1.2), 0)
        for s in (1, -1):
            w = [b, b + side * s * 0.26 + f * 0.16 + Vector((0, 0, 0.1)), b + side * s * 0.3 - f * 0.02 + Vector((0, 0, 0.12)), b + side * s * 0.18 - f * 0.16 + Vector((0, 0, 0.06))]
            P.part("SpinFlies", sheet([[tuple(p) for p in w]], 0.015), cols[k % 4], (0, 0, 1.2), 0, False)
    P.part("Muzzle", ball((0, 1.84, 0.2), (0.05, 0.03, 0.04), 8, 4), "Lamp", (0, 1.84, 0.2))
    return P


BOSSES = [("bee", M_bee), ("ladybug", M_ladybug), ("dragonfly", M_dragonfly), ("sunflower", M_sunflower), ("windmill", M_windmill), ("snail", M_snail)]

if __name__ == "__main__":
    os.makedirs(AB.OUT, exist_ok=True)
    for bid, fn in BOSSES:
        if ONLY and bid not in ONLY: continue
        fn().finish()
    print("DONE")
