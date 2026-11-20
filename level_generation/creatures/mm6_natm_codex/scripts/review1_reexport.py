import runpy
from pathlib import Path
p=Path(__file__).resolve().parent
runpy.run_path(str(p/'review1_feathers.py'),run_name='__main__')
runpy.run_path(str(p/'quick_export.py'),run_name='__main__')
