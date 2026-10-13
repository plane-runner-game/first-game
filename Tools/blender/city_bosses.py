# Sky Squad, downtown's five bosses (2026-10-11: "the rest of the worlds that have no bosses yet"): the billboard blimp, the news chopper,
# the king pigeon, the traffic titan and the skyscraper fortress. Built from code like the other worlds' bosses (alien_bosses.py lends its
# Boss class and shapes).
# Run: blender -b -P Tools/blender/city_bosses.py -- <out dir> [export] [ids,comma,separated]
# Conventions as alien_bosses.py: +Y nose, +Z up, +X right; "Prop*" spin about the nose, "Rotor*" about up, "TailRotor" about the wing axis,
# "Flap*" rock about the nose axis, "Sway*" about the wing axis, "Spin*" turn slowly about up, "Muzzle" is where his shots leave from.
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

TAXI = ((1.0, 0.76, 0.06), 0.6)
GOLD = ((0.98, 0.76, 0.22), 0.8)
STEEL = ((0.55, 0.58, 0.62), 0.7)


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

def rings_of(profile, step=0.12):
    """(y, r) keys -> loft rings every step along y, round sections."""
    out = []
    for (y0, r0), (y1, r1) in zip(profile, profile[1:]):
        n = max(1, int(abs(y1 - y0) / step))
        for i in range(n):
            t = i / n; s = 0.5 - 0.5 * math.cos(math.pi * t)
            out.append((y0 + (y1 - y0) * t, r0 + (r1 - r0) * s, r0 + (r1 - r0) * s, 0, 0))
    out.append((profile[-1][0], profile[-1][1], profile[-1][1], 0, 0))
    return out

def at(bm, t):
    return xf(bm, None, t)


# ================================================================= 1. the billboard blimp
def C_blimp():
    """An advertising airship over downtown: a silver envelope with a red nose cap and red fins, glowing LED screens down both flanks, a neon
    billboard standing on its back facing you, a gondola with lit windows and two propellers."""
    P = Boss("blimp", {"Base": ((0.82, 0.84, 0.88), 0.55), "Belly": ((0.62, 0.65, 0.70), 0.5), "Accent": ((0.85, 0.12, 0.12), 0.6), "Trim": GOLD,
                       "Glass": ((0.10, 0.80, 1.0), 0.9), "Dark": ((0.06, 0.07, 0.09), 0.5), "Glow": ((0.15, 0.85, 1.0), 0.5),
                       "Metal": STEEL, "Lamp": ((1.0, 0.30, 0.70), 0.8)})
    prof = [(-2.35, 0.06), (-2.0, 0.5), (-1.2, 0.92), (0.0, 1.05), (1.2, 0.95), (1.85, 0.62), (2.15, 0.25), (2.25, 0.04)]
    def env(c, n):
        if c.y > 1.8: return "Accent"
        if abs(n.x) > 0.55 and abs(c.y) < 1.15 and -0.35 < c.z < 0.45:
            if (c.y * 5.0) % 1.0 < 0.12 or abs(c.z - 0.05) < 0.03: return "Dark"
            return "Glass" if (int((c.y + 2) * 2.5) + (1 if c.z > 0.05 else 0)) % 3 else "Lamp"
        if abs(n.x) > 0.5 and abs(c.y) < 1.25 and -0.45 < c.z < 0.55: return "Dark"
        if abs(c.y + 1.45) < 0.06 or abs(c.y - 1.45) < 0.06: return "Accent"
        return "Belly" if n.z < -0.5 else "Base"
    P.obj("Body", loft(rings_of(prof, 0.1), 32), env, 0)
    # four red tail fins
    for k in range(4):
        a = math.radians(45 + 90 * k)
        secs = [(0.0, airfoil(-1.55, -2.25, 0.08, 0.0)), (0.45, airfoil(-1.75, -2.3, 0.06, 0.0)), (0.85, airfoil(-2.0, -2.38, 0.05, 0.0))]
        fb = sweep(secs, "x")
        for v in fb.verts:
            v.co += Vector((0.55, 0, 0))
            v.co = Matrix.Rotation(a, 3, "Y") @ v.co
        P.obj("Fin", fb, lambda c, n: "Trim" if math.hypot(c.x, c.z) > 1.3 else "Accent", 0, False)
    # the neon billboard on its back, facing the player
    P.obj("Pylon", box((-0.45, 0.0, 1.15), (0.08, 0.08, 0.35)), "Metal", 0, False)
    P.obj("Pylon", box((0.45, 0.0, 1.15), (0.08, 0.08, 0.35)), "Metal", 0, False)
    P.obj("Board", box((0, 0.0, 1.62), (1.7, 0.12, 0.72)), "Dark", 0, False)
    for i in range(6):
        for j in range(3):
            slot = "Lamp" if (i + j) % 2 else "Glass"
            if j == 1 and 1 <= i <= 4: slot = "Trim"
            P.obj("Pixel", box((-0.68 + i * 0.272, 0.07, 1.4 + j * 0.22), (0.23, 0.03, 0.18)), slot, 0, False)
    for s in (1, -1):
        for k in range(4): P.obj("Bulb", ball((s * (0.88), 0.08, 1.3 + k * 0.21), (0.04, 0.04, 0.04), 6, 3), "Trim")
    # the gondola
    P.obj("Gondola", loft([(0.95, 0.06, 0.06, 0, -1.08), (0.8, 0.28, 0.2, 0, -1.12), (0.0, 0.34, 0.24, 0, -1.15), (-0.7, 0.26, 0.2, 0, -1.12), (-0.85, 0.05, 0.05, 0, -1.08)], 14),
          lambda c, n: "Lamp" if abs(n.x) > 0.6 and abs(c.z + 1.12) < 0.07 and (c.y * 5) % 1.0 > 0.35 else ("Glass" if c.y > 0.65 and n.z > -0.3 else "Accent"), 1)
    for s in (1, -1):
        P.obj("Strut", pipe([(s * 0.18, 0.4, -1.0), (s * 0.3, 0.4, -0.88)], [0.03, 0.03], 6), "Metal")
        P.obj("Strut", pipe([(s * 0.18, -0.4, -1.0), (s * 0.3, -0.4, -0.88)], [0.03, 0.03], 6), "Metal")
        P.obj("Arm", pipe([(s * 0.3, -0.35, -1.1), (s * 0.85, -0.35, -1.0)], [0.035, 0.035], 6), "Metal")
        P.obj("Nacelle", loft([(-0.05, 0.06, 0.06, s * 0.88, -1.0), (-0.15, 0.12, 0.12, s * 0.88, -1.0), (-0.55, 0.1, 0.1, s * 0.88, -1.0), (-0.7, 0.04, 0.04, s * 0.88, -1.0)], 10), "Base", 1)
        P.prop((s * 0.88, -0.75, -1.0), 0.38, 3, blade="Dark", tip="Accent", spinner="Trim", spinner_len=0.1)
    P.obj("Searchlight", lathe([(0.0, 0.0), (0.09, 0.02), (0.11, 0.12), (0.0, 0.13)], 10, "y", (0, 0.92, -1.2)), lambda c, n: "Lamp" if n.y > 0.6 else "Metal")
    P.part("Muzzle", ball((0, 1.06, -1.2), (0.07, 0.04, 0.07), 8, 4), "Lamp", (0, 1.06, -1.2))
    return P


# ================================================================= 2. the news chopper
def speckle(c):
    v = math.sin(c.x * 12.9898 + c.y * 78.233 + c.z * 37.719) * 43758.5453
    return v - math.floor(v)


# ================================================================= 4. the traffic titan
def C_tower():
    """The last boss: the crown of a skyscraper torn loose and flying - an art-deco tower stepping up in three tiers of lit windows, a great
    clock on its face, a golden sunburst crown and a spire with a beacon, antennas blinking red, cannon turrets on its terraces, a broken
    concrete root with four thrusters under it, and a ring of drones turning round it."""
    P = Boss("tower", {"Base": ((0.20, 0.24, 0.34), 0.7), "Belly": ((0.92, 0.90, 0.84), 0.4), "Accent": ((0.62, 0.60, 0.58), 0.3), "Trim": GOLD,
                       "Glass": ((0.35, 0.55, 0.80), 0.9), "Dark": ((0.06, 0.07, 0.09), 0.5), "Glow": ((1.0, 0.15, 0.1), 0.5),
                       "Metal": STEEL, "Lamp": ((1.0, 0.85, 0.50), 0.8)})
    rng = random.Random(4)
    tiers = [(-0.2, 0.75, 1.0), (0.75, 1.45, 0.78), (1.45, 2.05, 0.58)]   # z0, z1, half width
    for (z0, z1, w) in tiers:
        P.obj("Tier", box((0, 0, (z0 + z1) / 2), (w * 2, w * 2, z1 - z0)), "Base", 0, False)
        P.obj("Ledge", box((0, 0, z1 + 0.03), (w * 2 + 0.12, w * 2 + 0.12, 0.06)), "Trim", 0, False)
        cols = max(3, int(w * 2 / 0.3)); rows = max(2, int((z1 - z0 - 0.15) / 0.24))
        for side in range(4):
            R = Matrix.Rotation(math.radians(90 * side), 3, "Z")
            for i in range(cols):
                for j in range(rows):
                    x = -w + (i + 0.5) * (2 * w / cols); z = z0 + 0.1 + (j + 0.5) * ((z1 - z0 - 0.15) / rows)
                    if side == 0 and z0 > 0.5 and z0 < 1.0 and abs(x) < 0.45 and z > 0.85: continue   # the clock
                    lit = rng.random() < 0.5
                    b = box((x, w + 0.012, z), (2 * w / cols * 0.62, 0.03, 0.15))
                    P.obj("Window", xf(b, R), "Lamp" if lit else "Glass", 0, False)
            for i in range(cols + 1):   # vertical piers
                x = -w + i * (2 * w / cols)
                P.obj("Pier", xf(box((x, w + 0.02, (z0 + z1) / 2), (0.04, 0.04, z1 - z0)), R), "Accent", 0, False)
    # the great clock on the middle tier
    cz = 1.12
    P.obj("ClockRim", lathe([(0.0, 0.0), (0.36, 0.0), (0.36, 0.06), (0.0, 0.06)], 24, "y", (0, 0.78, cz)), "Trim")
    P.obj("ClockFace", lathe([(0.0, 0.0), (0.31, 0.0), (0.0, 0.002)], 24, "y", (0, 0.845, cz)), "Belly")
    for k in range(12):
        a = 2 * math.pi * k / 12
        P.obj("Tick", box((math.sin(a) * 0.25, 0.85, cz + math.cos(a) * 0.25), (0.03, 0.02, 0.06), Matrix.Rotation(-a, 3, "Y")), "Dark", 0, False)
    P.obj("HandH", box((0.07, 0.86, cz + 0.05), (0.03, 0.02, 0.16), Matrix.Rotation(math.radians(-55), 3, "Y")), "Dark", 0, False)
    P.obj("HandM", box((-0.02, 0.86, cz + 0.11), (0.02, 0.02, 0.24), Matrix.Rotation(math.radians(10), 3, "Y")), "Dark", 0, False)
    # the art-deco crown: stacked sunburst arches and the spire
    for k in range(4):
        z = 2.1 + k * 0.2; r = 0.5 - k * 0.1
        P.obj("CrownStep", lathe([(r, z), (r, z + 0.12), (r * 0.7, z + 0.2), (0.0, z + 0.2)], 8, "z"), lambda c, n: "Trim" if n.z < 0.6 else "Base", 0, False)
        for a in range(8):
            ax = 2 * math.pi * (a + 0.5) / 8
            P.obj("Sunray", ball((math.cos(ax) * r * 0.93, math.sin(ax) * r * 0.93, z + 0.1), (0.05, 0.05, 0.09), 6, 3), "Lamp")
    P.obj("Spire", pipe([(0, 0, 2.85), (0, 0, 3.8)], [0.07, 0.0], 8), "Metal")
    P.obj("Beacon", ball((0, 0, 3.25), (0.08, 0.08, 0.08), 8, 4), "Glow")
    for sx in (-1, 1):
        for sy in (-1, 1):
            b = Vector((sx * 0.52, sy * 0.52, 2.05))
            P.obj("Antenna", pipe([b, b + Vector((0, 0, 0.55))], [0.025, 0.012], 5), "Metal")
            P.obj("Blink", ball(tuple(b + Vector((0, 0, 0.57))), (0.04, 0.04, 0.04), 6, 3), "Glow")
            # cannon turrets on the lower terrace corners
            t = Vector((sx * 0.86, sy * 0.86, 0.85))
            P.obj("Turret", ball(tuple(t), (0.14, 0.14, 0.1), 10, 5), "Dark")
            P.obj("Gun", pipe([t + Vector((0, 0.05, 0.02)), t + Vector((0, 0.45, 0.04))], [0.04, 0.035], 6), "Metal")
    # the broken concrete root and the thrusters
    root = []
    for k in range(30):
        a = rng.uniform(0, 2 * math.pi); r = rng.uniform(0.1, 1.0)
        root.append((math.cos(a) * r * 0.98, math.sin(a) * r * 0.98, -0.2 - (1.0 - r) * rng.uniform(0.5, 0.9)))
    root += [(sx * 0.98, sy * 0.98, -0.18) for sx in (-1, 1) for sy in (-1, 1)] + [(0, 0, -1.05)]
    P.obj("Root", hull(root), "Accent", 0, False)
    for k in range(10):
        a = rng.uniform(0, 2 * math.pi); r = rng.uniform(0.3, 0.8)
        b = Vector((math.cos(a) * r, math.sin(a) * r, -0.35))
        P.obj("Rebar", pipe([b, b + Vector((rng.uniform(-0.15, 0.15), rng.uniform(-0.15, 0.15), -0.45))], [0.015, 0.015], 4), "Dark")
    for sx in (-1, 1):
        for sy in (-1, 1):
            c = (sx * 0.65, sy * 0.65, -0.3)
            P.obj("Thruster", lathe([(0.0, 0.05), (0.18, 0.05), (0.2, -0.15), (0.16, -0.3), (0.0, -0.3)], 12, "z", c), "Metal")
            P.obj("Flame", cone((c[0], c[1], -0.32), (c[0], c[1], -0.85), 0.13, 8), "Lamp", 0, False)
    # the ring of drones
    for k in range(8):
        a = 2 * math.pi * k / 8
        d = Vector((math.cos(a) * 2.25, math.sin(a) * 2.25, 1.0 + 0.25 * math.sin(a * 2)))
        P.part("SpinDrones", box(tuple(d), (0.22, 0.22, 0.08)), "Dark", (0, 0, 1.0), 0, False)
        P.part("SpinDrones", ball(tuple(d + Vector((0, 0, -0.06))), (0.06, 0.06, 0.05), 6, 3), "Glow", (0, 0, 1.0))
        for sx in (-1, 1):
            for sy in (-1, 1):
                P.part("SpinDrones", lathe([(0.0, 0.0), (0.09, 0.0), (0.09, 0.015), (0.0, 0.015)], 8, "z", tuple(d + Vector((sx * 0.15, sy * 0.15, 0.05)))), "Metal", (0, 0, 1.0), 0, False)
    P.part("Muzzle", ball((0, 1.02, 0.35), (0.08, 0.04, 0.08), 8, 4), "Lamp", (0, 1.02, 0.35))
    return P


# ================================================================= 2026-10-11 round two: the chrome kong (in place of the blimp)
def cape_strip(cx=0.0, cy=-0.55, top=0.95, drop=1.75, R=1.05, depth=0.42):
    """a cape hanging behind the shoulders: a curved two-sided curtain flaring towards the hem."""
    bm = bmesh.new(); cols, rows = 12, 6; grid = []
    for j in range(rows + 1):
        z = top - drop * j / rows; flare = 1.0 + 0.35 * j / rows
        row = []
        for i in range(cols + 1):
            a = math.pi * (0.08 + 0.84 * i / cols)
            x = cx - math.cos(a) * R * flare; y = cy - math.sin(a) * depth * flare - 0.06 * math.sin(i * 1.7) * j / rows
            row.append(bm.verts.new((x, y, z)))
        grid.append(row)
    for j in range(rows):
        for i in range(cols):
            bm.faces.new((grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]))
    bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=0.03)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


# ================================================================= kong (2026-10-13 remake)
# ================================================================= chrome kong's helpers
def kg_vloft(keys, seg=32, sq=1.15):
    """a body round a vertical axis: keys (z, cy, rx, front, back) -> superellipse rings, deeper in front or behind; capped."""
    bm = bmesh.new(); rings = []
    fine = []
    for k0, k1 in zip(keys, keys[1:]):   # three more rings between each pair of keys, so the plates' edges come out clean
        for i in range(4):
            u = i / 4; s = u * u * (3 - 2 * u)
            fine.append(tuple(a + (b - a) * (s if j > 0 else u) for j, (a, b) in enumerate(zip(k0, k1))))
    fine.append(keys[-1])
    for (z, cy, rx, yf, yb) in fine:
        ring = []
        for k in range(seg):
            a = 2 * math.pi * k / seg; ca, sa = math.cos(a), math.sin(a)
            u = math.copysign(abs(ca) ** (1 / sq), ca) * rx
            v = math.copysign(abs(sa) ** (1 / sq), sa) * (yf if sa > 0 else yb)
            ring.append(bm.verts.new((u, cy + v, z)))
        rings.append(ring)
    for r0, r1 in zip(rings, rings[1:]):
        for k in range(seg): bm.faces.new((r0[k], r0[(k + 1) % seg], r1[(k + 1) % seg], r1[k]))
    bm.faces.new(list(reversed(rings[0]))); bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm

def kg_piston(P, a, b, r=0.05, name="Piston", hub=None):
    """a hydraulic ram from a to b: a gunmetal cylinder, a chrome rod, an eye at each end."""
    a, b = Vector(a), Vector(b); m = a + (b - a) * 0.55
    add = (lambda bm, s: P.part(name, bm, s, hub, 0)) if hub else (lambda bm, s: P.obj(name, bm, s, 0))
    add(pipe([a, m], [r, r], 10), "Base")
    add(pipe([m - (b - a) * 0.04, b], [r * 0.55, r * 0.55], 8), "Metal")
    for p in (a, b): add(ball(tuple(p), (r * 1.2, r * 1.2, r * 1.2), 8, 4), "Dark")

def kg_rivets(P, pts, r=0.022, name="Rivet", hub=None):
    for p in pts:
        bm = ball(tuple(p), (r, r, r), 6, 3)
        if hub: P.part(name, bm, "Metal", hub, 0)
        else: P.obj(name, bm, "Metal", 0)

def kg_link(c, t, k, R=0.05, r=0.016):
    """one chain link at c, its long axis along t, every other one turned a quarter about it."""
    t = Vector(t).normalized(); a, b = frame(t)
    if k % 2: a, b = b, -a
    bm = torus(R, r, 0.0, 12, 5)
    for v in bm.verts: v.co.x *= 1.45
    return xf(bm, Matrix((t, a, b)).transposed(), tuple(c))

def kg_envelope_r(y, L=1.3, R=0.5):
    """the blimp's envelope radius at y: a teardrop, fullest a little ahead of the middle."""
    u = (y - 0.12) / (L + (0.12 if y < 0.12 else -0.12))
    return R * max(0.0, 1 - u * u) ** 0.5 * (1.0 if y > 0.12 else (1 - 0.18 * u * u))

KG_CROWN = ["..XXXXXXXXXXXX..", "..X.X.X..X.X.X..", "..XXXXXXXXXXXX..", "..XXXXXXXXXXXX..", "..XXX.XXXX.XXX..", "...X...XX...X..."]


