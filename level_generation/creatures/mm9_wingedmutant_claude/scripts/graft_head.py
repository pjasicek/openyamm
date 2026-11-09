"""Graft the head-only Smart Topology (meshy/head_smart_v1, from the Codex head turnaround references_head/) onto the
rigged, UV-mapped body (rework 2026-10-30, user review: long wedge chin, open slab mouth, flat profile, faceted eye
sockets). Diagnosis (review/v2_diag/stages*.png): the face came from the full-body Smart Topology, where the face was
about 40 px in the master: a small, narrow head 5.5 cm off the symmetry plane, no jaw line (the chin slopes straight
into the throat), a small open mouth hole and bump eyes; the texture then painted the lips and the throat skin as a
long pale wedge. Reduction (0.75 on the head) only added faceting; the fit only rotated the head rigidly; MM9 has no
jaw bone (Bip01 Head carries the whole face), so no clip stretches it.

On <uv blend> (Body + MM9_Rig):
1. Old head out: every Body component except the main shell (the old hair cap, its front strands, small hair bits)
   and the main shell above a neck cut plane (normal = the MM9 Neck -> Head line U, at CUT_U along it from Bip01
   Neck), inside a cylinder of radius CUT_R around that line (the wings stay).
2. New head: the Meshy head's skin shell, eyes and hair locks (components; its feathered bust pieces dropped), made
   exactly symmetric (the creature's right half, which faces the camera in the three-quarter master, mirrored),
   decimated with Blender's symmetric collapse (skin SKIN_RATIO, hair HAIR_RATIO), then placed: its neck axis on U,
   its face forward on the MM9 head's forward axis, scaled so its chin-to-crown height is HEAD_HEIGHT, its neck ring
   at NECK_DROP head heights below the chin centred on the body's neck ring, and cut there (skin only; the hair locks
   hang free).
3. The two neck rings are bridged (bmesh bridge_loops).
4. Weights of the new vertices: skin and bridge blend from the body's cut-ring weights to Bip01 Head between the cut
   and the jaw (with a Neck1 share in between); eyes rigid on Bip01 Head; hair from the nearest old hair vertex
   (wing bones removed). Face attribute 'head' = 1 on the new faces (the head texture set).
Args: -- <uv blend> <head glb> <config json> <out blend> <report json>"""
import bpy, bmesh, sys, json, math
import numpy as np
from mathutils import Vector, Matrix
from mathutils.kdtree import KDTree

a = sys.argv[sys.argv.index('--') + 1:]
IN, HEADGLB, CFGF, OUT, REP = a
import os as _os
MM9_BLEND = _os.path.join(_os.path.dirname(IN), 'mm9_wmut_ground.blend')
cfg = json.load(open(CFGF))
CUT_U, CUT_R = cfg.get('cut_u', -0.01), cfg.get('cut_r', 0.13)
HEAD_HEIGHT = cfg.get('head_height', 0.215)
NECK_DROP = cfg.get('neck_drop', 0.35)
SKIN_RATIO, HAIR_RATIO = cfg.get('skin_ratio', 0.7), cfg.get('hair_ratio', 0.3)
rep = {'config': cfg}

bpy.ops.wm.open_mainfile(filepath=IN)
sc = bpy.context.scene
body = bpy.data.objects['Body']
rig = body.parent
J = {b.name: np.array(b.head_local) for b in rig.data.bones}
HM = np.array(rig.data.bones['Bip01 Head'].matrix_local.to_3x3())
N0 = J['Bip01 Neck']
U = J['Bip01 Head'] - N0
U /= np.linalg.norm(U)
F = HM[:, 2] - (HM[:, 2] @ U) * U
F /= np.linalg.norm(F)
S = np.cross(U, F)                       # third axis of the neck frame
gidx = {g.name: g.index for g in body.vertex_groups}
gname = {i: n for n, i in gidx.items()}
HEAD_G, NECK1_G = gidx['Bip01 Head'], gidx['Bip01 Neck1']


