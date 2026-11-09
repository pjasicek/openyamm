import runpy
from pathlib import Path
P=Path(__file__).parent
for n in ('finish_rig.py','contacts.py','review_motion.py'):runpy.run_path(str(P/n),run_name='__main__')
