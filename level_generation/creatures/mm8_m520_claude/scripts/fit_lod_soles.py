"""Keep the reduced boots flat and pointing along the accepted full-detail soles."""
from pathlib import Path
import json,sys,numpy as np
from shrink_shadow_lods import read_glb,write_glb,view
from scipy.spatial import ConvexHull
src,dst=map(Path,sys.argv[1:]);doc,binary=read_glb(src);node=next(n for n in doc['nodes'] if n.get('name')=='Cyclops');base=doc['meshes'][node['mesh']];joint_names=[doc['nodes'][i]['name'] for i in doc['skins'][node['skin']]['joints']]
foot={s:joint_names.index(f'B_{s}_Foot') for s in 'LR'}
def channels(prim):
 a=prim['attributes'];keys=sorted(k for k in a if k.startswith('WEIGHTS_'));w=np.concatenate([view(doc,binary,a[k])[0] for k in keys],axis=1).copy();j=np.concatenate([view(doc,binary,a[k.replace('WEIGHTS','JOINTS')])[0] for k in keys],axis=1).copy();return keys,w,j
reference={};footprints={}
for prim in base['primitives']:
 pos=view(doc,binary,prim['attributes']['POSITION'])[0].copy();keys,w,j=channels(prim)
 for side,ji in foot.items():
  ids=((w*(j==ji)).sum(1)>.3)&(pos[:,1]<.011)
  if ids.sum()<3:continue
  pts=np.unique(pos[ids],axis=0);z=pts[:,2];d=pts[z>=np.quantile(z,.7)].mean(0)-pts[z<=np.quantile(z,.3)].mean(0);reference[side]=float(d[0]/d[2]);xz=pts[:,[0,2]];footprints[side]=xz[ConvexHull(xz).vertices]
assert set(reference)==set('LR')
levels={mi:level for level,mi in enumerate([node['mesh']]+base['extras']['openyamm_lods']) if level}
levels.update({mi:level for level,mi in enumerate(base['extras']['openyamm_shadow_lods']) if level})
report=[]
for mi,level in levels.items():
 for prim in doc['meshes'][mi]['primitives']:
  attrs=prim['attributes'];pos,off=view(doc,binary,attrs['POSITION']);pos=pos.copy();before=pos.copy();keys,w,j=channels(prim);touched=False
  for side,ji in foot.items():
   owns=(w*(j==ji)).sum(1)>.3;sole=owns&(pos[:,1] < {1:.03,2:.055,3:.08}[level])
   if sole.sum()<3:continue
   pts=pos[sole].copy();pts[:,1]=.008;pts=np.unique(pts,axis=0);z=pts[:,2];d=pts[z>=np.quantile(z,.7)].mean(0)-pts[z<=np.quantile(z,.3)].mean(0)
   assert abs(d[2])>.05,(mi,side,'sole length')
   shear=d[0]/d[2]-reference[side];blend=owns*np.clip((.16-pos[:,1])/.08,0,1)
   pos[:,0]-=shear*(pos[:,2]-z.mean())*blend;pos[sole,1]=.008
   # Decimation can widen the low boot; keep its sole inside the original contact footprint.
   hull=footprints[side];edges=np.roll(hull,-1,axis=0)-hull
   for index in np.flatnonzero(sole):
    q=pos[index,[0,2]];delta=q-hull
    if np.all(edges[:,0]*delta[:,1]-edges[:,1]*delta[:,0]>=-1e-7):continue
    t=np.clip((delta*edges).sum(1)/(edges*edges).sum(1),0,1)
    candidates=hull+edges*t[:,None];pos[index,[0,2]]=candidates[np.argmin(((candidates-q)**2).sum(1))]
   w[sole]=0;j[sole]=0;w[sole,0]=1;j[sole,0]=ji
   assert np.linalg.matrix_rank(np.unique(pos[sole],axis=0)-pos[sole].mean(0),tol=1e-6)>=2,(mi,side,'sole plane')
   report.append({'mesh':doc['meshes'][mi]['name'],'side':side,'sole_vertices':int(sole.sum()),'shear':float(shear)});touched=True
  if not touched:continue
  binary[off:off+pos.nbytes]=pos.tobytes();a=doc['accessors'][attrs['POSITION']];a['min']=pos.min(0).tolist();a['max']=pos.max(0).tolist()
  for k,key in enumerate(keys):
   for name,data in [(key,w[:,4*k:4*k+4]),(key.replace('WEIGHTS','JOINTS'),j[:,4*k:4*k+4])]:
    dest,offset=view(doc,binary,attrs[name]);binary[offset:offset+dest.nbytes]=data.astype(dest.dtype).tobytes()
write_glb(dst,doc,binary);print('LOD_SOLES',json.dumps(report))
Path(__file__).resolve().parents[1].joinpath('work/lod_soles.json').write_text(json.dumps(report,indent=2))
