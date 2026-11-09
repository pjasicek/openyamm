"""Fit the Meshy Smart Topology Magreeb to the MM9 MAGREEB.abc bind pose, lifted so the lowest bind point is on the
floor (helpers from mm9_lobber_claude/scripts/fit_limbs.py, structure from mm9_eye_claude/scripts/fit_eye.py).

Args: <mm9 source blend> <meshy glb> <out blend> <report json>

1. Core: body (abdomen + thorax), head with horn and the small mouth/eye pieces are scaled and translated (both face
   -Y) by symmetric nearest-point ICP onto the MM9 non-limb vertices; the head piece then gets its own rigid ICP
   (rotation allowed) onto the MM9 head vertices (mag_cfg.HEAD).
2. Legs (four separate pieces): fit_chain onto the MM9 leg chains, assigned by tip position and side.
3. Arms: the pieces of one side (claw, forearm, upper arm) are fitted together by rigid ICP (rotation + translation)
   onto that side's MM9 arm vertices, then each piece is refined by its own rigid ICP onto the arm vertices.
Per-vertex attributes: 'piece' (0 body/limb, 2 small rigid piece) and 'chain' (-1 core, k = index in mag_cfg).
"""
import bpy, bmesh, sys, os, json, math, heapq, itertools
import numpy as np
from mathutils import Vector, Matrix
from mathutils.kdtree import KDTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mag_cfg as E


def linear_sum_assignment(cost):
    """Exact minimum-cost assignment (rows = pieces, cols = chains, equal counts) by dynamic programming."""
    n = cost.shape[0]
    best = {0: (0.0, [])}
    for r in range(n):
        nxt = {}
        for mask, (c, assign) in best.items():
            for j in range(cost.shape[1]):
                if mask & (1 << j):
                    continue
                m2 = mask | (1 << j)
                v = c + cost[r, j]
                if m2 not in nxt or v < nxt[m2][0]:
                    nxt[m2] = (v, assign + [j])
        best = nxt
    c, assign = min(best.values(), key=lambda x: x[0])
    return list(range(n)), assign


argv = sys.argv[sys.argv.index('--') + 1:]
SRC, MESHY, OUT, REP = argv
BLEND = 0.05
LBS_BEND = False
NB = 40
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
        n = o.vertex_groups[g.group].name
        mm9_l.append(E.RELABEL.get(n, n))
A = np.array([tuple(p) for p in mm9_p])
lab = np.array(mm9_l)

def kdt(P):
    k = KDTree(len(P))
    for i, p in enumerate(P):
        k.insert(Vector(p), i)
    k.balance()
    return k


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



# ---------------- import Meshy
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
co = lambda i: bm.verts[i].co
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
B = np.array([tuple(v.co) for v in bm.verts])
labels_count = {n: int((lab == n).sum()) for n in sorted(set(lab))}

# ---------------- classify (Meshy space: faces -Y, z up)
body_c = comps[0]
head_c = max(comps[1:], key=lambda c: B[c][:, 2].max() if len(c) >= 120 else -9)
small = [c for c in comps if len(c) < 120]
rest = [c for c in comps[1:] if len(c) >= 120 and c is not head_c]
bmin = B[body_c].min(0)
legs = [c for c in rest if B[c][:, 2].min() < bmin[2] - 0.05]
arms = [c for c in rest if not any(c is l for l in legs)]
report = {'components': [len(c) for c in comps], 'labels': labels_count,
          'pieces': {'body': len(body_c), 'head': len(head_c), 'legs': [len(c) for c in legs],
                     'arms': [len(c) for c in arms], 'small': [len(c) for c in small]}}
assert len(legs) == 4, report['pieces']

# ---------------- core similarity
limb_bones = {b for ch in E.CHAINS for b in ch[1:]}
core_mask = ~np.isin(lab, list(limb_bones))
Ac = A[core_mask]
core_ids = list(body_c) + list(head_c) + [i for c in small for i in c]
Bc = B[core_ids]
s = (Ac[:, 2].max() - Ac[:, 2].min()) / (Bc[:, 2].max() - Bc[:, 2].min())
t = Ac.mean(0) - s * Bc.mean(0)
kA = kdt(Ac)
rng = np.random.default_rng(0)
Bs = Bc[rng.choice(len(Bc), min(3000, len(Bc)), replace=False)]
s, R, t = icp_similarity(Bs, Ac, kA, s, t, iters=30)
X = s * B @ R.T + t
for v, x in zip(bm.verts, X):
    v.co = Vector(x)
B = X
report['global_scale'] = s
report['global_translate'] = t.tolist()


