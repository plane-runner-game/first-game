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



# ================================================================= 2026-10-14: the five remade like the alien / west / treasure / sea ones
# Real anatomy and proportions, scarier faces, the cartoon idea kept, details that sit evenly - each flying its own way, one you can see from
# the front - and their surfaces baked into textures (boss_bake.py) so they stop looking like plastic.
from west_bosses import V_, glow_strength, AB_pal, fib_dirs
from alien_bosses import lerp_keys, spine_frames, oriented_ball
from autumn_bosses import fx_tuft, st_loft, st_cloth, sq_axes, spline as st_spline
from treasure_bosses import frame_rh
from sea_bosses import ell_cap, rh, resample, ring_on
import boss_bake as BB


def ell_pt(c, r, d):
    """the point on the ellipsoid (centre c, radii r) straight out along d from its centre, and the outward normal there."""
    d = V_(d).normalized(); c = V_(c)
    k = 1.0 / math.sqrt((d.x / r[0]) ** 2 + (d.y / r[1]) ** 2 + (d.z / r[2]) ** 2)
    p = c + d * k
    return p, V_(((p.x - c.x) / r[0] ** 2, (p.y - c.y) / r[1] ** 2, (p.z - c.z) / r[2] ** 2)).normalized()


def facet_attrs(bm, c, x, y, z, k=16.0):
    """marks a compound eye (a ball about c whose axes x, y (its gaze), z are given) for the bake's regular hexagonal facets: "fx", "fy" are
    each point's angle from the gaze laid out flat round it (an azimuthal projection), k facets to the radian."""
    lx, ly = bm.verts.layers.float.new("fx"), bm.verts.layers.float.new("fy"); bm.verts.ensure_lookup_table()
    c, x, y, z = V_(c), V_(x).normalized(), V_(y).normalized(), V_(z).normalized()
    for v in bm.verts:
        d = (v.co - c).normalized(); th = math.acos(max(-1.0, min(1.0, d.dot(y)))); ph = math.atan2(d.dot(z), d.dot(x))
        v[lx] = th * math.cos(ph) * k; v[ly] = th * math.sin(ph) * k
    return bm


def tuft_into(bm, base, d, L, w, across, nrm=None, lie=0.0):
    """a fur clump into bm: four-sided, from base along d, L long, w wide across and half that thick, its middle and tip bent over toward
    the hide (nrm) by lie - so a coat of them lies down like fur instead of bristling."""
    d = V_(d).normalized(); across = (V_(across) - d * d.dot(V_(across))).normalized(); up = d.cross(across)
    if nrm is not None: nrm = V_(nrm).normalized()
    def ringat(c, ww): return [bm.verts.new(c + across * ww), bm.verts.new(c + up * (ww * 0.6)), bm.verts.new(c - across * ww)]
    sag = (-nrm * lie) if nrm is not None else V_((0, 0, 0))
    r0 = ringat(base, w); r1 = ringat(base + d * (L * 0.5) + sag * (L * 0.15), w * 0.7)
    tip = bm.verts.new(base + d * L + sag * (L * 0.45))
    for k in range(3):
        bm.faces.new((r0[k], r0[(k + 1) % 3], r1[(k + 1) % 3], r1[k])); bm.faces.new((r1[k], r1[(k + 1) % 3], tip))


class Coat:
    """fur tufts gathered by colour, each colour one object (hundreds of tufts would otherwise be hundreds of objects)."""
    def __init__(self, name): self.name = name; self.bms = {}
    def add(self, slot, base, d, L, w, across, nrm=None, lie=0.0):
        tuft_into(self.bms.setdefault(slot, bmesh.new()), V_(base), d, L, w, across, nrm, lie)
    def put(self, P):
        for slot, bm in self.bms.items():
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces); ob = P.obj(self.name, bm, slot)
            at = ob.data.attributes.new("small", "INT", "FACE"); at.data.foreach_set("value", [1] * len(ob.data.polygons))   # a sliver of the atlas


def comb(nn, lean, k):
    """the direction a hair grows from a hide facing nn, combed k of the way toward lean."""
    lv = V_(lean) - nn * nn.dot(V_(lean))
    return (nn + lv.normalized() * k).normalized() if lv.length > 1e-4 else nn


def insect_leg(P, pts, radii, slot="Metal", name="Leg", claws=True, hub=None):
    """an insect's leg through its joints (hip .. foot): each segment a little club, thicker toward its far end, the joints knobbed, a pair of
    hooked claws at the foot (part of the mover hub if given)."""
    pts = [V_(p) for p in pts]
    def put(bm, sl):
        if hub is None: P.obj(name, bm, sl)
        else: P.part(name, bm, sl, tuple(hub))
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]; r0, r1 = radii[i], radii[i + 1]
        put(pipe([a, a.lerp(b, 0.5), b], [r0 * 0.85, (r0 + r1) * 0.5 * 1.08, r1], 8), slot)
        put(ball(tuple(b), (r1 * 1.05,) * 3, 8, 4), slot)
    if claws:
        f = pts[-1]; d = (pts[-1] - pts[-2]).normalized(); sd = d.cross(V_((0, 0, 1)))
        sd = sd.normalized() if sd.length > 1e-3 else V_((1, 0, 0))
        for s in (1, -1):
            c = bez(f, f + d * 0.04 + sd * s * 0.02, f + d * 0.07 + sd * s * 0.035 - V_((0, 0, 0.02)), f + d * 0.06 + sd * s * 0.04 - V_((0, 0, 0.05)), 4)
            put(pipe(c, [radii[-1] * 0.6, radii[-1] * 0.5, radii[-1] * 0.38, radii[-1] * 0.22, 0.0], 5), slot)


def insect_wing(P, name, hub, root, S, C, L, le, te, veins, stigma=None, slot_web="Glass", slot_vein="Metal", nu=16, nv=5):
    """an insect's wing: the membrane between its leading edge le and trailing edge te (keys (u, v): u 0..1 along the span S from root, v in
    metres back across it along C), and its veins - polylines in (u, v), with radii - standing on both faces; one part, hub the pivot."""
    root, S, C = V_(root), V_(S).normalized(), V_(C).normalized(); N = S.cross(C).normalized()
    def at(u, v, w=0.0): return root + S * (u * L) + C * v + N * w
    rows = [[at(u, lerp_keys(u, le) + (lerp_keys(u, te) - lerp_keys(u, le)) * j / nv) for j in range(nv + 1)] for u in [i / nu for i in range(nu + 1)]]
    polys = [[tuple(rows[i][j]), tuple(rows[i + 1][j]), tuple(rows[i + 1][j + 1]), tuple(rows[i][j + 1])] for i in range(nu) for j in range(nv)]
    P.part(name, st_cloth(polys, 0.012), slot_web, tuple(hub), 0, True)
    for pts, r in veins:
        q = [at(u, v) for (u, v) in pts]
        if len(q) == 2: q = [q[0], q[0].lerp(q[1], 0.5), q[1]]
        P.part(name, pipe(q, [r * 0.62] * (len(q) - 1) + [r * 0.4], 5), slot_vein, tuple(hub))
    if stigma:
        (u0, u1, v) = stigma
        P.part(name, pipe([at(u0, v), at((u0 + u1) * 0.5, v), at(u1, v)], [0.012, 0.02, 0.009], 6), slot_vein, tuple(hub))


def worker_bee(P, name, c, fwd, hub, k=1.0):
    """a worker bumblebee flying along fwd: a fuzzy thorax, a banded abdomen, a dark head with its compound eyes, two smoky wings raised;
    part of the mover name."""
    c = V_(c); f = V_(fwd).normalized(); sd = f.cross(V_((0, 0, 1))).normalized(); up = sd.cross(f)
    def put(bm, sl): P.part(name, bm, sl, tuple(hub))
    put(oriented_ball(c, (0.085 * k, 0.085 * k, 0.08 * k), *rh(sd, f, up), 10, 6), "Dark")
    ab = c - f * 0.14 * k - up * 0.03 * k
    put(oriented_ball(ab, (0.075 * k, 0.12 * k, 0.07 * k), *rh(sd, f, up), 10, 6), "Base")
    put(oriented_ball(ab - f * 0.02 * k, (0.078 * k, 0.03 * k, 0.073 * k), *rh(sd, f, up), 10, 4), "Dark")
    put(oriented_ball(ab - f * 0.11 * k, (0.05 * k, 0.04 * k, 0.045 * k), *rh(sd, f, up), 8, 4), "Belly")
    hd = c + f * 0.1 * k
    put(oriented_ball(hd, (0.06 * k, 0.045 * k, 0.065 * k), *rh(sd, f, up), 10, 6), "Dark")
    for s in (1, -1):
        put(oriented_ball(hd + sd * s * 0.045 * k + f * 0.01 * k, (0.02 * k, 0.03 * k, 0.045 * k), *rh(sd, f, up), 8, 4), "Glow")
        put(oriented_ball(c + sd * s * 0.12 * k + up * 0.1 * k, (0.12 * k, 0.05 * k, 0.008), *rh(sd, f, up), 10, 3), "Glass")


