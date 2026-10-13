# Sky Squad, the camping forest's five bosses (2026-10-10: "bosses now for the camping forest"), the night by the fire: the firefly queen,
# the great horned owl, the lantern balloon, the star bear and the forest guardian. Built from code like the alien / sea / lava bosses
# (alien_bosses.py lends its Boss class and shapes).
# Run: blender -b -P Tools/blender/camping_bosses.py -- <out dir> [export] [ids,comma,separated]
# Conventions as alien_bosses.py: +Y nose, +Z up, +X right; "Prop*" spin about the nose, "Flap*" rock about the nose axis, "Sway*" about the
# wing axis, "Spin*" turn slowly about up, "Cloth" stays still without the outline, "Muzzle" is where his shots leave from.
import bpy, bmesh, math, sys, os, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mathutils import Vector, Matrix
from enemy_planes import loft, sweep, lathe, box, hull, tube, mirror_x, airfoil
import alien_bosses as AB
from alien_bosses import Boss, xf, ball, pipe, cone, bez, torus, sheet, grow, ang

import bmesh
from mathutils.bvhtree import BVHTree
from enemy_planes import loft, sweep, lathe, box, hull, tube, mirror_x, airfoil
from alien_bosses import Boss, xf, ball, pipe, cone, bez, torus, sheet, grow, ang, lerp_keys, spine_frames, body_loft, skin, oriented_ball, frame, sheet_solid, ribbon

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ONLY = argv[2].split(",") if len(argv) > 2 and argv[2] else None


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

def blob(c, r, n=24, seg=10):
    """a rounded wing outline: n points round an ellipse-ish shape, a fan from its first point."""
    return [Vector(c) + Vector((math.cos(2 * math.pi * i / n) * r[0], math.sin(2 * math.pi * i / n) * r[1], 0)) for i in range(n)]

def fan_sheet(center, outline, thick=0.02):
    polys = [[center, a, b] for a, b in zip(outline, outline[1:] + outline[:1])]
    return sheet([[tuple(p) for p in poly] for poly in polys], thick)

def tilt(bm, ax, deg, about):
    m = Matrix.Rotation(math.radians(deg), 3, ax)
    for v in bm.verts: v.co = m @ (v.co - Vector(about)) + Vector(about)
    return bm


# ================================================================= 1. the firefly queen
def C_balloon():
    """A patchwork hot-air balloon at night: red, cream and mustard gores with string lights round its belly, carrying a little log cabin
    with glowing windows and a chimney, lanterns hanging from its ropes, flag garlands, and a propeller at the back."""
    P = Boss("balloon", {"Base": ((0.45, 0.28, 0.15), 0.35), "Belly": ((0.95, 0.90, 0.78), 0.3), "Accent": ((0.80, 0.16, 0.12), 0.4),
                         "Trim": ((0.95, 0.70, 0.20), 0.5), "Glass": ((0.25, 0.45, 0.35), 0.4), "Dark": ((0.10, 0.07, 0.05), 0.4),
                         "Glow": ((1.0, 0.80, 0.35), 0.5), "Metal": ((0.35, 0.32, 0.3), 0.6), "Lamp": ((1.0, 0.62, 0.22), 0.8)})
    env = lathe([(0.0, 3.35), (0.55, 3.28), (0.95, 3.05), (1.2, 2.65), (1.25, 2.25), (1.12, 1.8), (0.82, 1.38), (0.45, 1.08), (0.32, 1.0)], 24, "z")
    def gores(c, n):
        k = int(((ang(c) / (2 * math.pi)) % 1.0) * 12)
        if 2.15 < c.z < 2.25: return "Glow"
        return ("Accent", "Belly", "Trim")[k % 3]
    P.obj("Envelope", env, gores, 1)
    for k in range(12):   # the string lights round its belly
        a = 2 * math.pi * (k + 0.5) / 12
        P.obj("Bulb", ball((math.sin(a) * 1.26, math.cos(a) * 1.26, 2.2), (0.06, 0.06, 0.06), 6, 3), "Lamp")
    P.obj("Crown", lathe([(0.0, 3.42), (0.18, 3.38), (0.2, 3.3)], 10, "z"), "Trim")
    # the cabin: a log hut with a roof, windows aglow, a chimney
    P.obj("Cabin", box((0, 0, 0.0), (1.05, 0.95, 0.6)), lambda c, n: "Base" if (c.z * 8) % 1.0 > 0.15 else "Dark", 0, False)
    P.obj("Roof", hull([(-0.65, -0.55, 0.3), (0.65, -0.55, 0.3), (-0.65, 0.55, 0.3), (0.65, 0.55, 0.3), (0, -0.55, 0.72), (0, 0.55, 0.72)]), "Accent", 0, False)
    P.obj("Chimney", box((0.3, -0.2, 0.68), (0.14, 0.14, 0.3)), "Metal", 0, False)
    for s in (1, -1):
        P.obj("Window", box((s * 0.25, 0.48, 0.02), (0.22, 0.02, 0.22)), "Glow", 0, False)
        P.obj("SideWindow", box((s * 0.53, 0.0, 0.02), (0.02, 0.22, 0.22)), "Glow", 0, False)
    P.obj("Door", box((0, -0.48, -0.05), (0.24, 0.02, 0.36)), "Dark", 0, False)
    P.obj("Porch", box((0, 0.62, -0.3), (0.9, 0.3, 0.05)), "Base", 0, False)
    # the ropes up to the envelope, lanterns hanging, a garland of flags between them
    tops = [Vector((math.sin(a) * 0.38, math.cos(a) * 0.38, 1.02)) for a in [2 * math.pi * k / 4 + math.pi / 4 for k in range(4)]]
    bots = [Vector((sx * 0.5, sy * 0.45, 0.3)) for sx, sy in ((1, 1), (1, -1), (-1, -1), (-1, 1))]
    bots = [bots[0], bots[1], bots[2], bots[3]]
    for t, b in zip(sorted(tops, key=lambda v: (v.x > 0, v.y > 0)), sorted(bots, key=lambda v: (v.x > 0, v.y > 0))):
        P.obj("Rope", pipe([b, t], [0.015, 0.015], 4), "Dark")
        mid = b + (t - b) * 0.35
        P.obj("LanternLine", pipe([mid, mid + Vector((0, 0, -0.18))], [0.008, 0.008], 4), "Dark")
        P.obj("Lantern", ball(tuple(mid + Vector((0, 0, -0.26))), (0.07, 0.07, 0.09), 8, 4), "Lamp")
    for k in range(9):   # flags along the porch garland
        x = -0.48 + k * 0.12
        P.obj("Flag", hull([(x - 0.045, 0.77, -0.12), (x + 0.045, 0.77, -0.12), (x, 0.77, -0.24), (x, 0.79, -0.12)]), ("Accent", "Belly", "Trim")[k % 3], 0, False)
    P.obj("Garland", pipe([(-0.5, 0.77, -0.11), (0.5, 0.77, -0.11)], [0.008, 0.008], 4), "Dark")
    # the propeller at the back on a boom, a rudder fin
    P.obj("Boom", pipe([(0, -0.48, 0.1), (0, -0.95, 0.15)], [0.04, 0.04], 6), "Metal")
    P.prop((0, -1.0, 0.15), 0.42, 3, blade="Base", tip="Accent", spinner="Trim", spinner_len=0.12)
    P.obj("Rudder", hull([(0, -0.9, 0.35), (0, -1.3, 0.55), (0, -1.3, 0.25), (0.02, -1.1, 0.4), (-0.02, -1.1, 0.4)]), "Accent", 0, False)
    P.part("Muzzle", ball((0, 0.8, 0.0), (0.07, 0.05, 0.07), 8, 4), "Glow", (0, 0.8, 0.0))
    return P


# ================================================================= 4. the star bear
def C_bear():
    """A bear made of the night sky: a deep blue body speckled with glowing stars and joined by constellation lines, a pale starlit muzzle,
    golden eyes, legs that run through the air, and a ring of little stars circling it."""
    P = Boss("bear", {"Base": ((0.08, 0.13, 0.38), 0.85), "Belly": ((0.30, 0.42, 0.85), 0.7), "Accent": ((0.55, 0.65, 1.0), 0.8),
                      "Trim": ((0.85, 0.90, 1.0), 0.6), "Glass": ((0.6, 0.8, 1.0), 0.95), "Dark": ((0.02, 0.03, 0.08), 0.8),
                      "Glow": ((0.75, 0.90, 1.0), 0.5), "Metal": ((0.4, 0.45, 0.6), 0.6), "Lamp": ((1.0, 0.85, 0.35), 0.8)})
    body = ball((0, 0.0, 0.0), (0.72, 1.25, 0.62), 20, 10)
    stars = [v.co.copy() for v in body.verts if v.co.z > 0.0 and speckle(v.co, 1.9) < 0.12]
    P.obj("Body", body, lambda c, n: "Belly" if n.z < -0.4 else "Base", 1)
    for q in stars: P.obj("Star", ball(tuple(q * 1.03), (0.05, 0.05, 0.05), 6, 3), "Glow")
    path = sorted(stars, key=lambda v: v.y)[::2]
    for a, b in zip(path, path[1:]):
        if (a - b).length < 0.9: P.obj("Line", pipe([a * 1.03, b * 1.03], [0.012, 0.012], 4), "Accent")
    P.obj("Head", ball((0, 1.3, 0.3), (0.45, 0.42, 0.4), 16, 8), "Base", 1)
    P.obj("Snout", ball((0, 1.68, 0.2), (0.22, 0.22, 0.17), 12, 6), "Belly", 1)
    P.obj("Nose", ball((0, 1.88, 0.26), (0.08, 0.05, 0.06), 8, 4), "Dark")
    for s in (1, -1):
        P.obj("Ear", ball((s * 0.32, 1.15, 0.68), (0.13, 0.08, 0.13), 10, 5), "Base")
        P.obj("EarIn", ball((s * 0.32, 1.2, 0.68), (0.07, 0.04, 0.08), 8, 4), "Belly")
        P.obj("Eye", ball((s * 0.18, 1.62, 0.43), (0.06, 0.05, 0.06), 8, 4), "Lamp")
        P.obj("HeadStar", ball((s * 0.2, 1.35, 0.68), (0.045, 0.045, 0.045), 6, 3), "Glow")
        for fy, k in ((0.8, 0), (-0.8, 1)):   # the legs: they run through the air, each swinging on its own
            hip = Vector((s * 0.45, fy, -0.25))
            leg = pipe([hip, hip + Vector((0, 0.15 if fy > 0 else -0.15, -0.45)), hip + Vector((0, 0.3 if fy > 0 else -0.05, -0.75))], [0.22, 0.18, 0.16], 10)
            name = "Sway%d" % (k * 2 + (1 if s > 0 else 0))
            P.part(name, leg, "Base", tuple(hip), 1)
            paw = hip + Vector((0, 0.32 if fy > 0 else -0.03, -0.82))
            P.part(name, ball(tuple(paw), (0.18, 0.2, 0.1), 10, 5), "Belly", tuple(hip))
            for t in (-1, 0, 1): P.part(name, cone(paw + Vector((t * 0.08, 0.12, -0.02)), paw + Vector((t * 0.09, 0.24, -0.06)), 0.025, 4), "Trim", tuple(hip), 0, False)
    P.obj("Tail", ball((0, -1.25, 0.2), (0.15, 0.14, 0.14), 8, 4), "Glow")
    for k in range(12):   # the ring of stars circling it
        a = 2 * math.pi * k / 12
        c = Vector((math.sin(a) * 1.5, math.cos(a) * 1.75, 0.35 + 0.15 * math.sin(a * 3)))
        r = 0.09 if k % 3 == 0 else 0.05
        P.part("SpinStars", hull([c + Vector((r * 2, 0, 0)), c + Vector((-r * 2, 0, 0)), c + Vector((0, r * 2, 0)), c + Vector((0, -r * 2, 0)), c + Vector((0, 0, r)), c + Vector((0, 0, -r))]), "Glow", (0, 0, 0.35), 0, False)
    P.part("Muzzle", ball((0, 1.95, 0.18), (0.07, 0.04, 0.05), 8, 4), "Glow", (0, 1.95, 0.18))
    return P


# ================================================================= 5. the forest guardian
def C_guardian():
    """The last boss: an ancient tree spirit - a gnarled trunk with a face of glowing eyes and a moss beard, red-capped mushrooms up its bark,
    two great branch arms with lanterns hanging from them, a crown of leaves full of fireflies, and roots trailing below that sway."""
    P = Boss("guardian", {"Base": ((0.30, 0.20, 0.12), 0.25), "Belly": ((0.16, 0.36, 0.16), 0.3), "Accent": ((0.28, 0.55, 0.20), 0.3),
                          "Trim": ((0.80, 0.16, 0.10), 0.5), "Glass": ((0.95, 0.92, 0.85), 0.4), "Dark": ((0.04, 0.03, 0.02), 0.5),
                          "Glow": ((0.75, 1.0, 0.35), 0.5), "Metal": ((0.3, 0.28, 0.25), 0.5), "Lamp": ((1.0, 0.68, 0.22), 0.8)})
    rng = random.Random(5)
    bark = lambda c, n: "Dark" if (ang(c) * 5.0 + c.z * 1.5) % 1.0 < 0.08 else "Base"
    P.obj("Trunk", lathe([(0.0, -0.6), (0.55, -0.55), (0.48, 0.0), (0.42, 0.7), (0.46, 1.2), (0.55, 1.5), (0.0, 1.6)], 18, "z"), bark, 1)
    for s in (1, -1):
        P.obj("Eye", ball((s * 0.17, 0.42, 0.75), (0.09, 0.05, 0.06), 10, 5), "Glow")
        P.obj("Brow", box((s * 0.17, 0.44, 0.86), (0.2, 0.08, 0.06), Matrix.Rotation(math.radians(-s * 18), 3, "Y")), "Base", 0, False)
        # the branch arms, lanterns hanging off them
        arm = bez((s * 0.35, 0.0, 1.05), (s * 0.9, 0.1, 1.25), (s * 1.35, 0.25, 1.15), (s * 1.8, 0.35, 1.35), 7)
        P.obj("Branch", pipe(arm, [0.2, 0.17, 0.14, 0.11, 0.09, 0.07, 0.05, 0.03], 8), bark, 1)
        for k, t in enumerate((3, 5, 7)):
            q = arm[t]
            twig = q + Vector((s * 0.15, 0.1, 0.3 + 0.1 * k))
            P.obj("Twig", pipe([q, twig], [0.04, 0.015], 5), "Base")
            line_top = q + Vector((0, 0, -0.05))
            P.obj("LanternLine", pipe([line_top, line_top + Vector((0, 0, -0.28))], [0.008, 0.008], 4), "Dark")
            P.obj("Lantern", ball(tuple(line_top + Vector((0, 0, -0.38))), (0.08, 0.08, 0.1), 8, 4), "Lamp")
        for k in range(3):   # mushrooms up the bark
            y = 0.1 + 0.3 * k; z = 0.0 + 0.35 * k
            c = Vector((s * 0.45, y - 0.2, z))
            P.obj("Stalk", pipe([c, c + Vector((s * 0.12, 0, 0.05))], [0.03, 0.03], 5), "Glass")
            P.obj("Cap", ball(tuple(c + Vector((s * 0.14, 0, 0.08))), (0.12, 0.12, 0.06), 10, 4), lambda c2, n: "Glass" if speckle(c2, 3.0) < 0.25 else "Trim")
    P.obj("Mouth", ball((0, 0.4, 0.45), (0.17, 0.06, 0.09), 10, 5), "Dark")
    for k in range(7):   # the moss beard
        a = math.radians(-60 + k * 20)
        base = Vector((math.sin(a) * 0.3, 0.38 + math.cos(a) * 0.04, 0.35))
        P.obj("Moss", cone(base, base + Vector((math.sin(a) * 0.08, 0.05, -0.45 - 0.1 * (3 - abs(k - 3)))), 0.07, 5), "Accent", 0, False)
    # the crown of leaves with fireflies in it
    for k in range(11):
        a = k * 2.399; r = 0.35 + 0.08 * k
        c = (math.sin(a) * min(r, 1.4), math.cos(a) * min(r, 1.0) * 0.8 - 0.1, 1.75 + 0.25 * math.cos(k * 1.3))
        P.obj("Leaves", ball(c, (0.55, 0.5, 0.42), 16, 8), lambda c2, n: "Accent" if n.z > 0.35 else "Belly", 0)
    for k in range(18):
        a = k * 2.1; r = 0.5 + 0.06 * k
        P.obj("Firefly", ball((math.sin(a) * min(r, 1.6), math.cos(a) * min(r, 1.1) * 0.8 + 0.3, 1.55 + 0.5 * speckle(Vector((k, 1, 2)))), (0.04, 0.04, 0.04), 6, 3), "Glow")
    # roots trailing below, swaying
    for k in range(6):
        a = 2 * math.pi * k / 6 + 0.3
        out = Vector((math.sin(a), math.cos(a), 0))
        p0 = out * 0.35 + Vector((0, 0, -0.5))
        pts = bez(p0, p0 + out * 0.35 + Vector((0, 0, -0.3)), p0 + out * 0.55 + Vector((0, 0.1, -0.75)), p0 + out * 0.45 + Vector((0, 0.15, -1.05)), 6)
        P.part("Sway%d" % k, pipe(pts, [0.13, 0.11, 0.09, 0.07, 0.05, 0.03, 0.0], 8), bark, tuple(p0), 1)
    P.part("Muzzle", ball((0, 0.47, 0.45), (0.08, 0.04, 0.05), 8, 4), "Lamp", (0, 0.47, 0.45))
    return P


