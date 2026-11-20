"""Print limb slices of the raw placed body along given axes to find joints."""
import bpy, sys
import numpy as np
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index('--') + 1])
o = bpy.data.objects['Body']
P = np.array([tuple(o.matrix_world @ v.co) for v in o.data.vertices])
print('Y slices of torso (x<0.1) z -> yrange')
for z in np.arange(-0.3, 0.56, 0.05):
    m = (np.abs(P[:, 2] - z) < 0.02) & (np.abs(P[:, 0]) < 0.1)
    print('tz %.2f y %.3f %.3f' % (z, P[m, 1].min(), P[m, 1].max()))
print('leg slices: x>0.03 by z; x<-0.03')
for sx in (1, -1):
    for z in np.arange(-0.62, -0.05, 0.04):
        m = (np.abs(P[:, 2] - z) < 0.015) & (P[:, 0] * sx > 0.03) & (P[:, 1] < 0.2 - 0.42)
        if m.any():
            print('leg %d z %.2f x %.3f %.3f y %.3f %.3f' % (sx, z, *(sorted(P[m, 0])[0], sorted(P[m, 0])[-1]), P[m, 1].min(), P[m, 1].max()))
print('arm slices')
for sx in (1, -1):
    for x in np.arange(0.15, 0.78, 0.05):
        m = (np.abs(P[:, 0] * sx - x) < 0.012) & (P[:, 2] > -0.25)
        if m.any():
            print('arm %d x %.2f y %.3f %.3f z %.3f %.3f' % (sx, x, P[m, 1].min(), P[m, 1].max(), P[m, 2].min(), P[m, 2].max()))
