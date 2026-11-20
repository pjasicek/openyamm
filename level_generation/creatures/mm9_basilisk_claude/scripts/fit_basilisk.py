"""Fit the globally aligned Meshy basilisk (align.py) to the MM9 bind pose, part by part.

Args: <align blend> <out blend> <report json>

0. Landmarks on the unfitted mesh: the six feet (lowest vertices clustered per side, three by y) and every leg's
   junction with the body (leg_junction: geodesic bins up the leg from the sole; the junction is where the bin spread
   jumps to 2.3x the lower leg's).
1. Body axis: a piecewise-linear map of y (the body axis; the head is at -y) through the mean front, middle and rear
   junction y onto the MM9 chain roots (Xfrontpivot, Xmidbase, Xrearpivot) and the tail tip onto the MM9 tail tip; in
   front of the front legs it is a translation (the head keeps its length).
2. Head: translation-only ICP of the Meshy head (in front of Xheadpiv) onto the MM9 head/jaw/frill vertices,
   blended out over the neck (smoothstep between Xheadpiv and Xneckpiv + 0.12 m).
3. Legs: segment skinning. Meshy joints on the leg centreline (junction = the chain root, the bend = the MM9 elbow,
   the rest by arc length); each segment is posed onto its MM9 segment (minimal rotation, stretch along it); leg
   vertices (flood fill from the sole on the foot side of the junction plane, within CAPSULE of the centreline) blend
   the segment transforms by distance (Gaussian SIGMA) and fade to rest across the plane (LEG_BLEND) and the capsule
   bound. The foot only translates with the wrist (it stays flat); its sole is set on the MM9 sole height.
4. Tail: a chain fit sheared its root, so the y-mapped tail keeps its plan and only its droop is matched to the MM9
   tail line (vertical move, faded in behind Xtailpiv).
5. Small pieces (teeth, eyes, claws): moved by the displacement of their nearest main-body vertex.
Per-vertex attributes 'piece' (0 body, 2 small piece) and 'chain' (-1 core, 0-5 legs, 6 tail) for rig_basilisk.py.
"""
import bpy, bmesh, sys, json, math, heapq
import numpy as np
from mathutils import Vector, Matrix
from mathutils.kdtree import KDTree

argv = sys.argv[sys.argv.index('--') + 1:]
SRC, OUT, REP = argv
LEG_BLEND = 0.07
FOOT_Z = 0.11
MM9_SOLE = 0.004
NB = 36  # centreline bins (leg_junction uses fixed 3 cm bins)
LEGS = [  # (name, side sign of x, rank by y: 0 front .. 2 rear, MM9 chain root..wrist)
    ('front', 1, 0, ['Xfrontpivot', 'Xfrontelbow', 'Xfrontarm']),
    ('front01', -1, 0, ['Xfrontpivot01', 'Xfrontelbow01', 'Xfrontarm01']),
    ('mid', 1, 1, ['Xmidbase', 'Xmidelbow', 'Xmidarm']),
    ('mid01', -1, 1, ['Xmidbase01', 'Xmidelbow01', 'Xmidarm01']),
    ('rear', 1, 2, ['Xrearpivot', 'Xrearelbow', 'Xreararm', 'Xrearwrist']),
    ('rear01', -1, 2, ['Xrearpivot01', 'Xrearelbow01', 'Xreararm01', 'Xrearwrist01']),
]
TAIL = ['Xtailpiv', 'XtailA', 'XtailB', 'XtailC']
HEAD_BONES = ['Xheadpiv', 'Xhead', 'Xeye', 'Xjawbase', 'Xjawpiv', 'Xjaw', 'XfinA', 'XfinA01', 'XfinDpiv',
              'XfinDpiv01', 'XfinB', 'XfinC', 'XfinB01', 'XfinC01']

bpy.ops.wm.open_mainfile(filepath=SRC)
sc = bpy.context.scene
arm = bpy.data.objects['MM9_Rig']
J = {b.name: Vector(b.head_local) for b in arm.data.bones}
mp, ml = [], []
for o in bpy.data.objects:
    if o.type != 'MESH' or o.name == 'Meshy':
        continue
    for v in o.data.vertices:
        g = max(v.groups, key=lambda g: g.weight)
        mp.append(tuple(o.matrix_world @ v.co)); ml.append(o.vertex_groups[g.group].name)
