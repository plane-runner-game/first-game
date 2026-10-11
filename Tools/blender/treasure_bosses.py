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
    """The pirate king's parrot grown to a monster: a scarlet macaw with yellow and blue wings that beat, a black tricorn with a skull, an
    eye patch, a gold earring, a great hooked beak, long red-and-blue tail plumes, and a gold doubloon gripped in its talons."""
    P = Boss("parrot", {"Base": ((0.88, 0.10, 0.08), 0.5), "Belly": BONE, "Accent": ((0.08, 0.35, 0.90), 0.55), "Trim": GOLD,
                        "Glass": ((1.0, 0.82, 0.10), 0.5), "Dark": BLACK, "Glow": ((1.0, 0.85, 0.45), 0.5),
                        "Metal": ((0.15, 0.15, 0.17), 0.5), "Lamp": ((1.0, 0.85, 0.35), 0.8)})
    P.obj("Body", loft([(0.7, 0.05, 0.05, 0, 0.35), (0.55, 0.36, 0.38, 0, 0.25), (0.15, 0.48, 0.5, 0, 0.05), (-0.35, 0.42, 0.42, 0, -0.05),
                        (-0.8, 0.26, 0.24, 0, -0.08), (-1.05, 0.1, 0.08, 0, -0.08)], 18), "Base", 1)
    P.obj("Head", ball((0, 0.78, 0.55), (0.36, 0.38, 0.36), 16, 8), "Base", 1)
    # the white face patch, the eyes (one patched), the beak
    for s in (1, -1):
        P.obj("Face", ball((s * 0.22, 0.95, 0.58), (0.14, 0.14, 0.15), 10, 5), "Belly", 1)
        if s > 0:
            P.obj("Eye", ball((s * 0.27, 1.02, 0.63), (0.08, 0.06, 0.09), 10, 5), "Glass")
            P.obj("Pupil", ball((s * 0.29, 1.07, 0.64), (0.04, 0.03, 0.05), 8, 4), "Dark")
            P.obj("Earring", torus(0.08, 0.018, 0.0, 14, 4), "Trim"); P.parts[-1].data.transform(Matrix.Translation((0.37, 0.7, 0.36)) @ Matrix.Rotation(math.radians(90), 4, "Y"))
        else:
            P.obj("Patch", ball((s * 0.27, 1.03, 0.63), (0.1, 0.05, 0.1), 10, 5), "Dark")
    strap = [Vector((math.sin(a) * 0.38, 0.78 + math.cos(a) * 0.39, 0.55 + 0.18 * math.cos(a))) for a in [2 * math.pi * k / 30 for k in range(31)]]
    P.obj("Strap", pipe(strap, [0.022] * 31, 5, False), "Dark")
    upper = bez((0, 1.08, 0.62), (0, 1.32, 0.62), (0, 1.42, 0.42), (0, 1.32, 0.2), 8)
    P.obj("Beak", pipe(upper, [0.17, 0.165, 0.15, 0.13, 0.11, 0.08, 0.055, 0.03, 0.0], 12), "Belly", 1)
    P.obj("Jaw", pipe(bez((0, 1.0, 0.42), (0, 1.15, 0.35), (0, 1.2, 0.32), (0, 1.22, 0.3), 5), [0.12, 0.1, 0.08, 0.06, 0.04, 0.0], 10), "Dark", 1)
    tricorn(P, (0, 0.72, 0.84), 0.32, 0.6, 0.28, 0.22)
    # the wings: red at the shoulder, a band of yellow, blue flight feathers
    for s in (1, -1):
        name = "FlapR" if s > 0 else "FlapL"
        hub = (s * 0.36, 0.15, 0.28)
        keys = [(0.3, 0.6, -0.4, 0.16, 0.3), (0.8, 0.62, -0.62, 0.12, 0.38), (1.35, 0.5, -0.72, 0.08, 0.45), (1.8, 0.25, -0.65, 0.05, 0.5), (2.05, 0.0, -0.45, 0.02, 0.5)]
        bm = sweep([(x, airfoil(le, te, th, z)) for (x, le, te, th, z) in fine(keys)], "x")
        if s < 0: bm = mirror_x(bm)
        P.part(name, bm, lambda c, n: "Accent" if abs(c.x) > 1.2 or c.y < -0.48 else ("Glass" if abs(c.x) > 0.8 else "Base"), hub, 0)
        for k in range(6):   # the long blue primaries
            x0 = 1.05 + k * 0.17; y0 = -0.5 - 0.02 * k
            P.part(name, cone((s * x0, y0 + 0.15, 0.44), (s * (x0 + 0.1), y0 - 0.4 - 0.04 * (5 - abs(k - 2)), 0.42), 0.08, 4), "Accent", hub, 0, False)
    # the tail plumes
    for k, (dx, col) in enumerate(((-0.12, "Accent"), (0.0, "Base"), (0.12, "Accent"), (-0.24, "Base"), (0.24, "Base"))):
        L = 1.6 - 0.2 * abs(dx) * 4
        P.obj("Plume", pipe(bez((dx * 0.5, -0.9, -0.05), (dx, -1.4, -0.1), (dx * 1.5, -1.9, -0.05), (dx * 2, -0.9 - L, 0.0), 6), [0.09, 0.1, 0.09, 0.08, 0.06, 0.035, 0.0], 6), col, 0)
        for v in P.parts[-1].data.vertices: v.co.z = (v.co.z - (-0.05)) * 0.35 - 0.05
    # legs and the doubloon in its talons
    for s in (1, -1):
        P.obj("Leg", pipe([(s * 0.18, 0.1, -0.35), (s * 0.18, 0.15, -0.6)], [0.07, 0.05], 8), "Metal")
        for k in (-1, 0, 1): P.obj("Talon", cone((s * 0.18, 0.15, -0.6), (s * 0.18 + k * 0.08, 0.32, -0.66), 0.03, 4), "Metal", 0, False)
    P.obj("Doubloon", coin((0, 0.28, -0.72), 0.22, 0.05, Matrix.Rotation(math.radians(90), 3, "X")), "Trim")
    P.obj("DoubloonX", box((0, 0.31, -0.72), (0.2, 0.01, 0.04)), "Glow", 0, False)
    P.part("Muzzle", ball((0, 1.3, 0.25), (0.06, 0.04, 0.05), 8, 4), "Glow", (0, 1.3, 0.25))
    return P


