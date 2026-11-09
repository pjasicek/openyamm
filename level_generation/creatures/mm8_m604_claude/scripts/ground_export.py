from pathlib import Path
import runpy
p=Path(__file__).resolve().parent
for n in ['ground_final.py','export_runtime.py']:runpy.run_path(str(p/n),run_name='__main__')
