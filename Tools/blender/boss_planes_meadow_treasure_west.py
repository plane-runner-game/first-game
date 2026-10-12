# Sky Squad, enemy planes styled on their world's bosses (2026-10-12, the user: "two planes for every level, inspired by the bosses - show
# me the pictures first"): meadow (the bumble buzzer, the ladybug lancer), treasure island (the parrot privateer, the ghost galleon) and the
# wild west (the thunderbird totem, the scorpion stinger). Same conventions as enemy_planes.py: +Y nose, +Z up, +X right wing, "Body" plus
# "Prop<n>" spinning about the nose, Plane.finish() stretches the body 1.3x in Z, centres it and exports Enemy_<id>.fbx.
# Run: blender -b -P Tools/blender/boss_planes_meadow_treasure_west.py -- <out dir> [export] [ids,comma,separated]
import bpy, bmesh, math, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mathutils import Vector, Matrix
import enemy_planes as EP
from enemy_planes import Plane, loft, sweep, lathe, box, hull, tube, mirror_x, airfoil
from alien_bosses import xf, ball, pipe, cone, bez, torus, sheet

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ONLY = argv[2].split(",") if len(argv) > 2 and argv[2] else None


def pilot(P, c, helmet="Dark", goggles="Glass"):
    """a little pilot in the cockpit: head, helmet, goggles."""
    c = Vector(c)
    P.obj("PilotHead", ball(tuple(c), (0.13, 0.13, 0.14), 10, 5), "Belly")
    P.obj("Helmet", ball(tuple(c + Vector((0, -0.02, 0.05))), (0.145, 0.14, 0.11), 10, 5), helmet)
    P.obj("Goggles", ball(tuple(c + Vector((0, 0.12, 0.03))), (0.12, 0.03, 0.04), 8, 4), goggles)

def flat(pts, thick=0.04):
    """a flat polygon (in any plane) made into a thin slab: a convex hull of the points pushed both ways along its normal."""
    v = [Vector(p) for p in pts]
    n = (v[1] - v[0]).cross(v[2] - v[0]).normalized()
    return hull([tuple(p + n * thick * 0.5) for p in v] + [tuple(p - n * thick * 0.5) for p in v])

def eye(P, c, r, iris="Dark", white="Accent", glint="Lamp", side=1):
    c = Vector(c)
    P.obj("Eye", ball(tuple(c), (r, r * 0.6, r), 10, 5), white)
    P.obj("Pupil", ball(tuple(c + Vector((side * r * 0.25, r * 0.5, 0))), (r * 0.55, r * 0.25, r * 0.6), 8, 4), iris)
    P.obj("Glint", ball(tuple(c + Vector((side * r * 0.35, r * 0.68, r * 0.3))), (r * 0.15, r * 0.06, r * 0.15), 6, 3), glint)


