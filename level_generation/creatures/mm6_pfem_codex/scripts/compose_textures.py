"""Shared 1K body/head maps and palette-derived green/brown/teal garment ramps."""
import json,sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
P=Path(__file__).resolve().parents[1];T=P/'textures';T.mkdir(exist_ok=True)
sys.path.insert(0,str(P.parent/'claude_shared'));import region_variants as R
N=1024;PAL={'pfem_a':786,'pfem_b':787,'pfem_c':788}
def load(f,mode='RGB'):
 return np.asarray(Image.open(f).convert(mode).resize((N,N),Image.Resampling.LANCZOS),float)/255
def save(a,f):
 Image.fromarray(np.uint8(np.clip(a,0,1)*255+.5)).save(f,optimize=True)
def pad(a,cov):
 ix=ndimage.distance_transform_edt(~cov,return_distances=False,return_indices=True)
 out=a[tuple(ix)];out[cov]=a[cov];return out
def hsv(a):
 h=np.asarray(Image.fromarray(np.uint8(np.clip(a,0,1)*255)).convert('HSV'),float)/255
 return h[...,0]*360,h[...,1],h[...,2]
cols={k:[] for k in PAL};skins=[]
for v in range(5):
 ims={k:np.asarray(Image.open(P.parent/'mm6_pfem/native_variants'/f'pfemsta{v}_{pal}.png').convert('RGBA'),float)/255 for k,pal in PAL.items()}
 a=ims['pfem_a'];opaque=a[...,3]>.5;changed=opaque&(np.maximum(abs(ims['pfem_b'][...,:3]-a[...,:3]).max(-1),abs(ims['pfem_c'][...,:3]-a[...,:3]).max(-1))>8/255)
 h,s,val=hsv(a[...,:3])
 skins.append(a[...,:3][opaque&~changed&(h>8)&(h<40)&(s>.15)&(s<.55)&(val>.6)])
 for k in PAL:cols[k].append(ims[k][...,:3][changed])
