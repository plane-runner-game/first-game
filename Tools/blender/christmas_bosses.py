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
def X_sleigh():
    """Santa's sleigh (2026-10-12, remade: "make it better"): a curvy red sleigh with gold scrollwork, a green velvet seat and long gold
    runners curling up into spirals at the front, a lantern on the dash; Santa riding high in it - red coat with white fur trim, black belt
    and gold buckle, a big white beard and moustache, rosy cheeks, gold spectacles, bushy brows, a floppy hat - one arm waving, the other
    holding the reins; a bulging sack behind him spilling presents and a candy cane; two reindeer out in front galloping through the air
    (the right one Rudolph, his nose glowing red), red harness hung with gold bells, big branching antlers; and a trail of magic stardust
    sparkling behind the runners."""
    P = Boss("sleigh", {"Base": ((0.46, 0.28, 0.15), 0.35), "Belly": ((0.97, 0.97, 0.96), 0.35), "Accent": ((0.80, 0.07, 0.07), 0.55),
                        "Trim": ((0.97, 0.76, 0.24), 0.85), "Glass": ((0.97, 0.76, 0.62), 0.3), "Dark": ((0.06, 0.05, 0.05), 0.45),
                        "Glow": ((1.0, 0.85, 0.45), 0.5), "Metal": ((0.10, 0.45, 0.22), 0.5), "Lamp": ((1.0, 0.12, 0.08), 0.8)})
    # the sleigh body: a curvy tub, red sides, green velvet on top, a gold band round its foot
    tub = loft([(-1.35, 0.62, 0.42, 0, 0.58), (-1.0, 0.68, 0.42, 0, 0.5), (-0.4, 0.68, 0.36, 0, 0.42), (0.2, 0.62, 0.3, 0, 0.38),
                (0.55, 0.52, 0.26, 0, 0.42), (0.78, 0.36, 0.2, 0, 0.55)], 20, True, True, 2.2)
    P.obj("Tub", tub, lambda c, n: "Metal" if n.z > 0.75 else ("Trim" if c.z < 0.2 else "Accent"), 1)
    P.obj("Dash", pipe(bez((0, 0.75, 0.55), (0, 0.95, 0.75), (0, 0.9, 1.0), (0, 0.72, 1.02), 6), [0.32, 0.3, 0.26, 0.2, 0.14, 0.1, 0.0], 12),
          lambda c, n: "Trim" if c.z > 0.92 else "Accent", 1)
    for s in (1, -1):
        # gold scrollwork along each side
        P.obj("Rail", pipe(bez((s * 0.66, -1.38, 0.95), (s * 0.72, -0.6, 0.85), (s * 0.68, 0.3, 0.72), (s * 0.5, 0.8, 0.78), 9), [0.04] * 10, 6), "Trim")
        for k in range(3):
            c = Vector((s * 0.7, -1.0 + k * 0.6, 0.45))
            sp = [c + Vector((0, math.cos(t) * 0.16 * (1 - t / 12), math.sin(t) * 0.16 * (1 - t / 12))) for t in [i * 0.55 for i in range(16)]]
            P.obj("Swirl", pipe(sp, [0.025] * 16, 5), "Trim")
        # runners: long gold rails, curling up into a spiral at the front
        run = [Vector((s * 0.5, y, -0.18)) for y in (-1.55, -1.0, -0.4, 0.2, 0.8)]
        cx, cz = 1.05, 0.1
        run += [Vector((s * 0.5, cx + math.sin(t) * 0.28 * (1 - t / 11), cz - math.cos(t) * 0.28 * (1 - t / 11))) for t in [i * 0.45 for i in range(1, 20)]]
        P.obj("Runner", pipe(run, [0.05] * len(run), 7), "Trim")
        P.obj("RunnerTail", pipe(bez((s * 0.5, -1.55, -0.18), (s * 0.5, -1.75, -0.18), (s * 0.5, -1.8, -0.05), (s * 0.5, -1.7, 0.05), 4), [0.05, 0.045, 0.04, 0.03, 0.0], 6), "Trim")
        for y in (-1.15, -0.45, 0.25):
            P.obj("RunnerPost", pipe([(s * 0.5, y, -0.16), (s * 0.55, y + 0.05, 0.25)], [0.035, 0.035], 6), "Trim")
        # shafts out to the reindeer
        P.obj("Shaft", pipe([(s * 0.45, 0.75, 0.3), (s * 0.62, 1.4, 0.22), (s * 0.72, 1.85, 0.3)], [0.03, 0.03, 0.025], 5), "Trim")
    # a lantern on the dash
    lc = Vector((0.62, 0.62, 0.95))
    P.obj("LanternPole", pipe([(0.6, 0.5, 0.6), lc], [0.025, 0.025], 5), "Dark")
    P.obj("LanternCap", lathe([(0.0, 0.0), (0.1, -0.05), (0.08, -0.08)], 8, "z", tuple(lc + Vector((0, 0, 0.25)))), "Dark")
    P.obj("Lantern", lathe([(0.08, -0.08), (0.08, -0.25), (0.0, -0.26)], 8, "z", tuple(lc + Vector((0, 0, 0.25)))), "Glow")
    # santa, riding high
    P.obj("Coat", ball((0, -0.3, 0.92), (0.44, 0.38, 0.46), 16, 8), lambda c, n: "Belly" if abs(c.x) < 0.06 and n.y > 0.3 else "Accent", 1)
    P.obj("CoatHem", xf(torus(0.42, 0.06, 0.0, 20, 5), None, (0, -0.3, 0.6)), "Belly")
    P.obj("Belt", xf(torus(0.44, 0.045, 0.0, 20, 4), None, (0, -0.3, 0.85)), "Dark")
    P.obj("Buckle", box((0, 0.11, 0.85), (0.16, 0.04, 0.12)), "Trim", 0, False)
    P.obj("BuckleHole", box((0, 0.125, 0.85), (0.08, 0.02, 0.06)), "Dark", 0, False)
    P.obj("Face", ball((0, -0.24, 1.5), (0.23, 0.22, 0.23), 14, 7), "Glass", 1)
    P.obj("Beard", ball((0, -0.08, 1.3), (0.27, 0.17, 0.3), 14, 7), "Belly", 1)
    P.obj("BeardTip", cone((0, -0.03, 1.15), (0, 0.02, 0.92), 0.17, 8), "Belly", 0, False)
    for s in (1, -1):
        P.obj("Moustache", pipe(bez((0, 0.0, 1.42), (s * 0.08, 0.04, 1.43), (s * 0.18, 0.02, 1.4), (s * 0.24, -0.02, 1.47), 5), [0.045, 0.05, 0.045, 0.035, 0.02, 0.0], 6), "Belly")
        P.obj("Cheek", ball((s * 0.13, -0.05, 1.48), (0.06, 0.03, 0.045), 8, 4), "Lamp")
        P.obj("Eye", ball((s * 0.08, -0.04, 1.57), (0.025, 0.015, 0.03), 6, 3), "Dark")
        P.obj("Specs", xf(torus(0.045, 0.01, 0.0, 12, 4), Matrix.Rotation(math.radians(90), 3, "X"), (s * 0.08, -0.02, 1.57)), "Trim")
        P.obj("Brow", ball((s * 0.09, -0.05, 1.64), (0.07, 0.03, 0.025), 8, 4), "Belly")
    P.obj("Nose", ball((0, 0.0, 1.5), (0.05, 0.04, 0.045), 8, 4), "Glass")
    P.obj("HatBrim", xf(torus(0.22, 0.06, 0.0, 18, 5), None, (0, -0.24, 1.66)), "Belly")
    P.obj("Hat", pipe(bez((0, -0.24, 1.66), (0, -0.25, 1.95), (0.15, -0.4, 2.05), (0.35, -0.5, 1.92), 6), [0.22, 0.19, 0.15, 0.11, 0.07, 0.05, 0.03], 10), "Accent")
    P.obj("Pompom", ball((0.37, -0.52, 1.88), (0.08, 0.08, 0.08), 8, 4), "Belly")
    # the waving arm (right) and the rein hand (left)
    P.obj("Arm", pipe([(0.38, -0.3, 1.1), (0.6, -0.2, 1.35), (0.65, -0.1, 1.7)], [0.1, 0.09, 0.08], 8), "Accent")
    P.obj("Cuff", xf(torus(0.08, 0.035, 0.0, 12, 4), None, (0.65, -0.1, 1.72)), "Belly")
    P.obj("Mitten", ball((0.66, -0.08, 1.82), (0.08, 0.06, 0.1), 8, 4), "Dark")
    P.obj("Thumb", ball((0.58, -0.06, 1.8), (0.035, 0.03, 0.05), 6, 3), "Dark")
    P.obj("Arm", pipe([(-0.38, -0.3, 1.1), (-0.5, -0.05, 0.95), (-0.3, 0.25, 0.95)], [0.1, 0.09, 0.08], 8), "Accent")
    P.obj("Cuff", xf(torus(0.08, 0.035, 0.0, 12, 4), Matrix.Rotation(math.radians(90), 3, "X"), (-0.3, 0.27, 0.95)), "Belly")
    rh = Vector((-0.28, 0.35, 0.95))
    P.obj("Mitten", ball(tuple(rh), (0.08, 0.08, 0.08), 8, 4), "Dark")
    # the sack behind him, spilling presents
    P.obj("Sack", ball((0, -1.0, 1.15), (0.5, 0.42, 0.6), 14, 7), lambda c, n: "Base" if speckle_sl(c) > 0.08 else "Dark", 1)
    P.obj("SackTie", xf(torus(0.13, 0.035, 0.0, 12, 4), None, (0, -1.0, 1.72)), "Trim")
    P.obj("SackTop", cone((0, -1.0, 1.72), (0.05, -1.05, 1.95), 0.18, 8), "Base", 0, False)
    present(P, (0.45, -1.15, 0.95), (0.3, 0.3, 0.3), "Metal", "Trim")
    present(P, (-0.45, -1.1, 0.92), (0.28, 0.28, 0.26), "Accent", "Belly")
    present(P, (-0.25, -0.75, 1.62), (0.22, 0.22, 0.2), "Trim", "Accent")
    present(P, (0.3, -0.7, 1.55), (0.2, 0.2, 0.2), "Belly", "Metal")
    present(P, (0.0, -1.35, 1.6), (0.24, 0.24, 0.24), "Glow", "Accent")
    cane = [Vector((-0.55, -0.85, 1.1)), Vector((-0.6, -0.85, 1.75))] + [Vector((-0.6 + 0.12 - 0.12 * math.cos(t), -0.85, 1.75 + 0.12 * math.sin(t))) for t in [math.pi * i / 6 for i in range(1, 7)]]
    P.obj("Cane", pipe(cane, [0.04] * len(cane), 8), lambda c, n: "Accent" if (c.z * 7 + c.x * 3) % 1.0 < 0.5 else "Belly")
    # two reindeer galloping out in front, the right one rudolph
    nose_tip = None
    for (rx, ry, lead) in ((0.72, 1.95, True), (-0.72, 1.95, False)):
        rz = 0.2
        P.obj("Deer", ball((rx, ry, rz), (0.26, 0.55, 0.27), 14, 7), lambda c, n: "Belly" if n.z < -0.55 else "Base", 1)
        P.obj("Chest", ball((rx, ry + 0.38, rz + 0.04), (0.22, 0.2, 0.24), 10, 5), "Belly", 1)
        P.obj("Neck", pipe([(rx, ry + 0.4, rz + 0.15), (rx, ry + 0.58, rz + 0.48), (rx, ry + 0.68, rz + 0.62)], [0.14, 0.12, 0.1], 8), "Base")
        hc = Vector((rx, ry + 0.78, rz + 0.68))
        P.obj("DeerHead", ball(tuple(hc), (0.13, 0.17, 0.13), 10, 5), "Base", 1)
        P.obj("Snout", pipe([hc + Vector((0, 0.08, -0.02)), hc + Vector((0, 0.28, -0.07))], [0.1, 0.075], 8), "Belly")
        nose = hc + Vector((0, 0.33, -0.07))
        P.obj("DeerNose", ball(tuple(nose), (0.06 if lead else 0.045,) * 3, 8, 4), "Lamp" if lead else "Dark")
        if lead: nose_tip = nose
        P.obj("Harness", xf(torus(0.2, 0.04, 0.0, 16, 4), Matrix.Rotation(math.radians(70), 3, "X"), (rx, ry + 0.32, rz + 0.1)), "Accent")
        for k in range(5):
            a = math.radians(-60 + 30 * k)
            P.obj("Bell", ball((rx + math.sin(a) * 0.2, ry + 0.42, rz + 0.1 - math.cos(a) * 0.17), (0.045, 0.045, 0.045), 6, 3), "Trim")
        P.obj("Saddle", ball((rx, ry - 0.05, rz + 0.25), (0.22, 0.2, 0.05), 10, 5), "Accent")
        P.obj("Tail", ball((rx, ry - 0.55, rz + 0.12), (0.07, 0.08, 0.1), 6, 3), "Belly")
        for s in (1, -1):
            P.obj("DeerEye", ball((rx + s * 0.08, ry + 0.88, rz + 0.75), (0.035, 0.03, 0.035), 6, 3), "Dark")
            P.obj("DeerGlint", ball((rx + s * 0.085, ry + 0.905, rz + 0.765), (0.01, 0.008, 0.01), 4, 2), "Belly")
            P.obj("DeerEar", cone((rx + s * 0.1, ry + 0.72, rz + 0.78), (rx + s * 0.28, ry + 0.66, rz + 0.84), 0.04, 5), "Base", 0, False)
            root = hc + Vector((s * 0.06, -0.05, 0.1))
            ant = bez(root, root + Vector((s * 0.12, -0.05, 0.25)), root + Vector((s * 0.3, -0.12, 0.45)), root + Vector((s * 0.42, -0.08, 0.62)), 6)
            P.obj("Antler", pipe(ant, [0.03, 0.028, 0.025, 0.022, 0.018, 0.012, 0.0], 5), "Trim")
            for t, d in ((2, (s * 0.02, 0.12, 0.16)), (4, (s * 0.1, 0.1, 0.14)), (3, (s * 0.12, -0.12, 0.08))):
                P.obj("Tine", cone(ant[t], ant[t] + Vector(d), 0.015, 4), "Trim", 0, False)
            # legs: the front pair stretched forward, the hind pair back - galloping
            for fy, k in ((0.3, 0), (-0.32, 1)):
                hip = Vector((rx + s * 0.14, ry + fy, rz - 0.08))
                name = "Sway%d" % ((0 if lead else 4) + k * 2 + (1 if s > 0 else 0))
                d1 = Vector((0, 0.22, -0.18)) if k == 0 else Vector((0, -0.2, -0.22))
                d2 = Vector((0, 0.2, -0.05)) if k == 0 else Vector((0, -0.3, -0.02))
                P.part(name, pipe([hip, hip + d1, hip + d1 + d2], [0.06, 0.045, 0.035], 6), "Base", tuple(hip))
                P.part(name, ball(tuple(hip + d1 + d2), (0.045, 0.06, 0.035), 6, 3), "Dark", tuple(hip))
        P.obj("Rein", pipe([rh, (rh + Vector((rx, ry + 0.35, rz + 0.25))) * 0.5 + Vector((0, 0, 0.12)), (rx, ry + 0.35, rz + 0.25)], [0.012, 0.012, 0.012], 4), "Accent")
    # a trail of magic stardust behind the runners
    for k in range(14):
        t = k / 13.0
        c = Vector((math.sin(t * 7) * 0.25 * t, -1.8 - t * 1.4, -0.15 - t * 0.35 + 0.08 * math.sin(t * 9)))
        r = 0.09 * (1 - t * 0.6)
        P.obj("Stardust", hull([c + Vector((r, 0, 0)), c - Vector((r, 0, 0)), c + Vector((0, 0, r * 1.8)), c - Vector((0, 0, r * 1.8)), c + Vector((0, r * 0.5, 0)), c - Vector((0, r * 0.5, 0))]),
              "Glow" if k % 3 else "Belly", 0, False)
        for s in (1, -1):
            q = c + Vector((s * (0.35 + 0.1 * t), 0.15, 0.05))
            P.obj("Sparkle", ball(tuple(q), (r * 0.5,) * 3, 6, 3), "Glow")
    P.part("Muzzle", ball(tuple(nose_tip + Vector((0, 0.06, 0))), (0.05, 0.04, 0.05), 8, 4), "Lamp", tuple(nose_tip + Vector((0, 0.06, 0))))
    return P

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
def X_snowman():
    """The snow giant (2026-10-12, remade: "make it better"): a hulking three-ball snowman flying under a propeller on his battered top hat -
    snowballs fringed with icicles, a string of christmas lights wound round his middle, a mischievous face: glowing ice-blue eyes in coal
    sockets under jagged coal brows, a long gnarled carrot nose, a wide crooked coal grin; a knitted striped scarf with flapping ends and
    tassels, holly on his hat with snow piled on the brim, big branchy arms - one fist hefting a glowing giant snowball, the other a
    candy-cane staff - coal buttons, and snowflakes whirling round him."""
    P = Boss("snowman", {"Base": ((0.36, 0.23, 0.12), 0.3), "Belly": ((0.96, 0.98, 1.0), 0.35), "Accent": ((1.0, 0.48, 0.08), 0.5),
                         "Trim": ((0.82, 0.08, 0.10), 0.5), "Glass": ((0.62, 0.80, 1.0), 0.85), "Dark": ((0.05, 0.05, 0.06), 0.55),
                         "Glow": ((0.45, 0.85, 1.0), 0.5), "Metal": ((0.08, 0.50, 0.24), 0.5), "Lamp": ((1.0, 0.82, 0.25), 0.8)})
    snow = lambda c, n: "Glass" if n.z < -0.55 else "Belly"
    balls = [((0, 0, -0.72), (0.82, 0.76, 0.7)), ((0, 0.05, 0.28), (0.62, 0.58, 0.55)), ((0, 0.08, 1.06), (0.46, 0.44, 0.44))]
    for nm, (c, r) in zip(("Bottom", "Middle", "Head"), balls):
        P.obj(nm, ball(c, r, 20, 10), snow, 1)
    rng = random.Random(5)
    for (c, r) in balls[:2]:   # icicles fringing the underside of the two lower balls
        for k in range(16):
            a = 2 * math.pi * (k + rng.uniform(-0.2, 0.2)) / 16
            b = Vector((math.sin(a) * r[0] * 0.82, c[1] + math.cos(a) * r[1] * 0.82, c[2] - r[2] * 0.5))
            P.obj("Icicle", cone(b, b + Vector((0, 0, -0.14 - 0.12 * rng.random())), 0.045, 5), "Glass", 0, False)
    for k, z in enumerate((0.55, 0.3, 0.05)):
        P.obj("Button", ball((0, 0.62, z), (0.075, 0.05, 0.075), 8, 4), "Dark")
    P.obj("Button", ball((0, 0.75, -0.55), (0.09, 0.05, 0.09), 8, 4), "Dark")
    # the string of christmas lights wound round his middle
    lights = [Vector((math.sin(t) * 0.64, 0.05 + math.cos(t) * 0.6, 0.12 + 0.28 * t / (2 * math.pi))) for t in [i * 2 * math.pi / 28 for i in range(29)]]
    P.obj("Wire", pipe(lights, [0.014] * 29, 4), "Metal")
    for i, p in enumerate(lights[1:-1:2]):
        out = Vector((p.x, p.y - 0.05, 0)).normalized()
        P.obj("Bulb", ball(tuple(p + out * 0.05), (0.045, 0.045, 0.06), 6, 3), ("Lamp", "Trim", "Glow", "Metal")[i % 4])
    # the face: glowing ice eyes in coal sockets, jagged brows, a crooked coal grin
    for s in (1, -1):
        P.obj("Socket", ball((s * 0.16, 0.45, 1.18), (0.1, 0.05, 0.1), 10, 5), "Dark")
        P.obj("Eye", ball((s * 0.16, 0.49, 1.18), (0.06, 0.03, 0.065), 8, 4), "Glow")
        P.obj("Glint", ball((s * 0.14, 0.51, 1.21), (0.018, 0.01, 0.018), 6, 3), "Belly")
        P.obj("Brow", hull([(s * 0.05, 0.48, 1.31), (s * 0.3, 0.42, 1.38), (s * 0.29, 0.4, 1.33), (s * 0.06, 0.46, 1.27), (s * 0.18, 0.47, 1.36)]), "Dark", 0, False)
        P.obj("Cheek", ball((s * 0.29, 0.42, 1.0), (0.07, 0.03, 0.05), 8, 4), "Trim")
    for k in range(9):   # the grin: coal lumps in a crooked smile, the two ends turned up
        t = (k - 4) / 4.0
        x = t * 0.26; z = 0.92 + 0.08 * t * t + 0.02 * t
        P.obj("Grin", hull([(x + dx, 0.505 - 0.08 * t * t + dy, z + dz) for dx, dy, dz in ((0.035, 0, 0.035), (-0.035, 0, 0.035), (0, 0.045, 0), (0.03, 0, -0.035), (-0.03, 0, -0.035), (0, -0.04, 0))]), "Dark", 0, False)
    carrot = [Vector((0, 0.42, 1.08)), Vector((0, 0.65, 1.06)), Vector((0.03, 0.88, 1.02)), Vector((0.08, 1.08, 1.0))]
    P.obj("Carrot", pipe(carrot, [0.09, 0.07, 0.045, 0.0], 8), lambda c, n: "Base" if ((c.y - 0.4) * 9) % 1.0 < 0.12 else "Accent")
    for k in range(3):
        P.obj("CarrotLeaf", cone((0, 0.42, 1.12), (0.06 * (k - 1), 0.36, 1.25), 0.025, 4), "Metal", 0, False)
    # the knitted scarf, its ends flapping in the wind
    P.obj("Scarf", torus(0.47, 0.1, 0.0, 26, 8), lambda c, n: "Trim" if (ang(Vector((c.x, c.y, 0))) * 3.5) % 1.0 < 0.5 else "Metal")
    P.parts[-1].data.transform(Matrix.Translation((0, 0.06, 0.72)))
    for s in (1, -1):
        root = Vector((s * 0.3, 0.35, 0.68))
        end = bez(root, root + Vector((s * 0.2, 0.0, -0.25)), root + Vector((s * 0.55, -0.35, -0.2)), root + Vector((s * 0.85, -0.7, 0.0)), 7)
        name = "SwayScarf%d" % (0 if s > 0 else 1)
        P.part(name, pipe(end, [0.09] * 7 + [0.08], 8), lambda c, n, root=root: "Trim" if ((c - root).length * 5) % 1.0 < 0.5 else "Metal", tuple(root))
        for k in range(4):
            q = end[-1] + Vector((0, 0, (k - 1.5) * 0.05))
            P.part(name, pipe([q, q + Vector((s * 0.05, -0.18, -0.03))], [0.02, 0.008], 4), "Belly", tuple(root))
    # branchy arms: a glowing giant snowball in one fist, a candy-cane staff in the other
    for s in (1, -1):
        sh = Vector((s * 0.55, 0.05, 0.42)); el = Vector((s * 1.0, 0.15, 0.7)); hd = Vector((s * 1.3, 0.3, 1.0))
        P.obj("Stick", pipe([sh, el, hd], [0.07, 0.055, 0.045], 7), "Base")
        P.obj("Twig", pipe([el, el + Vector((s * 0.1, 0.05, 0.3)), el + Vector((s * 0.2, 0.02, 0.4))], [0.03, 0.02, 0.008], 5), "Base")
        P.obj("Twig", pipe([sh + (el - sh) * 0.5, sh + (el - sh) * 0.5 + Vector((s * 0.05, -0.05, -0.25))], [0.025, 0.006], 5), "Base")
        P.obj("Mitten", ball(tuple(hd), (0.13, 0.12, 0.14), 10, 5), "Trim")
        P.obj("MittenCuff", ball(tuple(hd + Vector((-s * 0.08, -0.03, -0.08))), (0.1, 0.1, 0.06), 8, 4), "Belly")
    hb = Vector((1.3, 0.38, 1.33))
    P.obj("BigSnowball", ball(tuple(hb), (0.3, 0.3, 0.3), 14, 7), snow, 1)
    for k in range(7):   # frost spikes glowing on it
        a = 2 * math.pi * k / 7; d = Vector((math.sin(a), math.cos(a) * 0.6 + 0.4, math.cos(a * 2) * 0.5 + 0.3)).normalized()
        P.obj("Frost", cone(hb + d * 0.26, hb + d * 0.45, 0.06, 5), "Glow", 0, False)
    hl = Vector((-1.3, 0.35, 1.0))
    cane = [hl + Vector((0, 0, -1.0)), hl + Vector((0, 0, 0.5))] + [hl + Vector((-(0.18 - 0.18 * math.cos(t)), 0, 0.5 + 0.18 * math.sin(t))) for t in [math.pi * i / 8 for i in range(1, 9)]]
    P.obj("Cane", pipe(cane, [0.06] * len(cane), 10), lambda c, n: "Trim" if (c.z * 5 + c.x * 3) % 1.0 < 0.5 else "Belly")
    P.obj("CaneBow", ball(tuple(hl + Vector((0, 0.06, 0.35))), (0.12, 0.05, 0.08), 8, 4), "Metal")
    # the battered top hat: snow on the brim, a band with holly, the propeller
    P.obj("Brim", lathe([(0.0, 1.4), (0.5, 1.4), (0.52, 1.45), (0.0, 1.45)], 22, "z", (0, 0.08, 0)), "Dark")
    for k in range(9):
        a = 2 * math.pi * k / 9
        P.obj("BrimSnow", ball((math.sin(a) * 0.42, 0.08 + math.cos(a) * 0.42, 1.47), (0.12, 0.12, 0.05), 8, 4), "Belly")
    crown = lathe([(0.3, 1.45), (0.33, 1.98), (0.0, 1.98)], 20, "z", (0, 0.08, 0))
    for v in crown.verts:
        if v.co.z > 1.9: v.co.x += 0.04; v.co.z += 0.03 * v.co.x   # a little dented and askew
    P.obj("Crown", crown, lambda c, n: "Trim" if c.z < 1.58 else "Dark")
    P.obj("TopSnow", ball((0.03, 0.08, 2.0), (0.3, 0.3, 0.07), 12, 5), "Belly")
    for k in range(3):
        P.obj("Holly", ball((0.18 + 0.05 * k, 0.37, 1.53 + 0.04 * (k % 2)), (0.045, 0.035, 0.045), 6, 3), "Trim")
    for k in range(2):
        P.obj("HollyLeaf", hull([(0.22, 0.38, 1.53), (0.42 - 0.38 * k, 0.36, 1.62), (0.36 - 0.26 * k, 0.37, 1.48), (0.32 - 0.2 * k, 0.35, 1.57)]), "Metal", 0, False)
    P.obj("Mast", pipe([(0.03, 0.08, 2.0), (0.03, 0.08, 2.22)], [0.045, 0.045], 6), "Base")
    P.prop((0.03, 0.08, 2.24), 1.05, 3, axis="z", chord=0.2, blade="Trim", tip="Belly", spinner="Glow", spinner_len=0.1, name="Rotor")
    # snowflakes whirling round him
    for k in range(10):
        a = 2 * math.pi * k / 10
        c = Vector((math.sin(a) * 1.75, 0.05 + math.cos(a) * 1.45, 0.3 + 0.45 * math.sin(a * 2)))
        for j in range(3):
            d = Matrix.Rotation(math.radians(60 * j), 3, "Y") @ Vector((0, 0, 0.13))
            P.part("SpinSnow", pipe([c - d, c + d], [0.02, 0.02], 4), "Glow", (0, 0.05, 0.3))
    P.part("Muzzle", ball(tuple(hb + Vector((0, 0.3, 0))), (0.07, 0.04, 0.06), 8, 4), "Glow", tuple(hb + Vector((0, 0.3, 0))))
    return P

