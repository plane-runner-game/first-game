# Sky Squad, the soccer field's five bosses (2026-10-11: "the rest of the bosses for the maps that don't have them yet"): the striker
# bot, the whistle referee, the stadium blimp, the goalkeeper giant and the golden trophy titan. Built from code like the other worlds'
# bosses (alien_bosses.py lends its Boss class and shapes).
# Run: blender -b -P Tools/blender/soccer_bosses.py -- <out dir> [export] [ids,comma,separated]
# Conventions as alien_bosses.py: +Y nose, +Z up, +X right; "Flap*" rock about the nose axis, "Sway*" about the wing axis, "Spin*" turn slowly
# about up, "Roll*" slowly about the nose axis, "Wheel*" fast about the wing axis, "Prop*" / "Rotor*" fast (blur disc), "Cloth" stays still
# without the outline, "Muzzle" is where his shots leave from.
import bpy, bmesh, math, sys, os, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mathutils import Vector, Matrix
from enemy_planes import loft, sweep, lathe, box, hull, tube, mirror_x, airfoil
import alien_bosses as AB
from alien_bosses import Boss, xf, ball, pipe, cone, bez, torus, sheet, grow, ang

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ONLY = argv[2].split(",") if len(argv) > 2 and argv[2] else None

GOLD = ((0.98, 0.76, 0.22), 0.8)
WHITE = ((0.97, 0.97, 0.97), 0.45)
INK = ((0.05, 0.05, 0.07), 0.5)
PITCH = ((0.20, 0.72, 0.22), 0.4)

# ---- a football: black pentagons on white (a truncated icosahedron painted on a sphere)
_PHI = (1 + 5 ** 0.5) / 2
ICO = [Vector(v).normalized() for v in
       [(0, s1, s2 * _PHI) for s1 in (1, -1) for s2 in (1, -1)] +
       [(s1, s2 * _PHI, 0) for s1 in (1, -1) for s2 in (1, -1)] +
       [(s2 * _PHI, 0, s1) for s1 in (1, -1) for s2 in (1, -1)]]
_NB = []
for v in ICO:
    nb = max((w for w in ICO if w is not v), key=lambda w: v.dot(w))
    e1 = (nb - v * v.dot(nb)).normalized(); _NB.append((e1, v.cross(e1)))
APO = math.radians(17.5)

def football(d, white="Belly", black="Dark", seam=None):
    """the slot for a direction d from a football's centre."""
    d = Vector(d)
    if d.length < 1e-6: return white
    d.normalize()
    i = max(range(12), key=lambda k: ICO[k].dot(d)); v = ICO[i]
    phi = math.acos(max(-1.0, min(1.0, v.dot(d))))
    e1, e2 = _NB[i]
    th = math.degrees(math.atan2(d.dot(e2), d.dot(e1)))
    a = math.radians(((th - 36.0) % 72.0) - 36.0)
    r = phi * math.cos(a)
    if r < APO: return black
    if seam and r < APO + 0.035: return seam
    return white

def ball_mesh(c, r, seg=36, rings=18):
    return ball(c, (r, r, r), seg, rings)

def flame(P, base, tip, r, core=True):
    P.obj("Flame", cone(base, tip, r, 8), "Glow", 0, False)
    if core:
        b = Vector(base); t = Vector(tip)
        P.obj("FlameCore", cone(tuple(b + (t - b) * 0.05), tuple(b + (t - b) * 0.6), r * 0.55, 8), "Lamp", 0, False)


