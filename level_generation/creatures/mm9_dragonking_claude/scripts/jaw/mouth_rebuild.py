"""Real mouth cavity for the Dragon King (2026-10-30 rework, replaces reweight_mouth.py + mouth_uv.py).

Args: -- <in blend (uv_v2f)> <out blend> <report json>

Why: Meshy modelled a short open mouth (a side slot ~0.15 tall from the snout tip back to y -4.1 with the teeth in
it, a shallow palate/floor and a small pocket to y -3.77), while the MM9 jaw hinges at y -3.1. The old split plane
(reweight_mouth.py) ran ~0.3 above the real slot, through the eyes, so the upper lip, upper teeth and half of each eye
moved with the jaw and the lip band stretched into a red curtain over a hollow head.

What:
1. The tongue part (Meshy's loose tongue inside the closed pocket) is removed; the new floor carries a tongue shape.
2. A cutter volume is built station by station along the snout: a lens whose top is the palate (a vault above the
   mouth line), whose bottom is the floor (sulci beside a raised tongue), meeting outside the skin. In front of the
   Meshy corner its slit at the skin is Meshy's own slot (teeth stay seated in their lips); behind the corner the
   slit narrows to RIP_SLIT at RIP_END (in front of the hinge), so the mouth now opens back to the MM9 corner; behind
   RIP_END the cutter stays inside the head and becomes the throat, descending toward the neck and closing.
   Its faces carry their own UVs (palate and floor sheets in the head set's top strip, isotropic MOUTH_UV_SCALE)
   and materials MouthPalate / MouthFloor, transferred by the Boolean.
3. Exact Boolean difference of the cutter from the head part of the main shell (separated, then re-joined; teeth,
   eyes and the rest untouched).
4. Weights: every snout vertex in front of RIP_END is upper (skull) or lower (jaw) by connectivity from a seed on
   the snout top / chin (the cut separates them); behind RIP_END a band around the mouth line blends (cheeks,
   throat) and the throat's jaw share fades out toward the hinge (points behind the pivot would rise into the
   palate). Values: the nearest MM9 vertex label of that side (as reweight_mouth.py). Teeth and eyes are rigid:
   each tooth takes the weights of the gum vertex nearest its root (upper tooth: its top; lower: its bottom), each
   eye those of the nearest skull vertex.
Face attribute 'mouth' (1 palate, 2 floor) marks the cavity; 'tooth' marks teeth (seat/clearance check).
"""
import bpy, bmesh, sys, os, json, math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mouth_common as M

argv = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, REP = argv[:3]

Y_FRONT = -5.36          # cutter front (in front of the snout tip)
Y_CORNER = -4.10         # Meshy's mouth corner (end of its side slot)
RIP_END = -3.40          # new mouth corner (the MM9 hinge is at y -3.105)
Y_THROAT = -2.85         # throat end inside the head
CLEAR_TOP, CLEAR_BOT = 0.06, 0.05
RIP_SLIT = 0.022         # slit height at the skin at RIP_END
SLIT_INSET = 0.04
CORNER_RAMP = float(os.environ.get('DK_CORNER_RAMP', '0.45'))
NS = 24                  # stations
MOUTH_UV_SCALE = 0.18    # UV units per model unit (palate u 0.01.., floor u 0.51.., v around 0.90)
LOWER_TIP_Y = -4.97      # front of the lower jaw
SNOUT_BOX = ((-0.8, 0.8), (-5.5, -2.45), (14.35, 15.75))   # the snout (stray-face pass)
SEP_Y = float(os.environ.get('DK_SEP_Y', '-2.3'))           # shell faces in front of this go to the Boolean
USE_SELF = os.environ.get('DK_USE_SELF', '0') == '1'

bpy.ops.wm.open_mainfile(filepath=IN)
sc = bpy.context.scene
rig = bpy.data.objects['MM9_Rig']
body = bpy.data.objects['Body']
me = body.data
HINGE = Vector(rig.data.bones['Xjawpivot'].head_local)
rep = {'hinge': list(HINGE)}

# ---------------------------------------------------------------- parts, roles, tongue removal
bm = bmesh.new(); bm.from_mesh(me)
comp = M.parts(bm); R = M.roles(bm, comp)
rep['roles'] = {k: v for k, v in R.items()}
CO = np.array([tuple(v.co) for v in bm.verts])
shell_polys = [[v.index for v in f.verts] for f in bm.faces if comp[f.verts[0].index] == R['shell']]
SHELL = BVHTree.FromPolygons([tuple(v.co) for v in bm.verts], shell_polys, all_triangles=True)
teeth_info = []
for k in R['teeth']:
    P = CO[comp == k]
    teeth_info.append((k, P.mean(0), P.min(0), P.max(0)))
if R['tongue'] is not None:
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if comp[f.verts[0].index] == R['tongue']], context='FACES')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    bm.to_mesh(me)
rep['tongue_removed'] = R['tongue'] is not None
bm.free()


def ray_first(o, d, dist=10):
    h = SHELL.ray_cast(Vector(o), Vector(d), dist)
    return h[0]


