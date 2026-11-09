"""Rest-pose triangles (UV, 3D position, dominant bone) of the bat in work/uv_master.blend -> work/uv3d.npz."""
import bpy, os, numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work/uv_master.blend'))
rig = bpy.data.objects['Bat_Rig']; rig.animation_data.action = None
for b in rig.pose.bones: b.matrix_basis.identity()
me = bpy.data.objects['Bat'].data; me.calc_loop_triangles(); uv = me.uv_layers.active.data
U = np.array([[tuple(uv[l].uv) for l in t.loops] for t in me.loop_triangles], dtype=np.float32)
Xs = np.array([[tuple(me.vertices[v].co) for v in t.vertices] for t in me.loop_triangles], dtype=np.float32)
mesh = bpy.data.objects['Bat']; vg = {g.index: g.name for g in mesh.vertex_groups}
dom = [vg.get(max(v.groups, key=lambda g: g.weight).group, '') if v.groups else '' for v in me.vertices]
cls = np.array([1 if n.startswith(('UpperArm', 'ForeArm', 'Finger')) else 2 if n.startswith(('Head', 'Ear')) else 0
                for n in dom])
part = np.array([np.bincount(cls[list(t.vertices)], minlength=3).argmax() for t in me.loop_triangles], dtype=np.int32)
np.savez(os.path.join(HERE, 'work', 'uv3d.npz'), uv=U, xyz=Xs, part=part)  # part: 0 body, 1 wing, 2 head/ears
print('DUMPED', len(U))
