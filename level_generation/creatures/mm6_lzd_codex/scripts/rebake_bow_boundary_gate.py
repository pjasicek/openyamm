import sys,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'))
from round3_candidate_gates import check
from rebake_textures import bake
from rebake_render import render
r=check(P/'work/rebake/bow80_boundary.blend');(P/'review/rebake/bow80_boundary_gates.json').write_text(json.dumps(r,indent=2));print('BOW80_GATES',{k:v for k,v in r.items()if k!='motion'},r['motion']['issues'],flush=True)
if r['passed']:
 path=bake(P/'work/rebake/bow80_boundary.blend','bow80_boundary',0);render(path,'bow80_baked',0,parts=['bow'])
 import subprocess
 metrics=json.loads(subprocess.check_output(['/usr/bin/python3',str(P/'scripts/rebake_measure.py'),'bow80_baked','0','8','bow'],text=True));(P/'review/rebake/bow80_baked_metrics.json').write_text(json.dumps(metrics,indent=2));print('BOW80_BAKED',metrics,flush=True)
