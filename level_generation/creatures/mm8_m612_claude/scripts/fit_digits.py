from pathlib import Path
import runpy,sys
P=Path(__file__).resolve().parents[1]
def step(name,*args):
    script=P/'scripts'/name
    sys.argv=[str(script),'--',*map(str,args)]
    runpy.run_path(str(script),run_name='__main__')
step('fit_fingers.py',P/'work/rig_v1.blend')
step('finger_joints.py',P/'work/rig_v1.blend')
step('build_rig.py')
step('hand_frame_check.py',P/'work/rig_v1.blend')
step('hand_xray.py',P/'work/rig_v1.blend','L',P/'review/hand_L')
step('hand_xray.py',P/'work/rig_v1.blend','R',P/'review/hand_R')
step('finger_weights.py',P/'work/rig_v1.blend',P/'work/rig_fingers.blend')
