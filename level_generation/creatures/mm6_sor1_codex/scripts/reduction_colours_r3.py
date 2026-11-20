from pathlib import Path
import numpy as np,json
from PIL import Image
p=Path(__file__).resolve().parents[1];r=json.loads((p/'textures/sor1_ramps.json').read_text());entry=r['materials'][0]
lin=lambda c:np.where(c<=.04045,c/12.92,((c+.055)/1.055)**2.4)
srgb=lambda c:np.where(c<=.0031308,c*12.92,1.055*np.clip(c,0,None)**(1/2.4)-.055)
for label in ['reference','candidate']:
 for n in range(4):
  path=p/'textures/sor1_basecolor_1k.png' if label=='reference' else p/f'textures/round3/r3_lod{n}_Sorcerer_basecolor.png';maskpath=p/'textures/sor1_region_mask.png' if label=='reference' else p/f'textures/round3/r3_lod{n}_Sorcerer_mask.png'
  base=lin(np.asarray(Image.open(path).convert('RGB'),float)/255);mask=np.asarray(Image.open(maskpath).convert('RGBA'),float)/255;lum=base@np.array([.2126,.7152,.0722])
  for tier in 'abc':
   out=base.copy()
   for c,reg in enumerate(entry['ramps'][f'sor1_{tier}']):
    lo,hi=reg['range'];cs=np.array(reg['colors']);x=np.clip((lum-lo)/(hi-lo),0,1)*(len(cs)-1);ix=np.minimum(x.astype(int),len(cs)-2);f=(x-ix)[...,None];v=cs[ix]*(1-f)+cs[ix+1]*f;out=out*(1-mask[...,c:c+1])+v*mask[...,c:c+1]
   Image.fromarray(np.uint8(np.clip(srgb(out),0,1)*255+.5)).save(p/'work'/f'reduction_{label}{n}_{tier}.png')
