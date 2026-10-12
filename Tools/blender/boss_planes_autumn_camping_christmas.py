# Sky Squad, enemy planes styled on each world's bosses (2026-10-12: "for every level two planes inspired by the bosses - show me the
# pictures before you put them in"): autumn, camping and christmas. Same conventions as enemy_planes.py (whose Plane class builds them):
# +Y = nose, +Z = up, +X = right wing; "Prop<n>" spin about the nose axis; one "Body" for the rest; slots <id>_<Slot>.
# Run: blender -b -P Tools/blender/boss_planes_autumn_camping_christmas.py -- <out dir> [export] [ids,comma,separated]
#      writes Enemy_<id>.fbx per plane (with "export") and the usual previews.
import bpy, bmesh, math, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mathutils import Vector, Matrix
import enemy_planes as EP
from enemy_planes import Plane, loft, sweep, lathe, box, hull, tube, airfoil
from alien_bosses import xf, ball, pipe, cone, bez, torus, sheet

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ONLY = argv[2].split(",") if len(argv) > 2 and argv[2] else None


# ================================================================= shared bits
def grid(center, outline, rings=3):
    """a flat sheet as a polar grid from an inner point to its outline, so it can be painted face by face."""
    c = Vector(center); o = [Vector(p) for p in outline]; polys = []
    for i in range(len(o)):
        a, b = o[i], o[(i + 1) % len(o)]
        for j in range(rings):
            u0, u1 = j / rings, (j + 1) / rings
            p = [c + (a - c) * u0, c + (b - c) * u0, c + (b - c) * u1, c + (a - c) * u1]
            polys.append([tuple(q) for q in (p[1:] if j == 0 else p)])
    return polys

def polar(c, u, R, spec, z=0.0):
    """an outline round c: (angle from the outward direction u, radius fraction) pairs, in the wing plane."""
    c = Vector(c); u = Vector(u).normalized(); v = Vector((-u.y, u.x, 0))
    return [tuple(c + (u * math.cos(math.radians(a)) + v * math.sin(math.radians(a))) * R * r + Vector((0, 0, z))) for a, r in spec]

def pilot(P, y, z, cap, skin="Belly", goggles="Glass", rim="Trim", scarf="Accent"):
    """an open cockpit: a padded rim, the pilot's head, a flying cap and goggles, a scarf trailing back."""
    P.obj("Rim", xf(torus(0.21, 0.045, 0.0, 16, 5), None, (0, y, z)), rim)
    P.obj("PilotHead", ball((0, y, z + 0.15), (0.13, 0.13, 0.14), 10, 6), skin)
    P.obj("PilotCap", ball((0, y - 0.015, z + 0.2), (0.142, 0.142, 0.11), 10, 5), cap)
    for s in (1, -1):
        P.obj("Goggle", ball((s * 0.055, y + 0.115, z + 0.22), (0.045, 0.03, 0.04), 8, 4), goggles)
    P.obj("Scarf", pipe([(0.06, y - 0.08, z + 0.06), (0.12, y - 0.3, z + 0.1), (0.2, y - 0.55, z + 0.18)], [0.04, 0.035, 0.0], 5), scarf)

def nacelle(P, x, y0, y1, r, z, paint):
    P.obj("Nacelle", loft([(y1, r * 0.5, r * 0.5, x, z), (y1 - 0.12, r, r, x, z), (y0 + 0.2, r * 0.9, r * 0.9, x, z), (y0, r * 0.3, r * 0.3, x, z)], 10), paint, 1)

def tuft(P, a, b, r, paint, name="Tuft"):
    P.obj(name, cone(a, b, r, 5), paint, 0, False)


