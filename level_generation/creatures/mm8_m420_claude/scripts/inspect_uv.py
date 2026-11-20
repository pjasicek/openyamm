import bpy,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/master_settled.blend'));me=bpy.data.objects['Body'].data;me.calc_loop_triangles();head=np.array([d.value for d in me.attributes['head'].data]);pc=np.array([d.value for d in me.attributes['piece'].data])
for layer,ishead in [('UVMap',False),('HeadUV',True)]:
 uv=me.uv_layers[layer].data;hits=np.zeros((512,512),np.uint8);raster={}
 for tri in me.loop_triangles:
  if bool(head[tri.polygon_index])!=ishead:continue
  a,b,c=np.array([tuple(uv[i].uv) for i in tri.loops])*512;den=np.cross(b-a,c-a)
  if abs(float(den))<1e-8:continue
  lo=np.maximum(np.floor(np.minimum(np.minimum(a,b),c)).astype(int),0);hi=np.minimum(np.ceil(np.maximum(np.maximum(a,b),c)).astype(int),511)
  if (hi<lo).any():continue
  xx,yy=np.meshgrid(np.arange(lo[0],hi[0]+1)+.5,np.arange(lo[1],hi[1]+1)+.5);v=np.stack([xx-a[0],yy-a[1]],-1);w1=(v[:,:,0]*(c-a)[1]-v[:,:,1]*(c-a)[0])/den;w2=((b-a)[0]*v[:,:,1]-(b-a)[1]*v[:,:,0])/den;m=(w1>1e-4)&(w2>1e-4)&(w1+w2<.9999)
  iy,ix=np.where(m);iy+=lo[1];ix+=lo[0];hits[iy,ix]+=1;raster[tri.polygon_index]=(iy,ix)
 rows=sorted([(int((hits[iy,ix]>1).sum()),f,int(pc[me.polygons[f].vertices[0]])) for f,(iy,ix) in raster.items()],reverse=True)
 print('OVERLAPS',layer,rows[:25]);print('F8822',[(tuple(me.vertices[v].co),tuple(uv[li].uv)) for v,li in zip(me.polygons[8822].vertices,me.polygons[8822].loop_indices)])
