from pathlib import Path
import runpy
S=Path(__file__).resolve().parent
for n in ['build_lods.py','trace_final.py','final_blade_gate.py']:
 runpy.run_path(str(S/n),run_name='__main__')
