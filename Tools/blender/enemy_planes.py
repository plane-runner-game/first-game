# Sky Squad enemy planes: one warplane per world, built from code (2026-10-10: "a different enemy plane for every level, military
# designs that suit the environment").
# Run: blender -b -P Tools/blender/enemy_planes.py -- <out dir> [export] [ids,comma,separated]
#      (the second plane of each world, "<id>2", lives in enemy_planes_b.py next to this file)
#      writes Enemy_<id>.fbx per plane (with "export") and a preview contact sheet enemy_sheet.png (+ one front view per plane).
# Blender axes: +Y = nose, +Z = up, +X = right wing. Each FBX holds "Body" (everything that does not move) and the spinning parts as their
# own objects with the origin on the hub: "Prop<n>" spin about the nose axis, "Rotor" about up, "TailRotor" about the wing axis
# (SceneBuilder.EnemyPlanes.cs makes the pivots). Material slots are "<id>_<Slot>": the colour comes from the file, the slot name says how
# it is shaded (Glass glossy, Metal metallic, Glow / Lamp emissive).
import bpy, bmesh, math, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mathutils import Vector, Matrix

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = argv[0] if argv else os.getcwd()
EXPORT = len(argv) > 1 and argv[1] == "export"
ONLY = argv[2].split(",") if len(argv) > 2 and argv[2] else None

# ================================================================= geometry helpers (bmesh builders; y = along the body)
def loft(rings, seg, cs=True, ce=True, sq=1.0):
    """rings along y: (y, a, b, cx, cz) -> superellipse sections (sq > 1 squares them off)."""
    bm = bmesh.new(); loops = []
    for (t, a, b, c0, c1) in rings:
        ring = []
        for i in range(seg):
            ang = 2 * math.pi * i / seg
            ca, sa = math.cos(ang), math.sin(ang)
            ring.append(bm.verts.new((c0 + a * math.copysign(abs(ca) ** (1.0 / sq), ca), t, c1 + b * math.copysign(abs(sa) ** (1.0 / sq), sa))))
        loops.append(ring)
    for r0, r1 in zip(loops, loops[1:]):
        for i in range(seg):
            j = (i + 1) % seg
            bm.faces.new((r0[i], r0[j], r1[j], r1[i]))
    if cs: bm.faces.new(list(reversed(loops[0])))
    if ce: bm.faces.new(loops[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm

def sweep(sections, axis):
    """sections: (t, [(u, v)...]); axis 'x': (t, u, v); axis 'z': (v, u, t)."""
    bm = bmesh.new(); loops = []
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

def lathe(profile, seg, axis="z", c=(0, 0, 0)):
    """profile (r, h) revolved about an axis through c; r == 0 makes a pole."""
    bm = bmesh.new(); rings = []
    def pt(r, h, a):
        u, v = r * math.cos(a), r * math.sin(a)
        if axis == "z": return (c[0] + u, c[1] + v, c[2] + h)
        if axis == "y": return (c[0] + u, c[1] + h, c[2] + v)
        return (c[0] + h, c[1] + u, c[2] + v)
    for (r, h) in profile:
        if r < 1e-5: rings.append([bm.verts.new(pt(0, h, 0))])
        else: rings.append([bm.verts.new(pt(r, h, 2 * math.pi * i / seg)) for i in range(seg)])
    for r0, r1 in zip(rings, rings[1:]):
        if len(r0) == 1 and len(r1) == 1: continue
        if len(r0) == 1:
            for i in range(seg): bm.faces.new((r0[0], r1[i], r1[(i + 1) % seg]))
        elif len(r1) == 1:
            for i in range(seg): bm.faces.new((r0[i], r1[0], r0[(i + 1) % seg]))
        else:
            for i in range(seg):
                j = (i + 1) % seg
                bm.faces.new((r0[i], r0[j], r1[j], r1[i]))
    if len(rings[0]) > 1: bm.faces.new(list(reversed(rings[0])))
    if len(rings[-1]) > 1: bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm

def box(c, s, rot=None):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * s[0], v.co.y * s[1], v.co.z * s[2]))
        if rot: v.co = rot @ v.co
        v.co += Vector(c)
    return bm

def hull(points):
    bm = bmesh.new()
    for p in points: bm.verts.new(p)
    bmesh.ops.convex_hull(bm, input=bm.verts)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm

def tube(y0, y1, r0, r1, x, z, seg=12, cs=True, ce=True):
    return loft([(y0, r0, r0, x, z), (y1, r1, r1, x, z)], seg, cs, ce)

def mirror_x(bm):
    out = bm.copy()
    for v in out.verts: v.co.x = -v.co.x
    bmesh.ops.reverse_faces(out, faces=out.faces)
    return out

# ================================================================= a plane being built
THICK = 1.3   # every body is stretched this much vertically before export

SLOTS = ["Base", "Belly", "Accent", "Trim", "Glass", "Dark", "Glow", "Metal", "Lamp"]

