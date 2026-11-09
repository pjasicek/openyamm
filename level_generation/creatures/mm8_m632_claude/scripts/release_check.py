import os,runpy
from pathlib import Path
p=Path(__file__).resolve().parent
os.environ['M632_FAST_CHECK']='1'
for n in ('author_motion.py','grip_contacts.py','contacts.py'):runpy.run_path(str(p/n),run_name='__main__')
