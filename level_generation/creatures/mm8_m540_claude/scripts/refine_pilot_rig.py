from pathlib import Path
import runpy,sys
p=Path(__file__).resolve().parents[1]
def run(name,args=()):
 s=p/'scripts'/name;sys.argv=[str(s),'--']+[str(x) for x in args];runpy.run_path(str(s),run_name='__main__')
run('arm_rings.py',[p/'work/step1.blend'])
run('build_rig.py')
run('finger_weights.py',[p/'work/rig_v1.blend',p/'work/rig_fingers.blend'])
run('joint_xray.py',[p/'work/rig_fingers.blend','Body',p/'work/joints_final.json',p/'review/joints',p/'work/meshy_joints.json'])
for name in ['fit_body_weights.py','join_head.py','build_pilots.py']:run(name)
