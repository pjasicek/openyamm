"""Fit the Meshy Smart Topology Jellyspore to the MM9 bind pose (JELLYSPORE.abc).

Args: <mm9 source blend> <meshy glb> <out blend> <report json>

1. Global similarity: uniform scale from the bell width, yaw (about the vertical axis) that puts the four Meshy leg
   tips on the MM9 leg directions (+Y, -Y, -X, +X), bell tops aligned.
2. Components (welded): the bell shell pieces stay where the similarity puts them (core); small pieces (spikes,
   collar rings, < 300 vertices) become piece 2 and later follow their nearest body vertex rigidly.
3. Legs: each of the four legs is mapped onto its MM9 chain (Xarmpiv.. XarmD + the MM9 tip): separate leg pieces by
   arc length in parallel-transported frames (fit_chain), legs grown out of the stalk by per-segment skinning
   (fit_chain_lbs) blended out at the collar.
4. Stinger: the stalk below the collar is mapped onto Xtailpiv -> Xtail (the node with the three spikes); Meshy's
   short detached lower stinger piece is mapped onto Xtail -> XtailA -> XtailB -> XtailD -> MM9 tail tip, so the
   needle reaches the MM9 length.
Per-vertex attributes 'piece' (0 body, 2 small piece) and 'chain' (-1 core, k chain index) for rig_body.py.
"""
import bpy, bmesh, sys, os, json, math, heapq
import numpy as np
from mathutils import Vector, Matrix
from mathutils.kdtree import KDTree

argv = sys.argv[sys.argv.index('--') + 1:]
SRC, MESHY, OUT, REP = argv
NB = 40
BLEND = 0.05
LEGS = {'arm': ['Xarmpiv', 'XarmA', 'XarmB', 'XarmC', 'XarmD'],
        'arm01': ['Xarmpiv01', 'XarmA01', 'XarmB01', 'XarmC01', 'XarmD01'],
        'arm02': ['Xarmpiv02', 'XarmA02', 'XarmB02', 'XarmC02', 'XarmD02'],
        'arm03': ['Xarmpiv03', 'XarmA03', 'XarmB03', 'XarmC03', 'XarmD03']}
NAMES = list(LEGS) + ['stalk', 'stinger']

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


kA = kdt(A)
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

# ---------------- components
seen = {}
comps = []
for v in bm.verts:
    if v.index in seen:
        continue
    st = [v]; seen[v.index] = 1; c = []
    while st:
        x = st.pop(); c.append(x.index)
        for e in x.link_edges:
            y = e.other_vert(x)
            if y.index not in seen:
                seen[y.index] = 1; st.append(y)
    comps.append(c)
comps.sort(key=len, reverse=True)
B = np.array([tuple(v.co) for v in bm.verts])


def ext(c):
    P = B[c]
    return P.min(0), P.max(0)


# Meshy (Z up, centred): bell pieces are the components above the collar spanning most of the width
wmax = B[:, 0].max() - B[:, 0].min()
bell = [c for c in comps if ext(c)[0][2] > 0.1 and (ext(c)[1][0] - ext(c)[0][0]) > 0.6 * wmax]
bell_ids = [i for c in bell for i in c]
mm9_bell = A[obj_of == 'bell.mesh']
s = (mm9_bell[:, 0].max() - mm9_bell[:, 0].min()) / (B[bell_ids, 0].max() - B[bell_ids, 0].min())
main = comps[0]
lmin, lmax = ext(main)
# leg tips: lowest points away from the axis, in the main piece and the separate leg pieces
legs_sep = [c for c in comps[1:] if c not in bell and len(c) >= 300]
stinger = [c for c in comps if c not in bell and c is not main and 120 <= len(c) < 300
           and (ext(c)[1][2] - ext(c)[0][2]) > 2.5 * max(ext(c)[1][0] - ext(c)[0][0], ext(c)[1][1] - ext(c)[0][1])]
stinger = max(stinger, key=len) if stinger else None
small = [c for c in comps if c not in bell and c is not main and c not in legs_sep and c is not stinger]
rad = np.linalg.norm(B[:, :2], axis=1)
tips = []
for c in legs_sep:
    tips.append(min(c, key=lambda i: B[i, 2]))
cand = [i for i in main if rad[i] > 0.12 and B[i, 2] < -0.25]
az = np.arctan2(B[cand, 1], B[cand, 0])
groups = []
for i, a in zip(cand, az):
    for gp in groups:
        if abs((a - gp[0] + math.pi) % (2 * math.pi) - math.pi) < 0.6:
            gp[1].append(i); break
    else:
        groups.append([a, [i]])
