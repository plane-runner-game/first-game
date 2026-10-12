# Sky Squad, the sunny meadow's five bosses (2026-10-11: "do the bosses for the other maps that do not have their own yet"): the queen
# bumblebee, the giant ladybug, the emerald dragonfly, the sunflower titan and the windmill hill. Built from code like the other worlds' bosses
# (alien_bosses.py lends its Boss class and shapes).
# Run: blender -b -P Tools/blender/meadow_bosses.py -- <out dir> [export] [ids,comma,separated]
# Conventions as alien_bosses.py: +Y nose, +Z up, +X right; "Flap*" rock about the nose axis, "Sway*" about the wing axis, "Spin*" turn slowly
# about up, "Roll*" turn slowly about the nose axis, "Cloth" stays still without the outline, "Muzzle" is where his shots leave from.
import bpy, bmesh, math, sys, os, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mathutils import Vector, Matrix
from enemy_planes import loft, sweep, lathe, box, hull, tube, mirror_x, airfoil
import alien_bosses as AB
from alien_bosses import Boss, xf, ball, pipe, cone, bez, torus, sheet, grow, ang

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ONLY = argv[2].split(",") if len(argv) > 2 and argv[2] else None

GOLD = ((0.98, 0.76, 0.22), 0.8)
WING = ((0.86, 0.95, 1.0), 0.9)
INK = ((0.05, 0.04, 0.05), 0.5)


def R(axis, deg):
    return Matrix.Rotation(math.radians(deg), 3, axis)

def ewing(hub, L, W, yaw, lift, s, thick=0.03, seg=18):
    """a flat oval wing from the hub outwards (+x on the right), swept back by yaw, raised by lift; s = -1 mirrors it to the left."""
    bm = ball((L * 0.5, 0, 0), (L * 0.5, W * 0.5, thick), seg, 6)
    xf(bm, R("Z", -yaw) @ R("Y", -lift))
    if s < 0: bm = mirror_x(bm)
    return xf(bm, None, hub)

def leaf(c, L, W, yaw, pitch, thick=0.05):
    """a pointed leaf lying along +x from c, turned by yaw about up and pitch about the nose axis."""
    bm = ball((L * 0.5, 0, 0), (L * 0.5, W * 0.5, thick), 16, 6)
    for v in bm.verts:
        t = v.co.x / L                       # pinch both ends to points
        v.co.y *= 0.35 + 0.9 * math.sin(math.pi * min(max(t, 0.0), 1.0)) ** 0.8
        v.co.z += 0.12 * L * t * t           # the tip curls up
    xf(bm, R("Z", yaw) @ R("Y", -pitch))
    return xf(bm, None, c)

def cute_eyes(P, c, r, s, white="Glass", pupil="Dark", shine="Glow", look=(0, 1, 0)):
    """a big cartoon eye: a white, a pupil looking forward, a spark of light."""
    c = Vector(c); L = Vector(look).normalized()
    P.obj("EyeWhite", ball(tuple(c), (r, r * 0.7, r * 1.1), 12, 6), white)
    pc = c + L * r * 0.55 + Vector((-s * r * 0.08, 0, -r * 0.05))
    P.obj("Pupil", ball(tuple(pc), (r * 0.55, r * 0.35, r * 0.65), 10, 5), pupil)
    P.obj("Spark", ball(tuple(pc + L * r * 0.28 + Vector((s * r * 0.15, 0, r * 0.25))), (r * 0.15, r * 0.08, r * 0.15), 6, 3), shine)


# ================================================================= shared bits for the round-three meadow bosses (2026-10-12: "make them better, all of them")
def dome(c, r, cut=0.0, seg=16, rings=8, thick=0.025):
    """the top of an ellipsoid above c.z + cut, given a little thickness: a helmet, a cap."""
    bm = ball(tuple(c), r, seg, rings)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < c[2] + cut], context="VERTS")
    bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=thick)
    return bm

def wpt(hub, yaw, lift, s, u, v, w=0.0):
    """a point on a wing made by ewing: u along the wing, v across it, w above its face."""
    p = R("Z", -yaw) @ R("Y", -lift) @ Vector((u, v, w))
    if s < 0: p.x = -p.x
    return Vector(hub) + p

def veins(P, name, hub, root, L, W, yaw, lift, s, paint="Trim", r=0.016):
    """gold veins over a wing: a spine and four branches, slightly above the face."""
    spine = [wpt(root, yaw, lift, s, L * t, 0.0, 0.03) for t in (0.0, 0.35, 0.7, 0.96)]
    P.part(name, pipe(spine, [r * 1.3, r, r * 0.8, r * 0.5], 5), paint, hub)
    for t, side in ((0.3, 1), (0.45, -1), (0.62, 1), (0.78, -1)):
        a = wpt(root, yaw, lift, s, L * t, 0.0, 0.03); b = wpt(root, yaw, lift, s, L * (t + 0.16), side * W * 0.38, 0.03)
        P.part(name, pipe([a, b], [r * 0.8, r * 0.4], 4), paint, hub)

def bolt_pts(a, b, n=5, amp=0.12):
    a, b = Vector(a), Vector(b); d = b - a
    side = d.cross(Vector((0, 0, 1)))
    side = side.normalized() if side.length > 1e-4 else Vector((1, 0, 0))
    return [a] + [a + d * (i / n) + side * amp * (1 if i % 2 else -1) for i in range(1, n)] + [b]

def hexplate(P, c, nrm, r, name="Honeycomb"):
    """a gold hexagon rim holding a cell of glowing honey, laid on a surface facing nrm."""
    q = Vector(nrm).normalized().to_track_quat("Z", "Y").to_matrix()
    rim = lathe([(0.0, 0.025), (r, 0.025), (r, -0.02), (0.0, -0.02)], 6, "z"); xf(rim, q, tuple(c))
    cell = lathe([(0.0, 0.045), (r * 0.7, 0.04), (r * 0.7, 0.0), (0.0, 0.0)], 6, "z"); xf(cell, q, tuple(c))
    P.obj(name, rim, "Trim", 0, False); P.obj(name + "Cell", cell, "Lamp", 0, False)

def mini_bee(P, name, c, fwd, hub, k=1.0, spear=True, col="Base"):
    """a little worker bee (or a royal guard with a spear) flying along fwd - a part of the mover called name."""
    c = Vector(c); f = Vector(fwd).normalized(); side = f.cross(Vector((0, 0, 1))).normalized()
    body = ball((0, 0, 0), (0.1 * k, 0.15 * k, 0.1 * k), 10, 6)
    xf(body, f.to_track_quat("Y", "Z").to_matrix(), tuple(c))
    P.part(name, body, lambda cc, n, c=c, f=f, k=k, col=col: "Dark" if int(((cc - c).dot(f) + 0.3 * k) / (0.07 * k)) % 2 else col, hub)
    P.part(name, ball(tuple(c + f * 0.15 * k), (0.07 * k, 0.07 * k, 0.07 * k), 8, 4), "Dark", hub)
    for s in (1, -1):
        P.part(name, ball(tuple(c + f * 0.2 * k + side * s * 0.035 * k + Vector((0, 0, 0.02 * k))), (0.025 * k, 0.02 * k, 0.025 * k), 6, 3), "Glow", hub)
        w = ball((0, 0, 0), (0.12 * k, 0.05 * k, 0.012), 8, 3); xf(w, None, tuple(c + side * s * 0.11 * k + Vector((0, 0, 0.1 * k))))
        P.part(name, w, "Glass", hub, 0, False)
    if spear:
        P.part(name, pipe([c - f * 0.1 * k + side * 0.09 * k, c + f * 0.45 * k + side * 0.09 * k], [0.012 * k, 0.012 * k], 4), "Metal", hub)
        tip = c + f * 0.45 * k + side * 0.09 * k
        P.part(name, cone(tuple(tip), tuple(tip + f * 0.12 * k), 0.03 * k, 4), "Trim", hub, 0, False)


