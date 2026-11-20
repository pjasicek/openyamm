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

rows=[];matches={};collisions=[]
for poly in polys:
 c=Vector(T[list(poly.vertices)].mean(0));_,si,d=tree.find(c);rows.append(d)
 if si in matches:collisions.append((poly.index,matches[si],si,d))
 matches[si]=poly.index
print('UV_DIAGNOSTIC',LAYER,'scale',scale,'bounds ours',Tsub.min(0),Tsub.max(0),'return',S.min(0),S.max(0),'face counts',len(polys),len(src.data.polygons),'dist quantiles mm',np.quantile(rows,[0,.5,.99,1])*1000,'collisions',len(collisions))
for pi,prev,si,d in collisions[:10]:
 print('COLLISION',pi,prev,si,d,'OURS',T[list(me.polygons[pi].vertices)],'PREV',T[list(me.polygons[prev].vertices)],'RETURN',S[list(src.data.polygons[si].vertices)])

from collections import defaultdict
vt=kdtree.KDTree(len(S))
for i,v in enumerate(S):vt.insert(Vector(v),i)
vt.balance()
loops=defaultdict(list)
for poly in src.data.polygons:
 for li,vi in zip(poly.loop_indices,poly.vertices):loops[vi].append(li)
for pi in [7733,8120]:
 poly=me.polygons[pi];tri=T[list(poly.vertices)]
 print('MISSING',pi,'piece',me.attributes['piece'].data[pi].value,'area',np.linalg.norm(np.cross(tri[1]-tri[0],tri[2]-tri[0]))*.5,'normal',poly.normal[:])
 for vi in poly.vertices:
  matches=vt.find_range(Vector(T[vi]),.00001)
  print('CORNER',vi,'matched',[(j,d,sorted({tuple(round(q,6) for q in suv[li].uv) for li in loops[j]})) for _,j,d in matches])
