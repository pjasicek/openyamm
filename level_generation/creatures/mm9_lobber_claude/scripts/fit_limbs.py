"""Fit the Meshy Smart Topology mesh to the (re-oriented) MM9 bind pose: global similarity, local head ICP, then
every limb mapped onto its MM9 bone chain.

Args: <mm9 source blend> <meshy glb> <body: lobber|pod> <out blend> <report json>

1. Global: uniform scale from the bounding-box height, centred in x/y, bottom on the floor, refined by symmetric
   nearest-point ICP (lobber: scale + translation; pod: translation only; yaw stays 0: both face -Y).
2. Pieces: welded connected components. Small pieces (mouth tendrils, teeth) become piece 2 and later follow the
   nearest body vertex rigidly. Lobber: bulb, stalk, head and six separate limb components are classified.
3. Head (lobber): translation-only ICP of the head component (with its small pieces) onto the MM9 head/jaw vertices.
4. Limbs: for each MM9 chain (root pivot ... tip), the matching Meshy tip is a geodesic extremity (Hungarian
   assignment by distance, same side). The Meshy limb centreline = centroids of geodesic-distance bins from the tip,
   cut where it passes closest to the MM9 chain root. Arc length maps piecewise linearly onto the MM9 chain polyline
   (the sharpest Meshy bend onto the sharpest MM9 joint, both over 25 deg; else one linear map); every
   vertex (parameterised by its geodesic distance from the tip) keeps its offset in a parallel-transported frame. Near the root the move blends out over BLEND metres
   (attached limbs only), so the body junction stays continuous. The stalk (lobber) is fitted the same way.
Per-vertex attributes: 'piece' (0 body, 2 small piece) and 'chain' (-1 core, k = chain index) for rig_body.py.
"""
import bpy, bmesh, sys, json, math, heapq
import numpy as np
from mathutils import Vector, Matrix
from mathutils.kdtree import KDTree
import itertools


def linear_sum_assignment(cost):
    """Exact minimum-cost assignment of every column to a distinct row (small problems, brute force)."""
    nr, nc = cost.shape
    best = (1e18, None)
    for rows in itertools.permutations(range(nr), nc):
        c = sum(cost[r, j] for j, r in enumerate(rows))
        if c < best[0]:
            best = (c, rows)
    rows = best[1]
    pairs = sorted((r, j) for j, r in enumerate(rows))
    return [a for a, _ in pairs], [b for _, b in pairs]

argv = sys.argv[sys.argv.index('--') + 1:]
SRC, MESHY, BODY, OUT, REP = argv
BLEND = 0.05
LBS_BEND = False  # pod: proportional joint placement (the sharpest Meshy bend is often a foot fork)
NB = 40
CFG = {
    'lobber': {
        'chains': {
            'XA': ['XApivot', 'XAarm', 'XAmid', 'XAclaw'], 'XA01': ['XApivot01', 'XAarm01', 'XAmid01', 'XAclaw01'],
            'XB': ['XBpiv', 'XBarm', 'XBmid', 'XBclaw'], 'XB01': ['XBpiv01', 'XBarm01', 'XBmid01', 'XBclaw01'],
            'XC': ['XCbase', 'XCpiv', 'XCarm'], 'XC01': ['XCbase01', 'XCpiv01', 'XCarm01'],
        },
        'stalk': ['Xstembase', 'XstemA', 'XstemB', 'XstemC', 'Xpodbase', 'Xheadpiv'],
        'head_bones': ['Xheadpiv', 'Xhead', 'Xheadmid', 'Xjawbase', 'Xjawpiv', 'Xjaw', 'Xmouth', 'Xchin', 'XCbase',
                       'XCbase01', 'XApivot', 'XApivot01', 'XBpiv', 'XBpiv01', 'Xpodbase'],
    },
    'pod': {
        'chains': {
            'arm': ['Xarmpiv', 'Xarm', 'Xspike', 'Xclaw'], 'arm01': ['Xarmpiv01', 'Xarm02', 'Xspike01', 'Xclaw01'],
            'aleg': ['Xalegpiv', 'Xaleg', 'Xarm.001', 'Xatip'], 'aleg01': ['Xalegpiv01', 'Xaleg01', 'Xarm01', 'Xatip01'],
            'bleg': ['Xblegpiv', 'Xbleg', 'Xbarm', 'Xbtip'],
        },
        'stalk': None, 'head_bones': None,
    },
}[BODY]

