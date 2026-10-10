# Sky Squad, the sea world's five bosses (2026-10-10: "bosses for Sky Sea - something completely professional"). Built from code like the
# alien bosses (alien_bosses.py lends its Boss class and shapes): the thunder fortress, the sky galleon, the hurricane gunship, the abyss
# leviathan and the poseidon battleship.
# Run: blender -b -P Tools/blender/sea_bosses.py -- <out dir> [export] [ids,comma,separated]
#      writes Boss_<id>.fbx per boss (with "export") and two previews each.
# Same conventions as alien_bosses.py: +Y nose, +Z up, +X right; moving parts are their own objects named for how they move: "Prop*" spin
# about the nose, "Rotor*" about up, "TailRotor" about the wing axis (fast, with the blur disc), "Spin*" turn slowly about up, "Flap*" rock
# about the nose axis, "Sway*" about the wing axis; "Cloth" (sails, fins, frills: thin two-sided sheets) stays still but apart from the body, so
# the toon outline drawn round the body does not cover it; "Muzzle" is where his shots leave from.
import bpy, bmesh, math, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mathutils import Vector, Matrix
import enemy_planes as EP
from enemy_planes import loft, sweep, lathe, box, hull, tube, mirror_x, airfoil
import alien_bosses as AB
from alien_bosses import Boss, xf, ball, pipe, cone, bez, torus, sheet, grow, ang

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ONLY = argv[2].split(",") if len(argv) > 2 and argv[2] else None


