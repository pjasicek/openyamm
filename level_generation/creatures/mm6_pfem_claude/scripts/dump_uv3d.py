"""Dump rest-pose triangles (UV, 3D position, part) of Peasant to work/uv3d.npz for texture composition."""
import bpy, sys, os, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
rig = bpy.data.objects['Peasant_Rig']; rig.animation_data.action = None
for b in rig.pose.bones: b.matrix_basis.identity()
me = bpy.data.objects['Peasant'].data
me.calc_loop_triangles()
uv = me.uv_layers.active.data
part = np.zeros(len(me.polygons), dtype=np.int32); me.attributes['part'].data.foreach_get('value', part)
tris = me.loop_triangles
U = np.array([[tuple(uv[l].uv) for l in t.loops] for t in tris], dtype=np.float32)
X = np.array([[tuple(me.vertices[v].co) for v in t.vertices] for t in tris], dtype=np.float32)
Pp = np.array([part[t.polygon_index] for t in tris], dtype=np.int32)
fix = np.zeros(len(me.polygons), dtype=np.int32)
if 'uvfix' in me.attributes:
    me.attributes['uvfix'].data.foreach_get('value', fix)
Fx = np.array([fix[t.polygon_index] for t in tris], dtype=np.int32)
knife = json.loads(bpy.context.scene['pfem_knife'])
eyes = bpy.context.scene.get('pfem_eyes', '{}')
braid_info = bpy.context.scene.get('pfem_braid', '{}')
np.savez(os.path.join(common.WORK, 'uv3d.npz'), eyes=np.array(eyes), braid=np.array(braid_info), uv=U, xyz=X, part=Pp, uvfix=Fx, parts=np.array(json.loads(bpy.context.scene['pfem_parts'])),
         grip=np.array(knife['grip']), blade=np.array(knife['blade_dir']))
print('DUMPED', len(tris))
