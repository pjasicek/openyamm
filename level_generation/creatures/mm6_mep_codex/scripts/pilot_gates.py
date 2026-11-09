import runpy,sys
from pathlib import Path
p=Path(__file__).resolve().parents[1]
def run(n,*a):
 sys.argv=[n,'--',*map(str,a)];runpy.run_path(str(p/'scripts'/n),run_name='__main__')
run('author_mep.py')
run('g4_weights.py',p/'work/anim_pilot.blend','pilot','Standing:0','Walking:18','Running:18','Fidget:30','Attack:20','Cast:22','Hit:8','Death:60','Dead:0')
run('g5_hand_stretch.py',p/'work/anim_pilot.blend','Standing','Walking','Running','Fidget','Attack','Cast','Hit','Death','Dead')
