import runpy,sys,os
from pathlib import Path
p=Path(__file__).resolve().parents[1];w=p/'work'
def run(n,*args):
 sys.argv=[n,'--',*[str(a) for a in args]];runpy.run_path(str(p/'scripts'/n),run_name='__main__')
os.environ['GRIP_RENDER']=str(p/'review/grip_v3')
run('grip_solve.py',w/'rig_v4c.blend','GripRef','0')
run('apply_grip.py',w/'rig_v4c.blend',w/'rig_v5.blend')
run('g5_hand_stretch.py',w/'rig_v5.blend','Standing','Walking','Attack','Death')
