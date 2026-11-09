"""Neck cross-section centroids (y, z) and depth (y extent) of 'Body' and the MM9 mesh per z slice.
Args: <fit blend> [z0 z1 step]"""
import bpy, sys
import numpy as np
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
z0, z1, st = (float(a) for a in argv[1:4]) if len(argv) > 3 else (0.42, 0.80, 0.03)
out = {}
for o in bpy.data.objects:
    if o.type != 'MESH':
        continue
    P = np.array([tuple(o.matrix_world @ v.co) for v in o.data.vertices])
    rows = []
    for z in np.arange(z0, z1 + 1e-6, st):
        m = (np.abs(P[:, 2] - z) < st / 2) & (P[:, 1] < 0.02)
        if m.sum() < 3:
            continue
        rows.append('z %.2f y %.3f..%.3f mid %.3f n %d' % (z, P[m, 1].min(), P[m, 1].max(), (P[m, 1].min() + P[m, 1].max()) / 2, m.sum()))
    print('SLICE', o.name, *rows, sep='\n  ')
arm = bpy.data.objects['MM9_Rig']
for b in arm.data.bones:
    if 'neck' in b.name or b.name in ('Xhead', 'Xback'):
        print('JOINT', b.name, [round(x, 3) for x in arm.matrix_world @ b.head_local])
