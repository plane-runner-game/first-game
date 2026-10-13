# Sky Squad, the lava world's (INFERNO) five bosses (2026-10-10: "now for the lava, inferno" - five beautiful ones that suit the world, and
# the world ends after the fifth, as the sea). Built from code like the alien and sea bosses (alien_bosses.py lends its Boss class and
# shapes): the hellfire galleon (the magma phoenix until the same evening), the ember scarab, the inferno golem, the fire ifrit and the volcano fortress.
# Run: blender -b -P Tools/blender/lava_bosses.py -- <out dir> [export] [ids,comma,separated]
# Conventions as alien_bosses.py / sea_bosses.py: +Y nose, +Z up, +X right; "Flap*" rock about the nose axis, "Sway*" about the wing axis,
# "Spin*" turn slowly about up, "Cloth" stays still without the outline, "Muzzle" is where his shots leave from.
import bpy, bmesh, math, sys, os, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mathutils import Vector, Matrix
from enemy_planes import loft, sweep, lathe, box, hull, tube, mirror_x, airfoil
import alien_bosses as AB
from alien_bosses import Boss, xf, ball, pipe, cone, bez, torus, sheet, grow, ang

import bmesh
from mathutils.bvhtree import BVHTree
from enemy_planes import loft, sweep, lathe, box, hull, tube, mirror_x, airfoil, SLOTS
from alien_bosses import Boss, xf, ball, pipe, cone, bez, torus, sheet, grow, ang, lerp_keys, spine_frames, body_loft, skin, oriented_ball, frame, sheet_solid, ribbon

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ONLY = argv[2].split(",") if len(argv) > 2 and argv[2] else None


def speckle(c, k=1.0):
    v = math.sin(c.x * 12.9898 * k + c.y * 78.233 * k + c.z * 37.719 * k) * 43758.5453
    return v - math.floor(v)

def rock(c, r, rng, n=14, squash=(1, 1, 1)):
    """a lumpy convex rock about c."""
    pts = []
    for _ in range(n):
        d = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1)))
        if d.length < 1e-3: continue
        d.normalize(); k = r * rng.uniform(0.75, 1.0)
        pts.append(Vector(c) + Vector((d.x * k * squash[0], d.y * k * squash[1], d.z * k * squash[2])))
    return hull([tuple(p) for p in pts])

def fine(keys, step=0.08):
    """wing sections interpolated every 'step' so painted bands come out as thin stripes."""
    secs = []
    for a0, a1 in zip(keys, keys[1:]):
        n = max(2, int((a1[0] - a0[0]) / step))
        secs += [tuple(u + (v - u) * i / n for u, v in zip(a0, a1)) for i in range(n)]
    secs.append(keys[-1])
    return secs

def cracks(c, n):
    """glowing lava cracks over dark rock: a few thin wavy bands."""
    w = math.sin(c.x * 7.0 + math.sin(c.y * 5.0) * 1.5) * math.sin(c.y * 6.0 + c.z * 4.0)
    return abs(w) < 0.06


# ================================================================= 1. the hellfire galleon
def L_galleon():
    """A ship from the burning sea (2026-10-10, in place of the phoenix: "the first boss is ugly"; the sky galleon was the one liked best): the
    sea's galleon in obsidian and crimson - crimson sails with burning crosses, gold rails, a horned skull with burning eyes at the bow, flames
    all along the rails, the keel rings glowing like coals, canvas wings beating."""
    import sea_bosses
    return sea_bosses.S_galleon("hellship", {"Base": ((0.07, 0.05, 0.05), 0.45), "Belly": ((0.50, 0.07, 0.04), 0.3), "Accent": ((0.85, 0.20, 0.04), 0.4),
                                             "Trim": ((0.96, 0.70, 0.22), 0.75), "Glass": ((0.22, 0.08, 0.05), 0.3), "Dark": ((0.03, 0.02, 0.02), 0.4),
                                             "Glow": ((1.0, 0.45, 0.05), 0.5), "Metal": ((0.18, 0.16, 0.16), 0.6), "Lamp": ((1.0, 0.75, 0.25), 0.8)}, hell=True)


# ================================================================= 2. the ember scarab
def L_volcano():
    """The last boss: a floating volcanic island - a jagged basalt root below dripping lava falls, a smoking cone with a glowing crater and
    lava rivers running down it, a black fortress of towers with burning windows and red banners on its rim, a gate cannon at the front,
    and rocks drifting round it."""
    P = Boss("volcano", {"Base": ((0.13, 0.10, 0.10), 0.35), "Belly": ((0.22, 0.15, 0.12), 0.3), "Accent": ((0.70, 0.08, 0.05), 0.45),
                         "Trim": ((0.95, 0.70, 0.20), 0.7), "Glass": ((1.0, 0.75, 0.3), 0.9), "Dark": ((0.04, 0.03, 0.03), 0.4),
                         "Glow": ((1.0, 0.42, 0.05), 0.5), "Metal": ((0.30, 0.27, 0.27), 0.5), "Lamp": ((1.0, 0.85, 0.35), 0.8)})
    rng = random.Random(11)
    # the island: a flat top, a jagged root hanging below
    P.obj("Ground", lathe([(0.0, 0.18), (1.85, 0.18), (1.95, 0.08), (1.9, -0.05)], 30, "z"), lambda c, n: "Belly" if n.z > 0.5 else "Base")
    root = []
    for k in range(40):
        a = rng.uniform(0, 2 * math.pi); r = rng.uniform(0.2, 1.9); z = -0.05 - (1.9 - r) * rng.uniform(0.6, 0.9)
        root.append((math.sin(a) * r, math.cos(a) * r, z))
    root += [(math.sin(2 * math.pi * k / 16) * 1.9, math.cos(2 * math.pi * k / 16) * 1.9, -0.04) for k in range(16)] + [(0, 0, -1.6)]
    P.obj("Root", hull(root), lambda c, n: "Glow" if cracks(c, n) else "Base", 1)
    for k in range(6):   # lava falls off the rim
        a = 2 * math.pi * (k + 0.3) / 6
        p0 = Vector((math.sin(a) * 1.9, math.cos(a) * 1.9, 0.1))
        P.obj("LavaFall", pipe([p0, p0 + Vector((math.sin(a) * 0.15, math.cos(a) * 0.15, -0.3)), p0 + Vector((math.sin(a) * 0.12, math.cos(a) * 0.12, -0.9))], [0.07, 0.06, 0.0], 6), "Glow")
    # the volcano: rivers of lava down its flanks, the crater glowing
    cone_bm = lathe([(1.25, 0.18), (0.95, 0.55), (0.55, 1.15), (0.38, 1.35), (0.3, 1.32), (0.28, 1.2)], 28, "z", (0, -0.35, 0))
    def flank(c, n):
        if c.z > 1.28 or (c.z > 1.15 and n.z > 0.3): return "Glow"
        a = ang(Vector((c.x, c.y + 0.35, 0)))
        return "Glow" if (a / (2 * math.pi) * 5 + c.z * 0.25) % 1.0 < 0.08 else ("Belly" if c.z < 0.4 else "Base")
    P.obj("Cone", cone_bm, flank)
    P.obj("Crater", lathe([(0.0, 1.22), (0.28, 1.22)], 16, "z", (0, -0.35, 0)), "Glow")
    for k in range(5):   # the smoke and sparks over the crater
        P.obj("Ember", ball((rng.uniform(-0.15, 0.15), -0.35 + rng.uniform(-0.15, 0.15), 1.45 + k * 0.12), (0.07, 0.07, 0.09), 6, 3), "Lamp" if k % 2 else "Glow")
    # the fortress round the rim at the front: wall, towers, banners, the gate cannon
    for k in range(7):
        a = math.radians(-75 + k * 25)
        c = (math.sin(a) * 1.55, math.cos(a) * 1.4, 0.18)
        h = 0.55 + 0.2 * (k % 2)
        P.obj("Tower", lathe([(0.17, 0.0), (0.15, h), (0.2, h + 0.03), (0.2, h + 0.1)], 10, "z", c), lambda c2, n, h=h: "Glow" if abs(c2.z - 0.18 - h * 0.6) < 0.035 and n.z < 0.3 else "Metal")
        P.obj("Spike", cone((c[0], c[1], c[2] + h + 0.1), (c[0], c[1], c[2] + h + 0.42), 0.12, 8), "Dark", 0, False)
        if k % 2 == 0:
            P.obj("Banner", box((c[0], c[1] + 0.13, c[2] + h - 0.12), (0.02, 0.18, 0.3)), "Accent", 0, False)
    for k in range(6):
        a0 = math.radians(-75 + k * 25); a1 = math.radians(-50 + k * 25)
        p0 = Vector((math.sin(a0) * 1.55, math.cos(a0) * 1.4, 0.35)); p1 = Vector((math.sin(a1) * 1.55, math.cos(a1) * 1.4, 0.35))
        mid = (p0 + p1) * 0.5; d = p1 - p0
        P.obj("Wall", box(tuple(mid), (d.length, 0.12, 0.35), Matrix.Rotation(math.atan2(d.y, d.x), 3, "Z")), lambda c2, n: "Trim" if n.z > 0.5 else "Metal", 0, False)
    P.obj("Gate", box((0, 1.47, 0.32), (0.32, 0.1, 0.3)), "Glow", 0, False)
    P.obj("Cannon", pipe([(0, 1.35, 0.62), (0, 2.0, 0.66)], [0.13, 0.1], 10), "Metal")
    P.obj("CannonRing", pipe([(0, 1.9, 0.66), (0, 1.98, 0.66)], [0.12, 0.12], 10), "Trim")
    for k in range(7):   # rocks drifting round it
        a = 2 * math.pi * k / 7
        P.part("SpinRocks", rock((math.sin(a) * 2.4, math.cos(a) * 2.2, 0.2 + 0.3 * math.sin(a * 2)), 0.16 + 0.05 * (k % 3), rng, 10),
               lambda c, n: "Glow" if speckle(c, 1.1) < 0.12 else "Base", (0, 0, 0.2), 1)
    P.part("Muzzle", ball((0, 2.05, 0.66), (0.1, 0.05, 0.1), 8, 4), "Glow", (0, 2.05, 0.66))
    return P


# >>> 2026-10-11 new

# ================================================================= 2026-10-11: the new first and last ("new bosses with a new shape, with a
# face, grand, that suit the world"): the magma salamander king and the demon lord
def membrane(hub, wr, tips, back=0.04):
    """a bat-wing membrane: scalloped triangles from the wrist between the finger tips, thickened a little along -y."""
    polys = []
    for a, b in zip(tips, tips[1:]):
        m = (a + b) * 0.5 + (wr - (a + b) * 0.5) * 0.22
        polys += [[wr, a, m], [wr, m, b]]
    polys.append([wr, tips[-1], hub])
    bm = bmesh.new()
    for poly in polys:
        bm.faces.new([bm.verts.new(tuple(p)) for p in poly])
    ext = bmesh.ops.extrude_face_region(bm, geom=list(bm.faces))
    for v in [e for e in ext["geom"] if isinstance(e, bmesh.types.BMVert)]: v.co.y -= back
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm



# ================================================================= salamander (2026-10-13 remake)
SA_SURF = 0.15        # the lava's top under him (z)


