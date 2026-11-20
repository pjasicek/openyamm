import runpy
from pathlib import Path
S=Path(__file__).resolve().parent
runpy.run_path(str(S/'export_teeth.py'),run_name='__main__')
runpy.run_path(str(S/'render_teeth.py'),run_name='__main__')
