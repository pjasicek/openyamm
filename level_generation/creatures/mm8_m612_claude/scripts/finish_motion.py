import runpy,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];R=P.parents[2]
def step(name,*args):
 script=P/'scripts'/name;sys.argv=[str(script),'--',*map(str,args)];runpy.run_path(str(script),run_name='__main__')
step('retarget_mixamo.py',P/'work/animated_raw.blend',P/'work/animated_raw.blend',str(R/'anim_library/mixamo/Standard Run.fbx')+':Running')
step('animate_gog.py')
step('inspect_animation.py')
step('contacts.py')
for view in ('front','left','three_quarter'):
 step('clip_sheet.py',P/'work/animated_v1.blend',P/f'review/run_{view}',view,5,'Running')
step('source_jerk.py')
step('preview_run.py')
