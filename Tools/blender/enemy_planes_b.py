# Sky Squad enemy planes, the second of each world (2026-10-10: "two planes for every level: the first shape with the first two bosses,
# then the second shape to the end"). Imported by enemy_planes.py, which hands over its helpers (Plane, loft, sweep, lathe, ...).
# Same conventions: +Y nose, +Z up, +X right; "Prop<n>" spin about the nose, "Rotor..." about up.
import math
from mathutils import Vector, Matrix


def define_b(g):
    globals().update({k: v for k, v in g.items() if not k.startswith("__")})
    return [("sea2", B_sea), ("lava2", B_lava), ("alien2", B_alien), ("meadow2", B_meadow), ("autumn2", B_autumn), ("camping2", B_camping),
            ("christmas2", B_christmas), ("desert2", B_desert), ("city2", B_city), ("japan2", B_japan), ("soccer2", B_soccer),
            ("shuttle2", B_shuttle), ("treasure2", B_treasure), ("west2", B_west)]


def B_sea():
    """World 1, second: a carrier torpedo bomber (Avenger style) - a fat navy body, a ball turret behind the long canopy, a torpedo underneath."""
    P = Plane("sea2", {"Base": ((0.12, 0.22, 0.42), 0.45), "Belly": ((0.86, 0.88, 0.90), 0.4), "Accent": ((0.95, 0.95, 0.95), 0.5),
                       "Trim": ((0.96, 0.78, 0.15), 0.5), "Glass": ((0.4, 0.58, 0.68), 0.92), "Dark": ((0.07, 0.07, 0.08), 0.3),
                       "Glow": ((1.0, 0.55, 0.2), 0.5), "Metal": ((0.55, 0.56, 0.6), 0.6)})
    P.obj("Fuselage", loft([(2.3, 0.4, 0.4, 0, 0.0), (1.9, 0.48, 0.52, 0, 0.0), (0.9, 0.5, 0.6, 0, 0.0), (-0.3, 0.42, 0.55, 0, 0.02),
                            (-1.3, 0.24, 0.32, 0, 0.12), (-2.45, 0.06, 0.1, 0, 0.22)], 16, sq=1.2),
          lambda c, n: "Dark" if c.y > 2.0 else ("Belly" if c.z < -0.2 else "Base"), 1)
    P.obj("CowlFace", lathe([(0.0, 2.35), (0.25, 2.33), (0.38, 2.27)], 16, "y"), "Metal", 0)
    P.obj("Canopy", loft([(-0.25, 0.04, 0.03, 0, 0.45), (0.0, 0.2, 0.18, 0, 0.52), (1.0, 0.22, 0.22, 0, 0.56), (1.45, 0.15, 0.12, 0, 0.5), (1.6, 0.04, 0.03, 0, 0.45)], 12), "Glass", 1)
    P.obj("Turret", lathe([(0.0, 0.88), (0.17, 0.82), (0.24, 0.66), (0.22, 0.52)], 14, "z", (0, -0.45, 0)), "Glass", 1)
    P.obj("TurretGun", tube(-0.45, 0.25, 0.03, 0.03, 0, 0.7, 6), "Dark", 0)
    P.wing([(0.35, 0.95, -0.35, 0.18, -0.25), (1.6, 0.8, -0.2, 0.13, -0.17), (2.75, 0.5, 0.05, 0.07, -0.06), (2.95, 0.38, 0.12, 0.05, -0.04)],
           lambda c, n: "Belly" if n.z < -0.3 else ("Accent" if abs(c.x) > 2.7 else "Base"))
    P.obj("Torpedo", loft([(1.3, 0.02, 0.02, 0, -0.68), (1.1, 0.13, 0.13, 0, -0.68), (-0.6, 0.13, 0.13, 0, -0.68), (-0.85, 0.05, 0.05, 0, -0.68)], 10),
          lambda c, n: "Trim" if c.y > 1.0 else "Metal", 1)
    P.wing([(0.1, -1.85, -2.45, 0.07, 0.25), (1.15, -2.0, -2.4, 0.05, 0.25)], name="Stab")
    P.fin([(0.0, -1.6, -2.5, 0.09), (0.75, -1.9, -2.5, 0.07), (0.9, -2.05, -2.45, 0.05)], 0.0, 0.22, 0, lambda c, n: "Trim" if c.z > 1.0 else "Base")
    P.prop((0, 2.45, 0.0), 1.0, 3, spinner="Metal")
    return P


def B_lava():
    """World 2, second: a flying-wing bomber (B-2 style) - one black blade with a sawtooth trailing edge, magma-lit edges and glowing slit exhausts."""
    P = Plane("lava2", {"Base": ((0.10, 0.09, 0.09), 0.4), "Belly": ((0.18, 0.13, 0.11), 0.3), "Accent": ((0.5, 0.07, 0.03), 0.45),
                        "Trim": ((0.3, 0.28, 0.27), 0.5), "Glass": ((0.95, 0.42, 0.06), 0.92), "Dark": ((0.04, 0.04, 0.04), 0.3),
                        "Glow": ((1.0, 0.33, 0.03), 0.5), "Metal": ((0.32, 0.30, 0.29), 0.5)})
    xs = [0.0, 0.7, 1.35, 2.0, 2.65, 3.0]
    le = lambda x: 1.7 - x * 0.95
    te = [-1.05, -0.55, -1.15, -0.65, -1.0, -1.15]   # the sawtooth
    th = lambda x: 0.55 * (1 - x / 3.1) + 0.05
    sections = [(-x, airfoil(le(x), t, th(x), 0.0)) for x, t in zip(reversed(xs), reversed(te))] + [(x, airfoil(le(x), t, th(x), 0.0)) for x, t in zip(xs[1:], te[1:])]
    P.obj("Wing", sweep(sections, "x"), lambda c, n: "Glow" if n.y > 0.6 and abs(c.x) > 0.25 else ("Belly" if n.z < -0.3 else "Base"), 1)
    P.obj("Hump", loft([(1.75, 0.02, 0.02, 0, 0.12), (1.3, 0.38, 0.18, 0, 0.2), (0.4, 0.62, 0.28, 0, 0.22), (-0.6, 0.5, 0.18, 0, 0.16), (-0.95, 0.3, 0.06, 0, 0.1)], 16, sq=1.3), "Base", 1)
    P.obj("Canopy", hull([(0.18, 1.35, 0.33), (-0.18, 1.35, 0.33), (0.25, 1.05, 0.42), (-0.25, 1.05, 0.42), (0, 1.5, 0.27), (0.22, 0.95, 0.3), (-0.22, 0.95, 0.3)]), "Glass", 0, False)
    for s in (1, -1):
        P.obj("Intake", hull([(s * 0.55, 0.55, 0.3), (s * 0.95, 0.4, 0.26), (s * 0.55, 0.3, 0.42), (s * 0.95, 0.15, 0.38), (s * 0.6, 0.6, 0.22)]), "Dark", 0, False)
        P.obj("Slit", box((s * 0.75, -0.65, 0.22), (0.5, 0.18, 0.04)), "Glow", 0, False)
    return P


