# Sky Squad, the christmas village's five bosses (2026-10-10: "bosses for the christmas village"): the christmas express (the gingerbread
# zeppelin until the same evening, "change the first boss"), santa's sleigh, the frost crystal, the snow giant and the grand christmas tree.
# Built from code like the other worlds' bosses (alien_bosses.py lends its Boss class and shapes).
# Run: blender -b -P Tools/blender/christmas_bosses.py -- <out dir> [export] [ids,comma,separated]
# Conventions as alien_bosses.py: +Y nose, +Z up, +X right; "Prop*" spin about the nose, "Rotor*" about up, "Wheel*" fast about the wing axis
# (no blur disc), "Flap*" rock about the nose axis, "Sway*" about the wing axis, "Spin*" turn slowly about up, "Roll*" turn slowly about the
# nose axis, "Cloth" stays still without the outline, "Muzzle" is where his shots leave from.
import bpy, bmesh, math, sys, os, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mathutils import Vector, Matrix
from enemy_planes import loft, sweep, lathe, box, hull, tube, mirror_x, airfoil
import alien_bosses as AB
from alien_bosses import Boss, xf, ball, pipe, cone, bez, torus, sheet, grow, ang

import bmesh
from mathutils.bvhtree import BVHTree
from enemy_planes import loft, sweep, lathe, box, hull, tube, mirror_x, airfoil
from alien_bosses import Boss, xf, ball, pipe, cone, bez, torus, sheet, grow, ang, lerp_keys, spine_frames, body_loft, skin, oriented_ball, frame, sheet_solid, ribbon

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ONLY = argv[2].split(",") if len(argv) > 2 and argv[2] else None


def present(P, c, s, paper, ribbon, name="Present"):
    c = Vector(c)
    P.obj(name, box(tuple(c), s), paper, 0, False)
    P.obj("Ribbon", box(tuple(c), (s[0] * 1.02, s[1] * 0.18, s[2] * 1.02)), ribbon, 0, False)
    P.obj("Ribbon", box(tuple(c), (s[0] * 0.18, s[1] * 1.02, s[2] * 1.02)), ribbon, 0, False)
    for k in (1, -1):
        P.obj("Bow", ball(tuple(c + Vector((k * s[0] * 0.12, 0, s[2] * 0.55))), (s[0] * 0.14, s[1] * 0.08, s[2] * 0.12), 8, 4), ribbon)