# ================================================================= MEADOW 1: the bumble buzzer (the queen bumblebee)
def P_meadow():
    """A round bumblebee of a plane: a fat fuzzy body striped yellow and black, big glossy black eyes either side of a honey-gold propeller,
    curly antennae over the canopy, four glassy wings with dark veins, and a black stinger for a tail with a glowing honey tip."""
    P = Plane("meadow", {"Base": ((1.0, 0.78, 0.10), 0.35), "Belly": ((1.0, 0.86, 0.70), 0.3), "Accent": ((0.97, 0.97, 0.97), 0.5),
                         "Trim": ((0.95, 0.60, 0.08), 0.6), "Glass": ((0.75, 0.92, 1.0), 0.95), "Dark": ((0.07, 0.06, 0.05), 0.4),
                         "Glow": ((1.0, 0.70, 0.15), 0.5), "Metal": ((0.65, 0.62, 0.55), 0.6), "Lamp": ((1.0, 0.95, 0.75), 0.8)})
    stripes = lambda c, n: "Dark" if c.y < 1.2 and (c.y * 1.55) % 1.0 < 0.42 else "Base"
    P.obj("Fuselage", loft([(1.95, 0.25, 0.25, 0, 0.0), (1.7, 0.55, 0.55, 0, 0.0), (1.0, 0.78, 0.78, 0, 0.0), (0.0, 0.82, 0.8, 0, 0.0),
                            (-1.0, 0.7, 0.68, 0, 0.04), (-1.8, 0.4, 0.4, 0, 0.1), (-2.2, 0.12, 0.12, 0, 0.14)], 16), stripes, 1)
    P.obj("Stinger", cone((0, -2.15, 0.14), (0, -2.75, 0.2), 0.13, 8), "Dark", 0, False)
    P.obj("StingTip", ball((0, -2.78, 0.2), (0.06, 0.06, 0.06), 6, 3), "Glow")
    for s in (1, -1):   # the big glossy eyes flank the nose
        P.obj("BugEye", ball((s * 0.45, 1.55, 0.18), (0.3, 0.3, 0.36), 12, 6), "Dark")
        P.obj("EyeShine", ball((s * 0.52, 1.8, 0.33), (0.08, 0.04, 0.08), 6, 3), "Lamp")
        ant = bez((s * 0.18, 1.2, 0.72), (s * 0.3, 1.5, 1.2), (s * 0.6, 1.6, 1.35), (s * 0.7, 1.4, 1.5), 6)
        P.obj("Antenna", pipe(ant, [0.04] * 6 + [0.03], 6), "Dark")
        P.obj("AntennaTip", ball(tuple(ant[-1]), (0.09, 0.09, 0.09), 8, 4), "Glow")
        P.obj("Gun", tube(0.9, 1.75, 0.05, 0.045, s * 0.62, -0.45, 8), "Dark", 0)
    # four glassy wings with dark veins, held up a little
    for (le, te, span, z, k) in ((0.75, -0.35, 2.7, 0.55, 1.0), (-0.35, -1.15, 2.0, 0.45, 0.8)):
        for s in (1, -1):
            pts = [(s * 0.55, le, z), (s * span * 0.55, le + 0.25 * k, z + 0.3 * k), (s * span, le - 0.15, z + 0.45 * k), (s * span * 1.02, te + 0.2, z + 0.4 * k), (s * span * 0.6, te, z + 0.2 * k), (s * 0.55, te + 0.15, z)]
            P.obj("BeeWing", flat(pts, 0.03), "Glass", 0, False)
            for t in (pts[1], pts[2], pts[3]):
                P.obj("Vein", pipe([pts[0], t], [0.025, 0.012], 4), "Dark")
    P.obj("Canopy", ball((0, 0.85, 0.72), (0.34, 0.5, 0.26), 12, 6), "Glass")
    pilot(P, (0, 0.8, 0.82), "Trim")
    P.wing([(0.1, -1.55, -2.0, 0.06, 0.2), (0.85, -1.7, -2.0, 0.04, 0.25)], lambda c, n: "Dark", name="Stab")
    P.prop((0, 2.0, 0.0), 0.95, 3, chord=0.16, blade="Trim", tip="Dark", spinner="Glow", spinner_len=0.3)
    return P


