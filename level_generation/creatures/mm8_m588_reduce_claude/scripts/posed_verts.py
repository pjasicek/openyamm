"""Posed source vertices (work/source.blend Body, the vertex order of dump_mesh.py) at every 2nd frame of every clip
-> work/posed_verts.npz (clip:frame labels, positions F x V x 3). Usage: blender -b -P posed_verts.py"""
import os, bpy
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'source.blend'))
body = bpy.data.objects['Body']; rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE'); sc = bpy.context.scene
labels, P = [], []
for act in bpy.data.actions:
    rig.animation_data.action = act
    if act.slots:
        rig.animation_data.action_slot = act.slots[0]
    a, b = (int(x) for x in act.frame_range)
    for fr in range(a, b + 1, 2):
        sc.frame_set(fr); e = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = e.to_mesh()
        P.append(np.array([body.matrix_world @ v.co for v in m.vertices], np.float32)); e.to_mesh_clear()
        labels.append(f'{act.name}:{fr}')
np.savez(os.path.join(HERE, 'work', 'posed_verts.npz'), labels=np.array(labels), P=np.array(P))
print('POSED', len(labels), 'frames')
