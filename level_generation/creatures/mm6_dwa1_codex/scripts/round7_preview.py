import runpy
from pathlib import Path
P=Path(__file__).resolve().parent
for script in ['round7_render.py','round7_gates.py']:runpy.run_path(str(P/script),run_name='__main__')
