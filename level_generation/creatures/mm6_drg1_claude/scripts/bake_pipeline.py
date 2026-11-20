from pathlib import Path
import runpy
p=Path(__file__).resolve().parent
runpy.run_path(str(p/'uv_raster.py'),run_name='__main__')
runpy.run_path(str(p/'bake_ao.py'),run_name='__main__')
