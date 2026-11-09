from pathlib import Path
import runpy
P=Path(__file__).resolve().parent
for s in ('author_full.py','check_death.py'):runpy.run_path(str(P/s),run_name='__main__')
