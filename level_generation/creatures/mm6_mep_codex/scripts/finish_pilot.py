import runpy,sys,os
from pathlib import Path
p=Path(__file__).resolve().parents[1]
def run(n,*a):
 sys.argv=[n,'--',*map(str,a)];runpy.run_path(str(p/'scripts'/n),run_name='__main__')
run('author_mep.py')
os.environ['FA']='0.6';os.environ['FA_RAMP']='0.15,0.85'
run('twist_bones.py',p/'work/anim_pilot.blend',p/'work/anim_twist.blend')
run('g4_weights.py',p/'work/anim_twist.blend','twist','Standing:0','Walking:18','Running:18','Fidget:30','Attack:20','Cast:22','Hit:8','Death:60','Dead:0')
