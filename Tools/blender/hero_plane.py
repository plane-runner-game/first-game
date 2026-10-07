# Sky Squad hero plane (the plane every attempt starts on), built from code.
# Run: blender -b -P Tools/blender/hero_plane.py -- Assets/_Game/Art/Hero export   (writes HeroPlane.fbx + four preview renders)
# Blender axes: +Y = nose, +Z = up, +X = right wing.
# The look (2026-10-07, second pass: "bigger, longer, more of a warplane"): a twin-engine fighter in grey camouflage with a red nose
# band, red twin tails and red-tipped missiles on the wing tips, blue-white-red roundels on the wings, a gold canopy and two hot engines - from behind
# it reads as an "H" (the missiles) with a red "V" (the tails) over two glowing nozzles.
import bpy, bmesh, math, sys, os
from mathutils import Vector, Matrix

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = argv[0] if argv else os.getcwd()
EXPORT = len(argv) > 1 and argv[1] == "export"

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

# ---------------------------------------------------------------- materials (Unity maps them by name: SceneBuilder.Hero.cs owns the real colours)
PAL = {
    "HeroBody":  ((0.30, 0.37, 0.41, 1), 0.40, None),
    "HeroCamo":  ((0.15, 0.20, 0.22, 1), 0.35, None),
    "HeroBelly": ((0.62, 0.66, 0.69, 1), 0.40, None),
    "HeroRed":   ((0.80, 0.05, 0.05, 1), 0.50, None),
    "HeroWhite": ((0.92, 0.92, 0.92, 1), 0.45, None),
    "HeroGlass": ((0.95, 0.62, 0.12, 1), 0.92, None),
    "HeroDark":  ((0.06, 0.07, 0.09, 1), 0.30, None),
    "HeroGlow":  ((1.00, 0.45, 0.08, 1), 0.50, (1.0, 0.5, 0.1)),
    "HeroBlue":  ((0.05, 0.16, 0.45, 1), 0.45, None),
}
def make_mat(name, col, gloss, emit):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = col
    b.inputs["Roughness"].default_value = 1.0 - gloss
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = 6.0
    m.diffuse_color = col
    return m
MATS = {k: make_mat(k, *v) for k, v in PAL.items()}
ORDER = list(PAL.keys())
def mi(name): return ORDER.index(name)

def new_obj(name, bm):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me)
    scene.collection.objects.link(ob)
    for k in ORDER: me.materials.append(MATS[k])
    return ob

def subsurf(ob, levels):
    md = ob.modifiers.new("ss", "SUBSURF"); md.levels = levels; md.render_levels = levels
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.modifier_apply(modifier="ss")
    ob.select_set(False)

def smooth(ob):
    for p in ob.data.polygons: p.use_smooth = True

def paint(ob, fn):
    """fn(face_centre, face_normal) -> material name or None (keep)."""
    for p in ob.data.polygons:
        k = fn(p.center, p.normal)
        if k: p.material_index = mi(k)

def camo(c):
    """a soft splinter camouflage: dark patches where three crossing waves add up."""
    v = math.sin(c.x * 2.3 + c.y * 1.7) + 0.8 * math.sin(c.y * 3.1 - c.x * 1.3 + 1.0) + 0.4 * math.sin((c.x + c.y) * 4.7)
    return "HeroCamo" if v > 0.75 else "HeroBody"