# ================================================================= 1. the queen bumblebee (round three)
def M_bee():
    """The queen of the meadow (2026-10-12, round three: "make them better"): a fuzzy golden queen with a fluffy ermine ruff, a breastplate
    of gold honeycomb cells glowing with honey, a golden face with long lashes, arched brows, rosy cheeks and a knowing smile, a tall
    jewelled crown with arches, an orb and a cross, four glassy wings veined in gold, a honey sceptre crowned with a glowing orb in one
    hand and a golden stinger lance levelled at the player in the other, a glowing stinger behind, and her worker bees circling her."""
    P = Boss("bee", {"Base": ((1.0, 0.78, 0.12), 0.35), "Belly": ((0.98, 0.58, 0.10), 0.25), "Accent": ((0.85, 0.08, 0.16), 0.8), "Trim": GOLD,
                     "Glass": WING, "Dark": INK, "Glow": ((1.0, 1.0, 0.95), 0.5), "Metal": ((0.97, 0.96, 0.92), 0.5), "Lamp": ((1.0, 0.62, 0.10), 0.9)})
    band = lambda c, n: "Dark" if int((0.25 - c.y) / 0.3) % 2 else "Base"
    rings = [(-0.1, 0.32, 0.3, 0, 0.05), (-0.35, 0.56, 0.52, 0, 0.02), (-0.75, 0.66, 0.6, 0, -0.04), (-1.15, 0.58, 0.54, 0, -0.08), (-1.48, 0.38, 0.36, 0, -0.1), (-1.72, 0.12, 0.12, 0, -0.1)]
    P.obj("Abdomen", loft(rings, 22), band, 1)
    P.obj("Stinger", cone((0, -1.68, -0.1), (0, -2.15, -0.18), 0.08, 8), "Dark", 0, False)
    P.obj("StingerGlow", ball((0, -2.12, -0.17), (0.05, 0.05, 0.05), 6, 3), "Lamp")
    # the thorax and its honeycomb breastplate
    T0, TR = Vector((0, 0.15, 0.05)), Vector((0.52, 0.48, 0.48))
    P.obj("Thorax", ball(tuple(T0), tuple(TR), 18, 9), "Belly", 1)
    for row in range(5):
        z = T0.z - 0.05 - row * 0.105
        for col in range(-4, 5):
            x = (col + 0.5 * (row % 2)) * 0.122
            q = (x / TR.x) ** 2 + ((z - T0.z) / TR.z) ** 2
            if q > 0.86: continue
            y = T0.y + TR.y * math.sqrt(1 - q)
            nrm = Vector((x / TR.x ** 2, (y - T0.y) / TR.y ** 2, (z - T0.z) / TR.z ** 2))
            if nrm.normalized().y < 0.25: continue
            hexplate(P, Vector((x, y, z)) + nrm.normalized() * 0.01, nrm, 0.062)
    # the fluffy ermine ruff round her neck
    for k in range(20):
        a = 2 * math.pi * k / 20
        b = Vector((math.sin(a) * 0.4, 0.52 + math.cos(a) * 0.05, 0.12 + math.cos(a) * 0.36))
        d = Vector((math.sin(a), 0.35, math.cos(a))).normalized()
        P.obj("Ruff", cone(tuple(b), tuple(b + d * 0.2), 0.11, 5), lambda c, n, k=k: "Dark" if k % 5 == 0 else "Metal", 0)
    # the head: a golden face, a dark crown of fuzz behind
    HC = Vector((0, 0.8, 0.2))
    P.obj("Head", ball(tuple(HC), (0.4, 0.34, 0.36), 18, 9), lambda c, n: "Dark" if n.y < -0.15 else "Base", 1)
    for s in (1, -1):
        cute_eyes(P, (s * 0.17, 1.02, 0.27), 0.15, s, white="Glass", pupil="Dark", shine="Glow")
        for k in range(3):   # long lashes
            b = Vector((s * (0.1 + 0.07 * k), 1.06, 0.42 - 0.02 * k))
            P.obj("Lash", cone(tuple(b), tuple(b + Vector((s * (0.04 + 0.04 * k), 0.04, 0.1 - 0.02 * k))), 0.018, 4), "Dark", 0, False)
        P.obj("Brow", bar((s * 0.05, 1.08, 0.5), (s * 0.3, 1.0, 0.52), 0.035, 0.03), "Dark")
        P.obj("Cheek", ball((s * 0.25, 1.07, 0.1), (0.08, 0.03, 0.05), 8, 4), "Accent")
        ant = bez((s * 0.1, 0.95, 0.5), (s * 0.18, 1.1, 0.8), (s * 0.4, 1.18, 0.92), (s * 0.52, 1.25, 0.86), 7)
        P.obj("Antenna", pipe(ant, [0.03] * 7 + [0.025], 6), "Dark")
        P.obj("AntennaTip", ball(tuple(ant[-1]), (0.065, 0.065, 0.065), 8, 4), "Lamp")
        for k in range(3):   # six legs; the front pair hold the sceptre and the lance
            hip = Vector((s * 0.3, 0.3 - 0.2 * k, -0.25)); knee = Vector((s * 0.55, 0.38 - 0.25 * k, -0.45)); foot = Vector((s * 0.45, 0.5 - 0.3 * k, -0.72))
            if k == 0: foot = Vector((s * 0.64, 0.8, -0.25))
            P.obj("Leg", pipe([hip, knee, foot], [0.05, 0.045, 0.035], 6), "Dark")
        # four glassy wings veined in gold, glowing at the tips
        name = "FlapR" if s > 0 else "FlapL"
        hub = (s * 0.3, 0.2, 0.55)
        wp = lambda c, n: "Trim" if abs(n.z) < 0.3 else "Glass"
        for root, L, W, yaw, lift in (((s * 0.3, 0.2, 0.55), 1.7, 0.68, 18, 24), ((s * 0.3, 0.05, 0.5), 1.15, 0.48, 48, 14)):
            P.part(name, ewing(root, L, W, yaw, lift, s), wp, hub, 0)
            veins(P, name, hub, root, L, W, yaw, lift, s)
            P.part(name, ball(tuple(wpt(root, yaw, lift, s, L * 0.9, 0.0, 0.03)), (0.05, 0.05, 0.03), 6, 3), "Lamp", hub)
    P.obj("Smile", pipe(bez((-0.13, 1.12, 0.09), (-0.05, 1.15, 0.03), (0.06, 1.15, 0.03), (0.14, 1.11, 0.1), 6), [0.02] * 7, 5), "Dark")
    # the tall crown: a band of rubies, points, two arches, an orb and a cross; a great sapphire in front
    cc = Vector((0, 0.76, 0.5))
    P.obj("Crown", lathe([(0.24, 0.0), (0.28, 0.2), (0.26, 0.21), (0.22, 0.02)], 18, "z", tuple(cc)), "Trim")
    for k in range(8):
        a = 2 * math.pi * k / 8
        b = cc + Vector((math.sin(a) * 0.27, math.cos(a) * 0.27, 0.19))
        P.obj("CrownSpike", cone(tuple(b), tuple(b + Vector((math.sin(a) * 0.04, math.cos(a) * 0.04, 0.2))), 0.055, 5), "Trim", 0, False)
        P.obj("CrownBall", ball(tuple(b + Vector((math.sin(a) * 0.04, math.cos(a) * 0.04, 0.22))), (0.035, 0.035, 0.035), 6, 3), "Metal")
        P.obj("Ruby", ball(tuple(cc + Vector((math.sin(a + 0.39) * 0.275, math.cos(a + 0.39) * 0.275, 0.1))), (0.045, 0.03, 0.045), 6, 3), "Accent")
    for a in (0.0, math.pi / 2):
        arc = [cc + Vector((math.sin(a) * math.cos(t) * 0.26, math.cos(a) * math.cos(t) * 0.26, 0.2 + math.sin(t) * 0.26)) for t in [math.pi * i / 10 for i in range(11)]]
        P.obj("CrownArch", pipe(arc, [0.025] * 11, 5), "Trim")
    P.obj("CrownOrb", ball(tuple(cc + Vector((0, 0, 0.5))), (0.07, 0.07, 0.07), 10, 5), "Trim")
    P.obj("CrownCross", bar(cc + Vector((0, 0, 0.55)), cc + Vector((0, 0, 0.72)), 0.035, 0.035), "Trim")
    P.obj("CrownCross", bar(cc + Vector((-0.06, 0, 0.66)), cc + Vector((0.06, 0, 0.66)), 0.035, 0.035), "Trim")
    P.obj("Sapphire", ball(tuple(cc + Vector((0, 0.29, 0.1))), (0.08, 0.04, 0.09), 10, 5), "Glow")
    # the honey sceptre in her right hand, crowned with a glowing orb
    P.obj("Staff", pipe([(0.64, 0.8, -0.6), (0.68, 0.82, 0.45)], [0.035, 0.035], 6), "Trim")
    P.obj("Dipper", lathe([(0.0, 0.3), (0.1, 0.32), (0.14, 0.4), (0.1, 0.48), (0.14, 0.56), (0.1, 0.64), (0.0, 0.67)], 12, "z", (0.68, 0.82, 0)), "Lamp")
    P.obj("SceptreCup", lathe([(0.0, 0.66), (0.12, 0.7), (0.1, 0.76)], 10, "z", (0.68, 0.82, 0)), "Trim")
    P.obj("SceptreOrb", ball((0.68, 0.82, 0.86), (0.11, 0.11, 0.11), 12, 6), "Lamp")
    for k in range(5): P.obj("Drip", ball((0.68 + 0.09 * math.cos(k * 1.7), 0.82 + 0.09 * math.sin(k * 1.7), 0.26 - 0.07 * k), (0.035, 0.035, 0.05), 6, 3), "Lamp")
    # the golden stinger lance in her left hand, levelled at the player
    g = Vector((-0.64, 0.8, -0.25)); d = Vector((-0.05, 1.0, 0.2)).normalized()
    P.obj("Lance", pipe([g - d * 0.35, g, g + d * 1.25], [0.05, 0.06, 0.0], 8), lambda c, n: "Dark" if int(c.y * 6) % 2 else "Trim")
    P.obj("Vamplate", cone(tuple(g + d * 0.12), tuple(g - d * 0.12), 0.17, 12), "Trim", 0, False)
    P.obj("LanceGem", ball(tuple(g + d * 0.16), (0.05, 0.05, 0.05), 6, 3), "Accent")
    tip = g + d * 1.25
    # her workers circling her, honey drops between them
    for k in range(7):
        a = 2 * math.pi * k / 7
        c = Vector((math.sin(a) * 1.95, -0.3 + math.cos(a) * 1.75, 0.35 + 0.3 * math.sin(a * 2)))
        mini_bee(P, "SpinWorkers", c, (math.cos(a), -math.sin(a), 0), (0, -0.3, 0.35), 1.1, spear=False)
        a2 = a + math.pi / 7
        P.part("SpinWorkers", ball((math.sin(a2) * 1.95, -0.3 + math.cos(a2) * 1.75, 0.3 + 0.3 * math.sin(a2 * 2)), (0.05, 0.05, 0.07), 6, 3), "Lamp", (0, -0.3, 0.35))
    P.part("Muzzle", ball(tuple(tip), (0.06, 0.06, 0.06), 8, 4), "Glow", tuple(tip))
    return P