def star_mesh(c, r, depth):
    """a fat star: a fan of thin wedges from its centre (a convex hull would round the points off)."""
    c = Vector(c); bm = bmesh.new()
    front = c + Vector((0, depth, 0)); back = c - Vector((0, depth, 0))
    ring = []
    for i in range(10):
        a = math.pi / 2 + i * math.pi / 5; rr = r if i % 2 == 0 else r * 0.45
        ring.append(c + Vector((math.cos(a) * rr, 0, math.sin(a) * rr)))
    vf = bm.verts.new(front); vb = bm.verts.new(back); vr = [bm.verts.new(p) for p in ring]
    for i in range(10):
        j = (i + 1) % 10
        bm.faces.new((vf, vr[i], vr[j])); bm.faces.new((vb, vr[j], vr[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


# ================================================================= 1. the christmas express
def X_train():
    """A flying toy train (2026-10-10, in place of the gingerbread zeppelin: "change the first boss"): a red-and-gold steam locomotive with a
    bright headlight, a cowcatcher, a chimney puffing white smoke and a wreath on its boiler, spinning wheels, red toy wings with gold tips,
    pulling a car piled with presents and a flatcar carrying a little christmas tree, a trail of glowing stardust beneath."""
    P = Boss("train", {"Base": ((0.80, 0.08, 0.08), 0.6), "Belly": ((0.97, 0.97, 0.96), 0.35), "Accent": ((0.10, 0.10, 0.12), 0.6),
                       "Trim": ((0.97, 0.75, 0.22), 0.8), "Glass": ((0.25, 0.50, 0.95), 0.8), "Dark": ((0.05, 0.05, 0.06), 0.5),
                       "Glow": ((1.0, 0.85, 0.45), 0.5), "Metal": ((0.10, 0.48, 0.24), 0.5), "Lamp": ((1.0, 0.92, 0.60), 0.8)})
    # the locomotive: boiler, smokebox, cab
    P.obj("Boiler", loft([(1.55, 0.36, 0.36, 0, 0.45), (0.2, 0.38, 0.38, 0, 0.45)], 18), lambda c, n: "Trim" if (c.y * 2.2) % 1.0 < 0.1 else "Base", 0)
    P.obj("Smokebox", loft([(1.85, 0.34, 0.34, 0, 0.45), (1.55, 0.37, 0.37, 0, 0.45)], 18), "Accent", 0)
    P.obj("Face", lathe([(0.0, 1.88), (0.34, 1.86)], 18, "y", (0, 0, 0.45)), "Accent")
    P.obj("FaceRing", torus(0.3, 0.03, 0.0, 18, 5), "Trim"); P.parts[-1].data.transform(Matrix.Translation((0, 1.89, 0.45)) @ Matrix.Rotation(math.radians(90), 4, "X"))
    P.obj("Headlight", lathe([(0.13, 1.9), (0.13, 2.05), (0.0, 2.05)], 12, "y", (0, 0, 0.92)), "Trim")
    P.obj("Lamp", ball((0, 2.06, 0.92), (0.1, 0.03, 0.1), 10, 5), "Lamp")
    P.obj("Chimney", lathe([(0.1, 0.8), (0.12, 1.1), (0.2, 1.25), (0.2, 1.32), (0.0, 1.32)], 14, "z", (0, 1.45, 0)), lambda c, n: "Trim" if c.z > 1.22 else "Accent")
    P.obj("Dome", ball((0, 0.9, 0.82), (0.14, 0.16, 0.14), 12, 6), "Trim")
    for k, z in enumerate((1.5, 1.75, 2.05)):   # puffs of smoke
        P.obj("Smoke", ball((0.05 * k, 1.45 - 0.25 * k, z), (0.18 + 0.06 * k, 0.18 + 0.06 * k, 0.15 + 0.05 * k), 10, 5), "Belly", 1)
    P.obj("Wreath", torus(0.2, 0.06, 0.0, 16, 6), "Metal"); P.parts[-1].data.transform(Matrix.Translation((0, 1.91, 0.45)) @ Matrix.Rotation(math.radians(90), 4, "X"))
    P.obj("WreathBow", ball((0, 1.93, 0.28), (0.08, 0.03, 0.06), 8, 4), "Base")
    P.obj("Cab", box((0, -0.05, 0.75), (0.95, 0.65, 0.9)), lambda c, n: "Trim" if n.z > 0.5 else "Base", 0, False)
    P.obj("CabRoof", box((0, -0.05, 1.23), (1.1, 0.8, 0.07)), "Accent", 0, False)
    for s in (1, -1):
        P.obj("CabWindow", box((s * 0.48, -0.05, 0.92), (0.02, 0.36, 0.3)), "Lamp", 0, False)
        P.obj("FrontWindow", box((s * 0.24, 0.28, 0.98), (0.26, 0.02, 0.22)), "Lamp", 0, False)
        P.obj("Rail", box((s * 0.42, 0.95, 0.15), (0.06, 2.3, 0.08)), "Trim", 0, False)
    P.obj("Frame", box((0, 0.85, 0.08), (0.75, 2.4, 0.16)), "Accent", 0, False)
    P.obj("Catcher", hull([(-0.4, 1.95, 0.12), (0.4, 1.95, 0.12), (0, 2.35, -0.15), (-0.4, 1.95, -0.15), (0.4, 1.95, -0.15)]),
          lambda c, n: "Trim" if (c.x * 8) % 1.0 < 0.3 else "Base", 0, False)
    # the wheels, turning
    for s in (1, -1):
        for k, y in enumerate((1.45, 0.85, 0.25)):
            r = 0.26 if k else 0.2
            hub = (s * 0.45, y, 0.0 + (0.0 if k else -0.06))
            w = lathe([(r * 0.3, -0.05), (r, -0.05), (r, 0.05), (r * 0.3, 0.05)], 16, "x", hub)
            P.part("Wheel%d%d" % (k, 1 if s > 0 else 0), w, lambda c, n: "Trim" if abs(n.x) > 0.6 else "Base", hub, 0, False)
            P.part("Wheel%d%d" % (k, 1 if s > 0 else 0), box(hub, (0.03, r * 1.7, 0.05)), "Trim", hub, 0, False)
        P.obj("Rod", box((s * 0.52, 0.85, 0.0), (0.03, 1.25, 0.05)), "Trim", 0, False)
        # the toy wings
        P.obj("Wing", hull([(s * 0.4, 0.75, 0.45), (s * 0.4, -0.05, 0.45), (s * 1.75, 0.35, 0.7), (s * 1.8, 0.05, 0.68), (s * 0.4, 0.4, 0.52), (s * 0.4, 0.4, 0.38)]),
              lambda c, n: "Trim" if abs(c.x) > 1.45 else ("Belly" if n.z < -0.3 else "Base"), 0, False)
        P.obj("WingStar", ball((s * 1.2, 0.33, 0.66), (0.09, 0.09, 0.03), 8, 3), "Trim")
    # the present car and the tree car
    P.obj("Car", box((0, -1.05, 0.4), (0.9, 1.05, 0.55)), lambda c, n: "Metal" if (c.z > 0.6 or n.z > 0.5) else "Base", 0, False)
    P.obj("Coupler", box((0, -0.45, 0.12), (0.12, 0.3, 0.08)), "Accent", 0, False)
    present(P, (-0.18, -0.85, 0.82), (0.32, 0.32, 0.3), "Base", "Trim")
    present(P, (0.2, -1.2, 0.8), (0.3, 0.3, 0.26), "Glass", "Belly")
    present(P, (0.0, -1.1, 1.08), (0.24, 0.24, 0.22), "Trim", "Base")
    P.obj("Flatcar", box((0, -2.1, 0.12), (0.85, 0.85, 0.12)), "Accent", 0, False)
    P.obj("Coupler", box((0, -1.65, 0.12), (0.12, 0.3, 0.08)), "Accent", 0, False)
    for (z, r, h) in ((0.2, 0.38, 0.4), (0.48, 0.3, 0.35), (0.72, 0.2, 0.3)):
        P.obj("Tree", lathe([(0.0, z), (r, z), (0.0, z + h)], 14, "z", (0, -2.1, 0)), "Metal", 1)
    P.obj("TreeStar", ball((0, -2.1, 1.07), (0.07, 0.03, 0.07), 6, 3), "Trim")
    for k in range(8):
        a = k * 2.4; z = 0.3 + 0.07 * k; r = 0.33 - 0.03 * k
        P.obj("Light", ball((math.cos(a) * r, -2.1 + math.sin(a) * r, z), (0.035, 0.035, 0.035), 6, 3), "Lamp" if k % 2 else "Base")
    for s in (1, -1):
        for k, y in enumerate((-0.75, -1.35, -1.85, -2.35)):
            P.part("Wheel%d%d" % (3 + k, 1 if s > 0 else 0), lathe([(0.05, -0.04), (0.17, -0.04), (0.17, 0.04), (0.05, 0.04)], 12, "x", (s * 0.42, y, -0.02)),
                   "Accent", (s * 0.42, y, -0.02), 0, False)
    # the stardust trail
    for k in range(9):
        P.obj("Stardust", ball((0.15 * math.sin(k * 1.7), -0.5 - k * 0.32, -0.35 - 0.04 * k), (0.07 - 0.005 * k, 0.07 - 0.005 * k, 0.07 - 0.005 * k), 6, 3), "Glow")
    P.part("Muzzle", ball((0, 2.08, 0.92), (0.07, 0.03, 0.07), 8, 4), "Lamp", (0, 2.08, 0.92))
    return P


# ================================================================= 2. santa's sleigh
def speckle_sl(c):
    v = math.sin(c.x * 12.9898 + c.y * 78.233 + c.z * 37.719) * 43758.5453
    return v - math.floor(v)


# ================================================================= 3. the frost crystal
def X_crystal():
    """A giant snowflake of living ice facing the player and turning slowly: a glowing hexagonal heart with two bright eyes, six arms
    branching into crystal fronds, a crystal at every tip, and a ring of frost orbs round it."""
    P = Boss("crystal", {"Base": ((0.72, 0.88, 1.0), 0.9), "Belly": ((0.96, 0.98, 1.0), 0.6), "Accent": ((0.40, 0.65, 0.95), 0.85),
                         "Trim": ((0.80, 0.85, 0.92), 0.8), "Glass": ((0.55, 0.82, 1.0), 0.95), "Dark": ((0.05, 0.08, 0.15), 0.8),
                         "Glow": ((0.60, 0.95, 1.0), 0.5), "Metal": ((0.6, 0.7, 0.8), 0.7), "Lamp": ((0.85, 1.0, 1.0), 0.8)})
    C = Vector((0, 0, 0))
    def arm_bm(a, L):
        d = Vector((math.cos(a), 0, math.sin(a))); side = Vector((-math.sin(a), 0, math.cos(a)))
        parts = [box(tuple(C + d * (L * 0.5)), (L, 0.14, 0.14), Matrix.Rotation(-a, 3, "Y"))]
        for k, t in enumerate((0.38, 0.62, 0.82)):
            base = C + d * (L * t); bl = 0.5 - 0.12 * k
            for sg in (1, -1):
                tip = base + (d * 0.6 + side * sg * 0.8).normalized() * bl
                parts.append(pipe([base, tip], [0.06, 0.02], 5))
        return parts
    for i in range(6):
        a = math.pi / 2 + i * math.pi / 3
        for bm in arm_bm(a, 1.75):
            P.part("RollFlake", bm, lambda c, n: "Base" if abs(n.y) > 0.6 else "Accent", (0, 0, 0), 0, False)
        d = Vector((math.cos(a), 0, math.sin(a)))
        tipc = d * 1.85
        P.part("RollFlake", hull([tuple(tipc + d * 0.25), tuple(tipc - d * 0.12), tuple(tipc + Vector((-d.z, 0, d.x)) * 0.13), tuple(tipc - Vector((-d.z, 0, d.x)) * 0.13),
                                   tuple(tipc + Vector((0, 0.12, 0))), tuple(tipc - Vector((0, 0.12, 0)))]), "Glass", (0, 0, 0), 0, False)
    hexagon = [Vector((math.cos(i * math.pi / 3) * 0.55, y, math.sin(i * math.pi / 3) * 0.55)) for i in range(6) for y in (-0.2, 0.2)]
    P.part("RollFlake", hull([tuple(p) for p in hexagon]), "Glass", (0, 0, 0), 0, False)
    P.obj("Heart", ball((0, 0.15, 0), (0.4, 0.14, 0.4), 16, 8), "Glow")
    for s in (1, -1):
        P.obj("Eye", ball((s * 0.15, 0.3, 0.06), (0.07, 0.03, 0.1), 8, 4), "Dark")
        P.obj("EyeGlint", ball((s * 0.13, 0.32, 0.11), (0.025, 0.012, 0.03), 6, 3), "Lamp")
    for k in range(10):   # the ring of frost orbs
        a = 2 * math.pi * k / 10
        P.part("SpinOrbs", ball((math.cos(a) * 2.3, math.sin(a) * 0.5, math.sin(a) * 0.0 + 0.0 + (0.25 if k % 2 else -0.25)), (0.11, 0.11, 0.11), 8, 4), "Glow" if k % 2 else "Belly", (0, 0, 0))
    P.part("Muzzle", ball((0, 0.32, -0.12), (0.07, 0.03, 0.05), 8, 4), "Lamp", (0, 0.32, -0.12))
    return P


# ================================================================= 4. the snow giant
def X_tree():
    """The last boss: a towering christmas tree floating over a ring of presents - green tiers wound with a golden garland, red, gold and blue
    baubles, warm lights, a great glowing star turning on top, and baubles circling it."""
    P = Boss("tree", {"Base": ((0.07, 0.36, 0.17), 0.35), "Belly": ((0.97, 0.97, 0.96), 0.4), "Accent": ((0.85, 0.08, 0.10), 0.75),
                      "Trim": ((0.98, 0.76, 0.22), 0.8), "Glass": ((0.25, 0.50, 0.95), 0.9), "Dark": ((0.30, 0.18, 0.08), 0.3),
                      "Glow": ((1.0, 0.85, 0.35), 0.5), "Metal": ((0.12, 0.50, 0.26), 0.5), "Lamp": ((1.0, 0.70, 0.30), 0.8)})
    tiers = [(-0.2, 1.35, 1.0), (0.55, 1.1, 0.9), (1.2, 0.85, 0.85), (1.8, 0.6, 0.75), (2.3, 0.38, 0.6)]
    for (z, r, h) in tiers:
        P.obj("Tier", lathe([(0.0, z), (r, z), (r * 0.92, z + 0.08), (0.0, z + h)], 24, "z"), lambda c, n: "Metal" if n.z < -0.3 else "Base", 1)
    P.obj("Trunk", pipe([(0, 0, -0.75), (0, 0, -0.15)], [0.22, 0.2], 10), "Dark")
    # the garland: a gold spiral down the tiers
    sp = []
    for i in range(80):
        t = i / 79; z = 2.75 - t * 2.95; r = 0.25 + t * 1.15
        a = t * 4.5 * 2 * math.pi
        sp.append(Vector((math.cos(a) * r, math.sin(a) * r, z)))
    P.obj("Garland", pipe(sp, [0.045] * len(sp), 6), "Trim")
    rng = random.Random(3)
    for k in range(34):   # baubles and lights
        t = rng.random(); z = 2.6 - t * 2.7; r = 0.3 + t * 1.05
        a = rng.uniform(0, 2 * math.pi)
        p = (math.cos(a) * r, math.sin(a) * r, z)
        if k % 3 == 2: P.obj("Light", ball(p, (0.05, 0.05, 0.05), 6, 3), "Lamp")
        else: P.obj("Bauble", ball(p, (0.1, 0.1, 0.1), 10, 5), ("Accent", "Trim", "Glass", "Belly")[k % 4])
    # the star on top, turning
    P.part("SpinStar", star_mesh((0, 0, 3.15), 0.42, 0.1), "Glow", (0, 0, 3.15), 0, False)
    P.obj("StarStem", pipe([(0, 0, 2.85), (0, 0, 2.95)], [0.05, 0.05], 6), "Trim")
    # the presents on a snowy platform beneath
    P.obj("Platform", lathe([(0.0, -0.95), (1.25, -0.95), (1.32, -0.85), (1.2, -0.75), (0.0, -0.75)], 24, "z"), "Belly")
    for k in range(7):
        a = 2 * math.pi * k / 7 + 0.3; r = 0.85
        w = 0.28 + 0.06 * (k % 3)
        present(P, (math.cos(a) * r, math.sin(a) * r, -0.75 + w * 0.5), (w, w, w), ("Accent", "Metal", "Glass", "Trim")[k % 4], ("Trim", "Belly", "Trim", "Accent")[k % 4])
    for k in range(12):   # baubles circling it
        a = 2 * math.pi * k / 12
        P.part("SpinBaubles", ball((math.cos(a) * 1.9, math.sin(a) * 1.9, 0.9 + 0.35 * math.sin(a * 2)), (0.12, 0.12, 0.12), 8, 4), ("Accent", "Trim", "Glass")[k % 3], (0, 0, 0.9))
    P.part("Muzzle", ball((0, 1.05, 0.5), (0.08, 0.04, 0.08), 8, 4), "Glow", (0, 1.05, 0.5))
    return P



# ================================================================= 2026-10-11: shared face helpers for the new bosses
def eye(P, c, r, iris, glint=True, pupil="Dark", white="Belly"):
    """an eye on a face looking toward +Y: the white, a coloured iris, a pupil and a glint."""
    c = Vector(c)
    P.obj("EyeWhite", ball(tuple(c), (r, r * 0.55, r * 1.1), 12, 6), white)
    P.obj("Iris", ball(tuple(c + Vector((0, r * 0.42, -r * 0.05))), (r * 0.62, r * 0.25, r * 0.68), 10, 5), iris)
    P.obj("Pupil", ball(tuple(c + Vector((0, r * 0.6, -r * 0.05))), (r * 0.3, r * 0.12, r * 0.36), 8, 4), pupil)
    if glint: P.obj("Glint", ball(tuple(c + Vector((r * 0.22, r * 0.68, r * 0.25))), (r * 0.14, r * 0.05, r * 0.14), 6, 3), "Belly")

def bar(a, b, w, t, up=(0, 1, 0)):
    """a squared-off bar between two points, w wide (across, in the face plane) and t thick (toward +Y)."""
    a, b = Vector(a), Vector(b); d = (b - a).normalized(); n = Vector(up)
    if abs(d.dot(n)) > 0.95: n = Vector((0, 0, 1))
    s = d.cross(n).normalized() * w * 0.5; f = n * t * 0.5
    pts = [p + ds + df for p in (a, b) for ds in (s, -s) for df in (f, -f)]
    return hull([tuple(p) for p in pts])


# ================================================================= 1 (new). the nutcracker king

# ================================================================= nutcracker (2026-10-13 remake)
NC_BAUBLE = (0.0, 0.0, 3.62)   # the bauble's centre
NC_BR = 1.1                    # and radius
NC_MUZZLE = (0.0, 0.38, 0.98)   # his shots leave from between his teeth


def nc_sphere_at(z):
    """the radius of the bauble's sphere at height z (0 above or below it)."""
    dz = z - NC_BAUBLE[2]
    return math.sqrt(max(0.0, NC_BR * NC_BR - dz * dz))

def nc_flake(c, n, size, w=0.03):
    """a six-armed snowflake lying on a surface at c with normal n: six arms, a pair of side branches on each, a hexagon at the middle."""
    c, n = Vector(c), Vector(n).normalized()
    u = n.cross(Vector((0, 0, 1)) if abs(n.z) < 0.9 else Vector((1, 0, 0))).normalized(); v = n.cross(u).normalized()
    bm = bmesh.new()
    def add(a, b, ww):
        part = bar(a, b, ww, 0.025, tuple(n)); me = bpy.data.meshes.new("t"); part.to_mesh(me); part.free(); bm.from_mesh(me); bpy.data.meshes.remove(me)
    for k in range(6):
        a = math.pi / 2 + k * math.pi / 3
        d = u * math.cos(a) + v * math.sin(a); s = u * math.cos(a + math.pi / 2) + v * math.sin(a + math.pi / 2)
        add(c, c + d * size, w)
        for t, L in ((0.45, 0.32), (0.72, 0.22)):   # two pairs of branches along each arm, raked outward
            p = c + d * size * t
            for sg in (1, -1): add(p, p + (d * 0.6 + s * sg * 0.8).normalized() * size * L, w * 0.8)
    return bm

def nc_drum_cords(r, z0, z1, n):
    """the drum's tensioning cords: a zigzag between the hoops, n V's round it."""
    pts = []
    for i in range(2 * n + 1):
        a = 2 * math.pi * i / (2 * n)
        z = z0 if i % 2 == 0 else z1
        pts.append(Vector((math.cos(a) * r, math.sin(a) * r, z)))
    return pts


def X_nutcracker():
    """The NUTCRACKER KING (2026-10-13, remade: "same as the alien bosses - realistic details, scarier, keep the cartoon shape"): the same
    towering toy soldier king with the snapping jaw and the sabre, now built like a real carved wooden nutcracker. Every part of him is turned
    on a lathe and painted: a body of stacked turnings - the coat's skirt, a belt groove, the chest and a bead at the neck - and the red
    paint worn through to the bare wood at the edges that get handled, at the hem and the collar. A red guard's coat with three rows of gold
    frogging across the chest, gold buttons evenly down both sides, a green sash, a black belt with a gold buckle, gold epaulettes with
    bullion fringes. The head is a block of pale wood: a big turned nose, painted rosy cheeks, painted eyes that glare - white, a small black
    pupil, a black lid line cutting the top of each eye at an angle and a red rim under it - under bushy white rabbit-fur brows that slant
    down to the middle; a white fur moustache, and white hair down the sides and the back. His mouth is the real nutcracker's: a square block
    opening full of big white teeth, and the jaw is a hinged block of its own, more big teeth on it, a long white fur beard hanging from it,
    and its lever running down his back - it drops and snaps shut (SwayJaw). On his head a tall black shako crowned with gold points, gold
    bands at the brim and the top, a gold sunburst badge with a red jewel at the front and a white plume tipped red. His right arm swings a
    sabre with a gold knuckle-bow (SwayArm); his left hand grips one of the ropes.
    He flies in a CHRISTMAS-BAUBLE HOT-AIR BALLOON: above him hangs a huge glass christmas ornament - glossy red, two gold painted bands round
    its middle with a ring of white snowflakes between them, a thin gold band near the top and one near the bottom, a fluted silver cap with
    crimped prongs and the wire loop on top, and an open mouth underneath ringed in gold, glowing from the heat inside. It turns slowly
    (SpinBauble). A gold load ring hugs it below its middle, and four ropes run from the ring down to his basket - a toy drum: a red shell
    with gold hoops, white cords zigzagging between them through gold lugs, and two drumsticks crossed on its side. He stands in the drum to
    his knees; between his head and the bauble a little brass burner hangs from the load ring, its flame licking up into the mouth."""
    P = Boss("nutcracker", {"Base": ((0.72, 0.03, 0.05), 0.6), "Belly": ((0.97, 0.96, 0.93), 0.3), "Accent": ((0.88, 0.68, 0.46), 0.35),
                            "Trim": ((0.98, 0.74, 0.20), 0.85), "Glass": ((0.04, 0.36, 0.16), 0.5), "Dark": ((0.035, 0.03, 0.035), 0.55),
                            "Glow": ((1.0, 0.82, 0.35), 0.5), "Metal": ((0.82, 0.84, 0.88), 0.9), "Lamp": ((1.0, 0.45, 0.10), 0.8)})

    # ---- the drum he stands in: a red shell, gold hoops, white cords through gold lugs, the open top dark inside
    DZ0, DZ1, DR = -1.8, -1.04, 0.7
    P.obj("Drum", lathe([(0.0, DZ0 + 0.06), (DR - 0.02, DZ0), (DR, DZ0 + 0.04), (DR, DZ1 - 0.02), (DR - 0.04, DZ1), (DR - 0.06, DZ1 - 0.04),
                         (DR - 0.06, DZ0 + 0.12), (0.0, DZ0 + 0.12)], 40, "z"),
          lambda c, n: "Dark" if math.hypot(c.x, c.y) < DR - 0.03 else "Base")
    for z in (DZ0 + 0.05, DZ1 - 0.05):
        P.obj("Hoop", torus(DR + 0.01, 0.045, z, 40, 8), "Trim")
    cords = nc_drum_cords(DR + 0.035, DZ0 + 0.13, DZ1 - 0.13, 9)
    for a, b in zip(cords, cords[1:]):
        P.obj("Cord", pipe([a, b], [0.018, 0.018], 5, False), "Belly")
    for i in range(0, len(cords) - 1):
        p = cords[i]; o = Vector((p.x, p.y, 0)).normalized()
        P.obj("Lug", box(tuple(p + o * 0.01 + Vector((0, 0, 0.03 if i % 2 == 0 else -0.03))), (0.06, 0.06, 0.06)), "Trim", 0, False)
    for s in (1, -1):   # two drumsticks crossed on its right side, their round tips red
        a = Vector((DR + 0.07, 0.42 * s, DZ0 + 0.12)); b = Vector((DR + 0.07, -0.38 * s, DZ1 + 0.05))
        P.obj("Stick", pipe([a, b], [0.028, 0.03], 8), "Accent")
        P.obj("StickTip", ball(tuple(b + (b - a).normalized() * 0.03), (0.055, 0.055, 0.055), 10, 5), "Base")

    # ---- legs: white trousers into the drum (his black boots stand inside it)
    for s in (1, -1):
        x = s * 0.22
        P.obj("Leg", pipe([(x, 0, -0.45), (x, 0, -1.4)], [0.17, 0.15], 12), "Belly")
        P.obj("Boot", pipe([(x, 0.02, -1.25), (x, 0.02, -1.62)], [0.17, 0.18], 12), "Dark")

    # ---- the body: stacked turnings, red paint worn to the wood at the handled edges
    def coat_paint(c, n):
        a = (math.atan2(c.y, c.x) / (2 * math.pi) * 14) % 1.0
        if c.z < -0.5: return "Accent" if a < 0.18 and n.z < 0.5 else "Belly"           # the white skirt lining, worn at the hem
        if c.z > 0.66 and a < 0.12: return "Accent"                                      # worn at the collar
        return "Base"
    P.obj("Coat", lathe([(0.0, -0.56), (0.6, -0.56), (0.62, -0.5), (0.56, -0.25), (0.5, -0.14), (0.47, -0.2), (0.49, -0.1), (0.5, 0.1),
                         (0.54, 0.45), (0.5, 0.62), (0.42, 0.7), (0.0, 0.73)], 32, "z"), coat_paint, 1)
    for k in range(7):   # the paint chipped to the bare wood along the front of the hem, where hands grab him
        a = math.radians(-60 + 20 * k)
        P.obj("Chip", ball((math.sin(a) * 0.61, math.cos(a) * 0.61, -0.47 + 0.02 * (k % 2)), (0.05 + 0.012 * (k % 3), 0.02, 0.03), 8, 3), "Accent")
    P.obj("Belt", torus(0.49, 0.055, -0.17, 32, 6), "Dark")
    P.obj("Buckle", box((0, 0.53, -0.17), (0.18, 0.05, 0.13)), "Trim", 0, False)
    P.obj("BuckleIn", box((0, 0.56, -0.17), (0.1, 0.03, 0.06)), "Dark", 0, False)
    for i, z in enumerate((0.06, 0.22, 0.38)):     # gold frogging: three bars, a loop at each end, a button outside each loop
        r = 0.5 + 0.04 * i * 0.9
        w = 0.24 - 0.02 * i
        P.obj("Frog", bar((-w, r + 0.01, z), (w, r + 0.01, z), 0.04, 0.035), "Trim", 0, False)
        for s in (1, -1):
            P.obj("FrogLoop", xf(torus(0.04, 0.012, 0.0, 12, 4), Matrix.Rotation(math.radians(90), 3, "X"), (s * (w + 0.03), r + 0.01, z)), "Trim")
            P.obj("Button", ball((s * (w + 0.12), r - 0.03, z), (0.045, 0.03, 0.045), 8, 4), "Trim")
    sash = []
    for i in range(9):   # a green sash from the left shoulder across the chest to the right hip, lying on the coat
        t = i / 8; a = math.radians(-50 + 100 * t); z = 0.62 - 0.74 * t
        r = (0.46 if z > 0.5 else 0.53 if z > 0.1 else 0.52) + 0.035
        sash.append(Vector((math.sin(a) * r, math.cos(a) * r, z)))
    P.obj("Sash", pipe(sash, [0.055] * 9, 8, False), "Glass")
    P.obj("NeckBead", torus(0.3, 0.06, 0.74, 24, 6), "Trim")
    for s in (1, -1):    # epaulettes with bullion fringes, evenly round the outer edge
        P.obj("Epaulette", ball((s * 0.52, 0.0, 0.66), (0.2, 0.18, 0.07), 14, 5), "Trim")
        for k in range(9):
            a = math.pi * k / 8 - math.pi / 2
            o = Vector((s * math.cos(a), math.sin(a) * 0.9, 0))
            p0 = Vector((s * 0.52, 0, 0.63)) + o * 0.18
            P.obj("Fringe", pipe([p0, p0 + o * 0.03 + Vector((0, 0, -0.13))], [0.022, 0.02], 5), "Trim")

    # ---- the left arm: up to the front-left rope, the white glove gripping it
    RL = Vector((-0.45, 0.45, 0.32))
    P.obj("ArmL", pipe([(-0.56, 0.0, 0.58), (-0.76, 0.16, 0.3), (-0.55, 0.4, 0.32)], [0.13, 0.11, 0.1], 10), "Base")
    P.obj("Cuff", xf(torus(0.1, 0.03, 0.0, 14, 4), Matrix.Rotation(math.radians(75), 3, "Y"), (-0.6, 0.36, 0.32)), "Trim")
    P.obj("Glove", ball(tuple(RL), (0.1, 0.1, 0.11), 10, 5), "Belly")

    # ---- the right arm swings the sabre (gold knuckle-bow, a curved steel blade)
    sh = (0.56, 0.0, 0.58)
    hand = Vector((0.98, 0.32, 1.12))
    P.part("SwayArm", pipe([sh, (0.86, 0.06, 0.78), hand - Vector((0.03, 0.03, 0.06))], [0.13, 0.11, 0.1], 10), "Base", sh)
    P.part("SwayArm", xf(torus(0.1, 0.03, 0.0, 14, 4), Matrix.Rotation(math.radians(40), 3, "Y"), tuple(hand - Vector((0.06, 0.03, 0.1)))), "Trim", sh)
    P.part("SwayArm", ball(tuple(hand), (0.1, 0.1, 0.1), 10, 5), "Belly", sh)
    blade = bez(hand + Vector((0.02, 0.02, 0.12)), hand + Vector((0.15, 0.06, 0.6)), hand + Vector((0.3, 0.12, 1.0)), hand + Vector((0.5, 0.2, 1.3)), 8)
    P.part("SwayArm", pipe(blade, [0.04, 0.04, 0.038, 0.035, 0.032, 0.028, 0.022, 0.014, 0.0], 6), "Metal", sh)
    P.part("SwayArm", bar(hand + Vector((-0.12, 0, 0.12)), hand + Vector((0.14, 0, 0.12)), 0.04, 0.05), "Trim", sh)
    P.part("SwayArm", pipe(bez(hand + Vector((0.13, 0.02, 0.12)), hand + Vector((0.16, 0.12, -0.02)), hand + Vector((0.06, 0.14, -0.14)), hand + Vector((-0.04, 0.04, -0.12)), 6),
                       [0.018] * 7, 5, False), "Trim", sh)
    P.part("SwayArm", ball(tuple(hand + Vector((-0.02, 0.0, -0.14))), (0.045, 0.045, 0.045), 8, 4), "Trim", sh)

    # ---- the head: a turned block of pale wood
    P.obj("Head", lathe([(0.0, 0.76), (0.34, 0.78), (0.4, 0.84), (0.41, 1.0), (0.41, 1.52), (0.38, 1.58), (0.0, 1.6)], 28, "z"),
          "Accent", 1)
    for s in (1, -1):
        e = Vector((s * 0.16, 0.39, 1.3))
        P.obj("EyeWhite", ball(tuple(e), (0.095, 0.03, 0.075), 12, 6), "Belly")
        P.obj("Pupil", ball(tuple(e + Vector((-s * 0.012, 0.022, -0.01))), (0.03, 0.015, 0.035), 8, 4), "Dark")
        P.obj("Glint", ball(tuple(e + Vector((-s * 0.0, 0.032, 0.005))), (0.01, 0.006, 0.01), 6, 3), "Belly")
        P.obj("Lid", bar(e + Vector((-s * 0.11, 0.035, 0.0)), e + Vector((s * 0.11, 0.035, 0.07)), 0.035, 0.02, (0, 1, 0)), "Dark", 0, False)  # the lid line cuts the top of the eye, low at the middle
        P.obj("UnderRim", bar(e + Vector((-s * 0.08, 0.03, -0.07)), e + Vector((s * 0.08, 0.03, -0.06)), 0.016, 0.015, (0, 1, 0)), "Base", 0, False)
        # bushy rabbit-fur brows slanting down to the middle: tufts in a row
        for k in range(6):
            t = k / 5
            p = Vector((s * (0.05 + 0.27 * t), 0.4 - 0.05 * t * t, 1.4 + 0.12 * t))
            P.obj("Brow", ball(tuple(p), (0.06, 0.05, 0.05 - 0.008 * t), 8, 4), "Belly")
        P.obj("Cheek", ball((s * 0.27, 0.36, 1.12), (0.075, 0.03, 0.055), 10, 4), "Base")
        P.obj("Moustache", pipe(bez((0, 0.5, 1.09), (s * 0.12, 0.53, 1.11), (s * 0.26, 0.48, 1.06), (s * 0.36, 0.38, 1.14), 6),
                                [0.065, 0.065, 0.06, 0.05, 0.04, 0.03, 0.015], 10), "Belly")
        for k in range(5):   # white hair hanging down the side and back of his head, in even locks
            a = math.radians(s * (70 + 25 * k))
            p0 = Vector((math.sin(a) * 0.4, math.cos(a) * 0.4, 1.5))
            P.obj("Hair", pipe([p0, p0 * 1.08 + Vector((0, 0, -0.32)), Vector((p0.x * 1.12, p0.y * 1.12, 0.92))], [0.07, 0.065, 0.02], 7), "Belly")
    P.obj("Nose", lathe([(0.0, 0.0), (0.07, 0.02), (0.085, 0.12), (0.06, 0.2), (0.0, 0.22)], 12, "y", (0, 0.38, 1.21)), "Accent")
    # the square block mouth: dark inside, a row of big upper teeth
    P.obj("Mouth", box((0, 0.395, 0.99), (0.36, 0.05, 0.13)), "Dark", 0, False)
    for k in range(5):
        P.obj("Tooth", box((-0.14 + k * 0.07, 0.42, 1.02), (0.062, 0.04, 0.07)), "Belly", 0, False)
    # the hinged jaw: a block with big lower teeth, the fur beard, and the lever running down his back - it drops and snaps
    hinge = (0, -0.05, 0.98)
    P.part("SwayJaw", box((0, 0.17, 0.89), (0.4, 0.46, 0.1)), "Accent", hinge, 0, False)
    for k in range(5):
        P.part("SwayJaw", box((-0.14 + k * 0.07, 0.4, 0.955), (0.062, 0.04, 0.06)), "Belly", hinge, 0, False)
    for row, (y, z0, L) in enumerate(((0.4, 0.87, 0.38), (0.33, 0.86, 0.48), (0.22, 0.85, 0.42))):
        for k in range(7):
            x = (k - 3) * 0.058 * (1.0 + 0.15 * row)
            sway = (k - 3) * 0.012
            P.part("SwayJaw", pipe([(x, y, z0), (x * 1.15 + sway, y + 0.05, z0 - L * 0.5), (x * 0.8 + sway * 2, y + 0.02 - 0.04 * row, z0 - L)],
                                   [0.055, 0.045, 0.0], 7), "Belly", hinge)
    P.part("SwayJaw", bar((0, -0.08, 0.92), (0, -0.62, 0.62), 0.09, 0.07), "Accent", hinge, 0, False)
    P.part("SwayJaw", bar((0, -0.62, 0.62), (0, -0.6, -0.1), 0.09, 0.07), "Accent", hinge, 0, False)
    P.part("SwayJaw", ball((0, -0.6, -0.12), (0.075, 0.075, 0.075), 10, 5), "Trim", hinge)   # a gold knob on the lever's end

    # ---- the shako: tall, black, gold points round the crown, gold bands, a sunburst badge, a white plume tipped red
    P.obj("Shako", lathe([(0.0, 1.57), (0.42, 1.57), (0.43, 1.62), (0.46, 2.1), (0.0, 2.1)], 28, "z"), "Dark")
    for z, r in ((1.6, 0.435), (2.08, 0.465)):
        P.obj("ShakoBand", torus(r, 0.03, z, 28, 5), "Trim")
    for k in range(10):
        a = 2 * math.pi * k / 10 + math.pi / 2
        p = Vector((math.cos(a) * 0.45, math.sin(a) * 0.45, 2.08))
        P.obj("CrownPoint", cone(tuple(p), tuple(p + Vector((math.cos(a) * 0.03, math.sin(a) * 0.03, 0.17))), 0.05, 5), "Trim", 0, False)
        P.obj("CrownPearl", ball(tuple(p + Vector((math.cos(a) * 0.035, math.sin(a) * 0.035, 0.19))), (0.028, 0.028, 0.028), 6, 3), "Belly")
    bc = Vector((0, 0.45, 1.84))
    for k in range(12):   # the sunburst badge
        a = 2 * math.pi * k / 12
        L = 0.15 if k % 2 == 0 else 0.1
        P.obj("Badge", bar(bc, bc + Vector((math.cos(a) * L, 0, math.sin(a) * L)), 0.035, 0.02), "Trim", 0, False)
    P.obj("BadgeJewel", ball(tuple(bc + Vector((0, 0.02, 0))), (0.05, 0.03, 0.05), 10, 5), "Base")
    plume = bez((0, 0.38, 2.06), (0, 0.44, 2.22), (0, 0.5, 2.34), (0, 0.6, 2.42), 6)
    P.obj("Plume", pipe(plume, [0.07, 0.085, 0.085, 0.075, 0.06, 0.04, 0.0], 9), lambda c, n: "Base" if c.z > 2.34 else "Belly")

    # ---- the balloon: a glass christmas bauble, turning
    B = Vector(NC_BAUBLE); R = NC_BR
    mouth_r = 0.22
    phi0 = math.asin(mouth_r / R); phi1 = math.pi - math.asin(0.2 / R)
    prof = []
    for i in range(23):
        phi = phi0 + (phi1 - phi0) * i / 22
        prof.append((R * math.sin(phi), -R * math.cos(phi)))
    P.part("SpinBauble", lathe(prof, 48, "z", tuple(B)), "Base", tuple(B), 1)
    P.part("SpinBauble", torus(mouth_r + 0.01, 0.035, B.z - R * math.cos(phi0), 28, 6), "Trim", tuple(B))
    P.part("SpinBauble", ball(tuple(B + Vector((0, 0, -R * math.cos(phi0) + 0.03))), (mouth_r, mouth_r, 0.03), 16, 3), "Lamp", tuple(B))
    for dz, r in ((0.34, 0.036), (-0.34, 0.036), (0.8, 0.02), (-0.8, 0.02)):   # the painted gold bands, two wide round the middle
        P.part("SpinBauble", torus(nc_sphere_at(B.z + dz) + 0.006, r, B.z + dz, 48, 6), "Trim", tuple(B))
    for k in range(8):   # a ring of white snowflakes between the two wide bands
        a = 2 * math.pi * k / 8
        n = Vector((math.cos(a), math.sin(a), 0))
        P.part("SpinBauble", nc_flake(B + n * (R + 0.012), n, 0.24), "Belly", tuple(B))
        # little gold dots between the flakes, on the bands' inner edges
        for dz in (0.22, -0.22):
            a2 = a + math.pi / 8
            n2 = Vector((math.cos(a2), math.sin(a2), 0)); r2 = nc_sphere_at(B.z + dz)
            P.part("SpinBauble", ball(tuple(Vector((n2.x * r2, n2.y * r2, B.z + dz)) + Vector((n2.x, n2.y, dz / R)) * 0.01), (0.03, 0.03, 0.03), 6, 3), "Trim", tuple(B))
    ct = B.z + R * math.cos(math.asin(0.2 / R))   # the cap: fluted silver, crimped prongs, the wire loop
    P.part("SpinBauble", lathe([(0.0, ct + 0.2), (0.17, ct + 0.2), (0.19, ct + 0.16), (0.23, ct - 0.02), (0.0, ct - 0.02)], 24, "z"), "Metal", tuple(B))
    for k in range(12):
        a = 2 * math.pi * k / 12
        o = Vector((math.cos(a), math.sin(a), 0))
        P.part("SpinBauble", cone(tuple(o * 0.22 + Vector((0, 0, ct + 0.0))), tuple(o * 0.3 + Vector((0, 0, ct - 0.1))), 0.035, 4), "Metal", tuple(B), 0, False)
    P.part("SpinBauble", xf(torus(0.13, 0.025, 0.0, 20, 5), Matrix.Rotation(math.radians(90), 3, "X"), (0, 0, ct + 0.32)), "Metal", tuple(B))

    # ---- the load ring hugging the bauble below its middle, four ropes down to the drum, the burner hanging under the mouth
    RZ = B.z - 0.58
    rr = nc_sphere_at(RZ) + 0.04
    P.obj("LoadRing", torus(rr, 0.035, RZ, 40, 6), "Trim")
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        o = Vector((math.cos(a), math.sin(a), 0))
        top = o * rr + Vector((0, 0, RZ)); bot = o * (DR - 0.01) + Vector((0, 0, DZ1 + 0.01))
        P.obj("Rope", pipe([bot, top], [0.022, 0.022], 6), "Accent")
        P.obj("Shackle", xf(torus(0.05, 0.016, 0.0, 12, 4), Matrix.Rotation(math.radians(90), 3, "X") @ Matrix.Rotation(-a, 3, "Z") if False else Matrix.Rotation(a, 3, "Z") @ Matrix.Rotation(math.radians(90), 3, "X"), tuple(top - Vector((0, 0, 0.06)))), "Trim")
        P.obj("Strut", pipe([top, Vector((0, 0, 2.5)) + o * 0.13], [0.018, 0.016], 5), "Trim")
    P.obj("Burner", lathe([(0.0, 2.36), (0.1, 2.37), (0.15, 2.46), (0.14, 2.52), (0.08, 2.5), (0.0, 2.5)], 16, "z"), "Trim")
    P.obj("BurnerCoil", torus(0.12, 0.02, 2.44, 16, 4), "Dark")
    P.obj("Flame", lathe([(0.0, 2.5), (0.09, 2.54), (0.07, 2.66), (0.03, 2.78), (0.0, 2.84)], 12, "z"), "Lamp")
    P.obj("FlameCore", lathe([(0.0, 2.5), (0.05, 2.53), (0.03, 2.65), (0.0, 2.7)], 10, "z"), "Glow")

    P.part("Muzzle", ball(NC_MUZZLE, (0.045, 0.03, 0.035), 8, 4), "Glow", NC_MUZZLE)
    return P



# ================================================================= sleigh (2026-10-13 remake)
# Santa's sleigh, remade 2026-10-13 (scratch file; merged later into christmas_bosses.py)

# the tub's side profile (y toward the reindeer): its top edge, its bottom and its half width along the length
SL_TOP = [(-1.62, 0.6), (-1.5, 0.74), (-1.3, 0.8), (-1.04, 0.8), (-0.96, 0.66), (-0.3, 0.64), (-0.12, 0.52), (0.45, 0.5), (0.6, 0.6), (0.68, 0.64)]
SL_BOT = [(-1.62, 0.3), (-1.5, 0.13), (-1.3, 0.06), (0.4, 0.06), (0.6, 0.13), (0.68, 0.32)]
SL_HW = [(-1.62, 0.42), (-1.45, 0.58), (-0.6, 0.62), (0.2, 0.58), (0.6, 0.48), (0.68, 0.4)]
SL_SQ = 3.0

def sl_tub(step=0.055, seg=32):
    rows = []; y = -1.62
    while y < 0.68 + 1e-6:
        t, b = lerp_keys(y, SL_TOP), lerp_keys(y, SL_BOT)
        rows.append((y, lerp_keys(y, SL_HW), (t - b) * 0.5, 0.0, (t + b) * 0.5)); y += step
    return loft(rows, seg, True, True, SL_SQ)

def sl_surf_x(y, z):
    """how far out the tub's side is at (y, z): the superellipse section solved for x."""
    t, b = lerp_keys(y, SL_TOP), lerp_keys(y, SL_BOT)
    v = max(-1.0, min(1.0, (z - (t + b) * 0.5) / max(1e-4, (t - b) * 0.5)))
    sa = abs(v) ** SL_SQ; ca = math.sqrt(max(0.0, 1 - sa * sa))
    return lerp_keys(y, SL_HW) * ca ** (1.0 / SL_SQ)

def sl_xribbon(path, hw, th, seg=16):
    """a strip lying across x along a path in the y-z plane: superellipse sections hw[i] across and th[i] thick (a scroll, a dash)."""
    pts = [Vector(p) for p in path]; n = len(pts); bm = bmesh.new(); rings = []
    X = Vector((1, 0, 0))
    for i, p in enumerate(pts):
        t = (pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]); t.x = 0; t.normalize()
        nn = X.cross(t)
        ring = []
        for k in range(seg):
            a = 2 * math.pi * k / seg; ca, sa = math.cos(a), math.sin(a)
            u = math.copysign(abs(ca) ** 0.4, ca) * hw[i]; v = math.copysign(abs(sa) ** 0.8, sa) * th[i]
            ring.append(bm.verts.new(p + X * u + nn * v))
        rings.append(ring)
    return skin(bm, rings, seg)

def sl_spiral(c, r0, r1, a0, a1, n):
    """points of a spiral in the y-z plane about c (y, z): radius r0 -> r1 while the angle goes a0 -> a1 (degrees)."""
    out = []
    for i in range(n + 1):
        t = i / n; a = math.radians(a0 + (a1 - a0) * t); r = r0 + (r1 - r0) * t
        out.append(Vector((0, c[0] + math.cos(a) * r, c[1] + math.sin(a) * r)))
    return out

def sl_on_side(s, pts, lift=0.012):
    """points given in (y, z) laid onto the tub's side s (+1 right, -1 left)."""
    return [Vector((s * (sl_surf_x(p.y, p.z) + lift), p.y, p.z)) for p in pts]

def sl_ring(c, rx, ry, r, rot=None, n=28, seg=6):
    """an elliptic ring (a collar, a belt, a fur hem) rx by ry about c in its own x-y plane, turned by rot; the tube keeps its radius r."""
    rot = rot or Matrix.Identity(3); c = Vector(c)
    pts = [c + rot @ Vector((math.cos(2 * math.pi * k / n) * rx, math.sin(2 * math.pi * k / n) * ry, 0)) for k in range(n + 1)]
    pts.append(pts[1])
    bm = pipe(pts, [r] * len(pts), seg, cap=False)
    return bm

def sl_present(P, c, s, paper, ribbon, rot=0.0):
    """a wrapped box: the paper, a ribbon round it both ways, a bow of two loops and two tails on top."""
    c = Vector(c); R = Matrix.Rotation(math.radians(rot), 3, "Z")
    P.obj("Present", box(tuple(c), s, R), paper, 0, False)
    P.obj("Ribbon", box(tuple(c), (s[0] * 1.02, s[1] * 0.16, s[2] * 1.02), R), ribbon, 0, False)
    P.obj("Ribbon", box(tuple(c), (s[0] * 0.16, s[1] * 1.02, s[2] * 1.02), R), ribbon, 0, False)
    top = c + Vector((0, 0, s[2] * 0.5)); k = min(s[0], s[1])
    for sg in (1, -1):
        loop = torus(k * 0.16, k * 0.035, 0.0, 12, 4)
        xf(loop, R @ Matrix.Rotation(math.radians(90), 3, "X") @ Matrix.Scale(1.0, 3), tuple(top + R @ Vector((sg * k * 0.17, 0, k * 0.12))))
        P.obj("Bow", loop, ribbon)
        P.obj("BowTail", pipe([top, top + R @ Vector((sg * k * 0.2, k * 0.25, -0.01)), top + R @ Vector((sg * k * 0.26, k * 0.4, -s[2] * 0.25))], [k * 0.035, k * 0.03, 0.0], 4), ribbon)
    P.obj("Knot", ball(tuple(top + Vector((0, 0, k * 0.04))), (k * 0.07,) * 3, 8, 4), ribbon)

def sl_bell(P, c, r, name="Bell"):
    """a jingle bell: a gold ball with the dark slot across its lower half and a loop on top."""
    c = Vector(c)
    P.obj(name, ball(tuple(c), (r, r, r), 10, 5), "Trim")
    P.obj(name, box(tuple(c + Vector((0, 0, -r * 0.35))), (r * 1.6, r * 0.3, r * 0.22)), "Dark", 0, False)
    P.obj(name, ball(tuple(c + Vector((0, 0, -r * 0.35))), (r * 0.25,) * 3, 6, 3), "Dark")


def sl_grow(P, n0, s0, O, K):
    """everything added to P since it had n0 body pieces and s0 movers scaled by K about O (the movers keep their hinges in place)."""
    O = Vector(O)
    for ob in P.parts[n0:]:
        for v in ob.data.vertices: v.co = O + (v.co - O) * K
    for ob in P.spin[s0:]:
        for v in ob.data.vertices: v.co = v.co * K
        ob.location = O + (Vector(ob.location) - O) * K

def sl_deer(P, O, tag, lead, K=1.3):
    """one reindeer of the pair, built like a real reindeer and leaping in a flying gallop; O is the middle of its body. Returns where its
    bit rings and collar sides are, for the reins and the traces, and the tip of its nose."""
    O = Vector(O); n0, s0 = len(P.parts), len(P.spin)
    def W(p): return O + Vector(p)
    # ---- the body: a thick neck rising to the head, deep chest, short back, round rump
    neck = bez((0, 0.6, 0.4), (0, 0.55, 0.28), (0, 0.44, 0.14), (0, 0.3, 0.08), 7)
    torso = bez((0, 0.3, 0.08), (0, 0.05, 0.07), (0, -0.3, 0.08), (0, -0.5, 0.05), 8)[1:]
    PTS = [W(p) for p in neck + torso] + [W((0, -0.57, 0.04))]
    FR = spine_frames(PTS)
    RX, RZ = [], []
    for i in range(len(neck)):
        u = i / (len(neck) - 1)
        RX.append(lerp_keys(u, [(0, 0.075), (0.5, 0.1), (1, 0.15)])); RZ.append(lerp_keys(u, [(0, 0.085), (0.5, 0.13), (1, 0.2)]))
    for i in range(len(torso)):
        u = (i + 1) / len(torso)
        RX.append(lerp_keys(u, [(0, 0.17), (0.3, 0.18), (0.6, 0.16), (0.85, 0.17), (1, 0.13)]))
        RZ.append(lerp_keys(u, [(0, 0.22), (0.3, 0.21), (0.6, 0.18), (0.85, 0.17), (1, 0.12)]))
    RX.append(0.0); RZ.append(0.0)
    def coat(c, n):
        q = c - O
        if q.y < -0.44 and n.y < -0.25: return "Belly"                      # the white rump patch
        if q.y > 0.36 and q.z > 0.02 and n.z < 0.5: return "Belly"          # the pale neck of a reindeer in winter coat
        if n.z < -0.7 and q.y < 0.2: return "Belly" if q.y < -0.3 else "Base"
        return "Base"
    P.obj("Deer", body_loft(PTS, RX, RZ, FR, 20, 1.2, 0.9), coat, 0)
    P.obj("Tail", pipe([W((0, -0.55, 0.12)), W((0, -0.62, 0.11)), W((0, -0.66, 0.06))], [0.04, 0.035, 0.0], 6), "Belly")
    # the long white mane hanging from the throat in even staggered rows
    for i in range(1, len(neck) - 1):
        p = PTS[i]; t, side, up = FR[i]
        for j in range(-2, 3):
            if (i + j) % 2: continue
            a = j * 0.35
            q = p - up * RZ[i] * math.cos(a) * 0.9 + side * RX[i] * math.sin(a) * 0.9
            down = (Vector((0, 0.2, -1)) + side * math.sin(a) * 0.4).normalized()
            L = 0.08 + 0.04 * (1 - abs(j) / 2)
            lock = pipe([q - down * 0.02, q + down * L * 0.5, q + down * L * 0.85, q + down * L + Vector((0, -0.02, 0))], [0.032, 0.026, 0.014, 0.0], 6)
            fl = side.cross(down).normalized()
            for v in lock.verts:
                d = v.co - q; v.co = q + d - fl * d.dot(fl) * 0.55
            P.obj("Mane", lock, "Belly", 0)

    # ---- the head: broad, with the blunt furred muzzle of a reindeer; tipped down from the poll
    HB = W((0, 0.62, 0.43)); HR = Matrix.Rotation(math.radians(-22), 3, "X") @ Matrix.Scale(1.15, 3)
    def H(bm): return xf(bm, HR, tuple(HB))
    def hp(p): return HB + HR @ Vector(p)
    UP = [(-0.06, 0.068, 0.075, 0, 0.0), (0.02, 0.082, 0.085, 0, 0.01), (0.11, 0.078, 0.075, 0, 0.0), (0.2, 0.07, 0.062, 0, -0.018),
          (0.28, 0.07, 0.058, 0, -0.028), (0.34, 0.064, 0.052, 0, -0.033), (0.38, 0.04, 0.034, 0, -0.035)]
    HI = HR.inverted()
    def face(c, n):
        q = HI @ (c - HB); nn = HI @ n
        if nn.z < -0.35: return "Belly"                       # the pale chin and lower lip
        if q.y > 0.22 and abs(nn.x) > 0.6: return "Belly"     # the pale furred sides of the muzzle
        return "Base"
    P.obj("DeerHead", H(loft(UP, 18, sq=1.3)), face, 0)
    nose = hp((0, 0.385, -0.02))
    P.obj("DeerNose", H(ball((0, 0.385, -0.02), (0.05, 0.032, 0.042), 10, 5)), "Lamp" if lead else "Dark")
    P.obj("Mouth", H(pipe([(-0.055, 0.3, -0.07), (0, 0.37, -0.075), (0.055, 0.3, -0.07)], [0.006, 0.006, 0.006], 4)), "Dark")
    bits = []
    for s in (1, -1):
        P.obj("Nostril", H(ball((s * 0.022, 0.4, -0.015), (0.012, 0.008, 0.016), 6, 3)), "Dark")
        e = (s * 0.072, 0.1, 0.035)
        P.obj("Socket", H(oriented_ball(e, (0.022, 0.032, 0.026), Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1)), 10, 5)), "Dark")
        P.obj("DeerGlint", H(ball((s * 0.088, 0.112, 0.042), (0.006, 0.006, 0.006), 6, 3)), "Glow")
        # a heavy brow ridge slanted down toward the nose: the glare
        P.obj("DeerBrow", H(oriented_ball((s * 0.068, 0.105, 0.062), (0.03, 0.045, 0.012), Vector((1, 0, 0)), Vector((0, 0.9, -s * 0.0 - 0.35)).normalized(), Vector((0, 0.35, 0.94)), 10, 5)), "Base")
        ear = ball((0, 0, 0), (0.03, 0.08, 0.016), 10, 5)
        xf(ear, Matrix.Rotation(math.radians(s * 40), 3, "Z") @ Matrix.Rotation(math.radians(15), 3, "X"), (s * 0.1, -0.06, 0.06))
        P.obj("Ear", H(ear), "Base")
        # the bridle: cheek strap from the noseband up behind the ear, a gold bit ring at the corner of the mouth
        P.obj("Bridle", H(pipe([(s * 0.066, 0.27, -0.03), (s * 0.08, 0.12, -0.0), (s * 0.075, -0.02, 0.06), (s * 0.03, -0.05, 0.1)], [0.01] * 4, 5)), "Accent")
        P.obj("BitRing", H(xf(torus(0.02, 0.006, 0.0, 12, 4), Matrix.Rotation(math.radians(90), 3, "Y"), (s * 0.068, 0.3, -0.05))), "Trim")
        bits.append(hp((s * 0.072, 0.3, -0.05)))
        # the antlers of a reindeer: a long beam sweeping back and up, then forward, a palm at the top; the bez tine forward,
        # and on the right side the flat "shovel" brow tine reaching forward over the face
        ped = (s * 0.045, 0.0, 0.08)
        beam = bez(ped, (s * 0.14, -0.16, 0.2), (s * 0.24, -0.14, 0.44), (s * 0.19, 0.06, 0.58), 10)
        P.obj("Antler", H(pipe(beam, [0.022 - 0.012 * i / 10 for i in range(11)], 7)), "Metal")
        P.obj("Burr", H(xf(torus(0.024, 0.008, 0.0, 10, 4), None, ped)), "Metal")
        bz = beam[3]
        P.obj("Tine", H(pipe([bz, bz + Vector((s * 0.02, 0.1, 0.06)), bz + Vector((s * 0.03, 0.15, 0.13))], [0.014, 0.01, 0.0], 5)), "Metal")
        bk = beam[6]
        P.obj("Tine", H(pipe([bk, bk + Vector((s * 0.03, -0.08, 0.06)), bk + Vector((s * 0.05, -0.1, 0.12))], [0.012, 0.008, 0.0], 5)), "Metal")
        tip = beam[-1]
        for k in range(3):   # the top palm: three points fanned forward and up
            a = math.radians(-30 + 30 * k)
            d = Vector((s * 0.03, math.cos(a) * 0.09, math.sin(a) * 0.05 + 0.06))
            P.obj("Tine", H(pipe([beam[-3], tip, tip + d], [0.012, 0.01, 0.0], 5)), "Metal")
        if s > 0:
            sh = [Vector(ped) + Vector((0, 0.02, 0.03)), Vector((s * 0.025, 0.12, 0.1)), Vector((s * 0.02, 0.22, 0.1))]
            blade = pipe(sh, [0.014, 0.012, 0.004], 8)
            for v in blade.verts:   # flattened sideways into a palm
                v.co.x = sh[0].x + (v.co.x - sh[0].x) * 0.35
                v.co.z += (v.co.z - 0.1) * 0.9
            P.obj("Shovel", H(blade), "Metal")
            for k in range(3):
                p0 = Vector((s * 0.022, 0.16 + 0.03 * k, 0.12)); P.obj("Tine", H(cone(p0, p0 + Vector((0, 0.03, 0.035)), 0.008, 4)), "Metal")
    P.obj("Noseband", H(sl_ring((0, 0.27, -0.025), 0.074, 0.062, 0.012, Matrix.Rotation(math.radians(90), 3, "X"), 20, 5)), "Accent")

    # ---- the harness: a padded red collar hung with jingle bells, a back pad and a belly band
    cc = W((0, 0.43, 0.18))
    CR = Matrix.Rotation(math.radians(-42), 3, "X")
    P.obj("Collar", sl_ring(cc, 0.13, 0.17, 0.026, CR, 24, 8), "Accent")
    for k in range(5):
        a = math.radians(-60 + 30 * k)
        q = cc + CR @ Vector((math.sin(a) * 0.15, -math.cos(a) * 0.19, 0)) + Vector((0, 0.03, -0.02))
        sl_bell(P, q, 0.032)
    sides = [cc + Vector((s * 0.14, -0.02, -0.05)) for s in (1, -1)]
    P.obj("Pad", ball(tuple(W((0, 0.02, 0.26))), (0.15, 0.13, 0.035), 12, 5), lambda c, n: "Trim" if abs((c - O).x) > 0.12 else "Accent")
    P.obj("Girth", sl_ring(W((0, 0.02, 0.07)), 0.185, 0.215, 0.022, Matrix.Rotation(math.radians(90), 3, "X"), 24, 5), "Accent")
    for s in (1, -1):
        sl_bell(P, W((s * 0.19, 0.02, -0.04)), 0.026)

    # ---- the legs, each its own mover hinged at the shoulder or hip: a flying gallop, a deer's joints, broad cloven hooves
    def leg(name, hub, joints, radii):
        hub = W(hub); J = [W(p) for p in joints]
        P.part(name, oriented_ball(hub + Vector((0, 0, -0.03)), (0.09, 0.12, 0.15), Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1)), 10, 5), "Base", tuple(hub))
        P.part(name, pipe([hub] + J[:-1], radii, 9), "Base", tuple(hub))
        for k in range(1, len(J) - 2):
            P.part(name, ball(tuple(J[k]), (radii[k + 1] * 1.25,) * 3, 8, 4), "Base", tuple(hub))
        fet, cor, tip = J[-3], J[-2], J[-1]
        P.part(name, pipe([fet + (fet - cor) * 0.6, cor], [radii[-2] * 1.35, radii[-1] * 1.4], 9), "Belly", tuple(hub))   # the white sock above the hoof
        d = (tip - cor).normalized(); cannon = (fet - J[-4]).normalized()
        across = d.cross(Vector((0, 0, 1))).normalized() if abs(d.z) < 0.95 else Vector((1, 0, 0))
        bdir = -(d - cannon * d.dot(cannon)).normalized()
        for s in (1, -1):   # the two broad crescent toes of a reindeer's hoof, splayed, and a big dewclaw behind each
            o = across * s * 0.03
            P.part(name, oriented_ball(cor + o + d * 0.04, (0.03, 0.055, 0.022), across, d, d.cross(across).normalized(), 8, 4), "Dark", tuple(hub))
            b = fet + bdir * 0.025 + across * s * 0.02
            P.part(name, cone(b, b + cannon * 0.045 + bdir * 0.02, 0.013, 5), "Dark", tuple(hub))
    fr, hr = [0.075, 0.05, 0.032, 0.024, 0.024], [0.09, 0.055, 0.034, 0.025, 0.025]
    leg("SwayLeg0" + tag, (0.11, 0.24, -0.02), [(0.12, 0.3, -0.2), (0.12, 0.48, -0.3), (0.12, 0.66, -0.34), (0.12, 0.71, -0.36), (0.12, 0.77, -0.37)], fr)
    leg("SwayLeg1" + tag, (-0.11, 0.24, -0.02), [(-0.12, 0.29, -0.22), (-0.12, 0.42, -0.36), (-0.12, 0.31, -0.47), (-0.12, 0.27, -0.51), (-0.12, 0.27, -0.57)], fr)
    leg("SwayLeg2" + tag, (0.11, -0.36, 0.0), [(0.13, -0.3, -0.2), (0.13, -0.5, -0.28), (0.13, -0.72, -0.34), (0.13, -0.77, -0.35), (0.13, -0.83, -0.35)], hr)
    leg("SwayLeg3" + tag, (-0.11, -0.36, 0.0), [(-0.13, -0.28, -0.22), (-0.13, -0.46, -0.32), (-0.13, -0.62, -0.44), (-0.13, -0.66, -0.47), (-0.13, -0.7, -0.53)], hr)
    sl_grow(P, n0, s0, O, K)
    S = lambda p: O + (Vector(p) - O) * K
    return [S(b) for b in bits], [S(q) for q in sides], S(nose), S(cc)


