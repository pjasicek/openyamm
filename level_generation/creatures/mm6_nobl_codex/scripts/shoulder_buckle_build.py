import runpy,sys
from pathlib import Path
p=Path(__file__).resolve().parent
for name in ['shoulder_buckle_repair.py','export_runtime.py']:
 sys.argv=[name];runpy.run_path(str(p/name),run_name='__main__')
