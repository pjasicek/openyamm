import runpy, sys, os
from pathlib import Path
P=Path(__file__).resolve().parents[1]
def run(n,*args):
    sys.argv=[n,'--',*[str(x) for x in args]]
    runpy.run_path(str(P/'scripts'/n),run_name='__main__')
os.environ['R_HANDLE']='0.010'
os.environ['GRIP_RENDER']=str(P/'review/grip')
run('grip_solve.py',P/'work/rig_reduced.blend','GripRef',0)
run('apply_grip.py',P/'work/rig_reduced.blend',P/'work/rig_grip.blend')
for view in ['front','left','back']:
    run('clip_sheet.py',P/'work/rig_grip.blend',P/f'review/pilot_{view}',view,5,'Standing','Walking','Running','Hit','Death')
run('g5_hand_stretch.py',P/'work/rig_grip.blend','Standing','Walking','Running','Hit','Death')
