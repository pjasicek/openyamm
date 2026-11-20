import runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
for name in ['round3_configure_gates.py','round2_final_gates.py']:runpy.run_path(str(P/'scripts'/name),run_name='__main__')
