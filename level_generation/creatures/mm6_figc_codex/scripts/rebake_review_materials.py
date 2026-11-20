"""Bake the exact existing region-ramp equation into review textures for a trial."""
import sys,json
from pathlib import Path
import numpy as np
from PIL import Image
P=Path(__file__).resolve().parents[1];T=Path(sys.argv[1]);R=json.loads((T/'figc_ramps.json').read_text());lin=lambda c:np.where(c<=.04045,c/12.92,((c+.055)/1.055)**2.4);srgb=lambda c:np.where(c<=.0031308,c*12.92,1.055*np.maximum(c,0)**(1/2.4)-.055)
for m in R['materials']:
 s='_head' if 'Head' in m['base'] else '_gear' if 'Gear' in m['base'] else '';size='2k' if s=='_gear' else '1k';im=Image.open(T/f'figc{s}_basecolor_{size}.png').convert('RGB');base=lin(np.asarray(im,dtype=float)/255);mask=np.asarray(Image.open(T/m['mask']).convert('RGB').resize(im.size),dtype=float)/255;lum=base@np.array([.2126,.7152,.0722])
 for variant in R['variants']:
  out=base.copy()
  for c,reg in enumerate(m['ramps'][variant]):
   lo,hi=reg['range'];x=np.clip((lum-lo)/(hi-lo),0,1)*15;i=np.minimum(x.astype(int),14);f=(x-i)[...,None];colors=np.array(reg['colors']);mapped=colors[i]*(1-f)+colors[i+1]*f;out=out*(1-mask[...,c:c+1])+mapped*mask[...,c:c+1]
  Image.fromarray(np.clip(srgb(out)*255+.5,0,255).astype('uint8')).save(T/f"tier_{variant}_{m['base']}.png")
