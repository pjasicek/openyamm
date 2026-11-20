"""Compose separate 1K maps, restrained materials and the original tunic palette ramp."""
import json,sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
from feedback_texture_cleanup import clean
P=Path(__file__).resolve().parents[1];T=P/'textures';T.mkdir(exist_ok=True);N=1024
sys.path.insert(0,str(P.parent/'claude_shared'));import region_variants as R
sys.path.insert(0,str(Path('tools').resolve()));import normal_map_convention as NC
sets={};report={}
def load(path,mode='RGB'):
 return np.asarray(Image.open(path).convert(mode).resize((N,N),Image.Resampling.LANCZOS),float)/255
def save(a,path):Image.fromarray(np.uint8(np.clip(a,0,1)*255+.5)).save(path)
# Carry the painted head into its repaired non-overlapping UV layout. Face charts retain their orientation;
# hair micro-normals are flattened because the hair charts were unfolded in new tangent frames.
r=np.load(P/'work/head_reprojection.npz');cov=r['coverage'];uv=r['srcuv'];pc=r['piece'];nearest=ndimage.distance_transform_edt(~cov,return_distances=False,return_indices=True)
H=P/'texturing/head_reprojected';H.mkdir(exist_ok=True)
for kind in ['base_color','normal','roughness','metallic']:
 raw=np.asarray(Image.open(P/'meshy/head_texture_v1'/f'texture_urls_0_{kind}.png').convert('RGB'),float)/255
 h,w=raw.shape[:2]
 arr=np.stack([ndimage.map_coordinates(raw[...,c],[(1-uv[...,1])*h-.5,uv[...,0]*w-.5],order=1,mode='nearest') for c in range(3)],axis=-1)
 if kind=='normal':arr[pc==2]=[.5,.5,1]
 arr=arr[tuple(nearest)];save(arr,H/f'texture_urls_0_{kind}.png')
# Repack the restored arms with the body; sample the original return through the recorded surface mapping.
r=np.load(P/'work/body_reprojection.npz');cov=r['coverage'];uv=r['srcuv'];replaced=r['replaced'];nearest=ndimage.distance_transform_edt(~cov,return_distances=False,return_indices=True)
B=P/'texturing/body_reprojected';B.mkdir(exist_ok=True)
for kind in ['base_color','normal','roughness','metallic']:
 raw=np.asarray(Image.open(P/'meshy/body_texture_v1'/f'texture_urls_0_{kind}.png').convert('RGB'),float)/255
 h,w=raw.shape[:2]
 arr=np.stack([ndimage.map_coordinates(raw[...,c],[(1-uv[...,1])*h-.5,uv[...,0]*w-.5],order=1,mode='nearest') for c in range(3)],axis=-1)
 if kind=='normal':arr[replaced]=[.5,.5,1]
 arr=arr[tuple(nearest)];save(arr,B/f'texture_urls_0_{kind}.png')
for part,raw,layer in [('body',B,'UVMap'),('head',H,'HeadUV')]:
 data=np.load(P/'work'/f'uvraster_{layer}.npz');coverage=data['coverage'];piece=data['piece'];pos=data['pos'];base=load(raw/'texture_urls_0_base_color.png')
 base,repair_mask,repairs=clean(part,base,piece,pos,coverage)
 green=(base[...,1]>base[...,0]*1.06)&(base[...,1]>base[...,2]*1.09)
 region=(piece==0)&green&coverage if part=='body' else np.zeros_like(coverage)
 # Do not tint leather belts/cuffs or the brass buckle. Fill tiny cloth colour/shadow gaps only.
 region=ndimage.binary_closing(region,iterations=2)&(piece==0)&coverage
 nearest=ndimage.distance_transform_edt(~coverage,return_distances=False,return_indices=True)
 ao=load(P/'work'/f'ao_{part}.png','L');base*=1-.18*(1-np.maximum(ao,.4))[...,None]
 base=base[tuple(nearest)];mask=region[tuple(nearest)].astype(float)
 save(base,T/f'pman_{part}_basecolor_1k.png');R.write_mask([mask],T/f'pman_{part}_region_mask.png',N)
 normal=np.uint8(load(raw/'texture_urls_0_normal.png')*255+.5);correlation=NC.measure(normal)
 if correlation<=-.15:normal[...,1]=255-normal[...,1]
 strength=.4 if part=='head' else .7
 normal=np.uint8(np.clip((normal.astype(float)-np.array([127.5,127.5,255]))*strength+np.array([127.5,127.5,255]),0,255))
 normal[repair_mask]=[128,128,255]
 normal=normal[tuple(nearest)];Image.fromarray(normal).save(T/f'pman_{part}_normal_1k.png')
 rough=load(raw/'texture_urls_0_roughness.png','L');detail=.12*(rough-np.median(rough[coverage]));rr=np.full((N,N),.88);spec=np.full((N,N),.12);metal=np.zeros((N,N))
 skin=np.isin(piece,[1,4,5]);hair=piece==2;leather=np.isin(piece,[6,7])|((piece==0)&~green);brass=np.isin(piece,[10,11])
 rr[skin]=.76;rr[hair]=.8;rr[leather]=.64;rr[brass]=.36
 spec[hair]=.16;spec[leather]=.3;spec[brass]=.85;metal[brass]=.85
 orm=np.stack([spec,np.clip(rr+detail,.3,.96),metal],axis=-1)[tuple(nearest)];save(orm,T/f'pman_{part}_metal_rough_1k.png')
 sets[part]=(base,mask,coverage);report[part]={'source':str(raw),'region_texels':int(region.sum()),'feedback_repairs':repairs,'normal_correlation':correlation,'normal_green_flipped':correlation<=-.15}
PAL=P.parent/'new_sorpigal_3d_stage1_20261006/pman/source/palettes'
def palette(pid):return np.frombuffer((PAL/f'pal{pid}.act').read_bytes()[:768],np.uint8).reshape(256,3)/255
base=sets['body'][0];weight=sets['body'][1]*sets['body'][2];src=palette(798);tiers={'pman_a':base};fits={}
for tier,pid in [('pman_b',799),('pman_c',800)]:
 dst=palette(pid);changed=np.abs(src-dst).sum(1)>.02
 M,*_=np.linalg.lstsq(np.c_[src[changed],np.ones(changed.sum())],dst[changed],rcond=None)
 tiers[tier]=np.clip(np.c_[base.reshape(-1,3),np.ones(N*N)]@M,0,1).reshape(N,N,3)
 fits[tier]={'palette':pid,'samples':int(changed.sum()),'matrix':M.tolist()}
ramps,fit=R.fit_ramps(base,tiers,weight);cfg={'variants':['pman_a','pman_b','pman_c'],'materials':[]}
for part,name in [('body','Peasant_A'),('head','PeasantHead_A')]:
 cfg['materials'].append({'base':name,'prefix':name[:-2],'mask':f'pman_{part}_region_mask.png','regions':['tunic'],'palettes':{'pman_a':798,'pman_b':799,'pman_c':800},'ramps':{k:[ramps[k]] for k in cfg['variants']}})
(T/'pman_ramps.json').write_text(json.dumps(cfg,indent=2));report['native_palette_fits']=fits;report['ramp_fit']=fit
(T/'composition.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
