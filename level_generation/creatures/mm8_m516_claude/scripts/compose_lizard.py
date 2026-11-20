"""Shared native-palette skin/frill/eye ramps and class-based PBR, retaining both UV sets."""
from pathlib import Path
import json,sys
import numpy as np
from PIL import Image
from scipy import ndimage
P=Path(__file__).resolve().parents[1];T=P/'textures';N=1024;LUMA=np.array([.2126,.7152,.0722]);sys.path.insert(0,str(P.parent/'claude_shared'));import region_variants as R
from material_classes_to_orm import TABLE
sys.path.insert(0,str(P.parents[2]/'tools'));from normal_map_convention import measure
PALETTES={'m516_a':516,'m516_b':518,'m516_c':519};pals={k:np.frombuffer((P.parents[2]/f'assets_dev/worlds/mm8/textures/pal{v}.act').read_bytes()[:768],np.uint8).reshape(256,3)/255 for k,v in PALETTES.items()}
def read(path,mode='RGB'):return np.asarray(Image.open(path).convert(mode),float)/255
def save(a,path):Image.fromarray(np.uint8(np.clip(a,0,1)*255+.5)).save(path,optimize=True)
def pad(a,cov):return a[tuple(ndimage.distance_transform_edt(~cov,return_distances=False,return_indices=True))]
def sample(a,uv):
 coords=[(1-uv[...,1])*a.shape[0]-.5,uv[...,0]*a.shape[1]-.5]
 return np.stack([ndimage.map_coordinates(a[...,i],coords,order=1,mode='nearest') for i in range(a.shape[2])],-1) if a.ndim==3 else ndimage.map_coordinates(a,coords,order=1,mode='nearest')
def hsv(a):return np.moveaxis(np.asarray(Image.fromarray(np.uint8(np.clip(a,0,1)*255)).convert('HSV'),float)/255,-1,0)
sets={}
for label in ['body','head']:
 data=np.load(P/'work'/f'uvraster_{label}.npz');part,pos,uv=data['piece'],data['pos'],data['texture_uv'];cov=part>=0;job=P/'meshy'/f'{label}_retexture_v1';raw=sample(read(job/'texture_urls_0_base_color.png'),uv);ao=sample(read(P/'texturing'/f'{label}_ao.png','L'),uv);ao=np.clip(ndimage.gaussian_filter(pad(ao,cov&(ao>.003)),.7),.25,1);img=raw*(1-.45*(1-ao))[...,None]
 if label=='head':
  bodypaint=sample(read(P/'meshy/body_retexture_v1/texture_urls_0_base_color.png'),data['body_uv'])*(1-.45*(1-ao))[...,None];distance=np.minimum(pos[...,2]-1.31,-.25-pos[...,1]);blend=np.clip(distance/.10,0,1);blend=blend*blend*(3-2*blend);blend=np.where(part==0,blend,1);img=bodypaint*(1-blend[...,None])+img*blend[...,None]
 h,s,v=hsv(img);x,y,z=np.moveaxis(pos,-1,0);classes=np.zeros((N,N),np.uint8);classes[cov]=1
 if label=='body':
  ends=((z<.13)|((y<-.61)&(z<1.05))|((abs(x)<.09)&(z>1.22)&(y>-.20)))
  bone=cov&ends&(s<.43)&(v>.22)&(img[...,0]>img[...,1]*1.04)&(img[...,1]>img[...,2]*1.03);classes[bone]=4
 else:
  membrane=cov&(abs(x)>.12)&(y>-.70)&(z>1.30)&(s>.36)&((h<.17)|(h>.94));classes[membrane]=3
  horn=cov&(z>1.80)&(abs(x)<.12)&(s<.42)&(img[...,0]>img[...,1]*1.04);classes[horn]=4
  mouth=cov&((part==1)|((y<-.76)&(z<1.70)&((h<.06)|(h>.94))&(s>.40)));classes[mouth]=7
  teeth=cov&(y<-.75)&(abs(z-(1.685+.20*(y+.75)))<.025)&(s<.32)&(v>.42)&(img[...,0]>img[...,1]*1.04);classes[teeth]=5
  classes[cov&np.isin(part,[2,3])]=6
 skin=(classes==1);under=skin&(s<.20);skin=skin&~under;frill=classes==3;eye=(classes==6)&(s>.30)&(v>.40)
 masks=[skin.astype(float),under.astype(float),frill.astype(float),eye.astype(float)]
 normal=sample(read(job/'texture_urls_0_normal.png'),uv);convention=measure(np.uint8(read(job/'texture_urls_0_normal.png')*255+.5));assert convention<-.15,convention;normal[...,1]=1-normal[...,1];nn=normal*2-1;normal=(nn/np.maximum(np.linalg.norm(nn,axis=-1,keepdims=True),.001)+1)/2
 rough=sample(read(job/'texture_urls_0_roughness.png','L'),uv);detail=np.clip(rough-ndimage.gaussian_filter(rough,4),-.12,.12);spec=np.zeros((N,N));rg=np.ones((N,N));metal=np.zeros((N,N))
 for cls in np.unique(classes[cov]):
  m=classes==cls;mt,base,band,sp=TABLE[int(cls)];spec[m]=sp*ao[m];rg[m]=np.clip(base+detail[m],*band);metal[m]=mt
 save(pad(img,cov),T/f'm516_{label}_basecolor_1k.png');save(pad(normal,cov),T/f'm516_{label}_normal_1k.png');save(pad(np.stack([spec,rg,metal],-1),cov),T/f'm516_{label}_metal_rough_1k.png');R.write_mask([ndimage.gaussian_filter(pad(m,cov),.6) for m in masks],T/f'm516_{label}_region_mask.png',size=N);Image.fromarray(classes).save(T/f'm516_{label}_material_classes.png');sets[label]={'img':img,'masks':masks,'classes':classes,'coverage':float(cov.mean()),'normal_convention':float(convention)}
