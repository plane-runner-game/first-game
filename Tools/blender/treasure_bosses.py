# Sky Squad, the treasure island's five bosses (2026-10-11: "the bosses for the rest of the maps"): the captain parrot, the treasure mimic,
# the ghost captain, the cannon crab and skull rock. Built from code like the other worlds' bosses (alien_bosses.py lends its Boss class and
# shapes).
# Run: blender -b -P Tools/blender/treasure_bosses.py -- <out dir> [export] [ids,comma,separated]
# Conventions as alien_bosses.py: +Y nose, +Z up, +X right; "Flap*" rock about the nose axis, "Sway*" about the wing axis, "Spin*" turn slowly
# about up, "Cloth" stays still without the outline, "Muzzle" is where his shots leave from.
import bpy, bmesh, math, sys, os, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mathutils import Vector, Matrix
from enemy_planes import loft, sweep, lathe, box, hull, tube, mirror_x, airfoil
import alien_bosses as AB
from alien_bosses import Boss, xf, ball, pipe, cone, bez, torus, sheet, grow, ang

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ONLY = argv[2].split(",") if len(argv) > 2 and argv[2] else None

GOLD = ((0.98, 0.76, 0.22), 0.8)
BONE = ((0.95, 0.92, 0.82), 0.35)
BLACK = ((0.05, 0.05, 0.06), 0.5)


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

def fan(hub, tips, thick=0.02, scallop=0.12):
    polys = []
    for a, b in zip(tips, tips[1:]):
        mid = (a + b) * 0.5 + (hub - (a + b) * 0.5) * scallop
        polys.append([hub, a, mid]); polys.append([hub, mid, b])
    return sheet([[tuple(p) for p in poly] for poly in polys], thick)

def tricorn(P, c, r_in, r_out, lift, crown, emblem=True, paint="Dark"):
    """a pirate's tricorn: a round crown and a brim turned up between three corners (one to the front), gold-edged, a skull on the front."""
    c = Vector(c); N = 36; polys = []
    def pt(a, r, outer):
        if not outer: return c + Vector((math.sin(a) * r, math.cos(a) * r, 0.0))
        rr = r * (1 + 0.16 * math.cos(3 * a)); z = lift * (0.5 - 0.5 * math.cos(3 * a))
        return c + Vector((math.sin(a) * rr, math.cos(a) * rr, z))
    for i in range(N):
        a0 = 2 * math.pi * i / N; a1 = 2 * math.pi * (i + 1) / N
        polys.append([tuple(pt(a0, r_in * 0.9, False)), tuple(pt(a0, r_out, True)), tuple(pt(a1, r_out, True)), tuple(pt(a1, r_in * 0.9, False))])
    P.obj("Brim", sheet(polys, 0.05), paint, 0, False)
    edge = [pt(2 * math.pi * i / 48, r_out, True) for i in range(49)]
    P.obj("BrimEdge", pipe(edge, [0.025] * 49, 5, False), "Trim")
    P.obj("Crown", ball(tuple(c + Vector((0, 0, crown * 0.3))), (r_in, r_in, crown), 16, 8), paint, 1)
    if emblem:   # a little skull and crossbones on the front corner's upturned faces
        f = c + Vector((0, r_in * 0.95, crown * 0.55))
        P.obj("HatSkull", ball(tuple(f), (r_in * 0.22, r_in * 0.08, r_in * 0.2), 10, 5), "Belly")
        for s in (1, -1):
            P.obj("HatBone", pipe([f + Vector((-s * r_in * 0.3, 0.01, -r_in * 0.28)), f + Vector((s * r_in * 0.3, 0.01, r_in * 0.0 - r_in * 0.05))], [r_in * 0.04] * 2, 5), "Belly")
            P.obj("HatEye", ball(tuple(f + Vector((s * r_in * 0.08, r_in * 0.07, r_in * 0.03))), (r_in * 0.05, r_in * 0.02, r_in * 0.05), 6, 3), "Dark")

def coin(c, r=0.08, t=0.025, rot=None):
    bm = lathe([(0.0, -t * 0.5), (r, -t * 0.5), (r, t * 0.5), (0.0, t * 0.5)], 12, "z")
    return xf(bm, rot, c)

def rrot(rng):
    return (Matrix.Rotation(rng.uniform(-1.4, 1.4), 3, "X") @ Matrix.Rotation(rng.uniform(-1.4, 1.4), 3, "Y"))

def gold_heap(P, c, rx, ry, h, n, rng, name="Gold"):
    """a heap of gold: a domed mound of coins, loose coins and a few jewels on top."""
    c = Vector(c)
    P.obj(name, ball(tuple(c), (rx, ry, h), 14, 6), lambda q, nn: "Lamp" if nn.z > 0.2 else "Trim", 0)
    for k in range(n):
        a = rng.uniform(0, 2 * math.pi); r = rng.uniform(0, 0.9)
        p = c + Vector((math.sin(a) * rx * r, math.cos(a) * ry * r, h * math.sqrt(max(0.0, 1 - r * r)) * 0.95))
        if k % 6 == 5: P.obj("Jewel", hull([tuple(p + Vector(v) * 0.07) for v in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1.4), (0, 0, -0.6))]), "Glass", 0, False)
        else: P.obj("Coin", coin(p, 0.075, 0.025, rrot(rng)), "Trim", 0, False)


