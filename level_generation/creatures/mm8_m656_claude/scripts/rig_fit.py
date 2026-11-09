import sys, runpy, os
from pathlib import Path
P = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P/'scripts'))
def run(name, *args):
    sys.argv = [name, '--', *map(str,args)]
    runpy.run_path(str(P/'scripts'/name), run_name='__main__')
run('compose_joints.py')
run('joint_xray.py',P/'work/step1.blend','Body',P/'work/joints_final.json',P/'review/g3_joints',P/'work/joints.json')
run('build_rig.py')
run('fit_fingers.py', P/'work/rig_v1.blend')
run('finger_joints.py', P/'work/rig_v1.blend')
run('build_rig.py')
run('hand_frame_check.py', P/'work/rig_v1.blend')
for side in ('R','L'):
    run('hand_xray.py', P/'work/rig_v1.blend', side, P/f'review/g3_hand_{side}')