A = np.array(mp); lab = np.array(ml)


def kdt(P):
    k = KDTree(len(P))
    for i, p in enumerate(P):
        k.insert(Vector(tuple(p)), i)
    k.balance()
    return k


src = bpy.data.objects['Meshy']
bm = bmesh.new(); bm.from_mesh(src.data); bm.transform(src.matrix_world)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
bm.verts.ensure_lookup_table()
co = lambda i: bm.verts[i].co
n = len(bm.verts)
X0 = np.array([tuple(v.co) for v in bm.verts])

# ---------------- components
comp_of = np.full(n, -1)
comps = []
for v in bm.verts:
    if comp_of[v.index] >= 0:
        continue
    st = [v]; comp_of[v.index] = len(comps); c = []
    while st:
        x = st.pop(); c.append(x.index)
        for e in x.link_edges:
            y = e.other_vert(x)
            if comp_of[y.index] < 0:
                comp_of[y.index] = len(comps); st.append(y)
    comps.append(c)
order = sorted(range(len(comps)), key=lambda k: -len(comps[k]))
main = set(comps[order[0]])
main_ids = np.array(sorted(main))
piece = np.where(np.isin(np.arange(n), main_ids), 0, 2)
k_main0 = kdt(X0[main_ids])
small_anchor = {i: int(main_ids[k_main0.find(Vector(tuple(X0[i])))[1]]) for i in range(n) if piece[i] == 2}
chain_of = np.full(n, -1)
report = {'components': sorted((len(c) for c in comps), reverse=True)[:12], 'n_components': len(comps)}


def feet(P, low=0.07):
    """three foot clusters per side (front..rear) of the points P (N,3): list of (side, rank, centroid, member mask)"""
    out = []
    lowm = P[:, 2] < low
    for side in (1, -1):
        m = lowm & (np.sign(P[:, 0]) == side)
        ys = np.sort(P[m, 1])
        gaps = np.argsort(np.diff(ys))[-2:]
        cuts = sorted(ys[g] + 1e-6 for g in gaps)
        for r, (lo, hi) in enumerate(((-9, cuts[0]), (cuts[0], cuts[1]), (cuts[1], 9))):
            mm = m & (P[:, 1] > lo) & (P[:, 1] <= hi)
            out.append((side, r, P[mm].mean(0), mm))
    return out


Fa = {(s, r): c for s, r, c, _ in feet(A)}
Xm = X0[main_ids]
Fm = {(s, r): c for s, r, c, _ in feet(Xm, low=Xm[:, 2].min() + 0.07)}
report['feet_meshy'] = {f'{s},{r}': c.round(3).tolist() for (s, r), c in Fm.items()}
report['feet_mm9'] = {f'{s},{r}': c.round(3).tolist() for (s, r), c in Fa.items()}

# ---------------- helpers for chain fits


def geodesic(src_ids, allowed, limit=1e9):
    dist = {i: 0.0 for i in src_ids}
    pq = [(0.0, i) for i in src_ids]
    while pq:
        d, i = heapq.heappop(pq)
        if d > dist[i] or d > limit:
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


def arc(pts):
    s = [0.0]
    for a, b in zip(pts, pts[1:]):
        s.append(s[-1] + (b - a).length)
    return s


def at(pts, sl, x):
    if x <= 0:
        tg = (pts[1] - pts[0]).normalized()
        return pts[0] + tg * x
    if x >= sl[-1]:
        tg = (pts[-1] - pts[-2]).normalized()
        return pts[-1] + tg * (x - sl[-1])
    for i in range(len(pts) - 1):
        if x <= sl[i + 1]:
            h = sl[i + 1] - sl[i]
            return pts[i].lerp(pts[i + 1], (x - sl[i]) / h if h > 0 else 0)


