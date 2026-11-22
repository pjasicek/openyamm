"""Hidden-surface check: per face, a ray from just off the face along its normal; faces whose ray hits the mesh within
reach are enclosed (inner shells). Args: -- <blend in work/> <object> [reach m]"""
import bpy, os, sys
import numpy as np
from mathutils.bvhtree import BVHTree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', a[0]))
ob = bpy.data.objects[a[1]]; reach = float(a[2]) if len(a) > 2 else 0.3
me = ob.data
bvh = BVHTree.FromObject(ob, bpy.context.evaluated_depsgraph_get())
hidden = []; area = []
for p in me.polygons:
    o = p.center + p.normal * 1e-4
    loc, nrm, idx, dist = bvh.ray_cast(o, p.normal, reach)
    # enclosed when the ray hits a face from its back side (we are inside a closed surface)
    hidden.append(loc is not None and nrm.dot(p.normal) > 0)
    area.append(p.area)
hidden = np.array(hidden); area = np.array(area)
print('HIDDEN faces', int(hidden.sum()), 'of', len(hidden), 'area share', round(float(area[hidden].sum() / area.sum()), 3))
np.save(os.path.join(HERE, 'work', 'hidden_faces.npy'), hidden)
