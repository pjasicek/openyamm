import runpy
from pathlib import Path
P=Path(__file__).resolve().parent
runpy.run_path(str(P/'stride_fit.py'),run_name='__main__')
runpy.run_path(str(P/'reduction_search.py'),run_name='__main__')
