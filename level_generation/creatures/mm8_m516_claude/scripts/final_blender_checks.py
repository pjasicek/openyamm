import runpy
from pathlib import Path
p=Path(__file__).resolve().parent
for n in ['pack_editable.py','audit_lod_motion.py']:runpy.run_path(str(p/n),run_name='__main__')