def C_kong():
    """The king of the rooftops in chrome (2026-10-13, remade: "same as the alien bosses - realistic details, scarier, keep the cartoon
    shape"): CHROME KONG, the same colossal crowned robot gorilla, now built like a real silverback made as a real machine. A silverback's
    body - shoulders twice as wide as the hips under great trapezius humps, a barrel chest, a pot belly, short bowed legs and arms far longer
    than them; the skull rises into the bony sagittal crest of an old male, a heavy brow ridge juts over deep-set eyes, the muzzle is pushed
    in under a broad flat nose with flared nostrils. As a machine: chrome armour plates follow the muscles - the silver back and shoulders,
    the deltoids ringed with rivets - while the chest and belly are dark gunmetal like a gorilla's bare chest, with two pectoral plates and
    six belly plates on it, every plate riveted; hydraulic rams work every elbow and knee; red and black cables run bare up the back of his
    neck. His eyes are red visor lamps burning under the brow, slanted down to the nose in a glare; the jaw hangs open in a roar on steel
    fangs, two great canines above and below. A king's touches: a gold crown round his crest, eight points with a red gem at the foot of
    each; a gold chain of office hung across his chest with a medallion set with a red stone.
    He flies HANGING FROM A BILLBOARD BLIMP: above him a small advertising airship - a silver teardrop envelope sewn in gores with a red band
    round the nose, four tail fins in a cross edged in red, on each flank an LED billboard showing his own crown in amber lights - with a
    gunmetal gondola under it, its windows lit, and two ducted propellers on outriggers that spin (PropL, PropR). From the gondola a heavy
    steel cable runs down to a red crane block and a steel hook, and he hangs from the hook by his right hand, legs dangling, swinging his
    left fist at the player (SwayArm). His shots leave from his roaring mouth."""
    P = Boss("kong", {"Base": ((0.20, 0.21, 0.25), 0.6), "Belly": ((0.92, 0.93, 0.95), 0.9), "Accent": ((0.86, 0.10, 0.07), 0.6), "Trim": GOLD,
                      "Glass": ((0.10, 0.22, 0.32), 0.95), "Dark": ((0.05, 0.05, 0.06), 0.4), "Glow": ((1.0, 0.70, 0.15), 0.5),
                      "Metal": ((0.86, 0.88, 0.92), 0.85), "Lamp": ((1.0, 0.08, 0.05), 0.9)})

    # ---- the torso: a silverback's - huge shoulders and traps, a barrel chest, a pot belly, narrow hips
    keys = [(-0.66, 0.0, 0.30, 0.24, 0.24), (-0.58, 0.0, 0.42, 0.32, 0.30), (-0.35, 0.03, 0.54, 0.46, 0.36), (-0.05, 0.02, 0.60, 0.44, 0.40),
            (0.25, 0.0, 0.74, 0.46, 0.44), (0.52, -0.02, 0.86, 0.42, 0.46), (0.74, -0.06, 0.62, 0.32, 0.44), (0.90, -0.04, 0.34, 0.24, 0.30),
            (0.96, -0.02, 0.22, 0.18, 0.20)]
    def torso_paint(c, n):
        front = n.y > 0.25 and (c.x / 0.6) ** 2 + ((c.z + 0.05) / 0.66) ** 2 < 1.0
        if front: return "Dark"                                           # the bare chest and belly, under the plates
        if c.y < -0.05 and (abs(c.z - 0.14) < 0.02 or abs(c.z - 0.42) < 0.02): return "Dark"   # the back's plate seams
        return "Metal"
    P.obj("Torso", kg_vloft(keys), torso_paint, 0)
    def surf(z, a, lift=0.01):   # a point on the torso at height z, angle a round it (0 = right, 90 = front)
        for k0, k1 in zip(keys, keys[1:]):
            if k0[0] <= z <= k1[0]:
                u = (z - k0[0]) / (k1[0] - k0[0]); u = u * u * (3 - 2 * u)
                cy, rx, yf, yb = (k0[i] + (k1[i] - k0[i]) * u for i in (1, 2, 3, 4)); break
        ca, sa = math.cos(a), math.sin(a)
        x = math.copysign(abs(ca) ** (1 / 1.15), ca) * (rx + lift); y = math.copysign(abs(sa) ** (1 / 1.15), sa) * ((yf if sa > 0 else yb) + lift)
        return Vector((x, cy + y, z))
    # rivets in even rows along the back's seams, either side of the spine seam
    kg_rivets(P, [surf(z, math.radians(a)) for z in (0.08, 0.2, 0.36, 0.48) for a in range(-160, -15, 16)], 0.024)
    for k in range(11):   # the spine: a row of gunmetal vertebra plates down the middle of the silver back
        z = -0.5 + 0.12 * k; c = surf(z, math.radians(-90), 0.0)
        P.obj("Spine", box(tuple(c + Vector((0, -0.01, 0))), (0.09, 0.05, 0.08)), "Base", 0, False)
    # two pectoral plates and six belly plates, riveted at their corners
    for s in (1, -1):
        c = Vector((s * 0.3, 0.36, 0.3))
        P.obj("Pec", xf(ball((0, 0, 0), (0.3, 0.14, 0.2), 16, 8), Matrix.Rotation(math.radians(s * 12), 3, "Y"), tuple(c)), "Base", 0)
        kg_rivets(P, [c + Vector((s * dx, 0.12, dz)) for dx, dz in ((-0.18, 0.1), (0.18, 0.08), (0.2, -0.08), (-0.16, -0.11))])
        for row, z in enumerate((-0.04, -0.22, -0.40)):
            c = Vector((s * 0.13, 0.41 + 0.03 * (row == 1), z))
            P.obj("Abs", ball(tuple(c), (0.11, 0.07, 0.075), 12, 6), "Base", 0)
            kg_rivets(P, [c + Vector((s * 0.07, 0.06, 0.04))], 0.016)
    # the deltoids: chrome domes ringed with rivets
    for s in (1, -1):
        c = Vector((s * 0.86, -0.02, 0.58))
        P.obj("Deltoid", ball(tuple(c), (0.3, 0.32, 0.3), 18, 9), lambda q, n: "Dark" if abs(q.z - 0.58) < 0.016 else "Metal", 0)
        kg_rivets(P, [c + Vector((s * 0.24, 0.18 * math.cos(2 * math.pi * k / 10), 0.18 * math.sin(2 * math.pi * k / 10))) for k in range(10)])
    # bare cables up the back of the neck, red and black in turn
    for i, x in enumerate((-0.16, -0.08, 0.0, 0.08, 0.16)):
        P.obj("Cable", pipe(bez((x, -0.14, 0.86), (x * 1.2, -0.2, 0.98), (x, -0.04, 1.02), (x * 0.8, 0.06, 0.96), 6), [0.026] * 7, 6),
              "Accent" if i % 2 else "Dark", 0)
    # the gold chain of office, and its medallion
    pts = bez((-0.58, 0.32, 0.62), (-0.36, 0.56, 0.12), (0.36, 0.56, 0.12), (0.58, 0.32, 0.62), 22)
    for k in range(1, len(pts) - 1):
        P.obj("Chain", kg_link(pts[k], pts[k + 1] - pts[k - 1], k), "Trim", 0)
    P.obj("Medallion", lathe([(0.0, 0.0), (0.14, 0.0), (0.155, 0.02), (0.155, 0.045), (0.125, 0.06), (0.0, 0.06)], 28, "y", (0, 0.5, 0.0)), "Trim")
    P.obj("MedallionStone", ball((0, 0.565, 0.0), (0.06, 0.03, 0.06), 12, 6), "Accent")
    kg_rivets(P, [(0.105 * math.cos(2 * math.pi * k / 8), 0.565, 0.105 * math.sin(2 * math.pi * k / 8)) for k in range(8)], 0.014)

    # ---- the head: forward and low between the shoulders; a crested skull, the brow ridge, a pushed-in muzzle roaring on steel fangs
    P.obj("Skull", ball((0, 0.22, 1.12), (0.38, 0.38, 0.36), 22, 11), "Metal", 0)
    crest = [(x, y, z) for (y, z) in ((0.42, 1.36), (0.1, 1.62), (-0.16, 1.36)) for x in (-0.03, 0.03)] + \
            [(x, y, z) for (y, z) in ((0.3, 1.2), (-0.05, 1.2)) for x in (-0.1, 0.1)]
    P.obj("Crest", hull(crest), "Metal", 0, False)
    P.obj("Face", ball((0, 0.48, 1.0), (0.32, 0.2, 0.28), 18, 9), "Base", 0)
    P.obj("Brow", pipe([(-0.36, 0.5, 1.17), (-0.18, 0.66, 1.16), (0, 0.71, 1.08), (0.18, 0.66, 1.16), (0.36, 0.5, 1.17)],
                       [0.05, 0.09, 0.08, 0.09, 0.05], 12), "Metal", 0)
    for s in (1, -1):
        P.obj("Socket", ball((s * 0.15, 0.62, 1.04), (0.1, 0.05, 0.055), 12, 6), "Dark", 0)
        eye = xf(ball((0, 0, 0), (0.075, 0.03, 0.028), 12, 6), Matrix.Rotation(math.radians(-s * 18), 3, "Y"), (s * 0.15, 0.655, 1.04))
        P.obj("Eye", eye, "Lamp", 0)
        P.obj("Ear", ball((s * 0.37, 0.2, 1.06), (0.05, 0.08, 0.1), 10, 5), "Base", 0)
        P.obj("Nostril", ball((s * 0.06, 0.875, 0.93), (0.045, 0.025, 0.03), 10, 5), "Dark", 0)
        for k in range(4):   # rivets round each cheek plate
            a = math.radians(200 + 35 * k)
            kg_rivets(P, [(s * (0.2 + 0.08 * math.cos(a)), 0.6 + 0.02 * math.sin(a), 0.9 + 0.08 * math.sin(a))], 0.016)
    P.obj("Muzzle_", ball((0, 0.68, 0.9), (0.27, 0.19, 0.16), 18, 9), "Base", 0)
    P.obj("Nose", ball((0, 0.83, 0.96), (0.13, 0.06, 0.07), 14, 7), "Base", 0)
    P.obj("Mouth", ball((0, 0.76, 0.76), (0.19, 0.1, 0.07), 14, 7), "Dark", 0)
    P.obj("Jaw", ball((0, 0.64, 0.66), (0.24, 0.2, 0.09), 16, 8), "Base", 0)
    for s in (1, -1):
        P.obj("Fang", cone((s * 0.13, 0.84, 0.83), (s * 0.12, 0.87, 0.68), 0.035, 8), "Belly", 0)
        P.obj("Fang", cone((s * 0.09, 0.8, 0.69), (s * 0.09, 0.83, 0.79), 0.028, 8), "Belly", 0)
    for k in range(4):
        P.obj("Tooth", box(((k - 1.5) * 0.038, 0.845, 0.8), (0.03, 0.025, 0.04)), "Belly", 0, False)
    # the crown round the crest: a gold band, eight points, a red gem at the foot of each
    P.obj("Crown", lathe([(0.3, 0.0), (0.33, 0.02), (0.33, 0.1), (0.31, 0.12), (0.28, 0.1), (0.28, 0.0)], 32, "z", (0, 0.22, 1.27)), "Trim")
    for k in range(8):
        a = 2 * math.pi * (k + 0.5) / 8; d = Vector((math.sin(a), math.cos(a), 0))
        b = Vector((0, 0.22, 1.37)) + d * 0.32
        P.obj("CrownPoint", cone(tuple(b), tuple(b + d * 0.04 + Vector((0, 0, 0.16))), 0.04, 6), "Trim", 0, False)
        P.obj("CrownGem", ball(tuple(Vector((0, 0.22, 1.33)) + d * 0.335), (0.03, 0.03, 0.03), 8, 4), "Accent", 0)

    # ---- the right arm, raised: he hangs from the hook by it
    P.obj("ArmR", pipe([(0.9, -0.02, 0.62), (0.86, 0.0, 0.92), (0.8, 0.02, 1.22)], [0.21, 0.2, 0.17], 16), "Metal", 0)
    P.obj("ForearmR", pipe([(0.8, 0.02, 1.22), (0.64, 0.04, 1.44), (0.42, 0.06, 1.64)], [0.18, 0.23, 0.14], 16), "Metal", 0)
    P.obj("ElbowR", xf(torus(0.17, 0.035, 0.0, 20, 6), Matrix.Rotation(math.radians(60), 3, "Y"), (0.8, 0.02, 1.22)), "Dark")
    kg_piston(P, (0.98, -0.12, 0.98), (0.66, -0.12, 1.48))
    P.obj("HandR", ball((0.33, 0.06, 1.7), (0.12, 0.12, 0.1), 12, 6), "Metal", 0)
    for k in range(4):   # four fingers curled over the hook's bar
        x = 0.19 + 0.05 * k
        P.obj("FingerR", pipe([(x, 0.15, 1.7), (x, 0.13, 1.82), (x, 0.0, 1.86), (x, -0.07, 1.78)], [0.04, 0.04, 0.038, 0.032], 8), "Metal", 0)

    # ---- the left arm, free: it swings a fist at the player (SwayArm, hinged at the shoulder)
    hub = (-0.86, -0.02, 0.6)
    P.part("SwayArm", pipe([(-0.9, -0.02, 0.52), (-1.04, 0.1, 0.22), (-1.12, 0.26, -0.1)], [0.22, 0.21, 0.18], 16), "Metal", hub, 0)
    P.part("SwayArm", pipe([(-1.12, 0.26, -0.1), (-1.08, 0.52, -0.38), (-0.96, 0.82, -0.6)], [0.19, 0.26, 0.16], 16), "Metal", hub, 0)
    P.part("SwayArm", xf(torus(0.18, 0.035, 0.0, 20, 6), Matrix.Rotation(math.radians(-50), 3, "X"), (-1.12, 0.26, -0.1)), "Dark", hub, 0)
    kg_piston(P, (-1.26, 0.0, 0.16), (-1.2, 0.5, -0.42), name="SwayArm", hub=hub)
    F = Vector((-0.92, 0.96, -0.68))
    P.part("SwayArm", ball(tuple(F), (0.24, 0.21, 0.2), 16, 8), "Metal", hub, 0)
    for k in range(4):   # the knuckles of a gorilla's fist, a gold signet on the second
        c = F + Vector(((k - 1.5) * 0.1, 0.17, 0.06))
        P.part("SwayArm", ball(tuple(c), (0.06, 0.06, 0.065), 10, 5), "Metal", hub, 0)
        P.part("SwayArm", pipe([c + Vector((0, -0.01, -0.08)), c + Vector((0, -0.07, -0.17))], [0.05, 0.045], 8), "Metal", hub, 0)
        if k == 1: P.part("SwayArm", xf(torus(0.055, 0.016, 0.0, 12, 5), Matrix.Rotation(math.radians(90), 3, "Y"), tuple(c + Vector((0, -0.04, -0.03)))), "Trim", hub, 0)
    P.part("SwayArm", pipe([F + Vector((0.2, 0.0, -0.02)), F + Vector((0.22, 0.12, -0.06))], [0.055, 0.045], 8), "Metal", hub, 0)

    # ---- the legs: short and bowed, dangling; a ram behind each knee, gorilla feet with the big toe set apart
    for s in (1, -1):
        P.obj("Thigh", pipe([(s * 0.3, 0.02, -0.5), (s * 0.36, 0.14, -0.72), (s * 0.38, 0.26, -0.92)], [0.2, 0.19, 0.15], 16), "Metal", 0)
        P.obj("Knee", ball((s * 0.38, 0.32, -0.93), (0.12, 0.08, 0.11), 12, 6), "Base", 0)
        P.obj("Shin", pipe([(s * 0.38, 0.26, -0.92), (s * 0.36, 0.18, -1.12), (s * 0.33, 0.1, -1.3)], [0.15, 0.15, 0.11], 14), "Metal", 0)
        kg_piston(P, (s * 0.38, -0.12, -0.7), (s * 0.36, -0.03, -1.14), 0.04)
        foot = Matrix.Rotation(math.radians(-40), 3, "X")
        P.obj("Foot", xf(ball((0, 0.1, 0), (0.17, 0.25, 0.1), 14, 7), foot, (s * 0.34, 0.08, -1.36)), "Base", 0)
        for k in range(4):
            x = s * (0.3 + 0.06 * k)
            P.obj("Toe", xf(ball((0, 0.33, 0), (0.042, 0.07, 0.045), 8, 4), foot, (x, 0.08, -1.36)), "Metal", 0)
        P.obj("BigToe", pipe([(s * 0.22, 0.12, -1.38), (s * 0.15, 0.24, -1.5)], [0.05, 0.045], 8), "Metal", 0)

    # ---- the hook, the block and the cable
    HX = 0.25
    P.obj("Hook", pipe(bez((HX + 0.08, 0.06, 2.0), (HX + 0.1, 0.06, 1.72), (HX - 0.2, 0.06, 1.72), (HX - 0.17, 0.06, 1.9), 10),
                       [0.045] * 10 + [0.02], 10), "Metal", 0)
    P.obj("HookShank", pipe([(HX + 0.08, 0.06, 2.0), (HX + 0.08, 0.06, 2.1)], [0.05, 0.05], 10), "Metal", 0)
    P.obj("Block", box((HX + 0.08, 0.06, 2.2), (0.2, 0.12, 0.2)), "Accent", 0, False)
    for s in (1, -1):
        P.obj("Cheek", box((HX + 0.08, 0.06 + s * 0.07, 2.2), (0.16, 0.02, 0.16)), "Metal", 0, False)
        P.obj("Pin", ball((HX + 0.08, 0.06 + s * 0.085, 2.2), (0.03, 0.02, 0.03), 8, 4), "Dark", 0)
    P.obj("Cable", pipe([(HX + 0.08, 0.06, 2.3), (HX + 0.08, 0.04, 2.56)], [0.025, 0.025], 8), "Dark", 0)

    # ---- the billboard blimp
    BZ = 3.1; L = 1.3; R = 0.5; seg = 36
    ys = [-L + 2 * L * i / 24 for i in range(25)]
    prof = [(kg_envelope_r(y, L, R), y) for y in ys]
    prof[0] = (0.0, prof[0][1]); prof[-1] = (0.0, prof[-1][1])
    def env_paint(c, n):
        a = math.degrees(math.atan2(c.z - BZ, c.x - HX)) % 45
        if 0.88 < c.y < 0.98: return "Accent"            # the red band round the nose
        if a < 1.6 or a > 43.4: return "Dark"            # the seams between the gores
        return "Metal"
    P.obj("Envelope", lathe(prof, seg, "y", (HX, 0, BZ)), env_paint, 0)
    P.obj("NoseCap", ball((HX, L - 0.02, BZ), (0.06, 0.03, 0.06), 10, 5), "Base", 0)
    # a curved LED billboard on each flank showing his crown in amber lights
    cols, rows = 16, 6; y0, y1 = -0.62, 0.62; a0 = math.radians(24)
    for s in (1, -1):
        bm = bmesh.new()
        def V(i, j, lift=0.022):
            y = y0 + (y1 - y0) * i / cols; a = -a0 + 2 * a0 * j / rows
            r = kg_envelope_r(y, L, R) + lift
            return bm.verts.new((HX + s * r * math.cos(a), y, BZ + r * math.sin(a)))
        grid = [[V(i, j) for j in range(rows + 1)] for i in range(cols + 1)]
        for i in range(cols):
            for j in range(rows):
                f = bm.faces.new((grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1]))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        for f in bm.faces:
            if (f.calc_center_median().x - HX) * f.normal.x < 0: f.normal_flip()
        def led(c, n, s=s):
            i = int((c.y - y0) / (y1 - y0) * cols); a = math.atan2(c.z - BZ, (c.x - HX) * s)
            j = int((a + a0) / (2 * a0) * rows)
            i, j = min(max(i, 0), cols - 1), min(max(j, 0), rows - 1)
            return "Glow" if KG_CROWN[j][i] == "X" else "Dark"
        P.obj("Billboard", bm, led, 0, False)
        P.obj("BillboardFrame", pipe([(HX + s * (kg_envelope_r(y, L, R) + 0.03) * math.cos(a0), y, BZ + (kg_envelope_r(y, L, R) + 0.03) * math.sin(a0))
                                      for y in [y0 + (y1 - y0) * i / 8 for i in range(9)]], [0.018] * 9, 6), "Base", 0)
        P.obj("BillboardFrame", pipe([(HX + s * (kg_envelope_r(y, L, R) + 0.03) * math.cos(a0), y, BZ - (kg_envelope_r(y, L, R) + 0.03) * math.sin(a0))
                                      for y in [y0 + (y1 - y0) * i / 8 for i in range(9)]], [0.018] * 9, 6), "Base", 0)
    # four tail fins in a cross, edged in red
    for k in range(4):
        a = math.pi / 2 * k; d = Vector((math.cos(a), 0, math.sin(a)))
        pts = []
        for (y, out) in ((-0.62, 0.0), (-1.12, 0.0), (-0.98, 0.42), (-1.2, 0.42)):
            base = kg_envelope_r(y, L, R) * 0.92 + out
            for t in (-0.018, 0.018):
                side = Vector((-d.z, 0, d.x)) * t
                pts.append(tuple(Vector((HX, y, BZ)) + d * base + side))
        P.obj("Fin", hull(pts), lambda c, n, d=d: "Accent" if (Vector((c.x - HX, 0, c.z - BZ))).length > kg_envelope_r(c.y, L, R) * 0.92 + 0.34 else "Metal", 0, False)
    # the gondola under the envelope: lit windows, a red stripe, struts up to the envelope
    GZ = BZ - R - 0.08
    rings = [(-0.38, 0.06, 0.05, HX, GZ), (-0.3, 0.15, 0.11, HX, GZ), (0.25, 0.17, 0.13, HX, GZ), (0.42, 0.13, 0.1, HX, GZ), (0.5, 0.05, 0.05, HX, GZ)]
    def gondola_paint(c, n):
        if abs(c.z - GZ - 0.03) < 0.035 and (abs(n.x) > 0.6 or n.y > 0.6): return "Glass"
        if abs(c.z - GZ + 0.05) < 0.015: return "Accent"
        return "Base"
    P.obj("Gondola", loft(rings, 20, sq=2.2), gondola_paint, 0)
    for y in (-0.2, 0.3):
        for s in (1, -1):
            P.obj("Strut", pipe([(HX + s * 0.1, y, GZ + 0.1), (HX + s * 0.18, y, BZ - kg_envelope_r(y, L, R) * 0.9)], [0.015, 0.015], 6), "Dark", 0)
    # two ducted propellers out on outriggers behind the gondola
    for s in (1, -1):
        hubp = (HX + s * 0.48, -0.24, GZ + 0.04)
        P.obj("Outrigger", pipe([(HX + s * 0.14, -0.2, GZ), (hubp[0] - s * 0.14, -0.24, hubp[2])], [0.028, 0.028], 8), "Base", 0)
        P.obj("Duct", xf(lathe([(0.15, -0.09), (0.18, -0.08), (0.185, 0.04), (0.165, 0.08), (0.15, 0.06)], 24, "y"), None, hubp),
              lambda c, n: "Accent" if c.y > -0.18 else "Base", 0)
        P.obj("Nacelle", pipe([(hubp[0], -0.3, hubp[2]), (hubp[0], -0.42, hubp[2])], [0.05, 0.03], 10), "Base", 0)
        name = "PropR" if s > 0 else "PropL"
        P.part(name, cone((hubp[0], -0.22, hubp[2]), (hubp[0], -0.14, hubp[2]), 0.04, 10), "Metal", hubp, 0)
        for k in range(3):
            a = 2 * math.pi * k / 3 + (0.3 if s > 0 else 0)
            m = Matrix.Rotation(a, 3, "Y") @ Matrix.Rotation(math.radians(20), 3, "X")
            P.part(name, xf(box((0.075, 0, 0), (0.13, 0.008, 0.035)), m, (hubp[0], -0.23, hubp[2])), "Dark", hubp, 0)

    P.part("Muzzle", ball((0, 0.8, 0.76), (0.04, 0.025, 0.03), 8, 4), "Lamp", (0, 0.8, 0.76))
    return P



