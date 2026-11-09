import runpy,sys,os
from pathlib import Path
p=Path(__file__).resolve().parents[1]
def run(n,*a):
 sys.argv=[n,'--',*map(str,a)];runpy.run_path(str(p/'scripts'/n),run_name='__main__')
run('motion_fit.py')
run('tail_fit.py')
os.environ['FA']='0.6';os.environ['FA_RAMP']='0.0,0.12'
run('twist_bones.py',p/'work/rig_tail.blend',p/'work/rig_twist.blend')
run('weights_body.py',p/'work/rig_twist.blend',p/'work/rig_weighted_final.blend')
run('floor_finish.py')
run('finish_cloth.py')
run('audit_motion.py')
