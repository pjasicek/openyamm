"""Reproduce fitted source-frame skeleton and inspect both hands."""
import runpy, sys, json
from pathlib import Path
P=Path(__file__).resolve().parent; W=P.parent/'work'
def run(name,*args):
    sys.argv=[name,'--',*map(str,args)]; runpy.run_path(str(P/name),run_name='__main__')
run('compose_joints.py')
run('joint_xray.py',W/'step1.blend','Body',W/'joints_final.json',P.parent/'review/g3_joints',W/'joints.json')
run('build_rig.py')
run('fit_fingers.py',W/'rig_v1.blend')
F=json.loads((W/'fingers_fit.json').read_text())
assert set(F)=={'L','R'} and all(set(f)-{'verts'}=={'thumb','index','middle','ring','pinky'} for f in F.values())
run('finger_joints.py',W/'rig_v1.blend')
run('build_rig.py')
run('hand_frame_check.py',W/'rig_v1.blend')
for side in ('L','R'):
    run('hand_xray.py',W/'rig_v1.blend',side,P.parent/f'review/g5_hand_{side}')
