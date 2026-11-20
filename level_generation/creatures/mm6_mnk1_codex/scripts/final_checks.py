import runpy
from pathlib import Path
p=Path(__file__).resolve().parents[1]
for s in ['export_parity.py','run_trace.py']:runpy.run_path(str(p/'scripts'/s),run_name='__main__')
