import runpy
from pathlib import Path
S=Path(__file__).resolve().parent
for n in ['settle_final_corpse.py','solve_skirt_corpse.py','check_corpse.py','elbow_gate.py','export_runtime.py']:
 runpy.run_path(str(S/n),run_name='__main__')
