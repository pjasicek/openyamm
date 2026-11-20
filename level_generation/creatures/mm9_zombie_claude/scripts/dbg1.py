import bpy, sys
import numpy as np
b = sys.argv[sys.argv.index('--') + 1]
bpy.ops.wm.open_mainfile(filepath=b)
o = bpy.data.objects['Body']
pa = np.zeros(len(o.data.vertices), int); o.data.attributes['part'].data.foreach_get('value', pa)
c = np.array([v.co[:] for v in o.data.vertices])
for k in np.unique(pa):
    q = c[pa == k]; print('PART', k, len(q), q.min(0).round(3), q.max(0).round(3))
q = c[pa == 0]
for z in np.arange(0.6, 0.8, 0.02):
    m = q[np.abs(q[:, 2] - z) < 0.008]
    if len(m): print('U z %.2f n %d w %.3f d %.3f cy %.3f' % (z, len(m), np.ptp(m[:, 0]), np.ptp(m[:, 1]), 0.5 * (m[:, 1].min() + m[:, 1].max())))
q = c[pa == 10]
for z in np.arange(0.74, 0.9, 0.02):
    m = q[np.abs(q[:, 2] - z) < 0.008]
    if len(m): print('F z %.2f n %d w %.3f d %.3f cy %.3f' % (z, len(m), np.ptp(m[:, 0]), np.ptp(m[:, 1]), 0.5 * (m[:, 1].min() + m[:, 1].max())))
