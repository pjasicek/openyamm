"""Fit the Meshy Smart Topology dog to the MM9 DOG.abc bind pose (from mm9_wolf_claude/scripts/fit_quad.py;
lengths scaled by K = 0.35, the dog's size against the MM9 wolf).

Args: <mm9 source blend> <meshy glb> <out blend> <report json>

1. Global: uniform scale from the bounding-box height, centred in x/y, paws on the floor, refined by symmetric
   nearest-point ICP (rotation + scale + translation).
2. Labels: every Meshy vertex takes the bone of the nearest MM9 vertex (the MM9 skin is rigid, one bone per vertex).
3. Head: translation-only ICP of the head (skull, snout, jaw, ears) onto the MM9 head vertices, blended into the neck
   by a weight diffused along the mesh from the head labels.
4. Legs and tail: each MM9 chain (root pivot ... toe or tail tip) is fitted by linear blend skinning
   (fit_chain_lbs): joints estimated on the Meshy limb centreline at the MM9 joint arc fractions, each segment posed
   onto its MM9 segment (minimal rotation, stretch along the segment only), the root blended to rest over BLEND.
Per-vertex attributes: 'piece' (0 body, 2 small separate piece) and 'chain' (-1 core, k = chain index) for rig_body.py.
"""
import bpy, bmesh, sys, json, math, heapq, os
import numpy as np
from mathutils import Vector, Matrix
from mathutils.kdtree import KDTree

argv = sys.argv[sys.argv.index('--') + 1:]
SRC, MESHY, OUT, REP = argv
NB = 40
CHAINS = {
    'leg_fl': ['Xflegpiv01', 'Xfleg01', 'Xfankle01', 'Xffoot01'],   # +X = the dog's left
    'leg_fr': ['Xflegpiv', 'Xfleg', 'Xfankle', 'Xffoot'],
    'leg_hl': ['Xblegpiv01', 'Xbleg01', 'Xblegmid01', 'Xbankle01', 'Xbfoot01'],
    'leg_hr': ['Xblegpiv', 'Xbleg', 'Xblegmid', 'Xbankle', 'Xbfoot'],
    'tail': ['Xtailpiv', 'XtailA', 'XtailB', 'XtailC'],
}
BLEND = {'leg_fl': 0.14, 'leg_fr': 0.14, 'leg_hl': 0.16, 'leg_hr': 0.16, 'tail': 0.08}
TORSO_BONES = ['XCENTER', 'XbackA', 'Xback', 'XbackB', 'XbackC', 'Xfrontleg', 'XneckA', 'XneckB', 'XneckC', 'Xheadpiv', 'Xhead', 'Xmouth', 'Xjawpiv', 'Xearbase', 'Xearpiv', 'Xearbase1', 'Xearpiv1']
K = 0.35   # size against the MM9 wolf (body width 0.8): lengths below are wolf lengths x K
LEG_TOP = 0.1 * K  # leg regions end this far above the MM9 leg root pivot
POSE_SIGMA = 0.12 * K  # transient pose weights: soft-min width over the bone capsule distances
SIGMA = 0.05 * K
HEAD_BONES = ['Xheadpiv', 'Xhead', 'Xmouth', 'Xjawpiv', 'Xearbase', 'Xearpiv', 'Xearbase1', 'Xearpiv1']

bpy.ops.wm.open_mainfile(filepath=SRC)
sc = bpy.context.scene
arm = bpy.data.objects['MM9_Rig']
if arm.animation_data:
    arm.animation_data.action = None
for pb in arm.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
J = {b.name: Vector(b.head_local) for b in arm.data.bones}
mm9_p, mm9_l = [], []
for o in bpy.data.objects:
    if o.type != 'MESH':
        continue
    for v in o.data.vertices:
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


before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=MESHY)
new = [o for o in bpy.data.objects if o not in before]
src = next(o for o in new if o.type == 'MESH')
bm = bmesh.new()
bm.from_mesh(src.data)
bm.transform(src.matrix_world)
for o in new:
    bpy.data.objects.remove(o)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
bm.verts.ensure_lookup_table()
B = np.array([tuple(v.co) for v in bm.verts])
s = (A[:, 2].max() - A[:, 2].min()) / (B[:, 2].max() - B[:, 2].min())
t = np.array([(A[:, 0].min() + A[:, 0].max()) / 2 - s * (B[:, 0].min() + B[:, 0].max()) / 2,
              (A[:, 1].min() + A[:, 1].max()) / 2 - s * (B[:, 1].min() + B[:, 1].max()) / 2,
              A[:, 2].min() - s * B[:, 2].min()])
kA = kdt(A)
rng = np.random.default_rng(0)
Bs = B[rng.choice(len(B), min(3000, len(B)), replace=False)]


