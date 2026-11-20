"""Raw Meshy parts -> symmetric labelled figure, Blender frame (faces -Y, z up, floor 0). The robe is rebuilt as a regular grid r(theta, z) sampled from Meshy's outer surface (its shell is two-walled, with slits);
paired parts: the +x part mirrored; midline parts bisected, +x half mirrored; head from the head-only model. Args: <body npz> <head npz> <out npz>"""
import bpy, bmesh, sys, os, math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
BODY, HEAD, OUT = sys.argv[sys.argv.index('--') + 1:]
D = np.load(BODY); co, tri, comp = D['co'], D['tri'], D['comp']
H = np.load(HEAD); hco, htri, hcomp = H['co'], H['tri'], H['comp']
bpy.ops.wm.read_factory_settings(use_empty=True)
coll = bpy.context.scene.collection
def make(name, comps, src=(co, tri, comp)):
    c, t, k = src; keep = np.isin(k, comps); idx = -np.ones(len(c), int); idx[keep] = np.arange(keep.sum())
    tt = idx[t[keep[t[:, 0]]]]
    me = bpy.data.meshes.new(name); me.from_pydata(c[keep].tolist(), [], tt.tolist()); me.update()
    o = bpy.data.objects.new(name, me); coll.objects.link(o)
    bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
    return o
def mirror_mid(o, keep_positive=True, x0=0.0):
    me = o.data; bm = bmesh.new(); bm.from_mesh(me)
    for v in bm.verts: v.co.x -= x0
    g = list(bm.verts) + list(bm.edges) + list(bm.faces)
    bmesh.ops.bisect_plane(bm, geom=g, plane_co=(0, 0, 0), plane_no=(1, 0, 0), clear_outer=not keep_positive, clear_inner=keep_positive, dist=1e-5)
    for v in bm.verts:
        if abs(v.co.x) < 1e-4: v.co.x = 0
    g = list(bm.verts) + list(bm.edges) + list(bm.faces)
    bmesh.ops.mirror(bm, geom=g, axis='X', merge_dist=1e-4)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me); bm.free()
def pair(name, comps, x0=None):
    o = make(name, comps); me = o.data; bm = bmesh.new(); bm.from_mesh(me)
    g = list(bm.verts) + list(bm.edges) + list(bm.faces)
    ret = bmesh.ops.duplicate(bm, geom=g)
    vs = [e for e in ret['geom'] if isinstance(e, bmesh.types.BMVert)]; fs = [e for e in ret['geom'] if isinstance(e, bmesh.types.BMFace)]
    for v in vs: v.co.x = -v.co.x
    bmesh.ops.reverse_faces(bm, faces=fs)
    bm.to_mesh(me); bm.free(); return o
parts = {}
# ---- robe grid
NC = int(os.environ.get('NC', '30'))           # columns on one half, front centre to back centre
ZS = np.array([1.170, 1.13, 1.09, 1.04, 0.98, 0.91, 0.84, 0.76, 0.68, 0.60, 0.52, 0.44, 0.36, 0.28, 0.20, 0.13, 0.07, 0.03, 0.0])
rb = make('rawrobe', [0])
bm = bmesh.new(); bm.from_mesh(rb.data); tree = BVHTree.FromBMesh(bm); bm.free()
th = np.linspace(0, math.pi, NC + 1)                     # 0 front (-y), pi back (+y), through +x
ax_y = 0.0
R = np.zeros((len(ZS), NC + 1))
for j, z in enumerate(ZS):
    zz = max(float(z), 0.006)
    for i, t in enumerate(th):
        d = Vector((math.sin(t), -math.cos(t), 0)); o_ = Vector((0, ax_y, zz)) + d * 1.2
        hit = tree.ray_cast(o_, -d, 1.3)
        R[j, i] = (Vector((0, ax_y, zz)) - o_).length - 0 if hit[0] is None else (hit[0] - Vector((0, ax_y, zz))).length
        if hit[0] is None: R[j, i] = float('nan')
