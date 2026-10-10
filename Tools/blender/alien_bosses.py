# Sky Squad, the alien world's five bosses (2026-10-10: "new bosses for Alien, cancel the ones it has - vehicles, a flying space dragon,
# a flying saucer with someone on it shooting - legendary, five bosses only"). Built from code like the enemy planes (enemy_planes.py lends
# its helpers): the saucer gunner, the xeno hover tank, the void dragon, the space kraken and the overlord's mothership.
# Run: blender -b -P Tools/blender/alien_bosses.py -- <out dir> [export] [ids,comma,separated]
#      writes Boss_<id>.fbx per boss (with "export") and two previews each (prev_<id>_front.png, the player's view, and prev_<id>_34.png).
# Same axes as the planes: +Y = nose (toward the player), +Z = up, +X = right. "Body" is everything that does not move; the moving parts are
# their own objects with the origin on their hinge, and SceneBuilder.AlienBosses.cs reads the name: "Spin*" turns slowly about up, "Flap*"
# rocks about the nose axis (a wing), "Sway*" swings about the wing axis (a tentacle), "Muzzle" is the glowing point his shots leave from.
import bpy, bmesh, math, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mathutils import Vector, Matrix
import enemy_planes as EP
from enemy_planes import loft, sweep, lathe, box, hull, tube, mirror_x

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = argv[0] if argv else os.getcwd()
EXPORT = len(argv) > 1 and argv[1] == "export"
ONLY = argv[2].split(",") if len(argv) > 2 and argv[2] else None


# ================================================================= more shapes
def xf(bm, m=None, t=(0, 0, 0)):
    for v in bm.verts:
        if m is not None: v.co = m @ v.co
        v.co += Vector(t)
    return bm

def ball(c, r, seg=14, rings=8):
    """an ellipsoid with radii r = (rx, ry, rz) about c."""
    prof = [(math.sin(math.pi * i / rings), -math.cos(math.pi * i / rings)) for i in range(rings + 1)]
    bm = lathe([(p[0] if 0 < i < rings else 0.0, p[1]) for i, p in enumerate(prof)], seg, "z")
    for v in bm.verts: v.co = Vector((v.co.x * r[0], v.co.y * r[1], v.co.z * r[2])) + Vector(c)
    return bm

def frame(tan):
    t = tan.normalized()
    up = Vector((0, 0, 1)) if abs(t.z) < 0.9 else Vector((1, 0, 0))
    a = t.cross(up).normalized(); b = a.cross(t).normalized()
    return a, b

def pipe(pts, radii, seg=10, cap=True):
    """a tube through pts (rings square to the path), radius per point; a radius of 0 closes to a point."""
    pts = [Vector(p) for p in pts]
    bm = bmesh.new(); rings = []
    for i, p in enumerate(pts):
        tan = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)])
        a, b = frame(tan); r = radii[i]
        if r < 1e-5: rings.append([bm.verts.new(p)])
        else: rings.append([bm.verts.new(p + (a * math.cos(2 * math.pi * k / seg) + b * math.sin(2 * math.pi * k / seg)) * r) for k in range(seg)])
    for r0, r1 in zip(rings, rings[1:]):
        if len(r0) == 1 and len(r1) == 1: continue
        if len(r0) == 1:
            for k in range(seg): bm.faces.new((r0[0], r1[k], r1[(k + 1) % seg]))
        elif len(r1) == 1:
            for k in range(seg): bm.faces.new((r0[k], r1[0], r0[(k + 1) % seg]))
        else:
            for k in range(seg): bm.faces.new((r0[k], r0[(k + 1) % seg], r1[(k + 1) % seg], r1[k]))
    if cap and len(rings[0]) > 1: bm.faces.new(list(reversed(rings[0])))
    if cap and len(rings[-1]) > 1: bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm

def cone(base, tip, r, seg=8):
    return pipe([base, tip], [r, 0.0], seg)

def bez(p0, p1, p2, p3, n):
    P = [Vector(p) for p in (p0, p1, p2, p3)]
    out = []
    for i in range(n + 1):
        t = i / n; u = 1 - t
        out.append(P[0] * u ** 3 + P[1] * 3 * u * u * t + P[2] * 3 * u * t * t + P[3] * t ** 3)
    return out

