# Sky Squad, the treasure island's five bosses (2026-10-11: "the bosses for the rest of the maps"): the captain parrot, the treasure mimic,
# the ghost captain, the cannon crab and skull rock. Built from code like the other worlds' bosses (alien_bosses.py lends its Boss class and
# shapes).
# Run: blender -b -P Tools/blender/treasure_bosses.py -- <out dir> [export] [ids,comma,separated]
#      (export also bakes each boss's surfaces into Boss_<id>_Albedo / _Normal / _Mask / _Emission.png beside its FBX: boss_bake.py)
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


# ================================================================= 2026-10-14: the five remade like the alien / autumn / west ones
# Real anatomy and proportions, details that each have a reason and sit evenly, scarier faces, the cartoon idea kept - and each flies its own
# way, one you can see from the front: the captain parrot on his own macaw wings (the one bird), the mimic sails the sky under a mast rammed
# through its lid, the ghost captain is rowed through the air by his skeleton crew, the cannon crab hangs from three blown-up pufferfish,
# and the dread skull is the Jolly Roger come to life - its crossbones spin behind it like a propeller.
from west_bosses import V_, flat_pipe, feather, glow_strength, AB_pal, flame, fib_dirs, hint_frames, ribbon_tube
from alien_bosses import lerp_keys, spine_frames, oriented_ball
from autumn_bosses import fx_tuft, st_loft, st_cloth, st_sheet, sq_axes, spline

def femur(P, name, head, cond, r, slot, hub=None):
    """a real thigh bone from the hip end to the knee end: the ball of the head on its angled neck, the great trochanter, a shaft bowed a
    little forward, and at the knee the two rounded condyles with the groove between them."""
    head, cond = V_(head), V_(cond); d = (cond - head).normalized()
    side = d.cross(V_((0, 1, 0))); side = side.normalized() if side.length > 1e-4 else V_((1, 0, 0))
    fwd = side.cross(d).normalized()
    def put(bm):
        if hub is None: P.obj(name, bm, slot, 0)
        else: P.part(name, bm, slot, hub)
    L = (cond - head).length
    shaft = [head + d * L * t + fwd * 0.05 * r * math.sin(math.pi * t) for t in (0.12, 0.3, 0.5, 0.7, 0.86)]
    put(pipe(shaft, [r * 1.15, r * 0.92, r * 0.85, r * 0.95, r * 1.3], 12))
    nk = head + d * L * 0.06 - side * r * 1.1
    put(pipe([shaft[0], nk], [r, r * 0.8], 10))
    put(ball(tuple(nk - side * r * 0.6), (r * 1.25,) * 3, 14, 7))                        # the head of the femur
    put(ball(tuple(head + d * L * 0.08 + side * r * 0.75), (r * 0.9, r * 0.9, r * 1.1), 12, 6))   # the great trochanter
    for q in (1, -1):                                                                       # the two condyles at the knee
        put(ball(tuple(cond - d * r * 0.4 + side * q * r * 0.65 - fwd * r * 0.2), (r * 0.85, r * 0.95, r * 0.85), 12, 6))


def T2_skull():
    """The DREAD SKULL (2026-10-14, remade like the alien / autumn / west bosses): the Jolly Roger come to life. A giant skull built like a
    real one: the vault of the cranium with its sutures - the coronal across the top, the sagittal down the middle, the lambdoid at the back -
    a heavy brow ridge low over the nose, the scowl; deep orbits with green ghost-fire burning in them, a white-hot core in each; the
    pear-shaped nasal opening; the cheekbones sweeping back into the zygomatic arches; the upper teeth set in the maxilla, two of them gold
    and one gone; and the mandible hinged under the ear, its chin and its own row of teeth, chomping (SwayJaw). A sword cut has cracked it
    from the brow over the crown. A crimson bandana under a great black tricorn edged in gold, a ruby in a gold badge and a crimson plume.
    It flies on its CROSSBONES: two real thigh bones crossed behind it on an iron shaft through the back of the skull, spinning like the blades
    of a propeller (PropBones), a gold spinner on the hub."""
    P = Boss("skull2", AB_pal(Base=((0.70, 0.62, 0.48), 0.3), Belly=((0.95, 0.92, 0.82), 0.35), Accent=((0.70, 0.05, 0.07), 0.45),
                              Trim=((0.98, 0.76, 0.22), 0.8), Glass=((0.85, 0.04, 0.12), 0.9), Dark=((0.05, 0.05, 0.06), 0.5),
                              Glow=((0.08, 0.85, 0.30), 0.5), Metal=((0.3, 0.3, 0.33), 0.7), Lamp=((0.75, 1.0, 0.8), 0.8)))
    glow_strength(P, 2.2)
    bone = lambda c, n: "Base" if n.z < -0.55 else "Belly"
    # ---- the cranium: a long vault, the temples flattened a little; the sutures as fine dark seams over it
    CC = V_((0, -0.12, 0.28)); CR = (0.92, 1.05, 0.9)
    cran = ball(tuple(CC), CR, 48, 24)
    for v in cran.verts:
        if abs(v.co.x) > 0.6 and v.co.z < 0.45: v.co.x *= 1 - 0.12 * min(1.0, (abs(v.co.x) - 0.6) / 0.3) * min(1.0, (0.45 - v.co.z) / 0.4)   # the temples
    holes = []   # (centre, frame, rx, rz): openings cut through the vault and the face
    def on_cran(u, w, lift=0.006):
        """a point on the vault: u across (-1..1), w front-to-back (-1..1)."""
        x, y = u * CR[0], w * CR[1]; k = max(0.0, 1 - u * u - w * w)
        return V_((x, CC.y + y, CC.z + CR[2] * math.sqrt(k))) + V_((u, w, math.sqrt(k) + 1e-3)).normalized() * lift
    def suture(pts, r=0.012):
        zig = []
        for i, (a, b) in enumerate(zip(pts, pts[1:])):
            for t in (0.0, 0.5):
                q = a + (b - a) * t
                zig.append(q + ((b - a).cross(V_((0, 0, 1))).normalized() * (0.018 if (i * 2 + int(t * 2)) % 2 else -0.018)))
        zig.append(pts[-1])
        P.obj("Suture", pipe(zig, [r] * len(zig), 4), "Base")
    suture([on_cran(u / 10, 0.18 - 0.08 * (u / 10) ** 2) for u in range(-8, 9)])     # coronal, across the top
    suture([on_cran(0, w / 10) for w in range(2, -9, -1)])                            # sagittal, down the middle
    suture([on_cran(u / 10, -0.6 - 0.18 * (1 - abs(u) / 8)) for u in range(-7, 8)])   # lambdoid, at the back
    # the crack of a sword cut from the brow over the crown, branching
    cr = [on_cran(0.12, 0.62, 0.0), on_cran(0.18, 0.45, 0.0), on_cran(0.14, 0.3, 0.0), on_cran(0.2, 0.12, 0.0)]
    P.obj("Crack", pipe(cr, [0.0, 0.026, 0.022, 0.0], 5), "Dark")
    P.obj("Crack", pipe([cr[1], on_cran(0.3, 0.42, 0.0), on_cran(0.36, 0.36, 0.0)], [0.016, 0.012, 0.0], 5), "Dark")
    # ---- the face: the brow ridge, the orbits, the nasal opening, the cheekbones and arches
    face = ball((0, 0.42, -0.2), (0.74, 0.58, 0.55), 48, 24)
    for s in (1, -1):
        P.obj("Brow", pipe(bez((0, 0.93, 0.1), (s * 0.18, 0.92, 0.22), (s * 0.44, 0.83, 0.36), (s * 0.68, 0.64, 0.34), 8),
                           [0.1, 0.11, 0.11, 0.11, 0.1, 0.095, 0.085, 0.07, 0.05], 10), "Belly")
        m = Matrix.Rotation(math.radians(-s * 16), 3, "Y")
        oc = V_((s * 0.35, 0.8, 0.0))
        holes.append((oc, m, 0.27, 0.25))   # cut a little inside the bony rim, which hides the cut edge
        cup = ball((0, 0, 0), (0.31, 0.3, 0.29), 18, 9)          # the hollow of the orbit behind the opening, seen from inside
        bmesh.ops.delete(cup, geom=[v for v in cup.verts if v.co.y > 0.02], context="VERTS"); bmesh.ops.reverse_faces(cup, faces=cup.faces)
        P.obj("Orbit", xf(cup, m, tuple(oc + V_((0, 0.1, 0)))), "Dark")
        rim = [oc + m @ V_((math.cos(a) * 0.33, 0.06 - 0.03 * math.sin(a), math.sin(a) * 0.31)) for a in [2 * math.pi * k / 32 for k in range(33)]]
        P.obj("OrbitRim", pipe(rim, [0.07] * 33, 8, False), "Belly")
        P.obj("EyeFire", xf(ball((0, 0, 0), (0.17, 0.08, 0.16), 14, 7), m, tuple(oc + V_((0, -0.04, -0.03)))), "Glow")
        P.obj("EyeCore", ball(tuple(oc + V_((0, 0.02, -0.03))), (0.06, 0.03, 0.07), 10, 5), "Lamp")
        # the cheekbone below the orbit, sweeping back into the zygomatic arch to the ear
        zy = bez(oc + V_((s * 0.04, 0.02, -0.26)), oc + V_((s * 0.25, -0.05, -0.28)), oc + V_((s * 0.42, -0.35, -0.24)), V_((s * 0.82, 0.05, -0.18)), 8)
        P.obj("Zygoma", pipe(zy, [0.09, 0.1, 0.095, 0.085, 0.075, 0.07, 0.065, 0.06, 0.06], 8), "Belly")
        P.obj("Mastoid", ball((s * 0.74, -0.12, -0.42), (0.11, 0.12, 0.16), 10, 5), "Belly")
    holes.append((V_((0, 0.95, -0.29)), Matrix.Identity(3), 0.11, 0.15))   # the nasal opening (pear-shaped: narrower at the top, below)
    ncup = ball((0, 0, 0), (0.11, 0.2, 0.15), 12, 6)
    bmesh.ops.delete(ncup, geom=[v for v in ncup.verts if v.co.y > 0.02], context="VERTS"); bmesh.ops.reverse_faces(ncup, faces=ncup.faces)
    P.obj("Nasal", xf(ncup, None, (0, 1.0, -0.29)), "Dark")
    def cut(bm):
        dead = []
        for f in bm.faces:
            c = f.calc_center_median()
            for (hc, hm, rx, rz) in holes:
                q = hm.inverted() @ (c - hc)
                if q.y > -0.25 and (q.x / rx) ** 2 + (q.z / (rz * (1.15 if rz > 0.2 else 1.0) if q.z < 0 else rz)) ** 2 < 1.0: dead.append(f); break
        bmesh.ops.delete(bm, geom=dead, context="FACES")
        return bm
    P.obj("Cranium", cut(cran), bone, 0)
    P.obj("Face", cut(face), bone, 0)
    P.obj("NasalSpine", cone((0, 0.99, -0.44), (0, 1.06, -0.43), 0.025, 5), "Belly")
    # ---- the maxilla and the upper teeth: a curved row, two of gold, one gone
    arc = lambda t, R=0.48, y0=0.98: V_((math.sin(t) * R, y0 - (1 - math.cos(t)) * R * 0.9, 0.0))
    P.obj("Maxilla", pipe([arc(math.radians(a)) + V_((0, -0.04, -0.5)) for a in range(-80, 81, 10)], [0.08] * 17, 8), "Belly")
    for k in range(12):
        t = math.radians(-66 + 12 * k)
        if k == 8: continue                                   # the gap of a lost tooth
        q = arc(t) + V_((0, 0.0, -0.62)); w = 0.055 if 3 < k < 8 else 0.065
        P.obj("Tooth", xf(ball((0, 0, 0), (w, 0.045, 0.085), 8, 4), Matrix.Rotation(-t, 3, "Z"), tuple(q)), "Trim" if k in (2, 6) else "Belly")
    P.obj("Mouth", ball((0, 0.6, -0.7), (0.46, 0.34, 0.14), 16, 8), "Dark")
    # ---- the mandible, hinged under the ears and chomping: the rami, the body round to the chin, its row of teeth
    hub = (0, 0.02, -0.42); JR = Matrix.Rotation(math.radians(-9), 3, "X")
    def J(bm):
        for v in bm.verts: v.co = JR @ (v.co - V_(hub)) + V_(hub)
        return bm
    for s in (1, -1):
        P.part("SwayJaw", J(pipe([V_((s * 0.66, 0.02, -0.4)), V_((s * 0.62, 0.12, -0.78)), V_((s * 0.5, 0.36, -0.92))], [0.1, 0.11, 0.11], 10)), bone, hub)
    body = [V_((s_ * math.sin(t) * 0.5, 0.98 - (1 - math.cos(t)) * 0.5 * 0.9 - 0.04, -0.9 - 0.06 * math.cos(t))) for t, s_ in
            [(math.radians(a), 1) for a in range(-80, 81, 10)]]
    P.part("SwayJaw", J(pipe(body, [0.12] * len(body), 10)), bone, hub)
    P.part("SwayJaw", J(ball((0, 0.92, -1.0), (0.2, 0.1, 0.1), 12, 6)), bone, hub)   # the chin
    for k in range(10):
        t = math.radians(-60 + 13.3 * k)
        q = V_((math.sin(t) * 0.46, 0.96 - (1 - math.cos(t)) * 0.46 * 0.9 - 0.05, -0.8))
        P.part("SwayJaw", J(xf(ball((0, 0, 0), (0.05, 0.04, 0.075), 8, 4), Matrix.Rotation(-t, 3, "Z"), tuple(q))), "Trim" if k == 4 else "Belly", hub)
    # ---- the bandana and the tricorn
    cap = ball(tuple(CC), (CR[0] * 1.035, CR[1] * 1.035, CR[2] * 1.035), 32, 16)
    bmesh.ops.delete(cap, geom=[v for v in cap.verts if v.co.z < 0.56 - 0.12 * max(0.0, -(v.co.y - CC.y)) / CR[1]], context="VERTS")
    P.obj("Bandana", cap, "Accent", 0)
    kc = V_((-0.8, -0.42, 0.58))
    P.obj("Knot", ball(tuple(kc), (0.13,) * 3, 10, 5), "Accent")
    for k in range(2):
        P.obj("BandanaTail", flat_pipe(bez(kc, kc + V_((-0.12, -0.12 - k * 0.08, -0.15)), kc + V_((-0.18, -0.25 - k * 0.1, -0.42)), kc + V_((-0.1 - k * 0.1, -0.38 - k * 0.1, -0.66)), 6),
                                         [0.1, 0.11, 0.1, 0.09, 0.08, 0.06, 0.02], V_((0, 1, 0)), 0.6, 8), "Accent")
    h0 = len(P.parts)
    tricorn(P, (0, -0.12, 0.82), 0.7, 1.32, 0.42, 0.5, emblem=False, paint="Dark")
    P.obj("Badge", xf(lathe([(0.0, -0.03), (0.17, -0.03), (0.18, 0.0), (0.17, 0.03), (0.0, 0.03)], 20, "y"), Matrix.Rotation(math.radians(-20), 3, "X"), (0, 0.58, 1.06)), "Trim")
    P.obj("Ruby", ball((0, 0.62, 1.07), (0.09, 0.05, 0.1), 12, 6), "Glass")
    pl = bez((0.45, 0.2, 1.15), (0.9, 0.05, 1.55), (1.05, -0.45, 1.7), (0.85, -1.0, 1.55), 28)
    P.obj("Plume", pipe(pl, [0.035] * 28 + [0.0], 5), "Accent")
    for i in range(1, 28):   # the soft barbs, close together, drooping, longest in the middle
        t = (pl[i + 1] - pl[i - 1]).normalized(); up = V_((0, 0, 1)); sd = t.cross(up).normalized(); L = 0.34 * math.sin(math.pi * i / 28) ** 0.7 + 0.06
        for q in (1, -1):
            P.obj("Plume", fx_tuft(pl[i], sd * q * 0.8 - t * 0.55 - up * 0.2, L, 0.07, up, -0.06), "Accent", 0, False)
    R = Matrix.Rotation(math.radians(-9), 3, "Y"); pv = V_((0, 0, 0.82))
    for ob in P.parts[h0:]:
        for v in ob.data.vertices: v.co = R @ (v.co - pv) + pv

    # ---- the crossbones: two real femurs crossed behind the skull on an iron shaft, spinning like a propeller
    HZ = 0.05; HY = -1.35; hubp = (0, HY, HZ)
    P.obj("Shaft", pipe([V_((0, -0.85, HZ)), V_((0, HY + 0.02, HZ))], [0.07, 0.07], 12), "Metal")
    P.obj("ShaftCollar", pipe([V_((0, -0.9, HZ)), V_((0, -1.0, HZ))], [0.11, 0.11], 14), "Trim")
    for s in (1, -1):
        a = math.radians(45 if s > 0 else 135)
        dvec = V_((math.cos(a), 0, math.sin(a)))
        femur(P, "PropBones", V_(hubp) - dvec * 2.15, V_(hubp) + dvec * 2.15, 0.13, "Belly", hubp)
    P.part("PropBones", lathe([(0.0, -0.32), (0.08, -0.28), (0.15, -0.16), (0.17, 0.0), (0.0, 0.0)], 20, "y", (0, HY, HZ)), "Trim", hubp)   # the spinner
    for k in range(4):
        a = 2 * math.pi * (k + 0.5) / 4
        P.part("PropBones", ball((math.cos(a) * 0.12, HY + 0.02, HZ + math.sin(a) * 0.12), (0.03,) * 3, 6, 3), "Metal", hubp)
    P.part("Muzzle", ball((0, 0.86, -0.72), (0.08, 0.04, 0.06), 8, 4), "Glow", (0, 0.86, -0.72))
    return P


