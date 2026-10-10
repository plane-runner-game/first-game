# Sky Squad, the sea world's five bosses (2026-10-10: "bosses for Sky Sea - something completely professional"). Built from code like the
# alien bosses (alien_bosses.py lends its Boss class and shapes): the sky whale, the sky galleon, the thunder roc, the abyss leviathan and
# the citadel turtle (the same day the bomber, the gunship and the battleship were thrown out: "only the second and the fourth are beautiful").
# Run: blender -b -P Tools/blender/sea_bosses.py -- <out dir> [export] [ids,comma,separated]
#      writes Boss_<id>.fbx per boss (with "export") and two previews each.
# Same conventions as alien_bosses.py: +Y nose, +Z up, +X right; moving parts are their own objects named for how they move: "Prop*" spin
# about the nose, "Rotor*" about up, "TailRotor" about the wing axis (fast, with the blur disc), "Spin*" turn slowly about up, "Flap*" rock
# about the nose axis, "Sway*" about the wing axis; "Cloth" (sails, fins, frills: thin two-sided sheets) stays still but apart from the body, so
# the toon outline drawn round the body does not cover it; "Muzzle" is where his shots leave from.
import bpy, bmesh, math, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mathutils import Vector, Matrix
import enemy_planes as EP
from enemy_planes import loft, sweep, lathe, box, hull, tube, mirror_x, airfoil
import alien_bosses as AB
from alien_bosses import Boss, xf, ball, pipe, cone, bez, torus, sheet, grow, ang

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ONLY = argv[2].split(",") if len(argv) > 2 and argv[2] else None


def spline(pts, n):
    """a Catmull-Rom curve through pts, n samples per span."""
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

def grid(corner, u, v, nu, nv, bulge=Vector((0, 0, 0)), thick=0.025):
    """a cloth panel corner + u*s + v*t, bowed by bulge*sin(pi s)*sin(pi t), two-sided."""
    corner, u, v = Vector(corner), Vector(u), Vector(v)
    nrm = u.cross(v).normalized()
    bm = bmesh.new()
    def layer(off):
        return [[bm.verts.new(corner + u * (i / nu) + v * (j / nv) + bulge * math.sin(math.pi * i / nu) * math.sin(math.pi * j / nv) + nrm * off) for j in range(nv + 1)] for i in range(nu + 1)]
    A = layer(thick * 0.5); B = layer(-thick * 0.5)
    for i in range(nu):
        for j in range(nv):
            bm.faces.new((A[i][j], A[i + 1][j], A[i + 1][j + 1], A[i][j + 1]))
            bm.faces.new((B[i][j], B[i][j + 1], B[i + 1][j + 1], B[i + 1][j]))
    return bm


def speckle(c, k=1.0):
    """a steady pseudo-random number in [0, 1) for a face centre (star spots, barnacles)."""
    v = math.sin(c.x * 12.9898 * k + c.y * 78.233 * k + c.z * 37.719 * k) * 43758.5453
    return v - math.floor(v)