print('robe rays nan', int(np.isnan(R).sum()), 'r hem', np.nanmin(R[-1]), np.nanmax(R[-1]))
R = np.where(np.isnan(R), np.nanmedian(R, axis=1, keepdims=True), R)
def med3(A):
    P_ = np.pad(A, 1, mode='edge'); St = np.stack([P_[1 + dj: 1 + dj + A.shape[0], 1 + di: 1 + di + A.shape[1]] for dj in (-1, 0, 1) for di in (-1, 0, 1)], 0)
    return np.median(St, 0)
def blur(A, k_j=(0.1, 0.8, 0.1), k_i=(0.08, 0.84, 0.08)):
    P_ = np.pad(A, 1, mode='edge')
    B_ = sum(k_j[d + 1] * P_[1 + d: 1 + d + A.shape[0], 1: 1 + A.shape[1]] for d in (-1, 0, 1))
    P_ = np.pad(B_, 1, mode='edge')
    return sum(k_i[d + 1] * P_[1: 1 + A.shape[0], 1 + d: 1 + d + A.shape[1]] for d in (-1, 0, 1))
M = med3(R); slit = np.abs(R - M) > 0.012
print('slit samples', int(slit.sum()))
R = np.where(slit, M, R); R = blur(R)
# the back and front centres are mirror lines: flat in theta there, or the ring has a crease
for k_ in range(3):
    for e_ in (0, -1):
        n1 = 1 if e_ == 0 else -2; n2 = 2 if e_ == 0 else -3
        R[:, e_] = (2 * R[:, n1] + R[:, n2]) / 3
    R[:, 1] = 0.5 * R[:, 1] + 0.25 * (R[:, 0] + R[:, 2]); R[:, -2] = 0.5 * R[:, -2] + 0.25 * (R[:, -1] + R[:, -3])
# the bell: MM9's hem is narrower across and has a train behind
H_ = np.clip((1.165 - ZS) / 1.165, 0, 1)
gv = np.stack([np.sin(th), -np.cos(th)], 1)            # unit x, y
sx = 1 - 0.24 * H_ ** 1.4; syf = 1 - 0.10 * H_ ** 1.4; syb = 1 + 0.42 * H_ ** 1.6
Xg = np.zeros(R.shape + (3,))
for j in range(len(ZS)):
    x = R[j] * gv[:, 0] * sx[j]; y = R[j] * gv[:, 1]; y = np.where(y > 0, y * syb[j], y * syf[j])
    Xg[j, :, 0] = x; Xg[j, :, 1] = y; Xg[j, :, 2] = ZS[j]
Xg[:, 0, 0] = 0; Xg[:, -1, 0] = 0
full = np.concatenate([Xg, (Xg * [-1, 1, 1])[:, -2:0:-1]], 1)         # columns round the ring, front -> +x -> back -> -x
nc = full.shape[1]; nr = full.shape[0]
rv = full.reshape(-1, 3).tolist(); rf = []
vid = lambda j, i: j * nc + i % nc
for j in range(nr - 1):
    for i in range(nc):
        rf.append((vid(j, i), vid(j + 1, i), vid(j + 1, i + 1), vid(j, i + 1)))     # outward
me = bpy.data.meshes.new('robe'); me.from_pydata(rv, [], rf); me.update()
ob = bpy.data.objects.new('robe', me); coll.objects.link(ob); parts['robe'] = ob
np.save(OUT.replace('.npz', '_robegrid.npy'), full)
bpy.data.objects.remove(rb)
# robe lining: an inner wall inside every pleat valley, hem to z 0.60, a rim, then a dark cap across the tube
rows_l = [len(ZS) - 1] + [int(np.argmin(np.abs(ZS - z_))) for z_ in (0.28, 0.44, 0.60)]
lr = full[rows_l]; ctr_ = lr.mean(1, keepdims=True); d_ = lr - ctr_; d_[..., 2] = 0
rad = np.linalg.norm(d_, axis=2); n_c = rad.shape[1]
rmin = np.min(np.stack([np.roll(rad, k, axis=1) * (1 + 0.004 * abs(k)) for k in range(-4, 5)], 0), 0) - 0.012
lr2 = ctr_ + d_ / rad[..., None] * rmin[..., None]; lr2[..., 2] = lr[..., 2]
XR = np.concatenate([full[-1:], lr2, ctr_[-1:] + (lr2[-1:] - ctr_[-1:]) * 0.5, np.repeat(ctr_[-1:], nc, 1)], 0)
# ---- midline
for nm, cs in (('torso', [2]), ('neckin', [17]), ('trim', [8]), ('belt', [9]), ('buckle', [16])):
    o = make(nm, cs); parts[nm] = o; mirror_mid(o)
