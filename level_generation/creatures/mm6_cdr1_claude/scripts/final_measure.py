import runpy
from pathlib import Path
S=Path(__file__).resolve().parent
runpy.run_path(str(S/'measure_scale.py'),run_name='__main__')
runpy.run_path(str(S/'build_lods.py'),run_name='__main__')
