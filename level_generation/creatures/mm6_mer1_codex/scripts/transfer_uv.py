"""Copy Meshy's own UV layout (retexture with enable_original_uv: false) onto our rigged body, after
mm6_wdm_claude/scripts/transfer_uv.py: the returned mesh has the same faces in its own placement; it is fitted back by
bounding box, each of our faces is matched to the returned face with the nearest centroid, and each corner takes the
UV of the nearest returned corner of that face. Writes layer 'UVMap' (the head faces keep their own 'HeadUV').
Reports the worst centroid mismatch and face-count agreement. Args: -- <in blend> <meshy job dir> <out blend>"""
import bpy, sys, os, bmesh
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
polys = [p for p in me.polygons if LAYER=='UVMap' or hd[p.index]==1]
Tsub = T if LAYER=='UVMap' else T[sorted({v for p in polys for v in p.vertices})]
scale = (Tsub.max(0) - Tsub.min(0)).max() / (S.max(0) - S.min(0)).max()
S = S * scale + ((Tsub.max(0) + Tsub.min(0)) / 2 - (S.max(0) + S.min(0)) / 2 * scale)
suv = src.data.uv_layers.active.data
tree = kdtree.KDTree(len(src.data.polygons))
for p in src.data.polygons:
    tree.insert(Vector(S[list(p.vertices)].mean(0)), p.index)
tree.balance()
# glTF split 19 quads on upload. Match those exact diagonals before copying triangle UVs.
quads=[(f.index,list(f.vertices)) for f in me.polygons if len(f.vertices)>3]
if quads:
 bm=bmesh.new();bm.from_mesh(me);bm.verts.ensure_lookup_table()
 for fi,vs in quads:
  assert len(vs)==4
  coords=T[vs];centre=coords.mean(0);radius=max(np.linalg.norm(x-centre) for x in coords)+.0001
  matches=set()
  for _,si,dist in tree.find_range(Vector(centre),radius):
   sp=src.data.polygons[si];points=S[list(sp.vertices)]
   ids=[];err=0.
   for point in points:
    ds=np.linalg.norm(coords-point,axis=1);j=int(np.argmin(ds));err=max(err,float(ds[j]));ids.append(vs[j])
   if err<1e-4 and len(set(ids))==3:matches.add(tuple(sorted(ids)))
  assert len(matches)==2,(fi,vs,matches)
  diag=set.intersection(*(set(x) for x in matches));assert len(diag)==2
  bmesh.ops.connect_verts(bm,verts=[bm.verts[i] for i in diag])
 bm.to_mesh(me);bm.free()
 hd=np.zeros(len(me.polygons),np.int32);me.attributes['head'].data.foreach_get('value',hd)
 polys=[f for f in me.polygons if LAYER=='UVMap' or hd[f.index]==1]

if LAYER not in me.uv_layers:
    me.uv_layers.new(name=LAYER)
tuv = me.uv_layers[LAYER].data
worst, mism = 0.0, 0
bad_faces=[]
for p in polys:
    c = Vector(T[list(p.vertices)].mean(0))
    _, si, d = tree.find(c)
    worst = max(worst, d)
    if d>1e-4 or len(src.data.polygons[si].vertices)!=len(p.vertices):bad_faces.append({"face":p.index,"verts":list(p.vertices),"size":len(p.vertices),"piece":int(me.attributes["piece"].data[p.vertices[0]].value),"error_mm":d*1000,"ours":T[list(p.vertices)].tolist(),"source":S[list(src.data.polygons[si].vertices)].tolist()})
    sp = src.data.polygons[si]
    if len(sp.vertices) != len(p.vertices):
        mism += 1
    sco = [S[v] for v in sp.vertices]
    for li, vi in zip(p.loop_indices, p.vertices):
        k = int(np.argmin([np.linalg.norm(T[vi] - x) for x in sco]))
        tuv[li].uv = suv[sp.loop_indices[k]].uv
print('UVTRANSFER', LAYER, 'faces ours', len(polys), 'meshy', len(src.data.polygons), 'worst centroid mismatch mm',
      round(worst * 1000, 2), 'corner-count mismatches', mism)
import json
json.dump(bad_faces,open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),'work','uv_transfer_bad_'+LAYER+'.json'),'w'),indent=2)
assert worst<1e-4 and mism==0, (LAYER,worst,mism)
for o in list(bpy.data.objects):
    if o not in before:
        bpy.data.objects.remove(o, do_unlink=True)
me.uv_layers.active = me.uv_layers['UVMap']
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
