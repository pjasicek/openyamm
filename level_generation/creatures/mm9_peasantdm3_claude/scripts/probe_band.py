"""Diagnostic: y extent of Body (fit blend) in z bands near the centre (|x|<0.12). Args: <blend>"""
import bpy, sys
import numpy as np
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index('--') + 1])
b = bpy.data.objects['Body']; mw = b.matrix_world
p = np.array([tuple(mw @ v.co) for v in b.data.vertices])
for z in np.arange(0.30, 0.72, 0.03):
    m = (np.abs(p[:, 2] - z) < 0.03) & (np.abs(p[:, 0]) < 0.12)
    if m.sum():
        q = p[m, 1]
        print('BAND z=%.2f n=%d ymin=%.3f ymax=%.3f p5=%.3f p95=%.3f' % (z, m.sum(), q.min(), q.max(), *np.percentile(q, [5, 95])))
