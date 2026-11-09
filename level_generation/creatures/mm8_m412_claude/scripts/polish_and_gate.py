import sys,runpy,bpy
from pathlib import Path
p=Path(__file__).resolve().parents[1];w=p/'work'
def run(n,*args):
 sys.argv=[n,'--',*[str(a) for a in args]];runpy.run_path(str(p/'scripts'/n),run_name='__main__')
run('weights_polish.py',w/'motion_timed.blend',w/'motion_polished.blend')
picks=[]
for n in ['Standing','Walking','Running','Attack','Hit','Fidget','Death']:
 picks.extend(f'{n}:{f}' for f in range(0,int(bpy.data.actions[n].frame_range[1])+1,2))
run('g4_weights.py',w/'motion_polished.blend','polished',*picks)
