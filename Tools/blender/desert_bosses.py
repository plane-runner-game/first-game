# Sky Squad, the desert pyramids' five bosses (2026-10-10: "give me for desert pyramids and japanese island"): the magic carpet, the anubis
# guardian, the winged sphinx, the sun barque and the sky pyramid. Built from code like the other worlds' bosses (alien_bosses.py lends its
# Boss class and shapes).
# Run: blender -b -P Tools/blender/desert_bosses.py -- <out dir> [export] [ids,comma,separated]
# Conventions as alien_bosses.py: +Y nose, +Z up, +X right; "Flap*" rock about the nose axis, "Sway*" about the wing axis, "Spin*" turn slowly
# about up, "Cloth" stays still without the outline, "Muzzle" is where his shots leave from.
import bpy, bmesh, math, sys, os, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mathutils import Vector, Matrix
from enemy_planes import loft, sweep, lathe, box, hull, tube, mirror_x, airfoil
import alien_bosses as AB
from alien_bosses import Boss, xf, ball, pipe, cone, bez, torus, sheet, grow, ang

import bmesh
from mathutils.bvhtree import BVHTree
from enemy_planes import loft, sweep, lathe, box, hull, tube, mirror_x, airfoil
from alien_bosses import Boss, xf, ball, pipe, cone, bez, torus, sheet, grow, ang, lerp_keys, spine_frames, body_loft, skin, oriented_ball, frame, sheet_solid, ribbon

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ONLY = argv[2].split(",") if len(argv) > 2 and argv[2] else None

GOLD = ((0.98, 0.76, 0.22), 0.8)
LAPIS = ((0.10, 0.25, 0.70), 0.6)

def fine(keys, step=0.08):
    secs = []
    for a0, a1 in zip(keys, keys[1:]):
        n = max(2, int((a1[0] - a0[0]) / step))
        secs += [tuple(u + (v - u) * i / n for u, v in zip(a0, a1)) for i in range(n)]
    secs.append(keys[-1])
    return secs