def ship_cannon(P, c, d, L=0.9, R=0.16, iron="Metal", brass="Trim", name="Cannon", hub=None):
    """a naval cannon along d from its breech at c: the cascabel knob, the breech ring, two reinforce rings, the chase tapering to the muzzle
    swell and its lip, the bore dark inside, a touch hole on top. Returns the muzzle point."""
    c, d = V_(c), V_(d).normalized(); x, y, z = sq_axes(d)
    M3 = Matrix((x, y, z)).transposed()   # local z along the barrel
    def put(bm, slot):
        bm = xf(bm, M3, tuple(c))
        if hub is None: P.obj(name, bm, slot, 0)
        else: P.part(name, bm, slot, hub)
    prof = [(0.0, -0.1), (0.05 * R / 0.16, -0.1), (0.07 * R / 0.16, -0.06), (R * 0.95, -0.02), (R, 0.04), (R * 0.97, 0.3 * L), (R * 0.82, 0.62 * L),
            (R * 0.72, 0.88 * L), (R * 0.84, 0.95 * L), (R * 0.86, L), (R * 0.55, L), (R * 0.5, 0.92 * L)]
    put(lathe(prof, 20, "z"), iron)
    put(ball((0, 0, -0.14), (R * 0.42,) * 3, 10, 5), iron)                                   # the cascabel knob
    for zz in (0.05, 0.3 * L, 0.6 * L):
        put(torus(R * (1.02 if zz < 0.4 * L else 0.86), R * 0.09, zz, 24, 5), brass)
    put(lathe([(R * 0.5, 0.995 * L), (0.0, 0.8 * L)], 14, "z"), "Dark")                         # the bore
    put(pipe([V_((0, R * 0.9, 0.08)), V_((0, R * 1.05, 0.08))], [0.025, 0.02], 6), "Dark")     # the touch hole
    for s in (1, -1):                                                                           # the trunnions
        put(pipe([V_((s * R * 0.9, 0, 0.42 * L)), V_((s * R * 1.35, 0, 0.42 * L))], [R * 0.25, R * 0.25], 8), iron)
    return c + d * L


def puffer(P, c, R, name, beat_name):
    """a porcupinefish blown up into a ball: spines all over in even rows, the big eyes under a frown, the little beak of a mouth with its
    fused teeth, dark spots over the back, the pale belly; its two pectoral fins fan fast to hold it up (beat_name + L / R)."""
    c = V_(c)
    P.obj(name, ball(tuple(c), (R, R * 0.96, R * 0.94), 24, 12), lambda q, n: "Belly" if n.z < -0.25 else "Accent", 0)
    for d in fib_dirs(70):
        if d.y > 0.55 and d.z > -0.5: continue                         # the face is clear of spines
        b = c + V_((d.x * R, d.y * R * 0.96, d.z * R * 0.94))
        P.obj(name + "Spine", cone(b - d * 0.02, b + d * R * 0.24, R * 0.045, 4), "Belly" if d.z < -0.25 else "Accent", 0, False)
    for d in fib_dirs(26):
        if d.z < 0.15 or d.y > 0.5: continue
        b = c + V_((d.x * R, d.y * R * 0.96, d.z * R * 0.94)) * 1.0
        x, y, z = sq_axes(d)
        P.obj(name + "Spot", oriented_ball(b, (R * 0.09, R * 0.09, R * 0.02), x, y, z, 8, 3), "Dark")
    for s in (1, -1):
        e = c + V_((s * R * 0.42, R * 0.78, R * 0.25)); dv = V_((s * 0.5, 0.86, 0.1)).normalized()
        ex, ey, ez = sq_axes(dv)
        P.obj(name + "Eye", oriented_ball(e, (R * 0.2, R * 0.2, R * 0.14), ex, ey, dv, 14, 7), "Belly")
        P.obj(name + "Iris", oriented_ball(e + dv * R * 0.11, (R * 0.12, R * 0.12, R * 0.05), ex, ey, dv, 12, 5), "Glow")
        P.obj(name + "Pupil", oriented_ball(e + dv * R * 0.15, (R * 0.06, R * 0.06, R * 0.03), ex, ey, dv, 8, 4), "Dark")
        P.obj(name + "Brow", pipe([e + V_((-s * R * 0.2, R * 0.08, R * 0.12)), e + V_((s * R * 0.02, R * 0.1, R * 0.2)), e + V_((s * R * 0.22, R * 0.02, R * 0.24))],
                                  [R * 0.05, R * 0.07, R * 0.04], 6), "Dark")   # low over the nose: a frown
        # the pectoral fin behind the eye, fanning
        fr = c + V_((s * R * 0.92, R * 0.15, -R * 0.05)); hub = tuple(fr)
        rays = [fr + V_((s * R * (0.12 + 0.3 * math.cos(a)), -R * 0.45 * math.sin(a) - R * 0.05, R * 0.3 * math.sin(a) * 0.6)) for a in [math.radians(-70 + 28 * k) for k in range(6)]]
        P.part(beat_name + ("R" if s > 0 else "L"), fan(fr, rays, 0.02, 0.18), "Accent", hub, 0, False)
    m0 = c + V_((0, R * 0.98, -R * 0.12))
    P.obj(name + "Lip", torus(R * 0.12, R * 0.045, 0.0, 16, 5), "Accent"); P.parts[-1].data.transform(Matrix.Translation(m0) @ Matrix.Rotation(math.pi / 2, 4, "X"))
    P.obj(name + "Mouth", oriented_ball(m0 + V_((0, 0.01, 0)), (R * 0.09, R * 0.03, R * 0.07), V_((1, 0, 0)), V_((0, 0, 1)), V_((0, 1, 0)), 10, 4), "Dark")
    for q in (1, -1):
        P.obj(name + "Beak", oriented_ball(m0 + V_((0, R * 0.02, q * R * 0.05)), (R * 0.08, R * 0.02, R * 0.025), V_((1, 0, 0)), V_((0, 0, 1)), V_((0, 1, 0)), 8, 3), "Belly")
    tail = c + V_((0, -R * 1.0, 0))
    P.obj(name + "Tail", fan(tail, [tail + V_((R * 0.3 * math.sin(a), -R * 0.35, R * 0.3 * math.cos(a))) for a in [math.radians(-80 + 32 * k) for k in range(6)]], 0.02, 0.2), "Accent", 0, False)


