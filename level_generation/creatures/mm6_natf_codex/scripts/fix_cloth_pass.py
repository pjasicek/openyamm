import runpy
from pathlib import Path
p=Path(__file__).parent
for f in ['animate_natf.py','skirt_motion.py','audit_geometry.py']:runpy.run_path(str(p/f),run_name='__main__')
