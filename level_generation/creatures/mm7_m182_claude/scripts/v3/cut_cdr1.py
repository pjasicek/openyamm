"""Cut the cdr1 head off at a neck plane (Blender bmesh bisect: straddling triangles are split exactly on the plane,
UVs and vertex weights interpolated, so the ring is planar without moving any vertex). Only the main surface near
the neck is bisected; separate pieces (horns, teeth, spikes) whose centre lies beyond the plane are deleted whole.
Usage: blender -b work/v3/src.blend -P cut_cdr1.py -- cx,cy,cz nx,ny,nz <out.blend>"""
import bpy, bmesh, sys
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
c0 = Vector([float(v) for v in a[0].split(',')]); n0 = Vector([float(v) for v in a[1].split(',')]).normalized()
o = bpy.data.objects['Body']; me = o.data
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
# components
comp = {}; cid = 0
for v in bm.verts:
    if v in comp: continue
    stack = [v]; comp[v] = cid
    while stack:
        x = stack.pop()
        for e in x.link_edges:
            y = e.other_vert(x)
            if y not in comp: comp[y] = cid; stack.append(y)
    cid += 1
sizes = {}
for v, c in comp.items(): sizes[c] = sizes.get(c, 0) + 1
main = max(sizes, key=sizes.get)
pieces = {}
for v, c in comp.items():
    if c != main: pieces.setdefault(c, []).append(v)
dead = []
for c, vs in pieces.items():
    cen = sum((v.co for v in vs), Vector()) / len(vs)
    if (cen - c0).dot(n0) > 0 and (cen - c0).length < 0.8: dead += vs
bmesh.ops.delete(bm, geom=dead, context='VERTS')
near = [f for f in bm.faces if all(comp.get(v) == main for v in f.verts) and min((v.co - c0).length for v in f.verts) < 0.6]
geom = list({v for f in near for v in f.verts}) + list({e for f in near for e in f.edges}) + near
# snap vertices lying within SNAP of the plane onto it, so the bisect ring runs through them instead of leaving
# millimetre slivers next to them (they stretched 3x in Attack)
SNAP = 0.012
snapped = 0
for v in {v for f in near for v in f.verts}:
    d = (v.co - c0).dot(n0)
    if abs(d) < SNAP: v.co -= n0 * d; snapped += 1
res = bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-6, plane_co=c0, plane_no=n0, clear_outer=True)
# anything still beyond (disconnected leftovers of the head) goes
bm.verts.ensure_lookup_table()
left = [v for v in bm.verts if (v.co - c0).dot(n0) > 1e-5 and (v.co - c0).length < 0.8]
bmesh.ops.delete(bm, geom=left, context='VERTS')
loose = [v for v in bm.verts if not v.link_faces]; bmesh.ops.delete(bm, geom=loose, context='VERTS')
# merge very short edges of the planar cut ring (bisect leaves millimetre edges where it passes near a vertex)
merged = 0
while True:
    ring = [e for e in bm.edges if e.is_boundary and all(abs((v.co - c0).dot(n0)) < 1e-5 for v in e.verts)]
    if not ring: break
    mean = sum(e.calc_length() for e in ring) / len(ring); e = min(ring, key=lambda e: e.calc_length())
    if e.calc_length() > 0.4 * mean: break
    bmesh.ops.pointmerge(bm, verts=list(e.verts), merge_co=(e.verts[0].co + e.verts[1].co) / 2); merged += 1
print('RING merged short edges', merged)
print('CUT snapped', snapped, 'removed pieces', len({comp[v] for v in dead}), 'verts', len(bm.verts), 'faces', len(bm.faces),
      'open edges', sum(1 for e in bm.edges if e.is_boundary))
bm.to_mesh(me); bm.free(); me.update()
bpy.ops.wm.save_as_mainfile(filepath=a[2])
