import runpy
from pathlib import Path
P=Path(__file__).resolve().parent
for n in ['audit_full.py','review_death.py']:runpy.run_path(str(P/n),run_name='__main__')
