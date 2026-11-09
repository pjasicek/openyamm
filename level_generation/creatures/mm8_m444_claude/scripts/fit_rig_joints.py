from pathlib import Path
import runpy,sys
p=Path(__file__).resolve().parents[1]
steps=[('compose_joints.py',[]),('joint_xray.py',[str(p/'work/step1.blend'),'Body',str(p/'work/joints_final.json'),str(p/'review/joints'),str(p/'work/joints.json')])]
for name,args in steps:
 sys.argv=[str(p/'scripts'/name),'--']+args
 runpy.run_path(str(p/'scripts'/name),run_name='__main__')
