# Final reports consume existing comparison and shared-gate tools.
import json,sys,hashlib,shutil,subprocess,collections,datetime
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parents[1];R=P.parents[2];O=P/'review/round3'
sys.path.insert(0,str(P/'scripts'));from reduction_metrics import compare
now=datetime.datetime.now(datetime.timezone.utc).isoformat()
def read(p):return json.loads((P/p).read_text())
def dump(p,d):(P/p).write_text(json.dumps(d,indent=2)+'\n')
def artifact(p,role=None):
 f=P/p;d={'path':p,'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'bytes':f.stat().st_size}
 if role:d['role']=role
 return d
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',18)
def tile(p,size):
 im=Image.open(p).convert('RGBA');box=im.getbbox();im=im.crop(box)if box else im
 im.thumbnail((size[0]-16,size[1]-16),Image.Resampling.LANCZOS)
 bg=Image.new('RGBA',size,(58,62,66,255));bg.alpha_composite(im,((size[0]-im.width)//2,(size[1]-im.height)//2))
 return bg.convert('RGB')
def sheet(name,title,rows,size):
 w,h=size;im=Image.new('RGB',(max(map(len,rows))*w,len(rows)*(h+30)+45),(35,38,41))
 d=ImageDraw.Draw(im);d.text((10,10),title,font=font,fill='white')
 for row,items in enumerate(rows):
  for col,(p,label)in enumerate(items):
   x,y=col*w,45+row*(h+30);im.paste(tile(p,(w,h)),(x,y));d.text((x+8,y+h+3),label,font=font,fill='white')
 im.save(O/name,quality=93)
frames=read('review/round3/final_frames/frames.json')
for role,views in frames.items():
 sheet(f'clip_{role}.jpg',f'Review 3 — {role} — actual export — QA HOLD',[[ (p,v+' / '+label)for p,label in items]for v,items in views.items()],(360,480))
 shutil.copyfile(O/f'clip_{role}.jpg',P/f'review/clip_{role}.jpg')
sheet('body_turnaround.jpg','Review 3 body — final export — QA HOLD',[[ (O/f'body_final_{v}.png',v)for v in ['front','left','back','right']] ],(400,570))
sheet('shoulder_closeups.jpg','Refitted continuous shoulders — export evidence, not acceptance',[[ (O/f'shoulders_{r}_{v}.png',r+' / '+v)for v in ['front','left','back','right']]for r in ['Standing','Attack','Death']],(400,400))
sheet('hands_closeups.jpg','Clean hand maps — Attack grip still has shared-gate faults',[[ (O/f'hand_export_{s}_{v}.png',s+' / '+v)for s in 'LR'for v in ['front','outer']]],(350,350))
sheet('face_before_after.jpg','Review 3 — face: round 2 above / protected geometry and new 1K maps below',[[ (O/f'{stage}_face_{v}.png',stage+' / '+v)for v in ['front','left','three_quarter']]for stage in ['before','after']],(450,450))
sheet('hand_before_after.jpg','Review 3 — hands: round 2 above / dense geometry and new 512px maps below',[[ (O/f'{stage}_hand_{v}.png',stage+' / '+v)for v in ['palm','back']]for stage in ['before','after']],(450,450))
selection=read('review/reduction/selection.json');curves=[]
for level,entry in enumerate(selection['body']):
 f=O/f'reduction/lod{level}'
 rows={name:compare(f/'reference'/name,f/'reduced'/name)for name in [f'{t}_Standing_{i}.png'for t in 'abc'for i in range(8)]}
 union=[(v['reference_pixels']+v['candidate_pixels'])/(1+v['iou'])for v in rows.values()]
 pooled=sum(u*v['iou']for u,v in zip(union,rows.values()))/sum(union)
 row={'level':level,'triangles':entry['triangles'],'target_height_px':[700,550,220,88][level],'views':rows,'min_iou':min(v['iou']for v in rows.values()),'pooled_iou':pooled,'min_ssim':min(v['ssim']for v in rows.values())}
 row['numeric_visual_pass']=(row['min_iou']>=.99 and row['min_ssim']>=.95)if level==0 else pooled>=.97;curves.append(row)
 sheet(f'reduction/body_lod{level}_comparison.jpg',f'LOD{level} — unreduced / {entry["triangles"]} triangles — eight green-tier views',[[ (f/base/f'a_Standing_{i}.png',base+f' / view {i}')for i in range(8)]for base in ['reference','reduced']],(260,300))
dump('review/round3/reduction_curve.json',{'source_triangles':15945,'scope':'Fixed reduction/rebake candidate: 8 views x 3 actual palettes per level. Far views use switch sizes. Not an accepted all-gates-passing reduction curve.','body':curves})
lines=['# Round 3 reduction evidence','','| LOD | Body triangles | Actor px | Min IoU | Pooled IoU | Min SSIM | Numeric visual threshold |','|---|---:|---:|---:|---:|---:|---|']
for d in curves:lines.append(f'| {d["level"]} | {d["triangles"]} | {d["target_height_px"]} | {d["min_iou"]:.6f} | {d["pooled_iou"]:.6f} | {d["min_ssim"]:.6f} | {"PASS"if d["numeric_visual_pass"]else"FAIL"} |')
lines+=['','Near: minimum IoU 0.99 and textured SSIM 0.95. Far: pooled IoU 0.97.','All levels also require shared deformation/contact gates, which FAIL.','Numerical results are retained without a blanket perceptual exception.','One 6998-triangle clothing rebake is shared by all levels. LOD0 keeps 4946 head and 3010 hand triangles outside the clothing bake.','[Detailed measurements](../reduction_curve.json); comparison sheets are in this directory.']
(O/'reduction/README.md').write_text('\n'.join(lines)+'\n')
chart=Image.new('RGB',(1100,500),'white');draw=ImageDraw.Draw(chart)
draw.text((45,20),'Fixed candidate chain — view size differs by LOD — not accepted',font=font,fill='black')
for col,key in enumerate(['min_iou','min_ssim']):
 x0=65+col*530;y0=80;draw.rectangle((x0,y0,x0+450,y0+320),outline='black');draw.text((x0,y0-28),key,font=font,fill='black');pts=[]
 for row in sorted(curves,key=lambda x:x['triangles']):
  x=x0+450*row['triangles']/15945;y=y0+320*(1-row[key])/.4;pts.append((x,y));draw.ellipse((x-4,y-4,x+4,y+4),fill='#205e91');draw.text((x+6,y),str(row['level']),font=font,fill='black')
 draw.line(pts,fill='#205e91',width=2);draw.text((x0,y0+340),'Body triangles: 0                         15945',font=font,fill='black')
chart.save(O/'reduction/curve.png')
texture=read('textures/round3/skin_report.json');skin={}
for mi,name,key in [(1,'face','head'),(2,'hands','hands')]:
 mask=np.asarray(Image.open(P/f'textures/round3/{key}_skin_mask.png').convert('L'))>127
 rgb=np.asarray(Image.open(P/f'work/round3/shared_textures/{mi}_basecolor.png').convert('RGB'),float)/255
 lin=np.where(rgb<=.04045,rgb/12.92,((rgb+.055)/1.055)**2.4);lum=lin[mask]@np.array([.2126,.7152,.0722])
 stats={'mean':float(lum.mean()),'p90':float(np.percentile(lum,90)),'p95':float(np.percentile(lum,95))};native=texture[key]['native'];skin[name]={'pixels':int(mask.sum()),'native':native,'baked':stats,'not_darker':all(stats[k]>=native[k]for k in stats)}
dump('review/round3/final_skin_luminance.json',{'scope':'Covered skin texels only, excluding padding; separate head and hand sets shared by all LODs.','regions':skin});shutil.copyfile(O/'final_skin_luminance.json',P/'review/final_skin_luminance.json')
gates=read('review/gates/gates.json');assert gates['assets'][0]['sha256']==artifact('export/mm6_mer1.glb')['sha256']
faults=[g for g in gates['gates']if g['status']in ['FAIL','UNVERIFIED']]
dump('review/round3/open_findings.json',faults);dump('review/shared_gate_open_findings.json',faults)
by=collections.defaultdict(list)
for g in faults:by[(g['gate'],g['region'])].append(g)
fault_table=['| Gate / region | Rows | Worst | Limit | Clip / LOD / seconds |','|---|---:|---:|---:|---|']
for (gate,region),gs in sorted(by.items()):
 vals=[g for g in gs if g['worst']is not None]
 if vals:
  worst=(min if vals[0]['comparison']=='>='else max)(vals,key=lambda g:g['worst'])
  fault_table.append(f'| {gate} / {region} | {len(gs)} | {worst["worst"]:.4f} | {worst["comparison"]} {worst["threshold"]} | {worst["clip"]} / {worst["lod"]} / {worst["time_s"]} |')
 else:fault_table.append(f'| {gate} / {region} | {len(gs)} | UNVERIFIED | — | No weighted surface samples |')
(O/'fault_table.md').write_text('\n'.join(fault_table)+'\n')
binding=(P/'review/bindings_check.txt').read_text();assert binding.strip() and 'BAD'not in binding
receipt=json.loads((P/'review/round3/viewer_check_raw.txt').read_text());assert receipt['switched']==24 and not receipt['failed']and not receipt['consoleErrors'];receipt.update(checked_at=now,models=read('review/viewer/manifest.json')['models']);dump('review/round3/viewer_check.json',receipt)
artifacts=[artifact(p,role)for p,role in [('export/mm6_mer1.glb','runtime_body'),('export/mm6_mer1_club.glb','runtime_club'),('export/mm6_mer1.blend','editable_source')]+[(f'export/mm6_mer1_portable_{t}.glb',f'portable_{t}')for t in 'abc']]
dump('review/round3/artifacts.json',artifacts)
assert artifacts[1]['sha256']=='90d8d0ca129dbb046aeaf2d1eceae8ff0921e4cbc77208fe0752fe792d612b26'
changed=(P/'integration/actors.yml').read_bytes()!=(P/'work/round3/actors.yml').read_bytes();assert changed
cloth=[g for g in gates['gates']if g['gate']=='rotation_step_deg'and g['clip']=='Death'and g['region'].startswith('Cloak_')]
measurements=[g for g in gates['gates']if g['gate']in ['lowest_sole_m','walking_lift_min_mm','walking_lift_max_mm','walking_knee_flexion_deg','running_contact_pct','running_airborne_mm']]
dump('review/round3/locomotion_measurements.json',measurements)
state=read('creature_3d_progress.json');credits=sum(j.get('consumed_credits',0)for j in state['meshy']['jobs'].values());assert credits==80
summary={'status':'QA HOLD','technical_completion':False,'counts':gates['counts'],'runtime_sha256':artifacts[0]['sha256'],'credits_round3':20,'credits_total':credits,'credits_remaining':100-credits,'bindings_changed':changed,'viewer_switches':24,'skin_numeric_pass':all(x['not_darker']for x in skin.values()),'death_cloth_rotation_step_max_deg':max(g['worst']for g in cloth),'generated_at':now}
dump('review/round3/summary.json',summary)
print(json.dumps(summary,indent=2))