# ================================================================= 1. the captain parrot
def T_parrot():
    """The pirate captain parrot (2026-10-12, remade: "make it better"): a scarlet macaw grown to a monster in a navy captain's coat with gold
    lapels, two rows of gold buttons, gold-fringed epaulettes and a white lace jabot, a belt with a gold buckle and a rolled treasure map;
    a big head with a crest of red, gold and blue feathers, a fierce brow over a golden eye, an eye patch, a gold earring and a great ivory
    hooked beak open to squawk; a black tricorn with a skull badge and a blue-and-gold plume; a gold compass on a chain; layered wings - red
    coverts, a gold band, long blue primaries - that beat; long red and blue tail plumes; a cutlass raised in one talon and a flintlock
    pistol aimed at the player in the other; gold doubloons circling him."""
    P = Boss("parrot", {"Base": ((0.88, 0.10, 0.08), 0.5), "Belly": BONE, "Accent": ((0.08, 0.38, 0.92), 0.55), "Trim": GOLD,
                        "Glass": ((1.0, 0.80, 0.08), 0.5), "Dark": ((0.05, 0.06, 0.14), 0.5), "Glow": ((1.0, 0.85, 0.45), 0.5),
                        "Metal": ((0.72, 0.74, 0.80), 0.8), "Lamp": ((1.0, 0.85, 0.35), 0.8)})
    # the body, held upright toward the player, and the coat over it
    P.obj("Body", loft([(0.45, 0.05, 0.05, 0, 0.55), (0.38, 0.36, 0.4, 0, 0.35), (0.15, 0.48, 0.52, 0, 0.0), (-0.2, 0.44, 0.46, 0, -0.25),
                        (-0.55, 0.3, 0.28, 0, -0.38), (-0.8, 0.12, 0.1, 0, -0.42)], 18), "Base", 1)
    coat = lathe([(0.0, 0.62), (0.4, 0.55), (0.52, 0.3), (0.5, -0.05), (0.44, -0.35), (0.37, -0.55), (0.35, -0.58)], 22, "z", (0, -0.02, 0))
    P.obj("Coat", coat, lambda c, n: "Trim" if c.z < -0.5 else "Dark", 1)
    # the open front: the red chest feathers showing, the lace jabot, the lapels
    P.obj("Chest", ball((0, 0.33, 0.0), (0.3, 0.2, 0.5), 14, 7), lambda c, n: "Base" if (c.z * 6) % 1.0 > 0.25 else "Glass", 1)
    for k in range(4):
        P.obj("Jabot", ball((0, 0.55 - k * 0.01, 0.4 - k * 0.11), (0.17 - k * 0.025, 0.07, 0.07), 10, 5), "Belly", 1)
    for s in (1, -1):
        P.obj("Lapel", hull([(s * 0.12, 0.5, 0.5), (s * 0.34, 0.42, 0.45), (s * 0.3, 0.48, 0.05), (s * 0.18, 0.52, -0.35), (s * 0.12, 0.54, 0.0),
                             (s * 0.12, 0.44, 0.5), (s * 0.3, 0.38, 0.05)]), "Trim", 0, False)
        for k in range(4):
            P.obj("Button", ball((s * 0.3, 0.5 - k * 0.0, 0.3 - k * 0.2), (0.045, 0.03, 0.045), 8, 4), "Trim")
        # epaulettes: a gold pad with a fringe
        ep = Vector((s * 0.48, 0.05, 0.5))
        P.obj("Epaulette", ball(tuple(ep), (0.2, 0.2, 0.07), 12, 5), "Trim", 1)
        for k in range(9):
            a = math.pi * (k / 8.0) - math.pi / 2
            b = ep + Vector((s * (0.16 * math.cos(a) + 0.04), 0.18 * math.sin(a), -0.03))
            P.obj("Fringe", pipe([b, b + Vector((s * 0.03, 0, -0.16))], [0.022, 0.015], 4), "Trim")
    # belt, buckle, the rolled treasure map tucked in it
    P.obj("Belt", xf(torus(0.45, 0.045, 0.0, 24, 5), None, (0, -0.02, -0.35)), "Base")
    P.obj("Buckle", box((0, 0.46, -0.35), (0.2, 0.05, 0.16)), "Trim", 0, False)
    P.obj("BuckleIn", box((0, 0.485, -0.35), (0.1, 0.02, 0.07)), "Dark", 0, False)
    P.obj("Map", pipe([(-0.42, 0.4, -0.55), (-0.3, 0.45, -0.1)], [0.07, 0.07], 10), "Belly")
    P.obj("MapTie", xf(torus(0.075, 0.018, 0.0, 10, 4), Matrix.Rotation(math.radians(-15), 3, "Y"), (-0.36, 0.43, -0.33)), "Base")
    # the compass on a gold chain
    chain = [Vector((math.sin(a) * 0.34, 0.47 + math.cos(a) * 0.08, 0.45 - 0.55 * math.cos(a * 0.5) ** 2 * 0.0 - 0.45 * (1 - abs(a) / 1.2))) for a in [-1.2 + 2.4 * k / 16 for k in range(17)]]
    P.obj("Chain", pipe(chain, [0.016] * 17, 4, False), "Trim")
    P.obj("Compass", lathe([(0.0, 0.0), (0.13, 0.0), (0.13, 0.04), (0.0, 0.05)], 16, "y", (0, 0.56, 0.0)), "Trim")
    P.obj("CompassFace", ball((0, 0.6, 0.0), (0.1, 0.012, 0.1), 12, 4), "Belly")
    P.obj("Needle", hull([(0, 0.615, 0.08), (0.02, 0.615, 0.0), (-0.02, 0.615, 0.0), (0, 0.62, 0.0)]), "Base", 0, False)
    # the head
    HC = Vector((0, 0.5, 0.9))
    P.obj("Head", ball(tuple(HC), (0.4, 0.42, 0.4), 18, 9), "Base", 1)
    for k in range(9):   # the crest: red, gold and blue feathers fanning back
        a = math.radians(-60 + 120 * k / 8)
        b = HC + Vector((math.sin(a) * 0.15, -0.1, 0.3))
        tip = b + Vector((math.sin(a) * 0.35, -0.35 - 0.1 * math.cos(a), 0.35 + 0.1 * math.cos(a)))
        col = ("Base", "Glass", "Accent")[k % 3]
        P.obj("Crest", pipe(bez(b, b + Vector((0, -0.05, 0.15)), tip + Vector((0, 0.05, -0.1)), tip, 5), [0.07, 0.07, 0.06, 0.045, 0.025, 0.0], 6), col, 0)
    for s in (1, -1):
        P.obj("Face", ball((s * 0.22, 0.75, 0.92), (0.15, 0.13, 0.17), 10, 5), "Belly", 1)
        for k in range(3):   # the macaw's little face lines
            P.obj("FaceLine", ball((s * (0.2 + 0.04 * k), 0.84, 0.86 - k * 0.06), (0.05, 0.015, 0.012), 6, 3), "Base")
        P.obj("Brow", hull([(s * 0.06, 0.86, 1.1), (s * 0.4, 0.74, 1.14), (s * 0.4, 0.7, 1.07), (s * 0.08, 0.82, 1.03), (s * 0.22, 0.82, 1.15)]), "Dark", 0, False)
    P.obj("EyeWhite", ball((0.24, 0.84, 0.97), (0.11, 0.07, 0.12), 12, 6), "Belly")
    P.obj("Iris", ball((0.24, 0.89, 0.96), (0.075, 0.03, 0.08), 10, 5), "Glass")
    P.obj("Pupil", ball((0.24, 0.915, 0.96), (0.035, 0.02, 0.045), 8, 4), "Dark")
    P.obj("Glint", ball((0.27, 0.93, 1.0), (0.018, 0.01, 0.018), 6, 3), "Belly")
    P.obj("Patch", ball((-0.24, 0.85, 0.97), (0.13, 0.05, 0.12), 10, 5), "Dark")
    strap = [Vector((math.sin(a) * 0.41, 0.5 + math.cos(a) * 0.43, 0.97 + 0.12 * math.cos(a) * (1 if math.sin(a) < 0 else -1) * 0.0 + 0.1 * math.sin(a))) for a in [2 * math.pi * k / 30 for k in range(31)]]
    P.obj("Strap", pipe(strap, [0.022] * 31, 5, False), "Dark")
    P.obj("Earring", xf(torus(0.09, 0.02, 0.0, 14, 4), Matrix.Rotation(math.radians(90), 3, "Y"), (0.41, 0.42, 0.72)), "Trim")
    # the great hooked beak, open
    upper = bez((0, 0.85, 0.95), (0, 1.15, 0.97), (0, 1.3, 0.75), (0, 1.18, 0.5), 8)
    P.obj("Beak", pipe(upper, [0.2, 0.19, 0.175, 0.15, 0.12, 0.09, 0.06, 0.03, 0.0], 12), lambda c, n: "Dark" if c.z > 0.92 and c.y < 0.98 else "Belly", 1)
    P.obj("Jaw", pipe(bez((0, 0.82, 0.72), (0, 0.98, 0.6), (0, 1.06, 0.58), (0, 1.1, 0.6), 5), [0.15, 0.12, 0.09, 0.06, 0.035, 0.0], 10), "Dark", 1)
    P.obj("Mouth", ball((0, 0.92, 0.7), (0.1, 0.12, 0.06), 10, 5), "Base")
    P.obj("Tongue", ball((0, 0.98, 0.67), (0.06, 0.08, 0.035), 8, 4), "Dark")
    # the tricorn with its plume
    tricorn(P, (0, 0.45, 1.25), 0.34, 0.66, 0.3, 0.24)
    pl = bez((-0.35, 0.4, 1.45), (-0.55, 0.2, 1.75), (-0.75, -0.15, 1.85), (-0.95, -0.45, 1.75), 8)
    P.obj("Plume", pipe(pl, [0.04, 0.09, 0.12, 0.13, 0.12, 0.1, 0.07, 0.04, 0.0], 8), lambda c, n: "Accent" if c.y < 0.0 else "Glass", 1)
    # the wings: layered feathers, red coverts, a band of gold, long blue primaries
    for s in (1, -1):
        name = "FlapR" if s > 0 else "FlapL"
        hub = Vector((s * 0.48, -0.05, 0.35))
        keys = [(0.4, 0.4, -0.3, 0.16, 0.45), (0.9, 0.42, -0.5, 0.12, 0.6), (1.45, 0.32, -0.55, 0.08, 0.75), (1.9, 0.12, -0.45, 0.05, 0.85)]
        bm = sweep([(x, airfoil(le, te, th, z)) for (x, le, te, th, z) in fine(keys)], "x")
        if s < 0: bm = mirror_x(bm)
        P.part(name, bm, lambda c, n: "Base" if c.y > -0.1 else "Glass", tuple(hub), 0)
        for row, (y0, L, col, w) in enumerate(((-0.25, 0.4, "Glass", 0.09), (-0.4, 0.75, "Accent", 0.1))):
            n = 9 if row == 0 else 8
            for k in range(n):
                x = 0.5 + k * (1.45 / n)
                z = 0.45 + (x - 0.4) * 0.27
                L2 = L * (1.0 + 0.35 * (k / n)) if row == 1 else L
                P.part(name, hull([(s * (x - w), y0 + 0.1, z), (s * (x + w), y0 + 0.1, z), (s * x, y0 + 0.1, z + 0.04),
                                   (s * (x + 0.06 + 0.05 * k / n), y0 - L2, z - 0.02), (s * (x - 0.02 + 0.05 * k / n), y0 - L2 - 0.08, z - 0.02)]),
                       col if not (row == 1 and k >= n - 3) else "Accent", tuple(hub), 0, False)
        for k in range(5):   # the long fingered tip feathers
            x = 1.85 + k * 0.04; a = math.radians(-10 + k * 12)
            P.part(name, hull([(s * x, 0.15 - k * 0.12, 0.88), (s * x, 0.05 - k * 0.12, 0.88), (s * (x + 0.55 * math.cos(a)), 0.1 - k * 0.12 - 0.55 * math.sin(a), 0.92),
                               (s * x, 0.1 - k * 0.12, 0.92)]), "Accent", tuple(hub), 0, False)
    # the tail plumes
    for k, (dx, col) in enumerate(((-0.12, "Accent"), (0.0, "Base"), (0.12, "Accent"), (-0.26, "Base"), (0.26, "Base"), (-0.38, "Glass"), (0.38, "Glass"))):
        L = 1.7 - abs(dx) * 1.6
        P.obj("Plume", pipe(bez((dx * 0.4, -0.75, -0.42), (dx * 0.8, -1.2, -0.5), (dx * 1.3, -1.7, -0.45), (dx * 1.8, -0.75 - L, -0.35), 7),
                            [0.08, 0.1, 0.1, 0.09, 0.08, 0.06, 0.035, 0.0], 6), col, 0)
        for v in P.parts[-1].data.vertices: v.co.z = (v.co.z + 0.45) * 0.4 - 0.45
    # legs: the cutlass raised in the right talon, the flintlock aimed in the left
    for s in (1, -1):
        hip = Vector((s * 0.22, 0.1, -0.6)); ft = Vector((s * 0.42, 0.45, -0.75))
        P.obj("Leg", pipe([hip, hip + Vector((s * 0.08, 0.15, -0.12)), ft], [0.08, 0.065, 0.05], 8), "Metal")
        for k in (-1, 0, 1):
            P.obj("Talon", pipe(bez(ft, ft + Vector((k * 0.05, 0.1, 0.02)), ft + Vector((k * 0.07, 0.14, -0.06)), ft + Vector((k * 0.06, 0.1, -0.12)), 3), [0.035, 0.03, 0.02, 0.0], 5), "Dark")
    rc = Vector((0.42, 0.55, -0.78))   # the cutlass: a gold basket hilt, the curved blade swept up
    P.obj("Grip", pipe([rc + Vector((0, 0, -0.12)), rc + Vector((0, 0, 0.1))], [0.04, 0.04], 6), "Dark")
    P.obj("Guard", xf(torus(0.1, 0.025, 0.0, 14, 4), Matrix.Rotation(math.radians(90), 3, "Y"), tuple(rc + Vector((0.0, 0.04, 0.05)))), "Trim")
    P.obj("Pommel", ball(tuple(rc + Vector((0, 0, -0.15))), (0.045, 0.045, 0.045), 6, 3), "Trim")
    blade = bez(rc + Vector((0, 0, 0.12)), rc + Vector((0.25, 0.1, 0.55)), rc + Vector((0.6, 0.1, 0.95)), rc + Vector((0.95, -0.05, 1.15)), 8)
    for i in range(8):
        a, b = blade[i], blade[i + 1]; w = 0.1 * (1 - i / 9) + 0.025
        P.obj("Blade", hull([tuple(a + Vector((0, w, 0))), tuple(a - Vector((0, w * 0.4, 0))), tuple(b + Vector((0, w * 0.9, 0))), tuple(b - Vector((0, w * 0.35, 0))),
                             tuple(a + Vector((0.012, 0, 0))), tuple(b + Vector((0.012, 0, 0)))]), "Metal", 0, False)
    lc = Vector((-0.42, 0.55, -0.8))   # the flintlock: a wooden stock, a long steel barrel, gold fittings, aimed ahead
    P.obj("Stock", pipe([lc + Vector((0, -0.12, -0.12)), lc + Vector((0, 0.0, 0.0)), lc + Vector((0, 0.18, 0.04))], [0.055, 0.05, 0.05], 8), "Base")
    P.obj("Barrel", pipe([lc + Vector((0, 0.1, 0.06)), lc + Vector((0, 0.7, 0.06))], [0.04, 0.035], 10), "Metal")
    P.obj("BarrelRing", pipe([lc + Vector((0, 0.66, 0.06)), lc + Vector((0, 0.71, 0.06))], [0.048, 0.048], 10), "Trim")
    P.obj("Hammer", cone(lc + Vector((0, 0.08, 0.08)), lc + Vector((0, 0.02, 0.18)), 0.025, 4), "Trim", 0, False)
    P.obj("ButtCap", ball(tuple(lc + Vector((0, -0.14, -0.14))), (0.06, 0.06, 0.06), 8, 4), "Trim")
    # gold doubloons circling him
    for k in range(10):
        a = 2 * math.pi * k / 10
        c = Vector((math.sin(a) * 1.25, -0.05 + math.cos(a) * 1.1, 0.15 + 0.25 * math.sin(a * 2)))
        P.part("SpinCoins", coin(c, 0.09, 0.03, Matrix.Rotation(math.radians(90), 3, "X") @ Matrix.Rotation(a, 3, "Y")), "Trim", (0, -0.05, 0.15))
        P.part("SpinCoins", box(tuple(c + Vector((0, 0, 0))), (0.06, 0.04, 0.015), Matrix.Rotation(a, 3, "Z")), "Glow", (0, -0.05, 0.15), 0, False)
    mz = lc + Vector((0, 0.76, 0.06))
    P.part("Muzzle", ball(tuple(mz), (0.06, 0.04, 0.06), 8, 4), "Glow", tuple(mz))
    return P