o = make('pendant', [18, 20, 21]); parts['pendant'] = o
for nm, cs in (('hands', [4]), ('cuffs', [10])):
    parts[nm] = pair(nm, cs)
# ---- sleeve grid: outer wall r(phi, u) along the arm axis, u = 1 at the cuff edge (Meshy's wall is doubled at the cuff with a gap behind it); lining over the outer half, closed round the forearm tube
S_ = Vector((0.211, -0.02, 1.487)); W_ = Vector((0.475, -0.101, 1.026)); a_ = (W_ - S_).normalized()
e1 = a_.cross(Vector((0, 1, 0))).normalized(); e2 = a_.cross(e1).normalized()
sl = make('rawsleeve', [6]); bm = bmesh.new(); bm.from_mesh(sl.data); tree = BVHTree.FromBMesh(bm); bm.free()
NP = int(os.environ.get('NP', '22')); NU = 11
phis = np.linspace(0, 2 * math.pi, NP, endpoint=False); T0 = -0.05
def wall(t, ph):
    c = S_ + a_ * t; d = e1 * math.cos(ph) + e2 * math.sin(ph)
    h = tree.ray_cast(c + d * 0.5, -d, 0.5)
    return None if h[0] is None else (h[0] - c).length
TE = np.zeros(NP)
for k, ph in enumerate(phis):
    t = 0.75
    while t > 0.2 and wall(t, ph) is None: t -= 0.004
    TE[k] = t
for _ in range(2): TE = 0.5 * TE + 0.25 * (np.roll(TE, 1) + np.roll(TE, -1))
US = np.linspace(0, 1, NU + 1); RS = np.zeros((NU + 1, NP))
for j, u in enumerate(US):
    for k, ph in enumerate(phis):
        t = T0 + (TE[k] - 0.006 - T0) * u
        r = wall(t, ph); RS[j, k] = float('nan') if r is None else r
RS = np.where(np.isnan(RS), np.nanmedian(RS, axis=1, keepdims=True), RS)
for _ in range(1): RS = 0.6 * RS + 0.2 * (np.roll(RS, 1, axis=1) + np.roll(RS, -1, axis=1))
print('sleeve t_end', TE.min(), TE.max(), 'r', RS.min(), RS.max())
def ss_v(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)
XS = np.zeros((NU + 1, NP, 3))
for j, u in enumerate(US):
    for k, ph in enumerate(phis):
        t = T0 + (TE[k] - 0.006 - T0) * u; sc_ = 1 - float(os.environ.get('CUFF', '0.26')) * float(ss_v(t, 0.22, 0.60))
        c = S_ + a_ * t; d = e1 * math.cos(ph) + e2 * math.sin(ph); XS[j, k] = np.array(c + d * RS[j, k] * sc_)
bpy.data.objects.remove(sl)
def grid_mesh(name, X, flip=False, closed=True):
    nr, nc_ = X.shape[:2]; rv_ = X.reshape(-1, 3).tolist(); rf_ = []
    idf = lambda j, i: j * nc_ + i % nc_
    for j in range(nr - 1):
        for i in range(nc_ if closed else nc_ - 1):
            q = (idf(j, i), idf(j + 1, i), idf(j + 1, i + 1), idf(j, i + 1))
            rf_.append(q[::-1] if flip else q)
    m_ = bpy.data.meshes.new(name); m_.from_pydata(rv_, [], rf_); m_.update()
    o_ = bpy.data.objects.new(name, m_); coll.objects.link(o_); return o_
