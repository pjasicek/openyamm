from pathlib import Path
import sys,runpy,json
p=Path(__file__).resolve().parents[1]
def run(name,*args):
 path=p/'scripts'/name;sys.argv=[str(path),'--',*map(str,args)];runpy.run_path(str(path),run_name='__main__')
run('hand_review.py')
run('audit_motion.py',p/'work/hands.blend')
run('check_contacts.py',p/'work/hands.blend','Standing','Walking','Running','Attack','Hit','Fidget','Death','Dead')
run('g5_hand_stretch.py',p/'work/hands.blend','Standing','Walking','Running','Attack','Hit','Fidget','Death','Dead')
run('export_preview.py')
