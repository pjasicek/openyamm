"""Step B: the head-only parts on the posed body. Body and face are cut by one slanted plane, from the throat under the chin up to the nape (the hair covers the back of the
joint), the face ring conformed onto the body ring with a soft falloff and bridged. The flaps, hair sheet and studs stay parts; a new hair mass replaces Meshy's sheet.
Part ids: 0 skin, 3 studs, 6/7 flaps (rebuilt by make_flaps.py), 10 face, 11 hair, 12 teeth, 13 eyes. Args: <pose blend> <head blend> <out blend>"""
import bpy, bmesh, sys
import numpy as np
from mathutils import Vector
POSE, HEAD, OUT = sys.argv[sys.argv.index('--') + 1:]
A = np.array([0, -0.045, 0.600]); B = np.array([0, 0.115, 0.700])     # the plane's line in the x = 0 section, throat to nape
t_ = B - A; t_ = t_ / np.linalg.norm(t_)
PN = np.array([0, -t_[2], t_[1]])
if PN[2] < 0: PN = -PN
bpy.ops.wm.open_mainfile(filepath=POSE)
body = bpy.data.objects['Body']
with bpy.data.libraries.load(HEAD) as (src, dst):
    dst.objects = [n for n in src.objects]
parts = {o.name: o for o in dst.objects}
pid = {'Face': 10, 'Hair': 11, 'Teeth': 12, 'Eyes': 13}
bm = bmesh.new(); bm.from_mesh(body.data)
lay = bm.verts.layers.int['part']
# the old sheet of hair and the sheets of the flaps go. The sheets give the new flaps their shape
SHEET = {pid_: np.array([v.co[:] for v in bm.verts if v[lay] == pid_]) for pid_ in (6, 7)}
bmesh.ops.delete(bm, geom=[v for v in bm.verts if v[lay] in (2, 6, 7)], context='VERTS')
# belt plate: mirrored off-centre it read as two discs. Pieces on the centre line go; a clean disc is added below
seen = set(); dead = []
for v0 in bm.verts:
    if v0 in seen or v0[lay] != 3: continue
    st = [v0]; seen.add(v0); cc = [v0]
    while st:
        x_ = st.pop()
        for e in x_.link_edges:
            y_ = e.other_vert(x_)
            if y_ not in seen: seen.add(y_); st.append(y_); cc.append(y_)
    q = np.array([u.co[:] for u in cc])
    if q[:, 0].min() < 0 < q[:, 0].max() or np.abs(q[:, 0]).min() < 0.03 and np.ptp(q, 0).max() > 0.03 or np.ptp(q, 0).max() > 0.05: dead += cc
print('STUDS dead', len(dead))
bmesh.ops.delete(bm, geom=dead, context='VERTS')
for v in bm.verts:
    if v[lay] not in (0, 3): v[lay] = 0
mark = bm.verts.layers.int.new('mark')
for v in bm.verts: v[mark] = 1
# Meshy's trapezius stands well above MM9's shoulder line and left no neck under the chin
DROP = 0.085
for v in bm.verts:
    if v[lay] == 0 and v.co.z > 0.46:
        t = min(1.0, (v.co.z - 0.46) / 0.22); t = t * t * (3 - 2 * t)
        fx = max(0.0, min(1.0, (0.36 - abs(v.co.x)) / 0.2)); fx = fx * fx * (3 - 2 * fx)
        v.co.z -= DROP * t * fx
