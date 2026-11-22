"""Rest-pose triangles of the guard: UV, 3D position, face part and bone (segment.py labels), face normal ->
work/uv3d.npz (compose.py rasterises them)."""
import bpy, os, numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'rig_uv.blend'))
rig = bpy.data.objects['Guard_Rig']
if rig.animation_data: rig.animation_data.action = None
for b in rig.pose.bones: b.matrix_basis.identity()
me = bpy.data.objects['Guard'].data
fp = np.zeros(len(me.polygons), np.int32); me.attributes['part'].data.foreach_get('value', fp)
fb = np.zeros(len(me.polygons), np.int32); me.attributes['bone'].data.foreach_get('value', fb)
me.calc_loop_triangles(); uv = me.uv_layers.active.data
tris = list(me.loop_triangles)
U = np.array([[tuple(uv[l].uv) for l in t.loops] for t in tris], dtype=np.float32)
Xs = np.array([[tuple(me.vertices[v].co) for v in t.vertices] for t in tris], dtype=np.float32)
part = np.array([fp[t.polygon_index] for t in tris], dtype=np.int32)
bone = np.array([fb[t.polygon_index] for t in tris], dtype=np.int32)
nrm = np.array([tuple(t.normal) for t in tris], dtype=np.float32)
np.savez(os.path.join(HERE, 'work', 'uv3d.npz'), uv=U, xyz=Xs, part=part, bone=bone, normal=nrm)
print('DUMPED', len(U), 'parts', np.bincount(part).tolist())