def X_sleigh():
    """Santa's sleigh (2026-10-13, remade: "same as the alien bosses - realistic details, scarier, keep the cartoon shape"): the same
    red sleigh with Santa at the reins and two reindeer out in front, now built like a real Victorian cutter. A carved body in red lacquer,
    tall at the back where the sack rides, dipping over the seat and the footwell, the dash rising at the front and rolling forward into a
    scroll; gold pinstripes follow its top edge and its foot, and on each side three gold scroll pairs stand evenly along the panel. A
    padded black leather seat and a tufted back with gold buttons, the backrest rolling back into a scroll; a carriage lantern on each front
    corner, glass and gold, lit. Black iron runners, braced to the body by three knees a side, curl up at the front into a swan neck ending
    in a gold-capped volute. Behind the seat the burlap sack, tied with gold cord, and real wrapped presents - ribbons round them both ways,
    a bow of two loops and two tails on top.
    Santa is no jolly Santa: a heavy man in a red coat trimmed in white fur down the front and round the hem, a black belt with a gold
    buckle, black gloves and boots; a long white beard falling in locks to his belt and a thick moustache over a hard mouth, a broad nose,
    small eyes glinting red in deep sockets under thick white brows drawn down in a scowl, and the floppy fur-brimmed hat. His left fist
    holds the reins, his right raises the whip, its lash curling out over the team.
    It flies the way the legend says, PULLED BY A TEAM OF FLYING REINDEER: a pair of real reindeer in harness, side by side - dark winter
    coats, the long white mane at the throat and the pale neck, a white rump patch, white socks over broad cloven hooves with big
    dewclaws, a blunt furred muzzle, ears back, a glinting eye under a heavy brow, and the antlers of a reindeer: a long beam sweeping back,
    up and forward to a palm of three points, a bez tine forward, a back tine, and on the right side the flat shovel brow tine reaching out
    over the face. The right one leads with a glowing red nose (his shots leave from it). Each wears a padded red collar hung with five
    jingle bells, a bridle with gold bit rings, a back pad and a girth with a bell each side; the traces run from the collars back to a
    singletree each on the evener at the sleigh's pole, a neck yoke at the pole's end, and the reins run back to Santa's fist. They leap
    in a flying gallop - forelegs reaching, hind legs thrown back - each leg its own mover (SwayLeg0-3, A the right one and B the left);
    two trails of stardust sparkle away behind the runners."""
    P = Boss("sleigh", {"Base": ((0.30, 0.17, 0.09), 0.3), "Belly": ((0.96, 0.95, 0.92), 0.3), "Accent": ((0.72, 0.04, 0.05), 0.6),
                        "Trim": ((0.96, 0.72, 0.22), 0.85), "Glass": ((0.93, 0.66, 0.54), 0.3), "Dark": ((0.05, 0.04, 0.04), 0.5),
                        "Glow": ((1.0, 0.82, 0.42), 0.5), "Metal": ((0.76, 0.66, 0.5), 0.3), "Lamp": ((1.0, 0.1, 0.06), 0.8)})

    # ---- the sleigh body
    def tubpaint(c, n):
        if n.z > 0.7: return "Dark"                  # the floor inside
        if c.z < 0.11 and n.z < 0.5: return "Trim"   # the gold moulding round its foot
        return "Accent"
    P.obj("Tub", sl_tub(), tubpaint, 0)
    for s in (1, -1):
        ys = [-1.5 + 2.02 * i / 30 for i in range(31)]
        P.obj("Pinstripe", pipe(sl_on_side(s, [Vector((0, y, lerp_keys(y, SL_TOP) - 0.09)) for y in ys], 0.006), [0.013] * 31, 5), "Trim")
        ys = [-1.42 + 1.9 * i / 24 for i in range(25)]
        P.obj("Pinstripe", pipe(sl_on_side(s, [Vector((0, y, 0.17)) for y in ys], 0.006), [0.013] * 25, 5), "Trim")
        for y0 in (-1.22, -0.48, 0.24):   # three scroll pairs evenly along the panel: two volutes back to back under a leaf
            for d in (1, -1):
                sp = sl_spiral((y0 + d * 0.13, 0.36), 0.1, 0.02, 90 + d * 90 - d * 0, 90 + d * 90 + d * 300, 18) if False else \
                     sl_spiral((y0 + d * 0.11, 0.36), 0.095, 0.018, 90, 90 + d * 330, 18)
                P.obj("Scroll", pipe(sl_on_side(s, sp, 0.008), [0.012] * 19, 5), "Trim")
            P.obj("Scroll", pipe(sl_on_side(s, [Vector((0, y0, 0.45)), Vector((0, y0, 0.52))], 0.008), [0.02, 0.0], 5), "Trim")
    # the dash rising at the front and rolling forward into a scroll
    path = [Vector((0, 0.58, 0.5)), Vector((0, 0.63, 0.7)), Vector((0, 0.68, 0.9))] + sl_spiral((0.83, 0.93), 0.15, 0.035, 168, -200, 22)[1:]
    m = len(path)
    P.obj("Dash", sl_xribbon(path, [0.4 - 0.04 * i / m for i in range(m)], [0.03] * m), lambda c, n: "Trim" if abs(c.x) > 0.34 else "Accent", 0)
    # the seat back rolling back into a scroll, the tufted leather on its front, the padded seat
    path = [Vector((0, -0.97, 0.72)), Vector((0, -1.0, 0.95)), Vector((0, -1.04, 1.2))] + sl_spiral((-1.16, 1.24), 0.12, 0.03, 0, 330, 20)[1:]
    m = len(path)
    P.obj("SeatBack", sl_xribbon(path, [0.58] * m, [0.035] * m), lambda c, n: "Trim" if abs(c.x) > 0.53 else "Accent", 0)
    P.obj("Tufting", ball((0, -0.94, 0.98), (0.5, 0.05, 0.2), 16, 6), "Dark", 0)
    P.obj("Seat", ball((0, -0.62, 0.68), (0.55, 0.3, 0.07), 16, 6), "Dark", 0)
    for i in range(4):
        for j in range(2):
            P.obj("Button", ball((-0.3 + 0.2 * i, -0.895, 0.9 + 0.16 * j), (0.022, 0.012, 0.022), 6, 3), "Trim")
    # black iron runners curling up into a swan neck at the front, braced to the body by three knees
    for s in (1, -1):
        x = s * 0.47
        run = [Vector((x, -1.86, -0.04)), Vector((x, -1.8, -0.18)), Vector((x, -1.66, -0.25))] + [Vector((x, -1.4 + 2.15 * i / 8, -0.25)) for i in range(9)]
        run += [Vector((x, p.y, p.z)) for p in bez((0, 0.85, -0.25), (0, 1.1, -0.25), (0, 1.24, 0.0), (0, 1.16, 0.3), 6)[1:]]
        run += [Vector((x, p.y, p.z)) for p in sl_spiral((1.02, 0.34), 0.14, 0.04, -15, 300, 16)[1:]]
        P.obj("Runner", pipe(run, [0.036] * len(run), 7), "Dark")
        P.obj("Finial", ball((x, 1.02, 0.34), (0.045, 0.045, 0.045), 8, 4), "Trim")
        P.obj("Finial", ball((x, -1.86, -0.03), (0.04, 0.04, 0.04), 8, 4), "Trim")
        for y in (-1.2, -0.46, 0.26):
            P.obj("Knee", pipe([(x, y, -0.23), (s * 0.55, y + 0.02, -0.1), (s * 0.52, y + 0.05, 0.08)], [0.03, 0.026, 0.03], 6), "Dark")
            P.obj("KneeCap", ball((s * 0.55, y + 0.02, -0.1), (0.035,) * 3, 6, 3), "Trim")
    # carriage lanterns on the front corners
    for s in (1, -1):
        lc = Vector((s * 0.5, 0.58, 1.0))
        P.obj("Bracket", pipe([(s * 0.44, 0.55, 0.6), (s * 0.52, 0.57, 0.78), lc + Vector((0, 0, -0.1))], [0.018, 0.016, 0.016], 5), "Dark")
        P.obj("LampBase", lathe([(0.0, -0.13), (0.04, -0.13), (0.07, -0.09), (0.07, -0.07)], 6, "z", tuple(lc)), "Trim")
        P.obj("LampGlass", lathe([(0.0, -0.07), (0.065, -0.07), (0.072, 0.06), (0.0, 0.06)], 6, "z", tuple(lc)), "Glow")
        P.obj("LampCap", lathe([(0.0, 0.06), (0.085, 0.06), (0.06, 0.1), (0.025, 0.15), (0.0, 0.15)], 6, "z", tuple(lc)), "Trim")
        P.obj("LampTop", ball(tuple(lc + Vector((0, 0, 0.17))), (0.022,) * 3, 6, 3), "Trim")
        for k in range(6):
            a = 2 * math.pi * k / 6
            P.obj("LampPost", pipe([lc + Vector((math.cos(a) * 0.07, math.sin(a) * 0.07, -0.07)), lc + Vector((math.cos(a) * 0.074, math.sin(a) * 0.074, 0.06))], [0.008, 0.008], 4), "Trim")

    # ---- the sack and the presents behind the seat
    P.obj("Sack", ball((0, -1.32, 1.18), (0.42, 0.28, 0.42), 16, 8), lambda c, n: "Dark" if abs(math.sin(ang(c - Vector((0, -1.32, 1.18))) * 4)) < 0.06 else "Base", 1)
    P.obj("SackNeck", pipe([(0, -1.3, 1.52), (0.02, -1.28, 1.66), (0.05, -1.26, 1.74)], [0.13, 0.1, 0.16], 10), "Base")
    P.obj("Cord", xf(torus(0.13, 0.022, 0.0, 14, 4), None, (0.01, -1.29, 1.6)), "Trim")
    P.obj("Cord", pipe([(0.12, -1.25, 1.6), (0.2, -1.2, 1.45), (0.18, -1.15, 1.35)], [0.016, 0.014, 0.0], 4), "Trim")
    sl_present(P, (0.42, -1.4, 0.94), (0.26, 0.26, 0.28), "Accent", "Trim", 12)
    sl_present(P, (-0.42, -1.38, 0.92), (0.24, 0.24, 0.24), "Belly", "Accent", -8)
    sl_present(P, (0.04, -1.24, 1.84), (0.2, 0.2, 0.18), "Trim", "Accent", 20)
    sl_present(P, (0.36, -1.12, 1.22), (0.16, 0.16, 0.16), "Belly", "Trim", -15)

    # ---- Santa
    P.obj("Coat", ball((0, -0.64, 1.16), (0.42, 0.34, 0.44), 18, 9), lambda c, n: "Belly" if abs(c.x) < 0.07 and n.y > 0.3 else "Accent", 1)
    P.obj("CoatHem", sl_ring((0, -0.64, 0.84), 0.4, 0.33, 0.055, None, 24, 6), "Belly")
    P.obj("Belt", sl_ring((0, -0.64, 1.04), 0.425, 0.345, 0.04, None, 24, 5), "Dark")
    P.obj("Buckle", box((0, -0.29, 1.04), (0.15, 0.04, 0.12)), "Trim", 0, False)
    P.obj("BuckleHole", box((0, -0.275, 1.04), (0.08, 0.02, 0.06)), "Dark", 0, False)
    for s in (1, -1):   # thighs forward over the seat, shins down into the footwell, boots
        P.obj("Leg", pipe([(s * 0.18, -0.64, 0.88), (s * 0.2, -0.25, 0.84), (s * 0.21, -0.12, 0.55)], [0.13, 0.11, 0.09], 10), "Accent")
        P.obj("Boot", pipe([(s * 0.21, -0.12, 0.6), (s * 0.21, -0.11, 0.5), (s * 0.21, 0.02, 0.48)], [0.09, 0.09, 0.07], 10), "Dark")
        P.obj("BootFur", xf(torus(0.095, 0.03, 0.0, 14, 4), None, (s * 0.21, -0.12, 0.62)), "Belly")
    hc = Vector((0, -0.56, 1.74))
    P.obj("Face", ball(tuple(hc), (0.21, 0.2, 0.22), 16, 8), "Glass", 0)
    P.obj("Nose", ball(tuple(hc + Vector((0, 0.2, -0.02))), (0.055, 0.045, 0.045), 8, 4), "Glass")
    for s in (1, -1):
        P.obj("Socket", ball(tuple(hc + Vector((s * 0.075, 0.17, 0.05))), (0.04, 0.02, 0.03), 8, 4), "Dark")
        P.obj("EyeGlint", ball(tuple(hc + Vector((s * 0.075, 0.186, 0.05))), (0.012, 0.008, 0.012), 6, 3), "Lamp")
        # thick white brows drawn down toward the nose: the scowl
        P.obj("Brow", pipe([hc + Vector((s * 0.15, 0.13, 0.13)), hc + Vector((s * 0.09, 0.18, 0.1)), hc + Vector((s * 0.025, 0.2, 0.06))], [0.03, 0.035, 0.022], 7), "Belly")
        # the thick moustache curling out
        P.obj("Moustache", pipe(bez(hc + Vector((0, 0.21, -0.07)), hc + Vector((s * 0.08, 0.22, -0.08)), hc + Vector((s * 0.17, 0.18, -0.12)), hc + Vector((s * 0.22, 0.12, -0.06)), 6), [0.04, 0.045, 0.042, 0.035, 0.026, 0.016, 0.0], 7), "Belly")
        P.obj("Ear", ball(tuple(hc + Vector((s * 0.2, 0.0, 0.0))), (0.03, 0.05, 0.06), 6, 3), "Glass")
    P.obj("MouthLine", pipe([hc + Vector((-0.06, 0.19, -0.135)), hc + Vector((0, 0.205, -0.14)), hc + Vector((0.06, 0.19, -0.135))], [0.01, 0.01, 0.01], 4), "Dark")
    # the beard: a full white mass from the cheeks to the belt, its surface in locks curling at the ends
    P.obj("Beard", ball(tuple(hc + Vector((0, 0.1, -0.2))), (0.2, 0.12, 0.24), 14, 7), "Belly", 0)
    for k in range(9):
        u = -1 + 2 * k / 8
        b0 = hc + Vector((u * 0.17, 0.12 + 0.05 * (1 - abs(u)), -0.1 - 0.06 * abs(u)))
        L = 0.5 - 0.18 * abs(u)
        pts = [b0, b0 + Vector((u * 0.04, 0.06, -L * 0.4)), b0 + Vector((u * 0.06, 0.04, -L * 0.8)), b0 + Vector((u * 0.03 - math.copysign(0.03, u + 1e-3), 0.06, -L))]
        P.obj("Beard", pipe(pts, [0.05, 0.05, 0.035, 0.0], 8), "Belly")
    P.obj("HatBrim", sl_ring(hc + Vector((0, -0.02, 0.17)), 0.2, 0.19, 0.055, None, 22, 6), "Belly")
    P.obj("Hat", pipe(bez(hc + Vector((0, -0.02, 0.17)), hc + Vector((0, -0.04, 0.42)), hc + Vector((-0.12, -0.2, 0.5)), hc + Vector((-0.3, -0.3, 0.36)), 7), [0.2, 0.18, 0.15, 0.12, 0.09, 0.07, 0.05, 0.04], 12), "Accent")
    P.obj("Pompom", ball(tuple(hc + Vector((-0.32, -0.31, 0.32))), (0.07,) * 3, 8, 4), "Belly")
    # left fist on the reins, right arm raising the whip
    hand = Vector((-0.24, -0.16, 1.1))
    P.obj("Arm", pipe([(-0.38, -0.62, 1.4), (-0.48, -0.4, 1.18), hand + Vector((-0.03, -0.06, 0))], [0.1, 0.09, 0.08], 9), "Accent")
    P.obj("Cuff", xf(torus(0.075, 0.03, 0.0, 12, 4), Matrix.Rotation(math.radians(80), 3, "X"), tuple(hand + Vector((-0.03, -0.07, 0)))), "Belly")
    P.obj("Glove", ball(tuple(hand), (0.075, 0.07, 0.07), 8, 4), "Dark")
    rhand = Vector((0.66, -0.5, 1.84))
    P.obj("Arm", pipe([(0.38, -0.62, 1.4), (0.66, -0.6, 1.5), rhand + Vector((0, -0.04, -0.08))], [0.1, 0.09, 0.08], 9), "Accent")
    P.obj("Cuff", xf(torus(0.075, 0.03, 0.0, 12, 4), None, tuple(rhand + Vector((0, -0.03, -0.09)))), "Belly")
    P.obj("Glove", ball(tuple(rhand), (0.07, 0.07, 0.08), 8, 4), "Dark")
    wt = rhand + Vector((0.04, 0.26, 0.38))
    P.obj("WhipHandle", pipe([rhand + Vector((0, 0, -0.08)), wt], [0.022, 0.014], 6), "Dark")
    P.obj("WhipFerrule", ball(tuple(rhand + Vector((0, 0, -0.1))), (0.03,) * 3, 6, 3), "Trim")

    # ---- the team
    deer = []
    for (rx, tag, lead) in ((0.5, "A", True), (-0.5, "B", False)):
        deer.append(sl_deer(P, (rx, 2.3, 0.3), tag, lead))
    # the pole between them, the evener and two singletrees at its root, the neck yoke at its end
    P.obj("Pole", pipe([(0, 0.62, 0.12), (0, 1.2, 0.18), (0, 2.9, 0.5)], [0.035, 0.032, 0.028], 8), "Base")
    P.obj("Evener", pipe([(-0.62, 1.12, 0.18), (0.62, 1.12, 0.18)], [0.028, 0.028], 8), "Base")
    P.obj("Yoke", pipe([(-0.3, 2.86, 0.5), (0.3, 2.86, 0.5)], [0.022, 0.022], 6), "Base")
    P.obj("YokeCap", ball((0, 2.9, 0.5), (0.04,) * 3, 6, 3), "Trim")
    reins, traces = [], []
    for (bits, sides, nose, cc), rx in zip(deer, (0.5, -0.5)):
        P.obj("Singletree", pipe([(rx - 0.2, 1.24, 0.19), (rx + 0.2, 1.24, 0.19)], [0.022, 0.022], 6), "Base")
        P.obj("Clevis", pipe([(rx * 1.24, 1.12, 0.18), (rx, 1.24, 0.19)], [0.012, 0.012], 4), "Trim")
        for k, sd in enumerate(sides):
            end = Vector((rx + (0.2 if sd.x > rx else -0.2), 1.24, 0.19))
            traces.append(pipe([sd, (sd + end) * 0.5 + Vector((0, 0, -0.04)), end], [0.012, 0.012, 0.012], 4))
        for b in bits:
            reins.append(pipe([b, (b + hand) * 0.5 + Vector((0, 0, 0.12)), hand], [0.009, 0.009, 0.009], 4))
        P.obj("YokeStrap", pipe([cc + Vector((-math.copysign(0.15, rx), 0.0, -0.06)), Vector((math.copysign(0.3, rx), 2.86, 0.5))], [0.014, 0.014], 4), "Accent")
    lead_nose = deer[0][2]
    # thin lines (reins, traces, the lash) and the stardust on the no-outline Cloth part
    hub = (0, 0, 0)
    for bm in reins: P.part("Cloth", bm, "Accent", hub)
    for bm in traces: P.part("Cloth", bm, "Dark", hub)
    lash = bez(wt, wt + Vector((0.0, 0.45, 0.25)), wt + Vector((-0.2, 1.2, 0.15)), wt + Vector((-0.45, 1.6, -0.2)), 14)
    P.part("Cloth", pipe(lash, [0.012 - 0.008 * i / 14 for i in range(15)], 5), "Dark", hub)
    for s in (1, -1):
        for k in range(10):
            t = k / 9.0
            c = Vector((s * (0.47 + 0.1 * t), -1.95 - t * 0.7, -0.1 - 0.22 * t + 0.05 * math.sin(t * 7 + s)))
            r = 0.075 * (1 - 0.6 * t)
            P.part("Cloth", hull([c + Vector((r, 0, 0)), c - Vector((r, 0, 0)), c + Vector((0, 0, r * 1.6)), c - Vector((0, 0, r * 1.6)), c + Vector((0, r * 0.4, 0)), c - Vector((0, r * 0.4, 0))]),
                   "Glow" if k % 3 else "Belly", hub)
            q = c + Vector((s * 0.08, 0.06, 0.1 * (1 if k % 2 else -1)))
            P.part("Cloth", ball(tuple(q), (r * 0.3,) * 3, 6, 3), "Glow", hub)
    P.part("Muzzle", ball(tuple(lead_nose + Vector((0, 0.05, 0))), (0.05, 0.04, 0.05), 8, 4), "Lamp", tuple(lead_nose + Vector((0, 0.05, 0))))
    return P