def rigid_icp(ids, Adst, iters=30):
    P = B[ids]
    k = kdt(Adst)
    s_, R_, t_ = icp_similarity(P, Adst, k, 1.0, np.zeros(3), iters=iters, rotate=True, fixed_scale=True)
    Y = P @ R_.T + t_
    for i, y in zip(ids, Y):
        bm.verts[i].co = Vector(y)
        B[i] = y
    ang = math.degrees(math.acos(max(-1, min(1, (np.trace(R_) - 1) / 2))))
    return {'rot_deg': ang, 't': t_.tolist()}


# head + its small pieces (eyes, teeth) onto the MM9 head vertices
hid = list(head_c) + [i for c in small for i in c if np.linalg.norm(B[c].mean(0) - B[head_c].mean(0)) < 0.35]
report['head_icp'] = rigid_icp(hid, A[np.isin(lab, E.HEAD)])
piece = np.zeros(len(bm.verts), int)
chain_of = np.full(len(bm.verts), -1, int)
for c in small:
    piece[c] = 2

# ---------------- legs
nl = len(E.LEGS)
targets = {}
for k in range(nl):
    # MM9 feet end in a short sideways hook (tip bone); our legs end straight (front pair forked), so the target
    # continues the last segment's direction by the hook's length instead of turning into the hook
    cp = chain_poly(E.LEGS[k])
    hook = (cp[-1] - cp[-2]).length
    d = (cp[-2] - cp[-3]).normalized()
    targets[k] = cp[:-1] + [cp[-2] + d * hook]
kb = KDTree(len(body_c))
for j, i in enumerate(body_c):
    kb.insert(co(i), j)
kb.balance()
tips, roots = [], []
for c in legs:
    root_v = min(c, key=lambda i: kb.find(co(i))[2])
    g = geodesic([root_v], set(c))
    tips.append(max(g, key=g.get))
    roots.append(root_v)
cost = np.array([[(co(tp) - targets[k][-1]).length + (0 if np.sign(co(tp).x) == np.sign(targets[k][-1].x) else 10)
                  for k in range(nl)] for tp in tips])
rows, cols = linear_sum_assignment(cost)
report['chains'] = {}
for r, k in zip(rows, cols):
    # centreline from the attachment (geodesic bins from the root), so the front legs' forked feet average into one
    # foot instead of folding the centreline: the chain is passed reversed (MM9 tip ... root)
    report['chains'][E.LEGS[k][0]] = fit_chain(legs[r], roots[r], targets[k][-1], list(reversed(targets[k])), False, k)

# ---------------- arms: one centreline through the arm's pieces mapped onto the MM9 arm chain
def piece_centreline(c, start_pt):
    """centreline of a connected piece from its end nearest start_pt to its far end: (points, per-vertex arc)."""
    root = min(c, key=lambda i: (Vector(B[i]) - Vector(start_pt)).length)
    g0 = geodesic([root], set(c))
    tip = max(g0, key=g0.get)
    gd = geodesic([tip], set(c))
    gmax = max(gd.values())
    bins = [[] for _ in range(NB)]
    gb = [[] for _ in range(NB)]
    for i, d in gd.items():
        k = min(NB - 1, int(d / gmax * NB))
        bins[k].append(co(i)); gb[k].append(d)
    cl = [co(tip).copy()] + [sum(x, Vector()) / len(x) for x in bins if x]
    cg = [0.0] + [sum(x) / len(x) for x in gb if x]
    for _ in range(3):
        cl = [cl[0]] + [(cl[i - 1] + 2 * cl[i] + cl[i + 1]) / 4 for i in range(1, len(cl) - 1)] + [cl[-1]]
    cs = arc(cl)

    def from_tip(gv):
        for j in range(len(cg) - 1):
            if gv <= cg[j + 1] or j == len(cg) - 2:
                h = cg[j + 1] - cg[j]
                t_ = (gv - cg[j]) / h if h > 0 else 0.0
                return cs[j] + t_ * (cs[j + 1] - cs[j])
        return cs[-1]
    L = cs[-1]
    pts = list(reversed(cl))                       # proximal ... distal
    s_of = {i: L - from_tip(gd.get(i, gmax)) for i in c}
    return pts, s_of


def fit_polyline(s_of, mesh_pts, target_pts, map_x, label):
    ms = arc(mesh_pts)
    ts = arc(target_pts)
    f_src = frames(mesh_pts, ms, 120)
    f_dst = frames(target_pts, ts, 120)
    newpos = {}
    for i, x in s_of.items():
        v = co(i)
        p0, F0 = frame_at(f_src, x)
        p1, F1 = frame_at(f_dst, map_x(x))
        newpos[i] = p1 + F1 @ (F0.transposed() @ (v - p0))
        chain_of[i] = label
    for i, q in newpos.items():
        bm.verts[i].co = q
    return ms[-1], ts[-1]


