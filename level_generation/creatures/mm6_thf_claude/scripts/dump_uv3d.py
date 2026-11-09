"""Dump rest-pose triangles (UV, 3D position, part) of the Thief body to work/uv3d.npz for texture composition.
Run on work/rig_v2.blend (body UVs before the head split): blender --background work/rig_v2.blend --python dump_uv3d.py"""
import bpy, sys, os, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
rig = bpy.data.objects['Thief_Rig']
rig.animation_data_create()
rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()
obj = bpy.data.objects['Thief']
me = obj.data
me.calc_loop_triangles()
uv = me.uv_layers.active.data
part = np.zeros(len(me.polygons), dtype=np.int32)
me.attributes['part'].data.foreach_get('value', part)
tris = me.loop_triangles
U = np.array([[tuple(uv[l].uv) for l in t.loops] for t in tris], dtype=np.float32)
X = np.array([[tuple(obj.matrix_world @ me.vertices[v].co) for v in t.vertices] for t in tris], dtype=np.float32)
P = np.array([part[t.polygon_index] for t in tris], dtype=np.int32)
np.savez(os.path.join(common.WORK, 'uv3d.npz'), uv=U, xyz=X, part=P, parts=np.array(json.loads(bpy.context.scene['thf_parts'])))
print('DUMPED', len(tris))
