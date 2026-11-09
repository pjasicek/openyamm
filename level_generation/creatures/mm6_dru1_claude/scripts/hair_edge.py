"""Pin the hair shell's open front edge onto the scalp (review 5: thin black slivers under the hair's zigzag front edge
were the dark hood lining seen through the 2-6 mm gap between the edge and the scalp). Boundary vertices of the hair
(piece 1) in the front-top region move to the nearest scalp point + 0.5 mm along its normal; their direct neighbours
follow halfway. In place. Args: -- <blend>"""
import bpy, bmesh, sys, os
import numpy as np
from mathutils.bvhtree import BVHTree
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(sys.argv[sys.argv.index('--') + 1]))
rig = bpy.data.objects['Rig']; rig.animation_data_create(); rig.animation_data.action = None
me = bpy.data.objects['Body'].data
if me.get('hair_edge'):
    print('HAIREDGE already pinned'); sys.exit(0)
pv = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
tree = BVHTree.FromPolygons([v.co for v in bm.verts], [tuple(v.index for v in f.verts) for f in bm.faces if all(pv[v.index] == 0 for v in f.verts)])
edge = [v for v in bm.verts if pv[v.index] == 1 and any(e.is_boundary for e in v.link_edges)
        and v.co.z > 1.59 and v.co.y < -0.03 and abs(v.co.x + 0.007) < 0.07]
moved = {}
for v in edge:
    loc, n, i, d = tree.find_nearest(v.co, 0.02)
    if loc is not None:
        moved[v] = loc + n * 0.0005 - v.co
for v, dv in list(moved.items()):
    for e in v.link_edges:
        o = e.other_vert(v)
        if pv[o.index] == 1 and o not in moved:
            o.co += dv * 0.5
    v.co += dv
bm.to_mesh(me); bm.free(); me['hair_edge'] = 1; me.update(); bpy.ops.wm.save_mainfile()
print('HAIREDGE boundary vertices pinned', len(moved), 'max gap mm', round(max((d.length for d in moved.values()), default=0) * 1000, 1))
