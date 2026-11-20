"""Probe the face: front-most head-shell vertices near the midline by height (nose tip, lips), eyes. Args: blend"""
import bpy, sys
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
b = bpy.data.objects['Body']; me = b.data
co = np.array([tuple(b.matrix_world @ v.co) for v in me.vertices])
m = (np.abs(co[:, 0]) < 0.02) & (co[:, 2] > 0.95) & (co[:, 2] < 1.3)
for z in np.arange(0.98, 1.26, 0.01):
    k = m & (np.abs(co[:, 2] - z) < 0.005)
    if k.any():
        print('PROBE z %.3f front y %.3f' % (z, co[k, 1].min()))
k = (co[:, 2] > 1.0) & (co[:, 2] < 1.25) & (co[:, 1] < -0.05)
print('PROBE face x range', co[k, 0].min(), co[k, 0].max())