# ================================================================= 5. the grand christmas tree
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
def X_nutcracker():
    """A towering nutcracker king (2026-10-11, in place of the christmas express: "a new boss with features"): a red guard's coat with
    gold frogging, epaulettes and buttons, white trousers and black boots riding on jets of golden fire, a big wooden face with stern
    bushy brows, wide blue eyes, a great nose, a white moustache and a hinged jaw full of teeth that snaps, a white beard, an ermine-
    trimmed royal cape, a jewelled golden crown, and a sabre held high."""
    P = Boss("nutcracker", {"Base": ((0.78, 0.06, 0.08), 0.55), "Belly": ((0.97, 0.96, 0.93), 0.3), "Accent": ((0.93, 0.72, 0.55), 0.35),
                            "Trim": ((0.98, 0.76, 0.22), 0.85), "Glass": ((0.15, 0.40, 0.95), 0.9), "Dark": ((0.04, 0.04, 0.05), 0.6),
                            "Glow": ((1.0, 0.70, 0.25), 0.5), "Metal": ((0.80, 0.82, 0.86), 0.9), "Lamp": ((1.0, 0.85, 0.40), 0.8)})
    # boots, trousers, jets
    for s in (1, -1):
        x = s * 0.24
        P.obj("Leg", pipe([(x, 0, -0.45), (x, 0, -1.25)], [0.17, 0.15], 10), "Belly")
        P.obj("Boot", lathe([(0.0, -1.62), (0.19, -1.62), (0.2, -1.5), (0.17, -1.2), (0.18, -1.1), (0.0, -1.1)], 12, "z", (x, 0.02, 0)), lambda c, n: "Trim" if c.z > -1.16 else "Dark")
        P.obj("Jet", pipe([(x, 0, -1.6), (x, 0, -1.72), (x, 0, -1.95)], [0.17, 0.15, 0.0], 10), "Lamp")
        P.obj("JetCore", cone((x, 0, -1.6), (x, 0, -1.84), 0.1, 8), "Glow", 0, False)
    # the coat: a skirt flaring over the hips, a chest, a belt with a gold buckle
    P.obj("Coat", lathe([(0.0, -0.55), (0.62, -0.55), (0.58, -0.25), (0.5, 0.1), (0.54, 0.55), (0.42, 0.72), (0.0, 0.75)], 22, "z"),
          lambda c, n: "Belly" if c.z < -0.48 else "Base", 1)
    P.obj("Belt", torus(0.53, 0.05, -0.18, 24, 6), "Dark")
    P.obj("Buckle", box((0, 0.55, -0.18), (0.2, 0.05, 0.14)), "Trim", 0, False)
    for z in (0.05, 0.22, 0.39):    # gold frogging across the chest and buttons
        P.obj("Frog", bar((-0.3, 0.5, z), (0.3, 0.5, z), 0.045, 0.04), "Trim", 0, False)
        for s in (1, -1): P.obj("Button", ball((s * 0.32, 0.5, z), (0.05, 0.03, 0.05), 8, 4), "Trim")
    P.obj("Sash", bar((-0.42, 0.47, 0.6), (0.38, 0.5, -0.12), 0.13, 0.04), "Glass", 0, False)
    for s in (1, -1):    # epaulettes with fringes
        P.obj("Epaulette", ball((s * 0.55, 0.02, 0.68), (0.2, 0.18, 0.07), 12, 5), "Trim")
        for k in range(7):
            a = math.pi * k / 6
            P.obj("Fringe", pipe([(s * (0.55 + 0.18 * math.cos(a)), 0.18 * math.sin(a) * 0.9 + 0.02, 0.64), (s * (0.57 + 0.2 * math.cos(a)), 0.2 * math.sin(a) * 0.9 + 0.02, 0.5)], [0.02, 0.02], 4), "Trim")
    # the royal cape behind, purple velvet with ermine trim
    cape = [(sx * 0.55, -0.2, 0.7) for sx in (-1, 1)] + [(sx * 0.95, -0.55, -1.05) for sx in (-1, 1)] + [(sx * 0.5, -0.32, 0.7) for sx in (-1, 1)] + [(sx * 0.9, -0.68, -1.05) for sx in (-1, 1)]
    P.obj("Cape", hull(cape), "Glass", 0, False)
    for sx in (-1, 1): P.obj("CapeEdge", bar((sx * 0.55, -0.24, 0.66), (sx * 0.97, -0.6, -1.02), 0.06, 0.16), "Trim", 0, False)
    P.obj("Ermine", bar((-0.98, -0.62, -1.08), (0.98, -0.62, -1.08), 0.12, 0.16), lambda c, n: "Dark" if (c.x * 5) % 1.0 < 0.12 else "Belly", 0, False)
    P.obj("Collar", torus(0.42, 0.08, 0.72, 20, 6), "Belly")
    # the left arm: a fist on the hip holding a golden walnut
    P.obj("ArmL", pipe([(-0.6, 0.0, 0.6), (-0.82, 0.12, 0.15), (-0.62, 0.35, -0.12)], [0.14, 0.12, 0.11], 10), "Base")
    P.obj("Cuff", torus(0.11, 0.03, 0.0, 12, 4), "Trim"); P.parts[-1].data.transform(Matrix.Translation((-0.66, 0.31, -0.08)))
    P.obj("Glove", ball((-0.6, 0.4, -0.16), (0.12, 0.12, 0.12), 10, 5), "Belly")
    P.obj("Walnut", ball((-0.58, 0.55, -0.24), (0.13, 0.13, 0.12), 10, 5), "Trim", 1)
    # the right arm: a sabre raised high, swinging
    sh = (0.6, 0.0, 0.6)
    P.part("SwayArm", pipe([sh, (0.85, 0.12, 0.95), (0.85, 0.3, 1.35)], [0.14, 0.12, 0.11], 10), "Base", sh)
    P.part("SwayArm", ball((0.85, 0.32, 1.42), (0.12, 0.12, 0.12), 10, 5), "Belly", sh)
    P.part("SwayArm", bar((0.7, 0.34, 1.45), (1.0, 0.34, 1.45), 0.05, 0.06), "Trim", sh)
    P.part("SwayArm", bar((0.85, 0.34, 1.5), (0.95, 0.38, 2.6), 0.09, 0.025), "Metal", sh)
    P.part("SwayArm", cone((0.95, 0.38, 2.58), (0.97, 0.39, 2.78), 0.045, 4), "Metal", sh)
    # the head: a tall wooden block of a face
    P.obj("Head", lathe([(0.0, 0.75), (0.4, 0.78), (0.43, 1.0), (0.43, 1.55), (0.0, 1.58)], 20, "z"), "Accent", 1)
    for s in (1, -1):
        eye(P, (s * 0.16, 0.36, 1.3), 0.09, "Glass")
        P.obj("Brow", bar((s * 0.06, 0.43, 1.42), (s * 0.3, 0.4, 1.52), 0.07, 0.07), "Belly", 0, False)   # stern: low at the middle
        P.obj("Cheek", ball((s * 0.28, 0.33, 1.13), (0.08, 0.04, 0.06), 8, 4), "Base")
        P.obj("Hair", ball((s * 0.4, -0.08, 1.2), (0.12, 0.3, 0.32), 10, 5), "Belly", 1)
        P.obj("Moustache", pipe(bez((0, 0.47, 1.1), (s * 0.12, 0.5, 1.12), (s * 0.24, 0.48, 1.08), (s * 0.34, 0.42, 1.16), 6), [0.06, 0.06, 0.055, 0.05, 0.04, 0.03, 0.02], 8), "Belly")
    P.obj("Nose", ball((0, 0.47, 1.21), (0.07, 0.12, 0.09), 10, 5), "Accent")
    P.obj("Mouth", box((0, 0.38, 1.0), (0.32, 0.06, 0.12)), "Dark", 0, False)
    for k in range(6): P.obj("Tooth", box((-0.125 + k * 0.05, 0.42, 1.04), (0.04, 0.03, 0.05)), "Belly", 0, False)
    # the jaw on its hinge: it drops and snaps, a white beard hanging from it
    hinge = (0, 0.1, 1.02)
    P.part("SwayJaw", box((0, 0.3, 0.92), (0.4, 0.2, 0.12)), "Accent", hinge, 0, False)
    for k in range(6): P.part("SwayJaw", box((-0.125 + k * 0.05, 0.4, 0.98), (0.04, 0.03, 0.04)), "Belly", hinge, 0, False)
    P.part("SwayJaw", ball((0, 0.33, 0.75), (0.3, 0.14, 0.22), 12, 6), "Belly", hinge, 1)
    # the crown: a gold band with points, jewels, a red velvet cap and a cross-orb on top
    P.obj("Crown", lathe([(0.44, 1.55), (0.46, 1.78), (0.42, 1.78), (0.4, 1.58)], 22, "z"), "Trim")
    P.obj("Velvet", ball((0, 0, 1.72), (0.4, 0.4, 0.32), 14, 7), "Base")
    for k in range(8):
        a = 2 * math.pi * k / 8 + math.pi / 2
        p = Vector((math.cos(a) * 0.45, math.sin(a) * 0.45, 1.78))
        P.obj("CrownPoint", cone(tuple(p), tuple(p + Vector((0, 0, 0.28))), 0.08, 6), "Trim", 0, False)
        P.obj("Pearl", ball(tuple(p + Vector((0, 0, 0.3))), (0.04, 0.04, 0.04), 6, 3), "Belly")
        P.obj("Jewel", ball((math.cos(a) * 0.47, math.sin(a) * 0.47, 1.66), (0.05, 0.03, 0.05), 8, 4), ("Glass", "Base")[k % 2])
    P.obj("Orb", ball((0, 0, 2.08), (0.09, 0.09, 0.09), 10, 5), "Trim")
    P.obj("Cross", box((0, 0, 2.24), (0.035, 0.035, 0.18)), "Trim", 0, False)
    P.obj("Cross", box((0, 0, 2.25), (0.13, 0.035, 0.035)), "Trim", 0, False)
    P.part("Muzzle", ball((0, 0.46, 0.98), (0.06, 0.04, 0.05), 8, 4), "Glow", (0, 0.46, 0.98))
    return P


