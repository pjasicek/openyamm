import sys,runpy,os
from pathlib import Path
P=Path(__file__).resolve().parents[1];os.chdir(P);sys.path.insert(0,str(P/'scripts'));sys.dont_write_bytecode=True
for n in ['animate_natf.py','review_pilots.py']:
 sys.argv=[n,'--'];runpy.run_path(str(P/'scripts'/n),run_name='__main__')
