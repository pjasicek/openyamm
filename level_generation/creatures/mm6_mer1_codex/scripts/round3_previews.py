import sys,json,numpy as np
from pathlib import Path
from PIL import Image
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P.parent/'claude_shared'));import region_variants as R
folder=Path(sys.argv[1]);base=np.asarray(Image.open(folder/'0_basecolor.png').convert('RGB'),float)/255;mask=np.asarray(Image.open(folder/'0_region_mask.png').convert('RGB'),float)[...,0]/255;cfg=json.loads((P/'textures/round3/mer1_ramps.json').read_text());lum=R.luminance(base)
for k,ramps in cfg['materials'][0]['ramps'].items():
 r=ramps[0];x=np.clip((lum-r['range'][0])/(r['range'][1]-r['range'][0]),0,1)*15;i=np.minimum(x.astype(int),14);f=x-i;c=np.array(r['colors']);v=c[i]*(1-f[...,None])+c[i+1]*f[...,None];v=R.srgb_to_linear(base)*(1-mask[...,None])+v*mask[...,None];out=np.where(v<=.0031308,12.92*v,1.055*np.maximum(v,0)**(1/2.4)-.055);Image.fromarray(np.uint8(np.clip(out*255+.5,0,255))).save(folder/f'{k}_preview.png')