# ================================================================= 1. the sky whale
def S_whale():
    """A whale swimming through the sky (2026-10-10, in place of the bomber: "only the second and the fourth are beautiful"): a deep blue
    back scattered with glowing star spots, a cream grooved belly, barnacles on the head, a spray of water over the blowhole, long
    humpback fins that row and a tail fluke that beats up and down."""
    P = Boss("whale", {"Base": ((0.10, 0.27, 0.52), 0.6), "Belly": ((0.92, 0.89, 0.80), 0.45), "Accent": ((0.06, 0.16, 0.34), 0.55),
                       "Trim": ((0.78, 0.74, 0.66), 0.35), "Glass": ((0.62, 0.90, 1.0), 0.95), "Dark": ((0.03, 0.04, 0.07), 0.6),
                       "Glow": ((0.45, 1.0, 1.0), 0.5), "Metal": ((0.5, 0.55, 0.6), 0.6), "Lamp": ((1.0, 0.80, 0.35), 0.8)})
    def skin(c, n):
        if c.z < -0.12 and n.z < -0.2:
            return "Trim" if (c.x * 9.0) % 1.0 < 0.18 and c.y > -1.2 else "Belly"   # the throat grooves
        return "Base"
    body = loft([(2.55, 0.08, 0.07, 0, 0.0), (2.35, 0.45, 0.38, 0, -0.02), (1.7, 0.74, 0.6, 0, -0.02), (0.7, 0.86, 0.7, 0, 0.04),
                 (-0.4, 0.76, 0.63, 0, 0.1), (-1.3, 0.5, 0.44, 0, 0.16), (-2.0, 0.24, 0.22, 0, 0.2), (-2.35, 0.12, 0.11, 0, 0.22)], 20, sq=1.1)
    top = [v.co.copy() for v in body.verts if v.co.z > 0.15 and -1.9 < v.co.y < 1.3]
    P.obj("Body", body, skin, 1)
    for k, q in enumerate(top):   # the star spots: little glowing dots over the back
        if speckle(q, 1.7) < 0.55: P.obj("Star", ball(tuple(q * 1.0 + Vector((0, 0, 0.01))), (0.045, 0.045, 0.03), 6, 3), "Glow")
    for s in (1, -1):
        P.obj("Mouth", pipe(bez((s * 0.2, 2.42, -0.12), (s * 0.55, 2.1, -0.2), (s * 0.72, 1.6, -0.18), (s * 0.7, 1.25, -0.08), 6), [0.03] * 7, 6), "Accent")
        P.obj("Eye", ball((s * 0.7, 1.2, 0.02), (0.05, 0.09, 0.07), 10, 5), "Dark")
        P.obj("EyeShine", ball((s * 0.74, 1.24, 0.05), (0.02, 0.025, 0.02), 6, 3), "Lamp")
    for k in range(16):   # barnacles over the head
        a = k * 2.399; r = 0.15 + 0.035 * k
        x, y = math.sin(a) * r * 0.9, 2.05 - math.cos(a) * r * 0.8 - 0.05 * k
        P.obj("Barnacle", ball((x, y, 0.42 + 0.18 * max(0.0, 1 - abs(x) / 0.6) - 0.02 * k), (0.05 + 0.015 * (k % 3), 0.05, 0.03), 6, 3), "Trim")
    P.obj("Blowhole", ball((0, 1.45, 0.66), (0.08, 0.05, 0.02), 8, 3), "Dark")
    for k in range(9):   # the spray
        a = k * 2.4; h = 0.25 + 0.12 * (k % 4)
        P.obj("Spray", ball((math.sin(a) * 0.07 * (k % 3 + 1), 1.45 + math.cos(a) * 0.05, 0.7 + h), (0.06, 0.06, 0.08), 6, 3), "Glass")
    P.obj("Dorsal", hull([(0, -0.9, 0.5), (0, -1.35, 0.4), (0, -1.25, 0.72), (0.04, -1.1, 0.48), (-0.04, -1.1, 0.48)]), "Base", 0, False)
    for s in (1, -1):   # the long fins, rowing
        name = "FlapR" if s > 0 else "FlapL"
        hub = (s * 0.72, 1.05, -0.28)
        keys = [(0.72, 1.3, 0.85, 0.12, -0.28), (1.3, 1.15, 0.6, 0.08, -0.42), (1.9, 0.95, 0.5, 0.05, -0.5), (2.35, 0.7, 0.45, 0.03, -0.5)]
        bm = sweep([(x, airfoil(le, te, th, z)) for (x, le, te, th, z) in keys], "x")
        if s < 0: bm = mirror_x(bm)
        P.part(name, bm, lambda c, n: "Belly" if n.z < -0.3 else ("Trim" if speckle(c, 2.0) < 0.12 else "Base"), hub, 1)
    # the fluke: it beats up and down about the wing axis
    hub = (0, -2.3, 0.22)
    bm = sweep([(x, airfoil(-2.25 - abs(x) * 0.25, -2.75 + abs(x) * 0.15 - (0.12 if abs(x) < 0.15 else 0), 0.07 - abs(x) * 0.04, 0.22 + abs(x) * 0.06)) for x in (-1.15, -0.8, -0.4, 0.0, 0.4, 0.8, 1.15)], "x")
    P.part("Sway0", bm, lambda c, n: "Belly" if n.z < -0.3 else "Base", hub, 1)
    P.part("Muzzle", ball((0, 2.58, -0.05), (0.1, 0.05, 0.08), 8, 4), "Glow", (0, 2.58, -0.05))
    return P


