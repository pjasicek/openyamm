from pathlib import Path
import sys,runpy
P=Path(__file__).resolve().parents[1];W=P/'work';sys.path.insert(0,str(P/'scripts'))
def run(n,*args):
 sys.argv=[n,'--',*map(str,args)];runpy.run_path(str(P/'scripts'/n),run_name='__main__')
run('author_carry.py',W/'source_motion.blend',W/'pilot_carry.blend','Standing:0.1','Walking:0.18','Running:0.18:yaw=18:pitch=55')
run('apply_grip.py',W/'pilot_carry.blend',W/'pilot_carry.blend')
run('author_actions.py')
run('staff_clearance.py')
run('twist_bones.py',W/'actions.blend',W/'actions_twist.blend')
run('attach_staff.py')