# ================================================================= MEADOW 2: the ladybug lancer (the giant ladybug, the emerald dragonfly)
def P_meadow2():
    """A ladybug knight's fighter: a domed red shell with black spots for a body, split down the middle, a black head on the nose with big
    white eyes and two little antennae, emerald dragonfly wings out to the sides, a golden lance gun under the nose and twin props."""
    P = Plane("meadow2", {"Base": ((0.88, 0.10, 0.08), 0.6), "Belly": ((0.12, 0.10, 0.10), 0.4), "Accent": ((0.97, 0.97, 0.97), 0.5),
                          "Trim": ((1.0, 0.80, 0.25), 0.85), "Glass": ((0.35, 0.95, 0.55), 0.95), "Dark": ((0.05, 0.05, 0.05), 0.4),
                          "Glow": ((0.30, 1.0, 0.55), 0.5), "Metal": ((0.62, 0.62, 0.66), 0.7), "Lamp": ((1.0, 0.95, 0.75), 0.8)})
    spots = [(0.45, 0.3), (0.8, -0.35), (0.35, -0.95), (0.95, 0.65), (0.15, 0.85), (0.75, -1.25)]
    def shell(c, n):
        if c.z < 0.05: return "Belly"
        if abs(c.x) < 0.04: return "Dark"   # the split
        for (x, y) in spots:
            if math.hypot(abs(c.x) - x, c.y - y) < 0.2: return "Dark"
        return "Base"
    P.obj("Shell", ball((0, -0.25, 0.05), (1.05, 1.55, 0.72), 18, 9), shell, 0)
    P.obj("Underside", ball((0, -0.25, -0.05), (0.9, 1.4, 0.32), 14, 6), "Belly", 0)
    P.obj("Head", ball((0, 1.3, 0.05), (0.52, 0.42, 0.42), 14, 7), "Belly", 1)
    for s in (1, -1):
        eye(P, (s * 0.24, 1.6, 0.18), 0.17, side=s)
        P.obj("Cheek", ball((s * 0.24, 1.68, 0.18), (0.18, 0.02, 0.18), 10, 4), "Accent")
        P.obj("Antenna", pipe(bez((s * 0.15, 1.45, 0.4), (s * 0.25, 1.6, 0.75), (s * 0.4, 1.55, 0.85), (s * 0.5, 1.45, 0.9), 5), [0.035] * 5 + [0.025], 6), "Dark")
        P.obj("AntennaTip", ball((s * 0.5, 1.45, 0.92), (0.08, 0.08, 0.08), 6, 3), "Trim")
        # emerald dragonfly wings: two each side, glassy with gold edges
        for (y0, sp, back) in ((0.45, 2.75, 0.0), (-0.45, 2.4, 0.3)):
            root = Vector((s * 0.9, y0, 0.15))
            pts = [root + Vector((0, 0.18, 0)), root + Vector((s * sp * 0.5, 0.28 - back * 0.5, 0.08)), root + Vector((s * sp, 0.05 - back, 0.15)),
                   root + Vector((s * sp * 0.95, -0.28 - back, 0.14)), root + Vector((s * sp * 0.45, -0.3 - back * 0.5, 0.06)), root + Vector((0, -0.18, 0))]
            P.obj("FlyWing", flat([tuple(p) for p in pts], 0.03), "Glass", 0, False)
            P.obj("WingEdge", pipe(pts[1:4], [0.025, 0.025, 0.025], 4), "Trim")
            P.obj("WingSpot", ball(tuple(pts[2] * 0.9 + root * 0.1), (0.1, 0.08, 0.03), 6, 3), "Glow")
        # the twin props on pods under the wings
        P.obj("Pod", loft([(1.55, 0.06, 0.06, s * 1.35, -0.1), (1.35, 0.17, 0.17, s * 1.35, -0.1), (0.2, 0.17, 0.17, s * 1.35, -0.1), (-0.3, 0.06, 0.06, s * 1.35, -0.1)], 10), "Base", 0)
        P.prop((s * 1.35, 1.58, -0.1), 0.55, 3, chord=0.11, blade="Dark", tip="Trim", spinner="Trim", spinner_len=0.18)
        for k in range(3):   # little legs tucked under
            P.obj("Leg", pipe([(s * 0.45, 0.5 - k * 0.5, -0.25), (s * 0.7, 0.45 - k * 0.5, -0.45), (s * 0.65, 0.55 - k * 0.5, -0.6)], [0.04, 0.035, 0.02], 5), "Dark")
    P.obj("Lance", pipe([(0, 0.9, -0.42), (0, 1.6, -0.42), (0, 2.7, -0.42)], [0.11, 0.07, 0.0], 8), "Trim")
    P.obj("LanceGuard", lathe([(0.0, 0.85), (0.24, 0.9), (0.2, 1.0), (0.0, 1.02)], 10, "y", (0, 0, -0.42)), "Trim")
    P.obj("Canopy", ball((0, 0.55, 0.62), (0.3, 0.42, 0.24), 12, 6), "Glass")
    pilot(P, (0, 0.5, 0.7), "Base")
    P.fin([(0.0, -1.35, -1.85, 0.06), (0.45, -1.6, -1.9, 0.05)], 0.0, 0.45, 0, "Dark")
    return P