# ================================================================= 2. the treasure mimic
def T_mimic():
    """The treasure mimic (2026-10-12, remade: "make it better"): a huge iron-bound, gold-cornered chest whose lid gapes wide on a fleshy
    maw lined with jagged fangs and two great tusks, five glowing eyes of different sizes staring out of the dark under the lid, a long
    forked tongue curling out toward the player, heaps of gold, gems and a crown inside, coins and jewels cascading from its lips, a broken
    padlock and loose chains swinging, four curling tentacle legs underneath, great bat wings, and coins and gems circling it."""
    P = Boss("mimic", {"Base": ((0.50, 0.28, 0.12), 0.35), "Belly": BONE, "Accent": ((0.55, 0.08, 0.14), 0.45), "Trim": GOLD,
                       "Glass": ((0.95, 0.30, 0.45), 0.7), "Dark": ((0.06, 0.02, 0.03), 0.4), "Glow": ((1.0, 0.92, 0.35), 0.5),
                       "Metal": ((0.24, 0.22, 0.26), 0.6), "Lamp": ((0.25, 0.95, 0.55), 0.8)})
    rng = random.Random(4)
    W, D, H = 1.0, 0.7, 0.55
    plank = lambda c, n: "Dark" if abs(n.z) < 0.5 and (c.z * 4.5) % 1.0 < 0.07 else "Base"
    P.obj("Chest", box((0, 0, -H * 0.5), (W * 2, D * 2, H * 2)), plank, 0, False)
    P.obj("Gums", box((0, 0.0, -0.03), (W * 1.9, D * 1.9, 0.08)), "Accent", 0, False)
    P.obj("Throat", box((0, -0.05, 0.0), (W * 1.5, D * 1.4, 0.04)), "Dark", 0, False)
    for x in (-0.62, 0.62):   # iron bands with rivets, gold corners with studs
        P.obj("Band", box((x, 0, -H * 0.5), (0.14, D * 2 + 0.04, H * 2 + 0.04)), "Metal", 0, False)
        for z in (-0.12, -0.5, -0.88):
            P.obj("Rivet", ball((x, D + 0.03, z), (0.035, 0.025, 0.035), 6, 3), "Trim")
    for sx in (-1, 1):
        for sy in (-1, 1):
            P.obj("Corner", box((sx * W, sy * D, -H * 0.5), (0.16, 0.16, H * 2 + 0.06)), "Trim", 0, False)
            for z in (-0.05, -H * 2 + 0.05):
                P.obj("Stud", ball((sx * (W + 0.08), sy * (D + 0.08), z), (0.05, 0.05, 0.05), 6, 3), "Trim")
    P.obj("Skirt", box((0, 0, -H * 2 - 0.02), (W * 2 + 0.06, D * 2 + 0.06, 0.06)), "Metal", 0, False)
    # the lower jaw: jagged fangs along the front and sides, two great tusks
    for k in range(11):
        x = -W * 0.88 + k * W * 1.76 / 10
        h = 0.2 + 0.08 * (k % 2)
        P.obj("Tooth", cone((x, D - 0.07, -0.03), (x + 0.02, D - 0.04, h), 0.075, 5), "Belly", 0, False)
    for s in (1, -1):
        for k in range(4):
            y = -D * 0.6 + k * 0.35
            P.obj("Tooth", cone((s * (W - 0.08), y, -0.03), (s * (W - 0.1), y, 0.17), 0.06, 5), "Belly", 0, False)
        P.obj("Tusk", pipe(bez((s * 0.78, D - 0.1, -0.05), (s * 0.8, D + 0.05, 0.25), (s * 0.7, D + 0.12, 0.45), (s * 0.58, D + 0.05, 0.55), 5), [0.1, 0.09, 0.07, 0.05, 0.025, 0.0], 8), "Belly")
    # the lid, wide open on its hinge at the back
    hub = Vector((0, -D, 0.02)); op = Matrix.Rotation(math.radians(72), 3, "X")
    def lid(bm):
        for v in bm.verts: v.co = op @ (v.co - hub) + hub
        return bm
    arc = []
    for k in range(11):
        a = math.pi * k / 10
        for x in (-W, W): arc.append((x, math.cos(a) * D, math.sin(a) * 0.5 + 0.02))
    P.part("SwayLid", lid(hull(arc)), lambda c, n: "Accent" if (n.z < -0.3 or n.y > 0.45) and abs(c.x) < W * 0.95 else plank(c, n), tuple(hub), 0, False)
    for x in (-0.62, 0.62):
        band = [(x + dx, math.cos(math.pi * k / 10) * (D + 0.025), math.sin(math.pi * k / 10) * 0.525 + 0.02) for k in range(11) for dx in (-0.07, 0.07)]
        P.part("SwayLid", lid(hull(band)), "Metal", tuple(hub), 0, False)
    for sx in (-1, 1):
        cap = [(sx * (W + dx), math.cos(math.pi * k / 10) * (D + 0.03), math.sin(math.pi * k / 10) * 0.53 + 0.02) for k in range(11) for dx in (-0.08, 0.02)]
        P.part("SwayLid", lid(hull(cap)), "Trim", tuple(hub), 0, False)
    P.part("SwayLid", lid(ball((0, 0.05, 0.03), (W * 0.85, D * 0.85, 0.05), 14, 4)), "Dark", tuple(hub), 0)   # the dark of the lid
    for k in range(11):   # the upper fangs, hanging from the lid's front edge
        x = -W * 0.88 + k * W * 1.76 / 10
        P.part("SwayLid", lid(cone((x, D - 0.06, 0.03), (x - 0.02, D - 0.1, -0.24 + 0.08 * (k % 2)), 0.075, 5)), "Belly", tuple(hub), 0, False)
    # five eyes staring out of the dark under the lid
    for (x, y, r) in ((0.0, 0.05, 0.2), (-0.52, 0.22, 0.13), (0.52, 0.22, 0.13), (-0.4, -0.3, 0.1), (0.42, -0.32, 0.09)):
        P.part("SwayLid", lid(ball((x, y, -0.02), (r * 1.25, r * 1.1, r * 0.55), 12, 6)), "Glow", tuple(hub), 0)
        P.part("SwayLid", lid(ball((x, y, -0.02 - r * 0.5), (r * 0.18, r * 0.8, r * 0.1), 8, 4)), "Dark", tuple(hub), 0)
    # the broken padlock hanging from the lid
    lk = Vector((0, D + 0.08, 0.25))
    P.part("SwayLid", lid(box(tuple(lk), (0.3, 0.08, 0.28))), "Trim", tuple(hub), 0, False)
    P.part("SwayLid", lid(box(tuple(lk + Vector((0, 0.045, -0.02))), (0.05, 0.02, 0.1))), "Dark", tuple(hub), 0, False)
    shackle = [lk + Vector((0.09 * math.cos(a), 0, 0.14 + 0.12 * math.sin(a))) for a in [math.pi * k / 8 for k in range(7)]]
    P.part("SwayLid", lid(pipe(shackle, [0.025] * 7, 6)), "Metal", tuple(hub), 0)
    # loose chains swinging from the front corners
    for s in (1, -1):
        top = Vector((s * (W + 0.05), D + 0.05, -0.1))
        name = "SwayChain%d" % (0 if s > 0 else 1)
        for k in range(7):
            c = top + Vector((s * 0.03 * k, 0.04 * k, -0.11 * k))
            link = torus(0.055, 0.016, 0.0, 10, 4)
            xf(link, Matrix.Rotation(math.radians(90), 3, "X") @ Matrix.Rotation(math.radians(90 * (k % 2)), 3, "Y"), tuple(c))
            P.part(name, link, "Metal", tuple(top))
        P.part(name, ball(tuple(top + Vector((s * 0.21, 0.28, -0.85))), (0.09, 0.09, 0.09), 8, 4), "Metal", tuple(top))
    # the forked tongue curling out toward the player
    tg = bez((0, -0.1, 0.05), (0, 0.9, 0.35), (0, 1.5, 0.05), (0.15, 1.6, -0.55), 10)
    P.obj("Tongue", pipe(tg, [0.22, 0.24, 0.24, 0.22, 0.2, 0.18, 0.16, 0.14, 0.12, 0.1, 0.08], 12), lambda c, n: "Accent" if n.z < -0.4 else "Glass", 1)
    for v in P.parts[-1].data.vertices: v.co.x *= 1.0; v.co.z = v.co.z
    for s in (1, -1):
        P.obj("Fork", cone(tuple(tg[-1]), tuple(tg[-1] + Vector((s * 0.12, 0.08, -0.22))), 0.06, 6), "Glass", 0)
    # gold inside: heaps, gems, a crown
    gold_heap(P, (0.45, -0.15, 0.0), 0.45, 0.4, 0.22, 14, rng)
    gold_heap(P, (-0.45, -0.2, 0.0), 0.42, 0.38, 0.2, 12, rng)
    cr = Vector((-0.45, -0.2, 0.25))
    P.obj("Crown", lathe([(0.15, 0.0), (0.16, 0.12), (0.14, 0.12), (0.13, 0.02)], 14, "z", tuple(cr)), "Trim")
    for k in range(6):
        a = 2 * math.pi * k / 6
        P.obj("CrownPoint", cone(tuple(cr + Vector((math.sin(a) * 0.15, math.cos(a) * 0.15, 0.1))), tuple(cr + Vector((math.sin(a) * 0.16, math.cos(a) * 0.16, 0.24))), 0.035, 4), "Trim", 0, False)
    P.obj("CrownGem", ball(tuple(cr + Vector((0, 0.16, 0.06))), (0.04, 0.02, 0.04), 6, 3), "Lamp")
    for k in range(16):   # coins and gems cascading from its lips
        s = 1 if k % 2 else -1
        p = Vector((s * rng.uniform(0.35, 0.9), D + 0.12 + rng.uniform(0, 0.25), -0.05 - k * 0.06))
        if k % 4 == 3: P.obj("Jewel", hull([tuple(p + Vector(v) * 0.07) for v in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1.4), (0, 0, -0.6))]), "Lamp", 0, False)
        else: P.obj("Coin", coin(p, 0.08, 0.025, rrot(rng)), "Trim", 0, False)
    # four tentacle legs curling under it
    for k in range(4):
        sx = 1 if k % 2 else -1; sy = 1 if k < 2 else -1
        p0 = Vector((sx * 0.6, sy * 0.4, -H * 2 - 0.05))
        out = Vector((sx * 0.6, sy * 0.4, 0)).normalized()
        pts = bez(p0, p0 + out * 0.3 + Vector((0, 0, -0.3)), p0 + out * 0.65 + Vector((0, 0.1, -0.55)), p0 + out * 0.5 + Vector((0, 0.25, -0.35)), 8)
        rr = [0.13 - 0.12 * i / 8 for i in range(9)]
        P.part("Sway%d" % k, pipe(pts, rr, 10), "Accent", tuple(p0), 1)
        for i in range(2, 8, 2):
            P.part("Sway%d" % k, ball(tuple(pts[i] + Vector((0, 0, -rr[i] * 0.8))), (0.035, 0.035, 0.035), 6, 3), "Glass", tuple(p0))
    # great bat wings
    for s in (1, -1):
        name = "FlapR" if s > 0 else "FlapL"
        hub = Vector((s * W, -0.1, -0.15))
        wr = hub + Vector((s * 0.5, 0.15, 0.55))
        tips = [hub + Vector((s * 0.95, 0.35, 1.0)), hub + Vector((s * 1.55, 0.2, 0.75)), hub + Vector((s * 1.8, -0.1, 0.25)), hub + Vector((s * 1.5, -0.4, -0.2)), hub + Vector((s * 0.7, -0.45, -0.3))]
        P.part(name, pipe([hub, wr], [0.08, 0.06], 8), "Dark", tuple(hub))
        polys = [[hub, wr, tips[0]]]
        for a, b in zip(tips, tips[1:]):
            m = (a + b) * 0.5; m = m + (wr - m) * 0.25
            polys += [[wr, a, m], [wr, m, b]]
        polys.append([wr, tips[-1], hub])
        P.part(name, sheet([[tuple(p) for p in poly] for poly in polys], 0.03), "Accent", tuple(hub), 0, False)
        for t in tips:
            P.part(name, pipe([wr, t], [0.045, 0.015], 6), "Dark", tuple(hub))
            P.part(name, cone(t, t + (t - wr).normalized() * 0.15, 0.025, 4), "Belly", tuple(hub), 0, False)
        P.part(name, cone(wr, wr + Vector((s * 0.05, 0.2, 0.2)), 0.04, 5), "Belly", tuple(hub), 0, False)
    # coins and gems circling it
    for k in range(12):
        a = 2 * math.pi * k / 12
        c = Vector((math.sin(a) * 1.9, math.cos(a) * 1.6, -0.3 + 0.3 * math.sin(a * 2)))
        if k % 3 == 2: P.part("SpinTreasure", hull([tuple(c + Vector(v) * 0.09) for v in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1.5), (0, 0, -0.7))]), "Lamp", (0, 0, -0.3), 0, False)
        else: P.part("SpinTreasure", coin(c, 0.1, 0.03, Matrix.Rotation(math.radians(90), 3, "X") @ Matrix.Rotation(a, 3, "Y")), "Trim", (0, 0, -0.3))
    P.part("Muzzle", ball((0, 0.55, 0.2), (0.08, 0.05, 0.06), 8, 4), "Glow", (0, 0.55, 0.2))
    return P


