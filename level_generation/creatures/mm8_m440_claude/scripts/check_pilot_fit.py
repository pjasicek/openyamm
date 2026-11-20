from pathlib import Path
import runpy,sys,os
p=Path(__file__).resolve().parents[1]
def run(n,*a):
 sys.argv=[n,'--',*[str(x) for x in a]];runpy.run_path(str(p/'scripts'/n),run_name='__main__')
os.environ['R_HANDLE']='.025';os.environ['GRIP_RENDER']=str(p/'review/grip')
run('grip_solve.py',p/'work/pilot_fingers.blend','GripRef',8)
run('apply_grip.py',p/'work/pilot_fingers.blend',p/'work/pilot_grip.blend')
run('g4_weights.py',p/'work/pilot_grip.blend','pilot','Standing:15','Walking:9','Walking:27','Attack:9','Attack:17','Attack:26','Attack:36')
run('g5_hand_stretch.py',p/'work/pilot_grip.blend','Standing:15','Walking:9','Attack:17','Attack:26','Attack:36')
