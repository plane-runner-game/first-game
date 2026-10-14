# Sky Squad - real surfaces for the bosses, baked into textures (2026-10-14: "make them more realistic, keep the cartoonish look of course,
# but they still look plasticky"). The flat slot colours read as plastic: one colour and one shine per slot. Here every face of a boss is
# tagged, while it is built, with what it is made of - feathers, wool, felt, silk, lace, canvas, rope, skin, scales, horn, bone, wood,
# leather, gold, brass, steel, rusty iron, crab shell... (TABLES: by part name and slot) - and each surface keeps the slot's colour but gets
# its own grain, tone variation, relief and shine. The finished boss is unwrapped into one atlas and Cycles bakes it: the colour with the
# occlusion of every crease multiplied in, the relief as a tangent-space normal map, metal and smoothness, and the glow. They are saved
# beside the FBX as Boss_<id>_Albedo.jpg / _Normal.jpg / _Mask.png (R metal, A smoothness) / _Emission.jpg; the game's boss builder
# (SceneBuilder.ModelBosses) gives a boss that has them one textured URP material instead of the slot colours (the outline stays: the
# cartoon look is kept, the plastic is gone). A boss without them keeps the slot colours.
# Use (in a <world>_bosses.py): boss_bake.TABLES[id] = (slot defaults, [(part name pattern, look or {slot: look}), ...]) for the ids to bake,
# and boss_bake.finish_baked(P, out_dir) instead of P.finish() when exporting. P.hint = "look" makes the next parts that look whatever their
# name (None ends it).
import bpy, math, os, fnmatch
import numpy as np
import enemy_planes as EP
import alien_bosses as AB

LOOKS = ["", "feather", "down", "wool", "linen", "felt", "silk", "lace", "cloth", "canvas", "rope", "skin", "flesh", "ghost", "hair",
         "scales", "keratin", "horn", "bone", "enamel", "wood", "wood_v", "leather", "parchment", "gold", "brass", "steel", "iron",
         "shell", "shell_belly", "puffer", "fin", "barnacle", "weed", "gem", "eye", "eye_white", "glow", "lamp", "matte"]
TABLES = {}   # boss id -> ({slot: look}, [(name pattern, look | {slot: look}), ...]); the first pattern that matches the part's name decides


def look_of(bid, name, slot, hint=None):
    if hint: return hint
    defaults, names = TABLES[bid]
    for pat, v in names:
        if fnmatch.fnmatchcase(name, pat):
            if isinstance(v, str): return v
            if slot in v: return v[slot]
            break
    return defaults.get(slot, "matte")


_plain_obj = EP.Plane.obj
def _tagged_obj(self, name, bm, paint="Base", ss=0, smooth=True, spin=None):
    """Plane.obj, and each face told what it is made of ("look") and given its piece's own random number ("rnd": every feather, plank and
    button a shade apart)."""
    ob = _plain_obj(self, name, bm, paint, ss, smooth, spin)
    if self.id in TABLES:
        me = ob.data
        at = me.attributes.get("look") or me.attributes.new("look", "INT", "FACE")
        hint = getattr(self, "hint", None)
        at.data.foreach_set("value", [LOOKS.index(look_of(self.id, name, EP.SLOTS[p.material_index], hint)) for p in me.polygons])
        self._rc = getattr(self, "_rc", 0) + 1
        r = (math.sin(self._rc * 12.9898 + 4.1) * 43758.5453) % 1.0
        rd = me.attributes.get("rnd") or me.attributes.new("rnd", "FLOAT", "FACE")
        rd.data.foreach_set("value", [r] * len(me.polygons))
    return ob
EP.Plane.obj = _tagged_obj


def feathered(fn, seg=8):
    """a feather maker (feather(), long_feather(): a flat_pipe of rings of seg and a tip vertex) that also marks its vane: "fu" from the
    quill (0) to the tip (1), "fv" across the vane (-1 .. 1, 0 on the shaft), "fz" 1 - so the bake can draw the shaft and the barbs."""
    from mathutils import Vector
    def wrapped(*a, **k):
        bm = fn(*a, **k)
        fu = bm.verts.layers.float.new("fu"); fv = bm.verts.layers.float.new("fv"); fz = bm.verts.layers.float.new("fz")
        bm.verts.ensure_lookup_table(); vs = list(bm.verts); n = len(vs) // seg   # (after the new layers: they move the vertex data)
        prev = None
        for i in range(n):
            ring = vs[i * seg:(i + 1) * seg]; c = sum((v.co for v in ring), Vector()) / seg
            ax = max((v.co - c for v in ring), key=lambda d: d.length); L = ax.length or 1.0; ax = ax / L
            if prev is not None and ax.dot(prev) < 0: ax = -ax
            prev = ax
            for v in ring: v[fu] = i / max(1, n); v[fv] = (v.co - c).dot(ax) / L; v[fz] = 1.0
        for v in vs[n * seg:]: v[fu] = 1.0; v[fv] = 0.0; v[fz] = 1.0
        return bm
    return wrapped


