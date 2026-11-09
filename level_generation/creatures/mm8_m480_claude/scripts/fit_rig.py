from pathlib import Path
import runpy,sys
p=Path(__file__).resolve().parents[1]
def run(name,args=()):
 s=p/'scripts'/name;sys.argv=[str(s),'--']+[str(a) for a in args];runpy.run_path(str(s),run_name='__main__')
run('build_rig.py')
run('fit_fingers.py',[p/'work/rig_v1.blend'])
run('finger_joints.py',[p/'work/rig_v1.blend'])
run('build_rig.py')
run('hand_frame_check.py',[p/'work/rig_v1.blend'])
run('joint_xray.py',[p/'work/rig_v1.blend','Body',p/'work/joints_final.json',p/'review/joints',p/'work/meshy_joints.json'])
for side in 'LR':run('hand_xray.py',[p/'work/rig_v1.blend',side,p/'review'/('hand_'+side)])