# ================================================================= 5 (new). the ice queen
def X_icequeen():
    """The last boss (2026-10-11, in place of the grand christmas tree): the snow queen of the north pole - a towering gown of ice flaring
    into crystal shards, a royal blue bodice laced with silver, a pale face with cold glowing eyes under imperious brows, silver hair in a
    long braid, a crown of ice spires around a glowing jewel, a high collar of icicles, great crystal wings that beat, a snowflake sceptre
    raised in one hand, a frost orb in the other, and snowflakes circling her."""
    P = Boss("icequeen", {"Base": ((0.10, 0.22, 0.70), 0.65), "Belly": ((0.96, 0.98, 1.0), 0.4), "Accent": ((0.86, 0.90, 0.98), 0.35),
                          "Trim": ((0.98, 0.84, 0.45), 0.9), "Glass": ((0.55, 0.82, 1.0), 0.95), "Dark": ((0.04, 0.06, 0.18), 0.5),
                          "Glow": ((0.35, 0.90, 1.0), 0.5), "Metal": ((0.75, 0.80, 0.92), 0.9), "Lamp": ((0.70, 0.95, 1.0), 0.8)})
    # the gown: a bell of ice, white frost at the waist turning to blue ice at the hem, a scalloped skirt of shards
    P.obj("Gown", lathe([(0.0, -1.2), (1.0, -1.15), (0.85, -0.75), (0.55, -0.3), (0.32, 0.0), (0.27, 0.12), (0.0, 0.12)], 28, "z"),
          lambda c, n: "Glass" if c.z < -0.55 else ("Belly" if c.z < -0.1 else "Base"), 1)
    P.obj("HemBand", torus(0.98, 0.045, -1.13, 32, 6), "Trim")
    P.obj("WaistBand", torus(0.31, 0.04, 0.05, 20, 5), "Trim")
    for k in range(14):
        a = 2 * math.pi * k / 14
        b = Vector((math.cos(a) * 0.95, math.sin(a) * 0.95, -1.1))
        P.obj("HemShard", cone(tuple(b + Vector((0, 0, 0.25))), tuple(b + Vector((math.cos(a) * 0.3, math.sin(a) * 0.3, -0.32 - 0.12 * (k % 2)))), 0.12, 4), "Glass", 0, False)
    for k in range(8):    # an overskirt of ice petals falling from the waist
        a = 2 * math.pi * k / 8 + math.pi / 8
        d = Vector((math.cos(a), math.sin(a), 0))
        top = d * 0.32 + Vector((0, 0, 0.02)); bot = d * 0.86 + Vector((0, 0, -0.78)); mid = (top + bot) * 0.5 + d * 0.06
        side = Vector((-math.sin(a), math.cos(a), 0)) * 0.24
        P.obj("Petal", hull([tuple(top), tuple(bot), tuple(mid + side), tuple(mid - side), tuple(mid + d * 0.05), tuple(top + d * 0.03)]), "Glass", 0, False)
        P.obj("PetalVein", bar(tuple(top + d * 0.04), tuple(bot + d * 0.03), 0.025, 0.02, up=tuple(d)), "Trim", 0, False)
    # the bodice
    P.obj("Bodice", lathe([(0.0, 0.1), (0.28, 0.1), (0.33, 0.35), (0.3, 0.6), (0.16, 0.72), (0.0, 0.74)], 20, "z"), "Base", 1)
    for sx in (-1, 1): P.obj("Vee", bar((sx * 0.25, 0.25, 0.6), (0, 0.32, 0.18), 0.04, 0.03), "Trim", 0, False)
    P.obj("Brooch", ball((0, 0.3, 0.62), (0.07, 0.04, 0.08), 10, 5), "Lamp")
    P.obj("Neck", pipe([(0, 0, 0.7), (0, 0.02, 0.86)], [0.08, 0.07], 10), "Accent")
    # the high collar of icicles behind her head
    for k in range(11):
        a = math.radians(-100 + k * 20)
        base = Vector((math.sin(a) * 0.3, -0.12 - math.cos(a) * 0.12 + 0.12, 0.75))
        tip = base + Vector((math.sin(a) * 0.45, -0.18, 0.55 + 0.25 * math.cos(a)))
        P.obj("Collar", cone(tuple(base), tuple(tip), 0.07, 4), "Glass", 0, False)
    # the head and her face
    P.obj("Head", ball((0, 0.04, 1.1), (0.3, 0.29, 0.35), 16, 8), "Accent", 1)
    for s in (1, -1):
        eye(P, (s * 0.115, 0.28, 1.14), 0.07, "Glow", pupil="Dark")
        P.obj("Brow", bar((s * 0.04, 0.32, 1.23), (s * 0.2, 0.28, 1.29), 0.035, 0.03), "Dark", 0, False)
        P.obj("Lash", bar((s * 0.05, 0.33, 1.2), (s * 0.19, 0.3, 1.22), 0.02, 0.02), "Dark", 0, False)
        P.obj("HairSide", ball((s * 0.27, -0.03, 1.02), (0.12, 0.22, 0.36), 10, 5), "Belly", 1)
        P.obj("Blush", ball((s * 0.17, 0.27, 1.02), (0.05, 0.02, 0.03), 8, 4), "Glass")
    P.obj("Nose", ball((0, 0.33, 1.06), (0.03, 0.035, 0.045), 6, 3), "Accent")
    P.obj("Lips", ball((0, 0.31, 0.96), (0.07, 0.03, 0.025), 8, 4), "Base")
    P.obj("Hair", ball((0, -0.07, 1.18), (0.33, 0.3, 0.36), 14, 7), lambda c, n: "Accent" if n.y > 0.7 and c.z < 1.36 else "Belly", 1)
    P.obj("Braid", pipe(bez((0.15, -0.1, 0.95), (0.35, 0.05, 0.7), (0.3, 0.25, 0.4), (0.22, 0.32, 0.1), 7), [0.07, 0.07, 0.065, 0.06, 0.055, 0.05, 0.04, 0.02], 8),
          lambda c, n: "Belly" if (c.z * 9) % 1.0 < 0.65 else "Trim")
    # the crown of ice spires around a glowing jewel
    P.obj("Circlet", torus(0.29, 0.03, 1.4, 20, 5), "Trim")
    for k in range(9):
        a = math.radians(-80 + k * 20)
        h = 0.75 - abs(k - 4) * 0.12
        b = Vector((math.sin(a) * 0.28, math.cos(a) * 0.28 * 0.6, 1.4))
        P.obj("Spire", cone(tuple(b), tuple(b + Vector((math.sin(a) * 0.1, 0, h))), 0.06, 4), "Glass", 0, False)
    P.obj("CrownJewel", ball((0, 0.3, 1.47), (0.07, 0.04, 0.09), 10, 5), "Lamp")
    # the wings: great fans of crystal shards beating at her back
    for s, nm in ((1, "FlapR"), (-1, "FlapL")):
        hub = (s * 0.18, -0.25, 0.5)
        for k in range(6):
            a = math.radians(-25 + k * 22)
            L = 1.6 - abs(k - 2.2) * 0.18
            root = Vector(hub) + Vector((s * 0.05, 0, 0))
            tip = root + Vector((s * math.cos(a) * L, -0.25, math.sin(a) * L))
            mid = (root + tip) * 0.5; w = Vector((0, 0, 0.13)) if abs(math.sin(a)) < 0.6 else Vector((s * 0.13, 0, 0))
            P.part(nm, hull([tuple(root), tuple(tip), tuple(mid + w), tuple(mid - w), tuple(mid + Vector((0, 0.04, 0))), tuple(mid - Vector((0, 0.04, 0)))]), "Glass", hub, 0, False)
            P.part(nm, ball(tuple(tip), (0.05, 0.05, 0.05), 6, 3), "Lamp", hub)
    # the arms: the snowflake sceptre raised, the frost orb held out
    P.obj("ArmR", pipe([(0.3, 0, 0.62), (0.55, 0.12, 0.6), (0.66, 0.3, 0.95)], [0.08, 0.07, 0.06], 8), "Accent")
    P.obj("Sleeve", cone((0.3, 0, 0.62), (0.55, 0.12, 0.45), 0.12, 8), "Glass", 0, False)
    P.obj("Sceptre", pipe([(0.68, 0.32, 0.55), (0.68, 0.32, 1.75)], [0.03, 0.03], 6), "Trim")
    c = Vector((0.68, 0.34, 1.95))
    for k in range(6):   # the snowflake on top
        a = math.pi * k / 3
        d = Vector((math.cos(a), 0, math.sin(a)))
        P.obj("Flake", bar(tuple(c), tuple(c + d * 0.3), 0.045, 0.04), "Lamp", 0, False)
        for t in (0.15, 0.23):
            for q in (1, -1):
                e = Vector((math.cos(a + q * 0.8), 0, math.sin(a + q * 0.8)))
                P.obj("Flake", bar(tuple(c + d * t), tuple(c + d * t + e * 0.09), 0.03, 0.035), "Lamp", 0, False)
    P.obj("FlakeHeart", ball(tuple(c), (0.06, 0.04, 0.06), 8, 4), "Glow")
    P.obj("ArmL", pipe([(-0.3, 0, 0.62), (-0.6, 0.2, 0.5), (-0.75, 0.45, 0.42)], [0.08, 0.07, 0.06], 8), "Accent")
    P.obj("Sleeve", cone((-0.3, 0, 0.62), (-0.58, 0.2, 0.4), 0.12, 8), "Glass", 0, False)
    P.obj("Orb", ball((-0.78, 0.55, 0.55), (0.14, 0.14, 0.14), 14, 7), "Glow", 1)
    # snowflakes circling her
    for k in range(10):
        a = 2 * math.pi * k / 10
        p = Vector((math.cos(a) * 1.55, math.sin(a) * 1.55, -0.55 + 0.25 * math.sin(a * 3)))
        for j in range(3):
            b = math.pi * j / 3
            dd = Vector((math.cos(b), 0, math.sin(b))) * 0.12
            P.part("SpinFlakes", bar(tuple(p - dd), tuple(p + dd), 0.03, 0.03), "Lamp", (0, 0, -0.55))
    P.part("Muzzle", ball((-0.78, 0.7, 0.55), (0.06, 0.04, 0.05), 8, 4), "Glow", (-0.78, 0.7, 0.55))
    return P


