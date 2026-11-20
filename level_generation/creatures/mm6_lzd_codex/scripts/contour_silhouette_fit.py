"""Jointly fit all eight switch-size silhouettes with a differentiable triangle coverage loss."""
import os
os.environ['OPENBLAS_NUM_THREADS']='1';os.environ['OMP_NUM_THREADS']='1'
import sys,json,numpy as np
from pathlib import Path
from PIL import Image,ImageDraw
from scipy.optimize import minimize
from scipy.ndimage import distance_transform_edt
path=Path(sys.argv[1]);d=np.load(path);initial=d['vertices'];faces=d['faces'];part=str(d['part']);level=int(d['level']);P=path.parents[2];cal=json.loads((P/str(d['camera']) if 'camera'in d else P/'review/rebake/camera.json').read_text());res=[1024,768,384,192][level];scale=[700,550,220,88][level]/cal['height_m'];center=np.array(cal['center']);views=[]
for i in range(8):
 a=i*np.pi/4;right=np.array([np.cos(a),np.sin(a),0]);up=np.array([-.05*np.sin(a),.05*np.cos(a),1]);up/=np.linalg.norm(up);M=np.array([right,-up])*scale
 alpha=np.array(Image.open(P/f"review/rebake/{str(d['reference'])if'reference'in d else'reference_pbr'}_{part}_l{level}_{i}.png"))[...,3]/255;ys,xs=np.where(alpha>.03);x0,x1=max(0,xs.min()-4),min(res,xs.max()+5);y0,y1=max(0,ys.min()-4),min(res,ys.max()+5);yy,xx=np.mgrid[y0:y1,x0:x1];points=np.c_[xx.ravel(),yy.ravel()];target=(alpha[y0:y1,x0:x1].ravel()>=.5).astype(float)
 mask=alpha>=.5;band=(distance_transform_edt(mask)+distance_transform_edt(~mask))[y0:y1,x0:x1].ravel()<4.5;points=points[band];target=target[band]
 views.append((M,points,target))
# Mesh edges with their incident triangle IDs determine projected silhouette contours.
edge_faces={}
for fi,tri in enumerate(faces):
 for a,b in zip(tri,np.roll(tri,-1)):edge_faces.setdefault(tuple(sorted((int(a),int(b)))),[]).append(fi)
edge_list=np.array(list(edge_faces),int);adj=list(edge_faces.values())
history=[]
def objective(flat,record=False):
 xyz=flat.reshape(-1,3);gradient=np.zeros_like(xyz);loss=0;intersection=union=0
 for M,points,target in views:
  xy=(xyz-center)@M.T+res/2-.5;v=xy[faces];e0=v[:,1]-v[:,0];e1=v[:,2]-v[:,0];area=e0[:,0]*e1[:,1]-e0[:,1]*e1[:,0];sign=np.where(area>=0,1.,-1.)
  raster=Image.new('1',(res*8,res*8));draw=ImageDraw.Draw(raster)
  for tri in v:draw.polygon([tuple(p)for p in tri*8],fill=1)
  inside=np.asarray(raster)[points[:,1]*8,points[:,0]*8]
  if level==3:
   rel=points[None,:,None,:]-v[:,None,:,:];edge=np.roll(v,-1,axis=1)-v;cross=edge[:,None,:,0]*rel[:,:,:,1]-edge[:,None,:,1]*rel[:,:,:,0];inside=np.any(np.all(cross*sign[:,None,None]>=0,axis=2),axis=0)
  contour=np.array([i for i,fs in enumerate(adj)if len(fs)==1 or min(sign[fs])!=max(sign[fs])],int);ends=edge_list[contour];a=xy[ends[:,0]];b=xy[ends[:,1]];e=b-a
  # Occluded seams are not silhouette boundaries. Reject edges buried inside the raster union.
  normal=np.c_[-e[:,1],e[:,0]]/np.maximum(np.linalg.norm(e,axis=1)[:,None],1e-9)
  ts=np.array([.1,.3,.5,.7,.9]);probes=a[:,None,:]+ts[None,:,None]*e[:,None,:]
  samples=[]
  for side in [-1,1]:
   ij=np.rint((probes+side*.35*normal[:,None,:])*8).astype(int);ij=np.clip(ij,0,res*8-1);samples.append(np.asarray(raster)[ij[:,:,1],ij[:,:,0]])
  keep=(samples[0]!=samples[1]).any(1);ends=ends[keep];a=a[keep];b=b[keep];e=e[keep]
  length2=np.maximum((e*e).sum(1),1e-10);rel=points[None,:,:]-a[:,None,:];t=np.clip((rel*e[:,None,:]).sum(2)/length2[:,None],0,1);q=a[:,None,:]+t[:,:,None]*e[:,None,:];r=points[None,:,:]-q;distance2=(r*r).sum(2);chosen=distance2.argmin(0);pids=np.arange(len(points));dist=np.sqrt(distance2[chosen,pids]+1e-12);direction=r[chosen,pids]/dist[:,None];signed=dist*np.where(inside,1,-1);weights=t[chosen,pids]
  error=np.where(target>.5,np.minimum(signed-.025,0),np.maximum(signed+.025,0));loss+=float(np.mean(error*error));derivative=2*error/len(points);g=-direction*(derivative*np.where(inside,1,-1))[:,None];np.add.at(gradient,ends[chosen,0],(g*(1-weights)[:,None])@M);np.add.at(gradient,ends[chosen,1],(g*weights[:,None])@M)
  intersection+=int((inside&(target>.5)).sum());union+=int((inside|(target>.5)).sum())
 displacement=xyz-initial;regularization=.00001
 loss+=regularization*np.mean((displacement*scale)**2);gradient+=2*regularization*scale**2*displacement/displacement.size
 if record:history.append({'iteration':len(history),'pooled_iou':intersection/union,'loss':float(loss),'max_displacement_m':float(np.linalg.norm(displacement,axis=1).max())});print('CONTOUR_FIT',part,level,history[-1],flush=True)
 return loss,gradient.ravel()
# Finite differences validate the analytic projection/coverage gradient away from edge ties.
x=initial.ravel().copy();value,g=objective(x);index=int(np.argmax(abs(g)));eps=1e-7;y=x.copy();y[index]+=eps;z=x.copy();z[index]-=eps;numeric=(objective(y)[0]-objective(z)[0])/(2*eps);assert abs(numeric-g[index])<max(.005,abs(numeric)*.05),(numeric,g[index])
def callback(x):
 if len(history)%1==0:objective(x,True)
radius=(np.where(d['locked'],0.,.018).ravel()if d['locked'].ndim==2 else np.repeat(np.where(d['locked'],0.,.018),3))if'locked'in d else np.full_like(x,.018)
result=minimize(objective,x,jac=True,method='L-BFGS-B',bounds=list(zip(x-radius,x+radius)),callback=callback,options={'maxiter':40,'ftol':1e-8,'gtol':1e-6,'maxls':12})
out=result.x.reshape(-1,3);np.save(path.with_suffix('.npy'),out);path.with_suffix('.json').write_text(json.dumps({'history':history,'message':str(result.message),'passed_self_test':True},indent=2));print('SOFT_FINAL',part,level,str(result.message),flush=True)
