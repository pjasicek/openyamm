"""Fit the cleaned Meshy goose to the MM9 GOOSE.abc bind pose (from mm9_wolf_claude/scripts/fit_quad.py).

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

}
BLEND = {}
LEG_TOP = float(os.environ.get('LEG_TOP', '0.02'))  # leg regions end this far above the MM9 leg root pivot
POSE_SIGMA = 0.03  # transient pose weights: soft-min width over the bone capsule distances
SIGMA = 0.013
HEAD_BONES = ['Xhead', 'Xbeak']

bpy.ops.wm.open_mainfile(filepath=SRC)
sc = bpy.context.scene
arm = bpy.data.objects['MM9_Rig']
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


def pitch_only(R):
    a = math.atan2(R[2, 1], R[1, 1])
    return np.array(Matrix.Rotation(a, 3, 'X'))


def icp_similarity(Bs, Adst, kdst, s, t, iters=30, rotate=False, fixed_scale=False, pitch=False):
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
            if pitch:
                R = pitch_only(R)
        if not fixed_scale:
            s = float((Q0 * (P0 @ R.T)).sum() / (P0 * P0).sum())
        t = mq - s * (R @ mp)
    return s, R, t


s, R, t = icp_similarity(Bs, A, kA, s, t, rotate=True, pitch=True)
t[0] = 0.0   # both mid-planes are x = 0
X = s * B @ R.T + t
t[2] -= X[:, 2].min(); X[:, 2] -= X[:, 2].min()   # stand on the floor (z = 0) like the MM9 bind
for v, x in zip(bm.verts, X):
    v.co = Vector(x)
report = {'global_scale': s, 'global_rot_deg': math.degrees(math.acos(max(-1, min(1, (np.trace(R) - 1) / 2)))),
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


def diffuse(w, iters):
    w = w.astype(float)
    for _ in range(iters):
        w = 0.5 * w + 0.5 * np.array([w[n].mean() if n else w[i] for i, n in enumerate(nbr)])
    return w


# ---------------- head ICP, blended into the neck
L = labels()
hw = diffuse(np.isin(L, HEAD_BONES), 8)
hid = np.nonzero(hw > 0.5)[0]
Ah = A[np.isin(lab, HEAD_BONES)]
Hp = np.array([tuple(co(i)) for i in hid])
ht = np.zeros(3)   # goose: no early head ICP; the head is placed by landmarks below
ht[0] = 0.0   # stay on the mirror plane
ht[:] = 0.0   # goose: the head is placed by landmarks after the legs (below)
for i in range(len(bm.verts)):
    if hw[i] > 1e-3 and piece[i] == 0:
        bm.verts[i].co = co(i) + Vector(hw[i] * ht)
report['head_icp_t'] = ht.tolist()
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


CHAIN_TIP = {'leg_r': ['Xtoeb'], 'leg_l': ['Xtoeb01']}   # tip = farthest vertex of these bones (middle toe)
CHAIN_TIP_JOINT = {'neck': 'Xhead'}                         # tip = this joint (the skull centre)
REGION_EXTRA = {'leg_r': ['Xtoea', 'Xtoeb', 'Xtoec'], 'leg_l': ['Xtoea01', 'Xtoeb01', 'Xtoec01']}


def chain_poly(names, cname=None):
    pts = [J[n].copy() for n in names]
    if cname in CHAIN_TIP_JOINT:
        return pts + [J[CHAIN_TIP_JOINT[cname]].copy()]
    tipv = A[np.isin(lab, CHAIN_TIP.get(cname, [names[-1]]))]
    far = tipv[np.argmax(np.linalg.norm(tipv - np.array(pts[-1]), axis=1))]
    pts.append(Vector(far))
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
        stv = min(1.2, max(0.85, db.length / da.length))   # large stretches crease the shoulders
        S = Matrix.Identity(4)
        for i_ in range(3):
            for j_ in range(3):
                S[i_][j_] += (stv - 1) * u[i_] * u[j_]
        mats.append(Matrix.Translation(b0) @ r @ S @ Matrix.Translation(-a0))
    return {'tip': list(co(tip)), 'meshy_len': ms[-1], 'mm9_len': ts[-1], 'src_joints': src_j, 'target': target_pts,
            'mats': mats, 'segment_stretch': [round((target_pts[k + 1] - target_pts[k]).length /
                                                   max((src_j[k + 1] - src_j[k]).length, 1e-6), 2)
                                             for k in range(len(ts) - 1)]}


report['chains'] = {}
names = list(CHAINS)
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
    bones = CHAINS[n]
    tp = chain_poly(bones, n)
    region = np.isin(seg_labels(P_now), bones + REGION_EXTRA.get(n, [])) & (piece == 0)
    if n.startswith('leg'):
        region &= P_now[:, 2] < J[bones[0]].z + LEG_TOP
    if n.startswith('wing'):
        region &= np.abs(P_now[:, 0]) > abs(J[bones[0]].x) + 0.02
    if n == 'neck':
        region &= P_now[:, 2] > J[bones[0]].z - 0.02   # above the neck base, not the breast
    rid = np.nonzero(region)[0]
    tip = int(min(rid, key=lambda i: (co(int(i)) - tp[-1]).length))
    keep = set(geodesic([tip], set(int(i) for i in rid)))   # the connected part of the region holding the tip
    region = np.zeros(len(region), bool); region[list(keep)] = True
    grow = diffuse(region, 4) > 0.02
    ids = [int(i) for i in np.nonzero(grow & (piece == 0))[0]]
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
    anc = arm.data.bones[b]
    while anc is not None and anc.name not in chain_bone:
        anc = anc.parent
    if anc is not None:
        n, j = chain_bone[anc.name]
        M = np.array(info[n]['mats'][min(j, len(info[n]['mats']) - 1)])
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
    anc = arm.data.bones[lab2[i]]
    while anc is not None and anc.name not in chain_bone:
        anc = anc.parent
    if anc is not None:
        chain_of[i] = list(info).index(chain_bone[anc.name][0])
report['chain_names'] = names
# ---------------- head by landmarks (crow lesson: bill direction and head up must match MM9). The Meshy goose holds
# its head lower and further back than MM9's bind. Landmarks: the mid-eye point and the bill tip (the most forward
# vertex). MM9's eyes are found through the skin: the dark eye texels at EYE_UV, mapped onto MM9's triangles.
# The head moves rigidly (mid-eye onto MM9's, bill turned onto MM9's bill direction, pitch only), and the neck takes
# the motion with a weight that falls off by geodesic distance from the head (smoothstep over NECK_FALL).
EYE_UV = (27.5 / 128, 1 - 12.5 / 128)
NECK_FALL = float(os.environ.get('NECK_FALL', '0.30'))
mm9o = next(o for o in bpy.data.objects if o.type == 'MESH' and o.name != 'Body' and o.data.uv_layers)
uvl = mm9o.data.uv_layers.active.data
eyes9 = []
for poly in mm9o.data.polygons:
    li = list(poly.loop_indices)
    for k in range(1, len(li) - 1):
        tri = [li[0], li[k], li[k + 1]]
        u = [np.array(uvl[t].uv) for t in tri]
        T2 = np.array([u[1] - u[0], u[2] - u[0]]).T
        if abs(np.linalg.det(T2)) < 1e-12:
            continue
        bc = np.linalg.solve(T2, np.array(EYE_UV) - u[0])
        if bc.min() >= -1e-6 and bc.sum() <= 1 + 1e-6:
            vs = [mm9o.matrix_world @ mm9o.data.vertices[mm9o.data.loops[t].vertex_index].co for t in tri]
            eyes9.append(np.array(vs[0]) * (1 - bc.sum()) + np.array(vs[1]) * bc[0] + np.array(vs[2]) * bc[1])
eyes9 = np.array(eyes9)
em9 = eyes9.mean(0); em9[0] = 0.0
tip9 = A[np.argmin(A[:, 1])]
eye_ids = np.nonzero(piece == 2)[0]
eye_now = np.array([np.array(P_fit0[i]) + (np.array(tuple(co(anchor[int(i)]))) - P_fit0[anchor[int(i)]])
                    for i in eye_ids])
em = eye_now.mean(0); em[0] = 0.0
Pc = np.array([tuple(v.co) for v in bm.verts])
tip_o = Pc[np.argmin(np.where(piece == 0, Pc[:, 1], 9))]
d9, do = tip9 - em9, tip_o - em
ang = math.atan2(d9[2], -d9[1]) - math.atan2(do[2], -do[1])   # pitch in the YZ plane (forward = -Y)
# head region: within 0.75 bill lengths of the mid-eye, or along the bill
blen = np.linalg.norm(do)
u = np.clip(((Pc - em) @ do) / (blen ** 2), 0, 1)
dseg = np.linalg.norm(Pc - (em + u[:, None] * do), axis=1)
head = ((np.linalg.norm(Pc - em, axis=1) < 0.75 * blen) | (dseg < 0.35 * blen)) & (piece == 0)
gd = geodesic([int(i) for i in np.nonzero(head)[0]], set(np.nonzero(piece == 0)[0].tolist()))
for i in np.nonzero(piece == 0)[0]:
    d = gd.get(int(i), 1e9)
    x = min(1.0, d / NECK_FALL)
    w = 1.0 - x * x * (3 - 2 * x)
    if w <= 1e-4:
        continue
    p = np.array(tuple(co(int(i))))
    R = np.array(Matrix.Rotation(-ang * w, 3, 'X'))
    bm.verts[int(i)].co = Vector(em + w * (em9 - em) + R @ (p - em))
report['head_landmarks'] = {'pitch_deg': math.degrees(ang), 'mid_eye_ours': em.tolist(), 'mid_eye_mm9': em9.tolist(),
                            'eyes_mm9': eyes9.tolist(), 'tip_ours': tip_o.tolist(), 'tip_mm9': tip9.tolist(),
                            'bill_len_ours': float(blen), 'bill_len_mm9': float(np.linalg.norm(d9)),
                            'head_verts': int(head.sum())}
# ---------------- neck re-centred on the MM9 neck joints. The Meshy neck is deeper (front-back) than MM9's and its
# centre lay ~4.5 cm in front of the XneckA..XneckE joints, so neck bends would pivot at the back of our neck. Per
# horizontal slice (the neck is near vertical), our neck's mid-depth moves onto the joint polyline and the depth is
# scaled by NECK_DEPTH about it; the effect ramps in above the shoulders and out below the head (NECK_Z).
NECK_DEPTH = float(os.environ.get('NECK_DEPTH', '0.85'))
NZ = [float(x) for x in os.environ.get('NECK_Z', '0.38,0.60,0.69,0.76').split(',')]
jz = np.array([J[n].z for n in ('XneckA', 'XneckC', 'XneckD', 'XneckE')])
jy = np.array([J[n].y for n in ('XneckA', 'XneckC', 'XneckD', 'XneckE')])
Pc = np.array([tuple(v.co) for v in bm.verts])
body_m = (piece == 0) & (Pc[:, 1] < 0.02)
zs = np.arange(NZ[0] - 0.02, NZ[3] + 0.02, 0.01)
mids = []
for z in zs:
    m = body_m & (np.abs(Pc[:, 2] - z) < 0.015)
    mids.append((Pc[m, 1].min() + Pc[m, 1].max()) / 2 if m.sum() > 3 else np.nan)
mids = np.array(mids)
ok = ~np.isnan(mids)
mids = np.interp(zs, zs[ok], mids[ok])
mids = np.convolve(np.pad(mids, 2, mode='edge'), np.ones(5) / 5, mode='valid')


def sstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


wz = sstep(NZ[0], NZ[1], Pc[:, 2]) * (1 - sstep(NZ[2], NZ[3], Pc[:, 2]))
yc = np.interp(Pc[:, 2], zs, mids)
yj = np.interp(Pc[:, 2], jz, jy)
ynew = yj + NECK_DEPTH * (Pc[:, 1] - yc)
for i in np.nonzero((wz > 1e-4) & (piece == 0))[0]:
    v = bm.verts[int(i)]
    v.co.y = Pc[i, 1] + wz[i] * (ynew[i] - Pc[i, 1])
report['neck_recentre'] = {'mid_before': dict(zip([round(z, 2) for z in zs[::3]], np.round(mids[::3], 3).tolist())),
                           'depth': NECK_DEPTH, 'zramp': NZ}
# ---------------- legs (replaces the chain fit for the goose: the LBS chain twisted the webbed feet). Our Meshy legs
# stand like MM9's (short tarsus below the body, webbed feet flat, toes forward) but not exactly at MM9's joints,
# which are staggered (left foot 3.4 cm behind). Each leg moves by the offset between our tarsus and MM9's in the
# ground plane (centroids of the band LEG_BAND), fully below the body and fading out by LEG_FADE; then the foot
# turns about the vertical through MM9's ankle (Xfoot) so our three toes' mean direction (peaks of the foot's reach
# over the ground angle) matches MM9's toe tips. Leg vertices below the hip pivot get chain k for rig_body.py.
LEG_BAND = (0.065, 0.095)
LEG_FADE = (0.10, 0.17)
LEG_R = 0.06
FEET = {0: ('Xleg', 'Xfoot', ['Xtoea', 'Xtoeb', 'Xtoec']), 1: ('Xleg01', 'Xfoot01', ['Xtoea01', 'Xtoeb01', 'Xtoec01'])}
report['legs'] = {}


def sst(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


for k, (leg, foot, toes) in (FEET.items() if os.environ.get('NOLEGS') != '1' else []):
    Pc = np.array([tuple(v.co) for v in bm.verts])
    ank = np.array(J[foot])
    sgn = np.sign(ank[0])
    j0, j1 = np.array(J[leg]), np.array(J[foot])     # MM9 tarsus axis (its low-poly leg has no vertex in the band)
    zm = sum(LEG_BAND) / 2
    mc = j0 + (j1 - j0) * (zm - j0[2]) / (j1[2] - j0[2])
    hd = np.linalg.norm(Pc[:, :2] - mc[:2], axis=1)
    oband = (piece == 0) & (np.sign(Pc[:, 0]) == sgn) & (Pc[:, 2] > LEG_BAND[0]) & (Pc[:, 2] < LEG_BAND[1]) & (hd < LEG_R)
    oc = Pc[oband].mean(0)
    dlt = mc - oc; dlt[2] = 0.0
    region = (piece == 0) & (np.sign(Pc[:, 0]) == sgn) & (Pc[:, 2] < LEG_FADE[1]) & (hd < LEG_R * 1.5)
    for i in np.nonzero(region)[0]:
        w = (1 - sst(*LEG_FADE, Pc[i, 2])) * (1 - sst(LEG_R, LEG_R * 1.5, hd[i]))
        bm.verts[int(i)].co = Vector(Pc[i] + w * dlt)
    Pc = np.array([tuple(v.co) for v in bm.verts])
    # foot yaw
    md = []
    for t in toes:
        tv = A[lab == t]
        tip = tv[np.argmax(np.linalg.norm(tv - ank, axis=1))]
        md.append(math.atan2(tip[1] - ank[1], tip[0] - ank[0]))
    mid = math.atan2(np.mean(np.sin(md)), np.mean(np.cos(md)))
    hd = np.linalg.norm(Pc[:, :2] - ank[:2], axis=1)
    # our own ankle: the tarsus centroid just above the web (angles from MM9's ankle are skewed by any offset)
    ab = (piece == 0) & (np.sign(Pc[:, 0]) == sgn) & (Pc[:, 2] > 0.035) & (Pc[:, 2] < 0.065) & (hd < 0.05)
    ank = np.array([*Pc[ab, :2].mean(0), ank[2]])
    hd = np.linalg.norm(Pc[:, :2] - ank[:2], axis=1)
    sel = np.nonzero((piece == 0) & (np.sign(Pc[:, 0]) == sgn) & (Pc[:, 2] < 0.03) & (hd < 0.12))[0]
    H = Pc[sel][:, :2] - ank[:2]
    th = np.arctan2(H[:, 1], H[:, 0]); rr = np.linalg.norm(H, axis=1)
    front = np.abs((th - mid + math.pi) % (2 * math.pi) - math.pi) < math.radians(80)
    st_ = math.radians(4)
    bins = np.arange(-math.pi, math.pi, st_)
    reach = np.array([rr[front & (th >= a) & (th < a + st_)].max() if (front & (th >= a) & (th < a + st_)).any() else 0
                      for a in bins])
    peaks = []
    for idx in np.argsort(-reach):
        a = bins[idx] + st_ / 2
        if all(abs((a - q + math.pi) % (2 * math.pi) - math.pi) > math.radians(25) for q in peaks):
            peaks.append(a)
        if len(peaks) == 3:
            break
    ours = math.atan2(np.mean(np.sin(peaks)), np.mean(np.cos(peaks)))
    yaw = (mid - ours + math.pi) % (2 * math.pi) - math.pi
    for i in np.nonzero((piece == 0) & (np.sign(Pc[:, 0]) == sgn) & (Pc[:, 2] < ank[2] + 0.03) & (hd < 0.12))[0]:
        g = 1 - sst(ank[2], ank[2] + 0.03, Pc[i, 2])
        R = np.array(Matrix.Rotation(yaw * g, 3, 'Z'))
        q = Pc[i] - ank; q[2] = 0
        bm.verts[int(i)].co = Vector(np.append((R[:2, :2] @ q[:2]) + ank[:2], Pc[i, 2]))
    Pc = np.array([tuple(v.co) for v in bm.verts])
    H = Pc[sel][:, :2] - ank[:2]
    th = np.arctan2(H[:, 1], H[:, 0]); rr = np.linalg.norm(H, axis=1)
    peaks_after = []
    for p_ in peaks:
        a = p_ + yaw
        m = np.abs((th - a + math.pi) % (2 * math.pi) - math.pi) < math.radians(12)
        peaks_after.append(float(th[m][np.argmax(rr[m])]) if m.any() else float(a))
    hd = np.linalg.norm(Pc[:, :2] - np.array(J[leg])[:2], axis=1)
    hd2 = np.linalg.norm(Pc[:, :2] - ank[:2], axis=1)
    legv = (piece == 0) & (np.sign(Pc[:, 0]) == sgn) & (((Pc[:, 2] < J[leg].z - 0.005) & (hd < LEG_R * 1.2)) |
                                                          ((Pc[:, 2] < 0.035) & (hd2 < 0.15)))   # + the whole web
    chain_of[legv] = k
    report['legs'][leg] = {'shift': dlt.tolist(), 'toes_mm9_deg': math.degrees(mid), 'toes_ours_deg': math.degrees(ours),
                           'yaw_deg': math.degrees(yaw), 'peaks_deg': sorted(round(math.degrees(p_), 1) for p_ in peaks),
                           'chain_verts': int(legv.sum()), 'ankle_ours': ank.tolist(),
                           'toe_dirs_after_rad': sorted(peaks_after)}
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
