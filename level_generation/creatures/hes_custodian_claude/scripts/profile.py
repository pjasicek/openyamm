"""Front profile of the belt at x = 0: first hit y (and the hit face's part) per height. Args: none"""
import bpy, os, sys
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cust_common as cc
bpy.ops.wm.open_mainfile(filepath=cc.path('work/tex.blend'))
ob = bpy.data.objects['Custodian']
bvh = BVHTree.FromObject(ob, bpy.context.evaluated_depsgraph_get())
for z in np.arange(1.35, 2.35, 0.025):
    for x in (0.0, 0.25):
        h = bvh.ray_cast(Vector((x, -4, z)), Vector((0, 1, 0)))
        print('PROF x %.2f z %.3f y %s n %s' % (x, z, round(h[0].y, 3) if h[0] else None, tuple(round(c, 2) for c in h[1]) if h[0] else None))