bpy.ops.wm.open_mainfile(filepath=SRC)
sc = bpy.context.scene
arm = bpy.data.objects['MM9_Rig']
dg = bpy.context.evaluated_depsgraph_get()
J = {b.name: Vector(b.head_local) for b in arm.data.bones}  # armature matrix is identity after the apply
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


# ---------------- import Meshy, global alignment
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


s, R, t = icp_similarity(Bs, A, kA, s, t, fixed_scale=(BODY == 'pod'))
X = s * B @ R.T + t
for v, x in zip(bm.verts, X):
    v.co = Vector(x)
report = {'global_scale': s, 'global_translate': t.tolist()}

# ---------------- components
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
co = lambda i: bm.verts[i].co
cent = lambda c: sum((co(i) for i in c), Vector()) / len(c)
piece = np.zeros(len(bm.verts), int)
chain_of = np.full(len(bm.verts), -1, int)
small = [c for c in comps if len(c) < 120]
for c in small:
    piece[c] = 2
big = [c for c in comps if len(c) >= 120]
report['components'] = [len(c) for c in comps]


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
    last = names[-1]
    tipv = A[lab == last]
    if len(tipv) == 0:
        tipv = A[lab == names[-2]]
    far = tipv[np.argmax(np.linalg.norm(tipv - np.array(pts[0]), axis=1))]
    pts.append(Vector(far))
    return pts  # root ... tip


def arc(pts):
    s = [0.0]
    for a, b in zip(pts, pts[1:]):
        s.append(s[-1] + (b - a).length)
    return s


def at(pts, sl, x):
    """point and tangent at arc length x; extrapolates linearly beyond both ends"""
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


def frames(pts, sl, n=80):
    """parallel-transported frames at n samples: list of (s, p, Matrix cols t, n, b)"""
    out = []
    prev = None
    for k in range(n + 1):
        x = sl[-1] * k / n
        p, _ = at(pts, sl, x)
        a, _ = at(pts, sl, max(0, x - sl[-1] / n))
        b, _ = at(pts, sl, min(sl[-1], x + sl[-1] / n))
        tg = (b - a).normalized()
        if prev is None:
            ref = Vector((0, 0, 1)) if abs(tg.z) < 0.9 else Vector((0, 1, 0))
            nn = (ref - tg * ref.dot(tg)).normalized()
        else:
            nn = prev - tg * prev.dot(tg)
            nn = nn.normalized()
        prev = nn
        out.append((x, p, Matrix((tg, nn, tg.cross(nn))).transposed()))
    return out


def frame_at(fr, x):
    if x <= 0:
        s0, p0, F0 = fr[0]
        return p0 + F0.col[0] * x, F0
    if x >= fr[-1][0]:
        s1, p1, F1 = fr[-1]
        return p1 + F1.col[0] * (x - s1), F1
    k = min(range(len(fr) - 1), key=lambda i: abs(fr[i][0] - x))
    s0, p0, F0 = fr[k]
    return p0 + F0.col[0] * (x - s0), F0


def project_s(pts, sl, v):
    best = (1e9, 0.0)
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        ab = b - a
        L2 = ab.length_squared
        u = (v - a).dot(ab) / L2 if L2 > 0 else 0
        if (i > 0 and u < 0) or (i < len(pts) - 2 and u > 1):
            u = max(0.0, min(1.0, u))
        q = a + ab * u
        d = (v - q).length
        if d < best[0]:
            best = (d, sl[i] + u * math.sqrt(L2))
    return best[1]


