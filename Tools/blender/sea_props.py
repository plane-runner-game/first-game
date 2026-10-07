# Sky Squad - the sea world's scenery (2026-10-07: "the first level's details, beautiful"): a destroyer, an aircraft carrier and a gull.
# Run: blender -b -P Tools/blender/sea_props.py -- Assets/_Game/Art/Sea export   (writes Destroyer.fbx, Carrier.fbx, Gull.fbx + previews)
# Blender axes: +Y = bow / beak, +Z = up. The waterline is z = 0. Unity maps the material slots by name (SceneBuilder.SeaDetails.cs).
import bpy, bmesh, math, sys, os
from mathutils import Vector, Matrix

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = argv[0] if argv else os.getcwd()
EXPORT = len(argv) > 1 and argv[1] == "export"

PAL = {
    "ShipGrey":   (0.55, 0.60, 0.64), "ShipDark":  (0.20, 0.22, 0.25), "ShipDeck": (0.30, 0.32, 0.34), "ShipRed": (0.55, 0.12, 0.10),
    "ShipWhite":  (0.92, 0.92, 0.90), "ShipGlass": (0.10, 0.18, 0.28), "ShipBlack": (0.06, 0.06, 0.07), "ShipYellow": (0.95, 0.75, 0.15),
    "GullWhite":  (0.95, 0.95, 0.93), "GullGrey":  (0.62, 0.66, 0.70), "GullBlack": (0.10, 0.10, 0.11), "GullBeak": (1.00, 0.70, 0.10),
}

def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    global MATS
    MATS = {}
    for k, c in PAL.items():
        m = bpy.data.materials.new(k); m.use_nodes = True
        b = m.node_tree.nodes.get("Principled BSDF"); b.inputs["Base Color"].default_value = (*c, 1); b.inputs["Roughness"].default_value = 0.6
        m.diffuse_color = (*c, 1); MATS[k] = m

def obj(name, bm, mat):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob)
    for k in PAL: me.materials.append(MATS[k])
    idx = list(PAL).index(mat)
    for p in me.polygons: p.material_index = idx
    return ob

def paint(ob, fn):
    keys = list(PAL)
    for p in ob.data.polygons:
        k = fn(p.center, p.normal)
        if k: p.material_index = keys.index(k)

