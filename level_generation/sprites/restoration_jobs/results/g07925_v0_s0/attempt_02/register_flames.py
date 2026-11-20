from pathlib import Path
import json
from PIL import Image
p=Path(__file__).resolve().parent
boxes=[(14,32),(50,68),(80,94),(161,175),(196,213),(226,245)]
for k in json.loads((p/'checks.json').read_text())['frames']:
 f=p/(k+'.png');b=p/(k+'.before_flame_registration.png')
 if not b.exists():b.write_bytes(f.read_bytes())
 a=Image.open(b).convert('RGBA')
 for x0,x1 in boxes:
  patch=a.crop((x0,110,x1,146));w=x1-x0;nw=round(w*.8)
  patch=patch.convert('RGBa').resize((nw,25),Image.Resampling.LANCZOS).convert('RGBA')
  a.paste((0,0,0,0),(x0,110,x1,146));a.paste(patch,(x0+(w-nw)//2,121))
 a.save(f)
(p/'flame_registration.json').write_text(json.dumps({'method':'Common flame-region transform 0.8 horizontal and 25/36 vertical anchored at physical y146; premultiplied Lanczos. No body/candle/chain movement.','boxes':boxes,'source_y':[110,146],'target_y':[121,146]},indent=2)+'\n')