cols={k:np.concatenate(v) for k,v in cols.items()};skin_target=np.median(np.concatenate(skins),axis=0)
print('NATIVE skin target',np.round(skin_target*255).tolist())
sets={}
for suffix,job,layer in [('', 'retexture_v1','UVMap'),('_head','head_retexture_v1','HeadUV')]:
 M=P/'meshy'/job;raster=np.load(P/'work'/f'uvraster_{layer}.npz');piece=raster['piece'];pos=raster['pos'];cov=piece>=0
 base=load(M/'texture_urls_0_base_color.png');normal=load(M/'texture_urls_0_normal.png');rough=load(M/'texture_urls_0_roughness.png','L')
 h,s,val=hsv(base)
 classes={'skin':np.isin(piece,[1,3,4,8,9,10,11]),'hair':np.isin(piece,[2,19]),'leather':np.isin(piece,[5,6,12,14,15,18]),'gold':np.isin(piece,[7,13]),'cloth':np.isin(piece,[0,100])}
 # The generated garment includes the exposed upper-back panel. Classify its
 # warm skin paint as skin too; Meshy projected a fragment of the braid onto it.
 if not suffix:
  panel=(piece==0)&(pos[...,1]>.015)&(abs(pos[...,0])<.10)&(pos[...,2]>1.27)&(pos[...,2]<1.43)&(h>5)&(h<55)&(s>.13)
  classes['skin'] |= panel
  classes['cloth'] &= ~panel
 # Only the green bodice and two green hem bands change between native palettes.
 region=classes['cloth']&(h>65)&(h<175)&(s>.18)&(base[...,1]>base[...,0]*1.04)
 if suffix:
  face=load(P/'work/near_face_color.png')
  distance=np.load(P/'work/near_face_dist.npy')
  ellipse=np.hypot((pos[...,0]+.007)/.085,(pos[...,2]-1.493)/.080)
  fw=np.clip((1.12-ellipse)/.20,0,1)*(piece==1)*(pos[...,1]<-.035)*(distance<10)
  fw=fw*fw*(3-2*fw)
  base=base*(1-fw[...,None])+face*fw[...,None]
  normal=normal*(1-fw[...,None])+np.array([.5,.5,1])*fw[...,None]
  h,s,val=hsv(base)
 # One tone adjustment preserves painted shading, lips, eyes and fingernails.
 sk=classes['skin']&(h>9)&(h<42)&(s>.13)&(s<.55)&(val>.45)
 gain=skin_target/np.maximum(np.median(base[sk],axis=0),.02)
 base[classes['skin']]=np.clip(base[classes['skin']]*gain,0,1)
 # The return projected white cuffs onto wrist skin and left faceted neck shadows.
 # Skin regions use one continuous tone; facial features retain the head-model paint.
 if not suffix:
  m=classes['skin'];lum=R.luminance(base);blur=ndimage.gaussian_filter(lum*m,3)/np.maximum(ndimage.gaussian_filter(m.astype(float),3),1e-5)
  detail=np.clip(lum/np.maximum(blur,1e-5),.975,1.025)
  base[m]=skin_target[None,:]*detail[m,None]
  normal[m]=(.5,.5,1)
 else:
  w=np.clip((1.447-pos[...,2])/.028,0,1)*(piece==1)
  w=w*w*(3-2*w);base=base*(1-w[...,None])+skin_target*w[...,None]
  normal=normal*(1-w[...,None])+np.array([.5,.5,1])*w[...,None]
 # Preserve folds while reducing the amplified speckle in the green fabric.
 lum=R.luminance(base);blur=ndimage.gaussian_filter(lum*region,2.2)/np.maximum(ndimage.gaussian_filter(region.astype(float),2.2),1e-5)
 softened=blur+.2*(lum-blur)
 base[region]*=(softened[region]/np.maximum(lum[region],1e-5))[:,None]
 hair=classes['hair']
 if hair.any():
  gain=(np.array([105,73,52])/255/np.maximum(np.median(base[hair],axis=0),.02))**.45
  base[hair]=np.clip(base[hair]*gain,0,1)
  h,sat,value=hsv(base);projected_band=hair&(value>.65)&(sat<.45)
  if projected_band.any():
   keep=hair&~projected_band;index=ndimage.distance_transform_edt(~keep,return_distances=False,return_indices=True)
   base[projected_band]=base[tuple(index)][projected_band]
   normal[projected_band]=(.5,.5,1)
 spec=np.full((N,N),.1);rgh=np.full((N,N),.85)
 for key,sp,rg in [('skin',.25,.68),('hair',.12,.78),('leather',.25,.65),('gold',.7,.32),('cloth',.08,.9)]:
  m=classes[key]
  if m.any():
   spec[m]=sp;rgh[m]=np.clip(rg+.25*(rough[m]-np.median(rough[m])),.2,1)
 sets[suffix]={'base':base,'normal':normal,'cov':cov,'piece':piece,'pos':pos,'region':region}
 save(pad(base,cov),T/f'pfem{suffix}_basecolor_1k.png')
 save(pad(normal,cov),T/f'pfem{suffix}_normal_1k.png')
 save(pad(np.stack((spec,rgh,np.zeros_like(spec)),-1),cov),T/f'pfem{suffix}_metal_rough_1k.png')
 R.write_mask([ndimage.gaussian_filter(pad(region.astype(float),cov),.6)],T/f'pfem{suffix}_region_mask.png',size=N)
 print('TEXTURE',suffix or 'body','coverage',round(cov.mean(),3),'recolourable texels',int(region.sum()),'skin gain',np.round(gain,3).tolist())
# Match native changed pixels by the base cloth's luminance rank.
lum=np.sort(R.luminance(sets['']['base'])[sets['']['region']]);lo,hi=np.percentile(lum,[2,98])
select=cols['pfem_a'].max(1)>.08
order=np.argsort(R.srgb_to_linear(cols['pfem_a'][select])@np.array([.2126,.7152,.0722]))
ramps={}
for key in PAL:
 lin=R.srgb_to_linear(cols[key][select])[order];stops=[]
 for v in np.linspace(lo,hi,16):
  rank=np.clip(np.searchsorted(lum,v)/len(lum),.12,.98);i=int(rank*(len(lin)-1));w=max(3,len(lin)//50)
  stops.append(np.median(lin[max(0,i-w):min(len(lin),i+w+1)],axis=0))
 mid=stops[8];stops=[mid+.5*(x-mid) for x in stops]
 ramps[key]=[{'range':[float(lo),float(hi)],'colors':[x.tolist() for x in stops]}]
config={'variants':list(PAL),'materials':[]}
for suffix,material in [('', 'Peasant'),('_head','PeasantHead')]:
 config['materials'].append({'base':material+'_A','prefix':material,'mask':f'pfem{suffix}_region_mask.png','regions':['green_cloth'],'palettes':PAL,'ramps':ramps})
(T/'pfem_ramps.json').write_text(json.dumps(config,indent=2)+'\n')