def sa_spline(ctrl, n):
    """a Catmull-Rom curve through the control points, n points per span."""
    P = [Vector(p) for p in ctrl]
    P = [P[0] * 2 - P[1]] + P + [P[-1] * 2 - P[-2]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for j in range(n):
            t = j / n
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(P[-2])
    return out

def sa_loft(pts, rx, rz, seg, slot, flat=0.8, sq=1.15):
    """a body along a spine (rounded sections rx across, rz up, the belly flattened), each face painted by slot(u, t): u from the first
    ring to the last, t the angle round the section from the top (0) to the belly (+-pi), positive on the right."""
    fr = spine_frames(pts)
    bm = bmesh.new(); rings = []
    for i, p in enumerate(pts):
        t_, side, up = fr[i]
        if rx[i] < 1e-4: rings.append([bm.verts.new(p)]); continue
        ring = []
        for k in range(seg):
            a = 2 * math.pi * k / seg; ca, sa = math.cos(a), math.sin(a)
            u = math.copysign(abs(ca) ** (1 / sq), ca) * rx[i]
            v = math.copysign(abs(sa) ** (1 / sq), sa) * rz[i] * (flat if sa < 0 else 1.0)
            ring.append(bm.verts.new(p + side * u + up * v))
        rings.append(ring)
    skin(bm, rings, seg)
    n = len(rings)
    for i in range(n - 1):
        if len(rings[i]) == 1 or len(rings[i + 1]) == 1: continue
        for k in range(seg):
            vs = {rings[i][k], rings[i][(k + 1) % seg], rings[i + 1][k]}
            f = next((f for f in rings[i][k].link_faces if vs <= set(f.verts)), None)
            if f is None: continue
            a = 2 * math.pi * (k + 0.5) / seg
            t = math.atan2(math.cos(a), math.sin(a))          # 0 on top, + toward the side vector (the right when going tailward... flipped below)
            f.material_index = SLOTS.index(slot((i + 0.5) / (n - 1), t))
    for f in bm.faces:
        if len(f.verts) != 4 and f.material_index == 0: f.material_index = SLOTS.index(slot(0.0 if f.calc_center_median().y > pts[n // 2].y else 1.0, 3.0))
    return bm

def sa_hide(plates, u0=0.0):
    """the fire salamander's hide: black, its back broken into plates by glowing magma cracks (a seam down the spine and one between each
    pair of plates), a yellow-orange blotch on each side of every plate, a smaller one low on the flank between them, a dark belly."""
    def slot(u, t):
        at = abs(t); w = u * plates + u0
        cell = w - math.floor(w)
        if at > 2.25: return "Belly"
        if at < 0.9:
            if at < 0.07 or cell < 0.07: return "Glow"
            if ((cell - 0.55) / 0.3) ** 2 + ((at - 0.5) / 0.3) ** 2 < 1.0: return "Trim"
            return "Base"
        c2 = (w + 0.5) - math.floor(w + 0.5)
        if ((c2 - 0.55) / 0.2) ** 2 + ((at - 1.45) / 0.2) ** 2 < 1.0: return "Trim"
        return "Base"
    return slot

def sa_dome(c, rx, ry, rz, up=True, seg=28, rings=8):
    """half an ellipsoid about c with its flat face through c, the dome up (or down)."""
    s = 1 if up else -1
    prof = [(0.0, 0.0)] + [(math.cos(math.pi / 2 * j / rings), s * math.sin(math.pi / 2 * j / rings)) for j in range(rings)] + [(0.0, s * 1.0)]
    if not up: prof = list(reversed(prof))
    bm = lathe(prof, seg, "z")
    for v in bm.verts: v.co = Vector((v.co.x * rx, v.co.y * ry, v.co.z * rz)) + Vector(c)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm

def sa_river(path, W, T):
    """the lava river: a flat ribbon along the path, W the half-width per point, T the depth. Across it: a crust levee at each edge, the
    orange flow inside them, the yellow-hot current in the middle; underneath dark crust with a glowing crack every few sections."""
    sec = [(-1.0, 0.0, "Belly"), (-0.93, 0.2, "Belly"), (-0.8, 0.16, "Glow"), (-0.5, 0.1, "Glow"), (-0.18, 0.13, "Lamp"), (0.18, 0.13, "Lamp"),
           (0.5, 0.1, "Glow"), (0.8, 0.16, "Belly"), (0.93, 0.2, "Belly"), (1.0, 0.0, "Belly"), (0.9, -0.3, "Belly"), (0.6, -0.55, "Belly"), (0.2, -0.65, "Belly"),
           (-0.2, -0.65, "Belly"), (-0.6, -0.55, "Belly"), (-0.9, -0.3, "Belly")]
    m = len(sec)
    bm = bmesh.new(); rings = []
    fr = []
    for i, p in enumerate(path):
        t = (path[min(i + 1, len(path) - 1)] - path[max(i - 1, 0)]).normalized()
        side = t.cross(Vector((0, 0, 1))).normalized(); up = side.cross(t).normalized()
        fr.append((side, up))
    for i, p in enumerate(path):
        side, up = fr[i]
        rings.append([bm.verts.new(p + side * (s * W[i]) + up * (h * T[i] / 0.5 * 0.5)) for (s, h, _) in sec])
    for i in range(len(rings) - 1):
        for k in range(m):
            k2 = (k + 1) % m
            f = bm.faces.new((rings[i][k], rings[i + 1][k], rings[i + 1][k2], rings[i][k2]))
            slot = sec[k][2]
            if k >= 10 and i % 6 == 3: slot = "Glow"          # the glowing cracks across the crust underneath
            if slot == "Belly" and k not in (1, 8) and (i * 3 + k * 5) % 11 == 0: slot = "Glow"   # and broken through the levees
            f.material_index = SLOTS.index(slot)
    for r, rev in ((rings[0], True), (rings[-1], False)):
        f = bm.faces.new(list(reversed(r)) if rev else r); f.material_index = SLOTS.index("Belly")
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm, fr

def sa_flame(base, h, r, lean, curl):
    """a tongue of fire: a tapering curve rising from base, leaning back and curling at the tip."""
    b = Vector(base)
    pts = bez(b, b + Vector((0, -lean * 0.2, h * 0.45)), b + Vector((0, -lean * 0.7, h * 0.85)), b + Vector((curl, -lean, h)), 6)
    return pipe(pts, [r, r * 1.05, r * 0.85, r * 0.6, r * 0.38, r * 0.18, 0.0], 8)


def L_salamander():
    """The first boss, the MAGMA SALAMANDER KING (2026-10-14, remade: "same as the alien bosses - realistic details, scarier, keep the
    cartoon shape"): the same crowned fire salamander, now built like a real one (Salamandra salamandra) crossed with a fire spirit. A long
    low body, round in section, the glossy black hide of a fire salamander; down his back the skin is broken into plates by glowing magma
    cracks - a seam down the spine and one between each pair of plates - and every plate carries the salamander's yellow-orange blotch on
    each side, a smaller one low on the flank between them, in two even rows from the neck to the tip of the tail. The head is broad and
    flat with a rounded snout and the wide lipless mouth of an amphibian, thrown open: rows of small white-hot teeth along both jaws, a
    red tongue on the floor of the mouth and the throat glowing like a furnace (his shots leave from it). Bulging eyes on top of the head,
    fiery gold with the vertical slit pupil, half shut under heavy lids slanting down to the snout, under thick brow ridges; nostrils at the
    tip of the snout. Behind each eye the great kidney-shaped paratoid gland of a fire salamander, yellow-orange and pitted with pores, and
    a row of smaller gland bumps running on from it down each side of the back. Four sprawling legs with the elbows and knees out to the
    sides, four fingers on the hands and five toes on the feet, yellow-spotted. A long tail flattened side to side like a newt's, a fin
    ridge along its top, the blotches running on along it to a tip that burns. On his head a crown of obsidian and gold - a gold band
    with points and rubies between tall shards of black volcanic glass, a fire opal in front - the gold softening in the heat and running
    down in drips; a crest of fire rises along the glowing seam of his back, tallest over the shoulders.
    He flies by SWIMMING IN A RIVER OF LAVA THAT FLOWS THROUGH THE AIR: a thick ribbon of molten rock comes up out of the sky from behind
    and below him, runs under him and curls on past his head and down away to the left, as a serpent would. Its edges are crusted into
    dark levees, inside them the orange flow with the yellow-hot current running down its middle, crust plates floating along both edges,
    bubbles rising and popping evenly along it; underneath it is dark crust split by glowing cracks, and lava drips from it and falls. He
    swims in it half sunk, the lava up to his flanks, splashing up along his sides and in a bow wave at his chin, a wake of ripples
    spreading behind him; his legs paddle (SwayLeg0-3) and his tail sweeps (SwayTail)."""
    P = Boss("salamander", {"Base": ((0.045, 0.035, 0.035), 0.7), "Belly": ((0.075, 0.04, 0.035), 0.3), "Accent": ((0.62, 0.05, 0.05), 0.6),
                            "Trim": ((1.0, 0.6, 0.06), 0.65), "Glass": ((1.0, 0.62, 0.06), 0.95), "Dark": ((0.02, 0.015, 0.02), 0.85),
                            "Glow": ((1.0, 0.32, 0.03), 0.5), "Metal": ((1.0, 0.74, 0.28), 0.8), "Lamp": ((1.0, 0.74, 0.22), 0.8)})
    FX = "ClothFx"
    # ---- the river of lava
    ctrl = [(1.45, -2.9, -1.45), (1.15, -2.3, -0.72), (0.32, -1.5, -0.06), (0.0, -0.4, 0.06), (0.0, 0.7, 0.06), (-0.3, 1.6, -0.04),
            (-1.0, 2.0, -0.38), (-1.55, 1.62, -0.88), (-1.35, 0.95, -1.38), (-0.75, 0.75, -1.72)]
    path = sa_spline(ctrl, 10)
    n = len(path)
    W = [lerp_keys(i / (n - 1), [(0, 0.18), (0.12, 0.55), (0.3, 0.82), (0.62, 0.82), (0.85, 0.6), (1, 0.12)]) for i in range(n)]
    T = [lerp_keys(i / (n - 1), [(0, 0.18), (0.15, 0.5), (0.35, 0.64), (0.7, 0.58), (1, 0.18)]) for i in range(n)]
    rb, rfr = sa_river(path, W, T)
    P.obj("River", rb, lambda c, n_: None, 0, True)
    L = [0.0]
    for a, b in zip(path, path[1:]): L.append(L[-1] + (b - a).length)
    def at(s):
        """point, side, up, half-width, depth at arc length s along the river."""
        for i in range(n - 1):
            if L[i + 1] >= s:
                f = (s - L[i]) / max(1e-6, L[i + 1] - L[i])
                p = path[i].lerp(path[i + 1], f); sd, up = rfr[i]
                return p, sd, up, W[i] + (W[i + 1] - W[i]) * f, T[i] + (T[i + 1] - T[i]) * f
        return path[-1], rfr[-1][0], rfr[-1][1], W[-1], T[-1]
    under = lambda p: -0.7 < p.y < 1.4 and abs(p.x) < 0.9     # where his body lies in the river
    # crust plates floating along both edges, bubbles and popped rings along the flow, drips falling from underneath
    s = 0.35; k = 0
    while s < L[-1] - 0.3:
        p, sd, up, w, t = at(s); side = 1 if k % 2 else -1
        q = p + sd * (side * w * 0.66) + up * (t * 0.16)
        if not under(q):
            pl = [q + sd * (dx * 0.13) + (sd.cross(up)) * (dy * 0.1) for dx, dy in ((-1, -0.6), (-0.3, -1), (0.8, -0.7), (1, 0.4), (0.2, 1), (-0.8, 0.7))]
            pl = [x + up * 0.025 for x in pl] + [x - up * 0.015 for x in pl]
            P.obj("Crust", hull([tuple(x) for x in pl]), "Dark", 0, False)
        b = p + sd * (-side * w * 0.3) + up * (t * 0.2)
        if not under(b):
            if k % 3 == 2: P.part(FX, xf(torus(0.07, 0.014, 0, 14, 5), None, tuple(b)), "Glow", (0, 0, 0))
            else: P.part(FX, sa_dome(tuple(b), 0.06 + 0.02 * (k % 2), 0.06 + 0.02 * (k % 2), 0.05, True, 10, 3), "Lamp", (0, 0, 0))
        d = p - up * (t * 0.5)
        P.part(FX, pipe([d, d - up * 0.1 - Vector((0, 0, 0.04)), d - Vector((0, 0, 0.2))], [0.045, 0.03, 0.0], 6), "Glow", (0, 0, 0))
        P.part(FX, ball(tuple(d - Vector((0, 0, 0.32 + 0.06 * (k % 2)))), (0.03, 0.03, 0.05), 6, 3), "Glow", (0, 0, 0))
        s += 0.42; k += 1
    s = 0.2
    while s < L[-1] - 0.2:
        p, sd, up, w, t = at(s); fw = sd.cross(up) * -1
        if not under(p):
            arc = [p + sd * (w * 0.72 * x) + up * (t * 0.17 - 0.02 * x * x) + fw * (0.12 * (1 - x * x)) for x in (-1, -0.5, 0, 0.5, 1)]
            P.obj("Rope", pipe(arc, [0.012, 0.02, 0.024, 0.02, 0.012], 5), "Dark", 0, False)
        s += 0.27
    # the end of the river pours off in a short fall of drops
    e = path[-1]
    for j in range(5):
        P.part(FX, ball(tuple(e - Vector((0.04 * (j % 2), 0, 0.14 + j * 0.15))), (0.06 - j * 0.008,) * 2 + (0.08,), 6, 3), "Glow", (0, 0, 0))

    # ---- the body: neck, trunk and hips (the tail is its own part)
    trunk = sa_spline([(0, 1.05, 0.3), (0, 0.45, 0.24), (0.04, -0.2, 0.17), (0.0, -0.95, 0.12)], 26)
    nt = len(trunk)
    rx = [lerp_keys(i / (nt - 1), [(0, 0.4), (0.25, 0.44), (0.6, 0.46), (0.85, 0.42), (1, 0.34)]) for i in range(nt)]
    rz = [lerp_keys(i / (nt - 1), [(0, 0.26), (0.3, 0.28), (0.7, 0.27), (1, 0.24)]) for i in range(nt)]
    P.obj("Trunk", sa_loft(trunk, rx, rz, 64, sa_hide(5.0, 0.0)), lambda c, n_: None, 0, True)
    # the tail: flattened side to side, sweeping back along the river with a wave in it
    tail = sa_spline([(0.0, -0.95, 0.12), (0.12, -1.55, 0.12), (0.42, -2.1, 0.06), (0.62, -2.55, -0.05), (0.62, -3.0, -0.08)], 20)
    ntl = len(tail)
    trx = [lerp_keys(i / (ntl - 1), [(0, 0.32), (0.4, 0.2), (0.8, 0.09), (1, 0.0)]) for i in range(ntl)]
    trz = [lerp_keys(i / (ntl - 1), [(0, 0.25), (0.4, 0.24), (0.8, 0.14), (1, 0.0)]) for i in range(ntl)]
    hub = tuple(tail[0])
    P.part("SwayTail", sa_loft(tail, trx, trz, 40, sa_hide(5.0, 0.0)), lambda c, n_: None, hub, 0)
    # its fin ridge: a thin crest along the top of the tail, its edge glowing
    fin = []
    for i in range(1, ntl - 1):
        u = i / (ntl - 1); h = lerp_keys(u, [(0, 0.0), (0.2, 0.1), (0.6, 0.13), (1, 0.0)])
        p = tail[i] + Vector((0, 0, trz[i] * 0.92)); fin.append((p, p + Vector((0, 0, h))))
    fb = bmesh.new()
    rows = [[fb.verts.new(a + Vector((dx, 0, 0))), fb.verts.new(b + Vector((dx, 0, 0)))] for a, b in fin for dx in (0.012, -0.012)]
    for i in range(len(fin) - 1):
        for side in (0, 1):
            a0, b0 = rows[i * 2 + side]; a1, b1 = rows[(i + 1) * 2 + side]
            f = fb.faces.new((a0, a1, b1, b0)); f.material_index = SLOTS.index("Base")
        f = fb.faces.new((rows[i * 2][1], rows[(i + 1) * 2][1], rows[(i + 1) * 2 + 1][1], rows[i * 2 + 1][1])); f.material_index = SLOTS.index("Glow")
    bmesh.ops.recalc_face_normals(fb, faces=fb.faces)
    P.part("SwayTail", fb, lambda c, n_: None, hub, 0, False)
    tip = tail[-2]
    for j, (dx, h) in enumerate(((0.0, 0.42), (0.07, 0.26), (-0.07, 0.3))):
        P.part("SwayTail", sa_flame(tip + Vector((dx, -0.05, 0.02)), h, 0.06, 0.25, 0.02), "Glow", hub)
        P.part("SwayTail", sa_flame(tip + Vector((dx, -0.03, 0.03)), h * 0.6, 0.032, 0.15, 0.0), "Lamp", hub)

    # ---- the head: broad and flat, the mouth open
    HC = Vector((0, 1.3, 0.32))
    def skull_paint(c, n_):
        if n_.z < -0.7: return "Dark"
        if n_.z > 0.55 and (((abs(c.x) - 0.17) / 0.09) ** 2 + ((c.y - 1.2) / 0.16) ** 2 < 1): return "Trim"
        return "Base"
    P.obj("Skull", sa_dome(tuple(HC), 0.6, 0.62, 0.25, True, 40, 10), skull_paint, 0, True)
    hinge = Vector((0, 0.82, 0.3)); jaw_m = Matrix.Translation(hinge) @ Matrix.Rotation(math.radians(-17), 4, "X") @ Matrix.Translation(-hinge)
    jaw = sa_dome((0, 1.27, 0.3), 0.56, 0.57, 0.15, False, 32, 7)
    jaw.transform(jaw_m)
    P.obj("Jaw", jaw, lambda c, n_: "Dark" if n_.z > 0.6 else ("Trim" if n_.z < -0.75 and abs(c.x) < 0.2 else "Base"), 0, True)
    P.obj("Throat", ball((0, 1.02, 0.25), (0.3, 0.2, 0.09), 14, 6), "Glow")
    P.obj("ThroatCore", ball((0, 1.06, 0.26), (0.16, 0.12, 0.06), 12, 6), "Lamp")
    P.obj("Tongue", xf(ball((0, 1.32, 0.29), (0.22, 0.26, 0.05), 14, 6), jaw_m.to_3x3(), tuple(jaw_m.translation)), "Accent")
    # rows of small teeth round both jaws, white-hot
    for k in range(17):
        ph = math.radians(-78 + k * (156 / 16))
        x, y = math.sin(ph) * 0.57, 1.3 + math.cos(ph) * 0.59
        ln = 0.06 if abs(k - 8) in (5, 6) else 0.045
        P.obj("Tooth", cone((x, y, 0.33), (x * 0.98, y - 0.005, 0.33 - ln), 0.017, 5), "Lamp", 0, False)
        xl, yl = math.sin(ph) * 0.53, 1.27 + math.cos(ph) * 0.54
        b = jaw_m @ Vector((xl, yl, 0.29)); tp = jaw_m @ Vector((xl * 0.98, yl - 0.005, 0.29 + ln * 0.9))
        P.obj("Tooth", cone(b, tp, 0.016, 5), "Lamp", 0, False)
    for s_ in (1, -1):
        P.obj("Nostril", ball((s_ * 0.12, 1.86, 0.44), (0.035, 0.02, 0.022), 8, 4), "Dark")
        # the eye: a bulge on top of the head, a fiery gold eyeball with a vertical slit, a heavy lid slanting down to the snout, a brow ridge
        E = Vector((s_ * 0.36, 1.45, 0.5))
        P.obj("EyeBulge", ball(tuple(E - Vector((s_ * 0.02, 0.08, 0.08))), (0.17, 0.16, 0.13), 14, 7), "Base", 0, True)
        P.obj("Eye", ball(tuple(E + Vector((s_ * 0.02, 0.07, 0.03))), (0.165, 0.165, 0.155), 18, 9), "Glass")
        look = Vector((s_ * 0.3, 1.0, 0.12)).normalized(); sx = look.cross(Vector((0, 0, 1))).normalized(); upv = sx.cross(look).normalized()
        P.obj("Pupil", oriented_ball(E + Vector((s_ * 0.02, 0.07, 0.03)) + look * 0.16 - upv * 0.01, (0.034, 0.018, 0.1), sx, look, upv, 8, 4), "Dark")
        P.obj("Glint", ball(tuple(E + Vector((s_ * 0.02, 0.07, 0.03)) + look * 0.145 + upv * 0.04 - sx * 0.04 * s_), (0.022, 0.012, 0.018), 6, 3), "Lamp")
        lid = sa_dome((0, 0, 0), 0.185, 0.185, 0.075, True, 18, 5)
        rot = Matrix.Rotation(math.radians(-s_ * 24), 3, look) @ Matrix.Rotation(math.radians(-14), 3, sx)
        P.obj("Lid", xf(lid, rot, tuple(E + Vector((s_ * 0.02, 0.07, 0.03)) + rot @ Vector((0, 0, 0.085)))), "Base", 0, True)
        P.obj("Brow", pipe(bez((s_ * 0.17, 1.6, 0.6), (s_ * 0.3, 1.66, 0.72), (s_ * 0.46, 1.6, 0.73), (s_ * 0.58, 1.42, 0.64), 8),
                           [0.04, 0.055, 0.065, 0.065, 0.06, 0.055, 0.045, 0.035, 0.025], 8), "Base")
        # the paratoid gland behind the eye, pitted with pores, and a row of smaller glands running on down the back
        G = Vector((s_ * 0.33, 1.0, 0.47))
        P.obj("Paratoid", oriented_ball(G, (0.15, 0.25, 0.1), Vector((1, 0, 0)), Vector((s_ * -0.18, 1, 0)).normalized(), Vector((0, 0, 1)), 14, 7), "Trim")
        for a_ in range(3):
            for b_ in range(4):
                q = G + Vector((s_ * (-0.06 + a_ * 0.06), -0.15 + b_ * 0.1, 0.095 - abs(a_ - 1) * 0.02 - abs(b_ - 1.5) * 0.012))
                P.obj("Pore", ball(tuple(q), (0.013, 0.013, 0.008), 6, 3), "Dark")
        for j in range(3):
            y = 0.7 - j * 0.28
            P.obj("Gland", ball((s_ * 0.24, y, 0.48 - j * 0.03), (0.08, 0.11, 0.06), 10, 5), "Trim")

    # ---- the crown of obsidian and gold, its gold running in the heat
    CC = Vector((0, 1.06, 0.55))
    P.obj("Crown", lathe([(0.25, -0.05), (0.27, -0.03), (0.27, 0.08), (0.25, 0.09), (0.23, 0.07), (0.23, -0.03)], 24, "z", tuple(CC)), "Metal")
    for k in range(10):
        a = 2 * math.pi * k / 10
        d = Vector((math.sin(a), math.cos(a), 0)); b = CC + d * 0.25 + Vector((0, 0, 0.07))
        front = math.cos(a)
        if k % 2 == 0:   # a shard of obsidian: a faceted, leaning blade of black glass
            h = 0.3 + 0.12 * max(0, front)
            P.obj("Obsidian", cone(b, b + d * 0.07 + Vector((0, 0, h)), 0.06, 4), "Dark", 0, False)
        else:
            P.obj("CrownPoint", cone(b, b + d * 0.03 + Vector((0, 0, 0.14)), 0.045, 6), "Metal", 0, False)
            P.obj("Ruby", ball(tuple(b + d * 0.025 - Vector((0, 0, 0.05))), (0.03, 0.02, 0.03), 8, 4), "Accent")
        # a drip of molten gold under every point
        q = CC + d * 0.268 - Vector((0, 0, 0.04))
        ln = 0.06 + 0.05 * (k % 3) / 2
        P.obj("GoldDrip", pipe([q, q - Vector((0, 0, ln * 0.6)), q - Vector((0, 0, ln))], [0.022, 0.016, 0.0], 6), "Metal")
        P.obj("GoldDrop", ball(tuple(q - Vector((0, 0, ln + 0.03))), (0.018, 0.018, 0.026), 6, 3), "Metal")
    P.obj("FireOpal", ball(tuple(CC + Vector((0, 0.27, 0.02))), (0.06, 0.03, 0.06), 10, 5), "Glow")

    # ---- the crest of fire along the glowing seam of his back
    for j in range(7):
        u = (j + 0.5) / 7 * 0.92
        i = int(u * (nt - 1)); p = trunk[i] + Vector((0, 0, rz[i] * 0.98))
        h = lerp_keys(u, [(0, 0.34), (0.2, 0.46), (0.6, 0.32), (1, 0.18)])
        P.part(FX, sa_flame(p, h, 0.065, 0.3, 0.04 * (1 if j % 2 else -1)), "Glow", (0, 0, 0))
        P.part(FX, sa_flame(p + Vector((0, 0.02, 0.01)), h * 0.58, 0.035, 0.18, 0.0), "Lamp", (0, 0, 0))

    # ---- the legs: sprawling, elbows and knees out to the sides, paddling in the lava
    def leg(name, sh, el, wr, toes, up_len):
        hubp = tuple(sh)
        P.part(name, pipe([sh, el], [0.13, 0.1], 10), lambda c, n_: "Trim" if n_.z > 0.55 and (c - sh).length > 0.08 else "Base", hubp, 1)
        P.part(name, ball(tuple(el), (0.1, 0.1, 0.1), 10, 5), "Base", hubp)
        P.part(name, pipe([el, wr], [0.095, 0.075], 10), "Base", hubp, 1)
        P.part(name, ball(tuple(wr), (0.1, 0.11, 0.05), 10, 5), "Base", hubp)
        for d, ln in toes:
            tp = wr + d * ln
            P.part(name, pipe([wr, wr + d * ln * 0.55 + Vector((0, 0, 0.015)), tp], [0.035, 0.03, 0.022], 6), "Base", hubp)
            P.part(name, ball(tuple(tp), (0.032, 0.032, 0.022), 6, 3), "Trim", hubp)
        # a splash ring where the hand strikes the lava
        for k in range(5):
            a = 2 * math.pi * k / 5
            q = wr + Vector((math.cos(a) * 0.15, math.sin(a) * 0.15, -0.02))
            P.part(name, cone(q, q + Vector((math.cos(a) * 0.04, math.sin(a) * 0.04, 0.1 + 0.03 * (k % 2))), 0.022, 5), "Glow", hubp)
    for s_ in (1, -1):
        fwd = [Vector((s_ * math.sin(math.radians(a)), math.cos(math.radians(a)), 0)) for a in (-15, 15, 45, 80)]
        leg("SwayLeg" + ("0" if s_ > 0 else "1"), Vector((s_ * 0.36, 0.62, 0.18)), Vector((s_ * 0.74, 0.86, 0.22)), Vector((s_ * 0.88, 1.12, 0.13)),
            [(d, l) for d, l in zip(fwd, (0.13, 0.16, 0.15, 0.11))], 0)
        bwd = [Vector((s_ * math.sin(math.radians(a)), math.cos(math.radians(a)), 0)) for a in (-10, 25, 60, 95, 130)]
        leg("SwayLeg" + ("2" if s_ > 0 else "3"), Vector((s_ * 0.36, -0.72, 0.12)), Vector((s_ * 0.76, -0.85, 0.2)), Vector((s_ * 0.9, -1.12, 0.12)),
            [(d, l) for d, l in zip(bwd, (0.12, 0.16, 0.18, 0.16, 0.11))], 0)

    # ---- the lava splashing up along his flanks, a bow wave at his chin, a wake of ripples behind him
    for i in range(2, nt - 2, 3):
        p = trunk[i]
        for s_ in (1, -1):
            q = Vector((p.x + s_ * (rx[i] + 0.03), p.y, SA_SURF))
            for j, (dx, dy, h) in enumerate(((0.08, 0.0, 0.12), (0.05, 0.05, 0.08), (0.06, -0.05, 0.09))):
                P.part(FX, cone(q, q + Vector((s_ * dx, dy, h)), 0.025, 5), "Glow", (0, 0, 0))
    bow = [Vector((math.sin(math.radians(a)) * 0.62, 1.32 + math.cos(math.radians(a)) * 0.66, SA_SURF + 0.02)) for a in range(-70, 71, 14)]
    P.part(FX, pipe(bow, [0.03] + [0.05] * (len(bow) - 2) + [0.03], 8), "Lamp", (0, 0, 0))
    for q in bow[1:-1]:
        o = (q - Vector((0, 1.32, q.z))).normalized()
        P.part(FX, cone(q, q + o * 0.07 + Vector((0, 0, 0.13)), 0.025, 5), "Glow", (0, 0, 0))
    for j, y in enumerate((-1.25, -1.6, -1.95)):
        p, sd, up, w, t = at(L[int(0.3 * n)] + (j - 1) * 0.3)
        c = p + up * (t * 0.27)
        wing = w * (0.45 + 0.13 * j)
        chev = [c + sd * wing - (sd.cross(up)) * 0.18, c, c - sd * wing - (sd.cross(up)) * 0.18]
        P.part(FX, pipe(chev, [0.02, 0.028, 0.02], 6), "Lamp", (0, 0, 0))

    P.part("Muzzle", ball((0, 1.62, 0.25), (0.07, 0.04, 0.05), 8, 4), "Glow", (0, 1.62, 0.25))
    return P



# ================================================================= scarab (2026-10-13 remake)
SCB_C = Vector((0.0, 0.25, -0.85))   # the sun ball's centre
SCB_R = 1.0                           # and radius
SCB_TILT = 30.0                       # the beetle leans head-down over the front of the ball this much


def sc_shell(ys, W, H, zb, nu=97, nb=9, ridge=None, lip=0.1):
    """a domed shell along y: at each y a top arch of nu points evenly in u = x / W (so painted grooves come out even) over a shallow
    bottom of nb points; W(y), H(y) the half-width and the dome height above zb; ridge(u) lifts the top (grooves)."""
    bm = bmesh.new(); rings = []
    for y in ys:
        w, h = max(W(y), 1e-3), max(H(y), 1e-3)
        ring = []
        for i in range(nu):
            u = -1.0 + 2.0 * i / (nu - 1)
            z = zb + h * max(0.0, 1.0 - abs(u) ** 2.2) ** 0.5 + (ridge(u) * h if ridge else 0.0)
            ring.append(bm.verts.new((w * u, y, z)))
        for i in range(1, nb - 1):
            u = 1.0 - 2.0 * i / (nb - 1)
            ring.append(bm.verts.new((w * u * 0.96, y, zb - lip * (1.0 - u * u))))
        rings.append(ring)
    n = len(rings[0])
    for r0, r1 in zip(rings, rings[1:]):
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((r0[i], r0[j], r1[j], r1[i]))
    bm.faces.new(list(reversed(rings[0]))); bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def sc_plate(outline, c, rings=6, thick=0.06, dome=0.1):
    """a solid plate: concentric copies of a closed outline (2D points about c) on top, domed toward the middle, a flat copy under it."""
    bm = bmesh.new(); top = []; c = Vector(c)
    for k in range(rings + 1):
        s = 1.0 - k / rings * 0.999
        top.append([bm.verts.new(c + Vector((p[0] * s, p[1] * s, dome * (1.0 - s * s)))) for p in outline])
    bot = [bm.verts.new(c + Vector((p[0], p[1], -thick))) for p in outline]
    n = len(outline)
    for r0, r1 in zip(top, top[1:]):
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((r0[i], r0[j], r1[j], r1[i]))
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((bot[i], bot[j], top[0][j], top[0][i]))
    bm.faces.new(list(reversed(bot)))
    cen = bm.verts.new(c + Vector((0, 0, dome)))
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((top[-1][i], top[-1][j], cen))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def sc_fib(n):
    """n points spread evenly over the unit sphere."""
    g = math.pi * (3.0 - math.sqrt(5.0)); out = []
    for i in range(n):
        z = 1.0 - 2.0 * (i + 0.5) / n; r = math.sqrt(1.0 - z * z)
        out.append(Vector((math.cos(g * i) * r, math.sin(g * i) * r, z)))
    return out


SCB_SITES = sc_fib(22)   # the crust's plates

def sc_cell(d):
    """for a direction d: (nearest plate, how far inside its plate the point lies - 0 on a seam)."""
    best = sorted(((d.dot(s), i) for i, s in enumerate(SCB_SITES)), reverse=True)
    return best[0][1], best[0][0] - best[1][0]


def sc_crust(c, r, seg=112, rings=56):
    """the sun's crust: a sphere broken into plates of black slag, the seams between them sunk and molten."""
    bm = ball((0, 0, 0), (1, 1, 1), seg, rings)
    for v in bm.verts:
        d = v.co.normalized(); _, e = sc_cell(d)
        k = 1.0 - 0.06 * max(0.0, 1.0 - e / 0.07) + 0.02 * math.sin(d.x * 9 + d.y * 7 + d.z * 11)
        v.co = Vector(c) + d * r * k
    return bm

def sc_crust_paint(c, n):
    d = (c - SCB_C).normalized(); i, e = sc_cell(d)
    if e < 0.012: return "Lamp"
    if e < 0.04: return "Glow"
    return "Dark" if i % 3 else "Metal"


def L_scarab():
    """The EMBER SCARAB (2026-10-14, remade: "same as the alien bosses - realistic details, scarier, keep the cartoon shape"; "something
    impressive and new - when people see it they say ahhhh"): the same giant beetle with a horn, mandibles and an obsidian shell veined with
    lava, now built like a real sacred scarab, a dung beetle, in volcanic armour. The head is a scarab's: the broad flat clypeus spread over
    the face like a shovel, its front edge cut into six even teeth tipped in gold, the eyes glowing amber from under its side lobes behind a
    heavy obsidian brow ridge drawn down in a frown, curved gold mandibles under the shovel with a furnace glow between them (his shots leave
    from it), and the antennae ending in the gold leaf-club of a scarab, three lamellae fanned; from the head rises a great curved horn,
    its tip burning. Behind it the domed pronotum, broad and smooth, its rim a thin line of magma and two short horns at its front; then the
    elytra, the two wing cases closed along the suture, each ribbed lengthwise by seven striae - and every groove, the suture and the rim
    of the shell glow with molten lava, evenly, as if the beetle were cast in obsidian over a core of fire. Six real legs: the front pair the
    digging legs of a scarab, the tibia broad and flat with four teeth along its outer edge; the middle and hind legs long and slender,
    spurred gold at the end of the tibia, five-jointed tarsi with hooked gold claws; magma glowing in every joint.
    It flies by ROLLING THE SUN, as Khepri pushes the sun across the sky: under him a ball of fire as big as he is, a crust of black slag
    broken into plates with white-hot lava welling in every seam between them, tongues of flame licking evenly off its face toward the
    player and off its back; and the scarab rides it as a dung beetle climbs on top of its ball - head down over the front, glaring at the
    player, the digging legs gripping the front of the ball, the middle and hind legs spread over its top and back. The ball churns as it
    goes (RollSun); a corona of flame burns round its rim, and a trail of fire and embers streams away behind it."""
    P = Boss("scarab", {"Base": ((0.05, 0.045, 0.055), 0.85), "Belly": ((0.20, 0.05, 0.03), 0.5), "Accent": ((0.95, 0.62, 0.15), 0.8),
                        "Trim": ((0.42, 0.24, 0.10), 0.6), "Glass": ((1.0, 0.55, 0.12), 0.9), "Dark": ((0.035, 0.025, 0.025), 0.25),
                        "Glow": ((1.0, 0.36, 0.04), 0.5), "Metal": ((0.13, 0.09, 0.08), 0.4), "Lamp": ((1.0, 0.80, 0.32), 0.8)})
    C, R = SCB_C, SCB_R
    th = math.radians(SCB_TILT)
    nrm = Vector((0, math.sin(th), math.cos(th)))
    T = C + nrm * (R + 0.16)
    M = Matrix.Translation(T) @ Matrix.Rotation(-th, 4, "X") @ Matrix.Translation((0, -0.4, 0))
    R3 = Matrix.Rotation(-th, 3, "X")
    def W_(p): return M @ Vector(p)                          # beetle-local point -> world
    n0 = len(P.parts)

    # ---- the elytra: a domed shell ribbed with seven striae a side, every groove and the suture glowing
    def EW(y):
        if y > -0.25: return 0.62 * (1.0 - 0.1 * ((y + 0.25) / 0.57) ** 2)
        return 0.62 * math.sqrt(max(0.0, 1.0 - ((y + 0.25) / 0.85) ** 2))
    def EH(y):
        if y > -0.3: return 0.46 * (1.0 - 0.15 * ((y + 0.3) / 0.62) ** 2)
        return 0.46 * math.sqrt(max(0.0, 1.0 - ((y + 0.3) / 0.8) ** 2))
    ys = [0.32 - 1.415 * (1 - math.cos(math.pi / 2 * i / 35)) for i in range(36)]
    def stria(u):
        a = abs(u) * 8.0; f = abs(a - round(a))
        return 0 < round(a) < 8 and f < 0.085
    def groove(u):
        a = abs(u) * 8.0; f = abs(a - round(a))
        return -0.035 * max(0.0, 1.0 - f / 0.18) if 0 < round(a) < 8 else (-0.03 if abs(u) < 0.02 else 0.0)
    el = sc_shell(ys, EW, EH, -0.06, 129, 9, groove, 0.08)
    def el_paint(c, n):
        l = R3.inverted() @ (c - T); nl = R3.inverted() @ n
        if nl.z < -0.35: return "Belly"
        u = l.x / max(EW(l.y), 0.05)
        if abs(u) < 0.022 or abs(u) > 0.965 or stria(u): return "Glow"
        return "Base"
    xf(el, M.to_3x3(), T)
    P.obj("Elytra", el, el_paint)

    # ---- the pronotum: a broad smooth dome, its rim a line of magma, two short horns at its front edge
    def PW(y): return 0.66 + 0.06 * math.sin(math.pi * (y - 0.3) / 0.52) - 0.16 * max(0.0, (y - 0.62) / 0.2) ** 1.5
    def PH(y): return 0.5 * (1.0 - 0.6 * ((y - 0.42) / 0.45) ** 2)
    pys = [0.3 + 0.52 * i / 20 for i in range(21)]
    pr = sc_shell(pys, PW, PH, -0.05, 97, 9, None, 0.08)
    def pr_paint(c, n):
        l = R3.inverted() @ (c - T); nl = R3.inverted() @ n
        if nl.z < -0.35: return "Belly"
        u = l.x / max(PW(l.y), 0.05)
        return "Glow" if abs(u) > 0.955 or l.y > 0.81 else "Base"
    xf(pr, M.to_3x3(), T)
    P.obj("Pronotum", pr, pr_paint)
    for s in (1, -1):
        P.obj("PronotumHorn", pipe([W_((s * 0.26, 0.66, 0.4)), W_((s * 0.3, 0.84, 0.48)), W_((s * 0.28, 0.96, 0.54))], [0.08, 0.05, 0.0], 8),
              lambda c, n: "Glow" if (R3.inverted() @ (c - T)).y > 0.88 else "Base")

    # ---- the head: a small dome under the clypeus, the clypeus a toothed shovel
    P.obj("Head", ball(W_((0, 1.1, 0.0)), (0.36, 0.26, 0.2), 16, 8), "Base", 0)
    out = []
    for i in range(121):
        phi = math.radians(-105 + 210 * i / 120)
        k = 1.0
        if abs(math.degrees(phi)) < 60:
            q = (math.degrees(phi) + 60) / 20.0; f = q - math.floor(q)
            k = 1.0 + 0.14 * (1.0 - abs(f - 0.5) * 2.0) ** 1.4
        out.append((math.sin(phi) * 0.56 * k, math.cos(phi) * 0.4 * k))
    out = [(-0.5, -0.12)] + out + [(0.5, -0.12)]
    out = list(reversed(out))
    cl = sc_plate(out, (0, 1.12, 0.1), 7, 0.07, 0.12)
    for v in cl.verts:
        l = v.co - Vector((0, 1.12, 0.1))
        v.co.z -= 0.16 * max(0.0, l.y / 0.45) ** 2           # the shovel's front edge bends down toward the ball
    def cl_paint(c, n):
        l = R3.inverted() @ (c - T); d = Vector((l.x / 0.56, (l.y - 1.12) / 0.4, 0))
        if d.length > 1.02 and l.y > 1.25: return "Accent"     # the gold tips of the teeth
        if d.length > 0.93: return "Glow"
        return "Base"
    xf(cl, M.to_3x3(), T)
    P.obj("Clypeus", cl, cl_paint)
    for s in (1, -1):
        P.obj("Eye", ball(W_((s * 0.44, 1.0, 0.2)), (0.15, 0.13, 0.12), 14, 7), "Lamp")
        P.obj("Brow", pipe([W_((s * 0.68, 0.9, 0.22)), W_((s * 0.5, 0.94, 0.3)), W_((s * 0.3, 1.04, 0.28)), W_((s * 0.12, 1.14, 0.22))], [0.04, 0.075, 0.06, 0.03], 8), "Base")
        P.obj("Mandible", pipe(bez(W_((s * 0.25, 1.25, -0.06)), W_((s * 0.62, 1.55, -0.08)), W_((s * 0.5, 1.95, -0.06)), W_((s * 0.14, 2.0, -0.02)), 8),
                               [0.1, 0.095, 0.085, 0.075, 0.065, 0.05, 0.035, 0.018, 0.0], 10), lambda c, n: "Accent")
        for k in range(3):                                    # inner teeth of the mandible
            b = W_((s * (0.5 - 0.06 * k), 1.62 + 0.11 * k, -0.07))
            P.obj("MandTooth", cone(b, b + (M.to_3x3() @ Vector((-s * 0.12, 0.0, 0.0))), 0.035, 5), "Accent", 0, False)
        a0 = W_((s * 0.42, 1.18, -0.06)); a1 = W_((s * 0.62, 1.38, -0.02))
        P.obj("Antenna", pipe([a0, a1], [0.025, 0.02], 6), "Trim")
        for k in range(3):                                    # the lamellate club: three gold leaves fanned
            ang = math.radians(-25 + 25 * k)
            d = M.to_3x3() @ Vector((s * math.cos(ang) * 0.6, 0.6, math.sin(ang) * 0.5)).normalized()
            lam = ball((0, 0, 0), (0.1, 0.035, 0.06), 10, 5)
            q = d.to_track_quat("X", "Z").to_matrix()
            P.obj("Club", xf(lam, q, a1 + d * 0.09), "Accent")
    # the mouth's glow and the horn
    hb = [W_((0, 1.05, 0.2)), W_((0, 1.28, 0.65)), W_((0, 1.1, 1.08)), W_((0, 0.82, 1.28))]
    hp = bez(*hb, 10)
    P.obj("Horn", pipe(hp, [0.17 * (1 - i / 10) ** 0.8 + 0.001 for i in range(10)] + [0.0], 12),
          lambda c, n: "Glow" if (R3.inverted() @ (c - T)).z > 1.0 else "Base")
    for k in (3, 5, 7):                                       # magma rings round the horn
        P.obj("HornRing", pipe([hp[k] - (hp[k + 1] - hp[k]) * 0.12, hp[k] + (hp[k + 1] - hp[k]) * 0.12],
                               [0.17 * (1 - k / 10) ** 0.8 + 0.012] * 2, 12), "Glow")
    # the belly under the shell
    P.obj("Venter", ball(W_((0, -0.1, -0.08)), (0.5, 0.78, 0.12), 16, 6), "Belly")

    # ---- the legs, their feet on the ball
    def on_ball(d): return C + Vector(d).normalized() * (R + 0.015)
    def leg(hip_l, foot, kind, s):
        hip = W_(hip_l)
        mid = (hip + foot) * 0.5
        knee = hip + Vector((s * 0.5, 0, 0)) + (hip - C).normalized() * 0.12 + (foot - hip) * 0.25
        P.obj("Femur", pipe([hip, (hip + knee) * 0.5, knee], [0.085, 0.08, 0.06], 10), "Base")
        P.obj("Knee", ball(knee, (0.055, 0.055, 0.055), 10, 5), "Glow")
        if kind == "dig":
            # the scarab's digging tibia: a broad flat blade with four teeth along its outer edge
            tdir = (foot - knee); L = tdir.length; tdir.normalize()
            side = tdir.cross((foot - C).normalized()).normalized() * (1 if s > 0 else -1)
            if side.x * s < 0: side = -side
            pts = []
            for t, w in ((0.0, 0.05), (0.5, 0.09), (1.0, 0.13)):
                p = knee + tdir * L * t
                for sw in (-1, 1):
                    for sz in (-0.025, 0.025):
                        pts.append(p + side * sw * w + (foot - C).normalized() * sz)
            P.obj("Tibia", hull([tuple(p) for p in pts]), "Base", 0, False)
            for k in range(4):
                p = knee + tdir * L * (0.35 + 0.2 * k)
                w = 0.05 + 0.08 * (0.35 + 0.2 * k)
                P.obj("TibiaTooth", cone(p + side * w * 0.7, p + side * (w + 0.11) + tdir * 0.04, 0.035, 5), "Accent", 0, False)
            tip = foot
        else:
            P.obj("Tibia", pipe([knee, foot], [0.05, 0.04], 8), "Base")
            tdir = (foot - knee).normalized()
            for sw in (-1, 1):                                # the two spurs at the end of the tibia
                sp = tdir.cross(Vector((0, 0, 1))).normalized() * sw
                P.obj("Spur", cone(foot - tdir * 0.03, foot + tdir * 0.1 + sp * 0.07, 0.022, 5), "Accent", 0, False)
            tip = foot
        # five-jointed tarsus along the ball's surface, two hooked gold claws
        nrmf = (tip - C).normalized()
        tang = (Vector((s * 0.6, 0.4 if kind == "dig" else -0.4, 0)) - nrmf * nrmf.dot(Vector((s * 0.6, 0.4 if kind == "dig" else -0.4, 0)))).normalized()
        q = tip; tp = [q]
        for k in range(5):
            q = C + ((q + tang * 0.07) - C).normalized() * (R + 0.035); tp.append(q)
        P.obj("Tarsus", pipe(tp, [0.035, 0.032, 0.03, 0.027, 0.024, 0.02], 6), "Base")
        for p in tp[1:-1]: P.obj("TarsusJoint", ball(p, (0.034, 0.034, 0.034), 6, 3), "Base")
        for sw in (-1, 1):
            cs = tang.cross(nrmf).normalized() * sw * 0.035
            P.obj("Claw", pipe([q, q + tang * 0.05 + cs, q + tang * 0.07 + cs - nrmf * 0.04], [0.018, 0.012, 0.0], 5), "Accent")
    for s in (1, -1):
        leg((s * 0.42, 0.85, -0.12), on_ball((s * 0.55, 0.62, 0.55)), "dig", s)
        leg((s * 0.5, 0.25, -0.12), on_ball((s * 0.95, 0.12, 0.42)), "walk", s)
        leg((s * 0.45, -0.25, -0.12), on_ball((s * 0.72, -0.5, 0.62)), "walk", s)
    P.part("Muzzle", ball(W_((0, 1.7, -0.1)), (0.12, 0.1, 0.1), 10, 5), "Glow", tuple(W_((0, 1.7, -0.1))))

    # ---- the sun he rolls: a crust of slag plates with lava in every seam, flames licking off its face and its back; it churns (RollSun)
    P.part("RollSun", sc_crust(C, R), sc_crust_paint, tuple(C))
    for d in sc_fib(46):
        if d.y < 0.7: continue                       # the flames on the face and the back; the rim has its corona
        s0 = C + d * R
        t = Vector((0, 1, 0)).cross(d)
        t = t.normalized() if t.length > 1e-4 else Vector((1, 0, 0))
        L = 0.34
        pts = [s0 - d * 0.06, s0 + d * L * 0.4, s0 + d * L * 0.75 + t * 0.12, s0 + d * L + t * 0.26]
        P.part("RollSun", pipe(pts, [0.13, 0.11, 0.06, 0.0], 8), "Glow", tuple(C))
        P.part("RollSun", pipe([s0 - d * 0.04, s0 + d * L * 0.3, s0 + d * L * 0.5 + t * 0.08], [0.07, 0.05, 0.0], 6), "Lamp", tuple(C))
    # the corona round its rim (still), leaving the top where he rides
    for k in range(13):
        a = math.radians(60 + 240 * k / 12)                   # from the upper right round under it to the upper left
        d = Vector((math.sin(a), 0.0, math.cos(a)))
        s0 = C + d * R * 0.98
        L = 0.42 + 0.14 * (k % 2)
        tg = Vector((0, -1, 0))
        pts = [s0 - d * 0.05, s0 + d * L * 0.45, s0 + d * L * 0.8 + tg * 0.14, s0 + d * L + tg * 0.3]
        P.part("Cloth", pipe(pts, [0.13, 0.1, 0.05, 0.0], 8), "Glow", (0, 0, 0))
        P.part("Cloth", pipe([s0 - d * 0.04, s0 + d * L * 0.35, s0 + d * L * 0.55 + tg * 0.06], [0.08, 0.06, 0.0], 6), "Lamp", (0, 0, 0))
    # the trail: three streamers of fire behind the ball and embers evenly along them
    for k, (x, z) in enumerate(((-0.45, -0.55), (0.45, -0.55), (0.0, -1.2))):
        b = C + Vector((x * 0.9, -R * 0.75, z * 0.6 + 0.1))
        path = bez(b, b + Vector((x * 0.2, -0.6, 0.05)), b + Vector((x * 0.5, -1.2, 0.2)), b + Vector((x * 0.7, -1.75, 0.35)), 8)
        P.part("Cloth", pipe(path, [0.2, 0.19, 0.17, 0.14, 0.11, 0.08, 0.05, 0.025, 0.0], 10), "Glow", (0, 0, 0))
        for j in range(1, 6):
            e = path[min(8, j + 1)] + Vector(((j % 2 - 0.5) * 0.35, -0.1, (0.2 if j % 2 else -0.15)))
            P.part("Cloth", ball(e, (0.05, 0.05, 0.05), 4, 2), "Lamp", (0, 0, 0))
    return P



# ================================================================= golem (2026-10-13 remake)
# The inferno golem riding a meteor (2026-10-14 remake), merged into lava_bosses.py.

GO_MC = Vector((0, 0.3, -0.8))    # the meteor's centre
GO_MR = 0.98                      # and radius
GO_TAIL = (-0.6, -3.5)            # the fire tail runs back along y, on the meteor's axis (x = 0, z = GO_MC.z)


def go_fib(n, seed=0.0):
    """n directions spread evenly over the sphere (a Fibonacci spiral)."""
    out = []
    for i in range(n):
        z = 1 - 2 * (i + 0.5) / n; r = math.sqrt(max(0.0, 1 - z * z)); a = i * 2.399963 + seed
        out.append(Vector((math.cos(a) * r, math.sin(a) * r, z)))
    return out

def go_cells(d, seeds):
    """the nearest and second-nearest seed to direction d: (index, angular gap to the cell edge)."""
    best = sorted(((d.angle(s, 0.0), i) for i, s in enumerate(seeds)))[:2]
    return best[0][1], (best[1][0] - best[0][0]) * 0.5

def go_plated(c, r, n, seed, crack=0.09, seg=32, rings=20):
    """an ellipsoid of cooled lava crust broken into n even plates: each plate a flattish facet (the crust breaks into slabs), the seams
    between them sunk into cracks. Returns the bmesh and a paint function: magma in the cracks, red-hot crust along their lips, the plates
    black basalt or grey crust."""
    c = Vector(c); seeds = go_fib(n, seed)
    rnd = [speckle(s * 3.1, 1.7) for s in seeds]
    bm = ball(tuple(c), r, seg, rings)
    for v in bm.verts:
        q = v.co - c; d = Vector((q.x / r[0], q.y / r[1], q.z / r[2]))
        if d.length < 1e-6: continue
        d.normalize(); i, gap = go_cells(d, seeds)
        th = min(d.angle(seeds[i], 0.0), 0.9)
        k = 0.97 + 0.04 * rnd[i] - 0.06 * (th / 0.6) ** 2                        # each plate a low dome, sinking toward its edges
        if gap < crack: k -= 0.05 * (1 - gap / crack) ** 1.5                      # the crack between plates
        v.co = c + q * k
    def paint(p, nrm):
        q = p - c; d = Vector((q.x / r[0], q.y / r[1], q.z / r[2]))
        if d.length < 1e-6: return "Base"
        i, gap = go_cells(d.normalized(), seeds)
        if gap < crack * 0.42: return "Glow"
        if gap < crack * 0.85: return "Metal"
        return "Belly" if rnd[i] > 0.62 else "Base"
    return bm, paint

def go_columns(P, name, c, nrm, R, cr, hfn, base_paint="Glow"):
    """a patch of basalt columns, the hexagonal columnar jointing of cooled lava: hexagonal prisms packed in a honeycomb within radius R
    of c, standing along nrm, each hfn(u, v) tall (stepped like the Giant's Causeway); their tops pale, magma glowing in the joints."""
    c, n = Vector(c), Vector(nrm).normalized()
    a = n.cross(Vector((0, 0, 1)) if abs(n.z) < 0.9 else Vector((1, 0, 0))).normalized(); b = n.cross(a).normalized()
    s3 = math.sqrt(3)
    P.obj(name + "Bed", xf(lathe([(0.0, -0.02), (R + cr, -0.02), (R + cr, 0.02), (0.0, 0.02)], 18, "z"),
                           Matrix((a, b, n)).transposed(), tuple(c)), base_paint, 0, False)
    m = int(R / cr) + 2
    for i in range(-m, m + 1):
        for j in range(-m, m + 1):
            u = 1.5 * cr * i; v = s3 * cr * (j + 0.5 * (i % 2))
            if u * u + v * v > R * R: continue
            h = hfn(u / R, v / R); p = c + a * u + b * v
            col = pipe([p, p + n * h], [cr * 0.9, cr * 0.9], 6)
            # turn the hexagon so its corners point along a, matching the packing
            P.obj(name, col, lambda q, nn, n=n: "Trim" if nn.dot(n) > 0.85 else ("Belly" if speckle(q, 2.3) > 0.55 else "Base"), 0, False)

def go_meteor():
    """the meteor: a rough asteroid with even craters, ablation grooves streaked back along its flanks, its front face white-hot."""
    c, R = GO_MC, GO_MR
    craters = [d for d in go_fib(18, 0.7) if d.y < 0.35]
    bm = ball(tuple(c), (R, R * 1.1, R * 0.92), 56, 34)
    for v in bm.verts:
        q = v.co - c; d = q.normalized(); k = 1.0
        k += 0.035 * math.sin(d.x * 9 + d.z * 4) * math.sin(d.z * 7 - d.x * 3)          # a lumpy body
        for cd in craters:                                                                  # bowl-shaped craters with raised rims
            t = d.angle(cd, 0.0) / 0.28
            if t < 1.0: k -= 0.09 * (1 - t * t)
            elif t < 1.35: k += 0.03 * (1 - abs(t - 1.17) / 0.18) if abs(t - 1.17) < 0.18 else 0.0
        if d.y < 0.55:                                                                      # ablation: grooves streaming back from the hot face
            g = math.atan2(d.z, d.x) * 14
            k -= 0.03 * max(0.0, math.sin(g)) * (0.55 - d.y)
        v.co = c + q * k
    def paint(p, n):
        d = (p - c).normalized()
        if d.y > 0.9: return "Lamp"                        # the white-hot nose
        if d.y > 0.74: return "Glow"
        if d.y > 0.5: return "Metal"                       # glowing red as it cools back
        g = math.atan2(d.z, d.x) * 14
        if d.y < 0.3 and math.sin(g) > 0.75: return "Dark"  # the soot in the grooves
        for cd in craters:
            if d.angle(cd, 0.0) < 0.17: return "Dark"
        return "Belly" if n.z > 0.5 else "Base"
    return bm, paint

def go_flame(y0, y1, r0, phase, tongues, twist=0.6, depth=0.45, N=14):
    """a cone of flame streaming back from y0 to y1 along the tail axis, its rim cut into tongues (a star in section, the gaps between the
    tongues deepening down the tail) that twist and ripple as they go."""
    zc = GO_MC.z; bm = bmesh.new(); seg = tongues * 4; rings = []
    for i in range(N + 1):
        t = i / N; y = y0 + (y1 - y0) * t
        ring = []
        for k in range(seg):
            a = 2 * math.pi * k / seg + phase + twist * t
            tip = (0.5 + 0.5 * math.cos(tongues * (2 * math.pi * k / seg))) ** 2
            r = r0 * min(1.0, (1 - t) * 1.6) ** 0.5 * (1 - t) ** 0.6 * (1 - depth * (0.35 + 0.65 * t) * (1 - tip))
            r *= 1 + 0.08 * math.sin(t * 9 + k)
            ring.append(bm.verts.new((math.cos(a) * r, y, zc + math.sin(a) * r)))
        rings.append(ring)
    for r0_, r1_ in zip(rings, rings[1:]):
        for k in range(seg): bm.faces.new((r0_[k], r0_[(k + 1) % seg], r1_[(k + 1) % seg], r1_[k]))
    tip = bm.verts.new((0, y1 - 0.15, zc))
    for k in range(seg): bm.faces.new((rings[-1][k], rings[-1][(k + 1) % seg], tip))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm

def L_golem():
    """The INFERNO GOLEM (2026-10-14, remade: "same as the alien bosses - realistic details, scarier, keep the cartoon shape"; "something
    impressive - when people see it they say ahhhh"): the same horned giant of volcanic rock with magma glowing in his cracks, a burning
    heart and great fists, now built from real volcanic rock. His body is cooled lava crust - black basalt and grey crust - broken into
    plates the way a lava lake's crust breaks, each plate bulging a little, and in every seam between them the magma still flows, orange-
    yellow, the crust beside each crack glowing red where it is cooling. On his shoulders and the backs of his forearms stand the
    hexagonal columns of basalt that lava forms as it cools (columnar jointing, as at the Giant's Causeway): honeycomb-packed six-sided
    prisms, stepped in height, their tops pale, magma glowing in the joints between them. In the middle of his chest the crust has burst
    open on his molten core, white-hot in a ring of red, cracks running out from it. He is hulking: a small head sunk between huge
    shoulders, the arms thicker than his body, fists like boulders with pumice knuckles. The head is a rock with a heavy brow jutting over
    two deep sockets, an eye burning yellow-white in each; a jagged mouth split open on magma, teeth of black obsidian; two great horns of
    obsidian, glassy black, sweeping out and forward.
    He flies by RIDING A METEOR: he crouches on a huge flaming meteor plunging at the player, his feet sunk in it and his left fist driven
    into it - a rough asteroid of dark rock with even, bowl-shaped craters ringed by raised rims, the grooves of ablation streaking back
    along its flanks, its front face white-hot, glowing yellow and red behind as it cools. Behind it streams a long tail of fire: a white-
    hot core inside a cone of orange flame inside a cone of red, their tongues twisting as they go, ending in rolling dark smoke; chunks
    of the meteor broken off and sparks spiral along the tail (RollDebris turns them about the tail). His right fist is raised high to
    smash (SwayArm). His shots leave from the molten core in his chest."""
    P = Boss("golem", {"Base": ((0.09, 0.075, 0.075), 0.3), "Belly": ((0.24, 0.21, 0.20), 0.25), "Accent": ((0.78, 0.10, 0.03), 0.45),
                       "Trim": ((0.52, 0.48, 0.44), 0.2), "Glass": ((0.03, 0.025, 0.04), 0.95), "Dark": ((0.035, 0.03, 0.03), 0.3),
                       "Glow": ((1.0, 0.45, 0.05), 0.5), "Metal": ((0.75, 0.16, 0.03), 0.4), "Lamp": ((1.0, 0.88, 0.45), 0.8)})
    # ---- the meteor and its fire tail
    bm, mp = go_meteor(); P.obj("Meteor", bm, mp)
    zc = GO_MC.z
    y0 = GO_MC.y - 0.25
    P.part("Cloth", go_flame(y0, -2.1, 0.62, 0.0, 5, 1.1, 0.45), "Lamp", (0, 0, 0))
    P.part("Cloth", go_flame(y0 + 0.05, -2.8, 0.85, 0.4, 7, 1.0, 0.72), lambda c, n: "Glow" if c.y > -1.7 else "Accent", (0, 0, 0))
    P.part("Cloth", go_flame(y0 + 0.1, -3.3, 0.98, 0.9, 9, -0.9, 0.85), lambda c, n: "Accent" if c.y > -2.4 else "Dark", (0, 0, 0))
    for k in range(14):   # the bow of re-entry fire: tongues licking back from round the hot face, evenly
        a = 2 * math.pi * k / 14; d = Vector((math.cos(a), 0, math.sin(a)))
        b0 = GO_MC + d * GO_MR * 0.97 + Vector((0, 0.22, 0)); L = 0.6 + 0.25 * (k % 2)
        P.part("Cloth", pipe([b0, b0 + d * 0.1 + Vector((0, -L * 0.5, 0)), b0 + d * 0.12 + Vector((0, -L, 0))], [0.1, 0.065, 0.0], 6),
               lambda c, n: "Glow" if c.y > GO_MC.y else "Accent", (0, 0, 0))
    for k in range(5):   # the smoke the fire ends in: puffs rolling back, bigger and darker
        t = k / 4; y = -3.05 - 0.28 * k; r = 0.2 + 0.06 * k
        for j in range(3):
            a = 2 * math.pi * j / 3 + k * 0.9
            P.part("Cloth", ball((math.cos(a) * r * 0.6, y, zc + math.sin(a) * r * 0.6), (r * 0.75, r * 0.6, r * 0.75), 10, 6),
                   "Dark" if k > 1 else "Base", (0, 0, 0))
    # chunks broken off and sparks, on a helix round the tail: they turn about it
    rng = random.Random(5); hub = (0.0, -1.9, zc)
    for k in range(10):
        t = k / 9; y = -0.7 - 2.5 * t; a = k * 2.2; r = 0.95 + 0.25 * t
        p = Vector((math.cos(a) * r, y, zc + math.sin(a) * r))
        if k % 2 == 0:
            P.part("RollDebris", rock(tuple(p), 0.2 - 0.1 * t, rng, 10), lambda c, n: "Glow" if n.y > 0.5 else "Base", hub, 0, False)
        for j in range(3):
            q = p + Vector((math.cos(a + 1.1 + j) * 0.25, 0.2 * j - 0.2, math.sin(a + 1.1 + j) * 0.25))
            P.part("RollDebris", ball(tuple(q), (0.045, 0.09, 0.045), 6, 3), "Lamp", hub, 0, False)
    # ---- the golem, crouched on the meteor
    body, bp = go_plated((0, 0.0, 1.05), (0.88, 0.62, 0.72), 18, 0.3, 0.08, 44, 28); P.obj("Torso", body, bp)
    hips, hp = go_plated((0, -0.15, 0.48), (0.62, 0.5, 0.36), 10, 1.1); P.obj("Hips", hips, hp)
    # the molten core bursting through the chest
    core = Vector((0, 0.6, 1.08))
    P.obj("Core", ball(tuple(core), (0.2, 0.13, 0.2), 16, 8), "Lamp")
    P.obj("CoreRim", xf(torus(0.25, 0.06, 0.0, 20, 6), Matrix.Rotation(math.radians(90), 3, "X"), tuple(core + Vector((0, -0.04, 0)))), "Metal")
    for k in range(8):   # cracks of light running out of it, evenly
        a = 2 * math.pi * (k + 0.5) / 8
        d = Vector((math.cos(a), 0, math.sin(a)))
        pts = [core + d * 0.27 + Vector((0, -0.02, 0)), core + d * 0.55 + Vector((0, -0.08, 0)) + Vector((-d.z, 0, d.x)) * 0.05, core + d * 0.78 + Vector((0, -0.2, 0))]
        P.obj("CoreCrack", pipe(pts, [0.035, 0.025, 0.0], 5), "Glow")
    # the legs, crouched: thighs up and out to the knees, shins down into the meteor
    for s in (1, -1):
        hip, knee, foot = Vector((s * 0.42, -0.1, 0.5)), Vector((s * 0.82, 0.38, 0.72)), Vector((s * 0.72, 0.36, 0.18))
        P.obj("Thigh", pipe([hip, (hip + knee) * 0.5 + Vector((s * 0.06, 0, 0.06)), knee], [0.3, 0.33, 0.27], 12), lambda c, n: "Belly" if n.z > 0.5 else "Base")
        kb, kp = go_plated(tuple(knee), (0.28, 0.28, 0.26), 6, 2.0 + s); P.obj("Knee", kb, kp)
        P.obj("Shin", pipe([knee, (knee + foot) * 0.5, foot], [0.26, 0.24, 0.3], 12), lambda c, n: "Glow" if cracks(c * 1.4, n) else "Base")
        P.obj("Foot", rock(tuple(foot + Vector((0, 0.12, 0.0))), 0.3, random.Random(31 + s), 14, (1.1, 1.3, 0.6)), "Base", 0, False)
    # shoulders: great plated boulders crowned with basalt columns
    for s in (1, -1):
        sh = Vector((s * 1.0, -0.05, 1.42))
        sb, spn = go_plated(tuple(sh), (0.55, 0.52, 0.48), 9, 3.0 + s); P.obj("Shoulder", sb, spn)
        go_columns(P, "Columns", sh + Vector((s * 0.14, -0.05, 0.36)), (s * 0.5, -0.1, 1.0), 0.46, 0.09,
                   lambda u, v: 0.16 + 0.32 * (1 - (u * u + v * v)) + 0.08 * math.sin(u * 7 + v * 5))
    # the left arm: driven down into the meteor, gripping it
    sh, el, fi = Vector((-1.12, 0.0, 1.3)), Vector((-1.42, 0.35, 0.72)), Vector((-1.05, 0.95, 0.22))
    P.obj("Arm", pipe([sh, el], [0.33, 0.3], 12), lambda c, n: "Belly" if n.z > 0.4 else "Base")
    fb, fp = go_plated(tuple((el + fi) * 0.5), (0.34, 0.42, 0.3), 7, 4.4); P.obj("Forearm", fb, fp)
    go_columns(P, "Columns", (el + fi) * 0.5 + Vector((-0.3, -0.05, 0.1)), (-1, -0.2, 0.4), 0.22, 0.07, lambda u, v: 0.1 + 0.08 * (1 - u * u))
    fb, fp = go_plated(tuple(fi), (0.5, 0.48, 0.42), 8, 5.5); P.obj("Fist", fb, fp)
    for k in range(4):   # pumice knuckles
        P.obj("Knuckle", rock(tuple(fi + Vector((-0.27 + 0.18 * k, 0.32, 0.18))), 0.12, random.Random(40 + k), 9), "Trim", 0, False)
    hit = (fi - GO_MC).normalized()
    ax = hit.cross(Vector((0, 0, 1))).normalized(); ay = hit.cross(ax).normalized()
    for k in range(7):   # the meteor's crust cracked open round his fist, glowing
        a = 2 * math.pi * k / 7
        pts = [GO_MC + (hit * math.cos(w) + (ax * math.cos(a) + ay * math.sin(a)) * math.sin(w)).normalized() * GO_MR * 0.99 for w in (0.32, 0.5, 0.68)]
        P.obj("ImpactCrack", pipe(pts, [0.06, 0.045, 0.0], 5), "Glow")
    # the right arm: raised high to smash (it swings about the shoulder)
    sh, el, fi = Vector((1.12, 0.0, 1.5)), Vector((1.55, 0.15, 1.95)), Vector((1.3, 0.45, 2.38))
    hubR = tuple(sh)
    P.part("SwayArm", pipe([sh, el], [0.33, 0.3], 12), lambda c, n: "Belly" if n.z > 0.4 else "Base", hubR)
    fb, fp = go_plated(tuple((el + fi) * 0.5), (0.34, 0.32, 0.42), 7, 6.1); P.part("SwayArm", fb, fp, hubR)
    fb, fp = go_plated(tuple(fi), (0.5, 0.44, 0.48), 8, 7.3); P.part("SwayArm", fb, fp, hubR)
    for k in range(4):
        P.part("SwayArm", rock(tuple(fi + Vector((-0.27 + 0.18 * k, 0.3, 0.2))), 0.12, random.Random(50 + k), 9), "Trim", hubR, 0, False)
    # columns on the back of the raised forearm
    n0 = len(P.parts)
    go_columns(P, "Columns", (el + fi) * 0.5 + Vector((0.32, -0.05, 0.0)), (1, -0.2, 0.1), 0.22, 0.07, lambda u, v: 0.1 + 0.08 * (1 - u * u))
    for ob in P.parts[n0:]:   # they belong to the raised arm: move them over to the SwayArm mover
        P.parts.remove(ob); ob.name = "SwayArm"; ob.data.transform(Matrix.Translation(-Vector(hubR))); ob.location = hubR; P.spin.append(ob)
    # ---- the head: small, sunk between the shoulders, a heavy brow, burning eyes, a magma mouth, obsidian horns
    hc = Vector((0, 0.42, 1.78))
    hb, hpp = go_plated(tuple(hc), (0.36, 0.34, 0.33), 8, 8.8, 0.06); P.obj("Head", hb, hpp)
    P.obj("Brow", pipe([hc + Vector((-0.34, 0.2, 0.06)), hc + Vector((-0.12, 0.33, -0.02)), hc + Vector((0, 0.32, 0.0)),
                        hc + Vector((0.12, 0.33, -0.02)), hc + Vector((0.34, 0.2, 0.06))], [0.08, 0.1, 0.09, 0.1, 0.08], 8), "Base")
    for s in (1, -1):
        P.obj("Socket", ball(tuple(hc + Vector((s * 0.15, 0.28, -0.08))), (0.1, 0.06, 0.07), 10, 5), "Dark")
        P.obj("Eye", ball(tuple(hc + Vector((s * 0.15, 0.31, -0.09))), (0.06, 0.04, 0.035), 8, 4), "Lamp")
        horn = bez(hc + Vector((s * 0.28, 0.05, 0.18)), hc + Vector((s * 0.65, 0.0, 0.32)), hc + Vector((s * 0.85, 0.3, 0.62)), hc + Vector((s * 0.7, 0.62, 0.78)), 10)
        P.obj("Horn", pipe(horn, [0.14 * (1 - i / 10) ** 0.8 + 0.005 for i in range(11)], 10), "Glass")
        for k in range(3):   # growth ridges at the horn's root
            P.obj("HornRing", pipe([horn[k] - (horn[k + 1] - horn[k]) * 0.1, horn[k] + (horn[k + 1] - horn[k]) * 0.1], [0.15 * (1 - k / 10), 0.15 * (1 - k / 10)], 10), "Base")
    mc = hc + Vector((0, 0.3, -0.24))
    P.obj("Mouth", ball(tuple(mc), (0.2, 0.06, 0.08), 12, 6), "Glow")
    for k in range(6):   # jagged obsidian teeth, top and bottom
        x = -0.15 + 0.06 * k
        P.obj("Tooth", cone((x, mc.y + 0.03, mc.z + 0.07), (x + 0.01, mc.y + 0.05, mc.z - 0.02), 0.028, 4), "Glass")
        P.obj("Tooth", cone((x + 0.03, mc.y + 0.03, mc.z - 0.07), (x + 0.03, mc.y + 0.05, mc.z + 0.01), 0.024, 4), "Glass")
    P.obj("Jaw", rock(tuple(hc + Vector((0, 0.18, -0.36))), 0.24, random.Random(61), 12, (1.2, 0.9, 0.6)), lambda c, n: "Glow" if cracks(c * 1.6, n) else "Base", 0, False)
    P.part("Muzzle", ball(tuple(core + Vector((0, 0.12, 0))), (0.1, 0.05, 0.1), 8, 4), "Lamp", tuple(core + Vector((0, 0.12, 0))))
    return P



# ================================================================= ifrit (2026-10-13 remake)
IF_AXIS = Vector((0.0, -0.04, 0.0))   # the vortex's axis (vertical through here) and the hub of its turning layers
IF_TOP, IF_BOT = -0.05, -2.45          # the vortex from under the belt down to its point

def if_R(z):
    """the vortex's radius at height z: wide under the belt, narrowing to a point far below."""
    t = (IF_TOP - z) / (IF_TOP - IF_BOT)
    return 0.62 * (1 - t) ** 1.25 + 0.03

def if_grid(fn, nz, na, z0, z1, cap=True):
    """a closed surface of rings: fn(z, a) -> point, a measured round from +Y toward +X; capped top and bottom with a point."""
    bm = bmesh.new(); rings = []
    for i in range(nz + 1):
        z = z0 + (z1 - z0) * i / nz
        rings.append([bm.verts.new(fn(z, 2 * math.pi * k / na)) for k in range(na)])
    if cap:
        b = sum((v.co for v in rings[0]), Vector()) / na; t = sum((v.co for v in rings[-1]), Vector()) / na
        rings = [[bm.verts.new(b)]] + rings + [[bm.verts.new(t)]]
    return skin(bm, rings, na, cap=False)

def if_g(x, w):
    return math.exp(-(x / w) ** 2)

def if_torso_r(z, a):
    """the torso's section: an ellipse rx by ry at height z, swollen by the muscles under the skin."""
    rx = lerp(z, [(-0.12, 0.40), (0.05, 0.42), (0.4, 0.52), (0.72, 0.70), (0.9, 0.72), (1.0, 0.55), (1.08, 0.26)])
    ry = lerp(z, [(-0.12, 0.30), (0.05, 0.31), (0.4, 0.34), (0.72, 0.42), (0.9, 0.38), (1.0, 0.32), (1.08, 0.20)])
    af = math.atan2(math.sin(a), math.cos(a))        # -pi..pi, 0 at the front
    m = 0.0
    for s in (1, -1):                                 # the pectorals: two slabs of muscle, a crease under them
        m += 0.13 * if_g(af - s * 0.5, 0.42) * if_g(z - 0.76, 0.12)
        m -= 0.05 * if_g(af - s * 0.5, 0.5) * if_g(z - 0.6, 0.035)
        for zc in (0.14, 0.3, 0.46):                  # the six blocks of the abdomen
            m += 0.055 * if_g(af - s * 0.2, 0.13) * if_g(z - zc, 0.06)
        m += 0.06 * if_g(af - s * 1.35, 0.35) * if_g(z - 0.62, 0.18)   # the lats flaring under the arms
        m += 0.05 * if_g(af - s * 2.6, 0.3) * if_g(z - 0.78, 0.13)    # the shoulder blades
    m -= 0.03 * if_g(af, 0.07) * (1 if 0.05 < z < 0.92 else 0)          # the line down the middle
    m -= 0.03 * if_g(abs(af) - math.pi, 0.08) * (1 if 0.1 < z < 1.0 else 0)  # the spine's groove
    return rx * (1 + m), ry * (1 + m)

def lerp(u, keys):
    if u <= keys[0][0]: return keys[0][1]
    return lerp_keys(u, keys)

def if_torso_pt(z, a):
    rx, ry = if_torso_r(z, a)
    return Vector((math.sin(a) * rx, math.cos(a) * ry, z))

def if_torso_paint(c, n):
    """crimson above, charred black down to the belt."""
    af = math.atan2(c.x / 0.6, c.y / 0.4)
    if c.z < 0.1: return "Belly"
    if c.z < 0.22 and abs(af) > 1.2: return "Belly"
    return "Base"

def if_limb_paint(A, B, lines, dark_from=None):
    """paint for a limb from A to B: ember veins running along it at the given angles round it (with a slow wave), black from dark_from on."""
    A, B = Vector(A), Vector(B); ax = (B - A).normalized(); u, v = frame(ax)
    def paint(c, n):
        t = (c - A).dot(ax) / (B - A).length
        r = c - A - ax * (c - A).dot(ax)
        ang = math.atan2(r.dot(v), r.dot(u))
        for L in lines:
            d = math.atan2(math.sin(ang - L - 0.35 * math.sin(t * 7.0)), math.cos(ang - L - 0.35 * math.sin(t * 7.0)))
            if abs(d) < 0.11 and 0.05 < t < 0.95: return "Glow"
        if dark_from is not None and t > dark_from: return "Belly"
        return "Base"
    return paint

def if_tongue(root, d, L, r, curl=(0, 0, 0), n=7):
    """one tongue of flame: from root along d, bending by curl, tapering to a point."""
    root, d, curl = Vector(root), Vector(d).normalized(), Vector(curl)
    tip = root + d * L + curl
    pts = bez(root, root + d * L * 0.35, root + d * L * 0.75 + curl * 0.5, tip, n)
    radii = [r * (1 - (i / n) ** 1.3) * (0.85 + 0.3 * math.sin(math.pi * i / n)) for i in range(n)] + [0.0]
    return pipe(pts, radii, 7)

def if_flame_paint(root, L, hot="Lamp", mid="Glow", cool="Base", k0=0.25, k1=0.8):
    root = Vector(root)
    def paint(c, n):
        f = (c - root).length / L
        return hot if f < k0 else (mid if f < k1 else cool)
    return paint

def if_prism(poly, nrm, h):
    """a flat polygon raised h along nrm (an inlay or a stud on a surface)."""
    nrm = Vector(nrm).normalized()
    bm = bmesh.new()
    lo = [bm.verts.new(Vector(p)) for p in poly]; hi = [bm.verts.new(Vector(p) + nrm * h) for p in poly]
    bm.faces.new(hi); bm.faces.new(list(reversed(lo)))
    for i in range(len(poly)):
        j = (i + 1) % len(poly); bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm

def if_star(c, nrm, up, r, h=0.012, points=8):
    """an eight-pointed star (the khatam of Arabic geometric work) lying on a surface."""
    nrm = Vector(nrm).normalized(); up = (Vector(up) - nrm * Vector(up).dot(nrm)).normalized(); side = nrm.cross(up)
    poly = []
    for i in range(points * 2):
        a = math.pi * i / points; rr = r if i % 2 == 0 else r * 0.62
        poly.append(Vector(c) + (up * math.cos(a) + side * math.sin(a)) * rr)
    return if_prism(poly, nrm, h)

def if_fireball(P, name, c, R, hub):
    """a ball of fire as fire really burns: a round body of flame whose top splits into five tongues rising and twisting to points, the
    white-hot heart showing in the grooves between them, red at the tips."""
    c = Vector(c); H = R * 1.9
    def fn(z, a):
        if z < 0: r = R * max(0.0, 1 - (z / (R * 0.85)) ** 2) ** 0.5
        else: r = R * (1 - z / H) ** 1.15
        u = max(0.0, z) / H
        r *= 1 + (0.12 + 0.55 * u) * math.sin(5 * a + u * 4.5)
        tw = u * 0.5
        return c + Vector((math.sin(a + tw) * r, math.cos(a + tw) * r, z))
    def paint(p, n):
        z = p.z - c.z; u = max(0.0, z) / H
        q = p - c; a = math.atan2(q.x, q.y) - u * 0.5
        if z > H * 0.62: return "Base"
        if math.sin(5 * a + u * 4.5) < -0.45 and z < H * 0.5: return "Lamp"
        return "Glow"
    P.part(name, if_grid(fn, 18, 40, -R * 0.85, H * 0.98), paint, hub)
    for j in range(5):   # five tongues rising off the top, curling
        a = 2 * math.pi * j / 5 + 0.3
        root = c + Vector((math.sin(a) * R * 0.45, math.cos(a) * R * 0.45, R * 0.9))
        d = Vector((math.sin(a) * 0.35, math.cos(a) * 0.35, 1.0))
        L = R * (0.9 + 0.25 * (j % 2))
        P.part(name, if_tongue(root, d, L, R * 0.16, Vector((math.cos(a), -math.sin(a), 0)) * R * 0.18, 6),
               if_flame_paint(root, L, "Glow", "Glow", "Base", 0.0, 0.55), hub)

def if_surface_line(pt, ab, n, lift=0.007):
    """points along a line drawn on a surface: pt(s) -> (point, outward normal) for s from ab[0] to ab[1]."""
    out = []
    for i in range(n + 1):
        s = ab[0] + (ab[1] - ab[0]) * i / n
        q, nr = pt(s); out.append(q + nr * lift)
    return out

def if_torso_normal(z, a):
    e = 0.004
    p = if_torso_pt(z, a); dz = if_torso_pt(z + e, a) - p; da = if_torso_pt(z, a + e) - p
    nr = da.cross(dz).normalized()
    return p, (nr if nr.dot(Vector((p.x, p.y, 0))) > 0 else -nr)

def if_vein(pts, r=0.013):
    """an ember vein: a thin glowing cord lying on the skin, thinning at its ends."""
    n = len(pts)
    return pipe(pts, [r * (0.45 + 0.55 * math.sin(math.pi * (0.1 + 0.8 * i / (n - 1)))) for i in range(n)], 6)

def if_vortex_ribbon(phase, turns, r_k, n=44, wk=1.0):
    """a band of flame winding down round the vortex: a helix at r_k times the vortex radius, its broad face turned outward."""
    path, widths, thick, rolls = [], [], [], []
    for i in range(n + 1):
        t = i / n
        z = IF_TOP - 0.02 - t * (IF_TOP - IF_BOT - 0.12)
        a = phase + 2 * math.pi * turns * t
        R = if_R(z) * r_k
        path.append(IF_AXIS + Vector((math.sin(a) * R, math.cos(a) * R, z)))
        w = (0.3 * if_R(z) / if_R(IF_TOP) + 0.035) * wk * min(1.0, 0.25 + t / 0.16) * (1 - 0.15 * math.sin(math.pi * t * 3) ** 2)
        widths.append(w); thick.append(0.035 * (1 - t) + 0.012); rolls.append(math.pi / 2 + 0.25)
    return path, ribbon(path, widths, thick, rolls, 10)


def L_ifrit():
    """The FIRE IFRIT (2026-10-14, remade: "same as the alien bosses - realistic details, scarier, keep the cartoon shape"): the same horned
    red djinn of fire with a fireball in each hand, now built like the ifrit of the old Arabian tales - a giant of smokeless fire. A massive
    torso: the broad chest of two heavy pectorals with a crease under them, the six blocks of the abdomen, the lats flaring under the arms,
    the shoulder blades and the groove of the spine behind; great round deltoids, biceps swelling on the upper arms, thick forearms. His
    skin is crimson, charred to black down at the waist and on the forearms and hands as if burnt from inside, and his blood is fire: ember
    veins glow in every crease between the muscles - down the middle of the abdomen and across it, under the pectorals, along the serratus
    on each flank, down the spine - and wind in two lines along each arm. The head: a heavy skull under a beetling brow drawn down in a V,
    almond eyes burning white-gold in black sockets, a hooked nose, high cheekbones, pointed ears with two gold hoops in each; the mouth
    torn open in a roar, black inside with a furnace glow deep in the throat (his shots leave from it), two long fangs above and two below.
    His beard is fire - tongues of flame hanging from the jaw and the chin, white-hot at the roots, orange, red at the tips - and his hair
    is fire too, a mane of flame streaming back from the scalp in the wind of his flight. From his temples sweep two great ibex horns, back
    and up in a long arc and out at the tips, the front of each ridged with knots evenly all along it, as on a wild ibex, the tips capped
    in gold. Gold cuffs on his forearms engraved with the geometry of Arabic work - bands with a row of eight-pointed stars between them, a
    turquoise set in each - a gold torc round his neck, and on his waist a belt of gold plates set with turquoise and rubies round a great
    buckle. In each black hand, its fingers curled round it, a real ball of fire: a white-hot core, an orange body and tongues of flame
    licking out all round it and rising, red at their tips. Arms swing (SwayR, SwayL).
    He flies the way the djinn of legend do, ON A VORTEX OF FIRE: below the belt his body becomes a towering tornado of flame and smoke,
    wide under the belt and narrowing to a point far below - a white-hot core of fire twisting down its axis, four bands of flame
    (two broad orange ones on the outside with tongues of flame licking up off them evenly along their length, two narrower dark red ones
    set deeper between them), each band rising thin from under a skirt of flame at his belt and widening as it winds down, and sparks and
    embers set evenly along the spirals. The vortex turns (SpinA: the core and the bands of flame; SpinB: the embers)."""
    P = Boss("ifrit", {"Base": ((0.62, 0.07, 0.04), 0.45), "Belly": ((0.07, 0.025, 0.02), 0.35), "Accent": ((0.98, 0.70, 0.18), 0.8),
                       "Trim": ((0.22, 0.15, 0.11), 0.4), "Glass": ((0.08, 0.70, 0.62), 0.9), "Dark": ((0.035, 0.02, 0.02), 0.3),
                       "Glow": ((1.0, 0.42, 0.04), 0.5), "Metal": ((0.75, 0.04, 0.06), 0.85), "Lamp": ((1.0, 0.90, 0.55), 0.8)})
    # ---- the torso: one sculpted surface, the muscles swelling it, the veins glowing in the creases
    P.obj("Torso", if_grid(if_torso_pt, 48, 64, -0.14, 1.08), if_torso_paint, 0)
    V = lambda f, ab, n: P.obj("Vein", if_vein(if_surface_line(f, ab, n)), "Glow")
    V(lambda z: if_torso_normal(z, 0.0), (0.08, 0.6), 14)                                     # down the middle of the abdomen
    for zc in (0.22, 0.38):                                                                   # across it
        V(lambda a, zc=zc: if_torso_normal(zc, a), (-0.42, 0.42), 12)
    for s in (1, -1):
        V(lambda a, s=s: if_torso_normal(0.6 + 0.04 * math.cos(a * 3), s * a), (0.1, 0.95), 14)       # under the pectorals
        V(lambda z, s=s: if_torso_normal(z, s * (0.95 + 0.25 * (0.62 - z) + 0.04 * math.sin(z * 18))), (0.62, 0.95), 8)  # up to the shoulder
        V(lambda z, s=s: if_torso_normal(z, s * (1.05 + 0.25 * (z - 0.4))), (0.12, 0.6), 12)  # along the serratus
        V(lambda z, s=s: if_torso_normal(z, s * (0.22 + 0.05 * math.sin(z * 12))), (0.62, 0.86), 6)   # across the pectoral
    V(lambda z: if_torso_normal(z, math.pi), (0.1, 1.0), 18)                                   # down the spine
    P.obj("Neck", pipe([(0, -0.03, 0.98), (0, 0.0, 1.12), (0, 0.03, 1.22)], [0.22, 0.2, 0.19], 18), "Base")
    for s in (1, -1):   # the trapezius rising from the shoulders into the neck
        P.obj("Trap", oriented_ball((s * 0.3, -0.06, 1.0), (0.26, 0.16, 0.13), Vector((s * 0.9, 0, -0.42)).normalized(), Vector((0, 1, 0)),
                                    Vector((s * 0.42, 0, 0.9)).normalized(), 14, 7), "Base")
        P.obj("Deltoid", oriented_ball((s * 0.7, 0.0, 0.86), (0.25, 0.23, 0.24), Vector((s, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1)), 16, 8),
              lambda c, n, s=s: "Glow" if abs(c.y) < 0.012 and c.z > 0.8 else "Base")
    P.obj("Torc", xf(torus(0.215, 0.03, 0.0, 28, 6), Matrix.Scale(1.0, 3), (0, 0.0, 1.06)), "Accent")
    # ---- the belt: gold plates with turquoise and rubies, a great buckle
    belt = torus(1.0, 0.075, 0.0, 48, 8)
    for v in belt.verts: v.co = Vector((v.co.x * 0.44, v.co.y * 0.33, v.co.z + 0.0))
    P.obj("Belt", belt, lambda c, n: "Dark" if abs(math.sin(math.atan2(c.x / 0.44, c.y / 0.33) * 8)) < 0.08 else "Accent")
    for k in range(16):
        a = 2 * math.pi * (k + 0.5) / 16
        if abs(math.atan2(math.sin(a), math.cos(a))) < 0.3: continue
        p = Vector((math.sin(a) * 0.525, math.cos(a) * 0.405, 0.0))
        P.obj("BeltGem", ball(tuple(p), (0.032, 0.032, 0.032), 8, 4), "Glass" if k % 2 else "Metal")
    P.obj("Buckle", lathe([(0.0, -0.025), (0.11, -0.025), (0.13, 0.0), (0.11, 0.03), (0.0, 0.035)], 8, "z"), "Accent")
    P.parts[-1].data.transform(Matrix.Translation((0, 0.41, 0.0)) @ Matrix.Rotation(math.radians(-90), 4, "X") @ Matrix.Rotation(math.radians(22.5), 4, "Z"))
    P.obj("BuckleStone", ball((0, 0.455, 0.0), (0.06, 0.035, 0.06), 10, 5), "Metal")
    # ---- the head
    hc = Vector((0, 0.06, 1.4))
    P.obj("Skull", ball(tuple(hc + Vector((0, -0.03, 0.02))), (0.23, 0.25, 0.27), 20, 10), "Base")
    P.obj("Cheeks", ball(tuple(hc + Vector((0, 0.1, -0.06))), (0.21, 0.17, 0.13), 16, 8), "Base")
    P.obj("Jaw", ball(tuple(hc + Vector((0, 0.11, -0.2))), (0.17, 0.14, 0.09), 14, 7), "Base")
    P.obj("Nose", hull([tuple(hc + Vector(p)) for p in ((0, 0.24, 0.07), (0.035, 0.22, 0.04), (-0.035, 0.22, 0.04), (0, 0.3, -0.04),
                                                          (0.05, 0.25, -0.07), (-0.05, 0.25, -0.07), (0, 0.27, -0.09))]), "Base", 0, False)
    for s in (1, -1):
        so = hc + Vector((s * 0.095, 0.205, 0.05))
        P.obj("Socket", oriented_ball(so, (0.075, 0.03, 0.04), Vector((math.cos(math.radians(s * 14)), 0, math.sin(math.radians(s * 14)))),
                                      Vector((0, 1, 0)), Vector((-math.sin(math.radians(s * 14)), 0, math.cos(math.radians(s * 14)))), 12, 5), "Dark")
        P.obj("Eye", oriented_ball(so + Vector((0, 0.014, 0)), (0.055, 0.022, 0.022), Vector((math.cos(math.radians(s * 14)), 0, math.sin(math.radians(s * 14)))),
                                   Vector((0, 1, 0)), Vector((-math.sin(math.radians(s * 14)), 0, math.cos(math.radians(s * 14)))), 12, 5), "Lamp")
        # the brow: a heavy ridge drawn down to the nose in a V
        P.obj("Brow", pipe([hc + Vector((s * 0.02, 0.235, 0.075)), hc + Vector((s * 0.1, 0.225, 0.11)), hc + Vector((s * 0.19, 0.17, 0.14))],
                           [0.03, 0.035, 0.022], 8), "Belly")
        ear = hc + Vector((s * 0.22, 0.0, 0.02))
        P.obj("Ear", hull([tuple(ear + Vector(p)) for p in ((0, 0.04, 0.05), (0, -0.04, 0.05), (0, 0.03, -0.06), (s * 0.03, 0.0, 0.0),
                                                             (s * 0.17, -0.1, 0.12))]), "Base", 0, False)
        for j, (dz, rr) in enumerate(((-0.06, 0.035), (-0.02, 0.028))):
            P.obj("Earring", xf(torus(rr, 0.008, 0.0, 14, 4), Matrix.Rotation(math.radians(90), 3, "Y"), tuple(ear + Vector((s * 0.03, -0.01 - 0.03 * j, dz - rr)))), "Accent")
        # the horns: an ibex's, sweeping back and up in a long arc, knotted along the front, gold at the tips
        root = hc + Vector((s * 0.14, 0.08, 0.2))
        hp = bez(root, root + Vector((s * 0.12, -0.05, 0.35)), root + Vector((s * 0.32, -0.42, 0.6)), root + Vector((s * 0.55, -0.62, 0.5)), 24)
        radii = []
        for i in range(len(hp)):
            t = i / (len(hp) - 1)
            radii.append((0.085 * (1 - t) ** 0.8 + 0.006) * (1.18 if (i % 3 == 1 and t < 0.85) else 1.0))
        radii[-1] = 0.0
        radii = [r / 1.18 if i % 3 == 1 else r for i, r in enumerate(radii)]
        P.obj("Horn", pipe(hp, radii, 10), lambda c, n, hp=hp: "Accent" if (c - hp[-1]).length < 0.13 else "Trim")
        for i in range(2, len(hp) - 4, 2):   # the knots of an ibex horn, one after another along its front
            tn = (hp[i + 1] - hp[i - 1]).normalized(); a0, b0 = frame(tn); r = radii[i]
            P.obj("HornKnot", xf(torus(r * 0.98, r * 0.17, 0.0, 14, 5), Matrix((a0, b0, tn)).transposed(), tuple(hp[i])), "Trim")
        # the mouth: torn open, a furnace in the throat, fangs above and below
    P.obj("BrowJewel", oriented_ball(hc + Vector((0, 0.2, 0.2)), (0.04, 0.02, 0.055), Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1)), 10, 5), "Metal")
    P.obj("BrowSetting", xf(torus(0.048, 0.01, 0.0, 16, 4), Matrix(((1, 0, 0), (0, 0, 1.0), (0, 1.15, 0))), tuple(hc + Vector((0, 0.195, 0.2)))), "Accent")
    P.obj("Mouth", ball(tuple(hc + Vector((0, 0.235, -0.16))), (0.13, 0.05, 0.07), 16, 6), "Dark")
    P.obj("Throat", ball(tuple(hc + Vector((0, 0.25, -0.16))), (0.055, 0.03, 0.035), 10, 4), "Glow")
    P.obj("Lip", xf(torus(1.0, 0.016, 0.0, 24, 5), Matrix(((0.135, 0, 0), (0, 0, 0.03), (0, 0.075, 0))), tuple(hc + Vector((0, 0.262, -0.16)))), "Belly")
    for s in (1, -1):
        P.obj("Fang", cone(hc + Vector((s * 0.075, 0.272, -0.095)), hc + Vector((s * 0.068, 0.295, -0.21)), 0.022, 6), "Lamp", 0, False)
        P.obj("Fang", cone(hc + Vector((s * 0.06, 0.272, -0.225)), hc + Vector((s * 0.056, 0.29, -0.15)), 0.017, 6), "Lamp", 0, False)
        for j in range(2):   # the smaller teeth between the fangs
            x = s * (0.018 + 0.022 * j)
            P.obj("Tooth", cone(hc + Vector((x, 0.268, -0.098)), hc + Vector((x, 0.282, -0.135)), 0.011, 5), "Lamp", 0, False)
    P.part("Muzzle", ball(tuple(hc + Vector((0, 0.27, -0.16))), (0.035, 0.02, 0.025), 8, 4), "Glow", tuple(hc + Vector((0, 0.27, -0.16))))
    # ---- the beard of fire: tongues hanging from the jaw and the chin, curling forward at the tips
    for k in range(9):
        u = (k - 4) / 4.0
        root = hc + Vector((u * 0.15, 0.17 + 0.07 * (1 - abs(u)), -0.24 + 0.05 * abs(u)))
        L = 0.42 - 0.17 * abs(u)
        d = Vector((u * 0.25, 0.25, -1.0))
        P.obj("Beard", if_tongue(root, d, L, 0.045 - 0.01 * abs(u), Vector((u * 0.05, 0.1, 0.06)), 7), if_flame_paint(root, L, "Lamp", "Glow", "Base", 0.1, 0.78), 0, False)
    # ---- the mane of fire: tongues streaming back from the scalp in the wind
    for k in range(11):
        u = (k - 5) / 5.0
        root = hc + Vector((u * 0.17, -0.02 - 0.1 * (1 - u * u) ** 0.5, 0.24 - 0.09 * abs(u)))
        L = 0.75 - 0.25 * abs(u)
        d = Vector((u * 0.55, -1.0, 0.12))
        P.obj("Mane", if_tongue(root, d, L, 0.09 - 0.02 * abs(u), Vector((u * 0.06, -0.08, 0.12 + 0.05 * math.sin(k * 1.7))), 8),
              if_flame_paint(root, L, "Lamp", "Glow", "Base", 0.12, 0.9), 0, False)
    # ---- the arms (each swings from the shoulder): biceps, forearms, gold cuffs, black hands curled round the fireballs
    for s, name in ((1, "SwayR"), (-1, "SwayL")):
        sh = Vector((s * 0.74, 0.0, 0.86)); el = Vector((s * 1.2, 0.14, 0.58)); wr = Vector((s * 1.42, 0.44, 0.74))
        hub = tuple(sh)
        up = [sh + (el - sh) * t for t in (0.0, 0.25, 0.5, 0.78, 1.0)]
        rup = [0.2, 0.215, 0.225, 0.19, 0.155]
        P.part(name, pipe(up, rup, 16), "Base", hub)
        fo = [el + (wr - el) * t for t in (0.0, 0.18, 0.45, 0.8, 1.0)]
        rfo = [0.155, 0.175, 0.165, 0.13, 0.115]
        P.part(name, pipe(fo, rfo, 16), if_limb_paint(el, wr, [], 0.42), hub)
        for A, B, rr, lines, t1 in ((sh, el, rup, (0.5, 2.6), 0.95), (el, wr, rfo, (1.1, 3.4), 0.42)):
            ax0 = (B - A).normalized(); u0, v0 = frame(ax0)
            for L in lines:
                def lp(tt, A=A, B=B, rr=rr, L=L, u0=u0, v0=v0):
                    k = min(3.999, tt * 4); i0 = int(k); r = rr[i0] + (rr[i0 + 1] - rr[i0]) * (k - i0)
                    th = L + 0.35 * math.sin(tt * 7.0)
                    nr = u0 * math.cos(th) + v0 * math.sin(th)
                    return A + (B - A) * tt + nr * r, nr
                P.part(name, if_vein(if_surface_line(lp, (0.06, t1), 12), 0.012), "Glow", hub)
        P.part(name, ball(tuple(el), (0.16, 0.16, 0.16), 12, 6), "Base", hub)
        # the cuff: a gold band engraved at both edges, a row of eight-pointed stars with a turquoise in each
        ax = (wr - el).normalized(); u, v = frame(ax)
        c0, c1 = el + (wr - el) * 0.42, el + (wr - el) * 0.86
        P.part(name, pipe([c0, c0 + ax * 0.02, c1 - ax * 0.02, c1], [0.17, 0.185, 0.16, 0.145], 18),
               lambda c, n, c0=c0, ax=ax, L=(c1 - c0).length: "Dark" if abs((c - c0).dot(ax) / L - 0.12) < 0.03 or abs((c - c0).dot(ax) / L - 0.88) < 0.03 else "Accent", hub)
        mid = (c0 + c1) * 0.5; rm = 0.177
        for j in range(8):
            a = 2 * math.pi * j / 8
            nrm = u * math.cos(a) + v * math.sin(a)
            P.part(name, if_star(mid + nrm * rm, nrm, ax, 0.045, 0.01), "Accent", hub)
            P.part(name, ball(tuple(mid + nrm * (rm + 0.012)), (0.016, 0.016, 0.016), 6, 3), "Glass", hub)
        # the hand: a black palm turned up, four fingers and a thumb curled round the fireball
        palm = wr + ax * 0.09 + Vector((0, 0, 0.03))
        P.part(name, oriented_ball(palm, (0.1, 0.12, 0.06), u, ax, ax.cross(u), 12, 6), "Belly", hub)
        fb = palm + Vector((0, 0.05, 0.27))
        for j in range(4):
            f = (j - 1.5) / 1.5
            base = palm + ax * 0.08 + u * f * 0.06
            P.part(name, pipe(bez(base, base + ax * 0.08, base + ax * 0.12 + Vector((0, 0, 0.08)), base + ax * 0.06 + Vector((0, 0, 0.15)), 5),
                              [0.032, 0.03, 0.028, 0.025, 0.02, 0.0], 6), lambda c, n, b=base: "Glow" if abs((c - b).length - 0.1) < 0.012 else "Belly", hub)
        tb = palm - u * s * 0.08
        P.part(name, pipe(bez(tb, tb - u * s * 0.06, tb - u * s * 0.06 + Vector((0, 0.05, 0.1)), tb + Vector((0, 0.06, 0.16)), 4),
                          [0.035, 0.032, 0.026, 0.02, 0.0], 6), "Belly", hub)
        if_fireball(P, name, fb, 0.22, hub)
    # ---- the vortex of fire: a white-hot core twisting down its axis, four bands of flame winding round it (SpinA)
    hubv = tuple(IF_AXIS + Vector((0, 0, IF_TOP)))
    core = []
    for i in range(31):
        t = i / 30; z = IF_TOP - t * (IF_TOP - IF_BOT)
        core.append(IF_AXIS + Vector((0, 0, z)))
    P.part("SpinA", pipe(core, [if_R(p.z) * 0.42 * (1 + 0.15 * math.sin(i * 1.3)) for i, p in enumerate(core[:-1])] + [0.0], 16),
           lambda c, n: "Lamp" if c.z > IF_TOP - 1.4 else "Glow", hubv)
    for j in range(4):
        path, bm = if_vortex_ribbon(j * math.pi / 2, 1.6, 0.9 if j % 2 == 0 else 0.72, 44, 1.0 if j % 2 == 0 else 0.65)
        P.part("SpinA", bm, "Glow" if j % 2 == 0 else "Metal", hubv)
        # tongues of flame licking up off the band, evenly along it
        if j % 2: continue
        for i in range(2, len(path) - 5, 3):
            p = path[i]; r = p - IF_AXIS; r.z = 0
            out = r.normalized() if r.length > 1e-4 else Vector((1, 0, 0))
            L = 0.12 + 0.35 * if_R(p.z)
            P.part("SpinA", if_tongue(p + out * 0.02, out * 0.6 + Vector((0, 0, 1.0)), L, 0.05 * if_R(p.z) / 0.65 + 0.015, out * 0.05, 4),
                   "Glow" if j % 2 == 0 else "Metal", hubv)
    # the embers riding the spirals (SpinB)
    for j in range(4):
        for i in range(14):
            t = (i + 0.5) / 14
            z = IF_TOP - 0.1 - t * (IF_TOP - IF_BOT - 0.4)
            a = j * math.pi / 2 + math.pi / 4 + 2 * math.pi * 1.6 * t
            R = if_R(z) * 1.12 + 0.05
            p = IF_AXIS + Vector((math.sin(a) * R, math.cos(a) * R, z))
            e = 0.035 * (1 - 0.5 * t)
            P.part("SpinB", hull([tuple(p + Vector(q) * e) for q in ((0, 0, 1.8), (0, 0, -1.2), (1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0))]), "Lamp", hubv, 0, False)
    # where the flesh turns to fire: a skirt of flame tongues hanging from under the belt into the vortex (still)
    for k in range(14):
        a = 2 * math.pi * k / 14
        root = Vector((math.sin(a) * 0.4, math.cos(a) * 0.3, -0.06))
        out = Vector((math.sin(a), math.cos(a) * 0.8, 0)).normalized()
        P.obj("Skirt", if_tongue(root, out * 0.45 + Vector((0, 0, -1.0)), 0.34, 0.075, out * 0.06 + Vector((0, 0, 0.04)), 6),
              if_flame_paint(root, 0.34, "Glow", "Glow", "Metal", 0.0, 0.55), 0, False)
    return P



# ================================================================= demon (2026-10-13 remake)
def dm_hash(i, j, k, s):
    v = math.sin(i * 127.1 + j * 311.7 + k * 74.7 + s * 19.3) * 43758.5453
    return v - math.floor(v)

def dm_crack(c, cell=0.22, w=0.2):
    """glowing cracks in hide or coat, like cooling lava: the edges of an irregular cell pattern (true where the face lies on a crack)."""
    p = Vector(c) / cell; i0, j0, k0 = math.floor(p.x), math.floor(p.y), math.floor(p.z)
    d1 = d2 = 9.0
    for i in range(i0 - 1, i0 + 2):
        for j in range(j0 - 1, j0 + 2):
            for k in range(k0 - 1, k0 + 2):
                q = Vector((i + dm_hash(i, j, k, 1), j + dm_hash(i, j, k, 2), k + dm_hash(i, j, k, 3)))
                d = (q - p).length
                if d < d1: d1, d2 = d, d1
                elif d < d2: d2 = d
    return d2 - d1 < w

def dm_ring(c, rx, ry, r, rot=None, n=28, seg=6):
    """an elliptic ring rx by ry about c in its own x-y plane, turned by rot; the tube keeps its radius."""
    rot = rot or Matrix.Identity(3); c = Vector(c)
    pts = [c + rot @ Vector((math.cos(2 * math.pi * k / n) * rx, math.sin(2 * math.pi * k / n) * ry, 0)) for k in range(n + 1)]
    pts.append(pts[1])
    return pipe(pts, [r] * len(pts), seg, cap=False)

def dm_link(c, t, k, r=0.045, rr=0.013):
    """one chain link at c, long along t, every other one turned a quarter about it."""
    t = Vector(t).normalized(); a, b = frame(t)
    if k % 2: a, b = b, -a
    bm = torus(r, rr, 0.0, 6, 3)
    for v in bm.verts: v.co.x *= 1.5
    return xf(bm, Matrix((t, a, b)).transposed(), tuple(c))

def dm_chain(P, a, b, sag=0.0, step=0.18, name="Chain", slot="Trim"):
    """an iron chain from a to b, hanging `sag` in the middle, links evenly every `step`."""
    a, b = Vector(a), Vector(b); L = (b - a).length; n = max(2, int(L / step))
    pts = [a + (b - a) * (i / n) - Vector((0, 0, sag * 4 * (i / n) * (1 - i / n))) for i in range(n + 1)]
    for i in range(n):
        P.obj(name, dm_link((pts[i] + pts[i + 1]) * 0.5, pts[i + 1] - pts[i], i, r=min(0.045, L / n * 0.55)), slot, 0)

def dm_flame(base, d, L, r, curl=None, n=5):
    """one tongue of flame from base along d, tapering to a point and licking sideways at the tip."""
    base, d = Vector(base), Vector(d).normalized()
    curl = Vector(curl) if curl is not None else Vector((0, 0, 0))
    pts = bez(base, base + d * L * 0.35, base + d * L * 0.7 + curl * L * 0.15, base + d * L + curl * L * 0.35, n)
    return pipe(pts, [r * (1 - (i / n) ** 1.3) if i < n else 0.0 for i in range(n + 1)], 6)

def dm_grow(P, n0, s0, O, K):
    """everything added since P had n0 body pieces and s0 movers scaled by K about O (the movers keep their hinges)."""
    O = Vector(O)
    for ob in P.parts[n0:]:
        for v in ob.data.vertices: v.co = O + (v.co - O) * K
    for ob in P.spin[s0:]:
        for v in ob.data.vertices: v.co = v.co * K
        ob.location = O + (Vector(ob.location) - O) * K


# ---------------------------------------------------------------- a nightmare
def dm_horse(P, O, tag, K=1.15):
    """one nightmare of the pair, built like a real horse at a flying gallop; O is the middle of its barrel. Returns the two collar
    points the traces hang from and the bit rings."""
    O = Vector(O); n0, s0 = len(P.parts), len(P.spin)
    def W(p): return O + Vector(p)
    coat = lambda c, n: "Glow" if dm_crack(c - O, 0.26, 0.06) else "Belly"
    # ---- the body: an arched neck rising from deep shoulders, a deep chest, a short strong back, round quarters
    neck = bez((0, 0.9, 0.8), (0, 0.8, 0.66), (0, 0.62, 0.4), (0, 0.42, 0.2), 8)
    torso = bez((0, 0.42, 0.2), (0, 0.14, 0.18), (0, -0.25, 0.19), (0, -0.52, 0.17), 9)[1:]
    PTS = [W(p) for p in neck + torso] + [W((0, -0.62, 0.13))]
    FR = spine_frames(PTS); RX, RZ = [], []
    for i in range(len(neck)):
        u = i / (len(neck) - 1)
        RX.append(lerp_keys(u, [(0, 0.06), (0.15, 0.065), (0.6, 0.095), (1, 0.15)])); RZ.append(lerp_keys(u, [(0, 0.075), (0.15, 0.1), (0.6, 0.14), (1, 0.25)]))
    for i in range(len(torso)):
        u = (i + 1) / len(torso)
        RX.append(lerp_keys(u, [(0, 0.17), (0.25, 0.2), (0.55, 0.19), (0.85, 0.2), (1, 0.13)]))
        RZ.append(lerp_keys(u, [(0, 0.26), (0.25, 0.25), (0.55, 0.21), (0.85, 0.23), (1, 0.14)]))
    RX.append(0.0); RZ.append(0.0)
    P.obj("Horse", body_loft(PTS, RX, RZ, FR, 14, 1.15, 0.92), coat, 1)
    # the shoulder and the haunch stand out as muscle under the coat
    for s in (1, -1):
        P.obj("Muscle", oriented_ball(W((s * 0.12, 0.3, 0.1)), (0.1, 0.17, 0.2), Vector((1, 0, 0)), Vector((0, 0.9, 0.45)).normalized(), Vector((0, -0.45, 0.9)).normalized(), 12, 6), "Belly")
        P.obj("Muscle", oriented_ball(W((s * 0.12, -0.42, 0.13)), (0.11, 0.2, 0.2), Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1)), 12, 6), "Belly")

    # ---- the head: long, the bony face of a horse, tipped down at the poll; the mouth torn open, the eyes burning
    HB = W((0, 0.9, 0.8)); HR = Matrix.Rotation(math.radians(-50), 3, "X") @ Matrix.Scale(1.3, 3)
    def H(bm): return xf(bm, HR, tuple(HB))
    def hp(p): return HB + HR @ Vector(p)
    HI = HR.inverted()
    UP = [(-0.06, 0.07, 0.08, 0, 0.0), (0.02, 0.085, 0.095, 0, 0.0), (0.1, 0.08, 0.085, 0, -0.005), (0.2, 0.065, 0.07, 0, -0.02),
          (0.3, 0.058, 0.06, 0, -0.025), (0.38, 0.058, 0.058, 0, -0.025), (0.44, 0.045, 0.045, 0, -0.025)]
    P.obj("HorseHead", H(loft(UP, 18, sq=1.25)), "Belly", 0)
    jaw = loft([(0.08, 0.06, 0.04, 0, 0.0), (0.2, 0.05, 0.035, 0, 0.0), (0.33, 0.045, 0.03, 0, 0.0), (0.4, 0.035, 0.022, 0, 0.0)], 14, sq=1.2)
    xf(jaw, Matrix.Rotation(math.radians(-28), 3, "X"), (0, 0.04, -0.07))
    jaw.verts.ensure_lookup_table()
    P.obj("HorseJaw", H(jaw), "Belly", 0)
    P.obj("HorseMaw", H(oriented_ball((0, 0.3, -0.1), (0.04, 0.12, 0.03), Vector((1, 0, 0)), Vector((0, 0.94, -0.33)), Vector((0, 0.33, 0.94)), 10, 5)), "Glow")
    for k in range(4):   # teeth: incisors along the front of each jaw
        x = -0.03 + 0.02 * k
        P.obj("HTooth", H(cone((x, 0.43, -0.055), (x, 0.43, -0.085), 0.009, 4)), "Glass", 0, False)
        P.obj("HTooth", H(cone((x, 0.375, -0.2), (x, 0.39, -0.17), 0.009, 4)), "Glass", 0, False)
    bits = []
    for s in (1, -1):
        P.obj("Nostril", H(oriented_ball((s * 0.03, 0.445, -0.01), (0.014, 0.02, 0.022), Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1)), 8, 4)), "Glow")
        P.obj("HSocket", H(oriented_ball((s * 0.072, 0.07, 0.035), (0.022, 0.035, 0.026), Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1)), 10, 5)), "Dark")
        P.obj("HEye", H(oriented_ball((s * 0.083, 0.075, 0.035), (0.012, 0.026, 0.012), Vector((1, 0, 0)), Vector((0, 0.95, -s * 0.0 + 0.3)).normalized(), Vector((0, -0.3, 0.95)), 8, 4)), "Lamp")
        P.obj("HBrow", H(oriented_ball((s * 0.07, 0.07, 0.065), (0.03, 0.05, 0.013), Vector((1, 0, 0)), Vector((0, 0.94, -0.34)), Vector((0, 0.34, 0.94)), 10, 5)), "Belly")
        ear = cone((s * 0.05, -0.04, 0.07), (s * 0.08, -0.17, 0.12), 0.028, 6)   # ears pinned flat back
        P.obj("HEar", H(ear), "Belly", 0, False)
        # the bridle of black iron: cheek pieces, a ring bit at the corner of the mouth
        P.obj("Bridle", H(pipe([(s * 0.06, 0.33, -0.05), (s * 0.08, 0.15, -0.01), (s * 0.08, 0.0, 0.05), (s * 0.03, -0.05, 0.1)], [0.011] * 4, 5)), "Trim")
        P.obj("BitRing", H(xf(torus(0.022, 0.007, 0.0, 12, 4), Matrix.Rotation(math.radians(90), 3, "Y"), (s * 0.062, 0.34, -0.06))), "Accent")
        bits.append(hp((s * 0.062, 0.34, -0.06)))
    # the chanfron: a plate of black iron down the face with a spike rising from the brow and a skull boss between the eyes
    ch = hull([(x, y, z) for (x, y, z) in [(-0.06, -0.02, 0.1), (0.06, -0.02, 0.1), (-0.075, 0.12, 0.085), (0.075, 0.12, 0.085), (-0.055, 0.3, 0.06), (0.055, 0.3, 0.06),
                                            (-0.04, 0.38, 0.05), (0.04, 0.38, 0.05), (0, 0.05, 0.115), (0, 0.25, 0.085)]])
    P.obj("Chanfron", H(ch), "Trim", 0, False)
    P.obj("ChanSkull", H(ball((0, 0.13, 0.105), (0.03, 0.025, 0.025), 8, 4)), "Glass")
    P.obj("ChanSpike", H(pipe(bez((0, 0.02, 0.11), (0, 0.04, 0.2), (0, 0.1, 0.27), (0, 0.17, 0.31), 5), [0.024, 0.02, 0.015, 0.01, 0.005, 0.0], 6)), "Trim")
    # ---- a mane of fire along the crest of the neck and a forelock of flame
    for i in range(1, len(neck) - 1):
        p = PTS[i]; t, side, up = FR[i]
        base = p + up * RZ[i] * 0.85
        back = (up * 0.55 - Vector((0, 1, 0)) * 0.8).normalized()
        L = 0.17 + 0.09 * math.sin(math.pi * i / len(neck))
        P.obj("ManeFire", dm_flame(base, back, L, 0.05, Vector((0, -0.4, 0.6)), 5), "Glow", 0)
        P.obj("ManeFire", dm_flame(base + back * 0.02, back, L * 0.6, 0.028, Vector((0, -0.4, 0.6)), 4), "Lamp", 0)
    fl = hp((0, -0.02, 0.1))
    P.obj("ManeFire", dm_flame(fl, Vector((0, 0.6, 0.8)), 0.16, 0.045, Vector((0, -1, 0.3)), 5), "Glow", 0)
    # ---- a tail of fire streaming back from the croup
    tb = W((0, -0.6, 0.2))
    for k in range(5):
        a = (k - 2) * 0.35
        d = Vector((math.sin(a) * 0.35, -1.0, 0.55 + 0.1 * math.cos(a * 2))).normalized()
        P.obj("TailFire", dm_flame(tb, d, 0.42 - 0.05 * abs(k - 2), 0.07, Vector((math.sin(a), 0, 0.6)), 6), "Glow", 0)
    P.obj("TailFire", dm_flame(tb, Vector((0, -1, 0.6)), 0.3, 0.04, Vector((0, 0, 1)), 5), "Lamp", 0)
    # ---- the harness: a heavy iron collar studded with bronze, two spiked hames, a surcingle round the barrel
    cc = W((0, 0.47, 0.24)); CR = Matrix.Rotation(math.radians(-48), 3, "X")
    P.obj("Collar", dm_ring(cc, 0.15, 0.19, 0.032, CR, 20, 6), "Trim")
    for k in range(7):
        a = math.radians(-90 + 30 * k)
        q = cc + CR @ Vector((math.sin(a) * 0.17, -math.cos(a) * 0.21, 0)) + CR @ Vector((0, 0, 0.03))
        P.obj("Stud", ball(tuple(q), (0.016,) * 3, 6, 3), "Accent")
    for s in (1, -1):
        h0 = cc + CR @ Vector((s * 0.12, 0.17, 0))
        P.obj("Hame", cone(h0, h0 + Vector((s * 0.04, -0.05, 0.16)), 0.022, 6), "Trim", 0, False)
    P.obj("Surcingle", dm_ring(W((0, 0.05, 0.19)), 0.205, 0.26, 0.024, Matrix.Rotation(math.radians(90), 3, "X") @ Matrix.Rotation(math.radians(90), 3, "Z"), 26, 5), "Trim")
    P.obj("Buckle", box(tuple(W((0.205, 0.05, 0.19))), (0.02, 0.06, 0.06)), "Accent", 0, False)
    traces = [cc + CR @ Vector((s * 0.16, 0.02, 0)) for s in (1, -1)]
    # ---- the legs, each its own mover hinged at the shoulder or hip: the flying gallop of a horse, burning hooves
    def leg(name, hub, joints, radii):
        hub = W(hub); J = [hub + (W(p) - hub) * Vector((1.0, 1.08, 1.3)) for p in joints]
        legcoat = lambda c, n: "Glow" if dm_crack(c - O, 0.26, 0.06) else "Belly"
        P.part(name, oriented_ball(hub + Vector((0, 0, -0.04)), (0.085, 0.12, 0.15), Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1)), 10, 5), legcoat, tuple(hub))
        P.part(name, pipe([hub] + J[:-1], radii, 9), legcoat, tuple(hub))
        for k in range(1, len(J) - 2):
            P.part(name, ball(tuple(J[k - 1]), (radii[k] * 1.2,) * 3, 8, 4), legcoat, tuple(hub))
        fet, pas, tip = J[-3], J[-2], J[-1]
        d = (tip - pas).normalized()
        P.part(name, ball(tuple(fet), (radii[-2] * 1.35,) * 3, 8, 4), "Belly", tuple(hub))   # the fetlock joint
        P.part(name, pipe([pas - d * 0.02, tip + d * 0.03], [0.042, 0.058], 10), "Dark", tuple(hub))   # the hoof
        a, b = frame(d)
        for k in range(6):   # the coronet burns: a ring of flame tongues licking up off the hoof
            ang = 2 * math.pi * k / 6
            q = pas + (a * math.cos(ang) + b * math.sin(ang)) * 0.045
            P.part(name, dm_flame(q, (a * math.cos(ang) + b * math.sin(ang)) * 0.5 - d * 0.7 + Vector((0, -0.5, 0.3)), 0.1, 0.024, Vector((0, -1, 0)), 4), "Glow", tuple(hub))
    fr, hr = [0.08, 0.055, 0.04, 0.032, 0.032], [0.095, 0.07, 0.048, 0.034, 0.034]
    leg("SwayLeg0" + tag, (0.12, 0.32, 0.02), [(0.13, 0.4, -0.18), (0.13, 0.58, -0.32), (0.13, 0.78, -0.4), (0.13, 0.84, -0.42), (0.13, 0.9, -0.43)], fr)
    leg("SwayLeg1" + tag, (-0.12, 0.32, 0.02), [(-0.13, 0.36, -0.2), (-0.13, 0.5, -0.36), (-0.13, 0.36, -0.5), (-0.13, 0.32, -0.54), (-0.13, 0.3, -0.6)], fr)
    leg("SwayLeg2" + tag, (0.13, -0.42, 0.04), [(0.14, -0.3, -0.18), (0.14, -0.6, -0.3), (0.14, -0.85, -0.42), (0.14, -0.9, -0.44), (0.14, -0.96, -0.45)], hr)
    leg("SwayLeg3" + tag, (-0.13, -0.42, 0.04), [(-0.14, -0.28, -0.2), (-0.14, -0.5, -0.36), (-0.14, -0.4, -0.56), (-0.14, -0.37, -0.6), (-0.14, -0.34, -0.66)], hr)
    dm_grow(P, n0, s0, O, K)
    S = lambda p: O + (Vector(p) - O) * K
    return [S(q) for q in traces], [S(b) for b in bits]


