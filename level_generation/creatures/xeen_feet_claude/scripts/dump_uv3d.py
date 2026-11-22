"""Rest triangles of the single textured foot (work/foot_uv.blend): UV, 3D position and part label
(0 skin Foot/Toes, 1 medial wing, 2 lateral wing) -> work/uv3d.npz."""
import bpy, os, numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'foot_uv.blend'))
ob = bpy.data.objects['Foot']; me = ob.data
names = [g.name for g in ob.vertex_groups]
PART = {'Foot': 0, 'Toes': 0, 'WingIn': 1, 'WingOut': 2}
dom = [PART[names[max(v.groups, key=lambda g: g.weight).group]] for v in me.vertices]
me.calc_loop_triangles(); uv = me.uv_layers.active.data
tris = list(me.loop_triangles)
U = np.array([[tuple(uv[l].uv) for l in t.loops] for t in tris], dtype=np.float32)
X = np.array([[tuple(me.vertices[v].co) for v in t.vertices] for t in tris], dtype=np.float32)
part = np.array([max(dom[v] for v in t.vertices) for t in tris], dtype=np.int32)
np.savez(os.path.join(HERE, 'work', 'uv3d.npz'), uv=U, xyz=X, part=part)
print('DUMPED', len(U), [int((part == k).sum()) for k in range(3)])
