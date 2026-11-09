import runpy
from pathlib import Path
P=Path(__file__).resolve().parent
for name in ['motion_trace.py','blade_gate.py','export_parity.py','render_final.py','render_props_r2.py']:runpy.run_path(str(P/name),run_name='__main__')
