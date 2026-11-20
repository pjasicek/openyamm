"""Fit the Meshy Smart Topology Icky to the MM9 FLYINGICKY bind pose (see the full description below the args).

Args: <mm9 source blend> <meshy glb> <out blend> <report json> [stage: align|full]

1. Global similarity from four landmarks (mouth = teeth centroid, tail tip, right and left wing tips; Kabsch with
   scale), then a few ICP iterations (similarity with rotation) against the MM9 body and feet only.
2. Wings: Meshy's membranes are dropped (the wings are rebuilt flat from the HD top view by build_wings.py). A body
   vertex is a wing vertex when it lies beyond the shoulder (|x| > SHOULDER) inside the wing slab and is not part of a
   leg; the hole along each flank is filled.
3. Tail: centreline (geodesic bins from the tail tip) mapped by arc length onto the MM9 tail chain (Xtailbase ...
   XtailD, tail tip), offsets kept in parallel-transported frames, blended out at the root.
4. Legs: each leg (geodesic region from its middle toe tip) mapped onto its MM9 chain (Xlegpiv, Xleg, Xfoot, XtoeB tip)
   the same way.
5. Head: rigid (rotation + translation) ICP of the head region (vertices nearest the MM9 head bones) onto the MM9
   head vertices, blended into the neck over the neck vertices.
Per-vertex attributes: 'piece' (0 body, 2 teeth) and 'chain' (-1 core, 0 tail, 1 right leg, 2 left leg).
"""
import bpy, bmesh, sys, json, math, heapq
import numpy as np
from mathutils import Vector, Matrix
from mathutils.kdtree import KDTree

argv = sys.argv[sys.argv.index('--') + 1:]
SRC, MESHY, OUT, REP = argv[:4]
STAGE = argv[4] if len(argv) > 4 else 'full'
NB = 40
BLEND = 0.04
SHOULDER = 0.055

bpy.ops.wm.open_mainfile(filepath=SRC)
sc = bpy.context.scene
arm = bpy.data.objects['MM9_Rig']
J = {b.name: Vector(b.head_local) for b in arm.data.bones}
mm9 = {o.name.split('.')[0]: o for o in bpy.data.objects if o.type == 'MESH'}


def verts_of(o):
    out = []
    for v in o.data.vertices:
        g = max(v.groups, key=lambda g: g.weight)
        out.append((o.matrix_world @ v.co, o.vertex_groups[g.group].name))
    return out


allv = [x for o in mm9.values() for x in verts_of(o)]
A = np.array([tuple(p) for p, _ in allv])
lab = np.array([l for _, l in allv])
src_of = np.array([n for n, o in mm9.items() for _ in o.data.vertices])
body_feet = np.isin(src_of, ['body', 'foot', 'foot01'])
teeth_mm9 = np.char.startswith(src_of.astype(str), 'tooth')
M_MOUTH = A[teeth_mm9].mean(0)
bodyA = A[src_of == 'body']
M_TAIL = bodyA[bodyA[:, 1].argmax()]
wr = A[src_of == 'wing']; wl = A[src_of == 'wing01']
M_WR = wr[wr[:, 0].argmin()]; M_WL = wl[wl[:, 0].argmax()]


def kdt(P):
    k = KDTree(len(P))
    for i, p in enumerate(P):
        k.insert(Vector(p), i)
    k.balance()
    return k


# ---------------- Meshy
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=MESHY)
new = [o for o in bpy.data.objects if o not in before]
srco = next(o for o in new if o.type == 'MESH')
bm = bmesh.new()
bm.from_mesh(srco.data)
bm.transform(srco.matrix_world)
for o in new:
    bpy.data.objects.remove(o)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
bm.verts.ensure_lookup_table()


def components():
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
    return comps


comps = components()
main = comps[0]
teeth = [c for c in comps[1:]]
B = np.array([tuple(v.co) for v in bm.verts])
Y_MOUTH = B[[i for c in teeth for i in c]].mean(0)
Bm = B[main]
Y_TAIL = Bm[np.linalg.norm(Bm - Y_MOUTH, axis=1).argmax()]
f = (Y_MOUTH - Y_TAIL); f[2] = 0; f /= np.linalg.norm(f)
right = np.cross(f, [0, 0, 1.0])
line = Y_TAIL + np.outer((Bm - Y_TAIL) @ f, f)
side = (Bm - Y_TAIL) @ right
Y_WR = Bm[side.argmax()]; Y_WL = Bm[side.argmin()]


