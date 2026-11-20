"""MM6 Lich: two 1K texture sets, native bracer ramps, material classes and padded masks."""
import json,sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True
sys.path.insert(0,str(P.parent/'claude_shared'));import region_variants as R
sys.path.insert(0,str(P.parents[2]/'tools'));import normal_map_convention as NM
T=P/'textures';T.mkdir(exist_ok=True);N=1024
def load(path,mode='RGB'):
 return np.asarray(Image.open(path).convert(mode).resize((N,N),Image.Resampling.LANCZOS),float)/255
def save(a,path):
 Image.fromarray((np.clip(a,0,1)*255+.5).astype('uint8')).save(path)
def pad(a,cov):
 _,inds=ndimage.distance_transform_edt(~cov,return_indices=True);out=a[tuple(inds)];out[cov]=a[cov];return out
native={k:[] for k in ['lch_a','lch_b','lch_c']}
for view in range(5):
 ims=[np.asarray(Image.open(P.parent/'mm6_lch/native_variants'/f'lchstda{view}_{pal}.png').convert('RGBA'),float)/255 for pal in [763,764,765]]
 a,b,c=ims;changed=(a[:,:,3]>.5)&(np.maximum(abs(a[:,:,:3]-b[:,:,:3]).max(2),abs(a[:,:,:3]-c[:,:,:3]).max(2))>8/255)&(a[:,:,:3].max(2)>.1)
 for key,im in zip(native,ims):native[key].append(im[:,:,:3][changed])
native={k:np.concatenate(v) for k,v in native.items()}
body_region=None;body_base=None;reports={}
crown=[101,136,144,145,150,155,157,158,159,161,166,167,168,169,170,171,172,173,174]
for label,layer,suffix in [('body','UVMap',''),('head','HeadUV','_head')]:
 M=P/'meshy'/f'{label}_retexture_v1';rgb=load(M/'texture_urls_0_base_color.png');rough=load(M/'texture_urls_0_roughness.png','L')
 raster=np.load(P/'work'/f'uvraster_{layer}.npz');piece=raster['piece'];pos=raster['pos'];cov=piece>=0
 hsv=np.asarray(Image.fromarray((rgb*255).astype('uint8')).convert('HSV'),float)/255;h,s,v=hsv[:,:,0]*360,hsv[:,:,1],hsv[:,:,2]
 cls=np.where(cov,5,0).astype('uint8')
 if label=='body':
  cls[np.isin(piece,[1,2,13,14,15,33])]=9
  cls[np.isin(piece,[3,4,5,16,17,26,27,28,35])]=8
  # The actual thigh and hip bones keep the bone class; small rigid chest/vertebral pieces are bone.
  ruby=(h<14)&(s>.65)&(v>.35)&np.isin(piece,[1,2,3,4,14,15,33])
  cls[ruby]=11
  region=np.isin(piece,[14,15])&~ruby
  # Silver rim on the belt is a small native palette detail; its dark leather centre stays fixed.
  region|=(piece==5)&(s<.3)&(v>.27)
  # Grade the large materials without inventing replacement paint.
  for mask,gain in [(np.isin(piece,[3,4]),.62),(np.isin(piece,[16,17,26,27,28,35]),.88),((cls==9)&~region,.8)]:
   rgb[mask]*=gain
 else:
  cls[np.isin(piece,crown)]=9;cls[np.isin(piece,[102,103])]=6
  ruby=(h<15)&(s>.6)&(v>.2)&np.isin(piece,crown)
  cls[ruby]=11
  region=np.zeros_like(cov)
 # Bone remains warm ivory; red eye cores stay as generated.
 rgb[cls==5]*=np.array([.94,.92,.90])
 ao=load(P/'work'/f'ao_{label}.png','L')
 # AO comes from nearby geometry; do not double-darken already painted socket interiors.
 rgb*= (1-.45*(1-np.clip(ao,.25,1)))[...,None]
 normal=load(M/'texture_urls_0_normal.png')
 score=NM.measure((normal*255+.5).astype('uint8'))
 if score<-.15:normal[:,:,1]=1-normal[:,:,1]
 detail=normal*2-1;shape=load(P/'work'/f'shape_normal_{label}.png')*2-1
 shape[shape[:,:,2]<.2]=(0,0,1)
 # Keep the geometric bake; add the subdued fine Meshy surface detail in the same tangent space.
 combined=np.stack([shape[:,:,0]+.45*detail[:,:,0],shape[:,:,1]+.45*detail[:,:,1],shape[:,:,2]*detail[:,:,2]],axis=-1)
 combined/=np.maximum(np.linalg.norm(combined,axis=2,keepdims=True),1e-8)
 normal=combined*.5+.5
 spec=np.full((N,N),.25);rmap=np.full((N,N),.72)
 for cl,sp,rr in [(5,.25,.75),(8,.12,.86),(9,.9,.4),(6,.7,.25),(11,.5,.45)]:
  mask=cls==cl;spec[mask]=sp;rmap[mask]=np.clip(rr+(rough[mask]-.5)*.15,.1,.95)
 orm=np.stack([spec,rmap,np.zeros_like(spec)],axis=2)
 stem=f'lch{suffix}'
 save(pad(rgb,cov),T/f'{stem}_basecolor_1k.png');save(pad(normal,cov),T/f'{stem}_normal_1k.png');save(pad(orm,cov),T/f'{stem}_metal_rough_1k.png')
 Image.fromarray(cls).save(T/f'{stem}_material_classes.png')
 R.write_mask([ndimage.gaussian_filter(pad(region.astype(float),cov),.65)],T/f'{stem}_region_mask.png',size=N)
 reports[label]={'covered_texels':int(cov.sum()),'region_texels':int(region.sum()),'normal_correlation_input':score,'classes':{str(c):int((cls==c).sum()) for c in np.unique(cls)}}
 if label=='body':body_region=region;body_base=rgb
lum=np.sort(R.luminance(body_base)[body_region]);lo,hi=np.percentile(lum,[2,98]);assert hi>lo and len(lum)>100
order=np.argsort(R.luminance(native['lch_a']));ramps={}
for variant,colors in native.items():
 linear=R.srgb_to_linear(colors)[order];stops=[]
 for i in range(16):
  quantile=np.clip(np.searchsorted(lum,lo+(hi-lo)*i/15)/len(lum),.10,.97);j=int(quantile*(len(linear)-1));w=max(4,len(linear)//50)
  stops.append(np.median(linear[max(0,j-w):j+w],axis=0))
 ramps[variant]=[{'range':[float(lo),float(hi)],'colors':np.round(stops,6).tolist()}]
cfg={'variants':list(native),'materials':[{'base':f'{prefix}_A','prefix':prefix,'mask':f'lch{suffix}_region_mask.png','regions':['tier_metal'],'palettes':dict(zip(native,[763,764,765])),'ramps':ramps} for prefix,suffix in [('Lich',''),('LichHead','_head')]]}
(T/'lch_ramps.json').write_text(json.dumps(cfg,indent=2)+'\n');(T/'compose_report.json').write_text(json.dumps(reports,indent=2)+'\n')
print(json.dumps(reports));print('NATIVE RAMP PIXELS',len(order))
