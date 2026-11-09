"""Head-only Meshy parts on the body. Meshy's body neck (part 2) is a mess behind the collar, but its front fills the V of the mantle. So it goes, and the new neck runs on down in rings: front half on the old surface (it carries the bare V),
back half an ellipse under the collar. Helmet and eyes go in as parts 21, 22; face and neck are part 20. Args: <fit blend> <head blend> <out blend>"""
import bpy, bmesh, sys, os
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
POSE, HEAD, OUT = sys.argv[sys.argv.index('--') + 1:]
SC = float(os.environ.get('HEAD_S', 0.345)) / 0.31                # MM9's head is large on this body (chin 0.65, top 1.035): a compromise between the sculpt's proportions and MM9's mass
TOP = 1.03
OFF = np.array([0.0, float(os.environ.get('HEAD_Y', -0.007)), TOP - 0.155 * SC])
ZC = OFF[2] - 0.146 * SC
ZR = [ZC - 0.012 - 0.014 * k for k in range(7)]
NR = 28
bpy.ops.wm.open_mainfile(filepath=POSE)
body = bpy.data.objects['Body']
with bpy.data.libraries.load(HEAD) as (src, dst):
    dst.objects = [n for n in src.objects]
parts = {o.name: o for o in dst.objects}
pid = {'Face': 20, 'Helm': 21, 'Eyes': 22}
bm = bmesh.new(); bm.from_mesh(body.data)
lay = bm.faces.layers.int['part']
fs = [f for f in bm.faces if f[lay] == 2]
ot = bmesh.new(); vm = {}
for v in {v for f in fs for v in f.verts}: vm[v] = ot.verts.new(v.co)
for f in fs:
    try: ot.faces.new([vm[v] for v in f.verts])
    except ValueError: pass
