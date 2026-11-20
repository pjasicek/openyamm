"""Rasterize the selected body/head UVs for material classes and neck blending."""
import bpy,numpy as np,json
from pathlib import Path
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_textured_uv.blend'))
ob=bpy.data.objects['Body'];me=ob.data
reports={}
for layer,N,flag in [('UVMap',1024,0),('HeadUV',2048,1)]:
 unintended_overlap=0;bridge=np.zeros((N,N),bool);hits=np.zeros((N,N),np.uint16);pos=np.zeros((N,N,3),np.float32);piece=np.full((N,N),-1,np.int16)
 for f in me.polygons:
  if bool(me.attributes['head'].data[f.index].value)!=bool(flag):continue
  assert len(f.vertices)==3
  uv=np.array([me.uv_layers[layer].data[i].uv[:] for i in f.loop_indices]);a,b,c=uv*N
  den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
  if abs(den)<1e-8:continue
  x0,y0=np.maximum(np.floor(uv.min(0)*N).astype(int),0);x1,y1=np.minimum(np.ceil(uv.max(0)*N).astype(int),N-1)
  if x1<x0 or y1<y0:continue
  x,y=np.meshgrid(np.arange(x0,x1+1)+.5,np.arange(y0,y1+1)+.5)
  w0=((b[1]-c[1])*(x-c[0])+(c[0]-b[0])*(y-c[1]))/den;w1=((c[1]-a[1])*(x-c[0])+(a[0]-c[0])*(y-c[1]))/den;w2=1-w0-w1
  m=(w0>1e-6)&(w1>1e-6)&(w2>1e-6);ix=(x[m]-.5).astype(int);iy=N-1-(y[m]-.5).astype(int)
  is_bridge=bool(me.attributes.get('neck_bridge') and me.attributes['neck_bridge'].data[f.index].value)
  unintended_overlap+=int(((hits[iy,ix]>0)&~(bridge[iy,ix]&is_bridge)).sum())
  bridge[iy,ix]=is_bridge
  hits[iy,ix]+=1;piece[iy,ix]=me.attributes['region'].data[f.vertices[0]].value
  pos[iy,ix]=np.stack([w0[m],w1[m],w2[m]],1)@np.array([me.vertices[i].co[:] for i in f.vertices])
 np.savez_compressed(p/f'work/uvraster_{layer}.npz',coverage=hits>0,pos=pos,piece=piece,bridge=bridge)
 reports[layer]={'resolution':N,'covered':int((hits>0).sum()),'overlap':int((hits>1).sum()),'unintended_overlap':unintended_overlap}
 assert reports[layer]['covered']>50000,reports[layer]
 assert unintended_overlap==0,reports[layer]  # The flat-colour neck strip may reuse its own texels.
 print(layer,reports[layer])
(p/'work/head_v2_uv.json').write_text(json.dumps(reports,indent=2)+'\n')