# ================================================================= the surfaces: node networks over the slot colour
class NB:
    """a little node builder: every texture runs in the object's own space, so the pattern holds still on a part and the bake and the
    render agree."""
    def __init__(self, m):
        self.t = m.node_tree; self.t.nodes.clear(); self.N = self.t.nodes; self.L = self.t.links
        self.co = self.N.new("ShaderNodeTexCoord").outputs["Object"]

    def put(self, sock, v):
        if isinstance(v, bpy.types.NodeSocket): self.L.new(v, sock)
        elif v is not None:
            if hasattr(sock, "default_value"):
                dv = sock.default_value
                if hasattr(dv, "__len__") and not isinstance(v, (tuple, list)): v = (v,) * len(dv)
                if hasattr(dv, "__len__") and len(v) != len(dv): v = (tuple(v) + (1.0,))[:len(dv)]
                sock.default_value = v

    def _in(self, nd, key):
        return nd.inputs[key] if isinstance(key, int) else next(s for s in nd.inputs if s.identifier == key or s.name == key)

    def node(self, typ, **ins):
        nd = self.N.new(typ)
        for k, v in ins.items(): self.put(self._in(nd, k.replace("__", " ")), v)
        return nd

    def stretch(self, sx, sy, sz):
        nd = self.N.new("ShaderNodeMapping"); self.put(nd.inputs["Vector"], self.co); nd.inputs["Scale"].default_value = (sx, sy, sz)
        return nd.outputs["Vector"]

    def noise(self, scale, detail=3.0, rough=0.55, vec=None, distort=0.0):
        nd = self.N.new("ShaderNodeTexNoise"); self.put(nd.inputs["Vector"], vec or self.co)
        nd.inputs["Scale"].default_value = scale; nd.inputs["Detail"].default_value = detail
        nd.inputs["Roughness"].default_value = rough; nd.inputs["Distortion"].default_value = distort
        return nd.outputs["Fac"]

    def voronoi(self, scale, out="Distance", vec=None, feature="F1"):
        nd = self.N.new("ShaderNodeTexVoronoi"); nd.feature = feature; self.put(nd.inputs["Vector"], vec or self.co)
        nd.inputs["Scale"].default_value = scale
        return nd.outputs[out]

    def wave(self, scale, axis="Z", distort=0.0, detail=2.0, kind="BANDS", profile="SIN", vec=None):
        nd = self.N.new("ShaderNodeTexWave"); nd.wave_type = kind; nd.wave_profile = profile
        if kind == "BANDS": nd.bands_direction = axis
        else: nd.rings_direction = axis
        self.put(nd.inputs["Vector"], vec or self.co)
        nd.inputs["Scale"].default_value = scale; nd.inputs["Distortion"].default_value = distort; nd.inputs["Detail"].default_value = detail
        return nd.outputs["Fac"]

    def math(self, op, a, b=0.0, clamp=False):
        nd = self.N.new("ShaderNodeMath"); nd.operation = op; nd.use_clamp = clamp
        self.put(nd.inputs[0], a); self.put(nd.inputs[1], b)
        return nd.outputs[0]

    def attr(self, name):
        nd = self.N.new("ShaderNodeAttribute"); nd.attribute_type = "GEOMETRY"; nd.attribute_name = name
        return nd.outputs["Fac"]

    def mixf(self, a, b, f): return self.add(a, self.mul(self.math("SUBTRACT", b, a), f))

    def add(self, a, b): return self.math("ADD", a, b)
    def mul(self, a, b): return self.math("MULTIPLY", a, b)

    def remap(self, x, a0, a1, b0, b1, clamp=True):
        nd = self.N.new("ShaderNodeMapRange"); nd.clamp = clamp; self.put(nd.inputs["Value"], x)
        nd.inputs["From Min"].default_value = a0; nd.inputs["From Max"].default_value = a1
        nd.inputs["To Min"].default_value = b0; nd.inputs["To Max"].default_value = b1
        return nd.outputs["Result"]

    def vmath(self, op, a, b):
        nd = self.N.new("ShaderNodeVectorMath"); nd.operation = op
        self.put(nd.inputs[0], a); self.put(nd.inputs[1], b)
        return nd.outputs["Vector"]

    def tint(self, col, f): return self.vmath("MULTIPLY", col, f)            # a colour times a value (or a colour)

    def lerp(self, a, b, f):                                                 # a colour toward another by f
        return self.vmath("ADD", a, self.vmath("MULTIPLY", self.vmath("SUBTRACT", b, a), f))

    def tone(self, scale, lo, hi, detail=3.0):                               # a slow variation of tone across the part
        return self.remap(self.noise(scale, detail), 0.3, 0.7, lo, hi)

    def weave(self, scale):                                                  # threads across threads
        a = self.wave(scale, "X"); b = self.wave(scale, "Z"); c = self.wave(scale, "Y")
        return self.mul(self.add(a, c), b)


