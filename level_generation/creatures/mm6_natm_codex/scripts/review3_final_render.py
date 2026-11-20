import runpy
from pathlib import Path
p=Path(__file__).resolve().parent
for name in ['review3_final_diagnostics.py','review3_render.py','review3_render_focus.py']:runpy.run_path(str(p/name),run_name='__main__')
