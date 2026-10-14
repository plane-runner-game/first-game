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


# ================================================================= shared bits for the 2026-10-12 remakes ("make them better")
def fine_secs(keys, step=0.08):
    secs = []
    for a0, a1 in zip(keys, keys[1:]):
        n = max(2, int((a1[0] - a0[0]) / step))
        secs += [tuple(u + (v - u) * i / n for u, v in zip(a0, a1)) for i in range(n)]
    secs.append(keys[-1])
    return secs

def ring_on(p, t, R, r, seg=16, sides=5):
    """a torus of radius R round the point p, square to the direction t."""
    bm = torus(R, r, 0.0, seg, sides)
    q = Vector(t).normalized().to_track_quat("Z", "Y").to_matrix()
    for v in bm.verts: v.co = q @ v.co + Vector(p)
    return bm

def bolt(a, b, w, kinks=5, seed=1):
    """a zig-zag lightning bolt from a to b, a chain of thin tapered pieces."""
    a, b = Vector(a), Vector(b); d = b - a
    side = d.cross(Vector((0, 0, 1)) if abs(d.normalized().z) < 0.9 else Vector((1, 0, 0))).normalized()
    pts = [a]
    for i in range(1, kinks):
        pts.append(a + d * (i / kinks) + side * (w * 3.0 * (1 if (i + seed) % 2 else -1)))
    pts.append(b)
    return pipe(pts, [w * (1 - 0.8 * i / kinks) for i in range(len(pts) - 1)] + [0.0], 5)


# ================================================================= 1. the sky whale
def S_whale():
    """The sky whale (2026-10-12, remade: "make them better"): a great humpback swimming the sky with a face - a kind, ancient eye under a
    heavy brow, a long smiling mouth line, knobbly tubercles and barnacle clusters on the head, a cream belly with deep grooves; a
    constellation of glowing star spots joined by light along its back, glowing runes down its flanks, a golden harness carrying a little
    lantern pavilion with pennants, long humpback fins edged in light that row, a fluke with glowing tips that beats, a fountain of glowing
    spray from the blowhole, and rings of bubbles orbiting it."""
    P = Boss("whale", {"Base": ((0.10, 0.25, 0.55), 0.6), "Belly": ((0.94, 0.90, 0.80), 0.45), "Accent": ((0.05, 0.13, 0.32), 0.55),
                       "Trim": ((0.98, 0.76, 0.26), 0.85), "Glass": ((0.62, 0.92, 1.0), 0.95), "Dark": ((0.03, 0.04, 0.07), 0.6),
                       "Glow": ((0.40, 1.0, 1.0), 0.5), "Metal": ((0.72, 0.70, 0.64), 0.4), "Lamp": ((1.0, 0.80, 0.35), 0.8)})
    def skin(c, n):
        if c.z < -0.1 and n.z < -0.25:
            return "Accent" if (c.x * 8.0) % 1.0 < 0.2 and c.y > -1.3 else "Belly"   # the throat grooves
        if n.z > 0.55 and abs(c.x) < 0.22: return "Accent"   # a darker line down the spine
        return "Base"
    body = loft([(2.6, 0.08, 0.07, 0, -0.05), (2.42, 0.48, 0.4, 0, -0.06), (1.8, 0.8, 0.66, 0, -0.04), (0.8, 0.92, 0.76, 0, 0.02),
                 (-0.3, 0.84, 0.68, 0, 0.08), (-1.2, 0.56, 0.48, 0, 0.14), (-1.9, 0.28, 0.25, 0, 0.18), (-2.35, 0.13, 0.12, 0, 0.2)], 22, sq=1.1)
    P.obj("Body", body, skin, 1)
    # the face: a long smiling mouth line, a kind ancient eye with brow and lids
    for s in (1, -1):
        P.obj("Mouth", pipe(bez((s * 0.12, 2.55, -0.18), (s * 0.55, 2.3, -0.32), (s * 0.82, 1.75, -0.28), (s * 0.86, 1.25, -0.1), 8), [0.035] * 9, 6), "Dark")
        e = Vector((s * 0.8, 1.32, 0.1))
        P.obj("EyeWhite", ball(tuple(e), (0.09, 0.2, 0.16), 12, 6), "Belly")
        P.obj("Iris", ball(tuple(e + Vector((s * 0.05, 0.04, 0.0))), (0.06, 0.13, 0.12), 10, 5), "Glow")
        P.obj("Pupil", ball(tuple(e + Vector((s * 0.08, 0.05, 0.0))), (0.035, 0.07, 0.07), 8, 4), "Dark")
        P.obj("Glint", ball(tuple(e + Vector((s * 0.1, 0.09, 0.05))), (0.015, 0.03, 0.03), 6, 3), "Belly")
        P.obj("Lid", ball(tuple(e + Vector((s * 0.0, 0.0, 0.1))), (0.11, 0.24, 0.08), 12, 5), "Accent")
        P.obj("Brow", pipe(bez(e + Vector((s * -0.02, 0.22, 0.13)), e + Vector((s * 0.04, 0.08, 0.2)), e + Vector((s * 0.04, -0.1, 0.19)), e + Vector((s * -0.02, -0.25, 0.12)), 6), [0.03, 0.045, 0.05, 0.05, 0.045, 0.035, 0.02], 6), "Accent")
        for k in range(5):   # knobbly tubercles along the jaw
            q = bez((s * 0.25, 2.48, -0.05), (s * 0.55, 2.3, -0.12), (s * 0.75, 2.0, -0.12), (s * 0.82, 1.7, -0.05), 5)[k]
            P.obj("Tubercle", ball(tuple(q + Vector((s * 0.03, 0, 0.04))), (0.045, 0.045, 0.04), 6, 3), "Base")
    for k in range(18):   # barnacle clusters over the head
        a = k * 2.399; r = 0.12 + 0.03 * k
        x, y = math.sin(a) * r * 0.9, 2.15 - math.cos(a) * r * 0.75 - 0.04 * k
        P.obj("Barnacle", lathe([(0.05 + 0.01 * (k % 3), 0.0), (0.035, 0.05), (0.015, 0.05), (0.0, 0.03)], 7, "z", (x, y, 0.4 + 0.2 * max(0.0, 1 - abs(x) / 0.6) - 0.02 * k)), "Metal")
    # the constellation on its back: glowing stars joined by thin lines of light
    stars = [Vector(p) for p in ((0.0, 1.3, 0.78), (0.32, 0.9, 0.78), (-0.25, 0.55, 0.82), (0.2, 0.1, 0.8), (-0.35, -0.35, 0.72), (0.15, -0.8, 0.62), (0.0, -1.3, 0.47))]
    for k, q in enumerate(stars):
        r = 0.07 if k % 2 == 0 else 0.05
        P.obj("Star", hull([q + Vector((r, 0, 0.01)), q - Vector((r, 0, -0.01)), q + Vector((0, r * 1.6, 0.01)), q - Vector((0, r * 1.6, -0.01)), q + Vector((0, 0, 0.04)), q - Vector((0, 0, 0.02))]), "Lamp", 0, False)
    for a, b in zip(stars, stars[1:]):
        P.obj("StarLine", pipe([a + Vector((0, 0, 0.005)), b + Vector((0, 0, 0.005))], [0.012, 0.012], 4), "Glow")
    # the golden harness and the lantern pavilion on its back
    for y, R, H in ((0.65, 0.94, 0.79), (-0.05, 0.9, 0.73)):   # two golden bands round the body, hugging it
        band = ring_on((0, y, 0.0), (0, 1, 0), 1.0, 0.035, 32, 5)
        for v in band.verts: v.co.x = v.co.x * R; v.co.z = v.co.z * H + 0.04
        P.obj("Harness", band, "Trim")
    P.obj("Saddle", lathe([(0.42, 0.0), (0.44, 0.06), (0.4, 0.1), (0.0, 0.1)], 18, "z", (0, 0.3, 0.74)), lambda c, n: "Trim" if c.z > 0.8 else "Accent")
    for k in range(4):
        a = 2 * math.pi * k / 4 + math.pi / 4
        c = Vector((math.sin(a) * 0.3, 0.3 + math.cos(a) * 0.3, 0.84))
        P.obj("Pillar", pipe([c, c + Vector((0, 0, 0.42))], [0.03, 0.03], 6), "Trim")
    P.obj("PavRoof", lathe([(0.46, 1.26), (0.32, 1.36), (0.08, 1.52), (0.0, 1.6)], 16, "z", (0, 0.3, 0)), lambda c, n: "Accent" if c.z < 1.4 else "Trim")
    P.obj("PavLamp", ball((0, 0.3, 1.04), (0.12, 0.12, 0.15), 10, 5), "Lamp")
    P.obj("PavSpire", cone((0, 0.3, 1.58), (0, 0.3, 1.82), 0.03, 6), "Trim", 0, False)
    for s in (1, -1):
        mast = Vector((s * 0.36, 0.3, 1.3))
        P.obj("PennantPole", pipe([mast, mast + Vector((s * 0.05, 0, 0.35))], [0.015, 0.012], 5), "Trim")
        P.part("Cloth", sheet([[tuple(mast + Vector((s * 0.05, 0, 0.33))), tuple(mast + Vector((s * 0.05, -0.38, 0.27))), tuple(mast + Vector((s * 0.05, 0, 0.2)))]], 0.015), "Glow", (0, 0, 0), 0, False)
    # the blowhole and its glowing fountain, arching forward
    P.obj("Blowhole", ball((0, 1.55, 0.68), (0.09, 0.05, 0.02), 8, 3), "Dark")
    for j, side in enumerate((-1, 0, 1)):
        arc = bez((0, 1.55, 0.7), (side * 0.15, 1.6, 1.25), (side * 0.4, 1.8, 1.4), (side * 0.6, 2.0, 1.1), 7)
        for i, q in enumerate(arc[1:]):
            P.obj("Spray", ball(tuple(q), (0.07 - 0.006 * i,) * 3, 6, 3), "Glass" if i % 2 else "Glow")
    P.obj("Dorsal", hull([(0, -0.95, 0.52), (0, -1.45, 0.42), (0, -1.35, 0.78), (0.05, -1.15, 0.5), (-0.05, -1.15, 0.5)]), "Accent", 0, False)
    for s in (1, -1):   # the long humpback fins, scalloped and edged in light, rowing
        name = "FlapR" if s > 0 else "FlapL"
        hub = (s * 0.78, 1.1, -0.3)
        keys = [(0.78, 1.38, 0.9, 0.13, -0.3), (1.4, 1.25, 0.65, 0.09, -0.45), (2.0, 1.05, 0.55, 0.06, -0.55), (2.5, 0.8, 0.5, 0.035, -0.55), (2.7, 0.62, 0.52, 0.02, -0.52)]
        bm = sweep([(x, airfoil(le, te, th, z)) for (x, le, te, th, z) in fine_secs(keys, 0.1)], "x")
        if s < 0: bm = mirror_x(bm)
        def fin(c, n):
            if n.z < -0.3: return "Belly"
            le = 1.38 - (abs(c.x) - 0.78) * 0.4
            if c.y > le - 0.07: return "Glow"   # the bright leading edge
            return "Base"
        P.part(name, bm, fin, hub, 1)
        for k in range(5):   # knobs along the leading edge
            x = 1.0 + k * 0.35
            P.part(name, ball((s * x, 1.36 - (x - 0.78) * 0.37, -0.32 - (x - 0.78) * 0.12), (0.05, 0.05, 0.04), 6, 3), "Base", hub)
    # the fluke: it beats, with glowing tips
    hub = (0, -2.3, 0.2)
    bm = sweep([(x, airfoil(-2.22 - abs(x) * 0.25, -2.8 + abs(x) * 0.12 - (0.14 if abs(x) < 0.15 else 0), 0.08 - abs(x) * 0.045, 0.2 + abs(x) * 0.12)) for x in (-1.3, -1.0, -0.65, -0.3, 0.0, 0.3, 0.65, 1.0, 1.3)], "x")
    P.part("Sway0", bm, lambda c, n: "Belly" if n.z < -0.3 else ("Glow" if abs(c.x) > 1.05 else "Base"), hub, 1)
    # rings of bubbles orbiting it
    for k in range(14):
        a = 2 * math.pi * k / 14
        c = Vector((math.sin(a) * 1.75, math.cos(a) * 2.3, 0.1 + 0.4 * math.sin(a * 3)))
        P.part("SpinBubbles", ball(tuple(c), (0.09 - 0.03 * (k % 2),) * 3, 8, 4), "Glass", (0, 0, 0.1))
        P.part("SpinBubbles", ball(tuple(c + Vector((0.03, 0.03, 0.04))), (0.025,) * 3, 4, 2), "Belly", (0, 0, 0.1))
    P.part("Muzzle", ball((0, 2.62, -0.12), (0.1, 0.05, 0.08), 8, 4), "Glow", (0, 2.62, -0.12))
    return P


# ================================================================= 3. the thunder roc
def S_roc():
    """The thunder roc (2026-10-12, remade: "make them better"): a colossal storm eagle - a fierce white head with a heavy golden brow,
    blazing eyes, a hooked golden beak and a swept crest of storm-blue plumes, a shaggy ruff, a golden breastplate with a lightning
    emblem, broad wings built of layered feathers - white coverts, storm-blue primaries splayed at the tips - with lightning crackling
    across them, a fanned tail, golden talons clutching a thunderbolt, and storm clouds full of lightning circling it."""
    P = Boss("roc", {"Base": ((0.96, 0.97, 0.99), 0.4), "Belly": ((0.78, 0.82, 0.90), 0.35), "Accent": ((0.12, 0.30, 0.75), 0.5),
                     "Trim": ((1.0, 0.76, 0.20), 0.85), "Glass": ((0.55, 0.85, 1.0), 0.95), "Dark": ((0.05, 0.06, 0.10), 0.5),
                     "Glow": ((0.45, 0.92, 1.0), 0.5), "Metal": ((0.40, 0.44, 0.55), 0.5), "Lamp": ((1.0, 0.92, 0.30), 0.8)})
    P.obj("Body", loft([(1.45, 0.24, 0.24, 0, 0.42), (1.15, 0.38, 0.4, 0, 0.3), (0.55, 0.55, 0.52, 0, 0.08), (-0.3, 0.5, 0.45, 0, 0.0),
                        (-1.0, 0.32, 0.28, 0, 0.02), (-1.4, 0.15, 0.1, 0, 0.06)], 18), lambda c, n: "Belly" if n.z < -0.3 else "Base", 1)
    # the shaggy ruff where the neck meets the body
    for ring, (y, R) in enumerate(((1.2, 0.36), (1.0, 0.44))):
        for k in range(16):
            a = 2 * math.pi * (k + 0.5 * ring) / 16
            b = Vector((math.sin(a) * R, y, 0.38 + math.cos(a) * R * 0.9))
            P.obj("Ruff", cone(b, b + Vector((math.sin(a) * 0.18, -0.25, math.cos(a) * 0.15)), 0.09, 4), "Base" if math.cos(a) > -0.2 else "Belly", 0, False)
    # the golden breastplate with a lightning emblem
    P.obj("Breastplate", ball((0, 0.95, 0.12), (0.4, 0.22, 0.38), 16, 8), lambda c, n: "Trim" if n.y > 0.1 else None, 0)
    P.obj("Emblem", bolt((0.06, 1.17, 0.4), (-0.06, 1.17, -0.12), 0.035, 4), "Glow")
    for s in (1, -1):
        P.obj("Rivet", ball((s * 0.3, 1.08, 0.2), (0.035,) * 3, 6, 3), "Metal")
        P.obj("Rivet", ball((s * 0.28, 1.06, -0.05), (0.035,) * 3, 6, 3), "Metal")
    # the head
    P.obj("Head", ball((0, 1.58, 0.55), (0.33, 0.4, 0.33), 16, 8), "Base", 1)
    P.obj("Beak", pipe(bez((0, 1.88, 0.58), (0, 2.25, 0.6), (0, 2.5, 0.48), (0, 2.52, 0.28), 7), [0.15, 0.13, 0.11, 0.085, 0.06, 0.04, 0.02, 0.0], 10), "Trim")
    P.obj("BeakLow", pipe([(0, 1.9, 0.44), (0, 2.22, 0.4), (0, 2.34, 0.38)], [0.09, 0.05, 0.0], 8), "Trim")
    P.obj("Cere", ball((0, 1.92, 0.66), (0.14, 0.1, 0.06), 10, 4), "Trim")
    for s in (1, -1):
        P.obj("Nostril", ball((s * 0.06, 2.08, 0.66), (0.02, 0.03, 0.015), 6, 3), "Dark")
        P.obj("Socket", ball((s * 0.2, 1.8, 0.66), (0.09, 0.1, 0.07), 10, 5), "Dark")
        P.obj("Eye", ball((s * 0.215, 1.83, 0.66), (0.07, 0.08, 0.055), 10, 5), "Lamp")
        P.obj("Pupil", ball((s * 0.25, 1.88, 0.66), (0.025, 0.03, 0.035), 6, 3), "Dark")
        P.obj("Brow", hull([(s * 0.04, 1.95, 0.76), (s * 0.34, 1.75, 0.8), (s * 0.34, 1.7, 0.73), (s * 0.06, 1.9, 0.7), (s * 0.2, 1.9, 0.82)]), "Trim", 0, False)
        for k in range(4):   # the swept crest of storm-blue plumes
            r0 = Vector((s * (0.04 + 0.07 * k), 1.6 - 0.05 * k, 0.8 - 0.04 * k))
            P.obj("Crest", pipe(bez(r0, r0 + Vector((s * 0.05, -0.25, 0.25)), r0 + Vector((s * (0.1 + 0.06 * k), -0.6, 0.35)), r0 + Vector((s * (0.15 + 0.08 * k), -0.85 + 0.08 * k, 0.5 - 0.08 * k)), 6),
                                [0.07, 0.07, 0.06, 0.05, 0.035, 0.02, 0.0], 6), "Accent" if k % 2 == 0 else "Glow")
        for k in range(3):   # cheek feathers
            b = Vector((s * 0.28, 1.5 - k * 0.08, 0.45 - k * 0.06))
            P.obj("Cheek", cone(b, b + Vector((s * 0.2, -0.22, -0.05)), 0.07, 4), "Base", 0, False)
        # golden talons clutching a thunderbolt
        for k in (-1, 0, 1):
            P.obj("Talon", pipe(bez((s * 0.22, 0.05, -0.35), (s * (0.24 + k * 0.05), 0.2, -0.6), (s * (0.2 + k * 0.08), 0.42, -0.66), (s * (0.12 + k * 0.06), 0.5, -0.56), 4), [0.045, 0.04, 0.03, 0.02, 0.0], 6), "Trim")
        P.obj("Leg", pipe([(s * 0.25, -0.05, -0.15), (s * 0.23, 0.03, -0.4)], [0.09, 0.07], 8), "Belly")
        # the wings: a sweep of white coverts, then layered storm-blue primaries; lightning crackles across them
        name = "FlapR" if s > 0 else "FlapL"
        hub = (s * 0.42, 0.45, 0.28)
        keys = [(0.4, 1.0, -0.4, 0.17, 0.28), (1.2, 0.98, -0.55, 0.11, 0.45), (2.0, 0.78, -0.5, 0.07, 0.62), (2.6, 0.5, -0.35, 0.04, 0.72)]
        bm = sweep([(x, airfoil(le, te, th, z)) for (x, le, te, th, z) in fine_secs(keys)], "x")
        if s < 0: bm = mirror_x(bm)
        def plume(c, n):
            if n.z < -0.3: return "Belly"
            x = abs(c.x)
            if c.y > 0.92 - (x - 0.4) * 0.2: return "Trim"   # a golden leading edge
            if c.y < -0.25 - (x - 0.4) * 0.05: return "Accent"
            return "Base"
        P.part(name, bm, plume, hub, 0)
        for row, (y0, L, slot) in enumerate(((-0.3, 0.55, "Base"), (-0.45, 0.75, "Accent"))):   # rows of long feathers along the trailing edge
            for k in range(9):
                x = 0.55 + k * 0.25
                y = y0 + 0.12 * (x / 2.6) ** 2 + (0.35 if x > 2.2 else 0.0) * (x - 2.2) * 1.5
                z = 0.3 + (x - 0.4) * 0.2 - row * 0.02
                a = math.radians(-8 - k * 4)
                tip = Vector((s * (x + math.sin(-a) * L * 0.4), y - L, z + 0.02))
                P.part(name, hull([(s * (x - 0.13), y + 0.1, z), (s * (x + 0.13), y + 0.1, z), tuple(tip), (s * x, y + 0.05, z + 0.025), (s * x, y - L * 0.6, z + 0.02)]), slot, hub, 0, False)
        for k in range(6):   # the primaries splayed at the wing tip like fingers
            x0 = 2.45 + k * 0.08; y0 = 0.45 - k * 0.17
            tip = Vector((s * (x0 + 0.85 - k * 0.07), y0 - 0.1 - k * 0.12, 0.78 + 0.03 * k))
            P.part(name, hull([(s * x0, y0 + 0.08, 0.72), (s * x0, y0 - 0.08, 0.72), tuple(tip), (s * (x0 + 0.3), y0, 0.76), (s * (x0 + 0.3), y0 - 0.04, 0.74)]), "Accent", hub, 0, False)
        for j in range(2):   # lightning crackling across the wing
            P.part(name, bolt((s * (0.9 + j * 0.7), 0.6 - j * 0.15, 0.42 + j * 0.15), (s * (1.7 + j * 0.8), 0.15 - j * 0.2, 0.62 + j * 0.06), 0.03, 5, j), "Glow", hub)
    # the thunderbolt in its talons
    P.obj("Thunderbolt", bolt((-0.7, 0.55, -0.62), (0.7, 0.45, -0.62), 0.07, 6), "Lamp")
    for k in range(7):   # the tail fan, blue tipped
        a = math.radians(-42 + k * 14)
        P.obj("TailFeather", hull([(math.sin(a) * 0.15, -1.35, 0.1), (math.sin(a) * 0.15 + 0.08, -1.35, 0.08), (math.sin(a) * 0.85, -1.35 - math.cos(a) * 0.95, 0.12),
                                   (math.sin(a) * 0.85 + 0.12 * math.cos(a), -1.35 - math.cos(a) * 0.95 + 0.1, 0.1), (math.sin(a) * 0.5, -1.35 - math.cos(a) * 0.5, 0.14)]),
              lambda c, n: "Accent" if c.y < -2.0 else "Base", 0, False)
    # storm clouds circling it, lightning dropping from them
    for k in range(5):
        a = 2 * math.pi * k / 5 + 0.3
        c = Vector((math.sin(a) * 2.2, -0.2 + math.cos(a) * 1.8, -0.2 + 0.25 * math.sin(a * 2)))
        for j in range(4):
            P.part("SpinStorm", ball(tuple(c + Vector(((j - 1.5) * 0.17, 0, 0.05 * (j % 2)))), (0.17 + 0.04 * (j % 2), 0.14, 0.12), 8, 4), "Metal", (0, -0.2, 0))
        P.part("SpinStorm", bolt(c + Vector((0, 0, -0.1)), c + Vector((0.08, 0, -0.6)), 0.03, 3, k), "Lamp", (0, -0.2, 0))
    P.part("Muzzle", ball((0, 2.5, 0.3), (0.08, 0.05, 0.07), 8, 4), "Glow", (0, 2.5, 0.3))
    return P


