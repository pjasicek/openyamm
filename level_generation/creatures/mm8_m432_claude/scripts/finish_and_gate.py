import runpy
from pathlib import Path
P=Path(__file__).resolve().parent
for name in ['finish_motion.py','final_arm_pass.py']:runpy.run_path(str(P/name),run_name='__main__')
