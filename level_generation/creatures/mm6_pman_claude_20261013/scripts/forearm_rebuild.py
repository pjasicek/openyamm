import runpy
from pathlib import Path
p=Path(__file__).resolve().parent
for name in ['repair_forearms.py','forearm_finish.py']:runpy.run_path(str(p/name),run_name='__main__')
