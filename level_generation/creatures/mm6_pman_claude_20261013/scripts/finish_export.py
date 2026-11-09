import runpy
from pathlib import Path
p=Path(__file__).resolve().parent
for name in ['fix_quaternion_continuity.py','export_model.py','audit_final.py']:runpy.run_path(str(p/name),run_name='__main__')
