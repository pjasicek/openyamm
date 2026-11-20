"""Fit the Meshy Smart Topology body to the MM9 dragonfly bind pose (centreline bend), drop Meshy's wings and threads.

Args: <meshy glb> <mm9 tier1 glb> <out blend> <report json>

1. Import both. Meshy: main body, two eyes, jaw/teeth pieces; its four wings and the stray threads are deleted
   (the wings are rebuilt flat by build_wings.py). The S-curve plane is aligned to YZ, head toward -Y.
2. Centrelines of both bodies: centroids of geodesic-distance bins from the tail tip.
3. Arc length is mapped piecewise between landmarks (tail tip, wing root, back of skull); each vertex keeps its offset
   from its own centreline in the local (tangent, normal, lateral) frame, scaled by one factor, and is placed on the
   MM9 centreline. The head (from the back of the skull) and every separate piece move rigidly with the skull frame.
Writes the fitted mesh 'Dfly' (plus 'Dfly_Eyes' pieces joined in) next to the MM9 armature and its clips.
"""
import bpy, bmesh, sys, json, math, heapq
from mathutils import Vector, Matrix
from mathutils.kdtree import KDTree

argv = sys.argv[sys.argv.index('--') + 1:]
MESHY, MM9, OUT, REP = argv
NBINS = 70

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene


def import_glb(path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    return [o for o in bpy.data.objects if o not in before]


mm9_objs = import_glb(MM9)
mm9_arm = next(o for o in mm9_objs if o.type == 'ARMATURE')
mm9_arm.name = 'MM9_Rig'
for o in mm9_objs:
    if o.type == 'MESH' and o.name.startswith('Icosphere'):
        bpy.data.objects.remove(o)
mm9_body = bpy.data.objects['d_body.mesh']
if mm9_arm.animation_data:
    mm9_arm.animation_data.action = None
for pb in mm9_arm.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()


def welded(obj):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.transform(obj.matrix_world)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
    bm.verts.ensure_lookup_table()
    return bm


def components(bm):
    seen = {}
    comps = []
    for v in bm.verts:
        if v.index in seen:
            continue
        stack = [v]
        seen[v.index] = len(comps)
        c = []
        while stack:
            x = stack.pop()
            c.append(x.index)
            for e in x.link_edges:
                y = e.other_vert(x)
                if y.index not in seen:
                    seen[y.index] = len(comps)
                    stack.append(y)
        comps.append(c)
    return comps


def dijkstra(bm, src, allowed):
    dist = {src: 0.0}
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
                dist[j] = nd
                heapq.heappush(pq, (nd, j))
    return dist


def centreline(bm, idx, snout_pick):
    """Tail-to-snout centroid polyline and per-vertex geodesic distance from the tail tip."""
    allowed = set(idx)
    snout = snout_pick(idx)
    d0 = dijkstra(bm, snout, allowed)
    tail = max(d0, key=d0.get)
    dt = dijkstra(bm, tail, allowed)
    gmax = max(dt.values())
    bins = [[] for _ in range(NBINS)]
    for i, d in dt.items():
        bins[min(NBINS - 1, int(d / gmax * NBINS))].append(bm.verts[i].co)
    pts = [sum(b, Vector()) / len(b) for b in bins if b]
    pts = [bm.verts[tail].co.copy()] + pts + [bm.verts[snout].co.copy()]
    # light smoothing, keep the ends
    sm = [pts[0]] + [(pts[i - 1] + 2 * pts[i] + pts[i + 1]) / 4 for i in range(1, len(pts) - 1)] + [pts[-1]]
    return sm, dt, gmax, tail, snout


def arc(pts):
    s = [0.0]
    for a, b in zip(pts, pts[1:]):
        s.append(s[-1] + (b - a).length)
    return s


def at(pts, s_list, s):
    s = max(0.0, min(s_list[-1], s))
    for i in range(len(pts) - 1):
        if s <= s_list[i + 1] or i == len(pts) - 2:
            h = s_list[i + 1] - s_list[i]
            a = (s - s_list[i]) / h if h > 0 else 0.0
            return pts[i].lerp(pts[i + 1], a), (pts[i + 1] - pts[i]).normalized()
    return pts[-1], (pts[-1] - pts[-2]).normalized()


def frame(pts, s_list, s, window=0.03):
    p, _ = at(pts, s_list, s)
    a, _ = at(pts, s_list, s - window)
    b, _ = at(pts, s_list, s + window)
    t = (b - a).normalized()
    lat = Vector((1, 0, 0))
    lat = (lat - t * lat.dot(t)).normalized()
    n = t.cross(lat)
    return p, Matrix((t, n, lat)).transposed()  # columns t, n, lat


def project(pts, s_list, v, s_hint, win):
    best = (1e9, 0.0)
    for i in range(len(pts) - 1):
        if abs(s_list[i] - s_hint) > win and abs(s_list[i + 1] - s_hint) > win:
            continue
        a, b = pts[i], pts[i + 1]
        ab = b - a
        L2 = ab.length_squared
        u = max(0.0, min(1.0, (v - a).dot(ab) / L2)) if L2 > 0 else 0.0
        q = a + ab * u
        d = (v - q).length
        if d < best[0]:
            best = (d, s_list[i] + u * math.sqrt(L2))
    return best[1]


def catmull(ctrl, sub=10):
    out = []
    n = len(ctrl)
    for i in range(n - 1):
        p0 = ctrl[max(0, i - 1)]; p1 = ctrl[i]; p2 = ctrl[i + 1]; p3 = ctrl[min(n - 1, i + 2)]
        for k in range(sub):
            t = k / sub
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                              + (-p0 + 3 * p1 - 3 * p2 + p3) * t * t * t))
    out.append(ctrl[-1].copy())
    return out