# ================================================================= 2026-10-11: three new ones with faces ("new shapes, with features, grand")
def curve(*segs):
    """bezier pieces joined end to start (each 4 points), sampled 8 per piece, as one outline."""
    out = []
    for sg in segs: out += bez(*sg, 8)[:-1]
    return out

def wing_polys(center, outline, rings=7):
    """a flat wing as a polar grid from an inner point to its outline (so it can be painted face by face)."""
    c = Vector(center); polys = []
    o = [Vector(p) for p in outline]
    for i in range(len(o)):
        a, b = o[i], o[(i + 1) % len(o)]
        for j in range(rings):
            u0, u1 = j / rings, (j + 1) / rings
            p = [c + (a - c) * u0, c + (b - c) * u0, c + (b - c) * u1, c + (a - c) * u1]
            polys.append([tuple(q) for q in (p[1:] if j == 0 else p)])
    return polys


# ----------------------------------------------------------------- the campfire king (in place of the lantern balloon)
def rear(P, deg, head_deg, head_names, head_c):
    """the whole boss pitched by deg about the wing axis (nose down when negative, so the top of a flat wing faces the player); the parts named in head_names only by
    head_deg about their own centre so the face still looks ahead. Paint was laid on before, so nothing is repainted."""
    Rb = Matrix.Rotation(math.radians(deg), 4, "X")
    hc = Rb @ Vector(head_c)
    Rh = Matrix.Translation(hc) @ Matrix.Rotation(math.radians(head_deg - deg), 4, "X") @ Matrix.Translation(-hc)
    for ob in P.parts:
        m = Rb if ob.name.split(".")[0] not in head_names else Rh @ Rb
        ob.data.transform(m)
    for ob in P.spin:
        loc = Rb @ Vector(ob.location)
        ob.data.transform(Matrix.Rotation(math.radians(deg), 4, "X"))
        ob.location = loc


# ----------------------------------------------------------------- the luna moth empress (in place of the star bear)
def C_bigfoot():
    """The last boss: Bigfoot, the king of the woods - a towering shaggy giant striding through the air on enormous feet, a broad leathery
    face with a heavy brow, glowing amber eyes and a fanged grin, great antlers hung with lanterns and crowned in gold, a royal red cloak
    with a fur collar, a lantern staff in one fist and a log club in the other, fireflies circling him."""
    P = Boss("bigfoot", {"Base": ((0.36, 0.22, 0.12), 0.15), "Belly": ((0.66, 0.48, 0.34), 0.25), "Accent": ((0.62, 0.07, 0.09), 0.4),
                         "Trim": ((1.0, 0.78, 0.26), 0.85), "Glass": ((0.97, 0.95, 0.88), 0.5), "Dark": ((0.05, 0.03, 0.02), 0.5),
                         "Glow": ((0.80, 1.0, 0.40), 0.5), "Metal": ((0.30, 0.28, 0.26), 0.6), "Lamp": ((1.0, 0.70, 0.20), 0.8)})
    fur = lambda c, n: "Base"
    # the torso, chest and shaggy fur
    P.obj("Torso", lathe([(0.0, -0.75), (0.55, -0.7), (0.68, -0.2), (0.86, 0.4), (0.93, 0.75), (0.55, 1.05), (0.0, 1.1)], 22, "z"), "Base", 1)
    P.obj("Chest", ball((0, 0.8, 0.38), (0.42, 0.13, 0.4), 16, 8), "Belly", 1)
    rng = random.Random(3)
    for k in range(0):
        a = rng.uniform(0, 2 * math.pi); z = rng.uniform(-0.65, 0.8)
        if math.cos(a) > 0.55 and -0.15 < z < 0.7: continue   # keep the chest bare
        r = 0.7 + 0.1 * math.sin(z * 2)
        b = Vector((math.sin(a) * r, math.cos(a) * r, z))
        P.obj("Shag", cone(b, b + Vector((math.sin(a) * 0.18, math.cos(a) * 0.14, -0.15)), 0.09, 4), "Base", 0, False)
    # the head and his face
    P.obj("Head", ball((0, 0.2, 1.4), (0.55, 0.5, 0.52), 18, 9), fur, 1)
    P.obj("Face", ball((0, 0.52, 1.3), (0.42, 0.2, 0.38), 16, 8), "Belly", 1)
    P.obj("BrowRidge", hull([(-0.36, 0.62, 1.5), (0.36, 0.62, 1.5), (-0.4, 0.5, 1.6), (0.4, 0.5, 1.6), (0, 0.7, 1.45), (-0.3, 0.6, 1.42), (0.3, 0.6, 1.42), (0, 0.55, 1.62)]), "Base", 0, False)
    for s in (1, -1):
        P.obj("EyeWhite", ball((s * 0.16, 0.66, 1.38), (0.13, 0.06, 0.1), 12, 6), "Glass")
        P.obj("Iris", ball((s * 0.15, 0.7, 1.37), (0.08, 0.035, 0.08), 10, 5), "Lamp")
        P.obj("Pupil", ball((s * 0.145, 0.725, 1.37), (0.035, 0.015, 0.04), 8, 4), "Dark")
        P.obj("Brow", hull([(s * 0.04, 0.73, 1.48), (s * 0.32, 0.68, 1.56), (s * 0.32, 0.62, 1.52), (s * 0.05, 0.68, 1.44)]), "Dark", 0, False)
        P.obj("Ear", ball((s * 0.47, 0.2, 1.38), (0.08, 0.1, 0.13), 8, 4), "Belly")
        for k in range(4):   # cheek whiskers of fur
            b = Vector((s * 0.32, 0.45, 1.25 - k * 0.08))
            P.obj("Whisk", cone(b, b + Vector((s * 0.22, -0.02, -0.08 - k * 0.02)), 0.06, 4), "Base", 0, False)
        # antlers: a great branching rack, gold tipped, lanterns hanging
        root = Vector((s * 0.28, 0.15, 1.75))
        main = bez(root, root + Vector((s * 0.25, 0.0, 0.25)), root + Vector((s * 0.65, -0.05, 0.35)), root + Vector((s * 0.95, -0.1, 0.65)), 7)
        P.obj("Antler", pipe(main, [0.08, 0.075, 0.07, 0.06, 0.05, 0.045, 0.035, 0.02], 7), "Belly")
        P.obj("AntlerTip", ball(tuple(main[-1]), (0.04, 0.04, 0.04), 6, 3), "Trim")
        for t, (dx, dz) in ((2, (0.05, 0.4)), (4, (0.1, 0.45)), (6, (0.25, 0.25))):
            q = main[t]; tip = q + Vector((s * dx, 0.08, dz))
            P.obj("Tine", pipe([q, tip], [0.045, 0.02], 6), "Belly")
            P.obj("AntlerTip", ball(tuple(tip), (0.03, 0.03, 0.03), 6, 3), "Trim")
        for t in (3, 5):
            q = main[t]
            P.obj("LanternLine", pipe([q, q + Vector((0, 0, -0.22))], [0.008, 0.008], 4), "Dark")
            P.obj("LanternCap", lathe([(0.0, -0.2), (0.07, -0.24), (0.05, -0.26)], 8, "z", tuple(q)), "Metal")
            P.obj("Lantern", lathe([(0.05, -0.26), (0.055, -0.38), (0.0, -0.4)], 8, "z", tuple(q)), "Lamp")
    # the fanged grin and a broad nose
    P.obj("Nose", ball((0, 0.72, 1.26), (0.12, 0.07, 0.08), 10, 5), "Dark")
    P.obj("Mouth", ball((0, 0.66, 1.1), (0.24, 0.07, 0.09), 14, 6), "Dark")
    for s in (1, -1):
        P.obj("Fang", cone((s * 0.11, 0.71, 1.17), (s * 0.1, 0.73, 1.05), 0.035, 4), "Glass", 0, False)
        P.obj("Tusk", cone((s * 0.17, 0.69, 1.05), (s * 0.18, 0.72, 1.17), 0.03, 4), "Glass", 0, False)
    # the gold crown between the antlers
    P.obj("Crown", lathe([(0.36, 1.74), (0.4, 1.74), (0.38, 1.96), (0.34, 1.96)], 22, "z", (0, 0.15, 0)), "Trim")
    for k in range(6):
        a = 2 * math.pi * k / 6
        b = Vector((math.sin(a) * 0.37, 0.15 + math.cos(a) * 0.37, 1.94))
        P.obj("CrownPoint", cone(b, b + Vector((0, 0, 0.3)), 0.08, 4), "Trim", 0, False)
        P.obj("CrownPearl", ball(tuple(b + Vector((0, 0, 0.32))), (0.04, 0.04, 0.04), 6, 3), "Glass")
        P.obj("CrownGem", ball(tuple(b + Vector((math.sin(a) * 0.02, math.cos(a) * 0.02, -0.07))), (0.04, 0.04, 0.04), 6, 3), "Accent" if k % 2 else "Glow")
    # the royal cloak and its fur collar
    def cpt(u, v):
        a = math.radians(-120 + 240 * u)
        r = 0.85 + 0.35 * v
        return (math.sin(a) * r, -0.05 - math.cos(a) * r * 0.75 - 0.08 * v, 0.95 - 1.85 * v + 0.06 * math.sin(u * 18))
    polys = [[cpt(i / 10, j / 6), cpt((i + 1) / 10, j / 6), cpt((i + 1) / 10, (j + 1) / 6), cpt(i / 10, (j + 1) / 6)] for i in range(10) for j in range(6)]
    P.part("Cloth", sheet(polys, 0.03), lambda c, n: "Trim" if c.z < -0.78 else "Accent", (0, 0, 0), 0, False)
    collar = torus(0.62, 0.13, 0.98, 22, 7)
    for v in collar.verts: v.co.y += 0.05
    P.obj("Collar", collar, "Glass", 1)
    # arms: a lantern staff in the right fist, a log club in the left
    for s in (1, -1):
        sh = Vector((s * 0.75, 0.15, 0.7))
        el = sh + Vector((s * 0.35, 0.25, -0.35)); wr = el + Vector((s * 0.1, 0.4, -0.05))
        P.obj("Arm", pipe([sh, el, wr], [0.26, 0.21, 0.18], 10), fur, 1)
        P.obj("Hand", ball(tuple(wr + Vector((0, 0.12, 0))), (0.17, 0.17, 0.17), 10, 5), "Belly", 1)
        for k in range(5):
            a = 2 * math.pi * k / 5
            b = sh + (el - sh) * 0.5 + Vector((math.sin(a) * 0.2, math.cos(a) * 0.15, 0))
            P.obj("ArmShag", cone(b, b + Vector((s * 0.12, -0.05, -0.18)), 0.07, 4), "Base", 0, False)
    hr = Vector((1.2, 1.07, 0.3)); hl = Vector((-1.2, 1.07, 0.3))
    P.obj("Staff", pipe([hr + Vector((0, 0, -0.9)), hr + Vector((0, 0, 1.05))], [0.05, 0.05], 8), lambda c, n: "Trim" if (c.z * 4) % 1.0 < 0.12 else "Base")
    top = hr + Vector((0, 0, 1.05))
    P.obj("StaffCap", lathe([(0.0, 0.0), (0.16, 0.06), (0.14, 0.1)], 10, "z", tuple(top)), "Trim")
    P.obj("StaffLamp", lathe([(0.13, 0.1), (0.15, 0.4), (0.0, 0.42)], 10, "z", tuple(top)), "Lamp")
    for k in range(4):
        a = 2 * math.pi * k / 4 + 0.4
        P.obj("Cage", pipe([top + Vector((math.sin(a) * 0.15, math.cos(a) * 0.15, 0.08)), top + Vector((math.sin(a) * 0.16, math.cos(a) * 0.16, 0.42))], [0.015, 0.015], 4), "Metal")
    P.obj("StaffTop", lathe([(0.17, 0.42), (0.1, 0.52), (0.0, 0.62)], 10, "z", tuple(top)), "Trim")
    P.obj("Club", pipe([hl + Vector((0, -0.1, -0.3)), hl + Vector((-0.1, 0.1, 0.4)), hl + Vector((-0.2, 0.25, 0.9))], [0.07, 0.16, 0.2], 10), lambda c, n: "Dark" if speckle(c, 3) < 0.2 else "Belly")
    for k in range(4):
        b = hl + Vector((-0.12 - 0.03 * k, 0.15, 0.5 + 0.12 * k))
        P.obj("Knot", ball(tuple(b + Vector((-0.15, 0.0, 0))), (0.06, 0.06, 0.06), 6, 3), "Base")
    # legs striding on enormous feet
    for s, k in ((1, 0), (-1, 1)):
        hip = Vector((s * 0.35, 0.0, -0.6))
        name = "Sway%d" % k
        P.part(name, pipe([hip, hip + Vector((s * 0.05, 0.1, -0.45)), hip + Vector((s * 0.08, 0.0, -0.85))], [0.28, 0.23, 0.2], 10), fur, tuple(hip), 1)
        foot = hip + Vector((s * 0.08, 0.2, -0.98))
        P.part(name, ball(tuple(foot), (0.24, 0.42, 0.13), 12, 6), "Belly", tuple(hip), 1)
        for t in range(5):
            x = (t - 2) * 0.09
            P.part(name, ball(tuple(foot + Vector((x, 0.42 - abs(t - 2) * 0.04, 0.0))), (0.055, 0.07, 0.05), 6, 3), "Belly", tuple(hip))
    # fireflies circling him
    for k in range(14):
        a = 2 * math.pi * k / 14
        P.part("SpinFireflies", ball((math.sin(a) * 1.7, math.cos(a) * 1.4, 0.5 + 0.4 * math.sin(a * 2)), (0.05, 0.05, 0.05), 6, 3), "Glow", (0, 0, 0.5))
    P.part("Muzzle", ball(tuple(top + Vector((0, 0, 0.25))), (0.08, 0.08, 0.08), 8, 4), "Lamp", tuple(top + Vector((0, 0, 0.25))))
    return P


# ----------------------------------------------------------------- the moon wolf king (2026-10-12, in place of the sasquatch king, the last boss)

