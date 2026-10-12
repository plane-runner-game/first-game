# Sky Squad, the space launch's five bosses (2026-10-11: "the rest of the bosses for the maps that don't have theirs yet"): the retro
# rocket, the orbital satellite, the astro mech, the lunar lander and the space station. Human space tech, a launch base's own (the alien
# world has the saucer and the mothership). Built from code like the other worlds' bosses (alien_bosses.py lends its Boss class and shapes).
# Run: blender -b -P Tools/blender/shuttle_bosses.py -- <out dir> [export] [ids,comma,separated]
# Conventions as alien_bosses.py: +Y nose, +Z up, +X right; "Flap*" rock about the nose axis, "Sway*" about the wing axis, "Spin*" turn slowly
# about up, "Roll*" slowly about the nose axis, "Cloth" stays still without the outline, "Muzzle" is where his shots leave from.
import bpy, bmesh, math, sys, os, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mathutils import Vector, Matrix
from enemy_planes import loft, sweep, lathe, box, hull, tube, mirror_x, airfoil
import alien_bosses as AB
from alien_bosses import Boss, xf, ball, pipe, cone, bez, torus, sheet, grow, ang

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ONLY = argv[2].split(",") if len(argv) > 2 and argv[2] else None

WHITE = ((0.95, 0.95, 0.96), 0.5)
ORANGE = ((0.98, 0.45, 0.10), 0.55)
FOIL = ((0.98, 0.72, 0.18), 0.85)
SOLAR = ((0.08, 0.20, 0.62), 0.9)
FLAME = ((1.0, 0.55, 0.12), 0.5)


def speckle(c, k=1.0):
    v = math.sin(c.x * 12.9898 * k + c.y * 78.233 * k + c.z * 37.719 * k) * 43758.5453
    return v - math.floor(v)

def facing_y(bm, c):
    """a shape built about +Z turned to face the player (+Y), moved to c."""
    return xf(bm, Matrix.Rotation(math.radians(-90), 3, "X"), c)

def panel(P, name, x0, x1, y0, y1, z, nx, ny, hub=None, cell="Glass", frame="Metal"):
    """a solar array: a frame with nx * ny glossy cells on it (real boxes, so the outline treats it as a solid)."""
    add = (lambda n, bm, p: P.part(n, bm, p, hub, 0, False)) if hub is not None else (lambda n, bm, p: P.obj(n, bm, p, 0, False))
    add(name, box(((x0 + x1) / 2, (y0 + y1) / 2, z - 0.015), (abs(x1 - x0), abs(y1 - y0), 0.03)), frame)
    dx = (x1 - x0) / nx; dy = (y1 - y0) / ny
    for i in range(nx):
        for j in range(ny):
            add(name, box((x0 + dx * (i + 0.5), y0 + dy * (j + 0.5), z + 0.01), (abs(dx) * 0.88, abs(dy) * 0.86, 0.025)), cell)

def foil(c, n):
    """crinkled gold foil: facets of two golds."""
    return "Trim" if speckle(Vector((round(c.x * 6), round(c.y * 6), round(c.z * 6))), 1.7) < 0.6 else "Belly"


# ================================================================= 1. the retro rocket
def S_rocket():
    """A classic cartoon rocket standing on its flame: white with red bands and a red nose, a round porthole with a glowing pilot's visor,
    four swept red fins, two strap-on boosters, and a collar of launch lights turning round its waist."""
    P = Boss("rocket", {"Base": WHITE, "Belly": ((0.70, 0.72, 0.76), 0.5), "Accent": ((0.88, 0.12, 0.10), 0.6), "Trim": ((0.20, 0.32, 0.70), 0.6),
                        "Glass": ((0.35, 0.80, 1.0), 0.95), "Dark": ((0.10, 0.10, 0.12), 0.5), "Glow": FLAME,
                        "Metal": ((0.62, 0.64, 0.70), 0.8), "Lamp": ((1.0, 0.92, 0.55), 0.8)})
    def band(c, n):
        if c.z > 2.45: return "Accent"
        if 1.05 < c.z < 1.22 or 0.25 < c.z < 0.38: return "Accent"
        if 2.25 < c.z < 2.35: return "Trim"
        return "Base"
    P.obj("Hull", lathe([(0.0, 0.0), (0.40, 0.02), (0.47, 0.25), (0.50, 0.8), (0.50, 1.7), (0.46, 2.2), (0.36, 2.65), (0.2, 3.0), (0.06, 3.2), (0.0, 3.25)], 28, "z"), band)
    P.obj("Tip", pipe([(0, 0, 3.2), (0, 0, 3.55)], [0.03, 0.0], 6), "Metal")
    # the nozzle and the flame
    P.obj("Nozzle", lathe([(0.24, 0.02), (0.30, -0.18), (0.38, -0.34), (0.32, -0.34), (0.18, -0.05)], 20, "z"), "Dark")
    P.obj("Flame", lathe([(0.32, -0.32), (0.38, -0.6), (0.3, -1.0), (0.14, -1.4), (0.0, -1.65)], 16, "z"), "Glow")
    P.obj("FlameCore", lathe([(0.2, -0.3), (0.22, -0.55), (0.1, -0.95), (0.0, -1.15)], 12, "z"), "Lamp")
    # the porthole with the pilot
    win = (0, 0.47, 1.75)
    P.obj("Rim", facing_y(torus(0.27, 0.06, 0.0, 22, 6), win), "Metal")
    P.obj("Porthole", ball(win, (0.25, 0.07, 0.25), 14, 6), "Dark")
    P.obj("Visor", ball((0, 0.5, 1.72), (0.13, 0.05, 0.1), 12, 5), "Glass")
    for k in range(6):   # rivets round the porthole
        a = 2 * math.pi * k / 6
        P.obj("Rivet", ball((math.sin(a) * 0.3, 0.47 - 0.02 * abs(math.sin(a)), 1.75 + math.cos(a) * 0.3), (0.025, 0.025, 0.025), 6, 3), "Metal")
    # four swept fins
    for k in range(4):
        a = math.radians(45 + 90 * k)
        d = Vector((math.cos(a), math.sin(a), 0)); t = Vector((-math.sin(a), math.cos(a), 0)) * 0.05
        pts = []
        for (r, z) in ((0.46, 1.05), (0.49, 0.25), (1.05, -0.15), (1.1, 0.15), (0.75, 0.75)):
            p = d * r + Vector((0, 0, z)); pts += [tuple(p + t), tuple(p - t)]
        P.obj("Fin", hull(pts), lambda c, n: "Trim" if c.z < -0.02 else "Accent", 0, False)
    # two strap-on boosters
    for s in (1, -1):
        bx = s * 0.78
        P.obj("Booster", lathe([(0.0, 0.0), (0.2, 0.02), (0.22, 0.2), (0.22, 1.25), (0.15, 1.5), (0.0, 1.62)], 18, "z", (bx, -0.05, 0)),
              lambda c, n: "Accent" if c.z > 1.35 or 0.5 < c.z < 0.6 else "Base")
        P.obj("BNozzle", lathe([(0.12, 0.02), (0.18, -0.15), (0.12, -0.12)], 12, "z", (bx, -0.05, 0)), "Dark")
        P.obj("BFlame", lathe([(0.17, -0.14), (0.16, -0.45), (0.06, -0.8), (0.0, -0.9)], 12, "z", (bx, -0.05, 0)), "Glow")
        for z in (0.35, 1.15): P.obj("Strut", pipe([(s * 0.46, -0.03, z), (s * 0.6, -0.04, z)], [0.04, 0.04], 6), "Metal")
    # the collar of launch lights, turning
    P.part("SpinRing", torus(0.6, 0.06, 1.42, 32, 6), "Metal", (0, 0, 1.42))
    for k in range(10):
        a = 2 * math.pi * k / 10
        P.part("SpinRing", ball((math.sin(a) * 0.66, math.cos(a) * 0.66, 1.42), (0.09, 0.09, 0.09), 8, 4), "Lamp" if k % 2 == 0 else "Trim", (0, 0, 1.42))
    P.part("Muzzle", ball((0, 0.55, 2.3), (0.06, 0.03, 0.06), 8, 4), "Lamp", (0, 0.55, 2.3))
    return P


