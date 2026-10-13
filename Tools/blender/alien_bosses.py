# Sky Squad, the alien world's five bosses (2026-10-10: "new bosses for Alien, cancel the ones it has - vehicles, a flying space dragon,
# a flying saucer with someone on it shooting - legendary, five bosses only"). Built from code like the enemy planes (enemy_planes.py lends
# its helpers): the saucer gunner, the nebula manta, the void dragon, the space kraken and the overlord's mothership.
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


# ================================================================= 2. the nebula manta
MANTA_BODY = [(1.25, 0.40, 0.07, 0, 0.0), (1.1, 0.50, 0.15, 0, 0.02), (0.7, 0.58, 0.25, 0, 0.05), (0.2, 0.60, 0.28, 0, 0.05),
              (-0.4, 0.50, 0.22, 0, 0.03), (-0.9, 0.30, 0.13, 0, 0.02), (-1.2, 0.12, 0.06, 0, 0.02)]
# the wing from root to tip (x, leading edge, trailing edge, thickness, z): the leading edge bows out, the trailing edge curves in to a
# pointed, slightly raised, sickle-shaped tip, as on a real oceanic manta
MANTA_WING = [(0.3, 0.98, -0.78, 0.17, 0.04), (0.6, 0.86, -0.64, 0.14, 0.045), (0.9, 0.74, -0.56, 0.12, 0.05), (1.4, 0.50, -0.44, 0.085, 0.07),
              (1.9, 0.20, -0.30, 0.06, 0.10), (2.35, -0.15, -0.32, 0.04, 0.16), (2.65, -0.42, -0.46, 0.02, 0.22)]
MANTA_HUB = 0.42   # the wings hinge here, just inside the body's sides

def manta_at(rows, k, t):
    """column k of the rows (sorted by their first value) interpolated at t."""
    rows = sorted(rows, key=lambda r: r[0])
    t = min(max(t, rows[0][0]), rows[-1][0])
    for r0, r1 in zip(rows, rows[1:]):
        if t <= r1[0]:
            u = (t - r0[0]) / (r1[0] - r0[0]) if r1[0] > r0[0] else 0.0
            return r0[k] + (r1[k] - r0[k]) * u
    return rows[-1][k]

def manta_z(x, y, side):
    """the height of the body's back (side 1) or underside (side -1) at (x, y)."""
    a = manta_at(MANTA_BODY, 1, y); b = manta_at(MANTA_BODY, 2, y); cz = manta_at(MANTA_BODY, 4, y)
    return cz + side * b * math.sqrt(max(0.0, 1 - (x / a) ** 2))

def manta_skin(c, n):
    """an oceanic manta's coat: an indigo back with the two pale shoulder patches (split down the middle by a dark band, their front edge
    parallel to the wing's leading edge), a pale belly, a dark margin along the trailing edge and the tips underneath."""
    x = abs(c.x)
    if n.z < -0.3:
        if x > 0.6 and (c.y < manta_at(MANTA_WING, 2, x) + 0.13 or x > 2.3): return "Accent"
        return "Belly"
    return "Base"

# the shoulder patch (right side): its front edge follows the wing's leading edge out to a point a third of the way along the wing, its
# back edge sweeps in again to the middle of the back; the dark band down the spine keeps the two apart
PATCH_FRONT = [(0.12, 0.8), (0.4, 0.77), (0.8, 0.6), (1.2, 0.38), (1.45, 0.24)]
PATCH_BACK = [(0.12, -0.1), (0.4, 0.0), (0.75, 0.1), (1.15, 0.15), (1.45, 0.24)]
AIR_TOP = [(0.0, 0.0), (0.15, 0.5), (0.55, 0.42), (1.0, 0.06)]   # the upper side of EP.airfoil: (along the chord, thickness)

def wing_top(x, y):
    le = manta_at(MANTA_WING, 1, x); te = manta_at(MANTA_WING, 2, x); th = manta_at(MANTA_WING, 3, x); z = manta_at(MANTA_WING, 4, x)
    if x < MANTA_WING[0][0] or not te <= y <= le: return -9.0
    return z + th * manta_at(AIR_TOP, 1, (le - y) / (le - te))

def back_top(x, y):
    """the top of whatever is uppermost at (x, y): the body or the wing."""
    a = manta_at(MANTA_BODY, 1, y)
    return max(manta_z(x, y, 1) if x < a else -9.0, wing_top(x, y))

def manta_patch(P, s, flap, hub):
    """the pale shoulder patch laid over the back like a decal, in strips across it: the inner strips on the body, the outer ones on the
    (beating) wing."""
    split = 0.55
    xs = [0.12 + (split - 0.12) * i / 8 for i in range(9)] + [split + (1.43 - split) * i / 18 for i in range(1, 19)]
    rows = 8
    def col(x):
        f, k = manta_at(PATCH_FRONT, 1, x), manta_at(PATCH_BACK, 1, x)
        return [(x, k + (f - k) * j / rows) for j in range(rows + 1)]
    body, wing = bmesh.new(), bmesh.new()
    for x0, x1 in zip(xs, xs[1:]):
        bm = body if x1 <= split + 1e-6 else wing
        c0 = [bm.verts.new((s * x, y, back_top(x, y) + 0.008)) for (x, y) in col(x0)]
        c1 = [bm.verts.new((s * x, y, back_top(x, y) + 0.008)) for (x, y) in col(x1)]
        for j in range(rows):
            q = [c0[j], c1[j], c1[j + 1], c0[j + 1]]
            bm.faces.new(q if s > 0 else list(reversed(q)))
    for bm in (body, wing):
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    P.obj("ShoulderPatch", body, "Belly")
    P.part(flap, wing, "Belly", hub)