def _piece(b, lo=0.9, hi=1.08): return b.remap(b.attr("rnd"), 0.0, 1.0, lo, hi)     # each piece its own shade

def _feather(b, C):
    """a vane: the shaft down the middle, barbs slanting to the tip, darker at the quill where the next row covers it; each feather its own
    shade. Feathers without the vane marks (tufts) get long streaks instead."""
    fz = b.attr("fz"); fu = b.attr("fu"); av = b.math("ABSOLUTE", b.attr("fv"))
    shaft = b.remap(av, 0.0, 0.09, 1.0, 0.0)
    barbs = b.remap(b.math("SINE", b.mul(b.add(b.mul(fu, 52.0), b.mul(av, 7.0)), 6.2832)), -1.0, 1.0, 0.0, 1.0)
    streaks = b.wave(24, "Z", 7.0, 2.0)
    ridge = b.mixf(b.mul(streaks, 0.6), b.add(b.mul(barbs, 0.3), b.mul(shaft, 0.9)), fz)
    shade = b.mixf(1.0, b.mul(b.remap(fu, 0.0, 0.3, 0.72, 1.0), b.remap(av, 0.8, 1.0, 1.0, 0.86)), fz)
    v = b.mul(b.mul(_piece(b, 0.84, 1.1), shade), b.mixf(b.remap(streaks, 0, 1, 0.92, 1.04), b.add(b.remap(barbs, 0, 1, 0.9, 1.03), b.mul(shaft, -0.16)), fz))
    return dict(col=b.tint(C, v), rough=b.remap(barbs, 0, 1, 0.5, 0.64), height=ridge, bump=0.55, bdist=0.012)
def _down(b, C):
    """small body feathers lapping like tiles: each a shade apart, lighter where it lies on top, darker where the next one covers it."""
    st = b.stretch(1.0, 1.0, 0.7)
    cells = b.voronoi(13, "Distance", vec=st, feature="SMOOTH_F1"); var = b.voronoi(13, "Color", vec=st)
    return dict(col=b.tint(C, b.mul(b.mul(b.remap(var, 0, 1, 0.88, 1.08), b.remap(cells, 0.1, 0.55, 1.05, 0.86)), b.tone(3.0, 0.9, 1.06))),
                rough=0.64, height=b.remap(cells, 0.0, 0.55, 1.0, 0.0), bump=0.35, bdist=0.03)
def _wool(b, C):
    fib = b.noise(80, 2, 0.7); folds = b.noise(2.2, 2, 0.5)
    return dict(col=b.tint(C, b.mul(b.mul(b.tone(3.0, 0.8, 1.16), b.remap(fib, 0, 1, 0.88, 1.1)), b.remap(folds, 0.3, 0.7, 0.85, 1.08))), rough=0.9,
                height=b.add(b.add(b.mul(b.weave(34), 0.3), b.mul(fib, 0.06)), b.mul(folds, 1.6)), bump=0.6, bdist=0.03)
def _linen(b, C):
    folds = b.noise(3.0, 2, 0.5)
    return dict(col=b.tint(C, b.mul(b.tone(4.0, 0.88, 1.04), b.remap(folds, 0.3, 0.7, 0.88, 1.03))), rough=0.82,
                height=b.add(b.mul(b.weave(40), 0.4), b.mul(folds, 1.5)), bump=0.6, bdist=0.03)
def _felt(b, C):
    return dict(col=b.tint(C, b.mul(b.tone(5.0, 0.8, 1.14), b.remap(b.noise(60, 2), 0.3, 0.7, 0.92, 1.06))), rough=0.93,
                height=b.add(b.mul(b.noise(48, 3, 0.65), 0.25), b.mul(b.noise(4, 2), 1.2)), bump=0.5, bdist=0.02)
def _silk(b, C):
    folds = b.wave(3.2, "Z", 3.5, 1.5)
    return dict(col=b.tint(C, b.remap(folds, 0, 1, 0.7, 1.16)), rough=0.33, height=b.add(folds, b.mul(b.noise(9, 2), 0.3)), bump=0.7, bdist=0.05)
def _lace(b, C):
    holes = b.voronoi(30, "Distance"); ring = b.voronoi(9, "Distance")
    return dict(col=b.tint(C, b.mul(b.remap(holes, 0.0, 0.25, 0.66, 1.0), b.remap(ring, 0.3, 0.5, 1.0, 0.9))), rough=0.74,
                height=b.add(b.remap(holes, 0.0, 0.3, 0.0, 1.0), b.remap(ring, 0.3, 0.5, 0.0, 0.5)), bump=0.9, bdist=0.012)