def open_runs(y, sgn=1):
    zs = np.round(np.arange(14.6, 15.6, 0.01), 3); op = []
    for z in zs:
        o = Vector((0, y, z)); d = Vector((sgn, 0, 0)); hit = False
        while True:
            h = SHELL.ray_cast(o, d, 3)
            if h[0] is None:
                break
            hit = True; o = h[0] + d * 1e-4
        if not hit:
            op.append(z)
    op = np.array(op)
    if not len(op):
        return []
    br = np.where(np.diff(op) > 0.015)[0]
    return [(op[a], op[b]) for a, b in zip(np.r_[0, br + 1], np.r_[br, len(op) - 1])]


# ---------------------------------------------------------------- mouth line from Meshy's slot (front), then to RIP_END
def m_guess(y):
    return 14.90 + 0.19 * (y + 4.95)


slot = []
for y in np.arange(-4.95, Y_CORNER + 0.001, 0.05):
    best = None
    for a_, b_ in open_runs(y, 1):
        if a_ - 0.02 <= m_guess(y) <= b_ + 0.02 and b_ - a_ < 0.4:
            best = (a_, b_)
    if best:
        slot.append((y, best[0], best[1]))
slot = np.array(slot)
fit_m = np.polyfit(slot[:, 0], (slot[:, 1] + slot[:, 2]) / 2, 1)
fit_s = np.polyfit(slot[:, 0], slot[:, 2] - slot[:, 1], 1)
M_CORNER = float(np.polyval(fit_m, Y_CORNER))
M_END = M_CORNER + 0.07 * (RIP_END - Y_CORNER)       # toward the hinge (z 15.14 at y -3.1)
rep['slot_fit'] = {'m': fit_m.round(4).tolist(), 'height': fit_s.round(4).tolist(), 'samples': len(slot),
                   'm_corner': round(M_CORNER, 3), 'm_end': round(M_END, 3)}


def mline(y):
    if y <= Y_CORNER:
        return float(np.polyval(fit_m, y))
    if y <= RIP_END:
        return M_CORNER + (M_END - M_CORNER) * (y - Y_CORNER) / (RIP_END - Y_CORNER)
    t = (y - RIP_END) / (Y_THROAT - RIP_END)
    return M_END - 0.12 * t ** 1.5                 # the throat turns down toward the neck


def slit(y):
    """Cutter height at the skin (the lips' gap in bind)."""
    # 0.04 shorter than Meshy's slot: in front of the corner the cutter stays inside the open slot (never coplanar
    # with Meshy's lip faces), behind it it cuts the corner wall and the cheek transversally
    s_c = float(np.polyval(fit_s, Y_CORNER)) - SLIT_INSET
    if y <= Y_CORNER:
        return max(float(np.polyval(fit_s, y)) - SLIT_INSET, s_c)
    return s_c + (RIP_SLIT - s_c) * min(1.0, (y - Y_CORNER) / (RIP_END - Y_CORNER))


# tooth row (|x| of tooth centroids against y), gum line just inside it
tc = np.array([t[1] for t in teeth_info])
fit_t = np.polyfit(tc[:, 1], np.abs(tc[:, 0]), 1)
rep['tooth_row_fit'] = fit_t.round(4).tolist()


def skin_hw(y, z):
    h = ray_first((3, y, z), (-1, 0, 0))
    return abs(h.x) if h is not None and h.x > 0 else None


def skin_top(y):
    h = ray_first((0, y, 18), (0, 0, -1)); return h.z if h else None


def skin_bottom(y):
    h = ray_first((0, y, 13.5), (0, 0, 1)); return h.z if h else None


