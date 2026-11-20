"""Dump the production master's rest vertices and labels (../mm7_m438_claude/work/rig_v7.blend, read only; the same
vertices as the exported LOD0) -> work/master_pieces.npz (co, piece, garment, finger). Args: none"""
import os, bpy, numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, '..', 'mm7_m438_claude', 'work', 'rig_v7.blend'))
b = bpy.data.objects['Body']; me = b.data
co = np.array([tuple(b.matrix_world @ v.co) for v in me.vertices])
out = {'co': co}
for n in ('piece', 'garment', 'finger'):
    a = np.zeros(len(me.vertices), np.int32); me.attributes[n].data.foreach_get('value', a); out[n] = a
np.savez(os.path.join(HERE, 'work', 'master_pieces.npz'), **out)
print('MASTER verts', len(co), 'pieces', np.bincount(out['piece']).tolist(), 'garment', np.bincount(out['garment']).tolist(),
      'finger', np.bincount(out['finger']).tolist())
