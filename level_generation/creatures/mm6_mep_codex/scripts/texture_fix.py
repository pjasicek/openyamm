import runpy
from pathlib import Path
p=Path(__file__).resolve().parent
for n in ['texture_return.py','ao_bake.py']:runpy.run_path(str(p/n),run_name='__main__')
