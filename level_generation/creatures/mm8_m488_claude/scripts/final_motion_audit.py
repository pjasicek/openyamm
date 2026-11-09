from pathlib import Path
import runpy,sys
p=Path(__file__).resolve().parents[1];roles=['Standing','Walking','Running','Attack','Hit','Fidget','Death','Dead']
for name,args in [('audit_motion.py',[str(p/'work/hands.blend')]),('check_contacts.py',[str(p/'work/hands.blend'),*roles]),('g5_hand_stretch.py',[str(p/'work/hands.blend'),*roles]),('jerk_probe.py',[str(p/'work/hands.blend'),*roles]),('sole_probe.py',[str(p/'work/hands.blend'),'Standing','Walking','Running','Attack','Hit','Fidget'])]:
 path=p/'scripts'/name;sys.argv=[str(path),'--',*args];runpy.run_path(str(path),run_name='__main__')
