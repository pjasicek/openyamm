"""Copy Meshy's own UV layout (retexture with enable_original_uv: false) onto our rigged body, after
mm6_wdm_claude/scripts/transfer_uv.py: the returned mesh has the same faces in its own placement; it is fitted back by
bounding box, each of our faces is matched to the returned face with the nearest centroid, and each corner takes the
UV of the nearest returned corner of that face. Writes layer 'UVMap' (the head faces keep their own 'HeadUV').
Reports the worst centroid mismatch and face-count agreement. Args: -- <in blend> <meshy job dir> <out blend>"""
import bpy, sys, os
import numpy as np
from mathutils import Vector, kdtree
a_ = sys.argv[sys.argv.index('--') + 1:]
src_blend, job, out = a_[:3]
LAYER = a_[3] if len(a_) > 3 else 'UVMap'          # 'HeadUV': only the head faces, fitted to their own bbox
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src_blend))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
rig.animation_data_create(); rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=os.path.join(os.path.abspath(job), 'model_urls_glb.glb'))
src = max((o for o in bpy.data.objects if o not in before and o.type == 'MESH'), key=lambda o: len(o.data.polygons))
S = np.array([tuple(src.matrix_world @ v.co) for v in src.data.vertices])
T = np.array([tuple(body.matrix_world @ v.co) for v in me.vertices])
hd = np.zeros(len(me.polygons), np.int32); me.attributes['head'].data.foreach_get('value', hd)
polys = [p for p in me.polygons if (hd[p.index] == 1) == (LAYER == 'HeadUV')]
Tsub = T if LAYER == 'UVMap' else T[sorted({v for p in polys for v in p.vertices})]
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
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
surface = BVHTree.FromPolygons([tuple(v) for v in S], [tuple(p.vertices) for p in src.data.polygons])
vertex_tree = kdtree.KDTree(len(S))
vertex_uvs = {}
for face in src.data.polygons:
    for li, vi in zip(face.loop_indices, face.vertices):
        vertex_uvs.setdefault(vi, []).append(suv[li].uv.copy())
for i, point in enumerate(S):
    vertex_tree.insert(Vector(point), i)
vertex_tree.balance()
worst, mism, surface_error, retriangulated = 0.0, 0, 0.0, 0
for p in polys:
    c = Vector(T[list(p.vertices)].mean(0))
    _, si, d = tree.find(c)
    worst = max(worst, d)
    sp = src.data.polygons[si]
    if len(sp.vertices) != len(p.vertices):
        mism += 1
    sco = [S[v] for v in sp.vertices]
    if d > 0.0002:
        retriangulated += 1
    uv_centre = sum((suv[li].uv for li in sp.loop_indices), Vector((0, 0))) / len(sp.loop_indices)
    for li, vi in zip(p.loop_indices, p.vertices):
        k = int(np.argmin([np.linalg.norm(T[vi] - x) for x in sco]))
        if np.linalg.norm(T[vi] - sco[k]) < 0.00001:
            tuv[li].uv = suv[sp.loop_indices[k]].uv
            continue
        point, _, face_id, distance = surface.find_nearest(Vector(T[vi]))
        surface_error = max(surface_error, distance)
        assert distance < 0.00001, f'Returned surface changed by {distance} m'
        hits = vertex_tree.find_n(Vector(T[vi]), 16)
        candidates = [u for _, idx, dist in hits if dist < 0.00001 for u in vertex_uvs.get(idx, [])]
        if candidates:
            tuv[li].uv = min(candidates, key=lambda u: (u - uv_centre).length)
        else:
            source_face = src.data.polygons[face_id]
            points = [Vector(S[v]) for v in source_face.vertices]
            texels = [Vector((*suv[l].uv, 0)) for l in source_face.loop_indices]
            uv = barycentric_transform(point, *points, *texels)
            tuv[li].uv = uv.xy
print('UVTRANSFER', LAYER, 'faces ours', len(polys), 'meshy', len(src.data.polygons), 'worst centroid mismatch mm',
      round(worst * 1000, 2), 'corner-count mismatches', mism)
print('UV SURFACE max mm', surface_error * 1000, 'retriangulated faces', retriangulated)
assert retriangulated <= 10, 'Unexpected widespread retessellation'
assert mism == 0, 'UV corner counts differ'
for o in list(bpy.data.objects):
    if o not in before:
        bpy.data.objects.remove(o, do_unlink=True)
me.uv_layers.active = me.uv_layers['UVMap']
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
