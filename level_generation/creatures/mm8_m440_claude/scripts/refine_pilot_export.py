from pathlib import Path
import runpy,sys,os
p=Path(__file__).resolve().parents[1]
def run(n,*a):
 sys.argv=[n,'--',*[str(x) for x in a]];runpy.run_path(str(p/'scripts'/n),run_name='__main__')
run('clean_club.py')
os.environ['FA']='.6';os.environ['FA_RAMP']='.15,.85';os.environ['FRADIUS']='.035'
run('twist_bones.py',p/'work/pilot_carried.blend',p/'work/pilot_twist.blend')
run('finger_weights.py',p/'work/pilot_twist.blend',p/'work/pilot_fingers.blend')
run('smooth_thumb_weights.py')
run('apply_grip.py',p/'work/pilot_fingers.blend',p/'work/pilot_grip.blend')
run('export_pilot.py')