def fit_chain(ids, tip, root_target, target_pts, attached, label):
    """ids: candidate vertex ids; tip: Meshy tip vertex; target_pts: MM9 polyline root..tip"""
    allowed = set(ids)
    gd = geodesic([tip], allowed)
    gmax = max(gd.values())
    bins = [[] for _ in range(NB)]
    for i, d in gd.items():
        bins[min(NB - 1, int(d / gmax * NB))].append(co(i))
    gbin = [[] for _ in range(NB)]
    for i, d in gd.items():
        gbin[min(NB - 1, int(d / gmax * NB))].append(d)
    cl = [co(tip).copy()] + [sum(b, Vector()) / len(b) for b in bins if b]
    cg = [0.0] + [sum(g) / len(g) for g in gbin if g]  # mean geodesic distance of each centreline point
    for _ in range(3):
        cl = [cl[0]] + [(cl[i - 1] + 2 * cl[i] + cl[i + 1]) / 4 for i in range(1, len(cl) - 1)] + [cl[-1]]
    cs = arc(cl)
    # cut: centreline point nearest to the MM9 chain root
    kcut = min(range(len(cl)), key=lambda k: (cl[k] - root_target).length)
    if not attached:
        kcut = len(cl) - 1
    s_root = cs[kcut]
    mesh_pts = list(reversed(cl[:kcut + 1]))  # root ... tip
    ms = arc(mesh_pts)
    tp = target_pts
    ts = arc(tp)
    if not attached:
        # separate piece: its root end maps onto the MM9 chain root, the tip onto the tip
        pass
    f_src = frames(mesh_pts, ms)
    f_dst = frames(tp, ts)

    def bend_s(pts, sl, internal):
        """arc length of the sharpest bend (turning angle over a +-window) away from the ends"""
        best = (-1.0, sl[-1] / 2)
        for kk in internal:
            a, b, c = pts[kk[0]], pts[kk[1]], pts[kk[2]]
            u, w = (b - a), (c - b)
            if u.length < 1e-6 or w.length < 1e-6:
                continue
            ang = u.angle(w)
            if ang > best[0]:
                best = (ang, sl[kk[1]])
        return best

    n = len(mesh_pts)
    win = max(2, n // 10)
    ib, sb = bend_s(mesh_pts, ms, [(k - win, k, k + win) for k in range(max(win, n // 5), min(n - win, n - n // 5))])
    tb_ang, tb = bend_s(tp, ts, [(k - 1, k, k + 1) for k in range(1, len(tp) - 1)])
    use_bend = ib > math.radians(25) and tb_ang > math.radians(25)

    def map_x(x):
        if not use_bend:
            return x * ts[-1] / ms[-1]
        if x <= sb:
            return x * tb / sb
        return tb + (x - sb) * (ts[-1] - tb) / (ms[-1] - sb)
    k = ts[-1] / ms[-1]
    cs_tip = arc(cl)

    def arc_from_tip(g):
        for j in range(len(cg) - 1):
            if g <= cg[j + 1] or j == len(cg) - 2:
                h = cg[j + 1] - cg[j]
                a = (g - cg[j]) / h if h > 0 else 0.0
                return cs_tip[j] + a * (cs_tip[j + 1] - cs_tip[j])
        return cs_tip[-1]
    moved = 0
    newpos = {}
    for i in ids:
        if attached and gd.get(i, 1e9) > s_root + BLEND:
            continue
        v = co(i)
        g = gd.get(i, gmax)
        st = arc_from_tip(g)
        x = ms[-1] - st
        p0, F0 = frame_at(f_src, x)
        p1, F1 = frame_at(f_dst, map_x(x))
        q = p1 + F1 @ (F0.transposed() @ (v - p0))
        if attached:
            g = gd.get(i, 1e9)
            w = 1.0 if g <= s_root - BLEND else max(0.0, (s_root + BLEND - g) / (2 * BLEND))
            w = w * w * (3 - 2 * w)
            q = v.lerp(q, w)
            if w > 0.5:
                chain_of[i] = label
        else:
            chain_of[i] = label
        newpos[i] = q
        moved += 1
    for i, q in newpos.items():
        bm.verts[i].co = q
    return {'tip': list(co(tip)), 'meshy_len': ms[-1], 'mm9_len': ts[-1], 'stretch': k, 'moved': moved,
            'bend': [math.degrees(ib), sb, math.degrees(tb_ang), tb] if use_bend else None}


def geodesic_pred(src, allowed):
    dist = {src: 0.0}
    pred = {src: None}
    pq = [(0.0, src)]
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
                dist[j] = nd; pred[j] = i; heapq.heappush(pq, (nd, j))
    return dist, pred


def fit_chain_lbs(ids, tip, target_pts, label, sigma=0.02):
    """Skeleton-driven fit of an attached limb: joints estimated on the Meshy centreline at the MM9 joint arc
    fractions (sharpest bend landmark as in fit_chain), each segment posed onto its MM9 segment (minimal rotation,
    stretch along the segment only), vertices blended between segments by distance, the root blended to rest."""
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
    ts = arc(target_pts)
    # bend landmark
    n = len(mesh_pts)
    win = max(2, n // 10)
    best = (-1.0, ms[-1] / 2)
    for k in range(max(win, n // 5), min(n - win, n - n // 5)):
        u = mesh_pts[k] - mesh_pts[k - win]; w = mesh_pts[k + win] - mesh_pts[k]
        if u.length > 1e-6 and w.length > 1e-6 and u.angle(w) > best[0]:
            best = (u.angle(w), ms[k])
    tb = max(range(1, len(target_pts) - 1),
             key=lambda k: (target_pts[k] - target_pts[k - 1]).angle(target_pts[k + 1] - target_pts[k]))
    use_bend = LBS_BEND and best[0] > math.radians(25)

    def inv_map(xt):  # MM9 arc -> Meshy arc
        if not use_bend:
            return xt * ms[-1] / ts[-1]
        if xt <= ts[tb]:
            return xt * best[1] / ts[tb]
        return best[1] + (xt - ts[tb]) * (ms[-1] - best[1]) / (ts[-1] - ts[tb])
    src_j = [at(mesh_pts, ms, inv_map(x))[0] for x in ts]
    src_j[0] = mesh_pts[0].copy(); src_j[-1] = mesh_pts[-1].copy()
    mats = []
    for k in range(len(ts) - 1):
        a0, a1 = src_j[k], src_j[k + 1]
        b0, b1 = target_pts[k], target_pts[k + 1]
        da, db = (a1 - a0), (b1 - b0)
        if da.length < 1e-6:
            mats.append(Matrix.Translation(b0 - a0)); continue
        r = da.normalized().rotation_difference(db.normalized()).to_matrix().to_4x4()
        u = da.normalized()
        st = db.length / da.length
        S = Matrix.Identity(4)
        for i_ in range(3):
            for j_ in range(3):
                S[i_][j_] += (st - 1) * u[i_] * u[j_]
        mats.append(Matrix.Translation(b0) @ r @ S @ Matrix.Translation(-a0))
    root_g = ms[-1]  # geodesic-ish distance of the root from the tip

    def seg_dist(p, k):
        a, b = src_j[k], src_j[k + 1]
        ab = b - a
        u = max(0.0, min(1.0, (p - a).dot(ab) / max(ab.length_squared, 1e-12)))
        return (p - (a + ab * u)).length, u
    newpos = {}
    for i in ids:
        g = gd.get(i, 1e9)
        if g > root_g + BLEND:
            continue
        p = co(i)
        dists = [seg_dist(p, k) for k in range(len(mats))]
        dmin = min(d for d, _ in dists)
        ws = [math.exp(-((d - dmin) / sigma) ** 2) for d, _ in dists]
        # the root segment's start: blend to rest across the junction
        wr = 1.0 if g <= root_g - BLEND else max(0.0, (root_g + BLEND - g) / (2 * BLEND))
        wr = wr * wr * (3 - 2 * wr)
        tot = sum(ws)
        q = Vector()
        for w, M in zip(ws, mats):
            q += (M @ p) * (w / tot)
        newpos[i] = p.lerp(q, wr)
        if wr > 0.5:
            chain_of[i] = label
    for i, q in newpos.items():
        bm.verts[i].co = q
    return {'tip': list(co(tip)), 'meshy_len': ms[-1], 'mm9_len': ts[-1], 'moved': len(newpos),
            'bend_deg': math.degrees(best[0]) if use_bend else None,
            'segment_stretch': [round((target_pts[k + 1] - target_pts[k]).length /
                                      max((src_j[k + 1] - src_j[k]).length, 1e-6), 2) for k in range(len(ts) - 1)]}


chains = CFG['chains']
names = list(chains)
targets = {n: chain_poly(chains[n]) for n in names}

if BODY == 'lobber':
    # classify the big components
    head_c = max((c for c in comps if cent(c).z > 0.5), key=len)
    bulbs = [c for c in comps if len(c) >= 120 and cent(c).z < 0.3]
    stalk_c = min((c for c in comps if len(c) >= 120 and c is not head_c and c not in bulbs),
                  key=lambda c: (cent(c) - J['XstemB']).length)
    limbs = [c for c in comps if len(c) >= 150 and abs(cent(c).x) > 0.1 and cent(c).z >= 0.3]
    claimed = {id(c) for c in [head_c, stalk_c] + bulbs + limbs}
    small = [c for c in comps if id(c) not in claimed]
    piece[:] = 0
    for c in small:
        piece[c] = 2
    bulb = [i for c in bulbs for i in c]
    report['lobber_pieces'] = {'bulb': [len(c) for c in bulbs], 'head': len(head_c), 'stalk': len(stalk_c),
                               'limbs': [len(c) for c in limbs], 'small': [len(c) for c in small]}
    # head ICP (head comp + small pieces near it) onto the MM9 head vertices
    hb = np.isin(lab, CFG['head_bones'])
    Ah = A[hb]
    hid = list(head_c) + [i for c in small for i in c]
    Hp = np.array([tuple(co(i)) for i in hid])
    hs, hR, ht = icp_similarity(Hp, Ah, kdt(Ah), 1.0, np.zeros(3), iters=25, fixed_scale=True)
    for i, p in zip(hid, Hp):
        bm.verts[i].co = Vector(hs * hR @ p + ht)
    report['head_icp'] = {'scale': hs, 'rot_deg': math.degrees(math.acos(max(-1, min(1, (np.trace(hR) - 1) / 2)))),
                          't': ht.tolist()}
    # limbs move with the head first (they hang on it), then fit to their chains
    lid = [i for c in limbs for i in c]
    for i in lid:
        bm.verts[i].co = Vector(hs * hR @ np.array(tuple(co(i))) + ht)
    # tips: farthest vertex from the head centroid per limb component
    # tips: the vertex geodesically farthest from the limb's attachment (its vertex nearest the head)
    k_head = KDTree(len(head_c))
    for j, i in enumerate(head_c):
        k_head.insert(co(i), j)
    k_head.balance()
    tips = []
    for c in limbs:
        root_v = min(c, key=lambda i: k_head.find(co(i))[2])
        g = geodesic([root_v], set(c))
        tips.append(max(g, key=g.get))
    cost = np.array([[(co(tp) - targets[n][-1]).length + (0 if np.sign(co(tp).x) == np.sign(targets[n][-1].x) else 10)
                      for n in names] for tp in tips])
    r_, c_ = linear_sum_assignment(cost)
    report['limbs'] = {}
    for ri, ci in zip(r_, c_):
        n = names[ci]
        report['limbs'][n] = fit_chain(limbs[ri], tips[ri], targets[n][0], targets[n], False, ci)
    # stalk: bottom end on Xstembase, top on Xheadpiv
    stalk_t = [J[b].copy() for b in CFG['stalk']]
    bot = min(stalk_c, key=lambda i: co(i).z)
    g = geodesic([bot], set(stalk_c))
    top = max(g, key=g.get)
    report['stalk'] = fit_chain(stalk_c, top, stalk_t[0], stalk_t, False, len(names))
    # stalk tip index ordering: fit_chain maps tip->last target point; here 'tip' is the top, so the polyline
    # must run bottom (root) ... top (tip)
else:
    # pod (Smart Topology v2): body with the rear spike, four separate limb pieces, small mouth pieces
    body_c = comps[0]
    limbs = [c for c in comps[1:] if len(c) >= 150 and abs(cent(c).x) > 0.05]
    claimed = {id(c) for c in [body_c] + limbs}
    small = [c for c in comps if id(c) not in claimed]
    piece[:] = 0
    for c in small:
        piece[c] = 2
    k_body = KDTree(len(body_c))
    for j, i in enumerate(body_c):
        k_body.insert(co(i), j)
    k_body.balance()
    tips = []
    for c in limbs:
        root_v = min(c, key=lambda i: k_body.find(co(i))[2])
        g = geodesic([root_v], set(c))
        tips.append(max(g, key=g.get))
    mc = Vector(A[np.isin(lab, ['XCENTER', 'Xhinge', 'Xheadpiv', 'Xhead', 'Xjawpiv', 'Xjaw'])].mean(0))
    bc = cent(body_c)
    four = [n for n in names if n != 'bleg']
    cost = np.array([[(co(tp) - bc).angle(targets[n][-1] - mc) + (0 if np.sign(co(tp).x) == np.sign(targets[n][-1].x)
                                                                  else 2) for n in four] for tp in tips])
    r_, c_ = linear_sum_assignment(cost)
    report['pod_pieces'] = {'body': len(body_c), 'limbs': [len(c) for c in limbs], 'small': [len(c) for c in small]}
    report['limbs'] = {}
    for ri, ci in zip(r_, c_):
        n = four[ci]
        report['limbs'][n] = fit_chain(limbs[ri], tips[ri], targets[n][0], targets[n], False, names.index(n))
    # rear leg: the spike under the body, skinned onto the MM9 back-leg chain
    spike_tip = min(body_c, key=lambda i: co(i).z + 2 * abs(co(i).x))
    report['limbs']['bleg'] = fit_chain_lbs(body_c, spike_tip, targets['bleg'], names.index('bleg'))
report['chain_names'] = names + (['stalk'] if CFG['stalk'] else [])

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
print('FIT ' + json.dumps({k: v for k, v in report.items() if k != 'extremities'}, default=str))
