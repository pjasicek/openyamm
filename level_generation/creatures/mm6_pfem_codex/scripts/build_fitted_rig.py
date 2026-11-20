import bpy,runpy,sys,json
from pathlib import Path
p=Path(__file__).resolve().parents[1];s=p/'scripts'
def run(name,*args):
 sys.argv=[name,'--',*map(str,args)];runpy.run_path(str(s/name),run_name='__main__')
run('arm_rings.py',p/'work/step1.blend')
run('build_rig.py')
run('fit_fingers.py',p/'work/rig_v1.blend')
data=json.load(open(p/'work/fingers_fit.json'));assert set(data)=={'R','L'},data.keys()
run('finger_joints.py',p/'work/rig_v1.blend')
run('build_rig.py')
run('hand_frame_check.py',p/'work/rig_v1.blend')
run('weights_pfem.py',p/'work/rig_v1.blend',p/'work/rig_weighted.blend')
run('finger_weights.py',p/'work/rig_weighted.blend',p/'work/rig_fingers.blend')
run('hand_xray.py',p/'work/rig_fingers.blend','R',p/'review/hand_joints_R')
run('hand_xray.py',p/'work/rig_fingers.blend','L',p/'review/hand_joints_L')
