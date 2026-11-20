from pathlib import Path
import sys,runpy,json
p=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(p/'scripts'))
def run(name,*args):
 sys.argv=[str(p/'scripts'/name),'--',*map(str,args)]
 runpy.run_path(sys.argv[0],run_name='__main__')
run('meshy_joints.py',p/'meshy/rig_v1/result_rigged_character_glb_url.glb',p/'work/step1.blend')
run('arm_rings.py',p/'work/step1.blend')
# A fresh hand fit must not consume yesterday's fitted frames.
f=p/'work/finger_joints.json'
if f.exists(): f.rename(p/'work/finger_joints.previous.json')
run('build_rig.py')
run('fit_fingers.py',p/'work/rig_v1.blend')
assert set(json.loads((p/'work/fingers_fit.json').read_text()))=={'R','L'}, 'Both hands need five fitted chains'
run('finger_joints.py',p/'work/rig_v1.blend')
run('build_rig.py')
run('hand_frame_check.py',p/'work/rig_v1.blend')
run('joint_xray.py',p/'work/step1.blend','Body',p/'work/joints_final.json',p/'review/g3_joints',p/'work/meshy_joints.json')
for side in ('R','L'): run('hand_xray.py',p/'work/rig_v1.blend',side,p/f'review/g3_hand_{side}')
