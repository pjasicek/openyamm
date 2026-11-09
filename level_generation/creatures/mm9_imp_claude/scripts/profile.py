import bpy, sys
import numpy as np
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index('--') + 1])
o = bpy.data.objects['Body']
P = np.array([tuple(o.matrix_world @ v.co) for v in o.data.vertices])
m = np.abs(P[:, 0]) < 0.02
print('profile y -> zmin zmax (|x|<0.02)')
for y in np.arange(-0.36, 0.2, 0.02):
    k = m & (np.abs(P[:, 1] - y) < 0.012)
    if k.any():
        z = np.sort(P[k, 2]); print('y %.2f' % y, np.round(z[z > 0.05][:6], 3), '...', np.round(z[-3:], 3))
