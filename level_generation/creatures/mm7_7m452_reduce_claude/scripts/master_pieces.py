"""Dump the production master's rest vertices and 'piece' labels (../mm7_7m452_claude/work/rig_v6.blend, the same
vertices as the exported LOD0) -> work/master_pieces.npz (co, piece). Args: none"""
import os, bpy, numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, '..', 'mm7_7m452_claude', 'work', 'rig_v6.blend'))
b = bpy.data.objects['Body']; me = b.data
co = np.array([tuple(b.matrix_world @ v.co) for v in me.vertices])
pv = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
np.savez(os.path.join(HERE, 'work', 'master_pieces.npz'), co=co, piece=pv)
print('MASTER verts', len(co), 'pieces', sorted(set(pv.tolist())))
