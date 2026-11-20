import runpy
from pathlib import Path
P=Path(__file__).resolve().parent
for s in ['native_hit.py','assemble.py','master_gates.py']:runpy.run_path(str(P/s),run_name='__main__')
