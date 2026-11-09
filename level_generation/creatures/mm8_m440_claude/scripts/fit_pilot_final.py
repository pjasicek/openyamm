from pathlib import Path
import sys,runpy,os
p=Path(__file__).resolve().parents[1]
def run(n,*a):
 sys.argv=[n,'--',*[str(x) for x in a]];runpy.run_path(str(p/'scripts'/n),run_name='__main__')
run('restore_club_grip.py')
run('fit_actual_grip.py')
run('author_carry.py',p/'work/pilot_feet.blend',p/'work/pilot_carried.blend','Standing:.10','Walking:.15')
run('fit_attack.py')
run('support_pilot.py')
os.environ['FA']='.6';os.environ['FA_RAMP']='.15,.85';os.environ['FRADIUS']='.035'
run('twist_bones.py',p/'work/pilot_supported.blend',p/'work/pilot_twist.blend')
run('finger_weights.py',p/'work/pilot_twist.blend',p/'work/pilot_fingers.blend')
run('smooth_thumb_weights.py')
run('apply_grip.py',p/'work/pilot_fingers.blend',p/'work/pilot_grip.blend')
run('export_pilot.py')
run('source_motion_limits.py')
