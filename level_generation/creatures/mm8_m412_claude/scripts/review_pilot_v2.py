import runpy,sys
from pathlib import Path
p=Path(__file__).resolve().parents[1]
def run(n,*args):
 sys.argv=[n,'--',*[str(a) for a in args]];runpy.run_path(str(p/'scripts'/n),run_name='__main__')
for v in ['front','left','three_quarter']:
 run('clip_sheet.py',p/'work/master_rig.blend',p/('review/motion_v2_'+v),v,'7','Standing','Walking','Running','Attack','Hit','Fidget','Death')
run('sole_probe.py',p/'work/master_rig.blend','Standing','Walking','Running','Attack','Hit','Fidget','Death')
run('g5_hand_stretch.py',p/'work/master_rig.blend','Standing','Walking','Running','Attack','Hit','Fidget','Death')
run('jerk_probe.py',p/'work/master_rig.blend','Standing','Walking','Running','Attack','Hit','Fidget','Death')
