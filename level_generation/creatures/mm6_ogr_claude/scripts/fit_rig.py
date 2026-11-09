from pathlib import Path
import runpy,sys
p=Path(__file__).resolve().parents[1]
def run(name,args=()):
 s=p/'scripts'/name
 sys.argv=[str(s),'--']+[str(x) for x in args]
 runpy.run_path(str(s),run_name='__main__')
run('meshy_joints.py',[p/'meshy/rig_v1/result_rigged_character_glb_url.glb',p/'work/step1.blend'])
run('arm_rings.py',[p/'work/step1.blend'])
run('build_rig.py')
run('fit_fingers.py',[p/'work/rig_v1.blend'])
run('finger_joints.py',[p/'work/rig_v1.blend'])
run('build_rig.py')
run('hand_frame_check.py',[p/'work/rig_v1.blend'])

run('joint_xray.py',[p/'work/rig_v1.blend','Body',p/'work/joints_final.json',p/'review/joints',p/'work/meshy_joints.json'])
for side in ('R','L'):
 run('hand_xray.py',[p/'work/rig_v1.blend',side,p/'review'/('hand_'+side)])