# ================================================================= 2. the giant ladybug (round three: a knight)
def M_ladybug():
    """The ladybug knight (2026-10-12, round three: "make them better"): a great glossy scarlet ladybug whose spotted wing cases, rimmed
    in gold, open into amber flying wings veined with light; a silver knight's helm with a stern brow guard and a red plume over big brave
    eyes and a determined grin; a striped tournament lance couched at the player, a round spotted shield with a gold sun boss, and daisies
    circling him."""
    P = Boss("ladybug", {"Base": ((0.90, 0.08, 0.06), 0.85), "Belly": ((0.97, 0.97, 0.95), 0.4), "Accent": ((1.0, 0.85, 0.3), 0.5), "Trim": GOLD,
                         "Glass": ((1.0, 0.82, 0.45), 0.9), "Dark": INK, "Glow": ((1.0, 1.0, 0.95), 0.5), "Metal": ((0.82, 0.84, 0.9), 0.85), "Lamp": ((1.0, 0.75, 0.25), 0.8)})
    P.obj("Under", ball((0, -0.15, -0.05), (0.72, 1.0, 0.4), 18, 8), "Dark", 1)
    P.obj("Pronotum", ball((0, 0.7, 0.12), (0.6, 0.38, 0.34), 16, 8), lambda c, n: "Belly" if abs(c.x) > 0.3 and n.z > -0.2 else "Dark", 1)
    HC = Vector((0, 1.02, 0.02))
    P.obj("Head", ball(tuple(HC), (0.4, 0.32, 0.31), 16, 8), "Dark", 1)
    # the knight's helm: a silver dome, a gold crest ridge, a red plume, a brow guard
    P.obj("Helm", dome(HC + Vector((0, -0.04, 0.0)), (0.43, 0.35, 0.36), 0.17, 18, 10, 0.03), "Metal", 0)
    P.obj("HelmRidge", pipe([HC + Vector((0, 0.3, 0.3)), HC + Vector((0, 0.1, 0.4)), HC + Vector((0, -0.15, 0.38)), HC + Vector((0, -0.32, 0.22))], [0.035] * 4, 6), "Trim")
    for k in range(9):   # the plume streams back over the helm
        t = k / 8.0
        b = HC + Vector((0, 0.15 - 0.45 * t, 0.42 - 0.12 * t))
        P.obj("Plume", cone(tuple(b), tuple(b + Vector(((k % 3 - 1) * 0.08, -0.45, 0.42 - 0.15 * t))), 0.1, 6), "Base", 0, False)
    for s in (1, -1):
        cute_eyes(P, (s * 0.18, 1.24, 0.06), 0.16, s, white="Belly")
        P.obj("BrowGuard", bar((s * 0.02, 1.36, 0.28), (s * 0.36, 1.27, 0.2), 0.045, 0.04), "Trim")
        ant = bez((s * 0.12, 1.15, 0.33), (s * 0.22, 1.32, 0.62), (s * 0.42, 1.42, 0.66), (s * 0.45, 1.33, 0.52), 7)
        P.obj("Antenna", pipe(ant, [0.025] * 8, 6), "Dark")
        P.obj("AntennaTip", ball(tuple(ant[-1]), (0.05, 0.05, 0.05), 8, 4), "Trim")
        for k in range(3):
            hip = Vector((s * 0.45, 0.45 - 0.4 * k, -0.25)); knee = Vector((s * 0.75, 0.5 - 0.45 * k, -0.35)); foot = Vector((s * 0.7, 0.6 - 0.5 * k, -0.6))
            if k == 0: foot = Vector((s * 0.78, 0.9, -0.3))
            P.obj("Leg", pipe([hip, knee, foot], [0.05, 0.045, 0.035], 6), "Dark")
        # the wing case raised on its hinge, rimmed in gold, and the amber flying wing under it
        name = "FlapR" if s > 0 else "FlapL"
        hinge = Vector((s * 0.06, 0.45, 0.35))
        ctr = Vector((s * 0.4, -0.25, 0.12)); rad = Vector((0.46, 0.95, 0.5))
        rot = R("Y", -s * 28) @ R("X", 12)
        T = lambda p, rot=rot, hinge=hinge: rot @ (Vector(p) - hinge) + hinge
        bm = ball(tuple(ctr), tuple(rad), 24, 12)
        for v in bm.verts:
            if v.co.z < ctr.z: v.co.z = ctr.z + (v.co.z - ctr.z) * 0.25
            v.co = T(v.co)
        P.part(name, bm, "Base", tuple(hinge), 1)
        rim = [T(ctr + Vector((math.cos(2 * math.pi * i / 28) * rad.x * 1.0, math.sin(2 * math.pi * i / 28) * rad.y * 1.0, 0.0))) for i in range(29)]
        P.part(name, pipe(rim, [0.035] * 29, 6, False), "Trim", tuple(hinge))
        dirs = [(0.2, 0.75, 0.6), (0.55, 0.2, 0.75), (0.3, -0.3, 0.9), (0.75, -0.45, 0.45), (0.25, -0.8, 0.5), (0.85, 0.3, 0.3), (0.6, -0.75, 0.35)]
        for k, d in enumerate(dirs):
            d = Vector((s * d[0], d[1], d[2])).normalized()
            on = ctr + Vector((d.x * rad.x, d.y * rad.y, d.z * rad.z))
            nrm = (rot @ Vector((d.x / rad.x, d.y / rad.y, d.z / rad.z))).normalized()
            r = 0.15 if k % 2 == 0 else 0.11
            sp = ball((0, 0, 0), (r, r, 0.035), 14, 5)
            xf(sp, nrm.to_track_quat("Z", "Y").to_matrix(), tuple(T(on) + nrm * 0.005))
            P.part(name, sp, "Dark", tuple(hinge), 0)
        root = (s * 0.25, 0.25, 0.25)
        P.part(name, ewing(root, 1.85, 0.74, 30, 6, s), lambda c, n: "Trim" if abs(n.z) < 0.3 else "Glass", tuple(hinge), 0)
        veins(P, name, tuple(hinge), root, 1.85, 0.74, 30, 6, s, "Lamp", 0.018)
    P.obj("Grin", pipe(bez((-0.19, 1.27, -0.13), (-0.08, 1.33, -0.2), (0.08, 1.33, -0.2), (0.19, 1.27, -0.13), 6), [0.025] * 7, 5), "Belly")
    for x in (-0.07, 0.0, 0.07): P.obj("Tooth", ball((x, 1.32, -0.17), (0.03, 0.012, 0.025), 6, 3), "Belly")
    # the tournament lance in his right claw, striped red and gold
    g = Vector((0.8, 0.9, -0.3)); d = Vector((0.0, 1.0, 0.12)).normalized()
    P.obj("Lance", pipe([g - d * 0.55, g] + [g + d * (0.25 + 1.35 * i / 10) for i in range(11)], [0.06, 0.07] + [0.11 * (1 - i / 10) for i in range(11)], 10), lambda c, n, g=g: "Base" if int((c - g).length * 6) % 2 else "Trim")
    P.obj("Vamplate", cone(tuple(g + d * 0.2), tuple(g - d * 0.1), 0.24, 14), "Metal", 0, False)
    tip = g + d * 1.6
    # the round shield on his left, red with black spots and a gold sun boss
    sc = Vector((-0.86, 0.98, -0.12))
    P.obj("Shield", lathe([(0.0, 0.06), (0.36, 0.03), (0.42, -0.01), (0.4, -0.04), (0.0, -0.05)], 26, "y", tuple(sc)), lambda c, n, sc=sc: "Trim" if (c - sc).length > 0.36 else "Base", 0)
    for k in range(6):
        a = 2 * math.pi * k / 6 + 0.3
        P.obj("ShieldSpot", ball(tuple(sc + Vector((math.cos(a) * 0.24, 0.05, math.sin(a) * 0.24))), (0.07, 0.02, 0.07), 10, 4), "Dark")
    P.obj("ShieldBoss", ball(tuple(sc + Vector((0, 0.07, 0))), (0.11, 0.05, 0.11), 12, 6), "Trim")
    for k in range(8):
        a = 2 * math.pi * k / 8
        P.obj("ShieldRay", cone(tuple(sc + Vector((math.cos(a) * 0.1, 0.07, math.sin(a) * 0.1))), tuple(sc + Vector((math.cos(a) * 0.18, 0.065, math.sin(a) * 0.18))), 0.03, 4), "Trim", 0, False)
    # daisies circling him
    for k in range(8):
        a = 2 * math.pi * k / 8
        c = Vector((math.sin(a) * 1.9, -0.1 + math.cos(a) * 1.75, 0.35 + 0.3 * math.sin(a * 2)))
        P.part("SpinDaisies", ball(tuple(c), (0.06, 0.06, 0.04), 8, 4), "Lamp", (0, -0.1, 0.35))
        for j in range(8):
            b = 2 * math.pi * j / 8
            P.part("SpinDaisies", ball(tuple(c + Vector((math.cos(b) * 0.11, math.sin(b) * 0.11, 0))), (0.06, 0.06, 0.02), 6, 3), "Belly", (0, -0.1, 0.35))
    P.part("Muzzle", ball(tuple(tip), (0.06, 0.06, 0.06), 8, 4), "Glow", tuple(tip))
    return P


