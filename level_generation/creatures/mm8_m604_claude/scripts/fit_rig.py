"""Build cloned source frames, then refit the actual fingers and rebuild those frames."""
from pathlib import Path
import runpy
import sys
import json
p=Path(__file__).resolve().parents[1]
steps=[('build_rig.py',[]),('fit_fingers.py',[str(p/'work/rig_v1.blend')]),
 ('finger_joints.py',[str(p/'work/rig_v1.blend')]),('build_rig.py',[]),
 ('hand_frame_check.py',[str(p/'work/rig_v1.blend')]),
 ('hand_xray.py',[str(p/'work/rig_v1.blend'),'R',str(p/'review/hand_R')]),
 ('hand_xray.py',[str(p/'work/rig_v1.blend'),'L',str(p/'review/hand_L')])]
for name,args in steps:
 script=p/'scripts'/name; sys.argv=[str(script),'--',*args]
 runpy.run_path(str(script),run_name='__main__')
 if name=='fit_fingers.py':
  fitted=json.loads((p/'work/fingers_fit.json').read_text())
  assert set(fitted)=={'L','R'},'Both five-finger chains must fit before the rig advances'
