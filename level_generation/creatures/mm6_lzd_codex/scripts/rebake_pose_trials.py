import sys,json,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'))
from rebake_reduce import build
from rebake_render import render
for tag,ratio,level,bow in [('pose2',.172,2,.175),('pose3',.055,3,.052)]:
 path=build(tag,ratio,level,bow,True,False,True);render(path,tag,level)
 r=json.loads(subprocess.check_output(['/usr/bin/python3',str(P/'scripts/rebake_measure.py'),tag,str(level)],text=True));(P/f'review/rebake/{tag}_geometry_metrics.json').write_text(json.dumps(r,indent=2));print('POSE_SILHOUETTE',tag,{k:v['pooled_iou']for k,v in r.items()},flush=True)
