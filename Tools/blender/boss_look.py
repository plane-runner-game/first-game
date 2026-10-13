# Sky Squad, the realistic look for the code-built bosses (2026-10-13: "make them more realistic, they still look like plastic").
# The bosses are painted by slot (Base, Belly, Accent, Trim, Glass, Dark, Glow, Metal, Lamp: one flat colour each), which reads as plastic.
# This turns each slot's material into a real surface while keeping its colour: creature skin with mottling, pores and soft subsurface
# light, scales (a Voronoi cell bump) on the dragon, painted metal panels with grime and scratches on the ships, brushed bare metal, ivory
# for teeth and horns, wet glossy eyes - all procedural, in object space, so the meshes need no UVs. studio() lights the preview like a
# photo studio (key, rim and fill lights, soft sky light, Cycles on the GPU, AgX colour) instead of one flat sun.
#   import boss_look; boss_look.apply(P, "scaly" | "skin" | "ship"); boss_look.studio(bg)
import bpy, math

KINDS = {
    # per kind, what each slot is made of
    "scaly": {"Base": "scales", "Belly": "plates", "Accent": "scales", "Trim": "ivory", "Glass": "eye", "Dark": "skin_dark",
              "Glow": "glow", "Metal": "plates", "Lamp": "glow"},
    "skin":  {"Base": "skin", "Belly": "skin_pale", "Accent": "skin", "Trim": "ivory", "Glass": "eye", "Dark": "skin_dark",
              "Glow": "glow", "Metal": "skin", "Lamp": "glow"},
    "ship":  {"Base": "paint", "Belly": "paint", "Accent": "paint_bright", "Trim": "skin_pale", "Glass": "glass", "Dark": "rubber",
              "Glow": "glow", "Metal": "metal", "Lamp": "glow"},
}

def _n(nt, kind, loc, **inputs):
    n = nt.nodes.new(kind); n.location = loc
    for k, v in inputs.items():
        try: n.inputs[k].default_value = v
        except (KeyError, TypeError): setattr(n, k, v)
    return n

def _set(bsdf, name, v):
    if name in bsdf.inputs: bsdf.inputs[name].default_value = v

