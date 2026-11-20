from pathlib import Path
import runpy
p=Path(__file__).resolve().parent
for name in ('g3_fit.py','g4_animate.py'):
 runpy.run_path(str(p/name),run_name='__main__')