# ================================================================= 3. the ghost captain
def T_ghost():
    """The drowned captain risen: a glowing green ghost in a ragged navy coat with gold buttons and epaulettes, a tricorn, a great spectral
    beard, burning eyes, a cutlass raised in one hand and a lantern swinging in the other, a wisp of a tail for legs, and ghost-lights circling."""
    P = Boss("ghost", {"Base": ((0.45, 0.95, 0.80), 0.5), "Belly": ((0.80, 1.0, 0.92), 0.4), "Accent": ((0.08, 0.36, 0.40), 0.45), "Trim": GOLD,
                       "Glass": ((0.30, 1.0, 0.65), 0.6), "Dark": BLACK, "Glow": ((0.35, 1.0, 0.55), 0.5),
                       "Metal": ((0.78, 0.82, 0.88), 0.9), "Lamp": ((0.55, 1.0, 0.65), 0.8)})
    # the wisp tail curling back and down
    tail = bez((0, 0.0, 0.2), (0, -0.1, -0.5), (0, -0.7, -0.9), (0, -1.5, -0.6), 10)
    P.obj("Tail", pipe(tail, [0.55, 0.55, 0.5, 0.42, 0.34, 0.26, 0.19, 0.13, 0.08, 0.04, 0.0], 16), lambda c, n: "Belly" if speckle(c, 2) < 0.1 else "Base", 1)
    # the coat: a flared skirt and a body, ragged hem
    hem = []
    P.obj("Coat", lathe([(0.0, 1.05), (0.42, 1.02), (0.5, 0.75), (0.52, 0.35), (0.62, 0.0), (0.7, -0.25)], 20, "z"), lambda c, n: "Trim" if abs(c.x) < 0.07 and c.y > 0.3 else "Accent", 0)
    for v in P.parts[-1].data.vertices: v.co.y *= 0.8
    for k in range(10):   # ragged tatters at the hem
        a = 2 * math.pi * k / 10 + 0.3
        P.obj("Tatter", cone((math.sin(a) * 0.62, math.cos(a) * 0.5, -0.2), (math.sin(a) * 0.72, math.cos(a) * 0.58, -0.55 - 0.1 * (k % 3)), 0.13, 4), "Accent", 0, False)
    for k in range(4): P.obj("Button", ball((0.12, 0.43 - 0.01 * k, 0.85 - k * 0.22), (0.045, 0.03, 0.045), 6, 3), "Trim")
    for k in range(4): P.obj("Button", ball((-0.12, 0.43 - 0.01 * k, 0.85 - k * 0.22), (0.045, 0.03, 0.045), 6, 3), "Trim")
    P.obj("Sash", torus(0.5, 0.06, 0.25, 20, 5), "Glass")
    for v in P.parts[-1].data.vertices: v.co.y *= 0.82
    P.obj("Buckle", box((0, 0.43, 0.25), (0.16, 0.04, 0.13)), "Trim", 0, False)
    for s in (1, -1):
        P.obj("Epaulette", ball((s * 0.45, 0.0, 1.02), (0.2, 0.18, 0.06), 10, 5), "Trim")
        for k in range(5): P.obj("Fringe", pipe([(s * (0.32 + k * 0.06), 0.1, 0.98), (s * (0.34 + k * 0.06), 0.12, 0.84)], [0.018, 0.012], 4), "Trim")
    # the head, beard and eyes
    P.obj("Head", ball((0, 0.05, 1.38), (0.34, 0.32, 0.36), 16, 8), "Base", 1)
    P.obj("Beard", pipe(bez((0, 0.22, 1.25), (0, 0.38, 1.05), (0, 0.4, 0.85), (0, 0.32, 0.6), 7), [0.28, 0.3, 0.28, 0.24, 0.19, 0.13, 0.07, 0.0], 12), "Belly", 1)
    for s in (1, -1):
        P.obj("Moustache", pipe(bez((0, 0.35, 1.3), (s * 0.15, 0.4, 1.32), (s * 0.3, 0.36, 1.28), (s * 0.38, 0.3, 1.38), 6), [0.06, 0.07, 0.06, 0.05, 0.035, 0.02, 0.0], 6), "Belly")
        P.obj("Socket", ball((s * 0.13, 0.3, 1.47), (0.09, 0.05, 0.08), 10, 5), "Dark")
        P.obj("EyeFire", ball((s * 0.13, 0.34, 1.47), (0.05, 0.03, 0.05), 8, 4), "Glow")
    tricorn(P, (0, 0.03, 1.6), 0.3, 0.58, 0.26, 0.22)
    # the right arm raised with the cutlass, the left holding the lantern out
    sh = Vector((0.45, 0.05, 0.95)); el = Vector((0.75, 0.2, 1.2)); hd = Vector((0.82, 0.35, 1.55))
    P.obj("Sleeve", pipe([sh, el, hd], [0.15, 0.12, 0.11], 10), "Accent", 1)
    P.obj("Cuff", pipe([hd + (el - hd).normalized() * 0.06, hd - (el - hd).normalized() * 0.02], [0.14, 0.14], 10), "Trim")
    P.obj("Hand", ball(tuple(hd + Vector((0, 0.02, 0.06))), (0.1, 0.1, 0.1), 10, 5), "Base")
    P.obj("Guard", pipe(bez(hd + Vector((-0.08, 0.06, 0.0)), hd + Vector((-0.12, 0.18, 0.08)), hd + Vector((-0.06, 0.2, 0.2)), hd + Vector((0.0, 0.1, 0.2)), 6), [0.025] * 7, 5), "Trim")
    blade = [hd + Vector((0, 0.04, 0.12)), hd + Vector((0.05, 0.08, 0.6)), hd + Vector((0.18, 0.08, 1.0)), hd + Vector((0.38, 0.06, 1.25))]
    pts = []
    for i, b in enumerate(blade):
        w = [0.07, 0.085, 0.08, 0.0][i]
        pts += [tuple(b + Vector((w, 0, 0))), tuple(b + Vector((-w * 0.4, 0, 0))), tuple(b + Vector((0, 0.02, 0))), tuple(b + Vector((0, -0.02, 0)))]
    for a, b in zip(range(0, 12, 4), range(4, 16, 4)):
        P.obj("Blade", hull(pts[a:a + 4] + pts[b:b + 4]), "Metal", 0, False)
    sh = Vector((-0.45, 0.05, 0.95)); el = Vector((-0.8, 0.3, 0.85)); hd = Vector((-1.0, 0.55, 0.8))
    P.obj("Sleeve", pipe([sh, el, hd], [0.15, 0.12, 0.11], 10), "Accent", 1)
    P.obj("Cuff", pipe([hd + (el - hd).normalized() * 0.06, hd - (el - hd).normalized() * 0.02], [0.14, 0.14], 10), "Trim")
    P.obj("Hand", ball(tuple(hd), (0.1, 0.1, 0.1), 10, 5), "Base")
    lc = hd + Vector((0, 0.05, -0.4))
    P.obj("Bail", pipe([hd, lc + Vector((0, 0, 0.24))], [0.015, 0.015], 4), "Dark")
    P.obj("LanternCap", lathe([(0.0, 0.3), (0.1, 0.22), (0.14, 0.16), (0.0, 0.16)], 8, "z", lc), "Dark")
    P.obj("LanternGlass", lathe([(0.0, 0.16), (0.12, 0.15), (0.13, -0.05), (0.0, -0.08)], 8, "z", lc), "Lamp", 0)
    P.obj("LanternBase", lathe([(0.0, -0.06), (0.14, -0.06), (0.14, -0.12), (0.0, -0.12)], 8, "z", lc), "Dark")
    for k in range(4):
        a = math.pi * 0.5 * k + math.pi / 4
        P.obj("LanternBar", pipe([lc + Vector((math.cos(a) * 0.13, math.sin(a) * 0.13, -0.06)), lc + Vector((math.cos(a) * 0.13, math.sin(a) * 0.13, 0.16))], [0.015, 0.015], 4), "Dark")
    # ghost-lights circling
    for k in range(7):
        a = 2 * math.pi * k / 7
        c = Vector((math.cos(a) * 1.35, math.sin(a) * 1.1, 0.5 + 0.35 * math.sin(a * 2)))
        P.part("SpinWisps", ball(tuple(c), (0.13, 0.13, 0.15), 10, 5), "Glass", (0, 0, 0.5))
        P.part("SpinWisps", cone(c + Vector((0, 0, 0.08)), c + Vector((0, 0, 0.42)), 0.1, 8), "Glass", (0, 0, 0.5))
        P.part("SpinWisps", ball(tuple(c + Vector((0, 0.06, 0))), (0.05, 0.05, 0.06), 6, 3), "Glow", (0, 0, 0.5))
    P.part("Muzzle", ball((0, 0.4, 1.47), (0.05, 0.03, 0.04), 8, 4), "Glow", (0, 0.4, 1.47))
    return P


