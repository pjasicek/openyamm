"""How many skirt surfaces a horizontal ray from the pelvis axis crosses (rest pose), per angle and height, and where
the extra layers lie. Args: -- <blend> [garments]"""
import bpy, sys, os, math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0])); G = [int(x) for x in (a[1] if len(a) > 1 else '2').split(',')]
rig = bpy.data.objects['Rig']; me = bpy.data.objects['Body'].data
gv = np.array([x.value for x in me.attributes['garment'].data]); co = [v.co.copy() for v in me.vertices]
faces = [tuple(p.vertices) for p in me.polygons if all(gv[i] in G for i in p.vertices)]
T = BVHTree.FromPolygons(co, faces)
pel = rig.data.bones['B_Pelvis'].head_local
for z in (0.4, 0.5, 0.6, 0.7, 0.8):
    row = []
    for deg in range(-180, 180, 15):
        d = Vector((math.sin(math.radians(deg)), math.cos(math.radians(deg)), 0)); p = Vector((pel.x, pel.y, z)); hits = []; dist = 0
        while dist < 0.6:
            h = T.ray_cast(p + d * (dist + 1e-4), d, 0.6 - dist)
            if h[0] is None: break
            hits.append(round(dist + h[3], 3)); dist += h[3] + 1e-4
        row.append(f'{deg}:{len(hits)}' + (f'{hits}' if len(hits) > 1 else ''))
    print('LAYERS z', z, ' '.join(row))
