import bpy,runpy,sys,shutil,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];R=P/'review/round2';W=P/'work/round2'
def run(n,args=[]):
 sys.argv=[n,'--',*map(str,args)];runpy.run_path(str(P/'scripts'/n),run_name='__main__')
for lod in range(4):
 run('g6_sword_round2.py',[W/('runtime_combined.glb' if lod==0 else f'runtime_combined_l{lod}.glb')])
 for kind in ['sword','hand_furniture','blade_only']:shutil.copyfile(R/f'g6_{kind}.json',R/f'g6_{kind}_l{lod}.json')
run('posture_blade_round2.py')
run('trace_export.py',[W/'runtime_combined.glb',*[f'{r}={P}/work/source_motion_reference.glb:{r}'for r in ['Standing','Walking','Running','Attack','Hit','Death','Fidget']]])
shutil.copyfile(P/'work/g6_trace.json',R/'g6_trace.json')

import os
os.environ['ANATOMY_BLEND']='audit_baseline_l0.blend';os.environ['ANATOMY_REPORT']='anatomy_baseline.json';run('anatomy_round2.py');os.environ.pop('ANATOMY_BLEND');os.environ.pop('ANATOMY_REPORT')
a=json.loads((R/'anatomy.json').read_text());b=json.loads((R/'anatomy_baseline.json').read_text());assert a['clips']==b['clips'];a['baseline_identical']=True;a['no_hyperextension_or_roll_violation']=all(v['flexion_deg'][0]>=-5 and max(map(abs,v['roll_deg']))<=90 for row in a['clips'].values() for v in row.values());(R/'anatomy.json').write_text(json.dumps(a,indent=2))
