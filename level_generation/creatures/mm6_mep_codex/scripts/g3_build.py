import runpy,sys
from pathlib import Path
p=Path(__file__).resolve().parents[1]
def run(n,*args):
 sys.argv=[n,'--',*map(str,args)];runpy.run_path(str(p/'scripts'/n),run_name='__main__')
run('fit_joints.py')
run('joint_xray.py',p/'work/step1.blend','Body',p/'work/joints_final.json',p/'review/g3_joints',p/'work/meshy_joints.json')
run('build_rig.py')
run('fit_fingers.py',p/'work/rig_v1.blend')
run('finger_joints.py',p/'work/rig_v1.blend')
run('build_rig.py')
run('finger_weights.py',p/'work/rig_v1.blend',p/'work/rig_weighted.blend')
run('hand_frame_check.py',p/'work/rig_weighted.blend')
for side in ['R','L']:run('hand_xray.py',p/'work/rig_weighted.blend',side,p/'review'/f'g3_hand_{side}')
