import runpy
from pathlib import Path
p=Path(__file__).resolve().parent
for n in ('death_skirt_envelope.py','audit_skirt.py'):runpy.run_path(str(p/n),run_name='__main__')
