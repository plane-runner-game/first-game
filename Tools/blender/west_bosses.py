# Sky Squad, the wild west's five bosses (2026-10-11: "the rest of the bosses for the maps that don't have them yet"): the thunderbird, the
# sheriff robot, the rattlesnake, the outlaw zeppelin and the gold mine mesa. Built from code like the other worlds' bosses (alien_bosses.py
# lends its Boss class and shapes).
# 2026-10-14, the five in play remade like the alien / autumn bosses (W2_*: real anatomy, scarier faces, the cartoon idea kept) and each given
# its own way to fly: the thunderbird on its own wings, the sheriff robot on steam thrusters, the rattlesnake rides a dynamite rocket, the
# scorpion king rides a tumbleweed, the ghost rider gallops across a storm cloud. In Unity: Sky Squad > Rebuild West Bosses after an export.
# Run: blender -b -P Tools/blender/west_bosses.py -- <out dir> [export] [ids,comma,separated]
# Conventions as alien_bosses.py: +Y nose, +Z up, +X right; "Prop*" spin about the nose, "Flap*" rock about the nose axis, "Sway*" about the
# wing axis, "Spin*" turn slowly about up, "Roll*" turn slowly about the nose axis (face-on), "Muzzle" is where his shots leave from.
import bpy, bmesh, math, sys, os, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mathutils import Vector, Matrix
from enemy_planes import loft, sweep, lathe, box, hull, tube, mirror_x, airfoil
import alien_bosses as AB
from alien_bosses import Boss, xf, ball, pipe, cone, bez, torus, sheet, grow, ang

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ONLY = argv[2].split(",") if len(argv) > 2 and argv[2] else None

RED = ((0.78, 0.12, 0.07), 0.5)
GOLD = ((0.98, 0.74, 0.20), 0.8)
BRASS = ((0.86, 0.62, 0.26), 0.8)
WOOD = ((0.36, 0.20, 0.10), 0.35)


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

