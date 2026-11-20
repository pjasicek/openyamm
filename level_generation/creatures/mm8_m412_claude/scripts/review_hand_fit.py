import runpy,sys
from pathlib import Path
p=Path(__file__).resolve().parents[1]
for name,args in [('hand_frame_check.py',[p/'work/rig_v1.blend']),('hand_xray.py',[p/'work/rig_v1.blend','R',p/'review/hand_joints'])]:
 sys.argv=[name,'--',*[str(a) for a in args]];runpy.run_path(str(p/'scripts'/name),run_name='__main__')