def B_manta():
    """A cosmic manta ray, cartoon but true to the animal (2026-10-13: "keep the cartoon look, more realistic details, not random" - it had
    a halo of crystals, crystals down its spine and glowing stripes; 2026-10-10 it replaced the hover tank). A broad flat body with a wide
    mouth at the front glowing deep inside (his gun), the two cephalic fins reaching forward either side of it, big eyes on the sides of the
    head under heavy brows, sickle-shaped wings that beat slowly with a row of glowing photophores along each leading edge, the pale
    shoulder patches of an oceanic manta on its back, five gill slits a side and a few dark spots on its pale belly, small pelvic fins, a
    little dorsal fin, and a thin whip tail."""
    P = Boss("manta", {"Base": ((0.06, 0.11, 0.30), 0.6), "Belly": ((0.90, 0.93, 1.0), 0.5), "Accent": ((0.20, 0.13, 0.42), 0.55),
                       "Trim": ((1.0, 0.78, 0.25), 0.7), "Glass": ((0.60, 0.95, 1.0), 0.95), "Dark": ((0.02, 0.03, 0.08), 0.5),
                       "Glow": ((0.30, 1.0, 0.95), 0.5), "Metal": ((0.50, 0.55, 0.70), 0.7), "Lamp": ((1.0, 0.35, 0.85), 0.8)})
    P.obj("Body", loft(MANTA_BODY, 20), manta_skin, 1)
    # the mouth: a wide dark slot across the front with pale lips, glowing deep inside
    P.obj("Mouth", ball((0, 1.235, -0.015), (0.33, 0.06, 0.065), 16, 6), "Dark")
    lip = torus(0.33, 0.028, 0.0, 32, 6)
    xf(lip, Matrix.Diagonal((1.0, 1.0, 0.2)) @ Matrix.Rotation(math.radians(90), 3, "X"), (0, 1.25, -0.015))
    P.obj("Lip", lip, "Base")
    for s in (1, -1):
        # the cephalic fins: flat paddles reaching forward and a little down beside the mouth, the tips curling in; pale on the inside
        fin = loft([(1.05, 0.11, 0.035, s * 0.43, 0.0), (1.3, 0.12, 0.035, s * 0.45, -0.03), (1.55, 0.10, 0.03, s * 0.43, -0.07),
                    (1.72, 0.07, 0.025, s * 0.38, -0.09), (1.8, 0.03, 0.02, s * 0.34, -0.09)], 10)
        P.obj("CephalicFin", fin, lambda c, n, s=s: "Belly" if n.x * s < -0.5 or n.z < -0.5 else "Base", 1)
        # the eyes on the sides of the head, looking forward and out: pale eye, gold iris, black pupil, a glint
        e = Vector((s * 0.47, 1.06, 0.07)); d = Vector((s * 0.55, 0.75, 0.38)).normalized()
        P.obj("Eye", ball(tuple(e), (0.1, 0.1, 0.1), 14, 8), "Belly")
        P.obj("Iris", ball(tuple(e + d * 0.06), (0.065, 0.065, 0.065), 12, 6), "Trim")
        P.obj("Pupil", ball(tuple(e + d * 0.088), (0.04, 0.04, 0.04), 10, 5), "Dark")
        P.obj("Glint", ball(tuple(e + d * 0.115 + Vector((0, 0, 0.022))), (0.014, 0.014, 0.014), 6, 3), "Belly")
        # a heavy brow over each eye: it scowls at the player
        P.obj("Brow", pipe(bez((s * 0.36, 1.05, 0.17), (s * 0.43, 1.12, 0.2), (s * 0.52, 1.12, 0.17), (s * 0.58, 1.05, 0.1), 5),
                           [0.025, 0.04, 0.045, 0.04, 0.03, 0.02], 6), "Base")
        # five gill slits a side underneath, in a curving row behind the mouth
        for k in range(5):
            gx, gy = s * (0.30 + 0.015 * k), 0.82 - 0.1 * k
            g = box((0, 0, 0), (0.17 - 0.012 * k, 0.018, 0.02), Matrix.Rotation(math.radians(-s * (12 + 4 * k)), 3, "Z"))
            P.obj("Gill", xf(g, None, (gx, gy, manta_z(gx, gy, -1) - 0.004)), "Accent", 0, False)
        # the pelvic fins either side of the tail's root
        P.obj("PelvicFin", sheet([[(s * 0.12, -0.92, -0.02), (s * 0.34, -1.12, -0.03), (s * 0.3, -1.22, -0.03), (s * 0.1, -1.2, -0.02)]], 0.03), "Base", 0, False)
    # a few dark spots on the belly between the gills - each manta has its own pattern; this is his
    for (x, y, r) in ((0.0, 0.42, 0.05), (0.1, 0.28, 0.035), (-0.12, 0.2, 0.045), (0.05, 0.05, 0.03), (-0.04, -0.12, 0.04)):
        P.obj("Spot", ball((x, y, manta_z(x, y, -1) + 0.008), (r, r, 0.012), 10, 4), "Dark")
    # the little dorsal fin just ahead of the tail
    P.fin([(0.0, -0.78, -1.08, 0.05), (0.2, -1.0, -1.12, 0.02)], 0.0, manta_z(0, -0.95, 1) - 0.02, 0.0, "Base", 0, "DorsalFin")
    # the tail: a thin whip trailing back with a lazy S
    tail = bez((0, -1.15, 0.02), (0, -1.9, 0.0), (0.18, -2.4, 0.12), (-0.05, -2.95, 0.22), 12)
    P.obj("Tail", pipe(tail, [0.055 - 0.0042 * i for i in range(13)], 8), "Base")
    # the wings: they beat slowly; sliced every ~0.08 so the patterns follow the shape
    for s in (1, -1):
        name = "FlapR" if s > 0 else "FlapL"
        hub = (s * MANTA_HUB, 0.15, 0.04)
        secs = []
        for a0, a1 in zip(MANTA_WING, MANTA_WING[1:]):
            n = max(2, int((a1[0] - a0[0]) / 0.08))
            secs += [tuple(u + (v - u) * i / n for u, v in zip(a0, a1)) for i in range(n)]
        secs.append(MANTA_WING[-1])
        bm = sweep([(x, EP.airfoil(le, te, th, z)) for (x, le, te, th, z) in secs], "x")
        if s < 0: bm = mirror_x(bm)
        P.part(name, bm, manta_skin, hub, 0)
        manta_patch(P, s, name, hub)
        # photophores: a row of glowing spots evenly along the leading edge, shrinking toward the tip
        for k in range(5):
            x = 0.85 + k * 0.33
            le = manta_at(MANTA_WING, 1, x); th = manta_at(MANTA_WING, 3, x); z = manta_at(MANTA_WING, 4, x)
            r = 0.05 - 0.006 * k
            P.part(name, ball((s * x, le - 0.1 - 0.02 * k, z + th * 0.42), (r, r, r * 0.45), 8, 4), "Glow", hub)
    P.part("Muzzle", ball((0, 1.275, -0.015), (0.2, 0.04, 0.035), 10, 4), "Glow", (0, 1.275, -0.015))
    return P


# ================================================================= 3. the void dragon
def lerp_keys(u, keys):
    """piecewise-linear through (u, value) keys."""
    for (u0, a), (u1, b) in zip(keys, keys[1:]):
        if u <= u1: return a + (b - a) * max(0.0, (u - u0) / (u1 - u0))
    return keys[-1][1]

def spine_frames(pts):
    """(tangent toward the tail, side, up) per spine point; on the rearing neck 'up' is the back of the neck."""
    out = []
    for i in range(len(pts)):
        t = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        side = t.cross(Vector((0, 0, 1))).normalized(); up = side.cross(t).normalized()
        out.append((t, side, up))
    return out

def skin(bm, rings, seg, cap=True):
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

def body_loft(pts, rx, rz, fr, seg=22, sq=1.2, flat=0.8):
    """a body along a curved spine: rounded-square sections rx across and rz up, the belly side flattened."""
    bm = bmesh.new(); rings = []
    for i, p in enumerate(pts):
        t, side, up = fr[i]
        if rx[i] < 1e-4: rings.append([bm.verts.new(p)]); continue
        ring = []
        for k in range(seg):
            a = 2 * math.pi * k / seg; ca, sa = math.cos(a), math.sin(a)
            u = math.copysign(abs(ca) ** (1 / sq), ca) * rx[i]
            v = math.copysign(abs(sa) ** (1 / sq), sa) * rz[i] * (flat if sa < 0 else 1.0)
            ring.append(bm.verts.new(p + side * u + up * v))
        rings.append(ring)
    return skin(bm, rings, seg)