def join_mirror(o):
    bm = bmesh.new(); bm.from_mesh(o.data); g = list(bm.verts) + list(bm.edges) + list(bm.faces)
    ret = bmesh.ops.duplicate(bm, geom=g)
    for e in ret['geom']:
        if isinstance(e, bmesh.types.BMVert): e.co.x = -e.co.x
    bmesh.ops.reverse_faces(bm, faces=[e for e in ret['geom'] if isinstance(e, bmesh.types.BMFace)])
    bm.to_mesh(o.data); bm.free()
o = grid_mesh('sleeves', XS)
bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(o.data); bm.free()
join_mirror(o); parts['sleeves'] = o
# lining: inner copy of the cuff end, a rim strip at the edge, then in to the forearm
LI = XS[[7, 9, 11]].copy(); ctr = np.array([np.array(S_ + a_ * (T0 + (TE[k] - 0.006 - T0) * 0.0)) for k in range(NP)])
for j in range(LI.shape[0]):
    tmean = (T0 + (TE - 0.006 - T0) * US[[7, 9, 11][j]])
    cc = np.array([np.array(S_ + a_ * t) for t in tmean]); LI[j] = cc + (LI[j] - cc) * 0.965
cc0 = np.array([np.array(S_ + a_ * t) for t in (T0 + (TE - 0.006 - T0) * US[7])])
inner = cc0 + (LI[0] - cc0) * 0.22                       # closes on the forearm tube
XL = np.concatenate([XS[-1:], LI[::-1], inner[None]], 0)    # rim edge, lining from the cuff back to the elbow side, annulus
o = grid_mesh('slining', XL, flip=False)
bm = bmesh.new(); bm.from_mesh(o.data)
for f in bm.faces: f.normal_update()
inward = sum(((f.calc_center_median() - Vector(S_ + a_ * 0.45)).dot(f.normal) for f in bm.faces if abs((f.calc_center_median() - S_).dot(a_) - 0.45) < 0.1), 0.0)
print('lining inward score', inward)
if inward > 0: bmesh.ops.reverse_faces(bm, faces=bm.faces)
bm.to_mesh(o.data); bm.free(); join_mirror(o); parts['slining'] = o
# feet: legs cut at a true plane
o = make('feet', [3]); bm = bmesh.new(); bm.from_mesh(o.data)
bmesh.ops.bisect_plane(bm, geom=list(bm.verts) + list(bm.edges) + list(bm.faces), plane_co=(0, 0, float(os.environ.get('SHIN', '0.30'))), plane_no=(0, 0, 1), clear_outer=True, dist=1e-5)
bm.to_mesh(o.data); bm.free(); mirror_mid(o); parts['feet'] = o
# the forearm tube stays inside the narrowed sleeve
for v in parts['cuffs'].data.vertices:
    sg = 1 if v.co.x > 0 else -1; q = Vector((v.co.x * sg, v.co.y, v.co.z)); t = (q - S_).dot(a_); c = S_ + a_ * t; n_ = c + (q - c) * 0.72; v.co = Vector((n_.x * sg, n_.y, n_.z))
# ---- head: scale from MM9's ear span, placed by the eyes
HS = float(os.environ.get('HSCALE', '0.76'))
Eh = np.array([hco[hcomp == 2].mean(0), hco[hcomp == 3].mean(0)])
xm = Eh[:, 0].mean(); EZ = float(os.environ.get('EYEZ', '1.775')); EY = float(os.environ.get('EYEY', '-0.155'))
hq = (hco - [xm, 0, 0]) * HS + np.array([0, EY - Eh[:, 1].mean() * HS, EZ - Eh[:, 2].mean() * HS])
print('HEAD mid x', xm, 'z range', hq[:, 2].min(), hq[:, 2].max(), 'y', hq[:, 1].min(), hq[:, 1].max(), 'eye dist', np.linalg.norm(Eh[1] - Eh[0]) * HS)
hs = (hq, htri, hcomp)
parts['head'] = make('head', [0, 1], hs); mirror_mid(parts['head'], keep_positive=False)
bm = bmesh.new(); bm.from_mesh(parts['head'].data); n0_ = len(bm.verts)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0022)
bd_ = [e for e in bm.edges if e.is_boundary]; print('head merged', n0_, '->', len(bm.verts), 'boundary', len(bd_))
bmesh.ops.holes_fill(bm, edges=bd_, sides=10)
bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(parts['head'].data); bm.free()
if os.environ.get('VOX', '0') != '0':       # voxel skin: the two Meshy shells and their slits become one surface
    o = parts['head']; bpy.context.view_layer.objects.active = o
    for x in bpy.data.objects: x.select_set(x is o)
    m = o.modifiers.new('r', 'REMESH'); m.mode = 'VOXEL'; m.voxel_size = float(os.environ.get('VOX', '0.0015')); m.use_smooth_shade = True
    bpy.ops.object.modifier_apply(modifier='r')
    print('head voxel verts', len(o.data.vertices), 'polys', len(o.data.polygons))
    bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.triangulate(bm, faces=bm.faces); bm.to_mesh(o.data); bm.free()
    mirror_mid(o, keep_positive=False)
