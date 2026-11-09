"""Fit the globally aligned Meshy Terror (align.py) to the MM9 bind pose: the six head tentacles onto their MM9 chains.

Args: <align blend> <out blend> <report json>

The body, head and legs keep the global similarity fit (they already overlay the MM9 model: work/align_sheet.png).
Tentacles (attached to the head): the Meshy tip is the vertex nearest the MM9 tentacle tip, climbed to the local
maximum of the geodesic distance from the chest. Its centreline (geodesic bins from the tip) is cut where it passes
closest to the MM9 chain root; the tentacle = flood fill from the tip on the tip side of the cut plane (+ BLEND),
within CAP_K x the tentacle's mid-length radius (+ CAP_ADD) of the centreline. Meshy joints sit on the centreline at the
MM9 joints' arc fractions; every segment is posed onto its MM9 segment (minimal rotation, stretch along it), vertices
blend the segment transforms by distance (Gaussian, SIGMA); across the cut plane and the capsule bound the pose fades
to rest. Small pieces (teeth, eyes) move with their nearest main-body vertex.
Per-vertex attributes 'piece' (0 body, 2 small piece) and 'chain' (-1 core, 0-5 tentacles, 6-7 legs) for the rig.
"""
import bpy, bmesh, sys, json, math, heapq
import numpy as np
from mathutils import Vector, Matrix
from mathutils.kdtree import KDTree

argv = sys.argv[sys.argv.index('--') + 1:]
SRC, OUT, REP = argv
BLEND = 0.12
SIGMA = 0.05
CAP_K, CAP_ADD = 2.6, 0.05
BW = 0.04
ROOT_ZONE = 0.35
TIP_R = 0.75
MM9_SOLE = 0.004
TENTACLES = [
    ('long_R', ['Bone26', 'Bone27', 'Bone28', 'Bone29', 'Bone30', 'Bone31', 'Bone32', 'Bone33']),
    ('long_L', ['Bone01', 'Bone02', 'Bone03', 'Bone04', 'Bone21', 'Bone22', 'Bone23', 'Bone24']),
    ('horn_R', ['Bone14', 'Bone15', 'Bone16']),
    ('horn_L', ['Bone05', 'Bone06', 'Bone07']),
    ('short_R', ['Bone13', 'Bone18', 'Bone19']),
    ('short_L', ['Bone09', 'Bone10', 'Bone11']),
]
LEGS = [('leg_R', 1, ['Bip01 R Thigh', 'Bip01 R Calf', 'Bip01 R Foot', 'Bip01 R Toe0']),
        ('leg_L', -1, ['Bip01 L Thigh', 'Bip01 L Calf', 'Bip01 L Foot', 'Bip01 L Toe0'])]

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


def smooth(w):
    w = min(1.0, max(0.0, w))
    return w * w * (3 - 2 * w)


src = bpy.data.objects['Meshy']
bm = bmesh.new(); bm.from_mesh(src.data); bm.transform(src.matrix_world)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
bm.verts.ensure_lookup_table()
co = lambda i: bm.verts[i].co
n = len(bm.verts)
X0 = np.array([tuple(v.co) for v in bm.verts])
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
main = set(max(comps, key=len))
main_ids = np.array(sorted(main))
piece = np.where(np.isin(np.arange(n), main_ids), 0, 2)
k_main0 = kdt(X0[main_ids])
small_anchor = {i: int(main_ids[k_main0.find(Vector(tuple(X0[i])))[1]]) for i in range(n) if piece[i] == 2}
chain_of = np.full(n, -1)
report = {'components': sorted((len(c) for c in comps), reverse=True)[:12], 'n_components': len(comps)}