# ================================================================= chopper (2026-10-13 remake)
# ================================================================= the news chopper: helpers
# the cabin pod, nose to tailcone: (y, half width, half height, centre z); its sections are superellipses
CH_KEYS = [(1.58, 0.04, 0.04, -0.12), (1.52, 0.20, 0.19, -0.12), (1.42, 0.31, 0.29, -0.10), (1.25, 0.41, 0.37, -0.07),
           (1.0, 0.48, 0.42, -0.03), (0.7, 0.52, 0.45, 0.0), (0.3, 0.53, 0.45, 0.0), (-0.1, 0.52, 0.44, 0.0), (-0.45, 0.47, 0.40, 0.04),
           (-0.7, 0.36, 0.32, 0.09), (-0.85, 0.24, 0.24, 0.13), (-0.94, 0.15, 0.16, 0.15)]
CH_SQ = 1.25

def ch_sec(y):
    """the cabin's half width, half height and centre z at y (smoothly between the keys)."""
    ks = CH_KEYS
    if y >= ks[0][0]: return ks[0][1:]
    for k0, k1 in zip(ks, ks[1:]):
        if k1[0] <= y <= k0[0]:
            t = (k0[0] - y) / (k0[0] - k1[0]); t = t * t * (3 - 2 * t)
            return tuple(u + (v - u) * t for u, v in zip(k0[1:], k1[1:]))
    return ks[-1][1:]

def ch_raw(y, th):
    a, b, cz = ch_sec(y); ca, sa = math.cos(th), math.sin(th)
    return Vector((a * math.copysign(abs(ca) ** (1.0 / CH_SQ), ca), y, cz + b * math.copysign(abs(sa) ** (1.0 / CH_SQ), sa)))

def ch_pt(y, th, lift=0.0):
    """a point on the cabin's skin (th: 0 = right side, 90 deg = top, -90 deg = belly), lifted along the outward normal."""
    p = ch_raw(y, th)
    if lift == 0.0: return p
    e = 0.002
    dy = ch_raw(y + e, th) - ch_raw(y - e, th); dt = ch_raw(y, th + e) - ch_raw(y, th - e)
    n = dt.cross(dy)
    if n.length < 1e-9: n = Vector((math.cos(th), 0, math.sin(th)))
    n.normalize()
    if n.dot(p - Vector((0, y, ch_sec(y)[2]))) < 0: n = -n
    return p + n * lift

def ch_cabin(step=0.03, seg=72):
    ys, y = [], CH_KEYS[0][0]
    while y > CH_KEYS[-1][0]: ys.append(y); y -= step
    ys.append(CH_KEYS[-1][0])
    bm = bmesh.new(); rings = []
    for y in ys:
        rings.append([bm.verts.new(ch_raw(y, 2 * math.pi * i / seg)) for i in range(seg)])
    for r0, r1 in zip(rings, rings[1:]):
        for i in range(seg):
            j = (i + 1) % seg; bm.faces.new((r0[i], r0[j], r1[j], r1[i]))
    tip = bm.verts.new((0, CH_KEYS[0][0] + 0.012, CH_KEYS[0][3]))
    for i in range(seg): bm.faces.new((tip, rings[0][(i + 1) % seg], rings[0][i]))
    bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm

def ch_side(th, s):
    """the angle th on the right side (s=1) or mirrored onto the left (s=-1)."""
    return th if s > 0 else math.pi - th

def ch_patch(polys, lift, s):
    """flat decals lying on the cabin's skin: polys are outlines in (y, th) on the right side, mirrored for s=-1; each is a fan from its
    centre, cut in rings so it follows the curve."""
    bm = bmesh.new()
    for poly in polys:
        cy = sum(p[0] for p in poly) / len(poly); ct = sum(p[1] for p in poly) / len(poly)
        R = 3
        def at(k, p):
            f = k / R
            return ch_pt(cy + (p[0] - cy) * f, ch_side(ct + (p[1] - ct) * f, s), lift)
        centre = bm.verts.new(at(0, poly[0]))
        rings = [[bm.verts.new(at(k, p)) for p in poly] for k in range(1, R + 1)]
        n = len(poly)
        def face(vs):
            f = bm.faces.new(vs)
            c = sum((v.co for v in vs), Vector()) / len(vs)
            out = c - Vector((0, c.y, ch_sec(c.y)[2]))
            f.normal_update()
            if f.normal.dot(out) < 0: f.normal_flip()
        for i in range(n):
            j = (i + 1) % n
            face((centre, rings[0][i], rings[0][j]))
            for k in range(R - 1):
                face((rings[k][i], rings[k + 1][i], rings[k + 1][j], rings[k][j]))
    return bm

def ch_band(fa, fb, n, lift, s):
    """a strip lying on the skin between two curves fa(t), fb(t) -> (y, th), t from 0 to 1."""
    polys = []
    for i in range(n):
        t0, t1 = i / n, (i + 1) / n
        polys.append([fa(t0), fa(t1), fb(t1), fb(t0)])
    return ch_patch(polys, lift, s)

def ch_blade(r0, r1, chord, thick, twist=8.0):
    """one main rotor blade along +X from r0 to r1 (an airfoil, the leading edge toward -Y as it turns), twisted toward the root."""
    secs = []
    for k in range(9):
        x = r0 + (r1 - r0) * k / 8
        bm_sec = airfoil(chord * 0.3, -chord * 0.7, thick, 0.0)
        tw = math.radians(twist * (1 - k / 8))
        secs.append((x, [(u * math.cos(tw) - v * math.sin(tw), u * math.sin(tw) + v * math.cos(tw)) for (u, v) in bm_sec]))
    return sweep(secs, "x")


# ================================================================= 2. the news chopper
def C_chopper():
    """The news chopper turned gunship (2026-10-13, remade: "same as the alien bosses - realistic details, scarier, keep the cartoon shape"):
    the same black-and-red TV helicopter with a shark mouth, rocket pods and a chin gun, now built like a real light helicopter of the
    AS350 / Bell 206 kind. A bulbous cabin pod - a big framed windshield running up into the roof windows, a centre post, a pillar
    behind it and two framed door windows a side - narrowing into a slim tail boom; on top an engine fairing with seamed access panels
    and their latches, a grilled air intake each side and a hot exhaust glowing red at the back, a red anti-collision beacon; the tail has
    a horizontal stabiliser with angled red end plates, a swept fin over a ventral fin and tail skid, and the tail rotor in its gearbox
    on the left of the fin; a drive-shaft cover runs along the boom, its joints ringed with rivets. A real main rotor head: the mast, the
    swashplate with three pitch links up to the blade grips, a three-arm starflex hub under a red cap, and three twisted blades with
    yellow tip caps. Landing skids on two bent cross tubes, upturned at the front. The livery is a TV station's, done evenly: black above,
    grey below, a red stripe with a yellow pinstripe from the nose down the flank, an ON AIR panel with five lamps on each rear door and the
    channel's badge - a white disc in a red ring with a black lightning bolt - on each side of the tailcone. Under the nose on the right a
    gyro-stabilised camera ball on its yoke, its big lens glinting; under the left a searchlight. The menace is painted on: a shark's
    grin wrapped round the chin, red-lipped, black inside with a red glow deep in it and rows of white teeth, and above each mouth corner a
    glaring eye with a red-hot iris and a slit pupil under a heavy black brow slanting down to the nose. Its guns: a chin turret with a
    three-barrel gatling (his shots leave from it) and a weapons beam across the cabin floor carrying a seven-tube rocket pod each side.
    It flies as a real helicopter does: the main rotor spins as a blur over it (Rotor) and the tail rotor beside the fin (TailRotor),
    and the whole machine leans eight degrees nose-down, the way a helicopter flies when it is charging forward at speed."""
    P = Boss("chopper", {"Base": ((0.07, 0.075, 0.09), 0.62), "Belly": ((0.62, 0.64, 0.68), 0.5), "Accent": ((0.80, 0.07, 0.06), 0.6),
                         "Trim": TAXI, "Glass": ((0.06, 0.10, 0.15), 0.95), "Dark": ((0.02, 0.02, 0.025), 0.45),
                         "Glow": ((1.0, 0.16, 0.08), 0.5), "Metal": STEEL, "Lamp": ((0.85, 0.95, 1.0), 0.8)})
    W = (0.86, 0.87, 0.88)   # the white of the teeth, the eyes and the badge: the Belly slot is the grey underside
    deg = math.radians

    # ---- the cabin pod: windshield and roof windows over the nose, two door windows a side, the stripe, a grey belly
    def cabin_paint(c, n):
        a, b, cz = ch_sec(c.y)
        th = math.degrees(math.atan2((c.z - cz) / b, abs(c.x) / a))     # the angle round the pod, the same on both sides
        if c.y > 0.66 and th > -4 + max(0.0, c.y - 0.95) * 70:          # the windshield and the roof windows, over a painted chin
            if abs(c.x) < 0.022 and th > 30 and c.y < 1.45: return "Dark"   # the centre post
            if abs(c.y - 1.0) < 0.018 and th > 55: return "Dark"        # the roof-window frame
            return "Glass"
        if 0.60 < c.y <= 0.66 and th > -4: return "Dark"                # the pillar behind the windshield
        if c.y > 0.95 and -4 + (c.y - 0.95) * 70 - 3.5 < th <= -4 + (c.y - 0.95) * 70: return "Dark"   # the windshield's lower frame
        if -0.46 < c.y < 0.58 and 6 < th < 50:                          # the door windows
            if abs(c.y - 0.08) < 0.03 or th < 9 or th > 47 or c.y < -0.43 or c.y > 0.55: return "Dark"
            return "Glass"
        if abs(c.y - 0.08) < 0.008 and -50 < th < 6: return "Dark"      # the door seam below the windows
        if c.y < 0.66 and -15 < th < -5: return "Accent"                # the stripe
        if c.y < 0.66 and -20 < th < -17: return "Trim"                 # its pinstripe
        if th < -55: return "Belly"
        return "Base"
    P.obj("Cabin", ch_cabin(), cabin_paint)
    # the stripe carried on under the windshield to the nose, as a band on the skin
    for s in (1, -1):
        P.obj("NoseStripe", ch_band(lambda t: (0.66 + 0.4 * t, deg(-5) - deg(19) * t ** 2), lambda t: (0.66 + 0.4 * t, deg(-15) - deg(19) * t ** 2), 10, 0.004, s), "Accent", 0, False)

    # ---- the shark's grin round the chin: red lips, black inside with a red glow deep in it, white teeth
    def up(t, d=0.0): return (1.02 + 0.535 * t ** 0.8 + d * 0.6, deg(-27 - 63 * t ** 1.6) + d)
    def lo(t, d=0.0): return (1.02 + 0.34 * t - d * 0.6, deg(-27 - 63 * t ** 0.7) - d)
    for s in (1, -1):
        P.obj("Lips", ch_band(lambda t: up(t, 0.035), lambda t: lo(t, 0.035), 14, 0.005, s), "Accent", 0, False)
        P.obj("Mouth", ch_band(lambda t: up(t), lambda t: lo(t), 14, 0.009, s), "Dark", 0, False)
        P.obj("Throat", ch_band(lambda t: tuple(u + (v - u) * 0.38 for u, v in zip(up(0.15 + 0.85 * t), lo(0.15 + 0.85 * t))),
                                lambda t: tuple(u + (v - u) * 0.62 for u, v in zip(up(0.15 + 0.85 * t), lo(0.15 + 0.85 * t))), 10, 0.011, s), "Glow", 0, False)
        teeth = []
        for k in range(7):   # top teeth hang from the upper lip, the bottom ones stand on the lower lip between them
            t0, t1 = 0.07 + k * 0.133, 0.07 + k * 0.133 + 0.115
            tm = (t0 + t1) * 0.5; a, b = up(t0), up(t1); m = up(tm); l = lo(tm)
            teeth.append([a, b, tuple(u + (v - u) * 0.66 for u, v in zip(m, l))])
            if k < 6:
                u0, u1 = tm + 0.015, tm + 0.12
                a, b = lo(u0), lo(u1); m = lo((u0 + u1) * 0.5); l = up((u0 + u1) * 0.5)
                teeth.append([b, a, tuple(u + (v - u) * 0.5 for u, v in zip(m, l))])
        P.obj("Teeth", ch_patch(teeth, 0.014, s), "Lamp", 0, False)

    # ---- the glaring eyes above the mouth corners, under heavy brows slanting down to the nose
    for s in (1, -1):
        ey, et = 1.36, deg(4)
        def E(du, dv): return (ey + du, et + dv / 0.4)
        almond = [E(0.15 * math.cos(a), (0.055 if math.sin(a) > 0 else 0.045) * math.sin(a) - 0.02 * math.cos(a)) for a in [2 * math.pi * k / 20 for k in range(20)]]
        P.obj("EyeWhite", ch_patch([almond], 0.008, s), "Lamp", 0, False)
        iris = [E(0.05 + 0.045 * math.cos(a), -0.005 + 0.045 * math.sin(a)) for a in [2 * math.pi * k / 14 for k in range(14)]]
        P.obj("Iris", ch_patch([iris], 0.011, s), "Glow", 0, False)
        pupil = [E(0.05 + 0.012 * math.cos(a), -0.005 + 0.038 * math.sin(a)) for a in [2 * math.pi * k / 10 for k in range(10)]]
        P.obj("Pupil", ch_patch([pupil], 0.014, s), "Dark", 0, False)
        lid = [E(-0.16, 0.07), E(0.17, 0.0), E(0.17, 0.035), E(-0.16, 0.115)]      # the brow: high at the back, low over the nose
        P.obj("Brow", ch_patch([lid], 0.016, s), "Dark", 0, False)
        under = [E(-0.14, -0.05), E(0.12, -0.06), E(0.12, -0.075), E(-0.14, -0.065)]
        P.obj("EyeLine", ch_patch([under], 0.009, s), "Dark", 0, False)

    # ---- livery: an ON AIR panel on each rear door and the channel's badge on the tailcone
    for s in (1, -1):
        P.obj("OnAir", ch_patch([[(-0.08, deg(-26)), (-0.42, deg(-26)), (-0.42, deg(-40)), (-0.08, deg(-40))]], 0.006, s), "Dark", 0, False)
        P.obj("OnAirLamp", ch_patch([[(-0.11 - 0.065 * k, deg(-28.5)), (-0.16 - 0.065 * k, deg(-28.5)), (-0.16 - 0.065 * k, deg(-37.5)), (-0.11 - 0.065 * k, deg(-37.5))]
                                     for k in range(5)], 0.009, s), "Glow", 0, False)
        by, bt = -0.6, deg(8)
        def Bd(r, k=24): return [(by + r * math.cos(a), bt + r * math.sin(a) / 0.42) for a in [2 * math.pi * i / k for i in range(k)]]
        P.obj("BadgeRing", ch_patch([Bd(0.13)], 0.006, s), "Accent", 0, False)
        P.obj("Badge", ch_patch([Bd(0.1)], 0.009, s), "Lamp", 0, False)
        bolt = [(-0.04, 0.09), (0.03, 0.09), (0.0, 0.015), (0.045, 0.015), (-0.035, -0.095), (-0.005, -0.01), (-0.05, -0.01)]
        P.obj("BadgeBolt", ch_patch([[(by + u * (1 if s > 0 else -1) * -1, bt + v / 0.42) for (u, v) in bolt]], 0.012, s), "Dark", 0, False)

    # ---- the engine fairing on top: seamed access panels with latches, grilled intakes, the hot exhaust, the beacon
    cowl_keys = [(0.5, 0.05, 0.03, 0, 0.40), (0.42, 0.24, 0.08, 0, 0.44), (0.3, 0.3, 0.12, 0, 0.47), (-0.6, 0.3, 0.13, 0, 0.49),
                 (-0.9, 0.22, 0.1, 0, 0.42), (-1.06, 0.06, 0.04, 0, 0.32)]
    def cowl_paint(c, n):
        if abs(n.x) > 0.35:
            for (y0, y1) in ((-0.38, 0.06), (-0.86, -0.46)):
                if y0 - 0.012 < c.y < y1 + 0.012 and 0.43 < c.z < 0.58:
                    if c.y < y0 + 0.012 or c.y > y1 - 0.012 or c.z < 0.445 or c.z > 0.565: return "Dark"
        if abs(c.x) < 0.012 and n.z > 0.5: return "Dark"   # the seam down the top
        return "Base"
    P.obj("Cowl", loft(fine(cowl_keys, 0.03), 32, sq=1.8), cowl_paint, 0)
    for s in (1, -1):
        for y in (-0.16, -0.64):   # two latches on each access panel
            for z in (0.47, 0.54):
                P.obj("Latch", box((s * 0.302, y - 0.04, z), (0.012, 0.05, 0.022)), "Metal", 0, False)
        # the intake: a recessed grille of five slats in a frame
        P.obj("Intake", box((s * 0.29, 0.22, 0.5), (0.03, 0.2, 0.11)), "Dark", 0, False)
        P.obj("IntakeFrame", box((s * 0.3, 0.22, 0.56), (0.02, 0.22, 0.015)), "Metal", 0, False)
        P.obj("IntakeFrame", box((s * 0.3, 0.22, 0.44), (0.02, 0.22, 0.015)), "Metal", 0, False)
        for k in range(5):
            P.obj("IntakeSlat", box((s * 0.305, 0.14 + 0.04 * k, 0.5), (0.012, 0.012, 0.11)), "Metal", 0, False)
    P.obj("Exhaust", pipe([(0.12, -0.78, 0.5), (0.125, -0.98, 0.53), (0.13, -1.1, 0.57)], [0.075, 0.08, 0.085], 14, cap=False), "Metal")
    P.obj("ExhaustMouth", xf(torus(0.07, 0.015, 0.0, 14, 4), Matrix.Rotation(deg(70), 3, "X"), (0.13, -1.1, 0.57)), "Dark")
    P.obj("ExhaustHeat", xf(ball((0, 0, 0), (0.065, 0.065, 0.015), 12, 4), Matrix.Rotation(deg(70), 3, "X"), (0.13, -1.09, 0.565)), "Glow")
    P.obj("Beacon", ball((0, -0.75, 0.6), (0.04, 0.05, 0.035), 10, 5), "Glow")
    P.obj("BeaconBase", lathe([(0.0, 0.0), (0.05, 0.0), (0.045, 0.03), (0.0, 0.03)], 10, "z", (0, -0.75, 0.56)), "Metal")

    # ---- the tail boom, its shaft cover and riveted joints
    P.obj("Boom", loft(fine([(-0.8, 0.17, 0.17, 0, 0.17), (-1.6, 0.11, 0.11, 0, 0.24), (-2.55, 0.075, 0.075, 0, 0.29), (-2.78, 0.06, 0.06, 0, 0.3)], 0.05), 20),
          lambda c, n: "Dark" if any(abs(c.y - y) < 0.012 for y in (-1.1, -1.6, -2.1)) else ("Accent" if -0.06 < c.z - (0.17 + (-0.8 - c.y) * 0.068) < 0.0 and abs(n.x) > 0.5 else ("Belly" if n.z < -0.6 else "Base")))
    P.obj("ShaftCover", loft(fine([(-1.0, 0.05, 0.03, 0, 0.33), (-2.45, 0.04, 0.025, 0, 0.36)], 0.1), 10, sq=1.5), "Base")
    for y in (-1.1, -1.6, -2.1):
        r = 0.17 - (-0.8 - y) * 0.09 * 0.55 + 0.004; cz = 0.17 + (-0.8 - y) * 0.068
        for k in range(8):
            a = deg(-10 + 200 * k / 7)
            P.obj("Rivet", ball((r * math.cos(a), y, cz + r * math.sin(a)), (0.012, 0.012, 0.012), 6, 3), "Metal")
    P.obj("BoomAntenna", hull([(0, -1.45, 0.36), (0, -1.6, 0.36), (0, -1.62, 0.5), (0.008, -1.56, 0.42), (-0.008, -1.56, 0.42)]), "Dark", 0, False)

    # ---- tail: the stabiliser with angled end plates, the swept fin, the ventral fin and skid, the tail rotor gearbox
    P.obj("Stab", sweep([(x, airfoil(-1.98, -2.2, 0.03, 0.27)) for x in (-0.48, 0.48)], "x"), lambda c, n: "Accent" if abs(c.x) > 0.38 else "Base", 0, False)
    for s in (1, -1):
        plate = hull([(s * 0.48, -1.96, 0.18), (s * 0.48, -2.22, 0.18), (s * 0.52, -2.26, 0.42), (s * 0.52, -2.08, 0.42),
                      (s * 0.5, -2.0, 0.18), (s * 0.5, -2.22, 0.2)])
        P.obj("EndPlate", plate, "Accent", 0, False)
        P.obj("NavLight", ball((s * 0.52, -2.08, 0.43), (0.022, 0.022, 0.022), 6, 3), "Glow" if s < 0 else "Lamp")
    P.obj("Fin", sweep([(z, airfoil(-2.45 - (z - 0.28) * 0.45, -2.78 - (z - 0.28) * 0.12, 0.05 - (z - 0.28) * 0.03, 0.0)) for z in (0.28, 0.6, 0.98)], "z"),
          lambda c, n: "Accent" if c.z > 0.82 else "Base", 0, False)
    P.obj("VentralFin", sweep([(z, airfoil(-2.5 + (0.28 - z) * 0.4, -2.75, 0.04, 0.0)) for z in (0.28, -0.02)], "z"), "Base", 0, False)
    P.obj("TailSkid", pipe([(0, -2.62, 0.0), (0, -2.75, -0.06), (0, -2.85, -0.04)], [0.015, 0.015, 0.012], 6), "Metal")
    P.obj("Strobe", ball((0, -2.85, 0.31), (0.02, 0.025, 0.02), 6, 3), "Lamp")
    P.obj("Gearbox", ball((-0.06, -2.62, 0.52), (0.06, 0.09, 0.07), 10, 5), "Metal")
    P.obj("GearboxCap", lathe([(0.0, 0.0), (0.035, 0.0), (0.03, 0.05), (0.0, 0.06)], 10, "y", (0, 0, 0)), "Metal")
    gc = P.parts[-1]; gc.data.transform(Matrix.Translation((-0.11, -2.62, 0.52)) @ Matrix.Rotation(deg(90), 4, "Z"))
    th = Vector((-0.18, -2.62, 0.52))   # the tail rotor hub, on the left of the fin
    for k in (0, 1):
        sgn = 1 if k == 0 else -1
        bl = box((0, 0, sgn * 0.17), (0.02, 0.07, 0.3)); xf(bl, Matrix.Rotation(deg(sgn * 8), 3, "Z"), tuple(th))
        P.part("TailRotor", bl, lambda c, n: "Trim" if abs(c.z - th.z) > 0.26 else "Dark", tuple(th), 0, False)
    P.part("TailRotor", lathe([(0.0, -0.04), (0.04, -0.03), (0.04, 0.02), (0.0, 0.04)], 10, "x", tuple(th)), "Accent", tuple(th))

    # ---- the main rotor: mast and swashplate on the body; hub, links, grips and three blades turn (Rotor)
    H = Vector((0, -0.05, 0.86))
    P.obj("Mast", pipe([(0, -0.05, 0.55), (0, -0.05, 0.86)], [0.05, 0.045], 12), "Metal")
    P.obj("Swash", lathe([(0.0, 0.0), (0.13, 0.0), (0.13, 0.03), (0.0, 0.03)], 20, "z", (0, -0.05, 0.68)), "Metal")
    P.obj("SwashLink", pipe([(0.1, -0.05, 0.6), (0.11, -0.05, 0.68)], [0.012, 0.012], 5), "Dark")
    P.obj("SwashLink", pipe([(-0.1, -0.05, 0.6), (-0.11, -0.05, 0.68)], [0.012, 0.012], 5), "Dark")
    P.part("Rotor", lathe([(0.0, 0.0), (0.115, 0.0), (0.115, 0.025), (0.0, 0.025)], 20, "z", (0, -0.05, 0.715)), "Metal", tuple(H))
    for k in range(3):
        R = Matrix.Rotation(2 * math.pi * k / 3 + deg(30), 3, "Z")
        def put(bm):
            for v in bm.verts: v.co = H + R @ (v.co - H)
            return bm
        P.part("Rotor", put(box((0.17, -0.05, 0.86), (0.26, 0.11, 0.04))), "Dark", tuple(H), 0, False)              # the starflex arm
        P.part("Rotor", put(box((0.36, -0.05, 0.865), (0.16, 0.12, 0.07))), "Metal", tuple(H), 0, False)             # the blade grip
        P.part("Rotor", put(box((0.36, -0.12, 0.83), (0.06, 0.04, 0.03))), "Metal", tuple(H), 0, False)              # its pitch horn
        P.part("Rotor", put(pipe([(0.33, -0.13, 0.73), (0.36, -0.12, 0.82)], [0.011, 0.011], 5)), "Dark", tuple(H))  # the pitch link
        bl = ch_blade(0.42, 1.68, 0.17, 0.03)
        for v in bl.verts: v.co = Vector((v.co.x, v.co.y - 0.05, v.co.z + 0.865 + (v.co.x - 0.42) * 0.025))
        P.part("Rotor", put(bl), lambda c, n: "Trim" if (c - H).length > 1.54 else ("Accent" if abs((c - H).length - 1.3) < 0.03 else "Dark"), tuple(H), 0, False)
    P.part("Rotor", ball(tuple(H + Vector((0, 0, 0.05))), (0.11, 0.11, 0.08), 14, 6), "Accent", tuple(H))

    # ---- the skids on two bent cross tubes, upturned at the front
    for y in (0.6, -0.35):
        for s in (1, -1):
            P.obj("CrossTube", pipe(bez((s * 0.25, y, -0.36), (s * 0.45, y, -0.4), (s * 0.55, y, -0.55), (s * 0.56, y, -0.72), 6), [0.03] * 7, 8), "Metal")
    for s in (1, -1):
        P.obj("Skid", pipe([(s * 0.56, -0.62, -0.735), (s * 0.56, 0.9, -0.735)] + bez((s * 0.56, 0.9, -0.735), (s * 0.56, 1.1, -0.735), (s * 0.56, 1.2, -0.7), (s * 0.56, 1.24, -0.6), 4)[1:],
                           [0.032] * 6, 8), "Metal")
        P.obj("SkidShoe", box((s * 0.56, 0.1, -0.765), (0.03, 0.5, 0.012)), "Dark", 0, False)

    # ---- the weapons beam across the floor, a seven-tube rocket pod on each end
    P.obj("Beam", box((0, 0.05, -0.42), (1.7, 0.12, 0.08)), "Dark", 0, False)
    for s in (1, -1):
        P.obj("Pylon", box((s * 0.85, 0.05, -0.5), (0.06, 0.2, 0.1)), "Dark", 0, False)
        P.obj("RocketPod", lathe([(0.0, -0.36), (0.09, -0.36), (0.13, -0.3), (0.13, 0.3), (0.12, 0.34), (0.0, 0.34)], 16, "y", (s * 0.85, 0.05, -0.62)),
              "Base")
        P.obj("PodBand", xf(torus(0.133, 0.012, 0.0, 16, 4), Matrix.Rotation(deg(90), 3, "X"), (s * 0.85, 0.2, -0.62)), "Accent")
        P.obj("PodBand", xf(torus(0.133, 0.012, 0.0, 16, 4), Matrix.Rotation(deg(90), 3, "X"), (s * 0.85, -0.12, -0.62)), "Accent")
        for k in range(7):
            a = 2 * math.pi * k / 6
            o = Vector((math.cos(a) * 0.072, 0, math.sin(a) * 0.072)) if k < 6 else Vector()
            c = Vector((s * 0.85, 0.395, -0.62)) + o
            P.obj("RocketTube", lathe([(0.032, 0.0), (0.032, 0.006), (0.0, 0.006)], 10, "y", tuple(c)), "Dark")
            P.obj("RocketTip", cone(c + Vector((0, -0.03, 0)), c + Vector((0, 0.002, 0)), 0.022, 8), "Accent")

    # ---- under the nose: the gyro camera ball on the right, the searchlight on the left, the chin gatling in the middle
    P.obj("CamMount", pipe([(0.2, 1.12, -0.38), (0.22, 1.2, -0.48)], [0.035, 0.03], 8), "Dark")
    P.obj("CamYoke", xf(torus(0.15, 0.02, 0.0, 18, 5), Matrix.Rotation(deg(90), 3, "Y"), (0.23, 1.25, -0.58)), "Dark")
    P.obj("CamBall", ball((0.23, 1.25, -0.58), (0.13, 0.13, 0.13), 16, 8), lambda c, n: "Glass" if n.y > 0.55 else "Belly")
    P.obj("CamLens", lathe([(0.0, 0.0), (0.055, 0.0), (0.05, 0.03), (0.0, 0.035)], 14, "y", (0.23, 1.355, -0.58)), "Lamp")
    P.obj("CamHood", xf(torus(0.065, 0.012, 0.0, 14, 4), Matrix.Rotation(deg(90), 3, "X"), (0.23, 1.36, -0.58)), "Metal")
    P.obj("SpotMount", pipe([(-0.2, 1.05, -0.36), (-0.24, 1.1, -0.47)], [0.03, 0.025], 6), "Dark")
    P.obj("Searchlight", lathe([(0.0, -0.1), (0.05, -0.1), (0.1, 0.06), (0.1, 0.08), (0.0, 0.08)], 16, "y", (-0.25, 1.12, -0.5)),
          lambda c, n: "Lamp" if n.y > 0.8 else "Base")
    P.obj("GunTurret", ball((0, 0.92, -0.5), (0.11, 0.12, 0.09), 14, 6), "Dark")
    P.obj("GunBody", lathe([(0.0, 0.0), (0.06, 0.0), (0.06, 0.24), (0.04, 0.27), (0.0, 0.27)], 12, "y", (0, 0.98, -0.53)), "Base")
    for k in range(3):
        a = 2 * math.pi * k / 3 + deg(90)
        o = Vector((math.cos(a) * 0.03, 0, math.sin(a) * 0.03))
        P.obj("GunBarrel", pipe([Vector((0, 1.2, -0.53)) + o, Vector((0, 1.56, -0.53)) + o], [0.013, 0.013], 6), "Metal")
    for y in (1.3, 1.5):
        P.obj("BarrelClamp", lathe([(0.05, 0.0), (0.05, 0.025), (0.0, 0.025), (0.0, 0.0)], 12, "y", (0, y, -0.53)), "Dark")

    # ---- antennas
    P.obj("RoofAntenna", hull([(0, 0.52, 0.44), (0, 0.42, 0.44), (0, 0.4, 0.58), (0.008, 0.47, 0.5), (-0.008, 0.47, 0.5)]), "Dark", 0, False)
    P.obj("BellyAntenna", pipe([(0.1, -0.2, -0.43), (0.12, -0.32, -0.6)], [0.008, 0.004], 4), "Dark")
    P.obj("BellyAntenna", pipe([(-0.1, 0.25, -0.44), (-0.12, 0.13, -0.58)], [0.008, 0.004], 4), "Dark")
    P.part("Muzzle", ball((0, 1.58, -0.53), (0.05, 0.03, 0.05), 8, 4), "Glow", (0, 1.58, -0.53))

    # ---- flying at speed: the whole machine leans 8 degrees nose-down (the main rotor's disc stays level over the mast)
    R4 = Matrix.Rotation(deg(-8), 4, "X")
    for ob in P.parts: ob.data.transform(R4)
    for ob in P.spin:
        ob.location = R4 @ ob.location
        if not ob.name.startswith("Rotor"): ob.data.transform(Matrix.Rotation(deg(-8), 4, "X"))
    return P



