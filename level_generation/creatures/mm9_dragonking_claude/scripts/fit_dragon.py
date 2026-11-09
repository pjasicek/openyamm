"""Fit the Meshy Smart Topology dragon to the MM9 bind pose by articulated ICP and inverse skinning.

Args: <mm9 source blend> <meshy glb> <out blend> <report json>

1. Global: the Meshy mesh (welded) is turned to face -Y (best of four yaws by ICP), scaled to the MM9 bind height,
   centred, and refined by a symmetric similarity ICP.
2. Articulated ICP (MM9 skeleton -> Meshy): every MM9 bone b gets a similarity T_b (rotation, uniform scale,
   translation) that maps its MM9 bind vertices onto the Meshy surface. Solved Gauss-Seidel over the hierarchy with
   forward (MM9 -> nearest Meshy) and reverse (Meshy -> nearest posed MM9) pairs, strong joint-continuity pairs
   (T_b(head_b) = T_parent(head_b), and the same at every child head) and a weak prior toward the parent's
   transform. Bones without vertices follow their parent. Scale is clamped to [0.7, 1.45] x global.
3. Weights in Meshy space: nearest posed-MM9 vertex label, diffused along the mesh; small separate pieces (teeth,
   claws) rigid with their nearest main-surface vertex.
4. Inverse skinning: v_bind = (sum_b w_b T_b)^-1 v_meshy, which returns every vertex to the MM9 bind pose with the
   MM9 proportions (stretches and limb angles of the Meshy pose undone).
Per-vertex attributes: 'piece' (0 main surface, 2 small piece), 'chain' (bone-group id, see GROUPS) for rig_dragon.py.
Objects saved: MM9_Rig, the MM9 meshes, 'Body' (bind pose), 'MeshyPosed' (aligned Meshy copy, for overlays).
"""
import bpy, bmesh, sys, json, math
import numpy as np
from mathutils import Vector
from mathutils.kdtree import KDTree

argv = sys.argv[sys.argv.index('--') + 1:]
SRC, MESHY, OUT, REP = argv
ITERS = 12
JOINT_W = 6.0      # weight of a joint-continuity pair, relative to one surface pair (scaled by pair count)
PRIOR_W = 0.15     # weight of the parent-prior pairs
REL_LIMIT = 50      # degrees a bone may turn against its parent (subtree of 60+ MM9 vertices)
REL_LIMIT_SMALL = 25
FREE_ROOTS = {'Ywingbase', 'Ywingbase01'}
SMALL = 50         # components with fewer welded vertices are small pieces (teeth, eyes); wing scraps stay

bpy.ops.wm.open_mainfile(filepath=SRC)
arm = bpy.data.objects['MM9_Rig']
bones = [b.name for b in arm.data.bones]
bidx = {b: i for i, b in enumerate(bones)}
parent = [bidx[b.parent.name] if b.parent else -1 for b in arm.data.bones]
children = [[] for _ in bones]
for i, p in enumerate(parent):
    if p >= 0:
        children[p].append(i)
J = np.array([tuple(b.head_local) for b in arm.data.bones])

# MM9 vertices (rigid labels), deduplicated by position + label
seen = {}
for o in bpy.data.objects:
    if o.type != 'MESH':
        continue
    for v in o.data.vertices:
        g = max(v.groups, key=lambda g: g.weight)
        p = tuple(round(c, 5) for c in (o.matrix_world @ v.co))
        seen[(p, o.vertex_groups[g.group].name)] = 1
A = np.array([k[0] for k in seen])
lab = np.array([bidx[k[1]] for k in seen])
order = []  # hierarchy order (parents first)
stack = [i for i, p in enumerate(parent) if p < 0]
while stack:
    i = stack.pop(0)
    order.append(i)
    stack += children[i]


def kdt(P):
    k = KDTree(len(P))
    for i, p in enumerate(P):
        k.insert(Vector(p), i)
    k.balance()
    return k


def umeyama(p, q, w, smin, smax):
    w = w / w.sum()
    mp = (w[:, None] * p).sum(0)
    mq = (w[:, None] * q).sum(0)
    P0, Q0 = p - mp, q - mq
    C = (w[:, None] * Q0).T @ P0
    U, S, Vt = np.linalg.svd(C)
    D = np.diag([1, 1, np.sign(np.linalg.det(U @ Vt))])
    R = U @ D @ Vt
    var = (w * (P0 * P0).sum(1)).sum()
    s = float(np.trace(np.diag(S) @ D) / var) if var > 1e-12 else 1.0
    s = min(max(s, smin), smax)
    t = mq - s * R @ mp
    M = np.eye(4)
    M[:3, :3] = s * R
    M[:3, 3] = t
    return M


