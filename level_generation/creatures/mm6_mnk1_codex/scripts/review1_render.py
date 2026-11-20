import runpy
from pathlib import Path
p=Path(__file__).resolve().parents[1]
for name in ['final_checks.py','render_final.py','uv_and_lod_review.py']:runpy.run_path(str(p/'scripts'/name),run_name='__main__')
