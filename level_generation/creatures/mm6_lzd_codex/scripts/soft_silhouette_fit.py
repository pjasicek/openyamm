"""Jointly fit all eight switch-size silhouettes with a differentiable triangle coverage loss."""
import os
os.environ['OPENBLAS_NUM_THREADS']='1';os.environ['OMP_NUM_THREADS']='1'
import sys,json,numpy as np
from pathlib import Path
from PIL import Image
from scipy.optimize import minimize
from scipy.ndimage import distance_transform_edt
path=Path(sys.argv[1]);d=np.load(path);initial=d['vertices'];faces=d['faces'];part=str(d['part']);level=int(d['level']);P=path.parents[2];cal=json.loads((P/'review/rebake/camera.json').read_text());res=[1024,768,384,192][level];scale=[700,550,220,88][level]/cal['height_m'];center=np.array(cal['center']);views=[]
for i in range(8):
 a=i*np.pi/4;right=np.array([np.cos(a),np.sin(a),0]);up=np.array([-.05*np.sin(a),.05*np.cos(a),1]);up/=np.linalg.norm(up);M=np.array([right,-up])*scale
 alpha=np.array(Image.open(P/f'review/rebake/reference_pbr_{part}_l{level}_{i}.png'))[...,3]/255;ys,xs=np.where(alpha>.03);x0,x1=max(0,xs.min()-4),min(res,xs.max()+5);y0,y1=max(0,ys.min()-4),min(res,ys.max()+5);yy,xx=np.mgrid[y0:y1,x0:x1];points=np.c_[xx.ravel(),yy.ravel()];target=(alpha[y0:y1,x0:x1].ravel()>=.5).astype(float)
 mask=alpha>=.5;band=(distance_transform_edt(mask)+distance_transform_edt(~mask))[y0:y1,x0:x1].ravel()<4.5;points=points[band];target=target[band]
 views.append((M,points,target))
history=[];iterations=0
def objective(flat,record=False):
 xyz=flat.reshape(-1,3);gradient=np.zeros_like(xyz);loss=0;intersection=union=0
 for M,points,target in views:
  xy=(xyz-center)@M.T+res/2-.5;v=xy[faces];A=v;B=np.roll(v,-1,axis=1);edge=B-A;length=np.maximum(np.linalg.norm(edge,axis=2),1e-7);area=np.cross(v[:,1]-v[:,0],v[:,2]-v[:,0]);sign=np.where(area>=0,1.,-1.)
  # [triangle, pixel, edge]; positive inside each oriented triangle.
  rel=points[None,:,None,:]-A[:,None,:,:];cross=edge[:,None,:,0]*rel[:,:,:,1]-edge[:,None,:,1]*rel[:,:,:,0];dist=cross/length[:,None,:]*sign[:,None,None]
  edge_id=dist.argmin(2);near=np.take_along_axis(dist,edge_id[:,:,None],2)[:,:,0];tri=near.argmax(0);pids=np.arange(len(points));eid=edge_id[tri,pids];signed=near[tri,pids];temperature=.24;coverage=1/(1+np.exp(-np.clip(signed/temperature,-35,35)))
  # Correct pixel classification with a small margin; no drive to inflate already-correct silhouettes.
  wanted=np.where(target>.5,.56,.44);error=np.where(target>.5,np.minimum(coverage-wanted,0),np.maximum(coverage-wanted,0));loss+=float(np.mean(error*error));derivative=2*error*coverage*(1-coverage)/temperature/len(points)
  aa=A[tri,eid];bb=B[tri,eid];ee=edge[tri,eid];ll=length[tri,eid];ff=cross[tri,pids,eid];ss=sign[tri];pa=np.c_[bb[:,1]-points[:,1],points[:,0]-bb[:,0]]/ll[:,None]+ff[:,None]*ee/(ll**3)[:,None];pb=np.c_[points[:,1]-aa[:,1],aa[:,0]-points[:,0]]/ll[:,None]-ff[:,None]*ee/(ll**3)[:,None]
  ga=(pa*(ss*derivative)[:,None])@M;gb=(pb*(ss*derivative)[:,None])@M;np.add.at(gradient,faces[tri,eid],ga);np.add.at(gradient,faces[tri,(eid+1)%3],gb)
  mask=coverage>=.5;intersection+=int((mask&(target>.5)).sum());union+=int((mask|(target>.5)).sum())
 displacement=xyz-initial;regularization=.00001
 loss+=regularization*np.mean((displacement*scale)**2);gradient+=2*regularization*scale**2*displacement/displacement.size
 if record:history.append({'iteration':len(history),'pooled_iou':intersection/union,'loss':loss,'max_displacement_m':float(np.linalg.norm(displacement,axis=1).max())});print('SOFT_FIT',part,level,history[-1],flush=True)
 return loss,gradient.ravel()
# Finite differences validate the analytic projection/coverage gradient away from edge ties.
x=initial.ravel().copy();value,g=objective(x);index=int(np.argmax(abs(g)));eps=1e-7;y=x.copy();y[index]+=eps;z=x.copy();z[index]-=eps;numeric=(objective(y)[0]-objective(z)[0])/(2*eps);assert abs(numeric-g[index])<max(.005,abs(numeric)*.05),(numeric,g[index])
def callback(x):
 if len(history)%1==0:objective(x,True)
result=minimize(objective,x,jac=True,method='L-BFGS-B',bounds=list(zip(x-.018,x+.018)),callback=callback,options={'maxiter':80,'ftol':1e-10,'gtol':1e-6,'maxls':20})
out=result.x.reshape(-1,3);np.save(path.with_suffix('.npy'),out);path.with_suffix('.json').write_text(json.dumps({'history':history,'message':str(result.message),'passed_self_test':True},indent=2));print('SOFT_FINAL',part,level,str(result.message),flush=True)
