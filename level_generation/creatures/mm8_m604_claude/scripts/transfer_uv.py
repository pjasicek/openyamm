"""Copy Meshy's own UV layout (retexture with enable_original_uv: false) onto our rigged body, after
mm6_wdm_claude/scripts/transfer_uv.py: the returned mesh has the same faces in its own placement; it is fitted back by
bounding box, each of our faces is matched to the returned face with the nearest centroid, and each corner takes the
UV of the nearest returned corner of that face. Writes layer 'UVMap' (the head faces keep their own 'HeadUV').
Reports the worst centroid mismatch and face-count agreement. Args: -- <in blend> <meshy job dir> <out blend>"""
import bpy, bmesh, sys, os
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
bm=bmesh.new(); bm.from_mesh(me)
bmesh.ops.triangulate(bm, faces=list(bm.faces), quad_method='FIXED', ngon_method='BEAUTY')
bm.to_mesh(me); bm.free(); me.update()
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
bad=[]
ds = []
for p in polys:
    c = Vector(T[list(p.vertices)].mean(0))
    _, si, d = tree.find(c)
    worst = max(worst, d); ds.append(d)
    sp = src.data.polygons[si]
    if d>0.0001:
        bad.append({'face':p.index,'piece':int(me.attributes['piece'].data[p.vertices[0]].value),'centroid_mm':d*1000,'area':p.area,'vertices':[list(T[v]) for v in p.vertices]})
    if len(sp.vertices) != len(p.vertices):
        mism += 1
    sco = [S[v] for v in sp.vertices]
    for li, vi in zip(p.loop_indices, p.vertices):
        k = int(np.argmin([np.linalg.norm(T[vi] - x) for x in sco]))
        tuv[li].uv = suv[sp.loop_indices[k]].uv
ds = np.array(ds) * 1000
print('UVTRANSFER mismatch mm p50/p99', round(float(np.median(ds)), 2), round(float(np.percentile(ds, 99)), 2), 'faces > 2 mm', int((ds > 2).sum()), '> 5 mm', int((ds > 5).sum()))
print('UVTRANSFER', LAYER, 'faces ours', len(polys), 'meshy', len(src.data.polygons), 'worst centroid mismatch mm',
      round(worst * 1000, 2), 'corner-count mismatches', mism)
if bad:
    # The texture service omitted eight invalid hole-fill triangles (body, belt and chain), all retained vertices match.
    assert LAYER == 'UVMap' and len(bad) == 8 and {x['piece'] for x in bad} == {0,2,23}, bad
    returned_used=set()
    for f in me.polygons:
        _,si,d=tree.find(Vector(T[list(f.vertices)].mean(0)))
        if d<0.0001:returned_used.add(si)
    assert len(returned_used)==len(src.data.polygons), ('Unexpected new return triangles',len(returned_used))
    bm=bmesh.new();bm.from_mesh(me);bm.faces.ensure_lookup_table()
    bmesh.ops.delete(bm,geom=[bm.faces[x['face']] for x in bad],context='FACES_ONLY')
    bm.to_mesh(me);bm.free();me.update()
    print('Removed eight omitted invalid cap faces; every return triangle maps to an existing source triangle')
assert mism == 0
import json
from pathlib import Path
Path(out).with_suffix('.uv.json').write_text(json.dumps({'layer':LAYER,'matched_faces':len(polys)-len(bad),'removed_invalid_caps':bad,'maximum_retained_centroid_error_m':max([d for d in ds/1000 if d<0.0001],default=0)},indent=2,default=float))
for o in list(bpy.data.objects):
    if o not in before:
        bpy.data.objects.remove(o, do_unlink=True)
me.uv_layers.active = me.uv_layers['UVMap']
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
