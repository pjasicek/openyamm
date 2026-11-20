"""Compose shared Raven Man materials and native palette ramps; preserve the feather vane sheen."""
import json,sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
P=Path(__file__).resolve().parents[1];R=P.parents[2];T=P/'textures';T.mkdir(exist_ok=True);N=1024
sys.path[:0]=[str(P.parent/'claude_shared'),str(R/'tools')]
import region_variants as RV,material_classes_to_orm as MC,tier_textures as TT,normal_map_convention as NC
MC.TABLE[2]=(0,.72,(.65,.80),.3)
def load(p,mode='RGB'):return np.asarray(Image.open(p).convert(mode).resize((N,N),Image.Resampling.LANCZOS),float)/255
def save(a,p):Image.fromarray(np.uint8(np.clip(a,0,1)*255+.5)).save(p,optimize=True)
def hsv(a):
 x=np.asarray(Image.fromarray(np.uint8(np.clip(a,0,1)*255)).convert('HSV'),float)/255
 return x[...,0]*360,x[...,1],x[...,2]
def pad(a,c):
 _,(iy,ix)=ndimage.distance_transform_edt(~c,return_indices=True)
 out=a[iy,ix];out[c]=a[c];return out
def srgb(x):return np.where(x<=.0031308,x*12.92,1.055*np.maximum(x,0)**(1/2.4)-.055)
pal={f'raven_{tier}':np.frombuffer((R/f'assets_dev/worlds/mm8/textures/Pal{number}.act').read_bytes()[:768],np.uint8).reshape(256,3)/255 for tier,number in zip('abc',(585,586,587))}
ids=np.arange(8,34);lum=RV.luminance(pal['raven_a'][ids]);order=np.argsort(lum);lum=lum[order];ids=ids[order]
ramps={k:[{'range':[.01,.30],'colors':np.stack([np.interp(np.linspace(lum[0],lum[-1],16),lum,RV.srgb_to_linear(p[ids])[:,i]) for i in range(3)],axis=1).tolist()}] for k,p in pal.items()}
report={'palette_indices':ids.tolist(),'feather_material':{'class':2,'roughness':.72,'specular_mask':.3},'sets':{}}
configs=[]
for kind,layer,prefix,mat in [('body','UVMap','raven','Raven'),('head','HeadUV','raven_head','RavenHead'),('polearm','PolearmUV','raven_polearm','RavenPolearm')]:
 job=P/('meshy/polearm_v1' if kind=='polearm' else f'meshy/{kind}_texture_v{2 if kind=="head" else 1}')
 raster=np.load(P/f'work/uvraster_{layer}.npz');piece,pos=raster['piece'],raster['pos'];cov=piece>=0
 base=load(job/'texture_urls_0_base_color.png');h,s,v=hsv(base)
 cls=np.zeros((N,N),np.uint8);cls[cov]=1;region=np.zeros_like(cov)
 if kind=='body':
  cls[cov&(piece>=1000)]=2
  cls[cov&np.isin(piece,[6,8,11,14,15])]=8
  cls[cov&np.isin(piece,[7,16,17,19,22,23,24,25,26,27,28,29,30,31,32,33,34,35])]=9
  cls[cov&(piece==1)&(pos[...,2]<.17)]=4
  region=cov&np.isin(piece,[8,11])
 elif kind=='head':
  cls[cov]=2;cls[cov&np.isin(piece,[20,21])]=6
  beak=cov&(piece==2)&(pos[...,1]<-.15)&(pos[...,2]>1.59)&(h<75)&(s>.22)
  cls[beak]=4
  assert beak.sum()>500
 else:
  cls[cov]=9
  wood=cov&(h>12)&(h<65)&(s>.20);cls[wood]=10
  cls[wood&(v<.25)]=8
  region=cov&(h>80)&(h<175)&(s>.25)
 if kind!='polearm':
  ao=load(P/f'work/ao_{layer}.png','L');base[cov]*=(.7+.3*np.maximum(ao[cov],.45))[:,None]
 if region.any():
  x=RV.luminance(base[region]);lo,hi=np.log(np.percentile(x,[1,99]));assert hi>lo
  tone=np.clip((np.log(np.maximum(x,1e-6))-lo)/(hi-lo),0,1)
  target=.01+.29*tone;base[region]=srgb(np.clip(RV.srgb_to_linear(base[region])*(target/np.maximum(x,1e-6))[:,None],0,1))
  assert region.sum()>1000,(kind,region.sum())
 silver=(cls==9)&~region
 if silver.any():
  median=float(np.median(base[silver]));base[silver]=np.clip(base[silver]*max(1,.74/max(.1,median)),0,.92)
 base=pad(base,cov);save(base,T/f'{prefix}_basecolor_1k.png')
 normal=pad(load(job/'texture_urls_0_normal.png'),cov);correlation=NC.measure(np.uint8(normal*255+.5))
 if correlation<=-.15:normal[...,1]=1-normal[...,1]
 save(normal,T/f'{prefix}_normal_1k.png')
 labels=MC.fill_nearest(cls);rough=MC.roughness_map(labels,pad(load(job/'texture_urls_0_roughness.png','L'),cov),1)
 spec=np.zeros_like(rough);metal=np.zeros_like(rough)
 for label in np.unique(labels):metal[labels==label]=MC.TABLE[int(label)][0];spec[labels==label]=MC.TABLE[int(label)][3]
 save(np.stack([spec,rough,metal],-1),T/f'{prefix}_metal_rough_1k.png')
 weight=ndimage.gaussian_filter(pad(region.astype(float),cov),.7)
 RV.write_mask([weight],T/f'{prefix}_region_mask.png',size=N)
 Image.fromarray(cls).save(T/f'{prefix}_material_classes.png')
 configs.append({'base':mat+'_A','prefix':mat,'mask':f'{prefix}_region_mask.png','regions':['native_colour'],'ramps':ramps})
 mask=load(T/f'{prefix}_region_mask.png','RGBA')
 for tier in pal:save(TT.apply(base,mask,ramps[tier]),T/f'{prefix}_preview_{tier}.png')
 report['sets'][kind]={'coverage':float(cov.mean()),'region_texels':int(region.sum()),'class_pixels':{str(int(c)):int((cls==c).sum()) for c in np.unique(cls)},'normal_input_correlation':correlation,'normal_green_flipped':bool(correlation<=-.15)}
(T/'raven_ramps.json').write_text(json.dumps({'variants':list(pal),'materials':configs},indent=2)+'\n')
(T/'composition.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