# ================================================================= 3. the thunder roc
def S_roc():
    """A giant storm seabird (in place of the gunship): white plumage, storm-blue wing tips and tail, lightning running across its wings,
    a hooked golden beak, golden eyes, a swept crest, golden talons - and great wings that beat."""
    P = Boss("roc", {"Base": ((0.95, 0.96, 0.98), 0.4), "Belly": ((0.80, 0.84, 0.90), 0.35), "Accent": ((0.14, 0.36, 0.80), 0.5),
                     "Trim": ((0.98, 0.74, 0.18), 0.7), "Glass": ((0.55, 0.85, 1.0), 0.95), "Dark": ((0.05, 0.06, 0.10), 0.5),
                     "Glow": ((0.45, 0.90, 1.0), 0.5), "Metal": ((0.5, 0.55, 0.6), 0.6), "Lamp": ((1.0, 0.85, 0.20), 0.8)})
    P.obj("Body", loft([(1.55, 0.2, 0.2, 0, 0.42), (1.25, 0.32, 0.34, 0, 0.3), (0.6, 0.52, 0.5, 0, 0.08), (-0.3, 0.5, 0.45, 0, 0.0),
                        (-1.0, 0.32, 0.28, 0, 0.02), (-1.45, 0.14, 0.1, 0, 0.06)], 16), lambda c, n: "Belly" if n.z < -0.3 else "Base", 1)
    P.obj("Head", ball((0, 1.62, 0.5), (0.3, 0.36, 0.3), 14, 7), lambda c, n: "Base")
    P.obj("Beak", pipe(bez((0, 1.88, 0.5), (0, 2.25, 0.5), (0, 2.45, 0.42), (0, 2.5, 0.28), 6), [0.13, 0.11, 0.085, 0.06, 0.04, 0.02, 0.0], 10), "Trim")
    P.obj("BeakLow", pipe([(0, 1.9, 0.4), (0, 2.25, 0.37), (0, 2.35, 0.36)], [0.08, 0.05, 0.0], 8), "Trim")
    for s in (1, -1):
        P.obj("Eye", ball((s * 0.2, 1.8, 0.6), (0.05, 0.07, 0.05), 10, 5), "Lamp")
        P.obj("Pupil", ball((s * 0.23, 1.83, 0.6), (0.02, 0.03, 0.03), 6, 3), "Dark")
        P.obj("Brow", box((s * 0.17, 1.82, 0.67), (0.14, 0.18, 0.04), Matrix.Rotation(math.radians(s * 18), 3, "Y")), "Accent", 0, False)
        for k in range(3):   # the swept crest
            P.obj("Crest", cone((s * 0.05 * k, 1.55, 0.72), (s * (0.08 + 0.1 * k), 1.0 - 0.1 * k, 1.05 - 0.08 * k), 0.06, 5), "Accent", 0, False)
        # golden talons, tucked under
        for k in (-1, 0, 1):
            P.obj("Talon", pipe(bez((s * 0.22, 0.0, -0.35), (s * (0.25 + k * 0.05), 0.15, -0.6), (s * (0.27 + k * 0.08), 0.35, -0.62), (s * (0.27 + k * 0.08), 0.45, -0.52), 4), [0.04, 0.035, 0.03, 0.02, 0.0], 6), "Trim")
        # the wings, beating; sliced fine so the lightning comes out as streaks
        name = "FlapR" if s > 0 else "FlapL"
        hub = (s * 0.42, 0.45, 0.25)
        keys = [(0.4, 1.0, -0.55, 0.16, 0.25), (1.2, 0.95, -0.75, 0.1, 0.42), (2.0, 0.75, -0.75, 0.07, 0.6), (2.7, 0.45, -0.55, 0.04, 0.72), (3.15, 0.1, -0.2, 0.02, 0.78)]
        secs = []
        for a0, a1 in zip(keys, keys[1:]):
            n = max(2, int((a1[0] - a0[0]) / 0.08))
            secs += [tuple(u + (v - u) * i / n for u, v in zip(a0, a1)) for i in range(n)]
        secs.append(keys[-1])
        bm = sweep([(x, airfoil(le, te, th, z)) for (x, le, te, th, z) in secs], "x")
        if s < 0: bm = mirror_x(bm)
        def plume(c, n):
            if n.z < -0.3: return "Belly"
            x = abs(c.x)
            if x > 2.45 or c.y < -0.62: return "Accent"
            if 0.8 < x < 2.4 and abs(c.y - (0.55 - (x - 0.8) * 0.35) - 0.12 * math.sin(x * 9)) < 0.045: return "Glow"
            return "Base"
        P.part(name, bm, plume, hub, 0)
        for k in range(5):   # the primaries splayed at the tip
            x0 = 2.6 + k * 0.1; y0 = 0.35 - k * 0.15
            P.part(name, cone((s * x0, y0, 0.74), (s * (x0 + 0.55 - k * 0.05), y0 - 0.12 - k * 0.08, 0.8), 0.06, 4), "Accent", hub, 0, False)
    for k in range(7):   # the tail fan
        a = math.radians(-36 + k * 12)
        P.obj("TailFeather", box((math.sin(a) * 0.45, -1.55 - math.cos(a) * 0.35, 0.08), (0.14, 0.75, 0.03), Matrix.Rotation(-a, 3, "Z")),
              lambda c, n: "Accent" if c.y < -1.9 else "Base", 0, False)
    P.part("Muzzle", ball((0, 2.5, 0.3), (0.08, 0.05, 0.07), 8, 4), "Glow", (0, 2.5, 0.3))
    return P


