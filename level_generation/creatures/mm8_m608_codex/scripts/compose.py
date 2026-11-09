"""Shared stone textures and padded native belt palettes; no per-tier texture duplication."""
import sys,json
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
P=Path(__file__).resolve().parents[1];T=P/'textures'
sys.path[:0]=[str(P.parent/'mm6_gob_claude/scripts'),str(P.parent/'claude_shared'),str(P.parents[2]/'tools')]
import compose_textures_v2 as C
import region_variants as R
from normal_map_convention import measure
C.SIZE=1024
def load(path,mode='RGB'):
 return np.array(Image.open(path).convert(mode).resize((1024,1024),Image.Resampling.LANCZOS),dtype=float)/255
results={};body_median=None;ramps={}
for part in ['body','head']:
 data=np.load(P/f'work/{part}_uv3d.npz');labels,xyz=C.rasterise(data,tol=0);inside=labels>=0;core=ndimage.binary_erosion(inside,iterations=1)
 _,nearest=ndimage.distance_transform_edt(~core,return_indices=True)
 def pad(a):return a[tuple(nearest)]
 source=P/('meshy/head_texture_v2' if part=='head' else 'meshy/body_texture_v1');base=load(source/'texture_urls_0_base_color.png');ao=load(T/f'{part}_ao.png','L')
 band=labels==1 if part=='body' else np.zeros_like(inside)
 stone=inside&~band;lum=base@np.array([.2126,.7152,.0722]);grey=lum[...,None]*np.array([.96,.985,1.035])
 base[stone]=grey[stone];gain=1
 median=float(np.median(lum[stone]))
 if part=='body':body_median=median
 else:gain=body_median/median;base[stone]*=gain
 base*= (.72+.28*ao)[...,None];base=np.clip(pad(base),0,1)
 normal=np.round(load(source/'texture_urls_0_normal.png')*255).astype('uint8');corr=measure(normal)
 if corr<-.15:normal[:,:,1]=255-normal[:,:,1]
 normal=pad(normal)
 weight=ndimage.gaussian_filter(pad(band.astype(float)),.6)
 mask=np.zeros((1024,1024,4),dtype='uint8');mask[:,:,0]=np.round(weight*255)
 Image.fromarray(mask).save(T/f'{part}_region_mask.png')
 metal=pad(np.where(band,.62,0));rough=pad(np.where(band,.44,.86));specular=pad(np.where(band,.80,.12))
 orm=np.stack([specular,rough,metal],axis=-1)
 for name,a in [('basecolor',base),('normal',normal/255),('orm',orm)]:Image.fromarray(np.round(np.clip(a,0,1)*255).astype('uint8')).save(T/f'{part}_{name}.png')
 classes=np.where(inside,np.where(band,9,11),0).astype('uint8');Image.fromarray(classes).save(T/f'{part}_material_classes.png')
 if part=='body':
  pals=[np.frombuffer((P.parents[2]/f'assets_dev/worlds/mm8/textures/Pal{pid}.act').read_bytes()[:768],dtype='uint8').reshape(256,3)/255 for pid in [609,610,611]]
  changed=np.max(np.abs(pals[0]-pals[1]),axis=1)>.02;assert 10<changed.sum()<200
  lum_linear=R.luminance(base);low,high=np.percentile(lum_linear[band],[2,98]);assert high-low>.01
  for tier,palette in zip('abc',pals):
   colors=np.clip(palette[changed]*1.35,0,1);luma=R.luminance(colors);order=np.argsort(luma);colors=colors[order];luma=luma[order]
   query=np.linspace(luma.min(),luma.max(),16);ramp=np.stack([np.interp(query,luma,colors[:,c]) for c in range(3)],axis=-1)
   ramps[f'm608_{tier}']=[{'range':[float(low),float(high)],'colors':R.srgb_to_linear(ramp).tolist()}]
 results[part]={'normal_integrability':float(corr),'stone_input_luminance_median':median,'head_gain':gain,'inside_texels':int(inside.sum()),'band_texels':int(band.sum()),'size':[1024,1024]}
config={'variants':['m608_a','m608_b','m608_c'],'materials':[{'base':'Juggernaut'+part.title(),'prefix':'Juggernaut'+part.title(),'mask':part+'_region_mask.png','ramps':ramps} for part in ['body','head']]}
(T/'juggernaut_ramps.json').write_text(json.dumps(config,indent=2))
(T/'material_contract.json').write_text(json.dumps({'sets':results,'palettes':[609,610,611],'class_11':'grey stone','belt_class':9,'eye_material':'small separate unlit pale-yellow eyes','roughness':{'stone':.86,'band':.44},'metallic':{'stone':0,'band':.62},'specular_mask':{'stone':.12,'band':.80},'body_alpha':'OPAQUE','flash_alpha':'BLEND'},indent=2))
print('COMPOSED',results,flush=True)
