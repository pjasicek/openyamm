import runpy
from pathlib import Path
P=Path(__file__).parent
for n in ('assemble_rig.py','author_raven.py'):runpy.run_path(str(P/n),run_name='__main__')