# ================================================================= pigeon (2026-10-13 remake)
# ---- the newspaper dart: nose at +Y, the crease along the top of the middle, the keel hanging under it
PG_NOSE, PG_BACK, PG_SPAN, PG_KEEL = 1.75, -1.45, 2.05, 0.55

def pg_xmax(y):
    """half-width of a wing at y: the leading edge runs straight from the nose to the back corner."""
    return PG_SPAN * max(0.0, (PG_NOSE - y) / (PG_NOSE - PG_BACK))

def pg_zw(x, y):
    """the top of a wing: a little dihedral, and the nose crumpled where it hit something."""
    ax = abs(x); k = max(0.0, (y - 0.85) / (PG_NOSE - 0.85))
    return 0.11 * ax + k * (0.035 * math.sin(11 * ax + 7 * y) + 0.025 * math.cos(17 * ax - 5 * y)) - 0.1 * k * k

def pg_quad(bm, pts):
    """one flat face facing up (print on the paper): no back side, no outline."""
    f = bm.faces.new([bm.verts.new(p) for p in pts]); f.normal_update()
    if f.normal.z < 0: f.normal_flip()
    return f

def pg_on(x, y, lift=0.012):
    return Vector((x, y, pg_zw(x, y) + lift))

def pg_rect(bm, s, x0, x1, y0, y1, lift=0.012, n=1):
    """a printed rectangle on the right (s=1) or left (s=-1) wing, clipped to the wing, split n times along x to follow the dihedral."""
    for i in range(n):
        a = x0 + (x1 - x0) * i / n; b = x0 + (x1 - x0) * (i + 1) / n
        lim0, lim1 = pg_xmax(y0) - 0.07, pg_xmax(y1) - 0.07
        if a > min(lim0, lim1): return
        b = min(b, lim0, lim1)
        if b - a < 0.02: return
        pg_quad(bm, [pg_on(s * a, y0, lift), pg_on(s * b, y0, lift), pg_on(s * b, y1, lift), pg_on(s * a, y1, lift)])

def pg_page(c, w, h, rx, rz, bend):
    """a loose newspaper page tumbling behind: a sheet w x h curled by `bend`, turned rx about across and rz about up, about c."""
    polys = []; nx, ny = 4, 5
    def pt(i, j):
        u = (i / nx - 0.5) * w; v = (j / ny - 0.5) * h
        return Vector((u, v, bend * (u * u + 0.5 * v * v)))
    for i in range(nx):
        for j in range(ny):
            polys.append([tuple(pt(i, j)), tuple(pt(i + 1, j)), tuple(pt(i + 1, j + 1)), tuple(pt(i, j + 1))])
    bm = sheet(polys, 0.012)
    pr = bmesh.new()   # its print: a headline and lines of text
    for j in range(4):
        v0 = h * (0.3 - j * 0.14); v1 = v0 - (0.06 if j == 0 else 0.03)
        for (u0, u1) in ((-0.42 * w, -0.04 * w), (0.04 * w, 0.42 * w)) if j else ((-0.4 * w, 0.4 * w),):
            pr.faces.new([pr.verts.new(Vector((u, v, bend * (u * u + 0.5 * v * v) + 0.009))) for (u, v) in ((u0, v0), (u1, v0), (u1, v1), (u0, v1))])
    m = Matrix.Rotation(rz, 3, "Z") @ Matrix.Rotation(rx, 3, "X")
    return xf(bm, m, c), xf(pr, m, c)


