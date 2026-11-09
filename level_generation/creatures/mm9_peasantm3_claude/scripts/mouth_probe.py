"""Mouth geometry probe (rest): face-shell vertices near the mid-plane in the mouth box, depth (y) per 2 mm height band.
Args (Blender): <blend>"""
import bpy, sys
import numpy as np
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index('--') + 1])
body = bpy.data.objects['Body']; me = body.data
P = np.array([(body.matrix_world @ v.co)[:] for v in me.vertices])
for xs in (0.0, 0.012):
    m = (np.abs(np.abs(P[:, 0]) - xs) < 0.005) & (P[:, 2] > 0.715) & (P[:, 2] < 0.77) & (P[:, 1] < -0.02)
    print('MOUTH x=%.3f' % xs)
    for z0 in np.arange(0.716, 0.77, 0.003):
        k = m & (P[:, 2] >= z0) & (P[:, 2] < z0 + 0.003)
        if k.any():
            print('  MOUTH z %.3f n %2d y front %.4f back %.4f' % (z0, k.sum(), P[k, 1].min(), P[k, 1].max()))
