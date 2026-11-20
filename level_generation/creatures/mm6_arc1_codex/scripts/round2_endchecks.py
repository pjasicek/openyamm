import runpy,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True
for n in ['uv_gate_run.py','release_gate.py','export_trace_run.py','round2_export_gates.py','final_review.py']:runpy.run_path(str(P/'scripts'/n),run_name='__main__')
