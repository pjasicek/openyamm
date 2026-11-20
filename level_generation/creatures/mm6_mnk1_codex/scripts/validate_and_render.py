import runpy
from pathlib import Path
p=Path(__file__).resolve().parents[1]
for n in ['final_checks.py','render_final.py']:runpy.run_path(str(p/'scripts'/n),run_name='__main__')
