"""Production master (../mm7_m332_claude/work/rig_v6.blend, rest pose) -> work/master_pieces.npz: rest vertex positions
and the Smart Topology 'piece' attribute per vertex, to label the GLB's faces by piece (m332_pieces.py). Args: none"""
import bpy, os
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(os.path.dirname(HERE), 'mm7_m332_claude', 'work', 'rig_v6.blend'))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
rig.animation_data_create(); rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
co = np.array([tuple(body.matrix_world @ v.co) for v in me.vertices])
pv = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
np.savez(os.path.join(HERE, 'work', 'master_pieces.npz'), co=co, piece=pv)
print('MASTER', len(co), 'verts, pieces', sorted(set(pv.tolist())))
