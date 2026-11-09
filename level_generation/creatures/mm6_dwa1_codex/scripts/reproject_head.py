from pathlib import Path
import numpy as np,json,shutil
from PIL import Image
from scipy.ndimage import map_coordinates,distance_transform_edt
P=Path(__file__).resolve().parents[1];d=np.load(P/'work/head_reproject.npz');N=1024;backup=P/'textures/head_uv_before';backup.mkdir(exist_ok=True)
for p in (P/'textures').glob('dwa1_head*.png'):
 if not(backup/p.name).exists():shutil.copy2(p,backup/p.name)
src={p.name:np.array(Image.open(p))for p in backup.glob('*.png')};dst={k:np.zeros_like(v)for k,v in src.items()};hit=np.zeros((N,N),np.uint16)
def normalize(v):return v/np.maximum(np.linalg.norm(v,axis=-1,keepdims=True),1e-12)
def basis(xyz,uv,n):
 du=uv[1:]-uv[0];dp=xyz[1:]-xyz[0]
 if abs(np.linalg.det(du))<1e-12:return None
 t,b=np.linalg.solve(du,dp);t=normalize(t-n*np.sum(t*n,axis=-1,keepdims=True));b=normalize(np.cross(n,t))*np.sign(np.sum(np.cross(np.broadcast_to(t,t.shape),b)*n,axis=-1,keepdims=True));return t,b
for old,new,xyz,ns in zip(d['old'],d['new'],d['xyz'],d['normals']):
 px=new.copy();px[:,1]=1-px[:,1];px*=N;lo=np.maximum(np.floor(px.min(0)).astype(int),0);hi=np.minimum(np.ceil(px.max(0)).astype(int),N-1)
 if np.any(hi<lo):continue
 x,y=np.meshgrid(np.arange(lo[0],hi[0]+1)+.5,np.arange(lo[1],hi[1]+1)+.5);a,b,c=px;det=np.linalg.det(np.stack([b-a,c-a]))
 if abs(det)<1e-10:continue
 u=((x-a[0])*(c[1]-a[1])-(y-a[1])*(c[0]-a[0]))/det;v=((b[0]-a[0])*(y-a[1])-(b[1]-a[1])*(x-a[0]))/det;mask=(u>=-1e-6)&(v>=-1e-6)&(u+v<=1+1e-6);yy,xx=np.where(mask);yy+=lo[1];xx+=lo[0];w=np.stack([1-u[mask]-v[mask],u[mask],v[mask]],axis=1);uv=w@old;coords=np.array([(1-uv[:,1])*N-.5,uv[:,0]*N-.5]);n=normalize(w@ns);bo=basis(xyz,old,n);bn=basis(xyz,new,n);hit[yy,xx]+=1
 for name,im in src.items():
  order=0 if 'classes'in name or 'mask'in name else 1
  q=map_coordinates(im,coords,order=order,mode='nearest')if im.ndim==2 else np.stack([map_coordinates(im[:,:,k].astype(float),coords,order=order,mode='nearest')for k in range(im.shape[2])],axis=1)
  if 'normal'in name and bo is not None and bn is not None:
   z=q[:,:3]/127.5-1;z[:,1]*=-1;world=normalize(bo[0]*z[:,0,None]+bo[1]*z[:,1,None]+n*z[:,2,None]);z=np.stack([np.sum(world*bn[0],axis=1),-np.sum(world*bn[1],axis=1),np.sum(world*n,axis=1)],axis=1);q[:,:3]=(normalize(z)+1)*127.5
  dst[name][yy,xx]=np.clip(np.rint(q),0,255).astype(np.uint8)
valid=hit>0;dist,idx=distance_transform_edt(~valid,return_indices=True);pad=(~valid)&(dist<=8)
for name,im in dst.items():
 im[pad]=im[tuple(idx[:,pad])];Image.fromarray(im).save(P/'textures'/name)
report={'covered_texels':int(valid.sum()),'overlap_texels':int((hit>1).sum()),'paint_preserved_by':'barycentric UV reprojection, with per-face tangent normal basis conversion','maps':list(dst)};(P/'review/head_reprojection.json').write_text(json.dumps(report,indent=2));print(report)