o = make('eyes', [2, 3], hs); parts['eyes'] = o
bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.x > 0], context='VERTS')
g = list(bm.verts) + list(bm.edges) + list(bm.faces); ret = bmesh.ops.duplicate(bm, geom=g)
for e in ret['geom']:
    if isinstance(e, bmesh.types.BMVert): e.co.x = -e.co.x
bmesh.ops.reverse_faces(bm, faces=[e for e in ret['geom'] if isinstance(e, bmesh.types.BMFace)]); bm.to_mesh(o.data); bm.free()
# teeth: Meshy's are 5 mm beads, and one row lies on the chin; sharp cones on its sites of the two real rows, MM9's jagged snarl
sites = []
for c_ in range(4, 30):
    q = hq[hcomp == c_]; z_ = hco[hcomp == c_, 2].mean()
    if z_ < 0.13: continue                                # the stray row
    sites.append((q.mean(0), z_ > 0.165))
keep_ = [x for x in sites if x[0][0] <= 1e-3]
TV = []; TF = []
def cone(p, up, base, length, nrm):
    # four-sided cone, root in the gum, tip to the other jaw
    tip = p + np.array([0, 0, -length if up else length]); ax_ = np.array([1.0, 0, 0]); ay_ = np.array([0, 1.0, 0])
    root = p + np.array([0, 0, 0.004 if up else -0.004])
    i0 = len(TV)
    for dx, dy in ((1, 0), (0, 1), (-1, 0), (0, -1)): TV.append((root + ax_ * dx * base + ay_ * dy * base * 0.8).tolist())
    TV.append(tip.tolist())
    for k in range(4):
        a, b = i0 + k, i0 + (k + 1) % 4
        TF.append((a, b, i0 + 4) if up else (b, a, i0 + 4))
xs = [abs(x[0][0]) for x in keep_]
for p_, up_ in keep_:
    ax = abs(p_[0]); canine = 0.012 < ax < 0.024
    L_ = (0.0135 if canine else 0.0075) * (1.0 if up_ else 0.85); B_ = 0.0050 if canine else 0.0040
    for sgn in ((1, -1) if ax > 1e-3 else (1,)):
        q_ = p_ * [sgn, 1, 1]; cone(q_, up_, B_, L_, None)
print('teeth', len(TF), 'tris', len(keep_), 'sites on one side')
me = bpy.data.meshes.new('teeth'); me.from_pydata(TV, [], TF); me.update(); o = bpy.data.objects.new('teeth', me); coll.objects.link(o); parts['teeth'] = o
bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
# mouth plug: behind the teeth the head shell is open to the skull's far wall; a dark dome closes it
eyec = np.array([0, Eh[:, 1].mean(), Eh[:, 2].mean()]); cy = np.array([np.mean([x[0][1] for x in sites]), np.mean([x[0][2] for x in sites])])
bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=6, radius=1.0)
for v in bm.verts: v.co = Vector((v.co.x * 0.040, cy[0] + 0.040 + v.co.y * 0.028, cy[1] + v.co.z * 0.030))
me = bpy.data.meshes.new('plug'); bm.to_mesh(me); bm.free(); o = bpy.data.objects.new('plug', me); coll.objects.link(o); parts['plug'] = o
bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.triangulate(bm, faces=bm.faces); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
o = grid_mesh('rlining', XR, flip=False)
bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5); bm.to_mesh(o.data); bm.free(); parts['rlining'] = o
for o in parts.values():
    for p in o.data.polygons: p.use_smooth = True
