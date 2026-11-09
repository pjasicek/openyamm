from pathlib import Path
import sys,runpy,json,subprocess,shutil,hashlib,collections
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parents[1];R=P/'review/round3';sys.dont_write_bytecode=True
for name in ['round2_smoothness.py','compose_sheets.py','check_viewer.py']:
 code=(P/'scripts'/name).read_text().replace('review/round2/','review/round3/')
 exec(compile(code,str(P/'scripts'/name),'exec'),{'__file__':str(P/'scripts'/name),'__name__':'__main__'})
r=subprocess.run([sys.executable,str(P.parents[2]/'output/codex_batch/check_bindings.py'),str(P/'integration/actors.yml')],capture_output=True,text=True)
(R/'check_bindings.log').write_text(r.stdout+r.stderr);r.check_returncode();assert 'BAD'not in r.stdout+r.stderr;print(r.stdout)
for n in ['check_viewer.log','browser_capture.log']:shutil.copy2(P/'review'/n,R/n)
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',20);small=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',16)
m=json.loads((R/'native_pose.json').read_text())
out=Image.new('RGB',(1440,1250),'#34373c');d=ImageDraw.Draw(out)
for col,(view,nfile)in enumerate([('front','arc1sta0.png'),('left','arc1sta2.png')]):
 for kind in range(2):
  native=kind==0;x=(col*2+kind)*360
  path=P.parent/'mm6_arc1/native'/nfile if native else R/f'standing_alpha_{view}.png'
  im=Image.open(path).convert('RGBA');box=im.getbbox();im=im.crop(box);scale=650/im.height;im=im.resize((round(im.width*scale),650),Image.Resampling.NEAREST if native else Image.Resampling.LANCZOS)
  ox=x+(360-im.width)//2;oy=55;out.paste(im,(ox,oy),im)
  d.text((x+12,15),('Native 'if native else 'R3 ')+view,font=font,fill='white')
  if native:
   pts=m['native']['front_landmarks_px'if view=='front'else'side_landmarks_px']
   pix={k:(ox+(v[0]-box[0])*scale,oy+(v[1]-box[1])*scale)for k,v in pts.items()if k!='bow_tips'}
  else:
   pts=m['round3']['landmarks_m'];labels={'shoulder':'B_L_UpperArm','elbow':'B_L_Forearm','wrist':'B_L_Hand','hip':'B_L_Thigh','grip':'Bow'}
   pix={}
   for k,n in labels.items():
    v=pts[n];xx=340+(v[0]if view=='front'else v[1])*1000/1.85;yy=500+(.85-v[2])*1000/1.85;pix[k]=(ox+(xx-box[0])*scale,oy+(yy-box[1])*scale)
  d.line([pix[k]for k in ['shoulder','elbow','wrist']],fill='#55ddbb',width=3)
  for k,(a,b)in pix.items():
   d.ellipse((a-3,b-3,a+3,b+3),fill='#ffdb68');d.text((a+5,b-8),k,font=small,fill='#ffdb68')
  d.line((x+15,707,x+345,707),fill='#55aa77',width=2)
rows=[('Wrist lateral / height','wrist_lateral_from_hip_per_height',100,'%'),
('Wrist forward / height','wrist_forward_from_hip_per_height',100,'%'),
('Grip lateral / height','grip_lateral_from_hip_per_height',100,'%'),
('Grip forward / height','grip_forward_from_hip_per_height',100,'%'),
('Upper arm: front','upper_front_deg',1,'deg'),('Forearm: front','forearm_front_deg',1,'deg'),
('Upper arm: side','upper_side_deg',1,'deg'),('Forearm: side','forearm_side_deg',1,'deg'),('Bow from vertical','bow_tilt_deg',1,'deg')]
d.text((25,735),'Measurement                         Native       Round 2      Round 3',font=font,fill='white')
for i,(label,key,mult,unit)in enumerate(rows):
 d.text((25,770+i*29),label,font=small,fill='white')
 for j,n in enumerate(['native','round2','round3']):d.text((365+j*140,770+i*29),f'{m[n][key]*mult:.2f} {unit}',font=small,fill='white')
feet=Image.open(R/'soles_left.png').convert('RGB');feet.thumbnail((600,325));out.paste(feet,(820,755))
d.text((825,1090),'Soles preserved; actual 48 Hz contact reports retained.',font=small,fill='white')
for i,line in enumerate(['Native landmarks +/-2 px; estimated hip +/-6 px. Angles are image-plane projections.',
'Native side bow is ~72 deg from vertical; explicit review instruction chooses a vertical carry.',
'The bow follows the closed fist. Shared gate FAIL remains documented; this sheet is not acceptance.']):
 d.text((25,1140+i*28),line,font=small,fill='white')
out.save(R/'native_rest_comparison.jpg',quality=95)
# Current switch-size evidence: identical pixel scale, source left / candidate right.
D=R/'reduction';metrics=json.loads((D/'assembled_distance_metrics.json').read_text())
im=Image.new('RGB',(1600,890),'#303339');draw=ImageDraw.Draw(im)
draw.text((20,12),'Review 3: equipped Standing silhouettes at the actual switch sizes',font=font,fill='white')
for j,lod in enumerate([1,2,3]):
 row=next(r for r in metrics['rows']if r['lod']==lod and r['clip']=='Standing')
 draw.text((20,55+j*270),f'LOD{lod}, pooled IoU {row["pooled_iou"]:.5f} / .97000',font=small,fill='white')
 for i,view in enumerate([0,2,4,6]):
  for k,label in enumerate(['high','candidate']):
   pic=Image.open(D/f'assembled_l{lod}_Standing_{label}_{view}.png').convert('RGBA');pic.thumbnail((180,230))
   im.paste(pic,(i*390+k*185,85+j*270),pic)
im.save(D/'distance_sheet.jpg',quality=95)
# Same cloth intent/config on archived R2 and current runtime; retain every raw failure.
a=json.loads((R/'shared_baseline/gates.json').read_text());b=json.loads((R/'shared_final/gates.json').read_text())
key=lambda r:tuple(str(r[k])for k in ['asset','clip','lod','gate','region'])
old={key(r):r for r in a['gates']};new={key(r):r for r in b['gates']}
comparison={'baseline_status':a['status'],'final_status':b['status'],'baseline_counts':a['counts'],'final_counts':b['counts'],
'new_failures':[r for k,r in new.items()if r['status']=='FAIL'and old.get(k,{}).get('status')!='FAIL'],
'resolved_failures':[r for k,r in old.items()if r['status']=='FAIL'and new.get(k,{}).get('status')=='PASS'],
'failure_categories':dict(collections.Counter(r['gate']for r in b['gates']if r['status']=='FAIL')),
'baseline_failure_categories':dict(collections.Counter(r['gate']for r in a['gates']if r['status']=='FAIL'))}
(R/'shared_comparison.json').write_text(json.dumps(comparison,indent=2))
print('Shared comparison:',comparison['baseline_counts'],comparison['final_counts'],'new',len(comparison['new_failures']),'resolved',len(comparison['resolved_failures']))
