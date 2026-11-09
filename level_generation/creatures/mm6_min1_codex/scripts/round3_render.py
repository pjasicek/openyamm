import runpy
from pathlib import Path
P=Path(__file__).resolve().parent
for name in ['render_final.py','round3_render_lods.py']:runpy.run_path(str(P/name),run_name='__main__')
