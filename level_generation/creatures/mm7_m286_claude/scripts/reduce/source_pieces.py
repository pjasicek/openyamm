"""Source shell labels for the reduced mesh: open the source project's textured master (../mm7_m190_claude/work/rig_v6.blend,
read only, never saved) and write its Body rest positions with the 'piece' (Smart Topology shell) and 'garment' (weight
rule) point attributes -> work/source_pieces.npz. The runtime export drops both attributes; m190_pieces.py maps them onto
work/mesh_in.npz by position. Usage: blender -b -P source_pieces.py"""
import os, bpy
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'rig_v6.blend'))
body = bpy.data.objects['Body']; me = body.data; n = len(me.vertices)
co = np.array([(body.matrix_world @ v.co)[:] for v in me.vertices])
out = {'co': co}
for a in ('piece', 'garment'):
    x = np.zeros(n, np.int32); me.attributes[a].data.foreach_get('value', x); out[a] = x
np.savez(os.path.join(HERE, 'work', 'source_pieces.npz'), **out)
print('SOURCEPIECES', n, 'verts', sorted(set(out['piece'].tolist())), 'tris', sum(len(p.vertices) - 2 for p in me.polygons),
      'matrix', [round(x, 4) for r in body.matrix_world for x in r])
