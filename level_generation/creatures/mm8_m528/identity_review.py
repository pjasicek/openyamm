from pathlib import Path
from PIL import Image,ImageDraw
import json
from process import queue,ROOT,spill
n='m528wa0';im=Image.open(ROOT/f'aligned_2x/{n}.png').convert('RGBA');native=queue.native(ROOT,n).resize((256,256),Image.Resampling.NEAREST)
sheet=Image.new('RGB',(1024,600),(35,35,35));d=ImageDraw.Draw(sheet)
for row,color in enumerate([(20,20,20),(240,240,240)]):
 for col,pic in enumerate([native,im]):
  b=Image.new('RGBA',pic.size,(*color,255));b.alpha_composite(pic);sheet.paste(b.convert('RGB'),(col*256,row*300+30));d.text((col*256+4,row*300+5),'Native' if col==0 else 'Restored',fill='white')
 x,y=spill(im)['position'];box=(max(0,x-20),max(0,y-20),min(im.width,x+21),min(im.height,y+21));crop=im.crop(box);b=Image.new('RGBA',crop.size,(*color,255));b.alpha_composite(crop);b=b.resize((246,246),Image.Resampling.NEAREST);sheet.paste(b.convert('RGB'),(520,row*300+30));d.text((524,row*300+5),'Worst magenta contour',fill='white')
 crop=im.crop((80,70,160,110));b=Image.new('RGBA',crop.size,(*color,255));b.alpha_composite(crop);sheet.paste(b.resize((240,120)).convert('RGB'),(780,row*300+30))
sheet.save(ROOT/'review/identity_edges.png')
print(json.dumps(spill(im)))