def spline(pts, n):
    """a Catmull-Rom curve through pts, n samples per span."""
    P = [Vector(p) for p in pts]
    P = [P[0] * 2 - P[1]] + P + [P[-1] * 2 - P[-2]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for k in range(n):
            t = k / n
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(P[-2])
    return out

def grid(corner, u, v, nu, nv, bulge=Vector((0, 0, 0)), thick=0.025):
    """a cloth panel corner + u*s + v*t, bowed by bulge*sin(pi s)*sin(pi t), two-sided."""
    corner, u, v = Vector(corner), Vector(u), Vector(v)
    nrm = u.cross(v).normalized()
    bm = bmesh.new()
    def layer(off):
        return [[bm.verts.new(corner + u * (i / nu) + v * (j / nv) + bulge * math.sin(math.pi * i / nu) * math.sin(math.pi * j / nv) + nrm * off) for j in range(nv + 1)] for i in range(nu + 1)]
    A = layer(thick * 0.5); B = layer(-thick * 0.5)
    for i in range(nu):
        for j in range(nv):
            bm.faces.new((A[i][j], A[i + 1][j], A[i + 1][j + 1], A[i][j + 1]))
            bm.faces.new((B[i][j], B[i][j + 1], B[i + 1][j + 1], B[i + 1][j]))
    return bm


# ================================================================= 1. the thunder fortress
def S_fortress():
    """A six-engine heavy bomber: a long navy fuselage with a glazed nose, a great straight wing, six spinning props, gun turrets top,
    bottom and tail, a twin-gun chin turret, yellow squadron bands and a red nose ring."""
    P = Boss("fortress", {"Base": ((0.30, 0.38, 0.48), 0.5), "Belly": ((0.80, 0.83, 0.86), 0.45), "Accent": ((0.98, 0.76, 0.16), 0.55),
                          "Trim": ((0.78, 0.12, 0.10), 0.5), "Glass": ((0.35, 0.55, 0.68), 0.95), "Dark": ((0.06, 0.07, 0.09), 0.4),
                          "Glow": ((1.0, 0.55, 0.15), 0.5), "Metal": ((0.55, 0.57, 0.6), 0.7), "Lamp": ((1.0, 0.25, 0.2), 0.8)})
    def fus(c, n):
        if 2.25 < c.y < 2.42: return "Trim"
        if -1.05 < c.y < -0.8: return "Accent"
        return "Belly" if c.z < -0.12 else "Base"
    P.obj("Fuselage", loft([(2.6, 0.32, 0.34, 0, 0.0), (2.2, 0.44, 0.46, 0, 0.0), (0.5, 0.47, 0.5, 0, 0.02), (-1.2, 0.42, 0.44, 0, 0.05),
                            (-2.4, 0.2, 0.22, 0, 0.18), (-2.9, 0.08, 0.1, 0, 0.26)], 18), fus, 1)
    P.obj("NoseGlass", lathe([(0.0, 2.98), (0.17, 2.92), (0.27, 2.78), (0.32, 2.6)], 16, "y"), "Glass")
    for k in range(4):   # the glazing frames
        P.obj("Frame", box((0, 2.66 + k * 0.08, 0.0), (0.66 - k * 0.12, 0.015, 0.66 - k * 0.12)), "Dark", 0, False)
    P.obj("Canopy", loft([(1.55, 0.05, 0.04, 0, 0.42), (1.75, 0.26, 0.16, 0, 0.47), (2.15, 0.24, 0.14, 0, 0.44), (2.3, 0.05, 0.04, 0, 0.38)], 14), "Glass", 1)
    wpaint = lambda c, n: "Belly" if n.z < -0.3 else ("Accent" if abs(c.x) > 3.35 else ("Trim" if 2.0 < abs(c.x) < 2.12 else "Base"))
    P.wing([(0.4, 0.95, -0.3, 0.22, 0.05), (2.0, 0.68, -0.15, 0.15, 0.09), (3.7, 0.32, -0.04, 0.07, 0.14)], wpaint)
    for s in (1, -1):
        for x in (0.95, 1.75, 2.55):
            X = s * x; le = 0.95 - (x - 0.4) * 0.19
            P.obj("Nacelle", loft([(le + 0.42, 0.13, 0.13, X, -0.06), (le + 0.3, 0.19, 0.2, X, -0.07), (le - 0.6, 0.16, 0.17, X, -0.07), (le - 1.05, 0.04, 0.05, X, -0.04)], 12),
                  lambda c, n, y0=le + 0.36: "Dark" if c.y > y0 else ("Belly" if n.z < -0.3 else "Base"), 1)
            P.obj("Exhaust", pipe([(X + s * 0.12, le - 0.2, -0.16), (X + s * 0.14, le - 0.45, -0.16)], [0.04, 0.035], 6), "Glow")
            P.prop((X, le + 0.5, -0.06), 0.46, 4, spinner="Accent", spinner_len=0.18)
    P.fin([(0.0, -1.55, -2.75, 0.13), (1.1, -2.25, -2.95, 0.09), (1.32, -2.45, -2.95, 0.06)], 0.0, 0.25, 0, lambda c, n: "Accent" if c.z > 1.25 else ("Trim" if 0.9 < c.z < 1.0 else "Base"))
    P.wing([(0.1, -1.95, -2.85, 0.1, 0.24), (1.55, -2.3, -2.82, 0.06, 0.24)], name="Stab")
    def turret(c, guns_to, glass_r=0.21, up=True):
        c = Vector(c)
        prof = [(0.0, glass_r * 0.95), (glass_r * 0.7, glass_r * 0.8), (glass_r, 0.0)] if up else [(glass_r, 0.0), (glass_r * 0.7, -glass_r * 0.8), (0.0, -glass_r * 0.95)]
        P.obj("Turret", lathe(prof, 14, "z", tuple(c)), "Glass")
        for s2 in (1, -1):
            o = c + Vector((s2 * 0.07, 0, 0.06 if up else -0.06))
            P.obj("TurretGun", pipe([o, o + Vector(guns_to)], [0.025, 0.02], 6), "Dark")
    turret((0, 1.05, 0.46), (0, 0.55, 0.05))
    turret((0, -0.55, 0.47), (0, 0.55, 0.05))
    turret((0, 0.15, -0.47), (0, 0.55, -0.02), up=False)
    P.obj("TailGlass", lathe([(0.0, -3.1), (0.1, -3.05), (0.12, -2.9)], 10, "y", (0, 0, 0.26)), "Glass")
    for s2 in (1, -1): P.obj("TailGun", pipe([(s2 * 0.05, -3.0, 0.26), (s2 * 0.05, -3.35, 0.26)], [0.02, 0.02], 6), "Dark")
    # the chin turret: the boss's guns
    P.obj("ChinTurret", lathe([(0.24, 0.0), (0.2, -0.16), (0.0, -0.22)], 14, "z", (0, 2.35, -0.3)), "Metal")
    for s2 in (1, -1):
        P.obj("ChinGun", pipe([(s2 * 0.08, 2.4, -0.42), (s2 * 0.08, 3.05, -0.42)], [0.035, 0.03], 8), "Dark")
    P.obj("Lamp", ball((0, -0.2, 0.52), (0.05, 0.05, 0.04), 6, 3), "Lamp")
    P.part("Muzzle", ball((0, 3.12, -0.42), (0.09, 0.05, 0.07), 8, 4), "Glow", (0, 3.12, -0.42))
    return P


# ================================================================= 2. the sky galleon
def S_galleon():
    """A flying galleon: a dark wooden hull with a red bottom and gold rails, a castle at the stern with lit windows, three masts of bellied
    cream sails with red crosses, a gilded figurehead under the bowsprit, a row of cannon each side, glowing keel engines, two stern
    propellers - and canvas wings on gilded ribs that beat at its sides."""
    P = Boss("galleon", {"Base": ((0.33, 0.19, 0.10), 0.35), "Belly": ((0.95, 0.91, 0.80), 0.25), "Accent": ((0.72, 0.13, 0.10), 0.4),
                         "Trim": ((0.96, 0.74, 0.24), 0.7), "Glass": ((0.55, 0.38, 0.22), 0.3), "Dark": ((0.06, 0.05, 0.05), 0.3),
                         "Glow": ((0.30, 0.95, 1.0), 0.5), "Metal": ((0.22, 0.22, 0.24), 0.6), "Lamp": ((1.0, 0.72, 0.30), 0.8)})
    def hullp(c, n):
        if c.z < -0.22: return "Accent"
        if 0.16 < c.z < 0.24 and abs(c.x) > 0.3: return "Trim"
        return "Base"
    P.obj("Hull", loft([(2.35, 0.06, 0.22, 0, 0.12), (1.95, 0.42, 0.5, 0, 0.02), (0.8, 0.62, 0.6, 0, -0.04), (-0.8, 0.6, 0.6, 0, -0.02),
                        (-1.8, 0.52, 0.56, 0, 0.04), (-2.2, 0.44, 0.52, 0, 0.1)], 16, sq=1.7), hullp, 1)
    P.obj("Deck", box((0, -0.05, 0.47), (1.0, 3.9, 0.04)), "Glass", 0, False)
    P.obj("SternCastle", box((0, -1.75, 0.72), (1.02, 0.85, 0.5)), lambda c, n: "Trim" if n.z > 0.5 else "Base", 0, False)
    for s in (1, -1):
        for k in range(3):
            P.obj("Window", box((s * 0.52, -1.5 - k * 0.24, 0.74), (0.02, 0.14, 0.16)), "Lamp", 0, False)
        P.obj("Lantern", ball((s * 0.42, -2.25, 1.08), (0.07, 0.07, 0.09), 8, 4), "Lamp")
        for k in range(4):   # the cannon, run out
            y = 1.15 - k * 0.6
            P.obj("Cannon", pipe([(s * 0.5, y, 0.08), (s * 0.82, y, 0.08)], [0.06, 0.05], 8), "Metal")
            P.obj("Port", box((s * 0.6, y, 0.08), (0.03, 0.2, 0.2)), "Dark", 0, False)
        P.obj("Rail", box((s * 0.5, 0.0, 0.58), (0.04, 3.6, 0.06)), "Trim", 0, False)
    P.obj("Forecastle", box((0, 1.6, 0.6), (0.85, 0.6, 0.25)), lambda c, n: "Trim" if n.z > 0.5 else "Base", 0, False)
    for i in range(5):
        P.obj("SternWindow", box((-0.36 + i * 0.18, -2.19, 0.75), (0.12, 0.02, 0.18)), "Lamp", 0, False)
    # masts, yards and sails
    for (y, h, w) in ((1.05, 2.1, 1.3), (0.0, 2.5, 1.6), (-1.0, 2.0, 1.2)):
        P.obj("Mast", pipe([(0, y, 0.45), (0, y, 0.45 + h + 0.3)], [0.06, 0.035], 8), "Base")
        for (z0, z1, ww) in ((0.75, 0.45 + h * 0.55, w), (0.45 + h * 0.6, 0.45 + h, w * 0.75)):
            P.obj("Yard", pipe([(-ww * 0.55, y, z1), (ww * 0.55, y, z1)], [0.03, 0.03], 6), "Base")
            P.part("Cloth", grid((-ww * 0.5, y + 0.02, z0), (ww, 0, 0), (0, 0, z1 - z0 - 0.04), 6, 4, Vector((0, 0.22, 0))),
                  lambda c, n, y=y, z0=z0, z1=z1: "Accent" if (abs(c.x) < 0.07 or abs(c.z - (z0 + z1) * 0.5) < 0.06) else "Belly", (0, 0, 0), 0, False)
        P.obj("Nest", lathe([(0.16, 0.0), (0.16, 0.12), (0.0, 0.12)], 10, "z", (0, y, 0.45 + h * 0.62)), "Base")
        P.part("Cloth", grid((0, y, 0.45 + h + 0.15), (0, -0.45, 0.0), (0, 0, 0.2), 4, 2, Vector((0.06, 0, 0))), "Accent", (0, 0, 0), 0, False)
    P.obj("Bowsprit", pipe([(0, 2.0, 0.45), (0, 2.95, 0.85)], [0.05, 0.03], 8), "Base")
    P.part("Cloth", grid((0, 2.0, 0.55), (0, 0.85, 0.32), (0, -0.85, 1.25), 4, 4, Vector((0.12, 0, 0))), "Belly", (0, 0, 0), 0, False)
    P.obj("Figurehead", ball((0, 2.38, 0.22), (0.1, 0.16, 0.14), 10, 5), "Trim")
    P.obj("FigureWing", hull([(0, 2.3, 0.25), (0.25, 2.2, 0.45), (-0.25, 2.2, 0.45), (0, 2.1, 0.3)]), "Trim", 0, False)
    P.obj("BowCannon", pipe([(0, 2.1, 0.32), (0, 2.65, 0.3)], [0.07, 0.06], 8), "Metal")
    # the flying engines: glowing rings under the keel, two propellers at the stern
    for y in (0.9, -0.6):
        P.obj("KeelRing", lathe([(0.0, -0.78), (0.32, -0.72), (0.4, -0.6), (0.0, -0.55)], 18, "z", (0, y, 0)), lambda c, n: "Glow" if c.z < -0.72 else "Trim")
    for s in (1, -1):
        P.obj("PropShaft", pipe([(s * 0.38, -2.0, -0.05), (s * 0.38, -2.45, -0.05)], [0.05, 0.05], 8), "Metal")
        P.prop((s * 0.38, -2.5, -0.05), 0.42, 4, blade="Base", tip="Trim", spinner="Trim", spinner_len=0.12)
        # the canvas wings on gilded ribs, beating
        name = "FlapR" if s > 0 else "FlapL"
        hub = Vector((s * 0.58, 0.3, 0.3))
        tips = [Vector((s * 2.4, 0.75, 0.95)), Vector((s * 2.55, 0.0, 0.8)), Vector((s * 2.2, -0.7, 0.6)), Vector((s * 1.5, -1.1, 0.4))]
        for t in tips: P.part(name, pipe([hub, t], [0.05, 0.02], 6), "Trim", tuple(hub))
        polys = []
        for a, b in zip(tips, tips[1:]):
            mid = (a + b) * 0.5 + (hub - (a + b) * 0.5) * 0.12
            polys.append([hub, a, mid]); polys.append([hub, mid, b])
        P.part(name, sheet([[tuple(p) for p in poly] for poly in polys], 0.025), "Belly", tuple(hub), 0, False)
        P.part(name, ball(tuple(tips[0]), (0.06, 0.06, 0.06), 6, 3), "Lamp", tuple(hub))
    P.part("Muzzle", ball((0, 2.7, 0.3), (0.08, 0.05, 0.08), 8, 4), "Lamp", (0, 2.7, 0.3))
    return P


# ================================================================= 3. the hurricane gunship
def S_gunship():
    """A huge attack helicopter: a grey armoured body with a stepped tandem canopy, two great rotors side by side on pylon wings, missile pods
    and rotary cannon under the wings, a twin-cannon chin turret, a long tail with a fin and a tail rotor, hazard-yellow tips."""
    P = Boss("gunship", {"Base": ((0.24, 0.29, 0.34), 0.5), "Belly": ((0.55, 0.60, 0.64), 0.45), "Accent": ((0.98, 0.78, 0.10), 0.55),
                         "Trim": ((0.80, 0.12, 0.10), 0.5), "Glass": ((0.22, 0.38, 0.45), 0.95), "Dark": ((0.05, 0.06, 0.07), 0.4),
                         "Glow": ((1.0, 0.5, 0.15), 0.5), "Metal": ((0.45, 0.48, 0.52), 0.7), "Lamp": ((1.0, 0.2, 0.15), 0.8)})
    P.obj("Body", loft([(2.1, 0.12, 0.12, 0, -0.1), (1.85, 0.34, 0.36, 0, -0.08), (1.0, 0.5, 0.55, 0, 0.0), (-0.4, 0.55, 0.6, 0, 0.05),
                        (-1.1, 0.4, 0.45, 0, 0.1), (-1.5, 0.2, 0.22, 0, 0.2)], 16, sq=1.4), lambda c, n: "Belly" if c.z < -0.3 else "Base", 1)
    P.obj("Boom", loft([(-1.4, 0.2, 0.22, 0, 0.2), (-2.6, 0.1, 0.12, 0, 0.35), (-2.95, 0.08, 0.1, 0, 0.38)], 10), lambda c, n: "Accent" if c.y < -2.6 else "Base", 1)
    P.obj("CanopyFront", loft([(1.95, 0.05, 0.04, 0, 0.0), (1.75, 0.28, 0.25, 0, 0.18), (1.35, 0.3, 0.26, 0, 0.3), (1.15, 0.05, 0.05, 0, 0.32)], 14), "Glass", 1)
    P.obj("CanopyBack", loft([(1.25, 0.05, 0.05, 0, 0.36), (1.05, 0.3, 0.26, 0, 0.45), (0.65, 0.3, 0.26, 0, 0.5), (0.45, 0.05, 0.05, 0, 0.48)], 14), "Glass", 1)
    P.obj("Hump", loft([(0.5, 0.2, 0.15, 0, 0.5), (0.0, 0.38, 0.28, 0, 0.55), (-0.9, 0.3, 0.22, 0, 0.45), (-1.2, 0.1, 0.08, 0, 0.35)], 12), "Base", 1)
    for s in (1, -1):
        P.obj("Intake", lathe([(0.0, 0.25), (0.15, 0.2), (0.17, 0.0), (0.15, -0.6)], 12, "y", (s * 0.38, 0, 0.6)), lambda c, n: "Dark" if c.y > 0.2 else "Metal")
        P.obj("Exhaust", pipe([(s * 0.38, -0.65, 0.6), (s * 0.5, -1.0, 0.55)], [0.13, 0.11], 10), "Metal")
        P.obj("ExhaustGlow", pipe([(s * 0.5, -0.99, 0.55), (s * 0.51, -1.03, 0.55)], [0.1, 0.03], 10), "Glow")
    # the pylon wings and the rotors on their tips
    P.wing([(0.45, 0.4, -0.4, 0.16, 0.3), (1.45, 0.3, -0.3, 0.12, 0.5)], lambda c, n: "Belly" if n.z < -0.3 else ("Accent" if abs(c.x) > 1.3 else "Base"), name="Pylon")
    for s in (1, -1):
        hub = (s * 1.55, 0.0, 1.0)
        P.obj("Mast", pipe([(s * 1.5, 0.0, 0.48), (s * 1.55, 0.0, 0.95)], [0.12, 0.08], 10), "Metal")
        P.obj("Housing", ball((s * 1.5, 0.0, 0.5), (0.2, 0.42, 0.18), 12, 6), "Base")
        P.prop(hub, 1.25, 5, axis="z", chord=0.2, blade="Dark", tip="Accent", spinner="Metal", spinner_len=0.15, name="Rotor" + ("R" if s > 0 else "L"))
        # under the stub wing: a rocket pod and a rotary cannon
        P.obj("Stub", box((s * 0.85, -0.05, -0.15), (0.75, 0.55, 0.08)), "Base", 0, False)
        P.obj("Pod", pipe([(s * 0.95, -0.45, -0.38), (s * 0.95, 0.55, -0.38)], [0.17, 0.17], 12), lambda c, n: "Dark" if c.y > 0.53 else "Base")
        for k in range(5):
            a = 2 * math.pi * k / 5
            P.obj("Rocket", ball((s * 0.95 + math.cos(a) * 0.09, 0.57, -0.38 + math.sin(a) * 0.09), (0.03, 0.02, 0.03), 6, 3), "Lamp")
        P.obj("Minigun", pipe([(s * 1.28, -0.2, -0.32), (s * 1.28, 0.75, -0.32)], [0.07, 0.05], 8), "Metal")
    P.obj("Stub", box((0, -0.05, -0.15), (0.9, 0.5, 0.08)), "Base", 0, False)
    # the tail: fin, tail rotor, a red light
    P.fin([(0.0, -2.45, -2.95, 0.08), (0.75, -2.7, -3.05, 0.06), (0.85, -2.8, -3.05, 0.05)], 0.0, 0.35, 0, lambda c, n: "Accent" if c.z > 1.05 else "Base")
    P.wing([(0.05, -2.3, -2.6, 0.06, 0.35), (0.6, -2.35, -2.6, 0.04, 0.35)], name="Stab")
    P.prop((0.12, -2.88, 0.85), 0.38, 3, axis="x", chord=0.08, blade="Dark", tip="Accent", spinner=None, name="TailRotor")
    P.obj("Beacon", ball((0, -0.3, 0.68), (0.05, 0.05, 0.05), 6, 3), "Lamp")
    # the chin turret: twin cannon
    P.obj("Chin", lathe([(0.22, 0.0), (0.2, -0.15), (0.0, -0.2)], 14, "z", (0, 1.65, -0.38)), "Metal")
    for s2 in (1, -1): P.obj("ChinGun", pipe([(s2 * 0.08, 1.7, -0.5), (s2 * 0.08, 2.45, -0.5)], [0.045, 0.035], 8), "Dark")
    P.part("Muzzle", ball((0, 2.52, -0.5), (0.1, 0.05, 0.07), 8, 4), "Glow", (0, 2.52, -0.5))
    return P


# ================================================================= 4. the abyss leviathan
def S_leviathan():
    """A sea serpent risen into the sky: a coiled teal body with a pale belly and glowing spots, bone spikes and a coral sail down its back,
    a great horned head with an open jaw, glowing eyes and long barbels, a crescent tail fluke - and coral fan fins that row the air."""
    P = Boss("leviathan", {"Base": ((0.04, 0.27, 0.36), 0.6), "Belly": ((0.74, 0.88, 0.80), 0.45), "Accent": ((1.0, 0.42, 0.24), 0.5),
                           "Trim": ((0.90, 0.86, 0.74), 0.5), "Glass": ((0.25, 0.75, 0.9), 0.9), "Dark": ((0.03, 0.05, 0.07), 0.4),
                           "Glow": ((0.20, 1.0, 0.85), 0.5), "Metal": ((0.4, 0.45, 0.5), 0.6), "Lamp": ((1.0, 0.85, 0.25), 0.8)})
    ctrl = [(0, 1.55, 0.75), (0, 1.05, 0.35), (0.55, 0.45, 0.05), (0.75, -0.3, 0.3), (0.0, -0.75, 0.45), (-0.75, -1.05, 0.15), (-0.55, -1.75, -0.25),
            (0.25, -2.1, -0.2), (0.6, -2.55, 0.15)]
    sp = spline(ctrl, 4)
    N = len(sp)
    rad = [0.36 * (1 - 0.82 * (i / (N - 1)) ** 1.3) + 0.03 for i in range(N)]
    rad[0] = 0.3
    P.obj("Body", pipe(sp, rad, 14), lambda c, n: "Belly" if n.z < -0.4 else "Base", 0)
    # spines and the coral sail between them; glowing spots down the flanks
    tops = []
    for i in range(2, N - 3, 2):
        p = sp[i]; t = (sp[i + 1] - sp[i - 1]).normalized()
        side = t.cross(Vector((0, 0, 1)))
        side = side.normalized() if side.length > 1e-3 else Vector((1, 0, 0))
        up = side.cross(t).normalized()
        if up.z < 0: up = -up
        base = p + up * rad[i] * 0.85; tip = base + up * (0.38 * rad[i] / 0.36 + 0.08) - t * 0.12
        P.obj("Spine", cone(base, tip, 0.045, 5), "Trim", 0, False)
        tops.append((base, tip))
        for sg in (1, -1):
            P.obj("Spot", ball(tuple(p + side * sg * rad[i] * 0.95 + up * rad[i] * 0.15), (0.05, 0.05, 0.05), 6, 3), "Glow")
    polys = []
    for (b0, t0), (b1, t1) in zip(tops, tops[1:]):
        polys.append([b0, t0, t1, b1])
    bm = bmesh.new()
    for poly in polys:
        n = (poly[1] - poly[0]).cross(poly[3] - poly[0]).normalized() * 0.012
        f = [bm.verts.new(v + n) for v in poly]; g = [bm.verts.new(v - n) for v in poly]
        bm.faces.new(f); bm.faces.new(list(reversed(g)))
    P.part("Cloth", bm, "Accent", (0, 0, 0), 0, False)
    # the tail fluke
    tp = sp[-1]
    P.part("Cloth", sheet([[tuple(tp), tuple(tp + Vector((0.55, -0.35, 0.3))), tuple(tp + Vector((0.2, -0.25, 0.0)))],
                          [tuple(tp), tuple(tp + Vector((0.2, -0.25, 0.0))), tuple(tp + Vector((-0.2, -0.5, -0.25)))]], 0.03), "Accent", (0, 0, 0), 0, False)
    # the head
    HC, HK = Vector((0, 1.55, 0.75)), 1.35
    def H(bm): return grow(bm, HC, HK)
    P.obj("Skull", H(loft([(1.45, 0.24, 0.24, 0, 0.78), (1.75, 0.27, 0.22, 0, 0.84), (2.05, 0.22, 0.15, 0, 0.84), (2.3, 0.14, 0.09, 0, 0.8), (2.45, 0.06, 0.05, 0, 0.78)], 14)),
          lambda c, n: "Belly" if n.z < -0.4 else "Base", 1)
    P.obj("Jaw", H(loft([(1.55, 0.2, 0.08, 0, 0.6), (1.95, 0.17, 0.06, 0, 0.53), (2.3, 0.08, 0.04, 0, 0.48), (2.4, 0.03, 0.02, 0, 0.47)], 12)), lambda c, n: "Belly" if n.z < -0.2 else "Base", 1)
    P.obj("Throat", H(ball((0, 1.95, 0.67), (0.13, 0.32, 0.05), 12, 6)), "Glow")
    for s in (1, -1):
        P.obj("Eye", H(ball((s * 0.19, 1.82, 0.9), (0.055, 0.08, 0.045), 10, 5)), "Lamp")
        P.obj("Horn", H(pipe(bez((s * 0.14, 1.6, 0.98), (s * 0.2, 1.35, 1.18), (s * 0.18, 1.1, 1.28), (s * 0.1, 0.9, 1.3), 5), [0.06, 0.05, 0.04, 0.03, 0.015, 0.0], 8)), "Trim")
        P.obj("Barbel", H(pipe(bez((s * 0.12, 2.25, 0.72), (s * 0.35, 2.4, 0.6), (s * 0.5, 2.2, 0.35), (s * 0.55, 1.9, 0.2), 6), [0.025, 0.022, 0.019, 0.016, 0.012, 0.008, 0.0], 6)), "Trim")
        # the frill fan behind the jaw
        f0 = Vector((s * 0.22, 1.6, 0.78))
        fr = [f0 + Vector((s * 0.45, -0.25, 0.35)), f0 + Vector((s * 0.55, -0.35, 0.05)), f0 + Vector((s * 0.4, -0.3, -0.25))]
        P.part("Cloth", H(sheet([[tuple(f0), tuple(fr[0]), tuple(fr[1])], [tuple(f0), tuple(fr[1]), tuple(fr[2])]], 0.02)), "Accent", (0, 0, 0), 0, False)
        for t in fr: P.obj("FrillRib", H(pipe([f0, t], [0.02, 0.008], 5)), "Trim")
        for k in range(4):
            y = 1.85 + k * 0.12
            P.obj("Tooth", H(cone((s * (0.17 - k * 0.03), y, 0.7), (s * (0.16 - k * 0.03), y + 0.02, 0.6), 0.024, 5)), "Trim", 0, False)
            P.obj("Tooth", H(cone((s * (0.15 - k * 0.03), y, 0.56), (s * (0.14 - k * 0.03), y + 0.02, 0.65), 0.02, 5)), "Trim", 0, False)
        # the fan fins, rowing
        name = "FlapR" if s > 0 else "FlapL"
        hub = Vector((s * 0.35, 1.0, 0.35))
        tips = [hub + Vector((s * 0.85, 0.45, 0.5)), hub + Vector((s * 1.15, 0.0, 0.3)), hub + Vector((s * 1.05, -0.45, 0.05)), hub + Vector((s * 0.6, -0.65, -0.1))]
        polys = []
        for a, b in zip(tips, tips[1:]):
            mid = (a + b) * 0.5 + (hub - (a + b) * 0.5) * 0.18
            polys.append([hub, a, mid]); polys.append([hub, mid, b])
        P.part(name, sheet([[tuple(p) for p in poly] for poly in polys], 0.025), "Accent", tuple(hub), 0, False)
        for t in tips: P.part(name, pipe([hub, t], [0.035, 0.01], 6), "Trim", tuple(hub))
    mz = HC + (Vector((0, 2.42, 0.62)) - HC) * HK
    P.part("Muzzle", ball(tuple(mz), (0.11, 0.08, 0.08), 8, 4), "Glow", tuple(mz))
    return P


# ================================================================= 5. the poseidon battleship
def S_battleship():
    """The last boss: a battleship lifted into the sky - a grey hull with a red bottom, a teak deck, three triple-gun turrets, a tiered bridge
    tower with a radar that turns, a raked funnel, four glowing hover engines, two jet wings, and a golden trident for a ram."""
    P = Boss("battleship", {"Base": ((0.48, 0.51, 0.55), 0.5), "Belly": ((0.55, 0.12, 0.10), 0.4), "Accent": ((0.96, 0.74, 0.22), 0.75),
                            "Trim": ((0.56, 0.41, 0.26), 0.3), "Glass": ((0.30, 0.62, 0.82), 0.95), "Dark": ((0.06, 0.07, 0.08), 0.4),
                            "Glow": ((0.30, 0.90, 1.0), 0.5), "Metal": ((0.34, 0.37, 0.41), 0.6), "Lamp": ((1.0, 0.25, 0.2), 0.8)})
    def hullp(c, n):
        if c.z < -0.16: return "Belly"
        if c.z < -0.09: return "Dark"
        return "Base"
    P.obj("Hull", loft([(2.45, 0.04, 0.24, 0, 0.02), (2.05, 0.38, 0.36, 0, -0.02), (1.0, 0.62, 0.42, 0, 0.0), (-1.0, 0.62, 0.42, 0, 0.0),
                        (-1.9, 0.52, 0.38, 0, 0.02), (-2.2, 0.44, 0.34, 0, 0.04)], 18, sq=1.8), hullp, 1)
    P.obj("Deck", hull([(0, 2.4, 0.42), (0.36, 2.0, 0.42), (0.58, 1.0, 0.43), (0.58, -1.0, 0.43), (0.48, -1.9, 0.43), (0.4, -2.15, 0.43),
                        (-0.36, 2.0, 0.42), (-0.58, 1.0, 0.43), (-0.58, -1.0, 0.43), (-0.48, -1.9, 0.43), (-0.4, -2.15, 0.43),
                        (0, 2.4, 0.4), (0.5, 0, 0.4), (-0.5, 0, 0.4)]), lambda c, n: "Trim" if n.z > 0.5 else "Base", 0, False)
    # the bridge tower
    P.obj("Tier1", box((0, -0.15, 0.62), (0.75, 1.1, 0.36)), "Base", 0, False)
    P.obj("Tier2", box((0, -0.05, 0.92), (0.55, 0.7, 0.3)), "Base", 0, False)
    P.obj("Bridge", box((0, 0.05, 1.18), (0.46, 0.45, 0.22)), "Base", 0, False)
    P.obj("BridgeGlass", box((0, 0.28, 1.2), (0.42, 0.02, 0.08)), "Glass", 0, False)
    for s in (1, -1): P.obj("Wing", box((s * 0.36, 0.2, 1.1), (0.2, 0.18, 0.04)), "Base", 0, False)
    P.obj("Mast", pipe([(0, -0.05, 1.28), (0, -0.05, 2.0)], [0.05, 0.03], 8), "Metal")
    P.obj("Yardarm", pipe([(-0.35, -0.05, 1.75), (0.35, -0.05, 1.75)], [0.02, 0.02], 6), "Metal")
    P.obj("Beacon", ball((0, -0.05, 2.03), (0.05, 0.05, 0.05), 6, 3), "Lamp")
    P.part("SpinRadar", box((0, -0.05, 1.5), (0.6, 0.06, 0.18)), "Dark", (0, -0.05, 1.5), 0, False)
    P.part("SpinRadar", pipe([(0, -0.05, 1.38), (0, -0.05, 1.5)], [0.04, 0.04], 6), "Metal", (0, -0.05, 1.5))
    P.obj("Funnel", pipe([(0, -0.95, 0.75), (0, -1.1, 1.15), (0, -1.15, 1.3)], [0.2, 0.18, 0.18], 14), lambda c, n: "Dark" if c.z > 1.2 else ("Accent" if 1.05 < c.z < 1.12 else "Base"))
    # three triple turrets: two forward (the second raised), one aft
    def turret(y, z, facing):
        c = Vector((0, y, z))
        P.obj("Barbette", lathe([(0.3, -0.08), (0.3, 0.0), (0.0, 0.0)], 16, "z", tuple(c)), "Metal")
        P.obj("Gunhouse", hull([c + Vector((sx * 0.3, facing * fy, h)) for sx in (1, -1) for (fy, h) in ((0.32, 0.0), (0.2, 0.18), (-0.32, 0.0), (-0.3, 0.2))]), "Base", 0, False)
        for gx in (-0.13, 0.0, 0.13):
            P.obj("Gun", pipe([c + Vector((gx, facing * 0.25, 0.1)), c + Vector((gx, facing * 1.0, 0.12))], [0.045, 0.035], 8), "Metal")
    turret(1.45, 0.45, 1); turret(0.8, 0.62, 1); turret(-1.6, 0.45, -1)
    # hover engines, jet wings
    for s in (1, -1):
        for y in (1.2, -1.2):
            P.obj("Hover", lathe([(0.0, -0.62), (0.26, -0.58), (0.32, -0.42), (0.28, -0.25), (0.0, -0.2)], 16, "z", (s * 0.42, y, 0)), lambda c, n: "Glow" if c.z < -0.57 else "Metal")
        P.obj("Jet", pipe([(s * 1.75, 0.4, 0.1), (s * 1.75, -0.85, 0.13)], [0.19, 0.17], 12), lambda c, n: "Dark" if c.y > 0.3 else "Metal")
        P.obj("JetGlow", pipe([(s * 1.75, -0.84, 0.13), (s * 1.75, -0.91, 0.13)], [0.15, 0.04], 12), "Glow")
    P.wing([(0.55, 0.35, -0.75, 0.12, 0.05), (2.0, -0.1, -0.7, 0.07, 0.16)], lambda c, n: "Belly" if n.z < -0.3 else ("Accent" if abs(c.x) > 1.85 else "Base"), name="JetWing")
    # the golden trident at the bow
    P.obj("Trident", pipe([(0, 2.3, 0.05), (0, 3.05, 0.05)], [0.06, 0.05], 8), "Accent")
    P.obj("TridentTip", cone((0, 3.0, 0.05), (0, 3.3, 0.05), 0.08, 6), "Accent", 0, False)
    for s in (1, -1):
        prong = bez((0, 2.75, 0.05), (s * 0.25, 2.75, 0.05), (s * 0.3, 2.9, 0.05), (s * 0.3, 3.12, 0.05), 5)
        P.obj("Prong", pipe(prong, [0.04, 0.04, 0.04, 0.035, 0.03, 0.0], 6), "Accent")
    P.part("Muzzle", ball((0, 2.5, 0.57), (0.1, 0.05, 0.08), 8, 4), "Glow", (0, 2.5, 0.57))
    return P


BOSSES = [("fortress", S_fortress), ("galleon", S_galleon), ("gunship", S_gunship), ("leviathan", S_leviathan), ("battleship", S_battleship)]

if __name__ == "__main__":
    os.makedirs(AB.OUT, exist_ok=True)
    for bid, fn in BOSSES:
        if ONLY and bid not in ONLY: continue
        fn().finish()
    print("DONE")
