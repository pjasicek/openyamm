from pathlib import Path
import runpy,sys
p=Path(__file__).resolve().parents[1]
def run(n,*a):
 sys.argv=[n,'--',*[str(x) for x in a]];runpy.run_path(str(p/'scripts'/n),run_name='__main__')
for view in ['front','left']:
 run('clip_sheet.py',p/'work/pilot_raw.blend',p/f'review/pilot_raw_{view}',view,9,'Standing','Walking','Attack')
run('g5_hand_stretch.py',p/'work/pilot_raw.blend','Standing','Walking','Attack')