def _cloth(b, C):
    folds = b.noise(2.6, 2, 0.5)
    return dict(col=b.tint(C, b.mul(b.mul(b.tone(3.0, 0.8, 1.12), b.remap(b.noise(1.8, 3), 0.5, 0.75, 1.0, 0.82)), b.remap(folds, 0.3, 0.7, 0.86, 1.06))),
                rough=0.84, height=b.add(b.mul(b.weave(36), 0.4), b.mul(folds, 1.5)), bump=0.65, bdist=0.03)
def _canvas(b, C):
    stain = b.remap(b.noise(1.6, 4, 0.58), 0.46, 0.78, 1.0, 0.72); folds = b.noise(3.0, 2, 0.5)
    return dict(col=b.tint(C, b.mul(b.mul(b.tone(3.0, 0.86, 1.06), stain), b.remap(folds, 0.3, 0.7, 0.88, 1.04))), rough=0.86,
                height=b.add(b.mul(b.weave(30), 0.45), b.mul(folds, 1.4)), bump=0.7, bdist=0.03)
def _rope(b, C):
    strands = b.wave(40, "DIAGONAL", 1.5, 1.0)
    return dict(col=b.tint(C, b.mul(b.remap(strands, 0, 1, 0.62, 1.06), b.tone(4, 0.86, 1.06))), rough=0.88, height=strands, bump=0.9, bdist=0.015)
def _skin(b, C):
    return dict(col=b.tint(b.tint(C, (1.0, 0.95, 0.93)), b.mul(b.tone(9.0, 0.88, 1.05), b.remap(b.noise(60, 2), 0.3, 0.7, 0.96, 1.02))), rough=0.5,
                height=b.add(b.mul(b.noise(70, 3, 0.6), 0.15), b.mul(b.wave(12, "Z", 8.0, 2.0), 0.6)), bump=0.4, bdist=0.012)
def _flesh(b, C):
    return dict(col=b.tint(C, b.tone(6.0, 0.78, 1.08)), rough=0.3, height=b.noise(28, 3, 0.6), bump=0.5, bdist=0.015)
def _ghost(b, C):
    return dict(col=b.tint(C, b.tone(3.0, 0.78, 1.14)), rough=0.45, height=b.noise(20, 3, 0.6), bump=0.4, bdist=0.015, emis=C, es=0.22)
def _hair(b, C):
    streak = b.noise(1.0, 2, 0.5, vec=b.stretch(26, 26, 3))
    return dict(col=b.tint(C, b.remap(streak, 0.3, 0.7, 0.72, 1.14)), rough=0.55, height=streak, bump=0.7, bdist=0.02)
def _scales(b, C):
    cells = b.voronoi(26, "Distance"); var = b.voronoi(26, "Color")
    return dict(col=b.tint(C, b.mul(b.remap(var, 0.0, 1.0, 0.78, 1.12), b.remap(cells, 0.0, 0.45, 1.1, 0.72))), rough=0.5,
                height=b.remap(cells, 0.0, 0.5, 1.0, 0.0), bump=0.85, bdist=0.02)
def _keratin(b, C):
    st = b.noise(1.0, 2, 0.5, vec=b.stretch(18, 2.5, 18))
    return dict(col=b.tint(C, b.remap(st, 0.3, 0.7, 0.8, 1.12)), rough=0.32, height=st, bump=0.3, bdist=0.015)
def _horn(b, C):
    st = b.noise(1.0, 3, 0.55, vec=b.stretch(14, 2.0, 14))
    return dict(col=b.tint(C, b.mul(b.remap(st, 0.3, 0.7, 0.9, 1.05), b.tone(3, 0.92, 1.04))), rough=0.24, height=st, bump=0.25, bdist=0.012)
def _bone(b, C):
    """old bone: ivory gone yellow-brown in broad stains, pitted with pores, a few hairline cracks, each bone a shade apart."""
    stain = b.remap(b.noise(2.2, 4, 0.6), 0.36, 0.7, 0.0, 1.0)
    pores = b.voronoi(28, "Distance")
    cracks = b.voronoi(4.0, "Distance", feature="DISTANCE_TO_EDGE")
    col = b.lerp(b.tint(C, _piece(b, 0.86, 1.0)), b.tint(C, (0.7, 0.57, 0.38)), b.mul(stain, 0.9))
    col = b.tint(b.tint(col, b.remap(pores, 0.0, 0.07, 0.74, 1.0)), b.remap(cracks, 0.0, 0.012, 0.5, 1.0))
    return dict(col=col, rough=b.tone(10, 0.55, 0.74),
                height=b.add(b.add(b.mul(b.noise(16, 3, 0.6), 0.6), b.mul(b.remap(pores, 0.0, 0.08, 0.0, 1.0), 0.5)), b.remap(cracks, 0.0, 0.012, -0.8, 0.0)),
                bump=0.6, bdist=0.012)
