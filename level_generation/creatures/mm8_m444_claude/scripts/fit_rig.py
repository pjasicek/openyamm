"""Build cloned source frames, fit the five finger chains, then rebuild with measured hand frames."""
from pathlib import Path
import runpy,sys
p=Path(__file__).resolve().parents[1]
steps=[('build_rig.py',[]),('fit_fingers.py',[str(p/'work/rig_v1.blend')]),('finger_joints.py',[str(p/'work/rig_v1.blend')]),('build_rig.py',[])]
for name,args in steps:
 print('STAGE',name,flush=True)
 sys.argv=[str(p/'scripts'/name),'--']+args
 runpy.run_path(str(p/'scripts'/name),run_name='__main__')
