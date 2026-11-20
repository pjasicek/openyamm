"""Copy Meshy's own UV layout (retexture with enable_original_uv: false) onto our rigged body, after
mm6_wdm_claude/scripts/transfer_uv.py: the returned mesh has the same faces in its own placement; it is fitted back by
bounding box, each of our faces is matched to the returned face with the nearest centroid, and each corner takes the
UV of the nearest returned corner of that face. Writes layer 'UVMap' (the head faces keep their own 'HeadUV').
Reports the worst centroid mismatch and face-count agreement. Args: -- <in blend> <meshy job dir> <out blend>"""
import bpy, sys, os
import numpy as np
from mathutils import Vector, kdtree
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
import json
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
Tsub = T[sorted({v for p in polys for v in p.vertices})]
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
pv=[a.value for a in me.attributes["piece"].data]
surface=BVHTree.FromPolygons([tuple(x) for x in S],[tuple(p.vertices) for p in src.data.polygons])
changed=[];surface_worst=0.0
for p in polys:
    c = Vector(T[list(p.vertices)].mean(0))
    _, si, d = tree.find(c)
    worst = max(worst, d)
    if d>.0005:
        assert pv[p.vertices[0]] in [200,201,202], 'Unexpected non-fauld topology change'
        _,_,si,sd=surface.find_nearest(c);surface_worst=max(surface_worst,sd);changed.append(p.index)
        assert sd<.025, 'Fauld texture reprojection exceeds the 2.5 cm overlapping plate band'
        sp=src.data.polygons[si];assert len(sp.vertices)==3
        uv3=[Vector((*suv[l].uv,0)) for l in sp.loop_indices]
        for li,vi in zip(p.loop_indices,p.vertices):
            q=barycentric_transform(Vector(T[vi]),*[Vector(S[k]) for k in sp.vertices],*uv3)
            tuv[li].uv=(q.x,q.y)
    else:
        sp=src.data.polygons[si]
        assert len(sp.vertices)==len(p.vertices)
        sco=[S[v] for v in sp.vertices]
        for li,vi in zip(p.loop_indices,p.vertices):
            k=int(np.argmin([np.linalg.norm(T[vi]-x) for x in sco]));tuv[li].uv=suv[sp.loop_indices[k]].uv
print('UVTRANSFER', LAYER, 'faces ours', len(polys), 'meshy', len(src.data.polygons), 'worst centroid mismatch mm',
      round(worst * 1000, 2), 'corner-count mismatches', mism)
assert len(changed)==74 and len(polys)-len(src.data.polygons)==92, 'Unexpected retexture revision'
json.dump({'direct_faces':len(polys)-len(changed),'fauld_barycentric_faces':len(changed),'max_fauld_surface_distance_m':surface_worst},open(os.path.join(os.path.dirname(os.path.dirname(__file__)),'work/uv_transfer.json'),'w'),indent=2)
for o in list(bpy.data.objects):
    if o not in before:
        bpy.data.objects.remove(o, do_unlink=True)
me.uv_layers.active = me.uv_layers['UVMap']
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
