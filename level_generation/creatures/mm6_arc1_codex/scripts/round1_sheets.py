from pathlib import Path
import json
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parents[1];R=P/'review/round1';font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',21);small=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',17)
out=Image.new('RGB',(1500,1060),'#35383d');d=ImageDraw.Draw(out)
for x,label,file,native in [(0,'Native arc1sta0',P.parent/'mm6_arc1/native/arc1sta0.png',True),(420,'Review 1 - Standing',R/'standing_alpha_front.png',False)]:
 im=Image.open(file).convert('RGBA');im=im.crop(im.getbbox());h=810;im=im.resize((round(im.width*h/im.height),h),Image.Resampling.NEAREST if native else Image.Resampling.LANCZOS);out.paste(im,(x+(420-im.width)//2,60),im);d.text((x+25,20),label,font=font,fill='white');d.line((x+25,872,x+395,872),fill='#6cbc90',width=2)
feet=Image.open(R/'soles_left.png').convert('RGB');feet.thumbnail((640,490));out.paste(feet,(850,125));d.text((870,80),'Heel and toe against the floor',font=font,fill='white')
text=['Native / model, normalized by body height:','Foot spacing: 8.98% / 8.95%','Body width: 25.0% / 27.6%','Upper arms: about 0 deg / 4.3 deg','Forearms: 5.4-8.9 deg / 9.6 deg','','Hands clear the fitted hips by a small gap.','Native landmarks have +/-2 px uncertainty.','','Standing + Fidget, sampled at 48 Hz:','Sole tilt below 0.73 degrees.','Heel/toe contact 1.7-2.8 mm above floor.']
for i,line in enumerate(text):d.text((870,630+i*28),line,font=small,fill='white')
d.text((25,910),'Upright body; arms beside the thighs; loose side carry; string faces inward.',font=font,fill='white');d.text((25,952),'Fidget: gentle weight shift and glance, returning to this same rest pose.',font=font,fill='white');d.text((25,994),'Review 1 - unchanged mesh, textures, triangle budgets and gameplay release times.',font=small,fill='white');out.save(R/'native_rest_comparison.jpg',quality=95)
