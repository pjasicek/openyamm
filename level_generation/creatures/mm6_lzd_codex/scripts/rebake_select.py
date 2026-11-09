import sys,json,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'))
from rebake_reduce import build
from rebake_textures import bake
from rebake_render import render
from round3_candidate_gates import check
path=build('lod3anchors',.044,3,.049)
r=check(path);(P/'review/rebake/lod3anchors_gates.json').write_text(json.dumps(r,indent=2));print('LOD3_ANCHORS',r['passed'],{k:v for k,v in r.items()if k!='motion'},r['motion']['issues'],flush=True)
path=build('near60h',.6,0,.9);path=bake(path,'near60h',0);render(path,'near60h',0,False,1)
r=json.loads(subprocess.check_output(['/usr/bin/python3',str(P/'scripts/rebake_measure.py'),'near60h','0','1'],text=True));(P/'review/rebake/near60h_front_metrics.json').write_text(json.dumps(r,indent=2));print('NEAR60_FRONT',r,flush=True)
tag='near60h'if all(v['passed']for v in r.values())else'near70h';path=P/f'work/rebake/{tag}_baked.blend'
render(path,'reference_pbr',0,True);render(path,tag,0)
r=json.loads(subprocess.check_output(['/usr/bin/python3',str(P/'scripts/rebake_measure.py'),tag,'0'],text=True));(P/f'review/rebake/{tag}_metrics.json').write_text(json.dumps(r,indent=2));print('NEAR_ALL_VIEWS',tag,r,flush=True)
if all(v['passed']for v in r.values()):
 gates=check(path);(P/f'review/rebake/{tag}_gates.json').write_text(json.dumps(gates,indent=2));print('NEAR_GATES',tag,gates['passed'],flush=True)
