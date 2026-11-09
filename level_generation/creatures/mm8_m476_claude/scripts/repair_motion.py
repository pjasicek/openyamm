from pathlib import Path
import runpy,sys,os
p=Path(__file__).resolve().parents[1]
def run(name,*args):
 s=p/'scripts'/name;sys.argv=[str(s),'--',*map(str,args)];runpy.run_path(str(s),run_name='__main__')
run('ground_motion.py')
os.environ['FA']='0.6';os.environ['FA_RAMP']='0.15,0.85'
run('twist_bones.py',p/'work/motion_grounded.blend',p/'work/motion_twist.blend')
run('apply_grip.py',p/'work/motion_twist.blend',p/'work/motion_grip.blend')
run('smooth_thumb_webs.py')
run('reduce_rigged.py',p/'work/motion_grip_smooth.blend',p/'work/rig_v5.blend')
run('g5_hand_stretch.py',p/'work/rig_v5.blend','Standing','Walking','Running','Attack','Hit','Fidget','Death')
run('diagnose_reduction.py')
