from pathlib import Path
import runpy
p=Path(__file__).resolve().parent
for s in ['fit_neck.py','export_drake.py']:runpy.run_path(str(p/s),run_name='__main__')
