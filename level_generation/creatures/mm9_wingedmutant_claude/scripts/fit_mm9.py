"""Fit the Meshy Smart Topology mesh onto the ORIGINAL MM9 bind pose (skeleton unchanged): global similarity, then
an articulated pose correction by joint-pivoted segment rotations blended like skinning.

Args: <mm9 ground blend> <meshy glb> <config json> <out blend> <report json>

1. Global: uniform scale from the bounding-box height, centred, a yaw search (the masters face the camera, so Meshy
   normally returns yaw 0), then symmetric nearest-point ICP (scale + translation).
2. Articulated correction (config 'segments', root to tip; each names its pivot joint and its MM9 bones): every
   Meshy vertex is labelled by the nearest MM9 vertex (lateral segments only take vertices on their own side); for
   each segment a rotation about its pivot joint is solved (Kabsch on symmetric nearest points between the segment's
   Meshy vertices and its MM9 vertices, clamped to config 'max_deg'), composed with its parent's; the segment labels
   are diffused along the mesh and every vertex moves by the weight blend of the segment transforms (no tearing at
   joints). Optional 'stretch': the segment is also scaled along its pivot -> child-joint axis so its length matches.
   Repeated 'iterations' times.
3. Separate small components (teeth, spikes: < 'small_verts') move rigidly with their centroid's blend.
Per-vertex attributes for rig_mm9.py: 'piece' (0 body, 2 small piece) and 'side' (-1/0/1 of the x coordinate).
"""
import bpy, bmesh, sys, json, math
import numpy as np
from mathutils import Vector, Matrix
from mathutils.kdtree import KDTree

argv = sys.argv[sys.argv.index('--') + 1:]
SRC, MESHY, CFGF, OUT, REP = argv
cfg = json.load(open(CFGF))
SMALL = cfg.get('small_verts', 150)
SIDE_X = cfg.get('side_x', 0.04)

bpy.ops.wm.open_mainfile(filepath=SRC)
sc = bpy.context.scene
arm = bpy.data.objects['MM9_Rig']
J = {b.name: Vector(b.head_local) for b in arm.data.bones}
mm9_p, mm9_l = [], []
for o in bpy.data.objects:
    if o.type != 'MESH':
        continue
    for v in o.data.vertices:
        if not v.groups:
            continue
        g = max(v.groups, key=lambda g: g.weight)
        mm9_p.append(o.matrix_world @ v.co)
        mm9_l.append(o.vertex_groups[g.group].name)
A = np.array([tuple(p) for p in mm9_p])
lab = np.array(mm9_l)


def kdt(P):
    k = KDTree(len(P))
    for i, p in enumerate(P):
        k.insert(Vector(p), i)
    k.balance()
    return k


kA = kdt(A)
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=MESHY)
new = [o for o in bpy.data.objects if o not in before]
bm = bmesh.new()
for o in new:
    if o.type == 'MESH':
        tmp = bmesh.new(); tmp.from_mesh(o.data); tmp.transform(o.matrix_world)
        me_t = bpy.data.meshes.new('t'); tmp.to_mesh(me_t); bm.from_mesh(me_t); tmp.free()
for o in new:
    bpy.data.objects.remove(o)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
bm.verts.ensure_lookup_table()
B0 = np.array([tuple(v.co) for v in bm.verts])
rep = {'meshy_verts': len(B0)}


