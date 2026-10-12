# Sky Squad, boss-styled enemy planes for downtown, the desert pyramids and the japanese island (2026-10-12, the user: "for every level two
# enemy planes inspired by that level's bosses - show me the pictures first"). Same conventions as enemy_planes.py (+Y nose, +Z up, +X right,
# "Prop<n>" spin about the nose, materials "<id>_<Slot>"), drawn in the bosses' style: faces on the noses, open cockpits with a pilot,
# crowns, horns, hoods, glowing accents.
#   city  - the SHARK GUNSHIP JET (after the news chopper gunship): black and red, a shark mouth full of teeth, angry eyes, rocket pods
#   city2 - the KING PIGEON (after the king pigeon): a round iridescent pigeon of a plane, a beak spinner, a gold crown, a red cape fin
#   desert  - the PHARAOH COBRA JET (after the pharaoh cobra): gold and lapis, a cobra head nose with fangs, a flared hood behind the pilot
#   desert2 - the ANUBIS (after the anubis guardian): a black jackal-headed prop plane, tall gold-edged ears, feathered egyptian wings
#   japan  - the ONI FIGHTER (after the oni warlord): a red oni-mask nose with tusks and gold horns, flame-tipped wings
#   japan2 - the SHOGUN JET (after the shogun mecha): lacquered red and black armour plates, a gold crescent crest, a katana fin
# Run: blender -b -P Tools/blender/boss_planes_city_desert_japan.py -- <out dir> [export] [ids,comma,separated]
import bpy, bmesh, math, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mathutils import Vector, Matrix
import enemy_planes as EP
from enemy_planes import Plane, loft, sweep, lathe, box, hull, tube, mirror_x, airfoil
from alien_bosses import ball, pipe, cone, bez, torus, sheet, xf

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ONLY = argv[2].split(",") if len(argv) > 2 and argv[2] else None


# ================================================================= shared bits
def pilot(P, y, z, helmet="Trim", visor="Glow", suit="Dark", screen=True):
    """a pilot in an open cockpit at (0, y, z) (z = the rim of the cockpit): shoulders, a helmet with a glowing visor, a windscreen ahead."""
    P.obj("Cockpit", ball((0, y, z - 0.02), (0.24, 0.32, 0.06), 12, 4), "Dark", 0)
    P.obj("Shoulders", ball((0, y - 0.04, z + 0.08), (0.2, 0.14, 0.12), 10, 5), suit)
    P.obj("Helmet", ball((0, y, z + 0.27), (0.15, 0.16, 0.16), 12, 6), helmet)
    P.obj("Visor", ball((0, y + 0.1, z + 0.27), (0.12, 0.08, 0.06), 10, 5), visor)
    if screen:
        P.obj("Windscreen", hull([(-0.18, y + 0.3, z), (0.18, y + 0.3, z), (-0.12, y + 0.22, z + 0.2), (0.12, y + 0.22, z + 0.2), (0, y + 0.36, z)]), "Glass", 0, False)

def face_eyes(P, y, z, x, r, iris, angry=True, brow="Dark", white="Belly"):
    """two cartoon eyes on the nose looking at the player (+Y), angry brows over them."""
    for s in (1, -1):
        c = Vector((s * x, y, z))
        P.obj("EyeWhite", ball(tuple(c), (r, r * 0.5, r * 1.05), 10, 5), white)
        P.obj("Iris", ball(tuple(c + Vector((-s * r * 0.15, r * 0.4, 0))), (r * 0.6, r * 0.22, r * 0.65), 8, 4), iris)
        P.obj("Pupil", ball(tuple(c + Vector((-s * r * 0.18, r * 0.55, 0))), (r * 0.28, r * 0.1, r * 0.34), 6, 3), "Dark")
        if angry:
            P.obj("Brow", hull([(s * (x - r * 1.1), y + r * 0.3, z + r * 0.75), (s * (x + r * 1.1), y + r * 0.1, z + r * 1.35),
                                (s * (x + r * 1.1), y + r * 0.1, z + r * 1.1), (s * (x - r * 1.1), y + r * 0.3, z + r * 0.55),
                                (s * x, y + r * 0.45, z + r * 1.0)]), brow, 0, False)

def jet_core(P, x, y, z, r, glow="Glow"):
    """a jet nozzle with a glowing core facing the tail."""
    P.obj("Nozzle", lathe([(r * 0.8, y), (r, y - 0.1), (r * 0.9, y - 0.3)], 12, "y", (x, 0, z)), "Metal", 0)
    P.obj("Burner", lathe([(0.0, y - 0.32), (r * 0.75, y - 0.26), (r * 0.8, y - 0.1)], 12, "y", (x, 0, z)), glow, 0)

