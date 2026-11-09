"""Copy Meshy's own UV layout (body retexture, enable_original_uv: false) onto the animated master (bar1 rule): the
return has our faces in its own placement; it is fitted back by bounding box, each of our faces is matched to the
returned face with the nearest centroid and each corner takes the UV of the nearest returned corner of that face.
Writes layer 'UVMap' on work/anim_v3h.blend -> work/anim_v4.blend (the head faces also keep 'HeadUV', whose texture
comes from the head retexture with our own layout). Reports the worst centroid mismatch."""
import bpy, json
import numpy as np
from pathlib import Path
from mathutils import Vector, kdtree
P = Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P / 'work' / 'anim_v3h.blend'))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Queen']; me = body.data
rig.animation_data_create(); rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=str(P / 'meshy' / 'body_retexture_v1' / 'model_urls_glb.glb'))
src = max((o for o in bpy.data.objects if o not in before and o.type == 'MESH'), key=lambda o: len(o.data.polygons))
S = np.array([tuple(src.matrix_world @ v.co) for v in src.data.vertices])
T = np.array([tuple(body.matrix_world @ v.co) for v in me.vertices])
scale = (T.max(0) - T.min(0)).max() / (S.max(0) - S.min(0)).max()
S = S * scale + ((T.max(0) + T.min(0)) / 2 - (S.max(0) + S.min(0)) / 2 * scale)
suv = src.data.uv_layers.active.data
tree = kdtree.KDTree(len(src.data.polygons))
for p in src.data.polygons:
    tree.insert(Vector(S[list(p.vertices)].mean(0)), p.index)
tree.balance()
if 'UVMap' not in me.uv_layers:
    me.uv_layers.new(name='UVMap')
tuv = me.uv_layers['UVMap'].data
worst, mism, dists = 0.0, 0, []
for p in me.polygons:
    c = Vector(T[list(p.vertices)].mean(0))
    _, si, d = tree.find(c)
    worst = max(worst, d); dists.append(d)
    sp = src.data.polygons[si]
    if len(sp.vertices) != len(p.vertices):
        mism += 1
    sco = [S[v] for v in sp.vertices]
    for li, vi in zip(p.loop_indices, p.vertices):
        k = int(np.argmin([np.linalg.norm(T[vi] - x) for x in sco]))
        tuv[li].uv = suv[sp.loop_indices[k]].uv
report = {'faces_ours': len(me.polygons), 'faces_meshy': len(src.data.polygons),
          'worst_centroid_mm': round(worst * 1000, 2), 'p99_centroid_mm': round(float(np.percentile(dists, 99)) * 1000, 2),
          'corner_count_mismatch': mism}
print('UVTRANSFER', json.dumps(report))
(P / 'work' / 'uv_transfer.json').write_text(json.dumps(report, indent=1))
for o in list(bpy.data.objects):
    if o not in before:
        bpy.data.objects.remove(o, do_unlink=True)
me.uv_layers.active = me.uv_layers['UVMap']
bpy.ops.wm.save_as_mainfile(filepath=str(P / 'work' / 'anim_v4.blend'))