def centreline(gd):
    gmax = max(gd.values())
    bins = [[] for _ in range(NB)]
    for i, d in gd.items():
        bins[min(NB - 1, int(d / gmax * NB))].append(co(i))
    cl = [sum(b, Vector()) / len(b) for b in bins if b]
    for _ in range(3):
        cl = [cl[0]] + [(cl[i - 1] + 2 * cl[i] + cl[i + 1]) / 4 for i in range(1, len(cl) - 1)] + [cl[-1]]
    return cl


def project_s(pts, sl, v):
    best = (1e9, 0.0)
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        ab = b - a
        L2 = ab.length_squared
        u = (v - a).dot(ab) / L2 if L2 > 0 else 0
        if (i > 0 and u < 0) or (i < len(pts) - 2 and u > 1):
            u = max(0.0, min(1.0, u))
        d = (v - (a + ab * u)).length
        if d < best[0]:
            best = (d, sl[i] + u * math.sqrt(L2))
    return best


def cut_polyline(pts, side, xc):
    """MM9 polyline root..tip cut where side*x first reaches xc (the root replaced by that crossing)."""
    for k in range(len(pts) - 1):
        a, b = side * pts[k].x, side * pts[k + 1].x
        if a < xc <= b:
            u = (xc - a) / (b - a)
            return [pts[k].lerp(pts[k + 1], u)] + pts[k + 1:]
    return pts


def smooth(w):
    w = min(1.0, max(0.0, w))
    return w * w * (3 - 2 * w)




def leg_junction(tip, allowed, bw=0.03):
    """Leg centreline from geodesic bins (fixed width bw) up the leg; the junction is the first bin past 0.25 m whose
    spread (mean distance of its vertices from their centroid) and the next
    one's exceed 2.3x the lower leg's (0.15-0.35 m). Returns
    the cut plane (point, normal toward the body) and the lower-leg radius."""
    gd = geodesic([tip], allowed, 1.6)
    nb = int(1.6 / bw) + 1
    bins = [[] for _ in range(nb)]
    for i, d in gd.items():
        bins[min(nb - 1, int(d / bw))].append(np.array(tuple(co(i))))
    cen, spr, gs = [], [], []
    for k, b in enumerate(bins):
        if len(b) < 3:
            continue
        b = np.array(b); c = b.mean(0)
        cen.append(c); spr.append(float(np.linalg.norm(b - c, axis=1).mean())); gs.append((k + 0.5) * bw)
    cen = np.array(cen); spr = np.array(spr); gs = np.array(gs)
    r0 = float(np.median(spr[(gs > 0.15) & (gs < 0.35)]))
    k = next((k for k in range(len(gs) - 1) if gs[k] > 0.25 and min(spr[k], spr[k + 1]) > 2.3 * r0), None)
    if k is None:
        k = next(k for k in range(len(gs) - 1) if gs[k] > 0.25 and min(spr[k], spr[k + 1]) > 1.9 * r0)
    k -= 1
    nrm = Vector(tuple(cen[k] - cen[max(0, k - 3)])).normalized()
    line = [Vector(tuple(c)) for c in cen[:k + 1]]
    for _ in range(3):
        line = [line[0]] + [(line[i - 1] + 2 * line[i] + line[i + 1]) / 4 for i in range(1, len(line) - 1)] + [line[-1]]
    return Vector(tuple(cen[k])), nrm, r0, gs[k], [co(tip).copy()] + line


def sole_foot(tip, allowed, Xpre):
    """Foot (connected to the tip, less than FOOT_Z above it before the pose): shifted vertically so its sole lies on
    the MM9 sole height; blended into the shin up to FOOT_Z + 0.12."""
    seen = {tip}; st = [tip]; g = {}
    while st:
        i = st.pop(); g[i] = Xpre[i][2] - Xpre[tip][2]
        for e in bm.verts[i].link_edges:
            j = e.other_vert(bm.verts[i]).index
            if j not in seen and j in allowed and Xpre[j][2] - Xpre[tip][2] < FOOT_Z + 0.12:
                seen.add(j); st.append(j)
    sole = float(np.percentile([co(i).z for i, d in g.items() if d < FOOT_Z], 2))
    dz = MM9_SOLE - sole
    for i, d in g.items():
        w = 1.0 if d < FOOT_Z else smooth((FOOT_Z + 0.12 - d) / 0.12)
        bm.verts[i].co.z += dz * w
    return {'sole_shift': round(dz, 4), 'verts': len(g)}


