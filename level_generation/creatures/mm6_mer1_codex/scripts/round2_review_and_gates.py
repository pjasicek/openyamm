import runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
for n in ['round2_configure_gates.py','round2_render_final.py','round2_compare.py','round2_final_gates.py']:
 runpy.run_path(str(P/'scripts'/n),run_name='__main__')