# ---------------------------------------------------------------- the demon lord
def dm_demon(P, F):
    """the demon lord standing in the chariot, his feet at F; built at full size about his feet."""
    F = Vector(F)
    def W(p): return F + Vector(p)
    hide = lambda c, n: "Glow" if dm_crack(c - F, 0.2, 0.07) else "Base"
    # ---- legs in black plate (mostly behind the chariot's breastwork) and a fauld of lames over the hips
    for s in (1, -1):
        hip, knee, ank = W((s * 0.19, 0.0, 0.95)), W((s * 0.24, 0.1, 0.5)), W((s * 0.24, -0.02, 0.1))
        P.obj("Cuisse", pipe([hip, knee], [0.17, 0.13], 12), "Trim")
        P.obj("Poleyn", ball(tuple(knee + Vector((0, 0.06, 0))), (0.12, 0.1, 0.11), 10, 5), "Trim")
        P.obj("Greave", pipe([knee, ank], [0.12, 0.09], 12), "Trim")
        P.obj("Sabaton", hull([tuple(ank + Vector(q)) for q in ((-0.09, -0.12, -0.1), (0.09, -0.12, -0.1), (-0.08, 0.22, -0.1), (0.08, 0.22, -0.1), (-0.08, -0.08, 0.05), (0.08, -0.08, 0.05), (0, 0.3, -0.06))]), "Trim", 0, False)
    for k in range(3):
        P.obj("Fauld", dm_ring(W((0, 0.0, 1.02 - k * 0.08)), 0.37 + k * 0.025, 0.27 + k * 0.02, 0.045, None, 24, 5), "Trim" if k % 2 == 0 else "Accent")
    for s in (1, -1):   # tassets hanging over the thighs
        P.obj("Tasset", hull([tuple(W(q)) for q in ((s * 0.08, 0.22, 0.98), (s * 0.34, 0.15, 0.98), (s * 0.09, 0.26, 0.72), (s * 0.36, 0.17, 0.74),
                                                     (s * 0.08, 0.18, 0.98), (s * 0.34, 0.11, 0.98), (s * 0.09, 0.22, 0.72), (s * 0.36, 0.13, 0.74))]), "Trim", 0, False)
        P.obj("TassetRim", pipe([W((s * 0.09, 0.265, 0.72)), W((s * 0.36, 0.175, 0.74))], [0.018, 0.018], 6), "Accent")
    # ---- the torso: a towering V of muscle, the hide split by glowing cracks
    tor = lathe([(0.0, 0.95), (0.3, 0.96), (0.33, 1.05), (0.31, 1.18), (0.38, 1.35), (0.55, 1.55), (0.63, 1.7), (0.56, 1.8), (0.3, 1.88), (0.0, 1.9)], 32, "z", tuple(F))
    for v in tor.verts: v.co.y = F.y + (v.co.y - F.y) * 0.62
    P.obj("Torso", tor, hide, 1)
    for s in (1, -1):   # the belly under the plate: three rows of abdominal muscle
        for k in range(3):
            P.obj("Abs", ball(tuple(W((s * 0.085, 0.19, 1.08 + k * 0.1))), (0.075, 0.05, 0.05), 10, 5), hide)
    # the breastplate: blackened iron over the chest, bronze-rimmed, riveted evenly, a burning sigil in the middle
    bp = lathe([(0.4, 1.31), (0.57, 1.53), (0.655, 1.69), (0.58, 1.8), (0.33, 1.87)], 32, "z", tuple(F))
    for v in bp.verts: v.co.y = F.y + (v.co.y - F.y) * 0.66
    P.obj("Breastplate", bp, lambda c, n: "Accent" if (c - F).z < 1.36 or (c - F).z > 1.83 else "Trim", 0)
    for k in range(12):
        a = math.radians(-80 + 160 * k / 11)
        for z, r in ((1.38, 0.47), (1.79, 0.6)):
            P.obj("Rivet", ball(tuple(W((math.sin(a) * r, math.cos(a) * r * 0.66 + 0.01, z))), (0.018,) * 3, 5, 3), "Accent")
    sg = W((0, 0.425, 1.6)); SR = Matrix.Rotation(math.radians(90), 3, "X") @ Matrix.Rotation(math.radians(-6), 3, "X")
    P.obj("Sigil", dm_ring(sg, 0.14, 0.14, 0.018, Matrix.Rotation(math.radians(-82), 3, "X"), 30, 5), "Glow")
    star = [sg + Matrix.Rotation(math.radians(-82), 3, "X") @ Vector((math.sin(2 * math.pi * k / 5 + math.pi) * 0.13, math.cos(2 * math.pi * k / 5 + math.pi) * 0.13, 0.0)) for k in range(5)]
    for k in range(5):   # an inverted five-pointed star burning inside the ring
        P.obj("Sigil", pipe([star[k], star[(k + 2) % 5]], [0.012, 0.012], 5), "Glow")
    P.obj("SigilCore", ball(tuple(sg + Vector((0, 0.01, 0))), (0.04, 0.02, 0.04), 8, 4), "Lamp")
    # the gorget: two lames round the neck
    for k in range(2):
        P.obj("Gorget", dm_ring(W((0, 0.0, 1.86 + k * 0.06)), 0.29 - k * 0.05, 0.22 - k * 0.04, 0.035, None, 26, 6), "Trim" if k == 0 else "Accent")
    # ---- the pauldrons: three overlapping lames on each shoulder, bronze-edged, spiked
    for s in (1, -1):
        S0 = W((s * 0.62, 0.0, 1.76))
        for k, (dx, dz, r) in enumerate(((0.0, 0.1, (0.27, 0.26, 0.17)), (0.1, 0.0, (0.25, 0.25, 0.12)), (0.17, -0.08, (0.2, 0.22, 0.1)))):
            c = S0 + Vector((s * dx, 0, dz)); zc = c.z
            P.obj("Pauldron", ball(tuple(c), r, 14, 7), lambda q, n, zc=zc, r=r: "Accent" if q.z < zc - r[2] * 0.55 else "Trim")
        for k in range(3):
            b = S0 + Vector((s * (0.02 + 0.09 * k), -0.06 + 0.06 * k, 0.24 - 0.03 * k))
            P.obj("PSpike", cone(tuple(b), tuple(b + Vector((s * (0.08 + 0.05 * k), 0, 0.3 - 0.06 * k))), 0.05, 6), "Trim", 0, False)
    # ---- the arms: the right raises the greatsword, the left holds a fireball out at the player
    arms = {1: (W((0.62, 0.0, 1.7)), W((0.97, 0.1, 2.02)), W((0.82, 0.28, 2.42))), -1: (W((-0.62, 0.0, 1.7)), W((-0.92, 0.3, 1.45)), W((-0.76, 0.68, 1.56)))}
    for s, (sh, el, hd) in arms.items():
        P.obj("Arm", pipe([sh, sh + (el - sh) * 0.5, el], [0.15, 0.16, 0.12], 12), hide, 1)
        P.obj("Bicep", oriented_ball(sh + (el - sh) * 0.45 + Vector((0, 0.05, 0)), (0.12, 0.13, 0.18), Vector((1, 0, 0)), Vector((0, 1, 0)), (el - sh).normalized(), 10, 5), hide)
        P.obj("Couter", ball(tuple(el), (0.12, 0.12, 0.12), 10, 5), "Trim")
        P.obj("CouterSpike", cone(tuple(el), tuple(el + (el - sh).normalized() * 0.08 + (el - hd).normalized() * 0.18), 0.045, 6), "Trim", 0, False)
        P.obj("Vambrace", pipe([el + (hd - el) * 0.15, hd - (hd - el).normalized() * 0.08], [0.12, 0.1], 12), lambda c, n, el=el, hd=hd: "Accent" if abs(((c - el).dot((hd - el).normalized())) - 0.22) < 0.03 else "Trim")
        P.obj("Gauntlet", ball(tuple(hd), (0.12, 0.12, 0.12), 12, 6), "Trim")
        for k in range(4):   # clawed fingers curled round the grip
            a = math.radians(-45 + 30 * k)
            q = hd + Vector((math.sin(a) * 0.1, math.cos(a) * 0.1 * s, 0.03))
            P.obj("Claw", cone(tuple(q), tuple(q + Vector((math.sin(a) * 0.06, 0.06, -0.04))), 0.022, 5), "Glass", 0, False)
    # the greatsword: a long blade of black steel, its fuller burning, flames licking off both edges
    sh, el, hd = arms[1]
    d = Vector((-0.34, 0.12, 1.0)).normalized(); A = d.cross(Vector((0, 1, 0))).normalized(); B = A.cross(d).normalized()
    G = hd + d * 0.18
    P.obj("Grip", pipe([hd - d * 0.2, G], [0.035, 0.035], 8), lambda c, n: "Dark" if int(((c - hd).dot(d) + 0.3) * 30) % 2 else "Trim")
    P.obj("Pommel", ball(tuple(hd - d * 0.24), (0.06, 0.06, 0.06), 10, 5), "Accent")
    P.obj("Guard", pipe([G + A * 0.3 - d * 0.08, G + A * 0.22, G, G - A * 0.22, G - A * 0.3 - d * 0.08], [0.03, 0.04, 0.05, 0.04, 0.03], 8), "Trim")
    P.obj("GuardSkull", ball(tuple(G + B * 0.03), (0.06, 0.05, 0.06), 10, 5), "Glass")
    for s in (1, -1):
        P.obj("GuardEye", ball(tuple(G + B * 0.075 + A * s * 0.022 + d * 0.01), (0.012,) * 3, 6, 3), "Glow")
    L = 1.1; T = G + d * L
    bl = [G + A * sx * 0.085 + B * sb * 0.022 for sx in (1, -1) for sb in (1, -1)]
    bl += [G + d * L * 0.75 + A * sx * 0.07 + B * sb * 0.016 for sx in (1, -1) for sb in (1, -1)] + [T]
    P.obj("Blade", hull([tuple(p) for p in bl]), "Trim", 0, False)
    for sb in (1, -1):
        P.obj("Fuller", hull([tuple(G + d * 0.05 + B * sb * 0.024 + A * sx * 0.018) for sx in (1, -1)] + [tuple(G + d * L * 0.8 + B * sb * 0.018 + A * sx * 0.01) for sx in (1, -1)]
                             + [tuple(G + d * 0.05 + B * sb * 0.015 + A * sx * 0.018) for sx in (1, -1)]), "Lamp", 0, False)
    for sx in (1, -1):   # the edges burn: a row of flame tongues licking up and back off each edge
        P.obj("BladeEdge", pipe([G + A * sx * 0.088, G + d * L * 0.75 + A * sx * 0.073, T], [0.012, 0.01, 0.0], 5), "Glow")
        for k in range(8):
            u = 0.08 + 0.1 * k
            w = 0.085 - 0.02 * u
            q = G + d * L * u + A * sx * w
            P.obj("BladeFire", dm_flame(q, A * sx * 0.65 + d * 0.6 - Vector((0, 0.35, 0)), 0.16 - 0.06 * u, 0.03, Vector((0, -1, 0.4)), 4), "Glow", 0)
    P.obj("BladeFire", dm_flame(T - d * 0.02, d, 0.22, 0.035, Vector((0, -1, 0.3)), 5), "Glow", 0)
    # the fireball in his left hand: a ball of fire with a white-hot core and tongues swirling off it
    shL, elL, hdL = arms[-1]
    fc = hdL + Vector((0.02, 0.2, 0.14))
    P.obj("Fireball", ball(tuple(fc), (0.21, 0.21, 0.21), 16, 8), "Glow")
    P.obj("FireCore", ball(tuple(fc + Vector((0, 0.06, 0))), (0.13, 0.13, 0.13), 12, 6), "Lamp")
    for k in range(9):
        a = 2 * math.pi * k / 9; e = math.radians(25 * math.sin(3 * a))
        o = Vector((math.cos(a) * math.cos(e), -0.25, math.sin(a) * math.cos(e) + 0.2)).normalized()
        P.obj("FireTongue", dm_flame(fc + o * 0.17, o + Vector((0, -0.6, 0.4)), 0.24, 0.07, Vector((-math.sin(a), 0, math.cos(a))), 5), "Glow", 0)
    # ---- the head: a broad horned skull, a heavy brow, burning eyes, a fanged roar
    Hc = W((0, 0.07, 2.19))
    face = "Base"
    def h(p): return Hc + Vector(p)
    P.obj("Head", ball(tuple(Hc), (0.25, 0.24, 0.27), 18, 10), face, 0)
    P.obj("Neck", pipe([W((0, 0.0, 1.82)), Hc + Vector((0, -0.04, -0.12))], [0.17, 0.16], 12), face)
    P.obj("Cheek", ball(tuple(h((0, 0.1, -0.08))), (0.24, 0.18, 0.15), 14, 7), face, 0)
    P.obj("Snout", ball(tuple(h((0, 0.15, -0.17))), (0.2, 0.17, 0.12), 14, 7), face, 0)
    P.obj("Mouth", ball(tuple(h((0, 0.24, -0.17))), (0.15, 0.08, 0.085), 12, 6), "Dark")
    P.obj("Throat", ball(tuple(h((0, 0.26, -0.18))), (0.09, 0.04, 0.05), 10, 5), "Glow")
    P.obj("Jaw", ball(tuple(h((0, 0.14, -0.3))), (0.17, 0.15, 0.07), 12, 6), face, 0)
    for s in (1, -1):
        P.obj("Fang", cone(tuple(h((s * 0.085, 0.29, -0.11))), tuple(h((s * 0.08, 0.31, -0.24))), 0.03, 6), "Glass", 0, False)
        P.obj("Tusk", pipe(bez(h((s * 0.12, 0.25, -0.29)), h((s * 0.15, 0.3, -0.2)), h((s * 0.18, 0.33, -0.12)), h((s * 0.2, 0.32, -0.05)), 4), [0.035, 0.03, 0.022, 0.012, 0.0], 6), "Glass")
        for k in range(2):
            x = s * (0.03 + 0.03 * k)
            P.obj("Tooth", cone(tuple(h((x, 0.315, -0.13))), tuple(h((x, 0.32, -0.18))), 0.014, 4), "Glass", 0, False)
            P.obj("Tooth", cone(tuple(h((x, 0.29, -0.24))), tuple(h((x, 0.3, -0.2))), 0.014, 4), "Glass", 0, False)
        P.obj("Socket", oriented_ball(h((s * 0.1, 0.205, 0.0)), (0.075, 0.035, 0.045), Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1)), 12, 6), "Dark")
        e = Matrix.Rotation(math.radians(-s * 22), 3, "Y")
        P.obj("Eye", oriented_ball(h((s * 0.1, 0.225, 0.0)), (0.055, 0.02, 0.018), e @ Vector((1, 0, 0)), Vector((0, 1, 0)), e @ Vector((0, 0, 1)), 10, 5), "Lamp")
        P.obj("Brow", oriented_ball(h((s * 0.11, 0.21, 0.07)), (0.12, 0.06, 0.045), e @ Vector((1, 0, 0)), Vector((0, 1, 0)), e @ Vector((0, 0, 1)), 12, 6), face)
        P.obj("Ear", cone(tuple(h((s * 0.23, 0.0, 0.02))), tuple(h((s * 0.42, -0.12, 0.14))), 0.07, 6), face, 0, False)
        P.obj("Snarl", pipe([h((s * 0.02, 0.29, -0.0)), h((s * 0.06, 0.27, 0.01)), h((s * 0.09, 0.24, -0.02))], [0.012, 0.014, 0.008], 5), "Dark")   # the snout creased in a snarl
        P.obj("Nostril", ball(tuple(h((s * 0.035, 0.31, -0.06))), (0.022, 0.02, 0.018), 8, 4), "Dark")
        # the horns: thick ridged horns sweeping out and back, then curling up and forward
        hp_ = bez(h((s * 0.16, 0.0, 0.17)), h((s * 0.5, -0.25, 0.28)), h((s * 0.78, -0.12, 0.72)), h((s * 0.58, 0.22, 0.86)), 16)
        base = hp_[0]; Lh = sum((b - a).length for a, b in zip(hp_, hp_[1:]))
        P.obj("Horn", pipe(hp_, [0.1 * (1 - i / 16) ** 0.8 + 0.004 for i in range(16)] + [0.0], 12),
              lambda c, n, base=base, Lh=Lh: "Glass" if (c - base).length > Lh * 0.62 else ("Dark" if ((c - base).length * 22) % 1.0 < 0.3 else "Belly"))
    # the crown: a band of black iron round the brow, nine spikes graded tallest at the front, an ember set in front
    crc = h((0, 0.0, 0.19))
    P.obj("Crown", dm_ring(crc, 0.22, 0.21, 0.035, Matrix.Rotation(math.radians(-8), 3, "X"), 30, 6), "Trim")
    for k in range(9):
        a = math.radians(-120 + 30 * k)
        b = crc + Vector((math.sin(a) * 0.22, math.cos(a) * 0.21, 0.02 + 0.03 * math.cos(a)))
        P.obj("CrownSpike", cone(tuple(b), tuple(b + Vector((math.sin(a) * 0.05, math.cos(a) * 0.05, 0.13 + 0.12 * (1 + math.cos(a)) * 0.5))), 0.032, 6), "Trim", 0, False)
    P.obj("CrownGem", ball(tuple(crc + Vector((0, 0.23, 0.04))), (0.035, 0.022, 0.045), 8, 4), "Glow")
    # ---- the cape: tattered black cloth streaming back from his shoulders, its torn edge burning
    bm = bmesh.new(); NC, NR = 11, 8; G2 = []
    for j in range(NR + 1):
        row = []
        for i in range(NC + 1):
            u = i / NC - 0.5; v = j / NR
            if j == NR: v *= 1.0 - 0.16 * (i % 2)
            x = u * (1.05 + 0.55 * v)
            y = -0.3 - 0.5 * v ** 1.4 - 0.06 * v * math.cos(u * 3) + 0.06 * math.sin(u * 11 + v * 4) * v
            z = 1.78 - 1.3 * v
            row.append(bm.verts.new(tuple(W((x, y, z)))))
        G2.append(row)
    for j in range(NR):
        for i in range(NC):
            bm.faces.new((G2[j][i], G2[j][i + 1], G2[j + 1][i + 1], G2[j + 1][i]))
    sheet_solid(bm, 0.025)
    P.obj("ClothCape", bm, lambda c, n: "Glow" if (c - F).z < 0.62 + 0.08 * math.sin((c - F).x * 14) else "Belly", 0)
    return h((0, 0.3, -0.17))


