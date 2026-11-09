from pathlib import Path
from PIL import Image,ImageDraw
import json,sys
P=Path(__file__).resolve().parents[1];folder=sys.argv[1] if len(sys.argv)>1 else 'clay';rows=json.loads((P/f'review/{folder}/frames.json').read_text())
for view in ['front','left','three_quarter']:
 canvas=Image.new('RGB',(5*270,len(rows)*290),(42,44,48));d=ImageDraw.Draw(canvas)
 for ri,(name,shots)in enumerate(rows.items()):
  for i,s in enumerate([x for x in shots if x['view']==view]):
   im=Image.open(P/s['path']).convert('RGB');im.thumbnail((270,265));canvas.paste(im,(i*270+(270-im.width)//2,ri*290+22));d.text((i*270+8,ri*290+5),f"{name} {s['seconds']:.2f}s",fill='white')
 canvas.save(P/f'review/{folder}_{view}.jpg',quality=90)
