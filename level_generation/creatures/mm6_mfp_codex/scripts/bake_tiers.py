import sys,json,numpy as np
from PIL import Image
from pathlib import Path
P=Path(__file__).resolve().parents[1];folder=Path(sys.argv[1]);R=json.loads((P/'textures/mfp_ramps.json').read_text());lum=np.array([.2126,.7152,.0722]);lin=lambda x:np.where(x<=.04045,x/12.92,((x+.055)/1.055)**2.4);srgb=lambda x:np.where(x<=.0031308,x*12.92,1.055*np.maximum(x,0)**(1/2.4)-.055)
for stem in ['mfp','mfp_head']:
 base=np.asarray(Image.open(folder/f'{stem}_basecolor.png').convert('RGB'),float)/255;mask=np.asarray(Image.open(folder/f'{stem}_region_mask.png').convert('RGB'),float)[:,:,0]/255;entry=R['materials'][0];light=lin(base)@lum
 for tier in R['variants']:
  ramp=entry['ramps'][tier][0];lo,hi=ramp['range'];colors=np.array(ramp['colors']);u=np.clip((light-lo)/(hi-lo)*15,0,15);i=np.minimum(u.astype(int),14);t=(u-i)[:,:,None];rgb=colors[i]*(1-t)+colors[i+1]*t;out=lin(base)*(1-mask[:,:,None])+rgb*mask[:,:,None];Image.fromarray((np.clip(srgb(out),0,1)*255+.5).astype('uint8')).save(folder/f'{stem}_{tier}.png')