def fin_flat(P, pts, paint, name="Fin", thick=0.05):
    """a flat upright fin from an outline in the (y, z) plane at x = 0."""
    c = Vector((0, sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)))
    bm = bmesh.new()
    a = [bm.verts.new((-thick, p[0], p[1])) for p in pts]; b = [bm.verts.new((thick, p[0], p[1])) for p in pts]
    bm.faces.new(a); bm.faces.new(list(reversed(b)))
    for i in range(len(pts)):
        j = (i + 1) % len(pts)
        bm.faces.new((a[i], a[j], b[j], b[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return P.obj(name, bm, paint, 0, False)

def wing_flat(P, outline, paint, z=0.0, thick=0.08, name="Wing", dihedral=0.0):
    """a flat wing from a right-side outline in the (x, y) plane, mirrored to the left; the tips lifted by dihedral degrees."""
    for s in (1, -1):
        pts = [(s * p[0], p[1], z + abs(p[0]) * math.tan(math.radians(dihedral))) for p in outline]
        bm = bmesh.new()
        top = [bm.verts.new((p[0], p[1], p[2] + thick * 0.5)) for p in pts]
        bot = [bm.verts.new((p[0], p[1], p[2] - thick * 0.5)) for p in pts]
        f = bm.faces.new(top); g = bm.faces.new(list(reversed(bot)))
        for i in range(len(pts)):
            j = (i + 1) % len(pts)
            bm.faces.new((top[i], top[j], bot[j], bot[i]))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        # split into triangles from the root so the paint can tell bands apart
        bmesh.ops.triangulate(bm, faces=bm.faces)
        P.obj(name + ("R" if s > 0 else "L"), bm, paint, 0, False)


# ================================================================= CITY 1: the shark gunship jet
def Q_city():
    P = Plane("city", {"Base": ((0.14, 0.15, 0.18), 0.5), "Belly": ((0.92, 0.92, 0.94), 0.4), "Accent": ((0.86, 0.12, 0.12), 0.55),
                       "Trim": ((0.98, 0.80, 0.18), 0.6), "Glass": ((0.35, 0.75, 0.95), 0.95), "Dark": ((0.04, 0.04, 0.05), 0.4),
                       "Glow": ((1.0, 0.45, 0.10), 0.5), "Metal": ((0.55, 0.56, 0.6), 0.7), "Lamp": ((1.0, 0.95, 0.85), 0.8)})
    # the fuselage: a fat shark of a jet, nose rounded, a yellow lightning stripe along each flank
    def body_paint(c, n):
        if c.y > 1.75 and -0.2 < c.z < -0.06 + 0.25 * max(0.0, c.y - 2.2) and n.y > -0.3: return "Dark"   # the shark grin
        if c.y > 1.75 and -0.27 < c.z <= -0.2 and n.y > -0.3: return "Accent"
        if n.z < -0.35 and c.y > 1.2: return "Belly"
        if abs(c.x) > 0.3 and abs(c.z - (0.05 + 0.25 * math.sin(c.y * 4.0))) < 0.06: return "Trim"
        return "Base"
    P.obj("Fuselage", loft([(2.55, 0.05, 0.05, 0, -0.05), (2.35, 0.32, 0.3, 0, -0.03), (1.9, 0.48, 0.44, 0, 0.0), (1.0, 0.52, 0.48, 0, 0.02),
                            (-0.3, 0.46, 0.44, 0, 0.04), (-1.4, 0.36, 0.34, 0, 0.06), (-2.0, 0.3, 0.28, 0, 0.08)], 16), body_paint, 1)
    # the shark teeth along the painted grin, on the skin of the nose
    rad = lambda y: 0.32 + (0.48 - 0.32) * max(0.0, min(1.0, (2.35 - y) / 0.45))
    for k in range(6):
        y = 1.85 + k * 0.09
        for s_ in (1, -1):
            r = rad(y) * 0.97
            P.obj("Tooth", cone((s_ * r * 0.8, y, -0.08), (s_ * r * 0.82, y + 0.02, -0.19), 0.035, 4), "Belly", 0, False)
            P.obj("Tooth", cone((s_ * r * 0.82, y + 0.04, -0.27), (s_ * r * 0.8, y + 0.05, -0.17), 0.03, 4), "Belly", 0, False)
    face_eyes(P, 2.22, 0.2, 0.27, 0.12, "Accent", True, "Dark", "Belly")
    # the open cockpit and its pilot
    pilot(P, 0.95, 0.46, "Accent", "Glass", "Dark")
    # wings: short and broad, red tips, rocket pods with glowing noses, a red ON AIR lamp
    wing_flat(P, [(0.35, 0.6), (2.45, -0.45), (2.6, -0.75), (2.3, -0.9), (0.35, -1.0)],
              lambda c, n: "Accent" if abs(c.x) > 2.05 else ("Dark" if n.z < -0.5 else "Base"), -0.12, 0.1)
    for s in (1, -1):
        x = s * 1.45
        P.obj("Pod", loft([(0.75, 0.05, 0.05, x, -0.32), (0.6, 0.17, 0.17, x, -0.32), (-0.55, 0.17, 0.17, x, -0.32), (-0.7, 0.12, 0.12, x, -0.32)], 10),
              lambda c, n: "Accent" if c.y > 0.45 else "Metal", 0)
        for k in range(4):
            a = 2 * math.pi * k / 4 + 0.78
            P.obj("Rocket", ball((x + math.sin(a) * 0.08, 0.76, -0.32 + math.cos(a) * 0.08), (0.04, 0.03, 0.04), 6, 3), "Glow")
        P.missile(s * 2.35, -0.2, -0.6, 1.0, 0.07, "Belly", "Accent")
        jet_core(P, s * 0.26, -1.95, 0.05, 0.2)
        P.obj("Intake", loft([(0.55, 0.12, 0.2, s * 0.52, 0.12), (0.1, 0.14, 0.22, s * 0.52, 0.12), (-0.8, 0.1, 0.18, s * 0.48, 0.1)], 10, sq=1.3),
              lambda c, n: "Dark" if c.y > 0.5 else "Base", 1)
    # twin canted fins, red; tail planes
    for s in (1, -1):
        EPfin = P.fin([(0.0, -1.1, -2.0, 0.06), (0.85, -1.6, -2.15, 0.05), (1.0, -1.75, -2.15, 0.04)], s * 0.32, 0.25, 28, lambda c, n: "Accent" if c.z > 0.9 else "Base", 0)
    wing_flat(P, [(0.3, -1.4), (1.3, -1.9), (1.3, -2.1), (0.3, -2.1)], lambda c, n: "Base", 0.05, 0.06, "Stab")
    P.obj("OnAir", box((0, 0.3, 0.52), (0.26, 0.12, 0.09)), "Accent", 0, False)
    P.obj("OnAirLamp", ball((0, 0.37, 0.52), (0.1, 0.03, 0.035), 8, 3), "Lamp")
    P.obj("Antenna", pipe([(0, -0.3, 0.45), (0, -0.55, 0.85)], [0.015, 0.01], 4), "Metal")
    P.obj("AntennaTip", ball((0, -0.55, 0.87), (0.04, 0.04, 0.04), 6, 3), "Glow")
    return P


# ================================================================= CITY 2: the king pigeon
def Q_city2():
    P = Plane("city2", {"Base": ((0.55, 0.60, 0.70), 0.35), "Belly": ((0.86, 0.88, 0.92), 0.3), "Accent": ((0.62, 0.10, 0.14), 0.45),
                        "Trim": ((1.0, 0.80, 0.22), 0.85), "Glass": ((0.25, 0.80, 0.55), 0.7), "Dark": ((0.06, 0.06, 0.08), 0.4),
                        "Glow": ((0.70, 0.35, 0.95), 0.5), "Metal": ((0.38, 0.40, 0.48), 0.6), "Lamp": ((1.0, 0.55, 0.12), 0.8)})
    # the round pigeon body: grey-blue, a puffed iridescent chest of green and violet bands
    def chest(c, n):
        if c.y > 0.6 and n.y > 0.1 and c.z < 0.35:
            return "Glass" if (c.z * 6 + 10) % 2 < 1 else "Glow"
        return "Belly" if n.z < -0.5 else "Base"
    P.obj("Fuselage", loft([(2.05, 0.3, 0.3, 0, 0.0), (1.6, 0.58, 0.6, 0, -0.02), (0.8, 0.68, 0.7, 0, 0.0), (-0.2, 0.58, 0.6, 0, 0.05),
                            (-1.2, 0.36, 0.38, 0, 0.12), (-2.0, 0.12, 0.14, 0, 0.18)], 16), chest, 1)
    # the head on top at the front: round, orange eyes, a scowl
    P.obj("Head", ball((0, 1.45, 0.55), (0.34, 0.32, 0.3), 14, 7), "Base", 1)
    face_eyes(P, 1.72, 0.62, 0.15, 0.085, "Lamp", True, "Dark", "Belly")
    P.obj("Cheek", ball((0, 1.65, 0.42), (0.26, 0.16, 0.08), 10, 4), "Glass")
    # the beak: the spinner is a gold beak; the propeller turns behind it
    P.prop((0, 2.12, 0.0), 0.95, 3, blade="Metal", tip="Trim", spinner="Trim", spinner_len=0.5)
    # the crown on his head: a band, five points with pearls, a red cap and a gem
    P.obj("CrownBand", lathe([(0.2, 0.0), (0.21, 0.13), (0.19, 0.13), (0.18, 0.0)], 14, "z", (0, 1.4, 0.78)), "Trim")
    P.obj("CrownCap", ball((0, 1.4, 0.92), (0.17, 0.17, 0.12), 10, 5), "Accent")
    for k in range(5):
        a = 2 * math.pi * k / 5
        b = Vector((math.sin(a) * 0.2, 1.4 + math.cos(a) * 0.2, 0.9))
        P.obj("CrownPoint", cone(b, b + Vector((0, 0, 0.16)), 0.06, 4), "Trim", 0, False)
        P.obj("Pearl", ball(tuple(b + Vector((0, 0, 0.18))), (0.035, 0.035, 0.035), 6, 3), "Belly")
    P.obj("CrownGem", ball((0, 1.61, 0.85), (0.05, 0.03, 0.05), 8, 4), "Lamp")
    # the pilot rides on the back, under the crown's eye
    pilot(P, 0.25, 0.6, "Trim", "Glass", "Accent")
    # the wings: grey feathers, two dark bars, fingered tips
    def wpaint(c, n):
        if n.z < -0.5: return "Belly"
        x = abs(c.x)
        if 1.0 < x < 1.15 or 1.45 < x < 1.6: return "Dark"
        return "Base"
    wing_flat(P, [(0.5, 0.75), (2.0, 0.55), (2.6, 0.2), (2.75, -0.15), (2.45, -0.35), (2.5, -0.55), (2.1, -0.5), (2.05, -0.75), (1.6, -0.6), (0.5, -0.55)],
              wpaint, -0.05, 0.1, "Wing", 6)
    # the tail: a fanned tail of feathers with a royal red cape fin above it, gold edged
    for k in range(7):
        a = math.radians(-36 + 12 * k)
        b = Vector((0, -1.9, 0.15))
        P.obj("TailFeather", hull([b + Vector((-0.07, 0, 0)), b + Vector((0.07, 0, 0)), b + Vector((math.sin(a) * 0.9 - 0.1, -math.cos(a) * 0.9, 0.0)),
                                   b + Vector((math.sin(a) * 0.9 + 0.1, -math.cos(a) * 0.9, 0.0)), b + Vector((math.sin(a) * 0.5, -math.cos(a) * 0.5, 0.05))]),
              "Dark" if k in (0, 6) else "Base", 0, False)
    fin_flat(P, [(-1.0, 0.45), (-1.55, 1.25), (-2.1, 1.3), (-2.2, 0.3)], lambda c, n: "Trim" if c.z > 1.18 or c.y < -2.1 else "Accent", "Cape", 0.04)
    P.obj("Medallion", ball((0, 1.9, -0.15), (0.12, 0.05, 0.12), 10, 5), "Trim")
    # little coral feet tucked under
    for s in (1, -1):
        P.obj("Foot", pipe([(s * 0.25, 0.4, -0.6), (s * 0.27, 0.6, -0.8), (s * 0.27, 0.8, -0.82)], [0.05, 0.04, 0.03], 6), "Lamp")
    return P


# ================================================================= DESERT 1: the pharaoh cobra jet
def Q_desert():
    P = Plane("desert", {"Base": ((0.10, 0.22, 0.62), 0.55), "Belly": ((0.95, 0.85, 0.55), 0.5), "Accent": ((0.85, 0.15, 0.12), 0.5),
                         "Trim": ((1.0, 0.78, 0.22), 0.85), "Glass": ((0.15, 0.85, 0.55), 0.9), "Dark": ((0.05, 0.04, 0.06), 0.4),
                         "Glow": ((0.25, 1.0, 0.55), 0.5), "Metal": ((0.62, 0.55, 0.40), 0.75), "Lamp": ((1.0, 0.85, 0.30), 0.8)})
    # the body: a long cobra, lapis with gold rings, a pale scaled belly
    def scales(c, n):
        if n.z < -0.4: return "Belly"
        if (c.y * 3.0) % 1.0 < 0.18: return "Trim"
        return "Base"
    P.obj("Fuselage", loft([(1.9, 0.3, 0.26, 0, 0.0), (1.2, 0.38, 0.34, 0, 0.0), (0.2, 0.4, 0.36, 0, 0.02), (-0.9, 0.34, 0.3, 0, 0.04),
                            (-1.9, 0.24, 0.22, 0, 0.06), (-2.4, 0.2, 0.18, 0, 0.06)], 14), scales, 1)
    # the cobra head as the nose: a flat wide head, glowing slit eyes, fangs, a forked tongue
    P.obj("CobraHead", loft([(2.8, 0.08, 0.05, 0, 0.0), (2.62, 0.36, 0.2, 0, 0.0), (2.3, 0.48, 0.28, 0, 0.03), (1.9, 0.36, 0.28, 0, 0.0)], 14),
          lambda c, n: "Belly" if n.z < -0.4 else ("Trim" if abs(c.x) < 0.05 else "Base"), 1)
    for s in (1, -1):
        P.obj("Eye", ball((s * 0.27, 2.42, 0.2), (0.09, 0.13, 0.07), 8, 4), "Glow")
        P.obj("Slit", ball((s * 0.29, 2.47, 0.21), (0.015, 0.1, 0.055), 6, 3), "Dark")
        P.obj("Brow", hull([(s * 0.1, 2.52, 0.3), (s * 0.4, 2.38, 0.34), (s * 0.4, 2.33, 0.28), (s * 0.1, 2.48, 0.25)]), "Trim", 0, False)
        P.obj("Fang", cone((s * 0.16, 2.62, -0.06), (s * 0.15, 2.64, -0.28), 0.04, 5), "Belly", 0, False)
    P.obj("Tongue", pipe(bez((0, 2.7, -0.04), (0, 2.85, -0.06), (0.05, 2.95, -0.1), (0.07, 3.02, -0.12), 4), [0.022, 0.02, 0.016, 0.01, 0.0], 5), "Accent")
    P.obj("Tongue", pipe(bez((0, 2.9, -0.08), (-0.03, 2.97, -0.1), (-0.06, 3.02, -0.11), (-0.08, 3.04, -0.12), 3), [0.012, 0.01, 0.006, 0.0], 4), "Accent")
    # the flared hood behind the head, gold rimmed with an emerald eye-mark, a pharaoh's uraeus crest on top
    hood = [(0, 1.55, 0.25)]
    for k in range(13):
        a = math.radians(-100 + 200 * k / 12)
        hood.append((math.sin(a) * 0.62, 1.5 - 0.12 * abs(math.sin(a)), 0.25 + math.cos(a) * 0.48))
    polys = [[hood[0], hood[i], hood[i + 1]] for i in range(1, 13)]
    bm = bmesh.new()
    for poly in polys:
        f = [bm.verts.new(Vector(p) + Vector((0, 0.03, 0))) for p in poly]; g = [bm.verts.new(Vector(p) - Vector((0, 0.03, 0))) for p in poly]
        bm.faces.new(f); bm.faces.new(list(reversed(g)))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    P.obj("Hood", bm, lambda c, n: "Trim" if (Vector((c.x, 0, c.z - 0.25)).length > 0.47) else ("Belly" if n.y > 0 and abs(c.x) < 0.2 else "Base"), 0, False)
    for s in (1, -1):
        P.obj("HoodGem", ball((s * 0.42, 1.58, 0.55), (0.1, 0.03, 0.12), 8, 4), "Glass")
    P.obj("Uraeus", pipe(bez((0, 1.5, 0.9), (0, 1.55, 1.05), (0, 1.65, 1.1), (0, 1.72, 1.02), 4), [0.05, 0.045, 0.04, 0.035, 0.02], 6), "Trim")
    # the pilot behind the hood, in a little nemes headdress
    pilot(P, 0.55, 0.38, "Trim", "Glass", "Base", screen=False)
    for s in (1, -1):
        P.obj("Nemes", hull([(s * 0.1, 0.6, 0.72), (s * 0.18, 0.55, 0.6), (s * 0.2, 0.5, 0.38), (s * 0.14, 0.45, 0.35), (s * 0.12, 0.62, 0.55)]), "Base", 0, False)
    # the wings: swept like a spread hood, lapis with gold scale bands and red tips
    def wp(c, n):
        if n.z < -0.5: return "Belly"
        x = abs(c.x)
        if x > 2.3: return "Accent"
        if int(x * 3.2) % 2 == 0: return "Trim"
        return "Base"
    wing_flat(P, [(0.3, 0.8), (1.6, 0.15), (2.7, -0.6), (2.75, -0.95), (2.0, -0.8), (0.3, -0.6)], wp, -0.05, 0.1, "Wing", 4)
    # twin jets in gold, glowing green; the tail is a rattling cobra tail fin
    for s in (1, -1):
        P.obj("Engine", loft([(0.2, 0.1, 0.1, s * 0.45, -0.05), (0.0, 0.17, 0.17, s * 0.45, -0.05), (-1.6, 0.16, 0.16, s * 0.45, -0.05)], 10), "Metal", 0)
        jet_core(P, s * 0.45, -1.6, -0.05, 0.15)
    P.obj("TailCore", lathe([(0.0, -2.62), (0.16, -2.5), (0.2, -2.4)], 12, "y"), "Glow", 0)
    fin_flat(P, [(-1.4, 0.25), (-2.0, 1.05), (-2.4, 1.1), (-2.35, 0.2)], lambda c, n: "Trim" if c.z > 0.95 else ("Accent" if (c.z * 5) % 1.0 < 0.25 else "Base"), "Fin", 0.04)
    wing_flat(P, [(0.2, -1.9), (1.1, -2.3), (1.1, -2.5), (0.2, -2.45)], lambda c, n: "Trim", 0.05, 0.05, "Stab")
    P.obj("Ankh", torus(0.08, 0.025, 0.0, 10, 4), "Trim"); P.parts[-1].data.transform(Matrix.Translation((0.05, -2.1, 0.85)) @ Matrix.Rotation(math.radians(90), 4, "Y"))
    return P


# ================================================================= DESERT 2: the anubis
def Q_desert2():
    P = Plane("desert2", {"Base": ((0.07, 0.07, 0.10), 0.5), "Belly": ((0.92, 0.82, 0.55), 0.45), "Accent": ((0.10, 0.30, 0.72), 0.55),
                          "Trim": ((1.0, 0.78, 0.22), 0.85), "Glass": ((0.80, 0.18, 0.12), 0.6), "Dark": ((0.03, 0.03, 0.04), 0.4),
                          "Glow": ((1.0, 0.65, 0.10), 0.5), "Metal": ((0.50, 0.46, 0.38), 0.7), "Lamp": ((1.0, 0.90, 0.35), 0.8)})
    # the body: black with gold bands
    P.obj("Fuselage", loft([(1.65, 0.36, 0.36, 0, 0.0), (1.2, 0.46, 0.46, 0, 0.0), (0.2, 0.44, 0.46, 0, 0.03), (-1.0, 0.3, 0.32, 0, 0.08),
                            (-2.2, 0.1, 0.12, 0, 0.18)], 16), lambda c, n: "Trim" if (c.y * 2.2) % 1.0 < 0.12 else ("Belly" if n.z < -0.5 else "Base"), 1)
    # the jackal head as the cowl: a long muzzle beneath the propeller hub, glowing eyes, tall gold-edged ears up front
    P.obj("Snout", loft([(2.35, 0.06, 0.05, 0, -0.32), (2.15, 0.14, 0.11, 0, -0.3), (1.8, 0.22, 0.18, 0, -0.24), (1.5, 0.3, 0.26, 0, -0.16)], 12),
          lambda c, n: "Base", 1)
    P.obj("Nose", ball((0, 2.36, -0.3), (0.06, 0.05, 0.05), 8, 4), "Dark")
    P.obj("Collar", torus(0.5, 0.07, 0.0, 22, 6), lambda c, n: "Accent" if (math.atan2(c.x, c.z) * 4) % 1.0 < 0.5 else "Trim")
    P.parts[-1].data.transform(Matrix.Translation((0, 1.2, 0)) @ Matrix.Rotation(math.radians(90), 4, "X"))
    face_eyes(P, 1.85, 0.12, 0.2, 0.08, "Glow", True, "Trim", "Belly")
    for s in (1, -1):
        ear = [(s * 0.1, 1.5, 0.3), (s * 0.4, 1.4, 0.34), (s * 0.34, 1.48, 1.25), (s * 0.22, 1.58, 0.4)]
        P.obj("Ear", hull(ear + [(s * 0.24, 1.4, 0.4)]), "Base", 0, False)
        P.obj("EarIn", hull([(s * 0.15, 1.6, 0.42), (s * 0.33, 1.55, 0.44), (s * 0.31, 1.58, 1.1), (s * 0.22, 1.64, 0.46), (s * 0.24, 1.62, 0.7)]), "Trim", 0, False)
    P.prop((0, 2.05, 0.08), 0.85, 4, blade="Dark", tip="Trim", spinner="Trim", spinner_len=0.35)
    pilot(P, 0.4, 0.44, "Trim", "Glow", "Accent")
    # the wings: egyptian feathered wings in bands of gold, lapis and red, the feather tips cut in a saw edge
    def wp(c, n):
        if n.z < -0.5: return "Belly"
        u = c.y + abs(c.x) * 0.1
        if u > 0.35: return "Trim"
        if u > -0.05: return "Accent"
        if u > -0.3: return "Glass"
        return "Trim"
    outline = [(0.45, 0.75), (2.0, 0.6), (2.85, 0.35)]
    for k in range(8):
        x = 2.85 - k * 0.32
        outline += [(x, -0.15 - 0.04 * k), (x - 0.16, -0.55 - 0.03 * k)]
    outline += [(0.45, -0.7)]
    wing_flat(P, outline, wp, -0.1, 0.1, "Wing", 5)
    wing_flat(P, [(0.15, -1.6), (1.05, -1.95), (1.05, -2.2), (0.15, -2.15)], lambda c, n: "Trim", 0.12, 0.05, "Stab")
    fin_flat(P, [(-1.4, 0.3), (-1.95, 1.0), (-2.3, 1.05), (-2.25, 0.2)], lambda c, n: "Trim" if c.z > 0.9 else "Accent", "Fin", 0.04)
    # a gold ankh on the fin, an eye of horus on the belly
    P.obj("Ankh", torus(0.09, 0.025, 0.0, 10, 4), "Trim"); P.parts[-1].data.transform(Matrix.Translation((0.05, -1.95, 0.71)) @ Matrix.Rotation(math.radians(90), 4, "Y"))
    P.obj("AnkhBar", box((0.05, -1.95, 0.6), (0.03, 0.22, 0.04)), "Trim", 0, False)
    P.obj("AnkhStem", box((0.05, -1.95, 0.5), (0.03, 0.04, 0.22)), "Trim", 0, False)
    P.obj("Scarab", ball((0, 0.6, -0.48), (0.16, 0.22, 0.06), 10, 4), "Accent")
    return P


# ================================================================= JAPAN 1: the oni fighter
def Q_japan():
    P = Plane("japan", {"Base": ((0.80, 0.12, 0.10), 0.5), "Belly": ((0.95, 0.92, 0.85), 0.4), "Accent": ((0.10, 0.10, 0.12), 0.5),
                        "Trim": ((1.0, 0.78, 0.22), 0.85), "Glass": ((0.95, 0.92, 0.85), 0.6), "Dark": ((0.04, 0.03, 0.03), 0.4),
                        "Glow": ((1.0, 0.50, 0.08), 0.5), "Metal": ((0.38, 0.38, 0.42), 0.6), "Lamp": ((1.0, 0.90, 0.25), 0.8)})
    P.obj("Fuselage", loft([(1.9, 0.44, 0.44, 0, 0.0), (1.5, 0.48, 0.48, 0, 0.0), (0.4, 0.42, 0.44, 0, 0.04), (-1.0, 0.28, 0.3, 0, 0.1),
                            (-2.3, 0.08, 0.1, 0, 0.2)], 16), lambda c, n: "Accent" if (c.y * 2.5) % 1.0 < 0.1 else ("Belly" if n.z < -0.55 else "Base"), 1)
    # the oni mask on the nose: brows like flames, glowing eyes, a wide grin with fangs and two tusks, a gold horn on each side of the brow
    P.obj("Mask", ball((0, 1.95, 0.0), (0.5, 0.18, 0.46), 14, 7), "Base", 1)
    face_eyes(P, 2.05, 0.15, 0.2, 0.1, "Lamp", True, "Accent", "Glass")
    P.obj("MaskNose", ball((0, 2.14, 0.0), (0.09, 0.07, 0.07), 8, 4), "Base")
    P.obj("Grin", ball((0, 2.05, -0.2), (0.3, 0.08, 0.08), 12, 5), "Dark")
    for k in range(5):
        x = (k - 2) * 0.1
        P.obj("Tooth", cone((x, 2.11, -0.14), (x, 2.13, -0.22), 0.03, 4), "Glass", 0, False)
    for s in (1, -1):
        P.obj("Tusk", pipe(bez((s * 0.2, 2.09, -0.22), (s * 0.24, 2.15, -0.1), (s * 0.26, 2.15, 0.0), (s * 0.24, 2.13, 0.06), 3), [0.045, 0.035, 0.02, 0.0], 6), "Glass")
        P.obj("Horn", pipe(bez((s * 0.25, 1.95, 0.35), (s * 0.35, 1.95, 0.6), (s * 0.45, 1.85, 0.75), (s * 0.55, 1.7, 0.85), 5), [0.09, 0.075, 0.06, 0.04, 0.02, 0.0], 8), "Trim")
        P.obj("HornRing", torus(0.085, 0.022, 0.0, 10, 4), "Accent"); P.parts[-1].data.transform(Matrix.Translation((s * 0.28, 1.95, 0.42)))
    # flame hair crest running back over the cowl
    for k in range(5):
        y = 1.75 - k * 0.15
        b = Vector((0, y, 0.42 - k * 0.02))
        P.obj("FlameHair", pipe(bez(b, b + Vector((0, -0.05, 0.15)), b + Vector((0.04 * (k % 2 * 2 - 1), -0.15, 0.3)), b + Vector((0, -0.25, 0.38 - k * 0.03)), 4),
                                [0.08, 0.07, 0.05, 0.03, 0.0], 6), "Glow" if k % 2 else "Lamp", 0)
    P.prop((0, 2.2, 0.0), 0.92, 3, blade="Accent", tip="Trim", spinner="Trim", spinner_len=0.3)
    pilot(P, 0.6, 0.44, "Accent", "Glow", "Base")
    # wings: red with black bands, flame tips
    def wp(c, n):
        if n.z < -0.5: return "Belly"
        x = abs(c.x)
        if x > 2.35: return "Glow"
        if 1.3 < x < 1.45: return "Accent"
        return "Base"
    wing_flat(P, [(0.3, 0.7), (2.2, 0.45), (2.55, 0.5), (2.95, 0.3), (2.6, 0.05), (2.9, -0.15), (2.45, -0.25), (2.6, -0.45), (2.0, -0.35), (0.3, -0.5)],
              wp, -0.15, 0.1, "Wing", 5)
    wing_flat(P, [(0.15, -1.7), (1.0, -2.0), (1.05, -2.25), (0.15, -2.25)], lambda c, n: "Base", 0.15, 0.05, "Stab")
    fin_flat(P, [(-1.5, 0.3), (-2.0, 0.95), (-2.35, 1.0), (-2.3, 0.2)], lambda c, n: "Accent" if c.z > 0.85 else "Base", "Fin", 0.04)
    P.obj("Club", loft([(0.1, 0.04, 0.04, 0, -0.55), (-0.2, 0.1, 0.1, 0, -0.55), (-1.2, 0.14, 0.14, 0, -0.55), (-1.3, 0.05, 0.05, 0, -0.55)], 8), "Metal", 0)
    for k in range(5):
        y = -0.3 - k * 0.2
        for a in (0, 2.1, 4.2):
            P.obj("Stud", cone((math.sin(a) * 0.12, y, -0.55 + math.cos(a) * 0.12), (math.sin(a) * 0.22, y, -0.55 + math.cos(a) * 0.22), 0.035, 4), "Trim", 0, False)
    return P


# ================================================================= JAPAN 2: the shogun jet
def Q_japan2():
    P = Plane("japan2", {"Base": ((0.72, 0.08, 0.10), 0.7), "Belly": ((0.10, 0.10, 0.12), 0.6), "Accent": ((0.06, 0.06, 0.08), 0.7),
                         "Trim": ((1.0, 0.80, 0.25), 0.9), "Glass": ((0.30, 0.95, 1.0), 0.95), "Dark": ((0.03, 0.03, 0.04), 0.4),
                         "Glow": ((0.25, 0.95, 1.0), 0.5), "Metal": ((0.82, 0.86, 0.92), 0.85), "Lamp": ((1.0, 0.25, 0.20), 0.8)})
    # lacquered armour: red plates laced in black rows, a black belly
    def armour(c, n):
        if c.y > 1.85: return "Accent"   # the black menpo face-guard
        if n.z < -0.5: return "Belly"
        if (c.y * 4.0) % 1.0 < 0.12: return "Trim" if abs(c.x) < 0.08 else "Accent"
        return "Base"
    P.obj("Fuselage", loft([(2.8, 0.03, 0.03, 0, -0.05), (2.35, 0.2, 0.18, 0, -0.03), (1.6, 0.36, 0.34, 0, 0.0), (0.6, 0.42, 0.4, 0, 0.02),
                            (-0.6, 0.42, 0.4, 0, 0.03), (-1.8, 0.36, 0.34, 0, 0.04), (-2.2, 0.34, 0.32, 0, 0.04)], 14, sq=1.35), armour, 1)
    # the menpo face-guard on the nose: a black mask with glowing slit eyes and a gold moustache
    for s in (1, -1):
        P.obj("EyeSlit", hull([(s * 0.05, 2.25, 0.13), (s * 0.3, 2.0, 0.2), (s * 0.31, 1.98, 0.12), (s * 0.06, 2.22, 0.06), (s * 0.2, 2.13, 0.2)]), "Glow", 0, False)
        P.obj("Moustache", pipe(bez((0, 2.3, -0.05), (s * 0.12, 2.25, -0.08), (s * 0.2, 2.15, -0.04), (s * 0.28, 2.05, 0.02), 3), [0.03, 0.03, 0.02, 0.0], 5), "Trim")
    # shoulder-guard plates over the wing roots (sode)
    for s in (1, -1):
        for k in range(3):
            P.obj("Sode", box((s * (0.55 + k * 0.05), 0.55 - k * 0.12, 0.25 - k * 0.1), (0.36, 0.5, 0.06), Matrix.Rotation(math.radians(s * -28), 3, "Y")), "Base" if k % 2 == 0 else "Accent", 0, False)
    # the cockpit under a kabuto: the pilot, a gold crescent crest (maedate) rising over him, a glowing cyan visor
    pilot(P, 0.9, 0.38, "Accent", "Glass", "Base")
    arc = [Vector((math.sin(t) * 0.48, 1.08, 0.72 + math.cos(t) * 0.38)) for t in [math.radians(-80 + 160 * i / 10) for i in range(11)]]
    P.obj("Maedate", pipe(arc, [0.0] + [0.05 * math.sin(math.pi * i / 10) + 0.012 for i in range(1, 10)] + [0.0], 6), "Trim")
    P.obj("Crest", ball((0, 1.08, 0.48), (0.07, 0.04, 0.07), 8, 4), "Lamp")
    # wings: sharp, red with black lacing and a red sun disc on each
    def wp(c, n):
        if n.z < -0.5: return "Belly"
        d = Vector((abs(c.x) - 1.6, c.y + 0.25, 0)).length
        if d < 0.3: return "Belly" if d > 0.22 else "Lamp"
        if abs(c.x) > 2.5: return "Trim"
        return "Base"
    wing_flat(P, [(0.35, 0.6), (2.0, -0.2), (2.85, -0.85), (2.5, -0.95), (0.35, -0.85)], wp, -0.05, 0.08, "Wing", 0)
    # twin jets with cyan cores and gatling barrels under the wings
    for s in (1, -1):
        jet_core(P, s * 0.25, -2.2, 0.04, 0.2)
        P.obj("GunPod", loft([(0.5, 0.08, 0.08, s * 1.3, -0.18), (0.3, 0.12, 0.12, s * 1.3, -0.18), (-0.4, 0.12, 0.12, s * 1.3, -0.18)], 8), "Accent", 0)
        for k in range(4):
            a = 2 * math.pi * k / 4
            P.obj("Barrel", tube(0.5, 1.0, 0.025, 0.025, s * 1.3 + math.sin(a) * 0.06, -0.18 + math.cos(a) * 0.06, 5), "Metal", 0)
    # the katana fin: a silver curved blade standing on a gold tsuba with a black-wrapped grip
    blade = [(-1.25, 0.4), (-1.55, 1.2), (-1.85, 1.75), (-2.1, 1.72), (-1.95, 1.25), (-1.75, 0.4)]
    fin_flat(P, blade, lambda c, n: "Metal", "Katana", 0.05)
    P.obj("Tsuba", lathe([(0.0, -0.03), (0.2, -0.03), (0.2, 0.03), (0.0, 0.03)], 12, "z", (0, -1.5, 0.38)), "Trim")
    P.obj("Hilt", box((0, -1.5, 0.28), (0.1, 0.4, 0.14)), "Accent", 0, False)
    wing_flat(P, [(0.2, -1.6), (1.1, -2.1), (1.1, -2.3), (0.2, -2.3)], lambda c, n: "Base", 0.05, 0.05, "Stab")
    # two sashimono banners on the back
    for s in (1, -1):
        P.obj("Pole", pipe([(s * 0.25, -0.4, 0.3), (s * 0.25, -0.5, 1.15)], [0.02, 0.02], 4), "Accent")
        P.obj("Banner", box((s * 0.25, -0.62, 0.85), (0.02, 0.22, 0.5)), "Trim", 0, False)
        P.obj("BannerSun", ball((s * 0.28, -0.62, 0.9), (0.02, 0.08, 0.08), 6, 3), "Lamp")
    return P


PLANES = [("city", Q_city), ("city2", Q_city2), ("desert", Q_desert), ("desert2", Q_desert2), ("japan", Q_japan), ("japan2", Q_japan2)]

if __name__ == "__main__":
    os.makedirs(EP.OUT, exist_ok=True)
    for pid, fn in PLANES:
        if ONLY and pid not in ONLY: continue
        fn().finish()
    print("DONE")
