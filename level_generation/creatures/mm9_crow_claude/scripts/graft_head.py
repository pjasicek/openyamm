"""Replace the crow's head with the head-only Smart Topology (meshy/head_smart_v1, from the Codex head turnaround
references_head/), 2026-10-30 head rework (user review: boxy flat skull with a crest flap, a long thin wading-bird
beak, a ragged eye cluster and a flap under the throat; weights could not fix the Meshy body's head geometry).

Args: -- <uv blend (uv_v5)> <head glb> <mm9 rig blend> <config json> <out blend> <head upload glb> <report json>

1. Body: the old head out. Every core vertex in front of a plane across the neck (normal U = the MM9 XneckB -> XneckA
   line, CUT_U along it from Xneckpiv) inside a cylinder of radius CUT_R around the neck line, and the old eye pieces.
2. New head (raw Meshy frame: beak toward -Y, crown +Z): the shell decimated (symmetric collapse SKIN_RATIO), its neck
   stub cut at raw y = HEAD_CUT_Y; scaled so the stub's ring is SCALE_FIT of the body ring's half-width; turned about
   the lateral axis so its beak axis (gape corner -> beak tip) lies on MM9's bind beak axis (Xbeak joint -> MM9 beak
   tip), so the beak points where MM9's does in every clip; its gape corner placed on MM9's Xbeak joint.
3. A loft of LOFT_RINGS rings bridges the body ring to the head's neck ring along a Hermite curve (the bind head looks
   down as MM9's does; the clips straighten the neck); its faces belong to the head.
4. The head part (head, loft, a copy of the body ring) gets its own UVs (claude_shared/uv_atlas.py, 1K) and the
   'head' face attribute (material CrowHead); the upload for the head retexture is exported in the raw Meshy frame.
5. Weights: skull, beak and eyes rigid on Xhead (MM9's Xbeak only nods the bill a few degrees; the closed HD beak
   stays with the skull); the neck stub and the loft blend body-ring weights -> XneckA -> Xheadpiv -> Xhead along the
   neck (the throat bends with the neck: no hanging flap).
The beak tip (bind) is stored on the Body as the custom property 'beak_tip' for the mouth socket."""
import bpy, bmesh, sys, os, json, math, heapq
import numpy as np
from mathutils import Vector, Matrix, Quaternion
from mathutils.kdtree import KDTree

a = sys.argv[sys.argv.index('--') + 1:]
IN, HEADGLB, MM9, CFGF, OUT, UPLOAD, REP = a
cfg = json.load(open(CFGF))
CUT_U, CUT_R = cfg.get('cut_u', 0.05), cfg.get('cut_r', 0.085)
HEAD_CUT_Y = cfg.get('head_cut_y', 0.30)
SCALE_FIT = cfg.get('scale_fit', 0.92)
SKIN_RATIO = cfg.get('skin_ratio', 0.25)
LOFT = cfg.get('loft_rings', 3)
STATIONS = cfg.get('stations', [[0.35, 'XneckA'], [0.7, 'Xheadpiv'], [1.0, 'Xhead']])
SKULL_BACK_Y = cfg.get('skull_back_y', 0.05)
UV_SIZE = cfg.get('uv_size', 1024)
rep = {'config': cfg}
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                                'claude_shared'))
import uv_atlas

bpy.ops.wm.open_mainfile(filepath=IN)
sc = bpy.context.scene
body = bpy.data.objects['Body']
rig = bpy.data.objects['MM9_Rig']
if rig.animation_data:
    rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
J = {b.name: np.array(b.head_local) for b in rig.data.bones}
N0 = J['Xneckpiv']
U = J['XneckA'] - J['XneckB']; U /= np.linalg.norm(U)
gidx = {g.name: g.index for g in body.vertex_groups}
for name in ('Xhead', 'Xheadpiv', 'XneckA'):
    if name not in gidx:
        body.vertex_groups.new(name=name)
gidx = {g.name: g.index for g in body.vertex_groups}


def ucoord(p):
    return float((np.array(p) - N0) @ U)