def comps(bm):
    out = {}
    for v in bm.verts:
        if v in out:
            continue
        c = len(set(out.values())) if out else 0
        c = max(out.values()) + 1 if out else 0
        st = [v]; out[v] = c
        while st:
            x = st.pop()
            for e in x.link_edges:
                y = e.other_vert(x)
                if y not in out:
                    out[y] = c; st.append(y)
    return out


def ncomp_mesh(m):
    b = bmesh.new(); b.from_mesh(m); n = len(set(comps(b).values())); b.free(); return n


def ucoord(p):
    return float((np.array(p) - N0) @ U)


# ---------------- 1. body: old head out
bm = bmesh.new()
bm.from_mesh(body.data)
dl = bm.verts.layers.deform.active
hl = bm.faces.layers.int.get('head') or bm.faces.layers.int.new('head')
brl = bm.faces.layers.int.new('bridge')
bm.verts.layers.int.new('kind')           # created before any element is referenced (a new layer invalidates them)
cmap = comps(bm)
cnt = np.bincount(list(cmap.values()))
main = int(np.argmax(cnt))
old_hair = [(tuple(v.co), dict(v[dl].items())) for v, c in cmap.items() if c != main]
rep['old_pieces_removed'] = sorted((int(n) for i, n in enumerate(cnt) if i != main), reverse=True)
bmesh.ops.delete(bm, geom=[v for v, c in cmap.items() if c != main], context='VERTS')
P0 = N0 + U * CUT_U


def in_cyl(co):
    d = np.array(co) - N0
    return np.linalg.norm(d - (d @ U) * U) < CUT_R


HEADISH = {gidx[n] for n in gidx if n in ('Bip01 Head', 'Bip01 Neck1', 'Bip01 Neck') or n.startswith('Xhair')}


def headish(v):
    w = dict(v[dl].items())
    return bool(w) and max(w, key=w.get) in HEADISH


seed = [v for v in bm.verts if (in_cyl(v.co) or headish(v)) and ucoord(v.co) > CUT_U]
sel_f = list({f for v in seed for f in v.link_faces})
sel_e = list({e for f in sel_f for e in f.edges})
sel_v = list({x for f in sel_f for x in f.verts})
bmesh.ops.bisect_plane(bm, geom=sel_v + sel_e + sel_f, dist=1e-5, plane_co=Vector(P0), plane_no=Vector(U),
                       clear_outer=True)
on_plane = [e for e in bm.edges if e.is_boundary and all(abs(ucoord(x.co) - CUT_U) < 1e-4 for x in e.verts)]
loops, seen = [], set()
for e in on_plane:
    if e in seen:
        continue
    st, lp = [e], []
    seen.add(e)
    while st:
        x = st.pop(); lp.append(x)
        for vv in x.verts:
            for y in vv.link_edges:
                if y in on_plane and y not in seen:
                    seen.add(y); st.append(y)
    loops.append(lp)
on_plane = set(on_plane)


def axis_dist(lp):
    c = np.mean([tuple(x.co) for e in lp for x in e.verts], 0) - N0
    return np.linalg.norm(c - (c @ U) * U)


ring_b = min(loops, key=axis_dist)
rep['body_plane_loops'] = [[len(lp), round(float(axis_dist(lp)), 3)] for lp in loops]
ring_bv = list({x for e in ring_b for x in e.verts})
rep['body_ring_closed'] = all(sum(1 for e in x.link_edges if e in set(ring_b)) == 2 for x in ring_bv)
RB = np.array([tuple(x.co) for x in ring_bv])
cb = RB.mean(0)
cb_raw = cb.copy()
rb = float(np.mean(np.linalg.norm((RB - cb) - np.outer((RB - cb) @ U, U), axis=1)))
ring_w = [(np.array(tuple(x.co)), dict(x[dl].items())) for x in ring_bv]
rep['body_ring'] = {'verts': len(ring_bv), 'edges': len(ring_b), 'centre': cb.round(4).tolist(), 'radius': rb}
cb = cb.copy(); cb[0] = 0.0

# ---------------- 2. new head
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=HEADGLB)
new = [o for o in bpy.data.objects if o not in before]
hb = bmesh.new()
for o in new:
    if o.type == 'MESH':
        t = bmesh.new(); t.from_mesh(o.data); t.transform(o.matrix_world)
        mt = bpy.data.meshes.new('t'); t.to_mesh(mt); hb.from_mesh(mt); t.free()
