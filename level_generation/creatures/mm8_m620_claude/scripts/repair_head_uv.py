"""Unfold the hair more finely; preserve the painted face and reproject returned maps."""
import bpy,math,json,numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_textured_uv.blend'))
ob=bpy.data.objects['Body'];me=ob.data
head=[f.index for f in me.polygons if me.attributes['head'].data[f.index].value]
old={f.index:np.array([me.uv_layers['HeadUV'].data[i].uv[:] for i in f.loop_indices]) for f in (me.polygons[i] for i in head)}
for o in bpy.data.objects:o.select_set(o==ob)
bpy.context.view_layer.objects.active=ob
me.uv_layers.active=me.uv_layers['HeadUV']
def select(faces):
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_mode(type='FACE');bpy.ops.mesh.select_all(action='DESELECT');bpy.ops.object.mode_set(mode='OBJECT')
 for i in faces:me.polygons[i].select=True
 bpy.ops.object.mode_set(mode='EDIT')
select([i for i in head if me.attributes['region'].data[me.polygons[i].vertices[0]].value==4])
bpy.ops.uv.smart_project(angle_limit=math.radians(25),island_margin=.006)
bpy.ops.object.mode_set(mode='OBJECT')
select(head);bpy.ops.uv.pack_islands(rotate=False,margin=.006);bpy.ops.object.mode_set(mode='OBJECT')
def raster(N):
 hits=np.zeros((N,N),np.uint16);pos=np.zeros((N,N,3),np.float32);piece=np.full((N,N),-1,np.int16);srcuv=np.zeros((N,N,2),np.float32);owner=np.full((N,N),-1,np.int32);bad=set()
 for fi in head:
  f=me.polygons[fi]
  uv=np.array([me.uv_layers['HeadUV'].data[i].uv[:] for i in f.loop_indices]);a,b,c=uv*N
  den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1]);assert abs(den)>1e-10
  x0,y0=np.maximum(np.floor(uv.min(0)*N).astype(int),0);x1,y1=np.minimum(np.ceil(uv.max(0)*N).astype(int),N-1)
  x,y=np.meshgrid(np.arange(x0,x1+1)+.5,np.arange(y0,y1+1)+.5)
  w0=((b[1]-c[1])*(x-c[0])+(c[0]-b[0])*(y-c[1]))/den;w1=((c[1]-a[1])*(x-c[0])+(a[0]-c[0])*(y-c[1]))/den;w2=1-w0-w1
  inside=(w0>1e-6)&(w1>1e-6)&(w2>1e-6);ix=(x[inside]-.5).astype(int);iy=N-1-(y[inside]-.5).astype(int)
  prior=owner[iy,ix];over=prior>=0
  if over.any():bad.add(f.index);bad.update(map(int,prior[over]))
  hits[iy,ix]+=1;owner[iy,ix]=f.index;piece[iy,ix]=me.attributes['region'].data[f.vertices[0]].value
  weights=np.stack([w0[inside],w1[inside],w2[inside]],axis=1)
  pos[iy,ix]=weights@np.array([me.vertices[i].co[:] for i in f.vertices]);srcuv[iy,ix]=weights@old[f.index]
 return hits,pos,piece,srcuv,bad
# Separate only the triangles whose chart still folds back over itself, then pack all charts.
for iteration in range(8):
 hits,pos,piece,srcuv,bad=raster(2048)
 print('UV_REPAIR',iteration,len(bad),int((hits>1).sum()),flush=True)
 if not bad:break
 for k,fi in enumerate(sorted(bad)):
  f=me.polygons[fi];v=[me.vertices[i].co for i in f.vertices];e=(v[1]-v[0]);length=e.length;t=e.normalized();d=v[2]-v[0]
  coords=[(0,0),(length,0),(d.dot(t),math.sqrt(max(d.length_squared-d.dot(t)**2,1e-12)))]
  for li,uv in zip(f.loop_indices,coords):me.uv_layers['HeadUV'].data[li].uv=(uv[0]+2+k*2,uv[1]+2)
 select(head);bpy.ops.uv.pack_islands(rotate=False,margin=.005);bpy.ops.object.mode_set(mode='OBJECT')
assert not bad,'Head UV overlap remains'
hits,pos,piece,srcuv,bad=raster(1024);assert not bad
np.savez_compressed(P/'work/uvraster_HeadUV.npz',coverage=hits>0,pos=pos,piece=piece)
hits,pos,piece,srcuv,bad=raster(2048);assert not bad,'Head UV overlap remains at 2K'
np.savez_compressed(P/'work/head_reprojection.npz',coverage=hits>0,piece=piece,srcuv=srcuv)
me.uv_layers.active=me.uv_layers['UVMap']
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_textured_uv.blend'))
report=json.loads((P/'work/uv_transfer.json').read_text());report['HeadUV']['original_overlap_pixels']=report['HeadUV']['overlap_pixels'];report['HeadUV'].update(overlap_pixels=0,repair='Hair Smart UV at 25 degrees, isolate folded triangles and pack without rotation; reproject maps and flatten hair micro-normal.',covered_pixels=int((hits>0).sum()),validation_resolution=2048)
(P/'work/uv_transfer.json').write_text(json.dumps(report,indent=2))