# stud pieces below the belt are specks
bmesh.ops.delete(bm, geom=[v for v in bm.verts if v[lay] == 3 and v.co.z < 0.17], context='VERTS')
sk = [v for v in bm.verts if v[lay] == 0]
g = sk + list({e for v in sk for e in v.link_edges}) + list({f for v in sk for f in v.link_faces})
bmesh.ops.bisect_plane(bm, geom=g, plane_co=tuple(A), plane_no=tuple(PN), clear_outer=True)
sdist = lambda co: float((np.array(co) - A) @ PN)
# ---- clean skin: closed and voxel-remeshed, Meshy's specks and folds go; the hands stay as fitted, for sharp claws
VOX = 0.0036; XCUT = 0.70
tmpm = bpy.data.meshes.new('tmp')
bs = bm.copy()
lays = bs.verts.layers.int['part']
bmesh.ops.delete(bs, geom=[v for v in bs.verts if v[lays] != 0], context='VERTS')
r = bmesh.ops.holes_fill(bs, edges=[e for e in bs.edges if e.is_boundary], sides=200)
print('HOLES filled', len(r['faces']), 'left', sum(1 for e in bs.edges if e.is_boundary), 'nonman', sum(1 for e in bs.edges if len(e.link_faces) > 2))
bmesh.ops.recalc_face_normals(bs, faces=bs.faces)
bs.to_mesh(tmpm); bs.free()
vx = bpy.data.objects.new('Vox', tmpm); bpy.context.scene.collection.objects.link(vx)
bpy.context.view_layer.objects.active = vx
for o in bpy.data.objects: o.select_set(o is vx)
m = vx.modifiers.new('r', 'REMESH'); m.mode = 'VOXEL'; m.voxel_size = VOX; m.use_smooth_shade = True
bpy.ops.object.modifier_apply(modifier='r')
print('VOX', len(tmpm.vertices))
m = vx.modifiers.new('s', 'SMOOTH'); m.factor = 0.6; m.iterations = 6
bpy.ops.object.modifier_apply(modifier='s')
ends = bpy.data.meshes.new('ends')
bv = bmesh.new(); bv.from_mesh(tmpm)
seen = set(); comps = []
for v in bv.verts:
    if v in seen: continue
    st = [v]; seen.add(v); cc = [v]
    while st:
        x = st.pop()
        for e in x.link_edges:
            y = e.other_vert(x)
            if y not in seen: seen.add(y); st.append(y); cc.append(y)
    comps.append(cc)
comps.sort(key=len, reverse=True)
print('VOX comps', [len(c) for c in comps[:6]])
for c in comps[1:]: bmesh.ops.delete(bv, geom=c, context='VERTS')
for sgn in (1, -1):
    bmesh.ops.bisect_plane(bv, geom=list(bv.verts) + list(bv.edges) + list(bv.faces), plane_co=(sgn * XCUT, 0, 0), plane_no=(sgn, 0, 0), clear_outer=True)
# open the cap at the neck
bmesh.ops.delete(bv, geom=[f for f in bv.faces if abs(sdist(f.calc_center_median())) < 0.0025 and f.normal.dot(Vector(PN)) > 0.8], context='FACES')
# belt centre: Meshy's folds round the plate
for _ in range(12):
    mv = {}
    for v in bv.verts:
        if abs(v.co.x) < 0.16 and 0.17 < v.co.z < 0.40 and v.co.y < 0:
            w = min(1.0, (0.16 - abs(v.co.x)) / 0.03) * min(1.0, (v.co.z - 0.17) / 0.03) * min(1.0, (0.40 - v.co.z) / 0.03)
            mv[v] = (sum((e.other_vert(v).co for e in v.link_edges), Vector()) / len(v.link_edges), w)
    for v, (c, w) in mv.items(): v.co = v.co * (1 - w * 0.7) + c * w * 0.7
bv.to_mesh(tmpm); bv.free()
for o in bpy.data.objects: o.select_set(o is vx)
m = vx.modifiers.new('d', 'DECIMATE'); m.decimate_type = 'COLLAPSE'; m.ratio = 0.14; m.use_collapse_triangulate = True
bpy.ops.object.modifier_apply(modifier='d')
print('VOX decimated', len(tmpm.vertices))
# the arm ends of the fitted skin, in this bmesh; the rest of the old skin leaves
sk = [v for v in bm.verts if v[lay] == 0]
g = list({e for v in sk for e in v.link_edges}) + sk + list({f for v in sk for f in v.link_faces})
for sgn in (1, -1):
    bmesh.ops.bisect_plane(bm, geom=list(bm.verts) + list(bm.edges) + list(bm.faces), plane_co=(sgn * XCUT, 0, 0), plane_no=(sgn, 0, 0))
bmesh.ops.delete(bm, geom=[v for v in bm.verts if v[lay] == 0 and abs(v.co.x) < XCUT - 1e-4], context='VERTS')
for v in bm.verts: v[mark] = 1
bm.from_mesh(tmpm)
for v in bm.verts:
    if not v[mark]: v[lay] = 0
