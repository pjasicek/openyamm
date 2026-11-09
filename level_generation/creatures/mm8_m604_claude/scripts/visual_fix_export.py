from pathlib import Path
import runpy
p=Path(__file__).resolve().parent
for n in ['line_cloth.py','refresh_motion.py']:runpy.run_path(str(p/n),run_name='__main__')