# ================================================================= 4. the cannon crab
def T_crab():
    """A giant coral-red crab that flies a pirate flag: a broad knobbly shell crusted with barnacles, eyes on stalks, two huge claws each
    gripping a black-and-gold cannon, six legs that swing, and a jolly roger on a mast on its back."""
    P = Boss("crab", {"Base": ((0.92, 0.30, 0.12), 0.55), "Belly": ((1.0, 0.86, 0.66), 0.4), "Accent": ((0.75, 0.15, 0.08), 0.55), "Trim": GOLD,
                      "Glass": ((0.98, 0.97, 0.94), 0.6), "Dark": BLACK, "Glow": ((1.0, 0.65, 0.25), 0.5),
                      "Metal": ((0.16, 0.16, 0.18), 0.7), "Lamp": ((1.0, 0.75, 0.35), 0.8)})
    rng = random.Random(7)
    def shell(c, n):
        if n.z < -0.3: return "Belly"
        return "Accent" if math.sin(c.x * 7) * math.sin(c.y * 8 + 1) > 0.72 else "Base"
    P.obj("Shell", ball((0, 0, 0), (1.05, 0.78, 0.42), 22, 10), shell, 1)
    for v in P.parts[-1].data.vertices:   # a crab's shell: wider at the front, a point on each side
        a = math.atan2(v.co.x, v.co.y)
        v.co.x *= 1 + 0.12 * math.cos(2 * a) * (1 if v.co.y > 0 else 0.4)
        if v.co.z < 0: v.co.z *= 0.6
    for s in (1, -1):
        P.obj("Spike", cone((s * 1.05, 0.15, 0.05), (s * 1.35, 0.25, 0.12), 0.1, 6), "Accent", 0, False)
    for k in range(6):   # barnacles
        a = rng.uniform(-2.6, 2.6); r = rng.uniform(0.2, 0.8)
        p = Vector((math.sin(a) * r * 0.95, math.cos(a) * r * 0.7, 0.42 * math.sqrt(max(0.0, 1 - r * r)) + 0.0))
        P.obj("Barnacle", lathe([(0.1, 0.0), (0.07, 0.1), (0.035, 0.1), (0.0, 0.06)], 8, "z", tuple(p)), "Belly")
    # the eyes on stalks and a mouth
    for s in (1, -1):
        P.obj("Stalk", pipe(bez((s * 0.22, 0.6, 0.2), (s * 0.25, 0.7, 0.45), (s * 0.28, 0.72, 0.6), (s * 0.3, 0.72, 0.7), 4), [0.06, 0.055, 0.05, 0.05, 0.05], 8), "Base")
        P.obj("Eye", ball((s * 0.3, 0.74, 0.78), (0.13, 0.12, 0.14), 12, 6), "Glass")
        P.obj("Pupil", ball((s * 0.31, 0.85, 0.8), (0.06, 0.04, 0.07), 8, 4), "Dark")
        P.obj("Brow", box((s * 0.3, 0.8, 0.94), (0.2, 0.06, 0.05), Matrix.Rotation(math.radians(-s * 20), 3, "Y")), "Accent", 0, False)
    P.obj("Mouth", box((0, 0.78, -0.02), (0.36, 0.06, 0.1)), "Dark", 0, False)
    for k in range(4): P.obj("Fang", cone((-0.12 + k * 0.08, 0.81, 0.02), (-0.12 + k * 0.08, 0.82, -0.06), 0.022, 4), "Glass", 0, False)
    # the claws holding cannons
    for s in (1, -1):
        sh = Vector((s * 0.8, 0.45, 0.0)); el = Vector((s * 1.35, 0.8, 0.1)); wr = Vector((s * 1.3, 1.25, 0.2))
        P.obj("Arm", pipe([sh, el, wr], [0.15, 0.13, 0.15], 10), shell, 1)
        P.obj("Joint", ball(tuple(el), (0.17, 0.17, 0.17), 10, 5), "Accent")
        P.obj("Claw", ball(tuple(wr + Vector((0, 0.25, 0))), (0.33, 0.42, 0.3), 14, 7), shell, 1)
        cb = wr + Vector((0, 0.35, 0.0))
        P.obj("Cannon", lathe([(0.0, -0.1), (0.2, -0.1), (0.18, 0.2), (0.14, 0.6), (0.16, 0.62), (0.16, 0.7), (0.11, 0.7), (0.11, 0.55)], 14, "y", tuple(cb)), "Metal", 0)
        for y in (0.15, 0.4): P.obj("CannonRing", lathe([(0.19, y - 0.03), (0.19, y + 0.03)], 14, "y", tuple(cb)), "Trim")
        P.obj("Bore", lathe([(0.1, 0.69), (0.0, 0.6)], 12, "y", tuple(cb)), "Dark")
        for d in (1, -1):   # the pincers closing round the barrel
            P.obj("Pincer", pipe(bez(wr + Vector((s * 0.12 * d, 0.35, 0.18 * d)), wr + Vector((s * 0.15 * d, 0.6, 0.28 * d)), wr + Vector((s * 0.05 * d, 0.85, 0.24 * d)), wr + Vector((0, 0.9, 0.12 * d)), 5),
                                 [0.13, 0.12, 0.1, 0.07, 0.04, 0.0], 8), shell, 1)
    # six legs that swing
    for s in (1, -1):
        for k in range(3):
            hip = Vector((s * 0.85, 0.1 - k * 0.35, -0.05)); knee = hip + Vector((s * 0.5, -0.05, 0.28)); foot = knee + Vector((s * 0.45, -0.1, -0.8))
            name = "SwayLeg%d%d" % (k, 1 if s > 0 else 0)
            P.part(name, pipe([hip, knee, foot], [0.08, 0.07, 0.0], 8), shell, tuple(hip), 0)
            P.part(name, ball(tuple(knee), (0.085, 0.085, 0.085), 8, 4), "Accent", tuple(hip), 0)
    # the mast and the jolly roger
    P.obj("Mast", pipe([(0, -0.4, 0.3), (0, -0.45, 1.6)], [0.04, 0.03], 8), "Metal")
    P.obj("MastTop", ball((0, -0.45, 1.62), (0.06, 0.06, 0.06), 8, 4), "Trim")
    W = 0.75; Hh = 0.48
    def flag(u, v): return Vector((u * W, -0.45 + 0.05 * math.sin(u * 6), 1.55 - v * Hh + 0.06 * math.sin(u * 4)))
    polys = []
    nu, nv = 16, 10
    for i in range(nu):
        for j in range(nv):
            polys.append([tuple(flag(i / nu, j / nv)), tuple(flag((i + 1) / nu, j / nv)), tuple(flag((i + 1) / nu, (j + 1) / nv)), tuple(flag(i / nu, (j + 1) / nv))])
    def flagpaint(c, n):
        u = c.x / W; v = (1.55 - c.z) / Hh
        d = (u - 0.5) ** 2 + ((v - 0.42) * 1.2) ** 2
        if d < 0.03: return "Glass"
        if abs((u - 0.5) - (v - 0.5) * 1.3) < 0.05 and d < 0.12 or abs((u - 0.5) + (v - 0.5) * 1.3) < 0.05 and d < 0.12: return "Glass"
        return "Dark"
    bm = bmesh.new()
    for poly in polys:   # a flag hung on a vertical mast: two-sided along x
        a = [bm.verts.new(Vector(p) + Vector((0, 0.012, 0))) for p in poly]; b = [bm.verts.new(Vector(p) - Vector((0, 0.012, 0))) for p in poly]
        bm.faces.new(a); bm.faces.new(list(reversed(b)))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    P.part("Cloth", bm, flagpaint, (0, 0, 0), 0, False)
    P.part("Muzzle", ball((1.3, 2.3, 0.2), (0.08, 0.05, 0.08), 8, 4), "Glow", (1.3, 2.3, 0.2))
    return P