def chamfer(X, sub=2500):
    rng = np.random.default_rng(1)
    Xs = X[rng.choice(len(X), min(sub, len(X)), replace=False)]
    d1 = np.mean([kA.find(Vector(x))[2] for x in Xs])
    kX = kdt(Xs)
    d2 = np.mean([kX.find(Vector(a))[2] for a in A[::max(1, len(A) // sub)]])
    return d1 + d2


def place(B, yaw):
    c, s_ = math.cos(yaw), math.sin(yaw)
    R = np.array([[c, -s_, 0], [s_, c, 0], [0, 0, 1]])
    X = B @ R.T
    s = (A[:, 2].max() - A[:, 2].min()) / (X[:, 2].max() - X[:, 2].min())
    t = np.array([(A[:, 0].min() + A[:, 0].max()) / 2 - s * (X[:, 0].min() + X[:, 0].max()) / 2,
                  (A[:, 1].min() + A[:, 1].max()) / 2 - s * (X[:, 1].min() + X[:, 1].max()) / 2,
                  A[:, 2].min() - s * X[:, 2].min()])
    return s * X + t


yaws = [math.radians(d) for d in range(-180, 180, 15)]
scores = [(chamfer(place(B0, y)), y) for y in yaws]
best = min(scores)
y0 = best[1]
for d in np.linspace(-12, 12, 9):
    y = y0 + math.radians(d)
    sc_ = chamfer(place(B0, y))
    if sc_ < best[0]:
        best = (sc_, y)
yaw = best[1] if cfg.get('yaw_search', True) else 0.0
rep['yaw_deg'] = math.degrees(yaw)
rep['yaw_scores'] = {round(math.degrees(y)): round(s, 4) for s, y in scores}
X = place(B0, yaw)

# global ICP: scale + translation
rng = np.random.default_rng(0)
for _ in range(cfg.get('global_icp', 25)):
    Xs_i = rng.choice(len(X), min(3000, len(X)), replace=False)
    Xs = X[Xs_i]
    kX = kdt(Xs)
    p = list(Xs); q = [A[kA.find(Vector(x))[1]] for x in Xs]
    for a in A[::max(1, len(A) // 3000)]:
        p.append(Xs[kX.find(Vector(a))[1]]); q.append(a)
    p, q = np.array(p), np.array(q)
    mp, mq = p.mean(0), q.mean(0)
    P0, Q0 = p - mp, q - mq
    s = float((Q0 * P0).sum() / (P0 * P0).sum()) if cfg.get('global_scale_icp', True) else 1.0
    X = s * (X - mp) + mq
rep['global_chamfer'] = chamfer(X)
for v, x in zip(bm.verts, X):
    v.co = Vector(x)

# dropped components (config 'drop': [{comp_min, comp_max, centroid box [x0,x1,y0,y1,z0,z1], min_xspan}]), e.g.
# Meshy wings that are replaced by wings built on the MM9 wing geometry (build_wings.py)
if cfg.get('drop'):
    seen_ = set(); dropped = []
    for v in bm.verts:
        if v.index in seen_:
            continue
        st = [v]; seen_.add(v.index); c = []
        while st:
            x_ = st.pop(); c.append(x_)
            for e in x_.link_edges:
                y_ = e.other_vert(x_)
                if y_.index not in seen_:
                    seen_.add(y_.index); st.append(y_)
        P_ = np.array([tuple(q.co) for q in c]); m_ = P_.mean(0)
        for rule in cfg['drop']:
            bx = rule.get('box', [-1e9, 1e9] * 3)
            if (rule.get('comp_min', 0) <= len(c) <= rule.get('comp_max', 1e9)
                    and bx[0] <= m_[0] <= bx[1] and bx[2] <= m_[1] <= bx[3] and bx[4] <= m_[2] <= bx[5]
                    and np.ptp(P_[:, 0]) >= rule.get('min_xspan', 0)):
                dropped.append(c); break
    rep['dropped_components'] = [len(c) for c in dropped]
    bmesh.ops.delete(bm, geom=[q for c in dropped for q in c], context='VERTS')
    bm.verts.ensure_lookup_table(); bm.verts.index_update()
    X = np.array([tuple(v.co) for v in bm.verts])

# components
seen = {}
comps = []
for v in bm.verts:
    if v.index in seen:
        continue
    st = [v]; seen[v.index] = len(comps); c = []
    while st:
        x = st.pop(); c.append(x.index)
        for e in x.link_edges:
            y = e.other_vert(x)
            if y.index not in seen:
                seen[y.index] = len(comps); st.append(y)
    comps.append(c)
comps.sort(key=len, reverse=True)
n = len(bm.verts)
piece = np.zeros(n, int)
comp_of = np.zeros(n, int)
for ci, c in enumerate(comps):
    comp_of[c] = ci
    if len(c) < SMALL:
        piece[c] = 2
rep['components'] = [len(c) for c in comps][:40]
nbr = [[] for _ in range(n)]
for e in bm.edges:
    a, b = e.verts[0].index, e.verts[1].index
    nbr[a].append(b); nbr[b].append(a)

segs = cfg['segments']
seg_names = [sg['name'] for sg in segs]
bone_seg = {}
for k, sg in enumerate(segs):
    for b in sg['bones']:
        bone_seg[b] = k
seg_side = []
for sg in segs:
    xs = [J[b].x for b in sg['bones']]
    m = float(np.mean(xs))
    seg_side.append(0 if abs(m) < SIDE_X else int(np.sign(m)))
lab_seg = np.array([bone_seg.get(b, -1) for b in lab])
parent = [seg_names.index(sg['parent']) if sg.get('parent') else -1 for sg in segs]
rep['segments'] = {}


# forced regions (config 'force': [{segment, box [x0,x1,y0,y1,z0,z1], comp_max}]): vertices of components up to
# comp_max vertices inside the box belong to that segment's family (it and its descendants), e.g. wings that Meshy
# built in another plane than MM9, too far for nearest-vertex labels. Iteration 0 labels them the root segment and
# aligns its far point first; later iterations label them by the nearest MM9 vertex of the family.
forced = np.full(n, -1)
comp_len = np.array([len(comps[c]) for c in comp_of])
for rule in cfg.get('force', []):
    k = seg_names.index(rule['segment'])
    x0, x1, y0, y1, z0, z1 = rule['box']
    ok = ((X[:, 0] >= x0) & (X[:, 0] <= x1) & (X[:, 1] >= y0) & (X[:, 1] <= y1) & (X[:, 2] >= z0) & (X[:, 2] <= z1)
          & (comp_len <= rule.get('comp_max', 10 ** 9)) & (comp_len >= rule.get('comp_min', 0)))
    forced[ok] = k
    rep.setdefault('forced', {})[rule['segment']] = int(ok.sum())


def family(k):
    out = {k}
    for j, pj in enumerate(parent):
        if pj in out:
            out.add(j)
    for _ in range(5):
        for j, pj in enumerate(parent):
            if pj in out:
                out.add(j)
    return out


def labels(X, it=0):
    """segment label per Meshy vertex from the nearest MM9 vertex; lateral segments only on their own side"""
    Lf = labels_free(X)
    for k in set(forced[forced >= 0]):
        ids = np.nonzero(forced == k)[0]
        if it == 0:
            Lf[ids] = k
            continue
        fam = family(k)
        aidx = np.nonzero(np.isin(lab_seg, list(fam)))[0]
        kt = kdt(A[aidx])
        for i in ids:
            Lf[i] = lab_seg[aidx[kt.find(Vector(X[i]))[1]]]
    return Lf


def labels_free(X):
    side_v = np.where(np.abs(X[:, 0]) < SIDE_X, 0, np.sign(X[:, 0])).astype(int)
    trees = {}
    for sd in (-1, 0, 1):
        ok = np.array([seg_side[s] in (0, sd) or sd == 0 if s >= 0 else True for s in lab_seg])
        ids = np.nonzero(ok)[0]
        trees[sd] = (kdt(A[ids]), ids)
    L = np.zeros(len(X), int)
    for i, x in enumerate(X):
        k, ids = trees[side_v[i]]
        L[i] = lab_seg[ids[k.find(Vector(x))[1]]]
    return L


def diffuse_w(L, iters):
    W = np.zeros((n, len(segs) + 1))
    W[np.arange(n), L + 1] = 1.0  # column 0 = core (-1)
    for _ in range(iters):
        avg = np.array([W[nb].mean(0) if nb else W[i] for i, nb in enumerate(nbr)])
        W = 0.5 * W + 0.5 * avg
    return W


def kabsch(P, Q, pivot):
    P0 = P - pivot; Q0 = Q - pivot
    H = P0.T @ Q0
    U, S_, Vt = np.linalg.svd(H)
    D = np.diag([1, 1, np.sign(np.linalg.det(Vt.T @ U.T))])
    return Vt.T @ D @ U.T


for it in range(cfg.get('iterations', 3)):
    L = labels(X, it)
    T = [np.eye(4) for _ in segs]   # world transforms (composed)
    local = []
    for k, sg in enumerate(segs):
        pk = parent[k]
        Tp = T[pk] if pk >= 0 else np.eye(4)
        piv = np.array(tuple(J[sg['pivot']]))
        ids = np.nonzero((L == k) & (piece == 0))[0]
        aidx = np.nonzero(lab_seg == k)[0]
        if len(ids) < 20 or len(aidx) < 4:
            T[k] = Tp.copy(); local.append(0.0); continue
        P = (np.c_[X[ids], np.ones(len(ids))] @ Tp.T)[:, :3]   # after the parent's move
        R0 = np.eye(3)
        if it == 0 and sg.get('init_align'):
            far_m = P[np.argmax(np.linalg.norm(P - piv, axis=1))] - piv
            Aa = A[aidx] if not sg.get('init_family') else A[np.isin(lab_seg, list(family(k)))]
            far_a = Aa[np.argmax(np.linalg.norm(Aa - piv, axis=1))] - piv
            R0 = np.array(Vector(far_m).rotation_difference(Vector(far_a)).to_matrix())
            P = (P - piv) @ R0.T + piv
            rep['segments'].setdefault(sg['name'], {})['init_deg'] = round(math.degrees(
                Vector(far_m).angle(Vector(far_a))), 1)
        kAs = kdt(A[aidx]); kP = kdt(P)
        pp = list(P); qq = [A[aidx[kAs.find(Vector(x))[1]]] for x in P]
        for a in A[aidx]:
            pp.append(P[kP.find(Vector(a))[1]]); qq.append(a)
        pp, qq = np.array(pp), np.array(qq)
        R = kabsch(pp, qq, piv)
        ang = math.degrees(math.acos(max(-1, min(1, (np.trace(R) - 1) / 2))))
        lim = sg.get('max_deg', cfg.get('max_deg', 35))
        if ang > lim:
            qr = Matrix(R.tolist()).to_quaternion()
            ax_, an_ = qr.to_axis_angle()
            R = np.array(Matrix.Rotation(an_ * lim / ang, 3, ax_))
            ang = lim
        R = R @ R0
        M = np.eye(4)
        M[:3, :3] = R
        M[:3, 3] = piv - R @ piv
        if sg.get('stretch') and sg.get('child'):
            ch = np.array(tuple(J[sg['child']]))
            ax = ch - piv; Lm = np.linalg.norm(ax); ax /= Lm
            Pm = (np.c_[P, np.ones(len(P))] @ M.T)[:, :3]
            ext_m = np.percentile((Pm - piv) @ ax, 97)
            ext_a = np.percentile((A[aidx] - piv) @ ax, 97)
            st = float(np.clip(ext_a / max(ext_m, 1e-6), 0.75, 1.33))
            S = np.eye(4)
            S[:3, :3] += (st - 1) * np.outer(ax, ax)
            S[:3, 3] = piv - S[:3, :3] @ piv
            M = S @ M
            rep['segments'].setdefault(sg['name'], {})['stretch'] = st
        T[k] = M @ Tp
        local.append(ang)
        rep['segments'].setdefault(sg['name'], {})[f'iter{it}_deg'] = round(ang, 2)
        rep['segments'][sg['name']]['verts'] = int(len(ids))
    W = diffuse_w(L, cfg.get('blend_iters', 12))
    Xh = np.c_[X, np.ones(n)]
    newX = W[:, 0:1] * X
    for k in range(len(segs)):
        newX += W[:, k + 1:k + 2] * (Xh @ T[k].T)[:, :3]
    # small pieces rigid: the transform blend at the vertex of the piece nearest the body
    big_ids = np.nonzero(piece == 0)[0]
    kbig = kdt(X[big_ids])
    for c in comps:
        if len(c) >= SMALL:
            continue
        c = np.array(c)
        j = big_ids[min((kbig.find(Vector(X[i])) for i in c), key=lambda r: r[2])[1]]
        Mx = W[j, 0] * np.eye(4) + sum(W[j, k + 1] * T[k] for k in range(len(segs)))
        newX[c] = (Xh[c] @ Mx.T)[:, :3]
    X = newX
    rep[f'chamfer_iter{it}'] = chamfer(X)

for v, x in zip(bm.verts, X):
    v.co = Vector(x)
me = bpy.data.meshes.new('Body')
pl = bm.verts.layers.int.new('piece')
sl = bm.verts.layers.int.new('side')
for v in bm.verts:
    v[pl] = int(piece[v.index])
    v[sl] = 0 if abs(v.co.x) < SIDE_X else (1 if v.co.x > 0 else -1)
bm.to_mesh(me)
obj = bpy.data.objects.new('Body', me)
sc.collection.objects.link(obj)
for p in me.polygons:
    p.use_smooth = True
d = np.array([kA.find(v.co)[2] for v in me.vertices])
rep.update({'verts': len(me.vertices), 'tris': sum(len(p.vertices) - 2 for p in me.polygons),
            'dist_to_mm9_mean': float(d.mean()), 'dist_to_mm9_p90': float(np.percentile(d, 90))})
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(rep, open(REP, 'w'), indent=1, default=str)
print('FIT ' + json.dumps({k: v for k, v in rep.items() if k not in ('yaw_scores',)}, default=str))
