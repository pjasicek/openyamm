import runpy
from pathlib import Path
P=Path(__file__).resolve().parent
for name in ['build_rig.py','animate_serpentman.py','reduce_uv.py','check_reduced.py']:
 runpy.run_path(str(P/name))
