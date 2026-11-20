import runpy
from pathlib import Path
p=Path(__file__).resolve().parent
for n in ['transfer_uv.py','uv_raster.py','bake_ao.py']:runpy.run_path(str(p/n),run_name='__main__')
