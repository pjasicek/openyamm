"""Part-wise slices of a cleaned Body for joint estimates. Args: <blend>"""
import bpy, sys
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
b = bpy.data.objects['Body']; me = b.data
fp = np.zeros(len(me.polygons), int); me.attributes['part'].data.foreach_get('value', fp)
P = np.array([v.co[:] for v in me.vertices]); vp = np.zeros(len(P), int)
for p in me.polygons:
    for v in p.vertices: vp[v] = fp[p.index]
L = P[:, 0] < 0
print('SL parts', {int(k): int((vp == k).sum()) for k in np.unique(vp)})
for z in np.arange(0.62, -0.1, -0.06):
    m = L & (np.abs(P[:, 2] - z) < 0.012) & (vp == 1) & (P[:, 0] < -0.17)
    if m.sum() > 3: print('SL arm', round(float(z), 2), np.round(.5 * (P[m].min(0) + P[m].max(0)), 3).tolist(), np.round(np.ptp(P[m], axis=0), 3).tolist())
for z in np.arange(0.3, -0.9, -0.06):
    m = L & (np.abs(P[:, 2] - z) < 0.012) & np.isin(vp, (5, 6))
    if m.sum() > 3: print('SL leg', round(float(z), 2), np.round(.5 * (P[m].min(0) + P[m].max(0)), 3).tolist(), np.round(np.ptp(P[m], axis=0), 3).tolist())
for z in np.arange(0.6, 0.0, -0.05):
    m = L & (np.abs(P[:, 2] - z) < 0.012) & np.isin(vp, (1, 7, 9)) & (P[:, 0] > -0.27)
    if m.sum() > 3: print('SL torso', round(float(z), 2), np.round(P[m].min(0), 3).tolist(), np.round(P[m].max(0), 3).tolist())
m = L & (vp == 4)
print('SL hand', P[m].min(0).round(3), P[m].max(0).round(3))
m = L & (vp == 6); print('SL shoe', P[m].min(0).round(3), P[m].max(0).round(3), 'toe', P[m][P[m, 1].argmin()].round(3), 'heel', P[m][P[m, 1].argmax()].round(3))
