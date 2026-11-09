import bpy, sys
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
b = bpy.data.objects['Body']; me = b.data
fp = np.zeros(len(me.polygons), int); me.attributes['part'].data.foreach_get('value', fp)
P = np.array([v.co[:] for v in me.vertices]); vp = np.zeros(len(P), int)
for p in me.polygons:
    for v in p.vertices: vp[v] = fp[p.index]
q = P[(vp == 4) & (P[:, 0] < 0)]
c = q.mean(0); U = np.linalg.svd(q - c)[2]; d = U[0] * np.sign(U[0][0]) * -1
print('DUMP axis', d.round(3), 'c', c.round(3))
t = (q - c) @ d; r = q - c - np.outer(t, d)
for x in np.arange(t.min(), t.max(), 0.015):
    m = (t >= x) & (t < x + 0.015)
    if m.sum(): print('DUMP', round(float(x), 3), int(m.sum()), (c + d * x).round(3).tolist(), 'ext', np.round(np.ptp(q[m], axis=0), 3).tolist(), 'r', round(float(np.linalg.norm(r[m], axis=1).mean()), 3))
for z in (-0.2, -0.1, 0.0, 0.05, 0.1, 0.13, 0.2, 0.3, 0.4, 0.5):
    m = (np.abs(P[:, 2] - z) < 0.01) & (vp == 5) & (P[:, 0] < 0); n = (np.abs(P[:, 2] - z) < 0.01) & (vp == 1) & (np.abs(P[:, 0]) < 0.34) | (np.abs(P[:, 2] - z) < 0.01) & (vp == 7)
    print('DUMP z', z, 'leg', np.round(P[m].min(0) if m.any() else 0, 3), np.round(P[m].max(0) if m.any() else 0, 3), 'coat', np.round(P[n].min(0) if n.any() else 0, 3), np.round(P[n].max(0) if n.any() else 0, 3))
