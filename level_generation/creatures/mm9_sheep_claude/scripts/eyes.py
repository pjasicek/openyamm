"""Replace Meshy's lumpy eye pieces (blobs with thread spikes) and lip specks by clean eyeballs.

All separate pieces (attribute piece 2) are deleted. The eyeball centre is the median of the +X eye blob, projected
to the head surface and sunk RADIUS * SINK along the inward normal; the sphere (16 x 10) is mirrored to -X. Each
eyeball takes the weights of its nearest socket vertex (rigid in the socket) and piece 1 (eye).
Args: <in blend> <out blend> [radius]"""
import bpy, bmesh, sys, json
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
argv = sys.argv[sys.argv.index('--') + 1:]
IN, OUT = argv[:2]
RADIUS = float(argv[2]) if len(argv) > 2 else 0.0165
SINK = 0.72
bpy.ops.wm.open_mainfile(filepath=IN)
o = bpy.data.objects['Body']
me = o.data
piece = np.array([d.value for d in me.attributes['piece'].data])
P = np.array([tuple(v.co) for v in me.vertices])
blob = P[(piece == 2) & (P[:, 0] > 0.03)]
c0 = np.median(blob, axis=0)
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
bmesh.ops.delete(bm, geom=[bm.verts[i] for i in np.nonzero(piece == 2)[0]], context='VERTS')
bm.to_mesh(me); bm.free()
bm = bmesh.new(); bm.from_mesh(me)
bvh = BVHTree.FromBMesh(bm)
loc, nrm, _, _ = bvh.find_nearest(Vector(c0))
centre = np.array(loc) - np.array(nrm) * RADIUS * SINK
from mathutils.kdtree import KDTree
k = KDTree(len(me.vertices))
for v in me.vertices:
    k.insert(v.co, v.index)
k.balance()
n0 = len(me.vertices)
groups = {g.index: g.name for g in o.vertex_groups}
bm2 = bmesh.new(); bm2.from_mesh(me)
new_sets = []
for sx in (1, -1):
    c = centre * np.array([sx, 1, 1])
    res = bmesh.ops.create_uvsphere(bm2, u_segments=14, v_segments=8, radius=RADIUS)
    vs = res['verts']
    for v in vs:
        v.co = v.co + Vector(tuple(c))
    new_sets.append((c, [v for v in vs]))
for f in bm2.faces:
    f.smooth = True
bm2.to_mesh(me)
me.update()
pa = me.attributes['piece']
added = list(range(n0, len(me.vertices)))
for i in added:
    pa.data[i].value = 1
for c, _ in new_sets:
    ids = [i for i in added if np.linalg.norm(np.array(tuple(me.vertices[i].co)) - c) < RADIUS * 1.5]
    # socket: the nearest body vertex to the eyeball centre (body vertices only)
    best = None
    for (co, idx, dist) in k.find_n(Vector(tuple(c)), 40):
        if idx < n0:
            best = idx; break
    w = {groups[g.group]: g.weight for g in me.vertices[best].groups}
    for name, wt in w.items():
        o.vertex_groups[name].add(ids, wt, 'REPLACE')
print('EYES ' + json.dumps({'centre': centre.round(4).tolist(), 'radius': RADIUS, 'removed_piece_verts': int((piece == 2).sum()),
                           'socket_weights': w}))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
