"""Y extents of the Body (fitted blend) in |x| < W at given heights; also the rig's centre joints. Args: <blend> z1,z2,..."""
import bpy, sys
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
b = bpy.data.objects['Body']; arm = bpy.data.objects['MM9_Rig']
co = np.array([b.matrix_world @ v.co for v in b.data.vertices])
for z in [float(x) for x in a[1].split(',')]:
    for W in (0.03, 0.08):
        m = (np.abs(co[:, 2] - z) < 0.012) & (np.abs(co[:, 0]) < W)
        if m.sum():
            print('SEC z %.3f W %.2f y %.3f..%.3f  n %d' % (z, W, co[m, 1].min(), co[m, 1].max(), m.sum()))
    m = (np.abs(co[:, 2] - z) < 0.012)
    print('SEC z %.3f full x %.3f..%.3f' % (z, co[m, 0].min(), co[m, 0].max()))
for n in ('Bip01 Spine3', 'Bip01 Neck', 'Bip01 Head', 'Bip01 L Clavicle', 'Bip01 L UpperArm', 'Bip01 L Forearm', 'Bip01 L Hand'):
    print('JOINT', n, tuple(round(x, 3) for x in arm.matrix_world @ arm.data.bones[n].head_local))