# ================================================================= 3. the emerald dragonfly (round three)
def M_dragonfly():
    """The emerald dragonfly (2026-10-12, round three: "make them better"): a storm-dragonfly in emerald armour banded in gold, a horned
    crest, huge faceted turquoise eyes under fierce gold brows, golden mandibles round a glowing mouth, a long tail of jewelled segments
    ending in a glowing sting, four long iridescent wings veined in gold with a jewel at each tip, its claws gripping a crackling storm orb,
    and bolts of lightning circling it."""
    P = Boss("dragonfly", {"Base": ((0.08, 0.62, 0.38), 0.85), "Belly": ((0.12, 0.35, 0.65), 0.8), "Accent": ((0.0, 0.85, 0.85), 0.9), "Trim": GOLD,
                           "Glass": ((0.80, 0.95, 1.0), 0.9), "Dark": INK, "Glow": ((0.6, 1.0, 1.0), 0.5), "Metal": ((0.55, 0.30, 0.85), 0.9), "Lamp": ((0.75, 1.0, 0.35), 0.8)})
    # the armoured thorax: gold bands, a gem on the chest
    P.obj("Thorax", ball((0, 0.3, 0.05), (0.42, 0.58, 0.44), 16, 8), lambda c, n: "Trim" if (abs(c.x) < 0.06 and n.z > 0.5) or int((c.y + 2) * 5) % 3 == 0 else "Base", 1)
    P.obj("ChestPlate", ball((0, 0.72, -0.08), (0.3, 0.12, 0.26), 14, 7), "Trim", 1)
    P.obj("ChestGem", ball((0, 0.83, -0.06), (0.1, 0.05, 0.12), 10, 5), "Lamp")
    HC = Vector((0, 0.95, 0.12))
    P.obj("Head", ball(tuple(HC), (0.36, 0.26, 0.28), 14, 7), "Base", 1)
    for s in (1, -1):
        P.obj("Eye", ball((s * 0.26, 1.04, 0.25), (0.3, 0.27, 0.31), 16, 8), lambda c, n: "Belly" if n.z < -0.4 else "Accent", 1)
        P.obj("Pupil", ball((s * 0.25, 1.3, 0.22), (0.08, 0.03, 0.14), 10, 5), "Dark")
        P.obj("Glint", ball((s * 0.18, 1.29, 0.36), (0.04, 0.02, 0.04), 6, 3), "Glow")
        P.obj("Spark", ball((s * 0.3, 1.27, 0.4), (0.06, 0.025, 0.06), 6, 3), "Glow")
        P.obj("Brow", bar((s * 0.02, 1.24, 0.5), (s * 0.5, 1.14, 0.66), 0.09, 0.07), "Trim")
        P.obj("Horn", pipe(bez((s * 0.1, 0.9, 0.38), (s * 0.15, 0.8, 0.65), (s * 0.28, 0.6, 0.8), (s * 0.4, 0.45, 0.85), 5), [0.06, 0.05, 0.04, 0.03, 0.015, 0.0], 6), "Trim")
        P.obj("Mandible", pipe(bez((s * 0.12, 1.12, -0.05), (s * 0.18, 1.25, -0.08), (s * 0.12, 1.33, -0.12), (s * 0.03, 1.33, -0.14), 4), [0.04, 0.035, 0.025, 0.0, 0.0], 5), "Trim")
        for k in range(3):   # legs gripping the storm orb under its chest
            hip = Vector((s * 0.15, 0.55 - 0.18 * k, -0.25)); knee = Vector((s * 0.4, 0.62 - 0.2 * k, -0.45)); foot = Vector((s * 0.12, 0.6 - 0.05 * k, -0.78))
            P.obj("Leg", pipe([hip, knee, foot], [0.035, 0.03, 0.02], 5), "Dark")
            P.obj("Claw", cone(tuple(foot), tuple(foot + Vector((-s * 0.06, 0.03, -0.06))), 0.02, 4), "Trim", 0, False)
        # four long wings: iridescent at the root, glass beyond, gold veins, a jewel at each tip; dark tips
        name = "FlapR" if s > 0 else "FlapL"
        hub = (s * 0.18, 0.3, 0.32)
        for root, L, W, yaw, lift in (((s * 0.22, 0.48, 0.36), 2.3, 0.6, -4, 10), ((s * 0.22, 0.12, 0.34), 2.15, 0.66, 14, 7)):
            def wp(c, n, root=root, L=L):
                d = (c - Vector(root)).length / L
                if abs(n.z) < 0.3: return "Trim"
                if d > 0.93: return "Dark"
                if d < 0.3: return "Accent"
                if d < 0.42: return "Metal"
                return "Glass"
            P.part(name, ewing(root, L, W, yaw, lift, s, 0.03, 24), wp, hub, 0)
            veins(P, name, hub, root, L, W, yaw, lift, s)
            P.part(name, ball(tuple(wpt(root, yaw, lift, s, L * 0.82, W * 0.22, 0.03)), (0.07, 0.04, 0.035), 8, 4), "Lamp", hub)
    P.obj("Mouth", ball((0, 1.2, -0.06), (0.1, 0.05, 0.06), 10, 5), "Glow")
    # the storm orb in its claws
    P.obj("StormOrb", ball((0, 0.62, -0.9), (0.2, 0.2, 0.2), 14, 7), "Glass")
    P.obj("StormCore", ball((0, 0.62, -0.9), (0.11, 0.11, 0.11), 10, 5), "Glow")
    for k in range(4):
        a = 2 * math.pi * k / 4 + 0.4
        P.obj("Crackle", pipe(bolt_pts((0, 0.62, -0.9), (math.cos(a) * 0.32, 0.62 + math.sin(a) * 0.2, -0.9 + 0.12 * (k % 2)), 3, 0.05), [0.02, 0.018, 0.014, 0.0], 4), "Lamp")
    # the long tail of jewelled segments, a glowing sting at the end
    N = 10
    for k in range(N):
        y0 = -0.15 - k * 0.24; y1 = y0 - 0.24
        r0 = 0.15 - 0.006 * k; r1 = r0 - 0.012
        z0 = 0.02 + 0.012 * k; z1 = z0 + 0.012
        P.obj("Tail", loft([(y0, r0, r0, 0, z0), (y0 - 0.04, r0 * 1.1, r0 * 1.1, 0, z0), (y1 + 0.03, r1 * 0.9, r1 * 0.9, 0, z1), (y1, r1 * 0.85, r1 * 0.85, 0, z1)], 12),
              lambda c, n, y0=y0: "Trim" if c.y > y0 - 0.06 else ("Belly" if n.z < -0.3 else "Base"), 0)
        P.obj("TailGem", ball((0, y0 - 0.12, z0 + r0 * 0.95), (0.04, 0.05, 0.03), 6, 3), "Lamp" if k % 2 else "Glow")
    tip = Vector((0, -0.15 - N * 0.24, 0.02 + 0.012 * N))
    P.obj("Sting", cone(tuple(tip), tuple(tip + Vector((0, -0.35, 0.12))), 0.06, 6), "Lamp", 0, False)
    for s in (1, -1): P.obj("Clasper", cone(tuple(tip), tuple(tip + Vector((s * 0.12, -0.2, 0.04))), 0.035, 5), "Trim", 0, False)
    # lightning circling it
    for k in range(6):
        a = 2 * math.pi * k / 6
        c = Vector((math.sin(a) * 2.0, -0.6 + math.cos(a) * 1.9, 0.3 + 0.25 * math.sin(a * 2)))
        P.part("SpinBolts", pipe(bolt_pts(c + Vector((0, 0, 0.32)), c + Vector((0, 0, -0.32)), 4, 0.1), [0.035, 0.035, 0.03, 0.025, 0.0], 4), "Lamp", (0, -0.6, 0.3))
    P.part("Muzzle", ball((0, 1.22, -0.06), (0.06, 0.03, 0.05), 8, 4), "Glow", (0, 1.22, -0.06))
    return P


# ================================================================= 4. the sunflower titan
def M_sunflower():
    """A giant sunflower come alive, flying in its terracotta pot: a smiling face on the seed disc, two rings of golden petals turning slowly
    face-on, leaf arms waving, a curling stem, a ladybug on a leaf."""
    P = Boss("sunflower", {"Base": ((0.28, 0.66, 0.18), 0.45), "Belly": ((1.0, 0.56, 0.08), 0.45), "Accent": ((0.78, 0.36, 0.18), 0.3), "Trim": ((1.0, 0.82, 0.10), 0.5),
                           "Glass": ((0.98, 0.98, 0.95), 0.7), "Dark": ((0.14, 0.07, 0.03), 0.4), "Glow": ((1.0, 1.0, 0.9), 0.5),
                           "Metal": ((0.40, 0.22, 0.07), 0.5), "Lamp": ((1.0, 0.85, 0.35), 0.8)})
    FC = Vector((0, 0.25, 1.05))                          # the middle of the face
    # the face: a seed disc facing the player
    def seeds(c, n):
        d = c - FC; r = math.hypot(d.x, d.z)
        if n.y < 0.2: return "Base"
        a = math.atan2(d.z, d.x)
        return "Metal" if ((a / (2 * math.pi) * 13 + r * 9) % 1.0 < 0.5) ^ ((a / (2 * math.pi) * -8 + r * 9) % 1.0 < 0.5) else "Dark"
    P.obj("Disc", lathe([(0.0, 0.16), (0.42, 0.14), (0.66, 0.06), (0.72, -0.02), (0.6, -0.1), (0.0, -0.16)], 28, "y", tuple(FC)), seeds, 0)
    for s in (1, -1):
        cute_eyes(P, (FC.x + s * 0.24, FC.y + 0.14, FC.z + 0.12), 0.13, s, white="Glass")
        P.obj("Cheek", ball((FC.x + s * 0.4, FC.y + 0.12, FC.z - 0.08), (0.08, 0.03, 0.06), 8, 4), "Belly")
    P.obj("Smile", pipe(bez((-0.24, FC.y + 0.16, FC.z - 0.12), (-0.1, FC.y + 0.19, FC.z - 0.3), (0.1, FC.y + 0.19, FC.z - 0.3), (0.24, FC.y + 0.16, FC.z - 0.12), 8), [0.035] * 9, 6), "Accent")
    # the petals turn face-on about the nose axis
    for ring, (n, rr, L, W, col, dy, off) in enumerate(((18, 0.7, 0.62, 0.3, "Trim", 0.0, 0.0), (18, 0.66, 0.55, 0.28, "Belly", -0.06, 0.5))):
        for k in range(n):
            a = 2 * math.pi * (k + off) / n
            bm = ball((0, 0, L * 0.5), (W * 0.5, 0.04, L * 0.5), 10, 5)
            for v in bm.verts:   # pointed tips
                t = v.co.z / L; v.co.x *= 0.45 + 0.75 * math.sin(math.pi * min(max(t, 0.0), 1.0)) ** 0.7
                v.co.y += 0.08 * t * t * (1 if ring == 0 else -1)
            xf(bm, R("Y", math.degrees(a)), (FC.x + math.sin(a) * rr, FC.y + dy, FC.z + math.cos(a) * rr))
            P.part("RollPetals", bm, col, tuple(FC), 0)
    # the stem, the leaf arms and the pot
    stem = bez((0, FC.y - 0.15, FC.z - 0.2), (0, -0.25, 0.45), (0, 0.15, -0.15), (0, 0.0, -0.55), 8)
    P.obj("Stem", pipe(stem, [0.13, 0.12, 0.12, 0.11, 0.11, 0.11, 0.12, 0.13, 0.14], 10), "Base")
    for s in (1, -1):
        hub = Vector((s * 0.08, 0.05, -0.05))
        name = "SwayR" if s > 0 else "SwayL"
        P.part(name, leaf(hub, 1.45, 0.7, 25 if s > 0 else 155, 18), "Base", tuple(hub), 1)
    P.obj("Pot", lathe([(0.0, -1.35), (0.36, -1.35), (0.52, -0.75), (0.62, -0.72), (0.64, -0.55), (0.56, -0.52), (0.5, -0.56), (0.0, -0.56)], 22, "z"),
          lambda c, n: "Dark" if c.z > -0.58 and n.z > 0.5 else "Accent", 0)
    for k in range(6):
        a = 2 * math.pi * k / 6 + 0.3
        P.obj("Pebble", ball((math.cos(a) * 0.3, math.sin(a) * 0.3, -0.54), (0.07, 0.06, 0.04), 6, 3), "Metal")
    # a little ladybug riding on the right leaf
    lb = Vector((0.75, 0.42, 0.32))
    P.obj("Bug", ball(tuple(lb), (0.1, 0.12, 0.07), 10, 5), lambda c, n: "Dark" if abs(c.x - lb.x) < 0.012 or (c - lb).length < 0.05 else "Accent")
    P.part("Muzzle", ball((0, FC.y + 0.17, FC.z - 0.24), (0.04, 0.02, 0.03), 8, 4), "Accent", (0, FC.y + 0.17, FC.z - 0.24))
    return P


