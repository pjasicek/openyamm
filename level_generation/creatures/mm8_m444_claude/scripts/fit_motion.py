from pathlib import Path
import runpy,sys,os
p=Path(__file__).resolve().parents[1]
def run(name,args=[]):
 sys.argv=[str(p/'scripts'/name),'--']+[str(x) for x in args];runpy.run_path(str(p/'scripts'/name),run_name='__main__')
os.environ['RUN_STRIDE']='1.8'
run('run_fit.py',[p/'work/rig_v2.blend',p/'work/rig_v2f.blend'])
run('foot_level.py',[p/'work/rig_v2f.blend',p/'work/rig_v2l.blend','Standing','Walking:const','Attack','AttackFull','Death:until=24'])
run('plant_motion.py')
run('author_carry.py',[p/'work/rig_v2p.blend',p/'work/rig_v2c.blend','Standing:0.3','Walking:0.2','Running:0.3','Fidget:0.5'])
run('left_carry.py')
run('death_clearance.py')
run('clip_timing.py')
