import runpy
from pathlib import Path
p=Path(__file__).resolve().parent
for name in ['posture_timing.py','fit_diagonal_grip.py']:
 runpy.run_path(str(p/name),run_name='__main__')
