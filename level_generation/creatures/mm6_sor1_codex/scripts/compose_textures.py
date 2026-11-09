"""Preserve Meshy surface detail; derive one robe region and native 819/820/821 palette ramps."""
from pathlib import Path
import sys,json,numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt,gaussian_filter
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p.parent/'claude_shared'));import region_variants as R
T=p/'textures';T.mkdir(exist_ok=True)
def png(a,path):Image.fromarray(np.clip(a*255+.5,0,255).astype('uint8')).save(path)
def pad(a,covered):
 ix=distance_transform_edt(~covered,return_distances=False,return_indices=True)
 return a[tuple(ix)]
for part,job,uv in [('', 'body_retexture_v1','UVMap'),('head_','head_retexture_v2','HeadUV')]:
 ras=np.load(p/'work'/f'uvraster_{uv}.npz');piece=ras['piece'];covered=piece>=0
 base=R.load_srgb(p/'meshy'/job/'texture_urls_0_base_color.png',1024)
 normal=R.load_srgb(p/'meshy'/job/'texture_urls_0_normal.png',1024)
 rough=R.load_srgb(p/'meshy'/job/'texture_urls_0_roughness.png',1024)[...,0]
 # Preserve delivered paint and detail normals, extending island edges into unused texels.
 base=pad(base,covered);normal=pad(normal,covered)
 gold=(base[...,0]>base[...,2]*1.3)&(base[...,1]>base[...,2]*1.2)&(base[...,1]>.19)
 red=(base[...,0]>base[...,1]*1.5)&(base[...,0]>base[...,2]*1.3)
 rough=.8+.1*(rough-.5)
 rough[gold]=.5;rough[np.isin(piece,[3,4])]=.8
 if part:rough=np.where(piece==5,.86,.8)
 mr=np.stack([np.zeros_like(rough),rough,np.zeros_like(rough)],-1)
 png(base,T/f'sor1_{part}basecolor_1k.png');png(normal,T/f'sor1_{part}normal_1k.png');png(pad(mr,covered),T/f'sor1_{part}metal_rough_1k.png')
 if not part:
  cloth=np.isin(piece,[1,100])&~gold&~red
  mask=gaussian_filter(pad(cloth.astype(float),covered),.6)
  R.write_mask([mask],T/'sor1_region_mask.png')
  lum=R.luminance(base);lo,hi=np.percentile(lum[cloth],[1,99]);bodyrange=[round(float(lo),6),round(float(hi),6)]
arrays=[]
for palette in [819,820,821]:
 arrays.append(np.concatenate([np.asarray(Image.open(p.parent/'mm6_sor1'/'native_variants'/f'sor1sta{i}_{palette}.png').convert('RGBA'),float).reshape(-1,4)/255 for i in range(5)]))
changed=(np.max(np.abs(arrays[0][:,:3]-arrays[2][:,:3]),axis=1)>8/255)&(arrays[0][:,3]>.5)
assert changed.sum()>500
L=[R.srgb_to_linear(a[changed,:3]) for a in arrays];lum=L[2]@R.LUMA
# Palette entries correspond pixel-for-pixel, retaining the native shadow/highlight progression.
q=np.linspace(0,1,17);edges=np.quantile(lum,q);ramps={}
for k,tier in enumerate(['sor1_a','sor1_b','sor1_c']):
 colors=[]
 for j in range(16):
  m=(lum>=edges[j])&(lum<=edges[j+1]);colors.append(np.median(L[k][m],axis=0))
 ramps[tier]=[{'range':bodyrange,'colors':np.round(colors,6).tolist()}]
config={'variants':list(ramps),'materials':[{'base':'Sorcerer_A','prefix':'Sorcerer','mask':'sor1_region_mask.png','ramps':ramps}]}
(T/'sor1_ramps.json').write_text(json.dumps(config,indent=2))
# Original small rigid staff: wood, gold, gem swatches retain the authored material colours.
base=np.zeros((64,96,3));mr=np.zeros_like(base);norm=np.full_like(base,[.5,.5,1])
for i,(color,rough,spec) in enumerate([([.20,.095,.035],.8,.1),([.68,.43,.10],.4,1),([.65,.025,.015],.23,.6)]):
 base[:,i*32:(i+1)*32]=color;mr[:,i*32:(i+1)*32]=[spec,rough,0]
png(base,T/'sor1_staff_basecolor.png');png(mr,T/'sor1_staff_metal_rough.png');png(norm,T/'sor1_staff_normal.png')
(T/'composition.json').write_text(json.dumps({'native_changed_pixels':int(changed.sum()),'body_region_luminance_range':bodyrange,'body_head_size':1024,'specular':'body/head matte per creature texture playbook; staff per-texel mask','head_source':'head_retexture_v2'},indent=2))
print('TEXTURES',int(changed.sum()),bodyrange)
