from pathlib import Path
import sys,runpy,json
p=Path(__file__).resolve().parents[1]
def run(n,*a):
 sys.argv=[n,'--',*[str(x) for x in a]];runpy.run_path(str(p/'scripts'/n),run_name='__main__')
run('meshy_joints.py',p/'meshy/rig_v1/result_rigged_character_glb_url.glb',p/'work/step1.blend')
j=json.loads((p/'work/meshy_joints.json').read_text());j['height_m']=1.7;(p/'work/meshy_joints.json').write_text(json.dumps(j,indent=2))
run('fit_joints.py',p/'work/step1.blend','Body')
run('joint_xray.py',p/'work/step1.blend','Body',p/'work/meshy_joints.json',p/'review/joints',p/'work/joints.json')
