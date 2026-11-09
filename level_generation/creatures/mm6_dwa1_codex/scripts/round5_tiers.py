"""Preview the shared maps with the unchanged engine ramp equation."""
from pathlib import Path
import json,sys,numpy as np
from PIL import Image
P=Path(__file__).resolve().parents[1];W=P/'work/round5';R=json.loads((P/'textures/dwa1_ramps.json').read_text())
lin=lambda c:np.where(c<=.04045,c/12.92,((c+.055)/1.055)**2.4)
srgb=lambda c:np.where(c<=.0031308,c*12.92,1.055*np.maximum(c,0)**(1/2.4)-.055)
def tiers(folder,source=False):
 folder.mkdir(exist_ok=True);maps=np.load(W/'source_maps.npz')if source else None
 for entry in R['materials']:
  name=entry['base'];base=maps[name+'_base']if source else np.asarray(Image.open(folder/f'{name}_base.png').convert('RGB'))/255.;mask=maps[name+'_mask']if source else np.asarray(Image.open(folder/f'{name}_mask.png').convert('RGBA'))/255.
  if source:
   for mode in ['base','orm','normal','mask']:Image.fromarray(np.rint(maps[name+'_'+mode]*255).astype('uint8')).save(folder/f'{name}_{mode}.png')
  for variant in R['variants']:
   rgb=lin(base);lum=rgb@np.array([.2126,.7152,.0722]);out=rgb.copy()
   for ch,reg in enumerate(entry['ramps'][variant]):
    lo,hi=reg['range'];x=np.clip((lum-lo)/(hi-lo),0,1)*15;i=np.minimum(x.astype(int),14);f=(x-i)[...,None];c=np.array(reg['colors']);paint=c[i]*(1-f)+c[i+1]*f;out=out*(1-mask[...,ch:ch+1])+paint*mask[...,ch:ch+1]
   Image.fromarray(np.rint(np.clip(srgb(out),0,1)*255).astype('uint8')).save(folder/f'{name}_{variant}.png')
if __name__=='__main__':
 tiers(W/'source',True)
 for arg in sys.argv[1:]:tiers(W/arg)