# ================================================================= AUTUMN 1: the fox spirit fighter
def B_autumn():
    """The fox spirit as a fighter: a fox head for a nose (pointed ears, amber eyes, red markings, a black button nose), an orange body
    with a cream belly, two engines on the wings, three great fox tails tipped in blue foxfire for a tail, foxfire at the wing tips, and a
    fox-eared pilot in the open cockpit with a golden circlet."""
    P = Plane("autumn", {"Base": ((0.95, 0.48, 0.12), 0.4), "Belly": ((0.98, 0.93, 0.84), 0.3), "Accent": ((0.82, 0.10, 0.10), 0.45),
                         "Trim": ((1.0, 0.78, 0.25), 0.8), "Glass": ((0.55, 0.85, 1.0), 0.9), "Dark": ((0.06, 0.05, 0.05), 0.4),
                         "Glow": ((0.30, 0.75, 1.0), 0.5), "Metal": ((0.55, 0.55, 0.58), 0.6), "Lamp": ((1.0, 0.70, 0.15), 0.8)})
    fur = lambda c, n: "Belly" if (n.z < -0.35 or (c.y > 1.45 and c.z < 0.02)) else "Base"
    P.obj("Body", loft([(2.05, 0.05, 0.05, 0, -0.04), (1.85, 0.25, 0.2, 0, -0.02), (1.45, 0.38, 0.36, 0, 0.02), (0.6, 0.42, 0.4, 0, 0.04),
                        (-0.5, 0.32, 0.3, 0, 0.07), (-1.6, 0.13, 0.13, 0, 0.12)], 12), fur, 1)
    P.obj("Nose", ball((0, 2.06, -0.03), (0.08, 0.06, 0.06), 8, 4), "Dark")
    for s in (1, -1):
        P.obj("Eye", ball((s * 0.19, 1.62, 0.2), (0.1, 0.05, 0.08), 10, 5), "Lamp")
        P.obj("Pupil", ball((s * 0.19, 1.665, 0.2), (0.02, 0.02, 0.06), 6, 3), "Dark")
        P.obj("Brow", hull([(s * 0.08, 1.67, 0.31), (s * 0.3, 1.58, 0.33), (s * 0.3, 1.55, 0.29), (s * 0.09, 1.64, 0.28)]), "Dark", 0, False)
        P.obj("Marking", cone((s * 0.27, 1.55, 0.05), (s * 0.4, 1.4, -0.02), 0.05, 4), "Accent", 0, False)
        ear = [(s * 0.13, 1.35, 0.3), (s * 0.36, 1.3, 0.28), (s * 0.3, 1.25, 0.78), (s * 0.24, 1.42, 0.32)]
        P.obj("Ear", hull(ear), "Base", 0, False)
        P.obj("EarTip", hull([(s * 0.26, 1.29, 0.6), (s * 0.33, 1.27, 0.6), (s * 0.3, 1.25, 0.78), (s * 0.29, 1.31, 0.62)]), "Dark", 0, False)
        P.obj("Whisker", pipe([(s * 0.12, 1.92, -0.02), (s * 0.45, 1.95, 0.05)], [0.012, 0.004], 4), "Dark")
        # engines out on the wings
        x = s * 1.1
        nacelle(P, x, -0.1, 1.15, 0.2, -0.02, lambda c, n: "Trim" if c.y > 1.0 else "Base")
        P.prop((x, 1.17, -0.02), 0.5, 3, spinner="Trim")
        # foxfire at the wing tips
        P.obj("Foxfire", pipe(bez((s * 2.5, 0.1, 0.1), (s * 2.55, 0.0, 0.35), (s * 2.5, -0.15, 0.5), (s * 2.58, -0.3, 0.7), 4), [0.12, 0.1, 0.07, 0.04, 0.0], 6), "Glow")
    P.wing([(0.3, 0.75, -0.35, 0.14, -0.04), (1.3, 0.65, -0.25, 0.11, 0.0), (2.2, 0.45, -0.1, 0.07, 0.06), (2.5, 0.3, -0.02, 0.05, 0.1)],
           lambda c, n: "Belly" if n.z < -0.3 else ("Belly" if abs(c.x) > 2.25 else "Base"))
    P.obj("Stab", sweep([(x, airfoil(-1.2, -1.6, 0.06, 0.12)) for x in (-0.85, -0.6, 0.6, 0.85)], "x"), "Base", 1)
    # three great fox tails as the tail, each tipped with white fur and a flame of foxfire
    for k, dx in enumerate((-0.4, 0.0, 0.4)):
        a = Vector((dx * 0.3, -1.45, 0.15))
        pts = bez(a, a + Vector((dx * 0.4, -0.45, 0.25)), a + Vector((dx * 1.1, -0.7, 0.75)), a + Vector((dx * 1.3, -0.55, 1.15 - abs(dx) * 0.4)), 6)
        rr = [0.1, 0.18, 0.22, 0.22, 0.19, 0.13, 0.0]
        P.obj("Tail", pipe(pts, rr, 8), lambda c, n, t=pts[4]: "Belly" if (c - t).length < 0.32 and c.z > t.z - 0.1 else "Base", 1)
        P.obj("TailFire", pipe(bez(pts[-1], pts[-1] + Vector((0, 0.05, 0.15)), pts[-1] + Vector((dx * 0.2, -0.1, 0.3)), pts[-1] + Vector((dx * 0.1, -0.05, 0.45)), 4), [0.12, 0.1, 0.07, 0.04, 0.0], 6), "Glow")
    pilot(P, 0.55, 0.38, "Base", skin="Belly")
    for s in (1, -1):   # the pilot's fox ears and a golden circlet with red leaves
        P.obj("PilotEar", cone((s * 0.08, 0.54, 0.65), (s * 0.12, 0.52, 0.82), 0.045, 4), "Base", 0, False)
    P.obj("Circlet", xf(torus(0.135, 0.02, 0.0, 14, 4), None, (0, 0.55, 0.6)), "Trim")
    P.obj("Leaf", hull([(0, 0.69, 0.6), (-0.06, 0.69, 0.68), (0.06, 0.69, 0.68), (0, 0.68, 0.76), (0, 0.66, 0.66)]), "Accent", 0, False)
    return P