def B_alien():
    """World 3, second: a boomerang interceptor - a sweeping teal crescent around a long spine pod, three green engine rings and a glowing eye."""
    P = Plane("alien2", {"Base": ((0.07, 0.26, 0.27), 0.55), "Belly": ((0.04, 0.13, 0.15), 0.45), "Accent": ((0.75, 0.95, 0.4), 0.6),
                         "Trim": ((0.72, 0.78, 0.8), 0.6), "Glass": ((0.5, 1.0, 0.3), 0.9), "Dark": ((0.03, 0.06, 0.07), 0.4),
                         "Glow": ((0.45, 1.0, 0.25), 0.5), "Metal": ((0.45, 0.55, 0.58), 0.6), "Lamp": ((0.55, 1.0, 0.35), 0.8)})
    P.obj("Spine", loft([(2.6, 0.02, 0.02, 0, 0.0), (2.2, 0.16, 0.14, 0, 0.02), (1.2, 0.3, 0.26, 0, 0.05), (-0.4, 0.32, 0.28, 0, 0.05), (-1.6, 0.2, 0.18, 0, 0.04), (-2.2, 0.1, 0.1, 0, 0.02)], 14),
          lambda c, n: "Belly" if c.z < -0.12 else "Base", 1)
    P.obj("Eye", lathe([(0.0, 0.0), (0.16, 0.0), (0.2, 0.1), (0.14, 0.2), (0.0, 0.22)], 14, "z", (0, 1.4, 0.24)), "Lamp", 1)
    # the crescent: tips swept back and curling forward again
    P.wing([(0.25, 0.8, -0.5, 0.16, 0.0), (1.1, 0.0, -1.0, 0.12, 0.05), (1.9, -0.75, -1.45, 0.08, 0.12), (2.5, -1.1, -1.6, 0.06, 0.2), (2.75, -0.75, -1.15, 0.04, 0.28)],
           lambda c, n: "Glow" if n.y > 0.6 and abs(c.x) > 1.2 else ("Accent" if abs(c.x) > 2.55 else ("Belly" if n.z < -0.3 else "Base")), name="Crescent")
    for x, y, z in ((0, -2.1, 0.02), (1.25, -1.1, 0.0), (-1.25, -1.1, 0.0)):
        P.obj("Ring", lathe([(0.2, 0.12), (0.26, 0.05), (0.26, -0.15), (0.2, -0.2), (0.14, -0.15), (0.14, 0.08)], 14, "y", (x, y, z)), lambda c, n: "Metal", 1)
        P.obj("RingGlow", lathe([(0.0, -0.16), (0.15, -0.16), (0.15, -0.1), (0.0, -0.1)], 12, "y", (x, y, z)), "Glow", 0)
    for s in (1, -1):
        P.obj("Prong", loft([(0.9, 0.06, 0.06, s * 0.42, -0.1), (2.0, 0.04, 0.04, s * 0.42, -0.1), (2.15, 0.07, 0.07, s * 0.42, -0.1)], 8), lambda c, n: "Glow" if c.y > 2.05 else "Metal", 1)
    return P