def surface(m, what, scale=1.0):
    """rebuild material m as a `what` surface, keeping its base colour (and its emission, for glows)."""
    nt = m.node_tree; L = nt.links
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    col = tuple(bsdf.inputs["Base Color"].default_value)
    if what == "glow":
        _set(bsdf, "Roughness", 0.35); return
    tc = _n(nt, "ShaderNodeTexCoord", (-1200, 0))
    mp = _n(nt, "ShaderNodeMapping", (-1000, 0)); mp.inputs["Scale"].default_value = (scale, scale, scale)
    L.new(tc.outputs["Object"], mp.inputs["Vector"]); V = mp.outputs["Vector"]
    def noise(sc, detail=6.0, rough=0.55, loc=(-800, 0)):
        t = _n(nt, "ShaderNodeTexNoise", loc); t.inputs["Scale"].default_value = sc; t.inputs["Detail"].default_value = detail
        t.inputs["Roughness"].default_value = rough; L.new(V, t.inputs["Vector"]); return t
    def tint(fac_socket, lo, hi, loc=(-400, 200)):
        """the base colour times a ramp from lo to hi driven by fac (a mottle)."""
        r = _n(nt, "ShaderNodeValToRGB", (loc[0] - 200, loc[1])); r.color_ramp.elements[0].position = 0.3; r.color_ramp.elements[1].position = 0.7
        r.color_ramp.elements[0].color = (lo, lo, lo, 1); r.color_ramp.elements[1].color = (hi, hi, hi, 1)
        L.new(fac_socket, r.inputs["Fac"])
        mx = _n(nt, "ShaderNodeMix", loc); mx.data_type = "RGBA"; mx.blend_type = "MULTIPLY"; mx.inputs[0].default_value = 1.0
        mx.inputs[6].default_value = col; L.new(r.outputs["Color"], mx.inputs[7]); return mx.outputs[2]
    def bump(height_socket, strength, dist=0.02, normal=None, loc=(-200, -300)):
        b = _n(nt, "ShaderNodeBump", loc); b.inputs["Strength"].default_value = strength; b.inputs["Distance"].default_value = dist
        L.new(height_socket, b.inputs["Height"])
        if normal is not None: L.new(normal, b.inputs["Normal"])
        return b.outputs["Normal"]
    def rough_from(fac_socket, lo, hi, loc=(-300, -100)):
        r = _n(nt, "ShaderNodeMapRange", loc); r.inputs["To Min"].default_value = lo; r.inputs["To Max"].default_value = hi
        L.new(fac_socket, r.inputs["Value"]); return r.outputs["Result"]
    if what in ("skin", "skin_pale", "skin_dark", "scales", "plates"):
        mottle = noise(3.0, 8, 0.6, (-800, 300))
        L.new(tint(mottle.outputs["Fac"], 0.72, 1.18), bsdf.inputs["Base Color"])
        pores = noise(140.0, 4, 0.7, (-800, -300))
        nrm = bump(pores.outputs["Fac"], 0.12, 0.004)
        if what == "scales":   # overlapping scales: each Voronoi cell a raised, rounded plate
            vo = _n(nt, "ShaderNodeTexVoronoi", (-800, -600)); vo.inputs["Scale"].default_value = 26.0; vo.feature = "DISTANCE_TO_EDGE"
            L.new(V, vo.inputs["Vector"])
            sm = _n(nt, "ShaderNodeMath", (-600, -600)); sm.operation = "POWER"; sm.inputs[1].default_value = 0.45; L.new(vo.outputs["Distance"], sm.inputs[0])
            nrm = bump(sm.outputs[0], 0.55, 0.03, nrm, (0, -600))
            L.new(rough_from(vo.outputs["Distance"], 0.7, 0.42), bsdf.inputs["Roughness"])   # the scales shine, the gaps between them are dull
        elif what == "plates":
            wv = _n(nt, "ShaderNodeTexWave", (-800, -600)); wv.inputs["Scale"].default_value = 6.0; wv.wave_type = "BANDS"; wv.bands_direction = "Z"
            L.new(V, wv.inputs["Vector"]); nrm = bump(wv.outputs["Fac"], 0.25, 0.02, nrm, (0, -600))
            _set(bsdf, "Roughness", 0.5)
        else:
            L.new(rough_from(mottle.outputs["Fac"], 0.42, 0.62), bsdf.inputs["Roughness"])
        L.new(nrm, bsdf.inputs["Normal"])
        _set(bsdf, "Subsurface Weight", 0.15 if what != "skin_dark" else 0.0); _set(bsdf, "Subsurface Scale", 0.03)
        _set(bsdf, "Specular IOR Level", 0.45); _set(bsdf, "Coat Weight", 0.08 if what != "plates" else 0.0)
    elif what == "ivory":
        mottle = noise(9.0, 5, 0.6, (-800, 300))
        L.new(tint(mottle.outputs["Fac"], 0.86, 1.05), bsdf.inputs["Base Color"])
        rings = _n(nt, "ShaderNodeTexWave", (-800, -300)); rings.inputs["Scale"].default_value = 18.0; rings.inputs["Distortion"].default_value = 2.0
        L.new(V, rings.inputs["Vector"]); L.new(bump(rings.outputs["Fac"], 0.12, 0.01), bsdf.inputs["Normal"])
        _set(bsdf, "Roughness", 0.38); _set(bsdf, "Subsurface Weight", 0.2); _set(bsdf, "Subsurface Scale", 0.02)
    elif what in ("eye", "glass"):
        _set(bsdf, "Roughness", 0.04); _set(bsdf, "Coat Weight", 1.0); _set(bsdf, "Coat Roughness", 0.02)
        if what == "glass": _set(bsdf, "Metallic", 0.2)
    elif what == "rubber":
        n1 = noise(30.0, 4, 0.5); L.new(rough_from(n1.outputs["Fac"], 0.55, 0.8), bsdf.inputs["Roughness"])
    elif what in ("paint", "paint_bright", "metal"):
        # panels: each Voronoi cell a plate a shade lighter or darker; grime in a large noise; fine scratches stretched one way
        pan = _n(nt, "ShaderNodeTexVoronoi", (-800, 400)); pan.inputs["Scale"].default_value = 4.0; L.new(V, pan.inputs["Vector"])
        grime = noise(2.5, 8, 0.65, (-800, 100))
        mixf = _n(nt, "ShaderNodeMath", (-600, 300)); mixf.operation = "MULTIPLY_ADD"; mixf.inputs[1].default_value = 0.35
        L.new(pan.outputs["Distance"], mixf.inputs[0]); L.new(grime.outputs["Fac"], mixf.inputs[2])
        lo, hi = (0.7, 1.12) if what != "metal" else (0.8, 1.1)
        L.new(tint(mixf.outputs[0], lo, hi), bsdf.inputs["Base Color"])
        seams = _n(nt, "ShaderNodeTexVoronoi", (-800, -400)); seams.inputs["Scale"].default_value = 4.0; seams.feature = "DISTANCE_TO_EDGE"
        L.new(V, seams.inputs["Vector"])
        sm = _n(nt, "ShaderNodeMath", (-600, -400)); sm.operation = "GREATER_THAN"; sm.inputs[1].default_value = 0.025; L.new(seams.outputs["Distance"], sm.inputs[0])
        scr_map = _n(nt, "ShaderNodeMapping", (-1000, -700)); scr_map.inputs["Scale"].default_value = (1.0, 1.0, 30.0); L.new(V, scr_map.inputs["Vector"])
        scr = _n(nt, "ShaderNodeTexNoise", (-800, -700)); scr.inputs["Scale"].default_value = 40.0; scr.inputs["Detail"].default_value = 2.0
        L.new(scr_map.outputs["Vector"], scr.inputs["Vector"])
        nrm = bump(sm.outputs[0], 0.35, 0.01, None, (-200, -400))
        nrm = bump(scr.outputs["Fac"], 0.05, 0.002, nrm, (0, -600))
        L.new(nrm, bsdf.inputs["Normal"])
        if what == "metal":
            _set(bsdf, "Metallic", 0.9); L.new(rough_from(scr.outputs["Fac"], 0.22, 0.45), bsdf.inputs["Roughness"])
        else:
            _set(bsdf, "Metallic", 0.35); L.new(rough_from(grime.outputs["Fac"], 0.32, 0.6), bsdf.inputs["Roughness"])
            _set(bsdf, "Coat Weight", 0.25); _set(bsdf, "Coat Roughness", 0.15)

