import runpy
from pathlib import Path
p=Path(__file__).resolve().parent
for n in ('close_coincident_cloth.py','export_runtime.py'):runpy.run_path(str(p/n),run_name='__main__')
