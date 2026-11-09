import os,sys,runpy
from pathlib import Path
p=Path(__file__).resolve().parents[1];os.chdir(p);sys.path.insert(0,str(p/'scripts'))
def run(name,args=()):
 sys.argv=[name,'--']+[str(x) for x in args];runpy.run_path(str(p/'scripts'/name),run_name='__main__')
run('finalize_joint_envelope.py',[p/'work/step1.blend'])
run('build_rig.py')
run('fit_fingers.py',[p/'work/rig_v1.blend'])
run('finger_joints.py',[p/'work/rig_v1.blend'])
run('build_rig.py')
run('hand_frame_check.py',[p/'work/rig_v1.blend'])
run('hand_xray.py',[p/'work/rig_v1.blend','R',p/'review/finger_joints'])
