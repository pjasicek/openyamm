from pathlib import Path
import runpy,sys
p=Path(__file__).resolve().parents[1]
steps=[('hand_frame_check.py',[str(p/'work/rig_v1.blend')])]+[('hand_xray.py',[str(p/'work/rig_v1.blend'),s,str(p/'review'/('hand_'+s))]) for s in ('R','L')]
for name,args in steps:
 sys.argv=[str(p/'scripts'/name),'--']+args;runpy.run_path(str(p/'scripts'/name),run_name='__main__')
