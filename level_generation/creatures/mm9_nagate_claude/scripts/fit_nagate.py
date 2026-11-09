"""Fit the Meshy Smart Topology Nagate (beetle) to the grounded MM9 bind pose (from mm9_lobber_claude fit_limbs.py).

Args: <mm9 source blend> <meshy glb> <out blend> <report json>

Meshy returned the shell and the underbody (with the head) as two big pieces, four legs per side (each an upper piece
and a separate claw piece), two short stubs behind the front legs, and small head pieces (two antennae, two mandibles,
two eyes). MM9 has six legs.
1. Body/head warp: the neck is the narrowest cross-section of the underbody in front of the shell. Two per-axis affine
   maps from bounding boxes: body (shell + underbody behind the neck) -> MM9 body.mesh (its front taken at Xneck),
   head (underbody in front of the neck + the small head pieces) -> MM9 head.mesh; blended over +-BLEND_NECK metres.
   This widens and shortens Meshy's longer beetle to the MM9 proportions.
2. Legs: every claw piece joins the upper piece it touches (virtual edges between their nearest vertices); upper
   pieces without a claw are the stubs and are dropped. The six MM9 leg chains take six of the eight legs by
   exact assignment (hip and tip distances); the other pair is dropped. Each leg is mapped onto its chain from
   X*basepiv to the toe tip (fit_chain), with the upper/claw junction landmarked onto the MM9 knee (X*mid).
3. Antennae and mandibles are fitted onto their MM9 chains the same way (root = the vertex nearest the head).
   Eyes are small pieces (piece 2), later rigid with the head.
Per-vertex attributes: 'piece' (0 body, 2 small piece) and 'chain' (-1 core, k = chain index) for rig_body.py.
"""
import bpy, bmesh, sys, json, math, heapq
import numpy as np
from mathutils import Vector, Matrix
from mathutils.kdtree import KDTree
import itertools

argv = sys.argv[sys.argv.index('--') + 1:]
SRC, MESHY, OUT, REP = argv
BLEND = 0.05
BLEND_NECK = 0.025
LBS_BEND = False
NB = 40
LEG_RADIAL = 1.5  # leg cross-sections widened: MM9 legs are 1.5-2x longer than Meshy's
LEGS = {  # fit targets start at the leg's basepiv (the MM9 leg mesh emerges there); knee = X*mid
    'aleg': ['Xalegbasepiv', 'Xalegpiv', 'Xamid', 'Xacontrol', 'Xatoe'],
    'aleg02': ['Xalegbasepiv02', 'Xalegpiv02', 'Xamid02', 'Xacontrol02', 'Xatoe02'],
    'bleg': ['Xblegbasepiv', 'Xblegpiv', 'Xbmid', 'Xbcontrol', 'Xbtoe'],
    'bleg04': ['Xblegbasepiv04', 'Xblegpiv05', 'Xbmid05', 'Xbcontrol05', 'Xbtoe05'],
    'bleg01': ['Xblegbasepiv01', 'Xblegpiv01', 'Xbmid01', 'Xbcontrol01', 'Xbtoe01'],
    'bleg05': ['Xblegbasepiv05', 'Xblegpiv04', 'Xbmid04', 'Xbcontrol04', 'Xbtoe04'],
}
FEELERS = {'ant': ['Xantpiv', 'Xant', 'Xanttip', 'Xantmid'], 'ant01': ['Xantpiv01', 'Xant01', 'Xanttip01', 'Xantmid01'],
           'jaw': ['Xjawpiv', 'Xjaw', 'Xjawmid'], 'jaw01': ['Xjawpiv01', 'Xjaw01', 'Xjawmid01']}
EXTRA = {}


def nbrs(v):
    for e in v.link_edges:
        yield e.other_vert(v).index, e.calc_length()
    for j, L in EXTRA.get(v.index, ()):
        yield j, L


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