for o in new:
    bpy.data.objects.remove(o)
bmesh.ops.remove_doubles(hb, verts=hb.verts, dist=1e-6)
hb.verts.ensure_lookup_table()
hb.verts.layers.int.new('kind')
HP = np.array([tuple(v.co) for v in hb.verts])
H = float(np.ptp(HP[:, 2]))
hc = comps(hb)
hcn = np.bincount(list(hc.values()))
nose_v = min(hb.verts, key=lambda v: v.co.y)
skin = hc[nose_v]
# yaw / x offset of the face: mirror search on the skin shell's front (face) vertices
face = np.array([tuple(v.co) for v, c in hc.items() if c == skin and v.co.y < nose_v.co.y + 0.18 * H
                 and v.co.z > nose_v.co.z - 0.25 * H])
best = None
kd_face = KDTree(len(face))
for i, p in enumerate(face):
    kd_face.insert(Vector(p), i)
kd_face.balance()
for yaw in np.radians(np.arange(-12, 12.01, 0.5)):
    R = np.array([[math.cos(yaw), -math.sin(yaw), 0], [math.sin(yaw), math.cos(yaw), 0], [0, 0, 1]])
    for dx in np.linspace(-0.04, 0.04, 33) * H:
        # plane: x' = 0 after rotating by yaw about the nose and shifting dx; mirror back into the original frame
        q = (face - [nose_v.co.x, nose_v.co.y, 0]) @ R.T
        q[:, 0] -= dx
        m = q * [-1, 1, 1]
        m[:, 0] += dx
        m = m @ R + [nose_v.co.x, nose_v.co.y, 0]
        d = np.median([kd_face.find(Vector(p))[2] for p in m[::3]])
        if best is None or d < best[0]:
            best = (d, yaw, dx)
d, yaw, dx = best
rep['head_mirror_fit'] = {'median': d / H, 'yaw_deg': math.degrees(yaw), 'dx_rel': dx / H}
R = Matrix.Rotation(yaw, 3, 'Z')
n0 = Vector((nose_v.co.x, nose_v.co.y, 0))
for v in hb.verts:
    q = R @ (v.co - n0)
    q.x -= dx
    v.co = q
# eyes / hair / bust
info = {}
for v, c in hc.items():
    info.setdefault(c, []).append(v)
nose = nose_v.co.copy()
# chin: walking down the face's centre column from the nose, the lowest slice still within 0.11 H of the nose's
# forwardness (below it the throat recedes)
col = np.array([tuple(v.co) for v in info[skin] if abs(v.co.x) < 0.02 * H])
chin_z = nose.z
miss = 0
for z in np.arange(nose.z - 0.06 * H, nose.z - 0.4 * H, -0.006 * H):
    sl = col[(col[:, 2] < z + 0.003 * H) & (col[:, 2] >= z - 0.003 * H)]
    if len(sl) and sl[:, 1].min() - nose.y < 0.11 * H:
        chin_z = z; miss = 0
    elif len(sl):
        miss += 1
        if miss >= 3:
            break
chin_sl = col[np.abs(col[:, 2] - chin_z) < 0.01 * H]
chin = Vector((0.0, float(chin_sl[:, 1].min()), float(chin_z)))
crown_z = max(v.co.z for v in info[skin])
kinds = {}
for c, vs in info.items():
    Q = np.array([tuple(v.co) for v in vs])
    ext = np.ptp(Q, 0).max()
    if c == skin:
        kinds[c] = 'skin'
    elif len(vs) < 400 and ext < 0.08 * H and Q[:, 1].mean() < nose.y + 0.15 * H and 0 < Q[:, 2].mean() - nose.z < 0.15 * H:
        kinds[c] = 'eye'
    elif len(vs) < 400 and ext < 0.08 * H and Q[:, 1].mean() < nose.y + 0.15 * H and chin_z < Q[:, 2].mean() < nose.z:
        kinds[c] = 'tooth'
    elif Q[:, 2].max() < nose.z:
        kinds[c] = 'bust'
    else:
        kinds[c] = 'hair'
    rep.setdefault('head_comps', []).append([kinds[c], len(vs), Q.min(0).round(3).tolist(), Q.max(0).round(3).tolist()])
