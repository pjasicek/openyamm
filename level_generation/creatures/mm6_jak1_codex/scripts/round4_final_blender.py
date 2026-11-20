import runpy
from pathlib import Path
p=Path(__file__).parent
for s in ['round4_gates.py','round4_render.py']:runpy.run_path(str(p/s),run_name='__main__')
