from pathlib import Path
import runpy
p=Path(__file__).resolve().parent
for script in ['repair_texture_uv.py','uv_raster.py','bake_ao.py']:runpy.run_path(str(p/script),run_name='__main__')