groups.sort(key=lambda g: -len(g[1]))
main_tips = [min(g[1], key=lambda i: B[i, 2]) for g in groups[:4 - len(tips)]]
tips_all = tips + main_tips
tip_az = [math.atan2(B[i, 1], B[i, 0]) for i in tips_all]
mm9_az = {n: math.atan2(J[LEGS[n][-1]].y, J[LEGS[n][-1]].x) for n in LEGS}
# yaw: best rotation (fine search) taking the tip azimuths onto the four MM9 leg directions
best = (1e9, 0.0)
for k in range(720):
    yaw = k * math.pi / 360
    cost = sum(min(abs((a + yaw - m + math.pi) % (2 * math.pi) - math.pi) for m in mm9_az.values()) for a in tip_az)
    if cost < best[0]:
        best = (cost, yaw)
yaw = best[1]
R = np.array(Matrix.Rotation(yaw, 3, 'Z'))
X = s * B @ R.T
dz = mm9_bell[:, 2].max() - X[bell_ids, 2].max()
X[:, 2] += dz
for v, x in zip(bm.verts, X):
    v.co = Vector(x)
report = {'scale': s, 'yaw_deg': math.degrees(yaw), 'yaw_cost': best[0], 'dz': dz,
          'components': [len(c) for c in comps], 'bell': [len(c) for c in bell], 'legs_separate': [len(c) for c in legs_sep],
          'stinger_piece': len(stinger) if stinger else None, 'small': [len(c) for c in small]}

piece = np.zeros(len(bm.verts), int)
chain_of = np.full(len(bm.verts), -1, int)
for c in small:
    piece[c] = 2


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


def arc(pts):
    out = [0.0]
    for a, b in zip(pts, pts[1:]):
        out.append(out[-1] + (b - a).length)
    return out


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


def frames(pts, sl, n=80):
    out = []
    prev = None
    for k in range(n + 1):
        x = sl[-1] * k / n
        p, _ = at(pts, sl, x)
        a, _ = at(pts, sl, max(0, x - sl[-1] / n))
        b, _ = at(pts, sl, min(sl[-1], x + sl[-1] / n))
        tg = (b - a).normalized()
        if prev is None:
            ref = Vector((1, 0, 0)) if abs(tg.x) < 0.9 else Vector((0, 1, 0))
            nn = (ref - tg * ref.dot(tg)).normalized()
        else:
            nn = (prev - tg * prev.dot(tg)).normalized()
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


def centreline(ids, tip):
    allowed = set(ids)
    gd = geodesic([tip], allowed)
    gmax = max(gd.values())
    bins = [[] for _ in range(NB)]
    gb = [[] for _ in range(NB)]
    for i, d in gd.items():
        k = min(NB - 1, int(d / gmax * NB))
        bins[k].append(co(i)); gb[k].append(d)
    cl = [co(tip).copy()] + [sum(b, Vector()) / len(b) for b in bins if b]
    cg = [0.0] + [sum(g) / len(g) for g in gb if g]
    for _ in range(3):
        cl = [cl[0]] + [(cl[i - 1] + 2 * cl[i] + cl[i + 1]) / 4 for i in range(1, len(cl) - 1)] + [cl[-1]]
    return gd, gmax, cl, cg


def fit_piece(ids, tip, target_pts, label):
    """Separate piece: its far end maps onto target_pts[0], its tip onto target_pts[-1] (arc length, frames)."""
    gd, gmax, cl, cg = centreline(ids, tip)
    mesh_pts = list(reversed(cl))
    ms = arc(mesh_pts)
    ts = arc(target_pts)
    f_src, f_dst = frames(mesh_pts, ms), frames(target_pts, ts)
    cs_tip = arc(cl)

    def arc_from_tip(g):
        for j in range(len(cg) - 1):
            if g <= cg[j + 1] or j == len(cg) - 2:
                h = cg[j + 1] - cg[j]
                a = (g - cg[j]) / h if h > 0 else 0.0
                return cs_tip[j] + a * (cs_tip[j + 1] - cs_tip[j])
        return cs_tip[-1]
    newpos = {}
    for i in ids:
        x = ms[-1] - arc_from_tip(gd.get(i, gmax))
        p0, F0 = frame_at(f_src, x)
        p1, F1 = frame_at(f_dst, x * ts[-1] / ms[-1])
        newpos[i] = p1 + F1 @ (F0.transposed() @ (co(i) - p0))
        chain_of[i] = label
    for i, q in newpos.items():
        bm.verts[i].co = q
    return {'meshy_len': ms[-1], 'mm9_len': ts[-1], 'stretch': ts[-1] / ms[-1], 'moved': len(newpos)}