def _enamel(b, C):
    return dict(col=b.tint(C, b.mul(b.tone(8.0, 0.88, 1.03), _piece(b, 0.94, 1.02))), rough=0.3, height=b.noise(36, 2, 0.5), bump=0.2, bdist=0.01)
def _wood(b, C, vertical=False):
    grain = b.mul(b.add(b.wave(5.0, "X", 9.0, 3.0), b.wave(5.0, "Y", 9.0, 3.0)), 0.5) if vertical else b.wave(5.0, "Z", 9.0, 3.0)
    fine = b.wave(30, "Y" if vertical else "Z", 4.0, 2.0)
    return dict(col=b.tint(C, b.mul(b.mul(b.remap(grain, 0, 1, 0.62, 1.14), _piece(b, 0.82, 1.12)), b.remap(fine, 0, 1, 0.92, 1.04))), rough=0.72,
                height=b.add(b.add(b.mul(grain, 0.6), b.mul(fine, 0.3)), b.mul(b.noise(34, 2, 0.6), 0.2)), bump=0.75, bdist=0.015)
def _leather(b, C):
    return dict(col=b.tint(C, b.tone(6.0, 0.78, 1.12)), rough=0.5,
                height=b.add(b.mul(b.noise(64, 3, 0.65), 0.5), b.mul(b.voronoi(26, "Distance"), 0.6)), bump=0.55, bdist=0.012)
def _parchment(b, C):
    stain = b.remap(b.noise(2.8, 4, 0.6), 0.42, 0.75, 0.0, 1.0)
    return dict(col=b.lerp(C, b.tint(C, (0.74, 0.58, 0.36)), stain), rough=0.82, height=b.add(b.noise(24, 3), b.mul(b.noise(3, 2), 1.2)), bump=0.4, bdist=0.015)
def _gold(b, C):
    return dict(col=b.tint(C, b.mul(b.tone(6.0, 0.84, 1.08), _piece(b, 0.94, 1.04))), rough=b.tone(13, 0.18, 0.42), metal=1.0,
                height=b.noise(44, 2, 0.5), bump=0.2, bdist=0.01)
def _brass(b, C):
    tarn = b.remap(b.noise(5.0, 3, 0.6), 0.48, 0.72, 0.0, 1.0)
    return dict(col=b.lerp(b.tint(C, 0.84), b.tint(C, (0.5, 0.46, 0.32)), b.mul(tarn, 0.75)), rough=b.add(0.32, b.mul(tarn, 0.3)), metal=1.0,
                height=b.add(b.noise(40, 2, 0.5), b.mul(tarn, 0.5)), bump=0.25, bdist=0.01)
def _steel(b, C):
    scr = b.noise(1.0, 2, 0.5, vec=b.stretch(60, 60, 2))
    return dict(col=b.tint(C, b.remap(scr, 0.3, 0.7, 0.86, 1.06)), rough=b.remap(scr, 0.3, 0.7, 0.14, 0.36), metal=1.0, height=scr, bump=0.12, bdist=0.006)
def _iron(b, C):
    rust = b.remap(b.noise(4.5, 4, 0.62), 0.52, 0.74, 0.0, 1.0)
    return dict(col=b.lerp(b.tint(C, b.tone(5, 0.78, 1.2)), (0.3, 0.13, 0.05), b.mul(rust, 0.85)), rough=b.add(0.48, b.mul(rust, 0.38)),
                metal=b.remap(rust, 0.0, 1.0, 0.75, 0.1), height=b.add(b.mul(b.noise(26, 3, 0.6), 0.6), b.mul(rust, 0.7)), bump=0.6, bdist=0.012)
def _shell(b, C):
    speck = b.remap(b.noise(22, 2, 0.6), 0.58, 0.7, 1.0, 0.66)
    bumps = b.remap(b.voronoi(14, "Distance"), 0, 0.5, 1, 0)
    return dict(col=b.tint(C, b.mul(b.mul(b.tone(4.0, 0.78, 1.14), speck), b.remap(bumps, 0, 1, 0.9, 1.06))), rough=0.36,
                height=b.add(b.mul(b.noise(16, 3, 0.6), 0.5), b.mul(bumps, 0.6)), bump=0.7, bdist=0.015)
def _shell_belly(b, C):
    return dict(col=b.tint(C, b.tone(4.5, 0.86, 1.05)), rough=0.42, height=b.add(b.noise(28, 3, 0.6), b.mul(b.wave(8, "Z", 2.0, 1.0), 0.6)), bump=0.5, bdist=0.012)
