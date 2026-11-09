import runpy,sys,os
from pathlib import Path
p=Path(__file__).resolve().parents[1]
def run(n,*a):
 sys.argv=[n,'--',*map(str,a)];runpy.run_path(str(p/'scripts'/n),run_name='__main__')
run('weights_body.py',p/'work/rig_v2.blend',p/'work/rig_weighted.blend')
run('finger_weights.py',p/'work/rig_weighted.blend',p/'work/rig_fingers.blend')
os.environ['FA']='0.6';os.environ['FA_RAMP']='0.0,0.12'
run('twist_bones.py',p/'work/rig_fingers.blend',p/'work/rig_calibration_twist.blend')
run('weights_body.py',p/'work/rig_calibration_twist.blend',p/'work/rig_weighted_final.blend')
run('prepare_surface_cost.py')
run('posture_timing.py')
run('fit_diagonal_grip.py')
