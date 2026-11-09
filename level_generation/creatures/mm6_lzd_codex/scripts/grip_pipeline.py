import runpy,sys,os
from pathlib import Path
P=Path(__file__).resolve().parents[1]
def run(n,*a):
 sys.argv=[n,'--',*map(str,a)];runpy.run_path(str(P/'scripts'/n),run_name='__main__')
run('weights_lizard.py')
os.environ['GRIP_RENDER']=str(P/'review/grip_solved')
run('grip_solve.py',P/'work/rig_v5.blend','Standing','0')