def torus(R, r, z=0.0, seg=40, sides=8):
    bm = bmesh.new(); rings = []
    for i in range(seg):
        a = 2 * math.pi * i / seg; ca, sa = math.cos(a), math.sin(a)
        rings.append([bm.verts.new(((R + r * math.cos(2 * math.pi * k / sides)) * ca, (R + r * math.cos(2 * math.pi * k / sides)) * sa, z + r * math.sin(2 * math.pi * k / sides))) for k in range(sides)])
    for i in range(seg):
        r0, r1 = rings[i], rings[(i + 1) % seg]
        for k in range(sides): bm.faces.new((r0[k], r0[(k + 1) % sides], r1[(k + 1) % sides], r1[k]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm

def sheet(polys, thick=0.03):
    """flat polygons (lists of points) made two-sided: the top as given, a copy under it facing down."""
    bm = bmesh.new()
    for poly in polys:
        top = [bm.verts.new(Vector(p) + Vector((0, 0, thick * 0.5))) for p in poly]
        bot = [bm.verts.new(Vector(p) - Vector((0, 0, thick * 0.5))) for p in poly]
        f = bm.faces.new(top); g = bm.faces.new(list(reversed(bot)))
        f.normal_update(); g.normal_update()
        if f.normal.z < 0: bmesh.ops.reverse_faces(bm, faces=[f, g])
    return bm

def grow(bm, c, k):
    """scaled k times about the point c."""
    for v in bm.verts: v.co = (v.co - Vector(c)) * k + Vector(c)
    return bm

def ang(c):
    return math.atan2(c.x, c.y)


# ================================================================= a boss being built
class Boss(EP.Plane):
    def part(self, name, bm, paint, hub, ss=0, smooth=True):
        """a moving part (or a piece of one: pieces with the same name are joined) with its origin on the hub."""
        return self.obj(name, bm, paint, ss, smooth, spin=hub)

    def finish(self):
        bpy.ops.object.select_all(action="DESELECT")
        for p in self.parts: p.select_set(True)
        bpy.context.view_layer.objects.active = self.parts[0]
        bpy.ops.object.join()
        body = bpy.context.view_layer.objects.active
        body.name = "Body"; body.data.name = self.id + "_Body"
        groups = {}
        for s in self.spin: groups.setdefault(s.name.split(".")[0], []).append(s)
        movers = []
        for name, objs in groups.items():
            if len(objs) > 1:
                bpy.ops.object.select_all(action="DESELECT")
                for o in objs: o.select_set(True)
                bpy.context.view_layer.objects.active = objs[0]
                bpy.ops.object.join()
            o = bpy.context.view_layer.objects.active if len(objs) > 1 else objs[0]
            o.name = name; o.data.name = self.id + "_" + name
            movers.append(o)
        self.spin = movers
        pts = [body.matrix_world @ v.co for v in body.data.vertices]
        for s in self.spin: pts += [s.matrix_world @ v.co for v in s.data.vertices]
        lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
        hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
        c = (lo + hi) * 0.5
        body.data.transform(Matrix.Translation(-c))
        for s in self.spin: s.location -= c
        tris = sum(len(p.vertices) - 2 for p in body.data.polygons) + sum(sum(len(p.vertices) - 2 for p in s.data.polygons) for s in self.spin)
        print("BOSS", self.id, "tris", tris, "size", tuple(round(d, 2) for d in (hi - lo)), "movers", [s.name for s in self.spin])
        self.body = body; self.size = hi - lo
        if EXPORT:
            bpy.ops.object.select_all(action="DESELECT")
            body.select_set(True)
            for s in self.spin: s.select_set(True)
            bpy.ops.export_scene.fbx(filepath=os.path.join(OUT, "Boss_" + self.id + ".fbx"), use_selection=True, object_types={"MESH"},
                                     apply_scale_options="FBX_SCALE_UNITS", axis_forward="Z", axis_up="Y", bake_space_transform=True,
                                     mesh_smooth_type="FACE", use_mesh_modifiers=True, add_leaf_bones=False)
        self.preview()

    def preview(self):
        scene = bpy.context.scene
        scene.view_settings.view_transform = "Standard"
        world = bpy.data.worlds.new("W"); scene.world = world; world.use_nodes = True
        bg = next(n for n in world.node_tree.nodes if n.type == "BACKGROUND")
        bg.inputs[0].default_value = (0.20, 0.16, 0.38, 1); bg.inputs[1].default_value = 0.9
        sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN")); scene.collection.objects.link(sun)
        sun.data.energy = 3.4; sun.rotation_euler = (math.radians(40), math.radians(15), math.radians(150))
        try: scene.render.engine = "BLENDER_EEVEE_NEXT"
        except TypeError:
            try: scene.render.engine = "BLENDER_EEVEE"
            except TypeError: pass
        try:
            scene.eevee.use_bloom = True
        except Exception: pass
        scene.render.resolution_x = 480; scene.render.resolution_y = 360
        cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam")); scene.collection.objects.link(cam); scene.camera = cam
        cam.data.lens = 50
        d = max(self.size.x, self.size.y, self.size.z) * 3.2
        def shot(fn, loc):
            cam.location = loc
            cam.rotation_euler = (Vector((0, 0, 0)) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
            scene.render.filepath = os.path.join(OUT, fn)
            bpy.ops.render.render(write_still=True)
        shot("prev_%s_front.png" % self.id, (0, d * 0.95, d * 0.32))   # the player's view: he comes at you, seen a little from above
        shot("prev_%s_34.png" % self.id, (d * 0.6, d * 0.6, d * 0.42))


# ================================================================= 1. the saucer gunner
def B_saucer():
    """A silver saucer with a spinning ring of lights, and on top, in an open turret, a green alien at a twin plasma cannon."""
    P = Boss("saucer", {"Base": ((0.66, 0.66, 0.78), 0.65), "Belly": ((0.20, 0.13, 0.34), 0.5), "Accent": ((0.85, 0.18, 0.66), 0.6),
                        "Trim": ((0.36, 0.86, 0.30), 0.5), "Glass": ((0.35, 0.92, 1.0), 0.95), "Dark": ((0.04, 0.04, 0.07), 0.5),
                        "Glow": ((0.20, 1.0, 0.85), 0.5), "Metal": ((0.52, 0.52, 0.62), 0.7), "Lamp": ((1.0, 0.25, 0.80), 0.8)})
    disc = lathe([(0.0, -0.40), (0.55, -0.38), (1.15, -0.28), (1.65, -0.10), (1.88, 0.0), (1.72, 0.10), (1.30, 0.20), (0.90, 0.27), (0.0, 0.29)], 40, "z")
    P.obj("Disc", disc, lambda c, n: "Belly" if c.z < -0.06 else ("Accent" if math.hypot(c.x, c.y) > 1.6 else "Base"))
    # panel lines on the top: eight dark spokes
    for k in range(8):
        a = 2 * math.pi * (k + 0.5) / 8
        P.obj("Spoke", box((math.sin(a) * 1.15, math.cos(a) * 1.15, 0.215), (0.05, 0.75, 0.03), Matrix.Rotation(-a, 3, "Z") @ Matrix.Rotation(math.radians(9), 3, "X")), "Dark", 0, False)
    # the ring of lights round the rim: it turns
    for k in range(16):
        a = 2 * math.pi * k / 16
        P.part("SpinRim", ball((math.sin(a) * 1.8, math.cos(a) * 1.8, 0.02), (0.1, 0.1, 0.08), 8, 5), "Glow" if k % 2 == 0 else "Lamp", (0, 0, 0))
    # underneath: the tractor emitter and three pods
    P.obj("Emitter", lathe([(0.0, -0.62), (0.32, -0.56), (0.5, -0.40)], 20, "z"), "Glow")
    for k in range(3):
        a = 2 * math.pi * k / 3 + math.pi / 3
        P.obj("Pod", ball((math.sin(a) * 1.05, math.cos(a) * 1.05, -0.36), (0.24, 0.24, 0.13), 12, 6), lambda c, n: "Glow" if c.z < -0.44 else "Metal")
    # the turret well: a raised collar the gunner stands in
    P.obj("Collar", lathe([(0.82, 0.25), (0.86, 0.44), (0.76, 0.52), (0.64, 0.46), (0.62, 0.30)], 28, "z"), lambda c, n: "Accent" if c.z > 0.47 else "Metal")
    P.obj("Floor", lathe([(0.0, 0.40), (0.64, 0.40)], 20, "z"), "Dark")
    for s in (1, -1):
        P.obj("Headlamp", ball((s * 0.55, 1.55, 0.06), (0.14, 0.08, 0.06), 10, 5), "Lamp")
    P.obj("RearDome", ball((0, -1.05, 0.24), (0.42, 0.36, 0.26), 14, 7), "Glass")
    # the gunner: a green alien, big head, huge glowing eyes, antennae
    gx, gy = 0.0, -0.18
    P.obj("Suit", ball((gx, gy, 0.74), (0.30, 0.22, 0.34), 14, 8), lambda c, n: "Accent" if 0.85 < c.z < 0.93 else "Belly")
    P.obj("Badge", ball((gx, gy + 0.21, 0.80), (0.08, 0.03, 0.08), 8, 4), "Glow")
    P.obj("Neck", pipe([(gx, gy, 1.0), (gx, gy + 0.02, 1.12)], [0.09, 0.08], 10), "Trim")
    P.obj("Head", lathe([(0.0, -0.32), (0.12, -0.29), (0.20, -0.18), (0.28, 0.02), (0.33, 0.18), (0.30, 0.31), (0.18, 0.40), (0.0, 0.43)], 18, "z", (gx, gy + 0.03, 1.38)), "Trim")
    for s in (1, -1):
        eye = ball((0, 0, 0), (0.115, 0.06, 0.16), 12, 6)
        xf(eye, Matrix.Rotation(math.radians(-s * 28), 3, "Y"), (gx + s * 0.135, gy + 0.29, 1.38))
        P.obj("Eye", eye, "Lamp")
        P.obj("Antenna", pipe(bez((gx + s * 0.1, gy, 1.76), (gx + s * 0.15, gy - 0.05, 1.98), (gx + s * 0.3, gy - 0.1, 2.05), (gx + s * 0.36, gy - 0.12, 2.12), 5), [0.03, 0.026, 0.022, 0.02, 0.018, 0.016], 6), "Trim")
        P.obj("AntennaTip", ball((gx + s * 0.37, gy - 0.12, 2.15), (0.06, 0.06, 0.06), 8, 4), "Glow")
        # arms reaching for the grips of the gun
        sh = (gx + s * 0.27, gy + 0.02, 0.92); el = (gx + s * 0.36, gy + 0.22, 0.72); hd = (gx + s * 0.2, gy + 0.5, 0.80)
        P.obj("Arm", pipe([sh, el], [0.065, 0.055], 8), "Trim")
        P.obj("Arm", pipe([el, hd], [0.055, 0.045], 8), "Trim")
        P.obj("Hand", ball(hd, (0.07, 0.07, 0.06), 8, 4), "Trim")
    # the gun: a swivel post, the breech, twin barrels with glowing coils, a glowing emitter at the end
    P.obj("Post", pipe([(0, 0.35, 0.4), (0, 0.42, 0.72)], [0.09, 0.08], 10), "Metal")
    P.obj("Breech", box((0, 0.55, 0.82), (0.42, 0.55, 0.24)), lambda c, n: "Accent" if n.z > 0.5 else "Metal", 0, False)
    for s in (1, -1):
        P.obj("Barrel", pipe([(s * 0.11, 0.8, 0.84), (s * 0.11, 1.85, 0.84)], [0.07, 0.06], 10), "Dark")
        for k in range(3):
            P.obj("Coil", pipe([(s * 0.11, 1.05 + k * 0.25, 0.84), (s * 0.11, 1.13 + k * 0.25, 0.84)], [0.095, 0.095], 10), "Glow")
        P.obj("Grip", box((s * 0.2, 0.5, 0.74), (0.05, 0.08, 0.16)), "Dark", 0, False)
    P.obj("Brace", box((0, 1.82, 0.84), (0.36, 0.08, 0.1)), "Metal", 0, False)
    P.part("Muzzle", ball((0, 1.95, 0.84), (0.13, 0.1, 0.13), 10, 5), "Glow", (0, 1.95, 0.84))
    return P


# ================================================================= 2. the xeno hover tank
def B_tank():
    """An armoured alien hover tank: a wedge hull with bone tusks, four spinning anti-grav pods, a domed turret with a long rail cannon."""
    P = Boss("tank", {"Base": ((0.10, 0.34, 0.36), 0.55), "Belly": ((0.04, 0.12, 0.14), 0.45), "Accent": ((0.62, 1.0, 0.22), 0.6),
                      "Trim": ((0.80, 0.82, 0.70), 0.5), "Glass": ((0.55, 1.0, 0.35), 0.95), "Dark": ((0.03, 0.05, 0.05), 0.4),
                      "Glow": ((0.40, 1.0, 0.20), 0.5), "Metal": ((0.40, 0.50, 0.52), 0.7), "Lamp": ((1.0, 0.25, 0.70), 0.8)})
    pts = []
    for s in (1, -1):
        pts += [(s * 0.45, 1.75, -0.05), (s * 0.95, 1.15, -0.28), (s * 0.9, 1.15, 0.22), (s * 1.12, -1.35, -0.28), (s * 1.05, -1.35, 0.36),
                (s * 0.62, -1.7, 0.30), (s * 0.62, -1.7, -0.22), (s * 0.55, 0.85, 0.48), (s * 0.62, -1.15, 0.58)]
    pts += [(0, 1.85, 0.02)]
    P.obj("Hull", hull(pts), lambda c, n: "Belly" if n.z < -0.4 else ("Accent" if n.y > 0.55 and c.z > 0.05 else "Base"), 0, False)
    for s in (1, -1):
        P.obj("Vent", box((s * 1.1, -0.2, 0.05), (0.03, 1.6, 0.06)), "Glow", 0, False)
        P.obj("Tusk", pipe(bez((s * 0.45, 1.5, -0.12), (s * 0.55, 1.95, -0.2), (s * 0.45, 2.2, -0.15), (s * 0.3, 2.3, -0.02), 5), [0.11, 0.1, 0.08, 0.06, 0.03, 0.0], 8), "Trim")
        P.obj("Exhaust", pipe([(s * 0.5, -1.62, 0.1), (s * 0.5, -1.8, 0.1)], [0.18, 0.16], 12), "Metal")
        P.obj("ExhaustCore", pipe([(s * 0.5, -1.79, 0.1), (s * 0.5, -1.83, 0.1)], [0.14, 0.04], 12), "Glow")
        P.obj("Fin", hull([(s * 0.6, -0.9, 0.5), (s * 0.6, -1.5, 0.35), (s * 0.95, -1.55, 1.05), (s * 0.64, -1.0, 0.5)]), "Accent", 0, False)
        for t in (1, -1):
            hx, hy, hz = s * 1.35, t * 1.0 - 0.15, -0.32
            P.obj("PodArm", box((s * 1.15, hy, -0.12), (0.5, 0.2, 0.12)), "Metal", 0, False)
            name = "SpinPod%d%d" % (1 if s > 0 else 0, 1 if t > 0 else 0)
            P.part(name, lathe([(0.0, -0.18), (0.42, -0.14), (0.5, -0.02), (0.4, 0.1), (0.0, 0.12)], 18, "z", (hx, hy, hz)), lambda c, n: "Glow" if c.z < hz - 0.12 else "Metal", (hx, hy, hz))
            for k in range(3):
                a = 2 * math.pi * k / 3
                P.part(name, box((hx + math.sin(a) * 0.36, hy + math.cos(a) * 0.36, hz + 0.14), (0.08, 0.3, 0.06), Matrix.Rotation(-a, 3, "Z")), "Accent", (hx, hy, hz), 0, False)
    # the turret
    P.obj("Turret", lathe([(0.78, 0.0), (0.75, 0.2), (0.58, 0.42), (0.3, 0.53), (0.0, 0.56)], 24, "z", (0, -0.35, 0.48)), lambda c, n: "Accent" if 0.62 < c.z < 0.68 else "Base")
    P.obj("Visor", ball((0, 0.28, 0.82), (0.36, 0.1, 0.1), 14, 6), "Glass")
    for s in (1, -1):
        P.obj("Rack", box((s * 0.85, -0.35, 0.72), (0.3, 0.6, 0.34)), lambda c, n: "Belly" if n.z < -0.4 else "Base", 0, False)
        for i in range(3):
            P.obj("Tube", pipe([(s * 0.85 + (i - 1) * 0.085, -0.05, 0.76), (s * 0.85 + (i - 1) * 0.085, -0.03, 0.76)], [0.04, 0.04], 8), "Lamp")
    # the rail cannon: two rails, a glowing core between them, gold collars, the muzzle at the end
    for s in (1, -1):
        P.obj("Rail", box((s * 0.17, 1.25, 0.82), (0.11, 2.4, 0.16)), lambda c, n: "Dark" if n.z < -0.4 else "Metal", 0, False)
    P.obj("Core", pipe([(0, 0.2, 0.82), (0, 2.38, 0.82)], [0.07, 0.07], 10), "Glow")
    for y in (0.75, 1.35, 1.95):
        P.obj("Collar", box((0, y, 0.82), (0.55, 0.12, 0.26)), "Accent", 0, False)
    P.part("Muzzle", ball((0, 2.5, 0.82), (0.16, 0.12, 0.16), 10, 5), "Glow", (0, 2.5, 0.82))
    return P


# ================================================================= 3. the void dragon
def B_dragon():
    """A space dragon: an indigo serpent with a horned head, an open glowing jaw, a row of crystals down his back, and great bat wings that beat."""
    P = Boss("dragon", {"Base": ((0.13, 0.10, 0.34), 0.55), "Belly": ((0.58, 0.46, 0.80), 0.45), "Accent": ((0.42, 0.14, 0.72), 0.5),
                        "Trim": ((0.88, 0.84, 0.70), 0.5), "Glass": ((0.35, 0.95, 1.0), 0.95), "Dark": ((0.04, 0.02, 0.07), 0.4),
                        "Glow": ((0.25, 0.95, 1.0), 0.5), "Metal": ((0.40, 0.40, 0.50), 0.6), "Lamp": ((1.0, 0.30, 0.85), 0.8)})
    spine = bez((0, 1.55, 0.72), (0, 0.9, 0.05), (0, -0.4, 0.15), (0.0, -0.9, 0.05), 6) + bez((0.0, -0.9, 0.05), (0.45, -1.5, -0.05), (0.5, -2.0, 0.1), (-0.2, -2.45, 0.35), 6)[1:]
    radii = [0.15, 0.2, 0.27, 0.33, 0.36, 0.35, 0.3, 0.25, 0.2, 0.15, 0.11, 0.07, 0.04]
    P.obj("Body", pipe(spine, radii, 14), lambda c, n: "Belly" if n.z < -0.35 else "Base", 1)
    tip = spine[-1]
    P.obj("TailBlade", hull([tip + Vector((0, 0.1, 0)), tip + Vector((-0.35, -0.35, 0.25)), tip + Vector((0.1, -0.45, 0.05)), tip + Vector((-0.05, -0.1, 0.3)), tip + Vector((0, 0.05, -0.05))]), "Glass", 0, False)
    # the crystals down his back
    for i in range(1, 11):
        p = spine[i]; r = radii[i]
        h = 0.42 * (1 - abs(i - 4) / 9.0) + 0.08
        P.obj("Crystal", cone(p + Vector((0, 0, r * 0.75)), p + Vector((0, -h * 0.55, r * 0.75 + h)), 0.07 + r * 0.12, 5), "Glass", 0, False)
    # the head: skull and snout, the open lower jaw, a glowing throat, eyes, teeth and horns
    HC, HK = (0, 1.45, 0.78), 1.3   # the head is drawn 1.3 times bigger about the top of the neck
    P.obj("Skull", grow(loft([(1.45, 0.17, 0.17, 0, 0.80), (1.72, 0.23, 0.2, 0, 0.86), (1.98, 0.2, 0.14, 0, 0.84), (2.28, 0.13, 0.09, 0, 0.79), (2.5, 0.06, 0.05, 0, 0.76)], 14), HC, HK),
          lambda c, n: "Accent" if n.z > 0.6 and c.y < 1.9 else "Base", 1)
    P.obj("Jaw", grow(loft([(1.55, 0.15, 0.07, 0, 0.64), (1.95, 0.14, 0.05, 0, 0.58), (2.3, 0.08, 0.035, 0, 0.53), (2.42, 0.03, 0.02, 0, 0.52)], 12), HC, HK),
          lambda c, n: "Belly" if n.z < -0.2 else "Base", 1)
    P.obj("Throat", grow(ball((0, 1.95, 0.71), (0.11, 0.32, 0.06), 12, 6), HC, HK), "Glow")
    for s in (1, -1):
        P.obj("Eye", grow(ball((s * 0.15, 1.86, 0.93), (0.06, 0.1, 0.045), 10, 5), HC, HK), "Lamp")
        P.obj("Brow", grow(cone((s * 0.13, 1.8, 0.98), (s * 0.2, 1.98, 0.97), 0.05, 6), HC, HK), "Trim")
        P.obj("Horn", grow(pipe(bez((s * 0.12, 1.62, 0.95), (s * 0.22, 1.4, 1.2), (s * 0.35, 1.15, 1.35), (s * 0.42, 0.95, 1.55), 5), [0.075, 0.065, 0.05, 0.035, 0.02, 0.0], 8), HC, HK), "Trim")
        P.obj("Horn", grow(pipe(bez((s * 0.19, 1.58, 0.8), (s * 0.38, 1.35, 0.85), (s * 0.5, 1.15, 0.95), (s * 0.58, 1.0, 1.05), 4), [0.05, 0.04, 0.03, 0.015, 0.0], 6), HC, HK), "Trim")
        for k in range(4):
            y = 1.85 + k * 0.13
            P.obj("Tooth", grow(cone((s * (0.15 - k * 0.025), y, 0.73), (s * (0.14 - k * 0.025), y + 0.02, 0.63), 0.025, 5), HC, HK), "Trim", 0, False)
            P.obj("Tooth", grow(cone((s * (0.13 - k * 0.025), y, 0.6), (s * (0.12 - k * 0.025), y + 0.02, 0.68), 0.022, 5), HC, HK), "Trim", 0, False)
        # legs, folded under him, with claws
        for (y0, z0) in ((0.45, -0.05), (-0.7, -0.15)):
            hip = Vector((s * 0.22, y0, z0)); knee = Vector((s * 0.4, y0 + 0.15, z0 - 0.3)); foot = Vector((s * 0.36, y0 + 0.3, z0 - 0.5))
            P.obj("Leg", pipe([hip, knee, foot], [0.11, 0.08, 0.06], 8), lambda c, n: "Belly" if n.z < -0.3 else "Base")
            for k in (-1, 0, 1):
                P.obj("Claw", cone(foot, foot + Vector((s * 0.05 + k * 0.07, 0.15, -0.1)), 0.03, 5), "Trim", 0, False)
        # the wing: arm and fingers in bone, a purple membrane with a scalloped edge, the wrist claw; it beats about the shoulder
        sh = Vector((s * 0.28, 0.4, 0.38)); wr = Vector((s * 0.95, 0.5, 1.3))
        tips = [Vector((s * 1.8, 0.2, 2.05)), Vector((s * 2.15, -0.3, 1.6)), Vector((s * 2.0, -0.75, 1.05)), Vector((s * 1.4, -0.95, 0.55))]
        root = Vector((s * 0.3, -0.75, 0.22))
        name = "FlapL" if s < 0 else "FlapR"
        P.part(name, pipe([sh, wr], [0.09, 0.06], 8), "Base", tuple(sh))
        for t in tips: P.part(name, pipe([wr, t], [0.045, 0.012], 6), "Base", tuple(sh))
        P.part(name, cone(wr, wr + Vector((s * 0.05, 0.25, 0.12)), 0.045, 5), "Trim", tuple(sh), 0, False)
        polys = [[sh, wr, tips[0]]]
        chain = tips + [root]
        for a, b in zip(chain, chain[1:]):
            mid = (a + b) * 0.5; mid = mid + (wr - mid) * 0.22   # the scallop between two fingers
            polys.append([wr, a, mid]); polys.append([wr, mid, b])
        polys.append([wr, root, sh])
        P.part(name, sheet([[tuple(p) for p in poly] for poly in polys], 0.03), lambda c, n: "Accent", tuple(sh), 0, False)
    mz = Vector(HC) + (Vector((0, 2.5, 0.68)) - Vector(HC)) * HK
    P.part("Muzzle", ball(tuple(mz), (0.12, 0.1, 0.1), 8, 4), "Glow", tuple(mz))
    return P


# ================================================================= 4. the space kraken
def B_kraken():
    """A space kraken: a plum bell with glowing veins and an armoured collar with two plasma pods, one huge amber eye, and eight tentacles
    that hang down and curl toward the player, every one swaying on its own."""
    P = Boss("kraken", {"Base": ((0.46, 0.12, 0.42), 0.6), "Belly": ((0.92, 0.66, 0.80), 0.45), "Accent": ((0.20, 0.85, 0.75), 0.6),
                        "Trim": ((0.30, 0.32, 0.42), 0.6), "Glass": ((1.0, 0.78, 0.15), 0.95), "Dark": ((0.04, 0.02, 0.05), 0.5),
                        "Glow": ((0.20, 1.0, 0.85), 0.5), "Metal": ((0.55, 0.55, 0.64), 0.7), "Lamp": ((1.0, 0.45, 0.15), 0.8)})
    tilt = Matrix.Rotation(math.radians(-18), 3, "X")   # the bell leans back, away from the player
    bell = lathe([(0.0, 1.45), (0.38, 1.4), (0.78, 1.18), (1.08, 0.8), (1.22, 0.35), (1.18, 0.02), (1.0, -0.14), (0.6, -0.24), (0.0, -0.27)], 32, "z")
    xf(bell, tilt)
    def veins(c, n):
        if c.z < 0.0 and n.z < -0.2: return "Belly"
        f = (ang(c) / (2 * math.pi) * 10) % 1.0
        return "Glow" if f < 0.1 and c.z > 0.2 else "Base"
    P.obj("Bell", bell, veins, 1)
    for k in range(10):   # glowing spots between the veins
        a = 2 * math.pi * (k + 0.5) / 10
        p = tilt @ Vector((math.sin(a) * 0.95, math.cos(a) * 0.95, 0.95))
        P.obj("Spot", ball(tuple(p), (0.09, 0.09, 0.06), 8, 4), "Accent")
    collar = torus(1.2, 0.09, 0.08, 36, 8); xf(collar, tilt)
    P.obj("Collar", collar, "Trim")
    for s in (1, -1):
        base = tilt @ Vector((s * 1.12, 0.45, 0.1))
        P.obj("Pod", pipe([base + Vector((0, -0.3, 0)), base, base + Vector((0, 0.5, 0))], [0.16, 0.18, 0.14], 12), "Metal")
        P.obj("PodTip", ball(tuple(base + Vector((0, 0.56, 0))), (0.11, 0.07, 0.11), 10, 5), "Glow")
        P.obj("SideEye", ball(tuple(tilt @ Vector((s * 0.55, 1.0, 0.75))), (0.13, 0.08, 0.12), 10, 5), "Glass")
    # the great eye on the front
    P.obj("Eyeball", ball((0, 1.02, 0.35), (0.46, 0.22, 0.4), 18, 9), "Belly")
    P.obj("Iris", ball((0, 1.17, 0.35), (0.3, 0.1, 0.28), 16, 8), "Glass")
    P.obj("Pupil", ball((0, 1.25, 0.35), (0.06, 0.04, 0.22), 10, 5), "Dark")
    P.obj("LidTop", ball((0, 0.98, 0.62), (0.52, 0.26, 0.14), 16, 6), "Base")
    P.obj("LidLow", ball((0, 0.98, 0.07), (0.5, 0.24, 0.12), 16, 6), "Base")
    # eight tentacles: down, out, then curling forward; each its own part, hinged where it leaves the bell
    for k in range(8):
        a = 2 * math.pi * (k + 0.5) / 8
        out = Vector((math.sin(a), math.cos(a), 0))
        p0 = Vector((out.x * 0.62, out.y * 0.62, -0.18))
        front = 0.55 + 0.45 * max(0.0, out.y)   # the front ones reach further toward the player
        pts = bez(p0, p0 + out * 0.45 + Vector((0, 0, -0.55)), p0 + out * 0.7 + Vector((0, front * 0.6, -1.2)), p0 + out * 0.45 + Vector((0, front * 1.1, -1.05)), 8)
        rr = [0.17 - 0.155 * i / 8 for i in range(9)]
        name = "Sway%d" % k
        P.part(name, pipe(pts, rr, 10), lambda c, n, p0=p0: "Belly" if (c - p0).dot(Vector((0, 0, 1))) < -0.2 and n.dot(Vector((0, 1, 0))) > 0.3 else "Base", tuple(p0))
        for i in range(2, 8, 2):   # glowing suckers down the inside
            q = pts[i]; tq = (pts[i + 1] - pts[i - 1]).normalized()
            side = tq.cross(Vector((0, 0, 1)));
            inward = (tq.cross(side)).normalized() if side.length > 1e-3 else Vector((0, 1, 0))
            if inward.y < 0: inward = -inward
            P.part(name, ball(tuple(q + inward * rr[i] * 0.85), (0.045, 0.045, 0.045), 6, 3), "Glow", tuple(p0))
        P.part(name, ball(tuple(pts[-1]), (0.05, 0.05, 0.05), 6, 3), "Glow", tuple(p0))
    P.part("Muzzle", ball((0, 1.3, 0.35), (0.08, 0.04, 0.08), 8, 4), "Lamp", (0, 1.3, 0.35))
    return P


# ================================================================= 5. the overlord's mothership
def B_mothership():
    """The last boss: a great dark mothership with a gold rim and lit windows, a free ring of crystals turning round it, two cannon pods on
    pylons and a spinal cannon under the bow - and on top, on a golden throne, the alien overlord himself: a huge glowing brain, four eyes."""
    P = Boss("mothership", {"Base": ((0.20, 0.18, 0.30), 0.6), "Belly": ((0.09, 0.07, 0.14), 0.5), "Accent": ((0.95, 0.70, 0.20), 0.7),
                            "Trim": ((0.56, 0.46, 0.76), 0.45), "Glass": ((1.0, 0.32, 0.82), 0.95), "Dark": ((0.03, 0.03, 0.05), 0.5),
                            "Glow": ((0.88, 0.30, 1.0), 0.5), "Metal": ((0.60, 0.58, 0.66), 0.7), "Lamp": ((0.30, 1.0, 0.90), 0.8)})
    def hullpaint(c, n):
        r = math.hypot(c.x, c.y)
        if c.z < -0.05: return "Belly"
        if r > 1.93: return "Accent"
        if 0.17 < c.z < 0.26 and (ang(c) / (2 * math.pi) * 36) % 1.0 < 0.5: return "Lamp"   # the windows of the upper tier
        return "Base"
    P.obj("Hull", lathe([(0.0, -0.52), (0.8, -0.48), (1.6, -0.3), (2.0, -0.08), (2.06, 0.04), (1.75, 0.16), (1.3, 0.2), (1.25, 0.3), (1.15, 0.38), (0.0, 0.40)], 48, "z"), hullpaint)
    P.obj("Core", lathe([(0.0, -0.95), (0.42, -0.82), (0.62, -0.5)], 24, "z"), "Glow")
    for k in range(6):   # turrets round the upper tier
        a = 2 * math.pi * (k + 0.5) / 6
        c = Vector((math.sin(a) * 1.5, math.cos(a) * 1.5, 0.2))
        P.obj("Turret", lathe([(0.2, 0.0), (0.18, 0.12), (0.0, 0.18)], 10, "z", tuple(c)), "Metal")
        d = Vector((math.sin(a), math.cos(a), 0)) * 0.4 + Vector((0, 0.25, 0.04))
        P.obj("TurretGun", pipe([c + Vector((0, 0, 0.1)), c + Vector((0, 0, 0.1)) + d], [0.035, 0.03], 6), "Dark")
    # the free ring: it turns round the ship, eight crystals and eight lamps on it
    P.part("SpinRing", torus(2.42, 0.08, 0.0, 48, 8), "Metal", (0, 0, 0))
    for k in range(8):
        a = 2 * math.pi * k / 8
        c = Vector((math.sin(a) * 2.42, math.cos(a) * 2.42, 0.0))
        P.part("SpinRing", ball(tuple(c), (0.15, 0.15, 0.22), 6, 4), "Glass", (0, 0, 0), 0, False)
        a2 = a + math.pi / 8
        P.part("SpinRing", box((math.sin(a2) * 2.42, math.cos(a2) * 2.42, 0.0), (0.2, 0.08, 0.2), Matrix.Rotation(-a2, 3, "Z")), "Glow", (0, 0, 0), 0, False)
    # two cannon pods out on pylons, forward left and right
    for s in (1, -1):
        a = math.radians(s * 55)
        base = Vector((math.sin(a) * 1.7, math.cos(a) * 1.7, -0.05))
        P.obj("Pylon", hull([(base.x * 0.7, base.y * 0.7, 0.05), (base.x * 0.7, base.y * 0.7 - 0.3, 0.05), (base.x * 0.7, base.y * 0.7, -0.15),
                             (base.x, base.y + 0.1, 0.0), (base.x, base.y - 0.25, 0.0), (base.x, base.y, -0.2)]), "Accent", 0, False)
        P.obj("CannonPod", pipe([base + Vector((0, -0.5, 0)), base + Vector((0, -0.2, 0)), base + Vector((0, 0.55, 0))], [0.12, 0.22, 0.18], 12), "Metal")
        P.obj("CannonTip", ball(tuple(base + Vector((0, 0.62, 0))), (0.14, 0.08, 0.14), 10, 5), "Glow")
    # the spinal cannon under the bow
    P.obj("Spinal", pipe([(0, 0.9, -0.22), (0, 1.6, -0.22), (0, 2.3, -0.2)], [0.3, 0.24, 0.2], 14), "Metal")
    for y in (1.3, 1.75, 2.15):
        P.obj("SpinalRing", pipe([(0, y, -0.21), (0, y + 0.08, -0.21)], [0.29, 0.29], 14), "Accent")
    # the throne and the overlord (built at his first size, then made 1.3 times as big about the deck so he reads from the squad's low view)
    n0 = len(P.parts)
    P.obj("Dais", lathe([(0.75, 0.38), (0.7, 0.52), (0.0, 0.54)], 24, "z", (0, -0.15, 0)), "Accent")
    P.obj("ThroneBack", hull([(-0.55, -0.62, 0.52), (0.55, -0.62, 0.52), (-0.5, -0.5, 0.52), (0.5, -0.5, 0.52), (-0.42, -0.72, 1.75), (0.42, -0.72, 1.75),
                              (-0.38, -0.62, 1.75), (0.38, -0.62, 1.75), (0, -0.78, 2.15), (0, -0.66, 2.15)]), "Base", 0, False)
    for s in (1, -1):
        P.obj("ThroneSpike", cone((s * 0.42, -0.68, 1.65), (s * 0.7, -0.75, 2.2), 0.08, 6), "Accent", 0, False)
        P.obj("ThroneArm", box((s * 0.55, -0.15, 0.78), (0.14, 0.7, 0.14)), "Accent", 0, False)
    P.obj("ThroneGem", ball((0, -0.6, 1.95), (0.1, 0.06, 0.14), 8, 4), "Glass")
    P.obj("Robe", lathe([(0.0, 0.0), (0.5, 0.02), (0.46, 0.4), (0.38, 0.75), (0.22, 0.95), (0.0, 1.0)], 18, "z", (0, -0.25, 0.54)), lambda c, n: "Accent" if c.z > 1.32 else "Belly")
    P.obj("Collar", xf(torus(0.24, 0.06, 0.0, 20, 6), None, (0, -0.25, 1.48)), "Accent")
    P.obj("Head", lathe([(0.0, -0.3), (0.16, -0.27), (0.26, -0.14), (0.34, 0.08), (0.42, 0.3), (0.44, 0.48), (0.36, 0.64), (0.2, 0.72), (0.0, 0.74)], 20, "z", (0, -0.22, 1.82)),
          lambda c, n: "Glass" if c.z > 2.18 else "Trim", 1)
    for k in range(8):   # the gold crown round the brain
        a = 2 * math.pi * k / 8
        c = Vector((math.sin(a) * 0.43, -0.22 + math.cos(a) * 0.43, 2.12))
        P.obj("Crown", cone(c, c + Vector((math.sin(a) * 0.12, math.cos(a) * 0.12, 0.28)), 0.05, 5), "Accent", 0, False)
    for s in (1, -1):
        for (dx, dz, sz) in ((0.12, 1.86, 1.0), (0.23, 1.98, 0.7)):
            P.obj("Eye", ball((s * dx, 0.06 - (0.03 if sz < 1 else 0), dz), (0.07 * sz, 0.04, 0.05 * sz), 10, 5), "Lamp")
        P.obj("Arm", pipe([(s * 0.36, -0.2, 1.3), (s * 0.5, -0.05, 0.98), (s * 0.55, 0.15, 0.9)], [0.08, 0.07, 0.06], 8), "Belly")
        P.obj("Hand", ball((s * 0.55, 0.2, 0.9), (0.08, 0.08, 0.07), 8, 4), "Trim")
    P.obj("Sceptre", pipe([(0.55, 0.22, 0.62), (0.55, 0.22, 1.5)], [0.03, 0.03], 6), "Accent")
    P.obj("Orb", ball((0.55, 0.22, 1.6), (0.12, 0.12, 0.12), 10, 5), "Glow")
    big = Matrix.Translation((0, -0.2, 0.38)) @ Matrix.Scale(1.3, 4) @ Matrix.Translation((0, 0.2, -0.38))
    for ob in P.parts[n0:]: ob.data.transform(big)
    P.part("Muzzle", ball((0, 2.36, -0.2), (0.17, 0.08, 0.17), 10, 5), "Glow", (0, 2.36, -0.2))
    return P


BOSSES = [("saucer", B_saucer), ("tank", B_tank), ("dragon", B_dragon), ("kraken", B_kraken), ("mothership", B_mothership)]

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for bid, fn in BOSSES:
        if ONLY and bid not in ONLY: continue
        fn().finish()
    print("DONE")