def similarity(P, Q):
    mp, mq = P.mean(0), Q.mean(0)
    P0, Q0 = P - mp, Q - mq
    U, S_, Vt = np.linalg.svd(Q0.T @ P0)
    D = np.diag([1, 1, np.sign(np.linalg.det(U @ Vt))])
    R = U @ D @ Vt
    s = float((Q0 * (P0 @ R.T)).sum() / (P0 * P0).sum())
    return s, R, mq - s * (R @ mp)


s, R, t = similarity(np.array([Y_MOUTH, Y_TAIL, Y_WR, Y_WL]), np.array([M_MOUTH, M_TAIL, M_WR, M_WL]))
X = s * B @ R.T + t
report = {'landmark_scale': s, 'landmark_rot_deg': math.degrees(math.acos(max(-1, min(1, (np.trace(R) - 1) / 2)))),
          'landmark_residual': [float(np.linalg.norm(s * R @ a + t - b)) for a, b in
                                zip([Y_MOUTH, Y_TAIL, Y_WR, Y_WL], [M_MOUTH, M_TAIL, M_WR, M_WL])]}
for v, x in zip(bm.verts, X):
    v.co = Vector(x)
co = lambda i: bm.verts[i].co


def save(name='Body'):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    obj = bpy.data.objects.new(name, me)
    sc.collection.objects.link(obj)
    for p in me.polygons:
        p.use_smooth = True
    return obj


if STAGE == 'align':
    save()
    bpy.ops.wm.save_as_mainfile(filepath=OUT)
    json.dump(report, open(REP, 'w'), indent=1, default=str)
    print('FIT ' + json.dumps(report, default=str))
    sys.exit(0)

# ---------------- wings out: thin sheet beyond the shoulder (ray cast along -normal measures the thickness)
from mathutils.bvhtree import BVHTree
bm.normal_update()
bvh = BVHTree.FromBMesh(bm)
thick = np.full(len(bm.verts), 1.0)
for v in bm.verts:
    if v.index not in set(main) and False:
        continue
    n = v.normal
    if n.length < 0.5:
        continue
    hit = bvh.ray_cast(v.co - n * 1e-4, -n, 0.2)
    if hit[0] is not None:
        thick[v.index] = hit[3]
mainset = set(main)
Xc = np.array([tuple(v.co) for v in bm.verts])
cx = float(np.median(Xc[main][np.abs(Xc[main][:, 1]) < 0.1][:, 0]))
dxc = np.abs(Xc[:, 0] - cx)
inm = np.zeros(len(Xc), bool); inm[main] = True
# the flank (torso half width ~0.045) inside the wing-root span; beyond it everything at the wing level; the legs
# hang below z -0.045 (and the right leg starts behind the root span)
wing = inm & (Xc[:, 2] > -0.045) & (((dxc > 0.047) & (Xc[:, 1] > -0.13) & (Xc[:, 1] < 0.19))
                                    | ((dxc > 0.1) & (Xc[:, 1] < 0.3)))
report['wing_verts'] = int(wing.sum())
report['body_cx'] = cx
bmesh.ops.delete(bm, geom=[v for v in bm.verts if wing[v.index]], context='VERTS')
bm.verts.ensure_lookup_table()
comps = components()
keep_main = comps[0]
small = [c for c in comps[1:] if 10 <= len(c) < 60]  # the eight teeth
dropped = [c for c in comps[1:] if len(c) >= 60 or len(c) < 10]
report['after_wing_cut'] = {'main': len(keep_main), 'small': [len(c) for c in small],
                            'dropped': [len(c) for c in dropped]}
bmesh.ops.delete(bm, geom=[bm.verts[i] for c in dropped for i in c], context='VERTS')
bm.verts.ensure_lookup_table()
boundary = [e for e in bm.edges if e.is_boundary]
report['boundary_edges_before_fill'] = len(boundary)
bmesh.ops.holes_fill(bm, edges=boundary, sides=200)
bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
report['boundary_edges_after_fill'] = sum(1 for e in bm.edges if e.is_boundary)
# relax the filled caps (vertices on the old cut) a little
bm.verts.ensure_lookup_table()
comps = components()
main = comps[0]
teeth = comps[1:]
mainset = set(main)
piece = np.zeros(len(bm.verts), int)
for c in teeth:
    piece[c] = 2
