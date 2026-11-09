import sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P/'scripts'));sys.dont_write_bytecode=True
for script,args in [('compose_joints.py',[]),('build_rig.py',[]),('fit_fingers.py',[str(P/'work/rig_v1.blend')]),('finger_joints.py',[str(P/'work/rig_v1.blend')]),('build_rig.py',[]),('hand_frame_check.py',[str(P/'work/rig_v1.blend')]),('hand_xray.py',[str(P/'work/rig_v1.blend'),'R',str(P/'review/hands_fitted_R')]),('hand_xray.py',[str(P/'work/rig_v1.blend'),'L',str(P/'review/hands_fitted_L')])]:
    print('RUN',script,flush=True)
    sys.argv=[script,'--']+args
    runpy.run_path(str(P/'scripts'/script),run_name='__main__')
