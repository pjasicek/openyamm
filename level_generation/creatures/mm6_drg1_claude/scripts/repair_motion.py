import runpy
from pathlib import Path
p=Path(__file__).resolve().parent
for script in ['add_death_flames.py','animate_drake.py']:runpy.run_path(str(p/script),run_name='__main__')