class Plane:
    def __init__(self, pid, pal):
        bpy.ops.wm.read_factory_settings(use_empty=True)
        self.id = pid; self.parts = []; self.spin = []
        self.mats = []
        for s in SLOTS:
            col, gloss = pal.get(s, ((1, 0, 1), 0.4))
            m = bpy.data.materials.new(pid + "_" + s); m.use_nodes = True
            b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
            b.inputs["Base Color"].default_value = (*col, 1)
            b.inputs["Roughness"].default_value = 1.0 - gloss
            if s == "Metal": b.inputs["Metallic"].default_value = 0.6
            if s in ("Glow", "Lamp"):
                b.inputs["Emission Color"].default_value = (*col, 1)
                b.inputs["Emission Strength"].default_value = 6.0 if s == "Glow" else 2.5
            m.diffuse_color = (*col, 1)
            self.mats.append(m)

    def obj(self, name, bm, paint="Base", ss=0, smooth=True, spin=None):
        """paint: a slot name, or fn(centre, normal) -> slot. spin: hub location for a spinning part (its own object)."""
        if spin is not None:
            for v in bm.verts: v.co -= Vector(spin)
        me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
        ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob)
        for m in self.mats: me.materials.append(m)
        if ss:
            md = ob.modifiers.new("ss", "SUBSURF"); md.levels = ss; md.render_levels = ss
            bpy.context.view_layer.objects.active = ob; ob.select_set(True)
            bpy.ops.object.modifier_apply(modifier="ss"); ob.select_set(False)
        for p in me.polygons:
            p.use_smooth = smooth
            k = paint(p.center + (Vector(spin) if spin is not None else Vector()), p.normal) if callable(paint) else paint
            if k: p.material_index = SLOTS.index(k)
        if spin is not None:
            ob.location = spin; self.spin.append(ob)
        else:
            self.parts.append(ob)
        return ob

    # ---- composite parts
    def wing(self, secs, paint=None, ss=1, name="Wing", mirror=True, top="Base"):
        """secs (x, le, te, thick, z) from root to tip on the right side; mirrored to the left."""
        paint = paint or (lambda c, n: "Belly" if n.z < -0.3 else top)
        bm = sweep([(x, airfoil(le, te, th, z)) for (x, le, te, th, z) in secs], "x")
        if mirror:
            self.obj(name + "L", mirror_x(bm), paint, ss)
        self.obj(name + "R", bm, paint, ss)

    def fin(self, secs, x=0.0, z=0.0, cant=0.0, paint="Base", ss=1, name="Fin"):
        """secs (h, le, te, thick) from root up; canted outward (degrees) toward the side of x."""
        bm = sweep([(h, airfoil(le, te, th, 0.0)) for (h, le, te, th) in secs], "z")
        sgn = 1 if x >= 0 else -1
        for v in bm.verts:
            v.co = Matrix.Rotation(math.radians(sgn * cant), 3, "Y") @ v.co
            v.co += Vector((x, 0, z))
        return self.obj(name, bm, paint, ss)

    def missile(self, x, z, y0, length, r, body="Trim", head="Accent", fins="Dark"):
        L = length
        bm = loft([(y0, r * 0.7, r * 0.7, x, z), (y0 + 0.04, r, r, x, z), (y0 + L * 0.8, r, r, x, z), (y0 + L * 0.93, r * 0.55, r * 0.55, x, z), (y0 + L, 0.01, 0.01, x, z)], 8)
        self.obj("Missile", bm, lambda c, n: head if c.y > y0 + L * 0.8 else body)
        for k in range(4):
            a = math.radians(45 + 90 * k)
            secs = [(0.0, airfoil(y0 + 0.22, y0 + 0.02, 0.025, 0.0)), (r * 2.2, airfoil(y0 + 0.1, y0 + 0.02, 0.02, 0.0))]
            fb = sweep(secs, "x")
            for v in fb.verts:
                v.co = Matrix.Rotation(a, 3, "Y") @ v.co
                v.co += Vector((x, 0, z))
            self.obj("MissileFin", fb, fins, 0, False)

    def prop(self, hub, radius, blades=3, axis="y", chord=0.13, blade="Dark", tip="Trim", spinner="Metal", spinner_len=0.35, name="Prop"):
        """a propeller / rotor as its own object, origin on the hub. axis y: spins about the nose; z: a rotor; x: a tail rotor."""
        bm = bmesh.new()
        def put(b2, m):
            for v in b2.verts: v.co = m @ v.co
            return b2
        parts = []
        for k in range(blades):
            a = 2 * math.pi * k / blades
            # a blade along +X in the plane perpendicular to Y (axis y); twisted a little
            bl = box((radius * 0.55, 0, 0), (radius * 0.9, chord * 0.18, chord))
            for v in bl.verts:
                tw = math.radians(28) * (1 - v.co.x / radius)
                v.co = Matrix.Rotation(tw, 3, "X") @ v.co
                if abs(v.co.x) > radius * 0.85: v.co.z *= 0.7
            put(bl, Matrix.Rotation(a, 3, "Y"))
            parts.append(bl)
        if spinner and spinner_len > 0:
            sp = lathe([(0.0, spinner_len), (radius * 0.12, spinner_len * 0.65), (radius * 0.17, spinner_len * 0.2), (radius * 0.17, -0.05), (0.0, -0.06)], 12, "y")
            parts.append(sp)
        # merge into one bmesh, keep which faces are blades / tips / spinner
        me_parts = []
        for i, p in enumerate(parts):
            me = bpy.data.meshes.new("tmp"); p.to_mesh(me); p.free(); me_parts.append((i, me))
        out = bmesh.new()
        for i, me in me_parts:
            out.from_mesh(me)
            bpy.data.meshes.remove(me)
        # orient: built about Y; rotor about Z, tail rotor about X
        if axis == "z": rot = Matrix.Rotation(math.radians(-90), 3, "X")
        elif axis == "x": rot = Matrix.Rotation(math.radians(-90), 3, "Z")
        else: rot = Matrix.Identity(3)
        for v in out.verts: v.co = rot @ v.co + Vector(hub)
        cen = Vector(hub)
        def paint(c, n):
            d = (c - cen).length
            if spinner and d < radius * 0.2: return spinner
            return tip if d > radius * 0.8 else blade
        n = len(self.spin)
        nm = name if name.startswith("Rotor") or name.startswith("TailRotor") else "Prop" + str(n)
        return self.obj(nm, out, paint, 0, False, spin=hub)

    # ---- finish: one Body, everything centred, export + previews
    def finish(self):
        bpy.ops.object.select_all(action="DESELECT")
        for p in self.parts: p.select_set(True)
        bpy.context.view_layer.objects.active = self.parts[0]
        bpy.ops.object.join()
        body = bpy.context.view_layer.objects.active
        body.name = "Body"; body.data.name = self.id + "_Body"
        # thicker top to bottom (2026-10-10: "they are too thin on the Y axis, a bit wider"): the body only, the hubs follow, the blades keep their shape
        body.data.transform(Matrix.Scale(THICK, 4, Vector((0, 0, 1))))
        for s in self.spin: s.location.z *= THICK
        # centre on the bounds of everything (body + spinners)
        pts = [body.matrix_world @ v.co for v in body.data.vertices]
        for s in self.spin: pts += [s.matrix_world @ v.co for v in s.data.vertices]
        lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
        hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
        c = (lo + hi) * 0.5
        body.data.transform(Matrix.Translation(-c))
        for s in self.spin: s.location -= c
        tris = sum(len(p.vertices) - 2 for p in body.data.polygons) + sum(sum(len(p.vertices) - 2 for p in s.data.polygons) for s in self.spin)
        print("PLANE", self.id, "tris", tris, "size", tuple(round(d, 2) for d in (hi - lo)))
        self.body = body
        if EXPORT:
            bpy.ops.object.select_all(action="DESELECT")
            body.select_set(True)
            for s in self.spin: s.select_set(True)
            bpy.ops.export_scene.fbx(filepath=os.path.join(OUT, "Enemy_" + self.id + ".fbx"), use_selection=True, object_types={"MESH"},
                                     apply_scale_options="FBX_SCALE_UNITS", axis_forward="Z", axis_up="Y", bake_space_transform=True,
                                     mesh_smooth_type="FACE", use_mesh_modifiers=True, add_leaf_bones=False)
        self.preview()

    def preview(self):
        scene = bpy.context.scene
        scene.view_settings.view_transform = "Standard"
        world = bpy.data.worlds.new("W"); scene.world = world; world.use_nodes = True
        bg = next(n for n in world.node_tree.nodes if n.type == "BACKGROUND")
        bg.inputs[0].default_value = (0.42, 0.62, 0.78, 1); bg.inputs[1].default_value = 0.8
        sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN")); scene.collection.objects.link(sun)
        sun.data.energy = 3.2; sun.rotation_euler = (math.radians(40), math.radians(15), math.radians(150))
        try: scene.render.engine = "BLENDER_EEVEE_NEXT"
        except TypeError:
            try: scene.render.engine = "BLENDER_EEVEE"
            except TypeError: pass
        scene.render.resolution_x = 400; scene.render.resolution_y = 300
        cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam")); scene.collection.objects.link(cam); scene.camera = cam
        cam.data.lens = 50
        def shot(fn, loc):
            cam.location = loc
            cam.rotation_euler = (Vector((0, 0, 0)) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
            scene.render.filepath = os.path.join(OUT, fn)
            bpy.ops.render.render(write_still=True)
        shot("prev_%s_front.png" % self.id, (0, 15, 4.2))       # the player's view: it flies at you, seen a little from above
        shot("prev_%s_34.png" % self.id, (9, 9, 5.5))

# ================================================================= the fourteen
def P_sea():
    """World 1, the navy: a carrier fighter (F-14 style) - two engines under a flat 'pancake' body, swept wings, twin navy tails."""
    P = Plane("sea", {"Base": ((0.60, 0.65, 0.70), 0.45), "Belly": ((0.86, 0.88, 0.90), 0.4), "Accent": ((0.10, 0.18, 0.40), 0.5),
                      "Trim": ((0.96, 0.78, 0.15), 0.5), "Glass": ((0.18, 0.32, 0.42), 0.92), "Dark": ((0.07, 0.08, 0.10), 0.35),
                      "Glow": ((1.0, 0.5, 0.15), 0.5), "Metal": ((0.45, 0.47, 0.5), 0.5)})
    P.obj("Nose", loft([(2.75, 0.02, 0.02, 0, 0.12), (2.45, 0.15, 0.14, 0, 0.12), (1.9, 0.27, 0.26, 0, 0.13), (1.2, 0.34, 0.33, 0, 0.14),
                        (0.5, 0.38, 0.34, 0, 0.12), (-0.3, 0.36, 0.28, 0, 0.1)], 16, sq=1.2), lambda c, n: "Accent" if c.y > 2.35 else ("Belly" if c.z < 0.0 else "Base"), 1)
    P.obj("Pancake", loft([(0.7, 0.42, 0.18, 0, 0.05), (0.2, 0.98, 0.2, 0, 0.05), (-1.6, 1.0, 0.2, 0, 0.05), (-2.25, 0.82, 0.16, 0, 0.06)], 16, sq=2.2),
          lambda c, n: "Belly" if n.z < -0.3 else "Base", 1)
    for s in (1, -1):
        x = s * 0.55
        P.obj("Nacelle", loft([(0.75, 0.24, 0.25, x, -0.12), (0.3, 0.26, 0.27, x, -0.12), (-2.3, 0.24, 0.24, x, -0.1), (-2.65, 0.21, 0.21, x, -0.1)], 14, sq=1.4),
              lambda c, n: "Dark" if c.y > 0.7 or c.y < -2.6 else ("Belly" if n.z < -0.3 else "Base"), 1)
        P.obj("Core", tube(-2.6, -2.66, 0.17, 0.05, x, -0.1, 12), "Glow")
        P.missile(s * 0.28, -0.32, -1.6, 1.3, 0.07, "Belly", "Accent")
    P.wing([(0.9, 0.15, -1.15, 0.12, 0.1), (1.8, -0.55, -1.3, 0.08, 0.1), (2.75, -1.35, -1.75, 0.05, 0.1)],
           lambda c, n: "Belly" if n.z < -0.3 else ("Accent" if abs(c.x) > 2.45 else "Base"))
    for s in (1, -1):
        P.fin([(0.0, -1.0, -2.35, 0.11), (0.85, -1.75, -2.45, 0.08), (1.1, -1.95, -2.45, 0.06)], s * 0.62, 0.22, 10,
              lambda c, n: "Trim" if c.z > 1.05 else "Accent")
    P.wing([(0.9, -1.75, -2.55, 0.08, 0.05), (1.75, -2.25, -2.6, 0.05, 0.05)], name="Stab")
    P.obj("Canopy", loft([(0.6, 0.05, 0.04, 0, 0.42), (0.9, 0.19, 0.17, 0, 0.46), (1.5, 0.22, 0.22, 0, 0.5), (2.0, 0.17, 0.16, 0, 0.44), (2.25, 0.04, 0.03, 0, 0.38)], 14), "Glass", 1)
    return P

def P_lava():
    """World 2, the lava: a forward-swept black interceptor (Su-47 style) whose leading edges and spine glow like magma."""
    P = Plane("lava", {"Base": ((0.13, 0.12, 0.12), 0.35), "Belly": ((0.22, 0.17, 0.14), 0.3), "Accent": ((0.55, 0.08, 0.03), 0.45),
                       "Trim": ((0.35, 0.33, 0.32), 0.5), "Glass": ((0.95, 0.42, 0.06), 0.92), "Dark": ((0.04, 0.04, 0.04), 0.3),
                       "Glow": ((1.0, 0.36, 0.04), 0.5), "Metal": ((0.32, 0.30, 0.29), 0.5)})
    P.obj("Fuselage", loft([(2.8, 0.02, 0.02, 0, 0.05), (2.4, 0.16, 0.13, 0, 0.06), (1.7, 0.3, 0.26, 0, 0.08), (0.8, 0.38, 0.32, 0, 0.08),
                            (-0.6, 0.34, 0.3, 0, 0.06), (-1.9, 0.24, 0.22, 0, 0.05), (-2.35, 0.12, 0.12, 0, 0.05)], 16, sq=1.35),
          lambda c, n: "Accent" if c.y > 2.3 else ("Belly" if n.z < -0.4 else "Base"), 1)
    for s in (1, -1):
        x = s * 0.45
        P.obj("Nacelle", loft([(0.9, 0.2, 0.22, x, -0.12), (0.5, 0.22, 0.24, x, -0.12), (-2.3, 0.21, 0.21, x, -0.08), (-2.6, 0.19, 0.19, x, -0.08)], 12, sq=1.6),
              lambda c, n: "Glow" if c.y > 0.86 else ("Dark" if c.y < -2.5 else ("Belly" if n.z < -0.3 else "Base")), 1)
        P.obj("Core", tube(-2.56, -2.62, 0.15, 0.04, x, -0.08, 12), "Glow")
    glow_le = lambda c, n: "Glow" if n.y > 0.55 else ("Belly" if n.z < -0.3 else "Base")
    P.wing([(0.6, 0.35, -1.45, 0.13, 0.0), (1.6, 0.5, -0.55, 0.09, 0.02), (2.65, 0.85, 0.3, 0.05, 0.06)], glow_le)
    P.wing([(0.3, 1.75, 1.1, 0.06, 0.12), (0.95, 1.3, 1.05, 0.04, 0.14)], glow_le, name="Canard")
    P.wing([(0.55, -1.75, -2.45, 0.06, -0.02), (1.3, -2.2, -2.55, 0.04, -0.02)], glow_le, name="Stab")
    for s in (1, -1):
        P.fin([(0.0, -1.1, -2.3, 0.1), (0.8, -1.7, -2.35, 0.07), (1.0, -1.85, -2.35, 0.05)], s * 0.48, 0.12, 18,
              lambda c, n: "Glow" if n.y > 0.55 else ("Accent" if c.z > 0.85 else "Base"))
    P.obj("Spine", box((0, -0.6, 0.39), (0.06, 2.2, 0.04)), "Glow", 0, False)
    P.obj("Canopy", loft([(0.9, 0.04, 0.03, 0, 0.3), (1.2, 0.17, 0.16, 0, 0.36), (1.7, 0.19, 0.2, 0, 0.4), (2.1, 0.12, 0.12, 0, 0.34), (2.3, 0.03, 0.02, 0, 0.28)], 14), "Glass", 1)
    return P

def P_alien():
    """World 3, the alien planet: a saucer interceptor - a violet disc with a glowing dome, forward claws and two plasma cannons."""
    P = Plane("alien", {"Base": ((0.30, 0.23, 0.46), 0.55), "Belly": ((0.16, 0.12, 0.26), 0.45), "Accent": ((0.55, 0.95, 0.88), 0.6),
                        "Trim": ((0.72, 0.70, 0.84), 0.6), "Glass": ((0.2, 1.0, 0.88), 0.9), "Dark": ((0.06, 0.05, 0.10), 0.4),
                        "Glow": ((0.2, 1.0, 0.85), 0.5), "Metal": ((0.5, 0.5, 0.62), 0.6), "Lamp": ((0.35, 1.0, 0.9), 0.8)})
    P.obj("Disc", lathe([(0.0, 0.3), (0.55, 0.27), (1.05, 0.13), (1.35, 0.0), (1.1, -0.13), (0.55, -0.22), (0.0, -0.26)], 28, "z", (0, -0.2, 0)),
          lambda c, n: "Trim" if abs(c.z) < 0.07 else ("Belly" if c.z < 0 else "Base"), 1)
    P.obj("Dome", lathe([(0.0, 0.66), (0.24, 0.62), (0.42, 0.5), (0.52, 0.3), (0.5, 0.24)], 20, "z", (0, 0.05, 0)), "Lamp", 1)
    for k in range(12):
        a = 2 * math.pi * (k + 0.5) / 12
        P.obj("RimLight", box((1.37 * math.cos(a), -0.2 + 1.37 * math.sin(a), 0.0), (0.1, 0.1, 0.06), Matrix.Rotation(a, 3, "Z")), "Glow", 0, False)
    P.wing([(0.95, 0.75, -0.75, 0.16, 0.0), (1.8, 1.25, 0.25, 0.1, 0.05), (2.35, 1.95, 1.4, 0.06, 0.12), (2.45, 2.25, 1.95, 0.04, 0.16)],
           lambda c, n: "Glow" if abs(c.x) > 2.25 else ("Belly" if n.z < -0.3 else "Base"), name="Claw")
    for s in (1, -1):
        x = s * 0.55
        P.obj("Cannon", loft([(0.6, 0.13, 0.13, x, -0.24), (1.6, 0.1, 0.1, x, -0.24), (2.1, 0.07, 0.07, x, -0.24), (2.25, 0.09, 0.09, x, -0.24)], 10),
              lambda c, n: "Glow" if c.y > 2.05 else "Metal", 1)
        P.obj("Pod", loft([(-0.9, 0.2, 0.18, x, 0.05), (-1.6, 0.22, 0.2, x, 0.05), (-1.95, 0.16, 0.14, x, 0.05)], 12),
              lambda c, n: "Glow" if c.y < -1.85 else "Dark", 1)
    P.fin([(0.0, -0.7, -1.65, 0.09), (0.55, -1.25, -1.75, 0.06), (0.65, -1.4, -1.75, 0.04)], 0.0, 0.18, 0, lambda c, n: "Glow" if c.z > 0.7 else "Base")
    return P

def P_meadow():
    """World 4, the meadow: a WWI-style fighter biplane - olive wings with linen undersides, a red cowl, wooden struts, twin guns."""
    P = Plane("meadow", {"Base": ((0.36, 0.45, 0.18), 0.35), "Belly": ((0.86, 0.80, 0.62), 0.3), "Accent": ((0.78, 0.13, 0.08), 0.5),
                         "Trim": ((0.48, 0.30, 0.13), 0.4), "Glass": ((0.6, 0.8, 0.9), 0.9), "Dark": ((0.08, 0.08, 0.08), 0.3),
                         "Glow": ((1.0, 0.6, 0.2), 0.5), "Metal": ((0.58, 0.58, 0.6), 0.6)})
    P.obj("Fuselage", loft([(2.15, 0.33, 0.33, 0, 0.0), (1.9, 0.38, 0.38, 0, 0.0), (0.8, 0.36, 0.42, 0, 0.03), (-1.0, 0.24, 0.3, 0, 0.06), (-2.35, 0.05, 0.08, 0, 0.12)], 14, sq=1.5),
          lambda c, n: "Accent" if c.y > 1.55 else ("Belly" if c.z < -0.15 else "Base"), 1)
    P.obj("CowlFace", lathe([(0.0, 2.2), (0.24, 2.18), (0.3, 2.12)], 14, "y"), "Metal", 0)
    P.obj("UpperWing", sweep([(x, airfoil(1.05, 0.1, 0.09, 0.95 + abs(x) * 0.03)) for x in (-2.55, -2.2, -0.3, 0.3, 2.2, 2.55)], "x"),
          lambda c, n: "Belly" if n.z < -0.3 else ("Accent" if abs(c.x) > 2.25 else "Base"), 1)
    P.obj("LowerWing", sweep([(x, airfoil(0.85, -0.05, 0.08, -0.38 + abs(x) * 0.04)) for x in (-2.3, -2.0, -0.3, 0.3, 2.0, 2.3)], "x"),
          lambda c, n: "Belly" if n.z < -0.3 else "Base", 1)
    for s in (1, -1):
        for y in (0.8, 0.2):
            P.obj("Strut", box((s * 1.6, y, 0.27), (0.05, 0.08, 1.25), Matrix.Rotation(math.radians(s * -6), 3, "Y")), "Trim", 0, False)
        P.obj("Cabane", box((s * 0.24, 0.75, 0.7), (0.04, 0.05, 0.55), Matrix.Rotation(math.radians(s * -20), 3, "Y")), "Trim", 0, False)
        P.obj("Gear", box((s * 0.3, 1.05, -0.6), (0.04, 0.05, 0.6), Matrix.Rotation(math.radians(s * 20), 3, "Y")), "Trim", 0, False)
        P.obj("Wheel", lathe([(0.0, -0.06), (0.22, -0.06), (0.26, -0.02), (0.26, 0.02), (0.22, 0.06), (0.0, 0.06)], 14, "x", (s * 0.48, 1.05, -0.85)), "Dark", 0)
        P.obj("Gun", tube(1.0, 2.0, 0.045, 0.04, s * 0.12, 0.42, 8), "Dark", 0)
    P.obj("Axle", box((0, 1.05, -0.85), (0.96, 0.05, 0.05)), "Dark", 0, False)
    P.wing([(0.08, -1.8, -2.35, 0.06, 0.12), (1.0, -1.95, -2.35, 0.04, 0.12)], name="Stab")
    P.fin([(0.0, -1.7, -2.4, 0.06), (0.65, -2.0, -2.45, 0.05), (0.75, -2.15, -2.45, 0.04)], 0.0, 0.15, 0, lambda c, n: "Accent" if c.y < -2.1 else "Base")
    P.obj("Screen", box((0, 0.55, 0.47), (0.3, 0.03, 0.14), Matrix.Rotation(math.radians(-25), 3, "X")), "Glass", 0, False)
    P.obj("Cockpit", loft([(0.45, 0.2, 0.08, 0, 0.42), (-0.3, 0.2, 0.08, 0, 0.42)], 12), "Dark", 0)
    P.prop((0, 2.3, 0.0), 0.85, 2, chord=0.14, blade="Trim", tip="Trim", spinner="Accent", spinner_len=0.25)
    return P

def P_autumn():
    """World 5, the autumn forest: a twin-boom heavy fighter (P-38 style) in rust and tan - a glass pod between two engine booms."""
    P = Plane("autumn", {"Base": ((0.62, 0.30, 0.10), 0.4), "Belly": ((0.84, 0.74, 0.56), 0.35), "Accent": ((0.30, 0.19, 0.09), 0.4),
                         "Trim": ((0.96, 0.74, 0.22), 0.5), "Glass": ((0.35, 0.48, 0.45), 0.92), "Dark": ((0.07, 0.07, 0.07), 0.3),
                         "Glow": ((1.0, 0.55, 0.2), 0.5), "Metal": ((0.55, 0.55, 0.57), 0.6)})
    P.obj("Pod", loft([(2.05, 0.06, 0.06, 0, 0.0), (1.8, 0.22, 0.22, 0, 0.0), (1.0, 0.33, 0.35, 0, 0.04), (-0.3, 0.32, 0.33, 0, 0.04), (-1.0, 0.12, 0.14, 0, 0.06)], 14),
          lambda c, n: "Accent" if c.y > 1.75 else ("Belly" if c.z < -0.12 else "Base"), 1)
    P.obj("Canopy", loft([(0.0, 0.05, 0.04, 0, 0.28), (0.3, 0.2, 0.2, 0, 0.32), (0.9, 0.22, 0.24, 0, 0.34), (1.3, 0.14, 0.14, 0, 0.3), (1.45, 0.03, 0.03, 0, 0.26)], 14), "Glass", 1)
    for s in (1, -1):
        x = s * 1.05
        P.obj("Boom", loft([(1.95, 0.24, 0.24, x, 0.0), (1.5, 0.3, 0.33, x, 0.02), (0.4, 0.3, 0.35, x, 0.04), (-0.6, 0.18, 0.2, x, 0.06), (-2.2, 0.11, 0.12, x, 0.08), (-2.5, 0.07, 0.08, x, 0.08)], 14),
              lambda c, n: "Belly" if c.z < -0.12 else "Base", 1)
        P.obj("Turbo", loft([(0.3, 0.06, 0.04, x, 0.32), (0.1, 0.12, 0.09, x, 0.36), (-0.5, 0.11, 0.08, x, 0.32), (-0.8, 0.04, 0.03, x, 0.24)], 10), "Metal", 1)
        P.fin([(-0.25, -1.95, -2.55, 0.06), (0.0, -1.85, -2.6, 0.08), (0.55, -1.9, -2.55, 0.07), (0.7, -2.05, -2.45, 0.05)], x, 0.08, 0, lambda c, n: "Trim" if c.z > 0.62 else "Base")
        P.prop((x, 2.05, 0.0), 0.72, 3, spinner="Trim")
        for g in (-0.07, 0.07):
            P.obj("Gun", tube(1.6, 2.35, 0.03, 0.03, g, 0.05 + (0.06 if g > 0 else -0.06), 6), "Dark", 0)
    P.wing([(0.25, 0.85, -0.4, 0.15, -0.02), (1.3, 0.82, -0.35, 0.13, 0.0), (2.6, 0.55, 0.0, 0.07, 0.05), (2.85, 0.42, 0.08, 0.05, 0.06)],
           lambda c, n: "Belly" if n.z < -0.3 else ("Trim" if abs(c.x) > 2.62 else "Base"))
    P.obj("Stab", sweep([(x, airfoil(-1.95, -2.4, 0.06, 0.12)) for x in (-1.3, -1.05, 1.05, 1.3)], "x"), lambda c, n: "Belly" if n.z < -0.3 else "Base", 1)
    return P

def P_camping():
    """World 6, the night camp: a black attack helicopter (Apache style) with an amber-lit tandem cockpit, rocket pods and a searchlight."""
    P = Plane("camping", {"Base": ((0.11, 0.13, 0.17), 0.4), "Belly": ((0.17, 0.19, 0.23), 0.35), "Accent": ((0.27, 0.33, 0.22), 0.4),
                          "Trim": ((0.96, 0.72, 0.25), 0.5), "Glass": ((1.0, 0.68, 0.25), 0.9), "Dark": ((0.04, 0.04, 0.05), 0.3),
                          "Glow": ((1.0, 0.85, 0.5), 0.5), "Metal": ((0.36, 0.38, 0.42), 0.6), "Lamp": ((1.0, 0.62, 0.2), 0.9)})
    P.obj("Fuselage", loft([(2.05, 0.06, 0.08, 0, -0.08), (1.8, 0.2, 0.28, 0, -0.02), (1.1, 0.28, 0.4, 0, 0.04), (0.1, 0.35, 0.46, 0, 0.06),
                            (-0.6, 0.3, 0.4, 0, 0.12), (-1.1, 0.13, 0.17, 0, 0.24), (-2.9, 0.08, 0.1, 0, 0.3)], 14, sq=1.5),
          lambda c, n: "Belly" if c.z < -0.2 else "Base", 1)
    P.obj("CanopyFront", loft([(1.2, 0.14, 0.05, 0, 0.3), (1.45, 0.2, 0.16, 0, 0.34), (1.8, 0.12, 0.08, 0, 0.18)], 12), "Lamp", 1)
    P.obj("CanopyRear", loft([(0.45, 0.16, 0.06, 0, 0.45), (0.75, 0.22, 0.18, 0, 0.5), (1.15, 0.16, 0.1, 0, 0.42)], 12), "Lamp", 1)
    for s in (1, -1):
        x = s * 0.44
        P.obj("Engine", loft([(0.45, 0.13, 0.13, x, 0.38), (0.2, 0.17, 0.17, x, 0.4), (-0.6, 0.16, 0.16, x, 0.4), (-0.85, 0.11, 0.11, x, 0.4)], 12),
              lambda c, n: "Dark" if c.y > 0.4 or c.y < -0.8 else "Base", 1)
        P.obj("Pod", loft([(0.55, 0.06, 0.06, s * 0.95, -0.25), (0.45, 0.13, 0.13, s * 0.95, -0.25), (-0.45, 0.13, 0.13, s * 0.95, -0.25), (-0.5, 0.1, 0.1, s * 0.95, -0.25)], 10),
              lambda c, n: "Dark" if c.y > 0.5 else "Accent", 1)
        P.missile(s * 0.62, -0.25, -0.5, 1.05, 0.06, "Accent", "Trim")
        P.obj("Wheel", lathe([(0.0, -0.05), (0.14, -0.05), (0.15, 0.0), (0.14, 0.05), (0.0, 0.05)], 10, "x", (s * 0.42, 1.2, -0.62)), "Dark", 0)
        P.obj("Leg", box((s * 0.36, 1.2, -0.45), (0.04, 0.05, 0.34)), "Metal", 0, False)
    P.wing([(0.3, 0.3, -0.2, 0.09, -0.08), (1.05, 0.25, -0.15, 0.07, -0.12)], name="Stub")
    P.obj("MastBox", box((0, 0.05, 0.6), (0.28, 0.5, 0.16)), "Base", 0, False)
    P.obj("Turret", lathe([(0.0, -0.36), (0.12, -0.32), (0.13, -0.24), (0.0, -0.2)], 10, "z", (0, 1.7, 0)), "Dark", 0)
    P.obj("Cannon", tube(1.7, 2.35, 0.035, 0.03, 0, -0.29, 8), "Dark", 0)
    P.obj("Searchlight", lathe([(0.0, 0.0), (0.09, 0.0), (0.09, 0.05), (0.0, 0.06)], 12, "y", (0, 2.0, -0.18)), "Glow", 0)
    P.fin([(0.0, -2.45, -3.0, 0.08), (0.75, -2.75, -3.1, 0.06), (0.85, -2.85, -3.1, 0.05)], 0.0, 0.3, 0, "Base")
    P.wing([(0.05, -2.6, -2.95, 0.05, 0.32), (0.6, -2.65, -2.95, 0.04, 0.32)], name="Stab")
    P.prop((0, 0.05, 0.82), 1.65, 4, axis="z", chord=0.15, blade="Dark", tip="Trim", spinner="Metal", spinner_len=0.18, name="Rotor")
    P.prop((0.13, -2.95, 0.85), 0.36, 4, axis="x", chord=0.07, blade="Dark", tip="Trim", spinner=None, spinner_len=0, name="TailRotor")
    return P

def P_christmas():
    """World 7, the Christmas village: a swept-wing jet (MiG-15 style) in silver and white, red nose ring and tail, green tanks."""
    P = Plane("christmas", {"Base": ((0.86, 0.88, 0.91), 0.55), "Belly": ((0.74, 0.77, 0.81), 0.5), "Accent": ((0.82, 0.08, 0.10), 0.55),
                            "Trim": ((0.10, 0.48, 0.22), 0.5), "Glass": ((0.28, 0.45, 0.62), 0.92), "Dark": ((0.06, 0.06, 0.08), 0.3),
                            "Glow": ((1.0, 0.55, 0.2), 0.5), "Metal": ((0.62, 0.64, 0.68), 0.6)})
    P.obj("Fuselage", loft([(2.35, 0.33, 0.34, 0, 0.0), (2.05, 0.41, 0.43, 0, 0.0), (1.0, 0.46, 0.5, 0, 0.03), (0.0, 0.44, 0.48, 0, 0.04),
                            (-1.0, 0.36, 0.38, 0, 0.05), (-2.0, 0.25, 0.26, 0, 0.05), (-2.3, 0.23, 0.23, 0, 0.05)], 18, cs=False),
          lambda c, n: "Accent" if c.y > 1.95 else ("Belly" if c.z < -0.2 else "Base"), 1)
    P.obj("Intake", lathe([(0.32, 2.3), (0.0, 2.05)], 18, "y"), "Dark", 0)
    P.obj("Splitter", box((0, 2.25, 0.0), (0.04, 0.3, 0.6)), "Metal", 0, False)
    P.obj("Core", tube(-2.28, -2.35, 0.19, 0.05, 0, 0.05, 14), "Glow")
    P.wing([(0.4, 0.75, -0.55, 0.15, -0.06), (1.4, 0.05, -0.85, 0.1, -0.12), (2.4, -0.62, -1.12, 0.06, -0.18)],
           lambda c, n: "Belly" if n.z < -0.3 else ("Accent" if abs(c.x) > 2.15 else "Base"))
    for s in (1, -1):
        for xf in (1.0, 1.75):
            P.obj("Fence", box((s * xf, -0.25 - (xf - 1.0) * 0.6, -0.02), (0.02, 0.85, 0.12)), "Metal", 0, False)
        P.obj("Tank", loft([(0.4, 0.02, 0.02, s * 1.35, -0.4), (0.15, 0.13, 0.13, s * 1.35, -0.4), (-0.75, 0.13, 0.13, s * 1.35, -0.4), (-1.1, 0.02, 0.02, s * 1.35, -0.4)], 10),
              lambda c, n: "Accent" if c.y > 0.22 else "Trim", 1)
    P.fin([(0.0, -0.95, -2.3, 0.12), (0.9, -1.75, -2.45, 0.08), (1.35, -2.15, -2.55, 0.06)], 0.0, 0.3, 0, "Accent")
    P.obj("TStab", sweep([(x, airfoil(-1.95 - abs(x) * 0.25, -2.5 - abs(x) * 0.05, 0.06, 1.55)) for x in (-0.9, -0.1, 0.1, 0.9)], "x"), "Trim", 1)
    P.obj("Canopy", loft([(0.75, 0.05, 0.04, 0, 0.38), (1.0, 0.22, 0.2, 0, 0.44), (1.45, 0.24, 0.24, 0, 0.48), (1.8, 0.14, 0.13, 0, 0.42), (1.95, 0.03, 0.02, 0, 0.36)], 14), "Glass", 1)
    return P

def P_desert():
    """World 8, the desert: a ground-attack jet (A-10 style) in sand - straight wings full of bombs, two big engines up on the back, twin tails."""
    P = Plane("desert", {"Base": ((0.78, 0.65, 0.44), 0.35), "Belly": ((0.88, 0.81, 0.64), 0.3), "Accent": ((0.50, 0.35, 0.19), 0.35),
                         "Trim": ((0.30, 0.26, 0.21), 0.4), "Glass": ((0.3, 0.42, 0.44), 0.92), "Dark": ((0.07, 0.07, 0.07), 0.3),
                         "Glow": ((1.0, 0.55, 0.2), 0.5), "Metal": ((0.5, 0.48, 0.45), 0.6)})
    P.obj("Fuselage", loft([(2.4, 0.18, 0.18, 0, -0.08), (1.95, 0.33, 0.36, 0, 0.0), (1.0, 0.38, 0.42, 0, 0.05), (-0.5, 0.32, 0.38, 0, 0.06),
                            (-1.8, 0.18, 0.22, 0, 0.12), (-2.35, 0.1, 0.12, 0, 0.15)], 14, sq=1.4),
          lambda c, n: "Accent" if c.y > 2.2 else ("Belly" if c.z < -0.18 else "Base"), 1)
    for a in range(5):
        ang = 2 * math.pi * a / 5
        P.obj("Barrel", tube(2.3, 2.9, 0.025, 0.025, 0.06 * math.cos(ang), -0.12 + 0.06 * math.sin(ang), 6), "Dark", 0)
    P.obj("Canopy", lathe([(0.0, 0.62), (0.18, 0.58), (0.26, 0.48), (0.26, 0.36)], 14, "z", (0, 1.55, 0.0)), "Glass", 1)
    P.wing([(0.3, 0.55, -0.4, 0.17, -0.24), (1.9, 0.45, -0.25, 0.13, -0.22), (2.9, 0.35, -0.15, 0.08, -0.14), (3.05, 0.3, -0.1, 0.05, -0.1)],
           lambda c, n: "Belly" if n.z < -0.3 else ("Accent" if abs(c.x) > 2.85 else "Base"))
    for s in (1, -1):
        x = s * 0.68
        P.obj("Engine", loft([(-0.3, 0.27, 0.27, x, 0.62), (-0.45, 0.3, 0.3, x, 0.62), (-1.45, 0.28, 0.28, x, 0.62), (-1.75, 0.2, 0.2, x, 0.62)], 14),
              lambda c, n: "Dark" if c.y > -0.32 else "Base", 1)
        P.obj("Core", tube(-1.72, -1.78, 0.15, 0.04, x, 0.62, 12), "Glow")
        P.obj("EnginePylon", box((s * 0.42, -1.0, 0.42), (0.12, 0.7, 0.2)), "Base", 0, False)
        for bx in (1.1, 1.75, 2.35):
            P.obj("Bomb", loft([(0.25, 0.02, 0.02, s * bx, -0.48), (0.1, 0.1, 0.1, s * bx, -0.48), (-0.45, 0.1, 0.1, s * bx, -0.48), (-0.6, 0.05, 0.05, s * bx, -0.48)], 10),
                  lambda c, n: "Accent" if c.y > 0.15 else "Trim", 1)
            P.obj("BombPylon", box((s * bx, -0.1, -0.35), (0.03, 0.35, 0.12)), "Trim", 0, False)
        P.fin([(-0.35, -1.8, -2.4, 0.06), (0.0, -1.75, -2.45, 0.07), (0.75, -1.8, -2.4, 0.06)], s * 1.3, 0.2, 0, "Base")
    P.wing([(0.1, -1.85, -2.42, 0.07, 0.2), (1.32, -1.85, -2.42, 0.06, 0.2)], name="Stab")
    return P

def P_city():
    """World 9, downtown: a stealth fighter (F-117 style) - all flat dark facets, a gold faceted canopy, a V tail, glowing slot exhausts."""
    P = Plane("city", {"Base": ((0.23, 0.24, 0.27), 0.45), "Belly": ((0.16, 0.16, 0.18), 0.35), "Accent": ((0.38, 0.39, 0.42), 0.5),
                       "Trim": ((0.95, 0.80, 0.25), 0.5), "Glass": ((0.92, 0.66, 0.2), 0.95), "Dark": ((0.05, 0.05, 0.06), 0.3),
                       "Glow": ((1.0, 0.5, 0.15), 0.5), "Metal": ((0.4, 0.4, 0.43), 0.6)})
    pts = [(0, 2.75, -0.04), (0, 2.6, -0.12), (0, 1.1, 0.5), (0, -0.3, 0.44), (0, -1.45, 0.2),
           (0.5, 1.3, 0.14), (-0.5, 1.3, 0.14), (0.75, 0.0, 0.26), (-0.75, 0.0, 0.26),
           (2.35, -1.3, -0.02), (-2.35, -1.3, -0.02), (2.3, -1.48, -0.06), (-2.3, -1.48, -0.06),
           (0.9, -1.55, 0.02), (-0.9, -1.55, 0.02), (0, -1.85, 0.06),
           (0.6, 1.0, -0.16), (-0.6, 1.0, -0.16), (0.8, -0.9, -0.16), (-0.8, -0.9, -0.16), (0, 2.0, -0.17)]
    P.obj("Hull", hull(pts), lambda c, n: "Belly" if n.z < -0.5 else ("Accent" if abs(c.x) > 1.9 else "Base"), 0, False)
    P.obj("Canopy", hull([(0, 1.95, 0.24), (0.2, 1.5, 0.36), (-0.2, 1.5, 0.36), (0, 1.0, 0.56), (0.24, 0.9, 0.42), (-0.24, 0.9, 0.42), (0, 1.75, 0.18), (0.3, 1.2, 0.2), (-0.3, 1.2, 0.2)]), "Glass", 0, False)
    for s in (1, -1):
        P.fin([(0.0, -0.9, -1.75, 0.05), (0.95, -1.5, -2.0, 0.04), (1.05, -1.62, -2.0, 0.03)], s * 0.35, 0.25, 42, "Base", 0)
        P.obj("Slot", box((s * 0.42, -1.62, 0.12), (0.5, 0.06, 0.05)), "Glow", 0, False)
        P.obj("Grille", hull([(s * 0.55, 1.05, 0.2), (s * 0.78, 0.55, 0.3), (s * 0.78, 0.55, 0.1), (s * 0.6, 1.05, 0.05), (s * 0.82, 0.55, 0.2)]), "Dark", 0, False)
    return P

def P_japan():
    """World 10, the Japanese island: a carrier fighter (Zero style) - dark green over grey, a black cowl, yellow leading edges, a long canopy."""
    P = Plane("japan", {"Base": ((0.18, 0.30, 0.20), 0.4), "Belly": ((0.72, 0.73, 0.66), 0.35), "Accent": ((0.95, 0.74, 0.18), 0.5),
                        "Trim": ((0.80, 0.14, 0.14), 0.5), "Glass": ((0.45, 0.62, 0.68), 0.92), "Dark": ((0.07, 0.07, 0.08), 0.35),
                        "Glow": ((1.0, 0.55, 0.2), 0.5), "Metal": ((0.58, 0.6, 0.6), 0.6)})
    P.obj("Fuselage", loft([(2.25, 0.36, 0.36, 0, 0.0), (2.0, 0.42, 0.42, 0, 0.0), (1.55, 0.42, 0.42, 0, 0.0), (1.2, 0.38, 0.4, 0, 0.03),
                            (0.0, 0.33, 0.37, 0, 0.05), (-1.2, 0.21, 0.25, 0, 0.1), (-2.35, 0.05, 0.08, 0, 0.18)], 16),
          lambda c, n: "Dark" if c.y > 1.5 else ("Trim" if -1.45 < c.y < -1.25 else ("Belly" if c.z < -0.1 else "Base")), 1)
    P.obj("CowlFace", lathe([(0.0, 2.3), (0.22, 2.28), (0.33, 2.22)], 16, "y"), "Metal", 0)
    P.obj("Canopy", loft([(-0.15, 0.04, 0.03, 0, 0.3), (0.1, 0.17, 0.16, 0, 0.36), (0.6, 0.2, 0.22, 0, 0.4), (1.05, 0.17, 0.18, 0, 0.36), (1.25, 0.04, 0.03, 0, 0.3)], 12), "Glass", 1)
    le_yellow = lambda c, n: "Accent" if (n.y > 0.6 and abs(c.x) < 1.45) else ("Belly" if n.z < -0.3 else "Base")
    P.wing([(0.3, 0.9, -0.35, 0.16, -0.24), (1.6, 0.75, -0.15, 0.12, -0.14), (2.4, 0.5, 0.05, 0.07, -0.06), (2.62, 0.36, 0.14, 0.04, -0.04)], le_yellow)
    P.wing([(0.1, -1.8, -2.3, 0.06, 0.12), (0.85, -1.95, -2.25, 0.04, 0.12), (1.0, -2.05, -2.22, 0.03, 0.12)], name="Stab")
    P.fin([(0.0, -1.55, -2.4, 0.07), (0.55, -1.85, -2.4, 0.05), (0.75, -2.05, -2.35, 0.04)], 0.0, 0.18, 0, "Base")
    P.obj("DropTank", loft([(1.0, 0.02, 0.02, 0, -0.5), (0.7, 0.15, 0.15, 0, -0.5), (-0.3, 0.15, 0.15, 0, -0.5), (-0.7, 0.02, 0.02, 0, -0.5)], 10), "Belly", 1)
    for s in (1, -1):
        P.obj("Gun", tube(1.9, 2.55, 0.03, 0.03, s * 0.12, 0.38, 6), "Dark", 0)
    P.prop((0, 2.38, 0.0), 0.88, 3, spinner="Metal")
    return P

def P_soccer():
    """World 11, the stadium: a delta-wing interceptor (Mirage style) in white with green stripes and a black-topped green fin."""
    P = Plane("soccer", {"Base": ((0.92, 0.93, 0.94), 0.55), "Belly": ((0.80, 0.82, 0.85), 0.5), "Accent": ((0.10, 0.66, 0.26), 0.5),
                         "Trim": ((0.08, 0.08, 0.09), 0.45), "Glass": ((0.22, 0.34, 0.46), 0.92), "Dark": ((0.06, 0.06, 0.07), 0.3),
                         "Glow": ((1.0, 0.55, 0.2), 0.5), "Metal": ((0.6, 0.6, 0.62), 0.6)})
    P.obj("Fuselage", loft([(2.9, 0.02, 0.02, 0, 0.0), (2.4, 0.14, 0.14, 0, 0.0), (1.6, 0.26, 0.27, 0, 0.02), (0.8, 0.31, 0.36, 0, 0.04),
                            (-0.2, 0.33, 0.36, 0, 0.04), (-1.5, 0.31, 0.32, 0, 0.02), (-2.35, 0.27, 0.27, 0, 0.02)], 16),
          lambda c, n: "Trim" if c.y > 2.55 else ("Accent" if 0.9 < c.y < 1.2 else ("Belly" if c.z < -0.15 else "Base")), 1)
    P.obj("Core", tube(-2.33, -2.4, 0.2, 0.05, 0, 0.02, 14), "Glow")
    for s in (1, -1):
        x = s * 0.4
        P.obj("Intake", loft([(1.0, 0.13, 0.17, x, 0.02), (0.6, 0.15, 0.2, x, 0.02), (-0.6, 0.12, 0.16, x, 0.02)], 12, sq=1.2),
              lambda c, n: "Dark" if c.y > 0.95 else "Base", 1)
        P.obj("Cone", lathe([(0.0, 1.25), (0.06, 1.1), (0.08, 0.95)], 10, "y", (x, 0, 0.02)), "Metal", 0)
        P.missile(s * 2.3, -0.06, -2.0, 1.1, 0.06, "Base", "Trim")
    P.wing([(0.3, 0.45, -2.25, 0.14, -0.06), (1.2, -0.65, -2.28, 0.08, -0.06), (2.25, -1.85, -2.3, 0.04, -0.06)],
           lambda c, n: "Belly" if n.z < -0.3 else ("Accent" if 1.45 < abs(c.x) < 1.75 else "Base"))
    P.fin([(0.0, -0.85, -2.3, 0.1), (0.9, -1.55, -2.4, 0.07), (1.3, -1.95, -2.45, 0.05)], 0.0, 0.25, 0, lambda c, n: "Trim" if c.z > 1.35 else "Accent")
    P.obj("Canopy", loft([(0.9, 0.04, 0.03, 0, 0.32), (1.2, 0.17, 0.16, 0, 0.38), (1.6, 0.19, 0.2, 0, 0.42), (2.0, 0.1, 0.1, 0, 0.32), (2.15, 0.03, 0.02, 0, 0.26)], 12), "Glass", 1)
    return P

def P_shuttle():
    """World 12, the launch pad: a black high-altitude spy jet (SR-71 style) - chines, two huge engines with spike cones, canted fins, blue-hot nozzles."""
    P = Plane("shuttle", {"Base": ((0.08, 0.08, 0.10), 0.5), "Belly": ((0.11, 0.11, 0.13), 0.45), "Accent": ((0.26, 0.28, 0.33), 0.5),
                          "Trim": ((0.92, 0.92, 0.94), 0.5), "Glass": ((0.2, 0.28, 0.36), 0.95), "Dark": ((0.03, 0.03, 0.04), 0.3),
                          "Glow": ((0.45, 0.7, 1.0), 0.5), "Metal": ((0.55, 0.56, 0.6), 0.7)})
    P.obj("Fuselage", loft([(3.1, 0.02, 0.02, 0, 0.0), (2.5, 0.13, 0.09, 0, 0.02), (1.6, 0.24, 0.17, 0, 0.04), (0.5, 0.3, 0.21, 0, 0.06),
                            (-1.0, 0.3, 0.21, 0, 0.06), (-2.4, 0.2, 0.15, 0, 0.05)], 16),
          lambda c, n: "Belly" if c.z < -0.06 else "Base", 1)
    P.wing([(0.15, 2.6, -0.4, 0.05, 0.02), (0.75, 0.6, -0.6, 0.04, 0.02)], name="Chine")
    P.wing([(0.25, 0.3, -2.1, 0.07, 0.0), (1.05, -0.55, -2.15, 0.06, 0.0), (2.1, -1.65, -2.15, 0.04, 0.0)],
           lambda c, n: "Belly" if n.z < -0.3 else ("Trim" if abs(c.x) > 1.98 else "Base"))
    for s in (1, -1):
        x = s * 1.05
        P.obj("Nacelle", loft([(1.0, 0.22, 0.22, x, 0.0), (0.6, 0.27, 0.27, x, 0.0), (-2.2, 0.27, 0.27, x, 0.0), (-2.6, 0.22, 0.22, x, 0.0)], 14),
              lambda c, n: "Belly" if c.z < -0.1 else "Base", 1)
        P.obj("Spike", lathe([(0.0, 1.75), (0.1, 1.35), (0.16, 1.0)], 12, "y", (x, 0, 0.0)), "Metal", 0)
        P.obj("Core", tube(-2.55, -2.62, 0.18, 0.05, x, 0.0, 12), "Glow")
        P.fin([(0.0, -1.45, -2.4, 0.07), (0.7, -1.85, -2.45, 0.05), (0.85, -2.0, -2.45, 0.04)], x, 0.2, -15, "Base")
    P.obj("Canopy", loft([(1.8, 0.03, 0.02, 0, 0.18), (2.05, 0.12, 0.08, 0, 0.2), (2.3, 0.1, 0.06, 0, 0.17), (2.45, 0.02, 0.02, 0, 0.13)], 12), "Glass", 1)
    return P

def P_treasure():
    """World 13, treasure island: a patrol flying boat (Catalina style) - a teal boat hull, a parasol wing on a pylon, two engines, tip floats."""
    P = Plane("treasure", {"Base": ((0.12, 0.27, 0.34), 0.45), "Belly": ((0.80, 0.75, 0.62), 0.4), "Accent": ((0.90, 0.68, 0.18), 0.6),
                           "Trim": ((0.58, 0.10, 0.08), 0.45), "Glass": ((0.5, 0.72, 0.82), 0.92), "Dark": ((0.06, 0.06, 0.07), 0.3),
                           "Glow": ((1.0, 0.6, 0.2), 0.5), "Metal": ((0.55, 0.55, 0.57), 0.6)})
    P.obj("Hull", loft([(2.25, 0.16, 0.22, 0, -0.12), (1.8, 0.36, 0.42, 0, -0.06), (0.5, 0.42, 0.5, 0, 0.0), (-1.0, 0.36, 0.42, 0, 0.06),
                        (-2.2, 0.15, 0.2, 0, 0.26), (-2.7, 0.06, 0.08, 0, 0.38)], 16, sq=1.25),
          lambda c, n: "Belly" if c.z < -0.22 else ("Accent" if -0.2 < c.z < -0.12 else "Base"), 1)
    P.obj("NoseTurret", lathe([(0.0, 0.28), (0.15, 0.22), (0.18, 0.08), (0.17, 0.0)], 12, "y", (0, 2.1, 0.02)), "Glass", 1)
    P.obj("Pylon", hull([(0.1, 0.5, 0.35), (-0.1, 0.5, 0.35), (0.1, -0.6, 0.35), (-0.1, -0.6, 0.35), (0.07, 0.35, 0.95), (-0.07, 0.35, 0.95), (0.07, -0.3, 0.95), (-0.07, -0.3, 0.95)]), "Base", 0, False)
    P.obj("Wing", sweep([(x, airfoil(0.62 - max(0, abs(x) - 1.2) * 0.08, -0.38 + max(0, abs(x) - 1.2) * 0.1, 0.14 - abs(x) * 0.025, 1.0)) for x in (-3.0, -2.7, -1.2, 1.2, 2.7, 3.0)], "x"),
          lambda c, n: "Belly" if n.z < -0.3 else ("Accent" if n.y > 0.55 else "Base"), 1)
    for s in (1, -1):
        x = s * 0.95
        P.obj("Nacelle", loft([(0.95, 0.2, 0.2, x, 1.0), (0.6, 0.23, 0.24, x, 1.0), (-0.4, 0.18, 0.2, x, 1.02), (-0.75, 0.05, 0.06, x, 1.05)], 12),
              lambda c, n: "Trim" if c.y > 0.7 else "Base", 1)
        P.prop((x, 1.05, 1.0), 0.68, 3, spinner="Accent")
        P.obj("Float", loft([(0.35, 0.04, 0.04, s * 2.65, 0.25), (0.15, 0.12, 0.1, s * 2.65, 0.25), (-0.45, 0.1, 0.08, s * 2.65, 0.25), (-0.6, 0.02, 0.02, s * 2.65, 0.25)], 10),
              lambda c, n: "Belly" if c.z < 0.22 else "Accent", 1)
        P.obj("FloatStrut", box((s * 2.65, -0.1, 0.62), (0.04, 0.12, 0.65)), "Dark", 0, False)
        P.obj("Blister", lathe([(0.0, 0.22), (0.12, 0.2), (0.2, 0.12), (0.22, 0.0)], 12, "x", (s * 0.18, -0.8, 0.18)) if s > 0 else
              lathe([(0.0, -0.22), (0.12, -0.2), (0.2, -0.12), (0.22, 0.0)], 12, "x", (s * 0.18, -0.8, 0.18)), "Glass", 1)
    P.fin([(0.0, -2.05, -2.75, 0.09), (0.95, -2.45, -2.85, 0.06), (1.1, -2.6, -2.85, 0.05)], 0.0, 0.28, 0, lambda c, n: "Accent" if c.z > 1.15 else "Trim")
    P.wing([(0.05, -2.3, -2.8, 0.06, 0.62), (1.05, -2.45, -2.8, 0.04, 0.62)], name="Stab")
    P.obj("Canopy", loft([(1.2, 0.05, 0.04, 0, 0.36), (1.4, 0.24, 0.16, 0, 0.42), (1.75, 0.2, 0.12, 0, 0.36), (1.9, 0.04, 0.03, 0, 0.3)], 12), "Glass", 1)
    return P

def P_west():
    """World 14, the wild west: a dive bomber (Stuka style) - inverted gull wings, big spatted wheels, a yellow nose, a bomb under the belly."""
    P = Plane("west", {"Base": ((0.60, 0.45, 0.28), 0.35), "Belly": ((0.80, 0.72, 0.56), 0.3), "Accent": ((0.38, 0.25, 0.14), 0.35),
                       "Trim": ((0.93, 0.72, 0.18), 0.5), "Glass": ((0.45, 0.56, 0.56), 0.92), "Dark": ((0.07, 0.07, 0.07), 0.3),
                       "Glow": ((1.0, 0.55, 0.2), 0.5), "Metal": ((0.45, 0.45, 0.46), 0.6)})
    P.obj("Fuselage", loft([(2.4, 0.3, 0.36, 0, 0.0), (2.0, 0.36, 0.44, 0, 0.0), (1.2, 0.36, 0.44, 0, 0.03), (0.0, 0.3, 0.4, 0, 0.08),
                            (-1.2, 0.2, 0.28, 0, 0.12), (-2.4, 0.05, 0.08, 0, 0.2)], 14, sq=1.35),
          lambda c, n: "Trim" if c.y > 1.75 else ("Belly" if c.z < -0.18 else "Base"), 1)
    P.obj("Radiator", loft([(2.0, 0.2, 0.1, 0, -0.42), (1.3, 0.22, 0.14, 0, -0.44), (0.9, 0.12, 0.06, 0, -0.36)], 10, sq=1.6), lambda c, n: "Dark" if c.y > 1.9 else "Base", 1)
    P.obj("Canopy", loft([(-0.55, 0.04, 0.03, 0, 0.36), (-0.3, 0.17, 0.16, 0, 0.42), (0.6, 0.19, 0.2, 0, 0.45), (1.05, 0.15, 0.15, 0, 0.42), (1.2, 0.03, 0.03, 0, 0.36)], 12), "Glass", 1)
    gull = lambda c, n: "Belly" if n.z < -0.3 else ("Accent" if abs(c.x) > 2.55 else "Base")
    P.wing([(0.28, 0.7, -0.45, 0.17, -0.22), (1.0, 0.62, -0.38, 0.15, -0.5)], gull, name="WingIn")
    P.wing([(1.0, 0.62, -0.38, 0.15, -0.5), (2.2, 0.48, -0.18, 0.1, -0.22), (2.8, 0.34, -0.04, 0.06, -0.08)], gull, name="WingOut")
    for s in (1, -1):
        P.obj("Leg", box((s * 1.0, 0.35, -0.82), (0.1, 0.3, 0.6)), "Base", 0, False)
        P.obj("Spat", loft([(0.85, 0.04, 0.04, s * 1.0, -1.08), (0.6, 0.13, 0.2, s * 1.0, -1.08), (0.15, 0.14, 0.22, s * 1.0, -1.1), (-0.15, 0.05, 0.1, s * 1.0, -1.05)], 12),
              lambda c, n: "Dark" if c.z < -1.25 else "Base", 1)
        P.obj("Gun", tube(0.55, 1.15, 0.03, 0.03, s * 1.35, -0.42, 6), "Dark", 0)
    P.obj("Bomb", loft([(0.75, 0.02, 0.02, 0, -0.62), (0.5, 0.16, 0.16, 0, -0.62), (-0.35, 0.16, 0.16, 0, -0.62), (-0.7, 0.03, 0.03, 0, -0.62)], 12),
          lambda c, n: "Trim" if c.y > 0.55 else "Dark", 1)
    P.wing([(0.1, -1.75, -2.35, 0.07, 0.25), (1.05, -1.9, -2.3, 0.05, 0.25)], name="Stab")
    P.fin([(0.0, -1.6, -2.45, 0.08), (0.7, -1.85, -2.45, 0.06), (0.8, -1.95, -2.42, 0.05)], 0.0, 0.18, 0, lambda c, n: "Trim" if c.z > 0.9 else "Base")
    P.prop((0, 2.5, 0.0), 0.9, 3, spinner="Trim")
    return P

from enemy_planes_b import define_b
PLANES_B = define_b(globals())

PLANES = [("sea", P_sea), ("lava", P_lava), ("alien", P_alien), ("meadow", P_meadow), ("autumn", P_autumn), ("camping", P_camping),
          ("christmas", P_christmas), ("desert", P_desert), ("city", P_city), ("japan", P_japan), ("soccer", P_soccer),
          ("shuttle", P_shuttle), ("treasure", P_treasure), ("west", P_west)]

PLANES += PLANES_B
if __name__ == "__main__":   # alien_bosses.py imports the helpers without building the planes
    os.makedirs(OUT, exist_ok=True)
    for pid, fn in PLANES:
        if ONLY and pid not in ONLY: continue
        fn().finish()
    print("DONE")