# ================================================================= AUTUMN 2: the squirrel knight's acorn
def B_autumn2():
    """The squirrel knight's acorn fighter: a glossy acorn for a fuselage with its scaly cap over the back and the stalk for a propeller
    hub, maple-leaf wings in red and orange with gold veins, a huge bushy squirrel tail curling up for a fin, gold armour bands, acorn
    bombs under the wings, and the squirrel knight himself in the cockpit in a plumed gold helmet."""
    P = Plane("autumn2", {"Base": ((0.62, 0.36, 0.14), 0.6), "Belly": ((0.97, 0.90, 0.78), 0.3), "Accent": ((0.88, 0.22, 0.08), 0.4),
                          "Trim": ((1.0, 0.78, 0.25), 0.85), "Glass": ((0.95, 0.55, 0.12), 0.5), "Dark": ((0.10, 0.06, 0.04), 0.4),
                          "Glow": ((1.0, 0.62, 0.15), 0.5), "Metal": ((0.36, 0.22, 0.10), 0.3), "Lamp": ((1.0, 0.85, 0.3), 0.8)})
    # the acorn: the nut in front, the cap behind, then a slim boom
    P.obj("Nut", loft([(2.0, 0.08, 0.08, 0, 0.0), (1.8, 0.3, 0.3, 0, 0.0), (1.3, 0.48, 0.48, 0, 0.02), (0.6, 0.52, 0.52, 0, 0.04), (0.1, 0.5, 0.5, 0, 0.05)], 14),
          lambda c, n: "Glass" if n.z > 0.5 and c.y > 0.9 else "Base", 1)
    P.obj("Cap", loft([(0.25, 0.58, 0.58, 0, 0.05), (0.0, 0.6, 0.6, 0, 0.06), (-0.45, 0.5, 0.5, 0, 0.07), (-0.8, 0.28, 0.28, 0, 0.08), (-1.0, 0.1, 0.1, 0, 0.08)], 14),
          lambda c, n: "Dark" if (math.atan2(c.x, c.z) * 3 + c.y * 9) % 1.0 < 0.3 else "Metal", 1)
    P.obj("Boom", loft([(-0.9, 0.16, 0.16, 0, 0.08), (-1.8, 0.09, 0.09, 0, 0.12)], 8), "Metal", 1)
    for y in (1.15, 0.45):
        P.obj("Band", xf(torus(0.5 if y > 1 else 0.53, 0.035, 0.0, 22, 4), Matrix.Rotation(math.radians(90), 3, "X"), (0, y, 0.03)), "Trim")
    P.prop((0, 2.03, 0.0), 0.62, 3, spinner="Dark", tip="Trim", blade="Metal")
    # maple-leaf wings: lobed outlines, red to orange from the root, gold veins
    spec = [(-160, 0.8), (-125, 0.5), (-90, 0.8), (-68, 0.45), (-45, 0.95), (-22, 0.5), (0, 1.05), (22, 0.5), (45, 0.95), (68, 0.45), (90, 0.8), (125, 0.5), (160, 0.8), (180, 0.85)]
    for s in (1, -1):
        c = Vector((s * 1.35, 0.25, 0.02))
        out = polar(c, (s, 0.12, 0), 1.15, spec)
        P.obj("Leaf", sheet(grid(c, out, 3), 0.06), lambda q, n, c=c: "Glow" if (q - c).length > 0.75 else "Accent", 0, False)
        for a in (-90, -45, 0, 45, 90):
            u = Vector((s, 0.12, 0)).normalized(); v = Vector((-u.y, u.x, 0))
            tip = c + (u * math.cos(math.radians(a)) + v * math.sin(math.radians(a))) * 1.0
            P.obj("Vein", pipe([c + Vector((0, 0, 0.035)), tip + Vector((0, 0, 0.035))], [0.025, 0.008], 4), "Trim")
        P.obj("Vein", pipe([c + Vector((0, 0, 0.035)), Vector((s * 0.4, 0.15, 0.06))], [0.03, 0.03], 4), "Trim")
        # an acorn bomb under each wing
        b = Vector((s * 1.0, 0.25, -0.25))
        P.obj("BombNut", ball(tuple(b + Vector((0, 0.08, 0))), (0.11, 0.17, 0.11), 8, 5), "Base")
        P.obj("BombCap", ball(tuple(b + Vector((0, -0.06, 0))), (0.13, 0.08, 0.13), 8, 4), "Metal")
        P.obj("Pylon", box(tuple(b + Vector((0, 0, 0.14))), (0.03, 0.1, 0.16)), "Trim", 0, False)
    P.obj("Stab", sweep([(x, airfoil(-1.45, -1.8, 0.05, 0.12)) for x in (-0.7, -0.45, 0.45, 0.7)], "x"), "Accent", 1)
    # the bushy tail curling up behind for a fin
    a = Vector((0, -1.75, 0.15))
    tail = bez(a, a + Vector((0, -0.45, 0.45)), a + Vector((0, -0.3, 1.25)), a + Vector((0, 0.35, 1.35)), 8)
    rr = [0.12, 0.24, 0.32, 0.36, 0.36, 0.33, 0.27, 0.18, 0.0]
    P.obj("Tail", pipe(tail, rr, 10), lambda c, n: "Belly" if c.y > -1.55 and c.z > 1.2 else "Glass", 1)
    for i in range(1, 8):
        q = tail[i]
        for k in (-1, 1):
            tuft(P, q + Vector((k * rr[i] * 0.8, 0, 0)), q + Vector((k * (rr[i] + 0.14), -0.05, 0.05)), 0.07, "Belly" if i > 5 else "Glass")
    # the squirrel knight in the cockpit
    pilot(P, -0.15, 0.55, "Trim", skin="Glass", goggles="Dark", scarf="Accent")
    P.obj("Muzzle", ball((0, -0.03, 0.66), (0.08, 0.05, 0.06), 8, 4), "Belly")
    for s in (1, -1):
        P.obj("PilotEar", cone((s * 0.08, -0.17, 0.82), (s * 0.11, -0.18, 1.0), 0.05, 4), "Glass", 0, False)
    P.obj("Plume", pipe(bez((0, -0.15, 0.88), (0, -0.2, 1.05), (0, -0.35, 1.12), (0, -0.48, 1.08), 4), [0.06, 0.07, 0.06, 0.04, 0.0], 6), "Accent")
    return P


