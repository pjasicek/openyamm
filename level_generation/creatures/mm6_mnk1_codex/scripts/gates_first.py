import runpy,sys,json
from pathlib import Path
p=Path(__file__).resolve().parents[1]
acts=['Standing','Walking','Running','Attack','Cast','Hit','Death','Dead','Fidget']
def run(n,*a):
 sys.argv=[n,'--',*map(str,a)];runpy.run_path(str(p/'scripts'/n),run_name='__main__')
run('g5_hand_stretch.py',p/'work/anim_reduced.blend',*acts)
run('g4_weights.py',p/'work/anim_reduced.blend','first','Standing:0','Walking:8','Attack:22','Cast:15','Hit:8','Death:45','Dead:0','Fidget:20','Running:8')
run('g6_contacts.py',p/'work/anim_reduced.blend',*acts)