rep['chin_raw'] = list(chin); rep['nose_raw'] = list(nose)
rep['head_parts'] = {k: sum(1 for c in kinds if kinds[c] == k) for k in ('skin', 'eye', 'tooth', 'hair', 'bust')}
rep['head_part_verts'] = {k: sum(len(info[c]) for c in kinds if kinds[c] == k) for k in ('skin', 'eye', 'tooth', 'hair', 'bust')}
kl = hb.verts.layers.int['kind']
for v in hb.verts:
    v[kl] = {'skin': 1, 'eye': 2, 'hair': 3, 'tooth': 4, 'bust': 9}[kinds[hc[v]]] if v in hc else 9
bmesh.ops.delete(hb, geom=[v for v in hb.verts if v[kl] == 9], context='VERTS')
# symmetric: keep the creature's right (-x), mirror
bmesh.ops.bisect_plane(hb, geom=list(hb.verts) + list(hb.edges) + list(hb.faces), dist=1e-6,
                       plane_co=(0, 0, 0), plane_no=(1, 0, 0), clear_outer=True)
for v in hb.verts:
    if abs(v.co.x) < 1e-5:
        v.co.x = 0.0
dup = bmesh.ops.duplicate(hb, geom=list(hb.verts) + list(hb.edges) + list(hb.faces))
for g in dup['geom']:
    if isinstance(g, bmesh.types.BMVert):
        g.co.x = -g.co.x
bmesh.ops.reverse_faces(hb, faces=[g for g in dup['geom'] if isinstance(g, bmesh.types.BMFace)])
bmesh.ops.remove_doubles(hb, verts=[v for v in hb.verts if v.co.x == 0.0], dist=1e-6)
# decimate (symmetric collapse) per kind: each kind on its own object (a vertex group only biases a collapse, the
# ratio applies to the whole mesh), then joined again
TOOTH_RATIO = cfg.get('tooth_ratio', 0.5)
klay = hb.verts.layers.int['kind']
parts = []
for k, ratio in ((1, SKIN_RATIO), (2, 1.0), (3, HAIR_RATIO), (4, TOOTH_RATIO)):
    pb_ = hb.copy()
    kl2 = pb_.verts.layers.int['kind']
    bmesh.ops.delete(pb_, geom=[v for v in pb_.verts if v[kl2] != k], context='VERTS')
    m = bpy.data.meshes.new(f'NewHead{k}')
    pb_.to_mesh(m); pb_.free()
    ob_ = bpy.data.objects.new(f'NewHead{k}', m)
    sc.collection.objects.link(ob_)
    if ratio < 1.0:
        md = ob_.modifiers.new('dec', 'DECIMATE')
        md.decimate_type = 'COLLAPSE'; md.ratio = ratio
        md.use_symmetry = True; md.symmetry_axis = 'X'
        for o in bpy.data.objects:
            o.select_set(o == ob_)
        bpy.context.view_layer.objects.active = ob_
        bpy.ops.object.modifier_apply(modifier=md.name)
    parts.append(ob_)
rep['head_tris_before'] = len(hb.faces)
hb.free()
for o in bpy.data.objects:
    o.select_set(o in parts)
bpy.context.view_layer.objects.active = parts[0]
bpy.ops.object.join()
ho = bpy.context.view_layer.objects.active
ho.name = 'NewHead'
hm = ho.data
rep['dbg_comps_before_dec'] = None
rep['head_tris_decimated'] = len(hm.polygons)
rep['dbg_comps_after_dec'] = ncomp_mesh(hm)
# neck ring of the new head NECK_DROP head heights below the chin
hh = crown_z - chin.z
zc = chin.z - NECK_DROP * hh
HP = np.array([tuple(v.co) for v in hm.vertices])
kind = np.zeros(len(hm.vertices), np.int32)
hm.attributes['kind'].data.foreach_get('value', kind)


