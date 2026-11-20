"""Focused straight/diagonal comparison, not the broad terrain gallery."""
import json
from pathlib import Path
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;P=H.parents[1]
g=json.loads((P/'effective_grids.json').read_text())['out01'];im=Image.new('RGB',(1008,1040),'#202933');d=ImageDraw.Draw(im)
for c,v in enumerate(['v9','v10']):
 d.text((c*504+4,3),v,fill='white');folder=P/'roads'/v/'runtime'
 for y,row in enumerate(g[51:57]):
  for x,n in enumerate(row[74:80]):
   f=folder/(n+'.png')
   if not f.exists():f=P/'complete_runtime_x2/worlds/mm8/terrain_x2'/(n+'.png')
   im.paste(Image.open(f).convert('RGB').resize((84,84)),(c*504+x*84,24+y*84))
 for y in range(3):
  for x in range(3):
   n='drsrnw2' if x==2-y else 'drsrnw1' if x==1-y else None
   f=folder/(n+'.png') if n else P/'masters/v1/runtime/dirt.png'
   im.paste(Image.open(f).resize((168,168)),(c*504+x*168,536+y*168))
im.save(H/'connections.png')
