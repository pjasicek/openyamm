import runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
for name in ['run_gates_r6.py','run_finish_r6.py']:runpy.run_path(str(P/'scripts'/name),run_name='__main__')
