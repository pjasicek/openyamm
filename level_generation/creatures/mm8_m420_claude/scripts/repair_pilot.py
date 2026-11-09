from pathlib import Path
import runpy
p=Path(__file__).resolve().parent
for name in ['build_pilot.py','prepare_staff.py','inspect_pilot.py']:runpy.run_path(str(p/name),run_name='__main__')