def B_meadow():
    """World 4, second: an elliptical-wing fighter (Spitfire style) - green and brown over sky blue, a long nose, a bubble canopy."""
    P = Plane("meadow2", {"Base": ((0.30, 0.38, 0.20), 0.4), "Belly": ((0.62, 0.74, 0.80), 0.35), "Accent": ((0.42, 0.30, 0.16), 0.4),
                          "Trim": ((0.95, 0.80, 0.25), 0.5), "Glass": ((0.5, 0.68, 0.75), 0.92), "Dark": ((0.07, 0.07, 0.07), 0.3),
                          "Glow": ((1.0, 0.55, 0.2), 0.5), "Metal": ((0.55, 0.56, 0.58), 0.6)})
    P.obj("Fuselage", loft([(2.45, 0.08, 0.1, 0, 0.0), (2.2, 0.24, 0.3, 0, 0.0), (1.4, 0.32, 0.4, 0, 0.02), (0.3, 0.3, 0.4, 0, 0.05),
                            (-1.0, 0.18, 0.27, 0, 0.1), (-2.35, 0.04, 0.08, 0, 0.16)], 14),
          lambda c, n: "Accent" if c.y > 1.45 and c.z > 0.1 else ("Belly" if c.z < -0.12 else "Base"), 1)
    P.obj("Canopy", lathe([(0.0, 0.66), (0.14, 0.62), (0.2, 0.52), (0.21, 0.4)], 14, "z", (0, 0.4, 0.0)), "Glass", 1)
    secs = []
    for x in (0.25, 0.9, 1.5, 2.0, 2.4, 2.65, 2.78):
        f = math.sqrt(max(0.0, 1 - (x / 2.85) ** 2))   # the ellipse
        secs.append((x, 0.25 + 0.6 * f, 0.25 - 0.7 * f, 0.04 + 0.13 * f, -0.18 + x * 0.05))
    P.wing(secs, lambda c, n: "Belly" if n.z < -0.3 else ("Trim" if n.y > 0.6 and abs(c.x) < 1.2 else ("Accent" if 1.2 < abs(c.x) < 1.8 else "Base")))
    for s in (1, -1):
        P.obj("Radiator", box((s * 0.75, -0.05, -0.32), (0.22, 0.6, 0.12)), lambda c, n: "Dark" if n.y > 0.5 else "Belly", 0, False)
        for g in (1.0, 1.4):
            P.obj("Gun", tube(0.2, 0.75, 0.025, 0.025, s * g, -0.14 + g * 0.05, 6), "Dark", 0)
    P.wing([(0.08, -1.75, -2.3, 0.06, 0.15), (0.75, -1.85, -2.25, 0.05, 0.15), (0.95, -2.0, -2.2, 0.03, 0.15)], name="Stab")
    P.fin([(0.0, -1.55, -2.38, 0.07), (0.5, -1.8, -2.4, 0.05), (0.7, -2.05, -2.35, 0.04)], 0.0, 0.15, 0, "Base")
    P.prop((0, 2.55, 0.0), 0.85, 4, spinner="Trim")
    return P


def B_autumn():
    """World 5, second: the first jet fighter (Me-262 style) - a shark-shaped body, two jet pods under the swept wings, bark brown and rust."""
    P = Plane("autumn2", {"Base": ((0.42, 0.30, 0.16), 0.4), "Belly": ((0.78, 0.70, 0.52), 0.35), "Accent": ((0.70, 0.30, 0.08), 0.45),
                          "Trim": ((0.95, 0.70, 0.2), 0.5), "Glass": ((0.35, 0.48, 0.45), 0.92), "Dark": ((0.06, 0.06, 0.06), 0.3),
                          "Glow": ((1.0, 0.5, 0.15), 0.5), "Metal": ((0.5, 0.5, 0.52), 0.6)})
    P.obj("Fuselage", loft([(2.55, 0.03, 0.03, 0, -0.05), (2.2, 0.2, 0.2, 0, -0.03), (1.2, 0.34, 0.36, 0, 0.0), (0.0, 0.38, 0.36, 0, 0.0),
                            (-1.2, 0.26, 0.26, 0, 0.04), (-2.35, 0.06, 0.1, 0, 0.12)], 16, sq=1.1),
          lambda c, n: "Accent" if c.y > 2.0 else ("Belly" if c.z < -0.15 else "Base"), 1)
    for k in range(4):
        P.obj("Gun", tube(2.1, 2.5, 0.025, 0.025, (k - 1.5) * 0.08, 0.12, 6), "Dark", 0)
    P.obj("Canopy", loft([(0.1, 0.04, 0.03, 0, 0.3), (0.35, 0.17, 0.17, 0, 0.36), (0.9, 0.18, 0.2, 0, 0.38), (1.25, 0.1, 0.1, 0, 0.32)], 12), "Glass", 1)
    P.wing([(0.35, 0.55, -0.45, 0.13, -0.14), (1.4, 0.15, -0.65, 0.1, -0.1), (2.6, -0.45, -0.9, 0.06, -0.05), (2.75, -0.55, -0.88, 0.04, -0.04)],
           lambda c, n: "Belly" if n.z < -0.3 else ("Accent" if abs(c.x) > 2.5 else "Base"))
    for s in (1, -1):
        x = s * 1.15
        P.obj("Jet", loft([(0.85, 0.2, 0.2, x, -0.32), (0.6, 0.24, 0.24, x, -0.32), (-0.6, 0.22, 0.22, x, -0.32), (-0.95, 0.12, 0.12, x, -0.32)], 14),
              lambda c, n: "Dark" if c.y > 0.82 else ("Belly" if c.z < -0.4 else "Base"), 1)
        P.obj("Cone", lathe([(0.0, 0.95), (0.08, 0.86), (0.12, 0.8)], 10, "y", (x, 0, -0.32)), "Accent", 0)
        P.obj("Core", tube(-0.92, -0.98, 0.1, 0.03, x, -0.32, 12), "Glow")
    P.wing([(0.08, -1.65, -2.2, 0.06, 0.32), (0.85, -1.95, -2.25, 0.04, 0.32)], name="Stab")
    P.fin([(0.0, -1.5, -2.35, 0.08), (0.6, -1.85, -2.38, 0.06), (0.75, -2.0, -2.35, 0.04)], 0.0, 0.15, 0, lambda c, n: "Accent" if c.z > 0.65 else "Base")
    return P


