import sys,json,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'))
from rebake_render import render
path=P/'work/rebake/lod3_selected_baked.blend'
render(path,'reference64',3,True,parts=['actor'],samples=64);render(path,'lod3_quality64',3,parts=['actor'],samples=64)
r=json.loads(subprocess.check_output(['/usr/bin/python3',str(P/'scripts/rebake_measure.py'),'lod3_quality64','3','8','actor','reference64'],text=True));(P/'review/rebake/lod3_quality64_actor_metrics.json').write_text(json.dumps(r,indent=2));print('FAR_64_SAMPLES',r['actor']['pooled_iou'],flush=True)
if r['actor']['passed']:(P/'review/rebake/final_selection.json').write_text(json.dumps({'0':{'tag':'near70final'},'1':{'tag':'lod1_selected'},'2':{'tag':'lod2_selected'},'3':{'tag':'lod3_selected','comparison':'lod3_quality64','reference':'reference64','samples':64}},indent=2))
import runpy
runpy.run_path(str(P/'scripts/rebake_tier_checks.py'),run_name='__main__')
