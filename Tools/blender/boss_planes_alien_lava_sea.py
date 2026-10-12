# Sky Squad, boss-inspired enemy planes for the alien, inferno (lava) and sea worlds (2026-10-12: "for every level two planes inspired by
# its bosses - pictures first, before putting them in the game"). Same conventions as enemy_planes.py: +Y nose, +Z up, +X right wing;
# "Body" plus "Prop<n>" spinning about the nose; material slots <id>_<Slot>.
# Run: blender -b -P Tools/blender/boss_planes_alien_lava_sea.py -- <out dir> [export] [ids,comma,separated]
import bpy, bmesh, math, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mathutils import Vector, Matrix
import enemy_planes as EP
from enemy_planes import Plane, loft, sweep, lathe, box, hull, tube, mirror_x, airfoil
from alien_bosses import xf, ball, pipe, cone, bez, torus, sheet, grow

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ONLY = argv[2].split(",") if len(argv) > 2 and argv[2] else None


def speckle(c, k=1.0):
    v = math.sin(c.x * 12.9898 * k + c.y * 78.233 * k + c.z * 37.719 * k) * 43758.5453
    return v - math.floor(v)

def pilot(P, y, z, helmet="Trim", visor="Glass", rim="Metal", horns=None):
    """an open cockpit: a rim, the pilot's helmeted head and goggles looking ahead."""
    P.obj("CockpitRim", xf(torus(0.24, 0.045, 0.0, 16, 5), None, (0, y, z)), rim)
    P.obj("Pilot", ball((0, y, z + 0.14), (0.16, 0.16, 0.17), 10, 5), helmet, 1)
    P.obj("Goggles", ball((0, y + 0.13, z + 0.16), (0.13, 0.05, 0.055), 8, 4), visor)
    if horns:
        for s in (1, -1):
            P.obj("PilotHorn", pipe(bez((s * 0.1, y, z + 0.26), (s * 0.18, y, z + 0.34), (s * 0.22, y - 0.03, z + 0.42), (s * 0.2, y - 0.06, z + 0.5), 3), [0.04, 0.03, 0.015, 0.0], 5), horns)

def jet(P, x, y0, y1, z, r, shell="Metal", flame="Glow"):
    P.obj("Engine", loft([(y0, r * 0.8, r * 0.8, x, z), (y0 - 0.15, r, r, x, z), (y1 + 0.1, r * 0.95, r * 0.95, x, z), (y1, r * 0.8, r * 0.8, x, z)], 10), shell, 1)
    P.obj("Nozzle", tube(y1, y1 - 0.06, r * 0.65, r * 0.2, x, z, 10), flame)

def bat_wing(P, s, sh, wr, tips, root, bone, membrane, claw):
    """a bat / dragon wing: a bone arm and fingers with a scalloped membrane between them (a still part of the Body)."""
    P.obj("WingArm", pipe([sh, wr], [0.08, 0.05], 6), bone)
    for t in tips:
        P.obj("Finger", pipe([wr, t], [0.04, 0.012], 5), bone)
        P.obj("FingerTip", cone(t, t + (t - wr).normalized() * 0.15, 0.03, 4), claw, 0, False)
    polys = [[sh, wr, tips[0]]]
    chain = tips + [root]
    for a, b in zip(chain, chain[1:]):
        m = (a + b) * 0.5; m = m + (wr - m) * 0.22
        polys.append([wr, a, m]); polys.append([wr, m, b])
    polys.append([wr, root, sh])
    P.obj("Membrane", sheet([[tuple(p) for p in poly] for poly in polys], 0.04), membrane, 0, False)