def T2_crab():
    """The CANNON CRAB (2026-10-14, remade like the alien / autumn / west bosses): a giant mud crab built like the real animal - a broad
    carapace, nine teeth down each front edge and four lobes between the eyes, the grooves of its regions cut across the top in the H a real
    crab carries, granules in even rows; the eyes on stalks under spiny brows (one of them under a pirate's patch), the antennae and the
    plates of the mouth. The claws are real chelipeds - the spiny arm, the wrist with its great spine, the swollen palm - and each grips a
    ship's iron cannon in its fingers, aimed at you; the eight walking legs, each in four jointed parts with spines, hang and paddle in the air
    one after another (Sway*).
    It flies on PUFFERFISH: three porcupinefish blown up into spiny balls, roped round the middle and tied to its shell, hold it up like
    balloons, each fanning its little pectoral fins (Flap*) and glaring down with its big eyes."""
    P = Boss("crab", AB_pal(Base=((0.82, 0.22, 0.08), 0.55), Belly=((0.96, 0.88, 0.72), 0.4), Accent=((0.92, 0.7, 0.26), 0.45),
                            Trim=((0.86, 0.62, 0.26), 0.8), Glass=((0.03, 0.03, 0.04), 0.9), Dark=((0.05, 0.05, 0.06), 0.5),
                            Glow=((0.25, 0.75, 0.95), 0.5), Metal=((0.2, 0.2, 0.22), 0.7), Lamp=((1.0, 0.85, 0.5), 0.8)))
    glow_strength(P, 1.2)
    # ---- the carapace: wide, domed, flat underneath
    CR = [(-0.62, 0.5, 0.16, 0, 0.04), (-0.42, 0.82, 0.28, 0, 0.05), (-0.12, 1.0, 0.35, 0, 0.06), (0.18, 1.04, 0.34, 0, 0.06),
          (0.4, 0.88, 0.27, 0, 0.05), (0.54, 0.6, 0.18, 0, 0.04), (0.62, 0.32, 0.1, 0, 0.03)]
    shell = loft(CR, 40, sq=1.3)
    for v in shell.verts:
        if v.co.z < 0.04: v.co.z = 0.04 + (v.co.z - 0.04) * 0.45
    P.obj("Carapace", shell, lambda c, n: "Belly" if n.z < -0.3 else "Base", 0)
    def ring_at(y):
        for r0, r1 in zip(CR, CR[1:]):
            if y <= r1[0]:
                f = max(0.0, (y - r0[0]) / (r1[0] - r0[0])); return [a + (b - a) * f for a, b in zip(r0, r1)]
        return list(CR[-1])
    def top(x, y, lift=0.0):
        r = ring_at(y); u = min(0.98, abs(x) / r[1])
        return V_((x, y, r[4] + r[2] * (1 - u ** 2.6) ** (1 / 2.6) + lift))
    # nine teeth down each front edge, four lobes between the eyes
    for s in (1, -1):
        for k in range(9):
            y = 0.5 - 0.075 * k; r = ring_at(y); b = V_((s * r[1] * 0.97, y, r[4] + 0.03))
            out = V_((s * 1.0, 0.45 - 0.08 * k, 0.05)).normalized()
            P.obj("Tooth", cone(b - out * 0.03, b + out * (0.1 + 0.015 * (k % 3 == 2)), 0.045, 5), "Base", 0, False)
            P.obj("ToothTip", cone(b + out * 0.07, b + out * (0.12 + 0.015 * (k % 3 == 2)), 0.02, 4), "Dark", 0, False)
    for k in range(4):
        x = -0.12 + 0.08 * k
        P.obj("Lobe", ball((x, 0.64, 0.1), (0.04, 0.035, 0.03), 8, 4), "Base")
    # the H of the grooves across the top and the granules in even rows
    for s in (1, -1):
        P.obj("Groove", pipe([top(s * 0.22, 0.32, 0.005), top(s * 0.26, 0.05, 0.005), top(s * 0.2, -0.3, 0.005)], [0.014] * 3, 5), "Accent")
    P.obj("Groove", pipe([top(-0.25, 0.05, 0.005), top(0, 0.02, 0.005), top(0.25, 0.05, 0.005)], [0.014] * 3, 5), "Accent")
    for i in range(-6, 7):
        for j in range(-4, 5):
            x, y = i * 0.13 + (0.065 if j % 2 else 0.0), j * 0.12
            r = ring_at(y)
            if abs(x) > r[1] * 0.85 or abs(abs(x) - 0.24) < 0.04: continue
            P.obj("Granule", ball(tuple(top(x, y, -0.005)), (0.025, 0.025, 0.018), 6, 3), "Base")
    # ---- the eyes on stalks under spiny brows, one under a patch; antennae; the plates of the mouth
    for s in (1, -1):
        st0 = V_((s * 0.2, 0.56, 0.12)); st1 = V_((s * 0.25, 0.7, 0.34))
        P.obj("Stalk", pipe(bez(st0, st0 + V_((0, 0.05, 0.1)), st1 - V_((0, 0.03, 0.06)), st1, 5), [0.05, 0.05, 0.045, 0.045, 0.045, 0.045], 8), "Base")
        P.obj("Eye", ball(tuple(st1 + V_((0, 0.02, 0.05))), (0.085, 0.08, 0.09), 12, 6), "Glass")
        P.obj("Glint", ball(tuple(st1 + V_((-s * 0.02, 0.09, 0.09))), (0.016,) * 3, 6, 3), "Belly")
        P.obj("BrowSpine", cone(V_((s * 0.13, 0.62, 0.17)), V_((s * 0.38, 0.66, 0.36)), 0.035, 5), "Base", 0, False)   # rising outward: the scowl
        P.obj("Antenna", pipe(bez(V_((s * 0.06, 0.62, 0.1)), V_((s * 0.1, 0.8, 0.16)), V_((s * 0.25, 0.95, 0.2)), V_((s * 0.42, 1.05, 0.16)), 8),
                              [0.014, 0.012, 0.011, 0.01, 0.008, 0.007, 0.006, 0.004, 0.0], 5), "Accent")
    pc = V_((-0.25, 0.79, 0.43))   # the patch over the left eye, its strap round the stalk
    P.obj("Patch", oriented_ball(pc, (0.075, 0.03, 0.08), V_((1, 0, 0)), V_((0, 1, 0)), V_((0, 0, 1)), 12, 5), "Dark")
    P.obj("PatchStrap", torus(0.095, 0.012, 0.0, 16, 4), "Dark"); P.parts[-1].data.transform(Matrix.Translation(V_((-0.25, 0.72, 0.42))) @ Matrix.Rotation(math.radians(70), 4, "X"))
    for k in range(3):
        for s in (1, -1):
            P.obj("Maxilliped", oriented_ball(V_((s * (0.06 + 0.02 * k), 0.6 - 0.02 * k, -0.02 - 0.05 * k)), (0.06, 0.012, 0.05), V_((1, 0, 0)), V_((0, 1, 0)), V_((0, 0, 1)), 8, 3), "Belly")
    # ---- the claws: the spiny arm, the wrist and its great spine, the swollen palm, the fingers gripping a ship's cannon
    muzzle = None
    for s in (1, -1):
        sh = V_((s * 0.7, 0.35, -0.02)); me = V_((s * 1.15, 0.62, 0.08)); ca = V_((s * 1.1, 0.92, 0.14))
        P.obj("Arm", pipe([sh, (sh + me) * 0.5 + V_((0, 0, 0.04)), me], [0.12, 0.14, 0.12], 12), "Base")
        for k in range(3):
            q = sh + (me - sh) * (0.25 + 0.25 * k) + V_((0, 0, 0.12))
            P.obj("ArmSpine", cone(q, q + V_((s * 0.02, 0.04, 0.09)), 0.025, 4), "Dark", 0, False)
        P.obj("Wrist", ball(tuple(ca), (0.14, 0.15, 0.13), 12, 6), "Base")
        P.obj("WristSpine", cone(ca + V_((-s * 0.08, 0.04, 0.06)), ca + V_((-s * 0.22, 0.14, 0.1)), 0.04, 5), "Dark", 0, False)
        pa = ca + V_((-s * 0.06, 0.32, 0.02))
        P.obj("Palm", oriented_ball(pa, (0.24, 0.36, 0.22), V_((1, 0, 0)), V_((0, 1, 0)), V_((0, 0, 1)), 16, 8), lambda c, n: "Belly" if n.z < -0.4 else "Base")
        for k in range(4):   # granule rows on the palm
            for j in range(3):
                P.obj("Granule", ball(tuple(pa + V_((s * (0.12 + 0.04 * j), -0.15 + 0.1 * k, 0.12 - 0.04 * j))), (0.022,) * 3, 6, 3), "Accent")
        cb = pa + V_((0, 0.18, 0.0))
        m = ship_cannon(P, cb, (0, 1, 0.04), 0.95, 0.15)
        if s > 0: muzzle = m
        for q, z0 in ((1, 0.17), (-1, -0.17)):   # the fixed finger under the barrel, the movable one over it, both closed round it
            f0 = pa + V_((0, 0.3, z0 * 0.7)); f1 = f0 + V_((0, 0.3, -q * 0.02)); f2 = f1 + V_((0, 0.12, -q * 0.12))
            P.obj("Finger", pipe([f0, f1, f2], [0.08, 0.065, 0.02], 10), lambda c, n, f2=f2: "Dark" if (c - f2).length < 0.1 else "Base")
            for k in range(3):
                t0 = f0 + (f1 - f0) * (0.2 + 0.3 * k)
                P.obj("FingerTooth", cone(t0, t0 - V_((0, 0, q * 0.06)), 0.018, 4), "Belly", 0, False)
    # ---- eight walking legs hanging and paddling one after another
    k_ = 0
    for s in (1, -1):
        for j in range(4):
            y0 = 0.25 - 0.2 * j; r = ring_at(y0)
            b = V_((s * r[1] * 0.82, y0, -0.02)); hub = tuple(b)
            k1 = b + V_((s * 0.42, -0.05 * j, 0.14)); k2 = k1 + V_((s * 0.22, -0.04, -0.34)); tip = k2 + V_((s * 0.04, -0.03, -0.36))
            name = "Sway" + ("FootR" if s > 0 else "FootL") + str(j)
            P.part(name, pipe([b, k1], [0.08, 0.065], 10), "Base", hub)
            P.part(name, ball(tuple(k1), (0.07,) * 3, 8, 4), "Accent", hub)
            P.part(name, pipe([k1, k2], [0.06, 0.05], 10), "Base", hub)
            P.part(name, ball(tuple(k2), (0.055,) * 3, 8, 4), "Accent", hub)
            P.part(name, pipe([k2, tip], [0.045, 0.0], 8), lambda c, n, tip=tip: "Dark" if (c - tip).length < 0.12 else "Base", hub)
            for t in (0.3, 0.65):
                q = b + (k1 - b) * t + V_((0, 0, 0.06))
                P.part(name, cone(q, q + V_((s * 0.02, 0, 0.07)), 0.018, 4), "Dark", hub)
    # ---- the pufferfish balloons, roped round the middle and tied to the shell
    for k, (pc_, R, tie) in enumerate(((V_((0, -0.35, 2.3)), 0.55, V_((0, -0.3, 0.38))), (V_((-0.9, 0.25, 1.85)), 0.46, V_((-0.55, 0.2, 0.36))),
                                        (V_((0.9, 0.25, 1.85)), 0.46, V_((0.55, 0.2, 0.36))))):
        puffer(P, pc_, R, "Puffer%d" % k, "FlapFin%d" % k)
        rg = torus(R * 0.8, 0.022, 0.0, 32, 5)   # the rope round the belly, under the eyes
        P.obj("Rope", xf(rg, Matrix.Rotation(math.radians(-14), 3, "X"), tuple(pc_ - V_((0, 0, R * 0.58)))), "Belly")
        low = pc_ + (tie - pc_).normalized() * R * 0.98
        P.obj("Rope", pipe(bez(low, low + (tie - low) * 0.3 + V_((0, 0, -0.05)), tie + V_((0, 0, 0.25)), tie, 6), [0.022] * 7, 5), "Belly")
        P.obj("Knot", ball(tuple(tie), (0.05,) * 3, 8, 4), "Belly")
    P.part("Muzzle", ball(tuple(muzzle), (0.05, 0.03, 0.05), 8, 4), "Lamp", tuple(muzzle))
    return P


def jolly_roger(P, top, length, height, along, name="ClothFlag"):
    """a black flag flown from top, streaming along `along`, with the white skull and crossbones on both faces."""
    top, along = V_(top), V_(along).normalized(); dn = V_((0, 0, -1))
    nrm = along.cross(dn).normalized()
    quads = []
    for i in range(8):
        for j in range(4):
            def pt(u, v):
                return top + along * u * length + dn * v * height + nrm * 0.06 * math.sin(u * 7.0) * u
            u0, u1, v0, v1 = i / 8, (i + 1) / 8, j / 4, (j + 1) / 4
            quads.append([tuple(pt(u0, v0)), tuple(pt(u1, v0)), tuple(pt(u1, v1)), tuple(pt(u0, v1))])
    P.part(name, st_cloth(quads, 0.012), "Dark", (0, 0, 0), 0, True)
    mid = top + along * length * 0.5 + dn * height * 0.42 + nrm * 0.06 * math.sin(3.5) * 0.5
    for side in (1, -1):
        o = nrm * side * 0.014
        P.part(name, oriented_ball(mid + o + dn * height * 0.06, (height * 0.14, height * 0.13, 0.004), along, -dn, nrm, 12, 3), "Belly", (0, 0, 0), 0, True)
        for q in (1, -1):
            d = (along * q + dn).normalized()
            P.part(name, pipe([mid + o - d * height * 0.26, mid + o + d * height * 0.26], [height * 0.03] * 2, 4), "Belly", (0, 0, 0), 0, True)


