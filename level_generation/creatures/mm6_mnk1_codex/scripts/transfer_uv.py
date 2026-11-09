"""Copy Meshy's own UV layout (retexture with enable_original_uv: false) onto our rigged body, after
mm6_wdm_claude/scripts/transfer_uv.py: the returned mesh has the same faces in its own placement; it is fitted back by
bounding box, each of our faces is matched to the returned face with the nearest centroid, and each corner takes the
UV of the nearest returned corner of that face. Writes layer 'UVMap' (the head faces keep their own 'HeadUV').
Reports the worst centroid mismatch and face-count agreement. Args: -- <in blend> <meshy job dir> <out blend>"""
import bpy, sys, os
HERE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from mathutils import Vector, kdtree
a_ = sys.argv[sys.argv.index('--') + 1:]
src_blend, job, out = a_[:3]
LAYER = a_[3] if len(a_) > 3 else 'UVMap'          # 'HeadUV': only the head faces, fitted to their own bbox
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src_blend))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
before_faces=len(me.polygons);me.validate(verbose=True,clean_customdata=False);removed_faces=before_faces-len(me.polygons)
assert removed_faces==1
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
matched=set();corner_max=0.0;repairs=[]
for p in polys:
    c = Vector(T[list(p.vertices)].mean(0))
    _, si, d = tree.find(c)
    worst = max(worst, d)
    matched.add(si)
    sp = src.data.polygons[si]
    if len(sp.vertices) != len(p.vertices):
        mism += 1
    sco = [S[v] for v in sp.vertices]
    repair = d>.0001
    if repair:
        points=T[list(p.vertices)];part=int(me.attributes['piece'].data[p.vertices[0]].value)
        assert part==9 and p.area<.00004 and np.all(points[:,0]>-.003) and np.all(points[:,0]<.007) and np.all(points[:,2]>1.046) and np.all(points[:,2]<1.052)
        repairs.append({'face':p.index,'piece':part,'centroid_gap_m':float(d),'method':'project the omitted belt-knot triangle onto its adjacent returned belt UV chart'})

    for li, vi in zip(p.loop_indices, p.vertices):
        k = int(np.argmin([np.linalg.norm(T[vi] - x) for x in sco]))
        if repair:
            a,bb,c=np.array(sco);bc=np.linalg.lstsq(np.column_stack([bb-a,c-a]),T[vi]-a,rcond=None)[0]
            ua,ub,uc=[np.array(suv[l].uv) for l in sp.loop_indices];tuv[li].uv=ua+bc[0]*(ub-ua)+bc[1]*(uc-ua)
        else:
            corner_max=max(corner_max,float(np.linalg.norm(T[vi]-sco[k])))
            tuv[li].uv = suv[sp.loop_indices[k]].uv
print('UVTRANSFER', LAYER, 'faces ours', len(polys), 'meshy', len(src.data.polygons), 'worst centroid mismatch mm',
      round(worst * 1000, 2), 'corner-count mismatches', mism)
assert len(polys)==len(src.data.polygons)+2 and len(src.data.polygons)==len(matched) and len(repairs)==2 and mism==0 and corner_max<.0001
import json
from pathlib import Path
(Path(HERE) / 'work/uv_transfer.json').write_text(json.dumps({'faces':len(polys),'unique_matches':len(matched),'centroid_error_m':worst,'corner_error_m':corner_max,'removed_invalid_faces':removed_faces,'repairs':repairs},indent=2))
for o in list(bpy.data.objects):
    if o not in before:
        bpy.data.objects.remove(o, do_unlink=True)
me.uv_layers.active = me.uv_layers['UVMap']
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
