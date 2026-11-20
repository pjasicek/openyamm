import runpy
from pathlib import Path
P=Path(__file__).resolve().parent
for script in ['round6_editable.py','round6_render.py','round6_gates.py']:
 runpy.run_path(str(P/script),run_name='__main__')