def grid_surface(fn, nu, nv, thick=0.04):
    """a thick sheet from fn(u, v) -> point, u and v in [0, 1]."""
    bm = bmesh.new()
    top = [[bm.verts.new(fn(i / nu, j / nv) + Vector((0, 0, thick * 0.5))) for j in range(nv + 1)] for i in range(nu + 1)]
    bot = [[bm.verts.new(fn(i / nu, j / nv) - Vector((0, 0, thick * 0.5))) for j in range(nv + 1)] for i in range(nu + 1)]
    for i in range(nu):
        for j in range(nv):
            bm.faces.new((top[i][j], top[i + 1][j], top[i + 1][j + 1], top[i][j + 1]))
            bm.faces.new((bot[i][j], bot[i][j + 1], bot[i + 1][j + 1], bot[i + 1][j]))
    for i in range(nu):
        bm.faces.new((top[i][0], bot[i][0], bot[i + 1][0], top[i + 1][0])); bm.faces.new((top[i][nv], top[i + 1][nv], bot[i + 1][nv], bot[i][nv]))
    for j in range(nv):
        bm.faces.new((top[0][j], top[0][j + 1], bot[0][j + 1], bot[0][j])); bm.faces.new((top[nu][j], bot[nu][j], bot[nu][j + 1], top[nu][j + 1]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


# ================================================================= 1. the magic carpet
def D_barque():
    """Ra's sun barque sailing the sky: a golden papyrus boat with curled lotus prow and stern, a shrine amidships under a blazing sun disc
    held by a cobra, a square sail painted with the eye, and oars on each side that row."""
    P = Boss("barque", {"Base": ((0.85, 0.62, 0.25), 0.6), "Belly": ((0.95, 0.90, 0.78), 0.3), "Accent": LAPIS, "Trim": GOLD,
                        "Glass": ((0.25, 0.85, 0.65), 0.95), "Dark": ((0.10, 0.07, 0.05), 0.5), "Glow": ((1.0, 0.62, 0.15), 0.5),
                        "Metal": ((0.70, 0.18, 0.12), 0.5), "Lamp": ((1.0, 0.88, 0.45), 0.8)})
    P.obj("Hull", loft([(1.7, 0.08, 0.08, 0, 0.3), (1.4, 0.45, 0.3, 0, 0.05), (0.5, 0.62, 0.35, 0, -0.05), (-0.6, 0.6, 0.35, 0, -0.05), (-1.4, 0.4, 0.3, 0, 0.05), (-1.7, 0.08, 0.08, 0, 0.3)], 18, sq=1.4),
          lambda c, n: "Accent" if -0.05 < c.z < 0.05 else ("Trim" if c.z > 0.18 else "Base"), 1)
    for sy in (1, -1):   # lotus prow and stern, curling up
        curl = bez((0, sy * 1.65, 0.3), (0, sy * 2.0, 0.6), (0, sy * 2.05, 1.05), (0, sy * 1.85, 1.2), 7)
        P.obj("Curl", pipe(curl, [0.12, 0.11, 0.1, 0.09, 0.08, 0.07, 0.06, 0.05], 8), "Trim")
        for k in range(6):
            a = math.radians(-60 + k * 24)
            P.obj("Petal", cone(curl[-1], curl[-1] + Vector((math.sin(a) * 0.25, sy * 0.05, 0.2 + 0.1 * math.cos(a))), 0.06, 5), "Metal" if k % 2 else "Accent", 0, False)
    P.obj("Deck", box((0, 0, 0.32), (0.95, 3.0, 0.05)), "Belly", 0, False)
    # the shrine and the sun
    P.obj("Shrine", box((0, -0.1, 0.62), (0.7, 0.75, 0.55)), lambda c, n: "Accent" if abs(n.y) > 0.6 and (c.z * 6) % 1.0 < 0.4 else "Trim", 0, False)
    P.obj("ShrineTop", box((0, -0.1, 0.94), (0.82, 0.86, 0.08)), "Trim", 0, False)
    P.obj("Cobra", pipe(bez((0, 0.15, 0.95), (0, 0.2, 1.15), (0, 0.15, 1.3), (0, 0.05, 1.4), 5), [0.05, 0.06, 0.07, 0.06, 0.05, 0.04], 6), "Trim")
    P.obj("Sun", ball((0, -0.1, 1.75), (0.48, 0.12, 0.48), 20, 8), "Glow")
    P.obj("SunRim", torus(0.5, 0.05, 0.0, 24, 6), "Trim"); P.parts[-1].data.transform(Matrix.Translation((0, -0.1, 1.75)) @ Matrix.Rotation(math.radians(90), 4, "X"))
    for k in range(12):
        a = 2 * math.pi * k / 12
        P.part("RollRays", cone((math.cos(a) * 0.56, -0.12, 1.75 + math.sin(a) * 0.56), (math.cos(a) * 0.85, -0.12, 1.75 + math.sin(a) * 0.85), 0.06, 4), "Lamp", (0, -0.1, 1.75), 0, False)
    # mast and sail with the eye
    P.obj("Mast", pipe([(0, -0.95, 0.3), (0, -0.95, 1.9)], [0.04, 0.035], 6), "Dark")
    P.obj("Yard", pipe([(-0.7, -0.95, 1.85), (0.7, -0.95, 1.85)], [0.03, 0.03], 6), "Dark")
    def sail(u, v):
        return Vector(((u - 0.5) * 1.3, -0.92 + 0.15 * math.sin(math.pi * u) * math.sin(math.pi * v), 1.0 + v * 0.82))
    bm = grid_surface(lambda u, v: sail(u, v), 8, 6, 0.02)
    P.part("Cloth", bm, lambda c, n: "Accent" if ((c.x / 0.28) ** 2 + ((c.z - 1.42) / 0.12) ** 2 < 1.0) else ("Metal" if (c.z * 6) % 1.0 < 0.18 else "Belly"), (0, 0, 0), 0, False)
    # the oars, rowing
    for s in (1, -1):
        for k, y in enumerate((0.9, 0.3, -0.3, -0.9)):
            hub = (s * 0.58, y, 0.25)
            P.part("Sway%d" % (k * 2 + (1 if s > 0 else 0)), pipe([hub, (s * 1.25, y - 0.1, -0.45)], [0.03, 0.03], 5), "Dark", hub)
            P.part("Sway%d" % (k * 2 + (1 if s > 0 else 0)), box((s * 1.3, y - 0.11, -0.55), (0.06, 0.18, 0.25)), "Trim", hub, 0, False)
    P.part("Muzzle", ball((0, 0.0, 1.75), (0.1, 0.05, 0.1), 8, 4), "Glow", (0, 0.0, 1.75))
    return P


# ================================================================= 5. the sky pyramid
def bar(a, b, w, t, up=(0, 1, 0)):
    """a squared-off bar between two points, w wide (across, in the face plane) and t thick (toward +Y)."""
    a, b = Vector(a), Vector(b); d = (b - a).normalized(); n = Vector(up)
    if abs(d.dot(n)) > 0.95: n = Vector((0, 0, 1))
    s = d.cross(n).normalized() * w * 0.5; f = n * t * 0.5
    pts = [p + ds + df for p in (a, b) for ds in (s, -s) for df in (f, -f)]
    return hull([tuple(p) for p in pts])


# ================================================================= 4 (new). the pharaoh cobra

# ================================================================= carpet (2026-10-13 remake)
# Sinbad's carpet, remade 2026-10-13 (merged into Tools/blender/desert_bosses.py as D_carpet).

CP_W, CP_L, CP_T = 1.3, 1.9, 0.05      # the rug: half width, half length, thickness
CP_A, CP_WAVE = 0.14, 1.75             # the ripple: height and wavelength (a crest under Sinbad, troughs under the lamp and the chest)

def cp_z(x, y):
    """the rug's middle surface: a wave running down its length, the sides sagging up a little, the front edge lifting into the wind."""
    lift = 0.16 * max(0.0, (y - 1.15) / (CP_L - 1.15)) ** 2
    return CP_A * math.cos(2 * math.pi * y / CP_WAVE) + 0.07 * (x / CP_W) ** 2 + lift

def cp_top(x, y, lift=0.0):
    return Vector((x, y, cp_z(x, y) + CP_T * 0.5 + lift))

def cp_axis(lo, hi, breaks, step):
    """grid lines from lo to hi, at every break exactly and no further apart than step."""
    pts = sorted(set([lo, hi] + [b for b in breaks if lo < b < hi]))
    out = [pts[0]]
    for a, b in zip(pts, pts[1:]):
        n = max(1, int(math.ceil((b - a) / step)))
        out += [a + (b - a) * i / n for i in range(1, n + 1)]
    return out

CP_BANDS = (0.06, 0.09, 0.30, 0.335)   # outer gold guard, a crimson line, the indigo main border, the inner gold guard; the field inside

def cp_rug():
    """the rug as a rippled slab: a fine top following the wave, a skirt round the edge, a plain back."""
    bx = [s * (CP_W - d) for d in CP_BANDS for s in (1, -1)]
    by = [s * (CP_L - d) for d in CP_BANDS for s in (1, -1)]
    xs = cp_axis(-CP_W, CP_W, bx, 0.11); ys = cp_axis(-CP_L, CP_L, by, 0.075)
    bm = bmesh.new()
    top = [[bm.verts.new(cp_top(x, y)) for y in ys] for x in xs]
    for i in range(len(xs) - 1):
        for j in range(len(ys) - 1):
            bm.faces.new((top[i][j], top[i + 1][j], top[i + 1][j + 1], top[i][j + 1]))
    ring = [top[i][0] for i in range(len(xs))] + [top[-1][j] for j in range(1, len(ys))] + \
           [top[i][-1] for i in range(len(xs) - 2, -1, -1)] + [top[0][j] for j in range(len(ys) - 2, 0, -1)]
    low = [bm.verts.new(v.co - Vector((0, 0, CP_T))) for v in ring]
    for k in range(len(ring)):
        k2 = (k + 1) % len(ring)
        bm.faces.new((ring[k], low[k], low[k2], ring[k2]))
    bxs = [-CP_W + 2 * CP_W * i / 10 for i in range(11)]; bys = [-CP_L + 2 * CP_L * j / 24 for j in range(25)]
    bot = [[bm.verts.new(cp_top(x, y) - Vector((0, 0, CP_T))) for y in bys] for x in bxs]
    for i in range(10):
        for j in range(24):
            bm.faces.new((bot[i][j], bot[i][j + 1], bot[i + 1][j + 1], bot[i + 1][j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm

def cp_rug_paint(c, n):
    if n.z < 0.3: return "Base"
    d = min(CP_W - abs(c.x), CP_L - abs(c.y))
    if d < CP_BANDS[0]: return "Trim"
    if d < CP_BANDS[1]: return "Base"
    if d < CP_BANDS[2]: return "Accent"
    if d < CP_BANDS[3]: return "Trim"
    return "Base"

def cp_decal(outline, lift, rings=2):
    """a flat motif lying on the rug's top (it follows the wave): outline is a list of (x, y); a fan from its middle in rings."""
    cx = sum(p[0] for p in outline) / len(outline); cy = sum(p[1] for p in outline) / len(outline)
    bm = bmesh.new()
    mid = bm.verts.new(cp_top(cx, cy, lift)); prev = None
    for k in range(1, rings + 1):
        t = k / rings
        cur = [bm.verts.new(cp_top(cx + (x - cx) * t, cy + (y - cy) * t, lift)) for (x, y) in outline]
        n = len(cur)
        for i in range(n):
            if prev is None: bm.faces.new((mid, cur[i], cur[(i + 1) % n]))
            else: bm.faces.new((prev[i], cur[i], cur[(i + 1) % n], prev[(i + 1) % n]))
        prev = cur
    for f in bm.faces:
        f.normal_update()
        if f.normal.z < 0: f.normal_flip()
    return bm

def cp_lobed(cx, cy, rx, ry, lobes, depth, n=48, quarter=None):
    """a lobed oval outline (a medallion); quarter=(sx, sy) keeps only the quarter reaching away from (cx, cy) in -sx, -sy (a spandrel)."""
    pts = []
    if quarter:
        sx, sy = quarter
        pts.append((cx, cy))
        for i in range(n + 1):
            a = math.pi / 2 * i / n
            k = 1 - depth * (0.5 - 0.5 * math.cos(lobes * 2 * a))
            pts.append((cx - sx * rx * k * math.cos(a), cy - sy * ry * k * math.sin(a)))
        return pts
    for i in range(n):
        a = 2 * math.pi * i / n
        k = 1 - depth * (0.5 - 0.5 * math.cos(lobes * a))
        pts.append((cx + rx * k * math.sin(a), cy + ry * k * math.cos(a)))
    return pts

def cp_star(cx, cy, r0, r1, points, rot=0.0):
    return [(cx + (r1 if i % 2 == 0 else r0) * math.sin(rot + math.pi * i / points), cy + (r1 if i % 2 == 0 else r0) * math.cos(rot + math.pi * i / points))
            for i in range(points * 2)]

def cp_diamond(cx, cy, rx, ry):
    return [(cx, cy + ry), (cx + rx, cy), (cx, cy - ry), (cx - rx, cy)]

def cp_tassel(base, out, L):
    """one knotted tassel of the fringe: the warp threads gathered in a knot at the rug's edge, hanging out in a loose bundle."""
    out = Vector(out).normalized()
    a = Vector(base); b = a + out * (L * 0.18); m = a + out * (L * 0.6) + Vector((0, 0, -L * 0.25)); e = a + out * L + Vector((0, 0, -L * 0.45))
    return cp_join(ball(tuple(b), (0.032, 0.032, 0.03), 8, 4), pipe(bez(b, b + out * L * 0.2, m, e, 4), [0.02, 0.022, 0.026, 0.032, 0.0], 6))

def cp_join(*bms):
    import bpy
    out = bmesh.new()
    for b in bms:
        me = bpy.data.meshes.new("_j"); b.to_mesh(me); out.from_mesh(me); b.free(); bpy.data.meshes.remove(me)
    return out

def cp_blade(spine, th=0.018):
    """a sabre blade along spine (a curve in the x-z plane): the back on the spine, the edge out to the side away from the curve's centre,
    widening a little toward the point, then sweeping to the point."""
    bm = bmesh.new(); n = len(spine); rows = []
    for i, p in enumerate(spine):
        t = (spine[min(i + 1, n - 1)] - spine[max(i - 1, 0)]).normalized()
        side = t.cross(Vector((0, 1, 0))).normalized()
        u = i / (n - 1)
        w = (0.045 + 0.03 * u) * (1.0 if u < 0.82 else max(0.0, (1 - u) / 0.18))
        e = p + side * w; m = p + side * w * 0.45
        rows.append([bm.verts.new(p + Vector((0, th * 0.5, 0))), bm.verts.new(m + Vector((0, th * 0.25, 0))), bm.verts.new(e),
                     bm.verts.new(m - Vector((0, th * 0.25, 0))), bm.verts.new(p - Vector((0, th * 0.5, 0)))])
    for r0, r1 in zip(rows, rows[1:]):
        for k in range(5):
            k2 = (k + 1) % 5
            bm.faces.new((r0[k], r0[k2], r1[k2], r1[k]))
    bm.faces.new(list(reversed(rows[0]))); bm.faces.new(rows[-1])
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm

def cp_halfcyl(c, R, length, seg=12):
    """an open chest's barrel lid: half a cylinder along x about c, the curve up."""
    bm = bmesh.new(); c = Vector(c)
    ends = []
    for sx in (-0.5, 0.5):
        ends.append([bm.verts.new(c + Vector((sx * length, R * math.cos(math.pi * i / seg), R * math.sin(math.pi * i / seg)))) for i in range(seg + 1)])
    for i in range(seg):
        bm.faces.new((ends[0][i], ends[0][i + 1], ends[1][i + 1], ends[1][i]))
    for e in ends: bm.faces.new(e)
    bm.faces.new((ends[0][0], ends[1][0], ends[1][seg], ends[0][seg]))   # the underside: the lining
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def D_carpet():
    """Sinbad's carpet (2026-10-13, remade: "same as the alien bosses - realistic details, scarier, keep the cartoon shape"): the same
    flying carpet with Sinbad standing on it, the genie lamp and the chest of gold, now built like a real Persian rug and a real sailor
    of the old tales. The rug is a city rug laid out the way they are woven: an outer gold guard stripe, a thin crimson line, a wide indigo
    main border with gold eight-petalled rosettes evenly along it and small ivory lozenges between them, an inner gold guard, and a crimson
    field; in the middle of the field a great lobed medallion - gold rim, indigo, an ivory ring, crimson, a gold star at its heart - with a
    pendant at each end of it, a quarter of the same medallion in each corner of the field (the spandrels), and small gold lozenges strewn
    evenly over the rest of the field. At both ends the warp threads hang out as a knotted fringe of ivory tassels, a big gold-capped
    crimson tassel at each corner.
    Sinbad is a hard sea-captain, not a cartoon prince: a weathered, hook-nosed face with a heavy scowling brow, deep-set eyes, a red scar
    slashed across his left eye and cheek, a black beard falling to a point and a thick moustache curling up at the ends, his mouth open on
    bared teeth; a crimson turban wound in crossing folds with a gold-striped wrap, an emerald brooch in front and an ivory plume, a gold hoop
    in his ear; an open indigo vest edged in gold embroidery over a bare, muscular chest with a gold chain and medallion, a wide crimson sash
    knotted at his hip with a curved khanjar dagger tucked in front, baggy emerald sirwal gathered in gold cuffs at the ankle, curled golden
    slippers; leather bracers studded with gold on his forearms. His right arm raises a shamshir - the deeply curved, narrow Persian sabre,
    its blade widening a little toward the point, straight quillons ending in balls, langets over the blade, a wrapped grip and the bent
    pistol pommel - ready to slash (SwayArm); his left hand points at the player.
    Before him stands a real brass oil lamp - a long low body, a lid with a finial, a foot ring, a looped handle at the back and a long
    spout with a little flame at its tip - and out of the spout the genie's smoke rises in a twisted plume, three ropes of smoke winding
    round each other as they climb (SpinSmoke), into the genie himself: a broad blue torso tapering into the smoke, bald with a topknot in a
    gold ring, pointed ears with gold hoops, burning yellow eyes under heavy brows, a snarling mouth with a goatee, gold cuffs on his
    wrists, his hands cupped round the fireball he throws (his shots leave from it). Behind Sinbad a dark wooden chest bound in brass, its
    barrel lid thrown open on a crimson lining, heaped with gold coins, emeralds, rubies and a string of pearls, coins spilt on the rug.
    It flies the way a magic carpet does: the whole rug ripples in a long wave running down its length, the front edge lifting into the
    wind, and its fringes stream and swing at both ends (SwayFringeF, SwayFringeB)."""
    P = Boss("carpet", {"Base": ((0.52, 0.05, 0.07), 0.35), "Belly": ((0.66, 0.42, 0.27), 0.3), "Accent": ((0.07, 0.10, 0.34), 0.4),
                        "Trim": ((0.98, 0.74, 0.22), 0.8), "Glass": ((0.04, 0.42, 0.30), 0.7), "Dark": ((0.06, 0.04, 0.035), 0.35),
                        "Glow": ((0.16, 0.42, 0.95), 0.5), "Metal": ((0.86, 0.82, 0.72), 0.75), "Lamp": ((1.0, 0.82, 0.35), 0.8)})
    W, L = CP_W, CP_L
    deco = lambda bm, slot: P.part("ClothRug", bm, slot, (0, 0, 0))   # the woven pattern: thin, so without the toon outline
    # ---------------------------------------------------------------- the rug
    P.obj("Rug", cp_rug(), cp_rug_paint, 0, False)
    mb = (CP_BANDS[1] + CP_BANDS[2]) * 0.5   # the middle line of the main border
    # rosettes along the main border, evenly, with an ivory lozenge between each two
    def rosette(x, y):
        deco(cp_decal(cp_star(x, y, 0.05, 0.085, 8), 0.004), "Trim")
        deco(cp_decal(cp_star(x, y, 0.016, 0.03, 4), 0.008, 1), "Base")
    xa, xb = -(W - mb), W - mb; ya, yb = -(L - mb), L - mb
    ns, ne = 11, 6
    for i in range(ns + 1):
        y = ya + (yb - ya) * i / ns
        for x in (xa, xb): rosette(x, y)
        if i < ns:
            ym = y + (yb - ya) / ns * 0.5
            for x in (xa, xb): deco(cp_decal(cp_diamond(x, ym, 0.04, 0.07), 0.004, 1), "Metal")
    for i in range(1, ne):
        x = xa + (xb - xa) * i / ne
        for y in (ya, yb): rosette(x, y)
    for i in range(ne):
        xm = xa + (xb - xa) * (i + 0.5) / ne
        for y in (ya, yb): deco(cp_decal(cp_diamond(xm, y, 0.07, 0.04), 0.004, 1), "Metal")
    # the central medallion, in layers, and its two pendants
    for k, (rx, ry, slot) in enumerate(((0.66, 0.98, "Trim"), (0.61, 0.92, "Accent"), (0.44, 0.67, "Metal"), (0.38, 0.59, "Base"))):
        deco(cp_decal(cp_lobed(0, 0, rx, ry, 16, 0.1), 0.003 + 0.002 * k, 3), slot)
    deco(cp_decal(cp_star(0, 0, 0.12, 0.26, 8), 0.012, 2), "Trim")
    deco(cp_decal(cp_star(0, 0, 0.04, 0.09, 8, math.pi / 8), 0.015, 1), "Accent")
    for sy in (1, -1):
        deco(cp_decal(cp_diamond(0, sy * 1.12, 0.16, 0.16), 0.004, 2), "Trim")
        deco(cp_decal(cp_diamond(0, sy * 1.12, 0.09, 0.09), 0.007, 1), "Accent")
        deco(cp_decal(cp_diamond(0, sy * 1.3, 0.05, 0.07), 0.004, 1), "Trim")
    # the spandrels: a quarter medallion in each corner of the field
    fx, fy = W - CP_BANDS[3], L - CP_BANDS[3]
    for sx in (1, -1):
        for sy in (1, -1):
            deco(cp_decal(cp_lobed(sx * fx, sy * fy, 0.62, 0.78, 5, 0.07, 40, (sx, sy)), 0.003, 3), "Trim")
            deco(cp_decal(cp_lobed(sx * fx, sy * fy, 0.55, 0.7, 5, 0.07, 40, (sx, sy)), 0.005, 2), "Accent")
            deco(cp_decal(cp_lobed(sx * fx, sy * fy, 0.3, 0.38, 3, 0.08, 24, (sx, sy)), 0.007, 1), "Metal")
    # small gold lozenges strewn evenly over the rest of the field
    for i in range(-3, 4):
        for j in range(-6, 7):
            x, y = i * 0.27 + (0.135 if j % 2 else 0.0), j * 0.25
            if abs(x) > fx - 0.1 or abs(y) > fy - 0.1: continue
            if (x / 0.75) ** 2 + (y / 1.12) ** 2 < 1.0: continue            # the medallion
            if abs(y) > 1.0 and abs(y) < 1.45 and abs(x) < 0.25: continue   # the pendants
            if ((fx - abs(x)) / 0.68) + ((fy - abs(y)) / 0.86) < 1.15: continue   # the spandrels
            deco(cp_decal(cp_diamond(x, y, 0.035, 0.05), 0.003, 1), "Trim")
    # the fringe at both ends: knotted ivory tassels, a gold-capped crimson tassel at each corner (they stream and swing)
    for sy, name in ((1, "SwayFringeF"), (-1, "SwayFringeB")):
        hub = cp_top(0, sy * L, -CP_T * 0.5)
        n = 15
        for i in range(n):
            x = -W + 0.1 + (2 * W - 0.2) * i / (n - 1)
            P.part(name, cp_tassel(cp_top(x, sy * L, -CP_T * 0.5), (0.04 * x, sy, 0), 0.26), "Metal", hub)
        for sx in (1, -1):
            c = cp_top(sx * W, sy * L, -CP_T * 0.5)
            out = Vector((sx * 0.5, sy, 0)).normalized()
            cap = c + out * 0.06 + Vector((0, 0, -0.03))
            P.part(name, ball(tuple(cap), (0.05, 0.05, 0.06), 10, 5), "Trim", hub)
            P.part(name, pipe(bez(cap, cap + out * 0.12, cap + out * 0.2 + Vector((0, 0, -0.1)), cap + out * 0.26 + Vector((0, 0, -0.22)), 5),
                              [0.045, 0.05, 0.06, 0.07, 0.07, 0.0], 8), "Base", hub)
    # ---------------------------------------------------------------- Sinbad (stands on the crest of the wave)
    skin = "Belly"
    G = cp_z(0, 0) + CP_T * 0.5 + 0.03     # his soles
    y0 = 0.0
    # legs: very baggy sirwal gathered at the ankle in gold cuffs, curled golden slippers, a wide stance, the right foot forward
    for s, fy in ((1, 0.22), (-1, -0.12)):
        sole = cp_z(s * 0.32, y0 + fy) + CP_T * 0.5 + 0.03
        hip = Vector((s * 0.15, y0, G + 1.0)); knee = Vector((s * 0.28, y0 + fy * 0.55, G + 0.55)); ankle = Vector((s * 0.32, y0 + fy, sole + 0.14))
        mid = (hip + knee) * 0.5 + Vector((s * 0.03, 0, 0)); calf = (knee + ankle) * 0.5 + Vector((s * 0.02, 0, 0))
        P.obj("Sirwal", pipe([hip, mid, knee, calf, ankle + Vector((0, 0, 0.1))], [0.18, 0.23, 0.24, 0.2, 0.1], 14), "Glass", 1)
        P.obj("Cuff", pipe([ankle + Vector((0, 0, 0.11)), ankle + Vector((0, 0, 0.02))], [0.09, 0.08], 12), "Trim")
        P.obj("Slipper", ball(tuple(ankle + Vector((0, 0.07, -0.06))), (0.09, 0.18, 0.075), 12, 6), "Trim")
        P.obj("Sole", ball(tuple(ankle + Vector((0, 0.06, -0.115))), (0.085, 0.17, 0.02), 10, 3), "Dark")
        tip = ankle + Vector((0, 0.24, -0.06))
        P.obj("SlipperToe", pipe(bez(tip, tip + Vector((0, 0.09, 0.0)), tip + Vector((0, 0.15, 0.08)), tip + Vector((0, 0.08, 0.15)), 6),
                                 [0.055, 0.045, 0.035, 0.028, 0.022, 0.016, 0.0], 8), "Trim")
    # the torso: broad shoulders, a bare chest under an open indigo vest
    SX, SY = 1.18, 0.78
    prof = [(0.0, 0.95), (0.22, 0.97), (0.24, 1.08), (0.27, 1.3), (0.31, 1.5), (0.33, 1.62), (0.24, 1.72), (0.0, 1.76)]
    def r_at(z):
        for (r0, z0), (r1, z1) in zip(prof, prof[1:]):
            if z0 <= z <= z1 and z1 > z0: return r0 + (r1 - r0) * (z - z0) / (z1 - z0)
        return 0.0
    def gap(z):   # the vest's opening, narrow at the waist and wide over the chest
        return 0.05 + 0.13 * max(0.0, min(1.0, (z - 1.05) / 0.6))
    def front(xh, z):
        r = r_at(z); s = max(-1.0, min(1.0, xh / (r * SX))) if r > 0 else 0.0
        return Vector((xh, y0 + r * SY * math.cos(math.asin(s)), G + z))
    bmT = lathe([(r, G + z) for (r, z) in prof], 28, "z", (0, y0, 0))
    for v in bmT.verts: v.co.x *= SX; v.co.y = y0 + (v.co.y - y0) * SY
    P.obj("Torso", bmT, skin, 1)
    # the vest: a shell over the back, the sides and the shoulders, open down the front
    bmV = bmesh.new(); rows = []; zs = [0.98 + 0.04 * i for i in range(18)]
    for z in zs:
        r = r_at(z) + 0.018; g = gap(z) + 0.004
        a0 = math.asin(min(0.98, g / (r * SX))); row = []
        for k in range(25):
            a = a0 + (2 * math.pi - 2 * a0) * k / 24
            row.append(bmV.verts.new((r * SX * math.sin(a), y0 + r * SY * math.cos(a), G + z)))
        rows.append(row)
    for r0, r1 in zip(rows, rows[1:]):
        for k in range(24): bmV.faces.new((r0[k], r0[k + 1], r1[k + 1], r1[k]))
    bmesh.ops.recalc_face_normals(bmV, faces=bmV.faces)
    for f in bmV.faces:
        f.normal_update(); c = f.calc_center_median()
        if Vector((c.x, c.y - y0, 0)).dot(f.normal) < 0: f.normal_flip()
    P.obj("Vest", bmV, "Accent", 0)
    for s in (1, -1):   # the embroidered gold edge of the opening, and the chest under it
        edge = [front(s * (gap(z) + 0.004), z) + Vector((0, 0.02, 0)) for z in [0.98 + 0.04 * i for i in range(18)]]
        P.obj("VestEdge", pipe(edge, [0.022] * len(edge), 6), "Trim")
        P.obj("Pec", ball(tuple(front(s * 0.09, 1.48) + Vector((0, -0.04, 0))), (0.11, 0.06, 0.085), 12, 6), skin, 0)
    for k in range(3):   # the belly under the chest
        P.obj("Abs", ball(tuple(front(0, 1.18 + 0.08 * k) + Vector((0, -0.03, 0))), (0.07, 0.035, 0.04), 8, 4), skin)
    # the gold chain and medallion on his chest
    chain = [front(0.17 * math.sin(a), 1.66 - 0.2 * math.cos(a) ** 0.5 + 0.0) + Vector((0, 0.03, 0)) for a in [-1.3 + 2.6 * i / 12 for i in range(13)]]
    P.obj("Chain", pipe(chain, [0.012] * len(chain), 5), "Trim")
    P.obj("Medallion", xf(lathe([(0.0, 0.0), (0.05, 0.0), (0.05, 0.015), (0.0, 0.02)], 12, "y"), None, tuple(front(0, 1.44) + Vector((0, 0.02, 0)))), "Trim")
    # the sash: a wide crimson wrap, knotted at his left hip, two tails hanging; a khanjar tucked in front
    for k, dz in enumerate((0.0, 0.07)):
        bmS = torus(0.25 - 0.01 * k, 0.065, 0.0, 28, 8)
        for v in bmS.verts: v.co.x *= SX; v.co.y *= SY
        P.obj("Sash", xf(bmS, Matrix.Rotation(math.radians(4 - 8 * k), 3, "Y"), (0, y0, G + 1.0 + dz)), "Base", 0)
    kn = Vector((-0.27, y0 + 0.08, G + 1.02))
    P.obj("SashKnot", ball(tuple(kn), (0.08, 0.07, 0.08), 10, 5), "Base")
    for k in range(2):
        a = kn + Vector((-0.02 * k, 0.02, -0.05))
        P.obj("SashTail", pipe(bez(a, a + Vector((-0.06 - 0.03 * k, 0.04, -0.15)), a + Vector((-0.1 - 0.05 * k, 0.0, -0.3)), a + Vector((-0.08 - 0.08 * k, -0.04, -0.48)), 6),
                               [0.05, 0.055, 0.06, 0.06, 0.055, 0.05, 0.0], 6), "Base")
    kc = front(0.08, 1.04) + Vector((0, 0.05, 0))
    P.obj("Khanjar", pipe(bez(kc + Vector((0, 0, 0.12)), kc, kc + Vector((0.02, 0.02, -0.14)), kc + Vector((0.1, 0.05, -0.2)), 6), [0.035, 0.04, 0.038, 0.032, 0.026, 0.018, 0.0], 8), "Trim")
    P.obj("KhanjarHilt", pipe([kc + Vector((0, 0, 0.12)), kc + Vector((0, 0.01, 0.24))], [0.025, 0.03], 8), "Metal")
    P.obj("KhanjarPommel", ball(tuple(kc + Vector((0, 0.01, 0.27))), (0.05, 0.03, 0.03), 8, 4), "Metal")
    P.obj("Neck", pipe([(0, y0, G + 1.7), (0, y0 + 0.02, G + 1.84)], [0.085, 0.08], 12), skin)
    # ---- the head
    HC = Vector((0, y0 + 0.03, G + 2.0))
    P.obj("Head", ball(tuple(HC), (0.19, 0.18, 0.21), 18, 9), skin, 1)
    P.obj("BrowRidge", pipe([HC + Vector((-0.13, 0.15, 0.06)), HC + Vector((0, 0.18, 0.065)), HC + Vector((0.13, 0.15, 0.06))], [0.035, 0.04, 0.035], 8), skin)
    for s in (1, -1):
        e = HC + Vector((s * 0.07, 0.155, 0.02))
        P.obj("Socket", ball(tuple(e), (0.05, 0.03, 0.035), 10, 5), "Dark")
        P.obj("EyeWhite", ball(tuple(e + Vector((0, 0.012, -0.002))), (0.036, 0.02, 0.02), 10, 5), "Metal")
        P.obj("Pupil", ball(tuple(e + Vector((-s * 0.006, 0.026, -0.002))), (0.014, 0.008, 0.016), 8, 4), "Dark")
        P.obj("Brow", pipe([HC + Vector((s * 0.025, 0.19, 0.055)), HC + Vector((s * 0.08, 0.185, 0.075)), HC + Vector((s * 0.14, 0.15, 0.1))],
                           [0.025, 0.028, 0.016], 6), "Dark")
        P.obj("Ear", ball(tuple(HC + Vector((s * 0.185, 0.0, 0.0))), (0.03, 0.045, 0.06), 8, 4), skin)
    P.obj("Earring", xf(torus(0.035, 0.009, 0.0, 12, 5), Matrix.Rotation(math.radians(90), 3, "Y"), tuple(HC + Vector((0.195, 0.01, -0.08)))), "Trim")
    # the scar: slashed across his left eye and down the cheek
    P.obj("Scar", pipe([HC + Vector((-0.04, 0.19, 0.12)), HC + Vector((-0.08, 0.183, 0.03)), HC + Vector((-0.12, 0.16, -0.06))], [0.008, 0.011, 0.007], 5), "Base")
    # the hooked nose
    nb = HC + Vector((0, 0.185, 0.035))
    P.obj("Nose", pipe(bez(nb, nb + Vector((0, 0.05, -0.02)), nb + Vector((0, 0.09, -0.07)), nb + Vector((0, 0.06, -0.11)), 5), [0.026, 0.034, 0.04, 0.038, 0.03, 0.0], 8), skin)
    for s in (1, -1): P.obj("Nostril", ball(tuple(nb + Vector((s * 0.03, 0.06, -0.1))), (0.022, 0.02, 0.016), 6, 3), skin)
    # the snarling mouth: dark, the teeth bared top and bottom
    mc = HC + Vector((0, 0.19, -0.125))
    P.obj("Mouth", ball(tuple(mc), (0.07, 0.022, 0.034), 10, 5), "Dark")
    for k in range(6):
        x = -0.05 + 0.02 * k
        P.obj("Tooth", box(tuple(mc + Vector((x, 0.018, 0.018))), (0.016, 0.01, 0.02)), "Metal", 0, False)
        P.obj("Tooth", box(tuple(mc + Vector((x, 0.016, -0.019))), (0.016, 0.01, 0.018)), "Metal", 0, False)
    # the moustache curling up at the ends, the full beard falling to a point
    for s in (1, -1):
        m0 = HC + Vector((s * 0.01, 0.215, -0.08))
        P.obj("Moustache", pipe(bez(m0, m0 + Vector((s * 0.06, 0.0, -0.03)), m0 + Vector((s * 0.13, -0.03, -0.04)), m0 + Vector((s * 0.15, -0.04, 0.04)), 6),
                                [0.022, 0.03, 0.03, 0.026, 0.02, 0.012, 0.0], 7), "Dark")
        P.obj("Sideburn", ball(tuple(HC + Vector((s * 0.16, 0.06, -0.05))), (0.04, 0.05, 0.1), 10, 5), "Dark")
        P.obj("BeardSide", ball(tuple(HC + Vector((s * 0.1, 0.13, -0.17))), (0.065, 0.06, 0.075), 10, 5), "Dark")
    bc = HC + Vector((0, 0.15, -0.2))
    P.obj("Beard", pipe(bez(bc, bc + Vector((0, 0.04, -0.1)), bc + Vector((0, 0.06, -0.2)), bc + Vector((0, 0.04, -0.32)), 6),
                        [0.12, 0.12, 0.105, 0.085, 0.06, 0.035, 0.0], 12), "Dark")
    # the turban: a crimson dome under crossing wraps, a gold-striped wrap, an emerald brooch and an ivory plume, a tail behind
    tc = HC + Vector((0, -0.01, 0.1))
    P.obj("TurbanDome", lathe([(0.0, 0.0), (0.2, 0.02), (0.23, 0.12), (0.2, 0.24), (0.11, 0.31), (0.0, 0.33)], 20, "z", tuple(tc)), "Base", 1)
    for k in range(4):
        tilt = Matrix.Rotation(math.radians(14 if k % 2 == 0 else -14), 3, "Y") @ Matrix.Rotation(math.radians(6 if k < 2 else -6), 3, "X")
        P.obj("TurbanWrap", xf(torus(0.215 - 0.02 * k, 0.045, 0.0, 28, 7), tilt, tuple(tc + Vector((0, 0, 0.05 + 0.065 * k)))), "Base" if k != 1 else "Trim")
    J = HC + Vector((0, 0.235, 0.22))
    P.obj("BroochSet", ball(tuple(J), (0.075, 0.03, 0.085), 12, 6), "Trim")
    P.obj("Brooch", ball(tuple(J + Vector((0, 0.026, 0))), (0.048, 0.02, 0.058), 10, 5), "Glass")
    for k in range(8):
        a = 2 * math.pi * k / 8
        P.obj("BroochPearl", ball(tuple(J + Vector((math.sin(a) * 0.07, 0.02, math.cos(a) * 0.08))), (0.014, 0.014, 0.014), 6, 3), "Metal")
    # the plume: a real feather - the shaft and a vane either side of it, curling back
    shaft = bez(J + Vector((0, -0.02, 0.06)), J + Vector((0.01, -0.04, 0.22)), J + Vector((0.06, -0.12, 0.38)), J + Vector((0.16, -0.3, 0.44)), 8)
    P.obj("PlumeShaft", pipe(shaft, [0.012] * 8 + [0.0], 5), "Trim")
    vane = []
    for i in range(1, 8):
        a, b = shaft[i], shaft[i + 1]; t = (b - a).normalized(); side = t.cross(Vector((0, 0, 1))).normalized() if abs(t.z) < 0.95 else Vector((1, 0, 0))
        w = 0.07 * math.sin(math.pi * i / 8.5)
        vane.append([tuple(a + side * w), tuple(a - side * w), tuple(b - side * w * 0.9), tuple(b + side * w * 0.9)])
    P.obj("Plume", sheet(vane, 0.01), "Metal", 0, False)
    tail = tc + Vector((0.08, -0.2, 0.12))
    P.obj("TurbanTail", pipe(bez(tail, tail + Vector((0.04, -0.08, -0.1)), tail + Vector((0.06, -0.12, -0.3)), tail + Vector((0.04, -0.14, -0.45)), 6), [0.05, 0.06, 0.06, 0.055, 0.05, 0.04, 0.0], 7), "Base")
    # ---- the arms: muscular, leather bracers studded with gold; the right raises the shamshir, the left points at the player
    def arm(sh, el, wr, name, hub=None):
        put = (lambda n, bm, p: P.part(name, bm, p, hub)) if hub is not None else (lambda n, bm, p: P.obj(n, bm, p))
        put("Shoulder", ball(tuple(sh), (0.12, 0.11, 0.11), 12, 6), "Accent")
        bi = sh + (el - sh) * 0.5 + Vector((0, 0.02, 0))
        put("Arm", pipe([sh + (el - sh) * 0.12, bi, el], [0.09, 0.105, 0.08], 12, cap=False), skin)          # the upper arm and the forearm apart:
        put("Arm", pipe([el, el + (wr - el) * 0.3, wr], [0.08, 0.085, 0.065], 12), skin)                          # the tube's frame cannot twist at the elbow
        put("Elbow", ball(tuple(el), (0.082, 0.082, 0.082), 10, 5), skin)
        b0, b1 = el + (wr - el) * 0.35, el + (wr - el) * 0.92
        put("Bracer", pipe([b0, b1], [0.09, 0.078], 12), "Dark")
        for t in (0.0, 1.0): put("BracerRim", pipe([b0 + (b1 - b0) * (t * 0.94), b0 + (b1 - b0) * (t * 0.94 + 0.06)], [0.095 - 0.012 * t, 0.093 - 0.012 * t], 12), "Trim")
        ax = (b1 - b0).normalized(); a, b = frame(ax)
        for i in range(3):
            for k in range(4):
                q = 2 * math.pi * k / 4
                put("Stud", ball(tuple(b0 + (b1 - b0) * (0.25 + 0.25 * i) + (a * math.cos(q) + b * math.sin(q)) * 0.088), (0.014, 0.014, 0.014), 6, 3), "Trim")
        return put
    shR = Vector((0.36, y0, G + 1.62)); elR = Vector((0.6, y0 + 0.06, G + 1.92)); wrR = Vector((0.58, y0 + 0.12, G + 2.26))
    put = arm(shR, elR, wrR, "SwayArm", tuple(shR))
    put("Fist", ball(tuple(wrR + Vector((0, 0.01, 0.06))), (0.075, 0.08, 0.08), 10, 5), skin)
    # the shamshir: a wrapped grip, straight quillons with ball ends, langets, the bent pistol pommel, and the deeply curved blade
    g0 = wrR + Vector((0, 0.03, -0.06)); g1 = wrR + Vector((0, 0.03, 0.17))
    put("Grip", pipe([g0, g1], [0.028, 0.028], 8), "Dark")
    for k in range(4): put("GripWire", xf(torus(0.03, 0.006, 0.0, 10, 4), None, tuple(g0 + (g1 - g0) * (0.15 + 0.23 * k))), "Trim")
    pm = g0 + Vector((-0.045, 0, -0.03))
    put("Pommel", ball(tuple(pm), (0.05, 0.035, 0.035), 8, 4), "Trim")
    gd = g1 + Vector((0, 0, 0.02))
    put("Quillons", pipe([gd + Vector((-0.15, 0, 0)), gd, gd + Vector((0.15, 0, 0))], [0.02, 0.026, 0.02], 8), "Trim")
    for s in (1, -1): put("QuillonBall", ball(tuple(gd + Vector((s * 0.165, 0, 0))), (0.03, 0.03, 0.03), 8, 4), "Trim")
    put("Langet", hull([tuple(gd + Vector((-0.02, -0.02, 0.0))), tuple(gd + Vector((0.02, -0.02, 0.0))), tuple(gd + Vector((-0.02, 0.02, 0.0))), tuple(gd + Vector((0.02, 0.02, 0.0))),
                        tuple(gd + Vector((0, 0.025, 0.1))), tuple(gd + Vector((0, -0.025, 0.1)))]), "Trim")
    blade = bez(gd + Vector((0, 0, 0.02)), gd + Vector((-0.03, 0, 0.45)), gd + Vector((-0.18, 0, 0.85)), gd + Vector((-0.55, 0, 1.08)), 12)
    put("Blade", cp_blade(blade), "Metal")
    shL = Vector((-0.36, y0, G + 1.62)); elL = Vector((-0.52, y0 + 0.32, G + 1.5)); wrL = Vector((-0.52, y0 + 0.66, G + 1.56))
    arm(shL, elL, wrL, "ArmL")
    hdL = wrL + Vector((0, 0.06, 0))
    P.obj("Hand", ball(tuple(hdL), (0.065, 0.075, 0.055), 10, 5), skin)
    P.obj("Finger", pipe([hdL + Vector((0.02, 0.05, 0.01)), hdL + Vector((0.02, 0.2, 0.03))], [0.022, 0.017], 6), skin)   # the pointing finger
    for k in range(3):
        f = hdL + Vector((-0.02 + 0.02 * k, 0.06, -0.025))
        P.obj("Finger", pipe(bez(f, f + Vector((0, 0.04, 0)), f + Vector((0, 0.05, -0.03)), f + Vector((0, 0.02, -0.04)), 3), [0.02, 0.019, 0.017, 0.0], 5), skin)
    P.obj("Thumb", pipe([hdL + Vector((0.05, 0.02, 0.02)), hdL + Vector((0.06, 0.09, 0.05))], [0.02, 0.015], 5), skin)
    # ---------------------------------------------------------------- the brass lamp, the smoke and the genie
    lc = Vector((-0.85, 1.0, cp_z(-0.85, 1.0) + CP_T * 0.5))
    P.obj("LampFoot", xf(lathe([(0.0, 0.0), (0.1, 0.0), (0.1, 0.03), (0.06, 0.06), (0.0, 0.06)], 16, "z"), None, tuple(lc)), "Trim")
    bmL = lathe([(0.0, 0.0), (0.12, 0.02), (0.2, 0.08), (0.21, 0.13), (0.16, 0.19), (0.08, 0.22), (0.0, 0.23)], 18, "z")
    for v in bmL.verts: v.co.y *= 1.6
    P.obj("LampBody", xf(bmL, None, tuple(lc + Vector((0, 0, 0.05)))), "Trim", 1)
    P.obj("LampLid", xf(lathe([(0.0, 0.0), (0.08, 0.0), (0.07, 0.04), (0.03, 0.07), (0.0, 0.08)], 14, "z"), None, tuple(lc + Vector((0, -0.04, 0.27)))), "Trim")
    P.obj("LampFinial", ball(tuple(lc + Vector((0, -0.04, 0.37))), (0.025, 0.025, 0.035), 8, 4), "Trim")
    hb = lc + Vector((0, -0.3, 0.17))
    P.obj("LampHandle", pipe(bez(lc + Vector((0, -0.26, 0.24)), hb + Vector((0, -0.14, 0.12)), hb + Vector((0, -0.16, -0.08)), lc + Vector((0, -0.28, 0.1)), 8), [0.02] * 9, 6), "Trim")
    sp = [lc + Vector((0, 0.28, 0.15)), lc + Vector((0, 0.42, 0.18)), lc + Vector((0, 0.55, 0.25)), lc + Vector((0, 0.63, 0.33))]
    P.obj("LampSpout", pipe(sp, [0.07, 0.05, 0.035, 0.03], 10), "Trim")
    T = sp[-1] + Vector((0, 0.02, 0.03))
    P.obj("Wick", cone(T + Vector((0, 0, -0.01)), T + Vector((0, 0.02, 0.09)), 0.025, 8), "Lamp")
    # the smoke rises from the spout and climbs, three ropes of it winding round each other (they turn)
    gx, gy = -0.95, 1.18
    ax0 = Vector((gx, gy, T.z + 0.15)); ax1 = Vector((gx, gy, G + 1.25))
    P.obj("SmokeStem", pipe(bez(T + Vector((0, 0.02, 0.08)), T + Vector((0, 0.05, 0.3)), ax0 + Vector((0, 0, 0.3)), ax1 + Vector((0, 0, 0.1)), 10),
                            [0.03, 0.045, 0.06, 0.07, 0.08, 0.09, 0.1, 0.11, 0.12, 0.13, 0.14], 10), "Glow")
    hub = ((ax0 + ax1) * 0.5)
    for r in range(3):
        pts, rad = [], []
        for i in range(19):
            t = i / 18; a = 2 * math.pi * (1.4 * t) + 2 * math.pi * r / 3
            R = 0.1 + 0.12 * t
            pts.append(ax0 + (ax1 - ax0) * t + Vector((math.cos(a) * R, math.sin(a) * R, 0)))
            rad.append(0.035 + 0.04 * t + 0.015 * math.sin(7 * t + r))
        P.part("SpinSmoke", pipe(pts, rad, 8), "Glow", tuple(hub))
        for i in (5, 11, 17):
            P.part("SpinSmoke", ball(tuple(pts[i]), (rad[i] * 1.6,) * 3, 8, 4), "Glow", tuple(hub))
    # the genie: a broad torso out of the smoke, the head, the arms cupped round his fireball
    gw = Vector((gx, gy, G + 1.25))
    bmG = lathe([(0.12, 0.0), (0.16, 0.12), (0.22, 0.3), (0.25, 0.44), (0.18, 0.54), (0.07, 0.6), (0.0, 0.61)], 20, "z")
    for v in bmG.verts: v.co.x *= 1.25; v.co.y *= 0.8
    P.obj("GenieTorso", xf(bmG, None, tuple(gw)), "Glow", 1)
    for s in (1, -1): P.obj("GeniePec", ball(tuple(gw + Vector((s * 0.1, 0.13, 0.36))), (0.1, 0.06, 0.08), 10, 5), "Glow")
    gh = gw + Vector((0, 0.02, 0.76))
    P.obj("GenieHead", ball(tuple(gh), (0.15, 0.15, 0.17), 16, 8), "Glow", 1)
    P.obj("GenieJaw", ball(tuple(gh + Vector((0, 0.06, -0.09))), (0.11, 0.1, 0.07), 10, 5), "Glow")
    for s in (1, -1):
        P.obj("GenieEar", cone(gh + Vector((s * 0.13, -0.01, 0.0)), gh + Vector((s * 0.27, -0.06, 0.1)), 0.04, 6), "Glow")
        P.obj("GenieHoop", xf(torus(0.03, 0.008, 0.0, 10, 4), Matrix.Rotation(math.radians(90), 3, "Y"), tuple(gh + Vector((s * 0.15, 0.0, -0.06)))), "Trim")
        e = gh + Vector((s * 0.055, 0.135, 0.03))
        P.obj("GenieEye", ball(tuple(e), (0.035, 0.014, 0.016), 8, 4), "Lamp")
        P.obj("GenieBrow", pipe([gh + Vector((s * 0.015, 0.15, 0.06)), gh + Vector((s * 0.07, 0.145, 0.07)), gh + Vector((s * 0.13, 0.11, 0.11))], [0.022, 0.024, 0.012], 6), "Dark")
    P.obj("GenieNose", cone(gh + Vector((0, 0.14, 0.0)), gh + Vector((0, 0.2, -0.04)), 0.03, 6), "Glow")
    P.obj("GenieMouth", ball(tuple(gh + Vector((0, 0.15, -0.075))), (0.06, 0.02, 0.022), 10, 5), "Dark")
    for k in range(4): P.obj("GenieFang", cone(gh + Vector((-0.03 + 0.02 * k, 0.165, -0.06)), gh + Vector((-0.03 + 0.02 * k, 0.168, -0.085)), 0.008, 4), "Metal")
    P.obj("GenieGoatee", cone(gh + Vector((0, 0.13, -0.13)), gh + Vector((0, 0.16, -0.27)), 0.04, 8), "Accent")
    P.obj("GenieTopknot", pipe(bez(gh + Vector((0, -0.04, 0.16)), gh + Vector((0, -0.08, 0.26)), gh + Vector((0, -0.2, 0.24)), gh + Vector((0, -0.28, 0.1)), 6),
                               [0.04, 0.045, 0.04, 0.035, 0.03, 0.02, 0.0], 7), "Accent")
    P.obj("GenieKnotRing", xf(torus(0.045, 0.012, 0.0, 12, 5), Matrix.Rotation(math.radians(-30), 3, "X"), tuple(gh + Vector((0, -0.07, 0.22)))), "Trim")
    orb = gw + Vector((0, 0.42, 0.42))
    for s in (1, -1):
        sh = gw + Vector((s * 0.27, 0.0, 0.48)); el = gw + Vector((s * 0.3, 0.2, 0.3)); wr = orb + Vector((s * 0.12, -0.04, -0.02))
        P.obj("GenieArm", pipe([sh, (sh + el) * 0.5 + Vector((s * 0.03, 0, 0)), el, wr], [0.08, 0.085, 0.065, 0.055], 10), "Glow")
        P.obj("GenieCuff", pipe([wr + (el - wr).normalized() * 0.1, wr + (el - wr).normalized() * 0.03], [0.065, 0.06], 10), "Trim")
        P.obj("GenieHand", ball(tuple(wr + Vector((-s * 0.02, 0.03, 0.0))), (0.05, 0.065, 0.07), 8, 4), "Glow")
    P.part("Muzzle", ball(tuple(orb), (0.1, 0.1, 0.1), 12, 6), "Lamp", tuple(orb))
    # ---------------------------------------------------------------- the chest of treasure behind him
    cc = Vector((0.62, -0.95, 0.0)); cc.z = cp_z(cc.x, cc.y) + CP_T * 0.5
    cw, cd, ch = 0.72, 0.46, 0.36
    P.obj("Chest", box(tuple(cc + Vector((0, 0, ch / 2))), (cw, cd, ch)), "Dark", 0, False)
    for k in range(4):   # the planks' seams
        P.obj("Plank", box(tuple(cc + Vector((0, cd / 2 + 0.004, 0.07 + 0.075 * k))), (cw * 0.98, 0.008, 0.008)), "Base", 0, False)
    for sx in (-1, 1):   # brass bands round it, corner brackets
        P.obj("Band", box(tuple(cc + Vector((sx * cw * 0.3, 0, ch / 2))), (0.05, cd + 0.02, ch + 0.02)), "Trim", 0, False)
        for sy in (-1, 1):
            P.obj("Corner", box(tuple(cc + Vector((sx * (cw / 2 - 0.03), sy * (cd / 2 - 0.03), ch / 2))), (0.08, 0.08, ch + 0.025)), "Trim", 0, False)
    P.obj("LockPlate", box(tuple(cc + Vector((0, cd / 2 + 0.012, ch * 0.72))), (0.1, 0.02, 0.12)), "Trim", 0, False)
    P.obj("Keyhole", box(tuple(cc + Vector((0, cd / 2 + 0.024, ch * 0.7))), (0.02, 0.01, 0.045)), "Dark", 0, False)
    hinge = cc + Vector((0, -cd / 2, ch))
    lid = cp_halfcyl((0, 0, 0), cd / 2, cw, 12)
    for v in lid.verts: v.co.y += cd / 2
    rot = Matrix.Rotation(math.radians(105), 3, "X")
    P.obj("Lid", xf(lid, rot, tuple(hinge)), lambda c, n: "Base" if n.dot(rot @ Vector((0, 0, 1))) < -0.7 else "Dark", 0, False)
    for sx in (-1, 1):
        bnd = torus(cd / 2 + 0.01, 0.018, 0.0, 16, 4)
        bmesh.ops.delete(bnd, geom=[v for v in bnd.verts if v.co.y < -0.01], context="VERTS")
        for v in bnd.verts: v.co = Vector((sx * cw * 0.3, v.co.x, v.co.y)); v.co.y += cd / 2
        P.obj("LidBand", xf(bnd, rot, tuple(hinge)), "Trim", 0, False)
    # the hoard: a heap of gold, coins on it and spilling down the front onto the rug, gems and a string of pearls
    top = cc + Vector((0, 0, ch))
    P.obj("Hoard", ball(tuple(top), (cw * 0.46, cd * 0.44, 0.12), 14, 6), "Trim", 0)
    import random
    rnd = random.Random(7)
    def coin(c, tilt):
        return xf(lathe([(0.0, 0.0), (0.05, 0.0), (0.05, 0.012), (0.0, 0.012)], 12, "z"), Matrix.Rotation(tilt[0], 3, "X") @ Matrix.Rotation(tilt[1], 3, "Y"), tuple(c))
    for k in range(12):
        a = 2 * math.pi * k / 12
        P.obj("Coin", coin(top + Vector((math.cos(a) * 0.2, math.sin(a) * 0.12, 0.08 + 0.02 * (k % 3))), (rnd.uniform(-0.6, 0.6), rnd.uniform(-0.6, 0.6))), "Trim")
    for k in range(9):   # spilt down the front and lying on the rug
        t = k / 8
        p = cc + Vector((-0.2 + 0.4 * rnd.random(), cd / 2 + 0.06 + 0.35 * t, 0)); p.z = cp_z(p.x, p.y) + CP_T * 0.5 + 0.03 + (0.25 * (1 - t) ** 2 if t < 0.4 else 0.0)
        P.obj("Coin", coin(p, (rnd.uniform(-0.3, 0.3), rnd.uniform(-0.3, 0.3))), "Trim")
    for (dx, dy, slot, r) in ((0.12, 0.05, "Glass", 0.06), (-0.14, -0.04, "Base", 0.055), (0.02, -0.1, "Accent", 0.05), (-0.04, 0.1, "Glass", 0.045)):
        P.obj("Gem", xf(hull([(0, 0, r), (r, 0, 0), (0, r, 0), (-r, 0, 0), (0, -r, 0), (0, 0, -r * 0.6)]), None, tuple(top + Vector((dx, dy, 0.12)))), slot, 0, False)
    pearls = bez(top + Vector((-0.28, 0.0, 0.1)), top + Vector((-0.2, 0.25, 0.05)), top + Vector((-0.3, 0.3, -0.15)), top + Vector((-0.34, 0.24, -0.3)), 12)
    for q in pearls: P.obj("Pearl", ball(tuple(q), (0.022, 0.022, 0.022), 6, 3), "Metal")
    return P



# ================================================================= anubis (2026-10-13 remake)
AN_TOP, AN_FOOT, AN_HALF0, AN_HALF1, AN_TIP = 0.0, -1.5, 0.42, 0.27, -1.88   # the obelisk: its base (his floor), where the shaft ends, half-widths, tip
AN_JAR_Z, AN_JAR_R = -0.78, 0.86                                              # the canopic jars' ring


def an_trunk(secs, seg=24, sq=1.25):
    """a body of horizontal superellipse rings: (z, rx, ry, cy)."""
    bm = bmesh.new(); rings = []
    for (z, rx, ry, cy) in secs:
        ring = []
        for k in range(seg):
            a = 2 * math.pi * k / seg; ca, sa = math.cos(a), math.sin(a)
            ring.append(bm.verts.new((math.copysign(abs(ca) ** (1 / sq), ca) * rx, cy + math.copysign(abs(sa) ** (1 / sq), sa) * ry, z)))
        rings.append(ring)
    return skin(bm, rings, seg)

def an_pleated(profile, seg, n, ripple, ky=1.0, c=(0, 0, 0)):
    """a lathe about z whose radius ripples n times round (the pleats of a linen kilt), squashed ky front to back."""
    bm = lathe(profile, seg, "z")
    for v in bm.verts:
        a = math.atan2(v.co.y, v.co.x)
        v.co.x *= 1 + ripple * math.cos(n * a); v.co.y *= (1 + ripple * math.cos(n * a)) * ky
        v.co += Vector(c)
    return bm

def an_half(z):
    """the obelisk's half-width at height z (the shaft tapers down toward the tip)."""
    return AN_HALF0 + (AN_HALF1 - AN_HALF0) * (AN_TOP - z) / (AN_TOP - AN_FOOT)

def an_glyph(kind, d=0.022):
    """one carved hieroglyph about 0.14 tall, in a local frame: x across the face, y out of it (0..d), z up."""
    out = []
    if kind == "eye":        # the wedjat eye: brow, almond, pupil, the falcon's tear mark and curl below
        out += [box((0, d / 2, 0.048), (0.12, d, 0.014)), ball((0, d / 2, 0.005), (0.058, d / 2, 0.024), 12, 4),
                box((-0.018, d / 2, -0.04), (0.014, d, 0.05)), box((0.03, d / 2, -0.045), (0.05, d, 0.012), Matrix.Rotation(0.5, 3, "Y"))]
    elif kind == "ankh":
        t = torus(0.026, 0.009, 0.0, 14, 4); xf(t, Matrix.Rotation(math.pi / 2, 3, "X") @ Matrix.Diagonal((1.0, 1.0, 1.35)), (0, d / 2, 0.042)); out.append(t)
        out += [box((0, d / 2, 0.006), (0.08, d, 0.014)), box((0, d / 2, -0.04), (0.017, d, 0.075))]
    elif kind == "feather":  # the feather of Maat, curling over at the top
        out.append(hull([(x, y, z) for (x, z) in ((-0.018, -0.07), (0.014, -0.07), (0.03, 0.0), (0.024, 0.05), (-0.01, 0.075), (-0.03, 0.045), (-0.02, -0.02)) for y in (0, d)]))
    elif kind == "bird":     # a falcon standing, in profile
        out += [ball((0, d / 2, 0.0), (0.045, d / 2, 0.028), 10, 4), ball((0.04, d / 2, 0.035), (0.02, d / 2, 0.019), 8, 3),
                hull([(x, y, z) for (x, z) in ((0.055, 0.04), (0.072, 0.03), (0.056, 0.024)) for y in (0, d)]),
                hull([(x, y, z) for (x, z) in ((-0.03, 0.0), (-0.075, -0.035), (-0.06, -0.045), (-0.02, -0.02)) for y in (0, d)]),
                box((0.01, d / 2, -0.05), (0.008, d, 0.045)), box((-0.012, d / 2, -0.05), (0.008, d, 0.045))]
    elif kind == "water":    # three zigzags of water
        for r in range(3):
            for k in range(4):
                out.append(box((-0.045 + k * 0.03, d / 2, 0.04 - r * 0.04), (0.036, d, 0.011), Matrix.Rotation(0.6 if k % 2 else -0.6, 3, "Y")))
    else:                    # the sun disc with the dot in its middle
        t = torus(0.04, 0.01, 0.0, 16, 4); xf(t, Matrix.Rotation(math.pi / 2, 3, "X"), (0, d / 2, 0.0)); out.append(t)
        out.append(ball((0, d / 2, 0.0), (0.013, d / 2, 0.013), 8, 3))
    bm = bmesh.new()
    for b in out:
        me = bpy.data.meshes.new("g"); b.to_mesh(me); b.free(); bm.from_mesh(me); bpy.data.meshes.remove(me)
    return bm

def an_on_face(bm, n, u, z, sink=0.006):
    """lay a local-frame piece on the obelisk face whose outward normal is n, u across it (to the viewer's right), at height z."""
    n = Vector(n); s = Vector((0, 0, 1)).cross(n)
    up = (n * (AN_HALF0 - AN_HALF1) + Vector((0, 0, AN_TOP - AN_FOOT))).normalized()   # up the face, which leans in toward the tip
    out = s.cross(up).normalized()
    m = Matrix((s, out, up)).transposed()
    return xf(bm, m, tuple(n * an_half(z) - out * sink + s * u + Vector((0, 0, z))))

def an_jar(kind):
    """a canopic jar about 0.62 tall standing at the origin, its head looking along +y: the four sons of Horus."""
    parts = []
    body = lathe([(0.0, 0.0), (0.085, 0.0), (0.095, 0.03), (0.11, 0.08), (0.15, 0.24), (0.158, 0.31), (0.14, 0.37), (0.105, 0.41), (0.0, 0.41)], 20, "z")
    parts.append((body, "Belly"))
    parts.append((torus(0.152, 0.012, 0.31, 20, 4), "Trim"))
    parts.append((torus(0.098, 0.01, 0.03, 18, 4), "Trim"))
    for k in range(3):   # a column of inscription down its front
        parts.append((box((0, 0.13 + 0.006 * k, 0.24 - 0.06 * k), (0.03, 0.012, 0.035)), "Accent"))
    parts.append((lathe([(0.0, 0.40), (0.11, 0.40), (0.11, 0.43), (0.0, 0.44)], 18, "z"), "Trim"))   # the lid's rim
    hc = Vector((0, 0.0, 0.53))
    if kind == "human":      # Imsety: a gilded man's face under a striped wig, a plaited beard
        parts.append((ball(tuple(hc + Vector((0, -0.02, 0.01))), (0.1, 0.095, 0.11), 14, 7), "Accent"))
        parts.append((ball(tuple(hc + Vector((0, 0.03, -0.005))), (0.07, 0.065, 0.085), 12, 6), "Trim"))
        for s in (1, -1):
            parts.append((box((s * 0.075, 0.03, 0.47), (0.04, 0.03, 0.11)), "Accent"))
            parts.append((ball((s * 0.03, 0.095, 0.55), (0.014, 0.006, 0.008), 6, 3), "Dark"))
        parts.append((box((0, 0.07, 0.43), (0.025, 0.02, 0.06)), "Accent"))
    elif kind == "baboon":   # Hapy: the baboon, a heavy muzzle under a ruff of mane
        parts.append((ball(tuple(hc), (0.09, 0.085, 0.09), 14, 7), "Trim"))
        parts.append((ball(tuple(hc + Vector((0, 0.08, -0.03))), (0.05, 0.06, 0.04), 10, 5), "Trim"))
        parts.append((ball(tuple(hc + Vector((0, 0.135, -0.025))), (0.03, 0.012, 0.02), 8, 3), "Dark"))
        parts.append((torus(0.1, 0.03, 0.0, 18, 5), "Accent")); xf(parts[-1][0], Matrix.Diagonal((1.0, 0.85, 1.0)), tuple(hc + Vector((0, -0.01, -0.04))))
        for s in (1, -1): parts.append((ball((s * 0.035, 0.075, 0.555), (0.016, 0.008, 0.01), 6, 3), "Dark"))
    elif kind == "jackal":   # Duamutef: a little Anubis
        parts.append((ball(tuple(hc), (0.075, 0.08, 0.075), 12, 6), "Base"))
        parts.append((pipe([hc + Vector((0, 0.05, -0.01)), hc + Vector((0, 0.17, -0.03))], [0.045, 0.018], 8), "Base"))
        for s in (1, -1):
            parts.append((hull([(s * 0.03, -0.01, 0.58), (s * 0.075, -0.02, 0.57), (s * 0.06, -0.02, 0.7), (s * 0.05, 0.0, 0.6)]), "Base"))
            parts.append((ball((s * 0.035, 0.065, 0.55), (0.016, 0.006, 0.008), 6, 3), "Trim"))
    else:                    # Qebehsenuef: the falcon, a hooked beak, the dark falcon's tear under each eye
        parts.append((ball(tuple(hc + Vector((0, -0.02, 0.01))), (0.1, 0.095, 0.11), 14, 7), "Accent"))
        parts.append((ball(tuple(hc + Vector((0, 0.02, 0.0))), (0.075, 0.075, 0.08), 12, 6), "Trim"))
        parts.append((pipe(bez(hc + Vector((0, 0.07, 0.01)), hc + Vector((0, 0.12, 0.01)), hc + Vector((0, 0.13, -0.02)), hc + Vector((0, 0.11, -0.05)), 4), [0.025, 0.02, 0.014, 0.008, 0.0], 6), "Dark"))
        for s in (1, -1):
            parts.append((ball((s * 0.035, 0.08, 0.545), (0.016, 0.006, 0.012), 6, 3), "Dark"))
            parts.append((box((s * 0.035, 0.078, 0.51), (0.008, 0.008, 0.04)), "Dark"))
    return parts


def D_anubis():
    """The ANUBIS GUARDIAN (2026-10-13, remade: "same as the alien bosses - realistic details, scarier, keep the cartoon shape"): the same
    black jackal-headed god with the was-sceptre and the ankh, now built like Anubis in real Egyptian art - and angry. A long narrow
    jackal's snout under a sloping brow, the jaws open on bared white fangs, a black nose; tall pointed ears standing up, lined inside
    with gold; almond eyes glowing amber, rimmed in gold with the long painted line of kohl running back from each, under a brow ridge
    drawn down in a scowl. Behind his head the striped tripartite wig, its two lappets falling over his shoulders in bands of gold and
    lapis. A god's body, black and muscular - a broad chest with the pectorals and the ridges of the belly, heavy shoulders, strong arms
    and legs - in the striding pose of every Egyptian statue, the left foot forward. On his shoulders the broad usekh collar of real
    bead rows, gold, lapis, gold, carnelian, gold, lapis, gold out to the edge, with a fringe of drop beads hanging evenly round it; gold
    armbands set with lapis, gold-and-lapis wristbands, gold anklets; a pleated white linen shendyt kilt with a gold belt, a knot plate
    at the front and the striped apron hanging from it; gold sandals with toe straps. In his right fist the was-sceptre, its foot forked
    and its head the slanted head of the Set animal; in his left, held up at the player, a gold ankh.
    He flies STANDING ON A FLOATING OBELISK: a granite obelisk hangs point-down in the air, its flat base the floor under his feet
    (a gold border inlaid round it), its four faces carved with two columns of hieroglyphs each - the wedjat eye, the ankh, the
    feather of Maat, the falcon, water, the sun disc - between incised lines, glowing gold; its pyramidion at the bottom is capped in
    gold, and from the point a thin stream of sand pours and scatters below. Round it the four canopic jars of the sons of Horus, white
    alabaster banded in gold and inscribed down the front - Imsety with a man's gilded face, Hapy the baboon, Duamutef the jackal,
    Qebehsenuef the falcon - slowly circle the obelisk (SpinJars). His shots leave from his open jaws."""
    P = Boss("anubis", {"Base": ((0.06, 0.055, 0.07), 0.55), "Belly": ((0.95, 0.92, 0.84), 0.3), "Accent": LAPIS, "Trim": GOLD,
                        "Glass": ((0.72, 0.16, 0.10), 0.7), "Dark": ((0.02, 0.02, 0.025), 0.45), "Glow": ((1.0, 0.78, 0.30), 0.5),
                        "Metal": ((0.50, 0.36, 0.33), 0.35), "Lamp": ((1.0, 0.62, 0.12), 0.8)})
    # ---- the body: chest, belly, pelvis
    P.obj("Torso", an_trunk([(0.86, 0.17, 0.13, 0.0), (1.0, 0.2, 0.145, 0.0), (1.12, 0.21, 0.15, 0.005), (1.26, 0.245, 0.165, 0.015),
                             (1.4, 0.31, 0.185, 0.02), (1.52, 0.35, 0.18, 0.01), (1.6, 0.25, 0.15, 0.0), (1.68, 0.12, 0.11, 0.0)]), "Base")
    for s in (1, -1):
        P.obj("Pec", oriented_ball((s * 0.12, 0.155, 1.43), (0.125, 0.06, 0.085), Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1)), 12, 6), "Base")
        for k in range(3):
            P.obj("Abs", ball((s * 0.055, 0.14, 1.08 + 0.09 * k), (0.048, 0.022, 0.038), 8, 4), "Base")
        P.obj("Delt", ball((s * 0.37, 0.0, 1.5), (0.13, 0.13, 0.12), 12, 6), "Base")
    P.obj("Neck", pipe([(0, -0.01, 1.6), (0, 0.0, 1.78), (0, 0.02, 1.86)], [0.105, 0.095, 0.1], 12), "Base")
    # ---- the usekh collar: bead rows from the neck out, and a fringe of drop beads
    BANDS = [(0.16, "Trim"), (0.19, "Accent"), (0.205, "Trim"), (0.235, "Glass"), (0.25, "Trim"), (0.28, "Accent"), (0.295, "Trim"),
             (0.325, "Glass"), (0.34, "Trim"), (0.37, "Accent"), (0.385, "Trim"), (0.415, "Glass"), (0.5, "Trim")]
    def bead_row(c, n):
        r = math.hypot(c.x, c.y / 0.72)
        return next(k for (rr, k) in BANDS if r < rr)
    collar = lathe([(0.11, 1.67)] + [(0.11 + 0.335 * i / 16, 1.67 - 0.135 * (i / 16) ** 1.3) for i in range(1, 17)] + [(0.44, 1.515), (0.3, 1.575), (0.12, 1.645)], 48, "z")
    for v in collar.verts: v.co.y *= 0.72
    P.obj("Collar", collar, bead_row)
    for k in range(25):
        a = math.radians(-150 + 300 * k / 24)
        c = Vector((math.sin(a) * 0.45, math.cos(a) * 0.45 * 0.72, 1.5))
        P.obj("Drop", ball(tuple(c), (0.022, 0.022, 0.036), 8, 4), "Glass" if k % 2 else "Accent")
        P.obj("DropCap", ball(tuple(c + Vector((0, 0, 0.03))), (0.016, 0.016, 0.01), 6, 3), "Trim")
    # ---- the kilt: pleated linen, gold belt with a knot plate, the striped apron
    P.obj("Kilt", an_pleated([(0.2, 1.0), (0.23, 0.92), (0.29, 0.76), (0.33, 0.62), (0.31, 0.6), (0.0, 0.6)], 48, 16, 0.035, 0.74), "Belly")
    belt = torus(0.205, 0.03, 0.0, 28, 6); xf(belt, Matrix.Diagonal((1.0, 0.74, 1.0)), (0, 0, 0.99)); P.obj("Belt", belt, "Trim")
    P.obj("Knot", box((0, 0.155, 0.98), (0.11, 0.03, 0.075)), lambda c, n: "Accent" if abs(c.x) < 0.035 and n.y > 0.5 else "Trim", 0, False)
    P.obj("Apron", hull([(x, y, z) for (x, z) in ((-0.07, 0.94), (0.07, 0.94), (0.1, 0.62), (-0.1, 0.62)) for y in (0.17, 0.205)]),
          lambda c, n: "Trim" if int((0.95 - c.z) / 0.055) % 2 == 0 or abs(c.x) > 0.075 - (0.94 - c.z) * 0.1 else "Accent", 0, False)
    # ---- the legs, striding: left forward, right back; anklets and gold sandals
    for s, fw in ((-1, 1), (1, -1)):
        hip = Vector((s * 0.135, 0.02 * fw, 0.8)); knee = Vector((s * 0.15, 0.1 + 0.08 * fw, 0.46)); calf = Vector((s * 0.152, 0.075 + 0.11 * fw, 0.33))
        ank = Vector((s * 0.15, 0.08 + 0.14 * fw, 0.1))
        P.obj("Leg", pipe([hip, (hip + knee) / 2, knee, calf, ank], [0.11, 0.1, 0.07, 0.085, 0.05], 12), "Base")
        P.obj("Anklet", pipe([ank + Vector((0, 0, 0.02)), ank + Vector((0, 0, 0.06))], [0.058, 0.058], 12), "Trim")
        foot = ank + Vector((0, 0.1, -0.06))
        P.obj("Foot", ball(tuple(foot), (0.055, 0.12, 0.04), 10, 5), "Base")
        P.obj("Sole", box(tuple(foot + Vector((0, 0.005, -0.035))), (0.12, 0.28, 0.022)), "Trim", 0, False)
        P.obj("Strap", pipe([foot + Vector((0, 0.08, 0.03)), ank + Vector((0, 0.02, -0.02))], [0.01, 0.01], 5), "Trim")
    # ---- the arms: the right fist round the was-sceptre, the left holding the ankh up at the player
    for s, el, hd in ((1, Vector((0.5, 0.1, 1.2)), Vector((0.52, 0.36, 1.13))), (-1, Vector((-0.5, 0.2, 1.28)), Vector((-0.44, 0.58, 1.38)))):
        sh = Vector((s * 0.38, 0.0, 1.5))
        P.obj("Arm", pipe([sh, sh + (el - sh) * 0.45, el, el + (hd - el) * 0.35, hd], [0.1, 0.098, 0.068, 0.076, 0.05], 12), "Base")
        a0, a1 = sh + (el - sh) * 0.3, sh + (el - sh) * 0.48
        P.obj("Armband", pipe([a0, a1], [0.107, 0.107], 12), "Trim")
        P.obj("ArmbandInlay", pipe([a0 + (a1 - a0) * 0.35, a0 + (a1 - a0) * 0.65], [0.109, 0.109], 12), "Accent")
        w0, w1 = el + (hd - el) * 0.55, el + (hd - el) * 0.9
        for j in range(3):
            P.obj("Wrist", pipe([w0 + (w1 - w0) * j / 3, w0 + (w1 - w0) * (j + 1) / 3], [0.068, 0.066], 12), "Accent" if j == 1 else "Trim")
        P.obj("Fist", ball(tuple(hd + (hd - el).normalized() * 0.05), (0.07, 0.07, 0.065), 10, 5), "Base")
    # the was-sceptre: forked foot, the Set animal's head on top
    sx, sy = 0.53, 0.42
    P.obj("Was", pipe([(sx, sy, 0.1), (sx, sy, 2.06)], [0.024, 0.024], 8), "Trim")
    for s in (1, -1): P.obj("WasFork", pipe([(sx, sy, 0.14), (sx + s * 0.035, sy, 0.06), (sx + s * 0.045, sy, 0.0)], [0.018, 0.015, 0.01], 6), "Trim")
    P.obj("WasHead", pipe([(sx, sy - 0.01, 2.04), (sx, sy + 0.04, 2.12), (sx, sy + 0.13, 2.13), (sx, sy + 0.2, 2.09)], [0.035, 0.04, 0.026, 0.012], 8), "Trim")
    for s in (1, -1): P.obj("WasEar", cone((sx + s * 0.012, sy + 0.01, 2.13), (sx + s * 0.02, sy - 0.02, 2.22), 0.014, 5), "Trim")
    # the ankh, held by its loop
    ax, ay = -0.43, 0.64
    loop = torus(0.065, 0.017, 0.0, 20, 6); xf(loop, Matrix.Rotation(math.pi / 2, 3, "X") @ Matrix.Diagonal((1.0, 1.0, 1.3)), (ax, ay, 1.47))
    P.obj("Ankh", loop, "Trim")
    P.obj("Ankh", box((ax, ay, 1.33), (0.2, 0.035, 0.04)), "Trim", 0, False)
    P.obj("Ankh", hull([(ax + x, ay + y, z) for (x, z) in ((-0.022, 1.31), (0.022, 1.31), (0.04, 1.03), (-0.04, 1.03)) for y in (-0.018, 0.018)]), "Trim", 0, False)
    # ---- the head: skull, the long jackal snout, the open jaws with fangs
    H = Vector((0, 0.02, 1.92))
    P.obj("Skull", ball(tuple(H), (0.15, 0.17, 0.15), 16, 8), "Base")
    P.obj("Snout", pipe([H + Vector((0, 0.08, -0.02)), H + Vector((0, 0.22, -0.06)), H + Vector((0, 0.36, -0.1)), H + Vector((0, 0.5, -0.12))],
                        [0.1, 0.075, 0.055, 0.035], 12), "Base")
    P.obj("Jaw", pipe([H + Vector((0, 0.06, -0.12)), H + Vector((0, 0.22, -0.2)), H + Vector((0, 0.4, -0.27))], [0.07, 0.045, 0.026], 10), "Base")
    P.obj("Mouth", ball(tuple(H + Vector((0, 0.24, -0.15))), (0.035, 0.15, 0.035), 10, 5), "Glass")
    P.obj("Nose", ball(tuple(H + Vector((0, 0.53, -0.115))), (0.032, 0.03, 0.026), 8, 4), "Dark")
    for s in (1, -1):
        def along(keys, y):   # (y, z-offset, radius) of a jaw at y
            for (y0, z0, r0), (y1, z1, r1) in zip(keys, keys[1:]):
                if y <= y1: f = (y - y0) / (y1 - y0); return z0 + (z1 - z0) * f, r0 + (r1 - r0) * f
            return keys[-1][1], keys[-1][2]
        UP = [(0.08, -0.02, 0.1), (0.22, -0.06, 0.075), (0.36, -0.1, 0.055), (0.5, -0.12, 0.035)]
        LO = [(0.06, -0.12, 0.07), (0.22, -0.2, 0.045), (0.4, -0.27, 0.026)]
        for j, (y, L) in enumerate(((0.17, 0.035), (0.23, 0.04), (0.29, 0.04), (0.35, 0.045), (0.43, 0.07))):
            zc, r = along(UP, y); top = H + Vector((s * r * 0.5, y, zc - r * 0.8))
            P.obj("Fang", cone(top + Vector((0, 0, 0.012)), top - Vector((0, 0, L)), 0.014 if j < 4 else 0.019, 5), "Belly", 0, False)
        for y, L in ((0.18, 0.03), (0.26, 0.035), (0.34, 0.05)):
            zc, r = along(LO, y); bot = H + Vector((s * r * 0.5, y, zc + r * 0.8))
            P.obj("Fang", cone(bot - Vector((0, 0, 0.01)), bot + Vector((0, 0, L)), 0.012, 5), "Belly", 0, False)
        # eyes: amber almonds rimmed in gold, the kohl line running back, a brow drawn down in a scowl
        e = H + Vector((s * 0.078, 0.135, 0.03))
        rot = Matrix.Rotation(math.radians(-s * 18), 3, "Y")
        P.obj("EyeRim", xf(ball((0, 0, 0), (0.048, 0.02, 0.026), 12, 4), rot, tuple(e)), "Trim")
        P.obj("Eye", xf(ball((0, 0, 0), (0.036, 0.02, 0.017), 12, 4), rot, tuple(e + Vector((0, 0.008, 0)))), "Lamp")
        P.obj("Pupil", ball(tuple(e + Vector((0, 0.025, 0))), (0.007, 0.004, 0.014), 6, 3), "Dark")
        P.obj("Kohl", pipe([e + Vector((s * 0.04, -0.005, -0.006)), e + Vector((s * 0.085, -0.05, -0.014))], [0.008, 0.005], 5), "Trim")
        P.obj("Brow", pipe([H + Vector((s * 0.02, 0.17, 0.055)), H + Vector((s * 0.08, 0.15, 0.085)), H + Vector((s * 0.13, 0.1, 0.1))], [0.02, 0.026, 0.016], 8), "Base")
        # the ears: tall, pointed, cupped forward, lined with gold
        P.obj("Ear", hull([(s * 0.04, -0.03, 2.02), (s * 0.15, -0.07, 1.98), (s * 0.15, -0.06, 2.44), (s * 0.05, -0.08, 2.05), (s * 0.15, -0.11, 2.0)]), "Base", 0, False)
        P.obj("EarIn", hull([(s * 0.065, -0.025, 2.05), (s * 0.135, -0.055, 2.03), (s * 0.145, -0.05, 2.36), (s * 0.1, -0.06, 2.1)]), "Trim", 0, False)
    # the striped tripartite wig: a mass behind the head, a lappet falling over each shoulder
    wig = ball(tuple(H + Vector((0, -0.08, -0.08))), (0.18, 0.13, 0.2), 16, 8)
    P.obj("Wig", wig, lambda c, n: "Trim" if int((c.z - 1.5) / 0.045) % 2 else "Accent")
    for s in (1, -1):
        for j in range(7):
            t0, t1 = j / 7, (j + 1) / 7
            A, B = Vector((s * 0.13, 0.0, 1.9)), Vector((s * 0.165, 0.13, 1.68))
            a = A.lerp(B, t0); b = A.lerp(B, t1); d = (B - A).normalized(); nn = Vector((s * 0.35, 1, 0.25)).normalized()
            w = nn.cross(d).normalized()
            P.obj("Lappet", hull([tuple(p + w * dw + nn * dn) for p in (a, b) for dw in (-0.06, 0.06) for dn in (-0.02, 0.02)]), "Trim" if j % 2 else "Accent", 0, False)
    # ---- the obelisk he stands on: red granite, point down
    n0 = 8
    def octo(h, z, c=0.035):
        return [(sx_ * (h - c) if k == 0 else sx_ * h, sy_ * h if k == 0 else sy_ * (h - c), z) for sx_ in (1, -1) for sy_ in (1, -1) for k in (0, 1)]
    P.obj("Obelisk", hull(octo(AN_HALF0, AN_TOP - 0.001) + octo(AN_HALF1, AN_FOOT)), "Metal", 0, False)
    P.obj("Pyramidion", hull(octo(AN_HALF1 + 0.01, AN_FOOT + 0.005, 0.03) + [(0, 0, AN_TIP)]), "Trim", 0, False)
    for s in (1, -1):   # the gold border inlaid round its top
        P.obj("Inlay", box((0, s * (AN_HALF0 - 0.06), AN_TOP + 0.004), (2 * AN_HALF0 - 0.12, 0.03, 0.012)), "Trim", 0, False)
        P.obj("Inlay", box((s * (AN_HALF0 - 0.06), 0, AN_TOP + 0.004), (0.03, 2 * AN_HALF0 - 0.12, 0.012)), "Trim", 0, False)
    KINDS = ["eye", "ankh", "feather", "bird", "water", "sun"]
    for f, nrm in enumerate(((0, 1, 0), (1, 0, 0), (0, -1, 0), (-1, 0, 0))):
        for col, u in enumerate((-0.11, 0.11)):
            for row in range(6):
                z = -0.17 - row * 0.215
                P.obj("Glyph", an_on_face(an_glyph(KINDS[(row + col * 3 + f) % 6]), nrm, u, z), "Glow", 0, False)
        for u in (-0.22, 0.0, 0.22):   # incised lines between the columns
            P.obj("Groove", an_on_face(box((0, 0.004, 0), (0.012, 0.008, 1.32)), nrm, u, -0.76, 0.003), "Dark", 0, False)
    # ---- the sand pouring from its point
    P.part("Cloth", pipe([(0, 0, AN_TIP + 0.02), (0, 0.0, AN_TIP - 0.25), (0, 0.0, AN_TIP - 0.45)], [0.012, 0.022, 0.03], 8), "Trim", (0, 0, AN_TIP))
    for k in range(22):
        t = k / 21; a = k * 2.4
        r = 0.03 + 0.2 * t
        P.part("Cloth", ball((math.cos(a) * r, math.sin(a) * r, AN_TIP - 0.4 - 0.45 * t), (0.018 - 0.008 * t,) * 3, 6, 3), "Trim", (0, 0, AN_TIP))
    # ---- the four canopic jars circling it
    hub = (0, 0, AN_JAR_Z)
    for k, kind in enumerate(("human", "baboon", "jackal", "falcon")):
        a = math.radians(45 + 90 * k)
        m = Matrix.Rotation(-a + math.pi, 3, "Z")   # the jar's +y looks outward
        pos = Vector((math.sin(a) * AN_JAR_R, math.cos(a) * AN_JAR_R, AN_JAR_Z - 0.3))
        for bm, slot in an_jar(kind):
            out = Vector((math.sin(a), math.cos(a), 0))
            P.part("SpinJars", xf(bm, Matrix.Rotation(math.atan2(out.x, out.y), 3, "Z").inverted(), tuple(pos)), slot, hub)
    P.part("Muzzle", ball(tuple(H + Vector((0, 0.4, -0.17))), (0.03, 0.02, 0.03), 8, 4), "Glass", tuple(H + Vector((0, 0.4, -0.17))))
    return P



# ================================================================= sphinx (2026-10-13 remake)
SX_HUB = 0.42        # the wings' shoulder hinge, out from the spine


def sx_ribbon(rows, thick=0.03):
    """a thick band through rows of (a, b) point pairs: each row a straight edge across the band."""
    bm = bmesh.new(); top, bot = [], []
    for i, (a, b) in enumerate(rows):
        a, b = Vector(a), Vector(b)
        along = (Vector(rows[min(i + 1, len(rows) - 1)][0]) - Vector(rows[max(i - 1, 0)][0]))
        nrm = (b - a).cross(along).normalized() * (thick * 0.5)
        top.append((bm.verts.new(a + nrm), bm.verts.new(b + nrm))); bot.append((bm.verts.new(a - nrm), bm.verts.new(b - nrm)))
    for i in range(len(rows) - 1):
        (a0, b0), (a1, b1) = top[i], top[i + 1]; (c0, d0), (c1, d1) = bot[i], bot[i + 1]
        bm.faces.new((a0, b0, b1, a1)); bm.faces.new((c0, c1, d1, d0))
        bm.faces.new((a0, a1, c1, c0)); bm.faces.new((b0, d0, d1, b1))
    bm.faces.new((top[0][0], bot[0][0], bot[0][1], top[0][1])); bm.faces.new((top[-1][0], top[-1][1], bot[-1][1], bot[-1][0]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def sx_rows(keys, n):
    """n+1 rows interpolated (smoothly, through every key) between key rows of (a, b) pairs."""
    out = []
    m = len(keys) - 1
    for i in range(n + 1):
        t = i / n * m; k = min(int(t), m - 1); f = t - k
        f = f * f * (3 - 2 * f)
        a = Vector(keys[k][0]).lerp(Vector(keys[k + 1][0]), f); b = Vector(keys[k][1]).lerp(Vector(keys[k + 1][1]), f)
        out.append((a, b))
    return out


def sx_cut(bm, keep):
    """drop the faces whose centre fails keep(centre)."""
    dead = [f for f in bm.faces if not keep(f.calc_center_median())]
    bmesh.ops.delete(bm, geom=dead, context="FACES")
    return bm


def sx_feather(u0, v0, du, dv, L, W, tip=0.5, n=10):
    """a feather's outline in the wing's flat (u, v) plane: from its quill at (u0, v0) along (du, dv), length L, width W; a rounded
    end, or (tip < 0.5) a narrowing one, the separated finger of a primary."""
    d = Vector((du, dv)).normalized(); w = Vector((-d.y, d.x))
    def hw(t):
        if t < 0.3: return W * 0.5 * (0.35 + 0.65 * math.sin(math.pi * 0.5 * t / 0.3))
        if tip < 0.5 and t > 0.55: return W * 0.5 * (tip + (1 - tip) * (1 - (t - 0.55) / 0.45)) * math.sqrt(max(0.0, 1 - ((t - 0.9) / 0.1) ** 2) if t > 0.9 else 1.0)
        if t > 0.75: return W * 0.5 * math.sqrt(max(0.0, 1 - ((t - 0.75) / 0.25) ** 2))
        return W * 0.5
    ts = [i / n for i in range(n + 1)]
    q = Vector((u0, v0))
    return [q + d * (L * t) + w * hw(t) for t in ts] + [q + d * (L * t) - w * hw(t) for t in reversed(ts[:-1])]


def D_sphinx():
    """The WINGED SPHINX (2026-10-13, remade: "same as the alien bosses - realistic details, scarier, keep the cartoon shape"): the same
    lion with a pharaoh's head and great banded wings, now built like a real winged sphinx of ancient art. A lion's body: a deep chest and
    heavy shoulders, the ridge of the shoulder blades and the swell of the haunches standing out under a tawny coat, a pale belly, a narrow
    waist, a long tail ending in a dark tuft. The head is a pharaoh's: a stern, heavy face - a straight nose, full lips set hard and turned
    down at the corners, high cheekbones, and almond eyes outlined in black kohl, the kohl line drawn out to the temples, the eyes burning
    turquoise under brows drawn down in a frown. On it the royal nemes: the striped headcloth in gold and lapis, pulled tight across the
    brow under a gold band, falling behind the ears into the two broad lappets that hang down onto the chest, gathered behind into a braided
    queue; the uraeus rearing from the brow band - a gold cobra with its hood spread, its eyes alight (his shots leave from its mouth); the
    straight plaited false beard of a pharaoh, strapped up to the ears. Over the chest the broad bead collar (wesekh) in rows of gold, lapis,
    turquoise and carnelian, a row of drop beads round its edge.
    He flies on the GREAT FALCON WINGS OF HORUS: two wings built like a falcon's and painted like the wings carved over every temple door -
    the gold leading edge, then two rows of small rounded coverts lying like scales, lapis and turquoise, a row of carnelian-red middle
    coverts and a row of gold greater coverts, under them the long secondaries in lapis, each tipped in gold, and at the hand nine long
    primaries fanning out, separated like fingers at their tips, banded turquoise, lapis and gold. They beat (FlapL, FlapR, hinged at the
    shoulders). He comes on in a lion's leap - the forelegs reaching at the player with the claws out, the hind legs thrown back pushing off
    (SwayLeg0-3), the tail streaming behind and swaying (SwayTail)."""
    P = Boss("sphinx", {"Base": ((0.80, 0.56, 0.28), 0.4), "Belly": ((0.95, 0.85, 0.66), 0.35), "Accent": LAPIS, "Trim": GOLD,
                        "Glass": ((0.12, 0.70, 0.66), 0.7), "Dark": ((0.07, 0.05, 0.04), 0.5), "Glow": ((1.0, 0.80, 0.35), 0.5),
                        "Metal": ((0.70, 0.16, 0.08), 0.55), "Lamp": ((0.15, 1.0, 0.78), 0.8)})
    V = Vector

    # ---- the lion's body along a spine: the neck rising to the head, a deep chest, a narrow waist, the haunches
    neck = bez((0, 0.86, 0.6), (0, 0.8, 0.45), (0, 0.72, 0.32), (0, 0.6, 0.24), 5)
    torso = bez((0, 0.6, 0.24), (0, 0.15, 0.16), (0, -0.45, 0.18), (0, -0.95, 0.26), 14)[1:]
    PTS = neck + torso; NN = len(neck); n = len(PTS)
    RX, RZ = [], []
    for i in range(NN):
        u = i / (NN - 1)
        RX.append(lerp_keys(u, [(0, 0.2), (1, 0.32)])); RZ.append(lerp_keys(u, [(0, 0.22), (1, 0.38)]))
    for i in range(len(torso)):
        u = (i + 1) / len(torso)
        RX.append(lerp_keys(u, [(0, 0.33), (0.12, 0.35), (0.5, 0.25), (0.78, 0.31), (0.93, 0.26), (1, 0.14)]))
        RZ.append(lerp_keys(u, [(0, 0.4), (0.12, 0.42), (0.5, 0.27), (0.78, 0.32), (0.93, 0.26), (1, 0.14)]))
    FR = spine_frames(PTS)
    def coat(c, n_):
        i = min(range(n), key=lambda k: (PTS[k] - c).length_squared); t, side, up = FR[i]
        v = (c - PTS[i]).dot(up) / RZ[i]
        return "Belly" if v < -0.5 else "Base"
    P.obj("Body", body_loft(PTS, RX, RZ, FR, seg=26, sq=1.15, flat=0.85), coat, 0)
    # the muscles that show through a lion's coat: shoulder blades, the upper arms, the haunches
    for s in (1, -1):
        P.obj("Scapula", oriented_ball(V((s * 0.24, 0.5, 0.22)), (0.1, 0.24, 0.2), V((1, 0, 0)), V((0, 0.55, 0.83)).normalized(), V((0, -0.83, 0.55)).normalized(), 12, 6), "Base")
        P.obj("Haunch", oriented_ball(V((s * 0.22, -0.72, 0.12)), (0.13, 0.3, 0.26), V((1, 0, 0)), V((0, 0.85, -0.5)).normalized(), V((0, 0.5, 0.85)).normalized(), 12, 6), "Base")

    # ---- the legs, each its own mover hinged at the shoulder or hip, in a leaping pose
    def paw(name, hub, ft, d, size=1.0, dew=False):
        d = V(d).normalized(); sd = d.cross(V((0, 0, 1))).normalized(); upp = sd.cross(d).normalized()
        P.part(name, oriented_ball(ft, (0.1 * size, 0.12 * size, 0.07 * size), sd, d, upp, 12, 6), "Base", hub)
        P.part(name, oriented_ball(ft - upp * 0.045 * size + d * 0.01, (0.07 * size, 0.07 * size, 0.03 * size), sd, d, upp, 10, 4), "Dark", hub)
        for k in range(4):
            a = (k - 1.5) * 0.36
            dd = (Matrix.Rotation(a, 3, upp) @ d).normalized()
            tp = ft + dd * 0.1 * size
            P.part(name, ball(tuple(tp), (0.042 * size, 0.045 * size, 0.04 * size), 8, 4), "Base", hub)
            c0 = tp + dd * 0.03 * size
            P.part(name, pipe(bez(c0, c0 + dd * 0.05 * size, c0 + dd * 0.085 * size - upp * 0.02 * size, c0 + dd * 0.09 * size - upp * 0.075 * size, 4),
                              [0.018 * size, 0.015 * size, 0.01 * size, 0.005, 0.0], 6), "Belly", hub)
        if dew:
            c0 = ft - d * 0.1 * size + sd * 0.08 * size
            P.part(name, pipe([c0, c0 - upp * 0.05 * size + d * 0.02], [0.012, 0.0], 5), "Belly", hub)
    def leg(name, joints, radii, pawdir, size=1.0, dew=False):
        hub = tuple(joints[0])
        for i in range(len(joints) - 1):
            a, b = joints[i], joints[i + 1]
            P.part(name, pipe([a, (a + b) * 0.5, b], [radii[i], (radii[i] + radii[i + 1]) * 0.55, radii[i + 1]], 12), "Base", hub)
            if i > 0: P.part(name, ball(tuple(a), (radii[i] * 1.05,) * 3, 10, 5), "Base", hub)
        paw(name, hub, joints[-1], pawdir, size, dew)
    leg("SwayLeg0", [V((0.24, 0.55, 0.06)), V((0.27, 0.74, -0.2)), V((0.26, 1.08, -0.3)), V((0.26, 1.24, -0.33))], [0.16, 0.11, 0.08, 0.08], (0, 1, -0.25), 1.0, True)
    leg("SwayLeg1", [V((-0.24, 0.55, 0.06)), V((-0.27, 0.6, -0.28)), V((-0.26, 0.9, -0.42)), V((-0.26, 1.04, -0.48))], [0.16, 0.11, 0.08, 0.08], (0, 1, -0.45), 1.0, True)
    leg("SwayLeg2", [V((0.23, -0.74, 0.1)), V((0.27, -0.52, -0.2)), V((0.26, -0.9, -0.33)), V((0.25, -1.12, -0.42))], [0.17, 0.12, 0.075, 0.075], (0, -1, -0.5), 0.95)
    leg("SwayLeg3", [V((-0.23, -0.74, 0.1)), V((-0.27, -0.56, -0.24)), V((-0.26, -0.98, -0.28)), V((-0.25, -1.22, -0.33))], [0.17, 0.12, 0.075, 0.075], (0, -1, -0.3), 0.95)

    # ---- the tail: long, streaming back and up in an S, a dark tuft at the end; it sways
    tb = V((0, -0.98, 0.27))
    tpts = bez(tb, (0, -1.4, 0.2), (0.1, -1.7, 0.55), (0.06, -2.0, 0.62), 12)
    P.part("SwayTail", pipe(tpts, [lerp_keys(j / 12, [(0, 0.07), (0.3, 0.05), (1, 0.03)]) for j in range(13)], 8), "Base", tuple(tb))
    tip = tpts[-1]; tdir = (tpts[-1] - tpts[-2]).normalized()
    for k in range(7):
        a = 2 * math.pi * k / 7; side = tdir.cross(V((0, 0, 1))).normalized(); upp = side.cross(tdir)
        off = (side * math.cos(a) + upp * math.sin(a)) * 0.035
        P.part("SwayTail", pipe([tip - tdir * 0.02 + off * 0.5, tip + tdir * 0.12 + off * 1.6, tip + tdir * 0.2 + off * 1.2], [0.03, 0.025, 0.0], 6), "Dark", tuple(tb))
    P.part("SwayTail", ball(tuple(tip + tdir * 0.03), (0.055, 0.055, 0.055), 8, 4), "Dark", tuple(tb))

    # ---- the bead collar (wesekh) over the chest: rows of gold, lapis, turquoise and carnelian, drop beads round the edge
    cc = V((0, 0.66, 0.36)); ax = V((0, 0.62, -0.78)).normalized()   # the collar lies on the chest, tipped forward
    cx = V((1, 0, 0)); cy = ax.cross(cx).normalized()
    def on_collar(r, a, lift=0.0):
        return cc + cx * (math.sin(a) * r * 1.05) + cy * (math.cos(a) * r) * -1 + ax * lift - V((0, 0, 1)) * 0.0
    rows = [(0.2, "Trim"), (0.25, "Accent"), (0.3, "Glass"), (0.35, "Metal"), (0.4, "Trim"), (0.45, "Accent")]
    for r, slot in rows:
        arc = [on_collar(r, math.radians(a)) for a in range(-118, 119, 6)]
        P.obj("Collar", pipe(arc, [0.03] * len(arc), 6, True), slot)
    for k in range(-15, 16):
        a = math.radians(k * 7.6); p = on_collar(0.5, a)
        P.obj("CollarDrop", oriented_ball(p, (0.022, 0.03, 0.045), cx, cy * -1, ax, 8, 4), "Trim" if k % 2 == 0 else "Metal")

    # ---- the head, built pointing +Y about its centre, then set on the neck and scaled
    HC = V((0, 0.94, 0.86)); HR = Matrix.Rotation(math.radians(-4), 3, "X") @ Matrix.Scale(1.3, 3)
    def H(bm): return xf(bm, HR, tuple(HC))
    def hp(c): return HR @ V(c) + HC
    P.obj("Skull", H(ball((0, -0.01, 0.02), (0.19, 0.2, 0.23), 18, 10)), "Base")
    P.obj("Jaw", H(ball((0, 0.06, -0.1), (0.15, 0.15, 0.14), 16, 8)), "Base")
    P.obj("Cheek", H(ball((0.0, 0.1, -0.02), (0.165, 0.11, 0.1), 14, 7)), "Base")
    # a straight nose from the brow to its tip, its wings and nostrils
    P.obj("Nose", H(hull([(0, 0.2, 0.06), (-0.018, 0.19, 0.06), (0.018, 0.19, 0.06), (0, 0.262, -0.07), (-0.04, 0.215, -0.085), (0.04, 0.215, -0.085),
                         (0, 0.235, -0.095), (-0.03, 0.2, -0.09), (0.03, 0.2, -0.09)])), "Base", 0, False)
    for s in (1, -1):
        P.obj("Nostril", H(ball((s * 0.022, 0.228, -0.092), (0.012, 0.008, 0.006), 6, 3)), "Dark")
    # lips set hard, the corners turned down
    P.obj("LipTop", H(pipe(bez((-0.06, 0.19, -0.135), (-0.03, 0.215, -0.122), (0.03, 0.215, -0.122), (0.06, 0.19, -0.135), 6), [0.008, 0.012, 0.014, 0.014, 0.014, 0.012, 0.008], 8)), "Metal")
    P.obj("LipLow", H(pipe(bez((-0.05, 0.185, -0.15), (-0.025, 0.205, -0.162), (0.025, 0.205, -0.162), (0.05, 0.185, -0.15), 6), [0.007, 0.011, 0.014, 0.014, 0.014, 0.011, 0.007], 8)), "Metal")
    P.obj("Mouth", H(pipe(bez((-0.07, 0.185, -0.15), (-0.03, 0.21, -0.14), (0.03, 0.21, -0.14), (0.07, 0.185, -0.15), 6), [0.006] * 7, 6)), "Dark")
    for s in (1, -1):
        # almond eyes in black kohl, the kohl drawn out to the temple; the eye burns turquoise; a brow ridge drawn down in a frown
        e = V((s * 0.075, 0.172, 0.035))
        P.obj("Kohl", H(oriented_ball(e, (0.052, 0.026, 0.022), V((1, 0, 0)), V((0, 1, 0)), V((0, 0, 1)), 12, 6)), "Dark")
        P.obj("Eye", H(oriented_ball(e + V((0, 0.012, 0.0)), (0.04, 0.02, 0.014), V((1, 0, 0)), V((0, 1, 0)), V((0, 0, 1)), 12, 6)), "Lamp")
        P.obj("Pupil", H(ball(tuple(e + V((s * -0.004, 0.028, 0.0))), (0.007, 0.006, 0.012), 6, 3)), "Dark")
        P.obj("KohlLine", H(pipe([e + V((s * 0.045, 0.0, 0.002)), e + V((s * 0.085, -0.03, 0.012)), e + V((s * 0.11, -0.06, 0.016))], [0.009, 0.008, 0.004], 6)), "Dark")
        P.obj("Lid", H(pipe(bez(e + V((-s * 0.05, 0.02, 0.0)), e + V((-s * 0.02, 0.035, 0.03)), e + V((s * 0.025, 0.03, 0.024)), e + V((s * 0.05, 0.012, 0.012)), 6), [0.01, 0.013, 0.014, 0.013, 0.011, 0.009, 0.006], 6)), "Base")
        P.obj("Brow", H(pipe(bez(e + V((s * 0.065, 0.0, 0.07)), e + V((s * 0.03, 0.03, 0.065)), e + V((-s * 0.02, 0.04, 0.045)), e + V((-s * 0.06, 0.035, 0.022)), 6), [0.008, 0.013, 0.016, 0.016, 0.014, 0.011, 0.007], 6)), "Dark")
        P.obj("BrowRidge", H(pipe(bez(e + V((s * 0.07, -0.01, 0.06)), e + V((s * 0.03, 0.02, 0.055)), e + V((-s * 0.02, 0.03, 0.04)), e + V((-s * 0.065, 0.025, 0.02)), 6), [0.016, 0.022, 0.026, 0.026, 0.022, 0.016, 0.01], 8)), "Base")
        P.obj("Ear", H(oriented_ball(V((s * 0.19, -0.01, -0.0)), (0.025, 0.05, 0.07), V((1, 0, 0)), V((0, 1, 0)), V((0, 0, 1)), 10, 5)), "Base")

    # the nemes: the cap over the head behind the brow band, striped gold and lapis
    def stripes(c, n_):
        return "Accent" if (c.z * 13.0) % 1.0 < 0.5 else "Trim"
    # (the ball's poles lie on the ear axis, so its meridians run over the head parallel to the brow band: each band of faces one stripe)
    SXC, SXR = V((0, -0.02, 0.03)), (0.215, 0.23, 0.26)
    cap = ball((0, 0, 0), (1, 1, 1), 48, 26)
    for v in cap.verts:
        q = Matrix.Rotation(math.pi / 2, 3, "Y") @ v.co
        v.co = V((q.x * SXR[0], q.y * SXR[1], q.z * SXR[2])) + SXC
    cap = sx_cut(cap, lambda c: c.z > 0.07 or c.y < -0.02 or (abs(c.x) > 0.17 and c.y < 0.06))
    def cap_paint(c, n_):   # stripes running round the head parallel to the brow band, as on a real nemes
        q = HR.inverted() @ (c - HC) - SXC; a = math.atan2(q.y / SXR[1], q.z / SXR[2])
        return "Accent" if int((a + math.pi) / (2 * math.pi) * 48) // 2 % 2 else "Trim"
    P.obj("Nemes", H(cap), cap_paint)
    P.obj("BrowBand", H(pipe([V((math.sin(math.radians(a)) * 0.214, math.cos(math.radians(a)) * 0.228 - 0.02, 0.09)) for a in range(-100, 101, 8)], [0.018] * 26, 8)), "Trim")
    # the cloth falling behind the ears, flaring over the shoulders into the two lappets that hang down on the chest
    for s in (1, -1):
        keys = [((s * 0.17, 0.05, 0.1), (s * 0.19, -0.14, 0.12)),
                ((s * 0.22, 0.06, -0.06), (s * 0.33, -0.13, -0.06)),
                ((s * 0.26, 0.08, -0.24), (s * 0.43, -0.08, -0.26)),
                ((s * 0.24, 0.15, -0.42), (s * 0.38, 0.06, -0.44)),
                ((s * 0.2, 0.2, -0.64), (s * 0.32, 0.14, -0.66)),
                ((s * 0.19, 0.22, -0.8), (s * 0.3, 0.17, -0.82))]
        P.obj("Lappet", H(sx_ribbon(sx_rows(keys, 30), 0.025)), stripes)
        P.obj("LappetHem", H(pipe([V(keys[-1][0]) + V((0, 0.005, -0.012)), V(keys[-1][1]) + V((0, 0.005, -0.012))], [0.015, 0.015], 6)), "Trim")
    # the queue behind: the cloth gathered and bound into a braided tail
    q = bez((0, -0.2, 0.06), (0, -0.27, -0.06), (0, -0.28, -0.2), (0, -0.26, -0.34), 10)
    P.obj("Queue", H(pipe(q, [0.06, 0.06, 0.058, 0.055, 0.052, 0.05, 0.048, 0.046, 0.044, 0.04, 0.03], 10)), stripes)
    # the uraeus: a gold cobra reared on the brow band, its hood spread, its eyes alight
    P.obj("Uraeus", H(pipe(bez((0, 0.205, 0.08), (0, 0.23, 0.14), (0, 0.24, 0.2), (0, 0.235, 0.26), 6), [0.02, 0.022, 0.024, 0.024, 0.022, 0.02, 0.018], 8)), "Trim")
    P.obj("Hood", H(oriented_ball(V((0, 0.24, 0.27)), (0.055, 0.015, 0.06), V((1, 0, 0)), V((0, 1, 0)), V((0, 0, 1)), 12, 6)), "Trim")
    P.obj("HoodInlay", H(oriented_ball(V((0, 0.252, 0.27)), (0.035, 0.008, 0.04), V((1, 0, 0)), V((0, 1, 0)), V((0, 0, 1)), 10, 5)), "Accent")
    P.obj("CobraHead", H(oriented_ball(V((0, 0.26, 0.335)), (0.022, 0.035, 0.018), V((1, 0, 0)), V((0, 1, 0)), V((0, 0, 1)), 8, 4)), "Trim")
    for s in (1, -1):
        P.obj("CobraEye", H(ball((s * 0.016, 0.275, 0.342), (0.007, 0.007, 0.007), 6, 3)), "Lamp")
    mz = hp((0, 0.3, 0.33))
    P.part("Muzzle", ball(tuple(mz), (0.03, 0.02, 0.025), 8, 4), "Lamp", tuple(mz))
    # the false beard: straight, plaited, the tip curled forward, strapped to the ears
    bp = bez((0, 0.19, -0.19), (0, 0.205, -0.3), (0, 0.205, -0.42), (0, 0.235, -0.5), 10)
    P.obj("Beard", H(pipe(bp, [0.035, 0.036, 0.036, 0.035, 0.034, 0.033, 0.032, 0.031, 0.03, 0.03, 0.026], 8)),
          lambda c, n_: "Accent" if ((HR.inverted() @ (c - HC)).z * 40) % 1.0 < 0.5 else "Trim")
    for s in (1, -1):
        P.obj("BeardStrap", H(pipe(bez((s * 0.03, 0.19, -0.19), (s * 0.12, 0.15, -0.17), (s * 0.17, 0.08, -0.1), (s * 0.19, 0.01, -0.04), 6), [0.007] * 7, 5)), "Dark")

    # ---- the falcon wings of Horus, feather by feather, each wing its own mover hinged at the shoulder
    def wing(s):
        name = "FlapR" if s > 0 else "FlapL"
        hub = V((s * SX_HUB, 0.42, 0.42))
        def W3(u, v, h=0.0):
            """the wing's flat (u out along the span, v forward) plane in the world: swept back and curving up toward the tip."""
            return hub + V((s * u * 0.95, v - 0.12 * u, 0.3 * u + 0.08 * u * u + h))
        def LE(u):   # the leading edge's v at u along the span
            return 0.14 - 0.03 * u if u < 1.45 else 0.0965 - 0.25 * (u - 1.45)
        def feather(u0, v0, du, dv, L, Wd, col, tipcol, h, tip=0.5, band=None):
            pts = sx_feather(u0, v0, du, dv, L, Wd, tip)
            d = Vector((du, dv)).normalized()
            q0 = Vector((u0, v0))
            def paint(c, n_, q0=q0, d=d, L=L):
                return col
            # split the outline: the tip band in its own colour
            poly = [W3(p.x, p.y, h) for p in pts]
            bm = sheet([poly], 0.018)
            # paint per face is one colour per sheet: the tip band is a second, smaller sheet laid over the end
            P.part(name, bm, col, tuple(hub))
            if tipcol:
                tpts = sx_feather(u0 + d.x * L * 0.72, v0 + d.y * L * 0.72, du, dv, L * 0.28, Wd * 0.98, tip)
                P.part(name, sheet([[W3(p.x, p.y, h + 0.012) for p in tpts]], 0.016), tipcol, tuple(hub))
            if band:
                bpts = sx_feather(u0 + d.x * L * 0.42, v0 + d.y * L * 0.42, du, dv, L * 0.22, Wd * 0.96, 0.5)
                P.part(name, sheet([[W3(p.x, p.y, h + 0.012) for p in bpts]], 0.016), band, tuple(hub))
        # the leading edge: the gold-bound bone of the arm and hand
        lpts = [W3(u, LE(u) - 0.02, 0.06) for u in [x * 0.1 for x in range(0, 20)]]
        P.part(name, pipe(lpts, [lerp_keys(j / 19, [(0, 0.07), (0.7, 0.05), (1, 0.03)]) for j in range(20)], 8), "Trim", tuple(hub))
        P.part(name, ball(tuple(W3(1.45, LE(1.45) - 0.02, 0.06)), (0.06, 0.06, 0.06), 8, 4), "Trim", tuple(hub))
        # primaries: nine long fingers fanning out from the hand
        lens = [1.2, 1.36, 1.46, 1.46, 1.4, 1.3, 1.2, 1.1, 1.02]
        for k in range(9):
            t = k / 8
            u0 = 1.95 - 0.55 * t; v0 = LE(u0) - 0.1
            ang_ = math.radians(8 - 70 * t)   # 8 deg forward of straight out ... 62 deg back
            du, dv = math.cos(ang_), math.sin(ang_)
            feather(u0, v0, du, dv, lens[k], 0.2, "Glass", "Trim", -0.01 - 0.004 * k, 0.15, "Accent")
        # secondaries: long, lapis, gold-tipped, along the arm's trailing edge
        for k in range(12):
            u0 = 0.12 + 0.11 * k; v0 = LE(u0) - 0.5
            L = 0.86 + 0.16 * math.sin(math.pi * min(1.0, k / 9))
            feather(u0, v0, 0.12, -1.0, L, 0.19, "Accent", "Trim", 0.0)
        # greater coverts (gold, lapis tip), middle coverts (carnelian, gold tip), and two rows of small scale-like coverts
        for row, (dv0, L, Wd, col, tipcol, h, step) in enumerate([(-0.38, 0.42, 0.17, "Trim", "Accent", 0.02, 0.12),
                                                                  (-0.26, 0.32, 0.16, "Metal", "Trim", 0.03, 0.115),
                                                                  (-0.14, 0.21, 0.15, "Glass", None, 0.04, 0.11),
                                                                  (-0.04, 0.15, 0.14, "Accent", None, 0.05, 0.1)]):
            u = 0.06 + (step * 0.5 if row % 2 else 0.0); umax = 1.62 - 0.08 * row
            while u < umax:
                feather(u, LE(u) + dv0 + 0.02, 0.1, -1.0, L, Wd, col, tipcol, h, 0.5)
                u += step
    wing(1); wing(-1)
    return P



# ================================================================= cobra (2026-10-13 remake)
CB_DC = Vector((0.0, -0.3, 1.86))   # the sun disk's centre
CB_DR = 1.27                         # and radius
CB_RB = 1.45                         # the coil's radius round it


def cb_key(c):
    return (round(c[0], 3), round(c[1], 3), round(c[2], 3))

def cb_paint(table, default="Base"):
    return lambda c, n: table.get(cb_key(c), default)

def cb_loft(pts, bel, rx, rz, slot_of, seg=16, bulge=None):
    """a snake's body along pts: belly toward bel[i], rx across, rz belly-to-back; slot_of(i, k, a) paints each face.
    bulge(i, a) pushes a ring point out along its own direction (the hood's ribs, the cupped hood)."""
    bm = bmesh.new(); rings = []; table = {}
    n = len(pts)
    for i, p in enumerate(pts):
        t = (pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]).normalized()
        b = bel[i] - t * bel[i].dot(t); b.normalize(); s = t.cross(b).normalized()
        if rx[i] < 1e-4: rings.append([bm.verts.new(p)]); continue
        ring = []
        for k in range(seg):
            a = 2 * math.pi * k / seg
            off = s * math.cos(a) * rx[i] + b * math.sin(a) * rz[i]
            if bulge: off += b * bulge(i, a)
            ring.append(bm.verts.new(p + off))
        rings.append(ring)
    faces = []
    for i, (r0, r1) in enumerate(zip(rings, rings[1:])):
        if len(r0) == 1 and len(r1) == 1: continue
        for k in range(seg):
            a = 2 * math.pi * (k + 0.5) / seg
            if len(r0) == 1: f = bm.faces.new((r0[0], r1[k], r1[(k + 1) % seg]))
            elif len(r1) == 1: f = bm.faces.new((r0[k], r1[0], r0[(k + 1) % seg]))
            else: f = bm.faces.new((r0[k], r0[(k + 1) % seg], r1[(k + 1) % seg], r1[k]))
            faces.append((f, slot_of(i, k, a)))
    if len(rings[-1]) > 1:
        f = bm.faces.new(rings[-1]); faces.append((f, "Base"))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f, slot in faces: table[cb_key(f.calc_center_median())] = slot
    return bm, table

def cb_feather(root, d, L, w, thick=0.035):
    """a flat Egyptian feather in the XZ plane: a straight blade from root along d, L long, w wide, with a rounded end."""
    root, d = Vector(root), Vector(d).normalized(); s = Vector((-d.z, 0, d.x)) * w * 0.5
    pts = [root + s, root - s, root + d * L * 0.82 + s, root + d * L * 0.82 - s, root + d * L + s * 0.45, root + d * L - s * 0.45]
    out = []
    for p in pts: out += [tuple(p + Vector((0, thick * 0.5, 0))), tuple(p - Vector((0, thick * 0.5, 0)))]
    return hull(out)


def D_cobra():
    """The PHARAOH COBRA (2026-10-13, remade: "same as the alien bosses - realistic details, scarier, keep the cartoon shape"): the same
    giant golden royal cobra reared to strike, now built like a real Egyptian cobra and like the uraeus on a pharaoh's brow. Its long body
    is covered in smooth overlapping dorsal scales in bronze and gold set in an even diamond lattice, crossed at regular intervals by
    bands of lapis like the gold uraeus of the kings; underneath, the broad cream ventral scutes, one after another, each edged in gold.
    It rears from its coils with the hood spread wide on its long ribs (you can see them ridging the hood's back); the front of the hood
    is the uraeus's cloisonne - rows of gold cells inlaid with lapis, turquoise and carnelian, evenly, round the column of belly scutes
    running up the throat, with the dark throat band a real Egyptian cobra carries across it. The head is a cobra's: broad and flat,
    capped with the big smooth shields of an elapid (the frontal, the two parietals behind it, the supraoculars over the eyes jutting
    down into a frown, the prefrontals and internasals toward the snout) picked out in gold with dark seams; eyes glowing like coals
    under the brow ridges, with the round black pupil a cobra has; nostrils at the snout; the mouth thrown open in the strike - the hinged lower jaw snapping, a
    furnace glow inside, two short fixed fangs at the front of the upper jaw as on every cobra, a row of small teeth below, the black
    forked tongue flicking out. A small pharaoh's touch: a gold diadem round the back of its head inlaid with lapis, a carnelian at the brow.
    It flies by RIDING THE SUN DISK OF RA, the very icon of the uraeus: a great sun disk stands upright behind it facing the player - a
    thick disc in a heavy gold rim inlaid with lapis, its face glowing red-orange with a white-gold heart, twenty-four rays raised in
    gold running out from the heart - and the cobra's body is wound one and a half times round the rim, the tail tip at the top, coming
    off the bottom of the disk to rear up in front of it. The disk turns slowly face-on inside the coils (RollDisk); from its sides spread
    the carved gold wings of the winged sun of Behdet, rows of gold, turquoise and lapis feathers (static). Its shots leave from its jaws."""
    P = Boss("cobra", {"Base": ((0.70, 0.47, 0.14), 0.7), "Belly": ((0.90, 0.80, 0.55), 0.4), "Accent": LAPIS, "Trim": GOLD,
                       "Glass": ((0.10, 0.62, 0.58), 0.9), "Dark": ((0.05, 0.03, 0.02), 0.5), "Glow": ((1.0, 0.32, 0.06), 0.5),
                       "Metal": ((0.70, 0.10, 0.06), 0.5), "Lamp": ((1.0, 0.88, 0.50), 0.8)})
    dc = CB_DC

    # ---- the body: the tail tip at the top of the disk, one and a half turns round its rim, off the bottom, a U-turn forward, then up
    NC = 200
    pts, bel, rx, rz = [], [], [], []
    for i in range(NC + 1):
        u = i / NC; th = math.radians(90 - 505 * u)
        y = dc.y - 0.24 + 0.52 * u
        p = Vector((math.cos(th) * CB_RB, y, dc.z + math.sin(th) * CB_RB))
        pts.append(p); bel.append(Vector((dc.x - p.x, 0, dc.z - p.z)).normalized())
        r = 0.17 * min(1.0, 0.12 + u / 0.3) if u < 0.3 else 0.17
        if i == 0: r = 0.0
        rx.append(r); rz.append(r * 0.92)
    p0 = pts[-1]
    th1 = math.radians(90 - 505); tg1 = Vector((math.sin(th1), 0.25, -math.cos(th1))).normalized()
    turn = bez(p0, p0 + tg1 * 0.45, Vector((0.12, 0.72, 0.38)), Vector((0.0, 0.82, 0.62)), 16)[1:]
    rise = bez(Vector((0.0, 0.82, 0.62)), Vector((0.0, 0.9, 1.0)), Vector((0.0, 0.48, 1.38)), Vector((0.0, 0.62, 1.66)), 30)[1:]
    head = bez(Vector((0.0, 0.62, 1.66)), Vector((0.0, 0.66, 1.72)), Vector((0.0, 0.7, 1.73)), Vector((0.0, 0.78, 1.73)), 4)[1:]
    neck = turn + rise + head
    N0 = len(pts)
    i_rise0 = N0 + len(turn)
    for j, p in enumerate(neck):
        w = min(1.0, (j + 1) / len(turn))
        b = (Vector((0, 0, 1)) * (1 - w) + Vector((0, 1, 0.15)) * w).normalized()
        pts.append(p); bel.append(b)
        if j < len(turn): rx.append(0.17); rz.append(0.16); continue
        u = (j - len(turn)) / (len(rise) + len(head) - 1)
        rx.append(lerp_keys(u, [(0, 0.17), (0.14, 0.21), (0.3, 0.6), (0.52, 0.9), (0.72, 0.84), (0.86, 0.44), (1.0, 0.26)]))
        rz.append(lerp_keys(u, [(0, 0.16), (0.14, 0.15), (0.3, 0.1), (0.52, 0.085), (0.72, 0.09), (0.86, 0.13), (1.0, 0.17)]))
    NH0 = i_rise0; NH1 = len(pts) - 1
    def in_hood(i): return NH0 + 6 <= i <= NH1 - 2 and rx[i] > 0.3
    def bulge(i, a):
        if not in_hood(i): return 0.0
        cup = 0.22 * math.cos(a) ** 2 * (rx[i] / 0.9)                   # the hood's edges cupped forward
        rib = 0.02 if (math.sin(a) < -0.2 and (i - NH0) % 3 == 0) else 0.0  # the ribs ridging its back
        return cup - rib
    def slot(i, k, a):
        sa, ca = math.sin(a), math.cos(a)
        if in_hood(i) and sa > 0.0:                                       # the front of the hood: the uraeus's cloisonne
            x = abs(ca) * rx[i]
            if abs(ca) > 0.93: return "Trim"
            if x < 0.15: return "Trim" if (i % 3) == 2 else "Belly"       # the belly scutes running up the throat
            row = i - NH0
            if row in (9, 10): return "Dark"                               # the cobra's dark throat band
            if row % 2 == 0: return "Trim"
            return ("Accent", "Glass", "Accent", "Metal")[int((x - 0.15) / 0.13) % 4]
        if sa > 0.55: return "Trim" if (i % 3) == 2 else "Belly"          # ventral scutes
        if i % 10 == 0 and sa < 0.3: return "Accent"                       # lapis bands across the back
        return "Trim" if (i + k) % 6 == 0 or (i - k) % 6 == 0 else "Base"   # the overlapping dorsal scales, gold-edged in an even lattice
    bm, tab = cb_loft(pts, bel, rx, rz, slot, 16, bulge)
    P.obj("Body", bm, cb_paint(tab), 0)

    # ---- the head: broad and flat, a cobra's head shields on top, the mouth open in the strike
    nb0, ns0 = len(P.parts), len(P.spin)
    hc = Vector((0.0, 1.04, 1.78)); HX, HY, HZ = 0.31, 0.41, 0.15
    def skull_paint(c, n):
        return "Belly" if n.z < -0.6 else "Trim"
    P.obj("Skull", ball(tuple(hc), (HX, HY, HZ), 22, 12), skull_paint, 0)
    P.obj("Palate", ball(tuple(hc + Vector((0, 0.02, -0.115))), (0.26, 0.36, 0.035), 16, 6), "Glow")
    def top(x, y, lift=0.012):
        q = 1 - (x / HX) ** 2 - (y / HY) ** 2
        return hc + Vector((x, y, HZ * math.sqrt(max(q, 0.0)) + lift))
    shields = [((0.0, -0.03), (0.066, 0.1)), ((0.085, -0.21), (0.082, 0.11)), ((-0.085, -0.21), (0.082, 0.11)),
               ((0.066, 0.135), (0.062, 0.055)), ((-0.066, 0.135), (0.062, 0.055)),
               ((0.042, 0.255), (0.04, 0.04)), ((-0.042, 0.255), (0.04, 0.04))]
    # the elapid's head shields, drawn by their seams: the internasals and prefrontals across the snout, the long frontal between the
    # eyes narrowing behind, the two big parietals split down the middle
    seams = [[(-0.09, 0.2), (0.09, 0.2)], [(0.0, 0.2), (0.0, 0.31)], [(-0.16, 0.09), (0.16, 0.09)], [(0.0, 0.09), (0.0, 0.2)],
             [(0.075, 0.09), (0.07, -0.08), (0.0, -0.15), (-0.07, -0.08), (-0.075, 0.09)], [(0.0, -0.15), (0.0, -0.36)],
             [(0.07, -0.08), (0.2, -0.13)], [(-0.07, -0.08), (-0.2, -0.13)]]
    for line in seams:
        pts_ = []
        for (x0, y0), (x1, y1) in zip(line, line[1:]):
            for q in range(6): pts_.append(top(x0 + (x1 - x0) * q / 6, y0 + (y1 - y0) * q / 6, 0.0))
        pts_.append(top(*line[-1], 0.0))
        P.obj("Seam", pipe(pts_, [0.009] * len(pts_), 5), "Dark")
    for s in (1, -1):
        # the supraocular shields jut over the eyes and slope down to the snout: a frown
        e = hc + Vector((s * 0.2, 0.17, 0.045))
        P.obj("EyeRim", ball(tuple(e - Vector((s * 0.012, 0, 0))), (0.085, 0.09, 0.075), 12, 6), "Dark")
        P.obj("Eye", ball(tuple(e + Vector((s * 0.01, 0.01, 0))), (0.076, 0.08, 0.066), 14, 7), "Glow")
        P.obj("Pupil", ball(tuple(e + Vector((s * 0.06, 0.04, -0.005))), (0.03, 0.034, 0.034), 8, 4), "Dark")
        # the supraocular shield juts over the eye as a hard ridge, its inner end low at the snout: a frown
        P.obj("Brow", bar(tuple(e + Vector((-s * 0.11, 0.1, 0.035))), tuple(e + Vector((s * 0.07, -0.08, 0.11))), 0.07, 0.05, (0, 0, 1)), "Trim", 0, False)
        P.obj("Nostril", ball(tuple(hc + Vector((s * 0.07, 0.385, 0.035))), (0.026, 0.018, 0.018), 6, 3), "Dark")
        P.obj("Fang", cone(tuple(hc + Vector((s * 0.09, 0.29, -0.12))), tuple(hc + Vector((s * 0.085, 0.27, -0.27))), 0.026, 6), "Belly", 0, False)
    # a pharaoh's touch: a gold diadem round the back of its head, lapis set in it, a carnelian at the brow
    dia = torus(1.0, 0.07, 0.0, 32, 5)
    for v in dia.verts: v.co = Vector((v.co.x * 0.3, v.co.y * 0.24, v.co.z * 0.4))
    xf(dia, Matrix.Rotation(math.radians(-20), 3, "X"), tuple(hc + Vector((0, -0.16, 0.05))))
    P.obj("Diadem", dia, lambda c, n: "Accent" if int((math.atan2(c.x - hc.x, c.y - hc.y + 0.16) / (2 * math.pi) + 1) * 16) % 2 else "Trim")
    P.obj("Jewel", ball(tuple(top(0, 0.07, 0.03)), (0.04, 0.034, 0.028), 8, 4), "Metal")
    # the lower jaw: hinged at the back of the head, snapping (SwayJaw), the tongue flicking out of it
    hinge = hc + Vector((0.0, -0.3, -0.09))
    jaw = Matrix.Translation(hinge) @ Matrix.Rotation(math.radians(-30), 4, "X") @ Matrix.Translation(-hinge)
    def jp(p): return jaw @ Vector(p)
    jb = ball(tuple(hc + Vector((0, 0.0, -0.15))), (0.25, 0.36, 0.06), 16, 6); xf(jb, jaw.to_3x3(), (jaw.translation))
    P.part("SwayJaw", jb, lambda c, n: "Glow" if n.dot(jaw.to_3x3() @ Vector((0, 0, 1))) > 0.5 else "Belly", tuple(hinge))
    for s in (1, -1):
        for k in range(4):
            b0 = jp(hc + Vector((s * (0.17 - 0.014 * k), 0.02 + 0.065 * k, -0.1))); P.part("SwayJaw", cone(tuple(b0), tuple(b0 + Vector((0, 0.0, 0.05))), 0.014, 5), "Belly", tuple(hinge))
    tg = [jp(hc + Vector((0, 0.08, -0.1))), jp(hc + Vector((0, 0.3, -0.08))), jp(hc + Vector((0, 0.5, -0.07)))]
    P.part("SwayJaw", pipe(tg, [0.022, 0.02, 0.016], 6), "Dark", tuple(hinge))
    for s in (1, -1):
        P.part("SwayJaw", cone(tuple(tg[-1]), tuple(tg[-1] + Vector((s * 0.06, 0.1, 0.03))), 0.014, 5), "Dark", tuple(hinge))

    # the head pitched down at the player as it strikes: every head part turned about the head's base
    HS = 1.25   # and a little bigger than life, to read at a distance
    pitch = Matrix.Translation(hinge) @ Matrix.Rotation(math.radians(-16), 4, "X") @ Matrix.Scale(HS, 4) @ Matrix.Translation(-hinge)
    for ob in P.parts[nb0:]: ob.data.transform(pitch)
    for ob in P.spin[ns0:]:
        ob.data.transform(Matrix.Rotation(math.radians(-16), 4, "X") @ Matrix.Scale(HS, 4))
        ob.location = pitch @ ob.location
    # ---- the sun disk of Ra: a thick gold-rimmed disc facing the player, its face glowing, raised gold rays; it turns (RollDisk)
    hub = tuple(dc)
    prof = [(0.0, 0.135), (0.36, 0.125), (0.98, 0.1), (1.04, 0.11), (1.1, 0.15), (1.2, 0.15), (CB_DR, 0.09), (CB_DR, -0.09),
            (1.2, -0.15), (0.0, -0.15)]
    def disk_paint(c, n):
        d = c - dc; r = math.hypot(d.x, d.z)
        if d.y > 0.05 and r < 0.29: return "Lamp"
        if d.y > 0.05 and r < 1.02: return "Metal"
        if r > 1.19 and abs(d.y) < 0.1: return "Accent" if int((math.atan2(d.z, d.x) / (2 * math.pi) + 1) * 36) % 2 else "Trim"
        return "Trim"
    P.part("RollDisk", lathe(prof, 72, "y", hub), disk_paint, hub)
    P.part("RollDisk", ball((dc.x, dc.y + 0.13, dc.z), (0.27, 0.07, 0.27), 20, 6), "Lamp", hub)
    for k in range(24):
        a = 2 * math.pi * k / 24; L1 = 0.97 if k % 2 == 0 else 0.8
        u = Vector((math.cos(a), 0, math.sin(a)))
        P.part("RollDisk", bar(tuple(dc + u * 0.34 + Vector((0, 0.13, 0))), tuple(dc + u * L1 + Vector((0, 0.11, 0))), 0.04, 0.035), "Trim", hub)
    ring = xf(torus(1.05, 0.04, 0.0, 72, 6), Matrix.Rotation(math.radians(90), 3, "X"), tuple(dc + Vector((0, 0.11, 0))))
    P.part("RollDisk", ring, "Trim", hub)

    # ---- the carved wings of the winged sun of Behdet, spreading from the sides of the disk (static, no outline)
    wing = bmesh.new()
    def add(bm2):
        me = bpy.data.meshes.new("t"); bm2.to_mesh(me); wing.from_mesh(me); bpy.data.meshes.remove(me)
    tabw = {}
    yb = dc.y - 0.2
    for s in (1, -1):
        x0, x1 = 1.36, 2.4
        for row, (slot_, kL, n) in enumerate((("Accent", 1.0, 10), ("Glass", 0.62, 10), ("Trim", 0.32, 11))):
            for k in range(n):
                t = k / (n - 1); x = s * (x0 + (x1 - x0) * t)
                ztop = dc.z + 0.42 + 0.22 * t ** 1.5
                L = (0.92 - 0.55 * t) * kL
                d = Vector((s * (0.18 + 0.25 * t), 0, -1))
                f = cb_feather((x, yb + 0.03 * row, ztop), d, L, 0.15 - 0.03 * row)
                for fc in f.faces: tabw[cb_key(fc.calc_center_median())] = slot_ if row else ("Trim" if False else slot_)
                add(f)
                if row == 0:
                    tip = Vector((x, yb, ztop)) + d.normalized() * L
                    g = ball(tuple(tip + Vector((0, 0.01, 0))), (0.05, 0.03, 0.05), 6, 3)
                    for fc in g.faces: tabw[cb_key(fc.calc_center_median())] = "Trim"
                    add(g)
        bar_ = bar((s * x0, yb + 0.1, dc.z + 0.46), (s * (x1 + 0.05), yb + 0.1, dc.z + 0.7), 0.1, 0.08)
        for fc in bar_.faces: tabw[cb_key(fc.calc_center_median())] = "Trim"
        add(bar_)
    P.part("Cloth", wing, cb_paint(tabw, "Trim"), (0.0, 0.0, 0.0), 0, False)

    mz = pitch @ (hc + Vector((0, 0.44, -0.16)))
    P.part("Muzzle", ball(tuple(mz), (0.05, 0.03, 0.05), 8, 4), "Glow", tuple(mz))
    return P



# ================================================================= pyramid (2026-10-13 remake)
PY_A, PY_B = 1.75, 1.25        # the double pyramid: the height of each apex over the middle, half its base at the middle
PY_UP = [(0.5, 0.84), (0.95, 1.21), (1.32, 1.5)]          # the upper (limestone) slabs, bottom to top
PY_DN = [(-0.5, -0.84), (-0.95, -1.21), (-1.32, -1.5)]    # the lower (granite) slabs, top to bottom
PY_SPIN = {("U", 1), ("D", 0), ("D", 2)}                 # every other layer from the top turns: U2, D1, D3 (U3, U1, D2 stay)


def py_half(z):
    """half the double pyramid's width at height z."""
    return PY_B * max(0.0, 1.0 - abs(z) / PY_A)

def py_frustum(z0, z1, k=1.0, off=0.0):
    """the double pyramid's solid between heights z0 and z1 (k scales it, off pushes its sides out)."""
    return hull([(x * (py_half(z) * k + off), y * (py_half(z) * k + off), z) for z in (z0, z1) for x in (-1, 1) for y in (-1, 1)])

def py_side(side, u, z, out):
    """a point on face side (0 +Y, 1 +X, 2 -Y, 3 -X) at u along it, height z, out from it."""
    h = py_half(z) + out
    return Matrix.Rotation(-side * math.pi / 2, 3, "Z") @ Vector((u, h, z))


def D_pyramid():
    """The last boss, the SHATTERED SKY PYRAMID (2026-10-13, remade: "same as the alien bosses - realistic details, scarier, keep the
    cartoon shape"; then "the old design is better, I want something impressive and new - when people see it they say ahhhh"): the old
    double pyramid - an upright pyramid over an inverted one, a diamond floating in the sky - broken apart and held together by light. It
    is split into floating layers with gaps between them: above, three slabs of real stepped limestone, each laid in three courses of
    blocks with staggered joints, every course set back from the one below; below, three slabs of black polished granite, inverted, each
    edged with a gold band. Every gap blazes with a sheet of golden light, so the monument reads as a pyramid held up by light, and every
    slab carries a frieze of glowing hieroglyphs evenly round its band; the granite is crazed with glowing cracks, the same on all four
    faces. The layers turn against each other: every other one, counting from the top, turns slowly (SpinLayer0-2) while the others stay.
    In the middle the two widest layers part wide and show the core: a small sun blazing inside the pyramid, rays of light fanning out to
    the sides, and on its face the Eye of Horus - the white of the eye, the lapis lid lines running on to the side, the teardrop and the
    spiral - with a red-hot iris and a slit pupil staring at the player under a heavy brow; his shots leave from it. The gold capstone
    floats high over the top with a beam of light shooting up from its point, a thinner beam falls from the lower tip. To the left and
    right the two obelisks float upright, black granite banded in gold, a column of glowing glyphs down each, their tips burning; and
    round the lower half a ring of eight fragments orbits slowly (SpinDebris) - broken limestone blocks and the broken heads of sphinxes,
    their nemes headdresses striped in gold and lapis, one after the other."""
    P = Boss("pyramid", {"Base": ((0.86, 0.73, 0.50), 0.3), "Belly": ((0.97, 0.95, 0.88), 0.5), "Accent": LAPIS, "Trim": GOLD,
                         "Glass": ((0.80, 0.04, 0.02), 0.95), "Dark": ((0.05, 0.045, 0.06), 0.85), "Glow": ((1.0, 0.82, 0.42), 0.5),
                         "Metal": ((0.55, 0.45, 0.30), 0.3), "Lamp": ((1.0, 0.42, 0.06), 0.8)})

    def put(layer, bm, paint, smooth=False, hub_z=0.0):
        """into the static body, or into a turning layer (its hub on the vertical axis)."""
        if layer is None: P.obj("Stone", bm, paint, 0, smooth)
        else: P.part(layer, bm, paint, (0, 0, hub_z), 0, smooth)

    # ---- the upper slabs: stepped limestone, three courses of blocks each, a gold band with glowing glyphs at the foot
    for k, (z0, z1) in enumerate(PY_UP):
        layer = ("SpinLayer%d" % sum(1 for q in PY_SPIN if q < ("U", k))) if ("U", k) in PY_SPIN else None
        hz = (z0 + z1) * 0.5
        put(layer, py_frustum(z0 + 0.01, z1 - 0.01, 0.9), lambda c, n, k=k: "Glow" if (n.z < -0.5 and k == 0) else "Metal", False, hz)
        dz = (z1 - z0) / 3
        for j in range(3):
            c0 = z0 + j * dz; h = py_half(c0 + dz * 0.5) + 0.02; d = 0.15; L = 0.3
            band = j == 0
            for side in range(4):
                span = h if side % 2 == 0 else h - 2 * d
                n = max(2, round(2 * span / L)); off = 0.5 if (j + k) % 2 else 0.0
                cuts = sorted({-span, span} | {-span + (i + off) * 2 * span / n for i in range(1, n + 1) if -span < -span + (i + off) * 2 * span / n < span})
                for e0, e1 in zip(cuts, cuts[1:]):
                    mid, half = (e0 + e1) * 0.5, (e1 - e0) * 0.5 - 0.008
                    if half < 0.03: continue
                    rot = Matrix.Rotation(-side * math.pi / 2, 3, "Z")
                    bm = box((0, 0, 0), (half, d * 0.5 - 0.004, dz * 0.5 - 0.008))
                    xf(bm, rot, tuple(rot @ Vector((mid, h - d * 0.5, c0 + dz * 0.5))))
                    put(layer, bm, (lambda c, n, k=k: "Glow" if (n.z < -0.5 and k == 0) else "Trim") if band else
                        (lambda c, n, k=k: "Glow" if (n.z < -0.5 and k == 0) else "Base"), False, hz)
            if band:   # the glyph frieze on the gold band, evenly round all four sides
                for side in range(4):
                    m = max(3, round(2 * h / 0.2))
                    for i in range(m):
                        u = -h + 0.12 + (2 * h - 0.24) * i / (m - 1)
                        p = py_side(side, u, c0 + dz * 0.5, 0.002)
                        rot = Matrix.Rotation(-side * math.pi / 2, 3, "Z")
                        put(layer, xf(box((0, 0, 0), (0.035 if i % 2 else 0.022, 0.012, 0.04 if i % 3 else 0.028)), rot, tuple(p)), "Glow", False, hz)

    # ---- the lower slabs: inverted, black polished granite edged in gold, glyphs on the band, cracks of light on every face
    for k, (z0, z1) in enumerate(PY_DN):
        layer = ("SpinLayer%d" % sum(1 for q in PY_SPIN if q < ("D", k))) if ("D", k) in PY_SPIN else None
        hz = (z0 + z1) * 0.5
        put(layer, py_frustum(z0 - 0.06, z1), "Dark", False, hz)
        put(layer, py_frustum(z0, z0 - 0.07, 1.0, 0.025), lambda c, n: "Dark" if n.z > 0.5 else "Trim", False, hz)
        if k == 0:   # the top of the widest granite slab, under the sun: a sundial of gold rays inlaid in the black stone
            hw = py_half(z0) + 0.025
            for i in range(16):
                a = 2 * math.pi * i / 16; d = Vector((math.cos(a), math.sin(a), 0))
                L = min(hw / max(abs(d.x), abs(d.y)), 9.0) - 0.06
                put(layer, pipe([d * 0.56 + Vector((0, 0, z0 + 0.004)), d * L + Vector((0, 0, z0 + 0.004))], [0.018 if i % 2 == 0 else 0.011] * 2, 4), "Trim", False, hz)
            put(layer, torus(0.56, 0.02, z0 + 0.005, 48, 4), "Glow", False, hz)
            put(layer, torus(0.95, 0.014, z0 + 0.005, 56, 4), "Trim", False, hz)
        put(layer, py_frustum(z1 + 0.03, z1, 1.0, 0.015), "Trim", False, hz)
        h = py_half(z0 - 0.035) + 0.03
        for side in range(4):
            rot = Matrix.Rotation(-side * math.pi / 2, 3, "Z")
            m = max(3, round(2 * h / 0.2))
            for i in range(m):
                u = -h + 0.12 + (2 * h - 0.24) * i / (m - 1)
                put(layer, xf(box((0, 0, 0), (0.03 if i % 2 else 0.02, 0.012, 0.022)), rot, tuple(py_side(side, u, z0 - 0.035, 0.028))), "Glow", False, hz)
            # a crack of light across the face, forking, the same on each face
            zz = [z0 - 0.1, z0 - 0.17, z0 - 0.24, z1 + 0.06]
            uu = [-0.15, 0.02, -0.06, 0.08]
            cr = [py_side(side, u * py_half(z) / py_half(z0), z, 0.006) for u, z in zip(uu, zz)]
            put(layer, pipe(cr, [0.016, 0.014, 0.012, 0.0], 5), "Glow", False, hz)
            fk = cr[1].lerp(cr[2], 0.4)
            put(layer, pipe([fk, py_side(side, 0.22 * py_half(z0 - 0.3) / py_half(z0), z0 - 0.3, 0.006)], [0.011, 0.0], 5), "Glow", False, hz)

    # ---- sheets of golden light in the gaps between the layers
    for za, zb in ((PY_UP[0][1], PY_UP[1][0]), (PY_UP[1][1], PY_UP[2][0]), (PY_DN[0][1], PY_DN[1][0]), (PY_DN[1][1], PY_DN[2][0])):
        zm = (za + zb) * 0.5
        P.obj("LightSheet", py_frustum(zm - 0.008, zm + 0.008, 0.82), "Glow", 0, False)

    # ---- the core: a small sun inside the pyramid with the Eye of Horus on its face
    P.obj("Sun", ball((0, 0, 0), (0.47, 0.47, 0.47), 24, 12), "Lamp")
    for s in (1, -1):   # rays fanning out to the sides inside the hollow
        for i in range(5):
            a = math.radians(-32 + 16 * i); L = 0.95 if i % 2 == 0 else 0.78
            d = Vector((s * math.cos(a), 0, math.sin(a))); n_ = Vector((0, 1, 0)); w = d.cross(n_).normalized()
            P.obj("Ray", hull([tuple(d * 0.42 + w * 0.07 + n_ * t) for t in (-0.02, 0.02)] + [tuple(d * 0.42 - w * 0.07 + n_ * t) for t in (-0.02, 0.02)] +
                               [tuple(d * L + n_ * t) for t in (-0.01, 0.01)]), "Glow", 0, False)
    def E(u, v, out=0.0):
        """a point on the sun's face toward the player (the eye drawn 1.2 times larger)."""
        u, v = u * 1.2, v * 1.2
        y = math.sqrt(max(0.0, 0.47 ** 2 - u * u - v * v))
        return Vector((u, y + out, v))
    upper = [E(-0.3 + 0.56 * i / 12, 0.11 * math.sin(math.pi * i / 12), 0.03) for i in range(13)]
    lower = [E(-0.3 + 0.56 * i / 12, -0.07 * math.sin(math.pi * i / 12), 0.03) for i in range(13)]
    P.obj("EyeWhite", hull([tuple(E(-0.3 + 0.56 * i / 12, f * math.sin(math.pi * i / 12), o)) for i in range(13) for f in (0.11, -0.07) for o in (0.0, 0.025)]), "Belly", 0, False)
    P.obj("Iris", ball(tuple(E(-0.02, 0.01, 0.03)), (0.075, 0.035, 0.075), 14, 7), "Glass")
    P.obj("Pupil", ball(tuple(E(-0.02, 0.01, 0.06)), (0.017, 0.02, 0.06), 8, 4), "Dark")
    P.obj("EyeLine", pipe(upper + [E(0.33, -0.01, 0.03), E(0.37, -0.02, 0.02)], [0.024] * 15, 6), "Accent", 0, False)
    P.obj("EyeLine", pipe(lower, [0.02] * 13, 6), "Accent", 0, False)
    P.obj("Brow", pipe([E(-0.32, 0.1, 0.03), E(-0.1, 0.19, 0.03), E(0.16, 0.22, 0.03), E(0.34, 0.18, 0.02)], [0.03, 0.034, 0.03, 0.022], 6), "Accent", 0, False)
    P.obj("Teardrop", pipe([E(0.0, -0.08, 0.03), E(0.01, -0.18, 0.03), E(0.03, -0.27, 0.025)], [0.022, 0.022, 0.018], 6), "Accent", 0, False)
    spiral = [E(-0.13, -0.07, 0.03)] + [E(-0.17 + 0.06 * math.cos(a) - 0.06 * (1 - i / 14), -0.22 + 0.06 * math.sin(a) * (1 - i / 20), 0.03) for i, a in
                                         enumerate([math.pi * 0.5 + 1.6 * math.pi * i / 14 for i in range(15)])]
    P.obj("Spiral", pipe(spiral, [0.02] * len(spiral), 6), "Accent", 0, False)

    # ---- the floating capstone with its beam, the lower tip with its thinner one
    ct0, ct1 = 1.66, 2.02; ch = 0.3
    P.obj("Pyramidion", hull([(x * ch, y * ch, ct0) for x in (-1, 1) for y in (-1, 1)] + [(0, 0, ct1)]), "Trim", 0, False)
    P.obj("CapBand", hull([(x * (ch + 0.02), y * (ch + 0.02), z) for x in (-1, 1) for y in (-1, 1) for z in (ct0 - 0.03, ct0 + 0.03)]), "Accent", 0, False)
    P.obj("CapGlyph", hull([(x * (ch * 0.4), ch * 0.62 + 0.012, z) for x in (-1, 1) for z in (ct0 + 0.08, ct0 + 0.14)] + [(0, ch * 0.4 + 0.012, ct0 + 0.2)]), "Glow", 0, False)
    P.obj("ClothBeamUp", pipe([(0, 0, ct1), (0, 0, ct1 + 0.25), (0, 0, ct1 + 0.7)], [0.07, 0.045, 0.0], 10), "Glow", 0, False)
    lt0, lt1 = -1.6, -1.86
    P.obj("LowerTip", hull([(x * py_half(lt0), y * py_half(lt0), lt0) for x in (-1, 1) for y in (-1, 1)] + [(0, 0, lt1)]), "Dark", 0, False)
    P.obj("LowerTipBand", py_frustum(lt0 + 0.02, lt0 - 0.03, 1.0, 0.015), "Trim", 0, False)
    P.obj("ClothBeamDown", pipe([(0, 0, lt1), (0, 0, lt1 - 0.2), (0, 0, lt1 - 0.5)], [0.04, 0.025, 0.0], 8), "Glow", 0, False)
    P.obj("ClothThread", pipe([(0, 0, PY_UP[2][1]), (0, 0, ct0)], [0.025, 0.025], 6), "Glow", 0, False)

    # ---- the two obelisks floating upright left and right
    for s in (1, -1):
        c = Vector((s * 1.95, 0.05, 0.0)); zb, zt = -1.0, 0.95
        P.obj("Obelisk", hull([(c.x + x, c.y + y, zb) for x in (-0.14, 0.14) for y in (-0.14, 0.14)] + [(c.x + x, c.y + y, zt) for x in (-0.09, 0.09) for y in (-0.09, 0.09)]), "Dark", 0, False)
        P.obj("ObeliskTip", hull([(c.x + x, c.y + y, zt) for x in (-0.09, 0.09) for y in (-0.09, 0.09)] + [(c.x, c.y, zt + 0.2)]), "Glow", 0, False)
        for z in (zt - 0.04, zb + 0.06):
            hw = 0.14 - 0.05 * (z - zb) / (zt - zb) + 0.015
            P.obj("ObeliskBand", box((c.x, c.y, z), (hw, hw, 0.03)), "Trim", 0, False)
        P.obj("ObeliskFoot", hull([(c.x + x, c.y + y, zb) for x in (-0.14, 0.14) for y in (-0.14, 0.14)] + [(c.x, c.y, zb - 0.18)]), "Trim", 0, False)
        for i in range(7):   # a column of glowing glyphs down the face toward the player and the inner face
            z = zb + 0.22 + 0.22 * i; hw = 0.14 - 0.05 * (z - zb) / (zt - zb)
            P.obj("ObeliskGlyph", box((c.x, c.y + hw + 0.004, z), (0.045 if i % 2 else 0.03, 0.008, 0.05 if i % 3 else 0.035)), "Glow", 0, False)
            P.obj("ObeliskGlyph", box((c.x - s * (hw + 0.004), c.y, z), (0.008, 0.045 if i % 2 == 0 else 0.03, 0.05 if i % 3 else 0.035)), "Glow", 0, False)

    # ---- a ring of eight fragments orbiting the lower half: broken blocks and broken sphinx heads, one after the other
    rz, R = -1.0, 1.62
    for i in range(8):
        a = 2 * math.pi * (i + 0.5) / 8; o = Vector((math.cos(a), math.sin(a), 0)); c = Vector((0, 0, rz)) + o * R
        rot = Matrix.Rotation(a - math.pi / 2, 3, "Z")   # local +Y faces outward
        def dpart(bm, paint, c=c): P.part("SpinDebris", grow(bm, c, 1.5), paint, (0, 0, rz), 0, False)
        if i % 2 == 0:
            # a broken limestone block: a cube with two corners knocked off, a chipped top
            pts = [Vector((x * 0.16, y * 0.13, z * 0.12)) for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)]
            pts = [p for j, p in enumerate(pts) if j not in (7 - (i // 2) % 4, (i // 2 + 2) % 8)] + [Vector((0.16, 0.13, 0.03)), Vector((-0.05, -0.13, 0.12)), Vector((0.16, -0.02, 0.12))]
            dpart(hull([tuple(c + rot @ p) for p in pts]), "Base")
            dpart(xf(box((0, 0, 0), (0.05, 0.006, 0.04)), rot, tuple(c + rot @ Vector((0, 0.134, 0)))), "Glow")
        else:
            # a sphinx's head broken off at the neck: the face, the nemes headdress striped gold and lapis, the uraeus on the brow
            dpart(xf(ball((0, 0, 0), (0.1, 0.1, 0.12), 12, 6), rot, tuple(c + rot @ Vector((0, 0.04, 0.02)))), "Base")
            nem = hull([Vector(p) for p in [(-0.16, -0.06, -0.14), (0.16, -0.06, -0.14), (-0.13, 0.04, -0.14), (0.13, 0.04, -0.14),
                                               (-0.12, -0.08, 0.12), (0.12, -0.08, 0.12), (-0.08, 0.02, 0.16), (0.08, 0.02, 0.16), (0, -0.04, 0.19)]])
            dpart(xf(nem, rot, tuple(c)), lambda q, n, c=c: "Trim" if int((q.z - c.z + 0.2) / 0.05) % 2 else "Accent")
            dpart(xf(box((0, 0, 0), (0.045, 0.02, 0.025)), rot, tuple(c + rot @ Vector((0, 0.12, 0.06)))), "Dark")   # eyes in shadow
            dpart(xf(ball((0, 0, 0), (0.025, 0.02, 0.04), 6, 3), rot, tuple(c + rot @ Vector((0, 0.09, 0.15)))), "Trim")
            dpart(xf(box((0, 0, 0), (0.08, 0.06, 0.012)), rot, tuple(c + rot @ Vector((0, 0.0, -0.15)))), "Metal")   # the break

    mz = E(-0.02, 0.01, 0.09)
    P.part("Muzzle", ball(tuple(mz), (0.05, 0.03, 0.05), 8, 4), "Lamp", tuple(mz))
    return P


BOSSES = [("carpet", D_carpet), ("anubis", D_anubis), ("sphinx", D_sphinx), ("pyramid", D_pyramid),
          ("cobra", D_cobra)]

if __name__ == "__main__":
    os.makedirs(AB.OUT, exist_ok=True)
    for bid, fn in BOSSES:
        if ONLY and bid not in ONLY: continue
        fn().finish()
    print("DONE")
