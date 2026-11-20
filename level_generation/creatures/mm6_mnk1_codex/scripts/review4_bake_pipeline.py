import runpy
from pathlib import Path
p=Path(__file__).resolve().parent
for f in ['review4_uv.py','review4_surface_bake.py']:runpy.run_path(str(p/f),run_name='__main__')