# ================================================================= TREASURE 1: the parrot privateer (captain parrot)
def P_treasure():
    """A scarlet macaw of a plane: a red body with a yellow and blue belly, a hooked golden beak for a nose around the propeller, big eyes,
    a pirate pilot under a black tricorn with a skull, wings of red, yellow and blue layered feathers, a fanned feather tail, gold coins."""
    P = Plane("treasure", {"Base": ((0.90, 0.12, 0.10), 0.5), "Belly": ((1.0, 0.82, 0.16), 0.45), "Accent": ((0.12, 0.40, 0.92), 0.5),
                           "Trim": ((1.0, 0.80, 0.26), 0.85), "Glass": ((0.62, 0.86, 1.0), 0.9), "Dark": ((0.07, 0.06, 0.09), 0.4),
                           "Glow": ((1.0, 0.85, 0.30), 0.5), "Metal": ((0.92, 0.92, 0.9), 0.5), "Lamp": ((1.0, 0.95, 0.8), 0.8)})
    P.obj("Fuselage", loft([(1.7, 0.42, 0.42, 0, 0.0), (1.2, 0.58, 0.6, 0, 0.0), (0.2, 0.6, 0.62, 0, 0.02), (-1.0, 0.42, 0.45, 0, 0.06), (-2.0, 0.12, 0.14, 0, 0.12)], 16),
          lambda c, n: "Belly" if n.z < -0.45 else "Base", 1)
    # the beak: upper hooked gold, lower dark, the prop between
    P.obj("Beak", pipe(bez((0, 1.55, 0.3), (0, 2.0, 0.42), (0, 2.35, 0.25), (0, 2.38, -0.05), 6), [0.32, 0.3, 0.24, 0.16, 0.1, 0.05, 0.0], 10), "Trim")
    P.obj("LowerBeak", pipe(bez((0, 1.55, -0.28), (0, 1.85, -0.32), (0, 2.0, -0.28), (0, 2.05, -0.2), 4), [0.25, 0.2, 0.14, 0.08, 0.0], 8), "Dark")
    P.obj("FacePatch", ball((0, 1.45, 0.05), (0.5, 0.2, 0.48), 12, 6), "Metal")
    for s in (1, -1):
        eye(P, (s * 0.38, 1.45, 0.3), 0.16, white="Metal", glint="Lamp", side=s)
        P.obj("Gun", tube(0.9, 1.9, 0.045, 0.04, s * 0.55, -0.35, 8), "Dark", 0)
    # wings: three layers of feathers, red over yellow over blue, the tips spread
    for s in (1, -1):
        for layer, (paint, reach, y0) in enumerate((("Accent", 3.0, 0.15), ("Belly", 2.55, 0.35), ("Base", 2.05, 0.55))):
            z = 0.06 + layer * 0.05
            n = 7
            for k in range(n):
                t = k / (n - 1)
                root = Vector((s * (0.5 + t * (reach - 0.9) * 0.55), y0 - t * 0.35, z))
                tip = Vector((s * (0.6 + t * (reach - 0.6)), y0 - 0.65 - t * 0.55, z + t * 0.12))
                w = 0.2
                P.obj("Feather", flat([tuple(root + Vector((0, w, 0))), tuple(root - Vector((0, w * 0.5, 0))), tuple(tip - Vector((0, 0.05, 0))), tuple(tip + Vector((s * 0.12, 0.25, 0)))], 0.035), paint, 0, False)
    # the fanned tail feathers
    for k in range(5):
        a = math.radians(-40 + 20 * k)
        root = Vector((0, -1.85, 0.12)); tip = root + Vector((math.sin(a) * 0.75, -1.0, 0.1 + 0.05 * abs(k - 2)))
        P.obj("TailFeather", pipe([root, (root + tip) * 0.5, tip], [0.05, 0.15, 0.0], 6), "Accent" if k % 2 else "Base")
    P.fin([(0.0, -1.3, -1.9, 0.06), (0.5, -1.6, -1.95, 0.05)], 0.0, 0.3, 0, "Base")
    # the pirate pilot: a tricorn with a skull badge
    # an open cockpit: the pirate pilot sits up in it under a big black tricorn with a skull
    P.obj("CockpitRim", torus(0.3, 0.05, 0.0, 16, 5), "Trim"); P.parts[-1].data.transform(Matrix.Translation((0, 0.35, 0.58)))
    P.obj("Coat", ball((0, 0.33, 0.62), (0.22, 0.18, 0.16), 10, 5), "Accent")
    pilot(P, (0, 0.35, 0.8), "Dark")
    tri = [Vector((math.sin(a) * 0.36, 0.35 + math.cos(a) * 0.36, 0.9)) for a in (0.0, 2.1, 4.2)]
    P.obj("Tricorn", hull([tuple(p) for p in tri] + [tuple(p + Vector((0, 0, 0.1))) for p in tri] + [(0, 0.33, 1.12)]), "Dark", 0, False)
    P.obj("TricornTrim", pipe(tri + [tri[0]], [0.025] * 4, 4), "Trim")
    P.obj("Skull", ball((0, 0.66, 0.98), (0.07, 0.03, 0.07), 6, 3), "Metal")
    P.obj("Plume", pipe(bez((0.15, 0.25, 1.0), (0.25, 0.1, 1.3), (0.1, -0.2, 1.4), (-0.05, -0.35, 1.35), 5), [0.05, 0.07, 0.06, 0.04, 0.02, 0.0], 6), "Accent")
    P.obj("EyePatch", ball((0.06, 0.47, 0.84), (0.05, 0.02, 0.05), 6, 3), "Dark")
    for k in range(3):   # gold coins flipping off the wing tips
        P.obj("Coin", lathe([(0.0, -0.02), (0.12, -0.02), (0.12, 0.02), (0.0, 0.02)], 10, "x", ((-1) ** k * (1.2 + 0.5 * k), -0.9 - 0.3 * k, -0.35)), "Trim")
    P.prop((0, 2.05, 0.05), 0.85, 3, chord=0.14, blade="Dark", tip="Belly", spinner="Base", spinner_len=0.15)
    return P


