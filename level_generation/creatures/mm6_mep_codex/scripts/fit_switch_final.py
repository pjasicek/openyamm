import bpy,json,sys,subprocess
from pathlib import Path
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import reduce_measured as rm
R=p/'review/reduction';curve=[];sel=json.loads((R/'selected.json').read_text())
for part,level,targets in [('body',3,[1800,1600,1400,1200]),('staff',2,[600,528,480]),('staff',3,[320,240,192,160])]:
 for n,target in enumerate(targets):
  ob,r=rm.reset(part);original=sum(len(f.vertices)-2 for f in ob.data.polygons);count,protection=rm.reduce(ob,r,part,level,target/original,preview=False);tag=f'switch_fine_{part}_{level}_{n}';path=f'work/reduction/{tag}.blend';bpy.ops.wm.save_as_mainfile(filepath=str(p/path));rm.render(ob,r,part,level,tag)
  score=json.loads(subprocess.check_output(['/usr/bin/python3',str(p/'scripts/reduction_metrics.py'),str(R),f'switch_ref_{part}_{level}',tag],text=True));row={'part':part,'lod':level,'triangles':count,'blend':path,'protected':protection,**score};row['pass']=row['pooled_iou']>=.97;curve.append(row);print('SWITCH_FINE',part,level,count,row['pooled_iou'],row['pass'],flush=True)
  if row['pass']:sel[part][str(level)]=row
  (R/'switch_fine.json').write_text(json.dumps(curve,indent=2))
(R/'selected.json').write_text(json.dumps(sel,indent=2))
