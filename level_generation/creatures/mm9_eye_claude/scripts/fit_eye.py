"""Fit the Meshy Smart Topology Eye to the MM9 EVILEYETERROR.abc bind pose (helpers from
mm9_lobber_claude/scripts/fit_limbs.py).

Args: <mm9 source blend> <meshy glb> <out blend> <report json>

1. Core: the body shell, the big eyeball, the teeth and brow bumps are scaled and translated (no rotation: both face
   -Y) by symmetric nearest-point ICP onto the MM9 core vertices (Box01 / jaw Box02), initial scale from the height.
2. Pieces (welded components): body = largest; legs = long pieces below the body (8); stalks = long pieces above or
   beside it (5); eyeballs = compact pieces of the stalk ends (5); the big eyeball = the large compact piece in front;
   small = the rest (teeth, brow bumps).
3. Legs and stalks: every piece mapped onto its MM9 bone chain (eye_cfg.py) with fit_chain (geodesic centreline, arc
   length mapped, offsets kept in parallel-transported frames). Meshy pieces are assigned to MM9 chains by their tip
   position (exact minimum-cost assignment, same side). A stalk's chain ends at its eyeball bone's head.
4. Stalk eyeballs: moved rigidly so their centre is the centre of the MM9 eyeball (that chain's last bone vertices),
   scaled to the MM9 eyeball size.
Per-vertex attributes: 'piece' (0 body/limb, 2 small rigid piece, 3 big eyeball) and 'chain' (-1 core, k index).
"""
import bpy, bmesh, sys, os, json, math, heapq, itertools
import numpy as np
from mathutils import Vector, Matrix
from mathutils.kdtree import KDTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import eye_cfg as E


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


def ext(c):
    P = B[c]
    return P.min(0), P.max(0)


body_c = comps[0]
bmin, bmax = ext(body_c)
big = [c for c in comps[1:] if len(c) >= 120]
small = [c for c in comps[1:] if len(c) < 120]
elong = {}
for c in big:
    ev = np.sqrt(np.maximum(np.linalg.eigvalsh(np.cov((B[c] - B[c].mean(0)).T)), 1e-12))
    elong[id(c)] = ev[2] / ev[0]
compact = [c for c in big if elong[id(c)] < 2.0]
eyeball_c = max(compact, key=len)
stalk_eyes = [c for c in compact if c is not eyeball_c]
longs = [c for c in big if elong[id(c)] >= 2.0]
legs = [c for c in longs if B[c][:, 2].mean() < bmin[2] + 0.25 * (bmax[2] - bmin[2])]
stalks = [c for c in longs if not any(c is l for l in legs)]
report = {'components': [len(c) for c in comps], 'pieces': {'body': len(body_c), 'eyeball': len(eyeball_c),
          'legs': [len(c) for c in legs], 'stalks': [len(c) for c in stalks], 'stalk_eyes': [len(c) for c in stalk_eyes],
          'small': len(small)}}
assert len(legs) == 8 and len(stalks) == 5 and len(stalk_eyes) == 5, report['pieces']

# ---------------- core similarity (scale + translation)
core_mask = np.isin(lab, E.CORE) & (A[:, 2] > J['Box01'].z - 0.35)
Ac = A[core_mask]
core_ids = list(body_c) + list(eyeball_c) + [i for c in small for i in c]
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
piece = np.zeros(len(bm.verts), int)
chain_of = np.full(len(bm.verts), -1, int)
for c in small:
    piece[c] = 2
piece[eyeball_c] = 3
for c in stalk_eyes:
    piece[c] = 2

chains = E.CHAINS
targets = {}
for k, names in enumerate(chains):
    if k < len(E.LEGS):
        targets[k] = chain_poly(names)
    else:
        targets[k] = [J[n].copy() for n in names]
        if len(targets[k]) == 2:  # short side stalk: base and eyeball bone heads only
            targets[k] = [targets[k][0], targets[k][0].lerp(targets[k][1], 0.5), targets[k][1]]
kb = KDTree(len(body_c))
for j, i in enumerate(body_c):
    kb.insert(co(i), j)
kb.balance()


def tips_of(cs):
    out = []
    for c in cs:
        root_v = min(c, key=lambda i: kb.find(co(i))[2])
        g = geodesic([root_v], set(c))
        out.append(max(g, key=g.get))
    return out


report['chains'] = {}
for group, idx in ((legs, list(range(len(E.LEGS)))), (stalks, list(range(len(E.LEGS), len(chains))))):
    tips = tips_of(group)
    cost = np.array([[(co(tp) - targets[k][-1]).length
                      + (0 if np.sign(co(tp).x) == np.sign(targets[k][-1].x) or abs(targets[k][-1].x) < 0.05 else 10)
                      for k in idx] for tp in tips])
    rows, cols = linear_sum_assignment(cost)
    pre_tips = {}
    for r, cidx in zip(rows, cols):
        k = idx[cidx]
        pre_tips[k] = co(tips[r]).copy()
        report['chains'][chains[k][0]] = fit_chain(group[r], tips[r], targets[k][0], targets[k], False, k)
    if group is stalks:
        # eyeballs: nearest stalk tip (pre-fit), centred on the MM9 eyeball of that chain, scaled to its size
        for c in stalk_eyes:
            cen = Vector(B[c].mean(0))
            k = min(pre_tips, key=lambda kk: (pre_tips[kk] - cen).length)
            ev = A[lab == chains[k][-1]]
            tgt = Vector(ev.mean(0))
            r_mm9 = float(np.linalg.norm(ev - ev.mean(0), axis=1).mean())
            r_ours = float(np.linalg.norm(B[c] - B[c].mean(0), axis=1).mean())
            f = max(0.8, min(1.25, r_mm9 / max(r_ours, 1e-6)))
            for i in c:
                bm.verts[i].co = tgt + (co(i) - cen) * f
            report['chains'][chains[k][0]]['eyeball'] = {'scale': f, 'centre': list(tgt)}
            chain_of[c] = k

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