# ================================================================= CAMPING 1: the great horned owl
def B_camping():
    """The great horned owl as a fighter: the whole nose is the owl's face - a two-lobed facial disc, huge amber eyes ringed in gold under
    fierce brows, a hooked gold beak and feathered horn tufts - a round brown body with a speckled cream breast, broad banded feather wings
    with fingered tips, a fan tail, a pusher propeller behind, a glowing lantern hanging under the belly and a pilot in an aviator cap."""
    P = Plane("camping", {"Base": ((0.48, 0.32, 0.18), 0.35), "Belly": ((0.95, 0.90, 0.78), 0.3), "Accent": ((0.28, 0.18, 0.10), 0.35),
                          "Trim": ((1.0, 0.78, 0.25), 0.85), "Glass": ((0.75, 0.9, 1.0), 0.9), "Dark": ((0.05, 0.04, 0.03), 0.5),
                          "Glow": ((0.75, 1.0, 0.45), 0.5), "Metal": ((0.28, 0.28, 0.3), 0.6), "Lamp": ((1.0, 0.68, 0.15), 0.8)})
    speck = lambda c: (math.sin(c.x * 41) * math.sin(c.y * 37) * math.sin(c.z * 29)) > 0.35
    def body_paint(c, n):
        if n.y > 0.55 and c.y > 1.3: return "Belly"   # the facial disc
        if n.z < -0.25: return "Accent" if speck(c) else "Belly"   # the speckled breast
        return "Accent" if speck(c) else "Base"
    P.obj("Body", loft([(1.85, 0.18, 0.18, 0, 0.05), (1.7, 0.42, 0.4, 0, 0.06), (1.2, 0.55, 0.52, 0, 0.06), (0.3, 0.52, 0.5, 0, 0.05),
                        (-0.6, 0.38, 0.36, 0, 0.06), (-1.5, 0.16, 0.16, 0, 0.08)], 14), body_paint, 1)
    for s in (1, -1):   # the face: two lobes of the disc, eyes, brows, tufts
        P.obj("Disc", ball((s * 0.22, 1.72, 0.12), (0.26, 0.1, 0.3), 12, 6), "Belly", 1)
        P.obj("EyeRim", ball((s * 0.22, 1.8, 0.16), (0.17, 0.05, 0.17), 12, 6), "Trim")
        P.obj("Eye", ball((s * 0.22, 1.83, 0.16), (0.14, 0.04, 0.14), 12, 6), "Lamp")
        P.obj("Pupil", ball((s * 0.21, 1.86, 0.16), (0.07, 0.025, 0.07), 10, 5), "Dark")
        P.obj("Shine", ball((s * 0.18, 1.88, 0.21), (0.025, 0.01, 0.025), 6, 3), "Belly")
        P.obj("Brow", hull([(s * 0.03, 1.84, 0.33), (s * 0.42, 1.74, 0.42), (s * 0.42, 1.7, 0.36), (s * 0.04, 1.8, 0.28)]), "Accent", 0, False)
        for k in range(3):   # the feathered horn tufts
            b = Vector((s * (0.22 + 0.06 * k), 1.5 - 0.06 * k, 0.48))
            tuft(P, b, b + Vector((s * (0.12 + 0.05 * k), -0.12, 0.38 - 0.06 * k)), 0.06, "Base" if k != 1 else "Accent")
    P.obj("Beak", pipe(bez((0, 1.82, 0.04), (0, 1.97, 0.02), (0, 2.0, -0.08), (0, 1.94, -0.16), 4), [0.07, 0.06, 0.045, 0.025, 0.0], 6), "Trim")
    # the wings: broad, banded, fingered tips
    def band(c, n):
        if n.z < -0.3: return "Belly"
        return "Accent" if (abs(c.x) * 3.2) % 1.0 < 0.22 else "Base"
    P.wing([(0.35, 0.8, -0.35, 0.15, 0.0), (1.2, 0.75, -0.4, 0.12, 0.05), (2.0, 0.6, -0.3, 0.08, 0.12), (2.3, 0.45, -0.15, 0.05, 0.16)], band)
    for s in (1, -1):
        for k in range(5):
            y = 0.42 - k * 0.15
            b = Vector((s * 2.2, y, 0.15))
            P.obj("Finger", cone(b, b + Vector((s * (0.45 - abs(k - 2) * 0.06), -0.08 * k, 0.04)), 0.07, 4), "Accent" if k % 2 else "Base", 0, False)
    # the fan tail and the pusher propeller
    fan = [(math.sin(math.radians(a)) * 0.75, -1.45 - math.cos(math.radians(a)) * 0.75, 0.1) for a in range(-60, 61, 15)]
    P.obj("TailFan", sheet(grid((0, -1.3, 0.1), [(0, -1.3, 0.1)] + fan, 2), 0.05), lambda c, n: "Accent" if (math.atan2(c.x, -c.y - 1.3) * 6) % 1.0 < 0.3 else "Base", 0, False)
    P.obj("Fin", sweep([(h, airfoil(-1.2, -1.6, 0.05, 0.0)) for h in (0.1, 0.6)], "z"), "Base", 1)
    P.prop((0, -1.62, 0.08), 0.5, 3, spinner=None, blade="Accent", tip="Trim")
    # the lantern hanging under the belly
    P.obj("Hook", pipe([(0, 0.5, -0.45), (0, 0.5, -0.65)], [0.015, 0.015], 4), "Metal")
    P.obj("LanternCap", lathe([(0.0, -0.62), (0.13, -0.68), (0.1, -0.72)], 8, "z", (0, 0.5, 0)), "Metal")
    P.obj("Lantern", lathe([(0.1, -0.72), (0.11, -0.95), (0.0, -0.97)], 8, "z", (0, 0.5, 0)), "Lamp")
    P.obj("LanternBase", lathe([(0.13, -0.95), (0.0, -1.0)], 8, "z", (0, 0.5, 0)), "Metal")
    pilot(P, 0.5, 0.5, "Accent", skin="Belly", goggles="Glass", scarf="Glow")
    return P