def T2_mimic():
    """The TREASURE MIMIC (2026-10-14, remade like the alien / autumn / west bosses): a real pirate's sea chest come alive. Oak planks with
    dark seams, three iron straps round it riveted at even steps, brass caps on the corners, an iron ring at each end and the hasp broken,
    its padlock hanging open. The barrel lid is its upper jaw and the box its lower one, both lined with fangs, the lid snapping (SwayLid);
    inside, red velvet gone dark, a heap of glowing gold, and three eyes burning in the shadow under the lid, a big one and two small, each
    with a slit pupil; a long tongue lolls out over the front with doubloons stuck to it.
    It SAILS THE SKY: a ship's broken mast is lashed to its back with iron brackets, a yard across the top and a boom below, a square sail
    of patched canvas full of wind between them, shrouds down to the chest's corners, a rudder on its back, and the Jolly Roger flying from
    the masthead."""
    P = Boss("mimic", AB_pal(Base=((0.44, 0.25, 0.11), 0.35), Belly=((0.93, 0.87, 0.72), 0.3), Accent=((0.6, 0.07, 0.12), 0.5),
                             Trim=((0.98, 0.76, 0.22), 0.8), Glass=((0.08, 0.62, 0.42), 0.9), Dark=((0.06, 0.06, 0.07), 0.5),
                             Glow=((1.0, 0.82, 0.15), 0.5), Metal=((0.26, 0.26, 0.29), 0.7), Lamp=((1.0, 0.72, 0.25), 0.8)))
    glow_strength(P, 2.0)
    W, D, H = 0.78, 0.5, 0.36        # half width, half depth, half height of the box; its top at z = H
    # ---- the box: planks with dark seams between them, iron straps, brass corners
    for k in range(4):               # four planks up each face, a dark seam between each
        z0 = -H + 2 * H * k / 4; z1 = -H + 2 * H * (k + 1) / 4
        P.obj("Plank", box((0, 0, (z0 + z1) / 2), (2 * W, 2 * D, (z1 - z0) - 0.018)), "Base", 0, False)
    P.obj("Seams", box((0, 0, 0), (2 * W - 0.01, 2 * D - 0.01, 2 * H)), "Dark", 0, False)
    P.obj("Floor", box((0, 0, -H - 0.03), (2 * W + 0.04, 2 * D + 0.04, 0.06)), "Base", 0, False)
    for x in (-W * 0.62, 0.0, W * 0.62):     # three iron straps, riveted
        P.obj("Strap", box((x, 0, -0.02), (0.1, 2 * D + 0.035, 2 * H + 0.04)), "Dark", 0, False)
        for z in (-H + 0.1, 0.0, H - 0.1):
            for y in (D + 0.02, -D - 0.02):
                P.obj("Rivet", ball((x, y, z), (0.022, 0.012, 0.022), 6, 3), "Metal")
    for sx in (1, -1):
        for sy in (1, -1):
            for sz in (1, -1):
                P.obj("Corner", box((sx * (W - 0.05), sy * (D - 0.05), sz * (H - 0.05) - (0.0 if sz > 0 else 0.03)), (0.14, 0.14, 0.14)), "Trim", 0, False)
        P.obj("Handle", xf(torus(0.11, 0.022, 0.0, 16, 5), Matrix.Rotation(math.pi / 2, 3, "Y"), (sx * (W + 0.06), 0, 0.04)), "Metal")
    # ---- the lower jaw: the front lip lined with fangs, the dark mouth, the velvet, the gold, the tongue
    for k in range(9):
        x = -W * 0.85 + 2 * W * 0.85 * k / 8; L = 0.18 if k % 2 == 0 else 0.11
        P.obj("Fang", cone((x, D - 0.05, H - 0.01), (x, D - 0.02, H + L), 0.05 if k % 2 == 0 else 0.035, 6), "Belly", 0, False)
    P.obj("Mouth", box((0, 0, H - 0.02), (2 * W - 0.1, 2 * D - 0.1, 0.03)), "Accent", 0, False)
    gold_heap(P, (0, -0.05, H - 0.04), W * 0.75, D * 0.7, 0.18, 26, random.Random(11))
    tg = bez(V_((0, 0.15, H + 0.02)), V_((0, 0.5, H + 0.1)), V_((0, 0.75, H - 0.05)), V_((0.05, 0.85, -0.25)), 8)
    P.obj("Tongue", flat_pipe(tg, [0.13, 0.14, 0.14, 0.13, 0.12, 0.11, 0.09, 0.07, 0.04], V_((0, 0, 1)), 0.55, 10), "Accent")
    for k in (3, 6):
        P.obj("Doubloon", coin(tg[k] + V_((0.02, 0, 0.035)), 0.06, 0.02, Matrix.Rotation(math.radians(20), 3, "X")), "Trim", 0, False)
    # the hasp broken off the front, the padlock hanging open
    P.obj("Hasp", box((0, D + 0.03, H - 0.12), (0.12, 0.02, 0.16)), "Metal", 0, False)
    lk = V_((0.22, D + 0.06, -0.12))
    P.obj("Padlock", oriented_ball(lk, (0.09, 0.04, 0.1), V_((1, 0, 0)), V_((0, 1, 0)), V_((0, 0, 1)), 12, 6), "Trim")
    P.obj("Shackle", pipe(bez(lk + V_((-0.05, 0, 0.08)), lk + V_((-0.06, 0, 0.18)), lk + V_((0.04, 0, 0.2)), lk + V_((0.1, 0, 0.12)), 5), [0.016] * 6, 5), "Metal")
    P.obj("Keyhole", oriented_ball(lk + V_((0, 0.04, -0.01)), (0.012, 0.005, 0.025), V_((1, 0, 0)), V_((0, 1, 0)), V_((0, 0, 1)), 6, 3), "Dark")
    # ---- the lid: the upper jaw, a barrel top on its hinge at the back, fangs underneath, the eyes in its shadow; it snaps (SwayLid)
    hz, hy = H, -D; hub = (0, hy, hz)
    LR = Matrix.Rotation(math.radians(50), 3, "X")
    def Ld(bm):
        for v in bm.verts: v.co = LR @ (v.co - V_(hub)) + V_(hub)
        return bm
    lid = lathe([(0.0, -W), (D, -W), (D, W), (0.0, W)], 28, "x")
    for v in lid.verts:   # half a barrel: the lower half flattened onto the hinge line
        if v.co.z < 0: v.co.z = 0.0
        v.co.z = v.co.z * 0.75 + hz; v.co.y = v.co.y
    P.part("SwayLid", Ld(lid), lambda c, n: "Accent" if n.z < -0.5 else "Base", hub)
    for x in (-W * 0.62, 0.0, W * 0.62):
        arc = [V_((x, math.cos(a) * (D + 0.02), hz + math.sin(a) * (D + 0.02) * 0.75)) for a in [math.pi * k / 16 for k in range(17)]]
        P.part("SwayLid", Ld(pipe(arc, [0.05] * 17, 6, False)), "Dark", hub)
    for k in range(9):
        x = -W * 0.85 + 2 * W * 0.85 * k / 8; L = 0.2 if k % 2 else 0.13
        P.part("SwayLid", Ld(cone((x, D - 0.05, hz + 0.01), (x, D - 0.02, hz - L), 0.05 if k % 2 else 0.036, 6)), "Belly", hub)
    for (ex, ez, er) in ((0.0, 0.0, 0.17), (-0.4, 0.0, 0.11), (0.4, 0.0, 0.11)):   # three eyes in the shadow under the lid
        e = V_((ex, D * 0.42, hz - er * 0.35 + ez * 0.2))   # bulging out of the roof of the mouth
        P.hint = "matte"; P.part("SwayLid", Ld(ball(tuple(e - V_((0, 0.03, 0))), (er * 1.25, er * 0.5, er * 1.05), 12, 6)), "Dark", hub)
        P.hint = None; P.part("SwayLid", Ld(ball(tuple(e), (er, er * 0.45, er * 0.85), 12, 6)), "Glow", hub)
        P.hint = "eye"; P.part("SwayLid", Ld(ball(tuple(e + V_((0, er * 0.4, 0))), (er * 0.18, er * 0.1, er * 0.7), 8, 4)), "Dark", hub)
        P.hint = None
    for sx in (1, -1):
        P.part("SwayLid", Ld(box((sx * (W - 0.05), 0.0, hz + D * 0.62), (0.14, 2 * D * 0.9, 0.08))), "Trim", hub)

    # ---- the rig: a broken mast lashed to its back, the yard and boom, the sail full of wind, shrouds, the Jolly Roger, a rudder
    MY = -D - 0.12; MB, MT = -H - 0.1, 3.05
    P.obj("Mast", pipe([V_((0, MY, MB)), V_((0, MY, MT))], [0.085, 0.065], 12), "Base")
    for z in (-0.1, 0.3, 1.4, 2.6):
        P.obj("MastBand", pipe([V_((0, MY, z - 0.03)), V_((0, MY, z + 0.03))], [0.1, 0.1], 12), "Dark")
    for z in (-0.15, 0.2):   # the iron brackets lashing it to the chest's back
        P.obj("Bracket", box((0, -D - 0.06, z), (0.3, 0.14, 0.06)), "Dark", 0, False)
    P.obj("Masthead", ball((0, MY, MT + 0.04), (0.09,) * 3, 8, 4), "Trim")
    YZ, BZ_, YW, BW = 2.55, 0.95, 1.3, 1.15
    P.obj("Yard", pipe([V_((-YW, MY + 0.08, YZ)), V_((YW, MY + 0.08, YZ))], [0.05, 0.05], 10), "Base")
    P.obj("Boom", pipe([V_((-BW, MY + 0.08, BZ_)), V_((BW, MY + 0.08, BZ_))], [0.045, 0.045], 10), "Base")
    quads = []; patch = []
    NU, NV = 12, 10
    def sail_pt(u, v):   # u across -1..1, v from the yard (0) down to the boom (1); bellied forward, most in the middle
        x = (YW + (BW - YW) * v) * u * 0.96; z = YZ + (BZ_ - YZ) * v
        bel = 0.55 * (1 - u * u) * math.sin(math.pi * min(1.0, v * 1.05)) ** 0.8
        return V_((x, MY + 0.1 + bel, z))
    for i in range(NU):
        for j in range(NV):
            u0, u1 = -1 + 2 * i / NU, -1 + 2 * (i + 1) / NU; v0, v1 = j / NV, (j + 1) / NV
            q = [tuple(sail_pt(u0, v0)), tuple(sail_pt(u1, v0)), tuple(sail_pt(u1, v1)), tuple(sail_pt(u0, v1))]
            (patch if (i, j) in ((2, 3), (8, 6), (5, 8)) else quads).append(q)   # three sewn patches
    P.part("ClothSail", st_cloth(quads, 0.014), "Belly", (0, 0, 0), 0, True)
    P.part("ClothSailPatch", st_cloth(patch, 0.018), "Base", (0, 0, 0), 0, True)
    for j in range(1, 4):   # the reef points: short ties in even rows across the sail
        for i in range(-5, 6):
            q = sail_pt(i / 5.5, j * 0.12)
            P.obj("ReefPoint", pipe([q + V_((0, 0.01, 0)), q + V_((0, 0.03, -0.07))], [0.008, 0.006], 4), "Base")
    for sx in (1, -1):   # the shrouds from the masthead to the chest's back corners, the sheets from the boom ends
        P.obj("Shroud", pipe([V_((0, MY, MT - 0.05)), V_((sx * (W - 0.05), -D, H))], [0.014] * 2, 4), "Belly")
        P.obj("Sheet", pipe([V_((sx * BW, MY + 0.08, BZ_)), V_((sx * (W - 0.1), D - 0.1, H + 0.02))], [0.012] * 2, 4), "Belly")
    jolly_roger(P, V_((0, MY, MT - 0.02)), 0.75, 0.48, V_((0.85, 0.2, 0.0)))
    P.obj("Rudder", box((0, -D - 0.28, -0.05), (0.06, 0.34, 0.6)), "Base", 0, False)
    P.obj("Tiller", pipe([V_((0, -D - 0.28, 0.27)), V_((0, -D - 0.62, 0.42))], [0.025, 0.02], 6), "Base")
    mz = (0, D * 0.6, hz + 0.06)
    P.part("Muzzle", ball(mz, (0.05, 0.03, 0.05), 8, 4), "Lamp", mz)
    return P


def small_skull(P, c, look, k, bandana=False, name="Skull"):
    """a skeleton's skull at c looking along `look`: the vault, the face, two dark sockets with a green spark in each, the nasal hole, a
    grin of teeth and the jaw; a red bandana tied over the vault when asked."""
    c = V_(c); f = V_(look).normalized(); x, y, z = sq_axes(f, (0, 0, 1))   # x across, y up, z = f forward
    def at(a, b, d): return c + x * a * k + y * b * k + f * d * k
    def ob(p, r): return oriented_ball(p, tuple(v * k for v in r), x, y, f, 12, 6)
    P.obj(name, ob(at(0, 0.02, -0.02), (0.11, 0.11, 0.12)), "Belly")
    P.obj(name, ob(at(0, -0.05, 0.05), (0.085, 0.08, 0.08)), "Belly")
    for s in (1, -1):
        P.obj(name + "Socket", ob(at(s * 0.042, -0.02, 0.11), (0.032, 0.03, 0.02)), "Dark")
        P.obj(name + "Spark", ob(at(s * 0.042, -0.02, 0.122), (0.012, 0.012, 0.008)), "Glow")
        P.obj(name + "Cheek", ob(at(s * 0.07, -0.07, 0.07), (0.025, 0.02, 0.025)), "Belly")
    P.obj(name + "Nose", ob(at(0, -0.075, 0.125), (0.014, 0.022, 0.01)), "Dark")
    P.obj(name + "Grin", ob(at(0, -0.12, 0.1), (0.05, 0.016, 0.02)), "Dark")
    for j in range(6):
        P.obj(name + "Tooth", ob(at(-0.035 + 0.014 * j, -0.115, 0.115 - 0.004 * abs(j - 2.5)), (0.006, 0.012, 0.005)), "Belly")
    P.obj(name + "Jaw", ob(at(0, -0.16, 0.06), (0.06, 0.025, 0.05)), "Belly")
    if bandana:
        P.obj(name + "Bandana", ob(at(0, 0.06, -0.02), (0.118, 0.085, 0.13)), "Accent")
        P.obj(name + "Knot", ob(at(0, 0.03, -0.14), (0.03, 0.03, 0.03)), "Accent")


