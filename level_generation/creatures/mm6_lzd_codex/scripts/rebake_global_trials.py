import sys,json,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'))
from rebake_reduce import build
from rebake_textures import bake
from rebake_render import render
from round3_candidate_gates import check
for tag,ratio,level,bow in [('global1',.4,1,.44),('global2',.17,2,.17),('global3',.054,3,.049)]:
 path=build(tag,ratio,level,bow,True);r=check(path);(P/f'review/rebake/{tag}_gates.json').write_text(json.dumps(r,indent=2));print('GLOBAL_GATES',tag,r['passed'],{k:v for k,v in r.items()if k!='motion'},r['motion']['issues'],flush=True)
 # Reject geometry before baking if its silhouette cannot meet the cap.
 render(path,tag,level)
 r=json.loads(subprocess.check_output(['/usr/bin/python3',str(P/'scripts/rebake_measure.py'),tag,str(level)],text=True));(P/f'review/rebake/{tag}_geometry_metrics.json').write_text(json.dumps(r,indent=2));print('GLOBAL_SILHOUETTE',tag,{k:v['pooled_iou']for k,v in r.items()},flush=True)