# ================================================================= CAMPING 2: the luna moth glider
def B_camping2():
    """The luna moth empress as a glider-fighter: a fluffy white body ringed in glowing bands, a sweet moth face with glossy black eyes and
    golden fern antennae, two pairs of jade wings edged in plum with golden eye-spots and long swallow tails, twin propellers at the wing
    roots, a crescent moon standing on the tail and a pilot in a moon-silver cap."""
    P = Plane("camping2", {"Base": ((0.42, 0.85, 0.62), 0.4), "Belly": ((0.97, 0.96, 0.92), 0.2), "Accent": ((0.52, 0.16, 0.40), 0.4),
                           "Trim": ((1.0, 0.80, 0.32), 0.85), "Glass": ((0.02, 0.02, 0.05), 0.95), "Dark": ((0.10, 0.05, 0.10), 0.4),
                           "Glow": ((0.35, 0.85, 1.0), 0.5), "Metal": ((0.80, 0.82, 0.88), 0.7), "Lamp": ((1.0, 0.82, 0.35), 0.8)})
    P.obj("Body", loft([(1.75, 0.1, 0.1, 0, 0.05), (1.55, 0.32, 0.3, 0, 0.05), (1.0, 0.38, 0.36, 0, 0.04), (0.2, 0.34, 0.32, 0, 0.03),
                        (-0.6, 0.26, 0.24, 0, 0.04), (-1.4, 0.1, 0.1, 0, 0.06)], 12),
          lambda c, n: "Glow" if c.y < 0.1 and (c.y * 3.5) % 1.0 < 0.22 else "Belly", 1)
    for k in range(14):   # a fluffy ruff behind the head
        a = 2 * math.pi * k / 14
        b = Vector((math.sin(a) * 0.32, 1.25, 0.05 + math.cos(a) * 0.3))
        tuft(P, b, b + Vector((math.sin(a) * 0.15, -0.06, math.cos(a) * 0.14)), 0.08, "Belly")
    for s in (1, -1):
        P.obj("Eye", ball((s * 0.2, 1.6, 0.14), (0.15, 0.12, 0.16), 12, 6), "Glass")
        P.obj("Shine", ball((s * 0.16, 1.71, 0.22), (0.04, 0.02, 0.04), 6, 3), "Lamp")
        P.obj("Cheek", ball((s * 0.25, 1.62, -0.04), (0.06, 0.03, 0.035), 6, 3), "Accent")
        ant = bez((s * 0.08, 1.62, 0.32), (s * 0.18, 1.8, 0.6), (s * 0.42, 1.88, 0.78), (s * 0.62, 1.8, 0.92), 7)
        P.obj("Antenna", pipe(ant, [0.025] * 7 + [0.012], 5), "Trim")
        for k in range(2, 8):
            q = ant[k]; L = 0.15 * math.sin(math.pi * k / 8) + 0.03
            for side in (-1, 1):
                P.obj("Barb", cone(q, q + Vector((s * 0.02, -L * 0.6, side * L)), 0.012, 3), "Trim", 0, False)
    P.obj("Smile", pipe(bez((-0.08, 1.7, -0.02), (-0.03, 1.73, -0.07), (0.03, 1.73, -0.07), (0.08, 1.7, -0.02), 5), [0.013] * 6, 4), "Dark")
    # the wings: a forewing and a swallow-tailed hindwing each side
    for s in (1, -1):
        fc = Vector((s * 1.25, 0.45, 0.12)); hc = Vector((s * 0.85, -0.45, 0.06))
        fore = polar(fc, (s, 0.18, 0), 1.0, [(a, 1.0 if abs(a) < 90 else 0.75) for a in range(-180, 180, 20)])
        fore[9] = tuple(Vector((s * 0.3, 0.45, 0.1)))   # pull the root in to the body
        hind = polar(hc, (s, -0.5, 0), 0.62, [(a, 1.0) for a in range(-180, 180, 24)])
        # the swallow tail: one point pulled far back
        hind[5] = tuple(hc + Vector((s * 0.35, -1.25, -0.05)))
        hind[7] = tuple(Vector((s * 0.25, -0.35, 0.05)))
        spots = [(fc + Vector((s * 0.05, -0.02, 0)), 0.32), (hc + Vector((0, -0.05, 0)), 0.24)]
        def paint(c, n, spots=spots, outline=fore + hind):
            for sp, r in spots:
                d = ((c - sp) * Vector((1, 1, 0))).length
                if d < r * 0.45: return "Dark"
                if d < r * 0.75: return "Lamp"
                if d < r: return "Trim"
            e = min(((c - Vector(o)) * Vector((1, 1, 0))).length for o in outline)
            return "Accent" if e < 0.16 else "Base"
        P.obj("Forewing", sheet(grid(fc, fore, 4), 0.04), paint, 0, False)
        P.obj("Hindwing", sheet(grid(hc, hind, 4), 0.04), paint, 0, False)
        P.obj("TailGem", ball(tuple(Vector(hind[5]) + Vector((0, 0, 0.02))), (0.06, 0.06, 0.04), 6, 3), "Glow")
        # a propeller at each wing root
        x = s * 0.62
        nacelle(P, x, 0.3, 1.25, 0.14, -0.08, "Belly")
        P.prop((x, 1.27, -0.08), 0.36, 3, spinner="Trim", blade="Accent", tip="Trim")
    # the crescent moon standing on the tail
    arc = [Vector((0, -1.25 - math.sin(t) * 0.38, 0.5 + math.cos(t) * 0.38)) for t in [math.radians(-150 + 300 * i / 12) for i in range(13)]]
    P.obj("Crescent", pipe(arc, [0.0] + [0.07 * math.sin(math.pi * i / 12) + 0.015 for i in range(1, 12)] + [0.0], 6), "Lamp")
    P.obj("Mast", pipe([(0, -1.25, 0.08), (0, -1.25, 0.15)], [0.04, 0.04], 5), "Trim")
    P.obj("Stab", sweep([(x, airfoil(-1.1, -1.4, 0.04, 0.08)) for x in (-0.6, -0.4, 0.4, 0.6)], "x"), "Base", 1)
    pilot(P, 0.55, 0.38, "Metal", skin="Belly", goggles="Glow", scarf="Accent")
    return P


