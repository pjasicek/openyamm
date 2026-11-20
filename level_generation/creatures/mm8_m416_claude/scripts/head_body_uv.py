"""Map the body's unchanged head texels into the high-detail face UV layout."""
from pathlib import Path
import bpy,sys,runpy,numpy as np
P=Path(__file__).resolve().parents[1]
s=P/'scripts/transfer_uv.py';sys.argv=[str(s),'--',str(P/'work/textured.blend'),str(P/'meshy/body_retexture_v1'),str(P/'work/textured_full_uv.blend'),'BodyFullUV'];runpy.run_path(str(s),run_name='__main__')
me=bpy.data.objects['Body'].data;huv=me.uv_layers['HeadUV'].data;suv=me.uv_layers['BodyFullUV'].data;hd=me.attributes['head'].data;N=1024;out=np.full((N,N,2),-1,np.float32);me.calc_loop_triangles()
for t in me.loop_triangles:
 if not hd[t.polygon_index].value:continue
 L=list(t.loops);uv=np.array([huv[i].uv[:] for i in L])*N;a,b,c=uv;mn=np.maximum(np.floor(uv.min(0)).astype(int),0);mx=np.minimum(np.ceil(uv.max(0)).astype(int),N-1)
 if np.any(mx<mn):continue
 xs,ys=np.meshgrid(np.arange(mn[0],mx[0]+1)+.5,np.arange(mn[1],mx[1]+1)+.5);den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
 if abs(den)<1e-12:continue
 w0=((b[1]-c[1])*(xs-c[0])+(c[0]-b[0])*(ys-c[1]))/den;w1=((c[1]-a[1])*(xs-c[0])+(a[0]-c[0])*(ys-c[1]))/den;w2=1-w0-w1;m=(w0>=-.02)&(w1>=-.02)&(w2>=-.02);iy=(N-1-(ys[m]-.5)).astype(int);ix=(xs[m]-.5).astype(int);s=np.array([suv[i].uv[:] for i in L]);out[iy,ix]=w0[m,None]*s[0]+w1[m,None]*s[1]+w2[m,None]*s[2]
np.save(P/'work/head_body_uv.npy',out);assert (out[...,0]>=0).sum()>500000
