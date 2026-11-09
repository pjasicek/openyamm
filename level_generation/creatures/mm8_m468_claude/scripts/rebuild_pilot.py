from pathlib import Path
import runpy
p=Path(__file__).resolve().parents[1]
for name in ['build_pilots.py','finish_pilot.py']:runpy.run_path(str(p/'scripts'/name),run_name='__main__')