# ================================================================= TREASURE 2: the ghost galleon (ghost captain, dread skull, cannon crab)
def P_treasure2():
    """A ghost-ship jet: a dark wooden hull with a gold rail, a skull figurehead with green fire in its eyes on the bow, tattered ghostly sails
    for wings with a skull-and-crossbones, cannons poking from the gun ports, a lantern on the stern, green ghost-fire jets behind."""
    P = Plane("treasure2", {"Base": ((0.32, 0.20, 0.12), 0.35), "Belly": ((0.20, 0.13, 0.08), 0.3), "Accent": ((0.88, 0.94, 0.90), 0.5),
                            "Trim": ((1.0, 0.80, 0.26), 0.85), "Glass": ((0.55, 1.0, 0.80), 0.9), "Dark": ((0.05, 0.05, 0.06), 0.4),
                            "Glow": ((0.30, 1.0, 0.60), 0.5), "Metal": ((0.40, 0.40, 0.44), 0.7), "Lamp": ((1.0, 0.85, 0.40), 0.8)})
    planks = lambda c, n: "Belly" if (c.z * 6) % 1.0 < 0.12 else "Base"
    P.obj("Hull", loft([(2.0, 0.08, 0.2, 0, 0.0), (1.6, 0.42, 0.45, 0, -0.05), (0.5, 0.6, 0.55, 0, -0.08), (-1.0, 0.58, 0.55, 0, -0.06), (-1.9, 0.48, 0.5, 0, 0.0)], 16, sq=1.6), planks, 0)
    P.obj("Deck", box((0, -0.1, 0.42), (1.05, 3.7, 0.06)), "Belly", 0, False)
    for s in (1, -1):
        P.obj("Rail", pipe([(s * 0.52, 1.6, 0.5), (s * 0.58, 0.3, 0.52), (s * 0.55, -1.85, 0.6)], [0.035] * 3, 5), "Trim")
        for k in range(3):   # cannons from the gun ports
            y = 0.9 - k * 0.75
            P.obj("Port", box((s * 0.6, y, 0.05), (0.04, 0.22, 0.2)), "Dark", 0, False)
            P.obj("Cannon", tube(y - 0.05, y + 0.45, 0.07, 0.065, s * 0.66, 0.05, 8), "Metal", 0)
            P.obj("Muzzle", ball((s * 0.66, y + 0.46, 0.05), (0.08, 0.03, 0.08), 6, 3), "Glow")
    P.obj("Stern", box((0, -1.75, 0.7), (1.05, 0.5, 0.6)), lambda c, n: "Trim" if c.z > 0.95 else "Base", 0, False)
    for s in (1, -1):
        P.obj("SternWindow", box((s * 0.25, -2.0, 0.7), (0.18, 0.03, 0.2)), "Lamp", 0, False)
    P.obj("Lantern", lathe([(0.0, 1.05), (0.1, 1.08), (0.11, 1.3), (0.0, 1.38)], 8, "z", (0, -1.75, 0)), "Glow")
    # the skull figurehead on the bow
    P.obj("SkullHead", ball((0, 2.05, 0.3), (0.32, 0.3, 0.34), 12, 6), "Accent", 1)
    P.obj("SkullJaw", box((0, 2.15, 0.02), (0.36, 0.25, 0.14)), "Accent", 0, False)
    for s in (1, -1):
        P.obj("Socket", ball((s * 0.13, 2.3, 0.36), (0.1, 0.06, 0.1), 8, 4), "Dark")
        P.obj("GhostFire", cone((s * 0.13, 2.34, 0.36), (s * 0.15, 2.28, 0.6), 0.07, 6), "Glow", 0, False)
    for k in range(5):
        P.obj("Tooth", box(((k - 2) * 0.07, 2.3, 0.12), (0.05, 0.03, 0.07)), "Accent", 0, False)
    # tattered ghost sails as wings, on spars, a jolly roger on the right
    for s in (1, -1):
        for (y, span, h) in ((0.55, 3.0, 0.5), (-0.65, 2.4, 0.4)):
            pts = [(s * 0.55, y + 0.25, 0.3), (s * span, y + 0.05, 0.4 + h * 0.2), (s * span * 0.85, y - 0.5, 0.35), (s * span * 0.6, y - 0.35, 0.3),
                   (s * span * 0.45, y - 0.6, 0.3), (s * 0.55, y - 0.4, 0.28)]
            P.obj("Sail", flat(pts, 0.03), "Glass", 0, False)
            P.obj("Spar", pipe([pts[0], pts[1]], [0.04, 0.03], 5), "Base")
        P.obj("Jet", loft([(-1.6, 0.18, 0.18, s * 0.35, -0.25), (-2.15, 0.15, 0.15, s * 0.35, -0.25)], 10), "Metal", 0)
        P.obj("GhostJet", cone((s * 0.35, -2.15, -0.25), (s * 0.35, -2.75, -0.25), 0.13, 8), "Glow", 0, False)
    P.obj("Mast", pipe([(0, 0.4, 0.45), (0, 0.4, 1.6)], [0.05, 0.04], 6), "Base")
    P.obj("Flag", flat([(0.02, 0.38, 1.55), (0.02, -0.25, 1.5), (0.02, -0.2, 1.2), (0.02, 0.38, 1.22)], 0.025), "Dark", 0, False)
    P.obj("FlagSkull", ball((0.05, 0.08, 1.38), (0.03, 0.07, 0.07), 6, 3), "Accent")
    for a in (1, -1):
        P.obj("Bone", pipe([(0.05, 0.08 - 0.13 * a, 1.27), (0.05, 0.08 + 0.13 * a, 1.48)], [0.018, 0.018], 4), "Accent")
    P.obj("Canopy", ball((0, 1.05, 0.55), (0.28, 0.38, 0.22), 12, 6), "Glass")
    pilot(P, (0, 1.0, 0.62), "Dark", "Glow")
    return P