# ================================================================= ALIEN 1: the manta raider (the nebula manta)
def A_manta():
    """A manta-ray raider: a broad indigo flying-wing body striped with glowing nebula bands, two horn-fins curling forward past three pink
    eye-lamps, crystal fins down the spine, a whip tail with a crystal, twin plasma jets, and an alien pilot in a gold helmet."""
    P = Plane("alien", {"Base": ((0.10, 0.20, 0.50), 0.6), "Belly": ((0.86, 0.90, 1.0), 0.5), "Accent": ((0.55, 0.22, 0.95), 0.6),
                        "Trim": ((0.95, 0.80, 0.40), 0.7), "Glass": ((0.55, 0.95, 1.0), 0.95), "Dark": ((0.03, 0.04, 0.10), 0.5),
                        "Glow": ((0.30, 1.0, 0.95), 0.5), "Metal": ((0.40, 0.95, 0.40), 0.5), "Lamp": ((1.0, 0.35, 0.85), 0.8)})
    P.obj("Body", loft([(2.5, 0.12, 0.06, 0, 0), (2.2, 0.5, 0.18, 0, 0), (1.3, 0.75, 0.28, 0, 0.02), (0.0, 0.7, 0.28, 0, 0.03),
                        (-1.2, 0.45, 0.2, 0, 0.02), (-2.0, 0.14, 0.08, 0, 0)], 16),
          lambda c, n: "Belly" if n.z < -0.35 else ("Accent" if abs(c.x) > 0.5 else "Base"), 1)
    def band(c, n):
        if n.z < -0.3: return "Belly"
        x = abs(c.x)
        if (x * 2.4) % 1.0 < 0.2 and x > 0.9: return "Glow"
        if c.y < -0.55 - x * 0.15: return "Accent"
        return "Base"
    P.wing([(0.6, 1.5, -1.2, 0.16, 0.0), (1.5, 0.95, -0.95, 0.11, 0.04), (2.3, 0.2, -0.7, 0.07, 0.18), (2.85, -0.35, -0.8, 0.04, 0.42)], band)
    P.obj("Mouth", ball((0, 2.45, -0.02), (0.32, 0.08, 0.05), 10, 4), "Glow")
    for x, z in ((0.22, 0.18), (-0.22, 0.18), (0.0, 0.26)):
        P.obj("Eye", ball((x, 2.2 if x else 2.1, z), (0.09, 0.06, 0.06), 8, 4), "Lamp")
    for s in (1, -1):
        P.obj("HornFin", pipe(bez((s * 0.42, 2.2, 0.0), (s * 0.68, 2.6, 0.02), (s * 0.6, 2.95, 0.12), (s * 0.34, 3.0, 0.22), 6),
                              [0.11, 0.1, 0.08, 0.06, 0.045, 0.03, 0.0], 7), lambda c, n: "Glow" if c.y > 2.85 else "Accent")
        jet(P, s * 0.42, -0.6, -1.75, -0.22, 0.17)
        for k in range(2):
            P.obj("WingLamp", ball((s * (1.7 + k * 0.5), -0.2 - k * 0.15, 0.13 + k * 0.08), (0.07, 0.07, 0.04), 6, 3), "Lamp")
    for i in range(4):
        y = 0.0 - i * 0.38
        P.obj("Crystal", cone((0, y, 0.28 - i * 0.02), (0, y - 0.22, 0.62 - i * 0.07), 0.07, 5), "Glass", 0, False)
    tail = bez((0, -1.95, 0.0), (0, -2.6, 0.0), (0.2, -3.0, 0.2), (-0.05, -3.3, 0.45), 7)
    P.obj("Tail", pipe(tail, [0.08 - 0.009 * i for i in range(8)], 6), "Base")
    t = tail[-1]
    P.obj("TailCrystal", hull([t + Vector((0, 0.05, -0.05)), t + Vector((-0.1, -0.12, 0.16)), t + Vector((0.1, -0.12, 0.16)), t + Vector((0, -0.05, 0.34)), t + Vector((0, -0.25, 0.12))]), "Glass", 0, False)
    pilot(P, 0.95, 0.3, helmet="Trim", visor="Glass", rim="Trim")
    for s in (1, -1):
        P.obj("Antenna", pipe([(s * 0.06, 0.95, 0.58), (s * 0.14, 0.9, 0.72)], [0.015, 0.012], 4), "Metal")
        P.obj("AntennaTip", ball((s * 0.14, 0.9, 0.74), (0.035, 0.035, 0.035), 6, 3), "Glow")
    return P