def box(name, cx, cy, cz, sx, sy, sz, mat, taper=0.0):
    """a box centred (cx, cy, cz), full sizes sx, sy, sz; taper shrinks the top face in x and y by that fraction."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        if v.co.z > 0 and taper: v.co.x *= (1 - taper); v.co.y *= (1 - taper)
        v.co.x = v.co.x * sx + cx; v.co.y = v.co.y * sy + cy; v.co.z = v.co.z * sz + cz
    return obj(name, bm, mat)

def cyl(name, p0, p1, r, mat, seg=10):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r, depth=1.0)
    a, b = Vector(p0), Vector(p1); d = b - a
    rot = d.to_track_quat("Z", "Y").to_matrix().to_4x4()
    bmesh.ops.transform(bm, matrix=Matrix.Translation((a + b) / 2) @ rot @ Matrix.Diagonal((1, 1, d.length, 1)), verts=bm.verts)
    return obj(name, bm, mat)

def hull(name, length, beam, depth, deck, bow_rise=0.35, stern=0.75):
    """a ship's hull: U sections lofted stern to bow, the bow drawn to a point and lifted; deck at z = deck."""
    secs = []
    N = 12
    for i in range(N + 1):
        t = i / N                                   # 0 stern .. 1 bow
        y = (t - 0.5) * length
        w = beam * 0.5 * (stern + (1 - stern) * math.sin(min(1.0, t / 0.35) * math.pi / 2)) if t < 0.6 else beam * 0.5 * math.cos((t - 0.6) / 0.4 * math.pi / 2) ** 0.8
        w = max(w, 0.02)
        dz = deck + bow_rise * max(0.0, (t - 0.55) / 0.45) ** 2
        kz = -depth * (1.0 if t < 0.85 else max(0.15, 1 - (t - 0.85) / 0.15 * 0.85))
        sec = [(-w, dz), (-w * 0.98, 0.0), (-w * 0.80, kz * 0.6), (-w * 0.35, kz), (w * 0.35, kz), (w * 0.80, kz * 0.6), (w * 0.98, 0.0), (w, dz)]
        secs.append((y, sec))
    bm = bmesh.new(); loops = []
    for y, sec in secs: loops.append([bm.verts.new((u, y, v)) for (u, v) in sec])
    n = len(loops[0])
    for r0, r1 in zip(loops, loops[1:]):
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((r0[i], r0[j], r1[j], r1[i]))
    bm.faces.new(list(reversed(loops[0]))); bm.faces.new(loops[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = obj(name, bm, "ShipGrey")
    paint(ob, lambda c, nrm: "ShipDeck" if nrm.z > 0.7 else ("ShipRed" if c.z < -0.05 else ("ShipBlack" if c.z < 0.08 else "ShipGrey")))
    return ob

def join(parts, name):
    bpy.ops.object.select_all(action="DESELECT")
    for p in parts: p.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active; ob.name = name; ob.data.name = name
    return ob

def turret(px, py, pz, s, facing=1):
    parts = [box("Turret", px, py, pz + 0.18 * s, 0.55 * s, 0.70 * s, 0.36 * s, "ShipGrey", taper=0.25)]
    parts.append(cyl("Barrel", (px, py + facing * 0.2 * s, pz + 0.22 * s), (px, py + facing * 1.05 * s, pz + 0.26 * s), 0.05 * s, "ShipDark", 8))
    return parts

def export(ob, fname, extra=()):
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    for e in extra: e.select_set(True)
    bpy.ops.export_scene.fbx(filepath=os.path.join(OUT, fname), use_selection=True, object_types={"MESH", "EMPTY"},
                             apply_scale_options="FBX_SCALE_UNITS", axis_forward="Z", axis_up="Y", bake_space_transform=True,
                             mesh_smooth_type="FACE", add_leaf_bones=False)

def preview(fname, loc, target=(0, 0, 0)):
    sc = bpy.context.scene
    sc.view_settings.view_transform = "Standard"
    w = bpy.data.worlds.new("W"); sc.world = w; w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.25, 0.62, 0.78, 1)
    sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN")); sc.collection.objects.link(sun)
    sun.data.energy = 3.5; sun.rotation_euler = (math.radians(40), math.radians(15), math.radians(30))
    for eng in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
        try: sc.render.engine = eng; break
        except Exception: pass
    sc.render.resolution_x = 640; sc.render.resolution_y = 400
    cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam")); sc.collection.objects.link(cam); sc.camera = cam
    cam.location = loc; cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = os.path.join(OUT, fname); bpy.ops.render.render(write_still=True)

# =========================================================================== the destroyer: 14 long
reset()
P = [hull("Hull", 14.0, 1.9, 0.65, 0.55, bow_rise=0.35)]
P += turret(0, 4.3, 0.55, 1.0, 1) + turret(0, 3.2, 0.95, 0.9, 1) + turret(0, -5.0, 0.55, 1.0, -1)
P.append(box("Pedestal", 0, 3.2, 0.72, 0.6, 0.7, 0.35, "ShipGrey"))
P.append(box("Bridge", 0, 1.8, 1.05, 1.25, 1.6, 1.0, "ShipGrey", taper=0.08))
P.append(box("Windows", 0, 2.57, 1.38, 1.05, 0.06, 0.18, "ShipGlass"))
P.append(box("BridgeTop", 0, 1.7, 1.66, 0.9, 1.1, 0.25, "ShipGrey"))
P.append(box("Mast", 0, 1.4, 2.5, 0.12, 0.12, 1.6, "ShipDark"))
P.append(box("Yard", 0, 1.4, 2.9, 1.1, 0.08, 0.06, "ShipDark"))
P.append(box("Radar", 0, 1.4, 3.35, 0.7, 0.12, 0.18, "ShipDark"))
P.append(box("Funnel", 0, -0.6, 1.2, 0.8, 1.2, 1.3, "ShipGrey", taper=0.15))
P.append(box("FunnelTop", 0, -0.6, 1.92, 0.68, 1.02, 0.16, "ShipBlack"))
P.append(box("Deckhouse", 0, -2.5, 0.85, 1.1, 2.2, 0.6, "ShipGrey"))
P.append(box("Launcher", 0, -2.5, 1.3, 0.7, 0.9, 0.3, "ShipDark"))
for s in (1, -1): P.append(cyl("Boat", (s * 0.68, -1.3, 0.9), (s * 0.68, 0.2, 0.9), 0.16, "ShipWhite", 8))
dest = join(P, "Destroyer")
if EXPORT: export(dest, "Destroyer.fbx")
preview("destroyer.png", (11, 9, 6), (0, 0, 0.6))

# =========================================================================== the carrier: 26 long, a flight deck with an angled landing strip
reset()
P = [hull("Hull", 24.0, 3.4, 1.0, 1.25, bow_rise=0.0, stern=0.9)]
deck = box("FlightDeck", -0.2, 0.6, 1.45, 4.6, 26.0, 0.4, "ShipDeck")
P.append(deck)
P.append(box("Sponson", -2.2, -3.0, 1.45, 2.0, 9.0, 0.38, "ShipDeck"))     # the angled deck sticks out to port
# deck markings: a white centre line in dashes, edge lines, a yellow landing line along the angled deck
for i in range(9): P.append(box("Dash", 0.0, -10.5 + i * 2.8, 1.66, 0.12, 1.4, 0.02, "ShipWhite"))
for s in (1, -1): P.append(box("Edge", s * 2.05 - 0.2, 0.6, 1.66, 0.08, 25.0, 0.02, "ShipWhite"))
lane = box("LandLine", -1.4, -3.0, 1.665, 0.12, 14.0, 0.02, "ShipYellow"); lane.data.transform(Matrix.Translation((1.4, 3.0, 0)) @ Matrix.Rotation(math.radians(-9), 4, "Z") @ Matrix.Translation((-1.4, -3.0, 0))); P.append(lane)
P.append(box("Spot", 0.0, 9.5, 1.665, 1.6, 1.6, 0.02, "ShipYellow"))
P.append(box("Num", 0.0, -11.0, 1.665, 1.2, 0.9, 0.02, "ShipWhite"))
# the island, to starboard
P.append(box("Island", 1.75, 1.0, 2.6, 0.9, 4.2, 2.0, "ShipGrey", taper=0.05))
P.append(box("IslandWin", 1.75, 3.12, 3.15, 0.8, 0.06, 0.25, "ShipGlass"))
P.append(box("IslandWin2", 1.29, 1.0, 3.15, 0.04, 3.6, 0.22, "ShipGlass"))
P.append(box("IslandTop", 1.75, 0.8, 3.75, 0.7, 2.6, 0.3, "ShipGrey"))
P.append(box("Funnel", 1.75, -0.4, 3.8, 0.7, 1.0, 0.5, "ShipBlack"))
P.append(box("Mast", 1.75, 1.4, 4.6, 0.12, 0.12, 1.6, "ShipDark"))
P.append(box("Yard", 1.75, 1.4, 5.0, 1.1, 0.08, 0.06, "ShipDark"))
P.append(box("Radar", 1.75, 1.4, 5.5, 0.9, 0.12, 0.2, "ShipDark"))
carrier = join(P, "Carrier")
if EXPORT: export(carrier, "Carrier.fbx")
preview("carrier.png", (20, 16, 12), (0, 0, 1.0))

# =========================================================================== the gull: a body and two wings that flap about their roots
reset()
def ell(name, c, r, mat, seg=10, rings=6):
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=rings, radius=1.0)
    for v in bm.verts: v.co = Vector((c[0] + v.co.x * r[0], c[1] + v.co.y * r[1], c[2] + v.co.z * r[2]))
    ob = obj(name, bm, mat)
    for p in ob.data.polygons: p.use_smooth = True
    return ob
