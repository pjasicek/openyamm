import runpy
from pathlib import Path
P=Path(__file__).parent
for name in ['select_reduction.py','export_efreeti.py']:runpy.run_path(str(P/name),run_name='__main__')
