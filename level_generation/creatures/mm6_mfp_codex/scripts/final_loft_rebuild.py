import runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
for n in ['action_refine.py','fit_native_fall.py','probe_current.py']:runpy.run_path(str(P/'scripts'/n),run_name='__main__')
