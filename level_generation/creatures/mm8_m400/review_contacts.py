from pathlib import Path
import json
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parent
reg=json.loads((ROOT/'registration.json').read_text())
batches=json.loads((ROOT/'batches.json').read_text())
for key,b in batches.items():
 names=b['frames']; out=Image.new('RGB',(240*len(names),1000),(42,42,42));d=ImageDraw.Draw(out)
 for i,n in enumerate(names):
  if n not in reg:continue
  im=Image.open(ROOT/f'aligned_2x/{n}.png').convert('RGBA')
  w=np.asarray(Image.open(ROOT/f'masks_2x/{n}.png'))[:,:,:2].astype(float)/255*.7
  over=np.array(im);over[:,:,:3]=np.round(over[:,:,:3]*(1-w.sum(axis=2,keepdims=True))+w[:,:,0,None]*[255,80,0]+w[:,:,1,None]*[80,80,255]).clip(0,255).astype(np.uint8)
  pics=[Image.open(ROOT/f'previews/{n}_{pal}.png').convert('RGBA') for pal in (401,402,403)]+[Image.fromarray(over)]
  for j,pic in enumerate(pics):
   bg=Image.new('RGBA',pic.size,(42,42,42,255));bg.alpha_composite(pic);bg.thumbnail((230,225),Image.Resampling.LANCZOS)
   out.paste(bg.convert('RGB'),(i*240+(240-bg.width)//2,j*250+25));d.text((i*240+4,j*250+4),n+' '+str([401,402,403,'mask'][j]),fill='white')
 out.save(ROOT/f'review/{key}_final_variants.png')
print('Final atlas-aligned variant/mask contacts:',len(batches))
