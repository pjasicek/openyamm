from pathlib import Path
import sys,runpy
p=Path(__file__).resolve().parents[1]
for name,args in [('audit_motion.py',[str(p/'work/cage.blend')]),('inspect_contact.py',[]),('check_contacts.py',[str(p/'work/cage.blend'),'Running','Fidget'])]:
 path=p/'scripts'/name;sys.argv=[str(path),'--',*args];runpy.run_path(str(path),run_name='__main__')
