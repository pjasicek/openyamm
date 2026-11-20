import runpy
from pathlib import Path
p=Path(__file__).parent
for n in ['select_reduction.py','export_genie.py']:runpy.run_path(str(p/n),run_name='__main__')
