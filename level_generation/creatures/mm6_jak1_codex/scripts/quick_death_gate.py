import os,runpy,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];os.environ['CLIPS']='Death';sys.argv=['gate','--',str(P/'export/mm6_jak1_runtime_lod0.glb')];runpy.run_path(str(P/'scripts/g6_staff_mesh.py'),run_name='__main__')

import json,numpy as np
sys.dont_write_bytecode=True
sys.path.insert(0,str(P.parent/'claude_shared/gates'))
import run_gates as shared
cfg={'hands':{'L':{'palm_axis':[0,1,0]},'R':{'palm_axis':[0,1,0]}},'props':[],'cloth':[]}
glb=shared.Glb(P/'export/mm6_jak1_runtime_lod0.glb');report=shared.Report(cfg)
for clip,animation,start,end in glb.clips():
 times=shared.sample_grid(start,end,48);shared.bone_gates(glb,glb.pose(animation,times),times,clip,cfg,report,[])
rows=list(report.rows.values());(P/'review/round2/shared_bone_probe.json').write_text(json.dumps(rows,indent=2))
print('SHARED BONE PROBE',[(r['clip'],r['gate'],r['region'],round(r['worst'],2))for r in rows if r['status']=='FAIL' and r['gate'] not in ['free_palm_angle_deg']],flush=True)
