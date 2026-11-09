"""Rest-pose body triangles of the mage (UV in the packed runtime atlas: u * body_u from textures/atlas_pack.json,
3D position) -> work/uv3d_body.npz for compose-style rasterisation. Head faces (own texture set) get part -1.
Run on work/rig_v8.blend."""
import bpy, os, json, numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
pack = json.load(open(os.path.join(HERE, 'textures', 'atlas_pack.json')))
rig = bpy.data.objects['Mage_Rig']
if rig.animation_data:
    rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
me = bpy.data.objects['Mage'].data; me.calc_loop_triangles(); uv = me.uv_layers.active.data
head = me.attributes['head'].data
U = np.array([[tuple(uv[l].uv) for l in t.loops] for t in me.loop_triangles], dtype=np.float32)
U[..., 0] *= pack['body_u']
X = np.array([[tuple(me.vertices[v].co) for v in t.vertices] for t in me.loop_triangles], dtype=np.float32)
P = np.array([-1 if head[t.polygon_index].value else 0 for t in me.loop_triangles], dtype=np.int32)
np.savez(os.path.join(HERE, 'work', 'uv3d_body.npz'), uv=U, xyz=X, part=P)
print('DUMPED', len(U), 'head tris', int((P < 0).sum()))