tm = {}
for sgn in (1, -1):
    a = [v for v in bm.verts if not v[mark] and v.is_boundary and abs(sgn * v.co.x - XCUT) < 1e-3]
    b = [v for v in bm.verts if v[mark] and v[lay] == 0 and v.is_boundary and abs(sgn * v.co.x - XCUT) < 1e-3]
    print('RINGS', sgn, len(a), len(b))
    for u in a: tm[u] = min(b, key=lambda q: (q.co - u.co).length_squared)
bmesh.ops.weld_verts(bm, targetmap=tm)
for v in bm.verts: v[mark] = 1
bpy.data.objects.remove(vx)
bm.verts.ensure_lookup_table()


def loops(edges):
    edges = set(edges); out = []
    while edges:
        st = [edges.pop()]; cur = {st[0]}
        while st:
            e = st.pop()
            for v in e.verts:
                for f in v.link_edges:
                    if f in edges: edges.remove(f); cur.add(f); st.append(f)
        out.append(list(cur))
    return sorted(out, key=len, reverse=True)


# neck tube: from the body's ring up into the skull
ZT = 0.745
neck_c = lambda z: float(np.interp(z, (0.58, 0.70, ZT), (-0.045, 0.02, 0.04)))
neck_ab = lambda z: (float(np.interp(z, (0.58, ZT), (0.105, 0.092))), float(np.interp(z, (0.58, 0.68, ZT), (0.095, 0.098, 0.10))))
for nm, ob in parts.items():
    t = bmesh.new(); t.from_mesh(ob.data)
    if nm == 'Face':
        bmesh.ops.holes_fill(t, edges=[e for e in t.edges if e.is_boundary and sum(1 for x in e.verts) == 2], sides=30)
        # below the jaw line only the old hair skirt's shell is left: it goes, a clean neck tube stands inside. The edge is drawn in under the jaw so skin meets skin
        zj = lambda y: float(np.interp(y, (-0.06, 0.02, 0.08), (0.60, 0.69, 0.725)))
        bmesh.ops.delete(t, geom=[v for v in t.verts if v.co.z < zj(v.co.y) or (abs(v.co.x) > 0.122 and v.co.z < 0.765)], context='VERTS')
        for _ in range(14):
            mv = {}
            for v in t.verts:
                if v.is_boundary:
                    nb = [e.other_vert(v) for e in v.link_edges if e.is_boundary]
                    if len(nb) == 2: mv[v] = (nb[0].co + nb[1].co) * 0.5
            for v, c in mv.items(): v.co = v.co * 0.45 + c * 0.55
        for v in t.verts:
            w = float(np.clip((zj(v.co.y) + 0.035 - v.co.z) / 0.035, 0, 1)); w = w * w * (3 - 2 * w)
            if w == 0: continue
            yc = neck_c(v.co.z); a_, b_ = neck_ab(v.co.z)
            e_ = float(np.hypot(v.co.x / a_, (v.co.y - yc) / b_))
            k_ = 1 + (0.96 / max(e_, 1e-3) - 1) * w
            if e_ > 0.96: v.co.x *= k_; v.co.y = yc + (v.co.y - yc) * k_
        t.verts.ensure_lookup_table()
        seen = set(); comps_ = []
        for v in t.verts:
            if v in seen: continue
            st = [v]; seen.add(v); cc = [v]
            while st:
                x_ = st.pop()
                for e in x_.link_edges:
                    y_ = e.other_vert(x_)
                    if y_ not in seen: seen.add(y_); st.append(y_); cc.append(y_)
            comps_.append(cc)
        comps_.sort(key=len, reverse=True)
        print('FACE comps', [len(c) for c in comps_[:8]])
        for c in comps_[1:]:
            bmesh.ops.delete(t, geom=c, context='VERTS')
    if nm == 'Hair':
        # narrower at the bottom, longer, lying on the back as in MM9
        for v in t.verts:
            x, y, z = v.co
            k = 1 - 0.42 * float(np.clip((0.76 - z) / 0.21, 0, 1))
            if z < 0.66:
                dz = 0.66 - z
                z = 0.66 - dz * 2.1
            yo = y - 0.06 * float(np.clip((0.72 - v.co.z) / 0.17, 0, 1)) ** 1.0
            yo -= 0.016 * float(np.clip((v.co.z - 0.74) / 0.09, 0, 1))     # the top goes in under the skull's skin
            v.co = Vector((x * k, yo, z))
        bmesh.ops.delete(t, geom=[v for v in t.verts if v.co.y < 0.03 + 0.25 * max(0, 0.72 - v.co.z)], context='VERTS')
    tm = bpy.data.meshes.new('t'); t.to_mesh(tm); t.free()
    bm.from_mesh(tm)
    for v in bm.verts:
        if not v[mark]: v[lay] = pid[nm]; v[mark] = 1
    bpy.data.meshes.remove(tm)
