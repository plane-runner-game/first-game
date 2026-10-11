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


BOSSES = [("rocket", S_rocket), ("satellite", S_satellite), ("mech", S_mech), ("lander", S_lander), ("station", S_station)]

if __name__ == "__main__":
    os.makedirs(AB.OUT, exist_ok=True)
    for bid, fn in BOSSES:
        if ONLY and bid not in ONLY: continue
        fn().finish()
    print("DONE")
