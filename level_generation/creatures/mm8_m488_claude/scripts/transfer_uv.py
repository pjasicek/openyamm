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
polys = [p for p in me.polygons if LAYER != 'HeadUV' or hd[p.index] == 1]
Tsub = T[sorted({v for p in polys for v in p.vertices})] if LAYER == 'HeadUV' else T
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
print('MATCH_COUNTS',LAYER,len(polys),len(src.data.polygons),'scale',scale,flush=True)
worst, mism = 0.0, 0
matched=set();corner_worst=0;duplicates=[];omitted=[]
vertex_tree=kdtree.KDTree(len(S));vertex_uvs={}
for i,co in enumerate(S):vertex_tree.insert(Vector(co),i)
vertex_tree.balance()
for face in src.data.polygons:
 for vi,li in zip(face.vertices,face.loop_indices):vertex_uvs.setdefault(vi,set()).add(tuple(suv[li].uv))
for p in polys:
    c = Vector(T[list(p.vertices)].mean(0))
    candidates=tree.find_n(c,8)
    def error(candidate):
        face=src.data.polygons[candidate[1]]
        distances=np.linalg.norm(T[list(p.vertices)][:,None,:]-S[list(face.vertices)][None,:,:],axis=2)
        return max(distances.min(0).max(),distances.min(1).max())
    _, si, d = min(candidates,key=error)
    if error((None,si,d))>.0001:
        # Meshy omitted four tiny original faces; retain them and use their surviving exact vertex UVs.
        import itertools
        choices=[]
        for vi in p.vertices:
            matches=vertex_tree.find_range(Vector(T[vi]),.000002)
            assert matches,(p.index,vi,'no exact returned vertex')
            choices.append(sorted({uv for _,j,_ in matches for uv in vertex_uvs[j]}))
        candidates=list(itertools.product(*choices))
        def uv_cost(uv):
            uv=np.array(uv);delta=uv-np.roll(uv,1,axis=0)
            return float((delta*delta).sum())
        selected=min(candidates,key=uv_cost)
        for li,uv in zip(p.loop_indices,selected):tuv[li].uv=uv
        omitted.append(p.index)
        continue
    worst = max(worst, d)
    if si in matched:duplicates.append([p.index,si])
    matched.add(si)
    sp = src.data.polygons[si]
    if len(sp.vertices) != len(p.vertices):
        mism += 1
    sco = [S[v] for v in sp.vertices]
    for li, vi in zip(p.loop_indices, p.vertices):
        k = int(np.argmin([np.linalg.norm(T[vi] - x) for x in sco]))
        corner_worst=max(corner_worst,float(np.linalg.norm(T[vi]-sco[k])))
        tuv[li].uv = suv[sp.loop_indices[k]].uv
assert worst<.0001 and corner_worst<.0001 and mism==0,(worst,corner_worst,mism)
assert len(duplicates)<=5 and len(omitted)<=5,(duplicates,omitted)
import json
from pathlib import Path
(Path(__file__).resolve().parents[1]/'review'/('uv_transfer_'+LAYER+'.json')).write_text(json.dumps(dict(faces=len(polys),returned_faces=len(src.data.polygons),max_centroid_mm=worst*1000,max_corner_mm=corner_worst*1000,coincident_face_matches=duplicates,omitted_faces_exact_corner_uv=omitted),indent=2)+'\n')
print('UVTRANSFER', LAYER, 'faces ours', len(polys), 'meshy', len(src.data.polygons), 'worst centroid mismatch mm',
      round(worst * 1000, 2), 'corner-count mismatches', mism)
for o in list(bpy.data.objects):
    if o not in before:
        bpy.data.objects.remove(o, do_unlink=True)
me.uv_layers.active = me.uv_layers['UVMap']
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
