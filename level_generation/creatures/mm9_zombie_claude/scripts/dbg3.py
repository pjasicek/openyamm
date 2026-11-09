import bpy, sys
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
o = bpy.data.objects['Face']
c = np.array([v.co[:] for v in o.data.vertices]); e = np.array([x.vertices[:] for x in o.data.edges])
c[:, 2] += 0.9053; c[:, 1] += 0.022
out = {}
for z in (0.77, 0.78, 0.80, 0.82, 0.84, 0.86):
    A, B = c[e[:, 0]], c[e[:, 1]]
    s = (A[:, 2] - z) * (B[:, 2] - z) < 0
    t = (z - A[s, 2]) / (B[s, 2] - A[s, 2])
    out[str(z)] = A[s] + (B[s] - A[s]) * t[:, None]
np.savez(a[1], **out)
