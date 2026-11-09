from pathlib import Path
import json
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parents[1];R=P/'review/round2';font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',21);small=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',17)
m=json.loads((R/'anatomy_and_feet.json').read_text())['native_comparison']['model']
out=Image.new('RGB',(1500,1080),'#35383d');d=ImageDraw.Draw(out)
for x,label,file,native in [(0,'Native arc1sta0',P.parent/'mm6_arc1/native/arc1sta0.png',True),(420,'Review 2 - Standing',R/'standing_alpha_front.png',False)]:
 im=Image.open(file).convert('RGBA');im=im.crop(im.getbbox());h=810;im=im.resize((round(im.width*h/im.height),h),Image.Resampling.NEAREST if native else Image.Resampling.LANCZOS);out.paste(im,(x+(420-im.width)//2,60),im);d.text((x+25,20),label,font=font,fill='white');d.line((x+25,872,x+395,872),fill='#6cbc90',width=2)
feet=Image.open(R/'soles_left.png').convert('RGB');feet.thumbnail((640,490));out.paste(feet,(850,125));d.text((870,80),'Heel and toe against the floor',font=font,fill='white')
lines=['Native / model, normalized by body height:',f"Foot spacing: 8.98% / {100*m['foot_spacing_per_height']:.2f}%",f"Body width: 25.0% / {100*m['body_width_per_height']:.1f}%",'Upper arms: about 0 deg / 4.3 deg','Forearms: 5.4-8.9 deg / 9.6 deg','','Native landmarks have +/-2 px uncertainty.','Closed grip and matching leather bracers.','','Standing + Fidget, sampled at 48 Hz:','Sole tilt below 0.74 degrees.','Heel/toe contact within 3 mm of floor.']
for i,line in enumerate(lines):d.text((870,630+i*28),line,font=small,fill='white')
for y,line in [(910,'Upright rest; closed left hand on the wrap; vertical bow with the string inward.'),(952,'Relaxed Fidget preserved. Feet aligned with travel; 9 cm walking swing clearance.'),(994,'Cast is the same bow shot as Attack; both release at 1.200 seconds.')]:d.text((25,y),line,font=font,fill='white')
out.save(R/'native_rest_comparison.jpg',quality=95)
D=R/'reduction';S=json.loads((D/'selected.json').read_text())
for part in ['body','bow','arrow']:
 rows=4;out=Image.new('RGB',(1600,rows*530+55),'#303339');d=ImageDraw.Draw(out)
 d.text((20,15),f'{part}: unreduced / selected rebake; eight views in the accompanying PNGs',font=font,fill='white')
 for row,view in enumerate([0,2,4,7]):
  for col,label in enumerate(['high','baked']):
   im=Image.open(D/f'{part}_l0_arc1_a_{label}_{view}.png').convert('RGBA')
   # Identical crop includes the union of source and selected silhouettes.
   other=Image.open(D/f'{part}_l0_arc1_a_{"baked"if label=="high"else"high"}_{view}.png').convert('RGBA')
   a,b=im.getbbox(),other.getbbox();box=(min(a[0],b[0])-10,min(a[1],b[1])-10,max(a[2],b[2])+10,max(a[3],b[3])+10);im=im.crop(box);im.thumbnail((720,480))
   x=col*800+(800-im.width)//2;y=55+row*530;out.paste(im,(x,y),im)
   d.text((col*800+20,y+485),f'View {view}: '+('unreduced'if col==0 else f"{S[part]['0']['triangles']} triangles, rebaked"),font=small,fill='white')
 out.save(D/f'{part}_side_by_side.jpg',quality=94)
print('Review 2 native, sole and reduction sheets written')
