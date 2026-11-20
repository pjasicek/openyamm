import runpy
from pathlib import Path
P=Path(__file__).resolve().parent
for s in ['grip_final.py','final_motion.py']:runpy.run_path(str(P/s),run_name='__main__')
