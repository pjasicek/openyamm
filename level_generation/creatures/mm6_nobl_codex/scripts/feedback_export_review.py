import sys,runpy
from pathlib import Path
p=Path(__file__).resolve().parent;sys.path.insert(0,str(p))
for n in ['final_motion_gates.py','lit_details.py','build_lods.py']:
 sys.argv=[n,'--'];runpy.run_path(str(p/n),run_name='__main__')
