import runpy
from pathlib import Path
P=Path(__file__).resolve().parent
for s in ['assemble.py','floor_complete.py','export_check.py','export_gates.py']:runpy.run_path(str(P/s),run_name='__main__')