def smooth_pts(pts, passes):
    for _ in range(passes):
        pts = [pts[0]] + [(pts[i - 1] + 2 * pts[i] + pts[i + 1]) / 4 for i in range(1, len(pts) - 1)] + [pts[-1]]
    return pts


def resample(pts, n):
    s = arc(pts)
    return [at(pts, s, s[-1] * k / (n - 1))[0] for k in range(n)]


# ---------------- MM9 side
mbm = welded(mm9_body)
mm9_idx = list(range(len(mbm.verts)))
m_pts, m_dt, m_gmax, m_tail, m_snout = centreline(
    mbm, mm9_idx, lambda idx: min(idx, key=lambda i: mbm.verts[i].co.y))
M_WING = Vector((0.0, 0.066, 0.287))
lab_layer = None
# MM9 skull landmark: the Xheadpiv bone head (skull pivot)
mm9_bones = {b.name: mm9_arm.matrix_world @ b.head_local for b in mm9_arm.data.bones}
M_SKULL = mm9_bones['Xheadpiv']
CHAIN = ['XtailE', 'XtailD', 'XtailC', 'XtailB', 'XtailA', 'Xtail', 'XbackE', 'XbackD', 'XbackC', 'XbackB', 'XbackA',
         'Xback', 'XCENTER', 'Xwingbase', 'Xneck', 'Xheadpiv']
ctrl = [mbm.verts[m_tail].co.copy()] + [mm9_bones[b].copy() for b in CHAIN] + [mbm.verts[m_snout].co.copy()]
m_pts = resample(catmull(ctrl), 160)
m_s = arc(m_pts)
M_WING = mm9_bones['Xwingbase']
eye_v = [mbm.verts[i].co for i in mm9_idx if abs(mbm.verts[i].co.x) > 0.06]
M_EYE = sum(eye_v, Vector()) / len(eye_v)

# ---------------- Meshy side
objs = import_glb(MESHY)
meshy = next(o for o in objs if o.type == 'MESH')
bm = bmesh.new()
bm.from_mesh(meshy.data)
bm.transform(meshy.matrix_world)
bm.verts.ensure_lookup_table()
comps = components(bm)
comps.sort(key=len, reverse=True)
main = comps[0]
cent = lambda c: sum((bm.verts[i].co for i in c), Vector()) / len(c)