def oriented_ball(c, r, x, y, z, seg=8, rings=4):
    """an ellipsoid with radii r along the axes x, y, z (unit vectors) about c."""
    bm = ball((0, 0, 0), r, seg, rings)
    m = Matrix((x, y, z)).transposed()
    return xf(bm, m, tuple(c))

def B_dragon():
    """The void dragon (2026-10-13, redesigned: "more realistic while keeping its cartoon shape, realistic details, not random"): the
    same indigo star-dragon rearing toward the player with a horned head and an open glowing jaw, now built like a real animal - an
    S-curved neck into a deep chest, narrow waist and hips, a long tapering tail ending in a spade; countershaded (dark back, violet
    flanks, gold belly plates that shrink with the body and are cut by bronze seams); one row of bony back spines graded biggest at the
    shoulders with a glowing seam along the ridge and two rows of armour scutes beside it; a row of glowing photophores along each flank,
    one per belly plate, like a deep-sea fish. The skull has brow ridges over slit-pupil eyes, nostrils and a nose horn on the snout, a
    hinged lower jaw with graded teeth (a canine on each side), three pairs of ringed horns and cheek spikes. Four jointed legs: forearms
    reaching at the player with three clawed fingers and a dewclaw, muscular hind legs with a digitigrade hock. The wings are bat wings
    on real bones - humerus, forearm, a thumb claw at the wrist and four long jointed fingers - the membrane scalloped between them,
    darker near the body and violet toward the edge with a cyan rim and a glowing vein down each panel; they beat about the shoulder."""
    P = Boss("dragon", {"Base": ((0.07, 0.06, 0.22), 0.55), "Belly": ((0.95, 0.76, 0.38), 0.65), "Accent": ((0.30, 0.13, 0.62), 0.5),
                        "Trim": ((0.93, 0.89, 0.80), 0.55), "Glass": ((0.40, 0.95, 1.0), 0.95), "Dark": ((0.04, 0.02, 0.07), 0.4),
                        "Glow": ((0.25, 0.95, 1.0), 0.5), "Metal": ((0.55, 0.36, 0.14), 0.7), "Lamp": ((1.0, 0.35, 0.70), 0.8)})
    # ---- the spine: the neck rises toward the player, a deep chest, a narrow waist, then the tail sweeps back and out
    neck = bez((0, 1.24, 1.16), (0, 1.08, 0.66), (0, 0.84, 0.36), (0, 0.42, 0.26), 10)
    torso = bez((0, 0.42, 0.26), (0, 0.02, 0.22), (0, -0.45, 0.14), (0, -0.85, 0.10), 8)[1:]
    tail = bez((0, -0.85, 0.10), (0.05, -1.55, 0.0), (0.8, -1.95, 0.12), (0.6, -2.65, 0.45), 18)[1:]
    PTS = neck + torso + tail
    RX, RZ = [], []
    for i in range(len(neck)):
        u = i / (len(neck) - 1)
        RX.append(lerp_keys(u, [(0, 0.15), (0.5, 0.2), (1, 0.33)])); RZ.append(lerp_keys(u, [(0, 0.19), (0.5, 0.25), (1, 0.37)]))
    for i in range(len(torso)):
        u = (i + 1) / len(torso)
        RX.append(lerp_keys(u, [(0, 0.33), (0.25, 0.43), (0.45, 0.44), (0.75, 0.36), (1, 0.35)]))
        RZ.append(lerp_keys(u, [(0, 0.37), (0.25, 0.48), (0.45, 0.45), (0.75, 0.35), (1, 0.33)]))
    for i in range(len(tail)):
        u = (i + 1) / len(tail); r = 0.35 * (1 - u) ** 1.3 + 0.02
        RX.append(r); RZ.append(r * 1.1)
    FR = spine_frames(PTS)
    n = len(PTS)
    # the plate phase: one belly plate per 0.4 of the local radius, so the plates shrink with the body
    PH = [0.0]
    for i in range(1, n):
        PH.append(PH[-1] + (PTS[i] - PTS[i - 1]).length / (0.4 * (RX[i] + RX[i - 1]) * 0.5 + 1e-4))
    def locate(c):
        i = min(range(n), key=lambda k: (PTS[k] - c).length_squared)
        j = i + 1 if i + 1 < n and (i == 0 or (PTS[i + 1] - c).length_squared < (PTS[i - 1] - c).length_squared) else i - 1
        a, b = PTS[i], PTS[j]; d = b - a
        f = max(0.0, min(1.0, (c - a).dot(d) / max(d.length_squared, 1e-9)))
        return i, PH[i] + (PH[j] - PH[i]) * f
    def at(ph):
        """the point, frame and radii at a plate phase."""
        for i in range(n - 1):
            if PH[i + 1] >= ph:
                f = (ph - PH[i]) / max(PH[i + 1] - PH[i], 1e-9)
                p = PTS[i].lerp(PTS[i + 1], f); k = i if f < 0.5 else i + 1
                return p, FR[k], RX[i] + (RX[i + 1] - RX[i]) * f, RZ[i] + (RZ[i + 1] - RZ[i]) * f
        return PTS[-1], FR[-1], RX[-1], RZ[-1]
    def hide(c, n_):
        i, ph = locate(c)
        t, side, up = FR[i]; d = c - PTS[i]
        u = d.dot(side) / RX[i]; v = d.dot(up) / RZ[i]
        if v < -0.38 and abs(u) < 0.78: return "Metal" if ph % 1.0 < 0.13 else "Belly"   # gold belly plates, bronze seams
        return "Base" if v > 0.3 else "Accent"   # countershading: dark back, violet flanks
    P.obj("Body", body_loft(PTS, RX, RZ, FR), hide, 0)
    # the ridge: a glowing seam down the back, one row of bony spines (biggest over the shoulders), two rows of scutes beside it
    lo, hi = 2, n - 3
    P.obj("Ridge", pipe([PTS[i] + FR[i][2] * RZ[i] * 0.97 for i in range(lo, hi)], [0.022 * min(1.0, RX[i] / 0.2) + 0.006 for i in range(lo, hi)], 5), "Glow")
    k = 1
    while k + 0.5 < PH[hi]:
        p, (t, side, up), rx, rz = at(k)
        if rx < 0.075 and int(k) % 2: k += 1; continue   # thinner down the tail, every other plate
        h = (0.55 * rz + 0.03) * (1.25 if 0.0 < p.y < 0.6 and p.z < 0.6 else 1.0)
        L = 0.3 * rx + 0.03; w = 0.03 + 0.05 * rx
        b0 = p + up * rz * 0.9
        tip = b0 + up * h + t * h * 0.6
        def spike(c, n_, b0=b0, up=up, h=h): return "Trim" if (c - b0).dot(up) > h * 0.5 else "Accent"
        P.obj("Spine", hull([b0 - t * L + side * w, b0 - t * L - side * w, b0 + t * L + side * w, b0 + t * L - side * w,
                             tip + side * w * 0.15, tip - side * w * 0.15, b0 - up * rz * 0.15]), spike, 0, False)
        if k + 1.0 < PH[hi]:
            p2, (t2, side2, up2), rx2, rz2 = at(k + 0.5)
            for s in (1, -1):
                q = p2 + side2 * s * 0.6 * rx2 + up2 * 0.78 * rz2
                nn = (side2 * s * 0.6 / rx2 + up2 * 0.78 / rz2).normalized()
                P.obj("Scute", oriented_ball(q, (0.16 * rx2, 0.24 * rx2, 0.07 * rx2), t2.cross(nn).normalized(), t2, nn), "Accent", 0)
        k += 1
    # photophores: one glowing spot per belly plate along each lower flank, from the throat to mid-tail
    k = 1.5
    while k < PH[n - 6]:
        p, (t, side, up), rx, rz = at(k)
        for s in (1, -1):
            nn = (side * s * 0.85 / rx - up * 0.35 / rz).normalized()
            q = p + side * s * 0.84 * rx - up * 0.3 * rz * 0.8
            P.obj("Photophore", oriented_ball(q, (0.025 + 0.06 * rx, 0.025 + 0.06 * rx, 0.02), t.cross(nn).normalized(), t, nn), "Glow", 0)
        k += 1
    # the tail spade, edged with light and ribbed down the middle
    T = PTS[-2]; t, side, up = FR[-2]
    outline = [T + side * 0.27 - t * 0.12, T + side * 0.22 + t * 0.2, T + t * 0.52, T - side * 0.22 + t * 0.2, T - side * 0.27 - t * 0.12, T - t * 0.02]
    mid = T + t * 0.14
    P.obj("Spade", sheet([[tuple(mid), tuple(outline[i]), tuple(outline[(i + 1) % 6])] for i in range(6)], 0.035), "Accent", 0, False)
    P.obj("SpadeRim", pipe(outline[:5], [0.022] * 5, 5), "Glow")
    P.obj("SpadeRib", pipe([T - t * 0.05, T + t * 0.25, T + t * 0.5], [0.04, 0.03, 0.0], 6), "Trim")

    # ---- the head, drawn big (built pointing +Y about the skull base, then tipped down and scaled)
    HB = Vector(PTS[0]); HR = Matrix.Rotation(math.radians(-14), 3, "X") @ Matrix.Scale(1.3, 3); HI = HR.inverted()
    def H(bm): return xf(bm, HR, tuple(HB))
    def hp(fn): return lambda c, n_: fn(HI @ (c - HB), (HI @ n_).normalized())
    def hpt(p): return HB + HR @ Vector(p)
    UP = [(-0.12, 0.10, 0.09, 0, 0.03), (-0.02, 0.19, 0.16, 0, 0.05), (0.12, 0.23, 0.18, 0, 0.07), (0.28, 0.21, 0.15, 0, 0.07),
          (0.42, 0.16, 0.11, 0, 0.04), (0.58, 0.135, 0.09, 0, 0.015), (0.72, 0.13, 0.08, 0, 0.0), (0.82, 0.12, 0.075, 0, -0.005),
          (0.89, 0.085, 0.055, 0, -0.01), (0.925, 0.03, 0.02, 0, -0.012)]
    def ring_at(rings, y):
        for r0, r1 in zip(rings, rings[1:]):
            if y <= r1[0]:
                f = (y - r0[0]) / (r1[0] - r0[0]); return [a + (b - a) * f for a, b in zip(r0, r1)]
        return list(rings[-1])
    def skull(c, n_):
        if n_.z > 0.45: return "Base"
        if n_.z < -0.45: return "Dark" if c.y > 0.08 else "Belly"   # the roof of the open mouth; the throat behind it
        return "Accent"
    P.obj("Skull", H(loft(UP, 20, sq=1.25)), hp(skull), 0)
    # the lower jaw, hinged under the ear and dropped open
    LO = [(0.0, 0.17, 0.07, 0, -0.08), (0.2, 0.16, 0.06, 0, -0.10), (0.42, 0.13, 0.05, 0, -0.11), (0.62, 0.11, 0.045, 0, -0.105),
          (0.78, 0.09, 0.04, 0, -0.10), (0.86, 0.05, 0.03, 0, -0.095)]
    J = Vector((0, 0.02, -0.06)); JR = Matrix.Rotation(math.radians(-30), 3, "X"); JI = JR.inverted()
    def Jw(bm): return H(xf(bm, JR, tuple(J - JR @ J)))
    def jpt(p): return hpt(J + JR @ (Vector(p) - J))
    def jaw(c, n_):
        c = JI @ (c - J) + J; n_ = JI @ n_
        if n_.z > 0.4: return "Dark"
        if n_.z < -0.3: return "Metal" if (c.y * 9.0) % 1.0 < 0.15 else "Belly"
        return "Accent"
    P.obj("Jaw", Jw(loft(LO, 16, sq=1.2)), hp(jaw), 0)
    P.obj("Mouth", H(ball((0, 0.30, -0.13), (0.11, 0.34, 0.07), 12, 6)), "Dark")
    P.obj("Throat", H(ball((0, 0.10, -0.12), (0.12, 0.2, 0.09), 12, 6)), "Glow")
    P.obj("Tongue", Jw(pipe([(0, 0.08, -0.05), (0, 0.35, -0.06), (0, 0.6, -0.055)], [0.05, 0.045, 0.02], 8)), "Lamp")
    for s in (1, -1):
        # teeth: small at the back, a long canine near the front, then little incisors
        for k in range(6):
            y = 0.30 + k * 0.1; r = ring_at(UP, y); L = 0.11 if k == 4 else (0.05 if k == 5 else 0.045 + 0.005 * k)
            top = Vector((s * r[1] * 0.78, y, r[4] - r[2] * 0.8))
            P.obj("Tooth", H(cone(top, top + Vector((-s * 0.01, 0.015, -L)), 0.02 + L * 0.15, 5)), "Trim", 0, False)
            r = ring_at(LO, y - 0.02)
            if y - 0.02 > LO[-1][0]: continue
            bot = Vector((s * r[1] * 0.75, y - 0.02, r[4] + r[2] * 0.8)); L = 0.085 if k == 3 else 0.04
            P.obj("Tooth", Jw(cone(bot, bot + Vector((-s * 0.01, 0.015, L)), 0.018 + L * 0.15, 5)), "Trim", 0, False)
        # the eye: a dark socket, a glowing iris with a slit pupil and a glint, under a heavy brow ridge
        P.obj("Socket", H(ball((s * 0.165, 0.32, 0.125), (0.07, 0.08, 0.06), 10, 5)), "Dark")
        ic = Vector((s * 0.18, 0.335, 0.13)); P.obj("Eye", H(ball(tuple(ic), (0.058, 0.062, 0.05), 12, 6)), "Glow")
        dv = Vector((s * 0.65, 0.75, 0.1)).normalized()
        P.obj("Pupil", H(oriented_ball(ic + dv * 0.052, (0.011, 0.012, 0.042), dv.cross(Vector((0, 0, 1))).normalized(), dv, Vector((0, 0, 1)))), "Dark")
        P.obj("Glint", H(ball(tuple(ic + dv * 0.045 + Vector((0, 0, 0.03))), (0.012, 0.012, 0.012), 6, 3)), "Trim")
        P.obj("Brow", H(pipe(bez((s * 0.07, 0.43, 0.17), (s * 0.19, 0.39, 0.215), (s * 0.25, 0.25, 0.2), (s * 0.24, 0.08, 0.17), 6),
                             [0.03, 0.04, 0.045, 0.045, 0.04, 0.035, 0.02], 7)), "Base")
        P.obj("Nostril", H(ball((s * 0.055, 0.85, 0.055), (0.024, 0.03, 0.014), 8, 4)), "Dark")
        # three pairs of horns, ivory darkening to the tip: the crown pair, a shorter pair outside it, and cheek spikes
        for (r0, d, L, rr) in (((s * 0.11, 0.0, 0.17), (s * 0.2, -0.8, -0.04), 1.0, 0.062), ((s * 0.19, -0.02, 0.09), (s * 0.32, -0.5, -0.12), 0.7, 0.05),
                               ((s * 0.21, 0.1, -0.03), (s * 0.3, -0.3, -0.14), 0.45, 0.045)):
            r0 = Vector(r0); d = Vector(d)
            pts = bez(r0, r0 + Vector((d.x * 0.25, d.y * 0.35, 0.08)), r0 + Vector((d.x * 0.7, d.y * 0.72, d.z * 0.3 + 0.06)), r0 + d + Vector((0, 0, 0.1 * L)), 7)   # back along the skull, the tip lifting
            def horn(c, n_, r0=r0, d=d): return "Dark" if (c - r0).dot(d) / d.length_squared > 0.72 else "Trim"
            P.obj("Horn", H(pipe(pts, [rr * (1 - j / 7) ** 0.8 + 0.004 for j in range(7)] + [0.0], 8)), hp(horn), 0)
        for j, (y, L) in enumerate(((0.12, 0.12), (0.0, 0.16), (-0.1, 0.13))):   # the frill of spikes behind the jaw
            b = Vector((s * 0.16, y, -0.1))
            P.obj("Frill", Jw(cone(b, b + Vector((s * L * 0.8, -L * 0.7, -L * 0.25)), 0.03, 5)), "Accent", 0, False)
    P.obj("NoseHorn", H(cone((0, 0.76, 0.07), (0, 0.83, 0.17), 0.035, 6)), "Trim", 0, False)
    for k, y in enumerate((0.6, 0.5, 0.4, 0.28, 0.16, 0.04)):   # a line of small ridge scales from the snout to the crown
        r = ring_at(UP, y); b = Vector((0, y, r[4] + r[2] * 0.95)); h = 0.025 + 0.007 * k
        P.obj("HeadRidge", H(hull([b + Vector((0.025, 0.03, 0)), b + Vector((-0.025, 0.03, 0)), b + Vector((0.025, -0.03, 0)),
                                   b + Vector((-0.025, -0.03, 0)), b + Vector((0, -0.03, h))])), "Accent", 0, False)

    # ---- the legs
    for s in (1, -1):
        def limb(c, n_): return "Base" if n_.z > 0.7 else "Accent"
        # forelegs reaching at the player: elbow back, three clawed fingers and a dewclaw
        sh = Vector((s * 0.28, 0.22, 0.12)); el = Vector((s * 0.5, 0.12, -0.3)); wr = Vector((s * 0.42, 0.62, -0.42))
        P.obj("Arm", pipe([sh, Vector((s * 0.46, 0.2, -0.1)), el], [0.16, 0.12, 0.085], 10), limb, 0)
        P.obj("Arm", pipe([el, Vector((s * 0.48, 0.38, -0.38)), wr], [0.085, 0.075, 0.055], 10), limb, 0)
        P.obj("Elbow", ball(tuple(el), (0.09, 0.09, 0.09), 8, 4), "Base")
        P.obj("Hand", ball(tuple(wr + Vector((0, 0.03, 0))), (0.075, 0.08, 0.05), 8, 4), limb)
        for a in (-28, 0, 28, -75):
            d = Matrix.Rotation(math.radians(a * s), 3, "Z") @ Vector((0, 1, -0.35)).normalized()
            Lf = 0.11 if a != -75 else 0.06
            k1 = wr + d * Lf; tp = wr + d * Lf * 1.9 + Vector((0, 0, -0.03))
            P.obj("Finger", pipe([wr, k1, tp], [0.035, 0.03, 0.024], 6), limb, 0)
            P.obj("Claw", pipe(bez(tp, tp + d * 0.04, tp + d * 0.08 + Vector((0, 0, -0.02)), tp + d * 0.09 + Vector((0, 0, -0.08)), 4),
                               [0.024, 0.02, 0.014, 0.007, 0.0], 5), "Trim")
        # hind legs: a muscular thigh, knee forward, a digitigrade hock with a spur, three clawed toes
        hip = Vector((s * 0.3, -0.7, 0.1)); kn = Vector((s * 0.48, -0.4, -0.22)); hk = Vector((s * 0.46, -0.7, -0.42)); ft = Vector((s * 0.45, -0.55, -0.58))
        P.obj("Thigh", ball((s * 0.38, -0.6, -0.02), (0.18, 0.3, 0.24), 12, 6), limb)
        P.obj("Leg", pipe([hip, kn], [0.15, 0.1], 10), limb, 0)
        P.obj("Leg", pipe([kn, hk], [0.1, 0.065], 8), limb, 0)
        P.obj("Leg", pipe([hk, ft], [0.065, 0.05], 8), limb, 0)
        P.obj("Spur", cone(hk, hk + Vector((s * 0.02, -0.12, 0.02)), 0.03, 5), "Trim", 0, False)
        for a in (-25, 0, 25):
            d = Matrix.Rotation(math.radians(a * s), 3, "Z") @ Vector((0, 1, -0.5)).normalized()
            tp = ft + d * 0.12
            P.obj("Toe", pipe([ft, tp], [0.04, 0.028], 6), limb, 0)
            P.obj("Claw", pipe(bez(tp, tp + d * 0.04, tp + d * 0.07 + Vector((0, 0, -0.02)), tp + d * 0.08 + Vector((0, 0, -0.07)), 4),
                               [0.026, 0.02, 0.014, 0.007, 0.0], 5), "Trim")

        # ---- the wing: humerus, forearm, a thumb claw at the wrist and four jointed fingers; it beats about the shoulder
        name = "FlapL" if s < 0 else "FlapR"
        ws = Vector((s * 0.22, 0.18, 0.55)); we = Vector((s * 0.8, -0.05, 0.95)); wr = Vector((s * 1.25, 0.28, 1.5))
        tips = [Vector((s * 2.05, 0.05, 2.25)), Vector((s * 2.6, -0.35, 1.75)), Vector((s * 2.55, -0.85, 1.05)), Vector((s * 1.95, -1.15, 0.45))]
        root = Vector((s * 0.3, -0.78, 0.32))
        hub = tuple(ws)
        P.part(name, pipe([ws, (ws + we) * 0.5 + Vector((0, 0, 0.06)), we], [0.1, 0.075, 0.06], 8), "Base", hub)
        P.part(name, pipe([we, wr], [0.06, 0.045], 8), "Base", hub)
        P.part(name, ball(tuple(we), (0.065, 0.065, 0.065), 8, 4), "Base", hub)
        P.part(name, ball(tuple(wr), (0.06, 0.06, 0.06), 8, 4), "Base", hub)
        P.part(name, pipe(bez(wr, wr + Vector((s * 0.02, 0.1, 0.05)), wr + Vector((s * 0.03, 0.2, 0.06)), wr + Vector((s * 0.02, 0.26, 0.0)), 4),
                          [0.035, 0.028, 0.02, 0.01, 0.0], 5), "Trim", hub)
        for tp in tips:
            kn = wr + (tp - wr) * 0.45 + Vector((0, 0.04, 0.06))
            P.part(name, pipe([wr, kn, tp], [0.042, 0.03, 0.01], 6), "Base", hub)
            P.part(name, ball(tuple(kn), (0.036, 0.036, 0.036), 6, 3), "Base", hub)
            P.part(name, cone(tp, tp + (tp - wr).normalized() * 0.12, 0.018, 4), "Trim", hub, 0, False)
        # the membrane, fanned from the wrist, its trailing edge scalloped between the fingers; dark near the bones, violet outward, a cyan rim
        chain = tips + [root]; edge = []
        for gi, (a, b) in enumerate(zip(chain, chain[1:])):
            sag = 0.24 if gi < 3 else 0.16
            for m in range(6):
                f = m / 6; q = a.lerp(b, f); edge.append(q + (wr - q) * sag * math.sin(math.pi * f))
        edge.append(root)
        bands = [(0.0, 0.32, "Base"), (0.32, 0.6, "Base"), (0.6, 0.8, "Accent"), (0.8, 0.982, "Accent"), (0.982, 1.0, "Glow")]
        for (u0, u1, slot) in bands:
            polys = []
            for e0, e1 in zip(edge, edge[1:]):
                if u0 == 0: polys.append([wr, wr + (e1 - wr) * u1, wr + (e0 - wr) * u1])
                else: polys.append([wr + (e0 - wr) * u0, wr + (e1 - wr) * u0, wr + (e1 - wr) * u1, wr + (e0 - wr) * u1])
            P.part(name, sheet([[tuple(p) for p in poly] for poly in polys], 0.025), slot, hub, 0, False)
        P.part(name, sheet([[tuple(ws), tuple(we), tuple(wr)], [tuple(wr), tuple(root), tuple(ws)]], 0.025), "Base", hub, 0, False)
        for a, b in zip(chain, chain[1:]):   # a glowing vein down the middle of each panel
            m = a.lerp(b, 0.5); m = m + (wr - m) * 0.24
            P.part(name, pipe([wr + (m - wr) * 0.12, wr + (m - wr) * 0.55, wr + (m - wr) * 0.92], [0.016, 0.014, 0.008], 4), "Glow", hub)
    mz = hpt((0, 0.55, -0.1))
    P.part("Muzzle", ball(tuple(mz), (0.12, 0.1, 0.1), 8, 4), "Glow", tuple(mz))
    return P


