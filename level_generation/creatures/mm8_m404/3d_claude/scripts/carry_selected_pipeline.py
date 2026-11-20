import runpy
from pathlib import Path
p=Path(__file__).resolve().parent
for n in ('posture_timing.py','check_fit_pipeline.py','grip_surface.py'):
 runpy.run_path(str(p/n),run_name='__main__')