bm.verts.ensure_lookup_table()
near = lambda e: all(abs(sdist(v.co)) < 4e-3 for v in e.verts)
body_ring = loops([e for e in bm.edges if e.is_boundary and e.verts[0][lay] == 0 and near(e)])
print('body loops', [len(l) for l in body_ring]); body_ring = body_ring[0]
bv = list({v for e in body_ring for v in e.verts})
Bp = np.array([v.co[:] for v in bv])
print('rings body', len(bv), Bp.min(0).round(3), Bp.max(0).round(3))
cb = 0.5 * (Bp.min(0) + Bp.max(0))
N = 36; NR_ = 7
ang = np.arctan2(Bp[:, 1] - cb[1], Bp[:, 0] - cb[0]); o_ = np.argsort(ang)
aa = np.r_[ang[o_] - 2 * np.pi, ang[o_], ang[o_] + 2 * np.pi]
def ring_pt(c):
    rr = np.hypot(Bp[:, 0] - cb[0], Bp[:, 1] - cb[1])[o_]; zz = Bp[:, 2][o_]
    return np.interp(c, aa, np.r_[rr, rr, rr]), np.interp(c, aa, np.r_[zz, zz, zz])
rows = []
for r_ in range(NR_):
    t = (r_ + 1) / NR_
    row = []
    for i in range(N):
        c = -np.pi + 2 * np.pi * i / N
        r0, z0 = ring_pt(c)
        z_e = float(np.interp(t, (0, 1), (0.60, ZT))) + 0.04 * np.sin(c) * (1 - t)
        yc = neck_c(z_e); a_, b_ = neck_ab(z_e)
        p0 = np.array([cb[0] + r0 * np.cos(c), cb[1] + r0 * np.sin(c), z0])
        p1 = np.array([a_ * np.cos(c), yc + b_ * np.sin(c), z_e])
        tt = float(min(1, t * 2.2)); tt = tt * tt * (3 - 2 * tt)
        p = p0 * (1 - tt) + p1 * tt
        v = bm.verts.new(tuple(p)); v[lay] = 0; v[mark] = 1
        if abs(p[0]) < 1e-5: v.co.x = 0
        row.append(v)
    rows.append(row)
for r_ in range(NR_ - 1):
    for i in range(N):
        j = (i + 1) % N
        bm.faces.new([rows[r_][i], rows[r_][j], rows[r_ + 1][j], rows[r_ + 1][i]])
first = [e for i in range(N) for e in rows[0][i].link_edges if e.other_vert(rows[0][i]) is rows[0][(i + 1) % N]]
ret = bmesh.ops.bridge_loops(bm, edges=body_ring + first)
print('BRIDGE faces', len(ret['faces']))
band = set(bv)
for _ in range(2):
    band |= {e.other_vert(v) for v in band for e in v.link_edges}
for _ in range(10):
    mv = {}
    for v in band:
        if v[lay] != 0: continue
        nb = [e.other_vert(v).co for e in v.link_edges]
        mv[v] = sum(nb, Vector()) / len(nb)
    for v, c in mv.items():
        x0 = v.co.x
        v.co = v.co * 0.45 + c * 0.55
        if abs(x0) < 1e-5: v.co.x = 0
