"""Carry Meshy's UVs by original polygon corners; match its triangulation while preserving rig weights and attributes."""
import bpy,bmesh,sys,os,numpy as np
from mathutils import Vector,kdtree
args=sys.argv[sys.argv.index('--')+1:];blend,job,out=args[:3];layer=args[3] if len(args)>3 else 'UVMap'
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];me=body.data
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update();before=set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=os.path.join(os.path.abspath(job),'model_urls_glb.glb'))
src=max((o for o in bpy.data.objects if o not in before and o.type=='MESH'),key=lambda o:len(o.data.polygons))
S=np.array([tuple(src.matrix_world@v.co) for v in src.data.vertices]);T=np.array([tuple(body.matrix_world@v.co) for v in me.vertices])
polys=[p for p in me.polygons if layer=='UVMap' or me.attributes['head'].data[p.index].value]
Tsub=T if layer=='UVMap' else T[sorted({v for p in polys for v in p.vertices})]
scale=(Tsub.max(0)-Tsub.min(0)).max()/(S.max(0)-S.min(0)).max();S=S*scale+((Tsub.max(0)+Tsub.min(0))/2-(S.max(0)+S.min(0))/2*scale)
tree=kdtree.KDTree(len(polys))
for i,p in enumerate(polys):tree.insert(Vector(T[list(p.vertices)].mean(0)),i)
tree.balance();matches=[];worst=0
vertex_tree=kdtree.KDTree(len(T))
for vi,point in enumerate(T):vertex_tree.insert(point,vi)
vertex_tree.balance()
vertex_hits=[vertex_tree.find(point) for point in S]
assert max(hit[2] for hit in vertex_hits)<2e-6, max(hit[2] for hit in vertex_hits)
changed=0
for sp in src.data.polygons:
 vs=list(sp.vertices);sc=S[vs];best=None
 for _,i,_ in tree.find_n(Vector(sc.mean(0)),min(12,len(polys))):
  p=polys[i];ids=list(p.vertices);dist=np.linalg.norm(sc[:,None,:]-T[ids][None,:,:],axis=2);corners=dist.argmin(1);error=float(dist[np.arange(len(vs)),corners].max())
  if best is None or error<best[0]:best=(error,p,[ids[j] for j in corners],corners)
 error,p,ids,corners=best
 if layer=='UVMap' and error>=1e-5:
  # Meshy removed two subpixel ear slivers and changed their adjacent triangulation, without moving vertices.
  assert error<.0002,(layer,sp.index,p.index,error)
  ids=[vertex_hits[vi][1] for vi in vs];changed+=1
 else:assert error<1e-5,(layer,sp.index,p.index,error)
 assert len(set(ids))==3,(sp.index,ids)
 worst=max(worst,error);matches.append((sp,p,ids,corners))
matched={op.index for _,op,_,_ in matches}
missing=[p for p in polys if p.index not in matched]
missing_area=sum(p.area for p in missing)
assert len(missing)<=2 and missing_area<2e-7,(layer,len(missing),missing_area)
print('TRIANGULATION_RECONCILIATION',layer,'changed',changed,'missing',len(missing),'area_m2',missing_area,flush=True)
# A few hand quads use a different diagonal in glTF; retain that exact triangle split and their original weights.
if layer=='UVMap':
 assert abs(sum(len(p.vertices)-2 for p in polys)-len(matches))<=2
 olduv={l.name:[[tuple(l.data[i].uv) for i in p.loop_indices] for p in me.polygons] for l in me.uv_layers}
 oldhead=[a.value for a in me.attributes['head'].data]
 bm=bmesh.new();bm.from_mesh(me);bm.verts.ensure_lookup_table();verts=list(bm.verts)
 bmesh.ops.delete(bm,geom=list(bm.faces),context='FACES_ONLY')
 huv=bm.faces.layers.int['head'];uvlayers={n:bm.loops.layers.uv.get(n) or bm.loops.layers.uv.new(n) for n in olduv}
 for sp,op,ids,corners in matches:
  f=bm.faces.new([verts[i] for i in ids]);f[huv]=oldhead[op.index];f.smooth=True
  for j,loop in enumerate(f.loops):
   for name,uvl in uvlayers.items():loop[uvl].uv=olduv[name][op.index][corners[j]]
   loop[uvlayers['UVMap']].uv=src.data.uv_layers.active.data[sp.loop_indices[j]].uv
 bm.to_mesh(me);bm.free()
else:
 uv=me.uv_layers[layer].data
 for sp,op,ids,corners in matches:
  for j,k in enumerate(corners):uv[op.loop_indices[k]].uv=src.data.uv_layers.active.data[sp.loop_indices[j]].uv
for o in list(bpy.data.objects):
 if o not in before:bpy.data.objects.remove(o,do_unlink=True)
me.uv_layers.active=me.uv_layers['UVMap']
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
print('UVTRANSFER',layer,'faces',len(matches),'max matched-corner error mm',worst*1000)
