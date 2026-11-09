import runpy,sys,os
from pathlib import Path
p=Path(__file__).resolve().parents[1]
def run(n,*a):
 sys.argv=[n,'--',*map(str,a)];runpy.run_path(str(p/'scripts'/n),run_name='__main__')
os.environ['FA']='0.6';os.environ['FA_RAMP']='0.0,0.12'
run('twist_bones.py',p/'work/rig_tail.blend',p/'work/rig_twist.blend')
run('weights_body.py',p/'work/rig_twist.blend',p/'work/rig_weighted_final.blend')
run('g4_weights.py',p/'work/rig_weighted_final.blend','smooth','Standing:0','Attack:14','Attack:18','Hit:5','Death:28')
run('stretch_heatmap.py',p/'work/rig_weighted_final.blend','Attack',18,p/'review/arm_stretch')
