from pathlib import Path
import runpy,sys,os
p=Path(__file__).resolve().parents[1]
def run(n,*a):
 sys.argv=[n,'--',*[str(x) for x in a]];runpy.run_path(str(p/'scripts'/n),run_name='__main__')
run('adapt_pilots.py')
run('vest_weights.py')
run('align_hinges.py')
os.environ['FA']='.6';os.environ['FA_RAMP']='.15,.85';os.environ['TWIST_POSES_ONLY']='1'
run('twist_bones.py',p/'work/pilot_fitted.blend',p/'work/pilot_fitted.blend')
for view in ['front','left','three_quarter']:run('clip_sheet.py',p/'work/pilot_fitted.blend',p/f'review/pilot_fitted_{view}',view,9,'Standing','Walking','Attack')
run('g5_hand_stretch.py',p/'work/pilot_fitted.blend','Standing','Walking','Attack')

run('export_pilot.py')
