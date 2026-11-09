"""Mid-plane and jaw-angle profile of the head shell (rest pose) for face_rigid_pm3.py. Args (Blender): <blend>"""
import bpy, sys
import numpy as np
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index('--') + 1])
body = bpy.data.objects['Body']; me = body.data
P = np.array([body.matrix_world @ v.co for v in me.vertices])
for xs in (0.0, 0.03, 0.05):
    m = (np.abs(np.abs(P[:, 0]) - xs) < 0.008) & (P[:, 2] > 0.60) & (P[:, 2] < 0.80) & (P[:, 1] < 0.02)
    # front-most y per 1 cm z slice
    out = []
    for z0 in np.arange(0.62, 0.80, 0.01):
        k = m & (P[:, 2] >= z0) & (P[:, 2] < z0 + 0.01)
        if k.any(): out.append('%.2f:%.3f' % (z0, P[k, 1].min()))
    print('JAW x=%.2f' % xs, ' '.join(out))
for nm in ('Bip01 Neck', 'Bip01 Head'):
    b = bpy.data.objects['MM9_Rig'].data.bones[nm]; print('JOINT', nm, [round(c, 3) for c in (bpy.data.objects['MM9_Rig'].matrix_world @ b.head_local)])
