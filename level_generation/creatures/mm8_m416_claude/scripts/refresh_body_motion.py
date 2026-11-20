from pathlib import Path
import runpy,sys
P=Path(__file__).resolve().parents[1]
def run(n,args=()):
 s=P/'scripts'/n;sys.argv=[str(s),'--',*map(str,args)];runpy.run_path(str(s),run_name='__main__')
run('weights_fix.py')
run('finger_weights.py',[P/'work/weighted.blend',P/'work/fingered.blend'])
run('author_pilot.py')
run('complete_motion.py')
run('refine_clearance.py')
run('all_deformation.py')
run('surface_checks.py')