def _puffer(b, C):
    return dict(col=b.tint(C, b.tone(5.0, 0.82, 1.08)), rough=0.4, height=b.noise(40, 3, 0.6), bump=0.45, bdist=0.012)
def _fin(b, C):
    rays = b.wave(28, "X", 1.0, 1.0)
    return dict(col=b.tint(C, b.remap(rays, 0, 1, 0.78, 1.06)), rough=0.34, height=rays, bump=0.7, bdist=0.012)
def _barnacle(b, C):
    cells = b.voronoi(30, "Distance")
    return dict(col=b.tint(C, b.remap(cells, 0.0, 0.4, 0.62, 1.05)), rough=0.72, height=cells, bump=0.9, bdist=0.015)
def _weed(b, C):
    return dict(col=b.tint(b.tint(C, (0.9, 1.5, 1.0)), b.tone(6, 0.72, 1.25)), rough=0.3, height=b.noise(20, 3, 0.6), bump=0.5, bdist=0.015)
def _gem(b, C): return dict(col=C, rough=0.06, emis=C, es=0.15)
def _eye(b, C): return dict(col=C, rough=0.06)
def _eye_white(b, C): return dict(col=b.tint(C, b.tone(8, 0.92, 1.02)), rough=0.12)
def _glow(b, C): return dict(col=C, rough=0.4, emis=C, es=1.0)
def _lamp(b, C): return dict(col=C, rough=0.4, emis=C, es=0.53)
def _matte(b, C):
    return dict(col=b.tint(C, b.tone(5.0, 0.86, 1.08)), rough=0.66, height=b.noise(30, 2, 0.5), bump=0.3, bdist=0.01)

SURF = {"feather": _feather, "down": _down, "wool": _wool, "linen": _linen, "felt": _felt, "silk": _silk, "lace": _lace, "cloth": _cloth,
        "canvas": _canvas, "rope": _rope, "skin": _skin, "flesh": _flesh, "ghost": _ghost, "hair": _hair, "scales": _scales,
        "keratin": _keratin, "horn": _horn, "bone": _bone, "enamel": _enamel, "wood": _wood, "wood_v": lambda b, C: _wood(b, C, True),
        "leather": _leather, "parchment": _parchment, "gold": _gold, "brass": _brass, "steel": _steel, "iron": _iron, "shell": _shell,
        "shell_belly": _shell_belly, "puffer": _puffer, "fin": _fin, "barnacle": _barnacle, "weed": _weed, "gem": _gem, "eye": _eye,
        "eye_white": _eye_white, "glow": _glow, "lamp": _lamp, "matte": _matte}


def surface_material(name, C, look):
    """the bake material of one slot colour C made of one surface: a Principled BSDF fed by the surface's network, an Emission shader for
    the flat passes, and the image node every pass bakes into."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = NB(m); s = SURF.get(look, _matte)(b, tuple(C))
    bsdf = b.N.new("ShaderNodeBsdfPrincipled"); out = b.N.new("ShaderNodeOutputMaterial"); em = b.N.new("ShaderNodeEmission")
    b.put(bsdf.inputs["Base Color"], s["col"]); b.put(bsdf.inputs["Roughness"], s.get("rough", 0.6)); b.put(bsdf.inputs["Metallic"], s.get("metal", 0.0))
    if s.get("height") is not None:
        bump = b.N.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = s.get("bump", 0.2); bump.inputs["Distance"].default_value = s.get("bdist", 0.01)
        b.put(bump.inputs["Height"], s["height"]); b.L.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    img = b.N.new("ShaderNodeTexImage"); b.N.active = img
    m_s = {"col": s["col"], "rough": s.get("rough", 0.6), "metal": s.get("metal", 0.0), "emis": s.get("emis"), "es": s.get("es", 0.0)}
    _PASS[m.name] = (b, bsdf, out, em, img, m_s)
    b.L.new(bsdf.outputs[0], out.inputs["Surface"])
    return m

_PASS = {}   # material name -> its builder, BSDF, output, emission, image node and the pass sockets


def _set_pass(m, which, image):
    b, bsdf, out, em, img, s = _PASS[m.name]
    img.image = image; b.N.active = img
    for l in list(out.inputs["Surface"].links): b.L.remove(l)
    for l in list(em.inputs["Color"].links): b.L.remove(l)
    if which in ("normal", "ao"):
        b.L.new(bsdf.outputs[0], out.inputs["Surface"]); return
    em.inputs["Strength"].default_value = 1.0
    if which == "col": b.put(em.inputs["Color"], s["col"])
    elif which == "rough": b.put(em.inputs["Color"], s["rough"])
    elif which == "metal": b.put(em.inputs["Color"], s["metal"])
    elif which == "emis":
        if s["emis"] is None: em.inputs["Color"].default_value = (0, 0, 0, 1)
        else:
            b.put(em.inputs["Color"], s["emis"]); em.inputs["Strength"].default_value = s["es"]
    b.L.new(em.outputs[0], out.inputs["Surface"])


# ================================================================= unwrap, bake, save
def _gpu():
    sc = bpy.context.scene; sc.render.engine = "CYCLES"
    try:
        p = bpy.context.preferences.addons["cycles"].preferences
        for t in ("OPTIX", "CUDA"):
            try:
                p.compute_device_type = t; p.get_devices()
                if any(d.type == t for d in p.devices):
                    for d in p.devices: d.use = d.type == t
                    sc.cycles.device = "GPU"; return t
            except TypeError: pass
    except Exception: pass
    return "CPU"


def unwrap(objs):
    """all the boss's objects unwrapped together into one atlas: smart-projected (each island at the same texel density) and packed."""
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.remove_doubles(threshold=1e-5)
    bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=0.002, area_weight=0.0, correct_aspect=True, scale_to_bounds=False)
    bpy.ops.uv.pack_islands(rotate=True, margin=0.004)
    bpy.ops.object.mode_set(mode="OBJECT")


