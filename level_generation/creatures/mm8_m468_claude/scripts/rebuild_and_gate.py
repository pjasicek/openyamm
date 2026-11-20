from pathlib import Path
import runpy
p=Path(__file__).resolve().parents[1]
for n in ['rebuild_pilot.py','run_pilot_gates.py']:runpy.run_path(str(p/'scripts'/n),run_name='__main__')
