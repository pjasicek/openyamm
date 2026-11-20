import runpy
from pathlib import Path
P=Path(__file__).resolve().parent
for n in ['export_runtime.py','measure_export.py']:runpy.run_path(str(P/n),run_name='__main__')