# ================================================================= 5. skull rock
def T_skull():
    """The last boss: skull rock, the pirates' hoard island torn from the sea - a floating crag carved into a giant skull with gold fire in its
    eyes, a sandy top with a leaning palm, an open treasure chest overflowing with gold, a jolly roger flying, a waterfall spilling from its
    side, and a ring of gold doubloons turning round it."""
    P = Boss("skull", {"Base": ((0.95, 0.80, 0.52), 0.25), "Belly": ((0.93, 0.88, 0.74), 0.3), "Accent": ((0.20, 0.62, 0.20), 0.45), "Trim": GOLD,
                       "Glass": ((0.25, 0.65, 0.95), 0.9), "Dark": BLACK, "Glow": ((1.0, 0.75, 0.25), 0.5),
                       "Metal": ((0.40, 0.27, 0.17), 0.3), "Lamp": ((1.0, 0.82, 0.35), 0.8)})
    rng = random.Random(11)
    # the crag under it
    rock = []
    for k in range(40):
        a = rng.uniform(0, 2 * math.pi); r = rng.uniform(0.2, 1.7)
        rock.append((math.sin(a) * r, math.cos(a) * r * 0.9 - 0.2, -0.2 - (1.7 - r) * rng.uniform(0.6, 0.95)))
    rock += [(math.sin(2 * math.pi * k / 18) * 1.7, math.cos(2 * math.pi * k / 18) * 1.55 - 0.2, 0.0) for k in range(18)] + [(0, -0.2, -1.6)]
    P.obj("Crag", hull(rock), lambda c, n: "Metal" if speckle(c, 3) > 0.12 else "Dark", 0, False)
    P.obj("Sand", lathe([(0.0, 0.08), (1.55, 0.06), (1.72, 0.0), (1.7, -0.05)], 28, "z", (0, -0.2, 0)), lambda c, n: "Base" if n.z > 0.6 else "Metal")
    for v in P.parts[-1].data.vertices: v.co.y = (v.co.y + 0.2) * 0.9 - 0.2
    # the skull at the front, carved in the cliff
    sc = Vector((0, 0.55, 0.8))
    P.obj("Cranium", ball(tuple(sc), (0.92, 0.8, 0.85), 22, 11), lambda c, n: "Metal" if n.z < -0.6 else "Belly", 1)
    P.obj("Cheeks", ball(tuple(sc + Vector((0, 0.18, -0.45))), (0.75, 0.62, 0.42), 18, 8), "Belly", 1)
    P.obj("Jaw", box(tuple(sc + Vector((0, 0.45, -0.78))), (0.9, 0.4, 0.25)), "Belly", 0, False)
    for s in (1, -1):
        P.obj("Socket", ball(tuple(sc + Vector((s * 0.33, 0.66, 0.0))), (0.27, 0.18, 0.25), 14, 7), "Dark")
        P.obj("EyeFire", ball(tuple(sc + Vector((s * 0.33, 0.78, 0.0))), (0.12, 0.06, 0.14), 10, 5), "Glow")
        P.obj("Crack", pipe([sc + Vector((s * 0.15, 0.62, 0.55)), sc + Vector((s * 0.25, 0.68, 0.35)), sc + Vector((s * 0.18, 0.74, 0.22))], [0.03, 0.025, 0.0], 5), "Dark")
    P.obj("Nose", hull([tuple(sc + Vector(v)) for v in ((0, 0.86, -0.18), (0.11, 0.8, -0.35), (-0.11, 0.8, -0.35), (0, 0.72, -0.3), (0.08, 0.7, -0.2), (-0.08, 0.7, -0.2))]), "Dark", 0, False)
    P.obj("Grin", box(tuple(sc + Vector((0, 0.66, -0.62))), (0.7, 0.04, 0.2)), "Dark", 0, False)
    for k in range(7):
        x = -0.3 + k * 0.1
        P.obj("Tooth", box(tuple(sc + Vector((x, 0.68, -0.56))), (0.08, 0.06, 0.12)), "Belly", 0, False)
        P.obj("Tooth", box(tuple(sc + Vector((x, 0.68, -0.69))), (0.08, 0.06, 0.1)), "Belly", 0, False)
    # the palm leaning over the back
    base = Vector((-1.0, -0.75, 0.05))
    trunk = bez(base, base + Vector((0.0, 0.0, 0.7)), base + Vector((-0.15, -0.05, 1.3)), base + Vector((-0.45, -0.1, 1.75)), 10)
    P.obj("Trunk", pipe(trunk, [0.14 - 0.006 * i for i in range(11)], 8), lambda c, n: "Metal" if (c.z * 7) % 1.0 > 0.25 else "Dark")
    top = trunk[-1]
    for k in range(7):
        a = 2 * math.pi * k / 7 + 0.3
        d = Vector((math.cos(a), math.sin(a), 0))
        spine = [top + d * (0.19 * i) + Vector((0, 0, 0.13 * i - 0.032 * i * i)) for i in range(7)]
        polys = []
        for i in range(6):
            w0 = 0.17 * math.sin(math.pi * (i + 0.2) / 6.4); w1 = 0.17 * math.sin(math.pi * (i + 1.2) / 6.4)
            side = Vector((-d.y, d.x, 0))
            polys.append([tuple(spine[i] + side * w0), tuple(spine[i + 1] + side * w1), tuple(spine[i + 1] - side * w1), tuple(spine[i] - side * w0)])
        P.part("Cloth", sheet(polys, 0.025), "Accent", (0, 0, 0), 0, False)
    for k in range(3): P.obj("Coconut", ball(tuple(top + Vector((0.08 * math.cos(k * 2.1), 0.08 * math.sin(k * 2.1), -0.08))), (0.08, 0.08, 0.08), 8, 4), "Metal")
    # the open treasure chest on the back, and gold spilling
    cc = Vector((1.05, 0.45, 0.05))
    P.obj("ChestBox", box(tuple(cc + Vector((0, 0, 0.18))), (0.62, 0.42, 0.36)), lambda c, n: "Dark" if (c.z * 6) % 1.0 < 0.1 and abs(n.z) < 0.5 else "Metal", 0, False)
    for x in (-0.22, 0.22): P.obj("ChestBand", box(tuple(cc + Vector((x, 0, 0.18))), (0.06, 0.44, 0.38)), "Trim", 0, False)
    arc = []
    for k in range(7):
        a = math.pi * k / 6
        for x in (-0.31, 0.31): arc.append((x, math.cos(a) * 0.21, math.sin(a) * 0.18))
    lid = hull(arc); m = Matrix.Rotation(math.radians(-70), 3, "X")
    for v in lid.verts: v.co = m @ (v.co - Vector((0, -0.21, 0))) + Vector((0, -0.21, 0)) + cc + Vector((0, 0, 0.36))
    P.obj("ChestLid", lid, "Metal", 0, False)
    gold_heap(P, cc + Vector((0, 0, 0.36)), 0.28, 0.18, 0.13, 10, rng, "Hoard")
    gold_heap(P, cc + Vector((-0.05, 0.38, 0.03)), 0.32, 0.22, 0.09, 8, rng, "Spill")
    # the jolly roger
    P.obj("Pole", pipe([(0.35, -1.25, 0.05), (0.35, -1.3, 1.9)], [0.035, 0.025], 6), "Metal")
    W, Hh = 0.8, 0.5
    def flag(u, v): return Vector((0.35 + u * W, -1.3 + 0.05 * math.sin(u * 5), 1.85 - v * Hh + 0.05 * math.sin(u * 4)))
    bm = bmesh.new()
    for i in range(16):
        for j in range(10):
            q = [flag(i / 16, j / 10), flag((i + 1) / 16, j / 10), flag((i + 1) / 16, (j + 1) / 10), flag(i / 16, (j + 1) / 10)]
            a = [bm.verts.new(p + Vector((0, 0.012, 0))) for p in q]; b = [bm.verts.new(p - Vector((0, 0.012, 0))) for p in q]
            bm.faces.new(a); bm.faces.new(list(reversed(b)))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    def flagpaint(c, n):
        u = (c.x - 0.35) / W; v = (1.85 - c.z) / Hh
        d = (u - 0.5) ** 2 + ((v - 0.42) * 1.2) ** 2
        if d < 0.03: return "Belly"
        if (abs((u - 0.5) - (v - 0.5) * 1.3) < 0.05 or abs((u - 0.5) + (v - 0.5) * 1.3) < 0.05) and d < 0.12: return "Belly"
        return "Dark"
    P.part("Cloth", bm, flagpaint, (0, 0, 0), 0, False)
    # a waterfall pouring from the side of the crag
    def fall(u, v): return Vector((-1.62 - 0.25 * v * v, -0.1 + (u - 0.5) * 0.5, 0.02 - v * 1.4))
    bm = bmesh.new()
    for i in range(3):
        for j in range(6):
            q = [fall(i / 3, j / 6), fall((i + 1) / 3, j / 6), fall((i + 1) / 3, (j + 1) / 6), fall(i / 3, (j + 1) / 6)]
            a = [bm.verts.new(p + Vector((0.015, 0, 0))) for p in q]; b = [bm.verts.new(p - Vector((0.015, 0, 0))) for p in q]
            bm.faces.new(a); bm.faces.new(list(reversed(b)))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    P.part("Cloth", bm, lambda c, n: "Belly" if speckle(c, 4) < 0.15 else "Glass", (0, 0, 0), 0, False)
    # the ring of doubloons turning round it
    for k in range(16):
        a = 2 * math.pi * k / 16
        c = Vector((math.cos(a) * 2.25, math.sin(a) * 2.05 - 0.1, 0.5 + 0.35 * math.sin(a * 3)))
        m = Matrix.Rotation(math.radians(90), 3, "X") @ Matrix.Rotation(0.0, 3, "Z")
        m = Matrix.Rotation(a + math.pi / 2, 3, "Z") @ Matrix.Rotation(math.radians(90), 3, "X")
        P.part("SpinCoins", coin(c, 0.16, 0.04, m), "Trim", (0, -0.1, 0.5), 0, False)
        P.part("SpinCoins", coin(c, 0.09, 0.05, m), "Lamp", (0, -0.1, 0.5), 0, False)
    P.part("Muzzle", ball(tuple(sc + Vector((0, 0.72, -0.62))), (0.08, 0.04, 0.06), 8, 4), "Glow", tuple(sc + Vector((0, 0.72, -0.62))))
    return P