# ================================================================= 4. the space kraken
KR_RX, KR_RZ, KR_H0 = 1.22, 1.3, 0.15                     # the bell: half an ellipse revolved about up
KR_TILT = Matrix.Rotation(math.radians(-18), 3, "X")       # it leans back, away from the player

def kr_frame(a, th, off=0.0):
    """a point on the kraken's bell (a: round from the front toward +x, th: up from the rim) lifted off the skin, and the frame there
    as a matrix whose columns are x along the round, y out of the skin, z up the skin."""
    ca, sa = math.cos(a), math.sin(a)
    r, h = KR_RX * math.cos(th), KR_H0 + KR_RZ * math.sin(th)
    n = Vector((sa * math.cos(th) / KR_RX, ca * math.cos(th) / KR_RX, math.sin(th) / KR_RZ)).normalized()
    x = Vector((ca, -sa, 0.0)); z = x.cross(n)
    m = KR_TILT @ Matrix((x, n, z)).transposed()
    return KR_TILT @ (Vector((sa * r, ca * r, h)) + n * off), m

def kr_on(x, z, off, a0=0.0, th0=0.0):
    """a point on the bell x across and z up from (a0, th0), measured along the skin, lifted off it."""
    th = th0 + z / 1.25
    return kr_frame(a0 + x / max(0.3, KR_RX * math.cos(th)), th, off)[0]