B = [ell("Body", (0, 0, 0), (0.16, 0.48, 0.15), "GullWhite"), ell("Head", (0, 0.42, 0.08), (0.12, 0.14, 0.12), "GullWhite"),
     ell("Tail", (0, -0.48, 0.02), (0.12, 0.16, 0.04), "GullGrey")]
bk = bmesh.new(); bmesh.ops.create_cone(bk, cap_ends=True, segments=6, radius1=0.045, radius2=0.0, depth=0.18)
bmesh.ops.transform(bk, matrix=Matrix.Translation((0, 0.62, 0.06)) @ Matrix.Rotation(math.radians(-90), 4, "X"), verts=bk.verts); B.append(obj("Beak", bk, "GullBeak"))
body = join(B, "Body")
wings = []
for s in (1, -1):
    bm = bmesh.new()
    # a gull wing: broad at the root, a crook at the wrist, a pointed black tip; root at x = 0
    pts = [(0.0, 0.18), (0.45, 0.20), (0.75, 0.06), (1.15, -0.10), (0.70, -0.16), (0.40, -0.08), (0.0, -0.18)]
    top = [bm.verts.new((s * x, y, 0.02)) for x, y in pts]; bot = [bm.verts.new((s * x, y, -0.02)) for x, y in pts]
    bm.faces.new(top if s > 0 else list(reversed(top))); bm.faces.new(list(reversed(bot)) if s > 0 else bot)
    for i in range(len(pts)):
        j = (i + 1) % len(pts); bm.faces.new((top[i], top[j], bot[j], bot[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    w = obj("WingR" if s > 0 else "WingL", bm, "GullGrey")
    paint(w, lambda c, n: "GullBlack" if abs(c.x) > 0.78 else "GullGrey")
    w.location = (s * 0.12, 0.02, 0.04)
    for v in w.data.vertices: v.co.x -= 0.0
    w.parent = body
    wings.append(w)
if EXPORT: export(body, "Gull.fbx", wings)
preview("gull.png", (2.2, 1.5, 1.6))
print("SEA PROPS done")
