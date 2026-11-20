"""Piece labels of the batch I master (../mm7_m282_claude/work/anim_v2.blend, read only; Body 'piece' attribute:
0 skin, 5/6 hands, the 17 hair snakes, quiver, eyes, studs, rings, collar, string) plus the string tube
(StringMesh, label 99) -> work/master_pieces.npz (rest positions, labels); map_pieces.py maps them onto mesh_in."""
import os, bpy
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, '..', 'mm7_m282_claude', 'work', 'anim_v2.blend'))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']
if rig.animation_data:
    rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()
me = body.data
pv = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
P = np.array([tuple(body.matrix_world @ v.co) for v in me.vertices])
print('MASTER verts', len(P), 'pieces', np.unique(pv).tolist(), 'objects', [o.name for o in bpy.data.objects if o.type == 'MESH'])
S = bpy.data.objects.get('StringMesh')
if S:
    SP = np.array([tuple(S.matrix_world @ v.co) for v in S.data.vertices]); print('STRING verts', len(SP), 'parent', S.parent and S.parent.name)
    P = np.concatenate([P, SP]); pv = np.concatenate([pv, np.full(len(SP), 99, np.int32)])
np.savez(os.path.join(HERE, 'work', 'master_pieces.npz'), P=P, piece=pv)
print('SAVED', len(P))
