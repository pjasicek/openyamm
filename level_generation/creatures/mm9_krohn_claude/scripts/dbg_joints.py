import bpy, sys, json, os
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
rig = bpy.data.objects['Body'].parent
GJ = json.load(open(a[1]))['joints']['R']
for k, n in ((2, 'Index'), (3, 'Middle'), (5, 'Pinky'), (1, 'Thumb')):
    for j in (1, 2, 3):
        b = rig.data.bones[f'Bip01 R {n}{j}']
        h = np.array(rig.matrix_world @ b.head_local); t = np.array(rig.matrix_world @ b.tail_local)
        print('DBG', n, j, 'json', np.round(GJ[f'finger{k}-{j}'], 3), 'bone head', np.round(h, 3), 'tail dir', np.round((t - h) / np.linalg.norm(t - h), 2))
    print('DBG tip', np.round(GJ[f'finger{k}-3_tip'], 3))
print('DBG hand', np.round(np.array(rig.matrix_world @ rig.data.bones['Bip01 R Hand'].head_local), 3))
