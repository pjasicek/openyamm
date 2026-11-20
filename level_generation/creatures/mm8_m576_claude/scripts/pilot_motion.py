import runpy,sys,os
from pathlib import Path
P=Path(__file__).resolve().parent;W=P.parent/'work'
def run(n,*args):
    sys.argv=[n,'--',*map(str,args)];runpy.run_path(str(P/n),run_name='__main__')
run('author_carry.py',W/'sources_level.blend',W/'pilot_carry.blend','Standing:.15','Walking:.18')
run('author_attack.py',W/'pilot_carry.blend',W/'pilot_attack.blend')
run('apply_grip.py',W/'pilot_attack.blend',W/'pilot_gripped.blend')
os.environ['FA']='.6';os.environ['FA_RAMP']='.15,.85'
run('twist_bones.py',W/'pilot_gripped.blend',W/'pilot_twist.blend')
run('pauldrons.py',W/'pilot_twist.blend',W/'pilot_armour.blend')
run('weights_fix.py',W/'pilot_armour.blend',W/'pilot_weighted.blend')
run('floor_fit.py',W/'pilot_weighted.blend',W/'pilot_grounded.blend','Standing','Walking','Attack')