def T2_ghost():
    """The GHOST CAPTAIN (2026-10-14, remade like the alien / autumn / west bosses): the drowned captain is ROWED THROUGH THE SKY by his dead
    crew. His boat is a real ship's longboat, clinker-built - the planks overlapping in strakes, ribs inside at even steps, two thwarts,
    a gunwale rail, the stem and the sternpost - rotten and wet, a hole stove in its side, barnacles along the waterline and weed hanging from
    the keel, green ghost-fire pooled in the bilge, a ghost-lantern hung out from the stem and a torn red pennant at the stern. Four skeletons
    row it, two to a thwart, facing aft as rowers do but each with his skull turned back over his shoulder to grin at you; their four oars
    sweep through the air one after another (SwayOar*), green ghost-fire churning off every blade where there is no water.
    The captain stands in the bow: a gaunt ghost with hollow burning eyes, his mouth open in a wail, a beard of black sea-weed, a black
    tricorn edged in gold, a long black coat with gold buttons and a red sash whose hem tears into ghostly wisps streaming back over the boat;
    his cutlass is raised at you and his lantern of ghost-fire held out - his shots leave from it."""
    P = Boss("ghost", AB_pal(Base=((0.5, 0.86, 0.78), 0.4), Belly=((0.9, 0.87, 0.76), 0.35), Accent=((0.62, 0.07, 0.06), 0.45),
                             Trim=((0.86, 0.68, 0.3), 0.8), Glass=((0.3, 0.21, 0.12), 0.6), Dark=((0.05, 0.06, 0.06), 0.45),
                             Glow=((0.3, 1.0, 0.5), 0.5), Metal=((0.72, 0.75, 0.8), 0.9), Lamp=((0.75, 1.0, 0.8), 0.8)))
    glow_strength(P, 1.8)
    # ---- the hull: a lofted shell cut along the sheer line and given its thickness
    HR = [(-1.3, 0.32, 0.3), (-1.0, 0.48, 0.4), (-0.5, 0.55, 0.45), (0.0, 0.56, 0.46), (0.5, 0.52, 0.44), (0.95, 0.38, 0.38), (1.25, 0.16, 0.3), (1.38, 0.03, 0.2)]
    def hr(y):
        for r0, r1 in zip(HR, HR[1:]):
            if y <= r1[0]:
                f = max(0.0, (y - r0[0]) / (r1[0] - r0[0])); return r0[1] + (r1[1] - r0[1]) * f, r0[2] + (r1[2] - r0[2]) * f
        return HR[-1][1], HR[-1][2]
    def sheer(y): return 0.04 + 0.1 * (y / 1.3) ** 2 + (0.1 * (y - 1.0) / 0.38 if y > 1.0 else 0.0)
    rings = []
    for k in range(29):
        y = -1.3 + 2.68 * k / 28; a, b = hr(y); rings.append((y, a, b, 0, 0.0))
    hull_bm = loft(rings, 32, cs=True, ce=True)
    bmesh.ops.delete(hull_bm, geom=[v for v in hull_bm.verts if v.co.z > sheer(v.co.y) + 1e-4], context="VERTS")
    bmesh.ops.solidify(hull_bm, geom=hull_bm.faces[:], thickness=0.035)
    P.obj("Hull", hull_bm, "Glass", 0)
    def side_pt(y, f, s, out=0.0):
        a, b = hr(y); z = -b * f; x = a * math.sqrt(max(0.0, 1 - f * f))
        return V_((s * (x + out), y, z))
    for s in (1, -1):
        for f in (0.2, 0.42, 0.62, 0.8):   # the strakes: each plank's lower edge overlapping the next, a dark line along the hull
            P.obj("Strake", pipe([side_pt(-1.25 + 2.55 * t / 20, f, s, 0.012) for t in range(21)], [0.012] * 21, 4), "Dark")
        rail = [side_pt(y, 0.0, s, 0.01) + V_((0, 0, sheer(y))) for y in [-1.28 + 2.6 * t / 24 for t in range(25)]]
        P.obj("Gunwale", pipe(rail, [0.035] * 25, 6), "Glass")
    for k in range(9):   # the ribs inside, at even steps
        y = -1.05 + 2.1 * k / 8; a, b = hr(y)
        rib = [V_((math.sin(t) * (a - 0.03), y, -math.cos(t) * (b - 0.03))) for t in [math.radians(-90 + 180 * j / 12) for j in range(13)]]
        rib = [p + V_((0, 0, min(0.0, sheer(y) - 0.03) if abs(p.z) < 0.01 else 0.0)) for p in rib]
        P.obj("Rib", pipe(rib, [0.022] * 13, 5), "Glass")
    P.obj("Keel", pipe([V_((0, -1.32, -0.3)), V_((0, -0.5, -0.47)), V_((0, 0.5, -0.46)), V_((0, 1.2, -0.32))], [0.04] * 4, 6), "Glass")
    P.obj("Stem", pipe(bez(V_((0, 1.2, -0.32)), V_((0, 1.42, -0.18)), V_((0, 1.46, 0.12)), V_((0, 1.5, 0.36)), 8), [0.05] * 9, 8), "Glass")
    P.obj("Sternpost", pipe([V_((0, -1.32, -0.3)), V_((0, -1.38, 0.0)), V_((0, -1.4, 0.24))], [0.045] * 3, 8), "Glass")
    for ty in (0.25, -0.35):
        P.obj("Thwart", box((0, ty, 0.0), (1.06, 0.16, 0.05)), "Glass", 0, False)
    P.obj("Foredeck", box((0, 0.98, 0.06), (0.62, 0.42, 0.05)), "Glass", 0, False)
    # their plunder on the foredeck: a small iron-bound chest, its lid up on a heap of gold
    P.obj("LootChest", box((0, 1.0, 0.2), (0.36, 0.24, 0.2)), "Glass", 0, False)
    for x in (-0.11, 0.11): P.obj("LootStrap", box((x, 1.0, 0.2), (0.04, 0.25, 0.21)), "Dark", 0, False)
    P.obj("LootLid", xf(box((0, 0, 0), (0.36, 0.05, 0.22)), Matrix.Rotation(math.radians(-20), 3, "X"), (0, 0.87, 0.38)), "Glass", 0, False)
    gold_heap(P, (0, 1.01, 0.3), 0.15, 0.1, 0.08, 9, random.Random(5), name="Loot")
    P.obj("Bilge", ball((0, -0.05, -0.28), (0.36, 1.0, 0.04), 20, 4), "Glow")   # ghost-fire pooled in the bottom
    hole = side_pt(-0.75, 0.45, 1, 0.015)
    P.obj("Hole", oriented_ball(hole, (0.02, 0.17, 0.11), V_((1, 0, 0)), V_((0, 1, 0)), V_((0, 0, 1)), 12, 5), "Dark")
    for j in range(5):
        a = 2 * math.pi * j / 5
        p0 = hole + V_((0.0, math.cos(a) * 0.15, math.sin(a) * 0.1))
        P.obj("Splinter", cone(p0, p0 + V_((0.06, math.cos(a) * 0.08, math.sin(a) * 0.05)), 0.018, 4), "Glass", 0, False)
    for s in (1, -1):   # barnacles along the waterline at even steps
        for j in range(7):
            y = -1.0 + 0.32 * j; q = side_pt(y, 0.58 + 0.08 * (j % 2), s, 0.0)
            nrm = V_((s, 0, -0.3)).normalized()
            P.obj("Barnacle", xf(lathe([(0.05, 0.0), (0.035, 0.06), (0.018, 0.065), (0.0, 0.04)], 8, "z"), Matrix(sq_axes(nrm)).transposed(), tuple(q)), "Belly")
    for j in range(7):   # weed hanging from the keel
        y = -1.05 + 0.33 * j; top = V_((0, y, -0.46 + 0.05 * abs(y) ** 2))
        wd = [top + V_((0.05 * math.sin(i * 1.3 + j), -0.04 * i, -0.09 * i)) for i in range(7)]
        P.obj("Weed", flat_pipe(wd, [0.03, 0.035, 0.035, 0.03, 0.025, 0.015, 0.0], V_((0, 1, 0)), 0.6, 6), "Dark")
    # the ghost-lantern hung out from the stem, the torn pennant at the stern
    lp = [V_((0, 1.48, 0.3)), V_((0, 1.62, 0.5)), V_((0, 1.8, 0.56))]
    P.obj("LanternPole", pipe(lp, [0.025] * 3, 6), "Glass")
    L0 = V_((0, 1.82, 0.36))
    P.obj("LanternChain", pipe([lp[-1], L0 + V_((0, 0, 0.12))], [0.008] * 2, 4), "Metal")
    P.obj("LanternCap", lathe([(0.0, 0.18), (0.09, 0.1), (0.08, 0.08)], 10, "z", tuple(L0)), "Trim")
    P.obj("LanternGlass", lathe([(0.075, 0.08), (0.08, -0.06), (0.0, -0.08)], 10, "z", tuple(L0)), "Glow")
    for j in range(4):
        a = 2 * math.pi * (j + 0.5) / 4
        P.obj("LanternBar", pipe([L0 + V_((math.cos(a) * 0.08, math.sin(a) * 0.08, 0.08)), L0 + V_((math.cos(a) * 0.08, math.sin(a) * 0.08, -0.07))], [0.01] * 2, 4), "Trim")
    P.obj("PennantPole", pipe([V_((0, -1.42, 0.2)), V_((0, -1.46, 0.85))], [0.02] * 2, 5), "Glass")
    pq = []
    for i in range(6):
        u0, u1 = i / 6, (i + 1) / 6
        def pp(u, v): return V_((0.05 * math.sin(u * 6), -1.46 - 0.55 * u, 0.82 - 0.16 * v * (1 - u * 0.7) - 0.05 * u))
        pq.append([tuple(pp(u0, 0)), tuple(pp(u1, 0)), tuple(pp(u1, 1)), tuple(pp(u0, 1))])
    P.part("ClothPennant", st_cloth(pq, 0.012), "Accent", (0, 0, 0), 0, True)

    # ---- the skeleton crew: two to a thwart, facing aft, skulls turned back to grin at you; the oars sweep (each its own Sway part)
    n_oar = 0
    for ty in (0.25, -0.35):
        for s in (1, -1):
            seat = V_((s * 0.24, ty, 0.06)); O = V_((s * 0.56, ty - 0.12, sheer(ty - 0.12) + 0.04)); H = V_((s * 0.14, ty - 0.42, 0.34))
            d = (O - H).normalized(); B = O + d * 1.55
            P.obj("Pelvis", ball(tuple(seat + V_((0, 0, 0.06))), (0.11, 0.08, 0.06), 10, 5), "Belly")
            sp_ = [seat + V_((0, 0.02 * t, 0.08 + 0.09 * t)) for t in range(7)]
            P.obj("Spine", pipe(sp_, [0.025] * 7, 6), "Belly")
            for t in range(1, 7): P.obj("Vertebra", ball(tuple(sp_[t]), (0.032, 0.03, 0.022), 6, 3), "Belly")
            for r in range(5):   # the ribs curving round from the spine to the breastbone in front (aft, the way he faces)
                h = 0.32 + 0.06 * r; w = 0.12 - 0.008 * r
                for q in (1, -1):
                    rib = [seat + V_((q * w * math.sin(t), -0.02 - 0.1 * (1 - math.cos(t)), h - 0.04 * math.sin(t))) for t in [math.radians(a) for a in range(0, 181, 30)]]
                    P.obj("Rib", pipe(rib, [0.012] * len(rib), 4), "Belly")
            P.obj("Sternum", pipe([seat + V_((0, -0.22, 0.34)), seat + V_((0, -0.22, 0.56))], [0.014] * 2, 4), "Belly")
            neck = seat + V_((0, 0.03, 0.66))
            small_skull(P, neck + V_((0, 0.0, 0.13)), V_((s * 0.45, 0.88, -0.05)), 1.25, bandana=(n_oar % 2 == 0), name="CrewSkull")
            for q in (1, -1):   # the upper arms down to the elbow (static); forearms and hands ride on the oar
                shoulder = seat + V_((q * 0.13, -0.02, 0.58)); elbow = seat + V_((q * 0.14, -0.16, 0.42))
                P.obj("Humerus", pipe([shoulder, elbow], [0.02, 0.018], 5), "Belly")
                P.obj("Shoulder", ball(tuple(shoulder), (0.03,) * 3, 6, 3), "Belly")
                knee = seat + V_((q * 0.09, -0.3, 0.2)); foot = seat + V_((q * 0.1, -0.36, -0.22))
                P.obj("Femur", pipe([seat + V_((q * 0.08, 0, 0.06)), knee], [0.024, 0.02], 5), "Belly")
                P.obj("Tibia", pipe([knee, foot], [0.02, 0.016], 5), "Belly")
                P.obj("Foot", oriented_ball(foot + V_((0, -0.04, -0.01)), (0.03, 0.06, 0.02), V_((1, 0, 0)), V_((0, 1, 0)), V_((0, 0, 1)), 6, 3), "Belly")
            name = "SwayOar%d" % n_oar; hub = tuple(O)
            P.part(name, pipe([H - d * 0.12, B - d * 0.42], [0.025, 0.028], 8), "Glass", hub)
            P.part(name, flat_pipe([B - d * 0.45, B - d * 0.2, B], [0.03, 0.09, 0.07], V_((0, -1, 0.3)), 0.82, 8), "Glass", hub)
            for q in (1, -1):
                hand = H + d * (0.0 if q > 0 else -0.1)
                elbow = seat + V_((q * 0.14, -0.16, 0.42))
                P.part(name, pipe([elbow, hand], [0.016, 0.015], 5), "Belly", hub)
                P.part(name, ball(tuple(hand), (0.03,) * 3, 6, 3), "Belly", hub)
            for j in range(3):   # ghost-fire churning off the blade
                a = 2 * math.pi * j / 3
                P.part(name, flame(B + V_((0, 0, 0.04 * math.cos(a))), V_((s * 0.15 * math.sin(a), -1.0, 0.25)), 0.42 - 0.08 * j, 0.06, V_((0, 0, 1))), "Glow", hub)
            P.obj("Thole", pipe([O + V_((0, 0.05, -0.04)), O + V_((0, 0.05, 0.08))], [0.014] * 2, 4), "Glass")
            P.obj("Thole", pipe([O + V_((0, -0.05, -0.04)), O + V_((0, -0.05, 0.08))], [0.014] * 2, 4), "Glass")
            n_oar += 1

    # ---- the captain in the stern sheets, where an officer stands to command the rowers - they face him, he faces you over their heads
    P.obj("SternDeck", box((0, -0.98, 0.08), (0.7, 0.5, 0.05)), "Glass", 0, False)
    C0 = V_((0, -0.98, 0.1))
    coat = lathe([(0.0, 1.2), (0.25, 1.18), (0.28, 1.0), (0.27, 0.75), (0.33, 0.45), (0.4, 0.2), (0.44, 0.0)], 24, "z")
    for v in coat.verts: v.co.y *= 0.78
    P.obj("Coat", xf(coat, None, tuple(C0)), lambda c, n: "Trim" if abs(c.x) < 0.035 and c.y > C0.y + 0.15 else "Dark", 0)
    for j in range(4):
        P.obj("Button", ball(tuple(C0 + V_((0.05, 0.22 - 0.01 * j, 0.98 - 0.13 * j))), (0.025, 0.015, 0.025), 6, 3), "Trim")
    P.obj("Sash", xf(torus(0.29, 0.04, 0.0, 24, 5), Matrix.Scale(1.0, 3), tuple(C0 + V_((0, 0, 0.55)))), "Accent")
    for v in P.parts[-1].data.vertices: v.co.y = C0.y + (v.co.y - C0.y) * 0.8
    for j in range(10):   # the hem tears into wisps streaming back off the stern
        a = 2 * math.pi * j / 10
        b0 = C0 + V_((math.sin(a) * 0.42, math.cos(a) * 0.33, 0.02))
        P.obj("Wisp", flame(b0, V_((math.sin(a) * 0.5, -1.0, -0.2)), 0.6 + 0.14 * (j % 2), 0.08, V_((0, 0, 1))), "Base")
    for s in (1, -1):
        P.obj("Epaulette", ball(tuple(C0 + V_((s * 0.25, 0.0, 1.18))), (0.13, 0.11, 0.04), 10, 5), "Trim")
        for j in range(4): P.obj("Fringe", pipe([C0 + V_((s * (0.17 + 0.05 * j), 0.06, 1.15)), C0 + V_((s * (0.18 + 0.05 * j), 0.07, 1.06))], [0.012, 0.008], 4), "Trim")
    # the head: gaunt, hollow-eyed, wailing; a weed beard; long wisps of hair behind
    HC = C0 + V_((0, 0.03, 1.44))
    P.obj("Head", loft([(-0.14, 0.13, 0.15, 0, 0.04), (-0.02, 0.17, 0.18, 0, 0.03), (0.1, 0.15, 0.16, 0, 0.0), (0.17, 0.11, 0.13, 0, -0.04), (0.22, 0.05, 0.08, 0, -0.06)], 18, sq=1.1), "Base", 0)
    P.parts[-1].data.transform(Matrix.Translation(HC))
    for s in (1, -1):
        e = HC + V_((s * 0.065, 0.16, 0.05))
        P.obj("Socket", oriented_ball(e, (0.05, 0.03, 0.045), V_((1, 0, 0)), V_((0, 1, 0)), V_((0, 0, 1)), 10, 5), "Dark")
        P.obj("EyeFire", ball(tuple(e + V_((0, 0.02, -0.005))), (0.022, 0.012, 0.022), 8, 4), "Glow")
        P.obj("BrowRidge", pipe([HC + V_((s * 0.02, 0.18, 0.09)), HC + V_((s * 0.09, 0.15, 0.11)), HC + V_((s * 0.14, 0.09, 0.1))], [0.02, 0.022, 0.015], 5), "Base")
        P.obj("Cheekbone", ball(tuple(HC + V_((s * 0.09, 0.13, -0.04))), (0.03, 0.03, 0.025), 8, 4), "Base")
    P.obj("Mouth", oriented_ball(HC + V_((0, 0.17, -0.1)), (0.045, 0.02, 0.06), V_((1, 0, 0)), V_((0, 1, 0)), V_((0, 0, 1)), 10, 5), "Dark")
    P.obj("MouthFire", ball(tuple(HC + V_((0, 0.175, -0.11))), (0.022, 0.01, 0.03), 8, 4), "Glow")
    for j in range(7):   # the weed beard hanging to his chest
        a = math.radians(-60 + 20 * j)
        top = HC + V_((math.sin(a) * 0.12, 0.1 + math.cos(a) * 0.05, -0.12))
        bd = [top + V_((0.02 * math.sin(i + j), 0.02 * i, -0.08 * i)) for i in range(6)]
        P.obj("Beard", flat_pipe(bd, [0.03, 0.035, 0.03, 0.025, 0.015, 0.0], V_((0, 1, 0)), 0.6, 6), "Dark")
    for j in range(5):
        a = math.radians(-50 + 25 * j)
        b0 = HC + V_((math.sin(a) * 0.14, -0.1, 0.06))
        P.obj("Hair", flame(b0, V_((math.sin(a) * 0.4, -1.0, -0.6)), 0.38, 0.04, V_((0, 0, 1))), "Base")
    tricorn(P, HC + V_((0, -0.03, 0.16)), 0.19, 0.36, 0.12, 0.12, emblem=True, paint="Dark")
    # the right arm raises the cutlass at you, the left holds out the lantern
    sh = C0 + V_((0.27, 0.0, 1.12)); el = sh + V_((0.12, 0.22, 0.05)); hd = el + V_((-0.04, 0.24, 0.12))
    P.obj("Sleeve", pipe([sh, el, hd], [0.07, 0.06, 0.065], 8), "Dark")
    P.obj("Hand", ball(tuple(hd + V_((0, 0.04, 0))), (0.04,) * 3, 8, 4), "Base")
    bl = bez(hd + V_((0, 0.05, 0.02)), hd + V_((0, 0.25, 0.18)), hd + V_((0, 0.42, 0.38)), hd + V_((0, 0.5, 0.62)), 8)
    P.obj("Cutlass", flat_pipe(bl, [0.035, 0.04, 0.042, 0.042, 0.04, 0.035, 0.028, 0.016, 0.0], V_((1, 0, 0)), 0.75, 8), "Metal")
    P.obj("Guard", xf(torus(0.06, 0.012, 0.0, 14, 4), Matrix.Rotation(math.pi / 2, 3, "Y"), tuple(hd + V_((0, 0.04, 0.0)))), "Trim")
    sh2 = C0 + V_((-0.27, 0.0, 1.12)); el2 = sh2 + V_((-0.1, 0.2, -0.18)); hd2 = el2 + V_((0.02, 0.22, 0.02))
    P.obj("Sleeve", pipe([sh2, el2, hd2], [0.07, 0.06, 0.065], 8), "Dark")
    P.obj("Hand", ball(tuple(hd2 + V_((0, 0.03, 0))), (0.04,) * 3, 8, 4), "Base")
    L2 = hd2 + V_((0, 0.05, -0.2))
    P.obj("Bail", pipe([hd2 + V_((0, 0.03, -0.02)), L2 + V_((0, 0, 0.12))], [0.008] * 2, 4), "Trim")
    P.obj("LanternCap", lathe([(0.0, 0.14), (0.07, 0.08), (0.065, 0.06)], 10, "z", tuple(L2)), "Trim")
    P.obj("LanternGlass", lathe([(0.06, 0.06), (0.065, -0.06), (0.0, -0.075)], 10, "z", tuple(L2)), "Glow")
    for j in range(4):
        a = 2 * math.pi * (j + 0.5) / 4
        P.obj("LanternBar", pipe([L2 + V_((math.cos(a) * 0.066, math.sin(a) * 0.066, 0.06)), L2 + V_((math.cos(a) * 0.066, math.sin(a) * 0.066, -0.06))], [0.008] * 2, 4), "Trim")
    P.part("Muzzle", ball(tuple(L2), (0.04, 0.03, 0.04), 8, 4), "Lamp", tuple(L2))
    return P