LEATHER = {"Base": "skin", "Accent": "skin", "Belly": "skin_pale", "Metal": "skin"}   # a dragon's wing membrane: smooth leathery skin, no scales

def apply(P, kind, scale=1.0, parts=None):
    """every slot material of the boss P made a real surface of its kind. parts: {object name prefix: {slot: surface}} - those objects
    get their own copies of the materials, made the given surfaces instead (e.g. the dragon's wings "Flap": LEATHER)."""
    table = KINDS[kind]
    for m in P.mats:
        surface(m, table.get(m.name.split("_")[-1], "skin"), scale)
    for prefix, over in (parts or {}).items():
        for ob in [P.body] + list(P.spin):
            if not ob.name.startswith(prefix): continue
            for i, m in enumerate(ob.data.materials):
                slot = m.name.split("_")[-1]
                if slot not in over: continue
                c = m.copy(); c.name = m.name + "_" + prefix
                bsdf = next(n for n in c.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
                col = tuple(bsdf.inputs["Base Color"].default_value)
                c.node_tree.nodes.clear()
                o = c.node_tree.nodes.new("ShaderNodeOutputMaterial"); nb = c.node_tree.nodes.new("ShaderNodeBsdfPrincipled")
                nb.inputs["Base Color"].default_value = col; c.node_tree.links.new(nb.outputs[0], o.inputs[0])
                surface(c, over[slot], scale); ob.data.materials[i] = c

def studio(bg=(0.42, 0.52, 0.66), samples=96):
    """photo-studio light: a warm key, a cool rim behind, a soft fill and a sky for ambient light; the camera still sees the flat background."""
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    try:
        p = bpy.context.preferences.addons["cycles"].preferences
        for t in ("OPTIX", "CUDA"):
            try:
                p.compute_device_type = t; p.get_devices()
                if any(d.type == t for d in p.devices):
                    for d in p.devices: d.use = d.type == t
                    sc.cycles.device = "GPU"; break
            except TypeError: pass
    except Exception: pass
    sc.cycles.samples = samples; sc.cycles.use_denoising = True
    try: sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Medium High Contrast"
    except TypeError: pass
    w = sc.world; w.use_nodes = True; nt = w.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputWorld")
    sky = nt.nodes.new("ShaderNodeBackground"); sky.inputs["Color"].default_value = (0.55, 0.62, 0.8, 1); sky.inputs["Strength"].default_value = 0.55
    flat = nt.nodes.new("ShaderNodeBackground"); flat.inputs["Color"].default_value = (*bg, 1); flat.inputs["Strength"].default_value = 1.0
    lp = nt.nodes.new("ShaderNodeLightPath"); mx = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(lp.outputs["Is Camera Ray"], mx.inputs[0]); nt.links.new(sky.outputs[0], mx.inputs[1]); nt.links.new(flat.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs[0])
    for o in [o for o in sc.objects if o.type == "LIGHT"]: bpy.data.objects.remove(o)
    def light(name, kind, energy, color, rot, size):
        l = bpy.data.lights.new(name, kind); l.energy = energy; l.color = color
        if kind == "SUN": l.angle = math.radians(size)
        o = bpy.data.objects.new(name, l); sc.collection.objects.link(o); o.rotation_euler = tuple(math.radians(a) for a in rot)
    light("Key", "SUN", 4.0, (1.0, 0.95, 0.88), (50, 10, 145), 6)
    light("Rim", "SUN", 3.0, (0.75, 0.85, 1.0), (-60, 0, 10), 4)
    light("Fill", "SUN", 0.8, (0.9, 0.9, 1.0), (70, 0, -120), 20)
