"""Bake the engine's two native ramps for PBR review; runtime keeps shared maps."""
import sys,json,numpy as np
from pathlib import Path
from PIL import Image
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P.parent/'claude_shared'));import region_variants as R
folder=Path(sys.argv[1]);cfg=json.loads((P/'textures/natm_ramps.json').read_text())
for tag in ['body','head','spear','buckler']:
 if folder==P/'textures':basepath=folder/f'natm_{tag}_basecolor.png';maskpath=folder/f'natm_{tag}_region_mask.png';dest=folder
 else:dest=folder/('body'if tag=='head'else tag);i=1 if tag=='head'else 0;basepath=dest/f'{i}_basecolor.png';maskpath=dest/f'{i}_region_mask.png'
 base=np.asarray(Image.open(basepath).convert('RGB'),float)/255;mask=np.asarray(Image.open(maskpath).convert('RGB'),float)/255;linear=R.srgb_to_linear(base);lum=linear@R.LUMA;entry=cfg['materials'][['body','head','spear','buckler'].index(tag)]
 for tier,ramps in entry['ramps'].items():
  out=linear.copy()
  for channel,reg in enumerate(ramps):
   x=np.clip((lum-reg['range'][0])/(reg['range'][1]-reg['range'][0]),0,1)*15;i=np.minimum(x.astype(int),14);f=x-i;c=np.array(reg['colors']);v=c[i]*(1-f[...,None])+c[i+1]*f[...,None];a=mask[...,channel,None];out=out*(1-a)+v*a
  srgb=np.where(out<=.0031308,12.92*out,1.055*np.maximum(out,0)**(1/2.4)-.055);preview=Image.fromarray(np.uint8(np.clip(srgb*255+.5,0,255)))
  source=Image.open(basepath)
  if 'A'in source.getbands():preview=preview.convert('RGBA');preview.putalpha(source.getchannel('A'))
  preview.save(dest/f'{tier}_{tag}_preview.png')
