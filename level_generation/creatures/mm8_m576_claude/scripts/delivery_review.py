import sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parent
for name in ('measure_scale.py','lod_visual.py'):
 sys.argv=[name];runpy.run_path(str(P/name),run_name='__main__')
