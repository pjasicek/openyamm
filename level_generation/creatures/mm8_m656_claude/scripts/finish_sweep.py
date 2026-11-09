import runpy
from pathlib import Path
P=Path(__file__).resolve().parent
for n in ['equipment_floor.py','scabbard_sweep.py','probe_mount.py']:
 runpy.run_path(str(P/n),run_name='__main__')
