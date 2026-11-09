from pathlib import Path
import runpy,sys,os
p=Path(__file__).resolve().parents[1]
def run(n,*a):
 sys.argv=[n,'--',*[str(x) for x in a]];runpy.run_path(str(p/'scripts'/n),run_name='__main__')
for n in ['adapt_pilots.py','vest_weights.py','align_hinges.py']:run(n)
os.environ['FA']='.6';os.environ['FA_RAMP']='.15,.85';os.environ['TWIST_POSES_ONLY']='1'
run('twist_bones.py',p/'work/pilot_fitted.blend',p/'work/pilot_fitted.blend')
run('export_pilot.py')
run('run_pilot_gates.py')
