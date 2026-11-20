from pathlib import Path
import runpy,sys,os
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'))
def run(n,*a):
 sys.argv=[n,'--',*[str(x) for x in a]];runpy.run_path(str(p/'scripts'/n),run_name='__main__')
os.environ['FA']='.6';os.environ['FA_RAMP']='.15,.85'
run('twist_bones.py',p/'work/pilot_raw.blend',p/'work/pilot_twist.blend')
for view in ['front','left']:run('clip_sheet.py',p/'work/pilot_twist.blend',p/f'review/pilot_raw_{view}',view,7,'Standing','Walking','Attack')