# ================================================================= 1. the striker bot
def S_ballbot():
    """A giant football rolling through the sky inside a red steel yoke: a robot head on top with a visor and two angry glowing eyes, jet
    pods on its axles, flames below - the ball turns as it rolls."""
    P = Boss("ballbot", {"Base": ((0.86, 0.12, 0.10), 0.6), "Belly": WHITE, "Accent": ((0.10, 0.30, 0.85), 0.55), "Trim": GOLD,
                         "Glass": ((0.10, 0.12, 0.18), 0.95), "Dark": INK, "Glow": ((1.0, 0.55, 0.15), 0.5),
                         "Metal": ((0.62, 0.64, 0.70), 0.75), "Lamp": ((1.0, 0.92, 0.35), 0.8)})
    hub = (0, 0, 0)
    P.part("WheelBall", ball_mesh(hub, 1.0, 48, 24), lambda c, n: football(c, "Belly", "Dark", "Metal"), hub, 1)
    # the yoke: a ring round the ball along the flight, axles left and right
    ring = torus(1.12, 0.06, 0.0, 44, 8); xf(ring, Matrix.Rotation(math.radians(90), 3, "Y"))
    P.obj("Yoke", ring, "Base")
    for s in (1, -1):
        P.obj("Axle", pipe([(s * 1.02, 0, 0), (s * 1.38, 0, 0)], [0.13, 0.13], 12), "Metal")
        P.obj("Hubcap", lathe([(0.0, 0.0), (0.24, 0.0), (0.24, s * 0.1), (0.0, s * 0.16)], 16, "x", (s * 1.36, 0, 0)), "Trim")
        # the jet pods on the axles
        pc = Vector((s * 1.62, 0.05, 0.0))
        P.obj("Pod", loft([(0.75, 0.0, 0.0, pc.x, 0), (0.6, 0.2, 0.2, pc.x, 0), (0.2, 0.3, 0.3, pc.x, 0), (-0.45, 0.27, 0.27, pc.x, 0), (-0.65, 0.2, 0.2, pc.x, 0)], 16, False, True),
              lambda c, n: "Accent" if c.y > 0.45 else ("Belly" if abs(c.y - 0.0) < 0.08 else "Base"), 1)
        P.obj("Nozzle", lathe([(0.2, -0.62), (0.22, -0.78), (0.15, -0.78)], 14, "y", (pc.x, 0, 0)), "Metal")
        flame(P, (pc.x, -0.78, 0), (pc.x, -1.45, 0), 0.15)
        P.obj("Fin", sheet([[(pc.x, -0.2, 0.25), (pc.x, -0.6, 0.6), (pc.x, -0.65, 0.2)]], 0.05), "Accent", 0, False)
        P.obj("Fin", sheet([[(pc.x + s * 0.25, -0.2, 0.0), (pc.x + s * 0.6, -0.65, -0.05), (pc.x + s * 0.25, -0.65, -0.05)]], 0.05), "Accent", 0, False)
    # the head on top of the yoke
    hc = Vector((0, 0.05, 1.42))
    P.obj("Neck", pipe([(0, 0, 1.12), (0, 0.02, 1.3)], [0.18, 0.15], 12), "Metal")
    P.obj("Head", ball(tuple(hc), (0.55, 0.45, 0.36), 18, 9), lambda c, n: "Belly" if n.z > 0.85 else "Base", 1)
    P.obj("Stripe", torus(0.5, 0.04, 0.0, 28, 6), "Belly"); P.parts[-1].data.transform(Matrix.Translation(tuple(hc)) @ Matrix.Rotation(math.radians(90), 4, "Y") @ Matrix.Scale(0.85, 4))
    visor = ball((0, 0, 0), (0.42, 0.18, 0.15), 18, 8); xf(visor, None, (0, hc.y + 0.32, hc.z + 0.02))
    P.obj("Visor", visor, "Glass")
    for s in (1, -1):
        eye = ball((0, 0, 0), (0.11, 0.05, 0.08), 12, 6); xf(eye, Matrix.Rotation(math.radians(s * 12), 3, "Y"), (s * 0.18, hc.y + 0.47, hc.z + 0.04))
        P.obj("Eye", eye, "Lamp")
        P.obj("Brow", box((s * 0.19, hc.y + 0.47, hc.z + 0.16), (0.2, 0.05, 0.05), Matrix.Rotation(math.radians(-s * 18), 3, "Y")), "Dark", 0, False)
        P.obj("Ear", lathe([(0.0, 0.0), (0.14, 0.0), (0.14, s * 0.08), (0.0, s * 0.1)], 12, "x", (s * 0.52, hc.y, hc.z)), "Accent")
    # a horn of a mohawk: a crest of red-white fins
    for k in range(4):
        y = hc.y + 0.25 - k * 0.2
        P.obj("Crest", cone((0, y, hc.z + 0.3), (0, y - 0.18, hc.z + 0.62 - k * 0.06), 0.09, 6), "Accent" if k % 2 == 0 else "Belly", 0, False)
    P.obj("Antenna", pipe([(0.3, hc.y - 0.1, hc.z + 0.25), (0.42, hc.y - 0.2, hc.z + 0.6)], [0.025, 0.02], 6), "Metal")
    P.obj("AntennaTip", ball((0.42, hc.y - 0.2, hc.z + 0.62), (0.06, 0.06, 0.06), 8, 4), "Lamp")
    # flames from under the ball where the yoke ends
    flame(P, (0, 0, -1.2), (0, -0.25, -1.75), 0.18)
    P.obj("Thruster", lathe([(0.24, -1.05), (0.26, -1.25), (0.18, -1.25)], 14, "z"), "Metal")
    P.part("Muzzle", ball((0, hc.y + 0.5, hc.z - 0.12), (0.07, 0.03, 0.05), 8, 4), "Lamp", (0, hc.y + 0.5, hc.z - 0.12))
    return P


