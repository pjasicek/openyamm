import sys, runpy, json
from pathlib import Path
P = Path(__file__).resolve().parents[1]
sys.argv=['meshy_joints.py','--',str(P/'meshy/rig_v1/result_rigged_character_glb_url.glb'),str(P/'work/step1.blend')]
runpy.run_path(str(P/'scripts/meshy_joints.py'), run_name='__main__')
p = P/'work/meshy_joints.json'
j = json.loads(p.read_text()); j['height_m'] = 1.7; p.write_text(json.dumps(j,indent=2))
sys.argv=['joint_xray.py','--',str(P/'work/step1.blend'),'Body',str(p),str(P/'review/joints_meshy'),str(P/'work/joints.json')]
runpy.run_path(str(P/'scripts/joint_xray.py'), run_name='__main__')
