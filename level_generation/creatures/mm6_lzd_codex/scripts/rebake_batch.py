import sys,json,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'))
from rebake_reduce import build
from rebake_textures import bake
from rebake_render import render
from round3_candidate_gates import check
path=build('near70h',.7,0,.90);path=bake(path,'near70h',0);render(path,'near70h',0,False,1)
for tag,ratio,level,bow in [('lod1anchors',.39,1,.44),('lod2anchors',.10,2,.16),('lod3anchors',.044,3,.049)]:
 path=build(tag,ratio,level,bow)
 try:r=check(path)
 except Exception as e:r={'passed':False,'error':repr(e)}
 (P/f'review/rebake/{tag}_gates.json').write_text(json.dumps(r,indent=2));print('LOD_TRIAL',tag,r['passed'],{k:v for k,v in r.items()if k!='motion'},r.get('motion',{}).get('issues',[]),flush=True)
