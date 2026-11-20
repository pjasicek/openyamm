from pathlib import Path
import runpy
P=Path(__file__).resolve().parent
for name in ['transfer_three_sets.py','uv_raster.py','preview_raw_v2.py']:
 runpy.run_path(str(P/name),run_name='__main__')
