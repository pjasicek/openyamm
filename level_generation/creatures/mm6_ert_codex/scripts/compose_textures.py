"""One 1K body set and one 1K head set, matte stone, shared native palette ramps."""
import sys,json
import numpy as np
from pathlib import Path
from PIL import Image
from scipy import ndimage
P=Path(__file__).resolve().parents[1];T=P/'textures';T.mkdir(exist_ok=True)
sys.path.insert(0,str(P.parent/'claude_shared'));import region_variants as R
sys.path.insert(0,str(Path('tools').resolve()));import normal_map_convention as NC
N=1024
def load(path,mode='RGB'):
 return np.asarray(Image.open(path).convert(mode).resize((N,N),Image.Resampling.LANCZOS),np.float64)/255
def save(a,path):
 Image.fromarray(np.uint8(np.clip(a,0,1)*255+.5)).save(path)
sets={};report={}
for part,job,layer in [('body','body_texture_v1','UVMap'),('head','head_texture_v2','HeadUV')]:
 raw=P/'meshy'/job;coverage=np.load(P/'work'/f'uvraster_{layer}.npz')['coverage'];base=load(raw/'texture_urls_0_base_color.png')
 if part=='body':base*=.75;target=np.median(base[coverage],axis=0)
 else:base*=target/np.maximum(np.median(base[coverage],axis=0),1e-4)
 ao=load(P/'work'/f'ao_{part}.png','L')
 base*=1-.25*(1-np.maximum(ao,.35))[...,None]
 nearest=ndimage.distance_transform_edt(~coverage,return_distances=False,return_indices=True)
 base=base[tuple(nearest)];save(base,T/f'ert_{part}_basecolor_1k.png')
 normal=np.uint8(load(raw/'texture_urls_0_normal.png')*255+.5);correlation=NC.measure(normal)
 if correlation<=-.15:normal[...,1]=255-normal[...,1]
 Image.fromarray(normal).save(T/f'ert_{part}_normal_1k.png')
 rough=load(raw/'texture_urls_0_roughness.png','L');rough=np.clip(.90+.18*(rough-np.median(rough[coverage])),.82,1.)
 orm=np.stack([np.full((N,N),.16),rough,np.zeros((N,N))],axis=-1)
 save(orm,T/f'ert_{part}_metal_rough_1k.png')
 Image.new('RGBA',(N,N),(255,0,0,0)).save(T/f'ert_{part}_region_mask.png')
 sets[part]=(base,coverage);report[part]={'median_srgb':np.median(base[coverage],axis=0).tolist(),'source':job,'normal_correlation_before':correlation,'normal_green_flipped':correlation<=-.15}
# Reuse the validated Earth restoration's nonlinear native curves; they retain the dark green shadows.
vectors=json.loads((P.parent/'mm6_ert/recolor_vectors.json').read_text())
base=np.concatenate([sets[k][0] for k in ['body','head']],axis=0)
coverage=np.concatenate([sets[k][1] for k in ['body','head']],axis=0)
tiers={'ert_a':base};level=np.clip(np.rint(base@R.LUMA*255),0,255).astype(int)
for name,palette in [('ert_b','726'),('ert_c','727')]:
 srgb=np.array(vectors[palette])[level]
 # Native palettes carry sprite shading; the runtime stone receives its scene light.
 linear=R.srgb_to_linear(srgb)*1.35
 tiers[name]=np.where(linear<=.0031308,linear*12.92,1.055*np.maximum(linear,0)**(1/2.4)-.055).clip(0,1)
ramps,fit=R.fit_ramps(base,tiers,coverage.astype(float))
assert all(np.isfinite(np.array(v['colors'])).all() for v in ramps.values())
cfg={'variants':['ert_a','ert_b','ert_c'],'materials':[]}
for part,material in [('body','EarthElemental_A'),('head','EarthElementalHead_A')]:
 cfg['materials'].append({'base':material,'prefix':material[:-2],'mask':f'ert_{part}_region_mask.png','regions':['stone'],'palettes':{'ert_a':725,'ert_b':726,'ert_c':727},'ramps':{k:[v] for k,v in ramps.items()}})
(T/'ert_ramps.json').write_text(json.dumps(cfg,indent=2)+'\n')
report['ramp_fit']=fit;report['palette_source']='../mm6_ert/recolor_vectors.json (validated nonlinear native curves)'
(T/'composition.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
