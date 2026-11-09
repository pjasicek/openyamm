from pathlib import Path
import runpy
p=Path(__file__).resolve().parent
for name in ['make_sword.py','inspect_geometry_v2.py']:
 runpy.run_path(str(p/name),run_name='__main__')
