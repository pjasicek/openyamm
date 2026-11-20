import runpy
from pathlib import Path
p=Path(__file__).resolve().parent
for s in ['round2_motion.py','round2_preview.py','round2_export.py']:runpy.run_path(str(p/s),run_name='__main__')
