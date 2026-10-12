# Sky Squad, the desert pyramids' five bosses (2026-10-10: "give me for desert pyramids and japanese island"): the magic carpet, the anubis
# guardian, the winged sphinx, the sun barque and the sky pyramid. Built from code like the other worlds' bosses (alien_bosses.py lends its
# Boss class and shapes).
# Run: blender -b -P Tools/blender/desert_bosses.py -- <out dir> [export] [ids,comma,separated]
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
LAPIS = ((0.10, 0.25, 0.70), 0.6)

def fine(keys, step=0.08):
    secs = []
    for a0, a1 in zip(keys, keys[1:]):
        n = max(2, int((a1[0] - a0[0]) / step))
        secs += [tuple(u + (v - u) * i / n for u, v in zip(a0, a1)) for i in range(n)]
    secs.append(keys[-1])
    return secs

def grid_surface(fn, nu, nv, thick=0.04):
    """a thick sheet from fn(u, v) -> point, u and v in [0, 1]."""
    bm = bmesh.new()
    top = [[bm.verts.new(fn(i / nu, j / nv) + Vector((0, 0, thick * 0.5))) for j in range(nv + 1)] for i in range(nu + 1)]
    bot = [[bm.verts.new(fn(i / nu, j / nv) - Vector((0, 0, thick * 0.5))) for j in range(nv + 1)] for i in range(nu + 1)]
    for i in range(nu):
        for j in range(nv):
            bm.faces.new((top[i][j], top[i + 1][j], top[i + 1][j + 1], top[i][j + 1]))
            bm.faces.new((bot[i][j], bot[i][j + 1], bot[i + 1][j + 1], bot[i + 1][j]))
    for i in range(nu):
        bm.faces.new((top[i][0], bot[i][0], bot[i + 1][0], top[i + 1][0])); bm.faces.new((top[i][nv], top[i + 1][nv], bot[i + 1][nv], bot[i][nv]))
    for j in range(nv):
        bm.faces.new((top[0][j], top[0][j + 1], bot[0][j + 1], bot[0][j])); bm.faces.new((top[nu][j], bot[nu][j], bot[nu][j + 1], top[nu][j + 1]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


# ================================================================= 1. the magic carpet
def D_carpet():
    """Sinbad's carpet (2026-10-12: "I want Sinbad on the carpet, a person on the carpet"): a flying carpet rippling on the wind - crimson
    with a gold border and blue medallions, gold tassels - and standing on it Sinbad the sailor: a crimson turban with a gold band, a jewel
    and a plume, a bold face with a black beard and curling moustache, an open lapis vest on a bare chest, a crimson sash, baggy emerald
    trousers and curled golden slippers, gold armbands, a curved scimitar raised high in his right hand and his left hand thrust at the
    player; at his feet the genie lamp trailing blue smoke, behind him an open chest of gold and jewels."""
    P = Boss("carpet", {"Base": ((0.72, 0.10, 0.12), 0.35), "Belly": ((0.86, 0.60, 0.42), 0.3), "Accent": LAPIS, "Trim": GOLD,
                        "Glass": ((0.10, 0.62, 0.48), 0.75), "Dark": ((0.08, 0.05, 0.04), 0.4), "Glow": ((0.45, 0.80, 1.0), 0.5),
                        "Metal": ((0.82, 0.85, 0.92), 0.9), "Lamp": ((1.0, 0.92, 0.70), 0.8)})
    W, L = 1.4, 2.0
    def carpet(u, v):
        x = (u - 0.5) * 2 * W; y = (v - 0.5) * 2 * L
        return Vector((x, y, 0.12 * math.sin(v * 2 * math.pi * 1.5) + 0.18 * (abs(x) / W) ** 2))
    def pattern(c, n):
        if n.z < -0.5: return "Dark"
        x, y = abs(c.x), abs(c.y)
        if x > W * 0.86 or y > L * 0.9: return "Trim"
        if x > W * 0.78 or y > L * 0.82: return "Accent"
        if (x / 0.45) ** 2 + ((c.y % 1.3) - 0.65) ** 2 / 0.12 < 0.6: return "Accent"
        if ((x * 4 + c.y * 4) % 1.0 < 0.08): return "Trim"
        return "Base"
    P.obj("Carpet", grid_surface(carpet, 18, 24, 0.05), pattern, 0, False)
    for k in range(9):   # tassels
        for sy in (1, -1):
            c = carpet(k / 8 * 0.9 + 0.05, 1.0 if sy > 0 else 0.0)
            P.obj("Tassel", cone(c + Vector((0, sy * 0.02, 0)), c + Vector((0, sy * 0.22, -0.12)), 0.04, 5), "Trim", 0, False)
    # ---- Sinbad, standing on the carpet facing the player (built at his first size, then made 1.25 times as big about his feet)
    n0 = len(P.parts)
    y0, G = 0.05, -0.1
    skin = "Belly"
    # legs: baggy trousers gathered at the ankle, curled golden slippers, a wide stance
    for s, fy in ((1, 0.12), (-1, -0.05)):
        hip = Vector((s * 0.13, y0, G + 0.88)); knee = Vector((s * 0.26, y0 + fy * 0.6, G + 0.48)); ankle = Vector((s * 0.3, y0 + fy, G + 0.14))
        P.obj("Trousers", pipe([hip, knee, ankle + Vector((0, 0, 0.06))], [0.17, 0.2, 0.15], 12), "Glass", 1)
        P.obj("Cuff", pipe([ankle + Vector((0, 0, 0.08)), ankle], [0.08, 0.07], 10), "Trim")
        P.obj("Slipper", ball(tuple(ankle + Vector((0, 0.08, -0.06))), (0.08, 0.17, 0.07), 10, 5), "Trim")
        tip = ankle + Vector((0, 0.24, -0.06))
        P.obj("SlipperTip", pipe(bez(tip, tip + Vector((0, 0.08, 0.02)), tip + Vector((0, 0.12, 0.1)), tip + Vector((0, 0.06, 0.14)), 4), [0.05, 0.04, 0.03, 0.02, 0.0], 6), "Trim")
    # the torso: bare chest under an open lapis vest edged in gold
    def vest(c, n):
        x = abs(c.x)
        if n.z > 0.8 and c.z > G + 1.4: return skin
        if n.y > 0.2 and x < 0.11: return skin
        if n.y > 0.2 and x < 0.145: return "Trim"
        return "Accent"
    P.obj("Torso", lathe([(0.0, 0.84), (0.22, 0.86), (0.24, 0.98), (0.27, 1.2), (0.31, 1.36), (0.22, 1.46), (0.0, 1.48)], 20, "z", (0, y0, G)), vest, 1)
    P.obj("Sash", xf(torus(0.25, 0.07, 0.0, 22, 6), None, (0, y0, G + 0.92)), "Base")
    P.obj("SashEnd", pipe(bez((0.2, y0 + 0.12, G + 0.92), (0.3, y0 + 0.2, G + 0.8), (0.32, y0 + 0.15, G + 0.65), (0.36, y0 + 0.1, G + 0.55), 4), [0.06, 0.055, 0.05, 0.05, 0.04], 6), "Base")
    P.obj("Buckle", ball((0, y0 + 0.31, G + 0.93), (0.07, 0.03, 0.06), 8, 4), "Trim")
    P.obj("BuckleGem", ball((0, y0 + 0.335, G + 0.93), (0.035, 0.02, 0.035), 6, 3), "Glass")
    P.obj("Neck", pipe([(0, y0, G + 1.42), (0, y0 + 0.02, G + 1.56)], [0.08, 0.075], 10), skin)
    # the head: a bold face, black beard and a curling moustache
    HC = Vector((0, y0 + 0.03, G + 1.7))
    P.obj("Head", ball(tuple(HC), (0.17, 0.16, 0.19), 14, 7), skin, 1)
    P.obj("Nose", cone(HC + Vector((0, 0.13, 0.02)), HC + Vector((0, 0.22, -0.04)), 0.04, 6), skin, 0)
    for s in (1, -1):
        P.obj("EyeWhite", ball(tuple(HC + Vector((s * 0.065, 0.14, 0.04))), (0.04, 0.02, 0.028), 8, 4), "Lamp")
        P.obj("Eye", ball(tuple(HC + Vector((s * 0.062, 0.155, 0.04))), (0.022, 0.012, 0.024), 8, 4), "Dark")
        P.obj("Brow", bar(HC + Vector((s * 0.02, 0.15, 0.085)), HC + Vector((s * 0.11, 0.13, 0.1)), 0.025, 0.025), "Dark")
        P.obj("Ear", ball(tuple(HC + Vector((s * 0.165, 0.0, 0.0))), (0.03, 0.04, 0.05), 6, 3), skin)
        P.obj("Earring", xf(torus(0.03, 0.008, 0.0, 10, 4), Matrix.Rotation(math.radians(90), 3, "Y"), tuple(HC + Vector((s * 0.17, 0.01, -0.07)))), "Trim")
        m0 = HC + Vector((0, 0.17, -0.05))
        P.obj("Moustache", pipe(bez(m0, m0 + Vector((s * 0.06, 0.0, -0.01)), m0 + Vector((s * 0.12, -0.02, -0.03)), m0 + Vector((s * 0.15, -0.04, 0.03)), 5), [0.025, 0.028, 0.024, 0.018, 0.012, 0.0], 6), "Dark")
        P.obj("Sideburn", ball(tuple(HC + Vector((s * 0.13, 0.08, -0.05))), (0.04, 0.05, 0.09), 8, 4), "Dark")
    P.obj("Beard", hull([tuple(HC + Vector(p)) for p in ((-0.14, 0.06, -0.06), (0.14, 0.06, -0.06), (-0.11, 0.15, -0.09), (0.11, 0.15, -0.09), (0, 0.15, -0.3), (0, 0.08, -0.26), (-0.06, 0.1, -0.2), (0.06, 0.1, -0.2))]), "Dark", 0, False)
    P.obj("Mouth", ball(tuple(HC + Vector((0, 0.165, -0.09))), (0.045, 0.012, 0.015), 8, 4), "Base")
    # the turban: crimson folds, a gold band, a big jewel and a plume
    P.obj("Turban", lathe([(0.0, 0.0), (0.2, 0.02), (0.24, 0.1), (0.25, 0.2), (0.21, 0.3), (0.12, 0.36), (0.0, 0.38)], 18, "z", tuple(HC + Vector((0, -0.01, 0.06)))),
          lambda c, n: "Trim" if ((c.z - HC.z) * 7 + math.atan2(c.x, c.y - HC.y) / (2 * math.pi)) % 1.0 < 0.14 else "Base", 1)
    P.obj("TurbanBand", xf(torus(0.215, 0.025, 0.0, 22, 5), None, tuple(HC + Vector((0, -0.01, 0.1)))), "Trim")
    J = HC + Vector((0, 0.22, 0.22))
    P.obj("JewelSet", ball(tuple(J), (0.07, 0.03, 0.08), 10, 5), "Trim")
    P.obj("Jewel", ball(tuple(J + Vector((0, 0.025, 0))), (0.045, 0.02, 0.055), 8, 4), "Glass")
    P.obj("Plume", pipe(bez(J + Vector((0, -0.02, 0.05)), J + Vector((0.02, -0.05, 0.2)), J + Vector((0.1, -0.15, 0.35)), J + Vector((0.18, -0.3, 0.4)), 6), [0.03, 0.05, 0.06, 0.05, 0.04, 0.025, 0.0], 7), "Lamp")
    # arms: the right one raises the scimitar high, the left one thrust toward the player
    shR = Vector((0.3, y0, G + 1.36)); elR = Vector((0.5, y0 + 0.05, G + 1.65)); hdR = Vector((0.48, y0 + 0.1, G + 1.98))
    shL = Vector((-0.3, y0, G + 1.36)); elL = Vector((-0.45, y0 + 0.3, G + 1.25)); hdL = Vector((-0.45, y0 + 0.62, G + 1.3))
    for sh, el, hd in ((shR, elR, hdR), (shL, elL, hdL)):
        P.obj("Shoulder", ball(tuple(sh), (0.1, 0.1, 0.1), 10, 5), "Accent", 1)
        P.obj("Arm", pipe([sh, el, hd], [0.08, 0.07, 0.06], 10), skin, 1)
        P.obj("Armband", pipe([el + (hd - el) * 0.55, el + (hd - el) * 0.8], [0.075, 0.07], 10), "Trim")
        P.obj("Hand", ball(tuple(hd), (0.075, 0.075, 0.075), 8, 4), skin, 1)
    for k in range(4):   # the open left hand: fingers spread at the player
        a = math.radians(-50 + 33 * k)
        P.obj("Finger", pipe([hdL, hdL + Vector((math.sin(a) * 0.05, 0.12, math.cos(a) * 0.08))], [0.025, 0.018], 5), skin)
    # the scimitar: a gold hilt and a curved, widening steel blade
    P.obj("Grip", pipe([hdR + Vector((0, 0, -0.1)), hdR + Vector((0, 0, 0.1))], [0.03, 0.03], 6), "Dark")
    P.obj("Pommel", ball(tuple(hdR + Vector((0, 0, -0.12))), (0.04, 0.04, 0.04), 6, 3), "Trim")
    P.obj("Guard", bar(hdR + Vector((-0.12, 0, 0.11)), hdR + Vector((0.12, 0, 0.11)), 0.05, 0.05), "Trim")
    blade = bez(hdR + Vector((0, 0, 0.13)), hdR + Vector((-0.02, 0, 0.5)), hdR + Vector((-0.15, 0, 0.85)), hdR + Vector((-0.45, 0, 1.05)), 8)
    for i, (a, b) in enumerate(zip(blade, blade[1:])):
        w = 0.07 + 0.06 * i / 8 if i < 7 else 0.07
        P.obj("Blade", bar(a, b, w, 0.025), "Metal", 0, False)
    P.obj("BladeTip", hull([tuple(blade[-1] + Vector((0, 0.012, 0.04))), tuple(blade[-1] + Vector((0, -0.012, 0.04))), tuple(blade[-1] + Vector((0, 0.012, -0.05))),
                            tuple(blade[-1] + Vector((0, -0.012, -0.05))), tuple(blade[-1] + Vector((-0.14, 0, -0.04)))]), "Metal", 0, False)
    big = Matrix.Translation((0, y0, G)) @ Matrix.Scale(1.25, 4) @ Matrix.Translation((0, -y0, -G))
    for ob in P.parts[n0:]: ob.data.transform(big)
    # ---- the genie lamp at his feet, smoking
    lc = Vector((-0.55, 1.05, 0.06))
    P.obj("Lamp", lathe([(0.0, 0.0), (0.22, 0.04), (0.3, 0.14), (0.22, 0.24), (0.08, 0.28), (0.1, 0.36), (0.0, 0.42)], 14, "z", tuple(lc)), "Trim", 1)
    for v in P.parts[-1].data.vertices: v.co.y = lc.y + (v.co.y - lc.y) * 0.6
    P.obj("Spout", pipe(bez(lc + Vector((0, 0.12, 0.16)), lc + Vector((0, 0.35, 0.18)), lc + Vector((0, 0.5, 0.28)), lc + Vector((0, 0.6, 0.38)), 5), [0.07, 0.06, 0.05, 0.04, 0.035, 0.03], 8), "Trim")
    smoke = bez(lc + Vector((0, 0.62, 0.42)), lc + Vector((-0.3, 0.75, 0.9)), lc + Vector((-0.5, 0.5, 1.3)), lc + Vector((-0.35, 0.3, 1.75)), 9)
    for k, q in enumerate(smoke): P.obj("Smoke", ball(tuple(q), (0.07 + 0.022 * k, 0.07 + 0.022 * k, 0.06 + 0.018 * k), 8, 4), "Glow")
    # ---- the chest of treasure behind him, and cushions
    cc = Vector((0.6, -0.95, 0.3))
    P.obj("Chest", box(tuple(cc), (0.7, 0.5, 0.4)), lambda c, n: "Trim" if (abs(c.x - cc.x) > 0.3 or abs(c.z - cc.z) > 0.17) else "Dark", 0, False)
    P.obj("Lid", box(tuple(cc + Vector((0, -0.3, 0.38))), (0.7, 0.08, 0.45), Matrix.Rotation(math.radians(-25), 3, "X")), "Dark", 0, False)
    for k in range(9):
        P.obj("Coin", ball(tuple(cc + Vector((-0.25 + 0.06 * k, (k % 3) * 0.08 - 0.08, 0.22 + 0.04 * (k % 2)))), (0.07, 0.07, 0.03), 8, 3), "Trim")
    P.obj("Gem", ball(tuple(cc + Vector((0.1, 0.05, 0.32))), (0.07, 0.07, 0.07), 6, 3), "Glass")
    P.obj("Gem", ball(tuple(cc + Vector((-0.15, -0.05, 0.3))), (0.06, 0.06, 0.06), 6, 3), "Accent")
    for k, (x, y) in enumerate(((-0.65, -0.9), (-0.7, -0.3))):
        P.obj("Cushion", ball((x, y, 0.22), (0.28, 0.28, 0.12), 12, 6), ("Accent", "Trim")[k], 1)
    P.part("Muzzle", ball(tuple(lc + Vector((0, 0.65, 0.4))), (0.06, 0.04, 0.05), 8, 4), "Glow", tuple(lc + Vector((0, 0.65, 0.4))))
    return P


# ================================================================= 2. the anubis guardian
def D_anubis():
    """A guardian statue of Anubis: a black jackal head with tall ears and gold-lined eyes, a broad gold-and-lapis collar, a white kilt and
    gold armbands, holding a was-sceptre and an ankh, floating on a slab of sandstone."""
    P = Boss("anubis", {"Base": ((0.07, 0.07, 0.09), 0.6), "Belly": ((0.95, 0.92, 0.84), 0.3), "Accent": LAPIS, "Trim": GOLD,
                        "Glass": ((0.25, 0.85, 0.75), 0.95), "Dark": ((0.03, 0.03, 0.04), 0.5), "Glow": ((1.0, 0.82, 0.35), 0.5),
                        "Metal": ((0.85, 0.70, 0.48), 0.3), "Lamp": ((0.45, 1.0, 0.9), 0.8)})
    torso = pipe([(0, 0, 0.0), (0, 0, 0.35), (0, 0, 0.8), (0, 0, 1.05), (0, 0, 1.15)], [0.27, 0.25, 0.4, 0.42, 0.2], 16)
    for v in torso.verts: v.co.y *= 0.62
    P.obj("Torso", torso, "Base", 1)
    for s in (1, -1): P.obj("Shoulder", ball((s * 0.42, 0, 0.98), (0.17, 0.15, 0.15), 10, 5), "Base")
    kilt = lathe([(0.29, 0.08), (0.42, -0.45), (0.0, -0.45)], 16, "z")
    for v in kilt.verts: v.co.y *= 0.7
    P.obj("Kilt", kilt, lambda c, n: "Trim" if c.z > 0.0 else ("Belly" if (c.x * 8) % 1.0 > 0.15 else "Metal"), 1)
    P.obj("Belt", torus(0.29, 0.04, 0.05, 18, 5), "Trim")
    P.parts[-1].data.transform(Matrix.Scale(0.7, 4, Vector((0, 1, 0))))
    for s in (1, -1):
        P.obj("Leg", pipe([(s * 0.15, 0, -0.4), (s * 0.16, 0.05, -0.65)], [0.1, 0.08], 8), "Base")
        P.obj("Anklet", pipe([(s * 0.16, 0.05, -0.6), (s * 0.16, 0.05, -0.55)], [0.09, 0.09], 8), "Trim")
    collar = lathe([(0.18, 1.14), (0.48, 1.04), (0.5, 0.98), (0.2, 1.08)], 20, "z")
    for v in collar.verts: v.co.y *= 0.8
    P.obj("Collar", collar, lambda c, n: "Trim" if (math.hypot(c.x, c.y / 0.8) * 12) % 1.0 < 0.5 else "Accent")
    P.obj("Neck", pipe([(0, 0.0, 1.15), (0, 0.05, 1.35)], [0.16, 0.14], 10), "Base")
    P.obj("Head", ball((0, 0.05, 1.5), (0.22, 0.26, 0.22), 12, 6), "Base", 1)
    P.obj("Snout", cone((0, 0.2, 1.45), (0, 0.65, 1.38), 0.12, 10), "Base", 0, False)
    P.obj("Nose", ball((0, 0.64, 1.39), (0.04, 0.03, 0.03), 6, 3), "Dark")
    for s in (1, -1):
        P.obj("Ear", hull([(s * 0.08, 0.0, 1.62), (s * 0.2, -0.05, 1.6), (s * 0.18, -0.02, 2.05), (s * 0.13, 0.03, 1.68)]), "Base", 0, False)
        P.obj("EarIn", hull([(s * 0.11, 0.01, 1.66), (s * 0.18, -0.02, 1.65), (s * 0.165, 0.0, 1.95), (s * 0.135, 0.02, 1.7)]), "Trim", 0, False)
        P.obj("Eye", ball((s * 0.11, 0.2, 1.56), (0.05, 0.03, 0.025), 8, 4), "Lamp")
        P.obj("EyeLine", box((s * 0.15, 0.17, 1.55), (0.12, 0.02, 0.02), Matrix.Rotation(math.radians(s * 10), 3, "Y")), "Trim", 0, False)
        sh = Vector((s * 0.48, 0.0, 0.95)); el = Vector((s * 0.68, 0.25, 0.6)); hd = Vector((s * 0.7, 0.55, 0.65))
        P.obj("Arm", pipe([sh, el, hd], [0.13, 0.1, 0.08], 10), "Base", 1)
        P.obj("Armband", pipe([sh + (el - sh) * 0.3, sh + (el - sh) * 0.45], [0.14, 0.14], 10), "Trim")
        P.obj("Bracer", pipe([el + (hd - el) * 0.4, el + (hd - el) * 0.7], [0.11, 0.1], 10), "Trim")
        P.obj("Hand", ball(tuple(hd), (0.09, 0.09, 0.09), 8, 4), "Base")
    # the was-sceptre in the right hand, the ankh in the left
    P.obj("Sceptre", pipe([(0.7, 0.55, -0.6), (0.7, 0.55, 1.75)], [0.035, 0.035], 6), "Trim")
    P.obj("SceptreHead", pipe(bez((0.7, 0.55, 1.75), (0.7, 0.62, 1.88), (0.7, 0.75, 1.88), (0.7, 0.82, 1.8), 4), [0.05, 0.05, 0.045, 0.04, 0.035], 6), "Trim")
    P.obj("AnkhLoop", torus(0.12, 0.03, 0.0, 14, 5), "Trim"); P.parts[-1].data.transform(Matrix.Translation((-0.7, 0.6, 1.0)) @ Matrix.Scale(1.0, 4) @ Matrix.Rotation(math.radians(90), 4, "X"))
    P.obj("AnkhBar", box((-0.7, 0.6, 0.85), (0.3, 0.04, 0.05)), "Trim", 0, False)
    P.obj("AnkhStem", box((-0.7, 0.6, 0.7), (0.05, 0.04, 0.32)), "Trim", 0, False)
    # the sandstone slab
    P.obj("Slab", box((0, 0, -0.82), (1.5, 1.0, 0.3)), lambda c, n: "Trim" if n.z > 0.5 and (abs(c.x) > 0.68 or abs(c.y) > 0.43) else "Metal", 0, False)
    for k in range(5):
        P.obj("Glyph", box((-0.5 + k * 0.25, 0.51, -0.8), (0.12, 0.02, 0.15)), "Accent" if k % 2 else "Trim", 0, False)
    P.part("Muzzle", ball((0, 0.68, 1.38), (0.05, 0.03, 0.04), 8, 4), "Lamp", (0, 0.68, 1.38))
    return P


# ================================================================= 3. the winged sphinx
def D_sphinx():
    """A winged sphinx: a golden lion's body with a human face under a striped blue-and-gold nemes headdress, a cobra on its brow, a long
    plaited beard, and great feathered wings with blue and gold bands that beat."""
    P = Boss("sphinx", {"Base": ((0.85, 0.62, 0.32), 0.4), "Belly": ((0.95, 0.82, 0.58), 0.35), "Accent": LAPIS, "Trim": GOLD,
                        "Glass": ((0.25, 0.85, 0.65), 0.95), "Dark": ((0.10, 0.07, 0.05), 0.5), "Glow": ((1.0, 0.80, 0.35), 0.5),
                        "Metal": ((0.70, 0.50, 0.25), 0.4), "Lamp": ((0.45, 1.0, 0.9), 0.8)})
    P.obj("Body", ball((0, -0.2, 0.0), (0.48, 1.05, 0.42), 16, 8), lambda c, n: "Belly" if n.z < -0.4 else "Base", 1)
    P.obj("Chest", ball((0, 0.6, 0.15), (0.42, 0.38, 0.45), 14, 7), "Base", 1)
    P.obj("Head", ball((0, 0.85, 0.75), (0.26, 0.26, 0.3), 14, 7), "Base", 1)
    def nemes(c, n):
        if n.y > 0.75: return "Base"
        return "Accent" if (c.z * 9) % 1.0 < 0.45 else "Trim"
    P.obj("Nemes", hull([(-0.32, 0.7, 1.08), (0.32, 0.7, 1.08), (-0.38, 0.75, 0.55), (0.38, 0.75, 0.55), (-0.5, 0.6, 0.15), (0.5, 0.6, 0.15),
                         (-0.3, 0.45, 0.95), (0.3, 0.45, 0.95), (0, 0.5, 1.15), (-0.45, 0.4, 0.2), (0.45, 0.4, 0.2)]), nemes, 0, False)
    P.obj("Face", ball((0, 1.02, 0.72), (0.2, 0.1, 0.24), 12, 6), "Base")
    P.obj("Cobra", pipe(bez((0, 0.98, 1.0), (0, 1.1, 1.05), (0, 1.12, 1.15), (0, 1.08, 1.22), 4), [0.04, 0.045, 0.04, 0.035, 0.03], 6), "Trim")
    P.obj("Beard", pipe([(0, 1.08, 0.5), (0, 1.1, 0.3)], [0.05, 0.04], 6), lambda c, n: "Trim" if (c.z * 20) % 1.0 < 0.4 else "Accent")
    for s in (1, -1):
        P.obj("Eye", ball((s * 0.08, 1.1, 0.78), (0.04, 0.02, 0.022), 8, 4), "Lamp")
        P.obj("EyeLine", box((s * 0.12, 1.09, 0.78), (0.1, 0.02, 0.015)), "Dark", 0, False)
        for fy in (0.75, -0.95):   # paws stretched out
            hip = Vector((s * 0.3, fy, -0.15))
            P.obj("Leg", pipe([hip, hip + Vector((0, 0.3 if fy > 0 else -0.3, -0.3))], [0.13, 0.1], 8), "Base")
            P.obj("Paw", ball(tuple(hip + Vector((0, 0.36 if fy > 0 else -0.36, -0.34))), (0.11, 0.14, 0.07), 8, 4), "Belly")
        name = "FlapR" if s > 0 else "FlapL"
        hub = (s * 0.35, 0.2, 0.3)
        keys = [(0.35, 0.65, -0.55, 0.14, 0.3), (1.0, 0.75, -0.75, 0.1, 0.55), (1.8, 0.7, -0.7, 0.07, 0.9), (2.5, 0.5, -0.45, 0.04, 1.2), (2.9, 0.3, -0.05, 0.02, 1.4)]
        bm = sweep([(x, airfoil(le, te, th, z)) for (x, le, te, th, z) in fine(keys)], "x")
        if s < 0: bm = mirror_x(bm)
        def plumes(c, n):
            if n.z < -0.3: return "Belly"
            if c.y < -0.45: return "Accent" if (abs(c.x) * 5) % 1.0 < 0.5 else "Trim"
            return "Trim" if (abs(c.x) * 2.5) % 1.0 < 0.18 else ("Accent" if c.y < 0.0 else "Base")
        P.part(name, bm, plumes, hub, 0)
    P.obj("Tail", pipe(bez((0, -1.2, 0.05), (0, -1.6, 0.0), (0.2, -1.8, 0.3), (0.15, -1.85, 0.55), 6), [0.06, 0.05, 0.045, 0.04, 0.04, 0.04, 0.0], 6), "Base")
    P.obj("TailTuft", ball((0.15, -1.85, 0.6), (0.08, 0.08, 0.1), 8, 4), "Dark")
    P.part("Muzzle", ball((0, 1.14, 0.62), (0.05, 0.03, 0.04), 8, 4), "Lamp", (0, 1.14, 0.62))
    return P


# ================================================================= 4. the sun barque
def D_barque():
    """Ra's sun barque sailing the sky: a golden papyrus boat with curled lotus prow and stern, a shrine amidships under a blazing sun disc
    held by a cobra, a square sail painted with the eye, and oars on each side that row."""
    P = Boss("barque", {"Base": ((0.85, 0.62, 0.25), 0.6), "Belly": ((0.95, 0.90, 0.78), 0.3), "Accent": LAPIS, "Trim": GOLD,
                        "Glass": ((0.25, 0.85, 0.65), 0.95), "Dark": ((0.10, 0.07, 0.05), 0.5), "Glow": ((1.0, 0.62, 0.15), 0.5),
                        "Metal": ((0.70, 0.18, 0.12), 0.5), "Lamp": ((1.0, 0.88, 0.45), 0.8)})
    P.obj("Hull", loft([(1.7, 0.08, 0.08, 0, 0.3), (1.4, 0.45, 0.3, 0, 0.05), (0.5, 0.62, 0.35, 0, -0.05), (-0.6, 0.6, 0.35, 0, -0.05), (-1.4, 0.4, 0.3, 0, 0.05), (-1.7, 0.08, 0.08, 0, 0.3)], 18, sq=1.4),
          lambda c, n: "Accent" if -0.05 < c.z < 0.05 else ("Trim" if c.z > 0.18 else "Base"), 1)
    for sy in (1, -1):   # lotus prow and stern, curling up
        curl = bez((0, sy * 1.65, 0.3), (0, sy * 2.0, 0.6), (0, sy * 2.05, 1.05), (0, sy * 1.85, 1.2), 7)
        P.obj("Curl", pipe(curl, [0.12, 0.11, 0.1, 0.09, 0.08, 0.07, 0.06, 0.05], 8), "Trim")
        for k in range(6):
            a = math.radians(-60 + k * 24)
            P.obj("Petal", cone(curl[-1], curl[-1] + Vector((math.sin(a) * 0.25, sy * 0.05, 0.2 + 0.1 * math.cos(a))), 0.06, 5), "Metal" if k % 2 else "Accent", 0, False)
    P.obj("Deck", box((0, 0, 0.32), (0.95, 3.0, 0.05)), "Belly", 0, False)
    # the shrine and the sun
    P.obj("Shrine", box((0, -0.1, 0.62), (0.7, 0.75, 0.55)), lambda c, n: "Accent" if abs(n.y) > 0.6 and (c.z * 6) % 1.0 < 0.4 else "Trim", 0, False)
    P.obj("ShrineTop", box((0, -0.1, 0.94), (0.82, 0.86, 0.08)), "Trim", 0, False)
    P.obj("Cobra", pipe(bez((0, 0.15, 0.95), (0, 0.2, 1.15), (0, 0.15, 1.3), (0, 0.05, 1.4), 5), [0.05, 0.06, 0.07, 0.06, 0.05, 0.04], 6), "Trim")
    P.obj("Sun", ball((0, -0.1, 1.75), (0.48, 0.12, 0.48), 20, 8), "Glow")
    P.obj("SunRim", torus(0.5, 0.05, 0.0, 24, 6), "Trim"); P.parts[-1].data.transform(Matrix.Translation((0, -0.1, 1.75)) @ Matrix.Rotation(math.radians(90), 4, "X"))
    for k in range(12):
        a = 2 * math.pi * k / 12
        P.part("RollRays", cone((math.cos(a) * 0.56, -0.12, 1.75 + math.sin(a) * 0.56), (math.cos(a) * 0.85, -0.12, 1.75 + math.sin(a) * 0.85), 0.06, 4), "Lamp", (0, -0.1, 1.75), 0, False)
    # mast and sail with the eye
    P.obj("Mast", pipe([(0, -0.95, 0.3), (0, -0.95, 1.9)], [0.04, 0.035], 6), "Dark")
    P.obj("Yard", pipe([(-0.7, -0.95, 1.85), (0.7, -0.95, 1.85)], [0.03, 0.03], 6), "Dark")
    def sail(u, v):
        return Vector(((u - 0.5) * 1.3, -0.92 + 0.15 * math.sin(math.pi * u) * math.sin(math.pi * v), 1.0 + v * 0.82))
    bm = grid_surface(lambda u, v: sail(u, v), 8, 6, 0.02)
    P.part("Cloth", bm, lambda c, n: "Accent" if ((c.x / 0.28) ** 2 + ((c.z - 1.42) / 0.12) ** 2 < 1.0) else ("Metal" if (c.z * 6) % 1.0 < 0.18 else "Belly"), (0, 0, 0), 0, False)
    # the oars, rowing
    for s in (1, -1):
        for k, y in enumerate((0.9, 0.3, -0.3, -0.9)):
            hub = (s * 0.58, y, 0.25)
            P.part("Sway%d" % (k * 2 + (1 if s > 0 else 0)), pipe([hub, (s * 1.25, y - 0.1, -0.45)], [0.03, 0.03], 5), "Dark", hub)
            P.part("Sway%d" % (k * 2 + (1 if s > 0 else 0)), box((s * 1.3, y - 0.11, -0.55), (0.06, 0.18, 0.25)), "Trim", hub, 0, False)
    P.part("Muzzle", ball((0, 0.0, 1.75), (0.1, 0.05, 0.1), 8, 4), "Glow", (0, 0.0, 1.75))
    return P


# ================================================================= 5. the sky pyramid
def D_pyramid():
    """The last boss: a pyramid risen into the sky - sandstone courses with a golden capstone, a great glowing Eye of Horus on its face, two
    gilded obelisks floating beside it, a carved root of rock below, and two golden rings of hieroglyphs turning round it."""
    P = Boss("pyramid", {"Base": ((0.88, 0.72, 0.45), 0.3), "Belly": ((0.70, 0.55, 0.32), 0.3), "Accent": LAPIS, "Trim": GOLD,
                         "Glass": ((0.25, 0.85, 0.65), 0.95), "Dark": ((0.12, 0.08, 0.05), 0.5), "Glow": ((0.45, 1.0, 0.9), 0.5),
                         "Metal": ((0.70, 0.18, 0.12), 0.5), "Lamp": ((1.0, 0.88, 0.45), 0.8)})
    H = 2.2; B = 1.5
    pts = [(-B, -B, 0), (B, -B, 0), (B, B, 0), (-B, B, 0), (0, 0, H)]
    P.obj("Pyramid", hull(pts), lambda c, n: "Belly" if n.z < -0.5 else ("Trim" if c.z > H * 0.8 else ("Dark" if (c.z * 5) % 1.0 < 0.06 else "Base")), 0, False)
    P.obj("Root", hull([(-B, -B, 0), (B, -B, 0), (B, B, 0), (-B, B, 0), (0.3, 0.2, -1.1), (-0.25, -0.15, -1.2), (0.0, 0.0, -1.4)]), "Belly", 0, False)
    # the eye on the front face
    face_c = Vector((0, B * 0.45, H * 0.55))
    tilt = Matrix.Rotation(math.atan2(B, H), 3, "X")
    def onface(p): return tilt @ Vector(p) + face_c
    eye = [onface((math.cos(a) * 0.45, 0.04, math.sin(a) * 0.18 * (1 if math.sin(a) > 0 else 0.8))) for a in [2 * math.pi * i / 20 for i in range(20)]]
    P.obj("EyeWhite", hull([tuple(p) for p in eye] + [tuple(onface((0, -0.02, 0)))]), "Belly", 0, False)
    P.obj("Iris", ball(tuple(onface((0, 0.08, 0))), (0.14, 0.06, 0.14), 10, 5), "Glow")
    P.obj("Pupil", ball(tuple(onface((0, 0.12, 0))), (0.06, 0.03, 0.06), 8, 4), "Dark")
    P.obj("Brow", pipe([onface((-0.5, 0.06, 0.28)), onface((0, 0.06, 0.34)), onface((0.5, 0.06, 0.28))], [0.035] * 3, 6), "Accent")
    P.obj("Tear", pipe([onface((-0.05, 0.06, -0.18)), onface((-0.05, 0.06, -0.45)), onface((-0.22, 0.06, -0.55))], [0.03] * 3, 6), "Accent")
    P.obj("Mark", pipe([onface((0.42, 0.06, 0.0)), onface((0.6, 0.06, 0.0))], [0.03, 0.03], 6), "Accent")
    # obelisks floating beside it
    for s in (1, -1):
        c = Vector((s * 2.1, 0.4, 0.4))
        P.obj("Obelisk", hull([tuple(c + Vector((x, y, 0))) for x in (-0.18, 0.18) for y in (-0.18, 0.18)] + [tuple(c + Vector((x, y, 1.6))) for x in (-0.12, 0.12) for y in (-0.12, 0.12)]),
              lambda c2, n: "Trim" if c2.z > c.z + 1.4 else "Base", 0, False)
        P.obj("ObeliskTip", hull([tuple(c + Vector((x, y, 1.6))) for x in (-0.12, 0.12) for y in (-0.12, 0.12)] + [tuple(c + Vector((0, 0, 1.85)))]), "Trim", 0, False)
        for k in range(4): P.obj("Glyph", box(tuple(c + Vector((0, 0.17, 0.3 + k * 0.3))), (0.1, 0.02, 0.12)), "Accent", 0, False)
    # two golden rings of hieroglyphs turning round it
    for k, (r, z) in enumerate(((2.3, 0.5), (2.0, 1.3))):
        P.part("SpinRing%d" % k, torus(r, 0.05, z, 48, 6), "Trim", (0, 0, z))
        for i in range(12):
            a = 2 * math.pi * (i + 0.5 * k) / 12
            P.part("SpinRing%d" % k, box((math.cos(a) * r, math.sin(a) * r, z), (0.14, 0.14, 0.14), Matrix.Rotation(a, 3, "Z")), "Accent" if i % 2 else "Glow", (0, 0, z), 0, False)
    P.part("Muzzle", ball(tuple(onface((0, 0.16, 0))), (0.07, 0.03, 0.07), 8, 4), "Glow", tuple(onface((0, 0.16, 0))))
    return P



def bar(a, b, w, t, up=(0, 1, 0)):
    """a squared-off bar between two points, w wide (across, in the face plane) and t thick (toward +Y)."""
    a, b = Vector(a), Vector(b); d = (b - a).normalized(); n = Vector(up)
    if abs(d.dot(n)) > 0.95: n = Vector((0, 0, 1))
    s = d.cross(n).normalized() * w * 0.5; f = n * t * 0.5
    pts = [p + ds + df for p in (a, b) for ds in (s, -s) for df in (f, -f)]
    return hull([tuple(p) for p in pts])


# ================================================================= 4 (new). the pharaoh cobra
def D_cobra():
    """The uraeus, the pharaoh's cobra (2026-10-11, in place of the sun barque: "a new boss with features"): a giant golden cobra reared up
    from its coils on a floating dais, its spread hood painted in the gold-and-lapis stripes of a pharaoh's nemes, burning emerald eyes with
    slit pupils under angry golden brows, a striking jaw with long fangs and a forked tongue, gold bands down its cream belly, the sun disc of
    Ra between golden horns above its head, and great feathered wings of lapis, turquoise and gold spreading from behind the hood."""
    P = Boss("cobra", {"Base": ((0.86, 0.58, 0.16), 0.8), "Belly": ((0.96, 0.90, 0.72), 0.35), "Accent": LAPIS, "Trim": GOLD,
                       "Glass": ((0.12, 0.72, 0.66), 0.9), "Dark": ((0.03, 0.03, 0.04), 0.5), "Glow": ((0.30, 1.0, 0.45), 0.5),
                       "Metal": ((0.72, 0.08, 0.06), 0.5), "Lamp": ((1.0, 0.55, 0.15), 0.8)})
    # the coils: a spiral settling on the dais, the tail tapering at its outer end
    coil = []; radii = []
    for i in range(61):
        t = i / 60.0
        a = math.pi / 2 + (t - 1) * 2.2 * 2 * math.pi
        r = 0.95 - 0.42 * t
        coil.append(Vector((math.cos(a) * r, math.sin(a) * r, -0.92 + 0.3 * t + 0.08 * math.sin(t * 20))))
        radii.append(0.05 + 0.21 * min(1.0, t / 0.25))
    neck = bez(coil[-1], coil[-1] + Vector((0, 0.32, 0.25)), (0, 0.3, 0.6), (0, 0.08, 1.45), 12)[1:]
    path = coil + neck; radii += [0.26 - 0.03 * k / len(neck) for k in range(len(neck))]
    def scales(c, n):
        if n.y > 0.45 and c.z > -0.45:
            if (c.z * 4.5) % 1.0 < 0.2: return "Trim"
            return "Belly" if c.z < 0.3 else "Base"
        if n.z < -0.5: return "Belly"
        return "Accent" if (ang(c) / (2 * math.pi) * 26) % 1.0 < 0.24 else "Base"
    P.obj("Body", pipe(path, radii, 14), scales, 1)
    # the hood: a broad oval fanned behind the head, striped like a nemes, rimmed in gold
    def hoodpaint(c, n):
        if n.y < -0.2: return "Base"
        e = math.hypot(c.x / 0.88, (c.z - 1.15) / 0.92)
        if e > 0.87: return "Trim"
        if abs(c.x) < 0.2: return "Trim" if (c.z * 4.5) % 1.0 < 0.18 else "Belly"
        if abs(c.x) < 0.26: return "Trim"
        return "Accent" if (abs(c.x) * 6.5) % 1.0 < 0.45 else "Trim"
    hood = ball((0, 0.06, 1.15), (0.88, 0.15, 0.92), 26, 14)
    for v in hood.verts: v.co.y += 0.3 * (v.co.x / 0.88) ** 2
    P.obj("Hood", hood, hoodpaint, 1)
    for s in (1, -1): P.obj("HoodJewel", ball((s * 0.52, 0.22, 1.05), (0.1, 0.05, 0.13), 10, 5), "Glass")
    # the head: broad, flat, gold, crowned with lapis stripes, a gold snout
    def headpaint(c, n):
        if n.z > 0.35 and c.y < 0.72: return "Accent" if (abs(c.x) * 8) % 1.0 < 0.4 else "Trim"
        return "Belly" if n.z < -0.4 else "Base"
    P.obj("Head", ball((0, 0.42, 1.74), (0.42, 0.55, 0.25), 18, 9), headpaint, 1)
    P.obj("Mouth", ball((0, 0.5, 1.58), (0.36, 0.44, 0.07), 12, 6), "Metal")
    for s in (1, -1):
        c = Vector((s * 0.25, 0.7, 1.83))
        P.obj("EyeRidge", ball(tuple(c - Vector((0, 0.03, 0))), (0.14, 0.1, 0.12), 10, 5), "Base")
        P.obj("Eye", ball(tuple(c + Vector((0, 0.05, 0))), (0.11, 0.06, 0.11), 12, 6), "Glow")
        P.obj("Slit", box(tuple(c + Vector((0, 0.11, 0))), (0.024, 0.02, 0.16)), "Dark", 0, False)
        P.obj("Glint", ball(tuple(c + Vector((s * -0.03, 0.115, 0.05))), (0.02, 0.01, 0.02), 6, 3), "Belly")
        P.obj("Brow", bar((s * 0.07, 0.82, 1.9), (s * 0.42, 0.66, 2.04), 0.08, 0.07), "Trim", 0, False)   # angry: low at the middle
        P.obj("Kohl", bar((s * 0.35, 0.7, 1.8), (s * 0.52, 0.5, 1.76), 0.03, 0.04), "Dark", 0, False)
        P.obj("Nostril", ball((s * 0.08, 0.95, 1.76), (0.025, 0.015, 0.015), 6, 3), "Dark")
        P.obj("Fang", cone((s * 0.17, 0.86, 1.6), (s * 0.16, 0.88, 1.34), 0.045, 6), "Belly", 0, False)
    # the lower jaw strikes
    hinge = (0, 0.1, 1.58)
    P.part("SwayJaw", ball((0, 0.46, 1.5), (0.35, 0.46, 0.08), 12, 6), lambda c, n: "Metal" if n.z > 0.5 else "Belly", hinge)
    tongue = [Vector((0, 0.8, 1.54)), Vector((0, 1.05, 1.52)), Vector((0, 1.22, 1.5))]
    P.part("SwayJaw", pipe(tongue, [0.03, 0.026, 0.02], 6), "Metal", hinge)
    for s in (1, -1): P.part("SwayJaw", cone((0, 1.21, 1.5), (s * 0.08, 1.35, 1.49), 0.018, 5), "Metal", hinge)
    # the red sun disc of Ra between golden horns
    P.obj("SunDisc", lathe([(0.0, -0.06), (0.42, -0.06), (0.44, 0.0), (0.42, 0.06), (0.0, 0.06)], 24, "y", (0, -0.02, 2.5)), "Metal")
    P.obj("SunRim", torus(0.44, 0.035, 0.0, 26, 5), "Trim"); P.parts[-1].data.transform(Matrix.Translation((0, 0.05, 2.5)) @ Matrix.Rotation(math.radians(90), 4, "X"))
    P.obj("SunCore", ball((0, 0.05, 2.5), (0.16, 0.04, 0.16), 12, 6), "Lamp")
    for s in (1, -1):
        P.obj("Horn", pipe(bez((s * 0.14, 0.0, 2.0), (s * 0.6, 0.0, 2.05), (s * 0.62, 0.0, 2.72), (s * 0.3, 0.0, 2.95), 8), [0.06, 0.06, 0.055, 0.05, 0.045, 0.04, 0.03, 0.02, 0.01], 8), "Trim")
    # the wings: feathers of gold, turquoise and lapis fanned out from behind the hood
    for s, nm in ((1, "FlapR"), (-1, "FlapL")):
        hub = (s * 0.55, -0.08, 1.15)
        for row, (paint, n, L0, w) in enumerate((("Accent", 10, 1.85, 0.42), ("Glass", 9, 1.3, 0.38), ("Trim", 8, 0.8, 0.32))):
            for k in range(n):
                a = math.radians(-38 + k * (78.0 / (n - 1)))
                L = L0 * (1.0 - 0.18 * abs(a - math.radians(15)))
                root = Vector(hub) + Vector((0, row * 0.045, 0))
                tip = root + Vector((s * math.cos(a) * L, -0.08, math.sin(a) * L))
                side = Vector((-math.sin(a), 0, math.cos(a))) * w * 0.5; mid = root + (tip - root) * 0.55
                P.part(nm, hull([tuple(root + side * 0.5), tuple(root - side * 0.5), tuple(mid + side), tuple(mid - side), tuple(tip),
                                 tuple(mid + Vector((0, 0.025, 0))), tuple(mid - Vector((0, 0.025, 0)))]), paint, hub, 0, False)
                if row == 0: P.part(nm, ball(tuple(tip), (0.07, 0.025, 0.07), 6, 3), "Trim", hub)
    # the floating dais, lapis rimmed, glyphs round its edge; golden orbs circling
    P.obj("Dais", lathe([(0.0, -1.32), (0.9, -1.32), (1.2, -1.16), (1.2, -1.04), (0.0, -1.04)], 28, "z"), lambda c, n: "Trim" if n.z > 0.5 else ("Accent" if c.z > -1.12 else "Base"))
    for k in range(16):
        a = 2 * math.pi * k / 16
        P.obj("Glyph", box((math.cos(a) * 1.21, math.sin(a) * 1.21, -1.1), (0.1, 0.02, 0.07), Matrix.Rotation(a + math.pi / 2, 3, "Z")), ("Trim", "Glass")[k % 2], 0, False)
    for k in range(6):
        a = 2 * math.pi * k / 6
        P.part("SpinOrbs", ball((math.cos(a) * 1.6, math.sin(a) * 1.6, -0.6), (0.13, 0.13, 0.13), 10, 5), "Trim", (0, 0, -0.6))
        P.part("SpinOrbs", ball((math.cos(a) * 1.6, math.sin(a) * 1.6, -0.48), (0.07, 0.07, 0.05), 8, 4), "Accent", (0, 0, -0.6))
    P.part("Muzzle", ball((0, 0.98, 1.55), (0.06, 0.04, 0.05), 8, 4), "Glow", (0, 0.98, 1.55))
    return P


BOSSES = [("carpet", D_carpet), ("anubis", D_anubis), ("sphinx", D_sphinx), ("pyramid", D_pyramid),
          ("cobra", D_cobra)]

if __name__ == "__main__":
    os.makedirs(AB.OUT, exist_ok=True)
    for bid, fn in BOSSES:
        if ONLY and bid not in ONLY: continue
        fn().finish()
    print("DONE")
