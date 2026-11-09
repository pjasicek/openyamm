import bpy,json,sys,subprocess
from pathlib import Path
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import reduce_measured as rm
R=p/'review/reduction';rows=sum([json.loads((R/f).read_text()) for f in ['switch_curve.json','switch_curve_v2.json','switch_curve_v3.json','switch_fine.json']],[]);sel=json.loads((R/'selected.json').read_text());checks=[]
for part in ['body','staff']:
 previous=0
 for level in [3,2,1]:
  candidates=sorted([r for r in rows if r['part']==part and r['triangles']>previous and r['triangles']<sel[part]['0']['triangles']],key=lambda r:r['triangles']);seen=set()
  for i,row in enumerate(candidates):
   if row['blend'] in seen:continue
   seen.add(row['blend']);bpy.ops.wm.open_mainfile(filepath=str(p/row['blend']));ob=bpy.data.objects['Body' if part=='body' else 'StaffMesh'];r=bpy.data.objects['Rig'];tag=f'switch_cross_{part}_{level}_{i}';rm.render(ob,r,part,level,tag)
   score=json.loads(subprocess.check_output(['/usr/bin/python3',str(p/'scripts/reduction_metrics.py'),str(R),f'switch_ref_{part}_{level}',tag],text=True));result={**row,**score,'lod':level,'pass':score['pooled_iou']>=.97,'render_tag':tag};checks.append(result);print('SWITCH_CROSS',part,level,row['triangles'],score['pooled_iou'],result['pass'],flush=True)
   if result['pass']:sel[part][str(level)]=result;previous=row['triangles'];break
  else:raise AssertionError((part,level,'no decreasing passing candidate'))
  (R/'switch_cross.json').write_text(json.dumps(checks,indent=2));(R/'selected.json').write_text(json.dumps(sel,indent=2))
