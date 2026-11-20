import sys,os,runpy
from pathlib import Path
p=Path(__file__).resolve().parents[1];os.chdir(p);sys.path.insert(0,str(p/'scripts'))
def run(n,args=()):
 sys.argv=[n,'--',*map(str,args)];runpy.run_path(str(p/'scripts'/n),run_name='__main__')
run('body_weights.py');run('finger_weights.py',['work/pilot_weights.blend','work/pilot_fingers.blend'])
run('twist_bones.py',['work/pilot_fingers.blend','work/pilot.blend'])
run('grip_solve.py',['work/pilot.blend','GripRef','8'])