if STAGE == 'cut':
    save()
    bpy.ops.wm.save_as_mainfile(filepath=OUT)
    json.dump(report, open(REP, 'w'), indent=1, default=str)
    print('FIT ' + json.dumps(report, default=str))
    sys.exit(0)

# ---------------- helpers (from mm9_lobber_claude/scripts/fit_limbs.py)
chain_of = np.full(len(bm.verts), -1, int)
co = lambda i: bm.verts[i].co
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




def rigid_icp(P, Q, iters=25):
    """rotation + translation of P onto the point set Q (symmetric nearest points)"""
    kQ = kdt(Q)
    R = np.eye(3); t = np.zeros(3)
    for _ in range(iters):
        X = P @ R.T + t
        kX = kdt(X)
        p, q = [], []
        for i, x in enumerate(X):
            p.append(P[i]); q.append(Q[kQ.find(Vector(x))[1]])
        for qq in Q:
            p.append(P[kX.find(Vector(qq))[1]]); q.append(qq)
        p, q = np.array(p), np.array(q)
        mp, mq = p.mean(0), q.mean(0)
        U, S_, Vt = np.linalg.svd((q - mq).T @ (p - mp))
        D = np.diag([1, 1, np.sign(np.linalg.det(U @ Vt))])
        R = U @ D @ Vt
        t = mq - R @ mp
    return R, t


def apply(ids, R, t, w=None):
    for k, i in enumerate(ids):
        p = np.array(tuple(co(i)))
        q = R @ p + t
        bm.verts[i].co = Vector(q if w is None else p + (q - p) * w[k])


def rot_deg(R):
    return math.degrees(math.acos(max(-1, min(1, (np.trace(R) - 1) / 2))))


allids = list(range(len(bm.verts)))
mainl = list(main)
MB = A[src_of == 'body']
# a. trunk: rigid ICP of the torso slab onto the MM9 torso
Pc = np.array([tuple(co(i)) for i in mainl])
sel = (Pc[:, 1] > -0.12) & (Pc[:, 1] < 0.17)
R1, t1 = rigid_icp(Pc[sel][::2], MB[(MB[:, 1] > -0.12) & (MB[:, 1] < 0.17)])
apply(allids, R1, t1)
report['trunk_icp'] = {'rot_deg': rot_deg(R1), 't': t1.tolist()}
# b. head: rigid ICP (head + teeth onto MM9 head + teeth + ears), blended into the neck along y
teeth_ids = [i for c in teeth for i in c]
Pc = np.array([tuple(co(i)) for i in allids])
hsel = [i for i in mainl if Pc[i, 1] < -0.15] + teeth_ids
MH = np.concatenate([MB[MB[:, 1] < -0.16], A[teeth_mm9], A[teeth_mm9], A[teeth_mm9]])
R2, t2 = rigid_icp(Pc[hsel], MH)
Y0, Y1 = -0.17, -0.09
w = np.clip((Y1 - Pc[:, 1]) / (Y1 - Y0), 0, 1)
w = w * w * (3 - 2 * w)
apply(allids, R2, t2, w)
report['head_icp'] = {'rot_deg': rot_deg(R2), 't': t2.tolist()}
if STAGE == 'rigid':
    save()
    bpy.ops.wm.save_as_mainfile(filepath=OUT)
    json.dump(report, open(REP, 'w'), indent=1, default=str)
    print('FIT ' + json.dumps(report, default=str))
    sys.exit(0)

