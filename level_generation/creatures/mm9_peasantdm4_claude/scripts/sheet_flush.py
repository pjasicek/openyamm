"""Lay the beard/moustache sheet's open edge flush onto the face (Meshy left the beard as a sheet a few mm in front of the
cheeks, skin-painted at its top: a hard-edged "plate" on the cheek and background slivers through the gap at grazing
angles). Boundary vertices of 'Body' inside the box cast a ray backwards along their own normal (start 0.5 mm behind
them, faces touching the vertex ignored); a hit within MAXD moves the vertex onto that surface (+0.3 mm). Neighbours one
and two edge rings in (not on the boundary) follow with 0.55 / 0.25 of the mean move of their moved neighbours.
Positions only: UVs, weights and topology unchanged. Args: <in blend> <out blend> <xmin,ymin,zmin,xmax,ymax,zmax> [MAXD 0.012]"""
import bpy, bmesh, sys
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
box = [float(t) for t in a[2].split(',')]; MAXD = float(a[3]) if len(a) > 3 else 0.012
me = bpy.data.objects['Body'].data
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table(); bm.normal_update()
inb = lambda c: all(box[i] <= c[i] <= box[i + 3] for i in range(3))
bvh = BVHTree.FromBMesh(bm)
move = {}
for v in bm.verts:
    if not inb(v.co) or not any(e.is_boundary for e in v.link_edges):
        continue
    n = v.normal
    if n.length < 0.5:
        continue
    own = {f.index for f in v.link_faces}
    start = v.co - n * 0.0005
    hit = None
    for _ in range(4):
        h = bvh.ray_cast(start, -n, MAXD)
        if h[0] is None:
            break
        if h[2] in own:
            start = h[0] - n * 0.0002
            continue
        hit = h
        break
    if hit is not None and (hit[0] - v.co).length < MAXD:
        move[v.index] = (hit[0] + n * 0.0003) - v.co
ring1 = {}
for vi, d in move.items():
    for e in bm.verts[vi].link_edges:
        o = e.other_vert(bm.verts[vi])
        if o.index not in move and not any(x.is_boundary for x in o.link_edges):
            ring1.setdefault(o.index, []).append(d)
ring2 = {}
for vi, ds in ring1.items():
    for e in bm.verts[vi].link_edges:
        o = e.other_vert(bm.verts[vi])
        if o.index not in move and o.index not in ring1 and not any(x.is_boundary for x in o.link_edges):
            ring2.setdefault(o.index, []).append(sum(ds, Vector()) / len(ds))
for vi, d in move.items():
    bm.verts[vi].co += d
for vi, ds in ring1.items():
    bm.verts[vi].co += 0.55 * sum(ds, Vector()) / len(ds)
for vi, ds in ring2.items():
    bm.verts[vi].co += 0.25 * sum(ds, Vector()) / len(ds)
mx = max((d.length for d in move.values()), default=0)
print('FLUSH moved', len(move), 'ring1', len(ring1), 'ring2', len(ring2), 'max mm', round(mx * 1000, 1))
bm.to_mesh(me); me.update()
bpy.ops.wm.save_as_mainfile(filepath=a[1])
