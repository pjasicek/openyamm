import bpy, sys
import numpy as np
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
arm = bpy.data.objects['MM9_Rig']
J = {b.name: np.array(arm.matrix_world @ b.head_local) for b in arm.data.bones}
body = bpy.data.objects['Body']
P = np.array([tuple(v.co) for v in body.data.vertices])
print('ZMIN', P[:, 2].min())
for f in ('Xfoot', 'Xfoot01'):
    a = J[f]
    side = np.sign(a[0]) == np.sign(P[:, 0])
    for z0 in np.arange(0, 0.14, 0.01):
        m = side & (P[:, 2] >= z0) & (P[:, 2] < z0 + 0.01) & (np.linalg.norm(P[:, :2] - a[:2], axis=1) < 0.15)
        if m.sum():
            c = P[m].mean(0)
            print('FOOT', f, 'z %.2f n %d c %.3f %.3f  xr %.3f..%.3f yr %.3f..%.3f' % (z0, m.sum(), c[0], c[1], P[m, 0].min(), P[m, 0].max(), P[m, 1].min(), P[m, 1].max()))
    print('JOINT', f, a, 'leg', J[f.replace('foot', 'leg')])
