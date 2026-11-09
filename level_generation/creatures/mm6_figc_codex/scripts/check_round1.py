import runpy
from pathlib import Path
P=Path(__file__).resolve().parent
for name in ['motion_trace.py','blade_gate.py','export_parity.py','render_final.py']:runpy.run_path(str(P/name),run_name='__main__')