def M2_bee():
    """THE QUEEN BUMBLEBEE (2026-10-14, remade like the alien / west / treasure / sea bosses): a bumblebee queen built like the real insect -
    a garden bumblebee's colours in a deep pile of fur: the yellow collar and the yellow band at the back of the thorax, the black between,
    the abdomen's plates banded yellow, black, yellow, black and a white tail, a fuzz of hair standing all round her outline. The face of
    an insect, which is the frightening thing: two great compound eyes glowing honey-gold through thousands of facets, three ocelli in a
    triangle on her brow, elbowed antennae reaching forward, the shiny plate of the clypeus and a pair of toothed mandibles open. Six
    jointed legs, hairy; on each hind leg the pollen basket loaded with a glowing ball of pollen; the sting at the tail with a bead of venom.
    The cartoon idea kept: her crown, a breastplate of gold honeycomb with glowing honey in its cells, the honey sceptre in one forefoot
    and a golden sting-lance in the other levelled at you, and her workers circling her.
    She flies on two pairs of smoky glass wings with real veins - the stigma, the marginal and submarginal cells - held raised behind her
    and beating fast (FlapL / FlapR); the workers circle (SpinWorkers)."""
    P = Boss("bee", AB_pal(Base=((0.98, 0.7, 0.08), 0.3), Belly=((0.95, 0.92, 0.84), 0.3), Accent=((0.8, 0.06, 0.12), 0.8), Trim=((0.98, 0.76, 0.22), 0.85),
                           Glass=((0.8, 0.83, 0.86), 0.9), Dark=((0.035, 0.03, 0.028), 0.3), Glow=((1.0, 0.62, 0.08), 0.5), Metal=((0.07, 0.05, 0.04), 0.7),
                           Lamp=((1.0, 0.58, 0.08), 0.9)))
    glow_strength(P, 1.6)
    coat = Coat("Fur")
    # ---- the thorax: a round ball of fur, a yellow collar and a yellow band at the back, black between
    T, TR = V_((0, 0.32, 0.3)), (0.5, 0.47, 0.46)
    def tcol(d): return "Base" if d.y > 0.42 or d.y < -0.58 else "Dark"
    P.obj("Thorax", ball(tuple(T), TR, 28, 14), lambda c, n: tcol((c - T).normalized()))
    for d in fib_dirs(1000):
        if d.z < -0.6: continue
        p, nn = ell_pt(T, TR, d)
        coat.add(tcol(d), p - nn * 0.02, comb(nn, (0, -1, 0.2), 1.1), 0.08, 0.032, V_((0, 0, 1)).cross(nn) if abs(nn.z) < 0.9 else V_((1, 0, 0)), nn, 0.5)
    # the honeycomb breastplate on the chest, gold rims, honey glowing in the cells
    for row in range(5):
        z = T.z - 0.12 - row * 0.085
        for col in range(-3, 4):
            x = (col + 0.5 * (row % 2)) * 0.098
            q = (x / TR[0]) ** 2 + ((z - T.z) / TR[2]) ** 2
            if q > 0.8 or abs(x) > 0.3: continue
            y = T.y + TR[1] * math.sqrt(1 - q)
            nrm = V_((x / TR[0] ** 2, (y - T.y) / TR[1] ** 2, (z - T.z) / TR[2] ** 2)).normalized()
            hexplate(P, V_((x, y, z)) + nrm * 0.012, nrm, 0.05)
    # ---- the abdomen: six plates, each a little flared at its back edge, banded yellow / black / yellow / black / white
    A0, A1 = V_((0, -0.12, 0.12)), V_((0, -1.42, -0.64)); AL = (A1 - A0).length; ad = (A1 - A0).normalized()
    sp = [A0.lerp(A1, i / 60) for i in range(61)]; FR = spine_frames(sp)
    SEGS = (0.0, 0.15, 0.32, 0.49, 0.65, 0.8, 0.92, 1.0)
    def seg_of(u):
        for k in range(len(SEGS) - 1):
            if u < SEGS[k + 1]: return k, (u - SEGS[k]) / (SEGS[k + 1] - SEGS[k])
        return len(SEGS) - 2, 1.0
    def env(u): return lerp_keys(u, [(0, 0.24), (0.1, 0.5), (0.3, 0.62), (0.5, 0.63), (0.7, 0.55), (0.85, 0.38), (0.95, 0.2), (1, 0.04)])
    def arad(u):
        k, f = seg_of(u); return env(u) * (0.93 + 0.07 * f)
    ACOL = ["Base", "Dark", "Base", "Dark", "Belly", "Belly", "Belly"]
    def acol(u): return ACOL[seg_of(min(0.999, max(0.0, u)))[0]]
    RA = [arad(i / 60) for i in range(61)]
    P.obj("Abdomen", st_loft(sp, RA, [r * 0.94 for r in RA], [r * 0.88 for r in RA], FR, 28, 1.05), lambda c, n: acol((c - A0).dot(ad) / AL))
    for i in range(2, 59):
        u = i / 60; t, side, up = FR[i]; nr = max(12, int(52 * RA[i] / 0.63))
        for j in range(nr):
            a = 2 * math.pi * (j + 0.5 * (i % 2)) / nr
            nn = (side * math.cos(a) + up * math.sin(a)).normalized()
            p = sp[i] + side * (math.cos(a) * RA[i]) + up * (math.sin(a) * RA[i] * (0.94 if math.sin(a) > 0 else 0.88))
            coat.add(acol(u), p - nn * 0.02, comb(nn, t, 1.2), 0.075, 0.03, side.cross(nn) if abs(side.dot(nn)) < 0.9 else up, nn, 0.5)
    # the sting, a bead of venom on its point
    st = A1 - ad * 0.04
    P.obj("Sting", pipe([st, st + ad * 0.16, st + ad * 0.3], [0.04, 0.025, 0.0], 8), "Metal")
    for k in range(3):
        b0 = st + ad * (0.12 + 0.05 * k); P.obj("Sting", cone(b0, b0 - ad * 0.05 + V_((0, 0, 0.025)), 0.012, 4), "Metal")
    P.obj("Venom", ball(tuple(st + ad * 0.32), (0.035, 0.035, 0.045), 8, 4), "Glow")

    # ---- the head: an insect's face - the great compound eyes at its sides, the ocelli on the brow, antennae, the clypeus, open mandibles
    Hc, HR = V_((0, 0.92, 0.5)), (0.3, 0.23, 0.34)
    P.obj("Head", ball(tuple(Hc), HR, 24, 12), lambda c, n: "Base" if (c - Hc).z > 0.2 and (c - Hc).y < 0.12 else "Dark")
    for d in fib_dirs(520):
        if d.y > 0.35 or d.z < -0.2: continue   # no hair over the face itself
        p, nn = ell_pt(Hc, HR, d)
        coat.add("Base" if d.z > 0.55 else "Dark", p - nn * 0.016, comb(nn, (0, -1, 0.3), 1.0), 0.065, 0.028, V_((1, 0, 0)) if abs(nn.x) < 0.9 else V_((0, 0, 1)), nn, 0.45)
    for s in (1, -1):
        ne = V_((s * 1.0, 0.5, 0.05)).normalized()
        ec = Hc + V_((s * 0.22, 0.05, 0.04))
        ey_ = (V_((0, 1, 0)) - ne * ne.y).normalized(); ez_ = ne.cross(ey_).normalized()
        fr_ = rh(ne, ey_, ez_ if ez_.z > 0 else -ez_)
        P.obj("Eye", facet_attrs(oriented_ball(ec, (0.12, 0.16, 0.28), *fr_, 32, 16), ec, fr_[1], fr_[0], fr_[2], 9.0), "Glow")
        # the antenna: the long scape up from the face, the elbow, the beaded flagellum reaching forward
        a0 = Hc + V_((s * 0.075, 0.2, 0.04)); el = a0 + V_((s * 0.1, 0.12, 0.24))
        P.obj("Antenna", pipe([a0, a0.lerp(el, 0.5), el], [0.028, 0.026, 0.024], 8), "Metal")
        fl = bez(el, el + V_((s * 0.12, 0.2, 0.06)), el + V_((s * 0.26, 0.4, 0.0)), el + V_((s * 0.34, 0.56, -0.1)), 10)
        for k in range(10):
            P.obj("Antenna", oriented_ball(fl[k].lerp(fl[k + 1], 0.5), (0.024, 0.032, 0.024), *rh(*frame_rh(fl[k + 1] - fl[k])), 8, 4), "Metal")
        # the mandible: a curved, toothed blade from the side of the mouth, open
        m0 = Hc + V_((s * 0.14, 0.14, -0.25))
        mp = bez(m0, m0 + V_((s * 0.16, 0.1, -0.08)), m0 + V_((s * 0.1, 0.27, -0.17)), m0 + V_((-s * 0.02, 0.33, -0.2)), 6)
        P.obj("Mandible", pipe(mp, [0.07, 0.072, 0.066, 0.056, 0.042, 0.026, 0.0], 8), "Metal")
        for k in (2, 3, 4):
            q = mp[k]; inn = (V_((-s, 0.2, 0)) ).normalized()
            P.obj("MandibleTooth", cone(q, q + inn * 0.075 + V_((0, 0.01, -0.01)), 0.024, 5), "Accent")
    P.obj("Clypeus", oriented_ball(Hc + V_((0, 0.19, -0.11)), (0.12, 0.03, 0.11), V_((1, 0, 0)), V_((0, 1, 0)), V_((0, 0, 1)), 16, 8), "Dark")
    for p in (Hc + V_((0, 0.13, 0.28)), Hc + V_((0.07, 0.06, 0.31)), Hc + V_((-0.07, 0.06, 0.31))):   # the three ocelli
        P.obj("Ocellus", ball(tuple(p), (0.034, 0.034, 0.03), 10, 5), "Glow")
    # the crown, behind the ocelli: a ruby band, eight points, two arches, an orb and a cross, a sapphire at the front
    cc = Hc + V_((0, -0.05, 0.27))
    P.obj("Crown", lathe([(0.19, 0.0), (0.22, 0.15), (0.205, 0.16), (0.175, 0.015)], 24, "z", tuple(cc)), "Trim")
    for k in range(8):
        a = 2 * math.pi * k / 8
        b = cc + V_((math.sin(a) * 0.21, math.cos(a) * 0.21, 0.145))
        P.obj("CrownSpike", cone(tuple(b), tuple(b + V_((math.sin(a) * 0.03, math.cos(a) * 0.03, 0.15))), 0.042, 6), "Trim")
        P.obj("CrownPearl", ball(tuple(b + V_((math.sin(a) * 0.03, math.cos(a) * 0.03, 0.165))), (0.026, 0.026, 0.026), 8, 4), "Belly")
        P.obj("Ruby", ball(tuple(cc + V_((math.sin(a + 0.39) * 0.215, math.cos(a + 0.39) * 0.215, 0.075))), (0.035, 0.024, 0.035), 8, 4), "Accent")
    for a in (0.0, math.pi / 2):
        arc = [cc + V_((math.sin(a) * math.cos(t) * 0.2, math.cos(a) * math.cos(t) * 0.2, 0.15 + math.sin(t) * 0.2)) for t in [math.pi * i / 12 for i in range(13)]]
        P.obj("CrownArch", pipe(arc, [0.02] * 13, 6), "Trim")
    P.obj("CrownOrb", ball(tuple(cc + V_((0, 0, 0.38))), (0.055, 0.055, 0.055), 12, 6), "Trim")
    P.obj("CrownCross", bar(cc + V_((0, 0, 0.42)), cc + V_((0, 0, 0.55)), 0.028, 0.028), "Trim")
    P.obj("CrownCross", bar(cc + V_((-0.045, 0, 0.5)), cc + V_((0.045, 0, 0.5)), 0.028, 0.028), "Trim")

    # ---- six jointed legs, hairy; the hind ones carry the pollen baskets; the forefeet hold the sceptre and the lance
    GR, GL = V_((0.6, 1.08, -0.02)), V_((-0.6, 1.08, -0.02))
    for s in (1, -1):
        g = GR if s > 0 else GL
        hip = T + V_((s * 0.18, 0.3, -0.33)); knee = hip + V_((s * 0.3, 0.12, -0.16))
        insect_leg(P, [hip, hip + V_((s * 0.05, 0.03, -0.05)), knee, g - V_((s * 0.04, 0.1, 0.02)), g + V_((-s * 0.02, 0.02, 0.06))], [0.07, 0.06, 0.07, 0.06, 0.04])
        hip = T + V_((s * 0.24, 0.04, -0.37)); knee = hip + V_((s * 0.42, -0.02, -0.08)); foot = knee + V_((s * 0.08, -0.14, -0.4))
        insect_leg(P, [hip, hip + V_((s * 0.05, 0, -0.05)), knee, foot, foot + V_((s * 0.03, -0.1, -0.2))], [0.07, 0.06, 0.07, 0.055, 0.035])
        hip = T + V_((s * 0.22, -0.22, -0.33)); knee = hip + V_((s * 0.42, -0.18, -0.12)); ank = knee + V_((s * 0.08, -0.3, -0.42))
        insect_leg(P, [hip, hip + V_((s * 0.05, -0.03, -0.05)), knee, ank, ank + V_((s * 0.04, -0.12, -0.26))], [0.075, 0.065, 0.075, 0.07, 0.05])
        # the pollen basket: the broad shiny shin, a fringe of long hairs round it, a ball of pollen packed in
        tb = knee.lerp(ank, 0.55); td = (ank - knee).normalized(); ou = V_((s, 0, 0)); acr = td.cross(ou).normalized()
        P.obj("Corbicula", oriented_ball(tb, (0.035, 0.24, 0.11), *rh(ou, td, acr), 14, 7), "Metal")
        for k in range(14):
            t = k / 13; q = knee.lerp(ank, 0.15 + 0.8 * t)
            for side_ in (1, -1):
                coat.add("Dark", q + acr * side_ * 0.1, (acr * side_ + ou * 0.6 + td * 0.3).normalized(), 0.12, 0.016, td)
        P.obj("Pollen", ball(tuple(tb + ou * 0.12), (0.14, 0.16, 0.14), 16, 8), "Lamp")
    for s in (1, -1):   # hair on the femurs
        for k in range(3):
            hip = T + V_((s * (0.18 + 0.06 * k), 0.3 - 0.27 * k, -0.35))
            for j in range(6):
                q = hip + V_((s * 0.05 * j, 0.0, -0.02 * j))
                coat.add("Dark", q, V_((s * 0.2, -0.3, -1.0)).normalized(), 0.08, 0.02, V_((1, 0, 0)))
    coat.put(P)
    # the honey sceptre in her right forefoot: a gold staff, a honey dipper, a cup and a glowing orb of honey
    P.obj("Staff", pipe([GR + V_((0, 0, -0.62)), GR + V_((0.03, 0.01, 0.5))], [0.032, 0.032], 8), "Trim")
    top = GR + V_((0.03, 0.01, 0.5))
    P.obj("Dipper", lathe([(0.0, -0.36), (0.085, -0.34), (0.12, -0.28), (0.085, -0.21), (0.12, -0.14), (0.085, -0.07), (0.0, -0.05)], 16, "z", tuple(top)), "Lamp")
    P.obj("SceptreCup", lathe([(0.0, 0.0), (0.1, 0.04), (0.085, 0.1)], 14, "z", tuple(top)), "Trim")
    P.obj("SceptreOrb", ball(tuple(top + V_((0, 0, 0.19))), (0.1, 0.1, 0.1), 16, 8), "Lamp")
    for k in range(4): P.obj("Drip", ball(tuple(top + V_((0.08 * math.cos(k * 1.6), 0.08 * math.sin(k * 1.6), -0.42 - 0.06 * k))), (0.03, 0.03, 0.045), 8, 4), "Lamp")
    # the golden sting-lance in her left forefoot, levelled at you: barbed like her own sting, its point glowing
    d = V_((-0.35, 0.85, 0.3)).normalized()
    P.obj("Lance", pipe([GL - d * 0.4, GL, GL + d * 0.7, GL + d * 1.25], [0.045, 0.055, 0.04, 0.0], 10), "Trim")
    P.obj("Vamplate", cone(tuple(GL + d * 0.13), tuple(GL - d * 0.1), 0.15, 16), "Trim")
    sd = d.cross(V_((0, 0, 1))).normalized(); upl = sd.cross(d)
    for k in range(4):
        b0 = GL + d * (0.75 + 0.1 * k)
        for q in (sd, -sd, upl, -upl): P.obj("LanceBarb", cone(b0 + q * 0.02, b0 + q * 0.06 - d * 0.06, 0.014, 4), "Trim")
    tip = GL + d * 1.25
    P.obj("LanceTip", ball(tuple(tip), (0.04, 0.04, 0.04), 8, 4), "Glow")

    # ---- the wings: two pairs of smoky glass wings with real veins, raised behind her, beating
    FLE = [(0, -0.02), (0.15, -0.05), (0.4, -0.07), (0.65, -0.07), (0.85, -0.03), (0.96, 0.04), (1.0, 0.12)]
    FTE = [(0, 0.06), (0.12, 0.16), (0.3, 0.3), (0.5, 0.42), (0.7, 0.46), (0.85, 0.41), (0.95, 0.3), (1.0, 0.14)]
    FV = [([(0, -0.02), (0.3, -0.06), (0.6, -0.066)], 0.016), ([(0.0, 0.0), (0.3, -0.028), (0.58, -0.048)], 0.011),
          ([(0.66, -0.064), (0.8, -0.05), (0.92, -0.01), (0.86, 0.06), (0.72, 0.08), (0.62, 0.06), (0.6, -0.04)], 0.009),
          ([(0.42, 0.08), (0.55, 0.12), (0.7, 0.14), (0.82, 0.12)], 0.009), ([(0.5, 0.065), (0.52, 0.115)], 0.008), ([(0.61, 0.068), (0.63, 0.13)], 0.008),
          ([(0.72, 0.08), (0.74, 0.14)], 0.008), ([(0.0, 0.06), (0.25, 0.14), (0.45, 0.2), (0.72, 0.27)], 0.01),
          ([(0.0, 0.1), (0.22, 0.22), (0.42, 0.3), (0.62, 0.36)], 0.009), ([(0.42, 0.2), (0.44, 0.3)], 0.008), ([(0.6, 0.255), (0.62, 0.355)], 0.008),
          ([(0.0, 0.12), (0.15, 0.24), (0.3, 0.33)], 0.008)]
    HLE = [(0, -0.01), (0.3, -0.04), (0.7, -0.04), (0.92, 0.0), (1.0, 0.07)]
    HTE = [(0, 0.05), (0.2, 0.15), (0.45, 0.24), (0.7, 0.26), (0.88, 0.2), (1.0, 0.08)]
    HV = [([(0, -0.01), (0.5, -0.038)], 0.012), ([(0, 0.02), (0.45, 0.02), (0.75, 0.05)], 0.009), ([(0, 0.06), (0.35, 0.12), (0.7, 0.16)], 0.009),
          ([(0.42, 0.025), (0.44, 0.125)], 0.007)]
    for s in (1, -1):
        name = "FlapR" if s > 0 else "FlapL"
        fr, _ = ell_pt(T, TR, (s * 0.55, 0.2, 0.81)); hr, _ = ell_pt(T, TR, (s * 0.5, -0.18, 0.85))
        S1 = V_((s * 0.8, -0.18, 0.57)).normalized(); C0 = V_((0, -0.6, -0.8)); C1 = (C0 - S1 * C0.dot(S1)).normalized()
        S2 = V_((s * 0.86, -0.4, 0.32)).normalized(); C2 = (C0 - S2 * C0.dot(S2)).normalized()
        insect_wing(P, name, fr, hr, S2, C2, 1.0, HLE, HTE, HV)
        insect_wing(P, name, fr, fr, S1, C1, 1.55, FLE, FTE, FV, stigma=(0.58, 0.66, -0.06))
    # ---- her workers circling her
    for k in range(6):
        a = 2 * math.pi * k / 6 + 0.3
        c = V_((math.sin(a) * 1.9, -0.2 + math.cos(a) * 1.7, 0.35 + 0.25 * math.sin(a * 2)))
        worker_bee(P, "SpinWorkers", c, (math.cos(a), -math.sin(a), 0), (0, -0.2, 0.35), 1.15)
    P.part("Muzzle", ball(tuple(tip), (0.05, 0.05, 0.05), 8, 4), "Glow", tuple(tip))
    return P


