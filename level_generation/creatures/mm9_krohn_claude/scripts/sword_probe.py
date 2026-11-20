"""How deep the sword sits in the back: for each sword vertex, the body's outermost back surface at its (x, z) (ray from
+y toward -y) minus the vertex y. Positive = inside the body/cape. Args: blend"""
import bpy, sys
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
dg = bpy.context.evaluated_depsgraph_get()
body = bpy.data.objects['Body']; pr = bpy.data.objects['Props']
bvh = BVHTree.FromObject(body, dg)
pm = pr.data
g = pr.vertex_groups['Xsword'].index
pts = [pr.matrix_world @ v.co for v in pm.vertices if any(x.group == g for x in v.groups)]
dep = []
for p in pts:
    hit = bvh.ray_cast(Vector((p.x, 3.0, p.z)), Vector((0, -1, 0)))
    if hit[0] is not None:
        dep.append((hit[0].y - p.y, p.z))
dep = np.array(dep)
print('SWORD inside depth p50 %.3f p90 %.3f max %.3f m over %d verts' % (np.median(dep[:, 0]), np.percentile(dep[:, 0], 90), dep[:, 0].max(), len(dep)))
for z0 in np.arange(-0.2, 1.3, 0.15):
    k = np.abs(dep[:, 1] - z0) < 0.075
    if k.any(): print('SWORD z %.2f max depth %.3f' % (z0, dep[k, 0].max()))
