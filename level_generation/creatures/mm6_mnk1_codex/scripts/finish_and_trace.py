import runpy
from pathlib import Path
p=Path(__file__).resolve().parents[1]
for n in ['smooth_palms.py','export_runtime.py','trace_lod0.py']:runpy.run_path(str(p/'scripts'/n),run_name='__main__')
