"""Rest-pose body triangles (material slot 0; UV, 3D position, part: 1 = wing membrane) of the demon mesh ->
work/uv3d.npz. The wing flag comes from the point attribute 'wing' (grafted mesh) or work/wing_mask.npy."""
import bpy, os, numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rig = bpy.data.objects['Demon_Rig']
if rig.animation_data:
    rig.animation_data.action = None
for b in rig.pose.bones: b.matrix_basis.identity()
me = bpy.data.objects['Demon'].data; me.calc_loop_triangles(); uv = me.uv_layers.active.data
att = me.attributes.get('wing')
if att:
    wing = np.zeros(len(me.vertices), bool); att.data.foreach_get('value', wing)
else:
    wing = np.load(os.path.join(HERE, 'work', 'wing_mask.npy'))
tris = [t for t in me.loop_triangles if t.material_index == 0]
U = np.array([[tuple(uv[l].uv) for l in t.loops] for t in tris], dtype=np.float32)
Xs = np.array([[tuple(me.vertices[v].co) for v in t.vertices] for t in tris], dtype=np.float32)
part = np.array([int(sum(wing[v] for v in t.vertices) >= 2) for t in tris], dtype=np.int32)  # 1 = wing
np.savez(os.path.join(HERE, 'work', 'uv3d.npz'), uv=U, xyz=Xs, part=part)
print('DUMPED', len(U))
