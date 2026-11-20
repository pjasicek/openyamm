import runpy
from pathlib import Path
P=Path(__file__).resolve().parent
runpy.run_path(str(P/'reduce_step.py'),run_name='__main__')
runpy.run_path(str(P/'render_reduction.py'),run_name='__main__')