def leg_members(tip, allowed, Xpre, root):
    """Vertices of the leg for the rig's chain labels: connected to the foot through vertices whose posed distance
    from the body midline exceeds the MM9 chain root's (the root pivot sits at the body side)."""
    side = 1 if co(tip).x > 0 else -1
    xr = side * root.x
    seen = {tip}; st = [tip]
    while st:
        i = st.pop()
        for e in bm.verts[i].link_edges:
            j = e.other_vert(bm.verts[i]).index
            if j not in seen and j in allowed and side * co(j).x > xr:
                seen.add(j); st.append(j)
    return seen


# ---------------- 0. foot tips and leg junctions on the unmapped mesh (y-map landmarks)
Xy = X0[main_ids]
FOOT = {}
for s_, r_, c_, mm_ in feet(Xy, low=Xy[:, 2].min() + 0.07):
    cand = main_ids[mm_]
    FOOT[(s_, r_)] = (int(min(cand, key=lambda i: (Vector((co(i).x - c_[0], co(i).y - c_[1], 0)).length
                                                    + 0.5 * co(i).z))), c_)

mainset = set(main)
JY = {}
for name, side, rank, bones in LEGS:
    pt = leg_junction(FOOT[(side, rank)][0], mainset)[0]
    JY.setdefault(rank, []).append((pt.y, J[bones[0]].y))
report['junction_y'] = {r: [[round(a, 3), round(b, 3)] for a, b in v] for r, v in JY.items()}

# ---------------- 1. body axis map
ky = [(float(np.mean([a for a, b in JY[r]])), float(np.mean([b for a, b in JY[r]]))) for r in (0, 1, 2)]
yf_m, yf_a = ky[0]; yr_m, yr_a = ky[2]
yt_m = Xm[:, 1].max(); yt_a = A[:, 1].max()
knots_m = [ky[0][0], ky[1][0], ky[2][0], yt_m]; knots_a = [ky[0][1], ky[1][1], ky[2][1], yt_a]


def ymap(y):
    if y <= yf_m:
        return y - yf_m + yf_a
    if y >= yt_m:
        return y - yt_m + yt_a
    return float(np.interp(y, knots_m, knots_a))


for v in bm.verts:
    v.co.y = ymap(v.co.y)
report['ymap'] = {'meshy': [round(k, 3) for k in knots_m], 'mm9': [round(k, 3) for k in knots_a],
                  'body_scale': [(knots_a[k + 1] - knots_a[k]) / (knots_m[k + 1] - knots_m[k]) for k in range(3)]}

# ---------------- 2. head translation ICP
y1, y0 = J['Xheadpiv'].y, J['Xneckpiv'].y + 0.12   # w = 1 in front of y1, 0 behind y0


Ah = A[np.isin(lab, HEAD_BONES)]
kAh = kdt(Ah)
hid = [i for i in range(n) if co(i).y < y1]
Hp = np.array([tuple(co(i)) for i in hid])
t = np.zeros(3)
for _ in range(25):
    X = Hp + t
    kX = kdt(X)
    d1 = np.array([Ah[kAh.find(Vector(tuple(x)))[1]] - x for x in X])
    d2 = np.array([a - X[kX.find(Vector(tuple(a)))[1]] for a in Ah])
    t = t + 0.5 * (d1.mean(0) + d2.mean(0))
for v in bm.verts:
    w = smooth((y0 - v.co.y) / (y0 - y1))
    v.co += Vector(tuple(t)) * w
report['head_translate'] = t.round(4).tolist()

# ---------------- 3. legs: segment-skinned pose onto the MM9 leg chains
# Each Meshy leg gets joints on its centreline (junction = the chain root, the bend = the MM9 elbow, the other joints
# by arc length). Every segment between joints is posed onto its MM9 segment (minimal rotation, stretch along the
# segment only); leg vertices blend the segment transforms by distance (Gaussian, SIGMA); the foot (low vertices
# connected to the sole) only translates with the wrist, so it stays flat; across the junction plane the pose blends
# to rest over LEG_BLEND. The leg = flood fill from the sole on the foot side of the junction plane (+ LEG_BLEND),
# within CAPSULE of the leg centreline (the weight fades out toward both bounds).
SIGMA = 0.035
CAPSULE = 0.26  # leg region: within this distance of the Meshy leg centreline (weight fades over its last 7 cm)
Xpre = [tuple(v.co) for v in bm.verts]
report['legs'] = {}