# ================================================================= 5. the windmill hill
def M_windmill():
    """The last boss: a whole hill of the meadow flown up into the sky - a grassy island on an earthy root, a white windmill with a red cap
    whose four sails turn face-on, a cottage with glowing windows, a pond, round trees, flowers everywhere, and bees circling round it."""
    P = Boss("windmill", {"Base": ((0.36, 0.72, 0.22), 0.3), "Belly": ((0.97, 0.94, 0.86), 0.35), "Accent": ((0.84, 0.18, 0.12), 0.55), "Trim": ((1.0, 0.82, 0.18), 0.6),
                          "Glass": ((0.32, 0.65, 0.98), 0.85), "Dark": ((0.36, 0.22, 0.10), 0.3), "Glow": ((1.0, 1.0, 0.9), 0.5),
                          "Metal": ((0.60, 0.58, 0.54), 0.25), "Lamp": ((1.0, 0.82, 0.45), 0.8)})
    rng = random.Random(4)
    P.obj("Ground", lathe([(0.0, 0.12), (1.7, 0.12), (1.85, 0.06), (1.9, -0.02), (1.85, -0.1)], 30, "z"), lambda c, n: "Base" if n.z > 0.3 else "Dark")
    root = []
    for k in range(40):
        a = rng.uniform(0, 2 * math.pi); r = rng.uniform(0.2, 1.85)
        root.append((math.sin(a) * r, math.cos(a) * r, -0.1 - (1.85 - r) * rng.uniform(0.45, 0.75)))
    root += [(math.sin(2 * math.pi * k / 18) * 1.85, math.cos(2 * math.pi * k / 18) * 1.85, -0.08) for k in range(18)] + [(0, 0, -1.35)]
    P.obj("Root", hull(root), lambda c, n: "Metal" if speckle(c, 1.5) < 0.3 else "Dark", 0, False)
    # the windmill
    wc = Vector((-0.35, -0.35, 0.12))
    P.obj("Tower", lathe([(0.55, 0.0), (0.5, 0.6), (0.4, 1.6), (0.36, 1.75), (0.0, 1.75)], 8, "z", tuple(wc)),
          lambda c, n: "Dark" if 0.62 < c.z - wc.z < 0.72 else "Belly", 0, False)
    P.obj("Gallery", lathe([(0.62, 0.62), (0.62, 0.7), (0.0, 0.7)], 16, "z", tuple(wc)), "Dark", 0, False)
    P.obj("Cap", lathe([(0.44, 1.72), (0.42, 1.95), (0.25, 2.2), (0.0, 2.32)], 16, "z", tuple(wc)), "Accent")
    P.obj("Door", box((wc.x, wc.y + 0.52, wc.z + 0.2), (0.22, 0.05, 0.38)), "Dark", 0, False)
    for z in (0.95, 1.35): P.obj("Window", box((wc.x, wc.y + 0.49 - 0.1 * (z - 0.6), wc.z + z), (0.14, 0.06, 0.16)), "Lamp", 0, False)
    hub = Vector((wc.x, wc.y + 0.55, wc.z + 1.85))
    P.obj("Axle", pipe([hub + Vector((0, -0.2, 0)), hub + Vector((0, 0.08, 0))], [0.07, 0.07], 8), "Dark")
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        d = Vector((math.cos(a), 0, math.sin(a))); side = Vector((-d.z, 0, d.x))
        P.part("RollSails", pipe([hub, hub + d * 1.25], [0.035, 0.03], 5), "Dark", tuple(hub), 0, False)
        q = [hub + d * 0.3 + side * 0.04, hub + d * 1.22 + side * 0.04, hub + d * 1.22 + side * 0.32, hub + d * 0.3 + side * 0.28]
        P.part("RollSails", sheet([[tuple(p) for p in q]], 0.02), "Belly", tuple(hub), 0, False)   # the canvas
        for t in (0.45, 0.7, 0.95):   # the lattice
            P.part("RollSails", pipe([hub + d * (t + 0.08) + side * 0.03, hub + d * (t + 0.08) + side * 0.33], [0.015, 0.015], 4), "Dark", tuple(hub), 0, False)
        P.part("RollSails", pipe([hub + d * 1.22 + side * 0.34, hub + d * 0.3 + side * 0.32], [0.015, 0.015], 4), "Dark", tuple(hub), 0, False)
    # the cottage
    cc = Vector((0.85, -0.2, 0.12))
    P.obj("Cottage", box((cc.x, cc.y, cc.z + 0.25), (0.6, 0.5, 0.5)), "Belly", 0, False)
    P.obj("CottageRoof", hull([(cc.x - 0.36, cc.y - 0.32, cc.z + 0.48), (cc.x + 0.36, cc.y - 0.32, cc.z + 0.48), (cc.x - 0.36, cc.y + 0.32, cc.z + 0.48), (cc.x + 0.36, cc.y + 0.32, cc.z + 0.48),
                                (cc.x - 0.36, cc.y, cc.z + 0.8), (cc.x + 0.36, cc.y, cc.z + 0.8)]), "Accent", 0, False)
    P.obj("Chimney", box((cc.x + 0.18, cc.y - 0.1, cc.z + 0.8), (0.1, 0.1, 0.25)), "Metal", 0, False)
    P.obj("CDoor", box((cc.x, cc.y + 0.26, cc.z + 0.16), (0.14, 0.03, 0.26)), "Dark", 0, False)
    for s in (1, -1): P.obj("CWin", box((cc.x + s * 0.2, cc.y + 0.26, cc.z + 0.3), (0.1, 0.03, 0.1)), "Lamp", 0, False)
    # the pond, trees, flowers, a fence
    P.obj("Pond", ball((0.55, 0.85, 0.13), (0.42, 0.3, 0.03), 18, 4), "Glass")
    for (x, y, h) in ((-1.25, 0.35, 0.6), (1.3, 0.55, 0.45), (-0.95, -1.15, 0.7), (1.1, -1.05, 0.55)):
        P.obj("Trunk", pipe([(x, y, 0.1), (x, y, 0.1 + h)], [0.07, 0.05], 6), "Dark")
        P.obj("Crown", ball((x, y, 0.15 + h + 0.25), (0.34, 0.34, 0.36), 12, 6), "Base", 1)
        P.obj("Apple", ball((x + 0.2, y + 0.22, 0.15 + h + 0.25), (0.05, 0.05, 0.05), 6, 3), "Accent")
    for k in range(60):
        a = rng.uniform(0, 2 * math.pi); r = rng.uniform(0.3, 1.75)
        x, y = math.sin(a) * r, math.cos(a) * r
        if (Vector((x, y)) - wc.xy).length < 0.7 or (Vector((x, y)) - cc.xy).length < 0.5 or (Vector((x, y)) - Vector((0.55, 0.85))).length < 0.5: continue
        P.obj("Flower", ball((x, y, 0.17), (0.06, 0.06, 0.04), 6, 3), ("Trim", "Accent", "Belly", "Glass")[k % 4])
    for k in range(9):   # a little fence along the front edge
        a = math.radians(-50 + k * 12.5)
        p = Vector((math.sin(a) * 1.6, math.cos(a) * 1.6, 0.12))
        P.obj("Post", box((p.x, p.y, p.z + 0.12), (0.05, 0.05, 0.24)), "Belly", 0, False)
    P.obj("Rail", pipe([(math.sin(math.radians(-50 + t * 2.5)) * 1.6, math.cos(math.radians(-50 + t * 2.5)) * 1.6, 0.3) for t in range(41)], [0.022] * 41, 4), "Belly")
    # bees circling
    for k in range(8):
        a = 2 * math.pi * k / 8
        b = Vector((math.cos(a) * 2.3, math.sin(a) * 2.2, 0.9 + 0.35 * math.sin(a * 2)))
        P.part("SpinBees", ball(tuple(b), (0.09, 0.13, 0.09), 8, 4), lambda c, n, b=b: "Dark" if int((c.y - b.y + 0.2) / 0.08) % 2 else "Trim", (0, 0, 0.9))
        for s in (1, -1): P.part("SpinBees", ball(tuple(b + Vector((s * 0.1, 0, 0.08))), (0.08, 0.04, 0.02), 6, 3), "Glass", (0, 0, 0.9))
    P.part("Muzzle", ball((wc.x, wc.y + 0.6, wc.z + 0.5), (0.07, 0.03, 0.07), 8, 4), "Lamp", (wc.x, wc.y + 0.6, wc.z + 0.5))
    return P


def speckle(c, k=1.0):
    v = math.sin(c.x * 12.9898 * k + c.y * 78.233 * k + c.z * 37.719 * k) * 43758.5453
    return v - math.floor(v)


# ================================================================= 2026-10-11 round two: the snail king (in place of windmill hill)
def lid(c, r, s, tilt=18):
    """a heavy upper eyelid: the top of a ball a little bigger than the eye, tipped forward - a proud, half-closed look."""
    bm = ball(tuple(c), (r * 1.08, r * 1.08, r * 1.08), 12, 8)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < c[2] + r * 0.42], context="VERTS")
    xf(bm, None, (-c[0], -c[1], -c[2])); xf(bm, R("X", -tilt) @ R("Y", s * 8)); xf(bm, None, tuple(c))
    bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=0.02)
    return bm

