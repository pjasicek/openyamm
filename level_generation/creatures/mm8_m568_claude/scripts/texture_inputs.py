import runpy
from pathlib import Path
P=Path(__file__).resolve().parent
for name in ['transfer_body_uv.py','uv_raster.py','bake_ao.py']:runpy.run_path(str(P/name),run_name='__main__')
