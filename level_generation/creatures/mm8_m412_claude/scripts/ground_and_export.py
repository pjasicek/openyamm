import runpy
from pathlib import Path
p=Path(__file__).resolve().parent
for n in ['fit_source_run_floor.py','export_runtime.py']:runpy.run_path(str(p/n),run_name='__main__')
