from pathlib import Path
import sys,runpy
p=Path(__file__).resolve().parents[1]
for script,args in [('build_rig.py',[]),('fit_fingers.py',[str(p/'work/rig_v1.blend')]),('finger_joints.py',[str(p/'work/rig_v1.blend')]),('build_rig.py',[]),('hand_frame_check.py',[str(p/'work/rig_v1.blend')])]:
    sys.argv=[script,'--',*args]
    runpy.run_path(str(p/'scripts'/script),run_name='__main__')