def icp_similarity(Bs, Adst, kdst, s, t, iters=30, rotate=False, fixed_scale=False):
    R = np.eye(3)
    for _ in range(iters):
        X = s * Bs @ R.T + t
        kX = kdt(X)
        p, q = [], []
        for i, x in enumerate(X):
            p.append(Bs[i]); q.append(Adst[kdst.find(Vector(x))[1]])
        for a in Adst[::max(1, len(Adst) // 3000)]:
            p.append(Bs[kX.find(Vector(a))[1]]); q.append(a)
        p, q = np.array(p), np.array(q)
        mp, mq = p.mean(0), q.mean(0)
        P0, Q0 = p - mp, q - mq
        if rotate:
            U, S_, Vt = np.linalg.svd(Q0.T @ P0)
            D = np.diag([1, 1, np.sign(np.linalg.det(U @ Vt))])
            R = U @ D @ Vt
        if not fixed_scale:
            s = float((Q0 * (P0 @ R.T)).sum() / (P0 * P0).sum())
        t = mq - s * (R @ mp)
    return s, R, t


NOGLOBAL = os.environ.get('NOGLOBAL') == '1'   # second pass on an already fitted mesh: chains only
if NOGLOBAL:
    s, R, t = 1.0, np.eye(3), np.zeros(3)
elif os.environ.get('GLOBAL_TORSO'):
    # the MM9 bind is no standing pose (cat: front paws 5 cm up, tail below the floor): align the torso and head only.
    # GLOBAL_TORSO = 'zmin,ymax' in Meshy units: the Meshy points above zmin (over the legs) and ahead of ymax (the
    # rump, not the tail); MM9 points labelled with TORSO_BONES
    zmin_b, ymax_b = [float(x) for x in os.environ['GLOBAL_TORSO'].split(',')]
    At = A[np.isin(lab, TORSO_BONES)]
    Bt = B[(B[:, 2] > zmin_b) & (B[:, 1] < ymax_b)]
    s = (At[:, 1].max() - At[:, 1].min()) / (Bt[:, 1].max() - Bt[:, 1].min())
    t = At.mean(0) - s * Bt.mean(0)
    Bts = Bt[rng.choice(len(Bt), min(2500, len(Bt)), replace=False)]
    # yaw and roll: the turn that makes the torso mirror-symmetric (a Meshy body curves; ICP against the low-poly MM9
    # torso turned the cat 17 degrees); then pitch, scale and translation only, the mirror plane on x = 0
    c0 = Bts.mean(0)

    def asym_t(yaw, roll):
        Ry = np.array(Matrix.Rotation(math.radians(yaw), 3, 'Z'))
        Rr = np.array(Matrix.Rotation(math.radians(roll), 3, 'Y'))
        X = (Bts - c0) @ (Rr @ Ry).T
        k = kdt(X)
        cx = 0.0
        for _ in range(3):
            M = X.copy(); M[:, 0] = 2 * cx - M[:, 0]
            idx = np.array([k.find(Vector(m))[1] for m in M])
            cx = float(((X[idx, 0] + X[:, 0]) / 2).mean())
        M = X.copy(); M[:, 0] = 2 * cx - M[:, 0]
        return float(np.mean([k.find(Vector(m))[2] for m in M])), cx
    # GLOBAL_PAWS = zcut (Meshy units): the midline from the paws instead (the four lowest parts below zcut; torso
    # symmetry alone is ill-determined): yaw from the hind -> front midpoints, no roll
    if os.environ.get('GLOBAL_PAWS'):
        zc_ = float(os.environ['GLOBAL_PAWS'])
        ids_ = np.nonzero(B[:, 2] < zc_)[0]
        idset = set(int(i) for i in ids_)
        seen_p, parts_p = set(), []
        for i0 in ids_:
            i0 = int(i0)
            if i0 in seen_p:
                continue
            st, cc = [i0], []
            seen_p.add(i0)
            while st:
                x_ = st.pop(); cc.append(x_)
                for e in bm.verts[x_].link_edges:
                    y_ = e.other_vert(bm.verts[x_]).index
                    if y_ in idset and y_ not in seen_p:
                        seen_p.add(y_); st.append(y_)
            parts_p.append(cc)
        parts_p = [c for c in parts_p if len(c) > 30]
        parts_p.sort(key=lambda c: B[c, 2].min())
        cen_p = np.array([B[c].mean(0) for c in parts_p[:4]])
        cen_p = cen_p[np.argsort(cen_p[:, 1])]
        mF, mH = cen_p[:2].mean(0), cen_p[2:].mean(0)
        d_ = mF - mH
        yb = math.degrees(math.atan2(-d_[0], -d_[1]))   # turn about +Z that sends d_ to -Y
        rb = 0.0
        dbest = 0.0
        R0 = np.array(Matrix.Rotation(math.radians(yb), 3, 'Z'))
        cx = float(((mF - c0) @ R0.T)[0])
        report_paws = {'paws': np.round(cen_p, 3).tolist()}
    else:
        cand = [(asym_t(y_, r_)[0], y_, r_) for y_ in np.arange(-24, 24.1, 3.0) for r_ in np.arange(-12, 12.1, 3.0)]
        _, y0, r0 = min(cand)
        cand = [(asym_t(y_, r_)[0], y_, r_) for y_ in np.arange(y0 - 3, y0 + 3.1, 0.5) for r_ in np.arange(r0 - 3, r0 + 3.1, 0.5)]
        dbest, yb, rb = min(cand)
        R0 = np.array(Matrix.Rotation(math.radians(rb), 3, 'Y')) @ np.array(Matrix.Rotation(math.radians(yb), 3, 'Z'))
        cx = asym_t(yb, rb)[1]
    X0 = (Bts - c0) @ R0.T
    X0[:, 0] -= cx
    kAt = kdt(At)
    s_, Rx, ty, tz = s, np.eye(3), At[:, 1].mean() - s * X0[:, 1].mean(), At[:, 2].mean() - s * X0[:, 2].mean()
    for _ in range(30):
        Y = (s_ * X0 @ Rx.T) + np.array([0, ty, tz])
        q = np.array([At[kAt.find(Vector(y_))[1]] for y_ in Y])
        p2, q2 = X0[:, 1:], q[:, 1:]
        mp, mq = p2.mean(0), q2.mean(0)
        H = (p2 - mp).T @ (q2 - mq)
        a = math.atan2(H[0, 1] - H[1, 0], H[0, 0] + H[1, 1])
        R2 = np.array([[math.cos(a), -math.sin(a)], [math.sin(a), math.cos(a)]])
        s_ = float(((q2 - mq) * ((p2 - mp) @ R2.T)).sum() / ((p2 - mp) ** 2).sum())
        Rx = np.array([[1, 0, 0], [0, R2[0, 0], R2[0, 1]], [0, R2[1, 0], R2[1, 1]]])
        ty, tz = mq - s_ * (R2 @ mp)
    s = s_
    R = Rx @ R0
    t = np.array([0, ty, tz]) + s * (Rx @ (-R0 @ c0 - np.array([cx, 0, 0])))
    report_gs = {'yaw': float(yb), 'roll': float(rb), 'mirror_dist': dbest, 'pitch': math.degrees(a)}
else:
    s, R, t = icp_similarity(Bs, A, kA, s, t, rotate=True)
X = s * B @ R.T + t
for v, x in zip(bm.verts, X):
    v.co = Vector(x)
report = {'global_sym': globals().get('report_gs'), 'global_scale': s, 'global_rot_deg': math.degrees(math.acos(max(-1, min(1, (np.trace(R) - 1) / 2)))),
          'global_translate': t.tolist()}

# ---------------- components (small separate pieces: teeth, eyes)
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
piece = np.zeros(len(bm.verts), int)
for c in comps[1:]:
    piece[c] = 2
report['components'] = [len(c) for c in comps[:12]]
co = lambda i: bm.verts[i].co
# small pieces (teeth, claws) follow the displacement of their nearest main-body vertex
main_ids = np.nonzero(piece == 0)[0]
k_main = kdt(np.array([tuple(bm.verts[i].co) for i in main_ids]))
anchor = {int(i): int(main_ids[k_main.find(bm.verts[int(i)].co)[1]]) for i in np.nonzero(piece == 2)[0]}
P_fit0 = np.array([tuple(v.co) for v in bm.verts])
nbr = [[e.other_vert(v).index for e in v.link_edges] for v in bm.verts]


def labels():
    return np.array([lab[kA.find(v.co)[1]] for v in bm.verts])


EA = np.array([(e.verts[0].index, e.verts[1].index) for e in bm.edges])
DEG = np.maximum(np.bincount(EA.ravel(), minlength=len(bm.verts)), 1).astype(float)


def diffuse(w, iters):
    w = w.astype(float)
    for _ in range(iters):
        acc = np.zeros_like(w)
        np.add.at(acc, EA[:, 0], w[EA[:, 1]]); np.add.at(acc, EA[:, 1], w[EA[:, 0]])
        w = 0.5 * w + 0.5 * np.where(DEG > 0, acc / DEG, w)
    return w


# ---------------- head ICP, blended into the neck
L = labels()
hw = diffuse(np.isin(L, HEAD_BONES), int(os.environ.get('HEAD_DIFFUSE', '8')))
hw = np.clip((hw - 0.15) / 0.7, 0, 1) if os.environ.get('HEAD_ROT') in ('1', 'sym') else hw   # rigid head, blend in the neck
hid = np.nonzero(hw > 0.5)[0]
Ah = A[np.isin(lab, HEAD_BONES)]
Hp = np.array([tuple(co(i)) for i in hid])
import os
HEAD_ROT = os.environ.get('HEAD_ROT') in ('1', 'sym')   # the Meshy head is turned (cat): rigid head move with rotation
if NOGLOBAL:
    hs, hR, ht = 1.0, np.eye(3), np.zeros(3)
elif os.environ.get('HEAD_ROT') == 'sym':
    # the Meshy head is turned: its rotation is the one that makes the head mirror-symmetric about the midplane
    # (yaw and roll about the head centroid, searched), its translation the ICP onto the MM9 head with that rotation
    Hs = Hp[rng.choice(len(Hp), min(2500, len(Hp)), replace=False)]
    hc0 = Hs.mean(0)

    def asym(yaw, roll):
        Ry = np.array(Matrix.Rotation(math.radians(yaw), 3, 'Z'))
        Rr = np.array(Matrix.Rotation(math.radians(roll), 3, 'Y'))
        X = (Hs - hc0) @ (Rr @ Ry).T
        best = None
        for _ in range(3):   # the mirror plane x = c: c from the matched pairs
            c = 0.0 if best is None else best[1]
            M = X.copy(); M[:, 0] = 2 * c - M[:, 0]
            k = kdt(X)
            idx = np.array([k.find(Vector(m))[1] for m in M])
            c = float(((X[idx, 0] + X[:, 0]) / 2).mean())
            d = float(np.mean([k.find(Vector(m))[2] for m in M]))
            best = (d, c)
        return best
    cand = []
    for yaw in np.arange(-24, 24.1, 3.0):
        for roll in np.arange(-12, 12.1, 3.0):
            cand.append((asym(yaw, roll)[0], yaw, roll))
    _, y0, r0 = min(cand)
    cand = []
    for yaw in np.arange(y0 - 3, y0 + 3.1, 0.5):
        for roll in np.arange(r0 - 3, r0 + 3.1, 0.5):
            cand.append((asym(yaw, roll)[0], yaw, roll))
    dbest, yb, rb = min(cand)
    hR = np.array(Matrix.Rotation(math.radians(rb), 3, 'Y')) @ np.array(Matrix.Rotation(math.radians(yb), 3, 'Z'))
    Xr = (Hp - hc0) @ hR.T + hc0
    hs, R1, ht = icp_similarity(Xr, Ah, kdt(Ah), 1.0, np.zeros(3), iters=25, fixed_scale=True, rotate=False)
    ht = ht + hc0 - hR @ hc0   # p -> hR (p - hc0) + hc0 + ht'  ==  hR p + ht
    report['head_sym'] = {'yaw': float(yb), 'roll': float(rb), 'mirror_dist': dbest}
else:
    hs, hR, ht = icp_similarity(Hp, Ah, kdt(Ah), 1.0, np.zeros(3), iters=25, fixed_scale=True, rotate=HEAD_ROT)
# blend: the head moves rigidly (w = 1), the neck by a partial turn about the head centroid (slerp of hR)
from mathutils import Quaternion
hq = Matrix(hR.tolist()).to_quaternion()
hc = Hp.mean(0)
hmove = hR @ hc + ht - hc
for i in range(len(bm.verts)):
    if hw[i] > 1e-3 and (piece[i] == 0 or HEAD_ROT):
        w = min(1.0, hw[i])
        q = Quaternion().slerp(hq, w)
        bm.verts[i].co = Vector(hc) + q @ (co(i) - Vector(hc)) + Vector(w * hmove)
report['head_icp_t'] = ht.tolist()
report['head_icp_rot_deg'] = math.degrees(hq.angle)
chain_of = np.full(len(bm.verts), -1, int)


def geodesic(src_ids, allowed):
    dist = {i: 0.0 for i in src_ids}
    pq = [(0.0, i) for i in src_ids]
    while pq:
        d, i = heapq.heappop(pq)
        if d > dist[i]:
            continue
        v = bm.verts[i]
        for e in v.link_edges:
            j = e.other_vert(v).index
            if j not in allowed:
                continue
            nd = d + e.calc_length()
            if nd < dist.get(j, 1e9):
                dist[j] = nd; heapq.heappush(pq, (nd, j))
    return dist


def chain_poly(names):
    pts = [J[n].copy() for n in names]
    tipv = A[lab == names[-1]]
    far = tipv[np.argmax(np.linalg.norm(tipv - np.array(pts[-1]), axis=1))]
    pts.append(Vector(far))
    if names == CHAINS['tail'] and os.environ.get('TAIL_MIDLINE') == '1':
        # first pass of a two-pass fit: the tail onto the MM9 tail chain turned about its root into the midplane
        # (x = 0), so the mesh can be mirrored before the second pass poses it onto the real (sideways) MM9 tail
        root = pts[0]
        out = [root.copy()]
        for a, b in zip(pts, pts[1:]):
            d = b - a
            d2 = Vector((0.0, d.y, d.z))
            d2 = d2.normalized() * d.length if d2.length > 1e-9 else Vector((0, 0, -d.length))
            out.append(out[-1] + d2)
        pts = [Vector((0.0, q.y, q.z)) for q in out]
    return pts


def arc(pts):
    s = [0.0]
    for a, b in zip(pts, pts[1:]):
        s.append(s[-1] + (b - a).length)
    return s


def at(pts, sl, x):
    if x <= 0:
        tng = (pts[1] - pts[0]).normalized()
        return pts[0] + tng * x, tng
    if x >= sl[-1]:
        tng = (pts[-1] - pts[-2]).normalized()
        return pts[-1] + tng * (x - sl[-1]), tng
    for i in range(len(pts) - 1):
        if x <= sl[i + 1]:
            h = sl[i + 1] - sl[i]
            a = (x - sl[i]) / h if h > 0 else 0
            return pts[i].lerp(pts[i + 1], a), (pts[i + 1] - pts[i]).normalized()


def fit_chain_lbs(ids, tip, target_pts, label, blend, sigma, adjust_root=True):
    allowed = set(ids)
    gd = geodesic([tip], allowed)
    gmax = max(gd.values())
    bins = [[] for _ in range(NB)]
    for i, d in gd.items():
        bins[min(NB - 1, int(d / gmax * NB))].append(co(i))
    cl = [co(tip).copy()] + [sum(b, Vector()) / len(b) for b in bins if b]
    for _ in range(3):
        cl = [cl[0]] + [(cl[i - 1] + 2 * cl[i] + cl[i + 1]) / 4 for i in range(1, len(cl) - 1)] + [cl[-1]]
    kcut = min(range(len(cl)), key=lambda k: (cl[k] - target_pts[0]).length)
    mesh_pts = list(reversed(cl[:kcut + 1]))
    ms = arc(mesh_pts)
    # the Meshy limb leaves the body below the MM9 root pivot: start the target chain at the point of its first
    # segment nearest the Meshy cut, so the root segment is not stretched up into the body
    a0, a1 = target_pts[0], target_pts[1]
    u0 = max(0.0, min(0.8, (mesh_pts[0] - a0).dot(a1 - a0) / max((a1 - a0).length_squared, 1e-12))) if adjust_root else 0.0
    target_pts = [a0.lerp(a1, u0)] + list(target_pts[1:])
    ts = arc(target_pts)
    src_j = [at(mesh_pts, ms, x * ms[-1] / ts[-1])[0] for x in ts]
    src_j[0] = mesh_pts[0].copy(); src_j[-1] = mesh_pts[-1].copy()
    mats = []
    for k in range(len(ts) - 1):
        a0, a1 = src_j[k], src_j[k + 1]
        b0, b1 = target_pts[k], target_pts[k + 1]
        da, db = (a1 - a0), (b1 - b0)
        if da.length < 1e-6:
            mats.append(Matrix.Translation(b0 - a0)); continue
        rq = da.normalized().rotation_difference(db.normalized())
        if rq.angle > math.radians(50):   # a bad end estimate (the tail tip turned 130 deg): translate only
            rq = rq.__class__()
        r = rq.to_matrix().to_4x4()
        u = da.normalized()
        stv = min(float(os.environ.get('STRETCH_MAX', '1.2')), max(0.85, db.length / da.length))   # large stretches crease the shoulders (wolf); the cat's MM9 legs are 1.6x the Meshy ones
        S = Matrix.Identity(4)
        for i_ in range(3):
            for j_ in range(3):
                S[i_][j_] += (stv - 1) * u[i_] * u[j_]
        mats.append(Matrix.Translation(b0) @ r @ S @ Matrix.Translation(-a0))
    return {'mesh_pts': mesh_pts, 'tip': list(co(tip)), 'meshy_len': ms[-1], 'mm9_len': ts[-1], 'src_joints': src_j, 'target': target_pts,
            'mats': mats, 'segment_stretch': [round((target_pts[k + 1] - target_pts[k]).length /
                                                   max((src_j[k + 1] - src_j[k]).length, 1e-6), 2)
                                             for k in range(len(ts) - 1)]}


P_now = np.array([tuple(v.co) for v in bm.verts])
# REGION_GEO = 'zlo,zhi,tail_y,split_y[,rump_y]': limb regions from the Meshy geometry instead of the MM9 capsules (the MM9
# cat's bind sweeps the hind legs forward under the belly and hangs the tail down to one side, so the nearest capsule
# of a Meshy hind paw is the tail). Seeds: the connected parts below zlo (four paws and the tail end); a part behind
# tail_y is the tail, the others are legs, front/back by split_y and left/right by their x order (the Meshy cat walks
# with both hind paws left of the midline). Every vertex below zhi joins the seed nearest along the surface; the tail
# also takes everything above zhi behind rump_y (default tail_y).
GEO = None
if os.environ.get('REGION_GEO'):
    gv = [float(x) for x in os.environ['REGION_GEO'].split(',')]
    zlo, zhi, ty, sy = gv[:4]
    ry = gv[4] if len(gv) > 4 else ty
    GEO = np.full(len(bm.verts), -1, int)

    def parts_below(z):
        low = (P_now[:, 2] < z) & (piece == 0)
        seen_g = np.zeros(len(bm.verts), bool)
        out = []
        for i0 in np.nonzero(low)[0]:
            if seen_g[i0]:
                continue
            comp, st = [], [int(i0)]; seen_g[i0] = True
            while st:
                x = st.pop(); comp.append(x)
                for e in bm.verts[x].link_edges:
                    y = e.other_vert(bm.verts[x]).index
                    if low[y] and not seen_g[y]:
                        seen_g[y] = True; st.append(y)
            if len(comp) >= 50:
                out.append(comp)
        return out
    seeds = parts_below(zlo)
    cen = [P_now[c].mean(0) for c in seeds]
    for c, cc in zip(seeds, cen):
        print('GEOSEED', len(c), np.round(cc, 3).tolist())
    lab_seed = {}
    for k, cc in enumerate(cen):
        if cc[1] > ty:
            lab_seed[k] = 4
    for front in (True, False):
        ks = [k for k, cc in enumerate(cen) if k not in lab_seed and (cc[1] < sy) == front]
        assert len(ks) == 2, ('expected two paws', front, ks)
        ks.sort(key=lambda k: cen[k][0])
        lab_seed[ks[1]] = 0 if front else 2   # larger x = the animal's left
        lab_seed[ks[0]] = 1 if front else 3
    allowed = set(int(i) for i in np.nonzero((P_now[:, 2] < zhi) & (piece == 0))[0])
    dist = {}
    pq = []
    for k, c in enumerate(seeds):
        for i in c:
            dist[i] = (0.0, lab_seed[k]); pq.append((0.0, i, lab_seed[k]))
    heapq.heapify(pq)
    while pq:
        d, i, l = heapq.heappop(pq)
        if d > dist[i][0]:
            continue
        v = bm.verts[i]
        for e in v.link_edges:
            j = e.other_vert(v).index
            if j not in allowed:
                continue
            nd = d + e.calc_length()
            if nd < dist.get(j, (1e9, -1))[0]:
                dist[j] = (nd, l); heapq.heappush(pq, (nd, j, l))
    for i, (d, l) in dist.items():
        GEO[i] = l
    GEO[(P_now[:, 1] > ry) & (P_now[:, 2] >= zhi) & (GEO < 0) & (piece == 0)] = 4
    report['region_geo'] = {int(k): int((GEO == k).sum()) for k in range(-1, 5)}
report['chains'] = {}
names = list(CHAINS)
# AIM_LEGS = 1: pose the MM9 legs to the Meshy legs first (skeleton to mesh: each leg bone turned so it points along
# the Meshy limb centreline between the joint estimates), then fit only the residual against that pose. The output
# Body is in this pose (saved with the armature); rig_body.py weights it there and unposes it to the MM9 bind with
# its own weights. Used when the MM9 bind is far from a standing pose (the cat's hind legs swept under the belly).
if os.environ.get('AIM_LEGS') == '1':
    from mathutils import Quaternion as _Q
    P_aim = np.array([tuple(v.co) for v in bm.verts])
    aim_rep = {}
    # Meshy joint estimates per chain: the limb path from the MM9 pivot (inside the body) down the region's
    # centreline to the paw (tail: to its tip); the MM9 joints sit on it at their own arc fractions
    SRC = {}

    def paw_ankle(rid_, ankle):
        """Where the MM9 ankle goes so that the flat MM9 paw (bind orientation) sits on the Meshy paw: the sole on the
        Meshy sole, the paw centre on the Meshy paw centre."""
        foot = lab == ankle.replace('ankle', 'foot')
        bind_paw = A[foot | (lab == ankle)]
        P_ = P_aim[rid_]
        sole = P_[:, 2].min()
        mesh_paw = P_[P_[:, 2] < sole + 0.018]
        b_sole = bind_paw[:, 2].min()
        c_b, c_m = bind_paw[:, :2].mean(0), mesh_paw[:, :2].mean(0)
        a = J[ankle]
        return Vector((c_m[0] + a.x - c_b[0], c_m[1] + a.y - c_b[1], sole + a.z - b_sole))

    for ci, n in enumerate(names):
        if not n.startswith('leg') and not (n == 'tail' and os.environ.get('AIM_TAIL') == '1'):
            continue
        bones = CHAINS[n]
        tp = chain_poly(bones)
        region = (GEO == ci) & (piece == 0) if GEO is not None else np.isin(seg_labels(P_aim), bones) & (piece == 0)
        rid = np.nonzero(region)[0]
        if n.startswith('leg'):
            tip = int(min(rid, key=lambda i: co(int(i)).z))
        else:
            tip = int(max(rid, key=lambda i: (co(int(i)) - tp[0]).length))
        inf = fit_chain_lbs([int(i) for i in rid], tip, tp, ci, 0, 0, adjust_root=n.startswith('leg'))
        path = [tp[0].copy()] + [q.copy() for q in inf['mesh_pts']]
        ps_ = arc(path)
        ts_ = arc(tp)
        src = [at(path, ps_, x * ps_[-1] / ts_[-1])[0] for x in ts_]
        src[-1] = path[-1].copy()
        if n.startswith('leg_f') and os.environ.get('AIM_IK') == '1':
            T_ = paw_ankle(rid, bones[-2])
            src = [tp[0].copy(), T_, T_ + (tp[2] - tp[1]), T_ + (tp[3] - tp[1])]
        if n.startswith('leg_h') and os.environ.get('AIM_IK') == '1':
            # the MM9 hind chain is much longer than the Meshy leg when stretched out: keep its lengths, its paw on the
            # Meshy paw and bend it by two-bone IK (hip, knee forward, ankle); the mesh is not stretched at all
            T_ = paw_ankle(rid, bones[-2])
            foot_ = T_ + (tp[4] - tp[3])
            H_ = tp[0]
            L1_, L2_ = (tp[1] - tp[0]).length, (tp[3] - tp[1]).length
            D_ = T_ - H_
            d_ = min(D_.length, 0.995 * (L1_ + L2_))
            u_ = D_.normalized()
            fw_ = Vector((0, -1, 0)); fw_ = (fw_ - u_ * fw_.dot(u_)).normalized()
            c_ = (L1_ * L1_ + d_ * d_ - L2_ * L2_) / (2 * d_)
            h_ = math.sqrt(max(L1_ * L1_ - c_ * c_, 0.0))
            K_ = H_ + u_ * c_ + fw_ * h_
            # the mid joint keeps its bind offset from the knee -> ankle line
            ax_ = (tp[3] - tp[1]).normalized()
            f_ = (tp[2] - tp[1]).dot(ax_)
            off_ = (tp[2] - tp[1]) - ax_ * f_
            ax2_ = (T_ - K_).normalized()
            rear_ = -fw_
            M_ = K_ + ax2_ * f_ + rear_ * off_.length
            src = [H_.copy(), K_, M_, T_, foot_, path[-1].copy()]
        if n == 'tail':
            src = [Vector((0.0, q.y, q.z)) for q in src]   # the tail hangs in the midplane
        elif os.environ.get('AIM_VERTICAL') == '1':
            src = [Vector((src[0].x, q.y, q.z)) for q in src]   # the leg in its own vertical plane (no splay)
        SRC[n] = src
    # AIM_MIRROR = 1: a symmetric reference pose, the left legs aimed at the mirror of the right legs' joints (the
    # Meshy cat walks: its left hind paw crosses the midline)
    if os.environ.get('AIM_MIRROR') == '1':
        for l, r in (('leg_fl', 'leg_fr'), ('leg_hl', 'leg_hr')):
            SRC[l] = [Vector((-q.x, q.y, q.z)) for q in SRC[r]]
    for n, src in SRC.items():
        bones = CHAINS[n]
        tp = chain_poly(bones)
        last = arm.pose.bones[bones[-1]]
        far_local = arm.data.bones[bones[-1]].matrix_local.inverted() @ tp[-1]
        turns = []
        for k, b in enumerate(bones):
            if n.startswith('leg') and k == len(bones) - 1 and os.environ.get('AIM_IK') != '1':
                continue   # the paw keeps its rest angle to the ankle
            bpy.context.view_layer.update()
            pb = arm.pose.bones[b]
            h = pb.head.copy()
            if n.startswith('leg') and os.environ.get('AIM_IK') == '1' and b in bones[-2:]:
                # ankle and foot keep their bind world orientation: MM9's paw is flat in the bind
                pb.matrix = Matrix.Translation(h) @ arm.data.bones[b].matrix_local.to_3x3().to_4x4()
                continue
            nxt = arm.pose.bones[bones[k + 1]].head.copy() if k + 1 < len(bones) else last.matrix @ far_local
            d = src[k + 1] - src[k]
            if d.length < 1e-6:
                continue
            q = (nxt - h).normalized().rotation_difference(d.normalized())
            turns.append(round(math.degrees(q.angle), 1))
            R4 = Matrix.Translation(h) @ q.to_matrix().to_4x4() @ Matrix.Translation(-h)
            pb.matrix = R4 @ pb.matrix
        aim_rep[n] = turns
    bpy.context.view_layer.update()
    J = {b.name: arm.pose.bones[b.name].head.copy() for b in arm.data.bones}
    dg = bpy.context.evaluated_depsgraph_get()
    pts = []
    for o in bpy.data.objects:
        if o.type != 'MESH' or o.name == 'Body':
            continue
        me_e = o.evaluated_get(dg).to_mesh()
        pts += [tuple(o.matrix_world @ v.co) for v in me_e.vertices]
        o.evaluated_get(dg).to_mesh_clear()
    A = np.array(pts)
    assert len(A) == len(lab)
    kA = kdt(A)
    report['aim_legs_deg'] = aim_rep
    report['ref_pose'] = {pb.name: [round(x, 6) for x in pb.rotation_quaternion] for pb in arm.pose.bones
                          if pb.rotation_quaternion.angle > 1e-5}
# bone segments (capsules): bone p spans from its head to each child's head; a leaf bone to its farthest MM9 vertex
SEG = []
for b in arm.data.bones:
    if b.parent is None:
        continue
    kids = [c.name for c in b.children]
    ends = [J[c] for c in kids]
    if not ends:
        vv = A[lab == b.name]
        if len(vv):
            ends = [Vector(vv[np.argmax(np.linalg.norm(vv - np.array(J[b.name]), axis=1))])]
    for e in ends:
        SEG.append((b.name, np.array(J[b.name]), np.array(e)))


def seg_labels(P):
    best = np.full(len(P), 1e9); out = np.empty(len(P), object)
    for name, a, b in SEG:
        ab = b - a
        u = np.clip(((P - a) @ ab) / max(ab @ ab, 1e-12), 0, 1)
        d = np.linalg.norm(P - (a + u[:, None] * ab), axis=1)
        m = d < best
        best[m] = d[m]; out[m] = name
    return out


import os
P_now = np.array([tuple(v.co) for v in bm.verts])
info = {}
for ci, n in enumerate(names if os.environ.get('NOCHAIN') != '1' else []):
    if n.startswith('leg_h') and os.environ.get('AIM_IK') == '1':
        continue
    bones = CHAINS[n]
    tp = chain_poly(bones)
    if GEO is not None:
        region = (GEO == ci) & (piece == 0)
    else:
        region = np.isin(seg_labels(P_now), bones) & (piece == 0)
    if n.startswith('leg'):
        region &= P_now[:, 2] < J[bones[0]].z + LEG_TOP
    if n.startswith('wing'):
        region &= np.abs(P_now[:, 0]) > abs(J[bones[0]].x) + 0.02 * K
    if n == 'tail':
        region &= P_now[:, 1] > J[bones[0]].y + 0.02 * K   # behind the tail root, not the rump
    rid = np.nonzero(region)[0]
    if os.environ.get('TIP') == 'extreme':
        # the limb's own end: the lowest vertex of a leg region, the farthest from the root of the tail region (the
        # MM9 cat's bind holds its front paws 5 cm off the floor, so the vertex nearest the MM9 paw is mid-leg)
        if n.startswith('leg'):
            tip = int(min(rid, key=lambda i: co(int(i)).z))
        else:
            tip = int(max(rid, key=lambda i: (co(int(i)) - tp[0]).length))
    else:
        tip = int(min(rid, key=lambda i: (co(int(i)) - tp[-1]).length))
    keep = set(geodesic([tip], set(int(i) for i in rid)))   # the connected part of the region holding the tip
    region = np.zeros(len(region), bool); region[list(keep)] = True
    grow = diffuse(region, 4) > 0.02
    ids = [int(i) for i in np.nonzero(grow & (piece == 0))[0]]
    print('CHAINREGION', n, len(rid), len(keep), len(ids), 'tip', [round(x, 3) for x in co(tip)], 'target tip', [round(x, 3) for x in tp[-1]])
    info[n] = fit_chain_lbs(ids, tip, tp, ci, BLEND[n], SIGMA, adjust_root=n.startswith('leg'))
    report['chains'][n] = {k: v for k, v in info[n].items() if k not in ('mats', 'src_joints', 'target')}
    report['chains'][n]['seg_rot_deg'] = [round(math.degrees(M.to_quaternion().angle if hasattr(M, 'to_quaternion')
                                                             else 0), 1) for M in
                                          [m_.to_3x3().normalized() for m_ in info[n]['mats']]]
    report['chains'][n]['src_root'] = [round(x, 3) for x in info[n]['src_joints'][0]]
    report['chains'][n]['tgt_root'] = [round(x, 3) for x in info[n]['target'][0]]
# transient skinning: core bones on their MM9 segments, chain bones on the segments estimated on the Meshy limb;
# capsule labels diffused along the mesh; every chain bone carries its segment matrix (Meshy joints -> MM9 joints),
# the core stays. The pose p' = sum_b w_b T_b p is smooth wherever the weights are, so no seam opens.
chain_bone = {}
for ci, n in enumerate(info):
    for k, b in enumerate(CHAINS[n]):
        chain_bone[b] = (n, k)
SEG2 = [sg for sg in SEG if sg[0] not in chain_bone]
for n, inf in info.items():
    for k, b in enumerate(CHAINS[n]):
        SEG2.append((b, np.array(tuple(inf['src_joints'][k])), np.array(tuple(inf['src_joints'][k + 1]))))
lab2 = None
bone_names = sorted(set(sg[0] for sg in SEG2))
bi = {b: i for i, b in enumerate(bone_names)}
# smooth geometric weights: per bone the capsule distance, soft-min with POSE_SIGMA (independent of mesh density,
# so no small label island bends a few vertices on its own), then a short smoothing along the mesh
Dist = np.full((len(bm.verts), len(bone_names)), 1e9)
for name, a, b in SEG2:
    ab = b - a
    u = np.clip(((P_now - a) @ ab) / max(ab @ ab, 1e-12), 0, 1)
    d = np.linalg.norm(P_now - (a + u[:, None] * ab), axis=1)
    k = bi[name]
    Dist[:, k] = np.minimum(Dist[:, k], d)
lab2 = np.array(bone_names)[Dist.argmin(1)]
sig = float(os.environ.get('POSE_SIGMA', str(POSE_SIGMA)))
Wt = np.exp(-((Dist - Dist.min(1, keepdims=True)) / sig) ** 2)
Wt /= Wt.sum(1, keepdims=True)
ea = np.array([(e.verts[0].index, e.verts[1].index) for e in bm.edges])
deg = np.bincount(ea.ravel(), minlength=len(bm.verts)).astype(float)
for _ in range(int(os.environ.get('POSE_DIFFUSE', '4'))):
    S = np.zeros_like(Wt)
    np.add.at(S, ea[:, 0], Wt[ea[:, 1]]); np.add.at(S, ea[:, 1], Wt[ea[:, 0]])
    Wt = 0.5 * Wt + 0.5 * S / np.maximum(deg, 1)[:, None]
Ph = np.hstack([P_now, np.ones((len(P_now), 1))])
Pn = np.zeros_like(P_now)
for b, k in bi.items():
    w = Wt[:, k]
    if not (w > 0).any():
        continue
    if b in chain_bone:
        n, j = chain_bone[b]
        M = np.array(info[n]['mats'][j])
    else:
        M = np.eye(4)
    Pn += w[:, None] * (Ph @ M.T)[:, :3]
Pn /= Wt.sum(1)[:, None]
if os.environ.get('FITDEBUG') == '1':
    Dd = Pn - P_now
    S = np.zeros_like(Dd)
    np.add.at(S, ea[:, 0], Dd[ea[:, 1]]); np.add.at(S, ea[:, 1], Dd[ea[:, 0]])
    rough = np.linalg.norm(Dd - S / np.maximum(deg, 1)[:, None], axis=1)
    rough[piece != 0] = 0
    back = (np.abs(P_now[:, 0]) > 0.1) & (P_now[:, 1] > 0.0) & (P_now[:, 1] < 0.9) & (P_now[:, 2] > 1.2)
    print('ROUGHBACK max %.4f mean %.5f' % (rough[back].max(), rough[back].mean()), 'all mean %.5f' % rough.mean())
    for i in np.argsort(-(rough * back))[:5]:
        top = np.argsort(-Wt[i])[:3]
        print('RB %.4f %s %s' % (rough[i], np.round(P_now[i], 3).tolist(), [(bone_names[k], round(float(Wt[i, k]), 3)) for k in top]))
    for i in np.argsort(-rough)[:12]:
        top = np.argsort(-Wt[i])[:3]
        print('ROUGH %.4f v%d at %s deg %d lab %s w %s' % (rough[i], i, np.round(P_now[i], 3).tolist(), deg[i], lab2[i],
              [(bone_names[k], round(float(Wt[i, k]), 2)) for k in top]))
for i in np.nonzero(piece == 0)[0]:
    bm.verts[int(i)].co = Vector(Pn[i])
    if lab2[i] in chain_bone:
        chain_of[i] = list(info).index(chain_bone[lab2[i]][0])
report['chain_names'] = names
if not info and GEO is not None:
    chain_of = GEO.copy()   # NOCHAIN pass: the geometric limb regions (symmetrize.py centres the tail by them)
if os.environ.get('AIM_IK') == '1':
    chain_of = GEO.copy()   # the geometric regions, in CHAINS order (the fitted chains are a subset)
for i, a in anchor.items():
    bm.verts[i].co = Vector(P_fit0[i] + (np.array(tuple(co(a))) - P_fit0[a]))

me = bpy.data.meshes.new('Body')
pl = bm.verts.layers.int.new('piece')
cl_ = bm.verts.layers.int.new('chain')
for v in bm.verts:
    v[pl] = int(piece[v.index]); v[cl_] = int(chain_of[v.index])
bm.to_mesh(me)
obj = bpy.data.objects.new('Body', me)
sc.collection.objects.link(obj)
for p in me.polygons:
    p.use_smooth = True
d = np.array([kA.find(v.co)[2] for v in me.vertices])
report.update({'verts': len(me.vertices), 'tris': sum(len(p.vertices) - 2 for p in me.polygons),
               'dist_to_mm9_mean': float(d.mean()), 'dist_to_mm9_p90': float(np.percentile(d, 90))})
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(report, open(REP, 'w'), indent=1, default=str)
print('FIT ' + json.dumps({k: v for k, v in report.items() if k != 'chains'}, default=str))
