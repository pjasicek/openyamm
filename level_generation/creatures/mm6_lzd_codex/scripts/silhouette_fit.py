"""Fit reduced silhouettes to the unreduced eight-view masks with regularized vertex displacements."""
import os
os.environ['OPENBLAS_NUM_THREADS']='1';os.environ['OMP_NUM_THREADS']='1'
import sys,json,numpy as np
from pathlib import Path
from PIL import Image,ImageDraw
from scipy.ndimage import distance_transform_edt,map_coordinates,gaussian_filter
from scipy.sparse import coo_matrix,vstack,eye
from scipy.sparse.linalg import lsqr
path=Path(sys.argv[1]);d=np.load(path);xyz=d['vertices'].copy();origin=xyz.copy();faces=d['faces'];part=str(d['part']);level=int(d['level']);P=path.parents[2];cal=json.loads((P/'review/rebake/camera.json').read_text());res=[1024,768,384,192][level];pix=[700,550,220,88][level];scale=pix/cal['height_m'];center=np.array(cal['center']);edges=np.unique(np.sort(np.concatenate([faces[:,[0,1]],faces[:,[1,2]],faces[:,[2,0]]]),axis=1),axis=0)
views=[]
for i in range(8):
 a=i*np.pi/4;right=np.array([np.cos(a),np.sin(a),0]);up=np.array([-.05*np.sin(a),.05*np.cos(a),1]);up/=np.linalg.norm(up);M=np.array([right,-up])*scale
 mask=np.array(Image.open(P/f'review/rebake/reference_pbr_{part}_l{level}_{i}.png'))[...,3]>=128
 sdf=distance_transform_edt(~mask)-distance_transform_edt(mask);sdf=gaussian_filter(sdf,.65);gy,gx=np.gradient(sdf);views.append((M,sdf,gx,gy))
history=[]
for iteration in range(12):
 rows=[];cols=[];values=[];rhs=[];ious=[]
 for M,sdf,gx,gy in views:
  xy=(xyz-center)@M.T+res/2-.5
  im=Image.new('1',(res*4,res*4));draw=ImageDraw.Draw(im)
  for tri in faces:draw.polygon([tuple(p)for p in (xy[tri]+.5)*4],fill=1)
  low=np.array(im).reshape(res,4,res,4).mean((1,3))>=.5;hi=sdf<0;ious.append((low&hi).sum()/(low|hi).sum());own=distance_transform_edt(~low)-distance_transform_edt(low)
  for a,b in edges:
   length=np.linalg.norm(xy[b]-xy[a]);ts=np.linspace(0,1,max(2,min(40,int(length*2)+2)))
   ps=(1-ts[:,None])*xy[a]+ts[:,None]*xy[b];coord=ps[:,::-1].T
   vis=np.abs(map_coordinates(own,coord,order=1,mode='nearest'))<1.05
   ds=map_coordinates(sdf,coord,order=1,mode='nearest');vis&=abs(ds)<5
   for t,p,dist in zip(ts[vis],ps[vis],ds[vis]):
    grad=np.array([map_coordinates(gx,p[::-1,None],order=1)[0],map_coordinates(gy,p[::-1,None],order=1)[0]])@M
    row=len(rhs);rhs.append(-dist)
    for index,weight in [(a,1-t),(b,t)]:
     for k in range(3):rows.append(row);cols.append(index*3+k);values.append(grad[k]*weight)
 A=coo_matrix((values,(rows,cols)),shape=(len(rhs),xyz.size)).tocsr();reg=scale*.7
 A=vstack([A,eye(xyz.size)*reg]);v=np.r_[rhs,(origin-xyz).reshape(-1)*reg];delta=lsqr(A,v,atol=1e-5,btol=1e-5,iter_lim=100)[0].reshape(-1,3)
 lengths=np.linalg.norm(delta,axis=1);delta*=np.minimum(1,.004/np.maximum(lengths,1e-12))[:,None];xyz+=delta*.65
 total=xyz-origin;lengths=np.linalg.norm(total,axis=1);xyz=origin+total*np.minimum(1,.015/np.maximum(lengths,1e-12))[:,None]
 history.append({'iteration':iteration,'mean_iou':float(np.mean(ious)),'maximum_delta_m':float(lengths.max()),'constraints':len(rhs)})
np.save(path.with_suffix('.npy'),xyz);path.with_suffix('.json').write_text(json.dumps(history,indent=2));print('FIT',part,level,history[-1],flush=True)
