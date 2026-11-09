import runpy
from pathlib import Path
p=Path(__file__).resolve().parent
for name in ['review4_final_diagnostics.py','review4_costume_diagnostic.py','review4_clearance_diagnostic.py','review4_render.py']:runpy.run_path(str(p/name),run_name='__main__')