# ================================================================= 2. the whistle referee
def S_referee():
    """A flying robot referee under a propeller cap: a black-and-white striped shirt, a chrome head with a stern visor and a whistle at
    his mouth, a red card held high in one hand and a yellow card thrust forward in the other, legs kicking."""
    P = Boss("referee", {"Base": WHITE, "Belly": ((0.88, 0.89, 0.92), 0.4), "Accent": INK, "Trim": ((1.0, 0.86, 0.10), 0.55),
                         "Glass": ((0.08, 0.10, 0.16), 0.95), "Dark": ((0.02, 0.02, 0.03), 0.5), "Glow": ((1.0, 0.08, 0.06), 0.5),
                         "Metal": ((0.72, 0.74, 0.80), 0.85), "Lamp": ((0.55, 0.95, 1.0), 0.8)})
    stripes = lambda c, n: "Accent" if int(math.floor((math.atan2(c.x, c.y) + math.pi) / (2 * math.pi) * 14)) % 2 == 0 else "Base"
    shirt = lathe([(0.0, 0.0), (0.42, 0.02), (0.5, 0.3), (0.56, 0.7), (0.58, 0.95), (0.42, 1.1), (0.0, 1.12)], 28, "z")
    for v in shirt.verts: v.co.y *= 0.72
    P.obj("Shirt", shirt, stripes, 1)
    P.obj("Collar", torus(0.24, 0.06, 1.1, 18, 6), "Accent")
    P.obj("Shorts", lathe([(0.0, 0.02), (0.44, 0.02), (0.47, -0.25), (0.0, -0.28)], 24, "z"), "Accent")
    for v in P.parts[-1].data.vertices: v.co.y *= 0.72
    P.obj("Badge", ball((0.25, 0.37, 0.8), (0.08, 0.03, 0.08), 8, 4), "Trim")
    # the head
    hc = Vector((0, 0.02, 1.48))
    P.obj("Neck", pipe([(0, 0, 1.08), (0, 0.01, 1.24)], [0.13, 0.12], 10), "Metal")
    P.obj("Head", ball(tuple(hc), (0.32, 0.3, 0.34), 18, 9), "Metal", 1)
    P.obj("Visor", ball((0, hc.y + 0.17, hc.z + 0.06), (0.27, 0.14, 0.12), 16, 7), "Glass")
    for s in (1, -1):
        P.obj("Eye", ball((s * 0.11, hc.y + 0.29, hc.z + 0.06), (0.06, 0.03, 0.035), 8, 4), "Lamp")
        P.obj("Brow", box((s * 0.12, hc.y + 0.29, hc.z + 0.16), (0.14, 0.04, 0.035), Matrix.Rotation(math.radians(-s * 15), 3, "Y")), "Accent", 0, False)
        P.obj("EarCap", lathe([(0.0, 0.0), (0.1, 0.0), (0.1, s * 0.06), (0.0, s * 0.07)], 12, "x", (s * 0.31, hc.y, hc.z)), "Accent")
    # the whistle at his mouth, its lanyard
    P.obj("Whistle", pipe([(0.0, hc.y + 0.28, hc.z - 0.14), (0.08, hc.y + 0.45, hc.z - 0.17)], [0.035, 0.03], 8), "Metal")
    P.obj("WhistleBody", ball((0.12, hc.y + 0.47, hc.z - 0.2), (0.09, 0.09, 0.08), 10, 5), "Metal")
    P.obj("Lanyard", pipe(bez((0.12, hc.y + 0.42, hc.z - 0.26), (0.16, 0.35, 1.0), (-0.1, 0.38, 0.95), (-0.22, 0.3, 1.1), 8), [0.015] * 9, 5), "Glow")
    # the propeller cap
    P.obj("Cap", lathe([(0.0, 0.0), (0.3, 0.0), (0.26, 0.12), (0.0, 0.17)], 18, "z", (0, hc.y, hc.z + 0.24)), lambda c, n: "Accent" if c.z < hc.z + 0.3 else "Base")
    P.obj("Peak", hull([(-0.2, hc.y + 0.25, hc.z + 0.26), (0.2, hc.y + 0.25, hc.z + 0.26), (0, hc.y + 0.5, hc.z + 0.25), (0, hc.y + 0.25, hc.z + 0.29)]), "Accent", 0, False)
    P.obj("Mast", pipe([(0, hc.y, hc.z + 0.4), (0, hc.y, hc.z + 0.58)], [0.03, 0.03], 6), "Metal")
    P.prop((0, hc.y, hc.z + 0.6), 0.95, 3, "z", 0.2, blade="Trim", tip="Accent", spinner="Glow", spinner_len=0.1, name="Rotor")
    # the arms: the right holds the red card high, the left thrusts the yellow card forward
    for s in (1, -1):
        sh = Vector((s * 0.52, 0.0, 0.95))
        if s > 0:
            el = Vector((0.82, 0.05, 1.32)); hd = Vector((0.9, 0.12, 1.85))
            card, cslot = box((0.92, 0.16, 2.1), (0.28, 0.03, 0.4), Matrix.Rotation(math.radians(-8), 3, "Y")), "Glow"
        else:
            el = Vector((-0.78, 0.35, 0.82)); hd = Vector((-0.75, 0.85, 0.9))
            card, cslot = box((-0.75, 1.0, 1.08), (0.28, 0.03, 0.4), Matrix.Rotation(math.radians(10), 3, "Y")), "Trim"
        P.obj("Sleeve", ball(tuple(sh), (0.17, 0.17, 0.17), 10, 5), stripes)
        P.obj("Arm", pipe([sh, el, hd], [0.1, 0.085, 0.075], 10), "Metal")
        P.obj("Glove", ball(tuple(hd), (0.11, 0.11, 0.11), 10, 5), "Accent")
        P.obj("Card", card, cslot, 0, False)
    # the legs, kicking
    for s in (1, -1):
        name = "SwayR" if s > 0 else "SwayL"
        hip = Vector((s * 0.22, 0.0, -0.18))
        kn = hip + Vector((0, 0.18 if s > 0 else -0.12, -0.5)); ft = kn + Vector((0, -0.05 if s > 0 else -0.15, -0.5))
        P.part(name, pipe([hip, kn, ft], [0.12, 0.1, 0.09], 10), lambda c, n: "Accent" if c.z > kn.z - 0.05 else "Base", tuple(hip))
        P.part(name, ball(tuple(ft + Vector((0, 0.1, -0.06))), (0.12, 0.24, 0.1), 10, 5), "Accent", tuple(hip))
        P.part(name, box(tuple(ft + Vector((0, 0.1, -0.16))), (0.2, 0.42, 0.04)), "Trim", tuple(hip), 0, False)
    P.part("Muzzle", ball((0.13, hc.y + 0.56, hc.z - 0.2), (0.05, 0.03, 0.04), 8, 4), "Lamp", (0.13, hc.y + 0.56, hc.z - 0.2))
    return P


