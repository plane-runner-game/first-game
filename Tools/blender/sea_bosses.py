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


BOSSES = [("whale", S_whale), ("roc", S_roc), ("leviathan", S_leviathan), ("turtle", S_turtle),
          ("puffer", S_puffer)]   # 2026-10-11 previews

if __name__ == "__main__":
    os.makedirs(AB.OUT, exist_ok=True)
    for bid, fn in BOSSES:
        if ONLY and bid not in ONLY: continue
        fn().finish()
    print("DONE")