def long_feather(base, d, L, w, nrm, curl=0.0, tip=0.35, n=18):
    """feather() drawn with n rings, so a colour painted by distance changes in a clean line across it."""
    base, d, nrm = V_(base), V_(d).normalized(), V_(nrm).normalized()
    pts = bez(base, base + d * L * 0.35, base + d * L * 0.7 + nrm * curl * 0.5, base + d * L + nrm * curl, n)
    keys = [(0, w * 0.35), (1 / 6, w * 0.85), (2 / 6, w), (3 / 6, w * 0.95), (4 / 6, w * 0.8), (5 / 6, w * tip + w * 0.15), (1, 0.0)]
    return flat_pipe(pts, [lerp_keys(i / n, keys) for i in range(n + 1)], nrm, 0.86, 8)


def frame_rh(fwd, upref=(0, 0, 1)):
    """a right-handed frame (x, fwd, z) for something facing fwd, x level (oriented_ball keeps its faces outward only in such a frame)."""
    f = V_(fwd).normalized(); x = f.cross(V_(upref))
    if x.length < 1e-4: x = V_((1, 0, 0))
    x.normalize(); z = x.cross(f).normalized()
    return x, f, z


def grip_toes(P, foot, g, a, rg=0.03, name="Toe"):
    """a parrot's foot closed round a handle (centre g, axis a, radius rg): zygodactyl, two toes forward and two back, each curling round
    the handle from the foot and ending in a hooked black claw."""
    foot, g, a = V_(foot), V_(g), V_(a).normalized()
    e1 = foot - g; e1 = (e1 - a * e1.dot(a)).normalized(); e2 = a.cross(e1).normalized()
    R = rg + 0.024
    for along, sgn in ((-1.5, 1), (-0.5, 1), (0.5, -1), (1.5, -1)):
        o = a * (along * 0.036)
        pts = [foot + o * 0.6] + [g + o + (e1 * math.cos(th) + e2 * math.sin(th)) * R for th in [sgn * math.radians(20 + 210 * k / 6) for k in range(7)]]
        P.obj(name, pipe(pts, [0.03, 0.028, 0.026, 0.024, 0.022, 0.019, 0.014, 0.0], 8), "Dark")


def cutlass(P, grip, d, flat, L=0.95, name="Cutlass"):
    """a cutlass by its grip: a broad blade curving back along d with its flat facing 'flat', the brass cup guard and knuckle bow, the
    wire-bound grip and the pommel."""
    g = V_(grip); d = V_(d).normalized(); fl = V_(flat); fl = (fl - d * fl.dot(d)).normalized(); bk = fl.cross(d).normalized()   # bk: the back of the blade
    pts = [g + d * (0.08 + L * u) + bk * (0.13 * L * u * u) for u in [k / 12 for k in range(13)]]
    rr = [lerp_keys(k / 12, [(0, 0.05), (0.3, 0.058), (0.7, 0.062), (0.85, 0.052), (0.95, 0.03), (1, 0.0)]) for k in range(13)]
    P.obj(name, flat_pipe(pts, rr, fl, 0.84, 8), "Metal")
    P.obj(name, oriented_ball(g + d * 0.075, (0.085, 0.08, 0.022), bk, fl, d, 16, 6), "Trim")                     # the cup guard
    P.obj(name, pipe(bez(g + d * 0.07 - bk * 0.075, g - bk * 0.1, g - d * 0.1 - bk * 0.08, g - d * 0.15 - bk * 0.02, 6), [0.012] * 7, 5), "Trim")   # the knuckle bow
    P.obj(name, pipe([g - d * 0.14, g + d * 0.06], [0.026, 0.028], 10), "Dark")
    for t in (-0.1, -0.04, 0.02): P.obj(name, pipe([g + d * t, g + d * (t + 0.012)], [0.031, 0.031], 10), "Trim")
    P.obj(name, ball(tuple(g - d * 0.165), (0.036, 0.036, 0.036), 10, 5), "Trim")                                   # the pommel


def flintlock(P, grip, d, up, name="Pistol"):
    """a flintlock pistol by its grip: the curved butt with a brass cap, the lock plate with the cocked hammer and the frizzen, the long round
    barrel with brass bands and a muzzle ring, the wooden stock under it, the ramrod, the trigger and its guard. Returns the muzzle."""
    g = V_(grip); d = V_(d).normalized(); up = V_(up); up = (up - d * up.dot(d)).normalized(); sd = d.cross(up).normalized()
    O = g + d * 0.12 + up * 0.12          # the lock, above and ahead of the grip
    rot = Matrix((sd, d, up)).transposed()
    def at(a, b, c_=0.0): return O + d * a + up * b + sd * c_
    P.obj(name, pipe(bez(at(-0.2, -0.2), at(-0.12, -0.12), at(-0.04, -0.03), at(0.04, 0.0), 6), [0.05, 0.046, 0.042, 0.038, 0.035, 0.032, 0.03], 10), "Dark")
    P.obj(name, ball(tuple(at(-0.205, -0.205)), (0.054, 0.054, 0.054), 10, 5), "Trim")                             # the butt cap
    P.obj(name, pipe([at(0.0, -0.005), at(0.44, 0.0)], [0.03, 0.026], 10), "Dark")                                 # the stock
    P.obj(name, pipe([at(-0.02, 0.03), at(0.56, 0.03)], [0.026, 0.023], 12), "Metal")                              # the barrel
    for t in (0.2, 0.38): P.obj(name, pipe([at(t, 0.03), at(t + 0.022, 0.03)], [0.031, 0.031], 12), "Trim")
    P.obj(name, pipe([at(0.535, 0.03), at(0.565, 0.03)], [0.03, 0.03], 12), "Trim")                              # the muzzle ring
    P.obj(name, box(tuple(at(0.02, 0.03, 0.026)), (0.012, 0.11, 0.05), rot), "Metal", 0, False)                     # the lock plate
    P.obj(name, pipe(bez(at(-0.03, 0.05, 0.022), at(-0.06, 0.11, 0.022), at(-0.01, 0.15, 0.022), at(0.03, 0.12, 0.022), 5), [0.013] * 6, 5), "Metal")   # the hammer
    P.obj(name, box(tuple(at(0.06, 0.075, 0.018)), (0.012, 0.02, 0.055), rot), "Metal", 0, False)                   # the frizzen
    P.obj(name, pipe(bez(at(-0.01, -0.01), at(-0.015, -0.04), at(-0.03, -0.06), at(-0.045, -0.07), 4), [0.008] * 5, 4), "Trim")   # the trigger
    P.obj(name, pipe(bez(at(0.03, -0.01), at(0.03, -0.1), at(-0.1, -0.1), at(-0.08, -0.03), 8), [0.007] * 9, 4), "Trim")          # the guard
    P.obj(name, pipe([at(0.06, -0.035), at(0.5, -0.03)], [0.009, 0.009], 6), "Dark")                              # the ramrod
    return at(0.57, 0.03)


