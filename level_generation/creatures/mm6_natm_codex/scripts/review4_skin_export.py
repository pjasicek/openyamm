import runpy
from pathlib import Path
p=Path(__file__).resolve().parent
for n in ['review4_fragment.py','review2_reload.py']:runpy.run_path(str(p/n),run_name='__main__')