bmesh.ops.recalc_face_normals(bm, faces=[f for f in bm.faces if all(v[lay] == 0 for v in f.verts)])
bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
# ---- clean flaps: outline from MM9, surface a low polynomial through Meshy's sheet, off the skin by a small margin. The lining is added at export
from mathutils.bvhtree import BVHTree
skinv = [v for v in bm.verts if v[lay] in (0,)]
sf = [f for f in bm.faces if all(v[lay] == 0 for v in f.verts)]
idx = {v: i for i, v in enumerate(skinv)}
tree = BVHTree.FromPolygons([tuple(v.co) for v in skinv], [tuple(idx[v] for v in f.verts) for f in sf])
W_OUT = {6: [(0.0, 0.135), (0.25, 0.125), (0.55, 0.075), (0.8, 0.032), (1.0, 0.0)], 7: [(0.0, 0.125), (0.25, 0.115), (0.55, 0.075), (0.8, 0.03), (1.0, 0.0)]}
ZTOP = {6: 0.135, 7: 0.135}; ZTIP = {6: -0.31, 7: -0.31}
NC, NR = 7, 10
flap_faces = {}
for pid_, sign in ((6, -1), (7, 1)):
    q = SHEET[pid_]; q = q[q[:, 2] < 0.10]
    X = np.c_[np.ones(len(q)), q[:, 2], q[:, 2] ** 2, q[:, 0] ** 2]
    co, *_ = np.linalg.lstsq(X, q[:, 1], rcond=None)
    gridv = {}
    for r in range(NR + 1):
        t = r / NR
        z = ZTOP[pid_] + (ZTIP[pid_] - ZTOP[pid_]) * t
        w = float(np.interp(t, *zip(*W_OUT[pid_])))
        for c in range(NC + 1):
            if r == NR and c != NC // 2: continue
            u = (c / NC) * 2 - 1
            x = u * w
            y = float(co @ np.array([1, z, z * z, x * x]))
            # off the skin
            o = Vector((x, sign * 0.4, z)); h = tree.ray_cast(o, Vector((0, -sign, 0)), 0.6)
            if h[0] is not None:
                ys = h[0].y
                y = (min(y, ys - 0.006) if sign < 0 else max(y, ys + 0.006))
            v = bm.verts.new((x, y, z)); v[lay] = pid_; v[mark] = 1; gridv[(r, c)] = v
    mid = NC // 2
    for r in range(NR):
        for c in range(NC):
            a, b, c_, d = gridv.get((r, c)), gridv.get((r, c + 1)), gridv.get((r + 1, c + 1)), gridv.get((r + 1, c))
            if r == NR - 1:
                tip = gridv[(NR, mid)]
                bm.faces.new([a, b, tip] if sign < 0 else [b, a, tip])
                continue
            if sign < 0:
                bm.faces.new([a, b, c_]); bm.faces.new([a, c_, d])
            else:
                bm.faces.new([b, a, c_]); bm.faces.new([a, d, c_])
    print('FLAP', pid_, 'poly', np.round(co, 3).tolist())
# ---- belt plate, a shallow disc on the belt's front
pc = np.array([0.0, -0.1, 0.302]); hit = tree.ray_cast(Vector((0, -0.4, pc[2])), Vector((0, 1, 0)), 0.6)
y0 = hit[0].y
RD = 0.052
rings_ = [(0.0, -0.0075), (0.55, -0.007), (0.86, -0.0045), (1.0, 0.002)]
vs_ = []
for rk, off in rings_:
    n_ = 1 if rk == 0 else 20
    row = []
    for i in range(n_):
        a = 2 * np.pi * i / n_
        x, z = RD * rk * np.cos(a), pc[2] + RD * rk * np.sin(a)
        h = tree.ray_cast(Vector((x, -0.4, z)), Vector((0, 1, 0)), 0.6)
        v = bm.verts.new((x, h[0].y + off, z)); v[lay] = 3; v[mark] = 1; row.append(v)
    vs_.append(row)
for i in range(20):
    j = (i + 1) % 20
    bm.faces.new([vs_[0][0], vs_[1][i], vs_[1][j]][::-1])
    for r in (1, 2):
        bm.faces.new([vs_[r][i], vs_[r + 1][i], vs_[r + 1][j], vs_[r][j]][::-1])
bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
bm.verts.layers.int.remove(mark)
bm.to_mesh(body.data); bm.free()
for p in body.data.polygons: p.use_smooth = True
for o in list(bpy.data.objects):
    if o is not body: bpy.data.objects.remove(o)
c = np.array([v.co[:] for v in body.data.vertices])
print('FINAL verts', len(c), 'tris', sum(len(p.vertices) - 2 for p in body.data.polygons), 'bbox', c.min(0).round(3), c.max(0).round(3))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
