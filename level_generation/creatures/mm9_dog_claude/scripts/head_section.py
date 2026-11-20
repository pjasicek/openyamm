"""Sections of the head of 'Body' in a blend: plots surface points near given x planes in the y-z plane and near given
y planes in the x-z plane, MM9 joints marked. Args: <blend> <out png> <ymin,ymax,zmin,zmax> [x planes comma]"""
import bpy, sys, os
import numpy as np
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
b = bpy.data.objects['Body']
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
me = b.data
co = np.array([tuple(b.matrix_world @ v.co) for v in me.vertices])
pc = np.array([d.value for d in me.attributes['piece'].data]) if 'piece' in me.attributes else np.zeros(len(co), int)
J = {x.name: np.array(tuple(arm.matrix_world @ x.head_local)) for x in arm.data.bones}
np.savez(argv[1].replace('.png', '.npz'), co=co, piece=pc, jn=np.array(list(J.keys())), jp=np.array(list(J.values())))
print('SECTION saved')
