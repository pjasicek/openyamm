from pathlib import Path
import sys,runpy,os
p=Path(__file__).resolve().parents[1]
os.environ['GRIP_RENDER']=str(p/'review/grip_v2')
for name,args in [('grip_solve.py',[p/'work/rig_v4.blend','Standing','8']),('apply_grip.py',[p/'work/rig_v4.blend',p/'work/rig_v5.blend'])]:
 sys.argv=[str(p/'scripts'/name),'--',*map(str,args)]
 runpy.run_path(sys.argv[0],run_name='__main__')