def fit_chain_lbs(ids, tip, target_pts, label, sigma=0.02, stop=None):
    """Attached piece: joints on the Meshy centreline at the MM9 joint arc fractions, each segment posed onto its
    MM9 segment (rotation + stretch along it), blended by distance; the root blends to rest over BLEND."""
    allowed = set(ids)
    gd = geodesic([tip], allowed)
    gmax = max(gd.values())
    bins = [[] for _ in range(NB)]
    for i, d in gd.items():
        bins[min(NB - 1, int(d / gmax * NB))].append(co(i))
    cl = [co(tip).copy()] + [sum(b, Vector()) / len(b) for b in bins if b]
    for _ in range(3):
        cl = [cl[0]] + [(cl[i - 1] + 2 * cl[i] + cl[i + 1]) / 4 for i in range(1, len(cl) - 1)] + [cl[-1]]
    root = stop if stop is not None else target_pts[0]
    kcut = min(range(len(cl)), key=lambda k: (cl[k] - root).length)
    mesh_pts = list(reversed(cl[:kcut + 1]))
    ms = arc(mesh_pts)
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
        r = da.normalized().rotation_difference(db.normalized()).to_matrix().to_4x4()
        u = da.normalized()
        stt = db.length / da.length
        S = Matrix.Identity(4)
        for i_ in range(3):
            for j_ in range(3):
                S[i_][j_] += (stt - 1) * u[i_] * u[j_]
        mats.append(Matrix.Translation(b0) @ r @ S @ Matrix.Translation(-a0))
    root_g = ms[-1]

    def seg_dist(p, k):
        a, b = src_j[k], src_j[k + 1]
        ab = b - a
        u = max(0.0, min(1.0, (p - a).dot(ab) / max(ab.length_squared, 1e-12)))
        return (p - (a + ab * u)).length
    newpos = {}
    for i in ids:
        g = gd.get(i, 1e9)
        if g > root_g + BLEND:
            continue
        p = co(i)
        ds = [seg_dist(p, k) for k in range(len(mats))]
        dmin = min(ds)
        ws = [math.exp(-((d - dmin) / sigma) ** 2) for d in ds]
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
    return {'meshy_len': ms[-1], 'mm9_len': ts[-1], 'moved': len(newpos),
            'segment_stretch': [round((target_pts[k + 1] - target_pts[k]).length /
                                      max((src_j[k + 1] - src_j[k]).length, 1e-6), 2) for k in range(len(ts) - 1)]}


def mm9_tip(names, obj):
    pts = A[obj_of == obj]
    return Vector(pts[np.argmin(pts[:, 2])])


LEG_OBJ = {'arm': 'arm01.mesh', 'arm01': 'arm03.mesh', 'arm02': 'arm.mesh', 'arm03': 'arm02.mesh'}
targets = {n: [J[b].copy() for b in LEGS[n]] + [mm9_tip(LEGS[n], LEG_OBJ[n])] for n in LEGS}
report['legs'] = {}
# assign each tip to the MM9 leg of the nearest direction (after the yaw)
used = set()
for ti, tip in enumerate(tips_all):
    a = math.atan2(co(tip).y, co(tip).x)
    n = min((n for n in LEGS if n not in used), key=lambda n: abs((a - mm9_az[n] + math.pi) % (2 * math.pi) - math.pi))
    used.add(n)
    li = list(LEGS).index(n)
    if ti < len(tips):
        report['legs'][n] = {'separate': True, **fit_piece(legs_sep[ti], tip, targets[n], li)}
    else:
        report['legs'][n] = {'separate': False, **fit_chain_lbs(main, tip, targets[n], li, stop=J[LEGS[n][0]])}
# stalk: the lowest central point of the main piece is the node; it maps onto Xtailpiv -> Xtail
node = min((i for i in main if np.hypot(co(i).x, co(i).y) < 0.04), key=lambda i: co(i).z)
stalk_t = [J['Xtailpiv'].copy(), J['Xtail'].copy()]
report['stalk'] = fit_chain_lbs(main, node, stalk_t, NAMES.index('stalk'), stop=J['Xtailpiv'])
if stinger is not None:
    top = max(stinger, key=lambda i: co(i).z)
    g = geodesic([top], set(stinger))
    stip = max(g, key=g.get)
    tail_tip = mm9_tip(None, 'arm04.mesh')
    tt = [J['Xtail'].copy(), J['XtailA'].copy(), J['XtailB'].copy(), tail_tip]
    report['stinger'] = fit_piece(stinger, stip, tt, NAMES.index('stinger'))

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
report.update({'chain_names': NAMES, 'verts': len(me.vertices), 'tris': sum(len(p.vertices) - 2 for p in me.polygons),
               'dist_to_mm9_mean': float(d.mean()), 'dist_to_mm9_p90': float(np.percentile(d, 90))})
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(report, open(REP, 'w'), indent=1, default=str)
print('FIT ' + json.dumps(report, default=str))