# ================================================================= 5. the citadel turtle
def S_turtle():
    """The last boss (in place of the battleship): a giant sea turtle carrying a white-and-gold citadel on its shell - walls, three towers
    with golden roofs, a lighthouse whose beam turns - with glowing coral growing between the scutes, front flippers that row the air."""
    P = Boss("turtle", {"Base": ((0.20, 0.46, 0.42), 0.5), "Belly": ((0.90, 0.84, 0.64), 0.4), "Accent": ((0.56, 0.36, 0.17), 0.55),
                        "Trim": ((0.97, 0.76, 0.24), 0.75), "Glass": ((0.40, 0.85, 1.0), 0.95), "Dark": ((0.05, 0.05, 0.06), 0.5),
                        "Glow": ((0.55, 1.0, 1.0), 0.5), "Metal": ((0.93, 0.93, 0.90), 0.45), "Lamp": ((1.0, 0.45, 0.45), 0.8)})
    shell = lathe([(0.0, 0.85), (0.55, 0.8), (1.0, 0.62), (1.3, 0.35), (1.45, 0.08), (1.42, -0.02)], 36, "z")
    for v in shell.verts: v.co.y *= 1.22
    def scutes(c, n):
        r = math.hypot(c.x, c.y / 1.22); a = ang(Vector((c.x, c.y / 1.22, 0)))
        if r > 1.38: return "Belly"
        if r < 0.72: return "Accent"
        if (r * 2.6) % 1.0 < 0.1 or (a / (2 * math.pi) * (6 if r < 0.8 else 10)) % 1.0 < 0.06: return "Dark"
        return "Accent"
    P.obj("Shell", shell, scutes)
    P.obj("Plastron", ball((0, 0, -0.1), (1.3, 1.6, 0.32), 24, 8), lambda c, n: "Belly")
    P.obj("Neck", pipe([(0, 1.45, -0.05), (0, 1.85, 0.0), (0, 2.1, 0.08)], [0.3, 0.27, 0.25], 14), "Base")
    P.obj("Head", ball((0, 2.3, 0.12), (0.34, 0.4, 0.28), 16, 8), lambda c, n: "Belly" if n.z < -0.4 else "Base")
    P.obj("Beak", hull([(0, 2.72, 0.05), (0.15, 2.55, 0.02), (-0.15, 2.55, 0.02), (0, 2.6, -0.1), (0.12, 2.45, 0.15), (-0.12, 2.45, 0.15)]), "Accent", 0, False)
    for s in (1, -1):
        P.obj("Eye", ball((s * 0.24, 2.42, 0.2), (0.06, 0.07, 0.06), 10, 5), "Dark")
        P.obj("EyeShine", ball((s * 0.27, 2.46, 0.23), (0.02, 0.02, 0.02), 6, 3), "Glow")
        P.obj("BackFlipper", hull([(s * 0.9, -1.4, -0.1), (s * 0.7, -1.5, -0.12), (s * 1.4, -2.0, -0.2), (s * 1.2, -2.1, -0.18), (s * 0.85, -1.45, 0.0)]), "Base", 0, False)
        name = "FlapR" if s > 0 else "FlapL"
        hub = (s * 1.05, 0.95, -0.12)
        keys = [(1.05, 1.25, 0.65, 0.14, -0.12), (1.7, 1.2, 0.75, 0.1, -0.16), (2.35, 0.95, 0.65, 0.06, -0.2), (2.8, 0.6, 0.5, 0.03, -0.22)]
        bm = sweep([(x, airfoil(le, te, th, z)) for (x, le, te, th, z) in keys], "x")
        if s < 0: bm = mirror_x(bm)
        P.part(name, bm, lambda c, n: "Belly" if n.z < -0.3 else ("Dark" if speckle(c, 3.0) < 0.1 else "Base"), hub, 1)
    P.obj("Tail", cone((0, -1.85, -0.05), (0, -2.25, -0.1), 0.12, 8), "Base", 0, False)
    # coral among the scutes
    for k in range(10):
        a = k * 2.399 + 0.4; r = 0.95 + 0.25 * (k % 3) / 2
        base = Vector((math.sin(a) * r, math.cos(a) * r * 1.22, 0.62 - (r - 0.95) * 0.9))
        for j in range(3):
            d = Vector((math.sin(a + j * 2.1) * 0.12, math.cos(a + j * 2.1) * 0.12, 0.28 + 0.06 * j))
            P.obj("Coral", cone(base, base + d, 0.04, 5), "Lamp" if k % 2 == 0 else "Glass", 0, False)
            P.obj("CoralTip", ball(tuple(base + d), (0.04, 0.04, 0.04), 6, 3), "Lamp" if k % 2 == 0 else "Glass")
    # the citadel: a crenellated wall, three towers with golden roofs, the lighthouse in the middle
    P.obj("Wall", lathe([(0.62, 0.72), (0.62, 1.05), (0.0, 1.05)], 24, "z"), lambda c, n: "Metal")
    for k in range(12):
        a = 2 * math.pi * k / 12
        P.obj("Merlon", box((math.sin(a) * 0.6, math.cos(a) * 0.6, 1.1), (0.1, 0.1, 0.1), Matrix.Rotation(-a, 3, "Z")), "Metal", 0, False)
    P.obj("Gate", box((0, 0.6, 0.86), (0.2, 0.06, 0.24)), "Dark", 0, False)
    for k in range(3):
        a = 2 * math.pi * k / 3 + math.pi / 3
        c = (math.sin(a) * 0.62, math.cos(a) * 0.62, 0.7)
        P.obj("Tower", lathe([(0.17, 0.0), (0.17, 0.62), (0.2, 0.64), (0.2, 0.7)], 12, "z", c), "Metal")
        P.obj("Roof", lathe([(0.24, 0.7), (0.0, 1.05)], 12, "z", c), "Trim")
        P.obj("Window", box((c[0] * 1.27, c[1] * 1.27, 1.05), (0.06, 0.06, 0.1), Matrix.Rotation(-a, 3, "Z")), "Glass", 0, False)
    P.obj("Lighthouse", lathe([(0.26, 1.05), (0.2, 1.75), (0.24, 1.78), (0.24, 1.82)], 16, "z"),
          lambda c, n: "Accent" if (c.z * 6.0) % 1.0 < 0.5 and c.z < 1.75 else "Metal")
    P.obj("Lantern", lathe([(0.15, 1.82), (0.15, 2.02), (0.0, 2.02)], 12, "z"), "Glow")
    P.obj("Cupola", lathe([(0.2, 2.02), (0.0, 2.28)], 12, "z"), "Trim")
    P.obj("Spire", cone((0, 0, 2.26), (0, 0, 2.45), 0.03, 6), "Trim", 0, False)
    for s in (1, -1):   # the beam, turning
        P.part("SpinBeam", hull([(0, 0, 1.92), (0, s * 0.12, 1.86), (0, s * 0.12, 1.98), (0, s * 1.25, 1.75), (0, s * 1.25, 2.12), (0.05, s * 1.25, 1.94), (-0.05, s * 1.25, 1.94)]),
               "Glow", (0, 0, 1.92), 0, False)
    P.part("Muzzle", ball((0, 2.74, 0.05), (0.09, 0.05, 0.07), 8, 4), "Glow", (0, 2.74, 0.05))
    return P


