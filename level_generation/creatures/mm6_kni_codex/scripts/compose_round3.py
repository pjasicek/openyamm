"""Final rebake measurements and review sheets; no model mutations."""
from pathlib import Path
import csv,json,math
from PIL import Image,ImageDraw,ImageFont
from reduction_metrics_round2 import compare
P=Path(__file__).resolve().parents[1];R=P/'review/round3'
# Reuse the established clip/hand sheet layout.
source=(P/'scripts/compose_round2.py').read_text().split("for part,old,new")[0].replace("R=P/'review/round2'","R=P/'review/round3'")
exec(compile(source,__file__,'exec'))
old=[12815,6467,2314,754];before=[11100,5980,2314,697];new=[8403,5172,2110,697]
metrics=[]
def composite(path):
 im=Image.open(path).convert('RGBA');bg=Image.new('RGBA',im.size,(46,46,46,255));bg.alpha_composite(im);return bg.convert('RGB')
for lod in range(4):
 prefix='pbr'if lod==0 else f'lod{lod}'
 for tier in 'abc':
  rows=[compare(R/f'{prefix}_high_{tier}_{i}.png',R/f'{prefix}_low_{tier}_{i}.png') for i in range(8)]
  rec={'lod':lod,'tier':tier,'reference_triangles':old[lod],'round2_triangles':before[lod],'triangles':new[lod],'views':rows,'min_iou':min(x['iou']for x in rows),'min_ssim':min(x['ssim']for x in rows),'numeric_ssim_pass':min(x['ssim']for x in rows)>=.95}
  metrics.append(rec)
  pairs=[];heights=[]
  for i in range(8):
   a=Image.open(R/f'{prefix}_high_{tier}_{i}.png').convert('RGBA');b=Image.open(R/f'{prefix}_low_{tier}_{i}.png').convert('RGBA')
   ba=a.getbbox();bb=b.getbbox();box=(max(0,min(ba[0],bb[0])-14),max(0,min(ba[1],bb[1])-14),min(a.width,max(ba[2],bb[2])+14),min(a.height,max(ba[3],bb[3])+14))
   heights.append(ba[3]-ba[1]);a=composite(R/f'{prefix}_high_{tier}_{i}.png').crop(box);b=composite(R/f'{prefix}_low_{tier}_{i}.png').crop(box)
   w,h=a.size;cell=max(w,220);tile=Image.new('RGB',(2*cell+12,h+72),(28,31,36));d=ImageDraw.Draw(tile)
   d.text((8,5),f'{i*45} deg / IoU {rows[i]["iou"]:.4f} / SSIM {rows[i]["ssim"]:.4f}',font=small,fill='white')
   d.text((8,29),f'Accepted {old[lod]:,}',font=small,fill='white');d.text((cell+20,29),f'Rebaked {new[lod]:,}',font=small,fill='white')
   tile.paste(a,((cell-w)//2,68));tile.paste(b,(cell+12+(cell-w)//2,68));tile.save(R/f'comparison_l{lod}_{tier}_{i}.png');pairs.append(tile)
  rec['reference_actor_pixel_heights']=heights
  w=max(t.width for t in pairs);h=max(t.height for t in pairs);sheet=Image.new('RGB',(2*w,4*h+56),(28,31,36))
  ImageDraw.Draw(sheet).text((12,15),f'LOD{lod} / tier {tier.upper()} / native render size, accepted left - rebaked right',font=font,fill='white')
  for i,t in enumerate(pairs):sheet.paste(t,((i%2)*w,56+(i//2)*h))
  sheet.save(R/f'comparison_l{lod}_{tier}.jpg',quality=95)
(R/'visual_metrics.json').write_text(json.dumps(metrics,indent=2)+'\n')
with (R/'visual_metrics.csv').open('w')as f:
 w=csv.writer(f);w.writerow(['lod','tier','reference_triangles','round2_triangles','triangles','view_degrees','iou','ssim','actor_height_px'])
 for x in metrics:
  for i,v in enumerate(x['views']):w.writerow([x['lod'],x['tier'],x['reference_triangles'],x['round2_triangles'],x['triangles'],i*45,v['iou'],v['ssim'],x['reference_actor_pixel_heights'][i]])
curves=[]
for x in json.loads((R/'silhouette_curve.json').read_text()):
 curves.append({'lod':0,'method':x['tag'],'triangles':x['triangles'],'min_iou':x['min_iou'],'views':8,'stage':'silhouette','selected':x['tag']=='body_s04'})
for x in json.loads((R/'lod_curve.json').read_text()):
 curves.append({'lod':x['lod'],'method':str(x['step']),'triangles':x['triangles'],'min_iou':x['min_iou'],'views':8,'stage':'silhouette','selected':x['triangles']==new[x['lod']]})
for x in json.loads((R/'bake_candidate_probe.json').read_text()):
 curves.append({'lod':0,'method':x['tag'],'triangles':x['triangles'],'min_iou':min(v['iou']for v in x['views']),'min_ssim':min(v['ssim']for v in x['views']),'views':len(x['views']),'stage':'rebake_probe','selected':False})
for lod in range(4):
 subset=[x for x in metrics if x['lod']==lod]
 curves.append({'lod':lod,'method':'FINAL','triangles':new[lod],'min_iou':min(x['min_iou']for x in subset),'min_ssim':min(x['min_ssim']for x in subset),'views':24,'stage':'final_all_tiers','selected':True,'rig_status':'no new regression; baseline LOD3 G4 / Attack elbow findings retained','visual_status':'perceptual alternative; see README'})
(R/'reduction_curve.json').write_text(json.dumps(curves,indent=2)+'\n')
with (R/'reduction_curve.csv').open('w')as f:
 keys=['lod','method','triangles','min_iou','min_ssim','views','stage','selected','rig_status','visual_status'];w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(curves)
chart=Image.new('RGB',(1800,620),'white');d=ImageDraw.Draw(chart)
d.text((25,15),'Silhouette reduction curve: 8-view minimum IoU; green = final / red line = 0.99',font=font,fill='black')
for lod in range(4):
 points=[x for x in curves if x['lod']==lod and x['stage']=='silhouette' and (lod>0 or x['method'].startswith('body_s'))]
 points=sorted(points,key=lambda x:x['triangles']);final=next(x for x in curves if x['lod']==lod and x['method']=='FINAL')
 x0=lod*450+70;y0=90;w=345;h=410;mn=min(x['triangles']for x in points+[final]);mx=max(x['triangles']for x in points+[final]);lo=min(.985,min(x['min_iou']for x in points)-.001)
 xy=lambda n,v:(x0+(n-mn)/max(1,mx-mn)*w,y0+h*(1-(v-lo)/(1.001-lo)))
 d.text((x0,y0-30),f'LOD{lod}: {before[lod]:,} -> {new[lod]:,}',font=small,fill='black')
 for val in [.98,.99,1.0]:
  if val<lo:continue
  a,b=xy(mn,val),xy(mx,val);d.line([a,b],fill='#c04d4d'if val==.99 else '#ccc');d.text((x0-55,a[1]-8),f'{val:.2f}',font=small,fill='black')
 d.line([(x0,y0),(x0,y0+h),(x0+w,y0+h)],fill='black',width=2)
 pp=[xy(x['triangles'],x['min_iou'])for x in points];d.line(pp,fill='#3679cf',width=3)
 for a,b in pp:d.ellipse((a-4,b-4,a+4,b+4),fill='#3679cf')
 a,b=xy(new[lod],final['min_iou']);d.ellipse((a-7,b-7,a+7,b+7),outline='#158354',width=3)
 for n in [mn,mx]:
  a,_=xy(n,lo);d.text((a-15,y0+h+12),str(n),font=small,fill='black')
d.text((25,577),'All alternate methods, rebake probes and exact final SSIM are retained in CSV/JSON; no SSIM threshold pass is implied.',font=small,fill='black')
chart.save(R/'reduction_curve.png')
print(json.dumps([{k:v for k,v in x.items()if k not in ['views','reference_actor_pixel_heights']}for x in metrics],indent=2))