# ================================================================= 3. the stadium blimp
def S_blimp():
    """The match-day blimp: a royal-blue envelope with gold bands and a football on each flank, red tail fins, a gondola with lit windows
    carrying a glowing scoreboard, searchlights, a victory banner trailing from the tail, and two propellers at the stern."""
    P = Boss("blimp", {"Base": ((0.12, 0.28, 0.80), 0.6), "Belly": WHITE, "Accent": ((0.88, 0.14, 0.12), 0.55), "Trim": GOLD,
                       "Glass": ((0.55, 0.85, 1.0), 0.9), "Dark": INK, "Glow": ((0.25, 1.0, 0.45), 0.5),
                       "Metal": ((0.62, 0.64, 0.70), 0.75), "Lamp": ((1.0, 0.95, 0.65), 0.8)})
    L = [(2.3, 0.0, 0.0), (2.2, 0.38, 0.36), (1.9, 0.72, 0.68), (1.2, 0.95, 0.9), (0.2, 1.0, 0.95), (-0.8, 0.92, 0.88), (-1.6, 0.68, 0.65), (-2.1, 0.38, 0.36), (-2.35, 0.08, 0.08)]
    rings = [(y, a, b, 0, 0.4) for (y, a, b) in L]
    def env(c, n):
        if c.y > 1.9: return "Belly"
        if abs(c.y - 1.45) < 0.12 or abs(c.y + 1.3) < 0.12: return "Trim"
        if n.z < -0.55: return "Belly"
        return "Base"
    P.obj("Envelope", loft(rings, 32, False, False), env, 1)
    P.obj("NoseCap", ball((0, 2.27, 0.4), (0.12, 0.06, 0.12), 10, 5), "Trim")
    for s in (1, -1):   # a football on each flank
        fc = Vector((s * 0.93, 0.3, 0.55))
        b = ball((0, 0, 0), (0.5, 0.5, 0.5), 40, 20)
        for v in b.verts: v.co.x *= 0.18
        xf(b, None, tuple(fc))
        P.obj("Emblem", b, lambda c, n, fc=fc: football(Vector(((c.x - fc.x) / 0.18, c.y - fc.y, c.z - fc.z)), "Belly", "Dark"), 1)
        P.obj("EmblemRing", torus(0.52, 0.04, 0.0, 30, 6), "Trim"); P.parts[-1].data.transform(Matrix.Translation(tuple(fc + Vector((s * 0.02, 0, 0)))) @ Matrix.Rotation(math.radians(90), 4, "Y"))
    # the tail fins: a cross, red with a white edge
    for a in (0, 90, 180, 270):
        fin = sheet([[(0, -1.45, 0.0), (0, -2.45, 0.0), (0, -2.55, 0.85), (0, -2.05, 0.9)]], 0.07)
        xf(fin, Matrix.Rotation(math.radians(90), 3, "Y") @ Matrix.Rotation(math.radians(0), 3, "X"))
        xf(fin, Matrix.Rotation(math.radians(a), 3, "Y"), (0, 0, 0.4))
        P.obj("Fin", fin, lambda c, n: "Belly" if c.y < -2.38 else "Accent", 0, False)
    # the gondola under the envelope
    P.obj("Gondola", loft([(0.85, 0.0, 0.0, 0, -0.62), (0.75, 0.24, 0.16, 0, -0.62), (0.3, 0.32, 0.2, 0, -0.62), (-0.5, 0.3, 0.18, 0, -0.62), (-0.8, 0.12, 0.1, 0, -0.62)], 16, False, True, 1.6),
          lambda c, n: "Lamp" if abs(c.z + 0.6) < 0.05 and abs(n.z) < 0.6 and (c.y * 6) % 1.0 < 0.6 else "Belly", 0)
    for s in (1, -1):   # two engine pods on the gondola's flanks
        ec = Vector((s * 0.62, -0.1, -0.55))
        P.obj("Pylon", box(tuple(ec + Vector((-s * 0.2, 0, 0.0))), (0.3, 0.16, 0.05)), "Metal", 0, False)
        P.obj("Nacelle", loft([(ec.y + 0.3, 0.0, 0.0, ec.x, ec.z), (ec.y + 0.22, 0.13, 0.13, ec.x, ec.z), (ec.y - 0.22, 0.13, 0.13, ec.x, ec.z), (ec.y - 0.3, 0.08, 0.08, ec.x, ec.z)], 12, False, True),
              lambda c, n: "Trim" if c.y > ec.y + 0.18 else "Accent", 1)
    # it crosses the pitch side-on: everything so far turns a quarter round, nose to the left, a flank and its football to the player
    rot = Matrix.Rotation(math.radians(90), 4, "Z")
    for o in P.parts: o.data.transform(rot)
    # the scoreboard hung under the gondola, facing the player: a score of 2 - 1 lit up
    P.obj("Strut", box((0, 0.0, -0.95), (0.12, 0.12, 0.35)), "Metal", 0, False)
    P.obj("Board", box((0, 0.0, -1.35), (1.7, 0.18, 0.62)), lambda c, n: "Trim" if abs(n.z) > 0.5 else "Dark", 0, False)
    P.obj("Screen", box((0, 0.08, -1.35), (1.52, 0.04, 0.48)), "Glow", 0, False)
    def seg(x, z, w, h): P.obj("Digit", box((x, 0.11, z), (w, 0.03, h)), "Dark", 0, False)
    # "2": top, upper right, middle, lower left, bottom
    seg(-0.5, -1.17, 0.22, 0.05); seg(-0.4, -1.26, 0.05, 0.16); seg(-0.5, -1.35, 0.22, 0.05); seg(-0.6, -1.44, 0.05, 0.16); seg(-0.5, -1.53, 0.22, 0.05)
    seg(0.0, -1.35, 0.14, 0.05)
    seg(0.5, -1.35, 0.05, 0.4); seg(0.45, -1.2, 0.1, 0.05)   # "1"
    for s in (1, -1):
        P.obj("Searchlight", lathe([(0.0, 0.0), (0.12, 0.0), (0.14, 0.2), (0.0, 0.2)], 12, "y", (s * 0.55, 0.2, -0.85)), "Metal")
        P.obj("Lens", ball((s * 0.55, 0.42, -0.85), (0.12, 0.02, 0.12), 10, 5), "Lamp")
        P.obj("Rope", pipe([(s * 0.75, 0.0, -1.04), (s * 0.35, 0.0, -0.62)], [0.015, 0.015], 4), "Dark")
    # the propeller at the stern, turning about the wing axis
    P.obj("Shaft", pipe([(2.3, 0, 0.4), (2.62, 0, 0.4)], [0.06, 0.05], 8), "Metal")
    P.prop((2.68, 0, 0.4), 0.6, 4, "x", 0.2, blade="Accent", tip="Belly", spinner="Trim", spinner_len=0.15, name="TailRotor")
    P.part("Muzzle", ball((0, 0.14, -1.35), (0.07, 0.03, 0.07), 8, 4), "Lamp", (0, 0.14, -1.35))
    return P


