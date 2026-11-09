"""Copy Meshy's own UV layout (retexture with enable_original_uv: false) onto our rigged body, after
mm6_wdm_claude/scripts/transfer_uv.py: the returned mesh has the same faces in its own placement; it is fitted back by
bounding box, each of our faces is matched to the returned face with the nearest centroid, and each corner takes the
UV of the nearest returned corner of that face. Writes layer 'UVMap' (the head faces keep their own 'HeadUV').
Reports the worst centroid mismatch and face-count agreement. Args: -- <in blend> <meshy job dir> <out blend>"""
import bpy, sys, os, json
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
ds = []; matched = set(); worst_corner = 0.0; repaired = []
for p in polys:
    c = Vector(T[list(p.vertices)].mean(0))
    _, si, d = tree.find(c)
    if LAYER=='HeadUV':
        options=[]
        for _,candidate,cd in tree.find_range(c,.0001):
            sp=src.data.polygons[candidate];sco=[S[v] for v in sp.vertices]
            error=max((tuv[li].uv-suv[sp.loop_indices[int(np.argmin([np.linalg.norm(T[vi]-x) for x in sco]))]].uv).length for li,vi in zip(p.loop_indices,p.vertices))
            options.append((error,candidate,cd))
        if not options or min(options)[0]>.0001:
            repaired.append(p.index);continue
        _,si,d=min(options)
        if si in matched:
            repaired.append(p.index);continue
    if d >= .0001:
        if LAYER=='HeadUV':
            # This job retains the upload UVs; omitted hair faces keep their original charts.
            repaired.append(p.index);continue
        assert p.index in (767,5008,10026), ('Unreviewed missing body face',p.index,d)
        sp=src.data.polygons[si];points=S[list(sp.vertices)];uvs=np.array([tuple(suv[li].uv) for li in sp.loop_indices]);basis=np.stack([points[1]-points[0],points[2]-points[0]],axis=1)
        for li,vi in zip(p.loop_indices,p.vertices):
            ab=np.linalg.lstsq(basis,T[vi]-points[0],rcond=None)[0];value=uvs[0]+ab@(uvs[1:]-uvs[0]);assert value.min()>=0 and value.max()<=1
            tuv[li].uv=value
        repaired.append(p.index);continue
    worst = max(worst, d); ds.append(d)
    assert si not in matched, 'UV face correspondence is not one-to-one'
    matched.add(si)
    sp = src.data.polygons[si]
    if len(sp.vertices) != len(p.vertices):
        mism += 1
    sco = [S[v] for v in sp.vertices]
    for li, vi in zip(p.loop_indices, p.vertices):
        k = int(np.argmin([np.linalg.norm(T[vi] - x) for x in sco]))
        worst_corner = max(worst_corner, float(np.linalg.norm(T[vi]-sco[k])))
        value=suv[sp.loop_indices[k]].uv
        if LAYER=='HeadUV':
            assert (tuv[li].uv-value).length<.0001,('Head UV changed',p.index)
        else:tuv[li].uv=value
assert mism == 0 and worst < 0.0001 and worst_corner < 0.0001, 'Texture return changed geometry'
# Body retexture may omit head faces; the independently painted HeadUV supplies all of them.
assert len(matched) + len(repaired) == len(polys)
assert repaired == ([13572] if LAYER=='HeadUV' else [767,5008,10026]), ('Unexpected texture-return omission',LAYER,repaired)
print('OMITTED_FACES',LAYER,repaired)
json.dump({'missing_faces':repaired,'matched_faces':len(matched),'max_corner_error_m':worst_corner},open(os.path.join(os.path.dirname(out),'transfer_'+LAYER+'.json'),'w'),indent=2)
print('UV source faces', len(src.data.polygons), 'used faces', len(polys))
ds = np.array(ds) * 1000
print('UVTRANSFER mismatch mm p50/p99', round(float(np.median(ds)), 2), round(float(np.percentile(ds, 99)), 2), 'faces > 2 mm', int((ds > 2).sum()), '> 5 mm', int((ds > 5).sum()))
print('UVTRANSFER', LAYER, 'faces ours', len(polys), 'meshy', len(src.data.polygons), 'worst centroid mismatch mm',
      round(worst * 1000, 2), 'corner-count mismatches', mism)
for o in list(bpy.data.objects):
    if o not in before:
        bpy.data.objects.remove(o, do_unlink=True)
me.uv_layers.active = me.uv_layers['UVMap']
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