# ================================================================= krampus (2026-10-13 remake)
X_ = Vector((1, 0, 0))

def kp_lerp(keys, u):
    """keys sampled at whole u; linear between."""
    i = max(0, min(len(keys) - 2, int(math.floor(u)))); f = u - i
    a, b = keys[i], keys[i + 1]
    if isinstance(a, Vector): return a.lerp(b, f)
    return a + (b - a) * f

class kp_Body:
    """a loft along a spine: sections rx across, rp toward t x X ("front" for an upright spine, "down" for a forward one), rm the other way."""
    def __init__(self, pts, rx, rp, rm):
        self.S = [Vector(p) for p in pts]; self.rx, self.rp, self.rm = rx, rp, rm
    def frame(self, u):
        n = len(self.S) - 1; i = max(0, min(n, int(round(u))))
        t = (self.S[min(i + 1, n)] - self.S[max(i - 1, 0)]).normalized()
        return t, t.cross(X_).normalized()
    def pt(self, u, a, lift=0.0):
        p = kp_lerp(self.S, u); t, F = self.frame(u)
        ca, sa = math.cos(a), math.sin(a)
        rx = kp_lerp(self.rx, u); rf = kp_lerp(self.rp if sa > 0 else self.rm, u)
        q = p + X_ * ca * rx + F * sa * rf
        return q + (q - p).normalized() * lift if lift else q
    def normal(self, u, a):
        return (self.pt(u, a) - kp_lerp(self.S, u)).normalized()
    def mesh(self, rows=24, seg=24):
        bm = bmesh.new(); rings = [[bm.verts.new(self.S[0])]]
        n = len(self.S) - 1
        for j in range(1, rows):
            u = n * j / rows
            rings.append([bm.verts.new(self.pt(u, 2 * math.pi * k / seg)) for k in range(seg)])
        rings.append([bm.verts.new(self.S[-1])])
        return skin(bm, rings, seg)

