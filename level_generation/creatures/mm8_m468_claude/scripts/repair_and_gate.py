from pathlib import Path
import runpy,sys,os
p=Path(__file__).resolve().parents[1]
def run(n,*a):
 sys.argv=[n,'--',*[str(x) for x in a]];runpy.run_path(str(p/'scripts'/n),run_name='__main__')
run('repair_remaining.py')
os.environ['FA']='.6';os.environ['FA_RAMP']='.15,.85';os.environ['TWIST_POSES_ONLY']='1';os.environ['TWIST_ACTIONS']='Hit,Death,Dead,Fidget,Cast,Running'
run('twist_bones.py',p/'work/full_repaired.blend',p/'work/full_repaired.blend')
run('ground_remaining.py')
run('export_repaired.py')
run('run_full_gates.py')
