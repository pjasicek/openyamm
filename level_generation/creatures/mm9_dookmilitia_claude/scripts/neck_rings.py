import bpy, sys
import numpy as np
F, H = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=F)
me = bpy.data.objects['Body'].data
fp = np.zeros(len(me.polygons), int); me.attributes['part'].data.foreach_get('value', fp)
P = np.array([v.co[:] for v in me.vertices]); vp = np.zeros(len(P), int)
for p in me.polygons:
    for v in p.vertices: vp[v] = fp[p.index]
for lb, nm in ((2, 'oldneck'), (1, 'tunic'), (8, 'mantle')):
    q = P[vp == lb]
    print('RING', nm, 'n', len(q))
    for z in np.arange(0.74, 0.54, -0.02):
        m = (q[:, 2] > z - 0.012) & (q[:, 2] < z + 0.012) & (np.abs(q[:, 0]) < 0.32)
        if m.sum() > 1: print('RING ', round(z, 2), q[m].min(0).round(3).tolist(), q[m].max(0).round(3).tolist(), int(m.sum()))
with bpy.data.libraries.load(H) as (s, d): d.objects = list(s.objects)
for o in d.objects:
    Q = np.array([v.co[:] for v in o.data.vertices])
    print('RING', o.name, Q.min(0).round(3), Q.max(0).round(3))
    if o.name in ('Face', 'Helm'):
        for z in (-.2, -.17, -.14, -.11, -.08, -.05, 0, .05, .1):
            m = (Q[:, 2] > z - 0.012) & (Q[:, 2] < z + 0.012)
            if m.sum() > 1: print('RING ', o.name, z, Q[m].min(0).round(3).tolist(), Q[m].max(0).round(3).tolist(), int(m.sum()))
