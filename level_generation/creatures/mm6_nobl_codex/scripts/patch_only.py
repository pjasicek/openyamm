import runpy,sys
from pathlib import Path
p=Path(__file__).resolve().parent;sys.path.insert(0,str(p))
for n in ['patch_body_actions.py','review_contacts.py']:
 sys.argv=[n,'--'];runpy.run_path(str(p/n),run_name='__main__')
