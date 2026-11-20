from pathlib import Path
import runpy
p=Path(__file__).resolve().parent
for name in ['reduce_geometry.py','scale_review.py']:
 runpy.run_path(str(p/name),run_name='__main__')