def B_camping():
    """World 6, second: a twin-engine night bomber (Mosquito style) in black, amber-hot exhaust stacks and a lit cockpit."""
    P = Plane("camping2", {"Base": ((0.08, 0.09, 0.12), 0.4), "Belly": ((0.05, 0.05, 0.07), 0.3), "Accent": ((0.30, 0.34, 0.24), 0.4),
                           "Trim": ((0.85, 0.15, 0.12), 0.5), "Glass": ((1.0, 0.68, 0.25), 0.9), "Dark": ((0.03, 0.03, 0.04), 0.3),
                           "Glow": ((1.0, 0.62, 0.2), 0.5), "Metal": ((0.36, 0.38, 0.42), 0.6), "Lamp": ((1.0, 0.65, 0.25), 0.9)})
    P.obj("Fuselage", loft([(2.15, 0.06, 0.06, 0, 0.0), (1.9, 0.26, 0.3, 0, 0.02), (1.0, 0.36, 0.4, 0, 0.05), (-0.2, 0.32, 0.36, 0, 0.05),
                            (-1.4, 0.18, 0.22, 0, 0.1), (-2.4, 0.05, 0.08, 0, 0.16)], 14),
          lambda c, n: "Belly" if c.z < -0.15 else "Base", 1)
    P.obj("Canopy", loft([(1.0, 0.04, 0.03, 0, 0.38), (1.25, 0.22, 0.17, 0, 0.42), (1.6, 0.2, 0.15, 0, 0.36), (1.8, 0.05, 0.04, 0, 0.3)], 12), "Lamp", 1)
    P.obj("NoseGlass", lathe([(0.0, 2.25), (0.08, 2.2), (0.12, 2.12)], 10, "y", (0, 0, 0.02)), "Lamp", 0)
    P.wing([(0.3, 1.15, -0.25, 0.17, -0.02), (1.6, 1.0, -0.1, 0.13, 0.03), (2.85, 0.65, 0.12, 0.07, 0.1), (3.05, 0.5, 0.2, 0.05, 0.11)],
           lambda c, n: "Belly" if n.z < -0.3 else "Base")
    for s in (1, -1):
        x = s * 1.05
        P.obj("Nacelle", loft([(1.75, 0.22, 0.22, x, 0.0), (1.4, 0.27, 0.3, x, -0.02), (0.2, 0.25, 0.28, x, -0.04), (-0.7, 0.12, 0.12, x, 0.0)], 12),
              lambda c, n: "Belly" if c.z < -0.15 else "Base", 1)
        for k in range(3):
            P.obj("Stack", box((x + s * 0.27, 1.2 - k * 0.2, 0.02), (0.05, 0.12, 0.05)), "Glow", 0, False)
        P.prop((x, 1.85, 0.0), 0.75, 3, blade="Dark", tip="Trim")
    P.wing([(0.08, -1.85, -2.45, 0.07, 0.15), (1.15, -1.95, -2.4, 0.05, 0.15)], name="Stab")
    P.fin([(0.0, -1.55, -2.45, 0.08), (0.75, -1.85, -2.45, 0.06), (0.9, -2.05, -2.42, 0.04)], 0.0, 0.18, 0, lambda c, n: "Trim" if c.z > 0.95 else "Base")
    return P


def B_christmas():
    """World 7, second: a twin-rotor transport helicopter (Chinook style), white with red bands - the sleigh of the squadron."""
    P = Plane("christmas2", {"Base": ((0.90, 0.91, 0.93), 0.5), "Belly": ((0.70, 0.72, 0.76), 0.45), "Accent": ((0.82, 0.08, 0.10), 0.55),
                             "Trim": ((0.10, 0.48, 0.22), 0.5), "Glass": ((0.28, 0.45, 0.62), 0.92), "Dark": ((0.06, 0.06, 0.08), 0.3),
                             "Glow": ((1.0, 0.85, 0.4), 0.5), "Metal": ((0.55, 0.57, 0.6), 0.6)})
    P.obj("Body", loft([(2.3, 0.1, 0.12, 0, -0.05), (2.05, 0.38, 0.45, 0, 0.0), (1.4, 0.45, 0.55, 0, 0.02), (-1.6, 0.45, 0.55, 0, 0.02), (-2.3, 0.36, 0.48, 0, 0.1)], 14, sq=1.7),
          lambda c, n: "Accent" if (0.3 < c.y < 0.65 or -1.25 < c.y < -0.9) else ("Belly" if c.z < -0.35 else "Base"), 1)
    P.obj("Cockpit", loft([(1.75, 0.3, 0.12, 0, 0.32), (2.15, 0.26, 0.1, 0, 0.22), (2.3, 0.1, 0.04, 0, 0.1)], 12, sq=1.4), "Glass", 1)
    P.obj("FrontPylon", loft([(2.0, 0.12, 0.1, 0, 0.55), (1.3, 0.2, 0.3, 0, 0.7), (1.0, 0.16, 0.2, 0, 0.62)], 10), "Base", 1)
    P.obj("RearPylon", loft([(-1.0, 0.25, 0.2, 0, 0.6), (-1.8, 0.3, 0.55, 0, 0.75), (-2.45, 0.2, 0.35, 0, 0.7), (-2.6, 0.08, 0.1, 0, 0.6)], 12),
          lambda c, n: "Trim" if c.z > 0.95 else "Base", 1)
    for s in (1, -1):
        P.obj("Pod", loft([(0.9, 0.06, 0.06, s * 0.52, -0.15), (0.7, 0.14, 0.18, s * 0.52, -0.15), (-1.3, 0.14, 0.18, s * 0.52, -0.15), (-1.45, 0.08, 0.1, s * 0.52, -0.15)], 10),
              lambda c, n: "Trim", 1)
        for y in (1.55, -1.5):
            P.obj("Wheel", lathe([(0.0, -0.05), (0.13, -0.05), (0.15, 0.0), (0.13, 0.05), (0.0, 0.05)], 10, "x", (s * 0.42, y, -0.66)), "Dark", 0)
        P.obj("Lamp", lathe([(0.0, 0.0), (0.06, 0.0), (0.06, 0.04), (0.0, 0.05)], 10, "y", (s * 0.3, 2.2, -0.2)), "Glow", 0)
    P.prop((0, 1.3, 0.98), 1.55, 3, axis="z", chord=0.16, blade="Dark", tip="Accent", spinner="Metal", spinner_len=0.16, name="Rotor")
    P.prop((0, -1.85, 1.15), 1.55, 3, axis="z", chord=0.16, blade="Dark", tip="Accent", spinner="Metal", spinner_len=0.16, name="Rotor2")
    return P


