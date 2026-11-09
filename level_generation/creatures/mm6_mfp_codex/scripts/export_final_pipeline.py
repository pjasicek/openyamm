import runpy
from pathlib import Path
p=Path(__file__).resolve().parent
for name in ['propagate_polished.py','export_levels.py']:runpy.run_path(str(p/name),run_name='__main__')