# ================================================================= 4. the goalkeeper giant
def S_keeper():
    """A giant goalkeeper robot carrying his goal on his back like wings - white posts, a crossbar and a net - in a neon jersey with the
    number 1, huge orange gloves spread to save, waving, and jets blazing from his boots."""
    P = Boss("keeper", {"Base": ((0.55, 0.95, 0.12), 0.5), "Belly": WHITE, "Accent": ((1.0, 0.45, 0.08), 0.55), "Trim": ((0.08, 0.10, 0.12), 0.5),
                        "Glass": ((0.10, 0.12, 0.18), 0.95), "Dark": INK, "Glow": ((0.35, 0.85, 1.0), 0.5),
                        "Metal": ((0.62, 0.64, 0.70), 0.8), "Lamp": ((1.0, 0.95, 0.5), 0.8)})
    # the body: a broad chest, a belt, shorts
    chest = lathe([(0.0, 0.0), (0.5, 0.02), (0.62, 0.35), (0.75, 0.8), (0.72, 1.05), (0.4, 1.2), (0.0, 1.22)], 28, "z")
    for v in chest.verts: v.co.y *= 0.62
    P.obj("Jersey", chest, lambda c, n: "Trim" if abs(c.z - 0.62) < 0.05 and n.y < 0.3 else "Base", 1)
    P.obj("Shorts", lathe([(0.0, 0.05), (0.5, 0.05), (0.56, -0.3), (0.0, -0.32)], 24, "z"), "Trim")
    for v in P.parts[-1].data.vertices: v.co.y *= 0.65
    # the number 1 on the chest
    P.obj("Number", box((0.02, 0.47, 0.7), (0.1, 0.03, 0.42)), "Trim", 0, False)
    P.obj("Number", box((-0.06, 0.465, 0.86), (0.12, 0.03, 0.08), Matrix.Rotation(math.radians(-35), 3, "Y")), "Trim", 0, False)
    P.obj("Number", box((0.02, 0.465, 0.5), (0.24, 0.03, 0.06)), "Trim", 0, False)
    for s in (1, -1):
        P.obj("Shoulder", ball((s * 0.7, 0.0, 1.0), (0.3, 0.28, 0.24), 12, 6), "Base", 1)
        P.obj("ShoulderBand", torus(0.24, 0.03, 0.0, 16, 4), "Belly"); P.parts[-1].data.transform(Matrix.Translation((s * 0.78, 0, 0.98)) @ Matrix.Rotation(math.radians(90), 4, "Y"))
    # the head: a helmet-like dome, a visor, a headband
    hc = Vector((0, 0.05, 1.5))
    P.obj("Head", ball(tuple(hc), (0.34, 0.32, 0.32), 18, 9), "Metal", 1)
    P.obj("Visor", ball((0, hc.y + 0.18, hc.z + 0.02), (0.29, 0.15, 0.12), 16, 7), "Glass")
    P.obj("Band", torus(0.33, 0.04, 0.0, 22, 5), "Accent"); P.parts[-1].data.transform(Matrix.Translation((0, hc.y, hc.z + 0.16)))
    for s in (1, -1):
        P.obj("Eye", ball((s * 0.12, hc.y + 0.31, hc.z + 0.02), (0.07, 0.03, 0.04), 8, 4), "Lamp")
        P.obj("Brow", box((s * 0.12, hc.y + 0.31, hc.z + 0.11), (0.15, 0.04, 0.035), Matrix.Rotation(math.radians(-s * 14), 3, "Y")), "Trim", 0, False)
    P.obj("Mouth", box((0, hc.y + 0.3, hc.z - 0.15), (0.16, 0.03, 0.04)), "Trim", 0, False)
    # the arms spread wide to save, waving, the great gloves
    for s in (1, -1):
        name = "FlapR" if s > 0 else "FlapL"
        sh = Vector((s * 0.8, 0.0, 1.0)); el = Vector((s * 1.35, 0.15, 1.2)); wr = Vector((s * 1.75, 0.3, 1.55))
        P.part(name, pipe([sh, el, wr], [0.15, 0.13, 0.12], 10), "Base", tuple(sh))
        P.part(name, ball(tuple(el), (0.15, 0.15, 0.15), 10, 5), "Belly", tuple(sh))
        P.part(name, pipe([wr - (wr - el) * 0.15, wr + (wr - el).normalized() * 0.08], [0.16, 0.16], 10), "Belly", tuple(sh))
        gc = wr + Vector((s * 0.12, 0.08, 0.28))
        palm = ball((0, 0, 0), (0.18, 0.32, 0.36), 12, 6); xf(palm, Matrix.Rotation(math.radians(-s * 20), 3, "Y"), tuple(gc))
        P.part(name, palm, lambda c, n: "Belly" if n.y > 0.6 else "Accent", tuple(sh), 1)
        for k in range(4):   # four fingers fanned up
            a = math.radians(-s * (30 - k * 17))
            base = gc + Vector((math.sin(a) * 0.18, 0.04, math.cos(a) * 0.26))
            tip = gc + Vector((math.sin(a) * 0.42, 0.06, math.cos(a) * 0.62))
            P.part(name, pipe([base, tip], [0.085, 0.07], 8), "Accent", tuple(sh))
            P.part(name, ball(tuple(tip), (0.07, 0.07, 0.07), 8, 4), "Accent", tuple(sh))
        th = gc + Vector((-s * 0.2, 0.12, -0.1))
        P.part(name, pipe([gc + Vector((-s * 0.08, 0.08, -0.12)), th + Vector((-s * 0.15, 0.08, 0.05))], [0.09, 0.07], 8), "Accent", tuple(sh))
        P.part(name, box(tuple(gc + Vector((0, -0.06, -0.33))), (0.32, 0.22, 0.12)), "Trim", tuple(sh), 0, False)
    # the legs, crouched, boots blazing
    for s in (1, -1):
        hip = Vector((s * 0.28, 0.0, -0.25)); kn = Vector((s * 0.42, 0.28, -0.7)); ft = Vector((s * 0.4, 0.05, -1.15))
        P.obj("Leg", pipe([hip, kn, ft], [0.17, 0.14, 0.12], 10), lambda c, n: "Base" if c.z < -0.75 else "Metal")
        P.obj("Knee", ball(tuple(kn), (0.15, 0.15, 0.15), 10, 5), "Belly")
        P.obj("Boot", ball(tuple(ft + Vector((0, 0.1, -0.06))), (0.15, 0.28, 0.13), 12, 6), lambda c, n: "Accent" if n.z > 0.5 else "Dark")
        for k in range(3):
            P.obj("Stud", cone((s * 0.4 + (k - 1) * 0.06, 0.1 + (k - 1) * 0.12, -1.3), (s * 0.4 + (k - 1) * 0.06, 0.1 + (k - 1) * 0.12, -1.36), 0.03, 6), "Metal", 0, False)
        flame(P, (s * 0.4, 0.05, -1.32), (s * 0.4, -0.2, -1.85), 0.12)
    # his goal on his back: posts, crossbar, the net
    gy = -0.55; W = 1.85; Ht = 2.15; z0 = -0.45; D = 0.75
    for s in (1, -1):
        P.obj("Post", pipe([(s * W, gy, z0), (s * W, gy, z0 + Ht)], [0.07, 0.07], 10), "Belly")
        P.obj("Back", pipe([(s * W, gy, z0 + Ht), (s * W * 0.95, gy - D, z0 + Ht * 0.75), (s * W * 0.95, gy - D, z0)], [0.035, 0.035, 0.035], 6), "Metal")
        P.obj("Strap", box((s * 0.45, -0.3, 0.75), (0.14, 0.5, 0.12), Matrix.Rotation(math.radians(s * 30), 3, "Y")), "Trim", 0, False)
    P.obj("Crossbar", pipe([(-W, gy, z0 + Ht), (W, gy, z0 + Ht)], [0.07, 0.07], 10), "Belly")
    for k in range(13):   # net: verticals on the back
        x = -W * 0.95 + k * (W * 1.9 / 12)
        P.obj("Net", pipe([(x, gy - D, z0 + Ht * 0.75), (x, gy - D, z0)], [0.012, 0.012], 4), "Belly", 0, False)
        P.obj("Net", pipe([(x * 1.05, gy, z0 + Ht), (x, gy - D, z0 + Ht * 0.75)], [0.012, 0.012], 4), "Belly", 0, False)
    for k in range(8):   # net: horizontals on the back, and across the side panels
        f = k / 7; z = z0 + f * Ht * 0.75
        P.obj("Net", pipe([(-W * 0.95, gy - D, z), (W * 0.95, gy - D, z)], [0.012, 0.012], 4), "Belly", 0, False)
        for s in (1, -1):
            P.obj("Net", pipe([(s * W, gy, z0 + f * Ht), (s * W * 0.95, gy - D, z)], [0.012, 0.012], 4), "Belly", 0, False)
    for k in range(4):
        t = (k + 1) / 5
        P.obj("Net", pipe([(-W, gy - D * t, z0 + Ht - Ht * 0.25 * t), (W, gy - D * t, z0 + Ht - Ht * 0.25 * t)], [0.012, 0.012], 4), "Belly", 0, False)
    P.part("Muzzle", ball((0, 0.5, 0.95), (0.08, 0.03, 0.08), 8, 4), "Lamp", (0, 0.5, 0.95))
    return P


