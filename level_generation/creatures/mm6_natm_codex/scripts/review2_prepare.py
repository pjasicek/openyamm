import runpy
from pathlib import Path
p=Path(__file__).resolve().parent
for name in ['review2_motion.py','review2_raster.py','quick_export.py']:runpy.run_path(str(p/name),run_name='__main__')
