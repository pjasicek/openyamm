import bpy, sys
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
o = bpy.data.objects['Body']
c = np.array([v.co[:] for v in o.data.vertices]); e = np.array([x.vertices[:] for x in o.data.edges])
pa = np.zeros(len(c), int); o.data.attributes['part'].data.foreach_get('value', pa)
m = pa[e[:, 0]] == 0
e = e[m]
out = {}
for z in (0.76, 0.78, 0.80, 0.82, 0.84, 0.86):
    A, B = c[e[:, 0]], c[e[:, 1]]
    s = (A[:, 2] - z) * (B[:, 2] - z) < 0
    t = (z - A[s, 2]) / (B[s, 2] - A[s, 2])
    Q = A[s] + (B[s] - A[s]) * t[:, None]
    out[str(z)] = Q
    print('Z', z, len(Q), 'w', np.ptp(Q[:, 0]) if len(Q) else 0, 'd', np.ptp(Q[:, 1]) if len(Q) else 0, 'cy', Q[:, 1].mean() if len(Q) else 0)
np.savez(a[1], **out)
