import runpy
from pathlib import Path
p=Path(__file__).parent
for f in ['transfer_body_uv.py','uv_raster.py']:runpy.run_path(str(p/f),run_name='__main__')