def T2_parrot():
    """CAPTAIN PARROT (2026-10-14, remade like the alien / autumn / west bosses): a scarlet macaw built like the real bird and dressed as a
    pirate captain, held upright in the air to face you like an eagle on a coat of arms, both great wings spread and beating.
    The bird: a big macaw head on a short thick neck, the bare white face patch with faint lines of tiny red feathers under the eye, a pale
    gold eye with a pinpoint black pupil under a scowling ridge of scarlet brow feathers, a scar across the brow, his hackles raised in a fan
    behind the head, scarlet tipped blue, like an angry hawk-headed parrot's; the huge hooked beak - the upper mandible glossy pale horn, the
    lower one black - dropped open in a screech over the black tongue, the head thrown back a little to scream at you. The wings are
    real macaw wings: the rolled leading edge, shingled rows of scarlet lesser and median coverts, the band of yellow greater coverts, eleven
    square-tipped blue secondaries and ten long blue primaries fanned at the wrist like fingers. The long tail: twelve feathers, the middle
    pair longest, scarlet tipped blue, the outer ones more blue. The feet are a parrot's, two toes forward and two back, closed on his weapons.
    The captain: a black tricorn edged in gold with a skull on its front and one of his own tail feathers for a plume, a black patch over the
    left eye, a navy-black coat with a turned-down collar, a white lace jabot cascading down the open front, gold lapels, two rows of gold
    buttons, fringed gold epaulettes on the shoulders where the wings come out, a scarlet sash knotted at the hip with gold-fringed ends and a
    rolled map tucked in it, the coat skirts falling open over the legs, their hem edged in gold. A cutlass raised in the right foot, a
    flintlock aimed at you in the left - his shots leave from its muzzle.
    He is the one boss of the island that flies on wings, as a parrot does: both wings beat (FlapL / FlapR), the tail pumps (SwayTail)."""
    P = Boss("parrot", AB_pal(Base=((0.80, 0.06, 0.04), 0.45), Belly=((0.95, 0.93, 0.88), 0.35), Accent=((0.03, 0.16, 0.72), 0.45),
                              Trim=((0.98, 0.76, 0.22), 0.8), Glass=((0.64, 0.58, 0.47), 0.5), Dark=((0.03, 0.04, 0.11), 0.45),
                              Glow=((1.0, 0.6, 0.04), 0.5), Metal=((0.72, 0.75, 0.8), 0.9), Lamp=((1.0, 0.85, 0.5), 0.8)))
    glow_strength(P, 1.1)
    # ---- the body, upright, the coat on it: navy-black, the shirt white in the open V at the throat, the scarlet neck above the collar
    PTS = bez((0, 0.16, 1.38), (0, 0.1, 1.0), (0, 0.04, 0.55), (0, -0.14, 0.02), 12); n = len(PTS)
    FR = []
    for i in range(n):
        t = (PTS[min(i + 1, n - 1)] - PTS[max(i - 1, 0)]).normalized(); sd = V_((1, 0, 0))
        FR.append((t, sd, sd.cross(t).normalized()))                   # 'up' of the loft is the chest: it faces you
    def keys(k): return [lerp_keys(i / (n - 1), k) for i in range(n)]
    RX = keys([(0, 0.17), (0.12, 0.26), (0.3, 0.35), (0.5, 0.35), (0.7, 0.31), (0.88, 0.22), (1, 0.0)])
    RF = keys([(0, 0.16), (0.12, 0.24), (0.3, 0.33), (0.5, 0.32), (0.7, 0.27), (0.88, 0.18), (1, 0.0)])   # in front of the spine: the chest
    RB = keys([(0, 0.15), (0.12, 0.2), (0.3, 0.25), (0.5, 0.25), (0.7, 0.23), (0.88, 0.16), (1, 0.0)])    # behind it: the back
    SQ = 1.1
    def ring(f):
        i = max(0, min(int(f), n - 2)); a = f - i
        return (PTS[i].lerp(PTS[i + 1], a), FR[i][1], FR[i][2], RX[i] + (RX[i + 1] - RX[i]) * a, RF[i] + (RF[i + 1] - RF[i]) * a,
                RB[i] + (RB[i + 1] - RB[i]) * a)
    def fz(z):
        for i in range(n - 1):
            if PTS[i].z >= z >= PTS[i + 1].z: return i + (PTS[i].z - z) / max(1e-6, PTS[i].z - PTS[i + 1].z)
        return 0.0 if z > PTS[0].z else n - 1.0
    def rp(f, a, k=1.0):   # the point at angle a round the section at f (a = 90 degrees: the front), k times out
        c, sd, fw, rx, rf, rb = ring(f); ca, sa = math.cos(a), math.sin(a)
        u = math.copysign(abs(ca) ** (1 / SQ), ca) * rx; v = math.copysign(abs(sa) ** (1 / SQ), sa) * (rf if sa > 0 else rb)
        return c + (sd * u + fw * v) * k
    def front(x, z, out=0.0):   # the point on the chest at (x, z) and the normal there
        c, sd, fw, rx, rf, rb = ring(fz(z))
        u = max(-0.97, min(0.97, x / rx)); v = rf * (1 - abs(u) ** (2 * SQ)) ** (1 / (2 * SQ))
        nn = (sd * (math.copysign(abs(u) ** (2 * SQ - 1), u) / rx) + fw * ((v / rf) ** (2 * SQ - 1) / rf)).normalized()
        return c + sd * x + fw * v + nn * out, nn
    def vw(z): return 0.05 + 0.11 * max(0.0, min(1.0, (z - 0.6) / 0.7))   # the half-width of the open V
    def coat(c, nn):
        if c.z > 1.31 or c.z < 0.3: return "Base"
        if c.z > 0.6 and nn.y > 0.3 and abs(c.x) < vw(c.z): return "Belly"
        return "Dark"
    P.obj("Body", st_loft(PTS, RX, RF, RB, FR, 28, SQ), coat, 0)
    P.obj("Neck", pipe([V_((0, 0.13, 1.28)), V_((0, 0.2, 1.46)), V_((0, 0.26, 1.58))], [0.19, 0.19, 0.18], 20), "Base")
    fc = fz(1.31); fcp = fz(1.345)
    P.obj("Collar", pipe([rp(fc, 2 * math.pi * k / 40, 1.03) for k in range(41)], [0.045] * 41, 8, False), "Dark")
    P.obj("Collar", pipe([rp(fcp, 2 * math.pi * k / 40, 1.02) for k in range(41)], [0.014] * 41, 5, False), "Trim")
    for zt, w in ((1.29, 0.085), (1.18, 0.1), (1.07, 0.11), (0.96, 0.1)):   # the lace jabot: four ruffled tiers down the open front
        rows = []
        for r in range(3):
            row = []
            for j in range(15):
                a = -1 + 2 * j / 14; top, nn = front(a * w, zt, 0.012); k = r / 2
                row.append(top + V_((a * w * 0.25 * k, 0, -0.14 * k)) + nn * (0.045 * k * (1 - 0.5 * a * a) + 0.024 * math.sin((a + 1) * math.pi * 3) * k))
            rows.append(row)
        quads = [[tuple(rows[r][j]), tuple(rows[r][j + 1]), tuple(rows[r + 1][j + 1]), tuple(rows[r + 1][j])] for r in range(2) for j in range(14)]
        P.part("ClothJabot", st_cloth(quads, 0.012), "Belly", (0, 0, 0), 0, True)
    for s in (1, -1):   # the gold lapels down the edges of the V, two rows of gold buttons outside them
        zs = [1.3 - 0.68 * k / 10 for k in range(11)]
        P.obj("Lapel", flat_pipe([front(s * (vw(z) + 0.03), z, 0.008)[0] for z in zs], [0.035] * 11, front(s * (vw(0.95) + 0.03), 0.95)[1], 0.75, 8), "Trim")
        for z in (1.18, 1.03, 0.88, 0.73):
            q, nn = front(s * (vw(z) + 0.11), z, 0.012); bx, by, bz = frame_rh(nn)
            P.obj("Button", oriented_ball(q, (0.03, 0.016, 0.03), bx, by, bz, 10, 5), "Trim")
    # the scarlet sash at the waist, knotted at the left hip, its two ends hanging with gold fringes; a rolled map tucked in on the right
    fb = fz(0.53); f1 = fz(0.6); f2 = fz(0.46)
    quads = []
    for j in range(40):
        a0, a1 = 2 * math.pi * j / 40, 2 * math.pi * (j + 1) / 40
        quads.append([tuple(rp(f1, a0, 1.06)), tuple(rp(f1, a1, 1.06)), tuple(rp(f2, a1, 1.06)), tuple(rp(f2, a0, 1.06))])
    P.obj("Sash", st_cloth(quads, 0.03), "Base", 0, True)
    kc = rp(fb, math.radians(150), 1.12)
    P.obj("Knot", ball(tuple(kc), (0.075, 0.06, 0.075), 12, 6), "Base")
    for L, dx in ((0.42, -0.04), (0.34, 0.05)):
        e = bez(kc, kc + V_((dx, 0.04, -0.12)), kc + V_((dx * 1.5 - 0.03, 0.05, -L * 0.6)), kc + V_((dx * 2 - 0.05, 0.03, -L)), 6)
        P.obj("SashEnd", flat_pipe(e, [0.05, 0.055, 0.058, 0.06, 0.06, 0.062, 0.064], V_((0, 1, 0)), 0.8, 8), "Base")
        for f_ in range(5):
            q = e[-1] + V_((-0.05 + 0.025 * f_, 0, 0))
            P.obj("Fringe", pipe([q, q + V_((0, 0, -0.07))], [0.009, 0.007], 4), "Trim")
    mc = rp(fb, math.radians(30), 1.1)
    P.obj("Map", pipe([mc + V_((-0.02, 0, -0.16)), mc + V_((0.05, 0.03, 0.22))], [0.06, 0.06], 14), "Belly")
    P.obj("MapTie", pipe([mc + V_((-0.005, 0.0, -0.012)), mc + V_((0.003, 0.002, 0.016))], [0.067, 0.067], 14), "Base")
    # the coat skirts falling open from the sash over the legs: short in front, long behind, split at the back, the hem edged in gold
    c_b = ring(fb)[0]
    def skirt(a, t):
        p0 = rp(fb, a, 1.05); rad = V_((p0.x - c_b.x, p0.y - c_b.y, 0)).normalized()
        zh = lerp_keys((math.sin(a) + 1) / 2, [(0, -0.34), (0.5, -0.02), (1, 0.12)])
        return p0 + rad * (0.24 * t ** 1.3) + V_((0, 0, (zh - p0.z) * t))
    for a0, a1, af in ((-85, 58, 58), (122, 265, 122)):
        A = [math.radians(a0 + (a1 - a0) * j / 14) for j in range(15)]
        quads = [[tuple(skirt(A[j], i / 4)), tuple(skirt(A[j + 1], i / 4)), tuple(skirt(A[j + 1], (i + 1) / 4)), tuple(skirt(A[j], (i + 1) / 4))] for i in range(4) for j in range(14)]
        P.part("ClothSkirt", st_cloth(quads, 0.02), "Dark", (0, 0, 0), 0, True)
        P.obj("Hem", pipe([skirt(a, 1.0) for a in A], [0.022] * 15, 6), "Trim")
        P.obj("Hem", pipe([skirt(math.radians(af), i / 6) for i in range(7)], [0.02] * 7, 6), "Trim")
    # fringed gold epaulettes on the shoulders, over the roots of the wings
    for s in (1, -1):
        E = V_((s * 0.25, 0.02, 1.2)); z_ = V_((s * 0.45, 0.1, 1.0)).normalized()
        x_ = V_((0, 1, 0)).cross(z_).normalized(); y_ = z_.cross(x_).normalized()
        P.obj("Epaulette", oriented_ball(E, (0.15, 0.13, 0.04), x_, y_, z_, 16, 6), "Trim")
        for k in range(11):
            t = math.radians(-80 + 160 * k / 10)
            q = E + (x_ * s * math.cos(t) * 0.145 + y_ * math.sin(t) * 0.125)
            P.obj("Epaulette", pipe([q, q + V_((s * 0.02, 0, -0.13))], [0.012, 0.009], 5), "Trim")

    # ---- the head: a macaw's, built about HC (then tipped up a little to look at you)
    HC = V_((0, 0.3, 1.7)); HR3 = V_((0.27, 0.29, 0.28)); HK = 1.24   # built at 1, grown HK times
    def hs(d, out=0.0):   # the point on the head along d, out off it, and the normal there
        d = V_(d).normalized(); k = 1.0 / math.sqrt((d.x / HR3.x) ** 2 + (d.y / HR3.y) ** 2 + (d.z / HR3.z) ** 2)
        p = d * k; nn = V_((p.x / HR3.x ** 2, p.y / HR3.y ** 2, p.z / HR3.z ** 2)).normalized()
        return HC + p + nn * out, nn
    def azel(az, el):
        a, e = math.radians(az), math.radians(el)
        return V_((math.sin(a) * math.cos(e), math.cos(a) * math.cos(e), math.sin(e)))
    def plate(dc, A, B, out, thick, dome=0.0, rings=5, seg=28):   # a smooth oval patch lying on the head
        dc = V_(dc).normalized(); e1 = V_((0, 0, 1)).cross(dc).normalized(); e2 = dc.cross(e1).normalized()
        g = []
        for r in range(rings + 1):
            u = r / rings
            g.append([hs(dc + e1 * (A * u * math.cos(2 * math.pi * j / seg)) + e2 * (B * u * math.sin(2 * math.pi * j / seg)), out + dome * (1 - u * u))[0] for j in range(seg)])
        polys = [[tuple(g[0][0]), tuple(g[1][j]), tuple(g[1][(j + 1) % seg])] for j in range(seg)]
        polys += [[tuple(g[r][j]), tuple(g[r + 1][j]), tuple(g[r + 1][(j + 1) % seg]), tuple(g[r][(j + 1) % seg])] for r in range(1, rings) for j in range(seg)]
        return st_cloth(polys, thick)
    h0 = len(P.parts)
    P.obj("Head", ball(tuple(HC), tuple(HR3), 40, 20), "Base")
    for s in (1, -1):
        P.obj("FacePatch", plate(azel(s * 37, -1), 0.44, 0.37, 0.004, 0.01), "Belly")
        bd = [azel(s * (60 - 36 * k / 8), 30 - 20 * k / 8 + 1.5 * math.sin(math.pi * k / 8)) for k in range(9)]   # the brow, slanting down to the beak over the eye
        P.obj("Brow", flat_pipe([hs(d, 0.03)[0] for d in bd], [0.014, 0.03, 0.038, 0.042, 0.043, 0.042, 0.038, 0.03, 0.014], hs(bd[4])[1], 0.4, 8), "Base")
    for k in range(19):   # his hackles up, like an angry hawk-headed parrot: a fan of scarlet feathers tipped blue raised behind the head, framing the face
        psi = math.radians(-58 + 296 * k / 18); r = V_((math.cos(psi), 0.0, math.sin(psi)))
        root = HC + r * 0.2 + V_((0, -0.14, 0)); d = (r + V_((0, -0.3, 0))).normalized(); L = 0.34 + (0.06 if k % 2 else 0.0)
        P.obj("Hackle", long_feather(root, d, L, 0.065, V_((0, 1, 0)).cross(d).cross(d).normalized(), -0.03, 0.3),
              lambda cc, nn_, root=root, L=L: "Accent" if (cc - root).length > L * 0.74 else "Base", 0, False)
    pe, ne = hs(azel(35, 9))   # the right eye, turned a little toward you
    ex, ey, ez = frame_rh((ne + V_((0, 0.25, 0.04))).normalized())
    P.obj("EyeLid", oriented_ball(pe + ne * 0.008, (0.082, 0.024, 0.077), ex, ey, ez, 18, 8), "Dark")
    P.obj("Eye", oriented_ball(pe + ne * 0.014, (0.066, 0.028, 0.062), ex, ey, ez, 18, 8), "Glow")
    P.obj("Pupil", oriented_ball(pe + ne * 0.014 + ey * 0.024, (0.021, 0.012, 0.021), ex, ey, ez, 12, 6), "Dark")
    P.obj("Glint", ball(tuple(pe + ne * 0.014 + ey * 0.033 + ez * 0.025 - ex * 0.018), (0.01,) * 3, 6, 3), "Belly")
    P.obj("Scar", pipe([hs(azel(50 - 12 * k / 6, 42 - 18 * k / 6), 0.02)[0] for k in range(7)], [0.0, 0.008, 0.009, 0.009, 0.009, 0.008, 0.0], 5), "Dark")
    dP = azel(-35, 9)   # the patch over the left eye and its strap round the head
    P.obj("EyePatch", plate(dP, 0.3, 0.28, 0.016, 0.022, 0.016), "Dark")
    q2 = V_((0.35, 0.3, 0.9)); q2 = (q2 - dP * q2.dot(dP)).normalized()
    P.obj("PatchStrap", pipe([hs(dP * math.cos(t) + q2 * math.sin(t), 0.014)[0] for t in [2 * math.pi * k / 48 for k in range(49)]], [0.012] * 49, 6, False), "Dark")
    # the beak: the upper mandible pale horn, deep and hooked, black at its base by the gape; the lower one black, dropped open
    mid = bez(HC + V_((0, 0.18, 0.03)), HC + V_((0, 0.43, 0.1)), HC + V_((0, 0.57, -0.06)), HC + V_((0, 0.48, -0.29)), 14)
    ub = pipe(mid, [lerp_keys(k / 14, [(0, 0.145), (0.3, 0.135), (0.6, 0.095), (0.85, 0.05), (1, 0.0)]) for k in range(15)], 18)
    for v in ub.verts:
        q = v.co - HC; v.co.x = HC.x + q.x * lerp_keys((q.y - 0.18) / 0.32, [(0, 1.38), (0.5, 1.05), (1, 0.74)])
    P.obj("Beak", ub, "Glass")
    J0 = HC + V_((0, 0.15, -0.09)); JR = Matrix.Rotation(math.radians(-54), 3, "X")
    def jaw(bm): return xf(bm, JR, tuple(J0 - JR @ J0))
    lm = pipe(bez(HC + V_((0, 0.17, -0.1)), HC + V_((0, 0.28, -0.17)), HC + V_((0, 0.38, -0.18)), HC + V_((0, 0.44, -0.14)), 8),
              [0.12, 0.115, 0.105, 0.094, 0.08, 0.066, 0.052, 0.034, 0.0], 14)
    for v in lm.verts: v.co.x = HC.x + (v.co.x - HC.x) * 1.15
    P.obj("Jaw", jaw(lm), "Dark")
    P.obj("Mouth", ball(tuple(HC + V_((0, 0.2, -0.12))), (0.085, 0.1, 0.07), 14, 7), "Base")
    P.obj("Tongue", jaw(ball(tuple(HC + V_((0, 0.3, -0.125))), (0.065, 0.085, 0.05), 12, 6)), "Dark")
    # the tricorn, worn back off the brow, and the plume: one of his own tail feathers, scarlet tipped blue, swept back off the left
    hc = HC + V_((0, -0.04, 0.19)); k0 = len(P.parts)
    tricorn(P, tuple(hc), 0.215, 0.4, 0.14, 0.17, emblem=True, paint="Dark")
    pl = bez(hc + V_((-0.26, 0.06, 0.08)), hc + V_((-0.45, 0.0, 0.36)), hc + V_((-0.5, -0.38, 0.52)), hc + V_((-0.36, -0.72, 0.46)), 24)
    P.obj("Plume", pipe(pl, [0.016] * 24 + [0.0], 5), "Base")
    for i in range(1, 24):
        t = (pl[i + 1] - pl[i - 1]).normalized(); sd = t.cross(V_((0, 0, 1))).normalized(); upv = sd.cross(t).normalized()
        L = 0.15 * math.sin(math.pi * i / 24) ** 0.6 + 0.03
        for q in (1, -1): P.obj("Plume", fx_tuft(pl[i], sd * q * 0.85 + t * 0.5, L, 0.04, upv, -0.02), "Accent" if i > 16 else "Base", 0, False)
    R = Matrix.Rotation(math.radians(12), 3, "X")
    for ob in P.parts[k0:]:
        for v in ob.data.vertices: v.co = R @ (v.co - hc) + hc
    T = Matrix.Translation(HC) @ Matrix.Rotation(math.radians(16), 4, "X") @ Matrix.Scale(HK, 4) @ Matrix.Translation(-HC)
    for ob in P.parts[h0:]: ob.data.transform(T)

    # ---- the wings, spread to you in a V from the shoulders; each wing one Flap part, beating about the nose axis
    S0 = V_((0.26, -0.06, 1.08)); U0 = V_((1.0, -0.22, 0.42)).normalized()   # the shoulder; out along the leading edge
    C0 = V_((U0.z, 0.0, -U0.x)).normalized(); N0 = U0.cross(C0).normalized()   # down the chord; the face of the wing (toward you)
    def W(s, u, c, h=0.0):
        p = S0 + U0 * u + C0 * c + N0 * (h - 0.06 * math.sin(math.pi * min(max(u, 0.0), 1.0)) * (1 - 0.5 * min(c, 1.0)))
        return V_((s * p.x, p.y, p.z))
    def M(s, v): return V_((s * v.x, v.y, v.z))
    for s in (1, -1):
        name = "FlapR" if s > 0 else "FlapL"; hub = tuple(W(s, 0, 0)); nrm = M(s, N0)
        quads = []   # the skin of the arm under the coverts, its rolled leading edge over the bones
        for i in range(12):
            for j in range(3):
                u0, u1 = 1.02 * i / 12, 1.02 * (i + 1) / 12; c0, c1 = 0.42 * j / 3, 0.42 * (j + 1) / 3
                quads.append([tuple(W(s, u0, c0, -0.01)), tuple(W(s, u1, c0, -0.01)), tuple(W(s, u1, c1, -0.01)), tuple(W(s, u0, c1, -0.01))])
        P.part(name, st_cloth(quads, 0.022), "Base", hub, 0, True)
        P.part(name, pipe([W(s, 1.06 * k / 12, -0.005, 0.02) for k in range(13)], [lerp_keys(k / 12, [(0, 0.062), (0.5, 0.045), (1, 0.034)]) for k in range(13)], 12), "Base", hub)
        # the coverts in shingled rows, each row over the one below it: the lesser and median scarlet, the greater yellow
        for row, (c0, L, w, du, h, slot) in enumerate(((0.0, 0.13, 0.048, 0.068, 0.058, "Base"), (0.07, 0.14, 0.05, 0.068, 0.046, "Base"),
                                                       (0.16, 0.17, 0.058, 0.078, 0.034, "Base"), (0.24, 0.25, 0.068, 0.086, 0.022, "Trim"))):
            u = 0.05 + (du * 0.5 if row % 2 else 0.0)
            while u < 1.0:
                P.part(name, feather(W(s, u, c0, h), M(s, (C0 + U0 * (0.1 * u)).normalized()), L * (1 - 0.12 * u), w, nrm, -0.01, 0.5), slot, hub, 0, False)
                u += du
        for k in range(11):   # the secondaries: blue, square-tipped, hanging from the forearm
            u = 0.06 + 0.92 * k / 10
            P.part(name, feather(W(s, u, 0.36, 0.004 * k), M(s, (C0 + U0 * (0.04 + 0.22 * k / 10)).normalized()), 0.62 - 0.05 * k / 10, 0.085, nrm, -0.03, 0.55),
                   "Accent", hub, 0, False)
        for k in range(10):   # the primaries: ten long blue flight feathers fanned from the wrist like fingers
            phi = math.radians(-72 + 104 * k / 9)
            L = lerp_keys(k / 9, [(0, 0.72), (0.4, 0.98), (0.7, 1.2), (0.85, 1.22), (1, 1.06)])
            P.part(name, feather(W(s, 1.0 - 0.04 * k / 9, 0.4 - 0.32 * k / 9, 0.004 * (10 - k)), M(s, U0 * math.cos(phi) - C0 * math.sin(phi)), L, 0.1, nrm, -0.05, 0.16),
                   "Accent", hub, 0, False)
        for k in range(6):    # the primary coverts over their bases
            phi = math.radians(-60 + 90 * k / 5)
            P.part(name, feather(W(s, 0.96 - 0.02 * k / 5, 0.36 - 0.28 * k / 5, 0.03), M(s, U0 * math.cos(phi) - C0 * math.sin(phi)), 0.26, 0.075, nrm, -0.01, 0.45),
                   "Accent", hub, 0, False)

    # ---- the long tail hanging behind the legs: twelve feathers, the middle pair longest, scarlet tipped blue, the outer ones more blue
    th = V_((0, -0.16, 0.06)); tn = V_((0, 0.92, -0.39))
    for k in range(12):
        c_ = (k - 5.5) / 5.5
        d = V_((c_ * 0.22, -0.42, -1.0)).normalized(); L = 1.62 - 0.78 * abs(c_) ** 0.85; b = th + V_((c_ * 0.08, 0, 0))
        paint = "Accent" if abs(k - 5.5) > 2.5 else (lambda cc, nn: "Accent" if (cc - th).length > 1.02 else "Base")
        P.part("SwayTail", long_feather(b + tn * (0.006 * abs(k - 5.5)), d, L, 0.075, tn, -0.04, 0.4), paint, tuple(th), 0, False)

    # ---- the legs: feathered drumsticks out of the skirts, scaled shanks, the feet closed on the cutlass (raised) and the flintlock (aimed)
    muzzle = None
    for s in (1, -1):
        hip = V_((s * 0.13, 0.04, 0.28)); ank = V_((s * 0.2, 0.3, 0.05))
        P.obj("Thigh", pipe(bez(hip, hip + V_((s * 0.03, 0.1, -0.04)), ank + V_((-s * 0.01, -0.06, 0.06)), ank, 5), [0.1, 0.1, 0.092, 0.08, 0.068, 0.06], 12), "Base")
        dd = V_((s * 0.06, 0.17, -0.06)).normalized(); foot = ank + dd * 0.19
        lx, lf, lz = frame_rh(dd)
        for k in range(10):   # the feathered cuff at the ankle
            a = 2 * math.pi * k / 10; o = lx * math.cos(a) + lz * math.sin(a)
            P.obj("Cuff", fx_tuft(ank - dd * 0.05 + o * 0.058, (dd + o * 0.35).normalized(), 0.1, 0.035, o, 0.0), "Base", 0, False)
        P.obj("Shank", pipe([ank - dd * 0.02, foot], [0.05, 0.043], 12), "Dark")
        for k in range(4):
            q = ank.lerp(foot, 0.25 + 0.18 * k)
            P.obj("Scute", pipe([q - dd * 0.009, q + dd * 0.009], [0.052 - 0.002 * k, 0.05 - 0.002 * k], 12), "Dark")
        if s > 0:
            dc = V_((0.5, 0.22, 1.0)).normalized(); gc = foot + (dd - dc * dd.dot(dc)).normalized() * 0.05
            cutlass(P, gc, dc, (0, 1, 0)); grip_toes(P, foot, gc, dc, 0.028)
        else:
            dp_, up_ = V_((0, 1, 0)), V_((0, 0, 1)); ga = (dp_ + up_).normalized(); gp = foot + (dd - ga * dd.dot(ga)).normalized() * 0.05
            muzzle = flintlock(P, gp, dp_, up_); grip_toes(P, foot, gp, ga, 0.04)
    P.part("Muzzle", ball(tuple(muzzle), (0.03, 0.03, 0.03), 8, 4), "Lamp", tuple(muzzle))
    return P


