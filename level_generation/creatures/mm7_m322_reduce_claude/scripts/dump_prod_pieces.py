"""Rest positions and the 'piece' attribute (Smart Topology shell) of the production master's Body
(../mm7_m322_claude/work/rig_v6.blend) -> work/prod_pieces.npz, for m322_pieces.py. Args: -- <rig_v6.blend>"""
import bpy, sys, os
import numpy as np
src = sys.argv[sys.argv.index('--') + 1]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; b = bpy.data.objects['Body']
rig.animation_data_create(); rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
ev = b.evaluated_get(bpy.context.evaluated_depsgraph_get()); me = ev.to_mesh()
co = np.array([tuple(b.matrix_world @ v.co) for v in me.vertices]); ev.to_mesh_clear()
pv = np.zeros(len(b.data.vertices), np.int32); b.data.attributes['piece'].data.foreach_get('value', pv)
np.savez(os.path.join(HERE, 'work', 'prod_pieces.npz'), co=co, piece=pv)
print('PRODPIECES', len(co), 'pieces', len(set(pv.tolist())), 'z', round(float(co[:, 2].min()), 4), round(float(co[:, 2].max()), 4))
