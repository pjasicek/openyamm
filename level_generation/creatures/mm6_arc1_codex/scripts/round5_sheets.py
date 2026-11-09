"""Compose the native comparison with actual measured landmarks and current rendered sheets."""
from pathlib import Path
import json,runpy
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parents[1];R=P/'review/round5'
runpy.run_path(str(P/'scripts/compose_sheets.py'),run_name='__main__')
m=json.loads((R/'native_pose.json').read_text())
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',20);small=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',16)
out=Image.new('RGB',(1760,1290),'#34373c');d=ImageDraw.Draw(out)
for col,(view,nfile)in enumerate([('front','arc1sta0.png'),('left','arc1sta2.png')]):
 for kind in range(2):
  native=kind==0;x=(col*2+kind)*440
  path=P.parent/'mm6_arc1/native'/nfile if native else R/f'standing_alpha_{view}.png'
  im=Image.open(path).convert('RGBA');box=im.getbbox();im=im.crop(box);scale=650/im.height;im=im.resize((round(im.width*scale),650),Image.Resampling.NEAREST if native else Image.Resampling.LANCZOS)
  ox=x+(440-im.width)//2;oy=55;out.paste(im,(ox,oy),im)
  d.text((x+12,15),('Native 'if native else 'Round 5 ')+(view if view=='front'else('side (faces right)'if native else'side (faces left)')),font=font,fill='white')
  if native:
   pts=m['native']['front_landmarks_px'if view=='front'else'side_landmarks_px'];pix={k:(ox+(v[0]-box[0])*scale,oy+(v[1]-box[1])*scale)for k,v in pts.items()if k!='bow_tips'}
  else:
   pts=m['round5']['landmarks_m'];pix={}
   for k,n in {'shoulder':'B_L_UpperArm','elbow':'B_L_Forearm','wrist':'B_L_Hand','hip':'B_L_Thigh','grip':'Bow'}.items():
    v=pts[n];xx=340+(v[0]if view=='front'else v[1])*1000/1.85;yy=500+(.85-v[2])*1000/1.85;pix[k]=(ox+(xx-box[0])*scale,oy+(yy-box[1])*scale)
  d.line([pix[k]for k in ['shoulder','elbow','wrist']],fill='#55ddbb',width=3)
  for k,(a,b)in pix.items():
   d.ellipse((a-3,b-3,a+3,b+3),fill='#ffdb68');d.text((a+5,b-8),k,font=small,fill='#ffdb68')
rows=[('Wrist lateral / height','wrist_lateral_from_hip_per_height',100,'%'),('Wrist forward / height','wrist_forward_from_hip_per_height',100,'%'),('Grip lateral / height','grip_lateral_from_hip_per_height',100,'%'),('Grip forward / height','grip_forward_from_hip_per_height',100,'%'),('Upper arm: front','upper_front_deg',1,'deg'),('Forearm: front','forearm_front_deg',1,'deg'),('Upper arm: side (+ forward)','upper_side_deg',1,'deg'),('Forearm: side (+ forward)','forearm_side_deg',1,'deg'),('Elbow bend: side','elbow_bend_side_deg',1,'deg'),('Bow from vertical','bow_tilt_deg',1,'deg'),('Bow azimuth from forward','bow_azimuth_deg',1,'deg'),('Front tip pitch (+ upward)','front_tip_elevation_deg',1,'deg')]
d.text((25,730),'Measurement                               Native        Round 5',font=font,fill='white')
for i,(label,key,mult,unit)in enumerate(rows):
 d.text((25,765+i*29),label,font=small,fill='white')
 for j,n in enumerate(['native','round5']):d.text((420+j*160,765+i*29),f'{m[n][key]*mult:.2f} {unit}',font=small,fill='white')
feet=Image.open(R/'attack_soles_left.png').convert('RGB');feet.thumbnail((650,350));out.paste(feet,(900,735));d.text((910,1090),'Attack/Cast: both soles planted (release)',font=small,fill='white')
for i,line in enumerate(['R5 follows the native side bitmap: forward tip rises +18 degrees; string above the limbs.',
'Front-projection wrist mirror error: %.2f mm; native side bend retained.'%(m['round5']['mirrored_right_wrist_front_error_m']*1000),
'Native visible landmarks +/-2 px, inferred hip +/-6 px at 256 px height. Native azimuth is an estimate.',
'Shared gate failures remain documented; this sheet records the pose correction, not technical acceptance.']):
 d.text((25,1140+i*31),line,font=small,fill='white')
out.save(R/'native_rest_comparison.jpg',quality=95)
(R/'native_measurements.md').write_text('| Measurement | Native | Round 5 | Unit |\n|---|---:|---:|---|\n'+'\n'.join(f'| {label} | {m["native"][key]*mult:.3f} | {m["round5"][key]*mult:.3f} | {unit} |'for label,key,mult,unit in rows)+'\n\n'+m['decision']+'\n')
print('Round 5 sheets and native table complete.')

D=R/'reduction';metrics=json.loads((D/'assembled_distance_metrics.json').read_text())
canvas=Image.new('RGB',(1600,930),'#303339');draw=ImageDraw.Draw(canvas)
draw.text((20,12),'Round 5: unchanged LOD geometry, current equipped Standing pose',font=font,fill='white')
draw.text((20,40),'Resized previews; numeric IoU measured across 8 views at 550 / 220 / 88 actor pixels.',font=small,fill='white')
for j,level in enumerate([1,2,3]):
 row=next(r for r in metrics['rows']if r['lod']==level and r['clip']=='Standing')
 draw.text((20,75+j*270),f'LOD{level}: IoU {row["pooled_iou"]:.5f} / .97000; high left, selected right',font=small,fill='#77dd99'if row['pass']else'#ff9977')
 for i,view in enumerate([0,2,4,6]):
  for k,label in enumerate(['high','candidate']):
   pic=Image.open(D/f'assembled_l{level}_Standing_{label}_{view}.png').convert('RGBA');pic.thumbnail((180,225));canvas.paste(pic,(i*390+k*185,104+j*270),pic)
canvas.save(D/'distance_sheet.jpg',quality=95)