def _srgb(x):
    x = np.clip(x, 0.0, 1.0)
    return np.where(x <= 0.0031308, x * 12.92, 1.055 * np.power(x, 1 / 2.4) - 0.055)


def _save(arr, path, fmt="PNG", w=None, quality=93):
    """an RGBA array saved as it is (already encoded); halved down to w when asked. JPEG for the colour and the normals (a fifth of the
    PNG's size: the repo carries every boss's set), PNG where the alpha matters (the mask's smoothness)."""
    while w is not None and arr.shape[0] > w:
        h = arr.shape[0] // 2; arr = arr.reshape(h, 2, h, 2, 4).mean(axis=(1, 3))
    n = arr.shape[0]
    img = bpy.data.images.new(os.path.basename(path), n, n, alpha=fmt == "PNG", float_buffer=False)
    img.colorspace_settings.name = "Non-Color"
    img.pixels.foreach_set(np.ascontiguousarray(arr, dtype=np.float32).ravel())
    img.filepath_raw = path; img.file_format = fmt
    if fmt == "JPEG": img.save(quality=quality)
    else: img.save()
    bpy.data.images.remove(img)


def bake(P, out, size=2048, ao_dist=0.22, ao_k=0.72):
    """bakes the boss's surfaces into Boss_<id>_Albedo / _Normal / _Mask / _Emission.png in out; the slot materials come back afterwards
    (the FBX keeps them, for a game build without the textures)."""
    objs = [P.body] + list(P.spin)
    dev = _gpu(); sc = bpy.context.scene
    if sc.world is None: sc.world = bpy.data.worlds.new("W")
    sc.world.light_settings.distance = ao_dist
    unwrap(objs)
    keep, made = {}, {}
    for o in objs:   # one bake material per (slot, surface) the object uses
        me = o.data; n = len(me.polygons)
        slot = np.zeros(n, np.int32); me.polygons.foreach_get("material_index", slot)
        look = np.zeros(n, np.int32)
        at = me.attributes.get("look")
        if at is not None: at.data.foreach_get("value", look)
        keep[o.name] = ([m for m in me.materials], slot.copy())
        pairs = sorted(set(zip(slot.tolist(), look.tolist())))
        me.materials.clear()
        index = {}
        for si, li in pairs:
            sname = EP.SLOTS[si]; lname = LOOKS[li] or "matte"
            key = (si, li)
            if key not in made:
                src = P.mats[si]; bs = next(x for x in src.node_tree.nodes if x.type == "BSDF_PRINCIPLED")
                C = tuple(bs.inputs["Base Color"].default_value)[:3]
                made[key] = surface_material("bake_%s_%s_%s" % (P.id, sname, lname), C, lname)
            index[key] = len(me.materials); me.materials.append(made[key])
        me.polygons.foreach_set("material_index", np.array([index[(s_, l_)] for s_, l_ in zip(slot.tolist(), look.tolist())], np.int32))
        me.update()
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bk = sc.render.bake; bk.margin = 10; bk.use_clear = True; bk.target = "IMAGE_TEXTURES"
    res = {}
    for which, kind, spp in (("col", "EMIT", 8), ("rough", "EMIT", 4), ("metal", "EMIT", 4), ("emis", "EMIT", 4), ("normal", "NORMAL", 8), ("ao", "AO", 160)):
        img = bpy.data.images.new("bake_" + which, size, size, alpha=True, float_buffer=True)
        img.generated_color = (0.5, 0.5, 1.0, 1.0) if which == "normal" else (0, 0, 0, 1) if which != "ao" else (1, 1, 1, 1)
        for m in made.values(): _set_pass(m, which, img)
        sc.cycles.samples = spp
        if kind == "NORMAL":
            bpy.ops.object.bake(type="NORMAL", normal_space="TANGENT", normal_r="POS_X", normal_g="POS_Y", normal_b="POS_Z", margin=10, use_clear=True)
        else:
            bpy.ops.object.bake(type=kind, margin=10, use_clear=True)
        a = np.empty(size * size * 4, np.float32); img.pixels.foreach_get(a)
        res[which] = a.reshape(size, size, 4); bpy.data.images.remove(img)
        print("BAKE", P.id, which, dev)
    ao = res["ao"][..., :1]
    occl = 1.0 - ao_k * (1.0 - np.clip(ao, 0, 1))
    alb = np.concatenate([_srgb(res["col"][..., :3] * occl), np.ones((size, size, 1), np.float32)], -1)
    nrm = np.concatenate([res["normal"][..., :3], np.ones((size, size, 1), np.float32)], -1)
    mask = np.concatenate([res["metal"][..., :1], np.zeros((size, size, 2), np.float32), 1.0 - res["rough"][..., :1]], -1)
    emi = np.concatenate([_srgb(res["emis"][..., :3]), np.ones((size, size, 1), np.float32)], -1)
    os.makedirs(out, exist_ok=True)
    paths = {}
    for nm, arr, fmt, w in (("Albedo", alb, "JPEG", None), ("Normal", nrm, "JPEG", None), ("Mask", mask, "PNG", size // 2), ("Emission", emi, "JPEG", size // 2)):
        paths[nm] = os.path.join(out, "Boss_%s_%s.%s" % (P.id, nm, "jpg" if fmt == "JPEG" else "png"))
        for old in ("png", "jpg"):   # a set baked before in the other format goes
            q = os.path.join(out, "Boss_%s_%s.%s" % (P.id, nm, old))
            if q != paths[nm] and os.path.exists(q): os.remove(q)
        _save(arr, paths[nm], fmt, w, 95 if nm == "Normal" else 92)
    for o in objs:   # the slot materials back
        mats, slot = keep[o.name]; me = o.data
        me.materials.clear()
        for m in mats: me.materials.append(m)
        me.polygons.foreach_set("material_index", slot); me.update()
    return paths


def export(P, out):
    bpy.ops.object.select_all(action="DESELECT")
    P.body.select_set(True)
    for s in P.spin: s.select_set(True)
    bpy.ops.export_scene.fbx(filepath=os.path.join(out, "Boss_" + P.id + ".fbx"), use_selection=True, object_types={"MESH"},
                             apply_scale_options="FBX_SCALE_UNITS", axis_forward="Z", axis_up="Y", bake_space_transform=True,
                             mesh_smooth_type="FACE", use_mesh_modifiers=True, add_leaf_bones=False)


def finish_baked(P, out, size=2048, do_export=True):
    """P.finish() without its export and its quick previews, then the bake into out, then the FBX (now with its UVs) into out."""
    exp = AB.EXPORT; AB.EXPORT = False; prev = P.preview; P.preview = lambda: None
    try: P.finish()
    finally: AB.EXPORT = exp; P.preview = prev
    paths = bake(P, out, size)
    if do_export: export(P, out)
    return paths


def textured(P, paths, emission=3.2):
    """every object of the boss given one material made of its baked textures, as the game draws it (for the previews)."""
    m = bpy.data.materials.new("baked_" + P.id); m.use_nodes = True; nt = m.node_tree; N = nt.nodes; L = nt.links
    bsdf = next(n for n in N if n.type == "BSDF_PRINCIPLED")
    def tex(key, color):
        n = N.new("ShaderNodeTexImage"); n.image = bpy.data.images.load(paths[key], check_existing=True)
        n.image.colorspace_settings.name = "sRGB" if color else "Non-Color"; return n
    a = tex("Albedo", True); L.new(a.outputs["Color"], bsdf.inputs["Base Color"])
    nm = N.new("ShaderNodeNormalMap"); L.new(tex("Normal", False).outputs["Color"], nm.inputs["Color"]); L.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    mk = tex("Mask", False); sp = N.new("ShaderNodeSeparateColor"); L.new(mk.outputs["Color"], sp.inputs["Color"])
    L.new(sp.outputs[0], bsdf.inputs["Metallic"])
    inv = N.new("ShaderNodeMath"); inv.operation = "SUBTRACT"; inv.inputs[0].default_value = 1.0; L.new(mk.outputs["Alpha"], inv.inputs[1])
    L.new(inv.outputs[0], bsdf.inputs["Roughness"])
    e = tex("Emission", True); L.new(e.outputs["Color"], bsdf.inputs["Emission Color"]); bsdf.inputs["Emission Strength"].default_value = emission
    for o in [P.body] + list(P.spin):
        n = len(o.data.materials); o.data.materials.clear()
        for _ in range(max(1, n)): o.data.materials.append(m)
    return m
