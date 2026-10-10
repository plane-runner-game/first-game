# Sky Squad, the christmas village's five bosses (2026-10-10: "bosses for the christmas village"): the gingerbread zeppelin, santa's
# sleigh, the frost crystal, the snow giant and the grand christmas tree. Built from code like the other worlds' bosses (alien_bosses.py
# lends its Boss class and shapes).
# Run: blender -b -P Tools/blender/christmas_bosses.py -- <out dir> [export] [ids,comma,separated]
# Conventions as alien_bosses.py: +Y nose, +Z up, +X right; "Prop*" spin about the nose, "Rotor*" about up, "Flap*" rock about the nose axis,
# "Sway*" about the wing axis, "Spin*" turn slowly about up, "Roll*" turn slowly about the nose axis, "Cloth" stays still without the
# outline, "Muzzle" is where his shots leave from.
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


# ================================================================= 1. the gingerbread zeppelin
def X_zeppelin():
    """A gingerbread airship: a brown cookie envelope with white icing squiggles and gumdrops on top, a candy-striped gondola with lit
    windows, candy-cane fins, and red-and-white propellers on two engine pods."""
    P = Boss("zeppelin", {"Base": ((0.62, 0.36, 0.17), 0.3), "Belly": ((0.97, 0.96, 0.94), 0.5), "Accent": ((0.85, 0.10, 0.10), 0.5),
                          "Trim": ((0.95, 0.75, 0.25), 0.6), "Glass": ((0.35, 0.75, 0.95), 0.6), "Dark": ((0.10, 0.06, 0.04), 0.4),
                          "Glow": ((1.0, 0.82, 0.45), 0.5), "Metal": ((0.15, 0.62, 0.30), 0.5), "Lamp": ((1.0, 0.70, 0.30), 0.8)})
    def icing(c, n):
        a = math.atan2(c.x, c.z)
        if abs(((c.y * 1.6) % 1.0) - 0.5 + 0.08 * math.sin(a * 10)) < 0.045: return "Belly"
        return "Base"
    P.obj("Envelope", loft([(2.35, 0.1, 0.1, 0, 0.6), (2.05, 0.62, 0.62, 0, 0.6), (1.2, 0.95, 0.95, 0, 0.6), (-0.4, 0.98, 0.98, 0, 0.6),
                            (-1.6, 0.72, 0.72, 0, 0.6), (-2.3, 0.25, 0.25, 0, 0.6), (-2.45, 0.05, 0.05, 0, 0.6)], 22), icing, 1)
    P.obj("NoseCap", ball((0, 2.33, 0.6), (0.14, 0.08, 0.14), 10, 5), "Belly")
    rings = [(2.35, 0.1), (2.05, 0.62), (1.2, 0.95), (-0.4, 0.98), (-1.6, 0.72), (-2.3, 0.25)]
    def rad(y):
        for (y0, r0), (y1, r1) in zip(rings, rings[1:]):
            if y1 <= y <= y0: return r0 + (r1 - r0) * (y0 - y) / (y0 - y1)
        return 0.1
    for y in (1.75, 1.0, 0.25, -0.5, -1.25, -1.9):   # the icing: wavy white rings round the cookie
        pts = []
        for i in range(49):
            a = 2 * math.pi * i / 48; yy = y + 0.07 * math.sin(a * 8); r = rad(yy) + 0.015
            pts.append((math.sin(a) * r, yy, 0.6 + math.cos(a) * r))
        P.obj("Icing", pipe(pts, [0.035] * len(pts), 5, cap=False), "Belly")
    for k in range(9):   # gumdrops along the top
        y = 1.6 - k * 0.4
        r = 0.98 * max(0.3, 1 - ((y - 0.3) / 2.4) ** 2) ** 0.5
        P.obj("Gumdrop", lathe([(0.0, 0.0), (0.13, 0.0), (0.11, 0.1), (0.0, 0.16)], 10, "z", (0, y, 0.6 + r - 0.03)), ("Accent", "Metal", "Trim", "Glass")[k % 4])
    for s in (1, -1):   # the fins: candy-cane stripes
        P.obj("Fin", hull([(s * 0.35, -1.75, 0.6), (s * 0.35, -2.3, 0.6), (s * 1.2, -2.45, 0.6), (s * 1.1, -2.1, 0.6), (s * 0.35, -2.0, 0.65), (s * 0.35, -2.0, 0.55)]),
              lambda c, n: "Accent" if (c.x * 4 + c.y * 4) % 1.0 < 0.5 else "Belly", 0, False)
    P.obj("TopFin", hull([(0, -1.75, 1.0), (0, -2.3, 0.8), (0, -2.45, 1.65), (0, -2.15, 1.6), (0.05, -2.0, 1.0), (-0.05, -2.0, 1.0)]),
          lambda c, n: "Accent" if (c.z * 4 + c.y * 4) % 1.0 < 0.5 else "Belly", 0, False)
    # the gondola: a candy-striped car with lit windows, hung on struts
    P.obj("Gondola", loft([(1.0, 0.08, 0.08, 0, -0.55), (0.8, 0.32, 0.28, 0, -0.55), (-0.6, 0.32, 0.28, 0, -0.55), (-0.85, 0.08, 0.08, 0, -0.55)], 14, sq=1.8),
          lambda c, n: "Accent" if (c.y * 3.5) % 1.0 < 0.5 else "Belly", 1)
    for s in (1, -1):
        for k in range(4):
            P.obj("Window", box((s * 0.3, 0.55 - k * 0.35, -0.5), (0.03, 0.18, 0.13)), "Lamp", 0, False)
        for y in (0.6, -0.4):
            P.obj("Strut", pipe([(s * 0.2, y, -0.3), (s * 0.35, y, -0.05)], [0.025, 0.025], 5), "Dark")
        # the engine pods with candy propellers
        P.obj("Pylon", pipe([(s * 0.85, 0.2, 0.1), (s * 1.35, 0.25, -0.05)], [0.05, 0.05], 6), "Dark")
        P.obj("Pod", loft([(0.6, 0.08, 0.08, s * 1.4, -0.05), (0.45, 0.18, 0.18, s * 1.4, -0.05), (-0.2, 0.15, 0.15, s * 1.4, -0.05), (-0.4, 0.05, 0.05, s * 1.4, -0.05)], 12), "Metal", 1)
        P.prop((s * 1.4, 0.66, -0.05), 0.45, 3, blade="Accent", tip="Belly", spinner="Trim", spinner_len=0.12)
    P.part("Muzzle", ball((0, 2.42, 0.6), (0.08, 0.05, 0.08), 8, 4), "Glow", (0, 2.42, 0.6))
    return P