def kp_lock(P, base, d, L, w, name="Fur", tip="Belly"):
    """one lock of shaggy fur: a flat-ish tapering strand from base along d (not normalised: bends with it)."""
    base = Vector(base); d = Vector(d).normalized()
    pts = [base, base + d * L * 0.5 + Vector((0, 0, -L * 0.08)), base + d * L + Vector((0, 0, -L * 0.2))]
    P.obj(name, pipe(pts, [w, w * 0.75, 0.0], 4), lambda c, n, b=base: tip if (c - b).length > L * 0.68 else "Base", 0, True)

def kp_link(c, t, k, r=0.055, rr=0.016):
    """a chain link at c along t, every other one turned a quarter."""
    bm = torus(r, rr, 0.0, 10, 4)
    xf(bm, Matrix.Scale(1.0, 3))
    for v in bm.verts: v.co.x *= 0.62
    q = Vector(t).normalized().to_track_quat("X", "Z").to_matrix() @ Matrix.Rotation(math.radians(90 * (k % 2)), 3, "X")
    for v in bm.verts: v.co = q @ v.co + Vector(c)
    return bm

def kp_chain(P, pts, name="Chain", hub=None, step=0.085):
    """links along a polyline, evenly every `step`."""
    pts = [Vector(p) for p in pts]; segs = list(zip(pts, pts[1:]))
    total = sum((b - a).length for a, b in segs); n = max(2, int(total / step)); k = 0
    for i in range(n + 1):
        s = total * i / n
        for a, b in segs:
            L = (b - a).length
            if s <= L + 1e-6:
                c = a + (b - a) * (s / L if L else 0); t = b - a; break
            s -= L
        if hub is None: P.obj(name, kp_link(c, t, i), "Metal")
        else: P.part(name, kp_link(c, t, i), "Metal", hub)

def kp_bolt(c, drop, zig, seg=6, r=0.032):
    """a jagged lightning bolt hanging from c: alternating kinks, each shorter than the last."""
    c = Vector(c); pts = [c]
    for i in range(seg):
        side = 1 if i % 2 == 0 else -1
        pts.append(pts[-1] + Vector((side * zig * (1 - 0.1 * i), -0.04 * side, -drop / seg)))
    return pts, pipe(pts, [r * (1 - 0.8 * i / seg) for i in range(seg)] + [0.0], 5)


def X_krampus():
    """KRAMPUS (2026-10-13, remade: "same as the alien bosses - realistic details, scarier, keep the cartoon shape"): the same hulking
    shaggy goat-demon with the great horns, the red face, the tongue, the bells, the birch rod and the basket, now built like the Krampus
    of the Alpine Krampuslauf. His coat is long shaggy goat fur, black-brown, lying in even rows of locks from the shoulders down that turn
    rust-brown at their tips; furry goat legs bent under him, the hocks of a goat and split hooves with dewclaws; a short tufted tail. The
    face is a carved Krampus mask in red-brown: a long goat face, the forehead and the bridge of the snout cut with deep wrinkles, folds
    running from the nostrils to the corners of the mouth, heavy brows slanting down to the middle in a glare over yellow goat eyes with
    the bar pupil of a goat, flared nostrils, the jaw dropped open on fangs and a long red tongue lolling down his chest, a goat beard, long
    drooping goat ears, and a frame of fur round the mask. From his skull rise two long goat horns sweeping back and out, ringed all along
    with the growth ridges of real horn and tapering to points. The costume of the Krampuslauf: a leather belt round his middle hung with
    five iron cowbells, each with its clapper, evenly across the front; a rusty iron chain slung across his chest from shoulder to hip; in
    his raised right claw a bundle of birch rods (Ruten) tied with a red ribbon; in his left a swinging iron lantern; on his back a wicker
    basket strapped over his shoulders, birch twigs sticking out of it. His hands are clawed.
    He flies by RIDING A BLACK STORM CLOUD: he crouches in a heavy blizzard cloud, a heap of charcoal billows - a ring of ten big ones round
    six on top - whose underside hangs in the rounded pouches of a real storm cloud (mammatus), a cold light glowing deep between the
    billows; snow and hail stream down from under it in even streaks, slanting back in the wind, two jagged forks of lightning hang from
    it, and two of his chains trail down out of it and swing. The outer ring of billows, with the cold light between them and the small
    billows torn off its edge, slowly turns round the heap he crouches in (SpinCloud). His shots leave from his open mouth."""
    P = Boss("krampus", {"Base": ((0.06, 0.045, 0.035), 0.2), "Belly": ((0.17, 0.10, 0.06), 0.25), "Accent": ((0.50, 0.11, 0.07), 0.45),
                         "Trim": ((0.40, 0.33, 0.24), 0.45), "Glass": ((0.92, 0.88, 0.76), 0.55), "Dark": ((0.075, 0.08, 0.10), 0.35),
                         "Glow": ((0.62, 0.86, 1.0), 0.5), "Metal": ((0.24, 0.22, 0.22), 0.75), "Lamp": ((1.0, 0.78, 0.12), 0.8)})
    # ================= the body: a hunched torso along a spine leaning toward the player
    T = kp_Body([(0, -0.2, -0.44), (0, -0.13, -0.22), (0, -0.03, 0.12), (0, 0.09, 0.47), (0, 0.21, 0.8), (0, 0.34, 1.04), (0, 0.44, 1.22)],
                [0.18, 0.46, 0.55, 0.64, 0.7, 0.42, 0.24], [0.14, 0.36, 0.42, 0.44, 0.38, 0.26, 0.2], [0.14, 0.4, 0.44, 0.5, 0.52, 0.32, 0.22])
    P.obj("Torso", T.mesh(), "Base")
    # the shaggy coat: even rows of locks, each row offset half a lock, hanging down and out
    row = 0
    u = 0.5
    while u < 5.7:
        rx = kp_lerp(T.rx, u); rf = (kp_lerp(T.rp, u) + kp_lerp(T.rm, u)) / 2
        n = max(10, int(2 * math.pi * math.sqrt((rx * rx + rf * rf) / 2) / 0.15))
        tdir, _ = T.frame(u)
        for k in range(n):
            a = 2 * math.pi * (k + 0.5 * (row % 2)) / n
            b = T.pt(u, a, 0.01); out = T.normal(u, a)
            L = 0.56 if u < 4.6 else 0.36
            kp_lock(P, b, -tdir + out * 0.12, L, 0.052)
        u += 0.46; row += 1
    # ================= the head: a fur-covered skull behind a carved red-brown mask
    nh = len(P.parts)
    HC = Vector((0, 0.5, 1.42))
    P.obj("Skull", ball(tuple(HC), (0.34, 0.34, 0.36), 16, 8), "Base", 1)
    M = kp_Body([(0, 0.62, 1.6), (0, 0.8, 1.5), (0, 0.95, 1.33), (0, 1.04, 1.2)],
                [0.33, 0.31, 0.23, 0.165], [0.25, 0.27, 0.2, 0.12], [0.14, 0.15, 0.12, 0.09])
    P.obj("Mask", M.mesh(18, 22), "Accent")
    UP = -math.pi / 2   # the mask's top (its "minus" side points up)
    # a frame of fur round the mask, locks pointing out and back
    for k in range(18):
        a = 2 * math.pi * k / 18
        if math.sin(a) > 0.55: continue   # not across the mouth
        b = M.pt(0.45, a, -0.01); o = M.normal(0.45, a)
        kp_lock(P, b, o * 0.8 + Vector((0, -0.5, 0)), 0.22, 0.06, "Ruff")
    # wrinkles: three furrows across the forehead, three creases on the bridge, a fold from each nostril to the mouth corner
    for s in (1, -1):   # the two deep frown lines between the brows
        pts = [M.pt(0.35 + 0.1 * i, UP + s * (0.07 + 0.03 * i), 0.002) for i in range(6)]
        P.obj("Wrinkle", pipe(pts, [0.0, 0.012, 0.013, 0.013, 0.011, 0.0], 5), "Dark")
    for j in range(3):  # three creases arching over the bridge of the snout, each a little shorter
        uu = 1.65 + j * 0.24; sp = 0.75 - 0.12 * j
        pts = [M.pt(uu - 0.12 * (1 - (2 * i / 6 - 1) ** 2), UP + sp * (i / 6 - 0.5), 0.003) for i in range(7)]
        P.obj("Wrinkle", pipe(pts, [0.0] + [0.009] * 5 + [0.0], 5), "Dark")
    for s in (1, -1):   # a fold from each nostril down past the mouth corner
        a0 = UP + s * 0.95
        pts = [M.pt(2.7, a0, 0.003), M.pt(2.3, a0 + s * 0.5, 0.003), M.pt(1.9, a0 + s * 0.95, 0.003)]
        P.obj("Wrinkle", pipe(pts, [0.0, 0.014, 0.0], 5), "Dark")
    # brows: heavy ridges slanting down to the middle, a deep furrow between them
    for s in (1, -1):
        # the eye: a deep socket, a yellow eyeball and the goat's bar pupil, under the brow
        e = M.pt(1.0, UP + s * 1.05, -0.035)
        o = Vector((s * 0.35, 1.0, 0.1)).normalized(); ex = Vector((0, 0, 1)).cross(o).normalized(); ez = o.cross(ex).normalized()
        P.obj("Socket", oriented_ball(e, (0.125, 0.07, 0.085), ex, o, ez), "Dark")
        P.obj("Eye", oriented_ball(e + o * 0.03, (0.1, 0.045, 0.066), ex, o, ez), "Lamp")
        P.obj("Pupil", oriented_ball(e + o * 0.068, (0.058, 0.012, 0.012), ex, o, ez), "Dark")
        P.obj("Glint", ball(tuple(e + o * 0.075 + ex * s * 0.03 + ez * 0.025), (0.012, 0.008, 0.012), 6, 3), "Glass")
        # the brow: a heavy ridge slanting hard down to the middle over the eye, the glare of an angry goat
        bpts = [e + Vector((-s * 0.13, 0.07, 0.03)), e + Vector((-s * 0.01, 0.05, 0.085)), e + Vector((s * 0.14, -0.02, 0.15))]
        P.obj("Brow", pipe(bpts, [0.045, 0.06, 0.035], 8), "Accent")
        P.obj("Lid", oriented_ball(e + o * 0.03 + ez * 0.05 - ex * s * 0.04, (0.07, 0.05, 0.03), ex, o, ez), "Accent")
        # nostrils, flared
        P.obj("Nostril", ball(tuple(M.pt(2.85, UP + s * 0.75, 0.0)), (0.042, 0.035, 0.028), 8, 4), "Dark")
        # long drooping goat ears
        ec = HC + Vector((s * 0.4, 0.02, 0.02))
        ex = Vector((s * 0.85, 0.15, -0.5)).normalized(); ez = Vector((0, 0, 1)).cross(ex).normalized()
        P.obj("Ear", oriented_ball(ec + ex * 0.16, (0.24, 0.05, 0.085), ex, ez, ex.cross(ez)), "Base")
        P.obj("EarIn", oriented_ball(ec + ex * 0.17 + Vector((0, 0.035, 0)), (0.19, 0.03, 0.06), ex, ez, ex.cross(ez)), "Accent")
        # the horns: long goat horns sweeping back and out, ringed with growth ridges, tapering to a point
        h0 = HC + Vector((s * 0.17, -0.02, 0.28))
        pts = bez(h0, h0 + Vector((s * 0.14, -0.14, 0.45)), h0 + Vector((s * 0.6, -0.62, 0.62)), h0 + Vector((s * 1.0, -0.6, 0.2)), 44)
        N = len(pts) - 1
        rad = [0.115 * (1 - i / N) ** 0.85 * (1 + 0.13 * abs(math.sin(math.pi * i * 0.75))) if i < N else 0.0 for i in range(N + 1)]
        P.obj("Horn", pipe(pts, rad, 10), lambda c, n, tip=pts[-1]: "Dark" if (c - tip).length < 0.12 else "Trim")
        for k in range(5):   # the fur tuft round the horn's root
            a = 2 * math.pi * k / 5
            b = h0 + Vector((math.cos(a) * 0.1, math.sin(a) * 0.1, -0.06))
            kp_lock(P, b, Vector((math.cos(a), math.sin(a), -0.6)), 0.14, 0.05, "Tuft")
    # the open mouth: a dropped jaw, a dark throat, fangs, a long red tongue lolling down his chest; a goat beard below
    P.obj("Jaw", hull([(-0.12, 0.8, 1.12), (0.12, 0.8, 1.12), (-0.12, 0.8, 1.02), (0.12, 0.8, 1.02), (-0.07, 1.04, 0.98),
                       (0.07, 1.04, 0.98), (-0.06, 1.02, 0.92), (0.06, 1.02, 0.92)]), "Accent", 1)
    P.obj("Throat", ball((0, 0.98, 1.06), (0.11, 0.09, 0.065), 12, 6), "Dark")
    for s in (1, -1):
        for x, top, L, w in ((0.095, 1.1, 0.16, 0.03), (0.06, 1.12, 0.07, 0.016), (0.03, 1.13, 0.06, 0.014)):
            P.obj("Fang", cone((s * x, 1.05 + 0.06 * (0.1 - x), top), (s * x * 0.95, 1.07 + 0.06 * (0.1 - x), top - L), w, 5), "Glass", 0, False)
        P.obj("Fang", cone((s * 0.075, 1.01, 0.99), (s * 0.08, 1.03, 1.1), 0.026, 5), "Glass", 0, False)
    tg = bez((0, 0.98, 1.03), (0, 1.18, 0.98), (0.02, 1.24, 0.72), (-0.04, 1.08, 0.42), 20)
    # the tongue: broad and flat, lolling, a groove down its middle, rounded at the tip
    TG = kp_Body(tg, [0.05 + 0.03 * math.sin(math.pi * min(1.0, i / 16)) if i < 20 else 0.0 for i in range(21)],
                 [0.026] * 20 + [0.0], [0.022] * 20 + [0.0])
    P.obj("Tongue", TG.mesh(30, 16), "Accent")
    P.obj("Tongue", pipe([TG.pt(1 + i, -math.pi / 2, 0.0) for i in range(16)], [0.0] + [0.007] * 14 + [0.0], 4), "Dark")
    for k in range(5):
        x = (k - 2) * 0.05
        kp_lock(P, (x, 0.92, 0.95), Vector((x * 1.5, 0.15, -1)), 0.32 - 0.04 * abs(k - 2), 0.05, "Beard", "Base")
    piv = Vector((0, 0.4, 1.18)); big = Matrix.Translation(piv) @ Matrix.Scale(1.2, 4) @ Matrix.Translation(-piv)
    for ob in P.parts[nh:]: ob.data.transform(big)
    # ================= the belt and its five cowbells, the chain across the chest
    belt = [T.pt(1.45, 2 * math.pi * k / 28, 0.17) for k in range(29)]
    P.obj("Belt", pipe(belt, [0.045] * 29, 6, False), "Dark")
    for k in range(5):
        a = math.radians(30 + 30 * k)
        top = T.pt(1.45, a, 0.2) + Vector((0, 0, -0.04)); o = T.normal(1.45, a); o.z = 0; o.normalize()
        sx = Vector((0, 0, 1)).cross(o).normalized()
        name = "SwayBell%d" % k
        P.part(name, pipe([top + Vector((0, 0, 0.06)), top + o * 0.03, top + Vector((0, 0, -0.03))], [0.016, 0.016, 0.016], 5), "Dark", tuple(top))
        corners = []
        for z, hw, hd in ((-0.03, 0.065, 0.04), (-0.27, 0.1, 0.065), (-0.31, 0.115, 0.075)):
            for i in (1, -1):
                for j in (1, -1): corners.append(tuple(top + sx * hw * i + o * (0.03 + hd * j) + Vector((0, 0, z))))
        P.part(name, hull(corners), "Metal", tuple(top), 0, False)
        P.part(name, ball(tuple(top + o * 0.03 + Vector((0, 0, -0.32))), (0.03, 0.03, 0.035), 6, 3), "Dark", tuple(top))
    path = [T.pt(4.5 - 3.0 * i / 16, math.radians(150 - 130 * i / 16), 0.2) for i in range(17)]
    kp_chain(P, path, "Chain")
    # ================= the basket on his back, strapped over the shoulders, birch twigs sticking out
    BC = Vector((0, -0.66, 0.45))
    P.obj("Basket", lathe([(0.0, -0.36), (0.36, -0.36), (0.42, 0.0), (0.47, 0.42), (0.47, 0.46), (0.42, 0.46), (0.37, -0.3), (0.0, -0.3)], 36, "z", tuple(BC)),
          lambda c, n: "Trim" if (int((math.atan2(c.y - BC.y, c.x) + math.pi) / (2 * math.pi) * 36) + int((c.z - BC.z + 1) * 22)) % 2 == 0 else "Belly")
    P.obj("BasketRim", xf(torus(0.47, 0.035, 0.0, 28, 6), None, tuple(BC + Vector((0, 0, 0.46)))), "Trim")
    for k in range(7):
        a = 2 * math.pi * k / 7
        b = BC + Vector((math.cos(a) * 0.22, math.sin(a) * 0.2, 0.3))
        tip = b + Vector((math.cos(a) * 0.2, math.sin(a) * 0.14 - 0.12, 0.7 + 0.08 * (k % 2)))
        P.obj("Twig", pipe([b, b.lerp(tip, 0.5) + Vector((0, 0, 0.03)), tip], [0.022, 0.016, 0.004], 5),
              lambda c, n: "Dark" if int(c.z * 18) % 4 == 0 else "Glass")
    for s in (1, -1):
        P.obj("Strap", pipe([BC + Vector((s * 0.25, 0.3, 0.42)), T.pt(4.6, math.radians(90 - s * 55) if s > 0 else math.radians(90 + 55), 0.16) + Vector((0, -0.25, 0.15)),
                             T.pt(3.6, math.radians(90 - s * 45) if s > 0 else math.radians(135), 0.2)], [0.03, 0.03, 0.03], 5), "Dark")
    # ================= the arms: shaggy, clawed; birch rods raised in the right, the lantern swinging from the left
    for s in (1, -1):
        sh = Vector((s * 0.64, 0.2, 0.86))
        el = Vector((s * 1.02, 0.34, 0.66)) if s > 0 else Vector((s * 1.0, 0.36, 0.5))
        wr = Vector((s * 1.06, 0.62, 1.04)) if s > 0 else Vector((s * 1.0, 0.76, 0.36))
        P.obj("Arm", pipe([sh, el, wr], [0.2, 0.15, 0.11], 10), "Base")
        for seg, (a0, a1) in enumerate(((sh, el), (el, wr))):
            d = (a1 - a0)
            for j in range(3):
                c = a0 + d * (0.15 + 0.3 * j)
                for k in range(7):
                    a = 2 * math.pi * (k + 0.5 * (j % 2)) / 7
                    fa = d.normalized().to_track_quat("Z", "Y").to_matrix() @ Vector((math.cos(a), math.sin(a), 0))
                    r = 0.19 - 0.04 * seg - 0.02 * j
                    kp_lock(P, c + fa * r * 0.85, fa * 0.5 + Vector((0, 0, -1)), 0.2, 0.05, "ArmFur")
        hand = wr + (wr - el).normalized() * 0.08
        P.obj("Hand", ball(tuple(hand), (0.1, 0.11, 0.09), 10, 5), "Accent", 1)
        fw = (wr - el).normalized()
        for k in range(4):
            x = (k - 1.5) * 0.045
            base = hand + Vector((x, 0, 0)) + fw * 0.07
            if s > 0:   # gripped round the rods
                pts = [base, base + Vector((0, 0.06, -0.02)), base + Vector((-0.04, 0.07, -0.07))]
            else:       # hooked claws reaching
                pts = [base, base + fw * 0.09 + Vector((0, 0.03, 0)), base + fw * 0.15 + Vector((0, 0.03, -0.05))]
            P.obj("Finger", pipe(pts, [0.026, 0.022, 0.018], 6), "Accent")
            P.obj("Claw", cone(pts[-1], pts[-1] + (pts[-1] - pts[-2]).normalized() * 0.07 + Vector((0, 0, -0.02)), 0.017, 5), "Glass", 0, False)
    # the birch rods: nine twigs fanned up from the fist, white bark with dark marks, a red ribbon and bow round them
    hr = Vector((1.06, 0.68, 1.1))
    for k in range(9):
        a = 2 * math.pi * k / 9
        b = hr + Vector((math.cos(a) * 0.035, math.sin(a) * 0.035, -0.25))
        tip = hr + Vector((math.cos(a) * 0.22 + 0.05, math.sin(a) * 0.18, 0.8 + 0.06 * (k % 3)))
        P.obj("Rod", pipe([b, hr + Vector((math.cos(a) * 0.04, math.sin(a) * 0.04, 0.2)), tip], [0.022, 0.018, 0.004], 5),
              lambda c, n: "Dark" if int(c.z * 16) % 5 == 0 else "Glass")
    P.obj("Ribbon", xf(torus(0.065, 0.024, 0.0, 12, 4), None, tuple(hr + Vector((0, 0, 0.17)))), "Accent")
    for s in (1, -1):
        P.obj("Bow", oriented_ball(hr + Vector((s * 0.08, 0.05, 0.19)), (0.07, 0.025, 0.045), Vector((s, 0.3, 0.3)).normalized(), Vector((0, 1, 0)), Vector((0, 0, 1))), "Accent")
        P.obj("BowTail", pipe([hr + Vector((s * 0.02, 0.07, 0.15)), hr + Vector((s * 0.06, 0.09, 0.02)), hr + Vector((s * 0.05, 0.1, -0.1))], [0.02, 0.018, 0.012], 4), "Accent")
    # the lantern: iron frame, glass panes lit by a candle, hung from a ring in his left claw
    hl = Vector((-1.0, 0.86, 0.26)); lc = hl + Vector((0, 0, -0.12))
    P.part("SwayLantern", pipe([hl + Vector((0, 0, 0.06)), lc], [0.012, 0.012], 4), "Metal", tuple(hl))
    P.part("SwayLantern", lathe([(0.0, 0.03), (0.04, 0.0), (0.13, -0.08), (0.11, -0.1), (0.0, -0.1)], 6, "z", tuple(lc)), "Metal", tuple(hl))
    P.part("SwayLantern", lathe([(0.095, -0.1), (0.095, -0.36), (0.0, -0.36)], 6, "z", tuple(lc)), "Lamp", tuple(hl))
    P.part("SwayLantern", lathe([(0.0, -0.36), (0.12, -0.36), (0.12, -0.4), (0.0, -0.42)], 6, "z", tuple(lc)), "Metal", tuple(hl))
    for k in range(6):
        a = 2 * math.pi * k / 6
        P.part("SwayLantern", pipe([lc + Vector((math.cos(a) * 0.1, math.sin(a) * 0.1, -0.09)), lc + Vector((math.cos(a) * 0.1, math.sin(a) * 0.1, -0.37))], [0.012, 0.012], 4), "Metal", tuple(hl))
    # ================= the legs: furry goat legs bent under him, the hocks of a goat, split hooves with dewclaws
    for s in (1, -1):
        hip = Vector((s * 0.32, -0.12, -0.26)); knee = Vector((s * 0.44, 0.3, -0.52)); hock = Vector((s * 0.42, -0.2, -0.72))
        fet = Vector((s * 0.42, -0.02, -0.88))
        P.obj("Leg", pipe([hip, knee, hock, fet], [0.25, 0.17, 0.09, 0.075], 10), "Base")
        for a0, a1, rr, rows in ((hip, knee, 0.22, 3), (knee, hock, 0.15, 2)):
            d = a1 - a0
            for j in range(rows):
                c = a0 + d * (0.2 + 0.6 * j / max(1, rows - 1))
                for k in range(8):
                    a = 2 * math.pi * (k + 0.5 * (j % 2)) / 8
                    fa = d.normalized().to_track_quat("Z", "Y").to_matrix() @ Vector((math.cos(a), math.sin(a), 0))
                    kp_lock(P, c + fa * rr * 0.85, fa * 0.45 + Vector((0, 0, -1)), 0.22, 0.055, "LegFur")
        for h in (1, -1):   # the two halves of the cloven hoof
            P.obj("Hoof", hull([tuple(fet + Vector((h * 0.012 + h * 0.0, 0.02, 0.02))), tuple(fet + Vector((h * 0.075, 0.0, 0.02))),
                                tuple(fet + Vector((h * 0.07, 0.13, -0.1))), tuple(fet + Vector((h * 0.012, 0.16, -0.1))),
                                tuple(fet + Vector((h * 0.075, -0.04, -0.1))), tuple(fet + Vector((h * 0.012, -0.04, -0.1)))]), "Dark", 0, False)
            P.obj("Dewclaw", cone(fet + Vector((h * 0.04, -0.06, 0.04)), fet + Vector((h * 0.05, -0.11, -0.02)), 0.02, 4), "Dark", 0, False)
    tl = bez((0, -0.45, -0.28), (0, -0.62, -0.25), (0, -0.72, -0.12), (0, -0.74, -0.02), 4)
    P.obj("Tail", pipe(tl, [0.05, 0.045, 0.04, 0.03, 0.0], 6), "Base")
    for k in range(5):
        a = 2 * math.pi * k / 5
        kp_lock(P, tl[-2], Vector((math.cos(a) * 0.5, -0.4 + math.sin(a) * 0.5, 0.6)), 0.14, 0.04, "TailTuft")
    # ================= the storm cloud he rides
    C0 = Vector((0, -0.05, -1.12))
    P.obj("CloudBase", ball(tuple(C0 + Vector((0, 0, -0.08))), (1.0, 0.9, 0.3), 30, 12), "Dark")
    for k in range(10):   # the ring of ten big billows, alternately bigger and smaller
        a = 2 * math.pi * k / 10 + 0.31
        r = 0.44 if k % 2 == 0 else 0.36
        c = C0 + Vector((math.cos(a) * 0.86, math.sin(a) * 0.78, 0.06 + (0.05 if k % 2 == 0 else -0.02)))
        P.part("SpinCloud", ball(tuple(c), (r, r, r * 0.82), 20, 10), "Dark", tuple(C0))
        g = C0 + Vector((math.cos(a + math.pi / 10) * 0.86, math.sin(a + math.pi / 10) * 0.8, -0.02))   # the cold light between two billows
        P.part("SpinCloud", ball(tuple(g), (0.11, 0.11, 0.09), 8, 4), "Glow", tuple(C0))
        if k % 2 == 0:   # a small billow torn off the outside of every other one
            c2 = C0 + Vector((math.cos(a + 0.18) * 1.32, math.sin(a + 0.18) * 1.2, -0.06))
            P.part("SpinCloud", ball(tuple(c2), (0.17, 0.14, 0.12), 12, 6), "Dark", tuple(C0))
    for k in range(6):   # six on top round one in the middle, where he crouches
        a = 2 * math.pi * k / 6
        c = C0 + Vector((math.cos(a) * 0.48, math.sin(a) * 0.42, 0.26))
        P.obj("Billow", ball(tuple(c), (0.36, 0.36, 0.3), 18, 9), "Dark")
    for (x, y) in [(0, 0)] + [(math.cos(2 * math.pi * k / 6) * 0.42, math.sin(2 * math.pi * k / 6) * 0.38) for k in range(6)] + \
                  [(math.cos(2 * math.pi * (k + 0.5) / 8) * 0.75, math.sin(2 * math.pi * (k + 0.5) / 8) * 0.66) for k in range(8)]:
        c = C0 + Vector((x, y, -0.36))
        P.obj("Mammatus", ball(tuple(c), (0.18, 0.18, 0.2), 12, 6), "Dark")
    # snow and hail streaming down from under it, slanting back in the wind (fine lines: no outline)
    for ring, n in ((0.22, 4), (0.55, 7), (0.88, 9)):
        for k in range(n):
            a = 2 * math.pi * (k + 0.5 * (n % 2)) / n
            b = C0 + Vector((math.cos(a) * ring, math.sin(a) * ring * 0.9, -0.42))
            L = 0.42 + 0.16 * ((k + n) % 3) / 2
            e = b + Vector((0, -0.28 * L, -L))
            P.obj("Cloth", pipe([b, e], [0.014, 0.003], 4), "Glow", 0, False)
            if k % 2 == 0:
                for f in (0.45, 0.85):
                    P.obj("Cloth", ball(tuple(b.lerp(e, f) + Vector((0.03, 0, 0))), (0.03, 0.03, 0.03), 6, 3), "Glow")
    for s, at in ((1, (0.5, 0.45, -1.42)), (-1, (-0.62, 0.15, -1.42))):   # two forks of lightning hanging from it
        pts, bm = kp_bolt(at, 0.9, 0.16 * s, 6, 0.05)
        P.obj("Cloth", bm, "Glow", 0, False)
        _, br = kp_bolt(pts[2], 0.4, -0.11 * s, 3, 0.032)
        P.obj("Cloth", br, "Glow", 0, False)
    # two chains trailing down out of the cloud, swinging, an open shackle on each end
    for s in (1, -1):
        top = C0 + Vector((s * 0.72, 0.22, -0.28))
        pts = [top, top + Vector((s * 0.04, -0.12, -0.35)), top + Vector((s * 0.06, -0.3, -0.7))]
        kp_chain(P, pts, "SwayChain" + ("R" if s > 0 else "L"), tuple(top))
        sh = pts[-1] + Vector((0, -0.03, -0.1))
        P.part("SwayChain" + ("R" if s > 0 else "L"), xf(torus(0.08, 0.022, 0.0, 14, 5), Matrix.Rotation(math.pi / 2, 3, "X"), tuple(sh)), "Metal", tuple(top))
    P.part("Muzzle", ball((0, 1.14, 1.03), (0.06, 0.035, 0.045), 8, 4), "Lamp", (0, 1.14, 1.03))
    return P



