"""Carry Meshy's UVs by original polygon corners; match its triangulation while preserving rig weights and attributes."""
import bpy,bmesh,sys,os,json,hashlib,numpy as np
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
for sp in src.data.polygons:
 vs=list(sp.vertices);sc=S[vs];best=None
 for _,i,_ in tree.find_n(Vector(sc.mean(0)),min(12,len(polys))):
  p=polys[i];ids=list(p.vertices);dist=np.linalg.norm(sc[:,None,:]-T[ids][None,:,:],axis=2);corners=dist.argmin(1);error=float(dist[np.arange(len(vs)),corners].max())
  if best is None or error<best[0]:best=(error,p,[ids[j] for j in corners],corners)
 error,p,ids,corners=best;assert error<1e-5,(layer,sp.index,p.index,error)
 assert len(set(ids))==3,(sp.index,ids)
 worst=max(worst,error);matches.append((sp,p,ids,corners))
used={p.index for _,p,_,_ in matches};missing=[p for p in polys if p.index not in used]
# Meshy omitted tiny head faces from its paint return. Only its body UVs are used: our detailed head keeps HeadUV.
assert layer=='UVMap' and all(len(p.vertices)==3 for p in polys)
assert all(me.attributes['head'].data[p.index].value for p in missing),'body faces missing from the retexture'
body_faces={p.index for p in polys if not me.attributes['head'].data[p.index].value}
assert body_faces<=used and len(matches)==len(used),'ambiguous body face mapping'
head_before=[tuple(u.uv) for u in me.uv_layers['HeadUV'].data]
uv=me.uv_layers['UVMap'].data
for sp,op,ids,corners in matches:
 if op.index not in body_faces:continue
 for j,k in enumerate(corners):uv[op.loop_indices[k]].uv=src.data.uv_layers.active.data[sp.loop_indices[j]].uv
assert head_before==[tuple(u.uv) for u in me.uv_layers['HeadUV'].data]
report={'body_faces':len(body_faces),'matched_body_faces':len(body_faces&used),'meshy_omitted_unused_head_faces':len(missing),'max_corner_error_m':worst,'geometry_weights_and_HeadUV':'unchanged'}
from pathlib import Path
(Path(out).parent/'uv_transfer.json').write_text(json.dumps(report,indent=2)+'\n');print('UV_MATCH',report,flush=True)
for o in list(bpy.data.objects):
 if o not in before:bpy.data.objects.remove(o,do_unlink=True)
me.uv_layers.active=me.uv_layers['UVMap']
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
print('UVTRANSFER',layer,'faces',len(matches),'max matched-corner error mm',worst*1000)