# ================================================================= ALIEN 2: the void wyvern (the void dragon)
def A_dragon():
    """A dragon fighter: an indigo serpent fuselage with a horned dragon head for a nose (the open jaw glows - his cannon), bat wings of
    violet membrane on bone fingers tipped in cyan, crystal spines, a tail ending in a crystal blade, twin cyan jets and a pilot on his back."""
    P = Plane("alien2", {"Base": ((0.13, 0.10, 0.36), 0.55), "Belly": ((0.95, 0.78, 0.40), 0.7), "Accent": ((0.45, 0.16, 0.78), 0.5),
                         "Trim": ((0.92, 0.88, 0.78), 0.5), "Glass": ((0.40, 0.95, 1.0), 0.95), "Dark": ((0.03, 0.02, 0.06), 0.4),
                         "Glow": ((0.25, 0.95, 1.0), 0.5), "Metal": ((0.45, 0.45, 0.55), 0.6), "Lamp": ((1.0, 0.35, 0.90), 0.8)})
    belly = lambda c, n: ("Dark" if (c.y * 4.0) % 1.0 < 0.12 else "Belly") if n.z < -0.35 and abs(n.x) < 0.7 else ("Accent" if n.z > 0.75 else "Base")
    P.obj("Fuselage", loft([(1.7, 0.22, 0.22, 0, 0.12), (1.0, 0.34, 0.34, 0, 0.05), (0.0, 0.38, 0.36, 0, 0.0), (-1.1, 0.3, 0.28, 0, 0.03),
                            (-1.9, 0.17, 0.17, 0, 0.1), (-2.3, 0.08, 0.08, 0, 0.16)], 14), belly, 1)
    P.obj("Skull", loft([(1.55, 0.26, 0.24, 0, 0.2), (1.9, 0.26, 0.2, 0, 0.25), (2.3, 0.18, 0.12, 0, 0.2), (2.65, 0.08, 0.06, 0, 0.16)], 12),
          lambda c, n: "Accent" if n.z > 0.55 else "Base", 1)
    P.obj("Jaw", loft([(1.6, 0.2, 0.07, 0, -0.04), (2.1, 0.15, 0.05, 0, -0.1), (2.5, 0.07, 0.03, 0, -0.1)], 10), lambda c, n: "Belly" if n.z < -0.2 else "Base", 1)
    P.obj("Throat", ball((0, 2.05, 0.06), (0.12, 0.3, 0.06), 10, 4), "Glow")
    for s in (1, -1):
        P.obj("Eye", ball((s * 0.17, 1.95, 0.33), (0.06, 0.09, 0.045), 8, 4), "Glow")
        P.obj("Brow", cone((s * 0.12, 1.85, 0.38), (s * 0.26, 2.05, 0.38), 0.05, 5), "Trim")
        for k, L in enumerate((1.0, 0.75)):
            r0 = Vector((s * (0.12 + k * 0.1), 1.65, 0.38 - k * 0.1))
            P.obj("Horn", pipe(bez(r0, r0 + Vector((s * 0.1, -0.25 * L, 0.2 * L)), r0 + Vector((s * 0.22 * L, -0.5 * L, 0.3 * L)), r0 + Vector((s * 0.3 * L, -0.75 * L, 0.42 * L)), 4),
                               [0.07, 0.055, 0.04, 0.02, 0.0], 6), "Trim")
        for k in range(3):
            y = 2.1 + k * 0.15
            P.obj("Tooth", cone((s * (0.15 - k * 0.035), y, 0.1), (s * (0.14 - k * 0.035), y + 0.02, -0.02), 0.025, 4), "Trim", 0, False)
        bat_wing(P, s, Vector((s * 0.3, 0.45, 0.12)), Vector((s * 1.3, 0.3, 0.55)),
                 [Vector((s * 2.3, 0.05, 0.75)), Vector((s * 2.75, -0.45, 0.45)), Vector((s * 2.5, -1.0, 0.15)), Vector((s * 1.7, -1.25, 0.05))],
                 Vector((s * 0.32, -0.75, 0.05)), "Base", "Accent", "Glow")
        jet(P, s * 0.3, -0.9, -1.9, -0.18, 0.13)
    for i in range(5):
        y = 0.6 - i * 0.5; h = 0.32 - i * 0.04
        P.obj("Crystal", cone((0, y, 0.32 - i * 0.03), (0, y - 0.2, 0.32 + h), 0.07, 5), "Glass", 0, False)
    tip = Vector((0, -2.35, 0.17))
    P.obj("TailBlade", hull([tip + Vector((0, 0.1, 0)), tip + Vector((-0.3, -0.3, 0.2)), tip + Vector((0.3, -0.3, 0.2)), tip + Vector((0, -0.55, 0.1)), tip + Vector((0, -0.15, 0.38))]), "Glass", 0, False)
    pilot(P, 1.05, 0.36, helmet="Accent", visor="Glow", rim="Trim")
    return P