def geodesic(srcs, allowed, limit=1e9):
    dist = {i: 0.0 for i in srcs}
    pq = [(0.0, i) for i in srcs]
    while pq:
        d, i = heapq.heappop(pq)
        if d > dist[i] or d > limit:
            continue
        for e in bm.verts[i].link_edges:
            j = e.other_vert(bm.verts[i]).index
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
        return pts[0] + (pts[1] - pts[0]).normalized() * x
    if x >= sl[-1]:
        return pts[-1] + (pts[-1] - pts[-2]).normalized() * (x - sl[-1])
    for i in range(len(pts) - 1):
        if x <= sl[i + 1]:
            h = sl[i + 1] - sl[i]
            return pts[i].lerp(pts[i + 1], (x - sl[i]) / h if h > 0 else 0)


def project(pts, sl, v):
    best = (1e9, 0.0, 0)
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        ab = b - a
        L2 = ab.length_squared
        u = max(0.0, min(1.0, (v - a).dot(ab) / L2)) if L2 > 0 else 0.0
        d = (v - (a + ab * u)).length
        if d < best[0]:
            best = (d, sl[i] + u * math.sqrt(L2), i)
    return best


def seg_matrix(a0, a1, b0, b1, max_stretch=9.0):
    da, db = a1 - a0, b1 - b0
    r = da.normalized().rotation_difference(db.normalized()).to_matrix().to_4x4()
    u = da.normalized(); stt = min(max_stretch, max(1 / max_stretch, db.length / da.length))
    S = Matrix.Identity(4)
    for i_ in range(3):
        for j_ in range(3):
            S[i_][j_] += (stt - 1) * u[i_] * u[j_]
    return Matrix.Translation(b0) @ r @ S @ Matrix.Translation(-a0)


def seg_dist(p, a, b):
    ab = b - a
    u = max(0.0, min(1.0, (p - a).dot(ab) / max(ab.length_squared, 1e-12)))
    return (p - (a + ab * u)).length


chest = J['Bip01 Spine1']
c0 = min(main, key=lambda i: (co(i) - chest).length)
g_chest = geodesic([c0], main)
kM = kdt([tuple(co(i)) for i in main_ids])


def mm9_tip(last, root):
    """MM9 tentacle end: centroid of the last bone's vertices in the outer 15 % of their distance from the root"""
    pts = A[lab == last]
    d = np.linalg.norm(pts - np.array(tuple(root)), axis=1)
    return Vector(tuple(pts[d > d.max() - 0.15 * (d.max() - d.min())].mean(0)))


def climb(i):
    while True:
        nb = [e.other_vert(bm.verts[i]).index for e in bm.verts[i].link_edges]
        j = max(nb, key=lambda j: g_chest.get(j, -1))
        if g_chest.get(j, -1) <= g_chest[i]:
            return i
        i = j


# Meshy tentacle tips: local maxima of the chest geodesic (above the knees); for every MM9 tentacle tip the farthest
# (geodesically) such maximum within TIP_R of it, on the same side
ext = []
for i, d in g_chest.items():
    if co(i).z > 0.8 and all(g_chest.get(e.other_vert(bm.verts[i]).index, 0) <= d for e in bm.verts[i].link_edges):
        ext.append(i)
tips_mm9 = [mm9_tip(b[-1], J[b[0]]) for _, b in TENTACLES]
tip_of = []
for tm in tips_mm9:
    cand = [i for i in ext if (co(i) - tm).length < TIP_R and co(i).x * tm.x > 0 and i not in tip_of]
    tip_of.append(max(cand, key=lambda i: g_chest[i]))