# ================================================================= 2. the sky galleon
def S_galleon():
    """A flying galleon: a dark wooden hull with a red bottom and gold rails, a castle at the stern with lit windows, three masts of bellied
    cream sails with red crosses, a gilded figurehead under the bowsprit, a row of cannon each side, glowing keel engines, two stern
    propellers - and canvas wings on gilded ribs that beat at its sides."""
    P = Boss("galleon", {"Base": ((0.33, 0.19, 0.10), 0.35), "Belly": ((0.95, 0.91, 0.80), 0.25), "Accent": ((0.72, 0.13, 0.10), 0.4),
                         "Trim": ((0.96, 0.74, 0.24), 0.7), "Glass": ((0.55, 0.38, 0.22), 0.3), "Dark": ((0.06, 0.05, 0.05), 0.3),
                         "Glow": ((0.30, 0.95, 1.0), 0.5), "Metal": ((0.22, 0.22, 0.24), 0.6), "Lamp": ((1.0, 0.72, 0.30), 0.8)})
    def hullp(c, n):
        if c.z < -0.22: return "Accent"
        if 0.16 < c.z < 0.24 and abs(c.x) > 0.3: return "Trim"
        return "Base"
    P.obj("Hull", loft([(2.35, 0.06, 0.22, 0, 0.12), (1.95, 0.42, 0.5, 0, 0.02), (0.8, 0.62, 0.6, 0, -0.04), (-0.8, 0.6, 0.6, 0, -0.02),
                        (-1.8, 0.52, 0.56, 0, 0.04), (-2.2, 0.44, 0.52, 0, 0.1)], 16, sq=1.7), hullp, 1)
    P.obj("Deck", box((0, -0.05, 0.47), (1.0, 3.9, 0.04)), "Glass", 0, False)
    P.obj("SternCastle", box((0, -1.75, 0.72), (1.02, 0.85, 0.5)), lambda c, n: "Trim" if n.z > 0.5 else "Base", 0, False)
    for s in (1, -1):
        for k in range(3):
            P.obj("Window", box((s * 0.52, -1.5 - k * 0.24, 0.74), (0.02, 0.14, 0.16)), "Lamp", 0, False)
        P.obj("Lantern", ball((s * 0.42, -2.25, 1.08), (0.07, 0.07, 0.09), 8, 4), "Lamp")
        for k in range(4):   # the cannon, run out
            y = 1.15 - k * 0.6
            P.obj("Cannon", pipe([(s * 0.5, y, 0.08), (s * 0.82, y, 0.08)], [0.06, 0.05], 8), "Metal")
            P.obj("Port", box((s * 0.6, y, 0.08), (0.03, 0.2, 0.2)), "Dark", 0, False)
        P.obj("Rail", box((s * 0.5, 0.0, 0.58), (0.04, 3.6, 0.06)), "Trim", 0, False)
    P.obj("Forecastle", box((0, 1.6, 0.6), (0.85, 0.6, 0.25)), lambda c, n: "Trim" if n.z > 0.5 else "Base", 0, False)
    for i in range(5):
        P.obj("SternWindow", box((-0.36 + i * 0.18, -2.19, 0.75), (0.12, 0.02, 0.18)), "Lamp", 0, False)
    # masts, yards and sails
    for (y, h, w) in ((1.05, 2.1, 1.3), (0.0, 2.5, 1.6), (-1.0, 2.0, 1.2)):
        P.obj("Mast", pipe([(0, y, 0.45), (0, y, 0.45 + h + 0.3)], [0.06, 0.035], 8), "Base")
        for (z0, z1, ww) in ((0.75, 0.45 + h * 0.55, w), (0.45 + h * 0.6, 0.45 + h, w * 0.75)):
            P.obj("Yard", pipe([(-ww * 0.55, y, z1), (ww * 0.55, y, z1)], [0.03, 0.03], 6), "Base")
            P.part("Cloth", grid((-ww * 0.5, y + 0.02, z0), (ww, 0, 0), (0, 0, z1 - z0 - 0.04), 6, 4, Vector((0, 0.22, 0))),
                  lambda c, n, y=y, z0=z0, z1=z1: "Accent" if (abs(c.x) < 0.07 or abs(c.z - (z0 + z1) * 0.5) < 0.06) else "Belly", (0, 0, 0), 0, False)
        P.obj("Nest", lathe([(0.16, 0.0), (0.16, 0.12), (0.0, 0.12)], 10, "z", (0, y, 0.45 + h * 0.62)), "Base")
        P.part("Cloth", grid((0, y, 0.45 + h + 0.15), (0, -0.45, 0.0), (0, 0, 0.2), 4, 2, Vector((0.06, 0, 0))), "Accent", (0, 0, 0), 0, False)
    P.obj("Bowsprit", pipe([(0, 2.0, 0.45), (0, 2.95, 0.85)], [0.05, 0.03], 8), "Base")
    P.part("Cloth", grid((0, 2.0, 0.55), (0, 0.85, 0.32), (0, -0.85, 1.25), 4, 4, Vector((0.12, 0, 0))), "Belly", (0, 0, 0), 0, False)
    P.obj("Figurehead", ball((0, 2.38, 0.22), (0.1, 0.16, 0.14), 10, 5), "Trim")
    P.obj("FigureWing", hull([(0, 2.3, 0.25), (0.25, 2.2, 0.45), (-0.25, 2.2, 0.45), (0, 2.1, 0.3)]), "Trim", 0, False)
    P.obj("BowCannon", pipe([(0, 2.1, 0.32), (0, 2.65, 0.3)], [0.07, 0.06], 8), "Metal")
    # the flying engines: glowing rings under the keel, two propellers at the stern
    for y in (0.9, -0.6):
        P.obj("KeelRing", lathe([(0.0, -0.78), (0.32, -0.72), (0.4, -0.6), (0.0, -0.55)], 18, "z", (0, y, 0)), lambda c, n: "Glow" if c.z < -0.72 else "Trim")
    for s in (1, -1):
        P.obj("PropShaft", pipe([(s * 0.38, -2.0, -0.05), (s * 0.38, -2.45, -0.05)], [0.05, 0.05], 8), "Metal")
        P.prop((s * 0.38, -2.5, -0.05), 0.42, 4, blade="Base", tip="Trim", spinner="Trim", spinner_len=0.12)
        # the canvas wings on gilded ribs, beating
        name = "FlapR" if s > 0 else "FlapL"
        hub = Vector((s * 0.58, 0.3, 0.3))
        tips = [Vector((s * 2.4, 0.75, 0.95)), Vector((s * 2.55, 0.0, 0.8)), Vector((s * 2.2, -0.7, 0.6)), Vector((s * 1.5, -1.1, 0.4))]
        for t in tips: P.part(name, pipe([hub, t], [0.05, 0.02], 6), "Trim", tuple(hub))
        polys = []
        for a, b in zip(tips, tips[1:]):
            mid = (a + b) * 0.5 + (hub - (a + b) * 0.5) * 0.12
            polys.append([hub, a, mid]); polys.append([hub, mid, b])
        P.part(name, sheet([[tuple(p) for p in poly] for poly in polys], 0.025), "Belly", tuple(hub), 0, False)
        P.part(name, ball(tuple(tips[0]), (0.06, 0.06, 0.06), 6, 3), "Lamp", tuple(hub))
    P.part("Muzzle", ball((0, 2.7, 0.3), (0.08, 0.05, 0.08), 8, 4), "Lamp", (0, 2.7, 0.3))
    return P