# ================================================================= firefly (2026-10-13 remake)
def ff_slab(F, nu, nv, thick):
    """a curved plate: F(u, v) -> the top surface point, u along, v across (0..1); the underside thick below it, the rim closed."""
    bm = bmesh.new()
    T = [[bm.verts.new(F(i / nu, j / nv)) for j in range(nv + 1)] for i in range(nu + 1)]
    B = [[bm.verts.new(F(i / nu, j / nv) - Vector((0, 0, thick))) for j in range(nv + 1)] for i in range(nu + 1)]
    for i in range(nu):
        for j in range(nv):
            bm.faces.new((T[i][j], T[i + 1][j], T[i + 1][j + 1], T[i][j + 1]))
            bm.faces.new((B[i][j], B[i][j + 1], B[i + 1][j + 1], B[i + 1][j]))
    rim = [T[i][0] for i in range(nu + 1)] + [T[nu][j] for j in range(1, nv + 1)] + [T[i][nv] for i in range(nu - 1, -1, -1)] + [T[0][j] for j in range(nv - 1, 0, -1)]
    rimb = [B[i][0] for i in range(nu + 1)] + [B[nu][j] for j in range(1, nv + 1)] + [B[i][nv] for i in range(nu - 1, -1, -1)] + [B[0][j] for j in range(nv - 1, 0, -1)]
    for k in range(len(rim)):
        k2 = (k + 1) % len(rim)
        bm.faces.new((rim[k], rimb[k], rimb[k2], rim[k2]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm

def ff_pshape(bm, pc):
    """the pronotum's real outline: a rounded front, the hind edge nearly straight; tipped down a little at the front over the head."""
    m = Matrix.Rotation(math.radians(-9), 3, "X")
    for v in bm.verts:
        if v.co.y < pc.y: v.co.y = pc.y + (v.co.y - pc.y) * 0.5
        v.co = m @ (v.co - pc) + pc
    return bm

def ff_hinge(s, theta, yaw, pitch, at):
    """the elytron's opening: rolled up about the body's long axis, its tip swung out and lifted, all about the shoulder hinge."""
    at = Vector(at)
    m = Matrix.Rotation(math.radians(pitch), 3, "X") @ Matrix.Rotation(math.radians(s * yaw), 3, "Z") @ Matrix.Rotation(math.radians(-s * theta), 3, "Y")
    def f(bm):
        for v in bm.verts: v.co = m @ (v.co - at) + at
        return bm
    return f

def ff_leg(P, hip, knee, ankle, fdir, k=1.0):
    """a beetle's leg: coxa, a thick femur, a slimmer tibia with a spur, five tarsal segments, a pair of hooked claws."""
    hip, knee, ankle, fdir = Vector(hip), Vector(knee), Vector(ankle), Vector(fdir).normalized()
    P.obj("Coxa", ball(tuple(hip), (0.06 * k, 0.05 * k, 0.05 * k), 8, 4), "Base")
    P.obj("Femur", pipe([hip, hip.lerp(knee, 0.5) + Vector((0, 0, 0.015)), knee], [0.045 * k, 0.05 * k, 0.034 * k], 8), "Base")
    P.obj("Tibia", pipe([knee, knee.lerp(ankle, 0.5), ankle], [0.032 * k, 0.026 * k, 0.022 * k], 7), "Base")
    P.obj("Spur", cone(ankle, ankle + (ankle - knee).normalized() * 0.05 * k + Vector((0, 0, -0.02)), 0.01 * k, 4), "Dark")
    p = ankle
    for j in range(5):   # the tarsus: five beads, the fourth heart-shaped and wider, as on a firefly
        r = (0.017, 0.015, 0.014, 0.02, 0.011)[j] * k
        q = p + fdir * (0.04 * k)
        P.obj("Tarsus", xf(ball((0, 0, 0), (r, r, r * 1.6), 6, 3), fdir.to_track_quat("Z", "Y").to_matrix(), tuple(p.lerp(q, 0.5))), "Base")
        p = q
    side = fdir.cross(Vector((0, 0, 1))).normalized() if abs(fdir.z) < 0.95 else Vector((1, 0, 0))
    for c in (1, -1):
        P.obj("Claw", pipe(bez(p, p + fdir * 0.03 * k + side * c * 0.012 * k, p + fdir * 0.05 * k + Vector((0, 0, -0.03 * k)), p + fdir * 0.04 * k + Vector((0, 0, -0.06 * k)), 3),
                           [0.01 * k, 0.008 * k, 0.005 * k, 0.0], 4), "Trim")


def C_firefly():
    """The firefly queen (2026-10-13, remade: "same as the alien bosses - realistic details, scarier, keep the cartoon shape"): the same
    giant firefly with a shield over her head, big dark eyes, long antennae and a glowing lantern tail, now built like a real firefly, a
    lampyrid beetle. The flat pronotum spreads over her head like a hood: a pale-yellow rim, pink-red flanks and the black spot in the middle
    that a firefly carries there, and on its front edge a tiara of five gold prongs, each set with a warm glowing jewel. Under the hood a
    small black head: two great compound eyes, glossy and black, each lit by an amber glare and shaded by a frowning ridge of chitin; long
    serrated antennae of eleven segments, a saw-tooth on every one; a pair of curved gold-tipped mandibles crossed in front of her mouth with
    palps either side, and between them a glow where her shots leave. Six real beetle legs - coxa, femur, a slim tibia with its spur, five
    tarsal beads (the fourth heart-shaped) and a pair of hooked claws - the front pair reaching at the player, the others tucked. Her soft
    abdomen is seven overlapping rings, dark above and cream below, the last two the pale lantern that glows; a short dotted trail of light,
    evenly spaced and fading, hangs behind it.
    She flies like a real beetle: the hard wing cases (elytra), black edged in pale yellow and ribbed lengthwise, are lifted open from the
    shoulders and held out stiff and still in a V over her back; from under them the thin membranous hind wings unfold - smoky amber
    membrane on a dark costa and fanning veins - and beat as a fast blur (FlapL, FlapR, hinged at the shoulders)."""
    P = Boss("firefly", {"Base": ((0.06, 0.075, 0.045), 0.45), "Belly": ((0.80, 0.72, 0.48), 0.35), "Accent": ((0.86, 0.26, 0.22), 0.45),
                         "Trim": ((0.96, 0.82, 0.36), 0.5), "Glass": ((0.60, 0.52, 0.32), 0.9), "Dark": ((0.015, 0.018, 0.015), 0.88),
                         "Glow": ((0.78, 1.0, 0.25), 0.5), "Metal": ((0.88, 0.62, 0.16), 0.75), "Lamp": ((1.0, 0.70, 0.22), 0.8)})
    # ---- the pronotum: a flat hood over the head
    pc, prx, pry, prz = Vector((0, 0.98, 0.1)), 0.46, 0.38, 0.13
    def pron(c, n):
        q = math.hypot(c.x / prx, (c.y - pc.y) / pry)
        if n.z < -0.25: return "Base"
        if q > 0.8: return "Trim"
        if abs(c.x) < 0.1 and q < 0.62: return "Dark"
        return "Accent"
    P.obj("Pronotum", ff_pshape(ball(tuple(pc), (prx, pry, prz), 28, 10), pc), pron)
    P.obj("PronotumRim", ff_pshape(xf(torus(1.0, 0.022, 0.0, 48, 6), Matrix.Diagonal((prx * 0.99, pry * 0.99, 1.0)), (pc.x, pc.y, pc.z - 0.005)), pc), "Trim")
    def ptop(x, y):
        q = 1 - (x / prx) ** 2 - ((y - pc.y) / pry) ** 2
        p = Vector((x, y, pc.z + prz * math.sqrt(max(q, 0.0))))
        bm = bmesh.new(); bv = bm.verts.new(p); ff_pshape(bm, pc); p = bv.co.copy(); bm.free(); return p
    # the tiara: a gold band along the hood's front edge, five prongs, a jewel on each
    band = [ptop(0.3 * math.sin(a), pc.y + 0.25 * math.cos(a)) + Vector((0, 0, 0.012)) for a in [math.radians(-70 + 140 * i / 12) for i in range(13)]]
    P.obj("Tiara", pipe(band, [0.018] * 13, 6), "Metal")
    for i in range(5):
        a = math.radians(-56 + 28 * i)
        b = ptop(0.3 * math.sin(a), pc.y + 0.25 * math.cos(a)) + Vector((0, 0, 0.012))
        L = 0.12 if i == 2 else (0.09 if i in (1, 3) else 0.065)
        tip = b + Vector((math.sin(a) * 0.03, 0.03, L))
        P.obj("Prong", pipe([b, b.lerp(tip, 0.6), tip], [0.022, 0.014, 0.0], 6), "Metal")
        P.obj("Jewel", ball(tuple(b.lerp(tip, 0.55) + Vector((0, 0.012, 0))), (0.02, 0.016, 0.026) if i != 2 else (0.03, 0.022, 0.036), 8, 4), "Lamp")
    # ---- the head under the hood: compound eyes with a frowning ridge, saw-toothed antennae, mandibles and palps
    hc = Vector((0, 1.22, -0.05))
    P.obj("Head", ball(tuple(hc), (0.21, 0.19, 0.17), 14, 7), "Base")
    for s in (1, -1):
        e = hc + Vector((s * 0.16, 0.07, 0.01))
        P.obj("Eye", ball(tuple(e), (0.135, 0.125, 0.14), 16, 8), "Dark")
        P.obj("Glare", xf(ball((0, 0, 0), (0.05, 0.01, 0.012), 10, 4), Matrix.Rotation(math.radians(-s * 22), 3, "Y"), tuple(e + Vector((s * 0.03, 0.115, 0.02)))), "Lamp")
        P.obj("Ridge", pipe([e + Vector((-s * 0.11, 0.08, 0.06)), e + Vector((-s * 0.02, 0.1, 0.12)), e + Vector((s * 0.1, 0.07, 0.15))], [0.024, 0.03, 0.012], 6), "Base")
        # antenna: eleven segments, a saw-tooth on each, sweeping up and out
        b = hc + Vector((s * 0.07, 0.15, 0.06))
        ant = bez(b, b + Vector((s * 0.1, 0.2, 0.1)), b + Vector((s * 0.32, 0.26, 0.3)), b + Vector((s * 0.52, 0.12, 0.5)), 11)
        P.obj("Antenna", pipe(ant, [0.026 - 0.0012 * k for k in range(12)], 6), "Base")
        for k in range(1, 12):
            m = ant[k - 1].lerp(ant[k], 0.6); d = (ant[k] - ant[k - 1]).normalized()
            out = d.cross(Vector((0, 0, 1)) if abs(d.z) < 0.9 else Vector((1, 0, 0))).normalized() * (-s)
            if out.x * s < 0: out = -out
            P.obj("Tooth", cone(m, m + out * (0.055 - 0.003 * k) - d * 0.03, 0.017 - 0.0008 * k, 4), "Base", 0, False)
            P.obj("AntJoint", xf(torus(0.024 - 0.0012 * k, 0.006, 0.0, 10, 4), d.to_track_quat("Z", "Y").to_matrix(), tuple(ant[k])), "Dark")
        # mandible: a sickle curving in, crossing its twin, gold at the tip, two inner teeth
        m0 = hc + Vector((s * 0.08, 0.13, -0.08))
        mand = bez(m0, m0 + Vector((s * 0.12, 0.14, 0.0)), Vector((s * 0.1, 1.6, -0.14)), Vector((-s * 0.05, 1.64, -0.17)), 8)
        P.obj("Mandible", pipe(mand, [0.05, 0.05, 0.046, 0.04, 0.034, 0.026, 0.018, 0.009, 0.0], 8), lambda c, n: "Metal" if c.y > 1.55 else "Base")
        for t in (3, 5, 6):
            q = mand[t]; P.obj("MandTooth", cone(q, q + Vector((-s * 0.05, 0.01, -0.015)), 0.014, 4), "Metal")
        # a maxillary palp: three segments hanging below the jaw
        p0 = hc + Vector((s * 0.12, 0.08, -0.12))
        P.obj("Palp", pipe([p0, p0 + Vector((s * 0.05, 0.05, -0.08)), p0 + Vector((s * 0.06, 0.1, -0.15)), p0 + Vector((s * 0.05, 0.13, -0.2))], [0.018, 0.016, 0.014, 0.008], 6), "Base")
    # ---- thorax, scutellum, abdomen: seven soft rings, the last two the lantern
    P.obj("Thorax", ball((0, 0.6, 0.02), (0.27, 0.24, 0.19), 16, 8), "Base")
    P.obj("Scutellum", hull([(-0.06, 0.66, 0.2), (0.06, 0.66, 0.2), (0, 0.52, 0.2), (-0.05, 0.66, 0.16), (0.05, 0.66, 0.16), (0, 0.53, 0.16)]), "Dark", 0, False)
    for k in range(7):
        y = 0.4 - k * 0.23; rx = 0.34 - 0.01 * k - (0.05 if k == 6 else 0.0); rz = 0.17 - 0.01 * k
        lantern = k >= 5
        P.obj("Ring", ball((0, y, -0.02 - 0.025 * k), (rx, 0.2, rz), 22, 8),
              "Glow" if lantern else (lambda c, n: "Belly" if n.z < -0.35 else "Base"))
        if not lantern:   # the hind edge of each tergite: a narrow pale band where the rings overlap
            P.obj("RingEdge", xf(torus(1.0, 0.008, 0.0, 28, 4), Matrix.Rotation(math.radians(90), 3, "X") @ Matrix.Diagonal((rx * 0.97, rz * 0.97, 1.0)), (0, y - 0.11, -0.02 - 0.025 * k)), "Accent")
    # ---- the elytra: lifted open from the shoulders and held stiff in a V, black edged in pale yellow, ribbed
    y0, y1 = 0.6, -1.16
    def wid(u):
        w = 0.37 * math.sqrt(min(1.0, u / 0.1))
        if u > 0.55: w *= math.sqrt(max(0.0, 1 - ((u - 0.55) / 0.45) ** 2))
        return w
    for s in (1, -1):
        def F(u, v, s=s):
            u = 0.02 + 0.97 * u; w = wid(u)
            return Vector((s * (0.03 + v * w), y0 + (y1 - y0) * u, 0.15 - 0.13 * u + 0.1 * (1 - v * v) - 0.07 * v ** 4))
        op = ff_hinge(s, 42, 15, -4, (s * 0.03, y0, 0.25))
        P.obj("Shoulder", ball((s * 0.09, y0 - 0.02, 0.2), (0.09, 0.1, 0.07), 10, 5), "Base")
        P.obj("Elytron", op(ff_slab(F, 22, 8, 0.03)), lambda c, n: "Base", 0)
        # the pale margin and the suture edge, then three raised ribs (costae) along the case
        for v, r, slot in ((1.0, 0.02, "Trim"), (0.0, 0.016, "Trim"), (0.3, 0.011, "Dark"), (0.52, 0.011, "Dark"), (0.74, 0.011, "Dark")):
            us = [i / 24 for i in range(25)] if v in (0.0, 1.0) else [0.06 + 0.82 * i / 20 for i in range(21)]
            pts = [F(u, v) + Vector((0, 0, 0.004)) for u in us]
            P.obj("Costa" if slot == "Dark" else "Margin", op(pipe(pts, [r] * (len(pts) - 1) + [r * 0.5], 5)), slot)
    # ---- the hind wings: membrane unfolding from under the cases, beating as a blur
    for s in (1, -1):
        name = "FlapR" if s > 0 else "FlapL"
        hub = Vector((s * 0.2, 0.42, 0.12))
        def W(t, side):
            le = 0.1 - 0.16 * t * t
            c = 0.56 * math.sqrt(max(0.0, 1 - t ** 2.2)) * (0.45 + 0.55 * min(1.0, t / 0.18)) + 0.04
            return Vector((s * 1.55 * t, le if side else le - c, 0.0))
        ts = [i / 22 for i in range(23)]
        outline = [W(t, True) for t in ts] + [W(t, False) for t in reversed(ts)]
        rot = Matrix.Rotation(math.radians(s * 9), 3, "Y") @ Matrix.Rotation(math.radians(-s * 8), 3, "Z")   # a little dihedral, swept back
        def pl(p): return hub + rot @ p
        cen = Vector((s * 0.7, -0.12, 0.0))
        P.part(name, fan_sheet(pl(cen), [pl(p) for p in outline], 0.012), "Glass", tuple(hub), 0, False)
        costa = [pl(W(t, True) + Vector((0, -0.01, 0.008))) for t in ts[:20]]
        P.part(name, pipe(costa, [0.026 - 0.016 * i / 19 for i in range(20)], 6), "Base", tuple(hub))
        for j, (tt, frac) in enumerate(((0.95, 0.25), (0.8, 0.55), (0.62, 0.8), (0.42, 0.95))):   # veins fanning from the root to the hind edge
            a = W(0.04, True).lerp(W(0.04, False), 0.4); b = W(tt, True).lerp(W(tt, False), frac)
            vein = [pl(a.lerp(b, i / 8) + Vector((0, 0, 0.008))) for i in range(9)]
            P.part(name, pipe(vein, [0.012 - 0.008 * i / 8 for i in range(9)], 5), "Base", tuple(hub))
        P.part(name, ball(tuple(hub), (0.05, 0.06, 0.04), 8, 4), "Base", tuple(hub))
    # ---- legs: the front pair reaching at the player, the others tucked under
    for s in (1, -1):
        ff_leg(P, (s * 0.14, 0.86, -0.12), (s * 0.36, 1.0, -0.26), (s * 0.3, 1.26, -0.34), (s * 0.15, 1.0, -0.2), 1.05)
        ff_leg(P, (s * 0.17, 0.62, -0.12), (s * 0.44, 0.66, -0.3), (s * 0.4, 0.5, -0.5), (s * 0.3, -0.4, -0.85))
        ff_leg(P, (s * 0.17, 0.4, -0.12), (s * 0.46, 0.28, -0.26), (s * 0.4, 0.02, -0.46), (s * 0.3, -0.8, -0.5))
    # ---- the lantern's trail: dots of light, evenly spaced, fading
    for i, r in enumerate((0.075, 0.06, 0.046, 0.032)):
        P.part("Cloth", ball((0, -1.42 - 0.17 * i, -0.22 - 0.045 * i - 0.01 * i * i), (r, r, r), 10, 5), "Glow", (0, -1.5, -0.24))
    P.part("Muzzle", ball((0, 1.5, -0.16), (0.06, 0.04, 0.05), 8, 4), "Lamp", (0, 1.5, -0.16))
    return P



# ================================================================= owl (2026-10-13 remake)
# the camping world's great horned owl, remade (2026-10-13) - merged into camping_bosses.py as C_owl


def ow_plume(a, b, w, t=0.03, nseg=8):
    """one feather: a flat leaf from a to b, w wide, its broad face turned up (or toward the player when it stands upright)."""
    a, b = Vector(a), Vector(b); d = b - a; L = d.length; d = d.normalized()
    up = Vector((0, 0, 1)) if abs(d.z) < 0.9 else Vector((0, 1, 0))
    side = d.cross(up).normalized(); nrm = side.cross(d).normalized()
    return xf(ball((0, 0, 0), (w, L * 0.5, t), nseg, 4), Matrix((side, d, nrm)).transposed(), tuple((a + b) * 0.5))

def ow_barred(base, L, bands=4.0, tip="Belly", under="Belly"):
    """a feather's paint: dark bars across it evenly along its length, a pale soft tip (the owl's fringed edge), pale underneath."""
    base = Vector(base)
    def paint(c, n):
        u = (c - base).length / max(L, 1e-4)
        bar = (u * bands) % 1.0 < 0.26
        if u > 0.9: return tip
        if n.z < -0.45: return "Base" if bar else under          # underneath the bars show grey on pale
        return "Accent" if bar else "Base"
    return paint


def C_owl():
    """The great horned owl, lord of the night woods (2026-10-13, remade: "same as the alien bosses - realistic details, scarier, keep the
    cartoon shape"): the same big barrel of an owl coming at the player with the lantern, now built like a real great horned owl. Grey-brown
    above, dark chevrons down the back; the underparts pale buff crossed by fine grey-brown bars in even rows, a rusty upper
    breast, a white throat bib under the bill; the long soft feathers of the belly hanging over the legs, barred. The head: two tall plumicorns,
    each a tuft of five real feathers barred dark and tipped pale, rising from the ends of a pale V of brow feathers that meets over the bill in
    a frown; a rusty-orange facial disc in two lobes, rimmed in black; huge yellow-orange eyes that glow in the dark, black pupils, heavy
    lids slanting down to the bill in a glare; a black hooked bill half hidden in pale bristle feathers. Feathered legs thrust forward,
    four toes on each foot spread round the lantern's ring with long curved black talons.
    It flies the way an owl does - the SILENT GLIDE: broad rounded wings spread almost flat with a slight lift at the tips; on top two rows
    of coverts; along the trailing edge ten secondaries in a row, each barred and with a pale soft tip, the owl's fringed edge that makes no
    sound; at the hand eight primaries separated like fingers, fanned from forward to back, barred, their tips upturned; the tail fanned in
    ten barred feathers. The wings beat slowly and deeply about the shoulders (FlapL, FlapR). In its talons it carries the great lantern -
    an iron cap with a bail and vents, six posts round glass panes, a wax candle burning inside on an iron base - which swings below
    (SwayLantern). His shots leave from the candle's flame."""
    P = Boss("owl", {"Base": ((0.34, 0.26, 0.19), 0.35), "Belly": ((0.80, 0.70, 0.54), 0.3), "Accent": ((0.09, 0.06, 0.045), 0.35),
                     "Trim": ((0.96, 0.95, 0.91), 0.35), "Glass": ((0.72, 0.36, 0.13), 0.35), "Dark": ((0.02, 0.015, 0.015), 0.7),
                     "Glow": ((1.0, 0.74, 0.32), 0.5), "Metal": ((0.17, 0.16, 0.16), 0.65), "Lamp": ((1.0, 0.62, 0.06), 0.85)})

    # ---- the body: buff in front, crossed by fine grey-brown bars in even rows; a rusty upper breast; grey-brown above, barred in chevrons
    def bodypaint(c, n):
        if n.y > 0.15 and abs(c.x) < 0.64:
            w = c.z
            if c.z > 0.36: return "Base" if ((w + 3.0) * 12.0) % 1.0 < 0.2 else "Glass"   # the rusty upper breast under the bib
            return "Base" if ((w + 3.0) * 12.0) % 1.0 < 0.2 else "Belly"           # the fine bars of the underparts
        if n.y < -0.2 and ((c.z * 3.5 + abs(c.x) * 1.5 + 3.0) % 1.0) < 0.1: return "Accent"   # chevrons down the back
        return "Base"
    P.obj("Body", ball((0, 0.15, 0.0), (0.72, 0.64, 0.86), 32, 64), bodypaint, 1)
    for k in range(9):   # the hem: the long soft feathers of the belly over the legs
        x = (k - 4) * 0.12
        a = Vector((x, 0.6 - abs(x) * 0.35, -0.6)); b = a + Vector((x * 0.1, 0.05, -0.28))
        P.obj("HemFeather", ow_plume(a, b, 0.075, 0.025), ow_barred(a, 0.29, 2.5, "Trim", "Belly"), 0)

    # ---- the head: grey-brown crown finely streaked, a white bib under the bill
    hc = Vector((0, 0.45, 0.98))
    P.obj("Head", ball(tuple(hc), (0.6, 0.54, 0.5), 24, 14), "Base", 1)
    P.obj("Bib", ball((0, 0.78, 0.6), (0.27, 0.1, 0.11), 14, 6), "Trim", 1)
    # the facial disc: two rusty lobes round the eyes, rimmed in black
    for s in (1, -1):
        lc = Vector((s * 0.22, 0.83, 0.97))
        P.obj("Face", ball(tuple(lc), (0.3, 0.14, 0.33), 18, 9), lambda c, n: "Glass" if n.y > 0.35 else "Base", 1)
        rim = [lc + Vector((s * math.sin(a) * 0.31, -0.06 - 0.05 * math.sin(a), math.cos(a) * 0.35)) for a in [math.radians(-10 + 200 * i / 16) for i in range(17)]]
        P.obj("DiscRim", pipe(rim, [0.02] + [0.032] * 15 + [0.02], 6), "Dark")
        # the eye: glowing yellow-orange, a big black pupil, a heavy lid slanting down to the bill in a glare
        e = Vector((s * 0.21, 0.94, 0.99))
        P.obj("Socket", ball(tuple(e - Vector((0, 0.02, 0))), (0.19, 0.07, 0.19), 16, 8), "Dark")
        P.obj("Eye", ball(tuple(e), (0.165, 0.07, 0.165), 16, 8), "Lamp")
        P.obj("Pupil", ball(tuple(e + Vector((-s * 0.01, 0.045, -0.015))), (0.085, 0.035, 0.09), 12, 6), "Dark")
        P.obj("Shine", ball(tuple(e + Vector((s * 0.05, 0.075, 0.04))), (0.03, 0.012, 0.03), 6, 3), "Trim")
        lid = xf(ball((0, 0, 0), (0.2, 0.08, 0.075), 14, 6), Matrix.Rotation(math.radians(-s * 22), 3, "Y"), tuple(e + Vector((0, 0.03, 0.12))))
        P.obj("Lid", lid, "Base", 1)
        # the pale V of the brows, meeting over the bill: a frown that runs on up into the plumicorns
        P.obj("Brow", pipe(bez((s * 0.02, 1.03, 0.96), (s * 0.12, 1.03, 1.1), (s * 0.28, 0.98, 1.2), (s * 0.4, 0.86, 1.3), 6),
                           [0.02, 0.028, 0.032, 0.032, 0.03, 0.026, 0.02], 6), "Belly")
        # the plumicorn: a tuft of five feathers, barred dark, edged pale, rising up and out
        for k in range(5):
            b = Vector((s * (0.3 + 0.04 * k), 0.8 - 0.07 * k, 1.27 + 0.02 * k))
            tip = b + Vector((s * (0.12 + 0.05 * k), -0.06 - 0.05 * k, 0.6 - 0.07 * k))
            P.obj("Tuft", ow_plume(b, tip, 0.07 - 0.006 * k, 0.025), ow_barred(b, (tip - b).length, 3.0, "Belly", "Base"), 0)
    # the bill: black, hooked, half hidden in pale bristle feathers
    P.obj("Bill", pipe(bez((0, 1.0, 0.92), (0, 1.11, 0.9), (0, 1.13, 0.78), (0, 1.07, 0.7), 6), [0.07, 0.065, 0.055, 0.04, 0.025, 0.012, 0.0], 8), "Dark")
    for k in range(8):
        a = math.radians(-70 + 140 * k / 7)
        b = Vector((math.sin(a) * 0.07, 1.0, 0.94 + math.cos(a) * 0.04))
        P.obj("Bristle", ow_plume(b, b + Vector((math.sin(a) * 0.12, 0.07, -0.1 - 0.03 * abs(math.sin(a)))), 0.03, 0.012), "Belly", 0)

    # ---- the legs: feathered, thrust forward; four toes spread round the lantern's ring, long curved black talons
    ring = Vector((0, 0.95, -0.98))
    for s in (1, -1):
        P.obj("Thigh", ball((s * 0.24, 0.52, -0.62), (0.17, 0.2, 0.2), 12, 6), "Belly", 1)
        P.obj("Tarsus", pipe([Vector((s * 0.22, 0.6, -0.7)), Vector((s * 0.15, 0.82, -0.84)), Vector((s * 0.09, 0.93, -0.88))], [0.1, 0.085, 0.07], 10), "Belly")
        foot = Vector((s * 0.08, 0.95, -0.89))
        for k, (dx, dy, dz) in enumerate(((s * 0.08, 0.12, -0.02), (s * 0.02, 0.14, -0.03), (s * 0.1, -0.08, -0.03), (-s * 0.03, -0.12, -0.02))):
            d = Vector((dx, dy, dz)); tip = foot + d * 1.2
            P.obj("Toe", pipe([foot, foot + d * 0.6, tip], [0.035, 0.03, 0.026], 6), "Belly")
            curl = Vector((0, -0.09 if dy > 0 else 0.09, -0.08))   # the talon hooks down round the ring
            P.obj("Talon", pipe(bez(tip, tip + d.normalized() * 0.07, tip + d.normalized() * 0.08 + curl * 0.6, tip + d.normalized() * 0.03 + curl, 4),
                                [0.025, 0.021, 0.015, 0.008, 0.0], 6), "Dark")

    # ---- the wings: the silent glide - spread almost flat, broad and rounded, fingered primaries, a fringed trailing edge; they beat
    def wz(x): return 0.45 + 0.06 * (x - 0.5) + 0.05 * max(0.0, x - 2.0) ** 2
    for s in (1, -1):
        name = "FlapR" if s > 0 else "FlapL"
        hub = (s * 0.55, 0.12, 0.45)
        keys = [(0.5, 0.42, -0.42, 0.2, wz(0.5)), (1.0, 0.5, -0.5, 0.15, wz(1.0)), (1.6, 0.52, -0.46, 0.11, wz(1.6)),
                (2.15, 0.42, -0.3, 0.08, wz(2.15)), (2.4, 0.3, -0.1, 0.05, wz(2.4))]
        bm = sweep([(x, airfoil(le, te, th, z)) for (x, le, te, th, z) in fine(keys)], "x")
        if s < 0: bm = mirror_x(bm)
        P.part(name, bm, lambda c, n: "Belly" if n.z < -0.3 else "Base", hub, 0)
        # lesser coverts along the leading edge, greater coverts behind them
        for k in range(8):
            x = 0.7 + k * 0.2
            a = Vector((s * x, 0.38, wz(x) + 0.07)); b = a + Vector((s * 0.03, -0.26, -0.005))
            P.part(name, ow_plume(a, b, 0.09, 0.022), ow_barred(a, 0.26, 2.0, "Belly", "Belly"), hub, 0)
        for k in range(8):
            x = 0.72 + k * 0.2
            a = Vector((s * x, 0.12, wz(x) + 0.06)); b = a + Vector((s * 0.04, -0.4, -0.01))
            P.part(name, ow_plume(a, b, 0.11, 0.024), ow_barred(a, 0.4, 2.5), hub, 0)
        # ten secondaries in a row along the trailing edge, barred, with the pale soft tips that make the owl silent
        for k in range(10):
            x = 0.62 + k * 0.16
            a = Vector((s * x, -0.2, wz(x) + 0.03)); L = 0.72 - 0.015 * k
            b = a + Vector((s * 0.03, -L, -0.03))
            P.part(name, ow_plume(a, b, 0.1, 0.025), ow_barred(a, L, 4.0), hub, 0)
        # eight primaries at the hand, separated like fingers, fanned from forward to back, barred, tips upturned
        for k in range(8):
            ang_ = math.radians(30 - 13 * k)
            base = Vector((s * (2.2 + 0.03 * k), 0.36 - 0.08 * k, wz(2.2) + 0.02))
            L = 1.0 - 0.035 * abs(k - 2.5)
            tip = base + Vector((s * math.cos(ang_) * L, math.sin(ang_) * L, 0.16))
            P.part(name, ow_plume(base, tip, 0.085, 0.024), ow_barred(base, L, 4.5), hub, 0)

    # ---- the tail: ten feathers fanned out behind, barred, pale tipped
    for k in range(10):
        a = math.radians(-40 + k * 80 / 9)
        b = Vector((math.sin(a) * 0.12, -0.38, -0.32)); L = 0.8 - 0.06 * abs(k - 4.5) / 4.5
        tip = b + Vector((math.sin(a) * L, -math.cos(a) * L, -0.08))
        P.obj("TailFeather", ow_plume(b, tip, 0.1, 0.028), ow_barred(b, L, 4.0), 0)

    # ---- the great lantern, hung from the ring in his talons; it swings
    hub = tuple(ring)
    P.part("SwayLantern", xf(torus(0.1, 0.02, 0.0, 16, 5), Matrix.Rotation(math.radians(90), 3, "Y"), tuple(ring)), "Metal", hub, 0)
    lc = ring + Vector((0, 0, -0.12))
    bail = [lc + Vector((math.sin(t) * 0.17, 0, -0.12 - 0.12 * math.cos(t))) for t in [math.radians(-90 + 180 * i / 10) for i in range(11)]]
    P.part("SwayLantern", pipe(bail, [0.016] * 11, 5), "Metal", hub, 0)
    P.part("SwayLantern", lathe([(0.0, -0.02), (0.05, -0.04), (0.06, -0.1), (0.22, -0.24), (0.2, -0.27)], 12, "z", tuple(lc)), "Metal", hub, 0)
    for k in range(6):   # the vents in the cap
        a = 2 * math.pi * (k + 0.5) / 6
        P.part("SwayLantern", ball(tuple(lc + Vector((math.sin(a) * 0.14, math.cos(a) * 0.14, -0.18))), (0.03, 0.03, 0.02), 6, 3), "Dark", hub, 0)
    P.part("SwayLantern", lathe([(0.17, -0.27), (0.19, -0.68), (0.0, -0.69)], 6, "z", tuple(lc)), "Glow", hub, 0)
    for k in range(6):   # six iron posts round the panes
        a = 2 * math.pi * k / 6
        P.part("SwayLantern", pipe([lc + Vector((math.sin(a) * 0.19, math.cos(a) * 0.19, -0.27)), lc + Vector((math.sin(a) * 0.205, math.cos(a) * 0.205, -0.68))], [0.018, 0.018], 4), "Metal", hub, 0)
    P.part("SwayLantern", lathe([(0.0, -0.66), (0.06, -0.66), (0.06, -0.5), (0.0, -0.49)], 10, "z", tuple(lc)), "Belly", hub, 0)   # the candle
    P.part("SwayLantern", ball(tuple(lc + Vector((0, 0, -0.42))), (0.045, 0.045, 0.08), 8, 4), "Lamp", hub, 0)                        # its flame
    P.part("SwayLantern", lathe([(0.23, -0.68), (0.23, -0.75), (0.15, -0.79), (0.0, -0.8)], 12, "z", tuple(lc)), "Metal", hub, 0)
    P.part("SwayLantern", cone(tuple(lc + Vector((0, 0, -0.8))), tuple(lc + Vector((0, 0, -0.92))), 0.05, 6), "Metal", hub, 0)
    P.part("Muzzle", ball(tuple(lc + Vector((0, 0, -0.42))), (0.06, 0.06, 0.06), 8, 4), "Lamp", tuple(lc + Vector((0, 0, -0.42))))
    return P



# ================================================================= ember (2026-10-13 remake)
# the campfire king remade (2026-10-13): merged into camping_bosses.py as C_ember with its em_ helpers


def em_log(a, b, r, sector=360.0, roll=0.0, char=(0.0, 0.0), cap1="Trim", cap0="Trim", seg=20, step=0.04, cell=0.26):
    """a length of firewood from a to b, radius r: a round log (sector 360) or a split one (a sector of the round, its flat split faces
    pale wood), bark outside; between char[0] and char[1] (fractions of the length from a) it is burning - the bark gone to black char
    broken into blocks by glowing cracks, the alligator pattern of a real ember. Returns (bmesh, paint)."""
    a, b = Vector(a), Vector(b); d = b - a; L = d.length; d.normalize()
    side, up = frame(d)
    rs, rc = math.cos(roll), math.sin(roll); side, up = side * rs + up * rc, up * rs - side * rc
    split = sector < 359.0
    if split:
        h = math.radians(sector) * 0.5
        sec = [(0.0, None)] + [(r, -h + 2 * h * i / seg) for i in range(seg + 1)]
    else:
        sec = [(r, 2 * math.pi * i / seg) for i in range(seg)]
    n = max(2, int(L / step))
    bm = bmesh.new(); rings = []
    for j in range(n + 1):
        p = a + d * (L * j / n)
        rings.append([bm.verts.new(p if rr == 0 else p + (side * math.cos(t) + up * math.sin(t)) * rr) for rr, t in sec])
    m = len(sec)
    for r0, r1 in zip(rings, rings[1:]):
        for i in range(m):
            k = (i + 1) % m
            bm.faces.new((r0[i], r0[k], r1[k], r1[i]))
    bm.faces.new(list(reversed(rings[0]))); bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

    def paint(c, nrm):
        v = c - a; t = v.dot(d) / L
        if abs(nrm.dot(d)) > 0.8: return cap1 if t > 0.5 else cap0
        rad = v - d * v.dot(d)
        burning = char[0] <= t <= char[1]
        if split and rad.length > 1e-6 and abs(nrm.dot(rad.normalized())) < 0.5:
            return "Dark" if burning else "Trim"     # the split faces: pale wood, charred where it burns
        if not burning: return "Base"
        ang = math.atan2(rad.dot(up), rad.dot(side))
        u = t * L / cell; row = math.floor(u)
        w = (ang * r / cell + 0.5 * (row % 2)) % 1.0
        return "Glow" if (u - row) < 0.24 or w < 0.2 else "Dark"
    return bm, paint


def em_rings(c, nrm, r, n=3, slot="Dark"):
    """growth rings on a cut end: thin rings round its centre, just proud of the face."""
    c, nrm = Vector(c), Vector(nrm).normalized()
    rot = nrm.to_track_quat("Z", "Y").to_matrix()
    return em_join([xf(torus(r * (i + 1) / (n + 0.6), r * 0.035, 0.0, 20, 4), rot.to_4x4(), tuple(c + nrm * 0.006)) for i in range(n)])


def em_join(bms):
    """several bmeshes as one."""
    out = bmesh.new()
    for bm in bms:
        vm = {v: out.verts.new(v.co) for v in bm.verts}
        for f in bm.faces: out.faces.new([vm[v] for v in f.verts])
        bm.free()
    return out


def em_flame(base, up, h, w, curl=0.3, lean=None):
    """one tongue of fire from base: a broad tongue flattened like a real flame, swelling and then narrowing in an S to a curling point,
    orange going red at the tip, and inside it a fatter, shorter tongue that shows at the base, yellow-white low down - the layers of a
    real flame. Returns [(bmesh, paint)]."""
    base, up = Vector(base), Vector(up).normalized()
    lean = Vector(lean).normalized() if lean is not None else up.cross(Vector((0, 0, 1)) if abs(up.z) < 0.9 else Vector((1, 0, 0))).normalized()
    lean = (lean - up * lean.dot(up)).normalized()
    thin = up.cross(lean).normalized()
    def tongue(hh, prof):
        tip = base + up * hh + lean * curl * hh
        pts = bez(base, base + up * hh * 0.33 + lean * curl * hh * 0.5, base + up * hh * 0.66 - lean * curl * hh * 0.45, tip, len(prof) - 1)
        bm = pipe(pts, [w * k for k in prof], 10)
        for v in bm.verts:   # flattened across its lean, as a flame is
            o = v.co - base; v.co = base + o - thin * o.dot(thin) * 0.5
        return bm
    return [(tongue(h, [0.7, 1.0, 1.0, 0.85, 0.62, 0.4, 0.2, 0.0]), lambda c, n, base=base, up=up, h=h: "Glow" if (c - base).dot(up) > h * 0.68 else "Accent"),
            (tongue(h * 0.5, [1.12, 1.18, 1.0, 0.6, 0.0]), lambda c, n, base=base, up=up, h=h: "Accent" if (c - base).dot(up) > h * 0.2 else "Lamp")]


def em_stone(c, k):
    """a river stone: a rounded, flattened pebble, each one a little different (its size and squash from its place in the ring)."""
    rx = 0.2 + 0.035 * math.sin(k * 2.3); ry = 0.15 + 0.03 * math.cos(k * 1.7); rz = 0.12 + 0.025 * math.sin(k * 3.1 + 1)
    bm = ball((0, 0, 0), (rx, ry, rz), 12, 6)
    for v in bm.verts:   # a little lopsided, as a stone worn by water is
        v.co.z += 0.03 * v.co.x / max(rx, 1e-3) * math.sin(k)
    rot = Matrix.Rotation(math.atan2(c[0], c[1]), 3, "Z")
    for v in bm.verts: v.co = rot @ v.co + Vector(c)
    return bm


# ================================================================= the campfire king
def C_ember():
    """The CAMPFIRE KING (2026-10-13, remade: "same as the alien bosses - realistic details, scarier, keep the cartoon shape"): the same
    king made of the campfire - a ring of hearth stones, a teepee of burning logs, a great head of living fire with a crown and two burning
    log arms - now built like a real campfire. The logs are real firewood: split halves and round lengths with dark bark outside, the pale
    split faces of the wood, and where they stand in the fire the bark has burnt to black char broken into blocks by glowing cracks, the
    alligator pattern of a real ember; a bed of live coals lies between them. The hearth is a ring of eleven river stones, rounded and
    flattened by water, each a little different, blackened with soot on the side facing the fire. The flames are real flames: every tongue
    a white-yellow core low down, a fat orange tongue round it and a tall tongue curling to a point, orange going red at the tip; they lick
    up between the logs and rise from his head as his hair. His face is in the fire: two glowing coals for eyes with a black slit in each,
    sunk in charcoal sockets under a brow of two charred split logs meeting in a scowl, a wide mouth open on a bed of burning coals, ringed
    with jagged charred teeth glowing red at the tips, the corner ones longest like fangs. He wears a blacksmith's crown of iron - a riveted
    band, its rims red-hot, eight forged spikes glowing at the tips. His arms are burning logs bound with riveted iron shackles; his fists
    are their burning ends, the cut wood glowing white-hot inside its growth rings, each throwing a fan of flames.
    He flies on his own fire like a rocket: the hearth is an engine - the stones sit on a bowl of packed, charred earth that narrows to a
    red-hot mouth underneath - and out of it a roaring column of fire pours down: a white-hot core, four twisted ribbons of flame spiralling
    round it, three spirals of ember sparks spaced evenly along them and tongues of fire licking out, ending in a cap of dark smoke curling
    at the bottom. The column turns (SpinA: the core and the ribbons; SpinB: the sparks, the tongues and the smoke)."""
    P = Boss("ember", {"Base": ((0.15, 0.09, 0.05), 0.25), "Belly": ((0.30, 0.29, 0.28), 0.35), "Accent": ((1.0, 0.45, 0.04), 0.5),
                       "Trim": ((0.80, 0.62, 0.40), 0.3), "Glass": ((1.0, 0.97, 0.85), 0.6), "Dark": ((0.035, 0.025, 0.022), 0.35),
                       "Glow": ((0.95, 0.20, 0.02), 0.5), "Metal": ((0.20, 0.19, 0.20), 0.65), "Lamp": ((1.0, 0.80, 0.30), 0.8)})
    def put(name, items):
        for bm, paint in items: P.obj(name, bm, paint, 0)
    PIT = -0.92                       # the stones' middle
    # ---- the hearth: eleven river stones, sooty on the inside
    for k in range(11):
        a = 2 * math.pi * k / 11 + 0.15
        c = Vector((math.sin(a) * 0.8, math.cos(a) * 0.8, PIT))
        inward = Vector((-math.sin(a), -math.cos(a), 0))
        P.obj("Stone", em_stone(tuple(c), k), lambda q, n, c=c, inward=inward: "Dark" if n.dot(inward) > 0.25 and n.z > -0.4 else "Belly", 0)
    # the engine under them: a bowl of packed charred earth narrowing to a red-hot mouth
    P.obj("Pit", lathe([(0.0, PIT + 0.02), (0.74, PIT + 0.02), (0.76, PIT - 0.08), (0.66, PIT - 0.24), (0.5, PIT - 0.4), (0.42, PIT - 0.48), (0.4, PIT - 0.5), (0.0, PIT - 0.5)], 36, "z"),
          lambda c, n: "Glow" if c.z < PIT - 0.44 else "Dark")
    P.obj("Nozzle", xf(torus(0.42, 0.04, 0.0, 32, 6), None, (0, 0, PIT - 0.48)), "Lamp")
    # a bed of live coals
    for k in range(14):
        a = 2 * math.pi * k / 14; rr = 0.48 if k % 2 == 0 else 0.3
        c = (math.sin(a) * rr, math.cos(a) * rr, PIT + 0.04)
        P.obj("Coal", ball(c, (0.1, 0.08, 0.06), 8, 4), lambda q, n: "Lamp" if n.z > 0.5 else "Glow")
    # ---- the teepee: six logs, round and split by turns, black and cracked with fire low down
    for k in range(6):
        a = 2 * math.pi * k / 6 + math.pi / 6
        foot = Vector((math.sin(a) * 0.6, math.cos(a) * 0.6, PIT - 0.02)); top = Vector((math.sin(a + 0.5) * 0.12, math.cos(a + 0.5) * 0.12, 0.3))
        split = k % 2 == 1
        bm, paint = em_log(foot, top, 0.12 if not split else 0.15, 200.0 if split else 360.0, a + math.pi, (0.0, 0.48))
        P.obj("Log", bm, paint, 0, False)
    # flames licking up between the logs
    for k in range(6):
        a = 2 * math.pi * k / 6
        b = Vector((math.sin(a) * 0.38, math.cos(a) * 0.38, PIT + 0.02))
        put("Flame", em_flame(b, Vector((math.sin(a) * 0.25, math.cos(a) * 0.25, 1.0)), 0.75 + 0.12 * (k % 2), 0.12, 0.2,
                              Vector((math.cos(a), -math.sin(a), 0)) * (1 if k % 2 else -1)))
    # ---- the head of fire
    P.obj("Head", lathe([(0.0, 0.05), (0.36, 0.12), (0.58, 0.36), (0.63, 0.66), (0.57, 0.98), (0.5, 1.16), (0.44, 1.3), (0.3, 1.42), (0.0, 1.47)], 28, "z"),
          lambda c, n: "Glow" if c.z > 1.36 or n.y < -0.4 else "Accent", 1)
    # his hair: flames rising from the back and sides of his head, sweeping back, none over the face; three from the top inside the crown
    for deg, z, h in ((100, 0.62, 0.62), (130, 0.78, 0.78), (160, 0.9, 0.9), (180, 0.95, 0.95), (200, 0.9, 0.9), (230, 0.78, 0.78), (260, 0.62, 0.62)):
        a = math.radians(deg); o = Vector((math.sin(a), math.cos(a), 0))
        r = 0.6 if z < 0.8 else 0.55
        put("Hair", em_flame(o * r + Vector((0, 0, z)), o * 0.45 + Vector((0, -0.25, 1.0)), h, 0.15, 0.22, o))
    for k, (x, y) in enumerate(((-0.22, 0.05), (0.0, -0.08), (0.22, 0.05), (-0.1, 0.2), (0.1, 0.2))):   # the crown of his head: a blaze
        put("Crest", em_flame((x, y, 1.3), (x * 1.3, -0.15 + y * 0.3, 1.0), (0.85, 1.0, 0.85, 0.55, 0.55)[k], 0.16, 0.32, (1 if x >= 0 else -1, 0.3, 0)))
    # the face: coal eyes with a black slit, in charcoal sockets
    for s in (1, -1):
        P.obj("Socket", ball((s * 0.23, 0.5, 0.82), (0.19, 0.1, 0.15), 16, 8), "Dark")
        P.obj("Eye", ball((s * 0.22, 0.57, 0.8), (0.12, 0.06, 0.1), 14, 7), lambda c, n: "Lamp" if n.y > 0.4 else "Glow")
        P.obj("Pupil", hull([(s * 0.22, 0.635, 0.885), (s * 0.22, 0.635, 0.715), (s * 0.24, 0.63, 0.8), (s * 0.2, 0.63, 0.8),
                             (s * 0.22, 0.61, 0.8)]), "Dark", 0, False)
        # the brow: a charred split log over each eye, the two meeting low in the middle in a scowl
        bm, paint = em_log((s * 0.02, 0.6, 0.93), (s * 0.46, 0.48, 1.12), 0.07, 200.0, math.radians(-90 + 20 * s), (0.0, 1.0), "Glow", "Glow", 10, 0.035, 0.09)
        P.obj("Brow", bm, paint, 0, False)
    P.obj("Nose", hull([(0, 0.66, 0.74), (0.06, 0.6, 0.62), (-0.06, 0.6, 0.62), (0, 0.62, 0.6), (0.04, 0.58, 0.72), (-0.04, 0.58, 0.72)]), "Dark", 0, False)
    # the mouth: open wide on a bed of burning coals, jagged charred teeth glowing at the tips, the corner ones longest
    # the mouth: charred lips round a throat of fire, burning coals at the bottom of it
    P.obj("Throat", ball((0, 0.5, 0.42), (0.34, 0.1, 0.16), 18, 9), lambda c, n: "Lamp" if c.z < 0.4 else "Glow")
    lips = torus(1.0, 0.075, 0.0, 32, 8)
    for v in lips.verts: v.co = Vector((v.co.x * 0.36, 0.55 + v.co.z * 0.6, 0.42 + v.co.y * 0.17))
    P.obj("Lips", lips, "Dark")
    for k in range(5):
        x = (k - 2) * 0.11
        P.obj("MouthCoal", ball((x, 0.58, 0.3 + 0.015 * (k % 2)), (0.055, 0.03, 0.04), 8, 4), "Dark" if k % 2 else "Lamp")
    def teeth(n, z, dz, sign):
        for k in range(n):
            u = (k - (n - 1) / 2) / ((n - 1) / 2)
            x = u * 0.29; y = 0.6 - 0.1 * u * u; L = 0.1 + 0.08 * u * u
            base = Vector((x, y, z - 0.03 * u * u * sign)); tip = base + Vector((0.012 * u, 0.012, -L * sign))
            P.obj("Tooth", hull([base + Vector((0.045, 0, 0)), base - Vector((0.045, 0, 0)), base + Vector((0, 0.02, 0)), base - Vector((0, 0.02, 0)),
                                 base + (tip - base) * 0.5 + Vector((0.018, 0.005, 0)), tip]),
                  lambda c, n, base=base, L=L: "Glow" if abs(c.z - base.z) > L * 0.55 else "Dark", 0, False)
    teeth(7, 0.585, 0, 1); teeth(6, 0.255, 0, -1)
    # the blacksmith's crown: a riveted iron band, red-hot at its rims, eight forged spikes glowing at the tips
    P.obj("Crown", lathe([(0.5, 1.08), (0.53, 1.08), (0.53, 1.11), (0.5, 1.13), (0.48, 1.27), (0.5, 1.29), (0.5, 1.31), (0.46, 1.31), (0.46, 1.08)], 32, "z"),
          lambda c, n: "Glow" if c.z < 1.115 or c.z > 1.285 else "Metal", 0, False)
    for k in range(8):
        a = 2 * math.pi * k / 8
        o = Vector((math.sin(a), math.cos(a), 0))
        P.obj("Rivet", ball(tuple(o * 0.505 + Vector((0, 0, 1.19))), (0.025, 0.025, 0.025), 6, 3), "Metal")
        b = o * 0.48 + Vector((0, 0, 1.29)); L = 0.28 if k % 2 == 0 else 0.2
        P.obj("Spike", pipe([b, b + o * 0.03 + Vector((0, 0, L * 0.6)), b + o * 0.05 + Vector((0, 0, L))], [0.05, 0.03, 0.0], 4),
              lambda c, n, b=b, L=L: "Glow" if c.z > b.z + L * 0.55 else "Metal", 0, False)
    # ---- the arms: burning logs in riveted iron shackles; the fists are their burning ends throwing fans of flame
    for s in (1, -1):
        sh = Vector((s * 0.42, 0.0, 0.28)); name = "SwayR" if s > 0 else "SwayL"
        el = sh + Vector((s * 0.5, 0.12, -0.12)); fist = sh + Vector((s * 1.02, 0.42, 0.3))
        bm, paint = em_log(sh, el, 0.17, 360.0, 0.0, (0.0, 0.0), "Base", "Base", 14)
        P.part(name, bm, paint, tuple(sh), 0)
        bm, paint = em_log(el - (el - sh).normalized() * 0.08, fist, 0.16, 360.0, 0.0, (0.55, 1.0), "Lamp", "Base", 14)
        P.part(name, bm, paint, tuple(sh), 0)
        dfo = (fist - el).normalized()
        P.part(name, ball(tuple(el), (0.17, 0.17, 0.17), 12, 6), "Base", tuple(sh))
        P.part(name, em_rings(fist, dfo, 0.16), "Glow", tuple(sh))
        mid = el + (fist - el) * 0.35
        rot = dfo.to_track_quat("Z", "Y").to_matrix()
        band = torus(0.175, 0.03, 0.0, 20, 6)
        for v in band.verts: v.co = rot @ v.co + mid
        P.part(name, band, "Metal", tuple(sh))
        for j in range(6):
            a = 2 * math.pi * j / 6
            P.part(name, ball(tuple(mid + rot @ Vector((math.cos(a) * 0.2, math.sin(a) * 0.2, 0))), (0.022, 0.022, 0.022), 6, 3), "Metal", tuple(sh))
        side_, up_ = frame(dfo)
        for j in range(5):
            a = 2 * math.pi * j / 5
            b = fist + (side_ * math.cos(a) + up_ * math.sin(a)) * 0.08
            for bm, paint in em_flame(b, dfo * 0.6 + Vector((0, 0, 1.0)) + (side_ * math.cos(a) + up_ * math.sin(a)) * 0.3, 0.42 + 0.08 * (j % 2), 0.08, 0.25,
                                      side_ * math.cos(a) + up_ * math.sin(a)):
                P.part(name, bm, paint, tuple(sh), 0)
    # ---- the fire column he rides: a white-hot core, four twisted ribbons of flame, sparks and tongues in spirals, a cap of smoke
    HUB = Vector((0, 0, PIT - 0.5)); LEN = 1.15
    P.part("SpinA", lathe([(0.0, 0.0), (0.34, 0.0), (0.36, -0.2), (0.3, -0.5), (0.2, -0.8), (0.1, -1.0), (0.0, -LEN)], 24, "z", tuple(HUB)),
           lambda c, n: "Lamp" if c.z > HUB.z - 0.75 else "Accent", tuple(HUB), 0)
    for k in range(4):
        a0 = math.pi / 2 * k; path = []; N = 18
        for i in range(N + 1):
            u = i / N; a = a0 + u * 2 * math.pi * 1.1
            r = 0.44 - 0.22 * u
            path.append(HUB + Vector((math.sin(a) * r, math.cos(a) * r, -u * LEN * 0.98)))
        bm = ribbon(path, [0.07 + 0.08 * math.sin(math.pi * min(1.0, i / N * 1.3)) for i in range(N + 1)], [0.018] * (N + 1), [math.pi / 2] * (N + 1), 8)
        P.part("SpinA", bm, lambda c, n, k=k: "Glow" if c.z < HUB.z - LEN * 0.6 else ("Accent" if k % 2 else "Glow"), tuple(HUB), 0)
    for k in range(3):
        a0 = 2 * math.pi * k / 3 + 0.5
        for i in range(6):
            u = (i + 0.5) / 6; a = a0 + u * 2 * math.pi * 1.1
            r = 0.58 - 0.25 * u; c = HUB + Vector((math.sin(a) * r, math.cos(a) * r, -u * LEN * 0.95))
            e = 0.05 if i % 2 == 0 else 0.035
            P.part("SpinB", hull([c + Vector((e, 0, 0)), c - Vector((e, 0, 0)), c + Vector((0, e, 0)), c - Vector((0, e, 0)), c + Vector((0, 0, e * 1.8)), c - Vector((0, 0, e * 1.8))]),
                   "Lamp", tuple(HUB), 0, False)
    for k in range(6):   # tongues of fire licking out and down from the top of the column
        a = 2 * math.pi * k / 6 + 0.3
        b = HUB + Vector((math.sin(a) * 0.3, math.cos(a) * 0.3, -0.05))
        for bm, paint in em_flame(b, Vector((math.sin(a) * 0.8, math.cos(a) * 0.8, -1.0)), 0.45, 0.09, 0.3, Vector((math.cos(a), -math.sin(a), 0))):
            P.part("SpinB", bm, paint, tuple(HUB), 0)
    SB = HUB.z - LEN - 0.02
    for k in range(7):   # the smoke: puffs curling round in a ring, one under them
        a = 2 * math.pi * k / 7
        r = 0.2 + 0.05 * (k % 2)
        P.part("SpinB", ball((math.sin(a) * 0.3, math.cos(a) * 0.3, SB + 0.05 * math.sin(a * 2)), (r, r, r * 0.8), 12, 6), "Belly", tuple(HUB), 0)
    P.part("SpinB", ball((0, 0, SB - 0.14), (0.26, 0.26, 0.2), 12, 6), "Belly", tuple(HUB), 0)
    P.part("Muzzle", ball((0, 0.6, 0.42), (0.08, 0.04, 0.05), 8, 4), "Lamp", (0, 0.6, 0.42))
    return P



# ================================================================= moth (2026-10-13 remake)
# the luna moth empress, remade (2026-10-13) - merged into camping_bosses.py as C_moth with the mo_ helpers

MO_THICK = 0.035

def mo_wz(x, y, hind=False):
    """the height of the (still flat, before the V lift) wing at (x, y): rising a little to the tip; the hindwing just under the forewing,
    and its swallow tail curling up and over toward its end the way a luna's tails twist."""
    z = 0.15 + 0.08 * (x - 0.3) - (0.03 if hind else 0.0)
    if hind and y < -1.3: z += 0.32 * ((-1.3 - y) / 1.1) ** 2
    return z

def mo_P(x, y, hind=False, lift=0.0):
    return Vector((x, y, mo_wz(x, y, hind) + lift))

def mo_oval(c, rx, ry, rot, n=28):
    """an oval outline in the wing plane about c (x, y), turned by rot degrees."""
    a0 = math.radians(rot)
    return [(c[0] + math.cos(a0) * math.cos(t) * rx - math.sin(a0) * math.sin(t) * ry,
             c[1] + math.sin(a0) * math.cos(t) * rx + math.cos(a0) * math.sin(t) * ry) for t in [2 * math.pi * i / n for i in range(n)]]

def mo_disc(c, rx, ry, rot, hind, lift):
    """a thin flat oval lying on the wing's top face, lift above it (the rings of an eyespot are stacked discs, each a little higher)."""
    o = [mo_P(x, y, hind, MO_THICK * 0.5 + lift) for x, y in mo_oval(c, rx, ry, rot)]
    cen = mo_P(c[0], c[1], hind, MO_THICK * 0.5 + lift)
    return sheet([[tuple(cen), tuple(a), tuple(b)] for a, b in zip(o, o[1:] + o[:1])], 0.004)

def mo_vein(pts, hind, r=0.008):
    """a vein raised on the top of the wing along (x, y) points, thinning toward the margin."""
    p3 = [mo_P(x, y, hind, MO_THICK * 0.5 + 0.004) for x, y in pts]
    return pipe(p3, [r] * (len(p3) - 1) + [r * 0.4], 5)

def mo_dist(p, line):
    """the distance from (x, y) p to a polyline of (x, y) points."""
    best = 9.0
    for a, b in zip(line, line[1:]):
        a, b, q = Vector(a[:2]), Vector(b[:2]), Vector(p[:2])
        ab = b - a; t = max(0.0, min(1.0, (q - a).dot(ab) / max(1e-9, ab.dot(ab))))
        best = min(best, (a + ab * t - q).length)
    return best

def mo_fur(P, name, c, r, rows, per, length, slot="Belly", lat=(-60, 75), back=0.35):
    """even rows of fur tufts on an ellipsoid c, r: each a little cone leaning back (toward -y), like the dense pile of a moth."""
    c = Vector(c)
    for i in range(rows):
        la = math.radians(lat[0] + (lat[1] - lat[0]) * i / max(1, rows - 1))
        for k in range(per):
            a = 2 * math.pi * (k + 0.5 * (i % 2)) / per
            nrm = Vector((math.cos(la) * math.sin(a), math.cos(la) * math.cos(a), math.sin(la)))
            base = c + Vector((nrm.x * r[0], nrm.y * r[1], nrm.z * r[2])) * 0.92
            tip = base + (nrm + Vector((0, -back, 0))).normalized() * length
            P.obj(name, pipe([base, base + (tip - base) * 0.55, tip], [length * 0.5, length * 0.4, 0.0], 5), slot)



def C_moth():
    """The luna moth empress (2026-10-13, remade: "same as the alien bosses - realistic details, scarier, keep the cartoon shape"): the
    same giant moth as big as a tent, wings up in a V and pitched toward the player, now built like a real luna moth (Actias luna). Pale
    lime-green wings, the forewings' leading edge a thick maroon costa that runs on across the front of the thorax as a maroon collar,
    the outer margins edged in pale yellow; on each of the four wings the luna's eyespot - a clear window in the middle ringed by a thin
    dark line, yellow, maroon and black - the forewing spot tied to the costa by a short maroon bar, and the veins running out from the
    spots to the margin as on the real wing. The hindwings are drawn out into the long swallow tails, twisting up toward their pink-maroon
    tips. A thick body in dense white fur: tufts in even rows over the thorax and the head, a fur fringe on each ring of the abdomen;
    furry maroon legs, the forelegs reaching for the player with hooked claws. Big bipectinate antennae like golden ferns. No more blush
    and smile: her big dark compound eyes glint under heavy furred brows slanting down in a frown, two palps either side and the coiled
    proboscis under them (her shots leave from it); on her brow a silver tiara set with five moonstones.
    She flies by RIDING THE MOONBEAM: behind her and above hangs a small full moon (its seas on its face, a halo round it), and a shaft of
    moonlight comes down from it to her, rays widening and fading as they fall, motes of moon-dust evenly along every ray; she flutters
    down the beam with slow, big beats, fore and hind wing of each side beating together as one (FlapL / FlapR, hinged at the wing roots,
    the tails swinging with them), and silver scales shaken from her wings fall away under her in two trails."""
    P = Boss("moth", {"Base": ((0.55, 0.86, 0.46), 0.35), "Belly": ((0.95, 0.95, 0.90), 0.15), "Accent": ((0.30, 0.04, 0.12), 0.4),
                      "Trim": ((0.96, 0.80, 0.36), 0.5), "Glass": ((0.70, 0.90, 0.82), 0.95), "Dark": ((0.05, 0.03, 0.06), 0.75),
                      "Glow": ((0.62, 0.82, 1.0), 0.5), "Metal": ((0.74, 0.76, 0.86), 0.8), "Lamp": ((1.0, 0.96, 0.82), 0.8)})
    head_names = ("Head", "HeadFur", "Eye", "Glint", "Brow", "Antenna", "Barb", "Tiara", "Stone", "Prong", "Palp", "Proboscis")
    # ---- the body: a furry thorax with the maroon collar, a ringed abdomen with a fur fringe on every ring
    P.obj("Thorax", ball((0, 0.42, 0.06), (0.34, 0.38, 0.32), 16, 8), "Belly", 1)
    mo_fur(P, "ThoraxFur", (0, 0.42, 0.06), (0.34, 0.38, 0.32), 5, 14, 0.1, lat=(-35, 80))
    P.obj("Collar", xf(torus(0.3, 0.07, 0.0, 28, 8), Matrix.Rotation(math.radians(90), 3, "X") @ Matrix.Scale(1.0, 3), (0, 0.72, 0.08)), "Accent")
    for k in range(6):
        y = 0.02 - k * 0.24; r = 0.27 - k * 0.035; z = -0.02 - k * 0.03
        P.obj("Abdomen", ball((0, y, z), (r, 0.17, r * 0.9), 14, 6), "Belly", 1)
        for j in range(10):
            a = 2 * math.pi * (j + 0.5 * (k % 2)) / 10
            b = Vector((math.sin(a) * r * 0.95, y - 0.1, z + math.cos(a) * r * 0.85))
            d = Vector((math.sin(a) * 0.04, -0.08, math.cos(a) * 0.04))
            P.obj("AbdomenFur", pipe([b, b + d * 0.55, b + d], [0.045, 0.035, 0.0], 5), "Belly")
    # ---- the head: compound eyes under heavy furred brows, palps and the coiled proboscis
    hc = Vector((0, 0.88, 0.12))
    P.obj("Head", ball(tuple(hc), (0.25, 0.21, 0.23), 16, 8), "Belly", 1)
    mo_fur(P, "HeadFur", tuple(hc), (0.25, 0.21, 0.23), 3, 12, 0.08, lat=(20, 70), back=0.6)
    for s in (1, -1):
        e = hc + Vector((s * 0.16, 0.11, 0.0))
        P.obj("Eye", ball(tuple(e), (0.13, 0.11, 0.14), 16, 8), "Dark", 1)
        P.obj("Glint", ball(tuple(e + Vector((s * 0.0, 0.1, 0.05))), (0.03, 0.012, 0.03), 8, 4), "Lamp")
        P.obj("Glint", ball(tuple(e + Vector((s * 0.06, 0.08, -0.04))), (0.014, 0.008, 0.014), 6, 3), "Lamp")
        # the brow: a thick furred ridge, low over the inner corner, high at the outer one - a frown
        P.obj("Brow", pipe([hc + Vector((s * 0.03, 0.2, 0.08)), hc + Vector((s * 0.14, 0.21, 0.13)), hc + Vector((s * 0.27, 0.15, 0.2))],
                           [0.04, 0.05, 0.03], 8), "Belly")
        for j in range(4):
            q = hc + Vector((s * (0.06 + 0.06 * j), 0.2 - 0.01 * j, 0.1 + 0.03 * j))
            P.obj("Brow", cone(q, q + Vector((s * 0.05, -0.02, 0.07)), 0.03, 5), "Belly")
        P.obj("Palp", pipe([hc + Vector((s * 0.07, 0.17, -0.12)), hc + Vector((s * 0.09, 0.26, -0.2)), hc + Vector((s * 0.07, 0.3, -0.3))],
                           [0.045, 0.035, 0.0], 6), "Belly")
        # bipectinate antennae: a shaft sweeping up and out, two rows of barbs, longest in the middle
        ant = bez(tuple(hc + Vector((s * 0.08, 0.1, 0.2))), tuple(hc + Vector((s * 0.16, 0.26, 0.55))), tuple(hc + Vector((s * 0.36, 0.32, 0.86))),
                  tuple(hc + Vector((s * 0.6, 0.24, 1.04))), 12)
        P.obj("Antenna", pipe(ant, [0.028] * 11 + [0.01, 0.0], 6), "Trim")
        for k in range(2, 12):
            q = Vector(ant[k]); tan = (Vector(ant[k + 1]) - Vector(ant[k - 1])).normalized()
            side = tan.cross(Vector((0, 0, 1))).normalized()
            L = 0.19 * math.sin(math.pi * (k - 1) / 11) + 0.03
            for sd in (-1, 1):
                tip = q + side * sd * L + Vector((0, 0, 0.35 * L)) - tan * 0.04
                P.obj("Barb", pipe([q, tip], [0.011, 0.004], 4), "Trim", 0, False)
    # the proboscis coiled like a watch spring under the head
    pc = hc + Vector((0, 0.24, -0.22)); spiral = []
    for i in range(29):
        t = i / 28; a = 2 * math.pi * 1.75 * t; r = 0.085 * (1 - t) + 0.012
        spiral.append(pc + Vector((math.cos(a) * r, 0.02 * t, -math.sin(a) * r)))
    P.obj("Proboscis", pipe([hc + Vector((0, 0.17, -0.1))] + spiral, [0.018] * 25 + [0.014, 0.012, 0.01, 0.008, 0.0], 6), "Trim")
    # the empress's tiara: a silver band between the antennae, five moonstones evenly on it, the middle one biggest
    band = bez(tuple(hc + Vector((-0.2, 0.12, 0.17))), tuple(hc + Vector((-0.08, 0.22, 0.25))), tuple(hc + Vector((0.08, 0.22, 0.25))),
               tuple(hc + Vector((0.2, 0.12, 0.17))), 10)
    P.obj("Tiara", pipe(band, [0.02] * 11, 6), "Metal")
    for j, u in enumerate((0.1, 0.3, 0.5, 0.7, 0.9)):
        q = Vector(band[round(u * 10)]); k = 1.6 if j == 2 else 1.0
        P.obj("Stone", ball(tuple(q + Vector((0, 0.01, 0.035 * k))), (0.03 * k, 0.022 * k, 0.04 * k), 10, 5), "Glow")
        P.obj("Prong", cone(q + Vector((0, 0, 0.02)), q + Vector((0, -0.01, 0.06 + 0.05 * k)), 0.012, 4), "Metal")
    # ---- the legs: furry maroon, the forelegs reaching at the player with hooked claws, the others folded under
    for s in (1, -1):
        fore = [(s * 0.17, 0.66, -0.16), (s * 0.3, 0.86, -0.38), (s * 0.27, 1.12, -0.48), (s * 0.2, 1.32, -0.44)]
        P.obj("Leg", pipe(fore, [0.06, 0.05, 0.035, 0.03], 7), "Accent")
        for j in (-1, 1):
            f = Vector(fore[-1]); P.obj("Claw", pipe(bez(f, f + Vector((j * 0.03, 0.06, 0)), f + Vector((j * 0.05, 0.1, -0.04)), f + Vector((j * 0.04, 0.08, -0.1)), 4),
                                                 [0.016, 0.013, 0.01, 0.006, 0.0], 5), "Dark")
        for y, dy in ((0.42, 0.05), (0.18, -0.12)):
            pts = [(s * 0.24, y, -0.2), (s * 0.5, y + dy, -0.4), (s * 0.56, y + dy * 2, -0.66)]
            P.obj("Leg", pipe(pts, [0.05, 0.035, 0.012], 7), "Accent")
            P.obj("Claw", cone(Vector(pts[-1]), Vector(pts[-1]) + Vector((s * 0.02, 0.05, -0.08)), 0.012, 4), "Dark")
    # ---- the wings: lime green, the maroon costa, the yellow margins, an eyespot on each, veins from the spots to the margin
    fore_o = curve(((0.3, 0.62), (0.9, 0.95), (1.5, 1.12), (2.05, 1.1)),
                   ((2.05, 1.1), (2.12, 0.8), (1.95, 0.35), (1.6, 0.05)),
                   ((1.6, 0.05), (1.15, 0.0), (0.65, 0.18), (0.3, 0.32)))
    hind_o = curve(((0.3, 0.26), (0.9, 0.28), (1.45, 0.1), (1.5, -0.4)),
                   ((1.5, -0.4), (1.5, -0.9), (1.22, -1.5), (1.14, -2.15)),
                   ((1.14, -2.15), (1.06, -2.45), (0.86, -2.3), (0.92, -1.95)),
                   ((0.92, -1.95), (0.95, -1.25), (0.64, -0.62), (0.3, -0.05)))
    costa = fore_o[:9]; fore_margin = fore_o[8:]; hind_margin = hind_o[:9]
    FSPOT = ((1.12, 0.66), 0.17, 0.14, 20); HSPOT = ((0.95, -0.32), 0.18, 0.15, -30)
    for s in (1, -1):
        name = "FlapR" if s > 0 else "FlapL"
        hub = Vector((s * 0.28, 0.4, 0.15))
        lift = lambda bm, s=s, hub=hub: tilt(bm, "Y", -s * 14, hub)
        mx = lambda bm, s=s: bm if s > 0 else xf(bm, Matrix.Scale(-1.0, 3, (1, 0, 0)))
        def part(bm, paint, s=s, name=name, hub=hub, lift=lift, mx=mx, smooth=True):
            bm = mx(bm)
            if s < 0: bmesh.ops.reverse_faces(bm, faces=bm.faces)
            P.part(name, lift(bm), paint, tuple(hub), 0, smooth)
        unl = lambda c, s=s, hub=hub: Matrix.Rotation(math.radians(s * 14), 3, "Y") @ (c - hub) + hub
        def fpaint(c, n, unl=unl, s=s):
            c = unl(c); p = (abs(c.x), c.y)
            if mo_dist(p, costa) < 0.09: return "Accent"
            if mo_dist(p, fore_margin) < 0.05: return "Trim"
            return "Base"
        def hpaint(c, n, unl=unl, s=s):
            c = unl(c); p = (abs(c.x), c.y)
            if c.y < -2.05: return "Accent"
            if mo_dist(p, hind_margin) < 0.05: return "Trim"
            return "Base"
        f3 = [tuple(mo_P(x, y)) for x, y in fore_o]; h3 = [tuple(mo_P(x, y, True)) for x, y in hind_o]
        part(sheet(wing_polys(tuple(mo_P(1.2, 0.62)), f3, 9), MO_THICK), fpaint)
        part(sheet(wing_polys(tuple(mo_P(0.95, -0.35, True)), h3, 9), MO_THICK), hpaint)
        # the costa: a thick maroon vein along the leading edge
        part(pipe([tuple(mo_P(x, y, False, 0.004)) for x, y in costa], [0.05, 0.048, 0.045, 0.042, 0.04, 0.036, 0.032, 0.026, 0.0], 7), "Accent")
        # the eyespots: black, maroon, yellow, a thin dark line, the clear window
        for (c0, rx, ry, rot), hind in ((FSPOT, False), (HSPOT, True)):
            for i, (k, slot) in enumerate(((1.0, "Dark"), (0.86, "Accent"), (0.7, "Trim"), (0.5, "Dark"), (0.42, "Glass"))):
                part(mo_disc(c0, rx * k, ry * k, rot, hind, 0.004 * (i + 1)), slot, smooth=False)
        part(pipe([tuple(mo_P(1.1, 0.8, False, 0.01)), tuple(mo_P(1.04, 1.02, False, 0.01))], [0.03, 0.035], 6), "Accent")   # the bar from the costa
        # veins: into each spot from the root, and out from it to the margin
        fc, hcen = Vector(FSPOT[0]), Vector(HSPOT[0])
        for a, b in (((0.34, 0.5), (0.96, 0.6)), ((0.34, 0.38), (1.0, 0.52))):
            part(mo_vein([a, b], False), "Base")
        for k in (10, 12, 14, 16, 18, 20):
            o = Vector(fore_o[k]); d = (o - fc).normalized()
            st = fc + Vector((d.x * FSPOT[1], d.y * FSPOT[2])) * 1.05
            part(mo_vein([tuple(st), tuple(st + (o - st) * 0.55), tuple(o + (fc - o).normalized() * 0.03)], False), "Base")
        for a, b in (((0.34, 0.15), (0.8, -0.24)), ((0.34, 0.0), (0.84, -0.4))):
            part(mo_vein([a, b], True), "Base")
        for k in (2, 4, 6, 8):
            o = Vector(hind_o[k]); d = (o - hcen).normalized()
            st = hcen + Vector((d.x * HSPOT[1], d.y * HSPOT[2])) * 1.05
            part(mo_vein([tuple(st), tuple(o + (hcen - o).normalized() * 0.03)], True), "Base")
        part(mo_vein([(1.0, -0.5), (1.12, -1.0), (1.08, -1.6), (1.0, -2.15)], True, 0.011), "Base")   # down the tail
    HK = Matrix.Translation(hc + Vector((0, 0.08, 0.02))) @ Matrix.Scale(1.3, 4) @ Matrix.Translation(-hc)   # the head a size bigger, a little forward
    for ob in P.parts:
        if ob.name.split(".")[0] in head_names: ob.data.transform(HK)
    hc = HK @ hc; pc = HK @ pc
    rear(P, -30, -6, head_names, tuple(hc))
    Rb = Matrix.Rotation(math.radians(-30), 4, "X"); hr = Rb @ hc
    Rh = Matrix.Translation(hr) @ Matrix.Rotation(math.radians(24), 4, "X") @ Matrix.Translation(-hr)
    mz = Rh @ Rb @ (pc + Vector((0, 0.06, 0)))   # the proboscis, where it went with the head
    P.part("Muzzle", ball(tuple(mz), (0.06, 0.03, 0.06), 8, 4), "Lamp", tuple(mz))
    # ---- (after the pitch) the moon behind her and its beam she rides down
    mc = Vector((0, -1.55, 0.98)); mr = 0.3
    P.obj("Moon", ball(tuple(mc), (mr, mr, mr), 20, 10), "Lamp", 1)
    for (u, v, k) in ((-0.35, 0.3, 0.32), (0.1, 0.35, 0.26), (0.3, 0.05, 0.22), (-0.15, -0.2, 0.2), (0.2, -0.38, 0.12)):   # the seas
        q = mc + Vector((u * mr, 0.0, v * mr)); q.y = mc.y + math.sqrt(max(0.0, mr * mr - (u * mr) ** 2 - (v * mr) ** 2)) * 0.97
        P.obj("Sea", ball(tuple(q), (k * mr, 0.03, k * mr * 0.8), 10, 4), "Metal")
    P.obj("Halo", xf(torus(mr * 1.35, 0.018, 0.0, 40, 6), Matrix.Rotation(math.radians(90), 3, "X"), tuple(mc)), "Glow")
    to = Vector((0, 0.35, -0.1)); axis = (to - mc).normalized()
    u = axis.cross(Vector((1, 0, 0))).normalized(); w = axis.cross(u)
    L = (to - mc).length
    for k in range(8):
        a = 2 * math.pi * (k + 0.5) / 8
        off = u * math.cos(a) + w * math.sin(a)
        p0 = mc + off * mr * 0.9; p1 = to + off * 1.25
        pts = [p0 + (p1 - p0) * t for t in (0.0, 0.25, 0.48, 0.62)]
        P.obj("Beam", pipe(pts, [0.012, 0.02, 0.016, 0.008], 5), "Glow")
        for t in (0.3, 0.55, 0.72, 0.86):
            q = p0 + (p1 - p0) * t + off * 0.06
            P.obj("Mote", ball(tuple(q), (0.025, 0.025, 0.025), 6, 3), "Lamp")
    # ---- silver scales shaken from her wings, falling away under her in two trails
    for s in (1, -1):
        for j in range(6):
            c = Vector((s * (1.05 - 0.08 * j), -0.2 - 0.2 * j, -0.6 - 0.1 * j)); k = 0.07 * (1 - 0.1 * j)
            rot = Matrix.Rotation(math.radians(35 * j * s), 3, "Z") @ Matrix.Rotation(math.radians(50 + 20 * j), 3, "X")
            q = [c + rot @ Vector(p) * k for p in ((0, 1, 0), (0.55, 0, 0), (0, -1, 0), (-0.55, 0, 0))]
            P.part("Cloth", sheet([[tuple(q[0]), tuple(q[1]), tuple(q[2]), tuple(q[3])]], 0.006), "Metal", (0, -0.5, -1.0), 0, False)
    return P



# ================================================================= wolf (2026-10-13 remake)
# Sky Squad, the camping moon wolf king remade (2026-10-13). Merged later into Tools/blender/camping_bosses.py as C_wolf.


def wf_ring_at(rings, y):
    """the loft section (y, a, b, cx, cz) at y, interpolated."""
    for r0, r1 in zip(rings, rings[1:]):
        if y <= r1[0]:
            f = max(0.0, (y - r0[0]) / (r1[0] - r0[0])); return [a + (b - a) * f for a, b in zip(r0, r1)]
    return list(rings[-1])

def wf_top(rings, x, y, k=1.0):
    """a point on the upper surface of a loft at (x, y), lifted k times its height."""
    r = wf_ring_at(rings, y); u = min(0.98, abs(x) / max(r[1], 1e-4))
    return Vector((x, y, r[4] + r[2] * math.sqrt(1 - u * u) * k))

def wf_frame(bm, o, X, Y, Z):
    """the mesh built in its own axes (x across, y along, z out) put at o along the world axes X, Y, Z."""
    return xf(bm, Matrix((X, Y, Z)).transposed(), tuple(o))

def wf_lock(base, d, L, w, nrm, bend=0.0):
    """a lock of fur: a tapered clump from base along d, w thick, flattened across nrm, its tip curling along nrm by bend."""
    base = Vector(base); d = Vector(d).normalized(); nrm = Vector(nrm).normalized()
    pts = bez(base, base + d * L * 0.35, base + d * L * 0.7 + nrm * bend * 0.5, base + d * L + nrm * bend, 4)
    bm = pipe(pts, [w, w * 0.9, w * 0.65, w * 0.32, 0.0], 6)
    for v in bm.verts: v.co -= nrm * ((v.co - base).dot(nrm) - bend * 0.0) * 0.45
    return bm

def wf_star(c, r, nrm=(0, 1, 0), depth=0.6):
    """a four-pointed sparkle star facing nrm: long points up and down, shorter ones to the sides, a raised middle."""
    c = Vector(c); n = Vector(nrm).normalized()
    a = Vector((0, 0, 1)) - n * n.z; a = a.normalized() if a.length > 1e-4 else Vector((1, 0, 0))
    b = n.cross(a).normalized()
    pts = [c + a * r * 1.6, c - a * r * 1.6, c + b * r, c - b * r]
    pts += [c + (a + b) * r * 0.22, c + (a - b) * r * 0.22, c - (a + b) * r * 0.22, c - (a - b) * r * 0.22]
    pts += [c + n * r * depth, c - n * r * depth]
    return hull([tuple(p) for p in pts])

# ---- the crescent moon he rides: a horned crescent lying on its back in the YZ plane, its midline an arc about MC
MC = Vector((0, -0.1, 1.2)); MR = 1.6; TH0, TH1 = -72.0, 70.0

def wf_taper(th):
    u = th / (TH1 if th > 0 else -TH0)
    return max(0.0, 1 - u * u)

def wf_moon_pt(th, phi=90.0, out=0.0):
    """a point on the moon at arc angle th (0 = the bottom, + toward the front horn) and phi round its section (90 = the inner, upper
    face he stands on, -90 = the outer limb underneath, 0 = the right side), pushed out along the surface by out."""
    t = math.radians(th); f = wf_taper(th)
    p = MC + Vector((0, MR * math.sin(t), -MR * math.cos(t)))
    up = Vector((0, -math.sin(t), math.cos(t))); side = Vector((1, 0, 0))
    rx, rz = 0.92 * f ** 0.5, 0.36 * f ** 0.6
    ca, sa = math.cos(math.radians(phi)), math.sin(math.radians(phi))
    u = math.copysign(abs(ca) ** (1 / 1.3), ca) * rx; v = math.copysign(abs(sa) ** (1 / 1.3), sa) * rz
    nrm = (side * ca * max(rz, 1e-3) + up * sa * max(rx, 1e-3)).normalized()
    return p + side * u + up * v + nrm * out, nrm


def C_wolf():
    """The last boss, the MOON WOLF KING (2026-10-13, remade: "same as the alien bosses - realistic details, scarier, keep the cartoon
    shape"): the same huge silver-blue wolf snarling at the player, now built like a real grey wolf - a deep narrow chest and high withers,
    a lean waist, long legs and big paws with dark claws; the grey agouti coat of a timber wolf, a darker saddle down the back and on the
    tail, pale cheeks, throat, chest and belly. A thick ruff stands round his neck and shoulders in even layered rows of locks, longest
    mid-neck, pale under the throat, and his hackles are up along the spine. The head is a wolf's - a broad skull, a long blunt muzzle,
    the pale mask round the mouth and the pale spots over the eyes, a big black nose, flared white cheek ruffs - but snarling: the jaw
    dropped, the black lips drawn back over long ivory canines, incisors and a row of shearing teeth, three wrinkles creasing the top
    of the snout, a cold glow deep in the throat (his shots leave from it). Amber eyes with round pupils and a dark rim under heavy
    frowning brows; the ears pinned back flat. A king's silver collar round his neck set with moonstones and a crescent pendant at the
    throat. His long bushy brush is held straight out behind, the dark tip of a wolf's tail, and sways as he goes. He flies by RIDING THE
    CRESCENT MOON: a great horned crescent lies on its back under him like a sled or the prow of a ship, and he stands braced on it -
    forepaws planted at the foot of the front horn, hind legs braced in the curve - leaning forward at the player. It is a real moon:
    a pale grey surface with the darker maria spread over its sides, craters with raised rims and deep floors, its outer limb glowing
    silver all along the underside; from the back horn a trail of stardust streams away behind it, with stars evenly along it, the
    biggest nearest the horn."""
    P = Boss("wolf", {"Base": ((0.40, 0.43, 0.52), 0.35), "Belly": ((0.88, 0.90, 0.95), 0.3), "Accent": ((0.13, 0.14, 0.20), 0.35),
                      "Trim": ((0.60, 0.64, 0.74), 0.85), "Glass": ((0.95, 0.93, 0.85), 0.6), "Dark": ((0.035, 0.035, 0.05), 0.45),
                      "Glow": ((0.55, 0.85, 1.0), 0.5), "Metal": ((0.88, 0.88, 0.84), 0.25), "Lamp": ((1.0, 0.60, 0.10), 0.8)})
    V_ = Vector

    # ================================================================ the crescent moon
    N = 84; ths = [TH0 + (TH1 - TH0) * i / (N - 1) for i in range(N)]
    PTS = [MC + V_((0, MR * math.sin(math.radians(t)), -MR * math.cos(math.radians(t)))) for t in ths]
    FR = [(V_((0, math.cos(math.radians(t)), math.sin(math.radians(t)))), V_((1, 0, 0)), V_((0, -math.sin(math.radians(t)), math.cos(math.radians(t))))) for t in ths]
    RX = [0.92 * wf_taper(t) ** 0.5 for t in ths]; RZ = [0.36 * wf_taper(t) ** 0.6 for t in ths]
    RX[0] = RX[-1] = 0.0
    MARIA = [(1, -40, 15, 24, 50), (1, 5, -10, 18, 40), (1, 40, 25, 14, 35), (-1, -25, 10, 22, 45), (-1, 25, -20, 16, 40), (-1, 50, 30, 10, 30)]
    def moonpaint(c, n_):
        d = c - MC; th = math.degrees(math.atan2(d.y, -d.z)); rho = MR - math.hypot(d.y, d.z)
        f = wf_taper(th); rx, rz = 0.92 * f ** 0.5 + 1e-3, 0.36 * f ** 0.6 + 1e-3
        phi = math.degrees(math.atan2(rho / rz, abs(c.x) / rx)); sgn = 1 if c.x >= 0 else -1
        for (s, t0, p0, rt, rp) in MARIA:
            if s != sgn: continue
            wob = 1.0 + 0.18 * math.sin(th * 0.21 + p0) + 0.12 * math.sin(phi * 0.17 + t0)
            if ((th - t0) / rt) ** 2 + ((phi - p0) / rp) ** 2 < wob: return "Trim"
        return "Metal"
    P.obj("Moon", body_loft(PTS, RX, RZ, FR, seg=44, sq=1.3, flat=1.0), moonpaint, 0)
    # the lit limb: a silver glow along both outer edges, horn to horn
    for ph in (-28, 208):
        limb = [wf_moon_pt(t, ph, 0.01)[0] for t in ths[1:-1]]
        P.obj("Limb", pipe(limb, [0.03 * wf_taper(t) ** 0.3 for t in ths[1:-1]], 6), "Glow")
    # craters: a raised rim round a sunken floor, scattered over both sides and the top as on the real moon (big ones few, small many)
    CR = [(-55, 20, 0.09), (-38, -15, 0.13), (-20, 35, 0.07), (-8, -30, 0.1), (12, 10, 0.12), (28, -35, 0.08), (44, 15, 0.1), (58, -5, 0.06),
          (-48, -40, 0.06), (20, 40, 0.06)]
    for sgn in (1, -1):
        for k, (th, ph, r) in enumerate(CR):
            th2 = th + (6 if sgn < 0 else 0) * (1 if k % 2 else -1); ph2 = ph * (1 if sgn > 0 else -0.8)
            c, n_ = wf_moon_pt(th2, ph2 if sgn > 0 else 180 - ph2)
            a = n_.cross(V_((0, 0, 1)) if abs(n_.z) < 0.9 else V_((0, 1, 0))).normalized(); b = n_.cross(a).normalized()
            rim = torus(r, r * 0.24, 0.0, 16, 5); xf(rim, Matrix((a, b, n_)).transposed(), tuple(c))
            P.obj("Crater", rim, "Metal")
            P.obj("CraterFloor", oriented_ball(c - n_ * 0.012, (r * 0.85, r * 0.85, 0.02), a, b, n_, 12, 4), "Trim")
    for th, ph, r in ((-45, 80, 0.07), (-5, 70, 0.05), (55, 75, 0.06), (30, 100, 0.05)):   # a few on the top face, clear of his paws
        c, n_ = wf_moon_pt(th, ph)
        a = n_.cross(V_((1, 0, 0))).normalized(); b = n_.cross(a).normalized()
        rim = torus(r, r * 0.24, 0.0, 14, 5); xf(rim, Matrix((a, b, n_)).transposed(), tuple(c)); P.obj("Crater", rim, "Metal")
        P.obj("CraterFloor", oriented_ball(c - n_ * 0.012, (r * 0.85, r * 0.85, 0.02), a, b, n_, 10, 4), "Trim")
    # the stardust trail streaming from the back horn: a fading ribbon of dust, stars evenly along it (no outline: Cloth)
    horn = PTS[1]
    trail = bez(horn, horn + V_((0, -0.35, -0.08)), horn + V_((0, -0.7, -0.3)), horn + V_((0, -1.05, -0.5)), 12)
    P.part("Cloth", pipe(trail, [0.06 * (1 - i / 12) ** 0.8 for i in range(13)], 8), "Glow", (0, 0, 0), 0, False)
    for k, u in enumerate((0.12, 0.34, 0.56, 0.78, 0.98)):
        i = min(12, int(round(u * 12))); c = trail[i] + V_((0.16 if k % 2 else -0.16, 0, 0.1 if k % 2 else -0.04))
        P.part("Cloth", wf_star(c, 0.12 - 0.017 * k, (0.25, 1, 0.3)), "Glow", (0, 0, 0), 0, False)
        if k < 4:
            j = min(12, i + 1); d = trail[j] + V_((-0.08 if k % 2 else 0.08, 0, 0.05))
            P.part("Cloth", ball(tuple(d), (0.025, 0.025, 0.025), 6, 3), "Glow", (0, 0, 0), 0, False)

    # ================================================================ the wolf
    neck = bez((0, 1.04, 1.42), (0, 0.95, 1.27), (0, 0.82, 1.17), (0, 0.62, 1.1), 6)
    torso = bez((0, 0.62, 1.1), (0, 0.15, 1.08), (0, -0.4, 1.06), (0, -0.9, 1.13), 12)[1:]
    SP = neck + torso; NN = len(neck)
    SRX, SRZ = [], []
    for i in range(len(neck)):
        u = i / (len(neck) - 1)
        SRX.append(lerp_keys(u, [(0, 0.24), (0.5, 0.28), (1, 0.3)])); SRZ.append(lerp_keys(u, [(0, 0.28), (0.5, 0.34), (1, 0.39)]))
    for i in range(len(torso)):
        u = (i + 1) / len(torso)
        SRX.append(lerp_keys(u, [(0, 0.28), (0.15, 0.29), (0.5, 0.2), (0.78, 0.25), (0.93, 0.2), (1, 0.13)]))
        SRZ.append(lerp_keys(u, [(0, 0.37), (0.15, 0.38), (0.5, 0.25), (0.78, 0.29), (0.93, 0.22), (1, 0.13)]))
    SF = spine_frames(SP); ns = len(SP)
    def locate(c):
        return min(range(ns), key=lambda k: (SP[k] - c).length_squared)
    def coat(c, n_):
        i = locate(c); t, side, up = SF[i]; d = c - SP[i]
        u = d.dot(side) / SRX[i]; v = d.dot(up) / SRZ[i]
        if i < NN + 3 and v < -0.15: return "Belly"                     # the pale throat and chest
        if v < -0.5 and abs(u) < 0.75: return "Belly"                    # the pale belly
        if v > 0.5 and NN - 2 < i < ns - 1: return "Accent"              # the dark saddle
        return "Base"
    P.obj("Body", body_loft(SP, SRX, SRZ, SF, seg=24, sq=1.1, flat=0.9), coat, 0)
    # the ruff: even layered rows of locks round the neck and shoulders, combed back, longest mid-neck, pale under the throat
    for row in range(NN + 2):
        i = min(ns - 1, row); p = SP[i]; t, side, up = SF[i]
        L = 0.13 + 0.1 * math.sin(math.pi * min(1.0, (row + 0.5) / (NN + 2)))
        for k in range(18):
            a = 2 * math.pi * (k + 0.5 * (row % 2)) / 18; ca, sa = math.cos(a), math.sin(a)
            if row <= 1 and sa > 0.3: continue   # none standing up behind the skull
            q = p + side * ca * SRX[i] * 0.92 + up * sa * SRZ[i] * 0.92
            out = (side * ca + up * sa).normalized()
            d = out * 0.4 + t * 1.0 + (-up * 0.7 if sa < -0.3 else V_())
            nrm = out.cross(d.normalized()).cross(d.normalized()).normalized() * -1
            slot = "Belly" if sa < -0.35 else ("Accent" if sa > 0.75 else "Base")
            P.obj("Ruff", wf_lock(q, d, L * (1.1 if sa < -0.35 else 1.0), 0.06, nrm, 0.04), slot, 0, False)
    # hackles: dark locks standing along the spine from the withers to the hips, graded
    for i in range(NN + 2, ns - 3):
        p = SP[i]; t, side, up = SF[i]
        h = 0.07 + 0.08 * max(0.0, 1 - (i - NN - 2) / 9)
        q = p + up * SRZ[i] * 0.9
        P.obj("Hackle", wf_lock(q, up * 0.8 + t * 1.0, h, 0.05, side), "Accent", 0, False)

    # ---- the head (built pointing +Y from the back of the skull, then tipped down a little and scaled)
    HB = V_((0, 0.98, 1.44)); HR = Matrix.Rotation(math.radians(-9), 3, "X") @ Matrix.Scale(1.42, 3); HI = HR.inverted()
    def H(bm): return xf(bm, HR, tuple(HB))
    def hp(fn): return lambda c, n_: fn(HI @ (c - HB), (HI @ n_).normalized())
    def hpt(p): return HB + HR @ V_(p)
    UP = [(-0.12, 0.12, 0.11, 0, 0.03), (-0.03, 0.23, 0.2, 0, 0.05), (0.08, 0.27, 0.22, 0, 0.06), (0.2, 0.265, 0.19, 0, 0.045),
          (0.3, 0.2, 0.14, 0, 0.005), (0.4, 0.15, 0.105, 0, -0.03), (0.52, 0.132, 0.09, 0, -0.045), (0.63, 0.118, 0.08, 0, -0.05),
          (0.71, 0.1, 0.068, 0, -0.05), (0.775, 0.055, 0.045, 0, -0.045)]
    def skull(c, n_):
        if c.y > 0.3 and n_.z < 0.3: return "Belly"           # the pale mask round the mouth
        if c.y < 0.3 and n_.z < -0.3: return "Belly"          # under the jaw
        if c.y > 0.32 and n_.z > 0.6: return "Base"           # the top of the snout
        if c.y < 0.25 and n_.z > 0.5: return "Accent"         # the dark crown
        return "Base"
    P.obj("Skull", H(loft(UP, 24, sq=1.15)), hp(skull), 0)
    P.obj("Nose", H(ball((0, 0.78, -0.03), (0.06, 0.045, 0.045), 12, 6)), "Dark")
    for s in (1, -1):
        P.obj("Nostril", H(ball((s * 0.025, 0.818, -0.04), (0.016, 0.01, 0.01), 6, 3)), "Accent")
    LO = [(0.1, 0.17, 0.065, 0, -0.08), (0.3, 0.12, 0.05, 0, -0.1), (0.5, 0.095, 0.04, 0, -0.1), (0.64, 0.07, 0.032, 0, -0.095), (0.7, 0.04, 0.02, 0, -0.09)]
    J = V_((0, 0.12, -0.07)); JR = Matrix.Rotation(math.radians(-26), 3, "X")
    def Jw(bm): return H(xf(bm, JR, tuple(J - JR @ J)))
    P.obj("Jaw", Jw(loft(LO, 18, sq=1.1)), hp(lambda c, n_: "Dark" if n_.z > 0.55 else "Belly"), 0)
    P.obj("Mouth", H(ball((0, 0.42, -0.12), (0.095, 0.3, 0.06), 12, 6)), "Dark")
    P.obj("Throat", H(ball((0, 0.22, -0.1), (0.07, 0.06, 0.05), 10, 5)), "Glow")
    P.obj("Tongue", Jw(pipe([(0, 0.2, -0.065), (0, 0.42, -0.07), (0, 0.62, -0.065)], [0.055, 0.05, 0.025], 8)), "Accent")
    for s in (1, -1):
        up_lip = [V_((s * wf_ring_at(UP, y)[1] * 0.92, y, wf_ring_at(UP, y)[4] - wf_ring_at(UP, y)[2] * 0.75)) for y in (0.32, 0.42, 0.52, 0.62, 0.7, 0.76)]
        P.obj("Lip", H(pipe(up_lip, [0.018] * 5 + [0.011], 5)), "Dark")
        lo_lip = [V_((s * wf_ring_at(LO, y)[1] * 0.9, y, wf_ring_at(LO, y)[4] + wf_ring_at(LO, y)[2] * 0.8)) for y in (0.16, 0.3, 0.45, 0.58, 0.68)]
        P.obj("Lip", Jw(pipe(lo_lip, [0.015] * 4 + [0.009], 5)), "Dark")
        # teeth: the carnassial and premolars behind, a long canine, incisors at the tip
        for y, L in ((0.36, 0.045), (0.44, 0.06), (0.52, 0.045), (0.63, 0.15), (0.71, 0.04), (0.745, 0.035)):
            r = wf_ring_at(UP, y); top = V_((s * r[1] * (0.8 if y < 0.7 else 0.55), y, r[4] - r[2] * 0.8))
            P.obj("Tooth", H(cone(top, top + V_((-s * 0.01, 0.014, -L)), 0.014 + L * 0.13, 6)), "Glass", 0, False)
        for y, L in ((0.3, 0.04), (0.42, 0.045), (0.57, 0.12), (0.655, 0.035)):
            r = wf_ring_at(LO, y); bot = V_((s * r[1] * 0.75, y, r[4] + r[2] * 0.8))
            P.obj("Tooth", Jw(cone(bot, bot + V_((-s * 0.01, 0.012, L)), 0.013 + L * 0.13, 6)), "Glass", 0, False)
        # the eye: amber, a round pupil (a wolf's), a glint, a dark rim; a heavy frowning brow over it and the pale spot above
        ec = V_((s * 0.15, 0.3, 0.08)); dv = V_((s * 0.5, 0.86, 0.1)).normalized()
        ex = dv.cross(V_((0, 0, 1))).normalized(); ez = ex.cross(dv).normalized()
        if ez.z < 0: ez = -ez
        P.obj("EyeRim", H(oriented_ball(ec - dv * 0.004, (0.08, 0.03, 0.048), ex, dv, ez, 12, 6)), "Dark")
        P.obj("Eye", H(oriented_ball(ec + dv * 0.006, (0.066, 0.03, 0.038), ex, dv, ez, 12, 6)), "Lamp")
        P.obj("Pupil", H(oriented_ball(ec + dv * 0.03, (0.022, 0.012, 0.022), ex, dv, ez, 8, 4)), "Dark")
        P.obj("Glint", H(ball(tuple(ec + dv * 0.034 + ez * 0.017 - ex * s * 0.02), (0.01, 0.01, 0.01), 6, 3)), "Belly")
        P.obj("Brow", H(pipe(bez((s * 0.04, 0.35, 0.095), (s * 0.1, 0.34, 0.13), (s * 0.17, 0.31, 0.15), (s * 0.23, 0.26, 0.15), 6),
                             [0.02, 0.03, 0.034, 0.034, 0.03, 0.022, 0.01], 7)), "Accent")
        P.obj("BrowSpot", H(oriented_ball(wf_top(UP, s * 0.12, 0.22, 1.0), (0.04, 0.03, 0.012), V_((1, 0, 0)), V_((0, 1, 0)), V_((0, 0, 1)), 8, 4)), "Belly")
        # the ears pinned back flat: short, rounded at the tip, dark on the back, pale fur inside
        eb = wf_top(UP, s * 0.14, 0.02, 0.85); ED = V_((s * 0.5, -0.8, 0.35)).normalized()
        EZ = (V_((0, 0, 1)) - ED * ED.z).normalized(); EX = ED.cross(EZ).normalized()
        EAR = [(0.0, 0.11, 0.04, 0, 0.0), (0.1, 0.105, 0.036, 0, -0.01), (0.2, 0.08, 0.03, 0, -0.012), (0.28, 0.045, 0.02, 0, -0.008), (0.33, 0.01, 0.01, 0, 0.0)]
        ob = loft(EAR, 14, sq=1.0); wf_frame(ob, eb, EX, ED, EZ)
        P.obj("Ear", H(ob), hp(lambda c, n_, EZ=EZ: "Accent" if n_.dot(EZ) > 0.2 else "Base"), 0)
        for a in (-0.5, 0.0, 0.5):
            b = eb + ED * 0.03 + EX * a * 0.05 - EZ * 0.03
            P.obj("EarFur", H(wf_lock(b, ED + EX * a * 0.4, 0.15, 0.025, EZ)), "Belly", 0, False)
        # the cheek ruffs: pale fur flaring out and back below the ears
        for k in range(7):
            z = 0.04 - 0.04 * k; L = 0.13 + 0.07 * math.sin(math.pi * (k + 0.5) / 7)
            b = V_((s * 0.19, 0.13 + 0.012 * k, z))
            P.obj("CheekRuff", H(wf_lock(b, (s * 0.8, -0.8, -0.1 - 0.15 * k), L, 0.045, (0, 0.3, 1), -0.02)), "Belly", 0, False)
        pad = V_((s * 0.09, 0.62, -0.05))
        P.obj("WhiskerPad", H(ball(tuple(pad), (0.04, 0.08, 0.035), 8, 4)), "Belly")
        for k in range(3):
            d = V_((s * 1.0, -0.25 - 0.12 * k, 0.1 - 0.1 * k)).normalized()
            w = bez(pad, pad + d * 0.1, pad + d * 0.2 + V_((0, 0, -0.02)), pad + d * 0.28 + V_((0, 0, -0.05)), 4)
            P.part("Cloth", H(pipe([V_(p) for p in w], [0.006, 0.005, 0.004, 0.003, 0.0], 4)), "Dark", (0, 0, 0), 0, False)
    for k, y in enumerate((0.44, 0.49, 0.54)):   # the snarl wrinkles across the top of the snout
        r = wf_ring_at(UP, y)
        pts = [wf_top(UP, x * r[1], y - 0.02 * abs(x), 1.03) for x in (-0.75, -0.4, 0.0, 0.4, 0.75)]
        P.obj("Wrinkle", H(pipe(pts, [0.0, 0.009, 0.011, 0.009, 0.0], 4)), "Accent")

    # ---- the silver collar: moonstones evenly round it and a crescent pendant at the throat
    ci = 2; cp = SP[ci]; t, side, up = SF[ci]
    def ring_pt(a, grow=0.06):
        return cp + side * math.cos(a) * (SRX[ci] + grow) + up * math.sin(a) * (SRZ[ci] + grow)
    P.obj("Collar", pipe([ring_pt(2 * math.pi * k / 40) for k in range(41)], [0.05] * 41, 8, cap=False), "Trim")
    for k in range(8):
        a = 2 * math.pi * (k + 0.5) / 8
        if abs(math.sin(a) + 1) < 0.2: continue
        c = ring_pt(a, 0.1); o = (side * math.cos(a) + up * math.sin(a)).normalized()
        P.obj("Moonstone", oriented_ball(c, (0.035, 0.035, 0.02), side.cross(o).normalized() if abs(side.cross(o).length) > 0.1 else t, t, o, 8, 4), "Glow")
    bt = ring_pt(-math.pi / 2, 0.08)
    P.obj("Bail", xf(torus(0.035, 0.012, 0.0, 10, 4), Matrix.Rotation(math.radians(90), 3, "Y"), tuple(bt - up * 0.03)), "Trim")
    pc = bt - up * 0.12 + t * -0.02
    arc = [pc + up * math.cos(math.radians(a)) * 0.12 + (-t) * math.sin(math.radians(a)) * 0.085 for a in range(-150, 151, 15)]
    P.obj("Pendant", pipe(arc, [0.04 * max(0.0, math.cos(math.radians(a) * 0.55)) ** 0.7 for a in range(-150, 151, 15)], 8), "Trim")
    P.obj("PendantGem", ball(tuple(pc + (-t) * 0.09), (0.025, 0.025, 0.025), 8, 4), "Glow")

    # ---- legs: braced on the moon - forepaws planted at the foot of the front horn, hind legs braced in the curve
    def paw(ft, d, size=1.0):
        d = V_(d).normalized(); sd = d.cross(V_((0, 0, 1))).normalized(); upp = sd.cross(d).normalized()
        P.obj("Paw", oriented_ball(ft, (0.09 * size, 0.1 * size, 0.055 * size), sd, d, upp, 10, 5), "Base")
        for k in range(4):
            a = (k - 1.5) * 0.3
            dd = (Matrix.Rotation(a, 3, upp) @ d).normalized()
            tp = ft + dd * 0.1 * size - upp * 0.012
            P.obj("Toe", ball(tuple(tp), (0.038 * size, 0.045 * size, 0.032 * size), 8, 4), "Base")
            c0 = tp + dd * 0.03 * size
            P.obj("Claw", pipe(bez(c0, c0 + dd * 0.04, c0 + dd * 0.07 - upp * 0.02, c0 + dd * 0.075 - upp * 0.065, 4),
                               [0.016 * size, 0.014 * size, 0.01 * size, 0.005, 0.0], 5), "Dark")
    def leg(joints, radii, pale_from, pawdir, size=1.0):
        for i in range(len(joints) - 1):
            a, b = joints[i], joints[i + 1]
            P.obj("Leg", pipe([a, (a + b) * 0.5, b], [radii[i], (radii[i] + radii[i + 1]) * 0.5, radii[i + 1]], 10),
                  "Belly" if i >= pale_from else "Base", 0)
            if 0 < i: P.obj("Joint", ball(tuple(a), (radii[i] * 1.05,) * 3, 8, 4), "Belly" if i >= pale_from else "Base")
        paw(joints[-1], pawdir, size)
    fp, _ = wf_moon_pt(48, 90); hp_, _ = wf_moon_pt(-28, 90)
    for s in (1, -1):
        P.obj("Shoulder", oriented_ball(V_((s * 0.19, 0.55, 0.98)), (0.13, 0.22, 0.27), V_((1, 0, 0)), V_((0, 0.94, -0.34)), V_((0, 0.34, 0.94)), 12, 6), "Base")
        leg([V_((s * 0.2, 0.58, 0.95)), V_((s * 0.23, 0.5, 0.68)), V_((s * 0.22, fp.y - 0.12, fp.z + 0.2)), V_((s * 0.22, fp.y - 0.04, fp.z + 0.07))],
            [0.14, 0.095, 0.07, 0.068], 2, (0, 1, -0.15))
        P.obj("Thigh", oriented_ball(V_((s * 0.21, -0.62, 0.97)), (0.15, 0.3, 0.27), V_((1, 0, 0)), V_((0, 0.8, -0.6)).normalized(), V_((0, 0.6, 0.8)).normalized(), 12, 6), "Base")
        leg([V_((s * 0.22, -0.62, 0.95)), V_((s * 0.24, -0.4, 0.66)), V_((s * 0.22, -0.82, 0.42)), V_((s * 0.21, hp_.y + 0.02, hp_.z + 0.07))],
            [0.16, 0.1, 0.065, 0.062], 2, (0, 1, -0.1), 0.95)

    # ---- the brush: held straight out behind, bushy, dark at the tip; it sways
    tb = SP[-1]
    tail = bez(tb, tb + V_((0, -0.4, 0.04)), tb + V_((0.05, -0.85, -0.02)), tb + V_((0.12, -1.25, -0.1)), 12)
    tr = [lerp_keys(j / 12, [(0, 0.11), (0.2, 0.17), (0.55, 0.21), (0.8, 0.19), (0.93, 0.12), (1, 0.03)]) for j in range(13)]
    P.part("SwayTail", pipe(tail, tr, 14), lambda c, n_: "Accent" if (c - tb).length > 1.05 or n_.z > 0.55 else ("Belly" if n_.z < -0.5 else "Base"), tuple(tb), 0)
    for j in range(2, 12):
        t_ = (tail[min(12, j + 1)] - tail[j - 1]).normalized(); sd = t_.cross(V_((0, 0, 1))).normalized(); uv = sd.cross(t_).normalized()
        for k in range(8):
            a = 2 * math.pi * (k + 0.5 * (j % 2)) / 8; o = sd * math.cos(a) + uv * math.sin(a)
            q = tail[j] + o * tr[j] * 0.85
            slot = "Dark" if j >= 10 else ("Accent" if math.sin(a) > 0.4 else ("Belly" if math.sin(a) < -0.5 else "Base"))
            P.part("SwayTail", wf_lock(q, o * 0.5 + t_ * 1.0, 0.16 + 0.06 * math.sin(math.pi * j / 12), 0.05, o.cross(t_)), slot, tuple(tb), 0, False)

    mz = hpt((0, 0.6, -0.1))
    P.part("Muzzle", ball(tuple(mz), (0.06, 0.03, 0.04), 8, 4), "Lamp", tuple(mz))
    return P


BOSSES = [("firefly", C_firefly), ("owl", C_owl), ("ember", C_ember), ("moth", C_moth), ("wolf", C_wolf)]

if __name__ == "__main__":
    os.makedirs(AB.OUT, exist_ok=True)
    for bid, fn in BOSSES:
        if ONLY and bid not in ONLY: continue
        fn().finish()
    print("DONE")
