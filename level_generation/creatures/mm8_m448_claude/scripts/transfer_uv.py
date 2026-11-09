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
import bmesh
bm=bmesh.new();bm.from_mesh(me)
degenerate=[f for f in bm.faces if f.calc_area()<1e-12]
print('UV cleanup degenerate faces',len(degenerate),flush=True)
bmesh.ops.delete(bm,geom=degenerate,context='FACES_ONLY');bm.to_mesh(me);bm.free()
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
# the body upload is the WHOLE mesh: fit on all of it (a box of the non-head faces is shorter when the scalp is in the
# head set - goblin: 196 mm mismatch); the head upload is the head faces alone
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
worst, mism = 0.0, 0
ds = []; corner_errors = []; matched = []; used=set(); uv_errors=[]; collapsed=[]
for p in polys:
    c = Vector(T[list(p.vertices)].mean(0))
    tp=T[list(p.vertices)]
    tn=np.cross(tp[1]-tp[0],tp[2]-tp[0]);tn/=max(np.linalg.norm(tn),1e-20)
    candidates=[]
    for _, candidate, distance in tree.find_n(c,12):
        if candidate in used and LAYER != 'HeadUV':continue
        spoints=S[list(src.data.polygons[candidate].vertices)]
        sn=np.cross(spoints[1]-spoints[0],spoints[2]-spoints[0]);sn/=max(np.linalg.norm(sn),1e-20)
        error=max(min(np.linalg.norm(v-x) for x in spoints) for v in tp)
        candidates.append((error+1e-7*(1-float(tn@sn)),candidate,distance))
    assert candidates, (LAYER,p.index,len(polys),len(src.data.polygons),p.area)
    _,si,d=min(candidates);used.add(si)
    worst = max(worst, d); ds.append(d); matched.append(si)
    sp = src.data.polygons[si]
    if len(sp.vertices) != len(p.vertices):
        mism += 1
    sco = [S[v] for v in sp.vertices]
    corner_map=[int(np.argmin([np.linalg.norm(T[vi]-x) for x in sco])) for vi in p.vertices]
    if len(set(corner_map))<3:
        assert LAYER=='HeadUV'
        collapsed.append(p.index)
        continue
    for li, vi in zip(p.loop_indices, p.vertices):
        k = int(np.argmin([np.linalg.norm(T[vi] - x) for x in sco]))
        corner_errors.append(float(np.linalg.norm(T[vi] - sco[k])))
        if LAYER=='HeadUV':
            uv_errors.append((tuv[li].uv-suv[sp.loop_indices[k]].uv).length)
        else:
            tuv[li].uv = suv[sp.loop_indices[k]].uv
print('CORRESPONDENCE',LAYER,len(polys),len(src.data.polygons),len(set(matched)),max(corner_errors),flush=True)
assert mism == 0
assert len(set(matched)) == len(matched) or LAYER=='HeadUV'
assert max(corner_errors) < .0002, max(corner_errors)
assert len(collapsed)<=2,collapsed
assert not uv_errors or max(uv_errors)<.0001,max(uv_errors) if uv_errors else None
print('HEAD ORIGINAL UV verification',len(uv_errors),max(uv_errors,default=0),'collapsed sliver faces preserved',collapsed,flush=True)
import json
from pathlib import Path
(Path(__file__).resolve().parents[1]/'work'/('uv_transfer_'+LAYER+'.json')).write_text(json.dumps({'faces':len(polys),'returned_faces':len(src.data.polygons),'max_corner_error_m':max(corner_errors),'max_centroid_error_m':worst,'unique_face_correspondence':len(set(matched))==len(matched),'reused_returned_faces':len(matched)-len(set(matched)),'original_head_uv_preserved':LAYER=='HeadUV','max_original_uv_error':max(uv_errors,default=0),'head_sliver_faces_omitted_by_meshy':collapsed},indent=2))
ds = np.array(ds) * 1000
print('UVTRANSFER mismatch mm p50/p99', round(float(np.median(ds)), 2), round(float(np.percentile(ds, 99)), 2), 'faces > 2 mm', int((ds > 2).sum()), '> 5 mm', int((ds > 5).sum()))
print('UVTRANSFER', LAYER, 'faces ours', len(polys), 'meshy', len(src.data.polygons), 'worst centroid mismatch mm',
      round(worst * 1000, 2), 'corner-count mismatches', mism)
for o in list(bpy.data.objects):
    if o not in before:
        bpy.data.objects.remove(o, do_unlink=True)
me.uv_layers.active = me.uv_layers['UVMap']
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