# ================================================================= 2. the orbital satellite
def S_satellite():
    """A great satellite in gold foil: long blue solar wings that tilt to the sun, a white dish on its face that turns slowly with its feed
    glowing, a silver equipment deck, star trackers, whip antennas and a red beacon."""
    P = Boss("satellite", {"Base": WHITE, "Belly": ((0.85, 0.55, 0.12), 0.85), "Accent": ((0.88, 0.14, 0.12), 0.6), "Trim": FOIL,
                           "Glass": SOLAR, "Dark": ((0.08, 0.08, 0.10), 0.5), "Glow": ((0.4, 0.85, 1.0), 0.5),
                           "Metal": ((0.70, 0.72, 0.78), 0.85), "Lamp": ((1.0, 0.25, 0.2), 0.8)})
    rings = [(y, 0.55, 0.55, 0, 0) for y in (-0.55, -0.4, -0.2, 0.0, 0.2, 0.4, 0.55)]
    P.obj("Bus", loft(rings, 24, sq=4.0), foil, 0, False)
    P.obj("Deck", box((0, 0, 0.62), (1.0, 1.0, 0.14)), "Metal", 0, False)
    P.obj("DeckBase", box((0, 0, -0.62), (0.95, 0.95, 0.12)), "Metal", 0, False)
    P.obj("Thruster", lathe([(0.12, -0.68), (0.2, -0.9), (0.15, -0.9), (0.06, -0.7)], 12, "z"), "Dark")
    for s in (1, -1):   # star trackers and antennas on the deck
        P.obj("Tracker", pipe([(s * 0.3, -0.25, 0.69), (s * 0.34, -0.3, 0.95)], [0.09, 0.08], 10), lambda c, n: "Dark" if c.z > 0.9 else "Base")
        P.obj("Whip", pipe([(s * 0.35, 0.3, 0.69), (s * 0.5, 0.4, 1.5)], [0.02, 0.01], 5), "Metal")
    P.obj("Beacon", ball((0, -0.3, 0.75), (0.08, 0.08, 0.08), 8, 4), "Lamp")
    # the dish on its face, turning slowly face-on (three struts make the turn show)
    dc = Vector((0, 0.6, 0))
    dish = lathe([(0.0, 0.0), (0.34, 0.05), (0.62, 0.18), (0.78, 0.33), (0.75, 0.36), (0.6, 0.23), (0.32, 0.1), (0.0, 0.07)], 30, "z")
    P.part("RollDish", facing_y(dish, dc), lambda c, n: "Base" if n.y > 0.1 else "Metal", tuple(dc), 0)
    for k in range(3):
        a = 2 * math.pi * k / 3 + math.pi / 2
        rim = dc + Vector((math.cos(a) * 0.72, 0.33, math.sin(a) * 0.72))
        P.part("RollDish", pipe([rim, dc + Vector((0, 0.85, 0))], [0.025, 0.02], 6), "Metal", tuple(dc), 0)
    P.part("RollDish", ball(tuple(dc + Vector((0, 0.87, 0))), (0.09, 0.09, 0.09), 10, 5), "Glow", tuple(dc), 0)
    P.part("RollDish", lathe([(0.12, 0.0), (0.14, 0.12), (0.0, 0.14)], 12, "z", tuple(dc + Vector((0, 0.02, 0)))), "Metal", tuple(dc), 0)
    # the solar wings: a boom, a yoke, two panels a side; they tilt about the wing axis
    for s in (1, -1):
        name = "SwayWingR" if s > 0 else "SwayWingL"
        hub = (s * 0.56, 0, 0)
        P.obj("Gimbal", pipe([(s * 0.55, 0, 0), (s * 0.68, 0, 0)], [0.1, 0.1], 10), "Dark")
        P.part(name, pipe([(s * 0.66, 0, 0), (s * 2.95, 0, 0)], [0.045, 0.04], 8), "Metal", hub, 0)
        for (a0, a1) in ((0.85, 1.85), (1.95, 2.95)):
            panel(P, name, s * a0, s * a1, -0.68, 0.68, 0.0, 4, 4, hub)
    P.part("Muzzle", ball((0, 1.5, 0.0), (0.06, 0.03, 0.06), 8, 4), "Glow", (0, 1.5, 0.0))
    return P


# ================================================================= 3. the astro mech
def S_mech():
    """A chunky astronaut robot on a jetpack: a white suit with orange stripes and blue patches, a round helmet with a mirrored gold visor and
    a glowing antenna, a chest panel of lights, a ray blaster in his right hand, arms that rise and fall, legs swinging, two thrusters blazing."""
    P = Boss("mech", {"Base": WHITE, "Belly": ((0.72, 0.74, 0.78), 0.5), "Accent": ORANGE, "Trim": ((0.15, 0.35, 0.85), 0.6),
                      "Glass": ((1.0, 0.75, 0.25), 0.97), "Dark": ((0.16, 0.17, 0.20), 0.5), "Glow": FLAME,
                      "Metal": ((0.55, 0.57, 0.62), 0.8), "Lamp": ((0.35, 1.0, 0.85), 0.8)})
    P.obj("Torso", ball((0, 0, 0.95), (0.55, 0.42, 0.6), 18, 9), lambda c, n: "Accent" if 1.18 < c.z < 1.3 else "Base", 1)
    P.obj("Belt", lathe([(0.47, 0.42), (0.52, 0.5), (0.52, 0.6), (0.47, 0.66)], 20, "z"), "Dark")
    for v in P.parts[-1].data.vertices: v.co.y *= 0.8
    P.obj("Buckle", box((0, 0.42, 0.54), (0.22, 0.06, 0.13)), "Metal", 0, False)
    P.obj("Chest", box((0, 0.38, 0.92), (0.42, 0.12, 0.3), Matrix.Rotation(math.radians(-8), 3, "X")), "Belly", 0, False)
    for i, col in enumerate(("Lamp", "Accent", "Trim", "Lamp")):
        P.obj("Button", ball((-0.13 + i * 0.087, 0.45, 0.97), (0.035, 0.03, 0.035), 8, 4), col)
    P.obj("Grille", box((0, 0.45, 0.84), (0.28, 0.02, 0.07)), "Dark", 0, False)
    # the helmet
    P.obj("Collar", lathe([(0.32, 1.42), (0.36, 1.5), (0.3, 1.56)], 20, "z"), "Metal")
    P.obj("Helmet", ball((0, 0.0, 1.88), (0.44, 0.42, 0.42), 20, 10), "Base", 1)
    P.obj("Visor", ball((0, 0.17, 1.86), (0.35, 0.3, 0.27), 18, 9), "Glass", 1)
    P.obj("VisorRim", xf(torus(0.36, 0.035, 0.0, 26, 6), Matrix.Rotation(math.radians(-90), 3, "X") @ Matrix.Diagonal((1.0, 0.78, 1.0)), (0, 0.3, 1.86)), "Accent")
    for s in (1, -1):
        P.obj("EarPod", ball((s * 0.44, 0, 1.88), (0.08, 0.14, 0.14), 10, 5), "Accent")
        P.obj("Patch", ball((s * 0.5, 0.05, 1.22), (0.05, 0.14, 0.12), 8, 4), "Trim")
    P.obj("Antenna", pipe([(0.3, -0.05, 2.18), (0.36, -0.08, 2.55)], [0.02, 0.015], 6), "Metal")
    P.obj("AntennaTip", ball((0.36, -0.08, 2.58), (0.06, 0.06, 0.06), 8, 4), "Lamp")
    # the jetpack
    P.obj("Pack", box((0, -0.5, 1.05), (0.82, 0.34, 0.85)), lambda c, n: "Accent" if c.z > 1.36 else "Belly", 0, False)
    for s in (1, -1):
        tx = s * 0.26
        P.obj("Tank", lathe([(0.0, 0.42), (0.15, 0.48), (0.16, 1.45), (0.0, 1.6)], 14, "z", (tx, -0.72, 0)), lambda c, n: "Accent" if c.z > 1.35 else "Metal")
        P.obj("Jet", lathe([(0.1, 0.44), (0.16, 0.26), (0.1, 0.28)], 12, "z", (tx, -0.72, 0)), "Dark")
        P.obj("JetFlame", lathe([(0.15, 0.27), (0.15, 0.0), (0.07, -0.4), (0.0, -0.55)], 12, "z", (tx, -0.72, 0)), "Glow")
    # arms: rise and fall about the nose axis from the shoulder
    for s in (1, -1):
        name = "FlapR" if s > 0 else "FlapL"
        sh = Vector((s * 0.55, 0.02, 1.2)); el = Vector((s * 0.95, 0.15, 0.85)); hd = Vector((s * 1.0, 0.5, 0.82))
        P.part(name, ball(tuple(sh), (0.2, 0.2, 0.2), 10, 5), "Accent", tuple(sh))
        P.part(name, pipe([sh, el], [0.15, 0.13], 10), "Base", tuple(sh))
        P.part(name, ball(tuple(el), (0.13, 0.13, 0.13), 10, 5), "Metal", tuple(sh))
        P.part(name, pipe([el, hd], [0.13, 0.12], 10), lambda c, n: "Accent" if (c - hd).length < 0.12 else "Base", tuple(sh))
        P.part(name, ball(tuple(hd + Vector((0, 0.08, 0))), (0.13, 0.12, 0.12), 10, 5), "Belly", tuple(sh))
        if s > 0:   # the ray blaster
            P.part(name, box(tuple(hd + Vector((0, 0.22, 0.1))), (0.14, 0.42, 0.18)), "Trim", tuple(sh), 0, False)
            P.part(name, pipe([hd + Vector((0, 0.4, 0.14)), hd + Vector((0, 0.72, 0.14))], [0.06, 0.05], 8), "Metal", tuple(sh))
            for k in range(3): P.part(name, pipe([hd + Vector((0, 0.46 + 0.08 * k, 0.14)), hd + Vector((0, 0.5 + 0.08 * k, 0.14))], [0.085, 0.085], 10), "Lamp", tuple(sh))
    # legs swinging about the wing axis from the hip
    for s in (1, -1):
        name = "SwayLegR" if s > 0 else "SwayLegL"
        hip = Vector((s * 0.24, 0, 0.45)); kn = Vector((s * 0.28, 0.1, -0.05)); ft = Vector((s * 0.3, 0.0, -0.45))
        P.part(name, pipe([hip, kn], [0.17, 0.15], 10), "Base", tuple(hip))
        P.part(name, ball(tuple(kn), (0.15, 0.15, 0.15), 10, 5), "Accent", tuple(hip))
        P.part(name, pipe([kn, ft], [0.15, 0.14], 10), "Base", tuple(hip))
        P.part(name, ball(tuple(ft + Vector((0, 0.08, -0.1))), (0.17, 0.26, 0.13), 10, 5), "Dark", tuple(hip))
    mz = (1.0, 1.25, 0.96)
    P.part("Muzzle", ball(mz, (0.07, 0.04, 0.07), 8, 4), "Lamp", mz)
    return P


