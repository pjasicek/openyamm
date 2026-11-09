"""Rest-pose triangles (UV, 3D position) of the rat mesh -> work/uv3d.npz."""
import bpy, os, numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rig = bpy.data.objects['Bat_Rig']; rig.animation_data.action = None
for b in rig.pose.bones: b.matrix_basis.identity()
me = bpy.data.objects['Bat'].data; me.calc_loop_triangles(); uv = me.uv_layers.active.data
U = np.array([[tuple(uv[l].uv) for l in t.loops] for t in me.loop_triangles], dtype=np.float32)
Xs = np.array([[tuple(me.vertices[v].co) for v in t.vertices] for t in me.loop_triangles], dtype=np.float32)
np.savez(os.path.join(HERE, 'work', 'uv3d.npz'), uv=U, xyz=Xs, part=np.zeros(len(U), dtype=np.int32))
print('DUMPED', len(U))