from mathutils.bvhtree import BVHTree


def skin_bvh():
    tri = [list(p.vertices) for p in hm.polygons if all(kind[i] == 1 for i in p.vertices)]
    return BVHTree.FromPolygons([Vector(p) for p in HP], tri)


def neck_top(z, bvh):
    """horizontal section of the skin shell at z (just under the jaw): centre between the throat and the nape on the
    symmetry plane, mean radius from 48 rays"""
    f = bvh.ray_cast(Vector((0, -5 * hh, z)), Vector((0, 1, 0)), 10 * hh)[0]
    b = bvh.ray_cast(Vector((0, 5 * hh, z)), Vector((0, -1, 0)), 10 * hh)[0]
    c = np.array([0.0, (f.y + b.y) / 2, z])
    hits = []
    for ang in np.linspace(0, 2 * math.pi, 48, endpoint=False):
        h = bvh.ray_cast(Vector(c), Vector((math.cos(ang), math.sin(ang), 0)), hh)[0]
        if h is not None:
            hits.append(tuple(h))
    hits = np.array(hits)
    return c, float(np.hypot(hits[:, 0], hits[:, 1] - c[1]).mean()), len(hits)


# The head keeps MM9's orientation (its up on U, its forward on the MM9 head's forward, so it looks down as MM9's
# does) and its neck is cut just under the jaw; the body's neck (on the MM9 Neck -> Head line) carries it. The
# Meshy neck leans back 30 degrees under a thrust-forward head, which a longer graft would have kinked.
bvh = skin_bvh()
c1, r1, n1 = neck_top(zc, bvh)
# hair gravity: the head is pitched forward by the MM9 head's down-look (angle between U and the vertical), which
# would swing the hanging locks out backwards; the locks below ear level are turned forward by HAIR_GRAVITY of
# that angle about the back of the skull at ear level, so they hang down the back again
pitch = math.acos(float(np.clip(U[2], -1, 1)))
g = cfg.get('hair_gravity', 0.8) * pitch
zp, yp = nose.z, c1[1]
for i, v in enumerate(hm.vertices):
    if kind[i] != 3 or v.co.z >= zp:
        continue
    w = float(np.clip((zp - v.co.z) / (0.35 * hh), 0, 1))
    ang = -g * w * w * (3 - 2 * w)
    dy, dz = v.co.y - yp, v.co.z - zp
    v.co = Vector((v.co.x, yp + dy * math.cos(ang) - dz * math.sin(ang), zp + dy * math.sin(ang) + dz * math.cos(ang)))
HP = np.array([tuple(v.co) for v in hm.vertices])
rep['hair_gravity_deg'] = math.degrees(g)
axis = np.array([0.0, 0.0, 1.0])
s = HEAD_HEIGHT / hh
rep['new_head'] = {'chin_to_crown_raw': hh, 'scale': s, 'neck_ring_radius_scaled': r1 * s, 'neck_ring_n': n1,
                   'neck_axis_tilt_deg': math.degrees(math.acos(min(1, axis[2]))),
                   'scale_if_neck_matched': rb / r1}
# rotation: new axis -> U, new forward (-y, made orthogonal to the axis) -> F
fw = np.array([0, -1.0, 0]); fw -= (fw @ axis) * axis; fw /= np.linalg.norm(fw)
A = np.stack([axis, fw, np.cross(axis, fw)], 1)
Bm = np.stack([U, F, np.cross(U, F)], 1)
Rm = Bm @ A.T
X = (HP - c1) @ Rm.T * s + cb
for v, p in zip(hm.vertices, X):
    v.co = Vector(p)
rep['new_chin'] = ((np.array(chin) - c1) @ Rm.T * s + cb).round(4).tolist()
rep['new_crown_u'] = float(((np.array([0, 0, crown_z]) - c1) @ Rm.T * s + cb - N0) @ U)

def kind_of(v):
    return hm.attributes['kind'].data[v.index].value