def ordered_loop(edges):
    """vertices of a closed edge loop in order"""
    adj = {}
    for e in edges:
        x, y = e.verts
        adj.setdefault(x, []).append(y); adj.setdefault(y, []).append(x)
    start = next(iter(adj)); out = [start]; prev = None; cur = start
    while True:
        nxt = [y for y in adj[cur] if y is not prev]
        if not nxt or nxt[0] is start:
            break
        prev, cur = cur, nxt[0]
        out.append(cur)
    return out


def boundary_loops_on_plane(bm, test):
    on = [e for e in bm.edges if e.is_boundary and all(test(x.co) for x in e.verts)]
    loops, seen = [], set()
    for e in on:
        if e in seen:
            continue
        st, lp = [e], []
        seen.add(e)
        while st:
            x = st.pop(); lp.append(x)
            for vv in x.verts:
                for y in vv.link_edges:
                    if y in on and y not in seen:
                        seen.add(y); st.append(y)
        loops.append(lp)
    return loops


# ---------------- MM9 beak axis (bind)
with bpy.data.libraries.load(MM9) as (src, dst):
    dst.objects = [o for o in src.objects]
mp, ml = [], []
for o in dst.objects:
    if o is None or o.type != 'MESH':
        continue
    for v in o.data.vertices:
        g = max(v.groups, key=lambda g: g.weight)
        mp.append(tuple(o.matrix_world @ v.co)); ml.append(o.vertex_groups[g.group].name)
