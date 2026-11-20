"""Rasterize retained face labels; compose 1K PBR, seam-safe skin and tier hide ramps."""
import json,sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parent/'claude_shared'));import region_variants as R
N=1024;T=P/'textures';T.mkdir(exist_ok=True);report={}
def load(p,mode='RGB'):return np.asarray(Image.open(p).convert(mode).resize((N,N),Image.Resampling.LANCZOS),float)/255
def save(a,p):Image.fromarray(np.uint8(np.clip(a,0,1)*255+.5)).save(p)
def pad(a,cov):
 _,idx=ndimage.distance_transform_edt(~cov,return_indices=True);o=a[tuple(idx)];o[cov]=a[cov];return o
def srgb(x):return np.where(x<=.0031308,x*12.92,1.055*np.maximum(x,0)**(1/2.4)-.055)
def raster(d,key,head):
 uv=d[key];verts=d['vertices'][d['faces']];which=np.where(d['head']==head)[0];pc=np.full((N,N),-1,np.int16);pos=np.zeros((N,N,3),np.float32);face=np.full((N,N),-1,np.int32);overlap=0
 def cross(a,b):return a[...,0]*b[...,1]-a[...,1]*b[...,0]
 for fi in which:
  t=uv[fi]*N;a,b,c=t;lo=np.maximum(np.floor(t.min(0)).astype(int),0);hi=np.minimum(np.ceil(t.max(0)).astype(int),N-1)
  xx,yy=np.meshgrid(np.arange(lo[0],hi[0]+1)+.5,np.arange(lo[1],hi[1]+1)+.5);p=np.stack((xx,yy),-1);den=cross(b-a,c-a)
  if abs(den)<1e-12:continue
  v=cross(p-a,c-a)/den;w=cross(b-a,p-a)/den;inside=(v>1e-6)&(w>1e-6)&(v+w<1-1e-6);ys,xs=np.where(inside);y=N-1-(ys+lo[1]);x=xs+lo[0]
  overlap+=int((pc[y,x]>=0).sum());pc[y,x]=d['piece'][fi];pos[y,x]=(1-v[inside]-w[inside])[:,None]*verts[fi,0]+v[inside,None]*verts[fi,1]+w[inside,None]*verts[fi,2];face[y,x]=fi
 return pc,pos,face,overlap

from scipy.spatial import cKDTree
d=np.load(P/'texturing/gloamer_uv.npz');edges={}
for fi,tri in enumerate(d['faces']):
 for j in range(3):edges.setdefault(tuple(sorted((int(tri[j]),int(tri[(j+1)%3])))),[]).append(fi)
