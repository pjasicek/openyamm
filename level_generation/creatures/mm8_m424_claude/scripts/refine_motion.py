import runpy,sys,os
from pathlib import Path
P=Path(__file__).resolve().parents[1]
def run(n,*args):
    sys.argv=[n,'--',*[str(x) for x in args]]
    runpy.run_path(str(P/'scripts'/n),run_name='__main__')
run('refine_weights.py')
os.environ['R_HANDLE']='0.010'; os.environ['GRIP_RENDER']=str(P/'review/grip_refined')
run('grip_solve.py',P/'work/rig_refined.blend','GripRef',0)
run('apply_grip.py',P/'work/rig_refined.blend',P/'work/rig_refined_grip.blend')
# A short dagger can follow the source running arm; a fixed carry target flares the elbow.
run('author_carry.py',P/'work/rig_refined_grip.blend',P/'work/rig_carry.blend','Standing:0.3','Walking:0.35')
os.environ['FA']='0.6'; os.environ['FA_RAMP']='0.15,0.85'
run('twist_bones.py',P/'work/rig_carry.blend',P/'work/rig_carry_twist.blend')
for view in ['front','left','back']:
    run('clip_sheet.py',P/'work/rig_carry_twist.blend',P/f'review/carry_{view}',view,5,'Standing','Walking','Running')
run('g5_hand_stretch.py',P/'work/rig_carry_twist.blend','Standing','Walking','Running','Hit','Death')