# ================================================================= 4. the lunar lander
def S_lander():
    """A lunar lander: a gold-foil descent stage on four spindly legs with round pads, a faceted silver cabin with two triangular windows
    glowing, a hatch and a porch, thruster quads at its corners, a dish on top turning, and the descent engine burning underneath."""
    P = Boss("lander", {"Base": ((0.80, 0.82, 0.86), 0.6), "Belly": ((0.86, 0.58, 0.14), 0.85), "Accent": ((0.15, 0.15, 0.17), 0.5), "Trim": FOIL,
                        "Glass": ((0.12, 0.28, 0.55), 0.97), "Dark": ((0.07, 0.07, 0.08), 0.5), "Glow": FLAME,
                        "Metal": ((0.62, 0.64, 0.70), 0.85), "Lamp": ((0.55, 0.85, 1.0), 0.8)})
    prof = [(0.0, 0.0)] + [(0.95, h) for h in (0.0, 0.15, 0.3, 0.45, 0.6, 0.75)] + [(0.0, 0.75)]
    ds = xf(lathe(prof, 8, "z"), Matrix.Rotation(math.radians(22.5), 3, "Z"), (0, 0, -0.1))
    P.obj("Descent", ds, lambda c, n: "Accent" if abs(n.z) > 0.7 else foil(c, n), 0, False)
    P.obj("Engine", lathe([(0.22, -0.1), (0.3, -0.35), (0.4, -0.5), (0.34, -0.5), (0.18, -0.15)], 18, "z"), "Dark")
    P.obj("Burn", lathe([(0.36, -0.48), (0.36, -0.75), (0.22, -1.1), (0.0, -1.3)], 14, "z"), "Glow")
    # the cabin
    cab = [(sx * 0.62, 0.55, 0.65) for sx in (-1, 1)] + [(sx * 0.72, -0.4, 0.65) for sx in (-1, 1)] + [(sx * 0.58, 0.62, 1.25) for sx in (-1, 1)]
    cab += [(sx * 0.7, -0.45, 1.4) for sx in (-1, 1)] + [(sx * 0.32, 0.25, 1.6) for sx in (-1, 1)] + [(sx * 0.35, -0.45, 1.58) for sx in (-1, 1)] + [(0, 0.7, 0.95)]
    P.obj("Cabin", hull(cab), lambda c, n: "Metal" if n.z > 0.6 else "Base", 0, False)
    for s in (1, -1):   # two triangular windows, glowing
        w = [(s * 0.1, 0.665, 1.1), (s * 0.42, 0.62, 1.12), (s * 0.18, 0.6, 1.35)]
        P.obj("Window", hull([p for p in w] + [(p[0] * 0.98, p[1] + 0.03, p[2]) for p in w]), "Glass", 0, False)
        P.obj("WindowGlow", ball((s * 0.22, 0.66, 1.17), (0.05, 0.02, 0.05), 6, 3), "Lamp")
        P.obj("Frame", hull([(p[0] * 1.08, p[1] - 0.01, p[2]) for p in w] + [(p[0] * 1.08, p[1] + 0.015, p[2]) for p in w]), "Accent", 0, False)
    P.obj("Hatch", box((0, 0.66, 0.78), (0.32, 0.06, 0.26)), "Metal", 0, False)
    P.obj("Porch", box((0, 0.95, 0.62), (0.4, 0.5, 0.04)), "Trim", 0, False)
    P.obj("Ladder", pipe([(0, 1.2, 0.6), (0, 1.35, 0.0)], [0.025, 0.025], 6), "Metal")
    P.obj("Tunnel", lathe([(0.2, 1.5), (0.2, 1.75), (0.24, 1.78), (0.0, 1.8)], 14, "z", (0, -0.1, 0)), "Base")
    # thruster quads on the cabin corners
    for sx in (-1, 1):
        for sy in (-1, 1):
            c = Vector((sx * 0.78, sy * 0.5 - 0.05, 1.15))
            P.obj("Quad", box(tuple(c), (0.14, 0.14, 0.14)), "Accent", 0, False)
            for d in (Vector((sx, 0, 0)), Vector((0, sy, 0)), Vector((0, 0, 1)), Vector((0, 0, -1))):
                P.obj("Jet", cone(tuple(c + d * 0.2), tuple(c + d * 0.07), 0.05, 6), "Metal", 0, False)
    # the dish on top, turning
    dh = Vector((0.35, -0.3, 1.6))
    P.obj("Mast", pipe([dh, dh + Vector((0, 0, 0.35))], [0.025, 0.025], 6), "Metal")
    dish = lathe([(0.0, 0.0), (0.2, 0.03), (0.32, 0.1), (0.3, 0.12), (0.18, 0.06), (0.0, 0.04)], 18, "z")
    dish = xf(dish, Matrix.Rotation(math.radians(-60), 3, "X"), (0, 0.04, 0.38))
    P.part("SpinDish", xf(dish, None, tuple(dh)), lambda c, n: "Base" if n.y > 0 else "Metal", tuple(dh))
    # four legs with round pads
    for k in range(4):
        a = math.radians(45 + 90 * k)
        d = Vector((math.cos(a), math.sin(a), 0))
        top = d * 0.85 + Vector((0, 0, 0.5)); foot = d * 1.55 + Vector((0, 0, -0.75))
        P.obj("Leg", pipe([top, foot], [0.055, 0.045], 8), "Metal")
        P.obj("Brace", pipe([d * 0.9 + Vector((0, 0, -0.05)), top + (foot - top) * 0.55], [0.03, 0.03], 6), "Metal")
        P.obj("Pad", lathe([(0.0, -0.84), (0.24, -0.82), (0.26, -0.76), (0.0, -0.72)], 14, "z", tuple(d * 1.58)), "Trim")
    P.part("Muzzle", ball((0, 0.72, 0.95), (0.06, 0.03, 0.06), 8, 4), "Lamp", (0, 0.72, 0.95))
    return P


# ================================================================= 5. the space station
def S_station():
    """The last boss: a great space station - a white core tower of modules with an observation cupola under it, a ring habitat turning
    round it on six spokes with glowing windows, a long truss carrying four wings of blue solar arrays with radiators, and a little space
    shuttle docked at its front, its nose to the player."""
    P = Boss("station", {"Base": WHITE, "Belly": ((0.75, 0.77, 0.82), 0.5), "Accent": ORANGE, "Trim": FOIL,
                         "Glass": SOLAR, "Dark": ((0.07, 0.07, 0.09), 0.5), "Glow": ((0.45, 0.85, 1.0), 0.5),
                         "Metal": ((0.62, 0.64, 0.70), 0.85), "Lamp": ((1.0, 0.85, 0.45), 0.8)})
    def bands(c, n):
        if abs(n.z) > 0.8: return "Belly"
        return "Trim" if (c.z * 2.2) % 1.0 < 0.18 else "Base"
    P.obj("Core", lathe([(0.0, -0.95), (0.25, -0.95), (0.38, -0.8), (0.38, 1.25), (0.3, 1.4), (0.0, 1.45)], 20, "z"), bands)
    P.obj("Cupola", ball((0, 0, -1.0), (0.24, 0.24, 0.2), 12, 6), "Glow")
    P.obj("Dome", ball((0, 0, 1.45), (0.2, 0.2, 0.16), 12, 6), "Belly")
    P.obj("Mast", pipe([(0, 0, 1.55), (0, 0, 2.1)], [0.025, 0.015], 6), "Metal")
    P.obj("MastTip", ball((0, 0, 2.12), (0.05, 0.05, 0.05), 8, 4), "Lamp")
    for s in (1, -1):   # side modules below the ring
        P.obj("Module", lathe([(0.0, 0.38), (0.2, 0.4), (0.22, 0.5), (0.22, 1.25), (0.15, 1.35), (0.0, 1.36)], 14, "x", (0, 0, -0.45)) if s > 0 else
              mirror_x(lathe([(0.0, 0.38), (0.2, 0.4), (0.22, 0.5), (0.22, 1.25), (0.15, 1.35), (0.0, 1.36)], 14, "x", (0, 0, -0.45))),
              lambda c, n: "Trim" if 0.8 < abs(c.x) < 0.95 else "Base")
    # the ring habitat on six spokes, turning about up
    rz = 0.25; hub = (0, 0, rz)
    P.part("SpinRing", torus(1.75, 0.21, rz, 48, 10), lambda c, n: "Belly" if abs(n.z) > 0.6 else "Base", hub)
    for k in range(6):
        a = 2 * math.pi * k / 6
        P.part("SpinRing", pipe([(math.sin(a) * 0.38, math.cos(a) * 0.38, rz), (math.sin(a) * 1.6, math.cos(a) * 1.6, rz)], [0.05, 0.05], 8), "Metal", hub)
        P.part("SpinRing", ball((math.sin(a + 0.52) * 1.75, math.cos(a + 0.52) * 1.75, rz), (0.26, 0.26, 0.24), 12, 6), "Accent", hub)
    for k in range(24):
        a = 2 * math.pi * k / 24
        if k % 4 == 1: continue
        P.part("SpinRing", ball((math.sin(a) * 1.93, math.cos(a) * 1.93, rz), (0.06, 0.04, 0.06), 6, 3), "Lamp", hub)
    P.obj("Collar", torus(0.42, 0.07, rz, 20, 6), "Metal")
    # the truss and the solar arrays above the ring
    tz = 1.05
    P.obj("Truss", box((0, 0, tz), (5.8, 0.16, 0.16)), "Metal", 0, False)
    for k in range(14):
        x = -2.8 + k * 0.4
        P.obj("Lattice", pipe([(x, 0, tz - 0.08), (x + 0.4, 0, tz + 0.08)], [0.02, 0.02], 4), "Dark")
    for s in (1, -1):
        P.obj("Joint", ball((s * 0.95, 0, tz), (0.13, 0.13, 0.13), 10, 5), "Accent")
        for (y0, y1) in ((0.12, 1.25), (-1.25, -0.12)):
            panel(P, "Array", s * 1.05, s * 2.85, y0, y1, tz, 5, 3)
        P.obj("Radiator", box((s * 0.65, 0, tz + 0.35), (0.04, 0.9, 0.55)), "Belly", 0, False)
        P.obj("Beacon", ball((s * 2.92, 0, tz), (0.07, 0.07, 0.07), 8, 4), "Lamp")
    # the docking port and the shuttle docked at the front, its nose to the player
    P.obj("Port", pipe([(0, 0.3, 0.85), (0, 0.8, 0.85)], [0.17, 0.17], 12), lambda c, n: "Trim" if c.y > 0.7 else "Base")
    sy0, sz = 0.85, 0.82
    orb = loft([(sy0, 0.2, 0.2, 0, sz), (sy0 + 0.3, 0.27, 0.25, 0, sz), (sy0 + 1.05, 0.27, 0.26, 0, sz + 0.01), (sy0 + 1.35, 0.22, 0.22, 0, sz - 0.01),
                (sy0 + 1.55, 0.13, 0.13, 0, sz - 0.04), (sy0 + 1.65, 0.03, 0.03, 0, sz - 0.06)], 18, sq=1.4)
    P.obj("Orbiter", orb, lambda c, n: "Dark" if n.z < -0.35 or c.y > sy0 + 1.5 else "Base", 1)
    P.obj("Cockpit", hull([(sx * 0.15, sy0 + 1.25, sz + 0.2) for sx in (-1, 1)] + [(sx * 0.12, sy0 + 1.4, sz + 0.12) for sx in (-1, 1)] +
                          [(sx * 0.17, sy0 + 1.15, sz + 0.22) for sx in (-1, 1)] + [(0, sy0 + 1.2, sz + 0.25)]), "Dark", 0, False)
    for s in (1, -1):
        w = [(s * 0.2, sy0 + 0.05, sz - 0.12), (s * 0.85, sy0 + 0.0, sz - 0.14), (s * 0.85, sy0 + 0.2, sz - 0.14), (s * 0.22, sy0 + 1.0, sz - 0.1)]
        P.obj("Delta", hull(w + [(p[0], p[1], p[2] + 0.06) for p in w]), lambda c, n: "Dark" if n.z < -0.3 or abs(c.x) > 0.75 else "Base", 0, False)
        P.obj("Pod", ball((s * 0.18, sy0 + 0.15, sz + 0.23), (0.09, 0.22, 0.07), 10, 5), "Base")
        P.obj("Bell", lathe([(0.04, 0.0), (0.08, -0.15), (0.05, -0.15)], 10, "y", (s * 0.12, sy0 + 0.02, sz)), "Metal")
    P.obj("Tail", hull([(0, sy0 + 0.05, sz + 0.2), (0, sy0 + 0.45, sz + 0.2), (0, sy0 + 0.0, sz + 0.65), (0, sy0 + 0.12, sz + 0.65),
                        (0.03, sy0 + 0.2, sz + 0.3), (-0.03, sy0 + 0.2, sz + 0.3)]), lambda c, n: "Dark" if c.z > sz + 0.55 else "Base", 0, False)
    P.part("Muzzle", ball((0, sy0 + 1.68, sz - 0.06), (0.06, 0.04, 0.05), 8, 4), "Lamp", (0, sy0 + 1.68, sz - 0.06))
    return P