# ---------------------------------------------------------------- cutter
ys = np.linspace(Y_FRONT, Y_THROAT, NS)
UNIT = np.array([0.0, 0.35, 0.65, 0.88, 1.0])     # fractions of the gum line xg (inside the mouth)
rings, ring_kind = [], []
st_rows = []
prev_hw = 0.2
for y in ys:
    m = mline(y)
    top = skin_top(y) or (m + 0.2); bot = skin_bottom(y) or (m - 0.2)
    s = slit(y)
    hws = [h for h in (skin_hw(y, m), skin_hw(y, m + s / 2 + 0.03), skin_hw(y, m - s / 2 - 0.03)) if h]
    hw = max(hws) if hws else min(prev_hw, 0.08)
    prev_hw = hw
    s = slit(y)
    front = np.clip((y - (-5.02)) / 0.30, 0, 1)        # vault/floor depth ramps in behind the snout tip
    if y <= RIP_END:
        xt = float(np.polyval(fit_t, min(y, -4.2))) if y < Y_CORNER + 0.05 else 0.0
        xg = max(0.02, min(xt - 0.035, hw - 0.06)) if y < Y_CORNER + 0.05 else max(0.05, 0.72 * hw)
        if y > Y_CORNER:                               # behind Meshy's corner: gum line follows the skin
            xg = max(0.05, 0.72 * hw)
        xs = hw
        W = hw + 0.12
        hp = min(0.55 * (top - m), 0.36) * (0.25 + 0.75 * front)
        hf = min(0.55 * (m - bot), 0.24) * (0.25 + 0.75 * front) if y > LOWER_TIP_Y else s / 2
        k = 1.0
    else:
        t = (y - RIP_END) / (Y_THROAT - RIP_END)
        k = math.sqrt(max(0.0, 1 - t ** 2.2))          # rounded throat end
        k = max(k, 0.0)
        xg = max(0.012, 0.72 * hw * (1 - 0.45 * t) * k)
        xs = W = xg
        hp = min(0.55 * (top - m), 0.36) * max(k, 0.02)
        hf = min(0.55 * (m - bot), 0.24) * max(k, 0.02)
    hp = max(hp, s / 2 + 0.03); hf = max(hf, s / 2 + 0.03) if y > LOWER_TIP_Y else max(hf, s / 2)
    st_rows.append(dict(y=round(float(y), 3), m=round(m, 3), hw=round(hw, 3), xg=round(xg, 3), W=round(W, 3),
                        hp=round(hp, 3), hf=round(hf, 3), slit=round(s, 3)))
    # column x positions (one side, from the centre out)
    if y <= RIP_END:
        xcol = list(UNIT * xg) + [xg + 0.5 * (xs - xg), xs, W]
    else:
        xcol = list(np.array([0.0, 0.3, 0.55, 0.72, 0.84, 0.92, 0.97, 1.0]) * xg)   # same column count, all inside
    tongue = np.clip((y - (-4.80)) / 0.25, 0, 1) if y <= RIP_END else max(0.0, 1 - (y - RIP_END) / 0.4)

    def Tz(x):
        ax = abs(x)
        if ax <= xg:
            u = ax / max(xg, 1e-6)
            return m + s / 2 + (hp - s / 2) * math.cos(u * math.pi / 2) ** 0.9 * (1 - 0.25 * u)
        if ax <= xs:
            return m + s / 2
        return m + s / 2 * (1 - (ax - xs) / max(W - xs, 1e-6))

    def Bz(x):
        ax = abs(x)
        if ax <= xg:
            u = ax / max(xg, 1e-6)
            plain = math.cos(u * math.pi / 2) ** 0.9                      # a plain trough
            # tongue: raised centre (0.5 depth), deepest sulcus at u ~ 0.8, then up to the gum
            tg = (0.25 + 0.75 * (u / 0.8) ** 2) if u <= 0.8 else (1.0 - (u - 0.8) / 0.2) * 1.0
            prof = (1 - tongue) * plain + tongue * tg
            if u > 0.8:
                prof = (1 - tongue) * plain + tongue * max(0.0, (1 - (u - 0.8) / 0.2))
            return m - s / 2 - (hf - s / 2) * prof
        if ax <= xs:
            return m - s / 2
        return m - s / 2 * (1 - (ax - xs) / max(W - xs, 1e-6))

    xs_full = [-x for x in reversed(xcol[1:])] + xcol            # -W .. W

    def clamp(x, zt, zb):
        # stay inside the skin: palate CLEAR_TOP under the skull's outer surface, floor CLEAR_BOT over the jaw's
        # underside at the same (x, y) (the lower jaw is thin and round: deep sulci would cut through the chin)
        if abs(x) >= xs - 1e-6:
            return zt, zb
        ht = ray_first((x, y, 18), (0, 0, -1)); hb = ray_first((x, y, 13.0), (0, 0, 1))
        if ht is not None and ht.z > m:
            zt = min(zt, max(ht.z - CLEAR_TOP, m + s / 2))
        if hb is not None and hb.z < m and y > LOWER_TIP_Y:
            zb = max(zb, min(hb.z + CLEAR_BOT, m - s / 2))
        return zt, zb
    TB = [clamp(x, Tz(x), Bz(x)) for x in xs_full]
    top_pts = [(x, y, TB[k][0]) for k, x in enumerate(xs_full)]
    bot_pts = [(x, y, TB[k][1]) for k, x in reversed(list(enumerate(xs_full))[1:-1])]   # W .. -W without the shared ends
    if y > RIP_END:   # inside the head: make the lens ends round instead of knife edges
        top_pts[0] = (xs_full[0], y, m); top_pts[-1] = (xs_full[-1], y, m)
    rings.append(top_pts + bot_pts)
    ring_kind.append(len(top_pts))
rep['stations'] = st_rows

cb = bmesh.new()
uvl = cb.loops.layers.uv.new('UVMap')
mat_l = None
V = [[cb.verts.new(p) for p in r] for r in rings]
NT = ring_kind[0]; N = len(rings[0])


def arc_along():
    c = np.array([[0, y_, mline(y_)] for y_ in ys]); d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(c, axis=0), axis=1))]
    return d


ALONG = arc_along()