# ================================================================= 5. the golden trophy titan
def S_trophy():
    """The last boss: the cup itself come alive - a towering golden trophy on a malachite-banded plinth, two golden arms spiralling up its
    sides to hold a great golden football overhead, burning eyes in the bowl, laurel wings beating at its shoulders, a halo of stars turning
    face-on behind it and a ring of confetti turning round it."""
    P = Boss("trophy", {"Base": GOLD, "Belly": ((1.0, 0.92, 0.55), 0.8), "Accent": ((0.10, 0.55, 0.30), 0.6), "Trim": ((0.80, 0.52, 0.10), 0.7),
                        "Glass": ((0.95, 0.30, 0.55), 0.6), "Dark": ((0.08, 0.05, 0.04), 0.5), "Glow": ((0.30, 0.75, 1.0), 0.5),
                        "Metal": ((0.85, 0.86, 0.90), 0.8), "Lamp": ((1.0, 0.55, 0.12), 0.8)})
    # the plinth and the cup
    P.obj("Plinth", lathe([(0.0, -1.55), (0.95, -1.55), (0.95, -1.35), (0.85, -1.3), (0.85, -1.05), (0.7, -1.0), (0.0, -1.0)], 32, "z"),
          lambda c, n: "Accent" if -1.33 < c.z < -1.15 or (-1.12 < c.z < -1.06) else ("Dark" if n.z < -0.5 else "Base"))
    prof = [(0.0, -1.0), (0.62, -1.0), (0.5, -0.8), (0.3, -0.55), (0.24, -0.2), (0.3, 0.1), (0.48, 0.35), (0.7, 0.62), (0.82, 0.9), (0.8, 1.05), (0.0, 1.05)]
    P.obj("Cup", lathe(prof, 32, "z"), lambda c, n: "Accent" if abs(c.z + 0.75) < 0.05 else ("Trim" if abs(c.z - 0.98) < 0.06 else "Base"), 1)
    P.obj("Rim", torus(0.82, 0.07, 1.02, 36, 8), "Belly")
    P.obj("Band", torus(0.27, 0.05, -0.2, 20, 6), "Accent")
    # the face in the bowl
    for s in (1, -1):
        eye = ball((0, 0, 0), (0.15, 0.06, 0.1), 12, 6); xf(eye, Matrix.Rotation(math.radians(s * 14), 3, "Y"), (s * 0.24, 0.72, 0.62))
        P.obj("Eye", eye, "Lamp")
        P.obj("Socket", ball((s * 0.24, 0.68, 0.62), (0.2, 0.06, 0.14), 12, 6), "Dark")
        P.obj("Brow", box((s * 0.26, 0.79, 0.8), (0.3, 0.06, 0.07), Matrix.Rotation(math.radians(-s * 16), 3, "Y")), "Trim", 0, False)
    P.obj("Mouth", ball((0, 0.56, 0.22), (0.18, 0.05, 0.06), 12, 5), "Dark")
    # two arms spiralling up its sides holding the golden ball overhead
    bc = Vector((0, 0.05, 1.85)); br = 0.62
    for s in (1, -1):
        arm = bez((s * 0.3, 0.05, -0.35), (s * 1.15, 0.35, 0.2), (s * 1.15, -0.25, 1.15), (s * 0.55, 0.05, 1.6), 14)
        P.obj("Arm", pipe(arm, [0.09 + 0.06 * (k / 14) for k in range(15)], 10), "Base")
        P.obj("Hand", ball((s * 0.5, 0.05, 1.62), (0.2, 0.2, 0.16), 10, 5), "Base")
    P.obj("Ball", ball_mesh(tuple(bc), br, 48, 24), lambda c, n: football(c - bc, "Base", "Trim", "Belly"), 1)
    P.obj("Crown", lathe([(0.0, 0.0), (0.1, 0.0), (0.0, 0.25)], 10, "z", (0, bc.y, bc.z + br - 0.04)), "Lamp")
    # laurel wings beating at its shoulders
    for s in (1, -1):
        name = "FlapR" if s > 0 else "FlapL"
        hub = Vector((s * 0.7, -0.15, 0.85))
        stem = bez(hub, hub + Vector((s * 0.5, -0.05, 0.25)), hub + Vector((s * 1.1, -0.1, 0.45)), hub + Vector((s * 1.75, -0.15, 0.8)), 12)
        P.part(name, pipe(stem, [0.05 - 0.035 * (k / 12) for k in range(13)], 6), "Trim", tuple(hub))
        for k in range(2, 13):
            p = stem[k]; t = (stem[min(k + 1, 12)] - stem[k - 1]).normalized()
            for side in (1, -1):
                nrm = Vector((0, 0, 1)) * side + Vector((0, -0.3, 0))
                tip = p + t * 0.22 + nrm.normalized() * (0.28 - 0.012 * k)
                leaf = hull([tuple(p), tuple(tip), tuple(p + t * 0.15 + nrm.normalized() * 0.1 + Vector((0, 0.05, 0))), tuple(p + t * 0.15 + nrm.normalized() * 0.1 - Vector((0, 0.05, 0)))])
                P.part(name, leaf, "Base" if (k + side) % 3 else "Belly", tuple(hub), 0, False)
    # the halo of stars behind, turning face-on
    hcen = Vector((0, -0.75, 0.9))
    P.part("RollHalo", xf(torus(1.75, 0.04, 0.0, 48, 6), None, tuple(hcen)), "Belly", tuple(hcen))
    halo = P.spin[-1]; halo.data.transform(Matrix.Rotation(math.radians(90), 4, "X"))
    for k in range(10):
        a = 2 * math.pi * k / 10
        c = Vector((math.cos(a) * 1.75, 0, math.sin(a) * 1.75))
        pts = []
        for j in range(10):
            r = 0.22 if j % 2 == 0 else 0.09
            aa = math.pi / 2 + j * math.pi / 5
            pts.append((c.x + math.cos(aa) * r, c.z + math.sin(aa) * r))
        bm = bmesh.new()
        cen_f = bm.verts.new((c.x, 0.04, c.z)); cen_b = bm.verts.new((c.x, -0.04, c.z))
        ring = [bm.verts.new((x, 0, z)) for (x, z) in pts]
        for j in range(10):
            bm.faces.new((cen_f, ring[j], ring[(j + 1) % 10])); bm.faces.new((cen_b, ring[(j + 1) % 10], ring[j]))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        xf(bm, None, tuple(hcen))
        P.part("RollHalo", bm, "Lamp" if k % 2 == 0 else "Belly", tuple(hcen), 0, False)
    # confetti turning round it
    rng = random.Random(5); cols = ["Accent", "Glass", "Glow", "Belly", "Metal"]
    for k in range(26):
        a = 2 * math.pi * k / 26 + rng.uniform(-0.08, 0.08)
        c = Vector((math.cos(a) * 2.1, math.sin(a) * 1.9, -0.2 + rng.uniform(-0.5, 1.6)))
        m = Matrix.Rotation(rng.uniform(0, 3), 3, "X") @ Matrix.Rotation(rng.uniform(0, 3), 3, "Z")
        piece = box((0, 0, 0), (0.16, 0.09, 0.015), m); xf(piece, None, tuple(c))
        P.part("SpinConfetti", piece, cols[k % len(cols)], (0, 0, 0), 0, False)
    P.part("Muzzle", ball((0, 0.6, 0.22), (0.08, 0.03, 0.05), 8, 4), "Lamp", (0, 0.6, 0.22))
    return P


BOSSES = [("ballbot", S_ballbot), ("referee", S_referee), ("blimp", S_blimp), ("keeper", S_keeper), ("trophy", S_trophy)]

if __name__ == "__main__":
    os.makedirs(AB.OUT, exist_ok=True)
    for bid, fn in BOSSES:
        if ONLY and bid not in ONLY: continue
        fn().finish()
    print("DONE")
