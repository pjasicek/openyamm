"""Coordinate descent on the distant mesh's silhouette, using eight supersampled orthographic views."""
import json,sys,math
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
p=Path(sys.argv[1]);d=json.loads(p.read_text());xyz=np.array(d['low']);initial=xyz.copy();norm=np.array(d['normals']);faces=np.array(d['faces']);high=np.array(d['high']);hf=np.array(d['high_faces']);active=d['active'];S=8;size=128;ppm=88/d['diameter']
axes=np.array([[math.cos(k*math.pi/4),math.sin(k*math.pi/4),0] for k in range(8)])
def project(v):
 x=v@axes.T;y=(.93-v[:,2])[:,None]+np.zeros((len(v),8));return np.stack((x*ppm+size/2,y*ppm+size/2),axis=2).transpose(1,0,2)*S
def mask(points,fs,skip=None):
 im=Image.new('L',(size*S,size*S));draw=ImageDraw.Draw(im)
 for i,f in enumerate(fs):
  if skip is None or i not in skip:draw.polygon([tuple(x) for x in points[f]],fill=255)
 return im
def small(im):return np.asarray(im,dtype=float).reshape(size,S,size,S).mean((1,3))/255.
ref=[small(mask(x,hf)) for x in project(high)]
def loss(images):
 soft=hard=0
 for a,b in zip(ref,images):
  soft+=np.abs(a-b).sum();hard+=np.logical_xor(a>.5,b>.5).sum()
 return hard+.2*soft
proj=project(xyz);images=[small(mask(x,faces)) for x in proj];best=loss(images);history=[{'iteration':0,'loss':best}];print('RASTER START',best,len(active),flush=True)
adj={i:set(np.where((faces==i).any(1))[0]) for i in active}
for iteration,step in enumerate([.012,.008,.005,.003,.002],1):
 accepted=0
 for i in active:
  excluded=adj[i];background=[mask(x,faces,excluded) for x in proj];chosen=None;low=best
  for direction in [norm[i],np.array([0.,0.,1.])]:
   for sign in [-1,1]:
    position=xyz[i]+direction*step*sign
    if np.linalg.norm(position-initial[i])>.04:continue
    point=project(position[None,:])[:,0];trial=[]
    for k in range(8):
     im=background[k].copy();draw=ImageDraw.Draw(im)
     for fi in excluded:
      draw.polygon([tuple(point[k] if vi==i else proj[k,vi]) for vi in faces[fi]],fill=255)
     trial.append(small(im))
    score=loss(trial)
    if score<low-.05:low=score;chosen=position
  if chosen is not None:
   xyz[i]=chosen;proj[:,i]=project(chosen[None,:])[:,0];best=low;accepted+=1
 history.append({'iteration':iteration,'step_m':step,'accepted_vertices':accepted,'loss':best});print('RASTER ITER',history[-1],flush=True)
 assert np.isfinite(xyz).all()
 p.with_suffix('.result.json').write_text(json.dumps({'positions':xyz.tolist(),'history':history}))