bpy.ops.wm.open_mainfile(filepath=SRC)
sc = bpy.context.scene
arm = bpy.data.objects['MM9_Rig']
J = {b.name: Vector(b.head_local) for b in arm.data.bones}
mm9_p, mm9_l, mm9_o = [], [], []
for o in bpy.data.objects:
    if o.type != 'MESH':
        continue
    for v in o.data.vertices:
        g = max(v.groups, key=lambda g: g.weight)
        mm9_p.append(o.matrix_world @ v.co)
        mm9_l.append(o.vertex_groups[g.group].name)
        mm9_o.append(o.name)
A = np.array([tuple(p) for p in mm9_p])
lab = np.array(mm9_l)
obj_of = np.array(mm9_o)

def kdt(P):
    k = KDTree(len(P))
    for i, p in enumerate(P):
        k.insert(Vector(p), i)
    k.balance()
    return k


def geodesic(src_ids, allowed):
    dist = {i: 0.0 for i in src_ids}
    pq = [(0.0, i) for i in src_ids]
    while pq:
        d, i = heapq.heappop(pq)
        if d > dist[i]:
            continue
        v = bm.verts[i]
        for j, L in nbrs(v):
            if j not in allowed:
                continue
            nd = d + L
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


def fit_chain(ids, tip, root_target, target_pts, attached, label, landmark=None, radial=1.0):
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

    def arc_from_tip_pre(g):
        for j in range(len(cg) - 1):
            if g <= cg[j + 1] or j == len(cg) - 2:
                h = cg[j + 1] - cg[j]
                a = (g - cg[j]) / h if h > 0 else 0.0
                return cs[j] + a * (cs[j + 1] - cs[j])
        return cs[-1]

    n = len(mesh_pts)
    win = max(2, n // 10)
    ib, sb = bend_s(mesh_pts, ms, [(k - win, k, k + win) for k in range(max(win, n // 5), min(n - win, n - n // 5))])
    tb_ang, tb = bend_s(tp, ts, [(k - 1, k, k + 1) for k in range(1, len(tp) - 1)])
    use_bend = ib > math.radians(25) and tb_ang > math.radians(25)

    if landmark is not None:
        use_bend = True
        sb = ms[-1] - arc_from_tip_pre(landmark[0])
        tb = landmark[1]

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
        loc = F0.transposed() @ (v - p0)
        loc = Vector((loc.x, loc.y * radial, loc.z * radial))  # cross-section scale (stretched thin legs)
        q = p1 + F1 @ loc
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
            'bend': [math.degrees(ib), sb, math.degrees(tb_ang), tb] if use_bend else None,
            'landmark': list(landmark) if landmark is not None else None}


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
kA = kdt(A)
report = {}
co = lambda i: bm.verts[i].co
cent = lambda c: sum((co(i) for i in c), Vector()) / len(c)

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
report['components'] = [len(c) for c in comps]
shell, under = comps[0], comps[1]
rest = comps[2:]
B0 = np.array([tuple(co(i)) for i in shell + under])
head_small = [c for c in rest if len(c) < 160 and abs(cent(c).x) < 0.1 and cent(c).y < B0[:, 1].min() + 0.15]
limb_pieces = [c for c in rest if not any(c is h for h in head_small)]
uppers = [c for c in limb_pieces if len(c) >= 200]
lowers = [c for c in limb_pieces if len(c) < 200]

# ---------------- neck: narrowest underbody cross-section in front of the shell
U = np.array([tuple(co(i)) for i in under])
shell_front = min(co(i).y for i in shell)
ys = np.linspace(U[:, 1].min() + 0.01, shell_front + 0.06, 60)
widths = np.array([np.abs(U[np.abs(U[:, 1] - y) < 0.008, 0]).max() if (np.abs(U[:, 1] - y) < 0.008).any() else 0
                   for y in ys])
k_head = int(np.argmax(np.where(ys < U[:, 1].min() + 0.12, widths, -1)))  # widest slice of the head
k_neck = k_head + int(np.argmin(np.where(widths[k_head:] > 0, widths[k_head:], 9)))
y_neck = float(ys[k_neck])
report['neck_widths'] = [round(float(ys[k_head]), 3), round(float(widths[k_head]), 3), round(float(widths[k_neck]), 3)]
report['y_neck_meshy'] = y_neck


def box(P):
    return P.min(0), P.max(0)


Ub = U[U[:, 1] >= y_neck]
Uh = U[U[:, 1] < y_neck]
Sb = np.array([tuple(co(i)) for i in shell])
mb_lo, mb_hi = box(np.vstack([Sb, Ub]))
mh_lo, mh_hi = box(Uh)
Ab = A[obj_of == 'body.mesh']
Ah = A[np.isin(obj_of, ['head.mesh'])]
tb_lo, tb_hi = box(Ab)
th_lo, th_hi = box(Ah)
tb_lo = tb_lo.copy(); tb_lo[1] = J['Xneck'].y   # MM9 body front taken at the neck joint
th_hi = th_hi.copy(); th_hi[1] = J['Xneck'].y    # MM9 head back = neck joint
mh_hi = mh_hi.copy(); mh_hi[1] = y_neck
mb_lo = mb_lo.copy(); mb_lo[1] = y_neck


def affine(lo, hi, tlo, thi):
    s = (thi - tlo) / np.maximum(hi - lo, 1e-6)
    return lambda p: tlo + (p - lo) * s


f_body = affine(mb_lo, mb_hi, tb_lo, tb_hi)
f_head = affine(mh_lo, mh_hi, th_lo, th_hi)
report['scale_body'] = ((tb_hi - tb_lo) / (mb_hi - mb_lo)).tolist()
report['scale_head'] = ((th_hi - th_lo) / (mh_hi - mh_lo)).tolist()


def warp(p, force_head=False, force_body=False):
    p = np.array(tuple(p))
    if force_head:
        return f_head(p)
    if force_body:
        return f_body(p)
    a = min(1.0, max(0.0, (p[1] - (y_neck - BLEND_NECK)) / (2 * BLEND_NECK)))  # 0 head .. 1 body
    a = a * a * (3 - 2 * a)
    return f_head(p) * (1 - a) + f_body(p) * a


new_pos = {}
for i in shell:
    new_pos[i] = warp(co(i), force_body=True)
for i in under:
    new_pos[i] = warp(co(i))
for c in head_small:
    for i in c:
        new_pos[i] = warp(co(i), force_head=True)
# limbs: moved rigidly with the body map's translation at their hip, scaled by the body map (fitted below)
for c in limb_pieces:
    for i in c:
        new_pos[i] = warp(co(i), force_body=True)
for i, p in new_pos.items():
    bm.verts[i].co = Vector(p)

# ---------------- legs: join each claw piece to the upper piece it touches
piece = np.zeros(len(bm.verts), int)
chain_of = np.full(len(bm.verts), -1, int)
up_trees = []
for c in uppers:
    k = KDTree(len(c))
    for j, i in enumerate(c):
        k.insert(co(i), j)
    k.balance()
    up_trees.append(k)
legs = [{'upper': c, 'lower': None} for c in uppers]
for c in lowers:
    best = (1e9, None, None, None)
    for li, (u, k) in enumerate(zip(uppers, up_trees)):
        for i in c:
            p, j, d = k.find(co(i))
            if d < best[0]:
                best = (d, li, i, u[j])
    d, li, i_low, i_up = best
    legs[li]['lower'] = c
    legs[li]['join'] = (i_low, i_up, d)
    L = max(d, 1e-4)
    EXTRA.setdefault(i_low, []).append((i_up, L))
    EXTRA.setdefault(i_up, []).append((i_low, L))
stubs = [l for l in legs if l['lower'] is None]
legs = [l for l in legs if l['lower'] is not None]
report['legs_found'] = len(legs)
report['stubs_dropped'] = [len(l['upper']) for l in stubs]
core_ids = shell + under
kcore = KDTree(len(core_ids))
for j, i in enumerate(core_ids):
    kcore.insert(co(i), j)
kcore.balance()
for l in legs:
    ids = l['upper'] + l['lower']
    l['ids'] = ids
    l['hip'] = min(l['upper'], key=lambda i: kcore.find(co(i))[2])
    g = geodesic([l['hip']], set(ids))
    l['tip'] = max(g, key=g.get)


def chain_poly(names):
    pts = [J[n].copy() for n in names]
    tipv = A[lab == names[-1]]
    if len(tipv) == 0:
        tipv = A[lab == names[-2]]
    far = tipv[np.argmax(np.linalg.norm(tipv - np.array(pts[0]), axis=1))]
    pts.append(Vector(far))
    return pts


leg_names = list(LEGS)
targets = {n: chain_poly(LEGS[n]) for n in leg_names}
cost = np.array([[(co(l['hip']) - targets[n][0]).length + (co(l['tip']) - targets[n][-1]).length
                  + (0 if np.sign(co(l['tip']).x) == np.sign(targets[n][-1].x) else 10) for n in leg_names] for l in legs])
r_, c_ = linear_sum_assignment(cost)
report['legs'] = {}
used = set(r_)
dropped = [legs[k] for k in range(len(legs)) if k not in used] + stubs
for ri, ci in zip(r_, c_):
    n = leg_names[ci]
    l = legs[ri]
    # knee landmark: the claw piece's joining vertex, its geodesic distance from the tip -> MM9 arc at X*mid
    g = geodesic([l['tip']], set(l['ids']))
    tp = targets[n]
    ts = arc(tp)
    land = (g[l['join'][0]], ts[2])
    report['legs'][n] = fit_chain(l['ids'], l['tip'], tp[0], tp, False, ci, landmark=land, radial=LEG_RADIAL)
    report['legs'][n]['hip_tip_cost'] = float(cost[ri, ci])
# ---------------- antennae and mandibles
khead = KDTree(len(under))
for j, i in enumerate(under):
    khead.insert(co(i), j)
khead.balance()
def extent(c):
    P = np.array([tuple(co(i)) for i in c])
    return float((P.max(0) - P.min(0)).max())


by_extent = sorted(head_small, key=extent)
eyes = by_extent[:2]          # the two compact spheres
feelers = by_extent[2:]       # mandibles and antennae
report['feelers'] = {}
fnames = list(FEELERS)
ftargets = {n: chain_poly(FEELERS[n]) for n in fnames}
fdat = []
for c in feelers:
    root = min(c, key=lambda i: khead.find(co(i))[2])
    g = geodesic([root], set(c))
    fdat.append((c, max(g, key=g.get)))
fcost = np.array([[(cent(c) - (ftargets[n][0] + ftargets[n][-1]) / 2).length for n in fnames] for c, _ in fdat])
if len(fdat) >= len(fnames):
    fr, fc = linear_sum_assignment(fcost)
    for ri, ci in zip(fr, fc):
        n = fnames[ci]
        c, tip = fdat[ri]
        report['feelers'][n] = fit_chain(c, tip, ftargets[n][0], ftargets[n], False, len(leg_names) + ci)
for c in eyes:
    piece[c] = 2
report['eyes'] = [len(c) for c in eyes]
report['chain_names'] = leg_names + fnames
report['dropped_limbs'] = [len(l['upper']) for l in dropped]

# ---------------- delete the dropped legs / stubs, write the mesh
kill = set(i for l in dropped for i in (l['upper'] + (l['lower'] or [])))
keep = [i for i in range(len(bm.verts)) if i not in kill]
pl = bm.verts.layers.int.new('piece')
cl_ = bm.verts.layers.int.new('chain')
for v in bm.verts:
    v[pl] = int(piece[v.index]); v[cl_] = int(chain_of[v.index])
bmesh.ops.delete(bm, geom=[bm.verts[i] for i in sorted(kill)], context='VERTS')
me = bpy.data.meshes.new('Body')
bm.to_mesh(me)
obj = bpy.data.objects.new('Body', me)
sc.collection.objects.link(obj)
for p in me.polygons:
    p.use_smooth = True
d = np.array([kA.find(v.co)[2] for v in me.vertices])
report.update({'verts': len(me.vertices), 'tris': sum(len(p.vertices) - 2 for p in me.polygons),
               'dist_to_mm9_mean': float(d.mean()), 'dist_to_mm9_p90': float(np.percentile(d, 90)),
               'z_min': float(min(v.co.z for v in me.vertices))})
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(report, open(REP, 'w'), indent=1, default=str)
print('FIT ' + json.dumps({k: v for k, v in report.items() if k not in ('legs', 'feelers')}, default=str))