# ---------------------------------------------------------------- lofts
def loft(rings, seg, close_start=True, close_end=True, sq=1.0):
    """rings along y: (y, a, b, cx, cz) -> a superellipse (exponent 2/sq: sq > 1 squares the section off) with half-sizes a, b."""
    bm = bmesh.new()
    loops = []
    for (t, a, b, c0, c1) in rings:
        ring = []
        for i in range(seg):
            ang = 2 * math.pi * i / seg
            ca, sa = math.cos(ang), math.sin(ang)
            u = c0 + a * math.copysign(abs(ca) ** (1.0 / sq), ca)
            v = c1 + b * math.copysign(abs(sa) ** (1.0 / sq), sa)
            ring.append(bm.verts.new((u, t, v)))
        loops.append(ring)
    for r0, r1 in zip(loops, loops[1:]):
        for i in range(seg):
            j = (i + 1) % seg
            bm.faces.new((r0[i], r0[j], r1[j], r1[i]))
    if close_start: bm.faces.new(list(reversed(loops[0])))
    if close_end: bm.faces.new(loops[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm

def sweep(sections, axis):
    """sections: (t, [(u, v)...]) closed polygons of equal length. axis 'x': point = (t, u, v); axis 'z': point = (v, u, t)."""
    bm = bmesh.new()
    loops = []
    for t, poly in sections:
        loops.append([bm.verts.new((t, u, v) if axis == "x" else (v, u, t)) for (u, v) in poly])
    n = len(loops[0])
    for r0, r1 in zip(loops, loops[1:]):
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((r0[i], r0[j], r1[j], r1[i]))
    bm.faces.new(list(reversed(loops[0]))); bm.faces.new(loops[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm

def airfoil(le, te, thick, z):
    c = le - te
    return [(le, z), (le - 0.15 * c, z + thick * 0.5), (le - 0.55 * c, z + thick * 0.42), (te, z + thick * 0.06),
            (te, z - thick * 0.06), (le - 0.55 * c, z - thick * 0.30), (le - 0.15 * c, z - thick * 0.36)]

parts = []

# ---------------------------------------------------------------- fuselage: long, pointed, flat-sided, wide at the back for two engines
FUS = [   # y, half-width, half-height, z centre
    (-2.20, 0.50, 0.27, 0.04),
    (-1.85, 0.56, 0.33, 0.04),
    (-1.10, 0.58, 0.40, 0.03),
    (-0.30, 0.55, 0.45, 0.01),
    ( 0.50, 0.45, 0.44, 0.00),
    ( 1.20, 0.34, 0.36, -0.02),
    ( 1.80, 0.24, 0.26, -0.04),
    ( 2.25, 0.13, 0.14, -0.06),
    ( 2.62, 0.02, 0.02, -0.07),
]
fus = new_obj("Fuselage", loft([(y, a, b, 0.0, z) for (y, a, b, z) in FUS], 20, close_start=True, close_end=True, sq=1.35))
subsurf(fus, 1); smooth(fus)
def fus_paint(c, n):
    if c.y > 2.05: return "HeroDark"                          # the radome
    if 1.72 < c.y < 2.00: return "HeroRed"                    # the red nose band: the squad's mark
    if c.z < -0.12: return "HeroBelly"                        # light underside
    return camo(c)
paint(fus, fus_paint)
parts.append(fus)

can = new_obj("Canopy", loft([
    (0.10, 0.04, 0.03, 0, 0.30),
    (0.35, 0.20, 0.17, 0, 0.36),
    (0.80, 0.25, 0.25, 0, 0.40),
    (1.25, 0.22, 0.22, 0, 0.36),
    (1.60, 0.12, 0.10, 0, 0.27),
    (1.75, 0.03, 0.02, 0, 0.22),
], 16))
subsurf(can, 1); smooth(can)
paint(can, lambda c, n: "HeroGlass")
parts.append(can)

# ---------------------------------------------------------------- two engines: dark nozzles, hot cores
for side in (1, -1):
    x = side * 0.25
    noz = new_obj("Nozzle", loft([(-2.05, 0.23, 0.22, x, 0.04), (-2.42, 0.21, 0.20, x, 0.04), (-2.44, 0.17, 0.16, x, 0.04), (-2.30, 0.16, 0.15, x, 0.04)],
                                 16, close_start=False, close_end=True))
    smooth(noz); paint(noz, lambda c, n: "HeroDark"); parts.append(noz)
    core = new_obj("Core", loft([(-2.29, 0.155, 0.145, x, 0.04), (-2.34, 0.09, 0.085, x, 0.04), (-2.36, 0.02, 0.02, x, 0.04)], 16, close_start=True, close_end=False))
    smooth(core); paint(core, lambda c, n: "HeroGlow"); parts.append(core)

# ---------------------------------------------------------------- intakes: boxy scoops on the shoulders
for side in (1, -1):
    ob = new_obj("Intake", loft([
        (0.55, 0.15, 0.20, side * 0.52, -0.02), (0.30, 0.17, 0.22, side * 0.53, -0.02), (-0.60, 0.15, 0.20, side * 0.50, -0.02), (-1.10, 0.04, 0.06, side * 0.45, -0.02)
    ], 12, sq=1.8))
    smooth(ob)
    paint(ob, lambda c, n: "HeroDark" if c.y > 0.50 else ("HeroBelly" if c.z < -0.12 else camo(c)))
    parts.append(ob)

# ---------------------------------------------------------------- wings: swept, clipped tips, a missile on each tip and one under each wing
WING = [  # x, leading edge, trailing edge, thickness
    (0.40, 0.82, -1.08, 0.20),
    (1.00, 0.26, -1.08, 0.15),
    (1.60, -0.30, -1.08, 0.11),
    (2.02, -0.62, -1.10, 0.08),
]
def wz(x): return -0.12 - (x - 0.40) * 0.03   # a touch of anhedral
def missile(x, z, y0, length, r, name):
    """a white missile with a red nose and four dark fins at the back, its tail at y0."""
    L = length
    bm = loft([(y0, r * 0.7, r * 0.7, x, z), (y0 + 0.05, r, r, x, z), (y0 + L * 0.78, r, r, x, z), (y0 + L * 0.92, r * 0.6, r * 0.6, x, z), (y0 + L, 0.01, 0.01, x, z)], 10)
    ob = new_obj(name, bm); smooth(ob)
    paint(ob, lambda c, n: "HeroRed" if c.y > y0 + L * 0.80 else ("HeroDark" if c.y < y0 + 0.04 else "HeroWhite"))
    parts.append(ob)
    for k in range(4):
        a = math.radians(45 + 90 * k)
        secs = [(0.0, airfoil(y0 + 0.30, y0 + 0.02, 0.03, 0.0)), (r * 2.2, airfoil(y0 + 0.12, y0 + 0.02, 0.02, 0.0))]
        fin = new_obj(name + "Fin", sweep(secs, "x"))
        paint(fin, lambda c, n: "HeroDark")
        fin.data.transform(Matrix.Rotation(a, 4, "Y"))
        fin.data.transform(Matrix.Translation((x, 0, z)))
        parts.append(fin)

for side in (1, -1):
    secs = [(side * x, airfoil(le, te, th, wz(x))) for (x, le, te, th) in WING]
    if side < 0: secs = list(reversed(secs))
    ob = new_obj("Wing", sweep(secs, "x"))
    subsurf(ob, 1); smooth(ob)
    paint(ob, lambda c, n: "HeroBelly" if n.z < -0.2 else camo(c))
    parts.append(ob)
    # the roundel: blue, white, red, floating just over the wing
    for (r, k, dz) in ((0.29, "HeroBlue", 0.075), (0.20, "HeroWhite", 0.080), (0.11, "HeroRed", 0.085)):
        cx, cy = side * 1.28, -0.56
        bm = bmesh.new()
        ring = [bm.verts.new((cx + r * math.cos(2 * math.pi * i / 20), cy + r * math.sin(2 * math.pi * i / 20), wz(1.30) + dz)) for i in range(20)]
        f = bm.faces.new(ring); f.normal_update()
        if f.normal.z < 0: f.normal_flip()
        d = new_obj("Roundel", bm); paint(d, lambda c, n, k=k: k); parts.append(d)
    missile(side * 1.93, wz(1.95) + 0.01, -1.25, 1.75, 0.08, "TipMissile")
    missile(side * 1.05, wz(1.05) - 0.24, -1.00, 1.45, 0.085, "WingMissile")
    py = new_obj("Pylon", sweep([(side * 1.03, airfoil(0.05, -0.75, 0.04, 0)), (side * 1.07, airfoil(0.05, -0.75, 0.04, 0))], "x"))
    py.data.transform(Matrix.Scale(1, 4)); paint(py, lambda c, n: "HeroDark")
    for v in py.data.vertices: v.co.z = wz(1.05) - (0.17 if v.co.z < 0 else 0.03)
    parts.append(py)

# ---------------------------------------------------------------- tail: two tall canted red fins, swept stabilisers
def fin(side):
    secs = [(h, airfoil(le, te, th, 0.0)) for (h, le, te, th) in
            [(0.0, -0.85, -2.05, 0.12), (0.55, -1.40, -2.12, 0.09), (1.05, -1.82, -2.20, 0.07), (1.15, -1.92, -2.20, 0.05)]]
    ob = new_obj("Fin", sweep(secs, "z"))
    subsurf(ob, 1); smooth(ob)
    paint(ob, lambda c, n: "HeroDark" if c.z > 0.92 else ("HeroWhite" if 0.42 < c.z < 0.56 else "HeroRed"))
    ob.data.transform(Matrix.Rotation(math.radians(side * 22), 4, "Y"))   # cant outward
    ob.data.transform(Matrix.Translation((side * 0.36, 0, 0.26)))
    parts.append(ob)
fin(1); fin(-1)

for side in (1, -1):
    secs = [(side * x, airfoil(le, te, th, 0.0)) for (x, le, te, th) in [(0.45, -1.35, -2.25, 0.10), (0.95, -1.80, -2.28, 0.07), (1.30, -2.10, -2.30, 0.05)]]
    if side < 0: secs = list(reversed(secs))
    ob = new_obj("Stab", sweep(secs, "x"))
    subsurf(ob, 1); smooth(ob)
    paint(ob, lambda c, n: "HeroBelly" if n.z < -0.2 else camo(c))
    parts.append(ob)

# ---------------------------------------------------------------- one object, origin at the centre
bpy.ops.object.select_all(action="DESELECT")
for p in parts: p.select_set(True)
bpy.context.view_layer.objects.active = parts[0]
bpy.ops.object.join()
hero = bpy.context.view_layer.objects.active
hero.name = "HeroPlane"; hero.data.name = "HeroPlane"
bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY", center="BOUNDS")
hero.location = (0, 0, 0)
tris = sum(len(p.vertices) - 2 for p in hero.data.polygons)
print("HERO tris", tris, "dims", tuple(round(d, 2) for d in hero.dimensions))

if EXPORT:
    bpy.ops.export_scene.fbx(filepath=os.path.join(OUT, "HeroPlane.fbx"), use_selection=True, object_types={"MESH"},
                             apply_scale_options="FBX_SCALE_UNITS", axis_forward="Z", axis_up="Y", bake_space_transform=True,
                             mesh_smooth_type="FACE", use_mesh_modifiers=True, add_leaf_bones=False)
    print("exported")

# ---------------------------------------------------------------- previews
scene.view_settings.view_transform = "Standard"
world = bpy.data.worlds.new("W"); scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (0.25, 0.62, 0.78, 1)
world.node_tree.nodes["Background"].inputs[1].default_value = 0.9
sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN")); scene.collection.objects.link(sun)
sun.data.energy = 3.5; sun.rotation_euler = (math.radians(40), math.radians(15), math.radians(30))
for eng in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
    try: scene.render.engine = eng; break
    except Exception: pass
scene.render.resolution_x = 640; scene.render.resolution_y = 480
cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam")); scene.collection.objects.link(cam); scene.camera = cam
cam.data.lens = 50
def shot(name, loc):
    cam.location = loc
    d = Vector((0, 0, 0)) - Vector(loc)
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    scene.render.filepath = os.path.join(OUT, name)
    bpy.ops.render.render(write_still=True)
shot("hero_back.png", (0, -12, 4.2))        # roughly the game's view: from behind and above
shot("hero_34.png", (8, 7, 4.5))
shot("hero_top.png", (0.01, 0, 13))
shot("hero_side.png", (12, 0, 0.6))
