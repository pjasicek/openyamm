import sys,json,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'))
from rebake_reduce import build
from rebake_render import render
from round3_candidate_gates import check
path=build('bow70_boundary',.7,0,.7);render(path,'bow70_boundary',0,parts=['bow'])
r=json.loads(subprocess.check_output(['/usr/bin/python3',str(P/'scripts/rebake_measure.py'),'bow70_boundary','0','8','bow'],text=True));(P/'review/rebake/bow70_boundary_geometry_metrics.json').write_text(json.dumps(r,indent=2));print('BOW70_GEOMETRY',r,flush=True)
r=check(P/'work/rebake/global1.blend');(P/'review/rebake/global1_final_gates.json').write_text(json.dumps(r,indent=2));print('GLOBAL1_FINAL_GATES',{k:v for k,v in r.items()if k!='motion'},r['motion']['issues'],flush=True)
