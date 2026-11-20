"""Native, final palette and mask review for all sampling replacements."""
import json
from pathlib import Path
from PIL import Image, ImageDraw
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent/"mm7_m514"))
from process import apply_variant
P=Path(__file__).resolve().parent
variants=json.loads((P/'variants.json').read_text())['variants']
reg=json.loads((P/'registration.json').read_text())
names=sorted(reg)
for start in range(0,len(names),8):
 selected=names[start:start+8]
 out=Image.new('RGB',(1250,len(selected)*260),(42,42,42));d=ImageDraw.Draw(out)
 for i,name in enumerate(selected):
  base=Image.open(P/f'aligned_2x/{name}.png');mask=Image.open(P/f'masks_2x/{name}.png')
  mi=mask.convert('RGBA');mi.putalpha(base.getchannel('A'))
  images=[Image.open(P/f'native/{name}.png')]+[apply_variant(base,mask,v) for v in variants]+[mi]
  for col,im in enumerate(images):
   im=im.crop(im.getbbox());im.thumbnail((240,230))
   out.paste(im,(col*250+(250-im.width)//2,i*260+25),im)
   d.text((col*250+5,i*260+5),name+' / '+['native','259','260','261','mask'][col],fill='white')
 out.save(P/f'review/repair_variants_masks_{start//8}.png')
