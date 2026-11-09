"""Rest-pose triangles (UV, 3D position, Meshy piece id) of the beholder in work/uv_master.blend -> work/uv3d.npz.
piece: connected piece of the Smart Topology return (work/raw_st1.npz; see rig_plan.py)."""
import bpy, os, numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work/uv_master.blend'))
rig = bpy.data.objects['Beholder_Rig']; rig.animation_data.action = None
for b in rig.pose.bones: b.matrix_basis.identity()
me = bpy.data.objects['Beholder'].data; me.calc_loop_triangles(); uv = me.uv_layers.active.data
U = np.array([[tuple(uv[l].uv) for l in t.loops] for t in me.loop_triangles], dtype=np.float32)
Xs = np.array([[tuple(me.vertices[v].co) for v in t.vertices] for t in me.loop_triangles], dtype=np.float32)
piece = np.load(os.path.join(HERE, 'work/piece_master.npy'))   # piece_map.py (the eyeball split reordered vertices)
part = np.array([piece[t.vertices[0]] for t in me.loop_triangles], dtype=np.int32)
np.savez(os.path.join(HERE, 'work', 'uv3d.npz'), uv=U, xyz=Xs, part=part)
print('DUMPED', len(U))
