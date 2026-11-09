import runpy
from pathlib import Path
p=Path(__file__).resolve().parents[1]
for s in ['pilot_finish.py','gates_dense.py','gates_first.py']:runpy.run_path(str(p/'scripts'/s),run_name='__main__')
