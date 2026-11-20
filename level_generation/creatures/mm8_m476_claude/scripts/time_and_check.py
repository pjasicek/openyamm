from pathlib import Path
import runpy,sys
p=Path(__file__).resolve().parents[1]
def run(name,*args):
 s=p/'scripts'/name;sys.argv=[str(s),'--',*map(str,args)];runpy.run_path(str(s),run_name='__main__')
run('finish_clip_timing.py');run('attach_club.py');run('check_contacts.py')
run('g5_hand_stretch.py',p/'work/rig_v5.blend','Standing','Walking','Running','Attack','Hit','Fidget','Death')
