"""Hat triangles for the texel bakes. Args (Blender): <blend> <out npz>"""
import bpy, sys
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
h = bpy.data.objects['Hat']; me = h.data; me.calc_loop_triangles()
uv = me.uv_layers['UVMap'].data
U, X = [], []
for t in me.loop_triangles:
    U.append([tuple(uv[l].uv) for l in t.loops]); X.append([tuple(h.matrix_world @ me.vertices[v].co) for v in t.vertices])
np.savez(a[1], uv=np.array(U, np.float32), xyz=np.array(X, np.float32))
print('DUMPHAT', len(U))
