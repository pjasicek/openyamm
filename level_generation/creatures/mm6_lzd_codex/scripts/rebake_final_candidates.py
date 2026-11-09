import sys,json,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'))
from rebake_reduce import build
from rebake_textures import bake
from rebake_render import render
from round3_candidate_gates import check
for tag,ratio,level,bow in [('near70f',.7,0,.9),('lod1final',.33,1,.44),('lod2final',.10,2,.16),('lod3final',.044,3,.049)]:
 path=build(tag,ratio,level,bow);r=check(path);(P/f'review/rebake/{tag}_gates.json').write_text(json.dumps(r,indent=2));print('FINAL_CANDIDATE_GATES',tag,r['passed'],{k:v for k,v in r.items()if k!='motion'},r['motion']['issues'],flush=True)
 if not r['passed']:continue
 path=bake(path,tag,level);render(path,'reference_pbr',level,True);render(path,tag,level)
 r=json.loads(subprocess.check_output(['/usr/bin/python3',str(P/'scripts/rebake_measure.py'),tag,str(level)],text=True));(P/f'review/rebake/{tag}_metrics.json').write_text(json.dumps(r,indent=2));print('FINAL_CANDIDATE_VISUAL',tag,r,flush=True)
