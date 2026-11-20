import runpy,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'))
runpy.run_path(str(P/'scripts/rebake_textures.py'),run_name='__main__')
runpy.run_path(str(P/'scripts/rebake_render.py'),run_name='__main__')
from round3_candidate_gates import check
import json
r=check(P/'work/rebake/near60e_baked.blend');(P/'review/rebake/near60e_gates.json').write_text(json.dumps(r,indent=2));print('REBaked_GATES',r['passed'],{k:v for k,v in r.items()if k!='motion'},r['motion']['issues'],flush=True)
