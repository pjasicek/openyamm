import bpy,sys,runpy,os
from pathlib import Path
P=Path(__file__).resolve().parents[1];os.chdir(P)
def run(n,*args):
 sys.argv=[n,'--',*map(str,args)];runpy.run_path(str(P/'scripts'/n),run_name='__main__')
run('meshy_joints.py',P/'meshy/rig_v1/result_rigged_character_glb_url.glb',P/'work/step1.blend')
run('fit_figc_joints.py')
run('build_rig.py')
run('fit_fingers.py',P/'work/rig_v1.blend')
run('finger_joints.py',P/'work/rig_v1.blend')
run('build_rig.py')
run('joint_xray.py',P/'work/step1.blend','Body',P/'work/joints_final.json',P/'review/joints',P/'work/meshy_joints.json')
for side in ['L','R']:run('hand_xray.py',P/'work/rig_v1.blend',side,P/f'review/hand_{side}')
