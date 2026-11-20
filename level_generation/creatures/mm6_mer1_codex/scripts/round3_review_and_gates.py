import runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
for name in ['round3_configure_gates.py','round3_closeups.py','round3_render_final.py','round3_compare.py','round2_final_gates.py']:
 print('ROUND3 REVIEW',name,flush=True);runpy.run_path(str(P/'scripts'/name),run_name='__main__')
