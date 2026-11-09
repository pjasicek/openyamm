"""Audit overlap/density and cache UV-to-rest positions for shared texture composition."""
from pathlib import Path
import numpy as np,json
from PIL import Image
P=Path(__file__).resolve().parents[1];d=np.load(P/'work/uv_geometry.npz');N=1024
count=np.zeros((N,N),np.uint16);pos=np.zeros((N,N,3),np.float32);tid=np.full((N,N),-1,np.int32);areas={}
for k,(v,u,slot) in enumerate(zip(d['tri'],d['uv'],d['slots'])):
 if slot:continue
 assert u.min()>=-1e-5 and u.max()<=1.00001
 xy=u*N;lo=np.maximum(0,np.floor(xy.min(0)).astype(int));hi=np.minimum(N-1,np.ceil(xy.max(0)).astype(int));mat=np.column_stack([xy[1]-xy[0],xy[2]-xy[0]]);det=np.linalg.det(mat)
 if abs(det)<1e-9:continue
 xx,yy=np.meshgrid(np.arange(lo[0],hi[0]+1)+.5,np.arange(lo[1],hi[1]+1)+.5);b=(np.stack([xx,yy],-1)-xy[0])@np.linalg.inv(mat).T;inside=(b[...,0]>1e-5)&(b[...,1]>1e-5)&(b.sum(-1)<.99999)
 iy=(N-1-(yy[inside]-.5)).astype(int);ix=(xx[inside]-.5).astype(int);count[iy,ix]+=1
 q=d['co'][v];pos[iy,ix]=(1-b[inside].sum(-1))[:,None]*q[0]+b[inside,0,None]*q[1]+b[inside,1,None]*q[2];tid[iy,ix]=k
 c=q.mean(0);region='head' if c[1]<-.135 and c[2]>.62 else ('wing' if abs(c[0])>.1 and c[2]>.6 else 'body')
 world=np.linalg.norm(np.cross(q[1]-q[0],q[2]-q[0]))*.5;areas.setdefault(region,[]).append((world,abs(det)*.5/N**2))
coverage=float((count>0).mean());overlap=int((count>1).sum());densities={n:float(np.sqrt(np.array(a)[:,1].sum()/np.array(a)[:,0].sum())*N) for n,a in areas.items()}
report=dict(coverage=coverage,overlap_pixels=overlap,texels_per_meter_1k=densities,head_body_density_ratio=densities['head']/densities['body'])
assert overlap<30,report
assert coverage>.25 and report['head_body_density_ratio']>1.8,report
np.savez_compressed(P/'work/uv_raster.npz',pos=pos,covered=count>0,triangle=tid)
(P/'review/uv_audit.json').write_text(json.dumps(report,indent=2));Image.fromarray(np.where(count[...,None]>0,np.array([110,170,150],np.uint8),np.array([25,25,25],np.uint8)).astype(np.uint8)).save(P/'review/uv_coverage.png');print(report)
