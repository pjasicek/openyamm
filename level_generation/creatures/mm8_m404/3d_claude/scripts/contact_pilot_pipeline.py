import runpy
from pathlib import Path
p=Path(__file__).resolve().parent
for name in ['check_fit_pipeline.py','grip_surface.py','apply_surface_fingers.py','gates_pilot.py']:
 runpy.run_path(str(p/name),run_name='__main__')