def B_desert():
    """World 8, second: a light multirole fighter (F-16 style) in two sands - a chin intake, a bubble canopy, missiles on the tips, one tall fin."""
    P = Plane("desert2", {"Base": ((0.76, 0.63, 0.44), 0.4), "Belly": ((0.88, 0.82, 0.66), 0.35), "Accent": ((0.55, 0.42, 0.26), 0.4),
                          "Trim": ((0.92, 0.92, 0.9), 0.5), "Glass": ((0.75, 0.55, 0.2), 0.95), "Dark": ((0.06, 0.06, 0.06), 0.3),
                          "Glow": ((1.0, 0.55, 0.2), 0.5), "Metal": ((0.5, 0.5, 0.5), 0.6)})
    P.obj("Fuselage", loft([(2.85, 0.02, 0.02, 0, 0.08), (2.3, 0.15, 0.15, 0, 0.08), (1.4, 0.28, 0.3, 0, 0.06), (0.4, 0.34, 0.33, 0, 0.04),
                            (-1.2, 0.3, 0.3, 0, 0.04), (-2.2, 0.22, 0.22, 0, 0.04)], 16),
          lambda c, n: "Accent" if c.y > 2.5 else ("Belly" if c.z < -0.12 else "Base"), 1)
    P.obj("Intake", loft([(1.1, 0.24, 0.16, 0, -0.32), (0.7, 0.25, 0.17, 0, -0.3), (-0.6, 0.2, 0.14, 0, -0.22)], 12, sq=1.5), lambda c, n: "Dark" if c.y > 1.05 else "Belly", 1)
    P.obj("Core", tube(-2.18, -2.25, 0.17, 0.05, 0, 0.04, 14), "Glow")
    P.obj("Canopy", lathe([(0.0, 0.62), (0.15, 0.58), (0.22, 0.46), (0.22, 0.32)], 14, "z", (0, 1.45, 0.0)), "Glass", 1)
    P.obj("CanopyRear", loft([(1.45, 0.2, 0.25, 0, 0.32), (0.7, 0.14, 0.12, 0, 0.38), (0.2, 0.05, 0.05, 0, 0.3)], 12), "Glass", 1)
    P.wing([(0.3, 0.55, -1.05, 0.12, 0.0), (1.2, -0.25, -1.15, 0.08, 0.0), (2.0, -0.85, -1.25, 0.05, 0.0)],
           lambda c, n: "Belly" if n.z < -0.3 else ("Accent" if abs(c.x) > 1.75 else "Base"))
    for s in (1, -1):
        P.missile(s * 2.05, 0.0, -1.55, 1.25, 0.06, "Trim", "Accent")
        P.missile(s * 1.2, -0.2, -1.2, 1.1, 0.06, "Trim", "Dark")
    P.wing([(0.25, -1.55, -2.3, 0.06, 0.0), (1.05, -2.0, -2.35, 0.04, 0.0)], name="Stab")
    P.fin([(0.0, -0.9, -2.15, 0.1), (0.9, -1.55, -2.25, 0.07), (1.15, -1.8, -2.3, 0.05)], 0.0, 0.3, 0, lambda c, n: "Accent" if c.z > 1.3 else "Base")
    return P


def B_city():
    """World 9, second: a tiltrotor (Osprey style) - a gunmetal box body, a straight wing with two huge rotors on the tips, a twin-fin tail."""
    P = Plane("city2", {"Base": ((0.32, 0.34, 0.37), 0.45), "Belly": ((0.22, 0.23, 0.25), 0.4), "Accent": ((0.95, 0.80, 0.25), 0.5),
                        "Trim": ((0.95, 0.80, 0.25), 0.5), "Glass": ((0.25, 0.35, 0.42), 0.92), "Dark": ((0.05, 0.05, 0.06), 0.3),
                        "Glow": ((1.0, 0.5, 0.15), 0.5), "Metal": ((0.45, 0.46, 0.5), 0.6), "Lamp": ((1.0, 0.85, 0.45), 0.8)})
    P.obj("Body", loft([(2.3, 0.08, 0.1, 0, -0.1), (2.0, 0.3, 0.32, 0, -0.04), (1.3, 0.4, 0.42, 0, 0.0), (-1.2, 0.4, 0.42, 0, 0.0), (-2.4, 0.15, 0.2, 0, 0.22)], 14, sq=1.6),
          lambda c, n: "Belly" if c.z < -0.25 else "Base", 1)
    P.obj("Cockpit", loft([(1.6, 0.3, 0.1, 0, 0.3), (2.0, 0.24, 0.08, 0, 0.18), (2.2, 0.08, 0.03, 0, 0.05)], 12, sq=1.4), "Glass", 1)
    P.wing([(0.0, 0.45, -0.3, 0.14, 0.5), (2.0, 0.45, -0.3, 0.14, 0.5)], mirror=True)
    for s in (1, -1):
        x = s * 2.1
        P.obj("Nacelle", lathe([(0.0, 0.05), (0.2, 0.1), (0.22, 0.5), (0.2, 0.95), (0.08, 1.05)], 12, "z", (x, 0.05, 0.05)), lambda c, n: "Belly" if c.z < 0.4 else "Base", 1)
        P.obj("NavLight", box((x + s * 0.24, 0.05, 0.5), (0.06, 0.1, 0.06)), "Lamp", 0, False)
        P.prop((x, 0.05, 1.12), 1.15, 3, axis="z", chord=0.18, blade="Dark", tip="Accent", spinner="Metal", spinner_len=0.2, name="Rotor" + ("" if s > 0 else "2"))
        P.fin([(0.0, -1.95, -2.5, 0.07), (0.55, -2.15, -2.55, 0.05), (0.65, -2.25, -2.55, 0.04)], s * 0.8, 0.22, 0, "Base")
    P.wing([(0.1, -1.95, -2.5, 0.06, 0.22), (0.82, -1.98, -2.5, 0.05, 0.22)], name="Stab")
    P.obj("Probe", tube(2.0, 2.75, 0.025, 0.02, 0.22, 0.1, 6), "Metal", 0)
    return P


