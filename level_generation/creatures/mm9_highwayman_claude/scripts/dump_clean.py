import bpy, sys
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
b = bpy.data.objects['Body']; me = b.data
fp = np.zeros(len(me.polygons), int); me.attributes['part'].data.foreach_get('value', fp)
P = np.array([v.co[:] for v in me.vertices]); vp = np.zeros(len(P), int)
for p in me.polygons:
    for v in p.vertices: vp[v] = fp[p.index]
print('DUMP parts', {int(k): (int((vp == k).sum()), np.round(P[vp == k].min(0), 3).tolist(), np.round(P[vp == k].max(0), 3).tolist()) for k in np.unique(vp)})
for z in (-0.6, -0.65, -0.7, -0.75, -0.8, -0.85, -0.88, -0.91):
    m = (np.abs(P[:, 2] - z) < 0.012) & (P[:, 0] < 0) & (vp == 6)
    if m.sum() > 2: print('DUMP boot', z, np.round(.5 * (P[m].min(0) + P[m].max(0)), 3).tolist(), np.round(np.ptp(P[m], axis=0), 3).tolist())
m = (P[:, 0] < 0) & (vp == 6); print('DUMP toe', np.round(P[m][P[m, 1].argmin()], 3).tolist(), 'heel', np.round(P[m][P[m, 1].argmax()], 3).tolist())
for z in (-0.3, -0.35, -0.4, -0.45, -0.5, -0.55):
    m = (np.abs(P[:, 2] - z) < 0.012) & (P[:, 0] < 0) & (vp == 5)
    if m.sum(): print('DUMP leg', z, np.round(.5 * (P[m].min(0) + P[m].max(0)), 3).tolist(), np.round(np.ptp(P[m], axis=0), 3).tolist())
for z in (0.64, 0.62, 0.6, 0.58, 0.56, 0.54, 0.52, 0.5):
    m = (np.abs(P[:, 2] - z) < 0.012) & np.isin(vp, (1, 8)) & (np.abs(P[:, 0]) < 0.14)
    if m.sum(): print('DUMP neckhole', z, np.round(P[m].min(0), 3).tolist(), np.round(P[m].max(0), 3).tolist(), int(m.sum()))