def C_pigeon():
    """KING PIGEON, king of the rooftops (2026-10-13, remade: "same as the alien bosses - realistic details, scarier, keep the cartoon
    shape"): the same fat, crowned, scowling city pigeon in a red cape, now built like a real feral rock pigeon. A blue-grey bird with a
    heavy puffed-out chest, the paler grey of the wings crossed by the two black wing bars every rock pigeon carries, the white rump patch
    above the tail, the tail grey with the black band across its end and white outer edges; on the neck the iridescent hackles, real
    scale-like feathers in even rows, green high on the neck going to purple low on the breast. A small round head, darker grey, the slim
    dark bill with the white knobbly cere at its base; eyes of orange-red in rings of red bare skin, glaring at the player under heavy,
    frowning brows. Coral-red legs, scaly, the toes gripping with black claws. Kingly touches, done evenly: a small gold crown of six points,
    a pearl on each and a ruby in front; a red velvet cape on his shoulders, trimmed with white ermine set with the black tail tips in a row.
    He does not fly on his wings: HE RIDES A GIANT PAPER AIRPLANE FOLDED FROM A NEWSPAPER - a classic dart, its two wings folded down
    from the nose to the back corners with a slight dihedral, the keel hanging under the middle crease, the leading edges thick where the
    paper is folded over, the folded-in flap showing as a second layer under each wing and at the back edge; printed all over like a real
    front page - a masthead of block letters on the left wing over a rule, a photo of the city's skyline in a frame, a bold headline on the
    right wing, columns of grey text lines with rules between them, text down the keel; the nose crumpled where it hit something. He
    perches on the crease near the back, his feet clenched round it, wings held half open for balance, his cape streaming back and
    rippling (SwayCape); three loose pages of the paper tumble away behind (Cloth). His shots leave from his bill."""
    P = Boss("pigeon", {"Base": ((0.42, 0.46, 0.56), 0.35), "Belly": ((0.92, 0.90, 0.84), 0.2), "Accent": ((0.78, 0.10, 0.14), 0.45),
                        "Trim": GOLD, "Glass": ((0.10, 0.62, 0.42), 0.9), "Dark": ((0.08, 0.08, 0.10), 0.35),
                        "Glow": ((1.0, 0.30, 0.10), 0.5), "Metal": ((0.52, 0.22, 0.66), 0.85), "Lamp": ((0.95, 0.2, 0.04), 0.8)})
    # ================================================================= the paper plane
    paper = []
    for s in (1, -1):
        rows, cols = 18, 9; polys = []
        def wp(i, j):
            y = PG_NOSE + (PG_BACK - PG_NOSE) * i / rows; x = s * pg_xmax(y) * j / cols
            return (x, y, pg_zw(x, y))
        for i in range(rows):
            for j in range(cols):
                if i == 0: polys.append([wp(0, 0), wp(1, j + 1), wp(1, j)])
                else: polys.append([wp(i, j), wp(i, j + 1), wp(i + 1, j + 1), wp(i + 1, j)])
        paper.append(sheet(polys, 0.016))
        # the folded-in flap under the wing: a second layer of paper, its edge a step at the back
        fl = [[(0, PG_NOSE - 0.05, -0.035), (s * 0.85, PG_BACK, pg_zw(0.85, PG_BACK) - 0.035), (0, PG_BACK, -0.035)]]
        paper.append(sheet(fl, 0.014))
        # the leading edge is a fold: thick and rounded
        P.part("Cloth", pipe([Vector((s * pg_xmax(y), y, pg_zw(pg_xmax(y), y))) for y in [PG_NOSE - (PG_NOSE - PG_BACK) * t / 10 for t in range(11)]],
                             [0.008] + [0.014] * 10, 5), "Belly", (0, 0, 0), 0, False)
        # the keel: one half each side of the crease, a narrow V
        kp = [[(0, PG_NOSE, 0.0), (0, PG_BACK, 0.0), (s * 0.07, PG_BACK, -PG_KEEL)]]
        k = bmesh.new()
        f = k.faces.new([k.verts.new(p) for p in kp[0]]); g = k.faces.new([k.verts.new(Vector(p) + Vector((-s * 0.012, 0, 0))) for p in reversed(kp[0])])
        bmesh.ops.recalc_face_normals(k, faces=k.faces)
        paper.append(k)
    for bm in paper:
        P.part("Cloth", bm, "Belly", (0, 0, 0), 0, False)
    # ---- the print: a front page across the two wings and down the keel
    pr = bmesh.new()
    # masthead on the left wing: block letters over a rule
    x = 0.18
    for wdt in (0.1, 0.09, 0.1, 0.05, 0.1, 0.1, 0.09, 0.1, 0.1):
        if wdt > 0.06: pg_rect(pr, -1, x, x + wdt, -0.12, -0.3)
        x += wdt + 0.035
    pg_rect(pr, -1, 0.15, 1.25, -0.34, -0.36, n=3)
    pg_rect(pr, -1, 0.15, 1.25, -0.08, -0.095, n=3)
    # the photo: a framed picture of the skyline
    px0, px1, py0, py1 = 0.55, 1.15, -0.5, -0.95
    pg_rect(pr, -1, px0, px1, py0, py1, 0.011, n=3)
    for (a, b, top) in ((0.6, 0.68, 0.35), (0.7, 0.76, 0.22), (0.78, 0.88, 0.4), (0.9, 0.95, 0.18), (0.97, 1.05, 0.3), (1.06, 1.1, 0.2)):
        pg_quad(pr, [pg_on(-a, py1 + 0.03, 0.016), pg_on(-b, py1 + 0.03, 0.016), pg_on(-b, py1 + 0.03 + top, 0.016), pg_on(-a, py1 + 0.03 + top, 0.016)])
    # the headline on the right wing, its words as bold blocks
    x = 0.16
    for wdt in (0.28, 0.18, 0.34, 0.22):
        pg_rect(pr, 1, x, x + wdt, -0.14, -0.3, n=2); x += wdt + 0.06
    # columns of text on both wings, a rule between the columns
    cols = ((0.15, 0.58), (0.68, 1.11), (1.21, 1.64))
    for s in (1, -1):
        for ci, (a, b) in enumerate(cols):
            y = 0.95 if ci == 0 else 0.3
            while y > PG_BACK + 0.12:
                skip = (-0.36 < y < 0.0) or (s < 0 and ci == 1 and py1 - 0.03 < y < py0 + 0.03) or (s < 0 and ci == 2 and py1 - 0.03 < y < py0 + 0.03)
                if not skip:
                    end = b - (0.12 if int((y * 100)) % 7 == 0 else 0.0)
                    pg_rect(pr, s, a, end, y, y - 0.028)
                y -= 0.065
            if ci < 2:
                xr = b + 0.05; y0 = 0.9 if ci == 0 else 0.25
                if xr < pg_xmax(PG_BACK + 0.1):
                    for yy0, yy1 in ((0.5, -0.05), (-0.4, PG_BACK + 0.12)):
                        if pg_xmax(yy0) - 0.07 > xr + 0.01:
                            pg_quad(pr, [pg_on(s * xr, yy0), pg_on(s * (xr + 0.008), yy0), pg_on(s * (xr + 0.008), yy1), pg_on(s * xr, yy1)])
    P.part("ClothPrint", pr, lambda c, n: "Base" if -1.16 < c.x < -0.54 and -0.96 < c.y < -0.49 and c.z < pg_zw(c.x, c.y) + 0.0135 else "Dark",
           (0, 0, 0), 0, False)
    # text down the keel's sides
    kk = bmesh.new()
    for s in (1, -1):
        for j in range(6):
            z0 = -0.08 - j * 0.065
            ya, yb = PG_BACK + 0.1, PG_BACK + 0.1 + (PG_NOSE - PG_BACK) * (1 + z0 / PG_KEEL) * 0.85
            if yb - ya < 0.2: continue
            xo = s * (0.07 * (-z0) / PG_KEEL + 0.006)
            f = kk.faces.new([kk.verts.new(Vector(p)) for p in ((xo, ya, z0), (xo, yb, z0), (xo, yb, z0 - 0.026), (xo, ya, z0 - 0.026))])
            f.normal_update()
            if f.normal.x * s < 0: f.normal_flip()
    P.part("ClothPrint", kk, "Dark", (0, 0, 0), 0, False)
    # three loose pages tumbling away behind
    for (c, w, h, rx, rz, bend) in (((0.55, -1.85, 0.35), 0.5, 0.62, 0.6, 0.5, 0.35), ((-0.5, -2.15, 0.6), 0.42, 0.52, -0.9, -0.7, -0.4),
                                    ((0.15, -2.45, 0.15), 0.34, 0.44, 1.3, 1.1, 0.5)):
        pg_, pp = pg_page(c, w, h, rx, rz, bend)
        P.part("Cloth", pg_, "Belly", (0, 0, 0), 0, False)
        P.part("ClothPrint", pp, "Dark", (0, 0, 0), 0, False)

    # ================================================================= the pigeon, perched on the crease near the back
    # ---- body: tail root to the base of the head, a deep puffed chest
    spine = bez((0, -1.28, 0.62), (0, -0.85, 0.6), (0, -0.25, 0.66), (0, 0.12, 1.12), 14) + bez((0, 0.12, 1.12), (0, 0.2, 1.3), (0, 0.24, 1.45), (0, 0.28, 1.58), 5)[1:]
    n = len(spine); fr = spine_frames(spine)
    RX = [lerp_keys(i / (n - 1), [(0, 0.12), (0.18, 0.4), (0.45, 0.6), (0.62, 0.58), (0.8, 0.38), (1, 0.26)]) for i in range(n)]
    RZ = [lerp_keys(i / (n - 1), [(0, 0.1), (0.18, 0.36), (0.45, 0.6), (0.62, 0.6), (0.8, 0.4), (1, 0.27)]) for i in range(n)]
    def body_paint(c, nn):
        if c.y < -0.85 and nn.z > 0.35: return "Belly"   # the white rump
        return "Base"
    P.obj("Body", body_loft(spine, RX, RZ, fr, 24, 1.05, 0.85), body_paint, 1)
    tb = body_loft(spine, RX, RZ, fr, 24, 1.05, 0.85); bmesh.ops.subdivide_edges(tb, edges=tb.edges[:], cuts=1, use_grid_fill=True)
    tree = BVHTree.FromBMesh(tb)
    def on_body(o, d):
        hit = tree.ray_cast(Vector(o), Vector(d).normalized())
        return (hit[0], hit[1]) if hit[0] is not None else (None, None)
    # ---- the neck hackles: real scale feathers in even rows, green above, purple below
    for row in range(9):
        u = row / 8.0
        ax = Vector((0, 0.02 + 0.24 * u, 0.98 + 0.6 * u))
        cnt = 19 - row
        for k in range(cnt):
            a = math.radians(-118 + 236 * (k + 0.5 * (row % 2)) / cnt)
            p, nrm = on_body(ax, (math.sin(a), math.cos(a), 0.1))
            if p is None: continue
            nrm = nrm.normalized()
            down = (Vector((0, -0.25, -1)) - nrm * nrm.dot(Vector((0, -0.25, -1)))).normalized()
            across = down.cross(nrm).normalized()
            slot = "Glass" if row >= 5 or (row == 4 and k % 2) else "Metal"
            tip = p + down * 0.11 + nrm * 0.012   # a scale feather: rounded at the base, a blunt point, lying flat and overlapping the row below
            w = (0.06 - 0.012 * u) * across
            P.obj("Hackle", hull([p - down * 0.02 + w * 0.6, p - down * 0.02 - w * 0.6, p + down * 0.04 + w, p + down * 0.04 - w,
                                  tip + w * 0.35, tip - w * 0.35, p + down * 0.04 + nrm * 0.012]), slot, 0, False)
    # ---- the head
    H = Vector((0, 0.36, 1.74))
    P.obj("Head", ball(tuple(H), (0.3, 0.31, 0.29), 18, 9), "Base", 1)
    # the slim dark bill, slightly drooped at the tip, with the white knobbly cere at its base
    P.obj("Bill", loft([(H.y + 0.24, 0.065, 0.055, 0, H.z - 0.06), (H.y + 0.33, 0.045, 0.04, 0, H.z - 0.075), (H.y + 0.41, 0.028, 0.028, 0, H.z - 0.1),
                        (H.y + 0.46, 0.01, 0.012, 0, H.z - 0.13)], 10), "Dark", 1)
    for s in (1, -1):
        P.obj("Cere", ball((s * 0.028, H.y + 0.27, H.z + 0.005), (0.03, 0.045, 0.026), 8, 4), "Belly")
    # eyes: orange-red in rings of red skin, set forward enough to glare at the player, under heavy frowning brows
    for s in (1, -1):
        out = Vector((s * 0.62, 0.78, 0.08)).normalized()
        e = H + out * 0.27 + Vector((0, 0, 0.04))
        x_ = out.cross(Vector((0, 0, 1))).normalized(); z_ = x_.cross(out).normalized()
        P.obj("EyeRing", oriented_ball(e, (0.105, 0.1, 0.035), x_, z_, out, 12, 4), "Accent")
        P.obj("Eye", oriented_ball(e + out * 0.02, (0.075, 0.07, 0.03), x_, z_, out, 12, 4), "Lamp")
        P.obj("Pupil", oriented_ball(e + out * 0.04, (0.032, 0.03, 0.015), x_, z_, out, 8, 3), "Dark")
        P.obj("Glint", ball(tuple(e + out * 0.05 + z_ * 0.03 - x_ * 0.02 * s), (0.012, 0.012, 0.012), 6, 3), "Belly")
        b0 = H + Vector((s * 0.03, 0.27, 0.13)); b1 = H + Vector((s * 0.2, 0.22, 0.2)); b2 = H + Vector((s * 0.3, 0.07, 0.17))
        P.obj("Brow", pipe([b0, b1, b2], [0.035, 0.045, 0.02], 8), "Dark")
    # ---- the crown: six points with pearls, a ruby in front
    CC = H + Vector((0, -0.02, 0.24))
    P.obj("Crown", lathe([(0.15, 0.0), (0.165, 0.09), (0.15, 0.09), (0.135, 0.01)], 18, "z", tuple(CC)), "Trim")
    for k in range(6):
        a = 2 * math.pi * k / 6
        b = CC + Vector((math.sin(a) * 0.155, math.cos(a) * 0.155, 0.08))
        P.obj("CrownPoint", cone(b, b + Vector((math.sin(a) * 0.02, math.cos(a) * 0.02, 0.12)), 0.035, 5), "Trim", 0, False)
        P.obj("Pearl", ball(tuple(b + Vector((math.sin(a) * 0.02, math.cos(a) * 0.02, 0.135))), (0.022, 0.022, 0.022), 6, 3), "Belly")
    P.obj("Ruby", ball(tuple(CC + Vector((0, 0.165, 0.045))), (0.035, 0.02, 0.035), 8, 4), "Glow")
    # ---- the wings, held half open for balance: two black bars across the inner wing, fingered primaries with dark tips
    for s in (1, -1):
        keys = [(0.38, 0.0, -0.62, 0.14, 1.12), (0.68, -0.22, -0.88, 0.1, 1.28), (0.95, -0.46, -1.0, 0.07, 1.36), (1.12, -0.68, -1.06, 0.05, 1.4)]
        bm = sweep([(x, airfoil(le, te, th, z)) for (x, le, te, th, z) in fine(keys, 0.06)], "x")
        if s < 0: bm = mirror_x(bm)
        def wpaint(c, nn):
            ax = abs(c.x)
            le = lerp_keys(ax, [(0.38, 0.0), (0.68, -0.22), (0.95, -0.46), (1.12, -0.68)])
            te = lerp_keys(ax, [(0.38, -0.62), (0.68, -0.88), (0.95, -1.0), (1.12, -1.06)])
            f = (le - c.y) / max(0.01, le - te)
            if nn.z < -0.3: return "Belly" if f < 0.5 else "Base"
            if ax < 1.0 and 0.6 < f < 0.74: return "Dark"   # the first wing bar, across the greater coverts
            return "Base"
        P.obj("Wing", bm, wpaint, 0)
        for f in (0.5, 0.72):   # the two black wing bars, across the inner wing
            pts = []
            for x in (0.42, 0.55, 0.68, 0.8, 0.92):
                le = lerp_keys(x, [(0.38, 0.0), (0.68, -0.22), (0.95, -0.46)]); te = lerp_keys(x, [(0.38, -0.62), (0.68, -0.88), (0.95, -1.0)])
                z = lerp_keys(x, [(0.38, 1.12), (0.68, 1.28), (0.95, 1.36)]) + lerp_keys(x, [(0.38, 0.14), (0.68, 0.1), (0.95, 0.07)]) * 0.45 + 0.012
                pts.append(Vector((s * x, le - f * (le - te), z)))
            P.obj("WingBar", pipe(pts, [0.03, 0.04, 0.04, 0.035, 0.02], 6), "Dark")
        for k in range(8):   # the secondaries along the trailing edge, the second bar across them
            x = 0.42 + k * 0.075; te = lerp_keys(x, [(0.38, -0.62), (0.68, -0.88), (0.95, -1.0)])
            z = lerp_keys(x, [(0.38, 1.12), (0.68, 1.28), (0.95, 1.36)])
            base = Vector((s * x, te + 0.12, z)); tip = Vector((s * (x + 0.04), te - 0.26, z - 0.06))
            side = Vector((0.045, 0, 0))
            bmf = hull([base + side, base - side, tip + side * 0.8, tip - side * 0.8, base + (tip - base) * 0.5 + side * 1.1 + Vector((0, 0, 0.02)),
                        base + (tip - base) * 0.5 - side * 1.1 + Vector((0, 0, 0.02)), tip + Vector((0, -0.03, 0.01))])
            P.obj("Secondary", bmf, lambda c, nn, b=base, t=tip: "Dark" if 0.35 < (c - b).dot(t - b) / (t - b).length_squared < 0.55 else "Base", 0, False)
        for k in range(7):   # the primaries, spread like fingers, dark at the tips
            a = math.radians(28 + k * 11)
            base = Vector((s * (1.0 + 0.02 * k), -0.6 - 0.06 * k, 1.38 - 0.012 * k))
            ln = 0.62 - abs(k - 2) * 0.04
            d = Vector((s * math.cos(a), -math.sin(a), 0.06)).normalized()
            tip = base + d * ln
            side = d.cross(Vector((0, 0, 1))).normalized() * 0.05
            bmf = hull([base + side, base - side, tip + side * 0.5, tip - side * 0.5, base + d * ln * 0.6 + side * 1.1, base + d * ln * 0.6 - side * 1.1,
                        base + Vector((0, 0, 0.02)), tip + d * 0.03])
            P.obj("Primary", bmf, lambda c, nn, b=base, t=tip: "Dark" if (c - b).dot(t - b) / (t - b).length_squared > 0.7 else "Base", 0, False)
    # ---- the tail: twelve feathers in a fan, grey with a black band across the end, the outer ones edged white
    hub = Vector((0, -1.22, 0.62))
    for k in range(12):
        a = math.radians(-33 + 66 * k / 11)
        d = Vector((math.sin(a), -math.cos(a), -0.1)).normalized()
        tip = hub + d * 0.62
        side = Vector((math.cos(a), math.sin(a), 0)) * 0.055
        lift = Vector((0, 0, 0.012 * (6 - abs(k - 5.5))))
        bmf = hull([hub + side * 0.6 + lift, hub - side * 0.6 + lift, tip + side + lift, tip - side + lift, tip + d * 0.04 + lift,
                    hub + lift + Vector((0, 0, 0.02)), tip + lift + Vector((0, 0, 0.015))])
        outer = k in (0, 11)
        P.obj("TailFeather", bmf, lambda c, nn, h=hub, t=tip, o=outer: "Dark" if (c - h).dot(t - h) / (t - h).length_squared > 0.78 else ("Belly" if o else "Base"), 0, False)
    # ---- the legs: coral red and scaly, the toes clenched round the crease, black claws
    for s in (1, -1):
        hip = Vector((s * 0.16, -0.42, 0.22)); ank = Vector((s * 0.09, -0.36, 0.05))
        P.obj("Leg", pipe([hip, ank], [0.055, 0.04], 8), "Accent")
        for j in range(3):   # the scutes up the front of the leg
            P.obj("Scute", oriented_ball(hip + (ank - hip) * (0.25 + 0.25 * j) + Vector((0, 0.035, 0)), (0.045, 0.03, 0.02),
                                         Vector((1, 0, 0)), Vector((0, 0, 1)), Vector((0, 1, 0)), 6, 3), "Accent")
        for k, a in enumerate((-30, 0, 30, 180)):   # three toes forward over the crease, one behind
            r = math.radians(a + (s * 10 if a != 180 else 0))
            d = Vector((math.sin(r) * 0.6, math.cos(r), 0)).normalized()
            L = 0.24 if a != 180 else 0.14
            pts = [ank + d * L * u + Vector((0, 0, -0.04 * u + (pg_zw(ank.x + d.x * L * u, ank.y + d.y * L * u) if abs(ank.x + d.x * L * u) > 0.02 else 0.0) * 0.6)) for u in (0, 0.35, 0.7, 1.0)]
            for i in range(3):   # knuckle pads: segments, so the toes read scaly
                P.obj("Toe", oriented_ball((pts[i] + pts[i + 1]) * 0.5 + Vector((0, 0, 0.02)), (0.034, (pts[i + 1] - pts[i]).length * 0.62, 0.028),
                                           d.cross(Vector((0, 0, 1))).normalized(), d, Vector((0, 0, 1)), 8, 4), "Accent")
            P.obj("Claw", pipe(bez(pts[-1] + Vector((0, 0, 0.02)), pts[-1] + d * 0.04 + Vector((0, 0, 0.01)), pts[-1] + d * 0.06 - Vector((0, 0, 0.02)),
                                   pts[-1] + d * 0.05 - Vector((0, 0, 0.05)), 3), [0.016, 0.012, 0.008, 0.0], 5), "Dark")
    # ---- the cape: red velvet from his shoulders, streaming back over his back, an ermine trim with black tail tips in a row
    CH = Vector((0, -0.05, 1.32))
    def top_z(x, y):
        p, _ = on_body((x, y, 3.0), (0, 0, -1))
        return p.z if p is not None else None
    def cpt(u, v):
        a = math.radians(-80 + 160 * u)
        r = 0.34 + 0.26 * v
        x = math.sin(a) * r; y = 0.06 - math.cos(a) * 0.3 - 1.25 * v
        z = top_z(x, y)
        if z is None:
            zc = top_z(0, y); zc = zc if zc is not None else 0.85 - 0.3 * max(0.0, -1.28 - y)
            z = zc - 0.5 * abs(x)
        return (x, y, z + 0.05 + 0.04 * v + 0.07 * v * math.sin(u * math.pi * 3 + v * 4))
    polys = [[cpt(i / 14, j / 6), cpt((i + 1) / 14, j / 6), cpt((i + 1) / 14, (j + 1) / 6), cpt(i / 14, (j + 1) / 6)] for i in range(14) for j in range(6)]
    P.part("SwayCape", sheet(polys, 0.03), "Accent", tuple(CH), 0, False)
    hem = [Vector(cpt(i / 28, 1.0)) for i in range(29)]
    P.part("SwayCape", pipe(hem, [0.05] * 29, 8), "Belly", tuple(CH), 0, True)
    for side_u in (0.0, 1.0):
        P.part("SwayCape", pipe([Vector(cpt(side_u, j / 8)) for j in range(9)], [0.045] * 9, 8), "Belly", tuple(CH), 0, True)
    for i in range(1, 28, 3):   # ermine tails, evenly along the hem
        p = hem[i]
        P.part("SwayCape", cone(p + Vector((0, 0, -0.02)), p + Vector((0, -0.02, -0.11)), 0.022, 5), "Dark", tuple(CH), 0, False)
    # the clasp at his throat
    P.obj("Clasp", lathe([(0.0, 0.0), (0.07, 0.0), (0.07, 0.025), (0.0, 0.035)], 12, "y", (0, 0.5, 1.12)), "Trim")
    P.part("Muzzle", ball((0, H.y + 0.4, H.z - 0.095), (0.02, 0.02, 0.02), 6, 3), "Dark", (0, H.y + 0.4, H.z - 0.095))
    return P



# ================================================================= titan (2026-10-13 remake)
def tt_bar(c, u, v, nrm, a, b, w, t, ext=True):
    """a raised bar on a plane (origin c, axes u, v, out nrm) from 2D point a to b, w wide, t proud (ends pushed out by w/2 so strokes meet)."""
    a, b = Vector((a[0], a[1])), Vector((b[0], b[1])); d = (b - a).normalized()
    if ext: a, b = a - d * w * 0.5, b + d * w * 0.5
    s = Vector((-d.y, d.x)) * w * 0.5
    pts = []
    for p in (a + s, a - s, b - s, b + s):
        q = c + u * p.x + v * p.y
        pts += [q, q + nrm * t]
    return hull([tuple(p) for p in pts])

TT_GLYPHS = {   # strokes in a 0.62 x 1.0 cell
    "S": [((0, 1), (0.6, 1)), ((0, 1), (0, 0.5)), ((0, 0.5), (0.6, 0.5)), ((0.6, 0.5), (0.6, 0)), ((0, 0), (0.6, 0))],
    "T": [((0, 1), (0.62, 1)), ((0.31, 1), (0.31, 0))],
    "O": [((0, 0), (0, 1)), ((0, 1), (0.6, 1)), ((0.6, 1), (0.6, 0)), ((0.6, 0), (0, 0))],
    "P": [((0, 0), (0, 1)), ((0, 1), (0.6, 1)), ((0.6, 1), (0.6, 0.5)), ((0.6, 0.5), (0, 0.5))],
    "A": [((0, 0), (0.31, 1)), ((0.31, 1), (0.62, 0)), ((0.15, 0.42), (0.47, 0.42))],
    "X": [((0, 0), (0.62, 1)), ((0, 1), (0.62, 0))],
    "I": [((0.31, 0), (0.31, 1))],
}

def tt_word(P, name, word, c, u, v, nrm, h, w, t, paint, gap=0.28):
    """a word of raised bar letters, centred on c, letter height h, stroke width w."""
    adv = (0.62 + gap) * h; x0 = -(len(word) * adv - gap * h) * 0.5
    for i, ch in enumerate(word):
        for a, b in TT_GLYPHS[ch]:
            A = (x0 + i * adv + a[0] * h, (a[1] - 0.5) * h); B = (x0 + i * adv + b[0] * h, (b[1] - 0.5) * h)
            P.obj(name, tt_bar(c, u, v, nrm, A, B, w, t, ext=not (ch in "AX")), paint, 0, False)

def tt_clip(poly, x0, x1, y0, y1):
    """Sutherland-Hodgman: a convex 2D polygon clipped to a rectangle."""
    def cut(pts, inside, inter):
        out = []
        for i in range(len(pts)):
            p, q = pts[i], pts[(i + 1) % len(pts)]
            if inside(q):
                if not inside(p): out.append(inter(p, q))
                out.append(q)
            elif inside(p): out.append(inter(p, q))
        return out
    def ix(k): return lambda p, q: (k, p[1] + (q[1] - p[1]) * (k - p[0]) / (q[0] - p[0]))
    def iy(k): return lambda p, q: (p[0] + (q[0] - p[0]) * (k - p[1]) / (q[1] - p[1]), k)
    for inside, inter in ((lambda p: p[0] >= x0, ix(x0)), (lambda p: p[0] <= x1, ix(x1)), (lambda p: p[1] >= y0, iy(y0)), (lambda p: p[1] <= y1, iy(y1))):
        poly = cut(poly, inside, inter)
        if len(poly) < 3: return []
    return poly

def tt_plate(c, u, v, nrm, poly, t):
    pts = []
    for p in poly:
        q = c + u * p[0] + v * p[1]; pts += [tuple(q), tuple(q + nrm * t)]
    return hull(pts)

def tt_visor(c, r, L, th=0.012, seg=14):
    """a signal's tunnel visor over a lens facing +y at c: an arc over the top, cut long at the top and short at the sides."""
    bm = bmesh.new(); rows = []
    for k in range(seg + 1):
        a = math.radians(-12 + 204 * k / seg); x, z = math.cos(a) * r, math.sin(a) * r
        Lk = L * (0.3 + 0.7 * max(0.0, math.sin(a)))
        rows.append((bm.verts.new(c + Vector((x, 0, z))), bm.verts.new(c + Vector((x, Lk, z)))))
    for (a0, a1), (b0, b1) in zip(rows, rows[1:]): bm.faces.new((a0, b0, b1, a1))
    return sheet_solid(bm, th)

def tt_cone(base, axis, H, P, name):
    """a real traffic cone: a square moulded base with notched corners, the cone with two white reflective collars, a rolled lip at the top."""
    axis = axis.normalized(); R = axis.to_track_quat("Z", "Y").to_matrix().to_4x4()
    M = Matrix.Translation(base) @ R
    k = H / 0.62
    sq = [(0.17, 0.12), (0.12, 0.17), (-0.12, 0.17), (-0.17, 0.12), (-0.17, -0.12), (-0.12, -0.17), (0.12, -0.17), (0.17, -0.12)]
    bm = hull([(x * k, y * k, z) for (x, y) in sq for z in (0.0, 0.035 * k)]); bm.transform(M)
    P.obj(name, bm, "Trim", 0, False)
    prof = [(0.0, 0.03), (0.135, 0.03), (0.13, 0.06), (0.105, 0.2), (0.1, 0.22), (0.1, 0.3), (0.085, 0.34), (0.08, 0.36), (0.08, 0.42), (0.06, 0.52),
            (0.042, 0.6), (0.046, 0.6), (0.046, 0.62), (0.0, 0.62)]
    bm = lathe([(r * k, h * k) for r, h in prof], 18, "z"); bm.transform(M)
    def paint(c, n, M=M):
        h = (M.inverted() @ c).z / k
        return "Belly" if (0.205 < h < 0.305) or (0.345 < h < 0.425) else "Trim"
    P.obj(name, bm, paint, 0, True)


