import runpy
from pathlib import Path
p=Path(__file__).resolve().parents[1]
for f in ['render_final.py','uv_and_lod_review.py']:runpy.run_path(str(p/'scripts'/f),run_name='__main__')
