"""Step B: head-only Meshy parts on the posed body. Body and Face are cut on one tilted plane across the neck, the face's neck conforms to the body's ring and they are bridged, so the skin is one
connected shell. Hair and Eyes go in as parts (11, 13). The collar (part 6) is refitted round the neck on a lower tilted plane.
Args: <pose blend> <head blend> <out blend>"""
import bpy, bmesh, sys, json
import numpy as np
from mathutils import Vector
POSE, HEAD, OUT = sys.argv[sys.argv.index('--') + 1:]
OFF = np.array([0.008, -0.236, 0.77])
C = np.array([0.0, -0.205, 0.655]); N = np.array([0.0, -0.62, 0.785]); N /= np.linalg.norm(N)
HB, HF = 0.08, 0.02         # body cut, final ring: along N from C
C2 = C + N * 0.02
U = np.array([1.0, 0, 0]); V = np.cross(N, U)
bpy.ops.wm.open_mainfile(filepath=POSE)
body = bpy.data.objects['Body']
with bpy.data.libraries.load(HEAD) as (src, dst):
    dst.objects = [n for n in src.objects]
parts = {o.name: o for o in dst.objects}
pid = {'Face': 10, 'Hair': 11, 'Eyes': 13}
bm = bmesh.new(); bm.from_mesh(body.data)
lay = bm.verts.layers.int['part']
# body: everything of part 0 beyond the plane goes; part 0 has no faces there but the neck
vs = [v for v in bm.verts if v[lay] == 0]; es = list({e for v in vs for e in v.link_edges}); fs = list({f for v in vs for f in v.link_faces})
bmesh.ops.bisect_plane(bm, geom=vs + es + fs, plane_co=C + N * HB, plane_no=N, clear_outer=True)
# Meshy's trapezius stands high: the neck ring at HB comes down to HF, the shoulders' slope with it
for v in bm.verts:
    if v[lay] != 0: continue
    p = np.array(v.co[:]); h = (p - C) @ N
    if h < -0.07: continue
    t = np.clip((h + 0.07) / (HB + 0.07), 0, 1); t = t * t * (3 - 2 * t)
    fx = np.clip((0.34 - abs(p[0])) / 0.25, 0, 1); fx = fx * fx * (3 - 2 * fx)
    v.co = Vector(p - N * (HB - HF) * t * fx)
hh_ = np.array([(np.array(v.co[:]) - C) @ N for v in bm.verts]); print('RINGS beyond', int((hh_ > 0.001).sum()), 'near', int((np.abs(hh_) < 0.001).sum()), 'part0 boundary now', sum(1 for e in bm.edges if e.is_boundary))
for nm, ob in parts.items():
    t = bmesh.new(); t.from_mesh(ob.data)
    for v in t.verts: v.co += Vector(OFF)
    if nm == 'Face':
        bmesh.ops.bisect_plane(t, geom=list(t.verts) + list(t.edges) + list(t.faces), plane_co=C + N * HF, plane_no=N, clear_inner=True)
    tl = t.verts.layers.int.new('part')
    for v in t.verts: v[tl] = pid[nm]
    tm = bpy.data.meshes.new('t'); t.to_mesh(tm); t.free()
    bm.from_mesh(tm)
    lay = bm.verts.layers.int['part']
    bpy.data.meshes.remove(tm)
bm.verts.ensure_lookup_table()
def on_plane(v): return abs((np.array(v.co[:]) - C) @ N - HF) < 0.0015
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
bd = [e for e in bm.edges if e.is_boundary]
print('RINGS dbg', len(bd), {k: sum(1 for e in bd if e.verts[0][lay] == k) for k in (0, 1, 3, 5, 6, 10, 11, 13)}, [np.round(np.array(e.verts[0].co[:]), 3).tolist() for e in bd if e.verts[0][lay] == 0][:6], [round(float((np.array(e.verts[0].co[:]) - C) @ N), 4) for e in bd if e.verts[0][lay] == 0][:6])
from collections import Counter
print('RINGS onplane', Counter((e.verts[0][lay], e.verts[1][lay]) for e in bm.edges if on_plane(e.verts[0]) and on_plane(e.verts[1]) and e.is_boundary), Counter(v[lay] for v in bm.verts if on_plane(v)))
rb = loops([e for e in bm.edges if e.is_boundary and e.verts[0][lay] == 0 and on_plane(e.verts[0]) and on_plane(e.verts[1])])
rf = loops([e for e in bm.edges if e.is_boundary and e.verts[0][lay] == 10 and on_plane(e.verts[0]) and on_plane(e.verts[1])])
print('RINGS body', [len(l) for l in rb], 'face', [(len(l), np.round(np.mean([v.co[:] for e in l for v in e.verts], 0), 3).tolist()) for l in rf])
body_ring, face_ring = rb[0], rf[0]
bv = list({v for e in body_ring for v in e.verts}); fv = list({v for e in face_ring for v in e.verts})
B = np.array([v.co[:] for v in bv]); F = np.array([v.co[:] for v in fv])
def plane2(Q, o=C): return np.c_[(Q - o) @ U, (Q - o) @ V]
b2, f2 = plane2(B), plane2(F)
cb = 0.5 * (b2.min(0) + b2.max(0)); cf = 0.5 * (f2.min(0) + f2.max(0))
print('RING body c', np.round(cb, 3), 'ext', np.round(np.ptp(b2, 0), 3), 'face c', np.round(cf, 3), 'ext', np.round(np.ptp(f2, 0), 3))
def polar(q, c):
    a = np.arctan2(q[:, 1] - c[1], q[:, 0] - c[0]); r = np.hypot(q[:, 1] - c[1], q[:, 0] - c[0]); o = np.argsort(a)
    return a[o], r[o]
