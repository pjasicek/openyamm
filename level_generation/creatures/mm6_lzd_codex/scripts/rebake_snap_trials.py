import sys,json,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'))
from rebake_reduce import build
from rebake_render import render
from round3_candidate_gates import check
for tag,ratio,level,bow in [('snap2',.172,2,.175),('snap3',.055,3,.052)]:
 path=build(tag,ratio,level,bow,True);render(path,tag,level)
 r=json.loads(subprocess.check_output(['/usr/bin/python3',str(P/'scripts/rebake_measure.py'),tag,str(level)],text=True));(P/f'review/rebake/{tag}_geometry_metrics.json').write_text(json.dumps(r,indent=2));print('SNAP_SILHOUETTE',tag,{k:v['pooled_iou']for k,v in r.items()},flush=True)
 try:r=check(path)
 except Exception as e:r={'passed':False,'error':repr(e)}
 (P/f'review/rebake/{tag}_gates.json').write_text(json.dumps(r,indent=2));print('SNAP_GATES',tag,r['passed'],{k:v for k,v in r.items()if k!='motion'},r.get('motion',{}).get('issues',[]),flush=True)
