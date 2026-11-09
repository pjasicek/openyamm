"""Fit measured source-frame rig; run after the Meshy rig download."""
from pathlib import Path
import runpy,sys
p=Path(__file__).resolve().parents[1]
def run(n,*a):
 sys.argv=[n,'--',*[str(x) for x in a]];runpy.run_path(str(p/'scripts'/n),run_name='__main__')
run('measure_joints.py',p/'work/step1.blend','Body')
run('build_rig.py')
run('fit_fingers.py',p/'work/rig_v1.blend')
run('finger_joints.py',p/'work/rig_v1.blend')
run('build_rig.py')
run('hand_frame_check.py',p/'work/rig_v1.blend')
for side in ('R','L'):run('hand_xray.py',p/'work/rig_v1.blend',side,p/f'review/fingers_{side}')
run('joint_xray.py',p/'work/step1.blend','Body',p/'work/joints_final.json',p/'review/joints_final',p/'work/meshy_joints.json')
