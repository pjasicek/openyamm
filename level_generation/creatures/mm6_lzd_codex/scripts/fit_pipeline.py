import runpy,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1]
def run(n,*a):
 sys.argv=[n,'--',*map(str,a)];runpy.run_path(str(P/'scripts'/n),run_name='__main__')
run('meshy_joints.py',P/'meshy/rig_v1/result_rigged_character_glb_url.glb',P/'work/step1.blend')
run('fit_lizard_joints.py')
run('build_rig.py')
run('fit_fingers.py',P/'work/rig_v1.blend')
run('finger_joints.py',P/'work/rig_v1.blend')
run('build_rig.py')
run('joint_xray.py',P/'work/step1.blend','Body',P/'work/joints_final.json',P/'review/g3',P/'work/meshy_joints.json')
