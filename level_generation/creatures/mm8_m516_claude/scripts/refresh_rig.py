import runpy
from pathlib import Path
p=Path(__file__).resolve().parent
for n in ['build_rig.py','animate_lizard.py','sync_master.py']:runpy.run_path(str(p/n),run_name='__main__')