# ================================================================= 5. the citadel turtle
def S_turtle():
    """The last boss, the citadel turtle (2026-10-12, remade: "make them better"): an ancient giant sea turtle, wise and stern - heavy
    brows, glowing sea-green eyes, a barnacle beard, a golden circlet with a pearl - carrying a whole white-and-gold sea citadel on its
    domed, ridged shell: a curtain wall with six round towers flying blue banners, cannons pointing out at the player, a gatehouse with a
    glowing portcullis, a tall inner keep and a lighthouse whose beam turns; waterfalls pour off the shell's rim, glowing coral and
    palms grow on it, golden armour bands wrap its great flippers, and gulls circle the towers."""
    P = Boss("turtle", {"Base": ((0.18, 0.46, 0.42), 0.5), "Belly": ((0.92, 0.86, 0.66), 0.4), "Accent": ((0.50, 0.32, 0.16), 0.55),
                        "Trim": ((0.98, 0.76, 0.24), 0.85), "Glass": ((0.45, 0.85, 1.0), 0.95), "Dark": ((0.05, 0.05, 0.06), 0.5),
                        "Glow": ((0.55, 1.0, 0.95), 0.5), "Metal": ((0.95, 0.94, 0.90), 0.45), "Lamp": ((1.0, 0.55, 0.45), 0.8)})
    YS = 1.2   # the shell is longer than wide
    shell = lathe([(0.0, 0.8), (0.5, 0.76), (0.95, 0.6), (1.3, 0.36), (1.5, 0.1), (1.55, -0.02), (1.45, -0.08)], 40, "z")
    for v in shell.verts: v.co.y *= YS
    def scutes(c, n):
        r = math.hypot(c.x, c.y / YS)
        if r > 1.5: return "Trim" if (ang(Vector((c.x, c.y / YS, 0))) / (2 * math.pi) * 20) % 1.0 < 0.5 else "Belly"   # a gold-and-cream rim
        if 0.62 < r < 1.48 and ((r * 2.4) % 1.0 < 0.08 or (ang(Vector((c.x, c.y / YS, 0))) / (2 * math.pi) * 10) % 1.0 < 0.05): return "Dark"
        return "Accent"
    P.obj("Shell", shell, scutes)
    for k in range(10):   # raised ridges on the scutes
        a = 2 * math.pi * (k + 0.5) / 10
        c = Vector((math.sin(a) * 1.15, math.cos(a) * 1.15 * YS, 0.47))
        P.obj("Scute", ball(tuple(c), (0.24, 0.24 * YS, 0.08), 8, 4), "Accent")
    P.obj("Plastron", ball((0, 0, -0.1), (1.38, 1.7, 0.34), 24, 8), lambda c, n: "Belly" if (c.y * 3) % 1.0 > 0.08 else "Accent")
    # the head: ancient and stern
    P.obj("Neck", pipe([(0, 1.5, -0.05), (0, 1.9, 0.02), (0, 2.15, 0.12)], [0.34, 0.3, 0.28], 14), lambda c, n: "Belly" if n.z < -0.3 else "Base", 1)
    for k in range(3):
        P.obj("NeckFold", ring_on((0, 1.65 + k * 0.17, 0.0 + k * 0.03), (0, 1, 0.1), 0.31, 0.03, 16, 4), "Base")
    P.obj("Head", ball((0, 2.38, 0.18), (0.38, 0.44, 0.32), 18, 9), lambda c, n: "Belly" if n.z < -0.45 else "Base", 1)
    P.obj("Beak", hull([(0, 2.85, 0.1), (0.17, 2.66, 0.05), (-0.17, 2.66, 0.05), (0, 2.72, -0.08), (0.14, 2.55, 0.22), (-0.14, 2.55, 0.22), (0, 2.78, 0.22)]), "Accent", 0, False)
    P.obj("MouthLine", pipe(bez((-0.3, 2.45, -0.02), (-0.15, 2.7, 0.02), (0.15, 2.7, 0.02), (0.3, 2.45, -0.02), 8), [0.02] * 9, 5), "Dark")
    for s in (1, -1):
        e = Vector((s * 0.25, 2.55, 0.28))
        P.obj("EyeWhite", ball(tuple(e), (0.1, 0.07, 0.08), 10, 5), "Belly")
        P.obj("Iris", ball(tuple(e + Vector((s * 0.01, 0.045, 0))), (0.065, 0.035, 0.065), 10, 5), "Glow")
        P.obj("Pupil", ball(tuple(e + Vector((s * 0.01, 0.07, 0))), (0.03, 0.02, 0.035), 6, 3), "Dark")
        P.obj("Brow", hull([(s * 0.08, 2.66, 0.38), (s * 0.4, 2.48, 0.42), (s * 0.4, 2.45, 0.35), (s * 0.1, 2.62, 0.32), (s * 0.25, 2.6, 0.44)]), "Accent", 0, False)
    for k in range(9):   # the barnacle beard under the chin
        a = math.radians(-60 + k * 15)
        P.obj("Beard", lathe([(0.045, 0.0), (0.03, 0.05), (0.012, 0.05)], 6, "z", (math.sin(a) * 0.22, 2.5 + math.cos(a) * 0.12, -0.12 - 0.03 * (k % 2))), "Metal")
    P.obj("Circlet", ring_on((0, 2.34, 0.3), (0, 0.3, 1), 0.36, 0.04, 24, 5), "Trim")
    P.obj("Pearl", ball((0, 2.62, 0.47), (0.07, 0.05, 0.07), 10, 5), "Belly")
    P.obj("PearlSet", ring_on((0, 2.6, 0.47), (0, 1, 0), 0.075, 0.02, 12, 4), "Trim")
    # flippers: front ones row the air (gold armour bands), back ones still
    for s in (1, -1):
        P.obj("BackFlipper", hull([(s * 0.9, -1.5, -0.1), (s * 0.7, -1.6, -0.12), (s * 1.5, -2.15, -0.2), (s * 1.3, -2.25, -0.18), (s * 0.85, -1.55, 0.0)]), "Base", 0, False)
        name = "FlapR" if s > 0 else "FlapL"
        hub = (s * 1.1, 1.0, -0.12)
        keys = [(1.1, 1.3, 0.65, 0.16, -0.12), (1.8, 1.25, 0.75, 0.11, -0.17), (2.5, 1.0, 0.65, 0.07, -0.22), (3.0, 0.6, 0.48, 0.03, -0.24)]
        bm = sweep([(x, airfoil(le, te, th, z)) for (x, le, te, th, z) in keys], "x")
        if s < 0: bm = mirror_x(bm)
        P.part(name, bm, lambda c, n: "Belly" if n.z < -0.3 else ("Trim" if 1.55 < abs(c.x) < 1.68 or 2.1 < abs(c.x) < 2.2 else ("Dark" if speckle(c, 3.0) < 0.08 else "Base")), hub, 1)
    P.obj("Tail", cone((0, -1.95, -0.05), (0, -2.4, -0.12), 0.13, 8), "Base", 0, False)
    # waterfalls pouring off the shell rim, white foam where they break
    for k in range(6):
        a = 2 * math.pi * (k + 0.5) / 6 + 0.25
        if math.cos(a) > 0.7: continue   # leave the front clear
        top = Vector((math.sin(a) * 1.3, math.cos(a) * 1.3 * YS, 0.38))
        out = Vector((math.sin(a), math.cos(a), 0))
        side = Vector((math.cos(a), -math.sin(a), 0)) * 0.13
        pts = bez(top, top + out * 0.3 + Vector((0, 0, 0.05)), top + out * 0.42 + Vector((0, 0, -0.4)), top + out * 0.45 + Vector((0, 0, -0.85)), 6)
        polys = [[tuple(p - side), tuple(p + side), tuple(q + side * 1.2), tuple(q - side * 1.2)] for p, q in zip(pts, pts[1:])]
        P.part("Cloth", sheet(polys, 0.02), lambda c, n: "Glass", (0, 0, 0), 0, False)
        for j in range(3):
            P.obj("Foam", ball(tuple(pts[-1] + side * (j - 1) * 0.9), (0.08, 0.08, 0.06), 6, 3), "Belly")
    # coral and palms on the shell
    for k in range(8):
        a = k * 2.399 + 0.4; r = 0.95 + 0.25 * (k % 3) / 2
        if math.cos(a) > 0.75: continue
        base = Vector((math.sin(a) * r, math.cos(a) * r * YS, 0.62 - (r - 0.95) * 0.9))
        for j in range(3):
            d = Vector((math.sin(a + j * 2.1) * 0.12, math.cos(a + j * 2.1) * 0.12, 0.25 + 0.06 * j))
            P.obj("Coral", cone(base, base + d, 0.045, 5), "Lamp" if k % 2 == 0 else "Glow", 0, False)
            P.obj("CoralTip", ball(tuple(base + d), (0.045,) * 3, 6, 3), "Lamp" if k % 2 == 0 else "Glow")
    for (px, py) in ((-0.95, -0.65), (1.0, -0.5), (-0.4, -1.2)):
        b = Vector((px, py * YS, 0.55))
        top = b + Vector((0.1, 0.0, 0.6))
        P.obj("PalmTrunk", pipe(bez(b, b + Vector((0, 0, 0.3)), top + Vector((-0.05, 0, -0.1)), top, 5), [0.05, 0.045, 0.04, 0.035, 0.03, 0.03], 6), "Accent")
        for j in range(6):
            a = 2 * math.pi * j / 6
            tip = top + Vector((math.sin(a) * 0.42, math.cos(a) * 0.42, -0.2))
            mid = (top + tip) * 0.5 + Vector((0, 0, 0.1))
            side = Vector((math.cos(a), -math.sin(a), 0)) * 0.08
            P.obj("PalmLeaf", sheet([[tuple(top), tuple(mid + side), tuple(tip)], [tuple(top), tuple(tip), tuple(mid - side)]], 0.015), "Base", 0, False)
    # the citadel: curtain wall, six towers with banners, gatehouse, cannons, the keep and the lighthouse
    wall = lambda c, n: "Glass" if 0.86 < c.z < 0.96 and (ang(c) / (2 * math.pi) * 28) % 1.0 < 0.35 else "Metal"
    P.obj("Wall", lathe([(0.82, 0.6), (0.82, 1.08), (0.74, 1.08), (0.74, 0.9), (0.0, 0.9)], 32, "z"), wall)
    for k in range(20):
        a = 2 * math.pi * k / 20
        P.obj("Merlon", box((math.sin(a) * 0.79, math.cos(a) * 0.79, 1.13), (0.1, 0.07, 0.1), Matrix.Rotation(-a, 3, "Z")), "Metal", 0, False)
    for k in range(6):
        a = 2 * math.pi * k / 6 + math.pi / 6
        c = (math.sin(a) * 0.82, math.cos(a) * 0.82, 0.55)
        P.obj("Tower", lathe([(0.18, 0.0), (0.18, 0.72), (0.23, 0.74), (0.23, 0.8)], 14, "z", c), lambda cc, n: "Trim" if cc.z > 1.27 else "Metal")
        P.obj("TowerWin", box((c[0] * 1.22, c[1] * 1.22, 1.05), (0.06, 0.06, 0.12), Matrix.Rotation(-a, 3, "Z")), "Lamp", 0, False)
        P.obj("Roof", lathe([(0.27, 0.8), (0.12, 0.98), (0.0, 1.18)], 14, "z", c), "Trim")
        pole = Vector(c) + Vector((0, 0, 1.18))
        P.obj("FlagPole", pipe([pole, pole + Vector((0, 0, 0.32))], [0.012, 0.01], 4), "Trim")
        P.part("Cloth", sheet([[tuple(pole + Vector((0, 0, 0.31))), tuple(pole + Vector((0.0, -0.32, 0.27))), tuple(pole + Vector((0, -0.26, 0.2))), tuple(pole + Vector((0, 0, 0.18)))]], 0.015), "Glass", (0, 0, 0), 0, False)
    P.obj("Gatehouse", box((0, 0.84, 0.88), (0.42, 0.2, 0.56)), "Metal", 0, False)
    P.obj("GateArch", box((0, 0.95, 0.8), (0.22, 0.03, 0.3)), "Dark", 0, False)
    for k in range(4):
        P.obj("Portcullis", box(((k - 1.5) * 0.05, 0.965, 0.8), (0.015, 0.02, 0.3)), "Glow", 0, False)
    for s in (-1, 0, 1):
        P.obj("GateMerlon", box((s * 0.15, 0.84, 1.2), (0.09, 0.2, 0.09)), "Metal", 0, False)
    for s in (1, -1):   # cannons pointing at the player
        for z in (0.78, 1.0):
            base = Vector((s * 0.42, 0.72, z))
            P.obj("Cannon", pipe([base, base + Vector((s * 0.05, 0.3, 0.02))], [0.065, 0.05], 10), "Dark")
            P.obj("CannonRim", ring_on(base + Vector((s * 0.05, 0.3, 0.02)), (0, 1, 0), 0.055, 0.015, 10, 4), "Trim")
    P.obj("Keep", box((0, -0.15, 1.12), (0.7, 0.62, 0.45)), lambda c, n: "Lamp" if 1.15 < c.z < 1.25 and abs(n.z) < 0.5 and (c.x * 5 + c.y * 5) % 1.0 < 0.5 else "Metal", 0, False)
    for sx in (1, -1):
        for sy in (1, -1):
            P.obj("KeepTurret", lathe([(0.1, 0.0), (0.1, 0.3), (0.0, 0.48)], 10, "z", (sx * 0.35, -0.15 + sy * 0.31, 1.3)), lambda c, n: "Trim" if c.z > 1.6 else "Metal")
    P.obj("KeepRoof", hull([(-0.35, -0.46, 1.34), (0.35, -0.46, 1.34), (-0.35, 0.16, 1.34), (0.35, 0.16, 1.34), (0, -0.15, 1.6)]), "Trim", 0, False)
    P.obj("Lighthouse", lathe([(0.24, 1.3), (0.18, 2.15), (0.24, 2.18), (0.24, 2.22)], 16, "z", (0, -0.15, 0)),
          lambda c, n: "Accent" if (c.z * 5.0) % 1.0 < 0.5 and c.z < 2.15 else "Metal")
    P.obj("Lantern", lathe([(0.15, 2.22), (0.15, 2.45), (0.0, 2.45)], 12, "z", (0, -0.15, 0)), "Glow")
    for k in range(6):
        a = 2 * math.pi * k / 6
        P.obj("LanternBar", pipe([(math.sin(a) * 0.16, -0.15 + math.cos(a) * 0.16, 2.22), (math.sin(a) * 0.16, -0.15 + math.cos(a) * 0.16, 2.45)], [0.012, 0.012], 4), "Trim")
    P.obj("Cupola", lathe([(0.22, 2.45), (0.1, 2.6), (0.0, 2.72)], 12, "z", (0, -0.15, 0)), "Trim")
    P.obj("Spire", cone((0, -0.15, 2.7), (0, -0.15, 2.95), 0.03, 6), "Trim", 0, False)
    for s in (1, -1):   # the beam, turning
        P.part("SpinBeam", hull([(0, -0.15, 2.33), (0, -0.15 + s * 0.12, 2.27), (0, -0.15 + s * 0.12, 2.39), (0, -0.15 + s * 1.4, 2.13), (0, -0.15 + s * 1.4, 2.53), (0.06, -0.15 + s * 1.4, 2.33), (-0.06, -0.15 + s * 1.4, 2.33)]),
               "Glow", (0, -0.15, 2.33), 0, False)
    # gulls circling the towers
    for k in range(6):
        a = 2 * math.pi * k / 6
        c = Vector((math.sin(a) * 1.45, -0.15 + math.cos(a) * 1.45, 1.75 + 0.2 * math.sin(a * 2)))
        t = Vector((math.cos(a), -math.sin(a), 0))
        side = Vector((math.sin(a), math.cos(a), 0))
        P.part("SpinGulls", ball(tuple(c), (0.05, 0.05, 0.05), 6, 3), "Metal", (0, -0.15, 1.75))
        for w in (1, -1):
            P.part("SpinGulls", sheet([[tuple(c), tuple(c + side * w * 0.22 + Vector((0, 0, 0.08)) + t * 0.04), tuple(c + side * w * 0.12 - t * 0.06)]], 0.015), "Metal", (0, -0.15, 1.75), 0, False)
    P.part("Muzzle", ball((0, 2.86, 0.05), (0.09, 0.05, 0.07), 8, 4), "Glow", (0, 2.86, 0.05))
    return P


# ================================================================= 2. the sky galleon
def S_galleon(pid="galleon", pal=None, hell=False):
    """A flying galleon: a dark wooden hull with a red bottom and gold rails, a castle at the stern with lit windows, three masts of bellied
    cream sails with red crosses, a gilded figurehead under the bowsprit, a row of cannon each side, glowing keel engines, two stern
    propellers - and canvas wings on gilded ribs that beat at its sides.
    hell (lava_bosses.py, the hellfire galleon): its own palette, the sails' crosses burning, flames along the rails, a horned skull at the bow."""
    P = Boss(pid, pal or {"Base": ((0.33, 0.19, 0.10), 0.35), "Belly": ((0.95, 0.91, 0.80), 0.25), "Accent": ((0.72, 0.13, 0.10), 0.4),
                          "Trim": ((0.96, 0.74, 0.24), 0.7), "Glass": ((0.55, 0.38, 0.22), 0.3), "Dark": ((0.06, 0.05, 0.05), 0.3),
                          "Glow": ((0.30, 0.95, 1.0), 0.5), "Metal": ((0.22, 0.22, 0.24), 0.6), "Lamp": ((1.0, 0.72, 0.30), 0.8)})
    cross = "Glow" if hell else "Accent"
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
                  lambda c, n, y=y, z0=z0, z1=z1: cross if (abs(c.x) < 0.07 or abs(c.z - (z0 + z1) * 0.5) < 0.06) else "Belly", (0, 0, 0), 0, False)
        P.obj("Nest", lathe([(0.16, 0.0), (0.16, 0.12), (0.0, 0.12)], 10, "z", (0, y, 0.45 + h * 0.62)), "Base")
        P.part("Cloth", grid((0, y, 0.45 + h + 0.15), (0, -0.45, 0.0), (0, 0, 0.2), 4, 2, Vector((0.06, 0, 0))), "Accent", (0, 0, 0), 0, False)
    P.obj("Bowsprit", pipe([(0, 2.0, 0.45), (0, 2.95, 0.85)], [0.05, 0.03], 8), "Base")
    P.part("Cloth", grid((0, 2.0, 0.55), (0, 0.85, 0.32), (0, -0.85, 1.25), 4, 4, Vector((0.12, 0, 0))), "Belly", (0, 0, 0), 0, False)
    if hell:   # a horned skull with burning eyes, and flames all along the rails
        P.obj("Skull", ball((0, 2.38, 0.24), (0.17, 0.18, 0.17), 12, 6), "Trim")
        P.obj("SkullJaw", box((0, 2.45, 0.1), (0.18, 0.12, 0.08)), "Trim", 0, False)
        for s2 in (1, -1):
            P.obj("SkullEye", ball((s2 * 0.07, 2.53, 0.27), (0.045, 0.03, 0.04), 8, 4), "Glow")
            P.obj("SkullHorn", pipe(bez((s2 * 0.12, 2.35, 0.36), (s2 * 0.3, 2.3, 0.45), (s2 * 0.38, 2.4, 0.62), (s2 * 0.32, 2.55, 0.72), 5), [0.05, 0.045, 0.035, 0.025, 0.012, 0.0], 6), "Dark")
            for k in range(7):
                P.obj("RailFlame", cone((s2 * 0.5, 1.5 - k * 0.5, 0.6), (s2 * 0.52, 1.45 - k * 0.5, 0.82 + 0.06 * (k % 2)), 0.06, 5), "Glow", 0, False)
    else:
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