# ================================================================= LAVA 1: the salamander racer (the magma salamander king)
def L_salamander():
    """A salamander racer: a black lava-rock body cracked with glowing magma, a broad salamander head for a nose with big golden eyes, a
    grin and a little gold crown, glowing gill frills, short stubby wings ending in toes, a ridge of spines, a long curling tail with a
    flame at its tip, and twin fire jets."""
    P = Plane("lava", {"Base": ((0.13, 0.11, 0.11), 0.35), "Belly": ((0.55, 0.22, 0.08), 0.35), "Accent": ((0.75, 0.12, 0.04), 0.45),
                       "Trim": ((1.0, 0.78, 0.26), 0.85), "Glass": ((1.0, 0.92, 0.6), 0.6), "Dark": ((0.04, 0.03, 0.03), 0.3),
                       "Glow": ((1.0, 0.40, 0.04), 0.5), "Metal": ((0.32, 0.30, 0.29), 0.5), "Lamp": ((1.0, 0.85, 0.20), 0.8)})
    magma = lambda c, n: "Belly" if n.z < -0.4 else ("Glow" if (c.y * 2.6 + math.sin(c.x * 7.0) * 0.35) % 1.0 < 0.09 else "Base")   # glowing magma cracks round the body
    P.obj("Fuselage", loft([(1.7, 0.4, 0.28, 0, 0.0), (0.9, 0.46, 0.34, 0, 0.02), (-0.2, 0.42, 0.32, 0, 0.03), (-1.2, 0.3, 0.24, 0, 0.04), (-1.8, 0.16, 0.14, 0, 0.06)], 14), magma, 1)
    P.obj("Head", ball((0, 2.1, 0.02), (0.58, 0.55, 0.28), 14, 7), magma, 1)
    P.obj("Mouth", pipe(bez((-0.38, 2.45, -0.08), (-0.15, 2.66, -0.12), (0.15, 2.66, -0.12), (0.38, 2.45, -0.08), 6), [0.025] * 7, 5), "Glow")
    for s in (1, -1):
        P.obj("Eye", ball((s * 0.27, 2.25, 0.27), (0.13, 0.12, 0.12), 10, 5), "Lamp")
        P.obj("Pupil", ball((s * 0.27, 2.36, 0.3), (0.035, 0.03, 0.08), 6, 3), "Dark")
        P.obj("Lid", ball((s * 0.27, 2.22, 0.36), (0.15, 0.13, 0.06), 8, 4), "Base")
        for k in range(3):   # the glowing gill frills
            b = Vector((s * 0.5, 1.85 - k * 0.12, 0.1 + k * 0.05))
            P.obj("Gill", cone(b, b + Vector((s * 0.35, -0.28, 0.12 + k * 0.08)), 0.07, 5), "Glow" if k != 1 else "Accent", 0, False)
        jet(P, s * 0.32, -0.6, -1.65, -0.18, 0.15, "Metal", "Glow")
        for k in range(3):   # toes at the wing tips
            P.obj("Toe", ball((s * 2.55, 0.25 - k * 0.22, 0.05), (0.13, 0.1, 0.07), 8, 4), "Base")
    for k in range(5):
        a = math.radians(-50 + k * 25)
        b = Vector((math.sin(a) * 0.2, 2.0 + math.cos(a) * 0.1, 0.27))
        P.obj("Crown", cone(b, b + Vector((0, 0, 0.18 if k % 2 == 0 else 0.12)), 0.05, 4), "Trim", 0, False)
    P.obj("CrownBand", xf(torus(0.22, 0.03, 0.0, 14, 4), None, (0, 2.0, 0.28)), "Trim")
    P.wing([(0.4, 0.75, -0.45, 0.16, 0.0), (1.6, 0.55, -0.35, 0.11, 0.02), (2.45, 0.42, -0.2, 0.07, 0.05)],
           lambda c, n: "Glow" if n.y > 0.55 else ("Belly" if n.z < -0.3 else ("Glow" if (abs(c.x) * 2.2 + c.y * 0.6) % 1.0 < 0.08 else "Base")))
    for i in range(5):
        y = 0.9 - i * 0.55
        P.obj("Spine", cone((0, y, 0.33), (0, y - 0.18, 0.62 - i * 0.04), 0.08, 4), "Accent", 0, False)
    tail = bez((0, -1.75, 0.06), (0, -2.4, 0.0), (0.45, -2.75, 0.15), (0.2, -3.1, 0.45), 8)
    P.obj("Tail", pipe(tail, [0.14 - 0.015 * i for i in range(9)], 7), magma)
    t = tail[-1]
    P.obj("TailFlame", cone(t, t + Vector((0.0, -0.1, 0.45)), 0.12, 6), "Glow", 0, False)
    P.obj("TailFlame2", cone(t + Vector((0.05, 0, 0)), t + Vector((0.12, -0.05, 0.3)), 0.07, 5), "Lamp", 0, False)
    pilot(P, 1.15, 0.32, helmet="Accent", visor="Lamp", rim="Trim")
    return P


