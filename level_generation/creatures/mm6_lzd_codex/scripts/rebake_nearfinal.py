import sys,json,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'))
from rebake_reduce import build
from rebake_textures import bake
from rebake_render import render
from round3_candidate_gates import check
for tag,ratio in [('near65final',.65),('near70final',.7)]:
 path=build(tag,ratio,0,.9);path=bake(path,tag,0);render(path,tag,0)
 r=json.loads(subprocess.check_output(['/usr/bin/python3',str(P/'scripts/rebake_measure.py'),tag,'0'],text=True));(P/f'review/rebake/{tag}_metrics.json').write_text(json.dumps(r,indent=2));print('NEAR_FINAL',tag,{k:[v['min_iou'],v['min_ssim'],v['passed']]for k,v in r.items()},flush=True)
 if all(v['passed']for v in r.values()):
  r=check(path);(P/f'review/rebake/{tag}_gates.json').write_text(json.dumps(r,indent=2));print('NEAR_FINAL_GATES',tag,r['passed'],{k:v for k,v in r.items()if k!='motion'},r['motion']['issues'],flush=True)
  if r['passed']:break
