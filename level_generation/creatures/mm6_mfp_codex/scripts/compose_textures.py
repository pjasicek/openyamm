"""Compose shared 1K materials, measured native skin luminance, and blouse-only palette ramps."""
import json,sys,numpy as np
from pathlib import Path
from PIL import Image
from scipy import ndimage
from scipy.spatial import cKDTree
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P.parent/'claude_shared'));import region_variants as R
sys.path.insert(0,str(P.parents[2]/'tools'));import normal_map_convention as NM
T=P/'textures';N=1024;lumw=np.array([.2126,.7152,.0722])
def load(path,mode='RGB'):return np.asarray(Image.open(path).convert(mode).resize((N,N),Image.Resampling.LANCZOS),float)/255
def save(x,path):Image.fromarray((np.clip(x,0,1)*255+.5).astype('uint8')).save(path)
def pad(x,cov):
 _,ix=ndimage.distance_transform_edt(~cov,return_indices=True);return x[tuple(ix)]
def srgb(x):return np.where(x<=.0031308,x*12.92,1.055*np.clip(x,0,None)**(1/2.4)-.055)
# Explicit native front skin sampling regions; cyan, gold and outlines outside them are excluded.
native_path=P.parent/'mm6_mfp/native/mfpstaa0.png';im=Image.open(native_path).convert('RGB');rgb=np.asarray(im,float)/255;hsv=np.asarray(im.convert('HSV'),float)/255;y,x=np.indices(rgb.shape[:2]);mask=(((x>128)&(x<151)&(y>14)&(y<41))|((x>104)&(x<122)&(y>77)&(y<132))|((x>160)&(x<174)&(y>73)&(y<133)))&(hsv[:,:,0]*360<42)&(hsv[:,:,1]>.18)&(hsv[:,:,2]>.13)
ref=np.sort(R.srgb_to_linear(rgb)[mask]@lumw);assert len(ref)>1000
Image.fromarray((mask*255).astype('uint8')).save(T/'native_skin_sample.png')
report={'native_skin':{'file':str(native_path.relative_to(P.parent)),'pixels':len(ref),'mean_linear':float(ref.mean()),'p90_linear':float(np.percentile(ref,90)),'p95_linear':float(np.percentile(ref,95))},'sets':{}}
region=None;base=None
for label,layer,suffix in [('body','UVMap',''),('head','HeadUV','_head')]:
 M=P/f'meshy/{label}_retexture_v{2 if label=="body" else 1}';a=load(M/'texture_urls_0_base_color.png');rough=load(M/'texture_urls_0_roughness.png','L');normal=load(M/'texture_urls_0_normal.png');data=np.load(P/f'work/uvraster_{layer}.npz');part=data['piece'];pos=data['pos'];cov=part>=0
 hsv=np.asarray(Image.fromarray((a*255).astype('uint8')).convert('HSV'),float)/255;h=hsv[:,:,0]*360;sat=hsv[:,:,1];value=hsv[:,:,2];cls=np.zeros((N,N),np.uint8);cls[cov]=7;reg=np.zeros((N,N),bool)
 if label=='body':
  reg=(part==0)&(h>70)&(h<175)&(sat>.12)&(pos[:,:,2]>1.11);skin=np.isin(part,[4,5])|((part==0)&~reg&(((pos[:,:,2]<.89)&(pos[:,:,2]>.075))|((pos[:,:,2]>.98)&(pos[:,:,2]<1.15))|(pos[:,:,2]>1.32)))
  cls[np.isin(part,[1,6])|reg]=4;cls[part==3]=3;cls[np.isin(part,[13,14,16,17])]=1;cls[(part>=7)&~np.isin(part,[13,14,16,17])]=6;cls[skin]=7
 else:
  skin=(part==0)&(h<44)&(sat>.16)&(value>.17)&(pos[:,:,2]<1.61)
  cls[(part==0)&~skin]=3;cls[np.isin(part,[8,9])]=5;cls[(part>19)]=6;cls[np.isin(part,[15,19])]=7
 # Remove generated speckling before histogram fitting so native contrast follows skin planes.
 if label=='body':
  den=ndimage.gaussian_filter(skin.astype(float),3)
  for channel in range(3):
   smooth=ndimage.gaussian_filter(a[:,:,channel]*skin,3)/np.maximum(den,1e-8);a[:,:,channel][skin]=smooth[skin]
 ao=load(P/f'work/ao_{label}.png','L');a*=(1-.40*(1-np.clip(ao,.25,1)))[...,None]
 # Monotone quantile fit matches both native mean and highlight percentiles without flat colour replacement.
 lin=R.srgb_to_linear(a);L=lin@lumw;source=np.sort(L[skin]);quant=np.interp(L[skin],source,np.linspace(0,1,len(source)));target=np.interp(quant,np.linspace(0,1,len(ref)),ref);lin[skin]*=(target/np.maximum(L[skin],1e-8))[:,None];a=srgb(lin)
 final=R.srgb_to_linear(np.clip(a,0,1))[skin]@lumw
 score=NM.measure((normal*255+.5).astype('uint8'))
 if score<-.15:normal[:,:,1]=1-normal[:,:,1]
 # Fine normal detail is subdued on skin and cloth; base geometry retains its sculpted planes.
 nn=normal*2-1;nn[:,:,:2]*=.55;nn/=np.maximum(np.linalg.norm(nn,axis=2,keepdims=True),1e-8);normal=nn*.5+.5
 spec=np.full((N,N),.10);rmap=np.full((N,N),.78)
 for cl,sp,rr in [(1,.10,.75),(3,.10,.77),(4,.05,.87),(5,.30,.32),(6,.45,.46),(7,.10,.79)]:
  m=cls==cl;spec[m]=sp;rmap[m]=np.clip(rr+(rough[m]-.5)*.10,.25,.95)
 orm=np.stack([spec,rmap,np.zeros_like(spec)],axis=2);stem='mfp'+suffix
 save(pad(a,cov),T/f'{stem}_basecolor_1k.png');save(pad(normal,cov),T/f'{stem}_normal_1k.png');save(pad(orm,cov),T/f'{stem}_metal_rough_1k.png');Image.fromarray(cls).save(T/f'{stem}_material_classes.png');R.write_mask([ndimage.gaussian_filter(pad(reg.astype(float),cov),.6)],T/f'{stem}_region_mask.png',size=N)
 report['sets'][label]={'skin_texels':int(skin.sum()),'mean_linear':float(final.mean()),'p90_linear':float(np.percentile(final,90)),'p95_linear':float(np.percentile(final,95)),'normal_correlation':score,'region_texels':int(reg.sum())}
 assert abs(final.mean()-ref.mean())<.01
 if label=='body':region=reg;base=a
