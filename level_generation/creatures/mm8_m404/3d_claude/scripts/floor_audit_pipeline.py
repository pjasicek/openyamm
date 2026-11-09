import runpy
from pathlib import Path
p=Path(__file__).resolve().parent
for n in ('floor_finish.py','audit_motion.py'):runpy.run_path(str(p/n),run_name='__main__')
