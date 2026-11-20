import runpy,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1]
work=P/'work'
for script,args in [
    ('fit_joints.py',[]),
    ('joint_xray.py',[str(work/'step1.blend'),'Body',str(work/'joints_final.json'),str(P/'review/joints'),str(work/'meshy_joints.json')]),
    ('build_rig.py',[]),
    ('fit_fingers.py',[str(work/'rig_v1.blend')]),
    ('finger_joints.py',[str(work/'rig_v1.blend')]),
    ('build_rig.py',[]),
    ('hand_frame_check.py',[str(work/'rig_v1.blend')]),
    ('hand_xray.py',[str(work/'rig_v1.blend'),'R',str(P/'review/hand_R')]),
    ('hand_xray.py',[str(work/'rig_v1.blend'),'L',str(P/'review/hand_L')]),
]:
    sys.argv=[script,'--',*args]
    runpy.run_path(str(P/'scripts'/script),run_name='__main__')
