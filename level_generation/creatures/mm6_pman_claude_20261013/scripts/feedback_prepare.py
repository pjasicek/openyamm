import runpy
from pathlib import Path
p=Path(__file__).resolve().parent
for name in ['feedback_repair.py','raster_feedback.py','bake_ao.py']:runpy.run_path(str(p/name),run_name='__main__')