def seg_matrix(a0, a1, b0, b1):
    da, db = a1 - a0, b1 - b0
    r = da.normalized().rotation_difference(db.normalized()).to_matrix().to_4x4()
    u = da.normalized(); st = db.length / da.length
    S = Matrix.Identity(4)
    for i_ in range(3):
        for j_ in range(3):
            S[i_][j_] += (st - 1) * u[i_] * u[j_]
    return Matrix.Translation(b0) @ r @ S @ Matrix.Translation(-a0)


def seg_dist(p, a, b):
    ab = b - a
    u = max(0.0, min(1.0, (p - a).dot(ab) / max(ab.length_squared, 1e-12)))
    return (p - (a + ab * u)).length


JUNC = {name: leg_junction(FOOT[(side, rank)][0], mainset) for name, side, rank, bones in LEGS}
for li, (name, side, rank, bones) in enumerate(LEGS):
    tip, c = FOOT[(side, rank)]
    pt, nrm, r0, gk, line = JUNC[name]
    full = cut_polyline([J[b].copy() for b in bones] + [Vector(tuple(Fa[(side, rank)]))], side, side * pt.x)
    mesh_pts = list(reversed(line))  # junction .. sole
    ms = arc(mesh_pts); ts = arc(full)
    a_, b_ = mesh_pts[0], mesh_pts[-1]
    ab = (b_ - a_).normalized()
    dev = [((p - a_) - ab * (p - a_).dot(ab)).length for p in mesh_pts]
    kb = max(range(1, len(mesh_pts) - 1), key=lambda k: dev[k])
    sb, tb = ms[kb], ts[1]

    def inv_map(xt, sb=sb, tb=tb, ms=ms, ts=ts):
        if xt <= tb:
            return xt * sb / tb
        return sb + (xt - tb) * (ms[-1] - sb) / (ts[-1] - tb)
    jm = [at(mesh_pts, ms, inv_map(x)) for x in ts[:-1]]   # Meshy joints for the MM9 chain joints (root..wrist)
    ja = full[:-1]
    mats = [seg_matrix(jm[k], jm[k + 1], ja[k], ja[k + 1]) for k in range(len(jm) - 1)]
    T_foot = Matrix.Translation(ja[-1] - jm[-1])
    # the leg region
    plane = lambda v: (v - pt).dot(nrm)
    seen = {tip}; st = [tip]
    while st:
        i = st.pop()
        for e in bm.verts[i].link_edges:
            j = e.other_vert(bm.verts[i]).index
            if j in seen or j not in mainset:
                continue
            v = co(j)
            if plane(v) < LEG_BLEND and project_s(mesh_pts, ms, v)[0] < CAPSULE:
                seen.add(j); st.append(j)
    # the foot: connected to the sole, less than FOOT_Z (+0.1 blend) above it
    fseen = {tip}; st = [tip]; fh = {tip: 0.0}
    while st:
        i = st.pop()
        for e in bm.verts[i].link_edges:
            j = e.other_vert(bm.verts[i]).index
            if j not in fseen and j in seen and co(j).z - co(tip).z < FOOT_Z + 0.1:
                fseen.add(j); st.append(j); fh[j] = co(j).z - co(tip).z
    newp = {}
    for i in seen:
        v = co(i)
        ds = [seg_dist(v, jm[k], jm[k + 1]) for k in range(len(mats))]
        dmin = min(ds)
        ws = [math.exp(-((d - dmin) / SIGMA) ** 2) for d in ds]
        tot = sum(ws)
        q = Vector()
        for w, M in zip(ws, mats):
            q += (M @ v) * (w / tot)
        if i in fh:
            wf = 1.0 if fh[i] < FOOT_Z else smooth((FOOT_Z + 0.1 - fh[i]) / 0.1)
            q = q.lerp(T_foot @ v, wf)
        wr = smooth((LEG_BLEND - plane(v)) / (2 * LEG_BLEND)) * smooth((CAPSULE - project_s(mesh_pts, ms, v)[0]) / 0.07)
        newp[i] = v.lerp(q, wr)
        if wr > 0.5:
            chain_of[i] = li
    for i, q in newp.items():
        bm.verts[i].co = q
    report['legs'][name] = {'meshy_len': round(ms[-1], 3), 'mm9_len': round(ts[-1], 3),
                            'junction': [round(c, 3) for c in pt], 'junction_g': round(float(gk), 3),
                            'bend': [round(sb, 3), round(tb, 3)], 'verts': len(seen), 'foot_verts': len(fh),
                            'seg_stretch': [round((ja[k + 1] - ja[k]).length / max((jm[k + 1] - jm[k]).length, 1e-6), 2)
                                            for k in range(len(jm) - 1)]}
    report['legs'][name]['foot'] = sole_foot(tip, mainset, Xpre)