def B_japan():
    """World 10, second: a float fighter (Rufe style) - pale grey with a cherry-red cowl and tail, one big float under the belly, two tip floats."""
    P = Plane("japan2", {"Base": ((0.80, 0.80, 0.76), 0.45), "Belly": ((0.68, 0.70, 0.67), 0.4), "Accent": ((0.85, 0.20, 0.30), 0.5),
                         "Trim": ((0.95, 0.55, 0.65), 0.5), "Glass": ((0.45, 0.62, 0.68), 0.92), "Dark": ((0.07, 0.07, 0.08), 0.3),
                         "Glow": ((1.0, 0.55, 0.2), 0.5), "Metal": ((0.58, 0.6, 0.6), 0.6)})
    P.obj("Fuselage", loft([(2.2, 0.34, 0.34, 0, 0.3), (1.95, 0.4, 0.4, 0, 0.3), (1.5, 0.4, 0.4, 0, 0.3), (0.2, 0.32, 0.36, 0, 0.33), (-1.2, 0.2, 0.24, 0, 0.38), (-2.3, 0.05, 0.08, 0, 0.45)], 16),
          lambda c, n: "Accent" if c.y > 1.5 or c.y < -1.85 else ("Belly" if c.z < 0.15 else "Base"), 1)
    P.obj("CowlFace", lathe([(0.0, 2.25), (0.22, 2.23), (0.32, 2.17)], 16, "y", (0, 0, 0.3)), "Dark", 0)
    P.obj("Canopy", loft([(-0.1, 0.04, 0.03, 0, 0.6), (0.15, 0.17, 0.16, 0, 0.66), (0.7, 0.19, 0.2, 0, 0.7), (1.1, 0.15, 0.14, 0, 0.65), (1.25, 0.04, 0.03, 0, 0.6)], 12), "Glass", 1)
    P.wing([(0.3, 0.85, -0.3, 0.15, 0.12), (1.6, 0.7, -0.12, 0.11, 0.2), (2.45, 0.45, 0.05, 0.06, 0.28), (2.6, 0.32, 0.12, 0.04, 0.3)],
           lambda c, n: "Belly" if n.z < -0.3 else ("Trim" if n.y > 0.6 else "Base"))
    P.obj("Float", loft([(1.9, 0.03, 0.03, 0, -0.62), (1.55, 0.2, 0.17, 0, -0.62), (0.2, 0.24, 0.2, 0, -0.65), (-1.0, 0.12, 0.1, 0, -0.6), (-1.3, 0.03, 0.03, 0, -0.55)], 12),
          lambda c, n: "Belly" if c.z < -0.7 else "Base", 1)
    for y in (0.9, -0.3):
        P.obj("Strut", box((0, y, -0.25), (0.05, 0.12, 0.55)), "Dark", 0, False)
    for s in (1, -1):
        P.obj("TipFloat", loft([(0.6, 0.02, 0.02, s * 2.25, -0.12), (0.4, 0.09, 0.08, s * 2.25, -0.12), (-0.2, 0.08, 0.06, s * 2.25, -0.12), (-0.35, 0.02, 0.02, s * 2.25, -0.12)], 10), "Base", 1)
        P.obj("TipStrut", box((s * 2.25, 0.15, 0.06), (0.04, 0.08, 0.32)), "Dark", 0, False)
        P.obj("Gun", tube(1.9, 2.5, 0.03, 0.03, s * 0.12, 0.68, 6), "Dark", 0)
    P.wing([(0.1, -1.85, -2.3, 0.06, 0.48), (0.95, -2.0, -2.25, 0.04, 0.48)], name="Stab")
    P.fin([(0.0, -1.55, -2.42, 0.07), (0.6, -1.9, -2.42, 0.05), (0.75, -2.08, -2.38, 0.04)], 0.0, 0.5, 0, "Accent")
    P.prop((0, 2.33, 0.3), 0.85, 3, spinner="Accent")
    return P


def B_soccer():
    """World 11, second: a jump jet (Harrier style) in red and white - huge side intakes, drooping wings, four swivel nozzles."""
    P = Plane("soccer2", {"Base": ((0.85, 0.10, 0.12), 0.5), "Belly": ((0.93, 0.93, 0.94), 0.5), "Accent": ((0.95, 0.95, 0.96), 0.5),
                          "Trim": ((0.08, 0.08, 0.09), 0.45), "Glass": ((0.22, 0.34, 0.46), 0.92), "Dark": ((0.06, 0.06, 0.07), 0.3),
                          "Glow": ((1.0, 0.55, 0.2), 0.5), "Metal": ((0.45, 0.45, 0.48), 0.6)})
    P.obj("Fuselage", loft([(2.6, 0.03, 0.03, 0, 0.0), (2.2, 0.17, 0.2, 0, 0.02), (1.4, 0.3, 0.38, 0, 0.05), (0.2, 0.45, 0.42, 0, 0.03),
                            (-1.0, 0.36, 0.34, 0, 0.05), (-2.3, 0.1, 0.14, 0, 0.18)], 16, sq=1.2),
          lambda c, n: "Accent" if c.z < -0.12 else ("Trim" if c.y > 2.35 else "Base"), 1)
    P.obj("Canopy", loft([(0.9, 0.04, 0.03, 0, 0.36), (1.2, 0.18, 0.17, 0, 0.44), (1.6, 0.18, 0.18, 0, 0.44), (1.95, 0.05, 0.04, 0, 0.32)], 12), "Glass", 1)
    for s in (1, -1):
        P.obj("Intake", loft([(1.0, 0.18, 0.28, s * 0.5, 0.06), (0.7, 0.22, 0.32, s * 0.52, 0.04), (-0.3, 0.16, 0.26, s * 0.42, 0.04)], 12, sq=1.3),
              lambda c, n: "Dark" if c.y > 0.95 else "Base", 1)
        for y in (0.3, -0.55):
            P.obj("Nozzle", loft([(y + 0.15, 0.13, 0.13, s * 0.58, -0.22), (y - 0.15, 0.13, 0.13, s * 0.58, -0.22)], 10), "Metal", 1)
            P.obj("Core", tube(y - 0.12, y - 0.17, 0.1, 0.03, s * 0.58, -0.22, 10), "Glow")
    P.wing([(0.35, 0.15, -1.0, 0.12, 0.38), (1.3, -0.45, -1.2, 0.08, 0.22), (2.2, -0.95, -1.35, 0.05, 0.05)],
           lambda c, n: "Belly" if n.z < -0.3 else ("Accent" if abs(c.x) > 1.95 else "Base"))
    P.wing([(0.2, -1.8, -2.35, 0.06, 0.15), (1.05, -2.15, -2.4, 0.04, 0.05)], name="Stab")
    P.fin([(0.0, -1.45, -2.4, 0.08), (0.75, -1.85, -2.45, 0.06), (0.9, -2.0, -2.45, 0.04)], 0.0, 0.3, 0, lambda c, n: "Accent" if c.z > 1.05 else "Base")
    return P