# ================================================================= 2026-10-11, round two: characters with faces
# "the rocket, the satellite and the station - new ones with a new shape, with features, that suit the place, something grand"

def eye(P, c, r, iris="Glass", glow="Lamp", look=(0.0, 0.0), name="Eye"):
    """a cartoon eye facing the player (+Y): a dark rim, a white, a big iris, a pupil and a catchlight."""
    c = Vector(c)
    P.obj(name, ball(tuple(c), (r * 1.12, r * 0.45, r * 1.12), 14, 7), "Dark")
    P.obj(name, ball(tuple(c + Vector((0, 0.03, 0))), (r, r * 0.45, r), 14, 7), "Base")
    ic = c + Vector((look[0] * r, r * 0.3, look[1] * r))
    P.obj(name, ball(tuple(ic), (r * 0.62, r * 0.3, r * 0.66), 12, 6), iris)
    P.obj(name, ball(tuple(ic + Vector((0, r * 0.12, 0))), (r * 0.3, r * 0.22, r * 0.34), 10, 5), "Dark")
    P.obj(name, ball(tuple(ic + Vector((r * 0.22, r * 0.25, r * 0.25))), (r * 0.13, r * 0.08, r * 0.13), 8, 4), glow)

def brow(P, c, w, tilt, paint="Dark", t=0.07):
    """an eyebrow facing the player, tilted (degrees about the nose axis)."""
    P.obj("Brow", box(tuple(c), (w, t * 0.9, t), Matrix.Rotation(math.radians(tilt), 3, "Y")), paint, 0, False)

def star_pts(c, r0, r1, dy=0.04, n=5):
    """a five-pointed star facing the player, as hull points."""
    c = Vector(c)
    return [tuple(c + Vector((math.sin(math.pi * k / n) * (r0 if k % 2 == 0 else r1), d, math.cos(math.pi * k / n) * (r0 if k % 2 == 0 else r1))))
            for k in range(2 * n) for d in (-dy, dy)]


# ================================================================= 1b. the cosmo hound
def S_hound():
    """The first dog in space grown to a hero: a husky in a red flight suit with gold epaulettes and a star medal, flying goggles pushed up
    on his brow, a radio headset with a glowing antenna, big brave blue eyes, a grin with his tongue out, a red cape streaming behind, a
    rocket pack blazing, a ray blaster in his paw and his fluffy tail curled up."""
    P = Boss("hound", {"Base": ((0.97, 0.97, 0.97), 0.35), "Belly": ((0.42, 0.47, 0.56), 0.35), "Accent": ((0.85, 0.10, 0.10), 0.55),
                       "Trim": ((0.98, 0.76, 0.22), 0.85), "Glass": ((0.25, 0.65, 1.0), 0.95), "Dark": ((0.07, 0.07, 0.09), 0.5),
                       "Glow": FLAME, "Metal": ((0.66, 0.68, 0.74), 0.8), "Lamp": ((0.75, 0.95, 1.0), 0.9)})
    H = Vector((0, 0.15, 1.95))
    def fur(c, n):
        r = c - H
        if r.y > 0.18 and r.z < 0.02: return "Base"                                   # the white mask
        if abs(r.x) < 0.07 and r.y > 0.2: return "Base"                               # the blaze up the forehead
        if 0.1 < abs(r.x) < 0.36 and 0.08 < r.z < 0.3 and r.y > 0.3: return "Base"    # the husky's brow spots
        return "Belly"
    P.obj("Head", ball(tuple(H), (0.68, 0.6, 0.6), 22, 11), fur, 1)
    P.obj("Cheeks", ball(tuple(H + Vector((0, 0.25, -0.2))), (0.62, 0.4, 0.34), 18, 9), "Base", 1)
    P.obj("Snout", ball(tuple(H + Vector((0, 0.58, -0.17))), (0.32, 0.26, 0.21), 16, 8), "Base", 1)
    P.obj("Nose", ball(tuple(H + Vector((0, 0.83, -0.07))), (0.12, 0.08, 0.085), 12, 6), "Dark", 1)
    P.obj("NoseShine", ball(tuple(H + Vector((0.03, 0.9, -0.03))), (0.035, 0.02, 0.025), 6, 3), "Lamp")
    # the grin: an open mouth, a tongue, two little fangs
    P.obj("Mouth", ball(tuple(H + Vector((0, 0.6, -0.36))), (0.21, 0.14, 0.1), 14, 7), "Dark")
    P.obj("Tongue", ball(tuple(H + Vector((0, 0.68, -0.43))), (0.11, 0.09, 0.09), 10, 5), "Accent", 1)
    for sx in (1, -1):
        P.obj("Fang", cone((sx * 0.11, H.y + 0.7, H.z - 0.3), (sx * 0.1, H.y + 0.72, H.z - 0.39), 0.025, 6), "Base", 0, False)
    # big brave eyes and determined brows
    for sx in (1, -1):
        eye(P, H + Vector((sx * 0.25, 0.5, 0.08)), 0.19, look=(sx * -0.05, 0.05))
        brow(P, H + Vector((sx * 0.26, 0.56, 0.32)), 0.26, sx * -16, "Dark", 0.08)
    # tall husky ears, red inside
    for sx in (1, -1):
        base = H + Vector((sx * 0.4, -0.05, 0.38))
        tip = H + Vector((sx * 0.62, -0.1, 1.0))
        P.obj("Ear", hull([tuple(base + Vector((dx, dy, 0))) for dx in (-0.17, 0.17) for dy in (-0.1, 0.1)] + [tuple(tip)]), "Belly", 0, False)
        P.obj("EarIn", hull([tuple(base + Vector((dx, 0.1, 0.06))) for dx in (-0.1, 0.1)] + [tuple(base + Vector((0, 0.13, 0.06)))] +
                            [tuple(tip + Vector((0, 0.06, -0.2))), tuple(base + Vector((0, 0.05, 0.1)))]), "Accent", 0, False)
    # the goggles pushed up on his brow, the headset
    P.obj("GoggleStrap", xf(torus(0.66, 0.035, 0.0, 30, 6), Matrix.Rotation(math.radians(16), 3, "X"), tuple(H + Vector((0, -0.03, 0.3)))), "Dark")
    muff = lathe([(0.0, 0.0), (0.16, 0.0), (0.17, 0.1), (0.0, 0.12)], 14, "x", tuple(H + Vector((0.62, -0.05, 0.02))))
    P.obj("Muff", muff.copy(), "Metal"); P.obj("Muff", mirror_x(muff), "Metal")
    for sx in (1, -1):
        gc = H + Vector((sx * 0.2, 0.5, 0.48))
        P.obj("Goggle", facing_y(torus(0.12, 0.04, 0.0, 18, 6), tuple(gc)), "Trim")
        P.obj("Lens", ball(tuple(gc + Vector((0, 0.02, 0))), (0.11, 0.04, 0.11), 12, 5), "Glass")
    P.obj("Mic", pipe([H + Vector((-0.7, 0.0, -0.05)), H + Vector((-0.6, 0.35, -0.3)), H + Vector((-0.38, 0.62, -0.35))], [0.025, 0.025, 0.02], 6), "Metal")
    P.obj("MicTip", ball(tuple(H + Vector((-0.36, 0.64, -0.35))), (0.05, 0.05, 0.05), 8, 4), "Dark")
    P.obj("Antenna", pipe([H + Vector((0.72, -0.05, 0.1)), H + Vector((0.8, -0.1, 0.75))], [0.02, 0.015], 6), "Metal")
    P.obj("AntennaTip", ball(tuple(H + Vector((0.8, -0.1, 0.8))), (0.07, 0.07, 0.07), 8, 4), "Lamp")
    # the body: a red flight suit, a white chest, a gold star medal, a gold collar ring
    P.obj("Collar", torus(0.38, 0.08, H.z - 0.6, 24, 8), "Trim")
    P.obj("Torso", ball((0, 0, 0.95), (0.55, 0.45, 0.62), 18, 9), lambda c, n: "Base" if c.y > 0.3 and abs(c.x) < 0.25 and c.z > 0.7 else "Accent", 1)
    P.obj("Belt", lathe([(0.5, 0.52), (0.54, 0.6), (0.54, 0.7), (0.5, 0.76)], 20, "z"), "Dark")
    for v in P.parts[-1].data.vertices: v.co.y *= 0.85
    P.obj("Buckle", box((0, 0.46, 0.64), (0.2, 0.06, 0.13)), "Trim", 0, False)
    P.obj("Medal", hull(star_pts((0, 0.47, 1.05), 0.14, 0.06, 0.03)), "Trim", 0, False)
    P.obj("Ribbon", box((0, 0.44, 1.24), (0.12, 0.04, 0.12)), "Glass", 0, False)
    for sx in (1, -1):   # gold epaulettes with a fringe
        ep = Vector((sx * 0.5, 0.0, 1.35))
        P.obj("Epaulette", ball(tuple(ep), (0.25, 0.25, 0.08), 14, 5), "Trim")
        for k in range(7):
            a = math.radians(-70 + 140 * k / 6)
            q = ep + Vector((sx * (0.18 + math.cos(a) * 0.05), math.sin(a) * 0.22, -0.02))
            P.obj("Fringe", pipe([q, q + Vector((sx * 0.03, 0, -0.18))], [0.025, 0.02], 5), "Trim")
    # the cape streaming behind
    rows = []
    for j in range(6):
        t = j / 5.0
        rows.append([(u * (0.5 + 0.55 * t), -0.4 - 0.75 * t, 1.38 - 1.35 * t + 0.08 * math.sin(u * 3.0 + t * 4)) for u in (-1, -0.5, 0, 0.5, 1)])
    polys = [[rows[j][i], rows[j][i + 1], rows[j + 1][i + 1], rows[j + 1][i]] for j in range(5) for i in range(4)]
    P.obj("Cloth", sheet(polys, 0.025), "Accent", 0, False)
    # the rocket pack
    P.obj("Pack", box((0, -0.45, 1.0), (0.7, 0.3, 0.7)), lambda c, n: "Trim" if c.z > 1.28 else "Base", 0, False)
    for sx in (1, -1):
        tx = sx * 0.24
        P.obj("Tank", lathe([(0.0, 0.42), (0.14, 0.48), (0.15, 1.38), (0.0, 1.55)], 14, "z", (tx, -0.65, 0)), lambda c, n: "Accent" if c.z > 1.3 else "Base")
        P.obj("Jet", lathe([(0.1, 0.44), (0.16, 0.26), (0.1, 0.28)], 12, "z", (tx, -0.65, 0)), "Dark")
        P.obj("JetFlame", lathe([(0.15, 0.27), (0.15, 0.0), (0.07, -0.45), (0.0, -0.62)], 12, "z", (tx, -0.65, 0)), "Glow")
        P.obj("JetCore", lathe([(0.08, 0.26), (0.08, 0.05), (0.0, -0.25)], 10, "z", (tx, -0.65, 0)), "Lamp")
    # the fluffy tail curled up behind
    tp = bez((0, -0.45, 0.55), (0, -1.0, 0.45), (0, -1.15, 1.0), (0, -0.85, 1.35), 10)
    P.obj("Tail", pipe(tp, [0.12, 0.16, 0.19, 0.2, 0.2, 0.19, 0.17, 0.15, 0.12, 0.08, 0.0], 12), lambda c, n: "Base" if c.z > 1.15 else "Belly", 1)
    # paws: the right holds a ray blaster, the left waves high
    for sx in (1, -1):
        name = "FlapR" if sx > 0 else "FlapL"
        sh = Vector((sx * 0.55, 0.05, 1.22))
        if sx > 0: el, hd = Vector((0.95, 0.25, 0.95)), Vector((1.0, 0.6, 0.92))
        else: el, hd = Vector((-0.98, 0.15, 1.15)), Vector((-1.05, 0.25, 1.5))
        P.part(name, pipe([sh, el, hd], [0.15, 0.13, 0.12], 10), "Accent", tuple(sh))
        P.part(name, ball(tuple(hd + Vector((0, 0.06, 0))), (0.15, 0.14, 0.14), 12, 6), "Base", tuple(sh), 1)
        if sx > 0:
            P.part(name, box(tuple(hd + Vector((0, 0.24, 0.12))), (0.14, 0.4, 0.18)), "Metal", tuple(sh), 0, False)
            P.part(name, pipe([hd + Vector((0, 0.42, 0.15)), hd + Vector((0, 0.72, 0.15))], [0.06, 0.05], 8), "Trim", tuple(sh))
            for k in range(3): P.part(name, pipe([hd + Vector((0, 0.48 + 0.08 * k, 0.15)), hd + Vector((0, 0.52 + 0.08 * k, 0.15))], [0.085, 0.085], 10), "Lamp", tuple(sh))
    # little legs and boots
    for sx in (1, -1):
        name = "SwayLegR" if sx > 0 else "SwayLegL"
        hip = Vector((sx * 0.24, 0.05, 0.5)); ft = Vector((sx * 0.3, 0.1, -0.1))
        P.part(name, pipe([hip, ft], [0.17, 0.15], 10), "Accent", tuple(hip))
        P.part(name, ball(tuple(ft + Vector((0, 0.1, -0.08))), (0.18, 0.26, 0.13), 12, 6), "Base", tuple(hip), 1)
    mz = (1.0, 1.35, 1.07)
    P.part("Muzzle", ball(mz, (0.07, 0.04, 0.07), 8, 4), "Lamp", mz)
    return P


