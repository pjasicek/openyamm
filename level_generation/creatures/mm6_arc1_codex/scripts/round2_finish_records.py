"""Write final measured reduction records and validate the staged descriptor/skin weights."""
import json,csv,subprocess,sys
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parents[1];R=P/'review/round2';D=R/'reduction'
cal=json.loads((R/'transitions_and_head.json').read_text())['calibration'];path=P/'integration/actors.yml'
import re
path.write_text(re.sub(r'stride_length: [0-9.]+',f"stride_length: {cal['new_binding_stride_m']:.8f}",path.read_text()))
rows=json.loads((D/'curve.json').read_text());selected=json.loads((D/'selected.json').read_text())
rows=[r for r in rows if r.get('strategy')!='selected rebake; actual tier materials']
metrics=json.loads((D/'final_material_metrics.json').read_text());assert not metrics['failures']
for part,levels in selected.items():
 for level,row in levels.items():
  assert json.loads((R/f'lod_gates/lod{level}/status.json').read_text())['pass']
  m=metrics['measurements'][part][level];row.update(min_iou=min(x['min_iou']for x in m.values()),min_ssim=min(x['min_ssim']for x in m.values()),pass_=True,rig_gates='pass_all_clips',strategy='selected rebake; actual tier materials',tier_metrics=m)
  row['pass']=row.pop('pass_');row['criterion']='near per-view .99/.95'if int(level)==0 else 'equipped-standing pooled IoU .97 at the switch size';row['pooled_iou']=min(x.get('pooled_iou',x['min_iou'])for x in m.values());rows.append(row)
probe=json.loads((R/'rebake_probe.json').read_text())['metrics']
rows.append({'part':'body','lod':0,'step':2,'ratio':.81,'triangles':8555,'strategy':'rejected rebake','min_iou':probe['min_iou'],'min_ssim':probe['min_ssim'],'pass':False,'rig_gates':'visual_rejection'})
(D/'curve.json').write_text(json.dumps(rows,indent=2));(D/'selected.json').write_text(json.dumps(selected,indent=2))
with (D/'curve.csv').open('w')as f:
 fields=['part','lod','step','ratio','triangles','min_iou','min_ssim','pass','rig_gates','strategy','pooled_iou','criterion'];w=csv.DictWriter(f,fields,extrasaction='ignore');w.writeheader();w.writerows(rows)
im=Image.new('RGB',(1500,1050),'white');draw=ImageDraw.Draw(im);font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',16)
draw.text((25,15),'Near-mesh reduction: eight-view component IoU / SSIM; selected circles use final rebaked tier maps',fill='black',font=font)
for col,part in enumerate(['body','bow','arrow']):
 rs=[r for r in rows if r['part']==part and r.get('lod')==0 and ('revised batch'in r.get('strategy','')or r.get('strategy')=='rejected rebake')]
 for row,(key,limit)in enumerate([('min_iou',.99),('min_ssim',.95)]):
  left=col*500+70;top=row*300+80;right=left+390;bottom=top+210
  values=[r['triangles']for r in rs]+[selected[part]['0']['triangles']];lo,hi=min(values),max(values);span=max(1,hi-lo);lo-=span*.06;hi+=span*.06
  low=max(0,min([r[key]for r in rs]+[limit])-.015);high=1.005
  def xy(x,y):return(left+(x-lo)/(hi-lo)*(right-left),bottom-(y-low)/(high-low)*(bottom-top))
  draw.text((left,top-27),part+' / '+key,fill='black',font=font)
  for i in range(5):
   x=lo+(hi-lo)*i/4;y=low+(high-low)*i/4;px,_=xy(x,low);_,py=xy(lo,y);draw.line((left,py,right,py),fill='#dddddd');draw.text((left-60,py-8),f'{y:.3f}',fill='black',font=font);draw.text((px-15,bottom+5),str(round(x)),fill='black',font=font)
  draw.line((left,top,left,bottom,right,bottom),fill='black',width=2);_,y=xy(lo,limit);draw.line((left,y,right,y),fill='#888888',width=2)
  for item in rs:
   x,y=xy(item['triangles'],item[key]);draw.ellipse((x-3,y-3,x+3,y+3),fill='#777777')
  v=selected[part]['0'];x,y=xy(v['triangles'],v[key]);draw.ellipse((x-7,y-7,x+7,y+7),outline='#0072b2',width=3)
  draw.text((left+135,bottom+31),'Triangles',fill='black',font=font)
distance=json.loads((D/'assembled_distance_metrics.json').read_text());draw.text((25,702),'Distance selection: equipped Standing pooled IoU >= 0.97 at 550 / 220 / 88 px; strictly decreasing installed-count caps',fill='black',font=font)
draw.text((25,745),'Level       Body incl. string      Bow      Arrow      Equipped triangles      Standing IoU       Attack diagnostic IoU',fill='black',font=font)
for level in range(1,4):
 body=selected['body'][str(level)]['triangles']+24;bow=selected['bow'][str(level)]['triangles'];arrow=selected['arrow'][str(level)]['triangles'];st=next(r for r in distance['rows']if r['lod']==level and r['clip']=='Standing');at=next(r for r in distance['rows']if r['lod']==level and r['clip']=='Attack')
 draw.text((25,745+level*45),f'LOD{level}           {body:<22}{bow:<10}{arrow:<11}{body+bow+arrow:<26}{st["pooled_iou"]:.5f}                  {at["pooled_iou"]:.5f}',fill='black',font=font)
draw.text((25,960),'The Attack column is supplementary: LOD2/3 need visual acceptance at distance. Full component metrics and rejected trials are in curve.csv.',fill='black',font=font)
im.save(D/'curve.png')
r=subprocess.run([sys.executable,str(P.parents[2]/'output/codex_batch/check_bindings.py'),str(path)],capture_output=True,text=True)
(R/'check_bindings.log').write_text(r.stdout+r.stderr);r.check_returncode();assert 'BAD'not in r.stdout;print(r.stdout)