# ================================================================= 2. santa's sleigh
def X_sleigh():
    """Santa in his sleigh: a red sleigh with golden scroll runners, a bulging sack and a pile of presents, Santa in red with a white beard,
    pulled by two reindeer whose legs gallop through the air, the lead one's nose glowing red."""
    P = Boss("sleigh", {"Base": ((0.46, 0.28, 0.15), 0.35), "Belly": ((0.97, 0.97, 0.96), 0.35), "Accent": ((0.80, 0.07, 0.07), 0.5),
                        "Trim": ((0.95, 0.74, 0.24), 0.75), "Glass": ((0.95, 0.74, 0.60), 0.3), "Dark": ((0.06, 0.05, 0.05), 0.45),
                        "Glow": ((1.0, 0.80, 0.40), 0.5), "Metal": ((0.10, 0.45, 0.22), 0.5), "Lamp": ((1.0, 0.12, 0.08), 0.8)})
    # the sleigh
    P.obj("Sleigh", hull([(-0.55, -1.3, 0.0), (0.55, -1.3, 0.0), (-0.55, 0.3, 0.0), (0.55, 0.3, 0.0), (-0.6, -1.4, 0.55), (0.6, -1.4, 0.55),
                          (-0.55, 0.35, 0.3), (0.55, 0.35, 0.3), (-0.45, 0.55, 0.15), (0.45, 0.55, 0.15), (-0.6, -1.35, 0.75), (0.6, -1.35, 0.75)]),
          lambda c, n: "Trim" if c.z > 0.5 and n.z > 0.5 else "Accent", 0, False)
    for s in (1, -1):
        P.obj("Scroll", pipe(bez((s * 0.6, -1.4, 0.55), (s * 0.66, -1.0, 0.65), (s * 0.66, 0.1, 0.35), (s * 0.6, 0.55, 0.2), 6), [0.04] * 7, 6), "Trim")
        run = bez((s * 0.45, -1.4, -0.25), (s * 0.45, 0.3, -0.3), (s * 0.45, 1.1, -0.3), (s * 0.45, 1.25, 0.15), 8)
        P.obj("Runner", pipe(run, [0.04] * 9, 6), "Trim")
        for y in (-1.0, -0.2, 0.4):
            P.obj("RunnerPost", pipe([(s * 0.45, y, -0.26), (s * 0.45, y, 0.02)], [0.03, 0.03], 5), "Trim")
    # santa
    P.obj("Santa", ball((0, -0.25, 0.65), (0.36, 0.3, 0.42), 14, 7), lambda c, n: "Belly" if abs(c.x) < 0.05 or c.z < 0.3 else "Accent", 1)
    P.obj("Belt", torus(0.34, 0.04, 0.0, 16, 4), "Dark"); P.parts[-1].data.transform(Matrix.Translation((0, -0.25, 0.55)) @ Matrix.Scale(1.0, 4))
    P.obj("Buckle", box((0, 0.06, 0.55), (0.1, 0.03, 0.08)), "Trim", 0, False)
    P.obj("Face", ball((0, -0.22, 1.18), (0.2, 0.19, 0.2), 12, 6), "Glass")
    P.obj("Beard", ball((0, -0.12, 1.02), (0.22, 0.14, 0.2), 12, 6), "Belly")
    P.obj("Nose", ball((0, -0.03, 1.17), (0.05, 0.04, 0.04), 6, 3), "Accent")
    for s in (1, -1):
        P.obj("Eye", ball((s * 0.07, -0.05, 1.24), (0.025, 0.015, 0.025), 6, 3), "Dark")
        P.obj("Arm", pipe([(s * 0.32, -0.25, 0.85), (s * 0.4, 0.05, 0.7), (s * 0.25, 0.3, 0.65)], [0.09, 0.08, 0.07], 8), "Accent")
        P.obj("Mitten", ball((s * 0.22, 0.34, 0.65), (0.07, 0.07, 0.07), 8, 4), "Dark")
    P.obj("Hat", pipe(bez((0, -0.24, 1.3), (0, -0.25, 1.5), (0, -0.4, 1.6), (0.0, -0.55, 1.55), 5), [0.2, 0.16, 0.1, 0.06, 0.04, 0.03], 10), "Accent")
    P.obj("HatBrim", torus(0.19, 0.05, 0.0, 16, 5), "Belly"); P.parts[-1].data.transform(Matrix.Translation((0, -0.24, 1.32)))
    P.obj("Pompom", ball((0, -0.58, 1.52), (0.07, 0.07, 0.07), 8, 4), "Belly")
    # the sack and the presents behind him
    P.obj("Sack", ball((0, -0.95, 0.95), (0.45, 0.4, 0.5), 14, 7), "Base", 1)
    P.obj("SackTie", pipe([(0, -0.95, 1.4), (0, -0.95, 1.5)], [0.08, 0.05], 6), "Trim")
    present(P, (0.38, -1.1, 0.95), (0.3, 0.3, 0.3), "Metal", "Trim")
    present(P, (-0.38, -1.05, 0.92), (0.28, 0.28, 0.26), "Accent", "Belly")
    present(P, (0.0, -0.7, 0.9), (0.24, 0.24, 0.22), "Belly", "Accent")
    # the reins, and two reindeer galloping
    for (rx, ry, lead) in ((0.42, 1.75, True), (-0.42, 1.75, False)):
        P.obj("Body", ball((rx, ry, 0.35), (0.25, 0.48, 0.25), 12, 6), lambda c, n: "Belly" if n.z < -0.5 else "Base", 1)
        P.obj("Neck", pipe([(rx, ry + 0.35, 0.45), (rx, ry + 0.55, 0.75)], [0.12, 0.1], 8), "Base")
        P.obj("Head", ball((rx, ry + 0.65, 0.82), (0.12, 0.2, 0.12), 10, 5), "Base")
        P.obj("Nose", ball((rx, ry + 0.85, 0.8), (0.06, 0.05, 0.05), 8, 4), "Lamp" if lead else "Dark")
        P.obj("Collar", torus(0.13, 0.03, 0.0, 12, 4), "Accent"); P.parts[-1].data.transform(Matrix.Translation((rx, ry + 0.45, 0.6)) @ Matrix.Rotation(math.radians(60), 4, "X"))
        P.obj("Bell", ball((rx, ry + 0.53, 0.5), (0.04, 0.04, 0.04), 6, 3), "Trim")
        P.obj("Tail", ball((rx, ry - 0.48, 0.42), (0.06, 0.06, 0.08), 6, 3), "Belly")
        for s in (1, -1):
            P.obj("Eye", ball((rx + s * 0.07, ry + 0.72, 0.88), (0.02, 0.02, 0.02), 6, 3), "Dark")
            P.obj("Ear", cone((rx + s * 0.08, ry + 0.6, 0.9), (rx + s * 0.2, ry + 0.55, 0.95), 0.03, 5), "Base", 0, False)
            ant = bez((rx + s * 0.05, ry + 0.6, 0.92), (rx + s * 0.15, ry + 0.5, 1.15), (rx + s * 0.3, ry + 0.45, 1.25), (rx + s * 0.38, ry + 0.5, 1.35), 5)
            P.obj("Antler", pipe(ant, [0.025, 0.022, 0.02, 0.016, 0.012, 0.0], 5), "Trim")
            P.obj("Tine", cone(ant[2], ant[2] + Vector((s * 0.02, 0.1, 0.12)), 0.012, 4), "Trim", 0, False)
            for fy, k in ((0.3, 0), (-0.3, 1)):
                hip = Vector((rx + s * 0.13, ry + fy, 0.25))
                name = "Sway%d" % ((0 if lead else 4) + k * 2 + (1 if s > 0 else 0))
                P.part(name, pipe([hip, hip + Vector((0, 0.12 if k == 0 else -0.12, -0.3)), hip + Vector((0, 0.18 if k == 0 else -0.25, -0.55))], [0.05, 0.04, 0.03], 6), "Base", tuple(hip))
                P.part(name, ball(tuple(hip + Vector((0, 0.18 if k == 0 else -0.25, -0.58))), (0.045, 0.05, 0.03), 6, 3), "Dark", tuple(hip))
        P.obj("Rein", pipe([(rx, ry + 0.4, 0.55), (rx * 0.5, 0.3, 0.68)], [0.012, 0.012], 4), "Dark")
    P.part("Muzzle", ball((0.42, 2.64, 0.8), (0.06, 0.04, 0.05), 8, 4), "Lamp", (0.42, 2.64, 0.8))
    return P


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
    """A giant snowman flying under a propeller on his top hat: three snowballs, coal eyes and buttons, a carrot nose, a striped red-and-green
    scarf with flying ends, stick arms with mittens, a candy cane in each hand."""
    P = Boss("snowman", {"Base": ((0.36, 0.23, 0.12), 0.3), "Belly": ((0.95, 0.97, 1.0), 0.35), "Accent": ((1.0, 0.50, 0.10), 0.5),
                         "Trim": ((0.80, 0.10, 0.10), 0.5), "Glass": ((0.70, 0.85, 1.0), 0.8), "Dark": ((0.04, 0.04, 0.05), 0.6),
                         "Glow": ((1.0, 0.85, 0.40), 0.5), "Metal": ((0.10, 0.50, 0.25), 0.5), "Lamp": ((1.0, 0.75, 0.30), 0.8)})
    snow = lambda c, n: "Glass" if n.z < -0.55 else "Belly"
    P.obj("Bottom", ball((0, 0, -0.7), (0.78, 0.72, 0.68), 18, 9), snow, 1)
    P.obj("Middle", ball((0, 0.05, 0.25), (0.58, 0.54, 0.52), 16, 8), snow, 1)
    P.obj("Head", ball((0, 0.08, 1.0), (0.42, 0.4, 0.4), 16, 8), snow, 1)
    for k, z in enumerate((0.45, 0.22, -0.02, -0.5)):
        P.obj("Button", ball((0, 0.6 if z > -0.1 else 0.72, z), (0.06, 0.04, 0.06), 8, 4), "Dark")
    for s in (1, -1):
        P.obj("Eye", ball((s * 0.14, 0.44, 1.1), (0.06, 0.04, 0.06), 8, 4), "Dark")
        P.obj("Glint", ball((s * 0.12, 0.47, 1.13), (0.02, 0.01, 0.02), 6, 3), "Belly")
        for k in (1, 2):   # the coal smile
            P.obj("Smile", ball((s * (0.08 + 0.07 * k), 0.43 - 0.03 * k, 0.9 + 0.015 * k * k), (0.03, 0.02, 0.03), 6, 3), "Dark")
        # stick arms with mittens and candy canes
        sh = Vector((s * 0.52, 0.05, 0.4)); el = Vector((s * 0.95, 0.15, 0.65)); hd = Vector((s * 1.25, 0.3, 0.95))
        P.obj("Stick", pipe([sh, el, hd], [0.05, 0.04, 0.035], 6), "Base")
        P.obj("Twig", pipe([el, el + Vector((s * 0.1, 0.05, 0.25))], [0.025, 0.01], 5), "Base")
        P.obj("Mitten", ball(tuple(hd), (0.11, 0.1, 0.12), 10, 5), "Trim")
        cane = [hd + Vector((0, 0.05, -0.55)), hd + Vector((0, 0.05, 0.2))] + [hd + Vector((s * (0.12 - 0.12 * math.cos(t)), 0.05, 0.2 + 0.12 * math.sin(t))) for t in [math.pi * i / 6 for i in range(1, 7)]]
        P.obj("Cane", pipe(cane, [0.045] * len(cane), 8), lambda c, n: "Trim" if (c.z * 6 + c.x * 3) % 1.0 < 0.5 else "Belly")
    P.obj("Mouth", ball((0, 0.4, 0.88), (0.05, 0.02, 0.03), 6, 3), "Dark")
    P.obj("Carrot", cone((0, 0.4, 1.0), (0, 0.95, 0.96), 0.08, 8), "Accent", 0, False)
    # the scarf
    P.obj("Scarf", torus(0.44, 0.09, 0.0, 22, 8), lambda c, n: "Trim" if (ang(Vector((c.x, c.y, 0))) * 3.0) % 1.0 < 0.5 else "Metal")
    P.parts[-1].data.transform(Matrix.Translation((0, 0.06, 0.66)))
    P.obj("ScarfEnd", pipe(bez((0.3, 0.3, 0.62), (0.45, 0.2, 0.4), (0.7, -0.2, 0.35), (0.95, -0.45, 0.5), 6), [0.09, 0.09, 0.085, 0.08, 0.08, 0.075, 0.07], 8),
          lambda c, n: "Trim" if (c.x * 6) % 1.0 < 0.5 else "Metal")
    # the top hat with its propeller
    P.obj("Brim", lathe([(0.0, 1.32), (0.45, 1.32), (0.45, 1.36), (0.0, 1.36)], 18, "z", (0, 0.08, 0)), "Dark")
    P.obj("Crown", lathe([(0.28, 1.36), (0.3, 1.85), (0.0, 1.85)], 18, "z", (0, 0.08, 0)), lambda c, n: "Trim" if c.z < 1.48 else "Dark")
    P.obj("Holly", ball((0.2, 0.32, 1.44), (0.06, 0.04, 0.06), 6, 3), "Trim")
    for k in range(2):
        P.obj("HollyLeaf", hull([(0.2, 0.33, 1.44), (0.35 - 0.3 * k, 0.32, 1.52), (0.3 - 0.2 * k, 0.33, 1.4), (0.27 - 0.15 * k, 0.31, 1.47)]), "Metal", 0, False)
    P.obj("Mast", pipe([(0, 0.08, 1.85), (0, 0.08, 2.05)], [0.04, 0.04], 6), "Base")
    P.prop((0, 0.08, 2.07), 0.95, 3, axis="z", chord=0.18, blade="Trim", tip="Belly", spinner="Glow", spinner_len=0.1, name="Rotor")
    P.part("Muzzle", ball((0, 0.98, 0.96), (0.06, 0.04, 0.05), 8, 4), "Glow", (0, 0.98, 0.96))
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


BOSSES = [("zeppelin", X_zeppelin), ("sleigh", X_sleigh), ("crystal", X_crystal), ("snowman", X_snowman), ("tree", X_tree)]

if __name__ == "__main__":
    os.makedirs(AB.OUT, exist_ok=True)
    for bid, fn in BOSSES:
        if ONLY and bid not in ONLY: continue
        fn().finish()
    print("DONE")
