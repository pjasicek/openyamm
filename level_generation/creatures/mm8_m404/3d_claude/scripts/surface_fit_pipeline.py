import runpy
from pathlib import Path
p=Path(__file__).resolve().parent
for n in ('prepare_surface_cost.py','check_fit_pipeline.py'):
 runpy.run_path(str(p/n),run_name='__main__')
