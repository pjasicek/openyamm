"""Apply the engine's region ramps to source/rebaked colour maps for honest tier comparisons."""
import sys,json,numpy as np
from pathlib import Path
from PIL import Image
P=Path(__file__).resolve().parents[1];config=json.loads((P/'textures/lzd_ramps.json').read_text())
lin=lambda c:np.where(c<=.04045,c/12.92,((c+.055)/1.055)**2.4)
srgb=lambda c:np.where(c<=.0031308,c*12.92,1.055*np.clip(c,0,None)**(1/2.4)-.055)
def bake(tag):
 metadata=json.loads((P/f'review/rebake/{tag}_bake.json').read_text())if tag!='reference'else {g:{'base_material':m,'paths':{'basecolor':'textures/'+path,'regions':'textures/'+next(e['mask']for e in config['materials']if e['base']==m)}}for g,m,path in [('body','Lizard_A','body_basecolor_1k.png'),('head','LizardHead_A','head_basecolor_1k.png'),('bow','LizardBow_A','bow/basecolor_1k.png')]}
 out=P/'textures/rebake/tiers';out.mkdir(exist_ok=True)
 for group,item in metadata.items():
  im=Image.open(P/item['paths']['basecolor']).convert('RGB');base=lin(np.asarray(im,np.float32)/255);mask=np.stack([np.asarray(c.resize(im.size,Image.Resampling.BILINEAR),np.float32)/255 for c in Image.open(P/item['paths']['regions']).convert('RGBA').split()],-1);entry=next(e for e in config['materials']if e['base']==item['base_material']);lum=base@np.array([.2126,.7152,.0722])
  for variant in config['variants']:
   color=base.copy()
   for c,reg in enumerate(entry['ramps'][variant]):
    low,high=reg['range'];t=np.clip((lum-low)/(high-low),0,1)*15;idx=np.minimum(t.astype(int),14);f=(t-idx)[...,None];ramp=np.asarray(reg['colors'],float);mapped=ramp[idx]*(1-f)+ramp[idx+1]*f;color=color*(1-mask[...,c,None])+mapped*mask[...,c,None]
   Image.fromarray(np.clip(srgb(color)*255+.5,0,255).astype('uint8')).save(out/f'{tag}_{variant}_{group}.png')
if __name__=='__main__':
 for tag in sys.argv[1:]:bake(tag)