# ================================================================= snowman (2026-10-13 remake)
# the snow giant remade (2026-10-13): an evil snowman of real packed snow, surfing a giant snowflake


def sn_lump(c, r, seg=28, rings=16, seed=0.0, amp=0.03):
    """a snowball that was rolled by hand: an ellipsoid with a slightly uneven, lumpy surface (smooth waves, no noise)."""
    bm = ball(c, r, seg, rings); c = Vector(c)
    for v in bm.verts:
        d = v.co - c
        if d.length < 1e-6: continue
        a = math.atan2(d.x, d.y); b = math.atan2(d.z, math.hypot(d.x, d.y))
        k = 1 + amp * (math.sin(3 * a + seed) * math.cos(2 * b + seed * 0.7) + 0.6 * math.sin(5 * a - 2 * b + seed * 1.3) + 0.4 * math.cos(7 * b + a))
        v.co = c + d * k
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)   # the poles of the lathe close up
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm

def sn_on(c, r, x, y, z):
    """the point on the ellipsoid (c, r) in the direction (x, y, z)."""
    d = Vector((x / r[0], y / r[1], z / r[2]))
    t = 1.0 / d.length
    return Vector(c) + Vector((x, y, z)) * t

def sn_spiral(c, r, s, turns=2.2, n=60, inset=0.98):
    """the spiral of rolled-up snow on the flat side (x = s) of a rolled ball: each layer the ball picked up as it rolled."""
    pts = []
    for i in range(n + 1):
        u = i / n; th = u * turns * 2 * math.pi; rho = 0.12 + 0.72 * u
        y = rho * math.cos(th); z = rho * math.sin(th); x = s * math.sqrt(max(0.0, 1 - rho * rho))
        pts.append(Vector(c) + Vector((x * r[0], y * r[1], z * r[2])) * inset)
    return pts

def sn_coal(c, k, seed=0):
    """an irregular lump of coal about c, size k."""
    c = Vector(c); pts = []
    for i in range(9):
        a = 2.4 * i + seed; b = math.sin(1.7 * i + seed) * 1.2
        rr = k * (0.75 + 0.3 * math.sin(3.1 * i + seed * 2))
        pts.append(c + Vector((math.cos(a) * math.cos(b), math.sin(b) * 0.7, math.sin(a) * math.cos(b))) * rr)
    return hull([tuple(p) for p in pts])

def sn_flat(poly, z, thick):
    """a flat ice plate (a polygon in x, y) at height z."""
    return sheet([[(p[0], p[1], z) for p in poly]], thick)

def sn_bar(a, b, w0, w1, z, thick):
    """a tapering flat ice bar from a to b (x, y) at height z."""
    a, b = Vector((a[0], a[1], 0)), Vector((b[0], b[1], 0)); d = (b - a).normalized(); n = Vector((-d.y, d.x, 0))
    poly = [a + n * w0, b + n * w1, b - n * w1, a - n * w0]
    return sn_flat([(p.x, p.y) for p in poly], z, thick)

def sn_hex(c, R, z, thick, rot=0.0):
    return sn_flat([(c[0] + R * math.cos(rot + math.pi / 3 * i), c[1] + R * math.sin(rot + math.pi / 3 * i)) for i in range(6)], z, thick)


