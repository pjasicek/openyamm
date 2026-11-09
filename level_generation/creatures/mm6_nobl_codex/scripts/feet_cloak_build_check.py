import runpy,sys
from pathlib import Path
p=Path(__file__).resolve().parents[1]
for name in ['feet_cloak_finish.py','fall_cloak_clearance.py','export_runtime.py','feet_cloak_check.py']:
 sys.argv=[name];runpy.run_path(str(p/'scripts'/name),run_name='__main__')
