"""Push hair vertices that lie (nearly) coplanar with the skin out to a safe 5 mm, removing z-fighting.
Rest-pose vertex move only: topology, UVs and weights are unchanged."""
import bpy, sys, os, json
import numpy as np
from mathutils.bvhtree import BVHTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
mesh = bpy.data.objects['Peasant']; me = mesh.data
PARTS = json.loads(bpy.context.scene['pfem_parts'])
part = np.zeros(len(me.polygons), dtype=np.int32); me.attributes['part'].data.foreach_get('value', part)
body_faces = [p for p in me.polygons if part[p.index] == PARTS.index('Body')]
tree = BVHTree.FromPolygons([v.co for v in me.vertices], [tuple(p.vertices) for p in body_faces])
moved_parts = ('Hair', 'Braid', 'Headband')
verts = {vi for p in me.polygons if PARTS[part[p.index]] in moved_parts for vi in p.vertices}
moved = 0
for vi in verts:
    v = me.vertices[vi]
    loc, normal, _, dist = tree.find_nearest(v.co)
    if loc is not None and dist < 0.004:
        v.co = loc + normal * 0.005; moved += 1
me.update()
print('HAIR_OFFSET moved', moved, 'of', len(verts))
bpy.ops.wm.save_mainfile()
