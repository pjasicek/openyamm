import runpy
from pathlib import Path
P=Path(__file__).resolve().parent
for name in ['fix_weights.py','pilot_walk.py','animate_pilots.py','audit_pilots.py','export_pilots.py']:
 runpy.run_path(str(P/name),run_name='__main__')
