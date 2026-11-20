from pathlib import Path
import runpy
P=Path(__file__).resolve().parent
for s in ('raster_maps.py','bake_ao.py','bake_geometry_normal.py'):runpy.run_path(str(P/s),run_name='__main__')
