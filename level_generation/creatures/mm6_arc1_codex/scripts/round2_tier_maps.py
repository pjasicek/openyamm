"""Bake the exact engine colour ramps for source-versus-selected texture measurements."""
from pathlib import Path
import numpy as np,json,shutil
from PIL import Image
P=Path(__file__).resolve().parents[1];cfg=json.loads((P/'textures/arc1_ramps.json').read_text())
lin=lambda c:np.where(c<=.04045,c/12.92,((c+.055)/1.055)**2.4)
srgb=lambda c:np.where(c<=.0031308,c*12.92,1.055*np.clip(c,0,None)**(1/2.4)-.055)
for label,root in [('high',P/'work/round2/high_textures'),('baked',P/'textures')]:
 for tier in cfg['variants']:
  out=P/f'work/round2/metric_tiers/{label}/{tier}';out.mkdir(parents=True,exist_ok=True)
  for entry,prefix in zip(cfg['materials'],['arc1_','arc1_head_']):
   rgb=lin(np.array(Image.open(root/(prefix+'basecolor_1k.png')).convert('RGB'),float)/255);mask=np.array(Image.open(root/entry['mask']).convert('RGBA'),float)/255
   lum=rgb@np.array([.2126,.7152,.0722]);colour=rgb.copy()
   for c,r in enumerate(entry['ramps'][tier]):
    x=np.clip((lum-r['range'][0])/(r['range'][1]-r['range'][0]),0,1)*15;i=np.minimum(x.astype(int),14);f=(x-i)[...,None];ramp=np.array(r['colors']);colour=colour*(1-mask[...,c:c+1])+(ramp[i]*(1-f)+ramp[i+1]*f)*mask[...,c:c+1]
   Image.fromarray(np.clip(srgb(colour)*255+.5,0,255).astype('uint8')).save(out/(prefix+'basecolor_1k.png'))
  shutil.copytree(root/'bow',out/'bow',dirs_exist_ok=True)