# ================================================================= CHRISTMAS 1: the nutcracker king
def B_christmas():
    """The nutcracker king as a fighter: the nose is his big wooden face - wide blue eyes, a great nose, a white moustache and a jaw of square
    teeth, rosy cheeks - under a tall black busby with a gold badge and a red plume; a red guard's-coat fuselage with gold frogging, white
    wings trimmed in gold with red stripes, gold epaulette pods, a sabre-shaped fin, a pusher propeller and a toy-soldier pilot."""
    P = Plane("christmas", {"Base": ((0.80, 0.08, 0.10), 0.5), "Belly": ((0.96, 0.82, 0.64), 0.35), "Accent": ((0.06, 0.06, 0.08), 0.5),
                            "Trim": ((1.0, 0.78, 0.25), 0.85), "Glass": ((0.97, 0.97, 0.97), 0.5), "Dark": ((0.04, 0.04, 0.05), 0.4),
                            "Glow": ((0.30, 0.55, 1.0), 0.6), "Metal": ((0.75, 0.78, 0.82), 0.7), "Lamp": ((1.0, 0.85, 0.4), 0.8)})
    def coat(c, n):
        if c.y > 1.25: return "Belly"   # the face
        if n.z > 0.5 and (c.y * 4.0) % 1.0 < 0.18: return "Trim"   # gold frogging across the chest
        return "Glass" if n.z < -0.4 else "Base"
    P.obj("Body", loft([(1.95, 0.32, 0.36, 0, 0.0), (1.8, 0.38, 0.4, 0, 0.0), (1.3, 0.4, 0.42, 0, 0.0), (0.4, 0.4, 0.4, 0, 0.02),
                        (-0.6, 0.3, 0.3, 0, 0.06), (-1.5, 0.13, 0.13, 0, 0.1)], 12, sq=1.3), coat, 1)
    P.obj("FacePlate", lathe([(0.0, 1.97), (0.33, 1.95)], 14, "y", (0, 0, 0.0)), "Belly")
    for s in (1, -1):
        P.obj("EyeWhite", ball((s * 0.15, 1.97, 0.15), (0.1, 0.04, 0.08), 10, 5), "Glass")
        P.obj("Iris", ball((s * 0.15, 2.0, 0.15), (0.055, 0.02, 0.055), 8, 4), "Glow")
        P.obj("Pupil", ball((s * 0.15, 2.015, 0.15), (0.025, 0.01, 0.025), 6, 3), "Dark")
        P.obj("Brow", hull([(s * 0.04, 2.0, 0.26), (s * 0.28, 1.98, 0.28), (s * 0.28, 1.96, 0.24), (s * 0.05, 1.98, 0.22)]), "Glass", 0, False)
        P.obj("Cheek", ball((s * 0.24, 1.97, -0.04), (0.07, 0.03, 0.05), 8, 4), "Base")
        P.obj("Moustache", pipe(bez((s * 0.02, 2.04, -0.03), (s * 0.12, 2.06, -0.0), (s * 0.24, 2.02, -0.08), (s * 0.3, 1.98, -0.02), 4), [0.05, 0.055, 0.045, 0.03, 0.0], 6), "Glass")
    P.obj("Nose", ball((0, 2.06, 0.04), (0.06, 0.09, 0.07), 8, 4), "Belly")
    P.obj("Jaw", box((0, 1.98, -0.2), (0.3, 0.06, 0.1)), "Glass", 0, False)
    for k in range(5):
        P.obj("ToothGap", box(((k - 2) * 0.06, 2.015, -0.2), (0.008, 0.01, 0.1)), "Dark", 0, False)
    # the busby: a tall black hat on his head, a gold badge, a red plume, a chin strap
    P.obj("Busby", loft([(1.98, 0.3, 0.2, 0, 0.62), (1.82, 0.36, 0.26, 0, 0.66), (1.5, 0.36, 0.26, 0, 0.64), (1.35, 0.28, 0.2, 0, 0.6)], 12), "Accent", 1)
    P.obj("Busby", lathe([(0.32, 0.3), (0.34, 0.62), (0.3, 0.92), (0.0, 0.98)], 12, "z", (0, 1.68, 0)), "Accent", 1)
    P.obj("HatBand", lathe([(0.35, 0.3), (0.355, 0.38), (0.0, 0.38)], 12, "z", (0, 1.68, 0)), "Trim")
    P.obj("Badge", lathe([(0.0, 0.0), (0.09, 0.0), (0.09, 0.03), (0.0, 0.04)], 10, "y", (0, 2.0, 0.6)), "Trim")
    P.obj("Plume", pipe(bez((0.22, 1.7, 0.85), (0.3, 1.7, 1.05), (0.3, 1.55, 1.2), (0.25, 1.4, 1.22), 4), [0.06, 0.07, 0.06, 0.04, 0.0], 6), "Base")
    # wings, white with gold edges and a red stripe; gold epaulette pods at the roots
    def wingp(c, n):
        if n.z < -0.3: return "Glass"
        x = abs(c.x)
        if x > 2.3: return "Trim"
        return "Base" if 1.5 < x < 1.75 else "Glass"
    P.wing([(0.3, 0.7, -0.3, 0.13, -0.05), (1.3, 0.65, -0.25, 0.11, -0.02), (2.2, 0.45, -0.1, 0.07, 0.03), (2.45, 0.3, -0.02, 0.05, 0.05)], wingp)
    for s in (1, -1):
        P.obj("Epaulette", ball((s * 0.45, 0.35, 0.25), (0.2, 0.25, 0.1), 10, 5), "Trim")
        for k in range(6):
            b = Vector((s * (0.3 + k * 0.05), 0.12 + k * 0.08, 0.18))
            P.obj("Fringe", pipe([b, b + Vector((s * 0.06, 0, -0.15))], [0.02, 0.012], 4), "Trim")
        P.obj("Sabre", hull([(s * 0.9, 0.95, -0.2), (s * 0.9, 1.0, -0.15), (s * 0.9, -0.4, -0.18), (s * 0.95, -0.4, -0.15)]), "Metal", 0, False)
        P.obj("Hilt", box((s * 0.9, 1.0, -0.17), (0.12, 0.03, 0.05)), "Trim", 0, False)
    # the tail: a fin like a sabre blade, a stabiliser, the pusher propeller
    P.obj("Fin", sweep([(h, airfoil(-1.0 - h * 0.6, -1.55 - h * 0.3, 0.05, 0.0)) for h in (0.1, 0.5, 0.85)], "z"), lambda c, n: "Trim" if c.z > 0.75 else "Base", 1)
    P.obj("Stab", sweep([(x, airfoil(-1.15, -1.5, 0.05, 0.1)) for x in (-0.75, -0.5, 0.5, 0.75)], "x"), "Glass", 1)
    P.prop((0, -1.58, 0.1), 0.5, 3, spinner=None, blade="Accent", tip="Trim")
    pilot(P, 0.6, 0.4, "Base", skin="Belly", goggles="Glass", scarf="Trim")
    P.obj("PilotStrap", xf(torus(0.11, 0.015, 0.0, 12, 4), Matrix.Rotation(math.radians(90), 3, "Y"), (0, 0.6, 0.55)), "Trim")
    return P


