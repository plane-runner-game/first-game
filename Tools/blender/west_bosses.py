# Sky Squad, the wild west's five bosses (2026-10-11: "the rest of the bosses for the maps that don't have them yet"): the thunderbird, the
# sheriff robot, the rattlesnake, the outlaw zeppelin and the gold mine mesa. Built from code like the other worlds' bosses (alien_bosses.py
# lends its Boss class and shapes).
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
    """The thunderbird of the plains: a great eagle of storm-blue feathers painted in red, gold and white bands, lightning zigzags glowing
    across its broad wings, a hooked golden beak, a crest of long plumes, a fanned tail, and a bolt of lightning gripped in its talons."""
    P = Boss("thunderbird", {"Base": ((0.10, 0.26, 0.52), 0.5), "Belly": ((0.96, 0.92, 0.82), 0.35), "Accent": RED, "Trim": GOLD,
                             "Glass": ((0.12, 0.70, 0.66), 0.6), "Dark": ((0.04, 0.05, 0.08), 0.5), "Glow": ((1.0, 0.72, 0.08), 0.5),
                             "Metal": ((0.6, 0.6, 0.6), 0.6), "Lamp": ((1.0, 0.85, 0.25), 0.8)})
    P.obj("Body", ball((0, 0.0, 0.0), (0.55, 1.0, 0.48), 16, 8), lambda c, n: "Belly" if n.z < -0.35 else ("Accent" if abs(c.y - 0.35) < 0.08 else "Base"), 1)
    P.obj("Chest", ball((0, 0.55, -0.05), (0.34, 0.35, 0.33), 12, 6), lambda c, n: "Belly" if n.z < 0.2 else "Base", 1)
    # the head
    P.obj("Head", ball((0, 1.0, 0.32), (0.3, 0.34, 0.28), 14, 7), lambda c, n: "Belly" if n.z < -0.5 else "Base", 1)
    P.obj("Mask", ball((0, 1.05, 0.38), (0.31, 0.26, 0.12), 12, 5), "Belly", 1)
    P.obj("Beak", hull([(0.13, 1.22, 0.42), (-0.13, 1.22, 0.42), (0.12, 1.2, 0.2), (-0.12, 1.2, 0.2), (0.05, 1.55, 0.38), (-0.05, 1.55, 0.38),
                        (0.0, 1.68, 0.28), (0.0, 1.62, 0.1), (0.0, 1.5, 0.18)]), "Trim", 0, False)
    for s in (1, -1):
        P.obj("Eye", ball((s * 0.17, 1.18, 0.45), (0.06, 0.06, 0.06), 8, 4), "Lamp")
        P.obj("Pupil", ball((s * 0.2, 1.21, 0.45), (0.03, 0.03, 0.03), 6, 3), "Dark")
        P.obj("Brow", hull([(s * 0.06, 1.2, 0.55), (s * 0.3, 1.1, 0.6), (s * 0.28, 1.05, 0.52), (s * 0.08, 1.18, 0.5)]), "Dark", 0, False)
    for k in range(7):   # the crest of plumes sweeping back
        a = math.radians(-36 + k * 12); col = ("Accent", "Trim", "Belly", "Accent", "Belly", "Trim", "Accent")[k]
        p0 = Vector((math.sin(a) * 0.12, 0.95, 0.52))
        P.obj("Plume", pipe(bez(p0, p0 + Vector((math.sin(a) * 0.15, -0.2, 0.35)), p0 + Vector((math.sin(a) * 0.35, -0.6, 0.45)), p0 + Vector((math.sin(a) * 0.45, -0.95, 0.3 - 0.04 * abs(k - 3))), 6),
                                [0.05, 0.07, 0.07, 0.06, 0.04, 0.02, 0.0], 6), col)
    # the wings: storm-blue with red, gold and white bands, a glowing lightning zigzag along each
    def zig(x): t = (x * 1.4) % 1.0; return -0.25 + 0.45 * (t * 2 if t < 0.5 else 2 - t * 2)
    for s in (1, -1):
        name = "FlapR" if s > 0 else "FlapL"
        hub = (s * 0.36, 0.1, 0.2)
        keys = [(0.3, 0.75, -0.75, 0.2, 0.18), (0.9, 0.85, -1.05, 0.15, 0.28), (1.6, 0.8, -1.1, 0.11, 0.38), (2.2, 0.6, -0.95, 0.07, 0.46), (2.5, 0.3, -0.7, 0.04, 0.5)]
        bm = sweep([(x, airfoil(le, te, th, z)) for (x, le, te, th, z) in fine(keys)], "x")
        if s < 0: bm = mirror_x(bm)
        def wpaint(c, n):
            x = abs(c.x)
            if n.z < -0.3: return "Belly"
            if abs(c.y - zig(x)) < 0.1 and 0.5 < x < 2.3: return "Glow"
            if c.y > 0.5: return "Trim"
            if c.y > 0.32: return "Accent"
            if c.y < -0.7: return "Belly"
            if c.y < -0.55: return "Dark"
            return "Base"
        P.part(name, bm, wpaint, hub, 0)
        for k in range(6):   # the long flight feathers at the tip, spread like fingers
            a = math.radians(10 - k * 16); r0 = Vector((s * 2.3, -0.2, 0.48))
            tip = r0 + Vector((s * math.cos(a) * 0.95, math.sin(a) * 0.95, 0.04))
            P.part(name, pipe([r0, r0 + (tip - r0) * 0.5, tip], [0.13, 0.11, 0.0], 6), lambda c, n, t=tip: "Dark" if (c - t).length < 0.35 else "Belly", hub, 0, False)
        for k in range(7):   # the trailing feathers
            x0 = 0.5 + k * 0.28
            P.part(name, cone((s * x0, -0.85, 0.2 + x0 * 0.1), (s * (x0 + 0.08), -1.25, 0.2 + x0 * 0.1), 0.12, 5), "Belly" if k % 2 else "Dark", hub, 0, False)
    # the fanned tail, banded
    hub = Vector((0, -0.85, 0.05))
    tips = [hub + Vector((math.sin(math.radians(a)) * 1.25, -math.cos(math.radians(a)) * 1.25, 0.05)) for a in range(-50, 51, 20)]
    P.obj("Tail", fan(hub, tips, 0.05, 0.25), lambda c, n: "Dark" if (c - hub).length > 1.0 else ("Belly" if (c - hub).length > 0.7 else ("Trim" if (c - hub).length > 0.5 else "Accent")), 0, False)
    # the legs and the lightning bolt in its talons
    for s in (1, -1):
        P.obj("Leg", pipe([(s * 0.18, 0.2, -0.3), (s * 0.2, 0.35, -0.6)], [0.09, 0.07], 8), "Belly")
        for k in (-1, 0, 1): P.obj("Talon", cone((s * 0.2, 0.35, -0.62), (s * 0.2 + k * 0.07, 0.48, -0.72), 0.03, 4), "Trim", 0, False)
    P.obj("Bolt", bolt([(-0.75, 0.42, -0.62), (-0.3, 0.4, -0.85), (-0.05, 0.4, -0.6), (0.3, 0.4, -0.85), (0.85, 0.42, -0.65)], 0.07, 0.06), "Glow", 0, False)
    P.part("Muzzle", ball((0, 1.66, 0.22), (0.06, 0.04, 0.05), 8, 4), "Glow", (0, 1.66, 0.22))
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


BOSSES = [("thunderbird", W_thunderbird), ("sheriff", W_sheriff), ("rattler", W_rattler), ("zeppelin", W_zeppelin), ("mesa", W_mesa)]

if __name__ == "__main__":
    os.makedirs(AB.OUT, exist_ok=True)
    for bid, fn in BOSSES:
        if ONLY and bid not in ONLY: continue
        fn().finish()
    print("DONE")