# ================================================================= 3 (new). krampus (2026-10-12, in place of the frost crystal: "give me something impressive")
def X_krampus():
    """Krampus, the christmas beast: a towering shaggy black goat-demon with great curling ram horns ringed in gold, a red face with
    blazing yellow eyes, a wicked fanged grin and a long red tongue, a wicker basket on his back stuffed with a sack, heavy chains hung with
    golden bells draped round him, a birch switch in one claw and a swinging lantern in the other, goat legs on cloven hooves, a tufted
    tail, and snowflakes whirling round him."""
    P = Boss("krampus", {"Base": ((0.13, 0.10, 0.10), 0.2), "Belly": ((0.40, 0.30, 0.24), 0.25), "Accent": ((0.72, 0.10, 0.10), 0.45),
                         "Trim": ((1.0, 0.78, 0.26), 0.85), "Glass": ((0.95, 0.93, 0.85), 0.5), "Dark": ((0.03, 0.02, 0.02), 0.5),
                         "Glow": ((0.70, 0.95, 1.0), 0.5), "Metal": ((0.50, 0.50, 0.55), 0.75), "Lamp": ((1.0, 0.85, 0.20), 0.8)})
    rng = random.Random(11)
    fur = lambda c, n: "Belly" if n.y > 0.6 and abs(c.x) < 0.3 and c.z > 0.0 else "Base"
    # the hulking torso, hunched forward, and shag all over it
    P.obj("Torso", lathe([(0.0, -0.55), (0.5, -0.5), (0.62, -0.1), (0.78, 0.45), (0.85, 0.8), (0.55, 1.08), (0.0, 1.12)], 22, "z"), fur, 1)
    for k in range(70):
        a = rng.uniform(0, 2 * math.pi); z = rng.uniform(-0.45, 0.95)
        if math.cos(a) > 0.6 and 0.0 < z < 0.85: continue   # leave his chest
        r = 0.62 + 0.18 * (z + 0.45) / 1.4
        b = Vector((math.sin(a) * r, math.cos(a) * r, z))
        P.obj("Shag", cone(b, b + Vector((math.sin(a) * 0.16, math.cos(a) * 0.12, -0.18)), 0.09, 4), "Base", 0, False)
    # the head: a goat's long face, red and fierce
    HC = Vector((0, 0.42, 1.38))
    P.obj("Head", ball(tuple(HC), (0.42, 0.4, 0.42), 16, 8), "Base", 1)
    P.obj("Face", loft([(0.55, 0.32, 0.34, 0, 1.38), (0.75, 0.28, 0.3, 0, 1.3), (0.95, 0.2, 0.2, 0, 1.18), (1.08, 0.13, 0.12, 0, 1.1)], 14), "Accent", 1)
    P.obj("Snout", ball((0, 1.08, 1.12), (0.13, 0.08, 0.1), 10, 5), "Accent")
    for s in (1, -1):
        P.obj("Nostril", ball((s * 0.05, 1.15, 1.12), (0.025, 0.02, 0.02), 6, 3), "Dark")
        P.obj("Socket", ball((s * 0.17, 0.82, 1.45), (0.13, 0.07, 0.09), 10, 5), "Dark")
        P.obj("Eye", ball((s * 0.17, 0.86, 1.45), (0.1, 0.04, 0.065), 10, 5), "Lamp")
        P.obj("Pupil", ball((s * 0.17, 0.89, 1.45), (0.018, 0.02, 0.05), 6, 3), "Dark")
        P.obj("Brow", hull([(s * 0.03, 0.88, 1.56), (s * 0.34, 0.76, 1.66), (s * 0.34, 0.72, 1.6), (s * 0.05, 0.83, 1.5), (s * 0.2, 0.86, 1.64)]), "Dark", 0, False)
        P.obj("Ear", hull([(s * 0.35, 0.4, 1.45), (s * 0.4, 0.5, 1.4), (s * 0.8, 0.45, 1.25), (s * 0.4, 0.42, 1.3)]), "Accent", 0, False)
        # the great curling ram horns, ringed in gold
        h0 = HC + Vector((s * 0.22, 0.05, 0.32))
        pts = bez(h0, h0 + Vector((s * 0.35, -0.35, 0.55)), h0 + Vector((s * 1.0, -0.25, 0.35)), h0 + Vector((s * 0.95, 0.15, -0.15)), 10)
        pts += bez(pts[-1], pts[-1] + Vector((s * -0.05, 0.25, -0.25)), pts[-1] + Vector((s * -0.3, 0.3, -0.15)), pts[-1] + Vector((s * -0.32, 0.22, 0.05)), 5)[1:]
        hr = [0.15 - 0.15 * i / (len(pts) - 1) + 0.004 for i in range(len(pts))]; hr[-1] = 0.0
        P.obj("Horn", pipe(pts, hr, 10), "Glass", 1)
        for i in (2, 4, 6, 8, 10):
            t = (pts[i + 1] - pts[i - 1]).normalized()
            ring = torus(hr[i] * 1.1, 0.025, 0.0, 14, 4)
            q = t.to_track_quat("Z", "Y").to_matrix()
            for v in ring.verts: v.co = q @ v.co + pts[i]
            P.obj("HornRing", ring, "Trim")
    # the grin: wide, dark, fangs, and a long red tongue lolling out
    P.obj("Mouth", ball((0, 0.98, 1.0), (0.2, 0.08, 0.07), 14, 6), "Dark")
    P.obj("Tongue", pipe(bez((0, 1.0, 0.98), (0, 1.2, 0.95), (0.05, 1.3, 0.75), (0.0, 1.25, 0.55), 6), [0.06, 0.065, 0.06, 0.055, 0.045, 0.03, 0.0], 8), "Accent")
    for s in (1, -1):
        for k in range(3):
            x = s * (0.06 + k * 0.05)
            P.obj("Fang", cone((x, 1.02, 1.06), (x, 1.04, 0.95 - (0.04 if k == 1 else 0)), 0.025, 4), "Glass", 0, False)
    P.obj("Beard", cone((0, 0.85, 0.95), (0, 0.9, 0.55), 0.18, 7), "Base", 0, False)
    # heavy chains with golden bells, draped round his chest and hanging; the bells swing
    for k in range(18):
        t = k / 17
        a = math.radians(-70 + 140 * t)
        c = Vector((math.sin(a) * 0.82, math.cos(a) * 0.62 + 0.05, 0.75 - 0.55 * math.sin(math.pi * t)))
        link = torus(0.055, 0.016, 0.0, 10, 4)
        xf(link, Matrix.Rotation(math.radians(90 * (k % 2)), 3, "Y") @ Matrix.Rotation(a, 3, "Z"), tuple(c))
        P.obj("Chain", link, "Metal")
        if k % 4 == 2:
            P.part("SwayBell%d" % k, pipe([c, c + Vector((0, 0, -0.12))], [0.01, 0.01], 4), "Metal", tuple(c))
            P.part("SwayBell%d" % k, lathe([(0.0, -0.1), (0.06, -0.12), (0.09, -0.24), (0.11, -0.28), (0.0, -0.28)], 12, "z", tuple(c)), "Trim", tuple(c))
            P.part("SwayBell%d" % k, ball(tuple(c + Vector((0, 0, -0.3))), (0.03, 0.03, 0.03), 6, 3), "Dark", tuple(c))
    # the wicker basket on his back, a sack bulging out of it
    P.obj("Basket", lathe([(0.42, -0.5), (0.5, 0.3), (0.54, 0.35), (0.48, 0.35), (0.4, -0.45), (0.0, -0.45)], 16, "z", (0, -0.75, 0.55)),
          lambda c, n: "Belly" if (c.z * 9) % 1.0 < 0.5 else "Metal")
    P.obj("Sack", ball((0, -0.8, 1.15), (0.42, 0.4, 0.45), 14, 7), "Accent", 1)
    P.obj("SackTie", xf(torus(0.14, 0.03, 0.0, 12, 4), None, (0, -0.8, 1.55)), "Trim")
    for k in range(5):   # toys and birch twigs poking out of the sack
        a = 2 * math.pi * k / 5
        b = Vector((math.sin(a) * 0.12, -0.8 + math.cos(a) * 0.12, 1.55))
        P.obj("Twig", pipe([b, b + Vector((math.sin(a) * 0.25, math.cos(a) * 0.2, 0.55))], [0.02, 0.008], 4), "Belly")
    # arms: a birch switch in the right claw, a swinging lantern in the left
    for s in (1, -1):
        sh = Vector((s * 0.72, 0.15, 0.85))
        el = sh + Vector((s * 0.35, 0.25, -0.35)); wr = el + Vector((s * 0.05, 0.4, 0.05))
        P.obj("Arm", pipe([sh, el, wr], [0.22, 0.17, 0.13], 10), "Base", 1)
        P.obj("Hand", ball(tuple(wr + Vector((0, 0.1, 0))), (0.13, 0.13, 0.13), 10, 5), "Accent", 1)
        for k in range(4):
            x = (k - 1.5) * 0.06
            P.obj("Claw", cone(tuple(wr + Vector((x, 0.2, 0.0))), tuple(wr + Vector((x * 1.3, 0.32, -0.08))), 0.02, 4), "Glass", 0, False)
        for k in range(4):
            a = 2 * math.pi * k / 4
            b = sh + (el - sh) * 0.5 + Vector((math.sin(a) * 0.17, math.cos(a) * 0.12, 0))
            P.obj("ArmShag", cone(b, b + Vector((s * 0.12, -0.05, -0.18)), 0.07, 4), "Base", 0, False)
    hr_ = Vector((1.12, 1.0, 0.55)); hl = Vector((-1.12, 1.0, 0.55))
    for k in range(6):   # the birch switch: a bundle of twigs tied with a red ribbon
        a = 2 * math.pi * k / 6
        d = Vector((math.sin(a) * 0.12, 0.05, 1.0 + 0.1 * (k % 2)))
        P.obj("Switch", pipe([hr_ + Vector((0, 0, -0.25)), hr_ + Vector((math.sin(a) * 0.03, 0, 0.3)), hr_ + d], [0.025, 0.02, 0.008], 4), "Glass")
    P.obj("SwitchTie", xf(torus(0.06, 0.025, 0.0, 10, 4), None, tuple(hr_ + Vector((0, 0, 0.15)))), "Accent")
    lc = hl + Vector((0, 0.05, -0.25))
    P.part("SwayLantern", pipe([hl, lc], [0.012, 0.012], 4), "Metal", tuple(hl))
    P.part("SwayLantern", lathe([(0.0, 0.0), (0.12, -0.06), (0.1, -0.1)], 8, "z", tuple(lc)), "Dark", tuple(hl))
    P.part("SwayLantern", lathe([(0.1, -0.1), (0.1, -0.38), (0.0, -0.4)], 8, "z", tuple(lc)), "Lamp", tuple(hl))
    P.part("SwayLantern", lathe([(0.12, -0.38), (0.0, -0.44)], 8, "z", tuple(lc)), "Dark", tuple(hl))
    for k in range(4):
        a = 2 * math.pi * k / 4 + 0.4
        P.part("SwayLantern", pipe([lc + Vector((math.sin(a) * 0.11, math.cos(a) * 0.11, -0.08)), lc + Vector((math.sin(a) * 0.11, math.cos(a) * 0.11, -0.38))], [0.014, 0.014], 4), "Dark", tuple(hl))
    # goat legs on cloven hooves, kicking
    for s, k in ((1, 0), (-1, 1)):
        hip = Vector((s * 0.3, 0.0, -0.45))
        name = "Sway%d" % k
        thigh = hip + Vector((s * 0.05, 0.3, -0.35)); hock = thigh + Vector((0, -0.3, -0.35)); hoof = hock + Vector((0, 0.15, -0.3))
        P.part(name, pipe([hip, thigh, hock, hoof], [0.24, 0.18, 0.1, 0.08], 10), "Base", tuple(hip), 1)
        P.part(name, lathe([(0.11, 0.0), (0.12, -0.12), (0.0, -0.13)], 10, "z", tuple(hoof)), "Dark", tuple(hip))
        P.part(name, box(tuple(hoof + Vector((0, 0.08, -0.07))), (0.02, 0.12, 0.13)), "Base", tuple(hip), 0, False)
        for j in range(4):
            b = thigh + (hock - thigh) * (j / 4) + Vector((s * 0.12, 0, 0))
            P.part(name, cone(b, b + Vector((s * 0.12, -0.08, -0.16)), 0.07, 4), "Base", tuple(hip), 0, False)
    tail = bez((0, -0.45, -0.35), (0, -0.9, -0.5), (0.2, -1.2, -0.2), (0.15, -1.3, 0.1), 6)
    P.obj("Tail", pipe(tail, [0.06, 0.05, 0.045, 0.04, 0.035, 0.03, 0.0], 6), "Base")
    P.obj("TailTuft", ball(tuple(tail[-1]), (0.11, 0.11, 0.15), 8, 4), "Base")
    # snowflakes whirling round him
    for k in range(10):
        a = 2 * math.pi * k / 10
        c = Vector((math.sin(a) * 1.65, math.cos(a) * 1.5, 0.4 + 0.4 * math.sin(a * 2)))
        for j in range(3):
            d = Matrix.Rotation(math.radians(60 * j), 3, "Y") @ Vector((0, 0, 0.13))
            P.part("SpinSnow", pipe([c - d, c + d], [0.018, 0.018], 4), "Glow", (0, 0, 0.4))
    P.part("Muzzle", ball((0, 1.1, 1.0), (0.07, 0.04, 0.05), 8, 4), "Lamp", (0, 1.1, 1.0))
    return P

BOSSES = [("sleigh", X_sleigh), ("snowman", X_snowman), ("nutcracker", X_nutcracker), ("icequeen", X_icequeen), ("krampus", X_krampus)]

if __name__ == "__main__":
    os.makedirs(AB.OUT, exist_ok=True)
    for bid, fn in BOSSES:
        if ONLY and bid not in ONLY: continue
        fn().finish()
    print("DONE")
