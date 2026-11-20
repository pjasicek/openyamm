from pathlib import Path
import runpy,sys,json
p=Path(__file__).resolve().parents[1]
def run(n,*a):
 sys.argv=[n,'--',*map(str,a)];runpy.run_path(str(p/'scripts'/n),run_name='__main__')
run('meshy_joints.py',p/'meshy/rig_v1/result_rigged_character_glb_url.glb',p/'work/step1.blend')
f=p/'work/meshy_joints.json';j=json.loads(f.read_text());j['height_m']=1.7;f.write_text(json.dumps(j,indent=2))
run('proportions.py','source',p.parents[2]/'anim_library/humanoid_set/Armed.glb')
run('fit_joints.py',p/'work/step1.blend','Body')
run('joint_xray.py',p/'work/step1.blend','Body',p/'work/meshy_joints.json',p/'review/proposal_joints',p/'work/joints.json')