seam={v for edge,fs in edges.items() if len(fs)==2 and d['head'][fs[0]]!=d['head'][fs[1]] for v in edge}
assert seam
seam_edges=[edge for edge,fs in edges.items() if len(fs)==2 and d['head'][fs[0]]!=d['head'][fs[1]]]
seam_points=np.concatenate([np.linspace(d['vertices'][a],d['vertices'][b],16) for a,b in seam_edges])
seamtree=cKDTree(seam_points)
pores=set(json.loads((P/'review/geometry/cleanup.json').read_text())['pores_flattened']);allsets={}
base_target=np.array([174,153,145])/255
for kind,key in [('body','BodyUV'),('head','HeadUV')]:
 pc,pos,face,overlap=raster(d,key,kind=='head');cov=pc>=0;stem='gloamer_'+kind;job=P/'meshy'/('retexture_'+kind+'_v1')
 b=load(job/'texture_urls_0_base_color.png');normal=load(job/'texture_urls_0_normal.png');rough=load(job/'texture_urls_0_roughness.png','L')
 skin=pc==0;pore=np.isin(pc,list(pores));teeth=cov&~skin&~pore
 cls=np.zeros((N,N),np.uint8);cls[skin]=1;cls[pore]=11;cls[teeth]=5
 # Keep the returned warm paint and broad crease shading; match the two atlas medians at the neck.
 mouth=skin&(pos[...,1]<-.28)&(pos[...,2]<1.37)&(pos[...,2]>1.16)&(b.max(-1)<.27)
 cls[mouth]=7;skin&=~mouth
 linear=R.srgb_to_linear(b);median=np.median(linear[skin],axis=0)
 graded=b.copy();graded[skin]=srgb(R.srgb_to_linear(base_target)*(linear[skin]/median)**1.15)
 graded[pore]=np.array([.58,.60,.52]);graded[teeth]=np.clip(b[teeth],.08,.92)
 ao=load(P/'texturing'/f'{stem}_ao.png','L');graded[cov]*=(.88+.12*np.maximum(ao[cov],.35))[:,None]
 dist=np.full((N,N),1.);dist[cov]=seamtree.query(pos[cov])[0];blend=np.clip(1-dist/.035,0,1);blend=blend*blend*(3-2*blend)*skin
 graded=graded*(1-blend[...,None])+base_target*blend[...,None]
 normal=normal*(1-blend[...,None])+np.array([.5,.5,1])*blend[...,None]
 spec=np.zeros((N,N));rgh=np.ones((N,N))*.82
 for label,sp,rg in [(1,.22,.80),(5,.45,.45),(7,.26,.66),(11,.18,.75)]:
  m=cls==label
  if m.any():spec[m]=sp;rgh[m]=np.clip(rg+.15*(rough[m]-np.median(rough[m])),.3,1)
 rgh=rgh*(1-blend)+.8*blend
 graded=pad(np.clip(graded,8/255,243/255),cov)
 save(graded,T/f'{stem}_basecolor_1k.png');save(pad(normal,cov),T/f'{stem}_normal_1k.png');save(np.stack([pad(spec,cov),pad(rgh,cov),np.zeros((N,N))],-1),T/f'{stem}_metal_rough_1k.png')
 Image.fromarray(cls).save(T/f'{stem}_material_classes.png')
 weights=[pad(x.astype(float),cov) for x in [skin,pore]];R.write_mask(weights,T/f'{stem}_region_mask.png')
 allsets[kind]=(graded,cov,skin,pore);np.savez_compressed(P/'texturing'/f'{stem}_raster.npz',piece=pc,pos=pos,face=face)
 quantiles=np.percentile(graded[skin]*255,[10,50,90],axis=0)
 assert quantiles[1,0]>quantiles[1,2]+15 and quantiles[2].mean()-quantiles[0].mean()>35
 report[kind]={'skin_rgb8_p10_p50_p90':quantiles.tolist(),'coverage':int(cov.sum()),'overlap_pixels':overlap,'classes':{int(c):int((cls==c).sum()) for c in np.unique(cls)}}
base,cov,skin,pore=allsets['body'];variants=['gloamer_a','gloamer_b','gloamer_c']
colours={'gloamer_a':[181,162,154],'gloamer_b':[174,153,145],'gloamer_c':[118,123,113]}
targets={k:np.clip(base* (np.array(c)/255/base_target),0,1) for k,c in colours.items()}
skin_ramps,skinfit=R.fit_ramps(base,targets,skin.astype(float))
# Pores remain yellow-green across tiers; emitted colour is supplied separately by factors only.
porecolours={'gloamer_a':[100,114,48],'gloamer_b':[166,185,62],'gloamer_c':[206,221,91]}
poretargets={k:np.clip(base*np.array(c)/255/np.array([.58,.60,.52]),0,1) for k,c in porecolours.items()}
poreramps,porefit=R.fit_ramps(base,poretargets,pore.astype(float))
ramps={k:[skin_ramps[k],poreramps[k]] for k in variants}
cfg={'variants':variants,'materials':[{'base':name+'_A','prefix':name,'mask':f'gloamer_{kind}_region_mask.png','regions':['hide','pores'],'ramps':ramps} for name,kind in [('GloamerBody','body'),('GloamerHead','head'),('GloamerPores','body')]]}
(T/'gloamer_ramps.json').write_text(json.dumps(cfg,indent=2)+'\n')
report['ramps']={'skin_palette_srgb8':colours,'pore_palette_srgb8':porecolours,'skin_fit':skinfit,'pore_fit':porefit,'head_uses_identical_ramps':True}
# Measure both atlas samples on every actual neck-boundary edge.
def sample(img,uv):
 coords=np.array([(1-uv[:,1])*N-.5,uv[:,0]*N-.5]);return np.stack([ndimage.map_coordinates(img[...,c],coords,order=1,mode='nearest') for c in range(3)],-1)
a=[];b=[]
for edge,fs in edges.items():
 if len(fs)!=2 or d['head'][fs[0]]==d['head'][fs[1]]:continue
 for fi in fs:
  bary=np.array([.5 if v in edge else 0 for v in d['faces'][fi]]);uv=d['HeadUV' if d['head'][fi] else 'BodyUV'][fi];(b if d['head'][fi] else a).append(bary@uv)
err=np.abs(sample(allsets['body'][0],np.array(a))-sample(allsets['head'][0],np.array(b)))*255
report['seam']={'edges':len(a),'mean_rgb8':float(err.mean()),'max_rgb8':float(err.max())};print('SEAM',report['seam'],flush=True);assert err.mean()<5
(P/'review/texture_composition.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=1))
