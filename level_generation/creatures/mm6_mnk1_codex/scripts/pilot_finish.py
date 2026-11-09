import runpy,sys
from pathlib import Path
p=Path(__file__).resolve().parents[1]
def run(n,*args):
 sys.argv=[n,'--',*map(str,args)];runpy.run_path(str(p/'scripts'/n),run_name='__main__')
run('fit_sleeves.py');run('author_monk.py');run('cast_steps.py');run('floor_boots.py');run('robe_monk.py');run('twist_bones.py',p/'work/anim_robe.blend',p/'work/anim_gates.blend')
for view in ['front','left','three_quarter']:run('clip_sheet.py',p/'work/anim_gates.blend',p/'review'/f'pilot_sheet_{view}',view,5,'Standing','Walking','Attack','Cast','Hit','Death')

run('reduce_rigged.py',p/'work/anim_gates.blend',p/'work/anim_reduced.blend')
