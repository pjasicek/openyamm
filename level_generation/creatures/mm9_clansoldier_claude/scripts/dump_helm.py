import bpy, sys
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=a[0])
o = next(x for x in bpy.data.objects if x.type == 'MESH')
dg = bpy.context.evaluated_depsgraph_get(); bv = BVHTree.FromObject(o, dg)
S = 0.31
for z in np.arange(0.155, -0.03, -0.0075):
    r = []
    for t in (0, 45, 90, 135, 180):
        th = np.radians(t); d = Vector((-np.sin(th), np.cos(th), 0))      # 0 = back, 180 = front
        p = d * 2 + Vector((0, 0, z / S))
        loc, *_ = bv.ray_cast(p, -d, 3)
        r.append(round((loc - Vector((0, 0, z / S))).length * S, 4) if loc else None)
    print('DUMP', round(float(z), 4), r)
