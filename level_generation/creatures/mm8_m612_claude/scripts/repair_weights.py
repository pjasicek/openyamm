from pathlib import Path
import runpy,sys
P=Path(__file__).resolve().parents[1]
def step(name,*args):
 script=P/'scripts'/name;sys.argv=[str(script),'--',*map(str,args)];runpy.run_path(str(script),run_name='__main__')
step('fit_digits.py')
step('retarget_gog.py')
step('animate_gog.py')
step('inspect_animation.py')
for view in ('front','left','three_quarter'):
 step('clip_sheet.py',P/'work/animated_v1.blend',P/f'review/pilot_{view}',view,5,'Standing','Walking','Attack','Death')
