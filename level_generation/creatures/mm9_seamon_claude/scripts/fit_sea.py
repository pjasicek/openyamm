"""Fit the Meshy Smart Topology Sea Monster to the MM9 bind pose (SEAMONSTER.abc).

Args: <mm9 source blend> <meshy glb> <out blend> <report json>

0. Clean: faces with an edge longer than THREAD x the median edge (Meshy's thread fan between the hidden far hind leg
   and the tail) are deleted, loose vertices removed and the small holes left behind filled.
1. Global similarity: scale from the length, then symmetric nearest-point ICP (scale + translation; both face -Y).
2. Pieces: welded components under 120 vertices (teeth, tail spines) become piece 2 and later follow their nearest
   body vertex rigidly; the dorsal sail stays a body piece (weighted to the MM9 fin bones).
3. Chains: the tail, both hind legs and both arms are posed onto their MM9 bone chains by per-segment skinning
   (fit_chain_lbs: Meshy joints at the MM9 joint arc fractions, rotation + stretch per segment, blended out at the
   root). The Meshy tip of a chain is the main-body vertex nearest the MM9 tip after step 1.
Per-vertex attributes 'piece' (0 body, 2 small piece) and 'chain' (-1 core, k chain index) for rig_body.py.
"""
import bpy, bmesh, sys, os, json, math, heapq
import numpy as np
from mathutils import Vector, Matrix
from mathutils.kdtree import KDTree

argv = sys.argv[sys.argv.index('--') + 1:]
SRC, MESHY, OUT, REP = argv
NB = 40
BLEND = 0.12
THREAD = 12.0
CHAINS = {'tail': ['Bone02', 'Bone38', 'Bone39', 'Bone03', 'Bone04', 'Bone40', 'Bone05'],
          'legR': ['Bone10', 'Bone11', 'Bone12', 'Bone13'], 'legL': ['Bone21', 'Bone22', 'Bone23', 'Bone24'],
          'armR': ['Bone15', 'Bone16', 'Bone17', 'Bone18', 'Bone19'],
          'armL': ['Bone26', 'Bone27', 'Bone28', 'Bone29', 'Bone30']}
NAMES = list(CHAINS)

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
med = float(np.median([e.calc_length() for e in bm.edges]))
threads = [f for f in bm.faces if max(e.calc_length() for e in f.edges) > THREAD * med]
bmesh.ops.delete(bm, geom=threads, context='FACES')
loose = [v for v in bm.verts if not v.link_faces]
bmesh.ops.delete(bm, geom=loose, context='VERTS')
nb_before = sum(1 for e in bm.edges if e.is_boundary)
bmesh.ops.holes_fill(bm, edges=[e for e in bm.edges if e.is_boundary], sides=40)
bmesh.ops.triangulate(bm, faces=bm.faces[:])
nb_after = sum(1 for e in bm.edges if e.is_boundary)
bm.verts.ensure_lookup_table()
co = lambda i: bm.verts[i].co
report = {'threads_deleted': len(threads), 'loose_deleted': len(loose), 'boundary_edges_before_fill': nb_before,
          'boundary_edges_after_fill': nb_after}

B = np.array([tuple(v.co) for v in bm.verts])
s = (A[:, 1].max() - A[:, 1].min()) / (B[:, 1].max() - B[:, 1].min())
t = np.array([(A[:, i].min() + A[:, i].max()) / 2 - s * (B[:, i].min() + B[:, i].max()) / 2 for i in range(3)])
rng = np.random.default_rng(0)
Bs = B[rng.choice(len(B), min(3000, len(B)), replace=False)]
for _ in range(30):
    X = s * Bs + t
    kX = kdt(X)
    p, q = [], []
    for i, x in enumerate(X):
        p.append(Bs[i]); q.append(A[kA.find(Vector(x))[1]])
    for a_ in A[::max(1, len(A) // 3000)]:
        p.append(Bs[kX.find(Vector(a_))[1]]); q.append(a_)
    p, q = np.array(p), np.array(q)
    mp, mq = p.mean(0), q.mean(0)
    P0, Q0 = p - mp, q - mq
    s = float((Q0 * P0).sum() / (P0 * P0).sum())
    t = mq - s * mp
X = s * B + t
for v, x in zip(bm.verts, X):
    v.co = Vector(x)
report.update({'scale': s, 'translate': t.tolist()})

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
main = comps[0]
piece = np.zeros(len(bm.verts), int)
chain_of = np.full(len(bm.verts), -1, int)
small = [c for c in comps if len(c) < 120]
for c in small:
    piece[c] = 2
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



def mm9_tip(names):
    pts = A[lab == names[-1]]
    far = pts[np.argmax(np.linalg.norm(pts - np.array(J[names[0]]), axis=1))]
    return Vector(far)


report['chains'] = {}
km = KDTree(len(main))
for j, i in enumerate(main):
    km.insert(co(i), j)
km.balance()
for ci, n in enumerate(NAMES):
    tgt = [J[b].copy() for b in CHAINS[n]] + [mm9_tip(CHAINS[n])]
    tip = main[km.find(tgt[-1])[1]]
    report['chains'][n] = {'tip_gap': (co(tip) - tgt[-1]).length,
                           **fit_chain_lbs(main, tip, tgt, ci, sigma=0.05, stop=tgt[0])}

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
