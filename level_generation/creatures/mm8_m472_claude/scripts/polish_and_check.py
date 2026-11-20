from pathlib import Path
import runpy
p=Path(__file__).resolve().parents[1]
for name in ['polish_weights.py','check_deformation.py']:runpy.run_path(str(p/'scripts'/name),run_name='__main__')
