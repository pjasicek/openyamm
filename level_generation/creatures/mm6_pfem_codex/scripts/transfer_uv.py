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
errors=[];patched=[]
source_vertices={}
for sf in src.data.polygons:
 for vi in sf.vertices:
  key=tuple(round(float(x),5) for x in S[vi]);source_vertices.setdefault(key,set()).add(sf.index)
for p in polys:
    c = Vector(T[list(p.vertices)].mean(0))
    _, si, d = tree.find(c)
    worst = max(worst, d)
    errors.append((d,p.index,me.attributes['piece'].data[p.vertices[0]].value,list(c)))
    sp = src.data.polygons[si]
    if d > .001 and LAYER=='UVMap':
        # Meshy removed the opposing pair at the repaired narrow skirt puncture.
        # Keep the repaired surface and unfold that one triangle into its neighbour's chart.
        part=me.attributes['piece'].data[p.vertices[0]].value
        assert part==100 and .33<c.z<.42 and .16<c.x<.20,(part,list(c),d)
        counts={}
        for vi in p.vertices:
            for fi in source_vertices.get(tuple(round(float(x),5) for x in T[vi]),set()):
                counts[fi]=counts.get(fi,0)+1
        candidates=[fi for fi,count in counts.items() if count>=2]
        assert candidates,('no shared-edge UV neighbour',p.index)
        si=min(candidates,key=lambda i:(S[list(src.data.polygons[i].vertices)].mean(0)-np.array(c)).dot(S[list(src.data.polygons[i].vertices)].mean(0)-np.array(c)))
        sp=src.data.polygons[si];pts=S[list(sp.vertices)]
        A=np.column_stack((pts[1]-pts[0],pts[2]-pts[0]))
        uv0=np.array(suv[sp.loop_indices[0]].uv)
        du=np.column_stack((np.array(suv[sp.loop_indices[1]].uv)-uv0,np.array(suv[sp.loop_indices[2]].uv)-uv0))
        for li,vi in zip(p.loop_indices,p.vertices):
            coeff=np.linalg.lstsq(A,T[vi]-pts[0],rcond=None)[0];uv=uv0+du@coeff
            assert np.all(uv>=0) and np.all(uv<=1),uv
            tuv[li].uv=uv
        patched.append(p.index);continue
    if len(sp.vertices) != len(p.vertices):
        mism += 1
    sco = [S[v] for v in sp.vertices]
    for li, vi in zip(p.loop_indices, p.vertices):
        k = int(np.argmin([np.linalg.norm(T[vi] - x) for x in sco]))
        tuv[li].uv = suv[sp.loop_indices[k]].uv
print('UVTRANSFER', LAYER, 'faces ours', len(polys), 'meshy', len(src.data.polygons), 'worst centroid mismatch mm',
      round(worst * 1000, 2), 'corner-count mismatches', mism)
print('UV ERROR QUANTILES',np.percentile([e[0] for e in errors],[0,50,90,99,100])*1000,'WORST',sorted(errors,reverse=True)[:10])
print('MISSING FACES',[(e[1],me.polygons[e[1]].area,[list(T[v]) for v in me.polygons[e[1]].vertices]) for e in errors if e[0]>.001])
assert all(e[0]<.001 or e[1] in patched for e in errors) and mism==0,(worst,mism)
print('LOCAL UV PATCHES',patched)
for o in list(bpy.data.objects):
    if o not in before:
        bpy.data.objects.remove(o, do_unlink=True)
me.uv_layers.active = me.uv_layers['UVMap']
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
