import runpy,sys,os
from pathlib import Path
P=Path(__file__).resolve().parents[1];W=P/'work'
def run(n,*a):
 sys.argv=[n,'--',*map(str,a)];runpy.run_path(str(P/'scripts'/n),run_name='__main__')
run('weights_fix.py',W/'motion_mixamo.blend',W/'motion_weights.blend')
os.environ['FA']='0.6';os.environ['FA_RAMP']='0.05,0.3'
run('twist_bones.py',W/'motion_weights.blend',W/'motion_twist.blend')
run('finger_weights.py',W/'motion_twist.blend',W/'rig_pilot.blend')
run('author_motion.py')
run('pilot_gates.py')