ot.verts.ensure_lookup_table(); ot.faces.ensure_lookup_table()
bo = BVHTree.FromBMesh(ot)
bmesh.ops.delete(bm, geom=fs, context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
bm.faces.ensure_lookup_table()
for nm, ob in parts.items():
    t = bmesh.new(); t.from_mesh(ob.data)
    for v in t.verts: v.co = v.co * SC + Vector(OFF)
    if nm == 'Face':
        bmesh.ops.bisect_plane(t, geom=list(t.verts) + list(t.edges) + list(t.faces), plane_co=(0, 0, ZC), plane_no=(0, 0, 1), clear_inner=True)
    tl = t.faces.layers.int.new('part')
    for f in t.faces: f[tl] = pid[nm]
    tm = bpy.data.meshes.new('t'); t.to_mesh(tm); t.free()
    bm.from_mesh(tm)
    bpy.data.meshes.remove(tm)
lay = bm.faces.layers.int['part']
bm.verts.ensure_lookup_table(); bm.edges.ensure_lookup_table()
ring = {v for e in bm.edges if e.is_boundary and e.link_faces[0][lay] == 20 for v in e.verts if abs(v.co.z - ZC) < 0.0012}
bmesh.ops.remove_doubles(bm, verts=list(ring), dist=0.002)
bm.verts.ensure_lookup_table(); bm.edges.ensure_lookup_table()
edges = [e for e in bm.edges if e.is_boundary and e.link_faces[0][lay] == 20 and all(abs(v.co.z - ZC) < 0.0012 for v in e.verts)]
ring = list({v for e in edges for v in e.verts})
R = np.array([v.co[:] for v in ring])
cx, cy = 0.0, 0.5 * (R[:, 1].min() + R[:, 1].max())
ang = np.arctan2(R[:, 1] - cy, R[:, 0] - cx); o = np.argsort(ang)
ring = [ring[i] for i in o]; ang = ang[o]; rad = np.hypot(R[o, 0], R[o, 1] - cy)
print('RING', len(ring), 'edges', len(edges), 'c', round(float(cy), 3), 'x', np.round(R[:, 0].max(), 3), 'y', np.round([R[:, 1].min(), R[:, 1].max()], 3))
A = -np.pi + (np.arange(NR) + 0.5) * 2 * np.pi / NR          # symmetric about x = 0 by construction: pairs mirrored below
r0 = np.interp(A, np.r_[ang - 2 * np.pi, ang, ang + 2 * np.pi], np.r_[rad, rad, rad])
r0 = 0.5 * (r0 + np.interp(np.pi - A, np.r_[A - 2 * np.pi, A, A + 2 * np.pi], np.r_[r0, r0, r0]))
rings = []
prev = r0.copy()
for k, z in enumerate(ZR):
    yc = cy + (0.012 - cy) * min(1.0, (ZC - z) / 0.04)
    w = np.clip((ZC - z) / 0.05, 0, 1); w = w * w * (3 - 2 * w)
    cur = np.zeros(NR)
    for i, a in enumerate(A):
        d = Vector((np.cos(a), np.sin(a), 0)); front = np.sin(a) < 0.15
        base = 0.062 if not front else prev[i]
        rr = base
        if front:
            loc, *_ = bo.ray_cast(Vector((0, yc, z)) + d * 0.2, -d, 0.2)
            if loc is not None:
                rr = (loc - Vector((0, yc, z))).length - 0.001
        cur[i] = prev[i] * (1 - w) + rr * w if front else 0.6 * prev[i] + 0.4 * base
    s = 0.25 * np.roll(cur, 1) + 0.5 * cur + 0.25 * np.roll(cur, -1)
    s = 0.5 * (s + np.interp(np.pi - A, np.r_[A - 2 * np.pi, A, A + 2 * np.pi], np.r_[s, s, s]))
    prev = s
    rings.append([bm.verts.new((s[i] * np.cos(A[i]), yc + s[i] * np.sin(A[i]), z)) for i in range(NR)])
    print('RING', round(z, 3), 'front y', round(float(yc - s[np.argmin(np.abs(A + np.pi / 2))]), 3), 'x', round(float(s[np.argmin(np.abs(A))]), 3))
bm.verts.ensure_lookup_table()
new = []
for a_, b_ in zip(rings[:-1], rings[1:]):
    for i in range(NR):
        k = (i + 1) % NR
        new += [bm.faces.new((a_[i], a_[k], b_[k])), bm.faces.new((a_[i], b_[k], b_[i]))]
# stitch by angle
aa, ab = A, ang; A_, B_ = rings[0], ring; na, nb = len(A_), len(B_); i = j = 0
while i < na or j < nb:
    ni = aa[(i + 1) % na] + (2 * np.pi if i + 1 >= na else 0); nj = ab[(j + 1) % nb] + (2 * np.pi if j + 1 >= nb else 0)
    if j >= nb or (i < na and ni <= nj):
        tri = (A_[i % na], A_[(i + 1) % na], B_[j % nb]); i += 1
    else:
        tri = (A_[i % na], B_[(j + 1) % nb], B_[j % nb]); j += 1
    if len(set(tri)) == 3:
        try: new.append(bm.faces.new(tri))
        except ValueError: pass
for f in new: f[lay] = 20; f.smooth = True
print('BRIDGE faces', len(new))
bmesh.ops.recalc_face_normals(bm, faces=[f for f in bm.faces if f[lay] == 20])
bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
# the seam relaxes
nv_ = [v for v in {v for f in bm.faces if f[lay] == 20 for v in f.verts} if abs(v.co.z - ZC) < 0.03 and not v.is_boundary and np.hypot(v.co.x, v.co.y - cy) < 0.09]
for _ in range(6):
    mv = {}
    for v in nv_:
        nb = [e.other_vert(v).co for e in v.link_edges]
        mv[v] = sum(nb, Vector()) / len(nb)
    for v, c in mv.items(): v.co = v.co * 0.5 + c * 0.5
bm.to_mesh(body.data); bm.free(); ot.free()
for p in body.data.polygons: p.use_smooth = True
for o_ in list(bpy.data.objects):
    if o_.type == 'MESH' and o_ is not body: bpy.data.objects.remove(o_)
c = np.array([v.co[:] for v in body.data.vertices])
print('FINAL verts', len(c), 'tris', sum(len(p.vertices) - 2 for p in body.data.polygons), 'bbox', c.min(0).round(3), c.max(0).round(3))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