# cut the skin shell at the body plane + a small gap (the bridge spans it); hair and eyes are not cut
GAP = cfg.get('bridge_gap', 0.008)
nb = bmesh.new(); nb.from_mesh(hm)
kl = nb.verts.layers.int['kind']
sk = [v for v in nb.verts if v[kl] == 1]
skf = list({f for v in sk for f in v.link_faces})
ske = list({e for f in skf for e in f.edges})
bmesh.ops.bisect_plane(nb, geom=sk + ske + skf, dist=1e-6, plane_co=Vector(P0 + U * GAP), plane_no=Vector(-U),
                       clear_outer=True)
# anything of the skin left below the plane in separate bits (shoulder stubs) goes
hcn = comps(nb)
skin_c = {}
for v, c in hcn.items():
    if v[kl] in (0, 1):
        skin_c[c] = skin_c.get(c, 0) + 1
keep_skin = max(skin_c, key=skin_c.get)
bmesh.ops.delete(nb, geom=[v for v, c in hcn.items() if v[kl] in (0, 1) and c != keep_skin], context='VERTS')
for v in nb.verts:
    if v[kl] == 0:
        v[kl] = 1
nb.to_mesh(hm); nb.free()
rep['head_tris_final'] = len(hm.polygons)
rep['dbg_comps_after_cut'] = ncomp_mesh(hm)

# ---------------- 3. body neck tapered onto the head's ring (radius and centre), join + bridge
ring_h_pos = np.array([tuple(v.co) for v in hm.vertices if abs(ucoord(v.co) - CUT_U - GAP) < 1e-4 and kind_of(v) == 1])
ch = ring_h_pos.mean(0)
rh = float(np.mean(np.linalg.norm((ring_h_pos - ch) - np.outer((ring_h_pos - ch) @ U, U), axis=1)))
ob = (cb_raw - N0) - ((cb_raw - N0) @ U) * U
oh = (ch - N0) - ((ch - N0) @ U) * U
TAPER = cfg.get('taper', 0.06)
k_r = rh / rb
nt = 0
for v in bm.verts:
    d = np.array(tuple(v.co)) - N0
    u = d @ U
    if not (CUT_U - TAPER - 1e-6 <= u <= CUT_U + 1e-6):
        continue
    perp = d - u * U
    rr = np.linalg.norm(perp - ob)
    wr = float(np.clip((2.0 * rb - rr) / (0.6 * rb), 0, 1))
    t = float(np.clip((u - (CUT_U - TAPER)) / TAPER, 0, 1))
    w = t * t * (3 - 2 * t) * wr
    if w <= 0:
        continue
    newp = (ob + (oh - ob) * w) + (perp - ob) * (1 + (k_r - 1) * w)
    v.co = Vector(N0 + u * U + newp)
    nt += 1
rep['neck_taper'] = {'head_ring_radius': rh, 'body_ring_radius': rb, 'ratio': k_r, 'verts_moved': nt}
nbase = len(bm.verts)
fbase = len(bm.faces)
for f in bm.faces:
    f[hl] = 0
hm.attributes.new('head', 'INT', 'FACE').data.foreach_set('value', [1] * len(hm.polygons))
bm.from_mesh(hm)
bm.verts.index_update(); bm.faces.index_update()
bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
new_verts = bm.verts[nbase:]
kl = bm.verts.layers.int.get('kind')
ring_h = [e for e in bm.edges if e.is_boundary and all(x.index >= nbase and x[kl] == 1 and
                                                         abs(ucoord(x.co) - CUT_U - GAP) < 1e-4 for x in e.verts)]
rep['head_ring_edges'] = len(ring_h)
res = bmesh.ops.bridge_loops(bm, edges=ring_b + ring_h)
bridge_f = res['faces']
rep['bridge_faces'] = len(bridge_f)
rep['dbg_comps_joined'] = len(set(comps(bm).values()))
bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
bset = set(bridge_f)
bm.verts.index_update(); bm.faces.index_update()
for f in bm.faces:
    if f in bset:
        f[hl] = 1
    f[brl] = 1 if f in bset else 0
for f in bm.faces:
    f.smooth = True

# ---------------- 4. weights
print('GRAFT-PRE', json.dumps(rep, default=str))
kd_ring = KDTree(len(ring_w))
for i, (p, w) in enumerate(ring_w):
    kd_ring.insert(Vector(p), i)