BUDGET = dict(robe=99999, sleeves=99999, slining=99999, rlining=99999, plug=99999, teeth=99999, torso=1100, neckin=120, trim=260, belt=260, buckle=120, pendant=160, hands=1500, cuffs=220, feet=380, head=4300, eyes=160)
# the skull's back and the ears go first, the face keeps the density
o = parts['head']; vg = o.vertex_groups.new(name='far')
for v in o.data.vertices:
    near = v.co.y < -0.02 and abs(v.co.x) < 0.085 and v.co.z < EZ + 0.045
    vg.add([v.index], 0.3 if near else 1.0, 'REPLACE')
bpy.context.view_layer.objects.active = o
for x in bpy.data.objects: x.select_set(x is o)
m = o.modifiers.new('d0', 'DECIMATE'); m.decimate_type = 'COLLAPSE'; m.ratio = BUDGET['head'] / sum(len(p.vertices) - 2 for p in o.data.polygons); m.vertex_group = 'far'; m.vertex_group_factor = 1.0; m.use_symmetry = True; m.symmetry_axis = 'X'; m.use_collapse_triangulate = True
bpy.ops.object.modifier_apply(modifier='d0')
bm = bmesh.new(); bm.from_mesh(o.data)
dome = [v for v in bm.verts if (v.co.z > EZ + 0.035 and abs(v.co.x) < 0.098) or (v.co.y > 0.0 and abs(v.co.x) < 0.09 and v.co.z > EZ - 0.09)]
bmesh.ops.smooth_vert(bm, verts=dome, factor=0.5, use_axis_x=True, use_axis_y=True, use_axis_z=True)
bmesh.ops.smooth_vert(bm, verts=dome, factor=0.5, use_axis_x=True, use_axis_y=True, use_axis_z=True)
bm.to_mesh(o.data); bm.free()
print('head after far pass', sum(len(p.vertices) - 2 for p in o.data.polygons))
def tris(o): return sum(len(p.vertices) - 2 for p in o.data.polygons)
total = 0
for nm, o in parts.items():
    t0 = tris(o)
    if not os.environ.get('NOREDUCE') and t0 > BUDGET[nm] * 1.02:
        bpy.context.view_layer.objects.active = o
        for x in bpy.data.objects: x.select_set(x is o)
        m = o.modifiers.new('d', 'DECIMATE'); m.decimate_type = 'COLLAPSE'; m.ratio = BUDGET[nm] / t0; m.use_symmetry = True; m.symmetry_axis = 'X'; m.use_collapse_triangulate = True
        bpy.ops.object.modifier_apply(modifier='d')
    print('PART', nm, t0, '->', tris(o)); total += tris(o)
print('TOTAL tris', total)
# the collar flares away from the neck as MM9's does
def ss_(x, a, b):
    t = min(max((x - a) / (b - a), 0.0), 1.0); return t * t * (3 - 2 * t)
for nm in ('torso', 'neckin', 'trim'):
    for v in parts[nm].data.vertices:
        if abs(v.co.x) < 0.16 and v.co.z > 1.56:
            k = 1 + float(os.environ.get('FLARE', '0.34')) * ss_(v.co.z, 1.585, 1.70); y0 = -0.02
            v.co.x *= k; v.co.y = y0 + (v.co.y - y0) * k
names = list(parts); Co = []; Tr = []; Pa = []; base = 0
for k, nm in enumerate(names):
    o = parts[nm]; me = o.data
    me.calc_loop_triangles()
    c = np.array([v.co[:] for v in me.vertices]); t = np.array([lt.vertices[:] for lt in me.loop_triangles])
    Co.append(c); Tr.append(t + base); Pa.append(np.full(len(c), k)); base += len(c)
np.savez(OUT, co=np.vstack(Co), tri=np.vstack(Tr), comp=np.concatenate(Pa), names=np.array(names))
print('SAVED', base)
