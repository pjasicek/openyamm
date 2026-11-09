"""Probe P01 (shorts + right leg + tail): y extent per z slice, to locate the tail junction."""
import bpy, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, 'st1_parts.blend'))
o = bpy.data.objects['P01']
co = np.array([tuple(v.co) for v in o.data.vertices])
for z in np.arange(0.10, 0.96, 0.04):
    s = co[(co[:, 2] >= z) & (co[:, 2] < z + 0.04)]
    if len(s):
        ys = np.sort(s[:, 1])
        t = s[s[:, 1] > 0.12]
        tx = (t[:, 0].min(), t[:, 0].max()) if len(t) else (0, 0)
        print('Z %.2f n %4d y %.3f..%.3f  x %.3f..%.3f  y>0.12: %d (x %.3f..%.3f)' % (z, len(s), ys[0], ys[-1],
              s[:, 0].min(), s[:, 0].max(), len(t), tx[0], tx[1]))
b = bpy.data.objects['P02']; c2 = np.array([tuple(v.co) for v in b.data.vertices])
print('P02 left leg y max per z', [(round(z, 2), round(float(c2[(c2[:, 2] >= z) & (c2[:, 2] < z + .08), 1].max()), 3)) for z in np.arange(0.12, 0.9, 0.08) if ((c2[:, 2] >= z) & (c2[:, 2] < z + .08)).any()])
