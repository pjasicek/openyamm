import bpy, sys, bmesh
import numpy as np
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index('--') + 1])
o = bpy.data.objects['Helm']; me = o.data
Q = np.array([v.co[:] for v in me.vertices])
m = (np.abs(Q[:, 0]) < 0.012) & (Q[:, 2] > 0.1)
print('SEAM', m.sum())
for q in Q[m][np.argsort(Q[m, 1])]: print('SEAM ', q.round(3))