mp, ml = np.array(mp), np.array(ml)
bk9 = mp[np.isin(ml, ['Xbeak', 'Xjawpiv'])]
tip9 = bk9[np.argsort(np.linalg.norm(bk9 - J['Xbeak'], axis=1))[-max(3, len(bk9) // 10):]].mean(0)
axis9 = tip9 - J['Xbeak']
sag = lambda d: math.atan2(d[2], -d[1])
rep['mm9_beak'] = {'base': J['Xbeak'].tolist(), 'tip': tip9.tolist(), 'length': float(np.linalg.norm(axis9)),
                   'sag_deg': math.degrees(sag(axis9))}

# ---------------- 1. body: old head out
bm = bmesh.new()
bm.from_mesh(body.data)
dl = bm.verts.layers.deform.active
pl = bm.verts.layers.int['piece']
cl = bm.verts.layers.int['chain']
hl = bm.faces.layers.int.get('head') or bm.faces.layers.int.new('head')
bm.verts.ensure_lookup_table()
eyes_old = [v for v in bm.verts if v[pl] == 2]
rep['old_eye_verts'] = len(eyes_old)
bmesh.ops.delete(bm, geom=eyes_old, context='VERTS')
P0 = N0 + U * CUT_U


def in_cyl(co):
    d = np.array(co) - N0
    return np.linalg.norm(d - (d @ U) * U) < CUT_R


# the head's size reference: the neck's half-width at SCALE_REF_U (independent of where the neck is cut)
SCALE_REF_U = cfg.get('scale_ref_u', 0.05)
ref = np.array([tuple(v.co) for v in bm.verts if v[cl] < 0 and in_cyl(v.co) and abs(ucoord(v.co) - SCALE_REF_U) < 0.012])
hw_ref = float(np.abs(ref[:, 0] - ref[:, 0].mean()).max())
rep['scale_ref'] = {'u': SCALE_REF_U, 'half_width': hw_ref, 'verts': len(ref)}
seed = [v for v in bm.verts if v[cl] < 0 and in_cyl(v.co) and ucoord(v.co) > CUT_U - 0.02]
sel_f = list({f for v in seed for f in v.link_faces})
sel_e = list({e for f in sel_f for e in f.edges})
sel_v = list({x for f in sel_f for x in f.verts})
bmesh.ops.bisect_plane(bm, geom=sel_v + sel_e + sel_f, dist=1e-5, plane_co=Vector(P0), plane_no=Vector(U),
                       clear_outer=True)
# leftovers of the old head in front of the plane, cut off from the body (pieces), go too
seen = {}
for v in bm.verts:
    if v in seen:
        continue
    c = len(set(seen.values())); st = [v]; seen[v] = c
    while st:
        x = st.pop()
        for e in x.link_edges:
            y = e.other_vert(x)
            if y not in seen:
                seen[y] = c; st.append(y)
cnt = np.bincount(list(seen.values()))
main = int(np.argmax(cnt))
stray = [v for v, c in seen.items() if c != main]       # the old beak and other head pieces cut off the body
rep['stray_old_head_verts'] = len(stray)
bmesh.ops.delete(bm, geom=stray, context='VERTS')
loops = boundary_loops_on_plane(bm, lambda co: abs(ucoord(co) - CUT_U) < 1e-4)


def axis_dist(lp):
    c = np.mean([tuple(x.co) for e in lp for x in e.verts], 0) - N0
    return np.linalg.norm(c - (c @ U) * U)


ring_b_edges = min(loops, key=axis_dist)
ring_b = ordered_loop(ring_b_edges)
RB = np.array([tuple(v.co) for v in ring_b])
cb = RB.mean(0)
up_b = np.array([0, 0, 1.0]) - U[2] * U; up_b /= np.linalg.norm(up_b)
side_b = np.cross(U, up_b)
hw_b = float(np.abs((RB - cb) @ side_b).max())
ring_w = [dict(v[dl].items()) for v in ring_b]
rep['body_ring'] = {'verts': len(ring_b), 'centre': cb.round(4).tolist(), 'half_width': hw_b,
                    'half_height': float(np.abs((RB - cb) @ up_b).max()), 'plane_loops': len(loops)}

# ---------------- 2. new head (raw frame)
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=HEADGLB)
new = [o for o in bpy.data.objects if o not in before]
hsrc = next(o for o in new if o.type == 'MESH')
hb = bmesh.new(); hb.from_mesh(hsrc.data); hb.transform(hsrc.matrix_world)
for o in new:
    bpy.data.objects.remove(o)
bmesh.ops.remove_doubles(hb, verts=hb.verts, dist=1e-6)
kind = hb.verts.layers.int.new('kind')            # 1 shell, 2 eye (layers before any element is referenced)
for f in hb.faces:
    f.material_index = 0
# components: the main shell and the two eyes
comp = {}
for v in hb.verts:
    if v in comp:
        continue
    c = len(set(comp.values())); st = [v]; comp[v] = c
    while st:
        x = st.pop()
        for e in x.link_edges:
            y = e.other_vert(x)
            if y not in comp:
                comp[y] = c; st.append(y)
csz = np.bincount(list(comp.values()))
shell_c = int(np.argmax(csz))
for v in hb.verts:
    v[kind] = 1 if comp[v] == shell_c else 2
rep['head_raw'] = {'verts': len(hb.verts), 'tris': len(hb.faces), 'components': sorted(csz.tolist(), reverse=True)}

# beak tip and gape corner (the mouth slit is the shell's open boundary; its rear ends are the gape corners)
shell_v = [v for v in hb.verts if v[kind] == 1]
tip_raw = np.array(tuple(min(shell_v, key=lambda v: v.co.y).co))
slit = [v for v in shell_v if v.is_boundary]
SL = np.array([tuple(v.co) for v in slit])
rear = SL[np.argsort(SL[:, 1])[-6:]]
gape_raw = np.array([0.0, rear[:, 1].mean(), rear[:, 2].mean()])
axis_raw = tip_raw - gape_raw
rep['head_raw'].update({'tip': tip_raw.round(4).tolist(), 'gape': gape_raw.round(4).tolist(),
                        'beak_len': float(np.linalg.norm(axis_raw)), 'beak_sag_deg': math.degrees(sag(axis_raw))})
# the Meshy head is double-walled (an inner lining under the whole surface, joined to the outer one at the mouth
# slit): vertices that see no sky (ray escape < 2 % over a hemisphere) are the lining and go
from mathutils.bvhtree import BVHTree
hb.normal_update()
bvh_h = BVHTree.FromBMesh(hb)
rng = np.random.default_rng(0)
DIRS = rng.normal(size=(48, 3)); DIRS /= np.linalg.norm(DIRS, axis=1)[:, None]
inner = []
for v in hb.verts:
    if v[kind] != 1:
        continue
    nrm = np.array(v.normal); hit = tot = 0
    for d in DIRS:
        if d @ nrm <= 0.05:
            continue
        tot += 1
        if bvh_h.ray_cast(v.co + Vector(d) * 1e-4, Vector(d), 5.0)[0] is not None:
            hit += 1
    if tot and (tot - hit) / tot < 0.02:
        inner.append(v)
# only the big connected sheet is the lining; small dark pockets (nostrils, eye sockets) stay
iset = set(inner); icomp = {}
for v in inner:
    if v in icomp:
        continue
    c = len(set(icomp.values())); st = [v]; icomp[v] = c
    while st:
        x = st.pop()
        for e in x.link_edges:
            y = e.other_vert(x)
            if y in iset and y not in icomp:
                icomp[y] = c; st.append(y)
isz = np.bincount(list(icomp.values())) if icomp else np.zeros(0, int)
inner = [v for v in inner if isz[icomp[v]] >= 200]
rep['head_raw']['inner_lining_verts'] = len(inner)
rep['head_raw']['dark_pockets_kept'] = int(sum(x for x in isz if x < 200))
bmesh.ops.delete(hb, geom=inner, context='VERTS')
# small loose bits left by the lining removal (single faces at the slit)
lc = {}
for v in hb.verts:
    if v in lc or v[kind] != 1:
        continue
    c = len(set(lc.values())); st = [v]; lc[v] = c
    while st:
        x = st.pop()
        for e in x.link_edges:
            y = e.other_vert(x)
            if y not in lc:
                lc[y] = c; st.append(y)
lsz = np.bincount(list(lc.values()))
bmesh.ops.delete(hb, geom=[v for v, c in lc.items() if c != int(np.argmax(lsz))], context='VERTS')
rep['head_raw']['loose_after_lining'] = int(lsz.sum() - lsz.max())
# the mouth slit, open into the removed lining, is closed (the beak stays shut)
slit_e = [e for e in hb.edges if e.is_boundary]
filled = bmesh.ops.holes_fill(hb, edges=slit_e, sides=0)
bmesh.ops.triangulate(hb, faces=filled['faces'])
rep['head_raw']['mouth_fill_faces'] = len(filled['faces'])
left = [e for e in hb.edges if e.is_boundary]
if left:
    tf = bmesh.ops.triangle_fill(hb, use_beauty=True, use_dissolve=False, edges=left)
    rep['head_raw']['mouth_trifill_faces'] = len(tf['geom'])
rep['head_raw']['open_edges_left'] = sum(1 for e in hb.edges if e.is_boundary)
# decimate the shell (symmetric collapse), eyes kept
tmp = hb.copy()
kl = tmp.verts.layers.int['kind']
bmesh.ops.delete(tmp, geom=[v for v in tmp.verts if v[kl] != 1], context='VERTS')
m_sh = bpy.data.meshes.new('HeadShell'); tmp.to_mesh(m_sh); tmp.free()
o_sh = bpy.data.objects.new('HeadShell', m_sh); sc.collection.objects.link(o_sh)
md = o_sh.modifiers.new('dec', 'DECIMATE'); md.decimate_type = 'COLLAPSE'; md.ratio = SKIN_RATIO
md.use_symmetry = True; md.symmetry_axis = 'X'
for o in bpy.data.objects:
    o.select_set(o == o_sh)
bpy.context.view_layer.objects.active = o_sh
bpy.ops.object.modifier_apply(modifier=md.name)
eb = hb.copy()
kl = eb.verts.layers.int['kind']
bmesh.ops.delete(eb, geom=[v for v in eb.verts if v[kl] != 2], context='VERTS')
m_ey = bpy.data.meshes.new('HeadEyes'); eb.to_mesh(m_ey); eb.free()
hb.free()
nb = bmesh.new(); nb.from_mesh(m_sh)
kl = nb.verts.layers.int.get('kind') or nb.verts.layers.int.new('kind')
dlh = nb.verts.layers.deform.verify()
for v in nb.verts:
    v[kl] = 1
nsh = len(nb.verts)
nb.from_mesh(m_ey)
nb.verts.ensure_lookup_table()
for v in nb.verts[nsh:]:
    v[kl] = 2
bpy.data.objects.remove(o_sh)
# the stub cut
shell = [v for v in nb.verts if v[kl] == 1]
sf = list({f for v in shell for f in v.link_faces})
se = list({e for f in sf for e in f.edges})
bmesh.ops.bisect_plane(nb, geom=shell + se + sf, dist=1e-6, plane_co=(0, HEAD_CUT_Y, 0), plane_no=(0, 1, 0),
                       clear_outer=True)
# the shell's inner lining (Meshy closed the neck with an inward cap) is cut free: keep the largest shell piece
hcomp = {}
for v in nb.verts:
    if v in hcomp or v[kl] != 1:
        continue
    c = len(set(hcomp.values())); st = [v]; hcomp[v] = c
    while st:
        x = st.pop()
        for e in x.link_edges:
            y = e.other_vert(x)
            if y not in hcomp:
                hcomp[y] = c; st.append(y)
hsz = np.bincount(list(hcomp.values()))
rep['head_shell_pieces_removed'] = sorted((int(x) for i, x in enumerate(hsz) if i != int(np.argmax(hsz))), reverse=True)
bmesh.ops.delete(nb, geom=[v for v, c in hcomp.items() if c != int(np.argmax(hsz))], context='VERTS')
hloops = boundary_loops_on_plane(nb, lambda co: abs(co.y - HEAD_CUT_Y) < 1e-4)
ring_h_edges = max(hloops, key=len)
ring_h = ordered_loop(ring_h_edges)
RH = np.array([tuple(v.co) for v in ring_h])
ch_raw = RH.mean(0)
hw_h_raw = float(np.abs(RH[:, 0] - ch_raw[0]).max())
rep['head_tris_final'] = len(nb.faces)
rep['head_ring_raw'] = {'verts': len(ring_h), 'centre': ch_raw.round(4).tolist(), 'half_width': hw_h_raw,
                        'loops_on_plane': len(hloops)}

# ---------------- placement raw -> bind: scale, turn about X, translate (gape corner on MM9's Xbeak joint)
s = SCALE_FIT * hw_ref / hw_h_raw
alpha = sag(axis_raw) - sag(axis9)
R = np.array(Matrix.Rotation(alpha, 3, 'X'))
T = J['Xbeak'] - s * (R @ gape_raw)


def place(p):
    return s * (R @ np.array(p)) + T


def unplace(p):
    return R.T @ ((np.array(p) - T) / s)


for v in nb.verts:
    v.co = Vector(place(tuple(v.co)))
tip_b = place(tip_raw)
ch = place(ch_raw)
rep['placement'] = {'scale': s, 'turn_deg': math.degrees(alpha), 'beak_tip': tip_b.round(4).tolist(),
                    'beak_len_m': float(np.linalg.norm(axis_raw) * s), 'head_ring_centre': ch.round(4).tolist(),
                    'gap_m': float(np.linalg.norm(ch - cb))}
# head ring frame: n_h from the ring toward the head (raw -y), up from raw +z
n_h = R @ np.array([0, -1.0, 0]); up_h = R @ np.array([0, 0, 1.0])
up_h -= (up_h @ n_h) * n_h; up_h /= np.linalg.norm(up_h)

# ---------------- 3. loft: body ring copy + LOFT rings + bridge to the head ring
RHb = np.array([tuple(v.co) for v in ring_h])
side_h = np.cross(n_h, up_h)


def angles(P, c, up, side):
    d = P - c
    return np.arctan2(d @ side, d @ up), d @ up, d @ side


th_b, ab, bb = angles(RB, cb, up_b, side_b)
th_h, ah, bh = angles(RHb, ch, up_h, side_h)
oh = np.argsort(th_h)
tsort = np.concatenate([th_h[oh] - 2 * np.pi, th_h[oh], th_h[oh] + 2 * np.pi])
ah_i = np.interp(th_b, tsort, np.tile(ah[oh], 3))
bh_i = np.interp(th_b, tsort, np.tile(bh[oh], 3))
L = float(np.linalg.norm(ch - cb))


def herm(t):
    h00, h10, h01, h11 = 2 * t ** 3 - 3 * t ** 2 + 1, t ** 3 - 2 * t ** 2 + t, -2 * t ** 3 + 3 * t ** 2, t ** 3 - t ** 2
    return h00 * cb + h10 * U * L + h01 * ch + h11 * n_h * L


ring_copy = [nb.verts.new(Vector(p)) for p in RB]
for v in ring_copy:
    v[kl] = 3
n = len(RB)
for j in range(n):
    nb.edges.new((ring_copy[j], ring_copy[(j + 1) % n]))
rings = [ring_copy]
LOFT_MODE = cfg.get('loft_mode', 'custom')
if LOFT_MODE == 'custom':
    q_bh = Vector(U).rotation_difference(Vector(n_h))
    for k in range(1, LOFT + 1):
        t = k / (LOFT + 1)
        q = Quaternion().slerp(q_bh, t)
        n_t = np.array(q @ Vector(U))
        up_t = (1 - t) * up_b + t * up_h
        up_t -= (up_t @ n_t) * n_t; up_t /= np.linalg.norm(up_t)
        side_t = np.cross(n_t, up_t)
        C = herm(t)
        A = (1 - t) * ab + t * ah_i
        Bs = (1 - t) * bb + t * bh_i
        ring = [nb.verts.new(Vector(C + A[j] * up_t + Bs[j] * side_t)) for j in range(n)]
        for v in ring:
            v[kl] = 4
        rings.append(ring)
    loft_f = []
    for r0, r1 in zip(rings, rings[1:]):
        for j in range(n):
            loft_f.append(nb.faces.new((r0[j], r0[(j + 1) % n], r1[(j + 1) % n], r1[j])))
    for j in range(n):
        nb.edges.get((rings[-1][j], rings[-1][(j + 1) % n])) or nb.edges.new((rings[-1][j], rings[-1][(j + 1) % n]))
    last_edges = [nb.edges.get((rings[-1][j], rings[-1][(j + 1) % n])) for j in range(n)]
    res = bmesh.ops.bridge_loops(nb, edges=last_edges + ring_h_edges)
    rep['loft'] = {'mode': LOFT_MODE, 'rings': LOFT, 'ring_verts': n, 'bridge_faces': len(res['faces'])}
else:
    # Blender's bridge with cuts and surface smoothness between the body ring copy and the head ring
    copy_e = [nb.edges.get((ring_copy[j], ring_copy[(j + 1) % n])) for j in range(n)]
    for e in nb.edges:
        e.select = False
    for v in nb.verts:
        v.select = False
    for f in nb.faces:
        f.select = False
    for e in copy_e + ring_h_edges:
        e.select = True
        for x in e.verts:
            x.select = True
    tm = bpy.data.meshes.new('loft_tmp'); nb.to_mesh(tm); nb.free()
    to = bpy.data.objects.new('loft_tmp', tm); sc.collection.objects.link(to)
    for o in bpy.data.objects:
        o.select_set(o == to)
    bpy.context.view_layer.objects.active = to
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type='EDGE')
    bpy.ops.mesh.bridge_edge_loops(number_cuts=LOFT, interpolation='SURFACE', smoothness=cfg.get('loft_smooth', 1.0),
                                   profile_shape_factor=0.0)
    bpy.ops.object.mode_set(mode='OBJECT')
    nb = bmesh.new(); nb.from_mesh(tm)
    kl = nb.verts.layers.int['kind']
    dlh = nb.verts.layers.deform.verify()
    for v in nb.verts:
        if v[kl] == 0:
            v[kl] = 4
    bpy.data.objects.remove(to)
    rep['loft'] = {'mode': LOFT_MODE, 'cuts': LOFT, 'ring_verts': n}
bmesh.ops.recalc_face_normals(nb, faces=list(nb.faces))
bmesh.ops.triangulate(nb, faces=list(nb.faces))
nb.normal_update()

# ---------------- weights (param T along the neck: 0 body ring, 1 skull back)
y_back = SKULL_BACK_Y
y_cut = HEAD_CUT_Y
T_ring = 0.45            # the head ring's position along the neck parameter
WEIGHT_MODE = cfg.get('weight_mode', 'stations')
# segment centres along U of the MM9 neck chain (Xneckpiv .. Xheadpiv), from the joints
_chain = ['Xneckpiv', 'XneckB', 'XneckA', 'Xheadpiv', 'Xhead']
_uj = [ucoord(J[b]) for b in _chain]
CHAIN_C = [((_uj[i] + _uj[i + 1]) / 2, _chain[i]) for i in range(len(_chain) - 1)]
SKULL_BLEND = cfg.get('skull_blend', 0.08)      # raw units behind the skull back over which the stub turns rigid
RING_BLEND = cfg.get('ring_blend', 0.012)       # m from the body ring over which the loft leaves the body weights
rep['chain_centres'] = CHAIN_C


def station_w(Tv, base):
    pts = [(0.0, None)] + [(p, n_) for p, n_ in STATIONS]
    for (t0, a0), (t1, a1) in zip(pts, pts[1:]):
        if Tv <= t1:
            u = (Tv - t0) / max(t1 - t0, 1e-6)
            u = u * u * (3 - 2 * u)
            w = {}
            for g, x in (base.items() if a0 is None else [(gidx[a0], 1.0)]):
                w[g] = w.get(g, 0) + x * (1 - u)
            w[gidx[a1]] = w.get(gidx[a1], 0) + u
            return w
    return {gidx[STATIONS[-1][1]]: 1.0}


kd_ring = KDTree(len(RB))
for i, p in enumerate(RB):
    kd_ring.insert(Vector(p), i)
kd_ring.balance()
vw = {}
for v in nb.verts:
    base = ring_w[kd_ring.find(v.co)[1]]
    k = v[kl]
    if k == 2:
        Tv = 1.0
    elif k == 3:
        Tv = 0.0
    elif k == 4:
        tl = float(np.clip((np.array(tuple(v.co)) - cb) @ (ch - cb) / max(L * L, 1e-9), 0, 1))
        Tv = T_ring * tl
    else:
        yr = unplace(tuple(v.co))[1]
        Tv = T_ring + (1 - T_ring) * float(np.clip((y_cut - yr) / max(y_cut - y_back, 1e-6), 0, 1))
    if WEIGHT_MODE == 'chain' and k != 2:
        # along the MM9 neck chain: each vertex takes the bone whose segment its neck coordinate u lies on (blended
        # between the segment centres), so nothing behind a pivot follows that pivot's bone; the skull is rigid
        u = ucoord(tuple(v.co))
        cw = {}
        for (u0, b0), (u1, b1) in zip(CHAIN_C, CHAIN_C[1:]):
            if u <= u1:
                f = float(np.clip((u - u0) / (u1 - u0), 0, 1)); f = f * f * (3 - 2 * f)
                cw = {gidx[b0]: 1 - f, gidx[b1]: f}
                break
        if not cw:
            cw = {gidx[CHAIN_C[-1][1]]: 1.0}
        if k == 1:
            yr = unplace(tuple(v.co))[1]
            hk = float(np.clip((y_back + SKULL_BLEND - yr) / SKULL_BLEND, 0, 1)); hk = hk * hk * (3 - 2 * hk)
        else:
            hk = 0.0
        bk = 0.0 if k != 3 else 1.0
        if k == 4:
            bk = 1 - float(np.clip(np.linalg.norm(np.array(tuple(v.co)) - RB[kd_ring.find(v.co)[1]]) / RING_BLEND, 0, 1))
        w = {}
        for g, x in cw.items():
            w[g] = w.get(g, 0) + x * (1 - hk) * (1 - bk)
        w[gidx['Xhead']] = w.get(gidx['Xhead'], 0) + hk * (1 - bk)
        for g, x in base.items():
            w[g] = w.get(g, 0) + x * bk
        vw[v] = w
    else:
        vw[v] = station_w(Tv, base) if Tv < 1.0 else {gidx['Xhead']: 1.0}
# smooth the neck weights a little along the mesh (not the skull)
for _ in range(cfg.get('smooth', 3)):
    new_w = {}
    for v in nb.verts:
        if v[kl] in (2, 3):
            continue
        wv = vw[v]
        if len(wv) == 1 and gidx['Xhead'] in wv and v[kl] == 1 and unplace(tuple(v.co))[1] < y_back - 0.05:
            continue
        acc = dict(wv)
        nbv = [e.other_vert(v) for e in v.link_edges]
        for u_ in nbv:
            for g, x in vw[u_].items():
                acc[g] = acc.get(g, 0) + x
        new_w[v] = {g: x / (len(nbv) + 1) for g, x in acc.items()}
    vw.update(new_w)


def norm4(w):
    top = sorted(((g, x) for g, x in w.items() if x > 1e-4), key=lambda t: -t[1])[:4]
    s_ = sum(x for _, x in top)
    return {g: x / s_ for g, x in top if x / s_ >= 0.02}


# ---------------- 4. head object: UVs and the upload
hm = bpy.data.meshes.new('CrowHeadPart')
dlh = nb.verts.layers.deform.verify()
for v in nb.verts:
    v[dlh].clear()
for v in nb.verts:
    for g, x in norm4(vw[v]).items():
        v[dlh][g] = x
nb.to_mesh(hm)
nb.free()
ho = bpy.data.objects.new('CrowHeadPart', hm)
sc.collection.objects.link(ho)
for name in [g.name for g in body.vertex_groups]:
    ho.vertex_groups.new(name=name)
hm.update()
uvrep = uv_atlas.unwrap(ho, size=UV_SIZE)
rep['head_uv'] = {k: v for k, v in uvrep.items() if not isinstance(v, (list, dict))}
# upload: raw Meshy frame, no rig, no materials
up = ho.copy(); up.data = ho.data.copy(); sc.collection.objects.link(up)
for v in up.data.vertices:
    v.co = Vector(unplace(tuple(v.co)))
up.vertex_groups.clear()
for o in bpy.data.objects:
    o.select_set(o == up)
bpy.context.view_layer.objects.active = up
os.makedirs(os.path.dirname(UPLOAD), exist_ok=True)
bpy.ops.export_scene.gltf(filepath=UPLOAD, use_selection=True, export_format='GLB', export_yup=True,
                          export_skins=False, export_animations=False, export_materials='NONE',
                          export_attributes=False)
bpy.data.objects.remove(up)

# ---------------- 5. join into the body
bm.to_mesh(body.data); bm.free()
kind_vals = np.zeros(len(hm.vertices), np.int32)
hm.attributes['kind'].data.foreach_get('value', kind_vals)
hm.attributes.new('head', 'INT', 'FACE').data.foreach_set('value', [1] * len(hm.polygons))
hm.attributes.new('piece', 'INT', 'POINT').data.foreach_set('value', [2 if k == 2 else 0 for k in kind_vals])
hm.attributes.new('chain', 'INT', 'POINT').data.foreach_set('value', [-1] * len(hm.vertices))
nbody = len(body.data.vertices)
for o in bpy.data.objects:
    o.select_set(o in (body, ho))
bpy.context.view_layer.objects.active = body
bpy.ops.object.join()
me = body.data
# weld the ring copies onto the body ring
bmj = bmesh.new(); bmj.from_mesh(me); bmj.verts.ensure_lookup_table()
ring_ids = [v.index for v in bmj.verts if v.index < nbody and v.is_boundary and abs(ucoord(v.co) - CUT_U) < 1e-4]
copy_ids = [v.index for v in bmj.verts if v.index >= nbody and v.is_boundary and abs(ucoord(v.co) - CUT_U) < 1e-4]
targetmap = {}
kd = KDTree(len(ring_ids))
for i, vi in enumerate(ring_ids):
    kd.insert(bmj.verts[vi].co, i)
kd.balance()
for ci in copy_ids:
    p, i, d = kd.find(bmj.verts[ci].co)
    if d < 1e-5:
        targetmap[bmj.verts[ci]] = bmj.verts[ring_ids[i]]
bmesh.ops.weld_verts(bmj, targetmap=targetmap)
rep['welded'] = len(targetmap)
hlay = bmj.faces.layers.int['head']
for f in bmj.faces:
    f.material_index = 1 if f[hlay] == 1 else 0
    f.smooth = True
bmj.to_mesh(me); bmj.free()
while len(me.materials) < 2:
    me.materials.append(None)
body['beak_tip'] = list(tip_b)
# remaining open boundary (should be only the mouth slit)
bmc = bmesh.new(); bmc.from_mesh(me)
rep['boundary_edges_after'] = sum(1 for e in bmc.edges if e.is_boundary)
rep['tris'] = sum(len(f.verts) - 2 for f in bmc.faces)
rep['head_tris'] = sum(len(f.verts) - 2 for f in bmc.faces if f[bmc.faces.layers.int['head']] == 1)
bmc.free()
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(rep, open(REP, 'w'), indent=1, default=str)
print('GRAFT', json.dumps(rep, default=str))
