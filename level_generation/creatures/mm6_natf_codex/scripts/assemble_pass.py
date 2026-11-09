import runpy
from pathlib import Path
p=Path(__file__).parent
for f in ['build_props.py','assemble.py']:runpy.run_path(str(p/f),run_name='__main__')