# ================================================================= WEST 1: the thunderbird totem (the thunderbird)
def P_west():
    """A thunderbird of a plane: a cobalt body painted with red and turquoise totem bands, an eagle head on the nose with a gold hooked beak
    and fierce eyes, a feathered war bonnet behind the canopy, broad swept wings with lightning zigzags and fingered feather tips, two
    propellers in the wings, and glowing lightning down the tail."""
    P = Plane("west", {"Base": ((0.12, 0.30, 0.78), 0.5), "Belly": ((0.95, 0.93, 0.88), 0.4), "Accent": ((0.88, 0.20, 0.14), 0.5),
                       "Trim": ((1.0, 0.80, 0.26), 0.85), "Glass": ((0.62, 0.88, 1.0), 0.9), "Dark": ((0.07, 0.07, 0.10), 0.4),
                       "Glow": ((0.40, 0.95, 1.0), 0.5), "Metal": ((0.15, 0.80, 0.75), 0.6), "Lamp": ((1.0, 0.95, 0.8), 0.8)})
    def totem(c, n):
        if n.z < -0.5: return "Belly"
        b = (c.y * 1.4) % 1.0
        if b < 0.12: return "Accent"
        if b < 0.2: return "Metal"
        return "Base"
    P.obj("Fuselage", loft([(1.6, 0.4, 0.42, 0, 0.0), (0.9, 0.52, 0.55, 0, 0.0), (-0.4, 0.46, 0.5, 0, 0.04), (-1.6, 0.25, 0.28, 0, 0.1), (-2.3, 0.08, 0.1, 0, 0.14)], 14), totem, 1)
    # the eagle head
    P.obj("EagleHead", ball((0, 1.75, 0.15), (0.45, 0.5, 0.45), 12, 6), "Belly", 1)
    P.obj("Beak", pipe(bez((0, 2.05, 0.25), (0, 2.45, 0.28), (0, 2.65, 0.05), (0, 2.55, -0.18), 6), [0.2, 0.18, 0.14, 0.1, 0.06, 0.03, 0.0], 8), "Trim")
    for s in (1, -1):
        eye(P, (s * 0.24, 2.05, 0.32), 0.11, white="Lamp", side=s)
        P.obj("Brow", hull([(s * 0.06, 2.12, 0.47), (s * 0.4, 1.98, 0.5), (s * 0.4, 1.95, 0.44), (s * 0.08, 2.08, 0.4)]), "Dark", 0, False)
        P.obj("FaceStripe", box((s * 0.36, 1.9, 0.15), (0.06, 0.25, 0.08)), "Accent", 0, False)
    # the war bonnet: a fan of white feathers with red tips behind the canopy
    for k in range(9):
        a = math.radians(-60 + 15 * k)
        b = Vector((math.sin(a) * 0.3, 0.05, 0.72 + math.cos(a) * 0.1))
        tip = b + Vector((math.sin(a) * 0.45, -0.25, math.cos(a) * 0.55))
        P.obj("Bonnet", pipe([b, (b + tip) * 0.5, tip], [0.05, 0.07, 0.0], 5), "Belly")
        P.obj("BonnetTip", ball(tuple(tip), (0.05, 0.05, 0.06), 6, 3), "Accent")
    P.obj("Band", pipe(bez((-0.32, 0.1, 0.68), (-0.15, 0.2, 0.78), (0.15, 0.2, 0.78), (0.32, 0.1, 0.68), 6), [0.04] * 7, 5), "Metal")
    P.obj("Canopy", ball((0, 0.7, 0.55), (0.3, 0.42, 0.24), 12, 6), "Glass")
    pilot(P, (0, 0.65, 0.65), "Accent")
    # broad wings with zigzag lightning and fingered feather tips
    def wpaint(c, n):
        if n.z < -0.3: return "Belly"
        x = abs(c.x)
        if abs(((x * 2.2) % 1.0) - 0.5) * 0.6 + 0.05 > abs(c.y - 0.05) and 0.7 < x < 2.4: return "Glow"   # the zigzag
        return "Accent" if x > 2.3 else "Base"
    P.wing([(0.3, 0.75, -0.5, 0.14, 0.0), (1.4, 0.6, -0.55, 0.1, 0.12), (2.5, 0.35, -0.5, 0.07, 0.3)], wpaint)
    for s in (1, -1):
        for k in range(5):
            root = Vector((s * 2.5, 0.25 - k * 0.18, 0.3))
            tip = root + Vector((s * (0.55 - abs(k - 2) * 0.08), 0.1 - k * 0.12, 0.08))
            P.obj("WingFinger", pipe([root, (root + tip) * 0.5, tip], [0.06, 0.07, 0.0], 5), "Dark" if k % 2 else "Belly")
        P.obj("Nacelle", loft([(1.2, 0.08, 0.08, s * 1.3, -0.05), (1.0, 0.2, 0.2, s * 1.3, -0.05), (-0.4, 0.17, 0.17, s * 1.3, -0.05), (-0.8, 0.06, 0.06, s * 1.3, -0.05)], 10),
              lambda c, n: "Metal" if c.y > 0.9 else "Accent", 0)
        P.prop((s * 1.3, 1.25, -0.05), 0.6, 3, chord=0.12, blade="Dark", tip="Trim", spinner="Trim", spinner_len=0.18)
    P.wing([(0.1, -1.7, -2.2, 0.06, 0.15), (0.95, -1.9, -2.25, 0.04, 0.2)], lambda c, n: "Accent", name="Stab")
    P.fin([(0.0, -1.55, -2.35, 0.07), (0.7, -1.9, -2.4, 0.05)], 0.0, 0.2, 0, lambda c, n: "Glow" if abs(((c.z * 3) % 1.0) - (c.y % 0.5)) < 0.12 else "Base")
    return P


