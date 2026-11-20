import runpy
from pathlib import Path
p=Path(__file__).resolve().parent
for name in ['apply_surface_fingers.py','gates_pilot.py']:
 runpy.run_path(str(p/name),run_name='__main__')