# ================================================================= 4. the traffic titan
def C_titan():
    """The TRAFFIC TITAN (2026-10-13, remade: "same as the alien bosses - realistic details, scarier, keep the cartoon shape"): the same
    robot built from the street's own gear - a traffic light for a head, traffic cones for shoulders, a stop sign to fight with - now with
    every part made like the real thing, and riding a flying taxi.
    His head is a real three-aspect signal head: a black housing in three sections on a black backplate with the yellow reflective border,
    a tunnel visor over every lens (cut long at the top, short at the sides), each lens a stepped Fresnel dome in its door ring; the red
    one is lit and glares at the player under a black brow bent down into a V, the amber and green ones dark. Under it his jaw is the
    hanger bracket: a grille of steel fangs, top and bottom, with the red glow of his furnace behind them, on a clamp round a steel mast.
    His body is a signal controller cabinet - grey steel, a door seam, louvred vents and a handle with a lock - with a barricade board for a
    breastplate, yellow with black chevrons pointing up to his chin, and a flashing barricade lamp on each top corner. On each shoulder
    a real traffic cone: the square moulded base with notched corners, two white reflective collars, a rolled lip at the top. His arms
    and legs are galvanised signal poles with bolted flanges at every joint; his hips are a concrete jersey barrier with its two
    scupper slots; his feet are the poles' base plates, bolted to the roof with four anchor bolts each. In his left fist a STOP sign on
    its post, swung like a battle-axe - the octagon in red with its white border and the raised white letters, clamped to the post by
    two brackets. His right forearm ends in a yellow speed camera: the box, its rain hood, the flash window and the lens his shots
    leave from.
    He flies RIDING A FLYING TAXI: he stands on the roof of a real yellow city cab - a sedan with a long hood and trunk, the glasshouse
    of windshield, side windows and rear window between the A, B and C pillars, four doors with their seams and handles, side mirrors,
    a checker band down each side, the lit TAXI sign on the roof and the medallion on the hood, a chrome grille and bumpers, square
    headlights and amber turn signals in front, red tail lamps and the plate behind. Its four wheels have folded flat under it on struts
    out of the wheel wells and turned into hover thrusters: each tyre lies on its side round a five-spoke rim and spins fast
    (RotorFL/FR/BL/BR), a glowing nozzle in its hub, rings of exhaust light shrinking away under it."""
    P = Boss("titan", {"Base": TAXI, "Belly": ((0.9, 0.9, 0.88), 0.45), "Accent": ((0.82, 0.06, 0.06), 0.6), "Trim": ((1.0, 0.38, 0.04), 0.5),
                       "Glass": ((0.06, 0.3, 0.16), 0.9), "Dark": ((0.05, 0.055, 0.06), 0.6), "Glow": ((1.0, 0.1, 0.06), 0.5),
                       "Metal": ((0.6, 0.62, 0.66), 0.7), "Lamp": ((1.0, 0.75, 0.3), 0.8)})
    X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))
    # ================= the taxi: the cab's body, nose at +y (toward the player)
    keys = [(-1.28, 0.58, 0.15, 0.25), (-1.22, 0.63, 0.21, 0.27), (-1.1, 0.64, 0.24, 0.27), (1.05, 0.64, 0.24, 0.27), (1.2, 0.63, 0.2, 0.25),
            (1.28, 0.58, 0.14, 0.23)]
    rings = []
    for (y0, a0, b0, z0), (y1, a1, b1, z1) in zip(keys, keys[1:]):
        n = max(1, int((y1 - y0) / 0.1))
        for i in range(n):
            t = i / n; rings.append((y0 + (y1 - y0) * t, a0 + (a1 - a0) * t, b0 + (b1 - b0) * t, 0.0, z0 + (z1 - z0) * t))
    rings.append(keys[-1][:1] + (keys[-1][1], keys[-1][2], 0.0, keys[-1][3]))
    P.obj("Cab", loft(rings, 36, sq=4.0), "Base", 0, True)
    # the glasshouse: dark glass, with the roof panel and the pillars laid over it
    gb, gt = (0.57, 0.46, -0.92, 0.62), (0.5, 0.94, -0.5, 0.15)
    P.obj("Glasshouse", hull([(sx * w, y, z) for sx in (1, -1) for (w, z, ya, yb) in (gb, gt) for y in (ya, yb)]), "Dark", 0, False)
    P.obj("Roof", box((0, -0.175, 0.945), (1.03, 0.68, 0.03)), "Base", 0, False)
    def side_pt(s, y, z, out=0.012):
        t = (z - 0.46) / (0.94 - 0.46); w = 0.57 + (0.5 - 0.57) * t
        return (s * (w + out), y, z)
    for s in (1, -1):
        P.obj("APillar", pipe([(s * 0.575, 0.62, 0.47), (s * 0.505, 0.15, 0.94)], [0.035, 0.035], 6), "Base")
        P.obj("BPillar", hull([side_pt(s, y, z, o) for y in (-0.21, -0.14) for z in (0.47, 0.93) for o in (0.0, 0.016)]), "Base", 0, False)
        def at_y(z, ya, yb): t = (z - 0.46) / 0.48; return ya + (yb - ya) * t
        P.obj("CPillar", hull([side_pt(s, at_y(z, y0, y1), z, o) for (y0, y1) in ((-0.92, -0.5), (-0.62, -0.38)) for z in (0.47, 0.93) for o in (0.0, 0.016)]), "Base", 0, False)
        P.obj("Beltline", pipe([(s * 0.585, -0.95, 0.475), (s * 0.585, 0.64, 0.475)], [0.012, 0.012], 5), "Metal")
        # doors: seams, handles; the checker band; the wheel wells; the side mirror
        for y in (0.5, -0.17, -0.82):
            P.obj("Seam", box((s * 0.643, y, 0.27), (0.006, 0.012, 0.42)), "Dark", 0, False)
        for y in (0.3, -0.37):
            P.obj("Handle", box((s * 0.648, y, 0.41), (0.016, 0.1, 0.026)), "Metal", 0, False)
        for i in range(20):
            for j in range(2):
                y = -0.98 + i * 0.1
                if abs(abs(y) - 0.8) < 0.3: continue
                P.obj("Check", box((s * 0.645, y + 0.05, 0.305 + j * 0.06), (0.008, 0.1, 0.06)), "Dark" if (i + j) % 2 else "Belly", 0, False)
        for y in (0.8, -0.8):
            P.obj("Well", hull([(s * xx, y + math.cos(a) * 0.27, 0.03 + math.sin(a) * 0.27) for xx in (0.6, 0.648) for a in [math.pi * k / 12 for k in range(13)]]), "Dark", 0, False)
        P.obj("MirrorArm", pipe([(s * 0.6, 0.5, 0.52), (s * 0.7, 0.52, 0.57)], [0.02, 0.02], 5), "Dark")
        P.obj("Mirror", hull([(s * x, y, z) for x in (0.68, 0.76) for y in (0.5, 0.56) for z in (0.54, 0.62)]), "Base", 0, False)
        # front: square headlights in chrome bezels, amber turn signals; back: red tail lamps
        P.obj("Bezel", box((s * 0.44, 1.255, 0.33), (0.24, 0.03, 0.12)), "Metal", 0, False)
        P.obj("Headlight", box((s * 0.44, 1.27, 0.33), (0.2, 0.02, 0.09)), "Lamp", 0, False)
        P.obj("Turn", box((s * 0.44, 1.255, 0.2), (0.16, 0.03, 0.05)), "Trim", 0, False)
        P.obj("Tail", box((s * 0.47, -1.265, 0.32), (0.18, 0.03, 0.12)), "Accent", 0, False)
    P.obj("Grille", box((0, 1.27, 0.29), (0.5, 0.03, 0.16)), "Dark", 0, False)
    for k in range(4):
        P.obj("GrilleBar", box((0, 1.285, 0.23 + k * 0.04), (0.5, 0.012, 0.012)), "Metal", 0, False)
    for yb in (1.3, -1.3):
        P.obj("Bumper", hull([(sx * w, yb + dy, z) for sx in (1, -1) for (w, dy) in ((0.62, 0.0), (0.66, -0.04 * (1 if yb > 0 else -1))) for z in (0.06, 0.16)]), "Metal", 0, False)
    P.obj("Plate", box((0, -1.29, 0.22), (0.26, 0.012, 0.12)), "Belly", 0, False)
    P.obj("PlateText", box((0, -1.298, 0.22), (0.18, 0.006, 0.04)), "Dark", 0, False)
    P.obj("Medallion", box((0, 0.98, 0.512), (0.12, 0.08, 0.008)), "Metal", 0, False)
    # the TAXI sign on the roof, in front of his feet
    P.obj("TaxiSign", hull([(sx * w, y, z) for sx in (1, -1) for (w, y, z) in ((0.2, 0.18, 0.96), (0.2, 0.04, 0.96), (0.18, 0.165, 1.1), (0.18, 0.055, 1.1))]), "Lamp", 0, False)
    tt_word(P, "TaxiText", "TAXI", Vector((0, 0.177, 1.03)), -X, Z, Vector((0, 0.95, 0.31)).normalized(), 0.07, 0.016, 0.008, "Dark", 0.3)
    # the four wheels folded flat under the cab on struts: hover thrusters that spin
    for sy, fb in ((0.8, "F"), (-0.8, "B")):
        for s, lr in ((1, "R"), (-1, "L")):
            hub = Vector((s * 0.6, sy, -0.06)); name = "Rotor" + fb + lr
            P.obj("Strut", pipe([(s * 0.5, sy, 0.12), hub + Vector((0, 0, 0.06))], [0.04, 0.035], 8), "Metal")
            P.part(name, xf(torus(0.2, 0.075, 0.0, 28, 8), None, tuple(hub)), "Dark", tuple(hub))
            for k in range(24):
                a = 2 * math.pi * k / 24
                P.part(name, box(tuple(hub + Vector((math.cos(a) * 0.272, math.sin(a) * 0.272, 0))), (0.03, 0.05, 0.1), Matrix.Rotation(a, 3, "Z")), "Dark", tuple(hub), 0, False)
            P.part(name, lathe([(0.15, -0.02), (0.15, 0.02), (0.06, 0.03), (0.0, 0.035)], 20, "z", tuple(hub)), "Metal", tuple(hub))
            for k in range(5):
                a = 2 * math.pi * k / 5
                P.part(name, tt_bar(hub + Vector((0, 0, 0.03)), X, Y, Z, (math.cos(a) * 0.05, math.sin(a) * 0.05), (math.cos(a) * 0.14, math.sin(a) * 0.14), 0.035, 0.02), "Metal", tuple(hub), 0, False)
            P.part(name, lathe([(0.13, 0.0), (0.0, 0.0)], 20, "z", tuple(hub + Vector((0, 0, -0.025)))), "Lamp", tuple(hub))
            P.obj("ClothJet", lathe([(0.0, -0.03), (0.12, -0.03), (0.1, -0.12), (0.06, -0.24), (0.0, -0.4)], 16, "z", tuple(hub)), "Lamp", 0, True)
    # ================= the titan standing on the roof
    R0 = 0.96; cy = -0.18
    for s in (1, -1):   # feet: the poles' base plates bolted to the roof
        f = Vector((s * 0.27, cy, R0))
        P.obj("BasePlate", box(tuple(f + Vector((0, 0, 0.02))), (0.24, 0.24, 0.04)), "Metal", 0, False)
        for bx in (1, -1):
            for by in (1, -1):
                P.obj("Anchor", lathe([(0.022, 0.0), (0.022, 0.03), (0.012, 0.03), (0.012, 0.06), (0.0, 0.06)], 6, "z", tuple(f + Vector((bx * 0.085, by * 0.085, 0.04)))), "Dark", 0, False)
        hip = Vector((s * 0.2, cy, R0 + 0.6)); kn = Vector((s * 0.3, cy + 0.06, R0 + 0.32))
        P.obj("Leg", pipe([f + Vector((0, 0, 0.04)), kn, hip], [0.08, 0.075, 0.075], 12), "Metal")
        d = (hip - kn).normalized()
        P.obj("KneeFlange", pipe([kn - d * 0.025, kn + d * 0.025], [0.11, 0.11], 16), "Metal")
        for k in range(6):
            a = 2 * math.pi * k / 6; e1 = d.orthogonal().normalized(); e2 = d.cross(e1)
            P.obj("Bolt", ball(tuple(kn + d * 0.03 + (e1 * math.cos(a) + e2 * math.sin(a)) * 0.085), (0.016, 0.016, 0.016), 6, 3), "Dark")
    # hips: a concrete jersey barrier with its scuppers
    prof = [(-0.2, 0.0), (0.2, 0.0), (0.2, 0.05), (0.12, 0.11), (0.07, 0.28), (-0.07, 0.28), (-0.12, 0.11), (-0.2, 0.05)]
    z0 = R0 + 0.56
    P.obj("Jersey", sweep([(x, [(cy + u, z0 + v) for (u, v) in prof]) for x in (-0.4, 0.4)], "x"), "Belly", 0, False)
    for s in (1, -1):
        P.obj("Scupper", box((s * 0.22, cy + 0.2, z0 + 0.04), (0.12, 0.012, 0.05)), "Dark", 0, False)
    # the body: a signal controller cabinet
    tz0, tz1, ty = R0 + 0.82, R0 + 1.5, cy
    P.obj("Cabinet", hull([(sx * w, ty + sy * d, z) for sx in (1, -1) for sy in (1, -1) for (w, d, z) in ((0.33, 0.21, tz0), (0.37, 0.25, tz0 + 0.06), (0.37, 0.25, tz1 - 0.04), (0.33, 0.21, tz1))]), "Metal", 0, False)
    fy = ty + 0.25
    P.obj("DoorSeam", box((0.0, fy + 0.002, (tz0 + tz1) * 0.5), (0.62, 0.006, 0.6)), "Dark", 0, False)
    P.obj("Door", box((0.0, fy + 0.006, (tz0 + tz1) * 0.5), (0.6, 0.006, 0.58)), "Metal", 0, False)
    for k in range(5):
        P.obj("Louvre", hull([(sx * 0.22, fy + 0.008 + dy, tz0 + 0.1 + k * 0.045 + dz) for sx in (1, -1) for (dy, dz) in ((0.0, 0.0), (0.0, 0.03), (0.022, 0.0))]), "Dark", 0, False)
    P.obj("Handle", box((0.24, fy + 0.02, tz0 + 0.18), (0.03, 0.03, 0.12)), "Dark", 0, False)
    P.obj("Lock", lathe([(0.02, 0.0), (0.02, 0.012), (0.0, 0.012)], 10, "y", (0.24, fy + 0.01, tz0 + 0.3)), "Lamp")
    # the breastplate: a barricade board, yellow with black chevrons pointing up
    bc = Vector((0, fy + 0.012, tz1 - 0.2)); W, H, w = 0.33, 0.24, 0.07
    P.obj("Board", tt_plate(bc, X, Z, Y, [(-W, -H / 2), (W, -H / 2), (W, H / 2), (-W, H / 2)], 0.02), "Base", 0, False)
    for side in (1, -1):
        for k in range(-6, 6):
            c0 = k * 2 * w
            band = [(0.0, c0), (0.0, c0 + w), (W, c0 + w - W), (W, c0 - W)]
            poly = tt_clip(band, 0.0, W, -H / 2, H / 2)
            if poly: P.obj("Chevron", tt_plate(bc, X * side, Z, Y, poly, 0.026), "Dark", 0, False)
    for s in (1, -1):   # the flashing barricade lamps
        lc = Vector((s * 0.29, ty + 0.12, tz1 + 0.07))
        P.obj("LampBox", box(tuple(lc), (0.12, 0.08, 0.12)), "Dark", 0, False)
        P.obj("LampLens", lathe([(0.05, 0.0), (0.05, 0.015), (0.03, 0.035), (0.0, 0.04)], 14, "y", tuple(lc + Vector((0, 0.04, 0)))), "Lamp")
    # shoulders: real traffic cones
    for s in (1, -1):
        tt_cone(Vector((s * 0.4, cy, tz1 - 0.06)), Vector((s * 0.45, 0, 1)), 0.55, P, "Cone")
    # arms: signal poles with bolted flanges
    for s in (1, -1):
        sh = Vector((s * 0.44, cy, tz1 - 0.18)); el = Vector((s * 0.6, cy + 0.2, tz0 + 0.12)); hd = Vector((s * 0.62, cy + 0.52, tz0 + 0.22))
        P.obj("Shoulder", ball(tuple(sh), (0.1, 0.1, 0.1), 12, 6), "Dark")
        P.obj("Arm", pipe([sh, el, hd], [0.06, 0.055, 0.055], 12), "Metal")
        d = (hd - el).normalized()
        P.obj("Flange", pipe([el - d * 0.02, el + d * 0.03], [0.095, 0.095], 14), "Metal")
        for k in range(6):
            a = 2 * math.pi * k / 6; e1 = d.orthogonal().normalized(); e2 = d.cross(e1)
            P.obj("Bolt", ball(tuple(el + d * 0.035 + (e1 * math.cos(a) + e2 * math.sin(a)) * 0.072), (0.014, 0.014, 0.014), 6, 3), "Dark")
        if s < 0:   # the STOP sign swung like a battle-axe
            P.obj("Fist", ball(tuple(hd), (0.085, 0.085, 0.08), 12, 6), "Dark")
            pd = Vector((-0.28, 0.12, 1.0)).normalized()
            p0, p1 = hd - pd * 0.5, hd + pd * 0.95
            P.obj("Post", pipe([p0, p1], [0.028, 0.028], 8), "Metal")
            P.obj("PostCap", ball(tuple(p1), (0.03, 0.03, 0.02), 8, 4), "Dark")
            for k in range(3):
                P.obj("Finger", xf(torus(0.045, 0.02, 0.0, 12, 5), pd.to_track_quat("Z", "Y").to_matrix(), tuple(hd + pd * (-0.05 + k * 0.05))), "Dark")
            sc = p1 - pd * 0.32 + Vector((-0.3, 0.07, 0))
            nrm = Y; u = -X; v = Z
            oct8 = lambda r: [(math.cos(math.pi / 8 + k * math.pi / 4) * r, math.sin(math.pi / 8 + k * math.pi / 4) * r) for k in range(8)]
            P.obj("StopBack", tt_plate(sc - nrm * 0.02, u, v, nrm, oct8(0.36), 0.02), "Metal", 0, False)
            P.obj("StopRim", tt_plate(sc, u, v, nrm, oct8(0.36), 0.008), "Belly", 0, False)
            P.obj("StopFace", tt_plate(sc + nrm * 0.008, u, v, nrm, oct8(0.325), 0.008), "Accent", 0, False)
            tt_word(P, "StopText", "STOP", sc + nrm * 0.016, u, v, nrm, 0.15, 0.03, 0.012, "Belly", 0.22)
            for dz in (0.16, -0.16):   # brackets clamping the sign to the post
                q = p1 - pd * (0.32 - dz)
                P.obj("Bracket", pipe([q, Vector((q.x - 0.12, sc.y - 0.02, q.z))], [0.022, 0.022], 6), "Dark")
        else:       # the speed camera
            cc = hd + Vector((0, 0.12, 0.02))
            P.obj("CamBox", hull([(cc.x + sx * 0.1, cc.y + y, cc.z + sz * h) for sx in (1, -1) for sz in (1, -1) for (y, h) in ((-0.2, 0.1), (0.18, 0.1), (0.2, 0.09))]), "Base", 0, False)
            P.obj("CamHood", hull([(cc.x + sx * 0.115, cc.y + y, cc.z + z) for sx in (1, -1) for (y, z) in ((-0.2, 0.1), (0.3, 0.1), (0.3, 0.115), (-0.2, 0.115), (0.3, 0.06))]), "Dark", 0, False)
            P.obj("CamBezel", lathe([(0.07, 0.0), (0.07, 0.03), (0.055, 0.04), (0.0, 0.04)], 16, "y", tuple(cc + Vector((0, 0.2, -0.03)))), "Dark")
            P.obj("CamLens", lathe([(0.045, 0.0), (0.03, 0.02), (0.0, 0.025)], 14, "y", tuple(cc + Vector((0, 0.24, -0.03)))), "Glow")
            P.obj("Flash", box(tuple(cc + Vector((0, 0.205, 0.055))), (0.14, 0.01, 0.04)), "Lamp", 0, False)
            P.obj("Fist", ball(tuple(hd), (0.085, 0.085, 0.08), 12, 6), "Dark")
            muzzle = cc + Vector((0, 0.28, -0.03))
    # neck: a steel mast with a clamp
    P.obj("Neck", pipe([(0, cy, tz1), (0, cy, tz1 + 0.1)], [0.07, 0.07], 12), "Metal")
    P.obj("Clamp", pipe([(0, cy, tz1 + 0.05), (0, cy, tz1 + 0.09)], [0.1, 0.1], 12), "Dark")
    # the jaw: the hanger bracket with a grille of steel fangs and the furnace glow behind
    jz0, jz1, jy = tz1 + 0.08, tz1 + 0.28, cy + 0.04
    P.obj("Jaw", hull([(sx * w, jy + sy * d, z) for sx in (1, -1) for sy in (1, -1) for (w, d, z) in ((0.17, 0.12, jz0), (0.21, 0.15, jz0 + 0.04), (0.21, 0.15, jz1))]), "Dark", 0, False)
    P.obj("Furnace", box((0, jy + 0.152, (jz0 + jz1) * 0.5 + 0.01), (0.34, 0.01, 0.1)), "Glow", 0, False)
    for k in range(7):
        x = -0.15 + k * 0.05
        P.obj("Fang", cone(Vector((x, jy + 0.16, jz1 - 0.035)), Vector((x, jy + 0.17, jz1 - 0.1 - 0.02 * (k % 2))), 0.02, 5), "Metal")
    for k in range(6):
        x = -0.125 + k * 0.05
        P.obj("Fang", cone(Vector((x, jy + 0.16, jz0 + 0.045)), Vector((x, jy + 0.17, jz0 + 0.1)), 0.018, 5), "Metal")
    P.obj("JawRail", box((0, jy + 0.16, jz1 - 0.025), (0.4, 0.02, 0.025)), "Metal", 0, False)
    P.obj("JawRail", box((0, jy + 0.16, jz0 + 0.035), (0.4, 0.02, 0.025)), "Metal", 0, False)
    # the head: a three-aspect signal on its backplate
    hz0, hy = jz1, cy
    sec = 0.3
    for k in range(3):
        z = hz0 + sec * k
        P.obj("Housing", hull([(sx * w, hy + sy * d, z + dz) for sx in (1, -1) for sy in (1, -1) for (w, d, dz) in ((0.17, 0.13, 0.005), (0.19, 0.15, 0.02), (0.19, 0.15, sec - 0.02), (0.17, 0.13, sec - 0.005))]), "Dark", 0, False)
    P.obj("HousingCap", box((0, hy, hz0 + 3 * sec + 0.015), (0.4, 0.32, 0.03)), "Dark", 0, False)
    P.obj("Hanger", pipe([(0, hy, hz0 + 3 * sec + 0.03), (0, hy, hz0 + 3 * sec + 0.11)], [0.035, 0.035], 8), "Metal")
    P.obj("HangerCap", box((0, hy, hz0 + 3 * sec + 0.12), (0.16, 0.08, 0.03)), "Metal", 0, False)
    by = hy - 0.15
    P.obj("Backplate", box((0, by - 0.012, hz0 + 1.5 * sec), (0.66, 0.02, 3 * sec + 0.16)), "Base", 0, False)
    P.obj("BackplateIn", box((0, by - 0.0, hz0 + 1.5 * sec), (0.56, 0.01, 3 * sec + 0.06)), "Dark", 0, False)
    fy = hy + 0.15
    for k, slot in enumerate(("Glass", "Lamp", "Glow")):
        lc = Vector((0, fy, hz0 + sec * k + sec * 0.5))
        P.obj("Door", xf(torus(0.125, 0.018, 0.0, 24, 6), Matrix.Rotation(math.radians(90), 3, "X"), tuple(lc + Vector((0, 0.005, 0)))), "Dark")
        prof = [(0.112, 0.0), (0.11, 0.012), (0.092, 0.012), (0.088, 0.022), (0.068, 0.022), (0.064, 0.03), (0.044, 0.03), (0.04, 0.036), (0.0, 0.04)]
        P.obj("Lens", lathe(prof, 24, "y", tuple(lc)), slot if k == 2 else ("Glass" if k == 0 else "Trim"))
        P.obj("Visor", tt_visor(lc + Vector((0, 0.01, 0)), 0.135, 0.2), "Dark", 0, False)
    rz = hz0 + sec * 2.5   # the brow: bent down into a V over the red eye
    for s in (1, -1):
        P.obj("Brow", tt_bar(Vector((0, fy + 0.2, rz)), X, Z, Y, (s * 0.165, 0.16), (s * 0.01, 0.05), 0.05, 0.035), "Dark", 0, False)
    P.part("Muzzle", ball(tuple(muzzle), (0.05, 0.03, 0.05), 8, 4), "Glow", tuple(muzzle))
    return P



