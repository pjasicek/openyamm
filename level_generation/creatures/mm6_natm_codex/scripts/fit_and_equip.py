import sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
for s in ['fit_motion.py','equipment.py','run_motion_checks.py']:
 sys.argv=[s];runpy.run_path(str(P/'scripts'/s),run_name='__main__')