# align: plane normal of the main body (least-variance direction in XY) -> X; head toward -Y
import numpy as np
P = np.array([bm.verts[i].co[:] for i in main])
mu = P.mean(0)
cov = np.cov((P - mu)[:, :2].T)
w, V = np.linalg.eigh(cov)
nrm = V[:, 0]  # smallest variance in XY = lateral
ang = math.atan2(nrm[1], nrm[0])
R = Matrix.Rotation(-ang, 4, 'Z')
bm.transform(R)
# classify pieces
main_set = set(main)
kd_main = KDTree(len(main))
for k, i in enumerate(main):
    kd_main.insert(bm.verts[i].co, k)
kd_main.balance()
eyes, head_pieces, wings, dropped = [], [], [], []
zmax = max(bm.verts[i].co.z for i in main)
for c in comps[1:]:
    cc = cent(c)
    co = [bm.verts[i].co for i in c]
    ext = max((a - cc).length for a in co)
    near = min(kd_main.find(p)[2] for p in co)
    if len(c) > 300 and abs(cc.x) > 0.12 and cc.z > 0.12:
        wings.append(c)
    elif len(c) > 300 and near < 0.02:
        eyes.append(c)
    elif near < 0.02 and ext < 0.08:
        head_pieces.append(c)
    else:
        dropped.append(c)
# head toward -Y: flip when the eyes sit on the +Y side of the body
eye_mean = sum((cent(c) for c in eyes), Vector()) / max(1, len(eyes))
if eye_mean.y > mu[1] * 0 + sum(bm.verts[i].co.y for i in main) / len(main):
    F = Matrix.Rotation(math.pi, 4, 'Z')
    bm.transform(F)
    R = F @ R
snout_i = min(main, key=lambda i: bm.verts[i].co.y)
report = {'components': len(comps), 'main_verts': len(main), 'eyes': [len(c) for c in eyes],
          'head_pieces': [len(c) for c in head_pieces], 'wings': [len(c) for c in wings],
          'dropped': [[len(c), [round(x, 3) for x in cent(c)]] for c in dropped], 'rotation_deg': math.degrees(ang)}

# Meshy wing root: wing vertex nearest to the main body, averaged over the four wings
roots = []
for c in wings:
    best = min(((kd_main.find(bm.verts[i].co)[2], bm.verts[i].co.copy()) for i in c), key=lambda x: x[0])
    roots.append(best[1])
Y_WING = sum(roots, Vector()) / max(1, len(roots))
eye_c = [cent(c) for c in eyes]
Y_EYE = sum(eye_c, Vector()) / max(1, len(eye_c))

y_pts, y_dt, y_gmax, y_tail, y_snout = centreline(bm, main, lambda idx: snout_i)
y_pts = resample(smooth_pts(y_pts, 6), 160)
y_s = arc(y_pts)

# landmarks in arc length
def s_of(pts, s_list, p):
    return project(pts, s_list, p, 0.0, 1e9)

m_lm = [0.0, s_of(m_pts, m_s, M_WING), s_of(m_pts, m_s, M_SKULL), m_s[-1]]
# Meshy skull: back of the skull ~ the eye centre projected, moved back by the MM9 eye-to-skull ratio
m_eye = s_of(m_pts, m_s, M_EYE)
y_eye = s_of(y_pts, y_s, Y_EYE)
y_lm = [0.0, s_of(y_pts, y_s, Y_WING), 0.0, y_s[-1]]
y_lm[2] = y_eye - (m_eye - m_lm[2]) * (y_lm[3] - y_lm[1]) / (m_lm[3] - m_lm[1])
k = (m_lm[2] - m_lm[0]) / (y_lm[2] - y_lm[0])  # scale from the body length up to the skull
report['mm9_pts'] = [list(p) for p in m_pts]
report['meshy_pts'] = [list(p) for p in y_pts]
report['meshy_eye'] = list(Y_EYE); report['meshy_wing'] = list(Y_WING)
report.update({'mm9_landmarks': m_lm, 'meshy_landmarks': y_lm, 'scale': k, 'mm9_len': m_s[-1],
               'meshy_len': y_s[-1]})


