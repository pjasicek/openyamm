import runpy
from pathlib import Path
p=Path(__file__).parent
for f in ['export_salamander.py','audit_export.py']:runpy.run_path(str(p/f),run_name='__main__')