def B_shuttle():
    """World 12, second: a little space-plane (orbiter style) - white on top, black belly and nose, a double-delta wing, one tall fin, three engines."""
    P = Plane("shuttle2", {"Base": ((0.93, 0.93, 0.94), 0.5), "Belly": ((0.07, 0.07, 0.08), 0.4), "Accent": ((0.07, 0.07, 0.08), 0.4),
                           "Trim": ((0.95, 0.45, 0.12), 0.5), "Glass": ((0.12, 0.15, 0.2), 0.95), "Dark": ((0.05, 0.05, 0.06), 0.3),
                           "Glow": ((0.5, 0.75, 1.0), 0.5), "Metal": ((0.55, 0.56, 0.6), 0.6)})
    P.obj("Fuselage", loft([(2.6, 0.04, 0.04, 0, -0.05), (2.35, 0.24, 0.22, 0, 0.0), (1.8, 0.4, 0.38, 0, 0.05), (0.5, 0.45, 0.44, 0, 0.08),
                            (-1.6, 0.45, 0.44, 0, 0.08), (-2.0, 0.42, 0.4, 0, 0.1)], 16, sq=1.3),
          lambda c, n: "Belly" if c.z < -0.12 or c.y > 2.2 else "Base", 1)
    P.obj("Canopy", hull([(0.2, 1.9, 0.38), (-0.2, 1.9, 0.38), (0.25, 1.55, 0.48), (-0.25, 1.55, 0.48), (0, 2.1, 0.28), (0.3, 1.5, 0.35), (-0.3, 1.5, 0.35)]), "Glass", 0, False)
    P.wing([(0.4, 1.4, -1.9, 0.1, -0.22), (0.95, 0.0, -1.95, 0.08, -0.25), (1.8, -1.2, -1.95, 0.06, -0.28), (2.2, -1.65, -1.95, 0.04, -0.28)],
           lambda c, n: "Belly" if n.z < -0.3 or n.y > 0.7 else "Base")
    P.fin([(0.0, -0.95, -2.0, 0.1), (1.0, -1.55, -2.05, 0.07), (1.3, -1.8, -2.05, 0.05)], 0.0, 0.4, 0, lambda c, n: "Trim" if c.z > 1.45 else "Base")
    for (x, z) in ((0.0, 0.32), (0.24, -0.08), (-0.24, -0.08)):
        P.obj("Bell", loft([(-1.95, 0.12, 0.12, x, z), (-2.35, 0.19, 0.19, x, z)], 12, cs=True, ce=False), "Metal", 0)
        P.obj("Core", tube(-2.2, -2.3, 0.15, 0.05, x, z, 12), "Glow")
    return P


def B_treasure():
    """World 13, second: a gyrocopter gunship - a red-and-gold pod with a pusher prop, a free-spinning rotor on a mast, twin guns, a tail boom."""
    P = Plane("treasure2", {"Base": ((0.55, 0.10, 0.08), 0.45), "Belly": ((0.25, 0.08, 0.06), 0.4), "Accent": ((0.92, 0.70, 0.20), 0.65),
                            "Trim": ((0.10, 0.10, 0.10), 0.4), "Glass": ((0.5, 0.72, 0.82), 0.92), "Dark": ((0.06, 0.06, 0.07), 0.3),
                            "Glow": ((1.0, 0.6, 0.2), 0.5), "Metal": ((0.6, 0.55, 0.45), 0.7)})
    P.obj("Pod", loft([(1.6, 0.05, 0.06, 0, 0.0), (1.35, 0.3, 0.32, 0, 0.0), (0.6, 0.42, 0.45, 0, 0.03), (-0.3, 0.38, 0.4, 0, 0.05), (-0.75, 0.2, 0.22, 0, 0.08)], 14),
          lambda c, n: "Accent" if -0.05 < c.z < 0.05 else ("Belly" if c.z < -0.2 else "Base"), 1)
    P.obj("Screen", loft([(0.6, 0.3, 0.06, 0, 0.42), (1.05, 0.26, 0.1, 0, 0.3), (1.25, 0.12, 0.06, 0, 0.18)], 12, sq=1.3), "Glass", 1)
    P.obj("Mast", box((0, -0.2, 0.72), (0.12, 0.2, 0.75)), "Metal", 0, False)
    P.obj("Boom", tube(-0.6, -2.4, 0.07, 0.05, 0, 0.35, 8), "Metal", 0)
    P.obj("Engine", loft([(-0.55, 0.22, 0.22, 0, 0.22), (-0.95, 0.24, 0.24, 0, 0.22), (-1.15, 0.14, 0.14, 0, 0.22)], 12), "Accent", 1)
    P.fin([(0.0, -2.0, -2.6, 0.06), (0.75, -2.3, -2.7, 0.05), (0.85, -2.45, -2.7, 0.04)], 0.0, 0.25, 0, lambda c, n: "Accent" if c.z > 0.9 else "Base")
    P.wing([(0.05, -2.15, -2.6, 0.05, 0.35), (0.75, -2.25, -2.6, 0.04, 0.35)], name="Stab")
    P.wing([(0.35, 0.3, -0.15, 0.07, -0.18), (0.95, 0.25, -0.1, 0.05, -0.2)], name="Stub")
    for s in (1, -1):
        P.obj("Gun", tube(0.1, 1.4, 0.04, 0.035, s * 0.85, -0.24, 8), "Dark", 0)
        P.obj("Wheel", lathe([(0.0, -0.05), (0.15, -0.05), (0.17, 0.0), (0.15, 0.05), (0.0, 0.05)], 10, "x", (s * 0.45, 0.1, -0.62)), "Dark", 0)
        P.obj("Leg", box((s * 0.35, 0.1, -0.45), (0.04, 0.05, 0.32)), "Metal", 0, False)
    P.prop((0, -1.25, 0.22), 0.7, 3, blade="Dark", tip="Accent", spinner="Accent", spinner_len=0.2)
    P.prop((0, -0.2, 1.12), 1.85, 2, axis="z", chord=0.17, blade="Dark", tip="Accent", spinner="Metal", spinner_len=0.15, name="Rotor")
    return P


