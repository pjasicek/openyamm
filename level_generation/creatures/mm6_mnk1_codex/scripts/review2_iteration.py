import runpy
from pathlib import Path
p=Path(__file__).resolve().parents[1]
for name in ['review2_fold.py','review2_uv.py','review2_normals.py','review2_quick.py','review1_robe.py','review1_export.py','review2_cloth_metrics.py']:runpy.run_path(str(p/'scripts'/name),run_name='__main__')
