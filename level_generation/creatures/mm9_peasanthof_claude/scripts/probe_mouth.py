import bpy, bmesh, sys
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
ob = bpy.data.objects['Body']; me = ob.data
me.calc_loop_triangles() if hasattr(me,'calc_loop_triangles') else None
for v in me.vertices:
    c = ob.matrix_world @ v.co
    if abs(c.x) < 0.04 and float(a[1]) < c.z < float(a[2]) and c.y < float(a[3]):
        n = v.normal
        print('MV', v.index, round(c.x,4), round(c.y,4), round(c.z,4), '|', round(n.x,2), round(n.y,2), round(n.z,2))
