from pathlib import Path
import runpy
p=Path(__file__).resolve().parent
for name in ('refine_grip.py','clip_timing.py'):
 runpy.run_path(str(p/name),run_name='__main__')
