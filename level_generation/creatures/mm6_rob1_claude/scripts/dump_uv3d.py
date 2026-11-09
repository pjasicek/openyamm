"""Rest-pose triangles (UV, 3D position, face 'part') of the robot mesh -> work/uv3d.npz."""
import bpy, os, numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rig = bpy.data.objects['Robot_Rig']; rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
me = bpy.data.objects['Robot'].data; me.calc_loop_triangles(); uv = me.uv_layers.active.data
part = me.attributes['part'].data
U = np.array([[tuple(uv[l].uv) for l in t.loops] for t in me.loop_triangles], dtype=np.float32)
Xs = np.array([[tuple(me.vertices[v].co) for v in t.vertices] for t in me.loop_triangles], dtype=np.float32)
P = np.array([part[t.polygon_index].value for t in me.loop_triangles], dtype=np.int32)
np.savez(os.path.join(HERE, 'work', 'uv3d.npz'), uv=U, xyz=Xs, part=P)
print('DUMPED', len(U))
