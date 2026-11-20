import runpy
from pathlib import Path
p=Path(__file__).resolve().parent
for n in ['reload_textures.py','reduce_measured.py']:runpy.run_path(str(p/n),run_name='__main__')