kd_ring.balance()
# MM9 head and hair vertices (rest pose, our scale) from the MM9 ground blend
mm9_pos, mm9_lab = [], []
with bpy.data.libraries.load(cfg.get('mm9_blend', 'work/mm9_wmut_ground.blend') if False else MM9_BLEND) as (src_, dst_):
    dst_.objects = [n for n in src_.objects]
for o in dst_.objects:
    if o is None or o.type != 'MESH':
        continue
    for v in o.data.vertices:
        if not v.groups:
            continue
        g = max(v.groups, key=lambda g: g.weight)
        nm = o.vertex_groups[g.group].name
        if nm == 'Bip01 Head' or nm.startswith('Xhair'):
            mm9_pos.append(o.matrix_world @ v.co); mm9_lab.append(nm)
kd_mm9 = KDTree(len(mm9_pos))
for i, p in enumerate(mm9_pos):
    kd_mm9.insert(p, i)
kd_mm9.balance()
rep['mm9_hair_head_verts'] = len(mm9_pos)
kd_hair = KDTree(len(old_hair))
for i, (p, w) in enumerate(old_hair):
    kd_hair.insert(Vector(p), i)
kd_hair.balance()
u_jaw = ucoord(rep['new_chin']) - 0.01
u0 = CUT_U
wing = {i for n, i in gidx.items() if n.startswith('Yw')}


def norm4(w):
    w = {g: x for g, x in w.items() if x > 1e-4}
    top = sorted(w.items(), key=lambda t: -t[1])[:4]
    s_ = sum(x for g, x in top)
    return {g: x / s_ for g, x in top if x / s_ >= 0.02}


for v in bm.verts:
    k = v[kl]                      # body vertices are kind 0 (freed slots are reused, so indices do not separate them)
    if k == 0:
        continue
    if k in (2, 4):
        w = {HEAD_G: 1.0}
    elif k == 3:
        # hair: the bone of the nearest ORIGINAL MM9 head/hair vertex (Bip01 Head or an Xhair joint; the MM9 skin is
        # rigid), smoothed along each lock below; the first graft took the old Meshy hair's weights, which mixed
        # Spine2 into the locks and stretched them 3.6x in Hit
        p, i, dd = kd_mm9.find(v.co)
        w = {gidx.get(mm9_lab[i], HEAD_G): 1.0}
    else:
        p, i, dd = kd_ring.find(v.co)
        base = ring_w[i][1]
        t = float(np.clip((ucoord(v.co) - u0) / max(u_jaw - u0, 1e-3), 0, 1))
        t = t * t * (3 - 2 * t)
        w = {g: x * (1 - t) for g, x in base.items()}
        w[HEAD_G] = w.get(HEAD_G, 0) + t
        w[NECK1_G] = w.get(NECK1_G, 0) + 0.6 * t * (1 - t)
    w = norm4(w)
    v[dl].clear()
    for g, x in w.items():
        v[dl][g] = x
# smooth the hair weights along each lock (neighbour average over hair vertices), 4 influences
hair_v = [v for v in bm.verts if v[kl] == 3]
for it in range(cfg.get('hair_smooth', 8)):
    new_w = {}
    for v in hair_v:
        acc = dict(v[dl].items())
        nb = [e.other_vert(v) for e in v.link_edges if e.other_vert(v)[kl] == 3]
        for u_ in nb:
            for g, x in u_[dl].items():
                acc[g] = acc.get(g, 0) + x
        new_w[v] = norm4({g: x / (len(nb) + 1) for g, x in acc.items()})
    for v, w in new_w.items():
        v[dl].clear()
        for g, x in w.items():
            v[dl][g] = x
bm.to_mesh(body.data)
bm.free()
bpy.data.objects.remove(ho)
me = body.data
for p in me.polygons:
    p.use_smooth = True
rep['tris'] = sum(len(p.vertices) - 2 for p in me.polygons)
rep['head_faces'] = int(sum(d.value for d in me.attributes['head'].data))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(rep, open(REP, 'w'), indent=1, default=str)
print('GRAFT', json.dumps(rep, default=str))