# >>> 2026-10-11 new

# ================================================================= 2026-10-11: the new second ("new bosses with a new shape, with a face, grand,
# that suit the world"): the pufferfish emperor
def S_puffer():
    """The emperor of the sky sea: a great royal-blue pufferfish puffed up round, bristling with golden spines, a cream belly, big proud
    heavy-lidded eyes under arched gold brows, a puckered coral mouth under a white handlebar moustache, a tall jewelled imperial crown,
    a crimson sash with a gold medal, a string of pearls, little fins fluttering and a fan tail sweeping."""
    import random
    P = Boss("puffer", {"Base": ((0.10, 0.32, 0.78), 0.5), "Belly": ((0.98, 0.94, 0.80), 0.4), "Accent": ((0.78, 0.07, 0.16), 0.55),
                        "Trim": ((0.98, 0.76, 0.22), 0.85), "Glass": ((0.98, 0.98, 0.98), 0.7), "Dark": ((0.04, 0.05, 0.10), 0.6),
                        "Glow": ((0.35, 0.90, 1.0), 0.6), "Metal": ((0.97, 0.95, 0.92), 0.7), "Lamp": ((1.0, 1.0, 0.9), 0.9)})
    R = Vector((1.15, 1.05, 1.0))
    def skin(c, n):
        return "Belly" if n.z < -0.35 else "Base"
    P.obj("Body", ball((0, 0, 0), tuple(R), 24, 12), skin, 1)
    rng = random.Random(5)
    for k in range(40):   # round cream spots over his back and flanks
        d = Vector((rng.uniform(-1, 1), rng.uniform(-1, 0.35), rng.uniform(-0.2, 1))).normalized()
        if d.z > 0.75: continue
        p = Vector((d.x * R.x, d.y * R.y, d.z * R.z)) * 1.0
        r = rng.uniform(0.05, 0.09)
        sp = ball((0, 0, 0), (r, r, r * 0.3), 8, 4)
        P.obj("Spot", xf(sp, d.to_track_quat("Z", "Y").to_matrix().to_4x4(), tuple(p)), "Belly")
    # golden spines all over except the face
    N = 90; ga = math.pi * (3 - math.sqrt(5))
    for i in range(N):
        z = 1 - 2 * (i + 0.5) / N; r = math.sqrt(1 - z * z); a = ga * i
        d = Vector((math.cos(a) * r, math.sin(a) * r, z))
        if d.y > 0.45 and d.z > -0.75: continue
        if d.z > 0.8 and d.y > -0.3: continue      # leave the crown its seat
        p = Vector((d.x * R.x, d.y * R.y, d.z * R.z)) * 0.97
        P.obj("Spine", cone(tuple(p), tuple(p + d * 0.32), 0.07, 5), "Trim", 0, False)
    # the face
    for s in (1, -1):
        e = Vector((s * 0.42, 0.88, 0.3))
        P.obj("Eye", ball(tuple(e), (0.27, 0.22, 0.27), 16, 8), "Glass")
        P.obj("Iris", ball(tuple(e + Vector((-s * 0.02, 0.19, -0.03))), (0.14, 0.05, 0.15), 12, 6), "Base")
        P.obj("Pupil", ball(tuple(e + Vector((-s * 0.02, 0.23, -0.03))), (0.08, 0.03, 0.09), 10, 5), "Dark")
        P.obj("Glint", ball(tuple(e + Vector((-s * 0.06, 0.25, 0.04))), (0.035, 0.02, 0.035), 6, 3), "Lamp")
        P.obj("Lid", ball(tuple(e + Vector((0, 0.02, 0.1))), (0.3, 0.25, 0.19), 16, 8), "Base", 1)
        P.obj("Brow", pipe(bez(tuple(e + Vector((-s * 0.25, 0.17, 0.25))), tuple(e + Vector((-s * 0.05, 0.22, 0.42))), tuple(e + Vector((s * 0.2, 0.17, 0.42))),
                               tuple(e + Vector((s * 0.33, 0.05, 0.3))), 8), [0.04, 0.05, 0.06, 0.06, 0.05, 0.04, 0.03, 0.02, 0.01], 8), "Trim")
        # the handlebar moustache, curling up at the ends
        P.obj("Moustache", pipe(bez((s * 0.04, 1.12, -0.02), (s * 0.3, 1.1, -0.12), (s * 0.55, 1.0, 0.0), (s * 0.5, 0.95, 0.18), 10),
                                [0.07, 0.09, 0.09, 0.08, 0.07, 0.06, 0.05, 0.04, 0.03, 0.02, 0.0], 8), "Metal")
        P.obj("Cheek", ball((s * 0.68, 0.8, -0.1), (0.14, 0.06, 0.09), 10, 5), "Accent")
    P.obj("Lips", torus(0.12, 0.06, 0.0, 16, 6), "Accent"); P.parts[-1].data.transform(Matrix.Translation((0, 1.07, -0.22)) @ Matrix.Rotation(math.radians(90), 4, "X"))
    P.obj("MouthIn", ball((0, 1.08, -0.22), (0.08, 0.04, 0.08), 8, 4), "Dark")
    # the imperial crown
    cc = Vector((0, 0.05, 0.92))
    P.obj("CrownBand", lathe([(0.0, 0.0), (0.45, 0.0), (0.47, 0.22), (0.44, 0.23), (0.42, 0.04)], 24, "z", tuple(cc)), "Trim")
    P.obj("CrownVelvet", ball(tuple(cc + Vector((0, 0, 0.2))), (0.4, 0.4, 0.38), 16, 8), "Accent", 1)
    for k in range(4):   # the arches over the velvet, an orb and cross on top
        a = math.pi * k / 4
        P.obj("Arch", pipe(bez(tuple(cc + Vector((math.cos(a) * 0.45, math.sin(a) * 0.45, 0.22))), tuple(cc + Vector((math.cos(a) * 0.45, math.sin(a) * 0.45, 0.62))),
                                   tuple(cc + Vector((-math.cos(a) * 0.45, -math.sin(a) * 0.45, 0.62))), tuple(cc + Vector((-math.cos(a) * 0.45, -math.sin(a) * 0.45, 0.22))), 12), [0.035] * 13, 6), "Trim")
    P.obj("Orb", ball(tuple(cc + Vector((0, 0, 0.7))), (0.1, 0.1, 0.1), 10, 5), "Trim")
    P.obj("Cross", box(tuple(cc + Vector((0, 0, 0.88))), (0.04, 0.04, 0.2)), "Trim", 0, False)
    P.obj("Cross", box(tuple(cc + Vector((0, 0, 0.9))), (0.14, 0.04, 0.04)), "Trim", 0, False)
    for k in range(12):   # jewels round the band
        a = 2 * math.pi * k / 12
        P.obj("Jewel", ball(tuple(cc + Vector((math.sin(a) * 0.47, math.cos(a) * 0.47, 0.11))), (0.05, 0.05, 0.05), 8, 4), "Glow" if k % 2 else "Accent")
        P.obj("CrownPoint", cone(tuple(cc + Vector((math.sin(a) * 0.45, math.cos(a) * 0.45, 0.22))), tuple(cc + Vector((math.sin(a) * 0.47, math.cos(a) * 0.47, 0.36))), 0.05, 5), "Trim", 0, False)
        P.obj("Pearl", ball(tuple(cc + Vector((math.sin(a) * 0.47, math.cos(a) * 0.47, 0.37))), (0.035, 0.035, 0.035), 6, 3), "Metal")
    # the sash across his front with a gold medal, a string of pearls under his chin
    def onto(v, k=1.03):
        """the point on the body in the direction of v, k times out."""
        v = Vector(v); f = 1 / math.sqrt((v.x / R.x) ** 2 + (v.y / R.y) ** 2 + (v.z / R.z) ** 2)
        return v * f * k
    sdir = lambda t: (math.cos(t), math.sin(t), -0.6 * math.sin(t) + 0.35 * math.cos(t))
    sash = [onto(sdir(math.radians(-15 + i * 7.5))) for i in range(29)]
    P.obj("Sash", pipe(sash, [0.08] * len(sash), 8), "Accent")
    m = onto(sdir(math.radians(125)), 1.06)
    P.obj("Medal", ball(tuple(m), (0.14, 0.06, 0.14), 12, 6), "Trim")
    P.obj("MedalGem", ball(tuple(onto(sdir(math.radians(125)), 1.1)), (0.07, 0.03, 0.07), 8, 4), "Glow")
    for k in range(17):
        a = math.radians(-64 + k * 8)
        P.obj("Pearl", ball(tuple(onto((math.sin(a), math.cos(a), -0.55), 1.04)), (0.06, 0.06, 0.06), 8, 4), "Metal")
    # fins fluttering at his sides, a fan tail
    for s in (1, -1):
        hub = Vector((s * 1.05, 0.15, -0.1)); nm = "FlapR" if s > 0 else "FlapL"
        for k in range(5):
            a = math.radians(-40 + k * 20)
            tip = hub + Vector((s * math.cos(a) * 0.6, -0.15 - k * 0.04, math.sin(a) * 0.5))
            P.part(nm, pipe([hub, tip], [0.05, 0.02], 6), "Trim", tuple(hub))
            P.part(nm, ball(tuple((hub + tip) * 0.5), (0.16, 0.03, 0.1), 8, 4), "Glow", tuple(hub))
    th = Vector((0, -1.05, 0.0))
    for k in range(7):
        a = math.radians(-60 + k * 20)
        tip = th + Vector((math.sin(a) * 0.7, -0.75, math.cos(a) * 0.3 + math.sin(a) * 0.0))
        P.part("SwayTail", pipe([th, tip], [0.06, 0.025], 6), "Trim", tuple(th))
        P.part("SwayTail", ball(tuple(th + (tip - th) * 0.55), (0.14, 0.32, 0.04), 8, 4), "Glow", tuple(th))
    P.obj("Dorsal", hull([(0, -0.3, 0.95), (0, -0.85, 0.75), (0, -0.7, 1.3), (0.03, -0.5, 1.0), (-0.03, -0.5, 1.0)]), "Glow", 0, False)
    P.part("Muzzle", ball((0, 1.12, -0.22), (0.06, 0.03, 0.06), 8, 4), "Glow", (0, 1.12, -0.22))
    return P
# <<< 2026-10-11 new


# ================================================================= 2026-10-14: the five remade like the alien / west / treasure ones
# Real anatomy and proportions, scarier faces, the cartoon idea kept, details that sit evenly - each flying its own way, one you can see from
# the front - and their surfaces baked into textures (boss_bake.py) so they stop looking like plastic.
from west_bosses import V_, flat_pipe, feather, glow_strength, AB_pal, fib_dirs
from alien_bosses import lerp_keys, spine_frames, oriented_ball
from autumn_bosses import fx_tuft, st_loft, st_cloth, sq_axes, spline as st_spline
from treasure_bosses import frame_rh, long_feather
import boss_bake as BB


