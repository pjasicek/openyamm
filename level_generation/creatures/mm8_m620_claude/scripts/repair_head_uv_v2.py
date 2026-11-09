"""Repair collapsed head UV folds while preserving the source paint and chart orientation."""
import bpy,math,json,numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_head_v2.blend'))
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
def raster(N):
 hits=np.zeros((N,N),np.uint16);pos=np.zeros((N,N,3),np.float32);piece=np.full((N,N),-1,np.int16);srcuv=np.zeros((N,N,2),np.float32);owner=np.full((N,N),-1,np.int32);bad=set()
 for fi in head:
  f=me.polygons[fi]
  uv=np.array([me.uv_layers['HeadUV'].data[i].uv[:] for i in f.loop_indices]);a,b,c=uv*N
  den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
  if abs(den)<1e-10:bad.add(fi);continue
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
# Translate the small folded triangles into unused space without shrinking the face charts.
hits,pos,piece,srcuv,bad=raster(2048);repaired=set(bad);N=2048
occupied=hits>0
for fi in sorted(bad,key=lambda i:-np.prod(np.ptp(old[i],axis=0))):
 f=me.polygons[fi];coords=old[fi].copy();size=np.ptp(coords,axis=0)
 e1,e2=coords[1]-coords[0],coords[2]-coords[0]
 if abs(e1[0]*e2[1]-e1[1]*e2[0])<1e-10:
  v=[me.vertices[i].co for i in f.vertices];e=v[1]-v[0];d=v[2]-v[0];t=e.normalized();coords=np.array([(0,0),(e.length,0),(d.dot(t),math.sqrt(max(d.length_squared-d.dot(t)**2,1e-12)))])*3;size=np.ptp(coords,axis=0)
 w,h=np.ceil(size*N).astype(int)+10
 integral=np.pad(occupied.astype(np.int32),((1,0),(1,0))).cumsum(0).cumsum(1)
 areas=integral[h:,w:]-integral[:-h,w:]-integral[h:,:-w]+integral[:-h,:-w]
 free=np.argwhere(areas[::4,::4]==0);assert len(free),(fi,w,h)
 y,x=free[0]*4;occupied[y:y+h,x:x+w]=True
 # Raster coordinates have top-left origin; Blender UVs have bottom-left origin.
 shift=np.array([(x+5)/N,1-(y+h-5)/N])-coords.min(0)
 for li,uv in zip(f.loop_indices,coords+shift):me.uv_layers['HeadUV'].data[li].uv=uv
hits,pos,piece,srcuv,bad=raster(2048);assert not bad,bad
hits,pos,piece,srcuv,bad=raster(2048);assert not bad
np.savez_compressed(P/'work/uvraster_HeadUV.npz',coverage=hits>0,pos=pos,piece=piece)
np.savez_compressed(P/'work/head_v2_reprojection.npz',coverage=hits>0,piece=piece,srcuv=srcuv)
me.uv_layers.active=me.uv_layers['UVMap']
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_textured_uv.blend'))
report={'overlap_pixels':0,'covered_pixels':int((hits>0).sum()),'resolution':2048,'separated_triangles':len(repaired),'preserved_chart_rotation':True}
(P/'work/head_v2_uv_repaired.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