# ================================================================= 2b. the moon king
def S_moonking():
    """The moon himself, crowned: a great cratered silver moon with a proud old face - glowing golden eyes under heavy brows, a noble nose,
    sweeping white moustaches and a long pointed beard - a gold crown set with sapphires and rubies, a royal blue collar spangled with gold,
    two floating white gloves (a star sceptre in one, a ringed golden orb in the other), and his court of little satellites orbiting him."""
    P = Boss("moonking", {"Base": ((0.90, 0.89, 0.84), 0.35), "Belly": ((0.64, 0.64, 0.66), 0.3), "Accent": ((0.38, 0.10, 0.62), 0.55),
                          "Trim": ((0.98, 0.76, 0.22), 0.9), "Glass": ((0.15, 0.30, 0.85), 0.95), "Dark": ((0.10, 0.10, 0.16), 0.5),
                          "Glow": ((0.20, 0.22, 0.55), 0.45), "Metal": ((0.97, 0.97, 1.0), 0.45), "Lamp": ((1.0, 0.82, 0.35), 0.9)})
    C = Vector((0, 0, 1.3)); R = 1.0
    rng = random.Random(4)
    craters = []
    for k in range(40):
        z = rng.uniform(-0.9, 0.95); a = rng.uniform(0, 2 * math.pi)
        d = Vector((math.sqrt(1 - z * z) * math.sin(a), math.sqrt(1 - z * z) * math.cos(a), z))
        if d.y > 0.3 and -0.8 < d.z < 0.75: continue          # keep the face clear
        craters.append((d, rng.uniform(0.07, 0.17)))
    def moon(c, n):
        d = (c - C).normalized()
        for (cd, cr) in craters:
            if (d - cd).length < cr: return "Belly"
        return "Base"
    P.obj("Moon", ball(tuple(C), (R, R * 0.92, R), 36, 18), moon, 1)
    for (cd, cr) in craters[:16]:   # a few raised crater rims
        q = C + Vector((cd.x * R, cd.y * R * 0.92, cd.z * R))
        P.obj("Crater", xf(torus(cr * R, 0.025, 0.0, 14, 4), cd.to_track_quat("Z", "Y").to_matrix(), tuple(q)), "Belly")
    # glowing eyes in dark sockets, heavy angry brows
    for sx in (1, -1):
        ec = C + Vector((sx * 0.34, R * 0.78, 0.2))
        P.obj("Socket", ball(tuple(ec), (0.25, 0.14, 0.17), 14, 7), "Dark")
        P.obj("EyeGlow", ball(tuple(ec + Vector((0, 0.06, 0))), (0.19, 0.1, 0.12), 14, 7), "Lamp")
        P.obj("Pupil", ball(tuple(ec + Vector((sx * -0.03, 0.12, -0.01))), (0.07, 0.05, 0.08), 10, 5), "Dark")
        P.obj("Brow", hull([tuple(C + Vector((sx * x, R * 0.86 + y, z))) for (x, z) in ((0.1, 0.36), (0.6, 0.5), (0.58, 0.38), (0.12, 0.28)) for y in (-0.06, 0.06)]), "Metal", 0, False)
    # a noble nose
    P.obj("Nose", hull([tuple(C + Vector(p)) for p in ((0, R * 0.92, 0.2), (0.11, R * 0.9, -0.12), (-0.11, R * 0.9, -0.12), (0, R * 1.15, -0.12),
                                                         (0.06, R * 1.05, -0.16), (-0.06, R * 1.05, -0.16), (0, R * 0.92, -0.2))]), "Base", 0, False)
    # sweeping moustaches and the long pointed beard
    for sx in (1, -1):
        m = bez(C + Vector((sx * 0.03, R * 1.0, -0.24)), C + Vector((sx * 0.35, R * 1.02, -0.28)), C + Vector((sx * 0.62, R * 0.86, -0.18)), C + Vector((sx * 0.8, R * 0.62, 0.05)), 10)
        P.obj("Moustache", pipe(m, [0.07, 0.1, 0.11, 0.11, 0.1, 0.09, 0.08, 0.06, 0.05, 0.03, 0.0], 10), "Metal", 1)
    P.obj("Mouth", box(tuple(C + Vector((0, R * 0.9, -0.42))), (0.3, 0.06, 0.05)), "Dark", 0, False)
    bd = bez(C + Vector((0, R * 0.78, -0.45)), C + Vector((0, R * 1.0, -0.95)), C + Vector((0, R * 0.95, -1.3)), C + Vector((0, R * 1.15, -1.7)), 8)
    P.obj("Beard", pipe(bd, [0.44, 0.43, 0.4, 0.34, 0.27, 0.2, 0.13, 0.07, 0.0], 16), "Metal", 2)
    for v in P.parts[-1].data.vertices: v.co.x *= 1.35
    # the crown
    cz = C.z + R * 0.78
    P.obj("Crown", lathe([(0.58, cz), (0.62, cz + 0.05), (0.62, cz + 0.25), (0.58, cz + 0.28)], 28, "z"), "Trim")
    for k in range(8):
        a = 2 * math.pi * k / 8
        base = Vector((math.sin(a) * 0.6, math.cos(a) * 0.6, cz + 0.25))
        P.obj("Spike", cone(tuple(base), tuple(base + Vector((math.sin(a) * 0.08, math.cos(a) * 0.08, 0.42 if k % 2 == 0 else 0.28))), 0.11, 6), "Trim", 0, False)
        P.obj("Pearl", ball(tuple(base + Vector((math.sin(a) * 0.09, math.cos(a) * 0.09, 0.46 if k % 2 == 0 else 0.32))), (0.05, 0.05, 0.05), 8, 4), "Metal")
        P.obj("Jewel", ball((math.sin(a) * 0.63, math.cos(a) * 0.63, cz + 0.14), (0.07, 0.04, 0.07), 10, 5), "Glass" if k % 2 == 0 else "Lamp")
    P.obj("Cap", ball((0, 0, cz + 0.26), (0.55, 0.55, 0.3), 20, 8), "Accent")
    P.obj("CrownStar", hull(star_pts((0, 0, cz + 0.72), 0.17, 0.07)), "Lamp", 0, False)
    # the royal collar of blue velvet spangled with gold
    P.obj("Collar", xf(lathe([(0.0, C.z - 0.7), (0.75, C.z - 0.72), (1.0, C.z - 0.9), (1.08, C.z - 1.08), (1.02, C.z - 1.1), (0.7, C.z - 0.88), (0.0, C.z - 0.85)], 32, "z"), None, (0, -0.25, 0)),
          lambda c, n: "Trim" if (c.xy.length > 1.18) or speckle(Vector((round(c.x * 5), round(c.y * 5), 0)), 2.1) > 0.9 else "Accent", 0, False)
    # two floating white gloves: a star sceptre and a ringed orb
    for sx in (1, -1):
        name = "FlapR" if sx > 0 else "FlapL"
        hub = (sx * 1.0, 0.2, C.z - 0.2)
        hc = Vector((sx * 1.45, 0.45, C.z - 0.35))
        P.part(name, ball(tuple(hc), (0.22, 0.2, 0.2), 14, 7), "Metal", hub, 1)
        P.part(name, lathe([(0.17, -0.35), (0.22, -0.2), (0.17, -0.12)], 14, "z", tuple(hc + Vector((sx * 0.05, -0.02, 0.0)))), "Trim", hub)
        if sx > 0:   # the sceptre
            P.part(name, pipe([hc + Vector((0, 0.05, -0.75)), hc + Vector((0, 0.05, 0.95))], [0.045, 0.045], 8), "Trim", hub)
            P.part(name, hull(star_pts(hc + Vector((0, 0.05, 1.12)), 0.24, 0.1, 0.06)), "Lamp", hub, 0, False)
        else:        # the golden orb with a ring
            oc = hc + Vector((0, 0.08, 0.36))
            P.part(name, ball(tuple(oc), (0.24, 0.24, 0.24), 16, 8), "Trim", hub, 1)
            P.part(name, xf(torus(0.38, 0.03, 0.0, 26, 4), Matrix.Rotation(math.radians(24), 3, "Y"), tuple(oc)), "Glass", hub)
            P.part(name, ball(tuple(oc + Vector((0, 0, 0.27))), (0.05, 0.05, 0.08), 8, 4), "Accent", hub)
    # his court: little satellites orbiting
    hub = (0, 0, C.z + 0.1)
    for k in range(6):
        a = 2 * math.pi * k / 6 + math.pi / 6   # none of them in front of his face
        q = Vector((math.sin(a) * 1.75, math.cos(a) * 1.75, C.z + 0.1))
        t = Vector((math.cos(a), -math.sin(a), 0))
        rot = Matrix.Rotation(-a, 3, "Z")
        P.part("SpinSats", box(tuple(q), (0.18, 0.18, 0.18), rot), "Trim", hub, 0, False)
        for sgn in (1, -1):
            P.part("SpinSats", box(tuple(q + t * sgn * 0.27), (0.3, 0.03, 0.16), rot), "Glass", hub, 0, False)
        P.part("SpinSats", ball(tuple(q + Vector((0, 0, 0.14))), (0.04, 0.04, 0.04), 6, 3), "Lamp", hub)
    mz = tuple(C + Vector((0, R * 0.98, -0.42)))
    P.part("Muzzle", ball(mz, (0.07, 0.04, 0.07), 8, 4), "Lamp", mz)
    return P