def star(c, R, r, depth, n=5, axis="y"):
    """a flat five-pointed star facing +Y (axis y) or up (axis z)."""
    c = Vector(c); pts = []
    for k in range(2 * n):
        a = math.pi * k / n; rr = R if k % 2 == 0 else r
        u, v = math.sin(a) * rr, math.cos(a) * rr
        for d in (-depth * 0.5, depth * 0.5):
            pts.append(c + (Vector((u, d, v)) if axis == "y" else Vector((u, v, d))))
    bm = bmesh.new(); vs = [bm.verts.new(p) for p in pts]
    front = [vs[2 * k + 1] for k in range(2 * n)]; back = [vs[2 * k] for k in range(2 * n)]
    bm.faces.new(front); bm.faces.new(list(reversed(back)))
    for k in range(2 * n):
        j = (k + 1) % (2 * n)
        bm.faces.new((back[k], back[j], front[j], front[k]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm

def gear(c, R, teeth, depth, axis="y"):
    """a cog facing +Y: a disc with square teeth round it."""
    c = Vector(c); bm = bmesh.new()
    def put(b2, m, t):
        for v in b2.verts: v.co = m @ v.co + t
        return b2
    rot = Matrix.Rotation(math.radians(90), 3, "X") if axis == "y" else Matrix.Identity(3)
    parts = [put(lathe([(0.0, -depth * 0.5), (R, -depth * 0.5), (R, depth * 0.5), (0.0, depth * 0.5)], 24, "z"), rot, c)]
    for k in range(teeth):
        a = 2 * math.pi * k / teeth
        t = box((0, 0, 0), (R * 0.28, R * 0.3, depth * 0.9))
        parts.append(put(t, rot @ Matrix.Rotation(-a, 3, "Z"), c + rot @ (Matrix.Rotation(-a, 3, "Z") @ Vector((0, R * 1.08, 0)))))
    out = bmesh.new()
    for p in parts:
        me = bpy.data.meshes.new("tmp"); p.to_mesh(me); p.free(); out.from_mesh(me); bpy.data.meshes.remove(me)
    return out

def bolt(pts, w, thick=0.05):
    """a zigzag lightning bolt along pts (in a vertical plane), as flat prisms."""
    out = bmesh.new()
    for a, b in zip(pts, pts[1:]):
        a, b = Vector(a), Vector(b); d = (b - a); side = d.cross(Vector((0, 1, 0)))
        side = side.normalized() * w if side.length > 1e-4 else Vector((w, 0, 0))
        q = hull([tuple(a + side), tuple(a - side), tuple(b + side * 0.7), tuple(b - side * 0.7),
                  tuple(a + side + Vector((0, thick, 0))), tuple(b + side * 0.7 + Vector((0, thick, 0))),
                  tuple(a - side + Vector((0, thick, 0))), tuple(b - side * 0.7 + Vector((0, thick, 0)))])
        me = bpy.data.meshes.new("tmp"); q.to_mesh(me); q.free(); out.from_mesh(me); bpy.data.meshes.remove(me)
    return out

def hat(c, k=1.0, tilt=0.0):
    """a cowboy hat: a dented crown on a brim curled up at the sides."""
    c = Vector(c)
    crown = lathe([(0.0, 0.0), (0.26, 0.0), (0.25, 0.2), (0.2, 0.3), (0.0, 0.26)], 16, "z")
    for v in crown.verts:
        v.co.y *= 1.15
        if v.co.z > 0.22 and abs(v.co.x) < 0.08: v.co.z -= 0.05   # the dent
    brim = lathe([(0.0, -0.01), (0.5, 0.0), (0.56, 0.06), (0.5, 0.03), (0.0, 0.02)], 22, "z")
    for v in brim.verts:
        v.co.y *= 1.12
        v.co.z += (abs(v.co.x) / 0.56) ** 3 * 0.16 * (1.0 if abs(v.co.x) > 0.1 else 0.0)
    band = lathe([(0.265, 0.02), (0.262, 0.08), (0.0, 0.08)], 16, "z")
    for v in band.verts: v.co.y *= 1.15
    m = Matrix.Rotation(tilt, 3, "X")
    return [xf(grow(b, (0, 0, 0), k), m, c) for b in (crown, brim, band)]


# ================================================================= 1. the thunderbird
def W_thunderbird():
    """The thunderbird of the plains (2026-10-12, remade: "edit it, make it better"): a great storm eagle, wings spread wide and painted
    with totem bands of red, gold and turquoise triangles, glowing lightning zigzags and layered covert feathers; a fierce head with a
    heavy brow, blazing eyes, a hooked golden beak open on a glowing throat, and a war bonnet of long feathers fanned round it on a
    beaded band; a chest painted with totem chevrons and a turquoise sun medallion, a fanned tail with eye patterns, a lightning bolt
    gripped in its golden talons, and a ring of lightning bolts and feathers whirling round it."""
    P = Boss("thunderbird", {"Base": ((0.08, 0.20, 0.45), 0.5), "Belly": ((0.97, 0.93, 0.84), 0.35), "Accent": RED, "Trim": GOLD,
                             "Glass": ((0.10, 0.72, 0.68), 0.7), "Dark": ((0.04, 0.05, 0.08), 0.5), "Glow": ((0.45, 0.95, 1.0), 0.5),
                             "Metal": ((0.55, 0.32, 0.16), 0.4), "Lamp": ((1.0, 0.85, 0.25), 0.8)})
    def chest(c, n):
        if n.z < -0.45: return "Belly"
        if n.y > 0.35:   # totem chevrons down the front
            v = (c.z * 4.0 + abs(c.x) * 3.0) % 1.0
            return "Accent" if v < 0.22 else ("Trim" if v < 0.36 else ("Glass" if v < 0.5 else "Base"))
        return "Base"
    P.obj("Body", ball((0, 0.0, 0.0), (0.58, 1.0, 0.5), 18, 9), chest, 1)
    P.obj("Chest", ball((0, 0.55, -0.05), (0.4, 0.38, 0.4), 14, 7), chest, 1)
    for row in range(3):   # layered breast feathers
        for k in range(7):
            a = math.radians(-60 + k * 20)
            b = Vector((math.sin(a) * 0.38, 0.7 + math.cos(a) * 0.1, 0.12 - row * 0.2))
            P.obj("BreastFeather", cone(b, b + Vector((math.sin(a) * 0.05, 0.08, -0.2)), 0.08, 4), "Belly" if row % 2 else "Trim", 0, False)
    P.obj("Medallion", lathe([(0.0, 0.0), (0.16, 0.0), (0.16, 0.04), (0.0, 0.05)], 18, "y", (0, 0.92, -0.08)), "Trim")
    P.obj("Sun", ball((0, 0.97, -0.08), (0.11, 0.025, 0.11), 12, 5), "Glass")
    for k in range(8):
        a = 2 * math.pi * k / 8
        P.obj("SunRay", cone((math.sin(a) * 0.15, 0.95, -0.08 + math.cos(a) * 0.15), (math.sin(a) * 0.27, 0.93, -0.08 + math.cos(a) * 0.27), 0.04, 4), "Trim", 0, False)
    # the head: fierce, a heavy brow, blazing eyes, an open hooked beak with a glowing throat (drawn 1.35 times bigger about the neck)
    n0 = len(P.parts)
    P.obj("Head", ball((0, 1.08, 0.42), (0.33, 0.36, 0.3), 16, 8), lambda c, n: "Belly" if n.z < -0.4 else "Base", 1)
    P.obj("Mask", ball((0, 1.16, 0.46), (0.33, 0.25, 0.14), 14, 6), "Belly", 1)
    P.obj("UpperBeak", hull([(0.14, 1.3, 0.55), (-0.14, 1.3, 0.55), (0.13, 1.3, 0.36), (-0.13, 1.3, 0.36), (0.06, 1.62, 0.5), (-0.06, 1.62, 0.5),
                             (0.0, 1.78, 0.38), (0.0, 1.72, 0.22), (0.0, 1.6, 0.34)]), "Trim", 0, False)
    P.obj("LowerBeak", hull([(0.11, 1.3, 0.3), (-0.11, 1.3, 0.3), (0.09, 1.3, 0.2), (-0.09, 1.3, 0.2), (0.0, 1.58, 0.18), (0.0, 1.55, 0.12)]), "Trim", 0, False)
    P.obj("Throat", ball((0, 1.38, 0.3), (0.09, 0.14, 0.05), 10, 5), "Glow")
    P.obj("Cere", ball((0, 1.33, 0.52), (0.13, 0.06, 0.07), 10, 5), "Lamp")
    for s in (1, -1):
        P.obj("Socket", ball((s * 0.17, 1.27, 0.55), (0.1, 0.06, 0.08), 10, 5), "Dark")
        P.obj("Eye", ball((s * 0.17, 1.3, 0.55), (0.075, 0.04, 0.06), 10, 5), "Lamp")
        P.obj("Pupil", ball((s * 0.17, 1.33, 0.55), (0.03, 0.02, 0.04), 6, 3), "Dark")
        P.obj("Brow", hull([(s * 0.03, 1.33, 0.68), (s * 0.36, 1.18, 0.74), (s * 0.36, 1.12, 0.66), (s * 0.05, 1.3, 0.6), (s * 0.2, 1.3, 0.73)]), "Dark", 0, False)
        P.obj("FacePaint", hull([(s * 0.22, 1.22, 0.45), (s * 0.34, 1.12, 0.42), (s * 0.3, 1.1, 0.32), (s * 0.24, 1.2, 0.4)]), "Accent", 0, False)
    # the war bonnet: a beaded band and long feathers fanned round the head, red tipped
    band = torus(0.32, 0.045, 0.0, 22, 6)
    xf(band, Matrix.Rotation(math.radians(-25), 3, "X"), (0, 1.02, 0.62))
    P.obj("Band", band, lambda c, n: "Glass" if (ang(c - Vector((0, 1.02, 0))) * 3) % 1.0 < 0.5 else "Trim")
    for k in range(13):
        a = math.radians(-100 + k * (200 / 12))
        root = Vector((math.sin(a) * 0.3, 0.98 - abs(math.sin(a)) * 0.05, 0.66 + math.cos(a) * 0.12))
        d = Vector((math.sin(a) * 0.9, -0.55, math.cos(a) * 0.75 + 0.35)).normalized()
        L = 0.95 - abs(k - 6) * 0.04
        P.obj("Bonnet", pipe([root, root + d * L * 0.5, root + d * L], [0.035, 0.08, 0.0], 6),
              lambda c, n, r=root, L=L: "Dark" if (c - r).length > L * 0.78 else ("Accent" if (c - r).length > L * 0.62 else "Belly"), 0)
        P.obj("Bead", ball(tuple(root), (0.045, 0.045, 0.045), 6, 3), "Glass" if k % 2 else "Accent")
    big = Matrix.Translation((0, 0.95, 0.35)) @ Matrix.Scale(1.35, 4) @ Matrix.Translation((0, -0.95, -0.35))
    for ob in P.parts[n0:]: ob.data.transform(big)
    # the wings: storm blue, totem bands of triangles, glowing lightning, layered coverts, spread primaries
    def zig(x): t = (x * 1.3) % 1.0; return -0.3 + 0.45 * (t * 2 if t < 0.5 else 2 - t * 2)
    for s in (1, -1):
        name = "FlapR" if s > 0 else "FlapL"
        hub = Vector((s * 0.38, 0.1, 0.22))
        keys = [(0.3, 0.8, -0.8, 0.22, 0.2), (0.9, 0.9, -1.15, 0.16, 0.3), (1.6, 0.85, -1.2, 0.12, 0.4), (2.3, 0.62, -1.05, 0.08, 0.5), (2.7, 0.3, -0.75, 0.04, 0.55)]
        bm = sweep([(x, airfoil(le, te, th, z)) for (x, le, te, th, z) in fine(keys, 0.06)], "x")
        if s < 0: bm = mirror_x(bm)
        def wpaint(c, n):
            x = abs(c.x)
            if n.z < -0.3: return "Belly"
            if abs(c.y - zig(x)) < 0.07 and 0.55 < x < 2.5: return "Glow"
            if c.y > 0.55: return "Trim"
            if c.y > 0.4:   # a band of totem triangles
                return "Accent" if ((x * 3.0) % 1.0) < (c.y - 0.4) / 0.15 else "Glass"
            if c.y < -0.85: return "Belly"
            if c.y < -0.7: return "Dark"
            return "Base"
        P.part(name, bm, wpaint, tuple(hub), 0)
        for row, (y, z0, L) in enumerate(((0.3, 0.33, 0.32), (0.0, 0.31, 0.38))):   # covert feathers laid along the wing
            for k in range(8):
                x0 = 0.55 + k * 0.24
                b = Vector((s * x0, y, z0 + x0 * 0.1))
                P.part(name, cone(b, b + Vector((s * 0.06, -L, -0.01)), 0.1, 4), "Accent" if (k + row) % 3 == 0 else ("Belly" if row else "Base"), tuple(hub), 0, False)
        for k in range(7):   # the long primaries at the tip, spread like fingers
            a = math.radians(14 - k * 15); r0 = Vector((s * 2.5, -0.25, 0.53))
            tip = r0 + Vector((s * math.cos(a) * 1.1, math.sin(a) * 1.1, 0.05))
            P.part(name, pipe([r0, r0 + (tip - r0) * 0.5, tip], [0.14, 0.12, 0.0], 6),
                   lambda c, n, t=tip: "Accent" if (c - t).length < 0.25 else ("Dark" if (c - t).length < 0.5 else "Belly"), tuple(hub), 0, False)
        for k in range(8):   # the trailing secondaries
            x0 = 0.45 + k * 0.27
            P.part(name, cone((s * x0, -0.95, 0.22 + x0 * 0.1), (s * (x0 + 0.06), -1.45, 0.2 + x0 * 0.1), 0.13, 5), "Belly" if k % 2 else "Dark", tuple(hub), 0, False)
    # the fanned tail with totem eye patterns
    th = Vector((0, -0.85, 0.05))
    tips = [th + Vector((math.sin(math.radians(a)) * 1.35, -math.cos(math.radians(a)) * 1.35, 0.05)) for a in range(-56, 57, 14)]
    P.obj("Tail", fan(th, tips, 0.05, 0.25), lambda c, n: "Dark" if (c - th).length > 1.15 else ("Belly" if (c - th).length > 0.85 else ("Trim" if (c - th).length > 0.62 else "Accent")), 0, False)
    for t in tips[1:-1:2]:
        q = th + (t - th) * 0.72 + Vector((0, 0, 0.05))
        P.obj("TailEye", ball(tuple(q), (0.09, 0.09, 0.03), 10, 4), "Glass")
        P.obj("TailEyeIn", ball(tuple(q + Vector((0, 0, 0.02))), (0.04, 0.04, 0.02), 8, 3), "Dark")
    # golden talons gripping a lightning bolt
    for s in (1, -1):
        P.obj("Leg", pipe([(s * 0.2, 0.25, -0.3), (s * 0.22, 0.42, -0.62)], [0.11, 0.08], 8), "Belly")
        P.obj("Cuff", xf(torus(0.09, 0.025, 0.0, 12, 4), None, (s * 0.21, 0.36, -0.5)), "Glass")
        for k in (-1, 0, 1): P.obj("Talon", cone((s * 0.22, 0.42, -0.64), (s * 0.22 + k * 0.08, 0.58, -0.76), 0.035, 4), "Trim", 0, False)
    P.obj("Bolt", bolt([(-0.95, 0.5, -0.6), (-0.45, 0.48, -0.9), (-0.1, 0.48, -0.62), (0.3, 0.48, -0.92), (0.95, 0.5, -0.66)], 0.08, 0.07), "Glow", 0, False)
    # a ring of lightning bolts and feathers whirling round it
    for k in range(10):
        a = 2 * math.pi * k / 10
        c = Vector((math.sin(a) * 2.2, -0.1 + math.cos(a) * 1.9, 0.35 + 0.3 * math.sin(a * 2)))
        if k % 2 == 0:
            P.part("SpinBolts", bolt([tuple(c + Vector((-0.08, 0, 0.3))), tuple(c + Vector((0.08, 0, 0.05))), tuple(c + Vector((-0.06, 0, -0.08))), tuple(c + Vector((0.07, 0, -0.32)))], 0.045, 0.04), "Glow", (0, -0.1, 0.35), 0, False)
        else:
            P.part("SpinBolts", pipe([c + Vector((0, 0.18, 0)), c, c - Vector((0, 0.2, 0.02))], [0.0, 0.06, 0.0], 5), "Belly", (0, -0.1, 0.35), 0, False)
            P.part("SpinBolts", ball(tuple(c + Vector((0, 0.14, 0.0))), (0.03, 0.05, 0.02), 6, 3), "Accent", (0, -0.1, 0.35))
    mz = big @ Vector((0, 1.72, 0.3))
    P.part("Muzzle", ball(tuple(mz), (0.06, 0.04, 0.05), 8, 4), "Glow", tuple(mz))
    return P


# ================================================================= 2. the sheriff robot
def W_sheriff():
    """A steam-powered sheriff: a riveted brass barrel of a body with a turning cog on his chest, a silver star badge, a red bandana, a
    dome head with glowing eyes and a handlebar moustache under a wide cowboy hat, two smoking stacks on his back, a gun belt, a revolver in
    each hand aimed at you, and a boiler skirt riding on a jet of fire."""
    P = Boss("sheriff", {"Base": ((0.42, 0.24, 0.12), 0.35), "Belly": ((0.80, 0.80, 0.82), 0.35), "Accent": RED, "Trim": ((0.88, 0.89, 0.93), 0.9),
                         "Glass": ((0.22, 0.12, 0.06), 0.3), "Dark": ((0.07, 0.06, 0.06), 0.6), "Glow": ((1.0, 0.55, 0.15), 0.5),
                         "Metal": BRASS, "Lamp": ((0.55, 0.95, 1.0), 0.8)})
    rivets = lambda c, n: "Dark" if abs(((c.z + 0.05) * 3.2) % 1.0 - 0.5) < 0.04 else "Metal"
    P.obj("Torso", lathe([(0.0, -0.32), (0.42, -0.3), (0.56, 0.05), (0.6, 0.45), (0.56, 0.85), (0.44, 1.02), (0.0, 1.05)], 22, "z"), rivets)
    for v in P.parts[-1].data.vertices: v.co.y *= 0.82
    P.obj("Vest", lathe([(0.575, 0.22), (0.62, 0.45), (0.58, 0.8), (0.0, 0.8)], 22, "z"), lambda c, n: "Glass" if c.y < 0.3 or abs(c.x) > 0.16 else "Metal")
    for v in P.parts[-1].data.vertices: v.co.y *= 0.82
    for k in range(4): P.obj("Button", ball((0, 0.47, 0.3 + k * 0.14), (0.03, 0.02, 0.03), 6, 3), "Trim")
    P.obj("Badge", star((-0.3, 0.44, 0.66), 0.17, 0.075, 0.04), "Trim", 0, False)
    for k in range(5):
        a = math.pi * 2 * k / 5
        P.obj("BadgeTip", ball((-0.3 + math.sin(a) * 0.17, 0.46, 0.66 + math.cos(a) * 0.17), (0.025, 0.02, 0.025), 6, 3), "Trim")
    # the cog on his belly, turning face-on, round a glowing boiler window
    P.part("RollGear", gear((0.16, 0.46, 0.08), 0.17, 10, 0.06), "Metal", (0.16, 0.46, 0.08), 0, False)
    P.obj("Boiler", ball((0.16, 0.48, 0.08), (0.08, 0.03, 0.08), 10, 5), "Glow")
    P.obj("Belt", torus(0.6, 0.06, 0.0, 26, 6), "Base"); [setattr(v.co, "y", v.co.y * 0.82) for v in P.parts[-1].data.vertices]
    for k in range(12):
        a = math.radians(-70 + k * 11)
        if abs(k - 5.5) < 1: continue
        P.obj("Bullet", pipe([(math.sin(a) * 0.62, math.cos(a) * 0.52, -0.05), (math.sin(a) * 0.62, math.cos(a) * 0.52, 0.08)], [0.025, 0.02], 6), "Trim")
    P.obj("Buckle", box((0, 0.52, 0.0), (0.18, 0.04, 0.14)), "Metal", 0, False)
    # the boiler skirt and the jet of fire
    P.obj("Skirt", lathe([(0.42, -0.3), (0.36, -0.6), (0.22, -0.78), (0.18, -0.85), (0.0, -0.85)], 18, "z"), lambda c, n: "Dark" if c.z < -0.7 else "Metal")
    for v in P.parts[-1].data.vertices: v.co.y *= 0.82
    P.obj("Nozzle", lathe([(0.17, -0.8), (0.24, -1.02), (0.2, -1.04), (0.13, -0.85)], 14, "z"), "Dark")
    for k in range(6):
        a = 2 * math.pi * k / 6
        P.obj("Flame", cone((math.cos(a) * 0.12, math.sin(a) * 0.1, -1.0), (math.cos(a) * 0.08, math.sin(a) * 0.06 - 0.05, -1.45 - 0.12 * (k % 2)), 0.1, 6), "Glow", 0, False)
    P.obj("FlameCore", cone((0, 0, -0.98), (0, -0.05, -1.62), 0.13, 8), "Lamp", 0, False)
    # the head, the moustache, the hat
    P.obj("Neck", pipe([(0, 0, 1.0), (0, 0, 1.12)], [0.16, 0.16], 10), "Dark")
    P.obj("Bandana", cone((0, 0.05, 1.08), (0, 0.32, 0.86), 0.2, 8), "Accent", 0, False)
    P.obj("Bandana", torus(0.17, 0.05, 1.07, 16, 6), "Accent")
    P.obj("Dome", ball((0, 0, 1.3), (0.3, 0.28, 0.27), 16, 8), lambda c, n: "Dark" if abs(c.z - 1.33) < 0.035 and c.y > 0 else "Metal", 1)
    for s in (1, -1):
        P.obj("Eye", ball((s * 0.11, 0.24, 1.36), (0.065, 0.04, 0.05), 10, 5), "Lamp")
        P.obj("EyeRim", torus(0.07, 0.015, 0.0, 14, 4), "Dark"); P.parts[-1].data.transform(Matrix.Translation((s * 0.11, 0.25, 1.36)) @ Matrix.Rotation(math.radians(90), 4, "X"))
        P.obj("Moustache", pipe(bez((0, 0.29, 1.22), (s * 0.12, 0.31, 1.18), (s * 0.24, 0.28, 1.2), (s * 0.3, 0.22, 1.3), 6), [0.035, 0.05, 0.05, 0.04, 0.03, 0.02, 0.0], 6), "Dark")
        P.obj("Ear", lathe([(0.0, 0.0), (0.07, 0.0), (0.07, 0.06), (0.0, 0.06)], 10, "x", (0.27 if s > 0 else -0.33, 0, 1.3)), "Dark")
    for b, col in zip(hat((0, -0.06, 1.5), 1.1, math.radians(16)), ("Base", "Base", "Dark")):
        P.obj("Hat", b, col, 0, col != "Base")
    # the smokestacks on his back, puffing
    for s in (1, -1):
        P.obj("Stack", pipe([(s * 0.26, -0.3, 0.7), (s * 0.3, -0.42, 1.25)], [0.08, 0.07], 10), "Dark")
        P.obj("StackCap", lathe([(0.07, 0.0), (0.12, 0.1), (0.1, 0.12), (0.06, 0.04)], 10, "z", (s * 0.3, -0.42, 1.24)), "Metal")
        for k in range(4):
            c0 = Vector((s * (0.32 + k * 0.05), -0.5 - k * 0.14, 1.4 + k * 0.16))
            for j in range(3):
                P.obj("Smoke", ball(tuple(c0 + Vector((math.cos(j * 2.1) * 0.07, math.sin(j * 2.1) * 0.07, j * 0.03))), (0.09 + k * 0.025,) * 3, 10, 5), "Belly", 0)
    # the arms, a revolver in each hand aimed at you
    for s in (1, -1):
        sh = Vector((s * 0.6, 0.0, 0.8)); el = Vector((s * 0.82, 0.3, 0.5)); hd = Vector((s * 0.62, 0.68, 0.55))
        P.obj("Shoulder", ball(tuple(sh), (0.18, 0.18, 0.18), 12, 6), "Metal", 1)
        P.obj("Arm", pipe([sh, el, hd], [0.1, 0.09, 0.08], 10), lambda c, n: "Dark" if (c.y * 10) % 1.0 < 0.3 else "Belly")
        P.obj("Elbow", ball(tuple(el), (0.11, 0.11, 0.11), 10, 5), "Metal")
        P.obj("Hand", ball(tuple(hd), (0.12, 0.1, 0.11), 10, 5), "Dark")
        P.obj("Grip", box(tuple(hd + Vector((0, -0.02, -0.08))), (0.07, 0.09, 0.2), Matrix.Rotation(math.radians(-15), 3, "X")), "Glass", 0, False)
        P.obj("Frame", box(tuple(hd + Vector((0, 0.1, 0.07))), (0.08, 0.2, 0.1)), "Belly", 0, False)
        P.obj("Cylinder", lathe([(0.0, -0.08), (0.075, -0.08), (0.075, 0.08), (0.0, 0.08)], 8, "y", tuple(hd + Vector((0, 0.18, 0.08)))), "Belly")
        P.obj("Barrel", lathe([(0.0, 0.0), (0.04, 0.0), (0.04, 0.45), (0.0, 0.45)], 10, "y", tuple(hd + Vector((0, 0.24, 0.1)))), "Trim")
        P.obj("Hammer", box(tuple(hd + Vector((0, 0.03, 0.15))), (0.03, 0.05, 0.06)), "Dark", 0, False)
    P.part("Muzzle", ball((0.62, 1.15, 0.65), (0.05, 0.03, 0.05), 8, 4), "Glow", (0.62, 1.15, 0.65))
    return P


# ================================================================= 3. the rattlesnake
def W_rattler():
    """A giant diamondback rattlesnake coiled in the sky: a thick body in three coils patterned in brown and sand diamonds with a cream belly,
    its head reared up at you with jaws wide, long white fangs, a forked red tongue and glowing yellow eyes under a black outlaw's hat; the
    rattle held high behind it shakes."""
    P = Boss("rattler", {"Base": ((0.48, 0.30, 0.14), 0.45), "Belly": ((0.95, 0.86, 0.62), 0.4), "Accent": ((0.85, 0.66, 0.36), 0.45),
                         "Trim": ((0.98, 0.96, 0.90), 0.6), "Glass": ((0.62, 0.42, 0.20), 0.5), "Dark": ((0.10, 0.06, 0.04), 0.5),
                         "Glow": ((1.0, 0.85, 0.25), 0.5), "Metal": ((0.70, 0.18, 0.15), 0.4), "Lamp": ((1.0, 0.92, 0.30), 0.8)})
    # the coil: from the rattle (behind, low) round three turns rising inward, then the neck rearing up at the front
    ctrl = []
    turns = 2.3; N0 = 34
    for i in range(N0 + 1):
        t = i / N0
        a = math.pi + 2 * math.pi * turns * t           # starts at the back
        r = 1.25 - 0.55 * t
        ctrl.append((math.sin(a) * r, math.cos(a) * r, -0.55 + 0.75 * t))
    sp = ctrl + [tuple(Vector(p)) for p in bez(ctrl[-1], (0.0, 0.85, 0.35), (0.0, 0.75, 1.15), (0.0, 0.95, 1.55), 10)[1:]]
    sp = [Vector(p) for p in spline(sp[::2], 3)]
    N = len(sp)
    rad = []
    for i in range(N):
        t = i / (N - 1)
        r = 0.08 + 0.3 * min(1.0, t * 5.0)                 # thin at the rattle, thick in the coils
        if t > 0.72: r = 0.38 - (t - 0.72) / 0.28 * 0.16   # the neck narrows to the head
        rad.append(r)
    def diamonds(c, n):
        if n.z < -0.55: return "Belly"
        u = ang(c) * 2.6 + c.z * 3.0; v = ang(c) * 2.6 - c.z * 3.0
        if c.y > 0.55 and c.z > 0.4: u = c.z * 4.0 + c.x * 3.0; v = c.z * 4.0 - c.x * 3.0
        d = abs(u % 1.0 - 0.5) + abs(v % 1.0 - 0.5)
        return "Accent" if d < 0.2 else ("Dark" if d < 0.3 else "Base")
    P.obj("Body", pipe(sp, rad, 22), diamonds, 0)
    # the rattle, held up behind, shaking
    tp = sp[0]; up = Vector((0.0, -0.25, 1.0)).normalized()
    hub = tp
    for k in range(6):
        c = tp + up * (0.05 + k * 0.11); r = 0.11 - k * 0.012
        P.part("FlapRattle", ball(tuple(c), (r, r * 0.7, 0.08), 10, 5), "Accent" if k % 2 else "Glass", tuple(hub))
    P.part("FlapRattle", ball(tuple(tp + up * 0.72), (0.05, 0.04, 0.06), 8, 4), "Glass", tuple(hub))
    # the head, reared up, jaws wide (modelled small, then grown about the back of the skull)
    h0 = len(P.parts); HC = Vector((0, 0.85, 1.45)); HK = 1.45
    P.obj("Head", hull([(0.36, 0.85, 1.6), (-0.36, 0.85, 1.6), (0.34, 0.85, 1.42), (-0.34, 0.85, 1.42), (0.26, 1.2, 1.66), (-0.26, 1.2, 1.66),
                        (0.15, 1.5, 1.6), (-0.15, 1.5, 1.6), (0.13, 1.5, 1.48), (-0.13, 1.5, 1.48), (0.2, 1.15, 1.42), (-0.2, 1.15, 1.42), (0.0, 1.05, 1.75)]),
          lambda c, n: "Belly" if n.z < -0.5 else ("Dark" if abs(c.x) < 0.07 and n.z > 0.5 and c.y < 1.1 else "Base"), 0, False)
    P.obj("Jaw", hull([(0.3, 0.88, 1.36), (-0.3, 0.88, 1.36), (0.28, 0.9, 1.22), (-0.28, 0.9, 1.22), (0.12, 1.42, 1.12), (-0.12, 1.42, 1.12),
                       (0.1, 1.4, 1.02), (-0.1, 1.4, 1.02)]), lambda c, n: "Metal" if n.z > 0.5 else "Belly", 0, False)
    P.obj("Mouth", hull([(0.27, 0.9, 1.4), (-0.27, 0.9, 1.4), (0.13, 1.45, 1.46), (-0.13, 1.45, 1.46), (0.11, 1.4, 1.15), (-0.11, 1.4, 1.15),
                         (0.25, 0.92, 1.3), (-0.25, 0.92, 1.3)]), "Metal", 0, False)
    for s in (1, -1):
        P.obj("Fang", pipe(bez((s * 0.1, 1.38, 1.46), (s * 0.1, 1.42, 1.36), (s * 0.09, 1.4, 1.26), (s * 0.08, 1.35, 1.2), 4), [0.035, 0.03, 0.022, 0.012, 0.0], 6), "Trim")
        P.obj("Eye", ball((s * 0.25, 1.12, 1.6), (0.07, 0.08, 0.06), 10, 5), "Lamp")
        P.obj("Slit", box((s * 0.3, 1.14, 1.6), (0.012, 0.03, 0.09)), "Dark", 0, False)
        P.obj("Brow", hull([(s * 0.12, 1.2, 1.7), (s * 0.36, 1.05, 1.72), (s * 0.36, 1.0, 1.66), (s * 0.14, 1.2, 1.65)]), "Dark", 0, False)
        P.obj("Nostril", ball((s * 0.07, 1.5, 1.57), (0.025, 0.02, 0.02), 6, 3), "Dark")
        P.obj("Tongue", pipe(bez((0, 1.3, 1.22), (0, 1.55, 1.2), (s * 0.04, 1.75, 1.25), (s * 0.12, 1.9, 1.3), 6), [0.03, 0.03, 0.025, 0.02, 0.015, 0.01, 0.0], 6), "Metal")
    for ob in P.parts[h0:]:
        for v in ob.data.vertices: v.co = (v.co - HC) * HK + HC
    for b, col in zip(hat((0, 1.0, 1.74), 0.78, math.radians(14)), ("Dark", "Dark", "Accent")):
        P.obj("Hat", b, col, 0, col != "Dark")
    P.part("Muzzle", ball((0, 1.7, 1.25), (0.06, 0.04, 0.05), 8, 4), "Glow", (0, 1.7, 1.25))
    return P


# ================================================================= 4. the outlaw zeppelin
def W_zeppelin():
    """The outlaw gang's airship: a patched canvas envelope strapped in brass, a skull painted on its nose, red tail fins, a long wooden
    saloon gondola hung under it with glowing windows and wanted posters on its sides, two engines on outriggers with spinning propellers,
    a big pusher prop at the tail, and a gatling gun at the gondola's front."""
    P = Boss("zeppelin", {"Base": ((0.84, 0.74, 0.54), 0.35), "Belly": ((0.62, 0.48, 0.30), 0.3), "Accent": RED, "Trim": BRASS,
                          "Glass": ((0.96, 0.88, 0.66), 0.25), "Dark": WOOD, "Glow": ((1.0, 0.75, 0.30), 0.5),
                          "Metal": ((0.32, 0.32, 0.35), 0.75), "Lamp": ((1.0, 0.82, 0.42), 0.8)})
    rings = [(2.15, 0.05, 0.05, 0, 0.75), (2.05, 0.38, 0.36, 0, 0.75), (1.8, 0.62, 0.58, 0, 0.75), (1.2, 0.8, 0.75, 0, 0.75), (0.3, 0.84, 0.79, 0, 0.75),
             (-0.6, 0.8, 0.75, 0, 0.75), (-1.4, 0.62, 0.58, 0, 0.75), (-1.95, 0.32, 0.3, 0, 0.75), (-2.15, 0.06, 0.06, 0, 0.75)]
    def canvas(c, n):
        if c.y > 1.92: return "Trim"
        if (c.y * 1.8) % 1.0 < 0.06: return "Trim"
        if abs(c.z - 0.75) < 0.05 and abs(c.x) > 0.5: return "Trim"
        cell = Vector((math.floor(c.y * 2.2), math.floor(ang(Vector((c.x, c.z - 0.75, 0))) * 2.0), 0))
        return "Belly" if speckle(cell, 2.0) < 0.22 else "Base"
    P.obj("Envelope", loft(rings, 24), canvas, 1)
    # the skull on the nose
    SY = 2.12
    P.obj("Skull", ball((0, SY, 0.82), (0.24, 0.12, 0.22), 12, 6), "Glass", 1)
    P.obj("Jawbone", ball((0, SY - 0.02, 0.62), (0.15, 0.1, 0.08), 10, 5), "Glass", 1)
    for s in (1, -1): P.obj("Socket", ball((s * 0.09, SY + 0.1, 0.85), (0.06, 0.04, 0.065), 8, 4), "Dark")
    P.obj("NoseHole", ball((0, SY + 0.11, 0.74), (0.025, 0.02, 0.035), 6, 3), "Dark")
    for s in (1, -1):
        P.obj("Bone", pipe([(s * 0.38, SY - 0.12, 0.42), (-s * 0.38, SY - 0.12, 1.2)], [0.045, 0.045], 6, False), "Glass")
        for e in (1, -1): P.obj("BoneEnd", ball((e * s * 0.38, SY - 0.12, 0.81 - e * 0.39), (0.07, 0.05, 0.07), 6, 3), "Glass")
    # the tail fins
    for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        pts = []
        for (y, r) in ((-1.25, 0.6), (-2.0, 0.28)):
            pts += [(dx * r, y, 0.75 + dz * r)]
        a, b = Vector(pts[0]), Vector(pts[1])
        o = Vector((dx, 0, dz)) * 0.55
        side = Vector((dz, 0, dx)) * 0.04
        q = [a, b, b + o + Vector((0, -0.35, 0)), a + o * 0.6 + Vector((0, -0.25, 0))]
        P.obj("Fin", hull([tuple(p + side) for p in q] + [tuple(p - side) for p in q]), lambda c, n: "Trim" if (Vector((c.x, 0, c.z - 0.75)).length > 0.95) else "Accent", 0, False)
    P.prop((0, -2.18, 0.75), 0.5, 4, axis="y", chord=0.16, blade="Dark", tip="Trim", spinner="Trim", spinner_len=0.15, name="Prop0")
    # the gondola, a wooden saloon car
    P.obj("Gondola", box((0, 0.2, -0.32), (0.7, 2.0, 0.5)), lambda c, n: "Belly" if abs(n.z) > 0.5 else ("Dark" if ((c.y * 6) % 1.0 < 0.08 or abs(c.z + 0.32) > 0.2) else "Belly"), 0, False)
    P.obj("GondolaRoof", hull([(0.42, 1.25, -0.06), (-0.42, 1.25, -0.06), (0.42, -0.85, -0.06), (-0.42, -0.85, -0.06), (0.3, 1.15, 0.02), (-0.3, 1.15, 0.02), (0.3, -0.75, 0.02), (-0.3, -0.75, 0.02)]), "Accent", 0, False)
    P.obj("Keel", hull([(0.33, 1.2, -0.57), (-0.33, 1.2, -0.57), (0.33, -0.8, -0.57), (-0.33, -0.8, -0.57), (0.0, 1.0, -0.72), (0.0, -0.6, -0.72)]), "Dark", 0, False)
    for s in (1, -1):
        for k in range(5):
            y = -0.6 + k * 0.38
            if k == 2:   # a wanted poster in the middle
                P.obj("Poster", box((s * 0.36, y, -0.3), (0.03, 0.26, 0.32)), "Glass", 0, False)
                P.obj("Face", box((s * 0.375, y, -0.27), (0.02, 0.14, 0.14)), "Dark", 0, False)
                P.obj("Reward", box((s * 0.375, y, -0.42), (0.02, 0.18, 0.04)), "Accent", 0, False)
            else:
                P.obj("Window", box((s * 0.355, y, -0.28), (0.03, 0.2, 0.18)), "Lamp", 0, False)
                P.obj("Shutter", box((s * 0.36, y, -0.17), (0.04, 0.26, 0.04)), "Accent", 0, False)
        # rigging
        for y in (-0.6, 0.4, 1.0):
            P.obj("Rope", pipe([(s * 0.32, y, -0.06), (s * 0.55, y, 0.25)], [0.015, 0.015], 4, False), "Dark")
    # the engines on outriggers
    for s in (1, -1):
        P.obj("Strut", pipe([(s * 0.35, 0.2, -0.2), (s * 1.15, 0.0, -0.1)], [0.05, 0.05], 6), "Metal")
        P.obj("Nacelle", loft([(0.5, 0.04, 0.04, s * 1.25, -0.1), (0.38, 0.16, 0.16, s * 1.25, -0.1), (-0.25, 0.19, 0.19, s * 1.25, -0.1), (-0.5, 0.12, 0.12, s * 1.25, -0.1)], 14),
              lambda c, n: "Trim" if abs((c.y * 4) % 1.0) < 0.15 else "Metal", 0)
        P.obj("Exhaust", pipe([(s * 1.38, -0.1, 0.0), (s * 1.42, -0.2, 0.25)], [0.04, 0.05], 6), "Dark")
        P.prop((s * 1.25, 0.55, -0.1), 0.42, 3, axis="y", chord=0.14, blade="Dark", tip="Accent", spinner="Trim", spinner_len=0.15, name="Prop%d" % (1 if s > 0 else 2))
    # the gatling gun at the gondola's front, and lanterns
    gc = Vector((0, 1.32, -0.42))
    P.obj("GunMount", ball(tuple(gc), (0.16, 0.14, 0.14), 10, 5), "Metal")
    for k in range(6):
        a = 2 * math.pi * k / 6
        P.obj("GunBarrel", pipe([gc + Vector((math.cos(a) * 0.06, 0.05, math.sin(a) * 0.06)), gc + Vector((math.cos(a) * 0.06, 0.6, math.sin(a) * 0.06))], [0.025, 0.025], 6), "Metal")
    for z in (0.18, 0.42): P.obj("GunBand", lathe([(0.1, z), (0.1, z + 0.04)], 12, "y", tuple(gc)), "Trim")
    for s in (1, -1): P.obj("Lantern", ball((s * 0.4, 1.28, -0.12), (0.06, 0.06, 0.08), 8, 4), "Lamp")
    # a black flag at the tail
    P.obj("Pole", pipe([(0, -1.95, 1.0), (0, -1.95, 1.55)], [0.02, 0.02], 6), "Dark")
    flag = [(0, -1.96, 1.55), (0, -2.55, 1.5), (0, -2.5, 1.3), (0, -1.96, 1.28)]
    P.obj("Flag", hull([(x + d, y, z) for (x, y, z) in flag for d in (-0.012, 0.012)]), "Dark", 0, False)
    P.part("Muzzle", ball(tuple(gc + Vector((0, 0.65, 0))), (0.06, 0.03, 0.06), 8, 4), "Glow", tuple(gc + Vector((0, 0.65, 0))))
    return P


# ================================================================= 5. the gold mine mesa
def W_mesa():
    """The last boss: a mesa of red rock torn up into the sky, banded in red, sand and umber strata, carrying a whole boom town - a saloon
    with a false front and swinging doors, a water tower, a windmill whose wheel turns, saguaro cacti - a gold mine in its face with a timber
    frame, rails on a trestle and a cart heaped with glowing gold, and a ring of gold coins turning round it."""
    P = Boss("mesa", {"Base": ((0.74, 0.30, 0.14), 0.3), "Belly": ((0.92, 0.70, 0.44), 0.3), "Accent": ((0.62, 0.38, 0.20), 0.35), "Trim": GOLD,
                      "Glass": ((0.28, 0.58, 0.24), 0.35), "Dark": ((0.26, 0.13, 0.07), 0.35), "Glow": ((1.0, 0.80, 0.25), 0.5),
                      "Metal": ((0.42, 0.42, 0.46), 0.75), "Lamp": ((1.0, 0.80, 0.40), 0.8)})
    rng = random.Random(4)
    # the rock: rings of noisy radius, flat-topped, tapering to a point below
    prof = [(0.35, 1.95), (0.25, 2.0), (0.0, 1.98), (-0.3, 1.9), (-0.6, 1.7), (-0.85, 1.45), (-1.1, 1.0), (-1.35, 0.55), (-1.6, 0.15)]
    seg = 28; noise = [rng.uniform(0.9, 1.08) for _ in range(seg)]
    bm = bmesh.new(); loops = []
    for (z, r) in prof:
        lp = []
        for i in range(seg):
            a = 2 * math.pi * i / seg; rr = r * (noise[i] * 0.6 + 0.4 + rng.uniform(-0.03, 0.03) if z < 0.3 else noise[i] * 0.5 + 0.5)
            lp.append(bm.verts.new((math.sin(a) * rr, math.cos(a) * rr * 0.85, z)))
        loops.append(lp)
    for r0, r1 in zip(loops, loops[1:]):
        for i in range(seg):
            j = (i + 1) % seg
            bm.faces.new((r0[i], r0[j], r1[j], r1[i]))
    bm.faces.new(list(reversed(loops[0]))); bm.faces.new(loops[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    def strata(c, n):
        if n.z > 0.7 and c.z > 0.3: return "Belly"
        b = int(math.floor((c.z + 2.0) * 3.2)) % 4
        return ("Base", "Belly", "Base", "Accent")[b] if c.z > -1.1 else "Dark"
    P.obj("Mesa", bm, strata, 0, False)
    TOP = 0.36
    # the saloon (back left)
    sc = Vector((-0.75, -0.25, TOP))
    P.obj("Saloon", box((sc.x, sc.y, sc.z + 0.33), (0.9, 0.75, 0.66)), lambda c, n: "Dark" if (c.x * 9) % 1.0 < 0.1 else "Accent", 0, False)
    P.obj("SaloonRoof", hull([(sc.x - 0.48, sc.y - 0.4, sc.z + 0.66), (sc.x + 0.48, sc.y - 0.4, sc.z + 0.66), (sc.x - 0.48, sc.y + 0.4, sc.z + 0.66), (sc.x + 0.48, sc.y + 0.4, sc.z + 0.66),
                              (sc.x - 0.48, sc.y, sc.z + 0.86), (sc.x + 0.48, sc.y, sc.z + 0.86)]), "Dark", 0, False)
    fy = sc.y + 0.39
    P.obj("FalseFront", box((sc.x, fy, sc.z + 0.55), (1.0, 0.06, 1.1)), lambda c, n: "Dark" if c.z > sc.z + 1.05 else "Accent", 0, False)
    P.obj("Sign", box((sc.x, fy + 0.04, sc.z + 0.86), (0.7, 0.03, 0.2)), "Trim", 0, False)
    P.obj("SignText", box((sc.x, fy + 0.06, sc.z + 0.86), (0.52, 0.02, 0.06)), "Dark", 0, False)
    for s in (1, -1):
        P.obj("Window", box((sc.x + s * 0.28, fy + 0.04, sc.z + 0.42), (0.18, 0.03, 0.2)), "Lamp", 0, False)
    P.obj("Door", box((sc.x, fy + 0.04, sc.z + 0.2), (0.22, 0.03, 0.3)), "Lamp", 0, False)
    for s in (1, -1): P.obj("BatDoor", box((sc.x + s * 0.06, fy + 0.07, sc.z + 0.2), (0.1, 0.02, 0.16)), "Belly", 0, False)
    P.obj("Porch", box((sc.x, fy + 0.25, sc.z + 0.62), (1.0, 0.45, 0.04)), "Dark", 0, False)
    for s in (1, -1): P.obj("Post", pipe([(sc.x + s * 0.46, fy + 0.45, sc.z), (sc.x + s * 0.46, fy + 0.45, sc.z + 0.62)], [0.025, 0.025], 6), "Dark")
    # the water tower (back right)
    wc = Vector((0.85, -0.45, TOP))
    for sx in (1, -1):
        for sy in (1, -1):
            P.obj("TowerLeg", pipe([(wc.x + sx * 0.28, wc.y + sy * 0.28, wc.z), (wc.x + sx * 0.2, wc.y + sy * 0.2, wc.z + 0.75)], [0.035, 0.03], 6), "Dark")
    P.obj("Brace", box((wc.x, wc.y, wc.z + 0.4), (0.5, 0.5, 0.03)), "Dark", 0, False)
    P.obj("Tank", lathe([(0.0, 0.75), (0.32, 0.75), (0.34, 1.25), (0.0, 1.25)], 18, "z", tuple(wc)), lambda c, n: "Metal" if abs(((c.z - wc.z) * 6) % 1.0 - 0.5) < 0.06 else "Accent")
    P.obj("TankRoof", lathe([(0.38, 1.24), (0.0, 1.55)], 18, "z", tuple(wc)), "Base")
    # the windmill (front right): a lattice tower, a turning wheel facing you, a tail vane
    mc = Vector((1.15, 0.65, TOP))
    for sx in (1, -1):
        for sy in (1, -1):
            P.obj("MillLeg", pipe([(mc.x + sx * 0.18, mc.y + sy * 0.18, mc.z), (mc.x + sx * 0.04, mc.y + sy * 0.04, mc.z + 1.15)], [0.025, 0.02], 5), "Metal")
    for k in range(3): P.obj("MillRung", box((mc.x, mc.y, mc.z + 0.25 + k * 0.3), (0.32 - k * 0.08, 0.32 - k * 0.08, 0.025)), "Metal", 0, False)
    P.obj("MillHead", box((mc.x, mc.y - 0.05, mc.z + 1.2), (0.1, 0.25, 0.1)), "Metal", 0, False)
    P.obj("Vane", hull([(mc.x - 0.01, mc.y - 0.2, mc.z + 1.2), (mc.x + 0.01, mc.y - 0.2, mc.z + 1.2), (mc.x - 0.01, mc.y - 0.6, mc.z + 1.05), (mc.x + 0.01, mc.y - 0.6, mc.z + 1.05),
                        (mc.x - 0.01, mc.y - 0.6, mc.z + 1.4), (mc.x + 0.01, mc.y - 0.6, mc.z + 1.4)]), "Accent", 0, False)
    hub = (mc.x, mc.y + 0.12, mc.z + 1.2)
    for k in range(12):
        a = 2 * math.pi * k / 12
        P.part("PropMill", box((hub[0] + math.sin(a) * 0.3, hub[1], hub[2] + math.cos(a) * 0.3), (0.07, 0.015, 0.32), Matrix.Rotation(-a, 3, "Y")), "Belly", hub, 0, False)
    P.part("PropMill", xf(torus(0.45, 0.02, 0.0, 24, 4), Matrix.Rotation(math.radians(90), 3, "X"), hub), "Metal", hub, 0, False)
    P.part("PropMill", lathe([(0.0, -0.04), (0.06, -0.04), (0.06, 0.06), (0.0, 0.08)], 10, "y", hub), "Dark", hub, 0, False)
    # saguaro cacti
    for (x, y, h) in ((-1.45, 0.5, 0.65), (0.2, -1.1, 0.55), (-0.15, 0.4, 0.45)):
        P.obj("Cactus", pipe([(x, y, TOP), (x, y, TOP + h)], [0.07, 0.065], 8), "Glass")
        P.obj("CactusTop", ball((x, y, TOP + h), (0.065, 0.065, 0.065), 8, 4), "Glass")
        for s in (1, -1):
            P.obj("CactusArm", pipe([(x, y, TOP + h * 0.45 + s * 0.04), (x + s * 0.18, y, TOP + h * 0.45 + s * 0.04), (x + s * 0.18, y, TOP + h * 0.8 + s * 0.04)], [0.045, 0.045, 0.04], 6), "Glass")
    # the mine in its face: a timber frame round a dark mouth, rails out onto a trestle, a cart heaped with gold
    my = 1.38
    P.obj("MineMouth", box((0, my, -0.35), (0.62, 0.3, 0.58)), "Dark", 0, False)
    P.obj("MineBack", box((0, my - 0.05, -0.35), (0.5, 0.3, 0.48)), "Dark", 0, False)
    for s in (1, -1): P.obj("Timber", box((s * 0.33, my + 0.15, -0.38), (0.08, 0.1, 0.66)), "Accent", 0, False)
    P.obj("Lintel", box((0, my + 0.15, -0.02), (0.82, 0.12, 0.1)), "Accent", 0, False)
    P.obj("MineSign", box((0, my + 0.22, 0.12), (0.5, 0.03, 0.14)), "Trim", 0, False)
    for s in (1, -1): P.obj("Rail", box((s * 0.12, my + 0.5, -0.62), (0.025, 1.1, 0.025)), "Metal", 0, False)
    for k in range(7): P.obj("Tie", box((0, my + 0.05 + k * 0.15, -0.65), (0.36, 0.05, 0.025)), "Dark", 0, False)
    for s in (1, -1): P.obj("Trestle", pipe([(s * 0.18, my + 0.85, -0.65), (s * 0.08, my + 0.6, -1.15)], [0.03, 0.03], 5), "Dark")
    cc = Vector((0, my + 0.75, -0.48))
    P.obj("Cart", hull([(0.22, cc.y - 0.17, cc.z + 0.12), (-0.22, cc.y - 0.17, cc.z + 0.12), (0.22, cc.y + 0.17, cc.z + 0.12), (-0.22, cc.y + 0.17, cc.z + 0.12),
                        (0.16, cc.y - 0.12, cc.z - 0.1), (-0.16, cc.y - 0.12, cc.z - 0.1), (0.16, cc.y + 0.12, cc.z - 0.1), (-0.16, cc.y + 0.12, cc.z - 0.1)]), "Metal", 0, False)
    for k in range(9):
        P.obj("Nugget", ball((rng.uniform(-0.15, 0.15), cc.y + rng.uniform(-0.1, 0.1), cc.z + 0.14 + rng.uniform(0, 0.08)), (0.07, 0.07, 0.06), 6, 3), "Glow")
    for s in (1, -1):
        for e in (1, -1): P.obj("CartWheel", lathe([(0.0, -0.02), (0.06, -0.02), (0.06, 0.02), (0.0, 0.02)], 10, "x", (s * 0.17, cc.y + e * 0.1, cc.z - 0.11)), "Dark")
    for (x, y, z) in ((0.5, my - 0.15, -0.2), (-0.55, my - 0.2, -0.6), (0.6, my - 0.3, -0.8)):   # gold veins glinting in the rock
        P.obj("Vein", ball((x, y, z), (0.1, 0.06, 0.08), 6, 3), "Glow")
    for s in (1, -1): P.obj("MineLamp", ball((s * 0.42, my + 0.2, -0.1), (0.05, 0.05, 0.07), 8, 4), "Lamp")
    # the ring of gold coins
    for k in range(16):
        a = 2 * math.pi * k / 16
        c = Vector((math.cos(a) * 2.35, math.sin(a) * 2.1, 0.2 + 0.3 * math.sin(a * 3)))
        coin = lathe([(0.0, -0.02), (0.13, -0.02), (0.13, 0.02), (0.0, 0.02)], 12, "z")
        xf(coin, Matrix.Rotation(math.radians(70), 3, "X") @ Matrix.Rotation(a, 3, "Z"), c)
        P.part("SpinCoins", coin, "Trim", (0, 0, 0.2), 0, False)
    P.part("Muzzle", ball((0, my + 0.1, -0.35), (0.07, 0.03, 0.07), 8, 4), "Glow", (0, my + 0.1, -0.35))
    return P


# ================================================================= the second round (2026-10-11: "improve the snake, the way it comes to
# the player"; the mesa replaced by "something grand, with features, that suits the place")
def transport(sp):
    """tangents, a twist-free normal per point (parallel transport from 'up' at the start, twisted evenly so it is 'up' again at the
    end), and the arc length."""
    n = len(sp)
    T = [(sp[min(i + 1, n - 1)] - sp[max(i - 1, 0)]).normalized() for i in range(n)]
    up = Vector((0, 0, 1))
    N = [(up - T[0] * up.dot(T[0])).normalized()]
    for i in range(1, n):
        q = T[i - 1].rotation_difference(T[i]); v = q @ N[-1]
        N.append((v - T[i] * v.dot(T[i])).normalized())
    want = (up - T[-1] * up.dot(T[-1])).normalized()
    tw = math.atan2(T[-1].dot(N[-1].cross(want)), N[-1].dot(want))
    S = [0.0]
    for i in range(1, n): S.append(S[-1] + (sp[i] - sp[i - 1]).length)
    N = [Matrix.Rotation(tw * S[i] / S[-1], 3, T[i]) @ N[i] for i in range(n)]
    return T, N, S

def tpipe(sp, rad, N, seg=24):
    """a tube through sp whose rings follow the normals N (no flips where the path stands up)."""
    bm = bmesh.new(); rings = []
    for i, p in enumerate(sp):
        t = (sp[min(i + 1, len(sp) - 1)] - sp[max(i - 1, 0)]).normalized()
        a = N[i]; b = t.cross(a)
        if rad[i] < 1e-5: rings.append([bm.verts.new(p)]); continue
        rings.append([bm.verts.new(p + (a * math.cos(2 * math.pi * k / seg) + b * math.sin(2 * math.pi * k / seg)) * rad[i]) for k in range(seg)])
    for r0, r1 in zip(rings, rings[1:]):
        if len(r0) == 1:
            for k in range(seg): bm.faces.new((r0[0], r1[k], r1[(k + 1) % seg]))
        elif len(r1) == 1:
            for k in range(seg): bm.faces.new((r0[k], r1[0], r0[(k + 1) % seg]))
        else:
            for k in range(seg): bm.faces.new((r0[k], r0[(k + 1) % seg], r1[(k + 1) % seg], r1[k]))
    if len(rings[-1]) > 1: bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm

def W_rattler2():
    """The rattlesnake striking at you: one loose coil low behind, the body rising in an S out of it and the great head thrust forward at
    the player - jaws thrown wide on a glowing red throat, two long curved fangs, a forked tongue flicking out, burning yellow eyes with
    slit pupils under angry brow plates, an outlaw's hat with a gold band; brown diamonds outlined in cream down its back, a cream belly up
    the front of the neck, and the gold-ringed rattle raised high behind, shaking."""
    P = Boss("rattler2", {"Base": ((0.50, 0.33, 0.17), 0.45), "Belly": ((0.96, 0.88, 0.66), 0.4), "Accent": ((0.93, 0.80, 0.55), 0.45),
                          "Trim": ((0.99, 0.98, 0.94), 0.6), "Glass": ((0.20, 0.11, 0.05), 0.6), "Dark": ((0.06, 0.04, 0.03), 0.5),
                          "Glow": ((1.0, 0.82, 0.12), 0.5), "Metal": GOLD, "Lamp": ((0.50, 0.03, 0.05), 0.6)})
    # the path from the rattle (up behind) down into the coil, once round, up in an S and forward to the head
    C = Vector((0.0, -0.45, -0.85)); ctrl = [Vector((0.8, -1.55, 1.0)), Vector((0.9, -1.45, 0.4)), Vector((0.85, -1.3, -0.3))]
    for k in range(19):
        t = k / 18; a = math.radians(140 - 500 * t); r = 1.05 - 0.38 * t
        ctrl.append(C + Vector((math.sin(a) * r, math.cos(a) * r, 0.0 + 0.4 * t)))
    ctrl += [Vector((-0.32, 0.12, -0.15)), Vector((-0.22, -0.02, 0.45)), Vector((0.02, 0.0, 1.05)), Vector((0.08, 0.4, 1.5)),
             Vector((0.02, 0.8, 1.66)), Vector((0.0, 1.05, 1.62))]
    sp = spline(ctrl, 8)
    T, N, S = transport(sp)
    L = S[-1]
    rad = []
    for s in S:
        t = s / L
        r = 0.05 + 0.29 * min(1.0, t / 0.2)             # thin at the rattle, thick in the coil
        if t > 0.7: r -= (t - 0.7) / 0.3 * 0.06          # the neck a little narrower
        rad.append(r)
    def scales(c, nn):
        i = min(range(len(sp)), key=lambda j: (sp[j] - c).length_squared)
        d = c - sp[i]; b = T[i].cross(N[i])
        phi = math.atan2(d.dot(b), d.dot(N[i]))               # 0 on the spine
        if abs(phi) > 2.15: return "Accent" if (S[i] / 0.1) % 1.0 < 0.18 else "Belly"
        u = (S[i] / 0.46) % 1.0
        m = abs(u - 0.5) * 2.0 + abs(phi) / 1.25
        if m < 0.55: return "Glass"
        if m < 0.78: return "Accent"
        if abs(phi) > 1.6 and (S[i] / 0.23) % 1.0 < 0.35: return "Glass"   # blotches low on the flanks
        return "Base"
    P.obj("Body", tpipe(sp, rad, N, 28), scales, 0)
    # the rattle, held high behind and shaking: gold-ringed segments
    tp = sp[0]; up = (sp[0] - sp[3]).normalized()
    for k in range(7):
        c = tp + up * (0.02 + k * 0.14); r = 0.15 - k * 0.012
        P.part("FlapRattle", ball(tuple(c), (r, r * 0.75, 0.07), 12, 6), "Accent" if k % 2 else "Glass", tuple(tp))
        P.part("FlapRattle", ball(tuple(c + up * 0.07), (r * 0.9, r * 0.68, 0.02), 12, 3), "Metal", tuple(tp))
    P.part("FlapRattle", ball(tuple(tp + up * 1.02), (0.05, 0.04, 0.06), 8, 4), "Metal", tuple(tp))
    # the head, in its own frame: hinge at the origin, +Y forward; built small, then placed, lifted and grown
    H = sp[-1] + T[-1] * 0.05
    MH = Matrix.Translation(H) @ Matrix.Rotation(math.radians(-6), 4, "X") @ Matrix.Scale(1.55, 4)
    MU = MH @ Matrix.Rotation(math.radians(16), 4, "X")      # the upper jaw thrown up
    ML = MH @ Matrix.Rotation(math.radians(-34), 4, "X")     # the lower jaw dropped
    def xb(bm, m):
        for v in bm.verts: v.co = m @ v.co
        return bm
    # the upper head: a broad viper's wedge, flat under the palate
    up_r = [(-0.2, 0.26, 0.2, 0, 0.1), (-0.02, 0.4, 0.24, 0, 0.12), (0.2, 0.47, 0.23, 0, 0.12), (0.42, 0.4, 0.19, 0, 0.1),
            (0.64, 0.29, 0.15, 0, 0.07), (0.82, 0.19, 0.11, 0, 0.05), (0.93, 0.1, 0.07, 0, 0.04)]
    bm = loft(up_r, 24)
    for v in bm.verts: v.co.z = max(v.co.z, -0.0)
    def headpaint(c, n):
        if n.z < -0.6: return "Lamp"                       # the palate
        if abs(c.x) > 0.2 and abs(c.z - (0.14 - c.y * 0.05)) < 0.04 and c.y < 0.45: return "Glass"   # the dark stripe behind the eye
        if n.z > 0.55 and abs(c.x) < 0.24 and (c.y * 6.0) % 1.0 < 0.18: return "Glass"
        return "Base" if n.z > -0.2 else "Belly"
    P.obj("Head", xb(bm, MU), lambda c, n, m=MU.inverted(): headpaint(m @ c, (m.to_3x3() @ n).normalized()), 1)
    lo_r = [(-0.08, 0.34, 0.1, 0, -0.04), (0.2, 0.36, 0.1, 0, -0.05), (0.5, 0.28, 0.08, 0, -0.04), (0.76, 0.17, 0.06, 0, -0.03), (0.88, 0.07, 0.04, 0, -0.02)]
    bm = loft(lo_r, 20)
    for v in bm.verts: v.co.z = min(v.co.z, -0.02)
    P.obj("Jaw", xb(bm, ML), lambda c, n, m=ML.inverted(): "Lamp" if (m.to_3x3() @ n).z > 0.6 else "Belly", 1)
    P.obj("Throat", xb(ball((0, 0.12, 0.0), (0.3, 0.26, 0.17), 14, 7), MH), "Lamp", 1)
    P.obj("Gullet", xb(ball((0, 0.02, 0.0), (0.13, 0.1, 0.1), 10, 5), MH), "Dark", 1)
    for s in (1, -1):
        # the fangs, long and curved back, folded down from the front of the upper jaw
        P.obj("Fang", xb(pipe(bez((s * 0.16, 0.74, 0.02), (s * 0.16, 0.78, -0.12), (s * 0.15, 0.74, -0.26), (s * 0.13, 0.66, -0.33), 6),
                              [0.04, 0.036, 0.03, 0.024, 0.016, 0.008, 0.0], 8), MU), "Trim")
        for k in range(3):
            P.obj("Tooth", xb(cone((s * (0.28 - k * 0.06), 0.3 + k * 0.15, -0.01), (s * (0.27 - k * 0.06), 0.28 + k * 0.15, -0.09), 0.018, 5), MU), "Trim", 0, False)
            P.obj("Tooth", xb(cone((s * (0.24 - k * 0.05), 0.25 + k * 0.15, -0.0), (s * (0.24 - k * 0.05), 0.24 + k * 0.15, 0.07), 0.016, 5), ML), "Trim", 0, False)
        # eyes looking forward at you, slit pupils, angry brow plates over them
        e = Vector((s * 0.28, 0.46, 0.22))
        P.obj("Eye", xb(ball(tuple(e), (0.115, 0.115, 0.11), 14, 7), MU), "Glow", 1)
        d = Vector((s * 0.35, 0.85, 0.4)).normalized()
        P.obj("Pupil", xb(ball(tuple(e + d * 0.105), (0.025, 0.025, 0.08), 8, 5), MU), "Dark", 1)
        P.obj("Brow", xb(hull([(s * 0.1, 0.56, 0.3), (s * 0.12, 0.6, 0.25), (s * 0.44, 0.34, 0.42), (s * 0.46, 0.28, 0.36), (s * 0.3, 0.5, 0.4),
                                (s * 0.12, 0.48, 0.34), (s * 0.4, 0.26, 0.44)]), MU), "Glass", 0, False)
        P.obj("Pit", xb(ball((s * 0.19, 0.72, 0.1), (0.035, 0.03, 0.025), 8, 4), MU), "Dark")
        P.obj("Nostril", xb(ball((s * 0.07, 0.9, 0.09), (0.025, 0.02, 0.02), 8, 4), MU), "Dark")
    # the forked tongue flicking out at you
    tongue = bez((0, 0.2, -0.04), (0, 0.6, -0.02), (0, 0.95, 0.02), (0, 1.25, 0.0), 8)
    P.obj("Tongue", xb(pipe(tongue, [0.04, 0.04, 0.038, 0.035, 0.032, 0.03, 0.028, 0.026, 0.024], 8), ML), "Dark")
    for s in (1, -1):
        P.obj("Tongue", xb(pipe(bez((0, 1.24, 0.0), (s * 0.04, 1.32, 0.02), (s * 0.09, 1.38, 0.05), (s * 0.13, 1.44, 0.08), 4), [0.024, 0.02, 0.015, 0.008, 0.0], 6), ML), "Dark")
    # the outlaw's hat, tipped back on the skull, a gold band
    for b, col in zip(hat((0, 0, 0), 0.82, math.radians(-8)), ("Dark", "Dark", "Metal")):
        P.obj("Hat", xb(b, MU @ Matrix.Translation((0, 0.02, 0.3))), col, 0, col != "Dark")
    P.part("Muzzle", ball(tuple(MH @ Vector((0, 0.7, 0.0))), (0.06, 0.04, 0.05), 8, 4), "Lamp", tuple(MH @ Vector((0, 0.7, 0.0))))
    return P


# ================================================================= the stampede king (in place of the gold mine mesa)
def W_bison():
    """The last boss: the stampede king, a colossal spirit bison charging across the sky - a towering shaggy hump, a great low head with
    burning turquoise eyes under a scowling brow, a dark beard, thick ivory horns capped and ringed in gold, a gold nose ring, a turquoise
    medallion set in gold on its brow with eagle feathers hanging from the horns, glowing spirit chevrons on its flanks, gold-shod hooves
    trailing spirit fire, its legs galloping, and a ring of spirit feathers turning round it."""
    P = Boss("bison", {"Base": ((0.48, 0.29, 0.15), 0.35), "Belly": ((0.96, 0.91, 0.78), 0.45), "Accent": ((0.20, 0.11, 0.06), 0.3),
                       "Trim": ((0.98, 0.96, 0.92), 0.4), "Glass": ((0.05, 0.70, 0.68), 0.85), "Dark": ((0.05, 0.04, 0.04), 0.5),
                       "Glow": ((0.06, 0.80, 0.72), 0.5), "Metal": GOLD, "Lamp": ((1.0, 0.55, 0.15), 0.8)})
    rng = random.Random(5)
    def chevrons(c, n):
        if abs(c.x) > 0.45 and -1.0 < c.y < 0.1 and n.z > -0.4:
            u = (c.y + 1.0) * 2.4 - abs(c.z - 0.15) * 1.6
            if (u % 1.0) < 0.16 and abs(c.z - 0.15) < 0.5: return "Glow"
        return "Base"
    rings = [(-1.35, 0.3, 0.32, 0, 0.05), (-1.15, 0.52, 0.52, 0, 0.08), (-0.75, 0.66, 0.66, 0, 0.12), (-0.25, 0.76, 0.82, 0, 0.25),
             (0.2, 0.84, 0.86, 0, 0.36), (0.6, 0.8, 0.8, 0, 0.3), (0.95, 0.62, 0.72, 0, 0.12), (1.15, 0.42, 0.5, 0, -0.02)]
    P.obj("Body", loft(rings, 24), chevrons, 1)
    # the shaggy mane: a second, larger skin over the hump, the shoulders and the chest, tufted
    mane_r = [(-0.4, 0.62, 0.72, 0, 0.3), (-0.1, 0.84, 0.88, 0, 0.34), (0.25, 0.94, 0.98, 0, 0.42), (0.6, 0.9, 0.92, 0, 0.36),
              (0.95, 0.74, 0.86, 0, 0.2), (1.25, 0.56, 0.66, 0, 0.02)]
    bm = loft(mane_r, 32)
    for v in bm.verts:
        c0 = Vector((0, v.co.y, 0.0)); r = v.co - Vector((0, v.co.y, 0.35)); r.y = 0
        if r.length < 1e-4: continue
        tuft = 0.5 + 0.5 * math.sin(v.co.x * 9.0 + v.co.z * 4.0) * math.sin(v.co.y * 11.0 + v.co.z * 7.0)
        v.co += r.normalized() * (0.16 * tuft - 0.04)
        if v.co.z < -0.1: v.co.y += 0.04 * math.sin(v.co.x * 13.0)
    P.obj("Mane", bm, lambda c, n: "Accent", 1)
    for k in range(150):   # tufts of fur standing out of it, swept back
        y = rng.uniform(-0.35, 1.2); a = rng.uniform(-math.pi * 0.92, math.pi * 0.92)
        ra, rb, cz = None, None, None
        for r0, r1 in zip(mane_r, mane_r[1:]):
            if r0[0] <= y <= r1[0]:
                t = (y - r0[0]) / (r1[0] - r0[0]); ra, rb, cz = (r0[1] + (r1[1] - r0[1]) * t, r0[2] + (r1[2] - r0[2]) * t, r0[4] + (r1[4] - r0[4]) * t)
        if ra is None: continue
        dirn = Vector((math.sin(a), 0, math.cos(a))); base = Vector((math.sin(a) * ra * 0.97, y, cz + math.cos(a) * rb * 0.97))
        tip = base + dirn * rng.uniform(0.16, 0.28) + Vector((0, -rng.uniform(0.15, 0.3), -0.05))
        P.obj("Fur", cone(tuple(base), tuple(tip), rng.uniform(0.08, 0.12), 5), "Accent", 0, False)
    # the ceremonial blanket over its back: bands of gold, turquoise, black and white, fringed in gold
    def body_ab(y):
        for r0, r1 in zip(rings, rings[1:]):
            if r0[0] <= y <= r1[0]:
                t = (y - r0[0]) / (r1[0] - r1[0] + (r1[0] - r0[0])); return tuple(r0[k] + (r1[k] - r0[k]) * t for k in (1, 2, 4))
        return rings[-1][1], rings[-1][2], rings[-1][4]
    bm = bmesh.new(); NY, NA = 12, 18; grid = []
    for i in range(NY + 1):
        y = -1.12 + 0.82 * i / NY; ra, rb, cz = body_ab(y); row = []
        for j in range(NA + 1):
            t = math.radians(18 + 144 * j / NA)
            row.append((Vector((math.cos(t) * ra * 1.045, y, cz + math.sin(t) * rb * 1.045)), Vector((math.cos(t), 0, math.sin(t)))))
        grid.append(row)
    for i in range(NY):
        for j in range(NA):
            q = [grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1]]
            o = [bm.verts.new(p + n * 0.035) for p, n in q]; u = [bm.verts.new(p) for p, n in q]
            bm.faces.new(o); bm.faces.new(list(reversed(u)))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    def weave(c, n):
        u = (c.y + 1.12) / 0.82; ang_ = math.degrees(math.atan2(c.z - 0.1, c.x))
        if abs(ang_ - 90) > 64: return "Metal"
        band = int(u * 9) % 4
        if band == 1 and int((ang_ + 90) / 12) % 2: return "Trim"
        return ("Glass", "Dark", "Metal", "Glass")[band]
    P.obj("Blanket", bm, weave, 0, False)
    for side in (1, -1):
        t = math.radians(90 - side * 72)
        for i in range(10):
            y = -1.08 + 0.76 * i / 9; ra, rb, cz = body_ab(y)
            p0 = Vector((math.cos(t) * ra * 1.05, y, cz + math.sin(t) * rb * 1.05))
            P.obj("Tassel", cone(tuple(p0), tuple(p0 + Vector((side * 0.03, 0, -0.16))), 0.03, 5), "Metal", 0, False)
    # the head, low and forward
    HC = Vector((0, 1.5, -0.08)); h0 = len(P.parts)
    P.obj("Head", ball(tuple(HC), (0.55, 0.5, 0.55), 18, 9), "Accent", 1)
    for k in range(26):    # the shaggy forelock and cheeks
        a = rng.uniform(0, 2 * math.pi); b = rng.uniform(-0.2, 1.2)
        c = HC + Vector((math.sin(a) * 0.5 * math.cos(b * 0.6), -0.05 + math.cos(b) * 0.2, math.cos(a) * 0.45 * math.cos(b * 0.6)))
        if c.y > HC.y + 0.25 and abs(c.x) < 0.3 and c.z < HC.z + 0.25: continue
        P.obj("Shag", ball(tuple(c), (0.17, 0.15, 0.17), 8, 4), "Accent", 0)
    P.obj("Face", ball(tuple(HC + Vector((0, 0.38, -0.1))), (0.34, 0.32, 0.36), 16, 8), "Base", 1)
    P.obj("Snout", ball(tuple(HC + Vector((0, 0.66, -0.25))), (0.27, 0.16, 0.2), 14, 7), "Dark", 1)
    for s in (1, -1):
        P.obj("Nostril", ball(tuple(HC + Vector((s * 0.1, 0.8, -0.22))), (0.05, 0.03, 0.04), 8, 4), "Accent")
        # burning eyes under a scowling brow
        e = HC + Vector((s * 0.26, 0.6, 0.08))
        P.obj("EyeRim", ball(tuple(e - Vector((0, 0.01, 0))), (0.11, 0.06, 0.09), 12, 6), "Dark", 1)
        P.obj("Eye", ball(tuple(e + Vector((0, 0.02, 0))), (0.09, 0.06, 0.075), 12, 6), "Glow", 1)
        P.obj("Brow", hull([tuple(HC + Vector(v)) for v in ((s * 0.08, 0.66, 0.12), (s * 0.1, 0.64, 0.2), (s * 0.4, 0.55, 0.26), (s * 0.42, 0.5, 0.2),
                                                             (s * 0.26, 0.62, 0.24), (s * 0.24, 0.55, 0.3))]), "Accent", 0, False)
        # the horns: thick and ivory, sweeping out, up and forward, capped and ringed in gold
        root = HC + Vector((s * 0.42, 0.12, 0.32))
        hp = bez(root, root + Vector((s * 0.48, 0.05, -0.04)), root + Vector((s * 0.78, 0.15, 0.38)), root + Vector((s * 0.6, 0.42, 0.8)), 10)
        hr = [0.16, 0.155, 0.145, 0.135, 0.12, 0.105, 0.09, 0.07, 0.05, 0.03, 0.0]
        P.obj("Horn", pipe(hp, hr, 12), lambda c, n, tip=hp[-1], r0=root: "Metal" if (c - tip).length < 0.2 else "Belly")
        for j in (2, 4):
            t = (hp[j + 1] - hp[j - 1]).normalized(); m = t.to_track_quat("Z", "Y").to_matrix()
            P.obj("HornRing", xf(torus(hr[j] * 1.02, 0.03, 0.0, 16, 5), m, hp[j]), "Metal")
        # eagle feathers hanging from the horn roots, beaded in turquoise
        for j in range(2):
            f0 = root + Vector((s * (0.18 + j * 0.12), 0.08, -0.05)); f1 = f0 + Vector((s * 0.12, -0.05 - j * 0.04, -0.55))
            P.obj("Cord", pipe([f0, f0 + (f1 - f0) * 0.22], [0.015, 0.015], 5), "Dark")
            P.obj("Bead", ball(tuple(f0 + (f1 - f0) * 0.12), (0.035, 0.035, 0.035), 8, 4), "Glass")
            fp = [f0 + (f1 - f0) * (0.22 + 0.78 * i / 6) for i in range(7)]
            P.obj("Feather", pipe(fp, [0.03, 0.06, 0.075, 0.075, 0.065, 0.045, 0.0], 6), lambda c, n, f1=f1: "Dark" if (c - f1).length < 0.18 else "Trim")
            for v in P.parts[-1].data.vertices: v.co.y = f0.y + (v.co.y - f0.y) * 0.3
    for k in range(9):
        x = -0.4 + k * 0.1; c = HC + Vector((x, 0.42 - 2.2 * x * x * 0.3, 0.36 - 0.3 * x * x))
        P.obj("Band", ball(tuple(c), (0.06, 0.04, 0.05), 8, 4), "Glass" if k % 2 else "Metal", 1)
    # the medallion on its brow: a turquoise oval set in gold, a gold sun around it
    mc = HC + Vector((0, 0.52, 0.33))
    P.obj("Medallion", xf(lathe([(0.0, -0.03), (0.16, -0.03), (0.17, 0.0), (0.16, 0.03), (0.0, 0.03)], 20, "y"), Matrix.Rotation(math.radians(-25), 3, "X"), mc), "Metal")
    P.obj("Stone", ball(tuple(mc + Vector((0, 0.03, 0.0))), (0.11, 0.05, 0.13), 14, 7), "Glass", 1)
    for k in range(10):
        a = 2 * math.pi * k / 10
        P.obj("Ray", cone(tuple(mc + Vector((math.sin(a) * 0.16, 0.0, math.cos(a) * 0.16))), tuple(mc + Vector((math.sin(a) * 0.27, -0.03, math.cos(a) * 0.27))), 0.035, 4), "Metal", 0, False)
    P.obj("NoseRing", xf(torus(0.11, 0.022, 0.0, 18, 5), Matrix.Rotation(math.radians(90), 3, "Y"), HC + Vector((0, 0.8, -0.38))), "Metal")
    # the beard
    for k in range(9):
        c = HC + Vector((rng.uniform(-0.18, 0.18), 0.3 - k * 0.04, -0.5 - k * 0.06))
        P.obj("Beard", ball(tuple(c), (0.18 - k * 0.012, 0.15, 0.14), 10, 5), "Accent", 0)
    for ob in P.parts[h0:]:
        for v in ob.data.vertices: v.co = (v.co - (HC - Vector((0, 0.35, 0)))) * 1.45 + (HC - Vector((0, 0.35, 0)))
    # the legs, galloping: the forelegs shaggy, the hooves shod in gold and trailing spirit fire
    for name, y0, shag in (("SwayFore", 0.55, True), ("SwayHind", -0.95, False)):
        hub = (0, y0, -0.2)
        for s in (1, -1):
            top = Vector((s * 0.42, y0, -0.15)); knee = Vector((s * 0.46, y0 + 0.05, -0.7)); foot = Vector((s * 0.44, y0 - 0.02, -1.08))
            P.part(name, pipe([top, knee, foot], [0.24 if shag else 0.2, 0.15, 0.12], 12), "Accent" if shag else "Base", hub, 1)
            if shag:
                for k in range(5):
                    P.part(name, ball(tuple(top + (knee - top) * (k / 4.0) + Vector((s * 0.06, 0.04, 0))), (0.2, 0.18, 0.16), 8, 4), "Accent", hub, 0)
            P.part(name, lathe([(0.0, 0.0), (0.15, 0.0), (0.14, 0.12), (0.11, 0.17), (0.0, 0.17)], 12, "z", tuple(foot + Vector((0, 0, -0.17)))), "Metal", hub, 0)
            for k in range(4):
                P.part(name, cone(tuple(foot + Vector((rng.uniform(-0.05, 0.05), -0.02, -0.2))), tuple(foot + Vector((rng.uniform(-0.1, 0.1), -0.35 - k * 0.07, -0.42 + k * 0.06))), 0.08, 6), "Glow", hub, 0, False)
    # the tail, a tuft
    tl = bez((0, -1.33, 0.2), (0, -1.55, 0.25), (0, -1.65, 0.05), (0, -1.7, -0.25), 6)
    P.obj("Tail", pipe(tl, [0.07, 0.06, 0.05, 0.05, 0.05, 0.04, 0.0], 8), "Base")
    P.obj("Tuft", ball(tuple(tl[-2]), (0.1, 0.1, 0.18), 8, 4), "Accent", 0)
    P.part("Muzzle", ball(tuple(HC + Vector((0, 0.86, -0.2))), (0.06, 0.04, 0.05), 8, 4), "Lamp", tuple(HC + Vector((0, 0.86, -0.2))))
    return P

# ================================================================= the dust devil (in place of the gold mine mesa; the stampede king was rejected)
def W_devil():
    """The last boss: the dust devil, a desert genie of whirling sand - a broad chest and shoulders of swirling dust, arms crossed in gold
    cuffs, a big scowling face with burning amber eyes under heavy brows, a great handlebar moustache and a gold-toothed grin, a red bandana
    at his throat, a wide cowboy hat with a gold band and a sheriff star taken as a trophy; below the waist he is a tornado, its funnel
    turning, and tumbleweeds and dust whirl round him."""
    P = Boss("devil", {"Base": ((0.86, 0.64, 0.38), 0.3), "Belly": ((0.97, 0.86, 0.64), 0.3), "Accent": ((0.78, 0.10, 0.07), 0.45),
                       "Trim": ((0.99, 0.97, 0.92), 0.5), "Glass": ((0.50, 0.32, 0.16), 0.3), "Dark": ((0.16, 0.08, 0.04), 0.4),
                       "Glow": ((1.0, 0.60, 0.08), 0.5), "Metal": GOLD, "Lamp": ((1.0, 0.88, 0.45), 0.8)})
    rng = random.Random(21)
    def swirl(c, n):
        a = math.atan2(c.y, c.x); w = math.sin(a * 3.0 + c.z * 5.0)
        return "Belly" if w > 0.7 else ("Glass" if w < -0.82 else "Base")
    # the torso: chest, belly and shoulders of swirling sand
    P.obj("Chest", ball((0, 0.05, 0.55), (0.82, 0.55, 0.62), 26, 13), swirl, 1)
    P.obj("Waist", ball((0, 0.0, 0.0), (0.6, 0.45, 0.5), 18, 9), swirl, 1)
    for s in (1, -1):
        P.obj("Shoulder", ball((s * 0.82, 0.0, 0.85), (0.34, 0.32, 0.32), 16, 8), swirl, 1)
    # the arms, crossed over the chest, gold cuffs at the wrists
    for s, z, yy in ((1, 0.48, 0.55), (-1, 0.32, 0.62)):
        sh = Vector((s * 0.95, 0.05, 0.75)); el = Vector((s * 0.98, 0.45, 0.32)); wr = Vector((-s * 0.45, yy, z)); fist = Vector((-s * 0.72, yy - 0.04, z + 0.02))
        P.obj("UpperArm", pipe([sh, (sh + el) * 0.5 + Vector((s * 0.08, 0, 0)), el], [0.26, 0.25, 0.21], 14), swirl, 1)
        P.obj("Elbow", ball(tuple(el), (0.22, 0.22, 0.22), 12, 6), swirl, 1)
        P.obj("Forearm", pipe([el, (el + wr) * 0.5 + Vector((0, 0.06, 0.02)), wr], [0.21, 0.2, 0.17], 14), swirl, 1)
        P.obj("Cuff", xf(torus(0.19, 0.05, 0.0, 20, 6), Matrix.Rotation(math.radians(90), 3, "Y"), wr + Vector((s * 0.02, 0, 0))), "Metal")
        P.obj("Fist", ball(tuple(fist), (0.2, 0.18, 0.17), 12, 6), "Base", 1)
    # the head
    HC = Vector((0, 0.34, 1.62)); h0 = len(P.parts)
    P.obj("Head", ball(tuple(HC), (0.52, 0.48, 0.55), 22, 11), "Base", 1)
    P.obj("Jowls", ball(tuple(HC + Vector((0, 0.12, -0.28))), (0.46, 0.38, 0.3), 18, 9), "Base", 1)
    P.obj("Nose", ball(tuple(HC + Vector((0, 0.5, -0.02))), (0.12, 0.14, 0.15), 12, 6), "Base", 1)
    for s in (1, -1):
        e = HC + Vector((s * 0.2, 0.42, 0.14))
        P.obj("Socket", ball(tuple(e - Vector((0, 0.02, 0))), (0.13, 0.06, 0.1), 12, 6), "Dark", 1)
        P.obj("Eye", ball(tuple(e + Vector((0, 0.02, 0))), (0.1, 0.05, 0.075), 12, 6), "Glow", 1)
        P.obj("EyeCore", ball(tuple(e + Vector((s * 0.01, 0.06, 0))), (0.035, 0.02, 0.04), 8, 4), "Lamp")
        P.obj("Brow", hull([tuple(HC + Vector(v)) for v in ((s * 0.04, 0.5, 0.2), (s * 0.06, 0.46, 0.27), (s * 0.36, 0.38, 0.36), (s * 0.4, 0.32, 0.3),
                                                             (s * 0.2, 0.46, 0.33), (s * 0.06, 0.36, 0.22), (s * 0.36, 0.26, 0.32))]), "Dark", 0, False)
        # the handlebar moustache, curling up at the ends
        m0 = HC + Vector((0.0, 0.58, -0.14))
        P.obj("Moustache", pipe(bez(m0, m0 + Vector((s * 0.2, 0.0, -0.06)), m0 + Vector((s * 0.48, -0.12, -0.1)), m0 + Vector((s * 0.58, -0.2, 0.14)), 10),
                                [0.07, 0.09, 0.1, 0.1, 0.09, 0.08, 0.07, 0.055, 0.04, 0.025, 0.0], 8), "Dark", 1)
        P.obj("Ear", ball(tuple(HC + Vector((s * 0.52, 0.0, 0.0))), (0.08, 0.12, 0.15), 10, 5), "Base", 1)
        P.obj("Earring", xf(torus(0.07, 0.016, 0.0, 14, 4), Matrix.Rotation(math.radians(90), 3, "Y"), HC + Vector((s * 0.56, 0.02, -0.18))), "Metal")
    # the grin under the moustache: a dark mouth, white teeth, one of gold
    P.obj("Mouth", ball(tuple(HC + Vector((0, 0.44, -0.33))), (0.26, 0.08, 0.1), 14, 7), "Dark", 1)
    for k in range(6):
        x = -0.2 + k * 0.08
        P.obj("Tooth", box(tuple(HC + Vector((x, 0.5 - 1.2 * x * x, -0.3))), (0.07, 0.04, 0.07)), "Metal" if k == 4 else "Trim", 0, False)
    P.obj("Chin", ball(tuple(HC + Vector((0, 0.32, -0.5))), (0.24, 0.18, 0.14), 12, 6), "Base", 1)
    for ob in P.parts[h0:]:
        for v in ob.data.vertices: v.co = (v.co - HC) * 1.28 + HC
    # the bandana at his throat
    P.obj("Bandana", torus(0.48, 0.1, HC.z - 0.76, 26, 8), "Accent")
    for v in P.parts[-1].data.vertices: v.co.y = v.co.y * 0.9 + 0.2
    P.obj("BandanaTip", cone(tuple(HC + Vector((0, 0.4, -0.8))), tuple(HC + Vector((0, 0.66, -1.14))), 0.24, 6), "Accent", 0, False)
    for v in P.parts[-1].data.vertices: v.co.x *= 1.25
    # the hat, wide, a gold band and the star
    for b, col in zip(hat((0, 0, 0), 1.62, math.radians(16)), ("Dark", "Dark", "Metal")):
        P.obj("Hat", xf(b, None, HC + Vector((0, -0.1, 0.62))), col, 0, col != "Dark")
    P.obj("Star", xf(star((0, 0, 0), 0.16, 0.07, 0.05), Matrix.Rotation(math.radians(16), 3, "X"), HC + Vector((0, 0.37, 0.95))), "Metal", 0, False)
    # below the waist, the tornado: a funnel of whirling dust, turning
    prof = [(0.66, -0.15), (0.62, -0.45), (0.54, -0.85), (0.44, -1.25), (0.33, -1.65), (0.22, -2.0), (0.12, -2.3), (0.0, -2.45)]
    bm = lathe([(r, z) for (r, z) in prof for _ in (0,)], 32, "z")
    bmesh.ops.subdivide_edges(bm, edges=[e for e in bm.edges if abs(e.verts[0].co.z - e.verts[1].co.z) > 0.01], cuts=2, use_grid_fill=True)
    for v in bm.verts:
        a = math.atan2(v.co.y, v.co.x); r = Vector((v.co.x, v.co.y, 0))
        if r.length > 1e-4: v.co += r.normalized() * (0.09 + 0.04 * v.co.z) * math.sin(a * 4.0 + v.co.z * 6.0)
    def fpaint(c, n):
        w = math.sin(math.atan2(c.y, c.x) * 4.0 + c.z * 6.0)
        return "Belly" if w > 0.55 else ("Glass" if w < -0.7 else "Base")
    P.part("SpinFunnel", bm, fpaint, (0, 0, 0), 1)
    for k in range(16):   # streaks of wind sweeping round the funnel: tapered arcs
        t = k / 15; z = -2.1 + t * 1.85; R = 0.28 + 0.62 * t + 0.08 * math.sin(k * 1.7)
        a0 = k * 2.4; span = math.radians(150 + 40 * math.sin(k))
        arc = [Vector((math.cos(a0 + span * i / 10) * R, math.sin(a0 + span * i / 10) * R, z + 0.12 * (i / 10 - 0.5))) for i in range(11)]
        w = 0.035 + 0.04 * t
        P.part("SpinFunnel", pipe(arc, [w * math.sin(math.pi * i / 10) for i in range(11)], 6), "Belly" if k % 2 else "Base", (0, 0, 0), 0)
    # a gold belt with a big buckle where the man ends and the storm begins
    P.obj("Belt", torus(0.6, 0.075, -0.12, 30, 6), "Metal")
    for v in P.parts[-1].data.vertices: v.co.y = v.co.y * 0.78
    P.obj("Buckle", xf(lathe([(0.0, -0.04), (0.2, -0.04), (0.22, 0.0), (0.2, 0.04), (0.0, 0.04)], 20, "y"), None, (0, 0.47, -0.12)), "Metal")
    P.obj("BuckleStone", ball((0, 0.52, -0.12), (0.09, 0.03, 0.09), 10, 5), "Accent", 1)
    # tumbleweeds, pebbles and puffs of dust whirling round him
    for k in range(8):
        a = 2 * math.pi * k / 8 + 0.2
        c = Vector((math.cos(a) * 1.95, math.sin(a) * 1.8, -0.75 + 0.3 * math.sin(a * 2)))
        for j in range(9):
            m = Matrix.Rotation(rng.uniform(0, math.pi), 3, "X") @ Matrix.Rotation(rng.uniform(0, math.pi), 3, "Y")
            P.part("SpinWeeds", xf(torus(0.26, 0.022, 0.0, 12, 3), m, c), "Glass", (0, 0, -0.75), 0)
        P.part("SpinWeeds", ball(tuple(c), (0.14, 0.14, 0.14), 8, 4), "Glass", (0, 0, -0.75), 0)
    P.part("Muzzle", ball(tuple(HC + Vector((0, 0.56, -0.33))), (0.06, 0.04, 0.05), 8, 4), "Lamp", tuple(HC + Vector((0, 0.56, -0.33))))
    return P


# ================================================================= 4 (new). the scorpion king (2026-10-12, in place of the outlaw zeppelin)
def W_scorpion():
    """The scorpion king of the badlands: a colossal crimson-black scorpion in plated armour edged in gold, a jewelled gold crown on its
    head, a cluster of burning eyes, snapping mandibles, two huge pincers reaching for the player and swinging, eight jointed legs, gold
    bands round its tail segments, and the tail arched high over its back with a glowing golden stinger aimed forward; desert dust and
    gold coins whirl round it."""
    P = Boss("scorpion", {"Base": ((0.32, 0.06, 0.05), 0.55), "Belly": ((0.86, 0.70, 0.45), 0.35), "Accent": ((0.07, 0.05, 0.06), 0.6),
                          "Trim": GOLD, "Glass": ((0.08, 0.75, 0.70), 0.85), "Dark": ((0.03, 0.02, 0.02), 0.5),
                          "Glow": ((1.0, 0.40, 0.05), 0.5), "Metal": BRASS, "Lamp": ((1.0, 0.88, 0.30), 0.8)})
    def plate(c, n):
        if n.z < -0.35: return "Belly"
        if abs(c.x) < 0.05 and n.z > 0.5: return "Trim"   # a gold ridge down the middle
        if n.z > 0.6 and (abs(c.x) * 4 + c.y * 2) % 1.0 < 0.12: return "Accent"   # engraved chevrons
        return "Base"
    # the carapace and the head
    P.obj("Carapace", loft([(1.05, 0.25, 0.12, 0, 0.12), (0.85, 0.5, 0.22, 0, 0.15), (0.45, 0.62, 0.3, 0, 0.18), (0.0, 0.66, 0.32, 0, 0.18),
                            (-0.45, 0.6, 0.28, 0, 0.15)], 18), plate, 1)
    P.obj("Rim", loft([(1.0, 0.3, 0.06, 0, 0.0), (0.5, 0.68, 0.08, 0, 0.02), (-0.45, 0.64, 0.08, 0, 0.02)], 18), "Trim", 1)
    P.obj("Gem", ball((0, 0.25, 0.5), (0.13, 0.17, 0.07), 12, 6), "Glass")
    P.obj("GemSet", xf(torus(0.16, 0.03, 0.0, 18, 5), Matrix.Scale(1.0, 3), (0, 0.25, 0.47)), "Trim")
    # the eye cluster: two big blazing eyes and a row of small ones
    for s in (1, -1):
        P.obj("Eye", ball((s * 0.12, 0.88, 0.35), (0.085, 0.085, 0.07), 10, 5), "Glow")
        P.obj("Brow", hull([(s * 0.02, 0.95, 0.44), (s * 0.24, 0.85, 0.46), (s * 0.24, 0.82, 0.4), (s * 0.04, 0.92, 0.38)]), "Accent", 0, False)
        for k in range(3):
            P.obj("SmallEye", ball((s * (0.28 + k * 0.07), 0.95 - k * 0.08, 0.24), (0.035, 0.035, 0.035), 6, 3), "Lamp")
        # mandibles
        P.obj("Mandible", pipe(bez((s * 0.1, 1.0, 0.08), (s * 0.12, 1.18, 0.06), (s * 0.05, 1.28, 0.02), (s * 0.0, 1.28, -0.02), 4), [0.06, 0.05, 0.035, 0.02, 0.0], 6), "Accent")
    # the gold crown
    P.obj("Crown", lathe([(0.2, 0.0), (0.22, 0.0), (0.2, 0.12), (0.18, 0.12)], 18, "z", (0, 0.7, 0.42)), "Trim")
    for k in range(7):
        a = 2 * math.pi * k / 7
        b = Vector((math.sin(a) * 0.2, 0.7 + math.cos(a) * 0.2, 0.53))
        P.obj("CrownPoint", cone(b, b + Vector((math.sin(a) * 0.03, math.cos(a) * 0.03, 0.17)), 0.05, 4), "Trim", 0, False)
        P.obj("CrownGem", ball(tuple(b + Vector((0, 0, -0.06))), (0.03, 0.03, 0.03), 6, 3), "Glass" if k % 2 else "Glow")
    # the pincers: an arm, a great armoured claw with a fixed and a moving finger; each swings
    for s in (1, -1):
        sh = Vector((s * 0.5, 0.7, 0.1))
        name = "SwayClawR" if s > 0 else "SwayClawL"
        el = sh + Vector((s * 0.55, 0.25, 0.05)); wr = el + Vector((-s * 0.15, 0.5, 0.05))
        P.part(name, pipe([sh, el], [0.13, 0.11], 10), plate, tuple(sh), 1)
        P.part(name, ball(tuple(el), (0.13, 0.13, 0.13), 10, 5), "Trim", tuple(sh))
        P.part(name, pipe([el, wr], [0.11, 0.12], 10), plate, tuple(sh), 1)
        palm = wr + Vector((0, 0.25, 0))
        P.part(name, ball(tuple(palm), (0.22, 0.32, 0.18), 14, 7), plate, tuple(sh), 1)
        P.part(name, xf(torus(0.2, 0.03, 0.0, 16, 4), Matrix.Rotation(math.radians(90), 3, "X"), tuple(palm + Vector((0, -0.2, 0)))), "Trim", tuple(sh))
        fixed = bez(palm + Vector((s * 0.1, 0.25, 0.0)), palm + Vector((s * 0.15, 0.5, 0.0)), palm + Vector((s * 0.05, 0.7, 0.0)), palm + Vector((-s * 0.08, 0.78, 0.0)), 5)
        move = bez(palm + Vector((-s * 0.1, 0.25, 0.0)), palm + Vector((-s * 0.22, 0.45, 0.0)), palm + Vector((-s * 0.18, 0.62, 0.0)), palm + Vector((-s * 0.04, 0.72, 0.0)), 5)
        for f in (fixed, move):
            P.part(name, pipe(f, [0.11, 0.1, 0.08, 0.06, 0.035, 0.0], 8), "Accent", tuple(sh), 1)
            for k in (1, 3):
                P.part(name, cone(tuple(f[k]), tuple(f[k] + Vector(((-0.1 if f is fixed else 0.1) * s, 0.02, 0))), 0.025, 4), "Trim", tuple(sh), 0, False)
        # eight legs: four a side, jointed, reaching out and down
        for k in range(4):
            hip = Vector((s * 0.55, 0.35 - k * 0.3, 0.05))
            knee = hip + Vector((s * 0.45, 0.1 - k * 0.05, 0.25)); foot = knee + Vector((s * 0.3, 0.05 - k * 0.08, -0.65))
            P.obj("Leg", pipe([hip, knee, foot], [0.07, 0.055, 0.02], 7), lambda c, n: "Belly" if n.z < -0.5 else "Base")
            P.obj("Knee", ball(tuple(knee), (0.07, 0.07, 0.07), 8, 4), "Trim")
    # the abdomen and the tail arched over its back, gold banded, the stinger aimed forward
    for k in range(4):
        y = -0.55 - k * 0.24; r = 0.55 - k * 0.08
        P.obj("Segment", ball((0, y, 0.15), (r, 0.18, 0.26 - k * 0.02), 16, 7), plate, 1)
        P.obj("SegBand", ball((0, y - 0.15, 0.15), (r * 0.9, 0.03, 0.2), 14, 5), "Trim")
    tb = Vector((0, -1.35, 0.2))
    tail = bez(tb, tb + Vector((0, -0.8, 0.6)), tb + Vector((0, -0.6, 1.9)), tb + Vector((0, 0.45, 2.1)), 9)
    radii = [0.26 - 0.016 * i for i in range(10)]
    for i in range(1, len(tail)):
        p = tail[i]; r = radii[i]
        P.part("SwayTail", ball(tuple(p), (r, r * 1.1, r), 12, 6), plate, tuple(tb), 1)
        if i % 2 == 0:
            t = (tail[min(i + 1, 9)] - tail[i - 1]).normalized()
            ring = torus(r * 0.95, 0.03, 0.0, 16, 4)
            q = t.to_track_quat("Z", "Y").to_matrix()
            for v in ring.verts: v.co = q @ v.co + p
            P.part("SwayTail", ring, "Trim", tuple(tb))
        P.part("SwayTail", cone(tuple(p + Vector((0, 0, r * 0.8))), tuple(p + Vector((0, -0.05, r * 0.8 + 0.12))), 0.04, 4), "Trim", tuple(tb), 0, False)
    end = tail[-1]
    bulb = end + Vector((0, 0.2, -0.08))
    P.part("SwayTail", ball(tuple(bulb), (0.2, 0.26, 0.2), 14, 7), "Trim", tuple(tb), 1)
    P.part("SwayTail", ball(tuple(bulb + Vector((0, 0.05, -0.02))), (0.12, 0.16, 0.12), 10, 5), "Glow", tuple(tb))
    barb = pipe(bez(bulb + Vector((0, 0.2, -0.05)), bulb + Vector((0, 0.4, -0.1)), bulb + Vector((0, 0.55, -0.3)), bulb + Vector((0, 0.5, -0.5)), 5), [0.09, 0.07, 0.05, 0.035, 0.02, 0.0], 8)
    P.part("SwayTail", barb, "Lamp", tuple(tb))
    mz = bulb + Vector((0, 0.5, -0.52))
    # dust and gold coins whirling round it
    for k in range(12):
        a = 2 * math.pi * k / 12
        c = Vector((math.sin(a) * 2.0, -0.2 + math.cos(a) * 1.8, 0.3 + 0.3 * math.sin(a * 3)))
        if k % 2:
            P.part("SpinDust", xf(lathe([(0.0, -0.02), (0.1, -0.02), (0.1, 0.02), (0.0, 0.02)], 12, "z"), Matrix.Rotation(math.radians(70), 3, "X"), tuple(c)), "Trim", (0, -0.2, 0.3))
        else:
            for j in range(3):
                P.part("SpinDust", ball(tuple(c + Vector((0.08 * j, -0.06 * j, 0.03 * j))), (0.1 - 0.02 * j,) * 3, 6, 3), "Belly", (0, -0.2, 0.3))
    P.part("Muzzle", ball(tuple(mz), (0.07, 0.07, 0.07), 8, 4), "Glow", tuple(mz))
    return P


# ================================================================= 5 (new). the ghost rider (2026-10-12, in place of the gold mine mesa, the last boss)
def W_ghostrider():
    """The last boss: the ghost rider - a skeleton gunslinger on a black stallion of fire, charging out of the sky at the player. The horse
    gallops on burning hooves, its mane and tail roaring flames, eyes blazing, a gold-studded bridle and a red saddle blanket; the rider has
    a grinning skull with burning eye sockets under a wide black hat with a gold band and a silver skull-star, a red bandana, a long brown
    duster streaming behind him, crossed bandoliers, and two silver revolvers levelled at the player; spirit flames and skull lanterns
    whirl round them."""
    P = Boss("ghostrider", {"Base": ((0.07, 0.06, 0.09), 0.55), "Belly": ((0.93, 0.90, 0.80), 0.35), "Accent": ((0.75, 0.08, 0.06), 0.45),
                            "Trim": GOLD, "Glass": ((0.36, 0.22, 0.12), 0.3), "Dark": ((0.02, 0.02, 0.02), 0.5),
                            "Glow": ((1.0, 0.42, 0.04), 0.5), "Metal": ((0.78, 0.80, 0.86), 0.85), "Lamp": ((1.0, 0.85, 0.30), 0.8)})
    flame = lambda base: (lambda c, n, b=Vector(base): "Lamp" if (c - b).length < 0.12 else "Glow")
    # ---- the horse
    P.obj("Barrel", loft([(0.75, 0.24, 0.3, 0, 0.05), (0.45, 0.36, 0.4, 0, 0.0), (0.0, 0.38, 0.4, 0, -0.02), (-0.45, 0.37, 0.4, 0, 0.0),
                          (-0.8, 0.3, 0.33, 0, 0.05), (-0.95, 0.12, 0.15, 0, 0.1)], 18), lambda c, n: "Base", 1)
    P.obj("Neck", pipe([(0, 0.55, 0.15), (0, 0.85, 0.5), (0, 1.05, 0.82)], [0.27, 0.22, 0.17], 14), "Base", 1)
    P.obj("Head", loft([(0.92, 0.15, 0.2, 0, 0.92), (1.15, 0.14, 0.17, 0, 0.82), (1.4, 0.11, 0.12, 0, 0.66), (1.56, 0.09, 0.1, 0, 0.56), (1.62, 0.05, 0.06, 0, 0.53)], 14), "Base", 1)
    P.obj("Nose", ball((0, 1.55, 0.54), (0.1, 0.08, 0.09), 10, 5), "Base", 1)
    for s in (1, -1):
        P.obj("Nostril", ball((s * 0.05, 1.63, 0.56), (0.025, 0.02, 0.025), 6, 3), "Glow")
        P.obj("HorseEye", ball((s * 0.13, 1.1, 0.9), (0.04, 0.07, 0.05), 8, 4), "Glow")
        P.obj("EyeFlame", cone((s * 0.14, 1.06, 0.92), (s * 0.2, 0.85, 1.0), 0.04, 5), "Lamp", 0, False)
        P.obj("Ear", cone((s * 0.08, 0.98, 1.0), (s * 0.12, 0.92, 1.22), 0.05, 5), "Base", 0, False)
    # the bridle: gold studded straps, a bit, the reins to the rider's hand
    P.obj("Noseband", xf(torus(0.13, 0.022, 0.0, 16, 4), Matrix.Rotation(math.radians(-60), 3, "X"), (0, 1.38, 0.66)), "Trim")
    P.obj("Browband", xf(torus(0.16, 0.02, 0.0, 16, 4), Matrix.Rotation(math.radians(-35), 3, "X"), (0, 1.0, 0.92)), "Trim")
    for s in (1, -1):
        P.obj("Rein", pipe([(s * 0.13, 1.42, 0.6), (s * 0.2, 0.9, 0.55), (s * 0.18, 0.3, 0.78)], [0.015, 0.015, 0.015], 4), "Accent")
        P.obj("Stud", ball((s * 0.14, 1.42, 0.62), (0.03, 0.03, 0.03), 6, 3), "Trim")
    # the mane and the tail: roaring flames
    for k in range(9):
        t = k / 8
        b = Vector((0, 1.0 - t * 0.5, 0.95 - t * 0.7))
        L = 0.45 + 0.15 * math.sin(math.pi * t)
        P.obj("Mane", pipe(bez(b, b + Vector((0.05 * (1 if k % 2 else -1), -0.15, 0.15)), b + Vector((0, -0.4, 0.3)), b + Vector((0.03, -L - 0.2, 0.35)), 5), [0.11, 0.09, 0.07, 0.05, 0.025, 0.0], 7), flame(b), 0)
    tb = Vector((0, -0.95, 0.15))
    for k in range(6):
        a = math.radians(-50 + k * 20)
        tip = tb + Vector((math.sin(a) * 0.35, -1.0 - 0.15 * (k % 2), 0.35 + math.cos(a) * 0.25))
        P.part("SwayTail", pipe(bez(tb, tb + Vector((math.sin(a) * 0.1, -0.3, 0.05)), tip + Vector((0, 0.3, -0.15)), tip, 6), [0.1, 0.1, 0.09, 0.07, 0.05, 0.025, 0.0], 7), flame(tb), tuple(tb), 0)
    # the saddle blanket, saddle and stirrups
    P.obj("Blanket", loft([(0.3, 0.42, 0.06, 0, 0.32), (-0.45, 0.42, 0.06, 0, 0.32)], 16), lambda c, n: "Trim" if abs(c.y + 0.07) > 0.33 or abs(c.x) > 0.38 else "Accent", 0)
    P.obj("Saddle", ball((0, -0.08, 0.42), (0.26, 0.36, 0.1), 14, 6), "Glass", 1)
    P.obj("Horn", pipe([(0, 0.22, 0.42), (0, 0.26, 0.6)], [0.05, 0.06], 8), "Trim")
    # the legs: galloping - forelegs reaching, hind legs driving - on hooves of fire
    for i, (s, y0, front) in enumerate(((1, 0.5, True), (-1, 0.5, True), (1, -0.65, False), (-1, -0.65, False))):
        hip = Vector((s * 0.22, y0, -0.15))
        name = "Sway%d" % i
        if front:
            knee = hip + Vector((0, 0.35 + 0.1 * s, -0.3)); hoof = knee + Vector((0, 0.15, -0.45))
        else:
            knee = hip + Vector((0, -0.2, -0.4)); hoof = knee + Vector((0, -0.35 + 0.1 * s, -0.3))
        P.part(name, pipe([hip, (hip + knee) * 0.5, knee, hoof], [0.17, 0.13, 0.09, 0.075], 10), "Base", tuple(hip), 1)
        P.part(name, lathe([(0.075, 0.0), (0.085, -0.1), (0.0, -0.11)], 10, "z", tuple(hoof)), "Trim", tuple(hip))
        for k in range(5):
            a = 2 * math.pi * k / 5
            b = hoof + Vector((math.sin(a) * 0.06, math.cos(a) * 0.06, -0.08))
            P.part(name, cone(tuple(b), tuple(b + Vector((math.sin(a) * 0.05, -0.18, -0.12 + 0.05 * (k % 2)))), 0.05, 5), "Glow" if k % 2 else "Lamp", tuple(hip), 0, False)
    # ---- the rider (built at his own scale, then made 1.25 times bigger about the saddle so he reads)
    n0 = len(P.parts)
    for s in (1, -1):   # legs astride, boots in the stirrups
        P.obj("Thigh", pipe([(s * 0.2, -0.1, 0.5), (s * 0.4, 0.1, 0.35), (s * 0.42, 0.0, 0.0)], [0.09, 0.08, 0.07], 8), "Glass")
        P.obj("Boot", loft([(0.12, 0.08, 0.08, s * 0.42, -0.05), (-0.05, 0.08, 0.09, s * 0.42, -0.08), (-0.1, 0.06, 0.05, s * 0.42, -0.06)], 10), "Dark", 1)
        P.obj("BootTop", loft([(0.06, 0.08, 0.12, s * 0.42, 0.04), (-0.06, 0.085, 0.13, s * 0.42, 0.04)], 10), "Dark", 0)
        P.obj("Spur", xf(torus(0.04, 0.01, 0.0, 10, 3), Matrix.Rotation(math.radians(90), 3, "Y"), (s * 0.42, -0.13, -0.06)), "Trim")
        P.obj("Stirrup", xf(torus(0.07, 0.015, 0.0, 12, 4), Matrix.Rotation(math.radians(90), 3, "X"), (s * 0.42, 0.02, -0.1)), "Trim")
    def coat(c, n):
        if abs(c.x) < 0.11 and n.y > 0.4:   # the coat hangs open on his ribs
            return "Dark" if (c.z * 14) % 1.0 < 0.35 else "Belly"
        return "Glass"
    P.obj("Torso", lathe([(0.0, 0.45), (0.24, 0.48), (0.27, 0.75), (0.32, 1.0), (0.3, 1.1), (0.0, 1.12)], 18, "z", (0, -0.05, 0)), coat, 1)
    for s in (1, -1):   # crossed bandoliers with brass bullets
        a0 = Vector((s * 0.26, 0.2, 1.05)); a1 = Vector((-s * 0.25, 0.22, 0.55))
        P.obj("Bandolier", pipe([a0, (a0 + a1) * 0.5 + Vector((0, 0.08, 0)), a1], [0.035, 0.035, 0.035], 6), "Accent")
        for k in range(1, 6):
            q = a0 + (a1 - a0) * (k / 6) + Vector((0, 0.07 if 1 < k < 5 else 0.04, 0))
            P.obj("Bullet", cone(tuple(q - Vector((0, 0, 0.03))), tuple(q + Vector((0, 0, 0.05))), 0.018, 4), "Trim", 0, False)
    P.obj("Belt", xf(torus(0.25, 0.03, 0.0, 18, 4), None, (0, -0.05, 0.52)), "Dark")
    P.obj("Buckle", box((0, 0.21, 0.52), (0.1, 0.03, 0.07)), "Trim", 0, False)
    P.obj("Bandana", lathe([(0.17, 1.08), (0.2, 1.12), (0.16, 1.2), (0.12, 1.2)], 16, "z", (0, -0.03, 0)), "Accent")
    P.obj("BandanaTip", hull([(-0.12, 0.13, 1.1), (0.12, 0.13, 1.1), (0, 0.18, 0.95), (0, 0.12, 1.12)]), "Accent", 0, False)
    # the skull: burning sockets, a grin of teeth
    SC = Vector((0, 0.0, 1.38))
    P.obj("Skull", ball(tuple(SC), (0.22, 0.22, 0.24), 16, 8), "Belly", 1)
    P.obj("Jaw", ball((0, 0.06, 1.2), (0.15, 0.13, 0.08), 12, 6), "Belly", 1)
    for s in (1, -1):
        P.obj("Socket", ball((s * 0.09, 0.17, 1.4), (0.075, 0.06, 0.07), 10, 5), "Dark")
        P.obj("Flame", ball((s * 0.09, 0.2, 1.4), (0.04, 0.03, 0.04), 8, 4), "Glow")
        P.obj("FlameLick", cone((s * 0.09, 0.19, 1.43), (s * 0.13, 0.12, 1.56), 0.03, 5), "Lamp", 0, False)
        P.obj("Cheek", ball((s * 0.15, 0.1, 1.3), (0.05, 0.04, 0.04), 6, 3), "Belly")
    P.obj("NoseHole", hull([(0.0, 0.21, 1.34), (0.03, 0.19, 1.3), (-0.03, 0.19, 1.3), (0, 0.17, 1.31)]), "Dark", 0, False)
    for k in range(6):
        x = (k - 2.5) * 0.04
        P.obj("Tooth", box((x, 0.17 - abs(x) * 0.3, 1.24), (0.032, 0.03, 0.05)), "Belly", 0, False)
        P.obj("ToothGap", box((x + 0.02, 0.18 - abs(x) * 0.3, 1.24), (0.006, 0.02, 0.05)), "Dark", 0, False)
    # the hat: wide, black, a gold band and a silver skull-star
    for k, bm in enumerate(hat((0, -0.02, 1.52), 1.0, math.radians(-8))):
        P.obj("Hat", bm, ("Base", "Base", "Trim")[k], 0)
    P.obj("HatStar", star((0, 0.27, 1.62), 0.07, 0.03, 0.025), "Metal", 0, False)
    # arms: both revolvers levelled at the player
    for s in (1, -1):
        sh = Vector((s * 0.3, -0.05, 1.0)); el = sh + Vector((s * 0.12, 0.25, -0.1)); wr = el + Vector((-s * 0.04, 0.3, 0.05))
        P.obj("Sleeve", pipe([sh, el, wr], [0.09, 0.075, 0.07], 8), "Glass")
        P.obj("Cuff", xf(torus(0.07, 0.02, 0.0, 12, 4), Matrix.Rotation(math.radians(90), 3, "X"), tuple(wr)), "Belly")
        hand = wr + Vector((0, 0.05, 0))
        P.obj("Hand", ball(tuple(hand), (0.055, 0.06, 0.055), 8, 4), "Belly")
        P.obj("Grip", box(tuple(hand + Vector((0, 0.0, -0.06))), (0.04, 0.06, 0.1), Matrix.Rotation(math.radians(20), 3, "X")), "Glass", 0, False)
        P.obj("Cylinder", pipe([hand + Vector((0, 0.04, 0.05)), hand + Vector((0, 0.14, 0.05))], [0.045, 0.045], 8), "Metal")
        P.obj("Barrel", pipe([hand + Vector((0, 0.14, 0.06)), hand + Vector((0, 0.42, 0.06))], [0.022, 0.02], 6), "Metal")
        P.obj("MuzzleFlash", cone(tuple(hand + Vector((0, 0.44, 0.06))), tuple(hand + Vector((0, 0.56, 0.06))), 0.035, 5), "Lamp", 0, False)
    # the duster streaming out behind him
    def cpt(u, v):
        x = (u - 0.5) * (0.62 + 0.5 * v)
        return (x, -0.25 - 0.95 * v, 1.0 - 0.75 * v + 0.12 * math.sin(u * 9 + v * 3))
    polys = [[cpt(i / 8, j / 5), cpt((i + 1) / 8, j / 5), cpt((i + 1) / 8, (j + 1) / 5), cpt(i / 8, (j + 1) / 5)] for i in range(8) for j in range(5)]
    cloth = sheet(polys, 0.03)
    big = Matrix.Translation((0, -0.08, 0.42)) @ Matrix.Scale(1.25, 4) @ Matrix.Translation((0, 0.08, -0.42))
    for ob in P.parts[n0:]: ob.data.transform(big)
    for v in cloth.verts: v.co = big @ v.co
    P.part("Cloth", cloth, lambda c, n: "Dark" if c.z < -0.3 else "Glass", (0, 0, 0), 0, False)
    # spirit flames and skull lanterns whirling round them
    for k in range(10):
        a = 2 * math.pi * k / 10
        c = Vector((math.sin(a) * 2.0, -0.1 + math.cos(a) * 2.0, 0.4 + 0.35 * math.sin(a * 2)))
        if k % 2:
            P.part("SpinSpirits", ball(tuple(c), (0.11, 0.11, 0.12), 8, 4), "Belly", (0, -0.1, 0.4))
            for s in (1, -1): P.part("SpinSpirits", ball(tuple(c + Vector((s * 0.04, math.cos(a) * 0.09, 0.02))), (0.03, 0.03, 0.03), 6, 3), "Glow", (0, -0.1, 0.4))
        else:
            P.part("SpinSpirits", pipe(bez(c, c + Vector((0, 0, 0.12)), c + Vector((0.05, -0.05, 0.25)), c + Vector((0, -0.08, 0.35)), 4), [0.09, 0.07, 0.05, 0.025, 0.0], 6), "Glow", (0, -0.1, 0.4), 0)
    mz = big @ Vector((0.3 + 0.12 - 0.04, -0.05 + 0.25 + 0.3 + 0.05 + 0.5, 1.0 - 0.1 + 0.05 + 0.06))
    P.part("Muzzle", ball(tuple(mz), (0.07, 0.05, 0.07), 8, 4), "Lamp", tuple(mz))
    return P


# ================================================================= 2026-10-14: the five remade like the alien / autumn ones
# Real anatomy and proportions, details that each have a reason and sit evenly, scarier faces, the cartoon idea kept - and each flies its own
# way: the thunderbird on its own beating wings (it is the one bird), the sheriff robot on steam, the rattlesnake rides a dynamite rocket
# (coiled round it, fire and smoke behind), the scorpion king rides a giant tumbleweed, the ghost rider gallops across a storm cloud.
from autumn_bosses import fx_tuft, st_loft, st_cloth, st_sheet, sq_axes
from alien_bosses import lerp_keys, spine_frames, oriented_ball

V_ = Vector

def flat_pipe(pts, radii, flat_n, k=0.82, seg=8):
    """a tube through pts flattened k of the way along flat_n: a feather, a strap, a blade."""
    bm = pipe(pts, radii, seg)
    fn = Vector(flat_n).normalized(); c = Vector(pts[0])
    for v in bm.verts:
        d = v.co - c; v.co = c + d - fn * d.dot(fn) * k
    return bm

def feather(base, d, L, w, nrm, curl=0.0, tip=0.35):
    """a contour feather: a flat blade from base along d, widest a third of the way, a rounded point; curl bends it along nrm."""
    base, d, nrm = V_(base), V_(d).normalized(), V_(nrm).normalized()
    pts = bez(base, base + d * L * 0.35, base + d * L * 0.7 + nrm * curl * 0.5, base + d * L + nrm * curl, 6)
    rr = [w * 0.35, w * 0.85, w, w * 0.95, w * 0.8, w * tip + w * 0.15, 0.0]
    return flat_pipe(pts, rr, nrm, 0.86, 8)

def zigzag(a, b, n, amp, side):
    """a lightning bolt from a to b: n even zigs across 'side', the last one to the point."""
    a, b, side = V_(a), V_(b), V_(side).normalized()
    pts = []
    for i in range(n + 1):
        t = i / n; off = (amp if i % 2 else -amp) * (1 - t * 0.6) if 0 < i < n else 0.0
        pts.append(a + (b - a) * t + side * off)
    return pts


def W2_thunderbird():
    """The THUNDERBIRD (2026-10-14, remade like the alien / autumn bosses): the storm eagle of the plains, built like a real eagle. A deep
    keel of a chest and a short body, storm-indigo plumage with a bald eagle's white head and neck, the white shading into the dark through
    a ruff of hackles. The head is an eagle's: a heavy hooked golden beak with a yellow cere and a slit nostril, opened in a scream (his
    lightning leaves from the throat), a thick brow shelf over each eye slanting down to the beak - the scowl every eagle wears - and glowing
    storm-blue eyes with black pupils; two long plumes curl up and back off the crown like horns, red at the tips. The wings are real wings:
    an arm of layered coverts (a red bar across the greater coverts, a turquoise edge on each), twelve secondaries along the trailing edge
    and nine fingered primaries splayed at the tip, each tipped turquoise. The tail fans twelve banded feathers. The legs are thrown forward
    to strike, feathered trousers to the ankle, yellow scaled feet and black talons, and each foot grips a bolt of lightning.
    He is the one boss of the west that flies on wings, as an eagle does: both wings beat (FlapL / FlapR), the tail rocks (SwayTail)."""
    P = Boss("thunderbird", AB_pal(Base=((0.09, 0.11, 0.21), 0.45), Belly=((0.95, 0.93, 0.88), 0.35), Accent=((0.72, 0.10, 0.07), 0.5),
                                   Trim=((1.0, 0.74, 0.12), 0.7), Glass=((0.08, 0.66, 0.66), 0.6), Dark=((0.03, 0.03, 0.05), 0.4),
                                   Glow=((0.22, 0.62, 1.0), 0.5), Metal=((0.05, 0.05, 0.07), 0.8), Lamp=((0.85, 0.95, 1.0), 0.8)))
    glow_strength(P, 2.0)
    # ---- the body: neck to a deep keel, a short body, the rump
    PTS = bez((0, 0.86, 0.5), (0, 0.66, 0.36), (0, 0.42, 0.24), (0, 0.18, 0.18), 6) + bez((0, 0.18, 0.18), (0, -0.15, 0.13), (0, -0.45, 0.16), (0, -0.7, 0.24), 8)[1:]
    n = len(PTS); FR = spine_frames(PTS)
    RX = [lerp_keys(i / (n - 1), [(0, 0.15), (0.2, 0.22), (0.4, 0.33), (0.6, 0.32), (0.85, 0.2), (1, 0.08)]) for i in range(n)]
    RU = [lerp_keys(i / (n - 1), [(0, 0.15), (0.2, 0.2), (0.4, 0.22), (0.6, 0.2), (0.85, 0.14), (1, 0.06)]) for i in range(n)]
    RD = [lerp_keys(i / (n - 1), [(0, 0.16), (0.2, 0.26), (0.4, 0.38), (0.6, 0.3), (0.85, 0.15), (1, 0.06)]) for i in range(n)]
    def plumage(c, nn):
        return "Belly" if c.y > 0.62 else "Base"
    P.obj("Body", st_loft(PTS, RX, RU, RD, FR, 24, 1.1), plumage, 0)
    # the breast feathers: overlapping scallops in even staggered rows down the keel, the white ruff at the top
    for i in range(1, n - 3):
        p = PTS[i]; t, side, up = FR[i]
        for j in range(-3, 4):
            if (i + j) % 2: continue
            a = j * 0.33
            q = p - up * RD[i] * math.cos(a) * 0.92 + side * RX[i] * math.sin(a) * 0.95
            nrm = (-up * math.cos(a) + side * math.sin(a)).normalized()
            d = (t * 0.9 - up * 0.25 + nrm * 0.1).normalized()
            P.obj("Breast", feather(q, d, 0.17, 0.06, nrm, 0.02), "Belly" if p.y > 0.62 else "Base", 0, False)
    # the hackle ruff: white tufts round the neck combed back over the dark
    for k in range(14):
        a = 2 * math.pi * k / 14; i = 3; p = PTS[i]; t, side, up = FR[i]
        o = side * math.cos(a) * RX[i] + up * math.sin(a) * (RU[i] if math.sin(a) > 0 else RD[i])
        q = p + o * 0.95
        P.obj("Ruff", fx_tuft(q, t * 1.0 + o.normalized() * 0.35, 0.22, 0.055, o.normalized(), 0.02), "Belly", 0, False)

    # ---- the head (built pointing +Y about the back of the skull, tipped down a little)
    HB = V_((0, 0.78, 0.5)); HR = Matrix.Rotation(math.radians(-10), 3, "X") @ Matrix.Scale(1.45, 3); HI = HR.inverted()
    def H(bm): return xf(bm, HR, tuple(HB))
    def hp(fn): return lambda c, nn: fn(HI @ (c - HB), (HI @ nn).normalized())
    def hpt(p): return HB + HR @ V_(p)
    SK = [(-0.1, 0.1, 0.1, 0, 0.0), (0.0, 0.15, 0.15, 0, 0.02), (0.1, 0.165, 0.16, 0, 0.03), (0.2, 0.15, 0.14, 0, 0.02),
          (0.28, 0.12, 0.11, 0, 0.0), (0.34, 0.09, 0.085, 0, -0.01)]
    P.obj("Skull", H(loft(SK, 22, sq=1.1)), "Belly", 0)
    P.obj("Cere", H(loft([(0.3, 0.1, 0.09, 0, 0.0), (0.37, 0.085, 0.08, 0, 0.01), (0.4, 0.07, 0.065, 0, 0.0)], 14)), "Trim")
    # the upper mandible: deep at the base, hooked down at the tip, narrower than it is tall
    beak = bez((0, 0.35, 0.02), (0, 0.47, 0.07), (0, 0.58, 0.02), (0, 0.57, -0.13), 10)
    br = [lerp_keys(k / 10, [(0, 0.095), (0.35, 0.085), (0.65, 0.06), (0.85, 0.035), (1, 0.0)]) for k in range(11)]
    ub = pipe(beak, br, 12)
    for v in ub.verts: v.co.x *= 0.72
    P.obj("Beak", H(ub), hp(lambda c, nn: "Dark" if c.z < -0.07 and c.y > 0.52 else "Trim"))
    # the lower mandible, hinged under the cere and dropped open in the scream
    J0 = V_((0, 0.3, -0.04)); JR = Matrix.Rotation(math.radians(-22), 3, "X")
    def Jw(bm): return H(xf(bm, JR, tuple(J0 - JR @ J0)))
    lb = pipe(bez((0, 0.33, -0.05), (0, 0.4, -0.07), (0, 0.47, -0.07), (0, 0.52, -0.06), 6), [0.06, 0.055, 0.045, 0.035, 0.025, 0.012, 0.0], 10)
    for v in lb.verts: v.co.x *= 0.75
    P.obj("Jaw", Jw(lb), "Trim")
    P.obj("Mouth", H(ball((0, 0.41, -0.06), (0.05, 0.11, 0.04), 10, 5)), "Dark")
    P.obj("Throat", H(ball((0, 0.33, -0.06), (0.04, 0.05, 0.03), 8, 4)), "Glow")
    P.obj("Tongue", Jw(pipe([(0, 0.35, -0.045), (0, 0.42, -0.05), (0, 0.47, -0.04)], [0.025, 0.02, 0.008], 6)), "Accent")
    for s in (1, -1):
        P.obj("Nostril", H(oriented_ball((s * 0.05, 0.41, 0.06), (0.008, 0.025, 0.01), V_((1, 0, 0)), V_((0, 1, 0)), V_((0, 0, 1)), 6, 3)), "Dark")
        P.obj("Gape", H(pipe([(s * 0.065, 0.32, -0.03), (s * 0.06, 0.42, -0.03), (s * 0.045, 0.5, -0.05)], [0.01, 0.009, 0.0], 5)), "Dark")
        # the eye: big, set forward, storm-blue with a black pupil, under the brow shelf
        ec = V_((s * 0.1, 0.255, 0.06)); dv = V_((s * 0.4, 0.91, 0.04)).normalized()
        ex = dv.cross(V_((0, 0, 1))).normalized(); ez = ex.cross(dv).normalized()
        if ez.z < 0: ez = -ez
        P.obj("EyeRim", H(oriented_ball(ec - dv * 0.004, (0.056, 0.03, 0.05), ex, dv, ez, 12, 6)), "Dark")
        P.obj("Eye", H(oriented_ball(ec + dv * 0.006, (0.048, 0.03, 0.043), ex, dv, ez, 12, 6)), "Glow")
        P.obj("Pupil", H(oriented_ball(ec + dv * 0.03 - ez * 0.004, (0.024, 0.012, 0.024), ex, dv, ez, 8, 4)), "Dark")
        P.obj("Glint", H(ball(tuple(ec + dv * 0.036 + ez * 0.008 - ex * s * 0.014), (0.006,) * 3, 6, 3)), "Lamp")
        # the brow shelf: a heavy ridge over the eye, low at the beak, high at the back - the scowl
        P.obj("Brow", H(pipe(bez((s * 0.04, 0.34, 0.05), (s * 0.085, 0.305, 0.1), (s * 0.14, 0.24, 0.11), (s * 0.17, 0.14, 0.11), 6),
                             [0.024, 0.036, 0.042, 0.042, 0.036, 0.026, 0.012], 8)), "Belly")
        # the crest: a harpy eagle's split crest, five long feathers a side fanned back and up off the crown, red at the tips
        for k in range(5):
            b0 = V_((s * (0.03 + 0.025 * k), 0.06 - 0.05 * k, 0.15 - 0.01 * k))
            d = V_((s * (0.25 + 0.12 * k), -1.0, 0.75 - 0.12 * k))
            L = 0.42 - 0.045 * k
            P.obj("Crest", H(feather(b0, d, L, 0.05, V_((s * 0.3, 0.35, 1.0)), 0.06, 0.3)),
                  hp(lambda c, nn, b0=b0, L=L: "Accent" if (c - b0).length > L * 0.72 else "Belly"), 0, False)
        # the cheek feathers combed back from behind the eye
        for k in range(3):
            q = V_((s * 0.15, 0.08 - 0.03 * k, 0.0 - 0.05 * k))
            P.obj("Cheek", H(fx_tuft(q, (s * 0.4, -1, -0.1), 0.16, 0.04, (s, 0, 0.3), 0.0)), "Belly", 0, False)

    # ---- the wings: an arm of layered coverts, twelve secondaries, nine fingered primaries; each wing one Flap part about the shoulder
    for s in (1, -1):
        name = "FlapR" if s > 0 else "FlapL"; hub = (s * 0.22, 0.3, 0.32)
        dih = math.radians(14)   # held up in a shallow V
        def W(p, s=s):
            p = V_(p); return V_((s * (p.x * math.cos(dih)), p.y, 0.32 + p.x * math.sin(dih) + p.z))
        # the arm: an airfoil from the shoulder to the wrist
        secs = []
        for k in range(9):
            x = 0.18 + 1.3 * k / 8
            le = lerp_keys(k / 8, [(0, 0.52), (0.5, 0.5), (1, 0.42)]); te = lerp_keys(k / 8, [(0, -0.05), (0.5, -0.02), (1, 0.08)])
            th = lerp_keys(k / 8, [(0, 0.16), (1, 0.07)])
            secs.append((x, airfoil(le, te, th, 0.0)))
        arm = sweep(secs, "x")
        for v in arm.verts: v.co = W(v.co)
        if s < 0: bmesh.ops.reverse_faces(arm, faces=arm.faces)
        P.part(name, arm, lambda c, nn: "Base", hub, 0)
        # the wrist (alula) and lesser coverts: a scalloped band along the leading edge
        for k in range(10):
            x = 0.25 + 1.2 * k / 9; q = W((x, lerp_keys(k / 9, [(0, 0.44), (1, 0.33)]), 0.05))
            P.part(name, feather(q, W((x - 0.0, -1.0, 0.0)) - W((x, 0, 0)), 0.26, 0.09, V_((0, 0, 1)), -0.01), "Base", hub, 0, False)
        # the greater coverts: a row over the base of the secondaries, a red bar with turquoise edges
        for k in range(12):
            x = 0.22 + 1.22 * k / 11; q = W((x, lerp_keys(k / 11, [(0, 0.2), (1, 0.16)]), 0.045))
            col = "Glass" if k % 3 == 0 else "Accent"
            P.part(name, feather(q, (0, -1, -0.05), 0.3, 0.1, V_((0, 0, 1)), -0.01), col, hub, 0, False)
        # twelve secondaries along the trailing edge, overlapping, pointing back
        for k in range(12):
            x = 0.2 + 1.24 * k / 11; q = W((x, lerp_keys(k / 11, [(0, -0.02), (1, 0.06)]), 0.0))
            P.part(name, feather(q, (s * 0.08 * (k / 11), -1, -0.02), 0.68 - 0.08 * (k / 11), 0.12, V_((0, 0, 1)), -0.02, 0.5),
                   lambda c, nn, q=q: "Glass" if (c - q).length > 0.6 else "Base", hub, 0, False)
        # nine primaries splayed from the hand like fingers, the outer ones longest, tipped turquoise
        wrist = W((1.45, 0.2, 0.0))
        for k in range(9):
            a = math.radians(lerp_keys(k / 8, [(0, 28), (1, -62)]))   # from forward-out round to back-out
            d = W((math.cos(a) * 1.0 + 1.45, math.sin(a), 0.0)) - W((1.45, 0, 0))
            L = lerp_keys(k / 8, [(0, 1.0), (0.35, 1.28), (0.7, 1.2), (1, 0.9)])
            b = wrist + d.normalized() * 0.05
            P.part(name, feather(b, d, L, 0.11, V_((0, 0, 1)), 0.08, 0.25),
                   lambda c, nn, b=b, L=L: "Glass" if (c - b).length > L * 0.86 else ("Dark" if (c - b).length > L * 0.4 else "Base"), hub, 0, False)
        # a zig of lightning along the wing's leading edge, glowing
        zz = [W(p) for p in ((0.3, 0.42, 0.075), (0.55, 0.3, 0.08), (0.62, 0.4, 0.08), (0.9, 0.27, 0.075), (0.97, 0.37, 0.07), (1.3, 0.24, 0.06))]
        P.part(name, pipe(zz, [0.016, 0.024, 0.024, 0.022, 0.02, 0.0], 5), "Glow", hub, 0, False)

    # ---- the tail: twelve banded feathers fanned behind, rocking together about the rump
    th = (0, -0.7, 0.24)
    for k in range(12):
        a = math.radians(-50 + 100 * k / 11)
        d = V_((math.sin(a), -math.cos(a), -0.06))
        b = V_(th) + d * 0.05
        L = 0.78 - 0.1 * abs(k - 5.5) / 5.5
        P.part("SwayTail", feather(b, d, L, 0.09, V_((0, 0, 1)), -0.03, 0.55),
               lambda c, nn, b=b, L=L: "Belly" if 0.55 * L < (c - b).length < 0.72 * L or (c - b).length > 0.92 * L else "Base", th, 0, False)

    # ---- the legs thrown forward to strike: feathered trousers, yellow scaled feet, black talons, a bolt of lightning in each
    for s in (1, -1):
        hip = V_((s * 0.15, 0.05, 0.05)); knee = V_((s * 0.17, 0.28, -0.25)); ank = V_((s * 0.17, 0.5, -0.36))
        P.obj("Trouser", oriented_ball((hip + knee) * 0.5, (0.13, 0.22, 0.13), V_((1, 0, 0)), (knee - hip).normalized(), V_((0, -0.6, 0.8)).normalized(), 12, 6), "Base")
        for k in range(5):   # the trouser feathers falling over the ankle
            a = -0.9 + 0.45 * k
            q = knee + V_((math.sin(a) * 0.09, 0, math.cos(a) * 0.04))
            P.obj("Trouser", feather(q, (knee - hip).normalized() + V_((math.sin(a) * 0.3, 0, -0.2)), 0.16, 0.05, V_((math.sin(a), 0.3, math.cos(a))), 0.0), "Base", 0, False)
        P.obj("Tarsus", pipe([knee, ank], [0.045, 0.04], 10), "Trim")
        for k in range(5):   # scutes across the front of the tarsus
            q = knee + (ank - knee) * (0.15 + 0.17 * k)
            P.obj("Scute", oriented_ball(q + V_((0, 0.02, 0.025)), (0.045, 0.012, 0.02), V_((1, 0, 0)), V_((0, 1, 0)), V_((0, 0, 1)), 8, 3), "Trim")
        # three toes forward and the hallux behind, curled round the bolt; black talons
        bolt_at = ank + V_((0, 0.12, -0.08))
        for k, (dx, dy) in enumerate(((-0.6, 1), (0, 1), (0.6, 1), (0, -1))):
            d = V_((s * dx * 0.5, dy, -0.3)).normalized()
            t0 = ank + d * 0.02; t1 = ank + d * 0.13; t2 = t1 + (d + V_((0, 0, -0.9))).normalized() * 0.07
            P.obj("Toe", pipe([t0, t1, t2], [0.028, 0.024, 0.02], 7), "Trim")
            P.obj("Talon", pipe(bez(t2, t2 + V_((0, 0, -0.04)), t2 + V_((0, -0.03 * dy, -0.08)), t2 + V_((0, -0.07 * dy, -0.09)), 4), [0.02, 0.016, 0.01, 0.005, 0.0], 6), "Metal")
        bolt = zigzag(bolt_at + V_((s * 0.25, 0.25, 0.05)), bolt_at + V_((-s * 0.2, -0.3, -0.75)), 5, 0.12, (1, 0, 0))
        P.obj("Bolt", pipe(bolt, [0.035, 0.045, 0.045, 0.04, 0.035, 0.0], 6), "Glow", 0, False)

    mz = hpt((0, 0.45, -0.07))
    P.part("Muzzle", ball(tuple(mz), (0.05, 0.03, 0.04), 8, 4), "Lamp", tuple(mz))
    return P


def stetson(P, c, k=1.0, tilt=0.0, crown_slot="Glass", band_slot="Dark", concho_slot="Metal", name="Hat", roll=0.24):
    """a cattleman's hat: a tall crown with the crease down the middle and the two pinches at the front, a wide brim rolled up at the sides
    and dipping at the front and back, a band with five silver conchos at even steps."""
    c = V_(c); M = Matrix.Rotation(tilt, 3, "X")
    def put(bm): return xf(grow(bm, (0, 0, 0), k), M, tuple(c))
    crown = lathe([(0.0, 0.0), (0.27, 0.0), (0.268, 0.12), (0.25, 0.24), (0.22, 0.3), (0.16, 0.33), (0.0, 0.32)], 32, "z")
    for v in crown.verts:
        v.co.y *= 1.18
        x, y, z = v.co
        if z > 0.15:
            v.co.z -= 0.075 * math.exp(-(x / 0.07) ** 2) * min(1.0, (z - 0.15) / 0.15)          # the crease along the top
            if y > 0.05: v.co.x *= 1 - 0.22 * min(1.0, (z - 0.15) / 0.15) * min(1.0, y / 0.25)   # the pinches at the front
    P.obj(name, put(crown), crown_slot, 0)
    brim = lathe([(0.0, -0.012), (0.52, -0.004), (0.6, 0.02), (0.6, 0.04), (0.52, 0.012), (0.0, 0.012)], 40, "z")
    for v in brim.verts:
        v.co.y *= 1.14
        r = math.hypot(v.co.x / 0.6, v.co.y / 0.68)
        if r > 0.45:
            ax = abs(v.co.x) / 0.6
            v.co.z += ((r - 0.45) / 0.55) ** 2 * (roll * ax ** 2 - 0.05 * (1 - ax))   # rolled up at the sides, a dip front and back
    P.obj(name, put(brim), crown_slot, 0)
    band = lathe([(0.272, 0.015), (0.27, 0.075), (0.0, 0.075)], 32, "z")
    for v in band.verts: v.co.y *= 1.18
    P.obj(name + "Band", put(band), band_slot, 0)
    for j in range(5):
        a = math.radians(-60 + 30 * j)
        q = V_((math.sin(a) * 0.275, math.cos(a) * 0.275 * 1.18, 0.045))
        nrm = V_((math.sin(a), math.cos(a) * 1.18, 0)).normalized()
        P.obj(name + "Concho", put(oriented_ball(q, (0.03, 0.012, 0.03), V_((math.cos(a), -math.sin(a), 0)), nrm, V_((0, 0, 1)), 10, 4)), concho_slot)

def rivet_ring(P, c, R, z, n, r=0.018, ry=1.0, slot="Dark", name="Rivet"):
    for j in range(n):
        a = 2 * math.pi * j / n
        P.obj(name, ball((c[0] + math.cos(a) * R, c[1] + math.sin(a) * R * ry, z), (r, r, r), 6, 3), slot)

def revolver(P, grip, d, up, slot_name="Gun"):
    """a single-action army revolver held at grip, the barrel along d: the frame, a six-shot cylinder with its flutes, the cocked hammer,
    the barrel with the ejector rod under it and the front sight, the trigger in its guard, ivory grips. Returns the muzzle point."""
    g = V_(grip); d = V_(d).normalized(); up = V_(up).normalized(); sd = d.cross(up).normalized()
    def at(a, b, c_): return g + d * a + up * b + sd * c_
    P.obj(slot_name, oriented_ball(at(-0.02, -0.08, 0), (0.035, 0.05, 0.1), sd, d, (up - d * 0.35).normalized(), 10, 5), "Belly")          # the ivory grip
    P.obj(slot_name, hull([tuple(at(a, b, c_)) for a in (-0.06, 0.12) for b in (0.0, 0.09) for c_ in (-0.03, 0.03)]), "Metal", 0, False)  # the frame
    cy = at(0.13, 0.055, 0)
    P.obj(slot_name, pipe([cy - d * 0.07, cy + d * 0.07], [0.055, 0.055], 12), "Metal")                                                     # the cylinder
    for j in range(6):
        a = 2 * math.pi * j / 6
        o = up * math.cos(a) + sd * math.sin(a)
        P.obj(slot_name, pipe([cy - d * 0.05 + o * 0.056, cy + d * 0.05 + o * 0.056], [0.012, 0.012], 5), "Dark")                          # the flutes
    P.obj(slot_name, pipe([at(0.2, 0.06, 0), at(0.62, 0.06, 0)], [0.026, 0.024], 10), "Metal")                                             # the barrel
    P.obj(slot_name, pipe([at(0.2, 0.025, 0), at(0.5, 0.025, 0)], [0.014, 0.014], 6), "Metal")                                             # the ejector rod housing
    P.obj(slot_name, cone(at(0.6, 0.082, 0), at(0.61, 0.11, 0), 0.01, 4), "Metal")                                                         # the front sight
    P.obj(slot_name, pipe(bez(at(-0.04, 0.08, 0), at(-0.1, 0.11, 0), at(-0.1, 0.15, 0), at(-0.07, 0.16, 0), 4), [0.016] * 5, 5), "Metal")  # the cocked hammer
    P.obj(slot_name, pipe([at(0.06 + 0.05 * math.cos(math.pi * t / 8), -0.03 - 0.045 * math.sin(math.pi * t / 8), 0) for t in range(9)], [0.008] * 9, 5), "Trim")   # the guard
    return at(0.63, 0.06, 0)


def W2_sheriff():
    """The SHERIFF ROBOT (2026-10-14, remade like the alien / autumn bosses): a steam automaton built like a real locomotive boiler. His
    body is the boiler: a riveted brass barrel with iron bands, a rivet every hand's width round each; in his belly the round iron firebox
    door with its latch and hinges, the fire glowing through its draught slots; on his chest a pressure gauge with its needle in the red
    and the silver star of the law. A red bandana at the throat over a leather bellows of a neck. His head is an iron stovepipe with a brass
    face plate: a riveted brow plate slanting down to the nose - a scowl - over two deep furnace eyes, a nose ridge, an iron handlebar
    moustache curled at the ends and a jaw grille of six slats; on it a cattleman's hat with the crease and the front pinches, the brim
    rolled up at the sides, a band of five silver conchos. Each arm is a steam arm - iron shoulder, brass upper arm, a polished piston rod
    that drives the elbow, an iron forearm - and each hand aims a single-action revolver at you (ivory grips, fluted cylinder, hammer
    cocked). A leather gun belt with brass cartridges in its loops at even steps, two empty holsters.
    He flies on steam: his legs end in flared iron thruster bells ringed with cooling fins, each blowing a column of steam that whirls
    under him (SpinSteamR / SpinSteamL), fed by copper pipes from the boiler on his back; two balloon smokestacks stand over his shoulders
    and between them a flyball governor - the real regulator of a steam engine - spins (SpinGovernor), its brass balls flung out."""
    P = Boss("sheriff", AB_pal(Base=((0.80, 0.56, 0.22), 0.75), Belly=((0.93, 0.91, 0.86), 0.3), Accent=((0.74, 0.08, 0.06), 0.45),
                               Trim=((1.0, 0.8, 0.3), 0.85), Glass=((0.30, 0.16, 0.07), 0.35), Dark=((0.05, 0.045, 0.04), 0.5),
                               Glow=((1.0, 0.42, 0.06), 0.5), Metal=((0.22, 0.22, 0.24), 0.7), Lamp=((1.0, 0.8, 0.45), 0.8)))
    glow_strength(P, 3.0)
    # ---- the boiler body
    prof = [(0.0, 0.0), (0.4, 0.0), (0.5, 0.08), (0.56, 0.35), (0.57, 0.7), (0.53, 1.02), (0.42, 1.18), (0.2, 1.24), (0.0, 1.25)]
    body = lathe(prof, 36, "z")
    for v in body.verts: v.co.y *= 0.86
    P.obj("Boiler", body, "Base", 0)
    for z, R in ((0.1, 0.505), (0.52, 0.572), (0.92, 0.548)):
        band = torus(R, 0.028, z, 40, 6)
        for v in band.verts: v.co.y *= 0.86
        P.obj("BoilerBand", band, "Metal")
        for j in range(20):
            a = 2 * math.pi * j / 20
            P.obj("Rivet", ball((math.cos(a) * (R + 0.022), math.sin(a) * (R + 0.022) * 0.86, z + 0.035), (0.016,) * 3, 6, 3), "Metal")
            P.obj("Rivet", ball((math.cos(a) * (R + 0.022), math.sin(a) * (R + 0.022) * 0.86, z - 0.035), (0.016,) * 3, 6, 3), "Metal")
    # the firebox door in his belly: iron, hinged on the left, a latch on the right, the fire through five draught slots
    fd = V_((0, 0.49, 0.32))
    P.obj("Firebox", lathe([(0.0, 0.0), (0.2, 0.0), (0.21, 0.025), (0.19, 0.045), (0.0, 0.05)], 28, "y", tuple(fd)), "Metal")
    rr = 0.205
    for j in range(12):
        a = 2 * math.pi * j / 12
        P.obj("Rivet", ball(tuple(fd + V_((math.cos(a) * 0.18, 0.05, math.sin(a) * 0.18))), (0.013,) * 3, 6, 3), "Base")
    for j in range(5):
        z = -0.1 + 0.05 * j; w = math.sqrt(max(0.0, 0.14 ** 2 - z * z)) * 0.85
        P.obj("Draught", box(tuple(fd + V_((0, 0.05, z))), (w * 2, 0.02, 0.022)), "Glow", 0, False)
    for z in (0.1, -0.1):
        P.obj("Hinge", pipe([fd + V_((-0.26, 0.04, z)), fd + V_((-0.1, 0.06, z))], [0.022, 0.018], 6), "Dark")
    P.obj("Latch", pipe([fd + V_((0.12, 0.07, 0)), fd + V_((0.27, 0.08, 0.02))], [0.02, 0.018], 6), "Trim")
    P.obj("LatchKnob", ball(tuple(fd + V_((0.28, 0.08, 0.02))), (0.03,) * 3, 8, 4), "Trim")
    # the pressure gauge on his right chest, the needle in the red
    gc = V_((0.27, 0.43, 0.78)); gn = V_((0.38, 0.92, 0.0)).normalized(); gx, gy, gz = sq_axes(gn)
    P.obj("Gauge", xf(lathe([(0.0, 0.0), (0.12, 0.0), (0.125, 0.03), (0.105, 0.04), (0.0, 0.035)], 24, "z"), Matrix((gx, gy, gz)).transposed(), tuple(gc)), "Trim")
    P.obj("GaugeFace", oriented_ball(gc + gn * 0.035, (0.1, 0.1, 0.008), gx, gy, gz, 20, 4), "Belly")
    for j in range(9):
        a = math.radians(-135 + 33.75 * j)
        q = gc + gn * 0.045 + (gx * math.sin(a) + gy * math.cos(a)) * 0.08
        P.obj("GaugeTick", oriented_ball(q, (0.006, 0.016, 0.004), gx * math.cos(a) - gy * math.sin(a), gx * math.sin(a) + gy * math.cos(a), gz, 4, 2),
              "Accent" if j >= 7 else "Dark")
    a = math.radians(110)
    P.obj("GaugeNeedle", pipe([gc + gn * 0.05, gc + gn * 0.05 + (gx * math.sin(a) + gy * math.cos(a)) * 0.085], [0.008, 0.0], 4), "Accent")
    P.obj("GaugeHub", ball(tuple(gc + gn * 0.05), (0.014,) * 3, 6, 3), "Dark")
    # the star of the law on his left chest: six points, a ball on each, the word cut round the rim
    bc = V_((-0.27, 0.44, 0.8)); bn = V_((-0.38, 0.92, 0.0)).normalized(); bx, by, bz = sq_axes(bn)
    pts6 = [bc + (bx * math.sin(2 * math.pi * j / 12) + by * math.cos(2 * math.pi * j / 12)) * (0.16 if j % 2 == 0 else 0.08) for j in range(12)]
    for j in range(12):   # the star as twelve wedges round the centre (a hull would fill the notches)
        a, b = pts6[j], pts6[(j + 1) % 12]
        P.obj("Badge", hull([tuple(bc), tuple(a), tuple(b), tuple(bc + bn * 0.045), tuple(a + bn * 0.02), tuple(b + bn * 0.02)]), "Trim", 0, False)
    for j in range(6):
        q = bc + (bx * math.sin(2 * math.pi * j / 6) + by * math.cos(2 * math.pi * j / 6)) * 0.165 + bn * 0.02
        P.obj("BadgeBall", ball(tuple(q), (0.022,) * 3, 8, 4), "Trim")
    P.obj("BadgeRing", xf(torus(0.07, 0.008, 0.0, 20, 4), Matrix((bx, by, bz)).transposed(), tuple(bc + bn * 0.04)), "Dark")
    # ---- the gun belt: leather, brass cartridges in the loops at even steps, a buckle, two holsters
    belt = torus(0.53, 0.05, 0.0, 44, 6)
    for v in belt.verts: v.co.y *= 0.86; v.co.z *= 1.4
    P.obj("Belt", belt, "Glass")
    for j in range(22):
        a = math.radians(-160 + 320 * j / 21)
        if abs(math.degrees(a)) < 18: continue
        x, y = math.sin(a) * 0.58, math.cos(a) * 0.58 * 0.86
        P.obj("Cartridge", pipe([(x, y, -0.04), (x, y, 0.05)], [0.018, 0.018], 6), "Trim")
        P.obj("Cartridge", cone((x, y, 0.05), (x, y, 0.085), 0.017, 6), "Base")
    P.obj("Buckle", box((0, 0.5, 0.0), (0.2, 0.04, 0.15)), "Trim", 0, False)
    P.obj("BuckleBar", box((0, 0.525, 0.0), (0.12, 0.02, 0.08)), "Dark", 0, False)
    for s in (1, -1):
        P.obj("Holster", oriented_ball(V_((s * 0.55, 0.12, -0.16)), (0.07, 0.11, 0.2), V_((1, 0, 0)), V_((0, 1, 0)), V_((0, 0, 1)), 10, 5), "Glass")

    # ---- the neck, the bandana, the head
    for j in range(4):
        P.obj("Bellows", torus(0.15 - 0.008 * j, 0.03, 1.25 + 0.05 * j, 20, 6), "Dark")
    P.obj("Bandana", st_cloth([[(-0.2, 0.36, 1.2), (0.2, 0.36, 1.2), (0.0, 0.48, 0.92)]], 0.02), "Accent")
    P.obj("Bandana", torus(0.2, 0.045, 1.24, 24, 6), "Accent")
    HC = V_((0, 0.0, 1.62))
    P.obj("Head", lathe([(0.0, -0.22), (0.24, -0.22), (0.25, 0.0), (0.24, 0.16), (0.2, 0.22), (0.0, 0.24)], 28, "z", tuple(HC)), "Metal")
    face = hull([tuple(HC + V_((x, 0.2 + 0.06 * (1 - abs(x) / 0.22), z))) for x in (-0.22, 0.0, 0.22) for z in (-0.2, 0.12)] +
                [tuple(HC + V_((x, 0.1, z))) for x in (-0.24, 0.24) for z in (-0.2, 0.12)])
    P.obj("FacePlate", face, "Base", 0, False)
    for j in range(7):
        x = -0.18 + 0.06 * j
        P.obj("Rivet", ball(tuple(HC + V_((x, 0.27 - 0.06 * abs(x) / 0.22 + 0.01, -0.17))), (0.013,) * 3, 6, 3), "Metal")
    for s in (1, -1):
        # the furnace eyes, deep in iron sockets
        e = HC + V_((s * 0.1, 0.25, 0.02))
        P.obj("Socket", oriented_ball(e, (0.08, 0.03, 0.062), V_((1, 0, 0)), V_((0, 1, 0)), V_((0, 0, 1)), 12, 5), "Dark")
        P.obj("Eye", oriented_ball(e + V_((0, 0.012, -0.008)), (0.064, 0.026, 0.044), V_((1, 0, 0)), V_((0, 1, 0)), V_((0, 0, 1)), 12, 5), "Glow")
        P.obj("Pupil", oriented_ball(e + V_((0, 0.032, -0.008)), (0.014, 0.01, 0.036), V_((1, 0, 0)), V_((0, 1, 0)), V_((0, 0, 1)), 6, 3), "Dark")
        # the brow plate: a riveted wedge over each eye, low at the nose - the scowl
        bw = [HC + V_((s * 0.02, 0.28, 0.035)), HC + V_((s * 0.1, 0.28, 0.08)), HC + V_((s * 0.2, 0.25, 0.11))]
        P.obj("BrowPlate", pipe(bw, [0.03, 0.035, 0.03], 6), "Metal")
        P.obj("Rivet", ball(tuple(HC + V_((s * 0.12, 0.31, 0.095))), (0.012,) * 3, 6, 3), "Base")
        # the handlebar moustache, curled at the ends
        ms = [HC + V_((0, 0.3, -0.06)), HC + V_((s * 0.09, 0.31, -0.08)), HC + V_((s * 0.19, 0.29, -0.07)), HC + V_((s * 0.26, 0.24, -0.02)),
              HC + V_((s * 0.27, 0.22, 0.04)), HC + V_((s * 0.23, 0.22, 0.06))]
        P.obj("Moustache", pipe(ms, [0.04, 0.045, 0.04, 0.025, 0.016, 0.0], 8), "Dark")
        # ear bolts with a valve wheel
        P.obj("EarValve", lathe([(0.0, 0.0), (0.06, 0.0), (0.06, 0.04), (0.0, 0.05)], 12, "x", (s * 0.24 if s > 0 else -0.29, 0.0, 1.62)), "Trim")
    P.obj("Nose", pipe([HC + V_((0, 0.28, 0.05)), HC + V_((0, 0.31, -0.03))], [0.025, 0.035], 8), "Base")
    for j in range(6):   # the jaw grille: six slats under the moustache
        x = -0.1 + 0.04 * j
        P.obj("Grille", box(tuple(HC + V_((x, 0.27, -0.15))), (0.022, 0.03, 0.08)), "Metal", 0, False)
    P.obj("GrilleGap", box(tuple(HC + V_((0, 0.255, -0.15))), (0.24, 0.02, 0.08)), "Glow", 0, False)
    stetson(P, HC + V_((0, -0.04, 0.21)), 1.22, math.radians(7))

    # ---- the steam arms, a revolver in each hand aimed at you
    muzzle = None
    for s in (1, -1):
        sh = V_((s * 0.62, 0.0, 1.0)); el = V_((s * 0.8, 0.28, 0.66)); wr = V_((s * 0.55, 0.62, 0.72))
        P.obj("Shoulder", ball(tuple(sh), (0.17, 0.17, 0.17), 14, 7), "Metal")
        rivet_ring(P, sh, 0.17, sh.z, 10, 0.013, 1.0, "Base")
        P.obj("UpperArm", pipe([sh, el], [0.1, 0.09], 12), "Base")
        P.obj("Elbow", ball(tuple(el), (0.1,) * 3, 10, 5), "Metal")
        P.obj("Forearm", pipe([el, wr], [0.085, 0.1], 12), "Metal")
        for t in (0.3, 0.7):
            P.obj("ArmBand", pipe([el + (wr - el) * (t - 0.04), el + (wr - el) * (t + 0.04)], [0.1, 0.1], 12), "Base")
        # the piston: a cylinder on the upper arm driving a polished rod to the forearm
        c0 = sh + (el - sh) * 0.25 + V_((s * 0.06, 0.06, 0.06)); c1 = sh + (el - sh) * 0.7 + V_((s * 0.06, 0.08, 0.04))
        P.obj("Piston", pipe([c0, c1], [0.04, 0.04], 10), "Trim")
        P.obj("PistonRod", pipe([c1, el + V_((s * 0.04, 0.06, 0.07))], [0.016, 0.016], 6), "Metal")
        P.obj("Hand", oriented_ball(wr + V_((0, 0.06, 0)), (0.1, 0.11, 0.09), V_((1, 0, 0)), V_((0, 1, 0)), V_((0, 0, 1)), 10, 5), "Metal")
        for j in range(3):
            P.obj("Finger", pipe([wr + V_((s * 0.05, 0.1, 0.04 - 0.04 * j)), wr + V_((s * 0.03, 0.16, 0.03 - 0.04 * j)), wr + V_((-s * 0.02, 0.15, 0.03 - 0.04 * j))], [0.026, 0.024, 0.02], 6), "Metal")
        m = revolver(P, wr + V_((0, 0.13, -0.02)), (0, 1, 0.05), (0, -0.05, 1))
        if s > 0: muzzle = m

    # ---- the steam thrusters: iron legs ending in flared bells ringed with fins, each blowing a whirling column of steam
    for s in (1, -1):
        hip = V_((s * 0.25, 0.0, 0.02)); kn = V_((s * 0.3, 0.06, -0.38)); bell = V_((s * 0.3, 0.02, -0.68))
        P.obj("Thigh", pipe([hip, kn], [0.13, 0.11], 12), "Metal")
        P.obj("Knee", ball(tuple(kn), (0.12,) * 3, 10, 5), "Base")
        P.obj("Shin", pipe([kn, bell], [0.11, 0.13], 12), "Base")
        P.obj("Bell", lathe([(0.12, 0.0), (0.16, -0.08), (0.24, -0.2), (0.28, -0.24), (0.22, -0.2), (0.13, -0.08), (0.11, 0.0)], 24, "z", tuple(bell)), "Metal")
        for j in range(3):
            P.obj("Fin", torus(0.14 + 0.025 * j, 0.012, bell.z - 0.04 - 0.05 * j, 24, 4), "Trim")
            P.parts[-1].data.transform(Matrix.Translation((bell.x, bell.y, 0)))
        rivet_ring(P, bell, 0.125, bell.z + 0.0, 10, 0.012, 1.0, "Trim")
        P.obj("BellFire", ball(tuple(bell + V_((0, 0, -0.22))), (0.2, 0.2, 0.03), 16, 4), "Glow")
        # the steam: puffs on a helix under the bell, bigger as they fall and spread
        hub = (bell.x, bell.y, bell.z - 0.6)
        name = "SpinSteamR" if s > 0 else "SpinSteamL"
        for j in range(14):
            u = j / 13; a = 2 * math.pi * (u * 1.6) * s
            r = 0.04 + 0.16 * u; z = bell.z - 0.26 - 0.75 * u
            q = V_((bell.x + math.cos(a) * r, bell.y + math.sin(a) * r, z))
            P.part(name, ball(tuple(q), (0.09 + 0.1 * u,) * 3, 12, 6), "Belly", hub)
        # the copper feed pipe from the boiler on his back, with its red valve wheel
        fp = [V_((s * 0.2, -0.55, 0.45)), V_((s * 0.45, -0.45, 0.2)), V_((s * 0.42, -0.1, -0.35)), bell + V_((s * 0.08, -0.08, 0.02))]
        P.obj("FeedPipe", pipe(fp, [0.035] * 4, 8), "Trim")
        vw = fp[1]
        P.obj("Valve", xf(torus(0.06, 0.012, 0.0, 16, 4), Matrix.Rotation(math.pi / 2, 3, "Y"), tuple(vw + V_((s * 0.05, 0, 0)))), "Accent")

    # ---- the boiler on his back: a riveted tank, two balloon smokestacks puffing, the flyball governor between them
    P.obj("BackTank", pipe([V_((-0.36, -0.56, 0.65)), V_((0.36, -0.56, 0.65))], [0.26, 0.26], 24), "Base")
    for x in (-0.36, 0.0, 0.36):
        P.obj("TankBand", pipe([V_((x - 0.025, -0.56, 0.65)), V_((x + 0.025, -0.56, 0.65))], [0.275, 0.275], 24), "Metal")
    for s in (1, -1):
        b0 = V_((s * 0.24, -0.6, 0.88))
        P.obj("Stack", lathe([(0.06, 0.0), (0.065, 0.42), (0.12, 0.52), (0.17, 0.66), (0.15, 0.72), (0.07, 0.7), (0.0, 0.7)], 18, "z", tuple(b0)), "Metal")
        P.obj("StackBand", torus(0.075, 0.015, b0.z + 0.42, 16, 4), "Trim"); P.parts[-1].data.transform(Matrix.Translation((b0.x, b0.y, 0)))
    gv = V_((0, -0.66, 0.92))
    P.obj("GovernorBase", lathe([(0.0, 0.0), (0.08, 0.0), (0.07, 0.05), (0.03, 0.08), (0.0, 0.08)], 14, "z", tuple(gv)), "Trim")
    hub = tuple(gv)
    P.part("SpinGovernor", pipe([gv, gv + V_((0, 0, 0.5))], [0.02, 0.02], 8), "Metal", hub)
    P.part("SpinGovernor", ball(tuple(gv + V_((0, 0, 0.52))), (0.035,) * 3, 8, 4), "Trim", hub)
    P.part("SpinGovernor", pipe([gv + V_((0, 0, 0.14)), gv + V_((0, 0, 0.2))], [0.045, 0.045], 10), "Trim", hub)   # the sliding sleeve
    for s in (1, -1):
        top = gv + V_((0, 0, 0.48)); ballc = gv + V_((s * 0.26, 0, 0.26))
        P.part("SpinGovernor", pipe([top, ballc], [0.014, 0.014], 6), "Metal", hub)
        P.part("SpinGovernor", pipe([gv + V_((0, 0, 0.18)), (top + ballc) * 0.5], [0.01, 0.01], 5), "Metal", hub)
        P.part("SpinGovernor", ball(tuple(ballc), (0.07,) * 3, 12, 6), "Trim", hub)
    P.part("Muzzle", ball(tuple(muzzle), (0.03, 0.02, 0.03), 8, 4), "Glow", tuple(muzzle))
    return P


def ribbon_tube(sp, T, N, wx, hu, hd, seg=28, sq=1.2):
    """a body along sp whose sections are wx[i] across, hu[i] above and hd[i] below the spine, turned by the twist-free normals N."""
    bm = bmesh.new(); rings = []
    for i, p in enumerate(sp):
        up = N[i]; side = T[i].cross(up).normalized()
        if wx[i] < 1e-4: rings.append([bm.verts.new(p)]); continue
        ring = []
        for k in range(seg):
            a = 2 * math.pi * k / seg; ca, sa = math.cos(a), math.sin(a)
            u = math.copysign(abs(ca) ** (1 / sq), ca) * wx[i]
            v = math.copysign(abs(sa) ** (1 / sq), sa) * (hu[i] if sa > 0 else hd[i])
            ring.append(bm.verts.new(p + side * u + up * v))
        rings.append(ring)
    from alien_bosses import skin
    return skin(bm, rings, seg)


def hint_frames(sp, hint, passes=4):
    """tangents and normals that follow a wanted 'up' along the path (hint(p, t) -> a direction, squared to the path and smoothed over its
    neighbours), and the arc length: the back of a snake coiled round something faces out of the coil."""
    n = len(sp)
    T = [(sp[min(i + 1, n - 1)] - sp[max(i - 1, 0)]).normalized() for i in range(n)]
    N = []
    for i in range(n):
        d = V_(hint(sp[i], T[i])); v = d - T[i] * d.dot(T[i])
        N.append(v.normalized() if v.length > 1e-5 else (N[-1] if N else V_((0, 0, 1))))
    for _ in range(passes):
        M_ = []
        for i in range(n):
            v = N[max(i - 1, 0)] + N[i] * 2 + N[min(i + 1, n - 1)]; v = v - T[i] * v.dot(T[i])
            M_.append(v.normalized() if v.length > 1e-5 else N[i])
        N = M_
    S = [0.0]
    for i in range(1, n): S.append(S[-1] + (sp[i] - sp[i - 1]).length)
    return T, N, S


def W2_rattler():
    """The RATTLESNAKE (2026-10-14, remade like the alien / autumn bosses): a western diamondback built like the real snake - a heavy body
    that tapers to a thin neck behind a broad triangular head, grey-brown with the dark diamonds down its back, each outlined in cream, the
    belly scutes cream with a fine dark seam between each, and before the rattle the black-and-white "coon tail" rings. The head is a pit
    viper's: the supraocular plates jut over the eyes like a frown, yellow eyes with the vertical slit pupil, the heat pit between eye and
    nostril, the dark stripe behind each eye edged in cream; the jaws thrown open to strike - the pale mouth, the two long fangs swung forward
    on their bones, a forked black tongue - and down the throat the venom glow his shots leave from. An outlaw's black hat with a gold band
    is still cocked on his head. The rattle is a real rattle: eight hollow interlocking segments, held high behind and shaking (FlapRattle).
    He flies like the outlaw he is, on a DYNAMITE ROCKET ("how is it going to fly - it has to have some kind of indicator"): seven sticks of
    red dynamite bundled in two brass hoops, a riveted brass nose cone, four wooden fins nailed on in an X, an iron nozzle at the back with
    fire roaring out of it, sparks and a trail of smoke, and a burning fuse; he is coiled twice round the bundle, gripping it, his neck
    rearing high over the nose to strike and his tail raised over the fins. The rocket dives at you nose-down, so you look along it at
    the fins, the fire flaring out round him and the smoke rising behind."""
    TILT = 18
    P = Boss("rattler2", AB_pal(Base=((0.56, 0.42, 0.27), 0.45), Belly=((0.94, 0.88, 0.72), 0.4), Accent=((0.98, 0.93, 0.80), 0.45),
                                Trim=((0.74, 0.09, 0.06), 0.35), Glass=((0.2, 0.11, 0.05), 0.5), Dark=((0.04, 0.035, 0.03), 0.5),
                                Glow=((1.0, 0.8, 0.12), 0.5), Metal=((0.98, 0.74, 0.2), 0.8), Lamp=((0.95, 0.32, 0.05), 0.6)))
    glow_strength(P, 2.5); glow_strength(P, 1.1, "_Lamp")   # previews only: the game lights Lamp at 1.7x its colour, the fire reads orange
    # ---- the dynamite rocket (built with its axis on +Y, the nose at the player; at the end the whole boss is tipped nose-down so the
    #      player, who sees him from a little above, looks along the rocket at its fins, its fire and its smoke)
    RS, RR, RO = 0.15, 0.3, 0.45   # a stick's radius, the ring the six outer sticks sit on, the bundle's outer radius
    def R(bm, slot, smooth=True): P.obj("Rocket", bm, slot, 0, smooth)
    for k in range(7):
        a = 2 * math.pi * k / 6
        x, z = (0.0, 0.0) if k == 6 else (math.cos(a) * RR, math.sin(a) * RR)
        R(pipe([V_((x, -0.9, z)), V_((x, 0.9, z))], [RS, RS], 16), "Trim")
        R(oriented_ball(V_((x, -0.9, z)), (RS * 0.9, 0.035, RS * 0.9), V_((1, 0, 0)), V_((0, 1, 0)), V_((0, 0, 1)), 14, 4), "Accent")   # the crimped paper end
    for y in (-0.62, 0.72):   # the brass hoops binding the bundle, a rivet every hand's width
        R(xf(torus(RO + 0.02, 0.035, 0.0, 40, 6), Matrix.Rotation(math.pi / 2, 3, "X"), (0, y, 0)), "Metal")
        for j in range(14):
            a = 2 * math.pi * j / 14
            R(ball((math.cos(a) * (RO + 0.055), y, math.sin(a) * (RO + 0.055)), (0.018,) * 3, 6, 3), "Metal")
    nose = lathe([(0.48, 0.0), (0.45, 0.12), (0.38, 0.3), (0.28, 0.5), (0.17, 0.68), (0.07, 0.82), (0.0, 0.88)], 32, "y", (0, 0.9, 0))
    R(nose, lambda c, nn: "Trim" if c.y > 1.47 else "Metal")   # the nose cone, brass, its point painted red
    for j in range(16):
        a = 2 * math.pi * j / 16
        R(ball((math.cos(a) * 0.485, 0.96, math.sin(a) * 0.485), (0.017,) * 3, 6, 3), "Dark")
    R(xf(torus(0.21, 0.02, 0.0, 24, 4), Matrix.Rotation(math.pi / 2, 3, "X"), (0, 1.47, 0)), "Accent")   # a cream band where the red begins
    for k in range(4):   # four wooden fins in a cross, flat out to the sides and up and down, three nails along each root
        a = math.radians(90 * k); o = V_((math.cos(a), 0, math.sin(a))); w = V_((-math.sin(a), 0, math.cos(a))) * 0.025
        root0, root1 = o * 0.4 + V_((0, -1.08, 0)), o * 0.4 + V_((0, -0.6, 0))
        tip0, tip1 = o * 1.18 + V_((0, -1.24, 0)), o * 1.18 + V_((0, -0.95, 0))
        R(hull([tuple(p + w) for p in (root0, root1, tip0, tip1)] + [tuple(p - w) for p in (root0, root1, tip0, tip1)]), "Glass", False)
        for j in range(3):
            q = o * 0.5 + V_((0, -1.0 + 0.17 * j, 0))
            for sgn in (1, -1): R(ball(tuple(q + w * 1.15 * sgn), (0.016,) * 3, 6, 3), "Dark")
    R(lathe([(0.2, -0.86), (0.24, -0.95), (0.3, -1.06), (0.34, -1.12), (0.3, -1.12), (0.25, -1.05), (0.19, -0.96)], 28, "y"), "Dark")   # the iron nozzle
    R(oriented_ball(V_((0, -1.08, 0)), (0.27, 0.02, 0.27), V_((1, 0, 0)), V_((0, 1, 0)), V_((0, 0, 1)), 20, 4), "Glow")
    # the fire roaring out of it: a yellow core in a ring of red-orange tongues flaring back, sparks off the rim
    R(pipe([V_((0, -1.1, 0)), V_((0, -1.35, 0)), V_((0, -1.65, 0)), V_((0, -1.9, 0)), V_((0, -2.05, 0))], [0.22, 0.26, 0.22, 0.12, 0.0], 16), "Glow")
    for k in range(10):
        a = 2 * math.pi * k / 10; o = V_((math.cos(a), 0, math.sin(a)))
        R(flame(o * 0.26 + V_((0, -1.1, 0)), o * 1.15 + V_((0, -1, 0)), 0.95 + 0.15 * (k % 2), 0.12, o * 0.8), "Lamp")   # flaring wide: from the front a ring of fire shows round him
    for k in range(12):
        a = 2 * math.pi * (k + 0.5) / 12; o = V_((math.cos(a), 0, math.sin(a)))
        b0 = o * 0.36 + V_((0, -1.12, 0))
        R(cone(b0, b0 + (o * 0.8 + V_((0, -0.6, 0))).normalized() * 0.22, 0.018, 4), "Glow", False)
    # the burning fuse curling up out of the back of the top stick, sparks at its tip
    fz = [V_((0, -0.9, RR)), V_((0, -1.0, RR + 0.08)), V_((0.05, -1.08, RR + 0.22)), V_((0.02, -1.12, RR + 0.36))]
    R(pipe(fz, [0.022, 0.022, 0.02, 0.018], 6), "Dark")
    ft = fz[-1]
    R(ball(tuple(ft), (0.04,) * 3, 8, 4), "Glow")
    for k in range(6):
        a = 2 * math.pi * k / 6; d = V_((math.cos(a), -0.3, math.sin(a) + 0.6)).normalized()
        R(cone(ft, ft + d * 0.12, 0.012, 4), "Glow", False)
    # the smoke trail behind, drifting up as it falls back
    for k in range(3):
        c = V_((0, -2.0 - 0.3 * k, 0.15 + 0.2 * k + 0.04 * k * k)); r = 0.24 + 0.07 * k
        P.obj("Smoke", ball(tuple(c), (r, r * 0.9, r * 0.85), 14, 7), "Belly")
        P.obj("Smoke", ball(tuple(c + V_((0.12 * (1 if k % 2 else -1), 0.05, r * 0.45))), (r * 0.6,) * 3, 12, 6), "Belly")

    # ---- the snake: down from the raised tail onto the rocket, twice round the bundle, along its top and up over the nose to strike
    RC = RO + 0.2   # the coils' radius round the rocket's axis
    ctrl = [V_((0, -0.32, 1.38)), V_((0, -0.3, 1.12)), V_((0, -0.28, 0.86)), V_((0, -0.26, RC + 0.01))]
    for k in range(1, 25):
        th = math.radians(90 - 30 * k); y = -0.26 + 0.81 * k / 24
        ctrl.append(V_((math.cos(th) * RC, y, math.sin(th) * RC)))
    ctrl += [V_((0, 0.75, RC + 0.01)), V_((0, 0.95, 0.86)), V_((0, 1.07, 1.12)), V_((0, 1.2, 1.3)), V_((0, 1.36, 1.36))]
    sp = spline(ctrl, 6)
    def hint(p, t):
        da = math.hypot(p.x, p.z); w = max(0.0, min(1.0, (RC + 0.18 - da) / 0.18)) if -0.45 < p.y < 0.85 else 0.0
        radial = V_((p.x, 0, p.z)) / max(da, 1e-4)
        other = V_((0, -1, 1)).normalized() if p.y > 0.6 else V_((0, -1, 0))
        return radial * w + other * (1 - w)
    T, N, S = hint_frames(sp, hint); L = S[-1]
    WX, HU, HD = [], [], []
    for s_ in S:
        r = lerp_keys(s_ / L, [(0, 0.045), (0.05, 0.1), (0.14, 0.165), (0.75, 0.17), (0.88, 0.13), (1, 0.14)])
        WX.append(r); HU.append(r); HD.append(r * 0.86)
    def skin_paint(c, nn):
        i = min(range(len(sp)), key=lambda j: (sp[j] - c).length_squared)
        v = (c - sp[i]).dot(N[i]) / max(HU[i], 1e-4)
        if v < -0.15: return "Dark" if (S[i] / 0.07) % 1.0 < 0.1 else "Belly"          # the belly scutes and the seams between them
        if S[i] / L < 0.1: return "Dark" if (S[i] / 0.09) % 1.0 < 0.5 else "Belly"      # the coon tail before the rattle
        return "Base"
    P.obj("Body", ribbon_tube(sp, T, N, WX, HU, HD, 28, 1.1), skin_paint, 0)
    # the diamonds down his back: each a dark plate edged by a cream one under it, laid on the skin at even steps
    def surf(sv, u, lift):
        i = min(range(len(S)), key=lambda j: abs(S[j] - sv)); side = T[i].cross(N[i]).normalized()
        vt = max(0.0, 1 - abs(u) ** 2.2) ** (1 / 2.2)
        return sp[i] + side * u * WX[i] + N[i] * (HU[i] * vt + lift)
    def diamond(sv, a, b, lift0, lift1, slot, name):
        pts = []
        for ia in range(-4, 5):
            for ib in range(-4, 5):
                ds, du = a * ia / 4, b * ib / 4
                if abs(ds) / a + abs(du) / b > 1.001: continue
                pts += [tuple(surf(sv + ds, du, lift1)), tuple(surf(sv + ds, du, lift0))]
        P.obj(name, hull(pts), slot, 0, False)
    sv = L * 0.12
    while sv < L * 0.86:
        diamond(sv, 0.14, 0.72, -0.03, 0.006, "Accent", "DiamondEdge")
        diamond(sv, 0.1, 0.52, -0.02, 0.013, "Glass", "Diamond")
        sv += 0.3
    # ---- the rattle: eight hollow segments, each a little smaller, interlocked, raised over the fins and shaking
    tp = sp[0]; ud = (sp[0] - sp[4]).normalized(); sd = ud.cross(V_((0, 1, 0))).normalized(); fd = sd.cross(ud).normalized()
    for k in range(8):
        c = tp + ud * (0.03 + k * 0.085); r = 0.075 - k * 0.0055
        P.part("FlapRattle", oriented_ball(c, (r, 0.045, r * 0.62), sd, ud, fd, 14, 6), "Accent" if k % 2 else "Belly", tuple(tp))
        P.part("FlapRattle", oriented_ball(c + ud * 0.042, (r * 0.86, 0.016, r * 0.5), sd, ud, fd, 14, 3), "Glass", tuple(tp))   # the groove between lobes
    P.part("FlapRattle", oriented_ball(tp + ud * 0.72, (0.026, 0.03, 0.02), sd, ud, fd, 8, 4), "Glass", tuple(tp))

    # ---- the head: built pointing +Y about the back of the skull, then set on the neck and tipped down at the player
    HB = sp[-1]; HR = Matrix.Rotation(math.radians(TILT - 14), 3, "X") @ Matrix.Scale(1.8, 3); HI = HR.inverted()   # tipped back by the tilt still to come
    def H(bm, m=None): return xf(bm if m is None else xf(bm, m), HR, tuple(HB))
    def hpt(p): return HB + HR @ V_(p)
    MU = Matrix.Rotation(math.radians(16), 3, "X"); ML = Matrix.Rotation(math.radians(-30), 3, "X")
    def U(bm): return H(xf(bm, MU))                       # the upper jaw, thrown up about the hinge at the origin
    def Lj(bm): return H(xf(bm, ML))                      # the lower jaw, dropped
    UPR = [(-0.06, 0.15, 0.11, 0, 0.03), (0.04, 0.23, 0.12, 0, 0.045), (0.16, 0.25, 0.115, 0, 0.05), (0.29, 0.21, 0.1, 0, 0.05),
           (0.41, 0.16, 0.08, 0, 0.045), (0.5, 0.11, 0.06, 0, 0.035), (0.55, 0.06, 0.04, 0, 0.025)]
    up = loft(UPR, 26, sq=1.25)
    for v in up.verts: v.co.z = max(v.co.z, 0.0)
    UI = MU.inverted()
    def headpaint(c, nn):
        q = UI @ (HI @ (c - HB)); n2 = (UI @ (HI @ nn)).normalized()
        if n2.z < -0.6: return "Belly"                                                     # the pale roof of the mouth
        z_stripe = 0.07 - (0.16 - q.y) * 0.35                                              # the line from the eye down to the jaw corner
        if abs(q.x) > 0.15 and q.y < 0.19:
            if abs(q.z - z_stripe) < 0.022: return "Glass"
            if abs(abs(q.z - z_stripe) - 0.033) < 0.011: return "Accent"
        if n2.z > 0.6 and q.y < 0.12 and abs(q.x) < 0.12 and (q.y / 0.1) % 1.0 < 0.3: return "Glass"   # two dark bars across the crown
        return "Base"
    P.obj("Head", U(up), headpaint, 0)
    lo = loft([(-0.04, 0.2, 0.06, 0, -0.03), (0.16, 0.22, 0.06, 0, -0.035), (0.34, 0.16, 0.05, 0, -0.03), (0.48, 0.09, 0.035, 0, -0.02), (0.52, 0.04, 0.02, 0, -0.015)], 22, sq=1.2)
    for v in lo.verts: v.co.z = min(v.co.z, -0.012)
    LI = ML.inverted()
    P.obj("Jaw", Lj(lo), lambda c, nn: "Lamp" if (LI @ (HI @ nn)).normalized().z > 0.5 else ("Belly" if (LI @ (HI @ nn)).normalized().z < -0.5 else "Base"), 0)
    P.obj("Gullet", H(ball((0, 0.02, -0.01), (0.1, 0.08, 0.07), 12, 6)), "Lamp")
    P.obj("Glottis", Lj(ball((0, 0.18, 0.0), (0.03, 0.05, 0.015), 8, 4)), "Accent")
    for s in (1, -1):
        # the fangs swung forward on their bones, long and curved, from the front of the upper jaw
        P.obj("Fang", U(pipe(bez((s * 0.075, 0.44, 0.0), (s * 0.075, 0.48, -0.06), (s * 0.072, 0.48, -0.13), (s * 0.065, 0.44, -0.18), 6),
                             [0.022, 0.02, 0.017, 0.014, 0.01, 0.005, 0.0], 8)), "Accent")
        P.obj("FangSheath", U(ball((s * 0.075, 0.44, -0.005), (0.03, 0.035, 0.02), 8, 4)), "Lamp")
        for k in range(4):   # the small back teeth along each jaw
            y = 0.12 + 0.07 * k
            P.obj("Tooth", U(cone((s * (0.17 - 0.03 * k), y, 0.0), (s * (0.17 - 0.03 * k), y - 0.01, -0.035), 0.008, 4)), "Accent", 0, False)
            P.obj("Tooth", Lj(cone((s * (0.15 - 0.025 * k), y, -0.01), (s * (0.15 - 0.025 * k), y - 0.01, 0.025), 0.008, 4)), "Accent", 0, False)
        # the eye: yellow, the vertical slit pupil, sunk under the supraocular plate that juts over it - the frown
        ec = V_((s * 0.19, 0.27, 0.075)); dv = V_((s * 0.62, 0.76, 0.12)).normalized()
        ex = dv.cross(V_((0, 0, 1))).normalized(); ez = ex.cross(dv).normalized()
        if ez.z < 0: ez = -ez
        P.obj("Eye", U(oriented_ball(ec, (0.05, 0.035, 0.045), ex, dv, ez, 12, 6)), "Glow")
        P.obj("Pupil", U(oriented_ball(ec + dv * 0.03, (0.008, 0.012, 0.034), ex, dv, ez, 6, 4)), "Dark")
        P.obj("Supraocular", U(hull([(s * 0.1, 0.36, 0.11), (s * 0.12, 0.35, 0.135), (s * 0.27, 0.22, 0.15), (s * 0.27, 0.2, 0.12), (s * 0.22, 0.3, 0.155),
                                     (s * 0.14, 0.24, 0.12), (s * 0.24, 0.16, 0.13)])), "Glass", 0, False)
        P.obj("Pit", U(oriented_ball(V_((s * 0.15, 0.4, 0.035)), (0.022, 0.016, 0.014), ex, dv, ez, 8, 4)), "Dark")
        P.obj("Nostril", U(ball((s * 0.06, 0.52, 0.05), (0.014, 0.012, 0.012), 6, 3)), "Dark")
    # the forked tongue flicking out at you
    tg = bez((0, 0.1, -0.02), (0, 0.28, 0.0), (0, 0.4, 0.06), (0, 0.5, 0.12), 8)
    P.obj("Tongue", Lj(pipe(tg, [0.022 - 0.0015 * k for k in range(9)], 8)), "Dark")
    for s in (1, -1):
        P.obj("Tongue", Lj(pipe(bez((0, 0.5, 0.12), (s * 0.02, 0.54, 0.15), (s * 0.04, 0.56, 0.18), (s * 0.055, 0.57, 0.22), 4), [0.012, 0.01, 0.007, 0.004, 0.0], 6)), "Dark")
    # the outlaw's hat cocked on the skull, a gold band
    n0 = len(P.parts)
    stetson(P, (0, 0, 0), 1.0, 0.0, "Dark", "Metal", "Metal", "Hat", 0.1)
    for ob in P.parts[n0:]:
        m4 = Matrix.Translation(HB) @ HR.to_4x4() @ MU.to_4x4() @ Matrix.Translation((0.02, 0.04, 0.115)) @ Matrix.Rotation(math.radians(10), 4, "Y") @ Matrix.Rotation(math.radians(-8), 4, "X") @ Matrix.Scale(0.5, 4)
        ob.data.transform(m4)
    mz = hpt((0, 0.06, -0.01))
    P.part("Muzzle", ball(tuple(mz), (0.04, 0.03, 0.03), 8, 4), "Lamp", tuple(mz))
    # the whole boss tipped nose-down (his face kept level by the head's own tilt above)
    Mt = Matrix.Rotation(math.radians(-TILT), 4, "X")
    for ob in P.parts: ob.data.transform(Mt)
    for ob in P.spin: ob.location = Mt @ ob.location; ob.data.transform(Matrix.Rotation(math.radians(-TILT), 4, "X"))
    return P


def fib_dirs(n):
    """n unit vectors spread evenly over a sphere (the golden-angle spiral)."""
    out = []
    for i in range(n):
        z = 1 - 2 * (i + 0.5) / n; r = math.sqrt(max(0.0, 1 - z * z)); a = i * 2.399963
        out.append(V_((math.cos(a) * r, math.sin(a) * r, z)))
    return out


def W2_scorpion():
    """The SCORPION KING (2026-10-14, remade like the alien / autumn bosses): a giant desert hairy scorpion built like the real animal. The
    carapace a shield over the head with the two median eyes on their mound and three lateral eyes at each front corner, small chelicerae
    in front; the body of seven tergites, each plate edged in gold, a glowing seam between them - scorpions really glow blue-green under
    the desert moon - and the tail of five keeled segments, each longer than the last, ringed with gold where they join, arched high over
    his back to the bulb of venom and the curved black sting aimed at you, a drop of venom shining on its point. The pincers are the real
    pedipalps: femur, patella and a heavy chela with a fixed and a movable finger lined with teeth, the hand rough with even rows of
    granules, raised and lowered as he threatens (SwayClawR / SwayClawL); eight legs of four segments each, every segment with a pair of
    hairs, the tarsal claws hooked into the branches under him. On the carapace a gold crown with five points and a ruby in each.
    He flies on a TUMBLEWEED: he clings to the top of a giant one, a ball of dry branches - long arcs crossing evenly all round it, each
    with short side twigs at even steps - that the desert wind rolls along under him (RollWeed)."""
    P = Boss("scorpion", AB_pal(Base=((0.13, 0.08, 0.05), 0.75), Belly=((0.76, 0.6, 0.36), 0.25), Accent=((0.72, 0.04, 0.07), 0.6),
                                Trim=((1.0, 0.76, 0.22), 0.85), Glass=((0.95, 0.58, 0.1), 0.8), Dark=((0.03, 0.02, 0.02), 0.6),
                                Glow=((0.25, 1.0, 0.72), 0.5), Metal=((0.46, 0.33, 0.18), 0.25), Lamp=((1.0, 0.9, 0.5), 0.8)))
    glow_strength(P, 2.2)
    BZ = 0.12   # the height his body rides at, over the top of the weed
    # ---- the carapace: a shield, wider behind, the eye mound in the middle front
    car = loft([(0.72, 0.13, 0.05, 0, BZ + 0.05), (0.62, 0.24, 0.09, 0, BZ + 0.06), (0.45, 0.31, 0.12, 0, BZ + 0.07), (0.25, 0.35, 0.13, 0, BZ + 0.07),
                (0.08, 0.36, 0.11, 0, BZ + 0.06), (0.02, 0.3, 0.06, 0, BZ + 0.04)], 24, sq=1.35)
    for v in car.verts: v.co.z = max(v.co.z, BZ - 0.02)
    P.obj("Carapace", car, "Base", 0)
    P.obj("CarapaceRim", loft([(0.7, 0.15, 0.025, 0, BZ - 0.0), (0.45, 0.33, 0.025, 0, BZ - 0.0), (0.06, 0.38, 0.025, 0, BZ - 0.0)], 24, sq=1.35), "Trim")
    P.obj("EyeMound", ball((0, 0.5, BZ + 0.18), (0.07, 0.06, 0.04), 10, 5), "Base")
    for s in (1, -1):
        P.obj("MedianEye", ball((s * 0.035, 0.53, BZ + 0.21), (0.03, 0.03, 0.026), 8, 4), "Glow")
        for k in range(3):   # the lateral eyes, three in a row at each front corner
            P.obj("LateralEye", ball((s * (0.12 + 0.03 * k), 0.69 - 0.035 * k, BZ + 0.1), (0.018,) * 3, 6, 3), "Glow")
        P.obj("Chelicera", pipe(bez((s * 0.05, 0.7, BZ + 0.04), (s * 0.06, 0.8, BZ + 0.04), (s * 0.04, 0.86, BZ + 0.02), (s * 0.015, 0.88, BZ - 0.01), 4),
                                [0.04, 0.035, 0.025, 0.014, 0.0], 8), "Dark")
    # the crown: a gold band with five points, a ruby on each
    P.obj("Crown", lathe([(0.15, 0.0), (0.16, 0.0), (0.155, 0.07), (0.145, 0.07)], 24, "z", (0, 0.32, BZ + 0.15)), "Trim")
    for k in range(5):
        a = 2 * math.pi * k / 5
        b = V_((math.sin(a) * 0.155, 0.32 + math.cos(a) * 0.155, BZ + 0.21))
        P.obj("CrownPoint", cone(b, b + V_((math.sin(a) * 0.02, math.cos(a) * 0.02, 0.13)), 0.04, 4), "Trim", 0, False)
        P.obj("CrownBall", ball(tuple(b + V_((math.sin(a) * 0.022, math.cos(a) * 0.022, 0.14))), (0.018,) * 3, 6, 3), "Trim")
        P.obj("CrownRuby", ball(tuple(V_((math.sin(a) * 0.165, 0.32 + math.cos(a) * 0.165, BZ + 0.185))), (0.022, 0.022, 0.026), 8, 4), "Accent")
    # ---- the mesosoma: seven tergites, wider in the middle, a gold edge on each and a glowing seam between
    for k in range(7):
        y0 = 0.02 - 0.15 * k; w = lerp_keys(k / 6, [(0, 0.38), (0.4, 0.42), (1, 0.27)])
        P.obj("Tergite", loft([(y0, w * 0.97, 0.11, 0, BZ + 0.02), (y0 - 0.07, w, 0.13, 0, BZ + 0.03), (y0 - 0.13, w * 0.98, 0.11, 0, BZ + 0.02)], 24, sq=1.3), "Base", 0)
        P.obj("TergiteEdge", loft([(y0 - 0.125, w * 0.99, 0.112, 0, BZ + 0.02), (y0 - 0.145, w * 0.96, 0.1, 0, BZ + 0.02)], 24, sq=1.3), "Trim", 0)
        P.obj("Seam", loft([(y0 - 0.14, w * 0.93, 0.09, 0, BZ + 0.015), (y0 - 0.155, w * 0.9, 0.085, 0, BZ + 0.015)], 24, sq=1.3), "Glow", 0)
        P.obj("Keel", pipe([V_((0, y0 - 0.02, BZ + 0.15)), V_((0, y0 - 0.11, BZ + 0.15))], [0.016, 0.016], 6), "Dark")
    P.obj("Belly", ball((0, -0.45, BZ - 0.02), (0.35, 0.62, 0.07), 18, 6), "Base")
    # ---- the tail: five keeled segments arching over his back, gold rings at the joints, the venom bulb and the sting aimed at you
    tail = spline([V_((0, -1.0, BZ + 0.05)), V_((0, -1.25, BZ + 0.45)), V_((0, -1.12, BZ + 1.0)), V_((0, -0.7, BZ + 1.42)), V_((0, -0.15, BZ + 1.55)),
                   V_((0, 0.25, BZ + 1.38))], 6)
    Tt, Nt, St = transport(tail); Lt = St[-1]
    cuts = [0.0, 0.16, 0.33, 0.5, 0.68, 0.88]   # five segments, each longer than the one before
    def tail_at(f):
        sv = f * Lt; i = min(range(len(St)), key=lambda j: abs(St[j] - sv)); return tail[i], Tt[i], Nt[i]
    for k in range(5):
        f0, f1 = cuts[k], cuts[k + 1]
        r0 = lerp_keys(k / 4, [(0, 0.15), (1, 0.12)]); pts, rr = [], []
        for j in range(7):
            f = max(0.0, min(1.0, f0 - 0.012 + (f1 - f0 + 0.024) * j / 6))
            p, t, nn = tail_at(f); pts.append(p); rr.append(r0 * (0.84 + 0.16 * math.sin(math.pi * j / 6)))
        P.obj("TailSeg", pipe(pts, rr, 14), "Base")
        for side in (1, -1):   # two dorsal keels down each segment
            kp = []
            for j in range(5):
                p, t, nn = tail_at(f0 + (f1 - f0) * (0.12 + 0.76 * j / 4)); sd = t.cross(nn).normalized()
                kp.append(p + (nn * 0.85 + sd * side * 0.45).normalized() * r0 * 0.98)
            P.obj("TailKeel", pipe(kp, [0.0, 0.016, 0.018, 0.016, 0.0], 5), "Dark")
        p, t, nn = tail_at(f1)
        P.obj("TailRing", xf(torus(r0 * 0.86, 0.026, 0.0, 18, 5), Matrix(sq_axes(t)).transposed(), tuple(p)), "Trim")
        P.obj("TailJoint", ball(tuple(p), (r0 * 0.86,) * 3, 12, 6), "Dark")
    p, t, nn = tail_at(1.0)
    vb = p + t * 0.15
    P.obj("Vesicle", oriented_ball(vb, (0.15, 0.2, 0.14), t.cross(nn).normalized(), t, nn, 14, 7), "Glass")
    P.obj("VesicleBand", xf(torus(0.13, 0.018, 0.0, 18, 5), Matrix(sq_axes(t)).transposed(), tuple(p + t * 0.02)), "Trim")
    tip0 = vb + t * 0.17
    sting = bez(tip0, tip0 + t * 0.14, tip0 + t * 0.24 - nn * 0.08, tip0 + t * 0.26 - nn * 0.2, 6)
    P.obj("Aculeus", pipe(sting, [0.055, 0.045, 0.034, 0.024, 0.015, 0.007, 0.0], 8), "Dark")
    drop = sting[-1] - nn * 0.04
    P.obj("Venom", ball(tuple(drop), (0.035, 0.035, 0.05), 10, 5), "Glow")

    # ---- the pincers: femur, patella, the heavy chela with its fingers open, granules in rows; raised and lowered
    for s in (1, -1):
        name = "SwayClawR" if s > 0 else "SwayClawL"
        sh = V_((s * 0.2, 0.62, BZ + 0.0))
        fe = sh + V_((s * 0.42, 0.18, 0.12)); pa = fe + V_((s * 0.05, 0.36, 0.06)); hb = pa + V_((-s * 0.06, 0.12, 0.0))
        P.part(name, ball(tuple(sh), (0.07,) * 3, 8, 4), "Base", tuple(sh))
        P.part(name, pipe([sh, fe], [0.065, 0.058], 10), "Base", tuple(sh))
        P.part(name, ball(tuple(fe), (0.07,) * 3, 10, 5), "Trim", tuple(sh))
        P.part(name, pipe([fe, (fe + pa) * 0.5 + V_((s * 0.03, 0, 0.02)), pa], [0.07, 0.085, 0.075], 10), "Base", tuple(sh))
        # the hand (manus): swollen, flattened, granules in even rows on top
        d = V_((-s * 0.12, 1.0, 0.0)).normalized(); sd = d.cross(V_((0, 0, 1))).normalized() * s; up = V_((0, 0, 1))
        mc = hb + d * 0.2
        P.part(name, oriented_ball(mc, (0.17, 0.27, 0.13), sd * s, d, up, 16, 8), "Base", tuple(sh))
        for r_ in range(3):
            for j in range(4):
                q = mc + d * (-0.15 + 0.1 * j) + sd * s * (-0.07 + 0.07 * r_) + up * 0.12
                P.part(name, ball(tuple(q), (0.02,) * 3, 6, 3), "Dark", tuple(sh))
        # the fixed finger (outer) and the movable finger (inner), opened, lined with small teeth, gold tips
        root = mc + d * 0.24
        for which, ang_ in (("fixed", 0.16), ("movable", -0.22)):
            fd_ = (Matrix.Rotation(ang_ * s, 3, "Z") @ d).normalized()
            off = sd * s * (0.06 if which == "fixed" else -0.06)
            f0 = root + off; f2 = f0 + fd_ * 0.38 + (-off * 0.9)
            pts = bez(f0, f0 + fd_ * 0.15, f2 - fd_ * 0.08 + off * 0.2, f2, 6)
            P.part(name, pipe(pts, [0.07, 0.062, 0.052, 0.04, 0.028, 0.016, 0.0], 9), lambda c, nn, f2=f2: "Trim" if (c - f2).length < 0.08 else "Base", tuple(sh))
            for j in range(4):
                q = pts[1 + j]; tdir = (-off).normalized()
                P.part(name, cone(q + tdir * 0.03, q + tdir * 0.065, 0.014, 4), "Dark", tuple(sh))
    # ---- eight legs, four segments each, a pair of hairs on every segment, the tarsal claws hooked into the weed
    for s in (1, -1):
        for k in range(4):
            hip = V_((s * 0.3, 0.42 - 0.17 * k, BZ - 0.02))
            fwd = lerp_keys(k / 3, [(0, 0.35), (1, -0.4)])
            knee = hip + V_((s * 0.32, fwd * 0.4, 0.2)); ankle = knee + V_((s * 0.22, fwd * 0.35, -0.24)); foot = ankle + V_((s * 0.06, fwd * 0.15, -0.2))
            joints = [hip, knee, ankle, foot]
            radii = [0.05, 0.042, 0.032, 0.02]
            for j in range(3):
                a, b = joints[j], joints[j + 1]
                P.obj("Leg", pipe([a, (a + b) * 0.5, b], [radii[j], radii[j] * 1.08, radii[j + 1]], 8), "Base")
                P.obj("LegJoint", ball(tuple(b), (radii[j + 1] * 1.15,) * 3, 6, 3), "Trim" if j == 0 else "Base")
                for h in (0.35, 0.7):   # a pair of hairs on each segment
                    q = a + (b - a) * h; dd = (b - a).normalized(); o = dd.cross(V_((0, 0, 1))).normalized()
                    P.obj("Seta", cone(q, q + (o * s * 0.6 + V_((0, 0, 0.5)) + dd * 0.3).normalized() * 0.07, 0.006, 3), "Belly", 0, False)
            for c_ in (1, -1):
                P.obj("Claw", pipe(bez(foot, foot + V_((c_ * 0.02, 0.02, -0.03)), foot + V_((c_ * 0.03, 0.0, -0.06)), foot + V_((c_ * 0.025, -0.03, -0.07)), 3), [0.012, 0.01, 0.006, 0.0], 5), "Dark")

    # ---- the tumbleweed: long dry branches in arcs crossing evenly all round a ball, short side twigs at even steps; it rolls under him
    WC = V_((0, -0.2, -0.95)); WRd = 0.95; hub = tuple(WC)
    for layer, (count, R, th, col) in enumerate(((44, WRd, 0.013, "Belly"), (26, WRd * 0.62, 0.011, "Metal"))):   # an outer shell of arcs and a darker tangle inside
        for i, nrm in enumerate(fib_dirs(count)):
            a1 = nrm.cross(V_((0, 0, 1)) if abs(nrm.z) < 0.9 else V_((1, 0, 0))).normalized(); a2 = nrm.cross(a1).normalized()
            ph = i * 2.4; arc = []
            for j in range(21):
                t = ph + 2 * math.pi * 0.42 * j / 20
                rr = R * (0.9 + 0.1 * math.sin(2 * t + i * 1.3))
                arc.append(WC + (a1 * math.cos(t) + a2 * math.sin(t)) * rr)
            P.part("RollWeed", pipe(arc, [0.0] + [th * (1.0 + 0.5 * math.sin(math.pi * j / 20)) for j in range(1, 20)] + [0.0], 4), col, hub, 0, True)
            if layer: continue
            for j in range(3, 19, 4):   # side twigs, alternating sides, pointing on along the branch
                p = arc[j]; tdir = (arc[j + 1] - arc[j - 1]).normalized(); outn = (p - WC).normalized()
                side_ = tdir.cross(outn).normalized() * (1 if j % 8 == 3 else -1)
                tw = [p, p + (tdir * 0.6 + side_ * 0.6 + outn * 0.1).normalized() * 0.08, p + (tdir * 0.8 + side_ * 0.5 + outn * 0.15).normalized() * 0.15]
                P.part("RollWeed", pipe(tw, [0.009, 0.006, 0.0], 4), "Belly", hub, 0, True)
    P.part("Muzzle", ball(tuple(drop), (0.03, 0.03, 0.03), 8, 4), "Glow", tuple(drop))
    return P


def flame(base, d, L, r, curl=None):
    """a tongue of spirit fire from base along d, swelling then licking to a point, its tip curling toward curl."""
    base = V_(base); d = V_(d).normalized(); curl = V_(curl) if curl is not None else V_((0, 0, 1))
    pts = bez(base, base + d * L * 0.35, base + d * L * 0.7 + curl * L * 0.12, base + d * L + curl * L * 0.3, 6)
    return pipe(pts, [r * 0.6, r, r * 0.95, r * 0.75, r * 0.5, r * 0.25, 0.0], 8)


def W2_ghostrider():
    """The GHOST RIDER (2026-10-14, remade like the alien / autumn bosses): a dead outlaw on a ghost mustang, out of the old cowboy song.
    The horse is built like a real mustang in the gallop - an arched neck, a deep chest, a short back and round quarters, legs jointed like a
    horse's down to the hoof - but it is a spirit: a pale spectral hide with its ribs showing through in bone along both flanks, and for a
    head a bare horse skull, the long face and the great eye sockets with a green fire in each, the nasal opening, the rows of teeth and the
    jaw dropped in a scream. Its mane and its tail are spirit fire, tongues of green flame licking back along the crest and fanned from the
    dock, and green fire burns round every hoof. A worn saddle on a ragged red blanket, a coiled lariat on the horn, a silver-studded bridle.
    The rider is a skeleton: a skull with green fire in the sockets and a grin of teeth under a black cattleman's hat with silver conchos, a
    red bandana at the bones of his neck, a long black duster with a cape over the shoulders, its tails torn into rags and streaming
    back over the horse's quarters, bone hands - the left on the reins, the right aiming a revolver at you - a gun belt with silver
    cartridges, boots in the stirrups with silver spurs.
    He rides across the sky the way the song has it, on a storm: the mustang gallops (SwayLeg0-3) over a churning ring of black storm cloud
    that turns under its hooves (SpinCloud), forks of green lightning hanging from it."""
    P = Boss("ghostrider", AB_pal(Base=((0.6, 0.86, 0.82), 0.3), Belly=((0.92, 0.88, 0.76), 0.35), Accent=((0.62, 0.06, 0.05), 0.45),
                                  Trim=((0.84, 0.86, 0.9), 0.9), Glass=((0.32, 0.18, 0.08), 0.3), Dark=((0.06, 0.06, 0.09), 0.4),
                                  Glow=((0.16, 1.0, 0.3), 0.5), Metal=((0.24, 0.24, 0.27), 0.7), Lamp=((0.75, 1.0, 0.8), 0.8)))
    glow_strength(P, 1.6)
    # ---- the mustang's body: the arched neck from the poll to the withers, a deep chest, a short back, round quarters, the dock
    neck = bez((0, 0.98, 0.9), (0, 0.9, 0.68), (0, 0.72, 0.45), (0, 0.48, 0.3), 9)
    torso = bez((0, 0.48, 0.3), (0, 0.15, 0.24), (0, -0.4, 0.24), (0, -0.82, 0.3), 10)[1:]
    PTS = neck + torso + [V_((0, -0.94, 0.27))]
    n = len(PTS); FR = spine_frames(PTS)
    RX, RU, RD = [], [], []
    for i in range(len(neck)):
        u = i / (len(neck) - 1)
        RX.append(lerp_keys(u, [(0, 0.11), (0.5, 0.15), (1, 0.27)])); RU.append(lerp_keys(u, [(0, 0.13), (0.5, 0.18), (1, 0.3)]))
        RD.append(lerp_keys(u, [(0, 0.15), (0.5, 0.24), (1, 0.42)]))
    for i in range(len(torso)):
        u = (i + 1) / len(torso)
        RX.append(lerp_keys(u, [(0, 0.29), (0.3, 0.31), (0.6, 0.28), (0.85, 0.3), (1, 0.26)]))
        RU.append(lerp_keys(u, [(0, 0.18), (0.3, 0.14), (0.6, 0.14), (0.85, 0.2), (1, 0.17)]))
        RD.append(lerp_keys(u, [(0, 0.42), (0.3, 0.4), (0.6, 0.34), (0.85, 0.3), (1, 0.24)]))
    RX.append(0.0); RU.append(0.0); RD.append(0.0)
    bodybm = st_loft(PTS, RX, RU, RD, FR)
    from mathutils.bvhtree import BVHTree
    BV = BVHTree.FromBMesh(bodybm.copy())
    def onbody(c, d, lift):
        hit = BV.ray_cast(V_(c), V_(d).normalized(), 5.0)
        return (hit[0] + hit[1] * lift) if hit[0] is not None else V_(c) + V_(d).normalized() * 0.3
    P.obj("Body", bodybm, "Base", 0)
    # the ribs showing through the spectral hide: seven bone arcs down each flank
    for s in (1, -1):
        for k in range(7):
            y = 0.3 - 0.11 * k; c0 = V_((0, y, 0.2))
            arc = [onbody(c0, (s * math.cos(math.radians(a)), 0.05, math.sin(math.radians(a))), 0.012) for a in range(55, -76, -10)]
            P.obj("Rib", pipe(arc, [0.0] + [0.028] * (len(arc) - 2) + [0.0], 6), "Belly")
    # ---- the mane of spirit fire along the crest, the tail of it fanned from the dock
    for i in range(1, len(neck)):
        p = PTS[i]; t, side, up = FR[i]
        q = p + up * RU[i] * 0.9
        for s in (1, -1):
            P.obj("Mane", flame(q + side * s * 0.03, up * 0.8 - t * 0.9 + side * s * 0.35, 0.3 + 0.1 * math.sin(math.pi * i / len(neck)), 0.05, -t), "Glow", 0, False)
    dock = PTS[-2]
    for k in range(7):
        a = math.radians(-45 + 15 * k)
        d = V_((math.sin(a) * 0.6, -1.0, 0.15 - 0.25 * abs(math.sin(a))))
        P.obj("TailFire", flame(dock, d, 0.85 - 0.12 * abs(k - 3), 0.08, (0, 0, 1)), "Glow", 0, False)

    # ---- the legs: jointed like a horse's, galloping (each its own SwayLeg about the shoulder or hip), green fire round every hoof
    def hleg(name, hub, joints, radii):
        hub = V_(hub); J = [V_(p) for p in joints]
        P.part(name, oriented_ball(hub + V_((0, 0, -0.05)), (0.15, 0.22, 0.27), V_((1, 0, 0)), V_((0, 1, 0)), V_((0, 0, 1)), 12, 6), "Base", tuple(hub))
        P.part(name, pipe([hub] + J[:-1], radii, 10), "Base", tuple(hub))
        for k in range(1, len(J) - 1):
            P.part(name, ball(tuple(J[k]), (radii[min(k + 1, len(radii) - 1)] * 1.2,) * 3, 8, 4), "Belly" if k == 1 else "Base", tuple(hub))   # the knee / hock bone shows
        fet, hoof = J[-2], J[-1]
        d = (hoof - fet).normalized()
        P.part(name, pipe([fet, hoof], [0.045, 0.06], 10), "Dark", tuple(hub))
        P.part(name, ball(tuple(hoof), (0.065, 0.065, 0.05), 10, 5), "Dark", tuple(hub))
        back = V_((0, -1, 0.25))
        for k in range(3):   # the hoof fire, licking back
            a = 2 * math.pi * k / 3
            o = V_((math.cos(a) * 0.05, 0, math.sin(a) * 0.05))
            P.part(name, flame(hoof + o, back + o * 3, 0.3 - 0.05 * k, 0.05, (0, 0, 1)), "Glow", tuple(hub))
    hleg("SwayLeg0", (0.2, 0.52, 0.04), [(0.23, 0.55, -0.34), (0.23, 0.86, -0.52), (0.23, 1.06, -0.6), (0.23, 1.16, -0.66)], [0.13, 0.09, 0.06, 0.05])
    hleg("SwayLeg1", (-0.2, 0.52, 0.04), [(-0.23, 0.44, -0.34), (-0.23, 0.6, -0.55), (-0.23, 0.42, -0.72), (-0.23, 0.36, -0.79)], [0.13, 0.09, 0.06, 0.05])
    hleg("SwayLeg2", (0.21, -0.68, 0.1), [(0.25, -0.46, -0.28), (0.25, -0.9, -0.5), (0.25, -1.08, -0.8), (0.25, -1.16, -0.88)], [0.15, 0.1, 0.06, 0.05])
    hleg("SwayLeg3", (-0.21, -0.68, 0.1), [(-0.25, -0.4, -0.3), (-0.25, -0.75, -0.52), (-0.25, -0.56, -0.8), (-0.25, -0.48, -0.88)], [0.15, 0.1, 0.06, 0.05])

    # ---- the head: a bare horse skull (built pointing +Y about the poll, tipped down), green fire in the sockets, the jaw dropped
    HB = V_((0, 0.98, 0.92)); HR = Matrix.Rotation(math.radians(-34), 3, "X") @ Matrix.Scale(1.25, 3); HI = HR.inverted()
    def H(bm): return xf(bm, HR, tuple(HB))
    def hpt(p): return HB + HR @ V_(p)
    SKR = [(-0.08, 0.1, 0.1, 0, 0.0), (0.02, 0.15, 0.13, 0, 0.02), (0.14, 0.16, 0.12, 0, 0.02), (0.28, 0.12, 0.09, 0, 0.0), (0.42, 0.1, 0.075, 0, -0.01),
           (0.56, 0.09, 0.065, 0, -0.015), (0.64, 0.075, 0.055, 0, -0.02), (0.68, 0.04, 0.035, 0, -0.025)]
    P.obj("Skull", H(loft(SKR, 22, sq=1.25)), "Belly", 0)
    for s in (1, -1):
        oc = V_((s * 0.1, 0.17, 0.075)); od = V_((s * 0.5, 0.8, 0.33)).normalized(); ox = od.cross(V_((0, 0, 1))).normalized(); oz = ox.cross(od).normalized()
        if oz.z < 0: oz = -oz
        P.obj("Orbit", H(oriented_ball(oc, (0.075, 0.05, 0.068), ox, od, oz, 14, 7)), "Dark")
        P.obj("OrbitRim", H(pipe(bez(oc + V_((-s * 0.04, 0.07, 0.02)), oc + V_((s * 0.02, 0.06, 0.075)), oc + V_((s * 0.08, -0.01, 0.07)), oc + V_((s * 0.07, -0.08, 0.03)), 6),
                                 [0.02, 0.028, 0.03, 0.03, 0.026, 0.02, 0.012], 6)), "Belly")   # the brow of bone over the socket: the glare
        P.obj("EyeFire", H(ball(tuple(oc + od * 0.03), (0.034, 0.034, 0.034), 10, 5)), "Glow")
        P.obj("EyeFlame", H(flame(oc + od * 0.03 + oz * 0.02, (s * 0.35, -1.0, 0.7), 0.24, 0.028, (0, 0, 1))), "Glow")
        P.obj("Cheekbone", H(pipe([V_((s * 0.13, 0.2, -0.04)), V_((s * 0.11, 0.36, -0.05))], [0.022, 0.016], 6)), "Belly")
        P.obj("Nasal", H(oriented_ball(V_((s * 0.03, 0.56, 0.035)), (0.026, 0.12, 0.022), V_((1, 0, 0)), V_((0, 1, 0)), V_((0, 0, 1)), 10, 5)), "Dark")
        for k in range(5):   # the cheek teeth along the upper jaw
            P.obj("Tooth", H(box((s * 0.075, 0.24 + 0.06 * k, -0.075), (0.03, 0.045, 0.04))), "Belly", 0, False)
    for k in range(6):   # the incisors at the front, a neat arc
        a = math.radians(-50 + 20 * k)
        P.obj("Tooth", H(box((math.sin(a) * 0.045, 0.66 + math.cos(a) * 0.02, -0.07), (0.018, 0.02, 0.04))), "Belly", 0, False)
    J0 = V_((0, 0.08, -0.06)); JR = Matrix.Rotation(math.radians(-22), 3, "X")
    def Jw(bm): return H(xf(bm, JR, tuple(J0 - JR @ J0)))
    P.obj("Mandible", Jw(loft([(0.0, 0.11, 0.07, 0, -0.1), (0.2, 0.08, 0.035, 0, -0.11), (0.45, 0.06, 0.03, 0, -0.11), (0.62, 0.045, 0.025, 0, -0.1), (0.66, 0.025, 0.02, 0, -0.1)], 16, sq=1.2)), "Belly")
    for k in range(6):
        a = math.radians(-50 + 20 * k)
        P.obj("Tooth", Jw(box((math.sin(a) * 0.04, 0.63 + math.cos(a) * 0.018, -0.07), (0.016, 0.018, 0.035))), "Belly", 0, False)
    P.obj("MouthFire", H(ball((0, 0.4, -0.11), (0.05, 0.2, 0.03), 10, 5)), "Glow")
    for s in (1, -1):   # the ears, laid back
        ear = ball((0, 0, 0), (0.035, 0.12, 0.02), 8, 4)
        xf(ear, Matrix.Rotation(math.radians(s * 25), 3, "Z") @ Matrix.Rotation(math.radians(25), 3, "X"), (s * 0.1, -0.1, 0.11))
        P.obj("Ear", H(ear), "Base")
    # the bridle: a silver-studded headstall over the bone, reins up to the rider's hand
    def strap(pts):
        pts = [V_(p) for p in pts]
        P.obj("Bridle", H(pipe(pts, [0.014] * len(pts), 5)), "Glass")
        for p in pts[1:-1:2]: P.obj("Stud", H(ball(tuple(p), (0.016,) * 3, 6, 3)), "Trim")
    strap([(math.sin(math.radians(a)) * 0.165, 0.02, math.cos(math.radians(a)) * 0.14 + 0.01) for a in range(-100, 101, 25)])
    strap([(math.sin(math.radians(a)) * 0.11, 0.48, math.cos(math.radians(a)) * 0.085 - 0.01) for a in range(-115, 116, 23)])
    for s in (1, -1):
        strap([(s * 0.16, 0.02, 0.0), (s * 0.14, 0.25, -0.03), (s * 0.11, 0.47, -0.05)])
        P.obj("Bit", H(xf(torus(0.03, 0.008, 0.0, 12, 4), Matrix.Rotation(math.radians(90), 3, "Y"), (s * 0.11, 0.5, -0.07))), "Trim")

    # ---- the tack: a ragged red blanket, a worn saddle with a horn and a coiled lariat, a cinch
    for s in (1, -1):
        blank = []
        for i in range(6):
            for j in range(4):
                y0, y1 = 0.3 - 0.11 * i, 0.3 - 0.11 * (i + 1)
                a0, a1 = 70 - 25 * j, 70 - 25 * (j + 1)
                q = [onbody((0, y, 0.25), (s * math.cos(math.radians(a)), 0, math.sin(math.radians(a))), 0.03 + 0.004 * j) for (y, a) in ((y0, a0), (y1, a0), (y1, a1), (y0, a1))]
                if j == 3: q[1] = q[1] + V_((0, 0, -0.06 * (i % 2))); q[2] = q[2] + V_((0, 0, -0.06 * (i % 2)))   # the ragged hem
                blank.append([tuple(p) for p in q])
        P.part("ClothBlanket", st_cloth(blank, 0.018), "Accent", (0, 0, 0), 0, True)
    sad = loft([(0.28, 0.12, 0.05, 0, 0.6), (0.16, 0.24, 0.08, 0, 0.58), (-0.02, 0.26, 0.07, 0, 0.56), (-0.18, 0.24, 0.1, 0, 0.6), (-0.24, 0.15, 0.1, 0, 0.66)], 18, sq=1.3)
    P.obj("Saddle", sad, "Glass", 0)
    P.obj("Horn", pipe([V_((0, 0.27, 0.62)), V_((0, 0.31, 0.74)), V_((0, 0.34, 0.78))], [0.04, 0.03, 0.05], 8), "Glass")
    for k in range(3):
        P.obj("Lariat", xf(torus(0.11 - 0.012 * k, 0.012, 0.0, 22, 4), Matrix.Rotation(math.radians(80), 3, "Y"), (0.2 + 0.02 * k, 0.24, 0.62)), "Belly")
    for s in (1, -1):
        P.obj("Cinch", pipe([onbody((0, 0.1, 0.25), (s * math.cos(math.radians(a)), 0, math.sin(math.radians(a))), 0.035) for a in range(30, -91, -20)], [0.024] * 7, 5), "Glass")

    # ---- the rider: a skeleton in a long black duster
    PEL = V_((0, 0.06, 0.74)); CH = V_((0, 0.12, 1.18)); NK = V_((0, 0.16, 1.36))
    coat = st_loft(bez(NK + V_((0, 0, -0.06)), CH, CH + V_((0, -0.04, -0.25)), PEL + V_((0, -0.02, -0.02)), 8),
                   [0.12, 0.2, 0.24, 0.25, 0.25, 0.24, 0.23, 0.22, 0.22], [0.12, 0.16, 0.18, 0.18, 0.18, 0.17, 0.17, 0.16, 0.16],
                   [0.12, 0.16, 0.18, 0.18, 0.18, 0.17, 0.17, 0.16, 0.16], spine_frames(bez(NK + V_((0, 0, -0.06)), CH, CH + V_((0, -0.04, -0.25)), PEL + V_((0, -0.02, -0.02)), 8)))
    P.obj("Duster", coat, "Dark", 0)
    for k in range(5):   # the lapels and the buttons of the duster
        P.obj("Button", ball((0.05, 0.31 - 0.01 * k, 1.12 - 0.09 * k), (0.016,) * 3, 6, 3), "Trim")
    # the shoulder cape and the coat tails torn into rags, streaming back over the quarters
    cape = []
    for i in range(10):
        a0, a1 = math.radians(-120 + 24 * i), math.radians(-120 + 24 * (i + 1))
        for j in range(3):
            r0, r1 = 0.2 + 0.07 * j, 0.2 + 0.07 * (j + 1)
            q = [(math.sin(a) * r, 0.14 + math.cos(a) * r * 0.85, 1.3 - 0.07 * (r - 0.2) / 0.07) for (a, r) in ((a0, r0), (a1, r0), (a1, r1), (a0, r1))]
            cape.append(q)
    P.part("ClothCape", st_cloth(cape, 0.02), "Dark", (0, 0, 0), 0, True)
    tails = []
    for s in (1, -1):
        for i in range(5):
            x0, x1 = s * (0.04 + 0.05 * i), s * (0.04 + 0.05 * (i + 1))
            for j in range(6):
                v0, v1 = j / 6, (j + 1) / 6
                def tp(x, v, i=i):
                    tip = 0.08 * (i % 2) if v > 0.99 else 0.0
                    return (x * (1 + 1.6 * v), -0.08 - 0.75 * v - tip, 0.78 - 0.28 * v + 0.06 * math.sin(v * 5 + i))
                q = [tp(x0, v0), tp(x1, v0), tp(x1, v1), tp(x0, v1)]
                if s < 0: q = list(reversed(q))
                tails.append(q)
    P.part("ClothTails", st_cloth(tails, 0.02), "Dark", (0, 0, 0), 0, True)
    # the skull: green fire in the sockets, a grin of teeth, under a black cattleman's hat
    SK = V_((0, 0.2, 1.52))
    P.obj("Neckbones", pipe([NK, SK + V_((0, -0.04, -0.1))], [0.04, 0.035], 8), "Belly")
    P.obj("Bandana", torus(0.085, 0.04, NK.z + 0.02, 18, 6), "Accent"); P.parts[-1].data.transform(Matrix.Translation((0, NK.y, 0)))
    P.obj("BandanaTip", st_cloth([[tuple(NK + V_((-0.08, 0.08, 0.02))), tuple(NK + V_((0.08, 0.08, 0.02))), tuple(NK + V_((0.0, 0.14, -0.13)))]], 0.015), "Accent")
    P.obj("Cranium", ball(tuple(SK + V_((0, -0.02, 0.04))), (0.14, 0.16, 0.14), 18, 9), "Belly")
    P.obj("Face", ball(tuple(SK + V_((0, 0.06, -0.04))), (0.12, 0.11, 0.11), 16, 8), "Belly")
    for s in (1, -1):
        e = SK + V_((s * 0.055, 0.15, 0.0))
        P.obj("Socket", ball(tuple(e), (0.045, 0.03, 0.04), 10, 5), "Dark")
        P.obj("EyeFire", ball(tuple(e + V_((0, 0.012, -0.004))), (0.018, 0.018, 0.018), 8, 4), "Glow")
        P.obj("Brow", pipe([SK + V_((s * 0.015, 0.165, 0.055)), SK + V_((s * 0.06, 0.16, 0.06)), SK + V_((s * 0.11, 0.13, 0.07))], [0.016, 0.02, 0.014], 6), "Belly")
        P.obj("Cheek", ball(tuple(SK + V_((s * 0.085, 0.12, -0.06))), (0.035, 0.04, 0.03), 8, 4), "Belly")
    P.obj("NoseHole", oriented_ball(SK + V_((0, 0.175, -0.04)), (0.02, 0.01, 0.025), V_((1, 0, 0)), V_((0, 1, 0)), V_((0, 0, 1)), 6, 3), "Dark")
    P.obj("Grin", oriented_ball(SK + V_((0, 0.15, -0.105)), (0.075, 0.02, 0.022), V_((1, 0, 0)), V_((0, 1, 0)), V_((0, 0, 1)), 10, 4), "Dark")
    for k in range(8):
        x = -0.06 + 0.12 * k / 7
        P.obj("Tooth", box(tuple(SK + V_((x, 0.165 - 0.25 * x * x, -0.105))), (0.013, 0.012, 0.03)), "Belly", 0, False)
    P.obj("Jaw", ball(tuple(SK + V_((0, 0.09, -0.14))), (0.09, 0.08, 0.04), 12, 5), "Belly")
    stetson(P, SK + V_((0, -0.02, 0.1)), 0.68, math.radians(6), "Dark", "Glass", "Trim")
    # the arms: the right aims a revolver at you, the left holds the reins; bone hands from the sleeves
    for s in (1, -1):
        sh = CH + V_((s * 0.22, 0.0, 0.1))
        if s > 0: el = sh + V_((0.08, 0.2, -0.12)); wr = el + V_((-0.04, 0.3, 0.06))
        else: el = sh + V_((-0.08, 0.18, -0.22)); wr = el + V_((0.05, 0.25, -0.05))
        P.obj("Sleeve", pipe([sh, el, wr - (wr - el).normalized() * 0.04], [0.085, 0.07, 0.08], 10), "Dark")
        P.obj("Cuff", pipe([wr - (wr - el).normalized() * 0.06, wr - (wr - el).normalized() * 0.02], [0.085, 0.085], 10), "Dark")
        P.obj("Hand", ball(tuple(wr + (wr - el).normalized() * 0.04), (0.045, 0.06, 0.04), 8, 4), "Belly")
        for k in range(4):   # bone fingers
            q = wr + (wr - el).normalized() * 0.08 + V_((s * (-0.03 + 0.02 * k), 0, -0.01))
            P.obj("Finger", pipe([q, q + V_((0, 0.03, -0.03)), q + V_((-s * 0.01, 0.0, -0.06))], [0.011, 0.01, 0.008], 5), "Belly")
        if s > 0: muzzle = revolver(P, wr + V_((0, 0.06, -0.01)), (0, 1, 0.08), (0, -0.08, 1))
        else:
            for t_ in (1, -1):   # the reins from his hand down to the bit
                P.obj("Rein", pipe(bez(wr, wr + V_((0, 0.15, -0.15)), hpt((t_ * 0.11, 0.35, 0.0)), hpt((t_ * 0.11, 0.5, -0.07)), 8), [0.009] * 9, 4), "Glass")
    # the gun belt with silver cartridges, the legs down the saddle to the stirrups, boots and silver spurs
    belt = torus(0.24, 0.035, 0.0, 30, 5)
    for v in belt.verts: v.co.y = v.co.y * 0.75 + PEL.y; v.co.z += PEL.z + 0.08
    P.obj("GunBelt", belt, "Glass")
    for k in range(12):
        a = math.radians(-150 + 300 * k / 11)
        P.obj("Cartridge", pipe([V_((math.sin(a) * 0.27, PEL.y + math.cos(a) * 0.2, PEL.z + 0.05)), V_((math.sin(a) * 0.27, PEL.y + math.cos(a) * 0.2, PEL.z + 0.11))], [0.013, 0.013], 5), "Trim")
    for s in (1, -1):
        hip = PEL + V_((s * 0.14, 0.08, 0.0)); kn = hip + V_((s * 0.16, 0.22, -0.1)); ank = kn + V_((s * 0.04, -0.02, -0.38))
        P.obj("Thigh", pipe([hip, kn], [0.08, 0.07], 10), "Glass")
        P.obj("Boot", pipe([kn, ank], [0.07, 0.065], 10), "Dark")
        P.obj("BootFoot", oriented_ball(ank + V_((0, 0.05, -0.03)), (0.06, 0.11, 0.045), V_((1, 0, 0)), V_((0, 1, 0)), V_((0, 0, 1)), 10, 5), "Dark")
        P.obj("Stirrup", xf(torus(0.07, 0.012, 0.0, 14, 4), Matrix.Rotation(math.radians(90), 3, "Y"), tuple(ank + V_((0, 0.03, -0.06)))), "Trim")
        P.obj("StirrupLeather", pipe([V_((s * 0.26, 0.05, 0.62)), ank + V_((0, 0.03, 0.0))], [0.014, 0.014], 4), "Glass")
        sp_ = ank + V_((s * 0.0, -0.08, -0.01))
        P.obj("Spur", pipe([sp_, sp_ + V_((0, -0.07, 0))], [0.008, 0.008], 4), "Trim")
        rc = sp_ + V_((0, -0.09, 0))
        for k in range(8):   # the rowel: a star of eight points
            a = 2 * math.pi * k / 8
            P.obj("Rowel", cone(rc, rc + V_((0, math.cos(a) * 0.05, math.sin(a) * 0.05)), 0.008, 3), "Trim", 0, False)

    # ---- the storm under his hooves: a churning ring of black cloud, forks of green lightning hanging from it
    CC = V_((0, 0.0, -1.12)); hub = tuple(CC)
    for ring, (R, n_, sz) in enumerate(((0.82, 10, 0.36), (0.42, 6, 0.38), (0.0, 1, 0.42))):   # big puffs overlapping into one storm mass
        for k in range(n_):
            a = 2 * math.pi * (k + 0.5 * ring) / n_
            big = 1.0 if k % 2 == 0 else 0.82
            c = CC + V_((math.cos(a) * R, math.sin(a) * R * 0.9, 0.04 * big + 0.03 * ring))
            P.part("SpinCloud", ball(tuple(c), (sz * big, sz * big, sz * big * 0.62), 14, 7), lambda cc, nn: "Dark" if nn.z < -0.35 else "Base", hub)
            P.part("SpinCloud", ball(tuple(c + V_((math.cos(a) * sz * 0.2, math.sin(a) * sz * 0.2, sz * 0.32))), (sz * 0.58 * big,) * 3, 12, 6), "Base", hub)
    for k in range(3):
        a = 2 * math.pi * k / 3 + 0.5
        top = CC + V_((math.cos(a) * 0.7, math.sin(a) * 0.63, -0.16))
        bolt = zigzag(top, top + V_((math.cos(a) * 0.2, math.sin(a) * 0.2, -0.7)), 4, 0.07, (math.cos(a + 1.57), math.sin(a + 1.57), 0))
        P.part("SpinCloud", pipe(bolt, [0.03, 0.035, 0.03, 0.022, 0.0], 5), "Glow", hub)
    P.part("Muzzle", ball(tuple(muzzle), (0.025, 0.02, 0.025), 8, 4), "Glow", tuple(muzzle))
    return P


def glow_strength(P, k, slot="_Glow"):
    for m in P.mats:
        if m.name.endswith(slot):
            next(x for x in m.node_tree.nodes if x.type == "BSDF_PRINCIPLED").inputs["Emission Strength"].default_value = k


def AB_pal(**over):
    p = {"Base": ((0.5, 0.3, 0.15), 0.4), "Belly": ((0.92, 0.86, 0.72), 0.35), "Accent": ((0.7, 0.12, 0.07), 0.5), "Trim": ((0.98, 0.74, 0.2), 0.7),
         "Glass": ((0.1, 0.6, 0.6), 0.6), "Dark": ((0.05, 0.04, 0.03), 0.4), "Glow": ((1.0, 0.7, 0.25), 0.5), "Metal": ((0.4, 0.4, 0.42), 0.6), "Lamp": ((1.0, 0.85, 0.45), 0.8)}
    p.update(over); return p


BOSSES = [("thunderbird", W2_thunderbird), ("sheriff", W2_sheriff), ("rattler2", W2_rattler), ("scorpion", W2_scorpion), ("ghostrider", W2_ghostrider)]

if __name__ == "__main__":
    os.makedirs(AB.OUT, exist_ok=True)
    for bid, fn in BOSSES:
        if ONLY and bid not in ONLY: continue
        fn().finish()
    print("DONE")
