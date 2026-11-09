import runpy
from pathlib import Path
S=Path(__file__).resolve().parent
for n in ['elbow_gate.py','render_final.py']:
 runpy.run_path(str(S/n),run_name='__main__')
