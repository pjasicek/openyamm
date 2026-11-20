import runpy,sys,os
from pathlib import Path
P=Path(__file__).resolve().parents[1];B=P/'work/motion_native.blend'
def run(n,*a):
 sys.argv=[n,'--',str(B),*map(str,a)];runpy.run_path(str(P/'scripts'/n),run_name='__main__')
acts=['Standing','Walking','Running','Attack','Hit','Death','Fidget','Dead']
run('g4_weights.py','native','Standing:0','Walking:12','Running:11','Attack:37','Attack:49','Hit:12','Death:80','Fidget:37')
run('g5_hand_stretch.py',*acts)
os.environ['STEP']='0.5';run('sole_probe.py',*acts)
run('jerk_probe.py',*acts)
