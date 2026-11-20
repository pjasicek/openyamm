"""Fit lower LODs to current batch pooled-IoU .97 rule and decreasing triangle budgets."""
import bpy,json,sys,subprocess
from pathlib import Path
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import reduce_measured as rm
R=p/'review/reduction';sel=json.loads((R/'selected.json').read_text());curve=[]
for part,counts in [('body',[5500,2500,1000]),('staff',[880,400,160])]:
 for level,target in enumerate(counts,1):
  ob,r=rm.reset(part);rm.render(ob,r,part,level,f'switch_ref_{part}_{level}')
  original=sum(len(f.vertices)-2 for f in ob.data.polygons)
  for step,factor in enumerate([1,.8,.6,.4]):
   ob,r=rm.reset(part);n,protection=rm.reduce(ob,r,part,level,target*factor/original,preview=False);tag=f'switch3_{part}_{level}_{step}';path=f'work/reduction/{tag}.blend';bpy.ops.wm.save_as_mainfile(filepath=str(p/path));rm.render(ob,r,part,level,tag)
   score=json.loads(subprocess.check_output(['/usr/bin/python3',str(p/'scripts/reduction_metrics.py'),str(R),f'switch_ref_{part}_{level}',tag],text=True));row={'part':part,'lod':level,'triangles':n,'blend':path,'protected':protection,**score};row['pass']=row['pooled_iou']>=.97;curve.append(row);print('SWITCH_LOD',part,level,n,row['pooled_iou'],row['pass'],flush=True)
   (R/'switch_curve_v3.json').write_text(json.dumps(curve,indent=2))
   if row['pass']:sel[part][str(level)]=row
   else:break
(R/'selected.json').write_text(json.dumps(sel,indent=2))
