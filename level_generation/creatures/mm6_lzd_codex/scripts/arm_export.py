import runpy
from pathlib import Path
P=Path(__file__).resolve().parent
for s in ['final_arm_polish.py','assemble.py','export_check.py']:runpy.run_path(str(P/s),run_name='__main__')