# ---------------- c. legs and tail onto their MM9 chains
mouth_now = np.array([tuple(co(i)) for i in teeth_ids]).mean(0)
mainset = set(mainl)
Pc = np.array([tuple(co(i)) for i in allids])
tail_tip = max(mainl, key=lambda i: Pc[i, 1])
# right foot (-x): the backward toes behind the hip
rfoot = [i for i in mainl if Pc[i, 0] < -0.02 and 0.2 < Pc[i, 1] < 0.32 and Pc[i, 2] < 0.06]
rtoe = max(rfoot, key=lambda i: Pc[i, 1] - 0.3 * abs(Pc[i, 0] + 0.06))
LEG_LEN = 0.17
gd_leg = geodesic([rtoe], mainset)
leg_ids = [i for i, d in gd_leg.items() if d < LEG_LEN and Pc[i, 0] < -0.012]
legset = set(leg_ids)
tail_allowed = mainset - legset
tail_t = chain_poly(['Xtailbase', 'XtailA', 'XtailB', 'XtailC', 'XtailD'])
report['tail'] = fit_chain(list(tail_allowed), tail_tip, tail_t[0], tail_t, True, 0)
# The MM9 thigh runs inside the body from Xlegpiv (y 0.07), so a chain fit drags the body in; after the trunk ICP the
# Meshy foot already lies on the MM9 foot, so the leg keeps its shape and is only flagged for the leg-chain weights.
chain_of[leg_ids] = 1
report['leg_region_verts'] = len(leg_ids)
if STAGE == 'chains':
    save()
    bpy.ops.wm.save_as_mainfile(filepath=OUT)
    json.dump(report, open(REP, 'w'), indent=1, default=str)
    print('FIT ' + json.dumps(report, default=str))
    sys.exit(0)

# ---------------- d. symmetry: keep the creature's right half (x <= 0: the full leg), mirror it
tooth_c = [(c, np.array([tuple(co(i)) for i in c]).mean(0)) for c in teeth]
report['teeth_centroids'] = [[round(x, 4) for x in cc] for _, cc in tooth_c]
pl = bm.verts.layers.int.new('piece')
cl_ = bm.verts.layers.int.new('chain')
for v in bm.verts:
    v[pl] = int(piece[v.index]); v[cl_] = int(chain_of[v.index])
# teeth: drop those on the +x side, mirror those on the -x side, keep the ones on the centre line
TC = 0.006
drop_t = [bm.verts[i] for c, cc in tooth_c if cc[0] > TC for i in c]
mirror_t = [bm.verts[i] for c, cc in tooth_c if cc[0] < -TC for i in c]
main_geom = set(bm.verts[i] for i in mainl)
bmesh.ops.delete(bm, geom=drop_t, context='VERTS')
geom = list(main_geom) + list({e for v in main_geom for e in v.link_edges}) + list({f for v in main_geom for f in v.link_faces})
res = bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-6, plane_co=(0, 0, 0), plane_no=(1, 0, 0), clear_outer=True)
half = [v for v in bm.verts if v[pl] == 0] + mirror_t
half_faces = list({f for v in half for f in v.link_faces})
half_edges = list({e for v in half for e in v.link_edges})
dup = bmesh.ops.duplicate(bm, geom=half + half_edges + half_faces)
nv = [g for g in dup['geom'] if isinstance(g, bmesh.types.BMVert)]
nf = [g for g in dup['geom'] if isinstance(g, bmesh.types.BMFace)]
for v in nv:
    v.co.x = -v.co.x
    if v[cl_] == 1:
        v[cl_] = 2
bmesh.ops.reverse_faces(bm, faces=nf)
seam = [v for v in bm.verts if v[pl] == 0 and abs(v.co.x) < 1e-5]
bmesh.ops.remove_doubles(bm, verts=seam, dist=1e-5)
bm.verts.ensure_lookup_table()
# close the throat end and the small seam holes left by the bisect
bmesh.ops.holes_fill(bm, edges=[e for e in bm.edges if e.is_boundary], sides=0)

bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
report['boundary_edges_after_mirror'] = sum(1 for e in bm.edges if e.is_boundary)
report['nonmanifold_after_mirror'] = sum(1 for e in bm.edges if len(e.link_faces) > 2)
me = bpy.data.meshes.new('Body')
bm.to_mesh(me)
obj = bpy.data.objects.new('Body', me)
sc.collection.objects.link(obj)
for p in me.polygons:
    p.use_smooth = True
kA = kdt(A[body_feet])
d = np.array([kA.find(v.co)[2] for v in me.vertices])
report.update({'verts': len(me.vertices), 'tris': sum(len(p.vertices) - 2 for p in me.polygons),
               'dist_to_mm9_mean': float(d.mean()), 'dist_to_mm9_p90': float(np.percentile(d, 90))})
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(report, open(REP, 'w'), indent=1, default=str)
print('FIT ' + json.dumps({k: v for k, v in report.items() if k in ('tris', 'verts', 'boundary_edges_after_mirror',
      'nonmanifold_after_mirror', 'dist_to_mm9_mean', 'teeth_centroids')}, default=str))
