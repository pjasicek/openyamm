import runpy
from pathlib import Path
p=Path(__file__).resolve().parent
for n in ['review4_costume.py','review4_piece_render.py','review4_right_search.py']:runpy.run_path(str(p/n),run_name='__main__')
