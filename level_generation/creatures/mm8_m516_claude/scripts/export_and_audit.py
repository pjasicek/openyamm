import runpy
from pathlib import Path
p=Path(__file__).resolve().parent
for n in ['export_lizard.py','audit_export.py','inspect_dead.py']:runpy.run_path(str(p/n),run_name='__main__')