# ================================================================= LAVA 2: the demon bomber (the demon lord)
def L_demon():
    """A demon bomber: a crimson body with a demon face on the nose - blazing eyes, black brows, a fanged grin, gold horns - great bat wings
    of red membrane on black bones with gold claws, two engines whose propellers spin round burning spinners, a devil's tail ending in a
    gold arrowhead, and a horned pilot."""
    P = Plane("lava2", {"Base": ((0.62, 0.08, 0.07), 0.45), "Belly": ((0.12, 0.08, 0.08), 0.35), "Accent": ((0.08, 0.06, 0.07), 0.4),
                        "Trim": ((1.0, 0.78, 0.26), 0.85), "Glass": ((0.95, 0.93, 0.85), 0.5), "Dark": ((0.03, 0.02, 0.02), 0.3),
                        "Glow": ((1.0, 0.45, 0.05), 0.5), "Metal": ((0.32, 0.30, 0.29), 0.5), "Lamp": ((1.0, 0.85, 0.2), 0.8)})
    P.obj("Fuselage", loft([(2.4, 0.2, 0.18, 0, 0.0), (2.1, 0.42, 0.38, 0, 0.0), (1.2, 0.5, 0.46, 0, 0.02), (0.0, 0.48, 0.42, 0, 0.04),
                            (-1.2, 0.34, 0.3, 0, 0.08), (-2.0, 0.14, 0.14, 0, 0.14)], 14),
          lambda c, n: "Belly" if n.z < -0.45 else ("Accent" if n.z > 0.8 and c.y < 1.6 else "Base"), 1)
    P.obj("Mouth", ball((0, 2.25, -0.12), (0.26, 0.1, 0.08), 10, 4), "Dark")
    P.obj("MouthGlow", ball((0, 2.28, -0.14), (0.18, 0.08, 0.04), 8, 4), "Glow")
    for s in (1, -1):
        P.obj("Socket", ball((s * 0.19, 2.08, 0.19), (0.15, 0.08, 0.11), 8, 4), "Dark")
        P.obj("Eye", ball((s * 0.19, 2.13, 0.19), (0.12, 0.06, 0.085), 8, 4), "Lamp")
        P.obj("Brow", hull([(s * 0.04, 2.2, 0.3), (s * 0.32, 2.05, 0.38), (s * 0.32, 2.0, 0.33), (s * 0.05, 2.16, 0.25)]), "Accent", 0, False)
        for k in range(2):
            x = s * (0.09 + k * 0.1)
            P.obj("Fang", cone((x, 2.32, -0.06), (x, 2.34, -0.2), 0.03, 4), "Glass", 0, False)
        P.obj("Horn", pipe(bez((s * 0.3, 1.9, 0.3), (s * 0.5, 1.8, 0.5), (s * 0.55, 1.6, 0.72), (s * 0.45, 1.45, 0.88), 4), [0.09, 0.07, 0.05, 0.025, 0.0], 6), "Trim")
        bat_wing(P, s, Vector((s * 0.4, 0.6, 0.1)), Vector((s * 1.35, 0.35, 0.5)),
                 [Vector((s * 2.4, 0.15, 0.7)), Vector((s * 2.85, -0.4, 0.4)), Vector((s * 2.55, -1.0, 0.1)), Vector((s * 1.7, -1.2, 0.0))],
                 Vector((s * 0.4, -0.8, 0.02)), "Accent", "Base", "Trim")
        x = s * 1.3
        P.obj("Nacelle", loft([(1.05, 0.15, 0.15, x, -0.12), (0.8, 0.2, 0.2, x, -0.12), (-0.3, 0.18, 0.18, x, -0.1), (-0.5, 0.1, 0.1, x, -0.1)], 10), "Accent", 1)
        P.obj("Exhaust", tube(-0.5, -0.56, 0.08, 0.03, x, -0.1, 8), "Glow")
        P.prop((x, 1.12, -0.12), 0.5, 3, blade="Accent", tip="Trim", spinner="Glow", spinner_len=0.25)
    tail = bez((0, -1.95, 0.14), (0, -2.5, 0.2), (0.3, -2.8, 0.45), (0.1, -3.0, 0.75), 7)
    P.obj("Tail", pipe(tail, [0.08, 0.07, 0.065, 0.06, 0.05, 0.045, 0.04, 0.035], 6), "Base")
    t = tail[-1]
    P.obj("TailArrow", hull([t + Vector((0, 0, 0.3)), t + Vector((-0.18, 0, 0.0)), t + Vector((0.18, 0, 0.0)), t + Vector((0, 0.05, 0.1)), t + Vector((0, -0.05, 0.1))]), "Trim", 0, False)
    pilot(P, 0.95, 0.42, helmet="Accent", visor="Lamp", rim="Trim", horns="Trim")
    return P


