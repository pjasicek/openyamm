from pathlib import Path
import runpy
p=Path(__file__).resolve().parent
for name in ('g4_animate.py','build_native_prop.py','g6_audit.py'):
 runpy.run_path(str(p/name),run_name='__main__')