def map_s(s):
    for i in range(len(y_lm) - 1):
        if s <= y_lm[i + 1] or i == len(y_lm) - 2:
            a = (s - y_lm[i]) / (y_lm[i + 1] - y_lm[i])
            return m_lm[i] + a * (m_lm[i + 1] - m_lm[i])


def rigid(p, s_src):
    c0, F0 = frame(y_pts, y_s, s_src)
    c1, F1 = frame(m_pts, m_s, map_s(s_src))
    return c1 + F1 @ (F0.transposed() @ (p - c0)) * k


S_HEAD = y_lm[2]
new_co = {}
win = 0.12 * y_s[-1]
for i in main:
    v = bm.verts[i].co
    s_hint = y_dt.get(i, 0.0) / y_gmax * y_s[-1]
    s = project(y_pts, y_s, v, s_hint, win)
    if s >= S_HEAD:
        new_co[i] = rigid(v, S_HEAD)
    else:
        new_co[i] = rigid(v, s)
for c in head_pieces:
    for i in c:
        new_co[i] = rigid(bm.verts[i].co, S_HEAD)
# eyes: clean spheres fitted to Meshy's lumpy eye pieces (their stray threads go with them)
eye_spheres = []
for c in eyes:
    pts = [bm.verts[i].co.copy() for i in c]
    cen = Vector([sorted(p[j] for p in pts)[len(pts) // 2] for j in range(3)])
    for _ in range(4):
        d = sorted((p - cen).length for p in pts)
        r = d[len(d) // 2]
        core = [p for p in pts if (p - cen).length < 1.3 * r]
        cen = sum(core, Vector()) / len(core)
    d = sorted((p - cen).length for p in core)
    r = d[int(len(d) * 0.8)]
    eye_spheres.append((rigid(cen, S_HEAD), r * k))
report['eye_spheres'] = [[list(c), r] for c, r in eye_spheres]
# stray threads: Meshy strings from the head to the wings, far from the body's centreline
far = []
for i, p in list(new_co.items()):
    if project(m_pts, m_s, p, 0.0, 1e9) is not None:
        d = min((p - q).length for q in m_pts)
        if d > 0.07:
            far.append(i)
for i in far:
    del new_co[i]
report['thread_verts_dropped'] = len(far)
keep = set(new_co)
for i, p in new_co.items():
    bm.verts[i].co = p
piece = bm.verts.layers.int.new('piece')
hp_set = set(i for c in head_pieces for i in c)
for v in bm.verts:
    v[piece] = 2 if v.index in hp_set else 0
bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.index not in keep], context='VERTS')
loose = [v for v in bm.verts if not v.link_faces]
bmesh.ops.delete(bm, geom=loose, context='VERTS')
boundary = [e for e in bm.edges if e.is_boundary]
report['boundary_edges_before_fill'] = len(boundary)
bmesh.ops.holes_fill(bm, edges=boundary, sides=40)
bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
report['boundary_edges_after_fill'] = sum(1 for e in bm.edges if e.is_boundary)
for cen, r in eye_spheres:
    res = bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=10, radius=r,
                                    matrix=Matrix.Translation(cen))
    for v in res['verts']:
        v[piece] = 1
me = bpy.data.meshes.new('Dfly')
bm.to_mesh(me)
obj = bpy.data.objects.new('Dfly', me)
sc.collection.objects.link(obj)
for o in objs:
    bpy.data.objects.remove(o)
for p in me.polygons:
    p.use_smooth = True
report['fitted_tris'] = sum(len(p.vertices) - 2 for p in me.polygons)
report['fitted_verts'] = len(me.vertices)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(report, open(REP, 'w'), indent=1, default=str)
print('FIT ' + json.dumps(report, default=str))
