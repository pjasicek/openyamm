import os,sys,runpy
from pathlib import Path
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'))
for n in ['weight_and_grip.py','rebuild_motion.py','review_contacts.py']:
 sys.argv=[n,'--'];runpy.run_path(str(p/'scripts'/n),run_name='__main__')
