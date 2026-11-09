from pathlib import Path
import runpy,sys,os
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'))
def run(n,*a):
 sys.argv=[n,'--',*[str(x) for x in a]];runpy.run_path(str(p/'scripts'/n),run_name='__main__')
run('repair_remaining.py')
os.environ['FA']='.6';os.environ['FA_RAMP']='.15,.85';os.environ['TWIST_POSES_ONLY']='1';os.environ['TWIST_ACTIONS']='Hit,Death,Dead,Fidget,Running'
run('twist_bones.py',p/'work/full_repaired.blend',p/'work/full_repaired.blend')
run('reduce_and_gate.py')
for view in ['front','left']:run('clip_sheet.py',p/'work/full_reduced.blend',p/f'review/reduced_{view}',view,7,'Hit','Death','Running')