leg_sets = set(np.nonzero(chain_of >= 0)[0].tolist())

# ---------------- 4. tail
yc = J['Xtailpiv'].y
tail_ids = mainset - leg_sets
tip = max(tail_ids, key=lambda i: co(i).y)
tv = A[lab == 'XtailC']
tail_tip = Vector(tuple(tv[np.argmax(tv[:, 1])]))
# the y-mapped Meshy tail already follows the MM9 tail in plan (a chain fit sheared its root); its droop is matched:
# every tail vertex moves vertically by the difference of the MM9 tail line (joints + tip) and the Meshy tail's
# centre height at its y (10 cm bins), faded in over 0.3 m behind Xtailpiv
tpts = [J[b] for b in TAIL] + [tail_tip]
tl = [i for i in tail_ids if co(i).y > yc - 0.05]
edges_y = np.arange(yc - 0.05, tail_tip.y + 0.1, 0.1)
cz = []
for y0_, y1_ in zip(edges_y, edges_y[1:]):
    zs = [co(i).z for i in tl if y0_ <= co(i).y < y1_]
    if zs:
        cz.append(((y0_ + y1_) / 2, (min(zs) + max(zs)) / 2))
cy_, cz_ = np.array([c[0] for c in cz]), np.array([c[1] for c in cz])
for i in tl:
    v = co(i)
    dz = float(np.interp(v.y, [p.y for p in tpts], [p.z for p in tpts]) - np.interp(v.y, cy_, cz_))
    v.z += dz * smooth((v.y - yc) / 0.3)
    if v.y > yc:
        chain_of[i] = len(LEGS)
report['tail'] = {'labelled': int((chain_of == len(LEGS)).sum()), 'tip': [round(c, 3) for c in co(tip)],
                  'mm9_tip': [round(c, 3) for c in tail_tip]}

# ---------------- 5. small pieces follow their anchor
X1 = np.array([tuple(v.co) for v in bm.verts])
disp = X1 - X0
for i, a in small_anchor.items():
    bm.verts[i].co = Vector(tuple(X0[i] + disp[a]))

me = bpy.data.meshes.new('Body')
pl = bm.verts.layers.int.new('piece'); cl_ = bm.verts.layers.int.new('chain')
for v in bm.verts:
    v[pl] = int(piece[v.index]); v[cl_] = int(chain_of[v.index])
bm.to_mesh(me)
obj = bpy.data.objects.new('Body', me)
sc.collection.objects.link(obj)
for p in me.polygons:
    p.use_smooth = True
bpy.data.objects.remove(src)
kA = kdt(A)
d = np.array([kA.find(v.co)[2] for v in me.vertices])
report.update({'verts': len(me.vertices), 'tris': sum(len(p.vertices) - 2 for p in me.polygons),
               'dist_to_mm9_mean': float(d.mean()), 'dist_to_mm9_p90': float(np.percentile(d, 90)),
               'zmin': float(min(v.co.z for v in me.vertices))})
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(report, open(REP, 'w'), indent=1, default=str)
print('FIT ' + json.dumps(report, default=str))
