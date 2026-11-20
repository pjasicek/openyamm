import sys,runpy,os
from pathlib import Path
P=Path(__file__).resolve().parents[1]
def run(n,*args):
    sys.argv=[n,'--',*[str(x) for x in args]]
    runpy.run_path(str(P/'scripts'/n),run_name='__main__')
run('author_fidget.py')
run('finish_timing.py')
run('settle_wrists.py')
os.environ['FA']='0.6'; os.environ['FA_RAMP']='0.15,0.85'
run('twist_bones.py',P/'work/rig_wrists.blend',P/'work/rig_timed_twist.blend')
run('dagger.py')
for view in ['front','left','back']:
    run('clip_sheet.py',P/'work/rig_props.blend',P/f'review/fidget_{view}',view,8,'Fidget')
run('g5_hand_stretch.py',P/'work/rig_props.blend','Fidget')
run('sole_probe.py',P/'work/rig_props.blend','Standing','Walking','Running','Hit','Death','Fidget')
