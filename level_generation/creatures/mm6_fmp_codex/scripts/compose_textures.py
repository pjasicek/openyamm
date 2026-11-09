"""Separate 1K sets, matte fabric/skin and one shared native apron/cap palette channel."""
import json,sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
P=Path(__file__).resolve().parents[1];T=P/'textures';T.mkdir(exist_ok=True);N=1024
sys.path.insert(0,str(P.parent/'claude_shared'));import region_variants as R
sys.path.insert(0,str(Path('tools').resolve()));import normal_map_convention as NC
sets={};report={}
def load(path,mode='RGB'):
 return np.asarray(Image.open(path).convert(mode).resize((N,N),Image.Resampling.LANCZOS),float)/255
def save(a,path):Image.fromarray(np.uint8(np.clip(a,0,1)*255+.5)).save(path)
for part,job,layer in [('body','body_texture_v1','UVMap'),('head','head_texture_v2','HeadUV')]:
 raw=P/'meshy'/job;data=np.load(P/'work'/f'uvraster_{layer}.npz');coverage=data['coverage'];piece=data['piece'];pos=data['pos'];base=load(raw/'texture_urls_0_base_color.png')
 # Restrict the recolour to the separately modelled apron/cap and the narrow blue waist tie.
 region=np.isin(piece,[7,9]);blue=(base[...,2]>base[...,0]*1.07)&(base[...,2]>base[...,1]*.97)
 region|=np.isin(piece,[0,1])&(pos[...,2]>.99)&(pos[...,2]<1.09)&blue
 region&=coverage
 nearest=ndimage.distance_transform_edt(~coverage,return_distances=False,return_indices=True)
 ao=load(P/'work'/f'ao_{part}.png','L');base*=1-.15*(1-np.maximum(ao,.4))[...,None]
 if part=='head':
  uv=np.load(P/'work/head_body_uv.npy');bmap=load(P/'meshy/body_texture_v1/texture_urls_0_base_color.png')
  overlap=np.stack([ndimage.map_coordinates(bmap[...,c],[(1-uv[...,1])*N-.5,uv[...,0]*N-.5],order=1,mode='nearest') for c in range(3)],axis=-1)
  blend=np.clip((1.47-pos[...,2])/.03,0,1)*(piece==20)*coverage
  base=base*(1-blend[...,None])+overlap*blend[...,None]
 base=base[tuple(nearest)];mask=region[tuple(nearest)].astype(float)
 save(base,T/f'fmp_{part}_basecolor_1k.png');R.write_mask([mask],T/f'fmp_{part}_region_mask.png',N)
 normal=np.uint8(load(raw/'texture_urls_0_normal.png')*255+.5);correlation=NC.measure(normal)
 if correlation<=-.15:normal[...,1]=255-normal[...,1]
 if part=='head':
  normal=np.uint8(np.clip((normal.astype(float)-np.array([127.5,127.5,255]))*.4+np.array([127.5,127.5,255]),0,255))
 Image.fromarray(normal).save(T/f'fmp_{part}_normal_1k.png')
 rough=load(raw/'texture_urls_0_roughness.png','L');rough=np.clip(.84+.18*(rough-np.median(rough[coverage])),.68,.96)
 orm=np.stack([np.full((N,N),.16),rough,np.zeros((N,N))],axis=-1);save(orm,T/f'fmp_{part}_metal_rough_1k.png')
 sets[part]=(base,mask,coverage);report[part]={'source':job,'region_texels':int(region.sum()),'normal_correlation':correlation,'normal_green_flipped':correlation<=-.15}
# Match the native colour changes at corresponding sprite pixels; neutral clothes and skin are excluded.
native={k:[] for k in ('789','790','791')}
for v in range(5):
 imgs={k:np.asarray(Image.open(P.parent/'mm6_fmp/native_variants'/f'fmpstaa{v}_{k}.png').convert('RGBA'),float)/255 for k in native}
 changed=(imgs['790'][...,3]>.5)&(np.max(abs(imgs['789'][...,:3]-imgs['790'][...,:3]),axis=-1)>.025)&(np.max(abs(imgs['791'][...,:3]-imgs['790'][...,:3]),axis=-1)>.025)
 for k in native:native[k].append(imgs[k][...,:3][changed])
native={k:np.concatenate(v) for k,v in native.items()};nb=native['790'];good=(nb[:,2]>nb[:,0]*1.3)&(nb[:,2]>nb[:,1]*1.1)&(nb[:,2]>.4)
native_medians={k:np.median(v[good],axis=0) for k,v in native.items()}
base=np.concatenate([sets[k][0] for k in ('body','head')]);weight=np.concatenate([sets[k][1]*sets[k][2] for k in ('body','head')]);core=weight>.9;base_linear=R.srgb_to_linear(base);median=np.median(base_linear[core],axis=0)
tiers={'fmp_b':base}
for tier,k in [('fmp_a','789'),('fmp_c','791')]:
 c=np.clip(base_linear*(R.srgb_to_linear(native_medians[k])/median),0,1)
 tiers[tier]=np.where(c<=.0031308,c*12.92,1.055*c**(1/2.4)-.055)
ramps,fit=R.fit_ramps(base,tiers,weight);cfg={'variants':['fmp_a','fmp_b','fmp_c'],'materials':[]}
for part,name in [('body','PeasantF2_A'),('head','PeasantF2Head_A')]:
 cfg['materials'].append({'base':name,'prefix':name[:-2],'mask':f'fmp_{part}_region_mask.png','regions':['apron_cap'],'palettes':{'fmp_a':789,'fmp_b':790,'fmp_c':791},'ramps':{k:[ramps[k]] for k in cfg['variants']}})
(T/'fmp_ramps.json').write_text(json.dumps(cfg,indent=2));report['native_samples']=int(good.sum());report['ramp_fit']=fit
(T/'composition.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
