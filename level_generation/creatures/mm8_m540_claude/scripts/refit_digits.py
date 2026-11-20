from pathlib import Path
import runpy,sys
p=Path(__file__).resolve().parents[1]
def run(name,args=()):
 s=p/'scripts'/name;sys.argv=[str(s),'--']+[str(x) for x in args];runpy.run_path(str(s),run_name='__main__')
run('fit_fingers.py',[p/'work/rig_v1.blend'])
run('finger_joints.py',[p/'work/rig_v1.blend'])
run('build_rig.py')
run('hand_frame_check.py',[p/'work/rig_v1.blend'])
run('finger_weights.py',[p/'work/rig_v1.blend',p/'work/rig_fingers.blend'])
for side in ('R','L'):run('hand_xray.py',[p/'work/rig_fingers.blend',side,p/'review'/('hand_'+side)])