BOSSES = [("parrot", T2_parrot), ("mimic", T2_mimic), ("ghost", T2_ghost), ("crab", T2_crab), ("skull2", T2_skull)]

# 2026-10-14 ("more realistic, keep the cartoonish look, they still look plasticky"): what each part is made of, for boss_bake.py - the
# slot's surface unless the part's name says otherwise. Export bakes them into Boss_<id>_Albedo / _Normal / _Mask / _Emission.png.
import boss_bake as BB
feather = BB.feathered(feather); long_feather = BB.feathered(long_feather)   # the vane marked for the bake: shaft and barbs
BB.TABLES.update({
    "parrot": ({"Base": "down", "Belly": "skin", "Accent": "feather", "Trim": "gold", "Glass": "horn", "Dark": "wool", "Glow": "glow", "Metal": "steel", "Lamp": "lamp"},
               [("Flap*", "feather"), ("SwayTail", "feather"), ("Hackle", "feather"), ("Plume", "feather"), ("Cuff", "feather"),
                ("Body", {"Base": "down", "Belly": "linen", "Dark": "wool"}), ("ClothJabot", "lace"), ("ClothSkirt", "wool"), ("Collar", {"Dark": "wool"}),
                ("Sash", "silk"), ("Knot", "silk"), ("SashEnd", "silk"), ("Map", "parchment"), ("MapTie", "cloth"),
                ("FacePatch", "skin"), ("EyeLid", "skin"), ("Pupil", "eye"), ("Glint", "eye"), ("Scar", "skin"), ("EyePatch", "leather"), ("PatchStrap", "leather"),
                ("Beak", "horn"), ("Jaw", "keratin"), ("Mouth", "flesh"), ("Tongue", "flesh"),
                ("Brim", "felt"), ("Crown", "felt"), ("HatSkull", "bone"), ("HatBone", "bone"), ("HatEye", "matte"),
                ("Shank", "scales"), ("Scute", "scales"), ("Toe", "scales"),
                ("Cutlass", {"Metal": "steel", "Trim": "brass", "Dark": "leather"}), ("Pistol", {"Dark": "wood", "Trim": "brass", "Metal": "iron"})]),
    "mimic": ({"Base": "wood", "Belly": "enamel", "Accent": "flesh", "Trim": "gold", "Glass": "gem", "Dark": "iron", "Glow": "glow", "Metal": "iron", "Lamp": "lamp"},
              [("Seams", "matte"), ("Keyhole", "matte"), ("Corner", "brass"), ("Padlock", "brass"), ("SwayLid", {"Trim": "brass"}),
               ("Mast", "wood_v"), ("MastBand", "iron"), ("Masthead", "brass"), ("ClothSail*", "canvas"), ("ReefPoint", "rope"),
               ("Shroud", "rope"), ("Sheet", "rope"), ("ClothFlag", "canvas")]),
    "ghost": ({"Base": "ghost", "Belly": "bone", "Accent": "cloth", "Trim": "brass", "Glass": "wood", "Dark": "wool", "Glow": "glow", "Metal": "steel", "Lamp": "lamp"},
              [("Strake", "wood"), ("LootStrap", "iron"), ("Loot", {"Trim": "gold"}), ("Coin", "gold"), ("Jewel", "gem"), ("Hole", "matte"),
               ("Barnacle", "barnacle"), ("Weed", "weed"), ("LanternChain", "iron"), ("ClothPennant", "canvas"), ("CrewSkullSocket", "matte"),
               ("CrewSkullNose", "matte"), ("CrewSkullGrin", "matte"), ("CrewSkullTooth", "enamel"), ("Socket", "matte"), ("Mouth", "matte"),
               ("Beard", "weed"), ("Hair", "hair"), ("Brim", "felt"), ("Crown", "felt"), ("BrimEdge", "gold"), ("HatSkull", "bone"), ("HatBone", "bone"),
               ("HatEye", "matte"), ("Coat", {"Trim": "gold"}), ("Button", "gold"), ("Epaulette", "gold"), ("Fringe", "gold"), ("Sash", "silk"),
               ("Cutlass", "steel"), ("Rib", {"Glass": "wood", "Belly": "bone"})]),
    "crab": ({"Base": "shell", "Belly": "shell_belly", "Accent": "shell", "Trim": "brass", "Glass": "eye", "Dark": "keratin", "Glow": "glow", "Metal": "iron", "Lamp": "lamp"},
             [("Puffer*Spine", "keratin"), ("Puffer*Spot", "puffer"), ("Puffer*Eye", "eye_white"), ("Puffer*Pupil", "eye"), ("Puffer*Brow", "puffer"),
              ("Puffer*Lip", "puffer"), ("Puffer*Mouth", "matte"), ("Puffer*Beak", "enamel"), ("Puffer*Tail", "fin"), ("FlapFin*", "fin"), ("Puffer?", "puffer"),
              ("Glint", "eye"), ("Patch", "leather"), ("PatchStrap", "leather"), ("Rope", "rope"), ("Knot", "rope"), ("FingerTooth", "enamel"),
              ("Cannon", {"Metal": "iron", "Trim": "brass", "Dark": "matte"})]),
    "skull2": ({"Base": "bone", "Belly": "bone", "Accent": "cloth", "Trim": "gold", "Glass": "gem", "Dark": "matte", "Glow": "glow", "Metal": "iron", "Lamp": "lamp"},
               [("Tooth", {"Belly": "enamel"}), ("Plume", "feather"), ("Brim", "felt"), ("Crown", "felt"), ("ShaftCollar", "brass")]),
})

if __name__ == "__main__":
    os.makedirs(AB.OUT, exist_ok=True)
    for bid, fn in BOSSES:
        if ONLY and bid not in ONLY: continue
        P = fn()
        if AB.EXPORT and bid in BB.TABLES: BB.finish_baked(P, AB.OUT)   # the real surfaces baked into textures beside the FBX
        else: P.finish()
    print("DONE")
