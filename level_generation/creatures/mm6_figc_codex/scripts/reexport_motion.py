import runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
for n in ['motion_finish.py','export_runtime.py']:runpy.run_path(str(P/'scripts'/n),run_name='__main__')
