"""Dump the 'Body' vertices (+ piece attr), edges and the MM9 joints/vertex labels of a fit blend to npz.
Args: <blend> <out npz>"""
import bpy, sys
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0])
b = bpy.data.objects['Body']; me = b.data
P = np.array([tuple(b.matrix_world @ v.co) for v in me.vertices])
E = np.array([tuple(e.vertices) for e in me.edges])
F = np.array([tuple(p.vertices) for p in me.polygons if len(p.vertices) == 3])
piece = np.array([d.value for d in me.attributes['piece'].data]) if 'piece' in me.attributes else np.zeros(len(P), int)
arm = bpy.data.objects['MM9_Rig']
J = {bb.name: tuple(arm.matrix_world @ bb.head_local) for bb in arm.data.bones}
mp, ml = [], []
for o in bpy.data.objects:
    if o.type == 'MESH' and o.name != 'Body':
        for v in o.data.vertices:
            if v.groups:
                g = max(v.groups, key=lambda g: g.weight)
                mp.append(tuple(o.matrix_world @ v.co)); ml.append(o.vertex_groups[g.group].name)
np.savez(a[1], P=P, E=E, F=F, piece=piece, jn=np.array(list(J)), jp=np.array(list(J.values())), mp=np.array(mp), ml=np.array(ml))
print('DUMP', len(P))