def X_snowman():
    """The snow giant (2026-10-13, remade: "same as the alien bosses - realistic details, scarier, keep the cartoon shape"): the same hulking
    three-ball snowman with a battered top hat, a carrot nose, a knitted scarf and branch arms, now built like a real snowman of packed snow -
    and evil. Three hand-rolled balls, each a little lumpy and uneven, the bottom and middle ones showing on their sides the spiral of snow
    they picked up as they were rolled, with what came up with it caught evenly along the spiral - gravel, a twig, a dead oak leaf; their
    shaded undersides glazed to blue ice. His face is coal: two deep coal sockets under heavy frowning brows of packed snow, an ice-blue light
    glowing inside each with a slit of a pupil; a jagged grin of irregular coal lumps, the mouth behind them dark and set with icicle teeth
    hanging from the top and jutting from the bottom; a real carrot for a nose, tapering, ringed with its growth lines, a stub of green top at
    its root; coal buttons down his front; a row of icicles hanging evenly from his chin. A knitted scarf in red and green rib-knit, wound
    round his neck, its two ends with knotted fringes trailing back in the wind. His arms are real branches: crooked, knotted, a side twig
    at the elbow, the hands forked into three twig fingers - the left reaching at the player like a claw, the right closed round a hard-packed
    snowball glowing ice-blue that his shots come from. A battered top hat, its crown dented and leaning, a red band with a sprig of holly,
    snow on the brim and the crown, icicles hanging evenly round the brim.
    He flies by SURFING A GIANT SNOWFLAKE: under him lies a huge real snowflake - a stellar dendrite, six-fold, each of the six arms a ridged
    spine with three pairs of side branches at sixty degrees, longest near the middle, a small six-sided plate at every tip, a ring of plates
    round the hexagonal heart, which glows; it lies flat like a flying disc with his bottom ball sitting in its heart, and it turns slowly
    under him (SpinFlake). Fine snow powder blows off its back in a widening stream of puffs (Cloth)."""
    P = Boss("snowman", {"Base": ((0.30, 0.19, 0.11), 0.25), "Belly": ((0.95, 0.97, 1.0), 0.3), "Accent": ((1.0, 0.45, 0.06), 0.45),
                         "Trim": ((0.72, 0.05, 0.08), 0.35), "Glass": ((0.60, 0.80, 1.0), 0.9), "Dark": ((0.035, 0.035, 0.045), 0.5),
                         "Glow": ((0.06, 0.5, 1.0), 0.5), "Metal": ((0.05, 0.38, 0.18), 0.35), "Lamp": ((0.75, 0.92, 1.0), 0.8)})
    def snow_of(c0, r):   # glazed ice on the shaded underside of a ball
        return lambda c, n: "Glass" if (c.z - c0[2]) < -0.62 * r[2] else "Belly"
    BOT = ((0, 0, -0.62), (0.8, 0.74, 0.7)); MID = ((0, 0.04, 0.32), (0.6, 0.56, 0.54)); HEAD = ((0, 0.07, 1.06), (0.48, 0.46, 0.46))
    for nm, (c, r), sd in (("Bottom", BOT, 0.3), ("Middle", MID, 1.9), ("Head", HEAD, 3.7)):
        P.obj(nm, sn_lump(c, r, 30, 16, sd, 0.03 if nm != "Head" else 0.018), snow_of(c, r))
    # the spiral of rolled-up snow on each side of the two lower balls, with what it picked up caught evenly along it
    for (c, r) in (BOT, MID):
        for s in (1, -1):
            sp = sn_spiral(c, r, s, 2.2, 60, 0.985)
            P.obj("Roll", pipe(sp, [0.008] + [0.022] * (len(sp) - 2) + [0.008], 6), "Belly")
            for j, i in enumerate(range(8, len(sp) - 4, 13)):
                p = sp[i]; out = (p - Vector(c)).normalized()
                kind = j % 3
                if kind == 0:   # gravel
                    P.obj("Gravel", sn_coal(p + out * 0.02, 0.03, j + s), "Base", 0, False)
                elif kind == 1:   # a twig
                    t = (sp[i + 2] - sp[i - 2]).normalized()
                    P.obj("Twig", pipe([p - t * 0.09 + out * 0.02, p + out * 0.03, p + t * 0.1 + out * 0.015], [0.012, 0.01, 0.004], 4), "Base")
                else:   # a dead oak leaf pressed into the snow
                    t = (sp[i + 2] - sp[i - 2]).normalized(); w = out.cross(t).normalized()
                    lp = [p + out * 0.02 + t * (0.07 * math.cos(a)) + w * (0.045 * math.sin(a) * (1 + 0.25 * math.cos(5 * a))) for a in [2 * math.pi * q / 12 for q in range(12)]]
                    bm = bmesh.new(); vs = [bm.verts.new(q) for q in lp]; bm.faces.new(vs)
                    bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=0.01)
                    P.obj("Leaf", bm, "Base", 0, False)
    # coal buttons down his front
    for k, z in enumerate((0.62, 0.38, 0.14, -0.3)):
        p = sn_on(MID[0] if z > -0.1 else BOT[0], MID[1] if z > -0.1 else BOT[1], 0, 1, (z - (MID[0][2] if z > -0.1 else BOT[0][2])) / 0.75)
        P.obj("Button", sn_coal(p + Vector((0, 0.01, 0)), 0.08, k * 2.3), "Dark", 0, False)
    # ---- the face
    hc = Vector(HEAD[0])
    for s in (1, -1):
        e = sn_on(HEAD[0], HEAD[1], s * 0.38, 0.85, 0.32)
        P.obj("Socket", ball(tuple(e + Vector((0, -0.02, 0))), (0.1, 0.06, 0.085), 12, 6), "Dark")
        P.obj("Eye", ball(tuple(e + Vector((0, 0.022, -0.005))), (0.062, 0.03, 0.05), 10, 5), "Glow")
        P.obj("Pupil", ball(tuple(e + Vector((s * 0.008, 0.048, -0.005))), (0.012, 0.01, 0.038), 6, 4), "Dark")
        # a heavy frowning brow of packed snow, low at the nose and rising outward
        b0 = sn_on(HEAD[0], HEAD[1], s * 0.05, 0.9, 0.3) + Vector((0, 0.05, -0.02)); b1 = sn_on(HEAD[0], HEAD[1], s * 0.42, 0.75, 0.62) + Vector((0, 0.04, 0.02))
        P.obj("Brow", pipe(bez(b0, b0 + (b1 - b0) * 0.33 + Vector((0, 0.04, 0.03)), b0 + (b1 - b0) * 0.7 + Vector((0, 0.03, 0.02)), b1, 6),
                           [0.035, 0.05, 0.055, 0.055, 0.05, 0.04, 0.025], 8), "Belly")
    # the grin: a dark mouth with icicle teeth, framed by jagged coal lumps
    mouth = []
    for k in range(11):
        t = (k - 5) / 5.0
        mouth.append(sn_on(HEAD[0], HEAD[1], t * 0.55, 0.9, -0.38 + 0.2 * t * t))
    P.obj("Mouth", pipe([m + Vector((0, -0.01, 0)) for m in mouth], [0.025] + [0.065 - 0.02 * abs((k - 5) / 5.0) for k in range(1, 10)] + [0.025], 8), "Dark")
    for k in range(1, 10):   # icicle teeth: from the top lip down, and from the bottom lip up between them
        m = mouth[k]; w = 0.065 - 0.02 * abs((k - 5) / 5.0); fwd = Vector((0, 0.045, 0))
        P.obj("Tooth", cone(m + fwd + Vector((0, 0, w * 0.7)), m + fwd + Vector((0, 0.005, -w * 0.85)), 0.024, 5), "Glass", 0, False)
        if k % 2 == 0:
            P.obj("Tooth", cone(m + fwd + Vector((0, 0, -w * 0.8)), m + fwd + Vector((0, 0.005, w * 0.5)), 0.018, 5), "Glass", 0, False)
    for k in range(0, 11, 2):   # jagged coal lumps along the lips
        m = mouth[k]
        P.obj("Grin", sn_coal(m + Vector((0, 0.04, 0.07)), 0.04, k), "Dark", 0, False)
        P.obj("Grin", sn_coal(m + Vector((0, 0.035, -0.075)), 0.035, k + 9), "Dark", 0, False)
    # the carrot: tapering, ringed with growth lines, a stub of green top at its root, pointing at the player and a little down
    nb = sn_on(HEAD[0], HEAD[1], 0.0, 1.0, 0.05); tip = nb + Vector((0.04, 0.62, -0.1))
    cpts = [nb + (tip - nb) * u + Vector((0, 0, 0.02 * math.sin(u * math.pi))) for u in [i / 10 for i in range(11)]]
    P.obj("Carrot", pipe(cpts, [0.085 * (1 - u) ** 0.8 + 0.004 for u in [i / 10 for i in range(10)]] + [0.0], 10),
          lambda c, n: "Base" if (((c - nb).length * 22) % 1.0) < 0.12 else "Accent")
    for k in range(3):
        a = 2 * math.pi * k / 3 + 0.4
        P.obj("CarrotTop", cone(nb + Vector((0, -0.04, 0.0)), nb + Vector((math.cos(a) * 0.09, -0.02, 0.07 + math.sin(a) * 0.05)), 0.018, 4), "Metal", 0, False)
    # icicles hanging evenly from his chin
    for k in range(7):
        t = (k - 3) / 3.0
        b = sn_on(HEAD[0], HEAD[1], t * 0.5, 0.7, -0.62)
        P.obj("Icicle", cone(b + Vector((0, 0, 0.02)), b + Vector((0, 0.02, -0.12 - 0.07 * (1 - abs(t)))), 0.026, 5), "Glass", 0, False)
    # ---- the knitted scarf: red and green rib-knit, the ends with knotted fringes trailing back
    sc = torus(0.4, 0.085, 0.0, 36, 8)
    for v in sc.verts: v.co.y *= 0.95
    xf(sc, None, (0, 0.06, 0.73))
    P.obj("Scarf", sc, lambda c, n: ("Trim" if (ang(Vector((c.x, c.y - 0.06, 0))) / (2 * math.pi) * 6) % 1.0 < 0.5 else "Metal"))
    for s in (1, -1):
        root = Vector((s * 0.22, 0.38, 0.68))
        end = bez(root, root + Vector((s * 0.18, 0.06, -0.25)), root + Vector((s * 0.42, -0.3, -0.32)), root + Vector((s * 0.6, -0.75, -0.2)), 8)
        name = "SwayScarf%d" % (0 if s > 0 else 1)
        P.part(name, pipe(end, [0.07] * 8 + [0.065], 8),
               lambda c, n, root=root: "Trim" if (((c - root).length * 6) % 1.0) < 0.5 else "Metal", tuple(root))
        d = (end[-1] - end[-2]).normalized()
        for k in range(5):
            q = end[-1] + Vector((s * 0.0, 0, (k - 2) * 0.026))
            P.part(name, ball(tuple(q + d * 0.01), (0.016, 0.016, 0.014), 5, 3), "Metal" if k % 2 else "Trim", tuple(root))
            P.part(name, pipe([q + d * 0.01, q + d * 0.09 + Vector((0, 0, -0.02))], [0.01, 0.004], 4), "Metal" if k % 2 else "Trim", tuple(root))
    # ---- the branch arms
    def branch(sh, el, hd, s):
        mid1 = sh + (el - sh) * 0.5 + Vector((0, 0, 0.04)); mid2 = el + (hd - el) * 0.5 + Vector((s * 0.02, 0, -0.03))
        P.obj("Branch", pipe([sh, mid1, el, mid2, hd], [0.07, 0.06, 0.055, 0.045, 0.035], 7), "Base")
        P.obj("Knot", ball(tuple(el + Vector((0, 0.02, 0.02))), (0.06, 0.06, 0.06), 8, 4), "Base")
        P.obj("Knot", ball(tuple(mid1 + Vector((0, 0.03, 0))), (0.045, 0.045, 0.04), 6, 3), "Base")
        sb = el + Vector((s * 0.06, -0.04, 0.18)); P.obj("SideTwig", pipe([el, sb, sb + Vector((s * 0.1, -0.05, 0.12))], [0.03, 0.02, 0.005], 5), "Base")
        return hd
    hR = branch(Vector((0.52, 0.05, 0.45)), Vector((0.98, 0.2, 0.7)), Vector((1.25, 0.42, 0.95)), 1)
    hL = branch(Vector((-0.52, 0.05, 0.45)), Vector((-0.95, 0.3, 0.55)), Vector((-1.15, 0.72, 0.62)), -1)
    # left hand: three twig fingers spread like a claw at the player
    for k in range(3):
        a = math.radians(-35 + 35 * k)
        d = Vector((-math.sin(a) * 0.5 - 0.2, 0.8, math.cos(a) * 0.45)).normalized()
        f1 = hL + d * 0.16; f2 = f1 + (d + Vector((0, 0.3, -0.35))).normalized() * 0.11
        P.obj("Finger", pipe([hL, f1, f2], [0.03, 0.02, 0.0], 5), "Base")
    # right hand: three twig fingers closed round a glowing snowball
    sbc = hR + Vector((0.1, 0.12, 0.22)); R = 0.24
    P.obj("Snowball", sn_lump(tuple(sbc), (R, R, R), 18, 9, 5.0, 0.04), "Belly")
    for k in range(3):
        a = math.radians(-50 + 50 * k)
        p0 = hR; p1 = sbc + Vector((math.sin(a) * R * 1.05, -R * 0.4, -R * 0.75)); p2 = sbc + Vector((math.sin(a) * R * 1.1, R * 0.1, -R * 0.05))
        P.obj("Finger", pipe([p0, p1, p2], [0.03, 0.022, 0.0], 5), "Base")
    for k in range(6):   # frost glowing on the snowball
        a = 2 * math.pi * k / 6; d = Vector((math.sin(a), 0.5 + 0.5 * math.cos(a), math.cos(a) * 0.4 + 0.5)).normalized()
        P.obj("Frost", cone(sbc + d * R * 0.9, sbc + d * R * 1.45, 0.035, 4), "Glow", 0, False)
    # ---- the battered top hat: a dented, leaning crown, a red band with holly, snow on the brim and crown, icicles round the brim
    hb = Vector((0.02, 0.05, 1.44))
    brim = lathe([(0.0, 0.0), (0.46, 0.0), (0.5, 0.03), (0.47, 0.05), (0.0, 0.05)], 28, "z", tuple(hb))
    for v in brim.verts:
        d = v.co - hb; v.co.z += 0.05 * d.x + 0.03 * math.sin(math.atan2(d.y, d.x) * 2) * (math.hypot(d.x, d.y) / 0.5)
    P.obj("Brim", brim, "Dark", 0, False)
    crown = lathe([(0.29, 0.04), (0.3, 0.2), (0.31, 0.5), (0.32, 0.56), (0.0, 0.56)], 24, "z", tuple(hb))
    for v in crown.verts:
        h = v.co.z - hb.z
        v.co.x += 0.1 * (h / 0.56) ** 1.5; v.co.y -= 0.03 * (h / 0.56)
        if h > 0.5 and v.co.x - hb.x < 0: v.co.z -= 0.06   # the dent in the top
        d = v.co - hb
        if h > 0.25 and d.y > 0.15 and abs(d.x - 0.05) < 0.12: v.co.y -= 0.03 * math.sin(min(1, (h - 0.25) / 0.2) * math.pi)   # a crease in front
    P.obj("Crown", crown, lambda c, n: "Trim" if c.z < hb.z + 0.15 else "Dark", 0, False)
    P.obj("TopSnow", sn_lump((hb.x + 0.12, hb.y - 0.03, hb.z + 0.53), (0.24, 0.24, 0.06), 14, 6, 2.0, 0.08), "Belly")
    for k in range(8):
        a = 2 * math.pi * (k + 0.5) / 8
        p = hb + Vector((math.sin(a) * 0.42, math.cos(a) * 0.42, 0.07 + 0.05 * math.sin(a) * 0.42 / 0.5))
        P.obj("BrimSnow", sn_lump(tuple(p), (0.1, 0.1, 0.04), 10, 5, k * 1.1, 0.1), "Belly")
    for k in range(12):
        a = 2 * math.pi * k / 12
        p = hb + Vector((math.sin(a) * 0.49, math.cos(a) * 0.49, 0.02 + 0.05 * math.sin(a) * 0.49))
        P.obj("Icicle", cone(p, p + Vector((0, 0, -0.08 - 0.05 * (k % 2))), 0.02, 5), "Glass", 0, False)
    for k in range(3):   # a sprig of holly on the band
        P.obj("Holly", ball((hb.x + 0.12 + 0.045 * k, hb.y + 0.28, hb.z + 0.12 + 0.03 * (k % 2)), (0.035, 0.03, 0.035), 6, 3), "Trim")
    for k in range(2):
        s = 1 if k else -1
        P.obj("HollyLeaf", hull([(hb.x + 0.17, hb.y + 0.29, hb.z + 0.12), (hb.x + 0.17 + s * 0.15, hb.y + 0.28, hb.z + 0.17), (hb.x + 0.17 + s * 0.1, hb.y + 0.3, hb.z + 0.08),
                                 (hb.x + 0.17 + s * 0.07, hb.y + 0.27, hb.z + 0.15)]), "Metal", 0, False)
    # ---- the giant snowflake he surfs: a stellar dendrite, six-fold, lying flat, turning slowly
    zf = -1.3; T = 0.05; FR = 1.55; hub = (0, 0, zf)
    def flake(name, bm, paint):
        P.part(name, bm, paint, hub, 0, False)
    flake("SpinFlake", sn_hex((0, 0), 0.34, zf, T), "Glass")
    flake("SpinFlake", sn_hex((0, 0), 0.22, zf + T * 0.6, T * 0.4, math.pi / 6), "Glow")
    for i in range(6):
        a = math.pi / 2 + math.pi / 3 * i; d = Vector((math.cos(a), math.sin(a), 0)); nrm = Vector((-d.y, d.x, 0))
        P0 = d * 0.3; P1 = d * FR
        flake("SpinFlake", sn_bar((P0.x, P0.y), (P1.x, P1.y), 0.075, 0.03, zf, T), "Glass")
        flake("SpinFlake", sn_bar(((d * 0.35).x, (d * 0.35).y), ((d * (FR - 0.12)).x, (d * (FR - 0.12)).y), 0.022, 0.01, zf + T * 0.55, T * 0.3), "Lamp")   # the ridge down the spine
        # a ring of plates round the heart
        q = d.copy(); q.rotate(Matrix.Rotation(math.pi / 6, 3, "Z")); pc = q * 0.42
        flake("SpinFlake", sn_hex((pc.x, pc.y), 0.09, zf, T * 0.8, a), "Glass")
        # three pairs of side branches at sixty degrees, longest near the middle
        for t, L in ((0.38, 0.38), (0.6, 0.42), (0.8, 0.26)):
            b = d * (FR * t)
            for s in (1, -1):
                bd = d * math.cos(math.pi / 3) + nrm * s * math.sin(math.pi / 3)
                e = b + bd * L
                flake("SpinFlake", sn_bar((b.x, b.y), (e.x, e.y), 0.045, 0.018, zf, T * 0.8), "Glass")
                # little twigs on the side branches, pointing out again
                m = b + bd * (L * 0.55)
                f = m + (bd * math.cos(math.pi / 3) + d * math.sin(math.pi / 3) * 0.0 + d * 0.5).normalized() * L * 0.35
                flake("SpinFlake", sn_bar((m.x, m.y), (f.x, f.y), 0.022, 0.01, zf, T * 0.6), "Glass")
        tip = d * (FR + 0.02)
        flake("SpinFlake", sn_hex((tip.x, tip.y), 0.1, zf, T * 0.9, a), "Glass")
        flake("SpinFlake", sn_hex((tip.x, tip.y), 0.05, zf + T * 0.5, T * 0.3, a + math.pi / 6), "Lamp")
    # ---- fine snow powder blowing off the back of the flake: a widening, fading stream of puffs
    for k in range(10):
        u = k / 9.0
        y = -FR * 0.85 - 0.12 - u * 0.9; spread = 0.25 + 0.5 * u
        for j in (-1, 0, 1):
            if j == 0 and k % 2: continue
            x = j * spread * 0.6 + (0.06 if k % 2 else -0.06)
            r = 0.09 * (1 - 0.6 * u) + 0.02
            P.part("Cloth", ball((x, y, zf + 0.04 + 0.1 * u), (r * 1.4, r * 1.2, r * 0.7), 8, 4), "Belly", (0, -FR, zf))
    P.part("Muzzle", ball(tuple(sbc + Vector((0, R + 0.02, 0))), (0.07, 0.04, 0.06), 8, 4), "Glow", tuple(sbc + Vector((0, R + 0.02, 0))))
    return P



# ================================================================= icequeen (2026-10-13 remake)
# Sky Squad, the christmas ICE QUEEN remade (scratch, to be merged into Tools/blender/christmas_bosses.py).


def iq_join(bms):
    """several bmeshes as one."""
    out = bmesh.new()
    for bm in bms:
        vm = {v: out.verts.new(v.co) for v in bm.verts}
        for f in bm.faces: out.faces.new([vm[v] for v in f.verts])
        bm.free()
    return out

def iq_rot(axis):
    """the rotation taking +Z to axis."""
    return Vector((0, 0, 1)).rotation_difference(Vector(axis).normalized()).to_matrix()

def iq_crystal(base, axis, r, h, tip=None, twist=0.0):
    """an ice crystal as it really grows: a six-sided prism standing on base along axis, r across, h long, a six-sided point on top."""
    tip = r * 1.7 if tip is None else tip
    bm = lathe([(0.0, -r * 0.3), (r, 0.0), (r, h), (0.0, h + tip)], 6, "z")
    if twist: xf(bm, Matrix.Rotation(twist, 3, "Z"))
    return xf(bm, iq_rot(axis), tuple(base))

def iq_hexplate(c, nrm, r, t, twist=0.0):
    """a flat six-sided ice plate (the heart of a snowflake, a chip of ice) about c, facing nrm."""
    bm = lathe([(0.0, -t * 0.5), (r, -t * 0.5), (r, t * 0.5), (0.0, t * 0.5)], 6, "z")
    if twist: xf(bm, Matrix.Rotation(twist, 3, "Z"))
    return xf(bm, iq_rot(nrm), tuple(c))

def iq_flake(c, nrm, up, size, t=None, heart=True):
    """a real six-fold snowflake (a stellar dendrite) lying in the plane facing nrm: six arms, each with two pairs of side branches at 60
    degrees, the inner pair longer, and a six-sided plate at the heart."""
    c, n = Vector(c), Vector(nrm).normalized()
    u = (Vector(up) - n * Vector(up).dot(n)).normalized(); v = n.cross(u)
    t = size * 0.1 if t is None else t; w = size * 0.11
    bms = []
    for k in range(6):
        a = k * math.pi / 3
        d = u * math.cos(a) + v * math.sin(a)
        bms.append(bar(c, c + d * size, w, t, up=tuple(n)))
        for f, L in ((0.42, 0.34), (0.7, 0.22)):
            p = c + d * size * f
            for q in (1, -1):
                e = d * math.cos(math.pi / 3) + n.cross(d) * math.sin(math.pi / 3) * q
                bms.append(bar(p, p + e * size * L, w * 0.75, t * 0.9, up=tuple(n)))
    if heart: bms.append(iq_hexplate(c, n, size * 0.2, t * 1.3, math.pi / 6))
    return iq_join(bms)