def ell_patch(c, r, s, phi0, phi1, th0, th1, nu=24, nv=36, thick=0.04):
    """a piece of the ellipsoid (centre c, radii r) on the side s: phi round the long (y) axis from the top (0) down the side, theta along it
    (+ the front); a grid, given a thickness. Returns the mesh and the point function (phi, theta) -> its place."""
    c = V_(c)
    def pt(phi, th):
        p, t = math.radians(phi), math.radians(th)
        return c + V_((s * math.sin(p) * math.cos(t) * r[0], math.sin(t) * r[1], math.cos(p) * math.cos(t) * r[2]))
    bm = bmesh.new()
    grid = [[bm.verts.new(pt(phi0 + (phi1 - phi0) * i / nu, th0 + (th1 - th0) * j / nv)) for j in range(nv + 1)] for i in range(nu + 1)]
    for i in range(nu):
        for j in range(nv): bm.faces.new((grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.faces.ensure_lookup_table(); f0 = bm.faces[len(bm.faces) // 2]
    if f0.normal.dot(f0.calc_center_median() - c) < 0: bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
    bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=thick)
    return bm, pt


def spot_attr(bm, centres, radius):
    """marks a mesh for the bake's round spots: each vertex is told where it lies from the centre of the nearest spot ("spx", "spy", "spz") and
    that spot's radius ("spr") - an offset interpolates exactly across a face, so the bake draws every spot a true circle at any texture size.
    centres: points (each radius r) or (point, r) pairs."""
    lx, ly, lz, lr, lm, ld = (bm.verts.layers.float.new(n) for n in ("spx", "spy", "spz", "spr", "spotted", "spd"))
    bm.verts.ensure_lookup_table()
    cs = [(V_(c[0]), c[1]) if isinstance(c, tuple) and len(c) == 2 and not isinstance(c[0], (int, float)) else (V_(c), radius) for c in centres]
    for v in bm.verts:
        c, r = min(cs, key=lambda cr: (v.co - cr[0]).length - cr[1])
        o = v.co - c; v[lx], v[ly], v[lz], v[lr], v[lm], v[ld] = o.x, o.y, o.z, r, 1.0, o.length - r   # spd: no spot where it is far from one
    return bm


def M2_ladybug():
    """THE GIANT LADYBUG (2026-10-14, remade like the alien / west / treasure / sea bosses): a seven-spot ladybird built like the real
    beetle - a hard round dome; the wing cases (elytra) glossy scarlet with the seven black spots where a seven-spot has them, crisp-edged;
    the black pronotum with its two white patches; the small black head with the white cheek spots, the compound eyes glowing red, short
    clubbed antennae and the sickle mandibles of a hunter that eats aphids alive, open. Six jointed black legs.
    The cartoon idea kept: the knight - an open-faced silver helm framing that face, gold-rimmed, a crest and a red plume streaming back; a
    tournament lance striped red and gold couched at you, a round shield blazoned with his own seven spots and a gold sun boss; daisies
    circling him.
    He flies the way a ladybird really does: the wing cases thrown up and open in a V and held there, and from under them the long amber
    hind wings unfolded and beating (FlapL / FlapR); the daisies circle (SpinDaisies)."""
    P = Boss("ladybug", AB_pal(Base=((0.82, 0.05, 0.03), 0.9), Belly=((0.96, 0.95, 0.9), 0.4), Accent=((0.85, 0.06, 0.05), 0.5), Trim=((0.98, 0.76, 0.22), 0.85),
                               Glass=((0.9, 0.7, 0.38), 0.9), Dark=((0.03, 0.03, 0.035), 0.6), Glow=((1.0, 0.2, 0.06), 0.5), Metal=((0.82, 0.84, 0.88), 0.85),
                               Lamp=((1.0, 0.82, 0.2), 0.8)))
    glow_strength(P, 1.8)
    # ---- the body under the wing cases: the black underside, the abdomen's plates bared on top where the elytra have lifted
    P.obj("Under", ball((0, -0.1, 0.02), (0.66, 0.98, 0.3), 28, 12), "Dark")
    ab = ball((0, -0.2, 0.12), (0.56, 0.82, 0.36), 28, 14)
    P.obj("Abdomen", ab, "Dark")
    # ---- the elytra: two halves of the dome, glossy scarlet, the seven spots; thrown up and open in a V and held there
    EC, ER = V_((0, -0.12, 0.08)), (0.7, 0.98, 0.68)
    for s in (1, -1):
        bm, pt = ell_patch(EC, ER, s, 1.0, 98.0, -86.0, 52.0, 28, 40, 0.045)
        spots = [(pt(3.0, 42.0), 0.1), (pt(56.0, 26.0), 0.12), (pt(66.0, -14.0), 0.2), (pt(30.0, -40.0), 0.17)]
        spot_attr(bm, spots, 0.0)
        hinge = pt(1.0, 48.0)
        R = Matrix.Rotation(math.radians(-24), 3, "X") @ Matrix.Rotation(math.radians(-s * 50), 3, V_((0, 1, 0)))   # out and up, the rear lifted
        xf(bm, R, tuple(hinge - R @ hinge))
        P.obj("Elytron", bm, "Base")
        rim = [pt(1.0 + 97.0 * k / 30, 52.0) for k in range(31)] + [pt(98.0, 52.0 - 138.0 * k / 40) for k in range(1, 41)] + [pt(98.0 - 97.0 * k / 30, -86.0) for k in range(1, 31)]
        P.obj("ElytronRim", xf(pipe(rim, [0.022] * len(rim), 6, False), R, tuple(hinge - R @ hinge)), "Dark")
    # ---- the pronotum: black, the white patches at its front corners
    pr = ball((0, 0.6, 0.3), (0.6, 0.34, 0.3), 30, 14)
    bmesh.ops.delete(pr, geom=[v for v in pr.verts if v.co.z < 0.12], context="VERTS")
    spot_attr(pr, [((s * 0.5, 0.72, 0.26), 0.09) for s in (1, -1)], 0.0)
    P.obj("Pronotum", pr, "Dark")
    # ---- the head: black, white cheek spots, red compound eyes, clubbed antennae, sickle mandibles
    Hc, HR = V_((0, 0.92, 0.2)), (0.3, 0.22, 0.24)
    hd = ball(tuple(Hc), HR, 32, 16)
    spot_attr(hd, [((s * 0.1, 1.11, 0.33), 0.04) for s in (1, -1)], 0.0)
    P.obj("Head", hd, "Dark")
    for s in (1, -1):
        ne = V_((s * 1.0, 0.55, 0.1)).normalized(); ey_ = (V_((0, 1, 0)) - ne * ne.y).normalized(); ez_ = ne.cross(ey_)
        ez_ = ez_ if ez_.z > 0 else -ez_
        fr_ = rh(ne, ey_, ez_); ec_ = Hc + V_((s * 0.22, 0.08, 0.06))
        P.obj("Eye", facet_attrs(oriented_ball(ec_, (0.09, 0.11, 0.14), *fr_, 28, 14), ec_, fr_[1], fr_[0], fr_[2], 7.5), "Glow")
        a0 = Hc + V_((s * 0.13, 0.17, 0.12))
        ant = bez(a0, a0 + V_((s * 0.08, 0.12, 0.1)), a0 + V_((s * 0.18, 0.2, 0.14)), a0 + V_((s * 0.26, 0.26, 0.12)), 8)
        for k in range(8):
            rr = 0.022 if k < 5 else 0.034 + 0.008 * (k - 5)
            P.obj("Antenna", oriented_ball(ant[k].lerp(ant[k + 1], 0.5), (rr, rr * 1.3, rr), *rh(*frame_rh(ant[k + 1] - ant[k])), 8, 4), "Dark")
        m0 = Hc + V_((s * 0.1, 0.17, -0.16))
        mp = bez(m0, m0 + V_((s * 0.14, 0.1, -0.06)), m0 + V_((s * 0.08, 0.27, -0.12)), m0 + V_((-s * 0.04, 0.31, -0.12)), 6)
        P.obj("Mandible", pipe(mp, [0.058, 0.06, 0.054, 0.045, 0.034, 0.02, 0.0], 8), "Dark")
        q = mp[4]; P.obj("Mandible", cone(q, q + V_((-s * 0.05, 0.05, 0.0)), 0.016, 5), "Dark")
        P.obj("Palp", pipe(bez(m0 + V_((0, 0.02, 0.02)), m0 + V_((s * 0.08, 0.06, -0.08)), m0 + V_((s * 0.1, 0.1, -0.14)), m0 + V_((s * 0.08, 0.14, -0.18)), 4),
                           [0.022, 0.02, 0.018, 0.022, 0.012], 6), "Dark")
    # the knight's open-faced helm: silver over the brow, the crown and the back of the head, rimmed in gold, a crest and a red plume
    helm = ball(tuple(Hc + V_((0, -0.03, 0.03))), (0.34, 0.27, 0.29), 32, 16)
    def keep(v):
        d = v.co - (Hc + V_((0, -0.03, 0.03)))
        return not (d.y > 0.12 and d.z < 0.16) and d.z > -0.12   # the face open in front, the rim above the jaw
    bmesh.ops.delete(helm, geom=[v for v in helm.verts if not keep(v)], context="VERTS")
    bmesh.ops.solidify(helm, geom=helm.faces[:], thickness=0.03)
    P.obj("Helm", helm, "Metal")
    hc2 = Hc + V_((0, -0.03, 0.03))
    def Xs(z): return 0.34 * math.sqrt(max(0.0, 1 - (0.12 / 0.27) ** 2 - (z / 0.29) ** 2))
    def Yb(x): return 0.27 * math.sqrt(max(0.0, 1 - (x / 0.34) ** 2 - (0.16 / 0.29) ** 2))
    rimpts = [hc2 + V_((-Xs(z), 0.12, z)) for z in [-0.12 + 0.28 * k / 8 for k in range(9)]]                       # up one cheek
    rimpts += [hc2 + V_((x, Yb(x), 0.16)) for x in [-Xs(0.16) + 2 * Xs(0.16) * k / 12 for k in range(1, 12)]]          # over the brow
    rimpts += [hc2 + V_((Xs(z), 0.12, z)) for z in [0.16 - 0.28 * k / 8 for k in range(9)]]                         # down the other
    P.obj("HelmRim", pipe(rimpts, [0.028] * len(rimpts), 6, False), "Trim")
    P.obj("HelmCrest", pipe([hc2 + V_((0, 0.2, 0.22)), hc2 + V_((0, 0.08, 0.3)), hc2 + V_((0, -0.1, 0.3)), hc2 + V_((0, -0.24, 0.18))], [0.03, 0.04, 0.04, 0.03], 6), "Trim")
    # ---- six jointed black legs; the forefeet hold the lance and the shield
    GR, GL = V_((0.62, 1.05, -0.12)), V_((-0.66, 1.0, -0.06))
    for s in (1, -1):
        g = GR if s > 0 else GL
        hip = V_((s * 0.3, 0.55, -0.18)); knee = hip + V_((s * 0.28, 0.1, -0.12))
        insect_leg(P, [hip, knee, g - V_((s * 0.05, 0.08, 0.02)), g], [0.065, 0.06, 0.05, 0.04], "Dark")
        hip = V_((s * 0.36, 0.1, -0.2)); knee = hip + V_((s * 0.36, 0.0, -0.08))
        insect_leg(P, [hip, knee, knee + V_((s * 0.06, -0.08, -0.32)), knee + V_((s * 0.09, -0.16, -0.48))], [0.065, 0.06, 0.05, 0.035], "Dark")
        hip = V_((s * 0.34, -0.3, -0.2)); knee = hip + V_((s * 0.36, -0.12, -0.06))
        insect_leg(P, [hip, knee, knee + V_((s * 0.06, -0.18, -0.32)), knee + V_((s * 0.08, -0.3, -0.46))], [0.065, 0.06, 0.05, 0.035], "Dark")
    # the tournament lance in his right forefoot, couched at you, striped red and gold in even bands
    d = V_((0.36, 0.9, 0.18)).normalized()
    shaft = [GR - d * 0.5, GR] + [GR + d * (0.2 + 1.4 * i / 14) for i in range(15)]
    P.obj("Lance", pipe(shaft, [0.06, 0.065] + [0.1 * (1 - i / 14) + 0.012 for i in range(15)], 12), lambda c, n, GR=GR, d=d: "Accent" if int(((c - GR).dot(d) + 1.0) / 0.16) % 2 else "Trim")
    P.obj("Vamplate", cone(tuple(GR + d * 0.2), tuple(GR - d * 0.08), 0.22, 18), "Metal")
    tip = GR + d * 1.62
    # the round shield on his left forefoot, his own seven spots on it, a gold rim and a gold sun boss
    sc = V_((-0.82, 1.08, 0.0))
    P.obj("Shield", lathe([(0.0, 0.07), (0.34, 0.04), (0.42, 0.0), (0.4, -0.04), (0.0, -0.05)], 32, "y", tuple(sc)), lambda c, n, sc=sc: "Trim" if (c - sc).length > 0.37 else "Base")
    for x, z, r in ((0.0, 0.27, 0.07), (0.2, 0.12, 0.075), (-0.2, 0.12, 0.075), (0.22, -0.14, 0.07), (-0.22, -0.14, 0.07), (0.1, -0.29, 0.06), (-0.1, -0.29, 0.06)):
        P.obj("ShieldSpot", oriented_ball(sc + V_((x, 0.055, z)), (r, 0.018, r), V_((1, 0, 0)), V_((0, 1, 0)), V_((0, 0, 1)), 14, 5), "Dark")
    P.obj("ShieldBoss", ball(tuple(sc + V_((0, 0.075, 0))), (0.09, 0.05, 0.09), 14, 7), "Trim")
    for k in range(8):
        a = 2 * math.pi * k / 8
        P.obj("ShieldRay", cone(tuple(sc + V_((math.cos(a) * 0.085, 0.075, math.sin(a) * 0.085))), tuple(sc + V_((math.cos(a) * 0.16, 0.07, math.sin(a) * 0.16))), 0.026, 4), "Trim")
    # ---- the hind wings: long, amber, veined, unfolded from under the wing cases, beating
    LE = [(0, -0.01), (0.2, -0.05), (0.5, -0.07), (0.75, -0.05), (0.92, 0.0), (1.0, 0.1)]
    TE = [(0, 0.08), (0.15, 0.22), (0.35, 0.36), (0.6, 0.42), (0.8, 0.38), (0.93, 0.26), (1.0, 0.12)]
    WV = [([(0, -0.01), (0.25, -0.05), (0.48, -0.065)], 0.018), ([(0.0, 0.03), (0.3, 0.0), (0.46, -0.03)], 0.012),
          ([(0.46, -0.06), (0.52, 0.03), (0.44, 0.06), (0.46, -0.03)], 0.01), ([(0.0, 0.08), (0.3, 0.12), (0.6, 0.18), (0.85, 0.2)], 0.011),
          ([(0.0, 0.12), (0.25, 0.22), (0.5, 0.3), (0.7, 0.34)], 0.01), ([(0.0, 0.15), (0.18, 0.26), (0.35, 0.33)], 0.009)]
    for s in (1, -1):
        name = "FlapR" if s > 0 else "FlapL"
        root = V_((s * 0.24, 0.28, 0.42))
        S = V_((s * 0.92, -0.2, 0.32)).normalized(); C0 = V_((0, -0.3, -0.95)); C = (C0 - S * C0.dot(S)).normalized()
        insect_wing(P, name, root, root, S, C, 1.95, LE, TE, WV, stigma=(0.44, 0.52, -0.055), slot_vein="Dark")
    # ---- daisies circling him: white rays round a golden eye, evenly
    for k in range(8):
        a = 2 * math.pi * (k + 0.5) / 8   # none straight in front of his face
        c = V_((math.sin(a) * 2.0, -0.1 + math.cos(a) * 1.8, 0.4 + 0.25 * math.sin(a * 2)))
        fa = V_((0, 0.4, 1)).normalized(); x_, y_, z_ = sq_axes(fa)
        P.part("SpinDaisies", oriented_ball(c, (0.07, 0.07, 0.035), x_, y_, z_, 12, 6), "Lamp", (0, -0.1, 0.4))
        for j in range(16):
            b = 2 * math.pi * j / 16; dvec = x_ * math.cos(b) + y_ * math.sin(b)
            P.part("SpinDaisies", oriented_ball(c + dvec * 0.15, (0.03, 0.085, 0.01), *rh(dvec.cross(z_).normalized(), dvec, z_), 8, 3), "Belly", (0, -0.1, 0.4))
    P.part("Muzzle", ball(tuple(tip), (0.06, 0.06, 0.06), 8, 4), "Glow", tuple(tip))
    return P


def odonate_wing(P, name, hub, root, S, C, L, le, te, veins, slot_web="Glass", slot_vein="Dark", nu=24, nv=6):
    """a dragonfly's wing: the membrane between its leading edge le and trailing edge te (keys (u, v): u 0..1 along the span S from root, v in
    metres back across it along C), its main veins standing on both faces, and the membrane told where each point lies on the wing - "wu",
    "wv" (metres along and across), "wn" (u) and "wle" (metres back from the leading edge) - for the bake to draw the net of small cells, the
    pterostigma and the amber flush at the base. One part, hub the pivot."""
    root, S, C = V_(root), V_(S).normalized(), V_(C).normalized(); N = S.cross(C).normalized()
    def at(u, v): return root + S * (u * L) + C * v
    rows = [[at(u, lerp_keys(u, le) + (lerp_keys(u, te) - lerp_keys(u, le)) * j / nv) for j in range(nv + 1)] for u in [i / nu for i in range(nu + 1)]]
    polys = [[tuple(rows[i][j]), tuple(rows[i + 1][j]), tuple(rows[i + 1][j + 1]), tuple(rows[i][j + 1])] for i in range(nu) for j in range(nv)]
    bm = st_cloth(polys, 0.012)
    lu, lv, ln, ll = (bm.verts.layers.float.new(n) for n in ("wu", "wv", "wn", "wle"))
    bm.verts.ensure_lookup_table()
    for v in bm.verts:
        d = v.co - root; u = d.dot(S) / L; w = d.dot(C)
        v[lu] = u * L; v[lv] = w; v[ln] = u; v[ll] = w - lerp_keys(min(1.0, max(0.0, u)), le)
    P.part(name, bm, slot_web, tuple(hub), 0, True)
    for pts, r in veins:
        q = [at(u, v) for (u, v) in pts]
        if len(q) == 2: q = [q[0], q[0].lerp(q[1], 0.5), q[1]]
        P.part(name, pipe(q, [r] * (len(q) - 1) + [r * 0.5], 5), slot_vein, tuple(hub))


def M2_dragonfly():
    """THE EMERALD DRAGONFLY (2026-10-14, remade like the alien / west / treasure / sea bosses): an emperor of the dragonflies built like the
    real insect - the hunter that catches its prey in the air. Its head is nearly all eye: two great compound eyes wrapping round it and
    meeting on top, glowing emerald through their facets; below them the pale frons with its black T, the hinged labium and the toothed
    mandibles (Odonata: the toothed ones) open. The synthorax leans back, metallic green with dark stripes; the legs are held forward in a
    spiny basket under its chin; the abdomen is long and slender, ten segments with their joints ringed, a pair of claspers at the end.
    The cartoon idea kept: emerald armour banded in gold, two short horns on its crown, a crackling storm orb caught in its basket of legs,
    the tail tipped with light, lightning circling it.
    It flies on four long glass wings, each a net of hundreds of little cells with the dark pterostigma near its tip, the bases flushed
    amber, held raised and beating (FlapL / FlapR); the lightning circles (SpinBolts)."""
    P = Boss("dragonfly", AB_pal(Base=((0.04, 0.42, 0.22), 0.85), Belly=((0.75, 0.85, 0.45), 0.5), Accent=((0.05, 0.75, 0.5), 0.9), Trim=((0.98, 0.76, 0.22), 0.85),
                                 Glass=((0.82, 0.9, 0.92), 0.9), Dark=((0.03, 0.035, 0.03), 0.5), Glow=((0.2, 1.0, 0.55), 0.5), Metal=((0.1, 0.14, 0.12), 0.8),
                                 Lamp=((0.75, 1.0, 1.0), 0.8)))
    glow_strength(P, 2.0)
    # ---- the synthorax, leaning back: metallic green, dark stripes down its sides, a gold band at the front
    T, TR = V_((0, 0.55, 0.32)), (0.34, 0.42, 0.4)
    tb = ball((0, 0, 0), TR, 28, 14); Rt = Matrix.Rotation(math.radians(-28), 3, "X")
    xf(tb, Rt, tuple(T))
    P.obj("Thorax", tb, "Base")
    P.obj("ThoraxBand", xf(ring_on(V_((0, 0.3, 0)), (0, 1, 0), 0.3, 0.03, 32, 6), Rt, tuple(T)), "Trim")   # a gold band round its front
    # ---- the abdomen: ten segments, slender, the joints ringed gold, claspers at the end, its tip alight
    A = [V_(p) for p in ((0, 0.2, 0.18), (0, -0.4, 0.06), (0, -1.1, -0.08), (0, -1.8, -0.2), (0, -2.45, -0.3), (0, -2.85, -0.3))]
    sp, us = resample(st_spline(A, 8), 90); FR = spine_frames(sp); AL = us[-1]
    def arad(u):
        return lerp_keys(u, [(0, 0.2), (0.05, 0.22), (0.1, 0.13), (0.2, 0.12), (0.6, 0.11), (0.85, 0.1), (0.95, 0.11), (1, 0.06)])
    SEG = [0.0, 0.06, 0.13, 0.23, 0.33, 0.43, 0.53, 0.63, 0.73, 0.83, 1.0]
    def segu(u):
        for k in range(10):
            if u < SEG[k + 1]: return k, (u - SEG[k]) / (SEG[k + 1] - SEG[k])
        return 9, 1.0
    RA = [arad(x / AL) * (0.94 + 0.08 * segu(x / AL)[1]) for x in us]
    def apaint(c, n):
        i = min(range(len(sp)), key=lambda k: (sp[k] - c).length_squared); k, f = segu(us[i] / AL)
        return "Trim" if f < 0.06 else "Base"
    P.obj("Abdomen", st_loft(sp, RA, RA, [r * 0.9 for r in RA], FR, 20, 1.05), apaint)
    for k in range(1, 10):   # a gold ring at each joint
        i = int(SEG[k] * (len(sp) - 1)); t, side, up = FR[i]
        P.obj("Ring", ring_on(sp[i], t, RA[i] * 1.0, 0.018, 20, 5), "Trim")
    tip = sp[-1]; td = FR[-1][0]
    P.obj("TailLight", ball(tuple(tip + td * 0.04), (0.07, 0.07, 0.07), 12, 6), "Lamp")
    for s in (1, -1):
        cl = bez(tip, tip + td * 0.15 + V_((s * 0.05, 0, 0.0)), tip + td * 0.3 + V_((s * 0.1, 0, -0.02)), tip + td * 0.4 + V_((s * 0.06, 0, -0.06)), 5)
        P.obj("Clasper", pipe(cl, [0.035, 0.03, 0.025, 0.02, 0.012, 0.0], 6), "Dark")
    # ---- the head: two great compound eyes meeting on top, the frons with its T, the labium, the mandibles, two horns on the crown
    Hc = V_((0, 1.08, 0.5))
    P.obj("Head", ball(tuple(Hc), (0.3, 0.2, 0.26), 24, 12), "Base")
    for s in (1, -1):
        ec = Hc + V_((s * 0.19, 0.02, 0.07)); ne = V_((s * 0.75, 0.5, 0.42)).normalized()
        ey_ = (V_((0, 1, 0)) - ne * ne.y).normalized(); ez_ = ne.cross(ey_); ez_ = ez_ if ez_.z > 0 else -ez_
        fr_ = rh(ne, ey_, ez_)
        P.obj("Eye", facet_attrs(oriented_ball(ec, (0.26, 0.29, 0.3), *fr_, 40, 20), ec, fr_[1], fr_[0], fr_[2], 9.0), "Glow")
        P.obj("Horn", pipe(bez(Hc + V_((s * 0.06, -0.08, 0.3)), Hc + V_((s * 0.08, -0.12, 0.42)), Hc + V_((s * 0.12, -0.2, 0.5)), Hc + V_((s * 0.16, -0.3, 0.52)), 6),
                           [0.04, 0.036, 0.03, 0.024, 0.016, 0.008, 0.0], 6), "Trim")
        # the mandible: a toothed blade, open
        m0 = Hc + V_((s * 0.12, 0.16, -0.22))
        mp = bez(m0, m0 + V_((s * 0.16, 0.09, -0.06)), m0 + V_((s * 0.1, 0.26, -0.14)), m0 + V_((-s * 0.02, 0.3, -0.15)), 6)
        P.obj("Mandible", pipe(mp, [0.062, 0.065, 0.06, 0.05, 0.038, 0.022, 0.0], 8), "Metal")
        for k in (2, 3, 4):
            P.obj("MandibleTooth", cone(mp[k], mp[k] + V_((-s * 0.07, 0.025, -0.01)), 0.02, 5), "Belly")
    P.obj("Frons", oriented_ball(Hc + V_((0, 0.2, -0.04)), (0.16, 0.09, 0.13), V_((1, 0, 0)), V_((0, 1, 0)), V_((0, 0, 1)), 18, 9), "Base")
    P.obj("Labium", oriented_ball(Hc + V_((0, 0.1, -0.3)), (0.12, 0.08, 0.045), V_((1, 0, 0)), V_((0, 1, 0)), V_((0, 0, 1)), 16, 8), "Belly")
    # ---- the legs held forward in a spiny basket under its chin, gripping the storm orb
    orb = V_((0, 1.1, -0.38))
    for s in (1, -1):
        for k in range(3):
            hip = T + Rt @ V_((s * 0.14, 0.26 - 0.18 * k, -0.32)); knee = hip + V_((s * 0.24, 0.12 + 0.04 * k, -0.12))
            grip = orb + V_((s * 0.2 * math.cos(0.5 * k), 0.08 - 0.16 * k, 0.05 - 0.1 * k))
            insect_leg(P, [hip, knee, grip + V_((s * 0.05, 0, 0.06)), grip], [0.04, 0.04, 0.032, 0.02], "Dark")
            for j in range(5):   # the spines along the shin
                q = knee.lerp(grip, 0.2 + 0.15 * j); dd = (grip - knee).normalized(); out = dd.cross(V_((0, 0, 1))).normalized() * (-s)
                P.obj("Spine", cone(q, q + (out * 0.7 + V_((0, 0, -0.5)) - dd * 0.3).normalized() * 0.06, 0.008, 4), "Dark")
    P.obj("StormOrb", ball(tuple(orb), (0.17, 0.17, 0.17), 20, 10), "Glass")
    P.obj("StormCore", ball(tuple(orb), (0.1, 0.1, 0.1), 14, 7), "Lamp")
    for k in range(6):
        a = 2 * math.pi * k / 6 + 0.3
        P.obj("Crackle", pipe(bolt_pts(orb, orb + V_((math.cos(a) * 0.3, math.sin(a) * 0.15, 0.12 * (k % 2) - 0.06)), 3, 0.04), [0.018, 0.016, 0.012, 0.0], 4), "Lamp")
    # ---- four long glass wings, each a net of small cells, raised and beating
    FLE = [(0, -0.02), (0.1, -0.06), (0.4, -0.08), (0.7, -0.075), (0.9, -0.05), (1.0, 0.03)]
    FTE = [(0, 0.06), (0.08, 0.16), (0.3, 0.24), (0.6, 0.26), (0.85, 0.22), (0.97, 0.12), (1.0, 0.05)]
    HTE = [(0, 0.1), (0.08, 0.34), (0.25, 0.4), (0.55, 0.34), (0.85, 0.24), (0.97, 0.12), (1.0, 0.05)]
    def wveins(te):
        mid = [(u, (lerp_keys(u, FLE) + lerp_keys(u, te)) * 0.5) for u in (0.0, 0.3, 0.6, 0.9)]
        return [([(0, -0.02), (0.4, -0.08), (0.7, -0.075), (0.98, 0.0)], 0.016),                              # the costa
                ([(0.0, 0.0), (0.45, -0.045), (0.82, -0.04)], 0.011),                                         # subcosta and radius
                (mid, 0.01), ([(0.0, 0.05), (0.35, 0.12), (0.75, 0.13)], 0.009),                              # media, cubitus
                ([(0.45, -0.08), (0.46, -0.03)], 0.012)]                                                     # the nodus
    for s in (1, -1):
        name = "FlapR" if s > 0 else "FlapL"
        hub = T + Rt @ V_((s * 0.12, 0.05, 0.36))
        C0 = V_((0, -0.35, -0.94))
        for root, L, S_, te in ((hub + V_((0, 0.12, 0.02)), 2.35, V_((s * 0.93, 0.1, 0.36)), FTE), (hub + V_((0, -0.12, 0.0)), 2.2, V_((s * 0.9, -0.22, 0.32)), HTE)):
            S_ = S_.normalized(); C_ = (C0 - S_ * C0.dot(S_)).normalized()
            odonate_wing(P, name, hub, root, S_, C_, L, FLE, te, wveins(te))
    # ---- lightning circling it
    for k in range(6):
        a = 2 * math.pi * (k + 0.5) / 6
        c = V_((math.sin(a) * 2.2, -0.5 + math.cos(a) * 2.0, 0.3 + 0.25 * math.sin(a * 2)))
        P.part("SpinBolts", pipe(bolt_pts(c + V_((0, 0, 0.34)), c + V_((0, 0, -0.34)), 5, 0.09), [0.03, 0.03, 0.026, 0.022, 0.016, 0.0], 5), "Lamp", (0, -0.5, 0.3))
    mz = Hc + V_((0, 0.3, -0.2))
    P.part("Muzzle", ball(tuple(mz), (0.03, 0.03, 0.03), 6, 3), "Glow", tuple(mz))
    return P


def petal_mesh(L, W, curl, twist=0.0, nu=10, nv=4, thick=0.035):
    """a ray petal along +z from the origin, lying in the x-z plane: long and pointed, widest past the middle, cupped a little, its tip curled
    toward +y by curl and twisted; marked for the bake with "pu" (0 at the base, 1 at the tip) and "pv" (-1 .. 1 across)."""
    bm = bmesh.new(); grid = []
    for i in range(nu + 1):
        t = i / nu; w = W * 0.5 * (0.3 + 0.95 * math.sin(math.pi * min(1.0, t * 1.1)) ** 0.7) * (1 - t ** 3)
        row = []
        for j in range(nv + 1):
            v = -1 + 2 * j / nv
            x = v * w; y = curl * t * t + 0.04 * W * (1 - v * v) * math.sin(math.pi * t); z = L * t
            a = math.radians(twist) * t; x, y = x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)
            row.append(bm.verts.new((x, y, z)))
        grid.append(row)
    for i in range(nu):
        for j in range(nv): bm.faces.new((grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=thick)
    lu, lv = bm.verts.layers.float.new("pu"), bm.verts.layers.float.new("pv"); bm.verts.ensure_lookup_table()
    for v in bm.verts:
        t = max(0.0, min(1.0, v.co.z / L)); w = W * 0.5 * (0.3 + 0.95 * math.sin(math.pi * min(1.0, t * 1.1)) ** 0.7) * (1 - t ** 3) + 1e-4
        v[lu] = t; v[lv] = max(-1.0, min(1.0, v.co.x / w))
    return bm


def leaf_blade(L, W, n=14, m=6, thick=0.03):
    """a heart-shaped sunflower leaf along +x from its stalk, lying in the x-y plane: a cordate blade with a saw-toothed edge, cupped a
    little; marked with "lu" (0 at the stalk, 1 at the tip) and "lv" (-1 .. 1 across) for the bake's veins. Returns the mesh and its outline."""
    bm = bmesh.new(); grid = []
    def half(t):   # the half width at t, the heart's lobes behind the stalk, a tooth every so often along the edge
        base = W * 0.5 * (math.sin(math.pi * min(1.0, (t + 0.12) / 1.12)) ** 0.75) * (1.0 - 0.15 * t)
        tooth = 1.0 + 0.06 * (1 if int(t * 22) % 2 == 0 else -1) * min(1.0, t * 4)
        return base * tooth
    for i in range(n + 1):
        t = i / n; row = []
        for j in range(m + 1):
            v = -1 + 2 * j / m; x = L * (t - 0.08 * (1 - v * v) * (1 - t)); y = v * half(t)
            row.append(bm.verts.new((x, y, 0.05 * L * (1 - v * v) * math.sin(math.pi * t) - 0.06 * L * t * t)))
        grid.append(row)
    for i in range(n):
        for j in range(m): bm.faces.new((grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=thick)
    lu, lv = bm.verts.layers.float.new("lu"), bm.verts.layers.float.new("lv"); bm.verts.ensure_lookup_table()
    for v in bm.verts:
        t = max(0.0, min(1.0, v.co.x / L)); v[lu] = t; v[lv] = max(-1.0, min(1.0, v.co.y / (half(t) + 1e-4)))
    return bm


def M2_evilflower():
    """THE DEMON SUNFLOWER (2026-10-14, remade like the alien / west / treasure / sea bosses): a giant sunflower gone bad, built like the real
    plant. Its face is a real sunflower head: hundreds of seeds packed in the golden-angle spiral, so the two sets of spirals show, dark
    in the middle and opening into golden florets round the rim - and across it a gaping maw ringed with two rows of seed-fangs, a toxic
    green glow deep in its throat, drool hanging; two slanted eyes blaze among the seeds and four small ones stare. Round it the ray petals
    of a crimson sunflower (a 'Velvet Queen'), veined, gold at the tips, curling toward you like claws and turning slowly; behind them the
    bracts, dark and spiked. A thick bristling stem with thorns, two thorny whips with snapping buds, a torn-out tangle of roots hanging
    with clods of earth, and seeds it spits circling it.
    It flies on its leaves: its two great heart-shaped leaves, saw-edged and veined, spread wide like wings and beating (FlapL / FlapR);
    the petals turn (RollPetals), the whips lash (Sway*), the spat seeds circle (SpinSeeds)."""
    P = Boss("evilflower", AB_pal(Base=((0.1, 0.28, 0.08), 0.45), Belly=((0.98, 0.7, 0.08), 0.5), Accent=((0.55, 0.03, 0.06), 0.5),
                                  Trim=((0.98, 0.78, 0.16), 0.6), Glass=((0.96, 0.94, 0.82), 0.7), Dark=((0.05, 0.03, 0.02), 0.4),
                                  Glow=((0.55, 1.0, 0.15), 0.5), Metal=((0.24, 0.13, 0.05), 0.4), Lamp=((1.0, 0.25, 0.05), 0.8)))
    glow_strength(P, 2.0)
    FC = V_((0, 0.3, 1.05)); RD = 0.76                   # the face: a shallow dome bulging toward you
    MC = (0.0, -0.2); MR = (0.33, 0.19)                  # the maw, in the face's own (x, z)
    def fy(r): return 0.17 * (1 - min(1.0, r / RD) ** 2.2)
    def fpt(x, z, out=0.0): return FC + V_((x, fy(math.hypot(x, z)) + out, z))
    # the disc, built as rings from the maw's lip out to the rim, so the maw is a clean hole
    NA, NR = 64, 14; bm = bmesh.new(); rings = []
    for i in range(NR + 1):
        f = i / NR; ring = []
        for j in range(NA):
            a = 2 * math.pi * j / NA
            ix, iz = MC[0] + MR[0] * math.cos(a), MC[1] + MR[1] * math.sin(a)
            ox, oz = RD * math.cos(a), RD * math.sin(a)
            x, z = ix + (ox - ix) * f, iz + (oz - iz) * f
            ring.append(bm.verts.new(fpt(x, z)))
        rings.append(ring)
    for r0, r1 in zip(rings, rings[1:]):
        for j in range(NA): bm.faces.new((r0[j], r1[j], r1[(j + 1) % NA], r0[(j + 1) % NA]))
    back = [bm.verts.new(FC + V_((RD * 0.98 * math.cos(2 * math.pi * j / NA), -0.14, RD * 0.98 * math.sin(2 * math.pi * j / NA)))) for j in range(NA)]
    for j in range(NA): bm.faces.new((rings[-1][j], back[j], back[(j + 1) % NA], rings[-1][(j + 1) % NA]))
    bm.faces.new(list(reversed(back)))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    P.obj("Disc", bm, "Metal")
    # the seeds: the golden-angle spiral, dark in the middle, golden florets round the rim; none in the maw or the eyes
    EYES = [(s * 0.27, 0.2, 0.13) for s in (1, -1)]; SMALL = [(s * 0.17, 0.46, 0.05) for s in (1, -1)] + [(s * 0.5, 0.33, 0.045) for s in (1, -1)]
    seeds = {}
    N = 420
    for k in range(1, N):
        r = RD * 0.97 * math.sqrt(k / N); a = k * math.radians(137.508)
        x, z = r * math.cos(a), r * math.sin(a)
        if ((x - MC[0]) / (MR[0] + 0.05)) ** 2 + ((z - MC[1]) / (MR[1] + 0.05)) ** 2 < 1: continue
        if any(math.hypot(x - ex, z - ez) < er + 0.05 for ex, ez, er in EYES + SMALL): continue
        c = fpt(x, z); nn = V_((-(fy(r + 0.01) - fy(r)) / 0.01 * x / max(r, 1e-4), 1.0, -(fy(r + 0.01) - fy(r)) / 0.01 * z / max(r, 1e-4))).normalized()
        sz = 0.024 + 0.008 * (r / RD)
        slot = "Belly" if r > 0.6 else "Metal"
        bmS = seeds.setdefault(slot, bmesh.new())
        xa, ya, za = sq_axes(nn); rad = V_((x, 0, z)).normalized() if r > 1e-3 else xa
        ring = [bmS.verts.new(c + (xa * math.cos(math.pi * q / 4) + ya * math.sin(math.pi * q / 4)) * sz) for q in range(8)]
        mid = [bmS.verts.new(c + nn * 0.014 + (xa * math.cos(math.pi * q / 4) + ya * math.sin(math.pi * q / 4)) * sz * 0.7) for q in range(8)]
        apex = bmS.verts.new(c + nn * (0.032 if slot == "Belly" else 0.022) + rad * 0.004)
        for q in range(8):
            bmS.faces.new((ring[q], ring[(q + 1) % 8], mid[(q + 1) % 8], mid[q])); bmS.faces.new((mid[q], mid[(q + 1) % 8], apex))
    for slot, bmS in seeds.items():
        bmesh.ops.recalc_face_normals(bmS, faces=bmS.faces); ob = P.obj("Seed", bmS, slot)
        at = ob.data.attributes.new("small", "INT", "FACE"); at.data.foreach_set("value", [1] * len(ob.data.polygons))
    # the maw: a dark throat, the toxic glow in it, two rows of seed-fangs round the lip, drool
    mc = fpt(MC[0], MC[1], -0.02)
    P.obj("Throat", ball(tuple(mc + V_((0, -0.12, 0))), (MR[0] * 1.05, 0.2, MR[1] * 1.1), 20, 10), "Dark")
    P.obj("Gullet", ball(tuple(mc + V_((0, -0.16, -0.02))), (0.15, 0.06, 0.08), 14, 7), "Glow")
    P.obj("MawLip", pipe([fpt(MC[0] + MR[0] * math.cos(a), MC[1] + MR[1] * math.sin(a), 0.01) for a in [2 * math.pi * k / 40 for k in range(41)]], [0.03] * 41, 6), "Accent")
    for row, (n, L, rr, k0) in enumerate(((18, 0.62, 0.032, 0.0), (18, 0.4, 0.024, 0.5))):
        for k in range(n):
            a = 2 * math.pi * (k + k0) / n
            rim = fpt(MC[0] + MR[0] * math.cos(a) * (1 - 0.08 * row), MC[1] + MR[1] * math.sin(a) * (1 - 0.08 * row), -0.01 - 0.03 * row)
            tgt = fpt(MC[0] + MR[0] * math.cos(a) * 0.25, MC[1] + MR[1] * math.sin(a) * 0.25, -0.05)
            P.obj("Fang", cone(rim, rim + (tgt - rim) * L + V_((0, 0.04, 0)), rr, 6), "Glass")
    for k, (x, dz) in enumerate(((-0.18, 0.2), (0.04, 0.3), (0.2, 0.16))):   # drool
        b = fpt(MC[0] + x, MC[1] - MR[1] * 0.85, 0.01)
        P.obj("Drool", pipe([b, b + V_((0, 0.02, -dz * 0.5)), b + V_((0, 0.03, -dz))], [0.022, 0.016, 0.01], 6), "Glow")
        P.obj("Drip", ball(tuple(b + V_((0, 0.03, -dz - 0.04))), (0.035, 0.035, 0.05), 8, 4), "Glow")
    # the eyes: two slanted blazing ones in sockets, four small ones staring
    for (x, z, er), big in [(e, True) for e in EYES] + [(e, False) for e in SMALL]:
        s = 1 if x > 0 else -1; c = fpt(x, z, 0.0)
        tilt = Matrix.Rotation(math.radians(-s * (22 if big else 10)), 3, "Y")   # the outer corners up: a glare
        P.obj("Socket", xf(ball((0, 0, 0), (er * 1.35, 0.05, er * 0.85), 18, 6), tilt, tuple(c - V_((0, 0.02, 0)))), "Dark")
        P.obj("Eye" if big else "SeedEye", xf(ball((0, 0, 0), (er, 0.055, er * 0.6), 18, 8), tilt, tuple(c + V_((0, 0.01, 0)))), "Lamp")
        P.obj("Pupil", xf(ball((0, 0, 0), (er * 0.16, 0.03, er * 0.55), 10, 5), tilt, tuple(c + V_((0, 0.055, 0)))), "Dark")
        if big:
            P.obj("Brow", xf(pipe([V_((-s * er * 1.35, 0.03, er * 0.3)), V_((0, 0.02, er * 0.9)), V_((s * er * 1.25, 0, er * 1.25))], [0.03, 0.045, 0.035], 8), tilt, tuple(c)), "Accent")
    # ---- the ray petals: two whorls of crimson petals, gold at the tips, curling toward you like claws, turning
    for whorl, (n, L, W, curl, off, dy, tw) in enumerate(((17, 0.98, 0.3, 0.42, 0.0, -0.03, 14), (17, 0.82, 0.26, 0.3, 0.5, -0.09, -12))):
        for k in range(n):
            a = 2 * math.pi * (k + off) / n
            pm = petal_mesh(L, W, curl, tw if k % 2 else -tw)
            Rm = Matrix.Rotation(-a, 3, "Y")    # the petal's +z swung round the face
            xf(pm, Rm, tuple(FC + Rm @ V_((0, dy, RD * 0.93))))
            P.part("RollPetals", pm, "Accent", tuple(FC), 0)
    # the bracts behind them, dark and spiked
    for k in range(22):
        a = 2 * math.pi * (k + 0.25) / 22; d = V_((math.sin(a), 0, math.cos(a)))
        b = FC + d * (RD * 0.82) + V_((0, -0.16, 0)); L = 0.55 if k % 2 else 0.42
        tipb = b + d * L + V_((0, -0.12, 0)) + V_((0, 0, 0))
        P.obj("Bract", hull([tuple(b + d.cross(V_((0, 1, 0))) * 0.07), tuple(b - d.cross(V_((0, 1, 0))) * 0.07), tuple(b + V_((0, 0.03, 0))), tuple(b + V_((0, -0.04, 0))),
                             tuple(b.lerp(tipb, 0.5) + V_((0, 0.01, 0))), tuple(tipb)]), lambda c, n, b=b, tipb=tipb: "Lamp" if (c - b).length > (tipb - b).length * 0.82 else "Base")
    # ---- the stem: thick, bristling, a few thorns
    stem = bez(FC + V_((0, -0.22, -0.2)), FC + V_((0, -0.55, -0.85)), V_((0, 0.15, -0.1)), V_((0, 0.0, -0.85)), 12)
    rs = [0.17, 0.165, 0.16, 0.155, 0.15, 0.15, 0.15, 0.155, 0.16, 0.17, 0.18, 0.2, 0.22]
    P.obj("Stem", pipe(stem, rs, 16), "Base")
    for i in range(2, 12, 2):
        t = (stem[i + 1] - stem[i - 1]).normalized(); sd = t.cross(V_((0, 0, 1))); sd = sd.normalized() if sd.length > 1e-3 else V_((1, 0, 0)); up = sd.cross(t)
        for q in range(3):
            a = 2 * math.pi * (q / 3 + i * 0.13); o = (sd * math.cos(a) + up * math.sin(a)).normalized()
            P.obj("Thorn", cone(stem[i] + o * rs[i] * 0.9, stem[i] + o * (rs[i] + 0.16) + t * 0.05, 0.04, 6), "Accent")
    coat = Coat("Bristle")
    for i in range(1, 12):   # the stiff hairs of a sunflower stem, in rings
        t = (stem[i + 1] - stem[i - 1]).normalized(); sd = t.cross(V_((0, 0, 1))); sd = sd.normalized() if sd.length > 1e-3 else V_((1, 0, 0)); up = sd.cross(t)
        for q in range(14):
            a = 2 * math.pi * (q + 0.5 * (i % 2)) / 14; o = (sd * math.cos(a) + up * math.sin(a)).normalized()
            coat.add("Base", stem[i] + o * rs[i] * 0.95, (o + t * 0.6).normalized(), 0.06, 0.01, t, o, 0.0)
    coat.put(P)
    # the leaves: two great ones spread like wings and beating, two smaller ones hanging lower
    for s in (1, -1):
        name = "FlapR" if s > 0 else "FlapL"
        hub = FC + V_((s * 0.1, -0.5, -0.62))
        stalk = bez(hub, hub + V_((s * 0.3, 0.0, 0.15)), hub + V_((s * 0.55, -0.02, 0.4)), hub + V_((s * 0.7, -0.04, 0.55)), 5)
        P.part(name, pipe(stalk, [0.06, 0.055, 0.05, 0.045, 0.042, 0.04], 8), "Base", tuple(hub))
        lb = leaf_blade(2.25, 1.55)
        if s < 0:
            for v in lb.verts: v.co.x = -v.co.x
            bmesh.ops.reverse_faces(lb, faces=lb.faces)
        Rl = Matrix.Rotation(math.radians(-s * 38), 3, "Y") @ Matrix.Rotation(math.radians(-72), 3, "X")   # raised high, its face toward you
        xf(lb, Rl, tuple(stalk[-1]))
        P.part(name, lb, "Base", tuple(hub), 0)
        mid = [stalk[-1] + Rl @ V_((s * 2.25 * t, 0, 0.05 * 2.25 * math.sin(math.pi * t) - 0.06 * 2.25 * t * t + 0.016)) for t in [k / 10 for k in range(11)]]
        P.part(name, pipe(mid, [0.032 - 0.0025 * k for k in range(11)], 6), "Belly", tuple(hub))
    for s in (1, -1):
        lb = leaf_blade(0.95, 0.7)
        if s < 0:
            for v in lb.verts: v.co.x = -v.co.x
            bmesh.ops.reverse_faces(lb, faces=lb.faces)
        Rl = Matrix.Rotation(math.radians(s * 50), 3, "Y") @ Matrix.Rotation(math.radians(30), 3, "X")
        b0 = stem[9]
        P.obj("Leaf", xf(lb, Rl, tuple(b0 + V_((s * 0.15, 0, 0)))), "Base")
    # two thorny whips with snapping buds, lashing
    for s in (1, -1):
        hub = stem[7] + V_((s * 0.12, 0.05, 0.0))
        name = "SwayR" if s > 0 else "SwayL"
        vine = bez(hub, hub + V_((s * 0.6, 0.2, -0.1)), hub + V_((s * 1.05, 0.7, -0.4)), hub + V_((s * 0.95, 1.25, -0.15)), 12)
        vr = [0.085 - 0.06 * i / 12 for i in range(13)]
        P.part(name, pipe(vine, vr, 8), "Base", tuple(hub))
        for i in range(1, 12, 2):
            t = (vine[i + 1] - vine[i - 1]).normalized(); o = V_((0, 0, 1 if i % 4 == 1 else -1))
            P.part(name, cone(vine[i] + o * vr[i] * 0.8, vine[i] + o * (vr[i] + 0.11) + t * 0.04, 0.03, 5), "Accent", tuple(hub))
        tipc = vine[-1]; td = (vine[-1] - vine[-3]).normalized()
        for k in range(5):   # a bud of a mouth, its sepals open like jaws, glowing inside
            a = 2 * math.pi * k / 5
            o = (td.cross(V_((0, 0, 1))).normalized() * math.cos(a) + V_((0, 0, 1)) * math.sin(a)).normalized()
            P.part(name, cone(tipc + o * 0.06, tipc + o * 0.16 + td * 0.14, 0.045, 5), "Accent", tuple(hub))
        P.part(name, ball(tuple(tipc + td * 0.03), (0.06, 0.06, 0.06), 10, 5), "Glow", tuple(hub))
    # ---- the roots torn from the ground: the taproot and its laterals, clods of earth caught in them
    base = stem[-1]
    P.obj("RootCrown", ball(tuple(base + V_((0, 0, -0.06))), (0.26, 0.24, 0.18), 18, 9), "Metal")
    P.obj("Taproot", pipe(bez(base, base + V_((0, 0.02, -0.4)), base + V_((0.05, 0.0, -0.8)), base + V_((0.0, 0.03, -1.15)), 8),
                          [0.16, 0.13, 0.11, 0.09, 0.07, 0.05, 0.035, 0.02, 0.0], 10), "Metal")
    for k in range(10):
        a = 2 * math.pi * k / 10; d = V_((math.cos(a), math.sin(a), 0)); z0 = -0.08 - 0.07 * (k % 3)
        r = bez(base + d * 0.12 + V_((0, 0, z0)), base + d * 0.45 + V_((0, 0, z0 - 0.12)), base + d * 0.58 + V_((0, 0, z0 - 0.45)), base + d * 0.5 + V_((0, 0, z0 - 0.78)), 7)
        P.obj("Root", pipe(r, [0.06, 0.052, 0.045, 0.036, 0.028, 0.02, 0.012, 0.0], 6), "Metal")
        if k % 3 == 0: P.obj("Clod", ball(tuple(r[3]), (0.12, 0.11, 0.09), 10, 5), "Dark")
    # ---- the seeds it spits, circling it: striped sunflower seeds
    for k in range(12):
        a = 2 * math.pi * k / 12
        c = V_((math.sin(a) * 1.75, 0.2 + math.cos(a) * 1.35, 0.55 + 0.4 * math.sin(a * 3)))
        dirn = V_((math.cos(a), -math.sin(a), 0.2)).normalized()
        P.part("SpinSeeds", oriented_ball(c, (0.06, 0.11, 0.03), *rh(dirn.cross(V_((0, 0, 1))).normalized(), dirn, V_((0, 0, 1))), 10, 5), "Metal", (0, 0.2, 0.55))
        for q in (-1, 1):
            P.part("SpinSeeds", pipe([c + dirn * -0.1 + V_((0, 0, 0.028)) + dirn.cross(V_((0, 0, 1))).normalized() * q * 0.025,
                                      c + dirn * 0.1 + V_((0, 0, 0.028)) + dirn.cross(V_((0, 0, 1))).normalized() * q * 0.025], [0.01, 0.01], 4), "Glass", (0, 0.2, 0.55))
    mz = mc + V_((0, -0.05, 0))
    P.part("Muzzle", ball(tuple(mz), (0.02, 0.02, 0.02), 6, 3), "Dark", tuple(mz))
    return P


def bm_join(bms):
    """several little meshes made one (dozens of teeth, windows, beads as a single part)."""
    out = bmesh.new()
    for b in bms:
        m = {v: out.verts.new(v.co) for v in b.verts}
        for f in b.faces:
            try: out.faces.new([m[v] for v in f.verts])
            except ValueError: pass
        b.free()
    return out


def small(ob):
    """marks a part as little repeated pieces: the bake gives them one swatch of the atlas between them instead of room of their own."""
    at = ob.data.attributes.get("small") or ob.data.attributes.new("small", "INT", "FACE")
    at.data.foreach_set("value", [1] * len(ob.data.polygons)); return ob


def conispiral(SC, Z, X, R0=0.8, turns=4.5, rise=0.9, tube=0.58, nu=198, nv=24, piece=22):
    """a snail's shell: a right-handed (dextral) conispiral coiled about the axis Z through SC - the apex up the axis, each whorl twice as
    wide as the one before, R0 across at the mouth, which lies out along X - the tube round each coil tube * its radius, so the whorls lap
    over each other at the suture; the mouth left open (the body fills it). Marked for the bake: "su" from the apex (0) to the mouth (1),
    "sc", "ss" the cosine and sine of the angle round the tube (0 on the outer rim of the coil, a quarter turn on toward the base).
    Built in pieces of `piece` rings a hair apart (each half a turn): unwrapped whole, the overlapping whorls would lie on top of each
    other in the atlas. Returns the mesh and its mouth (centre, radius, the way the tube runs out of it)."""
    SC, Z = V_(SC), V_(Z).normalized(); X = V_(X); X = (X - Z * X.dot(Z)).normalized(); Y = Z.cross(X)
    T = turns * 2 * math.pi; k = math.log(25.0) / T
    def path(t):
        R = R0 * math.exp(-k * (T - t)); ph = T - t
        return SC + (X * math.cos(ph) + Y * math.sin(ph)) * R + Z * (rise * (R0 - R)), R
    bm = bmesh.new()
    lu, lc, ls = bm.verts.layers.float.new("su"), bm.verts.layers.float.new("sc"), bm.verts.layers.float.new("ss")
    rows = []
    for i in range(nu + 1):
        t = T * (0.02 + 0.98 * i / nu); p, R = path(t)
        tg = (path(t + 0.01)[0] - path(t - 0.01)[0]).normalized()
        inward = (SC + Z * (rise * (R0 - R))) - p; inward = (inward - tg * inward.dot(tg)).normalized(); bi = tg.cross(inward)
        rows.append((tg, [p + (-inward * math.cos(2 * math.pi * j / nv) + bi * math.sin(2 * math.pi * j / nv)) * (tube * R) for j in range(nv)]))
    def ring(i, nudge=0.0):
        tg, ps = rows[i]; out = []
        for j, q in enumerate(ps):
            v = bm.verts.new(q + tg * nudge); a = 2 * math.pi * j / nv; v[lu] = i / nu; v[lc] = math.cos(a); v[ls] = math.sin(a); out.append(v)
        return out
    for i0 in range(0, nu, piece):
        i1 = min(nu, i0 + piece); prev = ring(i0, 0.0 if i0 == 0 else 2e-4)
        if i0 == 0: bm.faces.new(prev)                                                          # the apex closed
        for i in range(i0 + 1, i1 + 1):
            cur = ring(i)
            for j in range(nv): bm.faces.new((prev[j], cur[j], cur[(j + 1) % nv], prev[(j + 1) % nv]))   # wound to face outward
            prev = cur
    pm, Rm = path(T)
    return bm, (pm, tube * Rm, (pm - path(T - 0.01)[0]).normalized())


def guard_bee(P, name, c, fwd, hub, k=1.0):
    """one of the Snail King's guards: a worker bumblebee flying along fwd - black thorax fur with a yellow collar, a yellow abdomen banded
    black with a pale tail, a dark head with its eyes, two smoky wings raised, a gold helmet, a gold spear levelled ahead; part of the mover
    name."""
    c = V_(c); f = V_(fwd).normalized(); sd = f.cross(V_((0, 0, 1))).normalized(); up = sd.cross(f); fr = rh(sd, f, up)
    def put(bm, sl): P.part(name, bm, sl, tuple(hub))
    put(oriented_ball(c, (0.085 * k, 0.085 * k, 0.08 * k), *fr, 12, 6), "Dark")
    put(oriented_ball(c + f * 0.03 * k + up * 0.012 * k, (0.08 * k, 0.045 * k, 0.07 * k), *fr, 10, 5), "Lamp")
    ab = c - f * 0.15 * k - up * 0.03 * k
    put(oriented_ball(ab, (0.078 * k, 0.125 * k, 0.072 * k), *fr, 12, 6), "Lamp")
    put(oriented_ball(ab - f * 0.01 * k, (0.081 * k, 0.03 * k, 0.075 * k), *fr, 12, 4), "Dark")
    put(oriented_ball(ab - f * 0.1 * k, (0.055 * k, 0.04 * k, 0.05 * k), *fr, 8, 4), "Belly")
    hd = c + f * 0.1 * k
    put(oriented_ball(hd, (0.06 * k, 0.045 * k, 0.065 * k), *fr, 10, 6), "Dark")
    put(dome(hd + up * 0.012 * k, (0.068 * k, 0.06 * k, 0.07 * k), 0.0, 12, 6, 0.012), "Trim")
    for s in (1, -1):
        put(oriented_ball(hd + sd * s * 0.045 * k + f * 0.012 * k, (0.02 * k, 0.03 * k, 0.042 * k), *fr, 8, 4), "Glow")
        put(oriented_ball(c + sd * s * 0.12 * k + up * 0.1 * k, (0.12 * k, 0.05 * k, 0.008), *fr, 10, 3), "Metal")
    a = c - f * 0.12 * k + sd * 0.1 * k - up * 0.05 * k; b = c + f * 0.5 * k + sd * 0.1 * k - up * 0.05 * k
    put(pipe([a, a.lerp(b, 0.5), b], [0.012 * k] * 3, 5), "Trim")
    put(cone(b, b + f * 0.14 * k, 0.03 * k, 6), "Trim")


def M2_snail():
    """THE SNAIL KING (2026-10-14, remade like the alien / west / treasure / sea bosses): a giant land snail built like the real animal.
    His shell is a true conispiral, coiled to the left (one snail in thousands is: a king's mark), its spire turned toward you, of four and a half whorls, each twice as wide as the last, lapping over the one before at the suture -
    the banded snail's own colours, glossy golden yellow with five chocolate bands spiralling round with the coil, fine growth lines across
    them and a stronger resting mark every half turn, the apex worn darker, the mouth's lip thickened and dark brown. His body is the long
    muscular foot, its sole flat and pale, its skin wet and raised in tubercles; the mantle collar fills the shell's mouth with the breathing
    pore open in its side. The head carries both pairs of tentacles: the long upper ones with the eyes at their tips - glowing acid green
    with slit pupils under a heavy, glaring lid, and they nod - and the short lower ones, curled at the tips the way a villain waxes his
    moustache. Under them the mouth gapes: the snail's ribbed horn jaw across its top like a row of fangs, and the radula - the ribbon of
    teeth a snail rasps its food with - lolling out, rows of little hooked teeth on it, slime drooling.
    The cartoon idea kept: the king - a jewelled crown with arches, orb and cross between his eye stalks, a gold monocle on his right eye on
    its chain; his palace on top of his shell (a round keep with a golden spire and a glowing gem, four turrets with red roofs and pennants,
    a crenellated curtain wall); his bee guards with gold helmets and spears circling him; a glowing slime trail.
    He flies the way the sea butterflies fly (they are snails too, shell and all): his foot has grown two broad fleshy fins, ribbed with
    muscle, dusky at the root and paling to a rim of living light, held up and cupped toward you - they beat (FlapL / FlapR)."""
    P = Boss("snail", AB_pal(Base=((0.11, 0.09, 0.07), 0.4), Belly=((0.7, 0.62, 0.52), 0.4), Accent=((0.7, 0.07, 0.09), 0.55),
                             Trim=((0.98, 0.76, 0.22), 0.7), Glass=((0.72, 0.95, 0.45), 0.8), Dark=((0.06, 0.04, 0.03), 0.4),
                             Glow=((0.62, 1.0, 0.12), 0.5), Metal=((0.66, 0.58, 0.46), 0.5), Lamp=((1.0, 0.78, 0.3), 0.8)))
    glow_strength(P, 2.0)
    # ---- the foot: long and muscular, flat-soled (the bake draws the pale sole), pointed at the tail, rising at the front into the head
    sp = st_spline([V_(p) for p in ((0, -1.8, -0.46), (0, -1.3, -0.42), (0, -0.6, -0.37), (0, 0.1, -0.32), (0, 0.65, -0.25), (0, 1.05, -0.12),
                                    (0, 1.32, 0.08), (0, 1.45, 0.28))], 6)
    FR = spine_frames(sp); n = len(sp); uu = [i / (n - 1) for i in range(n)]
    RX = [lerp_keys(u, [(0, 0.03), (0.07, 0.2), (0.3, 0.42), (0.55, 0.47), (0.75, 0.42), (0.88, 0.35), (1, 0.29)]) for u in uu]
    RU = [lerp_keys(u, [(0, 0.03), (0.07, 0.12), (0.3, 0.25), (0.55, 0.3), (0.75, 0.31), (0.88, 0.31), (1, 0.29)]) for u in uu]
    RD = [lerp_keys(u, [(0, 0.02), (0.07, 0.09), (0.3, 0.15), (0.55, 0.17), (0.75, 0.17), (0.88, 0.16), (1, 0.15)]) for u in uu]
    P.obj("Foot", st_loft(sp, RX, RU, RD, FR, 36, 1.5), "Base")
    H = V_((0, 1.56, 0.4))
    P.obj("Head", oriented_ball(H, (0.3, 0.32, 0.31), V_((1, 0, 0)), V_((0, 1, 0)), V_((0, 0, 1)), 32, 16), "Base")
    # ---- the shell: the apex up, back and to his left, the mouth low over the foot in front
    A_, T_ = V_((-0.6, -0.2, 0.75)).normalized(), V_((0.25, 0.75, -0.6)).normalized()   # (built right-handed, then mirrored)
    Zs = (A_ - T_ * A_.dot(T_)).normalized()
    sh, (mc, mr, mt) = conispiral((0, 0, 0), Zs, Zs.cross(T_), R0=0.9)
    for v in sh.verts: v.co.x = -v.co.x
    bmesh.ops.reverse_faces(sh, faces=sh.faces[:])
    mc, mt = V_((-mc.x, mc.y, mc.z)), V_((-mt.x, mt.y, mt.z))
    vs = [v.co for v in sh.verts]
    lo = V_((min(p.x for p in vs), min(p.y for p in vs), min(p.z for p in vs))); hi = V_((max(p.x for p in vs), max(p.y for p in vs), max(p.z for p in vs)))
    off = V_((0.0 - (lo.x + hi.x) * 0.5, -0.25 - (lo.y + hi.y) * 0.5, -0.32 - lo.z))
    for v in sh.verts: v.co += off
    mc = mc + off; top = max((v.co for v in sh.verts), key=lambda p: p.z).copy(); shell_pts = [v.co.copy() for v in sh.verts]
    P.obj("Shell", sh, "Trim")
    P.obj("ShellLip", ring_on(mc, mt, mr, 0.05, 40, 8), "Dark")
    P.obj("Mantle", ring_on(mc - mt * 0.03, mt, mr * 0.86, 0.075, 36, 8), "Belly")
    P.obj("MantlePlug", oriented_ball(mc - mt * 0.1, (mr * 0.9, mr * 0.9, 0.12), *sq_axes(mt), 24, 12), "Base")
    rgt = (V_((1, 0, 0)) - mt * mt.x).normalized(); po = mc - mt * 0.01 + rgt * mr * 0.86   # the breathing pore, on his right
    P.obj("Pneumostome", oriented_ball(po + rgt * 0.03, (0.05, 0.05, 0.035), *sq_axes(rgt), 12, 6), "Dark")
    P.obj("PoreRim", ring_on(po + rgt * 0.05, rgt, 0.055, 0.016, 16, 5), "Belly")
    # ---- the head: two pairs of tentacles - the long upper ones carry the eyes and nod (SwayEyeR / SwayEyeL), the short lower ones curl
    for s in (1, -1):
        name = "SwayEyeR" if s > 0 else "SwayEyeL"
        b0 = H + V_((s * 0.2, 0.02, 0.2)); tip = H + V_((s * 0.6, 0.36, 1.2)); hub = tuple(b0)
        st = bez(b0, b0 + V_((s * 0.03, 0.08, 0.38)), tip - V_((s * 0.14, 0.12, 0.3)), tip, 14)
        P.part(name, pipe(st, [0.078 - 0.026 * (k / 14) for k in range(15)], 12), "Base", hub)
        e = st[-1] + (st[-1] - st[-2]).normalized() * 0.06
        g = V_((-s * 0.1, 1.0, -0.18)).normalized()                  # his gaze: ahead and down at you, a little inward
        gx = g.cross(V_((0, 0, 1))).normalized(); gz = gx.cross(g).normalized()
        P.part(name, ball(tuple(e - g * 0.05), (0.12, 0.12, 0.12), 18, 9), "Base", hub)
        P.part(name, oriented_ball(e + g * 0.01, (0.105, 0.105, 0.105), *rh(gx, g, gz), 24, 12), "Glow", hub)
        P.part(name, oriented_ball(e + g * 0.105, (0.016, 0.014, 0.068), *rh(gx, g, gz), 10, 6), "Dark", hub)
        pn = (gz * math.cos(math.radians(35)) - gx * (s * math.sin(math.radians(35)))).normalized()   # the lid slanted down over the inner corner: a glare
        P.part(name, ell_cap(e, (0.122, 0.122, 0.122), gx, g, gz, pn, -0.005, 32, 8, 0.022), "Base", hub)
        if s > 0:   # the monocle, its chain hanging
            mo = e + g * 0.13
            P.part(name, ring_on(mo, g, 0.135, 0.018, 32, 6), "Trim", hub)
            c0 = mo + gx * 0.095 - gz * 0.095
            P.part(name, pipe(bez(c0, c0 + V_((0.06, 0.0, -0.25)), c0 + V_((0.02, -0.08, -0.45)), c0 + V_((-0.04, -0.14, -0.5)), 10), [0.011] * 11, 4), "Trim", hub)
        lb = H + V_((s * 0.15, 0.27, -0.04))
        lt = bez(lb, lb + V_((s * 0.1, 0.17, -0.1)), lb + V_((s * 0.3, 0.26, -0.12)), lb + V_((s * 0.4, 0.22, 0.02)), 10)
        P.obj("Tentacle", pipe(lt, [0.06 - 0.003 * k for k in range(11)], 10), "Base")
        P.obj("TentacleTip", ball(tuple(lt[-1]), (0.034,) * 3, 8, 4), "Belly")
    # the mouth: a wide maw - the snail's ribbed horn jaw across its top, its ribs grown into fangs; the radula on its floor, a pad of
    # hooked teeth pushed forward over the lower lip, ready to rasp; slime drooling from the corners
    fm = V_((0, 0.86, -0.51)).normalized(); mx = V_((1, 0, 0)); mz = mx.cross(fm).normalized()
    m0 = H + fm * 0.28
    P.obj("Mouth", oriented_ball(m0, (0.19, 0.07, 0.12), *rh(mx, fm, mz), 24, 12), "Dark")
    lip = torus(1.0, 0.22, 0.0, 40, 8); xf(lip, Matrix.Diagonal((0.205, 0.135, 0.11))); xf(lip, Matrix((mx, mz, fm)).transposed(), tuple(m0 + fm * 0.03))
    P.obj("Lips", lip, "Belly")
    def jp(a): return m0 + fm * 0.05 + mx * (math.cos(a) * 0.17) + mz * (math.sin(a) * 0.1)
    P.obj("Jaw", pipe([jp(math.radians(20 + 140 * i / 14)) for i in range(15)], [0.026] * 15, 8), "Dark")
    P.obj("JawRib", bm_join([cone(jp(math.radians(32 + 116 * i / 10)), jp(math.radians(32 + 116 * i / 10)) - mz * (0.11 - 0.045 * abs(i - 5) / 5) + fm * 0.012,
                                  0.024, 6) for i in range(11)]), "Metal")
    rc = m0 + fm * 0.06 - mz * 0.075
    P.obj("Radula", oriented_ball(rc, (0.14, 0.075, 0.038), *rh(mx, fm, mz), 24, 10), "Accent")
    teeth = []
    for row in range(3):
        y = -0.035 + 0.035 * row
        for q in range(-3, 4):
            x = q * 0.034 * (1.0 - 0.12 * abs(row - 1)); h = 0.038 * math.sqrt(max(0.05, 1 - (x / 0.14) ** 2 - (y / 0.075) ** 2))
            b = rc + mx * x + fm * y + mz * (h - 0.004)
            teeth.append(cone(b, b + mz * 0.042 - fm * 0.018, 0.011, 5))
    small(P.obj("RadulaTooth", bm_join(teeth), "Metal"))
    for x, L in ((-0.175, 0.36), (0.18, 0.27)):
        b = m0 + mx * x - mz * 0.05 + fm * 0.02
        P.obj("Slime", pipe([b, b + V_((0, 0.01, -L * 0.5)), b + V_((0, 0.015, -L))], [0.022, 0.015, 0.01], 6), "Glass")
        P.obj("SlimeDrop", ball(tuple(b + V_((0, 0.015, -L - 0.035))), (0.034, 0.034, 0.048), 8, 4), "Glass")
    # the crown perched on his brow between the eye stalks: band, spikes and pearls, two arches, the orb and cross, a ruby in front
    cc = H + V_((0, 0.14, 0.24))
    P.obj("Crown", lathe([(0.105, 0.0), (0.125, 0.04), (0.132, 0.11), (0.115, 0.11), (0.1, 0.025)], 28, "z", tuple(cc)), "Trim")
    for k in range(6):
        a = 2 * math.pi * k / 6 + math.pi / 6; b = cc + V_((math.sin(a) * 0.128, math.cos(a) * 0.128, 0.105))
        P.obj("CrownSpike", cone(b, b + V_((0, 0, 0.1)), 0.034, 6), "Trim")
        P.obj("CrownPearl", ball(tuple(b + V_((0, 0, 0.115))), (0.022,) * 3, 8, 4), "Metal")
    for a in (0.0, math.pi / 2):
        arc = [cc + V_((math.sin(a) * math.cos(t) * 0.12, math.cos(a) * math.cos(t) * 0.12, 0.11 + math.sin(t) * 0.15)) for t in [math.pi * i / 12 for i in range(13)]]
        P.obj("CrownArch", pipe(arc, [0.016] * 13, 6), "Trim")
    P.obj("CrownOrb", ball(tuple(cc + V_((0, 0, 0.29))), (0.04,) * 3, 12, 6), "Trim")
    P.obj("CrownCross", bar(cc + V_((0, 0, 0.31)), cc + V_((0, 0, 0.43)), 0.024, 0.024), "Trim")
    P.obj("CrownCross", bar(cc + V_((-0.042, 0, 0.38)), cc + V_((0.042, 0, 0.38)), 0.024, 0.024), "Trim")
    for k in range(6):
        a = 2 * math.pi * k / 6; d = V_((math.sin(a), math.cos(a), 0))
        P.obj("CrownPearl", oriented_ball(cc + d * 0.133 + V_((0, 0, 0.06)), (0.022, 0.012, 0.026), *rh(d.cross(V_((0, 0, 1))), d, V_((0, 0, 1))), 10, 5), "Metal")
    # ---- the fins he flies on: the foot grown into two broad rounded lobes (a sea butterfly's), held out from the neck, tipped back so
    # their faces look forward and up, cupped; the muscle fibres fanning through them, photophores along the rim
    WK = [(0.0, 0.55), (0.3, 1.28), (0.55, 1.75), (0.76, 1.45), (1.0, 0.62)]
    for s in (1, -1):
        name = "FlapR" if s > 0 else "FlapL"
        Rb, Rt = V_((s * 0.3, 0.98, -0.3)), V_((s * 0.26, 1.04, 0.02)); hub = (Rb + Rt) * 0.5   # (sunk into the neck: it rocks)
        def wp(f, r, s=s, Rb=Rb, Rt=Rt):
            th = math.radians(-15 + 75 * f)
            d = (V_((s * math.cos(th), -0.42 * math.sin(th), 0.9 * math.sin(th))) + V_((0, -0.12, 0))).normalized()
            return Rb.lerp(Rt, f) + d * (lerp_keys(f, WK) * r) - V_((0, 1, 0)) * (0.14 * math.sin(math.pi * r) * math.sin(math.pi * f))
        NF, NRr = 30, 10
        bm = bmesh.new(); lr, la = bm.verts.layers.float.new("wr"), bm.verts.layers.float.new("wa")
        grid = []
        for i in range(NF + 1):
            row = []
            for j in range(NRr + 1):
                v = bm.verts.new(wp(i / NF, j / NRr)); v[lr] = j / NRr; v[la] = 6.0 * i / NF; row.append(v)
            grid.append(row)
        for i in range(NF):
            for j in range(NRr): bm.faces.new((grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1]))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=0.03)
        P.part(name, bm, "Base", tuple(hub), 0, True)
        P.part(name, bm_join([ball(tuple(wp((k + 0.5) / 13, 0.93)), (0.034,) * 3, 8, 4) for k in range(13)]), "Glow", tuple(hub))
    # ---- his palace on top of his shell: a round keep, four turrets on a crenellated curtain wall, red roofs, a golden spire
    S = 0.75; k0 = top - V_((0, 0, 0.1))
    def at(x, y, z): return k0 + V_((x, y, z)) * S
    def shell_z(x, y):   # the shell's surface under a point
        zs = [q.z for q in shell_pts if abs(q.x - x) < 0.07 and abs(q.y - y) < 0.07]
        return max(zs) if zs else k0.z - 0.4
    bm = bmesh.new(); bot, tp = [], []
    for i in range(48):
        a = 2 * math.pi * i / 48; d = V_((math.sin(a), math.cos(a), 0))
        q = k0 + d * (0.5 * S); bot.append(bm.verts.new((q.x, q.y, shell_z(q.x, q.y) - 0.07)))
        tp.append(bm.verts.new(k0 + d * (0.45 * S) + V_((0, 0, 0.2 * S))))
    for i in range(48): bm.faces.new((bot[i], bot[(i + 1) % 48], tp[(i + 1) % 48], tp[i]))
    bm.faces.new(tp)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    P.obj("Bastion", bm, "Metal")
    walls = [box(tuple(at(math.sin(a) * 0.43, math.cos(a) * 0.43, 0.25)), (0.075 * S, 0.06 * S, 0.1 * S), Matrix.Rotation(-a, 3, "Z"))
             for a in [2 * math.pi * (k + 0.5) / 18 for k in range(18)]]
    P.obj("Merlon", bm_join(walls), "Metal")
    P.obj("Keep", lathe([(0.2 * S, -0.35 * S), (0.2 * S, 0.7 * S), (0.24 * S, 0.72 * S), (0.24 * S, 0.8 * S), (0.0, 0.8 * S)], 24, "z", tuple(k0)), "Metal")
    mer, win = [], []
    for k in range(10):
        a = 2 * math.pi * k / 10; mer.append(box(tuple(at(math.sin(a) * 0.22, math.cos(a) * 0.22, 0.84)), (0.07 * S, 0.05 * S, 0.08 * S), Matrix.Rotation(-a, 3, "Z")))
    for k in range(8):
        a = 2 * math.pi * (k + 0.5) / 8; win.append(box(tuple(at(math.sin(a) * 0.2, math.cos(a) * 0.2, 0.48)), (0.05 * S, 0.03 * S, 0.11 * S), Matrix.Rotation(-a, 3, "Z")))
    P.obj("Merlon", bm_join(mer), "Metal")   # (the keep's own crenellation)
    P.obj("KeepRoof", cone(tuple(at(0, 0, 0.8)), tuple(at(0, 0, 1.28)), 0.235 * S, 24), "Accent")
    P.obj("Spire", cone(tuple(at(0, 0, 1.24)), tuple(at(0, 0, 1.68)), 0.035 * S, 8), "Trim")
    P.obj("SpireGem", ball(tuple(at(0, 0, 1.7)), (0.05 * S, 0.05 * S, 0.065 * S), 10, 5), "Glow")
    for k in range(4):
        a = math.radians(45 + 90 * k); tc = at(math.sin(a) * 0.4, math.cos(a) * 0.4, 0.15)
        P.obj("Turret", lathe([(0.1 * S, 0.0), (0.1 * S, 0.42 * S), (0.125 * S, 0.44 * S), (0.125 * S, 0.5 * S), (0.0, 0.5 * S)], 16, "z", tuple(tc)), "Metal")
        P.obj("Roof", cone(tuple(tc + V_((0, 0, 0.5 * S))), tuple(tc + V_((0, 0, 0.8 * S))), 0.135 * S, 16), "Accent")
        P.obj("Finial", ball(tuple(tc + V_((0, 0, 0.82 * S))), (0.022 * S,) * 3, 6, 3), "Trim")
        for q in (-1, 0, 1):
            b_ = a + q * math.radians(70)
            win.append(box(tuple(tc + V_((math.sin(b_) * 0.1, math.cos(b_) * 0.1, 0.27)) * S), (0.035 * S, 0.03 * S, 0.08 * S), Matrix.Rotation(-b_, 3, "Z")))
        if k in (0, 3):   # pennants on the two front turrets
            pole = tc + V_((0, 0, 0.82 * S))
            P.obj("FlagPole", pipe([pole, pole + V_((0, 0, 0.24 * S))], [0.01, 0.008], 4), "Trim")
            P.obj("ClothPennant", st_cloth([[tuple(pole + V_((0, 0, 0.235)) * S), tuple(pole + V_((0, -0.26, 0.18)) * S), tuple(pole + V_((0, 0, 0.13)) * S)]], 0.012), "Accent")
    small(P.obj("Window", bm_join(win), "Lamp"))
    # ---- his guards circling, spears levelled
    for k in range(5):
        a = 2 * math.pi * k / 5 + 0.3
        c = V_((math.sin(a) * 2.35, -0.3 + math.cos(a) * 2.1, 0.75 + 0.22 * math.sin(a * 2)))
        guard_bee(P, "SpinGuards", c, V_((math.cos(a), -math.sin(a), 0)), (0, -0.3, 0.75), 1.35)
    mz_ = m0 + fm * 0.12
    P.part("Muzzle", ball(tuple(mz_), (0.02, 0.02, 0.02), 6, 3), "Dark", tuple(mz_))
    return P


BOSSES = [("bee", M2_bee), ("ladybug", M2_ladybug), ("dragonfly", M2_dragonfly), ("evilflower", M2_evilflower), ("snail", M2_snail)]

# the surfaces each part is made of, for the bake (boss_bake.py): slot defaults, then part-name patterns
BB.TABLES.update({
    "bee": ({"Base": "pile", "Belly": "pile", "Dark": "pile", "Accent": "gem", "Trim": "gold", "Glass": "insect_wing", "Glow": "compound",
             "Metal": "chitin", "Lamp": "honey"},
            [("Ocellus", "gem"), ("Venom", "glow"), ("LanceTip", "glow"), ("CrownPearl", "eye_white"), ("Ruby", "gem"), ("MandibleTooth", "chitin"), ("Clypeus", "chitin"), ("Flap*", {"Metal": "vein"})]),
    "ladybug": ({"Base": "spotted", "Belly": "silk", "Accent": "hair", "Trim": "gold", "Glass": "insect_wing", "Dark": "chitin", "Glow": "compound",
                 "Metal": "steel", "Lamp": "pile"},
                [("Pronotum", "patched"), ("Head", "patched"), ("Lance", {"Accent": "wood", "Trim": "gold"}), ("Shield", {"Base": "spotted"}),
                 ("Flap*", {"Dark": "vein"}), ("Muzzle", "glow")]),
    "dragonfly": ({"Base": "iridescent", "Belly": "chitin", "Accent": "iridescent", "Trim": "gold", "Glass": "dragon_wing", "Dark": "chitin", "Glow": "compound",
                   "Metal": "chitin", "Lamp": "glow"},
                  [("StormOrb", "water"), ("Flap*", {"Dark": "vein"}), ("MandibleTooth", "chitin")]),
    "evilflower": ({"Base": "plant", "Belly": "pile", "Accent": "petal", "Trim": "gold", "Glass": "enamel", "Dark": "flesh", "Glow": "glow",
                    "Metal": "chitin", "Lamp": "glow"},
                   [("Disc", "matte"), ("Seed", {"Metal": "chitin", "Base": "matte", "Belly": "pile"}), ("Root*", "wood_v"), ("Taproot", "wood_v"),
                    ("Thorn", "horn"), ("Clod", "matte"), ("Bract", {"Base": "plant", "Lamp": "glow"}), ("SpinSeeds", {"Metal": "chitin", "Glass": "matte"}),
                    ("Muzzle", "matte")]),
    "snail": ({"Base": "snail_skin", "Belly": "flesh", "Accent": "flesh", "Trim": "gold", "Glass": "water", "Dark": "eye", "Glow": "glow",
               "Metal": "stone", "Lamp": "lamp"},
              [("Shell", "snail_shell"), ("ShellLip", "horn"), ("JawRib", "enamel"), ("Jaw", "horn"), ("RadulaTooth", "enamel"), ("Mouth", "flesh"), ("Pneumostome", "flesh"),
               ("Flap*", {"Base": "parapodium", "Dark": "membrane"}), ("Roof", "clay_tiles"), ("KeepRoof", "clay_tiles"), ("Cloth*", "silk"),
               ("Crown*", {"Metal": "eye_white", "Accent": "gem"}),
               ("SpinGuards", {"Lamp": "pile", "Dark": "pile", "Belly": "pile", "Metal": "insect_wing"}), ("Muzzle", "matte")]),
})

if __name__ == "__main__":
    os.makedirs(AB.OUT, exist_ok=True)
    for bid, fn in BOSSES:
        if ONLY and bid not in ONLY: continue
        P = fn()
        if AB.EXPORT and bid in BB.TABLES: BB.finish_baked(P, AB.OUT)   # the real surfaces baked into textures beside the FBX
        else: P.finish()
    print("DONE")
