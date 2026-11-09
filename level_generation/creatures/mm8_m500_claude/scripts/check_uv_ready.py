from pathlib import Path
import runpy
P=Path(__file__).resolve().parent
for name in ['uv_gate.py','uv_raster.py','uv_checker.py']:runpy.run_path(str(P/name),run_name='__main__')
