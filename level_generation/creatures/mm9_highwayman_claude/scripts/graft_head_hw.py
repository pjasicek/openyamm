"""Head-only Meshy parts on the body (from mm9_thrall_claude/scripts/graft_thrall.py). The old neck (part 2, Meshy's own, it carries the bare V of the chest under the collar) and the new face are cut on one tilted
plane across the neck, the face's neck conforms to the old ring and they are bridged, so the skin is one shell. Hair and eyes go in as parts 21, 22; the face is part 20.
Args: <fit blend> <head blend> <out blend>"""
import bpy, bmesh, sys
import numpy as np
from mathutils import Vector
POSE, HEAD, OUT = sys.argv[sys.argv.index('--') + 1:]
OFF = np.array([0.0, 0.012, 0.777])
C = np.array([0.0, -0.03, 0.668]); N = np.array([0.0, -0.45, 0.893]); N /= np.linalg.norm(N)
U = np.array([1.0, 0, 0]); V = np.cross(N, U)
bpy.ops.wm.open_mainfile(filepath=POSE)
body = bpy.data.objects['Body']
with bpy.data.libraries.load(HEAD) as (src, dst):
    dst.objects = [n for n in src.objects]
parts = {o.name: o for o in dst.objects}
pid = {'Face': 20, 'Hair': 21, 'Eyes': 22}
bm = bmesh.new(); bm.from_mesh(body.data)
lay = bm.faces.layers.int['part']
fs = [f for f in bm.faces if f[lay] == 2]; vs = list({v for f in fs for v in f.verts}); es = list({e for f in fs for e in f.edges})
bmesh.ops.bisect_plane(bm, geom=vs + es + fs, plane_co=C, plane_no=N, clear_outer=True)
bm.faces.ensure_lookup_table()
for nm, ob in parts.items():
    t = bmesh.new(); t.from_mesh(ob.data)
    for v in t.verts: v.co += Vector(OFF)
    if nm == 'Face':
        bmesh.ops.bisect_plane(t, geom=list(t.verts) + list(t.edges) + list(t.faces), plane_co=C, plane_no=N, clear_inner=True)
    tl = t.faces.layers.int.new('part')
    for f in t.faces: f[tl] = pid[nm]
    tm = bpy.data.meshes.new('t'); t.to_mesh(tm); t.free()
    bm.from_mesh(tm)
    bpy.data.meshes.remove(tm)
lay = bm.faces.layers.int['part']
bm.verts.ensure_lookup_table()
def on_plane(v): return abs((np.array(v.co[:]) - C) @ N) < 0.0015
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
def part_of(e): return e.link_faces[0][lay]
fring = {v for f in bm.faces if f[lay] == 20 for v in f.verts if on_plane(v)}
bmesh.ops.remove_doubles(bm, verts=list(fring), dist=0.003)
bm.edges.ensure_lookup_table(); bm.verts.ensure_lookup_table()
bd = [e for e in bm.edges if e.is_boundary and on_plane(e.verts[0]) and on_plane(e.verts[1])]
rb = loops([e for e in bd if part_of(e) == 2]); rf = loops([e for e in bd if part_of(e) == 20])
print('RINGS old neck', [len(l) for l in rb], 'face', [len(l) for l in rf])
body_ring, face_ring = rb[0], rf[0]
bv = list({v for e in body_ring for v in e.verts}); fv = list({v for e in face_ring for v in e.verts})
B = np.array([v.co[:] for v in bv]); F = np.array([v.co[:] for v in fv])
def plane2(Q, o=C): return np.c_[(Q - o) @ U, (Q - o) @ V]
b2, f2 = plane2(B), plane2(F)
cb = 0.5 * (b2.min(0) + b2.max(0)); cf = 0.5 * (f2.min(0) + f2.max(0))
print('RING neck c', np.round(cb, 3), 'ext', np.round(np.ptp(b2, 0), 3), 'face c', np.round(cf, 3), 'ext', np.round(np.ptp(f2, 0), 3))
def polar(q, c):
    a = np.arctan2(q[:, 1] - c[1], q[:, 0] - c[0]); r = np.hypot(q[:, 1] - c[1], q[:, 0] - c[0]); o = np.argsort(a)
    return a[o], r[o]
