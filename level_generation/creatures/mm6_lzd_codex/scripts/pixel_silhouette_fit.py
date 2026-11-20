"""Refine distance mesh outlines by cached supersampled triangle coverage."""
import sys,json,numpy as np
from pathlib import Path
from PIL import Image,ImageDraw
path=Path(sys.argv[1]);d=np.load(path);xyz=d['vertices'].copy();origin=xyz.copy();faces=d['faces'];locked=d['locked'];P=path.parents[2];cal=json.loads((P/'review/round4/camera.json').read_text());res=192;ss=16;scale=88/cal['height_m'];center=np.array(cal['center']);views=[]
def raster(v):
 lo=np.maximum(0,np.floor(v.min(0)).astype(int)-1);hi=np.minimum(res*ss,np.ceil(v.max(0)).astype(int)+2)
 if np.any(hi<=lo):return (0,0,np.zeros((0,0),np.int16))
 im=Image.new('1',tuple(hi-lo));ImageDraw.Draw(im).polygon([tuple(p-lo)for p in v],fill=1);return int(lo[0]),int(lo[1]),np.asarray(im,dtype=np.int16)
def stamp(occ,item,sign):
 x,y,m=item;occ[y:y+m.shape[0],x:x+m.shape[1]]+=sign*m
def lowmask(occ):return (occ>0).reshape(occ.shape[0]//ss,ss,occ.shape[1]//ss,ss).sum((1,3))>=ss*ss/2
for i in range(8):
 a=i*np.pi/4;up=np.array([-.05*np.sin(a),.05*np.cos(a),1]);up/=np.linalg.norm(up);M=np.array([[np.cos(a),np.sin(a),0],-up])*scale;xy=((xyz-center)@M.T+res/2)*ss-.5
 cache=[raster(xy[t])for t in faces];occ=np.zeros((res*ss,res*ss),np.int16)
 for item in cache:stamp(occ,item,1)
 target=np.asarray(Image.open(P/f"review/rebake/{str(d['reference'])}_actor_l3_{i}.png"))[...,3]>=128;mask=lowmask(occ);views.append({'M':M,'cache':cache,'occ':occ,'target':target,'I':int((mask&target).sum()),'U':int((mask|target).sum())})
groups=d['groups'];unique=np.unique(groups);members={i:np.flatnonzero(groups==i)for i in unique};adj={i:np.flatnonzero(np.isin(faces,members[i]).any(1))for i in unique};I=sum(v['I']for v in views);U=sum(v['U']for v in views);history=[]
print('PIXEL_INITIAL',I/U,flush=True)
def trial(ids,fi,delta,apply=False):
 changes=[];di=du=0
 for v in views:
  old=[v['cache'][f]for f in fi];posed=xyz[faces[fi]].copy();posed+=np.isin(faces[fi],ids)[...,None]*delta
  xy=((posed-center)@v['M'].T+res/2)*ss-.5;new=[raster(t)for t in xy];alltiles=old+new;x0=min(t[0]for t in alltiles)//ss*ss;y0=min(t[1]for t in alltiles)//ss*ss;x1=min(res*ss,((max(t[0]+t[2].shape[1]for t in alltiles)+ss-1)//ss)*ss);y1=min(res*ss,((max(t[1]+t[2].shape[0]for t in alltiles)+ss-1)//ss)*ss)
  target=v['target'][y0//ss:y1//ss,x0//ss:x1//ss];occ=v['occ'];before=lowmask(occ[y0:y1,x0:x1])
  for t in old:stamp(occ,t,-1)
  for t in new:stamp(occ,t,1)
  after=lowmask(occ[y0:y1,x0:x1]);di+=int((after&target).sum())-int((before&target).sum());du+=int((after|target).sum())-int((before|target).sum())
  if apply:
   for f,t in zip(fi,new):v['cache'][f]=t
  else:
   for t in new:stamp(occ,t,-1)
   for t in old:stamp(occ,t,1)
 return di,du
for step in [.004,.004,.002,.002,.001,.001]:
 changed=0;start=I/U
 for group in unique:
  ids=members[group];fi=adj[group];best=(I/U,None,None)
  if not len(fi):continue
  for axis in range(3):
   if locked[ids,axis].any():continue
   for sign in [-1,1]:
    delta=np.zeros(3);delta[axis]=step*sign
    if np.abs(xyz[ids]+delta-origin[ids]).max()>.018:continue
    di,du=trial(ids,fi,delta);score=(I+di)/(U+du)
    if score>best[0]+1e-10:best=(score,delta,(di,du))
  if best[1]is not None:
   di,du=trial(ids,fi,best[1],True);xyz[ids]+=best[1];I+=di;U+=du;changed+=1
 assert I/U>=start
 assert all(v['occ'].min()>=0 for v in views)
 history.append({'step_m':step,'pooled_iou':I/U,'changed_groups':changed});print('PIXEL_FIT',history[-1],flush=True)
np.save(path.with_suffix('.npy'),xyz);path.with_suffix('.json').write_text(json.dumps(history,indent=2))