counts=np.zeros(256,int)
for f in (P.parents[2]/'assets_dev/engine/sprites').glob('m516*.bmp'):counts+=np.bincount(np.asarray(Image.open(f)).ravel(),minlength=256)
a=pals['m516_a'];h,s,v=hsv(a.reshape(16,16,3));s=s.ravel();ids=np.arange(256);main=(ids>=128)&(ids<=245)&(s>.28);under=(ids>=128)&(ids<=245)&(s<=.28);frill=(ids>=4)&(ids<=112)&(s>.65)&(a[:,0]>a[:,1]*1.4);eye=np.isin(ids,[66,72,78,92,93,100,111,112]);regions=[np.where(m&(counts>0))[0] for m in [main,under,frill,eye]];ramps={k:[] for k in pals};ranges=[]
for region,idx in enumerate(regions):
 lum=np.concatenate([R.luminance(d['img'])[d['masks'][region]>.9] for d in sets.values()]);assert len(lum)>20 and len(idx)>3
 lo,hi=np.percentile(lum,[1,99]);lo=max(.0001,float(lo));hi=max(lo+.01,float(hi));ranges.append([lo,hi])
 # A single ordering of native A palette entries preserves the exact corresponding palette identities in B/C.
 order=idx[np.argsort(R.srgb_to_linear(a[idx])@LUMA)];weights=counts[order].astype(float);cdf=(np.cumsum(weights)-weights/2)/weights.sum();stops=np.linspace(.015,.985,16)
 for key,pal in pals.items():
  colors=R.srgb_to_linear(pal[order])*1.5;sampled=np.column_stack([np.interp(stops,cdf,colors[:,j]) for j in range(3)]);ramps[key].append({'range':[lo,hi],'colors':np.clip(sampled,0,1).tolist()})
cfg={'variants':list(pals),'palettes':PALETTES,'regions':['scales','underside','frills','iris'],'native_indices':[v.tolist() for v in regions],'materials':[{'base':name+'_A','prefix':name,'mask':f'm516_{label}_region_mask.png','regions':['scales','underside','frills','iris'],'ramps':ramps} for label,name in [('body','ThunderLizard'),('head','ThunderLizardHead')]],'report':{k:{'coverage':d['coverage'],'classes':{int(n):int((d['classes']==n).sum()) for n in np.unique(d['classes'])},'normal_source_convention':d['normal_convention']} for k,d in sets.items()}}
(T/'m516_ramps.json').write_text(json.dumps(cfg,indent=2)+'\n');print(json.dumps(cfg['report'],indent=2))