def B_west():
    """World 14, second: a trimotor bomber (Ford Trimotor style) - a boxy silver body, a thick high wing, three radial engines, fixed wheels."""
    P = Plane("west2", {"Base": ((0.66, 0.66, 0.64), 0.55), "Belly": ((0.52, 0.52, 0.5), 0.5), "Accent": ((0.62, 0.18, 0.10), 0.45),
                        "Trim": ((0.93, 0.72, 0.18), 0.5), "Glass": ((0.4, 0.5, 0.55), 0.92), "Dark": ((0.07, 0.07, 0.07), 0.3),
                        "Glow": ((1.0, 0.55, 0.2), 0.5), "Metal": ((0.5, 0.5, 0.5), 0.7)})
    P.obj("Fuselage", loft([(2.0, 0.3, 0.34, 0, -0.05), (1.6, 0.4, 0.48, 0, 0.0), (0.0, 0.42, 0.5, 0, 0.02), (-1.2, 0.28, 0.38, 0, 0.1), (-2.5, 0.06, 0.1, 0, 0.22)], 14, sq=1.8),
          lambda c, n: "Accent" if -0.1 < c.z < 0.0 else ("Belly" if c.z < -0.3 else "Base"), 1)
    for k in range(4):
        for s in (1, -1):
            P.obj("Window", box((s * 0.43, 0.9 - k * 0.42, 0.15), (0.02, 0.24, 0.16)), "Glass", 0, False)
    P.obj("Windscreen", box((0, 1.7, 0.42), (0.6, 0.04, 0.16), Matrix.Rotation(math.radians(-35), 3, "X")), "Glass", 0, False)
    P.obj("Wing", sweep([(x, airfoil(1.25, 0.05, 0.22 - abs(x) * 0.03, 0.62)) for x in (-3.0, -2.7, -0.3, 0.3, 2.7, 3.0)], "x"),
          lambda c, n: "Belly" if n.z < -0.3 else ("Accent" if abs(c.x) > 2.75 else "Base"), 1)
    def radial(x, y, z):
        P.obj("Cowl", lathe([(0.2, y + 0.05), (0.27, y - 0.05), (0.27, y - 0.3), (0.18, y - 0.45)], 14, "y", (x, 0, z)), "Dark", 0)
        P.obj("Cyl", lathe([(0.0, y + 0.02), (0.19, y + 0.0)], 14, "y", (x, 0, z)), "Metal", 0)
        P.prop((x, y + 0.08, z), 0.62, 2, blade="Dark", tip="Trim", spinner="Trim", spinner_len=0.15)
    P.obj("NoseMount", loft([(2.0, 0.25, 0.25, 0, 0.0), (2.15, 0.22, 0.22, 0, 0.0)], 12), "Base", 0)
    radial(0, 2.2, 0.0)
    for s in (1, -1):
        x = s * 1.3
        P.obj("Nacelle", loft([(1.0, 0.18, 0.18, x, 0.15), (0.2, 0.15, 0.15, x, 0.17), (-0.4, 0.06, 0.06, x, 0.2)], 10), "Base", 1)
        P.obj("Strut", box((s * 0.85, 0.75, 0.32), (0.85, 0.05, 0.05), Matrix.Rotation(math.radians(s * 22), 3, "Y")), "Metal", 0, False)
        radial(x, 1.1, 0.15)
        P.obj("Leg", box((s * 0.75, 0.6, -0.6), (0.05, 0.06, 0.55), Matrix.Rotation(math.radians(s * 25), 3, "Y")), "Metal", 0, False)
        P.obj("Wheel", lathe([(0.0, -0.06), (0.2, -0.06), (0.24, 0.0), (0.2, 0.06), (0.0, 0.06)], 12, "x", (s * 0.95, 0.6, -0.85)), "Dark", 0)
    P.wing([(0.1, -2.0, -2.55, 0.07, 0.25), (1.2, -2.1, -2.5, 0.05, 0.25)], name="Stab")
    P.fin([(0.0, -1.85, -2.6, 0.08), (0.75, -2.1, -2.6, 0.06), (0.85, -2.25, -2.55, 0.05)], 0.0, 0.3, 0, lambda c, n: "Accent" if c.z > 0.9 else "Base")
    return P