def star_plate(c, nrm, r, pts=4, thick=0.02):
    """a flat star lying on a surface: a low pyramid over a star outline (points r, notches 0.3 r), open underneath where it lies on the hide."""
    c = V_(c); nrm = V_(nrm).normalized(); x, y, z = sq_axes(nrm)
    bm = bmesh.new(); ap = bm.verts.new(c + nrm * thick); ring = []
    for k in range(pts * 2):
        a = math.pi * k / pts; rr = r if k % 2 == 0 else r * 0.3
        ring.append(bm.verts.new(c + (x * math.cos(a) + y * math.sin(a)) * rr))
    for k in range(pts * 2): bm.faces.new((ap, ring[k], ring[(k + 1) % (pts * 2)]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def S2_whale():
    """THE SKY WHALE (2026-10-14, remade like the alien / west / treasure bosses): an old humpback bull built like the real animal, lunging at
    you with its jaws wide open. The flat head crusted with knobbly tubercles in rows down the rostrum and along the lower lip, a barnacle
    crust on the chin; the lower jaw dropped open and the pleated throat ballooned under it, white with dark grooves running back to the navel;
    inside, the pink tongue and the dark throat, and from the upper jaw the baleen hanging on both sides in black combs of plates, short in
    front and long at the back. The eye, small at the corner of the mouth under a heavy lid, glows cold cyan. A splashguard ridge and the
    paired blowholes, a bushy spout of glowing spray; the hump and the small hooked dorsal fin, the knuckles down the tail stock, the wide
    flukes with their serrated trailing edge, white beneath, raked by an orca's teeth long ago.
    The cartoon idea kept: the night sky on its back - a constellation of gold stars joined by lines of light - and the golden harness
    carrying a lantern pavilion with a silk canopy and pennants.
    It flies on its fins, as a humpback does through the sea: the two enormous white pectoral fins, knobbed along the leading edge and
    crusted with barnacles at the tips, spread like wings and beating (FlapL / FlapR); the flukes beat too (Sway0)."""
    P = Boss("whale", AB_pal(Base=((0.035, 0.07, 0.16), 0.4), Belly=((0.86, 0.87, 0.84), 0.35), Accent=((0.7, 0.3, 0.33), 0.45),
                             Trim=((0.98, 0.76, 0.22), 0.8), Glass=((0.55, 0.88, 1.0), 0.9), Dark=((0.02, 0.025, 0.035), 0.5),
                             Glow=((0.4, 1.0, 1.0), 0.5), Metal=((0.8, 0.77, 0.7), 0.4), Lamp=((1.0, 0.82, 0.45), 0.8)))
    glow_strength(P, 2.0)
    # ---- the body: the flat head, the deep chest behind the throat, the hump, the tail stock
    YS = [2.55, 2.25, 1.8, 1.3, 0.75, 0.15, -0.5, -1.1, -1.65, -2.1, -2.42]; ZS = [0.1, 0.13, 0.16, 0.19, 0.21, 0.22, 0.21, 0.19, 0.16, 0.13, 0.11]
    PTS = st_spline([V_((0, y, z)) for y, z in zip(YS, ZS)], 4); n = len(PTS); FR = spine_frames(PTS)
    def uy(y): return (2.55 - y) / 4.97
    RX = [lerp_keys(uy(p.y), [(0, 0.18), (0.06, 0.34), (0.15, 0.52), (0.25, 0.7), (0.36, 0.83), (0.48, 0.86), (0.6, 0.78), (0.72, 0.58), (0.83, 0.36), (0.92, 0.2), (1, 0.09)]) for p in PTS]
    RU = [lerp_keys(uy(p.y), [(0, 0.08), (0.06, 0.13), (0.15, 0.2), (0.25, 0.3), (0.36, 0.44), (0.48, 0.52), (0.6, 0.5), (0.72, 0.42), (0.83, 0.3), (0.92, 0.17), (1, 0.08)]) for p in PTS]
    RD = [lerp_keys(uy(p.y), [(0, 0.06), (0.15, 0.08), (0.25, 0.12), (0.33, 0.22), (0.42, 0.42), (0.52, 0.5), (0.62, 0.46), (0.74, 0.36), (0.85, 0.24), (0.93, 0.15), (1, 0.08)]) for p in PTS]
    SQ = 1.15
    def sec(y):
        i = 0
        for i in range(n - 1):
            if PTS[i].y >= y >= PTS[i + 1].y: break
        a = (PTS[i].y - y) / max(1e-6, PTS[i].y - PTS[i + 1].y)
        L = lambda arr: arr[i] + (arr[i + 1] - arr[i]) * a
        return PTS[i].lerp(PTS[i + 1], a), L(RX), L(RU), L(RD)
    def surf(y, ang, out=0.0):   # the point at angle ang (degrees: 90 the top, 0 the right flank) round the body at y, and its normal
        c, rx, ru, rd = sec(y); a = math.radians(ang); ca, sa = math.cos(a), math.sin(a)
        u = math.copysign(abs(ca) ** (1 / SQ), ca) * rx; v = math.copysign(abs(sa) ** (1 / SQ), sa) * (ru if sa > 0 else rd)
        gu = math.copysign(abs(u / rx) ** (2 * SQ - 1), u) / rx; gv = math.copysign(abs(v / (ru if sa > 0 else rd)) ** (2 * SQ - 1), v) / (ru if sa > 0 else rd)
        nn = V_((gu, 0.0, gv)).normalized()
        return c + V_((u, 0, v)) + nn * out, nn
    def top(x, y):
        c, rx, ru, rd = sec(y); q = min(0.97, abs(x) / rx)
        return c.z + ru * (1 - q ** (2 * SQ)) ** (1 / (2 * SQ))
    def hide(c, nn):
        if nn.z < -0.45 and c.y > 1.12: return "Accent"            # the palate, the roof of the open mouth
        if nn.z < -0.35 and c.y < 0.9: return "Belly"              # the pale belly behind the throat
        return "Base"
    P.obj("Body", st_loft(PTS, RX, RU, RD, FR, 36, SQ), hide, 0)

    # ---- the lower jaw dropped open (26 degrees about the hinge at the corner of the mouth) and the throat ballooned under it
    J = V_((0, 1.12, 0.02)); JR = Matrix.Rotation(math.radians(-32), 3, "X")
    def jaw_pt(p): return J + JR @ (V_(p) - J)
    rim = [jaw_pt((0.78 * math.sin(f), 1.12 + 1.56 * abs(math.cos(f)) ** 0.9, 0.02)) for f in [math.radians(-90 + 180 * k / 40) for k in range(41)]]
    P.obj("Lip", pipe(rim, [0.11] * 41, 12), "Base")
    down = JR @ V_((0, 0, -1)); mid = jaw_pt((0, 1.75, 0.02))
    def inward(q):
        d = mid - q; d = d - down * d.dot(down); return d.normalized()
    wall = []
    for k in range(41):
        f = abs(-90 + 180 * k / 40); D = 0.52 * (1 - 0.5 * max(0.0, (f - 66) / 24))
        wall.append([rim[k] + down * (D * t) + inward(rim[k]) * (0.02 * t) for t in (0.0, 0.5, 1.0)])
    quads = [[tuple(wall[k][j]), tuple(wall[k + 1][j]), tuple(wall[k + 1][j + 1]), tuple(wall[k][j + 1])] for k in range(40) for j in range(2)]
    P.obj("JawWall", st_cloth(quads, 0.05), lambda c, nn: "Accent" if nn.dot(inward(c)) > 0.1 else "Base", 0)
    BAG = [(2.12, -1.12, 0.28, 0.06, 0.12), (1.95, -1.03, 0.44, 0.1, 0.3), (1.6, -0.85, 0.62, 0.15, 0.46), (1.2, -0.67, 0.72, 0.22, 0.56),
           (0.8, -0.55, 0.74, 0.5, 0.52), (0.3, -0.42, 0.66, 0.45, 0.4), (-0.15, -0.28, 0.5, 0.3, 0.26), (-0.5, -0.18, 0.3, 0.2, 0.12)]
    bp = st_spline([V_((0, y, zc)) for (y, zc, w, hu, hd) in BAG], 4); bn = len(bp)
    def bag_k(y, j):   # the bag's sizes at y, interpolated in its keys
        ys = [b[0] for b in BAG]
        for i in range(len(BAG) - 1):
            if ys[i] >= y >= ys[i + 1]:
                a = (ys[i] - y) / (ys[i] - ys[i + 1]); return BAG[i][j] + (BAG[i + 1][j] - BAG[i][j]) * a
        return BAG[0][j] if y > ys[0] else BAG[-1][j]
    bfr = [(t, V_((-1, 0, 0)), V_((0, 0, 1))) for t in [V_((0, -1, 0))] * bn]
    def throat(c, nn):   # the floor of the mouth pink, the pleated throat under it white
        return "Accent" if nn.z > 0.6 and abs(c.x) < 0.7 * bag_k(c.y, 2) else "Belly"
    P.obj("Throat", st_loft(bp, [bag_k(p.y, 2) for p in bp], [bag_k(p.y, 3) for p in bp], [bag_k(p.y, 4) for p in bp], bfr, 40, 1.05), throat, 0)
    def bag_pt(y, deg, out=0.012):
        a = math.radians(deg); zc = bag_k(y, 1); w = bag_k(y, 2); h = bag_k(y, 3) if math.sin(a) > 0 else bag_k(y, 4)
        return V_((math.cos(a) * w * (1 + out), y, zc + math.sin(a) * h * (1 + out)))
    for k in range(15):   # the ventral pleats: grooves running from the chin back to the navel, evenly round the underside
        deg = -165 + 150 * k / 14
        ys = [2.08 - 2.54 * j / 24 for j in range(25)]
        P.obj("Pleat", pipe([bag_pt(y, deg) for y in ys], [0.0] + [0.016] * 23 + [0.0], 5), "Dark")
    P.obj("Tongue", ball((0, 1.6, -0.6), (0.32, 0.46, 0.12), 18, 9), "Accent")
    P.obj("Gullet", ball((0, 1.06, -0.3), (0.5, 0.3, 0.42), 14, 7), "Dark")
    # the baleen: black combs of plates hanging from the upper jaw on both sides, short in front, long at the back
    for s in (1, -1):
        for k in range(30):
            t = k / 29; y = 2.32 - 1.12 * t
            c, rx, ru, rd = sec(y); g = V_((s * rx * 0.8, y, c.z - rd * 0.8))
            L = 0.2 + 0.46 * t ** 0.8
            bot = g + V_((-s * 0.06, -0.04, -L))
            P.obj("Baleen", flat_pipe([g, g.lerp(bot, 0.5), bot], [0.05, 0.045, 0.03], V_((0, 1, 0)), 0.85, 6), "Dark")
    # tubercles: knobs in rows down the rostrum and along the lower lip; the splashguard and the blowholes
    for y in (2.4, 2.2, 2.0, 1.8, 1.6, 1.4):
        P.obj("Tubercle", ball((0, y, top(0, y) + 0.01), (0.05, 0.05, 0.04), 8, 4), "Base")
    for s in (1, -1):
        for y in (2.25, 2.0, 1.75, 1.5):
            c, rx, ru, rd = sec(y); x = s * rx * 0.55
            P.obj("Tubercle", ball((x, y, top(x, y) + 0.005), (0.042, 0.042, 0.034), 8, 4), "Base")
        for k in range(1, 9):
            f = s * math.radians(90 * k / 9)
            q = jaw_pt((0.78 * math.sin(f) * 1.07, 1.12 + 1.56 * abs(math.cos(f)) ** 0.9 * 1.01, -0.03))
            P.obj("Tubercle", ball(tuple(q), (0.05, 0.05, 0.045), 8, 4), "Base")
    chin = jaw_pt((0, 2.72, -0.03))
    for k in range(9):   # the barnacle crust on the chin
        a = 2 * math.pi * k / 9; r = 0.06 if k % 2 else 0.11
        b0 = chin + V_((math.cos(a) * r, 0.02, math.sin(a) * r * 0.7))
        P.obj("Barnacle", lathe([(0.045, 0.0), (0.035, 0.045), (0.016, 0.05), (0.0, 0.035)], 8, "y", tuple(b0)), "Metal")
    P.obj("Splashguard", pipe([V_((x, 1.02, top(x, 1.02) + 0.02)) for x in (-0.22, -0.1, 0.0, 0.1, 0.22)], [0.0, 0.04, 0.05, 0.04, 0.0], 8), "Base")
    for s in (1, -1):
        P.obj("Blowhole", oriented_ball((s * 0.07, 0.86, top(0.07, 0.86) + 0.005), (0.03, 0.09, 0.012), V_((1, 0, 0)), V_((0, 1, 0)), V_((0, 0, 1)), 10, 4), "Dark")
    # ---- the eye at the corner of the mouth: small, glowing cold, under a heavy lid; folds of skin round it
    for s in (1, -1):
        E = V_((s * 0.84, 0.98, 0.13))
        ex, ey, ez = frame_rh(V_((s * 1.0, 0.6, 0.05)))
        P.obj("Orbit", oriented_ball(E, (0.15, 0.08, 0.12), ex, ey, ez, 14, 7), "Base")
        P.obj("Eye", oriented_ball(E + ey * 0.06, (0.068, 0.03, 0.055), ex, ey, ez, 14, 7), "Glow")
        P.obj("Pupil", oriented_ball(E + ey * 0.085, (0.03, 0.012, 0.034), ex, ey, ez, 10, 5), "Dark")
        P.obj("Lid", oriented_ball(E + ey * 0.065 + ez * 0.035, (0.085, 0.035, 0.035), ex, ey, ez, 12, 6), "Base")
        for k, r in enumerate((0.12, 0.155)):
            arc = [E + ey * 0.045 + (ex * math.cos(a) + ez * math.sin(a)) * r for a in [math.radians(200 - 220 * j / 10) for j in range(11)]]
            P.obj("Fold", pipe(arc, [0.0] + [0.014 - 0.003 * k] * 9 + [0.0], 5), "Base")
    # ---- the hump, the small hooked dorsal fin, the knuckles down the tail stock
    yd = -1.15; zt = top(0, yd)
    P.obj("Dorsal", hull([(0, -0.92, top(0, -0.92) - 0.02), (0, -1.42, top(0, -1.42) - 0.02), (0.06, -1.15, zt), (-0.06, -1.15, zt),
                          (0, -1.38, zt + 0.26), (0, -1.3, zt + 0.22), (0.03, -1.25, zt + 0.12), (-0.03, -1.25, zt + 0.12)]), "Base", 0, False)
    for k in range(6):
        y = -1.62 - 0.12 * k; r = 0.06 - 0.005 * k
        P.obj("Knuckle", ball((0, y, top(0, y) + 0.005), (r, r * 1.3, r * 0.8), 8, 4), "Base")
    # ---- the flukes: wide, swept back, the trailing edge serrated, a notch in the middle; white beneath; three old orca rake scars
    hub = (0, -2.38, 0.11)
    secs = []
    for k in range(21):
        x = -1.45 + 2.9 * k / 20; ax = abs(x)
        le = -2.3 - 0.34 * ax ** 1.3
        ch = (0.62 - 0.32 * ax / 1.45) * (1 - 0.85 * max(0.0, (ax - 1.25) / 0.2)) - (0.12 if ax < 0.1 else 0.0) + (0.035 if k % 2 else -0.02)
        secs.append((x, airfoil(le, le - max(0.04, ch), 0.07 - 0.04 * ax / 1.45, 0.11 + 0.06 * ax)))
    P.part("Sway0", sweep(secs, "x"), lambda c, nn: "Base" if nn.z > 0.1 else "Belly", hub, 0)
    for k in range(3):
        a0 = V_((0.55 + 0.1 * k, -2.42 - 0.2 * 0.62, 0.11 + 0.06 * 0.62 + 0.034)); a1 = a0 + V_((0.3, -0.24, 0.012))
        P.part("Sway0", pipe([a0, a0.lerp(a1, 0.5), a1], [0.0, 0.013, 0.0], 4), "Belly", hub)
    for x in (1.38, -1.38):   # barnacles on the fluke tips
        for k in range(4):
            q = V_((x - 0.07 * math.copysign(1, x) * k, -2.3 - 0.34 * abs(x) ** 1.3 - 0.06 * k, 0.11 + 0.06 * abs(x) + 0.03))
            P.part("Sway0", lathe([(0.03, 0.0), (0.024, 0.03), (0.01, 0.035), (0.0, 0.02)], 7, "z", tuple(q)), "Metal", hub)

    # ---- the pectoral fins: enormous, white, knobbed along the leading edge, spread like wings and beating
    S0 = V_((0.8, 0.72, -0.2)); U0 = V_((1.0, 0.28, 0.62)).normalized()
    C0 = V_((U0.z, 0.0, -U0.x)).normalized(); N0 = U0.cross(C0).normalized()
    def M(s, v): return V_((s * v.x, v.y, v.z))
    for s in (1, -1):
        name = "FlapR" if s > 0 else "FlapL"; hub = tuple(M(s, S0)); NS = M(s, N0)
        def F(x, c, h=0.0, s=s): return M(s, S0 + U0 * x + C0 * c + N0 * h)
        rows = []
        for k in range(25):
            x = 2.45 * k / 24
            ch = lerp_keys(x / 2.45, [(0, 0.6), (0.2, 0.56), (0.5, 0.46), (0.78, 0.32), (0.93, 0.17), (1, 0.05)])
            th = lerp_keys(x / 2.45, [(0, 0.1), (0.5, 0.06), (1, 0.025)])
            bow = 0.05 * math.sin(math.pi * x / 2.45)
            rows.append([F(x, cc * ch + (0.018 * math.sin(k * math.pi / 2.0) if cc > 0.95 else 0.0), hh * th - bow) for cc, hh in
                         ((0.0, 0.0), (0.12, 0.55), (0.45, 0.45), (0.8, 0.2), (1.0, 0.0), (0.8, -0.18), (0.45, -0.32), (0.12, -0.42))])
        bm = bmesh.new(); vs = [[bm.verts.new(p) for p in r] for r in rows]
        for r0, r1 in zip(vs, vs[1:]):
            for j in range(8): bm.faces.new((r0[j], r0[(j + 1) % 8], r1[(j + 1) % 8], r1[j]))
        bm.faces.new(vs[0][::-1]); bm.faces.new(vs[-1]); bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        P.part(name, bm, lambda c, nn, NS=NS: "Belly" if nn.dot(NS) > -0.2 else "Base", hub, 0)
        ux, uc, un = M(s, U0), M(s, C0), NS
        if s < 0: ux = -ux   # keep the frame right-handed on the mirrored side
        for k in range(11):   # the tubercles: big knobs half sunk into the leading edge, evenly, smaller toward the tip, so it scallops
            x = 0.18 + 2.1 * k / 10; r = 0.085 - 0.004 * k
            P.part(name, oriented_ball(F(x, 0.01, -0.01), (r * 1.15, r * 0.8, r * 0.62), ux, uc, un, 10, 5), "Belly", hub)
        for x0 in (2.25, 1.3):   # barnacle crusts: at the tip and halfway out
            for k in range(6):
                a = 2 * math.pi * k / 6
                q = F(x0 + 0.06 * math.cos(a), 0.1 + 0.05 * math.sin(a), 0.035)
                P.part(name, lathe([(0.032, 0.0), (0.025, 0.032), (0.011, 0.036), (0.0, 0.022)], 7, "z", tuple(q)), "Metal", hub)

    # ---- the night sky on its back: gold stars joined by lines of light
    SP = [(0.0, 1.45), (0.3, 1.05), (-0.34, 0.78), (0.52, 0.3), (-0.56, -0.05), (0.3, -0.5), (-0.12, -0.85)]
    pts = []
    for (x, y) in SP:
        q = V_((x, y, top(x, y) + 0.004)); pts.append(q)
        P.obj("Star", star_plate(q, V_((x * 0.6, 0, 1)), 0.11 if len(pts) % 2 else 0.08), "Lamp", 0, False)
    for a, b in zip(pts, pts[1:]):
        line = [a.lerp(b, t) for t in (0.15, 0.3, 0.45, 0.6, 0.75, 0.85)]
        line = [V_((q.x, q.y, top(q.x, q.y) + 0.008)) for q in line]
        P.obj("StarLine", pipe(line, [0.0] + [0.011] * 4 + [0.0], 4), "Glow")
    # ---- the golden harness and the lantern pavilion: a gilt platform, four posts, a silk canopy, a lantern, pennants
    for y in (0.62, -0.18):
        P.obj("Harness", pipe([surf(y, a, 0.02)[0] for a in [360 * k / 48 for k in range(49)]], [0.03] * 49, 6, False), "Trim")
    PC = V_((0, 0.22, top(0, 0.22) + 0.03))
    P.obj("Platform", lathe([(0.0, 0.0), (0.42, 0.0), (0.44, 0.04), (0.42, 0.07), (0.0, 0.07)], 24, "z", tuple(PC)), "Trim")
    for k in range(4):
        a = 2 * math.pi * k / 4 + math.pi / 4; q = PC + V_((math.cos(a) * 0.32, math.sin(a) * 0.32, 0.07))
        P.obj("Post", pipe([q, q + V_((0, 0, 0.42))], [0.028, 0.024], 8), "Trim")
        P.obj("Post", ball(tuple(q + V_((0, 0, 0.44))), (0.04,) * 3, 8, 4), "Trim")
    roof = PC + V_((0, 0, 0.5))
    P.obj("Canopy", lathe([(0.0, 0.34), (0.2, 0.3), (0.38, 0.17), (0.48, 0.03), (0.46, 0.0), (0.0, 0.02)], 24, "z", tuple(roof)), "Glass")
    for k in range(12):   # the canopy's scalloped hem, evenly
        a = 2 * math.pi * k / 12; q = roof + V_((math.cos(a) * 0.47, math.sin(a) * 0.47, -0.01))
        P.obj("CanopyHem", ball(tuple(q), (0.05, 0.05, 0.04), 8, 4), "Trim")
    P.obj("Finial", lathe([(0.0, 0.0), (0.04, 0.0), (0.05, 0.06), (0.02, 0.14), (0.0, 0.22)], 10, "z", tuple(roof + V_((0, 0, 0.33)))), "Trim")
    P.obj("Lantern", ball(tuple(PC + V_((0, 0, 0.3))), (0.1, 0.1, 0.13), 12, 6), "Lamp")
    P.obj("LanternCap", lathe([(0.0, 0.0), (0.08, 0.0), (0.05, 0.05), (0.0, 0.08)], 10, "z", tuple(PC + V_((0, 0, 0.42)))), "Trim")
    for s in (1, -1):
        mast = PC + V_((s * 0.44, -0.05, 0.07))
        P.obj("PennantPole", pipe([mast, mast + V_((0, 0, 0.72))], [0.015, 0.012], 6), "Trim")
        tip = mast + V_((0, 0, 0.7)); quads = []
        for j in range(6):
            u0, u1 = j / 6, (j + 1) / 6
            def pp(u, v): return tip + V_((0, -0.5 * u, -0.16 * v * (1 - u) - 0.02 * math.sin(u * 6)))
            quads.append([tuple(pp(u0, 0)), tuple(pp(u1, 0)), tuple(pp(u1, 1)), tuple(pp(u0, 1))])
        P.part("ClothPennant", st_cloth(quads, 0.012), "Glass", (0, 0, 0), 0, True)
    # ---- the spout: a bushy column of glowing spray from the blowholes
    zb = top(0, 0.86)
    for j in range(9):
        a = 2 * math.pi * j / 9; dx, dy = math.cos(a) * 0.17, math.sin(a) * 0.17
        arc = bez(V_((dx * 0.25, 0.86 + dy * 0.25, zb)), V_((dx * 0.5, 0.86 + dy * 0.5, zb + 0.55)),
                  V_((dx * 1.8, 0.88 + dy * 1.6, zb + 1.1)), V_((dx * 3.2, 0.9 + dy * 2.8, zb + 1.05)), 11)
        for i, q in enumerate(arc[1:]):
            r = 0.03 + 0.045 * math.sin(math.pi * i / 10) + 0.012 * (j % 2)
            P.obj("Spray", ball(tuple(q), (r, r, r), 12, 6), "Glass")
    P.part("Muzzle", ball((0, 1.95, -0.4), (0.08, 0.05, 0.06), 8, 4), "Glow", (0, 1.95, -0.4))
    return P



def fish_fin(P, name, hub, out, up, n_rays, length, spread, slot_web="Belly", slot_ray="Trim", back=None, curve=0.08):
    """a fish's fan fin from its root at hub: n_rays bony rays spreading over `spread` degrees in the plane of out and up, each bent a little
    toward back, a thin web between them scalloped between the ray tips; one part named name (its hub the pivot)."""
    hub, out, up = V_(hub), V_(out).normalized(), V_(up).normalized()
    back = V_(back).normalized() if back is not None else out.cross(up).normalized()
    rays = []
    for k in range(n_rays):
        a = math.radians(-spread / 2 + spread * k / (n_rays - 1))
        d = (out * math.cos(a) + up * math.sin(a)).normalized()
        L = length * (1 - 0.18 * abs(2 * k / (n_rays - 1) - 1) ** 2)
        rays.append([hub + d * (L * t) + back * (curve * L * t * t) for t in (0.0, 0.33, 0.66, 1.0)])
    polys = []
    for k in range(n_rays - 1):
        r0, r1 = rays[k], rays[k + 1]
        for j in range(2): polys.append([tuple(r0[j]), tuple(r0[j + 1]), tuple(r1[j + 1]), tuple(r1[j])])
        m = (r0[3] + r1[3]) * 0.5 + (hub - (r0[3] + r1[3]) * 0.5) * 0.14   # the edge dips between two ray tips
        polys += [[tuple(r0[2]), tuple(r0[3]), tuple(m)], [tuple(r0[2]), tuple(m), tuple(r1[2])], [tuple(r1[2]), tuple(m), tuple(r1[3])]]
    P.part(name, st_cloth(polys, 0.016), slot_web, tuple(hub), 0, True)
    for pts in rays:
        P.part(name, pipe(pts, [0.022, 0.016, 0.012, 0.006], 5), slot_ray, tuple(hub))


def S2_puffer():
    """THE PUFFERFISH EMPEROR (2026-10-14, remade like the alien / west / treasure bosses): a porcupinefish built like the real one and
    blown up for war, round and taut as a balloon - which is how he floats - bristling all over with long ivory spines, each rising from its
    own raised root and raked back, cream spots set evenly between them on the royal blue, the belly pale. The real face: huge bulging eyes
    set high, gold irises glowing round black pupils under heavy blue lids and gilded brows; the fused beak of a porcupinefish - two white
    tooth plates above and two below, the seam down the middle - open between thick coral lips; the gill slits behind the eyes.
    The cartoon idea kept: a white handlebar moustache waxed into curls, a jewelled imperial crown of gold arches over crimson velvet with
    an orb and cross, a crimson sash with a gold star medal, a rope of pearls under the chin.
    He flies as a puffer swims: puffed up he floats, and his two fan-shaped pectoral fins flutter fast at his sides (FlapL / FlapR), the
    rounded tail wags (WagTail), the dorsal and anal fins far back sway (SwayDorsal, SwayAnal)."""
    P = Boss("puffer", AB_pal(Base=((0.05, 0.2, 0.6), 0.45), Belly=((0.95, 0.89, 0.72), 0.4), Accent=((0.72, 0.07, 0.12), 0.5),
                              Trim=((0.98, 0.76, 0.22), 0.8), Glass=((0.96, 0.95, 0.9), 0.85), Dark=((0.03, 0.04, 0.08), 0.5),
                              Glow=((1.0, 0.45, 0.04), 0.5), Metal=((0.97, 0.96, 0.93), 0.6), Lamp=((0.3, 0.62, 1.0), 0.8)))
    glow_strength(P, 1.0)
    R = V_((1.1, 1.04, 0.98))
    def on(d, k=1.0):   # the point on the body along d (k times out) and the normal there
        d = V_(d).normalized(); f = 1 / math.sqrt((d.x / R.x) ** 2 + (d.y / R.y) ** 2 + (d.z / R.z) ** 2)
        p = d * f; nn = V_((p.x / R.x ** 2, p.y / R.y ** 2, p.z / R.z ** 2)).normalized()
        return p + nn * (k - 1.0), nn
    P.obj("Body", ball((0, 0, 0), tuple(R), 48, 24), lambda c, nn: "Belly" if c.z < -0.38 * R.z else "Base", 0)
    EYE = [V_((s * 0.55, 0.72, 0.38)).normalized() for s in (1, -1)]; MOUTH = V_((0, 1, -0.3)).normalized()
    FIN = [V_((s * 1.0, 0.12, -0.12)).normalized() for s in (1, -1)]; TOP = V_((0, 0.05, 1)).normalized(); TAIL = V_((0, -1, 0))
    DORS = V_((0, -0.75, 0.66)).normalized(); ANAL = V_((0, -0.75, -0.66)).normalized()
    def ang(a, b): return math.degrees(a.angle(b))
    e1 = V_((1, 0, 0.45)).normalized(); e2 = V_((0, 0.6, -0.8)); e2 = (e2 - e1 * e2.dot(e1)).normalized(); WN = e1.cross(e2).normalized()
    sdir = lambda t: e1 * math.cos(t) + e2 * math.sin(t)   # the sash runs round this circle
    def clear(d, extra=0.0):
        return (min(ang(d, e) for e in EYE) > 27 + extra and ang(d, MOUTH) > 30 + extra and min(ang(d, f) for f in FIN) > 17
                and ang(d, TOP) > 37 and ang(d, TAIL) > 21 and abs(d.dot(WN)) > 0.15 and ang(d, DORS) > 14 and ang(d, ANAL) > 14)
    # ---- the spines: evenly over the whole body (a golden-angle spiral), each from its own raised root, raked back
    N = 130; ga = math.pi * (3 - math.sqrt(5))
    for i in range(N):
        z = 1 - 2 * (i + 0.5) / N; r = math.sqrt(1 - z * z); d = V_((math.cos(ga * i) * r, math.sin(ga * i) * r, z))
        if not clear(d): continue
        p, nn = on(d); dr = (nn - V_((0, 0.38, 0))).normalized()
        L = 0.27 if d.y > 0.45 else 0.38
        x_, y_, z_ = frame_rh(nn)
        P.obj("SpineRoot", oriented_ball(p, (0.085, 0.03, 0.085), x_, y_, z_, 10, 4), "Base")
        P.obj("Spine", pipe([p - dr * 0.02, p + dr * (L * 0.5), p + dr * L], [0.05, 0.028, 0.0], 7), "Belly")
    for i in range(70):   # cream spots between the spines (the spiral turned half a step), on the back and flanks
        z = 1 - 2 * (i + 0.5) / 70; r = math.sqrt(1 - z * z); d = V_((math.cos(ga * i + 1.3) * r, math.sin(ga * i + 1.3) * r, z))
        if d.z < -0.3 or not clear(d, 6): continue
        p, nn = on(d); x_, y_, z_ = frame_rh(nn)
        P.obj("Spot", oriented_ball(p, (0.075, 0.012, 0.075), x_, y_, z_, 10, 3), "Belly")
    # ---- the eyes: huge, bulging, set high; gold irises glowing; heavy lids; gilded brows
    def cap(c, r, pn, keep):   # a smooth cap of a ball round c, its pole along pn, its rim a clean circle where the plane keep out cuts it
        th = math.acos(max(-1.0, min(1.0, keep / r)))
        prof = [(r * math.sin(th * k / 10) if k else 0.0, r * math.cos(th * k / 10)) for k in range(11)]
        x_, y_, z_ = frame_rh(pn)   # (x, pn, z): the lathe's up must go to pn
        return xf(lathe(prof, 36, "z"), Matrix((x_, z_, y_)).transposed() @ Matrix.Scale(-1, 3, V_((1, 0, 0))), tuple(c))
    for s, d in zip((1, -1), EYE):
        p, nn = on(d); c = p + nn * 0.02
        f = (nn + V_((0, 0.45, 0))).normalized(); ex, ey, ez = frame_rh(f)
        lx, ly, lz = frame_rh((V_((0, 1, 0.12)) + nn * 0.35).normalized())   # the gaze: straight at you
        P.obj("Eyeball", ball(tuple(c), (0.27, 0.27, 0.27), 24, 12), "Glass")
        P.obj("Iris", oriented_ball(c + ly * 0.225, (0.165, 0.07, 0.165), lx, ly, lz, 18, 8), "Glow")
        P.obj("Pupil", oriented_ball(c + ly * 0.275, (0.058, 0.035, 0.064), lx, ly, lz, 12, 6), "Dark")
        P.obj("Glint", ball(tuple(c + ly * 0.3 + lz * 0.06 - lx * s * 0.05), (0.028, 0.018, 0.028), 6, 3), "Metal")
        P.obj("Socket", xf(torus(0.27, 0.06, 0.0, 36, 8), Matrix((ez, ex, ey)).transposed(), tuple(c - ey * 0.02)), "Base")
        P.obj("Lid", cap(c, 0.295, (ez + ey * 0.32 - ex * (s * 0.42)).normalized(), -0.035), "Base")   # tilted: lowest at the inner corner, the scowl
        brow = [c + ex * (s * (0.29 - 0.56 * t)) + ez * (0.35 - 0.3 * t + 0.045 * math.sin(math.pi * t)) + ey * (0.1 + 0.1 * t)
                for t in [k / 12 for k in range(13)]]   # the scowl: high at the outer corner, slanting down to the inner one
        P.obj("Brow", pipe(brow, [0.0, 0.04, 0.055, 0.065, 0.07, 0.07, 0.068, 0.064, 0.058, 0.05, 0.042, 0.03, 0.0], 8), "Trim")
        g = on(V_((s * 0.9, 0.3, -0.06)))[0]   # the gill slit
        P.obj("Gill", pipe([g + V_((0, 0.03, 0.16)), g + V_((s * 0.02, 0.06, 0.0)), g + V_((0, 0.03, -0.16))], [0.0, 0.03, 0.0], 6), "Dark")
    # ---- the beak: the fused tooth plates, open between thick coral lips; the moustache above
    pm, nm = on(MOUTH); mx, my, mz = frame_rh(nm)
    P.obj("Mouth", oriented_ball(pm, (0.2, 0.08, 0.16), mx, my, mz, 16, 8), "Dark")
    lips = torus(0.2, 0.075, 0.0, 32, 8)
    for v in lips.verts: v.co.x *= 1.35
    P.obj("Lips", xf(lips, Matrix((mx, mz, my)).transposed() @ Matrix.Scale(-1, 3, V_((0, 1, 0))), tuple(pm + my * 0.02)), "Accent")
    for sz, tilt, rr in ((1, 22, (0.21, 0.09, 0.08)), (-1, -26, (0.19, 0.085, 0.07))):
        R2 = Matrix.Rotation(math.radians(tilt), 3, mx) @ Matrix((mx, my, mz)).transposed()
        P.obj("Beak", xf(oriented_ball(V_((0, 0, 0)), rr, V_((1, 0, 0)), V_((0, 1, 0)), V_((0, 0, 1)), 18, 8), R2, tuple(pm + mz * (sz * 0.085) + my * 0.06)), "Glass")
        P.obj("Seam", pipe([pm + mz * (sz * 0.04) + my * 0.145, pm + mz * (sz * 0.15) + my * 0.13], [0.012, 0.01], 4), "Dark")
    for s in (1, -1):   # the moustache of an old emperor: out along the upper lip, then drooping long past the corners of the mouth
        b0 = pm + mz * 0.22 + my * 0.07
        pts = [b0 + mx * (s * 0.03), b0 + mx * (s * 0.18) - mz * 0.02 + my * 0.02, b0 + mx * (s * 0.32) - mz * 0.14 + my * 0.0,
               b0 + mx * (s * 0.38) - mz * 0.42 + my * 0.02, b0 + mx * (s * 0.41) - mz * 0.62 + my * 0.05, b0 + mx * (s * 0.48) - mz * 0.7 + my * 0.06]
        pts = st_spline(pts, 4)
        P.obj("Moustache", pipe(pts, [lerp_keys(k / (len(pts) - 1), [(0, 0.06), (0.2, 0.085), (0.5, 0.06), (0.8, 0.032), (1, 0.0)]) for k in range(len(pts))], 10), "Metal")
    # ---- the imperial crown: a jewelled gold band, crimson velvet, four arches, the orb and cross
    cc, cn = on(TOP); cc = cc + V_((0, 0, -0.06))
    P.obj("CrownBand", lathe([(0.0, 0.0), (0.46, 0.0), (0.48, 0.03), (0.48, 0.2), (0.46, 0.24), (0.43, 0.22), (0.43, 0.04)], 32, "z", tuple(cc)), "Trim")
    P.obj("CrownVelvet", ball(tuple(cc + V_((0, 0, 0.22))), (0.41, 0.41, 0.36), 24, 12), "Accent")
    for k in range(4):
        a = math.pi * k / 4; o = V_((math.cos(a), math.sin(a), 0))
        arch = bez(cc + o * 0.46 + V_((0, 0, 0.22)), cc + o * 0.47 + V_((0, 0, 0.66)), cc - o * 0.47 + V_((0, 0, 0.66)), cc - o * 0.46 + V_((0, 0, 0.22)), 16)
        P.obj("Arch", pipe(arch, [0.035] * 17, 7), "Trim")
        for t in (3, 6, 10, 13):   # pearls along each arch
            P.obj("Pearl", ball(tuple(arch[t] + V_((0, 0, 0.035))), (0.03,) * 3, 8, 4), "Metal")
    P.obj("Orb", ball(tuple(cc + V_((0, 0, 0.72))), (0.1, 0.1, 0.1), 14, 7), "Trim")
    P.obj("Cross", box(tuple(cc + V_((0, 0, 0.9))), (0.045, 0.045, 0.2)), "Trim", 0, False)
    P.obj("Cross", box(tuple(cc + V_((0, 0, 0.93))), (0.15, 0.045, 0.045)), "Trim", 0, False)
    for k in range(12):
        a = 2 * math.pi * k / 12; o = V_((math.sin(a), math.cos(a), 0))
        P.obj("Jewel", oriented_ball(cc + o * 0.49 + V_((0, 0, 0.12)), (0.055, 0.03, 0.06), *frame_rh(o), 10, 5), "Lamp" if k % 2 else "Accent")
        P.obj("CrownPoint", pipe([cc + o * 0.46 + V_((0, 0, 0.22)), cc + o * 0.47 + V_((0, 0, 0.36))], [0.05, 0.0], 6), "Trim")
        P.obj("Pearl", ball(tuple(cc + o * 0.47 + V_((0, 0, 0.38))), (0.035,) * 3, 8, 4), "Metal")
    # ---- the sash with its star medal, the rope of pearls under the chin
    strip = []
    for i in range(49):
        q = on(sdir(math.radians(-30 + 7.5 * i)), 1.03)[0]; strip.append((q + WN * 0.11, q - WN * 0.11))
    P.obj("Sash", st_cloth([[tuple(strip[i][0]), tuple(strip[i + 1][0]), tuple(strip[i + 1][1]), tuple(strip[i][1])] for i in range(48)], 0.03), "Accent", 0, True)
    mp, mn = on(sdir(math.radians(52)), 1.07); x_, y_, z_ = frame_rh(mn)
    P.obj("Medal", star_plate(mp, mn, 0.17, 8, 0.05), "Trim")
    P.obj("MedalGem", oriented_ball(mp + mn * 0.04, (0.07, 0.03, 0.07), x_, y_, z_, 10, 5), "Lamp")
    for k in range(19):
        a = math.radians(-72 + k * 8)
        P.obj("Pearl", ball(tuple(on(V_((math.sin(a), math.cos(a), -0.58)), 1.045)[0]), (0.058,) * 3, 10, 5), "Metal")
    # ---- the fins: the pectorals fluttering, the dorsal and anal far back, the rounded tail wagging
    for s, d in zip((1, -1), FIN):
        h, hn = on(d, 0.98)
        fish_fin(P, "FlapR" if s > 0 else "FlapL", h, V_((s * 1.0, -0.35, 0.0)), V_((0, 0, 1)), 9, 0.5, 110, back=V_((0, -1, 0)))
    h, hn = on(DORS, 0.96); fish_fin(P, "SwayDorsal", h, (hn - V_((0, 0.6, 0))), V_((0, -1, 0.2)), 7, 0.36, 70, curve=0.0)
    h, hn = on(ANAL, 0.96); fish_fin(P, "SwayAnal", h, (hn - V_((0, 0.6, 0))), V_((0, -1, -0.2)), 7, 0.33, 70, curve=0.0)
    h, hn = on(TAIL, 0.94); fish_fin(P, "WagTail", h, V_((0, -1, 0)), V_((0, 0, 1)), 11, 0.55, 120, curve=0.0)
    P.part("Muzzle", ball(tuple(pm + nm * 0.05), (0.06, 0.03, 0.06), 8, 4), "Lamp", tuple(pm + nm * 0.05))
    return P



def pitch_all(P, deg, about=(0, 0, 0)):
    """the whole boss so far turned about the wing axis (a dive: negative tips the nose down); moving parts keep their hubs with them."""
    R = Matrix.Rotation(math.radians(deg), 4, "X"); c = V_(about)
    T = Matrix.Translation(c) @ R @ Matrix.Translation(-c)
    for ob in P.parts: ob.data.transform(T)
    for ob in P.spin:
        ob.data.transform(R)                       # the mesh about its hub
        ob.location = T @ V_(ob.location)          # the hub with the rest


def S2_roc():
    """THE THUNDER ROC (2026-10-14, remade like the alien / west / treasure bosses): the storm bird of the open sea - a colossal albatross,
    the bird with the longest wings on earth, built like the real one and diving at you. A white body and head, a wedge tail tipped black; the
    albatross's face: a dark smudge of feathers above each eye that makes it scowl, the eyes burning electric blue, and the great bill made of
    horny plates with a hooked tip and the tube nostrils on its sides, gaping in a scream with lightning crackling in it (its shots leave from
    there). A collar of gold round the neck with a lightning-bolt medallion.
    The cartoon idea kept: thunder - the wings' leading edges crackle with lightning, and dark storm clouds full of it circle the bird.
    It flies as an albatross does, on its immense wings: held in the gull's "M" - the arms raised, the long hands swept down and back -
    white coverts over a black trailing edge and black primaries, beating (FlapL / FlapR); the storm turns round it (SpinStorm)."""
    P = Boss("roc", AB_pal(Base=((0.1, 0.105, 0.125), 0.4), Belly=((0.2, 0.21, 0.25), 0.35), Accent=((0.05, 0.05, 0.06), 0.5),
                           Trim=((0.98, 0.76, 0.22), 0.8), Glass=((0.92, 0.93, 0.95), 0.5), Dark=((0.03, 0.03, 0.035), 0.45),
                           Glow=((0.35, 0.78, 1.0), 0.5), Metal=((0.13, 0.15, 0.2), 0.4), Lamp=((0.85, 0.95, 1.0), 0.8)))
    glow_strength(P, 2.2)
    # ---- the body: a deep chest, a stout white body, the short wedge tail (built level, the dive is turned in at the end)
    PTS = st_spline([V_(p) for p in ((0, 1.0, 0.36), (0, 0.6, 0.22), (0, 0.1, 0.16), (0, -0.45, 0.18), (0, -0.95, 0.22))], 4); n = len(PTS)
    FR = spine_frames(PTS)
    def uu(i): return i / (n - 1)
    RX = [1.15 * lerp_keys(uu(i), [(0, 0.2), (0.2, 0.36), (0.45, 0.42), (0.7, 0.34), (0.9, 0.2), (1, 0.08)]) for i in range(n)]
    RU = [1.15 * lerp_keys(uu(i), [(0, 0.2), (0.2, 0.3), (0.45, 0.33), (0.7, 0.28), (0.9, 0.16), (1, 0.06)]) for i in range(n)]
    RD = [1.15 * lerp_keys(uu(i), [(0, 0.22), (0.2, 0.42), (0.45, 0.44), (0.7, 0.32), (0.9, 0.16), (1, 0.06)]) for i in range(n)]
    P.obj("Body", st_loft(PTS, RX, RU, RD, FR, 28, 1.1), lambda c, nn: "Belly" if nn.z < -0.55 else "Base", 0)
    for k in range(13):   # the wedge tail: thirteen feathers, white, the tips black
        c_ = (k - 6) / 6
        d = V_((c_ * 0.42, -1.0, 0.08)).normalized(); L = 0.62 - 0.16 * abs(c_); b = V_((c_ * 0.06, -0.85, 0.24))
        P.obj("Tail", long_feather(b + V_((0, 0, 0.004 * abs(k - 6))), d, L, 0.075, V_((0, 0, 1)), -0.02, 0.4),
              lambda cc, nn, b=b, d=d, L=L: "Dark" if (cc - b).dot(d) > L * 0.72 else "Base", 0, False)
    for s in (1, -1):   # the pink webbed feet tucked back under the tail
        f0 = V_((s * 0.16, -0.62, 0.0))
        P.obj("Leg", pipe([f0 + V_((0, 0.15, 0.1)), f0], [0.05, 0.04], 8), "Accent")
        for k in range(3):
            a = math.radians(-18 + 18 * k)
            tip = f0 + V_((s * math.sin(a) * 0.08 + s * 0.04 * (k - 1), -0.32, -0.02))
            P.obj("Toe", pipe([f0, f0.lerp(tip, 0.5), tip], [0.022, 0.018, 0.0], 6), "Accent")
        web = [[tuple(f0), tuple(f0 + V_((s * (-0.06), -0.3, -0.02))), tuple(f0 + V_((s * 0.04, -0.32, -0.02))), tuple(f0 + V_((s * 0.14, -0.28, -0.02)))]]
        P.obj("Web", st_cloth([[web[0][0], web[0][1], web[0][2]], [web[0][0], web[0][2], web[0][3]]], 0.012), "Accent", 0, True)

    # ---- the head, raised to look at you through the dive: the plated bill gaping, the scowling smudges, the burning eyes
    DIVE = 24
    HB = V_((0, 1.2, 0.64)); HR = Matrix.Rotation(math.radians(DIVE - 14), 3, "X") @ Matrix.Scale(1.2, 3)   # looking down at you a little   # built level, then tipped up by the dive it will be tipped down by
    def H(bm): return xf(bm, HR, tuple(HB))
    def hp(p): return HB + HR @ V_(p)
    P.obj("Neck", pipe([V_((0, 0.92, 0.36)), V_((0, 1.04, 0.5)), hp((0, -0.05, 0.0))], [0.29, 0.27, 0.26], 18), "Base")
    P.obj("Skull", H(loft([(-0.2, 0.17, 0.17, 0, 0.0), (-0.05, 0.25, 0.25, 0, 0.02), (0.12, 0.26, 0.24, 0, 0.04), (0.28, 0.21, 0.2, 0, 0.02),
                          (0.4, 0.14, 0.14, 0, -0.01)], 28, sq=1.05)), "Base")
    # the bill: horny plates - the culmen ridge down the top, the side plates, the hooked tip; the lower mandible dropped
    upper = bez((0, 0.32, 0.06), (0, 0.62, 0.07), (0, 0.9, 0.04), (0, 1.02, -0.08), 14)
    ub = pipe(upper, [lerp_keys(k / 14, [(0, 0.12), (0.4, 0.09), (0.8, 0.06), (0.92, 0.055), (1, 0.0)]) for k in range(15)], 16)
    for v in ub.verts: v.co.x *= 0.85
    P.obj("Bill", H(ub), lambda c, nn: "Accent")
    P.obj("Hook", H(pipe(bez((0, 0.9, 0.06), (0, 1.0, 0.07), (0, 1.07, 0.0), (0, 1.03, -0.12), 6), [0.06, 0.065, 0.06, 0.05, 0.035, 0.02, 0.0], 12)), "Accent")
    P.obj("Culmen", H(pipe(bez((0, 0.34, 0.17), (0, 0.6, 0.165), (0, 0.85, 0.13), (0, 0.95, 0.1), 8), [0.0] + [0.022] * 7 + [0.0], 6)), "Accent")
    for s in (1, -1):
        P.obj("Groove", H(pipe(bez((s * 0.075, 0.36, 0.02), (s * 0.07, 0.6, 0.03), (s * 0.055, 0.82, 0.02), (s * 0.04, 0.92, 0.0), 8), [0.0] + [0.009] * 7 + [0.0], 4)), "Dark")
        P.obj("Tube", H(pipe([V_((s * 0.085, 0.36, 0.1)), V_((s * 0.08, 0.52, 0.1))], [0.04, 0.03], 10)), "Accent")
    J0 = V_((0, 0.3, -0.04)); JR = Matrix.Rotation(math.radians(-32), 3, "X")
    def Jw(bm): return H(xf(bm, JR, tuple(J0 - JR @ J0)))
    lb = pipe(bez((0, 0.32, -0.05), (0, 0.6, -0.06), (0, 0.84, -0.06), (0, 0.98, -0.05), 10), [0.1, 0.085, 0.075, 0.065, 0.055, 0.045, 0.035, 0.028, 0.02, 0.012, 0.0], 12)
    for v in lb.verts: v.co.x *= 0.8
    P.obj("Jaw", Jw(lb), "Accent")
    for s in (1, -1):
        P.obj("Sulcus", Jw(pipe(bez((s * 0.075, 0.36, -0.035), (s * 0.07, 0.6, -0.04), (s * 0.055, 0.82, -0.04), (s * 0.035, 0.94, -0.04), 10), [0.0] + [0.013] * 9 + [0.0], 5)), "Glow")
    P.obj("Gape", H(ball((0, 0.5, -0.05), (0.07, 0.3, 0.06), 12, 6)), "Dark")
    P.obj("Spark", H(xf(bolt(V_((0, 0.4, 0.0)), V_((0.0, 0.92, -0.12)), 0.022, 5, 3), None, (0, 0, 0))), "Glow")   # lightning crackling in the gape
    for s in (1, -1):
        e = V_((s * 0.17, 0.25, 0.12)); f = V_((s * 0.55, 0.8, 0.1)).normalized(); ex, ey, ez = frame_rh(f)
        P.obj("Eye", H(oriented_ball(e, (0.078, 0.036, 0.07), ex, ey, ez, 14, 7)), "Glow")
        P.obj("Pupil", H(oriented_ball(e + ey * 0.026, (0.024, 0.012, 0.028), ex, ey, ez, 8, 4)), "Dark")
        cres = [e + V_((s * 0.014, 0, 0)) + (ez * math.cos(a) - ey * math.sin(a)) * 0.105 for a in [math.radians(-40 + 220 * k / 14) for k in range(15)]]
        P.obj("Crescent", H(flat_pipe(cres, [0.0, 0.016, 0.026, 0.032, 0.036, 0.038, 0.038, 0.038, 0.037, 0.035, 0.032, 0.027, 0.02, 0.011, 0.0], ex, 0.7, 6)), "Glass")
        brow = [V_((s * (0.1 + 0.13 * t), 0.31 - 0.2 * t, 0.17 + 0.02 * t + 0.03 * math.sin(math.pi * t))) for t in [k / 8 for k in range(9)]]
        P.obj("Brow", H(flat_pipe(brow, [0.02, 0.04, 0.05, 0.055, 0.055, 0.05, 0.045, 0.035, 0.02], V_((s * 0.6, 0.0, 0.8)), 0.55, 8)), "Base")
    # the gold collar with its lightning medallion
    P.obj("Collar", pipe([V_((math.sin(a) * 0.255, 0.98 + math.cos(a) * 0.05, 0.42 + math.cos(a) * 0.12)) for a in [2 * math.pi * k / 40 for k in range(41)]], [0.035] * 41, 6, False), "Trim")
    md = V_((0, 1.24, 0.5))
    P.obj("Medallion", xf(lathe([(0.0, -0.02), (0.13, -0.02), (0.14, 0.0), (0.13, 0.02), (0.0, 0.02)], 24, "y"), None, tuple(md)), "Trim")
    P.obj("MedalBolt", bolt(md + V_((0.04, 0.03, 0.1)), md + V_((-0.04, 0.03, -0.1)), 0.022, 3, 1), "Glow")

    # ---- the wings: the gull's M - the arm raised to the wrist, the long hand swept down and back
    def wing(s):
        name = "FlapR" if s > 0 else "FlapL"
        S = V_((s * 0.3, 0.28, 0.42)); Wr = V_((s * 1.35, 0.18, 0.98)); T = V_((s * 2.75, -0.22, 0.5))
        span = st_spline([S, S.lerp(Wr, 0.5) + V_((0, 0.03, 0.04)), Wr, Wr.lerp(T, 0.5) + V_((0, 0.02, 0.02)), T], 6)
        ns = len(span); hub = tuple(S); up0 = V_((0, 0.8, 1)).normalized()   # the wing's face turned to you
        L = [0.0]
        for a, b in zip(span, span[1:]): L.append(L[-1] + (b - a).length)
        def at(u):   # the frame at u (0 .. the full span length): the point, the span tangent, the chord (backward), the top normal
            i = max(0, min(ns - 2, next((k for k in range(ns - 1) if L[k + 1] >= u), ns - 2))); f = (u - L[i]) / max(1e-6, L[i + 1] - L[i])
            p = span[i].lerp(span[i + 1], f); t = (span[i + 1] - span[i]).normalized()
            c = up0.cross(t).normalized()
            if c.y > 0: c = -c                       # the chord runs back from the leading edge
            nrm = c.cross(t).normalized()
            if nrm.dot(up0) < 0: nrm = -nrm          # the top of the wing
            return p, t, c, nrm
        Ltot = L[-1]; Lw = L[next(k for k in range(ns) if (span[k] - Wr).length < 1e-6)] if any((sp - Wr).length < 1e-6 for sp in span) else Ltot * 0.45
        def chord(u): return lerp_keys(u / Ltot, [(0, 0.62), (Lw / Ltot, 0.56), (0.75, 0.4), (0.95, 0.2), (1, 0.08)])
        rows = []   # the skin of the wing under the feathers
        for k in range(28):
            u = Ltot * k / 27; p, t, c, nrm = at(u); ch = chord(u) * 0.6
            rows.append([p + c * (ch * cc) + nrm * (hh * (0.07 - 0.04 * u / Ltot)) for cc, hh in ((0.0, 0.0), (0.2, 0.6), (0.6, 0.4), (1.0, 0.0), (0.6, -0.3), (0.2, -0.45))])
        bm = bmesh.new(); vs = [[bm.verts.new(q) for q in r] for r in rows]
        for r0, r1 in zip(vs, vs[1:]):
            for j in range(6): bm.faces.new((r0[j], r0[(j + 1) % 6], r1[(j + 1) % 6], r1[j]))
        bm.faces.new(vs[0][::-1]); bm.faces.new(vs[-1]); bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        P.part(name, bm, "Base", hub, 0)
        P.part(name, pipe([at(Ltot * k / 30)[0] + at(Ltot * k / 30)[3] * 0.02 for k in range(31)], [lerp_keys(k / 30, [(0, 0.07), (0.5, 0.05), (1, 0.02)]) for k in range(31)], 10), "Base", hub)
        for row, (c0, Lf, w, du, h, slot) in enumerate(((0.04, 0.16, 0.055, 0.085, 0.05, "Base"), (0.13, 0.2, 0.06, 0.09, 0.038, "Base"))):
            u = 0.06 + (du * 0.5 if row % 2 else 0.0)
            while u < Ltot * 0.9:
                p, t, c, nrm = at(u)
                P.part(name, long_feather(p + c * (c0 * chord(u) / 0.62) + nrm * h, c, Lf * (1 - 0.35 * u / Ltot), w, nrm, -0.01, 0.5, 10), slot, hub, 0, False)
                u += du
        for k in range(17):   # the secondaries along the arm: white, tipped black - the black trailing edge
            u = 0.05 + (Lw - 0.05) * k / 16; p, t, c, nrm = at(u)
            b0 = p + c * (0.28 * chord(u)) + nrm * 0.01; Lf = 0.42 - 0.04 * k / 16
            P.part(name, long_feather(b0, (c + t * 0.05).normalized(), Lf, 0.07, nrm, -0.02, 0.5),
                   lambda cc, nn, b0=b0, c=c, Lf=Lf: "Dark" if (cc - b0).dot(c) > Lf * 0.62 else "Base", hub, 0, False)
        for k in range(11):   # the primaries along the hand: long, black, the outermost the longest, a pointed tip
            u = Lw + (Ltot * 0.93 - Lw) * k / 10; p, t, c, nrm = at(u)
            d = (c + t * (0.25 + 1.2 * k / 10)).normalized(); Lf = lerp_keys(k / 10, [(0, 0.5), (0.5, 0.62), (0.85, 0.72), (1, 0.8)])
            q0 = p + c * (0.22 * chord(u)) + nrm * (0.005 * k)
            P.part(name, long_feather(q0, d, Lf, 0.075, nrm, -0.03, 0.2), "Dark", hub, 0, False)
            vein = [q0 + d * (Lf * t) + nrm * (0.012 - 0.03 * t * t) for t in (0.12, 0.35, 0.6, 0.85, 0.97)]
            P.part(name, pipe(vein, [0.0, 0.009, 0.008, 0.006, 0.0], 4), "Glow", hub)
        tip = span[-1]   # a bolt striking down from the wingtip, beating with the wing
        P.part(name, bolt(tip + V_((0, 0, -0.04)), tip + V_((s * 0.25, -0.15, -1.1)), 0.04, 6, 7 + (s > 0)), "Glow", hub)
        for j in range(3):   # lightning crackling along the leading edge
            u0 = Ltot * (0.12 + 0.3 * j); u1 = u0 + Ltot * 0.24
            a, b = at(u0)[0] + at(u0)[3] * 0.06, at(u1)[0] + at(u1)[3] * 0.06
            P.part(name, bolt(a, b, 0.024, 5, j + 2 * (s > 0)), "Glow", hub)
    wing(1); wing(-1)
    # ---- the storm: dark clouds circling it, lightning dropping from each
    for k in range(4):
        a = 2 * math.pi * k / 4 + 0.6
        c = V_((math.sin(a) * 2.2, 0.1 + math.cos(a) * 1.7, 0.05 + 0.3 * math.sin(a * 2)))
        for j in range(5):
            o = V_(((j - 2) * 0.16, 0.06 * math.sin(j * 2.1), 0.07 * (j % 2)))
            P.part("SpinStorm", ball(tuple(c + o * 1.3), (0.27 + 0.06 * (j % 2), 0.22, 0.18 + 0.04 * (j % 2)), 14, 7), "Metal", (0, 0.1, 0.0))
        P.part("SpinStorm", bolt(c + V_((0, 0, -0.12)), c + V_((0.06, 0.02, -0.8)), 0.035, 4, k), "Lamp", (0, 0.1, 0.0))
    P.part("Muzzle", H(ball((0, 0.85, -0.06), (0.05, 0.04, 0.04), 8, 4)), "Lamp", tuple(hp((0, 0.85, -0.06))))
    pitch_all(P, -DIVE, (0, 0.2, 0.3))
    return P



def resample(pts, n):
    """n points evenly spaced along the polyline pts, and how far along it each one is."""
    pts = [V_(p) for p in pts]; cum = [0.0]
    for a, b in zip(pts, pts[1:]): cum.append(cum[-1] + (b - a).length)
    out, us, j = [], [], 0
    for i in range(n):
        s = cum[-1] * i / (n - 1)
        while j < len(cum) - 2 and cum[j + 1] < s: j += 1
        f = (s - cum[j]) / max(1e-9, cum[j + 1] - cum[j])
        out.append(pts[j].lerp(pts[j + 1], min(1.0, max(0.0, f)))); us.append(s)
    return out, us


def hide_attrs(bm, us=None, seg=None):
    """what the bake's oarfish hide is drawn from: "bu" (metres along the body; 0 on the head, which keeps it free of streaks) and "bv" (1 on
    the back, -1 under the belly) - per ring of a st_loft body (us: each ring's distance along it), or from each vertex's normal."""
    lu = bm.verts.layers.float.new("bu"); lv = bm.verts.layers.float.new("bv")
    bm.verts.ensure_lookup_table(); vs = list(bm.verts)
    if us is None:
        bm.normal_update()
        for v in vs: v[lu] = 0.0; v[lv] = v.normal.z
    else:
        for i, u in enumerate(us):
            for k in range(seg):
                v = vs[i * seg + k]; v[lu] = u; v[lv] = math.sin(2 * math.pi * k / seg)
    return bm


def ell_cap(c, r, ex, ey, ez, pn, keep, seg=36, rings=8, thick=0.008):
    """the part of the ellipsoid (radii r along ex, ey, ez about c) beyond the plane through c + pn * keep - a lid with a clean flat rim -
    given a little thickness."""
    c, pn = V_(c), V_(pn).normalized()
    a = V_((r[0] * ex.dot(pn), r[1] * ey.dot(pn), r[2] * ez.dot(pn))); k = keep / a.length; a.normalize()
    th0 = math.acos(max(-1.0, min(1.0, k))); u = a.orthogonal().normalized(); w = a.cross(u)
    bm = bmesh.new(); pole = bm.verts.new(a); rows = []
    for i in range(1, rings + 1):
        th = th0 * i / rings
        rows.append([bm.verts.new(a * math.cos(th) + (u * math.cos(2 * math.pi * j / seg) + w * math.sin(2 * math.pi * j / seg)) * math.sin(th)) for j in range(seg)])
    for j in range(seg): bm.faces.new((pole, rows[0][j], rows[0][(j + 1) % seg]))
    for r0, r1 in zip(rows, rows[1:]):
        for j in range(seg): bm.faces.new((r0[j], r1[j], r1[(j + 1) % seg], r0[(j + 1) % seg]))
    for v in bm.verts: v.co = c + ex * (v.co.x * r[0]) + ey * (v.co.y * r[1]) + ez * (v.co.z * r[2])
    bm.normal_update(); bm.faces.ensure_lookup_table()
    f0 = bm.faces[0]
    if f0.normal.dot(f0.calc_center_median() - c) < 0: bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
    bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=thick)
    return bm


def rh(x, y, z):
    """the frame (x, y, z) made right-handed (oriented_ball keeps its faces outward only then) by turning y round if it has to."""
    return (x, y, z) if x.cross(y).dot(z) > 0 else (x, -y, z)


def wing_fin(P, name, hub, d0, d1, n, L0, L1, back=(0, -1, 0), bend=0.1, cup=0.1, slot_web="Accent", slot_ray="Trim"):
    """a flying fish's wing: n rays from the root at hub, the leading one (along d0, L0 long) the stoutest, the rest swept round toward d1
    and shortening to L1, each bowed a little toward back and the middle ones toward the front (the wing cupped, so it never turns to a
    line); the web between them dips between the tips; one part named name (its hub the pivot)."""
    hub, d0, d1, back = V_(hub), V_(d0).normalized(), V_(d1).normalized(), V_(back).normalized()
    nrm = d0.cross(d1).normalized(); nrm = nrm if nrm.y > 0 else -nrm
    rays = []
    for k in range(n):
        f = k / (n - 1); d = d0.slerp(d1, f); L = L0 + (L1 - L0) * f ** 1.15
        rays.append([hub + d * (L * t) + back * (bend * L * t * t) + nrm * (cup * L * t * math.sin(math.pi * f)) for t in (0.0, 0.25, 0.5, 0.75, 1.0)])
    polys = []
    for k in range(n - 1):
        r0, r1 = rays[k], rays[k + 1]
        for j in range(3): polys.append([tuple(r0[j]), tuple(r0[j + 1]), tuple(r1[j + 1]), tuple(r1[j])])
        m = (r0[4] + r1[4]) * 0.5 + (hub - (r0[4] + r1[4]) * 0.5) * 0.035
        polys += [[tuple(r0[3]), tuple(r0[4]), tuple(m)], [tuple(r0[3]), tuple(m), tuple(r1[3])], [tuple(r1[3]), tuple(m), tuple(r1[4])]]
    P.part(name, st_cloth(polys, 0.018), slot_web, tuple(hub), 0, True)
    for k, pts in enumerate(rays):
        r = 0.04 if k == 0 else 0.026
        P.part(name, pipe(pts, [r, r * 0.8, r * 0.62, r * 0.45, 0.0], 6), slot_ray, tuple(hub))


def S2_leviathan():
    """THE ABYSS LEVIATHAN (2026-10-14, remade like the alien / west / treasure bosses): the real sea serpent - a giant oarfish risen out of
    the deep, wearing the head of a deep-sea dragonfish. The long ribbon of a body, flat from side to side and deepest behind the head,
    swims through the air in a slow S, dark teal along the back fading into bright silver, the upper flanks crossed by short dark streaks in
    an even rhythm, two rows of glowing photophores down the lower flanks; the blood-red dorsal fin runs its whole length on ivory rays, its
    edge dipping between them, and a small red fan of a tail. The head: the oarfish's crown of long red rays standing up and back over it,
    each with its little flag; huge eyes burning gold under bony brows, a glowing light organ under each one; the silver gill covers; and
    the dragonfish's jaws hinged far behind the eyes and gaping, needle fangs top and bottom too long to close over, the longest at the
    front, a glow deep in the throat, and from the chin a long barbel ending in a glowing lure.
    It flies as a flying fish does: two enormous red pectoral fins behind the head spread like wings on stout ivory rays, the leading ray
    the longest, beating (FlapL / FlapR); the tail wags (WagTail)."""
    P = Boss("leviathan", AB_pal(Base=((0.035, 0.14, 0.2), 0.45), Belly=((0.74, 0.79, 0.83), 0.55), Accent=((0.74, 0.06, 0.09), 0.5),
                                 Trim=((0.93, 0.89, 0.8), 0.5), Glass=((0.6, 0.92, 1.0), 0.9), Dark=((0.09, 0.02, 0.03), 0.5),
                                 Glow=((0.2, 0.95, 1.0), 0.5), Metal=((0.7, 0.75, 0.8), 0.8), Lamp=((1.0, 0.78, 0.22), 0.8)))
    glow_strength(P, 2.2)
    # ---- the head is built in its own frame: +Y from the nape (0) to the snout tip (1), +Z up; H() sets it on the boss (1.25 times, tipped down)
    HB = V_((0, 1.3, 1.0)); HK = 1.25
    HR = Matrix.Rotation(math.radians(-6), 3, "X") @ Matrix.Scale(HK, 3); HI = HR.inverted()
    def H(bm): return xf(bm, HR, tuple(HB))
    def hpt(p): return HB + HR @ V_(p)
    def loc(c, n): return HI @ (c - HB), (HI @ n).normalized()
    # ---- the body: an S of ribbon trailing back and down from the head, its back kept to the sky
    ctrl = [hpt((0, 0.08, 0.0)), hpt((0, -0.15, 0.0)), (0, 0.95, 0.7), (0.25, 0.8, 0.15), (0.78, 0.55, -0.35), (0.62, 0.25, -0.75), (-0.1, 0.05, -0.95),
            (-0.75, -0.2, -1.15), (-0.62, -0.55, -1.5), (0.05, -0.75, -1.65), (0.62, -0.95, -1.78), (1.1, -1.1, -1.8)]
    sp, us = resample(st_spline(ctrl, 12), 150); N = len(sp); BL = us[-1]
    FR = []
    for i in range(N):
        t = (sp[min(i + 1, N - 1)] - sp[max(i - 1, 0)]).normalized()
        side = t.cross(V_((0, 0, 1))).normalized(); up = side.cross(t).normalized()
        FR.append((t, side, up))
    def U(i): return us[i] / BL
    RX = [lerp_keys(U(i), [(0, 0.14), (0.06, 0.13), (0.3, 0.11), (0.7, 0.07), (1, 0.016)]) for i in range(N)]
    RU = [lerp_keys(U(i), [(0, 0.27), (0.06, 0.31), (0.25, 0.27), (0.6, 0.17), (0.9, 0.07), (1, 0.03)]) for i in range(N)]
    RD = [lerp_keys(U(i), [(0, 0.25), (0.06, 0.28), (0.25, 0.24), (0.6, 0.15), (0.9, 0.06), (1, 0.025)]) for i in range(N)]
    SEG = 24
    P.obj("Body", hide_attrs(st_loft(sp, RX, RU, RD, FR, SEG, 1.25), us, SEG), lambda c, nn: "Base" if nn.z > 0.62 else "Belly", 0)
    def at(i, a, out=0.0):   # the point a degrees round the body at ring i (90 the back, -90 the belly), out from the hide
        t, side, up = FR[i]; ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        q = side * (math.copysign(abs(ca) ** (1 / 1.25), ca) * RX[i]) + up * (math.copysign(abs(sa) ** (1 / 1.25), sa) * (RU[i] if sa > 0 else RD[i]))
        return sp[i] + q + q.normalized() * out
    def ring_at(s): return min(N - 1, max(0, int(round(s / BL * (N - 1)))))
    # the dorsal fin: one red web from the nape to the tail on ivory rays 13 cm apart, raked back, its edge dipping between them
    rays = []
    s = 0.45
    while s < BL - 0.12:
        i = ring_at(s); t, side, up = FR[i]
        h = lerp_keys(s / BL, [(0, 0.15), (0.12, 0.28), (0.35, 0.3), (0.7, 0.2), (1, 0.08)])
        b0 = sp[i] + up * (RU[i] - 0.02); rays.append((i, b0, b0 + up * h - t * (h * 0.4)))
        s += 0.13
    quads = []
    for (ia, a0, a1), (ib, b0, b1) in zip(rays, rays[1:]):
        e0, e1 = a0.lerp(a1, 0.9), b0.lerp(b1, 0.9); m = (e0 + e1) * 0.5 - FR[(ia + ib) // 2][2] * 0.022
        quads += [[tuple(a0), tuple(e0), tuple(m), tuple(b0)], [tuple(b0), tuple(m), tuple(e1)]]
    P.part("ClothDorsal", st_cloth(quads, 0.014), "Accent", (0, 0, 0), 0, True)
    for (i, b0, b1) in rays:
        P.obj("Ray", pipe([b0, b0.lerp(b1, 0.5), b1], [0.017, 0.012, 0.0], 5), "Trim")
    # two rows of photophores down each lower flank, 16 cm apart, shrinking with the body
    s = 0.5
    while s < BL - 0.35:
        i = ring_at(s); r = 0.012 + 0.024 * RD[i] / 0.28
        for a in (-28, -50, 208, 230):
            P.obj("Photophore", ball(tuple(at(i, a, -r * 0.3)), (r, r, r), 8, 4), "Glow")
        s += 0.16
    # the tail: a small red fan, wagging
    tt = FR[-1][0]
    fish_fin(P, "WagTail", sp[-1] - tt * 0.04, tt, V_((0, 0, 1)), 9, 0.46, 120, slot_web="Accent", slot_ray="Trim", curve=0.0)

    # ---- the skull: deep at the back, the forehead sloping to the snout, the roof of the mouth rising to the snout tip
    prof = st_spline([(-0.12, 0.12, 0.25, 0.23), (0.0, 0.18, 0.29, 0.27), (0.12, 0.21, 0.31, 0.27), (0.25, 0.215, 0.3, 0.2), (0.4, 0.2, 0.27, 0.12),
                      (0.55, 0.175, 0.22, 0.075), (0.7, 0.14, 0.16, 0.05), (0.82, 0.1, 0.11, 0.04), (0.92, 0.06, 0.07, 0.033), (0.99, 0.02, 0.025, 0.02)], 4)
    def pf(pr, y, col):   # a column of a profile at y
        for a, b in zip(pr, pr[1:]):
            if a[0] <= y <= b[0]: return a[col] + (b[col] - a[col]) * (y - a[0]) / max(1e-6, b[0] - a[0])
        return pr[0][col] if y < pr[0][0] else pr[-1][col]
    SQH = 1.3
    def sk0(y, a):   # the point on the skull a degrees round its section at y (0 the right side, 90 the top)
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        return V_((math.copysign(abs(ca) ** (1 / SQH), ca) * pf(prof, y, 1), y,
                   math.copysign(abs(sa) ** (1 / SQH), sa) * (pf(prof, y, 2) if sa > 0 else pf(prof, y, 3))))
    def skn(y, a):
        n = (sk0(y + 0.01, a) - sk0(y - 0.01, a)).cross(sk0(y, a + 1) - sk0(y, a - 1)).normalized()
        return n if n.dot(sk0(y, a) - V_((0, y, 0))) > 0 else -n
    def sk(y, a, out=0.0): return sk0(y, a) + skn(y, a) * out
    def sx(y, z):   # how far out the skull's side is at (y, z)
        h = pf(prof, y, 2) if z > 0 else pf(prof, y, 3)
        return pf(prof, y, 1) * max(0.0, 1 - min(1.0, abs(z) / h) ** SQH) ** (1 / SQH)
    fr0 = (V_((0, 1, 0)), V_((1, 0, 0)), V_((0, 0, 1)))
    skull = st_loft([V_((0, q[0], 0)) for q in prof], [q[1] for q in prof], [q[2] for q in prof], [q[3] for q in prof], [fr0] * len(prof), 28, SQH)
    def skull_paint(c, n):
        l, ln = loc(c, n)
        if l.y > 0.17 and ln.z < -0.5 and abs(l.x) < 0.8 * pf(prof, l.y, 1): return "Dark"   # the roof of the mouth
        return "Base" if ln.z > 0.62 else "Belly"
    P.obj("Skull", H(hide_attrs(skull)), skull_paint, 0)
    # the upper jaw: a silver lip along each side of the mouth from the corner, far behind the eye, to the snout, and the fangs hanging from it
    def fang(base, tip, r):   # a needle, its front edge bowed forward (+Y), raked back to the tip
        L = (tip - base).length; fw = V_((0, 1, 0))
        pts = bez(base, base.lerp(tip, 0.35) + fw * 0.12 * L, base.lerp(tip, 0.7) + fw * 0.08 * L, tip, 6)
        return pipe(pts, [r, r * 0.92, r * 0.8, r * 0.64, r * 0.46, r * 0.26, 0.0], 6)
    for s in (1, -1):
        lip = [sk(y, s * -22 if s > 0 else 180 + 22, -0.004) for y in [0.17 + 0.8 * k / 16 for k in range(17)]]
        P.obj("Lip", H(pipe(lip, [0.0] + [0.024] * 13 + [0.02, 0.014, 0.0], 8)), "Belly")
        for y, L in ((0.9, 0.17), (0.79, 0.27), (0.68, 0.15), (0.58, 0.12), (0.48, 0.1), (0.38, 0.085), (0.29, 0.07)):
            b = sk(y, s * -28 if s > 0 else 180 + 28, -0.012)
            P.obj("Fang", H(fang(b, b + V_((-s * 0.1 * L, -0.3 * L, -L)), 0.016 + 0.03 * L)), "Trim")
    P.obj("Gullet", H(ball((0, 0.2, -0.14), (0.12, 0.08, 0.08), 16, 8)), "Dark")
    # ---- the lower jaw, from its hinge far behind the eye to the chin, dropped wide open; its own silver lip and needles
    JA = 44; JH = V_((0, 0.14, -0.2)); JR = Matrix.Rotation(math.radians(-JA), 3, "X"); JI = JR.inverted()
    def JX(bm): return H(xf(bm, JR, tuple(JH - JR @ JH)))
    def jpt(p): return hpt(JH + JR @ (V_(p) - JH))
    jprof = st_spline([(0.08, 0.165, 0.03, 0.06, -0.215), (0.25, 0.185, 0.025, 0.08, -0.17), (0.45, 0.165, 0.02, 0.075, -0.115), (0.65, 0.13, 0.02, 0.06, -0.075),
                       (0.82, 0.085, 0.02, 0.05, -0.05), (0.95, 0.04, 0.018, 0.04, -0.04), (1.0, 0.015, 0.01, 0.02, -0.04)], 4)
    SQJ = 1.2
    def jk(y, a):
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        return V_((math.copysign(abs(ca) ** (1 / SQJ), ca) * pf(jprof, y, 1), y,
                   pf(jprof, y, 4) + math.copysign(abs(sa) ** (1 / SQJ), sa) * (pf(jprof, y, 2) if sa > 0 else pf(jprof, y, 3))))
    jaw = st_loft([V_((0, q[0], q[4])) for q in jprof], [q[1] for q in jprof], [q[2] for q in jprof], [q[3] for q in jprof], [fr0] * len(jprof), 22, SQJ)
    def jaw_paint(c, n):
        l, ln = loc(c, n); l = JH + JI @ (l - JH); ln = (JI @ ln).normalized()
        return "Dark" if ln.z > 0.35 and abs(l.x) < 0.8 * pf(jprof, l.y, 1) else "Belly"
    P.obj("Jaw", JX(hide_attrs(jaw)), jaw_paint, 0)
    for s in (1, -1):
        lip = [jk(y, 40 if s > 0 else 140) for y in [0.1 + 0.88 * k / 16 for k in range(17)]]
        P.obj("Lip", JX(pipe(lip, [0.0] + [0.02] * 13 + [0.017, 0.012, 0.0], 8)), "Belly")
        for y, L in ((0.93, 0.3), (0.81, 0.16), (0.69, 0.13), (0.57, 0.105), (0.45, 0.088), (0.34, 0.072)):
            b = jk(y, 48 if s > 0 else 132) - V_((0, 0, 0.008))
            P.obj("Fang", JX(fang(b, b + V_((-s * 0.1 * L, -0.25 * L, L)), 0.016 + 0.03 * L)), "Trim")
    # ---- the eyes: huge and burning gold, a black pupil, a dark rim, a bony brow scowling down to the front, a light organ under each
    for s in (1, -1):
        a = 24 if s > 0 else 156
        ec, en = sk(0.56, a, -0.015), skn(0.56, a)
        f = (en * 0.78 + V_((0, 0.45, 0))).normalized(); ex, ey, ez = frame_rh(f)
        P.obj("EyeRing", H(oriented_ball(ec - ey * 0.005, (0.12, 0.035, 0.116), ex, ey, ez, 22, 11)), "Dark")
        P.obj("Eye", H(oriented_ball(ec + ey * 0.0, (0.1, 0.05, 0.096), ex, ey, ez, 22, 11)), "Lamp")
        P.obj("Pupil", H(oriented_ball(ec + ey * 0.043, (0.026, 0.02, 0.05), ex, ey, ez, 14, 7)), "Dark")
        fw = (V_((0, 1, 0)) - ey * ey.y).normalized(); upv = (ez - fw * ez.dot(fw)).normalized(); R = 0.12
        # the heavy upper lid, its edge sloping down to the front: the scowl
        P.obj("Lid", H(ell_cap(ec, (0.11, 0.062, 0.106), ex, ey, ez, upv + fw * 0.5, 0.028)), "Base")
        brow = bez(ec + ey * 0.02 - fw * R * 0.95 + upv * R * 0.75, ec + ey * 0.04 - fw * R * 0.3 + upv * R * 1.18,
                   ec + ey * 0.04 + fw * R * 0.45 + upv * R * 0.98, ec + ey * 0.025 + fw * R * 0.95 + upv * R * 0.35, 10)
        P.obj("Brow", H(pipe(brow, [0.012, 0.026, 0.034, 0.038, 0.038, 0.036, 0.033, 0.029, 0.024, 0.016, 0.0], 8)), "Base")
        so = sk(0.38, -24 if s > 0 else 204, -0.012); son = skn(0.38, -24 if s > 0 else 204)
        P.obj("Suborbital", H(oriented_ball(so, (0.026, 0.085, 0.03), *rh(son, V_((0, 1, 0)), son.cross(V_((0, 1, 0))).normalized()), 12, 6)), "Glow")
        # the gill cover, silver, and the dark slit round its back edge
        oc = V_((s * (sx(0.12, -0.03) - 0.012), 0.12, -0.03))
        P.obj("Operculum", H(oriented_ball(oc, (0.03, 0.13, 0.19), *rh(V_((s, 0, 0)), V_((0, 1, 0)), V_((0, 0, 1))), 18, 9)), "Metal")
        slit = []
        for k in range(11):
            th = math.pi * k / 10; y = 0.12 - 0.13 * math.sin(th) - 0.006; z = -0.03 + 0.19 * math.cos(th)
            slit.append(V_((s * (sx(y, z) + 0.002), y, z)))
        P.obj("GillSlit", H(pipe(slit, [0.0, 0.01, 0.013, 0.015, 0.016, 0.016, 0.016, 0.015, 0.013, 0.01, 0.0], 6)), "Dark")
    # ---- the crown: the oarfish's long red crest rays, a middle one and three pairs splaying out, standing up and raked back, each with a flag
    for j, (y, L) in enumerate(((0.44, 0.8), (0.37, 0.72), (0.29, 0.62), (0.21, 0.5))):
        for s in ((1,) if j == 0 else (1, -1)):
            root = V_((s * 0.03 * j, y, pf(prof, y, 2) - 0.02))
            d = V_((s * 0.38 * j, -0.55 - 0.1 * j, 1.0 - 0.1 * j)).normalized(); bk = V_((s * 0.1 * j, -1, -0.2)).normalized()
            pts = bez(root, root + d * L * 0.4, root + d * L * 0.75 + bk * L * 0.12, root + d * L * 0.95 + bk * L * 0.35, 10)
            P.obj("Crest", H(pipe(pts, [0.03, 0.028, 0.026, 0.024, 0.021, 0.019, 0.016, 0.013, 0.01, 0.007, 0.0], 6)), "Accent")
            fd = (pts[-1] - pts[-4]).normalized(); fn = (V_((0, 1, 0)) - fd * fd.y).normalized(); fwid = fd.cross(fn).normalized()
            P.obj("CrestFlag", H(oriented_ball(pts[-3] - fd * 0.04, (0.032, 0.16, 0.009), fwid, fd, fn, 12, 6)), "Accent")
    # ---- the barbel from the chin, and its lure
    chin = jpt((0, 0.97, -0.075))
    bar = bez(chin, chin + V_((0, 0.14, -0.26)), chin + V_((0.05, 0.16, -0.62)), chin + V_((0.0, 0.08, -0.86)), 16)
    P.obj("Barbel", pipe(bar, [0.024] * 14 + [0.02, 0.016, 0.014], 6), "Base")
    lp = bar[-1] + V_((0, 0, -0.06))
    P.obj("Lure", ball(tuple(lp), (0.075, 0.075, 0.09), 14, 7), "Lamp")
    for k in range(5):
        a = 2 * math.pi * k / 5
        P.obj("LureFilament", pipe(bez(lp, lp + V_((math.cos(a) * 0.06, math.sin(a) * 0.06, -0.12)), lp + V_((math.cos(a) * 0.12, math.sin(a) * 0.12, -0.16)),
                                       lp + V_((math.cos(a) * 0.15, math.sin(a) * 0.15, -0.24)), 5), [0.012, 0.01, 0.008, 0.006, 0.004, 0.0], 4), "Glow")
    # ---- the wings: the pectoral fins behind the gill covers, spread like a flying fish's and beating
    for s in (1, -1):
        wing_fin(P, "FlapR" if s > 0 else "FlapL", hpt((s * 0.15, -0.04, -0.14)), V_((s * 0.75, -0.05, 0.66)), V_((s * 0.85, -0.25, -0.45)), 12, 2.0, 0.85)
    mz = hpt((0, 0.26, -0.21))   # deep in the throat, between the jaws
    P.part("Muzzle", ball(tuple(mz), (0.015, 0.015, 0.015), 6, 3), "Dark", tuple(mz))
    return P



def scute_attrs(bm, centres, sizes, proj, bulge=0.02, groove=0.026, gw=0.022, mask=None):
    """lays a turtle's plates over a shell: each vertex finds its plate - the nearest of the 2D centres, through proj - and is marked for the
    bake's tortoiseshell with "sr" (from the plate's centre, about 1 at its edge), "se" (from the seam to the nearest other plate), "sk" (which
    plate, 0..1), "rho" (proj's length: 0 the middle of the back, 1 the rim) and "ox", "oy" (where it lies from its plate's centre, for the
    flames that radiate from it); where mask allows, each plate is domed a little and the seams between them sunk."""
    lr, le, lk, lh, lx, ly = (bm.verts.layers.float.new(n) for n in ("sr", "se", "sk", "rho", "ox", "oy"))
    bm.verts.ensure_lookup_table(); bm.normal_update()
    C = [V_((c[0], c[1], 0)) for c in centres]
    moves = []
    for v in bm.verts:
        q = proj(v.co); q3 = V_((q[0], q[1], 0))
        d = [(q3 - c).length_squared for c in C]
        k1 = min(range(len(C)), key=lambda k: d[k]); c1 = C[k1]
        e = min((d[k] - d[k1]) / (2 * max(1e-6, (C[k] - c1).length)) for k in range(len(C)) if k != k1)
        sr = math.sqrt(d[k1]) / sizes[k1]
        v[lr] = sr; v[le] = e; v[lk] = (math.sin(k1 * 12.9898 + 1.3) * 43758.5453) % 1.0; v[lh] = q3.length
        v[lx] = (q3 - c1).x / sizes[k1]; v[ly] = (q3 - c1).y / sizes[k1]
        if mask is None or mask(v.co):
            big = sizes[k1] > 0.2
            moves.append((v, v.normal * ((bulge * max(0.0, 1 - sr * sr) if big else 0.0) - groove * (1.0 if big else 0.45) * math.exp(-(e / gw) ** 2))))
    for v, dv in moves: v.co += dv
    return bm


def flipper(keys, pitch, dihedral, root, side=1, ss_secs=None):
    """a sea turtle's flipper: airfoil sections (x out from the shoulder, leading edge, trailing edge, thickness) swept along x - thick at the
    leading edge, a knife at the trailing one - then turned (pitch about its span, raised by the dihedral) and set on the shoulder; side -1 the
    left one, mirrored. Returns the mesh and the matrix that took it there."""
    bm = sweep([(x, airfoil(le, te, th, 0.0)) for (x, le, te, th) in keys], "x")
    M = Matrix.Rotation(math.radians(-dihedral), 3, "Y") @ Matrix.Rotation(math.radians(pitch), 3, "X")
    if side < 0:
        S = Matrix.Scale(-1, 3, V_((1, 0, 0))); M = S @ M @ S
        for v in bm.verts: v.co.x = -v.co.x
        bmesh.ops.reverse_faces(bm, faces=bm.faces)
    for v in bm.verts: v.co = M @ v.co + V_(root)
    return bm, M


def S2_turtle():
    """THE CITADEL TURTLE (2026-10-14, remade like the alien / west / treasure bosses): the last boss - an ancient loggerhead, the oldest
    thing in the sea, built like the real animal. Its shell is a real carapace: five plates down the spine, four each side, a ring of
    two dozen small ones round the rim, every plate domed, laid down in growth rings and streaked like tortoiseshell, the seams between
    them sunk and dark, green with algae and crusted with barnacles toward the rim; the pale plastron beneath. The great head is armoured in
    scales edged pale, heavy plates over the eyes that make it glower, the eyes glowing sea-green between thick lids, the hooked horn beak
    of a loggerhead open on its serrated edge, barnacles on its crown; the old gold circlet with its pearl. A thick wrinkled neck.
    The cartoon idea kept: a whole white sea citadel on its back - a stone platform and curtain wall, six round towers with gold roofs and
    blue banners, the gatehouse facing you with a glowing portcullis and cannon, the keep, and on it the lighthouse whose beam turns; water
    pouring off the rim, palms, gulls circling the towers.
    It flies as a sea turtle swims - which is flying: the long front flippers, curved back like wings, scaled, a claw on each leading edge
    and a gold band round each, raised in the stroke and beating (FlapL / FlapR); the short hind flippers steer."""
    P = Boss("turtle", AB_pal(Base=((0.1, 0.19, 0.15), 0.45), Belly=((0.9, 0.82, 0.6), 0.4), Accent=((0.2, 0.09, 0.035), 0.55),
                              Trim=((0.98, 0.76, 0.24), 0.85), Glass=((0.32, 0.62, 0.95), 0.9), Dark=((0.05, 0.04, 0.04), 0.5),
                              Glow=((0.4, 1.0, 0.75), 0.5), Metal=((0.93, 0.91, 0.86), 0.4), Lamp=((1.0, 0.8, 0.45), 0.8)))
    glow_strength(P, 2.0)
    # ---- the carapace: a low dome, widest a third from the front, tapering to the tail; its plates (scutes) laid out like a loggerhead's
    R, YS, H0 = 1.15, 1.18, 0.62
    def outline(phi): return 1 + 0.05 * math.cos(phi) - 0.05 * math.cos(2 * phi)
    def dome(rho): return H0 * max(0.0, 1 - rho ** 2.3) ** 0.55
    NR, NS = 44, 160
    bm = bmesh.new(); pole = bm.verts.new((0, 0, dome(0))); rings = []
    prof = [(i / NR, None) for i in range(1, NR + 1)] + [(1.022, -0.035), (1.03, -0.08), (1.015, -0.11), (0.95, -0.13)]
    for rho, z in prof:
        ring = []
        for j in range(NS):
            phi = 2 * math.pi * j / NS; f = outline(phi)
            ring.append(bm.verts.new((math.sin(phi) * R * rho * f, math.cos(phi) * R * YS * rho * f, dome(min(rho, 1.0)) if z is None else z)))
        rings.append(ring)
    for j in range(NS): bm.faces.new((pole, rings[0][j], rings[0][(j + 1) % NS]))
    for r0, r1 in zip(rings, rings[1:]):
        for j in range(NS): bm.faces.new((r0[j], r1[j], r1[(j + 1) % NS], r0[(j + 1) % NS]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    cen, siz = [], []
    for y in (0.66, 0.33, 0.0, -0.33, -0.64): cen.append((0, y)); siz.append(0.3)                      # the vertebral plates
    for x, y in ((0.5, 0.44), (0.55, 0.15), (0.55, -0.15), (0.48, -0.44)):                               # the costal plates
        for s in (1, -1): cen.append((s * x, y)); siz.append(0.3)
    for k in range(24):                                                                                  # the marginal plates
        a = 2 * math.pi * k / 24; cen.append((math.sin(a) * 0.92, math.cos(a) * 0.92)); siz.append(0.13)
    def sproj(p):
        phi = math.atan2(p.x, p.y / YS); f = outline(phi)
        return (p.x / (R * f), p.y / (R * YS * f))
    P.obj("Carapace", scute_attrs(bm, cen, siz, sproj, mask=lambda p: p.z > -0.06), "Accent", 0)
    P.obj("Plastron", ball((0, 0.02, -0.12), (1.02, 1.28, 0.25), 36, 12), lambda c, n: "Belly" if n.z < 0.2 else "Accent")
    # barnacles: a cluster on every other rim plate down the back half, three on the crown of the head
    def barnacle(c, nrm, r):
        x, y, z = sq_axes(V_(nrm))
        bm = lathe([(r, 0.0), (r * 0.72, r * 0.9), (r * 0.42, r * 1.05), (r * 0.3, r * 0.75), (0.0, r * 0.7)], 9, "z")
        return xf(bm, Matrix((x, y, z)).transposed(), tuple(c))
    for k in range(5, 20, 2):
        a = 2 * math.pi * k / 24
        for dx, dy, rr in ((0.0, 0.0, 0.045), (0.06, 0.03, 0.032), (-0.05, 0.045, 0.028)):
            rho = 0.9; f = outline(a)
            p = V_((math.sin(a) * R * rho * f + dx, math.cos(a) * R * YS * rho * f + dy, 0)); p.z = dome(rho) - 0.005
            nrm = V_((p.x / (R * R), p.y / (R * R * YS * YS), 0.5)).normalized()
            P.obj("Barnacle", barnacle(p, nrm, rr), "Belly")

    h0 = len(P.parts)
    # ---- the neck, thick and folded, out from under the front of the shell
    neck = [V_(p) for p in ((0, 0.95, -0.16), (0, 1.15, -0.14), (0, 1.32, -0.1), (0, 1.5, -0.02))]
    P.obj("Neck", st_loft(neck, [0.3, 0.3, 0.28, 0.26], [0.22, 0.22, 0.22, 0.21], [0.24, 0.24, 0.23, 0.21], spine_frames(neck), 24, 1.1),
          lambda c, n: "Belly" if n.z < -0.4 else "Base")
    for k, y in enumerate((1.1, 1.2, 1.3)):
        P.obj("NeckFold", ring_on((0, y, -0.15 + 0.02 * k), (0, 1, 0.12), 0.255 - 0.01 * k, 0.028, 24, 6), "Base")
    # ---- the head: broad, heavy at the cheeks, the snout short and steep
    hk = st_spline([(1.45, 0.26, 0.22, 0.21, 0.0), (1.58, 0.33, 0.29, 0.25, 0.03), (1.76, 0.355, 0.31, 0.24, 0.04), (1.96, 0.32, 0.28, 0.19, 0.04),
                    (2.1, 0.24, 0.2, 0.13, 0.02), (2.19, 0.15, 0.12, 0.08, 0.0), (2.23, 0.05, 0.05, 0.03, -0.01)], 4)
    fry = (V_((0, 1, 0)), V_((1, 0, 0)), V_((0, 0, 1)))
    P.obj("Head", st_loft([V_((0, q[0], q[4])) for q in hk], [q[1] for q in hk], [q[2] for q in hk], [q[3] for q in hk], [fry] * len(hk), 28, 1.2),
          lambda c, n: "Belly" if n.z < -0.55 and c.y < 2.0 else "Base")
    def hq(y, col):
        for a_, b_ in zip(hk, hk[1:]):
            if a_[0] <= y <= b_[0]: return a_[col] + (b_[col] - a_[col]) * (y - a_[0]) / max(1e-6, b_[0] - a_[0])
        return hk[0][col] if y < hk[0][0] else hk[-1][col]
    def hs0(y, a):   # the point on the head a degrees round its section at y (0 its right side, 90 the top)
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        return V_((math.copysign(abs(ca) ** (1 / 1.2), ca) * hq(y, 1), y, hq(y, 4) + math.copysign(abs(sa) ** (1 / 1.2), sa) * (hq(y, 2) if sa > 0 else hq(y, 3))))
    def hn(y, a):
        n = (hs0(y + 0.01, a) - hs0(y - 0.01, a)).cross(hs0(y, a + 1) - hs0(y, a - 1)).normalized()
        return n if n.dot(hs0(y, a) - V_((0, y, hq(y, 4)))) > 0 else -n
    def hs(y, a, out=0.0): return hs0(y, a) + hn(y, a) * out
    # the beak: a horn sheath over the snout, hooked down at the tip, its cutting edges serrated; the lower beak on the jaw, dropped open
    bkk = st_spline([(1.98, 0.02, 0.235, 0.2, 0.11), (2.14, 0.0, 0.205, 0.165, 0.09), (2.27, -0.05, 0.135, 0.105, 0.055), (2.34, -0.12, 0.062, 0.052, 0.027),
                     (2.335, -0.19, 0.01, 0.01, 0.005)], 4)
    bk = [V_((0, q[0], q[1])) for q in bkk]; bfr = []
    for i in range(len(bk)):
        t = (bk[min(i + 1, len(bk) - 1)] - bk[max(i - 1, 0)]).normalized(); sd = V_((1, 0, 0)); bfr.append((t, sd, sd.cross(t).normalized()))
    P.obj("Beak", st_loft(bk, [q[2] for q in bkk], [q[3] for q in bkk], [q[4] for q in bkk], bfr, 26, 1.15), "Accent")
    JH = V_((0, 1.66, -0.12)); JR = Matrix.Rotation(math.radians(-17), 3, "X")
    def JX(bm): return xf(bm, JR, tuple(JH - JR @ JH))
    jkk = st_spline([(1.62, -0.14, 0.29, 0.045, 0.13), (1.85, -0.16, 0.27, 0.045, 0.13), (2.05, -0.18, 0.21, 0.04, 0.11), (2.22, -0.2, 0.12, 0.035, 0.08),
                     (2.3, -0.2, 0.04, 0.02, 0.04)], 4)
    P.obj("Jaw", JX(st_loft([V_((0, q[0], q[1])) for q in jkk], [q[2] for q in jkk], [q[3] for q in jkk], [q[4] for q in jkk], [fry] * len(jkk), 24, 1.2)),
          lambda c, n: "Dark" if n.z > 0.5 and c.y < 2.22 else ("Accent" if c.y > 2.02 else "Base"))
    P.obj("Mouth", JX(ball((0, 1.95, -0.135), (0.2, 0.3, 0.06), 18, 8)), "Dark")
    P.obj("Tongue", JX(ball((0, 1.98, -0.12), (0.1, 0.17, 0.04), 14, 7)), "Accent")
    ca, sa = math.cos(math.radians(25)) ** (1 / 1.15), math.sin(math.radians(25)) ** (1 / 1.15)
    cj, sj = math.cos(math.radians(35)) ** (1 / 1.2), math.sin(math.radians(35)) ** (1 / 1.2)
    for s in (1, -1):   # six points down each cutting edge, top and bottom
        for i in (3, 5, 7, 9, 11, 13):
            (t, sd, up), q = bfr[i], bkk[i]
            base = bk[i] + sd * (s * ca * q[2] * 0.97) - up * (sa * q[4] * 0.97)
            P.obj("Serration", cone(base, base - up * (0.05 - 0.002 * i) - t * 0.012, 0.02, 6), "Accent")
        for i in (4, 6, 8, 10, 12, 14):
            q = jkk[i]; base = V_((s * cj * q[2] * 0.97, q[0], q[1] + sj * q[3] * 0.97))
            P.obj("Serration", JX(cone(base, base + V_((0, -0.01, 0.045 - 0.0015 * i)), 0.018, 6)), "Accent")
    # the eyes: sea-green and glowing between thick lids, the heavy plate over each like a scowl
    for s in (1, -1):
        e = hs(2.03, 30 if s > 0 else 150, -0.022); f = (hn(2.03, 30 if s > 0 else 150) * 0.55 + V_((0, 0.7, 0.04))).normalized(); ex, ey, ez = frame_rh(f)
        P.obj("EyeRing", oriented_ball(e - ey * 0.012, (0.13, 0.052, 0.12), ex, ey, ez, 22, 11), "Dark")
        P.obj("Eye", oriented_ball(e, (0.092, 0.058, 0.086), ex, ey, ez, 20, 10), "Glow")
        P.obj("Pupil", oriented_ball(e + ey * 0.052, (0.027, 0.016, 0.036), ex, ey, ez, 14, 7), "Dark")
        fw = (V_((0, 1, 0)) - ey * ey.y).normalized(); upv = (ez - fw * ez.dot(fw)).normalized()
        P.obj("Lid", ell_cap(e, (0.099, 0.066, 0.093), ex, ey, ez, upv + fw * 0.65, 0.012, thick=0.014), "Base")
        P.obj("Lid", ell_cap(e, (0.098, 0.064, 0.092), ex, ey, ez, -upv - fw * 0.15, 0.05, thick=0.012), "Base")
    for y, a, rr in ((1.6, 68, 0.035), (1.64, 114, 0.03), (1.53, 92, 0.028)):   # barnacles on its crown
        P.obj("Barnacle", barnacle(hs(y, a, -0.006), hn(y, a), rr), "Belly")
    # the old gold circlet, now a diadem across the crown, its pearl at the front
    P.obj("Circlet", pipe([hs(1.84, a, 0.012) for a in range(16, 166, 6)], [0.0] + [0.026] * 23 + [0.0], 8), "Trim")
    pc, pnn = hs(1.86, 90, 0.0), hn(1.86, 90)
    P.obj("Pearl", ball(tuple(pc + pnn * 0.05), (0.058, 0.058, 0.058), 14, 7), "Metal")
    P.obj("PearlSet", ring_on(pc + pnn * 0.03, pnn, 0.058, 0.016, 16, 4), "Trim")

    HG = Matrix.Translation(V_((0, 1.45, 0.0))) @ Matrix.Scale(1.15, 4) @ Matrix.Translation(V_((0, -1.45, 0.0)))
    for ob in P.parts[h0:]:
        if ob.name.split(".")[0] not in ("Neck", "NeckFold"): ob.data.transform(HG)
    # ---- the front flippers: long and curved back like wings, raised in the stroke; a claw, a gold band; beating
    FK = [(0.0, 0.3, -0.3, 0.17), (0.2, 0.34, -0.3, 0.15), (0.55, 0.33, -0.26, 0.12), (0.95, 0.22, -0.22, 0.09), (1.35, 0.03, -0.22, 0.065),
          (1.7, -0.2, -0.3, 0.04), (1.9, -0.36, -0.4, 0.018)]
    for s in (1, -1):
        root = V_((s * 0.9, 0.82, -0.04))
        fb, FM = flipper(FK, -40, 26, root, s); FI = FM.inverted()
        def fpaint(c, n, root=root, FI=FI, s=s):
            l = FI @ (c - root); ln = FI @ n
            if 0.42 < abs(l.x) < 0.52: return "Trim"
            return "Belly" if ln.z < -0.2 else "Base"
        name = "FlapR" if s > 0 else "FlapL"
        P.part(name, fb, fpaint, tuple(root), 2)
        cb = root + FM @ V_((s * 0.62, 0.31, 0.0)); P.part(name, cone(cb, cb + FM @ V_((s * 0.06, 0.13, 0.0)), 0.035, 8), "Dark", tuple(root))
    # the hind flippers: short rounded paddles, steering
    HK_ = [(0.0, 0.17, -0.2, 0.1), (0.22, 0.2, -0.24, 0.08), (0.42, 0.12, -0.27, 0.05), (0.56, -0.02, -0.2, 0.02)]
    for s in (1, -1):
        hb, _ = flipper(HK_, 0, 8, V_((s * 0.62, -1.05, -0.08)), s)
        Rz = Matrix.Rotation(math.radians(-s * 52), 3, "Z"); c0 = V_((s * 0.62, -1.05, -0.08))
        P.obj("HindFlipper", xf(hb, Rz, tuple(c0 - Rz @ c0)), lambda c, n: "Belly" if n.z < -0.2 else "Base", 2)
    P.obj("Tail", pipe([(0, -1.3, -0.1), (0, -1.5, -0.13), (0, -1.66, -0.17)], [0.12, 0.08, 0.0], 10), "Base")

    # ---- the citadel: a stone platform levelled on the shell, the curtain wall, six towers, the gatehouse, the keep and the lighthouse
    P.hint = None
    P.obj("Platform", lathe([(0.9, 0.36), (0.92, 0.6), (0.88, 0.64), (0.0, 0.64)], 64, "z"), "Metal")
    P.obj("Wall", lathe([(0.8, 0.62), (0.8, 1.04), (0.72, 1.04), (0.72, 0.92), (0.0, 0.92)], 64, "z"), "Metal")
    for k in range(28):
        a = 2 * math.pi * (k + 0.5) / 28
        if (abs(math.sin(a)) < 0.3 and math.cos(a) > 0) or abs(abs(math.degrees(math.atan2(math.sin(a), math.cos(a)))) - 60) < 7: continue   # the gatehouse, the cannon
        P.obj("Merlon", box((math.sin(a) * 0.76, math.cos(a) * 0.76, 1.085), (0.085, 0.07, 0.09), Matrix.Rotation(-a, 3, "Z")), "Metal")
    for k in range(6):
        a = 2 * math.pi * k / 6 + math.pi / 6; c = (math.sin(a) * 0.8, math.cos(a) * 0.8, 0.0); out = V_((math.sin(a), math.cos(a), 0))
        P.obj("Tower", lathe([(0.17, 0.5), (0.17, 1.27), (0.205, 1.31), (0.205, 1.38), (0.0, 1.38)], 24, "z", c), "Metal")
        P.obj("Roof", lathe([(0.235, 1.37), (0.2, 1.43), (0.12, 1.6), (0.04, 1.77), (0.0, 1.8)], 24, "z", c), "Trim")
        P.obj("Finial", ball((c[0], c[1], 1.83), (0.03, 0.03, 0.03), 8, 4), "Trim")
        pole = V_((c[0], c[1], 1.8))
        P.obj("FlagPole", pipe([pole, pole + V_((0, 0, 0.36))], [0.012, 0.009], 5), "Trim")
        quads = []
        for i in range(6):   # the banner, streaming back and waving
            u0, u1 = i / 6, (i + 1) / 6
            def bp(u, v): return pole + V_((0.17 * u + 0.03 * math.sin(u * 7 + 1), -0.32 * u, 0.34 - 0.14 * v - 0.05 * u * v))
            quads.append([tuple(bp(u0, 0)), tuple(bp(u1, 0)), tuple(bp(u1, 1 - 0.4 * u1)), tuple(bp(u0, 1 - 0.4 * u0))])
        P.part("ClothBanner", st_cloth(quads, 0.012), "Glass", (0, 0, 0), 0, True)
        for z, kind in ((0.78, "Dark"), (1.08, "Lamp")):   # an arrow slit below, a lit window above, looking out
            w = V_(c) + out * 0.165; w.z = z
            P.obj("TowerWin", box(tuple(w), (0.05, 0.03, 0.13 if kind == "Dark" else 0.1), Matrix.Rotation(-a, 3, "Z")), kind)
    # the gatehouse facing you: its arch, the glowing portcullis, a gold shell over it, merlons; cannon on the wall either side
    P.obj("Gatehouse", box((0, 0.78, 0.9), (0.5, 0.3, 0.72)), "Metal")
    arch = [(x, 0.55) for x in (-0.13, 0.13)] + [(0.13 * math.cos(math.pi * k / 10), 0.8 + 0.13 * math.sin(math.pi * k / 10)) for k in range(11)]
    P.obj("GateArch", hull([(x, y, z) for (x, z) in arch for y in (0.925, 0.945)]), "Dark")
    for k in range(5):
        P.obj("Portcullis", box(((k - 2) * 0.048, 0.95, 0.76), (0.014, 0.012, 0.3)), "Glow")
    for z in (0.7, 0.8, 0.9): P.obj("Portcullis", box((0, 0.95, z), (0.22, 0.012, 0.012)), "Glow")
    P.obj("GateShell", lathe([(0.09, 0.0), (0.09, 0.012), (0.0, 0.02)], 18, "y", (0, 0.935, 1.08)), "Trim")
    for k in range(4):
        P.obj("GateMerlon", box(((k - 1.5) * 0.14, 0.78, 1.3), (0.085, 0.3, 0.09)), "Metal")
    for s in (1, -1):
        for b0, d in ((V_((s * 0.69, 0.4, 1.09)), V_((s * 0.05, 0.34, 0.02))),):
            b1 = b0 + d
            P.obj("Cannon", pipe([b0, b0.lerp(b1, 0.5), b1], [0.06, 0.052, 0.044], 12), "Dark")
            P.obj("CannonRim", ring_on(b1, (0, 1, 0), 0.05, 0.014, 12, 4), "Trim")
    # the keep, its corner turrets and merlons, and on it the lighthouse: black and white bands, a gold gallery, the lantern, the cupola
    KY = -0.12
    P.obj("Keep", box((0, KY, 1.23), (0.62, 0.56, 0.62)), "Metal")
    for k in range(12):
        t = k / 12 * 4; side = int(t); u = t - side
        p = [(-0.29 + 0.58 * u, 0.26), (0.29, 0.26 - 0.52 * u), (0.29 - 0.58 * u, -0.26), (-0.29, -0.26 + 0.52 * u)][side]
        P.obj("Merlon", box((p[0], KY + p[1], 1.585), (0.07, 0.07, 0.08)), "Metal")
    for sx in (1, -1):
        for sy in (1, -1):
            c = (sx * 0.31, KY + sy * 0.28, 0.0)
            P.obj("KeepTurret", lathe([(0.085, 1.25), (0.085, 1.6), (0.105, 1.63), (0.105, 1.66), (0.0, 1.66)], 14, "z", c), "Metal")
            P.obj("Roof", lathe([(0.12, 1.65), (0.06, 1.78), (0.0, 1.86)], 14, "z", c), "Trim")
    P.obj("Lighthouse", lathe([(0.21, 1.54), (0.165, 2.3), (0.0, 2.3)], 24, "z", (0, KY, 0)),
          lambda c, n: "Dark" if int((c.z - 1.54) / 0.152) % 2 == 1 else "Metal")
    P.obj("Gallery", lathe([(0.23, 2.28), (0.23, 2.33), (0.0, 2.33)], 24, "z", (0, KY, 0)), "Trim")
    P.obj("Lantern", lathe([(0.13, 2.33), (0.13, 2.56), (0.0, 2.56)], 16, "z", (0, KY, 0)), "Lamp")
    for k in range(8):
        a = 2 * math.pi * k / 8
        P.obj("LanternBar", pipe([(math.sin(a) * 0.14, KY + math.cos(a) * 0.14, 2.33), (math.sin(a) * 0.14, KY + math.cos(a) * 0.14, 2.56)], [0.012, 0.012], 4), "Trim")
    P.obj("Cupola", lathe([(0.19, 2.555), (0.1, 2.68), (0.0, 2.78)], 20, "z", (0, KY, 0)), "Trim")
    P.obj("Spire", cone((0, KY, 2.77), (0, KY, 3.0), 0.025, 6), "Trim")
    for s in (1, -1):   # the beam, turning
        P.part("SpinBeam", pipe([(s * 0.1, KY, 2.45), (s * 0.6, KY, 2.45), (s * 1.1, KY, 2.45), (s * 1.45, KY, 2.45)], [0.03, 0.075, 0.12, 0.15], 16), "Lamp", (0, KY, 2.45))
    # gulls circling the towers
    for k in range(5):
        a = 2 * math.pi * k / 5; c = V_((math.sin(a) * 1.45, KY + math.cos(a) * 1.45, 2.0 + 0.18 * math.sin(a * 2)))
        t = V_((math.cos(a), -math.sin(a), 0)); sd = V_((math.sin(a), math.cos(a), 0))
        P.part("SpinGulls", oriented_ball(c, (0.035, 0.08, 0.032), *rh(sd, t, V_((0, 0, 1))), 8, 4), "Metal", (0, KY, 2.0))
        for w in (1, -1):
            elbow = c + sd * w * 0.12 + V_((0, 0, 0.06)); tip = elbow + sd * w * 0.14 - t * 0.05 - V_((0, 0, 0.03))
            P.part("SpinGulls", pipe([c, elbow, tip], [0.022, 0.016, 0.0], 5), "Metal", (0, KY, 2.0))
            P.part("SpinGulls", pipe([elbow.lerp(tip, 0.6), tip], [0.012, 0.0], 4), "Dark", (0, KY, 2.0))
    # water pouring off the back of the rim in two short cascades, breaking into spray
    for a in (math.radians(145), math.radians(-145)):
        f = outline(a); top = V_((math.sin(a) * R * f, math.cos(a) * R * YS * f, 0.02))
        out = V_((math.sin(a), math.cos(a) / YS, 0)).normalized(); sd = V_((math.cos(a), -math.sin(a), 0)).normalized() * 0.11
        pts = bez(top - out * 0.25 + V_((0, 0, 0.26)), top + out * 0.1 + V_((0, 0, 0.05)), top + out * 0.22 + V_((0, 0, -0.2)), top + out * 0.25 + V_((0, 0, -0.45)), 8)
        P.part("ClothWater", st_cloth([[tuple(p - sd * (1 + 0.8 * i / 8)), tuple(q - sd * (1 + 0.8 * (i + 1) / 8)), tuple(q + sd * (1 + 0.8 * (i + 1) / 8)),
                                        tuple(p + sd * (1 + 0.8 * i / 8))] for i, (p, q) in enumerate(zip(pts, pts[1:]))], 0.02), "Glass", (0, 0, 0), 0, True)
        for j in range(5):
            r = 0.06 + 0.02 * (j % 2)
            P.obj("Foam", ball(tuple(pts[-1] + sd * (j - 2) * 0.9 + out * (0.03 * (j % 2)) + V_((0, 0, 0.02 * (j % 2)))), (r, r, r * 0.8), 8, 4), "Metal")
    # palms on the shell behind the wall
    for a in (math.radians(120), math.radians(-120)):
        f = outline(a); b = V_((math.sin(a) * R * 0.86 * f, math.cos(a) * R * YS * 0.86 * f, 0)); b.z = dome(0.86) - 0.02
        top = b + V_((math.sin(a) * 0.12, math.cos(a) * 0.12, 0.72))
        trunk = bez(b, b + V_((0, 0, 0.3)), top - V_((math.sin(a) * 0.08, math.cos(a) * 0.08, 0.15)), top, 8)
        P.obj("PalmTrunk", pipe(trunk, [0.055, 0.05, 0.047, 0.044, 0.041, 0.038, 0.035, 0.032, 0.03], 8), "Accent")
        for j in range(7):
            ja = 2 * math.pi * j / 7 + a; d = V_((math.sin(ja), math.cos(ja), 0)); sd = V_((math.cos(ja), -math.sin(ja), 0))
            rib = bez(top, top + d * 0.15 + V_((0, 0, 0.11)), top + d * 0.3 + V_((0, 0, 0.04)), top + d * 0.4 + V_((0, 0, -0.14)), 8)
            w = [0.0, 0.06, 0.075, 0.075, 0.068, 0.058, 0.044, 0.026, 0.0]
            P.obj("PalmLeaf", st_cloth([[tuple(rib[i] - sd * w[i]), tuple(rib[i + 1] - sd * w[i + 1]), tuple(rib[i + 1] + sd * w[i + 1]), tuple(rib[i] + sd * w[i])]
                                        for i in range(8)], 0.012), "Base")
    mz = HG @ V_((0, 2.12, -0.17))
    P.part("Muzzle", ball(tuple(mz), (0.02, 0.02, 0.02), 6, 3), "Dark", tuple(mz))
    return P


BOSSES = [("whale", S2_whale), ("roc", S2_roc), ("leviathan", S2_leviathan), ("turtle", S2_turtle),
          ("puffer", S2_puffer)]   # 2026-10-11 previews

# 2026-10-14: what each remade boss's parts are made of, for boss_bake.py (export bakes them into Boss_<id>_Albedo / _Normal / _Mask /
# _Emission beside the FBX)
BB.TABLES.update({
    "whale": ({"Base": "whale", "Belly": "whale", "Accent": "flesh", "Trim": "gold", "Glass": "silk", "Dark": "keratin", "Glow": "glow", "Metal": "barnacle", "Lamp": "lamp"},
              [("Spray", "water"), ("Baleen", "hair"), ("Pleat", "matte"), ("Gullet", "matte"), ("Pupil", "eye"), ("Blowhole", "matte"),
               ("Tongue", "flesh"), ("Throat", {"Accent": "flesh"})]),
    "puffer": ({"Base": "puffer", "Belly": "puffer", "Accent": "silk", "Trim": "gold", "Glass": "eye_white", "Dark": "matte", "Glow": "glow", "Metal": "gem", "Lamp": "gem"},
               [("Spine", "keratin"), ("Spot", "puffer"), ("Beak", "enamel"), ("Lips", "flesh"), ("Pupil", "eye"), ("Moustache", "hair"),
                ("CrownVelvet", "felt"), ("Jewel", {"Accent": "gem"}), ("Flap*", {"Belly": "fin", "Trim": "keratin"}), ("Sway*", {"Belly": "fin", "Trim": "keratin"}),
                ("WagTail", {"Belly": "fin", "Trim": "keratin"}), ("Pearl", "eye_white"), ("Glint", "eye")]),
    "leviathan": ({"Base": "oarfish", "Belly": "oarfish", "Accent": "membrane", "Trim": "bone", "Glass": "eye", "Dark": "flesh", "Glow": "glow",
                   "Metal": "silver", "Lamp": "lamp"},
                  [("Fang", "enamel"), ("Crest", "horn"), ("Eye", "glow"), ("Lure", "glow"), ("Pupil", "eye"), ("Brow", "skin"), ("Lid", "skin"), ("Barbel", "skin")]),
    "turtle": ({"Base": "turtle_skin", "Belly": "skin", "Accent": "tortoise", "Trim": "gold", "Glass": "water", "Dark": "matte", "Glow": "glow",
                "Metal": "stone", "Lamp": "lamp"},
               [("Beak", "beak"), ("Serration", "beak"), ("Jaw", {"Accent": "beak", "Dark": "flesh"}), ("Mouth", "flesh"), ("Tongue", "flesh"),
                ("Plastron", {"Belly": "shell_belly"}), ("Eye", "glow"), ("Pupil", "eye"), ("EyeRing", "skin"), ("Barnacle", "barnacle"),
                ("Pearl", "eye_white"), ("ClothBanner", "silk"), ("Foam", "cloud"), ("PalmTrunk", "wood_v"), ("PalmLeaf", "weed"),
                ("SpinGulls", {"Metal": "down", "Dark": "matte"}), ("Roof", "tiles"), ("Cupola", "tiles"), ("Cannon", "iron"), ("Lantern", "glow"), ("SpinBeam", "glow"),
                ("Flap*", {"Belly": "skin", "Dark": "keratin"})]),
    "roc": ({"Base": "down", "Belly": "down", "Accent": "horn", "Trim": "gold", "Glass": "water", "Dark": "feather", "Glow": "glow", "Metal": "cloud", "Lamp": "lamp"},
            [("Flap*", {"Base": "feather", "Dark": "feather"}), ("Tail", "feather"), ("Leg", "scales"), ("Toe", "scales"), ("Web", "skin"),
             ("Gape", "matte"), ("Nostril", "matte"), ("Groove", "matte"), ("Pupil", "eye"), ("Crescent", "down"), ("Jaw", "horn"), ("Hook", "horn"),
             ("Sulcus", "glow"), ("Bill", "horn"), ("Culmen", "horn"), ("Tube", "horn")]),
})

if __name__ == "__main__":
    os.makedirs(AB.OUT, exist_ok=True)
    for bid, fn in BOSSES:
        if ONLY and bid not in ONLY: continue
        P = fn()
        if AB.EXPORT and bid in BB.TABLES: BB.finish_baked(P, AB.OUT)   # the real surfaces baked into textures beside the FBX
        else: P.finish()
    print("DONE")