# ================================================================= 2. the treasure mimic
def T_mimic():
    """A treasure chest that bites: an iron-bound chest on leathery bat wings, its lid gaping and snapping on rows of teeth, a long tongue,
    glowing eyes in the dark of the lid, and gold and jewels spilling out of its mouth."""
    P = Boss("mimic", {"Base": ((0.48, 0.26, 0.12), 0.35), "Belly": BONE, "Accent": ((0.32, 0.12, 0.30), 0.4), "Trim": GOLD,
                       "Glass": ((0.95, 0.10, 0.25), 0.95), "Dark": ((0.07, 0.03, 0.03), 0.4), "Glow": ((1.0, 0.85, 0.3), 0.5),
                       "Metal": ((0.22, 0.20, 0.22), 0.6), "Lamp": ((1.0, 0.80, 0.30), 0.8)})
    rng = random.Random(4)
    W, D, H = 0.95, 0.65, 0.5
    plank = lambda c, n: "Dark" if abs(n.z) < 0.5 and (c.z * 4.5) % 1.0 < 0.08 else "Base"
    P.obj("Chest", box((0, 0, -H * 0.5), (W * 2, D * 2, H * 2)), plank, 0, False)
    P.obj("Inside", box((0, 0.0, -0.02), (W * 1.8, D * 1.8, 0.06)), "Dark", 0, False)
    for x in (-0.6, 0.6):   # iron bands and gold corners
        P.obj("Band", box((x, 0, -H * 0.5), (0.12, D * 2 + 0.04, H * 2 + 0.04)), "Metal", 0, False)
    for sx in (-1, 1):
        for sy in (-1, 1):
            P.obj("Corner", box((sx * W, sy * D, -H * 0.5), (0.14, 0.14, H * 2 + 0.06)), "Trim", 0, False)
    # the lid, open, on its hinge at the back
    hub = Vector((0, -D, 0.02)); op = Matrix.Rotation(math.radians(62), 3, "X")
    def lid(bm):
        for v in bm.verts: v.co = op @ (v.co - hub) + hub
        return bm
    arc = []
    for k in range(9):
        a = math.pi * k / 8
        for x in (-W, W): arc.append((x, math.cos(a) * D, math.sin(a) * 0.45))
    lidshape = lambda bm: lid(xf(bm, None, (0, 0, 0.02)))
    P.part("SwayLid", lidshape(hull(arc)), lambda c, n: "Dark" if (n.z < -0.3 or n.y > 0.45) and abs(c.x) < W * 0.95 else plank(c, n), tuple(hub), 0, False)
    for x in (-0.6, 0.6):
        band = [(x + dx, math.cos(math.pi * k / 8) * (D + 0.02), math.sin(math.pi * k / 8) * 0.47) for k in range(9) for dx in (-0.06, 0.06)]
        P.part("SwayLid", lidshape(hull(band)), "Metal", tuple(hub), 0, False)
    P.part("SwayLid", lidshape(box((0, D + 0.03, 0.08), (0.28, 0.06, 0.3))), "Trim", tuple(hub), 0, False)
    P.part("SwayLid", lidshape(box((0, D + 0.065, 0.06), (0.05, 0.02, 0.1))), "Dark", tuple(hub), 0, False)
    for k in range(9):   # the teeth of the lid, pointing down
        x = -W * 0.85 + k * W * 1.7 / 8
        P.part("SwayLid", lidshape(cone((x, D - 0.05, 0.02), (x, D - 0.08, -0.22 + 0.05 * (k % 2)), 0.07, 5)), "Belly", tuple(hub), 0, False)
    for s in (1, -1):   # the eyes glowing under the lid
        P.part("SwayLid", lidshape(ball((s * 0.35, 0.05, 0.05), (0.13, 0.1, 0.08), 10, 5)), "Lamp", tuple(hub), 0)
        P.part("SwayLid", lidshape(ball((s * 0.35, 0.1, 0.0), (0.05, 0.05, 0.05), 8, 4)), "Dark", tuple(hub), 0)
    for k in range(9):   # the lower teeth
        x = -W * 0.85 + k * W * 1.7 / 8
        P.obj("Tooth", cone((x, D - 0.06, -0.02), (x, D - 0.05, 0.2 - 0.05 * (k % 2)), 0.07, 5), "Belly", 0, False)
    # the tongue lolling out over the front, the gold spilling
    P.obj("Tongue", pipe(bez((0, 0.1, 0.05), (0, 0.8, 0.3), (0, 1.25, 0.1), (0, 1.35, -0.35), 8), [0.2, 0.22, 0.22, 0.2, 0.18, 0.16, 0.14, 0.12, 0.1], 10), "Glass", 1)
    for v in P.parts[-1].data.vertices: v.co.z = v.co.z * 0.55 + 0.05
    gold_heap(P, (0.35, -0.1, 0.0), 0.45, 0.4, 0.22, 14, rng)
    gold_heap(P, (-0.4, -0.15, 0.0), 0.4, 0.35, 0.18, 12, rng)
    for k in range(10):   # coins tumbling out of the corners of its mouth
        s = 1 if k % 2 else -1
        p = Vector((s * rng.uniform(0.55, 0.85), D + 0.1 + rng.uniform(0, 0.2), -0.1 - k * 0.07))
        P.obj("Coin", coin(p, 0.08, 0.025, rrot(rng)), "Trim", 0, False)
    # bat wings
    for s in (1, -1):
        name = "FlapR" if s > 0 else "FlapL"
        hub = Vector((s * W, -0.1, -0.1))
        tips = [hub + Vector((s * 0.35, 0.25, 0.6)), hub + Vector((s * 0.95, 0.15, 0.5)), hub + Vector((s * 1.25, -0.1, 0.15)), hub + Vector((s * 1.05, -0.35, -0.2)), hub + Vector((s * 0.5, -0.45, -0.25))]
        P.part(name, fan(hub, tips, 0.03, 0.22), "Accent", tuple(hub), 0, False)
        for t in tips[:-1]: P.part(name, pipe([hub, t], [0.05, 0.02], 6), "Dark", tuple(hub), 0, False)
    P.part("Muzzle", ball((0, 0.5, 0.15), (0.08, 0.05, 0.06), 8, 4), "Glow", (0, 0.5, 0.15))
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


BOSSES = [("parrot", T_parrot), ("mimic", T_mimic), ("ghost", T_ghost), ("crab", T_crab), ("skull", T_skull)]

if __name__ == "__main__":
    os.makedirs(AB.OUT, exist_ok=True)
    for bid, fn in BOSSES:
        if ONLY and bid not in ONLY: continue
        fn().finish()
    print("DONE")
