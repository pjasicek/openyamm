import runpy
from pathlib import Path
P=Path(__file__).resolve().parent
for name in ['rebake_nearfinal.py','rebake_soft_trials.py']:runpy.run_path(str(P/name),run_name='__main__')
