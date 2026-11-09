import bpy, sys
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
b = bpy.data.objects['Body']; me = b.data
fp = np.zeros(len(me.polygons), int); me.attributes['part'].data.foreach_get('value', fp)
P = np.array([v.co[:] for v in me.vertices]); vp = np.zeros(len(P), int)
for p in me.polygons:
    for v in p.vertices: vp[v] = fp[p.index]
L = (P[:, 0] < 0)
for x in np.arange(-0.86, -0.2, 0.04):
    m = L & (np.abs(P[:, 0] - x) < 0.02) & np.isin(vp, (1, 4)) & (P[:, 2] > 0.1 - (0 if x < -.3 else -0.2))
    if m.sum() > 3:
        lo, hi = P[m].min(0), P[m].max(0)
        print('DUMP arm x', round(float(x), 2), 'cy', round(float(lo[1] + hi[1]) / 2, 3), 'cz', round(float(lo[2] + hi[2]) / 2, 3), 'ext', np.round(hi - lo, 3)[1:].tolist())
for z in np.arange(-1.03, 0.1, 0.05):
    m = L & (np.abs(P[:, 2] - z) < 0.025) & np.isin(vp, (5, 6))
    if m.sum() > 3:
        lo, hi = P[m].min(0), P[m].max(0)
        print('DUMP leg z', round(float(z), 2), 'cx', round(float(lo[0] + hi[0]) / 2, 3), 'cy', round(float(lo[1] + hi[1]) / 2, 3), 'ext', np.round(hi - lo, 3)[:2].tolist(), 'miny', round(float(lo[1]),3), 'maxy', round(float(hi[1]),3))
for z in np.arange(0.55, 0.9, 0.03):
    m = (np.abs(P[:, 2] - z) < 0.015) & (vp == 2)
    if m.sum() > 3:
        lo, hi = P[m].min(0), P[m].max(0)
        print('DUMP neck z', round(float(z), 2), 'x', np.round([lo[0], hi[0]], 3).tolist(), 'y', np.round([lo[1], hi[1]], 3).tolist())
m = (vp == 1) & (P[:, 2] > 0.5) & (np.abs(P[:, 0]) < 0.2)
print('DUMP coat top', np.round(P[m].max(0), 3).tolist())