def L_demon():
    """The last boss, the DEMON LORD (2026-10-14, remade: "same as the alien bosses - realistic details, scarier, keep the cartoon shape";
    "something impressive and new - when people see it they say ahhhh"): the same horned, crowned lord of the inferno with a flaming
    greatsword and a fireball, now built with real weight. A towering demon - a V of muscle from broad shoulders to a narrow waist, three rows
    of abdominal muscle under the breastplate, thick arms - his dark crimson hide split all over by glowing cracks, as if the fire were
    showing through. His head is broad and heavy: a brow ridge drawn down in a scowl over two burning eyes in black sockets, a snout
    creased in a snarl, the jaws open in a roar on two long fangs, curved tusks and rows of teeth, a glow deep in the throat (his shots
    leave from it), pointed ears laid back; two thick horns ridged all along their length sweep out and back from his skull and curl up and
    forward, black at the root and ivory at the tips; a crown of black iron round his brow, nine spikes graded tallest at the front, an
    ember set in front. He wears blackened plate: a gorget of two lames, a breastplate rimmed in bronze and riveted evenly round its edges
    with an inverted five-pointed star burning in a ring on the chest, pauldrons of three overlapping lames edged in bronze with three
    spikes on each, spiked couters at the elbows, bronze-banded vambraces and clawed gauntlets, a fauld of lames over the hips, tassets,
    cuisses, poleyns, greaves and sabatons. In his raised right hand a greatsword of black steel - a long blade with its fuller burning
    white, flames licking evenly off both edges and its point, a crossguard of black iron with a skull at its heart, a wrapped grip and a
    bronze pommel; in his left, held out at the player, a fireball, white-hot in the middle, tongues of fire swirling off it. A tattered
    cape of black cloth streams back from his shoulders, its torn edge burning.
    He flies in a HELLFIRE CHARIOT DRAWN BY TWO NIGHTMARES: he stands in a heavy war chariot of black iron, its breastwork curving round
    from the sides and rising at the front, bronze-railed, a row of spikes along its rim, iron plates riveted in rows, a demon's skull
    with horns and burning eyes on the prow and a burning sigil on each flank. Two great iron wheels, spiked round the tyre, eight spokes,
    long scythe blades on the hubs, burn and spin (WheelL, WheelR), and a trail of fire streams away behind them. The pole runs forward to
    a yoke between two nightmare horses, built like real horses at a flying gallop - deep chests, arched necks, strong quarters, long legs,
    each leg its own mover (SwayLeg0-3, A the right horse and B the left) - their coats coal-black and cracked with fire, manes and tails
    of flame, burning eyes and nostrils, mouths torn open on their teeth, ears pinned back, a chanfron of black iron with a spike on each
    face, iron collars studded with bronze and spiked hames; iron chains run from their collars back to the chariot."""
    P = Boss("demon", {"Base": ((0.42, 0.045, 0.035), 0.5), "Belly": ((0.055, 0.045, 0.045), 0.45), "Accent": ((0.8, 0.46, 0.13), 0.75),
                       "Trim": ((0.075, 0.068, 0.075), 0.7), "Glass": ((0.86, 0.79, 0.64), 0.55), "Dark": ((0.02, 0.012, 0.012), 0.4),
                       "Glow": ((1.0, 0.36, 0.03), 0.5), "Metal": ((0.62, 0.62, 0.66), 0.75), "Lamp": ((1.0, 0.86, 0.42), 0.8)})
    FLOOR = -0.3
    # ---- the chariot: an iron floor, a breastwork curving round from the sides and rising at the front
    P.obj("Floor", box((0, -0.6, FLOOR - 0.035), (1.1, 0.9, 0.07)), "Trim", 0, False)
    path = [(-0.55, -1.05), (-0.55, -0.8)]
    for k in range(13):
        a = math.pi - math.pi * k / 12
        path.append((math.cos(a) * 0.55, -0.48 + math.sin(a) * 0.42))
    path += [(0.55, -0.8), (0.55, -1.05)]
    path = [Vector((x, y, 0)) for x, y in path]
    def hgt(p):
        f = max(0.0, min(1.0, (p.y + 1.05) / 0.99))
        return 0.22 + 0.42 * (f * f * (3 - 2 * f)) + 0.14 * max(0.0, 1 - abs(p.x) / 0.35) * f
    wb = bmesh.new(); cols = []
    for i, p in enumerate(path):
        t = (path[min(i + 1, len(path) - 1)] - path[max(i - 1, 0)]).normalized()
        nrm = Vector((t.y, -t.x, 0))
        if nrm.dot(Vector((p.x, p.y + 0.55, 0))) < 0: nrm = -nrm
        o, inn = p + nrm * 0.035, p - nrm * 0.035; H_ = hgt(p)
        fl = nrm * 0.09   # the breastwork flares outward toward its rim
        cols.append([wb.verts.new((o.x, o.y, FLOOR)), wb.verts.new((o.x + fl.x, o.y + fl.y, FLOOR + H_)), wb.verts.new((inn.x + fl.x, inn.y + fl.y, FLOOR + H_)), wb.verts.new((inn.x, inn.y, FLOOR))])
    for c0, c1 in zip(cols, cols[1:]):
        for k in range(4):
            wb.faces.new((c0[k], c0[(k + 1) % 4], c1[(k + 1) % 4], c1[k]))
    wb.faces.new(list(reversed(cols[0]))); wb.faces.new(cols[-1]); bmesh.ops.recalc_face_normals(wb, faces=wb.faces)
    P.obj("Breastwork", wb, lambda c, n: "Accent" if abs(c.z - (FLOOR + 0.06)) < 0.04 else "Trim", 0, False)
    rail = [Vector((p.x, p.y, FLOOR + hgt(p))) + Vector((p.x, p.y + 0.55, 0)).normalized() * 0.11 for p in path]
    P.obj("Rail", pipe(rail, [0.035] * len(rail), 8), "Accent")
    for i, p in enumerate(path):
        out = Vector((p.x, p.y + 0.55, 0)).normalized()
        top = Vector((p.x, p.y, FLOOR + hgt(p))) + out * 0.09
        if 1 <= i <= len(path) - 2:
            P.obj("RimSpike", cone(tuple(top + Vector((0, 0, 0.02))), tuple(top + out * 0.06 + Vector((0, 0, 0.16))), 0.03, 6), "Trim", 0, False)
        for z in (0.1, 0.25, 0.4):   # rows of rivets on the plates
            if z < hgt(p) - 0.06 and i % 2 == 0:
                P.obj("Rivet", ball(tuple(Vector((p.x, p.y, FLOOR + z)) + out * (0.045 + 0.09 * z / hgt(p))), (0.017,) * 3, 5, 3), "Accent")
    # the demon's skull on the prow: horned, its eyes burning, its fangs bared
    sk = Vector((0, -0.04, FLOOR + 0.42))
    P.obj("ProwSkull", ball(tuple(sk), (0.17, 0.09, 0.15), 14, 7), "Glass")
    P.obj("ProwJaw", ball(tuple(sk + Vector((0, 0.03, -0.12))), (0.11, 0.07, 0.06), 10, 5), "Glass")
    for s in (1, -1):
        P.obj("ProwSocket", ball(tuple(sk + Vector((s * 0.06, 0.07, 0.01))), (0.045, 0.03, 0.04), 8, 4), "Dark")
        P.obj("ProwEye", ball(tuple(sk + Vector((s * 0.06, 0.09, 0.01))), (0.025, 0.015, 0.02), 8, 4), "Glow")
        P.obj("ProwHorn", pipe(bez(sk + Vector((s * 0.13, 0.0, 0.08)), sk + Vector((s * 0.3, 0.05, 0.16)), sk + Vector((s * 0.36, 0.12, 0.0)), sk + Vector((s * 0.3, 0.16, -0.12)), 8),
                                    [0.045 * (1 - i / 8) + 0.003 for i in range(8)] + [0.0], 8), "Glass")
        P.obj("ProwFang", cone(tuple(sk + Vector((s * 0.04, 0.08, -0.09))), tuple(sk + Vector((s * 0.04, 0.09, -0.19))), 0.018, 5), "Glass", 0, False)
        # a burning sigil on each flank
        sc = Vector((s * 0.6, -0.68, FLOOR + 0.2))
        P.obj("FlankSigil", dm_ring(sc, 0.11, 0.11, 0.016, Matrix.Rotation(math.radians(90), 3, "Y"), 24, 5), "Glow")
        P.obj("FlankSigil", ball(tuple(sc), (0.01, 0.05, 0.05), 8, 4), "Lamp")
    # ---- under it: the axle and two great burning wheels
    AX = (-0.62, FLOOR - 0.04)
    P.obj("Axle", pipe([(-0.82, AX[0], AX[1]), (0.82, AX[0], AX[1])], [0.045, 0.045], 8), "Trim")
    WR = 0.47
    for s in (1, -1):
        hub = Vector((s * 0.76, AX[0], AX[1])); nm = "WheelR" if s > 0 else "WheelL"
        RY = Matrix.Rotation(math.radians(90), 4, "Y")
        P.part(nm, xf(torus(WR, 0.045, 0.0, 28, 6), RY, tuple(hub)), "Trim", tuple(hub))
        P.part(nm, xf(torus(WR + 0.035, 0.03, 0.0, 28, 5), RY, tuple(hub)), "Dark", tuple(hub))
        P.part(nm, xf(torus(WR - 0.06, 0.02, 0.0, 28, 4), RY, tuple(hub)), "Accent", tuple(hub))
        for k in range(14):
            a = 2 * math.pi * k / 14; r = Vector((0, math.cos(a), math.sin(a)))
            P.part(nm, cone(hub + r * (WR + 0.05), hub + r * (WR + 0.17), 0.03, 5), "Trim", tuple(hub), 0, False)
        for k in range(8):
            a = 2 * math.pi * (k + 0.5) / 8; r = Vector((0, math.cos(a), math.sin(a)))
            P.part(nm, pipe([hub + r * 0.08, hub + r * (WR - 0.03)], [0.03, 0.022], 6), "Trim", tuple(hub))
            # the rim burns: tongues of flame licking back off it as it turns
            q = hub + r * (WR + 0.02); tg = Vector((0, -math.sin(a), math.cos(a)))
            P.part(nm, dm_flame(q, r * 0.6 - tg * 0.7, 0.2, 0.045, -tg, 4), "Glow", tuple(hub))
        P.part(nm, xf(lathe([(0.0, -0.06), (0.11, -0.06), (0.12, 0.0), (0.1, 0.07), (0.0, 0.08)], 14, "x"), None, tuple(hub)), "Accent", tuple(hub))
        P.part(nm, pipe([hub + Vector((s * 0.06, 0, 0)), hub + Vector((s * 0.22, 0, 0)), hub + Vector((s * 0.42, 0, 0))], [0.06, 0.04, 0.0], 8), "Trim", tuple(hub))   # the scythe hub
        P.part(nm, xf(torus(0.07, 0.018, 0.0, 16, 5), RY, tuple(hub + Vector((s * 0.12, 0, 0)))), "Accent", tuple(hub))
        # a trail of fire streaming back behind the wheel
        for k in range(3):
            b = Vector((s * (0.76 + (k - 1) * 0.07), AX[0] - 0.35, AX[1] - 0.25 + 0.08 * k))
            P.obj("ClothTrail", dm_flame(b, Vector((0, -1, 0.12 + 0.08 * k)), 1.0 - 0.18 * abs(k - 1), 0.1 - 0.02 * abs(k - 1), Vector((s * 0.3, 0, 1)), 8), "Glow" if k != 1 else "Lamp", 0)
        for k in range(5):   # embers flung off the trail, evenly
            q = Vector((s * (0.76 + 0.1 * math.sin(k * 2.1)), AX[0] - 0.55 - 0.2 * k, AX[1] - 0.05 + 0.08 * k))
            P.obj("ClothTrail", ball(tuple(q), (0.035 - 0.004 * k,) * 3, 6, 3), "Lamp")
    # ---- the demon lord stands in it
    mz = dm_demon(P, (0, -0.62, FLOOR))
    # ---- the pole, the yoke and the two nightmares
    K = 1.15; HY = 1.5
    traces, bits = [], []
    for tag, x in (("A", 0.42), ("B", -0.42)):
        t, b = dm_horse(P, (x, HY, -0.02), tag, K); traces += t; bits += b
    P.obj("Pole", pipe([(0, -0.1, FLOOR + 0.02), (0, 0.6, FLOOR + 0.15), (0, HY + 0.62, 0.2)], [0.045, 0.04, 0.035], 8), lambda c, n: "Accent" if (c.y * 5) % 1.0 < 0.12 else "Trim")
    P.obj("Yoke", pipe([(-0.62, HY + 0.6, 0.36), (-0.3, HY + 0.62, 0.3), (0, HY + 0.62, 0.22), (0.3, HY + 0.62, 0.3), (0.62, HY + 0.6, 0.36)], [0.04] * 5, 8), "Trim")
    P.obj("YokeSkull", ball((0, HY + 0.66, 0.24), (0.06, 0.05, 0.06), 8, 4), "Glass")
    corners = [Vector((0.42, -0.2, FLOOR + 0.35)), Vector((0.22, -0.12, FLOOR + 0.35)), Vector((-0.22, -0.12, FLOOR + 0.35)), Vector((-0.42, -0.2, FLOOR + 0.35))]
    # traces: from each collar's outer and inner side back to the breastwork
    for q, c in zip(traces, corners):
        dm_chain(P, q, c, 0.12)
    for q in bits:   # the reins: black leather from the bits back to a ring on the prow
        e = Vector((0, -0.06, FLOOR + 0.82)); m = (q + e) * 0.5 - Vector((0, 0, 0.18))
        P.obj("ClothRein", pipe(bez(q, q + (m - q) * 0.6, e + (m - e) * 0.6, e, 8), [0.012] * 9, 5), "Dark", 0)
    P.part("Muzzle", ball(tuple(mz), (0.05, 0.03, 0.04), 8, 4), "Glow", tuple(mz))
    return P


BOSSES = [("scarab", L_scarab), ("golem", L_golem), ("ifrit", L_ifrit), ("salamander", L_salamander), ("demon", L_demon)]   # 2026-10-11 previews

if __name__ == "__main__":
    os.makedirs(AB.OUT, exist_ok=True)
    for bid, fn in BOSSES:
        if ONLY and bid not in ONLY: continue
        fn().finish()
    print("DONE")
