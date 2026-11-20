from pathlib import Path
import runpy,sys,os
p=Path(__file__).resolve().parents[1]
def run(n,*a):
 sys.argv=[n,'--',*[str(x) for x in a]];runpy.run_path(str(p/'scripts'/n),run_name='__main__')
run('run_fit.py',p/'work/full_reduced.blend',p/'work/full_runfit.blend')
run('refine_remaining.py')
run('author_carry.py',p/'work/full_repaired.blend',p/'work/full_repaired.blend','Running:.15:x=-.42:y=-.47:z=.98:pitch=15:yaw=-45','Fidget:.10')
os.environ['TWIST_POSES_ONLY']='1';os.environ['TWIST_ACTIONS']='Running,Fidget,Death,Dead,Hit';os.environ['FA']='.6'
run('twist_bones.py',p/'work/full_repaired.blend',p/'work/full_repaired.blend')

run('finish_physical.py')
