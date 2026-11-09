from pathlib import Path
import runpy,sys,os
p=Path(__file__).resolve().parents[1]
def run(n,args):
 s=p/'scripts'/n;sys.argv=[str(s),'--']+[str(x) for x in args];runpy.run_path(str(s),run_name='__main__')
os.environ['GRIP_RENDER']=str(p/'review/grip')
run('grip_solve.py',[p/'work/rig_v4.blend','Standing',8])
run('apply_grip.py',[p/'work/rig_v4.blend',p/'work/rig_v5.blend'])
run('g5_hand_stretch.py',[p/'work/rig_v5.blend','Standing','Walking','Running','Attack','Hit'])