def kr_put(bm, a, th, off=0.0, k=1.0):
    """a piece built in a skin frame (x along the round, y out, z up) set on the bell at (a, th), k times as big."""
    p, m = kr_frame(a, th, off)
    for v in bm.verts: v.co = p + m @ (v.co * k)
    return bm

def kr_local(a, th, off=0.0, k=1.0):
    """back from the bell into the skin frame at (a, th): for painting a piece by where it sits in its own frame."""
    p, m = kr_frame(a, th, off); mi = m.transposed()
    return lambda c: (mi @ (c - p)) / k

def B_kraken():
    """The star kraken (2026-10-13, remade: "scarier, keep the cartoon shape, more realistic details - not random"): the same plum bell,
    one great eye and eight tentacles, now built like a real cephalopod. Dark top, pale underside; seven branching veins raised on the bell
    with a photophore at each fork, a row of photophores round the rim and two rows of skin bumps between the veins. A bloodshot eye with
    an amber iris striated round a glowing ring and the horizontal bar pupil of an octopus, under heavy lids pulled into a frown, a fleshy
    brow and a crease. Under it the mouth: a ringed lip, two rings of hooked teeth and the black parrot beak, open (his shots leave from
    it). A siphon on the left flank. Each tentacle tapers to a curled tip with a glowing lure, two staggered rows of pale suckers with red
    cups down its inner side, shrinking to the tip; the two front ones carry ivory hooks like a colossal squid's."""
    P = Boss("kraken", {"Base": ((0.36, 0.07, 0.30), 0.6), "Belly": ((0.95, 0.66, 0.66), 0.45), "Accent": ((0.78, 0.05, 0.12), 0.6),
                        "Trim": ((0.97, 0.93, 0.80), 0.55), "Glass": ((1.0, 0.70, 0.08), 0.95), "Dark": ((0.03, 0.01, 0.03), 0.7),
                        "Glow": ((0.10, 0.85, 0.62), 0.5), "Metal": ((0.17, 0.02, 0.14), 0.6), "Lamp": ((1.0, 0.32, 0.04), 0.8)})
    untilt = KR_TILT.transposed()
    fine = lambda bm, paint: P.part("ClothDetail", bm, paint, (0, 0, 0))   # thin raised details: their own object, which the game leaves without the toon outline
    # the bell, dark on top and pale underneath, a muscular lip round the rim
    prof = [(KR_RX * math.cos(t), KR_H0 + KR_RZ * math.sin(t)) for t in [math.pi / 2 - (math.pi / 2 + 0.18) * i / 36 for i in range(37)]]
    prof[0] = (0.0, prof[0][1])
    bell = lathe(prof + [(1.0, -0.17), (0.6, -0.25), (0.0, -0.27)], 64, "z"); xf(bell, KR_TILT)
    P.obj("Bell", bell, lambda c, n: "Belly" if (untilt @ c).z < -0.1 else "Base")
    lip = torus(1.17, 0.085, -0.1, 64, 8); xf(lip, KR_TILT)
    P.obj("Lip", lip, lambda c, n: "Belly" if (untilt @ n).z < -0.3 else "Base")
    # seven veins from the crown, each forking in two two-thirds of the way down; a photophore at every fork
    veins = (-2.3, -1.55, -0.8, 0.8, 1.55, 2.3, math.pi)
    for a0 in veins:
        trunk = [kr_on(0, 0, 0.012, a0 + 0.05 * math.sin(t * 7), t) for t in [1.42 - 0.64 * i / 6 for i in range(7)]]
        fine(pipe(trunk, [0.022 + 0.018 * i / 6 for i in range(7)], 6), "Metal")
        for s in (1, -1):
            br = [kr_frame(a0 + 0.05 * math.sin(0.78 * 7) + s * 0.24 * (i / 6) ** 0.8, 0.78 - 0.66 * i / 6, 0.012)[0] for i in range(7)]
            fine(pipe(br, [0.034 - 0.022 * i / 6 for i in range(7)], 6), "Metal")
            tw = [kr_frame(a0 + s * (0.13 + 0.12 * i / 3), 0.5 - 0.14 * i / 3, 0.012)[0] for i in range(4)]   # a twig off each branch
            fine(pipe(tw, [0.018, 0.014, 0.01, 0.006], 5), "Metal")
        fine(kr_put(ball((0, 0, 0), (0.065, 0.03, 0.065), 10, 5), a0 + 0.05 * math.sin(0.78 * 7), 0.78, 0.01), "Glow")
    for k in range(18):   # the rim row, big and small in turn, none over the mouth
        a = 2 * math.pi * (k + 0.5) / 18
        if abs(math.atan2(math.sin(a), math.cos(a))) < 0.45: continue
        r = 0.065 if k % 2 == 0 else 0.04
        fine(kr_put(ball((0, 0, 0), (r, r * 0.45, r), 10, 5), a, 0.13, 0.005), "Glow")
    mids = (-2.72, -1.925, -1.175, 1.175, 1.925, 2.72)
    for a in mids:   # skin bumps (papillae) between the veins, two rows
        for th, r in ((1.05, 0.075), (0.45, 0.095)):
            P.obj("Papilla", kr_put(ball((0, 0, 0), (r, r * 0.55, r * 1.2), 10, 5), a, th, 0.0), "Base")
    # the eye: socket, bloodshot eyeball, striated iris round a glowing ring, the bar pupil of an octopus
    EA, ETH, EK = 0.0, 0.55, 1.12
    P.obj("Socket", kr_put(ball((0, -0.03, 0), (0.44, 0.14, 0.4), 18, 9), EA, ETH, 0, EK), "Dark")
    P.obj("Eyeball", kr_put(ball((0, 0, 0), (0.4, 0.2, 0.36), 20, 10), EA, ETH, 0, EK), "Trim")
    def on_ball(rho, b):
        return Vector((rho * math.cos(b) * 0.4, 0.2 * math.sqrt(max(0.0, 1 - rho * rho)) + 0.008, rho * math.sin(b) * 0.36))
    for j in range(12):   # capillaries creeping in from the white's edge, each with one branch
        b0 = 2 * math.pi * (j + 0.5) / 12
        if math.sin(b0) > 0.55: continue   # under the upper lid
        main = [on_ball(0.97 - 0.36 * i / 5, b0 + 0.1 * math.sin(i * 1.7 + j)) for i in range(6)]
        fine(kr_put(pipe(main, [0.014, 0.012, 0.01, 0.008, 0.006, 0.004], 5), EA, ETH, 0, EK), "Accent")
        twig = [on_ball(0.84 - 0.1 * i / 2, b0 + 0.1 * math.sin(1.7 + j) + 0.12 * i) for i in range(3)]
        fine(kr_put(pipe(twig, [0.008, 0.006, 0.004], 5), EA, ETH, 0, EK), "Accent")
    iris = lathe([(0.0, 0.226), (0.07, 0.224), (0.12, 0.215), (0.18, 0.198), (0.225, 0.178), (0.25, 0.16), (0.24, 0.12), (0.0, 0.12)], 28, "y")
    loc = kr_local(EA, ETH, 0, EK)
    def iris_paint(c, n):
        q = loc(c); r = math.hypot(q.x, q.z)
        if r < 0.11: return "Lamp"
        return "Lamp" if int((math.atan2(q.z, q.x) % (2 * math.pi)) / (2 * math.pi) * 28) % 3 == 0 and r < 0.22 else "Glass"
    P.obj("Iris", kr_put(iris, EA, ETH, 0, EK), iris_paint)
    pupil = pipe([(-0.14, 0.226, 0), (-0.07, 0.226, 0), (0, 0.226, 0), (0.07, 0.226, 0), (0.14, 0.226, 0)], [0.045, 0.058, 0.042, 0.058, 0.045], 10)
    for v in pupil.verts: v.co.y = 0.226 + (v.co.y - 0.226) * 0.35
    P.obj("Pupil", kr_put(pupil, EA, ETH, 0, EK), "Dark")
    # heavy lids pulled into a frown (the inner ends low), the lower lid, a fleshy brow and a crease over it
    for s in (1, -1):
        lid = ball((0, 0, 0), (0.3, 0.2, 0.15), 16, 7)
        xf(lid, Matrix.Rotation(math.radians(-s * 18), 3, "Y"), (s * 0.2, 0.06, 0.27))
        P.obj("LidTop", kr_put(lid, EA, ETH, 0, EK), "Base")
        brow = [kr_on(s * x, z, 0.05, EA, ETH) for (x, z) in ((0.03, 0.4), (0.18, 0.45), (0.34, 0.53), (0.48, 0.6), (0.6, 0.62))]
        P.obj("Brow", pipe(brow, [0.06, 0.085, 0.08, 0.065, 0.04], 8), "Base")
        for dz in (0.17,):
            cr = [kr_on(s * x, z + dz, 0.012, EA, ETH) for (x, z) in ((0.05, 0.42), (0.18, 0.46), (0.32, 0.53), (0.44, 0.58))]
            fine(pipe(cr, [0.012, 0.02, 0.018, 0.008], 6), "Metal")
    P.obj("LidLow", kr_put(ball((0, 0.05, -0.31), (0.46, 0.18, 0.12), 16, 6), EA, ETH, 0, EK), "Base")
    # the mouth: a ringed lip, a red gullet, two rings of hooked teeth, the black parrot beak open in the middle
    MA, MTH, MK = 0.0, -0.12, 1.3
    mlip = xf(torus(0.24, 0.07, 0.0, 28, 8), Matrix.Rotation(math.radians(90), 3, "X"), (0, 0.03, 0))
    mloc = kr_local(MA, MTH, 0, MK)
    P.obj("MouthLip", kr_put(mlip, MA, MTH, 0, MK), lambda c, n: "Belly" if math.hypot(mloc(c).x, mloc(c).z) < 0.235 else "Base")
    P.obj("Gullet", kr_put(ball((0, -0.01, 0), (0.22, 0.06, 0.22), 16, 6), MA, MTH, 0, MK), "Accent")
    P.obj("Throat", kr_put(ball((0, 0.02, 0), (0.1, 0.035, 0.1), 10, 5), MA, MTH, 0, MK), "Lamp")   # a glow deep in the gullet
    for cnt, r0, r1, y0, y1, w in ((12, 0.2, 0.11, 0.04, 0.14, 0.032), (8, 0.13, 0.06, 0.04, 0.1, 0.022)):
        for k in range(cnt):
            g = 2 * math.pi * (k + 0.5) / cnt; d = Vector((math.cos(g), 0, math.sin(g)))
            tooth = bez(d * r0 + Vector((0, y0, 0)), d * (r0 - 0.01) + Vector((0, y1, 0)), d * r1 + Vector((0, y1, 0)), d * (r1 - 0.02) + Vector((0, y1 - 0.02, 0)), 3)
            P.obj("Tooth", kr_put(pipe(tooth, [w, w * 0.7, w * 0.35, 0.0], 5), MA, MTH, 0, MK), "Trim")
    upper = pipe(bez((0, 0.0, 0.05), (0, 0.1, 0.08), (0, 0.17, 0.06), (0, 0.19, -0.01), 5), [0.06, 0.055, 0.045, 0.03, 0.014, 0.0], 8)
    lower = pipe(bez((0, 0.0, -0.05), (0, 0.08, -0.08), (0, 0.13, -0.06), (0, 0.14, -0.02), 4), [0.05, 0.042, 0.03, 0.012, 0.0], 8)
    for bk in (upper, lower):
        for v in bk.verts: v.co.x *= 0.8
        P.obj("Beak", kr_put(bk, MA, MTH, 0, MK), "Dark")
    mz = kr_frame(MA, MTH, 0.05)[0]
    # the siphon on the left flank, pointing back
    sp = bez((0, -0.02, 0), (0, 0.12, -0.02), (-0.1, 0.19, -0.06), (-0.22, 0.21, -0.08), 4)
    P.obj("Siphon", kr_put(pipe(sp, [0.12, 0.11, 0.1, 0.095, 0.1], 12), -1.6, 0.08), "Base")
    P.obj("SiphonRim", kr_put(xf(torus(0.09, 0.025, 0.0, 14, 5), Matrix.Rotation(math.radians(90), 3, "Y"), sp[-1]), -1.6, 0.08), "Belly")
    P.obj("SiphonHole", kr_put(ball(tuple(sp[-1] + Vector((0.01, 0, 0))), (0.03, 0.07, 0.07), 8, 4), -1.6, 0.08), "Dark")
    # eight tentacles: down, out, curling toward the player and hooking up at the tip; suckers down the inner side
    up = Vector((0, 0, 1))
    for k in range(8):
        a = 2 * math.pi * (k + 0.5) / 8
        out = Vector((math.sin(a), math.cos(a), 0))
        p0 = Vector((out.x * 0.62, out.y * 0.62, -0.18))
        front = 0.55 + 0.45 * max(0.0, out.y)   # the front ones reach further toward the player
        pts = bez(p0, p0 + out * 0.45 + Vector((0, 0, -0.55)), p0 + out * 0.7 + Vector((0, front * 0.6, -1.2)), p0 + out * 0.45 + Vector((0, front * 1.1, -1.05)), 13)
        t = (pts[-1] - pts[-2]).normalized()
        pts += bez(pts[-1], pts[-1] + t * 0.16, pts[-1] + t * 0.2 + up * 0.16, pts[-1] + t * 0.06 + up * 0.22, 4)[1:]   # the curled tip
        N = len(pts)
        rr = [0.19 * (1 - i / (N - 1)) ** 0.85 + 0.018 for i in range(N)]
        tans = [(pts[min(i + 1, N - 1)] - pts[max(i - 1, 0)]).normalized() for i in range(N)]
        inner = []
        for i in range(N):   # the oral side: toward the mouth near the bell, turning to face up along the curl
            u = i / (N - 1); w = -out * (1 - u) + up * u
            w = w - tans[i] * w.dot(tans[i])
            inner.append(w.normalized() if w.length > 1e-4 else up)
        name = "Sway%d" % k
        P.part(name, pipe(pts, rr, 14), "Base", tuple(p0))
        for i in range(1, N - 2):   # two staggered rows of suckers, shrinking toward the tip
            side = tans[i].cross(inner[i]).normalized(); s = 1 if i % 2 else -1
            sz = rr[i] * 0.42
            axis = (inner[i] * 0.92 + side * s * 0.4).normalized()
            q = pts[i] + axis * rr[i] * 0.86
            cup = lathe([(0.0, -0.2), (0.85, 0.0), (1.0, 0.35), (0.7, 0.55), (0.45, 0.3), (0.0, 0.25)], 8, "z")
            rot = axis.to_track_quat("Z", "Y").to_matrix()
            for v in cup.verts: v.co = q + rot @ (v.co * sz)
            P.part(name, cup, lambda c, n, q=q, axis=axis, sz=sz: "Accent" if ((c - q) - axis * (c - q).dot(axis)).length < 0.62 * sz else "Belly", tuple(p0))
        if out.y > 0.9:   # the two front ones: ivory hooks between the sucker rows near the tip
            for i in range(N - 8, N - 3, 2):
                q = pts[i] + inner[i] * rr[i] * 0.8
                hk = bez(q, q + inner[i] * 0.07, q + inner[i] * 0.12 - tans[i] * 0.04, q + inner[i] * 0.11 - tans[i] * 0.1, 3)
                P.part(name, pipe(hk, [0.028, 0.02, 0.011, 0.0], 5), "Trim", tuple(p0))
        P.part(name, ball(tuple(pts[-1]), (0.05, 0.05, 0.05), 8, 4), "Glow", tuple(p0))   # a glowing lure at the tip
    P.part("Muzzle", ball(tuple(mz), (0.05, 0.03, 0.05), 8, 4), "Lamp", tuple(mz))   # in the throat, behind the beak
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


BOSSES = [("saucer", B_saucer), ("manta", B_manta), ("dragon", B_dragon), ("kraken", B_kraken), ("mothership", B_mothership)]

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for bid, fn in BOSSES:
        if ONLY and bid not in ONLY: continue
        fn().finish()
    print("DONE")
