"""Review contact sheets and measured reduction curves, no source-art alterations."""
from pathlib import Path
import json,math
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parents[1];R=P/'review/round2';font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',20);small=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',16)
roles=['Standing','Walking','Running','Attack','Hit','Death','Dead','Fidget']
for view,name in [('front','front'),('left','side'),('three_quarter','three_quarter')]:
 sheet=Image.new('RGB',(1500,8*460),(28,31,36));draw=ImageDraw.Draw(sheet)
 for row,role in enumerate(roles):
  draw.text((10,row*460+7),role,fill='white',font=font)
  for col in range(5):sheet.paste(Image.open(P/f'review/clips/{role}_{col}_{view}.png').convert('RGB'),(col*300,row*460+35))
 sheet.save(P/f'review/clips_{name}.jpg',quality=91)
for role,time in [('Standing','0'),('Attack','0.71875'),('Death','0.291667')]:
 files=[R/f'hand_{role}{time}_{sd}_{v}.png' for sd in 'RL' for v in 'abcd'];tiles=[Image.open(f).convert('RGB')for f in files];w,h=tiles[0].size;sheet=Image.new('RGB',(w*4,h*2+40),(28,31,36));ImageDraw.Draw(sheet).text((10,8),f'{role} / {time}s - right hand above, left below',font=font,fill='white')
 for i,t in enumerate(tiles):sheet.paste(t,(i%4*w,i//4*h+40))
 sheet.save(R/f'hands_{role}.jpg',quality=92)
for part,old,new in [('body',12815,11100),('sword',2292,1985)]:
 sheet=Image.new('RGB',(8*384,2*420),(40,43,47));draw=ImageDraw.Draw(sheet)
 for row,tag in enumerate([f'{part}_l0_reference',f'{part}_l0_refine2']):
  for i in range(8):
   im=Image.open(R/f'{tag}_{i}.png').convert('RGBA');bg=Image.new('RGBA',im.size,(60,63,68,255));bg.alpha_composite(im);bg=bg.convert('RGB');bg.thumbnail((384,384));sheet.paste(bg,(i*384,row*420+32));draw.text((i*384+6,row*420+6),f'{"Before"if row==0 else "After"} {old if row==0 else new} / {i*45} deg',font=small,fill='white')
 sheet.save(R/f'{part}_before_after.jpg',quality=95)
curves=json.loads((R/'reduction_curve.json').read_text())+json.loads((R/'sword_reduction_curve.json').read_text());selected=json.loads((R/'selection.json').read_text())
chart=Image.new('RGB',(1800,900),'white');draw=ImageDraw.Draw(chart);draw.text((30,15),'KnightPlate reduction: 8-view minimum IoU (blue) and SSIM (orange); circle = selected',font=font,fill='black')
for r,part in enumerate(['body','sword']):
 for lod in range(4):
  rows=sorted([x for x in curves if x['part']==part and x['lod']==lod],key=lambda x:x['triangles']);sel=next(x for x in selected if x['part']==part and x['lod']==lod);left=lod*450+65;top=r*420+100;width=350;height=285
  xmin=min(x['triangles']for x in rows);xmax=max(max(x['triangles']for x in rows),sel['triangles']);ymin=min(.97,min(min(x['min_ssim'],x['min_iou'])for x in rows)-.005)
  xy=lambda x,y:(left+(x-xmin)/max(xmax-xmin,1)*width,top+height*(1-(y-ymin)/(1.001-ymin)))
  draw.text((left,top-34),f'{part.title()} LOD{lod} - selected {sel["triangles"]:,}',font=small,fill='black')
  for y in [.98,.995,1.0]:
   if y<ymin:continue
   a,b=xy(xmin,y),xy(xmax,y);draw.line([a,b],fill='#bcbcbc');draw.text((left-55,a[1]-9),str(y),font=small,fill='#666666')
  draw.line([(left,top),(left,top+height),(left+width,top+height)],fill='black',width=2)
  for key,col in [('min_iou','#3679cf'),('min_ssim','#c27729')]:
   points=[xy(x['triangles'],x[key])for x in rows];draw.line(points,fill=col,width=3)
   for x,y in points:draw.ellipse((x-3,y-3,x+3,y+3),fill=col)
   x,y=xy(sel['triangles'],sel[key]);draw.ellipse((x-7,y-7,x+7,y+7),outline=col,width=3)
  for x in [xmin,xmax]:
   xx,_=xy(x,ymin);draw.text((xx-20,top+height+12),str(x),font=small,fill='black')
  draw.text((left+120,top+height+35),'Triangles',font=small,fill='black')
chart.save(R/'reduction_curve.png')
print('Updated three clip sheets, three hand sheets, eight-view comparisons and reduction plot.')
