from pathlib import Path
import runpy
P=Path(__file__).resolve().parent
for s in ('author_pilots.py','twist_pilots.py','check_pilots.py'):runpy.run_path(str(P/s),run_name='__main__')
