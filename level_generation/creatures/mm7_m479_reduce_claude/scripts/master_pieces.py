"""Dump the production master's rest vertices with its 'piece' and 'part' labels (../mm7_m479_claude/work/anim_v1.blend,
read only; the same vertices as the exported LOD0) -> work/master_pieces.npz (co, piece, part).
part: 0 bark, 1 upper tooth, 2 lower tooth, 3 eye; piece 15 = lower lip, 20 = spire, 0 = main skin. Args: none"""
import os, bpy, numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, '..', 'mm7_m479_claude', 'work', 'anim_v1.blend'))
b = bpy.data.objects['Body']; me = b.data
co = np.array([tuple(b.matrix_world @ v.co) for v in me.vertices])
pv = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
pa = np.zeros(len(me.vertices), np.int32); me.attributes['part'].data.foreach_get('value', pa)
np.savez(os.path.join(HERE, 'work', 'master_pieces.npz'), co=co, piece=pv, part=pa)
print('MASTER verts', len(co), 'pieces', len(set(pv.tolist())), 'parts', np.bincount(pa).tolist())
