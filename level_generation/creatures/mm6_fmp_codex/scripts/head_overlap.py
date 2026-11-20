"""Map the body texture into the head UV overlap so their shared neck seam has identical colour."""
import bpy
import numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/textured_uv.blend'))
me=bpy.data.objects['Body'].data;head=np.array([v.value for v in me.attributes['head'].data]);N=1024;body_uv=np.zeros((N,N,2),np.float32)
for f in me.polygons:
 if not head[f.index]:continue
 uv=np.array([tuple(me.uv_layers['HeadUV'].data[i].uv) for i in f.loop_indices]);src=np.array([tuple(me.uv_layers['UVMap'].data[i].uv) for i in f.loop_indices]);a,b,c=uv*N
 den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1]);assert abs(den)>1e-10
 x0,y0=np.maximum(np.floor(uv.min(0)*N).astype(int),0);x1,y1=np.minimum(np.ceil(uv.max(0)*N).astype(int),N-1)
 if x1<x0 or y1<y0:continue
 x,y=np.meshgrid(np.arange(x0,x1+1)+.5,np.arange(y0,y1+1)+.5);w0=((b[1]-c[1])*(x-c[0])+(c[0]-b[0])*(y-c[1]))/den;w1=((c[1]-a[1])*(x-c[0])+(a[0]-c[0])*(y-c[1]))/den;w2=1-w0-w1
 mask=(w0>1e-6)&(w1>1e-6)&(w2>1e-6);ix=(x[mask]-.5).astype(int);iy=N-1-(y[mask]-.5).astype(int)
 body_uv[iy,ix]=w0[mask,None]*src[0]+w1[mask,None]*src[1]+w2[mask,None]*src[2]
np.save(P/'work/head_body_uv.npy',body_uv)