# ================================================================= tycoon (2026-10-13 remake)
# ================================================================= the tycoon: helpers
# the torso of the tycoon: elliptic rings up z (z, rx, ry, cy) - a heavy villain's barrel, the belly pushed forward
TY_TORSO = [(-0.46, 0.46, 0.40, 0.0), (-0.30, 0.56, 0.48, 0.02), (-0.08, 0.64, 0.55, 0.05), (0.18, 0.67, 0.56, 0.06), (0.45, 0.66, 0.52, 0.04),
            (0.70, 0.62, 0.46, 0.01), (0.88, 0.52, 0.40, 0.0), (1.00, 0.34, 0.30, 0.0), (1.08, 0.22, 0.22, 0.02)]

def ty_ring(z):
    """(rx, ry, cy) of the torso at height z."""
    T = TY_TORSO
    if z <= T[0][0]: return T[0][1:]
    for a, b in zip(T, T[1:]):
        if z <= b[0]:
            t = (z - a[0]) / (b[0] - a[0]); s = 0.5 - 0.5 * math.cos(math.pi * t)
            return tuple(u + (v - u) * s for u, v in zip(a[1:], b[1:]))
    return T[-1][1:]

def ty_pt(a, z, off=0.0):
    """the torso surface at angle a from the front (0 = +y, + toward +x) and height z, pushed off it by off."""
    rx, ry, cy = ty_ring(z)
    p = Vector((math.sin(a) * rx, cy + math.cos(a) * ry, z))
    n = Vector((math.sin(a) / rx, math.cos(a) / ry, 0)).normalized()
    return p + n * off

def ty_torso(seg=56, step=0.035):
    bm = bmesh.new(); rings = []
    zs = []; z = TY_TORSO[0][0]
    while z < TY_TORSO[-1][0] - 1e-6: zs.append(z); z += step
    zs.append(TY_TORSO[-1][0])
    for z in zs:
        rings.append([bm.verts.new(ty_pt(2 * math.pi * i / seg, z)) for i in range(seg)])
    for r0, r1 in zip(rings, rings[1:]):
        for i in range(seg):
            j = (i + 1) % seg; bm.faces.new((r0[i], r0[j], r1[j], r1[i]))
    bm.faces.new(list(reversed(rings[0]))); bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm

def ty_ribbon(left, right, thick, nrm=None):
    """a solid strip between two rows of points (same count), thick along nrm (or each quad's own normal)."""
    bm = bmesh.new(); L = [Vector(p) for p in left]; R = [Vector(p) for p in right]
    tops, bots = [], []
    for i in range(len(L)):
        a = L[min(i + 1, len(L) - 1)] - L[max(i - 1, 0)]; b = R[i] - L[i]
        n = Vector(nrm) if nrm is not None else b.cross(a).normalized()
        tops.append((bm.verts.new(L[i] + n * thick * 0.5), bm.verts.new(R[i] + n * thick * 0.5)))
        bots.append((bm.verts.new(L[i] - n * thick * 0.5), bm.verts.new(R[i] - n * thick * 0.5)))
    for i in range(len(L) - 1):
        bm.faces.new((tops[i][0], tops[i][1], tops[i + 1][1], tops[i + 1][0]))
        bm.faces.new((bots[i + 1][0], bots[i + 1][1], bots[i][1], bots[i][0]))
        bm.faces.new((tops[i][0], tops[i + 1][0], bots[i + 1][0], bots[i][0]))
        bm.faces.new((bots[i][1], bots[i + 1][1], tops[i + 1][1], tops[i][1]))
    for (t0, t1), (b0, b1) in ((tops[0], bots[0]), (tops[-1], bots[-1])):
        bm.faces.new((t0, b0, b1, t1))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm

def ty_basis(fwd, up=(0, 0, 1)):
    """a rotation whose y axis is fwd and whose z axis is as near up as it can be."""
    y = Vector(fwd).normalized(); x = y.cross(Vector(up))
    if x.length < 1e-4: x = y.cross(Vector((1, 0, 0)))
    x.normalize(); z = x.cross(y).normalized()
    return Matrix((x, y, z)).transposed()

def ty_hand(P, c, fwd, side, name=None, hub=None, grip=0.075):
    """a white-gloved fist round a bar along fwd at c (the bar's axis), knuckles out to side; gold rings on two fingers."""
    M = ty_basis(fwd); s = side
    put = lambda bm: xf(bm, M, tuple(Vector(c)))
    obj = (lambda n, bm, p, ss=1: P.part(name, bm, p, hub, ss)) if name else (lambda n, bm, p, ss=1: P.obj(n, bm, p, ss))
    obj("Palm", put(ball((s * 0.06, -0.02, 0.0), (0.075, 0.12, 0.11), 12, 6)), "Belly")
    for k in range(4):   # four fingers curled round the bar, the little one at the back
        y = 0.075 - k * 0.05; r = 0.034 - 0.003 * k
        pts = [Vector((s * 0.08, y, 0.06)), Vector((-s * 0.0, y, grip + 0.03)), Vector((-s * 0.09, y, 0.02)), Vector((-s * 0.07, y, -0.06))]
        obj("Finger", put(pipe(pts, [r, r, r * 0.95, r * 0.8], 8)), "Belly", 0)
        if k in (0, 2):   # signet rings, a ruby on each
            q = pts[1] + Vector((0, 0, 0.004))
            obj("Ring", put(xf(torus(r + 0.006, 0.011, 0.0, 12, 4), Matrix.Rotation(math.radians(90), 3, "X"), tuple(q))), "Metal", 0)
            obj("RingJewel", put(ball(tuple(q + Vector((0, 0, r + 0.02))), (0.022, 0.022, 0.016), 8, 4)), "Accent", 0)
    obj("Thumb", put(pipe([(s * 0.05, 0.1, -0.06), (-s * 0.02, 0.14, -0.08), (-s * 0.08, 0.12, -0.05)], [0.038, 0.034, 0.028], 8)), "Belly", 0)
    for k in range(3):   # the three stitched lines on the back of the glove
        obj("Stitch", put(pipe([(s * 0.13, 0.05 - k * 0.04, 0.07), (s * 0.135, 0.05 - k * 0.04, -0.04)], [0.006, 0.006], 4)), "Dark", 0)

def ty_note(c, ang, tilt, w=0.30, h=0.135):
    """a banknote at c: cream paper, a gold border, a dark oval portrait and two corner numerals; turned ang about up, tilted by tilt."""
    R = Matrix.Rotation(ang, 3, "Z") @ Matrix.Rotation(tilt, 3, "X") @ Matrix.Rotation(tilt * 0.6, 3, "Y")
    c = Vector(c); n = R @ Vector((0, 0, 1))
    out = [(box(tuple(c), (w, h, 0.008), R), "Belly")]
    for (dx, dy, sx, sy) in ((0, h * 0.36, w * 0.86, 0.012), (0, -h * 0.36, w * 0.86, 0.012), (w * 0.42, 0, 0.012, h * 0.74), (-w * 0.42, 0, 0.012, h * 0.74)):
        for k in (1, -1):
            out.append((box(tuple(c + R @ Vector((dx, dy, k * 0.0055))), (sx, sy, 0.003), R), "Metal"))
    for k in (1, -1):
        e = ball((0, 0, 0), (0.034, 0.044, 0.003), 10, 3)
        out.append((xf(e, R, tuple(c + R @ Vector((0, 0, k * 0.006)))), "Dark"))
        for sx in (1, -1):
            out.append((box(tuple(c + R @ Vector((sx * w * 0.33, h * 0.18 * sx, k * 0.0058))), (0.035, 0.035, 0.003), R), "Metal"))
        ring = torus(0.042, 0.006, 0.0, 14, 3); xf(ring, R @ Matrix.Diagonal((1.0, 1.25, 1.0)), tuple(c + R @ Vector((0, 0, k * 0.006))))
        out.append((ring, "Metal"))
    return out