# ================================================================= CHRISTMAS 2: the krampus bomber
def B_christmas2():
    """Krampus as a bomber: a shaggy black body, a red goat face for a nose with blazing yellow eyes, fangs and a lolling red tongue,
    great ram horns curling from its cheeks, two engines with gold-banded propellers, dark wings with red edges hung with golden bells on
    chains, a sack of coal on its back, a tufted goat tail and a hooded pilot."""
    P = Plane("christmas2", {"Base": ((0.13, 0.10, 0.10), 0.25), "Belly": ((0.40, 0.30, 0.24), 0.25), "Accent": ((0.75, 0.10, 0.10), 0.45),
                             "Trim": ((1.0, 0.78, 0.26), 0.85), "Glass": ((0.95, 0.93, 0.85), 0.5), "Dark": ((0.03, 0.02, 0.02), 0.5),
                             "Glow": ((0.70, 0.95, 1.0), 0.5), "Metal": ((0.50, 0.50, 0.55), 0.75), "Lamp": ((1.0, 0.85, 0.20), 0.8)})
    P.obj("Body", loft([(1.6, 0.36, 0.34, 0, 0.0), (1.2, 0.48, 0.45, 0, 0.02), (0.3, 0.5, 0.46, 0, 0.04), (-0.6, 0.38, 0.36, 0, 0.06), (-1.55, 0.14, 0.14, 0, 0.1)], 10), "Base", 1)
    for k in range(12):   # shag down its back and flanks
        y = 1.1 - (k // 2) * 0.36; s = 1 if k % 2 else -1
        b = Vector((s * 0.36, y, 0.25))
        tuft(P, b, b + Vector((s * 0.12, -0.2, 0.12)), 0.08, "Base", "Shag")
    # the red goat face
    P.obj("Face", loft([(1.45, 0.3, 0.3, 0, 0.02), (1.75, 0.26, 0.24, 0, -0.02), (2.0, 0.17, 0.15, 0, -0.08), (2.12, 0.08, 0.07, 0, -0.1)], 10), "Accent", 1)
    for s in (1, -1):
        P.obj("Socket", ball((s * 0.15, 1.72, 0.17), (0.1, 0.06, 0.07), 8, 4), "Dark")
        P.obj("Eye", ball((s * 0.15, 1.76, 0.17), (0.08, 0.04, 0.05), 8, 4), "Lamp")
        P.obj("Pupil", ball((s * 0.15, 1.79, 0.17), (0.015, 0.015, 0.04), 6, 3), "Dark")
        P.obj("Brow", hull([(s * 0.02, 1.78, 0.27), (s * 0.3, 1.66, 0.33), (s * 0.3, 1.63, 0.28), (s * 0.04, 1.74, 0.22)]), "Dark", 0, False)
        P.obj("Fang", cone((s * 0.07, 2.02, -0.14), (s * 0.07, 2.04, -0.27), 0.025, 4), "Glass", 0, False)
        P.obj("Nostril", ball((s * 0.04, 2.13, -0.07), (0.02, 0.015, 0.015), 5, 3), "Dark")
        # the great ram horns curling from the cheeks
        h0 = Vector((s * 0.25, 1.5, 0.25))
        pts = bez(h0, h0 + Vector((s * 0.3, -0.25, 0.45)), h0 + Vector((s * 0.85, -0.2, 0.3)), h0 + Vector((s * 0.8, 0.15, -0.12)), 8)
        pts += bez(pts[-1], pts[-1] + Vector((s * -0.05, 0.2, -0.2)), pts[-1] + Vector((s * -0.25, 0.25, -0.12)), pts[-1] + Vector((s * -0.27, 0.18, 0.04)), 4)[1:]
        hr = [0.13 - 0.13 * i / (len(pts) - 1) + 0.004 for i in range(len(pts))]; hr[-1] = 0.0
        P.obj("Horn", pipe(pts, hr, 9), "Glass", 0)
        for i in (2, 5):
            t = (pts[i + 1] - pts[i - 1]).normalized(); ring = torus(hr[i] * 1.12, 0.022, 0.0, 12, 4)
            q = t.to_track_quat("Z", "Y").to_matrix()
            for v in ring.verts: v.co = q @ v.co + pts[i]
            P.obj("HornRing", ring, "Trim")
        # engines on the wings
        x = s * 1.15
        nacelle(P, x, -0.15, 1.1, 0.22, -0.04, lambda c, n: "Trim" if c.y > 0.95 else "Belly")
        P.prop((x, 1.12, -0.04), 0.52, 3, spinner="Trim", blade="Dark", tip="Accent")
        # golden bells hanging from the wings on chains
        for bx in (1.75, 2.2):
            top = Vector((s * bx, 0.1, -0.05))
            P.obj("Chain", pipe([top, top + Vector((0, 0, -0.2))], [0.012, 0.012], 4), "Metal")
            P.obj("Bell", lathe([(0.0, -0.18), (0.05, -0.2), (0.08, -0.3), (0.1, -0.34), (0.0, -0.34)], 10, "z", tuple(top)), "Trim")
            P.obj("Clapper", ball(tuple(top + Vector((0, 0, -0.36))), (0.025, 0.025, 0.025), 5, 3), "Dark")
    P.obj("Mouth", ball((0, 2.0, -0.13), (0.11, 0.06, 0.04), 10, 5), "Dark")
    P.obj("Tongue", pipe(bez((0, 2.02, -0.14), (0, 2.18, -0.16), (0.03, 2.22, -0.3), (0.0, 2.18, -0.42), 5), [0.04, 0.045, 0.04, 0.035, 0.025, 0.0], 6), "Accent")
    P.obj("Beard", cone((0, 1.95, -0.18), (0, 1.98, -0.45), 0.09, 6), "Base", 0, False)
    def wingp(c, n):
        if n.z < -0.3: return "Belly"
        return "Accent" if abs(c.x) > 2.3 or (c.y < -0.15 and abs(c.x) > 0.6) else "Base"
    P.wing([(0.35, 0.75, -0.4, 0.15, -0.04), (1.3, 0.7, -0.35, 0.12, -0.02), (2.3, 0.5, -0.15, 0.08, 0.02), (2.6, 0.35, -0.05, 0.05, 0.04)], wingp)
    # the sack of coal on its back, the tufted tail, twin fins
    P.obj("Sack", ball((0, -0.35, 0.48), (0.3, 0.32, 0.26), 12, 7), "Accent", 0)
    P.obj("SackTie", xf(torus(0.1, 0.025, 0.0, 10, 4), None, (0, -0.4, 0.72)), "Trim")
    for k in range(3):
        P.obj("Coal", ball(((k - 1) * 0.08, -0.4, 0.78), (0.06, 0.06, 0.05), 6, 3), "Dark")
    tail = bez((0, -1.5, 0.12), (0, -1.75, 0.15), (0, -1.85, 0.35), (0, -1.8, 0.5), 4)
    P.obj("Tail", pipe(tail, [0.05, 0.045, 0.04, 0.035, 0.0], 6), "Base")
    P.obj("TailTuft", ball(tuple(tail[-1]), (0.1, 0.1, 0.14), 8, 4), "Base")
    for s in (1, -1):
        P.fin([(0.0, -1.0, -1.45, 0.05), (0.45, -1.15, -1.5, 0.04)], s * 0.55, 0.12, 12, lambda c, n: "Accent" if c.z > 0.45 else "Base")
    P.obj("Stab", sweep([(x, airfoil(-1.05, -1.45, 0.05, 0.12)) for x in (-0.8, -0.55, 0.55, 0.8)], "x"), "Base", 1)
    pilot(P, 0.55, 0.47, "Dark", skin="Accent", goggles="Lamp", scarf="Trim")
    for s in (1, -1):
        P.obj("PilotHorn", cone((s * 0.08, 0.55, 0.72), (s * 0.15, 0.5, 0.88), 0.035, 4), "Glass", 0, False)
    return P


PLANES = [("autumn", B_autumn), ("autumn2", B_autumn2), ("camping", B_camping), ("camping2", B_camping2), ("christmas", B_christmas), ("christmas2", B_christmas2)]

if __name__ == "__main__":
    os.makedirs(EP.OUT, exist_ok=True)
    for pid, fn in PLANES:
        if ONLY and pid not in ONLY: continue
        fn().finish()
    print("DONE")