ab, rb_ = polar(b2, cb); af, rf_ = polar(f2, cf)
FALL = 0.05
faceverts = {v for f in bm.faces if f[lay] == 20 for v in f.verts}
for v in faceverts:
    p = np.array(v.co[:]); h = (p - C) @ N
    if h > FALL: continue
    w = 1 - h / FALL; w = w * w * (3 - 2 * w)
    q = plane2(p[None])[0]
    a = np.arctan2(q[1] - cf[1], q[0] - cf[0]); r = np.hypot(q[1] - cf[1], q[0] - cf[0])
    r1 = np.interp(a, np.r_[ab - 2 * np.pi, ab, ab + 2 * np.pi], np.r_[rb_, rb_, rb_]); r0 = np.interp(a, np.r_[af - 2 * np.pi, af, af + 2 * np.pi], np.r_[rf_, rf_, rf_])
    t = cb + np.array([np.cos(a), np.sin(a)]) * r * r1 / max(r0, 1e-4)
    nq = q + (t - q) * w
    v.co = Vector(C + U * nq[0] + V * nq[1] + N * h)
# stitch by angle round the neck (the two rings differ in count and the seam vertices can branch)
def ordered(vs_):
    q = plane2(np.array([v.co[:] for v in vs_])); c = 0.5 * (q.min(0) + q.max(0))
    a = np.arctan2(q[:, 1] - c[1], q[:, 0] - c[0]); o = np.argsort(a)
    return [vs_[i] for i in o], a[o]
A_, aa = ordered(bv); B_, ab2 = ordered(list({v for e in face_ring for v in e.verts}))
na, nb = len(A_), len(B_); i = j = 0; new = []
while i < na or j < nb:
    ai = aa[i % na] + (2 * np.pi if i >= na else 0); ni = aa[(i + 1) % na] + (2 * np.pi if i + 1 >= na else 0)
    bj = ab2[j % nb] + (2 * np.pi if j >= nb else 0); nj = ab2[(j + 1) % nb] + (2 * np.pi if j + 1 >= nb else 0)
    if j >= nb or (i < na and ni <= nj):
        tri = (A_[i % na], A_[(i + 1) % na], B_[j % nb]); i += 1
    else:
        tri = (A_[i % na], B_[(j + 1) % nb], B_[j % nb]); j += 1
    if len(set(tri)) == 3:
        try: new.append(bm.faces.new(tri))
        except ValueError: pass
print('BRIDGE faces', len(new))
for f in new: f[lay] = 20; f.smooth = True
bmesh.ops.recalc_face_normals(bm, faces=[f for f in bm.faces if f[lay] in (2, 20)])
bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
# the seam relaxes into one smooth neck
skin = {v for f in bm.faces if f[lay] in (2, 20) for v in f.verts}
nv_ = [v for v in skin if abs((np.array(v.co[:]) - C) @ N) < 0.03]
for _ in range(10):
    mv = {}
    for v in nv_:
        h = abs((np.array(v.co[:]) - C) @ N); w = 0.6 * min(1.0, (0.03 - h) / 0.012)
        nb = [e.other_vert(v).co for e in v.link_edges]
        mv[v] = (sum(nb, Vector()) / len(nb), w)
    for v, (c, w) in mv.items(): v.co = v.co * (1 - w) + c * w
bm.to_mesh(body.data); bm.free()
for p in body.data.polygons: p.use_smooth = True
for o in list(bpy.data.objects):
    if o.type == 'MESH' and o is not body: bpy.data.objects.remove(o)
c = np.array([v.co[:] for v in body.data.vertices])
print('FINAL verts', len(c), 'tris', sum(len(p.vertices) - 2 for p in body.data.polygons), 'bbox', c.min(0).round(3), c.max(0).round(3))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