def M_snail():
    """The last boss: the snail king of the meadow - a great soft snail with a golden spiral shell banded in pearl, and on top of the
    shell his own little castle with red-roofed turrets, flags and glowing windows; a proud face with heavy-lidded eyes on tall stalks,
    rosy cheeks, a curling golden moustache and a smile, a jewelled crown between the stalks, a gold collar, and butterflies circling
    round him. The spiral faces the player, rising behind him like a golden shield. Round three (2026-10-12, "make them better"): a walled
    palace with a gate, banners and a golden spire, a red ermine-hemmed mantle, a monocle and bushy white brows, a taller crown with arches,
    a glowing slime trail, and five bee guards with spears circling him."""
    P = Boss("snail", {"Base": ((0.38, 0.72, 0.50), 0.45), "Belly": ((0.98, 0.97, 0.94), 0.4), "Accent": ((0.82, 0.10, 0.16), 0.55), "Trim": GOLD,
                       "Glass": ((0.20, 0.45, 0.98), 0.9), "Dark": INK, "Glow": ((1.0, 1.0, 0.95), 0.5),
                       "Metal": ((0.95, 0.93, 0.96), 0.85), "Lamp": ((1.0, 0.78, 0.35), 0.9)})
    # the soft body, long and low, rising into the neck and head
    P.obj("Foot", pipe([(0, -1.45, -0.75), (0, -1.1, -0.68), (0, -0.3, -0.62), (0, 0.5, -0.55), (0, 0.95, -0.3), (0, 1.15, 0.1)],
                       [0.04, 0.36, 0.56, 0.6, 0.58, 0.52], 18), lambda c, n: "Metal" if n.z < -0.6 else "Base", 1)
    P.obj("Head", ball((0, 1.2, 0.5), (0.72, 0.6, 0.66), 16, 8), "Base", 1)
    # the golden spiral shell, banded in pearl
    C = Vector((0, -0.55, 1.15)); R0, K = 1.25, 0.12
    pts, rad = [], []
    for i in range(70):
        t = i / 69.0 * 3.4 * math.pi; r = R0 * math.exp(-K * t); th = -math.pi / 2 + t
        pts.append(tuple(C + Vector((-math.cos(th) * r, 0, math.sin(th) * r)))); rad.append(0.0 if i == 69 else 0.5 * r / R0 * (1.0 if i < 64 else (69 - i) / 5.0))
    bm = pipe(pts, rad, 18)
    for v in bm.verts: v.co.y = C.y + (v.co.y - C.y) * 1.25
    def band(c, n):
        d = c - C; a = math.atan2(d.z, -d.x)
        return "Metal" if math.sin(a * 7.0) > 0.72 else "Trim"
    P.obj("Shell", bm, band, 1)
    for k in range(5):
        t = (k + 0.5) / 5.0 * 3.0 * math.pi; r = R0 * math.exp(-K * t); th = -math.pi / 2 + t
        q = C + Vector((-math.cos(th) * r, 0.42 * r / R0 + 0.02, math.sin(th) * r))
        P.obj("ShellGem", ball(tuple(q), (0.09 * r / R0 + 0.03, 0.05, 0.09 * r / R0 + 0.03), 10, 5), "Glass" if k % 2 else "Accent")
    # his castle on top of the shell
    rt = R0 * math.exp(-K * math.pi); k0 = Vector((0, C.y - 0.1, C.z + rt + 0.4 * rt / R0 * 0.8))
    P.obj("Keep", box(tuple(k0 + Vector((0, 0, 0.3))), (0.5, 0.5, 0.6)), lambda c, n: "Lamp" if abs(n.y) > 0.5 and abs(c.x) < 0.1 and c.z > k0.z + 0.35 else "Belly", 0, False)
    P.obj("KeepRoof", cone(tuple(k0 + Vector((0, 0, 0.6))), tuple(k0 + Vector((0, 0, 1.15))), 0.4, 4), "Accent", 0, False)
    P.obj("KeepFlagPole", pipe([tuple(k0 + Vector((0, 0, 1.1))), tuple(k0 + Vector((0, 0, 1.45)))], [0.015, 0.015], 4), "Dark")
    P.part("Cloth", sheet([[tuple(k0 + Vector((0, 0, 1.45))), tuple(k0 + Vector((0, 0, 1.31))), tuple(k0 + Vector((0, -0.28, 1.38)))]], 0.02), "Glass", (0, 0, 0), 0, False)
    for sx in (1, -1):
        for sy in (1, -1):
            tc = k0 + Vector((sx * 0.36, sy * 0.3, 0))
            P.obj("Turret", lathe([(0.15, 0.0), (0.15, 0.5), (0.18, 0.52), (0.18, 0.6), (0.0, 0.6)], 12, "z", tuple(tc)), lambda c, n: "Lamp" if n.y > 0.6 and 0.25 < c.z - k0.z < 0.36 else "Belly", 0, False)
            P.obj("TurretRoof", cone(tuple(tc + Vector((0, 0, 0.6))), tuple(tc + Vector((0, 0, 0.95))), 0.21, 12), "Accent", 0, False)
            P.obj("TurretTip", ball(tuple(tc + Vector((0, 0, 0.97))), (0.03, 0.03, 0.03), 6, 3), "Trim")
    # the face: heavy-lidded eyes on tall stalks, rosy cheeks, a golden moustache, a smile
    for s in (1, -1):
        top = Vector((s * 0.45, 1.55, 1.62))
        P.obj("Stalk", pipe([(s * 0.22, 1.3, 0.95), (s * 0.34, 1.45, 1.3), tuple(top - Vector((0, 0, 0.16)))], [0.11, 0.09, 0.085], 10), "Base", 1)
        P.obj("EyeWhite", ball(tuple(top), (0.27, 0.24, 0.27), 14, 7), "Belly", 1)
        P.obj("Pupil", ball(tuple(top + Vector((-s * 0.03, 0.2, -0.06))), (0.15, 0.07, 0.16), 10, 5), "Dark")
        P.obj("Spark", ball(tuple(top + Vector((s * 0.02, 0.27, 0.0))), (0.05, 0.02, 0.05), 6, 3), "Glow")
        P.obj("Lid", lid(top, 0.27, s, 12), "Base", 0, True)
        P.obj("Feeler", pipe([(s * 0.3, 1.68, 0.36), (s * 0.44, 1.88, 0.4), (s * 0.5, 1.96, 0.48)], [0.05, 0.04, 0.0], 8), "Base")
        P.obj("Cheek", ball((s * 0.42, 1.68, 0.44), (0.16, 0.06, 0.11), 10, 5), "Accent")
        P.obj("Moustache", pipe([(s * 0.03, 1.82, 0.42), (s * 0.2, 1.84, 0.36), (s * 0.38, 1.78, 0.42), (s * 0.48, 1.7, 0.55), (s * 0.43, 1.65, 0.65)],
                                [0.065, 0.07, 0.055, 0.03, 0.0], 8), "Trim")
    P.obj("Smile", pipe([(-0.22, 1.76, 0.24), (-0.1, 1.82, 0.16), (0.1, 1.82, 0.16), (0.22, 1.76, 0.24)], [0.03, 0.035, 0.035, 0.03], 6), "Dark")
    # the crown between the stalks
    cc = (0, 1.1, 1.08)
    P.obj("Crown", lathe([(0.24, 0.0), (0.27, 0.06), (0.28, 0.18), (0.25, 0.18), (0.22, 0.04)], 18, "z", cc), "Trim")
    for k in range(6):
        a = 2 * math.pi * k / 6 + 0.26
        b = Vector(cc) + Vector((math.cos(a) * 0.27, math.sin(a) * 0.27, 0.16))
        P.obj("CrownSpike", cone(tuple(b), tuple(b + Vector((0, 0, 0.17))), 0.06, 5), "Trim", 0, False)
        P.obj("CrownPearl", ball(tuple(b + Vector((0, 0, 0.19))), (0.035, 0.035, 0.035), 6, 3), "Belly")
        P.obj("CrownGem", ball(tuple(Vector(cc) + Vector((math.cos(a + 0.52) * 0.28, math.sin(a + 0.52) * 0.28, 0.09))), (0.04, 0.03, 0.04), 6, 3), "Glass" if k % 2 else "Accent")
    # a gold collar of office where the head meets the body
    P.obj("Collar", xf(torus(0.62, 0.07, 0.0, 26, 6), Matrix.Rotation(math.radians(-25), 3, "X") @ Matrix.Diagonal((1.0, 0.8, 1.0)), (0, 0.85, 0.05)), "Trim", 1)
    P.obj("CollarGem", ball((0, 1.38, -0.1), (0.1, 0.06, 0.1), 10, 5), "Accent")
    # butterflies circling
    cols = ("Glass", "Accent", "Trim", "Belly")
    for k in range(6):
        a = 2 * math.pi * k / 6 + 0.5
        b = Vector((math.cos(a) * 1.85, math.sin(a) * 1.7, 1.2 + 0.3 * math.sin(a * 2)))
        f = Vector((-math.sin(a), math.cos(a), 0))
        side = Vector((math.cos(a), math.sin(a), 0))
        P.part("SpinFlies", pipe([tuple(b - f * 0.12), tuple(b + f * 0.12)], [0.025, 0.02], 5), "Dark", (0, 0, 1.2), 0)
        for s in (1, -1):
            w = [b, b + side * s * 0.26 + f * 0.16 + Vector((0, 0, 0.1)), b + side * s * 0.3 - f * 0.02 + Vector((0, 0, 0.12)), b + side * s * 0.18 - f * 0.16 + Vector((0, 0, 0.06))]
            P.part("SpinFlies", sheet([[tuple(p) for p in w]], 0.015), cols[k % 4], (0, 0, 1.2), 0, False)
    # ---- round three (2026-10-12, "make them better"): a grander palace, a royal mantle, a monocle and bushy brows, a glowing slime trail,
    # a taller crown, and his bee guards with spears circling him
    for k in range(16):   # a curtain wall with battlements round the keep
        a = 2 * math.pi * k / 16
        c = k0 + Vector((math.sin(a) * 0.62, math.cos(a) * 0.5, 0.12))
        P.obj("Wall", box(tuple(c), (0.24, 0.12, 0.24), Matrix.Rotation(-a, 3, "Z")), "Belly", 0, False)
        P.obj("Merlon", box(tuple(c + Vector((0, 0, 0.17))), (0.1, 0.12, 0.1), Matrix.Rotation(-a, 3, "Z")), "Belly", 0, False)
    P.obj("Gate", ball(tuple(k0 + Vector((0, 0.26, 0.2))), (0.12, 0.02, 0.18), 10, 5), "Dark")
    P.obj("GateArch", xf(torus(0.13, 0.025, 0.0, 14, 4), Matrix.Rotation(math.radians(90), 3, "X"), tuple(k0 + Vector((0, 0.27, 0.24)))), "Trim")
    for x in (-0.13, 0.13):
        P.obj("Window", ball(tuple(k0 + Vector((x, 0.26, 0.48))), (0.045, 0.02, 0.07), 6, 3), "Lamp")
    P.obj("Spire", cone(tuple(k0 + Vector((0, 0, 1.05))), tuple(k0 + Vector((0, 0, 1.75))), 0.12, 8), "Trim", 0, False)
    P.obj("SpireGem", ball(tuple(k0 + Vector((0, 0, 1.78))), (0.07, 0.07, 0.07), 8, 4), "Glow")
    for sx in (1, -1):   # banners on the front turrets
        tc = k0 + Vector((sx * 0.36, 0.3, 0))
        ban = [tc + Vector((sx * 0.0, 0.16, 0.5)), tc + Vector((sx * 0.0, 0.16, 0.18)), tc + Vector((sx * 0.0, 0.17, 0.1))]
        P.part("Cloth", sheet([[tuple(tc + Vector((-0.1, 0.16, 0.52))), tuple(tc + Vector((0.1, 0.16, 0.52))), tuple(tc + Vector((0.1, 0.17, 0.2))), tuple(tc + Vector((0.0, 0.18, 0.1))), tuple(tc + Vector((-0.1, 0.17, 0.2)))]], 0.02), "Accent", (0, 0, 0), 0, False)
        P.obj("BannerSun", ball(tuple(tc + Vector((0, 0.185, 0.34))), (0.05, 0.015, 0.05), 6, 3), "Trim")
    # the royal mantle over his back, red with an ermine hem
    def mpt(u, v):
        a = math.radians(-120 + 240 * u)
        r = 0.82 + 0.3 * v
        return (math.sin(a) * r, 0.62 - math.cos(a) * r * 0.7 - 0.2 * v, 0.6 - 1.0 * v + 0.05 * math.sin(u * 20))
    polys = [[mpt(i / 12, j / 5), mpt((i + 1) / 12, j / 5), mpt((i + 1) / 12, (j + 1) / 5), mpt(i / 12, (j + 1) / 5)] for i in range(12) for j in range(5)]
    P.part("Cloth", sheet(polys, 0.03), lambda c, n: ("Dark" if speckle(c, 5.0) < 0.12 else "Belly") if c.z < -0.25 else "Accent", (0, 0, 0), 0, False)
    # a monocle on his right eye, bushy white brows on both
    top = Vector((0.45, 1.55, 1.62))
    P.obj("Monocle", xf(torus(0.22, 0.03, 0.0, 22, 5), Matrix.Rotation(math.radians(90), 3, "X"), tuple(top + Vector((0, 0.24, -0.02)))), "Trim")
    P.obj("MonocleChain", pipe(bez(top + Vector((0.18, 0.24, -0.16)), top + Vector((0.35, 0.2, -0.6)), Vector((0.5, 1.4, 0.2)), Vector((0.3, 1.38, -0.05)), 8), [0.012] * 9, 4), "Trim")
    for s in (1, -1):
        t = Vector((s * 0.45, 1.55, 1.62))
        for k in range(5):
            b = t + Vector((s * (-0.2 + 0.1 * k), 0.12, 0.27 - 0.02 * abs(k - 2)))
            P.obj("Brow", cone(tuple(b), tuple(b + Vector((s * (0.1 + 0.03 * k), 0.1, 0.12 - 0.02 * k))), 0.06, 5), "Belly", 0, False)
    # the taller crown: two arches, an orb, a cross, a great ruby in front
    ccv = Vector(cc)
    for a in (0.0, math.pi / 2):
        arc = [ccv + Vector((math.sin(a) * math.cos(t) * 0.25, math.cos(a) * math.cos(t) * 0.25, 0.18 + math.sin(t) * 0.3)) for t in [math.pi * i / 10 for i in range(11)]]
        P.obj("CrownArch", pipe(arc, [0.03] * 11, 5), "Trim")
    P.obj("CrownOrb", ball(tuple(ccv + Vector((0, 0, 0.55))), (0.08, 0.08, 0.08), 10, 5), "Trim")
    P.obj("CrownCross", bar(ccv + Vector((0, 0, 0.6)), ccv + Vector((0, 0, 0.8)), 0.04, 0.04), "Trim")
    P.obj("CrownCross", bar(ccv + Vector((-0.07, 0, 0.72)), ccv + Vector((0.07, 0, 0.72)), 0.04, 0.04), "Trim")
    P.obj("CrownRuby", ball(tuple(ccv + Vector((0, 0.29, 0.09))), (0.09, 0.05, 0.1), 10, 5), "Accent")
    # a glowing slime trail behind him
    P.obj("Slime", ball((0, -1.75, -0.8), (0.34, 0.6, 0.03), 16, 6), "Glass")
    for k in range(5):
        P.obj("SlimeDrip", ball((0.3 * math.sin(k * 2.1), -0.9 - 0.25 * k, -0.86 - 0.04 * (k % 2)), (0.06, 0.06, 0.09), 6, 3), "Glass")
    # his bee guards circling, spears levelled
    for k in range(5):
        a = 2 * math.pi * k / 5 + 0.3
        c = Vector((math.sin(a) * 2.25, -0.2 + math.cos(a) * 2.0, 0.55 + 0.25 * math.sin(a * 2)))
        mini_bee(P, "SpinGuards", c, (math.cos(a), -math.sin(a), 0), (0, -0.2, 0.55), 1.4, spear=True, col="Trim")
        P.part("SpinGuards", dome(c + Vector((0, 0, 0.04)), (0.1, 0.1, 0.1), 0.02, 10, 5, 0.015), "Trim", (0, -0.2, 0.55))
    P.part("Muzzle", ball((0, 1.84, 0.2), (0.05, 0.03, 0.04), 8, 4), "Lamp", (0, 1.84, 0.2))
    return P


