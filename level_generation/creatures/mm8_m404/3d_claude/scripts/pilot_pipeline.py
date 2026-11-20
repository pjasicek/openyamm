import runpy,sys,os
from pathlib import Path
p=Path(__file__).resolve().parents[1]
def run(n,*a):
 sys.argv=[n,'--',*map(str,a)];runpy.run_path(str(p/'scripts'/n),run_name='__main__')
run('tail_fit.py')
os.environ['FA']='0.6';os.environ['FA_RAMP']='0.0,0.12'
run('twist_bones.py',p/'work/rig_tail.blend',p/'work/rig_twist.blend')
run('weights_body.py',p/'work/rig_twist.blend',p/'work/rig_weighted_final.blend')
run('g5_hand_stretch.py',p/'work/rig_weighted_final.blend','Standing','Walking','Attack','Hit','Fidget','Death')
for view in ('front','left','three_quarter'):
 run('clip_sheet.py',p/'work/rig_weighted_final.blend',p/('review/pilot/'+view),view,6,'Standing','Walking','Attack','Hit','Fidget','Death')