# ================================================================= skull rock, the second round (2026-10-11: "make the skull by itself")
def T_skull2():
    """The last boss, the dread skull: a giant pirate's skull on its own - green ghost-fire burning in deep sockets under a scowling brow,
    a cracked crown of bone, a grin of big teeth with two of gold and a jaw that chomps, a crimson bandana knotted at the side under a
    great gold-edged tricorn with a ruby badge and a crimson plume, crossed bones behind it, and a ring of gold doubloons turning round it."""
    P = Boss("skull2", {"Base": ((0.70, 0.62, 0.48), 0.3), "Belly": BONE, "Accent": ((0.70, 0.05, 0.07), 0.45), "Trim": GOLD,
                        "Glass": ((0.85, 0.04, 0.12), 0.9), "Dark": BLACK, "Glow": ((0.08, 0.85, 0.30), 0.5),
                        "Metal": GOLD, "Lamp": ((1.0, 0.82, 0.35), 0.8)})
    bone = lambda c, n: "Base" if n.z < -0.6 else "Belly"
    sc = Vector((0, 0, 0.2))
    P.obj("Cranium", ball(tuple(sc), (0.95, 0.88, 0.92), 24, 12), bone, 1)
    P.obj("Face", ball((0, 0.32, -0.32), (0.78, 0.6, 0.5), 20, 10), bone, 1)
    for s in (1, -1):
        P.obj("Cheek", ball((s * 0.58, 0.5, -0.2), (0.26, 0.26, 0.18), 12, 6), bone, 1)
        # the sockets, tilted into a scowl, ghost-fire burning in them and licking up out of them
        m = Matrix.Rotation(math.radians(-s * 18), 3, "Y")
        P.obj("Socket", xf(ball((0, 0, 0), (0.3, 0.16, 0.27), 16, 8), m, (s * 0.36, 0.73, 0.02)), "Dark", 1)
        P.obj("EyeFire", xf(ball((0, 0, 0), (0.15, 0.06, 0.15), 12, 6), m, (s * 0.36, 0.84, 0.0)), "Glow", 1)
        P.obj("EyeCore", ball((s * 0.36, 0.88, 0.0), (0.05, 0.03, 0.06), 8, 4), "Lamp")
        # the brow ridge, low and angry at the middle
        P.obj("Brow", hull([(s * 0.06, 0.9, 0.1), (s * 0.08, 0.88, 0.2), (s * 0.36, 0.86, 0.36), (s * 0.36, 0.82, 0.26), (s * 0.64, 0.66, 0.38),
                            (s * 0.66, 0.62, 0.28), (s * 0.08, 0.76, 0.12), (s * 0.36, 0.72, 0.3), (s * 0.62, 0.52, 0.3)]), "Belly", 0, False)
    P.obj("Nose", hull([(0, 0.97, -0.1), (0.11, 0.92, -0.3), (-0.11, 0.92, -0.3), (0, 0.95, -0.36), (0.05, 0.86, -0.2), (-0.05, 0.86, -0.2)]), "Dark", 0, False)
    for crack in (((-0.18, 0.78, 0.75), (-0.28, 0.82, 0.55), (-0.2, 0.86, 0.42)), ((0.3, 0.6, 0.85), (0.42, 0.66, 0.66), (0.36, 0.72, 0.5))):
        P.obj("Crack", pipe([Vector(p) for p in crack], [0.025, 0.02, 0.0], 5), "Dark")
    # the grin: the upper teeth (two of gold), the dark mouth behind them
    P.obj("Mouth", ball((0, 0.52, -0.68), (0.52, 0.36, 0.17), 16, 8), "Dark", 1)
    P.obj("Maxilla", hull([(x, 0.84 - 0.9 * x * x, z) for x in (-0.5, -0.25, 0.0, 0.25, 0.5) for z in (-0.44, -0.52)] +
                          [(x, 0.6 - 0.9 * x * x, z) for x in (-0.5, 0.0, 0.5) for z in (-0.44, -0.52)]), "Belly", 0, False)
    for k in range(8):
        x = -0.42 + k * 0.12
        P.obj("Tooth", box((x, 0.85 - 0.9 * x * x, -0.6), (0.1, 0.08, 0.16)), "Metal" if k in (2, 5) else "Belly", 0, False)
    # the jaw, chomping about its hinge
    hub = (0, 0.1, -0.5); J = Matrix.Rotation(math.radians(-10), 3, "X")
    def jx(bm):
        for v in bm.verts: v.co = J @ (v.co - Vector(hub)) + Vector(hub)
        return bm
    path = [Vector(p) for p in ((-0.66, 0.05, -0.42), (-0.62, 0.22, -0.84), (-0.42, 0.6, -0.92), (0.0, 0.82, -0.96), (0.42, 0.6, -0.92), (0.62, 0.22, -0.84), (0.66, 0.05, -0.42))]
    jp = AB_spline(path, 5)
    P.part("SwayJaw", jx(pipe(jp, [0.12] * len(jp), 12)), bone, hub, 1)
    P.part("SwayJaw", jx(ball((0, 0.74, -0.95), (0.42, 0.18, 0.14), 14, 7)), bone, hub, 1)
    for k in range(8):
        x = -0.42 + k * 0.12
        P.part("SwayJaw", jx(box((x, 0.8 - 0.9 * x * x, -0.78), (0.1, 0.08, 0.14))), "Metal" if k == 3 else "Belly", hub, 0, False)
    # the crimson bandana, gold-spotted, knotted at the side, its tails hanging
    P.obj("Bandana", torus(0.8, 0.08, 0.72, 36, 8), lambda c, n: "Trim" if speckle(c, 2.2) < 0.08 else "Accent")
    for v in P.parts[-1].data.vertices: v.co.y *= 0.93
    kc = Vector((-0.74, -0.32, 0.68))
    P.obj("Knot", ball(tuple(kc), (0.12, 0.12, 0.12), 10, 5), "Accent", 1)
    for k in range(2):
        P.obj("BandanaTail", pipe(bez(kc, kc + Vector((-0.15, -0.1 - k * 0.08, -0.15)), kc + Vector((-0.2, -0.25 - k * 0.1, -0.4)), kc + Vector((-0.12 - k * 0.1, -0.4 - k * 0.1, -0.62)), 6),
                                  [0.1, 0.11, 0.1, 0.09, 0.08, 0.06, 0.02], 6), "Accent")
    # the tricorn, worn at a rake, a ruby badge in gold and a crimson plume
    h0 = len(P.parts)
    tricorn(P, (0, -0.05, 0.84), 0.68, 1.3, 0.42, 0.48, emblem=False, paint="Dark")
    P.obj("Badge", xf(lathe([(0.0, -0.03), (0.17, -0.03), (0.18, 0.0), (0.17, 0.03), (0.0, 0.03)], 20, "y"), Matrix.Rotation(math.radians(-20), 3, "X"), (0, 0.62, 1.08)), "Metal")
    P.obj("Ruby", ball((0, 0.66, 1.09), (0.09, 0.05, 0.1), 12, 6), "Glass", 1)
    pl = bez((0.45, 0.25, 1.15), (0.9, 0.1, 1.55), (1.05, -0.4, 1.7), (0.85, -0.95, 1.55), 10)
    P.obj("Plume", pipe(pl, [0.06, 0.12, 0.15, 0.16, 0.16, 0.15, 0.13, 0.11, 0.08, 0.05, 0.0], 8), "Accent")
    R = Matrix.Rotation(math.radians(-9), 3, "Y"); pv = Vector((0, 0, 0.84))
    for ob in P.parts[h0:]:
        for v in ob.data.vertices: v.co = R @ (v.co - pv) + pv
    # crossed bones behind
    for s in (1, -1):
        a0 = Vector((-s * 1.5, -0.6, -1.12)); a1 = Vector((s * 1.5, -0.6, 1.0))
        P.obj("Bone", pipe([a0, a0 + (a1 - a0) * 0.5, a1], [0.12, 0.1, 0.12], 12), "Belly", 1)
        d = (a1 - a0).normalized(); side = d.cross(Vector((0, 1, 0))).normalized()
        for e in (a0, a1):
            for q in (1, -1):
                P.obj("Knob", ball(tuple(e + side * q * 0.12 + (d if e is a1 else -d) * 0.04), (0.16, 0.14, 0.16), 12, 6), "Belly", 1)
    # the ring of doubloons turning round it
    for k in range(16):
        a = 2 * math.pi * k / 16
        c = Vector((math.cos(a) * 2.15, math.sin(a) * 2.0, -0.85))      # low, round the jaw, so none passes over the face
        m = Matrix.Rotation(a + math.pi / 2, 3, "Z") @ Matrix.Rotation(math.radians(90), 3, "X")
        P.part("SpinCoins", coin(c, 0.17, 0.04, m), "Trim", (0, 0, -0.85), 0, False)
        P.part("SpinCoins", coin(c, 0.1, 0.05, m), "Lamp", (0, 0, -0.85), 0, False)
    P.part("Muzzle", ball((0, 0.86, -0.68), (0.08, 0.04, 0.06), 8, 4), "Glow", (0, 0.86, -0.68))
    return P

def AB_spline(pts, n):
    P_ = [Vector(p) for p in pts]
    P_ = [P_[0] * 2 - P_[1]] + P_ + [P_[-1] * 2 - P_[-2]]
    out = []
    for i in range(1, len(P_) - 2):
        p0, p1, p2, p3 = P_[i - 1], P_[i], P_[i + 1], P_[i + 2]
        for k in range(n):
            t = k / n
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(P_[-2])
    return out


BOSSES = [("parrot", T_parrot), ("mimic", T_mimic), ("ghost", T_ghost), ("crab", T_crab), ("skull2", T_skull2)]

if __name__ == "__main__":
    os.makedirs(AB.OUT, exist_ok=True)
    for bid, fn in BOSSES:
        if ONLY and bid not in ONLY: continue
        fn().finish()
    print("DONE")