# ================================================================= the tycoon
def C_tycoon():
    """The master of downtown, THE TYCOON (2026-10-13, remade: "same as the alien bosses - realistic details, scarier, keep the cartoon
    shape"): the same sinister top-hatted billionaire with the cane, the gold, the monocle and the red bow tie, now a real man in a real
    evening suit - a heavy villain's build, a barrel chest and a belly pushed out over the trousers, broad shoulders. A black tailcoat cut
    away square at the waist in front, its peaked lapels faced in black satin, three gold buttons a side, a red rosebud in the left
    buttonhole and the two long tails hanging behind, blown back in the jet wash (they flap, SwayTails); a crimson waistcoat cut to a
    point, four gold buttons down it, a welt pocket on the left with a gold watch-chain swung across from the third button to it; a starched
    white shirt with a wing collar, two black studs and a red silk bow tie; black trousers with the satin stripe down the outer seam, patent
    shoes under white spats buttoned in gold. White gloves, a gold signet ring with a ruby on two fingers of each hand. A silk top hat with
    a curled brim and a black grosgrain band pinned with a gold clasp and a ruby, tipped forward over his eyes. The face of a villain: a
    heavy jaw and jowls, a big hooked nose, narrow eyes under heavy lids slanting down to the nose and black brows drawn into a frown, a
    gold monocle on the left eye on a gold chain to his lapel; a thin waxed pencil moustache curling up at the ends; a sneer, one corner of
    the mouth pulled up over his teeth with a gold one among them, and in that corner a fat cigar with a gold band, glowing at its tip.
    His right fist points his black lacquered cane at the player like a sword - a gold knob, a gold ferrule glowing at the tip where his
    shots leave from.
    He flies on a GOLDEN JETPACK: strapped to his back over the coat with black leather straps riveted in gold, crossed at the chest by a
    strap with a gold buckle, a backplate of black lacquer edged in gold with a gold dollar sign on it carries two polished gold turbines,
    each banded in black lacquer with a row of gold rivets on each band and three gold fins down its outer side; at the top of each an
    intake with a fan of eight blades round a pointed hub, turning fast (RotorL, RotorR); at the bottom a bell nozzle out of which pour a
    white-hot core and six tongues of orange flame. His left fist holds the control arm that swings forward from the pack at his hip - a
    lacquered arm on gold joints ending in a gold grip with a red button and the throttle lever. Out of the exhaust his money blows away
    behind him in two even streams of banknotes, each with its gold border, its portrait and its numerals, tumbling as they go."""
    P = Boss("tycoon", {"Base": ((0.045, 0.045, 0.055), 0.55), "Belly": ((0.95, 0.93, 0.87), 0.4), "Accent": ((0.62, 0.03, 0.06), 0.6),
                        "Trim": ((0.84, 0.64, 0.50), 0.45), "Glass": ((0.02, 0.02, 0.03), 0.95), "Dark": ((0.025, 0.022, 0.03), 0.35),
                        "Glow": ((1.0, 0.86, 0.45), 0.5), "Metal": ((0.98, 0.74, 0.25), 0.85), "Lamp": ((1.0, 0.45, 0.08), 0.8)})

    # ---- the torso: the black tailcoat over a crimson waistcoat, the shirt front, the trousers below the waist
    OPEN = 0.6   # half-angle of the coat's opening in front
    def wc_bottom(a): return -0.32 + 0.24 * min(1.0, abs(a) / OPEN)       # the waistcoat's pointed hem
    def torso_paint(c, n):
        rx, ry, cy = ty_ring(c.z); a = math.atan2(c.x / rx, (c.y - cy) / ry)
        if c.z > 0.56 and abs(a) < 0.07 + 0.62 * (c.z - 0.56) / 0.5: return "Belly"    # the shirt in the waistcoat's V
        if abs(a) < OPEN and wc_bottom(a) < c.z < 1.0: return "Accent"                 # the waistcoat
        if c.z < -0.1: return "Dark"                                                  # the trousers
        return "Base"
    P.obj("Torso", ty_torso(), torso_paint, 0)
    # black silk piping along the waistcoat's hem and up its fronts, and along the shirt's V
    hem = [ty_pt(a, wc_bottom(a) + 0.005, 0.012) for a in [OPEN * (i / 10.0 - 1) for i in range(21)]]
    P.obj("Piping", pipe(hem, [0.014] * len(hem), 5), "Base", 0)
    for s in (1, -1):
        vee = [ty_pt(s * (0.07 + 0.62 * (z - 0.56) / 0.5), z, 0.012) for z in [0.56 + 0.04 * i for i in range(11)]]
        P.obj("Piping", pipe(vee, [0.012] * len(vee), 5), "Base", 0)
    # the satin lapels: from the collar down the edge of the opening, peaked
    for s in (1, -1):
        inner, outer = [], []
        for i in range(19):
            z = 0.98 - i * 0.05
            w = 0.34 if z > 0.86 else (0.34 + (0.86 - z) / 0.08 * 0.2 if z > 0.78 else (0.12 if z > 0.74 else 0.3 - (0.74 - z) / 0.66 * 0.26))
            a0 = s * (OPEN - 0.02); a1 = s * (OPEN - 0.02 + w)
            inner.append(ty_pt(a0, z, 0.012)); outer.append(ty_pt(a1, z, 0.012))
        P.obj("Lapel", ty_ribbon(inner, outer, 0.025), "Glass", 0, False)
        P.obj("LapelEdge", pipe([ty_pt(s * (OPEN - 0.02), 0.98 - i * 0.05, 0.03) for i in range(19)], [0.012] * 19, 5), "Base", 0)
        for k in range(3):   # three gold buttons a side, worn open
            P.obj("CoatButton", ball(tuple(ty_pt(s * (OPEN + 0.18), 0.32 - k * 0.18, 0.012)), (0.035, 0.035, 0.035), 8, 4), "Metal")
    # a red rosebud in the left buttonhole
    rb = ty_pt(-(OPEN + 0.22), 0.8, 0.05)
    for k in range(3):
        P.obj("Rose", ball(tuple(rb + Vector((0.012 * math.cos(k * 2.1), 0.0, 0.012 * math.sin(k * 2.1)))), (0.04, 0.035, 0.045), 8, 4), "Accent")
    P.obj("RoseLeaf", hull([tuple(rb + Vector((0.0, 0.0, -0.04))), tuple(rb + Vector((0.07, 0.0, -0.09))), tuple(rb + Vector((0.03, 0.01, -0.06))), tuple(rb + Vector((0.04, -0.01, -0.07)))]), "Dark", 0, False)
    # the waistcoat: four gold buttons, a welt pocket, the watch-chain swung across to it
    for k in range(4): P.obj("WaistButton", ball(tuple(ty_pt(0.0, 0.46 - k * 0.16, 0.01)), (0.028, 0.028, 0.028), 8, 4), "Metal")
    P.obj("Pocket", ty_ribbon([ty_pt(-0.42, 0.06, 0.008), ty_pt(-0.2, 0.06, 0.008)], [ty_pt(-0.42, 0.03, 0.008), ty_pt(-0.2, 0.03, 0.008)], 0.012), "Dark", 0, False)
    a_from, z_from = 0.0, 0.14; a_to, z_to = -0.3, 0.06
    for k in range(18):   # the watch-chain: links, sagging in the middle
        t = k / 17; a = a_from + (a_to - a_from) * t; z = z_from + (z_to - z_from) * t - 0.1 * math.sin(math.pi * t)
        q = ty_pt(a, z, 0.02)
        L = torus(0.016, 0.005, 0.0, 8, 4)
        xf(L, Matrix.Rotation(math.radians(90 if k % 2 else 0), 3, "Z") @ Matrix.Rotation(math.radians(90), 3, "X"), tuple(q))
        P.obj("WatchChain", L, "Metal", 0, False)
    P.obj("Fob", ball(tuple(ty_pt(-0.2, -0.08, 0.03)), (0.035, 0.012, 0.045), 8, 4), "Metal")
    # the wing collar, the shirt studs, the red silk bow tie
    P.obj("Collar", lathe([(0.235, 0.98), (0.245, 1.06), (0.235, 1.13)], 24, "z", (0, 0.03, 0)), "Belly")
    for s in (1, -1):
        P.obj("CollarWing", hull([(s * 0.03, 0.28, 1.06), (s * 0.12, 0.25, 1.03), (s * 0.08, 0.27, 0.99), (s * 0.03, 0.26, 1.06), (s * 0.12, 0.23, 1.03)]), "Belly", 0, False)
    for k in range(2): P.obj("Stud", ball(tuple(ty_pt(0.0, 0.66 + k * 0.14, 0.008)), (0.022, 0.012, 0.022), 8, 4), "Dark")
    bt = Vector((0, 0.31, 1.0)); BW = 1.35
    for s in (1, -1):
        P.obj("Bow", hull([tuple(bt + Vector((s * x * BW, y, z * BW))) for x, y, z in ((0.03, 0.02, 0.025), (0.03, 0.02, -0.025), (0.03, -0.03, 0.025), (0.03, -0.03, -0.025),
                                                                                    (0.17, 0.02, 0.07), (0.18, 0.02, -0.06), (0.17, -0.03, 0.065), (0.18, -0.03, -0.055), (0.19, 0.0, 0.0))]), "Accent", 0, False)
        P.obj("BowFold", pipe([bt + Vector((s * 0.05, 0.02, 0.0)), bt + Vector((s * 0.14, 0.025, 0.02))], [0.008, 0.004], 4), "Dark", 0)
    P.obj("BowKnot", ball(tuple(bt + Vector((0, 0.025, 0))), (0.055, 0.04, 0.06), 10, 5), "Accent")
    # broad shoulders padded under the coat
    for s in (1, -1):
        P.obj("Shoulder", ball((s * 0.56, -0.02, 0.84), (0.23, 0.28, 0.18), 16, 8), "Base", 0)

    # ---- the tails, blown back between the turbines (they flap)
    hub = (0.0, -0.44, -0.08)
    for s in (1, -1):
        left, right = [], []
        for i in range(9):
            t = i / 8; z = -0.08 - 0.95 * t; y = -0.44 - 0.75 * t ** 1.2
            x0 = s * (0.03 + 0.01 * t); x1 = s * (0.22 - 0.05 * t)
            if i == 8: x0 = s * 0.07   # the swallow-cut end
            left.append((x0, y, z)); right.append((x1, y, z))
        P.part("SwayTails", ty_ribbon(left, right, 0.03), lambda c, n: "Glass" if n.y > 0.4 else "Base", hub, 0, False)

    # ---- the legs: black trousers with the satin stripe, white spats over patent shoes
    for s in (1, -1):
        hip, knee, ank = Vector((s * 0.25, 0.02, -0.3)), Vector((s * 0.28, 0.14, -0.96)), Vector((s * 0.26, -0.04, -1.48))
        P.obj("Leg", pipe([hip, (hip + knee) * 0.5, knee, (knee + ank) * 0.5, ank], [0.24, 0.21, 0.18, 0.16, 0.14], 16),
              lambda c, n, s=s: "Glass" if n.x * s > 0.93 else "Dark", 0)
        P.obj("Cuff", pipe([ank + Vector((0, 0, 0.04)), ank - Vector((0, 0.0, 0.04))], [0.155, 0.155], 16), "Dark", 0)
        P.obj("Spat", pipe([ank - Vector((0, 0.0, 0.02)), ank - Vector((0, -0.02, 0.17))], [0.13, 0.12], 14), "Belly", 0)
        for k in range(3): P.obj("SpatButton", ball(tuple(ank + Vector((s * 0.125, 0.0, -0.05 - k * 0.045))), (0.016, 0.016, 0.016), 6, 3), "Metal")
        heel = ank + Vector((0, -0.06, -0.2)); toe = ank + Vector((0, 0.22, -0.33))
        P.obj("Shoe", pipe([heel, heel + (toe - heel) * 0.35, heel + (toe - heel) * 0.75, toe], [0.1, 0.11, 0.095, 0.0], 12), "Glass", 1)
        P.obj("Sole", pipe([heel + Vector((0, 0, -0.06)), toe + Vector((0, -0.03, -0.035))], [0.06, 0.04], 8), "Dark", 0)

    # ---- the head: a heavy jaw, jowls, a hooked nose, narrow eyes, a sneer with a gold tooth, a cigar
    H = Vector((0, 0.06, 1.46))
    P.obj("Neck", pipe([(0, 0.02, 1.02), (0, 0.04, 1.2)], [0.21, 0.21], 16), "Trim", 0)
    P.obj("Skull", ball(tuple(H), (0.39, 0.37, 0.43), 28, 14), "Trim", 0)
    P.obj("Jowls", ball(tuple(H + Vector((0, 0.06, -0.2))), (0.38, 0.31, 0.24), 24, 12), "Trim", 0)
    P.obj("Chin", ball(tuple(H + Vector((0, 0.26, -0.29))), (0.15, 0.09, 0.09), 14, 7), "Trim", 0)
    hair = lathe([(0.0, -0.5), (0.4, -0.05), (0.405, 0.12), (0.37, 0.28), (0.0, 0.3)], 28, "z", tuple(H + Vector((0, -0.035, 0))))
    for v in hair.verts: v.co.y = H.y - 0.035 + (v.co.y - H.y + 0.035) * 0.97
    bmesh.ops.delete(hair, geom=[f for f in hair.faces if f.calc_center_median().y > H.y - 0.08 or f.calc_center_median().z < H.z - 0.14], context="FACES")
    P.obj("Hair", hair, "Dark", 0)
    for s in (1, -1):
        P.obj("Ear", ball(tuple(H + Vector((s * 0.38, -0.02, 0.02))), (0.05, 0.1, 0.13), 10, 5), "Trim", 0)
        P.obj("Sideburn", pipe([H + Vector((s * 0.37, 0.06, 0.2)), H + Vector((s * 0.385, 0.07, 0.07)), H + Vector((s * 0.37, 0.09, -0.04))], [0.035, 0.03, 0.012], 6), "Dark", 0)
        P.obj("Cheek", ball(tuple(H + Vector((s * 0.2, 0.28, -0.06))), (0.12, 0.08, 0.08), 12, 6), "Trim", 0)
    P.obj("Nose", pipe([H + Vector((0, 0.33, 0.1)), H + Vector((0, 0.44, 0.02)), H + Vector((0, 0.47, -0.05)), H + Vector((0, 0.43, -0.1))], [0.055, 0.07, 0.07, 0.045], 12), "Trim", 1)
    for s in (1, -1):
        P.obj("Nostril", ball(tuple(H + Vector((s * 0.05, 0.41, -0.1))), (0.035, 0.03, 0.025), 8, 4), "Trim", 0)
        e = H + Vector((s * 0.15, 0.31, 0.13))
        P.obj("EyeWhite", ball(tuple(e), (0.085, 0.04, 0.034), 12, 6), "Belly", 0)
        P.obj("Pupil", ball(tuple(e + Vector((-s * 0.012, 0.03, 0.0))), (0.03, 0.014, 0.028), 8, 4), "Dark", 0)
        lid = ball((0, 0, 0), (0.105, 0.055, 0.04), 12, 6)   # the heavy upper lid, slanting down to the nose
        xf(lid, Matrix.Rotation(math.radians(s * 14), 3, "Y"), tuple(e + Vector((0, 0.005, 0.03))))
        P.obj("Lid", lid, "Trim", 0)
        P.obj("Bag", pipe([e + Vector((-s * 0.06, 0.02, -0.045)), e + Vector((s * 0.02, 0.025, -0.055)), e + Vector((s * 0.08, 0.01, -0.04))], [0.012, 0.014, 0.01], 6), "Trim", 0)
        P.obj("Brow", pipe([H + Vector((s * 0.04, 0.37, 0.18)), H + Vector((s * 0.15, 0.36, 0.22)), H + Vector((s * 0.28, 0.3, 0.27))], [0.035, 0.04, 0.02], 8), "Dark", 0)
    # the monocle on his left eye, on a chain to the lapel
    me = H + Vector((-0.15, 0.36, 0.13))
    P.obj("Monocle", xf(torus(0.1, 0.014, 0.0, 24, 6), Matrix.Rotation(math.radians(90), 3, "X"), tuple(me)), "Metal")
    P.obj("MonocleGlint", ball(tuple(me + Vector((0.05, 0.01, 0.06))), (0.018, 0.008, 0.018), 6, 3), "Lamp")
    P.part("ClothDetail", pipe(bez(me + Vector((-0.09, 0.0, -0.05)), me + Vector((-0.24, 0.0, -0.3)), Vector((-0.42, 0.42, 0.95)), ty_pt(-(OPEN + 0.14), 0.88, 0.03), 10),
                                [0.008] * 11, 4), "Metal", (0, 0, 0), 0)
    # the sneer: the mouth pulled up at his right corner, upper teeth with one gold, the pencil moustache
    m0 = H + Vector((0.02, 0.35, -0.13)); tilt = Matrix.Rotation(math.radians(10), 3, "Y")
    mo = ball((0, 0, 0), (0.15, 0.04, 0.035), 14, 6); xf(mo, tilt, tuple(m0)); P.obj("Mouth", mo, "Dark", 0)
    for k in range(7):
        x = (k - 3) * 0.036; p = m0 + tilt @ Vector((x, 0.03, 0.014))
        P.obj("Tooth", box(tuple(p), (0.03, 0.02, 0.032), tilt), "Metal" if k == 4 else "Belly", 0, False)
    P.obj("Lip", pipe([m0 + tilt @ Vector((-0.16, 0.0, 0.0)), m0 + tilt @ Vector((0.0, 0.035, 0.04)), m0 + tilt @ Vector((0.17, 0.0, 0.01))], [0.014, 0.02, 0.012], 6), "Trim", 0)
    for s in (1, -1):
        P.obj("Moustache", pipe([H + Vector((s * 0.01, 0.42, -0.08)), H + Vector((s * 0.1, 0.42, -0.085)), H + Vector((s * 0.2, 0.38, -0.06)), H + Vector((s * 0.25, 0.34, -0.0)), H + Vector((s * 0.23, 0.33, 0.04))],
                                [0.022, 0.022, 0.016, 0.009, 0.0], 6), "Dark", 0)
    cg0 = m0 + tilt @ Vector((0.13, 0.02, 0.0)); cd = Vector((0.45, 0.85, -0.18)).normalized()
    P.obj("Cigar", pipe([cg0, cg0 + cd * 0.08, cg0 + cd * 0.36], [0.026, 0.034, 0.034], 10), "Dark", 0)
    P.obj("CigarBand", pipe([cg0 + cd * 0.1, cg0 + cd * 0.14], [0.037, 0.037], 10), "Metal", 0)
    P.obj("CigarAsh", pipe([cg0 + cd * 0.36, cg0 + cd * 0.38], [0.034, 0.033], 10), "Lamp", 0)
    # the silk top hat, tipped forward
    hatM = Matrix.Rotation(math.radians(9), 3, "X"); hc = H + Vector((0, 0.02, 0.3))
    brim = lathe([(0.0, 0.0), (0.34, 0.0), (0.53, 0.0), (0.56, 0.03), (0.53, 0.05), (0.34, 0.03), (0.0, 0.03)], 36, "z")
    for v in brim.verts:
        v.co.y *= 0.88; v.co.z += 0.08 * (v.co.x / 0.56) ** 2   # the brim curls up at the sides
    P.obj("Brim", xf(brim, hatM, tuple(hc)), "Glass", 0)
    P.obj("Crown", xf(lathe([(0.0, 0.0), (0.33, 0.0), (0.31, 0.4), (0.34, 0.78), (0.0, 0.79)], 36, "z"), hatM @ Matrix.Diagonal((1.0, 0.88, 1.0)), tuple(hc)), "Glass", 0)
    P.obj("HatBand", xf(lathe([(0.335, 0.03), (0.33, 0.2), (0.0, 0.2)], 36, "z"), hatM @ Matrix.Diagonal((1.0, 0.88, 1.0)), tuple(hc + Vector((0, 0, -0.01)))), "Base", 0)
    clasp = hc + hatM @ Vector((0, 0.3, 0.11))
    P.obj("HatClasp", xf(box((0, 0, 0), (0.12, 0.03, 0.09)), hatM, tuple(clasp)), "Metal", 0, False)
    P.obj("HatRuby", ball(tuple(clasp + hatM @ Vector((0, 0.02, 0))), (0.03, 0.02, 0.03), 8, 4), "Accent")

    # ---- the right arm: pointing the cane at the player like a sword
    sh = Vector((0.66, 0.0, 0.82)); el = Vector((0.98, 0.22, 0.48)); wr = Vector((0.96, 0.66, 0.36))
    P.obj("ArmR", pipe([sh, (sh + el) * 0.5, el, (el + wr) * 0.5, wr], [0.18, 0.165, 0.15, 0.14, 0.12], 14), "Base", 0)
    P.obj("ShirtCuffR", pipe([wr - (wr - el).normalized() * 0.02, wr + (wr - el).normalized() * 0.05], [0.125, 0.12], 14), "Belly", 0)
    P.obj("CufflinkR", ball(tuple(wr + Vector((0.12, 0.02, 0.0))), (0.02, 0.025, 0.025), 6, 3), "Metal")
    cd = Vector((0.0, 1.0, -0.38)).normalized(); hand = wr + (wr - el).normalized() * 0.12
    knob = hand - cd * 0.2; tip = hand + cd * 0.8
    P.obj("Cane", pipe([knob, tip], [0.028, 0.024], 10), "Glass", 0)
    P.obj("CaneKnob", ball(tuple(knob - cd * 0.05), (0.06, 0.06, 0.06), 12, 6), "Metal", 0)
    P.obj("CaneCollar", pipe([knob, knob + cd * 0.04], [0.035, 0.035], 10), "Metal", 0)
    P.obj("Ferrule", pipe([tip - cd * 0.12, tip], [0.028, 0.022], 10), "Metal", 0)
    ty_hand(P, hand, cd, 1)
    P.part("Muzzle", ball(tuple(tip + cd * 0.02), (0.035, 0.035, 0.035), 8, 4), "Lamp", tuple(tip + cd * 0.02))

    # ---- the jetpack: a lacquered backplate, two gold turbines, the fans, the flames, the control arm
    BY = -0.62   # the back of the backplate
    plate = box((0, -0.56, 0.45), (0.78, 0.12, 1.0)); P.obj("Backplate", plate, "Glass", 0, False)
    for (c, s) in (((0, -0.56, 0.96), (0.82, 0.14, 0.04)), ((0, -0.56, -0.06), (0.82, 0.14, 0.04)), ((0.4, -0.56, 0.45), (0.04, 0.14, 1.06)), ((-0.4, -0.56, 0.45), (0.04, 0.14, 1.06))):
        P.obj("PlateTrim", box(c, s), "Metal", 0, False)
    # a gold dollar sign on the backplate
    sc = [(0.11, 0.62), (0.0, 0.66), (-0.1, 0.6), (-0.08, 0.5), (0.0, 0.46), (0.08, 0.42), (0.1, 0.32), (0.0, 0.26), (-0.11, 0.3)]
    P.obj("Dollar", pipe([Vector((x, BY - 0.01, z)) for x, z in sc], [0.022] * len(sc), 6), "Metal", 0)
    P.obj("DollarBar", pipe([(0.0, BY - 0.01, 0.72), (0.0, BY - 0.01, 0.2)], [0.018, 0.018], 6), "Metal", 0)
    TX = 0.44; TY = -0.84
    for s in (1, -1):
        c = (s * TX, TY, 0.0)
        prof = [(0.0, -0.5), (0.12, -0.5), (0.17, -0.6), (0.19, -0.62), (0.15, -0.44), (0.21, -0.38), (0.22, -0.3), (0.22, -0.1), (0.225, 0.02), (0.225, 0.16), (0.22, 0.17), (0.22, 0.49), (0.225, 0.5), (0.225, 0.64), (0.22, 0.65), (0.22, 0.8), (0.245, 0.86), (0.245, 0.93), (0.205, 0.95), (0.19, 0.88), (0.0, 0.88)]
        def tpaint(cc, n, s=s):
            if cc.z < -0.36: return "Metal"
            if 0.86 < cc.z: return "Metal"
            if cc.z > 0.82 and math.hypot(cc.x - s * TX, cc.y - TY) < 0.2: return "Dark"   # the intake's throat
            return "Glass" if (0.02 < cc.z < 0.16) or (0.5 < cc.z < 0.64) else "Metal"
        P.obj("Turbine", lathe(prof, 32, "z", c), tpaint, 0)
        for zb in (0.02, 0.16, 0.5, 0.64):   # rows of rivets along the lacquer bands
            for k in range(14):
                a = 2 * math.pi * k / 14
                P.obj("Rivet", ball((s * TX + math.cos(a) * 0.225, TY + math.sin(a) * 0.225, zb), (0.012, 0.012, 0.012), 5, 3), "Metal", 0)
        for k in range(3):   # three gold fins down its outer side
            a = math.radians(-35 + 35 * k) if s > 0 else math.radians(180 + 35 - 35 * k)
            d = Vector((math.cos(a), math.sin(a), 0))
            b0 = Vector((s * TX, TY, 0)) + d * 0.2
            P.obj("Fin", hull([tuple(b0 + Vector((0, 0, -0.25))), tuple(b0 + Vector((0, 0, 0.7))), tuple(b0 + d * 0.12 + Vector((0, 0, 0.55))), tuple(b0 + d * 0.12 + Vector((0, 0, -0.15))),
                               tuple(b0 + d.cross(Vector((0, 0, 1))) * 0.012 + Vector((0, 0, 0.2)))]), "Metal", 0, False)
        for zb in (0.12, 0.62):   # the struts to the backplate
            P.obj("Strut", pipe([(s * 0.3, -0.6, zb), (s * TX * 0.7, TY + 0.1, zb)], [0.04, 0.04], 8), "Metal", 0)
        # the intake fan: eight twisted blades round a pointed hub (turns fast)
        hubp = (s * TX, TY, 0.9)
        nm = "RotorR" if s > 0 else "RotorL"
        P.part(nm, cone(hubp, (s * TX, TY, 1.0), 0.06, 12), "Metal", hubp, 0)
        for k in range(8):
            a = 2 * math.pi * k / 8
            d = Vector((math.cos(a), math.sin(a), 0)); t = Vector((-math.sin(a), math.cos(a), 0))
            r0, r1 = 0.05, 0.19
            pts = [Vector(hubp) + d * r0 + t * 0.03 + Vector((0, 0, 0.02)), Vector(hubp) + d * r1 + t * 0.04 + Vector((0, 0, 0.01)),
                   Vector(hubp) + d * r1 - t * 0.03 - Vector((0, 0, 0.02)), Vector(hubp) + d * r0 - t * 0.03 - Vector((0, 0, 0.03))]
            P.part(nm, hull([tuple(p) for p in pts] + [tuple(pts[0] + Vector((0, 0, 0.008))), tuple(pts[1] + Vector((0, 0, 0.008)))]), "Metal", hubp, 0, False)
        # the flames: a white-hot core and six tongues of orange flame round it
        nz = Vector((s * TX, TY, -0.6))
        P.obj("FlameCore", pipe([nz, nz + Vector((0, -0.02, -0.3)), nz + Vector((0, -0.05, -0.62))], [0.12, 0.1, 0.0], 12), "Glow", 0)
        for k in range(6):
            a = 2 * math.pi * k / 6 + 0.3; d = Vector((math.cos(a), math.sin(a), 0))
            L = 0.55 + 0.18 * (k % 2)
            pts = [nz + d * 0.1, nz + d * 0.15 + Vector((0, -0.02, -0.16)), nz + d * 0.11 + Vector((0, -0.04, -L * 0.6)), nz + d * 0.05 + Vector((0, -0.06, -L))]
            P.obj("Flame", pipe(pts, [0.07, 0.075, 0.05, 0.0], 8), "Lamp", 0)
        # the money: a stream of banknotes blowing back and out of each exhaust, evenly, tumbling
        path = bez(nz + Vector((s * 0.06, -0.15, -0.6)), nz + Vector((s * 0.2, -0.45, -0.95)), nz + Vector((s * 0.32, -0.6, -1.0)), nz + Vector((s * 0.48, -0.78, -1.2)), 6)
        for k, p in enumerate(path):
            for bm, slot in ty_note(tuple(p), s * (0.4 + 0.6 * k), 0.5 + 0.5 * k, 0.27 + 0.012 * k, 0.12 + 0.005 * k):
                P.part("Cloth", bm, slot, (0, 0, 0), 0, False)
    # the shoulder straps, riveted, and the chest strap with its gold buckle
    for s in (1, -1):
        path = [Vector((s * 0.26, -0.6, 0.92)), Vector((s * 0.34, -0.3, 1.06)), Vector((s * 0.36, 0.05, 1.08))] + [ty_pt(s * a, z, 0.02) for a, z in ((0.62, 0.98), (0.5, 0.86), (0.46, 0.72), (0.44, 0.56))]
        P.obj("Strap", pipe(path, [0.035] * len(path), 6), "Dark", 0)
        for p in path[1:]: P.obj("StrapRivet", ball(tuple(p + Vector((0, 0.0, 0.035)) if p.y < 0.1 else p + (p - Vector((0, 0, p.z))).normalized() * 0.03), (0.016, 0.016, 0.016), 5, 3), "Metal", 0)
    P.obj("ChestStrap", pipe([ty_pt(a, 0.56, 0.022) for a in (-0.44, -0.25, 0.0, 0.25, 0.44)], [0.03] * 5, 6), "Dark", 0)
    bk = ty_pt(0.0, 0.56, 0.05)
    P.obj("Buckle", box(tuple(bk), (0.14, 0.03, 0.1)), "Metal", 0, False)
    P.obj("BuckleJewel", ball(tuple(bk + Vector((0, 0.02, 0))), (0.03, 0.015, 0.03), 8, 4), "Accent")
    # the left arm on the control arm: the arm swings forward from the pack at his hip to a gold grip
    pv = Vector((-0.52, -0.42, -0.04)); j1 = Vector((-0.86, -0.12, -0.02)); gp = Vector((-0.96, 0.32, 0.1))
    P.obj("CtrlArm", pipe([pv, j1], [0.045, 0.045], 10), "Glass", 0)
    P.obj("CtrlArm", pipe([j1, gp - Vector((0, 0, 0.09))], [0.04, 0.04], 10), "Glass", 0)
    for j in (pv, j1): P.obj("CtrlJoint", ball(tuple(j), (0.07, 0.07, 0.07), 10, 5), "Metal", 0)
    P.obj("Grip", pipe([gp - Vector((0, 0, 0.12)), gp + Vector((0, 0, 0.14))], [0.045, 0.045], 10), "Metal", 0)
    P.obj("GripButton", ball(tuple(gp + Vector((0, 0, 0.16))), (0.035, 0.035, 0.025), 8, 4), "Accent")
    P.obj("Throttle", pipe([gp + Vector((0, 0.04, 0.06)), gp + Vector((0, 0.13, 0.0))], [0.014, 0.01], 6), "Metal", 0)
    sh = Vector((-0.66, 0.0, 0.82)); el = Vector((-1.0, -0.06, 0.4)); wr = gp + Vector((-0.02, -0.12, 0.02))
    P.obj("ArmL", pipe([sh, (sh + el) * 0.5, el, (el + wr) * 0.5, wr], [0.18, 0.165, 0.15, 0.14, 0.12], 14), "Base", 0)
    P.obj("ShirtCuffL", pipe([wr - (wr - el).normalized() * 0.02, wr + (wr - el).normalized() * 0.05], [0.125, 0.12], 14), "Belly", 0)
    ty_hand(P, gp + Vector((0, 0, 0.02)), (0, 0, 1), -1)
    return P


BOSSES = [("chopper", C_chopper), ("pigeon", C_pigeon), ("titan", C_titan), ("kong", C_kong), ("tycoon", C_tycoon)]

if __name__ == "__main__":
    os.makedirs(AB.OUT, exist_ok=True)
    for bid, fn in BOSSES:
        if ONLY and bid not in ONLY: continue
        fn().finish()
    print("DONE")
