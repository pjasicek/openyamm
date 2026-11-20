from pathlib import Path
import runpy
P=Path(__file__).resolve().parent
for name in ['uv_raster.py','bake_three_ao.py']:runpy.run_path(str(P/name),run_name='__main__')
