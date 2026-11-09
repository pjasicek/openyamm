"""Compare all native and restored golem standing palette appearances."""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
sys.path.insert(0,str(HERE.parent/'mm7_m514'))
from process import apply_variant
sources=json.loads((HERE/'sources.json').read_text())
variants=json.loads((HERE/'variants.json').read_text())['variants']
out=Image.new('RGB',(1080,1200),(48,48,48));draw=ImageDraw.Draw(out)
for view in range(5):
 name=f'm254sa{view}'
 indices=np.array(Image.open(REPO/sources['sources'][name]['path']))
 enhanced=Image.open(HERE/f'aligned_2x/{name}.png');mask=Image.open(HERE/f'masks_2x/{name}.png')
 for col,var in enumerate(variants):
  pal=np.frombuffer((REPO/sources['palette_sources'][str(var['palette_id'])]['path']).read_bytes()[:768],np.uint8).reshape(256,3)
  native=Image.fromarray(np.dstack((pal[indices],np.where(indices>0,255,0).astype(np.uint8))))
  for half,im in enumerate([native,apply_variant(enhanced,mask,var)]):
   tile=im.crop(im.getbbox());tile.thumbnail((172,210),Image.Resampling.NEAREST if half==0 else Image.Resampling.LANCZOS)
   x=col*360+half*180+(180-tile.width)//2;y=view*240+25+(210-tile.height)//2;out.paste(tile,(x,y),tile)
  draw.text((col*360+3,view*240+4),f'{name} / {var["palette_id"]}: native | restored',fill='white')
out.save(HERE/'review/palette_identity_comparison.png')