ab, rb_ = polar(b2, cb); af, rf_ = polar(f2, cf)
FALL = 0.05
for v in bm.verts:
    if v[lay] != 10: continue
    p = np.array(v.co[:]); h = (p - C) @ N - HF
    if h > FALL: continue
    w = 1 - h / FALL; w = w * w * (3 - 2 * w)
    q = plane2(p[None])[0]
    a = np.arctan2(q[1] - cf[1], q[0] - cf[0]); r = np.hypot(q[1] - cf[1], q[0] - cf[0])
    r1 = np.interp(a, np.r_[ab - 2 * np.pi, ab, ab + 2 * np.pi], np.r_[rb_, rb_, rb_]); r0 = np.interp(a, np.r_[af - 2 * np.pi, af, af + 2 * np.pi], np.r_[rf_, rf_, rf_])
    t = cb + np.array([np.cos(a), np.sin(a)]) * r * r1 / max(r0, 1e-4)
    nq = q + (t - q) * w
    v.co = Vector(C + U * nq[0] + V * nq[1] + N * (h + HF))
for v in bm.verts:
    if v[lay] == 10:
        pass
ret = bmesh.ops.bridge_loops(bm, edges=body_ring + face_ring)
print('BRIDGE faces', len(ret['faces']))
# the seam and the ragged shoulder-neck band relax into one smooth neck
nv_ = [v for v in bm.verts if v[lay] in (0, 10) and abs((np.array(v.co[:]) - C) @ N - HF) < 0.045 and abs(v.co.x) < 0.16]
for _ in range(10):
    mv = {}
    for v in nv_:
        h = abs((np.array(v.co[:]) - C) @ N - HF); w = 0.65 * min(1.0, (0.045 - h) / 0.015)
        nb = [e.other_vert(v).co for e in v.link_edges]
        mv[v] = (sum(nb, Vector()) / len(nb), w)
    for v, (c, w) in mv.items(): v.co = v.co * (1 - w) + c * w
# collar on the lower plane
col = [v for v in bm.verts if v[lay] == 6]
Qc = np.array([v.co[:] for v in col]); c0 = Qc.mean(0)
Us, Ss, Vt = np.linalg.svd(Qc - c0); n0 = Vt[2] if Vt[2] @ N > 0 else -Vt[2]; u0 = Vt[0] if Vt[0][0] > 0 else -Vt[0]
print('COLLAR axes', np.round(Vt, 2).tolist(), 'S', np.round(Ss, 2))
v0 = np.cross(n0, u0)
l2 = np.c_[(Qc - c0) @ u0, (Qc - c0) @ v0, (Qc - c0) @ n0]
cl = 0.5 * (l2.min(0) + l2.max(0))
cn = cb; ex = np.ptp(b2, 0)
TUBE = 0.03
print('COLLAR ext', np.round(np.ptp(l2, 0), 3), 'neck', np.round(ex, 3))
sx = (ex[0] + TUBE) / np.ptp(l2[:, 0]); sy = (ex[1] + TUBE) / np.ptp(l2[:, 1])
for v, p in zip(col, l2):
    q = (p - cl) * [sx, sy, 1.0]
    w = C2 + U * (cn[0] + q[0]) + V * (cn[1] + q[1]) + N * q[2]
    v.co = Vector(w)
bm.to_mesh(body.data); bm.free()
for p in body.data.polygons: p.use_smooth = True
for o in list(bpy.data.objects):
    if o is not body: bpy.data.objects.remove(o)
c = np.array([v.co[:] for v in body.data.vertices])
print('FINAL verts', len(c), 'tris', sum(len(p.vertices) - 2 for p in body.data.polygons), 'bbox', c.min(0).round(3), c.max(0).round(3))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
