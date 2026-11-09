"""Compare wing extents: MM9 bind wing vs unposed Body wing (label_meshy wing). Args: fit blend"""
import bpy, sys
import numpy as np
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
arm = bpy.data.objects['MM9_Rig']; bones = [b.name for b in arm.data.bones]
body = bpy.data.objects['Body']
lm = np.array([d.value for d in body.data.attributes['label_meshy'].data])
P = np.array([tuple(v.co) for v in body.data.vertices])
wing = np.array([bones[l].startswith('Y') for l in lm])
A = []
for o in bpy.data.objects:
    if o.type == 'MESH' and o.name.endswith('.mesh') and not o.name.startswith('MM9Posed'):
        for v in o.data.vertices:
            g = max(v.groups, key=lambda g: g.weight)
            if o.vertex_groups[g.group].name.startswith('Y'):
                A.append(tuple(o.matrix_world @ v.co))
A = np.array(A)
for side, nm in ((-1, 'right(-x)'), (1, 'left(+x)')):
    a = A[np.sign(A[:, 0]) == side]; b = P[wing & (np.sign(P[:, 0]) == side)]
    print('EXT', nm, 'MM9 min', a.min(0).round(2), 'max', a.max(0).round(2), '| ours min', b.min(0).round(2), 'max', b.max(0).round(2))
