"""One smooth subdivision of the hands (Body faces beyond the wrist): curled fingers were ~70 triangles each and
showed flat facets in a fist. UVs and skin weights are interpolated by the subdivision; finger weights are rebuilt
afterwards by refit_hands.py. Custom normals: every corner outside the hands keeps its normal, hand corners get
smooth vertex normals. Run before refit_hands.py."""
import bpy, bmesh, json
import numpy as np
from mathutils import Vector

mesh = bpy.data.objects['Peasant']; me = mesh.data; rig = bpy.data.objects['Peasant_Rig']
if rig.animation_data:
    rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()
PARTS = json.loads(bpy.context.scene['pfem_parts'])
BODY = PARTS.index('Body')
before = sum(len(p.vertices) - 2 for p in me.polygons)
# keep the current corner normals in a temporary attribute that bmesh carries through untouched faces
cn = np.array([tuple(n.vector) for n in me.corner_normals], dtype=np.float32)
tmp = me.attributes.new('tmp_cn', 'FLOAT_VECTOR', 'CORNER')
tmp.data.foreach_set('vector', cn.ravel())
inv = mesh.matrix_world.inverted()
planes = []
for side in ('Left', 'Right'):
    fa = rig.data.bones[f'mixamorig:{side}ForeArm']
    head = inv @ (rig.matrix_world @ fa.head_local); tail = inv @ (rig.matrix_world @ fa.tail_local)
    planes.append((tail, (tail - head).normalized()))

bm = bmesh.new(); bm.from_mesh(me)
pl = bm.faces.layers.int.get('part')


tips = [inv @ Vector(f['tip']) for side in json.load(open(bpy.path.abspath('//hand_fit.json'))).values()
        for f in side.values()]


def in_hand(co):
    """Fingers and thumbs only (within 85 mm of a fingertip, past the wrist): the palm stays as it was."""
    return any((co - t).dot(a) > -0.005 and (co - t).length < 0.30 for t, a in planes) and \
        min((co - t).length for t in tips) < 0.085


hand_faces = {f for f in bm.faces if f[pl] == BODY and all(in_hand(v.co) for v in f.verts)}
edges = list({e for f in hand_faces for e in f.edges if all(lf in hand_faces for lf in e.link_faces)})
res = bmesh.ops.subdivide_edges(bm, edges=edges, cuts=1, use_grid_fill=True, smooth=0.35)
bm.faces.ensure_lookup_table()
bm.faces.index_update()
hand_idx = {f.index for f in bm.faces if f[pl] == BODY and all(in_hand(v.co) for v in f.verts)}
bm.to_mesh(me); bm.free()
me.update()
loops = np.zeros(len(me.loops) * 3, dtype=np.float32); me.attributes['tmp_cn'].data.foreach_get('vector', loops)
loops = loops.reshape(-1, 3)
vn = np.array([tuple(v.normal) for v in me.vertices], dtype=np.float32)
for p in me.polygons:
    if p.index in hand_idx:
        for li in p.loop_indices:
            loops[li] = vn[me.loops[li].vertex_index]
norm = np.linalg.norm(loops, axis=1, keepdims=True); loops = loops / np.maximum(norm, 1e-6)
me.normals_split_custom_set([tuple(n) for n in loops])
me.attributes.remove(me.attributes['tmp_cn'])
after = sum(len(p.vertices) - 2 for p in me.polygons)
bpy.ops.wm.save_mainfile()
print('SUBDIVIDED hands', len(hand_idx), 'faces; triangles', before, '->', after)
