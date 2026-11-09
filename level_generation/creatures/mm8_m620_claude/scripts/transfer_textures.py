"""Verify one-to-one face/corner correspondence before copying the returned Meshy UVs."""
import bpy,bmesh,json,sys,math
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.kdtree import KDTree
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_uv_ready.blend'))
body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];me=body.data
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update()
# The service omitted one zero-area hair face in both returns; remove it from the master too.
# Four other hair faces are absent only from the whole-body return and use the exact head return below.
source=me.attributes.new('source_face','INT','FACE')
for f in me.polygons:source.data[f.index].value=f.index
assert me.polygons[4944].area < 1e-14
bm=bmesh.new();bm.from_mesh(me);bm.faces.ensure_lookup_table()
bmesh.ops.delete(bm,geom=[bm.faces[4944]],context='FACES_ONLY');bm.to_mesh(me);bm.free()
T=np.array([tuple(body.matrix_world@v.co) for v in me.vertices])
head=np.array([x.value for x in me.attributes['head'].data],bool)
reports={}
if 'UVMap' not in me.uv_layers:me.uv_layers.new(name='UVMap')
for job,layer in [('body_retexture_v1','UVMap'),('head_retexture_v1','HeadUV')]:
 before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(P/'meshy'/job/'model_urls_glb.glb'))
 imported=set(bpy.data.objects)-before;src=max((o for o in imported if o.type=='MESH'),key=lambda o:len(o.data.polygons))
 polys=list(me.polygons) if layer=='UVMap' else [f for f in me.polygons if head[f.index]]
 if layer=='UVMap':
  missing={4697,4840,5421,5676}
  skipped=[f for f in polys if me.attributes['source_face'].data[f.index].value in missing]
  assert len(skipped)==4 and all(head[f.index] and me.attributes['region'].data[f.vertices[0]].value==4 for f in skipped)
  polys=[f for f in polys if me.attributes['source_face'].data[f.index].value not in missing]
 assert len(src.data.polygons)==len(polys),(job,len(src.data.polygons),len(polys))
 S=np.array([tuple(src.matrix_world@v.co) for v in src.data.vertices]);sub=T[sorted({i for f in polys for i in f.vertices})]
 ratios=np.ptp(sub,axis=0)/np.ptp(S,axis=0);assert np.ptp(ratios)/ratios.mean()<1e-3,(job,ratios)
 scale=float(ratios.mean());S=S*scale+(sub.min(0)+sub.max(0))/2-(S.min(0)+S.max(0))/2*scale
 tree=KDTree(len(src.data.polygons))
 for f in src.data.polygons:tree.insert(Vector(S[list(f.vertices)].mean(0)),f.index)
 tree.balance();used=set();max_corner=0.;max_uv_change=0.
 for f in polys:
  _,i,d=tree.find(Vector(T[list(f.vertices)].mean(0)));assert i not in used and d<.0001,(job,f.index,i,d)
  used.add(i);sf=src.data.polygons[i];assert len(f.vertices)==len(sf.vertices)==3
  dist=np.linalg.norm(T[list(f.vertices)][:,None,:]-S[list(sf.vertices)][None,:,:],axis=2);nearest=dist.argmin(1)
  assert len(set(nearest))==3 and dist.min(1).max()<.0001,(job,f.index,dist)
  max_corner=max(max_corner,float(dist.min(1).max()))
  for li,j in zip(f.loop_indices,nearest):
   uv=src.data.uv_layers.active.data[sf.loop_indices[int(j)]].uv
   max_uv_change=max(max_uv_change,(me.uv_layers[layer].data[li].uv-uv).length)
   me.uv_layers[layer].data[li].uv=uv
 reports[layer]={'faces':len(polys),'unique_face_matches':len(used),'max_corner_error_mm':max_corner*1000,'max_uv_change':max_uv_change,'scale':scale}
 for o in imported:bpy.data.objects.remove(o,do_unlink=True)
# Exact raster interior tests; adjacent triangles sharing an edge do not count as overlap.
for layer in ['UVMap','HeadUV']:
 N=1024;want=layer=='HeadUV';hits=np.zeros((N,N),np.uint16);pos=np.zeros((N,N,3),np.float32);density={};degenerate=0;piece_map=np.full((N,N),-1,np.int16);pieces=np.array([v.value for v in me.attributes['region'].data])
 for f in me.polygons:
  if bool(head[f.index])!=want:continue
  uv=np.array([tuple(me.uv_layers[layer].data[i].uv) for i in f.loop_indices]);assert np.isfinite(uv).all() and uv.min()>-1e-5 and uv.max()<1.00001
  a,b,c=uv*N;den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
  if abs(den)<1e-10:degenerate+=1;continue
  area=abs(den)/2;names={g.index:g.name for g in body.vertex_groups};weights={}
  for vi in f.vertices:
   for g in me.vertices[vi].groups:weights[g.group]=weights.get(g.group,0)+g.weight
  group=names[max(weights,key=weights.get)];density.setdefault(group,[]).append(math.sqrt(area/max(f.area,1e-12)))
  x0,y0=np.maximum(np.floor(uv.min(0)*N).astype(int),0);x1,y1=np.minimum(np.ceil(uv.max(0)*N).astype(int),N-1)
  if x1<x0 or y1<y0:continue
  x,y=np.meshgrid(np.arange(x0,x1+1)+.5,np.arange(y0,y1+1)+.5)
  w0=((b[1]-c[1])*(x-c[0])+(c[0]-b[0])*(y-c[1]))/den
  w1=((c[1]-a[1])*(x-c[0])+(a[0]-c[0])*(y-c[1]))/den;w2=1-w0-w1
  mask=(w0>1e-6)&(w1>1e-6)&(w2>1e-6);ix=(x[mask]-.5).astype(int);iy=N-1-(y[mask]-.5).astype(int)
  hits[iy,ix]+=1;piece_map[iy,ix]=int(pieces[f.vertices[0]])
  pos[iy,ix]=w0[mask,None]*T[f.vertices[0]]+w1[mask,None]*T[f.vertices[1]]+w2[mask,None]*T[f.vertices[2]]
 reports[layer].update(covered_pixels=int((hits>0).sum()),overlap_pixels=int((hits>1).sum()),degenerate_faces=degenerate,density_px_per_m={n:[float(np.percentile(v,5)),float(np.median(v))] for n,v in density.items()})
 np.savez_compressed(P/'work'/f'uvraster_{layer}.npz',coverage=hits>0,pos=pos,piece=piece_map)
 assert degenerate==0,reports[layer]
 if layer=='UVMap':assert int((hits>1).sum())==0,reports[layer]
 else:reports[layer]['status']='pending local hair UV repair'
me.uv_layers.active=me.uv_layers['UVMap']
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_textured_uv.blend'))
(P/'work/uv_transfer.json').write_text(json.dumps(reports,indent=2))
print('UV_VERIFIED',json.dumps(reports))
