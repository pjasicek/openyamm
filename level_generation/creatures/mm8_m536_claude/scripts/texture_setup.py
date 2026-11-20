import runpy
from pathlib import Path
p=Path(__file__).parent
for n in ['transfer_body_uv.py','uv_raster.py','uv_gate.py']:runpy.run_path(str(p/n),run_name='__main__')
