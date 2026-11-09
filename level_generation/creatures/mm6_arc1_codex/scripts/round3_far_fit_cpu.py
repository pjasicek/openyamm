"""Fit the capped distance mesh to eight switch-size silhouettes; no new geometry."""
import json,math,time
from pathlib import Path
import numpy as np
from PIL import Image
P=Path(__file__).resolve().parents[1];D=P/'review/round3/reduction';W=P/'work/round3'
data=json.loads((W/'fit_input.json').read_text());world=np.array(data['world']);rest=np.array(data['rest']);original=rest.copy();mat=np.array(data['transforms']);tri=np.array(data['triangles'])
camera=json.loads((D/'camera.json').read_text())['body'];center=np.array(camera['center']);N=192;SS=4;M=N*SS;scale=camera['body_diameter_m']*N/88
basis=[]
for i in range(8):
 angle=i*math.pi/4;d=np.array([math.sin(angle),-math.cos(angle),.05]);d/=np.linalg.norm(d);right=np.array([math.cos(angle),math.sin(angle),0]);up=np.cross(d,right);basis.append(np.array([right,-up])*M/scale)
basis=np.array(basis);proj=np.einsum('vij,kj->vki',basis,world-center)+M/2
target=np.stack([np.array(Image.open(D/f'assembled_l3_Standing_high_{i}.png'))[:,:,3]/255 for i in range(8)]).ravel()
cover=np.zeros(8*M*M,np.int16);hits=np.zeros(8*N*N,np.int16)
def raster(points):
 ids=[]
 for view,p in enumerate(points):
  low=np.maximum(0,np.ceil(p.min(0)-.5).astype(int));high=np.minimum(M-1,np.floor(p.max(0)-.5).astype(int))
  if np.any(low>high):continue
  xx,yy=np.meshgrid(np.arange(low[0],high[0]+1),np.arange(low[1],high[1]+1));x=xx+.5;y=yy+.5
  e=[]
  for a,b in zip(p,np.roll(p,-1,axis=0)):e.append((x-a[0])*(b[1]-a[1])-(y-a[1])*(b[0]-a[0]))
  e=np.array(e);inside=np.all(e>=-1e-7,axis=0)|np.all(e<=1e-7,axis=0);ids.append(view*M*M+yy[inside]*M+xx[inside])
 return np.concatenate(ids)if ids else np.zeros(0,int)
def parent(ids):return(ids//(M*M))*N*N+((ids%(M*M))//M//SS)*N+(ids%M//SS)
faces=[raster(proj[:,t])for t in tri]
for ids in faces:cover[ids]+=1
np.add.at(hits,parent(np.flatnonzero(cover)),1)
mask=hits/(SS*SS);intersection=float(np.minimum(mask,target).sum());union=float(np.maximum(mask,target).sum());print('SOFTWARE_INITIAL',intersection/union,flush=True)
def change(old,new,commit=False):
 global intersection,union
 ids=np.concatenate([*old,*new]);sign=np.concatenate([*[np.full(len(x),-1,np.int16)for x in old],*[np.ones(len(x),np.int16)for x in new]])
 unique,index=np.unique(ids,return_inverse=True);delta=np.bincount(index,weights=sign).astype(np.int16);before=cover[unique];diff=((before+delta)>0).astype(np.int16)-(before>0).astype(np.int16);move=diff!=0
 parents=parent(unique[move]);base,ix=np.unique(parents,return_inverse=True);change=np.bincount(ix,weights=diff[move]).astype(np.int16);oldmask=hits[base]/(SS*SS);newmask=(hits[base]+change)/(SS*SS)
 di=float((np.minimum(newmask,target[base])-np.minimum(oldmask,target[base])).sum());du=float((np.maximum(newmask,target[base])-np.maximum(oldmask,target[base])).sum())
 score=(intersection+di)/(union+du)
 if commit:cover[unique]+=delta;hits[base]+=change;intersection+=di;union+=du
 return score
adj=[np.flatnonzero(np.any(tri==i,axis=1))for i in range(len(world))];history=[]
for radius in [.006,.003,.0015,.00075]:
 accepted=0
 for i,indices in enumerate(adj):
  if not len(indices) or not data['editable'][i]:continue
  old=[faces[t]for t in indices];best=intersection/union;best_delta=None;best_faces=None
  for axis in range(3):
   if axis==2 and original[i,2]<.03:continue
   for direction in [-1,1]:
    delta=np.zeros(3);delta[axis]=radius*direction
    if np.linalg.norm(rest[i]+delta-original[i])>.016:continue
    motion=mat[i]@delta;projected=proj[:,i]+np.einsum('vij,j->vi',basis,motion);candidate=[]
    for t in indices:
     points=proj[:,tri[t]].copy();points[:,tri[t]==i]=projected[:,None,:];candidate.append(raster(points))
    score=change(old,candidate)
    if score>best+1e-8:best=score;best_delta=delta;best_faces=candidate
  if best_delta is not None:
   change(old,best_faces,True);rest[i]+=best_delta;world[i]+=mat[i]@best_delta;proj[:,i]+=np.einsum('vij,j->vi',basis,mat[i]@best_delta)
   for t,f in zip(indices,best_faces):faces[t]=f
   accepted+=1
 history.append({'radius_m':radius,'pooled_iou':intersection/union,'vertices_changed':accepted});print('FIT',history[-1],flush=True)
 (W/'fit_output.json').write_text(json.dumps({'rest':rest.tolist(),'history':history,'max_vertex_change_m':float(np.linalg.norm(rest-original,axis=1).max())},indent=2))
