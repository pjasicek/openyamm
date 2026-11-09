import runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
runpy.run_path(str(P/'scripts/finish_motion.py'),run_name='__main__')
runpy.run_path(str(P/'scripts/check_motion.py'),run_name='__main__')
