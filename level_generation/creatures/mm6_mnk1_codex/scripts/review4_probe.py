import runpy
from pathlib import Path
p=Path(__file__).resolve().parent
for f in ['review4_tri_reduce.py','review4_candidate_gates.py','review4_reduction_render.py']:runpy.run_path(str(p/f),run_name='__main__')
