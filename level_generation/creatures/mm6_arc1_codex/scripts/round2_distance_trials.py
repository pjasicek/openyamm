"""Switch-size trials under the revised monotonically decreasing installed-count caps."""
import bpy,sys,json,subprocess,shutil
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'))
from round2_reduce import reset,reduce,render
D=P/'review/round2/reduction';W=P/'work/round2';S=json.loads((D/'selected.json').read_text());rows=[]
(D/'selected_before_distance_revision.json').write_text(json.dumps(S,indent=2))
for part,counts in [('body',[5200,1880,603]),('bow',[1150,420,200]),('arrow',[40,5,4])]:
 for level,count in enumerate(counts,1):
  ob,rig=reset(part);original=sum(len(f.vertices)-2 for f in ob.data.polygons);ratio=(count+.1)/original
  actual,protection=reduce(ob,rig,part,level,ratio);path=W/f'{part}_l{level}_distance.blend';bpy.ops.wm.save_as_mainfile(filepath=str(path));tag=f'{part}_l{level}_distance'
  render(ob,rig,part,level,tag,P/'work/round2/metric_tiers/baked/arc1_a')
  result=json.loads(subprocess.check_output(['/usr/bin/python3',str(P/'scripts/round2_reduction_metrics.py'),str(D),f'{part}_l{level}_arc1_a_high',tag],text=True))
  union=sum(v['union_pixels']for v in result['views']);inter=sum(v['intersection_pixels']for v in result['views'])
  row={'part':part,'lod':level,'triangles':actual,'ratio':ratio,'blend':str(path.relative_to(P)),'protected':protection,**result,'pooled_iou':inter/union,'union_pixels':union,'intersection_pixels':inter,'strategy':'distance cap revision'};rows.append(row);S[part][str(level)]=row
  (D/'distance_trials.json').write_text(json.dumps(rows,indent=2));(D/'distance_selected.json').write_text(json.dumps(S,indent=2));print('DISTANCE',part,level,actual,result['min_iou'],result['min_ssim'],inter/union,flush=True)