report['tip_candidates'] = len(ext)
report['tentacles'] = {}
for ti, (name, bones) in enumerate(TENTACLES):
    tipm = tips_mm9[ti]
    target = [J[b].copy() for b in bones] + [tipm]
    ts = arc(target)
    tip = tip_of[ti]
    gd = geodesic([tip], main, 1.4 * ts[-1])
    nb_ = int(1.4 * ts[-1] / BW) + 1
    bins = [[] for _ in range(nb_)]
    for i, d in gd.items():
        bins[min(nb_ - 1, int(d / BW))].append(np.array(tuple(co(i))))
    cen, spr = [], []
    for b in bins:
        if len(b) >= 3:
            b = np.array(b); c = b.mean(0)
            cen.append(Vector(tuple(c))); spr.append(float(np.linalg.norm(b - c, axis=1).mean()))
    # the centreline starts at the first bin centroid, not at the tip vertex (a mouth rim on the long tentacles)
    for _ in range(2):
        cen = [cen[0]] + [(cen[i - 1] + 2 * cen[i] + cen[i + 1]) / 4 for i in range(1, len(cen) - 1)] + [cen[-1]]
    kcut = min(range(len(cen)), key=lambda k: (cen[k] - target[0]).length)
    line = cen[:kcut + 1]                    # tip .. cut
    rad = spr[:kcut + 1]
    pt = line[-1]
    nrm = (line[-1] - line[max(0, len(line) - 4)]).normalized()
    mesh_pts = list(reversed(line)); mrad = list(reversed(rad))
    ms = arc(mesh_pts)

    def plane(v):  # the cut plane bounds only the root end (curled tentacles cross it farther out)
        return (v - pt).dot(nrm) if project(mesh_pts, ms, v)[1] < ROOT_ZONE else -1.0

    mid = rad[int(0.2 * len(rad)):max(int(0.7 * len(rad)), int(0.2 * len(rad)) + 1)]
    cap_r = CAP_K * float(np.median(mid)) + CAP_ADD   # one radius: the tentacle's mid-length spread

    def capsule(v):
        return project(mesh_pts, ms, v)[0], cap_r
    seen = {tip}; st = [tip]
    while st:
        i = st.pop()
        for e in bm.verts[i].link_edges:
            j = e.other_vert(bm.verts[i]).index
            if j in seen or j not in main:
                continue
            v = co(j)
            d, R = capsule(v)
            if plane(v) < BLEND and d < R:
                seen.add(j); st.append(j)
    # the tentacle root goes halfway to the MM9 chain root (a full move sheared the head around the junction)
    target = [pt.lerp(target[0], 0.5)] + target[1:]
    ts = arc(target)
    jm = [at(mesh_pts, ms, x * ms[-1] / ts[-1]) for x in ts]
    # the tip segment keeps the Meshy tip's length (its stretch only pulled the mouth rims into spikes)
    mats = [seg_matrix(jm[k], jm[k + 1], target[k], target[k + 1], 9.0 if k < len(jm) - 2 else 1.0)
            for k in range(len(jm) - 1)]
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
        d, R = capsule(v)
        w = smooth((BLEND - plane(v)) / (2 * BLEND)) * smooth((R - d) / 0.06)
        newp[i] = v.lerp(q, w)
        if w > 0.5:
            chain_of[i] = ti
    for i, q in newp.items():
        bm.verts[i].co = q
    report['tentacles'][name] = {'meshy_len': round(ms[-1], 3), 'mm9_len': round(ts[-1], 3), 'verts': len(seen),
                                 'tip_meshy': [round(c, 3) for c in X0[tip]], 'tip_mm9': [round(c, 3) for c in tipm],
                                 'cut': [round(c, 3) for c in pt], 'capsule': round(cap_r, 3), 'root_mm9': [round(c, 3) for c in target[0]]}

# legs: the global fit leaves the soles above the MM9 floor; below the hip every vertex is lowered by the sole gap
# tapered linearly to zero at the hip (MM9 thigh joint), then labelled by side
hip_z = J['Bip01 R Thigh'].z
sole = float(np.percentile([co(i).z for i in main if co(i).z < 0.5], 1))
gap = sole - MM9_SOLE
for i in main:
    v = co(i)
    if v.z < hip_z:
        v.z -= gap * (hip_z - v.z) / (hip_z - sole)
report['legs'] = {'sole_gap': round(gap, 4)}
for li, (name, side, bones) in enumerate(LEGS):
    for i in main:
        if side * co(i).x > 0.02 and co(i).z < hip_z - 0.08 and chain_of[i] < 0:
            chain_of[i] = len(TENTACLES) + li

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
