import runpy,sys
from pathlib import Path
P=Path(__file__).resolve().parent
for name in ('export_parity.py','source_motion_limits.py','build_lods.py'):
 sys.argv=[name];runpy.run_path(str(P/name),run_name='__main__')