# ================================================================= 5b. the star admiral
def S_admiral():
    """The last boss: the admiral of the space fleet, a colossus from the waist up - a white-and-navy dress uniform with gold braid,
    epaulettes, a red sash and rows of medals, a chrome face with glowing eyes under stern brows, a curled gold moustache and a square jaw,
    the peaked cap with the winged star, great solar wings rising behind him like a cloak, one fist a cannon pointed at you, a brass
    telescope in the other, his lower half a ring of rocket engines blazing, and a squadron of little rockets circling his waist."""
    P = Boss("admiral", {"Base": ((0.96, 0.96, 0.97), 0.55), "Belly": ((0.08, 0.14, 0.38), 0.6), "Accent": ((0.85, 0.12, 0.10), 0.6),
                         "Trim": ((0.98, 0.76, 0.22), 0.9), "Glass": SOLAR, "Dark": ((0.06, 0.06, 0.08), 0.5),
                         "Glow": FLAME, "Metal": ((0.78, 0.80, 0.86), 0.92), "Lamp": ((0.45, 0.95, 1.0), 0.9)})
    # the engine skirt and the flames
    P.obj("Skirt", lathe([(0.0, -0.05), (0.95, -0.05), (1.0, 0.05), (0.82, 0.3), (0.68, 0.6), (0.62, 0.8), (0.0, 0.85)], 36, "z"),
          lambda c, n: "Trim" if c.z < 0.08 or 0.42 < c.z < 0.5 else "Belly", 1)
    for k in range(12):
        a = 2 * math.pi * k / 12
        P.obj("Rib", pipe([(math.sin(a) * 0.97, math.cos(a) * 0.97, 0.02), (math.sin(a) * 0.66, math.cos(a) * 0.66, 0.62)], [0.035, 0.03], 6), "Trim")
    for k in range(5):
        a = 2 * math.pi * k / 5 + math.pi / 5
        nc = (math.sin(a) * 0.55, math.cos(a) * 0.55, -0.02)
        P.obj("Nozzle", lathe([(0.12, 0.0), (0.2, -0.22), (0.24, -0.32), (0.18, -0.3), (0.08, -0.02)], 14, "z", nc), "Metal")
        P.obj("Flame", lathe([(0.22, -0.3), (0.24, -0.55), (0.14, -0.95), (0.0, -1.15)], 12, "z", nc), "Glow")
        P.obj("FlameCore", lathe([(0.12, -0.3), (0.12, -0.5), (0.0, -0.78)], 10, "z", nc), "Lamp")
    # the chest: white armour, navy sides, gold braid, a red sash, medals
    T = Vector((0, 0, 1.55))
    def uniform(c, n):
        if abs(c.x) > 0.55 and c.y < 0.3: return "Belly"
        if abs(c.x - (c.z - 1.55) * 0.6) < 0.1 and c.y > 0.2: return "Accent"     # the sash, shoulder to hip
        return "Base"
    P.obj("Chest", ball(tuple(T), (0.85, 0.6, 0.85), 40, 20), uniform, 1)
    P.obj("Waist", lathe([(0.62, 0.75), (0.68, 0.9), (0.62, 1.05)], 24, "z"), "Trim")
    for row in range(3):
        for k in range(4 - row):
            P.obj("MedalBar", box((-0.62 + k * 0.13 + row * 0.065, 0.5 - row * 0.005, 1.85 - row * 0.13), (0.11, 0.1, 0.06)), ("Accent", "Glass", "Trim", "Belly")[(k + row) % 4], 0, False)
    P.obj("Medal", hull(star_pts((-0.42, 0.56, 1.35), 0.12, 0.05, 0.03)), "Trim", 0, False)
    P.obj("Medal", ball((0.35, 0.58, 1.25), (0.1, 0.04, 0.1), 12, 5), "Lamp")
    # epaulettes with a heavy gold fringe
    for sx in (1, -1):
        ep = Vector((sx * 0.85, 0.0, 2.15))
        P.obj("Epaulette", ball(tuple(ep), (0.36, 0.34, 0.1), 16, 6), "Trim")
        P.obj("EpauletteNavy", ball(tuple(ep + Vector((0, 0, 0.05))), (0.25, 0.24, 0.06), 14, 5), "Belly")
        for k in range(9):
            a = math.radians(-80 + 160 * k / 8)
            q = ep + Vector((sx * (0.28 + math.cos(a) * 0.06), math.sin(a) * 0.3, -0.03))
            P.obj("Fringe", pipe([q, q + Vector((sx * 0.04, 0, -0.26))], [0.03, 0.025], 5), "Trim")
    # the head: a chrome face with a square jaw (built at one size, then grown about the neck)
    Hc = Vector((0, 0.15, 2.65))
    HK = 1.3; i0 = len(P.parts)
    P.obj("Neck", lathe([(0.25, 2.1), (0.28, 2.3), (0.26, 2.4)], 16, "z", (0, 0.1, 0)), "Metal")
    P.obj("Collar", lathe([(0.34, 2.15), (0.38, 2.3), (0.33, 2.35)], 20, "z", (0, 0.1, 0)), "Belly")
    P.obj("Head", hull([tuple(Hc + Vector((sx * w, y, z))) for sx in (-1, 1) for (w, y, z) in
                        ((0.4, 0.3, 0.25), (0.42, -0.25, 0.25), (0.38, 0.38, -0.05), (0.3, 0.42, -0.3), (0.36, -0.2, -0.3), (0.2, 0.4, -0.42), (0.25, -0.1, -0.45))]), "Metal", 0, False)
    for sx in (1, -1):
        rot = Matrix.Rotation(math.radians(sx * -10), 3, "Y")
        P.obj("Socket", box(tuple(Hc + Vector((sx * 0.17, 0.39, 0.08))), (0.22, 0.06, 0.1), rot), "Dark", 0, False)
        P.obj("EyeGlow", box(tuple(Hc + Vector((sx * 0.17, 0.42, 0.075))), (0.17, 0.04, 0.05), rot), "Lamp", 0, False)
        brow(P, Hc + Vector((sx * 0.18, 0.42, 0.19)), 0.28, sx * -18, "Dark", 0.07)
        m = bez(Hc + Vector((sx * 0.02, 0.45, -0.15)), Hc + Vector((sx * 0.2, 0.5, -0.2)), Hc + Vector((sx * 0.35, 0.45, -0.1)), Hc + Vector((sx * 0.42, 0.38, 0.03)), 8)
        P.obj("Moustache", pipe(m, [0.05, 0.07, 0.075, 0.07, 0.06, 0.05, 0.04, 0.03, 0.0], 8), "Trim", 1)
        P.obj("Ear", box(tuple(Hc + Vector((sx * 0.43, 0.0, 0.0))), (0.06, 0.18, 0.22)), "Belly", 0, False)
    P.obj("Nose", hull([tuple(Hc + Vector(p)) for p in ((0, 0.41, 0.08), (0.06, 0.44, -0.1), (-0.06, 0.44, -0.1), (0, 0.52, -0.1))]), "Metal", 0, False)
    P.obj("Mouth", box(tuple(Hc + Vector((0, 0.41, -0.3))), (0.24, 0.04, 0.05)), "Dark", 0, False)
    # the peaked cap with the winged star
    cz = Hc.z + 0.26
    P.obj("CapBand", lathe([(0.47, cz - 0.02), (0.49, cz + 0.12), (0.47, cz + 0.14)], 26, "z", (0, 0.05, 0)), "Belly")
    P.obj("CapTop", lathe([(0.47, cz + 0.12), (0.62, cz + 0.3), (0.6, cz + 0.36), (0.0, cz + 0.36)], 26, "z", (0, 0.02, 0)), "Base")
    P.obj("Brim", hull([(sx * 0.42, 0.3, cz + 0.02) for sx in (-1, 1)] + [(sx * 0.4, 0.66, cz - 0.1) for sx in (-1, 1)] + [(0, 0.76, cz - 0.12)] +
                       [(sx * 0.42, 0.3, cz + 0.05) for sx in (-1, 1)] + [(sx * 0.4, 0.66, cz - 0.07) for sx in (-1, 1)] + [(0, 0.76, cz - 0.09)]), "Dark", 0, False)
    P.obj("Braid", pipe([(-0.42, 0.52, cz + 0.02), (0, 0.6, cz + 0.02), (0.42, 0.52, cz + 0.02)], [0.025, 0.025, 0.025], 6), "Trim")
    ec = Vector((0, 0.56, cz + 0.16))
    P.obj("CapStar", hull(star_pts(ec, 0.11, 0.045, 0.03)), "Trim", 0, False)
    for sx in (1, -1):
        P.obj("CapWing", hull([tuple(ec + Vector(p)) for p in ((sx * 0.08, 0, 0.02), (sx * 0.34, -0.06, 0.1), (sx * 0.3, -0.06, 0.0), (sx * 0.08, 0.02, -0.04), (sx * 0.2, -0.02, -0.05))]), "Trim", 0, False)
    piv = Vector((0, 0.15, 2.25))
    for o in P.parts[i0:]:
        for v in o.data.vertices: v.co = piv + (v.co - piv) * HK + Vector((0, 0.05, 0.0))
    # the solar wings rising behind him, tilting
    for sx in (1, -1):
        name = "SwayWingR" if sx > 0 else "SwayWingL"
        hub = (sx * 0.5, -0.55, 1.9)
        P.obj("WingMount", ball(hub, (0.18, 0.18, 0.18), 10, 5), "Trim")
        P.part(name, pipe([Vector(hub), Vector((sx * 2.55, -0.75, 3.15))], [0.06, 0.04], 8), "Trim", hub)
        for k in range(3):
            x0 = 0.75 + k * 0.62; xc = x0 + 0.27
            zc = 2.0 + k * 0.42; h = 1.3 - k * 0.22
            P.part(name, box((sx * xc, -0.75, zc), (0.56, 0.04, h)), "Trim", hub, 0, False)
            for i in range(2):
                for j in range(4):
                    P.part(name, box((sx * (xc - 0.135 + i * 0.27), -0.72, zc - h / 2 + (j + 0.5) * h / 4), (0.23, 0.03, h / 4 * 0.86)), "Glass", hub, 0, False)
    # the right fist is a cannon aimed at you; the left holds a brass telescope
    for sx in (1, -1):
        name = "FlapR" if sx > 0 else "FlapL"
        sh = Vector((sx * 0.95, 0.05, 1.95))
        el = Vector((sx * 1.3, 0.3, 1.45))
        hd = Vector((1.25, 0.85, 1.4)) if sx > 0 else Vector((-1.2, 0.6, 1.75))
        P.part(name, ball(tuple(sh), (0.3, 0.3, 0.3), 12, 6), "Base", tuple(sh), 1)
        P.part(name, pipe([sh, el], [0.24, 0.21], 12), "Belly", tuple(sh))
        P.part(name, ball(tuple(el), (0.2, 0.2, 0.2), 10, 5), "Metal", tuple(sh))
        P.part(name, pipe([el, hd], [0.2, 0.18], 12), "Belly", tuple(sh))
        cuff = hd - (hd - el).normalized() * 0.08
        P.part(name, pipe([cuff - (hd - el).normalized() * 0.06, cuff + (hd - el).normalized() * 0.06], [0.22, 0.22], 14), "Trim", tuple(sh))
        if sx > 0:
            P.part(name, pipe([hd, hd + Vector((0, 0.55, 0))], [0.22, 0.2], 14), "Metal", tuple(sh))
            for k in range(3): P.part(name, pipe([hd + Vector((0, 0.15 + 0.15 * k, 0)), hd + Vector((0, 0.2 + 0.15 * k, 0))], [0.24, 0.24], 14), "Trim", tuple(sh))
            P.part(name, lathe([(0.14, 0.0), (0.16, 0.04), (0.0, 0.05)], 14, "y", tuple(hd + Vector((0, 0.55, 0)))), "Lamp", tuple(sh))
        else:
            P.part(name, ball(tuple(hd + Vector((0, 0.05, 0))), (0.2, 0.2, 0.2), 12, 6), "Base", tuple(sh), 1)
            P.part(name, pipe([hd + Vector((0.0, -0.1, -0.5)), hd + Vector((0.0, 0.3, 0.7))], [0.06, 0.09], 10), "Trim", tuple(sh))
            P.part(name, ball(tuple(hd + Vector((0.0, 0.31, 0.72))), (0.09, 0.03, 0.09), 8, 4), "Glass", tuple(sh))
    # a squadron of little rockets circling his waist
    hub = (0, 0, 0.75)
    for k in range(8):
        a = 2 * math.pi * k / 8
        q = Vector((math.sin(a) * 1.55, math.cos(a) * 1.55, 0.75))
        P.part("SpinRockets", lathe([(0.0, -0.18), (0.08, -0.16), (0.09, 0.05), (0.06, 0.18), (0.0, 0.26)], 10, "z", tuple(q)), lambda c, n: "Accent" if c.z > 0.85 else "Base", hub)
        P.part("SpinRockets", lathe([(0.06, -0.18), (0.08, -0.32), (0.0, -0.42)], 8, "z", tuple(q)), "Glow", hub)
    mz = (1.25, 1.42, 1.4)
    P.part("Muzzle", ball(mz, (0.08, 0.04, 0.08), 8, 4), "Lamp", mz)
    return P