native={k:[]for k in ['mfp_a','mfp_b','mfp_c']}
for view in range(5):
 ims=[np.asarray(Image.open(P.parent/f'mm6_mfp/native_variants/mfpstaa{view}_{pal}.png').convert('RGB'),float)/255 for pal in [792,793,794]];a,b,c=ims;changed=np.maximum(abs(a-b).max(2),abs(a-c).max(2))>8/255
 for key,im in zip(native,ims):native[key].append(im[changed])
L=np.sort(R.luminance(base)[region]);lo,hi=np.percentile(L,[2,98]);ramps={}
for key,arrays in native.items():
 colors=R.srgb_to_linear(np.concatenate(arrays));colors=colors[np.argsort(colors@lumw)];ramp=np.stack([np.interp(np.linspace(0,1,16),np.linspace(0,1,len(colors)),colors[:,k])for k in range(3)],axis=1)*1.35;ramps[key]=[{'range':[float(lo),float(hi)],'colors':np.clip(ramp,0,1).round(6).tolist()}]
cfg={'variants':list(native),'materials':[{'base':prefix+'_A','prefix':prefix,'mask':'mfp'+suffix+'_region_mask.png','regions':['blouse'],'palettes':dict(zip(native,[792,793,794])),'ramps':ramps}for prefix,suffix in [('PeasantF3',''),('PeasantF3Head','_head')]]}
(T/'mfp_ramps.json').write_text(json.dumps(cfg,indent=2));(T/'compose_report.json').write_text(json.dumps(report,indent=2))
# Shared dull-grey prop textures, with enough roughness to preserve the native steel appearance.
kdir=T/'knife';kdir.mkdir(exist_ok=True);M=P/'meshy/knife_geometry_v1';a=load(M/'texture_urls_0_base_color.png');normal=load(M/'texture_urls_0_normal.png');rough=load(M/'texture_urls_0_roughness.png','L');metal=load(M/'texture_urls_0_metallic.png','L')
score=NM.measure((normal*255+.5).astype('uint8'))
if score<-.15:normal[:,:,1]=1-normal[:,:,1]
save(a,kdir/'basecolor_1k.png');save(normal,kdir/'normal_1k.png');save(np.stack([.15+.30*metal,np.maximum(.58,rough),np.zeros_like(metal)],axis=2),kdir/'metal_rough_1k.png');Image.fromarray(np.where(metal>.5,6,1).astype('uint8')).save(kdir/'material_classes.png')
print(json.dumps(report,indent=2))