def iq_grid(fn, nu, nv, closed=True):
    """a surface fn(u, v) -> point: u across (round if closed), v along."""
    bm = bmesh.new(); rows = []
    cols = nu if closed else nu + 1
    for j in range(nv + 1):
        rows.append([bm.verts.new(fn(i / nu, j / nv)) for i in range(cols)])
    for j in range(nv):
        for i in range(nu):
            i2 = (i + 1) % nu if closed else i + 1
            bm.faces.new((rows[j][i], rows[j][i2], rows[j + 1][i2], rows[j + 1][i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm

def iq_normal(fn, u, v, e=1e-3):
    """the outward normal of the surface fn at (u, v), by finite differences."""
    a = fn(min(u + e, 1.0), v) - fn(max(u - e, 0.0), v)
    b = fn(u, min(v + e, 1.0)) - fn(u, max(v - e, 0.0))
    return a.cross(b).normalized()

def iq_skate(P, ankle, fwd, down, k=1.0):
    """a figure skate on the foot at ankle: a white leather boot laced in silver up the front, a steel blade under it on two stanchions,
    rockered, with the jagged toe pick at its front - fwd along the foot, down toward the ice."""
    a = Vector(ankle); f = Vector(fwd).normalized(); dn = Vector(down).normalized(); up = -dn; s = f.cross(up).normalized()
    # the boot: a shaft up the shin from the ankle, the heel behind, the foot running out to the toe
    P.obj("Boot", pipe([a + up * 0.17 * k, a + up * 0.06 * k, a - f * 0.02 * k, a + f * 0.12 * k + dn * 0.04 * k, a + f * 0.2 * k + dn * 0.05 * k],
                       [0.068 * k, 0.064 * k, 0.062 * k, 0.05 * k, 0.0], 12), "Belly")
    P.obj("Heel", ball(tuple(a - f * 0.05 * k + dn * 0.06 * k), (0.045 * k, 0.045 * k, 0.04 * k), 10, 5), "Belly")
    P.obj("BootCuff", pipe([a + up * 0.16 * k, a + up * 0.19 * k], [0.074 * k, 0.074 * k], 12), "Metal")
    for j in range(5):   # the lacing: silver crosses up the front, evenly
        p = a + f * (0.1 - 0.025 * j) * k + up * (-0.02 + 0.045 * j) * k + f * 0.05 * k
        P.obj("Lace", bar(p - s * 0.03 * k, p + s * 0.03 * k, 0.012 * k, 0.012 * k, up=tuple(f)), "Metal", 0, False)
    # the sole and the blade: a thin steel blade, rockered, held by two stanchions; the toe pick's teeth at the front
    sole = a + dn * 0.08 * k
    P.obj("Sole", pipe([sole - f * 0.07 * k, sole + f * 0.18 * k], [0.03 * k, 0.025 * k], 8), "Dark")
    for x in (-0.03, 0.13):
        P.obj("Stanchion", pipe([sole + f * x * k, sole + f * x * k + dn * 0.08 * k], [0.018 * k, 0.012 * k], 6), "Metal")
    pts = []
    for i in range(9):
        x = -0.12 + 0.36 * i / 8
        rock = 0.012 * ((x - 0.06) / 0.18) ** 2
        pts += [sole + f * x * k + dn * (0.075 - 0.0) * k, sole + f * x * k + dn * (0.12 - rock) * k]
    bl = []
    for p in pts: bl += [p + s * 0.008 * k, p - s * 0.008 * k]
    P.obj("Blade", hull([tuple(p) for p in bl]), "Metal", 0, False)
    for j in range(3):
        b = sole + f * (0.235 + 0.012 * j) * k + dn * (0.1 - 0.02 * j) * k
        P.obj("ToePick", cone(tuple(b), tuple(b + f * 0.03 * k + dn * 0.012 * k), 0.012 * k, 4), "Metal", 0, False)
    return sole + dn * 0.12 * k   # where the blade meets the ice

def iq_braid(P, path, r):
    """a three-strand braid along path: lobes crossing over left and right in turn, as a real plait does."""
    pts = path; n = len(pts)
    for i in range(1, n - 1):
        t = (pts[i + 1] - pts[i - 1]).normalized(); a, b = frame(t)
        q = 1 if i % 2 else -1
        rr = r * (1.0 - 0.45 * i / n)
        x = (t * math.cos(math.radians(35)) + a * q * math.sin(math.radians(35))).normalized()
        z = x.cross(b).normalized()
        P.obj("Braid", oriented_ball(tuple(pts[i] + a * q * rr * 0.35), (rr * 1.25, rr * 0.75, rr * 0.8), x, b, z, 10, 5), "Trim")
    P.obj("BraidCore", pipe(pts, [r * 0.6 * (1 - 0.45 * i / n) for i in range(n)], 8), "Trim")


def X_icequeen():
    """The last boss, the ICE QUEEN (2026-10-13, remade: "same as the alien bosses - realistic details, scarier, keep the cartoon shape"):
    the same tall snow queen in a royal blue gown with a crown of ice and a snowflake sceptre, now built with real ice and real frost, and
    cold and terrible. Pale blue skin; a narrow face with high cheekbones and a pointed chin; glowing ice-blue almond eyes slanted up at the
    corners under heavy dark lids, two thin severe brows that sweep low over the nose and up to sharp points, a thin straight mouth of dark
    lips. White-blonde hair swept back into a long three-strand plait that falls over her right shoulder to her waist, tied with silver and a
    bead of ice. Her crown is grown, not forged: twelve real ice crystals - six-sided prisms with six-sided points - stand round a silver
    circlet, tallest at the front over a glowing jewel and graded down toward the back. A high stand-up collar of ice rises behind her head,
    eleven crystals fanned from a frosted band, tallest in the middle. A royal blue bodice with a silver neckline, a glowing crystal brooch
    and three silver snowflakes embroidered down the front; long fitted sleeves with bell cuffs of frost; a skating dress of three tiers of
    frost - blue at the waist, then clear ice, then white rime at the hem - each tier's hem scalloped like frost petals and embroidered with
    a ring of real six-fold snowflakes (stellar dendrites, every arm with its two pairs of side branches) in silver; a long cape of ice
    streaming behind her from the shoulders, white frost along its edges and two rows of silver snowflakes on it, swaying as she goes
    (SwayCape). In her raised right hand a silver sceptre crowned with a great six-fold snowflake around a glowing crystal heart; in her left,
    held out at the player, frost forming in her open palm: a glowing core with six crystals growing from it, where her shots leave.
    SHE SKATES ON A ROAD OF ICE SHE FREEZES IN THE AIR: she glides toward the player in a skater's arabesque - leaning into it, the right
    leg bent under her on its blade, the left stretched out behind with the foot pointed - on real figure skates (white boots laced in
    silver, steel blades on stanchions, rockered, a jagged toe pick at the front). Under her blade a road of clear ice sweeps down out of
    the sky behind her and curves away to her left: a ribbon of ice with frosted rime along both edges and pressure cracks across it at
    even intervals, glowing where it is newest under her blade and just ahead of it, where it is still freezing; the older the ice, the
    longer the icicles hanging in rows under its edges. Ice dust sprays off her blade in a fan of six-sided chips."""
    P = Boss("icequeen", {"Base": ((0.10, 0.25, 0.66), 0.55), "Belly": ((0.93, 0.96, 1.0), 0.35), "Accent": ((0.70, 0.83, 0.97), 0.4),
                          "Trim": ((0.98, 0.95, 0.84), 0.45), "Glass": ((0.56, 0.84, 1.0), 0.95), "Dark": ((0.03, 0.05, 0.15), 0.5),
                          "Glow": ((0.30, 0.85, 1.0), 0.5), "Metal": ((0.80, 0.85, 0.95), 0.9), "Lamp": ((0.75, 0.97, 1.0), 0.8)})
    n0 = len(P.parts)
    # ---- the legs and skates: the right leg bent under her on the ice, the left stretched behind in an arabesque, the foot pointed
    hipR, hipL = Vector((0.1, 0.0, -0.26)), Vector((-0.1, -0.02, -0.26))
    kneeR, ankR = Vector((0.12, 0.17, -0.66)), Vector((0.13, 0.06, -1.0))
    kneeL, ankL = Vector((-0.13, -0.48, -0.42)), Vector((-0.15, -0.92, -0.4))
    P.obj("Leg", pipe(bez(hipR, hipR + Vector((0, 0.12, -0.18)), kneeR + Vector((0, 0.04, 0.12)), kneeR, 5) + bez(kneeR, kneeR + Vector((0, -0.02, -0.12)), ankR + Vector((0, 0.04, 0.12)), ankR, 5)[1:],
                      [0.095, 0.092, 0.088, 0.082, 0.074, 0.066, 0.062, 0.058, 0.054, 0.05, 0.048], 12), "Base")
    P.obj("Leg", pipe(bez(hipL, hipL + Vector((0, -0.16, -0.08)), kneeL + Vector((0, 0.14, 0.02)), kneeL, 5) + bez(kneeL, kneeL + Vector((0, -0.14, 0.0)), ankL + Vector((0, 0.16, -0.02)), ankL, 5)[1:],
                      [0.095, 0.092, 0.088, 0.082, 0.074, 0.066, 0.062, 0.058, 0.054, 0.05, 0.048], 12), "Base")
    B = iq_skate(P, ankR, (0.06, 1.0, 0.0), (0, 0, -1))                  # the gliding blade on the road
    iq_skate(P, ankL, (0.0, -1.0, -0.35), (0, 0.33, -1))                # the free foot, pointed behind
    # ---- the skating dress: three tiers of frost, scalloped at the hems, each embroidered with a ring of silver snowflakes
    tiers = [(0.03, 0.19, -0.17, 0.3, 0.035, "Base"), (-0.1, 0.26, -0.36, 0.41, 0.04, "Glass"), (-0.25, 0.34, -0.56, 0.52, 0.05, "Belly")]
    for ti, (zt, rt, zb, rb, sc, slot) in enumerate(tiers):
        def skirt(u, v, zt=zt, rt=rt, zb=zb, rb=rb, sc=sc, ti=ti):
            a = 2 * math.pi * u + ti * math.pi / 12
            r = rt + (rb - rt) * v ** 0.8
            z = zt + (zb - zt) * v - sc * (0.5 + 0.5 * math.cos(12 * a)) * v ** 4
            return Vector((math.cos(a) * r, math.sin(a) * r * 0.92, z))
        P.obj("Skirt", sheet_solid(iq_grid(skirt, 72, 6), 0.022), slot, 0, True)
        for k in range(12):   # a snowflake over every scallop's point
            u = k / 12; p = skirt(u, 0.62); nrm = iq_normal(skirt, u, 0.62)
            if nrm.dot(Vector((p.x, p.y, 0))) < 0: nrm = -nrm
            P.obj("Embroidery", iq_flake(p + nrm * 0.02, nrm, (0, 0, 1), 0.055 + 0.01 * ti, 0.012), "Metal", 0, False)
    # ---- the bodice: royal blue, a silver neckline, a glowing crystal brooch, three silver snowflakes down the front
    bod = lathe([(0.0, -0.02), (0.18, -0.02), (0.17, 0.08), (0.2, 0.24), (0.215, 0.32), (0.2, 0.42), (0.12, 0.5), (0.0, 0.52)], 24, "z")
    for v in bod.verts: v.co.y *= 0.78
    P.obj("Bodice", bod, "Base")
    P.obj("Waist", xf(torus(0.18, 0.022, 0.0, 28, 6), Matrix.Diagonal((1, 0.8, 1))), "Metal")
    for s in (1, -1):
        P.obj("Neckline", pipe(bez((s * 0.19, 0.06, 0.45), (s * 0.12, 0.15, 0.4), (s * 0.04, 0.17, 0.34), (0, 0.17, 0.31), 6), [0.014] * 7, 6), "Metal")
    P.obj("Brooch", iq_crystal((0, 0.155, 0.31), (0, 1, 0.15), 0.035, 0.03, 0.04), "Lamp")
    for j, z in enumerate((0.2, 0.1, 0.0)):
        y = 0.165 if z > 0.15 else 0.14
        P.obj("Embroidery", iq_flake((0, y + 0.012, z), (0, 1, 0.1), (0, 0, 1), 0.045 - 0.006 * j, 0.01), "Metal", 0, False)
    # ---- the arms: long fitted sleeves with bell cuffs of frost; the right raises the sceptre, the left holds out the frost in her palm
    shR, shL = Vector((0.24, -0.02, 0.44)), Vector((-0.24, -0.02, 0.44))
    for s, sh in ((1, shR), (-1, shL)):
        P.obj("Shoulder", ball(tuple(sh + Vector((s * 0.02, 0, 0.01))), (0.08, 0.075, 0.07), 12, 6), "Base")
    elR, wrR = Vector((0.46, 0.06, 0.6)), Vector((0.6, 0.12, 0.84))
    elL, wrL = Vector((-0.5, 0.1, 0.38)), Vector((-0.72, 0.3, 0.4))
    for s, sh, el, wr in ((1, shR, elR, wrR), (-1, shL, elL, wrL)):
        P.obj("Sleeve", pipe(bez(sh, sh + (el - sh) * 0.4, el - (wr - el) * 0.2, el, 4) + bez(el, el + (wr - el) * 0.3, wr - (wr - el) * 0.3, wr, 4)[1:],
                             [0.07, 0.066, 0.06, 0.056, 0.052, 0.048, 0.044, 0.042, 0.04], 10), "Base")
        d = (wr - el).normalized()
        P.obj("Cuff", xf(lathe([(0.04, -0.02), (0.05, 0.0), (0.085, 0.09), (0.082, 0.1), (0.045, 0.02)], 12, "z"), iq_rot(d), tuple(wr - d * 0.09)), "Belly")
        a, b = frame(d)
        for k in range(6):   # the cuff's rim breaks into six little icicles
            ang = 2 * math.pi * k / 6
            p = wr + d * 0.005 + (a * math.cos(ang) + b * math.sin(ang)) * 0.08
            P.obj("CuffIce", cone(tuple(p), tuple(p + d * 0.06 + (a * math.cos(ang) + b * math.sin(ang)) * 0.01), 0.014, 4), "Glass", 0, False)
    # the right hand round the sceptre: a silver staff, a great six-fold snowflake on top round a glowing crystal heart
    P.obj("Hand", ball(tuple(wrR + Vector((0.03, 0.02, 0.05))), (0.045, 0.045, 0.06), 10, 5), "Accent")
    sx, sy = 0.64, 0.15
    P.obj("Sceptre", pipe([(sx, sy, 0.3), (sx, sy, 1.44)], [0.022, 0.022], 8), "Metal")
    for z in (0.32, 1.42):
        P.obj("SceptreRing", xf(torus(0.032, 0.012, 0.0, 12, 5), None, (sx, sy, z)), "Metal")
    P.obj("SceptrePommel", iq_crystal((sx, sy, 0.31), (0, 0, -1), 0.03, 0.04), "Glass")
    for k in range(3):    # the prongs that hold the snowflake
        a = math.radians(90 + 120 * k)
        P.obj("Prong", pipe(bez((sx, sy, 1.43), (sx + math.cos(a) * 0.04, sy + math.sin(a) * 0.02, 1.47), (sx + math.cos(a) * 0.05, sy + math.sin(a) * 0.02, 1.52), (sx, sy, 1.55), 4), [0.012, 0.011, 0.01, 0.008, 0.0], 5), "Metal")
    P.obj("Snowflake", iq_flake((sx, sy + 0.01, 1.66), (0, 1, 0), (0, 0, 1), 0.22, 0.035, heart=False), "Lamp", 0, False)
    P.obj("FlakeHeart", iq_hexplate((sx, sy + 0.01, 1.66), (0, 1, 0), 0.05, 0.06, math.pi / 6), "Glow", 0, False)
    # the left hand held out, palm to the player, and frost forming in it: a glowing core with six crystals growing out evenly
    P.obj("Hand", ball(tuple(wrL + Vector((-0.04, 0.05, 0.0))), (0.045, 0.035, 0.06), 10, 5), "Accent")
    for j in range(4):   # long fingers curled up round the frost
        f0 = wrL + Vector((-0.06 + 0.025 * j, 0.08, 0.04 - 0.0 * j))
        P.obj("Finger", pipe(bez(f0, f0 + Vector((-0.01, 0.04, 0.03)), f0 + Vector((-0.01, 0.07, 0.08)), f0 + Vector((-0.0, 0.07, 0.12)), 4), [0.014, 0.013, 0.012, 0.01, 0.0], 6), "Accent")
    orb = wrL + Vector((-0.05, 0.16, 0.08))
    P.obj("Frost", ball(tuple(orb), (0.06, 0.06, 0.06), 12, 6), "Glow")
    for k in range(6):
        a = 2 * math.pi * k / 6
        d = Vector((math.cos(a), 0.35, math.sin(a))).normalized()
        P.obj("FrostCrystal", iq_crystal(tuple(orb + d * 0.03), tuple(d), 0.02, 0.06 + 0.02 * (k % 2)), "Glass")
    # ---- the neck, the head, the face
    P.obj("Neck", pipe([(0, -0.01, 0.47), (0, 0.0, 0.66)], [0.055, 0.05], 10), "Accent")
    hc = Vector((0, 0.02, 0.83))
    P.obj("Head", ball(tuple(hc), (0.15, 0.16, 0.19), 18, 10), "Accent")
    P.obj("Chin", ball(tuple(hc + Vector((0, 0.07, -0.12))), (0.075, 0.075, 0.075), 12, 6), "Accent")
    for s in (1, -1):
        P.obj("Cheekbone", ball(tuple(hc + Vector((s * 0.085, 0.115, -0.03))), (0.05, 0.04, 0.03), 10, 5), "Accent")
        e = hc + Vector((s * 0.062, 0.145, 0.015))
        x = Vector((s * math.cos(math.radians(18)), -0.25 * s * 0.0, math.sin(math.radians(18)))).normalized()
        if s < 0: x = Vector((math.cos(math.radians(18)), 0, -math.sin(math.radians(18)))).normalized()
        yv = Vector((0, 1, 0)); zv = x.cross(yv).normalized(); yv = zv.cross(x).normalized()
        P.obj("Socket", oriented_ball(tuple(e - yv * 0.008), (0.05, 0.012, 0.027), x, yv, zv, 12, 6), "Dark")
        P.obj("Eye", oriented_ball(tuple(e + yv * 0.002), (0.04, 0.012, 0.019), x, yv, zv, 12, 6), "Glass")
        P.obj("Iris", oriented_ball(tuple(e + yv * 0.009), (0.019, 0.01, 0.017), x, yv, zv, 10, 5), "Glow")
        P.obj("Pupil", ball(tuple(e + yv * 0.016), (0.005, 0.005, 0.013), 6, 3), "Dark")
        # the heavy upper lid slanting down toward the nose, and the brow: low over the nose, sweeping up to a sharp point
        P.obj("Lid", bar(e + Vector((s * 0.045, 0.002, 0.025)), e + Vector((-s * 0.035, 0.012, 0.004)), 0.014, 0.012, up=(0, 1, 0.2)), "Dark", 0, False)
        P.obj("Brow", pipe([hc + Vector((s * 0.018, 0.168, 0.06)), hc + Vector((s * 0.07, 0.158, 0.075)), hc + Vector((s * 0.13, 0.12, 0.11))], [0.009, 0.008, 0.0], 6), "Dark")
    P.obj("Nose", hull([tuple(hc + Vector(p)) for p in ((0, 0.182, -0.03), (0.015, 0.162, -0.045), (-0.015, 0.162, -0.045), (0, 0.16, 0.02), (0, 0.172, -0.05))]), "Accent", 0, False)
    P.obj("Lips", oriented_ball(tuple(hc + Vector((0, 0.152, -0.087))), (0.04, 0.01, 0.009), Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1)), 10, 5), "Dark")
    P.obj("Lips", oriented_ball(tuple(hc + Vector((0, 0.148, -0.099))), (0.03, 0.01, 0.008), Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1)), 10, 5), "Dark")
    # the hair: white-blonde, swept back off the face into the plait
    P.obj("Hair", ball(tuple(hc + Vector((0, -0.04, 0.035))), (0.163, 0.17, 0.2), 18, 9), "Trim")
    P.obj("Hair", ball(tuple(hc + Vector((0, -0.13, -0.06))), (0.12, 0.09, 0.12), 12, 6), "Trim")
    for s in (1, -1):   # a lock at each temple, swept back over the ear to the plait
        P.obj("Lock", pipe(bez(hc + Vector((s * 0.11, 0.1, 0.12)), hc + Vector((s * 0.165, 0.06, 0.02)), hc + Vector((s * 0.16, -0.04, -0.08)), hc + Vector((s * 0.06, -0.15, -0.1)), 8),
                           [0.028, 0.036, 0.04, 0.04, 0.038, 0.034, 0.03, 0.025, 0.02], 8), "Trim")
    path = bez(hc + Vector((0.05, -0.16, -0.08)), hc + Vector((0.22, -0.12, -0.25)), Vector((0.28, 0.12, 0.38)), Vector((0.2, 0.2, 0.0)), 12)
    path += bez(Vector((0.2, 0.2, 0.0)), Vector((0.17, 0.22, -0.1)), Vector((0.16, 0.24, -0.16)), Vector((0.15, 0.25, -0.22)), 3)[1:]
    iq_braid(P, path, 0.05)
    P.obj("BraidTie", xf(torus(0.03, 0.01, 0.0, 12, 5), iq_rot(path[-1] - path[-2]), tuple(path[-2])), "Metal")
    P.obj("BraidBead", iq_crystal(tuple(path[-1]), tuple(path[-1] - path[-2]), 0.022, 0.03), "Glass")
    # ---- the crown: twelve ice crystals round a silver circlet, tallest at the front over a glowing jewel
    cc = hc + Vector((0, -0.015, 0.155)); tilt = Matrix.Rotation(math.radians(-14), 3, "X")
    P.obj("Circlet", xf(torus(0.15, 0.016, 0.0, 28, 6), tilt, tuple(cc)), "Metal")
    for k in range(12):
        a = 2 * math.pi * k / 12
        rad = Vector((math.sin(a), math.cos(a), 0)); base = cc + tilt @ (rad * 0.15)
        h = 0.07 + 0.2 * (0.5 + 0.5 * math.cos(a)) ** 1.5
        ax = (tilt @ Vector((0, 0, 1)) + rad * 0.3).normalized()
        P.obj("CrownIce", iq_crystal(tuple(base), tuple(ax), 0.022 + 0.008 * (0.5 + 0.5 * math.cos(a)), h, twist=a), "Glass")
    P.obj("CrownJewel", iq_crystal(tuple(cc + tilt @ Vector((0, 0.165, 0.005))), (0, 1, 0.2), 0.03, 0.02, 0.03), "Lamp")
    # ---- the stand-up collar of ice behind her head: eleven crystals fanned from a frosted band, tallest in the middle
    band = []
    for k in range(11):
        a = math.radians(-100 + 20 * k)
        base = Vector((math.sin(a) * 0.17, -math.cos(a) * 0.12 - 0.02, 0.5 + 0.02 * math.cos(a)))
        band.append(base)
        out = Vector((math.sin(a), -math.cos(a), 0))
        ax = (Vector((0, 0, 1)) + out * 0.55 + Vector((0, -0.25, 0))).normalized()
        P.obj("CollarIce", iq_crystal(tuple(base), tuple(ax), 0.03, 0.18 + 0.2 * math.cos(a) ** 2, twist=a), "Glass")
    P.obj("CollarBand", pipe(band, [0.035] * len(band), 8), "Belly")
    # ---- the cape of ice streaming back from her shoulders, frosted at the edges, two rows of silver snowflakes; it sways
    hub = Vector((0, -0.1, 0.46))
    def cape(u, v):
        x = (-0.24 + 0.48 * u) * (1 + 1.3 * v)
        y = -0.12 - 0.22 * v - 0.75 * v * v - 0.13 * math.sin(5 * math.pi * u) * v ** 0.8
        z = 0.47 - 1.55 * v + 0.3 * v * v
        return Vector((x, y, z))
    def cape_paint(c, n):
        return "Belly" if abs(c.x) > 0.24 * (1 + 1.3 * max(0.0, (0.47 - c.z) / 1.3)) - 0.06 or c.z < -0.66 else "Glass"
    P.part("SwayCape", sheet_solid(iq_grid(cape, 24, 14, False), 0.025), cape_paint, tuple(hub))
    for v, us in ((0.4, (0.2, 0.5, 0.8)), (0.7, (0.12, 0.37, 0.63, 0.88))):
        for u in us:
            p = cape(u, v); nrm = -iq_normal(cape, u, v)
            if nrm.y > 0: nrm = -nrm
            P.part("SwayCape", iq_flake(p + nrm * 0.018, nrm, (0, 0, 1), 0.08, 0.014), "Metal", tuple(hub))
    # ---- lean her into the glide, about the blade on the ice
    R = Matrix.Rotation(math.radians(-12), 4, "X"); M4 = Matrix.Translation(B) @ R @ Matrix.Translation(-B)
    for ob in P.parts[n0:]: ob.data.transform(M4)
    for ob in P.spin:
        ob.location = M4 @ ob.location; ob.data.transform(R)
    B = M4 @ B
    # ---- the road of ice: down out of the sky behind her, under her blade, a little way ahead where it is still freezing
    back = bez((-1.2, -2.25, 0.3), (-1.4, -1.15, -1.15), (-0.45, -0.75, B.z - 0.06), tuple(B), 22)
    ahead = bez(tuple(B), tuple(B + Vector((0.03, 0.25, 0.0))), tuple(B + Vector((0.07, 0.48, 0.02))), tuple(B + Vector((0.1, 0.62, 0.03))), 5)[1:]
    path = back + ahead; nb = len(back) - 1; n = len(path)
    W, TH = 0.46, 0.08
    rings, frames = [], []
    for i, p in enumerate(path):
        t = (path[min(i + 1, n - 1)] - path[max(i - 1, 0)]).normalized()
        s = t.cross(Vector((0, 0, 1))).normalized(); nr = s.cross(t).normalized()
        frames.append((t, s, nr))
    def section(i):
        p = path[i]; t, s, nr = frames[i]
        w = W * (0.85 + 0.15 * min(1.0, i / nb)) * (1.0 if i <= nb else 1.0 - 0.45 * (i - nb) / (n - 1 - nb))
        th = TH * (1.0 if i <= nb else 0.7)
        sec = [(-0.5, 0.0), (0.5, 0.0), (0.53, -0.4), (0.47, -1.0), (-0.47, -1.0), (-0.53, -0.4)]
        return [p + s * w * a + nr * th * b for a, b in sec], w, th
    bm = bmesh.new()
    rr = []
    for i in range(n):
        pts, w, th = section(i)
        rr.append([bm.verts.new(q) for q in pts])
    skin(bm, rr, 6)
    newest = path[nb - 4].y
    def road_paint(c, nrm):
        return "Glow" if nrm.z > 0.5 and c.y > newest else "Glass"
    P.obj("Road", bm, road_paint, 0, False)
    for side in (-1, 1):   # the rime along both edges
        rim = []
        for i in range(n):
            pts, w, th = section(i); t, s, nr = frames[i]
            rim.append(path[i] + s * w * 0.5 * side + nr * 0.005)
        P.obj("Rime", pipe(rim, [0.028 * (0.6 if i > nb else 1.0) for i in range(n)], 6), "Belly")
    for i in range(2, nb - 1, 3):   # pressure cracks across the road at even intervals, from one edge then the other
        t, s, nr = frames[i]; pts, w, th = section(i); q = 1 if (i // 3) % 2 else -1
        a0 = path[i] + s * q * w * 0.5 + nr * 0.004
        a1 = a0 - s * q * w * 0.22 + t * 0.04
        a2 = a1 - s * q * w * 0.18 - t * 0.05
        a3 = a2 - s * q * w * 0.14 + t * 0.03
        for a, b in ((a0, a1), (a1, a2), (a2, a3)):
            P.obj("Crack", bar(a, b, 0.012, 0.006, up=tuple(nr)), "Belly", 0, False)
    for i in range(1, nb - 1):   # icicles in rows under both edges: the older the ice, the longer they have grown
        age = 1.0 - i / nb
        if age < 0.12: continue
        t, s, nr = frames[i]; pts, w, th = section(i)
        for side in (-1, 1):
            L = (0.08 + 0.42 * age) * (1.0 if (i + (side > 0)) % 2 else 0.6)
            b = path[i] + s * side * w * 0.44 - nr * th * 0.95
            P.obj("Icicle", pipe([b, b + Vector((0, 0, -L * 0.5)), b + Vector((0, 0, -L))], [0.03, 0.017, 0.0], 6), "Glass", 0, False)
    # ---- the ice dust spraying off her blade, out to her right and back: a fan of six-sided chips, smaller as they fly
    chips = []
    for arc in range(3):
        for k in range(1, 6):
            f = k / 5
            p = B + Vector((0.08 + 0.42 * f, -0.06 - 0.25 * f - 0.1 * arc, 0.05 + 0.22 * f * (1.4 - f) + 0.04 * arc))
            chips.append(iq_hexplate(p, (0.4, -0.3, 1.0), 0.04 * (1.15 - f) * (1 - 0.15 * arc), 0.012, k * 0.7))
    P.obj("Cloth", iq_join(chips), "Lamp", 0, False)
    # ---- her shots leave from the frost in her palm
    mz = M4 @ (orb + Vector((0, 0.07, 0)))
    P.part("Muzzle", ball(tuple(mz), (0.05, 0.03, 0.05), 8, 4), "Glow", tuple(mz))
    return P


BOSSES = [("sleigh", X_sleigh), ("snowman", X_snowman), ("nutcracker", X_nutcracker), ("icequeen", X_icequeen), ("krampus", X_krampus)]

if __name__ == "__main__":
    os.makedirs(AB.OUT, exist_ok=True)
    for bid, fn in BOSSES:
        if ONLY and bid not in ONLY: continue
        fn().finish()
    print("DONE")
