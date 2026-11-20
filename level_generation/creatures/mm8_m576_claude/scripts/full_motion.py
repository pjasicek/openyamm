import runpy,sys,os
from pathlib import Path
P=Path(__file__).resolve().parent;W=P.parent/'work'
def run(n,*args):
    sys.argv=[n,'--',*map(str,args)];runpy.run_path(str(P/n),run_name='__main__')
run('run_fit.py',W/'pilot_attack.blend',W/'full_run.blend')
run('author_carry.py',W/'full_run.blend',W/'full_carry.blend','Running:.15','Hit:.12','Fidget:.10','Death:0')
run('apply_grip.py',W/'full_carry.blend',W/'full_grip.blend')
os.environ['FA']='.6';os.environ['FA_RAMP']='.15,.85'
run('twist_bones.py',W/'full_grip.blend',W/'full_twist.blend')
run('pauldrons.py',W/'full_twist.blend',W/'full_armour.blend')
run('weights_fix.py',W/'full_armour.blend',W/'full_weighted.blend')
run('finish_motion.py',W/'full_weighted.blend',W/'full_grounded.blend')
run('reduce_rigged.py',W/'full_grounded.blend',W/'master_rig.blend')
run('g5_hand_stretch.py',W/'master_rig.blend','Standing','Walking','Running','Attack','Hit','Death','Fidget')
run('jerk_probe.py',W/'master_rig.blend','Standing','Walking','Running','Attack','Hit','Death','Fidget')
os.environ['STEP']='.5';run('sole_probe.py',W/'master_rig.blend','Standing','Walking','Running','Attack','Hit','Fidget')