# ================================================================= SEA 1: the whale clipper (the sky whale)
def S_whale():
    """A whale flying boat: a fat blue whale of a hull with a pale grooved belly, a big friendly-fierce eye and a long smile on each side,
    barnacles, flippers for wings carrying two propeller engines, whale flukes for a tail, a gold band, a glowing water spout and a pilot."""
    P = Plane("sea", {"Base": ((0.22, 0.45, 0.82), 0.55), "Belly": ((0.92, 0.94, 0.96), 0.5), "Accent": ((0.08, 0.18, 0.40), 0.5),
                      "Trim": ((1.0, 0.80, 0.30), 0.85), "Glass": ((0.55, 0.92, 1.0), 0.95), "Dark": ((0.03, 0.05, 0.10), 0.4),
                      "Glow": ((0.40, 0.95, 1.0), 0.5), "Metal": ((0.62, 0.64, 0.68), 0.6), "Lamp": ((1.0, 0.85, 0.5), 0.8)})
    def hullpaint(c, n):
        if n.z < -0.3: return "Accent" if (c.x * 7.0) % 1.0 < 0.18 else "Belly"
        return "Base"
    P.obj("Hull", loft([(2.6, 0.12, 0.1, 0, -0.08), (2.35, 0.5, 0.42, 0, -0.04), (1.6, 0.72, 0.6, 0, 0.0), (0.2, 0.74, 0.6, 0, 0.02),
                        (-1.1, 0.52, 0.42, 0, 0.06), (-1.9, 0.26, 0.22, 0, 0.12), (-2.3, 0.12, 0.1, 0, 0.16)], 16), hullpaint, 1)
    P.obj("Band", xf(torus(0.745, 0.04, 0.0, 22, 5), Matrix.Diagonal((1.0, 1.0, 0.81)) @ Matrix.Rotation(math.radians(90), 3, "X"), (0, 0.55, 0.02)), "Trim")
    for s in (1, -1):
        P.obj("EyeWhite", ball((s * 0.58, 1.75, 0.12), (0.06, 0.15, 0.13), 8, 4), "Belly")
        P.obj("Pupil", ball((s * 0.62, 1.79, 0.11), (0.04, 0.08, 0.08), 6, 3), "Dark")
        P.obj("Brow", cone((s * 0.6, 1.6, 0.27), (s * 0.58, 1.93, 0.25), 0.04, 4), "Accent")
        smile = [Vector((s * (0.42 + 0.3 * math.sin(math.pi * u * 0.5)), 2.35 - u * 1.0, -0.12 - 0.08 * math.sin(math.pi * u))) for u in [i / 6 for i in range(7)]]
        P.obj("Smile", pipe(smile, [0.025] * 7, 4), "Dark")
        for k in range(3):
            P.obj("Barnacle", ball((s * (0.45 + 0.08 * k), 1.2 - k * 0.15, 0.4 - k * 0.05), (0.05, 0.05, 0.04), 6, 3), "Metal")
        x = s * 1.3
        P.obj("Nacelle", loft([(0.95, 0.12, 0.12, x, 0.12), (0.7, 0.17, 0.17, x, 0.12), (-0.4, 0.15, 0.15, x, 0.14), (-0.6, 0.06, 0.06, x, 0.14)], 10), "Trim", 1)
        P.prop((x, 1.02, 0.12), 0.55, 3, blade="Accent", tip="Belly", spinner="Base", spinner_len=0.25)
    P.wing([(0.6, 0.55, -0.45, 0.16, -0.12), (1.8, 0.35, -0.5, 0.11, -0.2), (2.7, -0.05, -0.55, 0.06, -0.3), (2.95, -0.3, -0.6, 0.04, -0.33)],
           lambda c, n: "Belly" if n.z < -0.3 else ("Glow" if abs(c.x) > 2.75 else "Base"))
    P.wing([(0.1, -1.9, -2.45, 0.09, 0.15), (0.9, -2.2, -2.75, 0.06, 0.2), (1.35, -2.55, -2.95, 0.04, 0.26)],
           lambda c, n: "Belly" if n.z < -0.3 else ("Glow" if abs(c.x) > 1.2 else "Base"), name="Fluke")
    P.fin([(0.0, -1.1, -1.6, 0.08), (0.3, -1.35, -1.6, 0.05)], 0.0, 0.5, 0, "Base")
    pilot(P, 1.15, 0.58, helmet="Accent", visor="Glass", rim="Trim")
    for k in range(5):   # the water spout
        a = 2 * math.pi * k / 5
        b = Vector((0, 0.15, 0.62))
        P.obj("Spout", cone(b, b + Vector((math.sin(a) * 0.18, -0.08 + math.cos(a) * 0.08, 0.45)), 0.05, 4), "Glow" if k % 2 else "Glass", 0, False)
    P.obj("SpoutTop", ball((0, 0.12, 1.05), (0.1, 0.1, 0.08), 6, 3), "Glass")
    return P


