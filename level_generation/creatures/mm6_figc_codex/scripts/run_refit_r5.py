import runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
for name in ['run_fit_r5.py','run_floor_r5.py']:runpy.run_path(str(P/'scripts'/name),run_name='__main__')
