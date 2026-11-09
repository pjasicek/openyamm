import runpy
from pathlib import Path
P=Path(__file__).resolve().parent
for name in ['round8_gates.py','round8_editable.py','round8_render.py']:
 runpy.run_path(str(P/name),run_name='__main__')