def bar(a, b, w, t, up=(0, 1, 0)):
    """a squared-off bar between two points, w wide (across, in the face plane) and t thick (toward +Y)."""
    a, b = Vector(a), Vector(b); d = (b - a).normalized(); n = Vector(up)
    if abs(d.dot(n)) > 0.95: n = Vector((0, 0, 1))
    s = d.cross(n).normalized() * w * 0.5; f = n * t * 0.5
    pts = [p + ds + df for p in (a, b) for ds in (s, -s) for df in (f, -f)]
    return hull([tuple(p) for p in pts])

# ================================================================= 4 (new). the demon sunflower (2026-10-12, in place of the sunflower titan: "make it a bad flower, something impressive")
def M_evilflower():
    """The sunflower gone bad: a huge carnivorous bloom whose seed face splits into a gaping maw ringed with fangs and dripping toxic green,
    slanted blazing eyes under angry brows, two rings of dagger-sharp crimson and purple petals curling toward the player like claws and
    turning slowly, a thick thorny stem, two thorned vine whips that lash, serrated leaf blades, a tangle of roots hanging below with clods
    of earth, and poison spores circling it. Round three (2026-10-12, "make them better"): a crown of great black thorns with glowing tips,
    a halo of black spikes behind the petals, seven more glowing seed-eyes staring from its face, and two more whips ending in snapping buds."""
    P = Boss("evilflower", {"Base": ((0.10, 0.30, 0.10), 0.45), "Belly": ((0.95, 0.72, 0.08), 0.5), "Accent": ((0.55, 0.04, 0.10), 0.5),
                            "Trim": ((0.32, 0.06, 0.42), 0.5), "Glass": ((0.96, 0.94, 0.82), 0.7), "Dark": ((0.06, 0.03, 0.03), 0.4),
                            "Glow": ((0.55, 1.0, 0.15), 0.5), "Metal": ((0.32, 0.20, 0.10), 0.4), "Lamp": ((1.0, 0.22, 0.05), 0.8)})
    FC = Vector((0, 0.3, 1.05))
    # the seed face: dark, crawling with a seed spiral
    def seeds(c, n):
        d = c - FC; r = math.hypot(d.x, d.z)
        if n.y < 0.2: return "Base"
        if r > 0.62: return "Belly"
        a = math.atan2(d.z, d.x)
        return "Metal" if ((a / (2 * math.pi) * 13 + r * 9) % 1.0 < 0.5) ^ ((a / (2 * math.pi) * -8 + r * 9) % 1.0 < 0.5) else "Dark"
    P.obj("Disc", lathe([(0.0, 0.18), (0.45, 0.16), (0.7, 0.07), (0.76, -0.02), (0.62, -0.12), (0.0, -0.18)], 30, "y", tuple(FC)), seeds, 0)
    # the maw: a gaping mouth in the lower face, a glowing throat, a ring of fangs, toxic drool
    MC = FC + Vector((0, 0.17, -0.18))
    P.obj("MawLip", xf(torus(1.0, 0.06, 0.0, 28, 6), Matrix.Rotation(math.radians(90), 3, "X") @ Matrix.Diagonal((0.36, 0.22, 1.0)), tuple(MC)), "Accent")
    P.obj("Maw", ball(tuple(MC), (0.34, 0.08, 0.2), 18, 8), "Dark")
    P.obj("Throat", ball(tuple(MC + Vector((0, 0.03, -0.02))), (0.18, 0.06, 0.09), 12, 6), "Glow")
    P.obj("Tongue", pipe(bez(MC + Vector((0, 0.04, -0.08)), MC + Vector((0, 0.2, -0.15)), MC + Vector((0.08, 0.3, -0.35)), MC + Vector((0.02, 0.28, -0.5)), 6), [0.06, 0.065, 0.06, 0.05, 0.04, 0.03, 0.0], 8), "Accent")
    for k in range(16):
        a = 2 * math.pi * k / 16
        rim = MC + Vector((math.cos(a) * 0.34, 0.06, math.sin(a) * 0.2))
        tipp = MC + Vector((math.cos(a) * 0.15, 0.1, math.sin(a) * 0.07))
        L = 0.75 if k % 2 == 0 else 0.55
        P.obj("Fang", cone(rim, rim + (tipp - rim) * L, 0.04 if k % 2 == 0 else 0.03, 5), "Glass", 0, False)
    for k, (x, z) in enumerate(((-0.2, -0.22), (0.05, -0.28), (0.22, -0.2))):   # drips of venom
        b = MC + Vector((x, 0.08, z))
        P.obj("Drool", pipe([b, b + Vector((0, 0.02, -0.18 - 0.08 * k))], [0.025, 0.02], 6), "Glow")
        P.obj("Drip", ball(tuple(b + Vector((0, 0.02, -0.22 - 0.08 * k))), (0.04, 0.04, 0.055), 8, 4), "Glow")
    # slanted blazing eyes and angry brows
    for s in (1, -1):
        ec = FC + Vector((s * 0.25, 0.17, 0.2))
        eye = ball((0, 0, 0), (0.14, 0.05, 0.08), 12, 6); xf(eye, Matrix.Rotation(math.radians(s * 20), 3, "Y"), tuple(ec))
        P.obj("Socket", xf(grow(eye.copy(), tuple(ec), 1.35), None, (0, -0.035, 0)), "Dark")
        P.obj("Eye", eye, "Lamp")
        P.obj("Pupil", ball(tuple(ec + Vector((0, 0.05, 0))), (0.02, 0.02, 0.06), 6, 3), "Dark")
        P.obj("Brow", bar(ec + Vector((-s * 0.14, 0.03, 0.14)), ec + Vector((s * 0.17, 0.0, 0.03)), 0.06, 0.06), "Trim")
    # two rings of dagger petals, curling toward the player, turning slowly about the nose axis
    for ring, (n, rr, L, W, col, dy, off, curl) in enumerate(((16, 0.72, 0.95, 0.26, "Accent", -0.02, 0.0, 0.45), (16, 0.68, 0.72, 0.22, "Trim", -0.1, 0.5, 0.25))):
        for k in range(n):
            a = 2 * math.pi * (k + off) / n
            bm = ball((0, 0, L * 0.5), (W * 0.5, 0.05, L * 0.5), 10, 6)
            for v in bm.verts:
                t = max(0.0, min(1.0, v.co.z / L))
                v.co.x *= 0.25 + 1.1 * math.sin(math.pi * t) ** 0.6 * (1 - t) ** 0.4
                v.co.y += curl * t * t
            def pp(c, nn, col=col, a=a, L=L, rr=rr):
                d = c - FC; r = math.hypot(d.x, d.z)
                return "Belly" if r > rr + L * 0.78 else col
            xf(bm, R("Y", math.degrees(a)), (FC.x + math.sin(a) * rr, FC.y + dy, FC.z + math.cos(a) * rr))
            P.part("RollPetals", bm, pp, tuple(FC), 0)
    # the thick thorny stem
    stem = bez((0, FC.y - 0.2, FC.z - 0.3), (0, -0.25, 0.4), (0, 0.15, -0.2), (0, 0.0, -0.75), 8)
    P.obj("Stem", pipe(stem, [0.2, 0.19, 0.18, 0.17, 0.17, 0.17, 0.18, 0.2, 0.22], 12), "Base", 1)
    for i in range(1, 8):
        for k in range(3):
            a = 2 * math.pi * (k / 3 + i * 0.37)
            t = (stem[i + 1] - stem[i - 1]).normalized(); side = t.cross(Vector((0, 0, 1)))
            side = side.normalized() if side.length > 1e-3 else Vector((1, 0, 0))
            out = (side * math.cos(a) + t.cross(side).normalized() * math.sin(a)).normalized()
            b = stem[i] + out * 0.16
            P.obj("Thorn", cone(b, b + out * 0.18 + t * 0.05, 0.045, 5), "Accent", 0, False)
    # serrated leaf blades
    for s in (1, -1):
        c0 = Vector((s * 0.12, 0.05, 0.1))
        bm = leaf((0, 0, 0), 1.3, 0.6, 0, 22, 0.05)
        for v in bm.verts:   # saw teeth along the edge
            if abs(v.co.y) > 0.12: v.co.y *= 1.0 + 0.35 * (1 if int(v.co.x * 14) % 2 else -0.2)
        if s < 0: bm = mirror_x(bm)
        xf(bm, None, tuple(c0))
        P.obj("Leaf", bm, lambda c, n: "Glow" if abs(c.y - 0.05) < 0.02 else "Base", 0)
    # two vine whips, thorned, lashing (each sways about where it leaves the stem)
    for s in (1, -1):
        hub = Vector((s * 0.15, 0.1, 0.55))
        name = "SwayR" if s > 0 else "SwayL"
        vine = bez(hub, hub + Vector((s * 0.6, 0.2, 0.35)), hub + Vector((s * 1.2, 0.5, -0.1)), hub + Vector((s * 1.35, 0.95, 0.4)), 12)
        vr = [0.1 - 0.075 * i / 12 for i in range(13)]
        P.part(name, pipe(vine, vr, 8), "Base", tuple(hub), 1)
        for i in range(1, 12, 2):
            t = (vine[i + 1] - vine[i - 1]).normalized(); up = Vector((0, 0, 1 if i % 4 == 1 else -1))
            b = vine[i] + up * vr[i] * 0.8
            P.part(name, cone(b, b + up * 0.12 + t * 0.04, 0.035, 4), "Accent", tuple(hub), 0, False)
        tipc = vine[-1]
        P.part(name, cone(tipc, tipc + (vine[-1] - vine[-3]).normalized() * 0.3, 0.06, 6), "Lamp", tuple(hub), 0, False)
        for k in range(3):   # a little bud on the whip, snapping
            a = 2 * math.pi * k / 3
            q = vine[8] + Vector((math.cos(a) * 0.1, 0, math.sin(a) * 0.1))
            P.part(name, cone(q, q + Vector((math.cos(a) * 0.12, 0.08, math.sin(a) * 0.12 + 0.05)), 0.05, 4), "Accent", tuple(hub), 0, False)
    # the tangle of roots hanging below, with clods of earth
    base = stem[-1]
    P.obj("Bulb", ball(tuple(base + Vector((0, 0, -0.08))), (0.32, 0.3, 0.22), 14, 7), "Metal", 1)
    rng = random.Random(5)
    for k in range(9):
        a = 2 * math.pi * k / 9 + rng.uniform(-0.2, 0.2)
        d = Vector((math.cos(a), math.sin(a), 0))
        r = bez(base + d * 0.15 + Vector((0, 0, -0.12)), base + d * 0.5 + Vector((0, 0, -0.25)), base + d * 0.6 + Vector((0, 0, -0.55)), base + d * (0.45 + rng.uniform(0, 0.3)) + Vector((rng.uniform(-0.15, 0.15), 0, -0.85)), 6)
        P.obj("Root", pipe(r, [0.07, 0.06, 0.05, 0.04, 0.03, 0.02, 0.0], 6), "Metal")
        if k % 3 == 0: P.obj("Clod", ball(tuple(r[3]), (0.11, 0.1, 0.08), 8, 4), "Dark")
    # poison spores circling it
    for k in range(12):
        a = 2 * math.pi * k / 12
        c = Vector((math.sin(a) * 1.7, math.cos(a) * 1.3, 0.5 + 0.45 * math.sin(a * 3)))
        P.part("SpinSpores", ball(tuple(c), (0.07, 0.07, 0.07), 8, 4), "Glow", (0, 0, 0.5))
        for j in range(4):
            b = Matrix.Rotation(math.radians(90 * j), 3, "Y") @ Vector((0, 0, 0.11))
            P.part("SpinSpores", cone(c, c + b, 0.025, 4), "Trim", (0, 0, 0.5), 0, False)
    # ---- round three (2026-10-12, "make them better"): a crown of thorns, a halo of black spikes, more glowing eyes, two more whips
    for k in range(9):   # the crown of great thorns rising from the top of the bloom
        a = math.radians(-64 + 128 * k / 8)
        d = Vector((math.sin(a), 0, math.cos(a)))
        b = FC + d * 0.66 + Vector((0, 0.02, 0))
        L = 0.75 if k % 2 == 0 else 0.5
        if k == 4: L = 0.95
        P.obj("ThornCrown", cone(tuple(b), tuple(b + d * L + Vector((0, 0.12, 0))), 0.1 if k % 2 == 0 else 0.075, 6), "Dark", 0, False)
        P.obj("ThornGlow", ball(tuple(b + d * (L * 0.82) + Vector((0, 0.1, 0))), (0.045, 0.045, 0.045), 6, 3), "Lamp")
    arc = [FC + Vector((math.sin(t) * 0.66, 0.02, math.cos(t) * 0.66)) for t in [math.radians(-70 + 140 * i / 14) for i in range(15)]]
    P.obj("ThornBand", pipe(arc, [0.06] * 15, 7), "Base")
    for k in range(18):   # a halo of black spikes behind the petals
        a = 2 * math.pi * (k + 0.5) / 18
        d = Vector((math.sin(a), 0, math.cos(a)))
        b = FC + d * 0.5 + Vector((0, -0.22, 0))
        P.obj("Spike", cone(tuple(b), tuple(b + d * (1.35 if k % 2 else 1.1) + Vector((0, -0.12, 0))), 0.07, 5), "Dark", 0, False)
    def face_y(x, z):
        r = math.hypot(x, z)
        return FC.y + (0.16 if r < 0.45 else 0.16 - 0.09 * (r - 0.45) / 0.25) + 0.02
    for (x, z, r) in ((0.0, 0.5, 0.07), (-0.44, 0.36, 0.05), (0.44, 0.36, 0.05), (-0.55, 0.05, 0.045), (0.55, 0.05, 0.045), (-0.2, 0.47, 0.04), (0.2, 0.47, 0.04)):
        c = Vector((x, face_y(x, z), FC.z + z))   # more glowing seed-eyes, staring
        P.obj("SeedSocket", ball(tuple(c + Vector((0, -0.01, 0))), (r * 1.35, 0.03, r * 1.1), 8, 4), "Dark")
        P.obj("SeedEye", ball(tuple(c), (r, 0.03, r * 0.8), 8, 4), "Lamp")
        P.obj("SeedPupil", ball(tuple(c + Vector((0, 0.025, 0))), (r * 0.25, 0.015, r * 0.7), 6, 3), "Dark")
    for s in (1, -1):   # two more whips, lower, lashing forward
        hub = Vector((s * 0.15, 0.05, -0.15))
        name = "Sway2" if s > 0 else "Sway3"
        vine = bez(hub, hub + Vector((s * 0.55, 0.1, -0.2)), hub + Vector((s * 0.95, 0.6, -0.45)), hub + Vector((s * 0.85, 1.1, -0.15)), 10)
        vr = [0.085 - 0.065 * i / 10 for i in range(11)]
        P.part(name, pipe(vine, vr, 8), "Base", tuple(hub), 1)
        for i in range(1, 10, 2):
            b = vine[i] + Vector((0, 0, vr[i] * 0.8 * (1 if i % 4 == 1 else -1)))
            P.part(name, cone(b, b + Vector((0, 0.03, 0.11 * (1 if i % 4 == 1 else -1))), 0.03, 4), "Accent", tuple(hub), 0, False)
        tipc = vine[-1]
        for k in range(4):   # a snapping bud of a mouth on the end, glowing inside
            a = 2 * math.pi * k / 4 + 0.4
            q = tipc + Vector((math.cos(a) * 0.08, 0, math.sin(a) * 0.08))
            P.part(name, cone(q, q + Vector((math.cos(a) * 0.1, 0.14, math.sin(a) * 0.1)), 0.05, 4), "Accent", tuple(hub), 0, False)
        P.part(name, ball(tuple(tipc + Vector((0, 0.04, 0))), (0.06, 0.06, 0.06), 6, 3), "Glow", tuple(hub))
    P.part("Muzzle", ball(tuple(MC + Vector((0, 0.1, 0))), (0.06, 0.03, 0.05), 8, 4), "Glow", tuple(MC + Vector((0, 0.1, 0))))
    return P


BOSSES = [("bee", M_bee), ("ladybug", M_ladybug), ("dragonfly", M_dragonfly), ("evilflower", M_evilflower), ("snail", M_snail)]

if __name__ == "__main__":
    os.makedirs(AB.OUT, exist_ok=True)
    for bid, fn in BOSSES:
        if ONLY and bid not in ONLY: continue
        fn().finish()
    print("DONE")