# ================================================================= 1c. the comet phoenix
def plume(a, b, w, t=0.035, n=7, curl=(0, 0, 0), nrm=(0, 0, 1)):
    """a feather from a to b: a leaf of width w (widest at 60%), t thick, lying in the plane whose normal is nrm, its tip bent by curl."""
    a, b, curl, nrm = Vector(a), Vector(b), Vector(curl), Vector(nrm).normalized()
    d = (b - a); side = d.cross(nrm)
    if side.length < 1e-4: side = Vector((1, 0, 0))
    side.normalize(); up = side.cross(d).normalized()
    pts = []
    for i in range(n + 1):
        u = i / n
        c = a + d * u + curl * (u * u)
        hw = w * (math.sin(math.pi * 0.5 * u / 0.6) if u <= 0.6 else 0.15 + 0.85 * (1 - u) / 0.4)
        for sgn in (1, -1):
            for tt in (t, -t):
                pts.append(tuple(c + side * hw * sgn + up * tt))
    return hull(pts)

def S_phoenix():
    """The comet phoenix, displayed like a crest: a majestic golden firebird rising at the player - a crowned head with fierce glowing eyes
    under gold brow ridges, a silver hooked beak, a sapphire on its brow and a great fan of flame feathers behind it, a sapphire set in its
    breast, two vast raised wings of gold and white-gold feathers tipped with fire beating slowly, and a comet's tail of long plumes with
    sapphire eyes streaming below it, a blaze of fire at their root."""
    P = Boss("phoenix", {"Base": ((1.0, 0.80, 0.42), 0.65), "Belly": ((1.0, 0.97, 0.86), 0.4), "Accent": ((0.92, 0.26, 0.04), 0.6),
                         "Trim": ((0.98, 0.68, 0.14), 0.92), "Glass": ((0.15, 0.40, 1.0), 0.97), "Dark": ((0.12, 0.05, 0.03), 0.5),
                         "Glow": ((0.95, 0.20, 0.02), 0.5), "Metal": ((0.85, 0.87, 0.92), 0.9), "Lamp": ((0.55, 0.95, 1.0), 0.9)})
    FWD = (0, 1, 0)
    # the body, upright, its breast to the player
    P.obj("Body", ball((0, 0, 0.55), (0.42, 0.36, 0.62), 20, 10), lambda c, n: "Belly" if n.y > 0.35 else "Trim", 1)
    for row in range(4):   # breast feathers, scale on scale
        for k in range(-2, 3):
            x = k * 0.16 - (0.08 if row % 2 else 0)
            if abs(x) > 0.3 - row * 0.02: continue
            z = 0.95 - row * 0.17
            P.obj("BreastFeather", plume((x, 0.3 + 0.02 * row, z + 0.08), (x, 0.36 + 0.02 * row, z - 0.13), 0.09, 0.02, 5, nrm=FWD), "Belly", 0, False)
    P.obj("Setting", facing_y(torus(0.14, 0.04, 0.0, 20, 6), (0, 0.38, 0.32)), "Trim")
    P.obj("Gem", ball((0, 0.39, 0.32), (0.12, 0.06, 0.14), 14, 7), "Glass")
    P.obj("Neck", pipe([(0, 0.0, 0.95), (0, 0.1, 1.2), (0, 0.18, 1.35)], [0.3, 0.25, 0.22], 16), "Trim", 1)
    # the head (built at one size, then grown about the neck)
    Hd = Vector((0, 0.2, 1.55)); i0 = len(P.parts)
    P.obj("Head", ball(tuple(Hd), (0.3, 0.33, 0.28), 18, 9), lambda c, n: "Belly" if c.z < Hd.z - 0.1 and n.y > 0.3 else "Trim", 1)
    P.obj("Beak", hull([tuple(Hd + Vector(p)) for p in ((0.12, 0.24, 0.02), (-0.12, 0.24, 0.02), (0.09, 0.22, -0.13), (-0.09, 0.22, -0.13),
                                                          (0, 0.5, -0.06), (0, 0.56, -0.17), (0, 0.48, -0.26), (0.045, 0.4, -0.2), (-0.045, 0.4, -0.2))]), "Metal", 1, True)
    P.obj("BeakTip", hull([tuple(Hd + Vector(p)) for p in ((0, 0.56, -0.17), (0.03, 0.5, -0.21), (-0.03, 0.5, -0.21), (0, 0.48, -0.28))]), "Trim", 0, False)
    for sx in (1, -1):
        ec = Hd + Vector((sx * 0.155, 0.255, 0.07))
        rot = Matrix.Rotation(math.radians(sx * -22), 3, "Y")
        P.obj("Socket", box(tuple(ec), (0.18, 0.07, 0.09), rot), "Dark", 0, False)
        P.obj("EyeGlow", box(tuple(ec + Vector((0, 0.03, 0.0))), (0.14, 0.05, 0.055), rot), "Lamp", 0, False)
        P.obj("BrowRidge", box(tuple(ec + Vector((sx * 0.01, 0.02, 0.09))), (0.24, 0.09, 0.055), Matrix.Rotation(math.radians(sx * -28), 3, "Y")), "Trim", 0, False)
        for k in range(3):   # flame plumes sweeping back from the cheeks
            P.obj("Cheek", plume(Hd + Vector((sx * 0.22, 0.05, -0.05 + 0.06 * k)), Hd + Vector((sx * (0.55 + 0.05 * k), -0.15, -0.2 + 0.22 * k)), 0.08, 0.02, 5, nrm=FWD), "Accent", 0, False)
    # the crown and the brow sapphire
    P.obj("Crown", xf(lathe([(0.22, 0.0), (0.24, 0.03), (0.24, 0.11), (0.22, 0.12)], 24, "z"), Matrix.Rotation(math.radians(-15), 3, "X"), tuple(Hd + Vector((0, -0.02, 0.18)))), "Trim")
    for k in range(7):
        a = math.radians(-75 + 25 * k)
        base = Hd + Vector((math.sin(a) * 0.23, math.cos(a) * 0.23 - 0.02, 0.29 - 0.06 * math.cos(a)))
        P.obj("CrownSpike", cone(tuple(base), tuple(base + Vector((math.sin(a) * 0.05, 0.0, 0.24 if k % 2 == 1 else 0.15))), 0.055, 6), "Trim", 0, False)
        P.obj("CrownPearl", ball(tuple(base + Vector((math.sin(a) * 0.05, 0.0, 0.26 if k % 2 == 1 else 0.17))), (0.035, 0.035, 0.035), 6, 3), "Belly")
    P.obj("BrowGem", ball(tuple(Hd + Vector((0, 0.27, 0.22))), (0.065, 0.04, 0.075), 10, 5), "Glass")
    # the great fan of flame feathers behind the head
    for k in range(9):
        a = math.radians(-64 + 16 * k)
        r = Hd + Vector((math.sin(a) * 0.12, -0.22, 0.1 + math.cos(a) * 0.12))
        L = 0.95 - 0.1 * abs(k - 4) ** 1.2
        tip = r + Vector((math.sin(a) * L, -0.12, math.cos(a) * L))
        P.obj("Crest", plume(r, tip, 0.13, 0.025, 6, (math.sin(a) * 0.1, 0, 0.06), nrm=FWD),
              lambda c, n, r=r, L=L: "Accent" if (c - r).length > L * 0.55 else "Trim", 0, False)
    piv = Vector((0, 0.15, 1.3))
    for o in P.parts[i0:]:
        for v in o.data.vertices: v.co = piv + (v.co - piv) * 1.45
    Hd = piv + (Hd - piv) * 1.45
    # the wings, raised and spread: an arm and two rows of feathers hanging from it in the plane facing the player
    for sx in (1, -1):
        name = "FlapR" if sx > 0 else "FlapL"
        sh = Vector((sx * 0.35, -0.1, 0.85))
        arm = bez(sh, Vector((sx * 0.85, -0.15, 1.35)), Vector((sx * 1.35, -0.3, 1.8)), Vector((sx * 1.8, -0.4, 2.1)), 14)
        P.part(name, pipe(arm, [0.17 - 0.12 * i / 14 for i in range(15)], 10), "Trim", tuple(sh), 1)
        for i, q in enumerate(arm[1:]):
            u = (i + 1) / 14.0
            d = Vector((sx * (0.12 + 1.15 * u), -0.15, -(1.0 - 1.25 * u))).normalized()
            L = 0.65 + 0.65 * math.sin(math.pi * min(1.0, u * 1.25) * 0.5)
            P.part(name, plume(q, q + d * L, 0.17, 0.03, 7, Vector((sx * 0.1, -0.08, 0.08)), nrm=FWD),
                   lambda c, n, q=q, L=L: "Accent" if (c - q).length > L * 0.7 else ("Base" if (c - q).length > L * 0.32 else "Trim"), tuple(sh), 0, False)
            if i % 2 == 0:   # gold coverts over their roots
                P.part(name, plume(q + Vector((0, 0.05, 0)), q + Vector((0, 0.05, 0)) + d * L * 0.42, 0.17, 0.03, 5, nrm=FWD), "Trim", tuple(sh), 0, False)
    # the comet's tail streaming below and behind: long plumes with sapphire eyes, a blaze of fire at their root
    for k in range(7):
        a = (k - 3) / 3.0
        r = Vector((a * 0.12, -0.15, 0.05))
        tip = Vector((a * 1.05, -1.25 - 0.25 * (1 - abs(a)), -2.35 + 0.5 * abs(a)))
        P.obj("TailPlume", plume(r, tip, 0.17 if k != 3 else 0.21, 0.03, 9, (a * 0.25, -0.1, 0.0), nrm=(0, 1, -0.5)),
              lambda c, n, r=r: "Accent" if (c - r).length > 1.35 else ("Base" if (c - r).length > 0.6 else "Trim"), 0, False)
        e = r + (tip - r) * 0.84 + Vector((a * 0.25, -0.1, 0.0)) * 0.7 + Vector((0, 0.06, 0.03))
        P.obj("TailEye", facing_y(ball((0, 0, 0), (0.08, 0.11, 0.025), 10, 4), tuple(e)), "Glass")
        P.obj("TailEyeRim", facing_y(ball((0, 0, 0), (0.13, 0.17, 0.02), 10, 4), tuple(e - Vector((0, 0.01, 0)))), "Trim")
    P.obj("Blaze", lathe([(0.0, 0.1), (0.2, -0.02), (0.2, -0.25), (0.1, -0.6), (0.0, -0.85)], 14, "z", (0, -0.18, 0)), "Glow")
    P.obj("BlazeCore", lathe([(0.0, 0.05), (0.11, -0.03), (0.11, -0.22), (0.0, -0.45)], 12, "z", (0, -0.12, 0)), "Lamp")
    # talons, gold, curled forward
    for sx in (1, -1):
        P.obj("Leg", pipe([(sx * 0.17, 0.1, 0.1), (sx * 0.2, 0.25, -0.12)], [0.065, 0.055], 8), "Trim")
        for k in range(3):
            a = math.radians(-30 + 30 * k)
            P.obj("Claw", cone((sx * 0.2, 0.26, -0.14), (sx * 0.2 + math.sin(a) * 0.15, 0.26 + math.cos(a) * 0.14, -0.24), 0.04, 6), "Metal", 0, False)
    mz = tuple(Hd + Vector((0, 0.56, -0.17)))
    P.part("Muzzle", ball(mz, (0.06, 0.04, 0.06), 8, 4), "Lamp", mz)
    return P

BOSSES = [("rocket", S_rocket), ("satellite", S_satellite), ("mech", S_mech), ("lander", S_lander), ("station", S_station),
          ("hound", S_hound), ("moonking", S_moonking), ("admiral", S_admiral), ("phoenix", S_phoenix)]

if __name__ == "__main__":
    os.makedirs(AB.OUT, exist_ok=True)
    for bid, fn in BOSSES:
        if ONLY and bid not in ONLY: continue
        fn().finish()
    print("DONE")