# ================================================================= WEST 2: the scorpion stinger (the scorpion king, the rattlesnake)
def P_west2():
    """A scorpion of a plane: a crimson armoured body in gold-trimmed plates, two pincer guns reaching forward, a segmented tail arching up
    over the canopy with a glowing stinger cannon aimed ahead, a jewelled gold crown on the pilot's helmet, short angular wings with
    rattlesnake diamond patterns and twin propellers."""
    P = Plane("west2", {"Base": ((0.62, 0.10, 0.08), 0.5), "Belly": ((0.95, 0.80, 0.55), 0.4), "Accent": ((0.30, 0.06, 0.05), 0.4),
                        "Trim": ((1.0, 0.80, 0.26), 0.85), "Glass": ((0.62, 0.88, 1.0), 0.9), "Dark": ((0.10, 0.06, 0.06), 0.4),
                        "Glow": ((1.0, 0.85, 0.25), 0.5), "Metal": ((0.25, 0.85, 0.85), 0.6), "Lamp": ((1.0, 0.95, 0.8), 0.8)})
    def plates(c, n):
        if n.z < -0.5: return "Belly"
        return "Trim" if (c.y * 2.5) % 1.0 < 0.1 else "Base"
    P.obj("Fuselage", loft([(1.8, 0.2, 0.2, 0, 0.0), (1.4, 0.48, 0.38, 0, 0.0), (0.4, 0.62, 0.45, 0, 0.0), (-0.8, 0.55, 0.42, 0, 0.0), (-1.6, 0.3, 0.3, 0, 0.05)], 14, sq=1.4), plates, 1)
    for s in (1, -1):
        eye(P, (s * 0.22, 1.6, 0.25), 0.1, white="Glow", side=s)
        # the pincer guns
        arm = [Vector((s * 0.5, 1.1, -0.15)), Vector((s * 0.85, 1.6, -0.2)), Vector((s * 0.75, 2.15, -0.2))]
        P.obj("Arm", pipe(arm, [0.13, 0.11, 0.1], 8), "Base")
        cl = arm[-1]
        P.obj("Claw", ball(tuple(cl + Vector((0, 0.15, 0))), (0.2, 0.25, 0.15), 10, 5), "Base", 1)
        for k in (1, -1):
            P.obj("Pincer", pipe(bez(cl + Vector((k * 0.08, 0.3, 0)), cl + Vector((k * 0.2, 0.55, 0)), cl + Vector((k * 0.12, 0.75, 0)), cl + Vector((-k * 0.02, 0.8, 0)), 4), [0.08, 0.07, 0.05, 0.03, 0.0], 6), "Dark")
        P.obj("ClawGun", tube(2.2, 2.95, 0.045, 0.04, s * 0.75, -0.2, 6), "Metal", 0)
        for k in range(3):   # legs folded under
            y = 0.6 - k * 0.5
            P.obj("Leg", pipe([(s * 0.5, y, -0.2), (s * 0.85, y + 0.05, -0.35), (s * 0.9, y + 0.15, -0.6)], [0.05, 0.04, 0.02], 5), "Accent")
        P.obj("Nacelle", loft([(1.0, 0.07, 0.07, s * 1.45, 0.0), (0.85, 0.17, 0.17, s * 1.45, 0.0), (-0.5, 0.15, 0.15, s * 1.45, 0.0), (-0.8, 0.06, 0.06, s * 1.45, 0.0)], 10), "Accent", 0)
        P.prop((s * 1.45, 1.05, 0.0), 0.55, 3, chord=0.11, blade="Dark", tip="Trim", spinner="Trim", spinner_len=0.16)
    # angular wings with rattlesnake diamonds
    def diamonds(c, n):
        if n.z < -0.3: return "Belly"
        u, v = abs(c.x) * 2.2, c.y * 2.2
        return "Trim" if abs((u % 1.0) - 0.5) + abs((v % 1.0) - 0.5) < 0.25 else "Base"
    P.wing([(0.4, 0.55, -0.6, 0.12, 0.0), (1.6, 0.3, -0.55, 0.09, 0.05), (2.5, -0.05, -0.45, 0.06, 0.1)], diamonds)
    # the segmented tail arching over, the stinger cannon aimed ahead
    tail = bez((0, -1.5, 0.15), (0, -2.4, 0.6), (0, -2.0, 1.7), (0, -0.7, 1.75), 9)
    for i, p in enumerate(tail):
        r = 0.24 - i * 0.014
        P.obj("TailSeg", ball(tuple(p), (r, r * 0.9, r), 10, 5), "Base" if i % 2 else "Trim")
    tip = tail[-1]
    P.obj("Stinger", pipe([tip, tip + Vector((0, 0.3, -0.05)), tip + Vector((0, 0.6, -0.2))], [0.16, 0.1, 0.0], 8), "Dark")
    P.obj("StingGlow", ball(tuple(tip + Vector((0, 0.62, -0.21))), (0.08, 0.08, 0.08), 6, 3), "Glow")
    # the canopy and the crowned pilot
    P.obj("Canopy", ball((0, 0.7, 0.42), (0.3, 0.42, 0.24), 12, 6), "Glass")
    pilot(P, (0, 0.65, 0.52), "Accent")
    P.obj("Crown", lathe([(0.12, 0.66), (0.14, 0.66), (0.14, 0.76), (0.12, 0.76)], 12, "z", (0, 0.63, 0)), "Trim")
    for k in range(5):
        a = 2 * math.pi * k / 5
        P.obj("CrownPoint", cone((math.sin(a) * 0.13, 0.63 + math.cos(a) * 0.13, 0.75), (math.sin(a) * 0.14, 0.63 + math.cos(a) * 0.14, 0.88), 0.03, 4), "Trim", 0, False)
    P.obj("CrownGem", ball((0, 0.77, 0.72), (0.03, 0.02, 0.03), 6, 3), "Metal")
    return P


PLANES = [("meadow", P_meadow), ("meadow2", P_meadow2), ("treasure", P_treasure), ("treasure2", P_treasure2), ("west", P_west), ("west2", P_west2)]

if __name__ == "__main__":
    os.makedirs(EP.OUT, exist_ok=True)
    for pid, fn in PLANES:
        if ONLY and pid not in ONLY: continue
        fn().finish()
    print("DONE")