# ================================================================= 4. the abyss leviathan
def S_leviathan():
    """A sea serpent risen into the sky: a coiled teal body with a pale belly and glowing spots, bone spikes and a coral sail down its back,
    a great horned head with an open jaw, glowing eyes and long barbels, a crescent tail fluke - and coral fan fins that row the air."""
    P = Boss("leviathan", {"Base": ((0.04, 0.27, 0.36), 0.6), "Belly": ((0.74, 0.88, 0.80), 0.45), "Accent": ((1.0, 0.42, 0.24), 0.5),
                           "Trim": ((0.90, 0.86, 0.74), 0.5), "Glass": ((0.25, 0.75, 0.9), 0.9), "Dark": ((0.03, 0.05, 0.07), 0.4),
                           "Glow": ((0.20, 1.0, 0.85), 0.5), "Metal": ((0.4, 0.45, 0.5), 0.6), "Lamp": ((1.0, 0.85, 0.25), 0.8)})
    ctrl = [(0, 1.55, 0.75), (0, 1.05, 0.35), (0.55, 0.45, 0.05), (0.75, -0.3, 0.3), (0.0, -0.75, 0.45), (-0.75, -1.05, 0.15), (-0.55, -1.75, -0.25),
            (0.25, -2.1, -0.2), (0.6, -2.55, 0.15)]
    sp = spline(ctrl, 4)
    N = len(sp)
    rad = [0.36 * (1 - 0.82 * (i / (N - 1)) ** 1.3) + 0.03 for i in range(N)]
    rad[0] = 0.3
    P.obj("Body", pipe(sp, rad, 14), lambda c, n: "Belly" if n.z < -0.4 else "Base", 0)
    # spines and the coral sail between them; glowing spots down the flanks
    tops = []
    for i in range(2, N - 3, 2):
        p = sp[i]; t = (sp[i + 1] - sp[i - 1]).normalized()
        side = t.cross(Vector((0, 0, 1)))
        side = side.normalized() if side.length > 1e-3 else Vector((1, 0, 0))
        up = side.cross(t).normalized()
        if up.z < 0: up = -up
        base = p + up * rad[i] * 0.85; tip = base + up * (0.38 * rad[i] / 0.36 + 0.08) - t * 0.12
        P.obj("Spine", cone(base, tip, 0.045, 5), "Trim", 0, False)
        tops.append((base, tip))
        for sg in (1, -1):
            P.obj("Spot", ball(tuple(p + side * sg * rad[i] * 0.95 + up * rad[i] * 0.15), (0.05, 0.05, 0.05), 6, 3), "Glow")
    polys = []
    for (b0, t0), (b1, t1) in zip(tops, tops[1:]):
        polys.append([b0, t0, t1, b1])
    bm = bmesh.new()
    for poly in polys:
        n = (poly[1] - poly[0]).cross(poly[3] - poly[0]).normalized() * 0.012
        f = [bm.verts.new(v + n) for v in poly]; g = [bm.verts.new(v - n) for v in poly]
        bm.faces.new(f); bm.faces.new(list(reversed(g)))
    P.part("Cloth", bm, "Accent", (0, 0, 0), 0, False)
    # the tail fluke
    tp = sp[-1]
    P.part("Cloth", sheet([[tuple(tp), tuple(tp + Vector((0.55, -0.35, 0.3))), tuple(tp + Vector((0.2, -0.25, 0.0)))],
                          [tuple(tp), tuple(tp + Vector((0.2, -0.25, 0.0))), tuple(tp + Vector((-0.2, -0.5, -0.25)))]], 0.03), "Accent", (0, 0, 0), 0, False)
    # the head
    HC, HK = Vector((0, 1.55, 0.75)), 1.35
    def H(bm): return grow(bm, HC, HK)
    P.obj("Skull", H(loft([(1.45, 0.24, 0.24, 0, 0.78), (1.75, 0.27, 0.22, 0, 0.84), (2.05, 0.22, 0.15, 0, 0.84), (2.3, 0.14, 0.09, 0, 0.8), (2.45, 0.06, 0.05, 0, 0.78)], 14)),
          lambda c, n: "Belly" if n.z < -0.4 else "Base", 1)
    P.obj("Jaw", H(loft([(1.55, 0.2, 0.08, 0, 0.6), (1.95, 0.17, 0.06, 0, 0.53), (2.3, 0.08, 0.04, 0, 0.48), (2.4, 0.03, 0.02, 0, 0.47)], 12)), lambda c, n: "Belly" if n.z < -0.2 else "Base", 1)
    P.obj("Throat", H(ball((0, 1.95, 0.67), (0.13, 0.32, 0.05), 12, 6)), "Glow")
    for s in (1, -1):
        P.obj("Eye", H(ball((s * 0.19, 1.82, 0.9), (0.055, 0.08, 0.045), 10, 5)), "Lamp")
        P.obj("Horn", H(pipe(bez((s * 0.14, 1.6, 0.98), (s * 0.2, 1.35, 1.18), (s * 0.18, 1.1, 1.28), (s * 0.1, 0.9, 1.3), 5), [0.06, 0.05, 0.04, 0.03, 0.015, 0.0], 8)), "Trim")
        P.obj("Barbel", H(pipe(bez((s * 0.12, 2.25, 0.72), (s * 0.35, 2.4, 0.6), (s * 0.5, 2.2, 0.35), (s * 0.55, 1.9, 0.2), 6), [0.025, 0.022, 0.019, 0.016, 0.012, 0.008, 0.0], 6)), "Trim")
        # the frill fan behind the jaw
        f0 = Vector((s * 0.22, 1.6, 0.78))
        fr = [f0 + Vector((s * 0.45, -0.25, 0.35)), f0 + Vector((s * 0.55, -0.35, 0.05)), f0 + Vector((s * 0.4, -0.3, -0.25))]
        P.part("Cloth", H(sheet([[tuple(f0), tuple(fr[0]), tuple(fr[1])], [tuple(f0), tuple(fr[1]), tuple(fr[2])]], 0.02)), "Accent", (0, 0, 0), 0, False)
        for t in fr: P.obj("FrillRib", H(pipe([f0, t], [0.02, 0.008], 5)), "Trim")
        for k in range(4):
            y = 1.85 + k * 0.12
            P.obj("Tooth", H(cone((s * (0.17 - k * 0.03), y, 0.7), (s * (0.16 - k * 0.03), y + 0.02, 0.6), 0.024, 5)), "Trim", 0, False)
            P.obj("Tooth", H(cone((s * (0.15 - k * 0.03), y, 0.56), (s * (0.14 - k * 0.03), y + 0.02, 0.65), 0.02, 5)), "Trim", 0, False)
        # the fan fins, rowing
        name = "FlapR" if s > 0 else "FlapL"
        hub = Vector((s * 0.35, 1.0, 0.35))
        tips = [hub + Vector((s * 0.85, 0.45, 0.5)), hub + Vector((s * 1.15, 0.0, 0.3)), hub + Vector((s * 1.05, -0.45, 0.05)), hub + Vector((s * 0.6, -0.65, -0.1))]
        polys = []
        for a, b in zip(tips, tips[1:]):
            mid = (a + b) * 0.5 + (hub - (a + b) * 0.5) * 0.18
            polys.append([hub, a, mid]); polys.append([hub, mid, b])
        P.part(name, sheet([[tuple(p) for p in poly] for poly in polys], 0.025), "Accent", tuple(hub), 0, False)
        for t in tips: P.part(name, pipe([hub, t], [0.035, 0.01], 6), "Trim", tuple(hub))
    mz = HC + (Vector((0, 2.42, 0.62)) - HC) * HK
    P.part("Muzzle", ball(tuple(mz), (0.11, 0.08, 0.08), 8, 4), "Glow", tuple(mz))
    return P


BOSSES = [("whale", S_whale), ("galleon", S_galleon), ("roc", S_roc), ("leviathan", S_leviathan), ("turtle", S_turtle)]

if __name__ == "__main__":
    os.makedirs(AB.OUT, exist_ok=True)
    for bid, fn in BOSSES:
        if ONLY and bid not in ONLY: continue
        fn().finish()
    print("DONE")
