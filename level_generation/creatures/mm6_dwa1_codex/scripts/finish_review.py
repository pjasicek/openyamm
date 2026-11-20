from pathlib import Path
import json,shutil
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parents[1];rows=json.loads((P/'review/clips/frames.json').read_text());font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',18);small=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',14)
def card(name,view):
 out=Image.new('RGB',(1500,452),(30,33,37));d=ImageDraw.Draw(out);d.text((10,7),f'{name} / {view} / exported GLB',font=font,fill='white')
 for i,r in enumerate(x for x in rows[name]if x['view']==view):
  im=Image.open(P/r['path']).convert('RGB');out.paste(im,(i*300,32));d.text((i*300+8,432),f"{r['seconds']:.3f} s",font=small,fill='white')
 return out
for view in ['front','left','three_quarter']:
 sheet=Image.new('RGB',(1500,452*len(rows)))
 for i,name in enumerate(rows):sheet.paste(card(name,view),(0,i*452))
 sheet.save(P/f'review/clips_{view}.jpg',quality=94)
for name in rows:
 sheet=Image.new('RGB',(1500,452*3))
 for i,view in enumerate(['front','left','three_quarter']):sheet.paste(card(name,view),(0,452*i))
 sheet.save(P/f'review/{name}_sheet.jpg',quality=94)
sheet=Image.new('RGB',(1800,936),(30,33,37));d=ImageDraw.Draw(sheet)
for i,(t,label)in enumerate(zip('abc',['A / Dwarf / palette 195','B / Dwarf Warrior / palette 196','C / Dwarf Lord / palette 197'])):
 sheet.paste(Image.open(P/f'review/tier_{t}_three_quarter.png').convert('RGB'),(i*600,36));d.text((i*600+10,7),label,font=font,fill='white')
sheet.save(P/'review/tiers.jpg',quality=95)
shutil.copy2(P/'work/g4_exported.json',P/'review/g4_exported.json')
print('Sheets written: 3 views, 8 clips, 3 tiers')

lod=Image.new('RGB',(1600,1280),(30,33,37));draw=ImageDraw.Draw(lod)
for row,clip in enumerate(['Standing','Attack']):
 for i in range(4):
  lod.paste(Image.open(P/f'review/lod_{i}_{clip}_three_quarter.png').convert('RGB'),(400*i,640*row+40))
  draw.text((400*i+10,640*row+10),f'LOD{i} / {clip}',font=font,fill='white')
lod.save(P/'review/lod_sheet.jpg',quality=95)
