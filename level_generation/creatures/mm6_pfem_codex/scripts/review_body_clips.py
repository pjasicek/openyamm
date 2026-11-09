import bpy,runpy,sys
from pathlib import Path
p=Path(__file__).resolve().parents[1];s=p/'scripts'
def run(name,*args):
 sys.argv=[name,'--',*map(str,args)];runpy.run_path(str(s/name),run_name='__main__')
run('clip_timing_pfem.py',p/'work/all_raw.blend',p/'work/all_timed.blend')
run('author_death_drape_pose.py')
run('correct_contacts.py')
run('twist_bones.py',p/'work/all_corrected.blend',p/'work/all_body.blend')
for view in ('front','left','three_quarter'):
 run('clip_sheet.py',p/'work/all_body.blend',p/'review/body_clips'/view,view,5,'Standing','Walking','Hit','Death','Fidget')
run('g4_weights.py',p/'work/all_body.blend','body','Standing:0','Walking:6','Hit:5','Hit:10','Death:24','Death:48','Death:71','Fidget:30')
run('g5_hand_stretch.py',p/'work/all_body.blend','Standing','Walking','Hit','Death','Fidget')
run('g6_contacts.py',p/'work/all_body.blend','Standing','Walking','Hit','Death','Fidget')