# ================================================================= SEA 2: the storm roc (the thunder roc)
def S_roc():
    """A storm-roc fighter: a white eagle body with a gold breastplate and a lightning emblem, an eagle head for a nose with a fierce brow,
    golden eyes and a big hooked gold beak, a swept blue crest, feathered wings with blue tips, layered feathers and a glowing lightning
    zigzag, a fanned tail, two jets under the wings and a pilot on its back."""
    P = Plane("sea2", {"Base": ((0.94, 0.95, 0.97), 0.45), "Belly": ((0.70, 0.78, 0.88), 0.4), "Accent": ((0.22, 0.48, 0.95), 0.55),
                       "Trim": ((1.0, 0.78, 0.26), 0.85), "Glass": ((0.55, 0.92, 1.0), 0.95), "Dark": ((0.05, 0.06, 0.10), 0.4),
                       "Glow": ((0.35, 0.90, 1.0), 0.5), "Metal": ((0.45, 0.47, 0.52), 0.6), "Lamp": ((1.0, 0.85, 0.2), 0.8)})
    P.obj("Body", loft([(1.6, 0.36, 0.34, 0, 0.0), (0.8, 0.46, 0.42, 0, -0.02), (-0.4, 0.42, 0.36, 0, 0.0), (-1.4, 0.26, 0.24, 0, 0.06), (-1.9, 0.12, 0.12, 0, 0.1)], 14),
          lambda c, n: "Trim" if n.y > 0.2 and n.z < 0.2 and c.y > 0.5 else ("Belly" if n.z < -0.4 else "Base"), 1)
    P.obj("Bolt", hull([(0.05, 1.42, 0.12), (-0.12, 1.45, -0.02), (0.04, 1.45, -0.02), (-0.08, 1.42, -0.2), (0.12, 1.4, 0.02), (-0.03, 1.4, 0.02)]), "Glow", 0, False)
    P.obj("Head", ball((0, 1.95, 0.18), (0.38, 0.42, 0.36), 12, 6), "Base", 1)
    beak = bez((0, 2.25, 0.18), (0, 2.65, 0.2), (0, 2.85, 0.05), (0, 2.8, -0.15), 6)
    P.obj("Beak", pipe(beak, [0.2, 0.18, 0.14, 0.1, 0.07, 0.04, 0.0], 8), "Trim")
    P.obj("BeakLow", pipe(bez((0, 2.25, 0.02), (0, 2.45, -0.02), (0, 2.55, -0.06), (0, 2.6, -0.08), 4), [0.12, 0.09, 0.06, 0.03, 0.0], 6), "Trim")
    for s in (1, -1):
        P.obj("Eye", ball((s * 0.2, 2.22, 0.3), (0.07, 0.07, 0.06), 8, 4), "Lamp")
        P.obj("Pupil", ball((s * 0.21, 2.27, 0.3), (0.03, 0.025, 0.035), 6, 3), "Dark")
        P.obj("Brow", hull([(s * 0.04, 2.27, 0.42), (s * 0.34, 2.12, 0.44), (s * 0.34, 2.1, 0.39), (s * 0.05, 2.24, 0.37)]), "Accent", 0, False)
        jet(P, s * 1.15, 0.4, -0.6, -0.25, 0.14, "Metal", "Glow")
        for k in range(6):   # layered feathers along the trailing edge, blue at the tip
            x = 0.6 + k * 0.42
            P.obj("Feather", cone((s * x, -0.45 + 0.06 * k, 0.03), (s * (x + 0.08), -0.95 + 0.08 * k, -0.02), 0.13, 4), "Accent" if k > 3 else "Base", 0, False)
        for k in range(4):   # the fingered tip feathers
            a = math.radians(-25 + k * 22)
            b = Vector((s * 2.6, 0.0 - k * 0.12, 0.08))
            P.obj("TipFeather", cone(b, b + Vector((s * math.cos(a) * 0.55, math.sin(a) * 0.4, 0.03 + k * 0.02)), 0.08, 4), "Accent", 0, False)
        zig = [Vector((s * x, y, 0.13)) for x, y in ((0.55, 0.3), (1.0, 0.05), (1.3, 0.3), (1.8, 0.0), (2.1, 0.2), (2.55, -0.05))]
        P.obj("Lightning", pipe([p + Vector((0, 0, 0.06)) for p in zig], [0.045] * len(zig), 4), "Glow")
        for k in range(4):   # the blue crest swept back
            b = Vector((s * 0.05 * k, 1.85 - k * 0.05, 0.48))
            P.obj("Crest", cone(b, b + Vector((s * 0.08 * k, -0.45 - k * 0.05, 0.25 - k * 0.04)), 0.07, 4), "Accent", 0, False)
    P.wing([(0.4, 0.55, -0.45, 0.15, 0.05), (1.5, 0.45, -0.45, 0.1, 0.08), (2.6, 0.25, -0.25, 0.05, 0.08)],
           lambda c, n: "Belly" if n.z < -0.3 else ("Trim" if n.y > 0.6 else "Base"))
    for k in range(7):   # the fanned tail
        a = math.radians(-45 + k * 15)
        b = Vector((0, -1.8, 0.1))
        P.obj("TailFeather", cone(b, b + Vector((math.sin(a) * 0.75, -math.cos(a) * 0.8, 0.0)), 0.11, 4), "Accent" if k % 2 else "Base", 0, False)
    pilot(P, 0.75, 0.42, helmet="Accent", visor="Glass", rim="Trim")
    return P


PLANES = [("alien", A_manta), ("alien2", A_dragon), ("lava", L_salamander), ("lava2", L_demon), ("sea", S_whale), ("sea2", S_roc)]

if __name__ == "__main__":
    os.makedirs(EP.OUT, exist_ok=True)
    for pid, fn in PLANES:
        if ONLY and pid not in ONLY: continue
        fn().finish()
    print("DONE")
