import runpy
from pathlib import Path
p=Path(__file__).parent
for f in ['finish_weights.py','audit_finished.py']:runpy.run_path(str(p/f),run_name='__main__')
