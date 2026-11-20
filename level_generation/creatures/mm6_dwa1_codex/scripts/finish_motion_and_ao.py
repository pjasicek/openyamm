import runpy
from pathlib import Path
P=Path(__file__).resolve().parent
for n in ['final_motion.py','bake_ao.py']:runpy.run_path(str(P/n),run_name='__main__')
