"""Transfer the full-silhouette Meshy body UVs; preserve the selected head UVs, rig and actions."""
import bpy,sys,os,json,hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector,kdtree
P=Path(__file__).resolve().parents[1]
src_blend=str(P/'work/anim_uv.blend');job=str(P/'meshy/body_retexture_v2');out=str(P/'work/textured_master.blend');LAYER='UVMap'
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src_blend))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data; LAYER=me.uv_layers.active.name
rig.animation_data_create(); rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=os.path.join(os.path.abspath(job), 'model_urls_glb.glb'))
src = max((o for o in bpy.data.objects if o not in before and o.type == 'MESH'), key=lambda o: len(o.data.polygons))
S = np.array([tuple(src.matrix_world @ v.co) for v in src.data.vertices])
T = np.array([tuple(body.matrix_world @ v.co) for v in me.vertices])
hd = np.array([p.material_index for p in me.polygons])
polys = [p for p in me.polygons if hd[p.index] == 0]
# the body upload is the WHOLE mesh: fit on all of it (a box of the non-head faces is shorter when the scalp is in the
# head set - goblin: 196 mm mismatch); the head upload is the head faces alone
Tsub = T
scale = (Tsub.max(0) - Tsub.min(0)).max() / (S.max(0) - S.min(0)).max()
S = S * scale + ((Tsub.max(0) + Tsub.min(0)) / 2 - (S.max(0) + S.min(0)) / 2 * scale)
suv = src.data.uv_layers.active.data
tree = kdtree.KDTree(len(src.data.polygons))
for p in src.data.polygons:
    tree.insert(Vector(S[list(p.vertices)].mean(0)), p.index)
tree.balance()
if LAYER not in me.uv_layers:
    me.uv_layers.new(name=LAYER)
tuv = me.uv_layers[LAYER].data
worst, mism = 0.0, 0
for p in polys:
    c = Vector(T[list(p.vertices)].mean(0))
    _, si, d = tree.find(c)
    worst = max(worst, d)
    sp = src.data.polygons[si]
    if len(sp.vertices) != len(p.vertices):
        mism += 1
    sco = [S[v] for v in sp.vertices]
    for li, vi in zip(p.loop_indices, p.vertices):
        k = int(np.argmin([np.linalg.norm(T[vi] - x) for x in sco]))
        tuv[li].uv = suv[sp.loop_indices[k]].uv
(P/'work/body_uv_transfer.json').write_text(json.dumps({'max_centroid_error':worst,'corner_mismatches':mism,'body_faces':len(polys),'source_faces':len(src.data.polygons)},indent=2))
print('UVTRANSFER', LAYER, 'faces ours', len(polys), 'meshy', len(src.data.polygons), 'worst centroid mismatch mm',
      round(worst * 1000, 2), 'corner-count mismatches', mism)
assert worst < .001 and mism == 0, f'UV mismatch {worst*1000:.3f} mm, {mism} faces'
for o in list(bpy.data.objects):
    if o not in before:
        bpy.data.objects.remove(o, do_unlink=True)
me.uv_layers.active = me.uv_layers[LAYER]
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