def across(ring, idx_list):
    pts = np.array([ring[i] for i in idx_list]); d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(pts[:, [0, 2]], axis=0), axis=1))]
    mid = d[len(d) // 2] if len(d) % 2 else d[len(d) // 2]
    return d - mid


faces_meta = []
for i in range(NS - 1):
    for j in range(N):
        a, b = j, (j + 1) % N
        f = cb.faces.new([V[i][a], V[i][b], V[i + 1][b], V[i + 1][a]])
        upper = (j < NT - 1)
        f.material_index = 0 if upper else 1
        faces_meta.append((f, i, a, b, upper))
# caps (fans)
for i, flip in ((0, True), (NS - 1, False)):
    c = cb.verts.new(tuple(np.mean([v.co for v in V[i]], axis=0)))
    for j in range(N):
        a, b = V[i][j], V[i][(j + 1) % N]
        f = cb.faces.new([a, c, b] if flip else [a, b, c])
        f.material_index = 0 if j < NT - 1 else 1
        for lp in f.loops:
            lp[uvl].uv = (0.005 if i == 0 else 0.48, 0.90) if j < NT - 1 else (0.515 if i == 0 else 0.98, 0.90)
# UVs on the side faces: u = along (arc of the mouth line), v = across (arc from the centre column)
ACR_T = [across(rings[i], list(range(NT))) for i in range(NS)]
ACR_B = [across(rings[i], [NT - 1] + list(range(NT, N)) + [0]) for i in range(NS)]


def uv_of(i, j, upper):
    s_ = MOUTH_UV_SCALE
    if upper:
        a_ = ACR_T[i][j] if j < NT else 0.0
        return (0.01 + s_ * ALONG[i], 0.90 + np.clip(s_ * a_, -0.094, 0.094))
    # bottom ring index j: NT-1 (right end), NT.., 0 (left end): position in ACR_B
    pos = 0 if j == NT - 1 else (len(ACR_B[i]) - 1 if j == 0 else j - NT + 1)
    a_ = -ACR_B[i][pos]
    return (0.51 + s_ * ALONG[i], 0.90 + np.clip(s_ * a_, -0.094, 0.094))


for f, i, a, b, upper in faces_meta:
    for lp, (ii, jj) in zip(f.loops, ((i, a), (i, b), (i + 1, b), (i + 1, a))):
        lp[uvl].uv = uv_of(ii, jj, upper)
bmesh.ops.recalc_face_normals(cb, faces=cb.faces)
cm = bpy.data.meshes.new('MouthCutter'); cb.to_mesh(cm); cb.free()
for nm in ('MouthPalate', 'MouthFloor'):
    mt = bpy.data.materials.get(nm) or bpy.data.materials.new(nm)
    cm.materials.append(mt)
cutter = bpy.data.objects.new('MouthCutter', cm); sc.collection.objects.link(cutter)
cutter.matrix_world = body.matrix_world.copy()

# ---------------------------------------------------------------- separate the head of the main shell, Boolean
for o in bpy.data.objects:
    o.select_set(False)
bpy.context.view_layer.objects.active = body
body.select_set(True)
# body materials: make sure slots exist so the transfer keeps indices sane
if not me.materials:
    me.materials.append(bpy.data.materials.get('BodySkin') or bpy.data.materials.new('BodySkin'))
bpy.ops.object.mode_set(mode='EDIT')
bmE = bmesh.from_edit_mesh(me); bmE.verts.ensure_lookup_table()
compE = M.parts(bmE)
for f in bmE.faces:
    f.select = bool(compE[f.verts[0].index] == R['shell'] and all(v.co.y < SEP_Y for v in f.verts))
bmesh.update_edit_mesh(me)
bpy.ops.mesh.separate(type='SELECTED')
bpy.ops.object.mode_set(mode='OBJECT')
head = [o for o in bpy.context.selected_objects if o != body][0]
head.name = 'HeadShell'
nf_before = len(head.data.polygons)
mod = head.modifiers.new('cut', 'BOOLEAN')
mod.operation = 'DIFFERENCE'; mod.solver = 'EXACT'; mod.object = cutter
mod.use_hole_tolerant = True; mod.use_self = USE_SELF
try:
    mod.material_mode = 'TRANSFER'
except Exception:
    pass
bpy.context.view_layer.objects.active = head
for o in bpy.data.objects:
    o.select_set(o == head)
bpy.ops.object.modifier_apply(modifier='cut')
rep['boolean'] = {'head_faces_before': nf_before, 'after': len(head.data.polygons)}
cutter.hide_render = True; cutter.hide_set(True)
# triangulate the new ngons, join back, weld the separation seam
for o in bpy.data.objects:
    o.select_set(o == head)
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')
bpy.ops.object.mode_set(mode='OBJECT')
mats_head = [m.name if m else '' for m in head.data.materials]
rep['head_materials'] = mats_head
for o in bpy.data.objects:
    o.select_set(o in (body, head))
bpy.context.view_layer.objects.active = body
bpy.ops.object.join()
me = body.data
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
seam = [v for v in bm.verts if v.is_boundary]
bmesh.ops.remove_doubles(bm, verts=seam, dist=1e-5)
# mouth face attribute from the transferred materials
mnames = [m.name if m else '' for m in me.materials]
mouth_l = bm.faces.layers.int.new('mouth')
kept_l = bm.faces.layers.int.new('kept')
n_mouth = [0, 0]
for f in bm.faces:
    nm = mnames[f.material_index] if f.material_index < len(mnames) else ''
    if nm.startswith('MouthPalate'):
        f[mouth_l] = 1; n_mouth[0] += 1
    elif nm.startswith('MouthFloor'):
        f[mouth_l] = 2; n_mouth[1] += 1
    f.material_index = 0
# faces the exact solver kept inside the cutter (Meshy's self-intersecting corner wall): ray parity on two axes
cbm = bmesh.new(); cbm.from_mesh(cutter.data); CUT = BVHTree.FromBMesh(cbm); cbm.free()


def inside_cutter(p):
    votes = 0
    for d in (Vector((0.013, 0.007, 1)).normalized(), Vector((1, 0.011, 0.017)).normalized(), Vector((0.009, -1, 0.021)).normalized()):
        o = p.copy(); n = 0
        while True:
            h = CUT.ray_cast(o, d, 20)
            if h[0] is None: break
            n += 1; o = h[0] + d * 1e-6
        votes += n % 2
    return votes >= 2


bm.faces.index_update()
compS = M.parts(bm); shellS = int(np.bincount(compS).argmax())
stray = [f for f in bm.faces if not f[mouth_l] and compS[f.verts[0].index] == shellS and M.in_box(f.calc_center_median(), SNOUT_BOX)
         and inside_cutter(f.calc_center_median())]
rep['meshy_interior_faces_kept_as_mouth'] = len(stray)
rep['snout_boundary_edges_before_stray'] = sum(1 for e in bm.edges if e.is_boundary and all(M.in_box(v.co, SNOUT_BOX) for v in e.verts))
# Deleting them would open holes (the solver added no cutter faces there), so they become cavity tissue: mouth
# palate/floor by their side of the mouth line, UVs projected onto the same sheets (u along, v across ~ x).
uvl_b = bm.loops.layers.uv['UVMap']
edge_arc = {round(float(y_), 4): (ACR_T[i][-1], st_rows[i]['W']) for i, y_ in enumerate(ys)}
for f in stray:
    f[kept_l] = 1
    c = f.calc_center_median()
    up_ = c.z > mline(c.y)
    f[mouth_l] = 1 if up_ else 2
    for lp in f.loops:
        q = lp.vert.co
        along = float(np.interp(q.y, ys, ALONG))
        i_ = int(np.clip(np.searchsorted(ys, q.y), 0, NS - 1))
        arc_edge, Wst = ACR_T[i_][-1], st_rows[i_]['W']
        acr = np.sign(q.x) * min(abs(q.x) / max(Wst, 1e-3), 1.0) * arc_edge
        u0 = 0.01 if up_ else 0.51
        lp[uvl_b].uv = (u0 + MOUTH_UV_SCALE * along, 0.90 + float(np.clip(MOUTH_UV_SCALE * (acr if up_ else -acr), -0.094, 0.094)))
rep['snout_boundary_edges_after_stray'] = sum(1 for e in bm.edges if e.is_boundary and all(M.in_box(v.co, SNOUT_BOX) for v in e.verts))
rep['snout_boundary_sample'] = [[round(c, 3) for c in (e.verts[0].co + e.verts[1].co) / 2] + [int(any(f[mouth_l] for f in e.link_faces))] for e in bm.edges if e.is_boundary and all(M.in_box(v.co, SNOUT_BOX) for v in e.verts)]
# remove degenerate slivers from the cut
bmesh.ops.dissolve_degenerate(bm, dist=2e-4, edges=[e for e in bm.edges if all(M.in_box(v.co) for v in e.verts)])
bm.to_mesh(me); bm.free()
while len(me.materials) > 1:
    me.materials.pop(index=len(me.materials) - 1)
rep['mouth_faces'] = {'palate': n_mouth[0], 'floor': n_mouth[1]}

# ---------------------------------------------------------------- weights
UPPER, LOWER = M.UPPER, M.LOWER
mp, ml = [], []
for o in bpy.data.objects:
    if o.type != 'MESH' or not o.name.endswith('.mesh') or o.name.startswith('MM9Posed'):
        continue
    for v in o.data.vertices:
        n = o.vertex_groups[max(v.groups, key=lambda g: g.weight).group].name
        if n in UPPER or n in LOWER:
            mp.append(tuple(o.matrix_world @ v.co)); ml.append(n)
MP = np.array(mp); ML = np.array(ml)
lowmask = np.isin(ML, list(LOWER))
kU = KDTree(int((~lowmask).sum())); kL = KDTree(int(lowmask.sum()))
iu = np.nonzero(~lowmask)[0]; il = np.nonzero(lowmask)[0]
for j, i in enumerate(iu):
    kU.insert(Vector(MP[i]), j)
for j, i in enumerate(il):
    kL.insert(Vector(MP[i]), j)
kU.balance(); kL.balance()
for n in UPPER | LOWER:
    if n not in body.vertex_groups:
        body.vertex_groups.new(name=n)
gi = {g.name: g.index for g in body.vertex_groups}
vgname = {g.index: g.name for g in body.vertex_groups}

bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
comp = M.parts(bm)
mouth_l = bm.faces.layers.int['mouth']
mouth_v = np.zeros(len(bm.verts), np.int8)
for f in bm.faces:
    if f[mouth_l]:
        for v in f.verts:
            mouth_v[v.index] = f[mouth_l]
CO = np.array([tuple(v.co) for v in bm.verts])
shell_id = np.bincount(comp).argmax()


def headw(v):
    return sum(g.weight for g in v.groups if vgname[g.group] in UPPER | LOWER)


dv = me.vertices
zone = np.array([bool(mouth_v[i]) or (comp[i] == shell_id and CO[i, 1] < HINGE.y + 0.15 and CO[i, 2] > 14.3 and
                  (headw(dv[i]) >= 0.5 or not dv[i].groups)) for i in range(len(dv))])
# connectivity split in front of RIP_END
front = zone & (CO[:, 1] < RIP_END - 0.12)   # the cutter's lens tips go inside the skin just before RIP_END


def flood(seed):
    lab = np.zeros(len(CO), bool); st = [seed]; lab[seed] = True
    while st:
        x = bm.verts[st.pop()]
        for e in x.link_edges:
            y = e.other_vert(x).index
            if not lab[y] and front[y]:
                lab[y] = True; st.append(y)
    return lab


fi = np.nonzero(front)[0]
seed_up = fi[np.argmax(CO[fi, 2] - 2.0 * np.abs(CO[fi, 0]) + 0.3 * (CO[fi, 1] < -4.4))]
seed_lo = fi[np.argmin(CO[fi, 2] + 2.0 * np.abs(CO[fi, 0]) - 0.0)]
up_lab = flood(seed_up); lo_lab = flood(seed_lo)
leak = int((up_lab & lo_lab).sum())
if (up_lab & lo_lab).any():
    import heapq
    dist = {int(seed_up): 0.0}; prv = {}; pq = [(0.0, int(seed_up))]
    while pq:
        d_, u_ = heapq.heappop(pq)
        if u_ == int(seed_lo): break
        for e in bm.verts[u_].link_edges:
            w_ = e.other_vert(bm.verts[u_]).index
            if front[w_] and d_ + e.calc_length() < dist.get(w_, 1e9):
                dist[w_] = d_ + e.calc_length(); prv[w_] = u_; heapq.heappush(pq, (dist[w_], w_))
    pth = [int(seed_lo)]
    while pth[-1] != int(seed_up) and pth[-1] in prv: pth.append(prv[pth[-1]])
    rep['leak_path'] = [[round(c, 3) for c in CO[i]] + [int(mouth_v[i])] for i in pth[::-1]]
rep['flood'] = {'front': int(front.sum()), 'upper': int(up_lab.sum()), 'lower': int(lo_lab.sum()), 'both': leak,
                'unlabelled': int((front & ~up_lab & ~lo_lab).sum())}
side = np.zeros(len(CO))      # 1 upper, 0 lower, fraction = blend (only zone vertices)
in_pal = np.zeros(len(CO), bool); in_flo = np.zeros(len(CO), bool)
for f in bm.faces:
    if f[mouth_l] == 1:
        in_pal[[v.index for v in f.verts]] = True
    elif f[mouth_l] == 2:
        in_flo[[v.index for v in f.verts]] = True
st_y = np.array([r['y'] for r in st_rows]); st_hp = np.array([r['hp'] for r in st_rows]); st_hf = np.array([r['hf'] for r in st_rows])
for i in map(int, np.nonzero(zone)[0]):
    y, z = CO[i, 1], CO[i, 2]
    d = z - mline(y)
    if mouth_v[i] and y < RIP_END:
        # cavity in front of the corner: hard by sheet (palate skull, floor jaw), shared lens-tip verts 0.5; over the
        # last CORNER_RAMP before RIP_END this blends into the throat's ring rule so the corner opens gradually
        hard = 1.0 if (in_pal[i] and not in_flo[i]) else (0.0 if (in_flo[i] and not in_pal[i]) else 0.5)
        hp_, hf_ = float(np.interp(y, st_y, st_hp)), float(np.interp(y, st_y, st_hf))
        u_ = float(np.clip((z - (mline(y) - hf_)) / max(hp_ + hf_, 1e-3), 0, 1))
        ring = u_ * u_ * (3 - 2 * u_)
        w_ = float(np.clip((y - (RIP_END - CORNER_RAMP)) / CORNER_RAMP, 0, 1))
        side[i] = (1 - w_) * hard + w_ * ring
    elif mouth_v[i]:
        # throat: the skull/jaw blend runs around the whole cross-section ring (floor bottom 0 -> palate top 1),
        # so the opening spreads over the ring instead of a narrow band; the jaw share fades out toward the hinge
        hp_, hf_ = float(np.interp(y, st_y, st_hp)), float(np.interp(y, st_y, st_hf))
        u_ = float(np.clip((z - (mline(y) - hf_)) / max(hp_ + hf_, 1e-3), 0, 1))
        t = u_ * u_ * (3 - 2 * u_)
        side[i] = 1 - (1 - t) * float(np.clip((HINGE.y - y) / (HINGE.y - RIP_END), 0, 1))
    elif front[i] and (up_lab[i] != lo_lab[i]):
        side[i] = 1.0 if up_lab[i] else 0.0
    elif front[i]:
        side[i] = 1.0 if d > 0 else 0.0
    else:
        band = 0.15 if not mouth_v[i] else 0.10
        t = float(np.clip(0.5 + d / (2 * band), 0, 1))
        if mouth_v[i]:      # throat: the jaw share fades out toward the hinge
            t = 1 - (1 - t) * float(np.clip((HINGE.y - y) / (HINGE.y - RIP_END), 0, 1))
        side[i] = t
changed = 0
for i in map(int, np.nonzero(zone)[0]):
    v = dv[i]
    hw_ = headw(v) if not mouth_v[i] else 1.0
    if hw_ < 0.5:
        hw_ = 1.0
    rest = [(g.group, g.weight) for g in v.groups if vgname[g.group] not in UPPER | LOWER] if not mouth_v[i] else []
    for g in list(v.groups):
        body.vertex_groups[g.group].remove([i])
    for gidx, w in rest:
        body.vertex_groups[gidx].add([i], w, 'REPLACE')
    t = side[i]
    co = Vector(CO[i])
    if t > 0:
        body.vertex_groups[gi[ML[iu[kU.find(co)[1]]]]].add([i], hw_ * t, 'ADD')
    if t < 1:
        body.vertex_groups[gi[ML[il[kL.find(co)[1]]]]].add([i], hw_ * (1 - t), 'ADD')
    changed += 1
rep['reweighted'] = changed


# ---------------------------------------------------------------- teeth and eyes: rigid copies
def copy_weights(dst_ids, src):
    src = int(src)
    w = [(g.group, g.weight) for g in dv[src].groups]
    for i in map(int, dst_ids):
        for g in list(dv[i].groups):
            body.vertex_groups[g.group].remove([int(i)])
        for gidx, ww in w:
            body.vertex_groups[gidx].add([int(i)], ww, 'REPLACE')


upper_ids = np.nonzero(zone & (side > 0.99))[0]; lower_ids = np.nonzero(zone & (side < 0.01))[0]
kup = KDTree(len(upper_ids)); [kup.insert(Vector(CO[i]), int(i)) for i in upper_ids]; kup.balance()
klo = KDTree(len(lower_ids)); [klo.insert(Vector(CO[i]), int(i)) for i in lower_ids]; klo.balance()
teeth_parts = {}
nparts = comp.max() + 1
for k in range(nparts):
    if k == shell_id:
        continue
    ids = np.nonzero(comp == k)[0]
    if len(ids) > 80 or mouth_v[ids].any():      # cavity islands (kept Meshy interior) are not teeth
        continue
    P = CO[ids]; c = P.mean(0)
    if not M.in_box(c):
        continue
    if abs(c[0]) > 0.35 and c[2] > 15.2:
        copy_weights(ids, kup.find(Vector(c))[1]); teeth_parts[int(k)] = 'eye'
        continue
    top = P[P[:, 2].argmax()]; bot = P[P[:, 2].argmin()]
    du = kup.find(Vector(top))[2]; dl = klo.find(Vector(bot))[2]
    if du < dl:
        copy_weights(ids, kup.find(Vector(top))[1]); teeth_parts[int(k)] = 'upper'
    else:
        copy_weights(ids, klo.find(Vector(bot))[1]); teeth_parts[int(k)] = 'lower'
rep['loose_parts'] = teeth_parts
tooth_l = bm.faces.layers.int.new('tooth')
for f in bm.faces:
    t_ = teeth_parts.get(int(comp[f.verts[0].index]))
    f[tooth_l] = 1 if t_ == 'upper' else (2 if t_ == 'lower' else 0)
# write the face attributes (weights live on the mesh vertices already; bmesh has none of them -> only attrs)
tooth_vals = [f[tooth_l] for f in bm.faces]
bm.free()
a = me.attributes.get('tooth') or me.attributes.new('tooth', 'INT', 'FACE')
a.data.foreach_set('value', tooth_vals)
if 'lip' in me.attributes:
    me.attributes.remove(me.attributes['lip'])
# ---------------------------------------------------------------- kept Meshy interior: side from the final weights
upw = np.array([sum(g.weight for g in v.groups if vgname[g.group] in UPPER) / max(sum(g.weight for g in v.groups), 1e-9)
                for v in me.vertices])
bm = bmesh.new(); bm.from_mesh(me)
ml_ = bm.faces.layers.int['mouth']; kl_ = bm.faces.layers.int['kept']; uvl_b = bm.loops.layers.uv['UVMap']
relabel = 0
for f in bm.faces:
    if not f[kl_]:
        continue
    up_ = float(np.mean([upw[v.index] for v in f.verts])) > 0.5
    new_m = 1 if up_ else 2
    relabel += int(new_m != f[ml_]); f[ml_] = new_m
    for lp in f.loops:
        q = lp.vert.co
        along = float(np.interp(q.y, ys, ALONG))
        i_ = int(np.clip(np.searchsorted(ys, q.y), 0, NS - 1))
        acr = np.sign(q.x) * min(abs(q.x) / max(st_rows[i_]['W'], 1e-3), 1.0) * ACR_T[i_][-1]
        lp[uvl_b].uv = ((0.01 if up_ else 0.51) + MOUTH_UV_SCALE * along,
                        0.90 + float(np.clip(MOUTH_UV_SCALE * (acr if up_ else -acr), -0.094, 0.094)))
bm.to_mesh(me); bm.free()
rep['kept_relabelled'] = relabel

# ---------------------------------------------------------------- teeth gate (bind = the most closed MM9 pose)
# Height fields from inside the mouth gap at a tooth vertex's (x, y): zU = the skull-side surface met going UP from the
# mouth line (palate, upper gum, upper lip), zL = the jaw-side surface met going DOWN (floor, lower gum, lower lip).
# Piercing: an upper-tooth vertex below zL, a lower-tooth vertex above zU (in the opposite jaw when closed).
# Seated: the root (an upper tooth's top, a lower tooth's bottom) beyond its own surface (inside its own gum).
# A failing tooth moves along z toward its own jaw by the larger shortfall + TOOTH_MARGIN (at most TOOTH_MOVE_MAX).
TOOTH_MARGIN, TOOTH_MOVE_MAX = 0.008, 0.10
fside = np.array([np.mean([upw[i] for i in p.vertices]) for p in me.polygons])
tooth_attr = np.zeros(len(me.polygons), np.int32); me.attributes['tooth'].data.foreach_get('value', tooth_attr)
COv = np.array([tuple(v.co) for v in me.vertices])
upolys = [list(p.vertices) for p in me.polygons if fside[p.index] > 0.5 and not tooth_attr[p.index]]
lpolys = [list(p.vertices) for p in me.polygons if fside[p.index] <= 0.5 and not tooth_attr[p.index]]
BU = BVHTree.FromPolygons([tuple(c) for c in COv], upolys)
BL = BVHTree.FromPolygons([tuple(c) for c in COv], lpolys)


def zU(x, y):
    h = BU.ray_cast(Vector((x, y, mline(y) - 0.03)), Vector((0, 0, 1)), 2.0); return h[0].z if h[0] is not None else None


def zL(x, y):
    h = BL.ray_cast(Vector((x, y, mline(y) + 0.03)), Vector((0, 0, -1)), 2.0); return h[0].z if h[0] is not None else None


bmT = bmesh.new(); bmT.from_mesh(me); compT = M.parts(bmT); bmT.free()
tooth_vert = np.zeros(len(COv), np.int8)
for p in me.polygons:
    if tooth_attr[p.index]:
        tooth_vert[list(p.vertices)] = 1
tooth_parts = sorted(set(int(compT[v]) for p in me.polygons if tooth_attr[p.index] for v in p.vertices))
teeth_report = {}
for k in tooth_parts:
    ids = np.nonzero(compT == k)[0]
    P = COv[ids]
    # which jaw holds it: the end that sits deeper inside its own jaw (root), else the side of the mouth line
    bot, top = P[P[:, 2].argmin()], P[P[:, 2].argmax()]
    zl_b, zu_t = zL(bot[0], bot[1]), zU(top[0], top[1])
    dl = (zl_b - bot[2]) if zl_b is not None else -1.0
    du = (top[2] - zu_t) if zu_t is not None else -1.0
    if dl < 0 and du < 0:
        kind = 'upper' if P[:, 2].mean() > mline(float(P[:, 1].mean())) else 'lower'
    else:
        kind = 'upper' if du > dl else 'lower'
    # rigid: the weights of the nearest gum vertex of that side
    cand = np.nonzero((upw > 0.99) if kind == 'upper' else (upw < 0.01))[0]
    cand = cand[(np.abs(COv[cand, 1] - P[:, 1].mean()) < 0.6) & (tooth_vert[cand] == 0)]
    root_ = top if kind == 'upper' else bot
    src = int(cand[np.argmin(np.linalg.norm(COv[cand] - root_, axis=1))])
    copy_weights(ids, src)
    upw[ids] = 1.0 if kind == 'upper' else 0.0
    pierce = 0.0
    for q in P:
        if kind == 'upper':
            zl = zL(q[0], q[1]); pierce = max(pierce, (zl - q[2]) if zl is not None else 0.0)
        else:
            zu = zU(q[0], q[1]); pierce = max(pierce, (q[2] - zu) if zu is not None else 0.0)
    root = P[P[:, 2].argmax()] if kind == 'upper' else P[P[:, 2].argmin()]
    if kind == 'upper':
        own = zU(root[0], root[1]); gap = (own - root[2]) if own is not None else None
    else:
        own = zL(root[0], root[1]); gap = (root[2] - own) if own is not None else None
    need = max(pierce, gap if gap is not None else 0.0)
    move = min(need + TOOTH_MARGIN, TOOTH_MOVE_MAX) if need > 0 else 0.0
    if move:
        dz = move if kind == 'upper' else -move
        for i in ids:
            me.vertices[int(i)].co.z += dz
    teeth_report[k] = {'kind': kind, 'pierce': round(pierce, 4), 'root_gap': None if gap is None else round(gap, 4),
                       'moved': round(move, 4), 'length': round(float(np.ptp(P[:, 2])), 3),
                       'y': round(float(P[:, 1].mean()), 3), 'x': round(float(P[:, 0].mean()), 3)}
rep['teeth_gate'] = teeth_report
rep['teeth_piercing_before'] = sum(1 for t in teeth_report.values() if t['pierce'] > 0)
rep['teeth_unseated_before'] = sum(1 for t in teeth_report.values() if t['root_gap'] is None or t['root_gap'] > 0)
# re-check after the moves
COv = np.array([tuple(v.co) for v in me.vertices])
after_p = 0
for k in tooth_parts:
    ids = np.nonzero(compT == k)[0]; kind = teeth_report[k]['kind']
    for q in COv[ids]:
        if kind == 'upper':
            zl = zL(q[0], q[1])
            if zl is not None and q[2] < zl - 1e-4: after_p += 1; break
        else:
            zu = zU(q[0], q[1])
            if zu is not None and q[2] > zu + 1e-4: after_p += 1; break
rep['teeth_piercing_after'] = after_p
bpy.context.view_layer.objects.active = body
for o in bpy.data.objects:
    o.select_set(o == body)
bpy.ops.object.vertex_group_limit_total(limit=4)
bpy.ops.object.vertex_group_normalize_all(lock_active=False)
rep['triangles'] = sum(len(p.vertices) - 2 for p in me.polygons)
uw = [v.index for v in me.vertices if not v.groups or sum(g.weight for g in v.groups) < 0.99]
rep['unweighted_vertices'] = len(uw)
rep['unweighted_sample'] = [[round(c, 3) for c in me.vertices[i].co] for i in uw[:8]]
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(rep, open(REP, 'w'), indent=1)
print('MOUTH_REBUILD', json.dumps({k: v for k, v in rep.items() if k not in ('stations',)}))
