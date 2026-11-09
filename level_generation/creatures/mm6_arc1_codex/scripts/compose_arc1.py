"""MM6 Archer: two 1K texture sets, native cloth ramps, material classes and padded masks."""
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
native={k:[] for k in ['arc1_a','arc1_b','arc1_c']}
for view in range(5):
 ims=[np.asarray(Image.open(P.parent/'mm6_arc1/native_variants'/f'arc1sta{view}_{pal}.png').convert('RGBA'),float)/255 for pal in [660,661,662]]
 a,b,c=ims;changed=(a[:,:,3]>.5)&(np.maximum(abs(a[:,:,:3]-b[:,:,:3]).max(2),abs(a[:,:,:3]-c[:,:,:3]).max(2))>8/255)&(a[:,:,:3].max(2)>.1)
 for key,im in zip(native,ims):native[key].append(im[:,:,:3][changed])
native={k:np.concatenate(v) for k,v in native.items()}
body_region=None;body_base=None;reports={}
for label,layer,suffix in [('body','UVMap',''),('head','HeadUV','_head')]:
 M=P/'meshy'/f'{label}_retexture_v1';rgb=load(M/'texture_urls_0_base_color.png');rough=load(M/'texture_urls_0_roughness.png','L')
 raster=np.load(P/'work'/f'uvraster_{layer}.npz');piece=raster['piece'];pos=raster['pos'];cov=piece>=0
 hsv=np.asarray(Image.fromarray((rgb*255).astype('uint8')).convert('HSV'),float)/255;h,s,v=hsv[:,:,0]*360,hsv[:,:,1],hsv[:,:,2]
 cls=np.where(cov,7,0).astype('uint8')
 region=np.zeros_like(cov)
 if label=='body':
  cloth=(piece==0)&(h>170)&(h<275)&(s>.12)
  region=cloth
  skin=np.isin(piece,[2,3,9,10])|((piece==0)&(pos[:,:,2]>1.31)&(np.abs(pos[:,:,0])<.13))
  cls[:]=8;cls[skin]=7;cls[cloth]=4
  cls[np.isin(piece,[4,13,14,15,16,17,18,19])]=1
  # Review 2 transfers the left leather to the right bracer after composition.
  cls[piece==11]=8
  boots=(piece==0)&(pos[:,:,2]<.85)&~cloth;rgb[boots]*=np.array([.83,.80,.77])
 else:
  # Match the body at the neckline; the dedicated head pass owns the face and hair.
  uv=raster['body_uv'];bodyrgb=load(P/'meshy/body_retexture_v1/texture_urls_0_base_color.png')
  coords=np.array([(1-uv[:,:,1])*N-.5,uv[:,:,0]*N-.5])
  neckrgb=np.stack([ndimage.map_coordinates(bodyrgb[:,:,k],coords,order=1,mode='nearest') for k in range(3)],axis=2)
  neck=np.clip((1.48-pos[:,:,2])/.045,0,1)*(piece==0)
  rgb=rgb*(1-neck[...,None])+neckrgb*neck[...,None]
  cls[piece==1]=3;cls[np.isin(piece,[6,8])]=6;cls[np.isin(piece,[20,22,23])]=7;cls[piece==24]=5
  rgb[piece==1]*=np.array([.78,.70,.70])
 ao=load(P/'work'/f'ao_{label}.png','L')
 # AO comes from nearby geometry; do not double-darken already painted socket interiors.
 rgb*= (1-.45*(1-np.clip(ao,.25,1)))[...,None]
 normal=load(M/'texture_urls_0_normal.png')
 score=NM.measure((normal*255+.5).astype('uint8'))
 if score<-.15:normal[:,:,1]=1-normal[:,:,1]
 detail=normal*2-1
 if label=='head':
  detail[:,:,:2]*=(1-neck[...,None]);detail[:,:,2]=detail[:,:,2]*(1-neck)+neck
 shape=load(P/'work'/f'shape_normal_{label}.png')*2-1
 shape[shape[:,:,2]<.2]=(0,0,1)
 # Keep the geometric bake; add the subdued fine Meshy surface detail in the same tangent space.
 combined=np.stack([shape[:,:,0]+.45*detail[:,:,0],shape[:,:,1]+.45*detail[:,:,1],shape[:,:,2]*detail[:,:,2]],axis=-1)
 combined/=np.maximum(np.linalg.norm(combined,axis=2,keepdims=True),1e-8)
 normal=combined*.5+.5
 spec=np.full((N,N),.12);rmap=np.full((N,N),.72)
 for cl,sp,rr in [(1,.12,.68),(3,.15,.70),(4,.05,.86),(5,.25,.7),(6,.65,.28),(7,.16,.69),(8,.18,.65)]:
  mask=cls==cl;spec[mask]=sp;rmap[mask]=np.clip(rr+(rough[mask]-.5)*.15,.1,.95)
 orm=np.stack([spec,rmap,np.zeros_like(spec)],axis=2)
 stem=f'arc1{suffix}'
 save(pad(rgb,cov),T/f'{stem}_basecolor_1k.png');save(pad(normal,cov),T/f'{stem}_normal_1k.png');save(pad(orm,cov),T/f'{stem}_metal_rough_1k.png')
 Image.fromarray(cls).save(T/f'{stem}_material_classes.png')
 R.write_mask([ndimage.gaussian_filter(pad(region.astype(float),cov),.65)],T/f'{stem}_region_mask.png',size=N)
 reports[label]={'covered_texels':int(cov.sum()),'region_texels':int(region.sum()),'normal_correlation_input':score,'classes':{str(c):int((cls==c).sum()) for c in np.unique(cls)}}
 if label=='body':body_region=region;body_base=rgb
lum=np.sort(R.luminance(body_base)[body_region]);lo,hi=np.percentile(lum,[2,98]);assert hi>lo and len(lum)>100
order=np.argsort(R.luminance(native['arc1_a']));ramps={}
base_mid=float(np.median(lum))
for variant,colors in native.items():
 linear=R.srgb_to_linear(colors)[order]
 # Use the native upper midtone hue; preserve the generated folds with a gentle luminance response.
 mid=np.median(linear[int(len(linear)*.65):int(len(linear)*.80)],axis=0)
 stops=[np.clip(mid*(max(x,1e-6)/base_mid)**.65,0,1) for x in np.linspace(lo,hi,16)]
 ramps[variant]=[{'range':[float(lo),float(hi)],'colors':np.round(stops,6).tolist()}]
cfg={'variants':list(native),'materials':[{'base':f'{prefix}_A','prefix':prefix,'mask':f'arc1{suffix}_region_mask.png','regions':['cloth'],'palettes':dict(zip(native,[660,661,662])),'ramps':ramps} for prefix,suffix in [('Archer',''),('ArcherHead','_head')]]}
(T/'arc1_ramps.json').write_text(json.dumps(cfg,indent=2)+'\n');(T/'compose_report.json').write_text(json.dumps(reports,indent=2)+'\n')
print(json.dumps(reports));print('NATIVE RAMP PIXELS',len(order))
