import runpy
from pathlib import Path
p=Path(__file__).resolve().parent
for n in ('posture_timing.py','contact_pilot_pipeline.py'):runpy.run_path(str(p/n),run_name='__main__')
