"""Per-vertex labels of the production master (../mm7_m294_claude/work/rig_v6.blend, read only): rest positions and
the point attributes 'garment' and 'piece' -> work/master_labels.npz. make_groups.py matches them to the source faces
(the GLB carries no part labels). Usage: blender -b -P master_labels.py"""
import os, bpy, numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, '..', 'mm7_m294_claude', 'work', 'rig_v6.blend'))
o = bpy.data.objects['Body']; me = o.data
co = np.array([tuple(o.matrix_world @ v.co) for v in me.vertices])
out = {'co': co}
for n in ('garment', 'piece'):
    a = np.zeros(len(me.vertices), np.int32); me.attributes[n].data.foreach_get('value', a); out[n] = a
np.savez(os.path.join(HERE, 'work', 'master_labels.npz'), **out)
print('MASTER', len(co), 'tris', sum(len(p.vertices) - 2 for p in me.polygons), 'garments', sorted(set(out['garment'].tolist())))