def apply(M, P):
    return P @ M[:3, :3].T + M[:3, 3]


# ---------------- import Meshy
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=MESHY)
new = [o for o in bpy.data.objects if o not in before]
src = next(o for o in new if o.type == 'MESH')
bm = bmesh.new()
bm.from_mesh(src.data)
bm.transform(src.matrix_world)
mat_src = list(src.data.materials)
for o in new:
    bpy.data.objects.remove(o)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
bm.verts.ensure_lookup_table()
bm.faces.ensure_lookup_table()
B0 = np.array([tuple(v.co) for v in bm.verts])
kA = kdt(A)
rng = np.random.default_rng(0)


wingA = np.array([bones[l].startswith('Y') for l in lab])


def wing_region(X):
    """Meshy wing points in MM9-aligned space: lateral of the shoulders and above them (MM9: Y* bones)."""
    return (np.abs(X[:, 0]) > 1.4) & (X[:, 2] > 9.5)


def global_fit(B, iters=25):
    s = (A[:, 2].max() - A[:, 2].min()) / (B[:, 2].max() - B[:, 2].min())
    t = np.array([(A[:, 0].min() + A[:, 0].max()) / 2 - s * (B[:, 0].min() + B[:, 0].max()) / 2,
                  (A[:, 1].min() + A[:, 1].max()) / 2 - s * (B[:, 1].min() + B[:, 1].max()) / 2,
                  A[:, 2].min() - s * B[:, 2].min()])
    M = np.eye(4); M[:3, :3] *= s; M[:3, 3] = t
    Bs = B[rng.choice(len(B), min(3000, len(B)), replace=False)]
    err = 0
    Ab = A[~wingA]
    kAb = kdt(Ab)
    for _ in range(iters):
        X = apply(M, Bs)
        keep = ~wing_region(X)
        Xk, Bk = X[keep], Bs[keep]
        kX = kdt(Xk)
        p, q = [], []
        for i, x in enumerate(Xk):
            p.append(Bk[i]); q.append(Ab[kAb.find(Vector(x))[1]])
        for a in Ab[::max(1, len(Ab) // 2000)]:
            p.append(Bk[kX.find(Vector(a))[1]]); q.append(a)
        p, q = np.array(p), np.array(q)
        M = umeyama(p, q, np.ones(len(p)), 0.01, 100)
        err = float(np.linalg.norm(apply(M, p) - q, axis=1).mean())
    return M, err


best = None
for k in range(4):
    yaw = k * math.pi / 2
    Rz = np.array([[math.cos(yaw), -math.sin(yaw), 0], [math.sin(yaw), math.cos(yaw), 0], [0, 0, 1]])
    M, err = global_fit(B0 @ Rz.T)
    if best is None or err < best[2]:
        best = (k, M, err, Rz)
yaw_k, Mg, gerr, Rz = best
B = apply(Mg, B0 @ Rz.T)          # Meshy, globally aligned (target space)
for v, x in zip(bm.verts, B):
    v.co = Vector(x)
gscale = float(np.cbrt(np.linalg.det(Mg[:3, :3])))
report = {'yaw_quarter_turns': yaw_k, 'global_error': gerr, 'global_scale': gscale}

# ---------------- cleanup: Meshy bridged the creature's right wing claws to the head frill with long sliver webs
# (faces with an edge over SPIKE_EDGE whose centre lies between the head and the wing wrist). Delete them, then the
# loose vertices, and fill the small holes they leave.
SPIKE_EDGE = 1.2
bm.faces.ensure_lookup_table()
spike = []
for f in bm.faces:
    e = max(ed.calc_length() for ed in f.edges)
    c = f.calc_center_median()
    if e > SPIKE_EDGE and 0.4 < abs(c.x) < 4.3 and -3.7 < c.y < 1.0 and 14.3 < c.z < 17.6:
        spike.append(f)
bmesh.ops.delete(bm, geom=spike, context='FACES')
loose = [v for v in bm.verts if not v.link_faces]
bmesh.ops.delete(bm, geom=loose, context='VERTS')
nb_before = sum(1 for e in bm.edges if e.is_boundary)
bmesh.ops.holes_fill(bm, edges=[e for e in bm.edges if e.is_boundary], sides=10)
bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table(); bm.verts.index_update()
B = np.array([tuple(v.co) for v in bm.verts])
report['cleanup'] = {'spike_faces_deleted': len(spike), 'loose_verts_deleted': len(loose),
                     'boundary_edges_before_fill': nb_before,
                     'boundary_edges_after_fill': sum(1 for e in bm.edges if e.is_boundary)}

# ---------------- components
comp = np.full(len(bm.verts), -1)
comps = []
for v in bm.verts:
    if comp[v.index] >= 0:
        continue
    st = [v]; comp[v.index] = len(comps); c = []
    while st:
        x = st.pop(); c.append(x.index)
        for e in x.link_edges:
            y = e.other_vert(x)
            if comp[y.index] < 0:
                comp[y.index] = len(comps); st.append(y)
    comps.append(c)
sizes = [len(c) for c in comps]
piece = np.array([2 if sizes[comp[i]] < SMALL else 0 for i in range(len(bm.verts))])
report['components'] = sorted(sizes, reverse=True)[:30]

# ---------------- articulated ICP (MM9 bind -> Meshy target), coarse to fine
T = [np.eye(4) for _ in bones]
kB = kdt(B)
has = np.array([np.any(lab == i) for i in range(len(bones))])
ids_of = [np.nonzero(lab == i)[0] for i in range(len(bones))]
desc = [[] for _ in bones]
for b in reversed(order):
    for c in children[b]:
        desc[b] += [c] + desc[c]
sub_ids = [np.concatenate([ids_of[b]] + [ids_of[c] for c in desc[b]]).astype(int) for b in range(len(bones))]
Bsub = np.arange(len(B))[::max(1, len(B) // 8000)]

# wing initialisation: the Meshy wings may spread sideways where MM9's sweep back. Search the rotation about the
# MM9 shoulder (Ywingbase head) and a uniform scale that best lays the MM9 wing (vertices + points sampled on its
# triangles) onto the Meshy wing region of that side (symmetric chamfer), then start the wing subtree from it.
def euler(yaw, pitch, roll):
    cz, sz, cx, sx, cy, sy = math.cos(yaw), math.sin(yaw), math.cos(pitch), math.sin(pitch), math.cos(roll), math.sin(roll)
    Rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    return Rz @ Rx @ Ry


wing_init = {}
from mathutils.bvhtree import BVHTree
mm9_tris = {}
for o in bpy.data.objects:
    if o.type != 'MESH' or o.name in ('Body', 'MeshyPosed') or o.name.startswith('MM9Posed_'):
        continue
    vl = [o.vertex_groups[max(v.groups, key=lambda g: g.weight).group].name for v in o.data.vertices]
    for p in o.data.polygons:
        if all(vl[i].startswith('Y') for i in p.vertices):
            vs = [tuple(o.matrix_world @ o.data.vertices[i].co) for i in p.vertices]
            side = 1 if sum(v[0] for v in vs) > 0 else -1
            for k in range(1, len(vs) - 1):
                mm9_tris.setdefault(side, []).append((vs[0], vs[k], vs[k + 1]))


def sample_tris(tris, n):
    t = np.array(tris)
    area = 0.5 * np.linalg.norm(np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0]), axis=1)
    pick = rng.choice(len(t), n, p=area / area.sum())
    u, v = rng.random(n), rng.random(n)
    flip = u + v > 1
    u[flip], v[flip] = 1 - u[flip], 1 - v[flip]
    return t[pick, 0] + u[:, None] * (t[pick, 1] - t[pick, 0]) + v[:, None] * (t[pick, 2] - t[pick, 0])


for root in ('Ywingbase', 'Ywingbase01'):
    r = bidx[root]
    side = int(np.sign(J[r][0]))
    tris = mm9_tris[side]
    bvh = BVHTree.FromPolygons([v for t in tris for v in t], [[3 * k, 3 * k + 1, 3 * k + 2] for k in range(len(tris))])
    Wa = sample_tris(tris, 500)
    reg = wing_region(B) & (np.sign(B[:, 0]) == side)
    Wb = B[reg]
    Wb = Wb[rng.choice(len(Wb), min(300, len(Wb)), replace=False)]
    kb_ = kdt(B[reg])
    sh = J[r]

    def cost(yaw, pitch, roll, sc_):
        R = euler(yaw, pitch, roll)
        X = (Wa - sh) @ R.T * sc_ + sh
        d1 = np.mean([kb_.find(Vector(x))[2] for x in X])
        Y = (Wb - sh) @ R / sc_ + sh          # Meshy points brought back into MM9 space
        d2 = np.mean([bvh.find_nearest(Vector(y))[3] for y in Y]) * sc_
        return d1 + d2

    # landmarks: wrist = highest wing point, tip = wing point farthest from the shoulder (MM9 and Meshy alike)
    Ab = np.array([v for t in tris for v in t])
    Bw = B[reg]
    lm9 = (Ab[Ab[:, 2].argmax()], Ab[np.linalg.norm(Ab - sh, axis=1).argmax()])
    lmm = (Bw[Bw[:, 2].argmax()], Bw[np.linalg.norm(Bw - sh, axis=1).argmax()])

    def frame(w, f):
        u = (w - sh) / np.linalg.norm(w - sh)
        v = (f - sh) - u * np.dot(f - sh, u)
        v /= np.linalg.norm(v)
        return np.stack([u, v, np.cross(u, v)], 1)
    R0 = frame(*lmm) @ frame(*lm9).T
    s0 = (np.linalg.norm(lmm[0] - sh) + np.linalg.norm(lmm[1] - sh)) / (np.linalg.norm(lm9[0] - sh) + np.linalg.norm(lm9[1] - sh))

    def cost_R(R, sc_):
        X = (Wa - sh) @ R.T * sc_ + sh
        d1 = np.mean([kb_.find(Vector(x))[2] for x in X])
        Y = (Wb - sh) @ R / sc_ + sh
        d2 = np.mean([bvh.find_nearest(Vector(y))[3] for y in Y]) * sc_
        dl = sum(np.linalg.norm((l9 - sh) @ R.T * sc_ + sh - lm_) for l9, lm_ in zip(lm9, lmm))
        return d1 + d2 + 0.25 * dl

    best_w = (cost_R(R0, s0), (0.0, 0.0, 0.0, s0))
    step = np.radians([10, 10, 10]); ss = 0.08
    for _ in range(5):
        y0, p0, r0, s_ = best_w[1]
        for dy in (-1, 0, 1):
            for dp in (-1, 0, 1):
                for dr in (-1, 0, 1):
                    for ds in (-1, 0, 1):
                        prm = (y0 + dy * step[0], p0 + dp * step[1], r0 + dr * step[2], max(0.6, s_ + ds * ss))
                        c = cost_R(euler(*prm[:3]) @ R0, prm[3])
                        if c < best_w[0]:
                            best_w = (c, prm)
        step = step / 2; ss /= 2
    c, (yaw, pitch, roll, sc_) = best_w
    R = euler(yaw, pitch, roll) @ R0
    M = np.eye(4); M[:3, :3] = R * sc_; M[:3, 3] = sh - (R * sc_) @ sh
    for b in [r] + desc[r]:
        T[b] = M.copy()
    wing_init[root] = {'chamfer': round(float(c), 4), 'scale': round(float(sc_), 3),
                       'refine_ypr_deg': [round(math.degrees(a), 1) for a in (yaw, pitch, roll)],
                       'landmark_scale': round(float(s0), 3),
                       'rotation_deg': round(math.degrees(math.acos(max(-1, min(1, (np.trace(R) - 1) / 2)))), 1),
                       'meshy_points': int(reg.sum())}
report['wing_init'] = wing_init


def posed():
    X = np.zeros_like(A)
    for b in range(len(bones)):
        if len(ids_of[b]):
            X[ids_of[b]] = apply(T[b], A[ids_of[b]])
    return X


for it in range(ITERS):
    for b in order:
        pb = parent[b]
        ids = sub_ids[b]
        if len(ids) < 3:
            if pb >= 0:
                T[b] = T[pb].copy()
            continue
        X = posed()
        Xs = X[ids]
        kS = kdt(Xs)
        fwd = np.array([kB.find(Vector(x))[1] for x in Xs])
        df = np.linalg.norm(B[fwd] - Xs, axis=1)
        cut = 3.0 * max(np.median(df), 1e-4)
        kX = kdt(X)
        own = set(ids.tolist())
        rp = []
        for j in Bsub:
            i = kX.find(Vector(B[j]))[1]
            if i in own and np.linalg.norm(X[i] - B[j]) < cut:
                rp.append((i, j))
        wself = np.where(np.isin(ids, ids_of[b]), 1.0, 0.5)
        ok = df < cut
        # source points are the CURRENT posed positions; solve a delta D, then T_b' = D T_b for the subtree
        P_ = [Xs[ok]]; Q_ = [B[fwd[ok]]]; W_ = [wself[ok]]
        if rp:
            P_.append(X[[i for i, _ in rp]]); Q_.append(B[[j for _, j in rp]]); W_.append(np.full(len(rp), 0.7))
        n = sum(len(w) for w in W_)
        if n < 3:
            continue
        if pb >= 0:
            jw = JOINT_W * max(1.0, n / 20)
            P_.append(apply(T[b], J[b][None])); Q_.append(apply(T[pb], J[b][None])); W_.append(np.array([jw]))
            P_.append(Xs); Q_.append(apply(T[pb], A[ids])); W_.append(np.full(len(ids), PRIOR_W))
        p, q, w = np.concatenate(P_), np.concatenate(Q_), np.concatenate(W_)
        D = umeyama(p, q, w, 0.93, 1.07)
        if pb >= 0 and bones[b] not in FREE_ROOTS:
            # limit the turn relative to the parent (about the joint): toes and fingers have few vertices and
            # flip in a free fit
            Tn = D @ T[b]
            Mrel = np.linalg.inv(T[pb][:3, :3]) @ Tn[:3, :3]
            sr = np.cbrt(abs(np.linalg.det(Mrel)))
            Rr = Mrel / sr
            ang = math.acos(max(-1.0, min(1.0, (np.trace(Rr) - 1) / 2)))
            lim = math.radians(REL_LIMIT_SMALL if len(sub_ids[b]) < 60 else REL_LIMIT)
            if ang > lim:
                ax = np.array([Rr[2, 1] - Rr[1, 2], Rr[0, 2] - Rr[2, 0], Rr[1, 0] - Rr[0, 1]])
                ax = ax / max(np.linalg.norm(ax), 1e-9)
                K = np.array([[0, -ax[2], ax[1]], [ax[2], 0, -ax[0]], [-ax[1], ax[0], 0]])
                Rl = np.eye(3) + math.sin(lim) * K + (1 - math.cos(lim)) * K @ K
                Mn = np.eye(4)
                Mn[:3, :3] = T[pb][:3, :3] @ (sr * Rl)
                jt = apply(Tn, J[b][None])[0]
                Mn[:3, 3] = jt - Mn[:3, :3] @ J[b]
                D = Mn @ np.linalg.inv(T[b])
        for c in [b] + desc[b]:
            T[c] = D @ T[c]
            sc_ = np.cbrt(abs(np.linalg.det(T[c][:3, :3])))
            if sc_ < 0.7 or sc_ > 1.45:
                T[c][:3, :3] *= min(max(sc_, 0.7), 1.45) / sc_
    X = posed()
    d = np.array([np.linalg.norm(B[kB.find(Vector(x))[1]] - x) for x in X])
    report.setdefault('icp_mean_mm9_to_meshy', []).append(round(float(d.mean()), 4))

# ---------------- weights in Meshy space
X = np.zeros_like(A)
for b in range(len(bones)):
    if len(ids_of[b]):
        X[ids_of[b]] = apply(T[b], A[ids_of[b]])
kX = kdt(X)
n = len(B)
W = np.zeros((n, len(bones)))
# the head frills sit next to the raised wings: a vertex in the head box never takes a wing label
nonwing = np.nonzero(~wingA)[0]
kXn = kdt(X[nonwing])
head_box = (B[:, 2] > 13.5) & (np.abs(B[:, 0]) < 2.2) & (B[:, 1] < 0.5)
for i in range(n):
    j = kX.find(Vector(B[i]))[1]
    if wingA[j] and head_box[i]:
        j = nonwing[kXn.find(Vector(B[i]))[1]]
    W[i, lab[j]] = 1
report['head_box_vertices'] = int(head_box.sum())
nbr = [[] for _ in range(n)]
for e in bm.edges:
    a, b_ = e.verts[0].index, e.verts[1].index
    nbr[a].append(b_); nbr[b_].append(a)
main = piece == 0
for _ in range(8):
    avg = np.array([W[nb].mean(0) if nb else W[i] for i, nb in enumerate(nbr)])
    W = np.where(main[:, None], 0.5 * W + 0.5 * avg, W)
main_ids = np.nonzero(main)[0]
km = kdt(B[main_ids])
for c in comps:
    if len(c) >= SMALL:
        continue
    best_i = min(c, key=lambda i: km.find(Vector(B[i]))[2])
    W[c] = W[main_ids[km.find(Vector(B[best_i]))[1]]]
Ts = np.array(T)  # (nb, 4, 4)
# blend of the per-bone inverse images (always finite; the inverse of a blended matrix is singular where bones
# with very different transforms meet, e.g. a wing turned ~50 degrees against the back)
Tinv = np.linalg.inv(Ts)
Bh = np.concatenate([B, np.ones((n, 1))], 1)
Xb = np.zeros((n, 3))
for b in np.nonzero(W.sum(0) > 0)[0]:
    Xb += W[:, b:b + 1] * (Bh @ Tinv[b].T)[:, :3]

# ---------------- build objects
me_pose = bpy.data.meshes.new('MeshyPosed')
bm.to_mesh(me_pose)
ob_pose = bpy.data.objects.new('MeshyPosed', me_pose)
bpy.context.scene.collection.objects.link(ob_pose)
for v, x in zip(bm.verts, Xb):
    v.co = Vector(x)
me = bpy.data.meshes.new('Body')
bm.to_mesh(me)
for m in mat_src:
    me.materials.append(m)
body = bpy.data.objects.new('Body', me)
bpy.context.scene.collection.objects.link(body)
a = me.attributes.new('piece', 'INT', 'POINT')
for i, d in enumerate(a.data):
    d.value = int(piece[i])
dom = W.argmax(1)
a = me.attributes.new('label_meshy', 'INT', 'POINT')
for i, d in enumerate(a.data):
    d.value = int(dom[i])
report['bone_scale'] = {bones[b]: round(float(np.cbrt(abs(np.linalg.det(T[b][:3, :3])))), 3)
                        for b in range(len(bones)) if has[b]}
report['bone_rot_deg'] = {}
for b in range(len(bones)):
    if has[b]:
        R = T[b][:3, :3] / np.cbrt(abs(np.linalg.det(T[b][:3, :3])))
        ang = math.degrees(math.acos(max(-1, min(1, (np.trace(R) - 1) / 2))))
        report['bone_rot_deg'][bones[b]] = round(ang, 1)
disp = np.linalg.norm(Xb - B, axis=1)
report['unpose_displacement'] = {'mean': float(disp.mean()), 'p95': float(np.percentile(disp, 95)),
                                 'max': float(disp.max())}
report['verts'] = n
report['faces'] = len(bm.faces)
# posed copies of the MM9 meshes (articulated fit result in Meshy space), for overlays
for o in [o for o in bpy.data.objects if o.type == 'MESH' and o.name not in ('Body', 'MeshyPosed')]:
    cp = o.copy(); cp.data = o.data.copy(); cp.name = 'MM9Posed_' + o.name
    cp.modifiers.clear(); cp.parent = None
    bpy.context.scene.collection.objects.link(cp)
    for v in cp.data.vertices:
        g = max(v.groups, key=lambda g: g.weight)
        bi = bidx[o.vertex_groups[g.group].name]
        v.co = cp.matrix_world.inverted() @ Vector(apply(T[bi], np.array([tuple(o.matrix_world @ v.co)]))[0])
bad = np.nonzero(np.linalg.norm(Xb - B, axis=1) > 3 * max(1.0, float(np.percentile(np.linalg.norm(Xb - B, axis=1), 99))))[0]
report['unpose_outliers'] = int(len(bad))
json.dump({'T': [t.tolist() for t in T], 'bones': bones}, open(OUT.replace('.blend', '_T.json'), 'w'))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(report, open(REP, 'w'), indent=1)
print('FIT ' + json.dumps({k: v for k, v in report.items() if k not in ('bone_scale', 'bone_rot_deg')}))
