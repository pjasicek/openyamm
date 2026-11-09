import runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
for name in ['round5_render.py','round5_trial_gates.py']:runpy.run_path(str(P/'scripts'/name),run_name='__main__')