def closest_pair(c1, c2):
    k_ = kdt(B[c2])
    best = (1e9, None, None)
    for i in c1:
        _, j, d = k_.find(Vector(B[i]))
        if d < best[0]:
            best = (d, B[i], B[c2[j]])
    return (best[1] + best[2]) / 2


report['arms'] = {}
for a, names in enumerate(E.ARMS):
    k = nl + a
    side = np.sign(J[names[2]].x)
    mine = [c for c in arms if np.sign(B[c][:, 0].mean()) == side and abs(B[c][:, 0].mean()) > 0.08]
    mine.sort(key=lambda c: min(kb.find(Vector(p))[2] for p in B[c]))
    assert len(mine) == 3, [len(c) for c in mine]
    up, fore, claw = mine
    j0 = min(B[up], key=lambda p: kb.find(Vector(p))[2])
    j1 = closest_pair(up, fore)
    j2 = closest_pair(fore, claw)
    cen = B[claw].mean(0)
    far = B[claw][np.argmax(np.linalg.norm(B[claw] - j2, axis=1))]
    # a claw piece longer than 0.8 m carries the forearm too (Meshy split this side differently): its wrist lies
    # 0.62 m (the other side's claw length) back from the far tip along the piece
    if np.linalg.norm(far - j2) > 0.8:
        d = (far - j2) / np.linalg.norm(far - j2)
        wrist = far - d * 0.62
        cen = B[claw][(B[claw] - wrist) @ d > 0].mean(0)
    else:
        wrist = j2
    mesh_pts = [Vector(p) for p in (j0, j1, j2, wrist, cen, far)]
    mesh_pts = [p for i_, p in enumerate(mesh_pts) if i_ == 0 or (p - mesh_pts[i_ - 1]).length > 1e-4]
    ms = arc(mesh_pts)
    Acl = A[np.isin(lab, names[3:])]
    t14 = np.array(J[names[3]])
    tfar = Acl[np.argmax(np.linalg.norm(Acl - t14, axis=1))]
    tgt = [J[n].copy() for n in names[:4]] + [Vector(Acl.mean(0)), Vector(tfar)]
    ts = arc(tgt)
    sb = ms[mesh_pts.index(Vector(wrist))] if Vector(wrist) in mesh_pts else ms[2]
    tb = ts[3]

    def map_x(x, sb=sb, tb=tb, mL=ms[-1], tL=ts[-1]):
        return x * tb / sb if x <= sb else tb + (x - sb) * (tL - tb) / (mL - sb)
    s_all = {}
    for c in mine:
        for i in c:
            s_all[i] = project_s(mesh_pts, ms, co(i))
    fit_polyline(s_all, mesh_pts, tgt, map_x, k)
    # claw roll: turn the claw about the MM9 claw axis so its blade-spread axis matches MM9's (upper minus lower
    # blade tip), blended in over 0.15 m past the wrist
    ax = (tgt[4] - tgt[3]).normalized()
    cids = [i for i in s_all if s_all[i] > sb]
    Q = np.array([tuple(co(i)) for i in cids])
    qc = Q - Q.mean(0)
    qc = qc - np.outer(qc @ np.array(ax), np.array(ax))
    ev, evec = np.linalg.eigh(np.cov(qc.T))
    sp = Vector(evec[:, 2])
    want = Vector(J[names[5]]) - Vector(J[names[7]])
    want = (want - ax * want.dot(ax)).normalized()
    sp = (sp - ax * sp.dot(ax)).normalized()
    if sp.dot(want) < 0:
        sp = -sp
    ang = math.atan2(ax.dot(sp.cross(want)), sp.dot(want))
    for i in cids:
        w = min(1.0, (s_all[i] - sb) / 0.15)
        w = w * w * (3 - 2 * w)
        Rm = Matrix.Rotation(ang * w, 3, ax)
        bm.verts[i].co = tgt[3] + Rm @ (co(i) - tgt[3])
    report['arms'][names[0]] = {'pieces': [len(c) for c in mine], 'meshy_len': ms[-1], 'mm9_len': ts[-1],
                                'claw_roll_deg': math.degrees(ang), 'wrist_meshy': sb, 'wrist_mm9': tb, 'fused_forearm': bool(np.linalg.norm(far - j2) > 0.8)}
for c in arms:
    if abs(B[c][:, 0].mean()) <= 0.08:
        piece[c] = 2   # midline mouth piece: rigid with the head

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
kAll = kdt(A)
d = np.array([kAll.find(v.co)[2] for v in me.vertices])
report.update({'verts': len(me.vertices), 'tris': sum(len(p.vertices) - 2 for p in me.polygons),
               'dist_to_mm9_mean': float(d.mean()), 'dist_to_mm9_p90': float(np.percentile(d, 90))})
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(report, open(REP, 'w'), indent=1, default=str)
print('FIT ' + json.dumps(report['pieces']) + ' scale %.4f' % s)
